# QQQ 200-Day Moving Average Deviation Analyzer

Interactive Streamlit application for analyzing QQQ's deviation from its 200-day moving average with 5-year historical percentile ranking.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)

## Features

- **Real-time Deviation Analysis**: Track QQQ price vs 200-day SMA
- **Historical Percentile**: 5-year percentile ranking for context
- **Interactive Charts**: Plotly-powered zoom and pan
- **Multiple Tickers**: Support for QQQ, AAPL, and more

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r qqq_web/requirements.txt

# Run the app
streamlit run qqq_web/app.py
```

## Project Structure

```
qqq-streamlit/
├── qqq_web/
│   ├── app.py              # Main Streamlit application
│   └── requirements.txt    # Dependencies
├── interactive_plot.py     # Plotting utilities
├── QQQ_interactive.html    # Pre-generated QQQ chart
└── AAPL_interactive.html   # Pre-generated AAPL chart
```

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" → Select your repo → Set file path to `qqq_web/app.py`
4. Deploy and share the URL

## License

MIT

---

# 中文说明

基于 Streamlit 的交互式应用，用于分析标的相对于 200 日均线的偏离度及其近 5 年历史分位。

## 本地运行

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r qqq_web/requirements.txt

# 运行应用
streamlit run qqq_web/app.py --server.port 666
```

## 部署到 Streamlit Cloud

1. 将仓库推送到 GitHub
2. 打开 [share.streamlit.io](https://share.streamlit.io)
3. 选择仓库 → 文件路径填写 `qqq_web/app.py`
4. 部署完成后分享 URL
