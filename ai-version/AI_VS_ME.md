# AI vs me

## The prompt

See `PROMPT.md` in this folder for the full text. Written from memory, without copying the
assignment document, covering: language/framework, the five CRUD endpoints, status codes,
in-memory storage, and a request for Swagger docs.

## What the AI did better

- **Used Pydantic's `response_model`** (`Task`, `List[Task]`) to define the response shape
  explicitly. I never did this — my version just returns raw dicts. Its version gets automatic
  response validation and cleaner Swagger schemas for free. I understand why it did this: it's
  a more "FastAPI-idiomatic" pattern than mine.
- **Slightly less code** for the same endpoint count, because `response_model` and stricter
  Pydantic types removed some manual checks it assumed didn't need doing.

## What it got wrong or quietly ignored

1. **Wrong status code on missing title.** I asked for a 400 on an invalid POST body. Because
   the AI declared `title: str` (no default) on `TaskCreate`, FastAPI's own request validation
   intercepts a `{}` body *before* the endpoint code ever runs, and returns **422 Unprocessable
   Entity** with a Pydantic-formatted error — not the 400 I asked for. Confirmed by curl:
   `POST /tasks -d '{}'` → `422`, not `400`.
2. **Whitespace-only titles are accepted.** Its check is `if not task.title`, which is only
   falsy for `""` or `None` — not for `"   "`. `POST /tasks -d '{"title":"   "}'` returned
   `201 Created`. My prompt said "reject empty/missing title" and it technically did handle
   *empty*, but not *effectively empty*.
3. **No error message shape guarantee.** I never specified what the error JSON should look
   like, and the AI defaulted to FastAPI's stock `{"detail": "..."}`. Not wrong exactly, since
   I didn't ask for anything specific — but it's a silent, un-flagged decision I'd have wanted
   surfaced.

## What my prompt forgot to specify — and what the AI silently decided

- I never said what key the error JSON should use (`detail` vs `error`), so it picked FastAPI's
  default. My hand-built version deliberately returns `{"error": "..."}` via a custom exception
  handler — a decision the AI had no way to know I wanted.
- I said "reject empty/missing title" but never defined "empty" precisely (empty string only,
  or also whitespace?). The AI picked the narrower interpretation.
- I didn't mention trimming/normalizing title text on save. My version calls `.strip()` before
  storing; the AI's stores titles verbatim, including leading/trailing whitespace.
- I didn't ask for `/stats`, filtering, search, or `/reset` — reasonably, the AI didn't build
  them, since I never asked. (These were "extras" in the original assignment, not core spec.)

## The rematch

**Improved prompt** (added to the original): *"For any 400/404 error, always return JSON in the
exact shape `{"error": "<message>"}` — do not use FastAPI's default `{"detail": ...}` format.
Also: an empty-or-whitespace-only title must be rejected with 400, and it must be caught in your
own code, not left to Pydantic's built-in field validation — so declare `title` as optional in
the request model and validate it yourself."*

**What changed after regenerating:** the rematch version now returns `{"error": "..."}` on both
the 400 and 404 paths, and switched `TaskCreate.title` to `Optional[str] = None` with an explicit
`if not title or not title.strip()` check in the handler — closing both bugs found above, and
landing very close to my own hand-built implementation.

## The lesson

An AI's output is only as good as the spec it's given — and I could only tell where it fell
short because I'd already built the thing myself and knew exactly what "correct" meant for this
API's edge cases (whitespace titles, exact error shape, status code precision).
