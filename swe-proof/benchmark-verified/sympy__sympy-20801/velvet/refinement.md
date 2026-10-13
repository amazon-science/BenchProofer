# refinement.md — sympy__sympy-20801

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`equalsOperand` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**. This bundle has **no axioms** and **no
deep-model references** (§C), so there is no A leg and `axiom_check.py` is a
no-op stub.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The site — `Float.__eq__` (`sympy/core/numbers.py:1383`)

Gold hunk (relocation of the zero short-circuit):
```
@@ -1386,8 +1386,6 @@ def __eq__(self, other):
         except SympifyError:
             return NotImplemented
-        if not self:
-            return not other
         if isinstance(other, Boolean):
             return False
         ...
@@ -1408,6 +1406,8 @@ def __eq__(self, other):
             ompf = other._as_mpf_val(self._prec)
             return bool(mlib.mpf_eq(self._mpf_, ompf))
+        if not self:
+            return not other
         return False    # Float != non-Number
```
The patch **moves** `if not self: return not other` from the head of the
dispatch (before the `isinstance(other, Boolean)` test) to the tail (after every
numeric branch, just before the final `return False`). No new behavior is added;
the shortcut's *position* in the ladder changes.

| # | Solution.lean impl op (`equalsOperand`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `selfVal : Int` | `self : Float` (its exact value; `0` ⇔ the zero float) | R | mapping.md §2. The method reads of `self` only `bool(self)` (`self._mpf_ != fzero`, line 1285 ⇒ `selfVal = 0`) and `self._mpf_` for the exact comparison; `Int` is a faithful exact proxy (the comparison is exact, line 1398). |
| A2 | parameter `o : Operand` (`logical`/`numeric`/`symbolic`) | the sympified `other` dispatched by `isinstance(other, Boolean)` / `is_NumberSymbol` / `is_Float` / `is_Rational` / `is_Number` / else | R | mapping.md §2: the ladder partitions every operand into exactly these three kinds; G-CONF bridges each Python operand to its ctor by the same predicates. |
| A3 | `match o`: `.logical _ => false` | `if isinstance(other, Boolean): return False` (now reached BEFORE the zero shortcut) | R/I | the post-patch ladder settles a logical constant to `False` unconditionally — the zero value no longer pre-empts it. `false` is `floatEq selfVal (.logical _)` for every `selfVal`. This is the discriminating clause. |
| A4 | `match o`: `.numeric m => decide (selfVal = m)` | the numeric branches `self._mpf_ == other._mpf_` / `mlib.mpf_eq(self._mpf_, ompf)` (lines 1397–1410) | R/I | exact value equality, modeled as `Int` equality (mapping.md §2,§3). Unchanged by the patch; the zero value is decided here too (`selfVal = 0 ↔ self == other == 0`), matching the relocated shortcut on numeric operands. |
| A5 | `match o`: `.symbolic t => if selfVal = 0 then !t else false` | the tail: relocated `if not self: return not other` then `return False` | R/I | for a non-`Boolean`, non-`Number` operand the post-patch flow falls to the tail; a zero value returns `not other` (= `!t`), a nonzero value returns `False`. Exactly `floatEq` on `.symbolic`. |

### Discriminating content
The change is observable **only** when a zero value meets a `logical` operand
(A3). Pre-patch the head shortcut fires first: `not other` — for `S.false`
(`t = false`) this is `True` (the reported defect). Post-patch the `Boolean`
branch fires first: `False`. `Solution_prepatch.lean` reproduces the head-first
order and **fails** `out = floatEq selfVal o` at exactly `selfVal = 0,
o = .logical false` (G-DIFF: unsolved goal `(!b) = false` for the logical ctor).

For `numeric` and `symbolic` operands the relocation is **behavior-preserving**:
a zero value vs a number is still decided by exact equality (the relocated
shortcut would have agreed: `not (other != 0)` = `other == 0` = `0 == other`),
and a zero value vs a generic symbolic falls to the relocated `not other` either
way. Hence the only F2P-observable change is the Boolean case, and the
F2P test `test_zero_not_false`'s `Float` assertion is precisely `S(0.0) == S.false
is False`.

## B. No axioms / no deep-model references
Every numeric/Boolean comparison the method performs is **grounded** as exact
`Int` equality or a constructor match on `Operand`. No callee is axiomatized and
none is deeply modeled-and-validated. `meta.json` lists empty `axioms` and
`deep_model_references`; `axiom_check.py` is a no-op stub that exits 0 (nothing
to validate against a real callee — there is no A leg).

## C. No kind-3 (inexpressible-changed-op) steps
Every step is R or R/I. The operation that *changed* — the **position** of the
zero short-circuit in the dispatch ladder — is expressed directly as the
`match`-order of `equalsOperand` (logical settled before the zero value is
consulted). Nothing is hidden behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved
`equalsOperand` verifies only if its output equals `floatEq selfVal o` for every
operand kind — in particular `false` for a `logical` operand regardless of
`selfVal` (A3). By R (`Float` value ↔ `Int`, operand ↔ `Operand`) the verified
function equals the post-patch `Float.__eq__` on the modeled domain; by G-CONF
the R/I transliteration agrees with `patch.diff`'s behavior on ≥10⁵ fuzzed
real-SymPy operands; the gold patch resolves (G-RESOLVE). The single trust point
is refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness
trust point because there are no axioms.
