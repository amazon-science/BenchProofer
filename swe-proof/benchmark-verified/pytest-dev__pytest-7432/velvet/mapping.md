# mapping.md — pytest-dev__pytest-7432

Binds `Solution.lean` symbols to the repo at
`base_commit = e6e300e729dd33956e5448d8be9a0b1540b4e53a`.

Repo file under change: `src/_pytest/skipping.py`
(the report post-processing in the `pytest_runtest_makereport` hook wrapper).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reportSkipLocation (markSkipped xfailReportingOff priorClassification : Bool) (rep : Report)` | the post-`yield` body of `pytest_runtest_makereport(item, call)` — `src/_pytest/skipping.py:261-307` | the modeled changed function (the report post-processing step) |
| `markSkipped` | `item._store.get(skipped_by_mark_key, True)` (`skipping.py:292`) | whether the skip originates from a skip/skip-if marker |
| `xfailReportingOff` | `item.config.option.runxfail` (`skipping.py:273`, the `--runxfail` option) | whether expected-failure reporting is switched off |
| `priorClassification` | whether any earlier arm of the `if/elif` classification chain matched and consumed this report (`skipping.py:266` unexpected-success, `273` runxfail, `275` imperative-xfail, `279` not-skipped-but-xfailed) | whether an earlier classification arm already handled the report |
| `rep` | `rep = outcome.get_result()` (`skipping.py:263`) — the report as already classified by the arms above | FREE INPUT: the classified report; the classification ahead of this step is UNCHANGED (§3) |
| `rep.skipped` | `rep.skipped` (`skipping.py:293`) | the report records the test as skipped |
| `rep.hasStructuredLocation` | `type(rep.longrepr) is tuple` (`skipping.py:294`) | the long-form representation is the `(file, line, reason)` triple |
| `rep.locatedAtItem` / `out.locatedAtItem` | the location component of `rep.longrepr` (`skipping.py:300-306`): `false` ⇔ it points inside pytest (`skipping.py:<framework line>`); `true` ⇔ rewritten to `str(filename), line + 1` from `item.reportinfo()` (the test definition) | the SIDE-EFFECT observable the F2P test asserts via `SKIPPED [1] test_sample.py:2:` |
| `fixSkipLocation markSkipped rep` | the body of the skip-location correction block (`skipping.py:294-306`) | pure helper: the corrected report |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `item._store.get(skipped_by_mark_key, True)` : truthy/falsey | `Bool` (`markSkipped`) | `true` ⇔ the marker key is present-and-truthy (default `True`); `false` ⇔ falsey. Only the boolean is observed. |
| `item.config.option.runxfail` : truthy/falsey | `Bool` (`xfailReportingOff`) | `true` ⇔ `--runxfail` given; `false` ⇔ not. |
| "an earlier `if/elif` arm matched" | `Bool` (`priorClassification`) | `true` ⇔ one of the unexpected-success / runxfail / imperative-xfail / not-skipped-xfailed arms fired; `false` ⇔ none did. |
| `rep.skipped` : bool | `Bool` (`rep.skipped`) | identity. |
| `type(rep.longrepr) is tuple` : bool | `Bool` (`rep.hasStructuredLocation`) | `true` ⇔ `longrepr` is the `(file, line, reason)` triple; `false` ⇔ any other shape (`str`, `None`, exception repr). |
| the location field of `rep.longrepr` (file:line) | `Bool` (`rep.locatedAtItem`) | `true` ⇔ the location is the test definition (`item.reportinfo()` → `test_sample.py:2`); `false` ⇔ it points inside the framework (`skipping.py:<n>`). The F2P assertion `SKIPPED [1] test_sample.py:2:` ⇔ `locatedAtItem = true`. The `reason` and exact filename/line numerals are not modeled — only WHETHER the location was corrected, which is the changed observable. |

The report is modeled as a `structure Report` carrying only the three touched
fields. `item`, `call`, and the unmodeled report fields (`reason`, `outcome`,
`wasxfail`, …) are not carried: the correction reads none of them, and the
classification that sets them is unchanged (§3).

## 3. Callee provenance

No axioms and no A-reference deep models.

- The report-classification ahead of the correction — the `if/elif` arms that
  set `rep.outcome` / `rep.longrepr` / `rep.wasxfail` for the unexpected-success,
  `--runxfail` pass-through, imperative-xfail, and not-skipped-but-xfailed cases
  (`skipping.py:265-290`) — is **UNCHANGED** by the fix. The patch does not alter
  what those arms compute; it only changes WHETHER the skip-location correction
  is reachable after them. Its result is therefore taken as the **free inputs**
  `rep : Report` (the already-classified report) and `priorClassification : Bool`
  (whether an earlier arm fired). The spec makes no behavioural claim about that
  classification and holds for EVERY value those inputs could take, so there is
  nothing to check against a real callee — hence **no G-AX** (mirrors
  django__django-11451's free-input `backendOutcome` and django__django-11149's
  free-input results).
- The CHANGED op is the **detachment of the correction from the `elif` chain**
  (`elif (...)` → a standalone `if (...)`), modeled **deeply** as the
  unconditional `fixSkipLocation` that depends only on `markSkipped`,
  `rep.skipped`, `rep.hasStructuredLocation` — never on `priorClassification` or
  `xfailReportingOff`. No outside contract is consumed (I-tagged, refinement.md).

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The fix's only DISCRIMINATING
observable is a **side effect on a live pytest run** — that a marker-induced
skip's reported location is rewritten to the test definition
(`SKIPPED [1] test_sample.py:2:`) even when `--runxfail` is given, rather than
left pointing inside the framework (`SKIPPED [1] src/_pytest/skipping.py:NNN:`).

There is no pytest-free, input-dependent R/I shadow to differential-test:

- The observable (`locatedAtItem`) materializes only when the **full pytest
  collection + runtest protocol** executes a real test item under a real config:
  to observe "the reported location was corrected" one must run `pytest -rs
  [--runxfail]` over a test file through the real `pytest_runtest_makereport`
  hook wrapper and read the terminal summary — i.e. the F2P test itself
  (`test_xfail_run_with_skip_mark[test_input1-expected1]`,
  `result.stdout.fnmatch_lines(["SKIPPED [1] test_sample.py:2: ...", ...])`),
  not a pure transliteration this gate can fuzz over ≥10⁵ inputs.
- The classified report (`rep`) and `priorClassification` are **free inputs**
  produced by the unchanged classification chain (§3); their R/I shadow is a
  pass-through with no input-dependent computation to refute. The changed op's
  content is the structural decision `markSkipped && rep.skipped &&
  rep.hasStructuredLocation` made INDEPENDENTLY of `priorClassification`, whose only
  shadow is a constant decision over presence bits — diffing it carries no
  information the spec (G-VERIFY) does not already pin.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only observable is a
side effect on a live framework run with no offline R/I shadow, set
`meta.json conf_skip=true` and ship a `status=skip` stub (precedent:
django__django-11451, django__django-11179). Soundness of the modeled behavior
is carried instead by **G-VERIFY** (the spec provably forces
`out = fixSkipLocation markSkipped rep` — the correction depends only on the
marker/skipped/tuple observations, never on `xfailReportingOff` or
`priorClassification`) and **G-DIFF** (the prepatch, which gates the correction
behind `!priorClassification`, fails exactly the `locatedAtItem = true` clause
when an earlier arm fired — refinement.md §B).

## 5. Notes

The single FAIL_TO_PASS entry is
`TestXFail::test_xfail_run_with_skip_mark[test_input1-expected1]` — the
`["-rs", "--runxfail"]` parametrization. `[test_input0-expected0]` (the `-rs`
case without `--runxfail`) is in PASS_TO_PASS: it already passed pre-patch
because, without `--runxfail`, no earlier arm fires for a marker skip, so the
old `elif` fell through to the correction. The fix makes the correction
independent of that, so the `--runxfail` case is corrected too. One modeled
function + one prepatch covers the single fixed behavior; the gold-verbatim
`patch.diff` resolves it (G-RESOLVE).

`markSkipped`, `xfailReportingOff`, `priorClassification`, `rep` are all
read-only inputs — none is declared `mut` (directive 5): the step reads them and
produces a fresh corrected `Report`, mutating nothing it is handed.
