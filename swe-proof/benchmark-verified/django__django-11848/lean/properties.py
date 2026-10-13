# properties.py — G-PBT falsification battery for django__django-11848 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   expandYear : (year currentYear : Int) → Int, obligation `correct_expandYear`
#   under precondition `0 ≤ year`. A parsed calendar year field is expanded to a
#   full year, interpreted relative to the current year `currentYear`. The whole
#   computation is exact integer arithmetic (`+`, `-`, `%`, comparison); there is NO
#   opaque callee and NO answer-key oracle — the postcondition pins the value with
#   arithmetic relations on the two Int inputs, so every witness computes by `decide`
#   at a concrete literal input (no conditioning on an opaque carrier needed).
#
# The postcondition is a conjunction of INDEPENDENT clauses over the two input
# binders (`year`, `currentYear`), each attackable one at a time. With
# `cc := currentYear - currentYear % 100`:
#   (1) year ≥ 100 → result = year                          [verbatim-passthrough]
#   (2) result % 100 = year                                 [last-two-digits kept]
#   (3) result ≤ currentYear + 50                           [never >50y future]
#   (4) year + cc ≤ currentYear + 50 → result = year + cc   [default century]
#   (5) currentYear + 50 < year + cc → result = year + cc-100 [roll back one century]
#
# CARRIER NOTE: the nagini sibling contracted `expand_two_digit_year(two_digit_year,
# reference_year)` under a precondition `0 <= two_digit_year < 100`, pinning the
# value to a fully-grounded @Pure helper `resolved_year(...)`. This backend models
# the same arithmetic but with a WIDER domain — the obligation's only precondition is
# `0 ≤ year`, and the spec covers the `year ≥ 100` passthrough as its own clause (1).
# So nagini's value clause maps onto clauses (2)-(5) here, AND clause (1) — a
# behaviour outside nagini's precondition — is additionally attackable (see
# weak-drop-year-guard).
#
# NAGINI CASES AND HOW THEY PORT (see 'assessment' in the verdict for the summary):
#   pos-cheapest        -> pos-direct-functional (verify). No standalone oracle exists
#                          here (behaviour is pinned by case predicates, not
#                          `result = f(args)`); the honest cheapest analogue is a
#                          structurally-different CORRECT functional impl, reproven.
#   pos-reshaped        -> pos-reshape-negated-guard (verify).
#   admiss-f2p-shape    -> admiss-pinned-shapes (verify). Nagini asserted the
#                          F2P-pinned values inside the impl via `Assert(...)`. The
#                          lean counterpart is a throwaway `example ... := by decide`
#                          sitting INSIDE the impl region: the impl region is elided
#                          from the spec view (so same_spec holds) and an `example` is
#                          not a theorem/lemma (so variant_scope admits it), while the
#                          checker still has to CONFIRM each pinned value. That is the
#                          same obligation `Assert` discharges, so this case ports.
#   weak-prepatch-fixed-cutoff -> weak-fixed-cutoff (reject).
#   weak-boundary-ge50  -> weak-boundary-ge50 (reject).
#   weak-threshold-49   -> OMITTED. On the Int carrier `year - cc > 49` and
#                          `year - cc ≥ 50` are the SAME predicate (integers), so this
#                          near-miss is byte-for-byte behaviourally identical to
#                          weak-boundary-ge50 and shipping it would be a duplicate
#                          refuted at the same input for the same reason. Demonstrated,
#                          not asserted: `∀ year currentYear, impl_49 year currentYear =
#                          impl_ge50 year currentYear` is provable by
#                          `split_ifs <;> first | rfl | omega` (built, exit 0).
#   weak-no-rollback    -> weak-no-rollback (reject).
#   weak-century-noclear-> weak-century-noclear (reject).
#   (NEW, carrier-widening) weak-drop-year-guard (reject) — attacks clause (1), which
#                          nagini's `year < 100` precondition excluded from its model.
#   (NEW, audit) weak-fencepost-century (reject) — a century base off by one
#                          fencepost, `(currentYear - 1) / 100 * 100`. Agrees with the
#                          frozen impl for EVERY reference year whose last two digits
#                          are nonzero, so no other rival's input can see it; it
#                          diverges exactly on the `currentYear % 100 = 0` reference
#                          years, a sub-domain the rest of the battery never varies.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's read-only `Acc(x,1/2)` pointer class): both inputs are
#     bare scalar Ints and Lean is referentially transparent — no aliasing, no
#     fractional permission, nothing to overwrite. The whole lane is VACUOUS here.
#   * AXIOM_TESTS: the axiom lane is G-AX's job and this gate ignores it. The
#     arithmetic is modeled DEEPLY (no opaque callee, no consumed axiom) so there is
#     no callee contract to probe anyway.
from pathlib import Path

INSTANCE = "django__django-11848"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The inner century-expansion block, lying ENTIRELY inside impl-start/impl-end and
# unique in the file. Rivals that keep the `if year < 100` guard edit THIS block.
_INNER = (
    "    let currentCentury := currentYear - currentYear % 100\n"
    "    if year - currentYear % 100 > 50 then\n"
    "      y := y + currentCentury - 100\n"
    "    else\n"
    "      y := y + currentCentury"
)
assert _BASE.count(_INNER) == 1, "inner block anchor drifted"

# The full impl def (used by rivals/positives that change the def shape itself).
_FULL_IMPL = (
    "def implementation_expandYear (year currentYear : Int) : Int := Id.run do\n"
    "  let mut y := year\n"
    "  if year < 100 then\n"
    "    let currentCentury := currentYear - currentYear % 100\n"
    "    if year - currentYear % 100 > 50 then\n"
    "      y := y + currentCentury - 100\n"
    "    else\n"
    "      y := y + currentCentury\n"
    "  return y"
)
assert _BASE.count(_FULL_IMPL) == 1, "full impl anchor drifted"

# The frozen proof body (only the tactic lines inside proof-start/proof-end). Swapped
# only by the functional positive, whose non-`Id.run` impl needs the same tactic
# script minus the `Id.run` normalisation step — the identical theorem STATEMENT is
# preserved byte-for-byte.
_PROOF = _BASE[
    _BASE.index("  intro year currentYear hy"):
    _BASE.rindex("<;> omega") + len("<;> omega")
]
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"

# The unique century-comparison, used by the boundary rival.
_CMP = "if year - currentYear % 100 > 50 then"
assert _BASE.count(_CMP) == 1, "comparison anchor drifted"

# The unique century-start binding, used by the no-clear rival.
_CENT = "let currentCentury := currentYear - currentYear % 100"
assert _BASE.count(_CENT) == 1, "century-start anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-reshape-negated-guard: structurally-DIFFERENT but behaviourally identical.
# The century remainder is hoisted to a local `c`, the SAME-century case is tested
# first through a negated guard (`≤ 50`, else-first), and the century start is
# computed from `c`. Same arithmetic on every input; the frozen `Id.run do` shape and
# the frozen `theorem correct_expandYear` statement are preserved and the frozen proof
# body still closes (branch reorder + let are transparent to the split/omega script),
# so this is a faithful restructure with no reproof, no new axiom/lemma/sorry. If it
# FAILS => SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape).
_POS_RESHAPE = _swap(
    _BASE,
    _INNER,
    "    let c := currentYear % 100\n"
    "    let currentCentury := currentYear - c\n"
    "    if year - c ≤ 50 then\n"
    "      y := y + currentCentury\n"
    "    else\n"
    "      y := y + currentCentury - 100",
)

# pos-direct-functional: the cheapest HONEST impl in a DIFFERENT shape — a pure
# functional `if-then-else` on the Int inputs, no `Id.run do` / `let mut`. The value
# is produced by the modeled arithmetic (not echoed from an oracle — there is none),
# so it must verify; the proof is the frozen script minus the `Id.run` normalisation
# line (the theorem STATEMENT is byte-identical). If it FAILS => SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE,
        _FULL_IMPL,
        "def implementation_expandYear (year currentYear : Int) : Int :=\n"
        "  if year < 100 then\n"
        "    if year - currentYear % 100 > 50 then\n"
        "      year + (currentYear - currentYear % 100) - 100\n"
        "    else\n"
        "      year + (currentYear - currentYear % 100)\n"
        "  else year",
    ),
    _PROOF,
    "  intro year currentYear hy\n"
    "  unfold problem_spec_expandYear implementation_expandYear\n"
    "  split <;> rename_i h1\n"
    "  · split <;> rename_i h2 <;>\n"
    "      refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega\n"
    "  · refine ⟨fun _ => ?_, fun _ => ⟨?_, ?_, fun _ => ?_, fun _ => ?_⟩⟩ <;> omega",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-fixed-cutoff: the PRE-PATCH skeleton — a FIXED pivot at 70 that ignores the
# reference year entirely (0..69 -> +2000, 70..99 -> +1900). Exactly the behaviour the
# fix removes.
_RIV_CUTOFF = _swap(
    _BASE,
    _INNER,
    "    if year < 70 then\n"
    "      y := y + 2000\n"
    "    else\n"
    "      y := y + 1900",
)

# weak-boundary-ge50: off-by-one at the rollback threshold — `≥ 50` instead of `> 50`.
# Correct everywhere except the exact boundary `year - cc = 50`, where it wrongly rolls
# back one century.
_RIV_GE50 = _swap(_BASE, _CMP, "if year - currentYear % 100 ≥ 50 then")

# weak-no-rollback: drops the future-rollback rule — always stays in the reference
# century. Correct on the near half of the domain, wrong on every input >50y ahead.
_RIV_NOROLL = _swap(
    _BASE,
    _INNER,
    "    let currentCentury := currentYear - currentYear % 100\n"
    "    y := y + currentCentury",
)

# weak-century-noclear: uses the reference year ITSELF as the century base instead of
# clearing its last two digits — so the reference year's own last two digits get added
# in and the last-two-digits clause fails whenever currentYear % 100 ≠ 0.
_RIV_NOCLEAR = _swap(_BASE, _CENT, "let currentCentury := currentYear")

# weak-drop-year-guard: drops the `if year < 100` guard, applying the century transform
# to ALL years — so an already-full year (year ≥ 100) is mangled instead of returned
# verbatim. Attacks clause (1), which nagini's precondition excluded.
_RIV_DROPGUARD = _swap(
    _BASE,
    _FULL_IMPL,
    "def implementation_expandYear (year currentYear : Int) : Int := Id.run do\n"
    "  let mut y := year\n"
    "  let currentCentury := currentYear - currentYear % 100\n"
    "  if year - currentYear % 100 > 50 then\n"
    "    y := y + currentCentury - 100\n"
    "  else\n"
    "    y := y + currentCentury\n"
    "  return y",
)

# weak-fencepost-century: the century base taken one fencepost early —
# `(currentYear - 1) / 100 * 100` instead of clearing the last two digits. This is
# the interesting near-miss for the `currentYear` binder: for every reference year
# with nonzero last two digits it is EQUAL to the frozen base, so none of the other
# rivals' inputs (all at currentYear ∈ {2019, 2020}) can distinguish it. It diverges
# exactly on the reference years that are century starts (`currentYear % 100 = 0`),
# where it drops the century by 100 and the last-two-digits clause fails.
_RIV_FENCEPOST = _swap(
    _BASE, _CENT, "let currentCentury := (currentYear - 1) / 100 * 100")

# admiss-pinned-shapes: the frozen impl UNCHANGED, plus throwaway `example`s inside
# the impl region pinning the concrete expansions the real behaviour fixes, and one
# pinning that the obligation's precondition domain (`0 ≤ year`) actually contains
# such a `year`. This is the lean counterpart of nagini's in-impl `Assert(...)`: the
# impl region is elided from the spec view (same_spec holds), an `example` is neither
# a theorem/lemma nor an assumption-bearing declaration (variant_scope admits it),
# and the checker must still CONFIRM each pinned value by computation. If any pinned
# shape failed to elaborate, the modeled domain would not admit it =>
# PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE,
    _FULL_IMPL,
    _FULL_IMPL + "\n\n"
    "-- Admissibility: the obligation's domain (`0 ≤ year`) admits the pinned\n"
    "-- two-digit shapes, and the modeled arithmetic yields exactly the expansion\n"
    "-- each pinned reference year calls for (both near-half and rolled-back).\n"
    "example : implementation_expandYear 69 2019 = 2069 := by decide\n"
    "example : implementation_expandYear 70 2019 = 1970 := by decide\n"
    "example : implementation_expandYear 94 2019 = 1994 := by decide\n"
    "example : implementation_expandYear 70 2020 = 2070 := by decide\n"
    "example : implementation_expandYear 71 2020 = 1971 := by decide\n"
    "example : implementation_expandYear 0 2048 = 2000 := by decide\n"
    "example : implementation_expandYear 99 2048 = 1999 := by decide\n"
    "example : (0 : Int) ≤ 69 := by decide",
)


def _wit(year, cur, note):
    """A refutation witness: `¬ problem_spec_expandYear year cur (implementation …)`
    at a concrete literal Int input, closed by `decide`. Elaborates against a rival
    that diverges from the spec there, and FAILS on gold (which satisfies the spec at
    every `0 ≤ year`)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_expandYear {year} {cur}\n"
        f"    (implementation_expandYear {year} {cur}) := by\n"
        f"  unfold problem_spec_expandYear implementation_expandYear\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reshape-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": (
            "structurally-different but CORRECT impl: the century remainder is hoisted "
            "to a local `c`, the same-century case is tested first via a negated guard "
            "(`≤ 50`, else-first), and the century start is computed from `c`. Same "
            "arithmetic on every input; the frozen `Id.run do` shape and the frozen "
            "`theorem correct_expandYear` statement are preserved and the frozen proof "
            "body still closes (branch reorder + let are transparent to the split/omega "
            "script). No reproof, no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-direct-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the honest cheapest analogue of nagini's pos-cheapest in a DIFFERENT shape "
            "— a pure functional `if-then-else` on the Int inputs (no `Id.run do` / "
            "`let mut`). There is no answer-key oracle to echo; the value is produced by "
            "the modeled arithmetic, so it must verify. The proof is the frozen tactic "
            "script minus the `Id.run` normalisation line, and the `theorem "
            "correct_expandYear` statement is byte-identical. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-fixed-cutoff",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CUTOFF,
        "refinement": (
            "this is the verbatim PRE-PATCH logic — a fixed pivot at 70 that ignores the "
            "reference year. Its faithful real patch is the unpatched code, which the "
            "F2P tests fail: at reference year 2020, a two-digit year 70 is pinned to a "
            "full year in the 2070s, but the fixed cut-off (70 -> +1900) gives the "
            "1970s. So its faithful patch does NOT resolve the F2P; a verifying rival is "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause (4): at (year=70, currentYear=2020), year + cc = 2070 = "
            "currentYear + 50, so the default-century branch requires result = 2070, but "
            "the fixed cut-off yields 1970. Varies the `year` binder into the upper "
            "two-digit band while pinning a reference century where the fix and the "
            "cut-off disagree. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (70,2020): gold clause (4) -> 2070; rival -> 70+1900 = 1970.
        "witness": _wit(70, 2020,
                        "fixed cutoff ignores reference year: gold=2070, rival=1970"),
    },
    {
        "id": "weak-boundary-ge50",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_GE50,
        "refinement": (
            "off-by-one at the rollback threshold (`≥ 50` for `> 50`): diverges ONLY at "
            "`year - cc = 50`. The F2P pins exactly this boundary — reference year 2019, "
            "two-digit year 69 (69 - 19 = 50) expands to the 2069 full year; gold keeps "
            "the reference century (2069) but this rival rolls back to 1969. Its faithful "
            "patch fails that F2P case and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (4): at (year=69, currentYear=2019), year + cc = 2069 = "
            "currentYear + 50, so the boundary belongs to the default-century branch "
            "(strict `> 50` does NOT roll back). The rival's `≥ 50` rolls back, giving "
            "1969. Varies `year` to the exact boundary input for this reference. If it "
            "VERIFIES => SPEC-TOO-WEAK. (Nagini's threshold-49 near-miss collapses onto "
            "this same predicate on the Int carrier and is omitted.)"
        ),
        # (69,2019): year-cc = 50, boundary -> gold clause (4) = 2069; rival = 1969.
        "witness": _wit(69, 2019,
                        "boundary year-cc=50: gold stays 2069, rival rolls back to 1969"),
    },
    {
        "id": "weak-no-rollback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOROLL,
        "refinement": (
            "never rolls back: always stays in the reference century. The F2P pins "
            "reference year 2020, two-digit year 71 (71 - 20 = 51 > 50) to the 1971 full "
            "year — more than 50 years ahead, so gold rolls back to 1971 — but this rival "
            "gives 2071. Its faithful patch fails that F2P case and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (5) and clause (3): at (year=71, currentYear=2020), "
            "currentYear + 50 = 2070 < year + cc = 2071, so clause (5) requires result = "
            "1971, but the rival gives 2071 — which also violates clause (3) "
            "(result ≤ currentYear + 50). Varies `year` onto the future subdomain. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (71,2020): year-cc = 51 > 50 -> gold rolls back to 1971; rival = 2071.
        "witness": _wit(71, 2020,
                        "future >50y: gold rolls back to 1971, rival overshoots to 2071"),
    },
    {
        "id": "weak-century-noclear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOCLEAR,
        "refinement": (
            "uses the reference year itself as the century base instead of clearing its "
            "last two digits, so the reference year's own last two digits are added into "
            "the result. At reference year 2019, two-digit year 94 (94 - 19 = 75 > 50, "
            "the rollback branch) is pinned to the 1994 full year, but this rival gives "
            "94 + 2019 - 100 = 2013. Its faithful patch produces a wrong full year and "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2) (result % 100 = year): adding the full reference "
            "year rather than its century start makes the last two digits wrong whenever "
            "currentYear % 100 ≠ 0. At (year=94, currentYear=2019) the rival yields 2013 "
            "(2013 % 100 = 13 ≠ 94); clause (5) also fails. Varies `year` while pinning a "
            "reference with nonzero last two digits. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (94,2019): gold rollback -> 1994; rival = 94+2019-100 = 2013, %100 = 13 ≠ 94.
        "witness": _wit(94, 2019,
                        "reference not century-cleared: gold=1994 (%100=94), rival=2013"),
    },
    {
        "id": "weak-drop-year-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPGUARD,
        "refinement": (
            "drops the `year < 100` guard, applying the century transform to ALL years "
            "— so an already-full year is mangled instead of returned verbatim. A "
            "four-digit year field (e.g. the 1994 in an rfc1123 date) would be rewritten, "
            "breaking a PASS_TO_PASS date parse that must round-trip a full year "
            "unchanged. Its faithful patch does NOT resolve (it regresses full-year "
            "inputs)."
        ),
        "rationale": (
            "REJECTED by clause (1) (year ≥ 100 → result = year): at (year=1994, "
            "currentYear=2019) the spec requires result = 1994, but the guardless rival "
            "computes 1994 + 2000 - 100 = 3894 ≠ 1994. This clause lies OUTSIDE nagini's "
            "`year < 100` precondition — a carrier-widening rival. Varies `year` into the "
            "≥ 100 passthrough regime, a subdomain no other witness probes. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # (1994,2019): clause (1) demands result=1994; rival mangles to 3894.
        "witness": _wit(1994, 2019,
                        "full-year passthrough: gold returns 1994 verbatim, rival mangles it"),
    },
    {
        "id": "weak-fencepost-century",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FENCEPOST,
        "refinement": (
            "the century base is taken one fencepost early — `(currentYear - 1) / 100 * "
            "100` rather than clearing the reference year's last two digits. For every "
            "reference year whose last two digits are nonzero the two agree exactly, so "
            "this rival is behaviourally indistinguishable from the frozen impl on the "
            "inputs the rest of the battery uses; it diverges only when the reference "
            "year IS a century start. Its faithful patch expands a two-digit year into "
            "the century BEFORE the reference one for any request parsed during a "
            "century-start year, producing a wrong full year, so it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (2) (result % 100 = year) and clause (4): at (year=5, "
            "currentYear=2000), cc = 2000 and the default-century branch requires "
            "result = 2005, but `(2000 - 1) / 100 * 100 = 1900` gives 1905. This is the "
            "only case that VARIES the `currentYear` binder onto a MEANINGFUL second "
            "point — every other witness pins currentYear to 2019 or 2020, both of "
            "which this rival gets right. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # (5,2000): gold clause (4) -> 2005; rival -> 1905, and 1905 % 100 = 5 but
        # the value clause still fails (1905 ≠ 2005).
        "witness": _wit(5, 2000,
                        "century-start reference: gold=2005, fencepost base gives 1905"),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-pinned-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the port of nagini's admiss-f2p-shape. The impl is the frozen one; the "
            "case adds throwaway `example`s INSIDE the impl region (elided from the "
            "spec view, and an `example` is neither a new theorem/lemma nor an "
            "assumption-bearing decl, so the variant stays in scope) pinning the "
            "concrete expansions the modeled behaviour must produce at several "
            "reference years — both the same-century half and the rolled-back half — "
            "plus one pinning that `0 ≤ year` admits such a `year`. The checker must "
            "CONFIRM each by computation, which is the obligation nagini's `Assert(...)` "
            "discharged. If any FAILS => the modeled domain does not admit a shape the "
            "real behaviour requires => PRECOND-TOO-STRONG."
        ),
    },
]


# No @ContractOnly axioms and no opaque callees: the year expansion is exact integer
# arithmetic modeled DEEPLY, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
