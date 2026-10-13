# refinement.md — django__django-11149

Operation correspondence between the `implementation_has*Permission` defs (plus
the shared `implementation_hasAnyPermsForTargetModel` helper) and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real behavior by
G-CONF/G-AX), **I** (identical concrete op).

No axioms are declared or consumed. The only repo callee the changed code calls
— `get_permission_codename` (UNCHANGED) — is modeled deeply as `permString`; the
permission lookup `request.user.has_perm` is modeled as membership against the
`userPerms` input; target-model resolution over `opts.fields` is modeled deeply.
Every row is **R**, **A-reference**, or **I**. The R/I/A-reference legs are
differential-tested by G-CONF; G-AX is a skip stub.

## What the gold patch changes (`django/contrib/admin/options.py`, `InlineModelAdmin`)

The auto_created branch of `has_add_permission`, `has_change_permission`,
`has_delete_permission` pre-patch returned `self.has_view_permission(...)`, i.e.
accepted `view OR change` on the target model. The patch factors target
resolution + the permission lookup into a new helper
`_has_any_perms_for_target_model(request, perms)` and:

* add / change / delete now pass `['change']` ⇒ require the *change* permission;
* view passes `['view', 'change']` ⇒ result unchanged (pure refactor of the
  pre-patch `view or change`).

So the observable fix is on add/change/delete: a view-only user is no longer
admitted.

## `implementation_hasAnyPermsForTargetModel` ↔ `_has_any_perms_for_target_model`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `selfAppLabel selfModelName parentModelId : String`, `fields : List LinkField`, `userPerms actions : List String` | `self.opts.app_label`/`.model_name`, `self.parent_model`, `self.opts.fields`, the user's `has_perm` set, `perms` | R | observables at the decision point (mapping.md bijection) |
| `let mut appLabel := selfAppLabel; let mut modelName := selfModelName; for f in fields do if f.hasRemote && f.remoteModelId != parentModelId then appLabel := …; modelName := …; break` | `opts = self.opts; for field in opts.fields: if field.remote_field and field.remote_field.model != self.parent_model: opts = field.remote_field.model._meta; break` | A-reference | target-model resolution, modeled deeply; first non-parent remote field wins, else fall back to self |
| `for a in actions do if userPerms.contains (permString appLabel modelName a) then return true; return false` | `any(request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts))) for perm in perms)` | A-reference | `get_permission_codename` is UNCHANGED (`'%s_%s' % (action, model_name)`), spelled out as `permString`; `has_perm(s)` ⇔ `s ∈ userPerms`; `any(...)` ⇔ early-return scan |

## `implementation_has{Add,Change,Delete}Permission` ↔ the patched predicates

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `if autoCreated then return implementation_hasAnyPermsForTargetModel … ["change"]` | `if self.opts.auto_created: return self._has_any_perms_for_target_model(request, ['change'])` | I | the EDITED branch: add/change/delete now require *change* (this is the fix) |
| `return superResult` | `return super().has_<action>_permission(request[, obj])` | R | non-auto_created passthrough; `superResult` is the opaque external decision |

## `implementation_hasViewPermission` ↔ the patched predicate

| Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|
| `if autoCreated then return implementation_hasAnyPermsForTargetModel … ["view", "change"]` | `if self.opts.auto_created: return self._has_any_perms_for_target_model(request, ['view', 'change'])` | I | view requires *view* OR *change* — semantically identical to the pre-patch `has_perm(view) or has_perm(change)`; only refactored |
| `return superResult` | `return super().has_view_permission(request)` | R | non-auto_created passthrough |

## Independently-observable behavior (G-DIFF)

One prepatch variant captures the bug (the three mutating actions reverting to
view-level authority):

- **`Solution_prepatch.lean`** — add/change/delete (auto_created) defer to the
  view authority `["view", "change"]` instead of `["change"]` (the pre-patch
  `return self.has_view_permission(...)`). Fails `correct_hasAddPermission` /
  `correct_hasChangePermission` / `correct_hasDeletePermission` on the
  `autoCreated = true` clause whenever the user holds the target's *view*
  permission but NOT its *change* permission: the impl returns `true`, but the
  spec demands `anyPermForTarget … ["change"]` = `false`. This is exactly the
  FAIL_TO_PASS behavior (`test_inline_add_m2m_view_only_perm`,
  `test_inline_change_m2m_view_only_perm`: a view-only user must NOT get
  add/change/delete on the m2m inline). `correct_hasViewPermission` and
  `correct_hasAnyPermsForTargetModel` still hold in the prepatch (view's result
  is unchanged by the fix), so the discriminating clauses are the three mutating
  actions.

The variant keeps the spec view byte-identical to `Solution.lean`.
