# refinement.md — django__django-14404

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `appendSlashRedirect` `do` block and the deep `fullPath` / `redirectTarget`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The redirect-destination change — `catch_all_view` (`django/contrib/admin/sites.py:423,430`)

Gold hunk:
```
-            path = '%s/' % request.path_info
             try:
-                match = resolve(path, urlconf)
+                match = resolve('%s/' % request.path_info, urlconf)
             except Resolver404:
                 pass
             else:
                 if getattr(match.func, 'should_append_slash', True):
-                    return HttpResponsePermanentRedirect(path)
+                    return HttpResponsePermanentRedirect('%s/' % request.path)
```

The change has two textual edits but **one** behavioural effect: the value
**returned to the client** (the `HttpResponsePermanentRedirect` argument) is now
built from `request.path` (full, prefix-including) instead of `request.path_info`
(local only). The other edit merely inlines the unchanged `'%s/' % request.path_info`
expression into the `resolve(...)` call — the URL **resolution** still keys off the
local path (correct: the URLconf is local), so the modeled function is precisely the
**redirect destination**, the only observable that changes.

| # | Solution.lean impl op (`appendSlashRedirect`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `mountPrefix : List Char` | the deployment mount-point prefix `script_name.rstrip('/')` that `request.path` carries but `request.path_info` does not (`wsgi.py:75`) | R | `script_name.rstrip('/')` (str) ↔ `mountPrefix` (List Char); empty ⇔ root mount. mapping.md §2. G-CONF/G-AX derive it from a real request. |
| A2 | param `localPath : List Char` | the per-request local path `request.path_info` (`wsgi.py:71`) | R | `request.path_info` (str) ↔ `localPath` (List Char). mapping.md §2. |
| A3 | `fullPath mountPrefix localPath = mountPrefix ++ localPath` | `request.path` (`'%s/%s' % (script_name.rstrip('/'), path_info.replace('/','',1))`, wsgi.py:75-76) | A-reference + I | the request's full path is modeled **deeply** as the concatenation of the two carriers; the `++` is **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `request.path` is the **A-reference** G-AX validates (mapping.md §3.1). The leading-slash bookkeeping of the `'%s/%s'` template is discharged in mapping.md §2. |
| A4 | `result := fullPath … ++ ['/']`; `return result` | `'%s/' % request.path`, wrapped by `HttpResponsePermanentRedirect` | I + R | the `'%s/'` template appends exactly one `'/'` (**I**, concrete, transliterated by G-CONF); `HttpResponsePermanentRedirect` is identity on the destination string the F2P tests compare (**R**, mapping.md §2). The destination is built from the FULL path — the behaviour the issue + F2P tests demand. |

Discriminating content of the change — **the mount-point prefix is preserved in
the redirect destination** — lives in `out = mountPrefix ++ localPath ++ ['/']`
and the frame clause `∃ rest, out = mountPrefix ++ rest` (model) ⇔ building the
destination from `request.path` rather than `request.path_info` (real). The
pre-patch `'%s/' % request.path_info` produced only `localPath ++ ['/']`;
`Solution_prepatch.lean` reproduces that (`result := localPath ++ ['/']`) and
**fails** `out = redirectTarget mountPrefix localPath` exactly on the prefix:
the unsolved goal reduces to `mountPrefix = []`, false whenever the application
is served under a non-empty mount point (the F2P `SCRIPT_NAME` /
`FORCE_SCRIPT_NAME='/prefix/'` cases) — G-DIFF.

## A.1 Termination semantics

The file uses `loom.semantics.termination "total"` (total correctness). The
real changed code is a straight-line string format (`'%s/' % request.path`)
that always terminates and returns, and the F2P tests observe the returned
redirect destination, so total correctness is the faithful semantics. Partial
correctness would admit a same-spec implementation that diverges (an infinite
loop vacuously satisfies every `ensures`) — a wrong impl the tests would
fail — so it would leave the spec too weak.

## B. No consumed axioms

There are no `axiom`s the proof consumes. The request's full path is an
unchanged framework attribute; rather than axiomatize it, it is modeled
**deeply** (the spelled-out `fullPath`, step A3, an A-reference + I) and
validated against the real `request.path` by G-AX. No dead axioms are shipped.
The unchanged URL resolver (`resolve`) is **not** modeled at all: it gates
*whether* a redirect fires, not *what* destination it carries, and the gold
change leaves the resolution input (`'%s/' % request.path_info`) behaviourally
identical — so it is outside the modeled redirect-destination expression.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The changed expression is expressible as a finite
character-list concatenation; nothing required a kind-3 escape hatch.

## D. verify(Solution) ⇒ resolved

`appendSlashRedirect` verifies only if its output equals the exact assembly
`redirectTarget` — the FULL path (mount prefix ++ local path) plus a single
trailing slash (A3–A4), with the prefix provably preserved (`∃ rest, out =
mountPrefix ++ rest`). By R (`script_name.rstrip('/')` ↔ `mountPrefix`,
`request.path_info` ↔ `localPath`, `HttpResponsePermanentRedirect` identity on
the destination string) the verified assembly equals `'%s/' % request.path` on
the tested inputs; by G-AX the deep model `fullPath` equals the real
`request.path` (A-reference); by G-CONF the R/I transliteration of the assembly
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model attribute — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
