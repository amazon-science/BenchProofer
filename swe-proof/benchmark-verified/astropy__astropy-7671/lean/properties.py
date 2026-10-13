"""properties.py — G-PBT falsification battery for astropy__astropy-7671 (lean).

NOT a Lean file; a record of adversarially-reasoned cases the G-PBT gate
executes. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery touches only text inside the
``-- impl-start`` / ``-- impl-end`` region and, for a case that legitimately
re-proves, inside ``-- proof-start`` / ``-- proof-end``), so
``markers.same_spec`` holds by construction and every ``theorem correct_*``
STATEMENT stays byte-identical. ``expect:"verify"`` passes iff the variant is in
scope AND the file elaborates with the obligation closed (no ``sorry`` /
``admit`` / new ``axiom``); ``expect:"reject"`` passes iff the variant is in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

=========================================================================
DEFENDED SURFACE
=========================================================================

One modeled behavior, one obligation (``correct_versionAtLeast``):

    problem_spec_versionAtLeast (haveVersion version : List Char)
        (inclusive : Bool) (result : Option Bool) : Prop :=
      if h : orderable haveVersion (normalizeVersion version) = true then
        result = some (if inclusive
                       then versionGe haveVersion (normalizeVersion version) h
                       else versionGt haveVersion (normalizeVersion version) h)
      else
        result = none

Three input binders — ``haveVersion`` (the available version), ``version`` (the
required minimum) and ``inclusive`` (which ordering to use) — and no
precondition hypothesis: the ``∀`` in ``correct_versionAtLeast`` is unguarded,
so the behavior is total and every input is in domain.

THE ORDERING IS PARTIAL, AND IS CARRIED AS WHAT A PARTIAL OPERATION IS: an
operation on its domain. ``orderable a b`` is the (total) question of whether
the pair is one the ordering compares; ``versionGe a b h`` / ``versionGt a b h``
are applicable only together with ``h``, the fact that it is. That shape is what
makes the behavior's partiality expressible in a language of total functions,
and it is load-bearing in a way the value-level clauses are not: over a total
``Bool`` carrier the ordering could be applied anywhere and a discarded
application would be erased, and over a total ``Option Bool`` carrier it could
still be APPLIED anywhere (a ``none`` merely reports it). Here there is no term
at all that names the ordering's answer at a pair whose commensurability has not
been settled first — so an implementation that would put the ordering to the
un-reduced pair must first ask a question that always completes.

The postcondition is a single top-level clause: a dependent conditional pinning
the result to a comparison. It is load-bearing in FIVE independent ways, and
each is a separate degree of freedom a wrong implementation can abuse:

  (C1) WHICH VALUE is compared — the required string reduced to its leading
       release-number prefix (``normalizeVersion version``), never the raw
       required string;
  (C2) WHICH OPERAND is reduced — the reduction applies to the required
       minimum, and ``haveVersion`` is passed through untouched;
  (C3) OPERAND ORDER — ``haveVersion`` is the left operand of the comparison
       and the reduced required value the right one;
  (C4) WHICH ORDERING — the non-strict comparison exactly when ``inclusive``
       holds, the strict one otherwise, and the SAME reduced value feeds both
       branches.
  (C5) DEFINEDNESS, in both directions. The result carries a verdict exactly
       when the REDUCED pair is one the ordering has a value at, and that
       verdict is the ordering's answer there; it carries none exactly when the
       reduced pair is not one of those. So the ordering's definedness at the
       UN-reduced pair cannot influence the outcome — the decision is available
       whenever the reduced comparison is, even at a raw pair the ordering says
       nothing about — and, because the ordering is an operation on its domain,
       the raw pair is not one this behavior can put the ordering to at all
       without first settling a question that has an answer wherever it is
       asked.

=========================================================================
ADVERSARIAL READ OF EACH CLASS ON THIS CARRIER
=========================================================================

* FRAME / PERMISSION MUTATION — **VACUOUS**. Lean is referentially transparent:
  the inputs are immutable ``List Char`` values, there is no heap permission to
  hold at a fraction, no aliasing, and no way to write through an input
  reference. The two nagini frame-mutation rivals have no expressible instance
  here. No substitute is fabricated for them.

* DIVERGENCE / NON-TERMINATION — **nothing to ship on lean**, but not because
  the variant is unwritable: a ``partial def`` self-recursive implementation is
  admissible to the scope check (measured: ``variant_problems`` returns ``[]``
  for one). What kills it is the OBLIGATION — such an impl does not verify here
  (measured: the frozen script's ``rfl`` fails against it, exit 1), because a
  ``partial def`` is opaque to definitional unfolding rather than vacuously
  satisfying its spec. So the disposition (no rival to ship, no spec hole to
  record) is right, and it is NOT the known-hole disposition that applies to
  velvet under partial termination semantics
  (``set_option loom.semantics.termination "partial"``), where such an impl
  verifies VACUOUSLY. Lean's total-``def`` obligation is what separates the two.

* UNGROUNDED-ORACLE ECHO — **VACUOUS for the reduction, tested for the
  verdict**. The reduction is modeled DEEPLY: ``normalizeVersion`` /
  ``releasePrefix`` are ordinary total ``def``s fully unfolded over ``version``,
  so the spec is a function OF the binders rather than an answer key. Returning
  that expression directly IS the specified behavior, which is why it appears
  below as an honest cheapest-implementation POSITIVE control rather than as a
  rival. The verdict half is a different question, and it was attacked: an impl
  keeping the specified definedness exactly while manufacturing the verdict from
  the arguments (a length comparison instead of the ordering) is rejected —
  see PROBED AND NOT SHIPPED.

* PARTIAL-DOMAIN / VALUE — **most of the battery**. This is where every ported
  nagini rival lands, re-expressed against clauses C1–C4.

* CONTROL-FLOW EFFECT — **expressible here, and both halves are pinned**. On a
  referentially transparent carrier "right value, wrong effect" normally has no
  instance. It has one here because the modeled callee is partial: an
  implementation can differ from the specified behavior not in what it answers
  but in WHERE it answers, by making its verdict's existence depend on a
  comparison the specified behavior never needs. That is the rival
  ``weak-definedness-leak``. Its mirror image is the positive control
  ``pos-guarded-raw-probe``, which puts the ordering to the un-reduced pair
  after settling commensurability there and discards the answer: the value is
  the specified one at every input and the extra step always completes, so it
  MUST verify. The two together are the precise statement of C5 — a guarded
  probe is admitted, a verdict conditioned on the raw pair is not — and shipping
  only the rival would leave the clause looking like a ban on touching the raw
  pair, which would be over-fitting.

A note on the OPAQUE carrier. ``orderable`` / ``versionGe`` / ``versionGt`` are
``opaque``, so no literal input computes a truth value and ``decide`` is useless
on the result. The witnesses therefore CONDITION on the carrier. Two shapes
occur, and each conditions on facts that are OBSERVED of the real callee rather
than merely consistent:

  * a VALUE witness assumes the pair the rival compares and the pair the spec
    compares are both ones the ordering answers at, and that it answers
    differently — exactly the sub-domain where the rival is wrong;
  * a DEFINEDNESS witness assumes the raw pair is one the ordering does NOT
    answer at while the reduced pair is one it does — the input the issue report
    itself exhibits.

The second shape is available only because definedness is nameable on this
carrier, and it is what lets the definedness rival be refuted at the instance's
own input point rather than at a contrived one. What stays fully transparent,
and is what every witness also exploits, is the reduction itself:
``releasePrefix "0.12dev".toList = some "0.12".toList`` closes by ``rfl``.

=========================================================================
BINDER COVERAGE
=========================================================================

All three binders are varied across the six reject witnesses; no binder is held
at one value by every rival, and the six witnesses probe six DISTINCT input
points:

  * ``version`` — five distinct values, spanning both halves of the
    reduction's domain: qualifier-BEARING (``0.12dev``, ``1.14dev``,
    ``1.2rc1``, where the reduction strictly shortens the string) and
    qualifier-FREE (``0.12.1``, ``0.12``, where it is the identity). A rival
    that mishandled only the no-op case would be invisible to a battery whose
    every witness carried a qualifier, and vice versa.
  * ``haveVersion`` — five distinct values, INCLUDING one that itself carries
    a qualifier (``0.12.1dev``, at ``weak-reduce-wrong-side``). That is the
    point where reducing the wrong operand becomes observable at all: a rival
    which reduced ``haveVersion`` instead of ``version`` agrees with the spec at
    every witness whose ``haveVersion`` has nothing to reduce, so holding this
    binder at a plain numeric string would let clause C2 go entirely untested.
  * ``inclusive`` — BOTH values. ``weak-reduce-wrong-side`` is refuted at
    ``false`` (the strict branch) and the other five at ``true``, so neither
    arm of C4's conditional is a branch no witness enters.

A CONSTRAINT on where a conditioned witness may be pinned, which cuts across
this coverage. The gate's consistency probe rules out a self-contradictory
hypothesis, not an UNINHABITED one, so a witness can pass every build while
describing a point the modeled behavior never reaches. Two rules keep that from
happening here, and every hypothesis below was checked against the real callee's
observed output:

  * a VALUE witness must be pinned where BOTH compared pairs are ones the
    ordering really answers at — which, for the rivals whose defect is about the
    reduced versus the un-reduced/overshot required value, means an
    ``haveVersion`` that is the reduced value itself rather than a version
    comfortably above it (measured: ``0.12`` answers ``False`` against
    ``0.12dev`` and ``True`` against ``0.12``, while ``0.12.2`` has no answer
    against ``0.12dev`` at all);
  * a DEFINEDNESS witness must assume ``= false`` only where the ordering
    really has no answer (measured: ``0.12.2`` against ``0.12dev``, and
    ``0.12.2`` against ``dev``) and ``= true`` only where it really has one.

=========================================================================
PORTED FROM NAGINI — and what was DROPPED, with reasons
=========================================================================

PORTED:
  (P1) pos-delegate-grounded-oracle  -> ``pos-closed-form``
  (P2) pos-single-return-reshape     -> ``pos-option-getD`` and
                                        ``pos-negated-flag``
  (A1) admiss-self-call              -> ``admiss-ground-instances``
  (R3) rival-no-strip-raw            -> ``weak-compare-unreduced``
  (R6) rival-keep-marker             -> ``weak-prefix-overshoot`` (same defended
       behavior — a reduction that leaves non-numeric material in the compared
       value — re-expressed for this carrier, where the reduction is a string
       prefix rather than an accumulated segment list, so "keep the marker"
       becomes "keep one character too many")

ADDED HERE (no nagini counterpart — these are not ports):
  ``weak-reduce-strict-only``  — C1 per-branch; the honest replacement for the
       two dropped ordering rivals, carrying a refinement that DOES hold.
  ``weak-reduce-wrong-side``   — C2, which operand is reduced.
  ``weak-operands-transposed`` — C3, operand order.
  ``weak-definedness-leak``    — C5, where the behavior answers.
  ``pos-guarded-raw-probe``    — C5's other half: the guarded probe the clause
       must NOT forbid.

DROPPED, with reasons (see ``assessment`` in the submitted payload):
  (R1) frame-mutate-want, (R2) frame-mutate-have — VACUOUS on this carrier
       (referential transparency; no permission system to subvert).
  (R4) rival-ge-gt-swap, (R5) rival-inclusive-only-gt — DROPPED as REJECT cases
       because their REFINEMENT ARGUMENT DOES NOT HOLD on this instance, not
       because they were hard to refute. Both are refutable here (each mismatches
       the spec at the equality boundary, and a witness for either elaborates
       against the rival and fails on gold). But a reject case must also argue
       that the rival's faithful real patch would NOT resolve the F2P, and that
       argument is FALSE: measured against the real comparison callee, the
       non-strict and strict orderings AGREE at every one of the six inputs the
       F2P exercises (the available version is never exactly equal to any
       reduced required version among them, and the strict-versus-inclusive flag
       is never passed a non-default value by that test), so the swapped patch
       passes the F2P and every P2P. Shipping them as ``expect="reject"`` would
       have asserted a verify-does-not-imply-resolve break that does not exist.
       The equality-boundary attack is retained in a form whose refinement DOES
       hold: ``weak-reduce-strict-only``, which makes the two branches disagree
       about C1 (which value is compared) rather than about C4 alone, and whose
       faithful patch does fail the F2P.

  AXIOM_TESTS — dropped wholesale; the axiom lane is G-AX's job and this gate
       ignores it.

=========================================================================
PROBED AND NOT SHIPPED (independent audit, all machine-checked)
=========================================================================

Wrong impls tried against the frozen spec to look for a SPEC-TOO-WEAK hole.
Every one was REJECTED, so no hole was found. Eleven of them are recent, run
through ``swebench_unified.adversary weakness`` (which re-checks
``same_spec`` and admissibility first) against a spec whose ordering is carried
on its domain, each carrying a multi-tactic proof attempt rather than the frozen
script so that a rejection is the spec's and not a tuned script's:

  * the raw pair consulted and its answer discarded, in three shapes (the
    consultation first, the consultation behind an identity test, the
    consultation propagated) — all rejected;
  * the un-reduced comparison (partial-domain);
  * a verdict manufactured from the arguments' lengths while keeping the
    specified definedness exactly (ungrounded-oracle echo);
  * the empty required string and the aliased ``haveVersion = reduced``
    case answered by fiat (boundary);
  * reduce-on-one-branch-only (control flow) and operands transposed;
  * refuse to answer wherever the reduction strictly shortens the required
    string (definedness at the reduction rather than at the comparison);
  * reduce only when the required string is short (partial-domain);
  * DERIVE the un-reduced pair's commensurability from the reduced pair's
    instead of establishing it, so the ordering can be put to the raw pair —
    the evasion this carrier exists to block. Rejected: the two facts are
    unrelated, so no term of that type can be produced, and the file does not
    elaborate.

Six older wrong impls were tried and all REJECTED (an impl ignoring the ordering
flag entirely; the ordering-swapped rival; an epoch-blind reduction; a reduction
truncated after the first dotted group; the ``none`` fallback returning ``[]``; a
constant ``true``), and four correct reshapes were tried and all VERIFIED (the
comparison selected into a local function value; an explicit ``match`` on the
optional prefix; ``cond`` with both branches computed eagerly;
``Option.elim``). The admissibility case was checked non-vacuous by the
complementary experiment: the same ground-instance shape asserting the RAW
required string satisfies the spec FAILS, so the discharged instances are not
instances anything would discharge.

The fallback-empty, flipped-negation and epoch-blind rivals are all genuinely
WRONG and each had a witness that discriminated. They are NOT shipped for the
same reason the two nagini ordering rivals were dropped: their faithful real
patches all PASS the F2P and every P2P, so shipping them as ``expect="reject"``
would assert a verify-does-not-imply-resolve break that does not exist. In
particular the epoch group is unreachable from this instance's tests — no F2P
input and no import-time minimum carries a ``!`` — so the epoch clause is
specified but not differentially defended, which is a property of the INSTANCE,
not a defect here.

Case count: 11 spec cases (5 must-verify, 6 must-reject).
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7671"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique
# in the frozen file (asserted at manifest load, so any drift in Solution.lean
# breaks this module loudly instead of silently mis-targeting a swap).
# ---------------------------------------------------------------------------

# The full body of the single impl region.
_IMPL = (
    "  let mut ver := version\n"
    "  if let some p := releasePrefix ver then\n"
    "    ver := p\n"
    "  if h : orderable haveVersion ver = true then\n"
    "    if inclusive then\n"
    "      return some (versionGe haveVersion ver h)\n"
    "    else\n"
    "      return some (versionGt haveVersion ver h)\n"
    "  else\n"
    "    return none"
)

# The impl SIGNATURE + body, for the one positive control that drops the
# `Id.run do` wrapper entirely and returns a plain expression.
_IMPL_SIG = (
    "def implementation_versionAtLeast (haveVersion version : List Char) "
    "(inclusive : Bool) :\n    Option Bool := Id.run do\n" + _IMPL
)

# The full tactic body of the single proof region.
_PROOF = (
    "  intro haveVersion version inclusive\n"
    "  rcases hp : releasePrefix version with _ | p <;>\n"
    "    simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "      normalizeVersion, hp, Id.run] <;>\n"
    "    split <;> cases inclusive <;> rfl"
)

for _anchor in (_IMPL, _IMPL_SIG, _PROOF):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"anchor drift / not unique: {_anchor[:60]!r}")


# ---------------------------------------------------------------------------
# Witness scaffolding.
#
# The callees are `opaque`, so the spec's value cannot be computed at any
# literal input. What IS transparent is the reduction, so each witness
# (a) discharges the reduction at its concrete input by `rfl`, (b) discharges
# the specified and the rival's commensurability guards from the hypotheses
# `h1` / `h2` it conditions on, (c) reduces the `Id.run do` wrapper away, and
# (d) concludes. The hypotheses name at most two distinct opaque applications,
# so they are jointly satisfiable (checked by the gate's consistency probe), and
# each is a fact OBSERVED of the real callee (see BINDER COVERAGE).
# ---------------------------------------------------------------------------

_SIMP = (
    "  simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "    normalizeVersion, hp, Id.run, dif_pos h1, dif_pos h2, if_true]\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify".
#
# Each is a structurally DIFFERENT but CORRECT implementation, re-proved inside
# the proof region with the theorem statement byte-identical. Nothing is
# assumed: no new lemma, no `sorry`, no `native_decide`. If any of these were
# rejected the spec would be over-fit to the frozen implementation's syntactic
# form => SPEC-TOO-STRONG.
# ===========================================================================

# (P1) The cheapest honest implementation: the closed form, returned directly,
# with no mutable local and no `Id.run do` wrapper at all. Ports nagini (P1).
_POS_CLOSED_FORM = _swap(
    _swap(
        _BASE, _IMPL_SIG,
        "def implementation_versionAtLeast (haveVersion version : List Char) "
        "(inclusive : Bool) :\n    Option Bool :=\n"
        "  if h : orderable haveVersion (normalizeVersion version) = true then\n"
        "    some (if inclusive\n"
        "          then versionGe haveVersion (normalizeVersion version) h\n"
        "          else versionGt haveVersion (normalizeVersion version) h)\n"
        "  else\n"
        "    none"),
    _PROOF,
    "  intro haveVersion version inclusive\n"
    "  unfold problem_spec_versionAtLeast implementation_versionAtLeast\n"
    "  split <;> simp_all")

# (P2) The reduction expressed as a total default-taking read of the optional
# prefix rather than a conditional rebinding of a mutable local. Same value at
# every input. Ports nagini (P2).
_POS_OPTION_GETD = _swap(
    _swap(
        _BASE, _IMPL,
        "  let ver := (releasePrefix version).getD version\n"
        "  if h : orderable haveVersion ver = true then\n"
        "    if inclusive then\n"
        "      return some (versionGe haveVersion ver h)\n"
        "    else\n"
        "      return some (versionGt haveVersion ver h)\n"
        "  else\n"
        "    return none"),
    _PROOF,
    "  intro haveVersion version inclusive\n"
    "  rcases hp : releasePrefix version with _ | p <;>\n"
    "    simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "      normalizeVersion, hp, Id.run, Option.getD_some, Option.getD_none] <;>\n"
    "    split <;> cases inclusive <;> rfl")

# (P2b) Branch REORDER: the flag is tested negated and the two arms exchanged,
# so the strict comparison is reached through the `then` arm. Semantically
# identical. A second reshape positive, aimed at the conditional in clause C4
# rather than at the reduction.
_POS_NEGATED_FLAG = _swap(
    _BASE, _IMPL,
    "  let mut ver := version\n"
    "  if let some p := releasePrefix ver then\n"
    "    ver := p\n"
    "  if h : orderable haveVersion ver = true then\n"
    "    if !inclusive then\n"
    "      return some (versionGt haveVersion ver h)\n"
    "    else\n"
    "      return some (versionGe haveVersion ver h)\n"
    "  else\n"
    "    return none")

# (P3) The ordering PUT TO THE UN-REDUCED PAIR, correctly: commensurability
# there is established first and the answer is then discarded. The returned
# value is the specified one at every input, and the extra step is one that
# always completes — so this MUST verify. It is the control that separates what
# clause C5 actually forbids (a verdict whose existence depends on the raw pair,
# the rival `weak-definedness-leak`) from what it must NOT forbid (looking at
# the raw pair at all, which would be over-fitting: a behavior may settle a
# total question and drop the answer). Note that the do-block places the whole
# continuation inside both arms of the guard, so this is not a syntactic no-op:
# the proof needs the extra `split`.
_POS_RAW_PROBE = _swap(
    _swap(
        _BASE, _IMPL,
        "  let mut ver := version\n"
        "  if let some p := releasePrefix ver then\n"
        "    ver := p\n"
        "  if hraw : orderable haveVersion version = true then\n"
        "    let _probe := versionGe haveVersion version hraw\n"
        "    pure ()\n"
        "  if h : orderable haveVersion ver = true then\n"
        "    if inclusive then\n"
        "      return some (versionGe haveVersion ver h)\n"
        "    else\n"
        "      return some (versionGt haveVersion ver h)\n"
        "  else\n"
        "    return none"),
    _PROOF,
    "  intro haveVersion version inclusive\n"
    "  rcases hp : releasePrefix version with _ | p <;>\n"
    "    simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "      normalizeVersion, hp, Id.run] <;>\n"
    "    split <;> (try split) <;> cases inclusive <;> rfl")


# ===========================================================================
# ADMISSIBILITY — expect "verify".
#
# `correct_versionAtLeast` binds no precondition hypothesis (the behavior is
# total), so the nagini precondition-admission probe has no binder to attack.
# The honest analogue discharges the spec predicate at SEVEN ground inputs drawn
# from the behavior's real usage, and pins the reduction's value at each by
# `rfl`. Because the ordering is carried on its domain, a ground instance is
# stated as "for any fact that this pair is one the ordering answers at, the
# specified result at this input is THIS", which is the strongest form available
# and the one that cannot be discharged by accident. If any instance could not
# be discharged, the behavior would be unsatisfiable at an input it must admit:
# the analogue of PRECOND-TOO-STRONG. Ports nagini (A1).
#
# One instance is in the NO-VERDICT branch (`adm_no_prefix`): a required string
# with no release-number prefix at all, where the reduction is the identity by
# its fallback and the ordering genuinely has no answer against the available
# version (measured on the real callee: it raises). Without it the else-branch of
# the spec would be a branch no must-verify case ever enters.
#
# The last three pin the DECIMAL-DIGIT boundary, each transcribed from the real
# callee's observed output rather than from a reading of the pattern, because the
# three cases fall differently and only observation distinguishes them:
#   * a non-ASCII decimal digit INSIDE a release number extends it, so the
#     reduction is the identity and the whole string reaches the comparison;
#   * a non-ASCII decimal digit at the FRONT is not a release-number start (the
#     leading class is ASCII-only), so there is no prefix at all;
#   * a numeric-but-not-decimal character (a superscript) does NOT extend a
#     release number, so the reduction stops before it.
# A model that gated every digit on ASCII, or one that gated on "is numeric",
# gets a different answer on the first or the third of these; both were live
# mis-modelings, so these instances are what hold the boundary in place.
# ===========================================================================

_ADMISS = _swap(
    _BASE, _PROOF,
    '  have red_qualifier : normalizeVersion "0.12dev".toList\n'
    '      = "0.12".toList := by rfl\n'
    '  have adm_qualifier : ∀ h : orderable "0.12.2".toList "0.12".toList = true,\n'
    '      problem_spec_versionAtLeast "0.12.2".toList "0.12dev".toList true\n'
    '        (some (versionGe "0.12.2".toList "0.12".toList h)) := by\n'
    "    intro h\n"
    "    simp only [problem_spec_versionAtLeast, red_qualifier, dif_pos h,\n"
    "      if_true]\n"
    '  have red_above : normalizeVersion "1.2rc1".toList = "1.2".toList := by rfl\n'
    '  have adm_above : ∀ h : orderable "0.12.2".toList "1.2".toList = true,\n'
    '      problem_spec_versionAtLeast "0.12.2".toList "1.2rc1".toList true\n'
    '        (some (versionGe "0.12.2".toList "1.2".toList h)) := by\n'
    "    intro h\n"
    "    simp only [problem_spec_versionAtLeast, red_above, dif_pos h, if_true]\n"
    '  have red_strict : normalizeVersion "0.12.0.dev".toList\n'
    '      = "0.12.0".toList := by rfl\n'
    '  have adm_strict : ∀ h : orderable "0.12.2".toList "0.12.0".toList = true,\n'
    '      problem_spec_versionAtLeast "0.12.2".toList "0.12.0.dev".toList false\n'
    '        (some (versionGt "0.12.2".toList "0.12.0".toList h)) := by\n'
    "    intro h\n"
    "    simp only [problem_spec_versionAtLeast, red_strict, dif_pos h,\n"
    "      Bool.false_eq_true, if_false]\n"
    '  have red_none : normalizeVersion "dev".toList = "dev".toList := by rfl\n'
    '  have adm_no_prefix : ∀ h : orderable "0.12.2".toList "dev".toList = false,\n'
    '      problem_spec_versionAtLeast "0.12.2".toList "dev".toList true\n'
    "        none := by\n"
    "    intro h\n"
    "    unfold problem_spec_versionAtLeast\n"
    "    split\n"
    "    next hc => simp only [red_none, h, Bool.false_eq_true] at hc\n"
    "    next => rfl\n"
    "  have red_inner_decimal : normalizeVersion ['1', Char.ofNat 0x0665, '5']\n"
    "      = ['1', Char.ofNat 0x0665, '5'] := by rfl\n"
    "  have adm_inner_decimal : ∀ h : orderable \"1\".toList\n"
    "      ['1', Char.ofNat 0x0665, '5'] = true,\n"
    "      problem_spec_versionAtLeast \"1\".toList\n"
    "        ['1', Char.ofNat 0x0665, '5'] true\n"
    "        (some (versionGe \"1\".toList ['1', Char.ofNat 0x0665, '5'] h)) := by\n"
    "    intro h\n"
    "    simp only [problem_spec_versionAtLeast, red_inner_decimal, dif_pos h,\n"
    "      if_true]\n"
    "  have red_leading_decimal : normalizeVersion [Char.ofNat 0x0665, '1']\n"
    "      = [Char.ofNat 0x0665, '1'] := by rfl\n"
    "  have adm_leading_decimal : ∀ h : orderable \"1\".toList\n"
    "      [Char.ofNat 0x0665, '1'] = true,\n"
    "      problem_spec_versionAtLeast \"1\".toList [Char.ofNat 0x0665, '1'] true\n"
    "        (some (versionGe \"1\".toList [Char.ofNat 0x0665, '1'] h)) := by\n"
    "    intro h\n"
    "    simp only [problem_spec_versionAtLeast, red_leading_decimal, dif_pos h,\n"
    "      if_true]\n"
    "  have red_numeric_not_decimal : normalizeVersion ['1', '²', '5']\n"
    "      = \"1\".toList := by rfl\n"
    "  have adm_numeric_not_decimal : ∀ h : orderable \"1\".toList \"1\".toList\n"
    "      = true,\n"
    "      problem_spec_versionAtLeast \"1\".toList ['1', '²', '5'] true\n"
    "        (some (versionGe \"1\".toList \"1\".toList h)) := by\n"
    "    intro h\n"
    "    simp only [problem_spec_versionAtLeast, red_numeric_not_decimal,\n"
    "      dif_pos h, if_true]\n"
    + _PROOF)


# ===========================================================================
# UNIQUENESS RIVALS — expect "reject".
#
# Each is a WRONG implementation sharing the frozen spec, and carries
#   (a) a `refinement` argument, MEASURED against the real comparison callee,
#       that its faithful real patch would NOT resolve the F2P — so a verifying
#       rival would be a true verify-does-not-imply-resolve break; and
#   (b) a `witness` seen to elaborate against the rival and to FAIL on the
#       frozen solution.
# ===========================================================================

# (R1) No reduction at all: the required string is compared as given. This is
# the un-patched behavior. Attacks C1.
_WEAK_UNREDUCED = _swap(
    _BASE, _IMPL,
    "  let ver := version\n"
    "  if h : orderable haveVersion ver = true then\n"
    "    if inclusive then\n"
    "      return some (versionGe haveVersion ver h)\n"
    "    else\n"
    "      return some (versionGt haveVersion ver h)\n"
    "  else\n"
    "    return none")

# `haveVersion` is "0.12", the reduced required value ITSELF, and that choice is
# load-bearing: a VALUE witness's hypotheses must be INHABITED under the real
# reading of the opaque callee, not merely unrefutable. At "0.12" both compared
# pairs are ones the ordering answers at and it answers DIFFERENTLY (measured:
# `False` against "0.12dev", `True` against "0.12"), so the assumed sub-domain is
# real. At an available version comfortably above the requirement the ordering
# has no answer for the raw string at all, and the claim would have been made at
# a point the behavior never reaches. `version` stays "0.12dev", so this remains
# the qualifier-bearing case it claims to be.
_W_UNREDUCED = (
    'example (h1 : orderable "0.12".toList "0.12dev".toList = true)\n'
    '    (h2 : orderable "0.12".toList "0.12".toList = true)\n'
    '    (h : versionGe "0.12".toList "0.12dev".toList h1\n'
    '          ≠ versionGe "0.12".toList "0.12".toList h2) :\n'
    '    ¬ problem_spec_versionAtLeast "0.12".toList "0.12dev".toList true\n'
    '        (implementation_versionAtLeast "0.12".toList "0.12dev".toList\n'
    "          true) := by\n"
    '  have hp : releasePrefix "0.12dev".toList = some "0.12".toList := by rfl\n'
    + _SIMP + "  exact fun hc => h (Option.some.inj hc)\n")

# (R2) NEAR MISS of R1: the reduction happens, but only on the strict branch —
# the non-strict branch compares the required string as given. Agrees with the
# spec on the whole strict half of the domain, so it needs its own witness at
# `inclusive = true`, where it diverges. Attacks C1 per-branch (and is the
# honest replacement for nagini's two dropped ordering rivals, whose refinement
# argument does not hold here — see the module docstring).
_WEAK_STRICT_ONLY = _swap(
    _BASE, _IMPL,
    "  let mut ver := version\n"
    "  if inclusive then\n"
    "    if h : orderable haveVersion ver = true then\n"
    "      return some (versionGe haveVersion ver h)\n"
    "    else\n"
    "      return none\n"
    "  else\n"
    "    if let some p := releasePrefix ver then\n"
    "      ver := p\n"
    "    if h : orderable haveVersion ver = true then\n"
    "      return some (versionGt haveVersion ver h)\n"
    "    else\n"
    "      return none")

# `haveVersion` is "1.14", the reduced required value itself, for the
# inhabitedness reason documented at `_W_UNREDUCED` (measured: "1.14" answers
# `False` against "1.14dev" and `True` against "1.14"; "1.14.3" has no answer
# against "1.14dev").
_W_STRICT_ONLY = (
    'example (h1 : orderable "1.14".toList "1.14dev".toList = true)\n'
    '    (h2 : orderable "1.14".toList "1.14".toList = true)\n'
    '    (h : versionGe "1.14".toList "1.14dev".toList h1\n'
    '          ≠ versionGe "1.14".toList "1.14".toList h2) :\n'
    '    ¬ problem_spec_versionAtLeast "1.14".toList "1.14dev".toList true\n'
    '        (implementation_versionAtLeast "1.14".toList "1.14dev".toList\n'
    "          true) := by\n"
    '  have hp : releasePrefix "1.14dev".toList = some "1.14".toList := by rfl\n'
    + _SIMP + "  exact fun hc => h (Option.some.inj hc)\n")

# (R3) The reduction is applied to the WRONG OPERAND: the available version is
# reduced and the required one passed through. Attacks C2. Refuted at an input
# where `haveVersion` itself carries a qualifier — the only place this rival is
# observable, and the reason that binder must not be held at a plain numeric
# string by every witness.
_WEAK_WRONG_SIDE = _swap(
    _BASE, _IMPL,
    "  let mut hv := haveVersion\n"
    "  if let some p := releasePrefix hv then\n"
    "    hv := p\n"
    "  if h : orderable hv version = true then\n"
    "    if inclusive then\n"
    "      return some (versionGe hv version h)\n"
    "    else\n"
    "      return some (versionGt hv version h)\n"
    "  else\n"
    "    return none")

# Measured: "0.12.1" is not strictly above "0.12.1" (`False`) while "0.12.1dev"
# is (`True`), and both pairs are ones the ordering answers at.
_W_WRONG_SIDE = (
    'example (h1 : orderable "0.12.1".toList "0.12.1".toList = true)\n'
    '    (h2 : orderable "0.12.1dev".toList "0.12.1".toList = true)\n'
    '    (h : versionGt "0.12.1".toList "0.12.1".toList h1\n'
    '          ≠ versionGt "0.12.1dev".toList "0.12.1".toList h2) :\n'
    '    ¬ problem_spec_versionAtLeast "0.12.1dev".toList "0.12.1".toList false\n'
    '        (implementation_versionAtLeast "0.12.1dev".toList "0.12.1".toList\n'
    "          false) := by\n"
    '  have hp : releasePrefix "0.12.1".toList = some "0.12.1".toList := by rfl\n'
    '  have hh : releasePrefix "0.12.1dev".toList = some "0.12.1".toList := by\n'
    "    rfl\n"
    "  simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "    normalizeVersion, hp, hh, Id.run, dif_pos h1, dif_pos h2,\n"
    "    Bool.false_eq_true, if_false]\n"
    "  exact fun hc => h (Option.some.inj hc)\n")

# (R4) OFF-BY-ONE reduction: the prefix is located correctly but one further
# character is kept, so non-numeric material survives into the compared value.
# Attacks C1 through the reduction's LENGTH rather than through skipping it.
# Ports nagini (R6) keep-marker.
_WEAK_OVERSHOOT = _swap(
    _BASE, _IMPL,
    "  let mut ver := version\n"
    "  if let some p := releasePrefix ver then\n"
    "    ver := version.take (p.length + 1)\n"
    "  if h : orderable haveVersion ver = true then\n"
    "    if inclusive then\n"
    "      return some (versionGe haveVersion ver h)\n"
    "    else\n"
    "      return some (versionGt haveVersion ver h)\n"
    "  else\n"
    "    return none")

# `haveVersion` is "1.2", NOT a version comfortably above the requirement, for
# the inhabitedness reason documented at `_W_UNREDUCED`: measured, "1.2" meets
# the reduced value ("1.2", `True`) and does not meet the overshot one ("1.2r",
# `False`), and the ordering answers at both pairs — whereas at "0.12.2" it
# answers the same way for both and the claim would have described an input
# point where this rival and the spec AGREE.
_W_OVERSHOOT = (
    'example (h1 : orderable "1.2".toList "1.2r".toList = true)\n'
    '    (h2 : orderable "1.2".toList "1.2".toList = true)\n'
    '    (h : versionGe "1.2".toList "1.2r".toList h1\n'
    '          ≠ versionGe "1.2".toList "1.2".toList h2) :\n'
    '    ¬ problem_spec_versionAtLeast "1.2".toList "1.2rc1".toList true\n'
    '        (implementation_versionAtLeast "1.2".toList "1.2rc1".toList\n'
    "          true) := by\n"
    '  have hp : releasePrefix "1.2rc1".toList = some "1.2".toList := by rfl\n'
    '  have ht : "1.2rc1".toList.take (("1.2".toList).length + 1)\n'
    '      = "1.2r".toList := by rfl\n'
    "  simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "    normalizeVersion, hp, ht, Id.run, dif_pos h1, dif_pos h2, if_true]\n"
    "  exact fun hc => h (Option.some.inj hc)\n")

# (R5) OPERANDS TRANSPOSED: the reduction is correct and applied to the right
# operand, but the comparison is asked in the wrong direction. Attacks C3 — a
# clause no other rival touches, and one the nagini model could not express
# separately (its helpers took the two sequences in a fixed order). Note the
# rival must also ask commensurability of the transposed pair: on this carrier
# an operand order cannot be swapped at the call site alone, which is itself a
# small piece of evidence that the carrier tracks what it claims to.
_WEAK_TRANSPOSED = _swap(
    _BASE, _IMPL,
    "  let mut ver := version\n"
    "  if let some p := releasePrefix ver then\n"
    "    ver := p\n"
    "  if h : orderable ver haveVersion = true then\n"
    "    if inclusive then\n"
    "      return some (versionGe ver haveVersion h)\n"
    "    else\n"
    "      return some (versionGt ver haveVersion h)\n"
    "  else\n"
    "    return none")

# Measured: "0.12" does not meet "0.12.2" (`False`) while "0.12.2" meets "0.12"
# (`True`), and the ordering answers at both pairs. Pinned at a QUALIFIER-FREE
# required version, where the reduction is the identity, so this isolates the
# order defect from every reduction defect above.
_W_TRANSPOSED = (
    'example (h1 : orderable "0.12".toList "0.12.2".toList = true)\n'
    '    (h2 : orderable "0.12.2".toList "0.12".toList = true)\n'
    '    (h : versionGe "0.12".toList "0.12.2".toList h1\n'
    '          ≠ versionGe "0.12.2".toList "0.12".toList h2) :\n'
    '    ¬ problem_spec_versionAtLeast "0.12.2".toList "0.12".toList true\n'
    '        (implementation_versionAtLeast "0.12.2".toList "0.12".toList\n'
    "          true) := by\n"
    '  have hp : releasePrefix "0.12".toList = some "0.12".toList := by rfl\n'
    + _SIMP + "  exact fun hc => h (Option.some.inj hc)\n")

# (R6) DEFINEDNESS LEAK: the reduction is performed and the returned VALUE is
# the specified one wherever this rival answers at all, but WHERE it answers is
# made to depend on the ordering at the un-reduced pair — it settles
# commensurability there first and treats "no" as "no verdict" rather than as an
# answer. Extensionally it agrees with the spec wherever the raw pair happens to
# be commensurable, and this is the shape no value-level clause over a TOTAL
# carrier could separate from the frozen implementation: over a total `Bool` the
# raw consultation would be a discarded pure subterm and the two implementations
# would be equal as functions. Attacks C5.
_WEAK_DEFINEDNESS = _swap(
    _BASE, _IMPL,
    "  let mut ver := version\n"
    "  if let some p := releasePrefix ver then\n"
    "    ver := p\n"
    "  if hraw : orderable haveVersion version = true then\n"
    "    if h : orderable haveVersion ver = true then\n"
    "      if inclusive then\n"
    "        return some (versionGe haveVersion ver h)\n"
    "      else\n"
    "        return some (versionGt haveVersion ver h)\n"
    "    else\n"
    "      return none\n"
    "  else\n"
    "    return none")

# Pinned at the F2P's own input point: available "0.12.2", required "0.12dev".
# Measured on the real callee: the raw pair is one the ordering has NO answer at
# (the release numbers run out and a residual qualifier would have to be ordered
# against a number) while the reduced pair "0.12.2" / "0.12" is one it answers.
# So this is a DEFINEDNESS witness whose two hypotheses are both observed facts
# rather than merely consistent assumptions, and it is the exact pair the issue
# report exhibits: the rival returns no verdict where the specified behavior
# returns one.
_W_DEFINEDNESS = (
    'example (h1 : orderable "0.12.2".toList "0.12dev".toList = false)\n'
    '    (h2 : orderable "0.12.2".toList "0.12".toList = true) :\n'
    '    ¬ problem_spec_versionAtLeast "0.12.2".toList "0.12dev".toList true\n'
    '        (implementation_versionAtLeast "0.12.2".toList "0.12dev".toList\n'
    "          true) := by\n"
    '  have hp : releasePrefix "0.12dev".toList = some "0.12".toList := by rfl\n'
    "  simp only [problem_spec_versionAtLeast, implementation_versionAtLeast,\n"
    "    normalizeVersion, hp, Id.run, h1, h2, Bool.false_eq_true, dif_neg,\n"
    "    dif_pos, if_true]\n"
    "  exact fun hc => Option.noConfusion hc\n")


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CLOSED_FORM,
        "rationale": (
            "the cheapest honest implementation: the specified closed form "
            "returned directly, with no mutable local and no `Id.run do` "
            "wrapper. The reduction is modeled deeply (a total `def` fully "
            "unfolded over `version`), so this expression is a function OF the "
            "binders rather than an opaque answer key — returning it IS the "
            "specified behavior, which is why it is a positive control and not "
            "a rival, and it shows the spec is not ungrounded-oracle-echo "
            "vulnerable on the reduction. Re-proved after unfolding, theorem "
            "statement byte-identical, nothing assumed. If this were rejected "
            "the spec would be over-fit to the frozen imperative form => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-option-getD",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_OPTION_GETD,
        "rationale": (
            "structurally different but correct: the reduction is read as a "
            "total default-taking projection of the optional prefix instead of "
            "a conditional rebinding of a mutable local. Same value at every "
            "input, so it MUST verify; it attacks the possibility that the spec "
            "is pinned to the frozen `if let ... then` shape rather than to the "
            "reduced VALUE (clause C1). If rejected => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-negated-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEGATED_FLAG,
        "rationale": (
            "second reshape, aimed at clause C4's conditional rather than at "
            "the reduction: the flag is tested negated and the two arms "
            "exchanged, so the strict comparison is reached through the `then` "
            "arm. Semantically identical, so it MUST verify — this is the "
            "control that distinguishes 'the spec pins WHICH ordering goes with "
            "which flag value' (true, and what the reject lane attacks) from "
            "'the spec pins the syntactic branch order' (which would be "
            "over-fitting). Closed by the frozen script unchanged; statement "
            "byte-identical. If rejected => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-guarded-raw-probe",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RAW_PROBE,
        "rationale": (
            "the mirror image of `weak-definedness-leak`, and the control that "
            "keeps clause C5 from over-reaching. This implementation DOES put "
            "the ordering to the un-reduced pair — but correctly: it settles "
            "whether that pair is one the ordering answers at, which is a total "
            "question, and discards the answer. Its value is the specified one "
            "at every input and its definedness is the specified one, so it "
            "MUST verify. C5 forbids a verdict whose EXISTENCE depends on the "
            "raw pair; it does not forbid asking a question that always "
            "completes, and a spec that forbade the latter would reject a "
            "correct alternative implementation => SPEC-TOO-STRONG. The `do` "
            "block puts the whole continuation inside both arms of the guard, "
            "so the reshape is real rather than syntactic, and the proof needs "
            "one extra `split`."),
    },
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "`correct_versionAtLeast` binds no precondition (the behavior is "
            "total), so there is no precondition to fail to re-establish; the "
            "honest analogue discharges the spec predicate at seven ground "
            "inputs the behavior is really exercised on — a qualifier-bearing "
            "required version, a required version above the available one, the "
            "strict branch, a required string with NO release-number prefix at "
            "all (where the reduction is the identity via its fallback and the "
            "ordering genuinely has no answer, so the instance lands in the "
            "spec's no-verdict branch), and the three decimal-digit boundary "
            "cases — then closes the frozen obligation verbatim. Each instance "
            "also pins the reduction's value at its input by `rfl`. Every "
            "instance is a `have` inside the tactic body and the theorem "
            "statement is byte-identical, so nothing is assumed. If an instance "
            "could not be discharged the behavior would be unsatisfiable at an "
            "input it must admit: the analogue of PRECOND-TOO-STRONG."),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "weak-compare-unreduced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_UNREDUCED,
        "witness": _W_UNREDUCED,
        "refinement": (
            "this is the un-patched behavior, and it is the instance's actual "
            "differential. Its faithful real patch performs the comparison on "
            "the required string as given, with no reduction. Measured against "
            "the real comparison callee: on the F2P's required version that "
            "carries a trailing development qualifier, comparing the "
            "un-reduced string does not yield a value at all — the callee "
            "raises, the assertion never evaluates, and the F2P test ERRORS. "
            "So the faithful patch does NOT resolve, and a verifying rival "
            "here would be a genuine verify-does-not-imply-resolve break."),
        "rationale": (
            "attacks clause C1 (WHICH VALUE is compared). Rejection source: "
            "the postcondition pins the result to the comparison against "
            "`normalizeVersion version`; this rival returns the comparison "
            "against `version`, and the two differ wherever the reduction is "
            "not the identity. The witness fixes such an input (a required "
            "version bearing a trailing qualifier), discharges the reduction "
            "there by `rfl`, and concludes from the hypothesis that the "
            "ordering answers differently at the two pairs — exactly the "
            "sub-domain where the rival is wrong. It is pinned at the available "
            "version that EQUALS the reduced required value, which is what "
            "makes those hypotheses inhabited rather than merely consistent. "
            "See `_W_UNREDUCED`. If it verified => SPEC-TOO-WEAK (the "
            "reduction would be unmodeled)."),
    },
    {
        "id": "weak-reduce-strict-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_STRICT_ONLY,
        "witness": _W_STRICT_ONLY,
        "refinement": (
            "NEAR MISS of weak-compare-unreduced: the faithful real patch "
            "reduces the required string only on the strict path and compares "
            "it as given on the non-strict one. Measured against the real "
            "callee: the F2P exercises only the non-strict path (it passes no "
            "explicit ordering flag), so the un-reduced comparison is exactly "
            "what runs, and on the required version carrying a development "
            "qualifier the callee raises and the F2P test ERRORS. Does NOT "
            "resolve."),
        "rationale": (
            "attacks clause C1 PER BRANCH: the spec feeds the SAME reduced "
            "value to both arms of C4's conditional, and this rival reduces in "
            "only one. Because it agrees with the spec across the whole strict "
            "half of the domain it is strictly closer to gold than "
            "weak-compare-unreduced, so it carries its own witness at a "
            "DIFFERENT input point — `inclusive = true`, where it diverges — "
            "rather than sharing that rival's; otherwise its rationale would "
            "claim a sub-domain the manifest never demonstrates. Pinned, like "
            "`weak-compare-unreduced`, at an available version the ordering "
            "really answers at for BOTH compared values, so the hypotheses are "
            "inhabited and not merely consistent. If it verified => "
            "SPEC-TOO-WEAK (the spec would permit reducing on only one "
            "branch)."),
        },
    {
        "id": "weak-reduce-wrong-side",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_WRONG_SIDE,
        "witness": _W_WRONG_SIDE,
        "refinement": (
            "faithful real patch: apply the reduction to the AVAILABLE version "
            "instead of the required one, leaving the required string as given. "
            "Measured against the real callee: the F2P's required version "
            "still carries its development qualifier when it reaches the "
            "comparison, the callee raises, and the F2P test ERRORS. Does NOT "
            "resolve — the reduction has to protect the operand that can carry "
            "a qualifier."),
        "rationale": (
            "attacks clause C2 (WHICH OPERAND is reduced). Rejection source: "
            "the postcondition reduces `version` and passes `haveVersion` "
            "through untouched. The witness is pinned to the only kind of "
            "input where this rival is observable at all — one whose "
            "`haveVersion` itself carries a qualifier, so that reducing it "
            "changes the compared value — and is the case that makes the "
            "`haveVersion` binder load-bearing. It is also the battery's only "
            "witness at `inclusive = false`, so neither arm of C4 is a branch "
            "no witness enters. If it verified => SPEC-TOO-WEAK (the spec "
            "would not pin which side is reduced)."),
    },
    {
        "id": "weak-prefix-overshoot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_OVERSHOOT,
        "witness": _W_OVERSHOOT,
        "refinement": (
            "faithful real patch: locate the leading release-number prefix "
            "correctly but keep one character too many, so non-numeric "
            "material survives into the compared value (the real-world shape "
            "is an off-by-one in the matched span). Measured against the real "
            "callee: on the F2P's qualifier-bearing required version the "
            "compared value still ends in a non-numeric character, the callee "
            "raises, and the F2P test ERRORS. Does NOT resolve."),
        "rationale": (
            "attacks clause C1 through the reduction's LENGTH rather than by "
            "skipping it: the spec pins the result to the comparison against "
            "the LONGEST leading release-number prefix, and any other prefix "
            "is a different value. Refuted at a required version whose "
            "qualifier begins immediately after the prefix, where the extra "
            "character is retained, and at an AVAILABLE version that the "
            "reduced required value clears while the overshot one does not — so "
            "the hypotheses describe an input point where this rival and the "
            "spec really do diverge, rather than one where the ordering happens "
            "to answer alike for both compared values. The reduction and the "
            "overshoot are both discharged by `rfl`, so only the comparison "
            "stays opaque. Ports the nagini keep-marker rival — same defended "
            "behavior (a reduction that leaves non-numeric material in the "
            "compared value), re-expressed for a carrier where the reduction is "
            "a string prefix rather than an accumulated segment list. If it "
            "verified => SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-operands-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_TRANSPOSED,
        "witness": _W_TRANSPOSED,
        "refinement": (
            "faithful real patch: reduce correctly, then ask the comparison in "
            "the wrong direction (required-versus-available instead of "
            "available-versus-required). Measured against the real callee: the "
            "verdict INVERTS on all six F2P inputs — every version the test "
            "requires to be accepted is reported unmet and every one it "
            "requires to be rejected is reported met — so the F2P test FAILS "
            "on its first assertion. It additionally inverts the package's "
            "import-time minimum-dependency guard, which would raise at import "
            "and break the P2P tests too. Does NOT resolve."),
        "rationale": (
            "attacks clause C3 (OPERAND ORDER), which no other rival in this "
            "battery touches and which nagini's battery did not carry a case "
            "for (its two comparison helpers are binary and symmetric in "
            "shape, so a transposing rival WAS expressible there and simply "
            "was not written — this case is an addition on this carrier, not a "
            "port). Rejection source: the postcondition names `haveVersion` as "
            "the left operand and the reduced required value as the right. "
            "Refuted at a QUALIFIER-FREE required version, where the reduction "
            "is the identity, so the witness isolates the order defect from "
            "every reduction defect above — and in doing so it exercises the "
            "reduction's no-op half, which the qualifier-bearing witnesses "
            "never reach. If it verified => SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-definedness-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_DEFINEDNESS,
        "witness": _W_DEFINEDNESS,
        "refinement": (
            "faithful real patch: perform the reduction and return the reduced "
            "comparison, but first find out whether the required string AS "
            "GIVEN is commensurable with the available version, and treat "
            "'not commensurable' as 'no verdict' — i.e. let the pre-reduction "
            "comparison's failure be the decision's failure. Measured against "
            "the real comparison callee: the F2P's required version carries a "
            "trailing development qualifier, so that pre-reduction comparison "
            "has no value, the decision has no verdict, and the F2P test never "
            "sees the correct reduced answer — it ERRORS. Does NOT resolve. "
            "This is the instance's actual failure mode: the issue report "
            "exhibits exactly this pair, so the rival is wrong for the same "
            "reason the un-patched code was, and its faithful patch fails the "
            "same test."),
        "rationale": (
            "attacks clause C5 (DEFINEDNESS), the degree of freedom no "
            "value-level clause over a TOTAL carrier can express. Over a total "
            "`Bool` this rival is EXTENSIONALLY EQUAL to the frozen "
            "implementation — the raw consultation is a pure subterm whose "
            "value is discarded, so `funext` proves the two functions equal and "
            "NO postcondition about the result could separate them. That is why "
            "the ordering is carried as an operation on its DOMAIN: the raw "
            "pair cannot be consulted without first settling its "
            "commensurability, and a decision that hangs on the outcome of that "
            "settling is a different behavior from one that does not. Rejection "
            "source: the spec's conditional is on the REDUCED pair, so the "
            "result carries a verdict exactly when the reduced comparison does; "
            "this rival additionally requires the raw pair to be one the "
            "ordering answers at. The witness is pinned at the F2P's own "
            "inputs, where (measured) the reduced pair is answered and the raw "
            "pair is not, so both hypotheses are observed facts about the real "
            "callee. Its mirror control `pos-guarded-raw-probe` must still "
            "verify, which is what keeps this clause from degenerating into a "
            "ban on touching the raw pair at all. If it verified => "
            "SPEC-TOO-WEAK (the spec would permit the un-patched behavior's "
            "failure mode to survive inside a correct-looking answer)."),
    },
]
