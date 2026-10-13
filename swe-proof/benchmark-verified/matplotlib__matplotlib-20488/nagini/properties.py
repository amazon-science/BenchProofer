# properties.py — PBT manifest for matplotlib__matplotlib-20488.
#
# NOT a Nagini module; a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS, writes each
# `module` to a temp file, runs Nagini verify + markers.same_spec against the
# frozen model.py, and stamps RESULT.
#
# DEFENDED SURFACE (reasoned, not corrupted):
#   sanitized_lower_bound(is_log: bool, lower_bound: float, eps: float) -> float
#   Inputs are ALL scalar value types (bool/float/float) passed by value. There
#   is NO Acc(x,1/2) read-only reference input and NO list/object input, so there
#   is NO frame to mutate -> the frame-mutation class is N/A here (see assessment).
#
#   The postcondition is THREE clauses that PARTITION the domain and pin Result()
#   exactly everywhere — it is a GROUNDED, COMPLETE oracle (Result is a function
#   of the args on every input):
#     (P1) Implies(is_log, Result() > 0.0)                      headline guarantee
#     (P2) Implies(is_log and lower_bound <= 0.0, Result()==eps) exact floor
#     (P3) Implies(not(is_log and lower_bound<=0.0), Result()==lower_bound) passthr
#   Because the oracle is fully grounded in the args (eps / lower_bound), there is
#   NO answer-key to echo -> ungrounded-oracle-echo is N/A; instead we ship a
#   cheapest grounded positive control (directive 2 fallback).
#
#   The real bug (prepatch) is the boundary at lower_bound == 0.0: the old guard
#   `if lower_bound < 0.0` MISSES exactly zero, leaving 0.0 fed to LogNorm
#   (ValueError "Invalid vmin or vmax", the F2P failure). The discriminating clause
#   is P1 (with P2 fixing the value). So the high-value attacks here are
#   PARTIAL-DOMAIN rivals at the exact-zero boundary, plus value/overreach rivals
#   that probe whether P2/P3 actually pin the constant and the passthrough.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20488"
FLOAT_ENCODING = "real"   # meta.json float_encoding; the spec is verified with --float-encoding=real

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact frozen impl region of model.py (everything between the markers,
# markers exclusive). We ONLY ever replace text strictly inside this region so
# that markers.same_spec stays True for every spec case.
_IMPL = """    result = lower_bound
    if is_log and lower_bound <= 0.0:
        result = eps
    else:
        # Either not logarithmic, or the candidate is already strictly positive;
        # in the logarithmic branch the result therefore stays positive.
        Assert(Implies(is_log, lower_bound > 0.0))
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(body: str) -> str:
    """Build a full model.py variant by replacing ONLY the impl-region body.
    `body` is the new impl, already indented to 4 spaces (inside the function)."""
    return _swap(_BASE, _IMPL, body)


SPEC_TESTS = [
    # -------------------------------------------------------------------------
    # 5. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
    # Nested-if shape (mirrors the gold guard split into two conditions) with the
    # CORRECT `<= 0.0` boundary, branches reordered (handle non-log first). Keeps
    # the gold proof valid (no induction; pure boolean/real reasoning). MUST verify
    # — else SPEC-TOO-STRONG.
    # -------------------------------------------------------------------------
    {
        "id": "pos-control-nested-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not is_log:\n"
            "        result = lower_bound\n"
            "    else:\n"
            "        if lower_bound <= 0.0:\n"
            "            result = eps\n"
            "        else:\n"
            "            result = lower_bound\n"
            "    return result"
        ),
        "rationale": "a structurally-different (non-log-first, nested) but CORRECT "
                     "impl must satisfy P1/P2/P3; if it cannot verify the "
                     "postcondition is too strong (SPEC-TOO-STRONG). No induction "
                     "lemma needed — pure bool/real reasoning the gold proof uses.",
    },
    # -------------------------------------------------------------------------
    # 2 (fallback). CHEAPEST GROUNDED POSITIVE CONTROL. The oracle is grounded in
    # the args, so there is no wrong echo; the honest minimal impl is a single
    # conditional expression. MUST verify.
    # -------------------------------------------------------------------------
    {
        "id": "pos-control-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    result = eps if (is_log and lower_bound <= 0.0) else lower_bound\n"
            "    return result"
        ),
        "rationale": "the oracle is fully grounded (Result is a function of the "
                     "args), so the cheapest faithful impl is a direct conditional; "
                     "it must verify. This is the directive-2 fallback in place of "
                     "an ungrounded-oracle echo (there is no answer-key to echo).",
    },
    # -------------------------------------------------------------------------
    # 6. ADMISSIBILITY — a self-call on the F2P-shaped input (is_log=True,
    # lower_bound=0.0, eps>0, the exact failing CI case) must establish the
    # Requires and then assert the headline guarantee on the returned value.
    # MUST verify — else PRECOND-TOO-STRONG (the precond would reject a normal
    # input). lower_bound==0.0 satisfies `lower_bound <= 0.0 or lower_bound > 0.0`.
    # -------------------------------------------------------------------------
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    result = lower_bound\n"
            "    if is_log and lower_bound <= 0.0:\n"
            "        result = eps\n"
            "    else:\n"
            "        Assert(Implies(is_log, lower_bound > 0.0))\n"
            "    # admissibility witness: the exact F2P input (LogNorm, vmin==0)\n"
            "    # lies inside the precondition and yields a strictly positive bound.\n"
            "    if is_log and lower_bound == 0.0:\n"
            "        Assert(result == eps)\n"
            "        Assert(result > 0.0)\n"
            "    return result"
        ),
        "rationale": "the precondition must admit the exact CI failure input "
                     "(is_log=True, lower_bound=0.0): 0.0 satisfies "
                     "`lower_bound <= 0.0 or lower_bound > 0.0` and eps>0 is "
                     "establishable. If the call cannot verify, PRECOND-TOO-STRONG.",
    },
    # -------------------------------------------------------------------------
    # 3. PARTIAL-DOMAIN (the real bug) — uses the OLD strict `< 0.0` guard, so it
    # is correct on the entire domain EXCEPT the single point (is_log, lb==0.0):
    # there it passes 0.0 through. expect=reject (fails P1 at lb==0, and P2 which
    # demands result==eps when lb<=0). This is literally the prepatch skeleton.
    # -------------------------------------------------------------------------
    {
        "id": "reject-partial-strict-lt-misses-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = lower_bound\n"
            "    if is_log and lower_bound < 0.0:\n"
            "        result = eps\n"
            "    return result"
        ),
        "refinement": "this IS the pre-patch guard (`< 0` misses exact zero). Its "
                      "faithful real patch leaves s_vmin==0.0 for LogNorm, so "
                      "self.norm(resampled) raises ValueError('Invalid vmin or "
                      "vmax') — exactly test_huge_range_log[png--1] FAILS. It does "
                      "NOT resolve the F2P.",
        "rationale": "violates P1 (Implies(is_log, Result()>0)) and P2 "
                     "(Implies(is_log and lb<=0, Result()==eps)) at lower_bound==0.0; "
                     "if it verified the spec would be SPEC-TOO-WEAK at the boundary.",
    },
    # -------------------------------------------------------------------------
    # 3'. PARTIAL-DOMAIN (G-MUT survivor `>` -> `>=`) — sanitizes only when the
    # candidate is STRICTLY negative `< 0.0` via a `lower_bound >= 0.0` passthrough
    # test, again leaking lb==0.0. Same defect, different surface (the surviving
    # mutant from G-MUT). expect=reject.
    # -------------------------------------------------------------------------
    {
        "id": "reject-partial-ge-zero-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_log and lower_bound >= 0.0:\n"
            "        result = lower_bound\n"
            "    elif is_log:\n"
            "        result = eps\n"
            "    else:\n"
            "        result = lower_bound\n"
            "    return result"
        ),
        "refinement": "the `>= 0.0` passthrough keeps lb==0.0 for LogNorm, so the "
                      "faithful real patch still feeds 0.0 to LogNorm -> ValueError "
                      "-> test_huge_range_log[png--1] FAILS. (This is the G-MUT "
                      "survivor `'>' -> '>='` made explicit.) Does NOT resolve F2P.",
        "rationale": "violates P1 and P2 at lower_bound==0.0 (passes 0.0 through "
                     "instead of eps); a verify here is SPEC-TOO-WEAK at the bug.",
    },
    # -------------------------------------------------------------------------
    # WRONG-CONSTANT (value pin) — sanitizes the right domain but returns a
    # DIFFERENT positive value (eps + 1.0) instead of eps. Satisfies P1 (>0) but
    # VIOLATES P2 (Result()==eps). expect=reject. This proves P2 actually pins the
    # constant, not merely positivity.
    # -------------------------------------------------------------------------
    {
        "id": "reject-wrong-positive-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = lower_bound\n"
            "    if is_log and lower_bound <= 0.0:\n"
            "        result = eps + 1.0\n"
            "    return result"
        ),
        "refinement": "the real patch sets s_vmin = eps (the smallest positive "
                      "magnitude). Returning eps+1.0 hands LogNorm a vmin far above "
                      "the data floor, shifting the normalization so the rendered "
                      "image differs from the Normalize-with-under reference figure "
                      "-> check_figures_equal MISMATCH -> test_huge_range_log[png--1] "
                      "FAILS. Does NOT resolve F2P (it produces a wrong figure).",
        "rationale": "violates P2 (Implies(is_log and lb<=0, Result()==eps)); a "
                     "verify here is SPEC-TOO-WEAK (P2 would not be pinning eps).",
    },
    # -------------------------------------------------------------------------
    # OVERREACH (passthrough pin) — clamps a STRICTLY POSITIVE candidate down to
    # eps in the log branch (sanitizes when it must not). Satisfies P1/P2 but
    # VIOLATES P3 (passthrough: result must equal lower_bound when lb>0). It only
    # fires on is_log and lb>0, a sub-domain P3 governs. expect=reject.
    # -------------------------------------------------------------------------
    {
        "id": "reject-overreach-clamp-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_log and lower_bound <= 0.0:\n"
            "        result = eps\n"
            "    elif is_log:\n"
            "        # WRONG: clamp an already-positive bound down to the floor\n"
            "        result = eps\n"
            "    else:\n"
            "        result = lower_bound\n"
            "    return result"
        ),
        "refinement": "the real patch leaves an already-positive s_vmin UNCHANGED "
                      "(the guard only fires when s_vmin<=0). Forcing s_vmin=eps for "
                      "a positive bound destroys the intended LogNorm vmin (the test "
                      "sets vmin=1), so the rendered figure no longer matches the "
                      "reference -> check_figures_equal MISMATCH -> the F2P (and the "
                      "P2P [png-1] sibling) FAIL. Does NOT resolve.",
        "rationale": "violates P3 (Implies(not(is_log and lb<=0), Result()==lb)) on "
                     "the is_log & lb>0 sub-domain; a verify here is SPEC-TOO-WEAK "
                     "(P3 would not be enforcing passthrough).",
    },
    # -------------------------------------------------------------------------
    # OVERREACH (non-log passthrough pin) — sanitizes in the NON-log branch when
    # lb<=0 (ignores is_log). Satisfies P1 (vacuously, is_log False) but VIOLATES
    # P3 (non-log must pass lower_bound through unchanged). expect=reject. Probes
    # whether is_log actually gates the sanitisation.
    # -------------------------------------------------------------------------
    {
        "id": "reject-overreach-nonlog-sanitizes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = lower_bound\n"
            "    if lower_bound <= 0.0:\n"
            "        # WRONG: drops the is_log gate, sanitizes for ANY norm\n"
            "        result = eps\n"
            "    return result"
        ),
        "refinement": "the real patch sanitizes ONLY when isinstance(norm, LogNorm). "
                      "Replacing a non-log vmin<=0 with eps corrupts a linear/other "
                      "Normalize's lower bound (e.g. the Normalize reference figure "
                      "in the test, vmin=1 untouched but a 0/negative case would be "
                      "clobbered), changing rendered output for non-log norms that "
                      "legitimately accept <=0 -> behaviour diverges from gold. Does "
                      "NOT resolve / regresses non-log norms.",
        "rationale": "violates P3 at is_log=False, lower_bound<=0.0 (returns eps "
                     "instead of lower_bound); a verify here is SPEC-TOO-WEAK (the "
                     "is_log gate in P2/P3 would be unenforced).",
    },
]


AXIOM_TESTS = [
    # -------------------------------------------------------------------------
    # No @ContractOnly axiom is CONSUMED and there are no A-reference deep models
    # (meta.axioms == [], deep_model_references == []). The ONE real-callee fact
    # the spec rests on is GROUNDED via the parameter precondition Requires(eps>0):
    # in the real code `eps` is `np.finfo(scaled_dtype).eps`. We port axiom_check.py
    # as a soundness+containment probe:
    #   * SOUNDNESS: the real callee np.finfo(dtype).eps is strictly positive on
    #     every floating dtype (so Requires(eps>0) is never a false promise).
    #   * CONTAINMENT: the dtypes the caller can actually reach in _make_image are
    #     float32/float64 (the two scaled_dtype picks); both are covered, plus
    #     neighbours (float16/float128) to show coverage is broader-than-reached
    #     (SOUND, float-vs-int rule). A reachable dtype with eps<=0 would be
    #     AXIOM-TOO-WEAK-FOR-CALLER — none exists.
    # The probe imports numpy only (the same library the gold patch calls). It is
    # not strictly Docker-dependent (numpy is in the verifier env too) but is
    # written to run in the instance image where the real callee lives.
    # -------------------------------------------------------------------------
    {
        "id": "ax-floor-positivity-finfo-eps",
        "axiom": "eps_positivity",   # the grounded real-callee fact behind Requires(eps>0.0)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "try:\n"
            "    import numpy as np\n"
            "except Exception as e:\n"
            "    print('cannot import numpy:', e); sys.exit(1)\n"
            "# CONTAINMENT: dtypes the caller (_make_image scaled_dtype) can reach.\n"
            "reached = ['float32', 'float64']\n"
            "# coverage neighbours (broader-than-reached is SOUND).\n"
            "neighbours = ['float16', 'float128']\n"
            "ok = True\n"
            "for name in reached + neighbours:\n"
            "    dt = getattr(np, name, None)\n"
            "    if dt is None:\n"
            "        if name in reached:\n"
            "            print('FAIL: caller-reachable dtype missing:', name); ok = False\n"
            "        else:\n"
            "            print('skip (platform lacks):', name)\n"
            "        continue\n"
            "    eps = float(np.finfo(dt).eps)\n"
            "    print('np.finfo(%s).eps = %r' % (name, eps))\n"
            "    if not (eps > 0.0):\n"
            "        print('FAIL: eps not strictly positive for', name); ok = False\n"
            "if not ok:\n"
            "    sys.exit(1)\n"
            "print('AX-SOUND OK: Requires(eps>0.0) grounded — np.finfo(dtype).eps>0 '\n"
            "      'for every caller-reachable (float32/float64) and neighbour dtype')\n"
            "sys.exit(0)\n"
        ),
        "rationale": "the spec's Requires(eps>0.0) is the abstraction of the real "
                     "constant np.finfo(scaled_dtype).eps. If the real callee could "
                     "produce eps<=0 on a caller-reachable dtype, the precondition "
                     "would be a false promise (AXIOM-UNSOUND / TOO-WEAK-FOR-CALLER). "
                     "Every reachable dtype (float32/float64) yields eps>0; coverage "
                     "extends to neighbours (sound by the float-vs-int rule).",
    },
]
