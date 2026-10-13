# mapping.md — psf__requests-6028

## Symbol binding (file:line @ base_commit 0192aac241)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_prependScheme` / `problem_spec_prependScheme` / `correct_prependScheme` | `prepend_scheme_if_needed(url, new_scheme)` | `requests/utils.py:960-982` @ base_commit |
| `reassemble` / the userinfo re-attach clause | `netloc = '@'.join([auth, netloc])` (post-patch, inserted before the scheme/path defaulting) | gold patch, `requests/utils.py:977-980` |
| `assembleUrl` | `urlunparse((scheme, netloc, path, '', query, fragment))` | `requests/utils.py:982` |

## What the function does (post-patch)

```python
def prepend_scheme_if_needed(url, new_scheme):
    parsed = parse_url(url)
    scheme, auth, host, port, path, query, fragment = parsed
    netloc = parsed.netloc                       # host[:port], NO userinfo
    if not netloc:
        netloc, path = path, netloc              # empty-authority swap (defect compat)
    if auth:                                     # <-- POST-PATCH (was absent)
        netloc = '@'.join([auth, netloc])        # re-attach userinfo to authority
    if scheme is None:
        scheme = new_scheme
    if path is None:
        path = ''
    return urlunparse((scheme, netloc, path, '', query, fragment))
```

`parse_url` (urllib3) returns the authority via its `.netloc` property as
`host` or `host:port` — it deliberately EXCLUDES the userinfo. The userinfo is
returned separately in `parsed.auth`. The pre-patch code re-assembled the URL
from `netloc` without the userinfo, so for a proxy URL like
`http://user:pass@host` the credentials were dropped, producing a 407. The patch
re-joins `auth` to the front of `netloc` with `@` before re-assembly.

`urlunparse((scheme, netloc, path, '', query, fragment))` is the standard library
URL un-splitter: with a present (truthy) scheme and authority it emits
`scheme://authority[/path][?query][#fragment]`, giving a non-empty path a leading
`/` if it lacks one, and dropping empty query/fragment. This is reproduced
concretely as `assembleUrl` (the standard `urlunsplit` truthy-netloc + truthy-
scheme arm).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

The upstream `parse_url(url)` is the I-tagged parse step that produces the
function's inputs; its components bind to the Lean inputs as:

| Python (`parse_url(url)`) | Lean | bijection |
|---|---|---|
| `parsed.scheme` (`str | None`) | `scheme0 : Option String` | `None ↦ none`, `s ↦ some s` |
| `parsed.auth` (`str | None`) | `auth : Option String` | `None ↦ none`, `a ↦ some a`; the userinfo/credentials |
| `parsed.netloc` (`str`, host[:port]) | `authority0 : String` | the authority WITHOUT userinfo; truthy in the modeled domain |
| `parsed.path or ''` | `path : String` | `None ↦ ""` |
| `parsed.query or ''` | `query : String` | `None ↦ ""` |
| `parsed.fragment or ''` | `fragment : String` | `None ↦ ""` |
| `new_scheme` (`str`) | `newScheme : String` | default scheme |
| return value (`str`) | `result : String` | verbatim string equality |

Python truthiness `if auth:` ↦ `auth = some a ∧ a ≠ ""` (an empty userinfo
string is falsy and not re-attached); `if not netloc:` ↦ `authority0 = ""`.

## Modeled domain / precondition

The bundle models the domain where `parse_url(url).netloc` is **non-empty** — a
host is present. This is exactly:

- the precondition `authority0 ≠ ""` carried as a binder of `correct_prependScheme`
  (with `newScheme ≠ ""` and "a present scheme is non-empty", both always true of
  the real `parse_url` output and the caller's `new_scheme`);
- the configuration the issue reports (a proxy URL `scheme://user:pass@host`).

Out-of-domain and excluded (not what the F2P tests exercise):
- empty authority (`not netloc`) → the swap branch; the real callee then handles
  a degenerate authority. The swap is still spelled out in `reassemble` so the
  model is total, but G-CONF restricts to the `netloc` truthy domain.
- userinfo present with no host (e.g. `"user@"`): `parse_url` gives `auth='user',
  netloc=''`, and the REAL post-patch callee RAISES `TypeError`
  (`'@'.join([auth, None])`), so it is outside any well-defined modeled behavior.

## Callee provenance + flag dependencies

- No callee axiom is consumed. The changed op (`'@'.join([auth, netloc])` userinfo
  re-attachment) is the operation the patch introduces, so it is modeled DEEPLY
  (an A-reference validated by G-CONF against the real `prepend_scheme_if_needed`),
  never axiomatized (§0.7).
- `urlunparse` (unchanged std-lib) is reproduced concretely as `assembleUrl` for
  the truthy-scheme/truthy-authority arm — the only arm reachable under the
  modeled precondition — so no axiom is needed; G-CONF validates it end-to-end.
- `parse_url` (urllib3, unchanged) is the upstream input-producing parse, out of
  scope; G-CONF bridges through the real `parse_url` so its component split is
  exercised by the real library.
- Flag/branch dependency: G-CONF fuzzes URLs with and without userinfo, with and
  without scheme/port/path/query/fragment, restricted to the non-empty-authority
  domain, matching how the bug manifests for proxy URLs with credentials.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).

## Leakage note

The public `problem_statement` is a proxy **407 "Proxy Authentication Required"**
report — i.e. it is already about proxy authentication / URL handling failing on
re-assembly. The spec view is deliberately written as a *component-symmetric* URL
round-trip: it states that a correct reconstruction carries **every** parsed piece
(scheme, userinfo, host/authority, path, query, fragment) through into its standard
syntactic slot, with `userinfo` placed at its standard `userinfo@authority`
position — general URL syntax, not the gold's `'@'.join([auth, netloc])` mechanism.
It names no patched symbol/file and no `prepend_scheme_if_needed`/`parse_url`/
`urlunparse`/`netloc`, and does not single out credential-preservation as *the*
behavior. Describing this postcondition is intrinsic to specifying a URL
re-assembler in the domain the public 407 statement already occupies, so it does
not disclose the gold edit beyond `problem_statement` (G-PANEL Role 4 = NO-LEAKAGE).
