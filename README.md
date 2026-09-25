# Hoppscotch Public Docs MCP

A read-only MCP server for [published Hoppscotch API documentation](https://docs.hoppscotch.io/documentation/features/documentation). Search requests, inspect endpoint details, and read saved response examples. It uses Hoppscotch's public documentation endpoint; no Hoppscotch account or token is required.

## Installation

### For Agents

Copy one of these prompts and paste it into your MCP-capable AI agent.

#### Using uv

```text
Install the Hoppscotch Public Docs MCP server for this AI client from https://github.com/KidiXDev/hoppscotch-public-docs-mcp.

Follow the repository README and install it using uv. Install uv first if needed.

Configure this client to run:
hoppscotch-public-docs-mcp

Do not set a default Hoppscotch document URL. I will give you a published URL for each project; pass it as doc_url on every tool call.

Verify that the server exposes get_document, search_documentation, list_endpoints, and get_endpoint.

Tell me what you configured and whether I need to restart the client.
```

#### Using Docker

```text
Install the Hoppscotch Public Docs MCP server for this AI client from https://github.com/KidiXDev/hoppscotch-public-docs-mcp.

Use the prebuilt Docker image:
ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest

Configure this client to run the MCP server over stdio using:
docker run --rm -i ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest

Do not set a default Hoppscotch document URL. I will give you a published URL for each project; pass it as doc_url on every tool call.

Verify that the server exposes get_document, search_documentation, list_endpoints, and get_endpoint.

Tell me what you configured and whether I need to restart the client.
```

### For Humans

#### Using uv

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

Install directly from GitHub:

```bash
uv tool install git+https://github.com/KidiXDev/hoppscotch-public-docs-mcp.git
```

Or install from a checkout:

```bash
uv tool install .
```

Then [configure your MCP client](#manual-mcp-client-setup).

To check a published document:

```bash
hoppscotch-public-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

If the command is not found after installation, run `uv tool update-shell`, reopen your terminal, or use the executable's absolute path in your MCP client.

#### Using Docker

Pull the prebuilt image:

```bash
docker pull ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest
```

Check a published document:

```bash
docker run --rm \
  ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest \
  --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

For an MCP client's stdio configuration, use:

```bash
docker run --rm -i ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest
```

Keep `-i` and do not detach the container.

## Choose a document per call

Start the server without a document URL. Pass the project's published `/view/<slug>` URL as `doc_url` on each tool call, optionally ending in a version.

For example:

```text
search_documentation(
  query="tenant",
  doc_url="https://api-docs.hoppscotch.io/view/YOUR_DOC_ID"
)
```

Include the relevant URL in your request to the agent so it can pass the right URL for each project.

Without a document URL, a tool call returns an error.

For compatible self-hosted deployments, these optional settings change where the server reads published docs:

| Variable                  | Purpose                                                 | Default                          |
| ------------------------- | ------------------------------------------------------- | -------------------------------- |
| `HOPPSCOTCH_DOCS_ORIGIN`  | Allowed public viewer origin                            | `https://api-docs.hoppscotch.io` |
| `HOPPSCOTCH_API_BASE_URL` | Backend base URL for compatible self-hosted deployments | `https://api.hoppscotch.io/v1`   |

For a self-hosted deployment using the same `/v1/published-docs` route, set both values to that deployment's viewer origin and backend `/v1` URL.

Per-call `doc_url` values must match the configured viewer origin.

## MCP tools

| Tool                                                          | What it returns                                                                       |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `get_document(doc_url="")`                                    | Title, version, folder names, environment variable names, and endpoint count          |
| `search_documentation(query, doc_url="", offset=0, limit=10)` | Ranked, short endpoint summaries for API concepts in a task; up to 50 per page        |
| `list_endpoints(query="", doc_url="", offset=0, limit=50)`    | Exact text matches by folder, name, method, URL, or description; up to 100 per page   |
| `get_endpoint(request_id, doc_url="", response_name="")`      | Request details and available response names; the named saved response when requested |

## Manual MCP client setup

These configurations start a **stdio** server without selecting a project.

Give your agent the published URL for the project you are working on; it passes that URL as `doc_url` when calling tools.

The server normally prints nothing in a terminal because it exchanges protocol messages over stdin/stdout.

The examples below use the `uv` installation.

If you use Docker, replace the executable with:

```json
{
  "command": "docker",
  "args": [
    "run",
    "--rm",
    "-i",
    "ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest"
  ]
}
```

### Codex

Add this to `~/.codex/config.toml` or a project `.codex/config.toml`:

```toml
[mcp_servers.hoppscotch_docs]
command = "hoppscotch-public-docs-mcp"
```

Run:

```bash
codex mcp list
```

See the [Codex MCP guide](https://developers.openai.com/codex/mcp).

### Claude Code

```bash
claude mcp add --scope user --transport stdio hoppscotch-docs -- hoppscotch-public-docs-mcp
claude mcp get hoppscotch-docs
```

See the [Claude Code MCP guide](https://code.claude.com/docs/en/mcp).

For **Claude Desktop**, edit `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows, then fully restart the app:

```json
{
  "mcpServers": {
    "hoppscotch-docs": {
      "command": "hoppscotch-public-docs-mcp"
    }
  }
}
```

Use the command's absolute path if Claude Desktop cannot find it.

See the [MCP Python SDK host guide](https://py.sdk.modelcontextprotocol.io/v2/get-started/real-host/).

### Google Antigravity

In the IDE, open:

```text
MCP Servers → Manage MCP Servers → View raw config
```

In Antigravity CLI, edit `~/.gemini/config/mcp_config.json` or `.agents/mcp_config.json` in a workspace:

```json
{
  "mcpServers": {
    "hoppscotch-docs": {
      "command": "hoppscotch-public-docs-mcp"
    }
  }
}
```

See the [Antigravity MCP guide](https://antigravity.google/docs/mcp).

### GitHub Copilot

For Copilot in VS Code, create `.vscode/mcp.json` in your project or use **MCP: Open User Configuration**:

```json
{
  "servers": {
    "hoppscotch-docs": {
      "type": "stdio",
      "command": "hoppscotch-public-docs-mcp"
    }
  }
}
```

Use Copilot Chat **Agent** mode and enable the server in its tools picker.

For Copilot CLI:

```bash
copilot mcp add hoppscotch-docs -- hoppscotch-public-docs-mcp
copilot mcp get hoppscotch-docs
```

The CLI also accepts a portable `~/.copilot/mcp-config.json` with a top-level `mcpServers` object. VS Code's `.vscode/mcp.json` uses `servers`.

See [VS Code's MCP configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) and the [Copilot CLI MCP guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers).

## HTTP transport

To run an HTTP server locally with Docker:

```bash
docker run --rm \
  -p 127.0.0.1:8000:8000 \
  ghcr.io/kidixdev/hoppscotch-public-docs-mcp:latest \
  --http \
  --host 0.0.0.0
```

Connect a Streamable HTTP MCP client to:

```text
http://127.0.0.1:8000/mcp
```

Pass `doc_url` to each tool call.

For a local Python process:

```bash
hoppscotch-public-docs-mcp --http
```

## Develop

```bash
uv run python -m unittest -v
uv run hoppscotch-public-docs-mcp --check https://api-docs.hoppscotch.io/view/YOUR_DOC_ID
```

Build the Docker image locally:

```bash
docker build -t hoppscotch-public-docs-mcp .
```

## License

This project is licensed under [MIT](LICENSE).
