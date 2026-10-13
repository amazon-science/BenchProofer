# mapping.md — django__django-14404

## Symbol binding (@ base_commit de32fe83a2e4a20887972c69a0693b94eb25a88b)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_catchAll` / `problem_spec_catchAll` | `AdminSite.catch_all_view(self, request, url)` | `django/contrib/admin/sites.py:419-431` |
| `resolveLoc : String → Urlconf → Option ResolveMatch` | `django.urls.resolve(path, urlconf)` | callee, `django/urls/base.py` (UNCHANGED) |
| `ResolveMatch.shouldAppend` | `getattr(match.func, 'should_append_slash', True)` | `sites.py:429` |
| `Request.visiblePath` | `request.path` | HttpRequest attr — externally visible path, INCLUDES script-name prefix |
| `Request.routingPath` | `request.path_info` | HttpRequest attr — routing path, EXCLUDES script-name prefix |
| `Request.urlconf` | `getattr(request, 'urlconf', None)` | `sites.py:422` |
| `Outcome.redirect target` | `HttpResponsePermanentRedirect(target)` (301) | `sites.py:430` |
| `Outcome.notFound` | `raise Http404` | `sites.py:431` |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

| Lean | Python |
|---|---|
| `String` | `str` (URL path values) |
| `Bool` (`appendSlash`) | `settings.APPEND_SLASH` (truthy) |
| `url.endsWith "/"` | `url.endswith('/')` |
| `s ++ "/"` | `'%s/' % s` |
| `Option ResolveMatch` | success match object vs `Resolver404` exception |
| `ResolveMatch.shouldAppend` | `getattr(match.func, 'should_append_slash', True)` (default True) |

## Callee provenance + flag deps

- `resolveLoc` (= `django.urls.resolve`) is an UNCHANGED callee. Its first
  argument is built from `request.path_info` both pre- and post-patch (the patch
  did NOT change the resolve argument — only inlined the local `path` variable).
  It is declared `opaque` (signature only). The fix does not depend on
  `resolve`'s internal behavior, so the proof consumes NO `resolveLoc_prop`
  axiom: `resolveLoc` appears identically in `problem_spec_catchAll` and
  `implementation_catchAll`. ⇒ A-reference with no consumed property; G-AX is a
  skip stub.
- The behavior change is entirely in the redirect-TARGET string:
  `request.path_info` (script-name stripped) → `request.path` (script-name
  included). Flag context: only reached under `settings.APPEND_SLASH` truthy,
  the locator not ending in `/`, a successful resolve, and
  `should_append_slash` truthy.

## G-CONF fuzz seed

`SEED = 14404` (pinned; used by conformance_check.py).
