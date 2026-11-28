# TPB-17 · Architecture decision draft

**Frontend decision.** The project owner selected React for the responsive website. TPB-20 will render the entry page with React. TypeScript and Vite are the proposed language and build tool.

**Architecture proposal · 27 November 2026.** Use a statically served responsive website for the first anonymous three-question round. Keep the versioned, reviewed question bank and its SVG files alongside the site. Keep answers in page memory. Engineering Lead owns D1. The project owner has supplied the repository. The static delivery model, build setup and CI runner remain proposed.

## Source inventory

The owner requested a fresh Grade 4 NGAT project, website first, and designated [ParagDeshmukh/TestPrepBuddy](https://github.com/ParagDeshmukh/TestPrepBuddy). The supplied AGENTS.md instruction places this work in the Test Prep Buddy project. The following commands were run in the new checkout before creating this contribution.

| Inspection | Observed result |
| --- | --- |
| `git rev-parse HEAD` | `c59ca8bde46c6918112ec81a603e72b3a5e656f7` |
| `git status --short --branch` | `## main...origin/main`. Clean working tree. |
| `git ls-tree -r --name-only HEAD` | `README.md` was the entire tracked tree. |
| `cat README.md` | One heading, `# Test Prep Buddy`. |
| `rg --files --hidden -g '!.git' -g 'AGENTS.md'` | No matching checkout instruction file (exit 1). The supplied project instruction applies. |
| `git branch -a` | Local main, origin/main (default), and origin/tpb-19-item-validator. |
| `git rev-parse origin/tpb-19-item-validator` | `7444c00c23cba362432dc09e143be1bd663bd8af`. |
| `git ls-tree -r --name-only origin/tpb-19-item-validator` and `git show origin/tpb-19-item-validator:item-bank/README.md` | Separate branch contains the documented v1 validator, offline tests, a synthetic bank and five SVGs. The README describes fixture and release modes. |

At the assessed main revision there was no application code, content bank, test suite, dependency or build configuration, CI workflow or deployment manifest. Host, out-of-repository CI settings and deployment state were unverified. There was no existing app command to run. The earlier FastAPI/frontend reports describe previous work. The inventory supplies no evidence of those components on main. There is no tracked implementation conflict with a fresh start. TPB-19 is parallel content tooling and introduces no web runtime requirement.

## Architecture choices

| Decision factor | Static client and local content (recommended) | Web client and practice API |
| --- | --- | --- |
| Anonymous round | Browser selects one verbal, one quantitative and one nonverbal item in that order, handles submissions, then computes the summary in memory. No session identifier is needed. | API can select items, validate submissions and return feedback. It needs request/error contracts and either a transient round identifier or state passed with requests. |
| Local diagrams and answer delivery | Ship one versioned bundle of approved JSON and same-origin SVGs with relative paths. Answers and rationales are inspectable in the download, acceptable for self-practice. Content fixes require a new build. | Serve local SVGs with the site. API can withhold keys until submission and update the bank independently. Asset and response versions must stay compatible. |
| Verification and operation | Check the bank and referenced assets before packaging. Serve built files over local HTTP, smoke-test the entry page, then exercise a three-item round once available. One deployable artifact. | Add API contract and integration tests, service configuration and failure handling for interrupted requests, plus the same browser and diagram checks. |
| State lifetime and future persistence | Reload, tab close or explicit restart discards the round. No cookies, browser storage or account needed for practice. Saved history later requires a new design. | Can also keep rounds ephemeral. A server offers a path to cross-device history, with added identity, retention and access decisions before storage is enabled. |

## Proposed implementation and ownership

- **Engineering Lead and web implementer (TPB-20)** — target the existing repository, working on a feature branch from main. The proposed skeleton pairs React with TypeScript and Vite under `web/`, using a pinned Node LTS toolchain and committed npm lockfile. From `web/`, propose `npm ci`, `npm run build` → `dist/`, and `npm run preview` for local HTTP serving. These are proposed interfaces for the skeleton.
- **Content Lead** — owns approval of the originals. Package only a release-checked bank and its matching asset directory, using the TPB-19 v1 contract when available. Keep calibration examples and test banks outside the distributable site.
- **QE and Engineering (TPB-21)** — propose a GitHub Actions Linux job that runs the same locked install/build, entry-heading smoke and available Python fixture checks from a clean checkout. For a release candidate, check release mode and confirm assets resolve from the built site. A missing heading or invalid asset must fail its corresponding check.
- **Project owner and Engineering Lead** — revisit an API if cross-device progress, restricted answer delivery or independently published content becomes a confirmed requirement. Hosting and data policy decisions remain with their respective owners.

## Unblock and verification

The repository and React frontend are confirmed. To start the TPB-20 skeleton, the Engineering Lead records D1 approval for the static approach, working location and toolchain/build interface above, or supplies the chosen equivalent. Confirm the permitted CI runner for TPB-21. A production host is unnecessary for a local skeleton.

V-001 was reviewed against the fresh-start and responsive-web instructions, REQ-001/002 and the recorded checkout inventory. No executable application check applies to this decision draft. The decision and owner review are open.
