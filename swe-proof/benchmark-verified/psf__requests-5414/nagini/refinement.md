# refinement.md — psf__requests-5414

The operation-by-operation correspondence between `model.py`'s implementation
(the `screen_host` impl region plus the live `encode_label` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`/`Exsures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The patch edits the host-validation slice of `PreparedRequest.prepare_url` in
`requests/models.py`: it widens the leading-code-point rejection in the ASCII
`elif` branch from the single prefix `'*'` to the prefix set `('*', '.')`.

Gold hunk:
```
             try:
                 host = self._get_idna_encoded_host(host)
             except UnicodeError:
                 raise InvalidURL('URL has an invalid label.')
-        elif host.startswith(u'*'):
+        elif host.startswith((u'*', u'.')):
             raise InvalidURL('URL has an invalid label.')
```

## A. The leading-code-point screen — `prepare_url` host slice (`models.py:401-407`)

| # | model.py impl op (`screen_host`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `host: List[int]` | the `host` local in `prepare_url` (a `str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). `str` indexing is banned in Nagini; the test reads `host[0]` ↔ the first code point. The slice is reached only after the empty-host rejection (`if not host: raise`), so `host` is non-empty ↔ the precondition `len(host) > 0`. |
| A2 | `if not host_is_ascii: encode_label(encodable)` | `if not unicode_is_ascii(host): host = self._get_idna_encoded_host(host) (except UnicodeError: raise InvalidURL(...))` | R + A-consumed | the ASCII predicate `unicode_is_ascii(host)` is refined to the branch-selector bit `host_is_ascii` (R, mapping.md §3.2); the IDNA branch's call `_get_idna_encoded_host` is the unchanged callee abstracted by the `encode_label` axiom (A-consumed, mapping.md §3.1). The `try/except UnicodeError → InvalidURL` is folded into the axiom's `Exsures(InvalidLocator, encodable is False)`. This whole branch is UNCHANGED by the patch and identical pre/post-patch. |
| A3 | `elif is_invalid_leading(host[0]): raise InvalidLocator()` | `elif host.startswith((u'*', u'.')): raise InvalidURL('URL has an invalid label.')` | R + I | `host.startswith((u'*', u'.'))` is truthy ⟺ the first character is `'*'` or `'.'` ⟺ `is_invalid_leading(host[0])` with `is_invalid_leading(c) ≡ c∈{42,46}` (each single-character prefix reduces `startswith` to a first-code-point comparison; mapping.md §2). The explicit `host[0]` comparison is the type-refined spelling of the prefix-set membership test; the decision (reject-or-not) is the identical concrete branch. The raise `InvalidLocator` ↔ `InvalidURL` (R: user-defined exception stands in for the builtin-carrying error; only raise/no-raise observed). |

The discriminating content of the change: post-patch the ASCII branch rejects a
host whose first code point is `'.'` (46) on equal footing with `'*'` (42),
whereas pre-patch it rejected only `'*'`. That is exactly the issue's scenario —
`http://.example.com` (host `.example.com`, which is ASCII) must raise
`InvalidURL` rather than slipping through.

`model_prepatch.py` reproduces the literal pre-patch test (`host[0] == 42`
only, i.e. `host.startswith(u'*')`) and **fails** verification on the
normal-completion postcondition
`Implies(host_is_ascii, not is_invalid_leading(host[0]))`: for an ASCII host
beginning with `'.'` (`host[0] == 46`), the pre-patch returns normally instead
of raising, which the spec forbids. The verifier reports the failure on exactly
this clause (`Postcondition of screen_host … Implies(host_is_ascii, … not
is_invalid_leading(host[0])) might not hold`). That is the spec sensing the
change (G-DIFF).

## A.1 Termination (total correctness)

The spec carries `Requires(MustTerminate(2))` on `screen_host` and the strictly
smaller `Requires(MustTerminate(1))` on the `encode_label` axiom. The real host
slice is bounded, straight-line code that always answers (returns normally or
raises `InvalidURL`) before `prepare_url` continues, and the real
`_get_idna_encoded_host` is a bounded call that always answers (total over
{return str, raise UnicodeError}, G-AX) — so the obligation is faithful, not an
over-strengthening. Nagini is a partial-correctness verifier by default; without
the obligation a diverging implementation (bare self-recursion, an endless
loop) satisfies every `Ensures`/`Exsures` vacuously and verifies — the
spec-too-weak wrong-impl class recorded by G-PANEL-1, which this obligation
closes. Verified against both attack shapes during repair (self-call rejected:
"Callee screen_host might not take all unsatisfied obligations"; unbounded loop
rejected: "Loop might not take all unsatisfied obligations from the context"),
while the gold impl and the branch-reorder/inline positive controls still
verify (the encoder call's measure 1 < 2 is admitted).

## A.2 Spec completeness (echo-shaped attacks are positive controls)

On the modeled domain (non-empty host × the two callee-verdict bits) the
contract is a COMPLETE input/output relation: the `Ensures`/`Exsures` pair
fixes, for every admissible input, exactly whether `screen_host` returns
normally or signals the rejection, and `is_invalid_leading` is a transparent
`@Pure` predicate (its body is the whole membership test), not an opaque
answer-key. Any same-spec implementation that verifies is therefore
behaviourally equal to the pinned behaviour on every admissible input — a
restructured/branch-reordered equivalent, or one that consults the pure
predicate directly, is a positive control, not a spec-too-weak
counterexample. Genuinely wrong implementations are rejected: checked during
repair — reject-only-46 / reject-nothing / reject-everything on the ASCII
branch, an out-of-contract rejection on the non-ASCII branch, bare
self-recursion and an endless loop (the last two via `MustTerminate`, §A.1)
all fail verification, while the gold-shaped impl and its reorderings verify.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the
widening of the leading-code-point rejection from `'*'` to `('*', '.')` — is
modelled **directly** as the explicit first-code-point membership test `host[0]
∈ {42,46}` (A3), a refinement of `host.startswith((u'*', u'.'))`, NOT hidden
behind an axiom about the function under change. The only consumed axiom,
`encode_label` (**A-consumed**), covers the **unchanged** IDNA encoder the
sibling branch defers to — never the operation under change. There is no
**A-reference** deep model and no dead axiom: the axiom's `Ensures`/`Exsures`
are consumed by `screen_host`'s postcondition on the non-ASCII path.

## C. verify(model) ⇒ resolved

`screen_host` verifies only if (a) on an ASCII host it raises EXACTLY when the
first code point is `'*'` or `'.'` (A3) — so a host beginning with `'.'` is
rejected on equal footing with `'*'` — and (b) on a non-ASCII host it defers
exactly to the encoder verdict (A2). By R (`str` ↔ `List[int]`,
`startswith((u'*',u'.'))` ↔ the first-code-point disjunction, `unicode_is_ascii`
↔ `host_is_ascii`, `InvalidURL` ↔ `InvalidLocator`) the verified screen equals
the gold `elif host.startswith((u'*', u'.')): raise InvalidURL(...)` placed after
the unchanged IDNA branch; by G-AX the real `_get_idna_encoded_host` meets the
`encode_label` axiom (A-consumed). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
