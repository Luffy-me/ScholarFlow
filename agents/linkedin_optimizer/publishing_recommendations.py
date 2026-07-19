"""Publishing recommendations — day/window/hashtags/length (local heuristics)."""

from __future__ import annotations

from agents.linkedin_optimizer._text import normalize, word_count
from agents.linkedin_optimizer.schemas import (
    CarouselReviewReport,
    LinkedInPostScore,
    PublishingRecommendations,
)


class PublishingAdvisor:
    name = "publishing_recommendations"

    def recommend(
        self,
        text: str,
        *,
        score: LinkedInPostScore | None = None,
        carousel: CarouselReviewReport | None = None,
        content_mode: str = "founder",
    ) -> PublishingRecommendations:
        text = normalize(text)
        wc = word_count(text)
        score = score or LinkedInPostScore()
        notes: list[str] = []

        # Practitioner audience: Tue–Thu mornings in audience local time
        if content_mode in {"researcher", "technical"}:
            day = "Tuesday"
            window = "08:30–10:00 local"
        elif content_mode in {"founder", "operator"}:
            day = "Wednesday"
            window = "09:00–11:00 local"
        else:
            day = "Thursday"
            window = "10:00–12:00 local"

        # Hashtags: usually low value for expert posts; help only for discovery niches
        hashtags_help = False
        hashtag_note = "Skip hashtag soup; expert posts rarely need more than 0–2 niche tags."
        if score.authority < 55 and score.novelty >= 70:
            hashtags_help = True
            hashtag_note = "Up to 2 niche hashtags may aid discovery given lower authority."
            notes.append("Keep hashtags niche and trailing — never in the hook.")
        else:
            notes.append("Prefer zero hashtags unless targeting a specific niche search.")

        ideal_post = (120, 220)
        if score.discussion_potential >= 75:
            ideal_post = (140, 260)
            notes.append("Discussion-heavy posts can run slightly longer.")
        if wc < ideal_post[0]:
            notes.append(f"Draft is short ({wc} words); consider adding one concrete example already in evidence.")
        elif wc > ideal_post[1] + 40:
            notes.append(f"Draft is long ({wc} words); trim for feed scanning.")

        ideal_carousel = (6, 10)
        if carousel and carousel.slide_count:
            if carousel.slide_count < 6:
                notes.append("Carousel is short; 6–10 slides usually perform better for frameworks.")
            elif carousel.slide_count > 10:
                notes.append("Carousel may be long; consider splitting into two posts.")

        notes.append(f"Suggested publish window: {day} {window}.")
        return PublishingRecommendations(
            best_posting_day=day,
            best_posting_window=window,
            hashtags_help=hashtags_help,
            hashtag_note=hashtag_note,
            ideal_post_length_words=ideal_post,
            ideal_carousel_length_slides=ideal_carousel,
            notes=notes,
        )
