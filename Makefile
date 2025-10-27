SHELL := /bin/bash

.PHONY: bootstrap up down logs clean

bootstrap:
	./ops/scripts/bootstrap.sh

up:
	docker compose up -d

logs:
	docker compose logs -f

down:
	docker compose down

clean:
	docker compose down -v
