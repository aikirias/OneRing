SHELL := /bin/bash

EMPTY :=
SPACE := $(EMPTY) $(EMPTY)
COMMA := ,

PROFILES ?= core
PROFILE_NORMALIZED := $(subst $(COMMA),$(SPACE),$(strip $(PROFILES)))
PROFILE_LIST := $(strip $(PROFILE_NORMALIZED))
PROFILE_FLAGS := $(foreach profile,$(PROFILE_LIST),--profile $(profile))
PROFILE_ARGS := $(subst $(SPACE),$(COMMA),$(PROFILE_LIST))

SKIP_PULL ?= false
BOOTSTRAP_SKIP := $(if $(filter true,$(SKIP_PULL)),--skip-pull,)

.PHONY: bootstrap up down logs clean up-core up-ingestion up-catalog up-ml up-observability up-analytics up-all

bootstrap:
	./ops/scripts/bootstrap.sh $(BOOTSTRAP_SKIP) --profiles $(PROFILE_ARGS)

up:
	docker compose $(PROFILE_FLAGS) up -d

logs:
	docker compose $(PROFILE_FLAGS) logs -f

down:
	docker compose $(PROFILE_FLAGS) down

clean:
	docker compose down -v

up-core:
	$(MAKE) up PROFILES="core"

up-ingestion:
	$(MAKE) up PROFILES="core ingestion"

up-catalog:
	$(MAKE) up PROFILES="core catalog"

up-ml:
	$(MAKE) up PROFILES="core ml"

up-observability:
	$(MAKE) up PROFILES="core observability"

up-analytics:
	$(MAKE) up PROFILES="analytics"

up-all:
	$(MAKE) up PROFILES="core ingestion catalog ml observability"
