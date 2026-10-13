# refinement.md — sphinx-doc__sphinx-8475

The operation-by-operation correspondence between `model.py`'s implementation
(the `probe_outcome` impl region plus the deep `is_retryable` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/behaviour by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The patch edits the inner HEAD-then-GET fallback of `check_uri`
(`sphinx/builders/linkcheck.py`): it widens the retried-failure `except` clause
from `HTTPError` to `(HTTPError, TooManyRedirects)`, and adds the matching
import.

Gold hunks:
```
-from requests.exceptions import HTTPError
+from requests.exceptions import HTTPError, TooManyRedirects
...
                         response.raise_for_status()
-                    except HTTPError:
+                    except (HTTPError, TooManyRedirects):
                         # retry with GET request if that fails, some servers
                         # don't like HEAD requests.
                         response = requests.get(req_url, stream=True, ...)
                         response.raise_for_status()
```

## A. The HEAD→GET fallback slice — `check_uri` (`linkcheck.py:168-180`)

| # | model.py impl op (`probe_outcome`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `head_kind: int ∈ {0,1,2,3}` | the response-or-raised-condition of `response = requests.head(req_url, allow_redirects=True, ...); response.raise_for_status()` | R | the response/exception of the light (HEAD) probe is refined to its observable outcome KIND: 0=success, 1=`HTTPError`, 2=`TooManyRedirects`, 3=other request failure (mapping.md §2). The full request arguments are unchanged by the patch and irrelevant to the tested behaviour. |
| A2 | parameter `get_kind: int ∈ {0,1,2,3}` | the response-or-raised-condition of the fallback `response = requests.get(req_url, stream=True, ...); response.raise_for_status()` | R | same outcome-kind refinement for the full (GET) probe (mapping.md §2). |
| A3 | `if is_retryable(head_kind): result = get_kind` | `except (HTTPError, TooManyRedirects): response = requests.get(...); response.raise_for_status()` — the GET response/exception replaces the HEAD one | A-reference + R | the retried-failure classification is the **changed** operation, modelled **deeply**: `is_retryable(kind) == (kind∈{1,2})` (the `pure` region) IS the membership test of the `except (HTTPError, TooManyRedirects)` tuple — and is false for a success (kind 0), exactly as the `except` is not entered when `raise_for_status()` did not raise. There is no consumed axiom — the deep model is validated **== the real exception-matching semantics** out-of-band: G-AX (axiom_check.py) asserts over the whole `requests.exceptions` surface that `except (HTTPError, TooManyRedirects)` catches an exception ⟺ `is_retryable(classify_kind(exc))`, and that kinds 1/2 are disjoint (mapping.md §3.1). On retry, the effective outcome becomes the GET outcome (`result = get_kind`), exactly as the patch reassigns `response` to the GET response. |
| A4 | `else: result = head_kind` | the HEAD outcome standing: EITHER the HEAD `try` block completed without raising (kind 0 ⇒ `is_retryable` false ⇒ the HEAD response flows to the outer reporter), OR the HEAD `except` clause did NOT match a non-retryable failure (kind 3), so the exception propagates out of the inner block to the outer `try` | I + R | the two non-retried cases — a HEAD success (kind 0) and a non-retryable HEAD failure (kind 3) — both leave the HEAD outcome authoritative (`result = head_kind`). `is_retryable` is false on exactly these kinds, so the single `else` is the faithful refinement of "the `except` was not entered" (no exception) ⊕ "the `except` did not catch this exception" (non-retryable), both of which leave `response` / the propagating exception as the HEAD outcome. Identical control decision under the kind refinement. |

The discriminating content of the change — a `TooManyRedirects` light-probe
failure (kind 2) IS now retried with the full probe — lives in
`is_retryable(2) == True` (model) ⟺ the added `TooManyRedirects` member of the
`except` tuple (real). The pre-patch clause retried only `HTTPError` (kind 1);
`model_prepatch.py` reproduces that (`if head_kind == 1:`) and **fails** the
postcondition
`Implies(head_kind != 0 and is_retryable(head_kind), Result() == get_kind)`
for `head_kind == 2` (the verifier reports the failure on exactly this clause).
That is precisely the spec sensing the change (G-DIFF): for an infinite-
redirect-on-HEAD locator whose GET succeeds (`head_kind == 2, get_kind == 0`),
the post-patch effective outcome is success (kind 0 ⇒ "working") whereas the
pre-patch one is the un-retried `TooManyRedirects` failure (kind 2 ⇒ "broken"),
which is exactly the F2P test `test_TooManyRedirects_on_HEAD`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the
widening of the retried-failure classification from `HTTPError` to
`(HTTPError, TooManyRedirects)` — is modelled **directly** as the deep predicate
`is_retryable(kind) == (kind∈{1,2})` (A4, an **A-reference** validated by G-AX
against the real `except`-tuple semantics), NOT hidden behind a `@ContractOnly`
axiom about the function under change. There is **no consumed axiom** in this
bundle (the `axioms` region is empty) and therefore no dead axiom: the only
kind-A relationship is the A-reference of A4. The outcome-kind carriers (A1, A2)
and the two unchanged control decisions (A3, A5) are pure R / I.

## C. verify(model) ⇒ resolved

`probe_outcome` verifies only if (a) a successful light probe is the outcome
(A3), (b) a RETRYABLE light-probe failure — a status error (kind 1) OR an
unbounded-relocation failure (kind 2) — yields the FULL probe's outcome (A4),
and (c) a non-retryable failure (kind 3) is authoritative (A5). By R (the
response/exception ↔ outcome kind) the verified slice equals the gold
`except (HTTPError, TooManyRedirects): response = requests.get(...)` placed
around the unchanged HEAD/GET requests; by G-AX the real `except` tuple's match
set equals the deep model `is_retryable` (the A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to the
outcome-kind type refinement and the one audited classification — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
deep-model/axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
