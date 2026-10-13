# properties.py — PBT falsification battery for django__django-15098. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
# Spec cases are full model.py variants (frozen spec, swapped impl region) checked
# by Nagini verify + same_spec; the axiom cases record the ONE consumed axiom's
# soundness obligations (executed by G-AX, not by this gate — see AXIOM_TESTS).
#
# DEFENDED SURFACE (read from model.py + refinement.md + mapping.md + the gold patch):
#   language_prefix_len(path: List[int]) -> int
#   Models the locale-prefix extraction the gold patch changes: the compiled regex
#   language_code_prefix_re = _lazy_re_compile(r'^/(\w+([@-]\w+){0,2})(/|$)') matched
#   in get_language_from_path, returning len(group(1)) or -1. The gold change is the
#   single repeat bound ? -> {0,2}: a candidate may now carry a primary sub-tag plus
#   UP TO TWO further sub-tags (script + region per RFC 5646) instead of just one.
#   The changed matcher is modeled DEEPLY as the @Pure structural parse
#   prefix_len_spec(path, maxsep) (run_len / nsep / no_adjacent_sep / well_formed_tag
#   / spec_unfold) built over ONE @Pure @ContractOnly primitive is_word(c) — the
#   per-code-point membership test for the character class a sub-tag is drawn from,
#   whose contract pins the class exactly BELOW code point 128 and leaves it OPEN
#   at/above 128, which is what the real, whole-of-Unicode class satisfies. The parse
#   is validated == the real compiled matcher over the WHOLE input domain (no ASCII
#   restriction, is_word instantiated at its real counterpart) by axiom_check.py
#   (G-AX). str is carried as List[int] code points; the spec is over PSeq[int] via
#   ToSeq.
#
#   Precondition (ONE input, READ-ONLY):
#     (P1) Requires(Acc(list_pred(path), 1 / 2))    # HALF permission => no write
#   Postcondition (three clauses):
#     (Q1) Ensures(Acc(list_pred(path), 1 / 2))     # framing: returns the read perm
#     (Q2) Ensures(Result() == prefix_len_spec(ToSeq(path), 2))  # LOAD-BEARING:
#          the returned length is EXACTLY the deep structural parse with budget TWO.
#     (Q3) Ensures(Result() == -1 or (1 <= Result() and Result() <= len(path) - 1))
#          # grounding: no prefix (-1), or a positive length strictly inside the path.
#
# THE LOAD-BEARING CLAUSE is Q2. Every uniqueness rival is rejected by Q2 (the impl
#   returns a length that disagrees with prefix_len_spec(.,2) on some path), surfaced
#   through the impl's own definitional-unfold asserts that bind the returned value
#   to spec_unfold(.,2,rlen) / prefix_len_spec(.,2). The budget literal in Q2 is the
#   ENTIRE behavioural delta of the patch (? <=> budget 1; {0,2} <=> budget 2).
#
# FRAME-MUTATION lane is MANDATORY: path is Acc(...,1/2) (read-only, P1). A rival
#   that WRITES to path must be REJECTED for INSUFFICIENT PERMISSION (the project's
#   #1 weakness class; a byte-fuzzer never thinks to mutate the input).
#
# UNGROUNDED-ORACLE-ECHO: there is NO wrong echo to build. Q2 pins Result to
#   prefix_len_spec(ToSeq(path), 2), which is NOT an opaque answer-key / exact-marker
#   oracle — it is a deterministic @Pure FUNCTION of the argument `path`, fully
#   unfolded in the pure region (run_len/nsep/.../spec_unfold). The unique satisfier
#   of Q2 IS the correct parse, so any value an impl could "echo" to satisfy Q2 is by
#   construction the correct answer; there is no wrong echo that verifies. The honest
#   substitute is a cheapest grounded-oracle positive control: an impl that produces
#   the correct length and proves Q2 (the structural-variant pos-control below). See
#   'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. language_prefix_len returns a pure int abstraction
#   of the regex match length with no raise / side-effect / capability difference
#   invisible to the value abstraction. The one genuine control-flow point of the
#   gold change — "matched (>=1) vs no-match (-1)" — is fully captured by the value
#   Result() (Q2/Q3); -1 <=> not regex_match <=> get_language_from_path returns None
#   (refinement.md A6). The downstream get_supported_language_variant resolver is an
#   UNCHANGED kind-I callee (refinement.md A7 / mapping.md §2), not modeled here.
#
# AXIOM lane: the bundle consumes ONE @ContractOnly axiom, is_word(c) (model.py's
#   axioms region), modelling per-code-point membership of the character class a
#   sub-tag is drawn from. Its two obligations are recorded below and are executed
#   by axiom_check.py under G-AX, which this gate deliberately does NOT re-judge
#   (pbt.py header: "a manifest may carry AXIOM_TESTS, and this gate ignores them"):
#   (i) SOUNDNESS of the contract — the real class must equal the pinned enumeration
#   on every code point below 128, and the contract must constrain NOTHING at/above
#   128, so the proof holds for every class the real one could be; (ii) SOUNDNESS of
#   the A-reference — with is_word at its real counterpart, prefix_len_spec(.,2) ==
#   the real post-patch matcher and prefix_len_spec(.,1) == the real pre-patch one,
#   over the whole domain (175156 probed inputs, ASCII and non-ASCII, 0 divergences).
from pathlib import Path

INSTANCE = "django__django-15098"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

_IMPL_OPEN = "    # impl-start\n"
_IMPL_CLOSE = "    # impl-end\n"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen function impl region body, verbatim — everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end` markers (INCLUDING the two nested
# invariants regions). same_spec is computed over the spec_view, which elides every
# impl region (and nested invariants), so _swap()ing inside this block is GUARANTEED
# same_spec: the spec (axioms/pure/pre-/post-conditions + signature) is never touched.
_s = _BASE.index(_IMPL_OPEN) + len(_IMPL_OPEN)
_e = _BASE.index(_IMPL_CLOSE)
_IMPL = _BASE[_s:_e]
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# Helpers that build a variant by editing the gold impl body in place. Editing
# *inside* _IMPL keeps the spec frozen (same_spec) while changing only behaviour
# and/or the proof scaffolding the impl carries.
# ---------------------------------------------------------------------------

def _edit(*pairs):
    """Apply a sequence of unique-substring replacements to the gold _IMPL body."""
    body = _IMPL
    for old, new in pairs:
        if body.count(old) != 1:
            raise AssertionError(f"impl-edit anchor not unique: {old!r}")
        body = body.replace(old, new, 1)
    return body


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ===========================================================================

# pos-ternary-reshape (soundness): a structurally-DIFFERENT but behaviourally
# IDENTICAL impl. Both per-element conditional updates are rewritten from
# if/else statement form into single-expression ternary assignments, and the
# inner-loop separator increment likewise. The executable shape changes; every
# gold Invariant and every framing/definitional-unfold Assert is KEPT verbatim, so
# the gold proof stays valid (this is a local-statement reshape, NOT a loop-
# direction flip — the backward scans and their front-recursive reconstruction
# invariants are untouched, so no f(a+b) fold lemma is needed). If this FAILS to
# verify => SPEC-TOO-STRONG (a faithful correct impl rejected by the postcondition).
_POS_TERNARY = _edit(
    (
        "        if is_tagchar(c):\n"
        "            rlen = rlen + 1\n"
        "        else:\n"
        "            rlen = 0\n",
        "        rlen = rlen + 1 if is_tagchar(c) else 0\n",
    ),
    (
        "        c2 = path[j]\n"
        "        if is_sep(c2):\n"
        "            tseps = tseps + 1\n",
        "        c2 = path[j]\n"
        "        tseps = tseps + (1 if is_sep(c2) else 0)\n",
    ),
)

# admiss-reads (admissibility): the precondition is the non-trivial heap permission
# Acc(list_pred(path), 1/2). This control confirms it ADMITS the reads a normal
# F2P-shaped path (e.g. "/en-latn-us/") needs: it explicitly reads len(path) and,
# when the path begins with "/", the leading code point path[0], asserting those
# reads succeed under the HALF permission BEFORE running the gold body verbatim. No
# write is performed, so no permission is demanded beyond the spec. If this FAILS =>
# PRECOND-TOO-STRONG (the half-permission would reject a legitimate input).
_ADMISS = (
    "    # Admissibility: a normal request path is in-domain; the half-permission\n"
    "    # admits reading its length and (when non-empty) its leading code point.\n"
    "    Assert(len(path) >= 0)\n"
    "    if len(path) > 0:\n"
    "        Assert(path[0] == path[0])  # read admitted under Acc(list_pred(path),1/2)\n"
    + _IMPL
)


# ===========================================================================
# FRAME-MUTATION RIVAL (MANDATORY — path is Acc(...,1/2) read-only).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ===========================================================================

# frame-mut-write: keeps the ENTIRE gold body verbatim (so the rejection is
# attributable solely to the added write, not to any value mismatch) and prepends a
# write back into the read-only input: `path[0] = path[0]`, guarded by len>0 so it
# is reached on every non-empty F2P path. A no-op store, but a STORE — it demands
# FULL write permission on `path`, which the caller granted only at 1/2. The verifier
# must reject for INSUFFICIENT PERMISSION.
_FRAME_MUT = (
    "    if len(path) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        path[0] = path[0]\n"
    + _IMPL
)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only the impl region.
# ===========================================================================

# weak-budget1 (uniqueness / the PRE-PATCH behaviour): change the separator-budget
# guard from `tseps > 2` (budget 2 = the gold {0,2}) to `tseps > 1` (budget 1 = the
# pre-patch `?`). This is exactly model_prepatch.py's value. On a script+region path
# (two separators) — /de-ch-1901/, /en-latn-us/, /nan-hani-tw/ — the rival returns
# -1, while prefix_len_spec(.,2) returns the run length (10 / 10 / 11). The rival's
# `return -1` lands on the gold's `Assert(prefix_len_spec(ToSeq(path), 2) == -1)`,
# which is FALSE there, so Q2 cannot be established and the verifier rejects.
_WEAK_BUDGET1 = _edit(("    if tseps > 2:\n", "    if tseps > 1:\n"))

# weak-budget3 (uniqueness): widen the budget guard the OTHER way, `tseps > 2` ->
# `tseps > 3`, accepting a candidate with THREE separators. On /de-simple-page-test/
# (three separators) the rival accepts and returns the run length 19, while
# prefix_len_spec(.,2) returns -1. Past the (now too-loose) guard the gold asserts
# bind the returned value to spec_unfold(.,2,rlen)/prefix_len_spec(.,2); the rival's
# returned positive length contradicts the spec's -1 for that path, so Q2 fails.
_WEAK_BUDGET3 = _edit(("    if tseps > 2:\n", "    if tseps > 3:\n"))

# weak-drop-termination (PARTIAL-DOMAIN): drop the trailing-`(/|$)` check. The gold
# accepts only when the candidate run is terminated by "/" (47), end-of-path, or a
# final newline, and returns -1 on the fall-through (non-terminated) path; this rival
# accepts the run regardless of the following character, by returning the run length
# on that fall-through path too. Every path through the terminator region then yields
# rlen, which is the whole behavioural claim of the attack. Correct on every properly
# terminated F2P path (/pl/, /en-latn-us/, …) but diverges on a path whose well-formed
# run is followed by non-"/" punctuation, e.g. "/aaa.bbb/": run = "aaa" (stops at
# "."), the next char is "." not "/", so prefix_len_spec(.,2) = -1 while the rival
# returns 3.
#   Attribution: the edit changes ONLY the returned value, so the gold's proof of the
# fall-through path — including `Assert(spec_val == -1)`, which is TRUE there —
# survives verbatim and still discharges. Viper reports exactly one error, the
# postcondition Q2 itself (`Result() == prefix_len_spec(ToSeq(path), 2)`), because
# spec_val is PROVEN to be -1 at the return while the rival returns rlen >= 1. So the
# rejection is definite and attributable solely to the divergence, not to any
# scaffolding assert the rival left behind.
#   Deliberately NOT written as a forced branch (`if path[rlen + 1] == 47:` ->
# `if True:`). That form makes the gold's remaining two branches unreachable, and
# mypy's dead-code check aborts the translation BEFORE Viper ever runs — nagini then
# exits with its rejection code on a front-end error, which on a backend that needs no
# refutation witness would be recorded as a rejection the spec never earned. Measured:
# `Type error: dead.code (@321.0)`, exit 1 in 9s, against 38s for this rival and 31s
# for gold. Two smaller variants of that form were measured too and both land on an
# impl-region assert rather than on Q2 (the unwrapped body keeps
# `Assert(ToSeq(path).drop(1)[rlen] == 47)`, a restatement of the branch condition the
# rival just dropped, and fails THERE), so neither attributes the rejection to the
# postcondition the way this one does.
_WEAK_DROP_TERM = _edit(
    (
        "    Assert(spec_val == -1)\n"
        "    return -1\n",
        "    Assert(spec_val == -1)\n"
        "    return rlen\n",
    )
)

# nonvacuity-drop-term-site-reachable: the reachability control for the site the
# rival above is judged at. `Assert(False)` immediately before that return, with the
# whole gold decision kept verbatim, so the ONLY question asked is whether any input
# gets there. It must FAIL. If it VERIFIED, the fall-through (non-terminated) path
# would be unreachable under P1 + the two loops' invariants, `Assert(spec_val == -1)`
# and the return would be dead, and weak-drop-termination's rejection would be a
# rejection of nothing at all — the spec would look strong on a sub-domain no input
# can enter (=> PRECOND-TOO-STRONG). A verifying rival cannot substitute for this
# claim: a vacuous region makes an expect="verify" case verify vacuously too, so only
# an assertion that must FAIL separates "reachable and refuted" from "never entered".
_NONVAC_DROP_TERM_SITE = _edit(
    (
        "    Assert(spec_val == -1)\n"
        "    return -1\n",
        "    Assert(spec_val == -1)\n"
        "    Assert(False)\n"
        "    return -1\n",
    )
)

# weak-allow-empty-run (PARTIAL-DOMAIN, the no-prefix boundary): when there is NO
# candidate run (rlen == 0), the gold returns -1; this rival returns 0 instead.
# prefix_len_spec(.,2) = -1 for such paths (e.g. "//", "/.foo/", "/-/"), and Q3 also
# forbids 0 (Result() must be -1 or >= 1). The rival's `return 0` on the rlen==0
# branch lands on the gold's `Assert(prefix_len_spec(ToSeq(path), 2) == -1)` (false
# for a returned 0 under Q2) — rejected. Cheap supporting near-miss at the exact
# no-match boundary (a path with no leading word run), still a real divergence.
_WEAK_EMPTY_RUN = _edit(
    (
        "    if rlen == 0:\n"
        "        Assert(prefix_len_spec(ToSeq(path), 2) == -1)\n"
        "        return -1\n",
        "    if rlen == 0:\n"
        "        Assert(prefix_len_spec(ToSeq(path), 2) == -1)\n"
        "        return 0\n",
    )
)


SPEC_TESTS = [
    {
        "id": "pos-ternary-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_TERNARY),
        "rationale": (
            "structurally-different but behaviourally identical impl: both per-"
            "element conditional updates and the inner separator increment are "
            "rewritten from if/else statements to single-expression ternaries. The "
            "backward scans and ALL gold Invariants / framing+definitional-unfold "
            "Asserts are kept verbatim (a local-statement reshape, not a loop-"
            "direction flip — no f(a+b) fold lemma needed), so the gold proof stays "
            "valid. If it fails to verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the non-trivial precondition Acc(list_pred(path), 1/2) must admit the "
            "reads a normal request path needs (its length and its leading code "
            "point). The control performs and asserts those reads under the half-"
            "permission before the gold body. If it fails => PRECOND-TOO-STRONG (the "
            "half-permission would reject a legitimate F2P-shaped input)."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch only READS the request path (regex .match(path), then "
            "regex_match[1]); it never mutates the caller's path string. A faithful "
            "real patch that wrote back into the shared path object would corrupt "
            "the caller's request path and diverge from the gold's read-only match — "
            "it is not the gold patch and would not faithfully resolve the F2P. The "
            "store here is a no-op only by coincidence; the spec must forbid ANY "
            "write to the read-only input."
        ),
        "rationale": (
            "REJECTED by the permission system: path is granted at Acc(...,1/2) "
            "(P1); the store path[0]=path[0] demands FULL write permission, which is "
            "unavailable, so the verifier rejects for INSUFFICIENT PERMISSION. The "
            "gold body is kept verbatim so the rejection is attributable solely to "
            "the write. If it verifies => the read-only frame is not enforced "
            "(frame-mutation, the #1 weakness class)."
        ),
    },
    {
        "id": "weak-budget1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BUDGET1),
        "refinement": (
            "this is exactly the PRE-PATCH behaviour (model_prepatch.py): the "
            "separator budget reverts to 1 (the old regex `?` / {0,1}). Its faithful "
            "real patch is the UNPATCHED repo regex r'^/(\\w+([@-]\\w+)?)(/|$)', "
            "which rejects a script+region path: get_language_from_path('/de-ch-1901/')"
            " returns None instead of 'de-ch-1901', failing the F2P "
            "test_get_language_from_path_real (which now asserts de-ch-1901 / "
            "en-latn-us / nan-hani-tw resolve). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2 (Result() == prefix_len_spec(ToSeq(path), 2)): on a "
            "two-separator path the rival returns -1 while prefix_len_spec(.,2) is "
            "the positive run length, so the rival's `return -1` contradicts the "
            "gold's bound-to-spec asserts. This is precisely the change the spec "
            "senses (G-DIFF). If it verifies => SPEC-TOO-WEAK (the {0,2} delta would "
            "not be enforced)."
        ),
    },
    {
        "id": "weak-budget3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BUDGET3),
        "refinement": (
            "widening the budget to 3 over-accepts: a real patch that wrote {0,3} "
            "(or dropped the bound) would extract a 3-separator run, so "
            "get_language_from_path('/de-simple-page-test/') would attempt to "
            "resolve 'de-simple-page-test' instead of returning None — failing the "
            "F2P (which asserts /de-simple-page-test/ -> None) and the view test "
            "test_page_with_dash (which expects /de-simple-page-test/ NOT to match a "
            "language). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2: on /de-simple-page-test/ (three separators) the rival "
            "returns the run length 19 while prefix_len_spec(.,2) is -1, so the "
            "returned positive length contradicts the gold's spec_unfold(.,2,rlen) / "
            "prefix_len_spec(.,2) binding asserts. If it verifies => SPEC-TOO-WEAK "
            "(the upper edge of the {0,2} budget would not be enforced)."
        ),
    },
    {
        "id": "weak-drop-termination",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_TERM),
        "refinement": (
            "dropping the trailing (/|$) anchor: a real patch that omitted the "
            "termination requirement would treat a word run followed by other "
            "punctuation as a match, so a path like '/aaa.bbb/' (run 'aaa', next "
            "char '.') would extract 'aaa' and try to resolve it, instead of the "
            "regex correctly NOT matching (group must be followed by '/' or end). "
            "It diverges from the real matcher on every run terminated by non-'/' "
            "punctuation. PARTIAL-DOMAIN attack on the terminator sub-domain. Does "
            "NOT resolve (and breaks the regex's (/|$) anchor that all F2P paths rely "
            "on)."
        ),
        "rationale": (
            "REJECTED by Q2, at the postcondition itself: on a run terminated by "
            "non-'/' (e.g. '/aaa.bbb/') the rival returns the run length while "
            "prefix_len_spec(.,2) is -1. The gold's `Assert(spec_val == -1)` on that "
            "fall-through path is retained and still PROVES (the edit changes only the "
            "returned value), so Viper reports exactly one error and it is the "
            "load-bearing clause: \"Postcondition of language_prefix_len might not "
            "hold. Assertion (Result() == prefix_len_spec(ToSeq(path), 2)) might not "
            "hold.\" Definite, not an incompleteness artifact — spec_val is proven -1 "
            "at the return and rlen >= 1 there. Correct on every properly-terminated "
            "F2P path, so a true PARTIAL-DOMAIN break, not a blanket divergent impl. "
            "The site's reachability is the separate control below. If it verifies => "
            "SPEC-TOO-WEAK on the terminator sub-domain."
        ),
    },
    {
        "id": "nonvacuity-drop-term-site-reachable",
        "kind": "admissibility",
        "expect": "reject",
        "module": _impl(_NONVAC_DROP_TERM_SITE),
        "refinement": (
            "not a rival impl: the gold decision verbatim with `Assert(False)` added "
            "at the fall-through (non-terminated) return, the site "
            "weak-drop-termination is judged at. It asks one question — can any input "
            "reach that site — and a real patch is not at issue."
        ),
        "rationale": (
            "REJECTED, and the rejection is the point: Viper reports \"Assert might "
            "fail. Assertion False might not hold.\" at that return, so the "
            "fall-through path IS reachable under P1 (Acc(list_pred(path), 1/2)) plus "
            "the two loops' invariants, and the obligations discharged there are not "
            "vacuous. Were it to VERIFY, no input could reach the site, "
            "`Assert(spec_val == -1)` and the return would be dead, and "
            "weak-drop-termination would be refuting a rival on a sub-domain that does "
            "not exist => PRECOND-TOO-STRONG (a vacuously satisfied region, the same "
            "defect class as an infeasible guard)."
        ),
    },
    {
        "id": "weak-allow-empty-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY_RUN),
        "refinement": (
            "returning 0 for a path with no leading word run (e.g. '//', '/.x/', "
            "'/-/') corresponds to a real patch that treated 'matched an empty "
            "prefix' as success — it would feed an empty/0-length code to the "
            "resolver instead of returning None, diverging from the regex (group 1 "
            "requires \\w+, never empty). Does NOT resolve. Cheap supporting "
            "near-miss at the exact no-match boundary, with a real refinement."
        ),
        "rationale": (
            "REJECTED by Q2 AND Q3: the rival's `return 0` on the rlen==0 branch "
            "lands on the gold's `Assert(prefix_len_spec(ToSeq(path), 2) == -1)` "
            "(prefix_len_spec is -1 there, not 0), and Q3 independently forbids 0 "
            "(Result() must be -1 or >= 1). If it verifies => SPEC-TOO-WEAK at the "
            "no-prefix boundary."
        ),
    },
]

# ---------------------------------------------------------------------------
# AXIOM-lane probes. Standalone stdlib scripts (the runtime oracle is the real
# `re` module, not the verifier), exit 0 iff the obligation holds. They are the
# same two obligations axiom_check.py discharges under G-AX; recorded here so
# the manifest names every trust point the proof rests on.
# ---------------------------------------------------------------------------

# ---- ax-sound-is-word: the consumed axiom's contract, both halves.
_AX_SOUND_IS_WORD = r"""
import re, sys
# The real per-code-point class the axiom models: exactly as the matcher
# evaluates it on a str pattern, i.e. over the whole of Unicode.
CLS = re.compile(r"\w")
def real(c):
    return CLS.fullmatch(chr(c)) is not None

# The axiom's Ensures, transcribed: pinned below 128, OPEN at/above 128.
def pinned(c):
    return (48 <= c <= 57) or (65 <= c <= 90) or (97 <= c <= 122) or c == 95
def permits(c, v):
    return v == pinned(c) if c < 128 else True

# (a) the pinned half, exhaustively.
bad = [(c, chr(c), real(c), pinned(c)) for c in range(128) if real(c) != pinned(c)]
if bad:
    for c, ch, got, want in bad:
        print("AXIOM-UNSOUND at cp=%d (%r): real=%r pinned=%r" % (c, ch, got, want))
    sys.exit(1)

# (b) the open half: real members AND real non-members above 128, each of which
#     the contract must permit; plus a non-vacuity guard on both sides.
members, nonmembers = [], []
for c in (0x00E9, 0x00F1, 0x00DF, 0x4E2D, 0x03B1, 0x0430, 0x0660, 0x00C7,
          0x00AA, 0x05D0, 0x3042, 0x0915, 0x1E9E, 0xFF21, 0x00B5,
          0x00D7, 0x2010, 0x00A0, 0x00AB, 0x2013, 0x00A9, 0x00B7,
          0x2026, 0x00F7, 0x2192, 0x3001, 0xFF0F, 0x20AC, 0x2603):
    v = real(c)
    if not permits(c, v):
        print("AXIOM-UNSOUND: contract does not permit real value %r at cp=%d "
              "(at/above 128 it must constrain nothing)" % (v, c))
        sys.exit(1)
    (members if v else nonmembers).append(c)
if not members or not nonmembers:
    print("VACUOUS open half: probes did not populate both sides above 128 "
          "(members=%d nonmembers=%d)" % (len(members), len(nonmembers)))
    sys.exit(1)

print("ax-sound-is-word OK: real class == the pinned enumeration on all 128 code "
      "points below 128; above 128 the real class has %d member and %d non-member "
      "probes (e.g. %r member, %r non-member) and the contract permits BOTH, so it "
      "over-claims nothing and no implementation may decide that region itself."
      % (len(members), len(nonmembers), chr(members[0]), chr(nonmembers[0])))
sys.exit(0)
"""

# ---- ax-ref-deep-parse: the A-reference at BOTH budgets, whole domain.
_AX_REF_DEEP_PARSE = r"""
import random, re, sys
REAL_OLD = re.compile(r"^/(\w+([@-]\w+)?)(/|$)")
REAL_NEW = re.compile(r"^/(\w+([@-]\w+){0,2})(/|$)")
CLS = re.compile(r"\w")

def is_word(c):            # the axiom, instantiated at its REAL counterpart
    return CLS.fullmatch(chr(c)) is not None
def is_sep(c):
    return c == 45 or c == 64
def is_tagchar(c):
    return is_word(c) or is_sep(c)

def prefix_len_spec(path, maxsep):
    if len(path) == 0 or path[0] != 47:
        return -1
    body = path[1:]
    r = 0
    while r < len(body) and is_tagchar(body[r]):
        r += 1
    if r == 0:
        return -1
    tag = body[:r]
    if not (is_word(tag[0]) and is_word(tag[-1])):
        return -1
    if any(is_sep(tag[k]) and is_sep(tag[k + 1]) for k in range(len(tag) - 1)):
        return -1
    if sum(1 for c in tag if is_sep(c)) > maxsep:
        return -1
    if r == len(body) or body[r] == 47:
        return r
    # `$` also matches immediately before a newline that is the LAST character.
    if body[r] == 10 and r == len(body) - 1:
        return r
    return -1

def real_len(rx, s):
    m = rx.match(s)
    return len(m.group(1)) if m else -1

def check(s):
    for rx, budget, name in ((REAL_OLD, 1, "pre"), (REAL_NEW, 2, "post")):
        model, real = prefix_len_spec([ord(ch) for ch in s], budget), real_len(rx, s)
        if model != real:
            print("A-REFERENCE UNSOUND (%s budget=%d): path=%r model=%r real=%r"
                  % (name, budget, s, model, real))
            sys.exit(1)

checked = 0
# Boundary corpus: structural edges, and non-ASCII word / non-word code points in
# both accepting and rejecting positions -- IN domain, not a documented gap.
for s in ("", "/", "//", "/pl/", "/pl", "/en-gb/", "/en-latn-us/", "/en-Latn-US/",
          "/de-ch-1901/", "/nan-hani-tw/", "/de-simple-page-test/", "/i-mingo/",
          "/-", "/-/", "/-a/", "/a-/", "/a--b/", "/a@b@c/", "/a@b@c@d/",
          "/a.b/", "/a b/", "/123/", "/a_b/", "/a/b/c", "/aaa/bbb/",
          "/en\n", "/en-us\n", "/de-ch-1901\n", "/en\n\n", "/en\nx", "/\n", "\n",
          "/é/", "/é", "/en-é/", "/en-é-us/", "/en-é-us-x/",
          "/é-en/", "/éñ中ß/", "/中文/",
          "/de-naïve/", "/中-文-字/", "/中-文-字-録/",
          "/α-β-γ/", "/а-б/", "/٠١٢/",
          "/é@ñ/", "/-é/", "/é-/", "/é--ñ/", "/é\n",
          "/×/", "/en×/", "/en-é×/", "/en–us/", "/en·us/",
          "/ /", "/en /", "/en€/", "/☃/", "/en…/"):
    checked += 1
    check(s)

# Exhaustive to length 4 over a CLASS-COMPLETE alphabet that straddles cp 128: an
# ASCII word char, a digit, the low line, both sub-tag separators, the path
# separator, an ASCII non-candidate, the newline, a non-ASCII letter, a non-ASCII
# ideograph, and a non-ASCII NON-word symbol. The decision depends only on these
# classes, so this exhausts the shape space at small length.
ALPHA = "a1_-@/.\né中×"
def gen(prefix, depth):
    global checked
    checked += 1
    check(prefix)
    if depth:
        for ch in ALPHA:
            gen(prefix + ch, depth - 1)
gen("", 4)

# Fuzz over a wide pool spanning both sides of cp 128.
rng = random.Random(15098)
POOL = list("abzAZ09_-@/. :;%~+!#\n\r\t") + [
    "é", "ñ", "ß", "中", "α", "а", "٠",
    "Ç", "ª", "א", "あ", "क",
    "×", "‐", " ", "«", "–", "©", "·",
    "…", "÷", "€", "☃"]
SUBTAGS = ["en", "de", "nan", "kl", "i", "zh", "x", "Latn", "US", "1996", "us",
           "é", "中", "ñ", "ß", "α", "аб"]
TAILS = ["/", "", "/x", "-z", "1", ".", "\n", "/\n", "\n\n", "\nx",
         "×", "–", " ", "€"]
for _ in range(60000):
    if rng.random() < 0.5:
        parts = [rng.choice(SUBTAGS) for _ in range(rng.randint(1, 5))]
        seps = [rng.choice("-@") for _ in range(len(parts) - 1)]
        s = "/" + parts[0] + "".join(a + b for a, b in zip(seps, parts[1:]))
        s += rng.choice(TAILS)
    else:
        s = "".join(rng.choice(POOL) for _ in range(rng.randint(0, 16)))
        if rng.random() < 0.7:
            s = "/" + s
    checked += 1
    check(s)

# A per-code-point sweep of the class boundary itself: this is the check that
# would catch the parse approximating the class by any enumeration instead of
# consuming the axiom. Both sides must be populated, else the sweep proves nothing.
n_word = n_nonword = 0
for c in (list(range(0, 0x300)) + list(range(0x370, 0x400))
          + list(range(0x4E00, 0x4E40)) + list(range(0x2000, 0x2040))
          + list(range(0xFF00, 0xFF20)) + list(range(0x600, 0x640))):
    if 0 <= c < 32 and c != 10:
        continue
    if 0xD800 <= c <= 0xDFFF:
        continue
    ch = chr(c)
    if is_word(c):
        n_word += 1
    else:
        n_nonword += 1
    for tmpl in ("/%s/", "/en-%s/", "/%s-en/", "/en-%s-us/", "/%s", "/e%sn/"):
        checked += 1
        check(tmpl % ch)
if not n_word or not n_nonword:
    print("VACUOUS sweep: saw %d word and %d non-word code points"
          % (n_word, n_nonword))
    sys.exit(1)

print("ax-ref-deep-parse-both-budgets OK: the structural parse == the real matcher "
      "at BOTH budgets on %d probed paths (ASCII and non-ASCII, no out-of-domain "
      "region); the class-boundary sweep saw %d word and %d non-word code points."
      % (checked, n_word, n_nonword))
sys.exit(0)
"""

# The two obligations of the ONE consumed axiom is_word(c), and of the A-reference
# built over it. Both are discharged by axiom_check.py under G-AX; recorded here so
# the manifest names every trust point of the proof. G-PBT ignores this lane by
# design, so one artifact is never judged twice by two gates with different oracles.
AXIOM_TESTS = [
    {
        "id": "ax-sound-is-word",
        "axiom": "is_word",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_IS_WORD,
        "rationale": (
            "the axiom's only Ensures is conditional on c < 128, where it pins the "
            "value to the decimal digits, the two cased letter runs and the low "
            "line. Two ways to be unsound, both probed: the real class could "
            "DISAGREE with that enumeration somewhere below 128 (checked "
            "exhaustively over all 128 code points), or the contract could "
            "over-claim at/above 128, where the real class is evaluated over the "
            "whole of Unicode — so the probe exhibits real members AND real "
            "non-members there, each of which the contract must permit, with a "
            "non-vacuity guard that both sides are actually populated. The open "
            "half is load-bearing in both directions: because nothing is entailed "
            "above 128, no implementation may decide that region for itself."
        ),
    },
    {
        "id": "ax-ref-deep-parse-both-budgets",
        "axiom": "prefix_len_spec (A-reference over is_word)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_DEEP_PARSE,
        "rationale": (
            "with is_word instantiated at its REAL counterpart rather than at any "
            "enumeration of it, the structural parse must equal the real matcher at "
            "BOTH budgets: prefix_len_spec(.,2) == the post-change matcher (what Q2 "
            "claims) and prefix_len_spec(.,1) == the pre-change one (so the model "
            "captures the exact behavioural delta and not merely the new side of "
            "it). There is NO out-of-domain region: paths carrying code points at "
            "or above 128 are ordinary probed inputs and a disagreement on one is a "
            "failure, so the probe deliberately includes non-ASCII letters, a "
            "non-ASCII digit, and non-ASCII NON-word characters in both accepting "
            "and rejecting positions."
        ),
    },
]
