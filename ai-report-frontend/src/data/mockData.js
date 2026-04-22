export const navItems = [
  { id: "features", label: "Features" },
  { id: "workflow", label: "Workflow" },
  { id: "report-studio", label: "Report Studio" },
  { id: "chat", label: "Agent Chat" },
];

export const kpis = [
  { label: "Articles Tracked", value: "12K+" },
  { label: "Sources Monitored", value: "340+" },
  { label: "Summaries Generated", value: "9.1K" },
  { label: "Average Accuracy", value: "98.2%" },
];

export const featureCards = [
  {
    title: "Autonomous Planning",
    description:
      "Agent splits goals into tasks, selects tools, and retries intelligently before finalizing reports.",
    gradient: "purple",
  },
  {
    title: "MCP Tool Integration",
    description:
      "Plug web search, browser fetch, email, file writer, and database tools using one standard protocol.",
    gradient: "blue",
  },
  {
    title: "Grounded Answers",
    description:
      "Every chat response can include references and source links so users trust the generated insights.",
    gradient: "teal",
  },
  {
    title: "Human Review Ready",
    description:
      "Analysts can edit generated report sections and approve final reports before publishing.",
    gradient: "orange",
  },
];

export const workflowSteps = [
  "Collect current AI news from trusted sources",
  "Classify updates into releases, funding, policies, and products",
  "Generate section-wise summary with confidence score",
  "Create final report in markdown and dashboard format",
];

export const initialHighlights = [
  {
    type: "Model Release",
    title: "Compact multimodal model improves cost-efficiency",
    impact: "High",
    source: "Tech Wire",
  },
  {
    type: "Funding",
    title: "AI monitoring startup raises $42M Series B",
    impact: "Medium",
    source: "Venture Daily",
  },
  {
    type: "Policy",
    title: "New synthetic media transparency guidance published",
    impact: "Medium",
    source: "Policy Watch",
  },
];

export const starterMessages = [
  {
    role: "assistant",
    content:
      "Hi! Ask me for weekly AI highlights, competitor movement, or policy changes.",
  },
];

export const categoryChips = [
  "All Updates",
  "Model Launches",
  "Funding",
  "Policy",
  "Startups",
  "Enterprise AI",
  "Open Source",
  "Benchmarks",
];

export const showcaseCards = [
  {
    title: "Market Pulse",
    subtitle: "Track 24h movement",
    description: "Realtime feed of launches, M&A, pricing changes, and adoption signals.",
    tag: "Live",
  },
  {
    title: "Competitor Radar",
    subtitle: "Company-level alerts",
    description: "Monitor strategic moves across top labs and AI product companies.",
    tag: "Smart",
  },
  {
    title: "Exec Brief Builder",
    subtitle: "Board-ready output",
    description: "Generate concise weekly decks and summary briefs in one click.",
    tag: "Fast",
  },
];
