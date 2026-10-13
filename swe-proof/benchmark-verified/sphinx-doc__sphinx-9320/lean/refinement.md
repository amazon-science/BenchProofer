# refinement.md — sphinx-doc__sphinx-9320

Maps every operation in `implementation_validateRootEntry` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `validateRootEntry` (`is_path_or_empty`)

Post-patch repo code (`sphinx/cmd/quickstart.py:98-101`, the gold-added function):
```python
def is_path_or_empty(x: str) -> str:
    if x == '':
        return x
    return is_path(x)
```

Lean impl (`implementation_validateRootEntry`):
```lean
def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok x
    return checkExistingDir x
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `x : String` | `x: str` parameter | **R** | identity string refinement (`str` ↔ Lean `String`). |
| 2 | result `: Except String String` | the validator's outcome: returned string vs. raised `ValidationError` | **R** | `return s` ↔ `.ok s`; `raise ValidationError(msg)` ↔ `.error msg` (mapping.md bijection). Encodes the return-vs-raise distinction `do_prompt` keys on. |
| 3 | `if x == "" then return Except.ok x` | `if x == '': return x` | **I** (deep model of the changed op) | **the fixed operation** (the gold-added empty-acceptance branch). An empty entry is returned verbatim; modeled deeply as `.ok x` (= `.ok ""`), never axiomatized (SPEC_GUIDE §3). G-CONF differential-tests it. |
| 4 | `return checkExistingDir x` | `return is_path(x)` | **A-reference** | the unchanged existing-directory validator `is_path`, delegated to for non-empty entries. Appears identically in spec and impl, so it cancels in the differential; validated == real callee by G-AX (here a skip stub, since the proof consumes no property of it and G-CONF holds it shared). |

The impl region is **not all-A-tagged** (op #3 is a deeply-modeled R/I op), so
`conf_skip = false`: `conformance_check.py` differential-tests the empty-vs-delegate
routing against an in-process replica of the post-patch `is_path_or_empty`, with
the existing-directory validator stood-in identically in oracle and shadow.

## Soundness check (verify ⟹ correct)

- `problem_spec_validateRootEntry x result` pins BOTH cases to the input:
  `x = "" → result = Except.ok x` (the new behavior) AND
  `x ≠ "" → result = checkExistingDir x` (the preserved delegation). Directive 5
  (frame): there is no unconstrained branch — both the empty and non-empty
  outcomes are fixed. Directive 8: the postcondition is grounded in the input
  (`x`, and `checkExistingDir x` applied to the actual input), not an opaque
  answer-key; the result must be *produced by* the empty-check + delegation.
- The prepatch impl (`return checkExistingDir x` for every `x`) violates the spec
  on the discriminating clause `x = ""`: the spec requires `Except.ok ""` but the
  prepatch yields `checkExistingDir ""` (which, like the real `is_path('')`,
  raises → `.error …`). `checkExistingDir` is opaque, so `checkExistingDir "" =
  Except.ok ""` is not provable; the carried gold proof cannot close the `x = ""`
  branch (G-DIFF/G-PANEL).
- This discriminating case is exactly the FAIL_TO_PASS test
  `tests/test_quickstart.py::test_exits_when_existing_confpy`: with an existing
  `conf.py` (mocked `path.isfile → True`), the user enters `''` at the new-root-path
  prompt; the test asserts `SystemExit`. Pre-patch the empty entry was rejected by
  `is_path` and `do_prompt` re-prompted, so the `sys.exit(1)` guard was never
  reached; post-patch the empty entry returns `''`, the guard fires, and the
  process exits.

## Why no consumed axiom

`is_path_or_empty` adds an empty-string short-circuit and otherwise delegates to
the UNCHANGED `is_path`. The changed decision (accept empty) is modeled deeply as
a direct `.ok x` write — never axiomatized. `is_path` is an A-reference: it occurs
identically in the spec's non-empty clause and the impl's non-empty branch, so it
cancels in the differential and the proof needs no property of it (the empty
branch is discharged structurally; the non-empty branch is a syntactic identity).
Hence the `axioms` region declares only the `opaque checkExistingDir` signature
(so the callee can appear in the executable impl) and no `axiom … _prop`;
`axiom_check.py` is a skip stub (G-AX = skip). G-CONF is the primary differential
for the modeled routing.
