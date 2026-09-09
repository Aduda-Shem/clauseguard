import math
import re

from reviews.services.chat.base import ChatClient

STOPWORDS = {
    "the", "a", "an", "is", "are", "of", "to", "in", "and", "or", "for", "on",
    "what", "does", "do", "this", "that", "it", "was", "were", "be", "can",
    "i", "you", "my", "your", "will", "have", "has", "if", "when", "how",
    "about", "with", "at", "by", "as", "from", "into", "under", "any",
}
RISK_INTENT_WORDS = {
    "risk", "risks", "risky", "danger", "dangerous", "concern", "concerns",
    "concerning", "problem", "problems", "issue", "issues", "worst",
    "biggest", "worry", "worrying", "exposure", "flag", "flagged", "flags",
}
EMPTY_FINDINGS_MARKERS = {
    "No review has been completed yet.",
    "No risk findings against the current playbook.",
}
WORD_RE = re.compile(r"[a-z][a-z']*")
MIN_SEGMENT_LENGTH = 25
MIN_MATCH_SCORE = 0.35
FALLBACK_NOTE = (
    "ClauseGuard's live AI assistant isn't available right now, so this is a "
    "keyword-matched excerpt from the contract rather than a generated answer."
)


def _words(text: str) -> set[str]:
    return {w for w in WORD_RE.findall(text.lower()) if w not in STOPWORDS}


def _segments(contract_text: str) -> list[str]:
    """Paragraph-sized chunks, with long paragraphs broken into sentences so
    one relevant sentence isn't buried inside an otherwise-unrelated block."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", contract_text) if p.strip()]
    segments = []
    for paragraph in paragraphs:
        if len(paragraph) <= 400:
            segments.append(paragraph)
            continue
        segments.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip())
    return segments


def _risk_answer(findings_context: str) -> str | None:
    """Answer "what's the biggest risk"-style questions directly from the
    already-computed, already-sorted-worst-first rule-based findings instead
    of trying (and failing) to keyword-search the raw contract text for a
    word like "risk" that a real contract is unlikely to use about itself."""
    if not findings_context or findings_context.strip() in EMPTY_FINDINGS_MARKERS:
        return None
    lines = [line.strip() for line in findings_context.splitlines() if line.strip().startswith("-")]
    if not lines:
        return None

    top, rest = lines[0].lstrip("- "), lines[1:4]
    answer = f"Based on the completed review, the top concern is: {top}"
    if rest:
        others = "\n".join(f"- {line.lstrip('- ')}" for line in rest)
        answer += f"\n\nOther flagged items:\n{others}"
    return answer


class TemplateChatClient(ChatClient):
    """Offline fallback: answers risk/concern questions from the rule-based
    findings directly, and everything else via IDF-weighted keyword search
    over the contract text. Not a real Q&A model -- says so explicitly
    rather than pretending to be a language model."""

    def answer(self, question: str, contract_text: str, findings_context: str, history: list[dict]) -> str:
        question_words = _words(question)
        if not question_words:
            return "Ask a specific question about a clause, obligation, or date in this contract."

        if question_words & RISK_INTENT_WORDS:
            risk_answer = _risk_answer(findings_context)
            if risk_answer:
                return f"{FALLBACK_NOTE}\n\n{risk_answer}"

        segments = _segments(contract_text)
        if not segments:
            return f"{FALLBACK_NOTE} This contract doesn't have enough text to search."

        segment_words = [_words(s) for s in segments]

        # Down-weight words that appear in almost every segment (e.g. a
        # boilerplate term repeated in every clause heading) so a rare,
        # distinguishing word decides the match instead of a common one.
        document_frequency: dict[str, int] = {}
        for words in segment_words:
            for w in words:
                document_frequency[w] = document_frequency.get(w, 0) + 1

        def weight(word: str) -> float:
            return 1.0 / math.log(2 + document_frequency.get(word, 0))

        best_index, best_score = None, 0.0
        for i, words in enumerate(segment_words):
            overlap = question_words & words
            if not overlap:
                continue
            score = sum(weight(w) for w in overlap)
            if len(segments[i]) < MIN_SEGMENT_LENGTH:
                score *= 0.5  # short fragments rarely stand alone as a useful answer
            if score > best_score:
                best_index, best_score = i, score

        if best_index is None or best_score < MIN_MATCH_SCORE:
            return (
                f"{FALLBACK_NOTE} I couldn't find anything in this contract clearly related to that "
                "question -- try asking about a specific clause, party, date, or amount."
            )

        excerpt = segments[best_index]
        if len(excerpt) < 80 and best_index + 1 < len(segments):
            excerpt = f"{excerpt} {segments[best_index + 1]}".strip()

        return f'{FALLBACK_NOTE}\n\nMost relevant passage:\n"{excerpt[:600]}"'
