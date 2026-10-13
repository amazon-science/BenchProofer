# P2 adversarial audit — psf__requests-1766

Instance: `psf/requests` digest-auth qop quoting fix
(`build_digest_header`, requests/auth.py). Gold edit: `qop=auth` (bare) →
`qop="auth"` (double-quoted), per RFC 2617.

Baseline sanity: `Solution.lean` compiles cleanly (lean_verify exit 0);
`#print axioms correct_digestAuthHeader` => "does not depend on any axioms"
(no `sorryAx`, fully closed). Marker byte-identity check exit 0.

The frozen spec is a **total exact-equality**:
```
problem_spec_digestAuthHeader … result :=
  result = assembledDigestHeader username realm nonce uri respdig
            opaqueVal algorithm entdig qop ncvalue cnonce
```
i.e. the entire output string is pinned for every input tuple. This shape
drives all four verdicts.

---

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

**Attack:** exhibit an alternative `implementation_digestAuthHeader` of the
frozen spec whose `correct_` closes but whose refined patch does NOT resolve.

**Result:** impossible. Because `problem_spec` is `result = assembledDigestHeader …`
(exact equality, total over all `String` inputs), ANY impl that closes
`correct_` must be extensionally equal to `assembledDigestHeader` on every
input — and `assembledDigestHeader` emits `qop="auth"` (quoted), the gold
behavior. So every closing alternative produces byte-identical output to gold
and therefore resolves; there is no closing-but-non-resolving alternative.

Concretely I tried the natural non-resolving alternative — the **pre-patch**
impl (bare `qop=auth`) — against the frozen spec
(`tmp/audit-1766/geq.lean`): the proof does NOT close (heartbeat timeout, the
`rfl` legs fail to unify on the qop branch). And I confirmed the prepatch
output literally differs from the spec value on a qop-present input
(`tmp/audit-1766/geq_neg.lean`, `decide` succeeds on `≠`):
```
prepatch:  …, qop=auth,   nc=00000001, …
spec/gold: …, qop="auth", nc=00000001, …
```
The discriminating clause (`qop` value is the quoted string `"auth"`) is in
the spec, so the only impls that close are exactly the resolving ones.
**Verdict: SOUND.**

**Recorded machine verdict.** eq: 7 attacks re-run, none breaks the spec; positive control verifies

The section above is this audit round's own account of the role, argued in prose: where it quotes an attack it quotes it as illustration, and no outcome is recorded there for the individual re-runs it counts. The recorded sentence above and the paragraphs below are what the harness retained about them.

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

**Attack:** from the spec view only, write a WRONG impl + closing proof.

**Result:** failed. The spec pins the full output string; there is zero slack.
I tried a wrong impl that quotes the nonce-count value (`nc="…"` instead of the
gold bare `nc=…`) — a real divergence from the oracle — and attempted the same
`split <;> … <;> (rfl | simp_all | decide)` proof
(`tmp/audit-1766/panel1.lean`). It does NOT close (heartbeat timeout; the qop
branch leg is unprovable because the strings genuinely differ). Any impl whose
output diverges from `assembledDigestHeader` on any input is rejected by the
exact-equality post-condition. **Verdict: TIGHT.**

**Recorded machine verdict.** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

The section above is this audit round's own account of the role, argued in prose: where it quotes an attack it quotes it as illustration, and no outcome is recorded there for the individual re-runs it counts. The recorded sentence above and the paragraphs below are what the harness retained about them.

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

**Attack:** find an input where the modeled `assembledDigestHeader` disagrees
with the real patched `build_digest_header`.

Checked the real source at base_commit `8477355…` (via
`the upstream repository`). The post-patch assembly tail is:
```python
base = 'username="%s", realm="%s", nonce="%s", uri="%s", response="%s"' % (...)
if opaque:    base += ', opaque="%s"' % opaque
if algorithm: base += ', algorithm="%s"' % algorithm
if entdig:    base += ', digest="%s"' % entdig
if qop:       base += ', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)
return 'Digest %s' % base
```
Every clause matches `assembledDigestHeader` op-for-op: directive order,
`", "` separators, quoted mandatory params, present-iff-truthy optionals,
the bare `nc` token, the quoted `cnonce`, the hardcoded `qop="auth"` value, and
the `Digest ` prefix. Ran the real Python on a qop-present tuple
(`python3` repro): output is byte-identical to the spec value verified in
Role 1.

Truthiness modeling: the only falsy `str` is `""`, and `None`→`""` per the
model, so Python `if opaque:`/`if qop:` ≡ Lean `≠ ""`. The qop directive value
is hardcoded `auth` in the source regardless of the actual qop string, and the
function only reaches this header-returning tail when
`qop=='auth' or 'auth' in qop.split(',')` (else `return None`), so
"qop present ⇒ emit `qop="auth"`" is exactly the real reachable behavior. No
diverging input found. **Verdict: FAITHFUL.**

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

**Attack:** does the spec view leak the gold edit beyond the public
problem_statement (not hints_text; hints_text is empty here)?

The public `problem_statement` already states the fix verbatim: "the value of
'qop-options' directive should be quoted with double quotes," quotes the RFC
2617 text, and notes curl appends the quotes. The gold edit (`qop="auth"`) IS
the publicly-stated requirement. The spec view (docstrings + signatures +
empty axioms block) describes the header-assembly structure but reveals nothing
beyond what the problem_statement already discloses; it carries no impl and no
proof. Therefore no leakage beyond the public statement. **Verdict: NO-LEAKAGE.**

---

## Synthesis

- **G-EQ = pass** (Role 1 SOUND).
- **G-PANEL = pass** (Role 2 TIGHT, Role 3 FAITHFUL, Role 4 NO-LEAKAGE).

The exact-equality spec is tight and faithful to the real patched callee; the
only behavior it can fail to fix is impossible to express as a closing
alternative, and the gold change is already public in the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
