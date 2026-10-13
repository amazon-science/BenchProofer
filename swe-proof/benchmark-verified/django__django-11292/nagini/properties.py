"""PBT falsification battery for django__django-11292.

NOT a Nagini module; an adversarial manifest the runner (swebench_nagini.pbt)
parses. Spec cases are full model.py variants built by region-surgery: each
swaps text ONLY inside an `# impl-start`/`# impl-end` region, so the frozen spec
(axioms/pure/pre/post-conditions, the spec_view) is byte-identical and
`markers.same_spec(base, variant)` holds. A spec case "passes" iff its verify
outcome matches `expect` (verify => must verify; reject => must NOT verify).

DEFENDED SURFACE (what this spec actually pins)
-----------------------------------------------
Two modeled functions, both over the boolean cross-product:

  parser_offers_skip(requires_validation: bool) -> bool
      post: Result() == requires_validation
            Result() == skip_request_offered(requires_validation)   # == rv (unfolded)
      => the output is FULLY pinned for both inputs (rv in {T,F}).

  will_run_validation(requires_validation: bool, requested_skip: bool) -> bool
      post: Result() == (requires_validation and not effective_skip(rv, rs))
            Implies(not rv, not Result())
            Implies(rv and rs, not Result())     # THE discriminating clause (the fix)
            Implies(rv and not rs, Result())
      effective_skip(rv, rs) unfolds to (rv and rs), so the load-bearing equality
      pins the output for ALL FOUR (rv, rs) combinations:
            (F,*) -> False ;  (T,F) -> True ;  (T,T) -> False.

Both functions are pure boolean logic; there are NO heap/reference parameters
(both args are pass-by-value `bool`), hence NO `Acc(x, 1/2)` read-only input and
NO frame to mutate. FRAME-MUTATION is therefore not applicable here (see
assessment) and is omitted with justification rather than faked.

The "oracle" helpers (skip_request_offered, effective_skip) are @Pure and fully
GROUNDED in the inputs (each unfolds to a boolean function of rv/rs). There is no
opaque answer-key to echo: any echo of the helper IS the correct value, so an
"ungrounded-oracle echo" rival cannot exist. We instead supply honest cheapest
positive controls (echo the grounded helper) which MUST verify.

The real adversarial leverage is PARTIAL-DOMAIN: a rival correct on 3 of the 4
(rv, rs) combinations but diverging on a single combination — most importantly
the discriminating combination (rv=T, rs=T) that the whole gold change exists to
fix. Each such rival corresponds to a faithful real patch that would NOT resolve
the F2P (`test_skip_checks`), and the spec MUST reject it.
"""
from pathlib import Path

INSTANCE = "django__django-11292"
FLOAT_ENCODING = None  # meta.json float_encoding is null; unused here.

_BASE = (Path(__file__).parent / "model.py").read_text()

# The two impl regions in the frozen model.py (verbatim, unique).
_POS_IMPL = """\
    if requires_validation:
        return True
    return False"""

_WRV_IMPL = """\
    skip = parser_offers_skip(requires_validation) and requested_skip
    if requires_validation and not skip:
        return True
    return False"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


def _pos(new_impl):
    """Variant that swaps ONLY parser_offers_skip's impl region."""
    return _swap(_BASE, _POS_IMPL, new_impl)


def _wrv(new_impl):
    """Variant that swaps ONLY will_run_validation's impl region."""
    return _swap(_BASE, _WRV_IMPL, new_impl)


SPEC_TESTS = [
    # ----------------------------------------------------------------- POSITIVE CONTROLS
    {
        "id": "pos-pos-bool-collapse",
        "kind": "soundness",
        "expect": "verify",
        # parser_offers_skip: structurally collapse the if/return into the direct
        # boolean (a different executable shape; same value for both inputs). MUST
        # verify against the fully-grounded postcondition.
        "module": _pos("    return requires_validation"),
        "rationale": ("a structurally-different but CORRECT impl of parser_offers_skip "
                      "(direct boolean instead of if/else) must satisfy the fully-grounded "
                      "post Result()==requires_validation; if it cannot, SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-wrv-direct-boolean",
        "kind": "soundness",
        "expect": "verify",
        # will_run_validation: drop the intermediate `skip` and the if/else; return
        # the grounded boolean directly. parser_offers_skip(rv)==rv is provable from
        # its post, so this equals (rv and not (rv and rs)) == (rv and not rs) == gold.
        "module": _wrv("    return requires_validation and not (parser_offers_skip(requires_validation) and requested_skip)"),
        "rationale": ("a different executable shape (no temp, no branch) that is still the "
                      "exact gold decision must verify; else SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-wrv-demorgan-nested",
        "kind": "soundness",
        "expect": "verify",
        # will_run_validation: reorder/nesting variant — explicit per-combination
        # branching that yields the identical truth table. Keeps no proof obligation
        # beyond the post (boolean logic auto-discharges); structurally different.
        "module": _wrv(
            "    if not requires_validation:\n"
            "        return False\n"
            "    if requested_skip:\n"
            "        return False\n"
            "    return True"),
        "rationale": ("branch-reordered, per-combination decision equal to the gold truth "
                      "table; a correct re-expression must verify (else SPEC-TOO-STRONG)."),
    },

    # ----------------------------------------------------------------- ADMISSIBILITY
    {
        "id": "admiss-fshaped-oracle-pin",
        "kind": "admissibility",
        "expect": "verify",
        # The precondition admits any bool and demands only termination
        # (MustTerminate(6)). A positive-control caller exercises the exact
        # F2P-shaped input (rv=True from a validating command; rs=True from the
        # --skip-checks token) and pins the honoured-skip outcome through the
        # grounded pure oracle, plus a call to the obligated callee
        # parser_offers_skip (level 2 < 6, so the level order is well-founded and
        # the call is admissible). If the precondition rejected a normal input,
        # or left no room beneath it for its own callee, this fails =>
        # PRECOND-TOO-STRONG.
        #
        # This replaces the former `admiss-self-call-fshaped`, whose probe made
        # the SAME claim through an unconditional recursive self-call. That case
        # is retained below in the reject lane: it does not terminate, so under
        # the termination obligation it is a rival the spec must now reject
        # rather than an admissibility positive control. The claim it carried is
        # preserved here in full (both F2P combinations, same expected values),
        # by a probe that terminates.
        "module": _wrv(
            "    skip = parser_offers_skip(requires_validation) and requested_skip\n"
            "    # admissibility: the F2P input (validating command + --skip-checks token)\n"
            "    # is in-domain; the obligated callee is called at a strictly lower\n"
            "    # level (2 < 6) and the honoured-skip decision is pinned through the\n"
            "    # grounded oracle. Verified non-vacuous: Assert(False) here is rejected.\n"
            "    Assert(parser_offers_skip(True) == True)\n"
            "    Assert(parser_offers_skip(False) == False)\n"
            "    Assert(effective_skip(True, True) == True)\n"
            "    Assert((True and not effective_skip(True, True)) == False)\n"
            "    Assert((True and not effective_skip(True, False)) == True)\n"
            "    if requires_validation and not skip:\n"
            "        return True\n"
            "    return False"),
        "rationale": ("the precondition (any bool + MustTerminate(6)) must admit the "
                      "F2P-shaped input (validating + skip token), must leave room beneath "
                      "it for its own obligated callee parser_offers_skip, and the pinned "
                      "F2P decision must hold; else PRECOND-TOO-STRONG."),
    },

    # ----------------------------------------------------------------- NON-TERMINATION (reject)
    {
        "id": "weak-wrv-diverging-self-call",
        "kind": "uniqueness",
        "expect": "reject",
        # DIVERGES: this rival never reaches its return. The self-call is
        # unconditional and sits ahead of every branch, and its arguments are the
        # constants (True, True) / (True, False) rather than anything derived from
        # the caller's own arguments, so no argument decreases and there is no
        # base case: entering will_run_validation immediately re-enters it at
        # (True, True), forever. Confirmed by execution against a stubbed contract
        # surface: RecursionError after 299 nested frames, return never reached.
        #
        # It cannot be repaired into an accept-lane case, and this was established
        # rather than assumed:
        #   - as written (unconditional self-call): rejected, "Obligation leak
        #     check failed. Callee will_run_validation might not take all
        #     unsatisfied obligations from the caller";
        #   - guarding the self-call so it recurses only once into a
        #     guard-failing input: STILL rejected with the same leak, because a
        #     self-call cannot be justified at its own method's level -- the
        #     callee needs a strictly smaller level than the caller and here they
        #     are the same method, so no level assignment is well-founded. The
        #     guard was feasible, not vacuously dead: the Assert(False) control in
        #     that same position was rejected ("Assertion False might not hold").
        # Raising the level does not help: the requirement is strict inequality
        # between caller and callee, which self-recursion cannot satisfy without a
        # decreasing measure the spec cannot see.
        #
        # This case previously lived in the ACCEPT lane as
        # `admiss-self-call-fshaped`, an admissibility positive control authored
        # against a specification that demanded nothing of termination, so it
        # never had to prove any. It is moved rather than deleted: a variant that
        # never returns IS a wrong implementation, and asserting that the
        # specification REJECTS it is a strictly stronger claim than asserting the
        # specification accepts it. Its admissibility claim is not lost -- it is
        # re-made, over both F2P combinations, by `admiss-fshaped-oracle-pin`
        # above, which terminates.
        "module": _wrv(
            "    skip = parser_offers_skip(requires_validation) and requested_skip\n"
            "    # admissibility: the F2P input (validating command + --skip-checks token)\n"
            "    # is in-domain and the call is well-formed (empty precondition).\n"
            "    Assert(will_run_validation(True, True) == False)\n"
            "    Assert(will_run_validation(True, False) == True)\n"
            "    if requires_validation and not skip:\n"
            "        return True\n"
            "    return False"),
        "refinement": ("A real patch shaped like this never returns a gating decision at all: "
                       "the management command would hang before deciding whether to run system "
                       "checks, so test_skip_checks never completes and the F2P is NOT resolved. "
                       "Under PARTIAL correctness such a rival satisfied every Ensures vacuously "
                       "-- the postconditions are claimed only of runs that REACH the return -- "
                       "so it VERIFIED while its faithful patch hung. This is exactly the hole "
                       "the MustTerminate obligation exists to close."),
        "rationale": ("must be rejected because it cannot discharge MustTerminate(6): the "
                      "unconditional self-call leaks the caller's unsatisfied obligation "
                      "(no strictly-smaller level exists for a self-call). If it verifies, the "
                      "termination obligation is absent or toothless => SPEC-TOO-WEAK."),
    },

    # ----------------------------------------------------------------- PARTIAL-DOMAIN (reject)
    {
        "id": "weak-wrv-drop-skip-discriminating",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central attack: the pre-fix gate that IGNORES the skip request and runs
        # validation whenever required (correct on 3/4 combos, wrong on rv=T,rs=T).
        # This is exactly model_prepatch_2.py's behaviour.
        "module": _wrv(
            "    if requires_validation:\n"
            "        return True\n"
            "    return False"),
        "refinement": ("This is the literal pre-fix behaviour: `requires_system_checks and "
                       "not options.get('skip_checks')` was effectively `if requires_system_checks` "
                       "before the request could ever be in force. A real patch with this gate runs "
                       "self.check() for a validating command even when --skip-checks was passed, so "
                       "test_skip_checks (validating command + broken STATICFILES_DIRS + --skip-checks "
                       "expecting clean run) STILL ERRORS => F2P NOT resolved."),
        "rationale": ("must fail the discriminating post Implies(rv and rs, not Result()) and the "
                      "equality Result()==(rv and not effective_skip(...)) at (T,T); if it verifies, "
                      "SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-wrv-inverted-skip-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        # Inverted-polarity gate: runs validation precisely when the skip was
        # requested for a validating command — the EXACT opposite of the fix at the
        # discriminating combo. Correct at (F,*) and at (T,F); wrong at (T,T).
        "module": _wrv(
            "    if requires_validation and requested_skip:\n"
            "        return True\n"
            "    if requires_validation:\n"
            "        return False\n"
            "    return False"),
        "refinement": ("A real patch that wired the gate as `requires_system_checks and "
                       "options['skip_checks']` (inverted: run checks ONLY when --skip-checks is "
                       "present) would (a) NOT run checks for a normal validating command -> the "
                       "PASS_TO_PASS default-checks behaviour breaks, and (b) RUN checks exactly when "
                       "the user asked to skip -> test_skip_checks STILL ERRORS on broken "
                       "STATICFILES_DIRS. F2P NOT resolved."),
        "rationale": ("must fail BOTH Implies(rv and rs, not Result()) at (T,T) [gold False, rival "
                      "True] and Implies(rv and not rs, Result()) at (T,F) [gold True, rival False]. "
                      "If it verifies, SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-wrv-flip-no-skip-combo",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain miss on the (rv=T, rs=F) combo: a rival that skips validation
        # even when NO skip was requested (correct at the other three combos).
        "module": _wrv(
            "    if requires_validation and requested_skip:\n"
            "        return False\n"
            "    return False"),
        "refinement": ("Always returns False (never runs validation) for a validating command. A "
                       "real patch that disables system checks unconditionally would let the "
                       "validating command run with broken settings WITHOUT skip — breaking the "
                       "PASS_TO_PASS expectation that checks run by default and admitting silently "
                       "invalid configs. It does honour the skip case, but fails the no-skip case."),
        "rationale": ("must fail Implies(rv and not rs, Result()) at (T,F): gold=True, rival=False. "
                      "If it verifies, SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-pos-constant-true",
        "kind": "uniqueness",
        "expect": "reject",
        # parser_offers_skip partial-domain: offer the skip request for EVERY command
        # (correct at rv=True, wrong at rv=False).
        "module": _pos("    return True"),
        "refinement": ("A create_parser that registers --skip-checks UNCONDITIONALLY exposes the "
                       "option even for non-validating commands. argparse would then accept "
                       "--skip-checks where the gold parser rejects it (SystemExit), changing the "
                       "help/usage and accepted-argument set for non-validating commands and "
                       "breaking their PASS_TO_PASS argument tests; the gold guards on "
                       "requires_system_checks. Faithful patch does NOT resolve cleanly."),
        "rationale": ("must fail Result()==requires_validation at rv=False (gold False, rival True). "
                      "If it verifies, SPEC-TOO-WEAK."),
    },
    {
        "id": "weak-pos-constant-false",
        "kind": "uniqueness",
        "expect": "reject",
        # parser_offers_skip partial-domain: never offer the skip request (the literal
        # pre-fix create_parser, == model_prepatch.py). Correct at rv=False, wrong at
        # rv=True.
        "module": _pos("    return False"),
        "refinement": ("This is the pre-fix create_parser with NO --skip-checks registration. The "
                       "option is never offered, so a supplied --skip-checks is dropped for a "
                       "validating command and the downstream gate runs validation regardless => "
                       "test_skip_checks errors on the broken STATICFILES_DIRS. F2P NOT resolved "
                       "(this is exactly model_prepatch.py)."),
        "rationale": ("must fail Result()==requires_validation at rv=True (gold True, rival False). "
                      "If it verifies, SPEC-TOO-WEAK."),
    },
]


# ----------------------------------------------------------------------- AXIOM LANE
# meta.json `axioms` is []: there are NO @ContractOnly consumed axioms. There is
# ONE A-reference deep model (argparse store_true exposure/default/rejection
# semantics) validated by axiom_check.py / G-AX. Per PBT_PLAN §2.4 / §4a an
# A-reference deep model is checked the same way as an axiom: the deep model must
# equal the real callee on every caller-reachable input. We run the REAL argparse
# (the very module the gold patch builds on) in the instance image and:
#   - axiom-soundness: assert the real parser's store_true exposure/default/
#     rejection semantics + the end-to-end gate decision match the model over the
#     FULL boolean cross-product the caller can reach (no disagreement allowed);
#   - axiom-containment: enumerate EXACTLY the (requires_validation, token) inputs
#     the model can reach and assert each lies in the A-reference's domain (the
#     parser only ever sees an offered token for a validating command; an
#     unregistered token is rejected, matching effective_skip==False when not
#     offered). Covering the token for a non-validating command (rejected) is the
#     SOUND over-coverage, not a defect.
#
# The runner mounts ONLY the probe at /work, so we embed axiom_check.py's source
# (read on the HOST at load time) into the probe and execute it directly. The
# probe imports only the standard library (argparse), opens nothing on disk, and
# prints a diagnostic, exiting 0 iff every obligation holds.

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_CONTAINMENT_PROBE = r'''
import sys, argparse, io, contextlib

# --- model reference encodings (lock-step with model.py spec) ----------------
def model_parser_offers_skip(rv):
    return rv

def model_effective_skip(rv, rs):
    return rs if model_parser_offers_skip(rv) else False

def model_will_run_validation(rv, rs):
    return rv and not model_effective_skip(rv, rs)

def build_real_parser(rv):
    p = argparse.ArgumentParser(prog="cmd")
    p.add_argument('--traceback', action='store_true')
    p.add_argument('--no-color', action='store_true')
    p.add_argument('--force-color', action='store_true')
    if rv:                                  # gold: if self.requires_system_checks
        p.add_argument('--skip-checks', action='store_true', help='Skip system checks.')
    return p

failures = 0

# CONTAINMENT: enumerate EXACTLY the (requires_validation, token-present) inputs
# the model/caller can reach, and assert each is inside the A-reference domain
# (argparse store_true semantics). The model reaches all 4 (rv, token) combos;
# for each we verify the real parser is in a well-defined state for that input.
for rv in (False, True):
    parser = build_real_parser(rv)
    # token absent: always parseable; store_true defaults present iff registered.
    ns = vars(parser.parse_args([]))
    registered = ('skip_checks' in ns)
    if registered != model_parser_offers_skip(rv):
        failures += 1
        print("CONTAINMENT MISS (registration): rv=%r real-registered=%r model-offers=%r"
              % (rv, registered, model_parser_offers_skip(rv)))
    if registered and ns['skip_checks'] is not False:
        failures += 1
        print("CONTAINMENT MISS (default): rv=%r store_true default=%r (expected False)"
              % (rv, ns['skip_checks']))
    # token present: in-domain ONLY when offered (rv True); when NOT offered the
    # A-reference rejects it (SystemExit) -> effective_skip drops it (==False).
    p2 = build_real_parser(rv)
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            ns2 = vars(p2.parse_args(['--skip-checks']))
            accepted = True
        except SystemExit:
            ns2 = None
            accepted = False
    if accepted != model_parser_offers_skip(rv):
        failures += 1
        print("CONTAINMENT MISS (token acceptance): rv=%r real-accepts-token=%r model-offers=%r"
              % (rv, accepted, model_parser_offers_skip(rv)))
    # the effective-skip the model would compute for this reachable input matches
    # what the real namespace yields (or the drop-on-reject semantics).
    real_effective = (ns2['skip_checks'] if accepted else False)
    if real_effective != model_effective_skip(rv, True):
        failures += 1
        print("CONTAINMENT MISS (effective_skip): rv=%r real=%r model=%r"
              % (rv, real_effective, model_effective_skip(rv, True)))

print("containment: all 4 (rv, token) reachable inputs lie in the argparse "
      "store_true A-reference domain (offered token in-domain iff rv; "
      "unregistered token rejected => effective_skip False).")
if failures:
    print("AXIOM-CONTAINMENT FAIL: %d miss(es)" % failures)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK")
sys.exit(0)
'''

# Soundness probe: run the bundle's own G-AX oracle (axiom_check.main) verbatim
# against real argparse, then ALSO fuzz the full cross-product to try to make the
# real callee DISAGREE with the deep model. Embeds axiom_check.py source.
_SOUNDNESS_PROBE = (
    _AXIOM_CHECK_SRC
    + r'''

# --- PBT extension: exhaustively fuzz the boolean cross-product + the reject path
def _pbt_extra():
    extra_failures = 0
    # full cross-product of (requires_validation, token-present); when the token is
    # not offered (rv False) the parser MUST reject it (the A-reference's domain edge).
    for rv in (False, True):
        for token in (False, True):
            ok, decision = real_run_validation(rv, token)
            offered = model_parser_offers_skip(rv)
            if token and not offered:
                # unregistered token: the real callee must reject (SystemExit) ->
                # request dropped; model effective_skip == False, gate runs iff rv.
                if ok:
                    extra_failures += 1
                    print("SOUNDNESS FAIL: unregistered --skip-checks accepted at rv=%r" % rv)
                continue
            expected = model_will_run_validation(rv, token)
            if not ok or decision != expected:
                extra_failures += 1
                print("SOUNDNESS FAIL: rv=%r token=%r real_ok=%r real=%r model=%r"
                      % (rv, token, ok, decision, expected))
    return extra_failures

if __name__ == "__main__":
    rc = main()
    if rc == 0:
        rc = 1 if _pbt_extra() else 0
        if rc == 0:
            print("AXIOM-SOUNDNESS OK: real argparse matches the deep model on the full "
                  "boolean cross-product incl. the unregistered-token reject path.")
    sys.exit(rc)
'''
)

AXIOM_TESTS = [
    {
        "id": "ax-ref-argparse-soundness",
        "axiom": "parser_offers_skip / effective_skip (argparse store_true A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": ("the deep model assumes argparse store_true: option exposed iff registered, "
                      "default False, unregistered token rejected, gate == will_run_validation over "
                      "the boolean cross-product. We run the REAL argparse (stdlib, the module the "
                      "gold patch builds on) and assert it matches the model on every reachable "
                      "input incl. the reject path. Any disagreement => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-ref-argparse-containment",
        "axiom": "parser_offers_skip / effective_skip (argparse store_true A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": ("enumerate EXACTLY the (requires_validation, token-present) inputs the model "
                      "can reach and assert each lies in the argparse store_true A-reference domain "
                      "(offered token in-domain iff rv; unregistered token rejected => effective_skip "
                      "False). A reachable input outside the domain => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
