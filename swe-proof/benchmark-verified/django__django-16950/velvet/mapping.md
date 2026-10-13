# mapping.md — django__django-16950

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f64fd47a7627ed6ffe2df2a32ded6ee528a784eb`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of each modeled observation. `spec_provenance: cold` — the spec was
derived from the `problem_statement`, the gold `patch`, and the repo source
only.

Repo file under change: `django/forms/models.py`
(`BaseInlineFormSet.add_fields`, body lines 1173-1181 @ base_commit).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepareParentKey (mut inst …)` | `BaseInlineFormSet.add_fields(self, form, index)` — `django/forms/models.py:1152`, decision body lines 1173-1181 | the modeled changed function: the block that conditionally nulls the parent instance's auto-generated key attribute before building the inline FK field |
| `ParentObject` / `inst` | `self.instance` (the parent model instance the inline formset is bound to) — restricted to the one attribute the block touches | parent object carrier |
| `inst.keyValue` | the value held in `self.instance.<to_field.attname>` (set to `None` by `setattr(self.instance, to_field.attname, None)`, line 1181) | the auto-generated key attribute value |
| `shouldClearKey …` | the guarding condition of the `setattr`, lines 1175-1180 (post-patch) | the discard decision |
| `creatingNew` | `self.instance._state.adding` (line 1175) | parent object is being created (not yet persisted) |
| `keyHasDefault` | `to_field.has_default()` (line 1180 post-patch / line 1180 pre-patch) | the resolved `to_field` carries a model-level default |
| `keyIsPrimaryKey` | `to_field.attname == self.fk.remote_field.model._meta.pk.name` (line 1183, the first added disjunct) | the FK target attribute is the parent model's own primary key |
| `noDataSubmitted` | `not form.data` (line 1184, the second added disjunct) | no field data was submitted for the child form |

The pre-patch decision (refinement audit only, not in the consumer spec view) was
the single guard `if to_field.has_default():` (line 1180 pre-patch) — i.e.
`creatingNew && keyHasDefault`, with the `(keyIsPrimaryKey || noDataSubmitted)`
factor absent. `Solution_prepatch.lean` reproduces exactly that.

`to_field` itself is resolved earlier (lines 1176-1179) to either
`self.instance._meta.get_field(kwargs["to_field"])` or `self.instance._meta.pk`;
that resolution is UNCHANGED by the patch and is upstream of the modeled
decision. The modeled function observes only its two relevant properties
(`has_default()` and whether its `attname` is the parent pk name), so the
resolution itself need not be modeled — it feeds `keyHasDefault` /
`keyIsPrimaryKey` (mapping rows above).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.instance` (parent model instance) | `ParentObject` structure | only the touched attribute is modeled; all other instance state is orthogonal to this step (directive: model only touched fields). |
| value of `self.instance.<attname>` | `inst.keyValue : Option Nat` | a present auto-generated value ↔ `some v`; the post-`setattr(...,None)` state ↔ `none`. The concrete value's *type* (UUID / int / …) is irrelevant — only present-vs-cleared is observable here, so `Option Nat` with an arbitrary witness `v` is a faithful carrier (the F2P tests assert `assertIsNone` / `assertIsNotNone` / `== parent.uuid`, all present-vs-cleared distinctions). |
| `self.instance._state.adding` | `creatingNew : Bool` | Python truthy bool ↔ Lean `Bool`. |
| `to_field.has_default()` | `keyHasDefault : Bool` | method returns a bool ↔ Lean `Bool`. |
| `to_field.attname == self.fk.remote_field.model._meta.pk.name` | `keyIsPrimaryKey : Bool` | string-equality predicate ↔ Lean `Bool`. |
| `not form.data` | `noDataSubmitted : Bool` | Python truthiness of `form.data` (empty/`None` ⇒ `not form.data` is `True`) ↔ Lean `Bool`. `form.data` is a `QueryDict`; `not form.data` is `True` exactly when it is empty. |

The four conditions are INDEPENDENT boolean observations of the parent object and
the submission. Modeling them as four free `Bool` inputs is an R refinement (no
algebraic relation between them is assumed); G-CONF fuzzes the full `2^4` cube
plus randomized booleans.

## 3. Callee provenance

**No axiomatized callees.** The modeled decision is a closed boolean function of
its four inputs (`shouldClearKey`), and the only state effect is clearing one
`Option` field. Nothing is delegated to an unchanged callee whose internal
behaviour the proof must assume. Hence:

- no module-level `axiom` in `Solution.lean`;
- no `deep_model_references` (A-reference);
- **no `axiom_check.py`** — `meta.json` records `gates.G-AX.status = "skip"`
  (no axioms to validate), matching the no-axiom boolean-band exemplar
  (django__django-12276).

The four boolean observations are R-refinements of repo predicates; their
fidelity (and the fidelity of the decision they feed) is the R leg that
conformance_check.py (G-CONF) mechanically refutes against `patch.diff`'s
behaviour.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16950`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`shouldClearKey` and the conditional clear of `keyValue` (the R/I-tagged ops) to
Python; there is no A-tagged callee to leave to a real implementation, so the
shadow is pure R/I. The oracle is `patch.diff`'s decision, transliterated
verbatim from `add_fields` lines 1175-1181 (post-patch).
