# refinement.md — django__django-10097

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `validateAuthsegment` impl region and the deep `accepts` /
`bodyOk` / `colons` / `isUchar` model) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-reference** (a deep model validated
`== ` the real callee/matcher by axiom_check.py / G-AX), **A-consumed** (the
proof uses an axiom's contract), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed hunk — the user:pass authentication group

Gold hunk (`django/core/validators.py:97`):
```
-        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
+        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
```

The change narrows the authentication character class from `\S` (any
non-whitespace) to `[^\s:@/]` (non-whitespace AND none of the three separators
`:`, `@`, `/` that RFC 1738 §3.1 requires to be percent-encoded).
`Solution.lean`'s `validateAuthsegment` decides exactly whether the
authentication segment — the content the group must full-match, i.e. the text
before the terminating `@` — is well-formed.

| # | Solution.lean impl op (`validateAuthsegment`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `seg : List Char` | the authentication segment, a substring of `str(value)` | R | `str` ↔ `List Char` code points (mapping.md §2). |
| A2 | `n = 0 → return false` | the body requires at least one char (`[^\s:@/]+`, a `+` quantifier); the empty wrapper alternative `(?:...@)?` is a *different* match (no segment), not an empty segment | I | a zero-length segment cannot full-match the `+`-quantified group. |
| A3 | the returned conjunct `seg[0]!.toNat != 58` (no leading `:`) | the leading `[^\s:@/]+` user run is non-empty, so the segment cannot start with the separator `:` | I | the user run before the optional `:` is mandatory. |
| A4 | the backward loop computing `good = bodyOk (...)` (every char is `isUchar` or `:`) and `ncolon = colons (...)`, returning `good ∧ ncolon ≤ 1 ∧ …` | the compiled group `[^\s:@/]+(?::[^\s:@/]*)?` full-matching the segment | A-reference | the changed matching operation is modeled **deeply**: `accepts`/`bodyOk`/`colons`/`isUchar` (the `pure` region) and the verified loop in `validateAuthsegment` ARE the acceptance predicate. There is **no consumed matcher axiom** — the proof never depends on one. The deep model is validated **== the real compiled group** out-of-band: G-AX (axiom_check.py) compiles `[^\s:@/]+(?::[^\s:@/]*)?` (re.IGNORECASE) and asserts `accepts == group.fullmatch` on 188 boundary + a programmatic per-code-point sweep over the full 29-code-point Unicode-whitespace class + 100k fuzz (alphabet includes the full whitespace block). `isWhitespace` excludes the **entire** Unicode `\s` class, so the equivalence is universal, not ASCII-only. mapping.md §3.1 proves the characterization (non-empty; only authentication chars apart from ≤1 separator colon; no leading colon). |

The discriminating content of the change — `:`, `@`, `/` (and a second `:`) are
no longer accepted inside the segment — lives in `isUchar` excluding 58/64/47
and in `colons s ≤ 1` (model) ⇔ the `[^\s:@/]` class + single optional `:`
(real). The pre-patch body `\S+(?::\S*)?` excluded only whitespace;
`Solution_prepatch.lean` reproduces that (a whitespace-only check) and **fails**
the postcondition `ok = accepts seg` — exactly the spec sensing the change
(G-DIFF). Its failing segments are precisely the issue's examples (`foo/bar`,
`foo@bar`, `foo:bar:baz`, `foo:bar/baz`, …), which the old regex accepts but the
new one rejects.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the authentication character-class/structure matcher — is modeled
**deeply** (the spelled-out per-code-point fold `bodyOk`/`colons` consumed in
`validateAuthsegment`, step A4, an **A-reference**), not hidden behind an axiom
about the function under change. There is **no consumed axiom** in this bundle:
the changed matcher is the A-reference G-AX validates the deep model against, and
there is no unchanged stdlib callee the new code newly invokes. (The surrounding
whole-URL pattern, `_lazy_re_compile`, and `str(value)` are unchanged by the
patch and are not part of the modeled behavior; the patch edits only the one
regex literal — the user:pass authentication group.)

## C. verify(model) ⇒ resolved

`validateAuthsegment` verifies only if its decision equals the exact acceptance
predicate `accepts` (A4) — non-empty, ≤1 separator colon, no leading colon, and
every other code point an authentication character (no `:`/`@`/`/`/whitespace).
By R (str ↔ List Char) the verified decision equals a full match of the
gold-patch authentication group on the tested `str` segments; by G-AX the deep
model `accepts` equals the real compiled group `[^\s:@/]+(?::[^\s:@/]*)?` over
188 boundary + a full per-code-point Unicode-whitespace sweep + 100 000 fuzz
inputs (A-reference), the equivalence being universal because `isWhitespace`
covers the entire Unicode `\s` class. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited matcher — and the gold patch resolves (G-RESOLVE: the validator now
rejects `http://foo/bar@example.com` and the other added invalid URLs, and still
accepts the rewritten valid encoded URL). The trust points are exactly matcher
soundness (G-AX) and refinement fidelity (this document, G-EQ).
