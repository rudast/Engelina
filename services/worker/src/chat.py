# ai_worker/chat.py

from model import AIWorkerModel
import json


CHAT_SYSTEM_PROMPT = """
You are an AI English Conversation Tutor.

Your job is to have a natural, friendly conversation in English and help the user practice.
Stay within everyday topics (hobbies, study/work, travel, relationships, lifestyle, feelings, culture, plans) and simple explanations about English.

Always:
- reply in English,
- be warm and supportive,
- adapt to A2–B2 level based on the user,
- ask at least one follow-up question.

If the user asks about programming, math, ML or other unrelated topics, briefly refuse and gently redirect them back to English practice.
"""

FEEDBACK_SYSTEM_PROMPT = """
You are an English language checker.

Your task is to analyse ONLY the user's last message in English and find language mistakes.
You MUST respond with ONE JSON object and NOTHING else.
No markdown, no backticks, no extra text.

JSON format:
{
  "language_feedback": {
    "items": [
      {
        "user_text": "...",
        "error_type": "...",
        "explanation": "...",
        "suggested_correction": "..."
      }
    ],
    "overall_comment": "..."
  }
}

Rules:
- "items": list of 0–5 most important mistakes from the user's last message.
  - "user_text": exact incorrect fragment from the user.
  - "error_type": one of "grammar", "vocabulary", "word_order", "spelling", "punctuation", "style", "other".
  - "explanation": short explanation (you MAY use Russian).
  - "suggested_correction": correct English version.
- If there were NO mistakes:
  - "items": [].
  - "overall_comment": "No mistakes — great job!".

Return ONLY valid JSON with this structure.
"""


def parse_feedback_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in feedback response")
    json_str = raw[start : end + 1]
    return json.loads(json_str)


def main():
    worker = AIWorkerModel(
        max_new_tokens=256,
        reply_temperature=0.6,
        feedback_temperature=0.2,
        top_p=0.9,
        device='auto',
    )

    history: list[dict] = []

    print("AI worker запущен. Напиши 'exit' или 'quit' для выхода.\n")

    while True:
        user_input = input("💬 Ты: ").strip()
        if user_input.lower() in {"exit", "quit", "выход"}:
            break

        history.append({"role": "user", "content": user_input})

        reply_text = worker.generate_reply(
            messages=history,
            system_prompt=CHAT_SYSTEM_PROMPT,
        )

        history.append({"role": "assistant", "content": reply_text})

        print(f"\n🤖 Модель: {reply_text}\n")

        feedback_raw = worker.generate_feedback(
            messages=[{"role": "user", "content": user_input}],
            system_prompt=FEEDBACK_SYSTEM_PROMPT,
        )

        try:
            feedback_data = parse_feedback_json(feedback_raw)
            feedback = feedback_data["language_feedback"]
        except Exception as e:
            print("⚠️ Не удалось распарсить feedback JSON, сырой ответ:")
            print(feedback_raw)
            print()
            continue

        print("🔎 Language Feedback:")
        if feedback["items"]:
            for i, item in enumerate(feedback["items"], start=1):
                print(f"{i}) \"{item['user_text']}\"")
                print(f"   Тип: {item['error_type']}")
                print(f"   Объяснение: {item['explanation']}")
                print(f"   Правильно: {item['suggested_correction']}\n")
        else:
            print(feedback["overall_comment"])
        print("-" * 40)


if __name__ == "__main__":
    main()
