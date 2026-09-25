# Hoppscotch Public Docs MCP

A read-only MCP server for [published Hoppscotch API documentation](https://docs.hoppscotch.io/documentation/features/documentation). Search requests, inspect endpoint details, and read saved response examples. It uses Hoppscotch's public documentation endpoint; no Hoppscotch account or token is required.

## Install

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/). From a checkout:

```bash
uv tool install .
hoppscotch-public-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

Replace `YOUR_DOC_ID` with the ID in your published Hoppscotch URL. The check prints its title and endpoint count. Install directly from GitHub:

```bash
uv tool install git+https://github.com/KidiXDev/hoppscotch-public-docs-mcp.git
```

If the command is not found after installation, run `uv tool update-shell`, reopen your terminal, or use the executable's absolute path in your MCP client.

## Configure a document

Set `HOPPSCOTCH_DOC_URL` to a published `/view/<slug>` URL, optionally ending in a version. Every tool also accepts `doc_url` to use a different document for one call. Without either, the tool returns a clear error. This keeps the server usable with multiple public documents rather than a built-in sample.

| Variable | Purpose | Default |
| --- | --- | --- |
| `HOPPSCOTCH_DOC_URL` | Default published document | None |
| `HOPPSCOTCH_DOCS_ORIGIN` | Allowed public viewer origin | `https://api-docs.hoppscotch.io` |
| `HOPPSCOTCH_API_BASE_URL` | Backend base URL for compatible self-hosted deployments | `https://api.hoppscotch.io/v1` |

For a self-hosted deployment using the same `/v1/published-docs` route, set both origin variables to that deployment's viewer origin and backend `/v1` URL. Per-call `doc_url` values must match the configured viewer origin.

## MCP tools

| Tool | What it returns |
| --- | --- |
| `get_document(doc_url="")` | Title, version, folder names, environment variable names, and endpoint count |
| `search_documentation(query, doc_url="", offset=0, limit=10)` | Ranked, short endpoint summaries for API concepts in a task; up to 50 per page |
| `list_endpoints(query="", doc_url="", offset=0, limit=50)` | Exact text matches by folder, name, method, URL, or description; up to 100 per page |
| `get_endpoint(request_id, doc_url="", response_name="")` | Request details and available response names; the named saved response when requested |

For a broad coding task, the agent can search focused concepts such as `product` and `tenant` with `search_documentation`. It returns brief summaries, IDs, `total`, and `next_offset` so the agent can page through all matches without loading the entire document into context. The search uses keyword ranking, not semantic understanding. The agent should then call `get_endpoint` only for relevant IDs. To read a sample response, pass one of its `response_names` as `response_name`.

Example agent instruction: “Build a product page. Search the Hoppscotch docs for product and tenant endpoints, page through all matches, inspect the routes and response examples needed for the page, and use those API details in the implementation.” The MCP reads published documentation; it does not fetch live product or tenant records.

The server omits saved auth values and redacts credential-like header and parameter values. Descriptions and request and response bodies are returned as published, so review the source document before sharing its contents.

## MCP client setup

Install the command above first. Replace the example URL with your published document URL. The command starts a **stdio** server, so it normally prints nothing in a terminal; your MCP client launches it and exchanges protocol messages over stdin/stdout.

### Codex

Add this to `~/.codex/config.toml` (or a project `.codex/config.toml`):

```toml
[mcp_servers.hoppscotch_docs]
command = "hoppscotch-public-docs-mcp"

[mcp_servers.hoppscotch_docs.env]
HOPPSCOTCH_DOC_URL = "https://api-docs.hoppscotch.io/view/YOUR_DOC_ID"
```

Run `codex mcp list` to verify it. See the [Codex MCP guide](https://developers.openai.com/codex/mcp).

### Claude Code

```bash
claude mcp add --scope user --env HOPPSCOTCH_DOC_URL=https://api-docs.hoppscotch.io/view/YOUR_DOC_ID --transport stdio hoppscotch-docs -- hoppscotch-public-docs-mcp
claude mcp get hoppscotch-docs
```

See the [Claude Code MCP guide](https://code.claude.com/docs/en/mcp).

For **Claude Desktop**, edit `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows, then fully restart the app:

```json
{
  "mcpServers": {
    "hoppscotch-docs": {
      "command": "hoppscotch-public-docs-mcp",
      "env": {
        "HOPPSCOTCH_DOC_URL": "https://api-docs.hoppscotch.io/view/YOUR_DOC_ID"
      }
    }
  }
}
```

Use the command's absolute path if Claude Desktop cannot find it. See the [MCP Python SDK host guide](https://py.sdk.modelcontextprotocol.io/v2/get-started/real-host/).

### Google Antigravity

In the IDE, open **MCP Servers → Manage MCP Servers → View raw config**. In Antigravity CLI, edit `~/.gemini/config/mcp_config.json` (or `.agents/mcp_config.json` in a workspace):

```json
{
  "mcpServers": {
    "hoppscotch-docs": {
      "command": "hoppscotch-public-docs-mcp",
      "env": {
        "HOPPSCOTCH_DOC_URL": "https://api-docs.hoppscotch.io/view/YOUR_DOC_ID"
      }
    }
  }
}
```

See the [Antigravity MCP guide](https://antigravity.google/docs/mcp).

### GitHub Copilot

For Copilot in VS Code, create `.vscode/mcp.json` in your project (or use **MCP: Open User Configuration**):

```json
{
  "servers": {
    "hoppscotch-docs": {
      "type": "stdio",
      "command": "hoppscotch-public-docs-mcp",
      "env": {
        "HOPPSCOTCH_DOC_URL": "https://api-docs.hoppscotch.io/view/YOUR_DOC_ID"
      }
    }
  }
}
```

Use Copilot Chat **Agent** mode and enable the server in its tools picker. For Copilot CLI:

```bash
copilot mcp add hoppscotch-docs --env HOPPSCOTCH_DOC_URL=https://api-docs.hoppscotch.io/view/YOUR_DOC_ID -- hoppscotch-public-docs-mcp
copilot mcp get hoppscotch-docs
```

The CLI also accepts a portable `~/.copilot/mcp-config.json` with a top-level `mcpServers` object; VS Code's `.vscode/mcp.json` uses `servers`. See [VS Code's MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) and the [Copilot CLI MCP guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers).

## Docker

Build locally:

```bash
docker build -t hoppscotch-public-docs-mcp .
```

Check a public document:

```bash
docker run --rm hoppscotch-public-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

For an MCP client's **stdio** configuration, use command `docker` and args `run`, `--rm`, `-i`, `-e`, `HOPPSCOTCH_DOC_URL=YOUR_URL`, `hoppscotch-public-docs-mcp`. Keep `-i` and do not detach the container.

To run an HTTP server locally instead:

```bash
docker run --rm -p 127.0.0.1:8000:8000 hoppscotch-public-docs-mcp --http --host 0.0.0.0
```

Connect a Streamable HTTP MCP client to `http://127.0.0.1:8000/mcp`. Pass `doc_url` to tools or add `-e HOPPSCOTCH_DOC_URL=YOUR_URL` to the Docker command. For a local Python process, use `hoppscotch-public-docs-mcp --http` instead.

## Develop

```bash
uv run python -m unittest -v
uv run hoppscotch-public-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

This project is licensed under [MIT](LICENSE).
