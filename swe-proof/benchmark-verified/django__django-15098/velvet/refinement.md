# refinement.md — django__django-15098

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `resolvePathLanguage` `do` block, the deep `leadingLocaleTag`/`lstep`/
`ldecode` model, and the `listedLanguage` axiom) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `ensures`, **A-reference** where
a deep model is validated == the real callee), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The single change site — the prefix matcher in `get_language_from_path`

Gold hunk (`django/utils/translation/trans_real.py:46`):
```
- language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+)?)(/|$)')
+ language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+){0,2})(/|$)')
```
consumed at `get_language_from_path` (`trans_real.py:508-515`):
```
regex_match = language_code_prefix_re.match(path)     # the changed matcher
if not regex_match: return None
lang_code = regex_match[1]
try:    return get_supported_language_variant(lang_code, strict=strict)
except LookupError: return None
```

| # | Solution.lean impl op (`resolvePathLanguage`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `path : List Char`, under `require ∀ c ∈ path, c.toNat < 128` | `path: str` arg of `get_language_from_path` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. The precondition pins the modeled domain to ASCII paths (mapping.md §3.1 domain note): outside ASCII the library word class is not claimed. |
| A2 | parameter `strict : Bool` (read-only, not `mut`) | `strict: bool` arg (default `False`) | R | `bool ↔ Bool`. Read-only frame: `strict` is never mutated; not declared `mut` (directive 5). |
| A3 | `tag := ldecode (foldl (lstep 2) initLS path)` — the `while` loop building `st`, then `ldecode` — i.e. `leadingLocaleTag 2 path` | `regex_match = language_code_prefix_re.match(path)`; `lang_code = regex_match[1]` (or the whole match is `None`) | A-reference + I | the **changed** matcher is modeled **deeply**: `lstep`/`ldecode` (pure region) and the verified `while` fold ARE the prefix automaton with the patched bound `maxSegs=2`. No consumed `prefixMatch` axiom. The fold ops (`lstep 2 st c`, `ldecode st`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real patched `language_code_prefix_re.match(...)[1]` is the **A-reference** G-CONF validates. mapping.md §3.1. |
| A4 | `result :| result = (match tag with \| none => none \| some lc => listedLanguage lc strict)` | `if not regex_match: return None` else `try: return get_supported_language_variant(lang_code, strict) except LookupError: return None` | A-consumed + R | the downstream resolve is the **unchanged** callee `get_supported_language_variant`, modeled opaquely by `listedLanguage` with its `LookupError` folded into `none` (mapping.md §3.2). `none` tag ⇒ `None` return (the `not regex_match` branch). The `:|` choice binds `result` to exactly the callee's result; the proof consumes only "`result` = `listedLanguage tag strict`", asserting no property of the value. R: `Option (List Char)` ↔ `str`/`None` (mapping.md §2). |
| A5 | `return result` (`Option (List Char)`) | the returned value (`str` or `None`) | R | `some s ↔ str`, `none ↔ None`. The caller (`i18n_patterns` URL resolution) observes only this code. |

Discriminating content of the change — a tag carrying **two** additional
subtags (a script *and* a region, e.g. `/en-latn-us/`, `/de-ch-1901/`,
`/nan-hani-tw/`) is now recognised, whereas the old matcher (`?`, ≤1 additional
subtag) rejected it — lives in `lstep 2`'s `if st.segs < maxSegs` guard with
`maxSegs = 2` (model) ⇔ the `{0,2}` quantifier (real). The pre-patch matcher
admitted `maxSegs = 1`; `Solution_prepatch.lean` reproduces that (`lstep 1`) and
**fails** `out = pathLanguage path strict` (which fixes `leadingLocaleTag 2`) at
exactly the two-additional-subtag input (G-DIFF — see §E).

## B. No second site

The patch edits a single regex literal. `get_supported_language_variant`
(`trans_real.py:464`) is **unchanged**; it appears only as the A-consumed opaque
callee `listedLanguage` (site A4), not as a separately-modeled function. There
is no other independently-fixed behaviour, so there is one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
prefix matcher's subtag bound — is modeled **deeply** (the spelled-out automaton
`leadingLocaleTag`/`lstep`/`ldecode`, step A3, an A-reference + I), not hidden
behind an axiom about the function under change: there is no consumed
`prefixMatch` axiom. The only consumed axiom, `listedLanguage` (site A4), covers
the **unchanged** callee `get_supported_language_variant`.

## D. `mut`-frame discipline (directive 5)

Neither `path` nor `strict` is declared `mut`: the impl mutates only the local
scan state (`st`, `i`) and never the inputs. The loop's `done_with i =
path.length` and the invariant `st = (path.take i).foldl (lstep 2) initLS` pin
the scan to a pure read over `path`. No postcondition refers to a value the impl
could have silently overwritten — the inputs are framed read-only by
construction (Lean has no aliasing; the unconstrained-`mut` hole does not arise
because no input is `mut`).

## E. verify(Solution) ⇒ resolved

`resolvePathLanguage` verifies only if its output equals `pathLanguage path
strict`, which is `leadingLocaleTag 2 path` (the patched-bound automaton, A3)
post-composed with the opaque resolve (A4). By R (`str ↔ List Char`, `bool ↔
Bool`, `Option ↔ str/None`) the verified function equals the patched
`get_language_from_path` on the tested `str` inputs; by G-CONF the deep model
`leadingLocaleTag 2` equals the real patched `language_code_prefix_re.match(...)[1]`
(A-reference) over the F2P/issue boundary + 10⁵ fuzz inputs; by G-AX the real
`get_supported_language_variant` is a deterministic total-dichotomy function of
`(lang_code, strict)` (A-consumed), so `listedLanguage` faithfully captures it.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE).

The pre-patch (`leadingLocaleTag 1`) is byte-faithful to the **old** matcher and
diverges from the spec exactly on a two-additional-subtag tag (`/en-latn-us/`
extracts `en-latn-us` under the spec but `None` under `lstep 1`), which is the
F2P `test_get_language_from_path_real` change — so the prepatch fails verify on
the discriminating clause. Trust points are exactly the two of plan §1.1:
axiom/callee soundness (G-AX) and refinement fidelity (this doc + G-CONF).
