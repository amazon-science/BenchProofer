# refinement.md — django__django-14534

The operation-by-operation correspondence between `model.py`'s implementation
(the `label_target_id` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`,
checked, and is the real correctness oracle, G-RESOLVE).

## A. The label-id site — `BoundWidget.id_for_label` (`django/forms/boundfield.py:278-280`)

Gold hunk:
```
  @property
  def id_for_label(self):
-     return 'id_%s_%s' % (self.data['name'], self.data['index'])
+     return self.data['attrs'].get('id')
```

| # | model.py impl op (`label_target_id`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `ctx: ChoiceContext` (fields `attrs`, `name`, `index`) | `self` (the `BoundWidget`), reading `self.data` (a dict) | R | the per-option context dict `self.data` ↔ `ChoiceContext` exposing only its three touched fields (mapping.md §2). The other `self.data` keys are untouched by the property and omitted. |
| A2 | `id_key() in ctx.attrs` | membership of the `'id'` key inside `self.data['attrs'].get('id')` (the `.get` that returns `None` when the key is absent) | R + I | `self.data['attrs']` (a `dict` of HTML attrs) ↔ `ctx.attrs` (`Dict[int,int]`); the literal key `'id'` ↔ the `id_key()` token (mapping.md §2). `dict.get('id')` is exactly "value if `'id' in d` else `None`"; the model spells the same membership test out (the `in` / lookup is ordinary mapping semantics, **A-reference**: validated == real `dict.get` by axiom_check.py, not consumed as an axiom). |
| A3 | `return ctx.attrs[id_key()]` (when present) | `self.data['attrs'].get('id')` returning the recorded id | R | the recorded id value (an id `str`) ↔ an `int` id token (mapping.md §2). The id stored in `attrs['id']` is **already fully resolved** by `ChoiceWidget.create_option` (prefix applied + per-option index appended, `widgets.py:626-627,645-651`); the property only reads it back, so the result equals the recorded id verbatim. |
| A4 | `return None` (when absent) | `self.data['attrs'].get('id')` returning `None` | I | `dict.get` returns `None` for a missing key; the model returns the genuine `None`. The carrier `None` models the absence of an id (`auto_id=False`). |

The discriminating content of the change lives in clauses (1)+(2) of the
postcondition: the result **is the recorded id** when one exists, and **is
None** when none exists. The pre-patch body `'id_%s_%s' % (name, index)`
fabricates a value from `name`/`index` that is independent of `attrs`:
`model_prepatch.py` reproduces it (`ctx.name * 1000 + ctx.index`, always
non-None) and **fails** the postcondition
`Implies(id_key() in ctx.attrs, Result() == ctx.attrs[id_key()])` (it also fails
the absence clause). That is exactly the spec sensing the change (G-DIFF):
the fabrication diverges from the recorded id whenever a prefix is configured
(F2P `test_boundfield_subwidget_id_for_label`) and invents an id when none was
recorded (F2P `test_iterable_boundfield_select`, expecting `None`).

The read-only discipline: `ctx.attrs`, `ctx.name`, `ctx.index` are all required
AND ensured at fractional permission (`Acc(..., 1/2)`), and the postcondition
asserts `ctx.attrs is Old(ctx.attrs)` — the property reads the context and
mutates nothing. A wrong impl cannot satisfy the spec vacuously by overwriting
the input (directive 5).

The termination discipline: the contract carries a
`Requires(MustTerminate(1))` obligation, so Nagini's total-correctness
obligation system rejects any implementation with a non-returning execution
path (an unbounded loop or unbounded recursion would otherwise discharge the
`Ensures` clauses vacuously under partial-correctness semantics). The real
property is a bounded dict membership test + lookup and trivially discharges
the obligation; a diverging same-spec impl fails the obligation leak check.

## B. No consumed axioms

There is **no `@ContractOnly` axiom** the proof consumes. The one operation that
genuinely *changed* — what value the property reports — is modeled **deeply**
(the membership test + lookup `attrs.get('id')` spelled out in
`label_target_id`), not hidden behind an axiom about the function under change.
The only out-of-band reference is the **A-reference** (mapping.md §3.1): the
deep model is validated == the real post-patch `BoundWidget.id_for_label`
(equivalently, `dict.get` semantics on the real per-option `attrs`) by G-AX
(`axiom_check.py`), which constructs the real Django subwidget data path for the
three observed form configurations. Ordinary `dict` membership/lookup is the
A-reference; nothing is consumed.

## C. No kind-3 (unexpressible-changed-op) steps

Every step A1–A4 is R, A-reference, or I. There is no changed operation that
Nagini cannot express: the change is a dict lookup over a small, fully-resolved
attribute mapping, which the model spells out directly.

## D. verify(model) ⇒ resolved

`label_target_id` verifies only if it terminates on every input
(`MustTerminate(1)`: no diverging path can discharge the postconditions
vacuously) AND its result equals the recorded id when one
exists (A3, clause 1) and is `None` when none exists (A4, clause 2). By R
(`self.data` dict ↔ `ChoiceContext`, `'id'` key ↔ `id_key()`, id `str` ↔ int
token, `dict.get` ↔ membership+lookup) the verified body equals
`self.data['attrs'].get('id')` on the tested inputs; by G-AX the deep model
equals the real post-patch property on the three observed form configurations
(and fuzzed variants). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited dict-lookup
reference — and the gold patch resolves (G-RESOLVE, checked: applies cleanly at
base_commit). The trust points are exactly the two of PLAN §1.1: the A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
