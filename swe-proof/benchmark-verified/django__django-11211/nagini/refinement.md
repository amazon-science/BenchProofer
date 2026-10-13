# refinement.md — django__django-11211

The operation-by-operation correspondence between `model.py`'s implementation
(the `prepare_key` impl region + the `base_prepare` and `canonicalize` axioms)
and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The added key-preparation method — `UUIDField.get_prep_value` (`django/db/models/fields/__init__.py:2328`)

Gold hunk (the whole change — a newly added method on `UUIDField`):
```
     def get_internal_type(self):
         return "UUIDField"

+    def get_prep_value(self, value):
+        value = super().get_prep_value(value)
+        return self.to_python(value)
+
     def get_db_prep_value(self, value, connection, prepared=False):
```

Before the patch `UUIDField` defines no `get_prep_value` and inherits
`Field.get_prep_value` (the identity/`Promise`-cast passthrough). The fix adds
a `UUIDField`-specific `get_prep_value` that, after the base preliminary
coercion, runs `to_python` to canonicalize the value into a `uuid.UUID`. The
prefetch join (`GenericForeignKey.get_prefetch_queryset`,
`contenttypes/fields.py:205`) calls `model._meta.pk.get_prep_value(...)` on the
holder's stored `object_pk` (a `str`) and matches it against the related
object's `uuid.UUID` pk (`contenttypes/fields.py:210`) through a dict
(`db/models/query.py:1746-1749` build, `:1770` look up). Without
canonicalization the `str` keys differently from the `uuid.UUID` and the join
silently produces `None`.

| # | model.py impl op (`prepare_key`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: Value` with facets `is_none`, `canon`, `key`, `is_canon_form` | the `value` argument of `get_prep_value` (a `uuid.UUID` / `str` / `int` / `None`) | R | the value is abstracted to its join-observable facets — canonical identity (`canon`) and BOTH halves of the join key: the numeric part (`key`) and the form it is held in (`is_canon_form` = `isinstance(value, uuid.UUID)`) — plus emptiness (`is_none`); see mapping.md §2. |
| A2 | `coerced = base_prepare(value)` | `value = super().get_prep_value(value)` | A-consumed | `super().get_prep_value` is the unchanged base callee `Field.get_prep_value`; on these inputs it is the identity on every facet (it only casts a `Promise`, which never occurs here). The proof consumes its `Ensures` (`Result()` preserves `is_none`/`canon`/`key`/`is_canon_form`) to carry the original value's facets into the `canonicalize` call (mapping.md §3.1). |
| A3 | `return canonicalize(coerced)` | `return self.to_python(value)` | A-consumed | `self.to_python` is the unchanged `UUIDField` canonicalizing parser; on a non-empty value it returns a real `uuid.UUID` (`fields/__init__.py:2342` parse branch, `:2349` already-canonical branch) — so the result is in the canonical object form AND its numeric join key is the canonical identity (`Result().key == coerced.canon == value.canon`); an empty value passes through in the same form. The proof consumes its `Ensures` to discharge both discriminating postconditions and hence `matches_target_key(Result(), value.canon)` (mapping.md §3.2). |

The discriminating content of the change — the result becomes a **canonical
`uuid.UUID` carrying the canonical identity**, rather than the as-stored value
carrying the as-stored key — lives in step A3 (`canonicalize`, i.e. the added
`self.to_python(value)` call). Both halves of that are load-bearing and both are
pinned; see §D. The pre-patch `UUIDField` reaches only the inherited base
coercion and never canonicalizes; `model_prepatch.py` reproduces that (it
returns `base_prepare(value)` and omits the `canonicalize` step) and **fails**
the postcondition
`Implies(not value.is_none, Result().is_canon_form)`
(`model_prepatch.py:179`), which is exactly the spec sensing the change
(G-DIFF).

## B. Why both callees are A-consumed (no A-reference, no kind-3)

The operation that genuinely *changed* is the **addition of the
canonicalization call** to a method that previously did not exist on
`UUIDField` — i.e. the *composition* `to_python(super().get_prep_value(value))`
in place of the inherited bare `Field.get_prep_value(value)`. Both composed
callees are **unchanged** library/field methods the new code merely *invokes*;
neither is the thing being changed and neither is re-implemented in the model.
They are therefore axiomatized as **A-consumed** callees (the proof uses both
`Ensures`), each with the weakest contract the proof needs and each validated
against its real counterpart by G-AX. There is no deep model and hence **no
A-reference**, and no kind-3 (unexpressible-changed-op) step: the changed
operation is expressed as the verified composition A2 ∘ A3.

We do NOT axiomatize the function under change (`get_prep_value` itself is
`prepare_key`, fully implemented and contracted). The `canonicalize` axiom
(`to_python`) is deliberately the WEAKEST sufficient contract: for a non-empty
value it asserts only that the result is in the canonical object form and that
its numeric join key is the canonical identity (and identity for the empty
value); it does NOT claim `to_python` never raises in general (it can
`ValidationError` on malformed input) — the prefetch path only ever feeds it the
well-formed stored representation of an existing pk, so that path is the only
one the proof and G-AX exercise (mapping.md §3.2). Note that the form half is
not an added assumption about the callee's *strength* beyond what its source
states: both of `to_python`'s return statements return a `uuid.UUID` on the
non-`None` path, so the clause is read directly off lines 2342 and 2349.

## C. Where the spec senses the pre-patch behaviour (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: it returns `base_prepare(value)`
only (the inherited `Field.get_prep_value` behaviour), dropping step **A3**
exactly as the pre-patch `UUIDField` lacks its own `get_prep_value`. With the
byte-identical frozen spec it **fails** verification on
`Ensures(Implies(not value.is_none, Result().is_canon_form))`
(`model_prepatch.py:179`) — and would equally fail the numeric clause on the
next line; the verifier reports the first. That is precisely the behaviour the
F2P test observes: `test_prefetch_GFK_uuid_pk` creates an `Article` (UUID pk),
attaches it through a GFK whose `object_pk` stores the UUID's string form, then
asserts `prefetch_related('content_object_uuid')` resolves the GFK back to the
`article` — which requires the prepared key of the stored string to *compare
equal* to the canonical UUID key, i.e. to agree with it on both halves. The
companion clauses (`Result().is_none == value.is_none`,
`Result().canon == value.canon`) keep the spec faithful: a wrong impl cannot
satisfy it by fabricating an identity or dropping emptiness, and the read-only
`value` is held at fractional permission on all four facets so an impl cannot
satisfy the post vacuously by overwriting the input (including by re-labelling
its form — `properties.py`'s `frame-mutate-write-input-form`).

Total correctness: `prepare_key` additionally carries
`Requires(MustTerminate(14))`, with strictly smaller callee measures
(`canonicalize` 10, `base_prepare` 6, `Value.__init__` 2). Nagini's default
semantics are partial correctness, under which a diverging body discharges every
`Ensures` vacuously; the real preparation step is a bounded, loop-free
composition that always returns, so the obligation rejects any implementation
that satisfies the postconditions only by never terminating. The obligation is
stated at the METHOD level because loop invariants alone do not reject a
diverging rival (`properties.py`'s `divergence-nonterminating-body` fails with
`Obligation leak check failed`).

## D. verify(model) ⇒ resolved

The prepared value's four facets are, for every admitted input, a **total
function of the input's facets** under this spec:

* `Result().is_none == value.is_none` and `Result().canon == value.canon`
  (unconditionally);
* for a non-empty value: `Result().key == value.canon` **and**
  `Result().is_canon_form` — i.e. the result is exactly the target-side key for
  identity `value.canon`, which is what `matches_target_key(Result(),
  value.canon)` says;
* for an empty value: `Result().key == value.key` and
  `Result().is_canon_form == value.is_canon_form` — the value is handed back
  unchanged in every facet.

There is no facet left free, so any verifying implementation returns the same
observable value gold returns at the granularity the prefetch join reads. That
granularity is the whole of what the F2P observes: the join is a dict lookup
(`db/models/query.py:1770`) whose outcome is decided by `hash` then `==` on the
`(key, class)` pair, and `hash`/`==` on a `UUIDField` pk read exactly the form
and the 128-bit identity — the two facets §A3 pins.

Both halves are necessary, which is why the earlier numeric-only version of this
document was wrong to claim the numeric clause alone forced equality with
`self.to_python(super().get_prep_value(value))`. It does not: an implementation
returning `self.to_python(value).int` satisfies a numeric-only spec while
`u.int != u`, so the dict lookup lands in the right bucket
(`hash(u) == hash(u.int)`) and then compares unequal, the relation resolves to
`None`, and `test_prefetch_GFK_uuid_pk` fails (measured on that rival: F2P 0/1,
P2P 76/76). Pinning `is_canon_form` closes that gap, and the closure is checked
three ways: `properties.py`'s `overapprox-right-number-wrong-form` (that exact
rival, now rejected on the form clause), `axiom_check.py`'s executable
hash-equal / `==`-unequal / dict-miss demonstration, and `conformance_check.py`,
which resolves every non-empty prepared value against its target key in a real
dict rather than only comparing facet tuples.

By R (the value ↔ its `Value` facets; `uuid.UUID`/`str`/`int`/`None` ↔
`is_none`/`canon`/`key`/`is_canon_form`, mapping.md §2) and the A-consumed
callees, the verified method equals
`self.to_python(super().get_prep_value(value))` on the tested inputs, on both
halves of the join key. By G-AX the real `Field.get_prep_value` meets the
`base_prepare` axiom (A-consumed) and the real `UUIDField.to_python` meets the
`canonicalize` axiom (A-consumed) — in particular the stored string form and the
`uuid.UUID` form of the same UUID prepare to keys that are equal *and compare
equal*. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
