"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
from pathlib import Path

from src.extensions.kb_extension import rag_search
from src.sql.text2sql import run_text2sql

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

# ============================================================
# UAT-LOCKED: This route has passed UAT. DO NOT MODIFY.
# ============================================================
@app.get("/activities")
def get_activities():
    return activities


# ============================================================
# UAT-LOCKED: This route has passed UAT. DO NOT MODIFY.
# ============================================================
@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


class AskRequest(BaseModel):
    question: str | None = None


def classify_query(question: str) -> str:
    """
    Classify a natural language question as rag, text2sql, or unknown.

    Uses keyword matching — no external calls.
    """
    q = question.lower()

    signup_keywords = ("sign up", "register", "join")
    if any(keyword in q for keyword in signup_keywords):
        return "direct"

    rag_keywords = (
        "tell me about", "what is", "describe", "how does", "explain",
        "what are", "what's",
    )
    if any(keyword in q for keyword in rag_keywords):
        return "rag"

    text2sql_keywords = (
        "how many", "which", "list", "count", "total", "how much", "how full",
        "how many spots", "which activities", "list all",
    )
    if any(keyword in q for keyword in text2sql_keywords):
        return "text2sql"

    return "unknown"


@app.post("/api/ask")
def ask(body: AskRequest):
    """Answer natural language questions about school activities."""
    if body.question is None:
        raise HTTPException(status_code=400, detail="question field required")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question field required")

    try:
        route = classify_query(question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="classification failed") from exc

    if route == "rag":
        try:
            return rag_search(question)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="classification failed") from exc

    if route == "text2sql":
        try:
            return run_text2sql(question)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="classification failed") from exc

    if route == "direct":
        return {
            "answer": (
                "To sign up for an activity, visit the main activities page "
                "and use the signup form, or POST to "
                "/activities/{activity_name}/signup with your email."
            ),
            "source": "direct",
            "confidence": 1.0,
        }

    return {
        "answer": (
            "I can only answer questions about activities. Try asking what an "
            "activity is about, or how many students have joined."
        ),
        "source": "direct",
        "confidence": 1.0,
    }


