# mapping.md — django__django-11149

Binds every `Solution.lean` symbol to the repository at
`base_commit = e245046bb6e8b32360aa48b8a41fb7050f0fc730`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/contrib/admin/options.py` (class
`InlineModelAdmin`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `addRelationAllowed (autoCreated, userHasPerm, superResult)` | `InlineModelAdmin.has_add_permission(self, request, obj)` — `options.py:2115` | modeled changed gate |
| `changeRelationAllowed (autoCreated, userHasPerm, superResult)` | `InlineModelAdmin.has_change_permission(self, request, obj=None)` — `options.py:2122` | modeled changed gate |
| `deleteRelationAllowed (autoCreated, userHasPerm, superResult)` | `InlineModelAdmin.has_delete_permission(self, request, obj=None)` — `options.py:2129` | modeled changed gate |
| `viewRelationAllowed (autoCreated, userHasPerm, superResult)` | `InlineModelAdmin.has_view_permission(self, request, obj=None)` — `options.py:2136` | modeled gate (decision unchanged by the fix; carried so its discriminating clause is part of the frozen spec and the other three gates' prepatch is expressible against the same spec) |
| `holdsAnyTargetPerm (userHasPerm, perms)` | the post-patch helper `_has_any_perms_for_target_model(self, request, perms)` — added by the gold patch (`options.py`, just above `has_add_permission`) | the disjunctive permission probe the four gates share post-patch |
| `anyPerm (userHasPerm) (perms)` *(pure)* | the helper body `any(request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts))) for perm in perms)` | pure spec: `any(...)` over the requested permission list |
| `Perm` (`.view` / `.change`) *(pure)* | the permission codename strings `'view'` / `'change'` passed to `get_permission_codename` | the only two codenames ever queried on the related model |

Inputs that are **free** (universally quantified — see §3):

| Solution.lean input | repo meaning |
|---|---|
| `autoCreated : Bool` | `self.opts.auto_created` — whether this inline's model is an implicitly-created M2M through model |
| `userHasPerm : Perm → Bool` | `λ perm. request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts)))` on the **resolved target model** `opts` — i.e. "the principal holds permission `perm` on the related model" |
| `superResult : Bool` | the inherited decision `super().has_*_permission(...)` taken when `self.opts.auto_created` is false |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.opts.auto_created` : truthy/falsey bool | `autoCreated : Bool` | `True ↔ true`, `False ↔ false` |
| `request.user.has_perm(<codename on target>)` : bool, per codename | `userHasPerm : Perm → Bool` | the permission test is a total function of the codename; `'view' ↔ Perm.view`, `'change' ↔ Perm.change`; bool ↔ `Bool` |
| `super().has_*_permission(...)` : bool | `superResult : Bool` | exact |
| codename string `'view'` / `'change'` | `Perm.view` / `Perm.change` | the two codenames the methods ever interrogate |
| `['view', 'change']` / `['change']` request lists | `[Perm.view, Perm.change]` / `[Perm.change]` | per-element |
| `any(g(p) for p in perms)` | `anyPerm g perms` | front-recursive disjunction; empty ↔ `false` |
| each gate's returned bool | the `Bool` `result` | exact |

## 3. Callee provenance — why there are NO axioms / NO A-references

The patch changes only the **decision logic** of the four gates (which
permission(s) the auto-created branch demands). Everything the gates *call* is
either unchanged infrastructure or abstracted into a free input:

- **`request.user.has_perm(...)`, `get_permission_codename(perm, opts)`,
  `'%s.%s' % (app_label, ...)`** — all UNCHANGED by the patch. Pre- and
  post-patch alike compute the per-codename permission test on the resolved
  target model. The modeled decision makes **no behavioural claim** about how
  `has_perm`/`get_permission_codename` decide; it treats the composite
  "principal holds permission `perm` on the related model" as the free input
  `userHasPerm : Perm → Bool`. The spec is proven for **every** such function,
  so there is nothing to validate against a real callee → no A-reference, no
  consumed axiom.
- **the target-model field walk** (`for field in opts.fields: if
  field.remote_field and field.remote_field.model != self.parent_model: opts =
  field.remote_field.model._meta; break`) — UNCHANGED by the patch (it merely
  moved from `has_view_permission` into the new helper). It only selects WHICH
  model `userHasPerm` queries; it does not alter the disjunctive decision. Folded
  into `userHasPerm` (which already abstracts "on the resolved related model").
- **`super().has_*_permission(...)`** — the non-auto-created branch is UNCHANGED;
  its value is the free input `superResult : Bool`.

Because every callee is unchanged and either bypassed by the modeled decision or
abstracted as a free input with no relied-on property, this bundle has
**`axioms: []`** and **`deep_model_references: []`** (cf. the structurally-twin
boolean-logic bundle django__django-16527). Consequently **no `axiom_check.py`**
is shipped and **G-AX skips** ("no axioms in bundle"). The single trust point is
refinement fidelity (refinement.md, G-EQ + G-CONF), not callee soundness.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11149`**. The R/I shadow
transliterates `anyPerm` + the four gates from `Solution.lean`; the oracle is the
gold-patched `options.py` decision logic transliterated verbatim (see the
`conformance_check.py` docstring for why the real `InlineModelAdmin` methods are
not driven in-container). Both are exercised over all 2^4 = 16 free-input
assignments × 4 gates plus seeded fuzz.
