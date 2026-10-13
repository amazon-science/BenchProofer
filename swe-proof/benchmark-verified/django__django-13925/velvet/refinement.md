# refinement.md — django__django-13925

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `implicitPrimaryKeyAdvisory` `do` block) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee:
A-consumed / A-reference), or **I** (identical concrete op). EVERY step is R, A,
or I — no kind-3 (inexpressible changed op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics:** the file pins
`set_option loom.semantics.termination "total"` (TotalCorrectness). The real
`_check_default_pk` is a straight-line boolean guard that always terminates,
so a diverging implementation (e.g. an infinite loop before returning) must
NOT satisfy the spec. Under the earlier `"partial"` setting a `while true`
body vacuously verified (an admitted-wrong-impl attack); total correctness
closes that hole. The `set_option` lines live in the spec view, so a
same-spec attacker cannot switch the semantics back.

## A. The advisory-gate site — `_check_default_pk()` (`django/db/models/base.py:1298`)

Gold hunk (the `if` guard of `_check_default_pk`):
```
  if (
      cls._meta.pk.auto_created and
+     # Inherited PKs are checked in parents models.
+     not (
+         isinstance(cls._meta.pk, OneToOneField) and
+         cls._meta.pk.remote_field.parent_link
+     ) and
      not settings.is_overridden('DEFAULT_AUTO_FIELD') and
      not cls._meta.app_config._is_default_auto_field_overridden
  ):
      return [ checks.Warning( ... id='models.W042' ) ]
  return []
```

| # | Solution.lean impl op (`implicitPrimaryKeyAdvisory`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `pkAutoCreated : Bool` | `cls._meta.pk.auto_created` | R | bool ↔ `Bool`, exact (mapping.md §2). Free boolean input to G-CONF. |
| A2 | param `pkInheritedFromAncestor : Bool` | `isinstance(cls._meta.pk, OneToOneField) and cls._meta.pk.remote_field.parent_link` | R | the whole `isinstance(...) and ...parent_link` sub-expression is one boolean "the PK is the inherited parent-link key" ↔ `Bool`, exact (mapping.md §2). This is the conjunct the patch ADDS. |
| A3 | param `defaultKeyTypeConfigured : Bool` | `settings.is_overridden('DEFAULT_AUTO_FIELD')` | R | bool ↔ `Bool`, exact (mapping.md §2). |
| A4 | param `appKeyTypeConfigured : Bool` | `cls._meta.app_config._is_default_auto_field_overridden` | R | bool ↔ `Bool`, exact (mapping.md §2). |
| A5 | `out = (pkAutoCreated && !pkInheritedFromAncestor && !defaultKeyTypeConfigured && !appKeyTypeConfigured)` | the 4-operand `if (... and not(...) and not ... and not ...)`, returning `[W042]` vs `[]` | I | identical concrete boolean op: Python `and`/`not` over the four pure boolean tests ↔ Lean `&&`/`!`; `out=true` ↔ guard holds ↔ `[Warning(... id='models.W042')]`, `out=false` ↔ `[]` (mapping.md §2). |

The added conjunct `not (isinstance(pk, OneToOneField) and pk.remote_field.parent_link)`
(model: `&& !pkInheritedFromAncestor`) is the entire behavioural change. The
emitted `Warning`'s message/hint/`obj` are produced unconditionally once the
guard fires and are unchanged by the patch (mapping.md §2); the F2P tests
discriminate only on advisory present vs absent, i.e. on `out`.

Discriminating content: when `pkAutoCreated = true`, `pkInheritedFromAncestor =
true`, and both config flags `false` — the inherited-PK case the issue reports —
the post-patch guard yields `out = false` (no advisory), whereas the pre-patch
guard (missing the conjunct) yields `out = true`. `Solution_prepatch.lean`
reproduces the pre-patch guard and **fails** `out = (... && !pkInheritedFromAncestor && ...)`
exactly there (G-DIFF). This is the FAIL_TO_PASS pair
`test_auto_created_inherited_pk` / `test_explicit_inherited_pk`.

## B. No axiomatized callees

There is no A-consumed axiom and no A-reference deep model. Every operand is a
direct boolean observation of already-resolved model metadata; the patch calls
no helper and changes no callee (mapping.md §3). Hence no `axiom_check.py` and
`G-AX = skip`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — adding the
`!pkInheritedFromAncestor` conjunct to the guard — is a pure boolean op modeled
**directly** (step A5, an I leg over an R-refined boolean input A2), not hidden
behind an axiom about the routine under change. There is no consumed axiom.

## D. verify(Solution) ⇒ resolved

`implicitPrimaryKeyAdvisory` verifies only if its output equals the exact
four-operand conjunction with the `!pkInheritedFromAncestor` conjunct present
(A5). By R (each operand's bool ↔ `Bool` bijection, mapping.md §2) the verified
decision equals the patched guard's truth value on every model; by the
list-shape bijection, `out = true` ↔ the model emits `[W042]` and `out = false`
↔ `[]`. G-CONF confirms the R/I transliteration of the post-image boolean
expression agrees with the patched guard over all 16 boolean combinations plus
fuzz. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
sole trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms (G-AX skip).
