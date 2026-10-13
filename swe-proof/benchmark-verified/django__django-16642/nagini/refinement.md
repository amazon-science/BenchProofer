# refinement.md — django__django-16642

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_content_type` impl region and the pure `resolved_type` /
`dedicated_type` / `is_known_encoding` model) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed** and **A-reference**), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The table-lookup site — `FileResponse.set_headers` (`django/http/response.py:611-615`)

Gold hunk (the dict gains two keys):
```
  content_type = {
+     "br": "application/x-brotli",
      "bzip2": "application/x-bzip",
+     "compress": "application/x-compress",
      "gzip": "application/gzip",
      "xz": "application/x-xz",
  }.get(encoding, content_type)
```

| # | model.py impl op (`select_content_type`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `encoding: List[int]` | `encoding` (2nd element of `mimetypes.guess_type(filename)`, a `str` or `None`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). `None` (no encoding detected) ↔ the empty list `[]`, which is `is_known_encoding == False`, matching `dict.get(None, content_type) == content_type`. |
| A2 | parameter `content_type: List[int]` | `content_type` (1st element of `guess_type`, the lookup default) | R | same code-point bijection; this is the `.get(encoding, content_type)` default. |
| A3 | the branch chain `if enc == tok_br(): return ct_brotli(); … ; if enc == tok_xz(): return ct_xz()` and the literal token/value sequences | the dict literal `{"br":"application/x-brotli", "bzip2":"application/x-bzip", "compress":"application/x-compress", "gzip":"application/gzip", "xz":"application/x-xz"}` | I + R | a `dict` literal keyed by five DISTINCT string literals, consumed only through `.get`, is observationally a finite case split on key equality. The model spells that split out (I: same control/data flow — five literal keys mapped to five literal values, in the same order), under the `str`↔`List[int]` code-point refinement (R) for each key and value. The five `tok_*` / `ct_*` byte sequences are the exact code points of the five keys / values (verified byte-for-byte in axiom_check.py). |
| A4 | the passthrough loop returning a copy of `content_type` (taken when no `tok_*` branch matched) | the `, content_type` default of `.get` | I + R | when `encoding` is not one of the five keys, `dict.get` returns the default `content_type`; the model returns a copy of `content_type`. `ToSeq(result) == ToSeq(content_type)` (proved by the loop invariant), so the returned value is character-identical. |

The discriminating content of the change — the two NEW keys `"br"` and
`"compress"` — lives in the `tok_br()`/`tok_compress()` branches (model) ⇔ the
`"br": …` and `"compress": …` dict entries (real). The pre-patch dict lacked
both keys; `model_prepatch.py` reproduces that (drops the `tok_br` and
`tok_compress` branches, so they fall through to the `content_type` passthrough)
and **fails** the postcondition
`ToSeq(Result()) == resolved_type(ToSeq(content_type), ToSeq(encoding))`
— exactly the spec sensing the change (G-DIFF, fails at model_prepatch.py:160).

## B. The unchanged producer — `mimetypes.guess_type`

The line `content_type, encoding = mimetypes.guess_type(filename)`
(`response.py:608`) is **unchanged** by the patch and is **not** part of the
modeled operation. The model receives `(content_type, encoding)` as inputs; this
is an R-refinement of "the pair the unchanged `guess_type` produced". There is
no axiom for it: it is neither changed nor consumed inside any `Ensures`. (Its
documented behaviour for the regressing inputs — `("text/html","br")` for
`*.br`, `("text/html","compress")` for `*.Z` — is recorded in mapping.md §3.1 as
context for why the F2P test observes the change, not as a contract the proof
relies on.)

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — the
two added rows of the compression-scheme table — is modeled **directly** (the
literal `tok_br`/`tok_compress` branches and their dedicated content-type
values), fully expressible in Nagini over `List[int]`/`PSeq[int]`. There is **no
consumed axiom** (no `@ContractOnly`) and **no A-reference deep model**: the
changed operation is a finite literal table, not an opaque callee. `dict.get`
is modeled as the case split it denotes for distinct literal keys (step A3/A4),
not axiomatized.

## D. verify(model) ⇒ resolved

`select_content_type` verifies only if, for each of the five recognised schemes,
its output equals that scheme's dedicated content type (the five `Implies`
postconditions, of which `br` and `compress` are the newly-added behaviour), and
for any other encoding its output equals the guessed `content_type` (the
passthrough clause), and the whole result equals `resolved_type` (the lookup).
By R (str ↔ List[int]; `dict.get`-as-case-split) the verified function equals the
post-patch `{…}.get(encoding, content_type)` expression on the tested inputs. The
F2P `test_compressed_response` (extended with `.tar.br → application/x-brotli`
and `.tar.Z → application/x-compress`) compares exactly these `Content-Type`
strings; the P2P set re-checks the three pre-existing schemes (`gzip`, `bzip2`,
`xz`) and the non-compressed paths, all preserved by the unchanged branches and
the passthrough. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom/deep-model trust points to carry (PLAN §1.1):
the only trust point is refinement fidelity (this document, G-EQ).
