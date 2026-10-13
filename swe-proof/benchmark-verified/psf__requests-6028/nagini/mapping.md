# mapping.md — psf__requests-6028

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0192aac24123735b3eaf9b08df46429bb770c283`, states the type
abstraction, and gives the provenance of each modelled callee (callee source +
the exact behaviour the deep model encodes).

Repo file under change: `requests/utils.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalize_location(scheme, creds, authority, path, query, frag, has_creds, has_query, has_frag)` | `prepend_scheme_if_needed(url, new_scheme)` — `requests/utils.py:960` (body 966-982) | the modeled changed function (location re-assembly that must preserve userinfo) |
| `effective_authority(creds, authority, has_creds)` *(deep model — A-reference)* | `'@'.join([auth, netloc])` — the inserted hunk, `requests/utils.py:977-980` post-patch | pure spec: the credential-join that keeps userinfo in the authority; the CHANGED operation, modeled deeply and validated `== '@'.join` by axiom_check.py (G-AX) |
| `assembled(scheme, authority, path, query, frag, has_query, has_frag)` *(deep model — A-reference)* | `urlunparse((scheme, netloc, path, '', query, fragment))` — `requests/utils.py:982` | pure spec: the location re-assembly; the unchanged combining callee `urllib.parse.urlunparse`, validated `assembled == urlunparse` by axiom_check.py (G-AX) |
| parameters `scheme, creds, authority, path, query, frag, has_creds, has_query, has_frag` | the components unpacked from `parse_url(url)` — `requests/utils.py:966-967,971` (`scheme, auth, host, port, path, query, fragment = parsed`; `netloc = parsed.netloc`) | the parsed components the function body operates on; `auth`↔`creds`, `parsed.netloc`↔`authority`, `fragment`↔`frag` |

The pre-patch behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): the function reconstructed the location
from `parsed.netloc` directly, and `parsed.netloc` (urllib3's `Url.netloc`
property) is `host[:port]` and **does not include the userinfo `auth`**, so the
credentials were dropped from the reconstructed location. The inserted hunk
`if auth: netloc = '@'.join([auth, netloc])` re-attaches them.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` component (`auth`, `netloc`, `scheme`, `path`, `query`, `fragment`) | `List[int]` of Unicode code points | `s[k]` ↔ `comp[k] == ord(s[k])`; `len(s)` ↔ `len(comp)`; `str` `+`/`'@'.join` ↔ list `+` with the `'@'` (64) separator; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `PSeq` `+`/`len`/`[i]` mirror `str` `+`/`len`/index |
| "`auth` is truthy" (`if auth:`) | the boolean `has_creds` | a present, non-empty userinfo ⇔ `has_creds and len(creds) > 0`; an absent userinfo (`parse_url` yields `None`/empty) ⇔ `has_creds == False`. (urllib3 returns `auth=None` when there is no userinfo, and a non-empty `str` when there is; `if auth:` is False on both `None` and `''`.) |
| "`query` is present" | the boolean `has_query` | a present query (`parse_url` yields a non-`None` `query`) ⇔ `has_query`; `urlunparse` appends `'?'+query` exactly when `query` is truthy |
| "`fragment` is present" | the boolean `has_frag` | a present fragment (`parse_url` yields a non-`None` `fragment`) ⇔ `has_frag`; `urlunparse` appends `'#'+fragment` exactly when `fragment` is truthy |
| `'#'` separator | code point `35` | `urlunsplit` emits `url + '#' + fragment` when the fragment is truthy |
| `'@'` separator | code point `64` | `'@'.join([auth, netloc]) == auth + '@' + netloc` for the two-element list |
| `'://'` separator | code points `58, 47, 47` (`':' '/' '/'`) | `urlunsplit` emits `scheme + ':' + '//' + netloc + url` in the regime here (non-empty netloc, present scheme) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

### 2.1 Why the function is modelled over components

The patched hunk operates entirely on the already-parsed COMPONENTS
(`scheme, auth, host, port, path, query, fragment` and `parsed.netloc`), never
on the raw `url` string — `parse_url` (the decomposition) is unchanged by the
patch. The model therefore takes the components as inputs (their provenance is
`parse_url`, §3.1) and reproduces the body's component-level logic: the
credential `'@'`-join (the fix) and the `urlunparse` re-assembly. The netloc/
path swap (`if not netloc: netloc, path = path, netloc`, line 970-971) sits
above the inserted hunk and does not fire when userinfo is present (a userinfo
always comes with a non-empty authority), so it is observationally inert on the
discriminating inputs and is not separately modelled; the end-to-end check in
axiom_check.py exercises the full real body including that branch.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `parse_url` — the unchanged decomposition (provenance of the inputs)
**Callee:** `urllib3.util.parse_url(url)` (`requests/utils.py:24` import).
Returns a `urllib3.util.url.Url` named tuple
`(scheme, auth, host, port, path, query, fragment)` with a `netloc` PROPERTY.
Critically, `Url.netloc == host` (with `:port` appended when a port is present)
and **omits the userinfo `auth`** — this is the urllib3/stdlib `netloc`
definition mismatch the issue is about. `parse_url` is UNCHANGED by the patch;
the model consumes its outputs as component inputs (no consumed axiom). The
end-to-end check in axiom_check.py calls the real `parse_url` to drive the full
pipeline against the real function.

### 3.2 `effective_authority` deep model ↔ `'@'.join([auth, netloc])` (A-reference)
**Callee:** the inserted hunk's credential-join, `'@'.join([auth, netloc])`
(`requests/utils.py:977-980` post-patch). The CHANGED operation is modelled
**deeply** by the `@Pure` `effective_authority`; there is no consumed axiom for
it. For a two-element list `'@'.join([a, b]) == a + '@' + b`, so
`effective_authority(creds, authority, True) == creds + PSeq(64) + authority`
and `effective_authority(_, authority, False) == authority`. G-AX
(axiom_check.py) asserts `effective_authority == '@'.join` over boundary + 20000
fuzz inputs.

### 3.3 `assembled` deep model ↔ `urlunparse` (A-reference)
**Callee:** CPython stdlib `urllib.parse.urlunparse(components)`
(`requests/utils.py:33` import via `requests.compat`), which delegates to
`urlunsplit`. Source (every supported 3.x):

```python
def urlunsplit(components):
    scheme, netloc, url, query, fragment, _coerce_result = _coerce_args(*components)
    if netloc:
        if url and url[:1] != '/': url = '/' + url
        url = '//' + netloc + url
    ...
    if scheme:
        url = scheme + ':' + url
    if query:
        url = url + '?' + query
    if fragment:
        url = url + '#' + fragment
    return _coerce_result(url)
```

In the regime these locations inhabit — non-empty `netloc` (authority), a
present `scheme`, empty `params` (the literal `''` passed at the call site),
and `path` either empty or already beginning with `'/'` (as urllib3 yields) —
this reduces to

  `scheme + '://' + netloc + path` (+ `'?' + query` when `query` is truthy)
  (+ `'#' + fragment` when `fragment` is truthy),

which is exactly what `assembled` encodes (the fragment passes through the
re-assembly unchanged; `parse_url` yields it and the call site forwards it
verbatim). Docs:
https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlunparse.
G-AX asserts `assembled == urlunparse` over boundary + 20000 fuzz inputs (with
the effective authority carrying credentials in half the fuzz, exercising the
post-patch netloc shape).

**Conformance check (G-CONF):** `conformance_check.py` runs the
contract-stripped impl region (shadow) against the real patched
`prepend_scheme_if_needed` in-container over >=1e5 inputs (boundary + 100000
end-to-end fuzz locations bridged through the real `parse_url`, plus 20000
component-level tuples vs the real `'@'.join` + `urlunparse` composition).
Pinned fuzz seed: 6028.

**Soundness check (G-AX):** `axiom_check.py` runs the real stdlib `urlunparse`
and the real `'@'.join` on boundary + 40000 fuzz inputs and asserts both deep
models agree; additionally it drives the WHOLE pipeline (real `parse_url` →
deep models) against the real post-patch `prepend_scheme_if_needed` on the
F2P/P2P URLs and 5000 fuzz URLs, asserting identical output. Core checks import
only stdlib `urllib.parse`; the end-to-end check uses urllib3's unchanged
`parse_url` (present in the eval container). Exit 0 iff sound.
