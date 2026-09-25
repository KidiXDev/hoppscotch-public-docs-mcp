"""Read published Hoppscotch API documentation over MCP stdio."""

import argparse
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


DEFAULT_DOCS_ORIGIN = "https://api-docs.hoppscotch.io"
DEFAULT_API_BASE = "https://api.hoppscotch.io/v1"
SLUG = re.compile(r"[A-Za-z0-9_-]+\Z")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SECRET = re.compile(r"authorization|cookie|password|secret|token|api[-_]?key", re.I)
QUERY_STOPWORDS = {
    "a", "all", "an", "and", "api", "build", "complete", "create", "data",
    "display", "endpoint", "endpoints", "for", "from", "get", "make", "need",
    "page", "show", "the", "to", "use", "using", "with",
}

mcp = MCPServer("Hoppscotch Public Docs")


def _api_url(doc_url: str) -> str:
    source = doc_url or os.getenv("HOPPSCOTCH_DOC_URL")
    if not source:
        raise ToolError("Pass doc_url or set HOPPSCOTCH_DOC_URL to a published Hoppscotch URL")
    url = urlsplit(source)
    docs_origin = urlsplit(os.getenv("HOPPSCOTCH_DOCS_ORIGIN", DEFAULT_DOCS_ORIGIN))
    if docs_origin.scheme not in ("http", "https") or not docs_origin.netloc or docs_origin.path not in ("", "/"):
        raise ToolError("HOPPSCOTCH_DOCS_ORIGIN must be an HTTP(S) origin without a path")
    parts = url.path.strip("/").split("/")
    if (
        url.scheme != docs_origin.scheme
        or url.netloc != docs_origin.netloc
        or url.query
        or url.fragment
        or len(parts) not in (2, 3)
        or parts[0] != "view"
        or not SLUG.fullmatch(parts[1])
        or (len(parts) == 3 and not VERSION.fullmatch(parts[2]))
    ):
        raise ToolError(f"Expected a public URL on {docs_origin.scheme}://{docs_origin.netloc}/view/<slug>[/<version>]")
    api_base = os.getenv("HOPPSCOTCH_API_BASE_URL", DEFAULT_API_BASE).rstrip("/")
    api_url = urlsplit(api_base)
    if api_url.scheme not in ("http", "https") or not api_url.netloc or api_url.query or api_url.fragment:
        raise ToolError("HOPPSCOTCH_API_BASE_URL must be an HTTP(S) URL without a query or fragment")
    return f"{api_base}/published-docs/{'/'.join(parts[1:])}"


def _load(doc_url: str) -> tuple[dict, dict]:
    request = Request(_api_url(doc_url), headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:
            doc = json.load(response)
    except HTTPError as exc:
        raise ToolError(f"Hoppscotch returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise ToolError(f"Could not reach Hoppscotch: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ToolError("Hoppscotch returned invalid JSON") from exc
    try:
        tree = doc["documentTree"]
        return doc, json.loads(tree) if isinstance(tree, str) else tree
    except (KeyError, ValueError, TypeError) as exc:
        raise ToolError("Hoppscotch returned an invalid published document") from exc


def _requests(node: dict, folder: str = ""):
    for request in node.get("requests", []):
        yield folder, request
    for child in node.get("folders", []):
        yield from _requests(child, f"{folder}/{child['name']}".strip("/"))


def _safe_rows(rows: list[dict]) -> list[dict]:
    return [
        {**row, **{field: "[redacted]" for field in ("value", "initialValue", "currentValue") if field in row}}
        if row.get("secret") or SECRET.search(str(row.get("key") or "")) else row
        for row in rows
    ]


def _short(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


@mcp.tool()
def get_document(doc_url: str = "") -> dict:
    """Get a published document's title, versions, folders, variables, and endpoint count."""
    doc, tree = _load(doc_url)
    variables = doc.get("environmentVariables") or "[]"
    variables = (json.loads(variables) if isinstance(variables, str) else variables) or []
    return {
        "title": doc["title"], "url": doc.get("url"), "version": doc["version"],
        "versions": [item["version"] for item in doc.get("versions", [])],
        "folders": [item["name"] for item in tree.get("folders", [])],
        "variables": [item["key"] for item in variables],
        "endpoint_count": sum(1 for _ in _requests(tree)),
    }


@mcp.tool()
def list_endpoints(query: str = "", doc_url: str = "", offset: int = 0, limit: int = 50) -> dict:
    """List endpoints using an exact text fragment, or list all with query="". Paginate for all results."""
    if offset < 0 or not 1 <= limit <= 100:
        raise ToolError("offset must be nonnegative and limit must be between 1 and 100")
    doc, tree = _load(doc_url)
    needle = query.casefold()
    matches = [
        {"id": item["id"], "folder": folder, "name": item["name"],
         "method": item["method"], "endpoint": item["endpoint"]}
        for folder, item in _requests(tree)
        if needle in " ".join(str(v) for v in
            (folder, item.get("name"), item.get("method"), item.get("endpoint"), item.get("description"))).casefold()
    ]
    return {"title": doc["title"], "url": doc.get("url"), "version": doc["version"],
            "total": len(matches), "offset": offset, "endpoints": matches[offset:offset + limit]}


@mcp.tool()
def search_documentation(query: str, doc_url: str = "", offset: int = 0, limit: int = 10) -> dict:
    """Start here for broad tasks: rank endpoints by API concepts in a phrase. Returns short summaries and IDs, not full docs. Search focused concepts (e.g. tenant), paginate when the user asks for all, then use get_endpoint for needed routes. This reads documentation, not live API data."""
    if offset < 0 or not 1 <= limit <= 50:
        raise ToolError("offset must be nonnegative and limit must be between 1 and 50")
    terms = [word for word in re.findall(r"[a-z0-9_]+", query.casefold())
             if len(word) > 2 and word not in QUERY_STOPWORDS]
    if not terms:
        raise ToolError("query needs an API concept, such as tenant or billing")
    doc, tree = _load(doc_url)
    matches = []
    for folder, item in _requests(tree):
        primary = " ".join(str(item.get(key) or "") for key in ("name", "endpoint")) + " " + folder
        description = str(item.get("description") or "")
        details = " ".join(str(item.get(key) or "") for key in
                           ("params", "headers", "body", "responses"))
        primary, description, details = (value.casefold() for value in (primary, description, details))
        score = sum(4 * (term in primary) + 2 * (term in description) + (term in details)
                    for term in terms)
        if score:
            matches.append((score, {
                "id": item["id"], "folder": _short(folder, 100),
                "name": _short(item.get("name"), 100), "method": item.get("method"),
                "endpoint": _short(item.get("endpoint"), 160),
                "description": _short(item.get("description"), 180),
            }))
    matches.sort(key=lambda match: -match[0])
    end = offset + limit
    return {"title": doc["title"], "url": doc.get("url"), "version": doc["version"],
            "total": len(matches), "offset": offset,
            "next_offset": end if end < len(matches) else None,
            "endpoints": [item for _, item in matches[offset:end]]}


@mcp.tool()
def get_endpoint(request_id: str, doc_url: str = "", response_name: str = "") -> dict:
    """Get full request details for an ID from search_documentation or list_endpoints. Pass response_name for a saved response example. Call only for relevant routes to keep context small."""
    doc, tree = _load(doc_url)
    for folder, item in _requests(tree):
        if item.get("id") != request_id:
            continue
        responses = item.get("responses") or {}
        if response_name and response_name not in responses:
            raise ToolError(f"Unknown response example: {response_name}")
        result = {
            "title": doc["title"], "url": doc.get("url"), "folder": folder, "id": item["id"],
            "name": item["name"], "method": item["method"],
            "endpoint": item["endpoint"], "description": item.get("description"),
            "auth_type": (item.get("auth") or {}).get("authType"),
            "params": _safe_rows(item.get("params") or []),
            "headers": _safe_rows(item.get("headers") or []),
            "body": item.get("body"), "response_names": list(responses),
        }
        if response_name:
            example = responses[response_name]
            result["response"] = {key: example.get(key) for key in ("name", "status", "code", "body")}
        return result
    raise ToolError(f"Request ID not found: {request_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hoppscotch public docs MCP server")
    parser.add_argument("--check", nargs="?", const="", metavar="DOC_URL", help="fetch a document and print a summary")
    parser.add_argument("--http", action="store_true", help="serve Streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    args = parser.parse_args()
    if args.check is not None:
        try:
            result = get_document(args.check)
        except ToolError as exc:
            parser.error(str(exc))
        print(f"{result['title']} ({result['version']}): {result['endpoint_count']} endpoints")
    elif args.http:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
