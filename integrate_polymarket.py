"""
Integration Script: Polymarket Features + ML Pipeline

This script shows how to integrate Polymarket prediction market features
into the existing MLPipeline.ipynb workflow.

Usage:
    python integrate_polymarket.py --polymarket-csv polymarket_data.csv --mode test
"""

import pandas as pd
import numpy as np
import argparse
from datetime import datetime
from pathlib import Path

from polymarket_features import (
    PolymarketFeatureEngine,
    prepare_polymarket_data_simple,
    prepare_polymarket_data_long,
    merge_polymarket_with_calls
)


def scenario_1_baseline(call_data: pd.DataFrame) -> pd.DataFrame:
    """
    Scenario 1: Baseline - No Polymarket features

    Just use call volume with basic time features
    """
    print("\n" + "=" * 60)
    print("SCENARIO 1: BASELINE (No Polymarket)")
    print("=" * 60)

    df = call_data.copy()

    # Add basic time features
    df['dow'] = df.index.dayofweek
    df['month'] = df.index.month
    df['is_weekend'] = (df['dow'] >= 5).astype(int)

    # Add lag features for calls
    for lag in [1, 7, 14]:
        df[f'calls_lag_{lag}'] = df['calls'].shift(lag)

    # Rolling features
    for window in [7, 14]:
        df[f'calls_rolling_mean_{window}'] = df['calls'].rolling(window).mean().shift(1)

    # Drop NaN
    df = df.dropna()

    print(f"Features: {len(df.columns) - 1}")  # -1 for target
    print(f"Samples: {len(df)}")

    return df


def scenario_2_polymarket_only(
    call_data: pd.DataFrame,
    polymarket_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Scenario 2: Polymarket features only

    Use prediction market features without spot BTC price
    """
    print("\n" + "=" * 60)
    print("SCENARIO 2: POLYMARKET ONLY")
    print("=" * 60)

    # Generate Polymarket features
    feature_engine = PolymarketFeatureEngine()
    poly_features = feature_engine.fit_transform(polymarket_data)

    # Merge with call data (with 1-day lag to prevent leakage)
    poly_features_lagged = poly_features.shift(1)
    df = call_data.merge(
        poly_features_lagged,
        left_index=True,
        right_index=True,
        how='inner'
    )

    # Add basic time features
    df['dow'] = df.index.dayofweek
    df['month'] = df.index.month

    # Add call lag features
    for lag in [1, 7]:
        df[f'calls_lag_{lag}'] = df['calls'].shift(lag)

    # Drop NaN
    df = df.dropna()

    print(f"Features: {len(df.columns) - 1}")
    print(f"Samples: {len(df)}")
    print(f"\nPolymarket features: {len([c for c in df.columns if 'poly' in c])}")

    return df


def scenario_3_combined(
    call_data: pd.DataFrame,
    polymarket_data: pd.DataFrame,
    market_data: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Scenario 3: Combined - Polymarket + Spot Prices + Traditional features

    Use everything available
    """
    print("\n" + "=" * 60)
    print("SCENARIO 3: COMBINED (Polymarket + Spot BTC + Traditional)")
    print("=" * 60)

    # Generate Polymarket features
    feature_engine = PolymarketFeatureEngine()
    poly_features = feature_engine.fit_transform(polymarket_data)

    # Merge with call data
    poly_features_lagged = poly_features.shift(1)
    df = call_data.merge(
        poly_features_lagged,
        left_index=True,
        right_index=True,
        how='inner'
    )

    # Add market data if available
    if market_data is not None:
        market_data_lagged = market_data.shift(1)
        df = df.merge(
            market_data_lagged,
            left_index=True,
            right_index=True,
            how='left'
        )

        # Add market-derived features
        if 'BTC-USD_close' in df.columns:
            df['btc_pct_change'] = df['BTC-USD_close'].pct_change()
            df['btc_rolling_vol_7d'] = df['btc_pct_change'].rolling(7).std()

        if '^VIX_close' in df.columns:
            df['vix_pct_change'] = df['^VIX_close'].pct_change()

    # Add time features
    df['dow'] = df.index.dayofweek
    df['month'] = df.index.month
    df['is_weekend'] = (df['dow'] >= 5).astype(int)

    # Add call lag features
    for lag in [1, 7, 14]:
        df[f'calls_lag_{lag}'] = df['calls'].shift(lag)

    for window in [7, 14]:
        df[f'calls_rolling_mean_{window}'] = df['calls'].rolling(window).mean().shift(1)

    # Drop NaN
    df = df.dropna()

    print(f"Features: {len(df.columns) - 1}")
    print(f"Samples: {len(df)}")
    print(f"- Polymarket features: {len([c for c in df.columns if 'poly' in c])}")
    print(f"- Market features: {len([c for c in df.columns if 'BTC' in c or 'VIX' in c])}")
    print(f"- Call lag features: {len([c for c in df.columns if 'calls_lag' in c or 'calls_rolling' in c])}")

    return df


def run_comparison_experiment(
    call_data: pd.DataFrame,
    polymarket_data: pd.DataFrame,
    market_data: pd.DataFrame = None,
    model_type: str = 'ExtraTrees'
):
    """
    Run A/B/C test comparing three scenarios

    Args:
        call_data: DataFrame with Date index and 'calls' column
        polymarket_data: DataFrame with Polymarket probability data
        market_data: Optional DataFrame with spot market prices
        model_type: 'ExtraTrees', 'RandomForest', 'XGBoost', etc.
    """
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
    from sklearn.metrics import mean_absolute_error
    import xgboost as xgb

    print("\n" + "=" * 80)
    print("POLYMARKET FEATURE COMPARISON EXPERIMENT")
    print("=" * 80)
    print(f"Model: {model_type}")
    print(f"Test period: {call_data.index[-60:].min()} to {call_data.index[-1]}")

    # Prepare three datasets
    data_baseline = scenario_1_baseline(call_data)
    data_polymarket = scenario_2_polymarket_only(call_data, polymarket_data)
    data_combined = scenario_3_combined(call_data, polymarket_data, market_data)

    # Time series split
    test_size = 60  # Last 60 days for testing

    scenarios = {
        'Baseline': data_baseline,
        'Polymarket_Only': data_polymarket,
        'Combined': data_combined
    }

    results = []

    for scenario_name, df in scenarios.items():
        print(f"\n{'='*60}")
        print(f"Training: {scenario_name}")
        print(f"{'='*60}")

        # Split data
        train_df = df.iloc[:-test_size]
        test_df = df.iloc[-test_size:]

        X_train = train_df.drop(columns=['calls'])
        y_train = train_df['calls']
        X_test = test_df.drop(columns=['calls'])
        y_test = test_df['calls']

        # Train model
        if model_type == 'ExtraTrees':
            model = ExtraTreesRegressor(
                n_estimators=200,
                max_depth=20,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'RandomForest':
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=20,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'XGBoost':
            model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=10,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)

        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        # Store results
        results.append({
            'scenario': scenario_name,
            'mae': mae,
            'n_features': len(X_train.columns),
            'n_samples': len(train_df),
            'top_5_features': list(feature_importance.head(5)['feature'].values),
            'model': model
        })

        print(f"MAE: {mae:.2f}")
        print(f"\nTop 5 Features:")
        for i, row in feature_importance.head(5).iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")

    # Summary comparison
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('mae')

    baseline_mae = results_df[results_df['scenario'] == 'Baseline']['mae'].values[0]

    print(f"\n{'Scenario':<20} {'MAE':<10} {'Improvement':<15} {'Features':<10}")
    print("-" * 60)

    for _, row in results_df.iterrows():
        improvement = ((baseline_mae - row['mae']) / baseline_mae) * 100
        print(f"{row['scenario']:<20} {row['mae']:<10.2f} {improvement:+.1f}%{'':<10} {row['n_features']:<10}")

    # Identify winner
    winner = results_df.iloc[0]
    print(f"\n🏆 WINNER: {winner['scenario']}")
    print(f"   MAE: {winner['mae']:.2f}")
    print(f"   Improvement over baseline: {((baseline_mae - winner['mae']) / baseline_mae) * 100:+.1f}%")

    print(f"\n📊 Key Insights:")

    # Check if Polymarket helped
    poly_mae = results_df[results_df['scenario'] == 'Polymarket_Only']['mae'].values[0]
    combined_mae = results_df[results_df['scenario'] == 'Combined']['mae'].values[0]

    if poly_mae < baseline_mae:
        print(f"   ✅ Polymarket features beat baseline by {((baseline_mae - poly_mae) / baseline_mae) * 100:.1f}%")
    else:
        print(f"   ❌ Polymarket features underperformed baseline by {((poly_mae - baseline_mae) / baseline_mae) * 100:.1f}%")

    if combined_mae < poly_mae and combined_mae < baseline_mae:
        print(f"   ✅ Combining Polymarket + Spot prices is optimal")
    elif poly_mae < combined_mae:
        print(f"   ⚠️  Polymarket alone beats combined (possible feature interference)")

    # Feature importance analysis
    print(f"\n📈 Top Features from Winning Model:")
    for i, feat in enumerate(winner['top_5_features'], 1):
        print(f"   {i}. {feat}")

    return results_df, winner['model']


def create_sample_polymarket_data(
    call_data: pd.DataFrame,
    noise_level: float = 0.1
) -> pd.DataFrame:
    """
    Create synthetic Polymarket data for testing

    This generates realistic-looking prediction market probabilities
    that correlate with call volume changes.

    Args:
        call_data: Real call center data
        noise_level: How much random noise to add (0-1)

    Returns:
        Synthetic Polymarket data
    """
    print("\n" + "=" * 60)
    print("GENERATING SYNTHETIC POLYMARKET DATA")
    print("=" * 60)
    print("Note: This is for testing. Replace with real Polymarket data.")

    dates = call_data.index
    n = len(dates)

    # Base Bitcoin price with realistic volatility
    btc_base = 60000
    btc_returns = np.random.normal(0.001, 0.03, n)
    btc_prices = btc_base * np.exp(np.cumsum(btc_returns))

    # Probabilities should reflect price movements
    # When BTC is high, higher probability of staying high

    poly_data = pd.DataFrame(index=dates)

    for strike in [50000, 60000, 70000, 80000]:
        # Probability of being above strike
        # Use sigmoid to map price distance to probability
        distance = btc_prices - strike
        base_prob = 1 / (1 + np.exp(-distance / 5000))

        # Add some noise and momentum
        noise = np.random.normal(0, noise_level * 0.1, n)
        momentum = pd.Series(base_prob).diff().rolling(7).mean().fillna(0).values * 0.3

        prob = np.clip(base_prob + noise + momentum, 0.01, 0.99)

        poly_data[f'prob_{strike}'] = prob

    poly_data['current_btc_price'] = btc_prices

    print(f"Generated {len(poly_data)} days of synthetic Polymarket data")
    print(f"BTC price range: ${btc_prices.min():.0f} - ${btc_prices.max():.0f}")
    print(f"\nSample probabilities:")
    print(poly_data.head())

    return poly_data


def main():
    """
    Main execution function
    """
    parser = argparse.ArgumentParser(description='Integrate Polymarket features')
    parser.add_argument('--call-csv', type=str, default='agent_contact_volume_wgsd2.csv',
                       help='Path to call center data CSV')
    parser.add_argument('--polymarket-csv', type=str, default=None,
                       help='Path to Polymarket data CSV (optional - will use synthetic if not provided)')
    parser.add_argument('--market-csv', type=str, default=None,
                       help='Path to market data CSV (BTC, VIX, etc.)')
    parser.add_argument('--mode', type=str, choices=['test', 'full'], default='test',
                       help='test = synthetic data, full = real Polymarket data')
    parser.add_argument('--model', type=str, default='ExtraTrees',
                       choices=['ExtraTrees', 'RandomForest', 'XGBoost'],
                       help='Model to use for comparison')

    args = parser.parse_args()

    # Load call center data
    print("Loading call center data...")
    call_df = pd.read_csv(args.call_csv)
    call_df.columns = ['Date', 'calls']  # Standardize column names
    call_df['Date'] = pd.to_datetime(call_df['Date'])
    call_df = call_df.set_index('Date').sort_index()

    print(f"Loaded {len(call_df)} days of call data")
    print(f"Date range: {call_df.index.min()} to {call_df.index.max()}")

    # Load or create Polymarket data
    if args.mode == 'test' or args.polymarket_csv is None:
        print("\nUsing synthetic Polymarket data for testing...")
        polymarket_df = create_sample_polymarket_data(call_df)
    else:
        print(f"\nLoading real Polymarket data from {args.polymarket_csv}...")
        polymarket_df = prepare_polymarket_data_simple(args.polymarket_csv)

    # Load market data if available
    market_df = None
    if args.market_csv:
        print(f"\nLoading market data from {args.market_csv}...")
        market_df = pd.read_csv(args.market_csv, index_col=0, parse_dates=True)

    # Run comparison experiment
    results_df, best_model = run_comparison_experiment(
        call_df,
        polymarket_df,
        market_df,
        model_type=args.model
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_df.to_csv(f'polymarket_comparison_{timestamp}.csv', index=False)

    print(f"\n✅ Results saved to: polymarket_comparison_{timestamp}.csv")

    return results_df, best_model


if __name__ == '__main__':
    results_df, best_model = main()
