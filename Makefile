# Docker shortcuts (README → Docker). Needs Docker with the compose plugin.
# Recipes avoid shell syntax, so they run the same from PowerShell (cmd) and Git Bash (sh).
.PHONY: build web down

# Build the image: PyTorch, both models and the KB index go into it (slow the first time).
build:
	docker compose build

# Start the web app in the background and wait until it answers.
web:
ifeq (,$(wildcard .env))
	$(error Missing .env: copy .env.example to .env and set ANTHROPIC_API_KEY)
endif
	docker compose up -d --wait
	@echo Klimabot runs on http://127.0.0.1:7860 - and on https://KLIMABOT_DOMAIN with COMPOSE_PROFILES=https - logs: docker compose logs -f

# Stop it: open conversations are ended and their leads e-mailed first. The data volume stays.
down:
	docker compose down
