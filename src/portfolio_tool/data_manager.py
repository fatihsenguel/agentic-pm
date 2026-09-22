# portfolio_tool/data_manager.py
import tomli  
import sys
from sqlalchemy import func
from sqlalchemy.orm import Session, DeclarativeMeta
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


from typing import Optional, List, Dict, Any

# The result type every update returns
from .models.responses import UpdateResult

from .database_setup import (
    Asset, DailyPrice, Dividend, CorporateAction, SharesHistory,
    Fundamentals, QuarterlyEarnings, AssetFetchMetadata, Base, FinancialStatement, MacroData,
    FxRate, FxFetchMetadata,
)
from .providers.base import DataProviderInterface 
from datetime import timedelta, date, datetime 

import logging
logger = logging.getLogger(__name__)

# --- Config ---
CONFIG_PATH = "config.toml"

def load_config():
    """Loads config.toml. The fetch intervals are policy and live there and
    nowhere else: a missing file raises rather than running a table of
    intervals from code, and a missing key raises at the reader."""
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomli.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{CONFIG_PATH} not found; the fetch intervals are read from it and "
            f"have no defaults in code"
        )
    except tomli.TOMLDecodeError:
        print(f"ERROR: {CONFIG_PATH} is malformed.")
        raise

CONFIG = load_config()
# --- End of config ---


class DataManager:
    
    def __init__(self, session: Session, provider: DataProviderInterface):
        self.session = session
        self.provider = provider
        self.config = CONFIG['data_fetch']
        
    # --- Internal helpers ---
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

    # --- Asset management ---
    def _get_or_create_asset(self, ticker: str, name: str, asset_class: str) -> Optional[Asset]:
        asset = self.session.query(Asset).filter_by(ticker=ticker).first()
        if asset:
            print(f"Asset found: {asset.name}")
            return asset
        print(f"Asset {ticker} not found, creating it...")
        info_dto = self.provider.get_asset_info(ticker)
        new_asset_data = {'ticker': ticker, 'asset_class': asset_class, 'name': name}
        if info_dto:
            print(f"... Loading extended master data for {ticker}")
            new_asset_data.update({
                'sector': info_dto.sector,
                'industry': info_dto.industry,
                'country': info_dto.country,
                'currency': info_dto.currency,
                'name': info_dto.long_name or name 
            })
        else:
            print(f"WARNING: Could not fetch extended data for {ticker}.")
        try:
            new_asset = Asset(**new_asset_data)
            self.session.add(new_asset)
            self.session.commit()
            print(f"Asset created: {new_asset}")
            return new_asset
        except Exception as e:
            print(f"Error creating asset {ticker}: {e}", file=sys.stderr)
            self.session.rollback()
            return None

    # --- Idempotent upserts, in batches ---
    def _perform_upsert(self,
                        model: DeclarativeMeta,
                        values: list[dict],
                        index_elements: list[str]) -> int:
        """
        Runs an atomic, idempotent upsert for SQLite.
        Returns the number of rows processed.
        """
        if not values:
            return 0 # Nothing to do

        BATCH_SIZE = 500
        total_rows = len(values)
        num_batches = (total_rows // BATCH_SIZE) + (1 if total_rows % BATCH_SIZE > 0 else 0)
        
        try:
            for i in range(0, total_rows, BATCH_SIZE):
                chunk = values[i:i + BATCH_SIZE]
                
                stmt = sqlite_insert(model).values(chunk)
                
                update_cols = [
                    col for col in chunk[0].keys() if col not in index_elements
                ]
                update_set = {
                    col: getattr(stmt.excluded, col) for col in update_cols
                }

                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=index_elements,
                    set_=update_set
                )
                
                self.session.execute(upsert_stmt)
            
            self.session.commit()
            print(f"... {total_rows} rows imported into {model.__tablename__} (upsert in {num_batches} batches).")
            return total_rows

        except Exception as e:
            print(f"... ERROR in the batch upsert into {model.__tablename__}: {e}", file=sys.stderr)
            self.session.rollback()
            raise e  # Re-raised so UpdateResult can catch it


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def update_prices_for_asset(self, asset: Asset, start_date: date | None = None,
                                force_update: bool = False) -> UpdateResult:
        """Updates daily prices for an asset.

        Every row stored carries the provider's name as `source` (D17, D19,
        Part 9), as the rate fetch does; the close itself is the print the
        provider returns, never adjusted here.

        Skips the provider when stored rows already cover the requested range and
        we checked within price_fetch_interval_days. When the range is covered but
        stale, fetches only from the newest stored date forward instead of
        re-downloading the whole window.

        Callers passing an explicit start_date previously bypassed all caching and
        hit the provider unconditionally, so two tools asking for the same window
        fetched it twice.
        """
        try:
            print(f"... checking prices for {asset.ticker}")
            meta = self._get_or_create_metadata(asset.id)

            first_stored, last_stored = self.session.query(
                func.min(DailyPrice.date), func.max(DailyPrice.date)
            ).filter(DailyPrice.asset_id == asset.id).one()

            requested_start = start_date or last_stored or date(2000, 1, 1)

            if requested_start > date.today():
                return UpdateResult(
                    success=True, operation="update_prices", affected_count=0, 
                    entities=[asset.ticker], entity_type="asset", metadata={"status": "up_to_date"}
                )

            # Coverage is "have we ever ASKED the provider for data this far back",
            # not "do we hold a row on or before that date". Those differ whenever
            # the requested start is a weekend, a holiday, or predates the listing:
            # asking for 2023-09-04 (Labor Day) returns 2023-09-05 as the first row,
            # so a first_stored comparison can never be satisfied and the asset
            # refetches its full history on every single call.
            covered = (
                meta.earliest_price_start is not None
                and meta.earliest_price_start <= requested_start
            )
            interval = self.config["price_fetch_interval_days"]

            if covered and not force_update and not self._should_fetch(
                meta.last_price_fetch_time, interval
            ):
                return UpdateResult(
                    success=True, operation="update_prices", affected_count=0,
                    entities=[asset.ticker], entity_type="asset",
                    date_range=(requested_start, last_stored),
                    metadata={"status": "cached",
                              "stored_through": last_stored.isoformat() if last_stored else None}
                )

            # Covered but stale: only the tail is missing. Not covered: full backfill.
            fetch_from = last_stored if (covered and last_stored) else requested_start

            provider_data = self.provider.get_daily_prices(
                ticker=asset.ticker,
                start=fetch_from,
                end=date.today()
            )
            meta.last_price_fetch_time = datetime.utcnow()
            # Record how far back we have now asked. first_stored is included so
            # assets with pre-existing history seed correctly on the first run.
            asked_from = [d for d in (meta.earliest_price_start, fetch_from, first_stored)
                          if d is not None]
            meta.earliest_price_start = min(asked_from)
            
            if not provider_data:
                return UpdateResult(
                    success=True, operation="update_prices", affected_count=0, 
                    entities=[asset.ticker], entity_type="asset", metadata={"status": "no_new_data_from_provider"}
                )

            values_to_upsert = []
            for price_dto in provider_data:
                if price_dto.date < fetch_from:
                    continue 
                values_to_upsert.append({
                    'asset_id': asset.id,
                    'date': price_dto.date,
                    'open': float(price_dto.open), 
                    'high': float(price_dto.high), 
                    'low': float(price_dto.low),
                    'close': float(price_dto.close), 
                    'volume': price_dto.volume,
                    'source': self.provider.name,
                })

            if not values_to_upsert:
                return UpdateResult(
                    success=True, operation="update_prices", affected_count=0, 
                    entities=[asset.ticker], entity_type="asset", metadata={"status": "filtered_empty"}
                )
                
            affected_count = self._perform_upsert(
                model=DailyPrice,
                values=values_to_upsert,
                index_elements=['asset_id', 'date']
            )
            
            return UpdateResult(
                success=True,
                operation="update_prices",
                affected_count=affected_count,
                entities=[asset.ticker],
                entity_type="asset",
                date_range=(fetch_from, date.today()),
                metadata={"provider": self.provider.name}
            )
            
        except Exception as e:
            return UpdateResult(
                success=False,
                operation="update_prices",
                affected_count=0,
                entities=[asset.ticker],
                entity_type="asset",
                error_message=str(e)
            )

    def update_fx_rates(self, base: str, quote: str, start_date: date | None = None,
                        force_update: bool = False) -> UpdateResult:
        """Updates daily spot rates for one pair, beside the price fetch and
        under its rules (expected_values.md D17: a rate is a price source).

        `rate` is units of `base` per one unit of `quote`, stored as the
        provider gives it, with the provider's name as `source`. The cache
        record is fx_fetch_metadata, keyed by the pair: skip the provider when
        we have asked this far back before and checked within
        price_fetch_interval_days; when covered but stale, fetch only from the
        newest stored date forward. Coverage is what was asked, never whether
        a row exists on the date - a weekend start has no row and never will.

        Base equal to quote is no lookup (D17), so no fetch and no row. A
        provider with nothing for the pair stores nothing and says so; the
        raise on a missing rate is the lookup's (quant/fx.py), not this
        method's, the same split as prices.
        """
        pair = f"{base}/{quote}"
        try:
            if base == quote:
                return UpdateResult(
                    success=True, operation="update_fx_rates", affected_count=0,
                    entities=[pair], entity_type="fx_pair",
                    metadata={"status": "same_currency"}
                )

            meta = self.session.get(FxFetchMetadata, (base, quote))
            if meta is None:
                meta = FxFetchMetadata(base=base, quote=quote)
                self.session.add(meta)

            first_stored, last_stored = self.session.query(
                func.min(FxRate.date), func.max(FxRate.date)
            ).filter(FxRate.base == base, FxRate.quote == quote).one()

            requested_start = start_date or last_stored or date(2000, 1, 1)

            if requested_start > date.today():
                return UpdateResult(
                    success=True, operation="update_fx_rates", affected_count=0,
                    entities=[pair], entity_type="fx_pair", metadata={"status": "up_to_date"}
                )

            covered = (
                meta.earliest_start is not None
                and meta.earliest_start <= requested_start
            )
            interval = self.config["price_fetch_interval_days"]

            if covered and not force_update and not self._should_fetch(
                meta.last_fetch_time, interval
            ):
                return UpdateResult(
                    success=True, operation="update_fx_rates", affected_count=0,
                    entities=[pair], entity_type="fx_pair",
                    date_range=(requested_start, last_stored),
                    metadata={"status": "cached",
                              "stored_through": last_stored.isoformat() if last_stored else None}
                )

            fetch_from = last_stored if (covered and last_stored) else requested_start

            provider_data = self.provider.get_fx_rates(
                base=base, quote=quote, start=fetch_from, end=date.today()
            )
            meta.last_fetch_time = datetime.utcnow()
            asked_from = [d for d in (meta.earliest_start, fetch_from, first_stored)
                          if d is not None]
            meta.earliest_start = min(asked_from)
            self.session.commit()

            if not provider_data:
                return UpdateResult(
                    success=True, operation="update_fx_rates", affected_count=0,
                    entities=[pair], entity_type="fx_pair",
                    metadata={"status": "no_new_data_from_provider"}
                )

            values_to_upsert = [
                {
                    'base': base,
                    'quote': quote,
                    'date': dto.date,
                    'rate': float(dto.rate),
                    'source': self.provider.name,
                }
                for dto in provider_data
                if dto.date >= fetch_from
            ]

            if not values_to_upsert:
                return UpdateResult(
                    success=True, operation="update_fx_rates", affected_count=0,
                    entities=[pair], entity_type="fx_pair", metadata={"status": "filtered_empty"}
                )

            affected_count = self._perform_upsert(
                model=FxRate,
                values=values_to_upsert,
                index_elements=['base', 'quote', 'date']
            )

            return UpdateResult(
                success=True,
                operation="update_fx_rates",
                affected_count=affected_count,
                entities=[pair],
                entity_type="fx_pair",
                date_range=(fetch_from, date.today()),
                metadata={"provider": self.provider.name}
            )

        except Exception as e:
            self.session.rollback()
            return UpdateResult(
                success=False,
                operation="update_fx_rates",
                affected_count=0,
                entities=[pair],
                entity_type="fx_pair",
                error_message=str(e)
            )

    def update_dividends_for_asset(self, asset: Asset) -> UpdateResult:
        try:
            print(f"... checking dividends for {asset.ticker}")
            last_ex_date = self.session.query(func.max(Dividend.ex_date)).filter(
                Dividend.asset_id == asset.id
            ).scalar()
            
            dividends_data = self.provider.get_dividends(asset.ticker, since=last_ex_date)
            if not dividends_data:
                return UpdateResult(True, "update_dividends", 0, [asset.ticker], "asset", metadata={"status": "no_data"})

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
                return UpdateResult(True, "update_dividends", 0, [asset.ticker], "asset", metadata={"status": "filtered"})

            affected_count = self._perform_upsert(
                model=Dividend,
                values=values_to_upsert,
                index_elements=['asset_id', 'ex_date']
            )
            return UpdateResult(True, "update_dividends", affected_count, [asset.ticker], "asset")

        except Exception as e:
            return UpdateResult(False, "update_dividends", 0, [asset.ticker], "asset", error_message=str(e))

    def update_splits_for_asset(self, asset: Asset) -> UpdateResult:
        try:
            print(f"... checking splits for {asset.ticker}")
            last_split_date = self.session.query(func.max(CorporateAction.date)).filter(
                CorporateAction.asset_id == asset.id,
                CorporateAction.action_type == 'Split'
            ).scalar()
            
            splits_data = self.provider.get_splits(asset.ticker, since=last_split_date)
            if not splits_data:
                return UpdateResult(True, "update_splits", 0, [asset.ticker], "asset")

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
                return UpdateResult(True, "update_splits", 0, [asset.ticker], "asset")
                
            affected_count = self._perform_upsert(
                model=CorporateAction,
                values=values_to_upsert,
                index_elements=['asset_id', 'date', 'action_type']
            )
            return UpdateResult(True, "update_splits", affected_count, [asset.ticker], "asset")
            
        except Exception as e:
            return UpdateResult(False, "update_splits", 0, [asset.ticker], "asset", error_message=str(e))

    def update_shares_history_for_asset(self, asset: Asset, force_update: bool = False) -> UpdateResult:
        try:
            print(f"... checking the shares history for {asset.ticker}")
            meta = self._get_or_create_metadata(asset.id)
            interval = self.config.get('shares_fetch_interval_days', 30)

            if not force_update and not self._should_fetch(meta.last_shares_fetch_time, interval):
                return UpdateResult(True, "update_shares", 0, [asset.ticker], "asset", metadata={"reason": "skipped_interval"})

            since_date = self.session.query(func.max(SharesHistory.date)).filter(
                SharesHistory.asset_id == asset.id
            ).scalar()
            
            hist_data = self.provider.get_shares_history(asset.ticker, since=since_date)

            if not hist_data:
                meta.last_shares_fetch_time = datetime.utcnow()
                self.session.commit()
                return UpdateResult(True, "update_shares", 0, [asset.ticker], "asset", metadata={"status": "no_data"})

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

            affected_count = 0
            if values_to_upsert:
                affected_count = self._perform_upsert(
                    model=SharesHistory,
                    values=values_to_upsert,
                    index_elements=['asset_id', 'date']
                )

            # Commit the metadata
            meta.last_shares_fetch_time = datetime.utcnow()
            self.session.commit()
            
            return UpdateResult(True, "update_shares", affected_count, [asset.ticker], "asset")
            
        except Exception as e:
            # Roll back if the session is still open
            try:
                self.session.rollback()
            except:
                pass
            return UpdateResult(False, "update_shares", 0, [asset.ticker], "asset", error_message=str(e))

    def update_quarterly_earnings_for_asset(self, asset: Asset, force_update: bool = False) -> UpdateResult:
        try:
            print(f"... checking quarterly reports for {asset.ticker}")
            meta = self._get_or_create_metadata(asset.id)
            interval = self.config.get('earnings_fetch_interval_days', 7)

            if not force_update and not self._should_fetch(meta.last_earnings_fetch_time, interval):
                return UpdateResult(True, "update_earnings", 0, [asset.ticker], "asset", metadata={"reason": "skipped_interval"})

            since_date = self.session.query(func.max(QuarterlyEarnings.report_date)).filter(
                QuarterlyEarnings.asset_id == asset.id
            ).scalar()

            provider_data = self.provider.get_quarterly_earnings(asset.ticker, since=since_date)

            if not provider_data:
                meta.last_earnings_fetch_time = datetime.utcnow()
                self.session.commit()
                return UpdateResult(True, "update_earnings", 0, [asset.ticker], "asset")

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

            affected_count = 0
            if values_to_upsert:
                affected_count = self._perform_upsert(
                    model=QuarterlyEarnings,
                    values=values_to_upsert,
                    index_elements=['asset_id', 'report_date']
                )

            # Commit the metadata
            meta.last_earnings_fetch_time = datetime.utcnow()
            if max_report_date and max_report_date != since_date:
                meta.last_earnings_report_date = max_report_date
            
            self.session.commit()
            return UpdateResult(True, "update_earnings", affected_count, [asset.ticker], "asset")
            
        except Exception as e:
            try:
                self.session.rollback()
            except:
                pass
            return UpdateResult(False, "update_earnings", 0, [asset.ticker], "asset", error_message=str(e))

    def force_update_asset_info(self, asset: Asset) -> UpdateResult:
        try:
            print(f"  > Forcing a master-data update for {asset.ticker}...")
            info_dto = self.provider.get_asset_info(asset.ticker)
            if not info_dto:
                return UpdateResult(False, "update_asset_info", 0, [asset.ticker], "asset", error_message="No data from provider")

            asset.sector = info_dto.sector
            asset.industry = info_dto.industry
            asset.country = info_dto.country
            asset.currency = info_dto.currency
            if info_dto.long_name:
                asset.name = info_dto.long_name
            
            self.session.commit()
            print(f"  > {asset.ticker} updated.")
            return UpdateResult(True, "update_asset_info", 1, [asset.ticker], "asset")
            
        except Exception as e:
            self.session.rollback()
            return UpdateResult(False, "update_asset_info", 0, [asset.ticker], "asset", error_message=str(e))

    def update_fundamental_data(self, asset: Asset, force_update: bool = False) -> UpdateResult:
        try:
            print(f"... checking fundamentals for {asset.ticker}")
            meta = self._get_or_create_metadata(asset.id)
            interval = self.config.get('profile_fetch_interval_days', 30)

            if not force_update and not self._should_fetch(meta.last_profile_fetch_time, interval):
                return UpdateResult(True, "update_fundamentals", 0, [asset.ticker], "asset", metadata={"reason": "skipped_interval"})

            dto = self.provider.get_fundamental_data(asset.ticker)
            if not dto:
                meta.last_profile_fetch_time = datetime.utcnow()
                self.session.commit()
                return UpdateResult(True, "update_fundamentals", 0, [asset.ticker], "asset", metadata={"status": "no_data"})

            db_fund = self.session.query(Fundamentals).filter_by(asset_id=asset.id).first()
            if not db_fund:
                db_fund = Fundamentals(asset_id=asset.id)
                self.session.add(db_fund)
            
            db_fund.beta = float(dto.beta) if dto.beta is not None else None
            db_fund.last_updated = datetime.utcnow() 

            meta.last_profile_fetch_time = datetime.utcnow()

            self.session.commit()
            print(f"... Fundamentals (beta) for {asset.ticker} stored.")
            return UpdateResult(True, "update_fundamentals", 1, [asset.ticker], "asset")
            
        except Exception as e:
            self.session.rollback()
            return UpdateResult(False, "update_fundamentals", 0, [asset.ticker], "asset", error_message=str(e))

    def update_financial_statements_for_asset(
        self,
        asset: Asset,
        report_type: str,
        period_type: str,
    ) -> UpdateResult:
        """
        Fetches financial statements for an asset and stores them
        idempotently in the financial_statements table.
        """
        try:
            print(f"... checking financial statements for {asset.ticker} ({report_type}, {period_type})")

            last_date = (
                self.session.query(func.max(FinancialStatement.date))
                .filter(
                    FinancialStatement.asset_id == asset.id,
                    FinancialStatement.report_type == report_type,
                    FinancialStatement.period_type == period_type,
                )
                .scalar()
            )

            provider_data = self.provider.get_financial_statements(
                ticker=asset.ticker,
                report_type=report_type,
                period_type=period_type,
                since=last_date,
            )

            if not provider_data:
                return UpdateResult(True, "update_financial_statements", 0, [asset.ticker], "asset", metadata={"report_type": report_type})

            values_to_upsert: list[dict] = []

            for dto in provider_data:
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
                return UpdateResult(True, "update_financial_statements", 0, [asset.ticker], "asset", metadata={"report_type": report_type})

            affected_count = self._perform_upsert(
                model=FinancialStatement,
                values=values_to_upsert,
                index_elements=["asset_id", "date", "report_type", "period_type"],
            )
            
            return UpdateResult(True, "update_financial_statements", affected_count, [asset.ticker], "asset", metadata={"report_type": report_type})

        except Exception as e:
            return UpdateResult(False, "update_financial_statements", 0, [asset.ticker], "asset", error_message=str(e))
        

    # Macro data, through the same session, upsert and UpdateResult as the
    # asset methods above.

    # ==================== UPDATE METHODS ====================
    
    def update_macro_data(
        self, 
        indicators: List[str], 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> UpdateResult:
        """
        Fetches macro data from the provider and stores it in the database.

        The same pattern as update_prices_for_asset():
        1. the provider returns List[ProviderMacroData]
        2. transformed to List[dict] for the upsert
        3. _perform_upsert() with index_elements=['date', 'indicator']
        4. an UpdateResult

        Args:
            indicators: the indicators ["VIX", "TNX_10Y", etc.]
            start_date: (default: 30 days back)
            end_date: (default: today)

        Returns:
            UpdateResult with affected_count
        """
        # Default: the last 30 days
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        try:
            all_values = []
            
            for indicator in indicators:
                # The provider fetches the data
                provider_data = self.provider.get_macro_indicator(
                    indicator=indicator,
                    start=start_date,
                    end=end_date
                )
                
                # Transform to the upsert shape
                for dto in provider_data:
                    all_values.append({
                        'date': dto.date,
                        'indicator': dto.indicator,
                        'value': dto.value,
                        'source': dto.source,
                        'created_at': datetime.utcnow()
                    })
            
            if not all_values:
                return UpdateResult(
                    success=True,
                    operation="update_macro_data",
                    affected_count=0,
                    entities=indicators,
                    entity_type="macro_indicator",
                    metadata={"reason": "no_data_from_provider"}
                )
            
            # Batch upsert through the same method as the asset tables
            affected_count = self._perform_upsert(
                MacroData, 
                all_values, 
                index_elements=['date', 'indicator']
            )
            
            return UpdateResult(
                success=True,
                operation="update_macro_data",
                affected_count=affected_count,
                entities=indicators,
                entity_type="macro_indicator",
                metadata={
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "total_data_points": len(all_values)
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating macro data: {e}")
            self.session.rollback()
            return UpdateResult(
                success=False,
                operation="update_macro_data",
                affected_count=0,
                entities=indicators,
                entity_type="macro_indicator",
                error_message=str(e)
            )
    
    def update_vix(self, days: int = 30) -> UpdateResult:
        """Convenience: update the VIX data only."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return self.update_macro_data(["VIX"], start_date, end_date)
    
    def update_treasury_yields(self, days: int = 30) -> UpdateResult:
        """Convenience: update every Treasury yield."""
        indicators = ["TNX_10Y", "TYX_30Y", "IRX_3M"]
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return self.update_macro_data(indicators, start_date, end_date)
    
    def update_all_macro_data(self, days: int = 30) -> UpdateResult:
        """Convenience: update every macro indicator."""
        indicators = ["VIX", "TNX_10Y", "TYX_30Y", "IRX_3M", "USD_INDEX", "GOLD"]
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return self.update_macro_data(indicators, start_date, end_date)
    
    # ==================== QUERY METHODS ====================
    
    def get_latest_macro_values(self) -> Dict[str, Any]:
        """
        Fetches the latest value of every macro indicator from the database.

        Returns:
            Dict of indicator -> {value, date}

        Hot potato: aggregated figures come back, no raw rows
        """
        try:
            # Subquery: the newest date per indicator
            subquery = self.session.query(
                MacroData.indicator,
                func.max(MacroData.date).label('max_date')
            ).group_by(MacroData.indicator).subquery()
            
            # Join for the newest values
            latest_records = self.session.query(MacroData).join(
                subquery,
                (MacroData.indicator == subquery.c.indicator) &
                (MacroData.date == subquery.c.max_date)
            ).all()
            
            result = {}
            for record in latest_records:
                result[record.indicator] = {
                    "value": record.value,
                    "date": record.date.isoformat()
                }
            
            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "indicators": result
            }
            
        except Exception as e:
            logger.error(f"Error getting latest macro values: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "indicators": {}
            }
    
    def get_macro_history(
        self, 
        indicator: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Fetches the history of one indicator.

        Returns:
            Dict with the list of values (hot potato)
        """
        try:
            start_date = date.today() - timedelta(days=days)
            
            records = self.session.query(MacroData).filter(
                MacroData.indicator == indicator,
                MacroData.date >= start_date
            ).order_by(MacroData.date).all()
            
            if not records:
                return {
                    "success": True,
                    "indicator": indicator,
                    "count": 0,
                    "data": [],
                    "metadata": {"reason": "no_data_in_db"}
                }
            
            data = [
                {"date": r.date.isoformat(), "value": r.value}
                for r in records
            ]
            
            return {
                "success": True,
                "indicator": indicator,
                "count": len(records),
                "latest_value": records[-1].value,
                "latest_date": records[-1].date.isoformat(),
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error getting macro history: {e}")
            return {
                "success": False,
                "indicator": indicator,
                "error_message": str(e)
            }
    
    def get_vix_with_regime(self) -> Dict[str, Any]:
        """
        Fetches the VIX with a regime classification.

        Returns:
            Dict with the VIX value, regime, trend and percentile

        Hot potato: the business logic is applied here and the agent
        receives the finished analysis
        """
        try:
            # The VIX history of the last 30 days
            history = self.get_macro_history("VIX", days=30)
            
            if not history.get("success") or history.get("count", 0) == 0:
                return {
                    "success": False,
                    "error_message": "No VIX data in database"
                }
            
            values = [d["value"] for d in history["data"]]
            current_vix = values[-1]
            avg_30d = sum(values) / len(values)
            
            # The percentile
            sorted_values = sorted(values)
            rank = sum(1 for v in sorted_values if v <= current_vix)
            percentile = int((rank / len(values)) * 100)
            
            # The regime
            if current_vix < 15:
                regime = "low"
            elif current_vix < 25:
                regime = "normal"
            elif current_vix < 35:
                regime = "elevated"
            else:
                regime = "crisis"
            
            # The trend (the last 5 days against the previous 5)
            if len(values) >= 10:
                recent_avg = sum(values[-5:]) / 5
                previous_avg = sum(values[-10:-5]) / 5
                if recent_avg > previous_avg * 1.1:
                    trend = "rising"
                elif recent_avg < previous_avg * 0.9:
                    trend = "falling"
                else:
                    trend = "stable"
            else:
                trend = "unknown"
            
            return {
                "success": True,
                "current_vix": current_vix,
                "regime": regime,
                "percentile_30d": percentile,
                "average_30d": round(avg_30d, 2),
                "trend": trend,
                "date": history["latest_date"]
            }
            
        except Exception as e:
            logger.error(f"Error getting VIX regime: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }
    
    def get_yield_curve_status(self) -> Dict[str, Any]:
        """
        Fetches the yield curve status with an inversion warning.

        Returns:
            Dict with the yields, slope, status and recession signal
        """
        try:
            latest = self.get_latest_macro_values()
            
            if not latest.get("success"):
                return latest
            
            indicators = latest.get("indicators", {})
            
            t10y = indicators.get("TNX_10Y", {}).get("value")
            t3m = indicators.get("IRX_3M", {}).get("value")
            t30y = indicators.get("TYX_30Y", {}).get("value")
            
            result = {
                "success": True,
                "treasury_10y": t10y,
                "treasury_3m": t3m,
                "treasury_30y": t30y
            }
            
            # The slope (10Y - 3M)
            if t10y is not None and t3m is not None:
                slope = t10y - t3m
                result["slope_10y_3m"] = round(slope, 4)
                
                # The status
                if slope < -0.5:
                    status = "deeply_inverted"
                    recession_signal = True
                elif slope < 0:
                    status = "inverted"
                    recession_signal = True
                elif slope < 0.5:
                    status = "flat"
                    recession_signal = False
                elif slope < 1.5:
                    status = "normal"
                    recession_signal = False
                else:
                    status = "steep"
                    recession_signal = False
                
                result["status"] = status
                result["recession_signal"] = recession_signal
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting yield curve status: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }
        
    # ==================== PUBLIC FACADE (The missing piece) ====================

    def fetch_price_data(
        self, 
        ticker: str, 
        start_date: Optional[datetime | date] = None, 
        end_date: Optional[datetime | date] = None
    ) -> UpdateResult:
        """
        High-level entry point to fetch data for a ticker string.
        
        This makes the DataManager user-friendly by handling the
        Asset object creation internally.
        """
        # 1. Normalize dates
        if isinstance(start_date, datetime):
            start_date = start_date.date()
            
        # 2. Ensure Asset Exists (The "Facade" magic)
        # We assume Equity/USD as defaults, or let the provider enrich it later
        asset = self._get_or_create_asset(ticker, name=ticker, asset_class="Equity")
        
        if not asset:
            return UpdateResult(
                success=False,
                operation="fetch_price_data",
                affected_count=0,
                entities=[ticker],
                entity_type="asset",
                error_message=f"Could not create or find asset: {ticker}"
            )
            
        # 3. Delegate to your existing strict logic
        return self.update_prices_for_asset(asset, start_date=start_date)

# Singleton instance
_data_manager_instance = None


def get_data_manager() -> 'DataManager':
    """
    Factory function to get DataManager singleton instance.
    
    Creates the DataManager with proper session and provider setup.
    Uses singleton pattern to avoid multiple DB connections.
    
    Returns:
        DataManager instance
        
    Usage:
        from portfolio_tool.data_manager import get_data_manager
        
        dm = get_data_manager()
        result = dm.update_prices_for_asset(...)
    """
    global _data_manager_instance
    
    if _data_manager_instance is None:
        from portfolio_tool.database_setup import get_session
        from portfolio_tool.providers.yfinance_provider import YFinanceProvider
        from portfolio_tool.services.quota_manager import DatabaseQuotaManager
        
        # Create session
        session = get_session()
        
        # Create provider with quota manager
        quota_manager = DatabaseQuotaManager(provider_name="yfinance", daily_limit=2000)
        provider = YFinanceProvider(quota_manager=quota_manager)
        
        # Create DataManager
        _data_manager_instance = DataManager(session=session, provider=provider)
    
    return _data_manager_instance


def reset_data_manager():
    """
    Reset the singleton instance (useful for testing).
    """
    global _data_manager_instance
    if _data_manager_instance is not None:
        try:
            _data_manager_instance.session.close()
        except:
            pass
    _data_manager_instance = None