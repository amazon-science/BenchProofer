# refinement.md — pytest-dev__pytest-8399

Operation-by-operation correspondence between `implementation_generatedFixtureName`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `name=` f-string in
`_make_xunit_fixture`). Tags: **R** type refinement, **A-consumed** proof uses an
axiom, **A-reference** deep model validated == real callee, **I** identical
concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `name := name ++ "_".toList` | the patch's prepended `_` in `name=f"_unittest_…"` | I (the fix: prepend the private marker) |
| 2 | `name := name ++ "unittest_".toList` | the literal `unittest_` of the f-string | I |
| 3 | `name := name ++ setupName` | the f-string field `{setup_name}` | R (`str` ↔ `List Char`, per code point) |
| 4 | `name := name ++ "_fixture_".toList` | the literal `_fixture_` of the f-string | I |
| 5 | `name := name ++ qualname` | the f-string field `{obj.__qualname__}` | R (`str` ↔ `List Char`, per code point) |

Notes:

- **Every step is R or I — no A.** The name is built purely from string literals
  and the two inputs by concatenation; there is no unchanged repo callee in the
  modeled op, so the `axioms` region is empty and **G-AX skips**.
- The **fix** is op #1: prepending the single `_` private marker. The pre-patch
  impl (`Solution_prepatch.lean`) drops op #1, producing the bare descriptive
  name `descriptiveName setupName qualname` with no leading underscore — exactly
  the bug (the generated fixture is not private, so it shows in the default
  `--fixtures` listing). Its `correct_*` cannot close against the spec
  `result = '_' :: descriptiveName …`, which is the G-DIFF signal.
- **Frame discipline (§0.5):** the spec pins the FULL result —
  `'_' :: descriptiveName setupName qualname` — so every component (the leading
  marker, both template literals, and both inputs in order) is constrained; no
  output component is left free for a wrong impl to fill.
- The gold patch applies the same `name → "_" + name` edit at five sites (four
  in `python.py`, one in `unittest.py`). The single modeled triple captures this
  uniform transformation; G-CONF fuzzes arbitrary template/qualname inputs, so it
  covers the behavior of all five sites (each is the identical concatenation with
  a leading `_`).
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the post-patch f-string over
  ≥1e5 fuzzed `(setupName, qualname)` inputs.
