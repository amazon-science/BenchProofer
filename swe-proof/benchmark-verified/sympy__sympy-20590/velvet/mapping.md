# mapping.md — sympy__sympy-20590

Model symbol ↔ repo symbol binding (file:line at `base_commit`
`cffd4e0f86fefd4802349a9f9b19ed70934ea354`), the type abstraction, and the
provenance of the runtime rule the model spells out.

## 1. The change and the tested behaviour

The core value type `Basic` (`sympy/core/basic.py:28`,
`class Basic(Printable, metaclass=ManagedProperties)`) declares a closed
instance slot set (`sympy/core/basic.py:72`, `__slots__ = ('_mhash', '_args',
'_assumptions')`). Its leaf subtypes also declare closed slot sets (e.g.
`Symbol.__slots__ = ('name',)`, `sympy/core/symbol.py:203`; `Atom.__slots__ =
()`, `sympy/core/basic.py:1825`).

The shared printing-behavior contributor `Printable`
(`sympy/core/_print_helpers.py:8`, `class Printable:`) did **not** declare a
closed slot set. Under the host runtime's object model, if ANY type in an
instance's resolution order (other than the universal root) omits a closed slot
declaration, that type contributes an open per-instance namespace, and every
subclass instance therefore carries that namespace regardless of the subclasses'
own slot declarations. So `Basic()` instances acquired an open namespace and
accepted arbitrary attribute binding, losing the intended immutability.

The gold patch (`patch.diff`, the diff verbatim) adds to `Printable`
(`sympy/core/_print_helpers.py`, in the class body after the docstring):

```python
    __slots__ = ()
```

With every type in `Basic`'s resolution order now declaring a closed slot set
(and none listing an open-namespace marker), `Basic` instances carry no open
namespace.

The F2P test `test_immutable` (`sympy/core/tests/test_basic.py`, added by the
test_patch) asserts on `b1 = Basic()`:

```python
assert not hasattr(b1, '__dict__')
with raises(AttributeError):
    b1.x = 1
```

## 2. Type abstraction (the refinement carrier)

| repo reality | model (`Solution.lean`) |
|---|---|
| a type's resolution order (excluding the universal root) | `chain : List Bool`, one flag per type |
| a type declares a closed slot set (fixed instance layout, no own open namespace) | the corresponding flag is `true` |
| a type omits a closed slot declaration (contributes an open per-instance namespace) | the corresponding flag is `false` |
| the value type's chain WITHOUT the shared printing contributor (`Basic` and any slotted bases, most-derived first) | the method input `others : List Bool` (universally quantified — the spec pins behaviour for EVERY layout of the other contributors, not just the actual one) |
| `Basic`'s own slot declaration at `base_commit` (closed) | the instantiation `allClosedLayout others = true` (the actual repo shape; pinned by the second `ensures` clause of each `core*` method) |
| `Printable`'s slot declaration | `mixinPinsClosedLayout` / the `trait` flag — `true` (gold) / `false` (prepatch); appended as the chain's last entry (`others ++ [trait]`) |
| instance carries an open namespace | `instanceAdmitsNamespace chain = !allClosedLayout chain` |
| `hasattr(inst, '__dict__')` | `instanceAdmitsNamespace chain` |
| `inst.x = 1` (x undeclared) succeeds (absorbed into the open namespace) | `bindUndeclared chain = Except.ok true` |
| `inst.x = 1` (x undeclared) raises `AttributeError` | `bindUndeclared chain = Except.error AttrError.bindingRefused` |

`AttrError.bindingRefused` (a one-constructor inductive) stands in for the
runtime's attribute error on a refused binding.

**On the chain shape (quantified `others`).** The real resolution order of
`Basic`, the universal root excluded, has exactly **two** entries:
`[Basic, Printable]` (`Basic` itself, then its only base `Printable`). The
model's chain is `others ++ [trait]` where `others` is the flags of the
non-`Printable` contributors — for the real repo shape, `others = [true]`
(`Basic`'s own closed slot set), and any longer all-`true` `others` is inert
under the conjunction. Crucially `others` is a **universally quantified method
input**, not a hardcoded literal: each `core*` method's primary `ensures`
clause pins the output to the model function applied to `others ++ [true]` for
EVERY `others`, so an implementation cannot satisfy the spec by returning a
constant — it must compute the runtime rule over the full chain. The second
`ensures` clause instantiates the actual repo shape (`allClosedLayout others =
true`, since `Basic` and its slotted bases are closed at `base_commit`) to pin
the concrete F2P observations. The flag the patch changes is `trait` (= the
printing contributor's slot declaration), fixed `true` in the appended entry by
the desired behavior.

## 3. Provenance of the modelled rule (the deep model, not a callee axiom)

The rule `instance has an open namespace ⟺ some contributing type (≠ root) omits
a closed slot declaration` is a **host-runtime object-model fact**, not a sympy
callee. It is therefore modelled **deeply** (`allClosedLayout` is the
front-recursive conjunction over the chain; `bindUndeclared` derives the
attribute-binding decision from it), not axiomatized. There is no `:|`-stub
callee and no consumed axiom.

Provenance of the rule (the host runtime's data model): an instance lacking an
open per-instance namespace cannot bind a name outside its declared slot set, and
binding such a name raises an attribute error; a closed slot declaration in a
parent does not by itself close a child's layout — the child re-opens it unless it
too declares a closed slot set. So a shared contributor without a closed slot
declaration re-opens the layout of every subclass that mixes it in.

`axiom_check.py` validates this modelled rule **against the real interpreter**
(A-reference): it constructs type chains with every combination of closed-slot /
open-layout layers, builds an instance, and asserts that `hasattr(inst,
'__dict__')` and the attribute-error-on-binding behaviour match the model's
`allClosedLayout` / `instanceAdmitsNamespace` / `bindUndeclared` rule on the
corresponding boolean chain — boundary (empty chain, single layer, the gold and
prepatch shapes) plus fuzz (random multi-layer chains). It uses only the stdlib
and exits 0 iff the modelled rule matches the interpreter on every observation.
`conformance_check.py` (G-CONF) differential-tests the same R/I shadow against
the interpreter on a pinned seed.

## 4. Determinism

Both `axiom_check.py` (G-AX) and `conformance_check.py` (G-CONF) pin the fuzz
seed to `20590` for a deterministic verdict.
