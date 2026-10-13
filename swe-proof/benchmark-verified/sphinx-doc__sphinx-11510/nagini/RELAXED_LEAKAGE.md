# RELAXED-LEAKAGE ACCEPTANCE: sphinx-doc__sphinx-11510

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14; see RELAXED_LEAKAGE.md).** This instance is a
`problem_statement <-> gold` MISMATCH at the level of the gold's single tested
discriminator: the public issue asks only that included RST content be run
through the `source-read` listener (a behavioural symptom report), but the gold
fix's actually-tested behaviour is the **two-marker exclusion** — the gathered
line sequence carries two trailing docutils-0.18 framing markers that must be
held OUT of the event and re-attached verbatim afterwards. That marker structure
(`include_lines[:-2]` / `include_lines[-2:]`, "framing markers", "book-keeping",
"final two") lives ONLY in the gold patch comment / `hints_text` / docutils
internals, never in the solver-visible `problem_statement`. A spec faithful to
the F2P tests MUST pin the marker exclusion (proven below), so faithful +
non-leaking is provably impossible. Independent adversarial analysis (the batch06
panel) confirmed the verification CORE is fully SOUND
(G-VERIFY/G-DIFF/G-MUT/G-EQ/G-AX/faithfulness clean) and the gold resolves
(G-RESOLVE), so the `verify => correct` guarantee is UNAFFECTED — only the
secondary no-leakage property is relaxed for this documented instance.

## The relaxed delta is NARROW: only the two-marker exclusion

It is important not to over-state the leak. Most of the fix-core is NOT a leak at
all under directive 6, and the rest is hidden from the consumer:

- **Already public in `problem_statement` (no leak):** the behavioural framing the
  spec view narrates — that included content should pass through the `source-read`
  content-transformation hook just as a primary document does. The public issue is
  literally titled "source-read event does not modify include'd files source", and
  its Expected-behaviour section asks for exactly this. Token check:
  `source-read`=PRESENT, `include`=PRESENT in `problem_statement`.
- **Hidden from the consumer (not in the spec view, so no leak to relax):** the fix
  *mechanism* — monkey-patching `StateMachine.insert_input`, `text = "\n".join(...)`,
  `events.emit("source-read", ...)`, `text.splitlines()`. These tokens appear only
  in `hints_text` (which the solver never sees) and in this bundle's
  consumer-hidden mapping.md / axiom_check.py — NOT in the spec view (model.py
  docstring + comments). The spec view names no patched symbol/path
  (`Include`/`insert_input`/`StateMachine`/`_insert_input`/`os_path`/`path2doc`)
  and quotes no diff line. Token check on `problem_statement`: `insert_input`,
  `statemachine`, `monkey`, `splitlines`, `".join`, `splitlines` = all ABSENT
  (present only in `hints_text`).
- **The ONLY relaxed increment:** the two-marker structure. The spec view
  (model.py docstring L11-21 and the post-condition comments) narrates that the
  gathered content's "final two entries are internal book-keeping markers that
  frame the inserted region ... carried through unchanged and re-attached." That
  marker vocabulary is the non-public docutils-0.18 detail. Token check on
  `problem_statement`: `marker`, `framing`, `book-keeping`, `final two`, `[:-2]`,
  `[-2:]` = all ABSENT (and `marker`/`framing`/`book-keeping` are absent from
  `hints_text` too — the markers live only in the gold patch comment and docutils'
  `Include.run`, which appends `['', '.. end of inclusion from "%s"' % path]`).

So the relaxation is confined to the marker-exclusion refinement layered on top of
an issue-public behaviour, which lowers practical severity.

---

## Why the marker leak is genuinely unavoidable (not lazy de-narration)

### The gold's tested discriminator: exclude the final two marker lines

Gold patch (`sphinx/directives/other.py`, the `_insert_input` closure installed in
`Include.run`):

```python
text = "\n".join(include_lines[:-2])          # body = all but the two markers
arg = [text]
self.env.app.events.emit("source-read", docname, arg)
text = arg[0]
include_lines = text.splitlines() + include_lines[-2:]   # reattach markers
```

with the explicit comment: *"In docutils 0.18 and later, there are two lines at
the end that act as markers. We must preserve them and leave them out of the
source-read event."*

The F2P tests (`tests/test_directive_other.py::test_include_source_read_event`,
`::test_include_source_read_event_nested_includes`) pin the exact parsed result.
The panel proved in-container that an impl which offers the FULL gathered lines to
the event (markers included) produces
`'\nBaz was here.\n\n.. end of inclusion from "baz/baz.rst"'` instead of the
F2P-required `'\nBaz was here.'` — i.e. the marker-exclusion is a TESTED
discriminator, not a cosmetic detail. A faithful spec therefore cannot omit it.

### The public problem_statement says nothing about markers

The `problem_statement` is a pure symptom report: a `source-read` listener's
`&REPLACE_ME;` substitution reaches a primary document but not an included one.
It contains nothing about the gathered line sequence's internal structure, no
trailing markers, no `[:-2]`/`[-2:]` slicing, no notion that part of the gathered
content must bypass the event. The two-marker structure is an artifact of how the
docutils `Include` directive frames inserted regions — surfaced only in the gold
patch comment and docutils internals. There is no PS-derivable reformulation that
both models the gold fix and avoids the marker structure: drop the marker
exclusion and the spec is unfaithful (the prepatch could no longer be
distinguished on the body-replacement clause without also corrupting the marker
clause, and a full-lines impl would satisfy it while failing the F2P tests).

### Any faithful spec must pin the leaked (marker) discriminator

To satisfy G-EQ / faithfulness, `model.py` pins three things the gold's
behaviour demands: (1) the body region offered to the hook is exactly
`lines[:-2]`; (2) the two framing markers `lines[-2:]` are preserved verbatim in
position; (3) the forwarded result is `hook(body) ++ markers`. Clauses (1)-(2)
are the relaxed marker increment. The spec view does NOT name the patched
symbols/path and contains no diff line; the relaxation is the *behavioural*
naming of the two-marker frame, which is the F2P discriminator and is absent from
the public issue.

## Why this is NOT a soundness defect

The `verify => correct` chain is intact and was re-verified after the refinement:

- **G-VERIFY: PASS** — `model.py` verifies (26.63s, no flags, no float encoding).
- **G-DIFF: PASS** — `model_prepatch.py` (gathered lines forwarded verbatim, the
  pre-patch `insert_input` path) FAILS at `model_prepatch.py:96` on the
  discriminating postcondition
  `Ensures(ToSeq(Result()) == transformed(ToSeq(lines)))` — the body region is
  not replaced by `hook(body)`. `same_spec == True` (axioms / pure / pre / post /
  invariants and the module docstring byte-identical between the twins).
- **G-MUT: PASS** — 20/20 impl mutants killed.
- **G-EQ: SOUND/TIGHT** — refinement.md all R / A-consumed / I, no kind-3; the
  changed op (route body through hook, splice between the framing markers) is
  modeled structurally and grounded in the runtime `lines` carrier (directive 8 —
  `hook` is uninterpreted and the result is pinned to `hook(actual input body)`,
  with no `materialize(PSeq) -> List` path, so the call-and-discard-result echo
  attack is rejected); only the unchanged event-dispatch + round-trip callee is
  axiomatized.
- **G-AX: SOUND** — `axiom_check.py` drives the REAL
  `sphinx.events.EventManager('source-read')` + real `os_path` over boundary
  (incl. the two F2P shapes) + fuzz line sets and confirms marker
  exclusion/reattachment, body-is-offered, round-trip identity under the identity
  hook, and hook propagation lands only in the body region. The markers bypass the
  join/splitlines round trip (reattached after the split), so splitlines edge
  behaviour can never reach them.
- **G-RESOLVE** — `patch.diff` == gold verbatim (2867 B), applies cleanly at
  `base_commit` (`git apply --check` OK); harness `resolved` (orchestrator Docker
  run).

The mechanical G-LEAK screen passes (no diff lines / patched-symbol names / patched
paths in the spec view), but it is lexical and blind to this semantic leak: a
token (the two-marker structure) that is ABSENT from `problem_statement` is
LOAD-BEARING for faithfulness here, which is precisely when a clean `pass` is
wrong and `relaxed` is required. The adversarial reconstruction judgment is binding
and establishes the PS<->gold mismatch.

## Conclusion

KEEP under the relaxed-leakage policy: the core is sound and the gold resolves,
but the gold's tested discriminator (the two-marker exclusion) is settled only in
the gold patch comment / docutils internals / `hints_text` while the public
`problem_statement` is a marker-agnostic symptom report, so a faithful spec cannot
avoid naming the marker frame. The relaxed delta is narrow (markers only; the
join/emit/splitlines/monkey-patch core is consumer-hidden, and the source-read /
include behaviour is already public). `meta.json` records
`gates.G-LEAK.status = "relaxed"` with a pointer to this document.
