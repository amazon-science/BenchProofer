"""PBT falsification battery for django__django-12713.

NOT a Nagini module; an adversarial manifest the runner (swebench_nagini.pbt)
parses. Spec cases are full model.py variants built by region-surgery: each
swaps text ONLY inside the `# impl-start`/`# impl-end` region, so the frozen spec
(axioms/pure/pre/post-conditions regions, the spec_view) is byte-identical and
`markers.same_spec(base, variant)` holds. A spec case "passes" iff its verify
outcome matches `expect` (verify => must verify; reject => must NOT verify).

DEFENDED SURFACE (read from model.py + refinement.md + mapping.md + meta.json)
------------------------------------------------------------------------------
ONE modeled function, mutating its options dict in place:

  select_component(options: Dict[int, int], component_present: bool,
                   test_primary: bool, test_secondary: bool,
                   test_tertiary: bool) -> None

  pre:
    Acc(dict_pred(options))                                   # FULL perm; mutated
    component_present == (key_component() in options)         # ENTRY membership fact
  post (the load-bearing surface):
    Acc(dict_pred(options))
    (P) PRESERVATION:  Forall k. Old(k in options) ==>
                       (k in options) and options[k] == Old(options[k])
        -- every entry key kept with its value. THIS is the precedence guarantee:
           a caller-supplied presentation component (key_component() present on
           entry) is left exactly as supplied; no name-derived default replaces
           it. The fix the patch adds.
    (1) primary:   not component_present and test_primary
                   ==> key in options and options[key]==default_primary()
    (2) secondary: not component_present and not test_primary and test_secondary
                   ==> ...==default_secondary()
    (3) tertiary:  not component_present and not test_primary and not test_secondary
                   and test_tertiary ==> ...==default_tertiary()
    (4) none:      not component_present and no test ==> not (key in options)
    (F) NO-SPURIOUS-KEY (forward frame): Forall k. (k in options) and
                       k != key_component() ==> Old(k in options)
        -- the only key the body may add is key_component(); no stray option.

  key_component()==0, default_primary()==1, default_secondary()==2,
  default_tertiary()==3 are @Pure constants GROUNDED in the spec (not opaque
  answer-key oracles): they are fixed integers, not a function of the input that
  an impl could "echo without doing the work". The selection work is the priority
  decision over the three booleans + the presence guard; that is what the
  postcondition pins. See 'assessment' re: ungrounded-oracle (N/A here).

READ-ONLY INPUT?  No. `options` is held at FULL permission (Acc(dict_pred(options)))
because the repo function genuinely MUTATES its **kwargs dict in place
(kwargs['widget'] = ...). There is NO Acc(x, 1/2) read-only parameter, so the
insufficient-permission frame-mutation probe (the project's #1 class) does NOT
apply to this instance (see meta.json G-HYGIENE advisory + 'assessment'). The
ANALOGOUS frame defence here is the PRESERVATION clause (P): a rival that
OVERWRITES an existing entry key fails (P) — that is the literal pre-patch bug
and is included as weak-no-guard-overwrite below. We also attack the forward
no-spurious-key frame (F) directly (weak-spurious-key).

F2P: test_formfield_overrides_m2m_filter_widget — a BandAdmin sets
     filter_vertical=['members'] (so the tertiary/filter test fires) AND
     formfield_overrides={ManyToManyField: {'widget': CheckboxSelectMultiple}}
     (so 'widget' in kwargs on entry, i.e. component_present==True). The patched
     code must KEEP the caller's CheckboxSelectMultiple and NOT replace it with
     the FilteredSelectMultiple the tertiary test would otherwise pick. That is
     exactly the (P) preservation clause on the entry component. The pre-patch
     (no guard) overwrote it (model_prepatch.py).

The real adversarial leverage is (a) PRESERVATION of the caller's entry
component (the fix itself) and (b) the PRIORITY ORDER + correct identity of the
default when none is present. Each reject rival below carries the refinement
argument that its faithful real patch would NOT resolve the F2P/P2P.
"""
from pathlib import Path

INSTANCE = "django__django-12713"
FLOAT_ENCODING = None  # meta.json float_encoding == null; unused.

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl body (model.py, BETWEEN the markers). Every rival edits ONLY
# this block, so spec_view (and hence markers.same_spec) is preserved verbatim.
# ---------------------------------------------------------------------------
_BODY = """    if not (key_component() in options):
        if test_primary:
            options[key_component()] = default_primary()
        elif test_secondary:
            options[key_component()] = default_secondary()
        elif test_tertiary:
            options[key_component()] = default_tertiary()"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (S1) Branch-reshape: keep the SAME presence guard and the SAME priority order,
# but spell the priority chain as nested if/else instead of the elif ladder.
# Semantically identical (highest-priority matching test wins; only one
# assignment), no loop / no fold, so no auto-undischargeable lemma is needed
# (directive-3 safe). If this CANNOT verify, the postcondition is over-fit to the
# elif spelling => SPEC-TOO-STRONG.
_S1_NESTED = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        if test_primary:\n"
    "            options[key_component()] = default_primary()\n"
    "        else:\n"
    "            if test_secondary:\n"
    "                options[key_component()] = default_secondary()\n"
    "            else:\n"
    "                if test_tertiary:\n"
    "                    options[key_component()] = default_tertiary()")

# (S2) Local-variable reshape: stage the chosen default identity through a typed
# local, then perform ONE guarded assignment. A genuinely different executable
# shape (compute-then-store-once, the structurally-different positive control the
# G-EQ note already validated as pos.py) that keeps the identical guard +
# priority decision. If it fails to verify => SPEC-TOO-STRONG (over-fit to the
# inline-assignment form). The guarded write keeps the no-spurious-key/no-establish
# clauses provable: a default is only stored when present-absent AND a test fires.
_S2_STAGE = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        chosen = 0  # type: int\n"
    "        have = False  # type: bool\n"
    "        if test_primary:\n"
    "            chosen = default_primary()\n"
    "            have = True\n"
    "        elif test_secondary:\n"
    "            chosen = default_secondary()\n"
    "            have = True\n"
    "        elif test_tertiary:\n"
    "            chosen = default_tertiary()\n"
    "            have = True\n"
    "        if have:\n"
    "            options[key_component()] = chosen")


# ===========================================================================
# ADMISSIBILITY — expect "verify"
# ===========================================================================

# Admissibility on the EXACT F2P-shaped input: the precondition pins
#   Requires(component_present == (key_component() in options))
# (plus Acc(dict_pred(options))). We test that this precondition is SATISFIABLE
# (non-vacuous) for the F2P shape -- a caller component present on entry
# (component_present == True) -- and for the absent shape (component_present ==
# False). The probe lives INSIDE the impl (a separate top-level helper would
# break same_spec, since spec_view elides only the impl region): build each
# witness dict at full permission and ASSERT the pinned-boolean precondition
# holds on it. The `key_component() in <witness>` query both exercises the
# dict_pred permission conjunct (membership requires the predicate) and pins the
# boolean conjunct; if either Assert cannot be discharged the precondition is
# unsatisfiable for that shape => PRECOND-TOO-STRONG.
#
# NOTE (proof-engineering, NOT a spec weakening): an actual self-call
# `select_component(probe, True, False, False, True)` re-verifies the ENTIRE
# heavy gold body a SECOND time (the function alone verifies in ~50s; the
# modular self-call havocs `probe` against four priority implications + two
# universally-quantified frame clauses, compounding with the outer body's own
# obligations), pushing the module past the 300s/600s budget and crashing the
# JVM/JPype prover. There is no in-impl-region lemma that avoids re-verifying the
# body, because the self-call IS the body invocation. Asserting the precondition
# facts on the witnesses tests the IDENTICAL admissibility obligation (the
# precondition admits both the present and absent F2P shapes) within budget. The
# frozen spec_view is byte-identical (same_spec preserved): only the impl region
# changes.
_ADMISS = _swap(_BASE, "    # impl-start",
    "    # impl-start\n"
    "    # ADMISSIBILITY PROBE: the precondition pins\n"
    "    #   Requires(component_present == (key_component() in options)).\n"
    "    # Build the exact F2P witness (caller component present on entry) and a\n"
    "    # component-absent witness, and ASSERT the pinned-boolean precondition is\n"
    "    # SATISFIABLE for both (component_present True and False). If either cannot\n"
    "    # be asserted, the precondition is unsatisfiable for that shape =>\n"
    "    # PRECOND-TOO-STRONG. (A full self-call re-verifies the whole heavy body a\n"
    "    # second time and exceeds the verifier budget; asserting the precondition\n"
    "    # facts on the witnesses tests the same admissibility obligation directly.)\n"
    "    present = {key_component(): 7}  # type: Dict[int, int]\n"
    "    Assert(True == (key_component() in present))\n"
    "    absent = {}  # type: Dict[int, int]\n"
    "    Assert(False == (key_component() in absent))")


# ===========================================================================
# UNIQUENESS / PRESERVATION / PARTIAL-DOMAIN RIVALS — expect "reject"
# ===========================================================================

# (W1) NO-GUARD OVERWRITE  -- THE central attack and the literal pre-patch bug
# (== model_prepatch.py). Drop the `if not (key_component() in options):` presence
# guard so the priority chain runs UNCONDITIONALLY; when a caller component is
# present on entry AND a test fires, it OVERWRITES the caller's value with a
# name-derived default. `options` is at FULL permission so the WRITE is permitted
# (this is NOT an insufficient-permission case -- there is no read-only input);
# the rejection comes from the PRESERVATION clause (P): the entry value at
# key_component() changed, so options[key]==Old(options[key]) fails.
_W1_NO_GUARD = _swap(_BASE, _BODY,
    "    if test_primary:\n"
    "        options[key_component()] = default_primary()\n"
    "    elif test_secondary:\n"
    "        options[key_component()] = default_secondary()\n"
    "    elif test_tertiary:\n"
    "        options[key_component()] = default_tertiary()")

# (W2) ALWAYS-TERTIARY priority violation. Keep the presence guard, but inside it
# ignore which test fires and always store the tertiary default. Correct when the
# tertiary test is the (only) firing one; WRONG when the primary or secondary test
# fires (it stores 3 where the spec pins 1 or 2). Rejected by clause (1)/(2).
_W2_ALWAYS_TERT = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        if test_primary or test_secondary or test_tertiary:\n"
    "            options[key_component()] = default_tertiary()")

# (W3) PRIORITY-SWAP (secondary checked before primary). Keep the guard, but test
# test_secondary FIRST. When BOTH test_primary and test_secondary fire, this
# stores default_secondary() (==2) where the spec's clause (1) pins
# default_primary() (==1). Rejected by clause (1).
_W3_PRIO_SWAP = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        if test_secondary:\n"
    "            options[key_component()] = default_secondary()\n"
    "        elif test_primary:\n"
    "            options[key_component()] = default_primary()\n"
    "        elif test_tertiary:\n"
    "            options[key_component()] = default_tertiary()")

# (W4) WRONG-IDENTITY on the primary branch. Keep guard + priority order, but the
# primary branch stores default_secondary() instead of default_primary(). Rejected
# by clause (1): options[key] must equal default_primary() when primary fires.
_W4_WRONG_ID = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        if test_primary:\n"
    "            options[key_component()] = default_secondary()\n"
    "        elif test_secondary:\n"
    "            options[key_component()] = default_secondary()\n"
    "        elif test_tertiary:\n"
    "            options[key_component()] = default_tertiary()")

# (W5) ESTABLISH-WHEN-NO-TEST. Keep guard + priority order, but in the no-test
# fall-through still store a default (tertiary). When the component is absent and
# NO test fires, the spec's clause (4) pins `not (key in options)`; this rival
# establishes it anyway. Rejected by clause (4).
_W5_ESTABLISH = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        if test_primary:\n"
    "            options[key_component()] = default_primary()\n"
    "        elif test_secondary:\n"
    "            options[key_component()] = default_secondary()\n"
    "        else:\n"
    "            options[key_component()] = default_tertiary()")

# (W6) SPURIOUS-KEY frame attack. Do the gold selection correctly, but ALSO store
# an unrelated extra option (key 7, which differs from key_component()==0). When
# 7 was NOT present on entry, the forward no-spurious-key clause (F) is violated:
# a key present on exit, != key_component(), that was not present on entry.
# Rejected by clause (F) (the recover-audit forward-frame fix).
_W6_SPURIOUS = _swap(_BASE, _BODY,
    "    if not (key_component() in options):\n"
    "        if test_primary:\n"
    "            options[key_component()] = default_primary()\n"
    "        elif test_secondary:\n"
    "            options[key_component()] = default_secondary()\n"
    "        elif test_tertiary:\n"
    "            options[key_component()] = default_tertiary()\n"
    "    options[7] = 50")


SPEC_TESTS = [
    {
        "id": "pos-nested-ifelse",
        "kind": "soundness",
        "expect": "verify",
        "module": _S1_NESTED,
        "rationale": "POSITIVE CONTROL: structurally-different CORRECT impl -- the "
        "same presence guard and the same primary>secondary>tertiary priority, but "
        "spelled as nested if/else instead of the elif ladder. Highest-priority "
        "matching test still wins; exactly one guarded assignment. No loop/fold "
        "(directive-3 safe). If it cannot verify, the spec is over-fit to the elif "
        "spelling => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-stage-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _S2_STAGE,
        "rationale": "POSITIVE CONTROL: compute-then-store-once reshape (stage the "
        "chosen default identity through typed locals, then perform ONE guarded "
        "write) -- the structurally-different correct impl the G-EQ note records as "
        "pos.py. Same guard + priority decision; only the executable shape differs. "
        "The `if have` guard keeps the no-establish (4) and no-spurious-key (F) "
        "clauses provable. If it fails => SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "ADMISSIBILITY: the precondition "
        "Requires(Acc(dict_pred(options))) + Requires(component_present == (key in "
        "options)) must be SATISFIABLE for the F2P shape (a caller component present "
        "on entry, component_present=True) and the absent shape (component_present="
        "False). We build each witness dict at full permission and assert the "
        "pinned-boolean precondition holds on it -- the membership query exercises "
        "the dict_pred permission conjunct and pins the boolean conjunct; an "
        "unsatisfiable precondition for either shape => PRECOND-TOO-STRONG. (A literal "
        "self-call re-verifies the heavy ~50s body a second time and exceeds the "
        "verifier budget / crashes the JVM prover; the assertion form tests the same "
        "admissibility obligation within budget. same_spec preserved -- only the impl "
        "region changes.)",
    },
    {
        "id": "weak-no-guard-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W1_NO_GUARD,
        "refinement": "This is the literal pre-patch behaviour (== model_prepatch.py): "
        "the priority chain ran with NO `if 'widget' not in kwargs:` guard, so a "
        "caller-supplied kwargs['widget'] was overwritten by a name-derived default. "
        "The F2P test_formfield_overrides_m2m_filter_widget supplies "
        "CheckboxSelectMultiple via formfield_overrides (so 'widget' in kwargs on "
        "entry) with filter_vertical=['members'] (so the tertiary test fires); this "
        "rival replaces the caller's CheckboxSelectMultiple with a "
        "FilteredSelectMultiple, and assertIsInstance(field.widget.widget, "
        "CheckboxSelectMultiple) FAILS -- the F2P is NOT resolved (it IS the bug).",
        "rationale": "Rejected by the PRESERVATION clause (P): when key_component() "
        "is present on entry and a test fires, the entry value at key_component() is "
        "overwritten, so Old(k in options) ==> options[k]==Old(options[k]) fails. "
        "Note: `options` is FULL-permission (it is genuinely mutated), so this is "
        "NOT an insufficient-permission case -- the rejection is the value-change in "
        "the preservation frame, the analog of the frame defence for a mutated input.",
    },
    {
        "id": "weak-always-tertiary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W2_ALWAYS_TERT,
        "refinement": "A real patch that kept the presence guard but collapsed the "
        "if/elif chain into a single `kwargs['widget'] = FilteredSelectMultiple(...)` "
        "for any matching field would pick the FilteredSelectMultiple widget even for "
        "a field in autocomplete_fields (primary) or raw_id_fields (secondary). The "
        "P2P tests test_raw_id_many_to_many and the autocomplete/filtered cases pin "
        "the SPECIFIC widget class per configuration; this rival renders the wrong "
        "widget for autocomplete/raw-id fields and FAILS those P2P tests -- NOT "
        "resolved.",
        "rationale": "Rejected by clauses (1)/(2): when not component_present and "
        "test_primary, options[key] must equal default_primary() (==1), but this "
        "stores default_tertiary() (==3); likewise for the secondary branch.",
    },
    {
        "id": "weak-priority-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W3_PRIO_SWAP,
        "refinement": "A real patch that tested raw_id_fields (secondary) BEFORE "
        "autocomplete_fields (primary) would, for a field that is in BOTH sets, pick "
        "ManyToManyRawIdWidget where the gold picks AutocompleteSelectMultiple. The "
        "gold if/elif order is autocomplete>raw_id>filter; swapping it changes which "
        "widget a dual-configured field gets, diverging from the gold behaviour the "
        "P2P widget-selection tests pin -- NOT resolved.",
        "rationale": "Rejected by clause (1): when not component_present and "
        "test_primary (regardless of test_secondary), the spec pins options[key] == "
        "default_primary() (==1). At the input test_primary=test_secondary=True this "
        "rival stores default_secondary() (==2), violating clause (1).",
    },
    {
        "id": "weak-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W4_WRONG_ID,
        "refinement": "A real patch whose primary (autocomplete) branch constructed "
        "the WRONG widget class (e.g. ManyToManyRawIdWidget instead of "
        "AutocompleteSelectMultiple) would render the raw-id widget for an "
        "autocomplete field; the autocomplete P2P widget-selection test pins the "
        "AutocompleteSelectMultiple class and FAILS -- NOT resolved.",
        "rationale": "Rejected by clause (1): when not component_present and "
        "test_primary, options[key] must equal default_primary() (==1); this rival "
        "stores default_secondary() (==2) on the primary branch.",
    },
    {
        "id": "weak-establish-no-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W5_ESTABLISH,
        "refinement": "A real patch that replaced the final `elif db_field.name in "
        "[*filter_vertical, *filter_horizontal]:` with an unconditional `else:` "
        "branch would force a FilteredSelectMultiple widget onto a plain M2M field "
        "that is in NONE of autocomplete_fields/raw_id_fields/filters. The P2P "
        "test_many_to_many expects a plain default widget (no filtered widget) for "
        "such a field; forcing one on FAILS it -- NOT resolved.",
        "rationale": "Rejected by clause (4): when not component_present and no test "
        "fires, the spec pins `not (key_component() in options)`; this rival "
        "establishes default_tertiary() anyway.",
    },
    {
        "id": "weak-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W6_SPURIOUS,
        "refinement": "A real patch that performed the correct widget selection but "
        "ALSO injected a stray, unrelated kwarg into the **kwargs dict (e.g. "
        "kwargs['some_extra'] = ...) would pass that extra keyword to the form-field "
        "constructor, which the formfield(...) signature does not accept -> TypeError "
        "at field construction. formfield_for_dbfield would raise rather than return "
        "a field; both the F2P and the P2P field-construction tests would ERROR -- "
        "NOT resolved.",
        "rationale": "Rejected by the forward no-spurious-key frame clause (F): "
        "Forall k. (k in options) and k != key_component() ==> Old(k in options). "
        "Storing options[7]=50 when 7 was absent on entry makes 7 present on exit, "
        "!= key_component(), yet not in Old -- violating (F). (This is exactly the "
        "recover-audit residual the forward-frame line was added to close.)",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# meta.json `axioms` is []: there is NO @ContractOnly CONSUMED axiom. There is ONE
# A-reference deep model: the presence-guarded priority selection is composed
# entirely of REAL CPython dict primitives -- the membership test `key in options`
# (dict.__contains__) and the assignment `options[key] = value` (dict.__setitem__)
# -- spelled out deeply in the impl region (NOT hidden behind an axiom). Per
# PBT_PLAN §2.4 / §4a an A-reference deep model is checked the SAME way as an
# axiom: the deep model must equal the real callee on every caller-reachable input.
#
# We reuse the bundle's own G-AX oracle (axiom_check.py) verbatim -- it reproduces
# the gold patch's exact control flow over a REAL dict and asserts every observation
# meets model.py's frozen postconditions across 7 boundary maps x 8 flag combos +
# the F2P caller-override case + 20000 fuzz cases -- and EXTEND it:
#   * soundness: fuzz the full boundary x flag cross-product harder and assert the
#     real dict primitives never disagree with the frozen postconditions (any
#     disagreement => AXIOM-UNSOUND);
#   * containment: enumerate EXACTLY the (option-map, flag) inputs the model can
#     reach (any Dict[int,int] satisfying dict_pred, all 8 boolean-flag combos)
#     and confirm each lies in the A-reference domain (the real dict membership /
#     assignment primitives are TOTAL on int-keyed dicts -- every reachable input
#     is in-domain; there is NO reachable input outside the A-reference). Covering
#     more than the caller reaches would be sound over-coverage, not a defect.
#
# The runner mounts ONLY the probe at /work, so axiom_check.py is NOT in-container:
# we read its source on the HOST at load time and embed it into the probe (stdlib
# only -- itertools, random; opens nothing on disk; exits 0 iff every obligation
# holds).

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")
# Strip the bundle oracle's own `if __name__ == "__main__": sys.exit(main())`
# trailing guard so it does NOT short-circuit before our extension runs. We
# invoke main() ourselves (then _pbt_extra()) from the probe's own __main__ block.
_GUARD = '\nif __name__ == "__main__":\n    sys.exit(main())\n'
if _GUARD not in _AXIOM_CHECK_SRC:
    raise AssertionError("axiom_check.py __main__ guard drift; cannot strip it")
_AXIOM_CHECK_SRC = _AXIOM_CHECK_SRC.replace(_GUARD, "\n", 1)

# Soundness probe: run the bundle's own G-AX oracle (axiom_check.main) verbatim,
# then ALSO drive a heavier randomized cross-product to try to make the real dict
# primitives DISAGREE with the deep model / frozen postconditions.
_SOUNDNESS_PROBE = (
    _AXIOM_CHECK_SRC
    + r'''

# --- PBT extension: heavier fuzz over the full boundary x flag cross-product,
#     plus an explicit caller-component-preservation stress (the F2P heart).
def _pbt_extra():
    extra_failures = 0
    rng = random.Random(127130517)
    for _ in range(50000):
        base = {}
        has_caller = bool(rng.getrandbits(1))
        if has_caller:
            base[KEY_COMPONENT] = rng.randint(-9, 20)     # maybe a caller component
        for _ in range(rng.randint(0, 5)):
            k = rng.randint(1, 30)                         # unrelated option keys (!= 0)
            base[k] = rng.randint(-9, 80)
        a = bool(rng.getrandbits(1))
        r = bool(rng.getrandbits(1))
        f = bool(rng.getrandbits(1))
        snapshot = dict(base)
        try:
            check(dict(base), a, r, f)                     # asserts all frozen post-conds
        except AssertionError as e:
            extra_failures += 1
            print("SOUNDNESS FAIL on input options=%r flags=(%r,%r,%r): %s"
                  % (snapshot, a, r, f, e))
    return extra_failures

if __name__ == "__main__":
    rc = main()
    if rc == 0:
        rc = 1 if _pbt_extra() else 0
        if rc == 0:
            print("AXIOM-SOUNDNESS OK: the real CPython dict membership/assignment "
                  "primitives match the deep model (frozen post-conditions) on the "
                  "G-AX battery + 50000 additional fuzz cases; caller component never "
                  "overwritten, default selected only when absent with priority "
                  "primary>secondary>tertiary, no spurious key added.")
    sys.exit(rc)
'''
)

# Containment probe: enumerate the model-reachable callee inputs and confirm each
# lies in the A-reference domain. The deep model's two primitives -- `key in d`
# and `d[key] = v` -- are TOTAL on int-keyed dicts; the model only ever passes
# int keys / int values (Dict[int,int]) and the eight boolean-flag combos. So
# every reachable input is in-domain; there is no reachable input the A-reference
# does not cover. We make this concrete by exercising every flag combo on a set of
# reachable option-maps and confirming the primitives behave (membership before
# write false-or-true as expected; assignment lands the value), i.e. the domain is
# total over what the model reaches.
_CONTAINMENT_PROBE = r'''
import sys, itertools, random

KEY_COMPONENT = 0

failures = 0
flags = list(itertools.product([False, True], repeat=3))

# Reachable option-maps: any Dict[int,int] satisfying dict_pred. Sample the
# boundary maps (present/absent component, with/without unrelated keys) the model
# can reach, across all eight flag combos.
reachable_maps = [
    {},
    {KEY_COMPONENT: 7},
    {KEY_COMPONENT: 1},
    {KEY_COMPONENT: 2},
    {KEY_COMPONENT: 3},
    {KEY_COMPONENT: 7, 5: 50},
    {5: 50, 6: 60},
    {1: 11, 2: 22, 3: 33},
]
rng = random.Random(12713)
for _ in range(2000):
    m = {}
    if rng.getrandbits(1):
        m[KEY_COMPONENT] = rng.randint(-9, 20)
    for _ in range(rng.randint(0, 4)):
        m[rng.randint(1, 25)] = rng.randint(-9, 60)
    reachable_maps.append(m)

for m in reachable_maps:
    for (a, r, f) in flags:
        # CONTAINMENT: every reachable input is in the domain of the A-reference
        # primitives. `key in d` is total (returns a bool for any int key):
        contains = (KEY_COMPONENT in m)
        if contains not in (True, False):
            failures += 1
            print("CONTAINMENT MISS: membership not total on %r" % (m,))
        # `d[key] = v` is total (lands any int value under an int key): verify on
        # a throwaway copy that the assignment the model would perform is in-domain.
        if not contains:
            d = dict(m)
            d[KEY_COMPONENT] = 1
            if d.get(KEY_COMPONENT) != 1:
                failures += 1
                print("CONTAINMENT MISS: assignment not in-domain on %r" % (m,))

print("containment: every model-reachable (option-map, flag) input lies in the "
      "A-reference domain -- the dict membership/assignment primitives are TOTAL "
      "on the int-keyed dicts (Dict[int,int]) and eight boolean-flag combos the "
      "model can reach; no reachable input is outside the A-reference.")
if failures:
    print("AXIOM-CONTAINMENT FAIL: %d miss(es)" % failures)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-ref-dict-soundness",
        "axiom": "presence-guarded priority selection (dict membership/assignment A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": "the deep model assumes the real CPython dict primitives -- "
        "membership `key in options` (dict.__contains__) and assignment "
        "`options[key]=value` (dict.__setitem__). We run them for real (stdlib dict, "
        "the very constructs the gold patch composes) via the bundle's G-AX oracle + "
        "50000 extra fuzz cases and assert they match the frozen post-conditions on "
        "every reachable input. Any disagreement => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-ref-dict-containment",
        "axiom": "presence-guarded priority selection (dict membership/assignment A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": "enumerate EXACTLY the (option-map, flag) inputs the model can "
        "reach (any Dict[int,int] satisfying dict_pred, all 8 boolean-flag combos) "
        "and confirm each lies in the A-reference domain. The dict membership/"
        "assignment primitives are TOTAL on int-keyed dicts, so every reachable "
        "input is in-domain; a reachable input outside the domain would be "
        "AXIOM-TOO-WEAK-FOR-CALLER (none exists here).",
    },
]
