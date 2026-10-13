# refinement.md — psf__requests-1142

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `contentLength` `do` block and the `announcedSize`/`Payload` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

There are **no axioms and no A-reference callees** in this bundle: the changed
operation is an inline control-flow decision over the request payload shape and a
single boolean method property, not a call into an unchanged repository or stdlib
callee whose result is read back opaquely. It is modeled **deeply** as concrete
R/I ops. Hence G-AX skips (no `axiom_check.py`), and every impl-region step below
is R or I — G-CONF carries the full refutation burden.

## A. The announcement site — `prepare_content_length()` (`requests/models.py:387`)

Gold hunk:
```
     def prepare_content_length(self, body):
-        self.headers['Content-Length'] = '0'
         if hasattr(body, 'seek') and hasattr(body, 'tell'):
             body.seek(0, 2)
             self.headers['Content-Length'] = str(body.tell())
             body.seek(0, 0)
         elif body is not None:
             self.headers['Content-Length'] = str(len(body))
+        elif self.method not in ('GET', 'HEAD'):
+            self.headers['Content-Length'] = '0'
```

Pre-patch, `Content-Length: '0'` is written **unconditionally up front** and then
overwritten only by the seekable / measurable branches — so a request with no
payload (`body is None`) always announces `'0'`, even for a method that
conventionally carries no entity body. Post-patch, the leading unconditional
write is removed and the zero is announced in a **final `elif`** that fires only
when the method is body-carrying; a body-less request whose method conventionally
has no body now announces **nothing** (no `Content-Length` header).
`contentLength`/`announcedSize` model exactly this announcement decision.

| # | Solution.lean impl op (`contentLength`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `payload : Payload` | the branch dispatch on `body` (`hasattr seek&tell` / `body is not None` / `body is None`) | R | the `body` argument ↔ `Payload` shape (mapping.md §2): file-like ↔ `seekable n`, in-memory buffer ↔ `measurable n`, `None` ↔ `absent`. G-CONF bridges via the real method's branch structure. |
| A2 | parameter `carriesBody : Bool` | `self.method not in ('GET', 'HEAD')` | R | the single touched projection of `self.method` ↔ the boolean `carriesBody` (mapping.md §2/§2.1). G-CONF instantiates it over GET, HEAD, and body-carrying methods. |
| A3 | `match payload \| .seekable n => some n` | `if hasattr(body,'seek') and hasattr(body,'tell'): body.seek(0,2); ...['Content-Length']=str(body.tell()); body.seek(0,0)` | I | the seekable branch announces the queried size `n`. The seek/tell mechanics are unchanged code (I-bridge, §B) that *obtains* `n`; the announcement `some n` ↔ header `str(n)` is transliterated 1:1 by G-CONF. |
| A4 | `\| .measurable n => some n` | `elif body is not None: ...['Content-Length']=str(len(body))` | I | the in-memory branch announces the measured size `n`. `len(body)` is unchanged code obtaining `n`; the announcement `some n` ↔ header `str(n)` transliterated 1:1. |
| A5 | `\| .absent => if carriesBody then some 0 else none` | `elif self.method not in ('GET','HEAD'): ...['Content-Length']='0'` (and otherwise no write) | I | the no-payload branch announces `'0'` (`some 0`) only for a body-carrying method, and attaches **no** header otherwise (`none` ↔ `'Content-Length' not in headers`). This is the changed decision. |
| A6 | `out : Option Nat` returned | the resulting state of `self.headers['Content-Length']` (present `str(n)` vs absent) | R | `some n` ↔ header value `str(n)`; `none` ↔ header absent (mapping.md §2). `Content-Length` is the only header this method writes, so absence is observable as `'Content-Length' not in headers` — exactly the F2P assertion. |

Discriminating content of the change — a no-payload request whose method
conventionally carries no entity body must announce **nothing**, not `'0'` —
lives in `announcedSize .absent false = none` (model) ⇔ the absence of any
`['Content-Length']` write when `self.method in ('GET','HEAD')` (real). The
pre-patch code announced `'0'` unconditionally for this case;
`Solution_prepatch.lean` reproduces that (a leading `some 0` that the `absent`
branch leaves untouched) and **fails** `out = announcedSize payload carriesBody`
exactly on `payload = .absent, carriesBody = false` (the unsolved goal
`carriesBody = true`) — i.e. the `requests.Request('GET'|'HEAD', ...).prepare()`
scenario the F2P `test_no_content_length` exercises (G-DIFF).

## B. The unchanged size-obtaining mechanics (I-bridge, not a modeled op)

The seek-to-end / `tell()` / seek-to-start dance and the `len(body)` measurement
are **unchanged** upstream code: they compute the byte count `n` for a present
payload. They are NOT modeled as ops in `Solution.lean` (the carrier `Payload`
records the resulting `n` directly); G-CONF reconstructs them faithfully as the
I-bridge that produces a real `body` object of each shape so the differential
exercises the announcement decision in its real calling context. No axiom is
needed because no value is read back from an opaque callee — `body.tell()` /
`len(body)` are concrete in-memory measurements the bridge performs directly.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
announcement decision for a no-payload request (announce `'0'` only for a
body-carrying method, else nothing) — is modeled **deeply** (the spelled-out
`announcedSize` with the `if carriesBody then some 0 else none` case, step A5,
I), not hidden behind an axiom: there is no consumed axiom and no A-reference.
The change is an inline control-flow restructure over an in-memory object, so it
has no callee to axiomatize.

## D. verify(Solution) ⇒ resolved

`contentLength` verifies only if its output equals `announcedSize` exactly —
in particular `none` (no header) for `payload = .absent, carriesBody = false`
(A5) and the queried/measured size for a present payload (A3/A4). By R (the
`body`-shape ↔ `Payload` bijection §2; the `Option Nat` ↔ header present/absent
bijection §2, A6; the method membership ↔ `carriesBody`, A2) the verified
decision equals the gold `prepare_content_length`'s header state on the tested
inputs; by G-CONF the R/I transliteration of `announcedSize` — composed with the
faithful I-bridge for the unchanged size-obtaining mechanics — agrees with
`patch.diff`'s real `prepare_content_length` on ≥10⁵ fuzzed `(body, method)`
inputs (incl. the issue's body-less GET and the F2P's body-less HEAD). Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement fidelity (this doc, G-EQ + G-CONF); there is no
axiom-soundness trust point because the bundle carries no axioms.
