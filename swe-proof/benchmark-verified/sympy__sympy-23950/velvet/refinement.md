# refinement.md — sympy__sympy-23950

Correspondence between `Solution.lean`'s `asSet` impl and `patch.diff` (the gold
patch makes `Contains.as_set` return its second stored component instead of
declining). `patch.diff` is the gold verbatim (applies at base_commit, resolves
— G-RESOLVE).

## A. The corrected conversion — `Contains.as_set`

Gold hunk:
```
     def as_set(self):
-        raise NotImplementedError()
+        return self.args[1]
```

| # | Solution.lean impl op (`asSet`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `a : MembershipAssertion` (fields `elem`, `container`) | `self`, a `Contains(args[0], args[1])` instance | R | the assertion object ↔ a structure carrying its two args (mapping.md §2). Read-only, not `mut`. |
| A2 | `return Except.ok a.container` | `return self.args[1]` | I | identical: hand back the second stored component (the set the membership ranges over) unchanged, as a normal return. `Except.ok` ↔ a normal `return` (mapping.md §2). |

No A (axiom) steps — the body calls no callee. No kind-3 (changed inexpressible)
steps. The op is a direct projection of the assertion's stored component,
modeled deeply and tagged **R/I**.

## B. verify(Solution) ⇒ resolved

`asSet` verifies only if `out = Except.ok a.container` (A2). By R (mapping.md §2)
the verified result equals the patched `return self.args[1]` — the assertion's
collection component returned normally. The F2P test `test_as_set` asserts:

```
assert Contains(x, FiniteSet(y)).as_set() == FiniteSet(y)
assert Contains(x, S.Integers).as_set()   == S.Integers
assert Contains(x, S.Reals).as_set()      == S.Reals
```

i.e. for each membership assertion `Contains(x, S)`, `as_set()` returns exactly
`S` — which is `self.args[1]`, exactly what the spec pins. The postcondition is
grounded in the input carrier (it returns the assertion's own stored component,
directive 8), not an opaque oracle: the only way to satisfy it is to actually
return `a.container`.

The discriminating clause: the spec requires `Except.ok a.container`.

* The prepatch impl returns `Except.error .unavailable` (the pre-image declines
  to produce a set — the real base_commit `raise NotImplementedError()`),
  leaving the unsolved goal
  `Except.error ConversionErr.unavailable = Except.ok a.container`, which is
  unsatisfiable (`error ≠ ok`) — G-DIFF fails exactly on the
  declines-vs-returns-the-set distinction. This is the actual bug the issue
  reports (`as_set` not yielding a set, so downstream `as_relational` fails).
* A strictly weaker wrong impl — returning the *element* (`Except.ok a.elem`,
  i.e. `self.args[0]`) — would also fail the spec whenever `elem ≠ container`,
  because the postcondition pins `a.container`, not `a.elem`. So an impl that
  "returns some stored component" cannot verify unless it returns the right one.

## C. Trust surface

G-CONF differential-tests the R/I shadow (return `c.args[1]`) against the real
patched `Contains.as_set()` over a fuzzed pool of symbolic membership assertions
(≥5·10⁴ that stay symbolic), seed 23950, zero disagreements required. There are
**no axioms** (no `axiom_check.py`; G-AX skips) — the only trust point is the
type bijection in mapping.md §2, which G-CONF exercises directly.
