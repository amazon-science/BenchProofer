# mapping.md — django__django-16612

## Instance
- repo: django/django
- base_commit: 55bcbd8d172b689811fae17cde2f09218dd74e9c
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch changes ONE expression in `AdminSite.catch_all_view`
(`django/contrib/admin/sites.py:456` @ base_commit). When the admin catch-all
view decides to issue an `APPEND_SLASH` permanent redirect, the redirect target
goes from

```python
return HttpResponsePermanentRedirect("%s/" % request.path)
```

to

```python
return HttpResponsePermanentRedirect(
    request.get_full_path(force_append_slash=True)
)
```

The pre-patch target is built solely from `request.path` with a hard-coded `/`
appended, which silently discards the request's query string. The post-patch
target delegates to `HttpRequest.get_full_path(force_append_slash=True)`, which
preserves the query string (and conditionalizes the trailing slash).

`get_full_path` is itself unchanged by the patch; its body @ base_commit
(`django/http/request.py:177,182`) is:

```python
def get_full_path(self, force_append_slash=False):
    return self._get_full_path(self.path, force_append_slash)

def _get_full_path(self, path, force_append_slash):
    return "%s%s%s" % (
        escape_uri_path(path),
        "/" if force_append_slash and not path.endswith("/") else "",
        ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
        if self.META.get("QUERY_STRING", "")
        else "",
    )
```

With `force_append_slash=True`, this is exactly: escaped path, then a trailing
slash iff the path does not already end in `/`, then `?` + the encoded query
string iff a non-empty query string is present.

The FAIL_TO_PASS tests
(`test_missing_slash_append_slash_true_query_string`,
`test_missing_slash_append_slash_true_script_name_query_string`) request a known
admin URL missing its trailing slash WITH a `?id=1` query string and assert the
301 redirect target still carries `?id=1` (pre-patch it was dropped).

## Modeled function
I model the **redirect-target construction** — the string value passed to
`HttpResponsePermanentRedirect` — as a total function of the two data the target
is built from: the requested path and the accompanying query string. This is the
smallest unit whose observable behavior the patch changes and the F2P tests pin.
The construction is pure (string assembly over `get_full_path(force_append_slash=
True)`); the surrounding control flow (`APPEND_SLASH`, the `resolve` lookup, the
`should_append_slash` guard) is unchanged by the patch and is the same on both
branches, so it is not part of the modeled unit.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_redirectTargetWithTrailingSlash` | the redirect-target expression in `AdminSite.catch_all_view`, post-patch `request.get_full_path(force_append_slash=True)` (`django/contrib/admin/sites.py:456`), unfolded through `HttpRequest._get_full_path` (`django/http/request.py:182`) |
| `problem_spec_redirectTargetWithTrailingSlash` | the post-condition the redirect target string must satisfy |
| `escapePathComponent` | `django.utils.encoding.escape_uri_path` (`django/http/request.py:186`) — percent-encodes a path into the safe URI-path range |
| `encodeQueryString` | `django.utils.encoding.iri_to_uri` (`django/http/request.py:189`) — encodes a query string into the safe URI-query range |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `path : String` | `request.path` (a `str`) | identity: Python `str` ↔ Lean `String` |
| `queryString : String` | `request.META.get("QUERY_STRING", "")` (a `str`) | identity; the empty string ↔ Lean `""` (the "no query string" case) |
| result `: String` | the `str` passed to `HttpResponsePermanentRedirect` | identity |
| `escapePathComponent path` | `escape_uri_path(path)` | opaque leaf; A-reference (G-AX validates equality on the real callee) |
| `encodeQueryString queryString` | `iri_to_uri(query_string)` | opaque leaf; A-reference |
| `path.endsWith "/"` | `path.endswith("/")` | identity on the trailing-slash test |
| `queryString = ""` | `if self.META.get("QUERY_STRING", "")` (falsy ⇔ empty) | a `QUERY_STRING` of `""` is the only falsy value reachable here; `queryString = "" ↔ no query string appended` |

## Callee provenance / flag deps
- `escape_uri_path` and `iri_to_uri` are UNCHANGED standard URI encoders that the
  modeled construction calls but does not change. They are declared `opaque`
  (signature only) so they can appear in the executable impl. They are
  **A-reference** leaves: the proof consumes NO property of them (they appear
  identically in spec and impl, so `correct_*` holds for any such functions);
  G-AX validates the `opaque` leaves equal the real callees on boundary + fuzz.
- Flag dependency: the modeled construction corresponds to `get_full_path` called
  with `force_append_slash=True` (the post-patch call site always passes
  `force_append_slash=True`). The trailing-slash conditional therefore reduces to
  "append `/` iff `not path.endswith('/')`", which is what the impl encodes.
  Recorded so G-AX/G-CONF exercise the `force_append_slash=True` configuration.

## G-CONF fuzz seed
- pinned seed: `16612`
- ≥10^5 fuzzed `(path, queryString)` tuples; paths drawn from a pool mixing
  trailing-slash / no-trailing-slash, ASCII-safe and percent-escape-triggering
  characters (spaces, unicode, reserved chars), and query strings mixing empty,
  simple `id=1`, multi-key, and escape-triggering values.
