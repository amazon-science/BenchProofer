# mapping.md — django__django-13964

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f39634ff229887bf7790c069d0c411b38494ca38`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the A-reference.

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fillEmptyKeyRefs (refs : List KeyRef)` | `Model._prepare_related_fields_for_save(self, operation_name)` — `django/db/models/base.py:911` (the `for field in self._meta.concrete_fields:` loop, line 915) | the modeled changed function: reconcile the locally-stored foreign-key value of each cached relation against the key the related object now carries |
| the per-reference decision `resolvedKey` | the `elif … : setattr(self, field.attname, obj.pk)` branch — `django/db/models/base.py:936-939` (post-patch line 936) | pure spec: when the locally-stored key is empty, adopt the related object's key; else keep it |
| `isEmpty` *(deep model — A-reference)* | the membership test `getattr(self, field.attname) in field.empty_values` — `django/db/models/base.py:936` (post-patch); `Field.empty_values = list(validators.EMPTY_VALUES)` — `django/db/models/fields/__init__.py:91`; `validators.EMPTY_VALUES = (None, '', [], (), {})` | pure spec: whether a stored value counts as empty; deep model of the unchanged notion `x in field.empty_values`, validated `isEmpty == (x in field.empty_values)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `KeyRef.stored` | `getattr(self, field.attname)` — the value currently recorded for `field` on the referring object (`base.py:936`); `attname` is e.g. `product_id` | the locally-stored foreign-key value |
| `KeyRef.targetKey` | `obj.pk` — the primary key the related object `obj = getattr(self, field.name)` now carries (`base.py:921`, used at `base.py:938`) | the key to adopt when the stored key is empty |
| `PyVal` | a Python value that can be stored in a model attribute (here: the FK attname value and the related pk) | the model's value carrier; only the four shapes that matter to emptiness are distinguished |

The pre-patch repo content the change replaces (refinement audit only, not in the
consumer spec view): the condition `getattr(self, field.attname) is None`
(`base.py:936` pre-patch), which fires only on the language null, never on an
empty-but-present value such as `''`.

### Scope of the model (what is and isn't reconciled)

`_prepare_related_fields_for_save` first handles, for each cached relation, two
prior cases left UNCHANGED by the patch and therefore outside the modeled
decision:

* `if not obj: continue` (`base.py:919`) — no related object cached → skip.
* `if obj.pk is None:` (`base.py:927`) — related object itself has no key → the
  `raise ValueError(...)` data-loss guard. UNCHANGED.

The patch edits ONLY the third case (`elif`, `base.py:936`), reached exactly when
a related object is cached AND carries a key (`obj.pk is not None`). `refs` models
that filtered set of references, hence the precondition
`∀ r ∈ refs, r.targetKey ≠ pyNone` (every referenced object already carries a
key). The trailing cache-invalidation `if getattr(obj, field.target_field.attname)
!= getattr(self, field.attname): field.delete_cached_value(self)`
(`base.py:940-942`) is UNCHANGED, observes only the resolved stored key the model
already produces, and has no effect the F2P test distinguishes; it is not modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the list of cached FK references reaching the `elif` (one per qualifying `field`) | `List KeyRef` | the `for field in self._meta.concrete_fields` loop, restricted to relation fields whose related object is cached, present, and has a non-`None` pk; order is concrete-field order; `len` ↔ `.length` |
| a stored Python value `v` (the FK attname value `getattr(self, field.attname)` and the related pk `obj.pk`) | `PyVal` | `None ↔ pyNone`; a `str` `s ↔ pyStr s.toList` (so `'' ↔ pyStr []`); a sized collection (`list`/`tuple`/`dict`) of length `n ↔ pyColl n` (so `[],(),{} ↔ pyColl 0`); an `int` `k ↔ pyInt k`. Bijective on the value shapes that occur as primary keys / FK values in this routine. |
| `getattr(self, field.attname)` | `KeyRef.stored` | the locally-stored key, mapped per the `PyVal` bijection |
| `obj.pk` | `KeyRef.targetKey` | the related object's key, mapped per the `PyVal` bijection |
| `setattr(self, field.attname, obj.pk)` performed iff `getattr(self, field.attname) in field.empty_values`, else left unchanged | element of `out = resolvedKeys refs` | the resolved stored key: `targetKey` when `isEmpty stored`, else `stored` |
| `x in field.empty_values` | `isEmpty x` | `field.empty_values` is `[None, '', [], (), {}]` for an ordinary `Field` (`fields/__init__.py:91`, via `validators.EMPTY_VALUES`); `isEmpty` is the structural recognizer of exactly that membership for the `PyVal` shapes — see §3 |

`PyVal` distinguishes only the four shapes whose emptiness differs; that is all the
decision (`x in field.empty_values`) observes. Numeric primary keys (`AutoField`,
`pyInt`) are never empty, matching the pre-existing behaviour for numeric pks; the
empty-string non-numeric primary key (`pyStr []`) is the case the issue is about.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `isEmpty` deep model ↔ `x in field.empty_values` (A-reference)
**Callee:** the membership test `x in field.empty_values` where, for an ordinary
`django.db.models.Field`, `empty_values == list(django.core.validators.EMPTY_VALUES)
== [None, '', [], (), {}]` (`django/db/models/fields/__init__.py:91`). The changed
emptiness decision is modeled **deeply** by `isEmpty` in the `pure` region; there
is **no consumed axiom**. `isEmpty` recognizes:

```
pyNone     -> true     (None  ∈ empty_values)
pyStr []   -> true     (''    ∈ empty_values)        ;  pyStr (_::_) -> false
pyColl 0   -> true     ([],(),{} ∈ empty_values)     ;  pyColl (n>0) -> false
pyInt k    -> false    (no integer ∈ empty_values)
```

This matches `x in field.empty_values` on every value shape that can be an FK
attname value or a related pk: `None`, strings (empty vs non-empty), the empty
collections `[] () {}` (and non-empty ones), and integers. Django evaluates `in`
with `==`; for these disjoint value shapes membership coincides with the
structural test (e.g. `'' == []` is `False`, so an empty string matches only the
`''` entry — still empty; a non-empty string matches no entry — not empty).

**Soundness check (G-AX):** `axiom_check.py` constructs a real ordinary `Field`,
reads its `.empty_values`, and asserts for boundary + fuzzed Python values `v`
that `isEmpty(model(v)) == (v in field.empty_values)` (the A-reference). Imports
only Django (the same package the gold patch lives in) + stdlib. Exit 0 iff sound.

`field.empty_values` lives in `django/db/models/fields/__init__.py:91` and is
**UNCHANGED** by the gold patch (which edits only the `elif` condition in
`base.py`), so this A-reference is sound against the repo G-AX runs in-container,
which is the repo **as-is, without the gold patch applied** (only G-CONF applies
the gold patch).

### 3.2 The empty⇒adopt decision `resolvedKey` is an I-leg, NOT a G-AX A-reference
The per-reference adopt/keep decision (`if isEmpty stored then targetKey else
stored`) is exactly the behaviour the patch installs (`elif … in
field.empty_values: setattr(self, field.attname, obj.pk)`), i.e. **the operation
the patch changes**. Per SPEC_GUIDE §0.7 it must NOT be G-AX-validated against the
real callee: G-AX runs the **unpatched** `_prepare_related_fields_for_save`, whose
`is None` test returns the *old* (buggy) result on an empty-but-present stored key
(`stored='' ⇒ product_id=''`, not the related pk), disagreeing with the spec **by
construction**. That decision is tagged **I** in refinement.md (§A5) and is refuted
instead by **G-CONF**, whose oracle is the repo **with the gold patch applied**
(`apply_gold=True`); G-CONF agrees with the `resolvedKey`/`resolvedKeys` shadow on
100 000 inputs.

There is **no A-consumed axiom**: the routine consults no outside contract. The
unchanged emptiness notion is the lone A-reference (`isEmpty`); the changed
adopt/keep decision is an I-leg under G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13964`** so the
consumer-side verdict (§11.3) is reproducible. It builds the R/I shadow of the
`fillEmptyKeyRefs` `do` block (the per-reference `resolvedKey`/`resolvedKeys`
fold, transliterated to Python over real `PyVal`-shaped values) and diffs it
against `patch.diff`'s behaviour — the patched
`_prepare_related_fields_for_save` driven on a live FK relation at base_commit
with the gold patch applied — over ≥10⁵ fuzzed (stored, target) reference lists.
The decision is DB-free (pure attribute manipulation: set up cached relations,
override the local attname, call the method, read back the attname), so a faithful
input-dependent R/I shadow exists and G-CONF is NOT skipped.
