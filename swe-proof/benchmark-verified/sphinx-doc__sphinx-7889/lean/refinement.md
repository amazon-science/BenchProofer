# refinement.md — sphinx-doc__sphinx-7889

Maps every operation in `implementation_mockSubscript` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `mockSubscript` (`_MockObject.__getitem__`)

Post-patch repo code (`patch.diff`, `sphinx/ext/autodoc/mock.py:55-56`):
```python
def __getitem__(self, key: Any) -> "_MockObject":
    return _make_subclass(str(key), self.__display_name__, self.__class__)()
```
where `_make_subclass(name, module, ...)` builds
`'__display_name__': module + '.' + name` (`mock.py:73`).

Lean impl (`implementation_mockSubscript`):
```lean
def implementation_mockSubscript
    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
  let name : PyKey := PyKey.str (strChars key)
  return concatName displayName name
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `key : PyKey` | the `key` argument of `__getitem__` (`Any`) | **R** | a subscript key is either an already-textual `str` (`PyKey.str s`) or a non-text object whose `str()` rendering is `r` (`PyKey.other r`). Bijection in mapping.md. |
| 2 | `displayName : List Char` | `self.__display_name__ : str` | **R** | per-code-point `str` ↔ `List Char` (SPEC_GUIDE §2). |
| 3 | result `: Except Unit (List Char)` | the constructed subclass's `__display_name__` vs. the raised `TypeError` | **R** | `Except.ok d` ↔ a derived subclass with display name `d`; `Except.error ()` ↔ the `TypeError` raised by the display-name join. |
| 4 | `let name := PyKey.str (strChars key)` | `str(key)` — render the key to text first | **R / I** (deep model of the changed op) | **the fixed operation.** `strChars` models `str(key)`: idempotent on text (`str(s) == s`, so `PyKey.str s ↦ s`) and renders a non-text key to its textual form (`PyKey.other r ↦ r`). Wrapping the result in `PyKey.str` records that the join now always receives a textual component (`str(...)` always returns a `str`). This is the line the patch adds (`key` → `str(key)`); modeled deeply, never axiomatized (SPEC_GUIDE §3). G-CONF differential-tests it. |
| 5 | `return concatName displayName name` | `_make_subclass(name, module, ...)` → `module + '.' + name` | **A-reference** (deep model of unchanged callee) | `concatName` models the UNCHANGED display-name concatenation `module + '.' + name`: a textual component yields `Except.ok (module ++ '.' :: s)`, a non-text component raises (`Except.error ()`). Validated == the real concatenation by G-AX. No `_prop` axiom consumed — the model IS the behavior. Because op 4 always hands it a `PyKey.str`, the post-patch impl never reaches the error leg. |

The impl region contains **R/I + one A-reference** ops and NO consumed axiom, so
`conf_skip = false`: `conformance_check.py` differential-tests the full subscript
outcome (render-then-join) against an in-process replica of the patched
`__getitem__` behavior.

## Soundness check (verify ⟹ correct)

- `problem_spec_mockSubscript displayName key result` pins the outcome EXACTLY
  for every key: `result = Except.ok (displayName ++ '.' :: strChars key)`. The
  result is fully determined — Directive 5 (frame): no output component is left
  unconstrained. Directive 8: the postcondition is grounded in the inputs via the
  structural rendering `strChars key` and the explicit concatenation
  `displayName ++ '.' :: …`, not an opaque oracle; the result must be *produced
  by* the modeled render-and-join, including the requirement that subscripting
  always succeeds (`Except.ok`, never `error`) for EVERY key — the precise
  behavior the fix guarantees.
- The prepatch impl forwards the raw `key` to the display-name join
  (`concatName displayName key`) without rendering it to text. It violates the
  spec on the discriminating clause: for a non-text key `PyKey.other r`,
  `concatName displayName (PyKey.other r) = Except.error ()`, while the spec
  requires `Except.ok (displayName ++ '.' :: r)`. Its carried gold proof cannot
  close (G-DIFF/G-PANEL). For a text key `PyKey.str s` both impls agree
  (`Except.ok (displayName ++ '.' :: s)`), confirming the fix preserves the
  existing textual-subscript behavior.
- This discriminating case is exactly the FAIL_TO_PASS behavior in
  `tests/test_ext_autodoc_mock.py::test_MockObject`: indexing a mock with a
  `TypeVar` (`mock.SomeClass[T]`, a non-text key) raised `TypeError` at
  base_commit and now succeeds, producing a derived subclass. The PASS_TO_PASS
  tests subscript with text keys / use `__getattr__` (text keys), which both
  impls handle identically.
- G-CONF confirms the R/I render-and-join outcome == an in-process replica of the
  post-patch `__getitem__` (`str(key)` then `module + '.' + str(key)`) over
  hand-picked edge cases (text keys, non-text keys such as a `TypeVar`, empty
  display name) plus ≥1e5 fuzzed inputs.
