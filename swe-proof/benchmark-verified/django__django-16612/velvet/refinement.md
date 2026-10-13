# refinement.md — django__django-16612

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `appendSlashRedirect` `do` block and the deep `redirectTarget` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The redirect-destination change — `catch_all_view` (`django/contrib/admin/sites.py:456`)

Gold hunk:
```
- return HttpResponsePermanentRedirect("%s/" % request.path)
+ return HttpResponsePermanentRedirect(
+     request.get_full_path(force_append_slash=True)
+ )
```

| # | Solution.lean impl op (`appendSlashRedirect`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `encodedPath : List Char` | `request.path`, fed through `escape_uri_path` inside `get_full_path` | R | the **output** of the unchanged path encoder is the carrier: `escape_uri_path(request.path)` (str) ↔ `encodedPath` (List Char). mapping.md §2. G-CONF bridges via the real `escape_uri_path`. |
| A2 | param `encodedQuery : List Char` | `request.META["QUERY_STRING"]`, fed through `iri_to_uri` inside `get_full_path` | R | the **output** of the unchanged query encoder is the carrier: `iri_to_uri(QUERY_STRING)` ↔ `encodedQuery`; `encodedQuery = []` ⇔ no query string (`iri_to_uri("")==""`). mapping.md §2. |
| A3 | `slash := if encodedPath.getLast? = some '/' then [] else ['/']` | `"/" if force_append_slash and not path.endswith("/") else ""` (with `force_append_slash=True`) | I + R | concrete conditional, transliterated by G-CONF. `force_append_slash` fixed `True` at the call site; `path.endswith("/")` ⇔ `encodedPath.getLast? = some '/'` because `escape_uri_path` keeps `/` safe (mapping.md §2). |
| A4 | `query := if encodedQuery = [] then [] else '?' :: encodedQuery` | `("?" + iri_to_uri(QS)) if QS else ""` | I + R | concrete conditional; the `'?'` literal is identical; the query is **preserved** — the behaviour the issue + F2P tests demand. The pre-patch expression had no counterpart op (it dropped the query). |
| A5 | `result := encodedPath ++ slash ++ query`; `return result` | the `"%s%s%s"` assembly built by `_get_full_path`, wrapped by `HttpResponsePermanentRedirect` | A-reference + I | the changed destination is modeled **deeply**: `redirectTarget`/`appendSlashRedirect` ARE the three-component assembly. The assembly ops (`++`, the two conditionals) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `get_full_path(force_append_slash=True)` is the **A-reference** G-AX validates. `HttpResponsePermanentRedirect` is identity on the destination string the F2P tests compare (mapping.md §2). |

Discriminating content of the change — **the query string is preserved after
`?`** — lives in `query = '?' :: encodedQuery` when `encodedQuery ≠ []` (model)
⇔ the `("?" + iri_to_uri(QS))` component of `get_full_path` (real). The pre-patch
`"%s/" % request.path` produced only `path + "/"`; `Solution_prepatch.lean`
reproduces that (`result := encodedPath ++ ['/']`) and **fails**
`out = redirectTarget encodedPath encodedQuery` exactly on the query-suffix
clause (G-DIFF): the unsolved goal reduces to `['/'] = (slash-component) ++ (if
encodedQuery = [] then [] else '?' :: encodedQuery)`, false whenever a query is
present (and also false on the slash component when the path already ends in `/`).

## B. No consumed axioms

There are no `axiom`s the proof consumes. The two URL percent-encoders
(`escape_uri_path`, `iri_to_uri`) are unchanged community helpers; their outputs
are refined into the input carrier (A1/A2, an **R** leg), not axiomatized — they
are not what this specification pins and would not be code-generable inside the
executable body. The one operation that genuinely *changed* — the redirect
destination's assembly, now query-preserving — is modeled **deeply** (the
spelled-out `redirectTarget`, step A5, an A-reference + I), not hidden behind an
axiom about the function under change. No dead axioms are shipped.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The changed expression is expressible as a finite
character-list assembly; nothing required a kind-3 escape hatch.

## D. verify(Solution) ⇒ resolved

`appendSlashRedirect` verifies only if its output equals the exact three-component
assembly `redirectTarget` — i.e. encoded path, conditional slash, **and the
preserved query suffix** (A3–A5). By R (`escape_uri_path`/`iri_to_uri` outputs ↔
`encodedPath`/`encodedQuery`, `HttpResponsePermanentRedirect` identity on the
destination string) the verified assembly equals
`request.get_full_path(force_append_slash=True)` on the tested inputs; by G-AX
the deep model `redirectTarget` equals the real `get_full_path(force=True)`
(A-reference); by G-CONF the R/I transliteration of the assembly agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
deep-model callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: deep-model soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
