from reviews.services.chat.base import ChatClient

ROLE_MAP = {"USER": "user", "ASSISTANT": "model"}


class GeminiChatClient(ChatClient):
    """Raises on any failure (network, quota, empty response) rather than
    swallowing it -- callers should wrap this in ResilientChatClient so a
    live-API failure degrades to the offline template search instead of a
    dead-end error message."""

    def __init__(self, api_key: str, model: str):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def answer(self, question: str, contract_text: str, findings_context: str, history: list[dict]) -> str:
        from google.genai import types

        contents = [
            types.Content(role=ROLE_MAP.get(turn["role"], "user"), parts=[types.Part(text=turn["content"])])
            for turn in history
        ]
        contents.append(types.Content(role="user", parts=[types.Part(text=question)]))

        system_instruction = (
            "You are ClauseGuard's contract assistant. Answer ONLY using the contract text and "
            "flagged findings below -- never speculate or use outside knowledge about contract law "
            "in general. If the answer isn't in the contract, say so plainly rather than guessing. "
            "When relevant, quote the exact clause language in quotation marks so the user can verify "
            "it themselves. Write 2-4 sentences of plain prose -- no markdown headers or bullet lists, "
            "no preamble like 'Based on the contract'. You are not a lawyer and this is not legal "
            "advice; say so only if the user's question calls for a legal judgment you can't make.\n\n"
            f"CONTRACT TEXT:\n{contract_text[:12000]}\n\nFLAGGED FINDINGS:\n{findings_context}"
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.2,
                # See redline/gemini_client.py -- without this, "thinking"
                # models can spend the whole token budget reasoning and
                # return an empty response (finish_reason=MAX_TOKENS).
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text
