# EARS construction worker prompt

Quoted verbatim into each construction subagent's task (with `{iid}` filled).
Edit here; do not fork per instance.

---

You are authoring an EARS-format REQUIREMENTS bundle for SWE-Bench-Verified
instance **{iid}**. Project root: the repository root. There is NO formal
verifier: the requirements document IS the specification artifact.

## Read first (binding)
1. `{root}/{iid}/instance.json` → `problem_statement` (the issue), `patch`
   (the gold fix), `test_patch` + `FAIL_TO_PASS` + `PASS_TO_PASS` (the hidden
   tests — SECRET; see the leakage rule below).
2. The real source in the worktree (changed functions AND their callers/
   consumers) so the requirements name the right modules/functions.
3. If a GREEN sibling formal bundle exists (`{root}/{iid}/lean/Solution.lean`,
   else velvet/nagini — check its meta.json gates first), read its
   pre/post-conditions as ground truth for making requirements PRECISE. Never
   include formal notation in your output.

## Produce in `{root}/{iid}/ears/`
- `requirements.md` — a standalone Kiro-style EARS document:
  - `## Introduction` — the problem, the affected module/function(s), and the
    goal, in behavioral terms.
  - `## Requirement N: <title>` sections (as many as the change needs), each
    with a `**User story:**` ("As a ..., I want ..., so that ...") and an
    `**Acceptance criteria**` numbered list. Every criterion is EARS:
    `WHEN <trigger>, THEN <subject> SHALL <response>`, `WHILE <state> ...
    SHALL ...`, `IF <condition>, THEN ... SHALL ...`, or ubiquitous
    `The system SHALL ...`. At least one criterion must be trigger-form.
  - Cover EVERY distinct behavior the hidden tests check — including
    regression protection: what PASS_TO_PASS guards becomes explicit
    "SHALL keep" requirements.
  - Name the concrete modules/functions/APIs involved (from the issue and the
    code) so an implementing agent can locate the fix — but never reveal that
    the requirements derive from tests or from a formal spec.
- `meta.json` — must include `spec_sources`: the list of inputs you actually
  consulted, from {{"issue", "hidden_tests", "gold_patch", "formal_sibling"}}.

## Hard rules
- **LEAKAGE (the rule that bites):** never quote test code, test file paths,
  test function/class names, or parametrization ids; never reproduce a gold-
  patch or test-patch line verbatim; never name an identifier the FIX invents
  (describe the behavior instead). G-LEAK screens all of this mechanically.
- **Completeness over brevity, but no padding:** a conforming implementation
  should have no freedom to fail the hidden tests; every SHALL should be
  checkable against observable behavior (values, ordering, errors, kept
  behavior).
- **No implementation prescriptions** beyond what the behavior requires — the
  document says WHAT must hold, localized to the right functions, not HOW to
  edit the code.

## Self-check loop (≤8 rounds)
```
swebench-unified gates --backend ears {iid} --static-only
```
G-HYGIENE (EARS structure + spec_sources) and G-LEAK (test/gold leakage) are
your feedback; fix what they report. If the change genuinely cannot be
described as observable behavioral requirements, write
`{root}/{iid}/ears/BLOCKED.md` (what you tried, why) — a principled BLOCKED is
valid; a vague document is not.

## Final message = structured report
status (green|blocked); static-gate outcomes; the requirements' coverage map
(which criterion pins which behavior of the fix, incl. the SHALL-keep
regression criteria); spec_sources; if blocked, the precise wall.
