---
title: "Build Your Own Backtesting Engine"
date: 2026-02-28
draft: false
tags: ["python", "backtesting", "tutorial", "crypto", "trading-bot"]
categories: ["Tutorial"]
description: "Step-by-step guide to building a backtesting engine that processes 264,000+ candles in under 60 seconds. Includes EMA, position management, and fee modeling."
---

## Why Build Your Own?

Existing backtesting frameworks (Backtrader, Zipline, VectorBT) are powerful but opaque. When your money is on the line, you need to understand every line of code. Building your own also forces you to think about edge cases that libraries abstract away.

## Architecture

Our backtester processes 264,062 one-minute candles in ~43 seconds. Here's the structure:

![Backtesting engine architecture](/images/backtest-architecture.png)

```python
class Backtester:
    def __init__(self, candles, params):
        self.candles = candles
        self.equity = params['initial_equity']
        self.trades = []
        self.params = params
    
    def run(self):
        for i, candle in enumerate(self.candles):
            self.update_indicators(i)
            
            if self.has_position:
                self.check_exit(candle)
            else:
                self.check_entry(candle)
        
        return self.calculate_metrics()
```

## Step 1: Data Loading

We use Deribit's API to fetch historical 1-minute candles:

```python
import json
import time

def fetch_candles(instrument, start_ts, end_ts, resolution=1):
    """Fetch 1-min candles from Deribit public API"""
    candles = []
    current = start_ts
    
    while current < end_ts:
        params = {
            'instrument_name': instrument,
            'start_timestamp': current,
            'end_timestamp': min(current + 86400000, end_ts),
            'resolution': resolution
        }
        # API call here...
        # Rate limit: 1 request per second
        time.sleep(1)
        current += 86400000
    
    return candles
```

**Pro tip**: Save the data locally. Our 6-month dataset is 17.6MB as JSON. Fetching it takes hours; loading it takes milliseconds.

```python
# Save once
with open('backtest_data_6m.json', 'w') as f:
    json.dump(candles, f)

# Load instantly
with open('backtest_data_6m.json') as f:
    candles = json.load(f)
```

## Step 2: EMA Calculation

We use EMA (Exponential Moving Average) for trend detection:

```python
def calculate_ema(prices, period):
    """Calculate EMA with proper initialization"""
    if len(prices) < period:
        return None
    
    multiplier = 2 / (period + 1)
    
    # Initialize with SMA
    ema = sum(prices[:period]) / period
    
    # Calculate EMA for remaining prices
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema
```

**Key insight**: We track two EMAs — EMA10 (fast) and EMA50 (slow). When EMA10 > EMA50 by more than our buffer threshold, we consider the trend "up" and only take long positions.

## Step 3: Position Management

```python
class Position:
    def __init__(self, side, entry_price, size, entry_time):
        self.side = side
        self.entry_price = entry_price
        self.size = size
        self.entry_time = entry_time
    
    def unrealized_pnl(self, current_price):
        if self.side == 'long':
            return (current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - current_price) / self.entry_price
    
    def should_take_profit(self, current_price, tp_pct):
        return self.unrealized_pnl(current_price) >= tp_pct
    
    def should_stop_loss(self, current_price, sl_pct):
        return self.unrealized_pnl(current_price) <= -sl_pct
    
    def should_timeout(self, current_time, max_hold):
        return (current_time - self.entry_time) >= max_hold
```

## Step 4: Fee Modeling (Critical!)

This is where most backtests lie. If you don't model fees correctly, your results are fiction.

```python
def calculate_fee(notional, order_type='maker'):
    fees = {
        'maker': 0.0000,   # Deribit maker: 0%
        'taker': 0.0005,   # Deribit taker: 0.05%
    }
    return notional * fees[order_type]

def execute_trade(self, side, price, exit_type):
    # Entry: maker order (limit, rests in book)
    entry_fee = calculate_fee(self.position_size, 'maker')
    
    # Exit depends on type:
    if exit_type == 'tp':
        exit_fee = calculate_fee(self.position_size, 'maker')  # TP is limit order
    elif exit_type == 'sl':
        exit_fee = calculate_fee(self.position_size, 'taker')  # SL is market order
    
    total_fee = entry_fee + exit_fee
    net_pnl = gross_pnl - total_fee
```

## Step 5: Grid Search

```python
from itertools import product

def grid_search(candles, param_grid):
    results = []
    
    combinations = list(product(
        param_grid['tp'],
        param_grid['sl'],
        param_grid['timeout'],
        param_grid['ema_buffer']
    ))
    
    for tp, sl, timeout, buffer in combinations:
        params = {
            'tp': tp, 'sl': sl,
            'timeout': timeout, 'ema_buffer': buffer,
            'initial_equity': 0.001  # BTC
        }
        
        bt = Backtester(candles, params)
        result = bt.run()
        results.append({
            'params': params,
            'return': result['total_return'],
            'mdd': result['max_drawdown'],
            'win_rate': result['win_rate'],
            'trades': result['total_trades']
        })
    
    # Sort by return
    results.sort(key=lambda x: x['return'], reverse=True)
    return results
```

## Step 6: Metrics

```python
def calculate_metrics(self):
    if not self.trades:
        return None
    
    wins = [t for t in self.trades if t['pnl'] > 0]
    losses = [t for t in self.trades if t['pnl'] <= 0]
    
    return {
        'total_return': (self.equity - self.initial) / self.initial,
        'win_rate': len(wins) / len(self.trades),
        'profit_factor': sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses)),
        'max_drawdown': self.max_drawdown,
        'total_trades': len(self.trades),
        'avg_win': np.mean([t['pnl'] for t in wins]),
        'avg_loss': np.mean([t['pnl'] for t in losses]),
        'sharpe': self.calculate_sharpe()
    }
```

## Performance Tips

1. **Pre-compute indicators**: Calculate all EMAs once, not per-trade
2. **Use numpy for arrays**: 10x faster than Python lists for math
3. **Cache candle data**: Load from disk, not API
4. **Parallelize grid search**: Use `multiprocessing.Pool` for independent combinations
5. **Profile your code**: Our bottleneck was EMA recalculation — pre-computing saved 40% runtime

## Full Example Run

```
Grid search: 750 combinations
Data: 264,062 candles (6 months)
Time: 43 seconds
Best result: TP=1.2%, SL=0.8%, T=240min, Buffer=0.5%
  → Return: +11.98%, MDD: 2.70%, WR: 50.8%, 61 trades
```

---

*The complete backtesting framework is proprietary, but the concepts above are everything you need to build your own. The edge isn't in the code — it's in knowing what to test.*
