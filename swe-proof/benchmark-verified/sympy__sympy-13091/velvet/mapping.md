# mapping.md — sympy__sympy-13091

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d1320814eda6549996190618a21eaf212cfd4d1e`, states the type
abstraction (the Lean↔Python bijection G-CONF uses), and gives the provenance of
each modeled callee.

Repo files under change (gold patch touches many files; the modeled, F2P-bearing
behaviour lives in `sympy/core/basic.py` and is mirrored verbatim in
`sympy/core/numbers.py`). The remaining diff sites are the SAME two edits applied
to other `__eq__`/`__ne__`/rich-comparison methods across the package — pure
repetitions of the modeled behaviour (see §4).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `directEquality (operand : Operand)` | the equality verdict computed inside `Basic.__eq__` — `sympy/core/basic.py:282`, specifically the value returned when `_sympify(other)` is rejected, `basic.py:316` | the value's OWN equality verdict for an operand (what `__eq__` returns: a decision or the delegation sentinel) |
| `equalityCompare (operand) (reflectedV)` | the `==` operator's resolution over `Basic.__eq__` and the operand's reflected `__eq__` (CPython rich-comparison dispatch; the unchanged language mechanism) | the equality OPERATOR's final boolean, honouring delegation on the sentinel |
| `inequalityCompare (operand) (reflectedV)` | `Basic.__ne__` — `sympy/core/basic.py:323`, body at `basic.py:332` (`return not self == other` post-patch; `return not self.__eq__(other)` pre-patch) | the inequality OPERATOR's final boolean |
| `Verdict` (inductive) | the three outcomes a Python comparison method can produce: `True`, `False`, and the `NotImplemented` singleton | the comparison outcome lattice |
| `Operand` (inductive) | the disjoint cases of `other` as `__eq__` reacts to it: rejected by `_sympify`; sympifies to an equal object; sympifies to a differing object | the only input distinctions the comparison reacts to |
| `eqResult`, `resolveEq`, `neResult` (pure) | the deep models of the verdict, of the `==` dispatch, and of `not (self == other)` | the modeled behaviour |

The modeled region of `Basic.__eq__` at base_commit (pre-image), `basic.py:308–321`:
```python
        if type(self) is not type(other):
            ...
            try:
                other = _sympify(other)
            except SympifyError:
                return False    # sympy != other     <-- the changed line (316)
            if type(self) != type(other):
                return False
        return self._hashable_content() == other._hashable_content()
```
and `Basic.__ne__` (pre-image), `basic.py:332`:
```python
        return not self.__eq__(other)              # <-- the changed line
```

The patch (post-image) replaces line 316 with `return NotImplemented` and line
332 with `return not self == other`. `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean domain
and the Python repo.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the value `other` as `__eq__` reacts to it | `Operand` (inductive) | an `other` for which `_sympify(other)` raises `SympifyError` (a value outside the sympy domain) ↔ `.foreign`; an `other` that sympifies to an object equal to `self` (same type, `_hashable_content` matches) ↔ `.matchingEqual`; an `other` that sympifies but is NOT equal (different type, or differing content) ↔ `.matchingUnequal`. These are the disjoint cases the F2P tests exercise. |
| a Python comparison outcome | `Verdict` (inductive) | the boolean `True` ↔ `.isTrue`; `False` ↔ `.isFalse`; the `NotImplemented` singleton ↔ `.undecided`. |
| the operand's OWN (reflected) equality outcome toward `self` | `Verdict` (`reflectedV`, a FREE INPUT) | the value `type(other).__eq__(other, self)` would produce. Not computed by the modeled function — it is the foreign object's own logic — so it is a universally-quantified input the spec makes NO assumption about. `True ↔ .isTrue`, `False ↔ .isFalse`, `NotImplemented ↔ .undecided`. |
| `==` operator result (`a == b`) | `Bool` from `resolveEq` | CPython evaluates `a.__eq__(b)`; if it is `NotImplemented`, it evaluates the reflected `b.__eq__(a)`; if that is also `NotImplemented`, it falls back to identity (`a is b`), which is `False` for distinct objects. `resolveEq selfV reflectedV` encodes exactly this dispatch; the final boolean ↔ the Python bool. |
| `!=` operator result via `__ne__` | `Bool` from `neResult` | post-patch `__ne__` is `not (self == other)` = `not resolveEq(...)`; `neResult = ! resolveEq` mirrors it. |

`NotImplemented` is a single CPython singleton; modeling it as the third `Verdict`
case is exact (it is neither truthy-as-decided nor falsy — it triggers delegation,
captured by `resolveEq`'s `.undecided` arm).

## 3. Callee provenance + flag dependencies

- **`_sympify(other)`** (`sympy/core/sympify.py`) — the conversion whose
  success/failure splits `.matchingEqual`/`.matchingUnequal` from `.foreign`. It
  is NOT axiomatized: the modeled behaviour does not depend on what `_sympify`
  *returns*, only on whether it raised, which is folded into the `Operand` case.
  No contract is owed; no G-AX entry.
- **the reflected comparison `type(other).__eq__(other, self)`** — a FREE INPUT
  (`reflectedV`). The whole point of the fix is that this belongs to a foreign
  object the modeled function knows nothing about; the spec quantifies over all
  three of its possible outcomes. No axiom, no A-reference.
- **the `==`/`!=` operator dispatch** — the unchanged CPython language mechanism,
  modeled deeply by `resolveEq` (a standard, documented protocol:
  https://docs.python.org/3/reference/datamodel.html#object.__eq__). Not a repo
  callee; modeled, not axiomatized.

No flag-dependent callees.

## 4. Why one model covers the multi-file gold patch

The gold patch edits ~30 sites across the package, but they are exactly **two
distinct edits** repeated:

1. `return False` → `return NotImplemented` in a `__eq__` body that has just
   failed to interpret its operand (`basic.py:316`, `numbers.py:1261/1722/3342`).
   This is modeled by `directEquality` / behaviour **A**.
2. `return not self.__eq__(other)` → `return not self == other` in a `__ne__`
   body (and the analogous `self.__lt__`→`self <`, `other.__le__(self)`→
   `other.__lt__(self)` operator-dispatch rewrites). This is modeled by
   `inequalityCompare` / behaviour **B**: route the negation through the operator
   so delegation is honoured before negating.

Every other diff site is one of these two edits applied to a different class's
comparison method (`Factors`, `Term`, `Float`, `Rational`, `NumberSymbol`,
`GeometryEntity`, `Medium`, polys classes, …). The F2P tests `test_equality`
(in `basic.py`'s `Basic`) and `test_comparisons_with_unknown_type` (in
`numbers.py`'s `Integer`/`Float`/`Rational`/`oo`/`nan`) observe exactly behaviours
A and B; both reduce to the same protocol modeled here. The `__gt__`/`__ge__`/
`__lt__`/`__le__` swaps in `numbers.py` (e.g. `other.__le__(self)`→
`other.__lt__(self)`) are observed only by `test_NumberSymbol_comparison`, which
is **neither F2P nor P2P** for this instance, so it is out of scope (not modeled);
the comparison operators are left raising `TypeError` on `.foreign` operands,
which the F2P `raises(TypeError, ...)` rows already require and the patch does not
change.

## 5. G-CONF fuzz seed

Pinned seed: **13091**. Differential space: the 3 `Operand` cases × 3 `reflectedV`
`Verdict` cases = 9 exhaustive combinations, plus ≥10⁵ seeded fuzz draws over the
same finite product (redundant coverage). See `conformance_check.py`.
