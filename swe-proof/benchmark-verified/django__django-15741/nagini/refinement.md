# refinement.md — django__django-15741

The operation-by-operation correspondence between `model.py`'s implementation
(the `lookup_format` impl region, the deep `resolve` model, and the
`format_value` / `do_lookup` axioms) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The lookup site — `get_format()` (`django/utils/formats.py:100`)

Gold hunk (the single inserted line, at body line 116 post-patch):
```
     if use_l10n and lang is None:
         lang = get_language()
+    format_type = str(format_type)  # format_type may be lazy.
     cache_key = (format_type, lang)
     try:
         return _format_cache[cache_key]
```
Everything after this line (`cache_key`, `_format_cache`, the `getattr` scan,
the `FORMAT_SETTINGS` / `ISO_INPUT_FORMATS` tests, the `settings` fallback) is
unchanged; the only edit is coercing `format_type` to a real `str` first.

| # | model.py impl op (`lookup_format`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `format_type: FormatType` (`deferred`, `content`) | the `format_type` argument of `get_format` (a real `str` or a lazy `__proxy__`) | R | `FormatType` ↔ "string that may be deferred": `deferred==False` ↔ real `str`, `deferred==True` ↔ lazy proxy; `content` ↔ the denoted string's code points (mapping.md §2). |
| A2 | the copy loop builds `name` (a `List[int]`) with `ToSeq(name) == ToSeq(content)`, asserted `== resolve(format_type)` | `format_type = str(format_type)` — coerce the (possibly lazy) name to its underlying `str` | A-reference | the changed coercion is modeled **deeply**: `resolve` (the `@Pure` model in the `pure` region) returns `ToSeq(content)` **regardless of `deferred`**; the loop realises that resolved value as a concrete list `name`. There is no consumed coercion axiom — the proof never depends on one. The deep model is validated **== the real `str()`** out-of-band: G-AX (axiom_check.py) runs `str()` on both an already-resolved name and the same name deferred (a lazy proxy) and asserts both equal the underlying string (= `resolve`). The real `str()` IS that coercion (mapping.md §3.1; lazy proxy's `__str__` evaluates to the underlying string). |
| A3 | `result = do_lookup(name)`; the postcondition is `ToSeq(Result()) == format_value(resolve(format_type))` | the unchanged remainder of `get_format` (cache key, `getattr` scan, membership tests, settings fallback) applied to the now-`str` `format_type` | A-consumed | `format_value` / `do_lookup` are the weakest contract on the unchanged downstream lookup the proof needs: the value is a deterministic function of the **resolved** name only (mapping.md §3.2). The proof consumes `do_lookup`'s `Ensures` (`ToSeq(Result()) == format_value(ToSeq(name))`) and, because `ToSeq(name) == resolve(format_type)`, derives the postcondition. G-AX confirms the real `get_format` is keyed only on the resolved name. |
| A4 | `return result` (a `List[int]`) | the value `get_format` returns | R | the returned format value ↔ `List[int]` whose `ToSeq` is `format_value` of the resolved name; the F2P tests compare returned values by equality (mapping.md §2). |

The discriminating content of the change — that the (possibly deferred) name is
**resolved before** it is used as a lookup key, so the value depends only on the
resolved characters — lives in step A2 (`resolve` ignores the `deferred` flag)
feeding A3. The pre-patch does NOT resolve a deferred name before the lookup
(`getattr(module, <lazy>)` raises `TypeError: attribute name must be string`);
`model_prepatch.py` reproduces that — its impl resolves the name only on the
`deferred == False` branch and feeds an empty (non-resolved) key on the
`deferred == True` branch — and **fails** the postcondition
`ToSeq(Result()) == format_value(resolve(format_type))`, which is exactly the
spec sensing the change (G-DIFF). The real crash is the extreme case of "the
deferred value is not usable as a resolved key"; the model encodes it as a value
mismatch (no-Exsures) on the same branch.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* —
the up-front coercion `str(format_type)` that makes the downstream lookup
independent of the deferred form — is modeled **deeply** (the spelled-out
`resolve` consumed in `lookup_format`, step A2, an **A-reference**), not hidden
behind an axiom about the function under change. There is **no consumed
coercion axiom**. The consumed axioms `format_value` / `do_lookup`
(**A-consumed**, step A3) cover the **unchanged** downstream lookup the function
already performed and continues to perform; the coercion's `str()` appears only
as the **A-reference** that G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`lookup_format` verifies only if its output equals `format_value` of the
**resolved** name (A2 + A3), i.e. only if the (possibly deferred) name is
resolved before lookup. By R (`FormatType` ↔ str-or-lazy, list ↔ returned
value) the verified function equals `get_format` with the inserted
`format_type = str(format_type)` on the tested inputs; by G-AX the deep model
`resolve` equals the real `str()` coercion (A-reference) and the real
downstream lookup meets the `format_value` / `do_lookup` axioms it stands for
(A-consumed, validated as keyed-only-on-resolved-name). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
