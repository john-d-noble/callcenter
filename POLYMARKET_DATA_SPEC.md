# Polymarket Data Specification

## Overview

This document specifies the exact data format needed from Polymarket to integrate prediction market features into the call center forecasting pipeline.

---

## Data Source: Polymarket Bitcoin Monthly Price Markets

Polymarket offers binary prediction markets for Bitcoin reaching specific price levels by month-end.

**Example markets:**
- "Will Bitcoin be above $60,000 on February 29, 2024?"
- "Will Bitcoin be above $70,000 on February 29, 2024?"

**Key insight:** The probability at each strike level creates a distribution of expected outcomes, revealing market uncertainty and sentiment.

---

## Required Data Format

### Format 1: Simple Wide Format (Recommended)

**File:** `polymarket_btc_daily.csv`

```csv
Date,prob_50000,prob_60000,prob_70000,prob_80000,current_btc_price,expiry_date
2024-01-15,0.82,0.45,0.18,0.05,48500,2024-01-31
2024-01-16,0.85,0.48,0.20,0.06,49200,2024-01-31
2024-01-17,0.80,0.42,0.15,0.04,47800,2024-01-31
2024-01-18,0.83,0.46,0.19,0.06,48900,2024-01-31
```

**Column Specifications:**

| Column | Type | Description | Example | Required |
|--------|------|-------------|---------|----------|
| `Date` | Date | Trading date in YYYY-MM-DD format | 2024-01-15 | Yes |
| `prob_50000` | Float | Probability (0-1) that BTC will be above $50,000 at expiry | 0.82 | Yes |
| `prob_60000` | Float | Probability (0-1) that BTC will be above $60,000 at expiry | 0.45 | Yes |
| `prob_70000` | Float | Probability (0-1) that BTC will be above $70,000 at expiry | 0.18 | Yes |
| `prob_80000` | Float | Probability (0-1) that BTC will be above $80,000 at expiry | 0.05 | Optional |
| `prob_40000` | Float | Probability (0-1) that BTC will be above $40,000 at expiry | 0.95 | Optional |
| `current_btc_price` | Float | Spot Bitcoin price at market close on Date | 48500.00 | Yes |
| `expiry_date` | Date | Contract expiration date (usually month-end) | 2024-01-31 | Optional |
| `volume` | Integer | Trading volume (number of shares) | 145000 | Optional |

**Notes:**
- Probabilities must be between 0 and 1 (not percentages)
- Probabilities should be monotonically decreasing (prob_50k > prob_60k > prob_70k)
- One row per trading day
- Use end-of-day values (market close)

---

### Format 2: Long Format (Alternative)

**File:** `polymarket_btc_long.csv`

```csv
Date,Market,Strike,Probability,Volume,Bid,Ask,Current_BTC_Price,Expiry
2024-01-15,BTC-Jan-2024,50000,0.82,145000,0.80,0.84,48500,2024-01-31
2024-01-15,BTC-Jan-2024,60000,0.45,98000,0.43,0.47,48500,2024-01-31
2024-01-15,BTC-Jan-2024,70000,0.18,52000,0.16,0.20,48500,2024-01-31
2024-01-16,BTC-Jan-2024,50000,0.85,152000,0.83,0.87,49200,2024-01-31
2024-01-16,BTC-Jan-2024,60000,0.48,105000,0.46,0.50,49200,2024-01-31
```

**Column Specifications:**

| Column | Type | Description | Example | Required |
|--------|------|-------------|---------|----------|
| `Date` | Date | Trading date | 2024-01-15 | Yes |
| `Market` | String | Market identifier | BTC-Jan-2024 | Yes |
| `Strike` | Integer | Strike price level | 60000 | Yes |
| `Probability` | Float | Market probability (0-1) | 0.45 | Yes |
| `Volume` | Integer | Trading volume | 98000 | Optional |
| `Bid` | Float | Bid price (0-1) | 0.43 | Optional |
| `Ask` | Float | Ask price (0-1) | 0.47 | Optional |
| `Current_BTC_Price` | Float | Spot Bitcoin price | 48500.00 | Yes |
| `Expiry` | Date | Contract expiration | 2024-01-31 | Optional |

**Notes:**
- Each strike level gets its own row
- Multiple rows per day (one per strike)
- Will be pivoted to wide format during processing

---

## Data Quality Requirements

### 1. Completeness

- **Daily coverage**: Data for every trading day (365 days/year)
- **Missing dates**: Acceptable for weekends/holidays (will forward-fill)
- **Minimum history**: 6 months recommended, 12+ months ideal

### 2. Consistency

- **Monotonicity**: Higher strikes must have lower probabilities
  ```
  ✅ VALID:   prob_50k=0.82, prob_60k=0.45, prob_70k=0.18
  ❌ INVALID: prob_50k=0.45, prob_60k=0.82, prob_70k=0.18
  ```

- **Probability bounds**: All values between 0 and 1
  ```
  ✅ VALID:   prob_60k = 0.45
  ❌ INVALID: prob_60k = 45  (should be 0.45, not percentage)
  ❌ INVALID: prob_60k = 1.2 (exceeds 1.0)
  ```

### 3. Alignment with Call Data

- **Date overlap**: Polymarket dates must overlap with call center dates
- **Time zones**: Use consistent time zone (UTC or market close time)
- **Lagging**: Pipeline automatically lags by 1 day to prevent data leakage

---

## Recommended Strike Levels

Based on Bitcoin's historical volatility and typical trading ranges:

### Minimum Set (4 strikes)
- $50,000 - Floor level
- $60,000 - Mid-range
- $70,000 - Upper range
- $80,000 - Bull case

### Expanded Set (6 strikes)
- $40,000 - Bear case
- $50,000 - Lower support
- $60,000 - Mid-range
- $70,000 - Upper range
- $80,000 - Bull case
- $90,000 - Extreme bull

### Adaptive Set (Dynamic)
- Strikes ± 20% from current price
- Example: If BTC = $60k, use strikes: $48k, $54k, $60k, $66k, $72k

---

## Data Collection Methods

### Method 1: Manual Export

1. Visit Polymarket website daily
2. Navigate to Bitcoin price markets
3. Record probabilities for each strike
4. Export to CSV

**Pros:** Simple, no API needed
**Cons:** Manual, time-consuming

### Method 2: Polymarket API

```python
import requests
import pandas as pd
from datetime import datetime

def fetch_polymarket_market(market_slug: str, date: str):
    """
    Fetch Polymarket market data for specific date

    Example market_slug: 'bitcoin-over-60k-january-2024'
    """
    url = f"https://api.polymarket.com/markets/{market_slug}"

    response = requests.get(url)
    data = response.json()

    return {
        'date': date,
        'probability': data['outcomeTokenPrices']['1'],  # "Yes" price
        'volume': data['volume24hr'],
        'liquidity': data['liquidity']
    }

# Example: Collect data for multiple strikes
strikes = [50000, 60000, 70000, 80000]
date = '2024-01-15'

market_data = []
for strike in strikes:
    market_slug = f'bitcoin-over-{strike//1000}k-january-2024'
    data = fetch_polymarket_market(market_slug, date)
    market_data.append({
        'Date': date,
        f'prob_{strike}': data['probability']
    })
```

**Pros:** Automated, scalable
**Cons:** Requires API access, rate limits

### Method 3: Web Scraping

```python
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd

def scrape_polymarket_probabilities(url: str):
    """
    Scrape Polymarket market page for current probabilities
    """
    driver = webdriver.Chrome()
    driver.get(url)

    # Wait for page load
    time.sleep(3)

    # Parse HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract probability (adjust selectors based on actual HTML)
    prob_element = soup.find('div', {'class': 'probability-display'})
    probability = float(prob_element.text.strip('%')) / 100

    driver.quit()

    return probability
```

**Pros:** Works when API unavailable
**Cons:** Fragile (breaks if website changes), slower

---

## Example: Daily Data Collection Workflow

### Step 1: Identify Active Markets

For each month, Polymarket typically has markets like:
- "Will Bitcoin be above $50k on Jan 31, 2024?"
- "Will Bitcoin be above $60k on Jan 31, 2024?"
- "Will Bitcoin be above $70k on Jan 31, 2024?"

Track market IDs or slugs for each strike.

### Step 2: Daily Data Capture

```python
import yfinance as yf
from datetime import datetime

def collect_daily_polymarket_data():
    """
    Collect daily snapshot of Polymarket probabilities
    """
    today = datetime.now().strftime('%Y-%m-%d')

    # Fetch Bitcoin spot price
    btc = yf.Ticker("BTC-USD")
    current_price = btc.history(period='1d')['Close'].iloc[-1]

    # Fetch probabilities for each strike
    # (Replace with actual Polymarket API calls)
    probabilities = {
        'Date': today,
        'prob_50000': fetch_polymarket_prob('btc-50k-jan-2024'),
        'prob_60000': fetch_polymarket_prob('btc-60k-jan-2024'),
        'prob_70000': fetch_polymarket_prob('btc-70k-jan-2024'),
        'prob_80000': fetch_polymarket_prob('btc-80k-jan-2024'),
        'current_btc_price': current_price,
        'expiry_date': '2024-01-31'
    }

    # Append to CSV
    df = pd.DataFrame([probabilities])
    df.to_csv('polymarket_btc_daily.csv', mode='a', header=False, index=False)

    print(f"✅ Collected data for {today}")
    return probabilities

# Run daily (e.g., via cron job)
collect_daily_polymarket_data()
```

### Step 3: Validation

```python
def validate_polymarket_data(csv_path: str):
    """
    Validate Polymarket data quality
    """
    df = pd.read_csv(csv_path, parse_dates=['Date'])

    print("Data Validation Report")
    print("=" * 60)

    # Check 1: Completeness
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Total days: {len(df)}")
    expected_days = (df['Date'].max() - df['Date'].min()).days + 1
    print(f"Expected days: {expected_days}")
    print(f"Missing days: {expected_days - len(df)}")

    # Check 2: Monotonicity
    prob_cols = [c for c in df.columns if c.startswith('prob_')]
    strikes = sorted([int(c.split('_')[1]) for c in prob_cols])

    violations = 0
    for idx, row in df.iterrows():
        probs = [row[f'prob_{s}'] for s in strikes]
        if not all(probs[i] >= probs[i+1] for i in range(len(probs)-1)):
            violations += 1
            print(f"⚠️  Monotonicity violation on {row['Date']}")

    print(f"Monotonicity violations: {violations}")

    # Check 3: Bounds
    for col in prob_cols:
        invalid = df[(df[col] < 0) | (df[col] > 1)]
        if len(invalid) > 0:
            print(f"⚠️  Invalid probabilities in {col}: {len(invalid)} rows")

    # Check 4: Correlations
    print(f"\nCorrelation with BTC price:")
    for col in prob_cols:
        corr = df[col].corr(df['current_btc_price'])
        print(f"  {col}: {corr:.3f}")

    print("\n✅ Validation complete")

# Validate before using
validate_polymarket_data('polymarket_btc_daily.csv')
```

---

## Sample Data Files

### Sample 1: Week of Data (Wide Format)

```csv
Date,prob_50000,prob_60000,prob_70000,prob_80000,current_btc_price,expiry_date
2024-01-15,0.82,0.45,0.18,0.05,48500,2024-01-31
2024-01-16,0.85,0.48,0.20,0.06,49200,2024-01-31
2024-01-17,0.80,0.42,0.15,0.04,47800,2024-01-31
2024-01-18,0.83,0.46,0.19,0.06,48900,2024-01-31
2024-01-19,0.87,0.52,0.24,0.08,50100,2024-01-31
2024-01-22,0.90,0.58,0.28,0.10,51200,2024-01-31
2024-01-23,0.88,0.54,0.25,0.08,50500,2024-01-31
```

### Sample 2: Transition Between Months

When markets roll over to new month:

```csv
Date,prob_50000,prob_60000,prob_70000,current_btc_price,expiry_date
2024-01-29,0.92,0.65,0.35,52000,2024-01-31
2024-01-30,0.94,0.70,0.40,52500,2024-01-31
2024-01-31,0.96,0.75,0.45,53000,2024-01-31
2024-02-01,0.85,0.48,0.20,53000,2024-02-29
2024-02-02,0.87,0.52,0.24,53500,2024-02-29
```

**Note:** Probabilities jump on Feb 1 because expiry moved from 30 days out to 28 days out.

---

## Integration Checklist

Before using Polymarket data with the ML pipeline:

- [ ] Data covers at least 6 months
- [ ] Dates align with call center data (overlap > 80%)
- [ ] Probabilities are decimals (0-1), not percentages (0-100)
- [ ] Monotonicity check passes (higher strikes = lower probabilities)
- [ ] No missing values in required columns
- [ ] Current BTC price included
- [ ] One row per day (or filled weekends/holidays)
- [ ] Validated with `validate_polymarket_data()` function

---

## Troubleshooting Common Issues

### Issue: Probabilities sum to > 1.0

**Problem:**
```csv
prob_50000,prob_60000,prob_70000
0.80,0.60,0.40  # These are NOT mutually exclusive!
```

**Explanation:**
- prob_50000 = 0.80 means 80% chance BTC > $50k
- prob_60000 = 0.60 means 60% chance BTC > $60k
- These are **nested**, not mutually exclusive
- If BTC is above $60k, it's also above $50k

**Solution:** This is correct! Probabilities should NOT sum to 1.0.

### Issue: Probabilities increase with strike price

**Problem:**
```csv
prob_50000,prob_60000,prob_70000
0.40,0.60,0.80  # Wrong order!
```

**Solution:** Higher strikes should have LOWER probabilities. Check data extraction logic.

### Issue: Gaps in dates

**Problem:**
```csv
Date
2024-01-15
2024-01-16
2024-01-19  # Missing 1/17, 1/18 (weekends)
```

**Solution:**
```python
# Forward-fill weekend/holiday values
df = df.set_index('Date')
df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq='D'))
df = df.fillna(method='ffill')
```

---

## Contact & Support

For questions about data format:
- Review example files in this specification
- Check validation function output
- Verify against sample data patterns shown above

**Remember:** The goal is to capture daily snapshots of market expectations and uncertainty, which will be transformed into 50+ predictive features for the ML pipeline.
