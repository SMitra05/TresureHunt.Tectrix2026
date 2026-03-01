.PHONY: migrate backend frontend

migrate:
	python3 backend/migrate.py

backend:
	python3 backend/app.py

frontend:
	python3 -m http.server 5173 --directory frontend
