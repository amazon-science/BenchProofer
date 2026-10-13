# properties.py — PBT falsification battery for matplotlib__matplotlib-23476.
#
# NOT a Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are full model.py variants that share
# the FROZEN spec (markers.same_spec) and swap ONLY the impl region; each is checked
# by re-running the Nagini verifier on the host. There are no @ContractOnly axioms in
# this bundle (axioms region empty; the dict.get-with-default selection is modeled
# DEEPLY), so the axiom lane is the single A-reference deep-model fidelity check,
# carried by the bundle's axiom_check.py — re-exercised here as a containment/soundness
# probe in Docker against real Python dict semantics.
#
# Defended surface (model.py normalize_state_dpi):
#   * state: Dict[int,int] is held at FULL permission Acc(dict_pred(state)) and is
#     GENUINELY MUTATED in place (the dpi entry key_dpi() is
#     reassigned). It is NOT a read-only Acc(...,1/2) input, so the classic
#     half-permission frame-mutation probe (overwrite a read-only arg) does not
#     apply. The analogous attack here is a FRAME-VIOLATION rival that satisfies the
#     dpi-selection clause but ALSO writes some OTHER entry — which the frame Forall
#     postconditions (no key but key_dpi() may change) must reject.
#   * The oracle is GROUNDED: reference_present / reference_value are pinned by the
#     pre-conditions to the genuine entry record of key_reference() at ENTRY
#     (reference_present == (key_reference() in state);
#      Implies(reference_present, reference_value == state[key_reference()])).
#     They are a function of the input, not an opaque answer-key, so there is no
#     ungrounded oracle to echo. (See 'assessment'.) The ungrounded-oracle lane is
#     therefore replaced by an honest cheapest-impl positive control.
#   * Load-bearing discriminating clause:
#       Ensures(Implies(reference_present, state[key_dpi()] == reference_value))
#     This is the gold fix; the pre-patch (pass) impl fails exactly here (G-DIFF).

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23476"
FLOAT_ENCODING = None   # meta.json float_encoding is null (selection is value-agnostic)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl region body (between # impl-start / # impl-end), verbatim.
_GOLD_IMPL = (
    "    if key_reference() in state:\n"
    "        state[key_dpi()] = state[key_reference()]\n"
    "    else:\n"
    "        state[key_dpi()] = state[key_dpi()]"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body: str) -> str:
    """Build a variant by replacing ONLY the gold impl region body. Everything
    outside # impl-start/# impl-end (the frozen spec) is untouched, so same_spec
    holds by construction."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # 1. POSITIVE CONTROL (soundness). Structurally DIFFERENT but CORRECT: the
    #    branch is reordered (test absence first) and the present-branch uses the
    #    grounded parameter reference_value (== state[key_reference()] by the
    #    precondition) instead of re-reading state[key_reference()]. Both are
    #    the same value, so every postcondition clause still holds; only the
    #    executable shape changed. No framing lemma is needed (the spec has no
    #    recursive @Pure fold), so this is a pure-shape reorder that keeps the
    #    gold proof valid.
    {
        "id": "pos-reorder-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not (key_reference() in state):\n"
            "        state[key_dpi()] = state[key_dpi()]\n"
            "    else:\n"
            "        state[key_dpi()] = reference_value"
        ),
        "rationale": "a structurally-different (branch-reordered) but correct impl "
                     "using the grounded reference_value must verify; else SPEC-TOO-STRONG.",
    },

    # 2. ADMISSIBILITY. The gold impl, augmented with an in-region Assert that the
    #    discriminating postcondition holds at exit on a normal F2P-shaped input.
    #    The Assert verifying confirms the precondition ADMITS such an input and
    #    that the body reaches the post-state (else PRECOND-TOO-STRONG). It keeps
    #    the gold body verbatim, so nothing in the proof is dropped.
    {
        "id": "admiss-poststate-reached",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    if key_reference() in state:\n"
            "        state[key_dpi()] = state[key_reference()]\n"
            "    else:\n"
            "        state[key_dpi()] = state[key_dpi()]\n"
            "    Assert(Implies(reference_present, state[key_dpi()] == reference_value))\n"
            "    Assert(key_dpi() in state)"
        ),
        "rationale": "the precondition must admit a normal serialisable-state input "
                     "and let the body establish the selection postcondition; else "
                     "PRECOND-TOO-STRONG.",
    },

    # 3. UNIQUENESS — drop the selection (the literal pre-patch skeleton). Leaves
    #    the dpi entry at its recorded (scaled) value. Must REJECT
    #    on Ensures(Implies(reference_present, state[key_dpi()] == reference_value)):
    #    when a reference entry is present and differs, the recorded value is the
    #    non-reference one.
    {
        "id": "weak-drop-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    pass"),
        "refinement": "this is exactly the pre-patch __getstate__ (no DPI reconciliation). "
                      "Its faithful real patch leaves state['_dpi'] at the scaled value, so "
                      "the F2P test_unpickle_with_device_pixel_ratio sees fig2.dpi == 42*7, "
                      "not 42 — it does NOT resolve.",
        "rationale": "rejection comes from the discriminating postcondition "
                     "Implies(reference_present, state[key_dpi()] == reference_value) "
                     "(the clause G-DIFF / model_prepatch flags).",
    },

    # 4. UNIQUENESS — inverted selection. When the reference entry is present this rival
    #    KEEPS the live value (does the opposite of the fix); when absent it keeps
    #    the live value (correct on that sub-domain). Must REJECT on the present
    #    branch of the discriminating clause.
    {
        "id": "weak-inverted-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if key_reference() in state:\n"
            "        state[key_dpi()] = state[key_dpi()]\n"
            "    else:\n"
            "        state[key_dpi()] = state[key_dpi()]"
        ),
        "refinement": "a patch that keeps state['_dpi'] = state['_dpi'] even when "
                      "'_original_dpi' is present is the un-fixed behaviour for the F2P "
                      "scenario (original present, live scaled): fig2.dpi == 294, not 42 — "
                      "does NOT resolve.",
        "rationale": "rejection from Implies(reference_present, state[key_dpi()] == reference_value): "
                     "the present branch records the live value, not the reference value.",
    },

    # 5. PARTIAL-DOMAIN — unconditional assign to reference_value. Correct on the
    #    present sub-domain (state[key_dpi()] := reference_value satisfies clause 2),
    #    but WRONG on the absent sub-domain: when reference_present is False,
    #    reference_value is unconstrained (the precondition only pins it when present),
    #    so the absent-branch clause Implies(not reference_present,
    #    state[key_dpi()] == Old(state[key_dpi()])) is not provable. Must REJECT.
    {
        "id": "partial-domain-uncond-original",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    state[key_dpi()] = reference_value"),
        "refinement": "a patch that unconditionally writes the 'original' value would, when "
                      "no '_original_dpi' key exists, overwrite '_dpi' with a garbage / default "
                      "value instead of leaving it untouched — corrupting figures that were "
                      "never device-pixel scaled. It diverges from gold on the no-original "
                      "sub-domain (e.g. test_change_dpi / ordinary pickling), so it does NOT "
                      "resolve the full P2P set.",
        "rationale": "rejection from the absent-branch clause "
                     "Implies(not reference_present, state[key_dpi()] == Old(state[key_dpi()])): "
                     "reference_value is only pinned when reference_present, so it cannot stand "
                     "in for the kept value.",
    },

    # 6. FRAME-VIOLATION (the read-only-frame analog for a full-perm mutated input).
    #    This rival does the CORRECT dpi selection (state[key_dpi()] is set to the
    #    grounded reference_value, satisfying the discriminating clause) AND
    #    additionally OVERWRITES the reference entry (key_reference()) with the
    #    LIVE value BEFORE re-recording the dpi entry — so the reference entry
    #    genuinely changes (Old(state[key_reference()]) != state[key_reference()]
    #    whenever the live and reference values differ, e.g. the F2P 294/42 case).
    #    The frame postconditions (no entry other than key_dpi() may change in value)
    #    must REJECT it. The rejection is attributable to the extra write, not to the
    #    dpi selection (the dpi entry ends at reference_value, the gold value).
    #
    #    NOTE: the order matters. The earlier formulation wrote
    #        state[key_dpi()] = state[key_reference()]
    #        state[key_reference()] = state[key_dpi()]
    #    which is a NO-OP on the reference entry (the second line re-reads the value the
    #    first line just copied INTO state[key_dpi()], i.e. the original reference value),
    #    so the final state was observably identical to gold and CORRECTLY verified.
    #    That was a malformed control, not a spec weakness. The corrected rival below
    #    writes the live value into the reference entry FIRST, so it truly changes.
    {
        "id": "frame-violation-writes-reference",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if key_reference() in state:\n"
            "        state[key_reference()] = state[key_dpi()]\n"
            "        state[key_dpi()] = reference_value\n"
            "    else:\n"
            "        state[key_dpi()] = state[key_dpi()]"
        ),
        "refinement": "the real __getstate__ must leave '_original_dpi' (and every entry but "
                      "'_dpi') exactly as it was; a patch that rewrites state['_original_dpi'] to "
                      "the live (scaled) value mutates the serialisable state beyond the fix. It "
                      "destroys the idempotence invariant the issue is about (the next cycle's "
                      "reference would no longer be the true original — fig.dpi would re-scale and "
                      "drift) and changes other pickled state — it does NOT faithfully reproduce "
                      "gold for the F2P scenario.",
        "rationale": "rejection from the frame clause "
                     "Forall(k != key_dpi() and Old(k in state): state[k] == Old(state[k])): "
                     "writing key_reference() = the live value changes an entry other than the "
                     "dpi one whenever live != reference (so the universal clause is unprovable).",
    },

    # 7. FRAME-VIOLATION (membership) — introduces a NEW entry. Does the correct
    #    dpi selection but also adds an entry at a fresh key token (2, distinct from
    #    key_dpi()=0 and key_reference()=1). Must REJECT on the membership frame
    #    clause (no new name may be introduced).
    {
        "id": "frame-violation-adds-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if key_reference() in state:\n"
            "        state[key_dpi()] = state[key_reference()]\n"
            "    else:\n"
            "        state[key_dpi()] = state[key_dpi()]\n"
            "    state[2] = 0"
        ),
        "refinement": "a patch that injects an extra entry into the serialisable state adds a "
                      "spurious key to the pickled dict (beyond the single '_dpi' fix); the real "
                      "__getstate__ adds only the version stamp the gold hunk does not touch here, "
                      "so an extra key is not gold behaviour and would change every figure's "
                      "pickle — it does NOT faithfully reproduce gold.",
        "rationale": "rejection from the membership frame clause "
                     "Forall(k != key_dpi(): (k in state) == Old(k in state)): introducing a new "
                     "key changes membership at k=2.",
    },

    # 8. NON-TERMINATION — a same-spec rival that diverges instead of performing
    #    the selection. Under Nagini's partial-correctness default this satisfies
    #    every value postcondition VACUOUSLY; the spec's Requires(MustTerminate(2))
    #    totality obligation must REJECT it (obligation leak: the loop takes no
    #    unsatisfied obligation). This is the G-PANEL-1 weakness the audit found
    #    before the obligation was added.
    {
        "id": "weak-diverge-no-terminate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    while True:\n        pass"),
        "refinement": "a real __getstate__ that loops forever never returns the state dict, so "
                      "pickling a figure hangs and the F2P round-trip "
                      "test_unpickle_with_device_pixel_ratio never completes — it does NOT "
                      "resolve.",
        "rationale": "rejection from Requires(MustTerminate(2)): the diverging body cannot "
                     "discharge the caller's termination obligation (obligation leak check), "
                     "so vacuous satisfaction of the value postconditions is not enough.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# No @ContractOnly axiom is consumed (meta.axioms == [], axioms region empty). The
# bundle has ONE A-reference: the impl-region deep model reproduces real Python's
# state["_dpi"] = state.get('_original_dpi', state['_dpi']). The bundle ships
# axiom_check.py for exactly this. We embed a self-contained probe (stdlib only)
# that re-runs the A-reference fidelity check in Docker:
#   * axiom-soundness: the deep model agrees with real dict.get-with-default on
#     boundary + sentinel + fuzz states (incl. the F2P 42.0/294.0 values, raise/
#     absent paths, int and float value tokens).
#   * axiom-containment: every callee-input the MODEL can reach (a dict whose
#     key_dpi token is always present — model.py Requires(key_dpi() in state) — and
#     which may or may not contain key_reference) lies in the domain real
#     dict.get handles. We assert the deep model is defined and matches on exactly
#     that reachable shape (key_dpi present; key_reference optional; arbitrary
#     extra keys), and that it never touches a non-'_dpi' entry.
# The probe imports only stdlib, opens nothing, prints a diagnostic, and exits 0
# iff the obligation holds. apply_gold=True so it runs against the post-gold image
# (irrelevant here — the probe needs no repo symbol — but kept consistent).

_AXIOM_PROBE = r'''
import copy
import random
import sys

KEY_DPI = "_dpi"
KEY_ORIGINAL_DPI = "_original_dpi"


def real_getstate_dpi_fix(state):
    # The REAL gold-patch operation verbatim (the line added to Figure.__getstate__).
    state["_dpi"] = state.get('_original_dpi', state['_dpi'])
    return state


def deep_model(state):
    # model.py's deep model normalize_state_dpi selection (key-token refinement).
    if KEY_ORIGINAL_DPI in state:
        state[KEY_DPI] = state[KEY_ORIGINAL_DPI]
    else:
        state[KEY_DPI] = state[KEY_DPI]
    return state


def check(state):
    # Soundness: deep model == real dict.get-with-default; the selected value is
    # exactly state.get('_original_dpi', state['_dpi']); nothing but '_dpi' changes.
    before = copy.deepcopy(state)
    real = real_getstate_dpi_fix(copy.deepcopy(state))
    model = deep_model(copy.deepcopy(state))
    assert real == model, ("deep model != real dict.get on %r: real=%r model=%r"
                           % (before, real, model))
    expected = before.get(KEY_ORIGINAL_DPI, before[KEY_DPI])
    assert model[KEY_DPI] == expected, ("selection wrong on %r: got %r want %r"
                                        % (before, model[KEY_DPI], expected))
    for k in set(before) | set(model):
        if k == KEY_DPI:
            continue
        assert (k in model) == (k in before), "membership of %r changed on %r" % (k, before)
        if k in before:
            assert model[k] == before[k], "value of %r changed on %r" % (k, before)


def main():
    # --- CONTAINMENT: enumerate exactly the callee-input shapes the MODEL can
    # reach. model.py Requires(key_dpi() in state) => '_dpi' ALWAYS present;
    # key_reference (==1) may be present or absent; any number of other entries.
    # real dict.get('_original_dpi', state['_dpi']) is defined on every such dict
    # (state['_dpi'] never KeyErrors because '_dpi' is guaranteed present), so the
    # reachable domain is fully contained in the real callee's domain. We assert
    # the deep model is total + matches on each reachable shape.
    reachable = [
        {"_dpi": 294.0, "_original_dpi": 42.0},                       # original present, scaled (F2P)
        {"_dpi": 42.0, "_original_dpi": 42.0},                        # present, equal
        {"_dpi": 100.0},                                              # original ABSENT (.get default)
        {"_dpi": 294.0, "_original_dpi": 42.0, "_cachedRenderer": None,
         "__mpl_version__": "3.5.2", "stale": True},                  # present + unrelated entries
        {"_dpi": 72.0, "figwidth": 6.4, "figheight": 4.8},            # absent + unrelated entries
        {"_dpi": 200, "_original_dpi": 100},                          # int value tokens
        {"_dpi": 0, "_original_dpi": 0},                              # zero boundary
        {"_dpi": 419430400.0, "_original_dpi": 200.0},                # 21-cycle doubled witness
    ]
    for st in reachable:
        assert KEY_DPI in st, "containment precondition violated: '_dpi' must be present"
        check(st)

    # The model can NEVER reach a state without '_dpi' (Requires(key_dpi() in state)).
    # Confirm that the ONLY way real dict.get would raise is the OUT-OF-DOMAIN shape
    # the model excludes — i.e. domain containment is exact, not over-wide where it
    # would be unsound.
    raised = False
    try:
        real_getstate_dpi_fix({"_original_dpi": 42.0})  # no '_dpi' -> KeyError on default
    except KeyError:
        raised = True
    assert raised, "expected the real callee to require '_dpi'; the model's Requires(key_dpi() in state) is what keeps it in-domain"

    # --- SOUNDNESS fuzz: boundary already covered; randomise value tokens (int &
    # float, incl. raise/absent paths) and extra entries.
    rng = random.Random(23476)
    extra = ["_cachedRenderer", "figwidth", "figheight", "stale",
             "__mpl_version__", "_restore_to_pylab", "dpi_scale_trans"]
    for _ in range(50000):
        st = {"_dpi": rng.choice([rng.randint(0, 10**9), rng.uniform(0.0, 1e9)])}
        if rng.random() < 0.6:
            st[KEY_ORIGINAL_DPI] = rng.choice([rng.randint(0, 10**9), rng.uniform(0.0, 1e9)])
        for k in extra:
            if rng.random() < 0.3:
                st[k] = rng.randint(-1000, 1000)
        check(st)

    # Idempotence witness (the issue's core): after the fix, re-recording original
    # == result and re-applying keeps the original (no re-scaling drift).
    st = {"_dpi": 294.0, "_original_dpi": 42.0}
    fixed = deep_model(copy.deepcopy(st))
    assert fixed["_dpi"] == 42.0
    st2 = {"_dpi": fixed["_dpi"], "_original_dpi": fixed["_dpi"]}
    assert deep_model(copy.deepcopy(st2))["_dpi"] == 42.0

    print("AX OK: deep model == real dict.get('_original_dpi', state['_dpi']); "
          "reachable shapes (=> '_dpi' always present) fully contained; "
          "8 boundary + 50000 fuzz states sound; idempotence holds")
    return 0


sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-deepmodel-soundness",
        "axiom": "normalize_state_dpi (A-reference deep model: dict.get-with-default)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": "the impl-region deep model must equal real Python "
                     "state['_dpi'] = state.get('_original_dpi', state['_dpi']) on every "
                     "boundary/sentinel/fuzz state, touching no other entry; a disagreement "
                     "would make verify ⇏ resolve (AXIOM-UNSOUND).",
    },
    {
        "id": "ax-deepmodel-containment",
        "axiom": "normalize_state_dpi (A-reference deep model: dict.get-with-default)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AXIOM_PROBE,
        "rationale": "every callee-input the model can reach has '_dpi' present "
                     "(model.py Requires(key_dpi() in state)), so state['_dpi'] never "
                     "KeyErrors and the reachable domain is fully inside real dict.get's "
                     "domain; a reachable input outside it would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
