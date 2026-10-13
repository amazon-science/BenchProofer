# refinement.md — psf__requests-5414

The operation-by-operation correspondence between `Solution.lean`'s
`validateAsciiHostLabel` impl region (plus the `startsWithInvalidLabel` /
`hostAccepted` deep model and the `isAsciiHost` A-reference) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; bijection stated),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The leading-label guard — `prepare_url` (`requests/models.py:401-407`)

Gold hunk:
```
                 host = self._get_idna_encoded_host(host)
             except UnicodeError:
                 raise InvalidURL('URL has an invalid label.')
-        elif host.startswith(u'*'):
+        elif host.startswith((u'*', u'.')):
             raise InvalidURL('URL has an invalid label.')
```

Surrounding (unchanged) context at base_commit:
```
        if not host:
            raise InvalidURL("Invalid URL %r: No host supplied" % url)
        if not unicode_is_ascii(host):
            try:
                host = self._get_idna_encoded_host(host)
            except UnicodeError:
                raise InvalidURL('URL has an invalid label.')
        elif host.startswith(u'*'):          # <- changed line
            raise InvalidURL('URL has an invalid label.')
```

| # | Solution.lean impl op (`validateAsciiHostLabel`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `host : List Char` parameter | `host: str` (the parsed host) at `models.py:401-406` | R | `str` ↔ `List Char` of code points (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `require host.length > 0` | the earlier guard `if not host: raise InvalidURL(...)` (`models.py:394`) | R | a host reaching the `elif` has already passed the non-empty guard. `not host` (str falsiness) ↔ `host.isEmpty`; the contract restricts to `host.length > 0`. Not modeled as an op; carried as a precondition. |
| A3 | `require isAsciiHost host = true` | the branch selector `if not unicode_is_ascii(host): … elif …` (`models.py:401`) | A-reference | the `elif` the patch changes is reached **only** on the all-ASCII branch. `isAsciiHost` deeply models `unicode_is_ascii` (mapping.md §3.1) and scopes the decision to that branch. Validated `isAsciiHost == unicode_is_ascii` by G-AX (axiom_check.py); the proof carries it opaquely (never unfolds it), so it is an A-reference, not a consumed axiom. |
| A4 | `let startsBad := host.head? == some '*' \|\| host.head? == some '.'` then `return !startsBad` | `host.startswith((u'*', u'.'))` → `raise InvalidURL(...)`; fall-through otherwise | R + I | **the changed op.** `s.startswith((u'*', u'.'))` for two one-character prefixes ↔ "`s[0] == '*'` or `s[0] == '.'`" ↔ `host.head? == some '*' \|\| host.head? == some '.'` (mapping.md §2). The boolean combination and `head?` test are **I** (concrete, transliterated by G-CONF). `out = true` (accept) ↔ the guard does not fire (prepare_url proceeds); `out = false` (reject) ↔ the guard fires and `InvalidURL` is raised. |
| A5 | `out = true` (the `return` value when the guard does not fire) | falling through the `elif` to "Carefully reconstruct the network location …" (`models.py:409+`) | R | normal continuation of `prepare_url`. The model abstracts the subsequent unchanged URL reconstruction to the accept verdict `true`; the only thing this decision point decides is accept vs reject. `out = false` (reject) ↔ `raise InvalidURL('URL has an invalid label.')` (`models.py:407`); the harness/F2P observes only that `InvalidURL` is raised. |

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — adding `.` to the set of rejected leading code points (A4) — is
modeled **deeply and exactly** (`host.head? == some '.'` is the precise
refinement of the new `u'.'` member of the `startswith` tuple), not hidden
behind an axiom about the function under change. There is **no consumed axiom
and no dead axiom** (the `axioms` region is empty). The only deep-model
reference is `isAsciiHost` (A-reference), which models the **unchanged** branch
selector `unicode_is_ascii`, not the changed op.

The discriminating content of the change is step **A4** — the added `u'.'`
member. The spec senses it through `ensures out = hostAccepted host` with
`hostAccepted host = !(host.head? == some '*' || host.head? == some '.')`: on a
host opening with `.` (and all-ASCII, non-empty — e.g. the F2P input
`.example.com`), `hostAccepted = false`, so any verifying impl must reject it.
The pre-patch guard rejected only `*`; `Solution_prepatch.lean` reproduces that
(`startsBad := host.head? == some '*'`) and **fails** the postcondition: the exit
goal reduces to `(!host.head? == some '*') = hostAccepted host`, unprovable
because for a `.`-leading host the LHS is `true` while `hostAccepted` is `false`.
That is exactly the spec sensing the change (G-DIFF), and exactly the behaviour
the F2P test
`tests/test_requests.py::TestRequests::test_invalid_url[InvalidURL-http://.example.com]`
demands. The companion P2P
`test_invalid_url[InvalidURL-http://*example.com]` is preserved because
`hostAccepted` still rejects a `*`-leading host (the `u'*'` disjunct).

## C. verify(model) ⇒ resolved

`validateAsciiHostLabel` returns `true` (accept) iff the host does not open with
`*` or `.`, and `false` (reject) otherwise (the single `ensures`), over the
non-empty all-ASCII domain the `require`s scope to. Under R (`str` ↔ `List Char`,
`startswith` single-char prefix ↔ `head?` test, `InvalidURL`-raise ↔
`out = false`) this is precisely the post-patch `elif`'s decision: reject a host
opening with `*` or `.` (raise `InvalidURL`), otherwise proceed. The branch
selector that gates this code path (`unicode_is_ascii`, A3) is unchanged and is
validated by G-AX; the non-ASCII IDNA branch is unchanged by the patch and out
of scope. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited A-reference — and the gold
patch resolves (G-RESOLVE). The R/I legs are mechanically refuted by G-CONF
(`conformance_check.py`); the A-reference is audited by G-AX (`axiom_check.py`).
Trust points are exactly the two of plan §1.1: A-reference fidelity (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
