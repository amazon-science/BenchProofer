# P2 adversarial audit — psf__requests-1921

Modeled function: `requests.sessions.merge_setting(request_setting, session_setting,
dict_class=OrderedDict)` at `requests/sessions.py:34` @ base_commit
`3c88e520da24ae6f736929a750876e7654accc3d` — the both-operands-are-`Mapping` tail
(the only region the patch touches). Lean: `implementation_effectiveSetting`.

Frozen spec (`problem_spec_effectiveSetting`):
`result = effective req ses`, where
`effective req ses = (dropNulledKeys req (overlay ses req)).filter (·.2.isSome)`.
An EXACT, fully-extensional list equality, stated for ALL `req ses` with NO
precondition. The patch adds a final pass dropping EVERY remaining `none`-valued
entry — fixing the case where a SESSION default carries `none`
(e.g. `Accept-Encoding`).

(Note: this verdict was rewritten against the actual frozen spec shipped in
`Solution.lean`. A prior draft referenced symbol names — `combineDefaults`,
`dropUnset`, `Nat` keys, a `Nodup` precondition — that do NOT appear in the
current bundle; it was stale and has been replaced.)

## Baseline: the shipped proof genuinely closes (no sorry, clean axioms)

`scripts/lean_verify.sh Solution.lean` → exit 0 (compiles, no sorry).
`#print axioms correct_effectiveSetting` → `[propext, Quot.sound]` — no `sorryAx`,
no custom axioms. The proof discharges the two `forIn`→`foldl` loop lemmas by
induction and closes with `rfl`. The spec is satisfiable by the intended impl, and
the impl is a true refinement. `python -m swebench_lean.markers .` → exit 0
(spec-region byte-identity holds). No `_prop` axiom is consumed (G-AX = skip,
correctly).

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

Attack: find an alternative `implementation_effectiveSetting` whose
`correct_effectiveSetting` CLOSES yet whose refined patch does NOT resolve.

The spec is `result = effective req ses` — an exact equality pinning the result to
a single total function of the inputs. Any closing impl must equal `effective` on
EVERY `List Entry` input. Crucially the spec carries NO `Nodup`/unique-key
precondition, so it is STRONGER than the real domain (Python dicts always have
unique keys). This eliminates the classic G-EQ escape (diverge outside the real
domain while staying faithful to the callee): there is no input class on which a
closing impl is free to differ.

Since `effective` is the verified-faithful model of the POST-patch callee (Role 3,
300k inputs, zero divergence), any closing impl computes exactly the post-patch
behavior on the unique-key inputs the real call site uses — in particular it drops
session-`none` entries. On the FAIL_TO_PASS witness (session
`Accept-Encoding=none`, empty request) the model returns `[]` (header dropped),
versus prepatch `[('Accept-Encoding', none)]` (the bug). Any closing impl must
return `[]` here, hence RESOLVES. No closing-but-unresolving impl exists. SOUND.

**Recorded machine verdict.** eq: 7 attacks re-run, none breaks the spec; positive control verifies

The section above is this audit round's own account of the role, argued in prose: where it quotes an attack it quotes it as illustration, and no outcome is recorded there for the individual re-runs it counts. The recorded sentence above and the paragraphs below are what the harness retained about them.

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

Attack: from the spec view alone, write a WRONG impl + a closing proof.

I took the most natural wrong impl — the prepatch/buggy behavior (start from `ses`,
overlay `req` via `dictSet`, drop request-`none` keys, but OMIT the final
value-present filter). I machine-disproved that it satisfies the frozen spec.
Witness: `req = []`, `ses = [("a", none)]`. Then `effective = []` (the final
`.filter (·.2.isSome)` drops the `none`), while the wrong impl returns
`[("a", none)]`. Lean `theorem wrong_is_false : ¬ (∀ req ses, problem_spec …
(implementation_wrong …))` closes via `simp` on this witness — verified exit 0, no
sorry.

Because the spec is an exact extensional equality, the result is uniquely
determined by the inputs; ANY impl differing from `effective` on any input fails to
close. No slack for a wrong-yet-closing impl. TIGHT.

**Recorded machine verdict.** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

The section above is this audit round's own account of the role, argued in prose: where it quotes an attack it quotes it as illustration, and no outcome is recorded there for the individual re-runs it counts. The recorded sentence above and the paragraphs below are what the harness retained about them.

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

Checked the real callee at base_commit via the bare mirror
(`git show 3c88e520…:requests/sessions.py`):
`merge_setting` matches mapping.md verbatim — `dict_class(to_key_val_list(session))`
+ `.update(to_key_val_list(request))` + per-request `del`-on-`None` loop +
`return`. `patch.diff` inserts exactly
`merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)`
before the return.

I transliterated the REAL post-patch body (with `to_key_val_list` + `OrderedDict`)
and differential-tested it against the Lean-model shadow of
`implementation_effectiveSetting` over the FAIL_TO_PASS edge case plus 300,000
randomized OrderedDict inputs (keys a–f, values `{None}∪{1,2,3}`, lengths 0–8,
seed 1921). ZERO divergences. Coverage includes OrderedDict update ordering
(keep-position on existing key vs append on new key), request-`None` deletion, and
the session-`None` drop the patch fixes. The patch's `dict(...)` comprehension
preserves insertion order on Py3.7+, matching the model. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

The public `problem_statement` already states the WHAT explicitly: setting
`session.headers['Accept-Encoding'] = None` must NOT send the header (it currently
sends `Accept-Encoding: None`), and `del session.headers[...]` is the existing
workaround. That is precisely "drop `None`-valued SESSION default headers."

The spec view's narrative restates this publicly-known WHAT (null sentinel
suppresses an entry regardless of whether it came from the request or the session
defaults). It does NOT reveal the HOW beyond the public statement: no file, no line
number, no patch text, no mention of the `dict((k,v) … if v is not None)`
mechanism. Those live only in mapping.md / patch.diff — auditor/build artifacts,
not part of the spec view. The behavioral requirement in `problem_spec` is
derivable directly from the public problem statement. NO-LEAKAGE.

## Decision

- G-EQ    = pass (Role 1 SOUND)
- G-PANEL = pass (Role 2 TIGHT ∧ Role 3 FAITHFUL ∧ Role 4 NO-LEAKAGE)

Attacked hard: confirmed the shipped proof closes with clean axioms, machine-
disproved the prepatch buggy impl against the frozen spec, ran a 300k-input
differential of the Lean model against the REAL post-patch callee (zero
divergences), and probed the no-precondition spec for a G-EQ domain-escape (none
exists). All four attacks failed; the bundle is sound.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
