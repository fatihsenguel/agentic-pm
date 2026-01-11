# portfolio_tool/data_manager.py
import tomli  
import sys
from sqlalchemy import func
from sqlalchemy.orm import Session, DeclarativeMeta
# NEUER IMPORT für Idempotenz (Upsert)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from typing import Optional

from .database_setup import (
    Asset, DailyPrice, Dividend, CorporateAction, SharesHistory,
    Fundamentals, QuarterlyEarnings, AssetFetchMetadata, Base, FinancialStatement
)
from .providers.base import DataProviderInterface 
from datetime import timedelta, date, datetime 
# --- CONFIG-LADEN (unverändert) ---
CONFIG_PATH = "config.toml" 

def load_config():
    """Lädt die Konfigurationsdatei."""
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomli.load(f)
    except FileNotFoundError:
        print(f"WARNUNG: {CONFIG_PATH} nicht gefunden. Verwende Standard-Intervalle.")
        return {"data_fetch": {
            "earnings_fetch_interval_days": 7,
            "profile_fetch_interval_days": 30,
            "shares_fetch_interval_days": 30
        }}
    except tomli.TOMLDecodeError:
        print(f"FEHLER: {CONFIG_PATH} ist fehlerhaft.")
        raise

CONFIG = load_config()
# --- ENDE CONFIG ---


class DataManager:
    
    def __init__(self, session: Session, provider: DataProviderInterface):
        self.session = session
        self.provider = provider  
        self.config = CONFIG['data_fetch']
        
    # --- Interne Helfer (unverändert) ---
    def _get_or_create_metadata(self, asset_id: int) -> AssetFetchMetadata:
        meta = self.session.query(AssetFetchMetadata).get(asset_id)
        if not meta:
            meta = AssetFetchMetadata(asset_id=asset_id)
            self.session.add(meta) 
        return meta

    def _should_fetch(self, last_fetch_time: datetime | None, interval_days: int) -> bool:
        if not last_fetch_time:
            return True 
        return (datetime.utcnow() - last_fetch_time).days >= interval_days

    # --- Asset-Management (unverändert) ---
    def get_or_create_asset(self, ticker: str, name: str, asset_class: str) -> Optional[Asset]:
        # (Diese Methode bleibt unverändert, sie war korrekt)
        asset = self.session.query(Asset).filter_by(ticker=ticker).first()
        if asset:
            print(f"Asset gefunden: {asset.name}")
            return asset
        print(f"Asset {ticker} nicht gefunden, erstelle es...")
        info_dto = self.provider.get_asset_info(ticker)
        new_asset_data = {'ticker': ticker, 'asset_class': asset_class, 'name': name}
        if info_dto:
            print(f"... Lade erweiterte Stammdaten für {ticker}")
            new_asset_data.update({
                'sector': info_dto.sector,
                'industry': info_dto.industry,
                'country': info_dto.country,
                'currency': info_dto.currency,
                'name': info_dto.long_name or name 
            })
        else:
            print(f"WARNUNG: Konnte keine erweiterten Daten für {ticker} abrufen.")
        try:
            new_asset = Asset(**new_asset_data)
            self.session.add(new_asset)
            self.session.commit()
            print(f"Asset erstellt: {new_asset}")
            return new_asset
        except Exception as e:
            print(f"Fehler beim Erstellen von Asset {ticker}: {e}", file=sys.stderr)
            self.session.rollback()
            return None

    # --- IDEMPOTENTE UPSERT-METHODEN --- MIT BATCHES ---
    def _perform_upsert(self, 
                        model: DeclarativeMeta, 
                        values: list[dict], 
                        index_elements: list[str]):
        """
        Führt einen atomaren, idempotenten Upsert-Vorgang für SQLite aus.
        NEU: Teilt große Einfügungen in Batches auf, um das
        "too many SQL variables"-Limit von SQLite zu umgehen.
        """
        if not values:
            return # Nichts zu tun

        # Wie viele Zeilen pro Batch?
        # 7 Spalten pro Preis-Zeile. SQLite-Limit ist oft ~32k Variablen.
        # 32000 / 7 = ~4500 Zeilen. Wir nehmen 500, um absolut sicher zu sein.
        BATCH_SIZE = 500
        total_rows = len(values)
        num_batches = (total_rows // BATCH_SIZE) + (1 if total_rows % BATCH_SIZE > 0 else 0)
        
        # Wir führen alle Batches in einer einzigen Transaktion aus.
        # Wenn ein Batch fehlschlägt, wird alles zurückgerollt.
        try:
            for i in range(0, total_rows, BATCH_SIZE):
                # Nimm den nächsten Stapel
                chunk = values[i:i + BATCH_SIZE]
                
                # Erstelle das Statement NUR für diesen Chunk
                stmt = sqlite_insert(model).values(chunk)
                
                # Definiere die Spalten, die bei einem Konflikt aktualisiert werden sollen
                update_cols = [
                    col for col in chunk[0].keys() if col not in index_elements
                ]
                update_set = {
                    col: getattr(stmt.excluded, col) for col in update_cols
                }

                # Definiere die ON CONFLICT DO UPDATE-Klausel
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=index_elements,
                    set_=update_set
                )
                
                # Führe das Statement für den Chunk aus
                self.session.execute(upsert_stmt)
            
            # Wenn alle Schleifen durchlaufen sind, committe die Transaktion
            self.session.commit()
            print(f"... {total_rows} Zeilen in {model.__tablename__} importiert (Upsert in {num_batches} Batches).")
        
        except Exception as e:
            # Wenn IRGENDEIN Batch fehlschlägt, rolle alles zurück
            print(f"... FEHLER beim Batch-Upsert in {model.__tablename__}: {e}", file=sys.stderr)
            self.session.rollback()

    def update_prices_for_asset(self, asset: Asset, start_date: date | None = None):
        print(f"... prüfe Preise für {asset.ticker}")
        if not start_date:
            last_entry = self.session.query(func.max(DailyPrice.date)).filter(
                DailyPrice.asset_id == asset.id
            ).scalar()
            start_date = (last_entry) if last_entry else date(2000, 1, 1) 
        
        if start_date and start_date > date.today():
            print("... Preise sind aktuell.")
            return
            
        provider_data = self.provider.get_daily_prices(
            ticker=asset.ticker,
            start=start_date,
            end=date.today()
        )
        if not provider_data:
            print("... Preise sind aktuell (Provider lieferte keine neuen Daten).")
            return

        # (1) Konvertiere DTOs in Dicts für den Upsert
        values_to_upsert = []
        for price_dto in provider_data:
            if start_date and price_dto.date < start_date:
                continue 
            values_to_upsert.append({
                'asset_id': asset.id,
                'date': price_dto.date,
                'open': float(price_dto.open), 
                'high': float(price_dto.high), 
                'low': float(price_dto.low),
                'close': float(price_dto.close), 
                'volume': price_dto.volume
            })

        if not values_to_upsert:
            print("... Preise sind aktuell (nach Filterung).")
            return
            
        # (2) Rufe die Upsert-Helfermethode auf
        self._perform_upsert(
            model=DailyPrice,
            values=values_to_upsert,
            index_elements=['asset_id', 'date']
        )


    def update_dividends_for_asset(self, asset: Asset):
        print(f"... prüfe Dividenden für {asset.ticker}")
        last_ex_date = self.session.query(func.max(Dividend.ex_date)).filter(
            Dividend.asset_id == asset.id
        ).scalar()
        
        dividends_data = self.provider.get_dividends(asset.ticker, since=last_ex_date)
        if not dividends_data:
            print("... keine neuen Dividenden-Daten gefunden.")
            return

        values_to_upsert = []
        for div_dto in dividends_data:
            if last_ex_date and div_dto.ex_date < last_ex_date:
                continue
            values_to_upsert.append({
                'asset_id': asset.id,
                'ex_date': div_dto.ex_date,
                'amount': float(div_dto.amount)
            })

        if not values_to_upsert:
            print("... Dividenden sind aktuell.")
            return

        self._perform_upsert(
            model=Dividend,
            values=values_to_upsert,
            index_elements=['asset_id', 'ex_date']
        )


    def update_splits_for_asset(self, asset: Asset):
        print(f"... prüfe Splits für {asset.ticker}")
        last_split_date = self.session.query(func.max(CorporateAction.date)).filter(
            CorporateAction.asset_id == asset.id,
            CorporateAction.action_type == 'Split'
        ).scalar()
        
        splits_data = self.provider.get_splits(asset.ticker, since=last_split_date)
        if not splits_data:
            print("... keine neuen Split-Daten gefunden.")
            return

        values_to_upsert = []
        for split_dto in splits_data:
            if last_split_date and split_dto.date < last_split_date:
                continue
            values_to_upsert.append({
                'asset_id': asset.id,
                'date': split_dto.date,
                'action_type': 'Split',
                'value': split_dto.ratio_str
            })

        if not values_to_upsert:
            print("... Splits sind aktuell.")
            return
            
        self._perform_upsert(
            model=CorporateAction,
            values=values_to_upsert,
            index_elements=['asset_id', 'date', 'action_type']
        )


    def update_shares_history_for_asset(self, asset: Asset, force_update: bool = False):
        print(f"... prüfe Historie der Aktienanzahl für {asset.ticker}")
        meta = self._get_or_create_metadata(asset.id)
        interval = self.config.get('shares_fetch_interval_days', 30)

        if not force_update and not self._should_fetch(meta.last_shares_fetch_time, interval):
            print(f"... Abruf der Aktienanzahl übersprungen (Intervall {interval} Tage).")
            return

        since_date = self.session.query(func.max(SharesHistory.date)).filter(
            SharesHistory.asset_id == asset.id
        ).scalar()
        
        try:
            hist_data = self.provider.get_shares_history(asset.ticker, since=since_date)
        except Exception as e:
            print(f"FEHLER beim Abrufen der Shares für {asset.ticker}: {e}", file=sys.stderr)
            return

        if not hist_data:
            print("... keine neuen Daten zur Aktienanzahl gefunden.")
            meta.last_shares_fetch_time = datetime.utcnow()
            self.session.commit()
            return

        unique_dtos = {}
        for shares_dto in hist_data:
            if since_date and shares_dto.date < since_date:
                continue 
            unique_dtos[shares_dto.date] = shares_dto 

        values_to_upsert = []
        for shares_dto in unique_dtos.values():
            values_to_upsert.append({
                'asset_id': asset.id,
                'date': shares_dto.date,
                'shares': shares_dto.shares
            })

        if not values_to_upsert:
            print("... Historie der Aktienanzahl ist aktuell (nach Filterung).")
        else:
            self._perform_upsert(
                model=SharesHistory,
                values=values_to_upsert,
                index_elements=['asset_id', 'date']
            )

        # Commit für die Metadaten
        meta.last_shares_fetch_time = datetime.utcnow()
        try:
            self.session.commit()
        except Exception as e:
            print(f"... Fehler beim Commit der Shares-Metadaten: {e}", file=sys.stderr)
            self.session.rollback()


    def update_quarterly_earnings_for_asset(self, asset: Asset, force_update: bool = False):
        print(f"... prüfe Quartalsberichte für {asset.ticker}")
        meta = self._get_or_create_metadata(asset.id)
        interval = self.config.get('earnings_fetch_interval_days', 7)

        if not force_update and not self._should_fetch(meta.last_earnings_fetch_time, interval):
            print(f"... Abruf der Earnings übersprungen (Intervall {interval} Tage).")
            return

        since_date = self.session.query(func.max(QuarterlyEarnings.report_date)).filter(
            QuarterlyEarnings.asset_id == asset.id
        ).scalar()

        try:
            provider_data = self.provider.get_quarterly_earnings(asset.ticker, since=since_date)
        except Exception as e:
            print(f"FEHLER beim Abrufen der Earnings für {asset.ticker}: {e}", file=sys.stderr)
            return

        if not provider_data:
            print("... keine neuen Quartalsberichte vom Provider erhalten.")
            meta.last_earnings_fetch_time = datetime.utcnow()
            self.session.commit()
            return

        values_to_upsert = []
        max_report_date = since_date
        
        for dto in provider_data:
            if since_date and dto.report_date < since_date:
                continue
            values_to_upsert.append({
                'asset_id': asset.id,
                'report_date': dto.report_date,
                'revenue': dto.revenue,
                'basic_eps': float(dto.basic_eps) if dto.basic_eps is not None else None
            })
            if max_report_date is None or dto.report_date > max_report_date:
                max_report_date = dto.report_date

        if not values_to_upsert:
            print("... Quartalsberichte sind aktuell.")
        else:
            self._perform_upsert(
                model=QuarterlyEarnings,
                values=values_to_upsert,
                index_elements=['asset_id', 'report_date']
            )

        # Commit für die Metadaten
        meta.last_earnings_fetch_time = datetime.utcnow()
        if max_report_date and max_report_date != since_date:
            meta.last_earnings_report_date = max_report_date
        
        try:
            self.session.commit()
        except Exception as e:
            print(f"... FEHLER beim Commit der Earnings-Metadaten: {e}", file=sys.stderr)
            self.session.rollback()

    # --- Methoden für Fundamentaldaten & Stammdaten (bleiben unverändert) ---
    # Diese Methoden (update_fundamental_data, force_update_asset_info)
    # bearbeiten keine Zeitreihen und nutzen bereits ein "Update"-Pattern,
    # daher müssen sie nicht auf 'on_conflict' umgestellt werden.

    def force_update_asset_info(self, asset: Asset) -> bool:
        # (Diese Methode bleibt unverändert, sie war korrekt)
        print(f"  > Erzwinge Stammdaten-Update für {asset.ticker}...")
        info_dto = self.provider.get_asset_info(asset.ticker)
        if not info_dto:
            print(f"  > Konnte keine Daten vom Provider für {asset.ticker} abrufen.")
            return False
        asset.sector = info_dto.sector
        asset.industry = info_dto.industry
        asset.country = info_dto.country
        asset.currency = info_dto.currency
        if info_dto.long_name:
            asset.name = info_dto.long_name
        try:
            self.session.commit()
            print(f"  > {asset.ticker} erfolgreich aktualisiert.")
            return True
        except Exception as e:
            print(f"  > FEHLER beim Speichern von {asset.ticker}: {e}", file=sys.stderr)
            self.session.rollback()
            return False

    def update_fundamental_data(self, asset: Asset, force_update: bool = False):
        # (Diese Methode bleibt unverändert, sie war korrekt)
        print(f"... prüfe Fundamentaldaten für {asset.ticker}")
        meta = self._get_or_create_metadata(asset.id)
        interval = self.config.get('profile_fetch_interval_days', 30)

        if not force_update and not self._should_fetch(meta.last_profile_fetch_time, interval):
            print(f"... Abruf der Fundamentaldaten übersprungen (Intervall {interval} Tage).")
            return

        dto = self.provider.get_fundamental_data(asset.ticker)
        if not dto:
            print(f"... keine Fundamentaldaten vom Provider erhalten.")
            meta.last_profile_fetch_time = datetime.utcnow()
            self.session.commit()
            return

        db_fund = self.session.query(Fundamentals).filter_by(asset_id=asset.id).first()
        if not db_fund:
            print("... erstelle neuen Fundamentals-Eintrag.")
            db_fund = Fundamentals(asset_id=asset.id)
            self.session.add(db_fund)
        else:
            print("... aktualisiere bestehenden Fundamentals-Eintrag.")

        db_fund.beta = float(dto.beta) if dto.beta is not None else None
        db_fund.last_updated = datetime.utcnow() 

        meta.last_profile_fetch_time = datetime.utcnow()

        try:
            self.session.commit()
            print(f"... Fundamentaldaten (beta) für {asset.ticker} gespeichert.")
        except Exception as e:
            print(f"... FEHLER beim Speichern der Fundamentaldaten: {e}", file=sys.stderr)
            self.session.rollback()

    def update_financial_statements_for_asset(
        self,
        asset: Asset,
        report_type: str,
        period_type: str,
    ) -> None:
        """
        Holt Financial Statements für ein Asset und speichert sie idempotent
        in der Tabelle financial_statements.

        report_type: "income", "balance_sheet", "cash_flow"
        period_type: "annual", "quarterly"
        """
        print(f"... prüfe Financial Statements für {asset.ticker} "
              f"({report_type}, {period_type})")

        # Letztes vorhandenes Periodenende für dieses Asset/Typ/Frequenz
        last_date = (
            self.session.query(func.max(FinancialStatement.date))
            .filter(
                FinancialStatement.asset_id == asset.id,
                FinancialStatement.report_type == report_type,
                FinancialStatement.period_type == period_type,
            )
            .scalar()
        )

        # Daten vom Provider holen
        try:
            provider_data = self.provider.get_financial_statements(
                ticker=asset.ticker,
                report_type=report_type,
                period_type=period_type,
                since=last_date,
            )
        except Exception as e:
            print(f"FEHLER beim Abrufen der Financial Statements für "
                  f"{asset.ticker}: {e}", file=sys.stderr)
            return

        if not provider_data:
            print("... keine neuen Financial Statements vom Provider erhalten.")
            return

        values_to_upsert: list[dict] = []

        for dto in provider_data:
            # defensive: falls Provider 'since' nicht 100% beachtet
            if last_date and dto.date <= last_date:
                continue

            values_to_upsert.append({
                "asset_id": asset.id,
                "date": dto.date,
                "report_type": dto.report_type,
                "period_type": dto.period_type,
                "source": dto.source,

                "revenue": dto.revenue,
                "net_income": dto.net_income,
                "eps": dto.eps,
                "free_cash_flow": dto.free_cash_flow,

                "total_assets": dto.total_assets,
                "total_liabilities": dto.total_liabilities,

                "cost_of_revenue": dto.cost_of_revenue,
                "research_and_development": dto.research_and_development,
                "selling_general_and_administrative": dto.selling_general_and_administrative,
                "interest_expense": dto.interest_expense,
                "income_tax_expense": dto.income_tax_expense,

                "cash_and_cash_equivalents": dto.cash_and_cash_equivalents,
                "accounts_receivable": dto.accounts_receivable,
                "inventory": dto.inventory,
                "property_plant_equipment": dto.property_plant_equipment,
                "accounts_payable": dto.accounts_payable,
                "current_debt": dto.current_debt,
                "long_term_debt": dto.long_term_debt,
                "common_stock": dto.common_stock,
                "retained_earnings": dto.retained_earnings,
                "accumulated_other_comprehensive_income": dto.accumulated_other_comprehensive_income,

                "operating_cash_flow": dto.operating_cash_flow,
                "depreciation_and_amortization": dto.depreciation_and_amortization,
                "stock_based_compensation": dto.stock_based_compensation,
                "change_in_working_capital": dto.change_in_working_capital,
                "capital_expenditure": dto.capital_expenditure,
                "dividends_paid": dto.dividends_paid,
                "issuance_of_debt": dto.issuance_of_debt,
                "repayment_of_debt": dto.repayment_of_debt,
                "issuance_of_stock": dto.issuance_of_stock,
                "repurchase_of_stock": dto.repurchase_of_stock,

                "raw_json": dto.raw_json,
            })

        if not values_to_upsert:
            print("... Financial Statements sind aktuell (nach Filterung).")
            return

        self._perform_upsert(
            model=FinancialStatement,
            values=values_to_upsert,
            index_elements=["asset_id", "date", "report_type", "period_type"],
        )
