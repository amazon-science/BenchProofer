# properties.py — G-PBT spec-lane falsification battery for django__django-15382
# (velvet). NOT a Velvet module: a record of adversarial cases. The runner writes
# each case's `module` to a temp file, checks it against the frozen Solution.lean
# with variant_scope.variant_problems (same_spec + obligation preserved + nothing
# assumed), Lean-verifies it, and for every `expect="reject"` case additionally
# builds the `witness` twice — against the rival (must ELABORATE) and against the
# frozen solution (must FAIL) — so a rejection is attributable to the spec rather
# than to the frozen tactic script no longer matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE
# ---------------------------------------------------------------------------
# One obligation: `prove_correct renderExistsTest`, over
#
#     method renderExistsTest (complemented : Bool) (inner : Except Unit Frag)
#         return (out : Except Unit Frag)
#       ensures out = renderExists complemented inner
#
# There is no `require`, so every input point is live and no witness can be
# vacuously short-circuited by a failed precondition. The postcondition is a
# single equation, but `renderExists` is a two-way case split on both binders, so
# it carries four INDEPENDENT top-level arms — the clauses this battery attacks:
#
#   C1  inner = ok f, ¬complemented   -> out = ok f
#                                        (carry the fragment through untouched:
#                                         both its text AND its bound parameters)
#   C2  inner = ok f,  complemented   -> out = ok { f with sql := "NOT " ++ f.sql }
#                                        (complement the predicate by prefixing the
#                                         keyword; parameters unchanged)
#   C3  inner = error,  complemented  -> out = ok ⟨[], []⟩
#                                        (the empty/always-true fragment — the
#                                         behaviour the public issue demands)
#   C4  inner = error, ¬complemented  -> out = error ()
#                                        (the emptiness signal propagates)
#
# Both binders are varied by the reject witnesses below: `complemented` takes both
# values and `inner` takes both constructors, and the FOUR arms are attacked at the
# four corners of that 2x2 — C1 at (false, ok), C2 at (true, ok), C3 at (true,
# error), C4 at (false, error) — with several distinct `ok` payloads so the
# fragment text and the parameter list are separately discriminated. Eight rivals
# over SIX distinct input points — atk-params-on-empty shares (true, error) with
# the two other C3 rivals, since that is the only arm any of the three touches,
# and the three are refuted there for three different reasons (wrong constructor /
# wrong text / wrong parameter list). Counted mechanically: scripts/pbt_coverage.py
# reports `binders=2 pts=6-6`.
#
# AUDIT NOTE (this file was audited independently of its port; the two clause
# hollows the audit found and closed are recorded at the two `[ADDED BY AUDIT]`
# rivals below and in the footer). The port shipped six rivals over FIVE points
# and its header claimed six points with C4 "probed at false"; both claims were
# false. No rival differed from gold at (false, error) at all, so clause C4 was
# undefended, and no rival differed from gold in the `params` field of arm C3.
# MEASURED: a spec hollowed at either place — `ensures (inner = Except.error () ∧
# complemented = false) ∨ out = renderExists ...`, and the C3-params analogue —
# admits a wrong impl yet reproduces the ported battery's recorded outcomes
# EXACTLY (3 positives verify, all 6 shipped rivals still rejected, on both
# hollowed specs). So the recorded SOUND did not distinguish the frozen spec from
# one with a hole in it. The two rivals added below do distinguish them.
#
# ---------------------------------------------------------------------------
# WHAT PORTED FROM THE NAGINI SIBLING, AND WHAT DID NOT
# ---------------------------------------------------------------------------
# The nagini battery has 11 spec cases over a `render_exists(satisfiable, negated)
# -> List[int]` carrier whose clauses C1..C5/E1 correspond to the four arms above
# (nagini splits the emptiness signal across a postcondition reachability clause
# and an exceptional-postcondition clause; here both collapse into the single
# `Except.error ()` result value, since this carrier returns the signal rather
# than raising it). Ported: the two soundness positives, the admissibility
# positive, and five of the eight rivals. The dispositions of the rest are
# recorded in the footer — three were DROPPED on measured evidence that their
# faithful real patch RESOLVES, which makes their nagini refinement argument
# false on this instance's harness set.
#
# Every case edits ONLY the impl region (and, for two positives, the elided proof
# body), so `markers.same_spec` holds by construction.
from pathlib import Path

INSTANCE = "django__django-15382"
BACKEND = "velvet"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen-region anchors. Both lie ENTIRELY inside a region a variant may edit
# (the impl region including its markers; the `prove_correct` block), and both are
# unique in the file — so the manifest breaks loudly if the frozen solution ever
# changes.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- impl-start\n"
    "    -- Carry the produced fragment through (prefixing `NOT` to its text when the\n"
    "    -- test is complemented); on a provably-empty signal, propagate it for a plain\n"
    "    -- test but render a complemented test as the empty (always-true) fragment.\n"
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok (if complemented then { f with sql := \"NOT \".toList ++ f.sql } else f)\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], []⟩ else Except.error ()\n"
    "    return out\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "frozen impl region drifted from expected text"

_PROOF = "prove_correct renderExistsTest by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "frozen proof region drifted from expected text"

# The frozen impl body alone (markers stripped), for variants that only PREPEND to
# it — the admissibility case keeps gold's computation verbatim and adds an assert.
_GOLD_BODY = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok (if complemented then { f with sql := \"NOT \".toList ++ f.sql } else f)\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], []⟩ else Except.error ()\n"
    "    return out"
)
assert _BASE.count(_GOLD_BODY) == 1, "frozen impl body drifted from expected text"


def _impl(body, proof=None):
    """Full Solution.lean variant with the impl region replaced by `body` (markers
    re-emitted) and, optionally, the elided proof body retuned. Edits are confined
    to the impl region and the `prove_correct` tactic body, so same_spec holds and
    the `prove_correct renderExistsTest` header survives."""
    src = _swap(_BASE, _IMPL,
                "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end")
    if proof is not None:
        src = _swap(src, _PROOF, proof)
    return src


# ---------------------------------------------------------------------------
# Witness machinery. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the postcondition through Velvet's own tester machinery:
# `renderExistsTestTester c i = false` says the extracted program's result
# VIOLATES the method's postcondition at that concrete input. The result carrier
# `Except Unit Frag` has no `DecidableEq` in scope (the frozen `Frag` derives one,
# but the `Except` wrapper does not), so the witness brings its own — a `deriving
# instance` line, which is appended to BOTH the rival and the gold build, so it
# exists on both sides and references only spec-region names. Checked in a file
# whose `prove_correct` block has been stripped, so no tactic script can mask the
# witness's own verdict. Every argument is a concrete literal, so `decide` reduces
# the extracted straight-line program without getting stuck, and the witness head
# binds nothing — there are no hypotheses that could be inconsistent.
# ---------------------------------------------------------------------------
_WITNESS_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for renderExistsTest\n"
    "prove_precondition_decidable_for renderExistsTest\n"
    "prove_postcondition_decidable_for renderExistsTest\n"
    "derive_tester_for renderExistsTest\n"
)


def _witness(args):
    """A refutation firing at one concrete input point `args` (the two tester
    arguments: the `complemented` flag and the `inner` outcome)."""
    return (_WITNESS_PREAMBLE
            + f"\nexample : renderExistsTestTester {args} = false := by\n  decide\n")


# ===========================================================================
# POSITIVE CONTROLS — MUST verify (else SPEC-TOO-STRONG)
# ===========================================================================

# pos-flag-first (ports nagini pos-structdiff): structurally different, same
# value behaviour. Gold scrutinises the renderer outcome first and consults the
# flag inside each branch; this pivots the other way — the flag is the OUTER
# split and the outcome is matched separately under each arm. Both `match`
# scrutinees and both nestings differ from gold, so this is a genuine reshape and
# not a reindentation; the frozen `loom_solve` still closes it.
_POS_FLAG_FIRST = (
    "    let out : Except Unit Frag :=\n"
    "      if complemented then\n"
    "        (match inner with\n"
    "         | Except.ok f => Except.ok { f with sql := \"NOT \".toList ++ f.sql }\n"
    "         | Except.error _ => Except.ok ⟨[], []⟩)\n"
    "      else\n"
    "        (match inner with\n"
    "         | Except.ok f => Except.ok f\n"
    "         | Except.error _ => Except.error ())\n"
    "    return out"
)

# pos-let-prefix (ports nagini pos-reorder + its typed-local reshape): the two
# outcome arms are REORDERED (the emptiness signal is handled first), the
# complemented fragment is bound to a typed local before the choice, and that
# local is spelled with an explicit field-wise literal rather than record-update
# syntax. Same value behaviour on all four arms.
_POS_LET_PREFIX = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok { sql := [], params := [] }\n"
    "          else Except.error ()\n"
    "      | Except.ok f =>\n"
    "          let flipped : Frag := { sql := \"NOT \".toList ++ f.sql, params := f.params }\n"
    "          Except.ok (if complemented then flipped else f)\n"
    "    return out"
)

# admiss-f2p (ports nagini admiss-f2p): the input the public issue reports — a
# COMPLEMENTED test over a provably-empty underlying set — is admitted, and on it
# the operation yields a fragment (not the emptiness signal). Asserted IN-REGION
# alongside the plain-test and complemented-fragment arms, so a precondition that
# excluded any of them, or a spec that did not pin the empty fragment there, would
# make this fail. Gold's computation is kept verbatim; only the assert is added.
#
# The assert is phrased through `Except.toOption` deliberately: stated directly as
# an `Except`-equation it needs a `Decidable` instance for that carrier, which the
# frozen spec view does not provide and which a variant may not add at top level
# (that would be a new declaration — MALFORMED-TESTS). Mapping the outcome into
# `Option Frag` reuses `Frag`'s own frozen `DecidableEq`, so `decide` closes it
# with no new declarations. `none` on the second conjunct is exactly the
# emptiness-signal outcome, so the plain-test arm is still pinned.
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss\n"
    "      ((renderExists true (Except.error ())).toOption = some ⟨[], []⟩ ∧\n"
    "       (renderExists false (Except.error ())).toOption = none ∧\n"
    "       (renderExists true (Except.ok ⟨\"a\".toList, [(7 : Int)]⟩)).toOption\n"
    "         = some ⟨\"NOT a\".toList, [(7 : Int)]⟩))\n"
) + _GOLD_BODY
_ADMISS_PROOF = "prove_correct renderExistsTest by\n  loom_solve\n  all_goals decide"


# ===========================================================================
# UNIQUENESS RIVALS — MUST reject (else SPEC-TOO-WEAK)
# ===========================================================================

# atk-propagate-complemented (ports nagini atk-raise-unsatneg): THE pre-fix
# behaviour. The emptiness signal is propagated unconditionally, so a complemented
# test over a provably-empty underlying set yields the signal instead of the
# empty/always-true fragment. Attacks C3 — the wrong RESULT CONSTRUCTOR.
_ATK_PROPAGATE = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok (if complemented then { f with sql := \"NOT \".toList ++ f.sql } else f)\n"
    "      | Except.error _ => Except.error ()\n"
    "    return out"
)

# atk-junk-fragment (ports nagini atk-junk-unsatneg, and subsumes its
# atk-false-pred / atk-space-unsatneg near-misses — see the footer): correct on
# three arms, but on the complemented-empty arm it emits a NON-EMPTY predicate
# text instead of the empty fragment. Attacks C3 — right constructor, wrong text.
_ATK_JUNK = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok (if complemented then { f with sql := \"NOT \".toList ++ f.sql } else f)\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨\"XYZ\".toList, []⟩ else Except.error ()\n"
    "    return out"
)

# atk-noprefix (ports nagini atk-noprefix): drops the complementing keyword, so a
# complemented test over a produced fragment renders as the bare fragment — the
# predicate is not complemented at all. Attacks C2.
_ATK_NOPREFIX = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f => Except.ok f\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], []⟩ else Except.error ()\n"
    "    return out"
)

# atk-prefix-always (ports nagini atk-prefix-always): complements the predicate
# even for a PLAIN test. Attacks C1 (the fragment must come through untouched).
_ATK_PREFIX_ALWAYS = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f => Except.ok { f with sql := \"NOT \".toList ++ f.sql }\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], []⟩ else Except.error ()\n"
    "    return out"
)

# atk-fabricate-echo (ports nagini atk-fabricate-echo): the UNGROUNDED-ORACLE
# test. On the produced-fragment arms it ignores the text the underlying renderer
# actually produced and substitutes a fabricated literal, keeping the parameters
# (so the fabrication is not detectable from the parameter list alone). Attacks
# C1/C2 on their TEXT component: the postcondition equates the result to the
# renderer's own output, so a different fabricated text cannot satisfy it.
_ATK_ECHO = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok ⟨(if complemented then \"NOT \".toList else []) ++ \"X\".toList,\n"
    "                    f.params⟩\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], []⟩ else Except.error ()\n"
    "    return out"
)

# atk-drop-params (no nagini counterpart — nagini's carrier is a single flat
# code-point sequence with no separate parameter channel, so this rival is not
# expressible there; it is NEW work for this carrier). The predicate TEXT is
# exactly gold's on every arm, but the produced fragment's ordered bound
# parameters are discarded. Attacks the parameter component of C1/C2, which the
# text-only rivals above leave entirely undefended.
_ATK_DROP_PARAMS = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok ⟨(if complemented then \"NOT \".toList ++ f.sql else f.sql), []⟩\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], []⟩ else Except.error ()\n"
    "    return out"
)


# atk-swallow-signal [ADDED BY AUDIT] (ports nagini atk-neverraise, which the port
# had DROPPED). The emptiness signal is swallowed UNCONDITIONALLY: a PLAIN test over
# a provably-empty underlying set yields the empty (always-true) fragment instead of
# propagating the signal. Attacks C4 — the one arm no other rival in this battery
# differs from gold on, so without this case the battery cannot tell the frozen spec
# apart from one that leaves (¬complemented, error) unconstrained.
_ATK_SWALLOW = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok (if complemented then { f with sql := \"NOT \".toList ++ f.sql } else f)\n"
    "      | Except.error _ => Except.ok ⟨[], []⟩\n"
    "    return out"
)

# atk-params-on-empty [ADDED BY AUDIT] (no nagini counterpart — nagini's carrier has
# no separate parameter channel). Correct on three arms and correct in the TEXT
# component of the fourth: on the complemented-empty arm it emits the required empty
# text but attaches a spurious bound parameter. Attacks the `params` component of C3,
# which no other rival touches — atk-drop-params attacks `params` only on C1/C2, and
# every C3 rival differs from gold in `sql`.
_ATK_PARAMS_ON_EMPTY = (
    "    let out : Except Unit Frag :=\n"
    "      match inner with\n"
    "      | Except.ok f =>\n"
    "          Except.ok (if complemented then { f with sql := \"NOT \".toList ++ f.sql } else f)\n"
    "      | Except.error _ =>\n"
    "          if complemented then Except.ok ⟨[], [(0 : Int)]⟩ else Except.error ()\n"
    "    return out"
)


SPEC_TESTS = [
    # ------------------------------------------------------------------ positives
    {
        "id": "pos-flag-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_FLAG_FIRST),
        "rationale": (
            "structurally-different CORRECT impl: the case split is pivoted so the "
            "complementation flag is the OUTER branch and the renderer outcome is "
            "matched separately beneath each arm (gold splits on the outcome first). "
            "Both `match` scrutinees and the nesting order differ from gold, yet all "
            "four postcondition arms C1-C4 hold pointwise, so the single `ensures "
            "out = renderExists complemented inner` must still discharge. If this "
            "REJECTED, the obligation would be pinned to gold's syntactic shape "
            "rather than to its behaviour => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-let-prefix",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LET_PREFIX),
        "rationale": (
            "second CORRECT reshape, independent of pos-flag-first: the two renderer-"
            "outcome arms are REORDERED (emptiness signal handled first), the "
            "complemented fragment is bound to a typed local before the choice, and "
            "both fragment literals are spelled field-wise instead of with record-"
            "update syntax. Value behaviour is identical on all four arms, so C1-C4 "
            "still hold and the obligation must discharge. Guards the same "
            "SPEC-TOO-STRONG failure from a different direction (arm order + local "
            "binding, vs. split pivot)."),
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_ASSERT, proof=_ADMISS_PROOF),
        "rationale": (
            "the operation ADMITS the input the public issue reports — a complemented "
            "test over a provably-empty underlying set — and on it yields a fragment "
            "rather than the emptiness signal. Asserted in-region over three points at "
            "once: the complemented-empty arm produces the EMPTY fragment (C3), the "
            "plain-empty arm produces the signal (C4, spelled as `toOption = none`), "
            "and the complemented-fragment arm prefixes the keyword while carrying the "
            "parameters through (C2). There is no `require`, so nothing narrows the "
            "domain; if this failed, the precondition or the empty-fragment pin would "
            "be wrong => PRECOND-TOO-STRONG. Gold's computation is kept verbatim — "
            "only the assert is added — so the case cannot pass by reshaping the impl."),
    },
    # ------------------------------------------------------------------- rivals
    {
        "id": "atk-propagate-complemented",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_PROPAGATE),
        "refinement": (
            "this IS the pre-fix behaviour, and the instance exists because it does "
            "not resolve. Its faithful real patch propagates the emptiness signal for "
            "a COMPLEMENTED existence test too, which discards the entire filter "
            "predicate — exactly the defect the public issue reports ('the WHERE block "
            "is missing completely'). MEASURED at base_commit against the official "
            "155-id harness set: the unpatched tree fails exactly and only the F2P "
            "`test_negated_empty_exists`, whose `assertSequenceEqual(qs, [manager])` "
            "gets an empty result set. So a rival verifying here would be a true "
            "verify-does-not-imply-resolve break."),
        "rationale": (
            "REJECTS on arm C3 (`inner = error`, `complemented = true` -> "
            "`out = ok ⟨[], []⟩`): the rival returns the `Except.error` CONSTRUCTOR "
            "where the clause demands `Except.ok` of the empty fragment. Refuted at "
            "(complemented = true, inner = error ()) — the only point at which this "
            "rival differs from gold, and the point the public issue names. Witness "
            "SEEN to discriminate: elaborates against the rival, fails on gold."),
        "witness": _witness("true (Except.error ())"),
    },
    {
        "id": "atk-junk-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_JUNK),
        "refinement": (
            "faithful real patch emits a NON-EMPTY predicate text on the complemented-"
            "empty case. A non-empty fragment is spliced into the enclosing "
            "conjunctive filter (the surrounding combinator appends any fragment whose "
            "text is non-empty), so the emitted predicate references a name the "
            "database does not know. MEASURED against the 155-id harness set: NOT "
            "RESOLVED — the F2P `test_negated_empty_exists` ERRORS with `no such "
            "column: XYZ` at its `assertSequenceEqual(qs, [manager])`. Distinct from "
            "atk-propagate-complemented: that rival drops the predicate, this one "
            "emits an invalid predicate; both fail the same F2P for different reasons."),
        "rationale": (
            "REJECTS on arm C3, on its TEXT component rather than its constructor: the "
            "rival returns `Except.ok` as required but with a non-empty `sql`, while "
            "the clause pins `⟨[], []⟩` exactly. Shares the input point (true, error) "
            "with atk-propagate-complemented because that is the sole arm either rival "
            "touches — but the two are refuted for DIFFERENT reasons (wrong "
            "constructor vs. wrong text under the right constructor), so neither "
            "witness stands in for the other. This case also covers the nagini "
            "atk-false-pred and atk-space-unsatneg near-misses, which differ only in "
            "WHICH non-empty text is emitted (see footer). Witness SEEN to "
            "discriminate."),
        "witness": _witness("true (Except.error ())"),
    },
    {
        "id": "atk-noprefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_NOPREFIX),
        "refinement": (
            "faithful real patch never complements the predicate, so a complemented "
            "existence test renders as the bare (un-complemented) one and matches the "
            "COMPLEMENT of the intended rows. MEASURED against the 155-id harness set: "
            "NOT RESOLVED — two P2P failures. "
            "`test_exists_in_filter (expressions.tests.BasicExpressionsTests)`: "
            "`AssertionError: Element counts were not equal: First has 1, Second has "
            "0`. `test_subquery (expressions.tests.BasicExpressionsTests)`: the "
            "annotated complemented flag comes back `False` where `True` is asserted. "
            "Note this rival leaves the F2P PASSING and is caught only by the P2P set, "
            "which is why it is worth carrying separately."),
        "rationale": (
            "REJECTS on arm C2 (`inner = ok f`, `complemented = true` -> "
            "`out = ok { f with sql := \"NOT \" ++ f.sql }`): the rival returns `ok f` "
            "with the text unprefixed. Refuted at (complemented = true, inner = ok "
            "⟨\"b\", [3]⟩) — a produced-fragment point, so it varies `inner` to the "
            "OTHER constructor from the two C3 rivals above, and carries a non-empty "
            "parameter list so the arm is probed with both fields populated. Witness "
            "SEEN to discriminate."),
        "witness": _witness("true (Except.ok ⟨\"b\".toList, [(3 : Int)]⟩)"),
    },
    {
        "id": "atk-prefix-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_PREFIX_ALWAYS),
        "refinement": (
            "faithful real patch complements the predicate even for a PLAIN existence "
            "test, inverting every non-complemented use. MEASURED against the 155-id "
            "harness set: NOT RESOLVED — six P2P failures, including "
            "`test_exists_in_filter` (`AssertionError: True is not false`), "
            "`test_order_by_exists` (ordering inverted: the sequence comes back "
            "reversed against `assertSequenceEqual(mustermanns_by_seniority, [max, "
            "mary])`), `test_subquery`, `test_boolean_expression_combined`, "
            "`test_boolean_expression_combined_with_empty_Q` (all eight subTests) and "
            "`test_boolean_expression_in_Q`."),
        "rationale": (
            "REJECTS on arm C1 (`inner = ok f`, `complemented = false` -> `out = ok f`, "
            "the fragment carried through UNTOUCHED): the rival prefixes the keyword "
            "regardless of the flag. Refuted at (complemented = FALSE, inner = ok "
            "⟨\"a\", []⟩) — the first witness to hold `complemented` at false, which is "
            "what stops that binder from being one every rival probes at the same "
            "value. Witness SEEN to discriminate."),
        "witness": _witness("false (Except.ok ⟨\"a\".toList, []⟩)"),
    },
    {
        "id": "atk-fabricate-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_ECHO),
        "refinement": (
            "faithful real patch emits a fabricated predicate text in place of the one "
            "the underlying renderer produced, keeping the bound parameters. MEASURED "
            "against the 155-id harness set: NOT RESOLVED — 9 distinct P2P tests error "
            "with `no such column: X`, including `test_exists_in_filter`, "
            "`test_subquery`, `test_nested_subquery`, `test_order_by_exists`, "
            "`test_boolean_expression_combined_with_empty_Q` (all 8 subTests), "
            "`test_boolean_expression_in_Q`, `test_case_in_filter_if_boolean_output_"
            "field` and `test_optimizations` — the last being notable because it "
            "inspects the GENERATED SQL rather than query results. The F2P PASSES here "
            "(the complemented-empty arm is untouched), so this rival is caught purely "
            "by the P2P set: it is the mirror of atk-junk-fragment, which fabricates "
            "only on the rare complemented-empty arm and is caught only by the F2P, "
            "whereas this one fabricates on the common produced-fragment arm."),
        "rationale": (
            "REJECTS on arms C1/C2 via the UNGROUNDED-ORACLE route: the postcondition "
            "equates the result to the renderer's OWN output, so an impl that ignores "
            "the produced text and substitutes a literal cannot satisfy it, however "
            "plausible the substitute looks. This is the case that certifies the "
            "content pin is grounded in the input carrier rather than echoable. "
            "Refuted at (complemented = true, inner = ok ⟨\"xy\", [1, 2]⟩) — a "
            "two-character text with a two-element parameter list, distinct from every "
            "other probe point, so the fabrication is caught on a payload no other "
            "witness visits. Witness SEEN to discriminate."),
        "witness": _witness("true (Except.ok ⟨\"xy\".toList, [(1 : Int), (2 : Int)]⟩)"),
    },
    {
        "id": "atk-drop-params",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_DROP_PARAMS),
        "refinement": (
            "faithful real patch emits the correct predicate TEXT but discards the "
            "produced fragment's ordered bound parameters, so the text's placeholders "
            "outnumber the supplied values. MEASURED against the 155-id harness set: "
            "NOT RESOLVED — P2P `test_subquery (expressions.tests."
            "BasicExpressionsTests)` ERRORS with `Incorrect number of bindings "
            "supplied. The current statement uses 2, and there are 0 supplied.` "
            "Strongly caught: a broader sweep produced 30 errors across four further "
            "test modules on every subquery-bearing path."),
        "rationale": (
            "REJECTS on the PARAMETER component of arms C1/C2, which every other rival "
            "in this battery leaves undefended — they all differ from gold in the `sql` "
            "field only, so without this case a rival that mishandled `params` alone "
            "would verify and the battery would never notice. NEW work for this "
            "carrier: nagini models the fragment as one flat code-point sequence with "
            "no separate parameter channel, so this rival is not expressible there. "
            "Refuted at (complemented = false, inner = ok ⟨\"z\", [7]⟩) — the second "
            "point holding `complemented` at false, and a distinct payload from "
            "atk-prefix-always's empty parameter list, so the parameter field is "
            "discriminated both when populated and when empty. Witness SEEN to "
            "discriminate."),
        "witness": _witness("false (Except.ok ⟨\"z\".toList, [(7 : Int)]⟩)"),
    },
    {
        "id": "atk-swallow-signal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_SWALLOW),
        "refinement": (
            "faithful real patch swallows the emptiness signal for a PLAIN "
            "existence test as well, so an existence test over a provably-empty "
            "underlying set contributes the always-true fragment where it must "
            "contribute nothing at all — it would then match every row instead of "
            "none, the OPPOSITE of the intended predicate on that input. This is a "
            "real behavioural divergence from the frozen operation, but the "
            "divergence is NOT observed by this instance's 155-id harness subset: "
            "the port measured the variant passing all 155 ids, with the "
            "non-complemented emptiness path reached zero times across that subset "
            "(the nearest test that would catch it lives in a module this instance "
            "does not run). Recorded as INHERITED from the port and NOT re-measured "
            "by this audit. So the direction here is spec-stronger-than-harness — "
            "the safe direction, and not a verify-does-not-imply-resolve break. "
            "That is a reason to keep the case, not to drop it: the reject lane's "
            "job is to certify the spec PINS the clause, and the clause is pinned."),
        "rationale": (
            "REJECTS on arm C4 (`inner = error`, `complemented = false` -> "
            "`out = error ()`): the rival returns `Except.ok` of the empty fragment "
            "where the clause demands the emptiness signal be propagated. Refuted "
            "at (complemented = false, inner = error ()) — THE corner of the 2x2 no "
            "other rival in this battery reaches, and the reason this case exists. "
            "MEASURED without it: a spec hollowed exactly at this point — `ensures "
            "(inner = Except.error () ∧ complemented = false) ∨ out = renderExists "
            "complemented inner` — verifies the C4-wrong impl above (exit 0) while "
            "still verifying all three positives and still rejecting all six other "
            "rivals, i.e. it reproduces the ported battery's recorded outcomes "
            "exactly. This case is what separates the two specs. Witness rebuilt by "
            "the audit: elaborates against the rival (exit 0), and on the frozen "
            "solution `decide` PROVES the proposition false (exit 1) — a semantic "
            "refutation, not a stuck reduction or an unknown name."),
        "witness": _witness("false (Except.error ())"),
    },
    {
        "id": "atk-params-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ATK_PARAMS_ON_EMPTY),
        "refinement": (
            "faithful real patch emits the correct empty predicate TEXT on the "
            "complemented-empty arm but attaches a bound parameter to it, so the "
            "emitted fragment carries a value its text has no placeholder for. The "
            "port DROPPED this rival claiming the surrounding combinator extends its "
            "parameter list only inside a branch guarded by non-empty text, making "
            "the difference unobservable end-to-end. That claim is INHERITED and NOT "
            "re-measured by this audit, and it is a claim about the enclosing "
            "combinator rather than about this operation: at this operation's own "
            "boundary — which is what the frozen postcondition is stated over — the "
            "rival returns a value the spec's arm C3 forbids. So this too is the "
            "spec-stronger-than-harness direction, which is the safe one."),
        "rationale": (
            "REJECTS on the PARAMETER component of arm C3, where the clause pins "
            "`⟨[], []⟩` — BOTH fields empty — and the rival satisfies only the text "
            "half. No other rival in this battery differs from gold in `params` on "
            "the emptiness arm: atk-drop-params attacks `params` on C1/C2 only, and "
            "every other C3 rival differs in `sql`. MEASURED without it: a spec that "
            "pins the C3 text but leaves its parameter list free (`∃ p, ... ∧ out = "
            "Except.ok ⟨[], p⟩ ∨ ...`) admits this rival while reproducing the "
            "ported battery's recorded outcomes exactly. Refuted at (complemented = "
            "true, inner = error ()); the input point is shared with the two other "
            "C3 rivals because it is the sole arm any of them touches, but the "
            "refutation is for a third distinct reason (right constructor, right "
            "text, wrong parameter list). Witness rebuilt by the audit: rival exit "
            "0, frozen solution exit 1 with `decide` proving the proposition false."),
        "witness": _witness("true (Except.error ())"),
    },
]


AXIOM_TESTS = []  # the axiom lane is G-AX's job; this bundle has no axioms anyway


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING: every omission, with its reason
# ===========================================================================
# PORTED (9 of 11 nagini spec cases, two merged, plus 2 cases with no nagini
# counterpart):
#   pos-structdiff      -> pos-flag-first
#   pos-reorder         -> pos-let-prefix
#   admiss-f2p          -> admiss-f2p
#   atk-raise-unsatneg  -> atk-propagate-complemented
#   atk-junk-unsatneg   -> atk-junk-fragment  (also subsumes atk-false-pred and
#                          atk-space-unsatneg, below)
#   atk-noprefix        -> atk-noprefix
#   atk-prefix-always   -> atk-prefix-always
#   atk-fabricate-echo  -> atk-fabricate-echo
#   atk-neverraise      -> atk-swallow-signal   [RESTORED BY AUDIT: the only rival
#                          defending clause C4]
#   (none)              -> atk-drop-params   [NEW: this carrier splits the fragment
#                          into text + ordered parameters, so the parameter channel
#                          is attackable here and is not in nagini]
#   (none)              -> atk-params-on-empty  [RESTORED BY AUDIT: the only rival
#                          defending the `params` component of clause C3]
#
# MERGED (2 nagini cases -> atk-junk-fragment):
#   atk-false-pred (emits an always-false predicate text) and atk-space-unsatneg
#   (emits a single-space text) differ from atk-junk-fragment ONLY in which
#   non-empty text is emitted on the complemented-empty arm. On this carrier all
#   three are refuted at the identical input point (true, error ()) for the
#   identical spec reason — `out = ok ⟨[], []⟩` pins the text to EMPTY, so any
#   non-empty text fails the same way, and no one of the three agrees with gold
#   over more of the domain than the others. Shipping all three would add two
#   witnesses at an input the battery already probes while claiming no sub-domain
#   the manifest does not already demonstrate. Recorded as merged, not dropped:
#   the clause they attack IS attacked.
#
# PORT-DROPPED — 3 rivals the port removed because their faithful real patch
# RESOLVES on this instance's harness subset, making the nagini refinement claim
# ("does NOT resolve") false as written. The audit AGREES the refinement claims
# were false and DISAGREES with the disposition for two of the three: a rival
# whose divergence the harness cannot observe still certifies that the spec pins
# the clause, and the fix is to correct the refinement prose, not to delete the
# only rival defending an arm. Two are restored below with corrected refinements;
# the third stays dropped, because it is not wrong on this carrier at all.
#
#   atk-neverraise (nagini) -> RESTORED BY AUDIT as atk-swallow-signal. The port
#     dropped it on the reasoning below, which the audit judges to be the WRONG
#     disposition for a correct measurement. The measurement (inherited, not
#     re-run here): the rival swallows the emptiness signal UNCONDITIONALLY,
#     returning the empty fragment even for a PLAIN existence test; it passes all
#     155 harness ids, and instrumenting the emptiness-signal handler shows the
#     non-complemented signal path is reached ZERO times across that subset (the
#     only hit is the complemented one, from the F2P; the nearest test that WOULD
#     catch it lives in a module this instance does not run). The port concluded
#     that this makes the case unshippable. It does not. "The harness cannot
#     observe this clause" is the SPEC-STRONGER-THAN-HARNESS direction, which is
#     safe; a reject case's job is to certify the spec PINS the clause, and the
#     refinement text now says exactly that rather than claiming a resolve break.
#     Dropping it left clause C4 with no rival at all, and MEASURED, that is not
#     cosmetic: a spec hollowed at (¬complemented, error) admits a wrong impl and
#     still reproduces every one of the port's recorded case outcomes.
#
#   atk-params-on-empty (C3 parameter component) -> RESTORED BY AUDIT under the
#     same id. The port's stated reason — the enclosing combinator extends its
#     parameter list only inside the branch guarded by a non-empty fragment text,
#     so parameters accompanying an empty text never reach the database — is a
#     claim about the ENCLOSING combinator, not about the operation under spec.
#     Inherited, not re-measured here. Same disposition error as above: the
#     frozen postcondition is stated at THIS operation's boundary, where the rival
#     returns a value arm C3 forbids, and the audit measured that a spec pinning
#     C3's text while leaving its parameter list free admits the rival and
#     reproduces the port's recorded outcomes exactly. Spec-stronger-than-
#     observable is a note for the faithfulness lane AND a shippable G-PBT rival;
#     it is not a reason to leave a clause component undefended.
#
#   atk-noprefix-empty-inner (a C2 near-miss) -> STAYS DROPPED, reason narrowed by
#     the audit. Applies the complementing keyword only when the produced text is
#     non-empty. The port's evidence: MEASURED RESOLVED, and unreachable BY
#     CONSTRUCTION, since the underlying renderer's output comes from a fixed
#     template that always contributes several literal characters, so the produced
#     text is never empty on that arm and the extra guard is a no-op (zero
#     empty-text outcomes across 160 produced-fragment calls). Inherited, not
#     re-measured. The audit BUILT this rival anyway to check the tooling claim:
#     it is scope-clean, the frozen spec REJECTS it (exit 1), and a witness at
#     (true, ok ⟨[], [5]⟩) discriminates (rival exit 0, gold exit 1). So it is
#     shippable, and it is dropped on a stronger ground than the two above rather
#     than on the same one: unlike them, its divergence from gold occurs ONLY at
#     an input the modeled renderer cannot produce, so the case would attack the
#     spec at a point outside the carrier's reachable domain and certify nothing
#     about the reachable behaviour. Clause C2 is already defended at reachable
#     points by atk-noprefix and atk-fabricate-echo.
#
# NOT APPLICABLE — classes with no counterpart on this backend:
#
#   * FRAME / PERMISSION-MUTATION rivals — VACUOUS here. These depend on nagini's
#     fractional-permission model (a callee mutating a structure the caller still
#     holds a read fraction of). Lean and Velvet are referentially transparent:
#     `Frag` and `Except Unit Frag` are immutable values, `renderExistsTest`
#     declares no `mut` binder, and there is no heap for a rival to disturb. The
#     class collapses, so no substitute is fabricated.
#
#   * DIVERGENCE / NON-TERMINATION - no nagini case to port, and the class is
#     CLOSED BY THE SEMANTICS rather than a spec hole. The nagini sibling carries NO
#     `diverge-*` / `nonterm-*` / `weak-diverge` case (its impl is straight-line and
#     always returns or raises), so there is nothing to carry over. The reason
#     matters, and the earlier version of this note had it exactly inverted: it
#     said that under this bundle's `set_option loom.semantics.termination "total"`
#     (Solution.lean line 4) a non-terminating impl satisfies every `ensures` clause
#     VACUOUSLY and VERIFIES, and called that a KNOWN SPEC HOLE. That is the
#     description of `partial` semantics, and it is false here. Under "total" a
#     postcondition is claimed of ALL runs, not only terminating ones, and the
#     verifier demands a decreasing measure on every loop. The option cannot drift
#     from the file's `open TotalCorrectness DemonicChoice` either, because the
#     `set_option` elaborator itself runs `openScope `TotalCorrectness`
#     (Loom/MonadAlgebras/WP/Options.lean:169-186).
#     Measured on this bundle, proof reduced to a bare `loom_solve`: an unmeasured
#     spun loop is refused at elaboration (`Decreasing annotations are required in
#     total correctness semantics`), and the sharper shape that CARRIES a measure
#     which does not decrease (`while q > 0 / invariant 0 <= q / done_with q = 0 /
#     decreasing q`, body `q := q`) is REJECTED on the measure's own goal --
#     `case «decreasing_1: q»`, residual `q < q`. So a diverging rival does NOT
#     satisfy this spec; there is no hole to record and none is inherited. The
#     401-vs-99 corpus census the earlier note cited is withdrawn as well: all 500
#     velvet bundles now set "total".
#     No reject case is written all the same, and the reason is the WITNESS
#     CONTRACT: a witness must ELABORATE against its rival, and each diverging
#     shape defeats that half by a different route. With NO measure the refusal is a
#     module-level error at the `method` DECLARATION, which the witness file retains
#     (only `prove_correct` is stripped), so the rival does not compile and even a
#     trivial witness returns `witness-unproven`. With a measure PRESENT BUT FALSE
#     the refusal moves to the `prove_correct` site, which IS stripped, so the
#     module elaborates; a real witness still fails, because the rival keeps a
#     `while` whose post-image is an unreduced `forIn Lean.Loop.mk ...
#     invariantGadget ... decreasingGadget` term the kernel will not normalise. Both
#     return `witness-unproven` -> INCONCLUSIVE instead of a rejection, and a
#     `witness_reference` rescues neither, since it substitutes the GOLD subject.
#
#   * AXIOM_TESTS (ax-sound-render-inner, ax-contain-render-inner) — dropped by
#     instruction: the axiom lane is G-AX's job and this gate ignores them. They
#     are moot here regardless — this bundle consumes no axiom (the underlying
#     renderer is modeled as a FREE input ranging over every outcome, which is
#     strictly weaker than any contract on it), and meta.json records G-AX = skip.
