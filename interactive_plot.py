import argparse
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def fetch_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        raise RuntimeError(f"无法获取 {ticker} 的数据 (period={period}, interval={interval})")
    return df


def make_interactive_chart(df: pd.DataFrame, ticker: str, interval: str = "1d") -> go.Figure:
    # 清理 index：去掉 tzinfo（如有），并在日线数据时只保留日期（方便显示）
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        try:
            df.index = df.index.tz_convert(None)
        except Exception:
            try:
                df.index = df.index.tz_localize(None)
            except Exception:
                pass

    if interval.endswith('d'):
        df.index = pd.to_datetime(df.index).normalize()

    close = df["Close"].copy()

    # 计算 MA200 与偏离度百分位（与原脚本保持一致）
    ma200 = close.rolling(window=200).mean()
    deviation = (close - ma200) / ma200
    rolling_window = 1260
    deviation_index = deviation.rolling(window=rolling_window).rank(pct=True) * 100

    # 构建带两个子图（上：偏离度，下：价格 + MA）
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.45, 0.55], subplot_titles=("偏离度历史分位 (5Y Rolling Percentile)", "价格 (复权) & MA200"))

    # 上图：偏离度百分位
    deviation_plot = deviation_index.dropna()
    fig.add_trace(
        go.Scatter(x=deviation_plot.index, y=deviation_plot, mode='lines', name='偏离度百分位', line=dict(color='#2c5d80')),
        row=1, col=1
    )

    # 在上方添加固定的高/低位背景带（可视化提示）
    fig.add_shape(type="rect", xref="paper", x0=0, x1=1, yref="y", y0=80, y1=100,
                  fillcolor="#e74c3c", opacity=0.08, layer="below", row=1, col=1)
    fig.add_shape(type="rect", xref="paper", x0=0, x1=1, yref="y", y0=0, y1=20,
                  fillcolor="green", opacity=0.06, layer="below", row=1, col=1)

    # 参考线
    fig.add_hline(y=80, line=dict(color='#e74c3c', width=1.5), row=1, col=1, annotation_text='80', annotation_position='top left')
    fig.add_hline(y=50, line=dict(color='gray', width=1, dash='dot'), row=1, col=1)
    fig.add_hline(y=20, line=dict(color='green', width=1, dash='dash'), row=1, col=1, annotation_text='20', annotation_position='bottom left')

    # 下图：价格与 MA200（仅绘制有值的区域，避免 NaN 导致显示异常）
    close_plot = close.dropna()
    ma200_plot = ma200.dropna()
    fig.add_trace(
        go.Scatter(x=close_plot.index, y=close_plot, mode='lines', name=f'{ticker} Close', line=dict(color='#1f77b4')),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=ma200_plot.index, y=ma200_plot, mode='lines', name='MA200', line=dict(color='#ff7f0e', dash='dash')),
        row=2, col=1
    )

    # 布局与交互控件（快捷选择、rangeslider）
    fig.update_layout(
        title=f"{ticker} — 交互式图表（支持 zoom / pan / rangeslider / rangeselector）",
        hovermode='x unified',
        template='plotly_white',
        margin=dict(l=40, r=20, t=80, b=40),
    )

    # x 轴控件放在底部 xaxis（共享）
    fig.update_xaxes(
        dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label='1w', step='day', stepmode='backward'),
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=3, label='3m', step='month', stepmode='backward'),
                    dict(count=1, label='1y', step='year', stepmode='backward'),
                    dict(step='all', label='全部')
                ])
            ),
            rangeslider=dict(visible=True),
            type='date',
        )
    )

    # 对日线数据使用更友好的刻度格式（避免出现毫秒/秒级标签）
    fig.update_xaxes(matches=None, tickformat='%Y-%m-%d', row=1, col=1)
    fig.update_xaxes(tickformat='%Y-%m-%d', row=2, col=1)

    # 上图 y 轴固定到 0-100（更接近原脚本视觉）
    fig.update_yaxes(range=[-5, 105], row=1, col=1, title_text='历史百分位 (0-100)')

    # 底图自动调整但保持网格
    fig.update_yaxes(row=2, col=1, title_text='价格 (复权)')

    # 标注最新值到上图（如果有可用值）
    if not deviation_plot.empty:
        last_date = deviation_plot.index[-1]
        last_val = deviation_plot.iloc[-1]
        fig.add_trace(go.Scatter(x=[last_date], y=[last_val], mode='markers', marker=dict(color='#e74c3c' if last_val>80 else ('green' if last_val<20 else '#2980b9'), size=8), name='最新值'), row=1, col=1)
        status_text = '中性：趋势正常' if 20<=last_val<=80 else ('警告：偏热' if last_val>80 else '机会：偏冷')
        fig.add_annotation(x=last_date, y=last_val, text=f"{last_val:.1f} {status_text}", showarrow=True, arrowhead=2, ax=-100, ay=-40, bgcolor='white')

    return fig


def main():
    parser = argparse.ArgumentParser(description="交互式股票价格图 (使用 yfinance + Plotly)")
    parser.add_argument("--ticker", "-t", default="AAPL", help="股票代码，默认 AAPL")
    parser.add_argument("--period", "-p", default="1y", help="数据周期，例如: 1mo,3mo,6mo,1y,2y,5y,max")
    parser.add_argument(
        "--interval",
        "-i",
        default="1d",
        help="数据粒度，例如: 1m,2m,5m,15m,60m,90m,1d (注意：某些 interval 受 period 限制)",
    )

    args = parser.parse_args()

    ticker = args.ticker
    period = args.period
    interval = args.interval

    print(f"📡 正在获取 {ticker} 的数据 (period={period}, interval={interval}) ...")
    try:
        df = fetch_data(ticker, period=period, interval=interval)
    except Exception as e:
        print("❌ 数据获取失败：", e)
        return

    print(f"✅ 获取到 {len(df)} 条数据，开始绘制交互图表...")
    fig = make_interactive_chart(df, ticker)

    out_file = f"{ticker}_interactive.html"
    fig.write_html(out_file, include_plotlyjs='cdn')
    print(f"✅ 交互式图表已保存为: {out_file}")

    try:
        fig.show()
    except Exception:
        pass


if __name__ == "__main__":
    main()
