# refinement.md — django__django-16950

The operation-by-operation correspondence between `model.py`'s implementation
(the `reset_default_related_key` impl region + the `should_clear` pure
predicate) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The clearing decision — `BaseInlineFormSet.add_fields` (`django/forms/models.py:1173-1181`)

Gold hunk:
```
             else:
                 to_field = self.instance._meta.pk
-            if to_field.has_default():
+
+            if to_field.has_default() and (
+                # Don't ignore a parent's auto-generated key if it's not the
+                # parent model's pk and form data is provided.
+                to_field.attname == self.fk.remote_field.model._meta.pk.name
+                or not form.data
+            ):
                 setattr(self.instance, to_field.attname, None)
```

The whole block runs only inside `if self.instance._state.adding:`
(`models.py:1175`, unchanged). The bug: the pre-patch guard
`if to_field.has_default():` cleared the parent's related-key value whenever
the resolved `to_field` carried a default — even when the relation targets a
non-primary alternate key (`to_field.attname != parent pk name`) AND submitted
form data is present. That wrongly nulled the parent's freshly generated
alternate key, so the child could not be related to the parent. The fix
qualifies the clear with `(to_field.attname == ...pk.name or not form.data)`.

| # | model.py impl op (`reset_default_related_key`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `instance: ParentObject` with field `instance.key` | `self.instance` and its related-key attribute reached via `to_field.attname` | R | the in-memory parent object modelled with only its one touched field; the dynamically-named attribute ↔ `instance.key` (mapping.md §1, §2). |
| A2 | `if adding:` | `if self.instance._state.adding:` (`models.py:1175`, unchanged outer guard) | R | the boolean `self.instance._state.adding` ↔ `adding` (mapping.md §2). The outer guard is unchanged by the patch but is included to model the complete clearing decision. |
| A3 | `if key_has_default and (key_is_primary or not form_data_present):` | `if to_field.has_default() and (to_field.attname == self.fk.remote_field.model._meta.pk.name or not form.data):` | **I** (under R on the three booleans) | the FIX. Identical boolean combination — `has_default AND (is_pk OR not data)` — with each operand refined from its repo boolean to a `bool` parameter (R, mapping.md §2). The pre-patch had only the `has_default` conjunct (no parenthesised disjunction); the post-patch adds it. This is the single changed expression of the gold patch. |
| A4 | `instance.key = None` | `setattr(self.instance, to_field.attname, None)` (`models.py:1181`) | **I** (under R on the attribute name) | identical concrete operation — store `None` into the parent's related-key attribute — with the dynamic attribute name refined to the field `key` (R, mapping.md §2). Unchanged by the patch; gated by A3. |
| A5 | `Requires(MustTerminate(2))` (total-correctness obligation) | the clearing block is a bounded, straight-line guard + one `setattr` inside `add_fields` that RETURNS to its caller on every call | R | the gold code terminates on every call; the F2P/P2P tests observe the (cleared or preserved) key only BECAUSE form construction returns. Under partial-correctness semantics a diverging body (e.g. `while True: pass` — the G-PANEL-1 same-spec attack class) or a same-measure self-call satisfies the two value postconditions vacuously while its faithful real patch hangs `add_fields` (and the tests) forever. The obligation pins termination: Nagini's obligation-leak check rejects a loop that does not take the obligation and a self-call at a non-decreasing measure. `ParentObject.__init__` carries `MustTerminate(1)` (strictly smaller), so constructing a parent object remains admissible. |

The comment lines in the gold hunk are an inert comment with no runtime
behaviour; they have no model counterpart.

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: its guard drops the
`(key_is_primary or not form_data_present)` conjunct (step **A3**), keeping only
`if key_has_default:` exactly as the pre-patch `if to_field.has_default():`.
With the byte-identical frozen spec it **fails** verification on the
postcondition

```
Ensures(Implies(not should_clear(adding, key_has_default, key_is_primary,
                                 form_data_present),
                instance.key is Old(instance.key)))
```

(`model_prepatch.py:74` — `Implies((not should_clear(...)), (instance.key is
Old(instance.key))) might not hold`). The witness is precisely the FAIL_TO_PASS
scenario: `adding=True, key_has_default=True, key_is_primary=False,
form_data_present=True` ⇒ `should_clear` is False (the value must be PRESERVED),
yet the pre-patch impl sets `instance.key = None`, violating the preserve
clause. The companion clause
`Ensures(Implies(should_clear(...), instance.key is None))` keeps the spec
faithful in the genuine-clear cases (so a wrong impl cannot satisfy the spec by
never clearing), and pins the post-state exactly, so the spec is strong enough
that no implementation of the clearing decision other than the patched guard
verifies. The frozen spec sees the bug.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
clearing guard's boolean condition — is an **I** step (the very same
`has_default AND (is_pk OR not data)` boolean combination, with each operand
refined from a repo boolean to a `bool` parameter by R). The changed operation
is fully expressible, so it is modelled DEEPLY and concretely (the
`should_clear` predicate + the guarded `instance.key = None` store), NOT hidden
behind an axiom about the function under change. There is therefore **no
A-consumed axiom and no A-reference** in this bundle; `axiom_check.py` instead
performs a decision-table G-AX equivalence check (mapping.md §3).

## D. verify(model) ⇒ resolved

`reset_default_related_key` verifies only if it TERMINATES (the
`MustTerminate(2)` obligation, step A5 — a diverging or self-recursive body
fails Nagini's obligation-leak check, so vacuous satisfaction of the
postconditions is impossible) and (A3/A4) it clears `instance.key`
to `None` exactly when `adding and key_has_default and (key_is_primary or not
form_data_present)` holds, and preserves it otherwise. By R (the in-memory
parent and its dynamically-named related-key attribute ↔ `ParentObject.key`;
the three repo booleans ↔ the three `bool` parameters) and the single **I** fix
step, the verified decision equals the gold guard
`if to_field.has_default() and (to_field.attname == ...pk.name or not
form.data): setattr(self.instance, to_field.attname, None)` evaluated inside
`if self.instance._state.adding:` on the tested inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There is no axiom, so the
only trust point of PLAN §1.1 that applies is refinement fidelity (this
document, G-EQ); the decision-table check in `axiom_check.py` corroborates the
guard's logic in-container.
