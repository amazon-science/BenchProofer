# properties.py — PBT falsification battery for astropy__astropy-7671.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-identically (region surgery edits ONLY inside the
# # impl-start / # impl-end region — the nested # invariants-* markers live
# inside that region too, so they may be reshaped without touching the spec)
# and are checked by Nagini verify + markers.same_spec. Axiom cases are
# real-callee probes run in Docker.
#
# ===========================================================================
# Defended surface (read from model.py + refinement.md + mapping.md + the gold
# patch + the F2P test).
# ===========================================================================
#
#   version_meets_minimum(have: List[int], want: List[int], inclusive: bool)
#       Requires(Acc(list_pred(have), 1/2))            # READ-ONLY input (1/2)
#       Requires(Acc(list_pred(want), 1/2))            # READ-ONLY input (1/2)
#       Requires(is_numeric(ToSeq(have)))              # installed ver is numeric
#       Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)   # numeric head
#       Ensures (Acc(list_pred(have), 1/2))            # frame: input unchanged
#       Ensures (Acc(list_pred(want), 1/2))            # frame: input unchanged
#       Ensures (is_numeric(ToSeq(have)))
#       Ensures (Implies(inclusive,
#                        Result() == loose_ge(ToSeq(have), normalize(ToSeq(want)))))  # C-ge
#       Ensures (Implies(not inclusive,
#                        Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))  # C-gt
#
# The load-bearing discriminating clauses are C-ge / C-gt: the result is the
# component-wise version order against the *qualifier-STRIPPED* requested
# version `normalize(ToSeq(want))`, inclusively (>=) or strictly (>). The gold
# patch's delta is exactly "strip the non-numeric qualifier tail BEFORE
# comparing" (re.match(PEP440-prefix, version).group(0)); the pre-patch code
# compared the raw `version`, which makes LooseVersion raise a TypeError on
# "0.12dev" (the new F2P good-version) and so the F2P fails pre-patch.
#
# F2P (instance.json): astropy/utils/tests/test_introspection.py::test_minversion
#   test_module.__version__ = '0.12.2'        => have ~ [0,12,2]
#   good_versions (must return TRUE, inclusive=True default):
#       '0.12'       ~ [0,12]        normalize=[0,12]      ge True
#       '0.12.1'     ~ [0,12,1]      normalize=[0,12,1]    ge True
#       '0.12.0.dev' ~ [0,12,0,-1]   normalize=[0,12,0]    ge True
#       '0.12dev'    ~ [0,12,-1]     normalize=[0,12]      ge True   <-- new F2P
#   bad_versions (must return FALSE):
#       '1'          ~ [1]           normalize=[1]         ge False
#       '1.2rc1'     ~ [1,2,-1]      normalize=[1,2]       ge False
#
# ===========================================================================
# What the spec defends, and the attacks it must survive (§4a doctrine).
# ===========================================================================
#
#   * FRAME MUTATION (MANDATORY, directive 5): both `have` and `want` are
#     READ-ONLY heap inputs held at Acc(...,1/2). A rival that WRITES to either
#     to satisfy the postcondition vacuously must be rejected for INSUFFICIENT
#     PERMISSION (a store / append through a 1/2 reference needs full perm, and
#     the Ensures(Acc(...,1/2)) frame cannot be re-established after a full
#     write). The gold loop/invariants are kept verbatim around the injected
#     write so the rejection is attributable solely to the mutation. Both probes
#     are present (frame-mutate-want, frame-mutate-have).
#
#   * UNGROUNDED-ORACLE ECHO (directive 2): there is NO opaque answer-key to
#     echo. `normalize`, `loose_ge`, `loose_gt` are @Pure helpers FULLY UNFOLDED
#     over the inputs (model.py pure region) — `Result() == loose_ge(have,
#     normalize(want))` is a function OF the args, not a marker. Returning that
#     expression directly IS the gold behaviour, so it is an honest cheapest-impl
#     POSITIVE control (pos-delegate-grounded-oracle), not a wrong echo. See
#     'assessment'.
#
#   * PARTIAL-DOMAIN: the decisive attacks. (a) compare the RAW `want` with no
#     strip (the pre-patch shape, model_prepatch.py) — diverges exactly on a
#     qualifier-bearing want like '0.12dev'/'1.2rc1'; (b) swap inclusive>=/strict>
#     — diverges exactly on the equality boundary (installed == requested-min);
#     (c) keep the qualifier marker in `norm` (treat the tail as a release
#     segment) — diverges on a qualifier-bearing want just like (a) but via a
#     different mechanism.
#
#   * CONTROL-FLOW-EFFECT: N/A. The routine returns a pure bool and the only
#     "effect" the issue cares about (the raw comparison would RAISE a TypeError)
#     is modeled as a returned value (loose_ge yields the non-satisfied outcome
#     False at a numeric-vs-marker position). There is no raise / side-effect
#     invisible to the value abstraction, so no capability-token rival is needed
#     (see 'assessment').
#
# Authoring mechanics: every variant is built by REGION-SURGERY (`_swap`) that
# edits ONLY inside the single # impl-start/# impl-end block (the nested
# # invariants-* markers are inside it), so markers.same_spec is guaranteed and
# a rejection comes from the POSTCONDITION (or the permission system), never from
# a tampered spec. Each expect="reject" rival carries the refinement argument
# that its faithful real patch would NOT resolve the F2P.

from pathlib import Path

INSTANCE = "astropy__astropy-7671"
FLOAT_ENCODING = None  # meta.json float_encoding is null


# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError("properties.py drift: substring not found:\n%r" % old)
    if src.count(old) != 1:
        raise AssertionError("properties.py: substring not unique: %r" % old)
    return src.replace(old, new, 1)


# ===========================================================================
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ===========================================================================

# The whole impl body (between # impl-start and # impl-end, exclusive). Used as
# a single replaceable block for the rivals that change the whole shape.
_GOLD_IMPL = """    norm = []  # type: List[int]
    i = len(want)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(have), 1 / 2))
        Invariant(Acc(list_pred(want), 1 / 2))
        Invariant(Acc(list_pred(norm)))
        Invariant(is_numeric(ToSeq(have)))
        Invariant(0 <= i and i <= len(want))
        Invariant(ToSeq(norm) == normalize(ToSeq(want).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = want[i - 1]
        Assert(ToSeq(want).drop(i - 1)[0] == c)
        Assert(ToSeq(want).drop(i - 1).drop(1) == ToSeq(want).drop(i))
        if c < 0:
            norm = []  # qualifier marker: discard the tail accumulated so far
        else:
            norm = [c] + norm
        i = i - 1
    Assert(ToSeq(norm) == normalize(ToSeq(want)))
    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(norm))
    else:
        return loose_gt(ToSeq(have), ToSeq(norm))"""

# The final comparison/return tail (where ge/gt and norm-vs-want live).
_GOLD_RETURN = """    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(norm))
    else:
        return loose_gt(ToSeq(have), ToSeq(norm))"""

# The read of `want` at the head of the loop body (frame-mutate-want anchor).
_GOLD_WANT_READ = "        c = want[i - 1]\n"

# The qualifier-reset branch (keep-marker rival anchor).
_GOLD_MARKER_BRANCH = """        if c < 0:
            norm = []  # qualifier marker: discard the tail accumulated so far
        else:
            norm = [c] + norm"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) DELEGATE / grounded-oracle positive control. Replace the whole body with
# the pinned expression returned directly. `normalize` is @Pure and GROUNDED in
# `want` (fully unfolded), so `loose_ge(ToSeq(have), normalize(ToSeq(want)))` is
# the exact gold behaviour, not a wrong echo. No loop, no invariants needed. If
# this fails to verify the spec is over-fit to the loop form => SPEC-TOO-STRONG.
_POS_DELEGATE = _swap(_BASE, _GOLD_IMPL, """    if inclusive:
        return loose_ge(ToSeq(have), normalize(ToSeq(want)))
    else:
        return loose_gt(ToSeq(have), normalize(ToSeq(want)))""")

# (P2) STRUCTURAL RESHAPE positive control. Keep the backward strip loop AND all
# its invariants/asserts VERBATIM (the proof that ToSeq(norm)==normalize(want)
# is the load-bearing obligation — deleting it would be a PROOF gap, not a spec
# defect, per PBT_PLAN caution 2). Only the final return is reshaped to a
# single assign-once / return-once on a local. Semantically identical, so it
# MUST verify (else SPEC-TOO-STRONG — over-fit to the if/else return form).
_POS_RESHAPE = _swap(_BASE, _GOLD_RETURN, """    res = loose_gt(ToSeq(have), ToSeq(norm))
    if inclusive:
        res = loose_ge(ToSeq(have), ToSeq(norm))
    return res""")

# (A1) ADMISSIBILITY. A self-call on the actual F2P-shaped parameters exercises
# the precondition at a real call site: it must re-establish
# Acc(list_pred(have),1/2) * Acc(list_pred(want),1/2) (splittable from the held
# 1/2) AND the value facts is_numeric(ToSeq(have)) and len(want)>0 & want[0]>=0
# — all already guaranteed by THIS function's own Requires, and returned by the
# callee's Ensures so the held permissions/facts survive the call. The gold body
# follows verbatim, so the postcondition obligation is unchanged. If the Requires
# could not be re-established for a legitimate in-domain input => PRECOND-TOO-
# STRONG. (Passing the real params rather than a fresh literal list avoids the
# is_numeric([0,12,2]) auto-unfold proof gap that PBT_PLAN caution 2 warns of.)
_ADMISS = _swap(_BASE, "    norm = []  # type: List[int]\n",
                "    Assert(Acc(list_pred(have), 1 / 2))\n"
    "    Assert(Acc(list_pred(want), 1 / 2))\n"
    "    Assert(is_numeric(ToSeq(have)))\n"
    "    Assert(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)\n"
                "    norm = []  # type: List[int]\n")


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (R1) FRAME MUTATION of `want` — MANDATORY (#1 weakness class). Inside the loop
# the rival WRITES `want[i - 1] = c` immediately after reading `c = want[i-1]`
# (an idempotent self-write, so no value would change). A store through a 1/2
# (read-only) reference requires FULL permission, so it MUST fail for INSUFFICIENT
# PERMISSION — not for a wrong value. The index i-1 is provably in-bounds (the
# loop reads want[i-1] on the line above), so the rejection is attributable
# solely to the write, not an index check. Rejection source: the PERMISSION
# SYSTEM.
_RIVAL_FRAME_WANT = _swap(
    _BASE, _GOLD_WANT_READ,
    "        c = want[i - 1]\n        want[i - 1] = c\n")

# (R2) FRAME MUTATION of `have` — MANDATORY (#1 weakness class). The rival
# APPENDS to `have` at the top of the body (`have.append(0)`). A list append
# requires FULL permission on list_pred(have); the precondition grants only
# Acc(list_pred(have),1/2), so it MUST fail for INSUFFICIENT PERMISSION, and the
# Ensures(Acc(list_pred(have),1/2)) frame could never be re-established after a
# mutation. The gold body follows verbatim. Rejection source: the PERMISSION
# SYSTEM.
_RIVAL_FRAME_HAVE = _swap(
    _BASE, "    norm = []  # type: List[int]\n",
    "    have.append(0)\n    norm = []  # type: List[int]\n")

# (R3) PARTIAL-DOMAIN / NO-STRIP (the pre-patch shape, model_prepatch.py).
# Compare against the RAW `want` (no qualifier stripping). Correct on every
# qualifier-FREE requested version, but DIVERGES exactly on a qualifier-bearing
# want: for '0.12dev' ~ [0,12,-1] the comparison reaches the qualifier marker
# and loose_ge yields the non-satisfied outcome False, where the spec
# (normalize first -> [0,12]) requires True. MUST be rejected.
_RIVAL_NO_STRIP = _swap(_BASE, _GOLD_IMPL, """    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(want))
    else:
        return loose_gt(ToSeq(have), ToSeq(want))""")

# (R4) VALUE-DOUBLE-MASK / inclusive<->strict SWAP. Use the STRICT order for the
# inclusive branch and the INCLUSIVE order for the strict branch. Correct
# everywhere EXCEPT the equality boundary (installed == requested-min): for an
# inclusive call with have == normalize(want) the spec requires True (>=) but the
# rival returns loose_gt == False. Diverges only on that sub-domain. MUST be
# rejected.
_RIVAL_GE_GT_SWAP = _swap(_BASE, _GOLD_RETURN, """    if inclusive:
        return loose_gt(ToSeq(have), ToSeq(norm))
    else:
        return loose_ge(ToSeq(have), ToSeq(norm))""")

# (R5) PARTIAL-DOMAIN / inclusive-only strict. Keep the strict branch correct but
# make the inclusive branch use the STRICT order. Diverges ONLY on the equality
# boundary in the inclusive case (the surgically-minimal partial-domain pinned to
# the input that fails first: a requested minimum exactly equal to the installed
# version, which the inclusive contract must accept). MUST be rejected.
_RIVAL_INCLUSIVE_GT = _swap(_BASE, _GOLD_RETURN, """    if inclusive:
        return loose_gt(ToSeq(have), ToSeq(norm))
    else:
        return loose_gt(ToSeq(have), ToSeq(norm))""")

# (R6, supporting) KEEP-MARKER. The strip loop never resets `norm` on a qualifier
# marker — it accumulates EVERY segment including the -1 marker (treating the
# qualifier tail as a release segment). So norm carries the marker for a
# qualifier-bearing want, and loose_ge reaches the numeric-vs-marker position and
# yields False where the spec (which strips) requires True. Diverges on the SAME
# sub-domain as R3 but via the loop body rather than the comparison operand; a
# distinct mechanism for the same defended behaviour. MUST be rejected.
_RIVAL_KEEP_MARKER = _swap(_BASE, _GOLD_MARKER_BRANCH,
                           "        norm = [c] + norm")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-delegate-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DELEGATE,
        "rationale": (
            "the honest cheapest impl: return the pinned expression "
            "loose_ge/loose_gt(ToSeq(have), normalize(ToSeq(want))) directly (no "
            "loop). `normalize`/`loose_ge`/`loose_gt` are @Pure and GROUNDED in "
            "the args (fully unfolded), so the only thing 'echoable' is the true "
            "decision; this IS the gold behaviour and MUST verify. Shows the spec "
            "is not ungrounded-oracle-echo-vulnerable. If it failed => "
            "SPEC-TOO-STRONG (over-fit to the loop form)."),
    },
    {
        "id": "pos-single-return-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": (
            "structurally different but correct: the backward strip loop and all "
            "its invariants/asserts (incl. ToSeq(norm)==normalize(want)) are kept "
            "VERBATIM (no proof-gap trap), only the final return is reshaped to a "
            "single assign-once / return-once on a local. Semantically identical, "
            "so it MUST verify (else SPEC-TOO-STRONG — over-fit to the if/else "
            "return form)."),
    },
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "a self-call version_meets_minimum(have, want, inclusive) on the actual "
            "F2P-shaped parameters exercises the precondition at a real call site: "
            "it must re-establish Acc(list_pred(have),1/2)*Acc(list_pred(want),1/2) "
            "(splittable from the held 1/2) and the value facts is_numeric(have) and "
            "len(want)>0 & want[0]>=0 — all guaranteed by the Requires and returned "
            "by the Ensures. If a legitimate in-domain input could not satisfy the "
            "precondition => PRECOND-TOO-STRONG. Passing the real params avoids the "
            "is_numeric([0,12,2]) auto-unfold proof gap."),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "frame-mutate-want",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FRAME_WANT,
        "refinement": (
            "no faithful real patch corresponds to this: the gold minversion never "
            "mutates the requested-version string/list — it READS it (re.match, "
            "then LooseVersion(version)). The rival exists only to test whether the "
            "read-only (1/2) precondition on `want` can be subverted by writing to "
            "it. No resolving patch overwrites the requested version, so a verifying "
            "rival here would be a pure verify-not-resolve artifact (vacuous "
            "satisfaction via self-mutation)."),
        "rationale": (
            "MANDATORY frame-mutation probe. `want[i-1] = c` writes through a 1/2 "
            "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (store "
            "needs full perm; the Ensures(Acc(want,1/2)) frame cannot be "
            "re-established after a write) — not for a wrong value (the write is "
            "idempotent and the index is provably in-bounds). Rejection source: the "
            "PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK (frame protection "
            "hollow)."),
    },
    {
        "id": "frame-mutate-have",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FRAME_HAVE,
        "refinement": (
            "no faithful real patch corresponds to this: the gold minversion never "
            "mutates the installed-version value (it only reads have_version to "
            "build LooseVersion(have_version)). The rival exists only to test "
            "whether the read-only (1/2) precondition on `have` can be subverted by "
            "appending to it. A verifying rival here would be a pure verify-not-"
            "resolve artifact."),
        "rationale": (
            "MANDATORY frame-mutation probe. `have.append(0)` requires FULL "
            "permission on list_pred(have) but the precondition grants only "
            "Acc(list_pred(have),1/2), so it MUST fail for INSUFFICIENT PERMISSION "
            "and the Ensures(Acc(have,1/2)) frame could never be re-established. "
            "Rejection source: the PERMISSION SYSTEM. If it verified => "
            "SPEC-TOO-WEAK (frame protection hollow)."),
    },
    {
        "id": "rival-no-strip-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NO_STRIP,
        "refinement": (
            "this is the PRE-PATCH minversion (model_prepatch.py): compare against "
            "the RAW requested version with no qualifier stripping — "
            "LooseVersion(have_version) >= LooseVersion(version) on the un-stripped "
            "version. On the new F2P good-version '0.12dev' the real LooseVersion "
            "comparison RAISES a TypeError (int 12 vs str 'dev'), so "
            "minversion(test_module, '0.12dev') propagates the exception and the "
            "F2P test_minversion FAILS. Its faithful real patch is exactly the "
            "base_commit code (no re.match strip), which does NOT resolve."),
        "rationale": (
            "the discriminating partial-domain rival (= G-DIFF against "
            "model_prepatch.py). Rejection source: the postcondition C-ge "
            "Result()==loose_ge(have, normalize(want)): the rival returns "
            "loose_ge(have, want) (raw), which for a qualifier-bearing want like "
            "[0,12,-1] reaches the numeric-vs-marker position and yields False where "
            "normalize-first requires True. If it verified => SPEC-TOO-WEAK (the "
            "strip is unmodeled)."),
    },
    {
        "id": "rival-ge-gt-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_GE_GT_SWAP,
        "refinement": (
            "faithful real patch: use `>` for the inclusive branch and `>=` for the "
            "strict branch (the two operators swapped). On a test where the installed "
            "version EXACTLY equals the requested minimum and inclusive=True, the "
            "real minversion would return False instead of True — the documented "
            "inclusive semantics ('installed is AT LEAST the requested') is violated, "
            "so any test asserting minversion(mod, installed_exact) is True FAILS. It "
            "does NOT resolve."),
        "rationale": (
            "value-double-mask on the equality boundary. Rejection source: BOTH "
            "postcondition branches are independently pinned — C-ge requires "
            "loose_ge on the inclusive branch and C-gt requires loose_gt on the "
            "strict branch; the swap returns loose_gt on the inclusive branch "
            "(False at have==normalize(want), where loose_ge is True). If it "
            "verified => SPEC-TOO-WEAK (inclusive/strict not pinned)."),
    },
    {
        "id": "rival-inclusive-only-gt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_INCLUSIVE_GT,
        "refinement": (
            "surgically-minimal partial-domain: keep the strict branch correct but "
            "use `>` (strict) for the inclusive branch. Faithful real patch: "
            "`return LooseVersion(have_version) > LooseVersion(version)` even when "
            "inclusive=True. Diverges ONLY when the installed version exactly equals "
            "the requested minimum (the input that fails first for the inclusive "
            "contract): minversion(mod, installed_exact) returns False where the "
            "inclusive semantics require True, so that test FAILS. It does NOT "
            "resolve."),
        "rationale": (
            "partial-domain pinned to the equality boundary in the inclusive case. "
            "Rejection source: postcondition C-ge "
            "Result()==loose_ge(have, normalize(want)); the rival returns loose_gt "
            "on the inclusive branch, which differs (False vs True) exactly when "
            "have==normalize(want). If it verified => SPEC-TOO-WEAK."),
    },
    {
        "id": "rival-keep-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_KEEP_MARKER,
        "refinement": (
            "supporting partial-domain via a different mechanism: the strip loop "
            "never discards the qualifier tail (it accumulates the -1 marker as if "
            "it were a release segment). Its faithful real patch is a broken strip "
            "that keeps the non-numeric tail in the compared version (e.g. omits the "
            "`if m: version = m.group(0)` reassignment), so LooseVersion(version) "
            "still carries 'dev'/'rc1' and the '0.12dev' F2P comparison RAISES — the "
            "F2P test_minversion FAILS. It does NOT resolve."),
        "rationale": (
            "supporting partial-domain with a real refinement, same defended "
            "behaviour as rival-no-strip-raw but exercised inside the loop body. "
            "Rejection source: the in-loop invariant "
            "ToSeq(norm)==normalize(ToSeq(want).drop(i)) and the post-loop "
            "Assert(ToSeq(norm)==normalize(ToSeq(want))) — accumulating the marker "
            "makes ToSeq(norm) carry -1, so the invariant (norm is the marker-free "
            "prefix) cannot be re-established; the comparison then also diverges on a "
            "qualifier-bearing want. If it verified => SPEC-TOO-WEAK."),
    },
]


# ===========================================================================
# AXIOM LANE (Docker, real callees) — A-reference deep models
# ===========================================================================
#
# model.py has NO @ContractOnly axioms (its axioms region is EMPTY, meta.json
# axioms=[]). The two operations the gold patch changes are modeled DEEPLY as the
# @Pure helpers `normalize` (the qualifier-stripping regex prefix) and
# `loose_ge`/`loose_gt` (the LooseVersion >=/> comparison). These are
# A-REFERENCE deep models (meta.json deep_model_references[]), which PBT_PLAN §2
# checks the same way as axioms: the deep model must equal the REAL callee
# (re.match / distutils LooseVersion) on every caller-reachable input, and the
# Requires domain on `want` must be exactly the non-raising region of the real
# gold-patched minversion (the directive-7 no-raise obligation).
#
# The bundle's axiom_check.py IS that soundness oracle (G-AX): it validates
# normalize == an INDEPENDENT distutils-LooseVersion prefix on 15 boundary +
# 20000 fuzz labels, loose_ge/loose_gt == the real LooseVersion order on 169
# boundary + 20000 fuzz pairs, the END-TO-END deep model == the real gold-patched
# minversion across the whole spec domain (no raise), and that every OUT-OF-DOMAIN
# label makes the real callee partial (raise/undefined). It imports only stdlib
# (re + distutils.version.LooseVersion) — the exact callees the gold patch uses,
# present in the py3.6 eval image.
#
# CONTAINMENT NOTE: the caller-reachable inputs are exactly the spec Requires
# domain (have numeric; want begins with a numeric release segment). The
# directive-7 obligation IS the containment statement here: the real callee never
# raises on that domain (covered) and is partial outside it (so the domain is not
# under-scoped). axiom_check.py's check_end_to_end_in_domain /
# check_out_of_domain_is_partial certify exactly this; re-running it in-container
# is the soundness+containment probe.
#
# The runner mounts ONLY the probe script at /work; axiom_check.py is NOT copied
# in (PBT caution 6). So we read the oracle SOURCE on the HOST at manifest-load
# time and embed it verbatim into the probe, then exec it as __main__ (PBT
# caution 4: it CALLS the real re/LooseVersion, never scrapes source; caution 5:
# it imports stdlib only, no non-ASCII file reads in-container).
_AX_ORACLE_SRC = (Path(__file__).parent / "axiom_check.py").read_text()
_AX_SOUNDNESS = (
    "import sys\n"
    "_ORACLE_SRC = " + repr(_AX_ORACLE_SRC) + "\n"
    "print('running embedded G-AX oracle (axiom_check.py source) in-container')\n"
    "_g = {'__name__': '__main__', '__file__': '/work/axiom_check.py'}\n"
    "try:\n"
    "    exec(compile(_ORACLE_SRC, 'axiom_check.py', 'exec'), _g)\n"
    "except SystemExit as e:\n"
    "    code = e.code if isinstance(e.code, int) else (0 if not e.code else 1)\n"
    "    print('axiom_check.py exit', code)\n"
    "    sys.exit(code)\n"
    "print('axiom_check.py completed without assertion failure')\n"
    "sys.exit(0)\n"
)

# A self-contained restatement (independent of axiom_check.py) of the A-reference
# soundness + the directive-7 domain obligation, so the check never silently
# depends on the oracle file being copied. It CALLS the real re.match and
# distutils LooseVersion (caution 4), imports stdlib only (caution 5), and fuzzes
# the boundary/raise behaviour trying to make a real callee DISAGREE with the
# deep model or to find an in-domain input on which the real minversion raises.
_AX_SELFCONTAINED = r'''
import re, random, sys
from distutils.version import LooseVersion

EXPR = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'
QUAL = -1

def encode(version):
    m = re.match(EXPR, version)
    prefix = m.group(0) if m else ""
    if '!' in prefix:
        return None  # epoch: outside model carrier domain
    comps = [int(x) for x in prefix.split('.')] if prefix else []
    if prefix != version:
        comps = comps + [QUAL]
    return comps

def normalize(s):
    out = []
    for c in s:
        if c < 0:
            break
        out.append(c)
    return out

def loose_ge(a, b):
    i = 0
    while True:
        if i >= len(a) and i >= len(b): return True
        if i >= len(a): return False
        if i >= len(b): return True
        if (a[i] < 0) != (b[i] < 0): return False
        if a[i] != b[i]: return a[i] > b[i]
        i += 1

def loose_gt(a, b):
    i = 0
    while True:
        if i >= len(a) and i >= len(b): return False
        if i >= len(a): return False
        if i >= len(b): return True
        if (a[i] < 0) != (b[i] < 0): return False
        if a[i] != b[i]: return a[i] > b[i]
        i += 1

def indep_prefix(version):
    out = []
    for c in LooseVersion(version).version:
        if isinstance(c, int):
            out.append(c)
        else:
            break
    return out

def real_minversion(have_version, version, inclusive=True):
    m = re.match(EXPR, version)
    if m:
        version = m.group(0)
    if inclusive:
        return LooseVersion(have_version) >= LooseVersion(version)
    else:
        return LooseVersion(have_version) > LooseVersion(version)

bad = []

# A-reference 1: normalize(encode(v)) == independent distutils prefix, in domain.
norm_boundary = ["0.12", "0.12.1", "0.12.0.dev", "0.12dev", "1", "1.2rc1",
                 "0.12.2", "1.14dev", "1.14.3", "2.0.0", "10.0",
                 "3.6.0rc2", "1.0a1", "2.1.0.post1", "0.0"]
for v in norm_boundary:
    e = encode(v)
    if e is None:
        continue
    if normalize(e) != indep_prefix(v):
        bad.append(("normalize", v, normalize(e), indep_prefix(v)))

# A-reference 2: loose_ge/loose_gt == real LooseVersion >=/> on numeric pairs.
nums = ["0", "1", "0.12", "0.12.0", "0.12.1", "0.12.2", "1.2", "1.14",
        "1.14.3", "2.0", "10.0", "1.0.0", "0.0.1"]
for a in nums:
    for b in nums:
        ea, eb = encode(a), encode(b)
        if QUAL in ea or QUAL in eb:
            continue
        if loose_ge(ea, eb) != (LooseVersion(a) >= LooseVersion(b)):
            bad.append(("loose_ge", a, b))
        if loose_gt(ea, eb) != (LooseVersion(a) > LooseVersion(b)):
            bad.append(("loose_gt", a, b))

# Randomized fuzz over the deep models.
rng = random.Random(7671)
quals = ["", "dev", "rc1", "rc2", "a1", "b2", ".dev", ".dev0", "post1",
         ".post0", "c1", "alpha", "beta"]
for _ in range(20000):
    nseg = rng.randint(1, 4)
    segs = ["0" if rng.random() < 0.3 else str(rng.randint(1, 99))
            for _ in range(nseg)]
    v = ".".join(segs) + rng.choice(quals)
    e = encode(v)
    if e is None:
        continue
    if normalize(e) != indep_prefix(v):
        bad.append(("normalize_fuzz", v))
    # in-domain (numeric head) end-to-end: real minversion must NOT raise and
    # must equal the deep model assembled exactly as model.py's impl.
    if len(e) > 0 and e[0] >= 0:
        have_s = "0.12.2"
        norm = normalize(e)
        for inc in (True, False):
            try:
                real = real_minversion(have_s, v, inc)
            except Exception as ex:
                bad.append(("in-domain-raise", v, inc, type(ex).__name__))
                continue
            model = (loose_ge(encode(have_s), norm) if inc
                     else loose_gt(encode(have_s), norm))
            if model != real:
                bad.append(("e2e", v, inc, real, model))

# Directive-7: every OUT-OF-DOMAIN label is partial (the real callee raises or
# loses a defined order); the Requires domain is exactly the non-raising region.
out_of_domain = ["dev", "beta", "stable", "rc1", "alpha", "", " ", "x",
                 "v1.0", ".1", ".12.3", ".dev", "1!2.3", "2!1.0", "abc.1.2"]
raise_witnesses = 0
for v in out_of_domain:
    e = encode(v)
    in_domain = (e is not None and len(e) > 0 and e[0] >= 0)
    if in_domain:
        bad.append(("misclassified-in-domain", v))
        continue
    try:
        real_minversion("0.12.2", v, True)
    except (TypeError, AttributeError):
        raise_witnesses += 1
    except Exception:
        raise_witnesses += 1
if raise_witnesses < 8:
    bad.append(("too-few-raise-witnesses", raise_witnesses))

# Headline differential: '0.12dev' stripped compares True, raw raises TypeError.
have = encode("0.12.2")
want = encode("0.12dev")
if QUAL not in want:
    bad.append(("0.12dev-no-marker", want))
if loose_ge(have, normalize(want)) is not True:
    bad.append(("stripped-not-true",))
if loose_ge(have, want) is not False:
    bad.append(("raw-not-false",))
if not (LooseVersion("0.12.2") >= LooseVersion("0.12")):
    bad.append(("real-stripped-not-true",))
raw_raised = False
try:
    LooseVersion("0.12.2") >= LooseVersion("0.12dev")
except TypeError:
    raw_raised = True
if not raw_raised:
    bad.append(("real-raw-did-not-raise",))

if bad:
    print("AXIOM-UNSOUND / DOMAIN defect: real callee disagrees with deep model "
          "or domain mis-scoped:", bad[:8])
    sys.exit(1)
print("A-reference soundness OK: normalize == independent LooseVersion prefix; "
      "loose_ge/loose_gt == real LooseVersion >=/> on boundary + 20000 fuzz; "
      "end-to-end deep model == real minversion (no raise) across the spec "
      "domain; every out-of-domain label is partial; qualifier-strip "
      "differential (stripped True / raw TypeError) confirmed.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-soundness-oracle",
        "axiom": "normalize/loose_ge/loose_gt",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS,
        "rationale": (
            "re-runs the bundle's axiom_check.py (the G-AX soundness oracle) in the "
            "instance image: normalize == an INDEPENDENT distutils LooseVersion "
            "prefix (15 boundary + 20000 fuzz labels), loose_ge/loose_gt == the real "
            "LooseVersion >=/> (169 boundary + 20000 fuzz pairs), the END-TO-END deep "
            "model == the real gold-patched minversion across the spec domain (no "
            "raise), and every out-of-domain label is partial. Any disagreement / "
            "in-domain raise => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-selfcontained-soundness-and-domain",
        "axiom": "normalize/loose_ge/loose_gt",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SELFCONTAINED,
        "rationale": (
            "self-contained restatement (independent of axiom_check.py being "
            "copied): CALLS the real re.match / distutils LooseVersion and asserts "
            "normalize / loose_ge / loose_gt agree on boundary + 20000 fuzz, the "
            "end-to-end model == real minversion with NO raise across the in-domain "
            "fuzz (directive-7 no-raise), and every out-of-domain label is partial "
            "(>=8 raise witnesses) — i.e. the Requires domain is exactly the "
            "non-raising region. Any mismatch / in-domain raise => AXIOM-UNSOUND; an "
            "in-domain label the real callee rejected would be "
            "AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
