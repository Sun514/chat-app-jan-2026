// Workflow registry — single source of truth for @mentions and tool calls.
//
// Each workflow exposes:
//   - id, label, description       → used by the @ autocomplete menu
//   - tool                         → OpenAI-format function schema sent to the LLM
//   - run({ args, router })        → called when the LLM invokes the tool;
//                                    returns { summary, data } for follow-up turn
//                                    OR returns { route: "/path" } to navigate

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function apiGet(path) {
  const res = await fetch(`${apiBase}${path}`);
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json();
}

export const workflows = [
  {
    id: "search-documents",
    label: "search",
    description: "Semantic search across uploaded documents",
    tool: {
      type: "function",
      function: {
        name: "search_documents",
        description:
          "Search the document library by meaning. Use when the user asks " +
          "about content that may live in uploaded documents.",
        parameters: {
          type: "object",
          properties: {
            query: { type: "string", description: "Natural-language query" },
            limit: { type: "integer", default: 5, minimum: 1, maximum: 20 },
          },
          required: ["query"],
        },
      },
    },
    async run({ args }) {
      const limit = args.limit ?? 5;
      const data = await apiGet(
        `/documents/search?q=${encodeURIComponent(args.query)}&limit=${limit}`,
      );
      const summary = data.results?.length
        ? data.results
            .map(
              (r, i) =>
                `[${i + 1}] ${r.filename}` +
                (r.page_number ? ` p.${r.page_number}` : "") +
                ` (sim ${r.similarity.toFixed(2)})\n${r.content.slice(0, 400)}`,
            )
            .join("\n\n")
        : "No matching chunks.";
      return { summary, data, view: "search" };
    },
  },
  {
    id: "audit-summary",
    label: "audit",
    description: "Pull current audit / usage metrics",
    tool: {
      type: "function",
      function: {
        name: "get_audit_summary",
        description:
          "Fetch the current audit metrics: users, model usage, module " +
          "traffic, token rates. Use when the user asks about app " +
          "analytics, usage, or 'what's our top model'.",
        parameters: { type: "object", properties: {} },
      },
    },
    async run() {
      const data = await apiGet(`/audit/summary`);
      const summary =
        `Users: ${data.users.total_users} total, ${data.users.active_users_30d} active (30d)\n` +
        `Top model: ${data.most_used_llm.model} (${data.most_used_llm.usage_percent}%)\n` +
        `Top module: ${data.most_used_module.module} (${data.most_used_module.usage_percent}%)\n` +
        `Avg tokens: ${data.tokens_per_request.avg_tokens_in} in / ${data.tokens_per_request.avg_tokens_out} out`;
      return { summary, data, view: "metrics" };
    },
  },
  {
    id: "list-documents",
    label: "documents",
    description: "List uploaded documents",
    tool: {
      type: "function",
      function: {
        name: "list_documents",
        description: "List documents in the library. Returns filenames and IDs.",
        parameters: {
          type: "object",
          properties: {
            limit: { type: "integer", default: 20, minimum: 1, maximum: 100 },
          },
        },
      },
    },
    async run({ args }) {
      const limit = args.limit ?? 20;
      const data = await apiGet(`/documents/?limit=${limit}`);
      const summary = data.length
        ? data
            .map(
              (d) =>
                `- ${d.filename} (${d.file_type}, ${(d.file_size / 1024).toFixed(1)}kB)`,
            )
            .join("\n")
        : "No documents uploaded.";
      return { summary, data, view: "json" };
    },
  },
  {
    id: "media-split",
    label: "split-media",
    description: "Open the media splitter (requires file upload)",
    tool: {
      type: "function",
      function: {
        name: "open_media_splitter",
        description:
          "Open the media splitter UI. Use when the user wants to split " +
          "an audio or video file — the actual file upload happens in the UI.",
        parameters: { type: "object", properties: {} },
      },
    },
    async run({ router }) {
      router.push("/media");
      return { summary: "Opened the Media Splitter page.", data: null };
    },
  },
  {
    id: "investigations",
    label: "investigations",
    description: "Open the investigations hub",
    tool: {
      type: "function",
      function: {
        name: "open_investigations",
        description:
          "Navigate to the investigations hub. Use when the user wants to " +
          "see, browse, or manage investigations.",
        parameters: { type: "object", properties: {} },
      },
    },
    async run({ router }) {
      router.push("/investigations");
      return { summary: "Opened the Investigations hub.", data: null };
    },
  },
];

// Lookup by tool function name (used by the dispatcher).
const byToolName = new Map(workflows.map((w) => [w.tool.function.name, w]));

export function getToolSchemas() {
  return workflows.map((w) => w.tool);
}

export async function dispatchTool(name, args, ctx) {
  const wf = byToolName.get(name);
  if (!wf) {
    return { summary: `Unknown tool: ${name}`, data: null };
  }
  try {
    return await wf.run({ args, ...ctx });
  } catch (err) {
    return { summary: `Tool ${name} failed: ${err.message}`, data: null };
  }
}

export function filterWorkflows(query) {
  const q = query.toLowerCase();
  if (!q) return workflows;
  return workflows.filter(
    (w) =>
      w.label.toLowerCase().includes(q) ||
      w.description.toLowerCase().includes(q),
  );
}
