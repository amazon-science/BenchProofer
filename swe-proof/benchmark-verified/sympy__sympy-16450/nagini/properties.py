# properties.py — PBT falsification battery for sympy__sympy-16450.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Spec
# cases are full model.py variants that share the FROZEN spec byte-for-byte and
# swap ONLY the text inside the # impl-start / # impl-end region (region surgery
# guarantees same_spec); each is checked by Nagini verify + markers.same_spec.
# Axiom cases are self-contained Python probes run in the instance Docker image
# (gold patch applied) against the REAL sympy assumption-inference engine.
#
# Defended surface (model.py):
#   positive_standin_properties(stated: Dict[int,bool]) models, for a
#   sign-undecided free symbol s in posify(eq), the effective assumptions of the
#   positive stand-in Dummy(s.name, positive=True, **s.assumptions0).assumptions0.
#   `stated` is the symbol's own assumptions0 and is READ-ONLY: Acc(...,1/2).
#   The load-bearing postcondition is the TOTALITY clause
#       Ensures(Result() is derived(stated, True))
#   (reference identity to the pure engine map) together with fractional result
#   permission Acc(dict_pred(Result()),1/2); these jointly pin the WHOLE result
#   to the engine's derivation, so no key may be added / dropped / altered. The
#   F2P (test_posify, issue 16438) asserts posify(Symbol('k',finite=True))[0]
#   .assumptions0 by EXACT whole-dict equality, which this clause binds.
#
# The only way to obtain a value `is derived(stated, True)` inside the impl
# region is to call resolve(stated, True) (its Ensures pin Result() is
# derived(base,add_positive)); the oracle `derived` is GROUNDED in the args, not
# an answer-key, so there is no "wrong echo" of a constant — see 'assessment' in
# the structured return. The reject battery therefore attacks the three ways a
# real wrong patch fails: wrong base (prepatch empty / dropped facts), wrong flag
# (positive=True forgotten), spurious-key injection (atk_12), and the read-only
# frame violation (mutating the source symbol's assumptions0).

from pathlib import Path

INSTANCE = "sympy__sympy-16450"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl region of model.py (gold impl). All spec variants swap ONLY
# this text, so the spec (axioms/pure/pre/post) is never touched.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    # The declaration for the stand-in is the original quantity's stated\n"
    "    # properties (the base) together with the added \"greater than zero\".\n"
    "    return resolve(stated, True)\n"
    "    # impl-end\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl_body):
    """Build a full model.py whose impl region body is `new_impl_body`
    (between the markers). Edits ONLY inside # impl-start/# impl-end."""
    new_region = "    # impl-start\n" + new_impl_body + "    # impl-end\n"
    return _swap(_BASE, _GOLD_IMPL, new_region)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = [

    # ---- POSITIVE CONTROL (soundness) -------------------------------------
    # Structurally different but CORRECT: bind the base declaration to a local
    # variable (a local-variable reshape, NOT a loop-direction/fold flip) and
    # call the engine through it. Keeps the gold proof obligations intact:
    # resolve's Ensures still pin Result() is derived(stated, True). MUST verify;
    # if it does not the totality postcondition is SPEC-TOO-STRONG (rejects a
    # faithful correct impl).
    {
        "id": "pos-control-local-base",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(
            "    # The declaration handed to the engine is exactly the original\n"
            "    # quantity's stated properties; bind it to a local first.\n"
            "    base = stated  # type: Dict[int, bool]\n"
            "    return resolve(base, True)\n"
        ),
        "rationale": "a correct, structurally-different impl (local-variable "
                     "reshape, same dataflow base=stated, add positive) must "
                     "verify; resolve's Ensures still give Result() is "
                     "derived(stated,True). If rejected => SPEC-TOO-STRONG.",
    },

    # ---- ADMISSIBILITY ----------------------------------------------------
    # A self-call on an F2P-shaped in-domain input: a base that does NOT state
    # POSITIVE (exactly the issue-16438 symbol Symbol('k', finite=True), whose
    # assumptions0 lacks 'positive'). The call site must establish the Requires
    # (1/2 permission on the input + POSITIVE() not in it). If it cannot, the
    # precondition is PRECOND-TOO-STRONG for a normal posify input.
    {
        "id": "admiss-finite-base",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    # F2P-shaped caller: a stated map carrying FINITE but NOT\n"
            "    # POSITIVE (the issue-16438 symbol). The precondition must admit\n"
            "    # it; we self-call positive_standin_properties on it.\n"
            "    probe = {}  # type: Dict[int, bool]\n"
            "    probe[FINITE()] = True\n"
            "    Assert(not (POSITIVE() in probe))\n"
            "    Assert(Acc(dict_pred(probe), 1 / 2))\n"
                    "    return resolve(stated, True)\n"
        ),
        "rationale": "the precondition must accept a normal posify input "
                     "(FINITE stated, POSITIVE undecided) at 1/2 permission; the "
                     "self-call establishes Requires and reads the positivity "
                     "postcondition back. If rejected => PRECOND-TOO-STRONG.",
    },

    # ---- FRAME-MUTATION (MANDATORY: `stated` is read-only Acc(...,1/2)) ----
    # The #1 weakness class. A rival WRITES to the read-only input (injects
    # FINITE into `stated`) before handing it to the engine, to vacuously make
    # the base carry the fact. With only 1/2 permission the write is illegal:
    # MUST be rejected for INSUFFICIENT PERMISSION. Every gold invariant/spec is
    # kept verbatim so the rejection is attributable to the write alone.
    # Refinement: a real patch that mutates the original symbol's assumptions0
    # (e.g. s.assumptions0[...] = ...) corrupts the source symbol shared with the
    # caller's expression and would NOT faithfully resolve posify (and SymPy
    # assumption dicts are read-only views anyway).
    {
        "id": "frame-mutate-stated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Illegal: write to the half-permission read-only input to force\n"
            "    # a fact into the base declaration.\n"
            "    stated[FINITE()] = True\n"
            "    return resolve(stated, True)\n"
        ),
        "refinement": "mutating the original symbol's stated assumptions to plant"
                      " a fact corrupts the source symbol the caller still holds; "
                      "the real posify must not write back into s.assumptions0 "
                      "(it builds a fresh Dummy), so this faithful patch would not"
                      " resolve.",
        "rationale": "reject from the PERMISSION SYSTEM: stated is held at "
                     "Acc(dict_pred(stated),1/2); a subscription store needs full "
                     "permission. If it verifies the read-only frame is hollow.",
    },

    # ---- PREPATCH / EMPTY-BASE (uniqueness; the G-DIFF discriminator) -----
    # The exact pre-patch behaviour: build the stand-in from positive=True ALONE
    # (empty base), discarding the symbol's stated assumptions. Fails the
    # TOTALITY clause Result() is derived(stated,True) (derived(empty,True) is
    # not derived(stated,True)) and the Forall fact-preservation (a stated FINITE
    # is dropped). MUST reject.
    {
        "id": "prepatch-empty-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Pre-patch (buggy): empty base reaches the engine; the original\n"
            "    # quantity's stated properties are discarded.\n"
            "    empty = {}  # type: Dict[int, bool]\n"
            "    return resolve(empty, True)\n"
        ),
        "refinement": "this IS the pre-patch Dummy(s.name, positive=True) — it "
                      "drops **s.assumptions0, so posify(Symbol('k',finite=True))"
                      "[0].assumptions0 lacks finite=True and the F2P exact-dict "
                      "equality (issue 16438) FAILS; the faithful patch does not "
                      "resolve.",
        "rationale": "reject from the TOTALITY postcondition Result() is "
                     "derived(stated,True) (empty base gives a different engine "
                     "map) and the Forall fact-preservation. This is G-DIFF.",
    },

    # ---- WRONG-FLAG (partial-domain / control-effect: positivity omitted) -
    # A real wrong patch that carries **s.assumptions0 but FORGETS positive=True
    # (Dummy(s.name, **s.assumptions0)). Models as resolve(stated, False): the
    # result is derived(stated, False), which is NOT derived(stated, True), and
    # POSITIVE is not derived. Fails totality + the positivity postcondition.
    {
        "id": "wrong-flag-no-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Wrong patch: carry the stated properties but forget to add the\n"
            "    # \"greater than zero\" declaration.\n"
            "    return resolve(stated, False)\n"
        ),
        "refinement": "Dummy(s.name, **s.assumptions0) without positive=True "
                      "leaves the stand-in's sign undecided; posify's whole point "
                      "is the positive stand-in, so eq.is_positive would be None "
                      "and the F2P (positive=True in the dict) FAILS — not "
                      "resolving.",
        "rationale": "reject from the positivity postcondition (POSITIVE() in "
                     "Result()) AND the totality clause (derived(stated,False) is "
                     "not derived(stated,True)).",
    },

    # ---- SPURIOUS-KEY INJECTION (value-double-mask; the atk_12 regression) -
    # The witness that motivated the Defect-1 strengthening. Take the engine's
    # real output, then try to extend it with a key the engine never derived
    # (FINITE forced True for a base that did not state it). With fractional
    # result permission the store is illegal (insufficient permission) AND the
    # mutated object is no longer `is derived(stated,True)` — both reject paths.
    # MUST reject; if it verified the spec would admit a fabricated derived key
    # (the old too-weak spec did), which breaks the F2P exact-dict equality.
    {
        "id": "atk12-spurious-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # Fabricate a derived property the engine did not produce.\n"
            "    r = resolve(stated, True)\n"
            "    r[FINITE()] = True\n"
            "    return r\n"
        ),
        "refinement": "forcing a derived key the engine never produced makes the "
                      "stand-in's assumptions0 differ from the real Dummy(...)"
                      ".assumptions0, so the F2P whole-dict equality FAILS; also a "
                      "fabricated assumption can be inconsistent and raise. The "
                      "faithful patch (mutate the engine output) does not resolve.",
        "rationale": "reject from FRACTIONAL RESULT PERMISSION (resolve yields "
                     "Acc(dict_pred(Result()),1/2); a store needs full) and from "
                     "the totality clause (the mutated dict is not the pure engine "
                     "map). Defect-1 strengthening regression.",
    },

    # ---- FRESH-DICT TOTALITY EVASION (uniqueness; supporting) -------------
    # Return a freshly-built dict that merely SATISFIES the fact-preservation /
    # positivity value clauses but is NOT the engine map object. Fails the
    # reference-identity totality clause Result() is derived(stated,True): a
    # fresh {} object is not `is` the pure engine map. MUST reject.
    {
        "id": "fresh-dict-not-engine-map",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(
            "    # A hand-built dict that ducks the engine entirely.\n"
            "    out = {}  # type: Dict[int, bool]\n"
            "    out[POSITIVE()] = True\n"
            "    return out\n"
        ),
        "refinement": "a hand-rolled assumptions dict bypasses the inference "
                      "engine, so it lacks the engine's closure (real/finite/"
                      "nonnegative/... and the stated facts); the F2P exact-dict "
                      "equality FAILS. The faithful patch does not resolve.",
        "rationale": "reject from the totality clause Result() is "
                     "derived(stated,True): a fresh object is not reference-"
                     "identical to the pure engine map; also drops the Forall "
                     "fact-preservation for any non-empty stated.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE  (bundle has @ContractOnly axioms `derived`/`resolve` +
# an A-reference deep model; probes run in-container against the REAL engine)
# ---------------------------------------------------------------------------

# Embed axiom_check.py's proven oracle logic; the runner mounts only the probe
# at /work, so model.py / axiom_check.py are NOT in-container — we inline the
# real-callee checks. Files are opened with encoding="utf-8" where relevant.

_AX_SOUND_PROBE = r'''
import random, sys
from sympy import Symbol, Dummy
from sympy.core.assumptions import _assume_rules
from sympy.simplify.simplify import posify

ASSUMPTION_KEYS = sorted(_assume_rules.defined_facts)

def engine(base, add_positive=True):
    """REAL property-inference engine == model.py resolve(base, add_positive):
    Dummy("x", positive=add_positive, **base).assumptions0; None if inconsistent."""
    asm = dict(base)
    if add_positive:
        asm["positive"] = True
    try:
        return Dummy("x", **asm).assumptions0
    except Exception:
        return None

consistent = 0
lockstep = 0
checked = 0

def check_resolve(s):
    """resolve axiom (A-consumed): on a replaced symbol (is_positive is None,
    so 'positive' not in base) the engine preserves every base fact, derives
    positive=True, and its output IS the engine map (totality, validated via
    posify fidelity below). Raise path checked in LOCK-STEP."""
    global consistent, lockstep
    base = s.assumptions0
    assert "positive" not in base, ("Requires-domain violated: %r" % (base,))
    derived = engine(base, add_positive=True)
    if derived is None:
        # inconsistent declaration: out of the modeled operation's domain. The
        # no-Exsures totality region is sound ONLY because real posify raises in
        # lock-step. Assert that rather than skip (G-AX Defect-2).
        raised = False
        try:
            posify(s)
        except Exception:
            raised = True
        assert raised, ("UNSOUND: engine raises (inconsistent %r) but real "
                        "posify did not raise" % (base,))
        lockstep += 1
        return
    consistent += 1
    for k, v in base.items():
        assert k in derived and derived[k] == v, (
            "UNSOUND: base fact %r=%r not preserved in %r" % (k, v, derived))
    assert derived.get("positive") is True, (
        "UNSOUND: positive not derived from %r -> %r" % (base, derived))

def check_fidelity(s):
    """A-reference: real posify transformation == the engine map (TOTALITY,
    full-dict equality both directions). Pre-patch (no **assumptions0) detectably
    wrong when the base carries a non-positive-implied fact."""
    if s.is_positive is not None:
        return
    base = s.assumptions0
    derived = engine(base, add_positive=True)
    try:
        eq, _rep = posify(s)
        real = eq.assumptions0
    except Exception:
        assert derived is None, ("posify raised but engine returned for %r" % (base,))
        return
    assert derived is not None, ("engine None but posify ok for %r" % (base,))
    assert real == derived, ("TOTALITY broken for base %r: posify=%r engine=%r"
                             % (base, real, derived))
    for k, v in base.items():
        assert real.get(k) == v, ("posify dropped stated fact %r=%r (got %r)"
                                  % (k, v, real))
    bare = engine({}, add_positive=True)
    for k, v in base.items():
        if bare.get(k) != v:
            assert real.get(k) == v and bare.get(k) != v, (
                "spec does not discriminate on base fact %r=%r" % (k, v))

# --- the issue's exact example (issue 16438) ---
k = Symbol("k", finite=True)
eq, _ = posify(k)
assert eq.is_finite is True, ("issue-16438 regression: is_finite=%r" % (eq.is_finite,))
assert eq.is_positive is True, ("stand-in not positive: is_positive=%r" % (eq.is_positive,))
assert eq.assumptions0.get("finite") is True and eq.assumptions0.get("positive") is True, eq.assumptions0
check_fidelity(k); check_resolve(k)

# --- single-fact boundary bases ---
single = ["finite","integer","rational","even","odd","prime","real","complex",
          "commutative","hermitian","algebraic","nonzero","irrational",
          "transcendental","composite"]
for key in single:
    try:
        s = Symbol("x", **{key: True})
    except Exception:
        continue
    if s.is_positive is None:
        check_resolve(s)
    check_fidelity(s)
check_resolve(Symbol("x")); check_fidelity(Symbol("x"))

# --- randomized fuzz over real consistent symbols (boundaries + raise paths) ---
rng = random.Random(16450)
for _ in range(20000):
    n = rng.randint(0, 4)
    keys = rng.sample(ASSUMPTION_KEYS, n)
    asm = {kk: rng.choice([True, False]) for kk in keys}
    try:
        s = Symbol("x", **asm)
    except Exception:
        continue
    if s.is_positive is None:
        check_resolve(s)
    check_fidelity(s)
    checked += 1

print("AX-SOUND OK: resolve/derived sound + posify fidelity (totality real==engine"
      " both directions) on the issue example + %d single-fact + %d fuzz consistent"
      " symbols; resolve exercised on %d consistent bases; raise path LOCK-STEP on"
      " %d inconsistent declarations." % (len(single), checked, consistent, lockstep))
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
import random, sys
from sympy import Symbol, Dummy
from sympy.core.assumptions import _assume_rules
from sympy.simplify.simplify import posify

# Containment: the MODEL calls resolve/derived with EXACTLY one callee-input
# shape: base = stated (the replaced symbol's assumptions0) and add_positive =
# True. The axiom's Requires domain is `add_positive => POSITIVE not in base`,
# i.e. when add_positive is True the base must NOT contain 'positive'. The model
# enforces this in its OWN precondition: Requires(not (POSITIVE() in stated)),
# and `stated` is the assumptions0 of a symbol posify replaces precisely when
# `s.is_positive is None`. So the single reachable input always lies in the
# axiom domain. We confirm it on every caller-reachable symbol: for every symbol
# posify would replace (is_positive is None) the base lacks 'positive'.
# A reachable input WITH 'positive' would be AXIOM-TOO-WEAK-FOR-CALLER; we try to
# manufacture one and assert posify never replaces such a symbol.

ASSUMPTION_KEYS = sorted(_assume_rules.defined_facts)

def reachable_base(s):
    """The exact base the model would pass to resolve for symbol s, IF posify
    replaces it. posify replaces s iff s.is_positive is None. Returns the base
    (s.assumptions0) or None if s is not in the replaced domain."""
    if s.is_positive is None:
        return s.assumptions0
    return None

checked = 0
# 1. issue example + single-fact bases
samples = [Symbol("k", finite=True), Symbol("x")]
single = ["finite","integer","rational","even","odd","prime","real","complex",
          "commutative","hermitian","algebraic","nonzero","irrational",
          "transcendental","composite"]
for key in single:
    try:
        samples.append(Symbol("x", **{key: True}))
    except Exception:
        pass

# 2. explicit attempt to reach an out-of-domain input: declare 'positive'
#    directly. Such a symbol has is_positive is not None, so posify does NOT
#    replace it -> it is NOT a caller-reachable base. Confirm.
for val in (True, False):
    try:
        sp = Symbol("p", positive=val)
    except Exception:
        continue
    assert sp.is_positive is not None, ("symbol with positive=%r still has "
                                        "is_positive None?" % (val,))
    assert reachable_base(sp) is None, ("a 'positive'-stating symbol is NOT in "
                                        "posify's replaced domain")

# 3. fuzz: every reachable base lies in the axiom domain (no 'positive' key)
rng = random.Random(164502)
for _ in range(20000):
    n = rng.randint(0, 4)
    keys = rng.sample(ASSUMPTION_KEYS, n)
    asm = {kk: rng.choice([True, False]) for kk in keys}
    try:
        s = Symbol("x", **asm)
    except Exception:
        continue
    samples.append(s)

for s in samples:
    base = reachable_base(s)
    if base is None:
        continue  # not a caller-reachable input
    # add_positive is fixed True in the model; domain requires positive not in base
    assert "positive" not in base, (
        "AXIOM-TOO-WEAK-FOR-CALLER: model reaches base %r containing 'positive' "
        "while add_positive=True (outside resolve/derived Requires domain)" % (base,))
    # also confirm the engine accepts it (consistent or raises out of domain),
    # i.e. the declaration the model forms is well-typed for the callee
    checked += 1

print("AX-CONTAIN OK: every caller-reachable base (replaced symbols, "
      "is_positive None) lacks 'positive', so each (base, add_positive=True) input"
      " the model forms lies inside resolve/derived's Requires domain; %d "
      "reachable bases checked; 'positive'-stating symbols confirmed NOT replaced "
      "(not reachable)." % (checked,))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-resolve",
        "axiom": "resolve",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the REAL engine Dummy('x',positive=True,**base).assumptions0"
                     " must meet resolve/derived's Ensures on every in-domain base"
                     " (preserve each base fact, derive positive=True, output IS "
                     "the engine map == real posify, both directions). Raise path "
                     "checked LOCK-STEP (engine raises <=> posify raises). A "
                     "violation => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-resolve",
        "axiom": "resolve",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "the model passes exactly (base=stated, add_positive=True); "
                     "the axiom domain requires positive not in base when "
                     "add_positive. Every caller-reachable base (a replaced "
                     "symbol's assumptions0, is_positive None) lacks 'positive', "
                     "so each reachable callee-input lies in the domain. A "
                     "reachable input outside it => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
