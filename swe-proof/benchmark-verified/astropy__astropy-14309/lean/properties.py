"""properties.py — G-PBT falsification battery for astropy__astropy-14309 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_isFits`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file elaborates
with the obligation closed, no ``sorry``/``admit``/``axiom``);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior — deciding whether the inputs denote a
source of the structured binary-table format, over three input binders):

  isFits (filepath fileobj : Option (List Char)) (args : List Bool)
        : Except Unit Bool

The postcondition is a FIRST-MATCH PRIORITY CASCADE over the three binders, and
it is total — every input point is pinned, with no precondition hypothesis (the
``∀`` in ``correct_isFits`` is unguarded). Its independent top-level clauses,
one per branch of the cascade:

  (C1) ``fileobj = some content``  -> ``ok (content.take 30 == fitsSignature)``
       the readable input wins outright, and the answer is the comparison of its
       leading 30 code points against the constant marker sequence;
  (C2) ``fileobj = none``, ``filepath = some p``
       -> ``ok (endsWithAny (p.map Char.toLower) fitsExtensions)``
       a present path yields the case-insensitive suffix test as the FULL answer
       for that branch — whether or not a suffix matches;
  (C3) both absent, ``args = []``   -> ``error ()``
       nothing remains to probe, so the access is out of range;
  (C4) both absent, ``args = a :: _`` -> ``ok a``
       the answer is the head flag, and only the head (the tail pins nothing,
       matching the modeled surface).

The load-bearing clause is C2, and specifically its "full answer" character: a
present path whose suffix does NOT match must yield ``ok false`` rather than
fall through to the ``args`` probe of C3/C4, where an empty positional list
turns into ``error ()``. That out-of-range access on a suffix-less path name is
the reported defect, and the F2P regression pins exactly it — a present,
non-matching path name with no positional argument must answer negatively
instead of raising.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's directive-5 note
    already records the probe as vacuous there (every parameter is a value type,
    so there is no read-only half-permission to overwrite). On this backend it is
    vacuous for the stronger reason: the carrier is referentially transparent, so
    there is no aliasing and no permission to mutate at all. No substitute is
    fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. The nagini sibling
    carries a self-recursion rival rejected by its termination obligation. Here
    ``implementation_isFits`` is a total Lean ``def``, so a body that never
    answers cannot be written in the first place: there is nothing to port and
    nothing the spec fails to see. (This is NOT the velvet ``partial``-semantics
    spec hole of ``the corpus-wide termination-semantics finding``, which does not apply to a
    vanilla-Lean bundle.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the three
    binders: it is built only from the marker constant, the suffix list, the
    fully-unfolded suffix test and the structural ``match``, and the bundle
    declares no ``opaque``/``axiom`` at all (the axioms region is empty). There
    is no answer key an implementation could echo without doing the work, which
    is what the nagini sibling's own directive-2 note records. Its honest
    cheapest-impl positive control is ported as the two ``pos-*`` cases below.

  * PARTIAL-DOMAIN / VALUE-SWAP / BRANCH-PRIORITY — APPLIES, and is where the
    whole battery lives. The observable is one ``Except Unit Bool``; the rivals
    below attack each clause of the cascade directly.

CARRIER NARROWING vs nagini. The nagini sibling models the same single behavior
as an integer-coded cascade over six pre-reduced scalar facts (four booleans, a
count, a flag), where the out-of-range access is a returned sentinel code. This
bundle keeps the three ACTUAL argument binders instead, so the path name and the
readable input are present as their real ``List Char`` payloads and the
positional list as a real ``List Bool``. Every nagini spec case therefore has a
counterpart here, and the extra structure buys three rivals nagini's flattened
carrier could not express at all (a suffix test that is inverted rather than
constant, a mis-ordered branch priority, and a negated head flag). The count
goes UP rather than down, which is carrier widening, not parity-chasing.

BINDER COVERAGE — every input binder is varied by the reject witnesses, so no
rival could mishandle one input while every witness held it fixed:

  * ``filepath`` — ``none`` (``weak-stream-verdict-inverted``,
    ``weak-positional-head-negated``), and ``some p`` at THREE materially
    different payloads: a non-matching name (``weak-path-fallthrough``,
    ``weak-path-always-positive``), a different non-matching name
    (``weak-path-fallthrough-narrow``), and a MATCHING name in upper case
    (``weak-path-verdict-inverted``, which is also the only witness exercising
    the case-folding half of C2) plus a matching name in lower case
    (``weak-branch-priority``). Both truth values of the suffix test are probed,
    at both letter cases.
  * ``fileobj`` — ``none`` in five witnesses, ``some`` at a MATCHING payload
    (``weak-stream-verdict-inverted``) and at a NON-matching payload
    (``weak-branch-priority``). Both truth values of C1's comparison are probed,
    and the non-matching one is what makes the priority rival visible.
  * ``args`` — ``[]`` (``weak-path-fallthrough-narrow``,
    ``weak-path-verdict-inverted``, ``weak-stream-verdict-inverted``,
    ``weak-branch-priority``), ``[true]`` (``weak-path-fallthrough``,
    ``weak-positional-head-negated``) and ``[false]``
    (``weak-path-always-positive``). Varying ``args`` UNDER a present path is
    what separates the two path-fallthrough rivals from each other: one is
    visible only when the positional list is empty, the other whenever it is not.

  ``args``'s TAIL is varied too, by ``weak-positional-tail-read`` at
  ``[true, false]``. An earlier revision of this manifest recorded the tail as
  "unobservable by construction, so no rival keyed on it could be refuted" —
  that claim is FALSE and was removed under audit. C4 pins the head flag *of
  the whole list*, which makes any rival that reads a DIFFERENT position of a
  multi-element list observably wrong: at ``[true, false]`` the spec pins
  ``ok true`` and a last-element reader answers ``ok false``. Two such rivals
  were built and both were refuted by real witnesses (rival 0 / gold 1), so
  omitting the sub-domain was a genuine coverage gap, now closed. What IS
  unobservable is the tail's effect *given the head* — no rival can be keyed on
  the tail while still reading the head correctly at every list — and that is a
  much narrower non-applicability than the one previously claimed.

CLAUSE COVERAGE — each independent clause is attacked: C1 by
``weak-stream-verdict-inverted``, C2 by ``weak-path-fallthrough``,
``weak-path-fallthrough-narrow``, ``weak-path-always-positive``,
``weak-path-verdict-inverted`` and ``weak-path-case-insensitive-dropped``, C3 by
``weak-path-fallthrough-narrow`` (which reaches ``error ()`` from a branch that
must not produce it), C4 by ``weak-positional-head-negated`` and
``weak-positional-tail-read``, and the CASCADE ORDER itself — which no single
clause states, but which the ``match`` nesting encodes — by
``weak-branch-priority``.

CASE FOLDING is attacked SEPARATELY, by ``weak-path-case-insensitive-dropped``,
and this too corrects an audited claim. An earlier revision asserted that
``weak-path-verdict-inverted`` "makes C2's ``Char.toLower`` folding
load-bearing" because its witness names an upper-case path. It does not: that
witness closes by ``simp`` alone, and against a rival which drops the folding
the same input leaves the residual goal
``¬ endsWithAny ['T','.','F','I','T','S'] .. = endsWithAny ['t','.','f','i','t','s'] ..``
UNCLOSED — measured, exit 1, so it refutes nothing there. Folding needed its own
rival, whose witness closes by ``simp; decide`` at the same input (rival 0 /
gold 1).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation, so a rejection alone attributes nothing to the spec:
the frozen script is a per-branch ``rfl`` cascade and ANY reshape breaks it.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec predicate at one concrete input. Each was built with the
gate's own file surgery and checked with two real builds — it ELABORATES against
its rival and FAILS on the frozen solution — so each is a seen discriminator and
not a tautology. All witnesses state literal inputs and bind nothing, so no
consistency probe applies (there are no hypotheses to be jointly unsatisfiable).

  Tactic note: ``Except Unit Bool`` has no ``DecidableEq`` instance in this
  workspace, so a bare ``decide`` cannot close these goals (it reports
  ``failed to synthesize Decidable``) and the frozen obligation itself is closed
  by ``rfl``, not ``decide``. The witnesses accordingly reduce with ``simp``
  first and only then ``decide`` the residual boolean; the one rival whose
  residual goal is a suffix test over a literal path needs the unfolding lemmas
  handed to ``simp`` (``endsWithAny``/``fitsExtensions``/``List.isSuffixOf``/
  ``List.isPrefixOf``) — the "when decide gets stuck on a literal" pattern.

  And ``Id.run`` must be kept OUT of that simp set, which is the defect the
  audit repaired. As a ``simp`` rewrite it unfolds the ``Id`` monad scaffolding
  into a form ``simp`` cannot then finish, leaving the goal stalled at
  ``¬(do PUnit.unit; Except.ok false) = Except.ok false`` on the frozen
  solution — a claim that was never evaluated. Left in, the gold-side failure is
  a stuck reduction rather than a refutation, and the flipped-claim FORGERY
  stalls with the same goal, so the exit code carries no information about what
  the witness asserts. Removed, ``simp``'s own ``Id`` lemmas reduce both sides
  and gold fails with ``unsolved goals ⊢ False`` while the forgery on gold
  PASSES. Every gold-side failure in this battery is now one of two shapes, both
  claim-tracking and both measured against their forgeries: ``unsolved goals ⊢
  False`` (``simp`` proved the equation for gold, so the negation is
  unprovable — forgery on gold exits 0) or ``Tactic `decide` proved that the
  proposition False is false`` (forgery on gold exits 0 once its now-redundant
  ``decide`` is dropped, since ``simp`` alone closes it).

AXIOM lane: EMPTY, as in nagini (whose axioms region is likewise empty). This
bundle declares no ``opaque`` callee and no ``axiom``; meta.json records the
suffix test as a deep-model A-reference, whose validation against the real
standard-library string operations belongs to G-AX, not this gate.

PORTED FROM NAGINI. (A) partial-domain-prepatch-fallthrough ->
``weak-path-fallthrough``; (C) narrow-fault-leak-f2p-only ->
``weak-path-fallthrough-narrow``; (B) value-swap-unrecognised-true ->
``weak-path-always-positive``; (D) unchanged-branch-stream-swap ->
``weak-stream-verdict-inverted``; (E) pos-control-localvar-reshape ->
``pos-branch-reshape``; (F) pos-control-grounded-oracle-delegate ->
``pos-functional-cascade``; (G) admissibility-f2p-shaped ->
``admiss-ground-instances``. (H) divergence-self-recursion is NOT ported
(vacuous: a total ``def`` cannot diverge — see above); the nagini frame-mutation
note has no case to port. Three rivals are ADDED for surface nagini's flattened
carrier could not express: ``weak-path-verdict-inverted``,
``weak-branch-priority``, ``weak-positional-head-negated``. Two MORE were added under
audit, closing gaps the port left unattacked and false prose it had recorded in
their place: ``weak-positional-tail-read`` (C4's read POSITION, which the
singleton-only head rival cannot pin) and
``weak-path-case-insensitive-dropped`` (C2's case folding, which no existing
witness actually refutes). See ``assessment`` in the submitted payload.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14309"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it edits and is unique in
# the file (asserted at load, so the manifest breaks loudly on any spec drift).
#   _IMPL  — the full body of the one impl region (below the `def` header line)
#   _DEF   — the `def` header line + body, for the one variant that changes the
#            impl's SHAPE from a `do` block to a pure functional cascade
#   _PROOF — the full tactic body of the one proof region
# ---------------------------------------------------------------------------
_IMPL = (
    "  if let some content := fileobj then\n"
    "    return Except.ok (content.take 30 == fitsSignature)\n"
    "  if let some p := filepath then\n"
    "    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)\n"
    "  match args with\n"
    "  | [] => return Except.error ()\n"
    "  | a :: _ => return Except.ok a"
)
_DEF_HEAD = (
    "def implementation_isFits (filepath fileobj : Option (List Char)) (args : List Bool) :\n"
    "    Except Unit Bool := Id.run do\n"
)
_PROOF = (
    "  intro filepath fileobj args\n"
    "  unfold problem_spec_isFits implementation_isFits\n"
    "  cases fileobj with\n"
    "  | some content => rfl\n"
    "  | none =>\n"
    "    cases filepath with\n"
    "    | some p => rfl\n"
    "    | none =>\n"
    "      cases args with\n"
    "      | nil => rfl\n"
    "      | cons a as => rfl"
)

for _anchor, _label in ((_IMPL, "impl body"), (_DEF_HEAD, "impl def header"),
                        (_PROOF, "proof body")):
    if _anchor not in _BASE:
        raise AssertionError(f"drift: {_label} anchor not found")
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"not unique: {_label} anchor")


# ---------------------------------------------------------------------------
# Witness helper. Every witness states the SAME shape — the spec predicate is
# contradicted at one concrete input — so the shape is built once and each case
# supplies its input point and the tactic that reduces its residual goal.
# ---------------------------------------------------------------------------
def _witness(filepath, fileobj, args, tactic):
    return (f"example : ¬ problem_spec_isFits {filepath} {fileobj} {args}\n"
            f"    (implementation_isFits {filepath} {fileobj} {args}) := by\n"
            f"  unfold problem_spec_isFits implementation_isFits\n"
            f"{tactic}")


# `simp` reduces the `Id.run` / `match` scaffolding, then `decide` settles the
# residual boolean. A bare `decide` cannot start the job: `Except Unit Bool`
# carries no `DecidableEq` instance in this workspace.
_T_SIMP_DECIDE = "  simp\n  decide\n"
# `simp` alone suffices when the residual boolean is already a literal clash.
_T_SIMP = "  simp\n"
# The suffix test over a literal path name does not reduce under plain `simp`
# (it stalls at `endsWithAny <literal> fitsExtensions`), so the unfolding
# lemmas are handed to `simp` explicitly.
#
# AUDIT REPAIR. `Id.run` must NOT be in this simp set, and the earlier revision
# put it there. Handing `Id.run` to `simp` as a rewrite rule makes it unfold the
# `Id` monad scaffolding into a shape `simp` then cannot finish: on the FROZEN
# solution the goal stalls at
#   ⊢ ¬(do PUnit.unit
#          Except.ok false) = Except.ok false
# i.e. the claim is never evaluated. That is a stuck reduction wearing an
# `unsolved goals` costume, and it is hollow in the precise sense attack B'
# tests: the FORGERY asserting the OPPOSITE claim (gold is CORRECT at this
# input) fails on gold with the same stalled goal modulo the dropped `¬`
# (measured: witness gold exit 1, forgery gold exit 1). Gold's exit code
# therefore carried no information about the claim, so the gate would have
# recorded `rejected` for a witness asserting gold is right.
#
# Dropping `Id.run` from the set is the whole fix: `simp`'s own `Id`
# simp-lemmas then reduce the scaffolding on both sides and the residual goal
# is decided. Re-measured with three real builds: rival exit 0, gold exit 1
# with `unsolved goals ⊢ False` (a SEMANTIC refutation — `simp` closed the
# equation for gold, leaving the negation's `False`), and the flipped-claim
# forgery on gold exit 0 (gold is PROVEN correct at that input). The gold-side
# error now tracks the claim, which is what makes the rejection evidence.
_T_SIMP_SUFFIX = ("  simp [endsWithAny, fitsExtensions, "
                  "List.isSuffixOf, List.isPrefixOf]\n")


# ---------------------------------------------------------------------------
# Proof bodies for the cases that legitimately RE-PROVE. The
# `theorem correct_isFits` STATEMENT is byte-identical in every case; only the
# tactic body differs. No helper lemma, no new declaration, no assumption token.
# ---------------------------------------------------------------------------

# AUDIT NOTE. This used to be a separate `_PROOF_FUNCTIONAL` string that
# `pos-functional-cascade` swapped in, described as a proof "re-authored for the
# new shape". It was byte-identical to `_PROOF` (checked: the swap was a no-op),
# so the description was false — the frozen script closes that reshape unchanged,
# because dropping `Id.run` only makes each branch's `rfl` easier. The alias is
# removed rather than kept as a no-op swap: a swap that changes nothing reads to a
# later maintainer as a re-proof that was needed, which is exactly the "positive
# that looks reproven but was not" shape an audit is meant to catch. The case now
# edits only its impl region, and its rationale says so.

# Admissibility: five ground instances discharged by evaluation INSIDE the tactic
# body (as `have`s, so nothing is added to the frozen declaration set), then the
# frozen obligation closed verbatim.
#
# AUDIT REPAIR. The earlier revision stated each `have` as
#   problem_spec_isFits <input> (implementation_isFits <input>)
# and closed it by `rfl`. That is an instance of the frozen obligation at a
# literal input, so `rfl` closes it by DEFINITIONAL IDENTITY between the two
# sides — it never evaluates the cascade and never learns what the answer at
# that input IS. Which means the case attested to nothing the frozen theorem
# does not already give: the obligation is closed at every input by the frozen
# script, so an instance of it at one input is a weaker restatement, and the
# rationale's claim of "discharged by evaluation" was false.
#
# Repaired to name the CONCRETE answer on the right-hand side of each `have`
# (`Except.ok false`, `Except.ok true`, `Except.error ()`), which forces the
# spec predicate to be evaluated at the literal input rather than matched
# against itself. `simp` with the suffix-unfolding lemmas is then what closes
# them, and the F2P-shaped one is the load-bearing entry: a present
# NON-matching path name with an EMPTY positional list is pinned to
# `Except.ok false` — the obligation is SATISFIABLE at exactly the input the
# regression exercises, and answerable there rather than out of range. That is
# the analogue of PRECOND-TOO-STRONG on a total carrier: were any of these
# unsatisfiable, no impl could admit an input the behavior must admit.
#
# The stream instance needs `fitsSignature` handed to `simp` — without it the
# residual goal is `fitsSignature.length ≤ 30` (measured, exit 1), since `simp`
# will not compute the length of the marker constant while it is still folded.
_PROOF_ADMISS = (
    "  have _g_path_unmatched : problem_spec_isFits (some \"sample.dat\".toList) none []\n"
    "      (Except.ok false) := by\n"
    "    unfold problem_spec_isFits\n"
    "    simp [endsWithAny, fitsExtensions, List.isSuffixOf, List.isPrefixOf]\n"
    "  have _g_path_matched : problem_spec_isFits (some \"t.fits\".toList) none []\n"
    "      (Except.ok true) := by\n"
    "    unfold problem_spec_isFits\n"
    "    simp [endsWithAny, fitsExtensions, List.isSuffixOf, List.isPrefixOf]\n"
    "  have _g_stream : problem_spec_isFits none (some fitsSignature) []\n"
    "      (Except.ok true) := by\n"
    "    unfold problem_spec_isFits; simp [fitsSignature]\n"
    "  have _g_positional_absent : problem_spec_isFits none none []\n"
    "      (Except.error ()) := by\n"
    "    unfold problem_spec_isFits; simp\n"
    "  have _g_positional_head : problem_spec_isFits none none [true]\n"
    "      (Except.ok true) := by\n"
    "    unfold problem_spec_isFits; simp\n"
) + _PROOF


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct reshape cannot
    # satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_isFits` statement byte-identical, introduces no helper
    # lemma / axiom / assumption token, and re-proves honestly where the frozen
    # script's per-branch `rfl` no longer applies.
    # =====================================================================
    {
        "id": "pos-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Same cascade, same order, but two branch expressions are re-spelled:
        # the suffix test is inlined to the `any`-over-suffixes form it is
        # defined as, and the positional probe reads the head via `head?`
        # instead of pattern-matching the list. Same value at every input.
        # Ports nagini case (E) pos-control-localvar-reshape.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    return Except.ok (fitsExtensions.any "
            "(fun suf => suf.isSuffixOf (p.map Char.toLower)))\n"
            "  match args.head? with\n"
            "  | none => return Except.error ()\n"
            "  | some a => return Except.ok a",
        ),
        "rationale": "a CORRECT reshape of two branch bodies: the suffix test is "
                     "written as the `any`-over-suffixes form its definition "
                     "unfolds to, and the positional branch reads the head "
                     "through `head?` (whose `none` case is exactly the empty "
                     "list) instead of matching `[] | a :: _`. Every clause "
                     "C1-C4 holds at the same value on every input, so this MUST "
                     "verify; a rejection would be SPEC-TOO-STRONG — the spec "
                     "pinning an incidental syntactic form of the branch bodies "
                     "rather than their behavior. The frozen per-branch `rfl` "
                     "cascade still closes it, so no re-proof is needed.",
    },
    {
        "id": "pos-functional-cascade",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest impl: drop the imperative `do`/early-return scaffolding
        # and write the cascade as the pure nested `match` the spec itself is
        # stated as. This is the grounded-oracle control the nagini sibling ships
        # as `return decided(...)`: because the postcondition is fully unfolded
        # over the binders rather than an opaque answer key, delegating to that
        # exact shape IS the modeled behavior, not a wrong echo. Statement
        # byte-identical, and the FROZEN proof region is kept verbatim — see the
        # audit note above `_PROOF_ADMISS`: this case's former "re-authored"
        # proof swap was byte-identical to `_PROOF`, i.e. a no-op, so it is now
        # simply not performed.
        # Ports nagini case (F) pos-control-grounded-oracle-delegate.
        "module": _swap(
            _BASE, _DEF_HEAD + _IMPL,
            "def implementation_isFits (filepath fileobj : Option (List Char)) "
            "(args : List Bool) :\n"
            "    Except Unit Bool :=\n"
            "  match fileobj with\n"
            "  | some content => Except.ok (content.take 30 == fitsSignature)\n"
            "  | none =>\n"
            "    match filepath with\n"
            "    | some p => Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)\n"
            "    | none =>\n"
            "      match args with\n"
            "      | [] => Except.error ()\n"
            "      | a :: _ => Except.ok a",
        ),
        "rationale": "the grounded-oracle control: the postcondition is built "
                     "only from the three binders, the marker constant, the "
                     "suffix list and the structural `match` — fully unfolded, "
                     "with no `opaque` callee and no axiom in the bundle — so an "
                     "implementation shaped exactly like it IS the modeled "
                     "behavior rather than an echo of an answer key, and it MUST "
                     "verify. Also the cheapest correct impl: dropping the "
                     "imperative scaffolding for the pure nested `match` changes "
                     "no value at any input. A rejection would be "
                     "SPEC-TOO-STRONG (the spec pinning the `do`-block shape "
                     "rather than the cascade). The FROZEN proof script closes "
                     "it unchanged — dropping the `Id.run` scaffolding only "
                     "makes each branch's `rfl` easier, never harder — so no "
                     "re-proof is performed; an earlier revision claimed one "
                     "and swapped in a byte-identical script, which the audit "
                     "removed. No new declaration, no helper lemma, and the "
                     "theorem statement is byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the normal
    # inputs the behavior is exercised on. The frozen theorem carries NO
    # precondition hypothesis (the cascade is total), so nagini's
    # precondition-admission probe has no binder to attack; the honest analogue
    # discharges the spec predicate at one ground input PER CLAUSE, by
    # evaluation, alongside the frozen obligation. If any ground instance could
    # not be discharged, the behavior would be unsatisfiable at an input it must
    # admit — the analogue of PRECOND-TOO-STRONG.
    # Ports nagini case (G) admissibility-f2p-shaped.
    # =====================================================================
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _PROOF_ADMISS),
        "rationale": "the obligation is discharged at five ground inputs, one "
                     "per clause of the cascade, each pinned to the CONCRETE "
                     "answer the spec gives there (so the `have` evaluates the "
                     "cascade rather than restating the obligation at a literal "
                     "input, which is what an earlier revision did and what the "
                     "audit repaired): a present NON-matching path "
                     "name with no positional argument (C2's negative side — the "
                     "regression-shaped input, which must be answerable at all "
                     "rather than out of range), a present MATCHING path name "
                     "(C2's positive side), a present readable input carrying "
                     "the marker sequence (C1), both absent with an empty "
                     "positional list (C3, the out-of-range answer), and both "
                     "absent with a head flag (C4). Verifies, else the behavior "
                     "is unsatisfiable at a normal input it must admit. Nothing "
                     "is assumed: the ground instances are `have`s inside the "
                     "tactic body, the frozen obligation follows verbatim, and "
                     "the theorem statement is byte-identical.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival is a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness, checked by two real builds to hold
    # of the rival and FAIL on the frozen solution.
    # =====================================================================
    {
        "id": "weak-path-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # THE ACTUAL DIFFERENTIAL (this is Solution_prepatch.lean's impl): the
        # present-path branch short-circuits ONLY when a suffix matches and
        # otherwise falls through to the positional probe, so C2 stops being the
        # full answer for that branch. Ports nagini case (A).
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    if endsWithAny (p.map Char.toLower) fitsExtensions then\n"
            "      return Except.ok true\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "this is the un-fixed behavior exactly: the path branch "
                      "answers only on a match and otherwise leaks into the "
                      "positional probe. Its faithful real patch is the "
                      "UNCHANGED routine, under which a present non-matching "
                      "path name is answered by whatever the first positional "
                      "argument happens to be — and when none was supplied, by "
                      "an out-of-range access that raises instead of returning. "
                      "That is the reported failure verbatim, so the F2P "
                      "regression (a present non-matching path name with no "
                      "positional argument must answer negatively) still fails. "
                      "It does NOT resolve.",
        "rationale": "REJECT from C2: at a present non-matching path name the "
                     "spec pins `ok (suffix test)` = `ok false`, but the rival "
                     "skips the branch and answers from the positional list "
                     "instead — with a head flag of `true` it returns `ok true`. "
                     "Refuted at a NON-EMPTY positional list on purpose: that "
                     "separates this rival from the narrow one below (which "
                     "agrees with the spec there), so the two are not sharing a "
                     "witness for different reasons. If it verified => "
                     "SPEC-TOO-WEAK, and the spec would not see the reported "
                     "defect at all.",
        "witness": _witness('(some "sample.dat".toList)', "none", "[true]",
                            _T_SIMP_DECIDE),
    },
    {
        "id": "weak-path-fallthrough-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the above, surgically narrowed to the single failing
        # sub-domain: a present non-matching path name is answered correctly
        # (`ok false`) WHENEVER a positional argument exists, and leaks the
        # out-of-range answer only when the positional list is empty. Ports
        # nagini case (C) narrow-fault-leak-f2p-only.
        #
        # AUDIT REPAIR (witness tactic). This case's witness was the one HOLLOW
        # rejection in the battery: its tactic handed `Id.run` to `simp`, which
        # left the gold-side goal stalled at `¬(do PUnit.unit; Except.ok false) =
        # Except.ok false` — never evaluated — and the flipped-claim forgery
        # stalled identically, so gold's exit 1 said nothing about the claim.
        # Fixed by dropping `Id.run` from the simp set (see `_T_SIMP_SUFFIX`);
        # gold now fails with `unsolved goals ⊢ False` and the forgery on gold
        # PASSES (exit 0), so the gold-side verdict tracks what is claimed.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    if endsWithAny (p.map Char.toLower) fitsExtensions then\n"
            "      return Except.ok true\n"
            "    if args.isEmpty then\n"
            "      return Except.error ()\n"
            "    return Except.ok false\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "a minimal rival that agrees with the fixed behavior "
                      "everywhere EXCEPT the one input that fails first. Its "
                      "faithful real patch keeps the fall-through but guards it "
                      "to the no-positional-argument case — so a present "
                      "non-matching path name STILL raises out of range exactly "
                      "when no positional argument was supplied, which is the "
                      "F2P regression's input. The regression fails unchanged, "
                      "and it does NOT resolve, even though the rival is correct "
                      "on the whole rest of the domain.",
        "rationale": "REJECT from C2 (and from C3, which it reaches from a "
                     "branch that must never produce the out-of-range answer): "
                     "at a present non-matching path name with an EMPTY "
                     "positional list the spec pins `ok false` while the rival "
                     "returns `error ()`. Refuted at `args = []`, where the "
                     "broader fallthrough rival above is refuted at a non-empty "
                     "list — so this near-miss is demonstrated on the "
                     "sub-domain it actually claims, and shows the spec is tight "
                     "even on a one-point divergence. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness('(some "table.ecsv".toList)', "none", "[]",
                            _T_SIMP_SUFFIX),
    },
    {
        "id": "weak-path-always-positive",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-SWAP on the discriminating branch: a present path is answered
        # positively unconditionally, so the branch is TOTAL (it never leaks to
        # the positional probe, and never produces the out-of-range answer) but
        # carries the wrong verdict whenever no suffix matches. Ports nagini
        # case (B) value-swap-unrecognised-true.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some _p := filepath then\n"
            "    return Except.ok true\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "answers every present path name positively, ignoring the "
                      "suffix test entirely. Its faithful real patch returns a "
                      "constant positive from the path branch: it does cure the "
                      "out-of-range access, but the F2P regression asserts a "
                      "NEGATIVE answer for a present non-matching path name and "
                      "would now get a positive one, so the regression fails for "
                      "the opposite reason. It also claims every unrelated path "
                      "name as this format, mis-routing the format-dispatch the "
                      "P2P round-trip tests depend on. It does NOT resolve. This "
                      "is the rival that shows curing the fault is not enough — "
                      "the VERDICT must be right too.",
        "rationale": "REJECT from C2 on the verdict value rather than on "
                     "totality: at a present non-matching path name the spec "
                     "pins `ok false` and the rival returns `ok true`. Note it "
                     "satisfies the fault-freedom half of the branch (it can "
                     "never return `error ()` from a present path) and is still "
                     "refuted, so the spec is not merely forbidding the "
                     "out-of-range answer — it pins the suffix test's value. "
                     "Refuted with a head flag of `false`, distinguishing it "
                     "from the fallthrough rival above (which at that input "
                     "returns the same `ok false` the spec wants, and so is NOT "
                     "refutable there). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness('(some "sample.dat".toList)', "none", "[false]",
                            _T_SIMP_DECIDE),
    },
    {
        "id": "weak-path-verdict-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # The other half of C2's value: the branch is total and consults the
        # suffix test, but NEGATES it. Refuted at a MATCHING path name in upper
        # case, which is also the only witness that exercises C2's case-folding
        # (no other rival's witness is sensitive to it). Not portable from
        # nagini, whose carrier pre-reduces the whole suffix test to one boolean
        # input fact.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    return Except.ok (! endsWithAny (p.map Char.toLower) fitsExtensions)\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "consults the suffix test but reports its complement. Its "
                      "faithful real patch negates the path branch's returned "
                      "test: it cures the out-of-range access, so the F2P "
                      "regression's negative assertion on a non-matching name "
                      "would pass by accident, but every genuinely matching path "
                      "name is then DENIED — the P2P round-trip tests that write "
                      "and re-read a table through a matching file name lose "
                      "their format dispatch and fail. It does NOT resolve.",
        "rationale": "REJECT from C2 at the positive side of the suffix test: at "
                     "a MATCHING path name the spec pins `ok true` and the rival "
                     "returns `ok false`. This is the only witness whose path "
                     "payload matches, and the only one written in UPPER case, "
                     "so it is also what makes C2's `Char.toLower` folding "
                     "load-bearing: a rival that ignored case would be invisible "
                     "to a witness whose matching name were already lower-case. "
                     "If it verified => SPEC-TOO-WEAK on the positive half of "
                     "the branch every other path rival probes negatively.",
        "witness": _witness('(some "T.FITS".toList)', "none", "[]", _T_SIMP),
    },
    {
        "id": "weak-stream-verdict-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # UNCHANGED-BRANCH rival: C1's comparison is negated. The fix does not
        # touch this branch, but a rival sharing the frozen spec must still
        # honour it. Ports nagini case (D) unchanged-branch-stream-swap.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (! (content.take 30 == fitsSignature))\n"
            "  if let some p := filepath then\n"
            "    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "inverts the leading-bytes comparison for a present "
                      "readable input. Its faithful real patch returns the "
                      "negated comparison from that branch — untouched by the "
                      "fix, but a rival that shares the frozen spec must still "
                      "honour it. A genuine stream carrying the marker sequence "
                      "is then denied, so the P2P tests that read a table "
                      "straight from an open binary handle lose their format "
                      "dispatch and fail. It does NOT resolve.",
        "rationale": "REJECT from C1: with a present readable input whose "
                     "leading 30 code points ARE the marker sequence the spec "
                     "pins `ok true` and the rival returns `ok false`. This is "
                     "the only witness that presents the readable-input binder "
                     "at a MATCHING payload, and it confirms the spec pins the "
                     "whole cascade rather than only the branch the fix "
                     "reshaped. If it verified => SPEC-TOO-WEAK on the "
                     "highest-priority clause.",
        "witness": _witness("none", "(some fitsSignature)", "[]", _T_SIMP),
    },
    {
        "id": "weak-branch-priority",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the CASCADE ORDER, which no single clause states — it is
        # encoded in the `match` nesting: the path name is consulted BEFORE the
        # readable input. Every branch body is individually correct, so this is
        # refutable only where the two branches disagree. Not portable from
        # nagini, whose flattened carrier fixes the priority in the input facts.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some p := filepath then\n"
            "    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)\n"
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "swaps the first two levels of the priority order: the "
                      "path name is consulted before the readable input, though "
                      "each branch's own answer is correct. Its faithful real "
                      "patch reorders those two tests. When both are supplied "
                      "they can disagree, and the readable input is the "
                      "authoritative evidence: the P2P tests that write a table "
                      "to a name carrying a matching suffix and re-read it "
                      "resolve the format from the CONTENT, and a file whose "
                      "name suggests the format but whose content does not match "
                      "is then mis-dispatched. It does NOT resolve. (The "
                      "regression input supplies no readable input at all, so "
                      "this rival passes the F2P test while breaking the "
                      "surrounding behavior — exactly the shape a "
                      "verify-does-not-imply-resolve break takes.)",
        "rationale": "REJECT from the cascade ORDER, which the nested `match` "
                     "encodes and no single clause states: C1 must win outright "
                     "whenever the readable input is present. At a present "
                     "readable input that does NOT match, together with a path "
                     "name that DOES, the spec pins `ok false` (C1) while the "
                     "rival answers from the path and returns `ok true`. This is "
                     "the only witness supplying two present binders at once, "
                     "and the only one presenting the readable input at a "
                     "non-matching payload — so it makes the priority itself "
                     "load-bearing. If it verified => SPEC-TOO-WEAK: every "
                     "clause could hold branch-by-branch while the routine "
                     "consulted its evidence in the wrong order.",
        "witness": _witness('(some "t.fits".toList)',
                            '(some "not a signature".toList)', "[]",
                            _T_SIMP_DECIDE),
    },
    {
        "id": "weak-positional-head-negated",
        "kind": "uniqueness",
        "expect": "reject",
        # The last unattacked clause: C4's head flag is negated. Reached only
        # when both the readable input and the path name are absent, so this is
        # the only rival visible on that sub-domain. Not portable from nagini,
        # whose carrier pre-reduces the head probe to an input fact it consumes
        # in the same shape.
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok (! a)",
        ),
        "refinement": "reports the complement of the first positional "
                      "argument's membership flag. Its faithful real patch "
                      "negates that final membership probe. The regression input "
                      "never reaches this branch (it supplies a path name), so "
                      "the F2P test is untouched — but every dispatch that "
                      "arrives with an in-memory structured object and no path "
                      "or handle is inverted, so the P2P tests that read a table "
                      "directly from such an object lose their dispatch and "
                      "fail. It does NOT resolve, and like the priority rival it "
                      "is the shape a verify-does-not-imply-resolve break takes: "
                      "F2P-clean, spec-violating.",
        "rationale": "REJECT from C4: with both the readable input and the path "
                     "name absent and a head flag of `true`, the spec pins "
                     "`ok true` and the rival returns `ok false`. This is the "
                     "only rival that reads the positional list's CONTENT (the "
                     "others only reach it, or not, from the path branch), so "
                     "without it a rival mishandling the head flag would verify. "
                     "It is refuted at a SINGLETON list, so it does not by "
                     "itself pin WHICH position C4 reads — that is "
                     "`weak-positional-tail-read`'s job. If it verified => "
                     "SPEC-TOO-WEAK on the lowest-priority clause.",
        "witness": _witness("none", "none", "[true]", _T_SIMP),
    },

    # ===== ADDED UNDER AUDIT (two coverage gaps the port left unattacked) =====
    {
        "id": "weak-positional-tail-read",
        "kind": "uniqueness",
        "expect": "reject",
        # C4 reads the HEAD of the positional list. This rival reads its LAST
        # element instead — correct on every singleton list, wrong as soon as the
        # list has a tail that disagrees with its head. Added under audit: the
        # port recorded the tail sub-domain as "unobservable by construction, so
        # no rival keyed on it could be refuted", and that is false. Refuted by a
        # real witness at `[true, false]` (rival exit 0, gold exit 1, gold's
        # residual goal reducing to `False`).
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    return Except.ok (endsWithAny (p.map Char.toLower) fitsExtensions)\n"
            "  match args.getLast? with\n"
            "  | none => return Except.error ()\n"
            "  | some a => return Except.ok a",
        ),
        "refinement": "probes the LAST positional argument rather than the "
                      "first. Its faithful real patch indexes the end of the "
                      "positional tuple instead of its front. The regression "
                      "input supplies a path name and never reaches this branch, "
                      "and any call passing exactly one positional argument is "
                      "unaffected — so the F2P test and most of the suite stay "
                      "green while every multi-argument dispatch reads the wrong "
                      "argument and mis-routes. It does NOT resolve, and it is "
                      "the F2P-clean shape a verify-does-not-imply-resolve break "
                      "takes.",
        "rationale": "REJECT from C4 on WHICH position is read, not on the "
                     "value read: at `args = [true, false]` the spec pins "
                     "`ok true` (the head) and the rival returns `ok false` (the "
                     "last). Note `weak-positional-head-negated` cannot cover "
                     "this — it is refuted only at a singleton, where head and "
                     "last coincide, so a position-confusing rival is invisible "
                     "to its witness. This is the only case varying the "
                     "positional list's LENGTH beyond one. If it verified => "
                     "SPEC-TOO-WEAK: C4 would pin a flag without pinning which "
                     "argument supplies it.",
        "witness": _witness("none", "none", "[true, false]", _T_SIMP),
    },
    {
        "id": "weak-path-case-insensitive-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # C2 folds the path to lower case before the suffix test. This rival runs
        # the suffix test on the RAW path, so it is correct on every already
        # lower-case name and wrong on any name whose recognised suffix is not.
        # Added under audit: the port claimed `weak-path-verdict-inverted` made
        # the folding load-bearing, but that witness closes by `simp` alone and
        # against this rival the same input leaves its residual goal unclosed
        # (measured, exit 1). Folding needed its own rival; this one's witness
        # closes by `simp; decide` (rival exit 0, gold exit 1, gold refuted by
        # `decide` proving the goal false).
        "module": _swap(
            _BASE, _IMPL,
            "  if let some content := fileobj then\n"
            "    return Except.ok (content.take 30 == fitsSignature)\n"
            "  if let some p := filepath then\n"
            "    return Except.ok (endsWithAny p fitsExtensions)\n"
            "  match args with\n"
            "  | [] => return Except.error ()\n"
            "  | a :: _ => return Except.ok a",
        ),
        "refinement": "drops the case normalisation and tests the raw path name "
                      "against the recognised lower-case suffixes. Its faithful "
                      "real patch omits the lower-casing from the suffix test. It "
                      "cures the out-of-range access, and the regression's "
                      "assertion (a lower-case non-matching name answers "
                      "negatively) still holds, so the F2P test passes — but "
                      "every upper- or mixed-case recognised name is now DENIED, "
                      "so the P2P round-trip tests that write and re-read through "
                      "such a name lose their format dispatch and fail. It does "
                      "NOT resolve.",
        "rationale": "REJECT from C2's case-folding half specifically: at an "
                     "upper-case MATCHING path name the spec pins `ok true` "
                     "(C2 folds first) and the rival returns `ok false`. This is "
                     "the case that makes `Char.toLower` load-bearing — verified "
                     "by hand that no other rival's witness refutes this one, so "
                     "without it a spec that omitted the folding entirely would "
                     "be indistinguishable. If it verified => SPEC-TOO-WEAK on "
                     "the normalisation C2 performs before its test.",
        "witness": _witness('(some "T.FITS".toList)', "none", "[]",
                            _T_SIMP_DECIDE),
    },
]

# nagini case (H) divergence-self-recursion is NOT ported, and the reason is
# narrower than either of the two this file previously recorded. Re-measured
# under audit with real builds rather than argued:
#
#   * the `partial` self-recursive rival (`partial def implementation_isFits ...
#     := implementation_isFits filepath fileobj args`) IS writable and IS in
#     scope — `variant_scope.variant_problems` returns an empty problem list
#     (checked). So "a total Lean `def` cannot diverge" is not the reason.
#   * but it does not need a witness at all, because it is already REJECTED by
#     the frozen obligation itself: the variant build fails at exit 1 with
#     `Tactic 'unfold' failed to unfold 'implementation_isFits'` raised inside
#     the FROZEN proof region (measured). `partial` supplies no equation lemma,
#     so the frozen script cannot reduce the impl and the obligation does not
#     close. A rival the frozen proof already rejects is not a SPEC-TOO-WEAK
#     probe: it would be recorded as `rejected` on a tactic failure, which is
#     exactly the witness-less rejection this gate refuses to credit. An earlier
#     revision of this note claimed `unfold` fails "on BOTH the rival and gold";
#     that is wrong as stated — gold has no such failure, the rival's failure IS
#     the rejection, and the claim was removed under audit.
#
# So the disposition (nothing to ship) stands, on the demonstrated ground that
# no admissible witness-bearing case exists here: the case would attest to the
# `partial` keyword defeating `unfold`, not to the spec. The frozen spec is
# indeed silent about termination — it is a `Prop` relating inputs to a returned
# `Except`, with no clause a non-terminating impl could contradict at a point —
# and that is the known `partial`-semantics finding of
# `the corpus-wide termination-semantics finding`, cited rather than re-measured and NOT re-raised
# as a `spec_holes` entry. Vanilla-Lean bundles are outside the 401 `partial`
# bundles it covers.
#
# The nagini frame-mutation note likewise has no case to port — it records the
# probe as already vacuous on its own value-typed carrier, and this carrier is
# referentially transparent besides. Neither is substituted; see the module
# docstring and the submitted `assessment`.
AXIOM_TESTS = []
