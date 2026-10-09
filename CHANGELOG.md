# Changelog

## Unreleased

### Changed

- Reworked the demo into TicketFlow Agents — a SaaS customer support multi-agent workbench (GitHub repository name: SupportPilot).
- Replaced the music and invoice flows with product knowledge, incident triage, and support-ticket agents.
- Added a Gradio workbench for ticket lifecycle and knowledge management backed by SQLite.
- Configured Alibaba Cloud Qwen through its OpenAI-compatible endpoint.
- Preserved the upstream MIT license and added clear source attribution in README.md.
- Show execution history by user request, with specialist and tool names preserved across handoffs and later turns.
- Accept Gradio text-block chat messages and ignore replayed LangGraph history when collecting current-turn tool calls.
- Isolate automated database checks from the local demonstration database.
