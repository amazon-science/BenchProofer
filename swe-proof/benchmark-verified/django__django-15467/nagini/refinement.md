# refinement.md — django__django-15467

The operation-by-operation correspondence between `model.py`'s implementation
(the `set_radio_empty_label` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed** / **A-reference**), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The empty-choice assignment — `formfield_for_foreignkey` (`django/contrib/admin/options.py:272`)

Gold hunk:
```
- kwargs["empty_label"] = _("None") if db_field.blank else None
+ kwargs["empty_label"] = (
+     kwargs.get("empty_label", _("None")) if db_field.blank else None
+ )
```

| # | model.py impl op (`set_radio_empty_label`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `permits_empty: bool` | `db_field.blank` | R | the relation's "permits empty" boolean; identity on the bool (mapping.md §2). |
| A2 | `if permits_empty:` … `else: value = absent_label()` | `… if db_field.blank else None` | I + R | the same conditional; the `else` arm assigns the absent sentinel. `None` ↔ `absent_label()` (R, mapping.md §2). |
| A3 | `if empty_label_key() in kwargs: value = kwargs[empty_label_key()] else: value = default_label()` | `kwargs.get("empty_label", _("None"))` | R | `dict.get(key, default)` spelled out deeply: present value (by membership) kept verbatim, else the default. `"empty_label"` ↔ `empty_label_key()`; `_("None")` ↔ `default_label()` (mapping.md §2). The unchanged language primitive `dict.get` is modeled deeply, not axiomatized — there is no consumed/referenced axiom. |
| A4 | `kwargs[empty_label_key()] = value` | `kwargs["empty_label"] = …` | R | the assignment to the empty-choice entry; `"empty_label"` ↔ `empty_label_key()` (mapping.md §2). |
| A5 | `return value` / postcondition `kwargs[empty_label_key()] == Result()` | the value subsequently forwarded by `db_field.formfield(**kwargs)` and observed as `ff.empty_label` | R | the observable is the mapping's empty-choice entry at call time (mapping.md §2). |
| A6 | frame postcondition `Forall(int, lambda k: Implies(k != empty_label_key(), ((k in kwargs) == Old(k in kwargs)) and Implies(Old(k in kwargs), kwargs[k] == Old(kwargs[k]))))` | the modeled assignment touches ONLY the empty-choice entry; every other entry of the mapping subsequently splatted into `db_field.formfield(**kwargs)` is left exactly as the caller accumulated it | I + R | the real code's only write in this slice is to the one key; because the WHOLE mapping is forwarded downstream, every other key/value pair is runtime-observable (an extra or altered entry changes — or crashes — the built field), so the spec must pin the rest of the mapping unchanged. |

The discriminating content of the change lives in step **A3**: under the
pre-patch code the empty-choice entry is set to `_("None")`
**unconditionally** whenever `db_field.blank`, discarding a caller-supplied
value; under the gold it is `kwargs.get("empty_label", _("None"))`, which keeps
a caller-supplied value when the key is present. `model_prepatch.py` reproduces
the pre-patch skeleton (`value = default_label()` unconditionally in the
permits-empty branch) and **fails** the postcondition

```
Implies(permits_empty and Old(empty_label_key() in kwargs),
        Result() == Old(kwargs[empty_label_key()]))
```

which is exactly the spec sensing the change (G-DIFF). The F2P test
`test_radio_fields_foreignkey_formfield_overrides_empty_label` exercises this
clause: `formfield_overrides` populates `kwargs["empty_label"] = "Custom empty
label"` before the radio branch, and `Inventory.parent` has `blank=True`
(permits empty), so the result must be the caller's label — the post-patch
behaviour, not the pre-patch default.

The PASS_TO_PASS test `test_radio_fields_ForeignKey` exercises the
`not permits_empty` arm (a `blank=False` relation with no caller override): the
result is the absent sentinel (`ff.empty_label is None`) under both pre- and
post-patch, preserved by the spec clause
`Implies(not permits_empty, Result() == absent_label())`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
choice of empty-choice label — is modeled **deeply** (the spelled-out
membership test + dict read in the impl, step A3), not hidden behind an axiom.
There is **no consumed axiom** and **no deep-model reference**: `dict.get` is an
unchanged language primitive recomposed deeply, so there is no `@ContractOnly`
and no `axiom_check.py` / G-AX obligation.

## C. verify(model) ⇒ resolved

`set_radio_empty_label` verifies only if (i) when the relation forbids empty,
the entry is the absent sentinel (A2); (ii) when the relation permits empty and
the caller supplied the key, the entry is the caller's value verbatim (A3,
the discriminating clause); (iii) when permitted and absent, the built-in
default is used (A3); and (iv) every OTHER entry of the mapping is left
untouched — no key added, removed, or revalued (A6, the frame clause). By R
(bool identity, `None` ↔ absent sentinel, `"empty_label"` ↔ the key token,
`_("None")` ↔ default, `dict.get` ↔ membership/index) the verified function
equals the gold assignment on every input, **on the whole mapping**: the
empty-choice entry is pinned exactly (i–iii) and the rest of the mapping is
pinned unchanged (iv), which matters because the entire mapping is splatted
into the downstream field constructor, making every entry observable.
Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
