# refinement.md — django__django-14672

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`comparisonKey` `do` block, the deep `canonicalize` model, and the `keyHashable`
predicate) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed site — `ManyToManyRel.identity`

Gold hunk (`django/db/models/fields/reverse_related.py:310-315`):
```
     def identity(self):
         return super().identity + (
             self.through,
-            self.through_fields,
+            make_hashable(self.through_fields),
             self.db_constraint,
         )
```

`identity` builds the comparison/hash key of the relation descriptor by
appending three elements to the inherited prefix: `through`, the through-fields
slot, and `db_constraint`. `__hash__` is `hash(self.identity)` and `__eq__`
compares `self.identity == other.identity`. The bug: when `through_fields` is a
Python `list` it is unhashable, so `hash(self.identity)` raises `TypeError`. The
fix wraps that one slot in `make_hashable`, which leaves already-hashable values
unchanged and converts an order-only `list` into the equal `tuple`.

`Solution.lean` models the key as `List Comp`: the inherited prefix + `through`
become the read-only `pre` components, `db_constraint` becomes the read-only
`post` component, and the through-fields slot is the one `Comp.slot` whose
canonical form the change controls.

| # | Solution.lean impl op (`comparisonKey`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `pre : List Comp`, `post : List Comp`, with `require keyHashable pre/​post` | `super().identity + (self.through, …, self.db_constraint)` — the already-hashable surrounding tuple elements | R | each surrounding element is already hashable (the prefix elements were themselves made hashable upstream — e.g. `make_hashable(self.limit_choices_to)` at `:126` — and `through`/`db_constraint` are a model object / bool). Modeled as opaque hashable `Comp`s (mapping.md §2). G-CONF represents them as hashable sentinels. They are read-only (not `mut`); directive 5. |
| A2 | `slot : Slot` parameter | `self.through_fields` | R | the through-fields slot value: `None` ↔ `Slot.none`; a `tuple` of names ↔ `Slot.seq names false`; a `list` of names ↔ `Slot.seq names true` (mapping.md §2). |
| A3 | `let canon := canonicalize slot` | `make_hashable(self.through_fields)` | A-reference + I | the changed callee application is modeled **deeply**: `canonicalize` (pure region) IS the canonicalization — absent slot unchanged, sequence → same items in canonical immutable (hashable) form. No consumed `makeHashable` axiom. The structural `let`/assembly ops are **I** (concrete, transliterated by G-CONF); the equality `canonicalize == real make_hashable` on the slot domain is the **A-reference** G-AX validates (mapping.md §3.1). |
| A4 | `return pre ++ [Comp.slot canon] ++ post` | `(self.through, make_hashable(self.through_fields), self.db_constraint)` appended to `super().identity` | I | the key is the prefix, then the canonical slot component, then the suffix — the same tuple assembly, order preserved. |

Discriminating content of the change — an order-only sequence slot
(`Slot.seq xs true`, the `list` case) must enter the key as its **canonical**
form (`Slot.seq xs false`), making the whole key usable as a hash key. This lives
in two frozen post-conditions:
- `ensures out = pre ++ [Comp.slot (canonicalize slot)] ++ post` — the slot is
  placed in canonical form (content + immutability), not raw;
- `ensures keyHashable out = true` — the whole key is usable as a hash key.

`Solution_prepatch.lean` reproduces the actual bug: it places the slot **raw**
(`Comp.slot slot`) into the key. `prove_correct` then fails on BOTH clauses — the
unsolved goals are exactly `slot.isHashable = true` (a loose sequence is not
hashable: the `TypeError` the issue reports) and the canonicalization-content
equality (G-DIFF). This is the single independently-observable fixed behaviour
(the F2P `test_reverse_inherited_m2m_with_through_fields_list_hashable` asserts
both that the relation is hashable and that a `list`-through_fields relation
hashes EQUAL to its inherited copy — the equality content `canonicalize` pins).

## B. No consumed axioms

This bundle ships **no consumed axioms**. The one unchanged callee the change
applies (`make_hashable`) is modeled **deeply** as `canonicalize` (an
A-reference, step A3), validated `== make_hashable` by G-AX over the slot domain
(`None` / tuple / list of names) — boundary + 20 000 fuzz. The proof borrows no
soundness from an opaque oracle: every post-condition is dischargeable only by
the canonical slot the modeled branch actually produces (directive 8).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
wrapping the slot in the canonicalizer — is modeled **deeply** (`canonicalize`,
step A3), not hidden behind an axiom about the function under change. There is no
`makeHashable` axiom the proof consumes.

## D. verify(Solution) ⇒ resolved

`comparisonKey` verifies only if its output places the slot in canonical form
(A3) and the whole key is hashable (`keyHashable out`). By R (`Slot`/`Comp`
carriers ↔ the identity-tuple elements; loose `list` ↔ `Slot.seq _ true`) the
verified key equals `super().identity + (through, make_hashable(through_fields),
db_constraint)` on the slot domain F2P exercises; by G-AX the deep model
`canonicalize` equals the real `make_hashable` (A-reference) — so the produced
slot is exactly `make_hashable(self.through_fields)` and the assembled tuple is
hashable (no `TypeError`), AND a `list` and its `tuple` form canonicalize equal
(so `__hash__` agrees with `__eq__`, the inherited-relation equality the F2P
test asserts); by G-CONF the R/I transliteration of the assembly agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: A-reference soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
