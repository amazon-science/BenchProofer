# mapping.md — django__django-14404

Binds every `model.py` symbol to its repository counterpart at
`base_commit = de32fe83a2e4a20887972c69a0693b94eb25a88b`, states the type
abstraction, and gives the provenance of the modelled behaviour.

Repo file under change: `django/contrib/admin/sites.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `slash_redirect_target(full_path, app_relative_path, append_slash_enabled, url_has_trailing_slash, slash_form_resolves, target_view_opts_in)` | `AdminSite.catch_all_view(self, request, url)` — `django/contrib/admin/sites.py:419-430` | the modeled changed function (the final fall-through slash-appending redirect view) |
| `full_path` | `request.path` — `django/core/handlers/wsgi.py:75-76` | the request's full externally-visible path, WITH any deployment/script-name prefix |
| `app_relative_path` | `request.path_info` — `django/core/handlers/wsgi.py:69-71` | the prefix-stripped, application-relative path (no script-name prefix) |
| `append_slash_enabled` | `settings.APPEND_SLASH` — used at `sites.py:421` | whether slash-appending is enabled |
| `url_has_trailing_slash` | `url.endswith('/')` — `sites.py:421` | whether the requested URL already ends with a slash |
| `slash_form_resolves` | `resolve('%s/' % request.path_info, urlconf)` succeeds (no `Resolver404`) — `sites.py:424-426` | whether the slash-terminated form routes to a view |
| `target_view_opts_in` | `getattr(match.func, 'should_append_slash', True)` — `sites.py:428` | whether the resolved view opts IN to slash-appending (default True; `@no_append_slash` sets it False) |
| `NotFound` (exception) | `Http404` — raised at `sites.py:430`; `django/http/response.py:575` | the not-found signal raised when no redirect is issued |
| `with_trailing_slash(p)` | `'%s/' % <path>` — the string-format that appends a single `'/'` (`sites.py:429` post-patch; was `sites.py:422` pre-patch) | pure spec: a path followed by code point 47 |

The pre-patch local the change removes (for the refinement audit, not
referenced from the consumer spec view): the local `path = '%s/' % request.path_info`
(`sites.py:422`), which was reused both as the `resolve` argument AND as the
redirect target. The fix splits these: `resolve` keeps the `path_info`-derived
argument inline, while the redirect target is rebuilt from `request.path`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`request.path`, `request.path_info`, and the redirect target string) | `List[int]` of Unicode code points | `s[k]` ↔ `list[k] == ord(s[k])`; `len(s)` ↔ `len(list)`; `str` `+` / `%s/` formatting ↔ list append of code point 47; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`len`/`[i]` mirror `str` `+`/`len`/index; `'%s/' % p` ↔ `p + PSeq(47)` (`with_trailing_slash`) |
| `'/'` code point | `47` | `ord('/') == 47` |
| `settings.APPEND_SLASH` (bool) | `append_slash_enabled: bool` | identity |
| `url.endswith('/')` (bool) | `url_has_trailing_slash: bool` | identity — the trailing-slash predicate evaluated at the call site |
| resolve succeeds vs. raises `Resolver404` (control outcome) | `slash_form_resolves: bool` | the `try/except Resolver404 … else` reduces, at this site, to "did the slash-form resolve" — the boolean that gates the `else` branch |
| `getattr(match.func, 'should_append_slash', True)` (bool) | `target_view_opts_in: bool` | identity — the per-view opt-in flag (default True) |
| `HttpResponsePermanentRedirect(<url>)` wrapper (`sites.py:429`) | identity on the redirect-target code points (the constructor's `Location` argument is the modelled `Result()`) | the `301` response wraps the target URL unchanged; the F2P tests observe the redirect target via `assertRedirects(..., status_code=301)` |
| `Http404` raised (`sites.py:430`) | `Exsures(NotFound, …)` with a user-defined `NotFound` | builtin-exception `Exsures` crashes the translator, so a user-defined class stands in; the raise condition is the negation of the four-guard conjunction |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the redirect-target specification is phrased over `PSeq[int]` via
`ToSeq`.

### 2.1 Why `request.path` carries the prefix and `request.path_info` does not

From `django/core/handlers/wsgi.py:65-76` (`WSGIRequest.__init__`, unchanged by
this instance):

```python
script_name = get_script_name(environ)          # FORCE_SCRIPT_NAME / SCRIPT_NAME
path_info = get_path_info(environ) or '/'
self.path_info = path_info                        # prefix-STRIPPED
self.path = '%s/%s' % (script_name.rstrip('/'),   # prefix + path_info tail
                       path_info.replace('/', '', 1))
```

`get_script_name` returns `settings.FORCE_SCRIPT_NAME` when set, else the WSGI
`SCRIPT_NAME` (`wsgi.py:159-187`). Thus `request.path` includes the deployment
prefix and `request.path_info` does not. When a prefix is present the two
strings differ — exactly the regime the F2P tests exercise. In the model this
is the fact that `full_path` and `app_relative_path` are independent inputs
(not assumed equal); the redirect target must be grounded in `full_path`.

## 3. Callees / axioms

**None consumed.** The only string operation that *changed* — building the
redirect target from the full path rather than the prefix-stripped path — is
modelled DEEPLY over the code-point sequences (`with_trailing_slash`, the
`result.append(47)` impl), so there is no `@ContractOnly` axiom the proof
consumes. The unchanged callees the view invokes are reduced to the booleans /
sequences they contribute at this site:

| repo callee | unchanged? | how modelled | why not an axiom |
|---|---|---|---|
| `resolve(path, urlconf)` / `Resolver404` (`django/urls/base.py:21`, `django/urls/exceptions.py:4`) | unchanged (gold keeps the `path_info`-derived argument) | `slash_form_resolves: bool` | its only effect at this site is to gate the `else` branch (success) vs. fall-through to `Http404` (raise); the value it computes is never used to build the redirect target |
| `getattr(match.func, 'should_append_slash', True)` (`django/views/decorators/common.py:13`) | unchanged | `target_view_opts_in: bool` | a plain attribute read with a default, reduced to its boolean value |
| `HttpResponsePermanentRedirect(url)` (`django/http/response.py`) | unchanged | identity on `Result()` (the `Location` URL) | the constructor copies the target URL into the `301` response unchanged; observed verbatim by `assertRedirects` |
| `Http404` (`django/http/response.py:575`) | unchanged | `Exsures(NotFound, …)` | the raise path; builtin-exception `Exsures` is banned, user-defined `NotFound` stands in |

Because there is **no axiom**, `axiom_check.py` (G-AX) instead validates the
one deep modelling decision that is load-bearing for correctness: that
`request.path` (the chosen base) carries the script-name prefix while
`request.path_info` does not, so building the redirect target from
`request.path` is what restores the prefix. It reconstructs `request.path` and
`request.path_info` exactly as `WSGIRequest.__init__` does, over boundary and
fuzzed `SCRIPT_NAME` / `PATH_INFO` pairs, and asserts the model's
`with_trailing_slash(full_path)` equals `'%s/' % request.path` (the gold
redirect target) and differs from `'%s/' % request.path_info` (the bug) exactly
when a non-empty prefix is present.
