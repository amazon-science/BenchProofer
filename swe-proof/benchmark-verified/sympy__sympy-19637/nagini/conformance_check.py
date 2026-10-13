#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-19637 (nagini).

SHADOW — the `# impl-start` / `# impl-end` region of `model.py`, copied VERBATIM
    below (only the contract calls `Requires`/`Ensures`/`MustTerminate` and the
    `@Pure` decorators are deleted; the `@Pure` helpers `key_member` and
    `expected_signal` the region depends on are copied the same way). No
    restructuring, no renaming: `compute_processing_signal` here is byte-for-byte
    the model's impl statements. This bundle consumes NO `@ContractOnly` axiom
    (meta.json `axioms: []`, mapping.md §3), so there is no axiomatized callee to
    substitute — the whole shadow is executable computation.

ORACLE — the REAL patched repo function, CALLED, not transliterated:
    `sympy.core.sympify.kernS` (`sympy/core/sympify.py:440`, the `hit`
    computation at `:471,473,510-516` @ base_commit
    63f8f465d48559fecb4e4bf3c48b75bf15a3e0ef; the gate git-applies the gold
    patch to /testbed before this script runs and sets PYTHONPATH, so the
    imported module IS the patched one).

    Where the velvet and lean siblings *reconstruct* the patched flag slice in
    Python/Lean (their oracle is a hand-copy of the gold hunk), this check drives
    the real function instead: `kernS(s)` is invoked on a real input string under
    `sys.settrace`, and the tracer stops the real frame at the first line AFTER
    the guard block (`for i in range(2):`) and reads the real function's own
    locals there:

      * `hit`  — the real signal the modeled function must reproduce;
      * `kern` — present in the frame locals iff the real code created a
        substitution key (the `if ' ' in s:` branch ran);
      * `olds` — present iff the real outer guard `'(' in s and not quoted` was
        entered;
      * `s`    — the rewritten text, for the real membership `kern in s`.

    Aborting the frame at that line (the tracer raises a private sentinel) means
    the downstream `sympify`/`subs` machinery — unchanged by the patch and not
    part of the model — never runs, so arbitrary fuzz strings can be pushed
    through the real flag computation without tripping parser errors. Nothing
    about the flag computation is reimplemented here: every `entered`, `key` and
    `hit` value compared below was produced by the repo's own bytecode.

    The script refuses to run against an UNPATCHED `kernS` (it checks, from
    `inspect.getsourcelines`, that `hit = kern in s` is indented inside
    `if ' ' in s:` and that the `else:` arm exists) so a green verdict can never
    mean "the oracle was the pre-patch function". Negative control: with the
    gold patch withheld, the real frame raises `UnboundLocalError` on the
    entered/no-key inputs (the F2P witness `"(2*x)/(x-1)"` among them) and every
    such input is recorded as a disagreement — i.e. this check is capable of
    failing, and does fail, on the pre-patch oracle.

BRIDGE — mapping.md §2, inverted. The model's carrier is
    (`entered: bool`, `key: Optional[bool]`); the real function's input is a
    `str`. Generation goes concrete -> abstract: a real string `s_in` is fed to
    the real `kernS`, and the observed frame yields
    `entered = ('olds' in locals)` (cross-checked against the guard predicate
    `'(' in s_in and not quoted` recomputed from the input) and
    `key = None if 'kern' not in locals else (locals['kern'] in locals['s'])`
    (absence = no substitution key was created; value = the real membership test
    `kern in s`, the key's single observable). Generating in this direction makes
    every input Requires-satisfying by construction: the real code binds `kern`
    only inside the guard, so `not entered ==> key is None` holds — and that is
    asserted on every input rather than assumed, since a violation would itself
    be a refutation of the model's precondition.

INPUTS — 100_000+ real strings driven through the real patched `kernS`
    (`SEED = 19637`, pinned here and recorded in mapping.md §G-CONF): boundary
    cases first (empty, singleton, quoted, the F2P witness `"(2*x)/(x-1)"`, the
    `test_kernS` expressions, key-collision inputs that force the `while kern in
    s` growth loop), then seeded fuzz over a paren/operator/quote/underscore
    alphabet with parentheses balanced so the input reaches the flag
    computation. The ABSTRACT domain is finite and tiny — 4 points, of which
    `Implies(not entered, key is None)` admits (F,None), (T,None), (T,True),
    (T,False) — so it is additionally ENUMERATED exhaustively against the
    model's own `expected_signal`, and the fuzz run asserts that each abstract
    state REACHABLE in the real repo is witnessed at least once by a real string
    (a run that missed a branch fails instead of passing vacuously). The fourth
    point (T,False) is unreachable in the real repo — a freshly created `kern` is
    unique in `s` and is then spliced in by `s.replace(' ', kern)`, so
    `kern in s` is necessarily True — and the run reports it as unwitnessed
    rather than pretending it was covered.

Exit 0 iff zero disagreements; on a disagreement the input, the bridged carrier
and both signals are printed and the exit status is 1. stdlib + the repo package
only.
"""
import inspect
import random
import sys

SEED = 19637
N_INPUTS = 100_000
MAX_REPORT = 10


# ---------------------------------------------------------------------------
# model.py `# pure-start` region, copied VERBATIM (@Pure and the Requires
# contract line stripped).
# ---------------------------------------------------------------------------
def key_member(key):
    """Whether the created substitution key occurs in the rewritten text. This
    inspection is defined ONLY when a key was actually created (key is not
    None); inspecting an absent key is excluded by the precondition — there is
    nothing to inspect when no key exists."""
    return key  # type: ignore[return-value]


def expected_signal(entered, key):
    """The signal the desired behaviour demands: the created key's membership in
    the rewritten text when a key was created (the entered-and-substituted
    case), and false otherwise (the no-substitution case — no key exists)."""
    if entered and key is not None:
        return key_member(key)
    return False


# ---------------------------------------------------------------------------
# model.py `# impl-start` / `# impl-end` region, copied VERBATIM (the enclosing
# def line kept; the Requires/Ensures/MustTerminate contract lines are the only
# thing removed).
# ---------------------------------------------------------------------------
def compute_processing_signal(entered, key):
    # Default: no processing was applied.
    hit = False
    if entered:
        # The transform is entered. A key is created and spliced in ONLY when a
        # substitution is performed (key is not None). The signal — the key's
        # membership in the rewritten text — is read ONLY in that case, when a
        # key actually exists; otherwise the signal stays false.
        if key is not None:
            hit = key_member(key)
        else:
            hit = False
    return hit


# ---------------------------------------------------------------------------
# Oracle plumbing: drive the REAL patched kernS and read its own locals.
# ---------------------------------------------------------------------------
class _StopAtFlag(Exception):
    """Private sentinel: stop the real kernS frame once the flag is final."""


def locate_flag_line(fn):
    """Return (record_lineno, patched) for the real `kernS`.

    record_lineno is the line of `for i in range(2):` — the first statement
    after the guard block, i.e. the point at which the real local `hit` is final
    and `kern`'s binding state is decided.  `patched` reports whether the gold
    shape is in place: `hit = kern in s` indented INSIDE `if ' ' in s:`, with an
    `else:` arm at the guard's own indentation.
    """
    src, start = inspect.getsourcelines(fn)
    record = space_guard = flag_assign = else_arm = None
    for off, raw in enumerate(src):
        text = raw.strip()
        if text == "for i in range(2):" and record is None:
            record = start + off
        if text == "if ' ' in s:":
            space_guard = (start + off, len(raw) - len(raw.lstrip()))
        if text == "hit = kern in s":
            flag_assign = (start + off, len(raw) - len(raw.lstrip()))
        if text == "else:" and space_guard is not None and else_arm is None:
            else_arm = (start + off, len(raw) - len(raw.lstrip()))
    if record is None or space_guard is None or flag_assign is None:
        raise RuntimeError("cannot locate the kernS flag computation in the "
                           "installed source (record=%r guard=%r assign=%r)"
                           % (record, space_guard, flag_assign))
    patched = (flag_assign[1] > space_guard[1]
               and else_arm is not None
               and else_arm[1] == space_guard[1])
    return record, patched


def observe_real(kern_s, code_obj, record_lineno, s_in):
    """Drive the REAL patched kernS on `s_in` and observe its flag computation.

    Returns one of
      ("ok", entered, key, hit)   the frame reached the flag-completion line
      ("excluded", reason)        the real code raised before the flag was
                                  computed (unmatched-parenthesis guard) — the
                                  input is outside the modeled domain
      ("raised", exc_repr)        the real code raised *at* the flag
                                  computation (the pre-patch UnboundLocalError)
    """
    box = {}

    def local_trace(frame, event, arg):
        if event == "line" and frame.f_lineno == record_lineno:
            box["locals"] = dict(frame.f_locals)
            raise _StopAtFlag()
        return local_trace

    def global_trace(frame, event, arg):
        if event == "call" and frame.f_code is code_obj:
            return local_trace
        return None

    sys.settrace(global_trace)
    try:
        kern_s(s_in)
    except _StopAtFlag:
        pass
    except UnboundLocalError as exc:
        return ("raised", "UnboundLocalError: %s" % (exc,))
    except Exception as exc:                      # noqa: BLE001 - see below
        if "locals" not in box:
            # raised before the flag was final: the unchanged
            # `unmatched left parenthesis` guard (or a parse-time failure of
            # the surrounding machinery). Outside the modeled slice.
            return ("excluded", "%s: %s" % (type(exc).__name__, exc))
    finally:
        # CPython unsets the trace function when a trace callback raises, so
        # it is (re)installed per call and cleared here unconditionally.
        sys.settrace(None)
    if "locals" not in box:
        return ("excluded", "flag line never reached")
    loc = box["locals"]
    # --- bridge: real locals -> the model's (entered, key) carrier ----------
    entered = "olds" in loc          # `olds = s` is the guard block's own local
    if "kern" in loc:
        key = loc["kern"] in loc["s"]   # the real membership test `kern in s`
    else:
        key = None
    return ("ok", entered, key, loc["hit"])


# ---------------------------------------------------------------------------
# Input generation (concrete strings; the bridge derives the carrier).
# ---------------------------------------------------------------------------
BOUNDARY = [
    # --- not entered (no '(' or quoted): guard false => no key -------------
    "",                       # empty
    "x",                      # singleton
    "1",
    "x + 1",
    "x - 1/x",
    "_kern",                  # the test_kernS underscore witness
    "'x'",                    # quoted
    '"x"',
    "'(x)'",                  # has '(' but quoted => guard false
    '"2*(x + y)"',
    "' '",
    # --- entered, NO key created (no space survives the rewrite) ----------
    "(2*x)/(x-1)",            # THE F2P witness of the issue
    "(x)",
    "(a+b)",
    "(1)",
    "()",
    "(x/y)",
    "(x)+(y)",
    "((x))",
    "(_)",
    "(_+_)",
    # --- entered, key created (a rewrite injects a space) ------------------
    "2*(x + y)",
    "2*(x + y)*y",
    "-(x + 1)",
    "-(2*sin(x)**2 + 2*sin(x)*cos(x))*y/2",
    "Interval(-1,-2 - 4*(-3))",
    "x - (x - 1)",
    "(1 - x)/(1 - x*(1-y))",
    "(1-x)/(1-(1-y)*x)",
    "(1-2**-(4+1)*(1-y)*x)",
    "(1-2**(4+1)*(1-y)*x)",
    "(1-2.*(1-y)*x)",
    "E**-(x)",
    "-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))",
    ("-1 - 2*(-(-x + 1/x)/(x*(x - 1/x)**2) - 1/(x*(x - 1/x)))"
     .replace("x", "_kern")),
    # key-collision inputs: force the `while kern in s` growth loop by
    # seeding the text with the initial key character and its extensions.
    "_*(x + _)",
    "-(_ + _a)",
    "2*(_ + _0)*_1",
    "-(__ + _z9)*_",
    "_*(_a*(_b + _c))",
    # --- unmatched parentheses: the unchanged SympifyError guard, outside
    #     the modeled slice (recorded as domain-excluded, not as agreement).
    "(x",
    "x)",
    "2*(x + y",
]

ALPHABET = list("xyzab_01.*+-/() ") + ["**", "*(", "-(", "()", "  ", "_a", "_0"]
QUOTES = ["'", '"']


def balance(s):
    """Make the parenthesis counts equal so the input reaches the flag
    computation instead of tripping the unchanged unmatched-paren guard."""
    d = s.count("(") - s.count(")")
    if d > 0:
        return s + ")" * d
    if d < 0:
        return "(" * (-d) + s
    return s


def fuzz_input(rng):
    n = rng.randint(0, 14)
    s = "".join(rng.choice(ALPHABET) for _ in range(n))
    if rng.random() < 0.04:                 # exercise the `quoted` guard leg
        q = rng.choice(QUOTES)
        s = q + s + q
    return balance(s)


# ---------------------------------------------------------------------------
def enumerate_abstract_domain():
    """The model's carrier domain is finite: entered in {False, True} x key in
    {None, True, False}, restricted by the precondition
    `Implies(not entered, key is None)`.  Enumerate all 4 admissible points and
    check the shadow against the model's own `expected_signal` postcondition
    (and the `key is None ==> not Result()` postcondition)."""
    points = [(False, None), (True, None), (True, True), (True, False)]
    for entered, key in points:
        got = compute_processing_signal(entered, key)
        want = expected_signal(entered, key)
        if got != want:
            return points, ("abstract point (entered=%r, key=%r): shadow=%r "
                            "expected_signal=%r" % (entered, key, got, want))
        if key is None and got:
            return points, ("abstract point (entered=%r, key=None) gave a true "
                            "signal: %r" % (entered, got))
    return points, None


def main():
    try:
        from sympy.core.sympify import kernS, sympify
    except Exception as exc:                       # pragma: no cover
        print("G-CONF ERROR: the repo package is not importable (%r); this "
              "check must run in-container with PYTHONPATH=/testbed." % (exc,))
        return 1

    record_lineno, patched = locate_flag_line(kernS)
    if not patched:
        print("G-CONF FAIL: the installed sympy.core.sympify.kernS is NOT the "
              "patched function (`hit = kern in s` is not nested inside "
              "`if ' ' in s:` / no `else:` arm) — the oracle must be the "
              "patched repo function, refusing to report agreement.")
        return 1
    code_obj = kernS.__code__

    # --- the finite abstract domain, enumerated exhaustively ---------------
    points, err = enumerate_abstract_domain()
    if err is not None:
        print("G-CONF FAIL: shadow disagrees with the model postcondition on "
              "the enumerated abstract domain: %s" % err)
        return 1

    # --- the F2P witness, end to end through the REAL patched function -----
    f2p = "(2*x)/(x-1)"
    try:
        real_out = kernS(f2p)             # pre-patch: UnboundLocalError here
    except UnboundLocalError as exc:
        print("G-CONF FAIL: the real kernS(%r) raised UnboundLocalError (%s) "
              "while the shadow returns the false signal — the modeled "
              "no-substitution path is not total in the installed repo."
              % (f2p, exc))
        return 1
    if real_out != sympify(f2p):
        print("G-CONF FAIL: real patched kernS(%r) = %r, expected %r"
              % (f2p, real_out, sympify(f2p)))
        return 1

    rng = random.Random(SEED)
    seen = {}                             # abstract state -> witnessing string
    disagreements = []
    checked = 0
    excluded = 0
    inputs = list(BOUNDARY)
    idx = 0
    while checked < N_INPUTS:
        if idx < len(inputs):
            s_in = inputs[idx]
        else:
            s_in = fuzz_input(rng)
        idx += 1
        obs = observe_real(kernS, code_obj, record_lineno, s_in)
        if obs[0] == "excluded":
            excluded += 1
            continue
        if obs[0] == "raised":
            # The real function blew up computing the flag (the pre-patch
            # unbound read).  The shadow always returns a value, so this is a
            # disagreement, not an excluded input.
            disagreements.append((s_in, "n/a", "n/a",
                                  "shadow=<a value>", "real raised %s" % obs[1]))
            checked += 1
            if len(disagreements) >= MAX_REPORT:
                break
            continue
        _, entered, key, real_hit = obs
        checked += 1
        # the model precondition, CHECKED against the real code, not assumed
        if (not entered) and key is not None:
            disagreements.append((s_in, entered, key, "n/a",
                                  "real code bound a key with the guard not "
                                  "entered (violates Implies(not entered, "
                                  "key is None))"))
            if len(disagreements) >= MAX_REPORT:
                break
            continue
        seen.setdefault((entered, key), s_in)
        shadow_hit = compute_processing_signal(entered, key)
        if shadow_hit != real_hit:
            disagreements.append((s_in, entered, key,
                                  "shadow=%r" % (shadow_hit,),
                                  "real hit=%r" % (real_hit,)))
            if len(disagreements) >= MAX_REPORT:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) between the model.py impl "
              "shadow and the real patched kernS flag computation "
              "(seed=%d, %d inputs driven):"
              % (len(disagreements), SEED, checked))
        for s_in, entered, key, sh, real in disagreements:
            print("  input=%r  bridge(entered=%r, key=%r)  %s  %s"
                  % (s_in, entered, key, sh, real))
        return 1

    # A run that never took a branch would certify nothing: demand a real
    # witness for every abstract state reachable in the repo.
    required = [(False, None), (True, None), (True, True)]
    missing = [p for p in required if p not in seen]
    if missing:
        print("G-CONF FAIL: no real input witnessed the abstract state(s) %r "
              "— the run did not exercise every reachable branch of the "
              "modeled flag computation." % (missing,))
        return 1

    unwitnessed = [p for p in points if p not in seen]
    print("witnesses: " + "; ".join(
        "(entered=%r, key=%r) <- %r" % (e, k, seen[(e, k)])
        for (e, k) in sorted(seen, key=lambda p: (p[0], str(p[1])))))
    print("G-CONF OK: model.py impl shadow (verbatim, contracts stripped) "
          "agrees with the REAL patched sympy.core.sympify.kernS flag "
          "computation on %d driven inputs (seed=%d, %d domain-excluded "
          "unmatched-paren inputs), all 4 abstract-domain points enumerated, "
          "every repo-reachable abstract state witnessed%s; 0 disagreements."
          % (checked, SEED, excluded,
             "" if not unwitnessed else
             " (unreachable in the repo, hence unwitnessed: %r)" % (unwitnessed,)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
