# AgentFoundry.me 注册零思考包 — Code for a Billion 参赛第一步（2026-10-17 官方页核实）

> 目的：用户 ≤10 分钟完成 AgentFoundry 注册并建好项目，不错过 11-15 部署截止。
> 官方页：https://agentfoundry.me · 注册入口：https://agentfoundry.me/signup

## 一、官方资费口径（此前物料写「注册送 1M tokens」不够精确，以此为准）

| 档位 | 价格 | 说明 |
|---|---|---|
| **Editor + Developer mode** | **$0 永久免费** | 完整 IDE、无限项目、多模型 BYOK、agent 构建、Live Replay |
| SMART-Code Agent | **前 3 个月免费**（1,000 credits/月 ≈ 100 万 tokens/月），之后 $14.99/月 | 托管编码 agent，无需 API key；模型自动路由 Haiku 4.5（快）+ GPT-5 Codex（深） |
| Business mode | $19.99/月（7 天试用） | 非开发者用，**我们不需要** |

**结论**：参赛零成本——Editor 永久免费够用；若想用托管 agent，3 个月免费窗覆盖整个赛期（11-15 截止）。

## 二、注册三步（照做）

1. **打开 https://agentfoundry.me/signup** → 注册（官方明示 "no credit card, ever"——**任何步骤要信用卡都是走错了**）
2. **下载 Windows 版**（官方提供 Mac Apple Silicon/Intel、Windows、Linux 四版——选 Windows）
3. **首次启动的凭证扫描**：官方会扫描本机已有工具（VS Code、Cursor、Claude Code、Codex CLI、Gemini、Aider、gh CLI、git 配置、环境变量）的凭证和配置，**一键导入 AI keys / GitHub auth / git identity**
   - ⚠️ 官方明示 **"Nothing imports without your click"**——不点确认就不会导入任何东西；想让 git 身份和 GitHub auth 自动配好就点，不想就跳过（跳过也能用，仓已公开）

## 三、注册后参赛动作（Code for a Billion）

1. **建项目**：导入本仓 `github.com/Zhiyilang/clauseguard-justice`（Track 07「Timely Justice — Legal Backlog」参赛仓，MIT，36 断言，CI 绿）
2. **跑通**：本地 `python eval.py` → 36/36（零依赖，Python 3.8+）
3. **部署**：Render Blueprint（`render.yaml` 已在仓）→ 公网 URL——**CFB 评分 25% 是「已证实的部署影响」，必须真部署**
4. **提交**（11-15 前）：官方 GitHub issue 表单（模板在 `karlmehta/code-for-a-billion` 仓 submission.yml）+ 公开仓链接 + 2-3min demo 视频（`clauseguard_demo.mp4` 30s 已在仓，可复用/扩写）
5. **赛道确认**：已在官方 Discussions 发过确认问题模板（文案在 `clauseguard-justice/CODE_FOR_A_BILLION.md` 末节，英文可直接发）

## 四、时间线（别卡点）

| 节点 | 时间 |
|---|---|
| 现在 → 11-10 | 注册 + 建项目 + 本地跑通（零 GPU，10 分钟） |
| 11-10 前 | Render 部署拿到公网 URL（评分刚需） |
| **11-15** | **部署 + 开源 + issue 表单提交截止** |
| 12-05 | 结果公布（每赛道 1st ₹1.5L ≈ ¥12.7k / 2nd ₹1L / 3rd ₹0.5L） |

## 五、联系兜底

AgentFoundry 团队联系邮箱（官方页提供）：karl@codenow.pro；wiki 发布说明：wiki.agentfoundry.me/release-notes。注册或提交遇阻（非技术问题）可邮件。
