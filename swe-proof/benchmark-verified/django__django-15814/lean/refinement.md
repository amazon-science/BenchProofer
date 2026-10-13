# refinement.md — django__django-15814

Maps every operation in `implementation_relationModelKeys` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

The modeled function is the per-step body of the `for name in parts[:-1]` loop in
`Query.deferred_to_data` (`django/db/models/sql/query.py:719-753`). The post-patch
step body is:

```python
for name in parts[:-1]:
    old_model = cur_model
    ...
    source = opts.get_field(name)
    if is_reverse_o2o(source):
        cur_model = source.related_model
    else:
        cur_model = source.remote_field.model
    cur_model = cur_model._meta.concrete_model     # <-- the added line
    opts = cur_model._meta
    if not is_reverse_o2o(source):
        must_include[old_model].add(source)
    add_to_dict(must_include, cur_model, opts.pk)  # cur_model used as the dict KEY
```

| # | `implementation_relationModelKeys` op | `patch.diff` / post-patch counterpart | tag | notes |
|---|---|---|---|---|
| 1 | `let mut keys : List Nat := []` | the accumulator of model keys recorded into `must_include` over the loop | I | accumulator init (models keyed across the traversal) |
| 2 | `for m in steps do` | `for name in parts[:-1]:` | R | one relation step ↔ one resolved `RelModel`. The resolution branch (`source.related_model` / `source.remote_field.model`, `query.py:747-751`) is UNCHANGED by the patch and selects WHICH model is reached; modeled as the already-resolved `RelModel` carried in `steps` (mapping.md bijection) |
| 3 | `let curModel := baseOf m` | `cur_model = cur_model._meta.concrete_model` | R | **the changed op, modeled DEEPLY.** `cur_model._meta.concrete_model` ↔ `baseOf m = m.baseIdent` (the base model that owns the shared storage). Idempotent on base models (`baseIdent = ident`), as `_meta.concrete_model` is the class itself for a non-proxy model (`options.py:141-142`) |
| 4 | `keys := keys ++ [curModel]` | `add_to_dict(must_include, cur_model, opts.pk)` — `cur_model` used as the dict key | R | one model-key registration ↔ one appended key. The pk value recorded (`opts.pk`) and the dict's set-merge semantics are unchanged by the patch and not observed by the changed key decision; the spec pins which model is KEYED, in step order |
| 5 | `return keys` | the sequence of model keys registered into `must_include` over the steps | I | the produced key list, in traversal order |

## No axioms

- **No A-consumed rows.** The behavior the patch changes — keying each step's
  identifier requirement under the *base* (concrete) model rather than the resolved
  (possibly proxy) model — is modeled DEEPLY by `baseOf`/`baseIdent` on `RelModel`
  (SPEC_GUIDE §3: a deeply-modeled changed op is never axiomatized). No external
  callee property is consumed by the proof, so the `axioms` region is empty and
  **G-AX skips**.
- **No A-reference rows.** Nothing in the impl delegates to an opaque callee whose
  real behavior the spec needs validated. The resolution branch, `is_reverse_o2o`,
  `opts.get_field`, `add_to_dict`, and the surrounding `must_include`/`seen`/`defer`
  machinery are all either unchanged or not observed by the modeled key decision
  (mapping.md "Callee provenance").

## Bug visibility (G-DIFF)

The pre-patch step keys the requirement under the resolved model AS-IS, modeled as
`curModel := m.ident`. `Solution_prepatch.lean` carries this buggy op together with
the carried-over gold-style proof; on an alias (proxy) step — where `m.ident ≠
m.baseIdent` — the buggy impl appends `m.ident` where the spec demands `baseOf m =
m.baseIdent`, so the proof's final `rfl` no longer holds and verification FAILS
(confirmed: exit 1, `rewrite` finds no occurrence of the `baseOf`-keyed loop). This
is exactly the discriminating behavior of FAIL_TO_PASS `test_select_related_only`:
a query that follows a relation to a proxy model and restricts loaded fields must
key the load plan under the proxy's concrete base, otherwise the base's identifier
column is missing from `init_list` and `RelatedPopulator.__init__` raises
`ValueError: 'id' is not in list`.

## Conformance (G-CONF)

The impl region is genuine R/I content (the concrete-model normalization + the
per-step key registration), so `conf_skip = false`. `conformance_check.py` builds
the R/I shadow (key = `baseIdent`) and differential-tests it against an in-process
replica of the POST-PATCH loop, which resolves each step's model and takes
`cur_model._meta.concrete_model` using stand-in `Model`/`Options` classes that
mirror the proxy/concrete hierarchy (a concrete model's `concrete_model` is itself;
a proxy's is its base), over ≥1e5 fuzzed inputs, with the proxy case
well-represented. Hand-picked edge case pins the discriminating clause: a proxy
step yields its concrete base model's id as the key.
