# refinement.md — django__django-15814

The operation-by-operation correspondence between `model.py`'s implementation
(the `related_reported_fields` impl region, the deep `canonical_of` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`Ensures`, **A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fixed site — `Query.deferred_to_data` (`django/db/models/sql/query.py:751`)

Gold hunk (insert one line after `cur_model = source.remote_field.model`):
```
                    cur_model = source.remote_field.model
+                cur_model = cur_model._meta.concrete_model
                 opts = cur_model._meta
```
The traversed related model `cur_model` (derived from the relation, line 750) is
normalized to its concrete model before it is used as the key for the
`must_include` accumulator (`add_to_dict(must_include, cur_model, opts.pk)`,
line 757) and for `opts`.

| # | model.py impl op (`related_reported_fields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `related, related_pk, chosen_attr: int`; `canonical: Dict[int,int]` | `cur_model` (model class), `opts.pk`, the `.only` attribute; `_meta.concrete_model` | R | model classes ↔ `int` tokens; field attnames ↔ `int` tokens; `._meta.concrete_model` ↔ the `canonical` map (mapping.md §2). |
| A2 | `cur_model = related` | `cur_model = source.remote_field.model` (line 750) | R | the FK-target model before normalization (the relation traversal is not the operation under change; it is the identical concrete step that yields the possibly-proxy model). |
| A3 | `cur_model = canonical_of(canonical, cur_model)` | `cur_model = cur_model._meta.concrete_model` (the inserted line) | A-reference | the changed operation is modelled **deeply**: `canonical_of` (the `@Pure` map application in the `pure` region) IS `._meta.concrete_model`. No `@ContractOnly` axiom is consumed; the deep model is validated **== the real attribute** out-of-band by G-AX (axiom_check.py): for a proxy it is the concrete parent, for a concrete model it is itself, and it is idempotent (mapping.md §3.1). |
| A4 | `must_include[cur_model] = {related_pk}` (via `pk_set`) | `add_to_dict(must_include, cur_model, opts.pk)` (line 757) | R + I | `add_to_dict`'s set-insert ↔ the guarded `Dict[int,int]`-as-set insert (mapping.md §2); the *key* is `cur_model`, which by A3 is now the concrete model — the load-bearing consequence of the fix. |
| A5 | `seen[rel_key] = {chosen_attr}` with `rel_key = canonical_of(canonical, related)` | `add_to_dict(seen, model, field)` with `model = field.model._meta.concrete_model` (lines 760-765) | R + I | the leaf `.only` attribute is recorded under the related model's concrete identity in BOTH versions (line 761 already normalizes the leaf's `model`); modelled as the same concrete key `rel_key`. |
| A6 | the per-key merge `if cur_model in seen: seen[cur_model] ∪= must_include[cur_model] else seen[cur_model] = must_include[cur_model]` | the `defer == False` else-branch merge loop (lines 787-795): for each `model, values` in `must_include`, `seen[model].update(values)` if present else `seen[model] = values` | I | identical per-model-key set merge, restricted to the one related-model key (the root-model key is concrete in both versions and carries no discriminating content). |
| A7 | `return seen` (the full per-model mapping `Dict[int,Dict[int,int]]`) | `target[model] = {f.attname for f in seen[model]}` over all models, the per-model `target` mapping (lines 801-802) | R | the per-model reported attname mapping (model -> its attname set), keyed by concrete identity; the related model's bucket is `Result()[canonical_of(canonical, related)]` (mapping.md §2). Returning the full mapping (not a single pre-read bucket) lets the postcondition constrain the KEYING/provenance, not just one bucket's contents. |

The discriminating content of the change lives in A3→A4: the pk is keyed by the
**concrete** model (`canonical_of(related)`), matching the key the leaf
attribute (A5) and the read-out (A7) use. The pre-patch kept `cur_model` as the
raw (proxy) model, so the pk was keyed by the proxy; when the related model is a
non-canonical alias (`related != canonical_of(related)`) the merge (A6) folds
the pk into a *different* bucket (`seen[related]`), leaving
`seen[canonical_of(related)]` without the pk. `model_prepatch.py` reproduces
exactly that (drops the `cur_model = canonical_of(canonical, cur_model)` step)
and **fails** the discriminating postcondition
`Ensures(related_pk in Result()[canonical_of(canonical, related)])` — and also
the provenance clause `Ensures(related != canonical_of(...) ==> related not in
Result())`, since it creates a `seen[related]` bucket — the spec sensing the
change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — keying the related model's passthrough pk by its concrete identity
rather than its raw (proxy) identity — is modelled **deeply** (the
`canonical_of` map application consumed at A3, an **A-reference**, plus the
identical per-key accumulation/merge), not hidden behind an axiom about the
function under change. There is **no consumed `@ContractOnly` axiom**: the only
non-trivial callee, `._meta.concrete_model`, is the unchanged attribute the
patch composes, and it appears only as the **A-reference** that G-AX validates
the deep `canonical_of` model against.

## C. verify(model) ⇒ resolved

The postcondition is no longer the purely-extensional "Result contains the two
attributes" that the batch01 adversarial panel broke (it admitted a disconnected
literal, an over-fetch, and a bug-retaining post-hoc injection). It now pins the
**keying/provenance** of the reported mapping the downstream identification step
depends on. `related_reported_fields` verifies only if, for the related model's
**canonical** identity `rk = canonical_of(canonical, related)`:

1. **Provenance / canonical keying** — `rk in Result()` and BOTH the chosen
   attribute (A5) and the primary key (A3+A4+A6) live in `Result()[rk]`,
   self-keyed. A reported mapping that ignores the canonical key (a disconnected
   literal keyed by the raw model) cannot satisfy `rk in Result()` with the pk
   in that bucket.
2. **Closure** — `Forall a :: a in Result()[rk] ==> a == related_pk or a ==
   chosen_attr`: the canonical bucket holds nothing else, so an over-fetch
   (a spurious extra attname the downstream `init_list` index logic does not
   tolerate) is rejected.
3. **Anti-scatter / causality** — `related != rk ==> related not in Result()`:
   when the related model is a non-canonical alias, its raw identity is not a
   key at all, so the pk cannot be lodged under the raw (proxy) bucket. This is
   precisely what the pre-patch keying and a "paper over the symptom" injection
   do, and it is now rejected.

By R (model/attname ↔ `int`, `add_to_dict` ↔ guarded set-insert, the per-model
`target` mapping ↔ the returned `seen`) the verified accumulation equals
`deferred_to_data`'s `target` restricted to the related model's concrete bucket
on the tested `.only("rel__attr")` input; by G-AX the deep model `canonical_of`
equals the real `._meta.concrete_model` (A-reference). Therefore a model
satisfying this spec, refined by the map above, places the related model's pk
into its **concrete** reported bucket alongside the chosen attribute, with no
over-fetch and without scattering the pk under the proxy — exactly the gold
patch's behaviour up to type refinement and the audited attribute, and the gold
patch resolves (G-RESOLVE). With the pk present in the concrete related model's
reported bucket, the downstream `RelatedPopulator.__init__` finds the pk attname
in `init_list` (`django/db/models/query.py:2599`) and no `ValueError` is raised;
the F2P test `test_select_related_only` passes.

**Adversarial re-panel (verifier env).** Against this frozen spec the four
batch01 counterexamples were re-checked: the disconnected literal FAILS the
provenance clause; the over-fetch FAILS the closure clause; the bug-retaining
post-hoc injection FAILS the anti-scatter clause; a behaviourally-correct
direct-build of the canonical bucket still verifies (positive control). The gold
skeleton (`model.py`) verifies; the pre-patch skeleton (`model_prepatch.py`)
fails the discriminating + provenance clauses. The §C claim that "a verifying
implementation, refined per the map, resolves" therefore holds under the
strengthened contract.

The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
