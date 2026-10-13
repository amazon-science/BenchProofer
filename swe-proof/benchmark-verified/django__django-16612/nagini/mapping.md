# mapping.md — django__django-16612

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 55bcbd8d172b689811fae17cde2f09218dd74e9c`, states the type
abstraction, and gives the provenance of the one external claim the bundle
relies on (the R-refinement on the URL/IRI normalisation, checked by
axiom_check.py / G-AX).

Repo file under change: `django/contrib/admin/sites.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_append_slash_redirect(path, query)` | the redirect target built in `AdminSite.catch_all_view` — `django/contrib/admin/sites.py:447` (changed line 456) | the modeled changed behaviour: the slash-completing redirect target |
| `redirect_target(path, query)` *(deep model)* | `HttpRequest._get_full_path(self.path, force_append_slash=True)` — `django/http/request.py:183` (invoked through `request.get_full_path(force_append_slash=True)`, `request.py:177`) | pure spec: the full target = location ++ slash ++ query, modelled deeply |
| `slash_part(path)` | the `"/" if force_append_slash and not path.endswith("/") else ""` term of `_get_full_path` (`request.py:188`) | pure spec: the single trailing-slash separator |
| `query_part(query)` | the `("?" + iri_to_uri(QUERY_STRING)) if QUERY_STRING else ""` term of `_get_full_path` (`request.py:189-191`) | pure spec: the "?"-introduced query component |
| `ends_with_slash(s)` | `path.endswith("/")` (`request.py:188`) | pure spec: trailing-slash test |

The pre-patch repo expression the change removes (for the refinement audit,
not referenced from the consumer spec view): `"%s/" % request.path`
(`sites.py:456`), which appends only the trailing slash to the location and
never includes the query component.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` location (`request.path`) and `str` query (`request.META["QUERY_STRING"]`) | `List[int]` of Unicode code points | `s[k]` ↔ `xs[k] == ord(s[k])`; `len(s)` ↔ `len(xs)`; `str` concatenation ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) via `ToSeq` | `PSeq` `+`/`take`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `path.endswith("/")` | `ends_with_slash(ToSeq(path))` = `len(s)>0 and s[len(s)-1]==47` | `47 == ord("/")` |
| `"?"`, `"/"` literals | `PSeq(63)`, `PSeq(47)` | `63 == ord("?")`, `47 == ord("/")` |
| `escape_uri_path(path)` (`request.py:187`, `encoding.py:195`) and `iri_to_uri(QUERY_STRING)` (`request.py:189`, `encoding.py:111`) | the **identity** on character content (omitted from the carrier) | for the location and query character classes the targeted behaviour exercises (admin endpoint paths; ASCII query strings such as `id=1`), both transforms are `urllib.parse.quote` with `safe=` sets that contain every character that occurs, so they return their argument unchanged. Audited by axiom_check.py / G-AX over boundary + 20 000 fuzz inputs in that class. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. The one external claim (R-refinement domain — checked by G-AX)

### 3.1 `redirect_target` deep model ↔ `_get_full_path(..., force_append_slash=True)`
There is **no consumed `@ContractOnly` axiom**. The changed behaviour (the
redirect target) is modelled **deeply** by the pure functions
`redirect_target` / `slash_part` / `query_part` and the verified loop in
`build_append_slash_redirect`. The only thing audited out-of-band is the
**R-refinement** that the location/query normalisations are the identity on
the exercised character class, so that the deep concatenation equals the real
`_get_full_path` output character-for-character.

`_get_full_path(path, force_append_slash)` (`django/http/request.py:183`):
```python
def _get_full_path(self, path, force_append_slash):
    return "%s%s%s" % (
        escape_uri_path(path),
        "/" if force_append_slash and not path.endswith("/") else "",
        ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
        if self.META.get("QUERY_STRING", "")
        else "",
    )
```
With `force_append_slash=True` this is exactly
`escape_uri_path(path) ++ slash ++ ("?" ++ iri_to_uri(q) if q else "")`. Under
the R-refinement (`escape_uri_path`/`iri_to_uri` = identity on the tested
class), this is `path ++ slash_part(path) ++ query_part(q)` = `redirect_target`.

**Flag dependency:** the slash term is present only under
`force_append_slash=True`, which is exactly the keyword the gold patch passes
(`request.get_full_path(force_append_slash=True)`). The query term depends only
on a non-empty `QUERY_STRING`. axiom_check.py reproduces `escape_uri_path` /
`iri_to_uri` with Django's exact `safe=` sets and pins `force_append_slash=True`.

### 3.2 Why the targeted F2P tests live in this domain
The two F2P tests of the fix —
`test_missing_slash_append_slash_true_query_string`
(`?id=1` → `?id=1`) and
`test_missing_slash_append_slash_true_script_name_query_string`
(`?id=1` → `?id=1` with a `/prefix` SCRIPT_NAME) — use the ASCII query `id=1`
and admin paths, all inside the identity-transform class (§2/§3.1). The
SCRIPT_NAME case only prepends `/prefix` to `request.path`, which is still in
the class. (The separate non-staff test produces a *login* redirect whose
`next=` parameter is percent-encoded by `redirect_to_login`, a different code
path not built by `catch_all_view`; it is a P2P regression guard here, not part
of the modeled construction.)
