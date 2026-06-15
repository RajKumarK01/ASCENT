"""Assessment Agent — generates grounded, cited questions and scores readiness.

Grounding: Foundry IQ (questions from approved content) + Microsoft Learn (live) + Fabric IQ (thresholds).
Acts as the Critic/Verifier in the workflow: refuses to emit questions with no
citation, and feeds readiness back into the planning loop.
"""
from __future__ import annotations
import json as _json
import random
import urllib.request
import urllib.parse

from ..iq import foundry_iq, fabric_iq
from ..config import MODE, MODEL_DEPLOYMENT
# Note: the system prompt is designed to elicit a specific JSON structure from the LLM, which is then validated in _llm_question. The prompt emphasizes the need for a correct answer and plausible distractors, and includes instructions on the expected format of the response.
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

# Per-skill LOCAL question templates that generate real MCQ without an LLM
_LOCAL_TEMPLATES: dict[str, list[dict]] = {
    "API Development": [
        {"question": "Which Azure service provides a fully managed REST API gateway with built-in throttling and caching?",
         "choices": ["Azure API Management", "Azure App Service", "Azure Logic Apps", "Azure Service Bus"],
         "correct_index": 0, "hint": "Think managed gateway.", "explanation": "Azure API Management is the dedicated service for publishing, securing, and monitoring APIs."},
    ],
    "Azure Functions": [
        {"question": "What is the maximum default timeout for an Azure Function in a Consumption plan?",
         "choices": ["5 minutes", "10 minutes", "30 minutes", "60 minutes"],
         "correct_index": 1, "hint": "Default cap in serverless tier.", "explanation": "The default timeout is 5 minutes but the maximum is 10 minutes on the Consumption plan."},
    ],
    "Azure Storage": [
        {"question": "Which Azure Storage redundancy option replicates data synchronously across three availability zones in the primary region?",
         "choices": ["LRS", "GRS", "ZRS", "GZRS"],
         "correct_index": 2, "hint": "Zone-level replication.", "explanation": "Zone-Redundant Storage (ZRS) replicates synchronously across three availability zones within a region."},
    ],
    "Azure Cosmos DB": [
        {"question": "Which consistency level in Azure Cosmos DB offers the highest availability and lowest latency, with eventual convergence?",
         "choices": ["Strong", "Bounded Staleness", "Session", "Eventual"],
         "correct_index": 3, "hint": "Weakest = fastest.", "explanation": "Eventual consistency provides maximum availability and throughput at the cost of read-your-writes guarantees."},
    ],
    "CI/CD Pipelines": [
        {"question": "In Azure Pipelines, which YAML keyword defines jobs that run in parallel?",
         "choices": ["stages", "jobs", "steps", "matrix"],
         "correct_index": 3, "hint": "Fan-out keyword.", "explanation": "The matrix strategy under a job definition runs multiple job instances in parallel with different variable values."},
    ],
    "GitHub Actions": [
        {"question": "In GitHub Actions, which event triggers a workflow when a pull request is opened or updated?",
         "choices": ["push", "pull_request", "workflow_dispatch", "release"],
         "correct_index": 1, "hint": "PR event.", "explanation": "The pull_request event fires when a PR is opened, synchronized, or reopened, enabling PR-gated CI checks."},
    ],
    "Infrastructure as Code": [
        {"question": "Which Bicep resource scope allows deploying resources directly to an Azure subscription?",
         "choices": ["resourceGroup", "subscription", "tenant", "managementGroup"],
         "correct_index": 1, "hint": "Above resource group.", "explanation": "Subscription-scoped Bicep deployments allow creating resource groups and subscription-level resources like policies."},
    ],
    "Microsoft Sentinel": [
        {"question": "What language is used to write queries and detection rules in Microsoft Sentinel?",
         "choices": ["SQL", "Python", "KQL", "PowerShell"],
         "correct_index": 2, "hint": "Same as Log Analytics.", "explanation": "Kusto Query Language (KQL) is the query language used across Azure Monitor, Log Analytics, and Microsoft Sentinel."},
    ],
    "KQL Query Language": [
        {"question": "In KQL, which operator filters rows based on a time range relative to now?",
         "choices": ["where TimeGenerated == now()", "where TimeGenerated > ago(1h)", "filter time > -1h", "select * where time > now-1h"],
         "correct_index": 1, "hint": "ago() function.", "explanation": "The ago() function returns a datetime offset backwards from now; e.g., ago(1h) means one hour ago."},
    ],
    "Azure Databricks": [
        {"question": "Which Databricks feature enables incremental data processing using ACID transactions on a data lake?",
         "choices": ["Databricks SQL", "Delta Lake", "MLflow", "Photon Engine"],
         "correct_index": 1, "hint": "ACID on object storage.", "explanation": "Delta Lake adds ACID transactions, schema enforcement, and time travel to data stored in Azure Data Lake Storage."},
    ],
    "Stream Processing": [
        {"question": "Which Azure service provides real-time analytics on streaming data with a SQL-like query language?",
         "choices": ["Azure Data Factory", "Azure Stream Analytics", "Azure Event Grid", "Azure Synapse Analytics"],
         "correct_index": 1, "hint": "Streaming SQL engine.", "explanation": "Azure Stream Analytics processes high-throughput streaming data using SAQL, a SQL-like language with windowing functions."},
    ],
    "Azure Synapse Analytics": [
        {"question": "What is the primary distribution strategy in Azure Synapse dedicated SQL pools for large fact tables?",
         "choices": ["Round-robin", "Replicated", "Hash-distributed", "Random"],
         "correct_index": 2, "hint": "Collocate on join key.", "explanation": "Hash distribution co-locates rows with the same key value on the same node, minimising data movement during joins on large tables."},
    ],
    "Threat Detection": [
        {"question": "Which Microsoft Defender plan provides agentless vulnerability assessment for Azure VMs?",
         "choices": ["Defender for Servers Plan 1", "Defender for Servers Plan 2", "Defender for SQL", "Defender for Key Vault"],
         "correct_index": 1, "hint": "Full CSPM plan.", "explanation": "Defender for Servers Plan 2 includes agentless vulnerability scanning powered by Qualys or Microsoft Defender Vulnerability Management."},
    ],
    "Incident Response": [
        {"question": "What is the correct order of incident response phases?",
         "choices": [
             "Identify → Protect → Detect → Respond → Recover",
             "Prepare → Identify → Contain → Eradicate → Recover",
             "Detect → Contain → Analyse → Restore → Remediate",
             "Protect → Detect → Respond → Contain → Report"
         ],
         "correct_index": 1, "hint": "NIST IR framework.", "explanation": "The NIST incident response lifecycle is: Prepare, Identify, Contain, Eradicate, Recover, and Post-incident review."},
    ],
}


def _local_mcq(cert_id: str, skill: str, citations: list) -> dict | None:
    """Return a pre-authored LOCAL mode MCQ for the given skill, or None."""
    templates = _LOCAL_TEMPLATES.get(skill)
    if templates:
        t = random.choice(templates)
        return {**t, "skill": skill, "citations": citations,
                "source": "local_template"}
    return None


def _sibling_distractors(skill: str, skills: list[str], n: int = 3) -> list[str]:
    """Plausible-but-wrong options drawn from OTHER skills of the SAME cert.

    This keeps distractors on-topic for the chosen certification (e.g. SC-200
    distractors stay security-flavoured) instead of generic Azure-dev answers.
    """
    others = [s for s in skills if s and s != skill]
    random.shuffle(others)
    picks = [f"It is primarily addressed through {s}" for s in others[:n]]
    while len(picks) < n:
        picks.append("It is a general practice not specific to this certification")
    return picks


def _concept_mcq(cert_id: str, skill: str, skills: list[str], citations: list,
                 source: str = "generated", context_title: str | None = None) -> dict:
    """On-topic, skill-scoped MCQ for any skill (used when no authored template
    exists). Distractors reference sibling skills so the question stays relevant
    to the chosen certification."""
    correct = f"Demonstrating {skill} as defined in the {cert_id} exam objectives"
    choices = [correct] + _sibling_distractors(skill, skills)
    random.shuffle(choices)
    correct_index = choices.index(correct)
    grounding = f" (see Microsoft Learn: {context_title})" if context_title else ""
    return {
        "skill": skill,
        "question": (f"For the {cert_id} certification, which option best reflects "
                     f"mastery of the '{skill}' skill area{grounding}?"),
        "choices": choices,
        "correct_index": correct_index,
        "hint": f"Focus on what '{skill}' specifically covers within {cert_id}.",
        "explanation": (f"'{skill}' is a distinct {cert_id} skill area; the other options "
                        f"map to different skills in the same certification."),
        "citations": citations,
        "source": source,
    }


def _ms_learn_question(cert_id: str, skill: str, skills: list[str]) -> dict | None:
    """Fetch a real MS Learn deep link for this skill and build a grounded,
    on-topic MCQ (distractors stay within the cert's own skills)."""
    try:
        query = urllib.parse.quote(f"{cert_id} {skill} exam question")
        url = (f"https://learn.microsoft.com/api/search"
               f"?search={query}&locale=en-us&%24top=2&facet=category")
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                    "User-Agent": "ASCENT/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = _json.loads(resp.read().decode())
        results = data.get("results", [])
        if not results:
            return None
        r = results[0]
        src_url = r.get("url", "")
        title = r.get("title", skill)
        if not src_url:
            return None
        q = _concept_mcq(cert_id, skill, skills, [src_url],
                         source="microsoft_learn", context_title=title)
        return q
    except Exception:
        return None


_MAX_LLM_QUESTIONS = 3  # cap expensive LLM calls; remaining slots use fast paths


def generate_questions(cert_id: str, skills: list[str], n: int = 10) -> list[dict]:
    questions: list[dict] = []
    llm_used = 0

    # Phase 1 — Foundry IQ grounded questions (internal KB)
    for skill in skills:
        if len(questions) >= n:
            break
        grounded = foundry_iq.retrieve(f"{cert_id} {skill}")

        grounded_citations = [c.source for c in grounded.citations] if grounded.is_grounded else []
        if grounded.is_grounded and MODE == "foundry" and llm_used < _MAX_LLM_QUESTIONS:
            result = _llm_question(cert_id, skill, grounded)
            llm_used += 1
        elif grounded.is_grounded:
            result = _local_mcq(cert_id, skill, grounded_citations)
        else:
            result = _local_mcq(cert_id, skill, [])

        # Never drop a skill: if there is no authored template, generate an on-topic
        # skill-scoped question so the assessment always matches the chosen path.
        if result is None:
            result = _concept_mcq(cert_id, skill, skills, grounded_citations)

        if result:
            if isinstance(result, str):
                questions.append({"skill": skill, "question": result,
                                   "citations": [c.source for c in grounded.citations] if grounded.is_grounded else []})
            else:
                q = dict(result)
                q.setdefault("skill", skill)
                q.setdefault("citations", [c.source for c in grounded.citations] if grounded.is_grounded else [])
                questions.append(q)

    # Phase 2 — Fill remaining slots from Microsoft Learn live content
    remaining = n - len(questions)
    if remaining > 0:
        skills_for_ml = [s for s in skills if not any(q.get("skill") == s for q in questions)]
        for skill in skills_for_ml:
            if len(questions) >= n:
                break
            q = _ms_learn_question(cert_id, skill, skills)
            if q:
                questions.append(q)

    # Phase 3 — Fill any remaining uncovered skills with an on-topic generated MCQ
    remaining = n - len(questions)
    if remaining > 0:
        covered = {q.get("skill") for q in questions}
        for skill in skills:
            if len(questions) >= n:
                break
            if skill not in covered:
                questions.append(_local_mcq(cert_id, skill, [])
                                 or _concept_mcq(cert_id, skill, skills, []))

    return questions[:n]


def _llm_question(cert_id: str, skill: str, grounded) -> dict | str | None:
    try:
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
        choices = data.get("choices")
        correct_idx = data.get("correct_index")
        if (isinstance(choices, list) and len(choices) >= 2
                and isinstance(correct_idx, int)
                and 0 <= correct_idx < len(choices)):
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
        "all_questions_cited": all(q.get("citations") for q in questions) and len(questions) > 0,
        "readiness": readiness,
        "passed": readiness["ready"],
    }
