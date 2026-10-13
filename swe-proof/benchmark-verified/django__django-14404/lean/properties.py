"""properties.py — G-PBT falsification battery for django__django-14404 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end``, or inside the ``-- proof-start`` / ``-- proof-end`` tactic body,
is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``theorem correct_catchAll`` obligation
survives with a byte-identical statement) and swaps in a candidate impl. It is
checked by the real verifier: ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates — the witness must ELABORATE against the
rival and FAIL against the frozen solution).

PORT PROVENANCE. This battery is a port of the nagini sibling
(../nagini/properties.py), re-expressed against this backend's carrier. The
nagini surface contracts one routine over six flat inputs with fractional heap
permissions; this lean bundle models the SAME routine's purely functional core
as one obligation ``correct_catchAll`` over three inputs plus an opaque
recognition callee. The porting notes per nagini case are in ``assessment`` of
the submitted payload.

DEFENDED SURFACE. One obligation over ``req : Request``, ``url : String``,
``appendSlash : Bool``:

  problem_spec_catchAll req url appendSlash result :=
    -- clause 1 (guard): outside the probing sub-domain, signal not-found
    (¬ (appendSlash = true ∧ url.endsWith "/" = false) → result = notFound)
    ∧
    -- clause 2 (probe): inside it, the recognition callee is driven by the
    -- INTERNAL routing location + "/", and
    (appendSlash = true ∧ url.endsWith "/" = false →
      match resolveLoc (req.routingPath ++ "/") req.urlconf with
      | none   => result = notFound
      | some m => (m.shouldAppend = true  → result = redirect (req.visiblePath ++ "/"))
                ∧ (m.shouldAppend = false → result = notFound))

The load-bearing decision is which of the two tracked locations grounds the
redirect TARGET. The recognition probe is driven by the internal routing
location (``routingPath ++ "/"``); the target the spec pins is the OUTWARD-facing
location (``visiblePath ++ "/"``). ``routingPath`` and ``visiblePath`` are
INDEPENDENT fields — they diverge exactly when a leading deployment prefix is
present — so an impl that grounds the target in ``routingPath`` (== the pre-patch
skeleton in Solution_prepatch.lean) is expressible against this identical spec
and is refuted precisely on the sub-domain where the two locations differ.

ADVERSARIAL READ of the nagini weakness classes on this carrier:
  * FRAME-MUTATION — VACUOUS here, and the second audit DEMONSTRATED it rather
    than arguing it. The nagini class exists because a read-only input carries a
    fractional heap permission an impl can overwrite in place; the dodge it tests
    for is "satisfy the postcondition of the MUTATED input and return that".
    Lean is referentially transparent: ``req`` is an immutable value, there is no
    heap and no aliasing. The closest expressible analogue is a structure update,
    and it was BUILT: an impl doing
    ``let req' := { req with visiblePath := req.visiblePath ++ "/" }`` and then
    returning ``redirect req'.visiblePath`` VERIFIES (exit 0) — because the update
    constructs a NEW value while ``problem_spec_catchAll`` still speaks of the
    ORIGINAL ``req``, so the impl computes exactly gold's function and is simply a
    correct reshape, not a frame violation. There is no way to make the spec's own
    ``req`` observe a write, so there is no rival to build and none was fabricated.
    Its SPIRIT — an output component grounded in the wrong input — is covered
    positively by the wrong-source rival (target from ``routingPath``) and by
    weak-probe-source-swap (probe argument from ``visiblePath``), both refuted by
    clause 2.
  * ADMISSIBILITY / precondition — LANDED (see ``admiss-f2p-shaped``). An
    earlier revision of this file recorded the lane as VACUOUS because
    ``correct_catchAll`` carries no precondition binder (∀ over all inputs).
    That reason is WRONG and the case is now shipped: on a TOTAL carrier the
    analogue of PRECOND-TOO-STRONG is not "a precondition rejects a normal
    input" but "the obligation is UNSATISFIABLE at exactly an F2P-shaped
    input" — i.e. the conjunction of clauses pins no achievable ``Outcome``
    there, so every impl is rejected on the sub-domain the behaviour is
    observed on. That is a real risk on THIS spec: clause 2's some-branch is a
    conjunction of two implications over the same ``result``, and had it pinned
    both a redirect and a not-found at the recognized-and-permitting point, the
    spec would be unsatisfiable exactly where the interesting behaviour lives
    while every reject case above still passed. The positive discharges the
    obligation at that concrete point BY EVALUATION as a ``have``, before
    closing the frozen obligation verbatim.
  * DIVERGENCE / non-termination — VACUOUS here (nagini carries none for this
    instance either). ``implementation_catchAll`` is a total Lean ``def``; a
    diverging impl cannot be written, so the velvet ``partial``-semantics spec
    hole does not arise.

WITNESS SCAFFOLD. The recognition callee ``resolveLoc`` and the config type
``Urlconf`` are ``opaque``. ``Urlconf`` has no ``Nonempty`` instance (checked:
``example : Nonempty Urlconf := by exact inferInstance`` fails to synthesize), so
no concrete ``Request`` value can be built and no witness can ``decide`` the spec
at a ground literal. That is a reason to CONDITION, never a reason to drop a
rival: an opaque term cannot yield ``False``, so the hypothesis-conditioned form
below is always available. Each reject witness instead
QUANTIFIES over ``req`` and CONDITIONS on the opaque term via one hypothesis
(what ``resolveLoc (req.routingPath ++ "/") req.urlconf`` returns), plus, where
the refutation needs it, one hypothesis about a TRANSPARENT String field
(``visiblePath``/``routingPath`` differ, or ``url`` ends in a slash). The
hypotheses are jointly satisfiable — each names a distinct term and asserts one
fact about it — so the gate's inconsistency probe is a no-op. The witness
elaborates against the rival (its answer contradicts the pinned clause on that
sub-domain) and FAILS against the frozen solution (there the two agree, so the
discriminating step — an injectivity/noConfusion clash — does not close).

GOLD-SIDE FAILURES ARE NOT FORGERIES (machine-checked, not argued). Every reject
case here fails on gold with a type/application mismatch rather than a plain
evaluation, which is exactly the shape that has been hollow elsewhere in this
corpus — a gold exit code that would be identical no matter WHAT the witness
claimed. Both halves of the forgery test were run on all nine, and gold's exit
code carries information in both:
  * TYPE-REVEAL. Replacing each witness's final refutation step with a
    deliberate type error (`exact (h3 : Nat)`) makes Lean print the
    discriminating hypothesis's REAL type on each side, and it DIFFERS for every
    case — e.g. gold shows `pure (redirect (visiblePath ++ "/")) = redirect
    (visiblePath ++ "/")` (a reflexive equation, so the injectivity clash cannot
    close) where the wrong-source rival shows `pure (redirect (routingPath ++
    "/")) = redirect (visiblePath ++ "/")` (two distinct opaque-free terms). For
    the guard rivals gold shows the un-taken `if ... then ... else notFound`
    against `notFound` while the rival shows `pure (redirect ...) = notFound`.
    No case reduced to `True` on either side, so nothing was silently proved.
  * CLAIM-FLIP, all nine (CORRECTED by the second audit). An earlier revision of
    this paragraph claimed "both halves were run on all nine". That was an
    OVERSTATEMENT and is now fixed: the hypothesis-flip described below is only
    available on the three `hne`-conditioned cases, and the other six had
    type-reveal evidence only. Both halves now exist for all nine, in the two
    forms the witness shapes admit:
      - The three `hne` cases (wrong-source, no-trailing-slash, target-from-url)
        flip the CONDITION: asserting the two targets are EQUAL where the witness
        asserts they differ. Exit codes INVERT — gold 0, rival 1 — the exact
        mirror of the real witness.
      - The six `noConfusion` cases (drop-optin, drop-trailing, drop-append,
        none-redirects, probe-source-swap, probe-drops-slash) have no hypothesis
        to negate, so the flip is stated at the VALUE level instead: assert that
        the impl DOES produce the Outcome the spec pins at that same
        discriminating point (`implementation_catchAll req … = <pinned Outcome>`).
        Measured, all six: gold exit 0, rival exit 1 (`Tactic 'rfl' failed`).
    So on every one of the nine, gold's exit code tracks WHAT is claimed rather
    than merely how the claim is spelled.
So each rejection attests to the spec, not to a tactic mismatch.

THE REJECT LANE IS COMPLETE BY PROOF, NOT BY SAMPLING (second audit). Two
theorems were proven against the frozen spec, in scope, with real builds:

    spec_functional : problem_spec_catchAll req url a r1 →
                      problem_spec_catchAll req url a r2 → r1 = r2
    spec_iff_gold   : problem_spec_catchAll req url a r ↔
                      r = implementation_catchAll req url a

The first says the spec pins `result` UNIQUELY at every input — the conjunction
of clause 1 and clause 2 is total (the two guards are exact complements) and
every branch of clause 2 fixes `result` outright. The second upgrades that to a
full characterization: the spec's models at each input are exactly the singleton
{gold's output}. Consequences, and they are the strongest statements this lane
can carry:
  * SPEC-TOO-WEAK is IMPOSSIBLE on this obligation. Any impl that verifies is
    extensionally equal to the frozen one, so no wrong impl can ever verify —
    not one already in this file and not one anybody adds later. The nine rivals
    are therefore not a sample hoping to catch a hole; they are demonstrations of
    a hole that provably does not exist. (Checked empirically too: six FURTHER
    wrong impls the battery does not contain — slash prepended, opt-in flag
    inverted, guard conjunction weakened to a disjunction, doubled slash,
    constant not-found, and both probe-and-target swapped at once — were each
    given three different proof attempts, 18 builds, and all 18 were rejected.)
  * SPEC-TOO-STRONG is bounded exactly: the spec admits an impl iff that impl
    computes gold's function. Every faithful correct reshape is admissible, and
    the only thing a soundness control can fail on is the PROOF, never the
    statement. Four independent reshapes were closed to confirm the proofs are
    reachable in practice (guard conjunction reordered, `Option.elim` +
    dependent-if, helper-`def` + `cond`, and a structure-update shadow).

No leaked symbol: this file names no patched file, function, or repo identifier
and narrates no bug→fix mechanism; it describes only the abstract frozen spec.
"""
from pathlib import Path

INSTANCE = "django__django-14404"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
# The gold redirect-target construction (grounded in the outward-facing location).
_REDIR = 'return Outcome.redirect (req.visiblePath ++ "/")'
# The outer probing guard.
_GUARD = 'if appendSlash && !(url.endsWith "/") then'
# The recognized-entry opt-in branch.
_OPTIN = (
    "    | some m =>\n"
    "        if m.shouldAppend then\n"
    '          return Outcome.redirect (req.visiblePath ++ "/")'
)
# The unrecognized-probe branch.
_NONE = "| none => pure ()"

for _a in (_REDIR, _GUARD, _OPTIN, _NONE):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"

# The full frozen impl body (for the two positive-control full-body reshapes).
_IMPL_BODY = (
    "def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :\n"
    "    Outcome := Id.run do\n"
    '  if appendSlash && !(url.endsWith "/") then\n'
    "    let urlconf := req.urlconf\n"
    '    match resolveLoc (req.routingPath ++ "/") urlconf with\n'
    "    | some m =>\n"
    "        if m.shouldAppend then\n"
    '          return Outcome.redirect (req.visiblePath ++ "/")\n'
    "    | none => pure ()\n"
    "  return Outcome.notFound"
)
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor drifted"

# The frozen proof body (replaced wholesale for each positive control so the new
# impl shape closes; the theorem STATEMENT above -- proof-start is untouched).
_PROOF_BODY = (
    "  intro req url appendSlash\n"
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  by_cases hpre : appendSlash = true ∧ url.endsWith \"/\" = false\n"
    "  · obtain ⟨ha, hu⟩ := hpre\n"
    "    refine ⟨fun hbad => absurd ⟨ha, hu⟩ hbad, ?_⟩\n"
    "    intro _\n"
    "    simp only [ha, hu, Bool.not_false, Bool.and_true, if_true, Id.run]\n"
    "    cases hm : resolveLoc (req.routingPath ++ \"/\") req.urlconf with\n"
    "    | none => rfl\n"
    "    | some m =>\n"
    "        refine ⟨fun hs => ?_, fun hs => ?_⟩\n"
    "        · simp only [hs, if_true]; rfl\n"
    "        · simp only [hs, Bool.false_eq_true, if_false]; rfl\n"
    "  · push_neg at hpre\n"
    "    constructor\n"
    "    · intro _\n"
    "      by_cases ha : appendSlash = true\n"
    "      · have hu : url.endsWith \"/\" = true := by\n"
    "          by_contra hu'\n"
    "          exact (hpre ha) (by simpa using hu')\n"
    "        simp only [ha, hu, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false, Id.run]; rfl\n"
    "      · simp only [ha, Bool.false_and, Bool.false_eq_true, if_false, Id.run]; rfl\n"
    "    · intro hbad\n"
    "      exact absurd hbad.1 (by simpa using fun h => (hpre h) hbad.2)"
)
assert _BASE.count(_PROOF_BODY) == 1, "proof-body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness -- expect "verify"). Structurally-different but
# behaviourally-identical CORRECT impls, each with a reproven -- proof-start
# body that actually closes (verified with a real build). The theorem STATEMENT
# is byte-identical; no helper lemma, no sorry, no new axiom.
# ===========================================================================

# (P1) branch-flatten: the `Id.run do` + early-return scaffold is replaced by a
# direct nested `if / match / if-else` returning the value structurally. Same
# value on every input; proof is the frozen tactic body with two `; rfl`s
# dropped (the direct-conditional form leaves the goal already closed).
_POS_FLATTEN_IMPL = (
    "def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :\n"
    "    Outcome :=\n"
    '  if appendSlash && !(url.endsWith "/") then\n'
    '    match resolveLoc (req.routingPath ++ "/") req.urlconf with\n'
    "    | some m =>\n"
    "        if m.shouldAppend then Outcome.redirect (req.visiblePath ++ \"/\")\n"
    "        else Outcome.notFound\n"
    "    | none => Outcome.notFound\n"
    "  else\n"
    "    Outcome.notFound"
)
_POS_FLATTEN_PROOF = (
    "  intro req url appendSlash\n"
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  by_cases hpre : appendSlash = true ∧ url.endsWith \"/\" = false\n"
    "  · obtain ⟨ha, hu⟩ := hpre\n"
    "    refine ⟨fun hbad => absurd ⟨ha, hu⟩ hbad, ?_⟩\n"
    "    intro _\n"
    "    simp only [ha, hu, Bool.not_false, Bool.and_true, if_true]\n"
    "    cases hm : resolveLoc (req.routingPath ++ \"/\") req.urlconf with\n"
    "    | none => rfl\n"
    "    | some m =>\n"
    "        refine ⟨fun hs => ?_, fun hs => ?_⟩\n"
    "        · simp only [hs, if_true]\n"
    "        · simp only [hs, Bool.false_eq_true, if_false]\n"
    "  · push_neg at hpre\n"
    "    constructor\n"
    "    · intro _\n"
    "      by_cases ha : appendSlash = true\n"
    "      · have hu : url.endsWith \"/\" = true := by\n"
    "          by_contra hu'\n"
    "          exact (hpre ha) (by simpa using hu')\n"
    "        simp only [ha, hu, Bool.not_true, Bool.and_false, Bool.false_eq_true, if_false]\n"
    "      · simp only [ha, Bool.false_and, Bool.false_eq_true, if_false]\n"
    "    · intro hbad\n"
    "      exact absurd hbad.1 (by simpa using fun h => (hpre h) hbad.2)"
)
_POS_FLATTEN = _swap(_swap(_BASE, _IMPL_BODY, _POS_FLATTEN_IMPL),
                     _PROOF_BODY, _POS_FLATTEN_PROOF)

# (P2) guard-the-negation / early-exit: each guard failure returns not-found
# immediately (mirroring clause 1 disjunct-by-disjunct), then the recognized
# path runs. Behaviourally identical; proof adapts the same case split to the
# reshaped `if !appendSlash / if url.endsWith / match` cascade.
_POS_EARLYEXIT_IMPL = (
    "def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :\n"
    "    Outcome :=\n"
    "  if !appendSlash then\n"
    "    Outcome.notFound\n"
    '  else if url.endsWith "/" then\n'
    "    Outcome.notFound\n"
    "  else\n"
    '    match resolveLoc (req.routingPath ++ "/") req.urlconf with\n'
    "    | some m => if m.shouldAppend then Outcome.redirect (req.visiblePath ++ \"/\") else Outcome.notFound\n"
    "    | none => Outcome.notFound"
)
_POS_EARLYEXIT_PROOF = (
    "  intro req url appendSlash\n"
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  by_cases hpre : appendSlash = true ∧ url.endsWith \"/\" = false\n"
    "  · obtain ⟨ha, hu⟩ := hpre\n"
    "    refine ⟨fun hbad => absurd ⟨ha, hu⟩ hbad, ?_⟩\n"
    "    intro _\n"
    "    simp only [ha, hu, Bool.not_true, Bool.false_eq_true, if_false, Bool.not_false]\n"
    "    cases hm : resolveLoc (req.routingPath ++ \"/\") req.urlconf with\n"
    "    | none => rfl\n"
    "    | some m =>\n"
    "        refine ⟨fun hs => ?_, fun hs => ?_⟩\n"
    "        · simp only [hs, if_true]\n"
    "        · simp only [hs, Bool.false_eq_true, if_false]\n"
    "  · push_neg at hpre\n"
    "    constructor\n"
    "    · intro _\n"
    "      by_cases ha : appendSlash = true\n"
    "      · have hu : url.endsWith \"/\" = true := by\n"
    "          by_contra hu'\n"
    "          exact (hpre ha) (by simpa using hu')\n"
    "        simp only [ha, hu, Bool.not_true, Bool.false_eq_true, if_false, if_true]\n"
    "      · simp only [ha, Bool.not_false, if_true]\n"
    "    · intro hbad\n"
    "      exact absurd hbad.1 (by simpa using fun h => (hpre h) hbad.2)"
)
_POS_EARLYEXIT = _swap(_swap(_BASE, _IMPL_BODY, _POS_EARLYEXIT_IMPL),
                       _PROOF_BODY, _POS_EARLYEXIT_PROOF)

# (P3, AUDIT-ADDED by the second audit) helper-def + `cond`: the decision is
# factored into a separate impl-region `def` and both branches are taken with
# `cond` rather than `if`. This is the furthest-from-gold correct shape in the
# file -- it changes the DECOMPOSITION (a new named helper), not just the
# spelling of one conditional -- and it is NOT definitionally equal to the frozen
# impl (checked: the `rfl` identity against the frozen def fails, exit 1).
_POS_HELPER_IMPL = (
    "def probeOutcome (req : Request) : Outcome :=\n"
    '  match resolveLoc (req.routingPath ++ "/") req.urlconf with\n'
    "  | some m => cond m.shouldAppend (Outcome.redirect (req.visiblePath ++ \"/\")) Outcome.notFound\n"
    "  | none => Outcome.notFound\n"
    "\n"
    "def implementation_catchAll (req : Request) (url : String) (appendSlash : Bool) :\n"
    "    Outcome :=\n"
    '  cond (appendSlash && !(url.endsWith "/")) (probeOutcome req) Outcome.notFound'
)
_POS_HELPER_PROOF = (
    "  intro req url appendSlash\n"
    "  unfold problem_spec_catchAll implementation_catchAll probeOutcome\n"
    "  by_cases hpre : appendSlash = true ∧ url.endsWith \"/\" = false\n"
    "  · obtain ⟨ha, hu⟩ := hpre\n"
    "    refine ⟨fun hbad => absurd ⟨ha, hu⟩ hbad, ?_⟩\n"
    "    intro _\n"
    "    simp only [ha, hu, Bool.not_false, Bool.and_true, cond_true]\n"
    "    cases hm : resolveLoc (req.routingPath ++ \"/\") req.urlconf with\n"
    "    | none => rfl\n"
    "    | some m =>\n"
    "        refine ⟨fun hs => ?_, fun hs => ?_⟩\n"
    "        · simp only [hs, cond_true]\n"
    "        · simp only [hs, cond_false]\n"
    "  · push_neg at hpre\n"
    "    refine ⟨fun _ => ?_, fun hbad => absurd hbad.1 "
    "(by simpa using fun h => (hpre h) hbad.2)⟩\n"
    "    by_cases ha : appendSlash = true\n"
    "    · have hu : url.endsWith \"/\" = true := by\n"
    "        by_contra hu'\n"
    "        exact (hpre ha) (by simpa using hu')\n"
    "      simp only [ha, hu, Bool.not_true, Bool.and_false, cond_false]\n"
    "    · simp only [ha, Bool.false_and, cond_false]"
)
_POS_HELPER = _swap(_swap(_BASE, _IMPL_BODY, _POS_HELPER_IMPL),
                    _PROOF_BODY, _POS_HELPER_PROOF)


# ===========================================================================
# ADMISSIBILITY (expect "verify"). See the ADMISSIBILITY note in the module
# docstring: on a total carrier the PRECOND-TOO-STRONG analogue is the frozen
# obligation being UNSATISFIABLE at an F2P-shaped input. This case discharges
# the obligation at exactly that point, BY EVALUATION, as a `have` PREPENDED to
# the frozen proof body -- which is then closed verbatim, so the case cannot
# pass by weakening anything. The impl region is the frozen one, untouched.
# ===========================================================================
# The F2P-shaped point: redirection enabled, the locator lacks a trailing slash,
# the probe recognizes the slash-terminated internal location AND permits the
# redirect, and the two tracked locations DIFFER (as they do exactly when a
# leading deployment prefix is configured -- the sub-domain the observed
# behaviour lives on). At that point the obligation must be satisfiable by the
# outward-facing target; `Outcome.redirect (r.visiblePath ++ "/")` is exhibited
# as a witness that it is.
_ADMISS_HAVE = (
    "  -- ADMISSIBILITY: the frozen obligation is SATISFIABLE at an F2P-shaped input\n"
    "  -- (redirection enabled, locator lacking a trailing slash, probe recognizes and\n"
    "  -- permits, and the two tracked locations DIFFER as under a deployment prefix).\n"
    "  have hadm : ∀ (r : Request) (u : String),\n"
    '      u.endsWith "/" = false →\n'
    "      r.visiblePath ≠ r.routingPath →\n"
    '      resolveLoc (r.routingPath ++ "/") r.urlconf = some { shouldAppend := true } →\n'
    '      problem_spec_catchAll r u true (Outcome.redirect (r.visiblePath ++ "/")) := by\n'
    "    intro r u hu _ hm\n"
    "    unfold problem_spec_catchAll\n"
    "    refine ⟨fun hbad => absurd ⟨rfl, hu⟩ hbad, ?_⟩\n"
    "    intro _\n"
    "    rw [hm]\n"
    "    exact ⟨fun _ => rfl, fun hs => by simp at hs⟩\n"
)
# Prepended, so the frozen proof body survives BYTE-IDENTICAL after it.
_POS_ADMISS = _swap(_BASE, _PROOF_BODY, _ADMISS_HAVE + _PROOF_BODY)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes -- expect "reject", each with a
# discriminating witness verified by two real builds).
# ===========================================================================

_RIVAL_WRONGSRC = _swap(_BASE, _REDIR,
                        'return Outcome.redirect (req.routingPath ++ "/")')
_RIVAL_NOSLASH = _swap(_BASE, _REDIR, "return Outcome.redirect req.visiblePath")
_RIVAL_DROP_OPTIN = _swap(
    _BASE, _OPTIN,
    "    | some _ =>\n"
    '        return Outcome.redirect (req.visiblePath ++ "/")')
_RIVAL_DROP_TRAILING = _swap(_BASE, _GUARD, "if appendSlash then")
_RIVAL_DROP_APPEND = _swap(_BASE, _GUARD, 'if !(url.endsWith "/") then')
_RIVAL_NONE_REDIR = _swap(
    _BASE, _NONE,
    '| none => return Outcome.redirect (req.visiblePath ++ "/")')
# (AUDIT) The six rivals above all mutate the redirect TARGET or a guard; none
# perturbs the recognition probe's ARGUMENT, which is the other half of the
# load-bearing decision (clause 2 pins the probe to routingPath ++ "/" while
# pinning the target to visiblePath ++ "/"). The two rivals below attack that
# argument and the third grounds the target in the `url` binder, a source no
# other rival uses. Each is refuted by a witness checked with two real builds.
_RIVAL_PROBE_SRC = _swap(
    _BASE, 'match resolveLoc (req.routingPath ++ "/") urlconf with',
    'match resolveLoc (req.visiblePath ++ "/") urlconf with')
_RIVAL_PROBE_NOSLASH = _swap(
    _BASE, 'match resolveLoc (req.routingPath ++ "/") urlconf with',
    "match resolveLoc req.routingPath urlconf with")
_RIVAL_TARGET_URL = _swap(_BASE, _REDIR,
                          'return Outcome.redirect (url ++ "/")')


# ---- witnesses (see WITNESS SCAFFOLD in the module docstring) ----

_W_WRONGSRC = (
    "example (req : Request)\n"
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true })\n'
    '    (hne : req.visiblePath ++ "/" ≠ req.routingPath ++ "/") :\n'
    '    ¬ problem_spec_catchAll req "" true (implementation_catchAll req "" true) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [he, hm]; simp only [Id.run, Bool.and_true, Bool.not_false, if_true]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := (h2 ⟨trivial, trivial⟩).1 trivial\n"
    "  rw [hm] at h3; simp only [if_true] at h3\n"
    "  exact hne (Outcome.redirect.inj h3).symm"
)

_W_NOSLASH = (
    "example (req : Request)\n"
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true })\n'
    '    (hne : req.visiblePath ++ "/" ≠ req.visiblePath) :\n'
    '    ¬ problem_spec_catchAll req "" true (implementation_catchAll req "" true) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [he, hm]; simp only [Id.run, Bool.and_true, Bool.not_false, if_true]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := (h2 ⟨trivial, trivial⟩).1 trivial\n"
    "  rw [hm] at h3; simp only [if_true] at h3\n"
    "  exact hne (Outcome.redirect.inj h3).symm"
)

_W_DROP_OPTIN = (
    "example (req : Request)\n"
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := false }) :\n'
    '    ¬ problem_spec_catchAll req "" true (implementation_catchAll req "" true) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [he, hm]; simp only [Id.run, Bool.and_true, Bool.not_false, if_true]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := (h2 ⟨trivial, trivial⟩).2 trivial\n"
    "  rw [hm] at h3\n"
    "  exact Outcome.noConfusion h3"
)

_W_DROP_TRAILING = (
    "example (req : Request) (url : String)\n"
    '    (hu : url.endsWith "/" = true)\n'
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true }) :\n'
    "    ¬ problem_spec_catchAll req url true (implementation_catchAll req url true) := by\n"
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [hm]; simp only [Id.run, if_true]\n"
    "  rintro ⟨h1, -⟩\n"
    "  have h3 := h1 (by rw [hu]; simp)\n"
    "  rw [hm] at h3; simp only [Id.run, if_true] at h3\n"
    "  exact Outcome.noConfusion h3"
)

_W_DROP_APPEND = (
    "example (req : Request)\n"
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true }) :\n'
    '    ¬ problem_spec_catchAll req "" false (implementation_catchAll req "" false) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [he, hm]; simp only [Id.run, Bool.not_false, if_true]\n"
    "  rintro ⟨h1, -⟩\n"
    "  have h3 := h1 (by simp)\n"
    "  rw [hm] at h3; simp only [Id.run, if_true] at h3\n"
    "  exact Outcome.noConfusion h3"
)

_W_NONE_REDIR = (
    "example (req : Request)\n"
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = none) :\n'
    '    ¬ problem_spec_catchAll req "" true (implementation_catchAll req "" true) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [he, hm]; simp only [Id.run, Bool.and_true, Bool.not_false, if_true]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := h2 ⟨trivial, trivial⟩\n"
    "  rw [hm] at h3\n"
    "  exact Outcome.noConfusion h3"
)


_W_PROBE_SRC = (
    "example (req : Request)\n"
    '    (hm1 : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true })\n'
    '    (hm2 : resolveLoc (req.visiblePath ++ "/") req.urlconf = none) :\n'
    '    ¬ problem_spec_catchAll req "" true (implementation_catchAll req "" true) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  simp only [he, Id.run, Bool.and_true, Bool.not_false, if_true, hm1, hm2]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := h2 ⟨trivial, trivial⟩\n"
    "  exact Outcome.noConfusion (h3.1 trivial)"
)

_W_PROBE_NOSLASH = (
    "example (req : Request)\n"
    '    (hm1 : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true })\n'
    "    (hm2 : resolveLoc req.routingPath req.urlconf = none) :\n"
    '    ¬ problem_spec_catchAll req "" true (implementation_catchAll req "" true) := by\n'
    '  have he : ("".endsWith "/") = false := by decide\n'
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  simp only [he, Id.run, Bool.and_true, Bool.not_false, if_true, hm1, hm2]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := h2 ⟨trivial, trivial⟩\n"
    "  exact Outcome.noConfusion (h3.1 trivial)"
)

_W_TARGET_URL = (
    "example (req : Request) (url : String)\n"
    '    (hu : url.endsWith "/" = false)\n'
    '    (hm : resolveLoc (req.routingPath ++ "/") req.urlconf = some { shouldAppend := true })\n'
    '    (hne : req.visiblePath ++ "/" ≠ url ++ "/") :\n'
    "    ¬ problem_spec_catchAll req url true (implementation_catchAll req url true) := by\n"
    "  unfold problem_spec_catchAll implementation_catchAll\n"
    "  rw [hu, hm]; simp only [Id.run, Bool.and_true, Bool.not_false, if_true]\n"
    "  rintro ⟨-, h2⟩\n"
    "  have h3 := (h2 ⟨trivial, trivial⟩).1 trivial\n"
    "  rw [hm] at h3; simp only [if_true] at h3\n"
    "  exact hne (Outcome.redirect.inj h3).symm"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-flatten", "kind": "soundness", "expect": "verify",
     "module": _POS_FLATTEN,
     "rationale": "structurally-different but behaviourally-identical CORRECT impl: "
                  "the Id.run-do + early-return scaffold is flattened into a direct "
                  "nested if/match/if-else returning the value, computing the same "
                  "Outcome on every input. It must satisfy both clauses of "
                  "problem_spec_catchAll (guard + probe), with the redirect target still "
                  "grounded in visiblePath; else the postcondition is over-fit to the "
                  "do-block FORM => SPEC-TOO-STRONG. Proof: the frozen case split with "
                  "the two trailing `; rfl`s dropped (the direct-conditional shape leaves "
                  "the goal already closed). Verified by a real build. AUDIT CAVEAT: this "
                  "reshape is DEFINITIONALLY EQUAL to the frozen impl -- checked, "
                  "`example : implementation_alt = implementation_catchAll := rfl` "
                  "elaborates -- because `Id.run do` with early `return` unfolds to exactly "
                  "this nested conditional. So it demonstrates only that the obligation is "
                  "not over-fit to the do-block SPELLING (the frozen tactic body does NOT "
                  "close it unchanged: checked, exit 1), not that the spec admits a "
                  "behaviourally-equal impl of genuinely different structure. "
                  "pos-control-earlyexit carries that load: it is NOT defeq to gold "
                  "(the same `rfl` check fails)."},
    {"id": "pos-control-earlyexit", "kind": "soundness", "expect": "verify",
     "module": _POS_EARLYEXIT,
     "rationale": "structurally-different control shape: each guard failure returns "
                  "not-found immediately (mirroring clause 1 disjunct-by-disjunct), then "
                  "the recognized path runs, keeping the visiblePath-grounded target. "
                  "Behaviourally identical; must verify else SPEC-TOO-STRONG. The proof "
                  "adapts the same case split to the reshaped if-cascade. Verified by a "
                  "real build. This is the load-bearing soundness control: it is NOT "
                  "definitionally equal to the frozen impl (checked, the `rfl` identity "
                  "against the frozen def fails to elaborate), so its verification shows "
                  "the obligation admits a genuinely restructured correct impl."},
    {"id": "pos-control-helper-cond", "kind": "soundness", "expect": "verify",
     "module": _POS_HELPER,
     "rationale": "Added by the second audit as the strongest SPEC-TOO-STRONG control in "
                  "the file: it changes the DECOMPOSITION rather than the spelling of a "
                  "conditional. The recognition-and-target decision is factored out into "
                  "a separate impl-region helper `def probeOutcome`, and both branch "
                  "points are taken with `cond` instead of `if`, so neither the frozen "
                  "impl's do-block scaffold nor its `if` shape survives anywhere. The "
                  "redirect target stays grounded in visiblePath and the probe in "
                  "routingPath ++ \"/\", so it computes gold's function on every input and "
                  "MUST verify; if it were rejected => SPEC-TOO-STRONG (the obligation "
                  "over-fit to a single-def decomposition). Checked with real builds: NOT "
                  "definitionally equal to the frozen impl (the `rfl` identity against "
                  "the frozen def fails, exit 1), the frozen tactic body does NOT close it "
                  "(exit 1, `Tactic 'rfl' failed`), and this module with its own reproven "
                  "body verifies (exit 0). Adding a helper `def` is inside the admissible "
                  "variant scope (the impl region is elided by the consumer spec view and "
                  "variant_scope bans only new theorems/axioms), and variant_problems "
                  "reports [] with the theorem statement byte-identical."},

    # ---- (AUDIT-ADDED a8) admissibility: the lane the port dropped ----
    {"id": "admiss-f2p-shaped", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "Added by audit: this battery carried NO admissibility case, and the "
                  "reason recorded for dropping it (\"correct_catchAll has no "
                  "precondition binder, so there is nothing to admit\") is not a valid "
                  "one -- on a TOTAL carrier the PRECOND-TOO-STRONG analogue is the "
                  "frozen obligation being UNSATISFIABLE at exactly an F2P-shaped "
                  "input. That is a live risk on this spec, because clause 2's "
                  "some-branch conjoins TWO implications over the same `result`: had "
                  "they pinned both a redirect and a not-found at the "
                  "recognized-and-permitting point, no impl could satisfy the spec on "
                  "the sub-domain where the observed behaviour lives, and every "
                  "uniqueness rival above would still have been rejected exactly as "
                  "recorded -- a battery reporting SOUND over a spec nothing can "
                  "satisfy. This case forecloses that: the prepended `have` "
                  "discharges problem_spec_catchAll BY EVALUATION at the concrete "
                  "point (appendSlash = true, url lacking a trailing slash, probe "
                  "recognizes-and-permits, and visiblePath != routingPath as under a "
                  "configured deployment prefix), exhibiting "
                  "`redirect (visiblePath ++ \"/\")` as an achievable Outcome there. "
                  "The frozen proof body then follows BYTE-IDENTICAL and the impl "
                  "region is untouched, so nothing is weakened to make it pass. "
                  "Checked with real builds: this module verifies (exit 0), and the "
                  "`have` has TEETH -- the same block claiming `notFound` satisfies "
                  "the spec at that point fails (exit 1), as does the one claiming "
                  "`redirect (routingPath ++ \"/\")` does, so the ground evaluation "
                  "really does pin the outward-facing target and is not a tautology. "
                  "If it were rejected => PRECOND-TOO-STRONG (obligation "
                  "unsatisfiable on the F2P sub-domain)."},

    # ---- uniqueness rivals (must be REJECTED, each with a checked witness) ----
    {"id": "weak-wrong-source", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONGSRC,
     "refinement": "this is EXACTLY the pre-patch skeleton (== Solution_prepatch.lean): "
                   "ground the redirect target in the INTERNAL routing location instead "
                   "of the outward-facing one. The faithful real patch keeping the "
                   "routing-location target drops the leading deployment prefix, so under "
                   "a configured prefix it redirects to the prefix-less location and FAILS "
                   "both F2P tests (the prefix must be PRESENT in the target). "
                   "verify-not-resolve.",
     "rationale": "rejection source: clause 2's some-branch, which pins result = "
                  "redirect (visiblePath ++ \"/\"). The rival returns redirect "
                  "(routingPath ++ \"/\"); visiblePath and routingPath are independent "
                  "Request fields the spec never equates, so on the sub-domain where they "
                  "differ the rival contradicts the clause. If it verified => "
                  "SPEC-TOO-WEAK.",
     "witness": _W_WRONGSRC},
    {"id": "weak-no-trailing-slash", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOSLASH,
     "refinement": "returning the visible location WITHOUT the appended slash is not a "
                   "slash-appending redirect at all -- it targets the same slash-less "
                   "location, an immediate redirect loop, and FAILS every F2P/P2P "
                   "slash-redirect assertion (the target must carry its trailing slash). "
                   "verify-not-resolve.",
     "rationale": "rejection source: clause 2's some-branch. Control flow is pinned "
                  "correctly (redirects on exactly the four-guard sub-domain), but the "
                  "target is visiblePath, not visiblePath ++ \"/\". The trailing slash "
                  "(a single code point) is load-bearing. If it verified => SPEC-TOO-WEAK.",
     "witness": _W_NOSLASH},
    {"id": "weak-drop-optin-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_OPTIN,
     "refinement": "dropping the opt-in check makes the routine redirect even when the "
                   "recognized entry does NOT permit automatic slash-redirection. The "
                   "faithful real patch removing that check redirects entries that "
                   "explicitly disabled it, breaking the behaviour the regression suite "
                   "pins (such an entry must signal not-found, not redirect). "
                   "verify-not-resolve.",
     "rationale": "rejection source: clause 2's `m.shouldAppend = false → result = "
                  "notFound` arm. On a recognized entry with shouldAppend = false the "
                  "rival redirects; the spec requires not-found. Attacks the "
                  "ResolveMatch.shouldAppend binder. If it verified => SPEC-TOO-WEAK.",
     "witness": _W_DROP_OPTIN},
    {"id": "weak-drop-trailing-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_TRAILING,
     "refinement": "dropping the `not already-ends-in-slash` guard makes the routine "
                   "redirect a locator that already ends in a slash, producing a "
                   "double-slash target / duplicate redirect the surrounding catch-all "
                   "behaviour forbids. verify-not-resolve.",
     "rationale": "rejection source: clause 1 (the guard arm). On an input whose url "
                  "already ends in a slash the guard conjunction is false, so the spec "
                  "requires not-found, but the rival ignores the trailing-slash test and "
                  "redirects. Attacks the `url` binder (via url.endsWith \"/\"). If it "
                  "verified => SPEC-TOO-WEAK (partial-domain).",
     "witness": _W_DROP_TRAILING},
    {"id": "weak-drop-append-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_APPEND,
     "refinement": "dropping the redirection-enabled toggle makes the routine redirect "
                   "even when automatic slash-redirection is globally disabled. The "
                   "faithful real patch removing that toggle would issue redirects the "
                   "deployment turned off, breaking the behaviour observed when the flag "
                   "is false. verify-not-resolve.",
     "rationale": "rejection source: clause 1 (the guard arm). With appendSlash = false "
                  "the guard conjunction is false, so the spec requires not-found, but "
                  "the rival ignores the toggle and redirects. Attacks the `appendSlash` "
                  "binder -- the only reject witness that moves it to false. If it "
                  "verified => SPEC-TOO-WEAK.",
     "witness": _W_DROP_APPEND},
    {"id": "weak-none-redirects", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONE_REDIR,
     "refinement": "redirecting on an UNRECOGNIZED probe means the routine issues a "
                   "permanent redirect to a locator the router never recognized -- a "
                   "redirect to a not-found target. The faithful real patch redirecting "
                   "on the resolver-miss path would send permanent redirects for URLs "
                   "that should 404, breaking the not-found behaviour. verify-not-resolve.",
     "rationale": "rejection source: clause 2's `none => result = notFound` arm. When the "
                  "recognition callee returns none the spec requires not-found, but the "
                  "rival redirects. Attacks the none-branch of the resolveLoc match "
                  "(the branch no other rival probes). If it verified => SPEC-TOO-WEAK.",
     "witness": _W_NONE_REDIR},

    # ---- (AUDIT-ADDED) rivals attacking the probe ARGUMENT and the `url` binder ----
    {"id": "weak-probe-source-swap", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PROBE_SRC,
     "refinement": "the two tracked locations are interchanged in the RECOGNITION step: "
                   "the probe is driven by the outward-facing location instead of the "
                   "internal routing one. Under a configured deployment prefix the "
                   "outward-facing location carries that prefix, so the probe asks the "
                   "router about a locator that does not exist in its table -- the routine "
                   "then signals not-found for locators that a correct probe recognizes "
                   "(and conversely for a prefix-shaped table). This is the mirror image of "
                   "the target-side error, and no other rival perturbs the probe argument. "
                   "verify-not-resolve.",
     "rationale": "rejection source: clause 2, which pins the probe to "
                  "resolveLoc (routingPath ++ \"/\") -- not merely the TARGET. Because the "
                  "spec fixes the probe argument, a rival probing at visiblePath ++ \"/\" "
                  "answers from a different point of the opaque callee and contradicts the "
                  "clause on the sub-domain where the two locations differ. Attacks the "
                  "resolveLoc ARGUMENT (the binder the original six rivals left "
                  "unperturbed). If it verified => SPEC-TOO-WEAK.",
     "witness": _W_PROBE_SRC},
    {"id": "weak-probe-drops-slash", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PROBE_NOSLASH,
     "refinement": "the probe is driven by the internal routing location WITHOUT appending "
                   "the slash, i.e. it asks whether the locator the routine already failed "
                   "on is recognized, rather than whether its slash-terminated form is. "
                   "That is not a slash-appending probe at all: the whole point is to test "
                   "the candidate locator, so the routine would answer from the wrong "
                   "recognition point and redirect (or not) on the wrong sub-domain. "
                   "verify-not-resolve.",
     "rationale": "rejection source: clause 2's pinned probe argument "
                  "routingPath ++ \"/\". The rival probes at routingPath, a DIFFERENT "
                  "point of the opaque callee, so its recognition answer is unconstrained "
                  "by the clause and contradicts it wherever the two answers differ. "
                  "Attacks the slash-append in the probe argument, which no other rival "
                  "touches. If it verified => SPEC-TOO-WEAK.",
     "witness": _W_PROBE_NOSLASH},
    {"id": "weak-target-from-url", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TARGET_URL,
     "refinement": "the redirect target is built from the ROUTINE'S OWN `url` argument "
                   "rather than from either tracked request location. The `url` argument is "
                   "the trailing portion the catch-all was invoked on, not a full location, "
                   "so redirecting to it drops both the deployment prefix and the leading "
                   "segments and sends the client to a locator that is not the requested "
                   "one. verify-not-resolve.",
     "rationale": "rejection source: clause 2's some-branch, which pins result = "
                  "redirect (visiblePath ++ \"/\"). `url` is an INDEPENDENT binder the spec "
                  "never equates to visiblePath, so on the sub-domain where they differ the "
                  "rival contradicts the clause. This is the only rival grounding the target "
                  "in the `url` binder rather than a Request field. If it verified => "
                  "SPEC-TOO-WEAK.",
     "witness": _W_TARGET_URL},
]
