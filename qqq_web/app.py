import os
import platform
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import streamlit as st
import plotly.graph_objects as go


def get_font_properties():
    """
    尽量在不同系统上找到中文字体，避免中文标题变成口口口
    """
    system_name = platform.system()

    # macOS 常见字体
    mac_candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]

    # Windows 常见中文字体
    win_candidates = [
        r"C:\\Windows\\Fonts\\simhei.ttf",
        r"C:\\Windows\\Fonts\\msyh.ttc",
    ]

    # Linux 常见（云部署常用）
    linux_candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/arphic/ukai.ttc",
    ]

    candidates = []
    if system_name == "Darwin":
        candidates = mac_candidates
    elif system_name == "Windows":
        candidates = win_candidates
    else:
        candidates = linux_candidates + mac_candidates  # Linux 找不到就顺便试试其它

    for p in candidates:
        if os.path.exists(p):
            return FontProperties(fname=p)

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_close_price(ticker: str) -> pd.Series:
    """
    拉取复权数据 auto_adjust=True，并返回 close 序列
    """
    data = yf.download(
        ticker,
        start="2010-01-01",
        progress=False,
        auto_adjust=True
    )
    if data is None or data.empty:
        raise RuntimeError("未能获取到数据，请检查网络或 ticker 是否正确。")

    # 兼容 MultiIndex 列
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"][ticker]
    else:
        close = data["Close"]

    close = close.dropna()
    if close.empty:
        raise RuntimeError("Close 数据为空。")

    return close


def compute_deviation_percentile(close: pd.Series, ma_window=200, rolling_window=1260):
    """
    计算 MA200、偏离度、以及 5年滚动历史分位（0-100）
    """
    ma200 = close.rolling(window=ma_window).mean()
    deviation = (close - ma200) / ma200
    pct = deviation.rolling(window=rolling_window).rank(pct=True) * 100
    return ma200, deviation, pct


def make_chart(ticker: str, close: pd.Series, ma200: pd.Series, pct: pd.Series, plot_start_date: str):
    """
    生成 matplotlib Figure，不落盘
    """
    subset = pct.loc[plot_start_date:].dropna()
    if subset.empty:
        raise RuntimeError("图表区间没有有效数据（可能起始日期太晚或滚动窗口尚未形成）。")

    font_prop = get_font_properties()
    font_name = font_prop.get_name() if font_prop else "sans-serif"
    plt.rcParams["font.sans-serif"] = [font_name]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)

    ax.plot(
        subset.index,
        subset,
        linewidth=1.5,
        label=f"{ticker} 偏离度历史分位 (5Y Rolling Percentile)"
    )

    ax.axhline(y=80, linestyle="-", linewidth=2, label="80 高危警戒线")
    ax.axhline(y=50, linestyle=":", linewidth=1, alpha=0.5)
    ax.axhline(y=20, linestyle="--", linewidth=1, alpha=0.5, label="20 底部机会区")

    ax.fill_between(subset.index, 80, 100, where=(subset >= 80), alpha=0.2, interpolate=True)
    ax.fill_between(subset.index, 0, 20, where=(subset <= 20), alpha=0.1, interpolate=True)

    last_date = subset.index[-1]
    last_val = float(subset.iloc[-1])
    last_price = float(close.iloc[-1])
    last_ma = float(ma200.iloc[-1])

    title_text = f"{ticker} 价格 vs 200天均线偏离度指数（复权口径 auto_adjust=True）"
    date_str = last_date.strftime("%Y-%m-%d")
    subtitle_text = (
        f"最新日期: {date_str} | 调整后收盘价: ${last_price:.2f} | "
        f"200天均线: ${last_ma:.2f} | 当前指标读数: {last_val:.1f}"
    )

    # 合并为一行标题，避免重复/双行显示
    combined_title = f"{title_text}  |  {subtitle_text}"
    ax.set_title(combined_title, fontsize=14, fontweight="bold", pad=14, fontproperties=font_prop)

    ax.set_ylabel("历史百分位 (0-100)", fontsize=12, fontproperties=font_prop)
    ax.set_ylim(-5, 105)
    ax.grid(True, which="major", linestyle="--", alpha=0.5)

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.legend()
    fig.tight_layout()
    return fig, last_val, date_str, last_price, last_ma


def make_plotly_chart(ticker: str, close: pd.Series, ma200: pd.Series, pct: pd.Series, plot_start_date: str):
    """
    生成可交互的 Plotly Figure，默认支持拖动/缩放 x 轴和 range slider
    """
    subset = pct.loc[plot_start_date:].dropna()
    if subset.empty:
        raise RuntimeError("图表区间没有有效数据（可能起始日期太晚或滚动窗口尚未形成）。")

    font_prop = get_font_properties()
    font_family = font_prop.get_name() if font_prop else None

    x = subset.index
    y = subset.values

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name=f"{ticker} 偏离度历史分位 (5Y Rolling Percentile)",
        line=dict(width=2)
    ))

    # Horizontal lines
    fig.add_hline(y=80, line=dict(color="red", width=2), annotation_text="80 高危警戒线", annotation_position="top left")
    fig.add_hline(y=50, line=dict(color="gray", width=1, dash="dot"))
    fig.add_hline(y=20, line=dict(color="green", width=1, dash="dash"), annotation_text="20 底部机会区", annotation_position="bottom left")

    # Shaded regions
    fig.add_shape(type="rect", xref="paper", x0=0, x1=1, yref="y", y0=80, y1=100, fillcolor="rgba(255,0,0,0.15)", line_width=0)
    fig.add_shape(type="rect", xref="paper", x0=0, x1=1, yref="y", y0=0, y1=20, fillcolor="rgba(0,128,0,0.08)", line_width=0)

    last_date = subset.index[-1]
    last_val = float(subset.iloc[-1])
    last_price = float(close.iloc[-1])
    last_ma = float(ma200.iloc[-1])

    date_str = last_date.strftime("%Y-%m-%d")

    title_text = f"{ticker} 价格 vs 200天均线偏离度指数（复权口径 auto_adjust=True）"
    subtitle_text = (
        f"最新日期: {date_str} | 调整后收盘价: ${last_price:.2f} | "
        f"200天均线: ${last_ma:.2f} | 当前指标读数: {last_val:.1f}"
    )

    # 合并为一行标题，避免重复/双行显示
    combined_title = f"{title_text}  |  {subtitle_text}"

    fig.update_layout(
        title={"text": combined_title, "x": 0.5},
        xaxis=dict(rangeslider=dict(visible=True), type="date", rangeselector=dict(buttons=[dict(count=1, label="1y", step="year", stepmode="backward"), dict(count=3, label="3y", step="year", stepmode="backward"), dict(step="all")])),
        yaxis=dict(range=[-5, 105], title="历史百分位 (0-100)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
    )

    if font_family:
        fig.update_layout(font=dict(family=font_family))

    return fig, last_val, date_str, last_price, last_ma


def status_from_value(v: float):
    if v > 80:
        return "偏热", "⚠️ 警告：偏离偏热（相对近5年偏高）", "error"
    if v < 20:
        return "偏冷", "💎 机会：偏离偏冷（相对近5年偏低）", "success"
    return "中性", "⚖️ 中性：趋势正常，价格贴近长期均线", "info"


def main():
    st.set_page_config(page_title="偏离度分析工具", layout="wide")
    st.title("趋势偏离度分析工具（网页版）")

    with st.sidebar:
        st.header("参数")
        ticker = st.text_input("Ticker", value="QQQ").strip().upper()
        plot_start_date = st.text_input("图表起始日期 (YYYY-MM-DD)", value="2018-01-01").strip()
        interactive = st.checkbox("交互式图表（可拖动/缩放 X 轴）", value=True)
        st.caption("说明：使用 yfinance 获取复权数据（auto_adjust=True），MA200 + 5年滚动分位。")
        run_btn = st.button("更新/刷新", type="primary")

    if run_btn:
        try:
            with st.spinner("正在拉取数据并计算..."):
                close = fetch_close_price(ticker)
                ma200, deviation, pct = compute_deviation_percentile(close)
                if interactive:
                    fig, last_val, date_str, last_price, last_ma = make_plotly_chart(
                        ticker=ticker,
                        close=close,
                        ma200=ma200,
                        pct=pct,
                        plot_start_date=plot_start_date,
                    )
                else:
                    fig, last_val, date_str, last_price, last_ma = make_chart(
                        ticker=ticker,
                        close=close,
                        ma200=ma200,
                        pct=pct,
                        plot_start_date=plot_start_date,
                    )

            if interactive:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.pyplot(fig, clear_figure=True)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("最新日期", date_str)
            col2.metric("调整后收盘价", f"${last_price:.2f}")
            col3.metric("MA200", f"${last_ma:.2f}")
            col4.metric("指标读数", f"{last_val:.1f}")

            label, msg, level = status_from_value(last_val)
            if level == "error":
                st.error(msg)
            elif level == "success":
                st.success(msg)
            else:
                st.info(msg)

            # 可选：展示最近几行数据
            with st.expander("查看最近数据（Close / MA200 / Percentile）"):
                df = pd.DataFrame({
                    "Close": close,
                    "MA200": ma200,
                    "Percentile": pct
                }).dropna().tail(20)
                st.dataframe(df)
        except Exception as exc:
            st.error(f"运行失败：{exc}")
    else:
        st.info("在左侧设置参数，然后点击「更新/刷新」。")


if __name__ == "__main__":
    main()
