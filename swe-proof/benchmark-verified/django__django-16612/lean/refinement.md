# refinement.md — django__django-16612

Maps every operation in `implementation_redirectTargetWithTrailingSlash` to its
`patch.diff` counterpart. The patch swaps the redirect-target expression in
`AdminSite.catch_all_view` from `"%s/" % request.path` to
`request.get_full_path(force_append_slash=True)`; the impl is the skeleton of the
post-patch target construction, unfolded through `HttpRequest._get_full_path`
(see mapping.md). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch)
```python
# django/contrib/admin/sites.py — AdminSite.catch_all_view
return HttpResponsePermanentRedirect(
    request.get_full_path(force_append_slash=True)
)
```
governing, unchanged (`django/http/request.py`):
```python
def get_full_path(self, force_append_slash=False):
    return self._get_full_path(self.path, force_append_slash)
def _get_full_path(self, path, force_append_slash):
    return "%s%s%s" % (
        escape_uri_path(path),
        "/" if force_append_slash and not path.endswith("/") else "",
        ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
        if self.META.get("QUERY_STRING", "") else "",
    )
```
(post-patch call site fixes `force_append_slash=True`.)

## Operation correspondence
| # | Lean op (`implementation_redirectTargetWithTrailingSlash`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `let escapedPath := escapePathComponent path` | `escape_uri_path(path)` | A-reference | unchanged standard URI-path encoder, opaque leaf; G-AX validates `escapePathComponent == escape_uri_path`. No property consumed by the proof. |
| 2 | `let trailingSlash := if path.endsWith "/" then "" else "/"` | `"/" if force_append_slash and not path.endswith("/") else ""` with `force_append_slash=True` | R/I | with `force_append_slash` fixed `True`, the Python conditional reduces to `"/" if not path.endswith("/") else ""`; `path.endsWith "/" ↔ path.endswith("/")` (identity on `String`). |
| 3 | `let querySuffix := if queryString = "" then "" else "?" ++ encodeQueryString queryString` | `("?" + iri_to_uri(QUERY_STRING)) if QUERY_STRING else ""` | A-reference / R | the falsy-`QUERY_STRING` test ⇔ `queryString = ""`; `iri_to_uri` is an unchanged opaque leaf (A-reference, G-AX-validated); `"?" + ...` ↔ `"?" ++ ...` (identity on `String`). |
| 4 | `return escapedPath ++ trailingSlash ++ querySuffix` | the `"%s%s%s"` three-piece string format | I | identical concatenation order: escaped path, slash piece, query piece. |

Every op is R, I, or A-reference. **No A-consumed row** — the proof consumes no
callee property (the opaque encoders appear identically in spec and impl, so
`correct_redirectTargetWithTrailingSlash` holds for any such functions and is in
fact closeable by `rfl`). The A-reference leaves are validated == the real
callees by G-AX; the R/I structure is differential-tested by G-CONF.

## R/I legs ⇒ G-CONF
The impl is R/I + A-reference. `conformance_check.py` builds the impl shadow in
Python with the A-reference leaves left as the REAL repo callees
(`escape_uri_path`, `iri_to_uri`) and differential-tests it against
`request.get_full_path(force_append_slash=True)` over ≥10^5 fuzzed
`(path, query_string)` inputs. `conf_skip = false` (the impl is not all-A-tagged;
the slash conditional and the concatenation are concrete R/I ops).

## A-reference ⇒ G-AX
`axiom_check.py` runs the real `escape_uri_path` and `iri_to_uri` on boundary +
fuzzed strings and confirms they are total deterministic `str → str` functions
(the only property the `opaque <callee> : String → String` declarations assert).
No `_prop` axiom is consumed, so there is no stronger contract to validate; the
check confirms the opaque-leaf modeling is faithful (callees are pure total
string functions).

## Prepatch = the real bug
`Solution_prepatch.lean` models the pre-patch target `"%s/" % request.path`:
`return path ++ "/"` — the raw path, an unconditional trailing slash, and NO
query suffix. The carried gold proof (`rfl`) fails to typecheck because the spec
demands `escapePathComponent path ++ (slash conditional) ++ (query suffix)`,
which the buggy impl does not produce: it omits the query string entirely (and
the path escaping, and the slash conditional). The discriminating clause is
exactly the dropped query string the FAIL_TO_PASS tests assert
(`?id=1` must survive the redirect). The spec is byte-identical between the two
files (only the impl body and the proof differ).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the redirect-target swap in
`django/contrib/admin/sites.py`); it applies at `base_commit` and the harness
resolves.
