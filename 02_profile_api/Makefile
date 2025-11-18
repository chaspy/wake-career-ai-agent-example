ifneq (,$(wildcard ../.env))
include ../.env
export $(shell sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' ../.env)
endif

BACKEND_DIR=backend
FRONTEND_DIR=frontend

PHASE_BACKEND_PORT=28089
PHASE_FRONTEND_PORT=25073

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
	$(MAKE) backend &
	cd $(FRONTEND_DIR) && npm install && PORT=$(FRONTEND_PORT) npm run dev

backend:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

frontend:
	cd $(FRONTEND_DIR) && npm install && PORT=$(FRONTEND_PORT) npm run dev
