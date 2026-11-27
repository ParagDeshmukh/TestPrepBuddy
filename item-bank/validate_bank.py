"""Check a Test Prep Buddy v1 item bank with the Python standard library."""
import argparse
from collections import Counter
import json
from pathlib import Path, PureWindowsPath
import sys


DOMAINS = ("verbal", "quantitative", "nonverbal")
STATUSES = ("draft", "approved", "rejected")


class InvalidBank(ValueError):
    """A diagnostic with a location in the input."""


def required_text(record, name, location):
    value = record.get(name)
    if not isinstance(value, str) or not value.strip():
        raise InvalidBank(f"{location}.{name}: expected nonempty text")
    return value.strip()


def check_asset(record, name, location, root):
    reference = required_text(record, name, location)
    field = f"{location}.{name}"
    path = Path(reference)
    if path.is_absolute() or PureWindowsPath(reference).anchor or "\\" in reference:
        raise InvalidBank(f"{field}: expected a relative path using forward slashes")
    if path.suffix.lower() != ".svg":
        raise InvalidBank(f"{field}: expected an .svg file")
    try:
        resolved = (root / path).resolve()
        if root not in resolved.parents:
            raise InvalidBank(f"{field}: path is outside asset root")
        if not resolved.is_file():
            raise InvalidBank(f"{field}: file does not exist: {reference}")
    except InvalidBank:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise InvalidBank(f"{field}: cannot resolve asset: {exc}") from exc


def check_choices(item, location, root, needs_svg):
    choices = item.get("choices")
    if not isinstance(choices, list) or len(choices) != 4:
        raise InvalidBank(f"{location}.choices: expected exactly four choices")
    ids = set()
    descriptions = set()
    for index, choice in enumerate(choices):
        field = f"{location}.choices[{index}]"
        if not isinstance(choice, dict):
            raise InvalidBank(f"{field}: expected a choice object")
        choice_id = required_text(choice, "id", field)
        if choice_id in ids:
            raise InvalidBank(f"{field}.id: duplicate choice id {choice_id!r}")
        ids.add(choice_id)
        description = required_text(choice, "text", field)
        normalized = " ".join(description.casefold().split())
        if normalized in descriptions:
            raise InvalidBank(f"{field}.text: duplicate option description")
        descriptions.add(normalized)
        if needs_svg or "svg" in choice:
            check_asset(choice, "svg", field, root)
    if required_text(item, "key", location) not in ids:
        raise InvalidBank(f"{location}.key: must match a choice id")


def check_bank(bank, root, mode):
    if not isinstance(bank, dict):
        raise InvalidBank("$: expected a bank object")
    version = bank.get("version")
    if type(version) is not int or version != 1:
        raise InvalidBank("$.version: expected integer 1")
    items = bank.get("items")
    if not isinstance(items, list) or not items:
        raise InvalidBank("$.items: expected a nonempty array")
    seen = set()
    counts = Counter()
    for index, item in enumerate(items):
        field = f"$.items[{index}]"
        if not isinstance(item, dict):
            raise InvalidBank(f"{field}: expected an item object")
        item_id = required_text(item, "id", field)
        if item_id in seen:
            raise InvalidBank(f"{field}.id: duplicate item id {item_id!r}")
        seen.add(item_id)
        for name in ("skill", "stem", "explanation"):
            required_text(item, name, field)
        domain = required_text(item, "domain", field)
        if domain not in DOMAINS:
            raise InvalidBank(f"{field}.domain: expected one of {', '.join(DOMAINS)}")
        counts[domain] += 1
        status = required_text(item, "status", field)
        if status not in STATUSES:
            raise InvalidBank(f"{field}.status: expected one of {', '.join(STATUSES)}")
        if mode == "release" and status != "approved":
            raise InvalidBank(f"{field}.status: release requires approved, found {status!r}")
        if domain == "nonverbal" or "stemSvg" in item:
            check_asset(item, "stemSvg", field, root)
        check_choices(item, field, root, domain == "nonverbal")
    if mode == "release":
        if len(items) != 18:
            raise InvalidBank(f"$.items: release requires 18 items, found {len(items)}")
        for domain in DOMAINS:
            if counts[domain] != 6:
                raise InvalidBank(f"$.items: release requires 6 {domain} items, found {counts[domain]}")
    return len(items)


def unique_fields(pairs):
    record = {}
    for name, value in pairs:
        if name in record:
            raise InvalidBank(f"duplicate JSON field {name!r}")
        record[name] = value
    return record


def reject_constant(token):
    raise InvalidBank(f"$: invalid JSON constant {token}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("fixture", "release"))
    parser.add_argument("--assets", type=Path, required=True, help="local SVG asset root")
    parser.add_argument("bank", type=Path, help="UTF-8 JSON bank")
    args = parser.parse_args()
    try:
        root = args.assets.resolve(strict=True)
        if not root.is_dir():
            raise OSError("expected a directory")
    except (OSError, RuntimeError) as exc:
        print(f"--assets: {exc}", file=sys.stderr)
        return 1
    try:
        bank = json.loads(
            args.bank.read_text(encoding="utf-8"),
            object_pairs_hook=unique_fields, parse_constant=reject_constant,
        )
        count = check_bank(bank, root, args.mode)
    except (ValueError, OSError, RecursionError) as exc:
        print(f"{args.bank}: {exc}", file=sys.stderr)
        return 1
    print(f"{args.mode}: {count} items passed structural validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
