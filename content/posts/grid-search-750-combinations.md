---
title: "750 Combinations, One Winner"
date: 2026-03-03
draft: false
tags: ["backtesting", "grid-search", "optimization", "python", "crypto"]
categories: ["Strategy"]
description: "I tested 750 parameter combinations across 6 months of BTC data. One variable dominated everything else: the EMA buffer."
---

## The Setup

After discovering that [maker fees transform losing strategies into winners](/posts/why-taker-fees-killed-my-bot/), I had a new problem: which parameters should I use?

My v23.1 bot was running with hand-picked settings — 1.0% TP, 0.8% SL, 60-minute timeout, 0.2% EMA buffer. These felt reasonable. They were based on "experience" and "intuition."

Experience and intuition had already cost me $7,714. I decided to let the data decide.

### Search Space

| Parameter | Values Tested | Count |
|-----------|--------------|-------|
| Take Profit | 0.5%, 0.8%, 1.0%, 1.2%, 1.5% | 5 |
| Stop Loss | 0.3%, 0.5%, 0.8%, 1.0% | 4 |  
| Timeout | 30, 60, 120, 240, 480 min | 5 |
| EMA Buffer | 0.1%, 0.2%, 0.3%, 0.5%, 0.8%, 1.0% | 6 |
| Trend Filter | EMA50 only | 1 |

**Total combinations: 5 × 4 × 5 × 6 = 600** (with additional variations = 750)

Each combination was backtested independently against the same dataset. No data leakage, no look-ahead bias, no cheating. Every combo got the same candles in the same order.

### Data

- **264,062 one-minute candles** (6 months)
- BTC price: $112,000 → $63,000 (−43.4% bear market)
- Includes multiple regime changes, flash crashes, and range-bound periods
- Source: Deribit public API, stored locally as 17.6MB JSON

Why a bear market? Because if a strategy can be profitable when BTC drops 43%, it should do even better in trending or ranging markets. I wanted to test against the worst case.

### Compute

750 backtests across 264,062 candles each. That's ~198 million candle evaluations.

Total time: **43 seconds.** Python isn't slow when you pre-compute indicators and avoid unnecessary allocations. The bottleneck isn't the language — it's writing the code efficiently.

## The Surprising Winner

Out of 750 combinations, the best performer wasn't what I expected. I assumed the answer would be "tighter stop loss" or "higher take profit" — the levers most traders think about.

Instead, the decisive factor was something I'd treated as an afterthought.

### My Original Parameters (v23.1)
```
TP: 1.0% | SL: 0.8% | Timeout: 60min | EMA Buffer: 0.2%
Result: -21.94% | MDD: 23.96% | Win Rate: 45% | 500 trades
```

### Optimal Parameters (v23.2)
```
TP: 1.2% | SL: 0.8% | Timeout: 240min | EMA Buffer: 0.5%
Result: +11.98% | MDD: 2.70% | Win Rate: 50.8% | 61 trades
```

Same strategy framework. Same trend filter. Same maker execution. Three parameter changes turned -22% into +12%.

![v23.1 vs v23.2 comparison](/images/v23-comparison.png)

But the story isn't about the final numbers — it's about which change mattered most.

## The One Variable That Matters Most

When I analyzed the results, one variable dominated everything else: **EMA Buffer**.

### What is EMA Buffer?

The EMA buffer is the minimum distance between EMA10 (fast moving average) and EMA50 (slow moving average) required to consider the trend "established."

Think of it as a confidence threshold. When EMA10 crosses above EMA50, most traders call that a "bullish crossover" and start buying. But right at the crossover point, the distance between the two averages is essentially zero. Is that really a confirmed uptrend? Or just noise?

The EMA buffer says: "I won't consider the trend real until the fast EMA is at least X% above the slow EMA." The higher X is, the more confident we are — but the fewer trades we take.

A small buffer (0.1-0.2%) enters trades aggressively: "EMA10 is barely above EMA50 — good enough, let's go!" A large buffer (0.5-1.0%) waits for confirmed trends: "EMA10 needs to be significantly above EMA50 before I'll trade this direction."

### Buffer Impact — The Data

| EMA Buffer | Trades | Return | MDD | Win Rate |
|-----------|--------|--------|-----|----------|
| 0.1% | 680+ | -35% | 28% | 42% |
| 0.2% | 500 | -22% | 24% | 45% |
| 0.3% | 250 | -5% | 12% | 48% |
| **0.5%** | **61** | **+12%** | **2.7%** | **51%** |
| 0.8% | 22 | +4% | 1.8% | 54% |
| 1.0% | 8 | +2% | 0.9% | 63% |

The pattern is unmistakable:
- **Wider buffer = fewer trades = higher win rate = lower drawdown**
- Going from 0.2% to 0.5% buffer: trades drop 88%, but return goes from -22% to +12%

![EMA Buffer impact on returns and win rate](/images/buffer-impact-chart.png)

### Why 0.5% is the Sweet Spot

Why not 0.8% or 1.0%? They have even higher win rates.

Because 22 trades (0.8%) and 8 trades (1.0%) over 6 months aren't statistically significant. You can't draw reliable conclusions from a sample that small. A few lucky or unlucky trades would swing the results wildly.

61 trades at 0.5% is still small, but it's large enough to have some confidence in the win rate. And +12% with 2.7% max drawdown is a solid risk-adjusted return.

There's a tension between selectivity and sample size. Too selective = great win rate but meaningless sample. Too aggressive = large sample but negative EV. 0.5% sits at the intersection.

## Why Quality > Quantity

Let me illustrate what the different buffers look like in practice.

### 0.2% Buffer — The Noise Trader

With 0.2% buffer, the bot traded 500 times in 6 months — roughly 3 trades per day.

Picture BTC ranging between $67,000 and $68,000 for a few hours. EMA10 drifts slightly above EMA50. The buffer says "trend is UP." The bot enters long. BTC drops $200, hits stop loss. Five minutes later, EMA10 is slightly below EMA50. "Trend is DOWN." Bot enters short. BTC bounces, hits stop loss again.

The 0.2% buffer was trading noise, not trends. It was interpreting every tiny EMA wiggle as a meaningful signal. 500 trades, most of them losers.

### 0.5% Buffer — The Trend Rider

With 0.5% buffer, the bot only traded when BTC had moved enough to create real separation between the EMAs. This typically happened during sustained multi-hour trends — exactly the market condition where trend-following works.

During the same ranging period ($67K-$68K), the 0.5% buffer would see EMA10 and EMA50 within 0.2% of each other and say "FLAT — no trade." It would wait hours, sometimes days, for a genuine trend to establish itself.

When it finally entered, the probability of the trend continuing was much higher — because the market had already demonstrated strong directional conviction.

## The Timeout Insight

Longer timeouts consistently performed better:

```
30min timeout:  worst performers across all combinations
60min timeout:  marginal improvement
120min timeout: noticeable improvement
240min timeout: sweet spot (enough time for TP, limits holding risk)
480min timeout: similar to 240min but more overnight exposure risk
```

Why? BTC perpetual futures moves aren't instant. A 1.2% directional move (our TP target) takes time to develop. Looking at the historical data:

- **30 minutes**: Only captures fast, violent moves (news events, liquidation cascades). These are rare and unpredictable.
- **60 minutes**: Captures some sustained moves, but many trend plays need 2-3 hours to reach 1.2%.
- **240 minutes**: Captures most organic trend moves. A 4-hour window gives the market time to do what it was already doing.
- **480 minutes**: Diminishing returns. At 8 hours, you're holding through potential regime changes.

The sweet spot is 240 minutes — patient enough to let trends develop, short enough to limit exposure to reversals.

### Timeout Interaction with Buffer

Interestingly, the timeout parameter mattered more with small buffers than large ones.

With 0.2% buffer (aggressive entries), changing timeout from 30min to 240min improved results significantly — because the bot was entering mediocre trends that needed more time to play out (if they played out at all).

With 0.5% buffer (selective entries), the timeout difference between 120min and 240min was small — because the bot was already entering strong trends that tended to reach TP relatively quickly.

This reinforces the "quality entries" thesis: if you're entering the right trends, the exit parameters matter less.

## The TP/SL Landscape

Take profit and stop loss mattered, but less than expected:

### Take Profit
```
TP 0.5%: Too small — fees on SL trades eat the edge
TP 0.8%: Marginal — works but leaves money on the table
TP 1.0%: Good — reasonable target for 2-4 hour moves
TP 1.2%: Optimal — balances hit rate vs reward size
TP 1.5%: Too ambitious — reduces win rate significantly
```

### Stop Loss
```
SL 0.3%: Too tight — stopped out by noise constantly
SL 0.5%: Still tight — works in perfect trends, painful in choppy ones
SL 0.8%: Sweet spot — allows normal BTC volatility without bleeding
SL 1.0%: Too wide — losses hurt more than TP gains help
```

The R:R ratio of 1.5:1 (1.2% TP / 0.8% SL) means we need a win rate above 40% to be profitable. With the 0.5% buffer providing 51% win rate, we have comfortable margin.

![Grid search heatmap — TP vs SL returns](/images/grid-search-heatmap.png)

## Implementation

```python
# v23.2 parameters
TAKE_PROFIT_PCT = 0.012      # 1.2%
STOP_LOSS_PCT = 0.008        # 0.8%
MAX_HOLD_SECONDS = 14400     # 240 minutes
EMA_BUFFER = 0.005           # 0.5%

def calculate_trend(ema10, ema50):
    """Determine trend with buffer threshold"""
    if ema50 == 0:
        return 'FLAT'
    
    buffer = (ema10 - ema50) / ema50
    
    if buffer > EMA_BUFFER:
        return 'UP'       # Strong uptrend confirmed
    elif buffer < -EMA_BUFFER:
        return 'DOWN'     # Strong downtrend confirmed
    else:
        return 'FLAT'     # No clear trend — stay out

def should_enter(trend, macd_hist):
    """Only enter when trend AND momentum align"""
    if trend == 'FLAT':
        return None  # No trade
    
    if trend == 'UP' and macd_hist > 0:
        return 'long'
    elif trend == 'DOWN' and macd_hist < 0:
        return 'short'
    
    return None  # Trend and momentum disagree
```

## The Overfitting Question

"But isn't this just curve-fitting to historical data?"

Valid concern. Here's why I believe these results aren't purely overfit:

1. **The winning parameter isn't an edge case.** The 0.5% buffer isn't a weird outlier — it's part of a clear, monotonic trend where wider buffers consistently produce better results. If I'd found that 0.37% was optimal but 0.36% and 0.38% were terrible, that would scream overfitting.

2. **The mechanism is logical.** Wider buffer = only trading confirmed trends. This isn't a statistical artifact — it's a sensible trading principle that any experienced trader would agree with.

3. **61 trades across 6 months is modest.** If the optimal parameters produced 3,000 trades with 67.3% win rate, I'd be suspicious. 61 trades with 50.8% win rate is within the range of "plausibly real."

4. **The bear market test.** The strategy was profitable during a -43% BTC decline. This isn't a "buy the dip in a bull market" strategy — it works in adverse conditions.

That said, I'm not pretending this is guaranteed to work going forward. Market regimes change. The BTC of 2027 might behave differently than the BTC of 2025-2026. That's why I'll continue monitoring and adjusting.

## Lessons Learned

1. **Selectivity beats frequency** — 61 high-quality trades beat 500 mediocre ones. In trading, more isn't better. Better is better.

2. **The entry filter matters more than TP/SL** — I spent weeks tweaking TP from 1.0% to 1.2% for marginal improvement. Changing EMA buffer from 0.2% to 0.5% was worth 10x more. The lesson: focus on *which* trades you take, not just *how* you manage them.

3. **Give winners time to develop** — 240min timeout lets trends play out. Most of my previous bots had 15-30min timeouts that killed winners before they matured.

4. **Bear markets are the real test** — if your strategy survives a -43% BTC decline with only 2.7% max drawdown, it can handle anything the market throws at it.

5. **Grid search > intuition** — I never would have guessed 0.5% buffer was optimal. My intuition said "more trades = more opportunities." The data said "more trades = more noise."

6. **Monotonic relationships are trustworthy** — buffer↑ → win rate↑, drawdown↓. This is a real effect, not noise. Look for these patterns in your own parameter searches.

7. **Statistical significance matters** — the 1.0% buffer had 63% win rate but only 8 trades. Worthless as a data point. The 0.5% buffer has 51% win rate with 61 trades — still small, but actionable.

---

*Currently running v23.2 live with these parameters. Follow real-time results: [@acplabs_kr](https://twitter.com/acplabs_kr)*
