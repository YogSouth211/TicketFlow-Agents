"""Styles for the Chinese TicketFlow Agents operator workbench."""

CUSTOM_CSS = """
:root {
  --ink: #172c34;
  --muted: #687f85;
  --line: #dfe9e8;
  --teal: #087f78;
  --teal-deep: #076a67;
  --surface: #ffffff;
}

body, .gradio-container {
  background: #f3f7f6 !important;
  color: var(--ink) !important;
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", system-ui, sans-serif !important;
}
.gradio-container {
  max-width: 1320px !important;
  padding: 24px 28px 16px !important;
  margin: 0 auto !important;
}

/* Header */
.hero {
  position: relative;
  overflow: hidden;
  padding: 20px 32px 22px;
  margin-bottom: 18px;
  border-radius: 24px;
  color: #f4fffd;
  background: radial-gradient(circle at 84% 10%, rgba(96,208,185,.25), transparent 28%),
              linear-gradient(116deg, #12313e 0%, #15515a 57%, #087f78 100%);
  box-shadow: 0 16px 40px rgba(15,64,70,.13);
}
.hero::after {
  content: "";
  position: absolute;
  right: -48px;
  bottom: -115px;
  width: 290px;
  height: 290px;
  border: 1px solid rgba(237,255,249,.18);
  border-radius: 50%;
  box-shadow: 0 0 0 32px rgba(237,255,249,.04), 0 0 0 65px rgba(237,255,249,.025);
  pointer-events: none;
}
.hero-topline, .hero-body, .hero-flow, .trace-heading, .panel-heading,
.section-heading, .app-footer { display: flex; align-items: center; }
.hero-topline { gap: 10px; margin-bottom: 18px; }
.brand-mark {
  display: grid;
  place-items: center;
  width: 31px;
  height: 31px;
  border-radius: 10px;
  background: #c7f2e4;
  color: #0e4b4c;
  font-size: 17px;
  font-weight: 800;
}
.brand-name { color: #d0ece6; letter-spacing: 2px; font-size: 11px; font-weight: 750; }
.live-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  padding: 6px 11px;
  border: 1px solid rgba(223,255,248,.21);
  border-radius: 999px;
  background: rgba(255,255,255,.08);
  color: #e6f8f3;
  font-size: 11px;
}
.live-badge i { width: 7px; height: 7px; border-radius: 50%; background: #71e6ad; box-shadow: 0 0 0 4px rgba(113,230,173,.12); }
.hero-body { justify-content: space-between; gap: 28px; position: relative; z-index: 1; }
.hero-eyebrow { color: #a9d9d0; letter-spacing: 1.6px; font-size: 10px; font-weight: 750; }
.hero h1 { margin: 6px 0 7px; color: white; font-size: 29px; line-height: 1.35; }
.hero p { margin: 0; color: #d3e9e5; font-size: 13px; line-height: 1.75; }
.hero-flow { flex-wrap: wrap; justify-content: flex-end; gap: 9px; color: #e8faf5; white-space: nowrap; }
.hero-flow span { padding: 9px 10px; border: 1px solid rgba(235,255,251,.15); border-radius: 10px; background: rgba(255,255,255,.08); font-size: 11px; }
.hero .hero-flow span { color: #e8faf5 !important; }
.hero-flow b { color: #86d6c7; font-size: 14px; }

/* Navigation and page headings */
.workspace-tabs { background: transparent !important; }
.workspace-tabs .tab-nav {
  gap: 7px;
  padding: 5px !important;
  margin: 0 0 21px !important;
  border: 1px solid var(--line) !important;
  border-radius: 14px;
  background: white;
  width: fit-content;
}
.workspace-tabs .tab-nav button {
  min-height: 38px;
  padding: 7px 18px;
  border: 0 !important;
  border-radius: 10px !important;
  color: #60777d !important;
  background: transparent !important;
  font-size: 13px;
  font-weight: 650;
}
.workspace-tabs .tab-nav button.selected {
  color: #086e68 !important;
  background: #e8f6f2 !important;
  box-shadow: none !important;
}
.workspace-tabs button[role="tab"][aria-selected="true"] {
  color: #086e68 !important;
  background: #e8f6f2 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
.section-heading { justify-content: space-between; align-items: end; gap: 16px; margin: 2px 2px 20px; }
.section-kicker { color: var(--teal); font-size: 11px; font-weight: 750; letter-spacing: 1px; }
.section-heading h2 { margin: 5px 0 3px; color: var(--ink); font-size: 23px; line-height: 1.3; }
.section-heading p { margin: 0; color: var(--muted); font-size: 12px; }
.workspace-tag { padding: 7px 11px; border: 1px solid #d8eee7; border-radius: 999px; color: #498276; background: #eaf7f2; font-size: 11px; white-space: nowrap; }

/* Shared cards and metrics */
.metric-grid { display: grid; grid-template-columns: repeat(5,minmax(0,1fr)); gap: 11px; margin: 0 0 19px; }
.metric-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  min-height: 89px;
  padding: 14px 17px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: white;
  box-shadow: 0 5px 17px rgba(25,69,69,.035);
}
.metric-card strong { color: #164b4d; font-size: 25px; line-height: 1; }
.metric-card span { color: var(--muted); font-size: 11px; }
.workbench-grid, .chat-workspace { align-items: stretch !important; gap: 16px !important; }
.surface-panel {
  min-width: 0;
  padding: 20px !important;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--surface);
  box-shadow: 0 10px 30px rgba(31,67,75,.045);
}
.panel-heading { justify-content: space-between; gap: 12px; margin-bottom: 15px; }
.panel-heading strong { color: #1a3941; font-size: 16px; }
.panel-heading span { color: #8b9b9e; font-size: 11px; text-align: right; }
.panel-subheading { margin: 18px 0 7px; padding-top: 14px; border-top: 1px solid #eaf0ef; color: #35535a; font-size: 12px; font-weight: 700; }
.surface-panel button.primary { background: var(--teal) !important; border: 0 !important; color: white !important; }
.surface-panel button.primary:hover { background: var(--teal-deep) !important; }
.surface-panel textarea, .surface-panel input { border-color: #dce9e7 !important; border-radius: 10px !important; }
.surface-panel textarea:focus, .surface-panel input:focus { border-color: #6fbeaa !important; }
.filter-row { align-items: end !important; gap: 9px !important; margin-bottom: 9px !important; }
.filter-row button { min-height: 42px !important; }
.create-accordion { margin-top: 16px; border: 1px solid var(--line) !important; border-radius: 15px !important; background: white !important; }

/* Conversation */
.chat-panel {
  padding: 14px !important;
  border: 1px solid var(--line) !important;
  border-radius: 20px !important;
  background: white !important;
  box-shadow: 0 10px 30px rgba(31,67,75,.05) !important;
}
.chatbot-container { border: 0 !important; border-radius: 14px !important; background: #f8fbfa !important; }
.chatbot-container [data-testid="bot"] { border: 1px solid #e6eeec !important; border-radius: 15px !important; }
.chatbot-container [data-testid="user"] { border-radius: 15px !important; }
.status-bar { min-height: 33px; margin: 6px 0 8px; }
.status-pill {
  display: flex;
  align-items: center;
  min-height: 32px;
  padding: 6px 10px;
  border: 1px solid color-mix(in srgb, var(--status-color) 20%, white);
  border-radius: 9px;
  color: var(--status-color);
  background: color-mix(in srgb, var(--status-color) 7%, white);
  font-size: 11px;
}
.status-icon { margin-right: 7px; font-weight: 800; }
.composer-row { align-items: stretch !important; gap: 9px !important; }
.composer-row textarea { min-height: 48px !important; padding: 12px 13px !important; border: 1px solid #dce8e6 !important; border-radius: 12px !important; background: #fbfdfc !important; }
.composer-row textarea:focus { border-color: #6bb9a7 !important; box-shadow: 0 0 0 3px rgba(8,127,120,.08) !important; }
.composer-row button.primary { min-height: 48px; border: 0 !important; border-radius: 12px !important; background: linear-gradient(135deg,#138d81,#08766e) !important; color: white !important; }
.composer-row button.primary:hover { filter: brightness(1.05); }
.action-row { align-items: center !important; gap: 7px !important; margin-top: 7px !important; flex-wrap: wrap !important; }
.examples-label { margin-right: 2px; color: #83969a; font-size: 11px; white-space: nowrap; }
.action-row button { min-height: 31px !important; padding: 4px 10px !important; border: 1px solid #e1ebe8 !important; border-radius: 999px !important; color: #557177 !important; background: #f9fcfb !important; font-size: 11px !important; }
.action-row button:hover { border-color: #a9d9cc !important; color: var(--teal) !important; background: #f0faf6 !important; }
.trace-panel {
  min-width: 0;
  padding: 18px !important;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: white;
  box-shadow: 0 10px 30px rgba(31,67,75,.045);
}
.trace-heading { gap: 11px; padding-bottom: 14px; margin-bottom: 13px; border-bottom: 1px solid #e9f0ee; }
.trace-symbol { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; color: var(--teal); background: #e7f6f1; font-size: 21px; }
.trace-heading strong, .trace-heading small { display: block; }
.trace-heading strong { color: #24444a; font-size: 14px; }
.trace-heading small { margin-top: 2px; color: #8a9b9f; font-size: 10px; }
.trace-panel .prose { color: #466069; font-size: 12px; }
.agent-legend { margin-top: 22px; padding: 12px 13px; border: 1px solid #e7f0ed; border-radius: 11px; background: #f8fbfa; }
.agent-legend span { display: block; margin-bottom: 5px; color: #7c9195; font-size: 10px; }
.agent-legend div { color: #416f6d; font-size: 11px; line-height: 1.8; }

.app-footer { justify-content: space-between; gap: 12px; margin-top: 21px; padding: 15px 3px 4px; border-top: 1px solid #e2ebe9; color: #8b9b9f; font-size: 11px; }
.app-footer span:first-child { color: #5c7778; font-weight: 700; }

@media (max-width: 1000px) {
  .hero-flow { display: none; }
  .chat-workspace, .workbench-grid { flex-direction: column !important; }
  .chat-workspace > .column, .workbench-grid > .column { width: 100% !important; }
  .metric-grid { grid-template-columns: repeat(3,minmax(0,1fr)); }
}
@media (max-width: 1500px) {
  .workbench-grid { flex-direction: column !important; }
  .workbench-grid > .column { width: 100% !important; }
}
@media (max-width: 700px) {
  .gradio-container { padding: 12px 12px 16px !important; }
  .hero { padding: 21px 19px 23px; border-radius: 18px; }
  .hero-topline { margin-bottom: 17px; }
  .hero h1 { font-size: 22px; }
  .hero p { font-size: 12px; }
  .workspace-tabs .tab-nav { width: 100%; }
  .workspace-tabs .tab-nav button { flex: 1; padding: 7px 8px; font-size: 12px; }
  .section-heading { align-items: start; }
  .section-heading h2 { font-size: 20px; }
  .section-heading p { max-width: 270px; line-height: 1.55; }
  .workspace-tag { display: none; }
  .metric-grid { grid-template-columns: repeat(2,minmax(0,1fr)); gap: 8px; }
  .metric-card { min-height: 75px; padding: 11px 13px; }
  .metric-card strong { font-size: 22px; }
  .surface-panel { padding: 13px !important; border-radius: 15px; }
  .panel-heading { align-items: start; flex-direction: column; gap: 4px; }
  .panel-heading span { text-align: left; }
  .chat-panel { padding: 9px !important; }
  .composer-row { flex-wrap: wrap !important; }
  .composer-row button { width: 100%; }
  .examples-label { width: 100%; }
  .trace-panel { padding: 14px !important; }
  .app-footer { align-items: start; flex-direction: column; gap: 5px; }
}
"""
