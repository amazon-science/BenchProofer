# properties.py — PBT falsification battery for matplotlib__matplotlib-20826.
#
# NOT a Nagini module: a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec (markers.same_spec) and differ
# ONLY inside the two `# impl-start`/`# impl-end` regions; they are checked by
# re-running the Nagini verifier on the host. Axiom cases are real-callee probes
# run in the instance Docker image.
#
# Defended surface (read model.py):
#   reinit_tick_kw_major / reinit_tick_kw_minor — structurally identical. Each:
#     * INPUT  tick_kw: Dict[int, bool] held at Acc(dict_pred(tick_kw), 1/2)
#              => READ-ONLY (the frame-mutation attack is MANDATORY).
#     * RETURNS a fresh Dict[int, bool].
#     * POST clauses:
#       (1) refreshed_key() in Result() AND
#           Result()[refreshed_key()] == (flag_enabled and selection_covers)
#       (2) PRESERVATION: every other key in tick_kw survives with its value
#       (3) NO-SPURIOUS: every key in Result() other than refreshed_key() was in
#           tick_kw with the same value
#   refreshed_key() is a @Pure constant (0) — fully GROUNDED (not an answer-key
#   oracle); the pinned grid value (flag_enabled and selection_covers) is a pure
#   function of the bool args, fully unfolded. There is NO ungrounded oracle to
#   echo wrongly => the ungrounded-oracle-echo class is N/A here (see assessment);
#   instead we include a grounded cheapest-impl positive control.
#   ONE axiom: dict_carry_over (A-reference), validated by axiom_check.py (G-AX).
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20826"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The two impl regions are byte-identical, so a plain single-occurrence swap is
# ambiguous. We split the source at the minor-function boundary and swap inside
# whichever half(s) a variant targets, guaranteeing we only ever edit text that
# lies INSIDE a `# impl-start`/`# impl-end` region (the spec is never touched).
_SPLIT = "\n\ndef reinit_tick_kw_minor("
assert _BASE.count(_SPLIT) == 1, "function-boundary anchor drifted"
_HEAD, _TAIL = _BASE.split(_SPLIT, 1)   # _HEAD ends with the major func; _TAIL is the minor func body sans the 'def ' line
_TAIL = "\ndef reinit_tick_kw_minor(" + _TAIL  # re-attach a clean header

# Exact gold impl block (identical in both functions).
_GOLD_IMPL = (
    "    # impl-start\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = flag_enabled and selection_covers\n"
    "    return result\n"
    "    # impl-end"
)
assert _HEAD.count(_GOLD_IMPL) == 1, "gold impl not unique in major half"
assert _TAIL.count(_GOLD_IMPL) == 1, "gold impl not unique in minor half"


def _impl(major_block: str, minor_block: str) -> str:
    """Rebuild a full model.py source, replacing the major and minor impl
    regions with the supplied blocks (each must be a full
    `# impl-start ... # impl-end` region, indented 4 spaces). Only impl-region
    text changes => same_spec is preserved by construction."""
    head = _HEAD.replace(_GOLD_IMPL, major_block, 1)
    tail = _TAIL.replace(_GOLD_IMPL, minor_block, 1)
    return head + "\n\ndef reinit_tick_kw_minor(" + tail.split("\ndef reinit_tick_kw_minor(", 1)[1]


def _both(block: str) -> str:
    return _impl(block, block)


# ----------------------------------------------------------------------------
# Impl blocks (each a complete `# impl-start ... # impl-end` region).
# ----------------------------------------------------------------------------

# Positive control 1: grounded cheapest CORRECT impl, structurally reshaped via
# a typed local for the grid value + a reordered (assign-then-copy is impossible
# since we must copy first; instead we bind the value before the copy). Keeps the
# carry-over + grid assignment the proof needs; only the executable shape moves.
_POS_LOCAL = (
    "    # impl-start\n"
    "    gridval = flag_enabled and selection_covers  # type: bool\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = gridval\n"
    "    return result\n"
    "    # impl-end"
)

# Positive control 2: a different correct shape — copy, then unconditionally set
# the grid key from the conjunction written the other way (selection_covers and
# flag_enabled). `and` is commutative on bools so the value is identical; this is
# a genuinely different surface text that must still verify.
_POS_COMMUTE = (
    "    # impl-start\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = selection_covers and flag_enabled\n"
    "    return result\n"
    "    # impl-end"
)

# Admissibility: a positive control that ALSO calls reinit_tick_kw_major on an
# F2P-shaped input (a tick-keyword mapping carrying a non-grid hidden flag) and
# asserts the postcondition holds at the call site — i.e. the precondition
# Acc(dict_pred(tick_kw),1/2) AND MustTerminate(6) are establishable for a normal
# input. We construct the input dict locally and pass full permission (the callee
# only needs 1/2), then read back the result. If the Requires cannot be met for a
# legitimate input the call site fails => PRECOND-TOO-STRONG.
#
# TERMINATION-OBLIGATION HOSTING (why this block is spliced into the MINOR half):
# the spec now carries Requires(MustTerminate(<level>)), and a call is only
# admissible when the CALLER's level is strictly greater than the CALLEE's.
# Levels in model.py are deliberately staggered: dict_carry_over=2, major=6,
# minor=10. Splicing this probe into the MAJOR half made it an unconditional
# major->major SELF-call at one and the same level 6, which can never satisfy
# strictly-greater at any single level — Nagini reported "Obligation leak check
# failed. Callee reinit_tick_kw_major might not take all unsatisfied obligations
# from the caller." That is a property of where the probe is HOSTED, not evidence
# that the precondition is too strong for an F2P-shaped input. Hosting it in the
# MINOR half (level 10) calling major (level 6) leaves the required room, so the
# case still asserts exactly the same claim — major's Requires is establishable
# for a legitimate stored-hidden-flag mapping, and its postcondition holds there
# — with nothing weakened and no case dropped. The call site is straight-line
# (unguarded), so the assertions are genuinely reachable rather than vacuous.
_ADMISS = (
    "    # impl-start\n"
    "    probe = {}  # type: Dict[int, bool]\n"
    "    probe[refreshed_key()] = False\n"
    "    probe[1] = False  # a stored side-hiding visibility flag (tick1On=False)\n"
    "    probe[2] = False  # label1On=False\n"
    "    out = reinit_tick_kw_major(probe, True, True)\n"
    "    Assert(refreshed_key() in out)\n"
    "    Assert(out[refreshed_key()] == (True and True))\n"
    "    Assert(1 in out and out[1] == False)\n"
    "    Assert(2 in out and out[2] == False)\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = flag_enabled and selection_covers\n"
    "    return result\n"
    "    # impl-end"
)

# FRAME-MUTATION (MANDATORY): satisfy clause (1) by WRITING the grid key into the
# read-only input tick_kw and returning it. tick_kw is held at Acc(...,1/2), so
# the write `tick_kw[...] = ...` requires FULL permission the function does not
# have => must be REJECTED for insufficient permission. The gold postconditions
# are kept verbatim; the rejection is attributable solely to the write.
_FRAME_MUT = (
    "    # impl-start\n"
    "    tick_kw[refreshed_key()] = flag_enabled and selection_covers\n"
    "    return tick_kw\n"
    "    # impl-end"
)

# PRESERVATION-DROPPER (= the prepatch behaviour): re-init by EMPTYING the
# mapping (a fresh {} carrying nothing over) then setting only the grid key.
# Satisfies (1) and (3) but DROPS every other stored key => violates clause (2).
_DROP_OTHERS = (
    "    # impl-start\n"
    "    result = {}  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = flag_enabled and selection_covers\n"
    "    return result\n"
    "    # impl-end"
)

# PARTIAL-DOMAIN: pin the grid value using ONLY flag_enabled, ignoring
# selection_covers. Correct on the subdomain where selection_covers is True (or
# flag_enabled is False), but WRONG on the subdomain {flag_enabled=True,
# selection_covers=False}, where the prescribed value is False but this returns
# True. Violates clause (1). A fuzzer that only tried selection_covers=True would
# miss it; the spec must reject it.
_PARTIAL_DOMAIN = (
    "    # impl-start\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = flag_enabled\n"
    "    return result\n"
    "    # impl-end"
)

# VALUE-MASK / SPURIOUS-KEY: carry over the input and set the grid key correctly,
# but ALSO introduce a spurious entry not present on entry. Satisfies (1) and (2)
# but violates clause (3) (no-spurious): the extra key 7 is in Result() but
# (generally) not in tick_kw. Models a re-init that injects an appearance entry
# the caller never stored.
_SPURIOUS = (
    "    # impl-start\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = flag_enabled and selection_covers\n"
    "    result[7] = True\n"
    "    return result\n"
    "    # impl-end"
)

# WRONG-CONJUNCTION (supporting near-miss): set the grid key to an OR instead of
# the prescribed AND. Wrong whenever exactly one flag is set. Violates clause (1).
_WRONG_OR = (
    "    # impl-start\n"
    "    result = dict_carry_over(tick_kw)  # type: Dict[int, bool]\n"
    "    result[refreshed_key()] = flag_enabled or selection_covers\n"
    "    return result\n"
    "    # impl-end"
)


SPEC_TESTS = [
    # ---- POSITIVE CONTROLS (soundness): must verify ----
    {
        "id": "pos-local-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _both(_POS_LOCAL),
        "rationale": "structurally-different but CORRECT: the prescribed grid "
                     "value is bound to a typed local before the carry-over and "
                     "assigned from it. Keeps the carry-over + grid-key assignment "
                     "the proof of clauses (1)/(2)/(3) needs. Must verify, else "
                     "SPEC-TOO-STRONG (a faithful correct shape rejected).",
    },
    {
        "id": "pos-commuted-and",
        "kind": "soundness",
        "expect": "verify",
        "module": _both(_POS_COMMUTE),
        "rationale": "different surface text (selection_covers and flag_enabled) "
                     "with identical boolean value; the carry-over is unchanged. "
                     "Must verify (and is the commuted form of clause (1)).",
    },
    # ---- ADMISSIBILITY: must verify ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_GOLD_IMPL, _ADMISS),
        "rationale": "calls reinit_tick_kw_major on an F2P-shaped mapping "
                     "({grid:False, tick1On:False, label1On:False}, flags True/True) "
                     "and asserts the postcondition at the call site. The "
                     "Requires — Acc(dict_pred(tick_kw),1/2) AND MustTerminate(6) — "
                     "must be establishable for a normal input, else "
                     "PRECOND-TOO-STRONG. HOSTED IN THE MINOR half (level 10) so the "
                     "caller's obligation level is strictly greater than major's (6), "
                     "which a major->major self-call at the same level could never "
                     "satisfy; the major func keeps the gold impl. Same claim, nothing "
                     "weakened — see the _ADMISS comment for the level arithmetic.",
    },
    # ---- FRAME-MUTATION (MANDATORY, read-only input): must reject ----
    {
        "id": "frame-mutation-write-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _both(_FRAME_MUT),
        "refinement": "Its faithful real patch would write gridOn into the SAME "
                      "self._<which>_tick_kw object and hand that same object back. "
                      "In matplotlib the dict is shared/aliased and re-init must "
                      "preserve the OTHER stored keys; this skeleton trivially "
                      "preserves them (it never copies) but the model forbids "
                      "observing the input mutated (Acc(...,1/2)). A model that "
                      "could verify by writing the read-only input would no longer "
                      "guarantee the result is a related-but-distinct mapping; the "
                      "frame condition (directive 5) is exactly the guard that the "
                      "spec does not silently permit in-place mutation it never "
                      "accounted for.",
        "rationale": "tick_kw is held at Acc(dict_pred(tick_kw),1/2); the write "
                     "tick_kw[refreshed_key()]=... needs FULL permission. REJECT "
                     "comes from the permission system (insufficient permission to "
                     "mutate the read-only input). #1 weakness class.",
    },
    # ---- UNIQUENESS / partial-domain / value-mask / preservation ----
    {
        "id": "drop-other-keys-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _both(_DROP_OTHERS),
        "refinement": "This IS the pre-patch behaviour (_reset_*_tick_kw: "
                      "self._<which>_tick_kw.clear() then set only gridOn). Its "
                      "faithful real patch drops the inner shared-axis side-hiding "
                      "tick*On/label*On keys on ax.clear(), so test_shared_axes_clear "
                      "would FAIL (hidden ticks/labels reappear). Does NOT resolve.",
        "rationale": "fresh {} carries nothing over; violates clause (2) "
                     "(preservation) for every non-grid key. REJECT from "
                     "postcondition clause (2).",
    },
    {
        "id": "partial-domain-ignore-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _both(_PARTIAL_DOMAIN),
        "refinement": "Sets gridOn = mpl.rcParams['axes.grid'] only, ignoring the "
                      "which-selection membership. On the subdomain grid-enabled "
                      "but which-selection NOT covering this class (e.g. axes.grid "
                      "True, axes.grid.which='minor' for the MAJOR axis) it turns "
                      "gridOn on when it must be off — a rendered grid that should "
                      "be absent. The F2P/P2P render-equality tests would diverge.",
        "rationale": "clause (1): Result()[refreshed_key()] must equal "
                     "(flag_enabled and selection_covers); returning flag_enabled "
                     "is wrong on {flag_enabled=True, selection_covers=False}. "
                     "REJECT from clause (1).",
    },
    {
        "id": "spurious-extra-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _both(_SPURIOUS),
        "refinement": "Injects an appearance entry (key 7) the caller never "
                      "stored. Its faithful real patch would add a tick-keyword "
                      "the consumer (_get_tick, **tick_kw) never expected, changing "
                      "the rendered tick and diverging from the gold image.",
        "rationale": "clause (3) (no-spurious): a key in Result() other than "
                     "refreshed_key() must have been in tick_kw with the same "
                     "value; key 7 (generally) was not. REJECT from clause (3).",
    },
    {
        "id": "wrong-conjunction-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _both(_WRONG_OR),
        "refinement": "gridOn = grid OR which-covers instead of AND: turns the "
                      "grid on when only one config flag holds (e.g. axes.grid "
                      "False but which='both'), rendering a grid the gold leaves "
                      "off. Diverges on the F2P/P2P render-equality tests.",
        "rationale": "supporting near-miss; clause (1) demands the AND, so OR is "
                     "wrong whenever exactly one flag is set. REJECT from clause (1).",
    },
]


# ----------------------------------------------------------------------------
# AXIOM lane — dict_carry_over (A-reference). Reuse axiom_check.py's executable
# soundness logic (read it on the HOST at load time and embed into the probe;
# the runner mounts ONLY the probe script in-container).
# ----------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# axiom-soundness probe: run the REAL mapping-copy primitive (dict(d)) and assert
# the axiom's Ensures (both equivalence directions + freshness) on boundary +
# 20000 fuzz mappings, AND validate the end-to-end fixed re-init against the
# modelled postconditions. This is exactly axiom_check.py's logic; we embed and
# run it. dict_carry_over has NO flag_dependency (a language primitive,
# config-independent), so no runtime-config gating is needed.
_AX_SOUND_PROBE = (
    "import sys\n"
    "# Embedded axiom_check.py (the bundle's G-AX oracle). The runner mounts only\n"
    "# this probe in-container, so axiom_check.py is read on the HOST and inlined.\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__embedded__'}\n"
    "exec(compile(_SRC, 'axiom_check_embedded.py', 'exec'), g)\n"
    "try:\n"
    "    rc = g['main']()\n"
    "except AssertionError as e:\n"
    "    print('AXIOM-UNSOUND: dict_carry_over disagreed with real dict():', e)\n"
    "    sys.exit(1)\n"
    "if rc not in (0, None):\n"
    "    print('axiom_check main() returned', rc)\n"
    "    sys.exit(1)\n"
    "print('axiom-soundness OK: real dict() satisfies dict_carry_over Ensures on '\n"
    "      'boundary + 20000 fuzz; fixed re-init matches modelled postconditions.')\n"
    "sys.exit(0)\n"
)

# axiom-containment probe: enumerate EXACTLY the callee-inputs the MODEL can pass
# to dict_carry_over and assert each lies in the axiom's Requires domain. The
# model calls dict_carry_over(tick_kw) where tick_kw: Dict[int, bool] held at
# Acc(dict_pred(tick_kw),1/2) — i.e. ANY well-formed int->bool mapping with read
# access. The axiom's Requires is exactly Acc(dict_pred(d),1/2) over
# Dict[int,bool] — no value/key restriction. So every reachable input (any
# int-keyed bool dict, including empty and the side-hiding-flag mixtures) is in
# the axiom domain; covering more would be sound, not a defect. We exercise the
# real callee over the full reachable shape to confirm it accepts each and that
# no caller-reachable input lies outside the axiom domain.
_AX_COVER_PROBE = (
    "import sys, random\n"
    "rng = random.Random(2026)\n"
    "# The model's only call is dict_carry_over(tick_kw) with tick_kw a\n"
    "# Dict[int, bool]. The axiom Requires(Acc(dict_pred(d),1/2)) over Dict[int,bool]\n"
    "# places NO restriction on keys/values beyond the type+read-permission. So the\n"
    "# set of caller-reachable inputs == {all int->bool mappings}, which the axiom\n"
    "# domain contains exactly. Confirm the real primitive accepts every reachable\n"
    "# shape (empty, grid-only, hidden-flag mixtures, large) and stays in-domain.\n"
    "def in_axiom_domain(d):\n"
    "    # well-formed int-keyed bool mapping == the axiom's Dict[int,bool] domain\n"
    "    return isinstance(d, dict) and all(isinstance(k, int) and isinstance(v, bool)\n"
    "                                       for k, v in d.items())\n"
    "reachable = [\n"
    "    {}, {0: True}, {0: False}, {1: False}, {1: False, 2: False},\n"
    "    {0: True, 1: False, 2: False}, {0: False, 1: True, 2: False, 3: True},\n"
    "]\n"
    "for _ in range(5000):\n"
    "    n = rng.randint(0, 8)\n"
    "    keys = rng.sample(range(0, 12), n)\n"
    "    reachable.append({k: bool(rng.getrandbits(1)) for k in keys})\n"
    "for d in reachable:\n"
    "    assert in_axiom_domain(d), ('reachable input OUTSIDE axiom domain', d)\n"
    "    r = dict(d)  # the real callee accepts every reachable input\n"
    "    assert r == d and r is not d\n"
    "print('axiom-containment OK: every caller-reachable dict_carry_over input '\n"
    "      '(int->bool mapping) lies in the axiom Requires domain; real callee accepts each.')\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-dict-carry-over",
        "axiom": "dict_carry_over",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "If the real mapping-copy primitive dict(d) ever violated the "
                     "axiom's Ensures (both key/value equivalence directions + "
                     "freshness) on a caller-reachable input, AXIOM-UNSOUND. dict() "
                     "is config-independent (no flag_dependency).",
    },
    {
        "id": "ax-cover-dict-carry-over",
        "axiom": "dict_carry_over",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "Every input the model can pass (any Dict[int,bool] under "
                     "Acc(...,1/2)) lies in the axiom's Requires domain (which "
                     "restricts only type+read-permission). A reachable input "
                     "outside it would be AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
