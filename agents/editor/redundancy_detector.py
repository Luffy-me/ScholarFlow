"""Redundancy detector — repeated phrases/words/points."""

from __future__ import annotations

from agents.editor._text import clamp100, normalize, phrase_ngrams, sentences, word_freq
from agents.editor.schemas import CheckReport, EditorialIssue, Severity


class RedundancyDetector:
    name = "redundancy_detector"

    def check(self, text: str) -> CheckReport:
        text = normalize(text)
        issues: list[EditorialIssue] = []
        score = 92

        freq = word_freq(text)
        repeated_words = [(w, c) for w, c in freq.most_common(12) if c >= 4 and w not in {"that", "with", "this", "from", "your", "have"}]
        for w, c in repeated_words[:3]:
            issues.append(
                EditorialIssue(
                    code="REPEATED_WORD",
                    category="redundancy",
                    severity=Severity.MINOR,
                    problem=f"Word '{w}' repeats {c} times.",
                    why="Lexical repetition creates a looping, unedited feel.",
                    suggestion=f"Keep the strongest use of '{w}' and vary or cut the rest.",
                )
            )
            score -= 6

        grams = phrase_ngrams(text, 3)
        for phrase, c in grams.most_common(8):
            if c < 2:
                continue
            if phrase in {"in order to", "the fact that"}:
                continue
            issues.append(
                EditorialIssue(
                    code="REPEATED_PHRASE",
                    category="redundancy",
                    severity=Severity.MAJOR if c >= 3 else Severity.MINOR,
                    problem=f"Phrase '{phrase}' repeats {c} times.",
                    why="Repeated phrases add length without new information.",
                    suggestion="Delete duplicate occurrences; keep the clearest instance.",
                )
            )
            score -= 8 if c >= 3 else 5

        # Near-duplicate sentences
        sents = [s.lower() for s in sentences(text)]
        seen: set[str] = set()
        for s in sents:
            key = " ".join(s.split()[:8])
            if key in seen and len(key) > 20:
                issues.append(
                    EditorialIssue(
                        code="REPEATED_POINT",
                        category="redundancy",
                        severity=Severity.MAJOR,
                        location=s[:100],
                        problem="Near-duplicate sentence/point detected.",
                        why="Restating the same point without new evidence wastes attention.",
                        suggestion="Merge into one sharper sentence or add a new implication.",
                    )
                )
                score -= 12
                break
            seen.add(key)

        return CheckReport(name=self.name, score=clamp100(score), issues=issues)
