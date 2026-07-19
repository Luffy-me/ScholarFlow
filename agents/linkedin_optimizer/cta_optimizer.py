"""CTA optimizer — choose discussion / save / follow / no CTA to maximize value."""

from __future__ import annotations

import re

from agents.linkedin_optimizer._text import has_question, normalize, word_count
from agents.linkedin_optimizer.schemas import CTARecommendation, LinkedInPostScore


class CTAOptimizer:
    name = "cta_optimizer"

    def recommend(self, text: str, *, score: LinkedInPostScore | None = None) -> CTARecommendation:
        text = normalize(text)
        score = score or LinkedInPostScore()
        discussion = "What constraint have you hit here in practice?"
        save = "Save this for the next time you revisit the trade-off."
        follow = "Follow for more evidence-backed operating notes."

        # Detect existing CTA-ish endings
        ending = text[-180:].lower() if text else ""
        already_has_cta = bool(
            re.search(r"\b(comment|thoughts|agree|follow|save this|what do you think)\b", ending)
        )

        # Decision policy
        if score.discussion_potential >= 70 or has_question(text):
            chosen = "discussion"
            chosen_text = "" if (already_has_cta and "?" in text) else discussion
            rationale = "Discussion CTA maximizes comment value given discussion potential."
        elif score.practical_value >= 75 and score.discussion_potential < 55:
            chosen = "save"
            chosen_text = "" if "save" in ending else save
            rationale = "High practical value → save CTA is the highest-ROI ask."
        elif score.authority >= 75 and score.overall >= 90:
            chosen = "follow"
            chosen_text = "" if "follow" in ending else follow
            rationale = "Strong authority + high overall score → follow CTA is appropriate."
        else:
            chosen = "no_cta"
            chosen_text = ""
            rationale = "No CTA — weak/medium drafts convert better when value is complete without an ask."

        # Very short posts: avoid heavy CTAs
        if word_count(text) < 60 and chosen != "no_cta":
            chosen = "no_cta"
            chosen_text = ""
            rationale = "Draft is short; skip CTA to avoid looking incomplete."

        return CTARecommendation(
            discussion_cta=discussion,
            save_cta=save,
            follow_cta=follow,
            chosen=chosen,
            chosen_text=chosen_text,
            rationale=rationale,
        )

    def apply(self, text: str, cta: CTARecommendation) -> str:
        """Append chosen CTA only; never rewrite body facts."""
        text = normalize(text)
        if cta.chosen == "no_cta" or not cta.chosen_text:
            return text
        if cta.chosen_text.lower() in text.lower():
            return text
        return f"{text.rstrip()}\n\n{cta.chosen_text}".strip()
