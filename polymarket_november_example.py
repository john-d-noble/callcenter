"""
Polymarket November Example: How Multiple Strike Levels Are Used

This demonstrates how probabilities across different strikes create
a probability distribution that reveals market uncertainty and sentiment.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Example: November 2024 Polymarket data for 3 different market scenarios

def create_november_scenarios():
    """
    Create 3 scenarios for November to show how strike distribution matters
    """

    # Scenario 1: Low Uncertainty (Bull Market)
    # Market is confident Bitcoin will stay high
    scenario_1 = {
        'Date': '2024-11-15',
        'Scenario': 'Low Uncertainty Bull',
        'Current_BTC': 68000,
        'prob_60000': 0.98,  # Very high confidence above $60k
        'prob_70000': 0.85,  # High confidence above $70k
        'prob_80000': 0.45,  # Moderate chance above $80k
        'prob_90000': 0.15,  # Low chance above $90k
        'prob_100000': 0.03  # Very low chance above $100k
    }

    # Scenario 2: High Uncertainty (Volatile Market)
    # Market is very uncertain - probabilities are flat/spread out
    scenario_2 = {
        'Date': '2024-11-16',
        'Scenario': 'High Uncertainty Volatile',
        'Current_BTC': 68000,  # Same spot price as Scenario 1!
        'prob_60000': 0.75,  # Lower confidence (vs 0.98)
        'prob_70000': 0.55,  # Much flatter distribution
        'prob_80000': 0.40,  # Higher than Scenario 1
        'prob_90000': 0.28,  # Much higher than Scenario 1
        'prob_100000': 0.18  # Much higher than Scenario 1
    }

    # Scenario 3: Low Uncertainty (Bear Market)
    # Market is confident Bitcoin will drop
    scenario_3 = {
        'Date': '2024-11-17',
        'Scenario': 'Low Uncertainty Bear',
        'Current_BTC': 68000,  # Same spot price again!
        'prob_60000': 0.65,  # Lower confidence
        'prob_70000': 0.25,  # Sharp drop
        'prob_80000': 0.08,  # Very low
        'prob_90000': 0.02,  # Almost zero
        'prob_100000': 0.00  # Zero chance
    }

    return pd.DataFrame([scenario_1, scenario_2, scenario_3])


def analyze_scenario(row):
    """
    Analyze a single scenario showing all derived features
    """

    print(f"\n{'='*80}")
    print(f"SCENARIO: {row['Scenario']}")
    print(f"Date: {row['Date']} | Current BTC Price: ${row['Current_BTC']:,.0f}")
    print(f"{'='*80}")

    strikes = [60000, 70000, 80000, 90000, 100000]
    probs = [row[f'prob_{s}'] for s in strikes]

    # Show raw probabilities
    print(f"\n📊 Raw Polymarket Probabilities:")
    print(f"{'Strike':<12} {'Probability':<15} {'Interpretation'}")
    print(f"{'-'*60}")
    for strike, prob in zip(strikes, probs):
        print(f"${strike:>6,}     {prob:>6.1%}          {int(prob*100)}% chance BTC > ${strike:,}")

    # ========================================
    # FEATURE 1: Implied Expected Price
    # ========================================

    # Calculate bin probabilities (probability mass in each range)
    extended_strikes = [50000] + strikes + [110000]
    extended_probs = [0.99] + probs + [0.00]  # Add bounds

    bin_probs = []
    for i in range(len(extended_probs) - 1):
        bin_prob = max(0, extended_probs[i] - extended_probs[i+1])
        bin_probs.append(bin_prob)

    # Calculate expected value
    expected_price = 0
    print(f"\n📈 Feature 1: Implied Expected Price Calculation")
    print(f"{'Price Range':<20} {'Probability':<15} {'Expected Value'}")
    print(f"{'-'*60}")

    for i in range(len(bin_probs)):
        if i < len(extended_strikes) - 1:
            lower = extended_strikes[i]
            upper = extended_strikes[i+1]
            midpoint = (lower + upper) / 2
            range_str = f"${lower:,} - ${upper:,}"
        else:
            midpoint = extended_strikes[-1] + 5000
            range_str = f"> ${extended_strikes[-1]:,}"

        contribution = bin_probs[i] * midpoint
        expected_price += contribution

        if bin_probs[i] > 0.01:  # Only show significant bins
            print(f"{range_str:<20} {bin_probs[i]:>6.1%}          ${contribution:>10,.0f}")

    print(f"{'-'*60}")
    print(f"{'IMPLIED EXPECTED PRICE:':<37} ${expected_price:>10,.0f}")
    print(f"{'Current Spot Price:':<37} ${row['Current_BTC']:>10,.0f}")

    # Reality gap
    reality_gap = expected_price - row['Current_BTC']
    reality_gap_pct = (reality_gap / row['Current_BTC']) * 100

    print(f"{'Reality Gap (Expected - Spot):':<37} ${reality_gap:>10,.0f} ({reality_gap_pct:+.1f}%)")

    if abs(reality_gap_pct) < 2:
        print(f"   → Market expects price to stay stable")
    elif reality_gap_pct > 2:
        print(f"   → Market is BULLISH (expects {reality_gap_pct:.1f}% increase)")
    else:
        print(f"   → Market is BEARISH (expects {abs(reality_gap_pct):.1f}% decrease)")

    # ========================================
    # FEATURE 2: Implied Volatility (Uncertainty)
    # ========================================

    # Calculate standard deviation of distribution
    variance = 0
    for i in range(len(bin_probs)):
        if i < len(extended_strikes) - 1:
            midpoint = (extended_strikes[i] + extended_strikes[i+1]) / 2
        else:
            midpoint = extended_strikes[-1] + 5000
        variance += bin_probs[i] * (midpoint - expected_price) ** 2

    implied_vol = np.sqrt(variance)
    implied_vol_pct = (implied_vol / expected_price) * 100

    print(f"\n📉 Feature 2: Implied Volatility (Market Uncertainty)")
    print(f"Standard Deviation: ${implied_vol:,.0f} ({implied_vol_pct:.1f}%)")

    if implied_vol_pct < 10:
        uncertainty_level = "LOW"
        call_impact = "LOW call volume expected (market confident)"
    elif implied_vol_pct < 15:
        uncertainty_level = "MODERATE"
        call_impact = "MODERATE call volume expected"
    else:
        uncertainty_level = "HIGH"
        call_impact = "HIGH call volume expected (market uncertain → customer anxiety)"

    print(f"Uncertainty Level: {uncertainty_level}")
    print(f"   → {call_impact}")

    # ========================================
    # FEATURE 3: Distribution Shape (Skewness)
    # ========================================

    # Upside probability (above current price)
    upside_prob = sum([p for s, p in zip(strikes, probs) if s > row['Current_BTC']])
    # Downside probability (below current price)
    downside_prob = 1 - max([p for s, p in zip(strikes, probs) if s < row['Current_BTC']], default=0)

    skew = upside_prob - downside_prob

    print(f"\n📊 Feature 3: Distribution Skewness")
    print(f"Upside Probability (BTC rises): {upside_prob:.1%}")
    print(f"Downside Probability (BTC falls): {downside_prob:.1%}")
    print(f"Skewness: {skew:+.2f}")

    if skew > 0.1:
        print(f"   → BULLISH skew (more upside probability)")
    elif skew < -0.1:
        print(f"   → BEARISH skew (more downside probability)")
    else:
        print(f"   → NEUTRAL skew (balanced distribution)")

    # ========================================
    # FEATURE 4: Market Disagreement
    # ========================================

    # Find probability closest to 0.5 (maximum disagreement)
    disagreements = [abs(p - 0.5) for p in probs]
    min_disagreement = min(disagreements)
    max_disagreement_metric = 1 - 2 * min_disagreement  # 0 = consensus, 1 = maximum disagreement

    print(f"\n🤝 Feature 4: Market Disagreement")
    print(f"Disagreement Metric: {max_disagreement_metric:.2f} (0 = consensus, 1 = max disagreement)")

    if max_disagreement_metric > 0.7:
        print(f"   → HIGH disagreement (market split on direction)")
        print(f"   → Expect HIGH customer confusion → MORE calls")
    elif max_disagreement_metric > 0.4:
        print(f"   → MODERATE disagreement")
    else:
        print(f"   → LOW disagreement (market has consensus)")

    # ========================================
    # FEATURE 5: Tail Risk
    # ========================================

    # Probability in extreme outcomes
    tail_risk = probs[-1] + (1 - probs[0])  # P(>$100k) + P(<$60k)

    print(f"\n⚠️  Feature 5: Tail Risk")
    print(f"Extreme Outcome Probability: {tail_risk:.1%}")
    print(f"   P(BTC > $100k): {probs[-1]:.1%}")
    print(f"   P(BTC < $60k): {1-probs[0]:.1%}")

    if tail_risk > 0.2:
        print(f"   → HIGH tail risk (fat tails in distribution)")
        print(f"   → Market pricing in extreme moves → Customer anxiety")
    else:
        print(f"   → LOW tail risk (normal distribution)")

    # ========================================
    # SUMMARY: Predicted Call Volume Impact
    # ========================================

    print(f"\n{'='*80}")
    print(f"💡 PREDICTED CALL VOLUME IMPACT")
    print(f"{'='*80}")

    # Simple scoring
    score = 0

    # High uncertainty adds to call volume
    if implied_vol_pct > 15:
        score += 3
    elif implied_vol_pct > 10:
        score += 1

    # Large reality gap adds to call volume (confusion)
    if abs(reality_gap_pct) > 5:
        score += 2

    # High disagreement adds to call volume
    if max_disagreement_metric > 0.7:
        score += 3
    elif max_disagreement_metric > 0.4:
        score += 1

    # High tail risk adds to call volume
    if tail_risk > 0.2:
        score += 2

    if score >= 7:
        volume_prediction = "VERY HIGH"
        reason = "High uncertainty + disagreement + tail risk"
    elif score >= 4:
        volume_prediction = "ELEVATED"
        reason = "Moderate uncertainty/disagreement"
    else:
        volume_prediction = "NORMAL"
        reason = "Low uncertainty, market consensus"

    print(f"Call Volume Prediction: {volume_prediction}")
    print(f"Reason: {reason}")
    print(f"Signal Strength: {score}/10")

    return {
        'scenario': row['Scenario'],
        'expected_price': expected_price,
        'reality_gap_pct': reality_gap_pct,
        'implied_vol_pct': implied_vol_pct,
        'skewness': skew,
        'disagreement': max_disagreement_metric,
        'tail_risk': tail_risk,
        'call_volume_score': score
    }


def visualize_distributions(scenarios_df):
    """
    Create visualization showing how different distributions look
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    strikes = [60000, 70000, 80000, 90000, 100000]

    for idx, (_, row) in enumerate(scenarios_df.iterrows()):
        ax = axes[idx]

        probs = [row[f'prob_{s}'] for s in strikes]

        # Calculate bin probabilities for histogram
        extended_strikes = [50000] + strikes + [110000]
        extended_probs = [0.99] + probs + [0.00]

        bin_probs = []
        bin_labels = []
        for i in range(len(extended_probs) - 1):
            bin_prob = max(0, extended_probs[i] - extended_probs[i+1])
            bin_probs.append(bin_prob)
            if i < len(extended_strikes) - 1:
                bin_labels.append(f"${extended_strikes[i]//1000}k-${extended_strikes[i+1]//1000}k")
            else:
                bin_labels.append(f">${extended_strikes[-1]//1000}k")

        # Create bar chart
        colors = ['green' if bp > 0.15 else 'orange' if bp > 0.05 else 'lightgray' for bp in bin_probs]
        ax.bar(range(len(bin_probs)), bin_probs, color=colors, edgecolor='black')
        ax.set_xticks(range(len(bin_probs)))
        ax.set_xticklabels(bin_labels, rotation=45, ha='right')
        ax.set_ylabel('Probability Mass')
        ax.set_title(f"{row['Scenario']}\nCurrent BTC: ${row['Current_BTC']:,}", fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, max(bin_probs) * 1.2)

        # Add current price line
        current_idx = 2  # Approximately where $68k falls
        ax.axvline(current_idx, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Current Price')
        ax.legend()

    plt.tight_layout()
    plt.savefig('/home/user/callcenter/november_distributions.png', dpi=150, bbox_inches='tight')
    print(f"\n📊 Visualization saved to: november_distributions.png")
    plt.close()


def main():
    """
    Run the complete November example
    """
    print("="*80)
    print("POLYMARKET NOVEMBER EXAMPLE")
    print("How Multiple Strike Levels Create Predictive Features")
    print("="*80)

    # Create scenarios
    scenarios_df = create_november_scenarios()

    print(f"\nWe have 3 days in November with THE SAME spot BTC price ($68,000)")
    print(f"but DIFFERENT Polymarket probability distributions.")
    print(f"\nThis shows how Polymarket captures information that spot price misses!")

    # Analyze each scenario
    results = []
    for _, row in scenarios_df.iterrows():
        result = analyze_scenario(row)
        results.append(result)

    # Create visualization
    visualize_distributions(scenarios_df)

    # Summary comparison
    results_df = pd.DataFrame(results)

    print(f"\n{'='*80}")
    print(f"SUMMARY COMPARISON: Why Multiple Strikes Matter")
    print(f"{'='*80}")
    print(f"\n{'Scenario':<25} {'Uncertainty':<12} {'Disagreement':<12} {'Call Score':<10}")
    print(f"{'-'*60}")
    for _, row in results_df.iterrows():
        print(f"{row['scenario']:<25} {row['implied_vol_pct']:>6.1f}%      {row['disagreement']:>6.2f}        {row['call_volume_score']:>3}/10")

    print(f"\n💡 KEY INSIGHT:")
    print(f"All three scenarios have the SAME Bitcoin spot price ($68,000)")
    print(f"but DIFFERENT call volume predictions based on Polymarket distribution!")
    print(f"\nTraditional features (spot price, % change) would treat these identically.")
    print(f"Polymarket features capture the uncertainty and sentiment that drive customer calls.")

    # Show time series example
    print(f"\n{'='*80}")
    print(f"TIME SERIES EXAMPLE: November 1-30, 2024")
    print(f"{'='*80}")

    # Simulate a month of data
    dates = pd.date_range('2024-11-01', '2024-11-30', freq='D')

    print(f"\nSample of how Polymarket data changes over November:")
    print(f"(In reality, you'd collect this daily)")
    print(f"\n{'Date':<12} {'BTC Price':<12} {'P(>$70k)':<10} {'P(>$80k)':<10} {'P(>$90k)':<10} {'Uncertainty'}")
    print(f"{'-'*80}")

    for i, date in enumerate(dates[:10]):  # Show first 10 days
        # Simulate changing probabilities
        base_price = 65000 + i * 500
        base_prob_70k = 0.60 + (i * 0.02)
        base_prob_80k = 0.30 + (i * 0.015)
        base_prob_90k = 0.10 + (i * 0.01)

        # Add some volatility spikes
        if i == 5:  # Simulate news event
            uncertainty = "HIGH ⚠️"
        else:
            uncertainty = "Normal"

        print(f"{date.strftime('%Y-%m-%d')}  ${base_price:>6,}      {base_prob_70k:>5.1%}     {base_prob_80k:>5.1%}     {base_prob_90k:>5.1%}    {uncertainty}")

    print(f"...")
    print(f"\n👆 Each day's probability distribution generates 50+ features for ML model")

    print(f"\n✅ November example complete!")
    print(f"\nNext steps:")
    print(f"1. Collect real Polymarket data in this format")
    print(f"2. Run: python integrate_polymarket.py --polymarket-csv november_data.csv")
    print(f"3. Compare performance vs baseline")


if __name__ == '__main__':
    main()
