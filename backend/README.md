# Database

The hackathon backend uses PostgreSQL and synchronous SQLAlchemy. The first schema contains users, user-owned chat sessions, and session messages. Deleting a user deletes their sessions and messages.

## Initialize a fresh database

From the repository root, create an empty PostgreSQL database, then run:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE'
PYTHONPATH=backend backend/.venv/bin/python -m app.db.init_db
```

`Base.metadata.create_all()` creates missing tables and is safe to rerun on the same schema. It does not alter existing tables or move existing data when models change. For this early hackathon setup, make schema changes only before retaining real user data; introduce a migration process before deploying breaking schema changes or storing data that must be preserved.

## Database test

Use a separate, disposable PostgreSQL database. The test writes and deletes synthetic rows:

```bash
TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/TEST_DATABASE' \
PYTHONPATH=backend backend/.venv/bin/pytest -q backend/tests
```