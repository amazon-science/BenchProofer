# refinement.md — django__django-15499

The operation-by-operation correspondence between `model.py`'s implementation
(the `reduce_create` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** if
the proof uses the axiom's `Ensures`, **A-reference** if a deep model is
validated == the real callee by G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **no axioms** in this bundle:
the change is pure structural selection over the two operations' own fields,
modelled deeply (no A-consumed, no A-reference rows).

## A. The folding site — `CreateModel.reduce` (`django/db/migrations/operations/models.py:136`)

Gold hunk (inserted as a new `elif` branch in `reduce`, between the
`AlterModelOptions` branch and the `AlterTogetherOptionOperation` branch):

```
+        elif (
+            isinstance(operation, AlterModelManagers)
+            and self.name_lower == operation.name_lower
+        ):
+            return [
+                CreateModel(
+                    self.name,
+                    fields=self.fields,
+                    options=self.options,
+                    bases=self.bases,
+                    managers=operation.managers,
+                ),
+            ]
```

`model.py`'s `reduce_create` models the relevant slice of `reduce`: the
already-present `AlterModelOptions` fold (the `elif isinstance(operation,
AlterModelOptions) …` branch at lines 156-172, modelled WITHOUT its option-key
filtering, see step A2 below) and the newly-added `AlterModelManagers` fold (the
gold hunk). Both produce a single `CreateModel`. The modeled DOMAIN is
restricted by the precondition to exactly these two operation kinds: every
other follow-up kind is handled by its own branch of `reduce` (or
`super().reduce(...)`) with its own folding behaviour, and is deliberately out
of scope — the model asserts nothing about it. Within the domain, a name-key
mismatch falls through to the null token ("not folded into a single op").

| # | model.py impl op (`reduce_create`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `model: CreateModel` with int-token fields `name, name_lower, fields, options, bases, managers` | the `self` `CreateModel` instance: `self.name` (case-preserved display name), `self.name_lower` (lower-cased comparison key, `models.py:26`), and its `self.fields/options/bases/managers` attributes | R | each model facet (a Python str/list/dict/tuple object) is abstracted to an integer identity token; two facet values are "the same object content" iff their tokens are equal (mapping.md §2). The display name and its lower-cased key are DISTINCT tokens in general (`"Foo" != "foo"` for any mixed-case declared name — including the F2P test's model `"Foo"`); modelling them as one token would wrongly admit an impl that installs the lower-cased key as the folded op's name. The fold only ever *selects which facet object to carry forward*; it never inspects facet contents, so identity-token equality is the exact observable. |
| A2 | `op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower` branch returns `CreateModel(model.name, model.name_lower, model.fields, op_options, model.bases, model.managers)` | the `elif isinstance(operation, AlterModelOptions) and self.name_lower == operation.name_lower` branch (lines 156-172) returning `CreateModel(self.name, fields=self.fields, options=options, bases=self.bases, managers=self.managers)` | R + I | `isinstance(operation, AlterModelOptions)` ↔ `op_kind == KIND_ALTER_OPTIONS`; `self.name_lower == operation.name_lower` ↔ `op_name == model.name_lower` (lower-key token, R). The folded op's name slot takes `self.name` ↔ `model.name` (the case-preserved DISPLAY name, not the comparison key); its derived `name_lower` is unchanged, so the model carries `model.name_lower` forward. The carried `options` token (`op_options`) abstracts the merged-and-key-filtered `options` dict the real branch builds; the spec pins only that the **option facet comes from the alter step and the manager/field/base facets from the creation step** — the merge/key-filter internals are an UNCHANGED, pre-existing computation, not part of this fix, so they are abstracted into the `op_options` token (mapping.md §2). The control-flow and facet-selection (which slot each facet fills) are identical (I). |
| A3 | `elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower` branch returns `CreateModel(model.name, model.name_lower, model.fields, model.options, model.bases, op_managers)` | the **added** branch returning `CreateModel(self.name, fields=self.fields, options=self.options, bases=self.bases, managers=operation.managers)` | R + I | `isinstance(operation, AlterModelManagers)` ↔ `op_kind == KIND_ALTER_MANAGERS`; `self.name_lower == operation.name_lower` ↔ `op_name == model.name_lower` (R). The constructor arguments map slot-for-slot: **`self.name`↔`model.name`** (the case-preserved display name — an impl that wired `operation.name_lower` here would rename `'Foo'` to `'foo'` and fail the F2P's deep-equality assertion; the spec's `Result().name == model.name` clause rejects it), `self.fields`↔`model.fields`, `self.options`↔`model.options`, `self.bases`↔`model.bases`, **`operation.managers`↔`op_managers`** (the altered manager collection carried forward, NOT `self.managers`). These are the load-bearing identical selections (I). |
| A4 | `return None` (in-domain kind, but the name keys differ) | for an `AlterModelOptions`/`AlterModelManagers` whose `name_lower` differs from `self.name_lower`, control falls through the two modelled `elif` guards to the rest of `reduce` / `super().reduce(...)`, which for the F2P/P2P scenarios returns the two operations un-collapsed | R | the null token abstracts "this pair is not folded into a single `CreateModel` by these two branches"; the optimiser then leaves the pair (or routes it to another, unmodelled rule). Other operation kinds are OUT OF DOMAIN (precondition), so the null-token claim is made only for the key-mismatch case within the two modeled kinds. The F2P test observes only that a same-named manager-alter DOES fold (Result non-null with `managers == op_managers`); the negative direction is pinned by the iff in the postcondition (mapping.md §3). |

## B. The discriminating clause (G-DIFF)

The single behavioural change is: a `CreateModel` followed by an
`AlterModelManagers` for the SAME model now folds into one `CreateModel`
carrying the altered managers. In `model.py` this is:

* `Ensures(Implies(op_name == model.name_lower, Result() is not None))`
  — the fold MUST happen for a same-named alter of an in-domain kind
  (in particular a same-named manager alter);
* `Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_MANAGERS,
  Result().managers == op_managers and Result().options == model.options))` —
  the folded step carries the altered managers (and keeps the original
  options); and
* `Ensures(Implies(Result() is not None, Result().name == model.name))` — the
  folded step keeps the creation step's case-preserved DISPLAY name (gold hunk
  argument `self.name`), never the lower-cased comparison key.

`model_prepatch.py` is the pre-patch skeleton: the `KIND_ALTER_MANAGERS` branch
is **absent**, so a same-named manager alter falls through to `return None`. It
**fails** verification on exactly the first clause above
(`Postcondition … Implies(… op_name == model.name_lower, Result() is not None)
might not hold`) — the spec sensing the missing fold (G-DIFF). The option-alter branch
(A2) is unchanged across the twin, so no separate `model_prepatch_<k>` is needed
for it; the single fixed behaviour is the manager fold.

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. There is **no axiomatized callee**: the fold calls
no library/utility that it does not change — it merely constructs a new
`CreateModel` by selecting which facet object to carry into which slot, which is
modelled deeply over integer identity tokens. Hence there are no A-consumed and
no A-reference rows, and `axiom_check.py` carries an executable check of the
*structural* obligation instead (the real `CreateModel.reduce` over real
`CreateModel`/`AlterModelManagers`/`AlterModelOptions` operations folds exactly
as the spec demands), so G-AX still has a sound, in-domain artifact to run.

## D. verify(model) ⇒ resolved

`reduce_create` verifies only if (A3) a same-named manager alter folds into a
`CreateModel` whose `managers` facet equals the alter step's managers, whose
`options/fields/bases` come from the creation step, AND whose `name` is the
creation step's case-preserved display name (`Result().name == model.name`,
with `model.name` a distinct token from the guard's `model.name_lower`), AND
(A2) a same-named option alter folds symmetrically (options from the alter
step, managers from the creation step, same display name). By R (facet object ↔
identity token; `isinstance` ↔ `op_kind`; `name_lower` equality ↔ `op_name ==
model.name_lower`; display name ↔ `model.name`) the verified fold equals the
gold branch slot-for-slot on the tested operations. The F2P test
`test_create_alter_model_managers` checks exactly that `CreateModel("Foo",
fields=[]) + AlterModelManagers("Foo", managers=[…])` optimises to a single
`CreateModel("Foo", fields=[], managers=[…])` — which is A3, INCLUDING the name
`"Foo"` (not `"foo"`): an impl that installed the lower-cased key as the folded
op's name verified against the previous one-token spec but failed this test
(recorded G-EQ break); the two-token spec rejects it. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to the
declared type refinement, and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ); there are no axioms.
