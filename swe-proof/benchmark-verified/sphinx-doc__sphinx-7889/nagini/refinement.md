# refinement.md — sphinx-doc__sphinx-7889

The operation-by-operation correspondence between `model.py`'s implementation
(the `subscript_placeholder` impl region, the deep `render_text` model, and the
live `display_name` axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`/`Requires`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

**Termination obligation.** `subscript_placeholder` carries
`Requires(MustTerminate(2))` (and each materialisation loop the invariant
`MustTerminate(<measure>)` with a strictly decreasing, bounded-below measure).
Nagini is a partial-correctness verifier by default: without the obligation an
implementation that diverges before returning (an endless loop followed by any
return) satisfies the display-name postcondition vacuously — a same-spec
wrong impl the adversarial audit exhibited. The obligation excludes that whole
class; the real subscript operation is bounded work and always returns its
placeholder.

## The change site — `_MockObject.__getitem__` (`sphinx/ext/autodoc/mock.py:55-56`)

Gold hunk:
```
-    def __getitem__(self, key: str) -> "_MockObject":
-        return _make_subclass(key, self.__display_name__, self.__class__)()
+    def __getitem__(self, key: Any) -> "_MockObject":
+        return _make_subclass(str(key), self.__display_name__, self.__class__)()
```

`model.py` models `__getitem__` as `subscript_placeholder`. The index `key` is
modelled by the pair `(key_is_text, key_text)`: `key_text` is the `List[int]`
code points of the index's canonical textual rendering (what `str(key)`
produces) and `key_is_text` records whether the index value is *already*
textual (so that passing it on unchanged would satisfy the string-only
fabricator). `self.__display_name__` is the `module` parameter (`List[int]`).
The trailing `()` instantiation is observationally irrelevant to the tested
property (the construction succeeding and the display name) and is folded into
the fabricator step.

| # | model.py impl op (`subscript_placeholder`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter pair `(key_is_text, key_text: List[int])` | `key: Any` (the subscript index) | R | a Python object ↔ `(is_text flag, List[int] code points of its `str()`)`. `key_is_text == isinstance(key, str)`; `key_text == [ord(c) for c in str(key)]`. The `key: str → key: Any` signature widening is exactly "the index need not be textual" (mapping.md §2). |
| 2 | parameter `module: List[int]` | `self.__display_name__` (a `str`) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| 3 | `name = render_text(ToSeq(key_text))`; `name_is_text = True` | `str(key)` | I + A-reference | `str(key)` is the canonical textual rendering of the index and is **always textual**; `render_text` is the deep model of that rendering (identity on the text content the spec observes — the F2P test only inspects that the construction succeeds and `__doc__`/`isinstance`, never the rendered glyphs of `~T`), so `name_is_text` is unconditionally `True`. The pre-patch passes `key` itself, hence `name_is_text = key_is_text` — false for a non-textual index. This single op IS the fix. |
| 4 | `produced = display_name(name_is_text, name, ToSeq(module))` | `_make_subclass(<name-arg>, self.__display_name__, self.__class__)` | A-consumed | the unchanged fabricator. `display_name` is the weakest contract the proof needs: (Requires) it is defined ONLY for a textual name argument whose code points are honest scalar values — no interior NUL and no surrogate code point (55296..57343). The real `_make_subclass` does `module + '.' + name` (str concat) and `type(name, ...)` (needs a str name, rejects a NUL in it with `ValueError`, and rejects a lone surrogate in it with `UnicodeEncodeError` since the class name has no encoded form); (Ensures) the fabricated subclass's display name is `module + '.' + name`. The proof consumes the Requires: the post-patch discharges the textual half because step 3 made the name textual, and the NUL-free + surrogate-free halves from the caller's precondition that the index rendering carries only scalar code points; the pre-patch CANNOT discharge `name_is_text`, modelling the real `TypeError`. G-AX confirms the axiom against the real `_make_subclass` on all three Requires halves (mapping.md §3). |
| 5 | the materialisation loops producing `result` with `ToSeq(result) == module ++ [46] ++ name` | the produced subclass carries `__display_name__ == module + '.' + name` (and is a `_MockObject` subclass, returned after `()` instantiation) | R | `result` (`List[int]`) is the code-point materialisation of the fabricator's display name `module + '.' + str(key)`. `46 == ord('.')`. The F2P test observes that the construction succeeds and the class behaves like a `_MockObject` subclass; the display content is the fabricator's contract. |

The discriminating content of the change — coercing the index to text
**before** handing it to the string-only fabricator — lives in step 3
(`name_is_text = True` because `name = render_text(key_text)` is always
textual) vs. the pre-patch's `name_is_text = key_is_text`. `model_prepatch.py`
reproduces the pre-patch (passes the raw index to `display_name`) and **fails**
the call's `Requires(name_is_text)` when `key_is_text` is false — exactly the
spec sensing the change (G-DIFF). This is the modelled image of
`_make_subclass(key, ...)` raising `TypeError` on a `TypeVar` index.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the
`str(...)` coercion of the index before it reaches the fabricator — is modelled
**deeply** (step 3: `render_text` always textual ⇒ `name_is_text = True`),
not hidden behind an axiom about the function under change (`__getitem__`).
The only consumed axiom, `display_name` (**A-consumed**, step 4), covers the
**unchanged** callee `_make_subclass` that both the old and new code invoke; the
fix is the argument now handed to it. `render_text` is an **A-reference** only
in the trivial sense that `str()` is total and text-valued — its content is the
identity on the text the spec observes, so the proof does not depend on any
non-identity property of it; G-AX nonetheless exercises `str(key)` end-to-end
against the real `_make_subclass` to confirm the coercion succeeds for the
non-textual indices the issue reports.

## verify(model) ⇒ resolved

`subscript_placeholder` verifies only if it hands the fabricator a textual name
for EVERY index (step 4's textual + NUL-free + surrogate-free Requires
discharged via step 3 — `name_is_text` because the rendering is always textual,
and the scalar-code-point halves from the caller's precondition that the
index's textual rendering carries no NUL and no surrogate, which holds for
every index the operation must handle) and
its result is the display content `module + '.' + str(key)` (step 5). By R
(`Any` ↔ `(is_text, List[int])`, `str` ↔ `List[int]`, the `()` instantiation
and `_MockObject`-subclass identity) the verified function equals
`_make_subclass(str(key), self.__display_name__, self.__class__)()` on every
index, including the `TypeVar` index the F2P test
(`tests/test_ext_autodoc_mock.py::test_MockObject`, `SubClass2(mock.SomeClass[T])`)
exercises. By G-AX the `display_name` axiom (A-consumed) is sound against the
real `_make_subclass`. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the one audited callee —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two
of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ).
