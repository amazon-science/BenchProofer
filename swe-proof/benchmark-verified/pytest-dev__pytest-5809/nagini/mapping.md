# mapping.md — pytest-dev__pytest-5809

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8aba863a634f40560e25055d179220f0eefabe9a`, states the type
abstraction, and gives the provenance of the one deep-model reference.

Repo file under change: `src/_pytest/pastebin.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `paste_mode_field(py_major)` | the `"lexer"` value of the `params` dict in `create_new_paste(contents)` — `src/_pytest/pastebin.py:80-84` (the `"lexer": "python3" if sys.version_info[0] >= 3 else "python"` entry, body line 82) | the modeled changed expression: which highlighting-mode token the request carries |
| `paste_body_field(contents)` | the `"code"` value of the same `params` dict (`"code": contents`, line 81) | unchanged body field: forwards `contents` (identity) |
| `paste_expiry_field()` | the `"expiry"` value of the same `params` dict (`"expiry": "1week"`, line 83) | unchanged expiry field: the fixed `"1week"` token |
| `text_token()` | the post-patch `"text"` literal (the value the mode field must carry) | pure spec: the plain-text mode token as code points |
| `expiry_token()` | the `"1week"` literal (`src/_pytest/pastebin.py:83`) | pure spec: the expiry token as code points |

`py_major` models `sys.version_info[0]` (the running interpreter major version)
— the value the pre-patch expression branches on. The post-patch value does NOT
depend on it; the postcondition holds for every `py_major`, which is exactly
what makes the value version-invariant.

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the conditional
`"python3" if sys.version_info[0] >= 3 else "python"`
(`src/_pytest/pastebin.py:82`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the dict values `"text"`, `"1week"`, and `contents`) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; element-wise / length / equality mirror `str` |
| `contents` (bytes in the F2P test; `str`/bytes session log in production) | `List[int]` of code/byte points | the body field forwards it unchanged; `urlencode` percent-quotes it identically whether the payload models bytes or str for the ASCII test body |
| the 3-key `params` dict | three independent modeled field-producing functions | the dict has exactly three entries (`code`, `lexer`, `expiry`); only the `lexer` value changed, so each entry is modeled by its own function and the changed one (`paste_mode_field`) is the differential carrier |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: every modeled value is a concrete
constant token (`paste_mode_field`/`paste_expiry_field`) or the identity on the
input (`paste_body_field`), all modeled deeply.

### 3.1 token constants ↔ `urllib.parse.urlencode` (A-reference)
**Callee:** CPython `urllib.parse.urlencode(params)` followed by
`.encode("ascii").decode()` — the UNCHANGED serializer `create_new_paste` calls
on the `params` dict (`src/_pytest/pastebin.py:86`). The modeled constant tokens
are validated against it: with the post-patch `params = {"code": contents,
"lexer": "text", "expiry": "1week"}`, the serialized wire form contains

  `lexer=text`, `expiry=1week`, `code=<contents>`

and never `lexer=python…`. This is exactly the form the FAIL_TO_PASS test
`testing/test_pastebin.py::TestPaste::test_create_new_paste` asserts
(`assert "lexer=text" in data.decode()`), and `urlencode` does not consult
`sys.version_info`, so the mode field is invariant under interpreter version.
Docs: https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlencode.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`urllib.parse.urlencode` on the gold patch's `params` dict over 3 interpreter-
major-version witnesses and 20 000+ body inputs, asserting `lexer=text`,
`expiry=1week`, and the percent-quoted `code` appear in the payload (and
`lexer=python` never does). stdlib-only (`urllib.parse`, `random`); exit 0 iff
sound.
