# Item bank contract v1

Content authors can validate a single item or a work-in-progress bank. The web team can use the three original Grade 4 examples in `fixtures/bank.json` to exercise a practice round. Those examples and their five SVGs in `assets/fixtures/` are test inputs. All three have `draft` status.

## Run locally

From `item-bank/`, use Python 3 and its standard library.

| Purpose | Command |
| --- | --- |
| Validate the three golden fixtures | `python3 validate_bank.py --mode fixture --assets assets fixtures/bank.json` |
| Check a release candidate | `python3 validate_bank.py --mode release --assets ASSET_DIR BANK_FILE` |
| Run the offline tests | `python3 -m unittest discover -s tests` |

Replace `ASSET_DIR` with the candidate’s asset directory and `BANK_FILE` with its JSON file. Both CLI paths may be absolute or relative to the working directory. Inside the JSON, asset paths are relative to the designated asset root.

Both modes read the inputs and exit 0 on success. On invalid input the program prints the first diagnostic to stderr and exits 1. Incorrect command-line usage exits 2. Record and option indices start at zero. JSON syntax errors report a line and column. For example, running release mode on the supplied fixtures prints:

```text
fixtures/bank.json: $.items[0].status: release requires approved, found 'draft'
```

## JSON shape

The UTF-8 document is one object with an integer `version` equal to `1` and a nonempty `items` array. Each item and each choice is an object. JSON field names are unique within their object. Additional fields are ignored in v1. Give incompatible changes a new version number.

| Item field | Meaning and validation |
| --- | --- |
| `id` | Nonempty text, unique across the bank. |
| `domain` | `verbal`, `quantitative`, or `nonverbal`. |
| `status` | `draft`, `approved`, or `rejected`. Only editorial review can grant approval. |
| `skill` | Nonempty text identifying the reasoning skill. |
| `stem` | Nonempty question text. For a visual question, describe the given diagram and its reading order without revealing the rule or key. |
| `choices` | Exactly four objects. Each has an `id` unique within the item and a nonempty `text` description distinct from the other options. |
| `key` | Nonempty text matching exactly one choice ID in this item. |
| `explanation` | Nonempty text showing how to reach the answer. |
| `stemSvg` and `choices[i].svg` | Paths to the stimulus and individual option drawings. All five are required for a nonverbal item. For the other domains, each reference is checked whenever present. |

The validator trims outer whitespace when checking strings and comparing IDs. IDs are case-sensitive. For distinct option descriptions it also folds case and collapses repeated whitespace. Use relative, forward-slash paths to local SVG files. Each supplied path must name an existing file with an `.svg` extension and resolve inside the asset root, including when symlinks are present.

## What each mode establishes

Fixture mode checks the structure and assets of any nonempty fragment. A single item, the three-domain example, and a six-item authoring fragment are all valid inputs. Release mode adds three checks: exactly 18 items, exactly six per domain, and an existing `approved` status on every record.

The tests generate a balanced 18-item bank in a temporary directory using synthetic copies. Its approvals exercise the release rule only. Keep candidate banks and their assets separate from the test inputs. Reviewers assess originality, Grade 4 suitability, neutral visual descriptions, plausible distractors, mathematical reasoning, and legibility before approving any candidate. The validator checks asset references and structural rules. It never promotes a record or publishes a bank.
