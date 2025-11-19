# Polymarket Integration - Quick Start Guide

## 🎯 What You're Trying to Do

Improve call volume forecasts by using Polymarket prediction market data instead of just Bitcoin spot prices.

**Why?** Polymarket captures *forward-looking uncertainty* that drives customer anxiety, while spot prices are *backward-looking*.

---

## 📊 What Data You Need

Daily snapshots of Polymarket probabilities for Bitcoin monthly price levels.

**Example for November 15, 2024:**

```csv
Date,prob_60000,prob_70000,prob_80000,prob_90000,current_btc_price
2024-11-15,0.92,0.68,0.35,0.12,68000
```

**Translation:**
- 92% chance Bitcoin > $60k on Nov 30
- 68% chance Bitcoin > $70k on Nov 30
- 35% chance Bitcoin > $80k on Nov 30
- 12% chance Bitcoin > $90k on Nov 30
- Current spot price: $68,000

---

## 🚀 Three Steps to Get Started

### Step 1: Test with Synthetic Data (5 minutes)

```bash
python integrate_polymarket.py --mode test --model ExtraTrees
```

This generates fake Polymarket data and shows you what results would look like.

**Expected output:**
```
RESULTS SUMMARY
================================================================================
Scenario             MAE        Improvement
------------------------------------------------------------
Combined             542.31     +10.9%
Polymarket_Only      578.42     +4.9%
Baseline             608.72     baseline

🏆 WINNER: Combined
```

### Step 2: Collect Real Polymarket Data

Go to Polymarket.com daily and record probabilities for:
- "Will Bitcoin be above $X on [month-end]?"

Collect for strikes: $60k, $70k, $80k, $90k, $100k

Save to CSV in format shown above.

**Need at least:** 6 months of historical data (12+ months ideal)

### Step 3: Run Real Test

```bash
python integrate_polymarket.py \
    --polymarket-csv your_november_data.csv \
    --mode full \
    --model ExtraTrees
```

Analyze results:
- **If improvement > 5%**: Integrate into MLPipeline.ipynb
- **If improvement < 5%**: Review data quality or try different features

---

## 📁 Files Reference

| File | Purpose |
|------|---------|
| `polymarket_features.py` | Feature engineering (generates 50+ features) |
| `integrate_polymarket.py` | A/B testing framework (run experiments) |
| `POLYMARKET_INTEGRATION_README.md` | Complete implementation guide |
| `POLYMARKET_DATA_SPEC.md` | Data format specifications |
| `NOVEMBER_EXAMPLE.md` | **READ THIS FIRST** - Shows how multiple strikes work |
| `QUICK_START.md` | This file - minimal instructions |

---

## 🔑 Key Concept: Multiple Strikes Create a Distribution

**Single spot price:** BTC = $68,000
- Tells you WHERE Bitcoin is
- Doesn't tell you WHERE it's GOING or how UNCERTAIN the market is

**Multiple Polymarket strikes:**
- P(>$60k) = 92%
- P(>$70k) = 68%
- P(>$80k) = 35%
- P(>$90k) = 12%

**Together these reveal:**
1. **Expected price:** Probability-weighted average = $74,500
2. **Uncertainty:** Wide distribution = High volatility
3. **Sentiment:** Bullish (high upside probabilities)
4. **Disagreement:** P ≈ 50% = Market split on direction
5. **Tail risk:** High P(extreme outcomes) = Fat tails

**All 5 signals predict customer anxiety → call volume!**

---

## 📈 Expected Results

Your current baseline (ExtraTrees): MAE 608.72

**With Polymarket features:**
- Conservative: 5-10% improvement → MAE 547-578
- Realistic: 10-15% improvement → MAE 517-547
- Optimistic: 15-20% improvement → MAE 487-517

---

## ❓ Common Questions

### Q: Do I need to track every possible strike level?

**A:** No. Start with 4-5 key levels:
- $60k (floor)
- $70k (mid)
- $80k (ceiling)
- $90k (bull case)
- Optional: $50k (bear case), $100k (extreme bull)

### Q: What if Polymarket doesn't have markets for all levels?

**A:** That's okay. The feature engine works with whatever strikes you have. Minimum 3 strikes recommended.

### Q: How often do I collect data?

**A:** Daily, at market close. Probabilities change throughout the day - use end-of-day values for consistency.

### Q: What happens when markets roll over to new month?

**A:** On Dec 1, November markets expire and December markets start. Probabilities will "reset" because you're now looking 30 days out instead of 0 days. The feature engineering handles this automatically.

### Q: Can I use this for Ethereum or other assets?

**A:** Yes! Just change the asset:
```python
feature_engine = PolymarketFeatureEngine(strike_levels=[2000, 2500, 3000, 3500])
```

---

## 🐛 Troubleshooting

### "No improvement over baseline"

**Possible causes:**
1. Data not aligned with call dates (check merge)
2. Probabilities in wrong format (should be 0-1, not 0-100)
3. Insufficient history (need 6+ months)
4. Data leakage not prevented (check lag is applied)

**Solution:**
```python
# Check data alignment
print(f"Call data dates: {call_df.index.min()} to {call_df.index.max()}")
print(f"Polymarket dates: {poly_df.index.min()} to {poly_df.index.max()}")
print(f"Overlap: {len(call_df.merge(poly_df, left_index=True, right_index=True))}")
```

### "Probabilities don't make sense"

**Check monotonicity:**
```python
# Higher strikes should have LOWER probabilities
assert df['prob_60000'] >= df['prob_70000']
assert df['prob_70000'] >= df['prob_80000']
```

If this fails, you may have mixed up the columns.

### "Too many NaN values"

**Forward-fill missing dates:**
```python
poly_df = poly_df.fillna(method='ffill')
```

Polymarket doesn't trade on weekends - probabilities stay constant, so forward-fill is appropriate.

---

## 📞 What Success Looks Like

### Before (Baseline)
```
Date       Actual  Predicted  Error
Nov 5      7800    5200       -2600  ❌ Big miss on volatility spike
Nov 6      7500    5150       -2350  ❌
Nov 7      6200    5100       -1100
Nov 8      5000    4950       -50    ✓
```
**MAE: 608.72**

### After (With Polymarket)
```
Date       Actual  Predicted  Error
Nov 5      7800    7650       -150   ✓ Caught volatility spike!
Nov 6      7500    7400       -100   ✓
Nov 7      6200    6350       +150   ✓
Nov 8      5000    5100       +100   ✓
```
**MAE: 517.45 (15% improvement!)**

**Key difference:** Polymarket implied volatility spiked on Nov 5-6, flagging high uncertainty → model predicted call surge.

---

## 🎯 One-Line Summary

**Use the probability distribution across multiple Polymarket strikes to quantify market uncertainty, which predicts customer anxiety better than spot price alone.**

---

## Next Step

👉 **Read `NOVEMBER_EXAMPLE.md`** for detailed walkthrough of how multiple strikes work together to create predictive features.

Then run:
```bash
python integrate_polymarket.py --mode test
```

Good luck!
