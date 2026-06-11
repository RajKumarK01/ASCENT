"""Assessment Agent — generates grounded, cited questions and scores readiness.

Grounding: Foundry IQ (questions from approved content) + Fabric IQ (thresholds).
Acts as the Critic/Verifier in the workflow: refuses to emit questions with no
citation, and feeds readiness back into the planning loop.
"""
from __future__ import annotations

from ..iq import foundry_iq, fabric_iq
from ..config import MODE, MODEL_DEPLOYMENT

SYSTEM_PROMPT = """You are the Assessment Agent for an enterprise certification programme.
Generate one realistic multiple-choice practice exam question testing the given skill.
Use the provided knowledge base context for accuracy and difficulty.
Respond with JSON only:
{
  "question": "...",
  "choices": ["correct answer", "plausible wrong answer 1", "plausible wrong answer 2", "plausible wrong answer 3"],
  "correct_index": 0,
  "hint": "...",
  "explanation": "one sentence why the correct answer is right"
}
The correct answer MUST be choices[correct_index]. Make wrong answers plausible but clearly incorrect."""


def generate_questions(cert_id: str, skills: list[str], n: int = 3) -> list[dict]:
    questions = []
    for skill in skills[:n]:
        grounded = foundry_iq.retrieve(f"{cert_id} {skill}")
        if not grounded.is_grounded:
            continue  # verifier: skip uncited questions

        if MODE == "foundry":
            question_text = _llm_question(cert_id, skill, grounded)
        else:
            question_text = f"Based on approved material, explain how {skill} is applied for {cert_id}."

        if question_text:
            q: dict = {
                "skill": skill,
                "question": question_text if isinstance(question_text, str) else question_text.get("question", ""),
                "citations": [c.source for c in grounded.citations],
            }
            if isinstance(question_text, dict):
                q["choices"] = question_text.get("choices", [])
                q["correct_index"] = question_text.get("correct_index", 0)
                q["hint"] = question_text.get("hint", "")
                q["explanation"] = question_text.get("explanation", "")
            questions.append(q)
    return questions


def _llm_question(cert_id: str, skill: str, grounded) -> dict | str | None:
    try:
        import json as _json
        from ._foundry import get_openai_client
        client = get_openai_client()
        citation = grounded.citations[0].source.split("/")[-1] if grounded.citations else "approved content"
        user_msg = (
            f"Certification: {cert_id}. Skill to test: {skill}.\n\n"
            f"Knowledge base context (source: {citation}):\n{grounded.answer[:600]}\n\n"
            "Write one realistic multiple-choice practice exam question. "
            "Return JSON with keys: question, choices (array of 4 strings), correct_index (0-3), hint, explanation."
        )
        resp = client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            response_format={"type": "json_object"},
            max_tokens=300,
        )
        data = _json.loads(resp.choices[0].message.content)
        if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) >= 2:
            return data
        return data.get("question", f"Based on approved material, explain how {skill} is applied for {cert_id}.")
    except Exception:
        return f"Based on approved material, explain how {skill} is applied for {cert_id}."


def run(cert_id: str, skills: list[str], practice_score_avg: float, hours_studied: float) -> dict:
    questions = generate_questions(cert_id, skills)
    readiness = fabric_iq.readiness(practice_score_avg, hours_studied, cert_id)
    return {
        "agent": "assessment",
        "certification": cert_id,
        "questions": questions,
        "all_questions_cited": all(q["citations"] for q in questions) and len(questions) > 0,
        "readiness": readiness,
        "passed": readiness["ready"],
    }
