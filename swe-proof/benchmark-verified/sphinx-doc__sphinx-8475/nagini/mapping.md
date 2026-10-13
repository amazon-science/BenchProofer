# mapping.md — sphinx-doc__sphinx-8475

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3ea1ec84cc610f7a9f4f6b354e264565254923ff`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
exception-matching semantics the deep model is validated against by G-AX).

Repo file under change: `sphinx/builders/linkcheck.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `probe_outcome(head_kind, get_kind)` | the inner HEAD-then-GET fallback block of `CheckExternalLinksBuilder.check_thread.check_uri` — `sphinx/builders/linkcheck.py:168-180` | the modeled changed control-flow slice (light-probe → full-probe fallback) |
| `is_retryable(kind)` *(deep model — A-reference)* | the retried-failure `except` clause `except (HTTPError, TooManyRedirects):` — `sphinx/builders/linkcheck.py:175` (post-patch) | pure spec: which light-probe failure kinds are retried with the full probe; the deep model of the exception-matching classification, validated `is_retryable == (the real except tuple catches it)` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo symbol the change widens (for the refinement audit, not
referenced from the consumer spec view): the original `except HTTPError:`
(`linkcheck.py:175` pre-patch) and the import `from requests.exceptions import
HTTPError` (`linkcheck.py:23` pre-patch), broadened by the patch to
`from requests.exceptions import HTTPError, TooManyRedirects`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the response-or-raised-condition of `requests.head(...); response.raise_for_status()` | `head_kind: int ∈ {0,1,2,3}` | 0 ↔ HEAD returned and `raise_for_status()` did not raise (success); 1 ↔ an `HTTPError` was raised (`raise_for_status()` on a 4xx/5xx); 2 ↔ a `TooManyRedirects` was raised (`allow_redirects=True` bounced through an unbounded relocation chain); 3 ↔ any other request failure was raised |
| the response-or-raised-condition of `requests.get(...); response.raise_for_status()` | `get_kind: int ∈ {0,1,2,3}` | same encoding as `head_kind`, for the full-probe (GET) form |
| the effective response/exception the OUTER reporter then observes (`linkcheck.py:181-203`) | `Result(): int ∈ {0,1,2,3}` | the outcome kind that flows out of the inner HEAD/GET block: a successful response (kind 0 ⇒ reporter records "working"), or a raised condition (kinds 1/2/3 ⇒ caught by the outer handler) |
| `except (HTTPError, TooManyRedirects):` matches the raised condition | `is_retryable(kind)` truthy | the `except` tuple catches an exception ⟺ it is an instance of `HTTPError` (kind 1) or `TooManyRedirects` (kind 2); both are `requests.exceptions.RequestException` subclasses and `TooManyRedirects` is NOT a subclass of `HTTPError` (verified in axiom_check.py), so kinds 1 and 2 are disjoint and the tuple ⟺ `kind ∈ {1,2}` ⟺ `is_retryable(kind)` |

The HEAD/GET request arguments (`req_url`, `stream`, `config`, `auth_info`,
`**kwargs`) are unchanged by the patch and irrelevant to the tested behaviour;
they are abstracted into the single observable `head_kind` / `get_kind` outcome
of each probe form. `requests.head(..., allow_redirects=True)` is the source of
the kind-2 (`TooManyRedirects`) failure: the HEAD form follows redirects and a
server that loops on HEAD raises `TooManyRedirects`, whereas the GET form on
the same server resolves (kind 0).

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `is_retryable` deep model ↔ `except (HTTPError, TooManyRedirects)`
**Real behaviour:** Python's `except (HTTPError, TooManyRedirects):` catches a
raised exception iff it is an instance of one of the two named classes. The
patch widens the retried-failure clause from the single class `HTTPError` to
the tuple `(HTTPError, TooManyRedirects)`; both classes are imported from the
third-party `requests.exceptions` module (`requests/exceptions.py`).

The changed retried-failure classification is modelled **deeply** by the
`@Pure` predicate `is_retryable(kind) == (kind == 1 or kind == 2)` in the
`pure` region; there is **no `@ContractOnly` axiom** the proof consumes. The
deep model is validated equal to the real exception-matching behaviour
out-of-band by axiom_check.py (G-AX):

- `TooManyRedirects` is NOT a subclass of `HTTPError` and vice-versa — so the
  two retried kinds (1 and 2) are produced by disjoint exception classes, and
  kind 2 (the newly-retried one) was genuinely NOT caught by the pre-patch
  `except HTTPError`. (This is precisely why the issue's infinite-redirect-on-
  HEAD scenario was reported broken before the fix.)
- Both `HTTPError` and `TooManyRedirects` ARE subclasses of `RequestException`
  (the failure surface), so the tuple catches exactly kinds {1, 2}.
- Every other request failure class (`ConnectionError`, `Timeout`, `SSLError`,
  `ProxyError`, `ChunkedEncodingError`, `InvalidURL`, … — kind 3) is NOT caught
  by the tuple, so a kind-3 failure is authoritative and not retried.

`axiom_check.py` asserts, over the full `requests.exceptions` failure surface,
that `(the real except tuple catches exc) == is_retryable(classify_kind(exc))`,
that kinds 1 and 2 are disjoint, and (differentially) that the pre-patch
`except HTTPError` does NOT catch a kind-2 failure. It imports only
`requests.exceptions` (the very module the patch imports the two classes from);
nothing repo-specific. Exit 0 iff sound.

The `allow_redirects=True` flag dependency of the HEAD request (the reason a
kind-2 `TooManyRedirects` can arise at all) is recorded here so G-AX fuzzes the
right configuration: the model's kind-2 corresponds to a HEAD request issued
with redirect-following enabled.
