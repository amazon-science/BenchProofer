# refinement.md — operation correspondence (sympy__sympy-12489)

Maps every op in `implementation_mul` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The modeled representative is `Permutation.__mul__`
(`sympy/combinatorics/permutations.py:1244-1307 @ aa9780761a`). Its post-patch
tail is `return self._af_new(perm)`; pre-patch it was `return _af_new(perm)`.
The single logical change of the whole patch (object construction must produce an
object of the *receiver's* class, not always the base class) is observed here as:
`type(a * b) == type(a)` — the product carries the LEFT operand's class.

The arrangement object is modeled by `Arr { arr : List Int, fam : Nat }`:
`arr` ↔ `array_form` (the mapping), `fam` ↔ the runtime class/family
(`0` = base family, any other tag = a distinct derived family). See mapping.md.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let a := self.arr` | `a = self.array_form` | I | field read of the left operand's mapping |
| 2 | `let b := other.arr` | `b = other.array_form` | I | field read of the right operand's mapping (`__rmul__` guarantees `other` is an arrangement) |
| 3 | `if b ≠ [] then … else perm := a` | `if not b: perm = a` | I | empty-right-operand short circuit returns the left mapping unchanged |
| 4 | `let bc := completeTo b a.length` | `b.extend(list(range(len(b), len(a))))` | A-reference | identity-pad the shorter mapping up to `len(a)`; modeled deeply as `completeTo`, validated == the real padded-and-composed product by G-AX (axiom_check.py) |
| 5 | `perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length` | `perm = [b[i] for i in a] + b[len(a):]` | A-reference | the array-form composition (UNCHANGED by the patch); modeled deeply via `completeTo`/`composeArr`, validated == real `Permutation.__mul__().array_form` by G-AX |
| 6 | `return { arr := perm, fam := self.fam }` | `return self._af_new(perm)` | R | the CHANGED constructor. Pre-patch `_af_new(perm)` always built the base family; post-patch `self._af_new(perm)` threads the receiver's class. Refined to `fam := self.fam` (result's family = LEFT operand's family); `arr := perm` carries the unchanged mapping. The class↔`Nat` family bijection is the type refinement (mapping.md) |

Row 6 is the discriminating clause. The prepatch impl sets `fam := 0` (always the
base family — the actual bug: construction ignored the receiver's class), so its
`correct_mul` cannot close the `result.fam = self.fam` conjunct against the frozen
`problem_spec_mul` (confirmed: prepatch leaves goal `0 = self.fam`, unprovable).
That is the G-DIFF signal.

No A-consumed rows: the proof discharges `composeArr` and the family copy
directly by reflexivity/`simp`; no UNCHANGED-callee property is assumed. No
changed-inexpressible op — the class-threading fix is modeled exactly as a field
copy. The array composition (rows 4–5) is the only deep model and is G-AX
validated against the real product. G-CONF differential-tests the whole R/I
shadow (family + mapping) against the real post-patch `__mul__`.
