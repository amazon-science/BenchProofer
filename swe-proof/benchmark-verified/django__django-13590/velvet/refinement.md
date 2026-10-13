# refinement.md — django__django-13590

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`reconstructSequence` `do` block plus the deep `resolvedSeq`/`rebuild*` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no axioms** (A) in this
bundle. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reconstruction site — `resolve_lookup_value` list/tuple branch

Gold hunk (`django/db/models/sql/query.py:1077-1086`):
```
 elif isinstance(value, (list, tuple)):
     # The items of the iterable may be expressions and therefore need
     # to be resolved independently.
-    return type(value)(
+    values = (
         self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
         for sub_value in value
     )
+    type_ = type(value)
+    if hasattr(type_, '_make'):  # namedtuple
+        return type_(*values)
+    return type_(values)
 return value
```

| # | Solution.lean impl op (`reconstructSequence`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s : SeqVal` (`positionalCtor`, `items`) | `value` (the `list`/`tuple`/namedtuple) | R | a sequence ↔ its two touched observables: `hasattr(type(value), '_make')` ↔ `positionalCtor`; `list(value)` ↔ `items` (mapping.md §2). G-CONF bridges via `observe`. |
| A2 | `f : Int → Int` (free total function) | `self.resolve_lookup_value(sub_value, can_reuse, allow_joins)` per member | R | the per-member resolution, UNCHANGED by the patch (present identically pre- and post-patch). Modeled as an arbitrary total resolver, so the spec quantifies over ALL `f` — strictly weaker than the real callee, no axiom owed (directive 7, mapping.md §3). G-CONF instantiates `f` with several in-process resolvers. |
| A3 | `let resolved := s.items.map f` | `values = (resolve_lookup_value(sv,…) for sv in value)` | I | element-wise application of the resolver in order; the generator's lazy `map` ↔ `List.map` (the order/values are identical, G-CONF-checked). |
| A4 | `if s.positionalCtor then rebuildPositional … else rebuildIterable …` | `type_ = type(value); if hasattr(type_, '_make'): return type_(*values); return type_(values)` | I | the CHANGED dispatch, modeled deeply: positional-constructor types are rebuilt by supplying members positionally (`rebuildPositional` ↔ `type_(*values)`), all others from the iterable (`rebuildIterable` ↔ `type_(values)`). BOTH helpers carry the real primitives' partiality: `rebuildIterable` errors on a positional type (namedtuple + single iterator ⇒ `TypeError`), and `rebuildPositional` errors on a non-positional nonempty carrier (`list`/`tuple` + splat ⇒ `TypeError`; the empty splat degenerates to the zero-arg call and succeeds). Reconstruction preserves the type and member order. G-CONF refutes any divergence, including at helper level. |
| A5 | result `Except RebuildErr SeqVal`; `.ok` for both branches here | the returned reconstructed container | R + I | post-patch reconstruction always SUCCEEDS (`resolvedSeq` is total-`ok`); the `Except.error` constructors model the two real failure modes of the UNGUARDED reconstruction primitives: `.iterableNotAccepted` = `type_(<iterator>)` on a namedtuple raising `TypeError` (the pre-patch bug), and `.positionalNotAccepted` = `type_(*values)` on a `list`/`tuple` with ≥1 member raising `TypeError` (splat gives the constructor N positional args where it takes exactly one iterable; the gold patch guards against this with `hasattr(type_, '_make')`). On the gold path neither error arises (G-CONF: oracle never raises; helper-level differential in `conformance_check.py` pins both partialities). |

Discriminating content of the change — a positional-constructor (namedtuple)
type must be reconstructed by `type_(*values)`, never by handing it a single
iterable — lives in the `if s.positionalCtor then rebuildPositional …` branch
(model) ⇔ the added `if hasattr(type_, '_make'): return type_(*values)` (real).
The pre-patch unconditionally did `type(value)(<iterator>)`;
`Solution_prepatch.lean` reproduces that (`rebuildIterable s.positionalCtor
resolved` for every type) and **fails** the postcondition `out =
resolvedSeq …`, leaving the goal `s.positionalCtor = false` (G-DIFF) — exactly
the namedtuple case the F2P `test_range_lookup_namedtuple` exercises.

## B. No consumed axioms / no A-reference callee

The only operation that genuinely *changed* — the container reconstruction — is
modeled **deeply** (the `resolvedSeq`/`rebuildPositional`/`rebuildIterable`
defs + the `positionalCtor` branch), not hidden behind an axiom about the
function under change. The per-member resolver is a free function, owed no
contract. Hence: no module-level `axiom`, no `axiom_check.py`, `gates.G-AX =
skip` (cf. django__django-11149).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed dispatch is expressed concretely (A4); the
type-capability test `hasattr(type_, '_make')` is abstracted to the boolean
`positionalCtor` (R, mapping.md §2). Nothing inexpressible is hidden.

## D. verify(Solution) ⇒ resolved

`reconstructSequence` verifies only if its output equals `resolvedSeq` — a
reconstruction that ALWAYS succeeds, preserves the sequence type, carries the
per-member-resolved values in order, AND (A4) supplies members positionally for a
positional-constructor type. By R (`SeqVal ↔ value`, `f ↔ resolve_lookup_value`,
mapping.md §2) the verified reconstruction equals the gold patch's
`type_(*values)`/`type_(values)` dispatch on every tested carrier; by G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs across
`list`/`tuple`/`namedtuple`. Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there is no axiom trust point.
