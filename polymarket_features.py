"""
Polymarket Feature Engineering Module

This module creates features from Polymarket prediction market data
to improve call center volume forecasting.

Author: Claude
Date: 2025-11-19
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')


class PolymarketFeatureEngine:
    """
    Feature engineering for Polymarket prediction market data

    Expected Input Data Format:
    ---------------------------
    Date | Market | Strike | Probability | Volume | Current_BTC_Price
    2024-01-15 | BTC-Feb-2024 | 50000 | 0.82 | 145000 | 48500
    2024-01-15 | BTC-Feb-2024 | 60000 | 0.45 | 98000 | 48500
    2024-01-15 | BTC-Feb-2024 | 70000 | 0.18 | 52000 | 48500

    Or Simplified Format (if you only have probabilities):
    --------------------------------------------------------
    Date | prob_btc_50k | prob_btc_60k | prob_btc_70k | Current_BTC_Price
    2024-01-15 | 0.82 | 0.45 | 0.18 | 48500
    """

    def __init__(self,
                 strike_levels: List[int] = [50000, 60000, 70000, 80000],
                 lookback_windows: List[int] = [1, 3, 7, 14]):
        """
        Initialize feature engine

        Args:
            strike_levels: Bitcoin price levels to track probabilities for
            lookback_windows: Windows for calculating probability momentum
        """
        self.strike_levels = strike_levels
        self.lookback_windows = lookback_windows
        self.feature_names_ = []

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate all Polymarket features from raw data

        Args:
            df: DataFrame with Polymarket data (wide format)
               Expects columns like: Date, prob_50000, prob_60000, etc.

        Returns:
            DataFrame with all engineered features
        """
        features = pd.DataFrame(index=df.index)

        # Approach 1: Direct Probability Features
        prob_features = self._create_probability_features(df)
        features = pd.concat([features, prob_features], axis=1)

        # Approach 2: Implied Expected Price
        expectation_features = self._create_expectation_features(df)
        features = pd.concat([features, expectation_features], axis=1)

        # Approach 3: Uncertainty/Volatility Features
        uncertainty_features = self._create_uncertainty_features(df)
        features = pd.concat([features, uncertainty_features], axis=1)

        # Approach 4: Distribution Shape Features
        shape_features = self._create_distribution_shape_features(df)
        features = pd.concat([features, shape_features], axis=1)

        # Approach 5: Temporal Features (momentum, regime shifts)
        temporal_features = self._create_temporal_features(df)
        features = pd.concat([features, temporal_features], axis=1)

        self.feature_names_ = list(features.columns)

        # Clean any NaN values
        features = features.fillna(method='ffill').fillna(method='bfill').fillna(0)

        return features

    def _create_probability_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Approach 1: Direct probability features

        Simple but effective - use raw probabilities as features
        """
        features = pd.DataFrame(index=df.index)

        for strike in self.strike_levels:
            prob_col = f'prob_{strike}'

            if prob_col in df.columns:
                # Raw probability
                features[f'poly_prob_{strike}'] = df[prob_col]

                # Probability momentum (how expectations are changing)
                for window in self.lookback_windows:
                    features[f'poly_prob_{strike}_change_{window}d'] = df[prob_col].diff(window)
                    features[f'poly_prob_{strike}_volatility_{window}d'] = (
                        df[prob_col].rolling(window, min_periods=1).std()
                    )

        # Probability spread (uncertainty indicator)
        if 'prob_50000' in df.columns and 'prob_70000' in df.columns:
            features['poly_prob_spread'] = df['prob_50000'] - df['prob_70000']

        return features

    def _create_expectation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Approach 2: Implied expected price from probability distribution

        Calculate the market's expected Bitcoin price and compare to reality
        """
        features = pd.DataFrame(index=df.index)

        # Calculate implied expected price
        expected_prices = []

        for idx in df.index:
            expected_price = self._calculate_expected_price(df.loc[idx])
            expected_prices.append(expected_price)

        features['poly_expected_btc'] = expected_prices

        # Gap between expectation and reality
        if 'current_btc_price' in df.columns or 'BTC-USD_close' in df.columns:
            current_price_col = 'current_btc_price' if 'current_btc_price' in df.columns else 'BTC-USD_close'

            features['poly_reality_gap'] = (
                features['poly_expected_btc'] - df[current_price_col]
            )

            features['poly_reality_gap_pct'] = (
                features['poly_reality_gap'] / df[current_price_col]
            )

            # Market sentiment (bullish vs bearish)
            features['poly_market_sentiment'] = (
                features['poly_expected_btc'] / df[current_price_col] - 1
            )

            # Sentiment momentum
            features['poly_sentiment_change_7d'] = features['poly_market_sentiment'].diff(7)

        return features

    def _calculate_expected_price(self, row: pd.Series) -> float:
        """
        Calculate probability-weighted expected Bitcoin price

        Example:
        If P(>50k) = 0.80, P(>60k) = 0.50, P(>70k) = 0.20
        Then:
        - P(50k-60k) = 0.30 → expected contribution = 0.30 * 55k = 16,500
        - P(60k-70k) = 0.30 → expected contribution = 0.30 * 65k = 19,500
        - P(>70k) = 0.20 → expected contribution = 0.20 * 75k = 15,000
        - P(<50k) = 0.20 → expected contribution = 0.20 * 45k = 9,000
        Total expected price = 60,000
        """

        # Extended strike ladder with bounds
        extended_strikes = [40000] + self.strike_levels + [90000]

        # Get probabilities (default to linear interpolation if missing)
        probs_above = []
        for strike in extended_strikes:
            prob_col = f'prob_{strike}'
            if prob_col in row.index:
                probs_above.append(row[prob_col])
            else:
                # Interpolate if missing
                probs_above.append(0.5)  # Neutral assumption

        # Ensure monotonicity (probabilities should decrease with higher strikes)
        probs_above = sorted(probs_above, reverse=True)[:len(extended_strikes)]

        # Calculate bin probabilities
        bin_probs = []
        for i in range(len(probs_above) - 1):
            bin_prob = max(0, probs_above[i] - probs_above[i+1])
            bin_probs.append(bin_prob)

        # Add tail probability
        bin_probs.append(max(0, probs_above[-1]))

        # Calculate expected value
        expected_price = 0
        for i in range(len(bin_probs)):
            if i < len(extended_strikes) - 1:
                bin_midpoint = (extended_strikes[i] + extended_strikes[i+1]) / 2
            else:
                bin_midpoint = extended_strikes[-1] + 5000  # Tail assumption

            expected_price += bin_probs[i] * bin_midpoint

        return expected_price

    def _create_uncertainty_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Approach 3: Market uncertainty and implied volatility

        Hypothesis: High uncertainty → More customer anxiety → More calls
        """
        features = pd.DataFrame(index=df.index)

        # Calculate implied volatility from distribution width
        implied_vols = []
        for idx in df.index:
            implied_vol = self._calculate_implied_volatility(df.loc[idx])
            implied_vols.append(implied_vol)

        features['poly_implied_vol'] = implied_vols

        # Volatility momentum
        for window in [3, 7, 14]:
            features[f'poly_implied_vol_change_{window}d'] = (
                features['poly_implied_vol'].diff(window)
            )

        # Market disagreement indicator
        # When prob ≈ 0.5, maximum disagreement
        for strike in [60000, 70000]:
            prob_col = f'prob_{strike}'
            if prob_col in df.columns:
                features[f'poly_disagreement_{strike}'] = (
                    1 - 2 * abs(df[prob_col] - 0.5)
                )

        # Regime shift detection
        if 'prob_60000' in df.columns:
            features['poly_regime_shift'] = df['prob_60000'].diff(1).abs()
            features['poly_regime_shift_7d'] = df['prob_60000'].diff(7).abs()

        return features

    def _calculate_implied_volatility(self, row: pd.Series) -> float:
        """
        Calculate implied volatility as standard deviation of probability distribution

        Wide distribution = high uncertainty = high volatility
        Narrow distribution = high certainty = low volatility
        """

        extended_strikes = [40000] + self.strike_levels + [90000]

        # Get probabilities
        probs_above = []
        for strike in extended_strikes:
            prob_col = f'prob_{strike}'
            if prob_col in row.index:
                probs_above.append(row[prob_col])
            else:
                probs_above.append(0.5)

        probs_above = sorted(probs_above, reverse=True)[:len(extended_strikes)]

        # Calculate bin probabilities
        bin_probs = []
        for i in range(len(probs_above) - 1):
            bin_prob = max(0, probs_above[i] - probs_above[i+1])
            bin_probs.append(bin_prob)
        bin_probs.append(max(0, probs_above[-1]))

        # Calculate mean
        mean_price = 0
        for i in range(len(bin_probs)):
            if i < len(extended_strikes) - 1:
                bin_midpoint = (extended_strikes[i] + extended_strikes[i+1]) / 2
            else:
                bin_midpoint = extended_strikes[-1] + 5000
            mean_price += bin_probs[i] * bin_midpoint

        # Calculate variance
        variance = 0
        for i in range(len(bin_probs)):
            if i < len(extended_strikes) - 1:
                bin_midpoint = (extended_strikes[i] + extended_strikes[i+1]) / 2
            else:
                bin_midpoint = extended_strikes[-1] + 5000
            variance += bin_probs[i] * (bin_midpoint - mean_price) ** 2

        return np.sqrt(variance)

    def _create_distribution_shape_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Approach 4: Distribution shape analysis (skewness, kurtosis, tail risk)
        """
        features = pd.DataFrame(index=df.index)

        # Skewness: More probability on upside vs downside
        if 'prob_70000' in df.columns and 'prob_50000' in df.columns:
            # Positive skew = more upside probability
            features['poly_distribution_skew'] = (
                df['prob_70000'] - (1 - df['prob_50000'])
            )

        # Tail risk: High probability in extreme outcomes
        tail_risk = 0
        if 'prob_80000' in df.columns:
            tail_risk += df['prob_80000']
        if 'prob_50000' in df.columns:
            tail_risk += (1 - df['prob_50000'])

        if tail_risk != 0:
            features['poly_tail_risk'] = tail_risk

        # ATM (at-the-money) probability tracking
        # Find strike closest to current price
        if 'current_btc_price' in df.columns or 'BTC-USD_close' in df.columns:
            current_price_col = 'current_btc_price' if 'current_btc_price' in df.columns else 'BTC-USD_close'

            atm_probs = []
            for idx in df.index:
                current_price = df.loc[idx, current_price_col]
                closest_strike = min(self.strike_levels, key=lambda x: abs(x - current_price))
                prob_col = f'prob_{closest_strike}'

                if prob_col in df.columns:
                    atm_probs.append(df.loc[idx, prob_col])
                else:
                    atm_probs.append(0.5)

            features['poly_atm_probability'] = atm_probs

        return features

    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Approach 5: Temporal patterns and momentum
        """
        features = pd.DataFrame(index=df.index)

        # If expiry date is available, calculate days to expiry
        if 'expiry_date' in df.columns:
            df['expiry_date'] = pd.to_datetime(df['expiry_date'])
            features['poly_days_to_expiry'] = (
                (df['expiry_date'] - df.index).dt.days
            )

            # Urgency × Uncertainty interaction
            if 'poly_implied_vol' in df.columns:
                features['poly_uncertainty_urgency'] = (
                    features['poly_implied_vol'] * (30 - features['poly_days_to_expiry'])
                )

        # Probability velocity (second derivative)
        if 'prob_60000' in df.columns:
            prob_change = df['prob_60000'].diff(1)
            features['poly_prob_velocity'] = prob_change
            features['poly_prob_acceleration'] = prob_change.diff(1)

        return features


def prepare_polymarket_data_simple(
    polymarket_csv: str,
    date_column: str = 'Date'
) -> pd.DataFrame:
    """
    Simple loader for Polymarket data in wide format

    Expected CSV format:
    Date,prob_50000,prob_60000,prob_70000,prob_80000,current_btc_price
    2024-01-15,0.82,0.45,0.18,0.05,48500

    Args:
        polymarket_csv: Path to CSV file with Polymarket data
        date_column: Name of date column

    Returns:
        DataFrame with Date index and probability columns
    """
    df = pd.read_csv(polymarket_csv)
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.set_index(date_column).sort_index()

    return df


def prepare_polymarket_data_long(
    polymarket_csv: str,
    date_column: str = 'Date',
    strike_column: str = 'Strike',
    prob_column: str = 'Probability'
) -> pd.DataFrame:
    """
    Convert long format Polymarket data to wide format

    Expected CSV format (long):
    Date,Market,Strike,Probability,Volume,Current_BTC_Price
    2024-01-15,BTC-Feb-2024,50000,0.82,145000,48500
    2024-01-15,BTC-Feb-2024,60000,0.45,98000,48500

    Args:
        polymarket_csv: Path to CSV file
        date_column: Name of date column
        strike_column: Name of strike price column
        prob_column: Name of probability column

    Returns:
        DataFrame in wide format with Date index
    """
    df = pd.read_csv(polymarket_csv)
    df[date_column] = pd.to_datetime(df[date_column])

    # Pivot to wide format
    df_wide = df.pivot_table(
        index=date_column,
        columns=strike_column,
        values=prob_column,
        aggfunc='last'
    )

    # Rename columns to match expected format
    df_wide.columns = [f'prob_{int(col)}' for col in df_wide.columns]

    # Add current BTC price if available
    if 'Current_BTC_Price' in df.columns:
        price_df = df.groupby(date_column)['Current_BTC_Price'].last()
        df_wide['current_btc_price'] = price_df

    return df_wide.sort_index()


def merge_polymarket_with_calls(
    call_data: pd.DataFrame,
    polymarket_data: pd.DataFrame,
    lag_days: int = 1
) -> pd.DataFrame:
    """
    Merge call center data with Polymarket features

    Args:
        call_data: DataFrame with Date index and 'calls' column
        polymarket_data: DataFrame with Date index and Polymarket features
        lag_days: Number of days to lag Polymarket data (prevent leakage)

    Returns:
        Merged DataFrame ready for ML pipeline
    """
    # Lag Polymarket data to prevent data leakage
    polymarket_lagged = polymarket_data.shift(lag_days)

    # Merge
    merged = call_data.merge(
        polymarket_lagged,
        left_index=True,
        right_index=True,
        how='left'
    )

    # Forward fill missing values (weekends/holidays)
    merged = merged.fillna(method='ffill')

    return merged


if __name__ == '__main__':
    """
    Example usage
    """

    # Example 1: Simple format
    print("Example 1: Simple Polymarket Data Format")
    print("=" * 60)

    # Create sample data
    sample_data = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=100),
        'prob_50000': np.random.uniform(0.6, 0.9, 100),
        'prob_60000': np.random.uniform(0.3, 0.6, 100),
        'prob_70000': np.random.uniform(0.1, 0.3, 100),
        'prob_80000': np.random.uniform(0.0, 0.1, 100),
        'current_btc_price': 60000 + np.random.normal(0, 5000, 100)
    })
    sample_data = sample_data.set_index('Date')

    # Generate features
    feature_engine = PolymarketFeatureEngine()
    features = feature_engine.fit_transform(sample_data)

    print(f"Generated {len(features.columns)} features")
    print(f"\nFeature categories:")
    print(f"- Probability features: {sum('prob' in col for col in features.columns)}")
    print(f"- Expectation features: {sum('expected' in col or 'sentiment' in col for col in features.columns)}")
    print(f"- Uncertainty features: {sum('vol' in col or 'disagreement' in col for col in features.columns)}")
    print(f"- Distribution features: {sum('skew' in col or 'tail' in col for col in features.columns)}")

    print(f"\nSample features:")
    print(features.head())

    print(f"\nTop 10 features by name:")
    for i, col in enumerate(features.columns[:10], 1):
        print(f"  {i}. {col}")
