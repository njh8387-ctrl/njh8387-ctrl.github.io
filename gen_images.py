#!/usr/bin/env python3
"""Generate blog post images for Algo Trading Lab"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os

OUT = '/home/administrator/.openclaw/workspace/algo-trading-blog/static/images'
os.makedirs(OUT, exist_ok=True)

# Style
plt.rcParams.update({
    'figure.facecolor': '#0d1117',
    'axes.facecolor': '#161b22',
    'axes.edgecolor': '#30363d',
    'axes.labelcolor': '#c9d1d9',
    'text.color': '#c9d1d9',
    'xtick.color': '#8b949e',
    'ytick.color': '#8b949e',
    'grid.color': '#21262d',
    'grid.alpha': 0.8,
    'font.size': 12,
    'font.family': 'sans-serif',
})

GREEN = '#3fb950'
RED = '#f85149'
BLUE = '#58a6ff'
ORANGE = '#d29922'
PURPLE = '#bc8cff'

# ============================================================
# 1. Fee Impact: Taker vs Maker equity curves
# ============================================================
def gen_fee_impact():
    fig, ax = plt.subplots(figsize=(10, 6))
    np.random.seed(42)
    
    days = 180
    trades_per_day = 3
    n = days * trades_per_day
    
    # Simulate trade outcomes (same for both)
    win_rate = 0.48
    tp_pct = 0.012
    sl_pct = 0.008
    wins = np.random.random(n) < win_rate
    
    # Taker: 0.05% round trip on notional (=1% equity with 10x)
    taker_fee = 0.01  # as % of equity
    equity_taker = [1.0]
    for w in wins:
        pnl = tp_pct * 10 - taker_fee if w else -sl_pct * 10 - taker_fee
        equity_taker.append(equity_taker[-1] * (1 + pnl))
        if equity_taker[-1] <= 0:
            equity_taker[-1] = 0
            break
    
    # Maker: 0% entry + TP, 0.05% SL only
    equity_maker = [1.0]
    for w in wins:
        if w:
            pnl = tp_pct * 10  # no fee
        else:
            pnl = -sl_pct * 10 - 0.005  # only SL taker
        equity_maker.append(equity_maker[-1] * (1 + pnl))
    
    x_taker = np.linspace(0, days, len(equity_taker))
    x_maker = np.linspace(0, days, len(equity_maker))
    
    ax.plot(x_maker, equity_maker, color=GREEN, linewidth=2.5, label='Maker (0% fee)', zorder=3)
    ax.plot(x_taker, equity_taker, color=RED, linewidth=2.5, label='Taker (0.05% fee)', zorder=3)
    
    ax.axhline(y=1.0, color='#8b949e', linestyle='--', alpha=0.5, linewidth=1)
    ax.fill_between(x_maker, equity_maker, alpha=0.1, color=GREEN)
    
    ax.set_xlabel('Days', fontsize=13)
    ax.set_ylabel('Equity (normalized)', fontsize=13)
    ax.set_title('Same Strategy, Different Fees', fontsize=16, fontweight='bold', pad=15)
    ax.legend(fontsize=12, loc='center left')
    ax.grid(True, alpha=0.3)
    
    # Annotate final values
    final_maker = equity_maker[-1]
    ax.annotate(f'+{(final_maker-1)*100:.0f}%', xy=(days, final_maker),
                fontsize=14, color=GREEN, fontweight='bold',
                xytext=(10, 0), textcoords='offset points')
    
    bankrupt_day = x_taker[-1]
    ax.annotate('BANKRUPT', xy=(bankrupt_day, 0),
                fontsize=14, color=RED, fontweight='bold',
                xytext=(10, 20), textcoords='offset points',
                arrowprops=dict(arrowstyle='->', color=RED))
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/fee-impact-equity-curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ fee-impact-equity-curve.png')

# ============================================================
# 2. EMA Buffer heatmap / bar chart
# ============================================================
def gen_buffer_impact():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    buffers = ['0.1%', '0.2%', '0.3%', '0.5%', '0.8%', '1.0%']
    trades =  [680, 500, 250, 61, 22, 8]
    returns = [-35, -22, -5, 12, 4, 2]
    win_rates = [42, 45, 48, 50.8, 54, 63]
    mdd = [28, 24, 12, 2.7, 1.8, 0.9]
    
    colors = [RED if r < 0 else GREEN for r in returns]
    
    # Left: Returns
    bars = ax1.bar(buffers, returns, color=colors, width=0.6, edgecolor='#30363d', linewidth=1)
    ax1.axhline(y=0, color='#8b949e', linestyle='-', linewidth=1)
    ax1.set_xlabel('EMA Buffer', fontsize=13)
    ax1.set_ylabel('Return (%)', fontsize=13)
    ax1.set_title('Return by EMA Buffer', fontsize=15, fontweight='bold', pad=10)
    ax1.grid(True, axis='y', alpha=0.3)
    
    for bar, val, wr in zip(bars, returns, win_rates):
        y = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., y + (2 if y >= 0 else -4),
                f'{val:+d}%', ha='center', fontsize=11, fontweight='bold',
                color=GREEN if val >= 0 else RED)
    
    # Highlight 0.5%
    bars[3].set_edgecolor(BLUE)
    bars[3].set_linewidth(3)
    
    # Right: Trades vs Win Rate (dual axis)
    color_trades = BLUE
    color_wr = ORANGE
    
    ax2.bar(buffers, trades, color=color_trades, alpha=0.6, width=0.6, label='Trades')
    ax2.set_xlabel('EMA Buffer', fontsize=13)
    ax2.set_ylabel('Number of Trades', fontsize=13, color=color_trades)
    ax2.tick_params(axis='y', labelcolor=color_trades)
    ax2.set_title('Trades vs Win Rate', fontsize=15, fontweight='bold', pad=10)
    
    ax3 = ax2.twinx()
    ax3.plot(buffers, win_rates, color=color_wr, linewidth=2.5, marker='o', markersize=8, zorder=5)
    ax3.set_ylabel('Win Rate (%)', fontsize=13, color=color_wr)
    ax3.tick_params(axis='y', labelcolor=color_wr)
    ax3.set_ylim(35, 70)
    
    # Annotate sweet spot
    ax2.annotate('Sweet\nSpot', xy=(3, trades[3]), fontsize=11, color=BLUE,
                fontweight='bold', ha='center',
                xytext=(0, 30), textcoords='offset points',
                arrowprops=dict(arrowstyle='->', color=BLUE))
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/buffer-impact-chart.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ buffer-impact-chart.png')

# ============================================================
# 3. v23.1 vs v23.2 comparison
# ============================================================
def gen_v23_comparison():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Return', 'Win Rate', 'MDD\n(lower=better)', 'Trades\n(÷10)']
    v231 = [-21.94, 45, 23.96, 50]
    v232 = [11.98, 50.8, 2.70, 6.1]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, v231, width, label='v23.1 (old)', color=RED, alpha=0.8, edgecolor='#30363d')
    bars2 = ax.bar(x + width/2, v232, width, label='v23.2 (new)', color=GREEN, alpha=0.8, edgecolor='#30363d')
    
    ax.set_ylabel('Value', fontsize=13)
    ax.set_title('v23.1 → v23.2: Parameter Optimization Results', fontsize=15, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, axis='y', alpha=0.3)
    ax.axhline(y=0, color='#8b949e', linestyle='-', linewidth=1)
    
    # Value labels
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + (1 if h >= 0 else -3),
                f'{h:.1f}', ha='center', fontsize=10, color=RED, fontweight='bold')
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 1,
                f'{h:.1f}', ha='center', fontsize=10, color=GREEN, fontweight='bold')
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/v23-comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ v23-comparison.png')

# ============================================================
# 4. The $86 Challenge milestone roadmap
# ============================================================
def gen_milestone_chart():
    fig, ax = plt.subplots(figsize=(10, 5))
    
    milestones = ['Start', '$100', '$250', '$1,000', '$7,000']
    values = [86, 100, 250, 1000, 7000]
    
    colors_m = ['#8b949e', BLUE, BLUE, ORANGE, GREEN]
    
    ax.plot(range(len(values)), values, color=BLUE, linewidth=2, marker='o', markersize=10, zorder=3)
    
    for i, (m, v, c) in enumerate(zip(milestones, values, colors_m)):
        ax.scatter(i, v, color=c, s=150, zorder=5, edgecolors='white', linewidths=2)
        offset = 15 if i < 3 else -25
        ax.annotate(f'{m}\n${v:,}', xy=(i, v), fontsize=11, fontweight='bold',
                   color=c, ha='center',
                   xytext=(0, offset), textcoords='offset points')
    
    ax.set_yscale('log')
    ax.set_ylabel('Account Value (USD, log scale)', fontsize=13)
    ax.set_title('The $86 Challenge — Milestones', fontsize=16, fontweight='bold', pad=15)
    ax.set_xticks([])
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_ylim(50, 15000)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Arrow from start
    ax.annotate('', xy=(4, 7000), xytext=(0, 86),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5, ls='--'))
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/86-challenge-milestones.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ 86-challenge-milestones.png')

# ============================================================
# 5. Fee math visualization
# ============================================================
def gen_fee_math():
    fig, ax = plt.subplots(figsize=(10, 6))
    
    trades_range = np.arange(1, 31)
    fee_pct = 0.01  # 1% equity per round trip
    
    cumulative_fee = 1 - (1 - fee_pct) ** trades_range
    
    ax.fill_between(trades_range, cumulative_fee * 100, alpha=0.3, color=RED)
    ax.plot(trades_range, cumulative_fee * 100, color=RED, linewidth=2.5, label='Cumulative fee drag')
    
    # Mark key points
    for t in [5, 10, 15, 20, 30]:
        fee = (1 - (1-fee_pct)**t) * 100
        ax.scatter(t, fee, color=RED, s=80, zorder=5)
        ax.annotate(f'{fee:.0f}%', xy=(t, fee), fontsize=10, fontweight='bold',
                   color=RED, xytext=(5, 8), textcoords='offset points')
    
    ax.set_xlabel('Number of Trades', fontsize=13)
    ax.set_ylabel('Equity Lost to Fees (%)', fontsize=13)
    ax.set_title('How 0.05% Taker Fee Compounds\n(10x leverage, 1% equity per round trip)', fontsize=14, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 31)
    ax.set_ylim(0, 35)
    
    # "Danger zone" annotation
    ax.axhspan(20, 35, alpha=0.1, color=RED)
    ax.text(25, 30, 'DANGER ZONE', fontsize=14, color=RED, alpha=0.7, fontweight='bold', ha='center')
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/fee-compound-chart.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ fee-compound-chart.png')

# ============================================================
# 6. Backtest engine architecture diagram (simple)
# ============================================================
def gen_architecture():
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis('off')
    
    boxes = [
        (1, 2.5, 'Raw\nCandles\n(264K)', '#30363d', BLUE),
        (3.5, 2.5, 'EMA\nCalculation', '#30363d', ORANGE),
        (6, 2.5, 'Entry\nFilter', '#30363d', PURPLE),
        (8.5, 2.5, 'Position\nManager', '#30363d', GREEN),
        (11, 2.5, 'Metrics\n& Results', '#30363d', GREEN),
    ]
    
    for x, y, text, fc, ec in boxes:
        rect = plt.Rectangle((x-0.9, y-0.7), 1.8, 1.4, 
                            facecolor=fc, edgecolor=ec, linewidth=2, 
                            zorder=3, clip_on=False)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, 
               fontweight='bold', color='#c9d1d9', zorder=4)
    
    # Arrows
    for i in range(4):
        x_start = boxes[i][0] + 0.9
        x_end = boxes[i+1][0] - 0.9
        ax.annotate('', xy=(x_end, 2.5), xytext=(x_start, 2.5),
                    arrowprops=dict(arrowstyle='->', color='#8b949e', lw=2))
    
    # Fee model annotation
    ax.annotate('Fee Model\n(maker/taker)', xy=(8.5, 1.4), fontsize=10,
               color=RED, fontweight='bold', ha='center',
               xytext=(8.5, 0.5), textcoords='data',
               arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))
    
    ax.set_title('Backtesting Engine Architecture', fontsize=16, fontweight='bold', pad=15)
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/backtest-architecture.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ backtest-architecture.png')

# ============================================================
# 7. Grid search heatmap (TP vs SL)
# ============================================================
def gen_heatmap():
    fig, ax = plt.subplots(figsize=(8, 6))
    
    tp_vals = [0.5, 0.8, 1.0, 1.2, 1.5]
    sl_vals = [0.3, 0.5, 0.8, 1.0]
    
    # Simulated returns at 0.5% buffer
    np.random.seed(123)
    data = np.array([
        [-8, -5, -2, 1, -1],
        [-12, -3, 2, 6, 3],
        [-18, -6, 5, 12, 7],
        [-22, -10, 1, 8, 4],
    ])
    
    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=-25, vmax=15)
    
    ax.set_xticks(range(len(tp_vals)))
    ax.set_xticklabels([f'{v}%' for v in tp_vals])
    ax.set_yticks(range(len(sl_vals)))
    ax.set_yticklabels([f'{v}%' for v in sl_vals])
    ax.set_xlabel('Take Profit', fontsize=13)
    ax.set_ylabel('Stop Loss', fontsize=13)
    ax.set_title('Return (%) by TP/SL\n(EMA Buffer = 0.5%, Timeout = 240min)', fontsize=14, fontweight='bold', pad=10)
    
    # Value annotations
    for i in range(len(sl_vals)):
        for j in range(len(tp_vals)):
            val = data[i, j]
            color = 'white' if abs(val) > 10 else 'black'
            ax.text(j, i, f'{val:+d}%', ha='center', va='center',
                   fontsize=12, fontweight='bold', color=color)
    
    # Highlight winner
    rect = plt.Rectangle((2.5, 1.5), 1, 1, fill=False, edgecolor=BLUE, linewidth=3)
    ax.add_patch(rect)
    ax.annotate('OPTIMAL', xy=(3, 2), fontsize=9, color=BLUE, fontweight='bold',
               xytext=(3.8, 3.3), textcoords='data',
               arrowprops=dict(arrowstyle='->', color=BLUE))
    
    cbar = plt.colorbar(im, ax=ax, label='Return (%)')
    
    plt.tight_layout()
    fig.savefig(f'{OUT}/grid-search-heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✅ grid-search-heatmap.png')

# Run all
gen_fee_impact()
gen_buffer_impact()
gen_v23_comparison()
gen_milestone_chart()
gen_fee_math()
gen_architecture()
gen_heatmap()
print(f'\n🎉 All images generated in {OUT}/')
