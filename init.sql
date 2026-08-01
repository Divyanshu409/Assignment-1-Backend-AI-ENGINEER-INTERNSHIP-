-- Runs once, automatically, the first time the Postgres container starts
-- with an empty data volume (mounted into /docker-entrypoint-initdb.d).
-- app's repo.init() also does CREATE TABLE IF NOT EXISTS as a safety net
-- for anyone who runs Postgres outside this compose file.

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO tasks (title, done)
SELECT * FROM (VALUES
    ('Buy milk', FALSE),
    ('Write README', FALSE),
    ('Learn FastAPI', TRUE)
) AS seed(title, done)
WHERE NOT EXISTS (SELECT 1 FROM tasks);
