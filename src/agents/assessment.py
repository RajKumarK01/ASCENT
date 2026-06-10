"""Assessment Agent — generates grounded, cited questions and scores readiness.

Grounding: Foundry IQ (questions from approved content) + Fabric IQ (thresholds).
Acts as the Critic/Verifier in the workflow: refuses to emit questions with no
citation, and feeds readiness back into the planning loop.
"""
from __future__ import annotations

from ..iq import foundry_iq, fabric_iq
from ..config import MODE, MODEL_DEPLOYMENT

SYSTEM_PROMPT = """You are the Assessment Agent for an enterprise certification programme.
Generate one realistic practice exam question testing the given skill in the context of
the certification. Use the provided knowledge base context to inform difficulty and framing.
Respond with JSON only: {"question": "...", "hint": "..."}"""


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
            questions.append({
                "skill": skill,
                "question": question_text,
                "citations": [c.source for c in grounded.citations],
            })
    return questions


def _llm_question(cert_id: str, skill: str, grounded) -> str | None:
    try:
        import json as _json
        from ._foundry import get_openai_client
        client = get_openai_client()
        citation = grounded.citations[0].source.split("/")[-1] if grounded.citations else "approved content"
        user_msg = (
            f"Certification: {cert_id}. Skill to test: {skill}.\n\n"
            f"Knowledge base context (source: {citation}):\n{grounded.answer[:600]}\n\n"
            "Write one realistic practice exam question for this skill and certification. "
            "Return JSON: {\"question\": \"...\", \"hint\": \"...\"}"
        )
        resp = client.chat.completions.create(
            model=MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
        )
        data = _json.loads(resp.choices[0].message.content)
        return data.get("question")
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
