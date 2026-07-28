Build a simple REST API for a to-do list using Python and FastAPI.

Requirements:
- Store tasks in memory (a Python list), no database.
- Each task has: id (int), title (string), done (boolean).
- Start with a few example tasks already in the list.
- Endpoints:
  - GET /tasks - list all tasks
  - GET /tasks/{id} - get one task, 404 if it doesn't exist
  - POST /tasks - create a new task from JSON body {"title": "..."}, return 201.
    Reject empty/missing title with a 400 error.
  - PUT /tasks/{id} - update a task's title and/or done status. 404 if missing.
  - DELETE /tasks/{id} - delete a task, return 204. 404 if missing.
- Also add a GET / that returns some basic info about the API, and a GET /health
  that returns {"status": "ok"}.
- Use proper HTTP status codes throughout.
- I want Swagger docs to show up automatically (FastAPI gives this for free at /docs).

Please write this as a single main.py file I can run with uvicorn.
