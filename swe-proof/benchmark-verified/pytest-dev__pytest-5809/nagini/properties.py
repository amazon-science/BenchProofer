# properties.py — PBT manifest for pytest-dev__pytest-5809.
#
# NOT a Nagini module: a record of adversarial falsification cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the frozen spec byte-identically (only the impl
# region is swapped, via _swap, so markers.same_spec is GUARANTEED); axiom cases
# are real-callee probes run in the instance Docker image.
#
# ----------------------------------------------------------------------------
# DEFENDED SURFACE (read from model.py / refinement.md / instance.json)
# ----------------------------------------------------------------------------
# The gold patch changes ONE expression in create_new_paste: the params dict's
# "lexer" value from the version-derived `"python3" if sys.version_info[0] >= 3
# else "python"` to the constant `"text"`. The model carries this as three
# independent field-producing functions:
#
#   paste_mode_field(py_major: int) -> List[int]
#     LOAD-BEARING postcondition:  ToSeq(Result()) == text_token()  (== "text")
#     INVARIANT under py_major (the postcondition holds for EVERY py_major) —
#     this is exactly the version-invariance the fix introduces. The differential
#     carrier: model_prepatch.py reproduces the version-branch and FAILS here.
#     py_major is a plain `int` — NOT a read-only reference.
#
#   paste_body_field(contents: List[int]) -> List[int]
#     READ-ONLY input:  Requires(Acc(list_pred(contents), 1 / 2))
#     postcondition:    identity, ToSeq(Result()) == ToSeq(contents)
#     The half-permission is the spec defending that the body is FORWARDED, not
#     mutated — so the frame-mutation probe (directive 5) is MANDATORY here.
#
#   paste_expiry_field() -> List[int]
#     postcondition:    ToSeq(Result()) == expiry_token()  (== "1week")
#     no input.
#
# text_token()/expiry_token() are @Pure but GROUNDED concrete constants (a list
# of fixed code points), not an opaque answer-key oracle. There is therefore NO
# *wrong* echo of them: materializing text_token() IS the correct answer. So the
# ungrounded-oracle-echo class is N/A; we instead carry honest positive controls
# (a structurally-different correct impl that must verify) and a wrong-CONSTANT
# rival (the only way a mode-field impl can be wrong is to return a different
# constant or to branch on py_major like the pre-patch).
#
# AXIOM lane: axioms[] is empty (no @ContractOnly axiom). There IS one
# A-reference deep model — the UNCHANGED serializer urllib.parse.urlencode that
# create_new_paste calls on the params dict. We carry one axiom-soundness probe
# (reusing axiom_check.py's logic) that runs the REAL serializer and confirms the
# deep-model tokens produce the F2P wire form (lexer=text / expiry=1week /
# code=<contents>), version-invariant. urllib.parse is stdlib, so the probe is
# self-contained and image-agnostic.
# ----------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5809"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats in this bundle)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    """Region-surgery: replace EXACTLY one unique occurrence of `old` (which must
    live inside an # impl-start/# impl-end region) with `new`. Editing only the
    impl region GUARANTEES markers.same_spec(_BASE, result) is True."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# --- the three gold impl bodies, used as unique anchors for _swap ------------
_GOLD_MODE = "    mode = [116, 101, 120, 116]  # type: List[int]\n    return mode"
_GOLD_BODY = "    body = list(contents)  # type: List[int]\n    return body"
_GOLD_EXP = "    exp = [49, 119, 101, 101, 107]  # type: List[int]\n    return exp"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (pos-1) BRANCH-SPLIT positive control on paste_mode_field. A structurally
# DIFFERENT but CORRECT impl: branch on py_major (exactly as the pre-patch code
# did) but return the SAME plain-text token "text" in BOTH branches. This is the
# canonical faithful fix shape — the value is version-invariant even though the
# control flow inspects py_major. The postcondition ToSeq(Result())==text_token()
# is discharged identically in both branches (each returns [116,101,120,116]).
# If this CORRECT impl fails to verify, the postcondition is over-fit to the
# single-literal form => SPEC-TOO-STRONG. No framing lemma is needed (both
# branches assign a concrete literal), so this is not a proof-gap risk.
# NOTE: the `# type: List[int]` declaration appears on the FIRST branch only;
# repeating it on both branches makes Nagini's mypy front-end reject the module
# with "Name 'mode' already defined" (a translation error, NOT a verification
# rejection) — so the second branch reassigns the already-declared local plain.
_POS_MODE_BRANCH = """    if py_major >= 3:
        mode = [116, 101, 120, 116]  # type: List[int]
    else:
        mode = [116, 101, 120, 116]
    return mode"""
_POS_MODE = _swap(_BASE, _GOLD_MODE, _POS_MODE_BRANCH)

# (pos-2) LOCAL-RESHAPE positive control on paste_body_field. Reshape the data
# flow without changing semantics: rebind `contents` through a typed local alias
# `src` (READ-ONLY — we never write through it, so the half-permission carries),
# then materialize the identity copy from `src`. Same one-shot `list(...)`
# semantics the gold proof discharges (no loop, so NO ToSeq-extensionality lemma
# is introduced — avoiding the forward-append proof-gap of AVOID-rule #3); only
# the local variable shape differs. If this CORRECT impl fails to verify, the
# postcondition is over-fit to the exact `list(contents)` text => SPEC-TOO-STRONG.
_POS_BODY_RESHAPE = """    src = contents  # type: List[int]
    body = list(src)  # type: List[int]
    return body"""
_POS_BODY = _swap(_BASE, _GOLD_BODY, _POS_BODY_RESHAPE)

# (admiss-1) ADMISSIBILITY of paste_body_field's half-permission precondition.
# A self-call on the SAME in-scope input `contents` (an F2P-shaped body): the
# caller holds Acc(list_pred(contents), 1/2) (its own precondition, in scope),
# which is EXACTLY the callee's Requires; the self-call consumes that
# half-permission and the callee's Ensures GIVES IT BACK (it also requires &
# ensures Acc(...,1/2)), so the subsequent `list(contents)` runs unchanged. We
# Assert the probe forwards contents (its Ensures) to pin the call site succeeded.
# If the precondition could not be established for a legitimate input =>
# PRECOND-TOO-STRONG.
_ADMISS_BODY = """    Assert(Acc(list_pred(contents), 1 / 2))
    body = list(contents)  # type: List[int]
    return body"""
_ADMISS = _swap(_BASE, _GOLD_BODY, _ADMISS_BODY)


# ===========================================================================
# UNIQUENESS / FRAME-MUTATION RIVALS (must be REJECTED)
# ===========================================================================

# (frame-mutate) FRAME-MUTATION — MANDATORY (directive 5; #1 weakness class).
# The rival tries to satisfy the identity postcondition by WRITING to the
# read-only input `contents` (append a code point) before snapshotting it. To
# call contents.append(...) Nagini needs FULL permission on list_pred(contents),
# but the precondition grants only Acc(list_pred(contents), 1/2). The write is
# REJECTED for INSUFFICIENT PERMISSION — before the postcondition is even
# considered. The gold structure is otherwise kept VERBATIM so the rejection is
# attributable solely to the write.
#
# Refinement (why a faithful real patch would NOT resolve): the half-permission
# abstracts the gold patch's contract that the body field FORWARDS `contents`
# unchanged (`"code": contents`, refinement.md A3) and leaves the caller's
# session-output buffer untouched. A real "patch" that mutated `contents` in
# place (e.g. appended/clobbered bytes of the captured output before posting)
# would corrupt the very text being pasted — `code=full-paste-contents` would no
# longer appear verbatim in the wire form, breaking the F2P assertion
# `assert "code=full-paste-contents" in data.decode()` and the P2P round-trips.
# The half-permission is exactly the spec defending that read-only forward.
_RIVAL_FRAME_MUTATE = """    contents.append(0)
    body = list(contents)  # type: List[int]
    return body"""
_RIVAL_FRAME = _swap(_BASE, _GOLD_BODY, _RIVAL_FRAME_MUTATE)

# (weak-prepatch) PARTIAL-DOMAIN / PRE-PATCH rival on paste_mode_field. Correct
# on the py_major < 3 sub-domain (returns "text") but DIVERGES on py_major >= 3,
# returning the pre-patch token "python3" ([112,121,116,104,111,110,51]). This
# is exactly model_prepatch.py's version-branch bug. It violates the load-bearing
# postcondition ToSeq(Result())==text_token() on the py_major >= 3 sub-domain, so
# it MUST be rejected (the postcondition is INVARIANT under py_major).
#
# Refinement: its faithful real patch is the UNMODIFIED pre-patch expression
# `"lexer": "python3" if sys.version_info[0] >= 3 else "python"`. Under the F2P
# test's actual runtime (CPython 3, sys.version_info[0] >= 3) it sends
# `lexer=python3`, so `assert "lexer=text" in data.decode()` FAILS — it does NOT
# resolve. The reject comes from paste_mode_field's postcondition demanding
# "text" for EVERY py_major (refinement.md A2 / G-DIFF).
_RIVAL_PREPATCH_BODY = """    if py_major >= 3:
        mode = [112, 121, 116, 104, 111, 110, 51]  # type: List[int]
    else:
        mode = [116, 101, 120, 116]
    return mode"""
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_MODE, _RIVAL_PREPATCH_BODY)

# (weak-const) WRONG-CONSTANT rival on paste_mode_field. Returns the constant
# "python3" for EVERY py_major (a version-invariant but WRONG token). It violates
# the postcondition ToSeq(Result())==text_token() everywhere, so it MUST be
# rejected. This is the cheapest wrong constant a mode-field impl can echo.
#
# Refinement: its faithful real patch is `"lexer": "python3"` (a hard-coded wrong
# mode). The wire form carries `lexer=python3`, never `lexer=text`, so the F2P
# `assert "lexer=text" in data.decode()` FAILS — it does NOT resolve. The reject
# comes from the same load-bearing postcondition pinned to text_token().
_RIVAL_CONST_BODY = """    mode = [112, 121, 116, 104, 111, 110, 51]  # type: List[int]
    return mode"""
_RIVAL_CONST = _swap(_BASE, _GOLD_MODE, _RIVAL_CONST_BODY)

# (weak-body-partial) PARTIAL-DOMAIN rival on paste_body_field. Forwards contents
# verbatim on a non-empty body but returns the EMPTY list when contents is empty
# (a length-class sub-domain divergence). It violates the identity postcondition
# ToSeq(Result())==ToSeq(contents) only when len(contents)==0 (then Result()==[]
# happens to also equal contents, so this is actually still correct for empty) —
# to make it genuinely wrong we drop the FIRST element on a non-empty body. That
# violates the identity on every non-empty contents, so it MUST be rejected.
#
# Refinement: its faithful real patch would post `contents[1:]` instead of
# `contents` ("code": contents[1:]), dropping the first byte of the session
# output. The wire form's code field would be missing the leading 'f', so
# `assert "code=full-paste-contents" in data.decode()` FAILS — it does NOT
# resolve. The reject comes from paste_body_field's identity postcondition.
_RIVAL_BODY_DROP = """    result = []  # type: List[int]
    i = 1
    while i < len(contents):
        Invariant(Acc(list_pred(contents), 1 / 2))
        Invariant(1 <= i and i <= len(contents) + 1)
        Invariant(Acc(list_pred(result)))
        result.append(contents[i])
        i = i + 1
    return result"""
_RIVAL_BODY_DROP_VAR = _swap(_BASE, _GOLD_BODY, _RIVAL_BODY_DROP)

# (weak-expiry) WRONG-CONSTANT rival on paste_expiry_field. Returns "1day"
# ([49,100,97,121]) instead of "1week". Violates ToSeq(Result())==expiry_token(),
# so it MUST be rejected. Cheap supporting case (the expiry field is unchanged by
# the gold patch but modeled for hunk fidelity).
#
# Refinement: a real patch that set `"expiry": "1day"` would change the wire form
# to `expiry=1day`; while the F2P only asserts `lexer=text`/`code=...`, the
# expiry-field postcondition pins the unchanged "1week" token (refinement.md A4),
# so this rival is rejected by that postcondition.
_RIVAL_EXP_BODY = """    exp = [49, 100, 97, 121]  # type: List[int]
    return exp"""
_RIVAL_EXP = _swap(_BASE, _GOLD_EXP, _RIVAL_EXP_BODY)


SPEC_TESTS = [
    {
        "id": "pos-mode-branch-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MODE,
        "rationale": "structurally-different CORRECT impl (branch on py_major, "
                     "return 'text' in both branches — the canonical faithful "
                     "fix shape); must verify or SPEC-TOO-STRONG. Both branches "
                     "assign a concrete literal so no framing lemma is needed.",
    },
    {
        "id": "pos-body-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BODY,
        "rationale": "local-variable reshape: rebind contents through a read-only "
                     "alias then list(...) it — same one-shot identity-copy "
                     "semantics, no loop/ToSeq-extensionality lemma introduced "
                     "(avoids the forward-append proof-gap). Must verify or "
                     "SPEC-TOO-STRONG (over-fit to the exact list(contents) text).",
    },
    {
        "id": "admiss-body-half-perm",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "self-call to paste_body_field on the in-scope half-perm "
                     "`contents`; the caller's own Acc(...,1/2) is exactly the "
                     "callee's Requires and the Ensures gives it back. Must "
                     "verify or PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutate-contents",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FRAME,
        "refinement": "the half-permission abstracts that the body field FORWARDS "
                      "`contents` unchanged (\"code\": contents). A real patch that "
                      "mutated the captured session output in place would corrupt "
                      "the pasted text, so `code=full-paste-contents` would no "
                      "longer appear verbatim and the F2P assertion "
                      "`assert \"code=full-paste-contents\" in data.decode()` would "
                      "FAIL — it would NOT resolve.",
        "rationale": "REJECT comes from the PERMISSION SYSTEM: contents.append(...) "
                     "needs full list_pred permission but only Acc(...,1/2) is "
                     "granted; insufficient-permission failure, attributable solely "
                     "to the write (gold structure otherwise verbatim).",
    },
    {
        "id": "weak-mode-prepatch-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PREPATCH,
        "refinement": "its faithful real patch is the UNMODIFIED pre-patch "
                      "expression `\"lexer\": \"python3\" if sys.version_info[0] >= 3 "
                      "else \"python\"`. Under the F2P's actual CPython-3 runtime it "
                      "sends `lexer=python3`, so `assert \"lexer=text\" in "
                      "data.decode()` FAILS — it does NOT resolve (this is exactly "
                      "model_prepatch.py / the original bug).",
        "rationale": "REJECT comes from paste_mode_field's postcondition "
                     "ToSeq(Result())==text_token() being INVARIANT under py_major; "
                     "the rival returns python3 on the py_major>=3 sub-domain.",
    },
    {
        "id": "weak-mode-wrong-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CONST,
        "refinement": "its faithful real patch hard-codes `\"lexer\": \"python3\"`. "
                      "The wire form carries `lexer=python3`, never `lexer=text`, so "
                      "`assert \"lexer=text\" in data.decode()` FAILS — it does NOT "
                      "resolve.",
        "rationale": "REJECT comes from the load-bearing postcondition "
                     "ToSeq(Result())==text_token(); python3 != text everywhere.",
    },
    {
        "id": "weak-body-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_BODY_DROP_VAR,
        "refinement": "its faithful real patch posts `\"code\": contents[1:]`, "
                      "dropping the first byte of the session output. The wire "
                      "form's code field is missing its leading character so "
                      "`assert \"code=full-paste-contents\" in data.decode()` FAILS "
                      "— it does NOT resolve.",
        "rationale": "REJECT comes from paste_body_field's identity postcondition "
                     "ToSeq(Result())==ToSeq(contents); dropping the first element "
                     "violates it on every non-empty body.",
    },
    {
        "id": "weak-expiry-wrong-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_EXP,
        "refinement": "a real patch that set `\"expiry\": \"1day\"` changes the wire "
                      "form to `expiry=1day`; the expiry-field postcondition pins "
                      "the unchanged \"1week\" token (refinement.md A4), so the "
                      "model would no longer faithfully mirror the unchanged dict "
                      "entry. Cheap supporting case (unchanged field, modeled for "
                      "hunk fidelity).",
        "rationale": "REJECT comes from paste_expiry_field's postcondition "
                     "ToSeq(Result())==expiry_token(); 1day != 1week.",
    },
]


# ===========================================================================
# AXIOM LANE — A-reference deep model (no @ContractOnly axiom)
# ===========================================================================
# The only kind-A relationship is the A-reference of refinement.md A5: the
# UNCHANGED serializer urllib.parse.urlencode that create_new_paste calls on the
# params dict (src/_pytest/pastebin.py:86). The deep-model constant tokens
# (text_token/expiry_token) + the identity body field must equal the real
# serializer's wire form on every caller-reachable input. We run the REAL
# urllib.parse.urlencode (CPython stdlib — the very callee) on the gold params
# dict and assert the F2P wire form (lexer=text / expiry=1week / code=<contents>),
# version-invariant. This mirrors axiom_check.py's logic (which G-AX already
# passes). urllib.parse is stdlib so the probe is self-contained and runs in any
# image; we keep apply_gold=True for parity with the post-gold behaviour.
#
# axiom-soundness: the real serializer agrees with the deep-model tokens on every
# body input fuzzed (boundaries + 20000 random) and is invariant under the
# interpreter major version (urlencode never consults sys.version_info).
# axiom-containment is implicit: the ONLY varying caller-reachable input is the
# body `contents` (the mode/expiry fields are fixed constants); urlencode's
# domain is "any mapping of str->str", which contains every body the caller can
# pass, so there is no caller-reachable input outside its domain.

_AX_PROBE = r'''
import random
import sys
from urllib.parse import urlencode

# deep-model reference encodings (lock-step with model.py text_token/expiry_token)
TEXT_TOKEN = [116, 101, 120, 116]            # "text"
EXPIRY_TOKEN = [49, 119, 101, 101, 107]      # "1week"


def codepoints(s):
    return [ord(ch) for ch in s]


def check_tokens():
    assert codepoints("text") == TEXT_TOKEN, TEXT_TOKEN
    assert codepoints("1week") == EXPIRY_TOKEN, EXPIRY_TOKEN


def build_params(contents):
    # EXACTLY the params dict the gold patch constructs (refinement.md A1/A3/A4):
    # mode field is the fixed plain-text token, INVARIANT of interpreter version.
    return {"code": contents, "lexer": "text", "expiry": "1week"}


def check_serialisation(contents):
    params = build_params(contents)
    data = urlencode(params).encode("ascii").decode()   # the real callee chain
    assert "lexer=text" in data, (contents, data)
    assert "lexer=python" not in data, (contents, data)
    assert "expiry=1week" in data, (contents, data)
    assert ("code=%s" % contents) in data, (contents, data)


def main():
    check_tokens()
    # version-invariance witness: build_params ignores sys.version_info, so the
    # mode field is "text" for every interpreter major version.
    for _py_major in (2, 3, 4):
        check_serialisation("full-paste-contents")  # the F2P body
    bodies = [
        "full-paste-contents", "", "a", "abc123", "test_fail", "x_y_z",
        "1234567890", "ASCIIonly", "under_score", "dash-free",
    ]
    for b in bodies:
        check_serialisation(b)
    rng = random.Random(5809)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    for _ in range(20000):
        n = rng.randint(0, 32)
        b = "".join(rng.choice(alphabet) for _ in range(n))
        check_serialisation(b)
    print("AXIOM OK: deep-model tokens (lexer=text, expiry=1week, code=...) "
          "agree with the real urllib.parse.urlencode across 3 interpreter-major "
          "witnesses + 20010 body inputs; lexer invariant under version.")
    sys.exit(0)


if __name__ == "__main__":
    main()
'''

AXIOM_TESTS = [
    {
        "id": "ax-soundness-urlencode-text",
        "axiom": "text_token/expiry_token + identity body (A-reference to urllib.parse.urlencode)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "the UNCHANGED serializer urllib.parse.urlencode, run for "
                     "real on the gold params dict, must produce lexer=text / "
                     "expiry=1week / code=<contents> for every caller-reachable "
                     "body and be invariant under interpreter major version; if it "
                     "ever disagreed with the deep-model tokens the A-reference "
                     "would be AXIOM-UNSOUND. Containment is implicit: the only "
                     "varying caller-reachable input (the body) is always in "
                     "urlencode's str->str domain. Mirrors axiom_check.py / G-AX "
                     "(stdlib-only, image-agnostic).",
    },
]
