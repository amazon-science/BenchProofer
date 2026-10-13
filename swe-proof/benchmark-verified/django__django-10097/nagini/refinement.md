# refinement.md — django__django-10097

The operation-by-operation correspondence between `model.py`'s implementation
(the `validate_authsegment` impl region and the deep `accepts` / `body_ok` /
`colons` / `is_uchar` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee/matcher by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed hunk — `URLValidator.regex` userinfo group

Gold hunk (`django/core/validators.py:97`):
```
-        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
+        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
```

The change narrows the userinfo character class from `\S` (any non-whitespace)
to `[^\s:@/]` (non-whitespace AND none of the three RFC-1738 separators that
must be percent-encoded). `model.py`'s `validate_authsegment` decides exactly
whether the authentication segment (the content the userinfo group must
full-match, i.e. the text before the terminating `@`) is well-formed.

| # | model.py impl op (`validate_authsegment`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `seg: List[int]` | the authentication segment, a substring of `str(value)` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `n == 0 → return False` | the userinfo body requires at least one char (`[^\s:@/]+`, a `+` quantifier); the empty wrapper alternative `(?:...@)?` is a *different* match (no segment), not an empty segment | I | a zero-length segment cannot full-match the `+`-quantified group. |
| A3 | `seg[0] == 58 → return False` | leading `[^\s:@/]+` user run is non-empty, so the segment cannot start with the separator `:` | I | the user run before the optional `:` is mandatory. |
| A4 | the loop computing `good = body_ok(...)` (every char is `is_uchar` or `:`) and `ncolon = colons(...)`, returning `good ∧ ncolon ≤ 1` | the compiled group `[^\s:@/]+(?::[^\s:@/]*)?` full-matching the segment | A-reference | the changed matching operation is modelled **deeply**: `accepts`/`body_ok`/`colons`/`is_uchar` (the `pure` region) and the verified loop in `validate_authsegment` ARE the acceptance predicate. There is **no consumed matcher axiom** — the proof never depends on one. The deep model is validated **== the real compiled group** out-of-band: G-AX (axiom_check.py) compiles `[^\s:@/]+(?::[^\s:@/]*)?` (re.IGNORECASE) and asserts `accepts == group.fullmatch` on 188 boundary + a programmatic per-code-point sweep over the full 29-code-point Unicode-whitespace class + 100k fuzz (alphabet includes the full whitespace block). The model excludes the **entire** Unicode `\s` class (`is_whitespace`), so the equivalence is universal, not ASCII-only. mapping.md §3.1 proves the characterization (non-empty; only authentication chars apart from ≤1 separator colon; no leading colon). |

The discriminating content of the change — `:`, `@`, `/` (and a second `:`) are
no longer accepted inside the segment — lives in `is_uchar` excluding 58/64/47
and in `colons(s) ≤ 1` (model) ⇔ the `[^\s:@/]` class + single optional `:`
(real). The pre-patch body `\S+(?::\S*)?` excluded only whitespace;
`model_prepatch.py` reproduces that (a whitespace-only check) and **fails** the
postcondition `Result() == accepts(ToSeq(seg))` — exactly the spec sensing the
change (G-DIFF). Its failing segments are precisely the issue's examples
(`foo/bar`, `foo@bar`, `foo:bar:baz`, `foo:bar/baz`, …), which the old regex
accepts but the new one rejects.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the userinfo character-class/structure matcher — is modeled
**deeply** (the spelled-out per-code-point fold `body_ok`/`colons` consumed in
`validate_authsegment`, step A4, an **A-reference**), not hidden behind an axiom
about the function under change. There is **no consumed axiom** in this bundle:
the changed matcher is the A-reference G-AX validates the deep model against,
and there is no unchanged stdlib callee the new code newly invokes. (The
surrounding `re.search`, `_lazy_re_compile`, `str(value)` are unchanged by the
patch and are not part of the modeled behavior; the patch edits only the regex
literal.)

## C. verify(model) ⇒ resolved

`validate_authsegment` verifies only if its decision equals the exact
acceptance predicate `accepts` (A4) — non-empty, ≤1 separator colon, no leading
colon, and every other code point an authentication character (no `:`/`@`/`/`/
whitespace). By R (str ↔ List[int]) the verified decision equals a full match of
the gold-patch userinfo group on the tested `str` segments; by G-AX the deep
model `accepts` equals the real compiled group `[^\s:@/]+(?::[^\s:@/]*)?` over
188 boundary + a full per-code-point Unicode-whitespace sweep + 100 000 fuzz
inputs (A-reference), the equivalence being universal because the model excludes
the entire Unicode `\s` class. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited matcher — and the gold patch resolves (G-RESOLVE: the validator now
rejects `http://foo/bar@example.com` and the other added invalid URLs, and still
accepts the rewritten valid encoded URL). The trust points are exactly the two
of PLAN §1.1: matcher soundness (G-AX) and refinement fidelity (this document,
G-EQ).
