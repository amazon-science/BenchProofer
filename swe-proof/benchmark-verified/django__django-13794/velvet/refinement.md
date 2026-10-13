# refinement.md — django__django-13794

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the four `deferred*` `do` blocks) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; state the bijection), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (deep model validated == real callee
by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (here empty) A legs and this narrative are audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (byte-identical; G-RESOLVE).

## A. The change

Gold hunk (`django/utils/functional.py`, inside the lazy `__proxy__` class):
```
+        def __add__(self, other):
+            return self.__cast() + other
+
+        def __radd__(self, other):
+            return other + self.__cast()
```
Two binary-add handlers are added to the deferred-value proxy: a left-operand
handler `__add__` (force self, then `forced + other`) and a right-operand
handler `__radd__` (force self, then `other + forced`). Pre-patch the proxy had
only the *auto-generated* left-operand wrapper (built by `__prepare_class__`,
`functional.py:108`), which evaluated `self.__cast().__add__(other)` eagerly and
**raised** when `other` was itself a deferred value (rather than returning the
not-implemented sentinel and letting the other operand's right-handler run); and
it had **no** right-operand handler at all. The `add` template filter
(`django/template/defaultfilters.py:675`) turns any raise from `value + arg`
into the empty string — the observed bug.

The change is **type-generic** (it works for any underlying result class). The
F2P tests exercise two result classes — character sequences (`add08`, `add09`)
and integers (`test_lazy_add`) — so the spec models both, in both operand
positions, via four methods.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `deferredConcatLeft`: input `forced : List Char` | `self.__cast()` (force, str result class) — `functional.py:152` | R | the unchanged forcing step yields the underlying `str`; modeled as the input already holding it. `str ↔ List Char` (mapping.md §2). |
| A2 | `deferredConcatLeft`: `return Except.ok (forced ++ other)` | `__add__`: `return self.__cast() + other` | R + I | `str` concat `+` ↔ `List` `++` (R, mapping.md §2); operand order `forced` then `other` is identical (I). Success (`.ok`) ↔ the operator returns normally. |
| A3 | `deferredConcatRight`: `return Except.ok (other ++ forced)` | `__radd__`: `return other + self.__cast()` | R + I | `str` concat with the OTHER operand on the left ↔ `other ++ forced` (R + I). Success ↔ returns normally. This is the handler that did not exist pre-patch. |
| A4 | `deferredSumLeft`: input `forced : Int`; `return Except.ok (forced + other)` | `__add__` at `int` result class: `self.__cast() + other` | R + I | Python `int` ↔ Lean `Int`; `int` `+` ↔ `Int` `+` (R, mapping.md §2); same operand order (I). |
| A5 | `deferredSumRight`: `return Except.ok (other + forced)` | `__radd__` at `int` result class: `other + self.__cast()` | R + I | as A4 with the other operand on the left. For `Int`, `+` commutes, so A4 and A5 yield equal values; they remain distinct methods to mirror the two distinct Python handlers and operand positions. |

No A (axiom) steps; no A-reference steps; no kind-3 (changed-inexpressible)
steps. The only callee is the unchanged forcing step `self.__cast()`, modeled as
the identity onto `forced` (A1/A4, an R-refinement) — per SPEC_GUIDE §3 a
deeply-modeled change is not a consumed axiom, and ordinary `++`/`+` need no
A-reference.

## B. The discriminating content (G-DIFF)

Three independently-observable fixed behaviours, each with its own failing
prepatch (the spec stays byte-identical across all three; G-DIFF):

* **`Solution_prepatch.lean`** — `deferredConcatRight` returns
  `Except.error .unsupported`: the pre-patch **absence of a right-operand
  handler**. Fails `out = Except.ok (other ++ forced)`. This is the behaviour
  F2P `add08` (`{{ s1|add:lazy_s2 }}`, a plain string on the left, a deferred
  string on the right) observes: pre-patch the filter returns `''`.
* **`Solution_prepatch_2.lean`** — `deferredConcatLeft` returns
  `Except.error .unsupported`: the pre-patch left handler **raised on a deferred
  right operand** (it combined eagerly instead of deferring). Fails
  `out = Except.ok (forced ++ other)`. This is the behaviour F2P `add09`
  (`{{ lazy_s1|add:lazy_s2 }}`, deferred on both sides) observes.
* **`Solution_prepatch_3.lean`** — `deferredSumRight` returns
  `Except.error .unsupported`: pre-patch combining two deferred **integers**
  raised (neither operand position absorbed the other). Fails
  `out = Except.ok (other + forced)`. This is the behaviour F2P
  `test_lazy_add` (`lazy_4() + lazy_5()`) observes.

## C. verify(Solution) ⇒ resolved

`deferredConcatLeft`/`deferredConcatRight` verify only if they return success
carrying, respectively, `forced ++ other` and `other ++ forced`; the `Sum`
methods only if they return success carrying the numeric sum. By R
(`str ↔ List Char`, `int ↔ Int`, forcing = identity onto `forced`) these are
exactly the values the patched `__add__`/`__radd__` return on the tested inputs,
and `.ok` ↔ "no raise". G-CONF differential-tests the four R/I legs against a
real patched lazy proxy over ≥10⁵ fuzzed inputs in both operand positions and
both result classes. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axioms, so the only trust point is refinement fidelity
(this doc + G-CONF); G-AX is `skip`.

**Termination semantics.** The spec is verified under
`loom.semantics.termination "total"` (`TotalCorrectness`). The real patched
handlers (`__add__`/`__radd__`) are straight-line returns that always
terminate, and each F2P test observes a *produced value*
(`'stringlazy'`, `9`) — a diverging handler would hang the test run, not pass
it. Under partial correctness a non-terminating impl (e.g. an unbounded loop
before the return) would vacuously satisfy the `ensures` clauses despite
being observably wrong; total correctness closes that admission, so verifying
impls must actually terminate and return the specified value.
