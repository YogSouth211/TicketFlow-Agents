# Security Scope

SupportPilot is a local learning demo, not a production support service.

- The sample account IDs are public demo values and do not authenticate users.
- Do not connect this demo to real customer data.
- Keep API keys in an untracked .env file.
- Ticket tools use parameterized SQL and validate the account, issue length, priority, and ticket ID.
- The local database is ignored by Git and should contain only sample data.

Before production use, add real authentication and authorization, tenant isolation, rate limits, audit logging, and a persistent secret-management solution.
