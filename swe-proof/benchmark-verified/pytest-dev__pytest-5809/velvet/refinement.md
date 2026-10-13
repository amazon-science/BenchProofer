# refinement.md — pytest-dev__pytest-5809

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildUploadParams` `do` block and the `UploadParams` construction) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A legs** (no axiomatized callee; §C). Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The submitted-parameter site — `create_new_paste` (`src/_pytest/pastebin.py:80-84`)

Gold hunk:
```
-    params = {
-        "code": contents,
-        "lexer": "python3" if sys.version_info[0] >= 3 else "python",
-        "expiry": "1week",
-    }
+    params = {"code": contents, "lexer": "text", "expiry": "1week"}
```

| # | Solution.lean impl op (`buildUploadParams`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `contents : List Char` | `contents` arg of `create_new_paste` (bytes payload) | R | bytes payload ↔ `List Char` (mapping.md §2). G-CONF bridges via the `urlencode`→`parse_qs` round trip on the `code` field. |
| A2 | `out.code := contents` | `"code": contents` | I | the payload is carried through verbatim, unchanged by the patch; identity on both sides. |
| A3 | `out.lexer := "text".toList` | `"lexer": "text"` | I | the changed value: the syntax-highlighting language label is the generic plain-text constant `"text"`. Concrete literal on both sides (mapping.md §2). |
| A4 | `out.expiry := "1week".toList` | `"expiry": "1week"` | I | the retention-period label, a fixed constant; unchanged by the patch. |

Discriminating content of the change — `lexer = "text"` rather than the
version-dependent programming-language label (`"python3"` under Python 3) — lives
in `out.lexer = "text".toList`. The pre-patch construction used
`"python3" if sys.version_info[0] >= 3 else "python"`;
`Solution_prepatch.lean` reproduces that (the `"python3"` branch taken in this
image's Python 3 interpreter, the value the F2P test compared against
pre-patch) and **fails** the `out.lexer = "text".toList` clause (G-DIFF).

## B. The submitted dict shape

The submitted `params` dict has exactly the three keys `code`, `lexer`, `expiry`
at both base_commit and post-patch (only the `lexer` *value* changes). The
`UploadParams` structure carries exactly those three fields. The surrounding
`create_new_paste` operations the patch does **not** touch — the `url`, the
`urlopen` POST, and the response regex parse — are outside the modeled
construction; they are neither changed by the fix nor part of what the F2P
`lexer=` / `code=` / `expiry=` assertions discriminate. Modeling them would be
spec dilution, not strength.

## C. No axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no A-consumed axiom and no A-reference**: the
submitted mapping is assembled entirely from the input `contents` plus the two
fixed labels, delegating to no unchanged callee. The version test the pre-patch
performed (`sys.version_info[0] >= 3`) is a constant choice fully expressed by the
prepatch's concrete `"python3"` branch, not an opaque callee — so there is
nothing to axiomatize. (No-axiom precedent: django__django-11138 /
django__django-12304.) `axiom_check.py` is a skip; `conf_skip = false` (the impl
region is all R/I, so G-CONF runs).

## D. verify(Solution) ⇒ resolved

`buildUploadParams` verifies only if its result has `lexer = "text"` (A3),
`code = contents` (A2), and `expiry = "1week"` (A4). By R (`bytes ↔ List Char`,
literal ↔ `List Char`) the verified construction equals the gold patched `params`
dict on every payload. By G-CONF the R/I transliteration of the construction
agrees with `patch.diff`'s behaviour — the actual params `create_new_paste`
submits, captured from the mocked POST exactly as the F2P test inspects them —
on ≥10⁵ fuzzed payloads. The F2P test `test_create_new_paste` asserts
`lexer=text`, `code=full-paste-contents`, and `expiry=1week` appear in the
submitted body; a model satisfying this spec produces exactly those, so it
resolves (G-RESOLVE). There are no axiom trust points (no callee modeled); the
sole trust point is refinement fidelity (this doc, G-EQ + G-CONF).
