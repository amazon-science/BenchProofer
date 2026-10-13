# refinement.md — operation correspondence (psf__requests-1724)

Each op of `implementation_normalizeMethod` ↔ its `patch.diff` counterpart.
Tags: **R** type refinement, **A-consumed** axiom property consumed by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

Modeled function: the request-method normalization at the top of
`Session.request` (`requests/sessions.py:311-313`). See mapping.md.

| # | Lean op (`implementation_normalizeMethod`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut m := method` | the incoming `method` parameter of `Session.request` | I | bind the supplied method name. |
| 2 | `m := { m with wide := false }` | `method = builtin_str(method)` (added line, `sessions.py:312`) | R | `builtin_str(...)` coerces a text string to the *native* string type. Modeled deeply as clearing the `wide` flag; identity on code-point content for ASCII method tokens (mapping.md domain note). This is the operation the patch ADDS — modeled deeply, never axiomatized. |
| 3 | `m := { m with chars := m.chars.map Char.toUpper }` | `method.upper()` inside `Request(method = method.upper(), …)` (`sessions.py:316`, unchanged by patch) | R | `str.upper()` ⟷ `List.map Char.toUpper` over the code points. On the ASCII method-token domain the two agree code-point-for-code-point, length preserving (mapping.md domain note). Unchanged callee, modeled deeply, exercised end-to-end by G-CONF. |
| 4 | `return m` | the normalized value stored as `req.method` / carried into the assembled request | I | the stored method. |

Every modeled op is **R** or **I**. There are **no A-consumed axioms** and **no
A-reference** callees: both `builtin_str` (added) and `str.upper` (unchanged) are
modeled deeply, so no `opaque`/`axiom` callee contract is needed. `axiom_check.py`
is therefore a skip stub.

There is no changed-inexpressible op: the entire fix is the insertion of the
native-coercion step before the upper-casing, modeled deeply by clearing the
`wide` flag.

## Order of operations note (faithfulness)
The patch coerces FIRST (`method = builtin_str(method)`) then upper-cases
(`method.upper()`). The impl mirrors that order: clear `wide` (op 2) then map
`Char.toUpper` (op 3). The two operations are independent (one touches `wide`,
the other `chars`), so the order is irrelevant to the result, but the skeleton
follows the patch's order regardless.

## conf_skip
`conf_skip = false` — the impl region is all-R/I (no A-tagged ops). G-CONF
differential-tests the runtime-observable leg (uppercased content + native type)
against the real patched `Session.request` over the ASCII domain. The Py2-only
`wide`-flag discriminator is not runtime-observable on the Python-3.9 testbed
(`builtin_str is str`); it is pinned by the spec and enforced by G-DIFF (the
prepatch fails to typecheck on the `result.wide = false` clause). See mapping.md.
