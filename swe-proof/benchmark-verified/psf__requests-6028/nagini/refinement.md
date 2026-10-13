# refinement.md — psf__requests-6028

The operation-by-operation correspondence between `model.py`'s implementation
(the `normalize_location` impl region, plus the deep `effective_authority` and
`assembled` models in the `pure` region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated `==` the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fix site — `prepend_scheme_if_needed` (`requests/utils.py:960`)

Gold hunk (inserted just before the `if scheme is None:` block):
```
+    if auth:
+        # parse_url doesn't provide the netloc with auth
+        # so we'll add it ourselves.
+        netloc = '@'.join([auth, netloc])
```

The surrounding body (unchanged) parses the location into components, reads
`netloc = parsed.netloc` (host[:port], **without** userinfo), optionally swaps
netloc/path, defaults scheme/path, and re-assembles with
`urlunparse((scheme, netloc, path, '', query, fragment))`.

| # | model.py impl op (`normalize_location`) | patch.diff / body op | tag | justification |
|---|---|---|---|---|
| A1 | params `scheme, creds, authority, path, query, frag: List[int]` | the components `scheme, auth, host, port, path, query, fragment = parse_url(url)` and `netloc = parsed.netloc` | R | `str` components ↔ `List[int]` code points; `auth`↔`creds`, `parsed.netloc`↔`authority`, `fragment`↔`frag` (mapping.md §1, §2, §2.1). `parse_url` is the UNCHANGED decomposition (mapping.md §3.1); its outputs are the model's inputs. |
| A2 | `has_creds` boolean param | the truthiness test `if auth:` | R | a present non-empty userinfo ⇔ `has_creds and len(creds)>0`; absent userinfo (`None`/`''`) ⇔ `has_creds == False` (mapping.md §2). |
| A3 | `if has_creds: netloc = creds + [64] + authority` ; pinned as `ToSeq(netloc) == effective_authority(...)` | `if auth: netloc = '@'.join([auth, netloc])` | A-reference | the CHANGED operation, modelled **deeply**: `effective_authority` (pure region) spells out the join (`creds + '@' + authority`, `'@'` = 64). There is no consumed join axiom; the proof uses the deep model, validated `== '@'.join` out-of-band by G-AX (axiom_check.py). For a two-element list `'@'.join([a,b]) == a+'@'+b` (mapping.md §3.2). |
| A4 | `base = scheme + [58,47,47] + netloc + path` ; `if has_query: result = base + [63] + query` ; `if has_frag: result = result + [35] + frag` ; pinned as `ToSeq(result) == assembled(...)` | `urlunparse((scheme, netloc, path, '', query, fragment))` | A-reference | the UNCHANGED combining callee `urllib.parse.urlunparse`, modelled **deeply**: `assembled` (pure region) spells out the `urlunsplit` reduction for this regime — `scheme '://' netloc path` (+`'?'query`) (+`'#'fragment`). Validated `== urlunparse` by G-AX (mapping.md §3.3). `'://'`↔`[58,47,47]`, `'?'`↔`[63]`, `'#'`↔`[35]`. |
| A5 | scheme/path defaulting: handled at the component boundary (the model receives the already-defaulted `scheme`/`path`) | `if scheme is None: scheme = new_scheme` / `if path is None: path = ''` | R | observationally inert on the discriminating (userinfo) inputs — those carry a present scheme and a `'/'`-path; the end-to-end check (axiom_check.py) drives the real defaulting. The netloc/path swap (`if not netloc:`) likewise does not fire when userinfo is present (mapping.md §2.1). |

The discriminating content of the change — the userinfo surviving into the
re-assembled authority — lives in `effective_authority(creds, authority, True)
== creds + PSeq(64) + authority` (model) ⇔ the inserted `netloc =
'@'.join([auth, netloc])` (real). The pre-patch body assembled from the bare
`netloc` (no userinfo); `model_prepatch.py` reproduces that (it omits the
`has_creds` branch, leaving `netloc = authority`) and **fails** the
postcondition `ToSeq(Result()) == assembled(..., effective_authority(...), ...)`
— exactly the spec sensing the change (G-DIFF). The two new F2P URLs
(`http://user:pass@example.com/path?query`, `http://user@example.com/path?query`)
are precisely the inputs on which pre- and post-patch differ.

## B. No kind-3 (inexpressible-changed-op) steps

Every step above is R, A, or I. The one operation that genuinely *changed* — the
credential `'@'`-join that keeps the userinfo in the authority — is modelled
**deeply** (`effective_authority`, step A3, an **A-reference**), not hidden
behind an axiom about the function under change. There are **no consumed
axioms** (`axioms` region empty): the combining callee `urlunparse` is also an
**A-reference** deep model (step A4, validated by G-AX), and the decomposition
callee `parse_url` is unchanged and supplies the component inputs (mapping.md
§3.1).

## C. verify(model) ⇒ resolved

`normalize_location` verifies only if its output equals the assembly over the
**effective authority** (A3 + A4) — i.e. only if the userinfo is re-attached
when present. By R (str ↔ List[int], the component decomposition, scheme/path
defaulting, the netloc/path swap inert on userinfo inputs) the verified function
equals `urlunparse((scheme, '@'.join([auth, netloc]), path, '', query,
fragment))` on the tested inputs; by G-AX the deep models `effective_authority`
and `assembled` equal the real `'@'.join` and `urlunparse` (A-references), and
the whole modelled pipeline reproduces the real post-patch
`prepend_scheme_if_needed` over the F2P/P2P URLs + 5000 fuzz. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: axiom/deep-model soundness (G-AX)
and refinement fidelity (this document, G-EQ).
