# RELAXED-LEAKAGE ACCEPTANCE: psf__requests-6028

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14).** `meta.json` records the top-level `relaxed_leakage: true` flag,
which (with this file present) makes the G-LEAK gate record
`status = "relaxed"` (`src/swebench_unified/gates/leak.py`). In this unified
repo the policy lives in the binding spec-construction rules,
`prompts/nagini/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
... for a proven `problem_statement ↔ gold` mismatch where the gold's tested
discriminator exists only in `hints_text`/gold internals, so a *faithful* spec
MUST name it ... KEEP the instance with the leak allowed"). (The
`RELAXED_LEAKAGE.md` cited by an earlier revision of this file was a
source-repo-only doc that does not exist here — see `prompts/README.md` on
dangling source-repo refs.)

## Why the leak is genuinely unavoidable (not lazy de-narration)

### The gold's tested discriminator: re-attach userinfo on re-assembly

Gold patch (`requests/utils.py`, the `prepend_scheme_if_needed` body):

```python
if auth:
    # parse_url doesn't provide the netloc with auth
    # so we'll add it ourselves.
    netloc = '@'.join([auth, netloc])
```

The discriminator is **the userinfo/credentials `'@'`-join**: when the parsed
URL carried credentials, they must be re-attached to the authority (`netloc`)
before re-assembly, because the switch to `parse_url` produces a `netloc` that
OMITS the userinfo. The F2P tests add userinfo-bearing proxy URLs that fail
pre-patch (credentials dropped -> 407) and pass post-patch.

### That discriminator is absent from the solver-visible problem_statement

The `problem_statement` is a pure symptom report: "When using proxies in python
3.8.12, I get an error 407 ... I should get a status of 200." It contains a
minimal `requests.get(..., proxies=proxies)` snippet and a system-info JSON dump.
Token check against the solver-visible `problem_statement`:

| token (the fix vocabulary) | in problem_statement? | where it actually lives |
|---|---|---|
| `auth` / `userinfo` / `credential` | ABSENT | hints_text + gold |
| `netloc` | ABSENT | hints_text only |
| `urlunparse` | ABSENT | hints_text only |
| `parse_url` | ABSENT | hints_text + gold comment |
| `prepend_scheme_if_needed` | ABSENT | hints_text + gold (patched symbol) |
| `scheme` / re-assembl* | ABSENT | hints_text + gold |
| `'@'`-join (`'@'.join`) | ABSENT | hints_text + gold (verbatim) |
| `407` / `200` / `3.8.12` / `proxy` | PRESENT | problem_statement (symptom) |

The entire fix mechanism — `parse_url` losing the `netloc` userinfo, the
`user:pwd@host:port` -> `host:port` decomposition, and the verbatim remedy
`netloc = '@'.join([auth, netloc])` — appears ONLY in `hints_text` (the
maintainer/reporter debugging thread the consumer never sees) and the gold diff.
A `problem_statement`-only solver sees a proxy-407 symptom with no pointer to
userinfo, `netloc`, or re-assembly.

### Any faithful spec must pin the leaked trigger

To satisfy G-EQ / faithfulness / G-DIFF, `model.py` must pin the gold's actual
behavior: the result is the assembly over the **effective authority**, i.e. the
authority that retains the credentials joined by `'@'` when they are present
(`effective_authority`), never the bare authority. This is exactly the
hints/gold-internal userinfo-`'@'`-join concept. There is no PS-derivable
(proxy/407/python-version) reformulation that still models the gold fix, because
the public symptom and the gold fix are about different surfaces (a status code
vs. a URL-component re-assembly). De-narrating the docstring to abstract
behavioral language does not help: the *behavior itself* (credentials surviving
into the effective authority) is the leak, and it is necessarily present in the
postconditions (`model.py:96-108`), which are part of the consumer-visible spec
view.

## Re-verify snapshot (soundness intact — this is a relaxed-leakage acceptance, not a defect-in-spec)

- **G-VERIFY: PASS** — `model.py` verifies, no flags, well under the 300s cap.
- **G-DIFF: PASS** — `model_prepatch.py` (pre-patch skeleton: re-assembly from
  the bare authority, no userinfo re-attachment) FAILS on the discriminating
  postcondition `ToSeq(Result()) == assembled(..., effective_authority(...), ...)`
  (the userinfo is dropped). Right reason.
- **same_spec: TRUE** — spec regions (axioms/pure/pre/post/invariants)
  byte-identical between `model.py` and `model_prepatch.py`; only `impl` differs.
- **Static gates** (G-INTEGRITY / G-HYGIENE / G-LEAK-mechanical): pass.
- **G-AX: SOUND** — axioms region empty (no consumed `@ContractOnly`; the changed
  `'@'`-join and the unchanged combining callee are modeled deeply as
  `effective_authority` / `assembled` and validated == the real `'@'.join` /
  `urlunparse` by `axiom_check.py`).
- **G-EQ: SOUND/TIGHT** — 6 wrong impls rejected on the load-bearing equality;
  positive-control correct-alt verifies; helpers are `@Pure` structural transforms
  of the actual inputs (no ungrounded-oracle echo, directive 8).
- **G-RESOLVE: resolves** — `patch.diff` == gold verbatim; applies cleanly at
  `base_commit`; F2P userinfo URLs fail pre / pass post.

The mechanical G-LEAK screen passes (no diff lines/paths/patched-symbol
identifiers/narration of the literal edit), but it is lexical and blind to this
semantic fix-mechanism leak; the adversarial PS<->spec-vocabulary diff (above) is
the binding judgment, and it establishes the relaxed-leakage disposition.

## Conclusion

This is a `problem_statement <-> gold` mismatch in which faithful + non-leaking is
provably impossible while the verification core is fully sound and the gold
resolves. Per the relaxed-leakage policy (`prompts/nagini/spec_guide.md`
directive 6) the instance is KEPT with `meta.json relaxed_leakage: true`
(=> G-LEAK records `status = "relaxed"`) and this in-bundle rationale. It is
the 2nd confirmed instance of this class (after `django__django-15252`).
