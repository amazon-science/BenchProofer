# mapping.md — sympy__sympy-23950

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 88664e6e0b781d0a8b5347896af74b555e92891e`, states the type
abstraction, and gives the provenance of the one in-container soundness check.

Repo file under change: `sympy/sets/contains.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `solution_region(self)` | `Contains.as_set(self)` — `sympy/sets/contains.py:47` | the modeled changed method (the membership assertion's set-of-values view) |
| `MembershipAssertion` | `Contains` (a `BooleanFunction`) — `sympy/sets/contains.py:8` | minimal abstraction of the membership-assertion object, carrying only its two touched operands |
| `self.element` | `self.args[0]` of the `Contains` instance (the asserted element `x`) | first operand: the element |
| `self.region` | `self.args[1]` of the `Contains` instance (the STORED set operand) | second operand: the set whose membership is asserted; the value the view returns (by identity) |
| `Region` | the operand objects `x` and `s` (a `Symbol`/`Set`/sympy `Basic`) | opaque object reference: only object identity is observable |

`Contains(x, s)` is constructed via `BooleanFunction.__new__`/`Application`,
which stores the operands as `self.args == (x, s)` in operand order (`Basic.args`
returns the constructor operands). The element operand is stored identically
(`self.args[0] is x`); the set operand is stored as an object equal to `s`
(`self.args[1] == s` — sympy may rebuild/canonicalize the operand into an equal
object, so this is `==` against the input, while `as_set()` returns that STORED
operand BY IDENTITY: `as_set() is self.args[1]`). The change replaces the method
body `raise NotImplementedError()` (line 48) with `return self.args[1]` —
returning the stored set operand, which equals `s` and is what the F2P test
compares.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Contains` instance (a `BooleanFunction` / `Basic`) | `MembershipAssertion` class with two reference fields | `self.args[0]` ↔ `self.element`; `self.args[1]` ↔ `self.region`; no other facet of `Contains` is touched by the change, so it is omitted |
| the operand objects `x`, `s` (sympy `Basic`: `Symbol`, `Set`, `FiniteSet`, `S.Integers`, `S.Reals`, …) | `Region` (opaque reference) | only object identity matters: the method returns the *same* STORED operand object (`as_set() is self.args[1]`), so the carrier need only support `is`. The F2P test observes equality of the returned object with the passed-in set, satisfied because the stored operand equals that set. |
| `return self.args[1]` (return the second STORED operand) | `return self.region` | the same component selection; postcondition `Result() is self.region` ↔ "the returned object is the stored set operand `self.args[1]`" (real `as_set() is self.args[1]`, confirmed in-container) |
| `raise NotImplementedError()` (pre-patch deferral) | `raise ViewNotProduced()` (prepatch skeleton) | a user-defined exception stands in for the builtin (a builtin exception in an `Exsures` crashes the Nagini translator); the no-`Exsures` spec makes any raise a verification failure — exactly the deferral the change removes |

`Contains.as_set` performs no library/utility call; the change is a pure
component selection. There is therefore **no `@ContractOnly` axiom** in this
bundle (no unchanged opaque callee is consumed).

The gold body is a single straight-line `return` — it always terminates. The
model carries this as `Requires(MustTerminate(2))` (Nagini's obligation
system): a total-correctness obligation matching the real method's guaranteed
termination. It closes the vacuous-divergence hole (a self-recursive or
looping body that never returns would otherwise satisfy the value
postcondition vacuously while its real counterpart hangs `test_as_set`), and
it is faithful — the real `as_set` completes on every call, and the gold-shaped
straight-line body discharges the obligation trivially.

## 3. In-container soundness check (G-AX / axiom_check.py)

There is no consumed axiom and no deep model of a library callee to validate.
The single soundness obligation is the **type-refinement (R) faithfulness** of
the field bijection used by refinement.md step 1: that a real `Contains(x, s)`
stores its operands as `self.args == (x, s)`, so that `self.args[1]` (what the
gold returns) is the set `s` (modelled as `self.region`).

`axiom_check.py` constructs real `Contains(x, s)` objects in-container over the
F2P operands and adversarial fuzz (`Symbol`/`FiniteSet`/`S.Integers`/`S.Reals`/
`Interval`/nested sets) and asserts, for each:

  * `Contains(x, s).args[1] == s` — the modelled `self.region` ↔ the STORED
    `self.args[1]` bijection (the value the gold returns equals the set operand;
    `==` because sympy may rebuild the operand into an equal object);
  * `Contains(x, s).args[0] is x` — the modelled `self.element` ↔ `self.args[0]`
    bijection (so the element operand is the distinct object the postcondition
    discriminates against);
  * after the gold change, `Contains(x, s).as_set() is Contains(x, s).args[1]`
    AND `Contains(x, s).as_set() == s` — the full round trip: the view returns
    the STORED set operand BY IDENTITY (the model's `Result() is self.region`),
    which equals the input set (the F2P equality).

It imports only `sympy` (the repo under test, in its own container) — no other
dependency. Exit 0 iff every observation holds. Provenance for the operand
storage: `sympy/core/basic.py` (`Basic.args` returns the stored constructor
operands) and `sympy/core/operations.py` / `sympy/logic/boolalg.py`
(`BooleanFunction`/`Application` construction preserves operand order); docs:
https://docs.sympy.org/latest/modules/core.html#sympy.core.basic.Basic.args .

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: the `# impl-start` /
`# impl-end` region of `model.py` (`return self.region`) is copied VERBATIM with
its contract calls stripped, together with the `Region` / `MembershipAssertion`
carriers it selects from. There are no `@Pure` helpers and no `@ContractOnly`
axioms to shim (both regions are empty, §2), so the whole impl region is
directly executable — this bundle is not a `conf_skip`.

* **Oracle**: the REAL gold-patched `Contains.as_set(self)`
  (`sympy/sets/contains.py:47`, §1), **called** — not transliterated. Two
  false-green guards: the loaded `as_set` source must contain
  `return self.args[1]` and must not contain `NotImplementedError` (exit 2
  otherwise), and no subclass may override `as_set` on any object under test.
* **Type bridge (§2 inverted)**: the real object is built first
  (`Contains(x, s)`), then its STORED operands are wrapped as
  `MembershipAssertion(c.args[0], c.args[1])`. Seeding the carrier from the
  constructor argument `s` would be unsound — sympy canonicalizes the region
  operand into an equal-but-distinct object (`Contains(x, FiniteSet(y)).args[1]
  is FiniteSet(y)` is False, `==` is True), which is exactly the `is` / `==`
  distinction §1 records.
* **Comparison**: object IDENTITY, matching `Ensures(Result() is self.region)`.
  Three further observations are pinned per input: `real is c.args[1]` (the
  stored operand, not a copy), `real == s` (the F2P equality), and `real is not
  c.args[0]` when the operands are distinct (the element is never returned).
* **Inputs**: 100 000 in-scope assertions — 258 boundary (the exact F2P triples;
  every region kind Reals/Integers/Naturals/Naturals0/Rationals/Complexes/
  EmptySet/UniversalSet/FiniteSet/Interval/Union/Intersection/Complement/
  ProductSet/ImageSet/ConditionSet/Range/SymmetricDifference; degenerate shapes:
  equal operands, a region as the element, a nested `Contains`, a non-`Set`
  region) then seeded fuzz. Both construction paths are exercised:
  `Contains(x, s)` (kept only when `Contains.eval` did not collapse the
  assertion to a Boolean/Set — that value comes from a different repo function)
  and `Contains(x, s, evaluate=False)`, which keeps decidable pairings such as
  `Contains(2, S.Integers)` in scope rather than discarding them.
* **Anti-vacuity control**: the `wrong-component-return-element` mutant
  (`return self.element`, the G-PBT rival) is run over the same boundary
  catalogue and must disagree at least once; if it agreed everywhere the
  differential would not be discriminating and the script exits 1.
* **Pinned seed**: `SEED = 23950`. Exit 0 iff zero disagreements.
