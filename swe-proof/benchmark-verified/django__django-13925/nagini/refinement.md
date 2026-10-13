# refinement.md — django__django-13925

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_default_pk` impl region and the pure predicate `advisory_warranted`
/ `reuses_ancestor_declared_key` it is pinned to) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** (the proof uses an
axiom's `Ensures`), **A-reference** (a model construct is validated == the real
operation by axiom_check.py / G-AX, NOT consumed as an axiom), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The check site — `Model._check_default_pk()` (`django/db/models/base.py:1298`)

Gold hunk (the only hunk):
```
      if (
          cls._meta.pk.auto_created and
+         # Inherited PKs are checked in parents models.
+         not (
+             isinstance(cls._meta.pk, OneToOneField) and
+             cls._meta.pk.remote_field.parent_link
+         ) and
          not settings.is_overridden('DEFAULT_AUTO_FIELD') and
          not cls._meta.app_config._is_default_auto_field_overridden
      ):
```

| # | model.py impl op (`check_default_pk`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `pk.auto` | `cls._meta.pk.auto_created` | R | a `bool` field read on the pk descriptor reduced to `PkField.auto` (mapping.md §2). Identity on the boolean. |
| A2 | `pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b` | `isinstance(cls._meta.pk, OneToOneField) and cls._meta.pk.remote_field.parent_link` | A-reference + R | `isinstance(..., OneToOneField)` is reduced to its boolean result `pk.reuses_ancestor_key_a`; `remote_field.parent_link` to `pk.reuses_ancestor_key_b` (the two abstract reuse flags). There is **no consumed axiom**: the operation is a boolean conjunction spelled out directly. The bijection (and that the auto-created inherited key carries both flags True) is validated == the real configuration by `axiom_check.py` over the full 2**5 truth table (G-AX), NOT consumed as a `@ContractOnly` contract. (mapping.md §3.) |
| A3 | `not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b)` | `not ( isinstance(...) and ...parent_link )` | I | the boolean negation of the new conjunct — the suppression of the advisory when the key re-uses the ancestor's declared key. Identical logical structure. |
| A4 | `not setting_overridden` | `not settings.is_overridden('DEFAULT_AUTO_FIELD')` | R | a global-state boolean read modeled as a parameter (mapping.md §2). Identity on the boolean. |
| A5 | `not appconfig_overridden` | `not cls._meta.app_config._is_default_auto_field_overridden` | R | a `bool` attribute read modeled as a parameter (mapping.md §2). Identity on the boolean. |
| A6 | the four-way `and` guarding `return 1` vs `return 0` | the `if (...)` guarding `return [Warning(... id='models.W042')]` vs `return []` | R + I | the `and`-chain is identical control flow; the returned singleton list ↔ count 1 and the empty list ↔ count 0 (mapping.md §2: the warning content is constant and identical pre/post-patch, so only the count is observable). |

The discriminating content of the change — suppressing the advisory exactly
when the auto-created primary key **re-uses a concrete ancestor's declared
key** — lives in the added conjunct
`not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b)` (A2/A3), which the
spec pins through the pure predicate `advisory_warranted` (via
`reuses_ancestor_declared_key`). The pre-patch guard lacks this conjunct;
`model_prepatch.py` reproduces that (drops the
`not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b)` term) and
**fails** the postcondition `(Result() == 1) == advisory_warranted(...)` —
exactly the spec sensing the change (G-DIFF). The failing assignment is
`(auto, reuses_ancestor_key_a, reuses_ancestor_key_b) = (True, True, True)`, no
overrides: the inherited ancestor-key-reusing key on which the prepatch wrongly
returns 1 while the spec demands 0.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding the ancestor-key-reuse suppression conjunct — is modeled
**deeply** as the spelled-out boolean predicate
`reuses_ancestor_declared_key(...)` consumed inside `advisory_warranted`, not
hidden behind any axiom about the function under change. There is **no consumed
`@ContractOnly` axiom** in this bundle. The only non-trivial refinement —
reducing `isinstance(pk, OneToOneField)` and the attribute reads to booleans —
is an **A-reference** (the field bijection, validated exhaustively by G-AX
against the real branch condition and Django's own auto-created inherited-key
field construction), §3 of mapping.md.

## C. verify(model) ⇒ resolved

`check_default_pk` verifies only if its returned count equals 1 exactly when the
advisory is warranted — i.e. for an auto-created key that does NOT re-use a
concrete ancestor's declared key, with neither override configured (the
postcondition `(Result() == 1) == advisory_warranted(...)`). By R (boolean
field/attribute reads ↔ `PkField` flags and parameters; singleton-list-vs-empty
↔ count) the verified check equals the patched `_check_default_pk` on every
input configuration; by G-AX (axiom_check.py) the model predicate
`advisory_warranted` equals the real branch condition on the full 2**5 truth
table, and Django's auto-created inherited key is exactly the
`(auto, reuses_ancestor_key_a, reuses_ancestor_key_b) = (True, True, True)` case
the new conjunct suppresses. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited field bijection — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(here the A-reference field bijection, G-AX) and refinement fidelity (this
document, G-EQ).
