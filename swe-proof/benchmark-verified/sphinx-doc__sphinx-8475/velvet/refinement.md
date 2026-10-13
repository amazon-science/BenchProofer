# refinement.md — sphinx-doc__sphinx-8475

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveLinkStatus` `do` block, the deep `retriable` / `classifyReached` /
`classifyUnhandled` models, and the `RequestFailure` failure hierarchy) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(modeled callee — **A-consumed** where the proof uses an axiom's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs would be mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); here the impl region's only observable is a live-network side effect with
no DB-/network-free R/I shadow, so **G-CONF is `status="skip"` (`conf_skip=true`)**
and the A-reference legs are carried entirely by **G-AX**; the narrative is
audited by **G-EQ**. Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dispatch site — `check_uri()` (`sphinx/builders/linkcheck.py:168–204`)

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

| # | Solution.lean impl op (`resolveLinkStatus`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `headProbe : Probe` | the first attempt: `requests.head(...).raise_for_status()` (`linkcheck.py:170–174`) | R | a returned response ↔ `.reached b` (`b = url-equality`); a raised exception ↔ `.failed (classifyEx ex)` (mapping.md §2). |
| A2 | `getProbe : Probe` | the fallback attempt: `requests.get(...).raise_for_status()` (`linkcheck.py:178–180`) | R | same bijection as A1; consulted only on the retry leg. |
| A3 | `match headProbe with \| .reached b => classifyReached b` | first attempt succeeded → fall through to `if response.url… == req_url…` (`linkcheck.py:192–204`) | I | `classifyReached` is the concrete `working`/`redirected` decision on URL equality (mapping.md §1). |
| A4 | `\| .failed e => if retriable e then …` | the **inner** `except (HTTPError, TooManyRedirects):` clause (`linkcheck.py:175`, post-patch) | **I (the changed op)** | `retriable e = isinstance(ex, (HTTPError, TooManyRedirects))`. This is the operation the patch changes — modeled deeply, not axiomatized. Pre-patch the set is `(HTTPError,)` only; the prepatch reproduces that (`retriable .redirectLoop = false`). |
| A5 | retry leg: `match getProbe with \| .reached b => classifyReached b \| .failed e2 => classifyUnhandled e2` | the GET attempt and, if it too raises, fall-through to the top-level handler (`linkcheck.py:178–191`) | I | the fallback's response is classified like A3; a fallback failure reaches the top-level handler (A6). |
| A6 | `else classifyUnhandled e` and the `.failed e2` leg | the top-level `except HTTPError as err: … / except Exception as err: return 'broken', …` (`linkcheck.py:181–191`) | A-reference + I | `classifyUnhandled` is the deep model of the top-level handler's status reading: `HTTPError` 401→working, 503→ignored, else broken; `TooManyRedirects`/other → broken. The equality of this model to the real handler's behaviour over the failure hierarchy is the **A-reference** G-AX validates (mapping.md §3.1); the dispatch ops are **I**. |

Discriminating content of the change — a redirect-budget exhaustion on the first
attempt is now retried with a full fetch (A4). This lives in
`retriable .redirectLoop = true` (model) ⇔ `TooManyRedirects ∈ (HTTPError,
TooManyRedirects)` (real). The pre-patch inner clause was `except HTTPError`, and
`TooManyRedirects` is **not** a subclass of `HTTPError` (mapping.md §3.1), so the
failure escaped the retry and reached `except Exception → 'broken'`.
`Solution_prepatch.lean` reproduces that (`retriable .redirectLoop = false`) and
**fails** `out = resolveLinkStatusSpec headProbe getProbe` on a
`.failed .redirectLoop` first probe whose full fetch reaches the target
(`.working` in the spec, `.broken` in the prepatch) — exactly the
`broken`-vs-`working` outcome the F2P `test_TooManyRedirects_on_HEAD` observes
(its `do_HEAD` infinitely redirects, its `do_GET` returns 200; the link must be
reported `working`). (G-DIFF.)

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation the patch changes — the inner exception
catch-set — is modeled **deeply** (`retriable`, step A4, an I op over the
`RequestFailure` hierarchy), not hidden behind an axiom about the function under
change. The unchanged callees (the `requests` exception classes + `isinstance`
dispatch, and the top-level handler's status reading) are an **A-reference** (deep
models `RequestFailure` / `classifyUnhandled`, G-AX-validated), not consumed
axioms; there are no consumed axioms, and nothing about the function under change
is axiomatized.

## C. verify(Solution) ⇒ resolved

`resolveLinkStatus` verifies only if its output equals `resolveLinkStatusSpec`:
a first attempt that exhausts the redirect budget (`.failed .redirectLoop`) is
retried (`retriable .redirectLoop = true`, A4), and a successful full fetch is
reported `working` (A5 + `classifyReached true`). By R (the `Probe` bijection of
A1/A2, the `LinkStatus` bijection) the verified dispatch equals the patched
`check_uri` control flow on the tested outcomes; by G-AX the deep models
`RequestFailure`/`retriable`/`classifyUnhandled` equal the real `requests`
exception hierarchy + `isinstance` dispatch + top-level handler (A-reference).
G-CONF is `skip` here (conf_skip=true, §4.1 / mapping.md §4): the only observable
is the live-network status of a link, with no network-free R/I shadow, so the
A-reference legs rest on G-AX and spec-tightness on G-VERIFY + G-DIFF + G-MUT.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited hierarchy — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this doc, G-EQ; G-CONF
skipped, so G-EQ + G-AX carry the cross-language leg).
