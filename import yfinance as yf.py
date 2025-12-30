import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import platform
import os

def get_font_properties():
    """
    智能检测系统中可用的中文字体文件
    """
    font_candidates = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf',
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc'
    ]

    system_name = platform.system()
    if system_name == "Darwin":  # macOS
        for font_path in font_candidates:
            if os.path.exists(font_path):
                print(f"✅ 已加载字体: {font_path}")
                return FontProperties(fname=font_path)

    elif system_name == "Windows":  # Windows
        # Windows 常见中文字体（SimHei）
        font_path = 'C:\\Windows\\Fonts\\simhei.ttf'
        if os.path.exists(font_path):
            return FontProperties(fname=font_path)

    # 如果都找不到，返回默认
    return None

def fetch_and_plot():
    print("------------------------------------------------")
    print("🚀 正在启动 QQQ 趋势偏离度分析工具...")
    print("📡 正在连接 Yahoo Finance 获取最新数据 (使用 auto_adjust=True 复权数据)...")

    ticker = "QQQ"

    # 1) 获取数据（关键：auto_adjust=True）
    # auto_adjust=True 会把 OHLC 都按拆分/分红等进行调整，口径更一致
    try:
        data = yf.download(
            ticker,
            start="2010-01-01",
            progress=False,
            auto_adjust=True
        )
        if data.empty:
            print("❌ 错误：未能获取到数据，请检查网络连接。")
            return
    except Exception as e:
        print(f"❌ 错误：{e}")
        return

    print(f"✅ 成功获取数据，共 {len(data)} 个交易日。")
    print("⚙️ 正在计算 200天均线 及 5年滚动历史分位值...")

    # 2) 取收盘价（此处的 Close 已经是“复权后的 Close”）
    # 注意：yfinance 可能返回 MultiIndex 列（某些情况下）
    if isinstance(data.columns, pd.MultiIndex):
        close_price = data['Close'][ticker]
    else:
        close_price = data['Close']

    # 3) 计算核心指标
    ma200 = close_price.rolling(window=200).mean()
    deviation = (close_price - ma200) / ma200

    # 过去约 5 年（1260 交易日）滚动窗口里的百分位
    rolling_window = 1260
    deviation_index = deviation.rolling(window=rolling_window).rank(pct=True) * 100

    # ✅ 在这里验证（打印）
    print("Yahoo最后5行价格：")
    print(close_price.tail())
    print("最后一天 MA200：", ma200.iloc[-1])
    print("最后一天 指数：", deviation_index.iloc[-1])


    # 绘图区间
    plot_start_date = "2018-01-01"
    subset_index = deviation_index.loc[plot_start_date:]

    # 4) 绘图
    print("🎨 正在绘制图表...")

    font_prop = get_font_properties()
    font_name = font_prop.get_name() if font_prop else "sans-serif"
    plt.rcParams['font.sans-serif'] = [font_name]
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)

    ax.plot(
        subset_index.index,
        subset_index,
        color='#2c5d80',
        linewidth=1.5,
        label='QQQ 偏离度历史分位 (5Y Rolling Percentile)'
    )

    # 警戒线/参考线
    ax.axhline(y=80, color='#e74c3c', linestyle='-', linewidth=2, label='80 高危警戒线')
    ax.axhline(y=50, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(y=20, color='green', linestyle='--', linewidth=1, alpha=0.5, label='20 底部机会区')

    # 填充区域
    ax.fill_between(
        subset_index.index, 80, 100,
        where=(subset_index >= 80),
        color='#e74c3c', alpha=0.2, interpolate=True
    )
    ax.fill_between(
        subset_index.index, 0, 20,
        where=(subset_index <= 20),
        color='green', alpha=0.1, interpolate=True
    )

    # 最新值
    last_date = subset_index.index[-1]
    last_val = subset_index.iloc[-1]
    last_price = close_price.iloc[-1]      # 复权收盘价（auto_adjust=True）
    last_ma = ma200.iloc[-1]               # 复权口径的MA200

    # 标题与副标题（强调复权口径）
    title_text = "QQQ 价格 vs 200天均线偏离度指数（复权口径 auto_adjust=True）"
    date_str = last_date.strftime('%Y-%m-%d')
    subtitle_text = (
        f"最新日期: {date_str} | 调整后收盘价: ${last_price:.2f} | "
        f"200天均线: ${last_ma:.2f} | 当前指标读数: {last_val:.1f}"
    )

    plt.title(title_text, fontsize=16, fontweight='bold', fontproperties=font_prop, pad=20)
    plt.figtext(0.5, 0.89, subtitle_text, ha="center", fontsize=10, color="#555555", fontproperties=font_prop)

    # 坐标轴/网格
    ax.set_ylabel('历史百分位 (0-100)', fontsize=12, fontproperties=font_prop)
    ax.set_ylim(-5, 105)
    ax.grid(True, which='major', linestyle='--', alpha=0.5)

    # 动态注解
    if last_val > 80:
        status_color = '#e74c3c'
        status_text = "⚠️ 警告：偏离偏热\n（相对近5年偏高）"
    elif last_val < 20:
        status_color = 'green'
        status_text = "💎 机会：偏离偏冷\n（相对近5年偏低）"
    else:
        status_color = '#2980b9'
        status_text = "⚖️ 中性：趋势正常\n价格贴近长期均线"

    ax.plot(last_date, last_val, marker='o', color=status_color, markersize=8)
    ax.annotate(
        f'{last_val:.1f}\n{status_text}',
        xy=(last_date, last_val),
        xytext=(last_date - pd.Timedelta(days=400), last_val + 10 if last_val < 50 else last_val - 20),
        arrowprops=dict(facecolor=status_color, arrowstyle="->", connectionstyle="arc3,rad=.2"),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=status_color, alpha=0.9),
        fontsize=11,
        fontproperties=font_prop,
        color=status_color
    )

    # X轴日期格式
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    plt.tight_layout()

    # 保存图片
    output_filename = 'qqq_deviation_chart_auto_adjust.png'
    plt.savefig(output_filename)
    print(f"✅ 图表已生成并保存为: {output_filename}")

    # 尝试自动打开图片
    try:
        if platform.system() == "Darwin":
            os.system(f"open {output_filename}")
        elif platform.system() == "Windows":
            os.startfile(output_filename)
    except:
        pass


if __name__ == "__main__":
    fetch_and_plot()

