"""
Offline fallback risk engine (zero-dependency, stdlib only).

Used ONLY when the InfiniSynapse API is unavailable (e.g. account not yet
activated, or network issue). The PRIMARY analysis path is InfiniSynapse;
this is a resilient local demo so the app is always runnable. It is a simple
transparent rule scan, NOT a substitute for the agent.

Bilingual: every rule carries zh + en strings. `scan(text, lang="zh")`
returns findings in the requested language. Default stays Chinese so the
InfiniSynapse-hackathon behaviour is unchanged; `lang="en"` powers the
Dubai Create AI Agents Championship entry (English-only requirement).
"""

import re

# Each rule: (patterns, severity, {"zh": (label, explanation, suggestion),
#                                   "en": (label, explanation, suggestion)})
RULES = [
    ([r"自动续", r"auto[\s-]?renew", r"automatic(ally)?[\s-]?renew", r"renewed", r"renewal", r"自动顺延", r"到期自动"], "HIGH",
     {"zh": ("自动续约 / Auto-renewal",
             "合同可能在期满后自动续约，你可能在不知情的情况下被锁定续费/续约。",
             "要求改为「需双方书面确认后方可续约」，或设定明确的终止通知期。"),
      "en": ("Auto-renewal",
             "The contract may renew automatically after expiry, locking you into another term without your knowledge.",
             "Require renewal only after written confirmation by both parties, or set a clear notice period for termination.")}),
    ([r"单方", r"有权(随时|自行)?修改", r"保留(最终|单方).{0,6}解释", r"without notice"], "HIGH",
     {"zh": ("单方修改条款 / Unilateral change",
             "对方可在不通知你的情况下单方面修改合同核心条款。",
             "删除单方修改权，任何变更须经双方书面同意。"),
      "en": ("Unilateral change of terms",
             "The other party can change core terms without notifying you.",
             "Remove the unilateral-change right; any amendment needs written consent from both parties.")}),
    ([r"责任.*(不超过|限于)", r"不(承担|负).{0,6}责任", r"limi(t|tation).{0,20}liab", r"概不负责"], "MEDIUM",
     {"zh": ("责任限制 / Liability cap",
             "对方试图把自身赔偿责任压到极低甚至归零。",
             "设定合理赔偿下限，排除故意或重大过失的免责。"),
      "en": ("Liability cap",
             "The other party is trying to push its liability down to near zero.",
             "Set a reasonable liability floor and exclude wilful misconduct or gross negligence from any exemption.")}),
    ([r"赔偿.{0,6}(全部|任何|所有)", r"indemn", r"使你免受", r"承担一切损失"], "HIGH",
     {"zh": ("宽泛赔偿 / Broad indemnity",
             "你可能需要为范围极广的损失买单，包括与己无关的部分。",
             "把赔偿范围限定在「因你违约直接造成的可预见损失」。"),
      "en": ("Broad indemnity",
             "You may have to cover an extremely wide range of losses, including parts unrelated to you.",
             "Limit indemnity to foreseeable losses directly caused by your breach.")}),
    ([r"仲裁.*(对方所在地|海外|异地)", r"管辖.*(被告|甲方)所在地", r"适用.{0,6}法律.*(外|offshore)"], "MEDIUM",
     {"zh": ("仲裁 / 管辖地偏向对方",
             "争议解决地被设在对方主场，你维权成本极高。",
             "争取约定中立地或你所在地法院/仲裁。"),
      "en": ("Dispute resolution tilted to the other party",
             "Disputes are resolved on the other party's home turf, making your remedy extremely costly.",
             "Negotiate a neutral venue, or a court/arbitration seat in your own jurisdiction.")}),
    ([r"提前终止.{0,6}(罚金|违约金|费用)", r"cancel.{0,10}fee", r"剩余费用.{0,6}照付"], "MEDIUM",
     {"zh": ("提前终止罚金 / Early-termination penalty",
             "你提前退出可能被要求付清全部剩余费用。",
             "违约金应与实际损失挂钩，并设置递减机制。"),
      "en": ("Early-termination penalty",
             "Leaving early may require you to pay all remaining fees.",
             "Tie penalties to actual losses and add a declining scale.")}),
    ([r"知识产权.{0,6}(归|属).{0,6}(甲方|对方)", r"所有成果.{0,6}归", r"assign.{0,10}ip"], "MEDIUM",
     {"zh": ("IP 归属 / IP assignment",
             "你产出的成果/创意可能被无偿收归对方所有。",
             "明确你保留背景知识产权，仅授予必要的使用许可。"),
      "en": ("IP assignment",
             "Everything you produce may be transferred to the other party for free.",
             "Keep your background IP and grant only the licence strictly needed.")}),
    ([r"竞业", r"不得从事", r"non[\s-]?compete", r"限制.{0,6}经营"], "LOW",
     {"zh": ("竞业限制 / Non-compete",
             "可能限制你未来的就业或创业自由。",
             "限定竞业范围、期限与补偿，超范围条款应删除。"),
      "en": ("Non-compete",
             "This may restrict your future employment or entrepreneurship.",
             "Limit scope, duration and compensation; delete anything beyond that.")}),
    ([r"个人(承担|担保|连带)", r"personal guarantee", r"以个人资产"], "HIGH",
     {"zh": ("个人担保 / Personal guarantee",
             "你可能以个人财产为公司/合同债务承担连带责任。",
             "拒绝个人担保，责任主体应为签约实体。"),
      "en": ("Personal guarantee",
             "You may be personally liable for company/contract debts with your own assets.",
             "Refuse personal guarantees; the signing entity should carry the liability.")}),
    ([r"不予退款", r"概不退款", r"no refund", r"恕不退还"], "LOW",
     {"zh": ("不退款 / No refund",
             "付款后无论服务如何都难以退款。",
             "约定明确的退款条件与服务质量不达标时的退费机制。"),
      "en": ("No refund",
             "Once paid, getting money back is hard no matter the service quality.",
             "Agree explicit refund conditions and a remedy when service falls short.")}),
]

_NOTES = {
    "zh": "本地离线规则扫描（演示兜底），正式分析由 InfiniSynapse 智能体完成。",
    "en": "Local offline rule scan (demo fallback). Full analysis is done by the InfiniSynapse agent.",
}
_SEV_WEIGHT = {"HIGH": 25, "MEDIUM": 12, "LOW": 5}


def scan(text, lang="zh"):
    """Scan contract text and return bilingual-safe findings (default zh)."""
    if lang not in ("zh", "en"):
        lang = "zh"
    text_lower = text.lower()
    findings = []
    for patterns, severity, strings in RULES:
        hit = False
        for p in patterns:
            if re.search(p, text, re.IGNORECASE) or re.search(p, text_lower):
                hit = True
                break
        if hit:
            label, explain, suggest = strings[lang]
            findings.append({
                "label": label, "severity": severity,
                "explanation": explain, "suggestion": suggest,
            })
    score = 0
    for f in findings:
        score += _SEV_WEIGHT[f["severity"]]
    score = min(score, 100)
    band = "HIGH" if score >= 40 else ("MEDIUM" if score >= 15 else "LOW")
    return {
        "findings": findings,
        "score": score,
        "band": band,
        "lang": lang,
        "note": _NOTES[lang],
    }
