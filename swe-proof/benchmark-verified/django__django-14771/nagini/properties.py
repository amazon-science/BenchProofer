# properties.py — PBT falsification battery for django__django-14771.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT.  Spec cases are full
# model.py variants that share the FROZEN spec byte-for-byte (region-surgery:
# every _swap edits ONLY text inside the # impl-start / # impl-end region, so
# same_spec is guaranteed) and swap only the implementation; they are checked
# by Nagini verify + markers.same_spec.  Axiom cases are real-callee probes run
# in the instance Docker image.
#
# DEFENDED SURFACE (read from model.py / refinement.md / instance.json):
#   child_arguments rebuilds the reloader child argv.  The CHANGED behaviour is
#   the `-X` implementation-option forwarding: on the reference interpreter
#   (is_reference_impl) each supplied option (opt_keys[i], opt_is_flag[i],
#   opt_vals[i]) becomes ONE token -- '-Xname' when opt_is_flag[i] (the value was
#   the present-with-no-value sentinel True), else '-Xname=value' -- in supplied
#   ORDER, inserted into the LEADING args (prefix) BEFORE the rest of the command
#   line; on a non-reference interpreter NOTHING is forwarded.  Modeled deeply by
#   the front-recursive fold option_tokens / option_token (NO consumed axiom; an
#   A-reference validated by axiom_check.py / G-AX).
#
#   The three postcondition clauses pin Result() exactly:
#     (A) module launch:  prefix + (option_tokens if is_reference_impl else empty)
#                          + PSeq(dash_m, launch_package) + argv.drop(1)
#     (B) not module launch, script_exists: prefix + (option_tokens if ref else
#                          empty) + argv
#     (C) not module launch, not script_exists: windows_recovery()
#   option_tokens is GROUNDED in the inputs (a fully-unfolded fold of opt_keys/
#   opt_is_flag/opt_vals); it is NOT an opaque answer-key oracle, so there is no
#   "wrong echo that still verifies" -- see ASSESSMENT.  All inputs are immutable
#   pure-sequence VALUES (no Acc(x,1/2) / list_pred), so the frame-mutation class
#   is N/A by construction -- see ASSESSMENT.
from pathlib import Path

INSTANCE = "django__django-14771"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _region(src, first, last):
    """The inclusive span from `first` to the first `last` at or after it.

    A guard whose body must go with it cannot be anchored by its header alone:
    deleting the header orphans the block, and rewriting the header to `if False:`
    makes the body unreachable, which Nagini's front end rejects (`dead.code`)
    before Viper sees anything -- and a rival that fails to translate proves
    nothing about the spec (43c6680f6). So the whole statement is the anchor.
    """
    if src.count(first) != 1:
        raise AssertionError(f"not unique: {first!r}")
    i = src.index(first)
    j = src.index(last, i) + len(last)
    return src[i:j]


# The WHOLE `-X` forwarding block as one anchor, so a rival that omits the
# forwarding is written by DELETING it rather than by disabling its guard.
_FORWARD_BLOCK = _region(_BASE, "    if is_reference_impl:\n",
                         "            i = i - 1\n")
_NO_FORWARD = (
    "    # PRE-PATCH: the implementation options are never forwarded at all, so\n"
    "    # `options` keeps the empty sequence it was initialised to.\n"
)


# ---------------------------------------------------------------------------
# The frozen impl region (verbatim from model.py); every variant is built by
# _swap against pieces of THIS text, so edits never escape # impl-start/-end.
# ---------------------------------------------------------------------------
_GOLD_LOOP = """    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    options = empty
    if is_reference_impl:
        i = len(opt_keys)
        while i > 0:
            # invariants-start
            Invariant(0 <= i and i <= len(opt_keys))
            Invariant(len(opt_keys) == len(opt_is_flag)
                      and len(opt_is_flag) == len(opt_vals))
            Invariant(options == option_tokens(opt_keys.drop(i),
                                                opt_is_flag.drop(i),
                                                opt_vals.drop(i)))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
                               opt_vals[i - 1])
            options = PSeq(tok) + options
            i = i - 1
    leading = prefix + options"""

_GOLD_RETURN = """    if package_reported and len(launch_package) > 0:
        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return leading + argv"""


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally-different but CORRECT -----
    # Reorder the trailing dispatch: test the recovery (script-absent) branch
    # FIRST, then the module-launch branch, then fall through.  The option-fold
    # loop and ALL its invariants/asserts are kept VERBATIM (caution #2/#3: a
    # front-recursive fold needs the backward loop + per-element pins to
    # discharge; we only reshape the executable branch order downstream).  Same
    # Result() in every clause-(A)/(B)/(C) case, so it MUST verify.
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_RETURN,
            """    if not is_module_launch(package_reported, launch_package) \\
            and not script_exists:
        return windows_recovery()
    elif is_module_launch(package_reported, launch_package):
        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
    else:
        return leading + argv""",
        ),
        "rationale": "a correct impl with the trailing branches reordered "
                     "(recovery-first) computes the identical Result() in every "
                     "clause; if it cannot verify the postcondition is "
                     "SPEC-TOO-STRONG. Loop + invariants/asserts kept verbatim "
                     "so no auto-discharge proof gap (caution #2/#3).",
    },

    # -- POSITIVE CONTROL #2: local-variable reshape -------------------------
    # Hoist the module-launch predicate into a local bool and the program tail
    # into a local seq; same values, different SSA shape.  Keep loop verbatim.
    {
        "id": "pos-control-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_RETURN,
            """    is_mod = is_module_launch(package_reported, launch_package)
    tail = argv.drop(1)  # type: PSeq[PSeq[int]]
    if is_mod:
        return leading + PSeq(dash_m(), launch_package) + tail
    elif not script_exists:
        return windows_recovery()
    else:
        return leading + argv""",
        ),
        "rationale": "binding the module-launch predicate and argv tail to typed "
                     "locals is a pure SSA reshape with identical Result(); must "
                     "verify (else SPEC-TOO-STRONG). Loop kept verbatim.",
    },

    # -- ADMISSIBILITY: the precondition admits a normal F2P-shaped input -----
    # F2P test_xoptions: argv=[script,'runserver'] (len 2 >= 1), not a module
    # launch, script present, is_reference_impl, 2 options {'utf8':True,'a':'b'}
    # => index-aligned len-2 sequences.  An assertion at impl entry confirms the
    # Requires accepts exactly that shape (len(opt_keys)==len(opt_is_flag)==
    # len(opt_vals) and len(argv)>=1) reflexively; then the gold body runs.
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]\n    options = empty",
            "    # F2P test_xoptions shape: len-2 aligned option seqs, argv>=1.\n"
            "    Assert(len(opt_keys) == len(opt_is_flag)\n"
            "           and len(opt_is_flag) == len(opt_vals))\n"
            "    Assert(len(argv) >= 1)\n"
            "    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]\n    options = empty",
        ),
        "rationale": "the precondition must accept a normal F2P-shaped input "
                     "(aligned option sequences, argv non-empty); the entry "
                     "asserts re-derive exactly the Requires, so they verify "
                     "iff the precondition is admissible (else PRECOND-TOO-STRONG).",
    },

    # -- UNIQUENESS / partial-domain: DROP the is_reference_impl guard --------
    # Forward the option tokens UNCONDITIONALLY (even on a non-reference
    # interpreter).  Refinement: the gold guards on
    # `sys.implementation.name == 'cpython'`; a faithful patch that drops that
    # guard would emit '-X...' tokens on PyPy/Jython that the real interpreter
    # never recorded that way -- behaviourally different from gold, would not
    # resolve on a non-cpython run.  Rejected by clauses (A)/(B): when
    # is_reference_impl is False the spec requires the EMPTY option segment, but
    # this impl inserts option_tokens.
    {
        "id": "weak-drop-cpython-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    options = empty\n    if is_reference_impl:\n        i = len(opt_keys)",
            "    options = empty\n    if True:\n        i = len(opt_keys)",
        ),
        "refinement": "the gold forwards options ONLY under "
                      "`if sys.implementation.name == 'cpython'`; dropping that "
                      "guard forwards -X tokens on a non-reference interpreter "
                      "where sys._xoptions would not be re-supplied that way, so "
                      "the faithful patch diverges from gold and would not resolve "
                      "(it changes the non-cpython child argv).",
        "rationale": "rejected by postcondition clauses (A)/(B): the "
                     "`option_tokens(...) if is_reference_impl else empty` "
                     "selector requires the EMPTY segment when not "
                     "is_reference_impl; forwarding unconditionally violates it.",
    },

    # -- UNIQUENESS / partial-domain: FLIP the flag/value rule ---------------
    # Always emit '-Xname=value' (use option_token with is_flag=False), even for
    # a present-with-no-value option.  Refinement: the F2P `{'utf8': True}`
    # expects '-Xutf8' (flag form); this rival emits '-Xutf8=...' and the real
    # patch would produce '-Xutf8=True'-style tokens, failing test_xoptions.
    # Rejected by clause's option_token definition (is_flag branch).
    {
        "id": "weak-flip-flag-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],\n"
            "                               opt_vals[i - 1])",
            "            tok = option_token(opt_keys[i - 1], False,\n"
            "                               opt_vals[i - 1])",
        ),
        "refinement": "the gold uses `f'-X{key}' if value is True` -- a flag-only "
                      "option yields just '-Xname'; forcing the name=value form "
                      "makes the F2P `sys._xoptions={'utf8':True,...}` emit "
                      "'-Xutf8=...' instead of '-Xutf8', so the faithful patch "
                      "fails test_xoptions (would not resolve).",
        "rationale": "rejected by the option_token definition consumed in the "
                     "postcondition: for opt_is_flag[i]=True the token is "
                     "dash_x()+key, not dash_x()+key+eq()+val.",
    },

    # -- UNIQUENESS / value-order: REVERSE the option order ------------------
    # Append each token to the END (options = options + PSeq(tok)) while walking
    # backward, producing the tokens in REVERSE supplied order.  Refinement: the
    # F2P `{'utf8': True, 'a': 'b'}` expects ['-Xutf8','-Xa=b'] in iteration
    # order; reversed gives ['-Xa=b','-Xutf8'], so the faithful patch fails
    # test_xoptions.  Rejected by option_tokens' front-recursive order.
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "            options = PSeq(tok) + options\n            i = i - 1",
            "            options = options + PSeq(tok)\n            i = i - 1",
        ),
        "refinement": "the gold preserves dict iteration order "
                      "(`{'utf8':True,'a':'b'}` -> ['-Xutf8','-Xa=b']); a reversed "
                      "order yields ['-Xa=b','-Xutf8'], so the faithful patch "
                      "fails the F2P test_xoptions equality (would not resolve).",
        "rationale": "rejected by option_tokens being a front-recursive fold "
                     "(supplied order); the reversed accumulation breaks the "
                     "loop invariant tying options to option_tokens(...drop(i)).",
    },

    # -- UNIQUENESS / partial-domain: FORWARD ONLY the first option ----------
    # Stop the fold after one option (i > len(opt_keys)-1 instead of i > 0):
    # forwards just the last-processed (== first supplied) token.  Refinement:
    # the F2P has TWO options; emitting only one drops '-Xa=b', so the faithful
    # patch fails test_xoptions.  Rejected by the fold over ALL options.
    {
        "id": "weak-only-first-option",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "        i = len(opt_keys)\n        while i > 0:",
            "        i = len(opt_keys)\n        while i > 1:",
        ),
        "refinement": "the gold forwards EVERY supplied option "
                      "(`for key, value in sys._xoptions.items()`); forwarding "
                      "only one drops the rest, so the F2P with two options "
                      "({'utf8':True,'a':'b'}) loses '-Xa=b' and the faithful "
                      "patch fails test_xoptions (would not resolve).",
        "rationale": "rejected by clauses (A)/(B): option_tokens covers all "
                     "indices; halting at i>1 leaves options == "
                     "option_tokens(...drop(1)) != option_tokens(full).",
    },

    # -- UNIQUENESS / placement: insert options AFTER the command line -------
    # Build the leading args WITHOUT options (leading = prefix) and append the
    # forwarded tokens at the END of every shape.  Refinement: the gold inserts
    # the tokens into the LEADING args (before argv); the F2P expects
    # [exe,'-Xutf8','-Xa=b',script,'runserver'] but this rival emits
    # [exe,script,'runserver','-Xutf8','-Xa=b'], failing test_xoptions.
    {
        "id": "weak-options-after-cmdline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _GOLD_RETURN,
            """    if package_reported and len(launch_package) > 0:
        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1) + options
    elif not script_exists:
        return windows_recovery()
    else:
        return prefix + argv + options""",
        ),
        "refinement": "the gold inserts the forwarded tokens into the LEADING "
                      "args (`args.extend(...)` before the `-m`/argv append), so "
                      "the F2P expects [exe,'-Xutf8','-Xa=b',script,'runserver']; "
                      "placing them after argv yields "
                      "[exe,script,'runserver','-Xutf8','-Xa=b'] and the faithful "
                      "patch fails test_xoptions (would not resolve).",
        "rationale": "rejected by clauses (A)/(B): Result() is pinned to "
                     "prefix + options + (rest), i.e. options PRECEDE argv; "
                     "appending them after argv violates the concatenation order.",
    },

    # -- UNIQUENESS / partial-domain: OMIT forwarding entirely (prepatch) ----
    # The pre-patch behaviour: never forward (options stays empty even on the
    # reference interpreter).  This is exactly model_prepatch.py.  Refinement:
    # the pre-patch is the bug the gold fixes; it fails the F2P test_xoptions
    # (no '-X' tokens).  Rejected by clauses (A)/(B) (G-DIFF already confirms
    # this fails clause (A)/(B)).  Supporting case grounded in model_prepatch.
    {
        "id": "weak-omit-forwarding-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FORWARD_BLOCK, _NO_FORWARD),
        "refinement": "this is the PRE-PATCH behaviour (model_prepatch.py): the "
                      "implementation options are never forwarded, so on the "
                      "reference interpreter with options supplied the child argv "
                      "omits the '-X' tokens -- exactly the bug the gold patch "
                      "fixes; the F2P test_xoptions fails (would not resolve).",
        "rationale": "rejected by postcondition clauses (A)/(B): when "
                     "is_reference_impl the required segment is "
                     "option_tokens(opt_keys,...), not the empty sequence "
                     "(G-DIFF confirms the prepatch fails here).",
    },
]


# ===========================================================================
# AXIOM LANE  --  the option_tokens deep model is an A-reference (NO consumed
# @ContractOnly axiom; meta.axioms == []).  We still probe it as an A-reference:
#   (1) axiom-soundness: the REAL gold forwarding generator
#       (`f'-X{key}' if value is True else f'-X{key}={value}'`, gated on
#       sys.implementation.name == 'cpython') must equal option_tokens on every
#       caller-reachable input -- reusing axiom_check.py's exact logic, fuzzed.
#   (2) axiom-containment: every callee-input the MODEL can reach lies inside
#       the A-reference's domain (the generator accepts ANY dict, so containment
#       is total; we assert the F2P + boundary inputs map cleanly).
# The probe imports ONLY stdlib (sys, random) and runs on the eval interpreter,
# which reports sys.implementation.name == 'cpython' (the guard the forwarding
# is gated on).  It is self-contained (does NOT read model.py / axiom_check.py
# from disk -- the runner mounts only the probe at /work; caution #6).
# ===========================================================================

_AX_SOUND_PROBE = r'''
import sys, random

# --- model reference encodings (in lock-step with model.py's deep model) ----
_DASH_X = [45, 88]   # dash_x() == PSeq(45,88) == '-X'
_EQ = [61]           # eq()     == PSeq(61)    == '='

def cp(s):
    return [ord(ch) for ch in s]

def option_token(key, is_flag, val):
    # Reference of model.py option_token: flag+name, else flag+name+'='+value.
    if is_flag:
        return _DASH_X + cp(key)
    return _DASH_X + cp(key) + _EQ + cp(val)

def option_tokens_model(xoptions):
    # Reference of model.py option_tokens fold, one token per option in order.
    out = []
    for key, value in xoptions.items():
        is_flag = (value is True)
        val = "" if is_flag else ("%s" % (value,))
        out.append(option_token(key, is_flag, val))
    return out

# --- the REAL gold forwarding generator, verbatim --------------------------
def real_forwarded_tokens(xoptions, implementation_name):
    if implementation_name != 'cpython':
        return []
    return [
        f'-X{key}' if value is True else f'-X{key}={value}'
        for key, value in xoptions.items()
    ]

def check(xoptions, impl='cpython'):
    real = [cp(t) for t in real_forwarded_tokens(xoptions, impl)]
    model = [] if impl != 'cpython' else option_tokens_model(xoptions)
    assert real == model, (
        "option_tokens deep model UNSOUND on %r (impl=%r): real=%r model=%r"
        % (xoptions, impl, real, model))

# --- boundary cases incl. the exact F2P sys._xoptions ----------------------
boundary = [
    {},
    {'utf8': True},
    {'a': 'b'},
    {'utf8': True, 'a': 'b'},          # the F2P case -> -Xutf8 -Xa=b
    {'a': 'b', 'utf8': True},          # order preserved
    {'opt': ''},                       # empty value -> '-Xopt='
    {'k': 'v=w'},                      # value containing '='
    {'truthy': 'True'},                # truthy STRING is NOT the True sentinel
    {'falsey': False},                 # False is NOT the sentinel
    {'n': 0}, {'n': 1}, {'pi': 3},     # int values rendered by %s
    {'importtime': True, 'tracemalloc': '5', 'utf8': True},
]
for xo in boundary:
    check(xo, 'cpython')
    check(xo, 'pypy')                  # non-reference forwards nothing
    check(xo, 'jython')

# --- the decisive `value is True` identity test ----------------------------
assert real_forwarded_tokens({'x': True}, 'cpython') == ['-Xx']
assert real_forwarded_tokens({'x': 'True'}, 'cpython') == ['-Xx=True']
assert real_forwarded_tokens({'x': 1}, 'cpython') == ['-Xx=1']
assert real_forwarded_tokens({'x': False}, 'cpython') == ['-Xx=False']

# --- randomized fuzz over the caller-reachable input space -----------------
rng = random.Random(14771)
ka = "abcdefghijklmnopqrstuvwxyz_0123456789"
va = ka + "=.-/ "
for _ in range(20000):
    n = rng.randint(0, 6)
    xo = {}
    for _ in range(n):
        key = "".join(rng.choice(ka) for _ in range(rng.randint(1, 8)))
        r = rng.random()
        if r < 0.4:
            xo[key] = True
        elif r < 0.7:
            xo[key] = "".join(rng.choice(va) for _ in range(rng.randint(0, 8)))
        elif r < 0.85:
            xo[key] = rng.randint(0, 1000)
        else:
            xo[key] = rng.choice([False, 'True', 'true', '0', ''])
    check(xo, rng.choice(['cpython', 'cpython', 'cpython', 'pypy']))

# --- the guard fact: the eval interpreter IS the reference one -------------
assert sys.implementation.name == 'cpython', (
    "expected the reference interpreter; got %r" % sys.implementation.name)

print("AX-SOUND OK: option_tokens deep model == real -X forwarding generator "
      "(gated on cpython) over %d boundary + 20000 fuzz dicts; value-is-True "
      "identity + cpython guard confirmed" % len(boundary))
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
import sys

# The A-reference (the gold generator) accepts ANY sys._xoptions dict iterated
# by .items(): keys are str, values are either the bool True sentinel or an
# arbitrary value rendered by the f-string.  The MODEL reaches this callee only
# through the three index-aligned sequences opt_keys/opt_is_flag/opt_vals built
# from the dict, under the cpython guard.  Containment is therefore TOTAL: every
# input the model can pass (any aligned (key, is_flag, val) triple) maps to a
# (key, value) pair the generator accepts.  We assert the F2P + boundary inputs
# the model reaches all lie inside the generator's domain (it raises on none).

def gen_accepts(xoptions):
    # The generator's domain: it iterates .items() and applies an f-string /
    # identity test -- defined for any dict with hashable str keys.  Returns the
    # token list (no exception) iff the input is in-domain.
    return [
        f'-X{key}' if value is True else f'-X{key}={value}'
        for key, value in xoptions.items()
    ]

# Exactly the inputs the model can reach (the F2P + the boundary classes the
# caller's Requires admits: aligned sequences <-> any dict).
reachable = [
    {},
    {'utf8': True, 'a': 'b'},          # the F2P sys._xoptions
    {'a': 'b'},
    {'opt': ''},
    {'truthy': 'True'},
    {'falsey': False},
    {'n': 0},
    {'importtime': True, 'tracemalloc': '5', 'utf8': True},
]
for xo in reachable:
    toks = gen_accepts(xo)            # in-domain: no exception
    assert len(toks) == len(xo), (
        "containment: one token per option expected for %r, got %r" % (xo, toks))

# A reachable input OUTSIDE the covered domain would be AXIOM-TOO-WEAK-FOR-CALLER;
# there is none -- the generator's domain is all dicts, a superset of every
# aligned-sequence triple the model can build (covering MORE than the caller
# reaches is SOUND, not a defect).
print("AX-CONTAIN OK: every model-reachable sys._xoptions input lies in the "
      "A-reference generator domain (containment total); %d reachable inputs "
      "checked" % len(reachable))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-option_tokens",
        "axiom": "option_tokens",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "option_tokens is an A-reference for the gold "
                     "`f'-X{key}' if value is True else f'-X{key}={value}'` "
                     "generator gated on sys.implementation.name=='cpython'. The "
                     "probe drives the REAL generator over boundary + 20000 fuzz "
                     "dicts under the caller's runtime config and asserts it "
                     "equals the deep model; any disagreement is AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-option_tokens",
        "axiom": "option_tokens",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "every sys._xoptions input the model can reach (any "
                     "aligned key/is_flag/val triple <-> any dict) lies inside "
                     "the generator's domain (all dicts); containment is total. "
                     "A reachable input outside it would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER -- there is none.",
    },
]
