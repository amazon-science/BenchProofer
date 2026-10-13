# refinement.md — psf__requests-6028

Operation correspondence between `implementation_prependScheme` (+ its `pure`
helpers `reassemble` / `assembleUrl`) and the gold `patch.diff`. Tags: **R**
(type refinement), **A-consumed** (proof uses an axiom's property), **A-reference**
(deep model validated == real callee by G-AX/G-CONF), **I** (identical concrete
op).

No axioms are declared or consumed: the changed operation (re-attaching the
userinfo to the authority) is modeled DEEPLY. Every row is **R**,
**A-reference**, or **I**. The R/I/A-reference legs are differential-tested by
G-CONF; G-AX is a skip stub (no consumed callee axiom).

## The gold patch

```python
     if not netloc:
         netloc, path = path, netloc

+    if auth:
+        # parse_url doesn't provide the netloc with auth
+        # so we'll add it ourselves.
+        netloc = '@'.join([auth, netloc])
     if scheme is None:
         scheme = new_scheme
     if path is None:
         path = ''
```

The surrounding parse, the empty-authority swap, the scheme/path defaulting, and
the final `urlunparse` re-assembly are unchanged.

## `implementation_prependScheme` / `reassemble` ↔ `prepend_scheme_if_needed`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| inputs `scheme0 auth authority0 path query fragment newScheme` | `parsed = parse_url(url); scheme,auth,host,port,path,query,fragment = parsed; netloc = parsed.netloc` and the `new_scheme` arg | R | the upstream parse is the I-tagged input-producing step (bridged through the real `parse_url` by G-CONF); `authority0 = parsed.netloc` (host[:port], no userinfo). `None ↦ none/""` per mapping.md |
| `if authority = "" then (swap path/authority)` | `if not netloc: netloc, path = path, netloc` | I | empty-authority swap; a no-op in the modeled domain (`authority0 ≠ ""`) |
| `match auth with some a => if a ≠ "" then authority := a ++ "@" ++ authority` | `if auth: netloc = '@'.join([auth, netloc])` (POST-PATCH) | A-reference | the EDITED op: re-attach userinfo to the front of the authority. Python truthy `auth` ↦ `some a ∧ a ≠ ""`; `'@'.join([a,b])` ↦ `a ++ "@" ++ b`. Modeled deeply; validated == real callee by G-CONF |
| `let scheme := match scheme0 with none => newScheme | some s => s` | `if scheme is None: scheme = new_scheme` | I | scheme defaulting |
| (path already `""` for absent path via the `or ''` bridge) | `if path is None: path = ''` | I | path defaulting folded into the `None ↦ ""` input bridge |
| `assembleUrl scheme authority path query fragment` | `urlunparse((scheme, netloc, path, '', query, fragment))` | R | std-lib URL un-splitter (truthy-scheme, truthy-authority arm) reproduced concretely: `//authority`, leading-`/` for a non-empty path lacking one, `?query`/`#fragment` for non-empty parts, empty `params`. Validated end-to-end by G-CONF |
| `return …` | `return urlunparse(...)` | R | returned URL ↦ `String` (verbatim equality) |

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the userinfo re-attach clause is omitted (the `match
  auth` step is dropped), exactly the pre-patch code. The carried gold proof of
  `correct_prependScheme` fails to close: for any input with `auth = some a`,
  `a ≠ ""`, the spec's `reassemble` puts `a ++ "@"` in front of the authority
  while the buggy impl does not, so `result = reassemble …` is violated. This is
  the single fixed behavior.
  (FAIL_TO_PASS: `test_prepend_scheme_if_needed[http://user:pass@example.com/path?query-…]`,
  `test_prepend_scheme_if_needed[http://user@example.com/path?query-…]`.)
