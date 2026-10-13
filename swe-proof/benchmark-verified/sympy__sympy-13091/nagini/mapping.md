# mapping.md — sympy__sympy-13091

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d1320814eda6549996190618a21eaf212cfd4d1e`, states the type
abstraction, and gives the provenance of the one deep-model reference.

The gold patch touches ~30 sites across many files, but they are instances of
exactly **two** behavioural deltas (the F2P tests target these two). The model
captures the two deltas as two contracted functions; the dozens of identical
call-sites are the same delta replicated and are not independently modeled
(the refinement is one-to-many, see refinement.md §C).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `sym_eq(sympifiable, content_equal)` | the `__eq__` methods that on a failed coercion did `return False` and now `return NotImplemented`: `Basic.__eq__` (`sympy/core/basic.py:316`), `Float.__eq__` (`sympy/core/numbers.py:1261`), `Rational.__eq__` (`sympy/core/numbers.py:1722`), `NumberSymbol.__eq__` (`sympy/core/numbers.py:3342`) | modeled changed function #1: three-valued equality reply |
| `sym_ne(sympifiable, content_equal, other_answer)` | the `__ne__` methods that changed from `return not self.__eq__(other)` to `return not self == other`: e.g. `Basic.__ne__` (`sympy/core/basic.py:332`), `Float.__ne__` (`sympy/core/numbers.py:1278`), and ~25 other `__ne__`/`eq`/operator sites across `sympy/core/{basic,numbers,exprtools}.py`, `sympy/geometry/entity.py`, `sympy/physics/...`, `sympy/polys/...`, `sympy/tensor/...`, `sympy/utilities/enumerative.py` | modeled changed function #2: inequality as the complement of the resolved operator |
| `op_eq(self_answer, other_answer)` *(deep model — A-reference)* | the CPython `==` rich-comparison operator dispatch (the data-model protocol `object.__eq__` participates in) — `Objects/object.c` `do_richcompare` / language reference §3.3.1 | pure spec: the fully-resolved `==` operator, validated `op_eq == real ==` by axiom_check.py (G-AX), NOT a consumed axiom |
| `eq_code(sympifiable, content_equal)` | the pure (side-effect-free) form of the equality reply used inside contracts | pure spec mirror of `sym_eq` |
| `EQ_FALSE/EQ_TRUE/EQ_NI` | the three rich-comparison replies `False` / `True` / `NotImplemented` | pure spec: the three protocol codes |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the right-hand object `other` of a comparison | two booleans: `sympifiable` (can `_sympify(other)` succeed — i.e. `other` is a comparable peer rather than a foreign object) and `content_equal` (when `sympifiable`, whether the coerced content equals `self`) | `other` is observed only through these two predicates; every concrete `other` falls in one of three classes the model enumerates: foreign (`not sympifiable`), equal peer (`sympifiable and content_equal`), unequal peer (`sympifiable and not content_equal`) |
| the rich-comparison reply `True`/`False`/`NotImplemented` (a Python object that is `bool` or the `NotImplemented` singleton) | `int` code `EQ_TRUE=1` / `EQ_FALSE=0` / `EQ_NI=2` | a definite `bool` ↔ `{EQ_TRUE, EQ_FALSE}`; the `NotImplemented` singleton ↔ `EQ_NI`. `bool(reply)` for a definite reply ↔ `code == EQ_TRUE` |
| the right-hand object's OWN equality reply `other.__eq__(self)` (what the reflected method yields) | the `int` parameter `other_answer` (same three-valued code) | the reflected method's reply, consulted by `==` on the delegation sentinel |
| the `==` operator `self == other` | `op_eq(self_answer, other_answer)` → `bool` | CPython dispatch: left reply if decided, else right reply if decided, else identity-fallback `False` |
| the `!=` operator / `__ne__` result | `sym_ne(...)` → `bool` | `not (self == other)` |

`__ne__`/`__eq__` take `self` implicitly; the model exposes only the observable
inputs (`sympifiable`, `content_equal`, and the reflected `other_answer`).

## 3. Deep-model reference provenance (A-reference — checked by G-AX)

### 3.1 `op_eq` deep model ↔ CPython `==` dispatch (A-reference)
**Callee:** the Python `==` (and `!=`) rich-comparison operator. It is NOT a
repo function the patch changes; it is the language-level dispatch the gold
patch *relies on* by switching `__eq__` to return `NotImplemented` and `__ne__`
to use the operator `self == other`. CPython semantics (language reference,
"Basic customization", and `do_richcompare`):

* `a == b` calls `type(a).__eq__(a, b)`; if that returns `NotImplemented`, it
  calls the reflected `type(b).__eq__(b, a)`; if that is also `NotImplemented`,
  it falls back to identity (`a is b`) — distinct objects compare unequal.
* `a != b` is `not (a == b)` when `__ne__` is defined as `not self == other`
  (the gold form); the operator-level negation resolves the sentinel first.

`op_eq(self_answer, other_answer)` encodes exactly this: decided-left, else
decided-right, else `False`. The model is validated **== the real operator** by
`axiom_check.py` (G-AX), which builds real Python objects whose `__eq__`
returns each of `True`/`False`/`NotImplemented` and asserts `op_eq` predicts
`left == right` and `sym_ne` predicts `left != right` over all 3×3 reply
combinations, plus the symmetry and identity-fallback witnesses the fix
establishes. No flag dependency (this is pure language semantics).

There is **no `@ContractOnly` axiom** the proof consumes — `op_eq` is spelled
out in the `pure` region and the proof reasons through it directly; G-AX only
validates that the spelled-out operator equals the real one.
