"""
Covariance Matrix Estimation for Portfolio Optimization.

This module provides various methods for estimating covariance matrices:
- Sample covariance (standard)
- Shrinkage estimators (Ledoit-Wolf)
- Exponentially weighted covariance

Why different methods?
- Sample covariance is unstable with limited data or many assets
- Shrinkage reduces estimation error by pulling towards a structured target
- Exponential weighting gives more weight to recent observations

Design Principles:
- All estimators return the same CovarianceResult format
- Include quality metrics (condition number) for stability assessment
- Warnings for edge cases (high correlation, insufficient data)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


# Constants
TRADING_DAYS_PER_YEAR = 252


class CovarianceMethod(str, Enum):
    """Available covariance estimation methods."""
    SAMPLE = "sample"
    SHRINKAGE = "shrinkage"
    EXPONENTIAL = "exponential"


@dataclass
class CovarianceResult:
    """
    Result from covariance matrix estimation.
    
    Includes both the matrices and quality metrics for assessment.
    """
    success: bool
    tickers: List[str]
    
    # Core outputs
    covariance_matrix: Optional[pd.DataFrame] = None
    correlation_matrix: Optional[pd.DataFrame] = None
    
    # Per-asset metrics
    annualized_volatilities: Optional[Dict[str, float]] = None
    
    # Estimation details
    method: CovarianceMethod = CovarianceMethod.SAMPLE
    estimation_period: Optional[str] = None
    num_observations: int = 0
    
    # Shrinkage-specific
    shrinkage_intensity: Optional[float] = None  # 0 = no shrinkage, 1 = full shrinkage
    
    # Quality metrics
    condition_number: Optional[float] = None  # High = unstable
    is_positive_definite: bool = True
    
    # Warnings and errors
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization and LLM consumption."""
        result = {
            "success": self.success,
            "tickers": self.tickers,
            "method": self.method.value,
            "num_observations": self.num_observations,
            "estimation_period": self.estimation_period,
        }
        
        if self.annualized_volatilities:
            result["annualized_volatilities"] = {
                k: f"{v:.2%}" for k, v in self.annualized_volatilities.items()
            }
            # Raw floats alongside the display strings. Anything doing further
            # arithmetic reads this key; the formatted one is for display only.
            # The ImportError fallback in data_agent.py already emits both.
            result["annualized_volatilities_raw"] = {
                k: float(v) for k, v in self.annualized_volatilities.items()
            }
        
        if self.condition_number is not None:
            result["condition_number"] = round(self.condition_number, 2)
            if self.condition_number > 100:
                result["stability_warning"] = "High condition number - matrix may be unstable"
        
        if self.shrinkage_intensity is not None:
            result["shrinkage_intensity"] = f"{self.shrinkage_intensity:.2%}"
        
        result["is_positive_definite"] = self.is_positive_definite
        
        if self.warnings:
            result["warnings"] = self.warnings
        if self.error_message:
            result["error_message"] = self.error_message
        
        # FIX: Include BOTH covariance and correlation matrices (limited to avoid huge output)
        if len(self.tickers) <= 10:
            # Include covariance matrix
            if self.covariance_matrix is not None:
                result["covariance_matrix"] = {
                    ticker: {
                        t2: float(self.covariance_matrix.loc[ticker, t2])
                        for t2 in self.tickers
                    }
                    for ticker in self.tickers
                }
            
            # Include correlation matrix
            if self.correlation_matrix is not None:
                result["correlation_matrix"] = {
                    ticker: {
                        t2: round(self.correlation_matrix.loc[ticker, t2], 3)
                        for t2 in self.tickers
                    }
                    for ticker in self.tickers
                }
        
        return result


        # EXPLANATION:
        # The fix adds the covariance_matrix to the to_dict() output.
        # It uses the same pattern as correlation_matrix but converts to float (not rounded)
        # since covariance values need more precision than correlations.
        #
        # This way, when data_agent.py calls result.to_dict(), it will get BOTH:
        # - covariance_matrix (needed by OptimizationAgent)
        # - correlation_matrix (nice to have for analysis)
    
    def get_covariance_as_nested_dict(self) -> Dict[str, Dict[str, float]]:
        """Get covariance matrix as nested dictionary."""
        if self.covariance_matrix is None:
            return {}
        
        return {
            ticker: {
                t2: float(self.covariance_matrix.loc[ticker, t2])
                for t2 in self.tickers
            }
            for ticker in self.tickers
        }


class CovarianceEstimator:
    """
    Unified interface for covariance matrix estimation.
    
    Usage:
        estimator = CovarianceEstimator(method="shrinkage")
        result = estimator.estimate(returns_df)
    """
    
    def __init__(
        self,
        method: Union[str, CovarianceMethod] = CovarianceMethod.SAMPLE,
        annualize: bool = True,
        trading_days: int = TRADING_DAYS_PER_YEAR,
        min_observations: int = 60,
    ):
        """
        Initialize covariance estimator.
        
        Args:
            method: Estimation method to use
            annualize: Whether to annualize the covariance matrix
            trading_days: Number of trading days per year for annualization
            min_observations: Minimum required observations
        """
        if isinstance(method, str):
            method = CovarianceMethod(method)
        
        self.method = method
        self.annualize = annualize
        self.trading_days = trading_days
        self.min_observations = min_observations
    
    def estimate(self, returns: pd.DataFrame) -> CovarianceResult:
        """
        Estimate covariance matrix using the configured method.
        
        Args:
            returns: DataFrame of returns (each column is an asset)
            
        Returns:
            CovarianceResult with matrices and quality metrics
        """
        warnings = []
        
        # Validate input
        if returns.empty:
            return CovarianceResult(
                success=False,
                tickers=list(returns.columns),
                error_message="Empty returns DataFrame"
            )
        
        tickers = list(returns.columns)
        n_obs = len(returns)
        
        if n_obs < self.min_observations:
            warnings.append(
                f"Only {n_obs} observations (recommended minimum: {self.min_observations})"
            )
        
        # Drop NaN rows (use common period only)
        returns_clean = returns.dropna()
        n_clean = len(returns_clean)
        
        if n_clean < self.min_observations:
            warnings.append(
                f"After removing NaN: only {n_clean} common observations"
            )
        
        if n_clean < 2:
            return CovarianceResult(
                success=False,
                tickers=tickers,
                error_message="Insufficient observations after cleaning",
                warnings=warnings
            )
        
        # Estimate covariance based on method
        try:
            if self.method == CovarianceMethod.SAMPLE:
                cov_matrix, shrinkage = self._sample_covariance(returns_clean)
            elif self.method == CovarianceMethod.SHRINKAGE:
                cov_matrix, shrinkage = self._shrinkage_covariance(returns_clean)
            elif self.method == CovarianceMethod.EXPONENTIAL:
                cov_matrix, shrinkage = self._exponential_covariance(returns_clean)
            else:
                return CovarianceResult(
                    success=False,
                    tickers=tickers,
                    error_message=f"Unknown method: {self.method}"
                )
        except Exception as e:
            return CovarianceResult(
                success=False,
                tickers=tickers,
                error_message=f"Estimation failed: {str(e)}",
                warnings=warnings
            )
        
        # Annualize if requested
        if self.annualize:
            cov_matrix = cov_matrix * self.trading_days
        
        # Calculate correlation matrix
        std_devs = np.sqrt(np.diag(cov_matrix.values))
        std_outer = np.outer(std_devs, std_devs)
        corr_values = cov_matrix.values / std_outer
        corr_matrix = pd.DataFrame(corr_values, index=tickers, columns=tickers)
        
        # Calculate annualized volatilities
        vols = {ticker: float(std_devs[i]) for i, ticker in enumerate(tickers)}
        
        # Quality metrics
        try:
            cond_number = np.linalg.cond(cov_matrix.values)
        except:
            cond_number = np.inf
        
        is_pd = self._is_positive_definite(cov_matrix.values)
        
        # Check for extreme correlations
        off_diag = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
        if len(off_diag) > 0:
            max_corr = np.max(np.abs(off_diag))
            if max_corr > 0.95:
                warnings.append(f"Very high correlation detected: {max_corr:.2f}")
        
        if cond_number > 100:
            warnings.append(f"High condition number ({cond_number:.0f}) - matrix may be unstable")
        
        if not is_pd:
            warnings.append("Matrix is not positive definite - may cause optimization issues")
        
        # Build estimation period string
        if hasattr(returns_clean.index[0], 'strftime'):
            start = returns_clean.index[0].strftime('%Y-%m-%d')
            end = returns_clean.index[-1].strftime('%Y-%m-%d')
        else:
            start = str(returns_clean.index[0])
            end = str(returns_clean.index[-1])
        
        return CovarianceResult(
            success=True,
            tickers=tickers,
            covariance_matrix=cov_matrix,
            correlation_matrix=corr_matrix,
            annualized_volatilities=vols,
            method=self.method,
            estimation_period=f"{start} to {end}",
            num_observations=n_clean,
            shrinkage_intensity=shrinkage,
            condition_number=float(cond_number),
            is_positive_definite=is_pd,
            warnings=warnings
        )
    
    def _sample_covariance(
        self, returns: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Optional[float]]:
        """Calculate sample covariance matrix."""
        cov_matrix = returns.cov()
        return cov_matrix, None
    
    def _shrinkage_covariance(
        self, returns: pd.DataFrame
    ) -> Tuple[pd.DataFrame, float]:
        """
        Calculate Ledoit-Wolf shrinkage covariance matrix.
        
        Shrinks sample covariance towards a structured target (diagonal).
        The shrinkage intensity is estimated optimally.
        
        Reference:
        Ledoit & Wolf (2004) "A Well-Conditioned Estimator for Large-Dimensional
        Covariance Matrices"
        """
        X = returns.values
        n, p = X.shape
        
        # Center the data
        X = X - X.mean(axis=0)
        
        # Sample covariance
        sample_cov = (X.T @ X) / n
        
        # Target: scaled identity (average variance on diagonal)
        mu = np.trace(sample_cov) / p
        target = mu * np.eye(p)
        
        # Calculate optimal shrinkage intensity
        # Based on Ledoit-Wolf formula
        
        # Sum of squared sample correlations
        delta = sample_cov - target
        delta_sq_sum = np.sum(delta ** 2)
        
        # Estimate of the expected squared error
        X_squared = X ** 2
        gamma_hat = np.sum(
            (X_squared.T @ X_squared) / n - 2 * (X.T @ X) * sample_cov / n + sample_cov ** 2
        ) / n
        
        # Kappa (scaling factor)
        kappa = (gamma_hat - delta_sq_sum / n) / ((n - 1) * delta_sq_sum / n / n)
        
        # Bound shrinkage between 0 and 1
        shrinkage = max(0, min(1, kappa))
        
        # Shrunk covariance
        shrunk_cov = shrinkage * target + (1 - shrinkage) * sample_cov
        
        cov_df = pd.DataFrame(shrunk_cov, index=returns.columns, columns=returns.columns)
        
        return cov_df, float(shrinkage)
    
    def _exponential_covariance(
        self, returns: pd.DataFrame,
        span: int = 60,
        min_periods: int = 20
    ) -> Tuple[pd.DataFrame, Optional[float]]:
        """
        Calculate exponentially weighted covariance matrix.
        
        Gives more weight to recent observations.
        
        Args:
            span: Decay in terms of center of mass (higher = slower decay)
            min_periods: Minimum observations required
        """
        # Use pandas ewm for exponential weighting
        ewm = returns.ewm(span=span, min_periods=min_periods)
        cov_matrix = ewm.cov().iloc[-len(returns.columns):]
        
        # Reset index to just have tickers
        cov_matrix = cov_matrix.droplevel(0)
        
        return cov_matrix, None
    
    def _is_positive_definite(self, matrix: np.ndarray) -> bool:
        """Check if matrix is positive definite."""
        try:
            np.linalg.cholesky(matrix)
            return True
        except np.linalg.LinAlgError:
            return False


def calculate_sample_covariance(
    returns: pd.DataFrame,
    annualize: bool = True,
    trading_days: int = TRADING_DAYS_PER_YEAR
) -> CovarianceResult:
    """
    Convenience function for sample covariance estimation.
    
    Args:
        returns: Returns DataFrame
        annualize: Whether to annualize
        trading_days: Trading days per year
        
    Returns:
        CovarianceResult
    """
    estimator = CovarianceEstimator(
        method=CovarianceMethod.SAMPLE,
        annualize=annualize,
        trading_days=trading_days
    )
    return estimator.estimate(returns)


def calculate_shrinkage_covariance(
    returns: pd.DataFrame,
    annualize: bool = True,
    trading_days: int = TRADING_DAYS_PER_YEAR
) -> CovarianceResult:
    """
    Convenience function for Ledoit-Wolf shrinkage covariance estimation.
    
    Recommended for:
    - Limited historical data (< 5 years)
    - Many assets (> 10)
    - Suspected multicollinearity
    
    Args:
        returns: Returns DataFrame
        annualize: Whether to annualize
        trading_days: Trading days per year
        
    Returns:
        CovarianceResult
    """
    estimator = CovarianceEstimator(
        method=CovarianceMethod.SHRINKAGE,
        annualize=annualize,
        trading_days=trading_days
    )
    return estimator.estimate(returns)


def calculate_exponential_covariance(
    returns: pd.DataFrame,
    annualize: bool = True,
    trading_days: int = TRADING_DAYS_PER_YEAR
) -> CovarianceResult:
    """
    Convenience function for exponentially weighted covariance estimation.
    
    Recommended for:
    - When recent data is more relevant
    - Detecting regime changes
    - TAA applications
    
    Args:
        returns: Returns DataFrame
        annualize: Whether to annualize
        trading_days: Trading days per year
        
    Returns:
        CovarianceResult
    """
    estimator = CovarianceEstimator(
        method=CovarianceMethod.EXPONENTIAL,
        annualize=annualize,
        trading_days=trading_days
    )
    return estimator.estimate(returns)


def make_positive_definite(
    cov_matrix: pd.DataFrame,
    method: str = "nearest"
) -> pd.DataFrame:
    """
    Make a covariance matrix positive definite if it isn't.
    
    This can happen due to numerical issues or data problems.
    
    Args:
        cov_matrix: Input covariance matrix
        method: "nearest" uses nearest PD matrix, "eigenvalue" adjusts eigenvalues
        
    Returns:
        Positive definite covariance matrix
    """
    matrix = cov_matrix.values
    
    # Check if already PD
    try:
        np.linalg.cholesky(matrix)
        return cov_matrix
    except np.linalg.LinAlgError:
        pass
    
    if method == "eigenvalue":
        # Eigenvalue adjustment method
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
        eigenvalues = np.maximum(eigenvalues, 1e-10)  # Ensure positive
        matrix_pd = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    elif method == "nearest":
        # Higham (2002) nearest positive definite matrix
        # Simplified version
        B = (matrix + matrix.T) / 2
        _, s, V = np.linalg.svd(B)
        H = V.T @ np.diag(s) @ V
        matrix_pd = (B + H) / 2
        matrix_pd = (matrix_pd + matrix_pd.T) / 2
        
        # Ensure positive eigenvalues
        spacing = np.spacing(np.linalg.norm(matrix_pd))
        I = np.eye(matrix_pd.shape[0])
        k = 1
        while True:
            try:
                np.linalg.cholesky(matrix_pd)
                break
            except np.linalg.LinAlgError:
                min_eig = np.min(np.real(np.linalg.eigvals(matrix_pd)))
                matrix_pd += I * (-min_eig * k**2 + spacing)
                k += 1
                if k > 100:
                    break
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return pd.DataFrame(matrix_pd, index=cov_matrix.index, columns=cov_matrix.columns)
