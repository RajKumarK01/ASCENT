"""Agent tool definitions and execution.

Exposes Microsoft Learn (search + fetch) and YouTube search as callable tools
for LLM agents via OpenAI function-calling.  The LLM decides which tools to
invoke and in what order; tool_loop() handles the multi-turn execution.
"""
from __future__ import annotations
import json
import os
import urllib.parse
import urllib.request

# ── Tool schemas (OpenAI function-calling format) ───────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "microsoft_docs_search",
            "description": (
                "Search Microsoft Learn for official training paths, exam objectives, "
                "and module lists. Use this to ground answers in current Microsoft content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — be specific (e.g. 'AZ-204 Azure Functions durable patterns')",
                    },
                    "top": {
                        "type": "integer",
                        "description": "Number of results to return (1-5).",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "microsoft_docs_fetch",
            "description": (
                "Fetch the full content of a specific Microsoft Learn page by URL. "
                "Use after microsoft_docs_search to get deeper module detail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "A learn.microsoft.com URL returned by microsoft_docs_search.",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_search",
            "description": (
                "Search YouTube for tutorial videos on an Azure/Microsoft topic. "
                "Use to recommend the most relevant learning video for a skill. "
                "Always call this to recommend a video — never guess a URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query optimised for the learner's level and skill gap.",
                    },
                    "skill_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "Learner's current level — shapes the query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of candidate videos to evaluate (1-5).",
                        "default": 3,
                    },
                },
                "required": ["query", "skill_level"],
            },
        },
    },
]


# ── Tool execution ────────────────────────────────────────────────────────────

def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return its result as a JSON string."""
    try:
        if name == "microsoft_docs_search":
            return _ms_learn_search(arguments.get("query", ""), arguments.get("top", 3))
        if name == "microsoft_docs_fetch":
            return _ms_learn_fetch(arguments.get("url", ""))
        if name == "youtube_search":
            return _youtube_search(
                arguments.get("query", ""),
                arguments.get("skill_level", "intermediate"),
                arguments.get("max_results", 3),
            )
    except Exception as exc:
        return json.dumps({"error": str(exc)})
    return json.dumps({"error": f"Unknown tool: {name}"})


def _ms_learn_search(query: str, top: int = 3) -> str:
    encoded = urllib.parse.quote(query)
    url = (
        f"https://learn.microsoft.com/api/search"
        f"?search={encoded}&locale=en-us&%24top={min(top, 5)}&facet=category"
    )
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                "User-Agent": "ASCENT/1.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode())
    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url") or r.get("displayUrl", ""),
            "description": (r.get("description") or "")[:200],
        }
        for r in data.get("results", [])[:top]
    ]
    return json.dumps({"results": results, "total": len(results)})


def _ms_learn_fetch(url: str) -> str:
    if not url.startswith("https://learn.microsoft.com"):
        return json.dumps({"error": "Only learn.microsoft.com URLs are supported."})
    req = urllib.request.Request(url, headers={"Accept": "text/html",
                                                "User-Agent": "ASCENT/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode(errors="replace")
    # Strip HTML tags for a lightweight text extract
    import re
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()[:3000]
    return json.dumps({"url": url, "content": text})


# Curated synthetic-safe fallback so the planner always has a candidate to reason
# over (no YouTube key, API quota error, or in the hosted agent). IDs reuse the
# repo's existing curated set; unmatched skills fall back to the AZ-204 full course.
_GENERIC_VIDEO = {"video_id": "jZx8PMQjobk",
                  "title": "Azure Developer (AZ-204) — Full Course", "channel": "freeCodeCamp.org"}
_CURATED_VIDEOS: dict[str, dict] = {
    "api":      {"video_id": "9HFB3UG5CQ4", "title": "Azure API Management Tutorial", "channel": "Microsoft Azure"},
    "function": {"video_id": "Vxf-rOEO1q4", "title": "Azure Functions Full Tutorial", "channel": "Microsoft Azure"},
    "storage":  {"video_id": "UzTtastcBsk", "title": "Azure Storage Overview", "channel": "Microsoft Azure"},
}


def _curated_videos(query: str, max_results: int = 3) -> list[dict]:
    q = query.lower()
    hits = [v for key, v in _CURATED_VIDEOS.items() if key in q] or [_GENERIC_VIDEO]
    out = []
    for v in hits[:max_results]:
        vid = v["video_id"]
        out.append({
            "video_id": vid, "title": v["title"], "channel": v["channel"],
            "description": "Curated tutorial (offline fallback).",
            "thumbnail_url": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
            "url": f"https://www.youtube.com/watch?v={vid}",
        })
    return out


def _youtube_search(query: str, skill_level: str, max_results: int = 3) -> str:
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    level_hints = {
        "beginner": "introduction overview getting started",
        "intermediate": "tutorial hands-on deep dive",
        "advanced": "advanced patterns best practices architecture",
    }
    enriched = f"{query} {level_hints.get(skill_level, '')} Azure Microsoft"

    if api_key:
        try:
            encoded = urllib.parse.quote(enriched)
            url = (
                f"https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet&q={encoded}&type=video"
                f"&maxResults={min(max_results, 5)}&key={api_key}"
            )
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            videos = []
            for item in data.get("items", []):
                vid_id = item["id"].get("videoId", "")
                snippet = item.get("snippet", {})
                if vid_id:
                    videos.append({
                        "video_id": vid_id,
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "description": (snippet.get("description") or "")[:150],
                        "thumbnail_url": (
                            snippet.get("thumbnails", {}).get("high", {}).get("url")
                            or f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
                        ),
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                    })
            if videos:
                return json.dumps({"videos": videos, "query_used": enriched})
        except Exception:
            pass  # fall through to curated

    # No key, quota error, or empty result → curated fallback.
    return json.dumps({"videos": _curated_videos(query, max_results),
                       "query_used": enriched, "source": "curated"})


# ── Tool-use loop ─────────────────────────────────────────────────────────────

def tool_loop(
    client,
    model: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_turns: int = 6,
) -> tuple[str, list[dict]]:
    """Run a multi-turn tool-use loop.

    Returns (final_text, tool_calls_log).
    tool_calls_log entries: {"tool": name, "args": {...}, "result_summary": str}
    """
    active_tools = tools if tools is not None else TOOL_SCHEMAS
    tool_calls_log: list[dict] = []
    msgs = list(messages)

    for _ in range(max_turns):
        resp = client.chat.completions.create(
            model=model,
            messages=msgs,
            tools=active_tools,
            tool_choice="auto",
            max_tokens=800,
        )
        choice = resp.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return (msg.content or "").strip(), tool_calls_log

        # Append assistant message with tool call intent
        msgs.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name,
                                 "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        # Execute each tool call and feed results back
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = execute_tool(tc.function.name, args)
            result_data = json.loads(result)

            # Summarise for trace (don't log full content)
            if tc.function.name == "microsoft_docs_search":
                n = len(result_data.get("results", []))
                summary = f"{n} result(s) for '{args.get('query','')[:50]}'"
            elif tc.function.name == "microsoft_docs_fetch":
                summary = f"fetched {len(result_data.get('content',''))} chars from {args.get('url','')[:60]}"
            elif tc.function.name == "youtube_search":
                vids = result_data.get("videos", [])
                summary = f"{len(vids)} video(s) — top: '{vids[0]['title'][:50] if vids else 'none'}'"
            else:
                summary = result[:80]

            tool_calls_log.append({
                "tool": tc.function.name,
                "args": args,
                "result_summary": summary,
                "result": result_data,
            })

            msgs.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    # Max turns reached — return last assistant content
    last = next((m for m in reversed(msgs) if m.get("role") == "assistant"), {})
    return (last.get("content") or "").strip(), tool_calls_log
