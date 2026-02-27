"""
LLM integration for water transfer analysis.

Multi-model routing:
  - GPT-4o-mini / Claude Haiku  → routine checks
  - GPT-4 / Claude Sonnet       → complex water-rights analysis

Falls back to deterministic analysis when API keys are unavailable.
"""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _call_openai(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 1024) -> Optional[str]:
    if not OPENAI_KEY:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": (
                    "You are a California water rights attorney and hydrologist. "
                    "Provide concise, factual analysis citing specific CWC sections."
                )},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return None


def _call_anthropic(prompt: str, model: str = "claude-3-haiku-20240307", max_tokens: int = 1024) -> Optional[str]:
    if not ANTHROPIC_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=(
                "You are a California water rights attorney and hydrologist. "
                "Provide concise, factual analysis citing specific CWC sections."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as exc:
        logger.warning("Anthropic call failed: %s", exc)
        return None


def analyze_transfer(
    seller: Dict, buyer: Dict, transfer: Dict,
    stage_results: list,
    tier: str = "routine",
) -> Dict[str, Any]:
    """
    Run LLM analysis on a transfer. tier="routine" uses smaller model,
    tier="complex" uses larger model for water-rights disputes.
    """
    prompt = _build_prompt(seller, buyer, transfer, stage_results)

    analysis_text = None
    model_used = "none"

    if tier == "complex":
        analysis_text = _call_openai(prompt, model="gpt-4", max_tokens=2048)
        if analysis_text:
            model_used = "gpt-4"
        else:
            analysis_text = _call_anthropic(prompt, model="claude-3-sonnet-20240229", max_tokens=2048)
            if analysis_text:
                model_used = "claude-3-sonnet"
    else:
        analysis_text = _call_openai(prompt, model="gpt-4o-mini")
        if analysis_text:
            model_used = "gpt-4o-mini"
        else:
            analysis_text = _call_anthropic(prompt, model="claude-3-haiku-20240307")
            if analysis_text:
                model_used = "claude-3-haiku"

    if analysis_text is None:
        analysis_text = _deterministic_analysis(seller, buyer, transfer, stage_results)
        model_used = "deterministic_fallback"

    return {
        "rights_analysis": {
            "analysis": analysis_text,
            "model_tier": "large" if "gpt-4" in model_used or "sonnet" in model_used else "fallback",
            "model": model_used,
        }
    }


def generate_report(
    seller: Dict, buyer: Dict, transfer: Dict,
    decision: str, score: float,
    stage_results: list,
    conditions: list,
    risk_flags: list,
) -> str:
    """Generate a human-readable compliance report."""
    lines = [
        "═" * 60,
        "  WATERXCHANGE TRANSFER COMPLIANCE REPORT",
        "═" * 60,
        "",
        f"  Decision:  {decision}",
        f"  Score:     {score:.1%}",
        "",
        f"  Seller:    {seller.get('name', 'Unknown')} ({seller.get('entity_type', '')})",
        f"  Buyer:     {buyer.get('name', 'Unknown')} ({buyer.get('entity_type', '')})",
        f"  Quantity:  {transfer.get('quantity_af', 0):,.0f} AF",
        f"  Type:      {transfer.get('transfer_type', '')}",
        "",
    ]

    if stage_results:
        lines.append("  STAGE RESULTS:")
        lines.append("  " + "-" * 56)
        for sr in stage_results:
            stage = sr if isinstance(sr, dict) else sr.__dict__
            lines.append(
                f"  {stage.get('stage', ''):28s}  "
                f"{stage.get('finding', ''):12s}  "
                f"{stage.get('score', 0):.0%}"
            )
            if stage.get("reasoning"):
                lines.append(f"    {stage['reasoning'][:100]}")
        lines.append("")

    if conditions:
        lines.append("  CONDITIONS:")
        for i, c in enumerate(conditions, 1):
            lines.append(f"    {i}. {c}")
        lines.append("")

    if risk_flags:
        lines.append("  RISK FLAGS:")
        for f_ in risk_flags:
            lines.append(f"    ⚠ {f_}")
        lines.append("")

    lines.append("═" * 60)
    return "\n".join(lines)


def _build_prompt(seller, buyer, transfer, stage_results):
    parts = [
        "Analyze this California water transfer for legal and hydrologic risks:\n",
        f"Seller: {seller.get('name')} ({seller.get('entity_type')})",
        f"  Basin: {seller.get('basin', 'N/A')}, GSA: {seller.get('gsa', 'N/A')}",
        f"Buyer: {buyer.get('name')} ({buyer.get('entity_type')})",
        f"  Basin: {buyer.get('basin', 'N/A')}, GSA: {buyer.get('gsa', 'N/A')}",
        f"Transfer: {transfer.get('quantity_af', 0)} AF, type={transfer.get('transfer_type', '')}",
        "\nStage results:",
    ]
    for sr in stage_results:
        s = sr if isinstance(sr, dict) else sr.__dict__
        parts.append(f"  {s.get('stage')}: {s.get('finding')} ({s.get('score', 0):.0%}) — {s.get('reasoning', '')[:80]}")

    parts.append(
        "\nProvide: 1) Key legal risks citing CWC sections, "
        "2) Hydrologic concerns, 3) Recommended conditions."
    )
    return "\n".join(parts)


def _deterministic_analysis(seller, buyer, transfer, stage_results):
    """Rule-based fallback when no LLM API key is available."""
    lines = ["[Deterministic Analysis — No LLM API key configured]\n"]

    qty = transfer.get("quantity_af", 0)
    ttype = transfer.get("transfer_type", "")
    src_gsa = transfer.get("source_gsa", seller.get("gsa", ""))
    dst_gsa = transfer.get("destination_gsa", buyer.get("gsa", ""))

    if src_gsa and dst_gsa and src_gsa.lower() != dst_gsa.lower():
        lines.append(
            f"Cross-GSA transfer ({src_gsa} → {dst_gsa}): "
            "Coordination agreement required per CWC §10726.4."
        )

    if ttype == "banked":
        lines.append(
            "Banked water transfer: Verify banking agreement allows "
            "third-party withdrawals and that stored water accounting is current."
        )
    elif ttype == "in_lieu":
        lines.append(
            "In-lieu transfer: Seller must demonstrate reduced pumping "
            "equal to the transfer quantity. Metering verification required."
        )

    failed = [s for s in stage_results if not (s if isinstance(s, dict) else s.__dict__).get("passed", True)]
    if failed:
        lines.append(f"\n{len(failed)} stage(s) did not pass — review required.")

    return "\n".join(lines)
