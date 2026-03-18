# CF Daily Picker

每日自动从 Codeforces 抓取指定难度的题目及题解，推送到 Telegram / 飞书 / 微信 / 入流。

## 功能

- **题目抓取** — 通过 Codeforces API 按难度筛选，支持单值、区间、每日随机
- **题解获取** — 优先爬取官方 Editorial，可选 LLM 兜底生成中文题解
- **LLM 增强**（可选）
  - 题面要点提取：从英文题面中提炼题意、约束、边界陷阱
  - 题解详细解析：对题解补充推导过程、举例、易错点
- **多渠道推送** — Telegram / 飞书 / 微信（Server酱）/ 入流
- **自动去重** — 已推送题目记录在 `data/sent.json`，不会重复推送
- **GitHub Actions** — 每天北京时间 20:00 自动运行，零运维

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 编辑配置

```bash
cp config.yaml config.yaml  # 直接编辑即可
```

核心配置项：

```yaml
codeforces:
  rating: 1000              # 单值、区间 [1000, 1400]、或配合 random_rating 随机
  daily_count: 2

editorial:
  official: true             # 抓取官方题解
  llm_fallback: false        # LLM 兜底（需配置 llm.api_key）

enhance:
  extract_problem_keypoints: false  # LLM 提取题面要点
  explain_editorial: false          # LLM 详细解析题解

llm:
  api_base: "https://api.openai.com/v1"  # 支持任何 OpenAI 兼容接口
  api_key: ""
  model: "gpt-4o-mini"

push:
  telegram:
    enabled: false
    bot_token: ""
    chat_id: ""
  feishu:
    enabled: false
    webhook_url: ""
  wechat:
    enabled: false
    server_chan_key: ""
  ruliu:
    enabled: false
    webhook_url: ""
```

### 3. 本地运行

```bash
python main.py
```

没有开启任何推送渠道时，消息会打印到终端。

### 4. 部署到 GitHub Actions

1. 将项目推到 GitHub
2. 在 **Settings → Secrets and variables → Actions** 中添加需要的 secrets：

   | Secret | 说明 |
   |--------|------|
   | `TG_BOT_TOKEN` | Telegram Bot Token |
   | `TG_CHAT_ID` | Telegram Chat ID |
   | `FEISHU_WEBHOOK` | 飞书机器人 Webhook URL |
   | `WECHAT_KEY` | Server酱 SendKey |
   | `RULIU_WEBHOOK` | 入流 Webhook URL |
   | `LLM_API_KEY` | LLM API Key |

3. 每天 UTC 12:00（北京时间 20:00）自动运行，也可在 Actions 页面手动触发

## 项目结构

```
cf-daily-picker/
├── main.py                      # 入口
├── config.yaml                  # 配置文件
├── requirements.txt
├── .github/workflows/daily.yml  # GitHub Actions
├── data/
│   └── sent.json                # 已推送记录（自动生成）
└── src/
    ├── codeforces.py            # CF API 题目抓取
    ├── editorial.py             # 题解获取 + LLM 增强
    ├── formatter.py             # 消息格式化
    ├── storage.py               # 持久化存储
    └── push/
        ├── telegram.py
        ├── feishu.py
        ├── wechat.py
        └── ruliu.py
```

## License

MIT
