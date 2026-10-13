# refinement.md — django__django-11211

Maps every operation in `implementation_normalizeKey` to its `patch.diff`
counterpart in `UUIDField.get_prep_value` (django/db/models/fields/__init__.py,
added ~:2328). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** op left as the real repo callee in G-CONF (modeled deeply,
not axiomatized), **I** identical concrete op.

## Patch (post-patch added method)
```python
def get_prep_value(self, value):
    value = super().get_prep_value(value)   # base Field.get_prep_value
    return self.to_python(value)            # UUIDField.to_python
```

## Modeling decision
At base_commit `UUIDField` has no `get_prep_value`, so it inherits
`Field.get_prep_value` — an identity pass-through for ordinary values. The prepared
key is therefore whatever shape the value arrived in (a `str` from a text fk
column STAYS a `str`). The gold patch composes two steps: the base pass-through,
then `to_python`, which decodes a text spelling to the `uuid.UUID` it denotes.

The model:
- `UuidValue` carries the three shapes that reach this step: `absent` (`None`),
  `canonical n` (an already-parsed identifier, `n = uuid.int`), `textual s` (a
  text spelling).
- `basePrep` = the base pass-through (identity), modeled deeply (A-reference to
  `Field.get_prep_value`).
- `canonicalValue` = `to_python`, modeled deeply (A-reference): `absent`/`canonical`
  unchanged; `textual s` → `canonical (decodeHex s)`, decoding the hex digits and
  ignoring separators (exactly `uuid.UUID(hex=s).int`).
- `problem_spec_normalizeKey` pins the post-patch result: `result =
  canonicalValue value`. A textual spelling MUST be converted; leaving it as text
  (the inherited identity behavior) violates the spec.

## Operation correspondence
| # | Lean op (`implementation_normalizeKey`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `v := basePrep v` | `value = super().get_prep_value(value)` | I + A-reference | the base pass-through; modeled as identity over `UuidValue` (a non-`Promise` value is returned unchanged). A-reference to `Field.get_prep_value`. |
| 2 | `return canonicalValue v` | `return self.to_python(value)` | R + A-reference | the conversion to a canonical identifier; `textual s` decodes (`decodeHex` = `uuid.UUID(hex=s).int`), `canonical`/`absent` pass through. R: `str`/`uuid.UUID`/`None` ↔ `UuidValue`. A-reference to `UUIDField.to_python`. |

The behavior-changing op is #2: pre-patch there is NO conversion (the inherited
identity leaves a `textual` value as text), so a stored string spelling never
matched a `uuid.UUID` pk; post-patch the conversion canonicalises it. The prepatch
impl omits op #2 (`return v`), reproducing the inherited identity behavior.

## R/I legs ⇒ G-CONF
Op #1 (identity, I) and op #2's R structure (the `UuidValue` ↔ `str`/`uuid.UUID`
refinement and the decode) are the R/I content. `conf_skip = false`:
conformance_check.py transliterates the shadow (`to_python(super().get_prep_value(v))`
over the modeled `UuidValue` domain) and differential-tests it against the REAL
patched `UUIDField().get_prep_value` over ≥10⁵ fuzzed values. The two callees
`basePrep`/`canonicalValue` are A-references left as the real repo callees in the
shadow (they are not substituted by an axiom model), so they are also exercised by
G-CONF rather than by G-AX.

## No A-consumed row
The proof consumes no separately-declared callee axiom — both helpers are spelled
out as pure functions (`basePrep`, `canonicalValue`) and the post-condition is a
direct equation over them. Hence `meta.json axioms = []`; `axiom_check.py` is a
skip stub. `basePrep`/`canonicalValue` are recorded as A-references (deep models of
the real callees, validated by G-CONF), not axioms.

## F2P alignment
- `test_prefetch_GFK_uuid_pk`: an `Article` keyed by a `UUIDField` pk and a
  `Comment` whose GFK points at it via a text `object_pk`. Prefetch must recover
  the related `Article`. The spec pins that the stored text spelling is prepared to
  the SAME canonical identifier as the related object's `uuid.UUID` pk, so the
  prefetch keys match. The prepatch impl (identity — text stays text) cannot
  satisfy the discriminating clause `result = canonicalValue (textual s)` whenever
  `s` is a real spelling, so the related object is not found — exactly the bug.
`patch.diff` (gold verbatim) makes the harness resolve.
