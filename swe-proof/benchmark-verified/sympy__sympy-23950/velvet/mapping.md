# mapping.md — sympy__sympy-23950

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 88664e6e0b781d0a8b5347896af74b555e92891e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `sympy/sets/contains.py`.
`spec_provenance: cold` — derived from `problem_statement` + gold `patch` + the
real source at `base_commit` only.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `asSet (a : MembershipAssertion)` | `Contains.as_set(self)` — `sympy/sets/contains.py:47-48` | the modeled changed function: the set form of a membership assertion |
| `MembershipAssertion` (structure) | a `Contains(elem, container)` instance | the assertion object; carries exactly the two components the conversion needs |
| `a.elem` | `self.args[0]` — the tested element | the element being tested for membership (read, not returned) |
| `a.container` | `self.args[1]` — the set the element is tested against | the collection the membership ranges over (this IS the result) |
| `out : Except ConversionErr Nat` | the return value of `as_set()` | `Except.ok v` ↔ a normal return of `v`; `Except.error .unavailable` ↔ the conversion declining to produce a set (the pre-image raised, see refinement.md) |

The gold patch changes ONLY the body of `Contains.as_set`: at base_commit it
declines to produce a set; the fix returns the assertion's second stored
component (`self.args[1]`) — the set the membership is taken over. There are no
callees: the body reads the object's own stored arguments and returns one of
them directly.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Contains(x, S)` membership assertion | `MembershipAssertion { elem, container }` | the object ↔ the structure carrying its two args as opaque identifiers; `self.args[0]` ↔ `elem`, `self.args[1]` ↔ `container` |
| a set object (the second arg / the result) | a `Nat` identifier | identity of the set object ↔ a `Nat` token; equality of set objects ↔ `Nat` equality. The conversion only ever returns the *same* object stored at `args[1]`, so identity-level modeling is exact for this behavior |
| a normal `return v` | `Except.ok v` | success ↔ `Except.ok` |
| the conversion being unavailable (the pre-image declines / raises) | `Except.error .unavailable` | the single non-success outcome the spec distinguishes |

The assertion `a` is a read-only input — NOT declared `mut`; `asSet` reads its
components, returns one of them, and mutates nothing (directive 5: no `mut`
params, so no frame obligation arises).

Why `Nat` for the element and the set, not a deeper model: the conversion's
entire observable behavior is *which of the two stored components it hands
back*. Modeling them as distinct opaque identifiers is the WEAKEST carrier that
still lets the spec discriminate "returns the collection" from "returns the
element" and from "declines" — and that discrimination is exactly what the
issue and the F2P test demand. A richer set model would add nothing the
postcondition consults.

## 3. Callee provenance

There are **no axioms and no deep-model references** in this bundle. The single
changed operation reads the object's own stored arguments and returns the
second one; it calls nothing. Hence `meta.json` has empty `axioms` /
`deep_model_references`, there is **no `axiom_check.py`**, and **G-AX skips**
(gates.py `gate_ax`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`23950`** so the
consumer-side verdict is reproducible. The shadow it builds transliterates the
I-tagged op (`return the assertion's container component`, i.e. `c.args[1]`) and
diffs it against the real patched `Contains.as_set()` over a fuzzed pool of
membership assertions built from a variety of elements and set kinds
(`S.Reals`, `S.Integers`, `FiniteSet`, `Interval`, `S.EmptySet`, …). Assertions
whose construction collapses to a plain boolean/Set (the `Contains.eval` fast
path) are skipped — `as_set` is meaningful only on assertions that remain a
symbolic membership statement, which is precisely where the F2P test lives.
