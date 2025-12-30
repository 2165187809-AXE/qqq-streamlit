# QQQ / 偏离度分析工具

这是一个基于 Streamlit 的交互式应用，用于展示标的相对于 200 日均线的偏离度及其近 5 年历史分位（支持 Plotly 交互缩放）。

目录结构（相关）：

- `qqq_web/app.py` - Streamlit 应用主文件
- `qqq_web/requirements.txt` - 应用依赖

快速开始（本地）

1. 创建并激活虚拟环境：
```bash
python3 -m venv .venv
source .venv/bin/activate
```
2. 安装依赖：
```bash
pip install --upgrade pip
pip install -r qqq_web/requirements.txt
```
3. 运行应用：
```bash
streamlit run qqq_web/app.py --server.port 666 --server.address 0.0.0.0
```

使朋友访问（推荐方式）

- 最简单：将仓库推送到 GitHub，然后使用 Streamlit Community Cloud（https://share.streamlit.io）部署。Streamlit Cloud 会直接从你的 GitHub 仓库拉取代码并运行。下面有详细步骤。

在 GitHub + Streamlit Cloud 上部署（推荐）

1. 在本地初始化 git（如果尚未）：
```bash
git init
git add .
git commit -m "Initial commit"
```
2. 在 GitHub 上创建一个新仓库（比如 `qqq-streamlit`），然后把远程仓库添加到本地并 push：
```bash
git remote add origin git@github.com:你的用户名/qqq-streamlit.git
git branch -M main
git push -u origin main
```
3. 打开 https://share.streamlit.io，登录并点击 "New app" → 选择你的 GitHub 仓库 → branch 选择 `main` → 在 `File` 填写 `qqq_web/app.py` → Deploy。

Streamlit Cloud 会自动安装 `qqq_web/requirements.txt` 中的依赖并运行你的应用。部署成功后会给出一个可公开访问的 URL，把该 URL 发给朋友即可。

替代：直接暴露本地（不推荐生产）

- 使用 `ngrok`：
```bash
ngrok http 666
```
`ngrok` 会给出一个公网地址，临时分享给朋友即可。


