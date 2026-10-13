# refinement.md — psf__requests-6028

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildAuthority` `do` block + the `assembleAuthority` / `authorityBase` deep
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — A-consumed / A-reference), or **I**
(identical concrete op). This bundle has **no A steps**: the authority string is
computed entirely from the parsed slots, so every step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — `prepend_scheme_if_needed` (`requests/utils.py:960`)

Gold hunk:
```
     if not netloc:
         netloc, path = path, netloc

+    if auth:
+        # parse_url doesn't provide the netloc with auth
+        # so we'll add it ourselves.
+        netloc = '@'.join([auth, netloc])
     if scheme is None:
         scheme = new_scheme
```

The function's surrounding glue is: `parsed = parse_url(url)`; unpack
`scheme, auth, host, port, path, query, fragment`; `netloc = parsed.netloc`;
the swap; **(the patched authority rebuild)**; scheme/path defaults;
`return urlunparse((scheme, netloc, path, '', query, fragment))`. The modeled
slice is the authority value `netloc` flowing into `urlunparse`.

| # | Solution.lean impl op (`buildAuthority`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `userinfo : List Char` | `auth` (2nd slot of `parse_url(url)`) | R | `Optional[str]` credentials ↔ `List Char` (`None`/`''` ↔ `[]`); mapping.md §2. |
| A2 | param `authoritySlot : List Char` | `parsed.netloc` | R | `Optional[str]` ↔ `List Char`; mapping.md §2. |
| A3 | param `fallbackSlot : List Char` | `path` (5th slot of `parse_url(url)`) | R | `Optional[str]` ↔ `List Char`; mapping.md §2. |
| A4 | `base := if authoritySlot = [] then fallbackSlot else authoritySlot` | `if not netloc: netloc, path = path, netloc` (the netloc-side of the swap) | I | identical fallback: when the authority slot is falsy the host portion is taken from the path slot; `if not netloc:` ↔ `authoritySlot = []` (mapping.md §2). |
| A5 | guard `userinfo = []` | `if auth:` | I | identical decision; Python `str` falsy iff empty, so `if auth:` ↔ `userinfo ≠ []` (mapping.md §2). |
| A6 | `userinfo ++ ['@'] ++ base` | `netloc = '@'.join([auth, netloc])` | I | `'@'.join([auth, netloc])` ↔ `userinfo ++ ['@'] ++ base`; the single `@` separator ↔ `['@']` (mapping.md §2). |
| A7 | else branch returns `base` unchanged | (no `auth` branch taken; `netloc` left as the swap result) | I | identity when no credentials are present. |

Discriminating content of the change — when credentials are present they are
folded back into the authority (`userinfo ++ ['@'] ++ base`, A5/A6); when absent
the host portion stands alone (A7) — lives in the `userinfo = []` guard and the
`@`-join. `Solution_prepatch.lean` reproduces the pre-patch bug (authority is
just the resolved host portion; credentials never folded back) and **fails**
`out = assembleAuthority userinfo (authorityBase authoritySlot fallbackSlot)` (G-DIFF)
precisely on the `userinfo ≠ []` leg — the proxy-credentials loss the issue
reports.

## B. The surrounding glue (shipped, not separately modeled)

The rest of `prepend_scheme_if_needed` (`parse_url`, the unpack, the `path`-side
of the swap, the scheme/path defaults, the final `urlunparse`) is **unchanged by
the patch**. It is exercised end-to-end by G-CONF: the conformance shadow runs
the real `parse_url` and the real `urlunparse`, with the verbatim swap/defaults
glue, around the R/I transliteration of `buildAuthority`. It carries no
behaviour the patch changed, so no second `method` and no
`Solution_prepatch_<k>.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — re-folding the
credentials into the authority — is modeled **deeply** (the spelled-out
`assembleAuthority` string computation, steps A5-A7), not hidden behind an axiom
about the function under change. There are **no axioms** in this bundle
(`axioms = []`, `deep_model_references = []`): nothing is delegated to an
unchanged callee inside the modeled slice, so `axiom_check.py` is a skip
(G-AX = skip). The two bracketing callees `parse_url`/`urlunparse` are unchanged
and run live in G-CONF, not axiomatized.

## D. verify(Solution) ⇒ resolved

`buildAuthority` verifies only if its output equals the exact authority decision:
prepend `userinfo` + `@` to the host portion precisely when credentials are
present, identity otherwise (A5-A7), where the host portion is the swap fallback
(A4). By R (`str ↔ List Char`, `None`/`''` ↔ `[]`, `'@'.join` ↔ `++ ['@'] ++`)
the verified builder equals the authority that the patched
`prepend_scheme_if_needed` feeds to `urlunparse` on every input; by G-CONF the
R/I transliteration, wrapped in the real `parse_url`/`urlunparse` callees, agrees
with `patch.diff`'s observable output on ≥10⁵ inputs (the patched real function
as oracle, restricted to its own non-raising domain — mapping.md §3.1). The F2P
pair (`test_prepend_scheme_if_needed[http://user:pass@…]`, `[http://user@…]`)
demands exactly credentials-preservation, which this spec pins (G-RESOLVE).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms
to trust (G-AX = skip).
