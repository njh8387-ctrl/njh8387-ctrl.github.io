---
title: "The Fee That Bankrupted 22 Bots"
date: 2026-03-02
draft: false
tags: ["fees", "maker-taker", "trading-bot", "lessons", "crypto"]
categories: ["Lessons"]
description: "I lost 98.8% of my capital before discovering that taker fees (0.05%) made every strategy negative EV. Here's the data."
---

## The $7,714 Lesson

Over 4 months, I built and deployed 22 versions of a BTC perpetual futures trading bot. Every single one lost money. Starting from $7,714, I watched my account shrink to $86 — a **98.8% loss**.

The losses came from everything: leverage liquidations, code bugs, bad parameters, manual panic sells at the worst prices. But when I finally sat down to figure out why **no strategy ever worked** — not even promising ones — the answer was simpler than I expected: **the fee structure**.

I want to be clear upfront: fees didn't directly cause $7,628 in losses. Liquidations, bugs, and bad decisions did most of that damage. But fees were the invisible force that made every strategy's expected value negative. Even a perfectly executed strategy with taker fees was a losing proposition. I just didn't know it.

## The Versions That Failed

Before I get to the data, let me show you what "22 versions" actually means. Each one felt like it could be The One.

**v1**: Simple moving average crossover. "If SMA20 crosses above SMA50, buy." Lost money because it was always late to the trend. By the time the crossover happened, the move was half over.

**v3**: Added RSI filtering. "Only buy when RSI < 30." Problem: in a strong downtrend, RSI can stay below 30 for days. Kept buying the dip of the dip of the dip.

**v6**: Grid trading with 5 layers. Mathematically elegant, practically a nightmare. Works beautifully in ranging markets, hemorrhages money in trending ones. And crypto trends a lot.

**v11**: Increased leverage to 25x to "make back losses faster." Got liquidated in 4 hours. This was the worst version, psychologically and financially.

**v16**: The first actually sophisticated version. Multi-timeframe analysis, MACD + RSI + Bollinger confluence, dynamic position sizing. It backtested beautifully. Live, it slowly bled out over 2 weeks. I couldn't figure out why.

**v20**: Added machine learning (basic random forest on 15 features). Slightly better win rate than v16, but still lost money. The ML model was predicting direction correctly ~53% of the time — and still losing because of fees.

**v22**: My best version before the breakthrough. Trend-following with EMA filters, adaptive parameters, proper risk management. Everything I learned from v1–v21 distilled into one bot. It lost $200 in a week.

The frustrating part? The strategy logic in v22 was actually sound. If I'd been running it with maker fees from the start, it would have been profitable. But I didn't know that yet.

## The Grid Search That Changed Everything

After v22 failed, I was ready to quit. But first, I wanted to understand **why**. Not "it lost money" — I knew that. I wanted to know whether any combination of parameters could have been profitable, or whether the entire approach was fundamentally flawed.

So I ran a grid search across **40 parameter combinations**:

- Take Profit: 0.3%, 0.5%, 0.8%, 1.0%, 1.5%
- Stop Loss: 0.2%, 0.3%, 0.5%, 0.8%
- Timeouts: 15min, 30min, 60min, 120min

All tested against 6 months of BTC 1-minute data (264,062 candles, $112K → $63K bear market).

### Under Taker Fees (0.05%)

**Every. Single. Combination. Went. Bankrupt.**

Not "lost a little" — went to zero. The best performer still ended at -87%. The worst hit zero within the first month.

I stared at those results for a long time. 40 combinations. Every reasonable parameter set I could think of. All bankrupt.

### Under Maker Fees (0%)

On a whim, I changed one line of code — the fee from 0.0005 to 0.0000 — and re-ran the entire grid search.

The same strategies? Many were profitable. The best returned **+233%**.

```
Same strategy. Same data. Same parameters.
Taker (0.05%): -100% (bankrupt)
Maker (0.00%): +233% (profitable)
```

I checked the code three times. I thought there was a bug. There wasn't.

![Same strategy, different fees — maker vs taker equity curves](/images/fee-impact-equity-curve.png)

## Why 0.05% Matters So Much

0.05% sounds like nothing. It's less than a rounding error. How can it possibly be the difference between +233% and bankruptcy?

Let me walk through the math.

### Per-Trade Impact

On a $100 position with 10x leverage, the actual notional is $1,000.

- **Taker fee per trade**: $1,000 × 0.05% = $0.50
- **Round trip** (open + close): $1.00
- **As % of equity**: 1.0% per trade

If your strategy targets 1% TP, **the entire profit goes to fees**. You need the price to move 1% just to break even.

But wait — that's only for winning trades. Losing trades also pay fees. So a 0.8% SL becomes effectively 1.8% after fees (0.8% loss + 0.5% entry fee + 0.5% exit fee, as percentage of equity).

Your 1.25:1 R:R ratio (1.0% TP / 0.8% SL) becomes 0:1.8 — you make nothing on wins and lose 1.8% on losses.

### The Compounding Effect

Average trades per day for my bot: 8-15

At 10 trades/day with 0.05% taker:
- Fee per trade: 1.0% of equity
- Daily fee cost: ~10% of equity
- Weekly: ~70% of equity
- Monthly: ~300% of equity

**You'd need to triple your money monthly just to cover fees.** No strategy can do that consistently. Not even close.

### The Invisible Killer

Here's what makes this so insidious: you can't see it in individual trades. A single $0.50 fee on a $100 account doesn't register. It's noise. You attribute losses to "bad entries," "wrong timing," "the market moved against me."

But plot your equity curve against what it would have been without fees, and you see two lines diverging relentlessly. The fee-free line trends up. The fee line trends down. Every trade, the gap widens.

It's not one fee that kills you. It's ten thousand fees.

## How Maker Orders Work

The key difference:

| Order Type | Adds Liquidity? | Fee on Deribit |
|-----------|----------------|----------------|
| Market order | No (taker) | 0.05% |
| Limit order (crosses book) | No (taker) | 0.05% |
| Limit order (rests in book) | Yes (maker) | 0.00% |

**Critical detail**: a limit order can still be a taker if it crosses the spread. If BTC is at $68,000 bid / $68,001 ask, and you place a limit buy at $68,001, it crosses the ask and executes as a taker (0.05%).

To guarantee maker execution, your limit order must **rest in the order book** — it can't immediately match with an existing order.

In practice, this means:
- For **long entries**: place limit buy at or below the current best bid
- For **take profit**: place limit sell at or above the current best ask
- Wait for the market to come to you

### The Post-Only Flag

Most exchanges offer a "post-only" flag for limit orders. With this flag:
- If the order would execute immediately (taker), it's **rejected** instead
- Only orders that rest in the book (maker) are accepted

This is essential for a maker bot. Without it, price spikes could turn your maker orders into taker orders, silently eating your edge.

```python
# Deribit API: post-only order
order = client.buy(
    instrument_name='BTC-PERPETUAL',
    amount=size,
    type='limit',
    price=entry_price,
    post_only=True  # Reject if would be taker
)
```

## The Tradeoff

Maker orders aren't free lunch. There are real costs to this approach:

| Aspect | Taker | Maker |
|--------|-------|-------|
| Fee | 0.05% | 0.00% |
| Execution | Instant, guaranteed | May not fill |
| Slippage | Possible | None |
| Strategy | Reactive | Patient |
| Speed | Milliseconds | Minutes to hours |
| Fill Rate | 100% | 60-80% |

You trade speed for savings. Your bot needs to be comfortable waiting — and comfortable with orders that never fill. Some of the best setups will pass you by because the price moved before your limit order was hit.

This is psychologically harder than it sounds. Watching a perfect setup play out exactly as predicted, except your order was 0.5% below where price went, is maddening. The taker voice in your head says "just use a market order, you'll catch the move."

Don't listen. The math is the math.

### The Fill Rate Problem

In my backtesting, maker orders have roughly a 70% fill rate. That means 30% of signals — potential winning trades — are missed because the price never reaches the limit order.

This sounds terrible. But consider: missing 30% of trades while paying 0% fees is vastly better than catching 100% of trades while paying 1% per round trip.

Let's compare (hypothetical 100 signals, 50% win rate, 1.2% TP, 0.8% SL):

**Taker (100% fill rate)**:
- 50 wins × (1.2% - 1.0% fee) = 50 × 0.2% = +10%
- 50 losses × (-0.8% - 1.0% fee) = 50 × -1.8% = -90%
- **Net: -80%**

**Maker (70% fill rate)**:
- 35 wins × 1.2% = +42%
- 35 losses × -0.8% = -28%
- **Net: +14%**

The maker bot makes 14% while the taker bot loses 80%. And the taker bot traded 43% more.

## My v23 Approach

After this discovery, I rebuilt the bot from scratch (v23) with maker-only execution:

1. **Entry**: Calculate ideal entry price based on EMA trend, post limit order, wait for fill
2. **Take Profit**: Post limit order immediately after entry fill, at TP price (0% fee)
3. **Stop Loss**: Still uses market order (safety > savings) — the only taker order in the system
4. **Unfilled Entries**: Cancel after timeout, no FOMO chasing
5. **Result**: First 6 trades after switching — all winners

The fee savings alone transformed a losing strategy into a winning one. The actual win rate didn't change dramatically — it went from ~45% to ~51%. But every win now kept its full profit, and every loss was 1% smaller (no entry fee).

## What I'd Tell Past Me

If I could go back to v1, here's what I'd say:

1. **Calculate fee impact before writing a single line of strategy code.** If your expected profit per trade is less than 2× the round-trip fee, the strategy is dead on arrival.

2. **Maker execution is not optional.** For high-frequency strategies (>5 trades/day), it's the difference between positive and negative EV. Not a nice-to-have — a requirement.

3. **Backtest with realistic fees.** If your backtest assumes 0% fees but your bot pays 0.05%, your beautiful equity curve is fiction. I produced many beautiful fiction curves.

4. **The best strategy with the wrong execution is a losing strategy.** v22 was a good strategy. It would have been profitable with maker fees. But I ran it with taker fees, and it lost $200 in a week.

5. **Check your assumptions before blaming the strategy.** I spent 4 months "improving" strategies that were fine. The problem was never the strategy — it was the execution cost.

## For Other Bot Builders

If you're building a crypto trading bot, please do this before anything else:

```python
# Calculate your minimum required edge
taker_fee = 0.0005  # 0.05%
leverage = 10
fee_as_equity_pct = taker_fee * leverage * 2  # round trip

trades_per_day = 10
daily_fee_drag = fee_as_equity_pct * trades_per_day

print(f"Fee per round trip: {fee_as_equity_pct:.1%} of equity")
print(f"Daily fee drag: {daily_fee_drag:.0%} of equity")
print(f"Monthly fee drag: {daily_fee_drag * 30:.0%} of equity")
print(f"Your strategy needs to generate >{daily_fee_drag:.0%}/day just to break even")
```

For Deribit BTC perpetuals with 10x leverage and 10 trades/day:
```
Fee per round trip: 1.0% of equity
Daily fee drag: 10% of equity
Monthly fee drag: 300% of equity
Your strategy needs to generate >10%/day just to break even
```

If those numbers don't scare you, re-read them.

![How taker fees compound over multiple trades](/images/fee-compound-chart.png)

---

*22 versions. $7,714 lost to liquidations, bugs, bad params, and invisible fee drag. One insight — switching from taker to maker — finally made the math work.*
