# refinement.md — sphinx-doc__sphinx-9711

Maps every operation in `implementation_verifyExtensionVersions` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

| # | Lean impl op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `for (req, loaded) in entries` | `for extname, reqversion in config.needs_extensions.items()` + `extension = app.extensions.get(extname)` | R | The Python dict-iteration + dict-get is refined to iterating a `List (String × Option String)` where the second component already carries `extension.version` (`some v`) or absence (`none`). The `extname` key and warning side-effect for the unloaded case are dropped (R: only the version-check behavior is observable; an unloaded extension never raises). mapping.md §type-bijection. |
| 2 | `match loaded with \| none => pure ()` | `if extension is None: logger.warning(...); continue` | R | extension-not-loaded ⇒ no failure for this entry (the warning is a non-observable side effect w.r.t. the raise behavior under spec). |
| 3 | `let mut fulfilled := true` | `fulfilled = True` | I | identical control variable. |
| 4 | `if ver == "unknown version" then fulfilled := false` | `if extension.version == 'unknown version': fulfilled = False` | I | identical sentinel test. |
| 5 | `match parseVersion req, parseVersion ver with \| some a, some b => if verGt a b then fulfilled := false` | `try: if Version(reqversion) > Version(extension.version): fulfilled = False` | A-reference | **Deep model of the fixed behavior.** `parseVersion`+`verGt` reproduce `packaging.version.Version(_) > Version(_)` over the admitted (ASCII) domain: blanks, ASCII case folding, a leading `v`, an era marker (`N!`), the dotted release with trailing-zero equality, the pre/revision/development qualifier tags, and the `+` build tag (mapping.md §deep model). Validated == real callee by G-AX (axiom_check.py). NOT axiomatized — it is the operation the patch changed, so modeled deeply (SPEC_GUIDE §3). |
| 6 | `\| _, _ => if stringGt req ver then fulfilled := false` | `except InvalidVersion: if reqversion > extension.version: fulfilled = False` | A-reference | Models the `InvalidVersion` fallback: when either operand is not a readable version, fall back to Python `str.__gt__` (lexicographic by code point). `parseVersion = none` ⟺ the callee raises `InvalidVersion`, measured over the admitted domain. Validated by G-AX. |
| 7 | `if !fulfilled then return some idx` | `if not fulfilled: raise VersionRequirementError(...)` | R | The raise (first failing extension) is refined to returning `some idx`, the 0-based index of the first unmet entry. The error message arguments are non-behavioral w.r.t. resolve. |
| 8 | `return none` (loop falls through) | function returns `None` implicitly | I | no entry unmet ⇒ no raise. |

## Soundness self-audit
- No op is changed-yet-inexpressible: the changed comparison (op 5/6) is modeled
  deeply, not axiomatized. No dead `axiom` is shipped (axioms region is empty).
- The R legs (ops 1,2,7) are mechanically refuted by G-CONF (conformance_check.py
  builds the same first-unmet-index shadow and diffs vs the patched Python).
- The A-reference legs (ops 5,6) are validated by G-AX (axiom_check.py runs the
  real `packaging.version.Version` comparison, the string fallback, and the
  composed per-entry decision against the deep model over the boundary + fuzz
  domain). That validation covers exactly the domain the correctness theorem
  admits (`problem_pre_verifyExtensionVersions`: ASCII version strings); the one
  excluded class, and why the callee is not stable there, is stated in
  mapping.md §admitted-domain and in the spec's own `pre-conditions` region.
- conf_skip = false (the impl region is not all-A-tagged; ops 1,2,3,4,7,8 are R/I).
