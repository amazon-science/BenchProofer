# mapping.md — django__django-16950

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f64fd47a7627ed6ffe2df2a32ded6ee528a784eb`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/forms/models.py` (the inline formset's
`add_fields`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reset_default_related_key(instance, adding, key_has_default, key_is_primary, form_data_present)` | the related-key-clearing block of `BaseInlineFormSet.add_fields` — `django/forms/models.py:1173-1181` | the modeled changed behaviour (the conditional reset of the parent's related-key value) |
| `ParentObject` with field `instance.key` | `self.instance` and its dynamically-named related-key attribute `to_field.attname` reached via `setattr(self.instance, to_field.attname, None)` (`django/forms/models.py:1181`) | the in-memory parent object, with only the one touched field |
| `adding` (bool) | `self.instance._state.adding` (`django/forms/models.py:1175`) | parent object is being added (not persisted) |
| `key_has_default` (bool) | `to_field.has_default()` (`django/forms/models.py:1180`; `Field.has_default`, `django/db/models/fields/__init__.py:1008`) | the resolved related key carries a model-supplied default |
| `key_is_primary` (bool) | `to_field.attname == self.fk.remote_field.model._meta.pk.name` (post-patch guard, `django/forms/models.py:1180-1181`) | the related key IS the parent model's primary identifier |
| `form_data_present` (bool) | `bool(form.data)` (post-patch guard `or not form.data`, `django/forms/models.py:1181`); `form.data` is the bound form's submitted data (`django/forms/forms.py:86`) | submitted form data accompanies the request |
| `should_clear(...)` | the post-patch guard `to_field.has_default() and (to_field.attname == ... or not form.data)` evaluated inside `if self.instance._state.adding:` | pure spec: the full clearing decision |

The resolution of `to_field` itself (`to_field = self.instance._meta.get_field(kwargs["to_field"])` else `self.instance._meta.pk`, `django/forms/models.py:1176-1179`) is unchanged by the patch; it determines WHICH field's `has_default()`/`attname` the booleans refer to and is captured abstractly by the three booleans (the patch does not alter it).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.instance` (a Django model instance) with the dynamically-named related-key attribute `to_field.attname` | `ParentObject` with a single field `key: Optional[int]` | `getattr(self.instance, to_field.attname)` ↔ `instance.key`; the model-generated default value (a UUID) ↔ a concrete non-`None` `int`; the cleared state `None` ↔ `None`. Only the one attribute the patch touches is modelled. |
| `setattr(self.instance, to_field.attname, None)` | `instance.key = None` | identical store of `None` into the related-key attribute (R on the dynamic attribute name). |
| `self.instance._state.adding` (bool) | `adding: bool` | identity. |
| `to_field.has_default()` (bool) | `key_has_default: bool` | identity (the boolean result of the field's default check). |
| `to_field.attname == self.fk.remote_field.model._meta.pk.name` (bool) | `key_is_primary: bool` | identity (the equality is a boolean the patch reads). |
| `bool(form.data)` (a possibly-empty `MultiValueDict` tested for truthiness) | `form_data_present: bool` | identity: `not form.data` ↔ `not form_data_present`; an empty/absent data mapping is falsey, a populated one is truthy. |

The three repository conditions are genuine booleans the patched guard reads;
abstracting them to `bool` parameters is exact (the patch performs no other
computation on them than the boolean combination). The single mutated object
is `self.instance`, modelled with full permission on `instance.key`; the
booleans are read-only scalars (no permission carrier needed).

| the clearing block returns to `add_fields` on every call (it is a bounded, straight-line guard + one `setattr`; no loop or recursion) | `Requires(MustTerminate(2))` on `reset_default_related_key`; `Requires(MustTerminate(1))` on `ParentObject.__init__` (strictly smaller measure, so constructing a probe parent inside a caller holding the obligation is admissible) | total-correctness obligation: the F2P/P2P tests observe the (cleared or preserved) key only because form construction RETURNS. A body that diverges (e.g. `while True: pass`) or re-enters the operation at a non-decreasing measure satisfies the two value postconditions only vacuously and is rejected by Nagini's obligation-leak check. |

## 3. Callee provenance (kind-A)

**None.** This bundle consumes no `@ContractOnly` axiom. The changed operation
is the clearing *decision* itself — a boolean combination of three conditions
the patched guard reads, plus the conditional `setattr(..., None)`. Both are
modelled DEEPLY and concretely (the `should_clear` predicate in the `pure`
region and the guarded `instance.key = None` store in the impl region). There
is no unchanged opaque callee the proof needs to axiomatize:

- `has_default()`, `_state.adding`, `attname`, `_meta.pk.name`, and
  `form.data` are simple attribute/boolean reads whose VALUES are the modeled
  booleans; the patch does not change them and does not depend on their
  internals, so they are abstracted as inputs (R), not axiomatized.
- `InlineForeignKeyField(self.instance, **kwargs)` (`models.py:1183`) and the
  `super().add_fields(form, index)` call (`models.py:1153`) are unchanged by
  the patch and lie OUTSIDE the modeled clearing decision; they are not part
  of the behaviour the F2P/P2P tests of this change observe (the tests observe
  `formset.instance.uuid` / `forms[0].instance.parent_id` — i.e. the value of
  the parent's related key after the formset's forms are constructed). They
  are therefore not modeled and not axiomatized.

Because there is no axiom, `axiom_check.py` performs a behavioural-equivalence
G-AX check instead: it reconstructs the `should_clear` decision table (all 16
boolean combinations) and asserts the modeled decision matches the post-patch
guard's logic `adding and has_default and (is_pk or not data)`, and that it
diverges from the pre-patch guard `adding and has_default` exactly on the
FAIL_TO_PASS case (alternate key + form data). stdlib-only; exit 0 iff sound.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg: it diffs the model's impl
region against the REAL patched repository function.

**Pinned seed: `SEED = 16950`** (module constant; `random.Random(16950)` drives
the fuzz stage). Input count: **100 020** — 16 exhaustive + 4 named boundary +
100 000 fuzz.

| leg | what it is |
|---|---|
| SHADOW | the `# impl-start` / `# impl-end` region of `model.py`, copied verbatim with only the contract calls deleted (`shadow_reset_default_related_key`), plus `ParentObject` and the `# pure-start` helper `should_clear` carried over the same way. No transliteration — on nagini the model IS Python. |
| ORACLE | `django.forms.models.BaseInlineFormSet.add_fields` **called, not transliterated** (§1 binding: `django/forms/models.py:1173-1181`, gold patch applied to /testbed by the gate). Real parent/child models are created with `connection.schema_editor()` over in-memory sqlite3 and real formsets with `inlineformset_factory`; each `add_fields(form, 0)` costs ~45–115 µs, so 1e5 real calls is seconds. The guard is never re-implemented. |

Both sibling bundles (`velvet/`, `lean/`) transliterate the patched block,
justifying it as "we do NOT stand up a Django FormSet / model / ORM (heavy)".
That justification does not hold in this container, so this bundle does **not**
reuse it and drives the real method instead. `to_field` (§1, resolution
unchanged by the patch) is additionally read back out of the real
`InlineForeignKeyField` the real `add_fields` installed into `form.fields`,
keeping our copy of that resolution out of the trust chain.

**Type bridge (§2, inverted).** Each abstraction is realized by a real Django
object rather than a poked flag:

| §2 model carrier | realized concretely as |
|---|---|
| `adding: bool` | `True` ⇐ an unsaved parent (`_state.adding` naturally `True`); `False` ⇐ `parent.objects.create(...)` passed as `instance=` |
| `key_has_default: bool` | `True` ⇐ parent whose related key is `UUIDField(default=uuid.uuid4)` (the F2P shape); `False` ⇐ `AutoField` pk / plain `BigIntegerField` alternate key |
| `key_is_primary: bool` | `True` ⇐ child FK targets the parent pk; `False` ⇐ FK targets a unique non-pk column via `to_field=` |
| `form_data_present: bool` | `True` ⇐ bound formset with a real management-form data dict; `False` ⇐ unbound formset (`form.data` empty/falsey) |
| `instance.key: Optional[int]` | `uuid.UUID(int=k)` for a UUIDField / `int(k)` for an integer column; back-map: `None → None`, planted value `→ k`, **any third value → a poison sentinel that can only mismatch** (so a rewritten key cannot pass as "preserved") |

The four booleans are re-read off the real objects immediately before each call
(`Config.observe`), so the shadow is fed the observables the real guard reads.
`_verify_bridge` asserts all 16 combos are realized and that each config's real
observables equal the combo it is filed under.

**Inputs.** The modeled boolean space is FINITE (2⁴ = 16) and every point is
realized by real Django objects (4 parent/child shapes × adding/saved ×
bound/unbound), so it is **enumerated exhaustively** rather than sampled —
strictly stronger than 1e5 random draws, since no combination is left unvisited.
Each impl branch (outer `if adding` not taken; taken with guard false; taken
with guard true) is hit by construction. Seeded fuzz over the same space
(16 configs × random planted key) then fills the count to ≥ 1e5.

**Positive control.** `_assert_patch_branch_live` makes the patch-discriminating
branch a hard precondition: for the F2P combo (adding + default + alternate key
+ data present) the real oracle must PRESERVE. Pre-patch code clears whenever
`adding and has_default`, so an unpatched /testbed exits 1 rather than recording
a vacuous pass. Verified by three negative controls: (i) running without the
gold patch → the control fires and the script exits 1; (ii) shadow reverted to
the pre-patch guard → 5 disagreements on `ak+default/adding/data`, exit 1;
(iii) shadow with the `key_is_primary` arm dropped → 5 disagreements on
`pk+default/adding/data`, exit 1. Exit 0 iff zero disagreements; stdlib only.
