# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI service; core code sits in `backend/app` (routers, LangChain helpers in `rag/`, config, db helpers).  
- `backend/data/`: stores wake article markdown, FAISS/Chroma vector stores, and SQLite/JSON profile snapshots; ingest tooling lives in `backend/scripts/`.  
- `frontend/`: Vite + React client with code in `frontend/src` and static assets in `public/`.  
- Tests live in `backend/app/tests`, matching each API surface (health, profile, ingest, recommend).

## Build, Test, and Development Commands
- `cp .env.sample .env`: bootstrap local config before editing values.  
- `make install`: installs backend requirements and runs `npm install` inside `frontend/`.  
- `MODE=fake make dev`: launches uvicorn on `:8089` and Vite on `:5173` with coordinated shutdown.  
- `make backend` / `make frontend`: run either service alone; override DB mode or ports via env vars.  
- `MODE=fake DB_MODE=sqlite make seed`: turn `backend/data/wake_articles` markdown into FAISS/Chroma chunks for RAG tests.  
- `make test` executes pytest; `cd frontend && npm run build` creates the production bundle.

## Coding Style & Naming Conventions
Python: 4-space indents, type hints on FastAPI endpoints, and Pydantic response/request objects declared in `models.py`. Keep routers thin—business logic belongs in `db.py`, `rag/`, or dedicated helpers. Use snake_case for functions/modules and PascalCase for classes. Frontend: strict TypeScript, functional React components, PascalCase filenames (`ProfilePanel.tsx`), camelCase hooks/state, and lint before committing with `npm run lint`.

## Testing Guidelines
Run `make test` before pushing; it sets `PYTHONPATH=app` for imports. Mirror new routes with `backend/app/tests/test_<feature>.py`, keep fixtures near the top, and assert both status and payload fields. Refresh sample data under `backend/data` when tests need new examples. Frontend tests are manual today; if you add Vitest or Playwright, place specs under `frontend/src/__tests__/` and document the npm script.

## Commit & Pull Request Guidelines
History follows Conventional Commits (`feat:`, `fix:`, `chore:`), so keep prefixes consistent and scope each commit to a single concern (code + tests + seeds). PRs should describe the change, note env or data mutations (rerun `make seed`, new `.env` keys), include screenshots or `curl` snippets when behavior shifts, and link WAKE Career tracking issues.

## Environment & Configuration Tips
`MODE` selects fake vs live inference (live requires `OPENAI_API_KEY`). Persist profiles via `DB_MODE=sqlite` (default) or `json`; switch JSON paths with `JSON_DB_DIR`. Adjust `BACKEND_PORT`/`FRONTEND_PORT` to avoid conflicts and keep `VITE_API_BASE` aligned with the running backend. Never commit `.env`; just describe new keys in the PR and share secrets through the manager.
