"""All data in this suite is synthetic. No release candidates are written."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "fixtures" / "bank.json"


def release_sample(items):
    result = []
    for n in range(6):
        for original in items:
            item = copy.deepcopy(original)
            item.update(id=f"{original['id']}-test-{n}", status="approved")
            result.append(item)
    return {"version": 1, "items": result}


class ValidatorCLI(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.assets = self.work / "assets"
        shutil.copytree(ROOT / "assets", self.assets)
        self.file = self.work / "test-bank.json"
        self.bank = json.loads(GOLDEN.read_text(encoding="utf-8"))

    def run_cli(self, mode="fixture", path=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "validate_bank.py"), "--mode", mode,
             "--assets", str(self.assets), str(path or self.file)],
            cwd=self.work, capture_output=True, text=True, encoding="utf-8",
        )

    def check(self, bank, expected_error=None, mode="fixture"):
        self.file.write_text(json.dumps(bank), encoding="utf-8")
        result = self.run_cli(mode)
        if expected_error is None:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
        else:
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(expected_error, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_golden_bank(self):
        result = self.run_cli(path=GOLDEN)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3 items passed", result.stdout)
        self.assertEqual([x["domain"] for x in self.bank["items"]],
                         ["verbal", "quantitative", "nonverbal"])
        self.assertTrue(all(x["status"] == "draft" for x in self.bank["items"]))

    def test_golden_artwork(self):
        visual = self.bank["items"][2]
        svg_ns = "{http://www.w3.org/2000/svg}"
        def dot_offsets(reference):
            svg = ElementTree.parse(self.assets / reference).getroot()
            panels = svg.findall(svg_ns + "rect")
            dots = svg.findall(svg_ns + "circle")
            self.assertEqual(len(panels), len(dots))
            return [(int(dot.get("cx")) - int(panel.get("x")),
                     int(dot.get("cy")) - int(panel.get("y")))
                    for panel, dot in zip(panels, dots)]
        self.assertEqual(dot_offsets(visual["stemSvg"]), [(11, 11), (41, 11), (41, 41)])
        positions = [dot_offsets(choice["svg"])[0] for choice in visual["choices"]]
        self.assertEqual(len(set(positions)), 4)
        correct = next(i for i, c in enumerate(visual["choices"]) if c["id"] == visual["key"])
        self.assertEqual(positions[correct], (11, 41))

    def test_fixture_fragments(self):
        sample = release_sample(self.bank["items"])
        six = [item for item in sample["items"] if item["domain"] == "verbal"]
        six[0]["status"] = "rejected"
        self.check({"version": 1, "items": six})
        self.check({"version": 1, "items": six[:1]})

    def test_json_and_encoding(self):
        for content, error in [(b'{"items":\n]}', "line 2 column 1"),
                               (b'{"version":1,"items":[NaN]}', "invalid JSON"),
                               (b'\xff', "utf-8")]:
            with self.subTest(content=content):
                self.file.write_bytes(content)
                result = self.run_cli()
                self.assertEqual(result.returncode, 1)
                self.assertIn(error, result.stderr)

    def test_duplicate_json_field(self):
        content = GOLDEN.read_text(encoding="utf-8")
        self.file.write_text(content.replace('"key": "B"', '"key": "A", "key": "B"', 1),
                             encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate JSON field 'key'", result.stderr)

    def test_bank_structure_and_version(self):
        for bank, field in [([], "$:"), ({}, "$.version"), ({"version":1}, "$.items"),
                            ({"version":1,"items":[]}, "$.items"),
                            ({"version":1,"items":{}}, "$.items"),
                            ({"version":1,"items":[None]}, "$.items[0]")]:
            with self.subTest(bank=bank):
                self.check(bank, field)
        for version in [2, True, "1", 1.0]:
            with self.subTest(version=version):
                self.check(dict(self.bank, version=version), "$.version")

    def test_item_fields(self):
        item = self.bank["items"][0]
        for name in ("id", "domain", "status", "skill", "stem", "key", "explanation"):
            for value in (None, " \t ", []):
                with self.subTest(name=name, value=value):
                    self.check({"version": 1, "items": [dict(item, **{name:value})]},
                               f"$.items[0].{name}")
        for name, value in [("domain","spatial"), ("status","pending"), ("key","E")]:
            with self.subTest(name=name):
                self.check({"version": 1, "items": [dict(item, **{name:value})]},
                           f"$.items[0].{name}")

    def test_duplicate_bank_ids(self):
        self.bank["items"][2]["id"] = "  " + self.bank["items"][0]["id"]
        self.check(self.bank, "$.items[2].id")

    def test_choice_shape_count_and_fields(self):
        item = self.bank["items"][0]
        choices = item["choices"]
        for value in [None, choices[:3], choices + [choices[0]]]:
            item["choices"] = value
            self.check(self.bank, "$.items[0].choices:")
        item["choices"] = choices
        for choice, field in [(False, ""), ({}, ".id"), ({"id":" "}, ".id"),
                              ({"id":"D","text":"  "}, ".text"),
                              ({"id":" A ","text":"Different"}, ".id"),
                              ({"id":"D","text":"  A   STAGE "}, ".text")]:
            with self.subTest(choice=choice):
                choices[3] = choice
                self.check(self.bank, "$.items[0].choices[3]" + field + ":")

    def test_required_visual_references(self):
        for field in ["stemSvg", "svg"]:
            bank = copy.deepcopy(self.bank)
            target = bank["items"][2]
            if field == "svg":
                target = target["choices"][3]
            del target[field]
            self.check(bank, ".choices[3].svg" if field == "svg" else ".stemSvg")

    def test_asset_boundaries_apply_to_optional_and_required_references(self):
        (self.work / "outside.svg").write_text("<svg/>", encoding="utf-8")
        (self.assets / "folder.svg").mkdir()
        for name in ("fixtures/missing.svg", "../outside.svg", str(self.work / "outside.svg"),
                     "folder.svg", "fixtures/sequence.png", "C:/data/plot.svg", "   "):
            with self.subTest(name=name):
                self.bank["items"][0]["stemSvg"] = name
                self.check(self.bank, "$.items[0].stemSvg:")
        del self.bank["items"][0]["stemSvg"]
        self.bank["items"][0]["choices"][1]["svg"] = "missing.svg"
        self.check(self.bank, "$.items[0].choices[1].svg:")
        del self.bank["items"][0]["choices"][1]["svg"]
        self.bank["items"][2]["choices"][0]["svg"] = "../outside.svg"
        self.check(self.bank, "path is outside asset root")

    def test_symlink_outside_assets(self):
        outside = self.work / "outside.svg"
        outside.write_text("<svg/>", encoding="utf-8")
        try:
            (self.assets / "alias.svg").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("this platform does not permit creating symlinks")
        self.bank["items"][2]["stemSvg"] = "alias.svg"
        self.check(self.bank, "$.items[2].stemSvg: path is outside asset root")

    def test_release_accepts_synthetic_balanced_bank(self):
        self.check(release_sample(self.bank["items"]), mode="release")

    def test_release_requires_every_item_approved(self):
        sample = release_sample(self.bank["items"])
        for status in ("draft", "rejected"):
            sample["items"][-1]["status"] = status
            self.check(sample, "$.items[17].status", "release")

    def test_release_counts_and_unique_ids(self):
        sample = release_sample(self.bank["items"])
        items = sample["items"]
        self.check(dict(sample, items=items[:-1]), "release requires 18 items", "release")
        items[0]["domain"] = "quantitative"
        self.check(sample, "release requires 6 verbal items, found 5", "release")
        items[0]["domain"] = "verbal"
        items[17]["id"] = items[0]["id"]
        self.check(sample, "$.items[17].id", "release")


if __name__ == "__main__":
    unittest.main()
