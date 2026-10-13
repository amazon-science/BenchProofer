# mapping.md — django__django-15499

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d90e34c61b27fba2527834806639eebbcfab9631`, states the type
abstraction, and records the (absence of) axiom provenance.

Repo file under change: `django/db/migrations/operations/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce_create(model, op_kind, op_name, op_options, op_managers)` | `CreateModel.reduce(self, operation, app_label)` — `django/db/migrations/operations/models.py:136` | the modeled changed method (migration-optimiser fold for a `CreateModel`) |
| `CreateModel` (model class, int-token facets) | `CreateModel` operation — `django/db/migrations/operations/models.py:41` (the `self` and the returned folded op) | the model-creation step; only the touched facets (`name, name_lower, fields, options, bases, managers`) are modelled |
| `model.name` | `self.name` (the case-preserved display name `str`, e.g. `"Foo"`) | the DISPLAY name the folded op must carry verbatim (`CreateModel(self.name, ...)` in both fold branches) |
| `model.name_lower` | `self.name_lower` (lower-cased comparison key, `models.py:26` cached property, e.g. `"foo"`) | the comparison key the guards use; a DISTINCT token from `model.name` in general (they differ whenever the declared name has an upper-case letter) |
| `op_kind == KIND_ALTER_OPTIONS` (0) | `isinstance(operation, AlterModelOptions)` — `AlterModelOptions` at `models.py:677` | follow-up step kind: alters the option set |
| `op_kind == KIND_ALTER_MANAGERS` (1) | `isinstance(operation, AlterModelManagers)` — `AlterModelManagers` at `models.py:732` | follow-up step kind: alters the manager collection (the newly-folded kind) |

**Domain restriction (modeled slice).** The precondition admits ONLY the two
kinds above. Any other follow-up operation kind is dispatched by `reduce` to
its own `elif isinstance(...)` branch (or the `super().reduce(...)` fallback),
each with its own folding behaviour — some of those branches fold, some do
not. Those kinds are OUTSIDE the modeled slice: the model makes no claim about
them (they are excluded by `Requires`, not mapped to an in-domain tag). This
avoids conflating heterogeneous behaviours under one catch-all token.
| `op_name` | `operation.name_lower` (compared to `self.name_lower`) — `models.py:26` (`name_lower` cached property) | the model the follow-up step targets, as a lower-cased key token; comparable to `model.name_lower` ONLY (never a stand-in for the display name `model.name`) |
| `op_options` | `operation.options` (post-merge/key-filter) carried as the folded step's `options` in the `AlterModelOptions` branch — `models.py:160-171` | the option facet the alter step installs (identity token) |
| `op_managers` | `operation.managers` carried as the folded step's `managers` in the **added** `AlterModelManagers` branch — gold hunk `managers=operation.managers` | the manager facet the alter step installs (identity token) |

The branch the gold patch ADDS is the `elif isinstance(operation,
AlterModelManagers) and self.name_lower == operation.name_lower` block returning
`CreateModel(self.name, fields=self.fields, options=self.options,
bases=self.bases, managers=operation.managers)`. The branch it sits beside (and
which `reduce_create` also models, for spec tightness) is the pre-existing
`AlterModelOptions` fold at `models.py:156-172`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a model facet object: `self.fields` (list), `self.options` (dict), `self.bases` (tuple), `self.managers` (list) and the alter step's `operation.options` / `operation.managers` | `int` identity token | two facet objects carry the same identity token iff they are the same facet content; the fold only ever *selects which facet object to forward into which constructor slot* (it never reads facet contents), so identity-token equality is the exact, lossless observable for what the fold does |
| `self.name` (case-preserved display name `str`, e.g. `"Foo"`) | `int` display-name token (`model.name`) | the fold carries the display name verbatim into the folded op's name slot (`CreateModel(self.name, ...)`); string equality ↔ token equality |
| `self.name_lower` / `operation.name_lower` (lower-cased model name `str`, e.g. `"foo"`) | `int` lower-key token (`model.name_lower`, `op_name`) | `self.name_lower == operation.name_lower` ↔ `op_name == model.name_lower`; the fold compares lower-cased keys for equality only. `model.name` and `model.name_lower` are DISTINCT tokens in general: `"Foo" != "foo"` whenever the declared name is not already all-lowercase (as in the F2P test's model `"Foo"`). A patch that installed `operation.name_lower` as the folded op's name would rename the model to its lowercase key — observably wrong (`CreateModel('foo', ...)` != expected `CreateModel('Foo', ...)`) and rejected by the spec's `Result().name == model.name` clause |
| `isinstance(operation, AlterModelOptions / AlterModelManagers)` | `op_kind ∈ {0,1}` integer tag (precondition-restricted domain) | one tag per MODELED follow-up step kind; the two modelled branches key off these tags exactly as the corresponding two `elif isinstance(...)` branches key off the operation's runtime class. Every other operation kind is out of the modeled domain (excluded by `Requires`), so the model asserts nothing about it |
| the returned `[CreateModel(...)]` (a one-element list) vs. the un-collapsed fall-through | `Optional[CreateModel]`: the folded `CreateModel` vs. the null token | a single-element fold result ↔ a non-null `CreateModel`; "not folded by these branches" ↔ `None`. The optimiser's F2P assertion compares the *single* resulting `CreateModel`'s facets, which is exactly the non-null carrier here |

The merge/key-filter the real `AlterModelOptions` branch performs on the options
dict (`options = {**self.options, **operation.options}` then popping
`ALTER_OPTION_KEYS` absent from `operation.options`) is a **pre-existing,
unchanged** computation, not part of this fix; it is abstracted into the single
`op_options` token (the spec pins only that the option facet originates from the
alter step). The `AlterModelManagers` branch performs no such transformation —
it carries `operation.managers` verbatim — so `op_managers` is the exact facet.

## 3. Axiom provenance (kind-A) — NONE

There are **no `@ContractOnly` axioms** in this bundle. The fold invokes no
library/utility callee it does not change: it compares an integer name token,
branches on an integer kind tag, and constructs a new `CreateModel` by selecting
which facet token to place in which slot. All of this is modelled deeply over
integers and the minimal `CreateModel` object, so there is nothing to
over-approximate and nothing for G-AX to over-claim.

**Soundness check (G-AX):** because there is no axiom, `axiom_check.py` instead
exercises the **real** `django.db.migrations.operations.models.CreateModel.reduce`
in-container against the structural obligation `model.py` pins: it constructs a
real `CreateModel` and a real `AlterModelManagers` (and `AlterModelOptions`) for
the same and for differing model names, calls `reduce`, and asserts the result
folds exactly as the spec demands — a same-named manager alter yields a single
`CreateModel` carrying the alter step's `managers` with `fields/options/bases`
from the creation step; a differing name does not fold via this branch. This is
the same in-domain Django code the gold patch edits (no third-party callee).
Exit 0 iff every observation matches the spec.
