# mapping.md — psf__requests-1921

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3c88e520da24ae6f736929a750876e7654accc3d`, states the type
abstraction, and (since the behaviour is modeled deeply) names the single
**A-reference**: the real operation the deep model is validated against by
`conformance_check.py` (G-CONF) and `axiom_check`-style execution (G-AX). There
are **no consumed axioms**.

Repo file under change: `requests/sessions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effectiveCollection session request` | `merge_setting(request_setting, session_setting, dict_class=OrderedDict)` — `requests/sessions.py:34` (dict-merge branch, body lines 54-62; the patched drop added after line 60) | the modeled changed function: combine two per-key value collections with precedence, then drop keys whose effective value is the unset value |
| `effective sv rv` | the per-session collection overlaid by the per-request collection so the per-request value wins on shared keys (`sessions.py:54-55`) | pure spec: per-key precedence merge — the per-request value wins where present, else the per-session value |
| `combined sv rv` *(deep model — A-reference)* | the full dict-merge branch INCLUDING the patched drop `merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)` (`sessions.py:62`, post-patch) | pure spec: the value the combined collection holds for a key — the effective value, except an effective value equal to the unset value drops the key; validated `combined == real op` by `conformance_check.py` (G-CONF), NOT consumed as an axiom |
| `combinedSeq session request` | the element-wise application of the combine-and-drop over the shared key universe | pure spec: the whole combined collection |
| `absent` (`= 0`) | "key not present in this dict" / "key not carried into the result" | the absence sentinel |
| `noneVal` (`= -1`) | the explicit unset value a caller may store under a key (e.g. setting a standing header to the absent-of-value sentinel) | the explicit unset value |

The pre-image behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): the only unset-drop at `base_commit`
inspects ONLY the per-request side, so a key carried only by the per-session
collection and set to the unset value there survives in the merged result still
holding the unset value. The gold patch adds a final pass dropping EVERY key
whose merged value is the unset value, regardless of which side contributed it.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a dict / case-insensitive dict of setting key → value | `List Int` indexed by key position: the key universe is the index set `0 .. n-1`, shared by both inputs and the output; position `k` holds the value for key `k` | dict key ↔ list index; "key not in dict" ↔ value `absent` at that index; only membership and per-key value are observed by the tested behaviour (a dropped key must be absent), so integer-indexed positions are a faithful carrier |
| the explicit unset value stored under a key | the integer `noneVal` (`-1`) | a value distinct from `absent` so "explicitly set to the unset value" is distinguishable from "never provided" — the distinction the behaviour turns on |
| an ordinary (real) setting value | any integer `≥ 1` (any value `≠ absent` and `≠ noneVal`) | identity on per-key value-identity; the tested behaviour observes only presence/absence of the key, never the value content |
| the order/representation coercions applied to a Mapping on the way into the merge | identity on the per-key value mapping | order/representation-only; they do not change which key maps to which value (G-CONF drives the REAL coercions) |
| the per-session-then-per-request overlay (precedence merge) | `effective` | overlaying the per-request collection makes the per-request value win on shared keys; ordering is unobserved by the tested behaviour |

String keys are irrelevant to the tested behaviour (only presence/absence of a
key in the result is observed), so keys are modelled as integer index positions.

## 3. Callee / operation provenance (A-reference — checked by G-CONF / G-AX)

### 3.1 `combined` deep model ↔ real combine-and-drop (A-reference)
**Operation:** `requests.sessions.merge_setting`, dict-merge branch, POST-patch.
The changed combine-and-drop op is modeled **deeply** by `effective` /
`combined` / `combinedSeq` (consumed by the verified loop in
`effectiveCollection`); there is **no axiom** the proof consumes. The deep model
is instead validated equal to the real operation out-of-band by
`conformance_check.py` (G-CONF), which drives the REAL repository code
(`merge_setting`) in the evaluation container.

Post-patch the dict branch computes, for every key `k` of the union of the two
collections:

  effective(k) = request[k] if k carried by request else session[k]   (request wins),
  result holds k ↦ effective(k)  unless effective(k) is the unset value, in
  which case k is dropped,

i.e. exactly `combined session[k] request[k]` with `noneVal` → `absent`. This
holds regardless of which side supplied the unset value — the single
behavioural change the F2P test `test_headers_on_session_with_None_are_not_sent`
observes (a per-session-side unset header must not be carried into the prepared
request).

**Comparison key.** `conformance_check.py` lifts the integer carrier back to the
real dicts (`absent` → key omitted; `noneVal` → the explicit unset value; any
other int → itself), drives the REAL `merge_setting`, and compares its per-key
result mapping to the deep model `combinedSeq` over `100_000` fuzzed inputs plus
the boundary cases (session-only unset, request-only unset, both unset, override
of an unset value, both ordinary). Exit 0 iff every observation matches.

## 4. Determinism

`conformance_check.py` pins the fuzz seed (`SEED = 1921`) so the G-CONF verdict
is reproducible.
