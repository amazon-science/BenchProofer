# mapping.md — django__django-15814

## Symbol binding (file:line @ base_commit 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_relationModelKeys` / `problem_spec_relationModelKeys` | the relation-traversal inner loop of `Query.deferred_to_data` that records, per relation step, the model under which the step's pk must be selected | `django/db/models/sql/query.py:719-753` (loop `for name in parts[:-1]`) |
| `RelModel` (pure structure) | the model reached by following one relation, `cur_model` (`source.related_model` or `source.remote_field.model`) | `django/db/models/sql/query.py:747-751` |
| `RelModel.ident` | the resolved relation-target model object itself (which may be a proxy class) | `query.py:748` / `:750` (`cur_model` before normalization) |
| `RelModel.concreteIdent` | the model's concrete (base) model — `cur_model._meta.concrete_model` | `query.py:751` (post-patch) / `django/db/models/options.py:141-142,762` |
| `relationModelKeys` result entry | the model key under which the step's pk is recorded, `add_to_dict(must_include, cur_model, opts.pk)` | `query.py:753,762` |

The modeled function is the per-step body of the `for name in parts[:-1]` loop in
`Query.deferred_to_data` — the only place whose behavior the patch changes, and the
locus exercised by the FAIL_TO_PASS test `test_select_related_only`.

### What the code does (base_commit)

```python
for name in parts[:-1]:
    old_model = cur_model
    ...
    source = opts.get_field(name)
    if is_reverse_o2o(source):
        cur_model = source.related_model
    else:
        cur_model = source.remote_field.model
    opts = cur_model._meta                         # <-- pre-patch: keyed off cur_model as-is
    if not is_reverse_o2o(source):
        must_include[old_model].add(source)
    add_to_dict(must_include, cur_model, opts.pk)  # cur_model used as a dict KEY
```

Step by step, per relation traversed:
1. resolve the next model `cur_model` reached by this relation
   (`source.related_model` for a reverse one-to-one, else `source.remote_field.model`);
2. take its options `opts = cur_model._meta`;
3. record `cur_model` as a key in `must_include` (the set of models whose fields
   must be loaded), with that model's pk.

The dict keyed by model is later turned into `target[model] = {field attnames}`,
which `RelatedPopulator` consumes to compute `init_list` and locate the model's pk
column.

### The bug and the fix

`cur_model` resolved from a relation can be a **proxy** model (e.g. a FK that
points at a proxy class). A proxy shares its concrete base's table and pk column,
but is a distinct model object. When the proxy model is used as the dict key, the
fields-to-load map ends up keyed under the proxy rather than its concrete base.
Downstream, `RelatedPopulator.__init__` looks up the concrete model's pk attname
in the per-model `init_list`; because the entry was registered under the proxy,
the pk column is missing and `self.init_list.index(self.model_cls._meta.pk.attname)`
raises `ValueError: 'id' is not in list`.

The fix normalizes the resolved model to its concrete base BEFORE using it as a
key:

```python
cur_model = cur_model._meta.concrete_model     # added line
opts = cur_model._meta
```

so the fields-to-load map is always keyed under the concrete model. For a
non-proxy model, `_meta.concrete_model` is the model itself, so the change is a
no-op there (`options.py:141-142`: a concrete model's `concrete_model` is the
class itself).

### Lean modeling

- A relation traversal is modeled as `steps : List RelModel`: each entry is the
  model reached by one relation step (the `cur_model` produced by the resolution
  branch — modeled as already resolved, since the branch is unchanged by the patch).
- `RelModel` carries `ident : Nat` (the identity of the resolved model object,
  which may be a proxy) and `concreteIdent : Nat` (the identity of its concrete
  base model). For a concrete (non-proxy) model `concreteIdent = ident`; for a
  proxy `concreteIdent ≠ ident`.
- `concreteOf m := m.concreteIdent` is the deep model of `cur_model._meta.concrete_model`
  (the operation the patch introduces, modeled structurally — never axiomatized).
- The result is the list of model keys recorded, one per step, in step order. The
  post-patch key for step `m` is `m.concreteIdent`; the pre-patch key is `m.ident`
  (the un-normalized model), which for a proxy step is the proxy, reproducing the bug.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| the sequence of relation steps `parts[:-1]` of one field name (resolved models) | `steps : List RelModel` | the i-th resolved `cur_model` ↔ `steps[i]` |
| `cur_model` (resolved model object, possibly a proxy) | `RelModel.ident` | distinct model object ↔ distinct `Nat` |
| `cur_model._meta.concrete_model` | `RelModel.concreteIdent` | concrete-base model object ↔ its `Nat` id; concrete model ⇒ `concreteIdent = ident` |
| `add_to_dict(must_include, cur_model, opts.pk)` — the model used as a dict key | result entry `: Nat` | one registration ↔ one key in the result list, in step order |

The result of the modeled loop is the list of model keys under which the pk is
registered, in step order; modeled as `result : List Nat`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — keying the
  fields-to-load map under the *concrete* model rather than the resolved (possibly
  proxy) model — is modeled DEEPLY by `concreteIdent` on `RelModel`
  (SPEC_GUIDE §3: a deeply-modeled changed op is never axiomatized). No property of
  an external callee is consumed by the proof, so the `axioms` region is empty and
  **G-AX skips**.
- The resolution branch `source.related_model` / `source.remote_field.model`
  (`query.py:747-751`) is UNCHANGED by the patch; it selects WHICH model is reached
  and is modeled as the already-resolved `RelModel` carried in `steps`. It is not a
  behavioral callee of the changed decision.
- `is_reverse_o2o(source)` (`query.py:2596`) gates both the resolution branch and
  the `must_include[old_model].add(source)` source registration. Neither is changed
  by the patch (the source registration keys under `old_model`, which the prior
  step already normalized to concrete); they do not bear on the changed
  `cur_model`-key decision and are not modeled. Their omission constrains no output
  component the spec leaves free — the spec pins every produced key for every step.
- `_meta.concrete_model` is the operation the patch INTRODUCES; it is modeled
  deeply (`concreteIdent`), not axiomatized.

## G-CONF fuzz seed

Pinned LCG seed: **15814** (see `conformance_check.py` `SEED`). Corpus: randomized
relation-step sequences of 0–8 steps, each step drawn so that proxy steps
(`concreteIdent ≠ ident`) are well-represented (the discriminating case), with
distinct model identities. The R/I shadow of `implementation_relationModelKeys`
(key = `concreteIdent`) is diffed against an in-process replica of the POST-PATCH
loop, which resolves each step's model and takes `cur_model._meta.concrete_model`
using stand-in `Model`/`Options` classes that mirror the proxy/concrete hierarchy
(a concrete model's `concrete_model` is itself; a proxy's is its base). Hand-picked
edge case pins the discriminating clause: a proxy step must yield its concrete
base model's id as the key, not the proxy's.
