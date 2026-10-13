# refinement.md — pallets__flask-5014

The operation-by-operation correspondence between `Solution.lean`'s
`validateBlueprintName` impl region and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; bijection stated), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The name-validation prologue — `Blueprint.__init__` (`src/flask/blueprints.py:172`)

Gold hunk (inserted between the `super().__init__(...)` call and the existing
dot check):
```
             root_path=root_path,
         )

+        if not name:
+            raise ValueError("'name' may not be empty.")
+
         if "." in name:
             raise ValueError("'name' may not contain a dot '.' character.")
```

| # | Solution.lean impl op (`validateBlueprintName`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `s : List Char` parameter | `name: str` argument of `__init__` | R | `str` ↔ `List Char` of code points (mapping.md §2). |
| A2 | the `while` loop over `s` accumulating `hasDot` + `return !s.isEmpty && !hasDot` | the two reject guards: `if not name: raise ValueError(...)` and `if "." in name: raise ValueError(...)`, with fall-through = construct | R + I | the loop computes `containsDot s` by a backward per-code-point fold (`hasDot = containsDot (s.drop i)` invariant); the returned `!s.isEmpty && !hasDot` is the conjunction of the two post-patch accept conditions. `out = true` (accept) ↔ falling through both guards to build the object; `out = false` (reject) ↔ one of the two `ValueError` raises. See A3/A4 for the per-guard correspondence. |
| A3 | the `!s.isEmpty` conjunct | `if not name: raise ValueError("'name' may not be empty.")` | R + I | **the added guard.** `not name` (Python `str` falsiness) ↔ `s.isEmpty`: a `str` is falsy iff it is `""`, i.e. zero code points (mapping.md §2). Reject-on-empty ↔ the `!s.isEmpty` conjunct being `false` for `s = []`. |
| A4 | the `!hasDot` conjunct (`hasDot = containsDot s` at loop exit) | `if "." in name: raise ValueError("'name' may not contain a dot '.' character.")` | R + I | pre-existing dot check, unchanged by the patch. `"." in name` (single-char membership) ↔ `'.' ∈ s` ↔ `containsDot s` (mapping.md §2). Reject-on-dot ↔ the `!hasDot` conjunct being `false`. |
| A5 | `out = true` (the `return` value when both conjuncts hold) | falling through both guards to `self.name = name; ...` (construction proceeds) | R | normal completion of the validation prologue. The model abstracts the subsequent unchanged field assignments to the accept verdict `true`: they are unchanged by the patch and not observed by this decision spec. The only thing the prologue decides is accept vs reject. |

No base-initialiser op appears in the impl region: `super().__init__(...)` →
`Scaffold.__init__` runs *before* the decision, is unchanged by the patch, is
independent of `name`, and observes no state this spec measures, so it is
abstracted away (mapping.md §3) — it is neither an R/I op of the modeled decision
nor a consumed axiom.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
empty-name rejection (A3) — is modelled **deeply and exactly** (`s.isEmpty` is the
precise refinement of `not name` for a `str`; the conjunction with the unchanged
dot check is the post-patch decision), not hidden behind an axiom about the
function under change. There is **no consumed axiom, no A-reference deep model,
and no dead axiom** (the `axioms` region is empty; G-AX skips).

The discriminating content of the change is step **A3** — the new empty-name
guard. The spec senses it through `ensures out = validName s` with
`validName s = !s.isEmpty && !containsDot s`: on the empty (and dot-free) input
`s = []`, `validName [] = false`, so any verifying impl must reject it. The
pre-patch constructor had no A3; `Solution_prepatch.lean` omits the `!s.isEmpty`
conjunct (returns `!hasDot`) and **fails** the postcondition on `s = []` — the
exit goal reduces to `i_1 = false → ¬s = []`, i.e. "a dot-free empty name must be
rejected", which is unprovable for the empty list. That is exactly the spec
sensing the change (G-DIFF), and exactly the behaviour the sole F2P test,
`tests/test_blueprints.py::test_empty_name_not_allowed`
(`flask.Blueprint("", __name__)` must raise `ValueError`), demands.

## C. verify(model) ⇒ resolved

`validateBlueprintName` returns `true` (accept) iff `!s.isEmpty && !containsDot s`
and `false` (reject) otherwise (the single `ensures`). Under R (`str` ↔
`List Char`, `not name` ↔ `s.isEmpty`, `"." in name` ↔ `containsDot s`,
`ValueError`-raise ↔ `out = false`) this is precisely the post-patch
constructor's name decision: reject empty or dotted names with a `ValueError`,
otherwise proceed. The base initialiser that runs first is unchanged and
independent of `name`, so it cannot affect the decision. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The R/I legs are
mechanically refuted by G-CONF (`conformance_check.py`); there are no A legs.
