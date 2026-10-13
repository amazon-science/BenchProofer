# mapping.md — django__django-15814

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5eb6a2b33d70b9889e1cafa12594ad6f80773d3a`, states the type
abstraction, and gives the provenance of the deep-model reference.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `related_reported_fields(canonical, related, related_pk, chosen_attr)` | `Query.deferred_to_data(self, target)` — `django/db/models/sql/query.py:721` (the patched body line 751, the `defer == False` else-branch lines 787-802) | the modeled changed function, restricted to the single-related-model `.only("rel__attr")` scenario the F2P test exercises |
| `canonical_of(canonical, model)` *(deep model — A-reference)* | `model._meta.concrete_model` attribute read (used at `query.py:737`, `740`, `751` post-patch, `761`, `776`) | pure spec: a model's storage/canonical representative; the unchanged attribute access the patch inserts a call to, validated `canonical_of == ._meta.concrete_model` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `must_include` (`Dict[int, Dict[int,int]]`) | the local `must_include` dict in `deferred_to_data` (`query.py:737` init, `757` add) | per-model accumulator of "passthrough" requirements (each model's pk) |
| `seen` (`Dict[int, Dict[int,int]]`) | the local `seen` dict in `deferred_to_data` (`query.py:765` add, `787-795` merge) | per-model accumulator of the reported (restricted) requirements |
| `related` (`int`) | `cur_model = source.remote_field.model` (`query.py:750`), the FK-target model before normalization | the traversed related model (may be a proxy = non-canonical alias) |
| `related_pk` (`int`) | `opts.pk` added by `add_to_dict(must_include, cur_model, opts.pk)` (`query.py:757`) | the related model's primary-key attribute (its `attname` is what the downstream identification step looks up) |
| `chosen_attr` (`int`) | `field = opts.get_field(parts[-1])` recorded via `add_to_dict(seen, model, field)` (`query.py:758-765`), with `model = field.model._meta.concrete_model` | the `.only(...)` restricted attribute on the related model |

The pre-patch behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): at `query.py:751` the line read
`opts = cur_model._meta` with `cur_model` still the *proxy* model from line 750,
so `add_to_dict(must_include, cur_model, opts.pk)` (line 757) keyed the pk by
the **proxy**. The patch inserts `cur_model = cur_model._meta.concrete_model`
before line 751, so `opts`, the `must_include` key, and the read-out all use the
**concrete** model.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a model class (e.g. `ProxyTrackerUser`, `TrackerUser`) | `int` token | distinct classes ↔ distinct ints; a proxy and its concrete parent are distinct tokens related by `canonical` |
| `model._meta.concrete_model` | `canonical_of(canonical, model)` over a `Dict[int,int]` map | a proxy maps to the token of the model it aliases; a concrete (non-proxy) model maps to itself; idempotent |
| a field `attname` (e.g. `'id'`, `'status'`) | `int` token | distinct attnames ↔ distinct ints; `related_pk != chosen_attr` |
| `add_to_dict(d, key, value)` (`query.py:2585`) — adds `value` to the set `d[key]`, creating it if absent | guarded dict-of-set update: `if key in d: d[key].add(v) else d[key] = {v}`, with the set carried as a `Dict[int,int]` whose keys are the attname tokens | set membership ↔ key membership in the inner `Dict[int,int]` |
| the `defer == False` merge of `must_include` into `seen` (`query.py:787-795`): for each model in `must_include`, if it is in `seen` update its set, else insert | per-key set-union in the impl merge block | `target[model] == {f.attname for f in seen[model]}` after merge (`query.py:801-802`) |
| the per-model `target` mapping built at `query.py:801-802` (`target[model] = {f.attname for f in seen[model]}`) | `Result()` = the full per-model mapping `seen` (`Dict[int,Dict[int,int]]`); the related model's reported attname set is `Result()[canonical_of(canonical, related)]` | the per-model reported attname mapping the loader hands downstream. The model returns the whole mapping (not a single pre-read bucket) so the contract can constrain the KEYING/provenance (canonical key present, closure, no scatter under the raw alias key), not just one bucket's contents |

`str`/class objects are not Nagini-expressible, so models and attnames are
`int` tokens and the field-set is a `Dict[int,int]` used as a set; dict access is
guarded by an explicit membership test (`k in d` before `d[k]`).

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `canonical_of` deep model ↔ `Model._meta.concrete_model` (A-reference)
**Callee:** Django's `Options.concrete_model` (the `_meta.concrete_model`
attribute), `django/db/models/options.py`. For a proxy model it is the concrete
(non-proxy) model the proxy is backed by; for a non-proxy (concrete) model it is
the model itself. The map is therefore idempotent:
`m._meta.concrete_model._meta.concrete_model is m._meta.concrete_model`.

There is **no consumed `@ContractOnly` axiom**: the canonical-key selection is
the behaviour under change and is modelled deeply by `canonical_of` plus the
impl (the `cur_model = canonical_of(...)` normalization mirrors the patch's
`cur_model = cur_model._meta.concrete_model`). The deep model is validated equal
to the real attribute out-of-band by axiom_check.py (G-AX): it constructs proxy
and concrete model classes and asserts `concrete_model` is the concrete parent
for a proxy, is the class itself for a concrete model, and is idempotent — and
that the end-to-end `deferred_to_data`-style accumulation places the related
model's pk into the same reported bucket as the chosen attribute iff the
canonical normalization is applied. Provenance: Django docs "proxy models"
(https://docs.djangoproject.com/en/4.2/topics/db/models/#proxy-models) and
`django/db/models/options.py` (`Options.concrete_model`).

The single behavioural change the F2P test (`test_select_related_only`,
`proxy_models.tests.ProxyModelTests`) observes: with the related FK target a
proxy (`Issue.assignee -> ProxyTrackerUser`, a proxy of `TrackerUser`), the
related model's pk (`id`) must be reported under the concrete `TrackerUser`
bucket alongside the `.only("assignee__status")` attribute; pre-patch it was
keyed by the proxy and so dropped from that bucket, raising
`ValueError: 'id' is not in list` in `RelatedPopulator.__init__`
(`django/db/models/query.py:2599`).

**Soundness check (G-AX):** `axiom_check.py` defines a concrete model, a proxy
of it (and a proxy-of-proxy), reads the real `._meta.concrete_model`, asserts
the `canonical_of` properties (idempotence, proxy→concrete, concrete→self), and
replays the abstract accumulation both with and without the canonical
normalization, asserting the pk lands in the related model's reported bucket iff
normalized. It imports only Django's ORM (the very module the patch lives in);
exit 0 iff sound.
