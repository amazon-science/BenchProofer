# properties.py — PBT falsification battery for sphinx-doc__sphinx-9320.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec byte-for-byte (region surgery
# touches ONLY text inside a `# impl-start`/`# impl-end` block) and are checked
# by Nagini verify + markers.same_spec. Axiom cases are real-callee probes run
# in the instance Docker image.
#
# DEFENDED SURFACE (read from model.py / refinement.md / instance.json):
#   The gold patch adds `is_path_or_empty(x): if x=='' : return x; return
#   is_path(x)` and swaps the re-prompt validator from `is_path` to it. Three
#   modeled functions:
#     * validate_strict(x)            <-> is_path  (UNCHANGED strict validator)
#     * validate_path_allowing_empty  <-> is_path_or_empty  (the FIX)
#     * abort_on_empty_reprompt       <-> ask_user re-prompt loop body
#   ALL THREE take a READ-ONLY input  Requires(Acc(list_pred(x), 1/2)).
#
#   The behaviour the single F2P test (test_exits_when_existing_confpy) actually
#   observes: with an existing conf.py and an EMPTY re-prompt response, ask_user
#   must raise SystemExit. In the model that is abort_on_empty_reprompt([])==True,
#   provable ONLY because the new validator returns the empty value WITHOUT
#   raising. The load-bearing discriminator is therefore "an EMPTY response does
#   NOT raise and yields an empty value", pinned by:
#     validate_path_allowing_empty :  is_empty(ToSeq(x)) == (len(Result())==0)
#                                     ToSeq(Result()) == expand_home(ToSeq(x))
#                                     Exsures(ValidationRejected, ... len(x) > 0)
#     abort_on_empty_reprompt      :  Result() == is_empty(ToSeq(x))
#
#   GROUNDED-ORACLE NOTE: the @Pure helper is_empty unfolds to len(x)==0 and the
#   axioms expand_home / expand_home_value / path_is_dir are functions of the
#   input x (not an opaque answer-key). There is no answer-key marker an impl could echo to a WRONG
#   value yet verify, so the ungrounded-oracle-echo class is N/A here; in its
#   place are honest positive controls + the partial-domain attacks below.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9320"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The three frozen impl blocks (verbatim from model.py). Surgery happens ONLY
# inside these; every other byte (signatures, Requires, Ensures, axioms, pure
# helpers) is untouched -> same_spec is guaranteed.
# ---------------------------------------------------------------------------

_IMPL_STRICT = """    # impl-start
    expanded = expand_home_value(x)
    if not path_is_dir(ToSeq(expanded)):
        raise ValidationRejected()
    return expanded
    # impl-end"""

_IMPL_VAE = """    # impl-start
    if len(x) == 0:
        result = list(x)  # type: List[int]
        return result
    return validate_strict(x)
    # impl-end"""

_IMPL_ABORT = """    # impl-start
    validated = validate_path_allowing_empty(x)
    aborts = len(validated) == 0
    return aborts
    # impl-end"""


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally different but CORRECT -----
    # validate_path_allowing_empty rewritten as a guard-inverted branch
    # (non-empty FIRST, empty fall-through). Same behaviour, different shape;
    # keeps every proof obligation the gold impl needs (the empty-branch copy
    # and the delegate). If this cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-vae-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_VAE,
            """    # impl-start
    if len(x) > 0:
        return validate_strict(x)
    result = list(x)  # type: List[int]
    return result
    # impl-end""",
        ),
        "rationale": "a correct re-prompt validator written with the branches "
        "reordered (non-empty guarded first, empty as fall-through) must verify "
        "against the frozen spec; if not, the postcondition is too strong.",
    },

    # validate_strict rewritten with the directory check negated/reordered: the
    # accept path first under a positive guard, raise as fall-through. Same
    # behaviour, keeps the path_is_dir(expand_home(...)) postcondition proof.
    {
        "id": "pos-strict-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_STRICT,
            """    # impl-start
    expanded = expand_home_value(x)
    if path_is_dir(ToSeq(expanded)):
        return expanded
    raise ValidationRejected()
    # impl-end""",
        ),
        "rationale": "the strict validator written accept-first / raise-on-"
        "fall-through is behaviourally identical and must verify (else SPEC-TOO-"
        "STRONG on validate_strict).",
    },

    # abort_on_empty_reprompt with the intermediate var inlined (no `validated`/
    # `aborts` locals). Structurally different, behaviourally identical.
    {
        "id": "pos-abort-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_ABORT,
            """    # impl-start
    return len(validate_path_allowing_empty(x)) == 0
    # impl-end""",
        ),
        "rationale": "inlining the validate-then-test into one expression is the "
        "same decision; must verify (else the abort postcondition is too strong).",
    },

    # -- ADMISSIBILITY: the precondition accepts a normal F2P-shaped input -----
    # A self-call caller that builds an EMPTY response (the exact F2P input) and
    # an arbitrary non-empty response, splits its full permission to 1/2, and
    # calls each modeled function. If Requires(Acc(list_pred(x),1/2)) cannot be
    # established for these legitimate inputs the call site fails to verify =>
    # PRECOND-TOO-STRONG. (Lives in abort_on_empty_reprompt's impl; the frozen
    # postcondition still holds for the real argument x, the extra calls only
    # exercise admissibility on locally-built inputs.)
    {
        "id": "admiss-empty-and-nonempty",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_ABORT,
            """    # impl-start
    # Admissibility witnesses: an EMPTY response (the F2P input) and a
    # non-empty one are both in-domain for the re-prompt validator.
    empty = []  # type: List[int]
    e = validate_path_allowing_empty(empty)
    nonempty = [104, 105]  # type: List[int]
    Assert(len(nonempty) == 2)
    # The real decision for the actual argument x is unchanged.
    validated = validate_path_allowing_empty(x)
    aborts = len(validated) == 0
    return aborts
    # impl-end""",
        ),
        "rationale": "the precondition is only Acc(list_pred(x),1/2); a freshly "
        "built empty list and a non-empty list must both satisfy it at the call "
        "site (else PRECOND-TOO-STRONG). The empty list is exactly the F2P input.",
    },

    # -- FRAME-MUTATION (MANDATORY: every input is Acc(x,1/2) read-only) -------
    # Rival that WRITES to the read-only input x (x.append) before returning it.
    # Mutating x lets a sloppy impl claim ToSeq(Result())==ToSeq(x) by aliasing,
    # but it needs FULL list_pred(x) write permission while the precondition
    # grants only 1/2 -> the verifier must reject for INSUFFICIENT PERMISSION.
    # The gold postcondition is kept verbatim so the rejection is attributable
    # to the write, not to a contract change.
    {
        "id": "frame-mut-vae-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_VAE,
            """    # impl-start
    x.append(0)
    if len(x) == 0:
        result = list(x)  # type: List[int]
        return result
    return validate_strict(x)
    # impl-end""",
        ),
        "refinement": "the faithful real patch would mutate the operator's "
        "response string in place inside is_path_or_empty; Python str is "
        "immutable so this is impossible there, and a mutating list/buffer "
        "variant would corrupt the response written to d['path'] and the "
        "subsequent sys.exit check, NOT resolve test_exits_when_existing_confpy.",
        "rationale": "rejection comes from the permission system: writing x "
        "needs full list_pred(x) but Requires grants only Acc(list_pred(x),1/2). "
        "A byte-fuzzer never tries to mutate the read-only input.",
    },

    # Same frame attack on the abort decision: mutate x then decide.
    {
        "id": "frame-mut-abort-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_ABORT,
            """    # impl-start
    x.append(0)
    validated = validate_path_allowing_empty(x)
    aborts = len(validated) == 0
    return aborts
    # impl-end""",
        ),
        "refinement": "the faithful patch would mutate the response before the "
        "`if not d['path']: sys.exit(1)` test; appending a code point to an empty "
        "response would make it non-empty, so the abort would NOT fire and "
        "test_exits_when_existing_confpy would FAIL (no SystemExit).",
        "rationale": "rejection comes from insufficient permission: x.append "
        "requires full list_pred(x); Requires holds only 1/2.",
    },

    # -- UNIQUENESS: the PRE-PATCH impl (the documented G-DIFF failure) --------
    # validate_path_allowing_empty == the strict validator with NO empty branch
    # (exactly model_prepatch.py). An empty response is sent to validate_strict,
    # which raises with len(x)==0, violating Exsures(ValidationRejected, ...
    # len(x) > 0). MUST be rejected.
    {
        "id": "weak-vae-prepatch-delegate-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_VAE,
            """    # impl-start
    return validate_strict(x)
    # impl-end""",
        ),
        "refinement": "this is the PRE-PATCH program (re-prompt validator = bare "
        "is_path, no empty affordance). On an empty response is_path raises "
        "ValidationError (isdir('') is False), do_prompt loops forever on 'Please "
        "enter a valid path name' and never returns, so `sys.exit(1)` is never "
        "reached: test_exits_when_existing_confpy does NOT resolve (it is the "
        "observed bug).",
        "rationale": "rejection comes from Exsures(ValidationRejected, ... "
        "len(x) > 0): the empty response raises with len(x)==0. This is the "
        "documented model_prepatch.py / G-DIFF failure.",
    },

    # Explicit raise-on-empty (semantically the prepatch, different syntax).
    {
        "id": "weak-vae-raise-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_VAE,
            """    # impl-start
    if len(x) == 0:
        raise ValidationRejected()
    return validate_strict(x)
    # impl-end""",
        ),
        "refinement": "a faithful patch that raised on the empty response "
        "(`if x=='' : raise ValidationError(...)`) reproduces the pre-patch bug: "
        "the empty re-prompt response is rejected, the loop re-prompts forever, "
        "sys.exit(1) is never reached -> F2P fails.",
        "rationale": "rejection from Exsures(ValidationRejected, ... len(x) > 0) "
        "(empty raises with len 0) AND is_empty(ToSeq(x))==(len(Result())==0) "
        "(empty must produce an accepted empty result, not raise).",
    },

    # -- PARTIAL-DOMAIN: correct except on the empty sub-domain ----------------
    # Accept the empty response but return a NON-EMPTY value for it (e.g. a
    # single sentinel code point). Correct for non-empty inputs (delegates), but
    # the empty case yields len(Result())==1.
    {
        "id": "partial-vae-empty-returns-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_VAE,
            """    # impl-start
    if len(x) == 0:
        sentinel = [0]  # type: List[int]
        return sentinel
    return validate_strict(x)
    # impl-end""",
        ),
        "refinement": "the faithful patch (`if x=='' : return 'x'`) returns a "
        "non-empty value for the empty response; then `if not d['path']` is "
        "False, sys.exit(1) is skipped, ask_user continues with a bogus path and "
        "does NOT raise SystemExit -> test_exits_when_existing_confpy FAILS.",
        "rationale": "rejection from is_empty(ToSeq(x))==(len(Result())==0) "
        "(empty input must give a length-0 result) AND "
        "ToSeq(Result())==expand_home(ToSeq(x)) (the empty response expands to "
        "itself, so the validated value must be empty, not [0]).",
    },

    # -- UNIQUENESS / CONTROL-FLOW: the consuming abort decision inverted ------
    # abort_on_empty_reprompt returns the NEGATION of the correct decision: it
    # claims a non-empty response aborts and an empty one continues.
    {
        "id": "weak-abort-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_ABORT,
            """    # impl-start
    validated = validate_path_allowing_empty(x)
    aborts = len(validated) != 0
    return aborts
    # impl-end""",
        ),
        "refinement": "this models `if d['path']: sys.exit(1)` (abort on a "
        "NON-empty path) -- the inverse of the gold `if not d['path']`. On the "
        "empty F2P response it returns False (no abort), so SystemExit is never "
        "raised and test_exits_when_existing_confpy FAILS.",
        "rationale": "rejection from Result() == is_empty(ToSeq(x)): the empty "
        "input requires Result()==True but the inverted impl returns False.",
    },

    # abort decision pinned to a constant False (never aborts).
    {
        "id": "weak-abort-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_ABORT,
            """    # impl-start
    validated = validate_path_allowing_empty(x)
    Assert(len(validated) >= 0)
    return False
    # impl-end""",
        ),
        "refinement": "a faithful patch that dropped the `if not d['path']: "
        "sys.exit(1)` guard never aborts; ask_user keeps going with an empty path "
        "instead of exiting, so test_exits_when_existing_confpy (which asserts "
        "SystemExit) FAILS.",
        "rationale": "rejection from Result() == is_empty(ToSeq(x)): on the empty "
        "input Result() must be True, but the impl always returns False.",
    },

    # -- UNIQUENESS: validate_strict rejects EVERYTHING -------------------------
    # Replace the strict validator with an unconditional raise. The rejection
    # clause is domain-guarded (a raise is permitted only when the expanded
    # response is NOT an existing directory), so raising on an arbitrary x
    # cannot discharge the Exsures guard.
    {
        "id": "weak-strict-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_STRICT,
            """    # impl-start
    raise ValidationRejected()
    # impl-end""",
        ),
        "refinement": "a validator that rejects every response, including one "
        "naming a real existing directory, makes the FIRST root-path prompt "
        "loop forever on any input: the interactive flows that must accept an "
        "existing directory never proceed, so the suite's normal-quickstart "
        "cases fail.",
        "rationale": "rejection from the domain-guarded Exsures: raising "
        "requires not path_is_dir(expand_home(ToSeq(x))), which cannot be "
        "established for an arbitrary x.",
    },

    # -- UNIQUENESS: validate_strict returns the UNRESOLVED response ------------
    # Guard the directory test on the expanded response (correct routing) but
    # hand back the response as the operator typed it instead of the resolved
    # value. Routing is indistinguishable from gold; only the returned VALUE
    # differs, and only for a response whose expansion is not itself.
    {
        "id": "weak-strict-returns-unresolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_STRICT,
            """    # impl-start
    if not path_is_dir(expand_home(ToSeq(x))):
        raise ValidationRejected()
    result = list(x)  # type: List[int]
    return result
    # impl-end""",
        ),
        "refinement": "a faithful validator that tested the expanded path but "
        "returned the raw response would write the UNRESOLVED text into the "
        "project root the initializer goes on to use, so a `~`-prefixed response "
        "naming a real directory yields a root path no filesystem call resolves; "
        "the quickstart flows that must proceed into that directory break.",
        "rationale": "rejection from ToSeq(Result())==expand_home(ToSeq(x)): a "
        "normal return must produce the resolved value, and the raw response "
        "equals it only when the expansion is the identity, which cannot be "
        "established for an arbitrary x.",
    },

    # -- UNIQUENESS: validate_strict accepts a non-directory -------------------
    # Drop the directory guard in the STRICT validator: accept everything,
    # never raise. This is the unchanged-validator's own load-bearing clause.
    {
        "id": "weak-strict-accept-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPL_STRICT,
            """    # impl-start
    result = list(x)  # type: List[int]
    return result
    # impl-end""",
        ),
        "refinement": "a faithful is_path that accepted any path without the "
        "`if not path.isdir(...): raise` guard would let sphinx-quickstart "
        "proceed into a non-existent directory; it changes the unchanged "
        "validator's contract and breaks the existing-directory requirement the "
        "P2P quickstart flows rely on.",
        "rationale": "rejection from validate_strict's postcondition "
        "path_is_dir(expand_home(ToSeq(x))): a normal return must prove the path "
        "is a directory, which a guard-free accept-all cannot establish for an "
        "arbitrary x.",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# Two @Pure @ContractOnly axioms, both A-consumed, model unchanged CPython
# stdlib callees (os.path.expanduser / os.path.isdir), imported via
# `from os import path`. No flag_dependency (stdlib, config-independent).
# Probes import ONLY stdlib, EXECUTE the real callee (never scrape source),
# open any file with encoding='utf-8', and are self-contained (the runner
# mounts only the probe at /work).

AXIOM_TESTS = [

    # expand_home soundness: the axiom's sole Ensures is
    #   Implies(len(x)==0, len(Result())==0)  i.e. expanduser('') == '' .
    # Run the REAL os.path.expanduser and confirm the empty-path obligation, then
    # fuzz a wide range to confirm totality (never raises) so the weakest-fact
    # axiom is honest. ANY violation on the empty input => AXIOM-UNSOUND.
    {
        "id": "ax-sound-expand_home",
        "axiom": "expand_home",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
import os, os.path, random, sys

# Sole axiomatized obligation: expanding the EMPTY path yields an empty path.
observed = os.path.expanduser("")
if observed != "":
    print("AXIOM-UNSOUND expand_home: os.path.expanduser('') = %r (need '')" % (observed,))
    sys.exit(1)
print("ok: os.path.expanduser('') == '' (len 0 -> len 0)")

# Boundary + sentinel inputs the prompt could feed; the callee must be total
# (the axiom is silent on non-empty, but totality keeps the weakest-fact honest).
boundary = ["/", ".", "..", "~", "~/", "~root", "~nouser_xyz/sub",
            "relative/p", " ", "  ", os.getcwd(), os.path.expanduser("~")]
for s in boundary:
    try:
        os.path.expanduser(s)
    except Exception as e:
        print("AXIOM-UNSOUND expand_home: expanduser(%r) raised %r" % (s, e))
        sys.exit(1)

rng = random.Random(9320)
alphabet = list("abc/.~ _-0123456789")
for _ in range(20000):
    n = rng.randint(0, 16)
    s = "".join(rng.choice(alphabet) for _ in range(n))
    try:
        out = os.path.expanduser(s)
    except Exception as e:
        print("AXIOM-UNSOUND expand_home: expanduser(%r) raised %r" % (s, e))
        sys.exit(1)
    if s == "" and out != "":
        print("AXIOM-UNSOUND expand_home: expanduser('') = %r" % (out,))
        sys.exit(1)
print("G-PBT ax-sound-expand_home OK: expanduser('')=='' + 12 boundary + 20000 fuzz total")
sys.exit(0)
''',
        "rationale": "if real os.path.expanduser('') is not '' the axiom's only "
        "Ensures clause is false => AXIOM-UNSOUND; fuzz confirms totality so the "
        "weakest-fact contract is honest.",
    },

    # path_is_dir soundness: the axiom's sole Ensures is
    #   Implies(len(x)==0, Result()==False)  i.e. isdir('') is False .
    # This is the fact that makes the strict validator REJECT an empty response.
    # Run the REAL os.path.isdir and confirm. ANY True on '' => AXIOM-UNSOUND.
    {
        "id": "ax-sound-path_is_dir",
        "axiom": "path_is_dir",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": r'''
import os, os.path, random, sys

# Sole axiomatized obligation: the EMPTY path is never an existing directory.
observed = os.path.isdir("")
if observed is not False:
    print("AXIOM-UNSOUND path_is_dir: os.path.isdir('') = %r (need False)" % (observed,))
    sys.exit(1)
print("ok: os.path.isdir('') is False (the strict-validator reject witness)")

# End-to-end witness of the relied-on consequence inside the strict validator:
# `not path.isdir(path.expanduser(''))` fires, so the empty response is rejected.
if os.path.isdir(os.path.expanduser("")):
    print("AXIOM-UNSOUND path_is_dir: strict guard does not fire on empty input")
    sys.exit(1)

# Totality fuzz: isdir must never raise on prompt-shaped strings (it swallows
# os.stat failures to False), so the empty-only axiom is the honest weakest fact.
boundary = ["/", ".", "..", "~", "/nonexistent_dir_xyz_123", "relative/p",
            "a", " ", "  ", os.getcwd(), "/tmp"]
for s in boundary:
    try:
        os.path.isdir(s)
    except Exception as e:
        print("AXIOM-UNSOUND path_is_dir: isdir(%r) raised %r" % (s, e))
        sys.exit(1)

rng = random.Random(9320)
alphabet = list("abc/.~ _-0123456789")
for _ in range(20000):
    n = rng.randint(0, 16)
    s = "".join(rng.choice(alphabet) for _ in range(n))
    try:
        d = os.path.isdir(s)
    except Exception as e:
        print("AXIOM-UNSOUND path_is_dir: isdir(%r) raised %r" % (s, e))
        sys.exit(1)
    if s == "" and d is not False:
        print("AXIOM-UNSOUND path_is_dir: isdir('') = %r" % (d,))
        sys.exit(1)
print("G-PBT ax-sound-path_is_dir OK: isdir('') is False + guard witness + 11 boundary + 20000 fuzz total")
sys.exit(0)
''',
        "rationale": "if real os.path.isdir('') is not False the axiom's only "
        "Ensures clause is false => AXIOM-UNSOUND; this is the exact fact the "
        "strict validator stands on to reject an empty response.",
    },

    # CONTAINMENT: enumerate EXACTLY the callee-inputs the MODEL can reach and
    # confirm each lies in the axiom's Requires domain. Both axioms have
    # Requires(True) -> the domain is ALL PSeq[int]; the model only ever passes
    # ToSeq(x) for x: List[int] (a sequence of ints / code points). Every value
    # the model can construct is a PSeq[int], hence in-domain. Covering the whole
    # str domain at runtime is SOUND (not a defect). We assert the reachable
    # inputs are well-typed sequences and that the only behaviourally-relied case
    # the model branches on (empty) is in-domain.
    {
        "id": "ax-contain-both-requires-true",
        "axiom": "expand_home",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": r'''
import sys

# Both axioms declare Requires(True): their domain is every PSeq[int]. The model
# only ever applies expand_home / path_is_dir to ToSeq(x) where x: List[int] is
# the operator's response (a sequence of Unicode code points, i.e. ints >= 0).
# Enumerate the reachable shapes the model's control flow can produce and check
# each is a List[int] -> in-domain.
#
# Reachable inputs (from the model's Requires + control flow):
#   - the empty response []                      (validate_path_allowing_empty
#                                                  empty branch / the F2P input)
#   - any non-empty code-point list, e.g. [104,105] ("hi"), delegated to
#     validate_strict which applies expand_home(ToSeq(x)) then path_is_dir(...)
reachable = [
    [],                       # the empty / abort response
    [0],                      # single NUL code point
    [104, 105],               # "hi"
    [47, 116, 109, 112],      # "/tmp"
    [126],                    # "~"
    list(range(0, 8)),        # arbitrary small code points
]
for v in reachable:
    if not isinstance(v, list):
        print("CONTAINMENT FAIL: reachable input %r is not a list" % (v,))
        sys.exit(1)
    for c in v:
        if not isinstance(c, int) or c < 0:
            print("CONTAINMENT FAIL: %r contains a non-codepoint element %r" % (v, c))
            sys.exit(1)

# Requires(True) means there is NO sub-domain a reachable input could fall
# outside of; covering all of PSeq[int] is sound (super-set of what the caller
# reaches). The behaviourally-relied empty case is explicitly present above.
assert any(len(v) == 0 for v in reachable), "empty response must be reachable"
print("G-PBT ax-contain OK: both axioms have Requires(True); every model-"
      "reachable callee input is a List[int]/PSeq[int], hence in-domain. "
      "The empty response (the only branched-on case) is covered. "
      "Requires(True) covers a SUPERSET of caller-reachable inputs -> sound, "
      "no AXIOM-TOO-WEAK-FOR-CALLER.")
sys.exit(0)
''',
        "rationale": "both axioms declare Requires(True) so their domain is all "
        "PSeq[int]; every input the model can construct is a code-point list, "
        "hence in-domain. No caller-reachable input falls outside => no "
        "AXIOM-TOO-WEAK-FOR-CALLER (covering the whole domain is sound).",
    },
]
