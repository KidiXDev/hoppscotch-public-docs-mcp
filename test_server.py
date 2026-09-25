import unittest
from unittest.mock import patch

from hoppscotch_public_docs_mcp import server


DOC = {"title": "Example", "version": "CURRENT", "url": "https://api-docs.hoppscotch.io/view/abc/CURRENT",
       "versions": [{"version": "CURRENT"}], "environmentVariables": '[{"key":"BASE_URL"}]'}
TREE = {"requests": [], "folders": [{"name": "Users", "requests": [{
    "id": "req1", "name": "Create", "method": "POST", "endpoint": "/users",
    "description": "Create a user", "auth": {"authType": "bearer", "token": "do-not-return"},
    "params": [{"key": "api_key", "value": "do-not-return"}],
    "headers": [{"key": "Content-Type", "value": "application/json"}],
    "body": {"contentType": "application/json", "body": "{}"},
    "responses": {"Created": {"name": "Created", "status": "OK", "code": 201, "body": "{}"}},
}]}]}


class ServerTest(unittest.TestCase):
    def test_url_and_lookup(self):
        self.assertEqual(
            server._api_url("https://api-docs.hoppscotch.io/view/abc/CURRENT"),
            "https://api.hoppscotch.io/v1/published-docs/abc/CURRENT",
        )
        with self.assertRaises(server.ToolError):
            server._api_url("https://example.com/view/abc")
        with patch.dict(server.os.environ, {"HOPPSCOTCH_DOC_URL": ""}):
            with self.assertRaises(server.ToolError):
                server._api_url("")
        with patch.dict(server.os.environ, {
            "HOPPSCOTCH_DOCS_ORIGIN": "http://localhost:3000",
            "HOPPSCOTCH_API_BASE_URL": "http://localhost:3170/v1",
        }):
            self.assertEqual(server._api_url("http://localhost:3000/view/abc"),
                             "http://localhost:3170/v1/published-docs/abc")
        with patch.object(server, "_load", return_value=(DOC, TREE)):
            overview = server.get_document()
            self.assertEqual(overview["endpoint_count"], 1)
            self.assertEqual(overview["variables"], ["BASE_URL"])
            found = server.list_endpoints("create")
            self.assertEqual(found["endpoints"][0]["id"], "req1")
            detail = server.get_endpoint("req1", response_name="Created")
            self.assertEqual(detail["folder"], "Users")
            self.assertEqual(detail["params"][0]["value"], "[redacted]")
            self.assertEqual(detail["response"]["code"], 201)
            self.assertNotIn("do-not-return", str(detail))
            with self.assertRaises(server.ToolError):
                server.get_endpoint("req1", response_name="Missing")


if __name__ == "__main__":
    unittest.main()
