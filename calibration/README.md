# Offline question and SVG calibration pack

Synthetic draft material for TPB-18. The five fixtures test a review process for the Grade 4 practice project. This directory can be copied or removed as a unit. Nothing here is a release candidate.

## Run a review

1. Give the reviewer `blind-review.html`, `rubric.md` and `assets/` together. Open the HTML directly in a browser with networking off. Fill or print the sheet. The fields start blank. Print to PDF to retain typed results.
2. The facilitator runs the following command from this directory. It uses only Python 3 and its standard library.

   ```sh
   python3 check_fixtures.py
   ```

3. Compare the independent solution with `answer-sheet.md`. Reconcile the structural result, stored key and rendered options. Record the reason for any changed verdict. QE reviews the pack and evidence. The Content Lead owns independent reviewer selection and D5 suitability review before publication.

## Contents

| Files | Purpose |
| --- | --- |
| `blind-review.html`, `rubric.md` | Five blind items, blank ratings and criteria for pass, revise or reject. |
| `answer-sheet.md` | Facilitator solutions, distractor rationales, labeled defects and reconciliation record. |
| `manifest.json` | Expected structural and editorial outcomes for every fixture. |
| `fixtures/H9.json`, `K4.json`, `M5.json`, `N7.json`, `R2.json` (all under `fixtures/`) | Fixture-only records with prompt, choices, key, rationale and editorial expectation. |
| `assets/sequence.svg` | Three stimulus panels in reading order. |
| `assets/tile-1.svg`, `tile-2.svg`, `tile-3.svg`, `tile-4.svg`, `tile-5.svg` (all under `assets/`) | Original answer drawings. The missing file named by H9 is deliberate. |
| `check_fixtures.py` | Compares actual structural diagnostics with the manifest. A mismatch, malformed record or unchecked fixture exits nonzero. |

The checker examines keys, ordered choice IDs and local SVG references. Editorial expectations are recorded for comparison after blind review. The checker does not judge the geometry of the drawings. If fixtures change, update the blind HTML and answer sheet to match, then repeat the rendering check.

## Verification V-002

On the supplied pack, `python3 check_fixtures.py` returned 0. H9 produced `missing-asset`, N7 produced `bad-key`, and K4, M5 and R2 produced `pass`. M5 is an editorial reject.

The following negative controls were run on disposable copies. Each returned 1. From the calibration directory, reproduce both with:

```sh
python3 - <<'PY'
import json, shutil, subprocess, tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    copy = Path(tmp) / "calibration"
    shutil.copytree(".", copy)
    manifest = copy / "manifest.json"
    entries = json.loads(manifest.read_text())
    next(e for e in entries if e["id"] == "K4")["structural"] = "bad-key"
    manifest.write_text(json.dumps(entries))
    command = ["python3", "check_fixtures.py"]
    assert subprocess.run(command, cwd=copy).returncode == 1
    shutil.copy("manifest.json", manifest)
    shutil.copy(copy / "fixtures/K4.json", copy / "fixtures/extra.json")
    assert subprocess.run(command, cwd=copy).returncode == 1
PY
```

For the rendering check, open `blind-review.html` as a local file with networking disabled and inspect H9, M5 and R2 at 320, 768 and 1280 CSS pixels. In the recorded Chromium 92 check at all three widths, the document fit the viewport, choices followed fixture order, and the only unresolved image was H9 choice D. Visual inspection of the 320-pixel render confirmed all three stimulus squares and their dots were inside their frames. R2 rendered A upper right, B lower left, C upper left and D lower right. In M5, B and D both rendered lower left. This records a rendering check; independent editorial calibration and D5 sign-off remain open.
