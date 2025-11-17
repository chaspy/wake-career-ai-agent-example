BACKEND_DIR=backend
FRONTEND_DIR=frontend

.PHONY: dev backend frontend

dev: backend frontend

backend:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8089

frontend:
	cd $(FRONTEND_DIR) && npm install && npm run dev
