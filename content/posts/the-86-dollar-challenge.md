---
title: "The $86 Challenge"
date: 2026-03-03T12:00:00+09:00
draft: false
tags: ["challenge", "trading-bot", "crypto", "journey", "deribit"]
categories: ["Journey"]
description: "After losing 98.8% of $7,714, I'm starting over with $86. Here's the plan, the strategy, and why I think it's possible."
weight: 1
---

## The Starting Point

**Account balance: $86.** That's what remains of a $7,714 Deribit trading account after 22 failed bot versions.

Let me put that in perspective. $7,714 was borrowed money. Four months of development, debugging at 3am, watching positions liquidate in real-time, rewriting the bot from scratch over and over. And at the end of it all: eighty-six dollars.

Most people would walk away. Close the account, eat the loss, tell themselves "crypto trading isn't for me" and move on. That's the rational thing to do.

I'm not doing the rational thing. I'm doubling down — but this time, with data.

## The Full Loss Timeline

Here's what $7,714 → $86 actually looked like:

**v1–v5: The Naive Phase (~$7,714 → $5,200)**
- Simple grid trading, momentum chasing
- No proper backtesting — "it looks good on the chart" reasoning
- Slow bleed from fees + bad entries
- Lost ~$2,500 over 3 weeks

**v6–v10: The "Fix It" Phase (~$5,200 → $2,800)**
- Added RSI, Bollinger Bands, multiple timeframes
- More complexity = more bugs = more losses
- One version had a bug where it opened positions in the wrong direction
- Another had SL and TP swapped for short positions
- Lost ~$2,400 over 2 weeks

**v11–v15: The Leverage Phase (~$2,800 → $800)**
- Thought the problem was position size, not strategy
- Increased leverage to "make back losses faster"
- Got liquidated 3 times in one week
- Lost ~$2,000 in 10 days

**v16–v22: The Sophistication Phase (~$800 → $86)**
- Machine learning signals, sentiment analysis, multi-agent systems
- More sophisticated but still paying taker fees
- The strategies were actually decent — they just couldn't overcome the fee drag
- Slow death by a thousand cuts

Total time: ~4 months. Total loss: $7,628 (98.8%).

## What Changed

### v1–v22: The Taker Era (RIP)

Every version from v1 to v22 paid taker fees (0.05%). I tried:
- Grid trading
- Momentum strategies  
- Mean reversion
- Scalping
- Trend following
- Multiple timeframes
- Machine learning signals

**All lost money.** Not because every strategy was bad, but because 0.05% per trade on 10x leverage eats 1% of equity per round trip. At 10 trades/day, that's 10% daily fee drag. No strategy can overcome that consistently.

The irony? Some of these strategies were profitable in backtesting — because the backtests assumed maker fees. I just didn't realize it at the time.

### The Discovery

After v22 failed, I did something I should have done from the start: a systematic grid search.

40 parameter combinations. Same strategy. Two fee conditions.

- **Under taker fees (0.05%)**: All 40 → bankrupt
- **Under maker fees (0.00%)**: Multiple profitable, best at +233%

Same code. Same data. Same parameters. The only difference was which fee tier the orders executed at.

It was like finding out you've been playing poker with a rigged deck — except you rigged it against yourself.

### v23: The Maker Revolution

Armed with this insight, I rebuilt everything for maker execution:

1. **Entry orders** rest in the order book (not cross it)
2. **Take profit orders** are limit orders (maker)
3. **Only stop losses** use market orders (taker) — because when you need to get out, you get out
4. **Patience is built into the strategy** — if the order doesn't fill, we wait

The first 6 trades after switching to v23 maker execution: **all winners**. Small sample, but directionally it confirmed the hypothesis.

## The Plan

### Strategy: v23.2 Maker Bot

After the initial success of v23, I ran a comprehensive [750-combination grid search](/posts/grid-search-750-combinations/) to optimize parameters:

| Parameter | Value | Why |
|-----------|-------|-----|
| Take Profit | 1.2% | Optimal from 750-combo grid search |
| Stop Loss | 0.8% | R:R = 1.5:1, enough room to breathe |
| Timeout | 240 min | Gives trends time to develop |
| EMA Buffer | 0.5% | Only trade established trends |
| Entry Fee | 0% (maker) | Limit orders that rest in book |
| TP Fee | 0% (maker) | Limit take-profit orders |
| SL Fee | 0.05% (taker) | Market stop-loss for safety |

### Backtest Results

Over 6 months of bear market data (BTC: $112K → $63K):
- **Return**: +11.98%
- **Max Drawdown**: 2.70%
- **Win Rate**: 50.8%
- **Trades**: 61 (selective, quality over quantity)

Is +12% in 6 months exciting? No. But compared to the previous 22 versions that all went to zero, it's revolutionary. This is the first strategy that shows **positive expected value** in backtesting with realistic fee modeling.

### The Math (Honest Version)

Starting: $86 (0.00124 BTC)

**Conservative case** (matching backtest, ~2% monthly):
- Month 1: $87.72
- Month 6: $96.84
- Month 12: $109.18
- Month 24: $138.76

That's... slow. At this rate, $86 → $7,000 would take about 19 years. Obviously not the plan.

**What needs to happen:**
1. **Add capital as strategy proves itself** — if v23.2 shows consistent positive results over 2-4 weeks, add more funds
2. **Better-than-backtest live performance** — backtests are usually conservative in trending markets
3. **Additional revenue streams** — blog, freelance, other projects feeding into the trading account
4. **Parameter optimization** — as more live data comes in, refine the strategy

The $86 isn't meant to compound to $7,000 on its own. It's a **proof of concept**. If the bot can consistently make positive returns at $86, the same strategy works at $860, $8,600, or $86,000. The hard part is proving the edge exists — scaling is just math.

## Milestones

| Milestone | Target | Significance |
|-----------|--------|-------------|
| $86 → $100 | +16% | ✅ Strategy works live |
| $100 → $250 | +150% | 💰 Add capital, increase size |
| $250 → $1,000 | +300% | 📈 Serious compounding begins |
| $1,000 → $7,000 | +600% | 🎯 Original capital recovered |
| $7,000 → ??? | ∞ | 🚀 Profit phase |

![The $86 Challenge milestones](/images/86-challenge-milestones.png)

## Rules

These aren't guidelines. They're laws. Breaking any of them is how I lost $7,714.

1. **No manual trading** — bot only. Every manual trade I've ever made was emotional, and every emotional trade lost money.
2. **No increasing leverage** — current settings only. "Just this once" is how liquidations happen.
3. **Every trade logged** — full transparency. If I can't show the data, I can't claim the results.
4. **If 3 consecutive losses** — stop and analyze before continuing. Losing streaks cascade when you let them run.
5. **Parameter changes require backtest validation** — no gut-feel adjustments. "I feel like TP should be higher" is not a valid reason.
6. **Stop loss is sacred** — never widen a stop loss on an open position. The SL was set for a reason; changing it mid-trade is gambling.

## Why I'm Sharing This

Because most trading content is fake. Screenshots of wins, hiding losses, selling courses about strategies they don't use. The "crypto influencer" playbook is: show a winning trade, hide nine losing ones, sell a $499 course.

This is different:
- **Real starting capital**: $86 (verifiable on-chain)
- **Real strategy**: Backtested with 264,000+ candles, grid-searched across 750+ combinations
- **Real losses**: I'm not pretending the $7,714 loss didn't happen — it's the foundation of everything I learned
- **Real-time updates**: Every trade posted to Twitter as it happens, win or lose

If the bot fails, you'll know. If it succeeds, you'll know exactly how and why. No BS, no cherry-picking, no fake screenshots.

## The Emotional Reality

I'll be honest about something most trading bloggers won't admit: watching $86 in an account that once held $7,714 is psychologically brutal.

Every trade feels heavier than it should. A $0.80 profit shouldn't matter — it's a coffee. But it represents a 1% gain on the only capital I have left. A $0.80 loss feels like confirmation that I should have quit months ago.

The bot helps with this. It doesn't feel emotions. It doesn't revenge-trade after a loss. It doesn't get greedy after a win. It executes the strategy exactly as programmed, every time.

That's why Rule #1 is "no manual trading." The bot is better at this than I am — not because it's smarter, but because it's incapable of being afraid.

## Follow Along

- **Twitter**: [@acplabs_kr](https://twitter.com/acplabs_kr) — real-time trade tweets with context
- **YouTube**: [$86 Challenge](https://youtube.com/@86challenge-u9v) — video updates and analysis
- **This blog** — deep dives into strategy, backtesting, and results

---

*Day 1 of the $86 Challenge. $86 in the account, a bot that's statistically proven to have positive EV, and nothing to lose except eighty-six dollars. Let's see where this goes.*
