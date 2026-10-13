# mapping.md — sympy__sympy-14711

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c6753448b5c34f95e250105d76709fe4d349ca1f`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the two unchanged callees the modeled behaviour routes through.

Repo file under change: `sympy/physics/vector/vector.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `vectorAdd (self : VecVal) (other : Operand)` | `Vector.__add__(self, other)` (`sympy/physics/vector/vector.py:58-60`) | the one modeled changed behaviour: the vector add operator, taught to absorb the additive identity |
| `VecVal` | a `Vector` value (`Vector`, `vector.py:9`); the touched observation is its identity and how two vectors combine | opaque handle (mapping.md §2): the internal `self.args` representation is never inspected by the fixed behaviour |
| `Operand` (`zero` / `vec` / `foreign`) | the runtime type of the right operand `other`: the additive identity `0` (a SymPy `S.Zero`/`int`), a genuine `Vector`, or any other value | the three operand classes `__add__` distinguishes after the fix |
| `asVector (other)` *(deep model, axioms region)* | the UNCHANGED coercion `_check_vector(other)` (`vector.py:723-726`): `if not isinstance(other, Vector): raise TypeError('A Vector must be supplied'); return other` | pure spec of the unchanged coercion: a `Vector` passes through, anything else raises `TypeError` |
| `combine (self) (v)` *(opaque, axioms region)* | the UNCHANGED combined-vector construction `Vector(self.args + other.args)` (`vector.py:60`) | the unchanged binary combination of two vectors; only that it yields a vector matters (its components are orthogonal to the fix) |
| `AddErr.notAVector` | the `TypeError('A Vector must be supplied')` raised by `_check_vector` | the one distinguished failure outcome |
| `addSpec self other` *(pure region)* | the desired post-fix `__add__`: `if other == 0: return self` then `other = _check_vector(other); return Vector(self.args + other.args)` | the abstract behaviour the spec pins |

The gold patch's actual edit inserts a guard `if other == 0: return self` at the
TOP of `__add__`, before the `_check_vector(other)` coercion. In the model this
is the `if isZeroOperand other then Except.ok self else …` step at the top of
`vectorAdd`'s impl; the prepatch removes that guard (unconditional coercion) to
exhibit the pre-fix `TypeError`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Vector` value `self` | `VecVal` | opaque handle: only identity and the combination are observed. For G-CONF the handle indexes a fixed pool of distinct real `Vector`s built over a `ReferenceFrame` (`N.x`, `N.y`, `x*N.x + y*N.y`, …); `VecVal.handle = i ↔ pool[i]`. |
| the right operand `other` | `Operand` | `zero ↔ 0` (the Python `int`/`S.Zero` that `other == 0` matches); `vec i ↔ pool[i]` (a genuine `Vector`); `foreign ↔` a non-vector, non-zero value (e.g. `"x"`, `1`, `3.5`, a `Symbol`). |
| `_check_vector` returning the vector vs raising `TypeError` | `Except AddErr VecVal` | `Except.ok v ↔` the returned `Vector`; `Except.error .notAVector ↔` the raised `TypeError('A Vector must be supplied')`. |
| `Vector(self.args + other.args)` | `combine self v : VecVal` | the combined `Vector` ↔ the opaque result handle; G-CONF observes the combined vector via value equality `==` against the real `self + v`, never its internal args. |
| `other == 0` (the new guard's test) | `isZeroOperand other` | `True ↔ true` exactly when `other` is the additive identity; a `Vector` and a foreign value both test `False` (a `Vector` is `== 0` only when empty, which the genuine-`Vector` pool excludes — see §3.1). |

Operand classification is total and the input space is a small product
(`self ∈ pool × other ∈ {zero} ∪ {vec : pool} ∪ {foreign-samples}`), so G-CONF
enumerates the full cross product and then re-samples foreign/vector values to
exceed the §4.1 fuzz floor deterministically. No `require` clause is needed.

## 3. Callee provenance (kind-A)

Two UNCHANGED callees, both **A-reference** (deep model / opaque, validated
== the real callee by G-AX), no consumed `axiom` and no `:|` stub.

### 3.1 `asVector` ⇔ `_check_vector` (`vector.py:723-726`)
The coercion is unchanged by the gold patch. Modeled deeply as: a genuine
`Vector` → `Except.ok`; the additive identity and any foreign value →
`Except.error .notAVector`. G-AX runs the real `_check_vector` on boundary +
fuzz operands and asserts: it returns the same object for a `Vector`, and raises
`TypeError` for `0`, for other non-vector values, AND — critically for the
discriminator — for the additive identity `0`. This establishes that the pre-fix
path (`_check_vector(0)`) genuinely raised (the bug is real) and that the
genuine-`Vector` pool members are NOT `== 0` (so `vec`/`zero` are disjoint
classes; an empty `Vector` would alias both, hence excluded from the pool).

### 3.2 `combine` ⇔ `Vector(self.args + other.args)` (`vector.py:60`)
The combined-vector construction is unchanged. Modeled `opaque` with NO
`ensures` — the fix establishes nothing about WHICH vector results, only that
two vectors combine into a vector and that this leg is reached unchanged when
`other` is a genuine vector. G-AX asserts the real construction returns a
`Vector` (never raises) on two genuine vectors, so the `Except.ok (combine …)`
leg is inhabited and faithful.

`Vector.__add__` calls no other function; `__radd__ = __add__` (`vector.py:452`)
reuses the same body, so the modeled fix covers the `0 + vector` direction the
F2P `sum([...])` exercises (`sum` seeds the accumulator with `int 0` and folds
left, so the first add is `0.__add__(N.x)` → `NotImplemented` →
`N.x.__radd__(0)` → `__add__(N.x, 0)`).

## 4. G-CONF fuzz seed (pinned)

`SEED = 14711`, `N_FUZZ = 100000` (see `conformance_check.py`). Deterministic
verdict.
