# mapping.md — pytest-dev__pytest-5809

## Instance
- repo: pytest-dev/pytest
- base_commit: 8aba863a634f40560e25055d179220f0eefabe9a
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch rewrites the `params` dictionary literal built inside
`create_new_paste` (`src/_pytest/pastebin.py:80-84` @ base_commit) before it is
URL-encoded and posted to the paste service:

```python
# @ base_commit (pre-patch)
params = {
    "code": contents,
    "lexer": "python3" if sys.version_info[0] >= 3 else "python",
    "expiry": "1week",
}
# post-patch
params = {"code": contents, "lexer": "text", "expiry": "1week"}
```

The only observable change is the value bound to the `"lexer"` key: the captured
terminal output is arbitrary console text, not Python source, so the syntax
highlighter requested goes from `"python3"` (on Python 3; `"python"` on legacy
Python 2) to the language-neutral `"text"`. The `"code"` and `"expiry"` entries
are unchanged. The encoded body is then `urlencode(params)`; the FAIL_TO_PASS
test `test_create_new_paste` asserts `"lexer=text"` (and `"code=..."`,
`"expiry=1week"`) appear in the encoded request body.

## Modeled function
I model the **parameter-mapping construction** — the `params` dict that
`create_new_paste` assembles and hands to `urlencode` — as a total function of
the caller-supplied `contents`. This is the smallest unit whose observable
behavior the patch changes and the F2P test pins. The surrounding I/O
(`urlencode`, `urlopen`, the response regex) is unchanged by the patch and is not
modeled: the test reads the parameters out of the encoded body, so pinning the
mapping pins the observable behavior.

The runtime `contents` is utf-8 bytes; the test passes `b"full-paste-contents"`
and reads `code=full-paste-contents` back. I model `contents` as a Lean `String`
(the value-level payload); the `code` entry carries it verbatim, exactly as the
test requires (`urlencode` is identity on the key/value text for this purpose).

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_buildPasteParams` | the `params = {...}` mapping literal assembled in `create_new_paste` (`src/_pytest/pastebin.py:80-84`) |
| `problem_spec_buildPasteParams` | the post-condition the assembled mapping must satisfy |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `contents : String` | the `contents` argument (utf-8 bytes) carried into `params["code"]` | value-level identity; the test exercises the ascii payload `b"full-paste-contents"` |
| `result : List (String × String)` | the `params` dict as an ordered list of `(key, value)` pairs | Python ≥3.7 dict preserves insertion order; the three entries map to the three pairs in order |
| `("code", contents)` | `"code": contents` | unchanged entry |
| `("lexer", "text")` | `"lexer": "text"` | the changed entry (post-patch value) |
| `("expiry", "1week")` | `"expiry": "1week"` | unchanged entry |

## Callee provenance / flag deps
- No unchanged repo callee is consumed. The mapping is built from string
  literals plus the verbatim `contents`; there is no `opaque` callee and no
  `axiom <callee>_prop`. The `axioms` region is empty and `axiom_check.py` is a
  skip stub.
- Pre-patch flag dependency: the pre-patch lexer value branches on
  `sys.version_info[0] >= 3` (`"python3"` vs `"python"`). The post-patch value
  `"text"` is constant and version-independent; the modeled (post-patch) behavior
  has no flag dependency. G-CONF runs in-container under Python 3, where the
  pre-patch value would have been `"python3"`.

## G-CONF fuzz seed
- pinned seed: `5809`
- ≥10^5 fuzzed `contents` strings (empty, ascii, the F2P payload, and random
  printable/utf-8 text); the shadow vs. the real patched `create_new_paste`
  parameter mapping are compared after a stub of `urlopen` captures the encoded
  body (the I/O is mocked exactly as the F2P test mocks it).
