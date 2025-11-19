# November Polymarket Example: How Multiple Strikes Work Together

## The Data: November 15, 2024

Here's what you'd collect from Polymarket for a single day in November:

```
Current Bitcoin Spot Price: $68,000

Polymarket Probabilities (for November 30 expiry):
- Will BTC be above $60,000? → 92% chance (0.92)
- Will BTC be above $70,000? → 68% chance (0.68)
- Will BTC be above $80,000? → 35% chance (0.35)
- Will BTC be above $90,000? → 12% chance (0.12)
- Will BTC be above $100,000? → 3% chance (0.03)
```

**CSV Format:**
```csv
Date,prob_60000,prob_70000,prob_80000,prob_90000,prob_100000,current_btc_price
2024-11-15,0.92,0.68,0.35,0.12,0.03,68000
```

---

## How These 5 Probabilities Create a Distribution

The probabilities create a **probability distribution** showing where markets think Bitcoin will end up:

```
Price Range          Probability    Interpretation
================================================================
$50k - $60k          8%             P(>$50k) - P(>$60k) = 99% - 92%
$60k - $70k          24%            P(>$60k) - P(>$70k) = 92% - 68%
$70k - $80k          33%            P(>$70k) - P(>$80k) = 68% - 35%
$80k - $90k          23%            P(>$80k) - P(>$90k) = 35% - 12%
$90k - $100k         9%             P(>$90k) - P(>$100k) = 12% - 3%
Above $100k          3%             P(>$100k) = 3%
```

**Visual Distribution:**
```
   |
24%|     ████
   |  ████████████
   |  ████████████████████
8% |  ████████████████████████
   |________________________________
   50k  60k  70k  80k  90k  100k+
         ↑ Current: $68k
```

This is a **moderately bullish** distribution with most probability mass in $70k-$80k range.

---

## Three Scenarios: Same Price, Different Distributions

Here's the KEY insight - let me show you 3 different days in November, all with **the same Bitcoin spot price** ($68,000) but **different Polymarket distributions**:

### Scenario 1: Low Uncertainty Bull Market (Nov 15)

**Spot Price:** $68,000

**Polymarket Probabilities:**
- P(>$60k) = 98% ← Very high confidence
- P(>$70k) = 85%
- P(>$80k) = 45%
- P(>$90k) = 15%
- P(>$100k) = 3% ← Very low

**Distribution Shape:**
```
      Narrow, steep distribution
   |
85%|  ████
   |  ████████
   |  ████████████
   |  ████████████████
   |  ████████████████████
   |________________________________
   50k  60k  70k  80k  90k  100k
         ↑ $68k (current)
```

**Derived Features:**
- **Implied Expected Price:** $74,500
- **Reality Gap:** $74,500 - $68,000 = +$6,500 (+9.6% bullish)
- **Implied Volatility:** 8.2% (LOW uncertainty)
- **Market Disagreement:** 0.30 (LOW - market has consensus)
- **Tail Risk:** 0.05 (LOW - no extreme outcomes expected)

**Call Volume Prediction:** **NORMAL**
- Market is confident → Low customer anxiety → Normal call volume

---

### Scenario 2: High Uncertainty Volatile Market (Nov 16)

**Spot Price:** $68,000 (SAME as Scenario 1!)

**Polymarket Probabilities:**
- P(>$60k) = 75% ← Much lower confidence
- P(>$70k) = 55%
- P(>$80k) = 40%  ← Much higher than Scenario 1
- P(>$90k) = 28%  ← Much higher
- P(>$100k) = 18% ← Much higher

**Distribution Shape:**
```
      Wide, flat distribution
   |
   |  ████████████████████
   |  ████████████████████████
   |  ████████████████████████████
   |  ████████████████████████████████
   |________________________________
   50k  60k  70k  80k  90k  100k+
         ↑ $68k (current)
```

**Derived Features:**
- **Implied Expected Price:** $76,200
- **Reality Gap:** $76,200 - $68,000 = +$8,200 (+12.1% bullish)
- **Implied Volatility:** 18.5% (HIGH uncertainty) ⚠️
- **Market Disagreement:** 0.90 (VERY HIGH - market split) ⚠️
- **Tail Risk:** 0.43 (HIGH - 18% chance of >$100k, 25% chance <$60k) ⚠️

**Call Volume Prediction:** **VERY HIGH**
- High uncertainty → High customer anxiety → Many confused customers calling
- Market is split 50/50 on direction → Customers don't know what to expect

---

### Scenario 3: Low Uncertainty Bear Market (Nov 17)

**Spot Price:** $68,000 (SAME as Scenarios 1 & 2!)

**Polymarket Probabilities:**
- P(>$60k) = 65%
- P(>$70k) = 25% ← Sharp drop
- P(>$80k) = 8%
- P(>$90k) = 2%
- P(>$100k) = 0%

**Distribution Shape:**
```
      Narrow, negative skew
   |
   |  ████████
   |  ████████████████
   |  ████████████████████
   |  ████████████████████████
65%|  ████████████████████████████
   |________________________________
   50k  60k  70k  80k  90k  100k
         ↑ $68k (current)
```

**Derived Features:**
- **Implied Expected Price:** $62,800
- **Reality Gap:** $62,800 - $68,000 = -$5,200 (-7.6% bearish)
- **Implied Volatility:** 9.1% (LOW uncertainty)
- **Market Disagreement:** 0.35 (LOW - market has bearish consensus)
- **Tail Risk:** 0.35 (MODERATE - 35% chance of drop below $60k)

**Call Volume Prediction:** **ELEVATED**
- Market is bearish but confident → Moderate customer concern
- Reality gap (current price above expected) → Some confusion

---

## Summary Comparison Table

| Metric | Scenario 1 (Bull) | Scenario 2 (Volatile) | Scenario 3 (Bear) |
|--------|------------------|----------------------|------------------|
| **Spot BTC Price** | $68,000 | $68,000 | $68,000 |
| **Expected Price** | $74,500 | $76,200 | $62,800 |
| **Reality Gap** | +$6,500 | +$8,200 | -$5,200 |
| **Implied Volatility** | 8.2% (LOW) | 18.5% (HIGH) ⚠️ | 9.1% (LOW) |
| **Market Disagreement** | 0.30 (LOW) | 0.90 (HIGH) ⚠️ | 0.35 (LOW) |
| **Tail Risk** | 0.05 (LOW) | 0.43 (HIGH) ⚠️ | 0.35 (MODERATE) |
| **Predicted Calls** | NORMAL | VERY HIGH ⚠️ | ELEVATED |

---

## Key Insight: Why Multiple Strikes Matter

### Traditional Approach (Spot Price Only)
```python
# All 3 scenarios look identical!
Nov 15: BTC = $68,000 → Predict 5,000 calls
Nov 16: BTC = $68,000 → Predict 5,000 calls
Nov 17: BTC = $68,000 → Predict 5,000 calls
```

**Problem:** Misses the volatility spike on Nov 16!

### Polymarket Approach (Multiple Strikes)
```python
# Distribution reveals different market conditions
Nov 15: BTC = $68k, Vol=8.2%, Disagreement=0.30 → Predict 5,000 calls
Nov 16: BTC = $68k, Vol=18.5%, Disagreement=0.90 → Predict 8,500 calls ⚠️
Nov 17: BTC = $68k, Vol=9.1%, Disagreement=0.35 → Predict 6,200 calls
```

**Benefit:** Captures the uncertainty-driven call spike on Nov 16!

---

## Actual Features Generated from November Data

From those 5 probabilities, the feature engine creates **50+ features**:

### 1. Direct Probability Features (20 features)
```
poly_prob_60000 = 0.92
poly_prob_70000 = 0.68
poly_prob_80000 = 0.35
poly_prob_60000_change_1d = 0.02    # Changed from yesterday
poly_prob_60000_change_7d = 0.05    # Changed from last week
poly_prob_60000_volatility_7d = 0.03  # How stable is this probability?
poly_prob_spread = 0.92 - 0.03 = 0.89  # Range of probabilities
... (4 strikes × 5 features each = 20)
```

### 2. Expectation Features (8 features)
```
poly_expected_btc = $74,500         # Weighted average expected price
poly_reality_gap = $74,500 - $68,000 = $6,500
poly_reality_gap_pct = +9.6%
poly_market_sentiment = +0.096      # Bullish
poly_sentiment_change_7d = +0.02    # Getting more bullish
... (8 total)
```

### 3. Uncertainty Features (12 features)
```
poly_implied_vol = 8.2%             # Low uncertainty
poly_implied_vol_change_7d = -2.1%  # Was higher last week
poly_disagreement_60000 = 0.16      # 92% → low disagreement
poly_disagreement_70000 = 0.36      # 68% → moderate disagreement
poly_regime_shift = 0.05            # Small change from yesterday
... (12 total)
```

### 4. Distribution Features (6 features)
```
poly_distribution_skew = +0.25      # Positive skew (bullish)
poly_tail_risk = 0.05               # Low fat tail probability
poly_atm_probability = 0.75         # Prob at current price
... (6 total)
```

### 5. Temporal Features (4 features)
```
poly_prob_velocity = +0.02          # Probabilities increasing
poly_prob_acceleration = +0.005     # Increasing faster
poly_days_to_expiry = 15            # 15 days until Nov 30
... (4 total)
```

**Total: 50 features from 5 probabilities!**

---

## November Time Series Example

Here's what a full month looks like:

```csv
Date,prob_60k,prob_70k,prob_80k,prob_90k,current_btc,calls,poly_vol,disagreement
2024-11-01,0.85,0.55,0.25,0.08,62000,5200,12.3%,0.50
2024-11-02,0.88,0.58,0.28,0.10,63000,5100,11.8%,0.48
2024-11-03,0.90,0.62,0.32,0.12,64500,5000,11.2%,0.44
2024-11-04,0.92,0.65,0.35,0.15,66000,4900,10.5%,0.40
2024-11-05,0.80,0.52,0.48,0.35,66500,7800,19.2%,0.96 ⚠️ HIGH UNCERTAINTY
2024-11-06,0.82,0.54,0.45,0.32,67000,7500,18.5%,0.92 ⚠️ HIGH UNCERTAINTY
2024-11-07,0.88,0.60,0.38,0.18,68000,6200,14.1%,0.60
2024-11-08,0.92,0.68,0.35,0.12,68000,5000,8.2%,0.36
...
```

**Notice:**
- Nov 1-4: Volatility declining, calls declining (normal market)
- Nov 5-6: **Volatility spike** (19.2%!), **disagreement spike** (0.96!) → **Calls spike** to 7,800!
- Nov 7-8: Volatility normalizes, calls normalize

**Spot price features would miss the Nov 5-6 spike entirely!**

---

## How to Collect This Data

### Daily Collection Workflow

**Step 1:** Each day, go to Polymarket and find the active November markets:

- "Will Bitcoin be above $60,000 on November 30, 2024?"
- "Will Bitcoin be above $70,000 on November 30, 2024?"
- "Will Bitcoin be above $80,000 on November 30, 2024?"
- "Will Bitcoin be above $90,000 on November 30, 2024?"
- "Will Bitcoin be above $100,000 on November 30, 2024?"

**Step 2:** Record the current probability for each market (shown as a price between $0-$1 or 0%-100%)

**Step 3:** Also record current Bitcoin spot price

**Step 4:** Save to CSV:

```csv
Date,prob_60000,prob_70000,prob_80000,prob_90000,prob_100000,current_btc_price
2024-11-15,0.92,0.68,0.35,0.12,0.03,68000
```

**Step 5:** Repeat daily until month-end

---

## What Happens at Month Rollover?

On December 1st, the November markets expire and new December markets open:

**November 30 (last day):**
```csv
2024-11-30,0.96,0.75,0.45,0.18,0.05,72000,2024-11-30
```

**December 1 (new markets):**
```csv
2024-12-01,0.88,0.60,0.32,0.12,0.03,72000,2024-12-31
```

Notice probabilities "reset" because now we're asking about December 31 (30 days out) instead of November 30 (0 days out).

**The feature engineering handles this automatically** - it focuses on the *shape* of the distribution and uncertainty metrics, not absolute probability levels.

---

## Expected Improvement Breakdown

Based on your baseline ExtraTrees MAE of 608.72:

### If Polymarket Features Work Well

**Scenario A: Captures Uncertainty (5-10% improvement)**
```
Current: Uses BTC spot price only → MAE 608.72
With Polymarket: Uses implied volatility → MAE 547-578

Improvement: Catches high-uncertainty days that drive call spikes
Example: Nov 5-6 volatility spike → predicts 7,800 calls instead of 5,000
```

**Scenario B: Captures Sentiment Divergence (10-15% improvement)**
```
Current: BTC at $68k → Predict 5,000 calls
With Polymarket:
  - BTC at $68k, market expects $75k → Reality gap → Predict 6,500 calls
  - BTC at $68k, market expects $62k → Different reality gap → Predict 6,200 calls

Improvement: Distinguishes between "stable at $68k" vs "confused about direction"
```

**Scenario C: Full Distribution Information (15-20% improvement)**
```
Current: Only price
With Polymarket: Price + Uncertainty + Sentiment + Tail Risk + Disagreement

Improvement: Comprehensive uncertainty quantification
MAE: 487-517
```

---

## Bottom Line

**Multiple strike levels create a probability distribution.**
**The distribution shape reveals:**
1. **Expected outcome** (where will BTC likely end up?)
2. **Uncertainty** (how confident is the market?)
3. **Sentiment** (bullish vs bearish?)
4. **Tail risk** (chance of extreme moves?)
5. **Disagreement** (is market split or consensus?)

**All 5 signals potentially predict customer anxiety → call volume.**

**You can't get this from spot price alone!**

---

## Next Steps

1. **Week 1:** Collect 1 month of historical Polymarket data for November 2024
   - Find the 5 Bitcoin price markets
   - Record daily probabilities
   - Format as CSV

2. **Week 2:** Run the A/B test
   ```bash
   python integrate_polymarket.py --polymarket-csv november_2024.csv --mode full
   ```

3. **Week 3:** Analyze results
   - Did Polymarket beat baseline?
   - Which features were most important?
   - What was the MAE improvement?

4. **Week 4:** Deploy if successful
   - Integrate into MLPipeline.ipynb
   - Set up automated daily data collection
   - Monitor production performance
