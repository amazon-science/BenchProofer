# refinement.md — django__django-16877

Maps every operation in `implementation_escapeEach` to its `patch.diff`
counterpart (the `escapeseq` filter ADDED to
`django/template/defaultfilters.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled / opaque
unchanged callee validated == real callee by G-AX, **I** identical concrete op.

## Patch (the added filter)
```python
@register.filter(is_safe=True)
def escapeseq(value):
    return [conditional_escape(obj) for obj in value]
```

## Operation correspondence
| # | Lean op (`implementation_escapeEach`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut acc := []` | the list comprehension's accumulator (empty result list) | R | the result list starts empty; `[] : List String` ↔ the empty Python `list`. |
| 2 | `for obj in value do` | `for obj in value` (the comprehension iterator) | I | iterate the input sequence in order; `value : List Elem` ↔ the Python iterable `value`. |
| 3 | `acc := acc ++ [condEscape obj]` | `conditional_escape(obj)` appended to the result | R + A-reference | each element is run through the UNCHANGED per-element conditional HTML escaper and appended in order. The append (`acc ++ [_]`, in iteration order) is R; the escaper `condEscape` ↔ `conditional_escape` is the **A-reference** (validated == real callee by G-AX). |
| 4 | `return acc` | `return [ … ]` | R | the assembled result list ↔ the comprehension's list. |
| (type) | `result : List String` | `list[str]` (`conditional_escape` returns a `str`/`SafeString`) | R | element-type bijection: each escaped element is a string (mapping.md). |

The impl builds the result by an in-order accumulator `for` loop (`acc ++
[condEscape obj]`), which is the imperative skeleton of the patch's list
comprehension `[conditional_escape(obj) for obj in value]`. Op 3's escaper is the
only callee; it is referenced, not axiomatized (the proof closes by a loop-fold
induction and consumes NO property of `condEscape`). The impl region is therefore
NOT all-A-tagged → `conf_skip = false`: G-CONF differential-tests the R/I legs
(length, order, element-wise application) with `condEscape` left as the real
`conditional_escape` callee.

## A-reference (no consumed axiom)
`conditional_escape` is referenced, not axiomatized: the proof does not use any
`condEscape_prop`. `meta.json axioms = []`; `deep_model_references =
["condEscape"]`. G-AX validates that the model treats the per-element escaper as
the real `conditional_escape` (it is invoked unchanged on each element), by
exercising the real `conditional_escape` on boundary + fuzzed elements (ordinary
text AND content marked safe) and confirming it is total and string-valued.

## R/I legs ⇒ G-CONF
Ops 1–4 are R/I, so `conformance_check.py` mechanically differential-tests the
impl shadow (`[conditional_escape(obj) for obj in value]`, with `condEscape` left
as the real `conditional_escape` callee per the A-reference rule) against the
patched `escapeseq` behavior over ≥10⁵ fuzzed input sequences (mixing ordinary
strings and safe-marked strings, varying lengths and orders). `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the companion sequence filter does not exist
(`django/template/defaultfilters.py` has no `escapeseq`), so a sequence is never
escaped element-wise — in the `autoescape off` usage `{{ a|escapeseq|join:"," }}`
the elements would be joined raw, unescaped. The prepatch impl models this by
passing each element through untouched (`acc ++ [obj.text]`) instead of applying
the per-element escaper. It cannot satisfy `problem_spec_escapeEach`: the spec
demands each entry be `condEscape obj` while the impl yields the raw `obj.text` —
precisely the case the FAIL_TO_PASS tests exercise (e.g. `["x&y","<p>"]` must
become `["x&amp;y","&lt;p&gt;"]`). The carried gold proof fails to typecheck
against the buggy impl (the loop-fold induction leaves the unprovable goal
`a.text = condEscape a`), the G-DIFF signal.
