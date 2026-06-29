# Copilot Instructions - Merington High School Activities API

## Project context
This file contains instructions for GitHub Copilot to assist in developing the Merington High School.

## NEVER_MODIFY - UAT-LOCKED Code
These following have passed UAT  and must not modified by any Copilot suggestion.

### Routes(src.app.py)
 - 'get_activities' - the GET /activities route
 - 'sign_in' - the POST /activities/{activity_name}/signup
 - 'remove_signup_for_activity' - the POST /activities/{activity_name}/signup route

### Tests(src/tests/test_app.py)
 - ALL existing testsfunctions - never delete,modify or,rename.
 - Never reduce assertion count in any existing test function.
 -

## What Copilot MAY help with
- New routes, functions, and tests that are not part of the UAT-LOCKED code.
- README and documentation updates.
- requirements.txt updates.

## Constraints
- Always use Falsks jsonify for returning JSON responses.
- Alweays return appropriate HTTP status codes for success and error scenarios.
- New routes and functions should be well-documented with docstrings and must have a corresponding test function in src/tests/test_app.py.

## Capstone — AI Ask Endpoint

### New in-scope files (capstone only)
- `src/app.py` — add /api/ask endpoint and classify_query() below existing routes
- `src/extensions/kb_extension.py` — RAG tool wrapper
- `src/sql/text2sql.py` — Text2SQL tool wrapper
- `src/static/ask.html` — frontend widget
- `src/tests/test_app.py` — new tests at BOTTOM only

### Capstone NEVER_MODIFY (in addition to existing NEVER_MODIFY list)
- src/static/index.html — existing UI must not change
- The activities dictionary — do not restructure, rename, or move
- Any existing route function signatures

### Query routing logic
- "Tell me about", "What is", "Describe", "How does" → RAG tool
- "How many", "Which activities", "List all", "How many spots" → Text2SQL
- "Sign up", "Register", "Join" → return link to existing signup endpoint (do not implement)

### API contract for /api/ask
POST /api/ask
Body: {"question": "string"}
Response 200: {"answer": "string", "source": "rag"|"text2sql"|"direct", "confidence": 0-1}
Response 400: {"error": "question field required"}
Response 500: {"error": "classification failed"}