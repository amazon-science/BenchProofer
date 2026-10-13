# refinement.md — django__django-16801

The operation-by-operation correspondence between `model.py`'s implementation
(the `attach_post_init_hook` impl region and the deep `should_register` /
`configured` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The registration site — `ImageField.contribute_to_class()` (`django/db/models/fields/files.py:438`)

Gold hunk 1:
```
-        if not cls._meta.abstract:
+        # with width_field/height_field.
+        if not cls._meta.abstract and (self.width_field or self.height_field):
             signals.post_init.connect(self.update_dimension_fields, sender=cls)
```

The per-instance recalculation hook (`self.update_dimension_fields`) is hooked
to the owning class's `post_init` notification list. Pre-patch it is registered
for every concrete class; the hook is a no-op when neither companion size-field
is configured, yet was still registered, paying signal-dispatch cost on every
instance build. The fix registers it only when it can ever do observable work:
the class is concrete AND at least one companion target is configured.

| # | model.py impl op (`attach_post_init_hook`) | patch.diff op (gold hunk 1) | tag | justification |
|---|---|---|---|---|
| A1 | params `is_abstract: bool`, `width_target`/`height_target: Optional[List[int]]`, `owner_id: int`, `receivers: List[int]` | `self.width_field`, `self.height_field`, `cls._meta.abstract`, `cls` (`id(cls)`), `signals.post_init.receivers` | R | the field-name `str`/`None` ↔ `Optional[List[int]]` (only truthiness observed); the abstract flag ↔ `bool`; the sender `cls` ↔ its identity token `owner_id`; the receiver list ↔ the `List[int]` of registered sender tokens (mapping.md §2). |
| A2 | guard `(not is_abstract) and (configured(width_target) or configured(height_target))` | `not cls._meta.abstract and (self.width_field or self.height_field)` | **I** (under R on the carriers) | the FIX. `configured(name) == name is not None and len(name) > 0` is exactly Python truthiness of a field name (a non-empty `str`, else `None`); the model's `... or ...` over `configured` is exactly `self.width_field or self.height_field`; `not is_abstract` ↔ `not cls._meta.abstract`. Same concrete boolean decision, carriers refined by R. The decision predicate is the **A-reference** validated == the real `contribute_to_class` registration by axiom_check.py / G-AX (mapping.md §3.1). |
| A3 | `receivers.append(owner_id)` inside the guard | `signals.post_init.connect(self.update_dimension_fields, sender=cls)` inside the guard | **I** (under R on the carrier) | the registration side effect ↔ appending the owner's identity token to the notification list; the F2P test observes exactly membership of `id(sender)` in `signals.post_init.receivers`. The hook object/`connect` plumbing carries no behaviour the test observes beyond "this sender is now registered" (mapping.md §2). |
| A4 | (no append when the guard is false; `receivers` unchanged) | (no `connect` call when the guard is false) | I | identical: when the guard fails the notification list is left exactly as it was. |

The discriminating content of the change — *do not register when neither
companion target is configured on a concrete class* — lives in the postcondition
clause `should_register(...) == (ToSeq(receivers) == Old(...) + PSeq(owner_id))`
together with its negation. The pre-patch guard `not cls._meta.abstract`
registers unconditionally for concrete classes; `model_prepatch.py` reproduces
that (`if not is_abstract: receivers.append(owner_id)`) and **fails** the
registration-decision postcondition (`model_prepatch.py:91` — "Postcondition …
`should_register == (ToSeq(receivers) == Old(ToSeq(receivers)) + PSeq(owner_id))`
might not hold"): for a concrete class with no companion target,
`should_register` is `False` but the prepatch grew `receivers`, exactly the spec
sensing the change (G-DIFF). This is the behaviour the F2P
`test_post_init_not_connected` observes: a concrete `ImageField` model with no
`width_field`/`height_field` must NOT appear in `signals.post_init.receivers`.

## B. The guard-cleanup site — `update_dimension_fields()` (`django/db/models/fields/files.py:447`)

Gold hunk 2:
```
-        # Nothing to update if the field doesn't have dimension fields or if
-        # the field is deferred.
-        has_dimension_fields = self.width_field or self.height_field
-        if not has_dimension_fields or self.attname not in instance.__dict__:
+        # Nothing to update if the field is deferred.
+        if self.attname not in instance.__dict__:
             return
```

This drops the now-redundant `has_dimension_fields` short-circuit from the
recalculation hook's own early-return. It is a **behaviour-preserving cleanup
enabled by hunk 1**, not an independently-observable fixed behaviour, so it has
no separate failing `model_prepatch` (cf. SPEC_GUIDE §3: one prepatch per
independently-fixed behaviour). Two facts establish behaviour preservation:

  1. **On the `post_init` path** (the only way the hook is invoked without
     `force`): after hunk 1, the hook is registered *only* when at least one
     companion target is configured. So whenever the hook runs from a
     notification, `self.width_field or self.height_field` is already truthy and
     the dropped guard `not has_dimension_fields` was always `False` — removing
     it changes nothing. The remaining `self.attname not in instance.__dict__`
     deferred-field guard is preserved verbatim.

  2. **On the `force=True` path** (called directly by the descriptor's setter,
     not via the signal): with neither companion target configured, the dropped
     guard previously returned early. Without it, control falls through, but
     every subsequent write is itself guarded by `if self.width_field:` /
     `if self.height_field:` (`files.py:499-502`) — both `None`, so no
     assignment occurs. The function is a no-op either way. Hence the cleanup is
     observationally the identity on every input, for both call paths.

Because hunk 2 changes no observable behaviour, the byte-identical frozen spec
(shared by `model.py` / `model_prepatch.py`) does not need a clause for it, and
G-DIFF is driven entirely by the registration decision of site A. The cleanup's
behaviour-preservation argument is the I-correspondence above; no axiom is
introduced for it.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or **I**, with the decision predicate additionally
validated as an **A-reference**. The one operation that genuinely *changed* —
the registration guard — is an **I** step (the same boolean decision, carriers
refined by R): `configured`/`should_register` spell the guard out exactly. There
is **no consumed axiom**: the registration decision is pure boolean/structure
logic, modeled deeply. The only callee behaviour relied on — that the real
`ImageField.contribute_to_class` registers the hook on `post_init` **iff** the
guard holds — is an **A-reference** the deep model is validated against by
axiom_check.py (G-AX, §A2), never an `@ContractOnly` the proof consumes. We
never axiomatize the function under change.

## D. verify(model) ⇒ resolved

`attach_post_init_hook` verifies only if it appends the owner's identity token
to the notification list **exactly** when `should_register` holds (the owner is
concrete and at least one companion target is configured), and leaves the list
untouched otherwise (A2–A4), with the companion-target names read-only. By R
(the field-name `str`/`None` ↔ `Optional[List[int]]`; `cls` ↔ `owner_id`;
`signals.post_init.receivers` ↔ the `List[int]` of registered sender tokens; the
`connect` side effect ↔ the append) and the single **I** fix step, the verified
function equals the gold hunk-1 guard
`not cls._meta.abstract and (self.width_field or self.height_field): connect(...)`
on the tested inputs; hunk 2 is the behaviour-preserving cleanup of §B. By G-AX
the real `ImageField.contribute_to_class` registers the hook iff the modeled
predicate holds (A-reference). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited
decision predicate — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom soundness (here, the A-reference G-AX
check) and refinement fidelity (this document, G-EQ).
