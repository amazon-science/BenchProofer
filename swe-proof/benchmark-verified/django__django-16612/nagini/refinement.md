# refinement.md — django__django-16612

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_append_slash_redirect` impl region and the deep `redirect_target`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement, possibly via a normalisation that is the identity on the exercised
character class), **A** (axiomatized callee — none here), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The redirect-target site — `catch_all_view` (`django/contrib/admin/sites.py:456`)

Gold hunk:
```
-                    return HttpResponsePermanentRedirect("%s/" % request.path)
+                    return HttpResponsePermanentRedirect(
+                        request.get_full_path(force_append_slash=True)
+                    )
```

The reached branch already guarantees `settings.APPEND_SLASH` and the requested
URL lacks its trailing slash; the only changed sub-expression is the **argument
to `HttpResponsePermanentRedirect`** — the redirect target string.

| # | model.py impl op (`build_append_slash_redirect`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `path: List[int]`, `query: List[int]` | `request.path` (`str`) and `request.META["QUERY_STRING"]` (`str`) consumed by `request.get_full_path(force_append_slash=True)` | R | `str` ↔ `List[int]` code points (mapping.md §2). `request.path` ↔ `path`; the request's query string ↔ `query`. |
| A2 | copy `path` into the result (the forward loop), giving `ToSeq(result) == ToSeq(path)` | `escape_uri_path(request.path)` term of `_get_full_path` (`request.py:187`) | R | `escape_uri_path` = `quote(path, safe=…)` is the **identity** on the tested location class (admin endpoint paths); mapping.md §2/§3.1, axiom_check.py confirms. The model copies the location verbatim. |
| A3 | append `[47]` iff `path` does not already end in `47` (`slash_part`) | `"/" if force_append_slash and not path.endswith("/") else ""` (`request.py:188`) | R + I | `47 == ord("/")`; the trailing-slash predicate `path.endswith("/")` ↔ `ends_with_slash`. The gold passes `force_append_slash=True`, so that conjunct is constant-true (mapping.md §3.1 flag dependency). |
| A4 | iff `len(query) > 0`: append `[63]` then copy `query` verbatim (`query_part`) | `("?" + iri_to_uri(QUERY_STRING)) if QUERY_STRING else ""` (`request.py:189-191`) | R + I | `63 == ord("?")`; `iri_to_uri` = `quote(q, safe=…)` is the **identity** on the tested ASCII query class (mapping.md §2/§3.1, axiom_check.py). The query is appended verbatim iff non-empty — this is the entire behavioural change. |
| A5 | `result` returned (a `List[int]`) | the assembled `str` passed to `HttpResponsePermanentRedirect(...)` | R | `HttpResponsePermanentRedirect` stores the target in the `Location` header; the F2P `assertRedirects` compares that target string. `List[int]` ↔ `str` content (mapping.md §2). |

The discriminating content of the change — the query component is **carried
into** the redirect rather than dropped — lives in step A4
(`query_part(query) == PSeq(63) + query` for non-empty `query`) ⇔ the
`("?" + iri_to_uri(QUERY_STRING))` term that the gold adds via `get_full_path`.
The pre-patch built `"%s/" % request.path`, i.e. location ++ slash with **no
query term**; `model_prepatch.py` reproduces exactly that skeleton (copy `path`,
append `[47]`, return — never touching `query`) and **fails** the postcondition
`ToSeq(Result()) == redirect_target(ToSeq(path), ToSeq(query))` (and the
`Implies(len(query) > 0, …)` clause) whenever the query is non-empty — which is
precisely the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — assembling
the redirect target so the query survives — is modelled **deeply** (the
spelled-out `redirect_target` / `slash_part` / `query_part` consumed in
`build_append_slash_redirect`), not hidden behind an axiom about the function
under change. There is **no consumed `@ContractOnly` axiom** (the `axioms`
region is empty). The only external trust point is the R-refinement that the
location/query normalisations (`escape_uri_path`, `iri_to_uri`) are the
identity on the exercised character class; that is an **A-reference**-style
claim validated out-of-band by axiom_check.py / G-AX (mapping.md §3), not a
consumed axiom in the proof.

## C. verify(model) ⇒ resolved

`build_append_slash_redirect` verifies only if its output equals
`redirect_target(path, query)` = location ++ slash ++ ("?" ++ query when the
query is non-empty) (A2-A4). By R (str ↔ List[int]; `escape_uri_path` /
`iri_to_uri` = identity on the tested class, §3.1; `force_append_slash=True`)
the verified target equals `request.get_full_path(force_append_slash=True)` on
the tested inputs — i.e. the gold patch's redirect argument. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement on the tested inputs — and the gold patch resolves (G-RESOLVE). The
single trust point is the §3.1 R-refinement (G-AX) plus the refinement fidelity
of this document (G-EQ).
