# properties.py — PBT falsification battery for pytest-dev__pytest-5262.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of reported_mode for a new body
# and leave the frozen spec (axioms / pure / pre / post-conditions / signatures)
# byte-identical. spec_view elides the entire impl region (nested invariants
# included), so same_spec is GUARANTEED for every case regardless of the proof
# scaffolding inside.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   reported_mode(buffer_mode: List[int]) -> List[int] pins, on the verified output:
#     (P1) ToSeq(Result()) == without_marker(ToSeq(buffer_mode))
#          -- the EXACT per-code-point deletion of the binary marker 'b' (98):
#             kept(c) = empty if c == 98 else PSeq(c); every other code point is
#             kept IN ORDER. This is the discriminating fix (the reported text mode
#             has the binary marker removed). The oracle without_marker is a verified
#             FRONT-RECURSIVE @Pure fold over the *actual input* ToSeq(buffer_mode)
#             -- it is fully GROUNDED/TRANSPARENT, not an opaque answer-key, so there
#             is no "wrong echo" (any impl satisfying P1 has actually done the
#             deletion). See 'assessment'.
#     (P2) marker_free(ToSeq(Result()))  -- the result carries NO binary marker;
#          this is precisely what the F2P observes (`"b" not in sys.stdout.mode`).
#   The pre-patch state had no `mode` property, so the mode fell through __getattr__
#   to the buffer's BINARY mode verbatim (the identity, marker NOT deleted);
#   model_prepatch.py reproduces that and FAILS P1 (and P2 whenever a marker is
#   present) -- exactly the spec sensing the change (G-DIFF).
#
# READ-ONLY INPUT (Acc(...,1/2)) -> FRAME-MUTATION IS MANDATORY:
#   buffer_mode is Acc(list_pred(buffer_mode), 1/2) -- required AND ensured. The
#   property only READS the buffer's mode string; it mutates nothing. An impl that
#   WRITES to buffer_mode holds only half permission and MUST be rejected for
#   INSUFFICIENT PERMISSION (frame-mutation case below).
#
# IMPL DIRECTION CONSTRAINT (pilot bug #3): without_marker / marker_free are
#   FRONT-RECURSIVE folds (peel s[0], recurse on s.drop(1)). The gold impl is a
#   BACKWARD loop (i = len .. 1, prepend kept char) precisely so a single front
#   unfold is available per step. A forward-append loop would need a
#   without_marker(a+b)==without_marker(a)+without_marker(b) lemma the verifier
#   does NOT auto-discharge -> it would fail as a PROOF gap, not a spec defect.
#   Every positive control here therefore keeps the BACKWARD direction and the gold
#   invariants/asserts; only local-variable shapes change.
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5262"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of reported_mode (verified verbatim from model.py). Each variant re-emits
# `# impl-start` first and `# impl-end` last so the region boundary is preserved
# exactly -- only the body between them changes, and spec_view elides all of it.
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace reported_mode's whole impl block with a new body. `body_lines` is
    the source BETWEEN the markers (no markers); we wrap it back in the exact
    `# impl-start` / `# impl-end` markers so the region is intact."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The gold impl body verbatim (between the markers), reused by attacks that
# prepend an illegal statement so the rejection is attributable solely to that
# statement (not to a value mismatch in the loop).
_GOLD_BODY = """    result = []  # type: List[int]
    i = len(buffer_mode)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(buffer_mode), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(buffer_mode))
        Invariant(ToSeq(result) == without_marker(ToSeq(buffer_mode).drop(i)))
        Invariant(marker_free(ToSeq(result)))
        # invariants-end
        c = buffer_mode[i - 1]
        Assert(ToSeq(buffer_mode).drop(i - 1)[0] == c)
        Assert(ToSeq(buffer_mode).drop(i - 1).drop(1) == ToSeq(buffer_mode).drop(i))
        if c != BINARY_MARKER:
            result = [c] + result
        i = i - 1
    return result
"""


SPEC_TESTS = [

    # ------------------------------------------------------------- soundness (1)
    # POSITIVE CONTROL (low-risk local-variable reshape). Keeps the BACKWARD loop
    # direction (front-recursive spec helper => single front unfold per step, no
    # fold-split lemma) and EVERY gold invariant/assert, but renames the locals
    # (i -> n, c -> ch) and rewrites the prepend with the equivalent list literal.
    # A structurally-different yet CORRECT impl that MUST verify; else
    # SPEC-TOO-STRONG. (Pilot bugs #2/#3 avoided: framing asserts kept verbatim,
    # direction unchanged.)
    {
        "id": "pos-control-rename-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    n = len(buffer_mode)\n"
            "    while n > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(buffer_mode), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(0 <= n and n <= len(buffer_mode))\n"
            "        Invariant(ToSeq(out) == without_marker(ToSeq(buffer_mode).drop(n)))\n"
            "        Invariant(marker_free(ToSeq(out)))\n"
            "        # invariants-end\n"
            "        ch = buffer_mode[n - 1]\n"
            "        Assert(ToSeq(buffer_mode).drop(n - 1)[0] == ch)\n"
            "        Assert(ToSeq(buffer_mode).drop(n - 1).drop(1) == ToSeq(buffer_mode).drop(n))\n"
            "        if ch != BINARY_MARKER:\n"
            "            out = [ch] + out\n"
            "        n = n - 1\n"
            "    return out\n"
        ),
        "rationale": "a correct impl with renamed locals (i->n, c->ch, result->out) "
                     "that keeps the BACKWARD direction and EVERY gold invariant/assert "
                     "must verify -- it computes the same per-code-point deletion. The "
                     "front-recursive helper is satisfied by the same single unfold per "
                     "step. Else SPEC-TOO-STRONG. (Stands also as the honest cheapest "
                     "positive control: the grounded oracle without_marker has no wrong "
                     "echo, so the cheapest correct impl is the real deletion.)",
    },

    # --------------------------------------------------------- admissibility (1)
    # ADMISSIBILITY: after computing the gold result, the modeled body self-calls
    # reported_mode on a freshly-built F2P-shaped input -- the buffer mode "rb+"
    # = [114, 98, 43], exactly what `safe_text_dupfile`'s "wb+" duplication makes
    # the underlying binary buffer report under FD capture (the F2P scenario). A
    # fresh list literal carries full list_pred; passing a half is admissible. If
    # the Requires could not be established for this normal input, the call site
    # would fail => PRECOND-TOO-STRONG. The caller lives strictly inside the impl
    # region (spec untouched).
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            _GOLD_BODY.rstrip("\n").rsplit("\n    return result", 1)[0] +
            "\n"
            "    # Admissibility self-call: the FD-capture buffer mode \"rb+\" =\n"
            "    # [114, 98, 43] is a normal F2P-shaped input. A fresh list literal\n"
            "    # carries full list_pred(probe); passing a half to reported_mode is\n"
            "    # admissible. If the Requires could not be established here, this\n"
            "    # call site would fail => PRECOND-TOO-STRONG.\n"
            "    probe = [114, 98, 43]  # type: List[int]\n"
            "    probe_out = reported_mode(probe)\n"
            "    Assert(Acc(list_pred(probe_out)))\n"
            "    Assert(marker_free(ToSeq(probe_out)))\n"
            "    return result\n"
        ),
        "rationale": "the precondition Acc(list_pred(buffer_mode), 1/2) must admit a "
                     "normal input: the FD-capture buffer mode \"rb+\" = [114, 98, 43]. "
                     "The self-call establishes reported_mode's Requires (a half of a "
                     "fresh full list_pred) and reads back a marker_free result; else "
                     "PRECOND-TOO-STRONG.",
    },

    # ---------------------------------------------------------------- uniqueness
    # ATTACK 1 (FRAME-MUTATION, MANDATORY -- the #1 weakness class). The impl
    # OVERWRITES the read-only input buffer_mode (clears its first element) before
    # running the gold loop. Only Acc(list_pred(buffer_mode), 1/2) is held, so a
    # WRITE requires full permission and the verifier MUST reject this for
    # INSUFFICIENT PERMISSION -- not for a value mismatch. The gold body is kept
    # verbatim AFTER the write so the rejection is attributable solely to the
    # illegal mutation.
    {
        "id": "frame-mutate-buffer-mode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input.\n"
            "    buffer_mode[0] = 0\n" +
            _GOLD_BODY
        ),
        "refinement": "in real pytest the property reads `self.buffer.mode` (a str) "
                      "and returns a NEW string from str.replace; it never mutates the "
                      "buffer. str objects are immutable, so a faithful real patch "
                      "CANNOT write into the buffer's mode at all -- a patch that did "
                      "(e.g. reassigning self.buffer.mode) would corrupt the live "
                      "EncodedFile that every capture P2P test "
                      "(test_capturing_basic_api[fd], test_simple_resume_suspend, ...) "
                      "still uses; the F2P and those P2P tests would diverge. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(list_pred(buffer_mode), 1/2); a write needs full permission. "
                     "Insufficient permission, NOT a value mismatch. This is the "
                     "mandatory frame-mutation probe; gold loop kept verbatim after the "
                     "write so the rejection is attributable solely to it.",
    },

    # ATTACK 2 (PARTIAL-DOMAIN = the bug-delta / prepatch identity). Keep EVERY
    # code point unconditionally (the binary marker is NOT deleted) -- exactly the
    # pre-patch behaviour where `mode` fell through __getattr__ to the buffer's
    # binary mode. CORRECT only on buffer modes that already carry no 'b'; WRONG on
    # every mode containing the binary marker (the FD-capture case "rb+"). Must
    # reject: violates P1 (Result == buffer_mode != without_marker(buffer_mode)
    # when a marker is present) and P2 (marker_free fails -- a 'b' survives).
    {
        "id": "weak-identity-keep-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    i = len(buffer_mode)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(buffer_mode), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(buffer_mode))\n"
            "        Invariant(ToSeq(result) == ToSeq(buffer_mode).drop(i))\n"
            "        # invariants-end\n"
            "        c = buffer_mode[i - 1]\n"
            "        result = [c] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "refinement": "this is the PRE-PATCH behaviour: the reported mode is the "
                      "buffer's binary mode VERBATIM (no deletion), reproducing the "
                      "__getattr__ fall-through model_prepatch.py captures. Under FD "
                      "capture sys.stdout's buffer mode is \"rb+\", so the reported "
                      "mode stays \"rb+\" and the F2P assertion `\"b\" not in "
                      "sys.stdout.mode` FAILS. The faithful real patch (no .replace) "
                      "does NOT resolve. (= model_prepatch.py, G-DIFF.)",
        "rationale": "violates P1 (Result == buffer_mode, not without_marker(...), "
                     "whenever a marker is present) and P2 (marker_free(Result) is "
                     "False -- a binary marker survives in the result).",
    },

    # ATTACK 3 (PARTIAL-DOMAIN, leading-marker survives). Delete the binary marker
    # at EVERY position EXCEPT the first code point (i == 1, the head). CORRECT on
    # every buffer mode whose first code point is not 'b'; WRONG whenever the mode
    # starts with the binary marker (e.g. "br" -> kept as "br"). Targets the head
    # of the sequence the front-recursive fold peels first. Must reject: when
    # buffer_mode[0] == 98 the result keeps the leading 'b', so P1 (without_marker
    # deletes it) and P2 (marker_free) both fail.
    {
        "id": "weak-keep-leading-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    i = len(buffer_mode)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(buffer_mode), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(buffer_mode))\n"
            "        # invariants-end\n"
            "        c = buffer_mode[i - 1]\n"
            "        # WRONG: at the head (i == 1) keep the marker unconditionally.\n"
            "        if c != BINARY_MARKER or i == 1:\n"
            "            result = [c] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "refinement": "this keeps a LEADING binary marker (the head code point) "
                      "instead of deleting it. The real str.replace(\"b\", \"\") "
                      "removes EVERY 'b' including a leading one, so a buffer mode like "
                      "\"brb+\" must report \"r+\" but this impl reports \"br+\". Any "
                      "EncodedFile whose buffer mode starts with 'b' (and FD-capture "
                      "modes generally include the marker; a leading 'b' arises from "
                      "duplications like \"b...\") would keep a 'b' in the reported "
                      "mode, so the F2P `\"b\" not in sys.stdout.mode` FAILS. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates P1 (when buffer_mode[0]==98 the result keeps the leading "
                     "marker, so Result != without_marker(...)) and P2 (marker_free is "
                     "False). A genuine partial-domain rival: correct on all modes whose "
                     "first code point is not 'b', wrong on leading-marker modes.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN, drop a non-marker code point too -- over-deletion).
    # Delete the binary marker AND also drop the '+' code point (43). CORRECT on
    # buffer modes with no '+' (e.g. "rb" -> "r"); WRONG on every mode containing
    # '+' (the FD-capture mode "rb+" -> should be "r+" but this yields "r"). Must
    # reject: P1 deletes ONLY the marker, so dropping '+' makes Result a code point
    # short of without_marker(...). (P2 still holds -- this is a P1-only break,
    # confirming the equality clause is load-bearing beyond marker_free.)
    {
        "id": "weak-over-delete-plus",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    result = []  # type: List[int]\n"
            "    i = len(buffer_mode)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(buffer_mode), 1 / 2))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(buffer_mode))\n"
            "        Invariant(marker_free(ToSeq(result)))\n"
            "        # invariants-end\n"
            "        c = buffer_mode[i - 1]\n"
            "        # WRONG: also drop the '+' code point (43), not just the marker.\n"
            "        if c != BINARY_MARKER and c != 43:\n"
            "            result = [c] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "refinement": "this deletes the '+' character as well as 'b'. The real "
                      "str.replace(\"b\", \"\") removes ONLY 'b' and preserves every "
                      "other character, so the FD-capture buffer mode \"rb+\" must "
                      "report \"r+\" (with the '+'), but this impl reports \"r\". Any "
                      "consumer that inspects the reported mode for read/write/append "
                      "capability (the '+' marks updatable) would mis-classify the "
                      "stream; the reported string differs from the real "
                      ".replace output on every mode containing '+' (the common "
                      "rb+/wb+ duplication modes), so the F2P (which checks the exact "
                      "mode value the property returns) and capture P2P diverge. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates P1: without_marker keeps '+'; this drops it, so Result "
                     "== without_marker(...) fails on any mode containing '+'. P2 "
                     "(marker_free) still holds, proving the EQUALITY clause P1 is "
                     "load-bearing independently of marker_free -- a marker_free-only "
                     "spec would be too weak and this case pins that.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE.
# There are NO @ContractOnly axioms in this bundle (meta.axioms == [], the axioms
# region is an empty singleton) and NO consumed-axiom proof step. The single
# kind-A item is an A-REFERENCE deep model: without_marker (the spelled-out
# front-recursive @Pure fold in the pure region) is validated == the REAL
# str.replace("b","") out-of-band. There is therefore no axiom-soundness obligation
# whose Ensures could drift and no caller-reachable callee-input outside any axiom
# domain (no axiom domain exists) -- containment is vacuous.
#
# We still run the bundle's host-validated G-AX oracle (axiom_check.py) in-container
# as the single axiom-lane probe, so the A-reference deep model is grounded in the
# REAL CPython str.replace (not a regex over source -- pilot bug #4): the probe
# EXECUTES s.replace("b","") on every file-mode string CPython produces (incl.
# repeated/adjacent/leading/trailing markers and uppercase 'B' which must be KEPT)
# + 20000 fuzz inputs, and asserts without_marker == the real callee AND the real
# result is marker_free. str.replace is stdlib (no repo import), so apply_gold is
# False; the probe reads no files (no utf-8 codec concern -- pilot bug #5); the
# runner mounts ONLY this probe script, and axiom_check.py is embedded verbatim
# from the HOST at load (pilot bug #6).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-without-marker-eq-str-replace",
        "axiom": "without_marker == str.replace('b','') (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,  # str.replace is stdlib; no repo symbol needed
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness/containment: the deep model without_marker "
                     "(per-code-point deletion of the binary marker) must equal the "
                     "REAL CPython str.replace(\"b\",\"\") at the code-point level on "
                     "every input the model can reach (all file-mode strings incl. "
                     "repeated/adjacent/leading/trailing markers, uppercase 'B' which "
                     "is KEPT, the empty string + 20000 fuzz) and the real result must "
                     "be marker_free. Any mismatch => the A-reference is unsound. There "
                     "is no @ContractOnly axiom and no caller-reachable callee-input "
                     "outside any axiom domain (no axiom domain exists -- containment "
                     "vacuous).",
    },
]
