ifneq (,$(wildcard ../.env))
include ../.env
export $(shell sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' ../.env)
endif

BACKEND_DIR=backend
FRONTEND_DIR=frontend

# フェーズ固有のデフォルトポート
PHASE_BACKEND_PORT=18089
PHASE_FRONTEND_PORT=15073

# ルート .env に BACKEND_PORT / FRONTEND_PORT があっても、
# 明示的なコマンドライン指定が無い限りフェーズ既定値を優先する
ifeq ($(origin BACKEND_PORT),command line)
BACKEND_PORT:=$(BACKEND_PORT)
else
BACKEND_PORT:=$(PHASE_BACKEND_PORT)
endif

ifeq ($(origin FRONTEND_PORT),command line)
FRONTEND_PORT:=$(FRONTEND_PORT)
else
FRONTEND_PORT:=$(PHASE_FRONTEND_PORT)
endif

.PHONY: dev backend frontend

dev:
	@echo "Starting dev servers... (BACKEND_PORT=$(BACKEND_PORT), FRONTEND_PORT=$(FRONTEND_PORT))"
	@BACKEND_PORT=$(BACKEND_PORT) FRONTEND_PORT=$(FRONTEND_PORT) bash -c 'set -euo pipefail; trap "kill 0" EXIT; \
	  echo "[backend] launching on port $$BACKEND_PORT"; \
	  (cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $$BACKEND_PORT) & BACK_PID=$$!; \
	  sleep 1; \
	  if ! kill -0 $$BACK_PID 2>/dev/null; then echo "[backend] failed to start (port $$BACKEND_PORT)"; wait $$BACK_PID; exit 1; fi; \
	  echo "[frontend] launching on port $$FRONTEND_PORT => http://localhost:$$FRONTEND_PORT"; \
	  cd $(FRONTEND_DIR) && npm install && PORT=$$FRONTEND_PORT npm run dev -- --host 0.0.0.0 --port $$FRONTEND_PORT;'

backend:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

frontend:
	cd $(FRONTEND_DIR) && npm install && PORT=$(FRONTEND_PORT) npm run dev
