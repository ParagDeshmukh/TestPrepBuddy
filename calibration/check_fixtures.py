"""Offline structural checks for the five TPB-18 calibration cases."""

import json
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent
REQUIRED = {"H9", "K4", "M5", "N7", "R2"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def text(value):
    return isinstance(value, str) and bool(value.strip())


def asset_result(reference):
    path = (ROOT / reference).resolve()
    if Path(reference).is_absolute() or ROOT / "assets" not in path.parents or path.suffix != ".svg":
        return "invalid-asset"
    if not path.is_file():
        return "missing-asset"
    if ElementTree.parse(path).getroot().tag != "{http://www.w3.org/2000/svg}svg":
        return "invalid-asset"
    return None


def inspect(item):
    choices = item["choices"]
    prompt = item["prompt"]
    if not text(prompt["text"]) or not text(item["rationale"]["worked"]) or not text(item["reviewReason"]):
        raise ValueError("empty prompt, worked answer or review reason")
    if item["domain"] not in {"quantitative", "nonverbal"} or item["expectedVerdict"] not in {"pass", "revise", "reject"}:
        raise ValueError("invalid domain or editorial verdict")
    ids = [choice["id"] for choice in choices]
    if ids != list("ABCD") or not all(text(choice["text"]) for choice in choices):
        raise ValueError("expected four labeled choices in A–D order with descriptions")
    issues = []
    if item["key"] not in ids:
        issues.append("bad-key")
    if item["domain"] == "nonverbal":
        if not text(prompt["alt"]):
            raise ValueError("missing stimulus description")
        for figure in [prompt, *choices]:
            issue = asset_result(figure["svg"])
            if issue:
                issues.append(issue)
    return ", ".join(issues) or "pass"


def main():
    manifest = load(ROOT / "manifest.json")
    ids = [entry["id"] for entry in manifest]
    files = {path.relative_to(ROOT / "fixtures").as_posix() for path in (ROOT / "fixtures").rglob("*.json")}
    if len(ids) != len(REQUIRED) or set(ids) != REQUIRED or files != {f"{i}.json" for i in REQUIRED}:
        raise ValueError("unchecked, missing or repeated fixture in manifest or directory")
    success = True
    for entry in manifest:
        case = entry["id"]
        try:
            item = load(ROOT / "fixtures" / f"{case}.json")
            if item["id"] != case or item["expectedVerdict"] != entry["editorial"]:
                raise ValueError("ID or recorded editorial expectation differs from manifest")
            result = inspect(item)
            print(f"{case}: {result} (expected {entry['structural']})")
            if result != entry["structural"]:
                success = False
        except (OSError, ValueError, KeyError, TypeError, ElementTree.ParseError) as error:
            print(f"{case}: {error}", file=sys.stderr)
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        sys.exit(f"Calibration pack: {error}")
