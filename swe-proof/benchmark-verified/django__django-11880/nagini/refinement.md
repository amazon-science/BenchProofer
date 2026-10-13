# refinement.md — django__django-11880

The operation-by-operation correspondence between `model.py`'s implementation
(the `deep_duplicate` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The field-duplication method — `Field.__deepcopy__()` (`django/forms/fields.py:198-203`)

Gold hunk (the one added line, at `fields.py:202`):
```
         result = copy.copy(self)
         memo[id(self)] = result
         result.widget = copy.deepcopy(self.widget, memo)
+        result.error_messages = self.error_messages.copy()
         result.validators = self.validators[:]
         return result
```

`copy.copy(self)` is a SHALLOW copy: `result` shares every attribute reference
with `self`, including the `error_messages` dict and the `validators` list. The
method then re-binds the two mutable per-field collections to fresh copies so
the duplicate owns them: `validators` was already re-bound to a fresh list
(`self.validators[:]`); the bug was that `error_messages` was NOT — so all
copies of a field shared one `error_messages` dict and a per-instance override
on one form's field bled into every other instance's field. The fix adds the
parallel `result.error_messages = self.error_messages.copy()` (a shallow dict
copy: a distinct dict object holding the same code→message entries).

| # | model.py impl op (`deep_duplicate`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | `self: Field` with fields `self.msg_codes`, `self.msg_values`, `self.validators` | the `self` field object; its `error_messages` dict and `validators` list | R | the form field modelled as a minimal object carrying only the two touched mutable collections. The `error_messages` **dict** (code→message) ↔ the two index-aligned `List[int]` `msg_codes`/`msg_values` (`msg_codes[k]` bound to `msg_values[k]`); the `validators` list ↔ `List[int]` of validator identities (mapping.md §1, §2). |
| A2 | `result = Field()` then the two copy loops | `result = copy.copy(self)` (the shallow base) followed by the per-collection re-binds | R | the shallow `copy.copy` shares all references; the *behaviour the change cares about* is the subsequent re-binding of the two mutable collections to fresh, independent copies. `Field()` gives a fresh result object; the loops fill its own collections. The unmodelled shallow-shared scalar/immutable attributes (`required`, `label`, …) are not touched by the change and carry no behaviour the F2P/P2P tests of *this* change observe (mapping.md §2). |
| A3 | the `msg_codes`/`msg_values` copy loop: a fresh, fully-owned collection whose entries equal `self`'s, with `result.msg_codes is not self.msg_codes` and `result.msg_values is not self.msg_values` | `result.error_messages = self.error_messages.copy()` | **I** (under R on the carrier) | the FIX. `dict.copy()` produces a DISTINCT dict object holding the same key→value entries; the deep model produces a distinct list pair holding the same code→value entries. Same concrete operation (a shallow copy of the override mapping into a separate object), only the dict carrier refined to two index-aligned lists (R). The distinct-object semantics of `dict.copy()` is the **A-reference** validated by axiom_check.py / G-AX (mapping.md §3.1). |
| A4 | the `validators` copy loop: a fresh, fully-owned list equal to `self.validators` in order, with `result.validators is not self.validators` | `result.validators = self.validators[:]` | **I** (under R on the carrier) | identical concrete operation — a shallow copy of the validator list into a separate list object — present pre- and post-patch; the slice `[:]` ↔ the element-by-element copy loop, the `list` ↔ `List[int]` (R). `list[:]`'s distinct-object semantics is also the **A-reference** (mapping.md §3.1). |
| A5 | `return result` | `return result` | I | identical return of the duplicated field. |

The `memo[id(self)] = result` and `result.widget = copy.deepcopy(self.widget, memo)`
lines are unchanged by the patch and concern the deep-copy memoization /
widget sub-object, not the per-field message overrides the change fixes; they
carry no behaviour the F2P test of this change observes and are outside the
modelled scope (mapping.md §2).

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it drops step **A3** — instead of
copying the message collections into fresh objects, it leaves them ALIASED to
`self`'s (`result.msg_codes = self.msg_codes`, `result.msg_values =
self.msg_values`), exactly as `copy.copy(self)` shares the `error_messages` dict
when the `.copy()` line is absent. Only the `validators` list is freshly copied
(step A4). With the byte-identical frozen spec it **fails** verification on the
postcondition that the duplicate owns its own message collection —
`Acc(list_pred(Result().msg_codes))` (full permission), `model_prepatch.py:101`
("There might be insufficient permission to access `list_pred(Result().msg_codes)`"):
a result that shares `self`'s half-owned collection cannot be a fully-owned,
independent object, and therefore also violates the companion clause
`Result().msg_codes is not self.msg_codes`.

That is precisely the behaviour the F2P test observes:
`test_field_deep_copy_error_messages` deep-copies a `CharField` subclass that
set `error_messages={'invalid': ...}` and asserts
`self.assertIsNot(field_copy.error_messages, field.error_messages)` — i.e. the
duplicate's overrides are a DISTINCT object. The spec is therefore strong enough
that no implementation that leaves the duplicate's message collection aliased to
the original can verify (the spec sees the bug). The `validators` clauses, which
both pre- and post-patch satisfy, keep the model faithful (the unchanged
collection stays correctly independent) and prevent a wrong impl from "fixing"
the wrong collection.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, **I**, or **A-reference**. The one operation that
genuinely *changed* — adding the independent copy of the override mapping to the
duplicate — is an **I** step (the very same shallow-copy-into-a-separate-object
operation that `validators[:]` already performed, only the dict carrier refined
to two index-aligned lists by R). There is **no consumed axiom**: the
duplication is pure object/structure logic, modelled deeply. The only callee
behaviour relied on — that `dict.copy()` / `list[:]` yield a *distinct object
with equal contents* — is an **A-reference** the deep model is validated against
by axiom_check.py (G-AX, §A3/A4), never an `@ContractOnly` the proof consumes.
We never axiomatize the function under change.

## D. verify(model) ⇒ resolved

`deep_duplicate` verifies only if (A3) the duplicate's message collection is a
fully-owned, DISTINCT object whose entries equal the original's, and (A4) the
duplicate's validator collection is likewise distinct and equal, and the
original is left untouched. By R (the `error_messages` dict ↔ the index-aligned
`msg_codes`/`msg_values`; `validators` list ↔ `List[int]`; the shallow base
`copy.copy` re-bound per-collection ↔ fresh `Field()` filled by the loops) and
the single **I** fix step, the verified method equals the gold
`__deepcopy__` — `result.error_messages = self.error_messages.copy();
result.validators = self.validators[:]; return result` — on the tested inputs.
By G-AX the real `dict.copy()` / `list[:]` (and the real `Field.__deepcopy__`
post-patch) have exactly the distinct-object-with-equal-contents semantics the
deep model encodes (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited primitive — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: axiom soundness (here, the A-reference G-AX
check) and refinement fidelity (this document, G-EQ).
