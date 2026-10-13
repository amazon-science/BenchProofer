# refinement.md — pytest-dev__pytest-5809

Maps every operation in `implementation_buildPasteParams` to its `patch.diff`
counterpart. The patch rewrites the `params` mapping literal in
`create_new_paste`; the observable behavior it changes is the value bound to the
`"lexer"` key (see mapping.md). Tags: **R** type-refinement, **A-consumed** proof
uses a callee axiom, **A-reference** deep-modeled changed op validated == real
callee, **I** identical concrete op.

## Patch (post-patch)
```python
# src/_pytest/pastebin.py, inside create_new_paste(contents)
params = {"code": contents, "lexer": "text", "expiry": "1week"}
```

## Operation correspondence
| # | Lean op (`implementation_buildPasteParams`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut params : List (String × String) := []` | start assembling the `params` dict | I | empty accumulator; the dict is built up entry-by-entry (ordered). |
| 2 | `params := params ++ [("code", contents)]` | `"code": contents` | R | `String ↔ str/utf-8 payload`; the entry carries `contents` verbatim. Unchanged by the patch. |
| 3 | `params := params ++ [("lexer", "text")]` | `"lexer": "text"` | I | THE changed entry: post-patch the value is the literal `"text"`. Prepatch uses `"python3"` (the version-dependent Python-source highlighter). |
| 4 | `params := params ++ [("expiry", "1week")]` | `"expiry": "1week"` | I | unchanged entry. |
| 5 | `return params` | the assembled `params` handed to `urlencode` | I | the mapping value is the observable; the downstream `urlencode`/`urlopen`/regex are unchanged and not modeled. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the real patched `create_new_paste` parameter mapping
(captured by stubbing `urlopen`, exactly as the F2P test does) over ≥10^5 fuzzed
`contents` inputs. `conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` builds the `"lexer"` entry with value `"python3"` (the
literal pre-patch highlighter on Python 3) instead of `"text"`. The spec's clause
`result = [("code", contents), ("lexer", "text"), ("expiry", "1week")]` then fails
on the `"lexer"` pair, so the carried gold proof (`rfl`) does not typecheck —
precisely the behavior the FAIL_TO_PASS test `test_create_new_paste` asserts
(the encoded body must contain `lexer=text`, not `lexer=python3`). The spec is
byte-identical between the two files (only the impl's lexer literal differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the `params` literal rewrite in
`src/_pytest/pastebin.py`); it applies at `base_commit` and the harness resolves.
