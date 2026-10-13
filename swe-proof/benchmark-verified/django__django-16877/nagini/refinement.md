# refinement.md — django__django-16877

The operation-by-operation correspondence between `model.py`'s implementation
(`escape_each` + `escape_when_unsafe_item` + the deep `escaped_seq` /
`escape_codepoints` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new filter — `escapeseq` (`django/template/defaultfilters.py`, added after `escape_filter`)

Gold hunk (purely additive):
```python
@register.filter(is_safe=True)
def escapeseq(value):
    """
    An "escape" filter for sequences. Mark each element in the sequence,
    individually, as a string that should be auto-escaped. Return a list with
    the results.
    """
    return [conditional_escape(obj) for obj in value]
```

The gold body is `[conditional_escape(obj) for obj in value]`: a list
comprehension that applies `conditional_escape` to each item, in order, and
returns a new list. The model splits this into the two faithful pieces it is
made of — the list map (`escape_each`) and the per-item transform
(`escape_when_unsafe_item`, which is what `conditional_escape` does).

### A.1 The sequence map — `escape_each` ↔ the comprehension

| # | model.py impl op (`escape_each`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[Elem]` | `value` (the iterable argument) | R | each item `str`/safe-string ↔ `Elem` (content `PSeq[int]` + `is_safe` flag); the iterable ↔ `List[Elem]` (mapping.md §2). |
| A2 | `result = []`; `while i < len(value)` appending one item per input item; `return result` | the comprehension `[ ... for obj in value]` building a new `list` | I | a list comprehension is exactly an in-order, length-preserving append loop over the input. The postcondition pins `len(Result()) == len(value)` and per-index alignment, so order and arity are preserved (the `join` that follows in the F2P tests is order-sensitive). |
| A3 | `result.append(escape_when_unsafe_item(value[i]))` | `conditional_escape(obj)` for the i-th `obj` | I + (see A.2) | the per-item call; its content is A.2. |

### A.2 The per-item transform — `escape_when_unsafe_item` ↔ `conditional_escape(obj)`

| # | model.py impl op (`escape_when_unsafe_item`) | patch.diff op (`conditional_escape`, `django/utils/html.py:82`) | tag | justification |
|---|---|---|---|---|
| B1 | `if item.is_safe: return Elem(item.chars, True)` | `if hasattr(text, "__html__"): return text.__html__()` (the already-safe branch; a `SafeData` returns itself unchanged) | R | `is_safe` ↔ "has `__html__`" (mapping.md §2). An already-safe item passes through with identical content and stays safe. No re-escaping — this is the F2P `b = [mark_safe(...)]` behaviour. |
| B2 | `return Elem(escape_codepoints(item.chars), True)` | `else: return escape(text)` = `SafeString(html.escape(str(text)))` | A-reference | the escape of an unsafe item is modeled **deeply**: `escape_codepoints` / `escaped_seq` (the spelled-out per-code-point fold in the `pure` region) ARE the substitution. There is no consumed `escape_html` axiom. The deep model is validated **== the real `html.escape`** out-of-band by G-AX (axiom_check.py): `escaped_seq(s) == html.escape(s)`, `quote=True`. The `SafeString(...)` wrapper ↔ `is_safe := True` and is the identity on content (mapping.md §2). |

The discriminating content of the new behaviour:
- An **unsafe** item is escaped exactly once (`& → &amp;`, … `' → &#x27;`); a
  wrong impl that merely marks items safe without escaping (the `safeseq`
  mistake) fails clause `Implies(not item.is_safe, Result().chars ==
  escaped_seq(item.chars))` — reproduced by `model_prepatch_2.py`.
- An **already-safe** item is NOT re-escaped; a wrong impl that escapes every
  item unconditionally (using `escape` instead of `conditional_escape`,
  double-escaping safe items) fails clause `Implies(item.is_safe,
  Result().chars == item.chars)` — reproduced by `model_prepatch.py`.

## B. No consumed axiom; the deep model is an A-reference

There is **no `@ContractOnly` axiom** in this bundle. `conditional_escape` is not
axiomatized: its `__html__`/escape branching is modeled directly as
`escape_when_unsafe_item`, whose contract `escape_each` consumes (caller uses
callee's spec, per SPEC_GUIDE §3 multi-site rule — both are under specification).
The single kind-A construct is the **A-reference** of the unsafe-branch escape
(`escaped_seq` == real `html.escape`, B2), validated by G-AX, never consumed as
an axiom. No dead axioms.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one genuinely new operation — the
per-element conditional escape — is modeled **deeply** (the spelled-out fold
`escaped_seq` for the escape, the `is_safe` branch for the passthrough), not
hidden behind an axiom about a changed function. `str` content is the R-refined
`PSeq[int]`; the comprehension is the I-identical append loop.

## D. verify(model) ⇒ resolved

`escape_each` verifies only if (i) its result has the same length and order as
the input (A.1, so the subsequent `join` produces the expected
character-for-character output), (ii) every already-safe item passes through
unchanged (B1), and (iii) every unsafe item is escaped exactly once by the
per-code-point substitution with `' → &#x27;` (B2). By R (`str` ↔ `Elem`,
`SafeString`/`mark_safe`/`str()` identities on content) the verified transform
equals `[conditional_escape(obj) for obj in value]` on the tested inputs; by
G-AX the deep model `escaped_seq` equals the real `html.escape` (A-reference) and
the safe-passthrough matches `conditional_escape`'s `__html__` branch. Therefore
a model satisfying this spec, refined by the map above, is the gold filter up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(here, the A-reference; G-AX) and refinement fidelity (this document, G-EQ).
