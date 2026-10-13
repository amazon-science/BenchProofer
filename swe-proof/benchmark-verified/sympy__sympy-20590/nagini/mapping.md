# mapping.md — sympy__sympy-20590

Model symbol ↔ repo symbol binding (file:line at `base_commit`
`cffd4e0f86fefd4802349a9f9b19ed70934ea354`), the type abstraction, and the
provenance of the runtime rule the model spells out.

## 1. The change and the tested behaviour

The core expression base type `Basic` (`sympy/core/basic.py:28`,
`class Basic(Printable, metaclass=ManagedProperties)`) declares fixed instance
slots (`sympy/core/basic.py:72`, `__slots__ = ('_mhash', '_args',
'_assumptions')`). Its leaf subtypes also declare fixed slots (e.g.
`Symbol.__slots__ = ('name',)`, `sympy/core/symbol.py:203`; `Atom.__slots__ =
()`, `sympy/core/basic.py:1825`).

The mixin `Printable` (`sympy/core/_print_helpers.py:8`, `class Printable:`),
introduced as a base of `Basic` in #19425, did **not** declare `__slots__`.
Under CPython's object model, if ANY class in an instance's MRO (other than the
universal root `object`) omits `__slots__`, that class contributes a per-
instance `__dict__`, and every subclass instance therefore carries a `__dict__`
regardless of the subclasses' own `__slots__`. So `Basic()` instances acquired a
`__dict__` and accepted arbitrary attribute assignment, losing the intended
immutability.

The gold patch (`patch.diff`, the diff verbatim) adds to `Printable`
(`sympy/core/_print_helpers.py`, in the class body after the docstring):

```python
    __slots__ = ()
```

With every class in `Basic`'s MRO now declaring `__slots__` (and none listing
`'__dict__'`), `Basic` instances carry no `__dict__`.

The F2P test `test_immutable` (`sympy/core/tests/test_basic.py`, added by the
test_patch) asserts on `b1 = Basic()`:

```python
assert not hasattr(b1, '__dict__')
with raises(AttributeError):
    b1.x = 1
```

## 2. Type abstraction (the refinement carrier)

| repo reality | model (`model.py`) |
|---|---|
| a class's MRO (excluding `object`) | `chain: PSeq[bool]`, one flag per class |
| a class declares `__slots__` (pins a fixed instance layout, no own `__dict__`) | the corresponding flag is `True` |
| a class omits `__slots__` (contributes a per-instance `__dict__`) | the corresponding flag is `False` |
| `Basic`'s own slot declaration (`__slots__ = (...)`) | flag `True` (the head, modelled as the leading `True` of the chain) |
| (no distinct MRO class here) | the second `True` is a **redundant all-closed padding entry**, not a real MRO layer — see the note below |
| `Printable`, slot declaration | `trait_pins_closed_layout()` — `True` (gold) / `False` (prepatch) |
| instance carries a `__dict__` | `instance_admits_namespace(chain) == not all_closed_layout(chain)` |
| `hasattr(inst, '__dict__')` | `instance_admits_namespace(chain)` |
| `inst.x = 1` (x undeclared) succeeds (stored in `__dict__`) | `bind_undeclared_attribute(chain)` returns `True` |
| `inst.x = 1` (x undeclared) raises `AttributeError` | `bind_undeclared_attribute(chain)` raises `AttributeBindingRefused` |

`AttributeBindingRefused` (user-defined `Exception` subclass) stands in for the
builtin `AttributeError`; a builtin exception in an `Exsures` crashes the Nagini
translator (SPEC_GUIDE §2).

**Termination obligations.** Every modelled function carries
`Requires(MustTerminate(n))` (from `nagini_contracts.obligations`), with
measures 1 (`bind_undeclared_attribute`), 2 (`trait_pins_closed_layout`) and 3
(the two `core_expression_*` observations) so each callee's strictly smaller
measure discharges its caller's obligation. This maps the fact that the real
operations are bounded and always complete: CPython's attribute binding either
stores or raises immediately, and reading a class-level `__slots__` declaration
is immediate. Nagini is a partial-correctness verifier, so without these
obligations a diverging implementation (an infinite loop before the
return/raise) satisfies every postcondition vacuously — including
`Ensures(False)` — while a faithful real patch that hangs would time
`test_immutable` out rather than resolve it.

**On the chain length (D4 correction).** The real MRO of `Basic`, root `object`
excluded, has exactly **two** entries: `[Basic, Printable]` (`Basic` itself, then
its only base `Printable`). The model's chain `PSeq(True, True, trait)` therefore
carries **one extra leading `True` beyond the real MRO** — it is a *redundant
all-closed padding entry*, NOT a distinct third class such as an intermediate
"abstract base". Under the front-recursive conjunction `all_closed_layout`, an
extra `True` entry is inert (it neither adds nor removes a namespace), so the
model's behaviour is identical to the faithful 2-entry chain `PSeq(True, trait)`;
the padding is benign and the rule quantifies over all entries regardless of
length. The flag that the patch changes is `trait` (= `Printable`'s slot
declaration); the leading `True`(s) only encode that `Basic`'s own layout was
already closed at `base_commit`.

## 3. Provenance of the modelled rule (the deep model, not a callee axiom)

The rule `instance has __dict__ ⟺ some MRO class (≠ object) lacks __slots__` is a
**CPython object-model fact**, not a sympy callee. It is therefore modelled
**deeply** (`all_closed_layout` is the front-recursive conjunction over the chain;
`bind_undeclared_attribute` derives the attribute-binding decision from it),
not axiomatized. There is no `@ContractOnly` callee and no consumed axiom.

Provenance of the rule:
- CPython data model, `object.__slots__` documentation: "Without a `__dict__`
  variable, instances cannot have new variables not listed in the `__slots__`
  definition. Attempts to assign to an unlisted variable name raises
  `AttributeError`." and "The action of a `__slots__` declaration is not limited
  to the class where it is defined. `__slots__` declared in parents are
  available in child classes. However, child subclasses will get a `__dict__`
  ... unless they also define `__slots__`."
- The hints/issue note the same: a mixin without `__slots__` re-opens the layout
  of subclasses; `EvalfMixin` already uses `__slots__ = ()` for this reason.

`axiom_check.py` validates this modelled rule **against the real CPython
interpreter** (A-reference): it constructs classes with every combination of
`__slots__`-present / `__slots__`-absent layers, builds an instance, and asserts
that `hasattr(inst, '__dict__')` and the `AttributeError`-on-assignment behaviour
match the model's `all_closed_layout` / `instance_admits_namespace` rule on the
corresponding boolean chain — boundary (empty chain, single layer) plus fuzz
(random multi-layer chains). It uses only the stdlib and exits 0 iff the
modelled rule matches the interpreter on every observation. (No external sympy
callee is executed; the trust point is the object-model rule, validated against
the interpreter that the harness itself runs on.)

## G-CONF (differential conformance: does the MODEL agree with the REAL patched code?)

`conformance_check.py` runs the **contract-stripped impl regions of `model.py`
verbatim** (the shadow) against the **real patched sympy** (the oracle) and exits
0 iff they never disagree. This is the refinement leg no other gate covers:
G-VERIFY says the impl meets the spec, G-PBT says no wrong impl meets it, G-AX
(above, §3) validates the modelled rule against the bare interpreter — none of
them touches the repository.

**Shadow.** All four `impl-start`/`impl-end` regions plus the `pure` region,
copied verbatim with only the contract calls removed (`Requires`, `Ensures`,
`Exsures` sit outside the regions; the `Assert(...)` proof scaffolding inside the
two `core_expression_*` regions is stripped and the locals it constrained —
`empty`, `one`, `two` — are deliberately KEPT rather than dead-code-eliminated,
so the shadow is the region and not a paraphrase). A `PSeq`/`ToSeq` tuple shim
realizes the Nagini sequence the front-recursive fold recurses on. There is no
`@ContractOnly` callee to bridge (`meta.json` `axioms: []`, §3), so the entire
impl region is executable shadow and nothing is assumed.

**Oracle.** The real patched hierarchy, called — not reimplemented — in four
legs:

| leg | oracle | count |
|---|---|---|
| L1 | the pinned F2P shape: real `sympy.core.basic.Basic` (`basic.py:28`) and real `sympy.core._print_helpers.Printable` (`_print_helpers.py:8`); the F2P's own `hasattr(b1,'__dict__')` and `b1.x = 1` | 7 |
| L2 | EVERY class in the patched package, layout fact `cls.__dictoffset__ != 0` | 1469 (1354 open-chain / 115 closed-chain) |
| L3 | the same classes, behaviourally: real `hasattr(inst,'__dict__')` + real undeclared binding | 106 (105 incl. binding) |
| L4 | synthetic chains realized as real class chains via `type(...)`, observed through the real interpreter | 108 207 |

L1 also diffs the model's padded chain `PSeq(True, True, trait)` against the
faithful 2-entry chain `PSeq(True, trait)` **and** against `Basic`'s real MRO
flags, so the §2 "the extra leading `True` is inert padding" claim is tested
rather than trusted. L2 is what exercises the model's **open-namespace branch on
real repository classes** — 1354 real sympy classes have an open chain, whereas
no F2P-adjacent class does.

**Type bridge (§2 inverted).** Forward: a real class -> `PSeq[bool]` = one flag
per MRO entry (`object` excluded), flag True iff that class declares `__slots__`
in its own body without listing `'__dict__'`. Backward: a `PSeq[bool]` -> a real
linear class chain built with `type(name, (base,), {'__slots__': ()})` when the
flag is True and a body omitting `__slots__` when it is False; the leaf is
instantiated. `AttributeBindingRefused` <-> the real `AttributeError`.

**Domain.** The model's only `Requires` is `MustTerminate(n)`, so every finite
`PSeq[bool]` is in the domain and L4 is unrestricted. The two real-class skips
are about what the OBSERVATION denotes, never about which answers come out, and
each is counted and printed: classes with a non-heap (C/static) type in the MRO
(201 — `__slots__` is a heap-type mechanism, so the flag has no denotation
there), and, for L3 only, classes overriding `__getattr__`/`__getattribute__`/
`__dict__` (1357) or `__setattr__` (1), which answer from a lookup hook rather
than from the instance layout. The single real class where the model and
`hasattr` diverge — `sympy.deprecated.class_registry.ClassRegistry`, which
defines `__getattr__` — is NOT dropped: L2 still checks it against
`__dictoffset__`, where the model is correct and `hasattr` was reading the hook.

**Inputs: 109 789 total (>= 1e5), pinned seed `SEED = 20590`.** L4's chain space
is **exhaustively enumerated** for every length 0..12 (all 2**13 - 1 = 8191
chains — a complete decision of that sub-space, stronger than sampling it), plus
16 explicit boundary chains (empty, each singleton, the faithful gold `[T,T]`,
the bug shape `[T,F]`, the model's padded gold `[T,T,T]` and prepatch `[T,T,F]`,
a single open layer at each of 6 positions, `[T]*10`, `[F]*10`), plus 100 000
seeded fuzz chains of length 0..14 over the same space. Both impl branches are
taken and the script FAILS if either is not (42 339 refusals / 65 868 stores).

**Recorded verdict: `G-CONF=pass`** — 109 789 inputs, 0 disagreements.

**Negative controls** (run out-of-tree; confirm the check can actually refute):
unpatched repo -> L1 fails on `Printable`'s missing `__slots__`; fold forced to
`True` -> L2 fails on `Quaternion`; `raise` branch removed -> L1 fails on the
F2P binding; `trait_pins_closed_layout` -> `False` (the prepatch model) -> L1
fails; fold base case `len(chain) <= 1` (off-by-one) -> L2 fails on `CNF`. All
five exit 1.
