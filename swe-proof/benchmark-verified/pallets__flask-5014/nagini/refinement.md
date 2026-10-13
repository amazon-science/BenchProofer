# refinement.md — pallets__flask-5014

The operation-by-operation correspondence between `model.py`'s implementation
(the `validate_name` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The validation prologue — `Blueprint.__init__` (`src/flask/blueprints.py:172`)

Gold hunk (inserted between the `super().__init__(...)` call and the existing
dot check):
```
         )

+        if not name:
+            raise ValueError("'name' may not be empty.")
+
         if "." in name:
             raise ValueError("'name' may not contain a dot '.' character.")
```

| # | model.py impl op (`validate_name`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `name: List[int]`, `import_name: List[int]` parameters | `name: str`, `import_name: str` arguments of `__init__` | R | `str` ↔ `List[int]` of code points (mapping.md §2). |
| A2 | `init_base(import_name)` | `super().__init__(import_name=import_name, ...)` → `Scaffold.__init__` (`blueprints.py:185`) | A-consumed | the unchanged base initialiser, invoked first and independent of `name`. The proof consumes its sound contract: it either returns normally, handing back the `import_name` permission for the subsequent guards together with the SUCCESS witness `base_init_can_complete(import_name)`, OR fails as a unit, handing back the permission with the FAILURE witness (`Exsures(BaseInitError, … base_init_can_fail(import_name))`), which `validate_name` propagates under its own matching `Exsures(BaseInitError, … base_init_can_fail(import_name))` — faithful to the real constructor aborting before name validation when `get_root_path` raises (mapping.md §3.1–3.2). The contract does not say WHICH exit a given `import_name` takes, because the real callee does not decide that from `import_name` alone (mapping.md §3.2). It validates no name, so it cannot pre-empt the checks below; and because the name guards run strictly after a NORMAL return, the only witness in scope where they raise is the success one, so a name reject is forced onto the `NameValidationError` channel (mapping.md §3.2). On the tested oracle `import_name = __name__` the base init completes, so the failure path is never hit and the normal `Ensures` post is the one consumed. |
| A3 | `if len(name) == 0: raise NameValidationError()` | `if not name: raise ValueError("'name' may not be empty.")` | R + I | **the added guard.** `not name` (Python `str` falsiness) ↔ `len(name) == 0`: a `str` is falsy iff it is `""`, i.e. zero code points (mapping.md §2). The `raise ValueError` ↔ `raise NameValidationError()`: one user-defined exception models the single `ValueError` (builtin-exception `Exsures` crashes Nagini; mapping.md §2). The control flow (test-then-raise, before the dot check) is identical. |
| A4 | `if contains_dot(ToSeq(name)): raise NameValidationError()` | `if "." in name: raise ValueError("'name' may not contain a dot '.' character.")` | R + I | pre-existing dot check, unchanged by the patch. `"." in name` (single-char membership) ↔ `46 ∈ name` ↔ `contains_dot(ToSeq(name))` (mapping.md §2). Same user-exception refinement as A3. |
| A5 | `return` (normal completion) | falling through to `self.name = name; ...` (the constructor proceeds to build the object) | R | normal completion of the validation prologue. The model abstracts the subsequent unchanged field assignments (`self.name = name`, `self.url_prefix = ...`, registries) to a bare `return`: they are unchanged by the patch and not observed by this validation spec; the only thing the prologue decides is accept (return / proceed) vs reject (raise). |

The base-init failure path (A2's `Exsures(BaseInitError, …
base_init_can_fail(import_name))`) does NOT weaken the discriminating content: it
carries no `len`/`dot` constraint and is reached only when the base init fails as a
unit *before* any name check — it is a faithful pass-through of the real
constructor's pre-validation abort, not a relaxation of the accept/reject decision.
The channel is pinned by the PROVENANCE of two independent A-reference witnesses
(mapping.md §3.2): `Exsures(NameValidationError, … base_init_can_complete(import_name)
and (len==0 or dot))` — a reject runs only after `init_base` RETURNED, which is the
only place the success witness comes from — versus `Exsures(BaseInitError, …
base_init_can_fail(import_name))`, whose witness only a base call that actually
FAILED hands out. A reject therefore *cannot* be surfaced through the base-init
channel: an implementation raising the base-init exception on an empty/dotted name
(after `init_base` returned) has only the success witness in scope, and the success
witness does not imply the failure one — the two are deliberately independent,
because the real base init can do either for one `import_name` (mapping.md §3.2).
This is faithful to the real control flow (name guards run strictly after
`super().__init__` returns) and required by the `pytest.raises(ValueError)`
F2P/P2P. The normal-return guarantees (`Ensures(len(name) > 0)`, `Ensures(not
contains_dot(...))`, `Ensures(base_init_can_complete(import_name))`) and the
`Exsures(NameValidationError, …)` reject set are otherwise unchanged.

The discriminating content of the change is step **A3** — the brand-new
empty-name guard. The spec senses it through `Ensures(len(name) > 0)` (normal
return implies a non-empty name) together with `Exsures(NameValidationError,
len(name) == 0 or contains_dot(...))` (the empty name is in the reject set). The
pre-patch constructor had no A3; `model_prepatch.py` omits it and **fails** the
postcondition `Ensures(len(name) > 0)` — an empty, dot-free name returns
normally — which is exactly the spec sensing the change (G-DIFF). This is the
behaviour the sole F2P test, `tests/test_blueprints.py::test_empty_name_not_allowed`
(`flask.Blueprint("", __name__)` must raise `ValueError`), demands.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — the empty-name rejection (A3) — is modelled **deeply and
exactly** (`len(name) == 0` is the precise refinement of `not name` for a `str`,
and the test-then-raise control flow is identical), not hidden behind an axiom
about the function under change. The consumed axiom, `init_base` (**A-consumed**,
A2), covers the **unchanged** base initialiser `Scaffold.__init__` the new code
delegates to; it is independent of `name` and so provably cannot affect the
validation outcome. The two A-references, `base_init_can_complete` and
`base_init_can_fail` (mapping.md §3.2), are attainability witnesses for the two
outcomes of that **unchanged** base init — they appear only in the contracts (never
called in the impl) and are used solely to pin `init_base`/`validate_name`'s two
exception channels by provenance (so a name reject cannot be routed through the
base-init channel). Their faithfulness — each attainable, both name-silent, and
mutually INDEPENDENT (the real base-init outcome is not a function of
`import_name`) — is validated against the real callee by G-AX / the PBT axiom
lane. No A-reference
or A-consumed axiom touches the function under change, and there is no dead axiom
(both `init_base` posts are load-bearing; dropping `validate_name`'s
`Exsures(BaseInitError, …)` makes the proof FAIL).

## C. verify(model) ⇒ resolved

`validate_name` returns normally only when `len(name) > 0 and not
contains_dot(name)` (the two `Ensures`), and raises `NameValidationError` on
exactly `len(name) == 0 or contains_dot(name)` *with
`base_init_can_complete(import_name)`* (the `Exsures`) — i.e. the name reject is on
the `ValueError` channel, never the base-init channel. Under R
(`str` ↔ `List[int]`, `not name` ↔ `len==0`, `"." in name` ↔ `contains_dot`,
`ValueError` ↔ `NameValidationError`) this is precisely the post-patch
constructor's name-validation behaviour: reject empty or dotted names with a
`ValueError`, otherwise proceed. By A-consumed (G-AX) the real
`Scaffold.__init__` is over-approximated by the `init_base` contract:
it ignores `name` and either completes (`Ensures(base_init_can_complete)`) or fails
as a unit (`Exsures(BaseInitError, base_init_can_fail)`) — the latter modelled
because `get_root_path` → `pkgutil.get_loader` raises on an unresolvable
`import_name`, and left as an ATTAINABILITY claim rather than a decision because
the real outcome also turns on the ambient module table and on the constructor's
optional `root_path` argument (mapping.md §3.2). Because the name guards run only
after `init_base` RETURNS — the sole source of the success witness — a reject is
forced onto the `NameValidationError` channel, so the `pytest.raises(ValueError)`
F2P/P2P hold and no faithful impl can route the reject through
`ImportError`/`RuntimeError`. On the tested oracle `import_name = __name__` the
base init completes, so the name decision is the only observable; the failure path
is latent. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
