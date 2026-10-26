"""Search the bundled React Bits index and retrieve a public registry item.

Only the canonical component name and variant are sent to the fixed public
registry hosts. The helper never executes component code or sends chat data.
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

CATALOG_PATH = Path(__file__).resolve().parent.parent / "assets" / "catalog.json"
VARIANTS = ("JS-CSS", "JS-TW", "TS-CSS", "TS-TW")
MAX_RESPONSE_BYTES = 2_000_000
REPOSITORY_API = "https://api.github.com/repos/osa822630-droid/react-bits/contents/public/r"
OFFICIAL_REGISTRY = "https://reactbits.dev/r"


class CatalogError(Exception):
    """A user-facing lookup or retrieval error."""


def load_catalog():
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    if catalog.get("schemaVersion") != 1 or not isinstance(catalog.get("components"), list):
        raise CatalogError("The bundled React Bits catalog has an unsupported format.")
    return catalog["components"]


def normalized(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def find_component(components, name):
    key = normalized(name)
    for component in components:
        if key and normalized(component["name"]) == key:
            return component
    raise CatalogError(f"Component {name!r} is not in the bundled catalog. Try search first.")


def search_components(components, query, category=None, limit=15):
    words = re.findall(r"[a-z0-9]+", query.lower())
    if not words:
        raise CatalogError("Search needs at least one English component name or keyword.")
    if category and normalized(category) not in {normalized(c["category"]) for c in components}:
        raise CatalogError("Unknown category. Use TextAnimations, Animations, Components, Micro, or Backgrounds.")

    matches = []
    for component in components:
        if category and normalized(component["category"]) != normalized(category):
            continue
        name = component["name"].lower()
        description = component["description"].lower()
        group = component["category"].lower()
        score = 0
        for word in words:
            if word in name:
                score += 10
            elif word in description:
                score += 3
            elif word in group:
                score += 1
            else:
                break
        else:
            matches.append((score, component))
    matches.sort(key=lambda result: (-result[0], result[1]["name"].lower()))
    return [
        {
            "name": component["name"],
            "category": component["category"],
            "description": component["description"],
            "docsUrl": component["docsUrl"],
            "variants": list(component["variants"]),
        }
        for _, component in matches[:limit]
    ]


def component_info(components, name, variant):
    component = find_component(components, name)
    if variant not in component["variants"]:
        options = ", ".join(component["variants"])
        raise CatalogError(f"{component['name']} does not have {variant}. Available: {options}.")
    registry_name = f"{component['name']}-{variant}"
    encoded_name = quote(registry_name, safe="")
    return {
        "name": component["name"],
        "category": component["category"],
        "description": component["description"],
        "docsUrl": component["docsUrl"],
        "variant": variant,
        "availableVariants": list(component["variants"]),
        **component["variants"][variant],
        "repositoryRegistryUrl": f"{REPOSITORY_API}/{encoded_name}.json?ref=main",
        "officialRegistryUrl": f"{OFFICIAL_REGISTRY}/{encoded_name}.json",
        "installCommand": f"npx shadcn@latest add {OFFICIAL_REGISTRY}/{encoded_name}",
    }


def fetch_registry(info):
    expected_name = f"{info['name']}-{info['variant']}"
    sources = (
        ("repository", info["repositoryRegistryUrl"], "application/vnd.github.raw+json"),
        ("official", info["officialRegistryUrl"], "application/json"),
    )
    errors = []
    for label, url, accept in sources:
        request = Request(url, headers={"Accept": accept, "User-Agent": "react-bits-claude-skill/1.0"})
        try:
            with urlopen(request, timeout=12) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError("response exceeds the size limit")
            item = json.loads(raw)
            # The GitHub API can return a contents envelope rather than raw JSON.
            if isinstance(item, dict) and item.get("encoding") == "base64" and isinstance(item.get("content"), str):
                item = json.loads(base64.b64decode(item["content"], validate=False))
            if not isinstance(item, dict) or item.get("name") != expected_name:
                raise ValueError("unexpected registry item")
            files = item.get("files")
            if not isinstance(files, list) or not files or any(
                not isinstance(file, dict)
                or not isinstance(file.get("path"), str)
                or not isinstance(file.get("content"), str)
                for file in files
            ):
                raise ValueError("registry item is missing source files")
            return {"source": label, "sourceUrl": url, "registry": item}
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError, TypeError) as error:
            errors.append(f"{label}: {error}")
    raise CatalogError(
        "Could not fetch the component source ("
        + "; ".join(errors)
        + "). Network access may be disabled. Use the links from info or ask the user to provide the registry JSON."
    )


def positive_limit(value):
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("limit must be a number from 1 to 100") from error
    if not 1 <= number <= 100:
        raise argparse.ArgumentTypeError("limit must be a number from 1 to 100")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    search_parser = subparsers.add_parser("search", help="Search the offline catalog")
    search_parser.add_argument("query", nargs="+", help="English name or keywords")
    search_parser.add_argument("--category", help="Restrict to a React Bits category")
    search_parser.add_argument("--limit", type=positive_limit, default=15)
    for action in ("info", "fetch"):
        action_parser = subparsers.add_parser(action, help=f"{action.title()} a catalog component")
        action_parser.add_argument("name", help="Component name, e.g. SplitText")
        action_parser.add_argument("--variant", type=str.upper, choices=VARIANTS, default="JS-CSS")
    args = parser.parse_args(argv)

    try:
        components = load_catalog()
        if args.command == "search":
            result = search_components(components, " ".join(args.query), args.category, args.limit)
        else:
            info = component_info(components, args.name, args.variant)
            result = fetch_registry(info) if args.command == "fetch" else info
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (CatalogError, OSError, json.JSONDecodeError) as error:
        print(f"React Bits: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
