# CF Daily Picker

每日自动从 Codeforces 抓取指定难度的题目及题解，翻译为中文，生成带 LaTeX 公式渲染的 HTML 题解，推送到 Telegram / 飞书 / 微信。

## 功能

- **题目抓取** — 通过 Codeforces API 按难度筛选，支持单值、区间、每日随机
- **题解获取** — 优先爬取官方 Editorial，可选 LLM 兜底生成中文题解
- **中文翻译** — 自动将英文题解翻译为中文，保留 LaTeX 公式原文
- **LLM 增强**（可选）
  - 题面要点提取：从英文题面中提炼题意、约束、边界陷阱
  - 题解详细解析：对题解补充推导过程、举例、易错点
- **HTML 导出** — 生成带 KaTeX 渲染的 HTML 文件，数学公式完美显示
- **多渠道推送** — Telegram（文字摘要 + HTML 附件）/ 飞书 / 微信（Server酱）
- **自动去重** — 已推送题目记录在 `data/sent.json`，不会重复推送
- **GitHub Actions** — 每天北京时间 20:00 自动运行，零运维

## 推送效果

Telegram 会收到两条消息：

1. **文字摘要** — 题目名称、难度、链接，一眼可见
2. **HTML 附件** — 点开在浏览器中查看完整题解，LaTeX 公式由 KaTeX 渲染

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 编辑配置

核心配置项（`config.yaml`）：

```yaml
codeforces:
  rating: 1000              # 单值、区间 [1000, 1400]、或配合 random_rating 随机
  daily_count: 2

editorial:
  official: true             # 抓取官方题解
  llm_fallback: false        # LLM 兜底生成题解（需配置 llm.api_key）

enhance:
  extract_problem_keypoints: true   # LLM 提取题面要点
  explain_editorial: true           # LLM 详细解析题解

llm:
  api_base: "https://api.deepseek.com/v1"  # 支持任何 OpenAI 兼容接口
  api_key: ""                               # 通过环境变量 LLM_API_KEY 注入
  model: "deepseek-chat"

push:
  telegram:
    enabled: true
    bot_token: ""            # 通过环境变量 TG_BOT_TOKEN 注入
    chat_id: ""              # 通过环境变量 TG_CHAT_ID 注入
  feishu:
    enabled: false
    webhook_url: ""
  wechat:
    enabled: false
    server_chan_key: ""
```

支持的 LLM 提供商（任何 OpenAI 兼容接口）：

| 提供商 | api_base | model |
|--------|----------|-------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Moonshot (Kimi) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱 (GLM) | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |

### 3. 本地运行

```bash
export LLM_API_KEY="your-api-key"
python main.py
```

没有开启推送渠道时，文字摘要打印到终端，HTML 文件保存到 `output/` 目录，可直接在浏览器打开预览。

### 4. 部署到 GitHub Actions

1. 将项目推到 GitHub
2. 在 **Settings → Secrets and variables → Actions** 中添加：

   | Secret | 说明 |
   |--------|------|
   | `TG_BOT_TOKEN` | Telegram Bot Token |
   | `TG_CHAT_ID` | Telegram Chat ID |
   | `FEISHU_WEBHOOK` | 飞书机器人 Webhook URL |
   | `WECHAT_KEY` | Server酱 SendKey |
   | `LLM_API_KEY` | LLM API Key |

3. 每天 UTC 12:00（北京时间 20:00）自动运行，也可在 Actions 页面手动触发

## 项目结构

```
cf-daily-picker/
├── main.py                      # 入口
├── config.yaml                  # 配置文件
├── requirements.txt
├── .github/workflows/daily.yml  # GitHub Actions
├── templates/
│   └── daily.html               # HTML 模版（KaTeX + 样式）
├── data/
│   └── sent.json                # 已推送记录（自动生成）
├── output/                      # 本地测试时 HTML 输出目录
└── src/
    ├── codeforces.py            # CF API 题目抓取
    ├── editorial.py             # 题解获取 + 翻译 + LLM 增强
    ├── formatter.py             # 消息格式化（摘要/Markdown）
    ├── renderer.py              # HTML 渲染（KaTeX 公式支持）
    ├── storage.py               # 持久化存储
    └── push/
        ├── telegram.py          # 文字摘要 + HTML 文件
        ├── feishu.py
        └── wechat.py
```

## License

MIT
