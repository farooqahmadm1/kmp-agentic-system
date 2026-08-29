.PHONY: help install test health init tui run docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install python dependencies from requirements.txt"
	@echo "  make test        - Run automated test suite"
	@echo "  make health      - Run pre-flight health check (Ollama & Cloud)"
	@echo "  make init        - Scaffold a fresh Kotlin Multiplatform project"
	@echo "  make tui         - Launch interactive Textual TUI dashboard"
	@echo "  make docker-up   - Launch multi-agent orchestrator & Ollama in Docker"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean       - Remove cache and temporary test files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	python3 -m unittest discover tests

health:
	python3 cli.py health

init:
	python3 cli.py init --name ComposeApp --package com.example.kmp

tui:
	python3 cli.py tui

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .test_scaffold_workspace/
