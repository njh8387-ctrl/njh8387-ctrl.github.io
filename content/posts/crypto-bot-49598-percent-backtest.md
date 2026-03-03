---
title: "+49,598% Backtest Results"
date: 2026-03-01
draft: false
tags: ["backtesting", "python", "trading-bot", "macd", "crypto"]
categories: ["Strategy"]
description: "A deep dive into building a BTC perpetual futures bot using MACD filtering, achieving +49,598% returns in 6-month backtesting with 264,000 candles."
---

## TL;DR

I built a BTC perpetual futures trading bot that backtested **+49,598%** over 6 months (264,000 one-minute candles) with a **41.4% win rate** and **2:1 reward-to-risk ratio**. The secret? A single MACD histogram filter that eliminated noise entries.

But here's the thing — impressive backtests mean nothing if you can't run them live. This post covers the strategy, the math, the pitfalls I fell into, and what actually matters when you go from backtest to real money.

## The Problem: Good Strategy, Bad Entries

My original bot used a simple but effective setup:
- **Trend filter**: EMA20 on 1-hour candles (long above, short below)
- **Entry**: 3-min and 5-min momentum confirmation
- **Take Profit**: 1.0% (limit order, 0% maker fee)
- **Stop Loss**: 0.5% (2:1 R:R)
- **Leverage**: 10x

This returned +3,942% in backtesting — impressive, but with a **39% win rate**. That means 61% of trades hit stop loss. Many of those were noise trades where price would dip just enough to trigger SL, then reverse toward where TP would have been.

I spent weeks watching the logs. The pattern was consistent: during trending markets, the bot printed money. During choppy, range-bound markets, it bled out. The trend filter (EMA20) wasn't enough — it would say "we're in an uptrend" even during minor pullbacks within a range, and the bot would enter long right before a 0.5% dip.

The question wasn't "is the strategy wrong?" It was "how do I stop it from trading during the wrong conditions?"

## The Research Behind the Fix

A paper published in February 2026 (Miyazaki et al.) studied multi-agent LLM trading systems. Their key finding:

> **Pre-calculated technical indicators dramatically outperform raw data when given to trading agents.**

The Technical Agent — which used pre-computed RSI, MACD, Bollinger Bands, and KDJ — was the single most important performance driver. Removing it crashed the system's Sharpe ratio by more than any other component.

What caught my attention wasn't the LLM part — it was the idea of using indicators as **pre-filters** rather than entry signals. Most retail traders use MACD crossovers as buy/sell signals. The paper suggested using them as environment classifiers: "Is this a good market to trade in right now?"

That's a fundamentally different question.

## Adding MACD Filtering

Instead of entering on every momentum signal, I added a MACD histogram filter:

```python
def check_macd_filter(candles_1m, period=60):
    closes = [c['close'] for c in candles_1m[-period:]]
    
    # Calculate MACD components
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd_line = ema12 - ema26
    signal_line = calculate_ema_from_values(macd_history, 9)
    histogram = macd_line - signal_line
    
    return {
        'bullish': histogram > 0 and histogram > prev_histogram,
        'bearish': histogram < 0 and histogram < prev_histogram
    }
```

The filter only allows:
- **Long entries** when MACD histogram is positive AND increasing
- **Short entries** when MACD histogram is negative AND decreasing

The "AND increasing/decreasing" part is crucial. A positive histogram that's shrinking means bullish momentum is fading — not the time to enter a long. You want to enter when momentum is **accelerating**, not decelerating.

### Why This Works

Think of it this way: the MACD histogram measures the **speed of the trend**. When it's positive and growing, the short-term average is pulling away from the long-term average faster and faster. That's a trend gaining strength.

When it's positive but shrinking, the trend still exists but it's losing steam. Entering here means you're buying near the top of the move.

In choppy markets, the histogram oscillates rapidly around zero — small positive, small negative, back and forth. The filter naturally avoids these periods because the histogram never builds sustained momentum in either direction.

## Results

| Metric | Without MACD | With MACD |
|--------|-------------|-----------|
| Return | +3,942% | +49,598% |
| Win Rate | 39.0% | 41.4% |
| Profit Factor | 1.28 | 1.43 |
| Max Drawdown | 18.2% | 12.7% |
| Total Trades | 8,234 | 6,891 |
| Avg Hold Time | 12 min | 14 min |
| Best Month | +312% | +1,847% |
| Worst Month | -8.3% | -4.1% |

The MACD filter didn't dramatically change the win rate — it went from 39% to 41.4%. But it eliminated the **worst** trades, the ones that would have been instant stop losses during choppy, directionless markets.

Look at the profit factor: 1.28 → 1.43. That might look small, but compounded over 6,891 trades, it's the difference between +3,942% and +49,598%. Small edges compound exponentially.

![Same strategy, different fees — the impact is staggering](/images/fee-impact-equity-curve.png)

The max drawdown improvement (18.2% → 12.7%) is equally important. Lower drawdown means you survive longer, which means more time for compounding to work.

## What the Backtest Doesn't Tell You

Here's where I need to be honest, because this is where most trading content lies by omission.

### 1. Slippage isn't modeled

The backtest assumes you get filled at the exact price you want. In reality, during fast moves, your limit order might not fill at all, or the market might gap past your stop loss. I've seen BTC move 0.3% in a single second during news events.

### 2. The 6-month window matters enormously

My test period (September 2025 to February 2026) included a massive bear market — BTC dropped from $112K to $63K. That's a -43.4% decline. The bot performed well because strong trends (even downtrends) are its ideal environment.

Would it perform the same in a sideways market? Probably not. The MACD filter would reject most trades, and the few it took might not have enough directional movement to hit TP.

### 3. +49,598% with compounding is misleading

This return assumes full compounding — every profit immediately increases position size. In practice, you'd use fractional Kelly sizing or fixed percentages. Realistic returns with conservative sizing would be more like +500% to +2,000%.

Still great. But not "turn $100 into $50,000" great.

### 4. Past data ≠ future data

The market regime that produced these results may never repeat. Strategies that worked in 2025-2026 may fail in 2027. This is why ongoing monitoring and adaptation are essential — you can't just deploy a bot and forget it.

## The Catch: Maker vs Taker

Here's what I learned the hard way: **these results assume maker fees (0%)**. When I ran the same strategy with taker fees (0.05%), every single combination went bankrupt.

I grid-searched 40 parameter combinations under taker fees. All 40 strategies ended at $0.

The same strategies under maker fees? +233% to +49,598%.

This was the most expensive lesson of my trading career. I deployed 22 versions of this bot live, paying taker fees every time, and lost $7,714 before figuring it out. The strategy was fine. The execution was wrong.

**The fee structure is everything.** (I wrote a [separate deep dive on this](/posts/why-taker-fees-killed-my-bot/).)

## Lessons I Wish I'd Known Earlier

1. **Technical indicators as filters > indicators as signals** — Use MACD to filter out bad entries, not to generate entries. The indicator isn't telling you "buy now" — it's telling you "conditions are favorable for buying."

2. **Maker fees are non-negotiable** — 0.05% taker fee destroys edge on high-frequency strategies. This isn't theoretical — I proved it with $7,714 of losses.

3. **Win rate isn't everything** — 41% win rate with 2:1 R:R is profitable; 60% win rate with 1:3 R:R isn't. The math: `0.41 × 2 - 0.59 × 1 = 0.23` (positive EV) vs `0.60 × 1 - 0.40 × 3 = -0.60` (negative EV).

4. **Backtest with real data** — 264,000 candles covering both bull and bear markets. Synthetic data or short timeframes will mislead you.

5. **Be skeptical of your own results** — +49,598% sounds amazing. It IS amazing — in a backtest. The question is always "what breaks when I go live?" For me, it was fees.

6. **The best strategy is the one you can actually execute** — A theoretically superior strategy that requires taker orders is worse than a mediocre strategy with maker execution, because the fees eat the edge.

## What's Next

I'm currently running v23.2 of this bot live with real money ($86 starting capital). The parameters have been optimized through a [750-combination grid search](/posts/grid-search-750-combinations/), and the execution is maker-only.

Early results: 6 consecutive wins after switching to maker execution. Small sample, but directionally encouraging.

Follow the journey on [Twitter @acplabs_kr](https://twitter.com/acplabs_kr) for real-time trade updates.

---

*Disclaimer: Past backtesting results do not guarantee future performance. Cryptocurrency trading involves significant risk. This is not financial advice. I lost 98.8% of my capital before finding a positive-EV approach — and I still might lose the remaining $86.*
