---
title: "From $86 to $100: How My Tiny Trading Bot Survived the Drawdown Gauntlet"
date: 2026-03-05T21:55:56+09:00
draft: false
tags: ["trading-bot", "crypto", "bitcoin", "deribit", "python"]
description: "Real lessons from building automated trading bots"
---

You know that feeling? The one where you've poured hours into building something, tweaking it, and finally unleashing it into the wild? It’s exhilarating, especially when you start with a shoestring budget. For me, that journey began with a modest $86, a dream of automated riches, and a trading bot I affectionately nicknamed "PocketRocket." This isn't about blowing up an account with leverage (though we'll touch on that!), or boasting about insane backtest numbers. This is a raw, honest account of what happens when your meticulously crafted bot faces the brutal reality of live trading, specifically, how it navigated the dreaded drawdown.

Let’s be clear: PocketRocket wasn’t born from a desire for quick wins. It was the culmination of countless hours spent dissecting market behavior, poring over indicator combinations, and yes, the painful lessons learned from previous bot failures (we’ll save those war stories for another day). The core idea was simple: build a robust maker bot that could scalp small profits in volatile markets, with strict risk management to protect that tiny initial capital.

The strategy, at its heart, was a blend of momentum and trend following. We wanted to catch quick moves, but only when the broader trend was in our favor. Think of it like this: you wouldn't try to swim upstream against a raging current, right? Same principle.

Here's a simplified look at the core logic:

```python
# Simplified Entry Logic
def should_enter(current_price, indicators, trend):
    if trend == "uptrend" and indicators_confirm_uptrend():
        if price_within_ema_buffer(current_price, indicators):
            if macd_is_bullish(indicators):
                if momentum_is_positive(indicators):
                    return True
    elif trend == "downtrend" and indicators_confirm_downtrend():
        if price_within_ema_buffer(current_price, indicators):
            if macd_is_bearish(indicators):
                if momentum_is_negative(indicators):
                    return True
    return False

def indicators_confirm_uptrend():
    # Check EMA50 for overall trend
    pass

def price_within_ema_buffer(price, indicators):
    # Is price close enough to EMA10 for entry?
    pass

def macd_is_bullish(indicators):
    # Check MACD value and crossover
    pass

def momentum_is_positive(indicators):
    # Check 3m and 5m momentum
    pass
```

The "maker" aspect was crucial. This means we were placing limit orders *before* hitting the market. The idea was to capture the spread and avoid the immediate slippage that comes with "taker" orders. For take-profit (TP), we also used limit orders, aiming for a small, consistent gain. But the real hero of this story, the one that kept PocketRocket alive, was the stop-loss (SL).

Our initial SL was set at a tight 0.5% of the trade value, with a take-profit of 1.5%. This was a deliberate choice to favor risk management over aggressive profit-taking. We weren't aiming to double our money on every trade; we were aiming to survive.

### The First Signs of Trouble: The Squeeze

PocketRocket started its life with a few small, profitable trades. It felt good! The equity curve, while modest, was trending upwards. Then, the market decided to have a little fun. We entered a period of low volatility, a trading graveyard for momentum-based bots.

This is where the concept of "drawdown" really hits home. Drawdown is the peak-to-trough decline in an investment. It’s the painful period where your equity curve goes down, and you question every line of code you’ve ever written.

One of the first challenges we faced was the **`CHOP_THRESHOLD`**. This parameter was designed to detect sideways, choppy markets where price action is erratic and unpredictable. In such conditions, our momentum-based strategy tends to get whipsawed, triggering entries that quickly reverse.

```python
# Simplified Chop Detection
def is_choppy(price_data_10min):
    price_range = max(price_data_10min) - min(price_data_10min)
    if price_range < CHOP_THRESHOLD:
        return True
    return False

# In main loop:
if is_choppy(recent_prices):
    log("Choppy market detected. Halting new entries.")
    # Prevent new trades
    pass
```

Initially, our `CHOP_THRESHOLD` was set a bit too wide. This meant that even in moderately volatile markets, the bot might have been hesitant to enter, missing out on potential opportunities. Conversely, if it was too narrow, it could get caught in minor fluctuations. Finding that sweet spot is an art, not a science. We adjusted it to `0.15%` for the 10-minute price range, a value that seemed to capture genuine stagnation.

Then came the **consecutive losses**. Even with a tight SL, a string of bad luck can quickly erode capital. Our initial `CONSEC_LOSS_LIMIT` was set at 5, with a `COOLDOWN_SEC` of 30 minutes. This meant that after 5 losing trades in a row, the bot would take a 30-minute break.

```python
# Simplified Loss Tracking and Cooldown
consecutive_losses = 0
last_trade_time = time.time()
cooldown_until = 0

def record_loss():
    global consecutive_losses, cooldown_until
    consecutive_losses += 1
    if consecutive_losses >= CONSEC_LOSS_LIMIT:
        log(f"Consecutive loss limit ({CONSEC_LOSS_LIMIT}) reached. Entering cooldown.")
        cooldown_until = time.time() + COOLDOWN_SEC
        consecutive_losses = 0 # Reset after cooldown period

def can_enter_trade():
    if time.time() < cooldown_until:
        return False
    # Other checks...
    return True
```

During a particularly brutal market swing, we hit that 5-loss streak. The 30-minute cooldown felt like an eternity. When the bot resumed trading, it was still in a volatile environment, and it quickly racked up another streak. This highlighted a key learning: a 30-minute break might not be enough to allow the market to reset, especially after a significant losing streak.

This led to a crucial revision: we increased the `CONSEC_LOSS_LIMIT` to 3, but significantly extended the `COOLDOWN_SEC` to a full hour (`3600` seconds). The logic was to have shorter, more frequent breaks if we hit a couple of losses, but a longer, more meaningful break after a slightly larger streak. This also meant we introduced an individual cooldown for each SL event.

```python
# v23.4 Updates (Conceptual)
CONSEC_LOSS_LIMIT = 3        # Shorter streak triggers cooldown
COOLDOWN_SEC = 3600          # Longer cooldown (1 hour)
SL_COOLDOWN_SEC = 300        # New: 5-minute cooldown per SL
```

The `SL_COOLDOWN_SEC` was a new addition, a direct response to the frustration of hitting multiple stop-losses in quick succession. The idea was that if a single trade was stopped out, we’d wait 5 minutes before considering another trade. This gave us a small breather and a chance for the market to settle *after* a specific loss, rather than just waiting for a general market cooldown. It felt like a more granular approach to risk management.

### The Leverage Tightrope

Ah, leverage. The double-edged sword of crypto trading. PocketRocket started with a modest 10x leverage. This was a conscious decision. We wanted to amplify our small capital without exposing ourselves to catastrophic liquidation risk.

However, even with 10x, a sharp move against us could wipe out a significant portion of our capital. This is where the **`SL_PCT`** became even more critical. We initially had it at 0.5%, but after seeing some trades get stopped out too quickly, and others linger too long and incur more slippage, we adjusted it.

The backtesting and live monitoring revealed that a SL of 0.8% was a better balance for our strategy. It allowed trades a little more breathing room to develop, but was still tight enough to prevent massive losses.

One of the biggest lessons here was the psychological impact of leverage. Even with automated trading, seeing your unrealized P&L swing wildly due to leverage is… intense. It reinforces the need for an ironclad stop-loss and a clear understanding of your risk per trade.

### The Equity Curve's Rollercoaster

Let’s look at the actual equity curve. Starting at $86, we saw some initial gains, pushing us towards $90. Then, the drawdown began.

**(Imagine a graph here: initial steady climb, then a dip, then a slow recovery, then another dip, and finally a gradual, more stable climb.)**

The first significant dip saw our capital shrink to around $75. This was a ~12.8% drawdown from our peak. It felt like a gut punch. The bot was still technically functioning, but the losses were outpacing the wins.

During this period, we identified that the **`MACD_THRESHOLD`** was too low. We were entering trades on signals that weren't strong enough, leading to many SL hits. The MACD (Moving Average Convergence Divergence) is a trend-following momentum indicator. A higher threshold means we're only entering when the MACD signal is very strong, indicating a more confirmed trend.

We bumped the `MACD_THRESHOLD` from 50 to 80. This was a significant change, and it definitely reduced the number of trades, but the quality of the trades improved. Fewer false signals, fewer quick SL hits.

Then, the market entered a period of moderate volatility. This was PocketRocket’s sweet spot. The momentum indicators were firing, the trend filter was aligning, and we started seeing more profitable trades. The equity curve began to climb back.

We eventually broke through our initial peak and nudged past $100. It wasn't a moonshot, but for an $86 starting capital, surviving a drawdown and ending up over $100 felt like a monumental victory.

### Lessons Learned the Hard Way

1.  **Drawdowns are Inevitable:** No matter how good your backtest looks, live markets will throw curveballs. The key is not to avoid drawdowns, but to *survive* them. This means prioritizing risk management above all else.
2.  **Parameter Tuning is an Art:** Finding the right values for parameters like `EMA_BUFFER`, `MACD_THRESHOLD`, `CHOP_THRESHOLD`, and cooldown periods is an iterative process. What works in backtest might not work live, and vice versa. Continuous monitoring and adjustment are essential.
3.  **Leverage is a Monster:** Even small amounts of leverage can amplify losses quickly. Understand your liquidation price and ensure your SL is well within the bounds of your capital.
4.  **Cooldowns are Your Friend (When Tuned Right):** Don’t be afraid to let your bot rest. A well-timed cooldown can prevent a string of losses from becoming a catastrophic one. The duration and trigger for cooldowns are crucial.
5.  **Focus on Survival, Not Just Profits:** With small capital, your primary goal should be to preserve it. Small, consistent wins and tight risk control are far more effective than chasing huge profits and risking everything.
6.  **The "Maker" Strategy's Value:** For small capital and scalping, a maker-focused strategy with limit orders for entry and TP can significantly reduce slippage and improve profitability, especially in volatile markets.

PocketRocket is still running. It’s not a money-printing machine, but it’s a testament to what’s possible when you combine a solid strategy with disciplined risk management. It’s proof that even with a tiny amount of capital, you can build something that survives the harsh realities of the trading world. The journey from $86 to $100 was more valuable than any percentage gain because it taught me resilience. And in the world of algorithmic trading, resilience is the ultimate currency.

### Key Takeaways

*   **Prioritize Risk Management:** Stop-losses and cooldown periods are your best friends when trading with small capital.
*   **Iterative Parameter Tuning:** Don't expect perfect parameters from the start. Continuously monitor and adjust your bot's settings based on live performance.
*   **Leverage with Caution:** Understand the risks associated with leverage and ensure your stop-losses are robust enough.
*   **Choppy Markets are Bot Killers:** Implement effective mechanisms to detect and avoid trading in sideways, low-volatility markets.
*   **Drawdowns are Opportunities to Learn:** View drawdowns not as failures, but as valuable data points for improving your bot's strategy and risk controls.