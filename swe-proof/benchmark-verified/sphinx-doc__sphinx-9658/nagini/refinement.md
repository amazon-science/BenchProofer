# refinement.md — sphinx-doc__sphinx-9658

The operation-by-operation correspondence between `model.py`'s implementation
(the `subclass_short_name`, `placeholder_display_name`, and `qualified_reference` impl
regions, plus the deep `render_qualified` model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The short-identifier site — `_make_subclass` (`sphinx/ext/autodoc/mock.py:72`)

Gold hunk:
```
  attrs = {'__module__': module,
           '__display_name__': module + '.' + name,
+          '__name__': name,
           '__sphinx_decorator_args__': decorator_args}
```

| # | model.py impl op (`subclass_short_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name: List[int]` | `name: str` argument of `_make_subclass` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `result` built equal to `name`, returned | `attrs['__name__'] = name` — the subclass records its own name as its short identifier | R + I | the placeholder's `__name__` attribute IS `name`; the model returns that code-point list. The carrier copy (the `take`-fold loop) is the identity on the sequence (`Ensures ToSeq(Result()) == ToSeq(name)`), matching `__name__ == name`. |

The pre-patch code recorded no `__name__`, so `self.__name__` inside `__init__`
fell through `__getattr__` to a fresh placeholder rather than the string name.
`model_prepatch_2.py` reverts this site (the short identifier is not the
attribute name) and **fails** `Ensures(ToSeq(Result()) == ToSeq(name))` (G-DIFF).

## B. The display-identifier site — `_MockObject.__init__` (`sphinx/ext/autodoc/mock.py:42`)

Gold hunks (the default + the assignment):
```
  __display_name__ = '_MockObject'
+ __name__ = ''
  ...
  def __init__(self, *args, **kwargs):
-     self.__qualname__ = ''
+     self.__qualname__ = self.__name__
```

| # | model.py impl op (`placeholder_display_name`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `short_name: List[int]` (the short identifier produced at site A) | `self.__name__` read inside `__init__` | R + I | `self.__name__` is the short identifier recorded at site A (`name`); modeled as the input `short_name`. The `__name__ = ''` class default (hunk 1) guarantees the attribute exists for a bare placeholder; the data flow under test is the `_make_subclass` path where it equals `name`. |
| B2 | `result` built equal to `short_name`, returned | `self.__qualname__ = self.__name__` — the display identifier becomes the short identifier | R + I | `Ensures(ToSeq(Result()) == ToSeq(short_name))` mirrors `__qualname__ == __name__`; the carrier copy is the identity on the sequence. |

The pre-patch code set `self.__qualname__ = ''`. `model_prepatch.py` reverts
this site (the display identifier is empty) and **fails**
`Ensures(ToSeq(Result()) == ToSeq(short_name))` (G-DIFF).

## C. The render site — `qualified_reference` ↔ the unchanged renderer

The renderer that carries the bug is `restify` (`sphinx/util/typing.py`
`_restify_py37`, **unchanged**), which reads the placeholder's `__qualname__`
directly and composes `':py:class:`%s.%s`' % (obj.__module__, obj.__qualname__)`.
The single FAIL_TO_PASS test is `tests/test_util_typing.py::test_restify_mock`,
so the dangling-dot symptom is observable through `restify` only. `stringify`
(`test_stringify_mock`, PASS_TO_PASS) yields the SAME value `<module>.<name>` at
both commits via a DIFFERENT code path — the placeholder is falsy
(`__len__()==0`), so `stringify` short-circuits at its `not annotation` guard to
`repr(obj)` == `__display_name__` == `<module>.<name>` and never reads
`__qualname__`; it is therefore already correct at base_commit and is NOT a
bug-discriminator (see §C-note).

| # | model.py impl op (`qualified_reference`) | patch.diff op / repo op | tag | justification |
|---|---|---|---|---|
| C1 | `short = subclass_short_name(name)` | `_make_subclass` records `__name__ = name` (site A) | R + I | the short identifier of the placeholder reached by `name`. |
| C2 | `display = placeholder_display_name(short)` | `__init__` sets `__qualname__ = __name__` (site B) | R + I | the display identifier of that placeholder. |
| C3 | `result = module + [46] + display` (loop copies `module`, then `.`, then `display`), `Ensures ToSeq(Result()) == render_qualified(ToSeq(module), ToSeq(name))` | `':py:class:`%s.%s`' % (obj.__module__, obj.__qualname__)` in `restify` (the F2P renderer) | A-reference | the renderer's dotted join is modeled **deeply** by the pure `render_qualified` (`module + '.' + display`); there is **no consumed axiom**. The deep model is validated **== the real `restify`** out-of-band by G-AX (axiom_check.py runs the real `restify` on the real placeholder and asserts the rendered reference equals `module + '.' + name`, never a dangling `<module>.`). `[46]` is `'.'`. |

The discriminating content of the change lives in the composition C1→C2→C3:
because `display == name` (sites A+B), `restify` ends the rendered reference in
the attribute `name` (`<module>.<name>`); the `Ensures(Implies(len(name) > 0,
len(Result()) > len(module) + 1))` clause pins that a non-empty name contributes
a non-empty trailing component, so the reference never degenerates to the
dangling `<module>.` the bug produced in `restify`.

**§C-note (provenance):** the deep model's computed VALUE (`module + '.' + name`)
also equals the real `stringify` output, but `stringify` reaches it via the
falsy-placeholder `repr()`/`__display_name__` short-circuit (not via
`__qualname__`), so it is invariant across the two commits. axiom_check.py
therefore discriminates the fix on `restify` only and pins `stringify` purely as
a value equality (P2P), not as a bug-path.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that genuinely
*changed* — recording the short identifier and propagating it to the display
identifier — are modeled **deeply** (the `subclass_short_name` and
`placeholder_display_name` impls, sites A and B), not hidden behind an axiom about the
function under change. The only A-tag is the **A-reference** at C3: the
*unchanged* renderer's dotted join, modeled deeply by `render_qualified` and
validated == the real `restify`/`stringify` by G-AX. There is **no A-consumed
axiom** (no `@ContractOnly`); the `axioms` region is empty.

## E. verify(model) ⇒ resolved

**Termination obligation.** Nagini proves partial correctness by default, so
the value postconditions alone would admit a non-terminating implementation
(frozen loop / unbounded self-recursion) that never delivers the value its
contract pins — such an implementation verifies vacuously while its faithful
refinement never produces the identifier/reference and the F2P test fails
with a recursion error. Each modeled function therefore carries
`Requires(MustTerminate(n))`: the helpers carry measure 2 and the composed
render site measure 3 (leaving room to invoke the two helpers, whose
obligation is strictly smaller). Every loop discharges the obligation with a
strictly decreasing, bounded-below `Invariant(MustTerminate(len(...) - i))`
measure. With this discipline a body that loops forever or self-recurses at
the same measure fails the obligation-leak check, so "verifies" implies "the
value is actually delivered in finite time" — matching the real functions,
which are straight-line attribute stores plus a bounded string join.

`qualified_reference` verifies only if its output equals
`render_qualified(module, name) == module + '.' + name` (C1→C3) with the
trailing component being the attribute name (the `len` clause). By R (str ↔
List[int], `'.'` ↔ `[46]`) the verified composition equals the real placeholder
`__module__ + '.' + __qualname__` with `__qualname__ == name`; by G-AX the deep
model `render_qualified` equals the real `restify` on the placeholder
(A-reference, the F2P bug-path). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited
renderer — and the gold patch resolves. The sole FAIL_TO_PASS test is
`tests/test_util_typing.py::test_restify_mock` (the dangling-dot symptom);
`tests/test_util_typing.py::test_stringify_mock` is PASS_TO_PASS — it asserts the
same value `unknown.secret.Class` but reaches it via the falsy-placeholder
`repr()`/`__display_name__` short-circuit, so it passes at both commits and is
not a discriminator. (G-RESOLVE: F2P `test_restify_mock` flips false→true; the
`test_stringify_mock` P2P and all other `restify`/`stringify` tests stay
passing.) The trust point is exactly the refinement-fidelity / A-reference one of
PLAN §1.1: there is no axiom soundness obligation because no axiom is consumed;
the A-reference is G-AX-validated (rc=0 on both the base_commit and gold
containers).
