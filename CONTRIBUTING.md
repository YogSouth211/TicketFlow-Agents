# Development Notes

SupportPilot is a learning demo. Keep changes small and easy to explain:

- Keep each specialist agent's tools limited to its responsibility.
- Use parameterized SQL for database access.
- Keep API keys in .env; never commit secrets or the local SQLite database.
- Update README.md and docs/architecture.md when behavior or routing changes.
- Keep the upstream MIT license and attribution when redistributing this derivative.

Run locally with Python 3.12, install requirements.txt, then run python app.py.
