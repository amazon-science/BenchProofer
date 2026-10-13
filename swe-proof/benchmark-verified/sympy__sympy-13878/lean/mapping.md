# mapping.md — sympy__sympy-13878

## Scope

The gold patch adds precomputed `_cdf` methods to many continuous
distributions in `sympy/stats/crv_types.py`. Only ONE behavior is scored by the
harness: `FAIL_TO_PASS = ["test_arcsin"]`. That test asserts the cumulative
distribution function of the arcsin distribution equals its precomputed
closed form, as a whole symbolic object, on FREE symbolic operands. Every other
`_cdf` added by the patch is exercised only by `test_long_precomputed_cdf` /
`test_precomputed_cdf`, which are NOT in FAIL_TO_PASS (and not in PASS_TO_PASS
either — they are out of the scored set). So the modeled function is the arcsin
distribution's `_cdf`.

## §1 Symbol binding (file:line @ base_commit 7b127bdf71, patch APPLIED)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_arcsinCdf` | `ArcsinDistribution._cdf` (added by patch) | `sympy/stats/crv_types.py:157` (method body 157–163; insertion after `pdf`, patch.diff hunk `@@ -153,6 +154,15 @@`) |
| `arcsinProfile a b x` | `2*asin(sqrt((x - a)/(b - a)))/pi`, the case-1 value | `crv_types.py:162` |
| `a`, `b` | `self.a`, `self.b` (`ArcsinDistribution._argnames = ('a','b')`) | `crv_types.py:151` |
| `x` | the `_cdf` evaluation point | method argument, `crv_types.py:157` |
| `Term.lt` / `Term.le` / `Term.always` | the guards `x < a` / `x <= b` / `True` as SUBMITTED by the method | `crv_types.py:160`–`162` |
| `CdfObject.caseSplit cs` | `Piecewise(*cs)` — the algebra layer's case-split constructor applied to the submitted list | `sympy/functions/elementary/piecewise.py:145` (`Piecewise.eval`) |
| `CdfObject.accumulateUpTo` | the integrate-the-density fallback, `ContinuousDistribution.compute_cdf` | `sympy/stats/crv.py:196`–`209` (reached from `crv.py:211`–`220` when `_cdf` returns `None`) |

### The callee's STEPS, and the leg of the model that carries each

The patched method is three lines, but its contract is a COMPOSITION and the
second half is code the patch does not touch. Enumerated:

1. **bind the operands** — `a, b = self.a, self.b` (`crv_types.py:159`). No
   sympification: the operands are whatever the distribution was constructed
   with, free symbols or ground numbers alike. Modeled by the `Term` signature
   offering BOTH a free-operand builder (`Term.sym`) and the ground builders, and
   by the modeled routine treating an operand it is handed the same way whichever
   it is — which is what the real method does, since it only passes them on.
2. **build the ordered case list** — three `(value, guard)` pairs in a fixed
   order, with a STRICT lower cutoff `x < a`, a NON-STRICT upper cutoff
   `x <= b`, and a `True` fall-through (`crv_types.py:160`–`163`). Modeled by
   `implementation_arcsinCdf`'s `cs`, position by position; this is what
   `problem_spec_arcsinCdf` pins.
3. **submit it to `Piecewise`** — `Piecewise.eval`
   (`piecewise.py:145`–`299`) then applies a SECOND, whole-container pass over
   the list it was handed, which can overwrite what step 2 produced. Reading it
   at base_commit, it: canonicalises each relational (`_canonical`, line 202 —
   this is why the method's source spells `x < a` while the stored guard prints
   `a > x`); drops any case whose guard evaluates to a literal `False` (line
   204ff via the `current_cond` bookkeeping); ignores a repeat of an earlier
   condition (lines 236–249); drops everything after the first case whose guard
   is literally `True`; and — the early return at lines 163–164 — returns the
   bare EXPRESSION, not a `Piecewise` at all, when one case with a `True` guard
   is all that survives. Modeled by `CdfObject.caseSplit` being an ABSTRACT
   denotation of "the case-split object assembled from this list" rather than a
   claim about which of those shapes is observed; §2 below carries the
   composition and `conformance_check.py` holds it to account.

Step 3 is deliberately outside the model. It is unchanged code, it is not the
behavior under spec, and it is a whole-container pass whose effect depends only
on whether the operands settle the guards — never on which values or cutoffs
step 2 chose. Pinning step 2 exactly, and abstracting step 3 to a constructor
the real one honors, is what makes the postcondition state what the callee
GUARANTEES.

## §2 Lean ↔ Python correspondence (used by G-CONF / G-AX)

The carrier is SYNTACTIC, not numeric: the scored assertion compares whole
expression trees, so the answer's shape — case count, case order, cutoff
strictness, and the term structure of each value — is part of the answer.

The Lean side does not commit to one datatype of trees, either. `Term T` is the
SIGNATURE of the builders — one operation per row of the table below, over a
carrier `T` the frozen file leaves ARBITRARY — and the answer type, the
on-support value, the postcondition and the obligation are all stated under
`{T : Type} [Term T]`. So each row reads "this Python operation IS that signature
operation", and the correspondence is between two ALGEBRAS over one signature:
sympy's expression layer is one carrier of it, a Lean datatype of syntax trees is
another, and the modeled behavior is what it does in every one of them. The
reason is in §2.1: the sympy layer identifies terms a datatype of trees keeps
apart, and the modeled behavior must not be allowed to turn on the difference.

| Python | Lean | note |
|---|---|---|
| a free `Symbol` operand | `Term.sym name` | settles no order comparison, so no guard decides |
| `Integer(n)` | `Term.lit n` | a ground operand; ground operands DO settle guards |
| `pi` | `Term.pi` | |
| `p/q`, `p*q`, `p-q` | `Term.div/mul/sub` | |
| `asin e`, `sqrt e` | `Term.arcsin/sqrt` | the symbolic functions, NOT Mathlib's total real ones |
| `x < a` (`StrictLessThan`) | `Term.lt x a` | strictness is observable and is compared |
| `x <= b` (`LessThan`) | `Term.le x b` | |
| `True` (`BooleanTrue`) | `Term.always` | |
| `[(v0,g0),(v1,g1),(v2,g2)]` as submitted | `cs : List (Case T)`, ordered | what the postcondition pins |
| `Piecewise(*cs)` | `CdfObject.caseSplit cs` | **the bridge is this composition** |
| the unevaluated integrate-the-density object | `CdfObject.accumulateUpTo x` | representable so that returning it is rejected |
| a single unguarded expression | `CdfObject.bare e` | representable so that returning it is rejected |

So the equation `conformance_check.py` checks is

    ArcsinDistribution(a, b)._cdf(x)  ==  Piecewise(*shadow_cases(a, b, x))

structurally (sympy `==`), on operands of BOTH kinds. Measured in the instance
image at base_commit + patch: on free operands the real method returns a
three-case `Piecewise` whose `.args` are exactly the submitted triple modulo
`_canonical`'s flip; on `a=0, b=Symbol('b'), x=1` two cases survive; on
`a=Symbol('a'), b=1, x=2` a different two survive; on all-ground `a=0, b=1,
x=0` a bare `0` comes back; on `a=b` a bare `nan`; and where the real method
raises `TypeError('Invalid comparison of complex …')` the composition raises
identically. The Lean model is NOT wrong on any of these — it denotes the
submitted list, which is invariant across all of them.

### §2.1 What has NO image under this correspondence

Every row above maps a Python operation to a signature operation, and the
correspondence extends to a Lean TERM only when that term is built by those
operations out of the operands the behavior receives — `a`, `b`, `x`, the
constants, and what is assembled from them. Two things therefore have no image at
all, and it matters because a Lean implementation that reaches for either is not
transliterable ROW BY ROW; the rule for each is stated here so that the reading
is fixed in advance rather than chosen after the fact.

**(a) A QUESTION about elements of the modeled algebra.** The signature offers
builders, no eliminator, and no laws, so `p = q` is not something the
correspondence can carry: the two algebras answer it differently, and by
construction. Sympy's layer evaluates as it builds, so `Integer(2)/Integer(2)` IS
`Integer(1)`, `x*2` and `2*x` are one term stored in that layer's own argument
order, and `x - 0` is `x`; a Lean datatype of syntax trees says each of those
pairs differs. Both are carriers of the signature — as are the free algebra,
which settles no identity, and the one-element algebra, which settles every
identity affirmatively. A behavior whose answer turned on such a question would
therefore not be a behavior OF the sympy layer, and it would have no faithful
Python reading: `Term.div (Term.lit 2) (Term.lit 2) = Term.lit 1` transliterates
to a comparison that is TRUE in sympy while a tree datatype makes it FALSE, so
the Lean branch taken and the Python branch taken come apart. This is why the
frozen file states everything at an arbitrary carrier: over an arbitrary carrier
the question cannot be asked, so an implementation can only ASSEMBLE the operands
it is given, and assembly is exactly what these rows carry.

**(b) A carrier an implementation introduces FOR ITSELF.** Nothing stops a Lean
implementation from declaring its own type, giving that type the signature, and
then deciding something about an element of it. Such an element is not `self.a`,
`self.b`, `x`, or anything built from them — it is not an object the Python method
holds at all — so no row applies and the correspondence gives its comparison no
Python image. The faithful reading of such a guard is therefore the BRANCH IT
SELECTS, not the syntax of the comparison: a private type has no Python
counterpart, so the only thing a transliteration can preserve is which branch
runs. That reading is forced rather than convenient, and it is safe in the
direction that matters: a guard whose operands are private to the implementation
does not mention `a`, `b` or `x`, so it selects the same branch at every operand
triple and at every carrier — and the frozen obligation, which is proved for
every carrier and every triple, holds of whatever that branch returns. So the
Python method the rule produces is one that yields the required case analysis, and
"verifies in Lean" still carries "resolves in Python". The rule cannot be read the
other way round: a comparison whose operands ARE built by the rows above is
covered by (a), where the transliteration is forced by the rows and the two
algebras' disagreement is the whole point.

An earlier revision of this file described an `a b x : ℝ` model over Mathlib
`Real.arcsin`/`Real.sqrt`. That is not what the bundle ships and it could not
carry this behavior: Mathlib's versions are total with clamped values off
domain, which makes the case-1 value already `0` below the support and already
`1` above it, so the three cases collapse into one function of a real `x` and
the case count, order and cutoff strictness become unobservable. A carrier of the
signature above is what keeps them observable: the reals are not one, because
`Term.lt` and `Term.le` would have to land in the same type as the values and
would stop being distinguishable elements.

## §3 Callee provenance + flag deps

No unchanged callee is CONSUMED as an axiom: every term-builder is modeled
deeply as an operation of the signature, so there is no `opaque` declaration and
no `_prop` axiom, and G-AX has nothing to validate (it emits `skip`). The
signature itself asserts nothing — it has operations and no laws — so it is not
an assumption about the callees either. The one
operation left outside the model is step 3's case-split constructor, carried by
§2's composition and checked by G-CONF rather than asserted in Lean. The gold
patch's `S.Zero`/`S.One` are the sympy constants 0/1 (no flag dependence).

## §4 G-CONF fuzz seed

Pinned seed: **13878**. Inputs fuzzed: `(a, b, x)` triples drawn from a pool
holding FREE symbols (assumption-carrying and bare) and GROUND terms (integers,
negatives, rationals, `pi`, radicals, nested inverse sines), plus a
deterministic head that hits each operand-kind combination on purpose:
all-free, one/two ground, all ground, aliasing (`x` IS `a`, `x` IS `b`), the
degenerate `a = b`, and reversed `b < a`. The run asserts it saw all three
observable shapes — the surviving three-case analysis, a pruned analysis, and a
bare collapse — so a run that silently tested only one is a failure.
