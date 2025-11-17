ifneq (,$(wildcard .env))
include .env
export $(shell sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env)
endif

MODE ?= live
DB_MODE ?= sqlite
UV ?= uv
BACKEND_DIR ?= backend
BACKEND_VENV ?= $(BACKEND_DIR)/.venv
BACKEND_VENV_REL ?= .venv
BACKEND_PYTHON ?= $(BACKEND_VENV)/bin/python
BACKEND_PYTHON_REL ?= $(BACKEND_VENV_REL)/bin/python
BACKEND_PORT ?= 8089
FRONTEND_PORT ?= 5173

.PHONY: install install-backend install-frontend dev backend frontend test lint fmt clean seed

$(BACKEND_PYTHON):
	cd $(BACKEND_DIR) && $(UV) venv $(BACKEND_VENV_REL)

install-backend: $(BACKEND_PYTHON)
	cd $(BACKEND_DIR) && $(UV) pip install --python $(BACKEND_PYTHON_REL) -r requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

backend:
	@echo "[backend] MODE=$(MODE) DB_MODE=$(DB_MODE) PORT=$(BACKEND_PORT)"
	@MODE=$(MODE) DB_MODE=$(DB_MODE) BACKEND_PORT=$(BACKEND_PORT) bash -c 'cd backend && \
	  $(BACKEND_PYTHON_REL) -m uvicorn uvicorn_app:app --reload --host 0.0.0.0 --port $$BACKEND_PORT'

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

dev:
	@echo "Starting dev servers... (MODE=$(MODE), DB_MODE=$(DB_MODE), BACKEND_PORT=$(BACKEND_PORT), FRONTEND_PORT=$(FRONTEND_PORT))"
	@MODE=$(MODE) DB_MODE=$(DB_MODE) BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) bash -c 'set -euo pipefail; trap "kill 0" EXIT; \
	  echo "[backend] launching on port $$BACKEND_PORT"; \
	  (cd backend && $(BACKEND_PYTHON_REL) -m uvicorn uvicorn_app:app --reload --host 0.0.0.0 --port $$BACKEND_PORT) & BACK_PID=$$!; \
	  sleep 1; \
	  if ! kill -0 $$BACK_PID 2>/dev/null; then \
	    echo "[backend] failed to start (port $$BACKEND_PORT)"; \
	    wait $$BACK_PID; \
	    exit 1; \
	  fi; \
	  echo "[frontend] launching on port $$FRONTEND_PORT (API http://localhost:$$BACKEND_PORT)"; \
	  cd frontend && VITE_API_BASE="http://localhost:$$BACKEND_PORT" npm run dev -- --host 0.0.0.0 --port $$FRONTEND_PORT;'

test:
	cd backend && PYTHONPATH=app $(BACKEND_PYTHON_REL) -m pytest -q

lint:
	cd frontend && npm run lint

seed:
	cd backend && PYTHONPATH=. $(BACKEND_PYTHON_REL) scripts/seed.py

clean:
	rm -rf backend/__pycache__ backend/app/__pycache__ $(BACKEND_VENV) frontend/node_modules
