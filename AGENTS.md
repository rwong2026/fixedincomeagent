# Antigravity Project Instructions

## graphify Codebase Intelligence
This project uses graphify to maintain a persistent knowledge graph of the codebase architecture, modules, and dataflows in `graphify-out/`.

- **Architecture Questions:** Before answering questions about codebase structure, dependencies, execution flow, or file relationships, check `graphify-out/graph.json` or use the `/graphify query` skill.
- **Incremental Updates:** When code files are modified, added, or refactored, run `/graphify --update` (or rely on the installed git post-commit hook) to keep the graph and `GRAPH_REPORT.md` synchronized.
- **Key Artifacts:**
  - `graphify-out/graph.html`: Interactive graph visualization.
  - `graphify-out/GRAPH_REPORT.md`: Audit report with god nodes, community clusters, and insights.
  - `graphify-out/graph.json`: Complete graph data (nodes, edges, hyperedges).
