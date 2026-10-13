# mapping.md — psf__requests-1921

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3c88e520da24ae6f736929a750876e7654accc3d`, states the type
abstraction, and (since the behaviour is modelled deeply) names the single
**A-reference**: the real operation the deep model is validated against by
`axiom_check.py` (G-AX). There are **no consumed axioms**.

Repo file under change: `requests/sessions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effective_collection(session, request, n)` | `merge_setting(request_setting, session_setting, dict_class=OrderedDict)` — `requests/sessions.py:34` (dict-merge branch, body lines 54-62; the patched drop added after line 60) | the modeled changed function (combine two key/value collections with precedence, then drop keys whose effective value is `None`) |
| `effective(sv, rv)` | `merged_setting = dict_class(to_key_val_list(session_setting)); merged_setting.update(to_key_val_list(request_setting))` (`sessions.py:54-55`) | pure spec: per-key precedence merge — the per-request value wins where present, else the per-session value |
| `combined(sv, rv)` *(deep model — A-reference)* | the full dict-merge branch INCLUDING the patched drop `merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)` (`sessions.py:62`, post-patch) | pure spec: the value the combined collection holds for a key — the effective value, except an effective value of `None` drops the key; validated `combined == real merge_setting` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `absent()` (`== 0`) | "key not present in this dict" / "key not carried into the result" | the absence sentinel |
| `none_val()` (`== -1`) | the explicit Python value `None` stored under a key (e.g. `session.headers['Accept-Encoding'] = None`) | the explicit unset value |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): the only None-drop at `base_commit` is
the loop

```python
for (k, v) in request_setting.items():
    if v is None:
        del merged_setting[k]
```

which inspects ONLY the per-request side, so a key carried only by
`session_setting` and set to `None` there survives in `merged_setting` still
holding `None`. The gold patch adds a final pass dropping EVERY key whose merged
value is `None`, regardless of which side contributed it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a dict / `CaseInsensitiveDict` of header (or other setting) key → value | `List[int]` indexed by key position: the key universe is the index set `0 .. n-1`, shared by both inputs and the output; position `k` holds the value for key `k` | dict key ↔ list index; "key not in dict" ↔ value `absent()` at that index; only membership and per-key value are observed by the F2P test (`'Accept-Encoding' not in prep.headers`), so integer-indexed positions are a faithful carrier |
| value `None` stored under a key | the integer `none_val()` (`-1`) | a value distinct from `absent()` so "explicitly set to None" is distinguishable from "never provided" — the distinction the behaviour turns on |
| an ordinary (non-None) setting value | any integer `>= 1` (any value `!= absent()` and `!= none_val()`) | identity on per-key value-identity; the F2P test only observes presence/absence, never value content |
| `to_key_val_list` (`requests/utils.py:144`) coercion of a Mapping to a list of `(k, v)` pairs | identity on the per-key value mapping | `to_key_val_list` is order/representation-only on a Mapping (`value.items()` → `list`); it does not change which key maps to which value (see G-AX, which drives the REAL `to_key_val_list`) |
| `dict_class` (= `OrderedDict`) construction + `.update` | the precedence merge `effective` | building from `session` then `.update(request)` makes the per-request value win on shared keys; ordering is unobserved by the tested behaviour |

String keys are banned from indexing in Nagini and are irrelevant to the tested
behaviour (only presence/absence of a key in the result is observed), so keys
are modelled as integer index positions.

## 3. Callee / operation provenance (A-reference — checked by G-AX)

### 3.1 `combined` deep model ↔ real `merge_setting` dict-merge branch (A-reference)
**Operation:** `requests.sessions.merge_setting`, dict-merge branch, POST-patch.
The changed combine-and-drop operation is modelled **deeply** by the `@Pure`
functions `effective` / `combined` (consumed by the verified loop in
`effective_collection`); there is **no `@ContractOnly` axiom** the proof consumes. The
deep model is instead validated equal to the real operation out-of-band by
`axiom_check.py` (G-AX), which drives the REAL repository code
(`merge_setting`, `to_key_val_list`, `OrderedDict.update`) in the evaluation
container.

Post-patch the dict branch computes, for every key `k` of the union of the two
collections:

  effective(k) = request[k] if k in request else session[k]   (request wins),
  result holds k ↦ effective(k)  unless effective(k) is None, in which case k is dropped,

i.e. exactly `combined(session[k], request[k])` with `none_val()` → `absent()`.
This holds regardless of which side supplied the `None` — the single
behavioural change the F2P test `test_headers_on_session_with_None_are_not_sent`
observes (a session-side `None` header must not be sent).

**PATCH-STATE control (load-bearing).** The SWE-bench image is checked out at
`base_commit` — the UNPATCHED tree, whose only None-drop inspects the
per-request side. `axiom_check.py` therefore does NOT trust the ambient
`merge_setting`'s drop; it exercises BOTH states at runtime by controlling only
the final drop line (the exact line the gold patch adds), reusing the real
`to_key_val_list` and `OrderedDict.update` for the precedence merge:
  * FIXED state (gold, self-applied): drop EVERY key whose merged value is
    `None`. The deep model `combined` must match here.
  * BUGGY state (base_commit): drop only keys whose PER-REQUEST value is `None`.
    A key carried only by `session` and set to `None` there must SURVIVE holding
    `None` — proving the observable discriminates fixed from buggy.
Exit 0 iff every observation matches the deep model in BOTH states. Imports: the
standard library plus the `requests` package under evaluation.

## G-CONF (differential conformance: MODEL vs REAL patched code)

`conformance_check.py` refutes the refinement leg no other gate covers — that the
model's impl region agrees with the real patched repository function.

**Shadow (provenance `direct`).** The model IS Python, so the impl region of
`effective_collection` (model.py lines 130-168) is copied VERBATIM with only the
contract statements (`Invariant`, `Assert`) and the `# invariants-start`/`-end`
markers deleted — the loop, the `old_result` bookkeeping and both branch tests
are byte-for-byte the model's. The `@Pure` helpers it depends on (`absent`,
`none_val`, `effective`, `combined`) copy over with `@Pure` stripped. There is no
`@ContractOnly` callee to stub (§3: the behaviour is modelled deeply, A-reference
only), so the whole modelled computation is under differential test. No
`PSeq`/`ToSeq` shim is needed — the carrier is `List[int]`.

**Oracle: CALLED, not transliterated.** `requests.sessions.merge_setting`
(`requests/sessions.py:34`, dict-merge branch) is imported and called; the gate
git-applies the gold patch and sets `PYTHONPATH` first, so the function under
test includes the added drop at `sessions.py:62`. Driving it needs nothing beyond
two mappings, so no transliteration is warranted. This also exercises the real
`to_key_val_list` (`requests/utils.py:144`) and `OrderedDict.update`, so the
§2 R-refinements about them are tested rather than assumed. Both arguments are
always real dicts, so only the dict-merge tail — the sole branch the patch
touches and the sole branch the model models — is ever taken.

**Bridge (§2, inverted).** `to_repo`: each `List[int]` becomes an `OrderedDict`
over keys `str(0..n-1)`, OMITTING positions equal to `absent()` (key genuinely
not in that dict) and storing the Python value `None` for `none_val()`; any other
integer is stored as itself. `from_repo` inverts it: a key missing from the
merged dict reads back as `absent()`, a key still mapping to `None` reads back as
`none_val()` — that is exactly the pre-patch bug shape, so it surfaces as a
disagreement rather than being normalised away. Result ordering is neither
modelled nor compared (§2: `dict_class` ordering is unobserved); the per-key
value mapping over `0 .. n-1` is.

**Inputs — 109921 total, all satisfying the Requires** (`0 <= n <= len(session)`,
`n <= len(request)`; the permission conjuncts are vacuous outside Nagini):
  * 16 boundary cases: empty universe; the exact F2P shape (a session-only key
    set to the unset value, which `test_headers_on_session_with_None_are_not_sent`
    pins and the pre-patch per-request-only drop leaves in place); each branch of
    the impl taken; `n == 0` and `n < len` with unequal list lengths, so
    positions outside the key universe are never read.
  * 69905 EXHAUSTIVE: because both sides decide each key independently of the
    others, the modelled decision space is the per-key class grid, and it is
    enumerated in full — all (session, request) pairs of every length 0..4 over
    the 4-class alphabet {absent, unset, real 1, real 7}
    (1 + 16 + 256 + 4096 + 65536). Every reachable combination of the impl's two
    branch tests across up to four keys is covered, not sampled; that is a
    stronger check than 1e5 random samples over the same space.
  * 40000 seeded fuzz over the same space with longer inputs (length <= 12), a
    wider real-value alphabet, and `n` often strictly below both list lengths.

**Pinned seed: `SEED = 1921`** (module constant), matching the velvet and lean
siblings.

**Falsifiability, checked out-of-band.** Against the UNPATCHED `merge_setting`
the script fails on its first boundary case (`session=[-1]`, `request=[0]`:
shadow `[0]` vs oracle `[-1]` — the session-only `None` survives), and
shadow-only mutants (reversed precedence, no unset-drop, off-by-one key
universe) each fail too. A green verdict here is therefore evidence, not a
tautology.

**Recorded verdict:** `G-CONF=pass` — 109921 inputs, 0 disagreements.
