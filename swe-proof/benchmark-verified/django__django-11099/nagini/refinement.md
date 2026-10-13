# refinement.md — django__django-11099

The operation-by-operation correspondence between `model.py`'s implementation
(the `accepts_ascii` / `accepts_unicode` impl regions, the deep folds
`all_*_permitted`, and the membership axioms `permitted_ascii` /
`permitted_unicode`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses the axiom's `Ensures`, and **A-reference**, where a deep
model is validated `==` the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Gold patch (both hunks)

```
 class ASCIIUsernameValidator(validators.RegexValidator):
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\Z'
 ...
 class UnicodeUsernameValidator(validators.RegexValidator):
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\Z'
```

Two hunks, one per validator class; the only change is the end anchor `$` → `\Z`
in each pattern string. The character class `[\w.@+-]` and `flags` are unchanged.

## A. The ASCII validator — `accepts_ascii` ⇔ `ASCIIUsernameValidator`

| # | model.py impl op (`accepts_ascii`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[int]` | the `value` argument of `RegexValidator.__call__`, after `str(value)` (`core/validators.py:57`) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `Result()` is `True`/`False` | "no `ValidationError`" vs raised | R | `__call__` raises iff `not regex_matches` and `inverse_match` is `False`; "accepted" ⇔ a match exists (mapping.md §2). |
| A3 | `len(value) == 0 → return False` | `^[\w.@+-]+\Z` requires `+` (≥1 char): the empty string never matches | I | the `+` quantifier forbids the empty match; modeled as the explicit empty-string rejection. |
| A4 | `permitted_ascii(c)` per code point | membership of `c` in the class `[\w.@+-]` under `re.ASCII` | A-consumed | unchanged callee; the proof uses the axiom's `Ensures` (mapping.md §3.1). G-AX confirms it against the real class. |
| A5 | the result is `all_ascii_permitted(ToSeq(value))` over a NON-EMPTY value, i.e. EVERY code point — the last included — is permitted | `^[\w.@+-]+\Z` matches `str(value)` | A-reference | the changed end-anchoring is modeled **deeply**: the backward loop + the fold `all_ascii_permitted` ARE the whole-string "every code point admissible" decision. There is no axiom about the match itself. G-AX (axiom_check.py) validates `deep == real ^[\w.@+-]+\Z` under `re.ASCII` (mapping.md §3.2). |

## B. The Unicode validator — `accepts_unicode` ⇔ `UnicodeUsernameValidator`

Identical structure to site A, with `permitted_unicode` (the class under
`flags=0`) and `all_unicode_permitted`.

| # | model.py impl op (`accepts_unicode`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| B1 | parameter / result refinement | as A1, A2 | R | identical to site A. |
| B2 | `len(value) == 0 → return False` | the `+` quantifier | I | as A3. |
| B3 | `permitted_unicode(c)` per code point | membership of `c` in `[\w.@+-]` under `flags=0` | A-consumed | unchanged callee (mapping.md §3.1); G-AX-checked. |
| B4 | result `== all_unicode_permitted(ToSeq(value))` over non-empty value | `^[\w.@+-]+\Z` under `flags=0` | A-reference | deep model of the changed end anchor, validated `==` the real fixed regex by G-AX (mapping.md §3.2). |

## C. The discriminating delta and the prepatch (G-DIFF)

The whole change is `$` → `\Z`. `$` matches at end-of-string OR immediately
before a single trailing line feed; `\Z` matches only at the true end. So the
sole behavioural difference is: a non-empty all-permitted string followed by
exactly one trailing line feed is ACCEPTED by `$` but REJECTED by `\Z`.

`model_prepatch.py` keeps the spec byte-identical and reproduces the `$`
skeleton: it drops a single trailing line feed (`m = n-1` when `value[n-1]==10`)
before the all-permitted check. It **fails** the postcondition
`Result() == (len(value) >= 1 and all_*_permitted(ToSeq(value)))` for BOTH
functions on a trailing-line-feed witness (e.g. `[97, 10]` = `"a\n"`): the
prepatch returns `True`, the spec requires `False` because the line feed is not
permitted (`permitted_*(10) == False`). This is exactly the spec sensing the
change. The post-conditions of model.py and model_prepatch.py are byte-identical
(verified); only the impl regions differ. Both `accepts_ascii` and
`accepts_unicode` yield an independent G-DIFF witness (the patch fixes both
validators), so the single `model_prepatch.py` fails on two clauses, one per
independently-fixed validator.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — the end anchor of the regex — is modeled **deeply** (the
"non-empty and every code point admissible" decision via the front-recursive
folds and the verified loops, an **A-reference** validated `==` the real fixed
regex by G-AX), not hidden behind an axiom about the function under change. The
only consumed axioms, `permitted_ascii` / `permitted_unicode`, cover the
**unchanged** character class `[\w.@+-]` the pattern still uses; the match itself
appears only as the **A-reference** that G-AX validates the deep model against.

## E. verify(model) ⇒ resolved

`accepts_ascii` / `accepts_unicode` verify only if their result equals "non-empty
and every code point permitted" (A5/B4) — which, by G-AX, equals the real fixed
regex `^[\w.@+-]+\Z` under each validator's flags. By R (`str` ↔ `List[int]`,
"accepted ⇔ no `ValidationError`") the verified predicate equals the real
validators' decision on the tested `str` inputs. The prepatch's `$` semantics
(the bug) fails the spec on a trailing-line-feed input — the exact case the F2P
tests add (`'trailingnewline\n'`, `'trailingnewline
'`). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX, the
membership axioms + the deep-model == fixed-regex check) and refinement fidelity
(this document, G-EQ).
