# mapping.md — pytest-dev__pytest-5809

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8aba863a634f40560e25055d179220f0eefabe9a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change (gold patch.diff): `src/_pytest/pastebin.py`.

The modeled site is `create_new_paste`'s construction of the parameter mapping
submitted to the external paste service — the single line the problem statement
cites as the cause of the HTTP 400 errors (the syntax-highlighting language
label). It carries the complete discriminating logic of the fix in a single,
self-contained, pure data construction (see §3).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildUploadParams (contents : List Char)` | the `params = {…}` construction inside `create_new_paste(contents)` — `src/_pytest/pastebin.py:80-84` (body of `create_new_paste`, defined at line 64) | the modeled changed function step (assembles the submitted parameter mapping) |
| `UploadParams` (pure structure) | the `params` `dict` submitted via `urlencode(params)` — `src/_pytest/pastebin.py:80` | pure spec: the three submitted fields `code` / `lexer` / `expiry` |
| `contents` (param) | `contents` arg of `create_new_paste` (utf-8 encoded bytes payload) | the uploaded payload |
| `out.code` | `params["code"]` | the payload, carried through verbatim |
| `out.lexer` | `params["lexer"]` | the syntax-highlighting language label |
| `out.expiry` | `params["expiry"]` | the retention-period label |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): the version-dependent label
`"python3" if sys.version_info[0] >= 3 else "python"` at `pastebin.py:82`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `contents : bytes` (the payload) | `List Char` | each byte/character of the payload ↔ one `Char`; the payload is carried verbatim, so identity on contents; G-CONF bridges via the urlencode→parse_qs round trip that `urlencode(params)` performs (the `code` field round-trips to its text form). |
| the string literal `"text"` (`params["lexer"]` post-patch) | `"text".toList : List Char` | string literal ↔ its `List Char`; equality of labels ↔ `=` on `List Char` |
| the string literal `"1week"` (`params["expiry"]`) | `"1week".toList : List Char` | string literal ↔ its `List Char` |
| the `params` `dict` `{"code":…, "lexer":…, "expiry":…}` | `UploadParams { code, lexer, expiry }` | the three submitted entries ↔ the three structure fields; the dict has exactly these keys (mapping.md §3.1) |

The submitted dict has exactly three keys (`code`, `lexer`, `expiry`) at both
base_commit and post-patch; only the *value* of `lexer` changes. The
`UploadParams` structure carries exactly these three observed fields. The `url`,
the network POST, and the response parsing in `create_new_paste` are unchanged by
the patch and are not part of the modeled construction (they are not what the
fix touches and not what the F2P test's `lexer=` / `code=` / `expiry=`
assertions discriminate).

## 3. Callee provenance & multi-site handling

### 3.1 No axioms — fully deep model (band: pure-data)
`buildUploadParams` calls NO unchanged callee inside the modeled construction:
the result is computed entirely from the single input `contents` plus the two
fixed literal labels. The pre-patch `sys.version_info[0] >= 3` test and the
ternary are transliterated R/I ops (a constant choice that resolves to the
specific programming-language label), not delegated behaviour. Hence
**`deep_model_references = []`, `axioms = []`**, and `axiom_check.py` is a
**skip** (G-AX = skip — the django__django-11138 / django__django-12304 no-axiom
precedent). There is no flag dependency in the *post-patch* construction: the
fix replaces the version-dependent label with the unconditional constant
`"text"`, so the modeled value depends on nothing but being the plain-text label.

### 3.2 No additional change sites
The gold patch.diff changes exactly one site: the `params` construction in
`create_new_paste`. There is no second modeled function and no
`Solution_prepatch_<k>.lean` beyond the single one.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`5809`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the `UploadParams` construction (R/I-tagged ops) to Python and
runs the *patched* real `_pytest.pastebin.create_new_paste` as the oracle, with
`urllib.request.urlopen` mocked exactly as `testing/test_pastebin.py` mocks it,
capturing the urlencoded POST body and parsing it back into the submitted params
mapping (the observable the F2P test inspects). There is no A-tagged callee to
leave un-substituted — this bundle has none.
