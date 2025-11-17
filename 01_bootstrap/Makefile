BACKEND_DIR=backend
FRONTEND_DIR=frontend
BACKEND_PORT?=18089
FRONTEND_PORT?=15073

.PHONY: dev backend frontend

dev: backend frontend

dev:
	$(MAKE) backend &
	cd $(FRONTEND_DIR) && npm install && PORT=$(FRONTEND_PORT) npm run dev

backend:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

frontend:
	cd $(FRONTEND_DIR) && npm install && PORT=$(FRONTEND_PORT) npm run dev
