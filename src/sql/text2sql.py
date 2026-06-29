"""
Text2SQL tool for quantitative activity questions.

Generates parameterised SELECT queries and executes them against the
in-memory activities data (PostgreSQL fallback per trainer notes).
"""

import re

ACTIVITIES_SCHEMA = """
activities(name TEXT, description TEXT, schedule TEXT,
max_participants INT, participants JSONB)
"""


def security_validate(sql: str) -> bool:
    """
    Validate that SQL is a safe, parameterised SELECT on activities only.

    Rejects destructive statements and f-string-style user input patterns.
    """
    normalised = sql.strip().upper()
    if not normalised.startswith("SELECT"):
        return False

    forbidden = ("DELETE", "DROP", "UPDATE", "INSERT", "TRUNCATE", "ALTER")
    for keyword in forbidden:
        if keyword in normalised:
            return False

    if "ACTIVITIES" not in normalised:
        return False

    # Reject f-string / format-style injection patterns
    if re.search(r"\{[^}]+\}", sql):
        return False
    if re.search(r"'\s*\+\s*", sql):
        return False
    if re.search(r"=\s*'[^']*\{", sql):
        return False

    return True


def _generate_sql(question: str) -> tuple[str, list]:
    """Generate a parameterised SELECT query from a natural language question."""
    question_lower = question.lower()

    if "how many" in question_lower or "count" in question_lower:
        for activity_name in _get_activity_names():
            if activity_name.lower() in question_lower:
                sql = (
                    "SELECT jsonb_array_length(participants) AS participant_count "
                    "FROM activities WHERE name = %s"
                )
                return sql, [activity_name]

        sql = (
            "SELECT name, jsonb_array_length(participants) AS participant_count "
            "FROM activities"
        )
        return sql, []

    if "list" in question_lower or "which" in question_lower:
        sql = "SELECT name, max_participants FROM activities"
        return sql, []

    sql = "SELECT name, description FROM activities WHERE name = %s"
    activity = _extract_activity_name(question)
    return sql, [activity] if activity else [""]


def _get_activity_names() -> list[str]:
    from src.app import activities

    return list(activities.keys())


def _extract_activity_name(question: str) -> str | None:
    for name in _get_activity_names():
        if name.lower() in question.lower():
            return name
    return None


def _execute_sql(sql: str, params: list) -> list[dict]:
    """Execute a validated SELECT against the in-memory activities dict."""
    from src.app import activities

    if "jsonb_array_length(participants)" in sql and "WHERE name = %s" in sql:
        name = params[0]
        if name not in activities:
            return []
        count = len(activities[name]["participants"])
        return [{"participant_count": count}]

    if "jsonb_array_length(participants)" in sql:
        return [
            {"name": name, "participant_count": len(data["participants"])}
            for name, data in activities.items()
        ]

    if "max_participants" in sql:
        return [
            {"name": name, "max_participants": data["max_participants"]}
            for name, data in activities.items()
        ]

    if "WHERE name = %s" in sql:
        name = params[0]
        if name not in activities:
            return []
        data = activities[name]
        return [{"name": name, "description": data["description"]}]

    return []


def _format_answer(question: str, rows: list[dict]) -> str:
    """Format query results as a human-readable sentence."""
    if not rows:
        return "No matching activity data was found."

    if "participant_count" in rows[0] and "name" not in rows[0]:
        count = rows[0]["participant_count"]
        activity = _extract_activity_name(question) or "that activity"
        return f"There are {count} students signed up for {activity}."

    if "participant_count" in rows[0]:
        parts = [
            f"{row['name']}: {row['participant_count']} students"
            for row in rows
        ]
        return "Participant counts — " + "; ".join(parts) + "."

    if "max_participants" in rows[0]:
        parts = [
            f"{row['name']} (max {row['max_participants']})" for row in rows
        ]
        return "Activities — " + ", ".join(parts) + "."

    if "description" in rows[0]:
        row = rows[0]
        return f"{row['name']}: {row['description']}"

    return str(rows)


def run_text2sql(question: str) -> dict:
    """
    Convert a quantitative question to SQL, validate, execute, and format.

    Returns dict with answer, source, and confidence keys.
    """
    try:
        sql, params = _generate_sql(question)

        if not security_validate(sql):
            return {
                "answer": "Could not generate a safe query for that question.",
                "source": "text2sql",
                "confidence": 0.0,
            }

        rows = _execute_sql(sql, params)
        answer = _format_answer(question, rows)
        return {"answer": answer, "source": "text2sql", "confidence": 1.0}

    except Exception:
        return {
            "answer": "An error occurred while querying activity data.",
            "source": "text2sql",
            "confidence": 0.0,
        }
