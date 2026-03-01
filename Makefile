.PHONY: migrate backend frontend test

migrate:
	python3 backend/migrate.py

backend:
	python3 backend/app.py

frontend:
	python3 -m http.server 5173 --directory frontend

test:
	python3 -m unittest tests/test_api.py
