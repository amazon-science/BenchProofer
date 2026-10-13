# refinement.md — django__django-15098

The operation-by-operation correspondence between `model.py`'s implementation
(the `language_prefix_len` impl region + the deep `prefix_len_spec` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated `== ` the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — the locale-prefix regex (`trans_real.py:46`)

Gold hunk:
```
-language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+)?)(/|$)')
+language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+){0,2})(/|$)')
```

The patch changes the repeat bound of the `([@-]\w+)` sub-tag group from `?`
(`{0,1}`) to `{0,2}`: a locale candidate may now carry a primary sub-tag plus
**up to two** further sub-tags (script + region per RFC 5646), instead of one.

| # | model.py impl op (`language_prefix_len` / `prefix_len_spec`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | `is_word(c)` — `@Pure` `@ContractOnly` (`axioms` region) | the `\w` character class inside the regex, i.e. per-code-point membership of the "word" class a sub-tag's characters are drawn from | A-consumed | the ONE consumed axiom. Its `Ensures` pins the class exactly **below** code point 128 and leaves it **open** at/above 128, which is precisely what the real class — evaluated over the whole of Unicode — satisfies. The proof therefore holds for EVERY class the contract permits, so no implementation may decide the open region for itself. Soundness of both halves, and of the deep model with `is_word` instantiated at its real counterpart, is discharged by axiom_check.py / G-AX (mapping.md §3.1, §4). |
| A1 | parameter `path: List[int]` | the `str` `path` matched by `language_code_prefix_re.match(path)` | R | `str` ↔ `List[int]` code points (mapping.md §3). |
| A2 | `path[0] == 47` guard | the regex anchor `^/` | A-reference | the leading-`/` requirement of the matcher; part of the deeply-modeled regex (mapping.md §4). |
| A3 | `run_len(body)`, `well_formed_tag(tag)` | `(\w+([@-]\w+)…)` group 1 = the maximal word/separator run that is a well-formed `word+(sep word+)*` | A-reference | the changed regex is modeled **deeply**: `run_len` + `well_formed_tag` (front-recursive, `pure` region) ARE the group-1 structure, expressed over the A0 axiom rather than over any transcription of the character class. Validated `== real matcher` by G-AX (mapping.md §4). |
| A4 | `nsep(tag) <= 2` (the `maxsep == 2` argument) | the `{0,2}` repeat bound | A-reference | **the single behavioural change.** The separator budget 2 ⇔ `{0,2}`. The pre-patch `?` ⇔ budget 1 — captured by `maxsep == 1` in `model_prepatch.py`. G-AX checks `prefix_len_spec(.,2) == new matcher` AND `prefix_len_spec(.,1) == old matcher`. |
| A5 | termination: `rlen == len(body)`, or `body[rlen] == 47`, or (`body[rlen] == 10` and `rlen == len(body) - 1`) | the trailing `(/|$)` | A-reference | the candidate run must be followed by `/` or a position where Python-`re` `$` matches — end-of-path OR immediately before a newline that is the path's final character; part of the deep regex model (mapping.md §4). |
| A6 | `Result()` = captured length `prefix_len_spec(path,2)` (`-1` if no match) | `regex_match` truthiness + `len(regex_match[1])` (`trans_real.py:508,511`) | R | the model returns the captured group-1 **length**; the captured *content* is `path[1:1+len]`. `-1` ⇔ `not regex_match` ⇔ `get_language_from_path` returns `None` (mapping.md §3). |
| A7 | (not modeled — composition) | `get_supported_language_variant(lang_code, strict)` resolving the extracted code (`trans_real.py:513`) | I | the resolver is **unchanged** by the patch; it is the identical concrete callee applied to the extracted code in both pre- and post-patch `get_language_from_path`. The only delta is which codes A6 extracts. See mapping.md §2. Not referenced from the spec view ⇒ no leakage, no over-claim. |

The discriminating content of the change — a candidate with **both a script and
a region sub-tag** (three word sub-tags, two separators, e.g. `en-latn-us`,
`de-ch-1901`, `nan-hani-tw`) — lives in `nsep(tag) <= 2` (model, A4) ⇔ the
`{0,2}` bound (real). The pre-patch budget 1 (`?`) rejects such a path outright
(`regex_match` is falsy ⇒ `get_language_from_path` returns `None`);
`model_prepatch.py` reproduces that (`tseps > 1`) and **fails** the postcondition
`Result() == prefix_len_spec(ToSeq(path), 2)`, which is exactly the spec sensing
the change (G-DIFF). A run with three-or-more separators (e.g.
`/de-simple-page-test/`) is rejected by BOTH budgets (`nsep > 2`), matching the
F2P expectation `None`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The one operation that
genuinely *changed* — the regex repeat bound — is modeled **deeply** (the
spelled-out structural parse `prefix_len_spec`, an **A-reference** validated by
G-AX), never hidden behind an axiom. The single consumed `@ContractOnly` axiom
(A0) is the per-code-point character-class test, which the change does **not**
touch: it is the same class before and after, and its contract is a partial one
(pinned below code point 128, open above) so that the structural claim is made
for every class the real, whole-of-Unicode one could be — not for an
ASCII-shaped guess at it. The only other callee in the patched function
(`get_supported_language_variant`) is **unchanged** and enters by composition as
an **I** step (mapping.md §2), so it is neither modeled nor axiomatized.

## C. verify(model) ⇒ resolved

`language_prefix_len` verifies only if its returned length equals the exact
structural parse with a budget of **two** separators (A3–A5) — i.e. only if a
script+region candidate IS extracted (length > 0) rather than rejected. By R
(`str` ↔ `List[int]`; length ↔ group-1 length; `-1` ↔ no-match ↔ `None`) and
by the **I** composition with the unchanged resolver (A7), the verified
extraction equals the gold `language_code_prefix_re.match(path)[1]` feeding
`get_supported_language_variant`; G-AX confirms the deep model
`prefix_len_spec(.,2)` equals the real post-patch matcher and
`prefix_len_spec(.,1)` the pre-patch matcher (A-reference, mapping.md §4) over
the WHOLE `Requires`-satisfying input domain — with `is_word` instantiated at its
real counterpart, so paths carrying code points at or above 128 are ordinary
probed inputs and not an excluded region — and it confirms the A0 contract is one
the real class satisfies. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement, the A0 axiom, and the
G-AX-audited deep reference — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: soundness of the consumed axiom and of
the deep reference (G-AX, no domain restriction) and refinement fidelity (this
document, G-EQ).
