# Polymarket Integration for Call Center Forecasting

This guide explains how to integrate Polymarket prediction market data into your ML forecasting pipeline to improve call volume predictions.

## 🎯 Why Polymarket Data?

**Current approach:** Uses yesterday's Bitcoin closing price
- Backward-looking
- Single point estimate
- Doesn't capture market expectations

**Polymarket approach:** Uses prediction market probabilities
- **Forward-looking**: Captures what markets expect
- **Uncertainty signal**: Probability distributions reveal market disagreement
- **Sentiment indicator**: Divergence between spot price and expectations

**Hypothesis:** Customer anxiety (→ call volume) correlates more with *expected future volatility* than *yesterday's price*. When Polymarket shows 50/50 odds on Bitcoin hitting $70k vs $50k, that uncertainty likely drives more support calls than a stable $60k spot price.

---

## 📊 Data Requirements

### Option 1: Simple Wide Format (Recommended for Getting Started)

Create a CSV file with daily snapshots of Polymarket probabilities:

```csv
Date,prob_50000,prob_60000,prob_70000,prob_80000,current_btc_price
2024-01-15,0.82,0.45,0.18,0.05,48500
2024-01-16,0.85,0.48,0.20,0.06,49200
2024-01-17,0.80,0.42,0.15,0.04,47800
```

**Columns:**
- `Date`: Trading date (YYYY-MM-DD)
- `prob_XXXXX`: Probability that Bitcoin will be above $XXXXX at month-end
  - Example: `prob_60000 = 0.45` means 45% chance BTC > $60k
- `current_btc_price`: Spot Bitcoin price on that date

### Option 2: Long Format (If You Have Multiple Markets)

```csv
Date,Market,Strike,Probability,Volume,Current_BTC_Price
2024-01-15,BTC-Feb-2024,50000,0.82,145000,48500
2024-01-15,BTC-Feb-2024,60000,0.45,98000,48500
2024-01-15,BTC-Feb-2024,70000,0.18,52000,48500
2024-01-16,BTC-Feb-2024,50000,0.85,152000,49200
```

**Columns:**
- `Date`: Trading date
- `Market`: Polymarket market identifier (e.g., "BTC-Feb-2024")
- `Strike`: Strike price level ($50k, $60k, etc.)
- `Probability`: Market probability (0-1) that BTC will exceed strike
- `Volume`: Trading volume (optional, can be used for weighting)
- `Current_BTC_Price`: Spot Bitcoin price

---

## 🔧 Implementation

### Quick Start (Test with Synthetic Data)

```bash
# Test the integration with synthetic Polymarket data
python integrate_polymarket.py --mode test --model ExtraTrees
```

This will:
1. Load your call center data
2. Generate synthetic Polymarket probabilities
3. Run A/B/C test comparing:
   - **Baseline**: No Polymarket features
   - **Polymarket Only**: Prediction market features only
   - **Combined**: Polymarket + Spot BTC + Traditional features
4. Show which approach performs best

### Full Run (With Real Polymarket Data)

```bash
# Run with real Polymarket data
python integrate_polymarket.py \
    --call-csv agent_contact_volume_wgsd2.csv \
    --polymarket-csv polymarket_data.csv \
    --mode full \
    --model ExtraTrees
```

---

## 📈 Features Generated

The `PolymarketFeatureEngine` creates 50+ features across 5 categories:

### 1. Direct Probability Features (Approach 1)
- `poly_prob_60000`: Raw probability of BTC > $60k
- `poly_prob_60000_change_7d`: How probability changed over 7 days
- `poly_prob_60000_volatility_7d`: Volatility of probability estimates
- `poly_prob_spread`: Difference between high/low strike probabilities

**Why this matters:** Tracks market consensus and momentum

### 2. Implied Expected Price (Approach 2)
- `poly_expected_btc`: Probability-weighted expected Bitcoin price
- `poly_reality_gap`: Gap between expected price and spot price
- `poly_market_sentiment`: Bullish vs bearish indicator
- `poly_sentiment_change_7d`: How sentiment is shifting

**Why this matters:** When reality diverges from expectations → customer confusion → more calls

### 3. Uncertainty/Volatility Features (Approach 3)
- `poly_implied_vol`: Implied volatility from probability distribution width
- `poly_disagreement_60000`: Market disagreement indicator (peaks at 50% probability)
- `poly_regime_shift`: Sudden changes in market expectations

**Why this matters:** High uncertainty → high customer anxiety → high call volume

### 4. Distribution Shape Features (Approach 4)
- `poly_distribution_skew`: Upside vs downside probability asymmetry
- `poly_tail_risk`: Probability mass in extreme outcomes
- `poly_atm_probability`: Probability at current price level

**Why this matters:** Fat tails and skewed distributions signal market stress

### 5. Temporal Features (Approach 5)
- `poly_prob_velocity`: Rate of probability change
- `poly_prob_acceleration`: Acceleration of probability changes
- `poly_days_to_expiry`: Days until market expiration (if available)

**Why this matters:** Rapid expectation changes create customer uncertainty

---

## 🧪 A/B Testing Framework

The integration script automatically runs three scenarios:

### Scenario 1: Baseline
- Call lag features (1, 7, 14 days)
- Rolling averages (7, 14 days)
- Day of week, month features
- **No** Polymarket data

### Scenario 2: Polymarket Only
- All 50+ Polymarket features
- Basic time features
- Call lag features
- **No** spot BTC prices

### Scenario 3: Combined
- Polymarket features
- Spot BTC, VIX, market prices
- All traditional features
- **Everything** available

**Expected Output:**
```
RESULTS SUMMARY
================================================================================
Scenario             MAE        Improvement     Features
------------------------------------------------------------
Combined             542.31     +10.9%          87
Polymarket_Only      578.42     +4.9%           65
Baseline             608.72     baseline        15

🏆 WINNER: Combined
   MAE: 542.31
   Improvement over baseline: +10.9%

📊 Key Insights:
   ✅ Polymarket features beat baseline by 4.9%
   ✅ Combining Polymarket + Spot prices is optimal

📈 Top Features from Winning Model:
   1. poly_implied_vol
   2. poly_reality_gap_pct
   3. calls_lag_7
   4. poly_prob_60000_change_7d
   5. poly_market_sentiment
```

---

## 🚀 Integration with Existing MLPipeline.ipynb

### Method 1: Standalone Script (Easiest)

Run the comparison as a separate analysis:

```bash
python integrate_polymarket.py --polymarket-csv your_polymarket_data.csv --mode full
```

### Method 2: Modify MLPipeline.ipynb (Most Integrated)

Add this to the `FeatureEngineer` class in `MLPipeline.ipynb`:

```python
# In MLPipeline.ipynb, add to FeatureEngineer class

from polymarket_features import PolymarketFeatureEngine

def create_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    # ... existing feature engineering code ...

    # ADD THIS SECTION:
    # ============================================================
    # POLYMARKET FEATURES
    # ============================================================
    if 'prob_60000' in data.columns:  # Check if Polymarket data exists
        print("Adding Polymarket prediction market features...")

        # Extract Polymarket columns
        poly_cols = [c for c in data.columns if c.startswith('prob_') or c == 'current_btc_price']
        polymarket_data = data[poly_cols]

        # Generate features
        poly_engine = PolymarketFeatureEngine()
        poly_features = poly_engine.fit_transform(polymarket_data)

        # Lag by 1 day to prevent data leakage
        poly_features = poly_features.shift(1)

        # Add to feature set
        features = pd.concat([features, poly_features], axis=1)

        print(f"Added {len(poly_features.columns)} Polymarket features")
    # ============================================================

    # ... rest of existing code ...
```

### Method 3: Prepare Enhanced Data First

```python
# Create enhanced dataset with Polymarket features
from polymarket_features import prepare_polymarket_data_simple, merge_polymarket_with_calls

# Load data
calls = pd.read_csv('agent_contact_volume_wgsd2.csv', index_col=0, parse_dates=True)
polymarket = prepare_polymarket_data_simple('polymarket_data.csv')

# Merge
enhanced_data = merge_polymarket_with_calls(calls, polymarket, lag_days=1)

# Save for MLPipeline
enhanced_data.to_csv('enhanced_data_with_polymarket.csv')

# Then use in MLPipeline:
# CSV_FILE_PATH = "enhanced_data_with_polymarket.csv"
```

---

## 📥 Collecting Polymarket Data

### Option 1: Manual Download
1. Go to Polymarket website
2. Find Bitcoin monthly price markets
3. Download daily snapshots of probabilities
4. Format as CSV (see Data Requirements above)

### Option 2: Polymarket API (Recommended)

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_polymarket_probabilities(market_id: str, start_date: str, end_date: str):
    """
    Fetch historical probabilities from Polymarket API

    Args:
        market_id: Polymarket market identifier
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame with daily probabilities
    """
    # NOTE: Replace with actual Polymarket API endpoint
    # This is pseudo-code - check Polymarket docs for real API

    url = f"https://api.polymarket.com/markets/{market_id}/history"
    params = {
        'start': start_date,
        'end': end_date,
        'resolution': 'daily'
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('Date')

    return df

# Example usage
btc_60k_probs = fetch_polymarket_probabilities(
    market_id='btc-feb-2024-60k',
    start_date='2024-01-01',
    end_date='2024-02-29'
)
```

### Option 3: Use Existing Price Data as Proxy (Quick Test)

If you don't have Polymarket data yet, you can create a proxy:

```python
def create_polymarket_proxy_from_prices(btc_prices: pd.Series):
    """
    Create pseudo-Polymarket features from BTC spot prices
    This is NOT as good as real prediction market data,
    but can be used for initial testing
    """
    df = pd.DataFrame(index=btc_prices.index)

    # Simple probability estimates based on price position
    for strike in [50000, 60000, 70000, 80000]:
        distance = btc_prices - strike
        # Sigmoid function to convert price distance to probability
        df[f'prob_{strike}'] = 1 / (1 + np.exp(-distance / 5000))

    df['current_btc_price'] = btc_prices

    return df
```

---

## 📊 Expected Results

Based on your existing analysis showing:
- ExtraTrees_100 baseline: MAE 608.72
- Market data matters (VIX, BTC correlate with calls)
- Tree models excel at interaction effects

**Conservative estimate: 5-10% improvement**
- Baseline MAE: 608.72
- With Polymarket: 547-578 MAE

**Optimistic estimate: 10-15% improvement**
- Baseline MAE: 608.72
- With Polymarket: 517-547 MAE

**Best case: 15-20% improvement**
- Baseline MAE: 608.72
- With Polymarket: 487-517 MAE

This would occur if:
1. Forward-looking sentiment beats backward-looking prices
2. Uncertainty metrics capture customer anxiety
3. Expectation gaps predict confusion-driven call spikes

---

## 🐛 Troubleshooting

### Issue: "No improvement over baseline"

**Possible causes:**
1. Polymarket data not aligned with call data dates
2. Insufficient historical data (need >6 months)
3. Polymarket probabilities don't correlate with call drivers
4. Data leakage prevented (check lag is applied correctly)

**Solutions:**
- Check data alignment: `df.merge(..., how='inner')` to see overlap
- Verify lag: Polymarket data from day T-1 should predict calls on day T
- Inspect correlations: `df.corr()['calls'].sort_values(ascending=False)`

### Issue: "Too many features, model slow"

**Solutions:**
```python
# Use feature selection
from sklearn.feature_selection import SelectKBest, f_regression

selector = SelectKBest(f_regression, k=30)
X_selected = selector.fit_transform(X_train, y_train)
```

### Issue: "Missing Polymarket data for some dates"

**Solutions:**
```python
# Forward-fill probabilities (they change slowly)
polymarket_df = polymarket_df.fillna(method='ffill')

# Or interpolate
polymarket_df = polymarket_df.interpolate(method='linear')
```

---

## 📝 Next Steps

1. **Week 1: Data Collection**
   - Identify Polymarket markets (Bitcoin monthly prices)
   - Download historical probabilities (past 6-12 months)
   - Format as CSV per requirements above

2. **Week 2: Testing**
   - Run A/B test with synthetic data: `python integrate_polymarket.py --mode test`
   - Run A/B test with real data: `python integrate_polymarket.py --mode full --polymarket-csv your_data.csv`
   - Analyze results

3. **Week 3: Integration**
   - If results positive (>5% improvement), integrate into MLPipeline.ipynb
   - Set up automated Polymarket data pipeline
   - Deploy to production

4. **Week 4: Monitoring**
   - Track forecast accuracy vs actual calls
   - Monitor feature importance (are Polymarket features used?)
   - Iterate on feature engineering

---

## 📚 Files Created

- `polymarket_features.py`: Feature engineering module (50+ features)
- `integrate_polymarket.py`: A/B testing framework
- `POLYMARKET_INTEGRATION_README.md`: This documentation
- `POLYMARKET_DATA_SPEC.md`: Detailed data specifications

---

## 🤝 Support

For questions or issues:
1. Check troubleshooting section above
2. Review generated comparison reports
3. Examine feature importance from best model
4. Verify data format matches specification

---

**Remember:** The key insight is that prediction markets capture *forward-looking expectations and uncertainty*, which may predict customer anxiety better than *backward-looking spot prices*.
