# properties.py — PBT falsification battery for sympy__sympy-20590.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by region-surgery: we edit
# ONLY text inside a # impl-start/# impl-end region, so the frozen spec view
# (axioms/pure/pre/post-conditions + signatures) is byte-identical and
# markers.same_spec holds for every case. AXIOM_TESTS probe the single
# A-reference deep model (the CPython __slots__ -> __dict__/AttributeError rule)
# against the real interpreter in-container.
#
# === The defended surface (adversarial read) ===
# Four modeled functions; ALL inputs are pure `PSeq[bool]` value sequences with
# NO heap permission (the pre-condition comment says so explicitly) -> there is
# NO Acc(...,1/2) read-only heap input anywhere, hence NO frame-mutation attack
# surface (PSeq is immutable; there is nothing to overwrite). has_readonly_input
# is False and that is honest, not an omission.
#
# The load-bearing general contract is bind_undeclared_attribute(chain):
#     Ensures(instance_admits_namespace(chain))   # = not all_closed_layout(chain)
#     Ensures(Result() is True)
#     Exsures(AttributeBindingRefused, all_closed_layout(chain))
# i.e. NORMAL return is admitted ONLY on an open-namespace (not all-closed)
# chain; a refusal (AttributeBindingRefused) carries all_closed_layout(chain).
# The discrimination anchor for the F2P (refinement.md §D) is
# trait_pins_closed_layout()'s constant Ensures(Result() is True): it verifies
# only for the impl that returns the closed-layout flag (= the gold __slots__=()).
#
# The @Pure helpers in the postcondition (all_closed_layout / instance_admits_
# namespace) are GROUNDED in the input `chain` and fully front-recursively
# unfolded — they are NOT an opaque answer-key oracle the impl could echo
# without doing the work. So the ungrounded-oracle-echo class does not apply;
# its slot is replaced by an honest cheapest-impl positive control (pos-control-
# bind). See 'assessment'.
#
# TERMINATION (P1 repair): every modelled function carries a MustTerminate
# obligation (measures 1/2/3 along the call chain). Without it Nagini's
# partial-correctness semantics admitted a diverging same-spec rival (the
# audit's P1 witness): an Invariant(True) infinite loop satisfies every
# Ensures vacuously. The reject-diverge-* cases below pin that class closed.

from pathlib import Path

INSTANCE = "sympy__sympy-20590"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region of bind_undeclared_attribute (the only impl with no proof
# scaffolding — just the branch). Editing here keeps same_spec by construction.
_GOLD_BIND_IMPL = (
    "    # impl-start\n"
    "    if all_closed_layout(chain):\n"
    "        raise AttributeBindingRefused()\n"
    "    return True\n"
    "    # impl-end"
)

# The gold impl region of trait_pins_closed_layout (the F2P discrimination
# anchor, refinement.md §D).
_GOLD_TRAIT_IMPL = (
    "    # impl-start\n"
    "    return True\n"
    "    # impl-end"
)


# === REJECT 1 — inverted branch (partial/whole-domain wrong) ================
# Flip the namespace decision: refuse on the OPEN-namespace chain and SUCCEED on
# the all-closed chain. On an all-closed chain it returns True, violating
# Ensures(instance_admits_namespace(chain)) (which is False there); on an open
# chain it raises, violating Exsures(... all_closed_layout(chain)). Either side
# rejects. This is the canonical "spec admits a wrong impl?" probe for the
# load-bearing general contract.
_REJECT_INVERT = _swap(
    _BASE, _GOLD_BIND_IMPL,
    "    # impl-start\n"
    "    if all_closed_layout(chain):\n"
    "        return True\n"
    "    raise AttributeBindingRefused()\n"
    "    # impl-end",
)

# === REJECT 2 — always return True (prepatch-style binding-succeeds bug) =====
# The exact shape of the reported regression: binding an undeclared attribute
# always succeeds. On an all-closed chain (the Basic chain) this returns True,
# violating Ensures(instance_admits_namespace(chain)) == False there. A faithful
# real patch with this behaviour (Basic() accepts b1.x = 1) does NOT resolve
# test_immutable.
_REJECT_ALWAYS_TRUE = _swap(
    _BASE, _GOLD_BIND_IMPL,
    "    # impl-start\n"
    "    return True\n"
    "    # impl-end",
)

# === REJECT 3 — always raise (over-refusal) =================================
# Binding ALWAYS refused, even on an open-namespace chain. The Exsures condition
# all_closed_layout(chain) is False on an open chain, so the raise is not
# admitted there -> reject. A faithful real patch that raises AttributeError on
# EVERY undeclared assignment (even for classes that legitimately keep a
# __dict__) would break PASS_TO_PASS code that relies on dynamic attributes on
# open-layout classes, so it would not be a correct fix.
_REJECT_ALWAYS_RAISE = _swap(
    _BASE, _GOLD_BIND_IMPL,
    "    # impl-start\n"
    "    raise AttributeBindingRefused()\n"
    "    # impl-end",
)

# === REJECT 4 — empty-chain partial-domain miss =============================
# Correct on every NON-empty chain but wrong on the empty boundary: returns True
# when len(chain)==0. all_closed_layout(empty)==True so instance_admits_namespace
# (empty)==False; returning True there violates Ensures(instance_admits_namespace
# (chain)). This is the partial-domain attack: a rival that diverges only on the
# first/degenerate input class. Its faithful real patch — a closed-layout
# instance with an EMPTY MRO-minus-object (the object-only / pure-mixin case)
# that still accepts an undeclared attribute — would not resolve the immutability
# requirement on that layout.
_REJECT_EMPTY_DOMAIN = _swap(
    _BASE, _GOLD_BIND_IMPL,
    "    # impl-start\n"
    "    if len(chain) == 0:\n"
    "        return True\n"
    "    if all_closed_layout(chain):\n"
    "        raise AttributeBindingRefused()\n"
    "    return True\n"
    "    # impl-end",
)

# === REJECT 5 — trait flag flipped to False (mirrors model_prepatch) ========
# The F2P discrimination anchor. Returning False from trait_pins_closed_layout
# violates its Ensures(Result() is True). This is exactly model_prepatch's
# regression (Printable without __slots__): Basic instances acquire a __dict__
# and test_immutable fails. Supporting case grounding refinement.md §D.
_REJECT_TRAIT_FALSE = _swap(
    _BASE, _GOLD_TRAIT_IMPL,
    "    # impl-start\n"
    "    return False\n"
    "    # impl-end",
)

# === REJECT 6 — diverging bind (vacuous partial-correctness pass) ===========
# Nagini is a partial-correctness verifier: without a termination obligation an
# infinite loop before the branch satisfies every Ensures/Exsures vacuously.
# This was the audit's P1 witness class (a same-spec impl that VERIFIED under
# the pre-fix contract). The MustTerminate(1) precondition now rejects it: the
# loop takes no termination measure, so Nagini reports an obligation leak.
_REJECT_DIVERGE_BIND = _swap(
    _BASE, _GOLD_BIND_IMPL,
    "    # impl-start\n"
    "    b = True\n"
    "    while b:\n"
    "        Invariant(True)\n"
    "        b = True\n"
    "    if all_closed_layout(chain):\n"
    "        raise AttributeBindingRefused()\n"
    "    return True\n"
    "    # impl-end",
)

# === REJECT 7 — diverging trait read (vacuous discrimination anchor) =========
# Same vacuity attack aimed at the F2P discrimination anchor: spin forever
# before returning the closed-layout flag. Under the pre-fix contract this
# verified (Ensures(Result() is True) held vacuously) although the flag is
# never delivered. Rejected by MustTerminate(2).
_REJECT_DIVERGE_TRAIT = _swap(
    _BASE, _GOLD_TRAIT_IMPL,
    "    # impl-start\n"
    "    b = True\n"
    "    while b:\n"
    "        Invariant(True)\n"
    "        b = True\n"
    "    return True\n"
    "    # impl-end",
)

# === VERIFY 1 — positive control: structurally-different CORRECT bind =======
# Reorder the branch and route through the named namespace predicate instead of
# the bare conjunction: compute `admits = instance_admits_namespace(chain)`
# (== not all_closed_layout(chain)), return True on the open case, raise on the
# closed case. Logically identical to gold, different executable shape; it keeps
# every proof obligation (no scaffolding to drop in THIS impl region). MUST
# verify, else SPEC-TOO-STRONG.
_VERIFY_POS_BIND = _swap(
    _BASE, _GOLD_BIND_IMPL,
    "    # impl-start\n"
    "    admits = instance_admits_namespace(chain)\n"
    "    if admits:\n"
    "        return True\n"
    "    raise AttributeBindingRefused()\n"
    "    # impl-end",
)

# === VERIFY 2 — admissibility: the precondition admits an F2P-shaped input ===
# A self-call caller proving the normal-return path of the load-bearing contract
# is LIVE (not vacuous) for an open-namespace chain: build an open chain
# (contains a False), call bind_undeclared_attribute, assert it returns True. The
# Exsures condition all_closed_layout(open) is False so the verifier knows the
# call cannot raise; Ensures(instance_admits_namespace(open)) holds. If this
# cannot verify the precondition would be too strong / the success path dead.
# We add this caller INSIDE trait_pins_closed_layout's impl region (which has no
# scaffolding) so the spec view is untouched; we keep its `return True`.
# Nagini will not auto-unfold the front-recursive @Pure all_closed_layout on a
# literal PSeq, so we supply the same one-step .drop() unfold facts that
# model.py's own core_expression_* impls use (a proof-engineering scaffold, NOT
# a spec change): all_closed_layout(PSeq(True,False)) reduces via its tail
# PSeq(False) whose head is False.
_VERIFY_ADMISS = _swap(
    _BASE, _GOLD_TRAIT_IMPL,
    "    # impl-start\n"
    "    open_chain = PSeq(True, False)  # type: PSeq[bool]\n"
    "    # Unfold the front-recursive @Pure all_closed_layout one step, exactly as\n"
    "    # model.py's own core_expression_* impls do via .drop() ladders. Nagini\n"
    "    # does not auto-unfold the recursive fold, so we supply the drop facts:\n"
    "    # all_closed_layout(PSeq(True,False)) = True and all_closed_layout(PSeq(False))\n"
    "    # and all_closed_layout(PSeq(False)) = False (head False), so the chain is open.\n"
    "    tail = open_chain.drop(1)  # type: PSeq[bool]\n"
    "    Assert(len(tail) == 1)\n"
    "    Assert(tail[0] is False)\n"
    "    Assert(not all_closed_layout(tail))\n"
    "    Assert(open_chain[0] is True)\n"
    "    Assert(not all_closed_layout(open_chain))\n"
    "    res = bind_undeclared_attribute(open_chain)\n"
    "    Assert(res is True)\n"
    "    return True\n"
    "    # impl-end",
)


SPEC_TESTS = [
    {
        "id": "reject-invert-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_INVERT,
        "refinement": (
            "Inverts the namespace decision: succeeds binding on the all-closed "
            "(Basic) chain and refuses on open chains. A faithful real patch with "
            "this behaviour lets Basic() accept b1.x = 1 (binding succeeds where it "
            "must raise), so test_immutable's `with raises(AttributeError): b1.x=1` "
            "fails -> does NOT resolve the F2P."
        ),
        "rationale": (
            "Rejected by Ensures(instance_admits_namespace(chain)) (False on the "
            "all-closed chain, so a normal True return is inadmissible) and by "
            "Exsures(AttributeBindingRefused, all_closed_layout(chain)) (False on an "
            "open chain, so the raise is inadmissible there)."
        ),
    },
    {
        "id": "reject-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_ALWAYS_TRUE,
        "refinement": (
            "Binding always succeeds — the exact reported regression. Its faithful "
            "real patch is Basic() keeping an open __dict__ (Printable without "
            "__slots__): `not hasattr(b1,'__dict__')` is False and `b1.x = 1` does "
            "not raise, so test_immutable fails -> does NOT resolve the F2P."
        ),
        "rationale": (
            "Rejected by Ensures(instance_admits_namespace(chain)): on the all-closed "
            "chain instance_admits_namespace is False, so a normal True return is "
            "inadmissible (Nagini cannot establish the normal postcondition)."
        ),
    },
    {
        "id": "reject-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_ALWAYS_RAISE,
        "refinement": (
            "Binding is always refused, even on open-namespace chains. A faithful "
            "real patch that raises AttributeError on every undeclared assignment "
            "regardless of layout breaks normal dynamic-attribute use on classes "
            "that legitimately keep a __dict__ (PASS_TO_PASS object behaviour), so "
            "it is not a correct fix and would regress other tests."
        ),
        "rationale": (
            "Rejected by Exsures(AttributeBindingRefused, all_closed_layout(chain)): "
            "on an open chain all_closed_layout is False, so the raise carries an "
            "unsatisfiable exceptional postcondition -> the Exsures cannot be "
            "established for the open case."
        ),
    },
    {
        "id": "reject-empty-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_EMPTY_DOMAIN,
        "refinement": (
            "Correct on every non-empty chain but returns True (binding succeeds) on "
            "the empty chain. Its faithful real patch lets a closed-layout instance "
            "whose MRO-minus-object is empty (an object-only / fully-pinned layout) "
            "still accept an undeclared attribute, contradicting the immutability the "
            "F2P pins -> does NOT resolve the empty/degenerate boundary."
        ),
        "rationale": (
            "Partial-domain miss rejected by Ensures(instance_admits_namespace(chain)): "
            "all_closed_layout(empty) is True so instance_admits_namespace(empty) is "
            "False, making a normal True return on the empty chain inadmissible."
        ),
    },
    {
        "id": "reject-trait-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_TRAIT_FALSE,
        "refinement": (
            "Flips the F2P discrimination anchor: the contributing type leaves its "
            "layout open. This is model_prepatch verbatim (Printable without "
            "__slots__): Basic instances acquire a __dict__, so `not hasattr(b1,"
            "'__dict__')` is False -> test_immutable fails -> does NOT resolve."
        ),
        "rationale": (
            "Rejected by trait_pins_closed_layout's constant Ensures(Result() is "
            "True); returning False cannot satisfy it. (Refinement.md §D: this is the "
            "load-bearing soundness anchor for the whole F2P.)"
        ),
    },
    {
        "id": "reject-diverge-bind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_DIVERGE_BIND,
        "refinement": (
            "Spins forever before the correct branch. A faithful real patch whose "
            "attribute-binding step hangs never raises AttributeError and never "
            "stores: `with raises(AttributeError): b1.x = 1` blocks forever, so "
            "test_immutable (and every P2P touching attribute assignment) times "
            "out -> does NOT resolve the F2P."
        ),
        "rationale": (
            "Rejected by the MustTerminate(1) termination obligation in "
            "bind_undeclared_attribute's preconditions: the loop takes no "
            "termination measure, so Nagini reports an obligation leak ('Loop "
            "might not take all unsatisfied obligations from the context'). "
            "Without MustTerminate this rival VERIFIED — the audit's P1 hole."
        ),
    },
    {
        "id": "reject-diverge-trait",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_DIVERGE_TRAIT,
        "refinement": (
            "Spins forever before delivering the closed-layout flag — the F2P "
            "discrimination anchor never completes. A faithful real patch whose "
            "class construction/declaration hangs never even imports sympy.core, "
            "so test_immutable cannot run -> does NOT resolve."
        ),
        "rationale": (
            "Rejected by the MustTerminate(2) termination obligation in "
            "trait_pins_closed_layout's preconditions (obligation leak on the "
            "measureless loop). Under the pre-fix contract Ensures(Result() is "
            "True) held vacuously for this diverging body."
        ),
    },
    {
        "id": "pos-control-bind",
        "kind": "soundness",
        "expect": "verify",
        "module": _VERIFY_POS_BIND,
        "rationale": (
            "Structurally-different but CORRECT impl of the load-bearing contract: "
            "branches on the named predicate instance_admits_namespace(chain) "
            "(== not all_closed_layout(chain)) with the cases reordered (return on "
            "open, raise on closed). Logically identical to gold; keeps every proof "
            "obligation. Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-open-chain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _VERIFY_ADMISS,
        "rationale": (
            "Admissibility / liveness of the success path: a caller builds an open "
            "chain PSeq(True, False), calls bind_undeclared_attribute, and asserts a "
            "normal True return. The precondition (Requires True) admits this "
            "F2P-shaped input and the normal-return branch is reachable (not vacuous); "
            "the verifier knows the Exsures cannot fire because all_closed_layout is "
            "False here. If it could not verify, the precondition would be too strong "
            "or the success path dead."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. meta.json axioms == [] (no @ContractOnly callee), but there is ONE
# A-reference deep model: the CPython object-model rule that an instance has a
# __dict__ (and accepts undeclared-attribute assignment) iff some MRO class
# (!= object) omits __slots__, and raises AttributeError otherwise. PBT checks an
# A-reference exactly like a consumed axiom: the deep model must equal the real
# callee (here the real interpreter) on every input the caller can reach
# (soundness) and every caller-reachable input must lie in the modelled domain
# (containment). Probes EXECUTE the real interpreter (build real classes and
# observe hasattr/__dict__/AttributeError) — they never scrape source (AVOID #4)
# — and read no in-container bundle file (the runner only mounts the probe;
# AVOID #6), so the deep-model rule is embedded into each probe at load time.

# Embed the bundle oracle's transcribed rule + real-interpreter builder so the
# probe is self-contained. We strip the `if __name__` tail so we can call our own
# main() instead of axiom_check.py's.
_AX_RULE = _AXIOM_CHECK_SRC.split('def main(')[0]

_PROBE_SOUND = _AX_RULE + r'''

def main():
    checked = 0
    # Boundary: empty, single layers, the patched/bug 2- and 3-layer Basic shapes.
    boundary = [
        [], [True], [False],
        [True, True], [True, False], [False, True],
        [True, True, True],   # gold Basic chain (all closed -> no namespace)
        [True, True, False],  # prepatch Basic chain (trait open -> namespace)
    ]
    for chain in boundary:
        check_chain(chain)
        checked += 1
    rng = random.Random(20590)
    for _ in range(4000):
        n = rng.randint(0, 6)
        chain = [rng.random() < 0.5 for _ in range(n)]
        check_chain(chain)
        checked += 1
    print("axiom-soundness OK: deep __slots__/__dict__/AttributeError rule == "
          "real interpreter on %d chains (boundary + fuzz), 0 mismatch." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# Containment: enumerate EXACTLY the chains the MODEL can reach. The model only
# constructs chains from `trait` in {True (gold), False (prepatch)}:
#   PSeq(True, True, trait)  and the proof sub-chains it derives by drop:
#   PSeq(), PSeq(trait), PSeq(True, trait), and the F2P observations on
#   the all-True gold chain. The deep model's domain is "all finite bool
#   sequences", so every reachable chain is trivially in-domain; the meaningful
#   containment assertion is that on the GOLD reachable chain (all-True) the
#   interpreter agrees with the model (no namespace + raise) and on the prepatch
#   reachable chain (trailing False) it also agrees (namespace + no raise) — i.e.
#   the deep model covers and correctly classifies every caller-reachable input.
_PROBE_COVER = _AX_RULE + r'''

def main():
    # Exactly the chains the model can construct (trait in {True, False}) plus
    # the proof sub-chains derived by `.drop(...)` in the core_expression_* impls.
    reachable = []
    for trait in (True, False):
        reachable.append([True, True, trait])    # the Basic chain
        reachable.append([])                      # PSeq()
        reachable.append([trait])                 # PSeq(trait)
        reachable.append([True, trait])           # PSeq(True, trait)
    seen = set()
    for chain in reachable:
        key = tuple(chain)
        if key in seen:
            continue
        seen.add(key)
        # Each reachable chain is a finite bool sequence -> inside the deep
        # model's domain (all finite bool sequences). Assert the deep model and
        # the real interpreter AGREE on it (the containment + correctness obligation).
        check_chain(chain)
    # The two F2P-anchoring chains must classify as the F2P expects.
    gold = [True, True, True]
    assert model_instance_admits_namespace(gold) is False, "gold chain must admit NO namespace"
    assert real_instance_admits_namespace(gold) is False, "interpreter: gold Basic has no __dict__"
    assert real_undeclared_assignment_raises(gold) is True, "interpreter: gold Basic raises on b1.x=1"
    bug = [True, True, False]
    assert model_instance_admits_namespace(bug) is True, "prepatch chain must admit a namespace"
    assert real_instance_admits_namespace(bug) is True, "interpreter: prepatch Basic has a __dict__"
    print("axiom-containment OK: every caller-reachable chain (%d) lies in the "
          "deep model's domain and agrees with the interpreter; gold/prepatch "
          "anchors classify as the F2P expects." % len(seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-slots-rule",
        "axiom": "all_closed_layout / instance_admits_namespace (A-reference: CPython __slots__ rule)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUND,
        "rationale": (
            "The A-reference deep model is the only trust point (no @ContractOnly "
            "callee). If the real interpreter's hasattr(inst,'__dict__') or its "
            "AttributeError-on-undeclared-assignment behaviour ever disagrees with "
            "the modelled rule (front-recursive all_closed_layout / "
            "instance_admits_namespace) on a chain in the domain, the deep model is "
            "AXIOM-UNSOUND. Probe executes the real interpreter on 8 boundary + 4000 "
            "fuzz chains (mirrors axiom_check.py / G-AX); never scrapes source."
        ),
    },
    {
        "id": "ax-cover-slots-rule",
        "axiom": "all_closed_layout / instance_admits_namespace (A-reference: CPython __slots__ rule)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_COVER,
        "rationale": (
            "Enumerates EXACTLY the chains the model can reach: PSeq(True,True,trait) "
            "and its drop-derived sub-chains for trait in {True (gold), False "
            "(prepatch)}. Each is a finite bool sequence inside the deep model's "
            "domain (all finite bool sequences), and the probe asserts the model and "
            "the interpreter agree on each, plus that the gold all-True chain and the "
            "prepatch trailing-False chain classify exactly as the F2P expects. A "
            "reachable chain outside the modelled domain would be "
            "AXIOM-TOO-WEAK-FOR-CALLER; none exists."
        ),
    },
]
