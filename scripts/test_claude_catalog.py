"""Tests for the portable, standard-library-only Claude Web skill helper."""

import base64
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/react-bits/skills/react-bits/scripts/react_bits.py"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("react_bits_skill", SCRIPT)
react_bits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(react_bits)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, limit):
        return self.data[:limit]


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.components = react_bits.load_catalog()
        cls.info = react_bits.component_info(cls.components, "SplitText", "JS-CSS")
        cls.item = {
            "name": "SplitText-JS-CSS",
            "files": [{"path": "SplitText.jsx", "content": "export default function SplitText() {}"}],
            "dependencies": ["gsap@^3.13.0"],
            "registryDependencies": [],
        }
        cls.payload = json.dumps(cls.item).encode()

    def test_search_finds_text_effects_and_category_filter(self):
        results = react_bits.search_components(self.components, "text reveal", "TextAnimations")
        self.assertTrue(results)
        self.assertTrue(all(item["category"] == "TextAnimations" for item in results))
        self.assertTrue(any(item["name"] == "ScrollReveal" for item in results))
        self.assertEqual(react_bits.search_components(self.components, "not-a-real-component"), [])

    def test_search_rejects_empty_query_and_unknown_category(self):
        with self.assertRaises(react_bits.CatalogError):
            react_bits.search_components(self.components, "!!!")
        with self.assertRaises(react_bits.CatalogError):
            react_bits.search_components(self.components, "text", "unknown")

    def test_info_resolves_normalized_name_and_reports_real_dependencies(self):
        info = react_bits.component_info(self.components, "split text", "JS-CSS")
        self.assertEqual(info["name"], "SplitText")
        self.assertIn("gsap@^3.13.0", info["dependencies"])
        self.assertTrue(info["repositoryRegistryUrl"].endswith("SplitText-JS-CSS.json?ref=main"))
        self.assertEqual(
            info["installCommand"], "npx shadcn@latest add https://reactbits.dev/r/SplitText-JS-CSS"
        )
        css = react_bits.component_info(self.components, "LiquidEther", "TS-CSS")
        self.assertTrue(any(file["path"].endswith(".css") for file in css["files"]))

    def test_unknown_names_and_unavailable_variants_cannot_form_urls(self):
        for name in ("../../.git/config", "", "no-such-component"):
            with self.assertRaises(react_bits.CatalogError):
                react_bits.component_info(self.components, name, "JS-CSS")
        with self.assertRaises(react_bits.CatalogError):
            react_bits.component_info(self.components, "SplitText", "INVALID")

    def test_fetch_uses_fixed_github_url_and_returns_actual_source(self):
        with patch.object(react_bits, "urlopen", return_value=FakeResponse(self.payload)) as get:
            result = react_bits.fetch_registry(self.info)
        self.assertEqual(result["source"], "repository")
        self.assertEqual(result["registry"], self.item)
        request = get.call_args.args[0]
        self.assertEqual(request.full_url, self.info["repositoryRegistryUrl"])
        self.assertEqual(get.call_args.kwargs["timeout"], 12)
        self.assertNotIn("conversation", request.full_url)

    def test_github_contents_envelope_is_supported(self):
        envelope = {"encoding": "base64", "content": base64.b64encode(self.payload).decode()}
        with patch.object(react_bits, "urlopen", return_value=FakeResponse(json.dumps(envelope).encode())):
            result = react_bits.fetch_registry(self.info)
        self.assertEqual(result["registry"], self.item)

    def test_network_failure_falls_back_to_official_registry(self):
        with patch.object(
            react_bits, "urlopen", side_effect=[URLError("blocked"), FakeResponse(self.payload)]
        ) as get:
            result = react_bits.fetch_registry(self.info)
        self.assertEqual(result["source"], "official")
        self.assertEqual(result["sourceUrl"], self.info["officialRegistryUrl"])
        self.assertEqual(get.call_count, 2)

    def test_invalid_or_wrong_item_falls_back_and_never_returns_invented_source(self):
        wrong = json.dumps({**self.item, "name": "Other-JS-CSS"}).encode()
        with patch.object(react_bits, "urlopen", side_effect=[FakeResponse(wrong), FakeResponse(self.payload)]):
            self.assertEqual(react_bits.fetch_registry(self.info)["source"], "official")
        invalid_files = json.dumps({**self.item, "files": [{"path": "x"}]}).encode()
        with patch.object(react_bits, "urlopen", side_effect=[FakeResponse(wrong), FakeResponse(invalid_files)]):
            with self.assertRaisesRegex(react_bits.CatalogError, "Could not fetch"):
                react_bits.fetch_registry(self.info)

    def test_oversize_response_and_no_network_have_clear_failures(self):
        oversize = FakeResponse(b"x" * (react_bits.MAX_RESPONSE_BYTES + 1))
        with patch.object(react_bits, "urlopen", side_effect=[oversize, URLError("blocked")]):
            with self.assertRaisesRegex(react_bits.CatalogError, "Network access may be disabled"):
                react_bits.fetch_registry(self.info)

    def test_cli_search_info_and_invalid_name(self):
        def run(*args):
            return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True, check=False)

        search = run("search", "SplitText")
        self.assertEqual(search.returncode, 0)
        self.assertEqual(json.loads(search.stdout)[0]["name"], "SplitText")
        info = run("info", "ProfileCard", "--variant", "ts-tw")
        self.assertEqual(info.returncode, 0)
        self.assertEqual(json.loads(info.stdout)["variant"], "TS-TW")
        bad_name = run("fetch", "../../.git/config")
        self.assertNotEqual(bad_name.returncode, 0)
        self.assertIn("not in the bundled catalog", bad_name.stderr)
        bad_limit = run("search", "text", "--limit", "0")
        self.assertNotEqual(bad_limit.returncode, 0)

    def test_main_reports_both_network_failures_without_a_traceback(self):
        stderr = io.StringIO()
        with patch.object(react_bits, "urlopen", side_effect=URLError("blocked")), patch("sys.stderr", stderr):
            exit_code = react_bits.main(["fetch", "SplitText"])
        self.assertEqual(exit_code, 1)
        self.assertIn("Network access may be disabled", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
