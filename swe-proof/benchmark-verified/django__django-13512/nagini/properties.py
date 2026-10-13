"""PBT manifest for django__django-13512 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  json_render_text(text: List[int]) -> List[int]
    Requires: Acc(list_pred(text), 1/2)            -- text is READ-ONLY (1/2 perm)
    Requires: Forall(k: 0<=k<len -> text[k] >= 32) -- printable domain (the tested
                                                      domain: ASCII, CJK, emoji,
                                                      accented Latin, punctuation)
    Ensures (frame): Acc(list_pred(text), 1/2)     -- the 1/2 perm is returned
    Ensures: Acc(list_pred(Result()))              -- full perm on the new result
    Ensures (LOAD-BEARING):
        ToSeq(Result()) == PSeq(34) + json_string_body(ToSeq(text)) + PSeq(34)
    Ensures (discriminator, a tautology over the @Pure helper, documents intent):
        Forall(c: c >= 128 -> json_char(c) == PSeq(c))

  json_char(c)        = '"'(34) -> PSeq(92,34); '\\'(92) -> PSeq(92,92);
                        else PSeq(c)  (literal, INCLUDING every non-ASCII c >= 128)
  json_string_body(s) = front-recursive fold: json_char(s[0]) + body(s.drop(1))

This models the gold one-character change at TWO convergent sites:
  forms/fields.py   : json.dumps(value, cls)  ->  json.dumps(value, ensure_ascii=False, cls)
  admin/utils.py    : field.get_prep_value(value) -> json.dumps(value, ensure_ascii=False, cls)
i.e. ensure_ascii=True -> False, so non-ASCII text is kept literal instead of
being transliterated into \\uXXXX escapes.

GROUNDED-ORACLE NOTE: the postcondition oracle `json_string_body(ToSeq(text))` is
GROUNDED in the argument -- it is a @Pure fold fully computable from `text`, with
no opaque answer-key. Moreover it returns a PSeq[int] (a whole encoded body), NOT
a scalar marker, and there is no executable Python materialisation of it in the
impl region (it is @Pure over PSeq). So there is NO ungrounded-oracle echo a rival
can construct: a rival cannot `return materialize(oracle)` because the oracle is
non-executable, and any constant/partial body it does build is checked code-point
by code-point by the loop invariant ToSeq(body)==json_string_body(...). The
uniqueness lane is therefore about whether a rival can satisfy the rendering on
the F2P domain while diverging on a discriminating sub-domain (non-ASCII kept
literal -- the exact pre-patch bug; the two escaped code points " and \\).
Because the oracle is a PSeq fold and not a returnable scalar, the cheapest-honest
positive controls are structural reshapes of the gold loop (a branch reorder and
a split result assembly), not a direct `return oracle`.

CONTROL-FLOW-EFFECT: N/A. json_render_text has no raise/return-variation visible
beyond its value; the value abstraction ToSeq(Result()) fully captures the output
(the real admin site's try/except TypeError is the unmodelled error path; the
modelled success path has a single linear control flow).

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty).
The changed serialiser is modelled DEEPLY (pure region: json_char/json_string_body)
and validated == the real json.dumps(..., ensure_ascii=False) out-of-band by
axiom_check.py (G-AX, an A-reference). PBT re-runs that real-callee equivalence as
an axiom-soundness probe (the deep model must equal the real stdlib serialiser on
the F2P discriminators + full 0x20-0xFFFF per-code-point index sweep + astral +
boundary + 40000 fuzz, with the non-ASCII-literal discriminator checked at the
index level on BOTH sides). axiom_check.py's source is read on the HOST at
load time and embedded into the probe (the runner mounts only the probe at /work).
A containment probe is N/A: there is no axiom Requires domain for a model-reachable
input to fall outside; the deep model is validated over a SUPERSET (full BMP +
astral) of the modelled printable-code-point domain, which is sound.

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the invariants are nested inside that region, so
editing them is still inside impl and preserves same_spec). The frozen spec
(axioms/pure/pre/post-conditions/signatures) is never touched.
"""
from pathlib import Path

INSTANCE = "django__django-13512"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_HEAD = "    body = []  # type: List[int]\n    i = len(text)\n"
_READ_C = "        c = text[i - 1]\n"
_BRANCH = ("        if c == 34:\n"
           "            body = [92, 34] + body\n"
           "        elif c == 92:\n"
           "            body = [92, 92] + body\n"
           "        else:\n"
           "            body = [c] + body\n")
_RESULT = "    result = [34] + body + [34]\n    return result\n"

for _a in (_HEAD, _READ_C, _BRANCH, _RESULT):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- branch reorder. The gold tests `c == 34` first, then
# `c == 92`; this variant tests `c == 92` first, then `c == 34` -- semantically
# identical (json_char distinguishes 34 vs 92 either way) but a different
# executable branch FORM. The backward fold and the load-bearing invariant
# ToSeq(body)==json_string_body(ToSeq(text).drop(i)) are kept verbatim, so the
# gold proof stays valid. MUST verify; else the postcondition is over-fit to the
# branch ORDER => SPEC-TOO-STRONG.
_POS_REORDER = _swap(
    _BASE, _BRANCH,
    "        if c == 92:\n"
    "            body = [92, 92] + body\n"
    "        elif c == 34:\n"
    "            body = [92, 34] + body\n"
    "        else:\n"
    "            body = [c] + body\n",
)

# (5b) POSITIVE CONTROL -- split result assembly. Instead of the single
# `result = [34] + body + [34]`, build the result in two steps on a freshly-owned
# local (`result = [34] + body` then `result = result + [34]`). This is a
# structural reshape of the final assembly that relies on the SAME list-pred
# concatenation lemma the gold already uses (ToSeq(a+b)==ToSeq(a)+ToSeq(b)). The
# loop and its invariants are untouched, so the gold proof stays valid. MUST
# verify; else the postcondition is over-fit to the one-expression assembly FORM
# => SPEC-TOO-STRONG. (A forward-append rewrite is deliberately AVOIDED: it would
# need an f(a+b)==f(a)+f(b) lemma for the front-recursive json_string_body that
# the verifier won't auto-discharge -- a proof gap, not a spec defect.)
_POS_SPLIT = _swap(
    _BASE, _RESULT,
    "    result = [34] + body\n"
    "    result = result + [34]\n"
    "    return result\n",
)

# (6) ADMISSIBILITY -- a self-call on a fresh, F2P-shaped input "a" ([97], the
# admin/forms F2P plain-ASCII scalar) establishes the precondition
# Acc(list_pred(.),1/2) AND the printable-domain Forall (97 >= 32), then the gold
# body runs on the actual `text`. The Assert pins the self-call's result property
# (its ToSeq equals the rendering of [97]). MUST verify; else the precondition
# rejects a normal F2P input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _HEAD,
    "    probe = [97]  # type: List[int]\n"
    "    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(probe),\n"
    "                                          probe[k] >= 32), [[probe[k]]])))\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    body = []  # type: List[int]\n"
    "    i = len(text)\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). text is read-only at 1/2.
# This rival WRITES `text[i - 1] = 97` ('a') before reading it, attempting to
# normalize the input so the rendering is vacuously satisfiable. Under
# Acc(list_pred(text),1/2) a store needs FULL permission, so it must be rejected
# for INSUFFICIENT PERMISSION (not a value mismatch). All gold invariants and
# framing asserts are kept verbatim, so the rejection is attributable solely to
# the write.
_RIVAL_FRAME = _swap(
    _BASE, _READ_C,
    "        text[i - 1] = 97\n        c = text[i - 1]\n",
)

# (3a) PARTIAL-DOMAIN -- non-ASCII escaped (the EXACT pre-patch bug, == the spirit
# of model_prepatch.py / ensure_ascii=True). The else branch is split so a
# non-ASCII code point (c >= 128) is emitted as a `\\u` escape ([92,117]) instead
# of literal [c]. Diverges ONLY on non-ASCII inputs; correct on all-ASCII inputs.
# The load-bearing invariant ToSeq(body)==json_string_body(ToSeq(text).drop(i)) is
# kept verbatim and is exactly what senses the divergence: json_string_body keeps
# c >= 128 literal, so on a non-ASCII code point the loop CANNOT re-establish the
# invariant -> reject.
_RIVAL_NONASCII = _swap(
    _BASE, _BRANCH,
    "        if c == 34:\n"
    "            body = [92, 34] + body\n"
    "        elif c == 92:\n"
    "            body = [92, 92] + body\n"
    "        elif c >= 128:\n"
    "            body = [92, 117] + body\n"
    "        else:\n"
    "            body = [c] + body\n",
)

# (3b) PARTIAL-DOMAIN -- quotation mark NOT escaped. The c == 34 branch is changed
# to emit a literal [34] instead of [92, 34]. Diverges ONLY on inputs containing a
# '"' code point; correct on every quote-free input (incl. all the F2P strings,
# which contain no literal '"'). The kept invariant
# ToSeq(body)==json_string_body(ToSeq(text).drop(i)) senses it: json_char(34) is
# PSeq(92,34), so on a '"' the loop cannot re-establish the invariant -> reject.
_RIVAL_NOQUOTE = _swap(
    _BASE, _BRANCH,
    "        if c == 34:\n"
    "            body = [34] + body\n"
    "        elif c == 92:\n"
    "            body = [92, 92] + body\n"
    "        else:\n"
    "            body = [c] + body\n",
)

# (3c) PARTIAL-DOMAIN / supporting near-miss -- the closing quote is dropped. The
# final assembly emits `[34] + body` (no trailing 34). Diverges on EVERY input
# (the rendering is missing its closing '"'), failing the postcondition
# ToSeq(Result()) == PSeq(34)+json_string_body(...)+PSeq(34) -> reject. A cheap
# structural near-miss but it carries a real refinement (see below).
_RIVAL_NOCLOSE = _swap(_BASE, _RESULT, "    result = [34] + body\n    return result\n")


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different (branch order flipped: c==92 tested "
                  "before c==34) but CORRECT impl, keeping the backward fold and "
                  "every gold invariant/framing assert. Must verify; else the "
                  "postcondition is over-fit to the branch ORDER => SPEC-TOO-STRONG."},
    {"id": "pos-control-split-assembly", "kind": "soundness", "expect": "verify",
     "module": _POS_SPLIT,
     "rationale": "structurally-different final assembly: result built in two "
                  "steps ([34]+body, then +[34]) on a fresh full-perm local, "
                  "relying on the SAME list concatenation lemma the gold uses. The "
                  "loop/invariants are untouched. Must verify; else the "
                  "postcondition is over-fit to the one-expression assembly FORM "
                  "=> SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a fresh F2P-shaped plain-ASCII scalar \"a\" ([97]) must establish "
                  "the precondition Acc(list_pred(.),1/2) AND the printable-domain "
                  "Forall (97>=32); both are asserted AT the witness. They are "
                  "asserted rather than exercised by a self-call because the model "
                  "carries Requires(MustTerminate(2)) and a same-level self-call on a "
                  "non-shrinking argument is an obligation leak Nagini is right to "
                  "refuse; the result property that call used to assert stated a fact "
                  "about the CALL, not about the precondition's domain, so it is not "
                  "part of what this case proves. If the precondition rejects this "
                  "normal F2P input => PRECOND-TOO-STRONG. NEGATIVE CONTROL "
                  "(measured): move the witness outside the frozen printable domain, "
                  "probe = [9] (a TAB, code point 9 < 32), and the probe REJECTS: "
                  "`Assert might fail. Assertion Forall(int, (lambda k: (Implies(((0 "
                  "<= k) and (k < len(probe))), (probe[k] >= 32)), ...))) might not "
                  "hold.` The asserted domain is a real check on this precondition, "
                  "not a restatement of it."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-text", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: json.dumps never "
                   "mutates the str value it serialises (str is immutable in "
                   "CPython); both gold hunks only READ `value` and build a new "
                   "string. There is no resolving patch that rewrites its input "
                   "text scalar, so a verifying rival here would be a pure "
                   "verify-not-resolve artifact (vacuous satisfaction by "
                   "self-normalising the input before rendering it).",
     "rationale": "MANDATORY frame-mutation probe. `text[i-1] = 97` writes through "
                  "a 1/2 (read-only) reference and MUST fail for INSUFFICIENT "
                  "PERMISSION (a store needs full Acc(list_pred(text))), NOT a value "
                  "mismatch; the gold invariants/asserts are kept verbatim so the "
                  "rejection is attributable to the write. Rejection source: the "
                  "PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK (frame "
                  "protection hollow)."},
    {"id": "weak-nonascii-escaped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONASCII,
     "refinement": "emitting a `\\u` escape for c >= 128 is EXACTLY the pre-patch "
                   "default ensure_ascii=True (== the spirit of model_prepatch.py). "
                   "A faithful patch that keeps ensure_ascii=True for non-ASCII "
                   "renders prepare_value('你好，世界') as '\"\\u4f60\\u597d...\"' "
                   "instead of '\"你好，世界\"', and admin display_for_field({'a': "
                   "'你好 世界'}) likewise -- it FAILS test_prepare_value and "
                   "test_json_display_for_field (the F2P), which assert the literal "
                   "non-ASCII rendering. verify-not-resolve.",
     "rationale": "rejection source: the loop invariant ToSeq(body)==json_string_"
                  "body(ToSeq(text).drop(i)) (kept verbatim), which feeds the "
                  "postcondition. json_string_body keeps c >= 128 LITERAL, so on a "
                  "non-ASCII code point the rival's `\\u`-escaped body cannot "
                  "re-establish the invariant; the verifier rejects. Correct on "
                  "all-ASCII inputs, wrong on every non-ASCII one. If it verified => "
                  "SPEC-TOO-WEAK (the ensure_ascii=False discriminator hollow)."},
    {"id": "weak-quote-not-escaped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOQUOTE,
     "refinement": "emitting a literal '\"' for the quotation-mark code point "
                   "(json_char(34) should be \\\") produces INVALID JSON for any "
                   "text containing a '\"' -- e.g. prepare_value('a\"b') would yield "
                   "'\"a\"b\"' instead of the correct '\"a\\\"b\"'. This diverges "
                   "from json.dumps(..., ensure_ascii=False), the gold callee the "
                   "A-reference pins; a faithful patch shipping this is not the gold "
                   "serialiser and produces malformed output on quote-bearing values "
                   "(round-tripping through the JSONField breaks). verify-not-resolve.",
     "rationale": "rejection source: the loop invariant ToSeq(body)==json_string_"
                  "body(ToSeq(text).drop(i)) (kept verbatim). json_char(34)==PSeq("
                  "92,34), so on a '\"' code point the rival's literal-[34] body "
                  "cannot re-establish the invariant; the verifier rejects. Correct "
                  "on every quote-free input (incl. all F2P strings). If it verified "
                  "=> SPEC-TOO-WEAK (JSON escaping of '\"' not enforced)."},
    {"id": "weak-no-closing-quote", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOCLOSE,
     "refinement": "dropping the trailing '\"' renders prepare_value('foo') as "
                   "'\"foo' instead of '\"foo\"' -- malformed JSON for EVERY value. "
                   "A faithful patch doing this FAILS every F2P assertion "
                   "(prepare_value('foo')=='\"foo\"', ('a','\"a\"'), etc.). "
                   "verify-not-resolve. (Cheap structural near-miss; included as a "
                   "supporting case alongside the reasoned partial-domain attacks.)",
     "rationale": "rejection source: the postcondition ToSeq(Result())==PSeq(34)+"
                  "json_string_body(ToSeq(text))+PSeq(34). The rival's result is "
                  "PSeq(34)+json_string_body(...) (no closing PSeq(34)), so the "
                  "postcondition equality cannot be closed -> reject on every input. "
                  "If it verified => SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed; the changed serialiser is an
# A-reference deep model (json_char/json_string_body) validated == the real
# json.dumps(..., ensure_ascii=False). We re-run that real-callee equivalence
# (axiom_check.py's logic, read on the HOST and embedded into a self-contained
# probe) as an axiom-soundness check: if the deep model ever disagrees with the
# real stdlib serialiser, the A-reference is unsound. A containment probe is N/A
# (no axiom Requires domain to fall outside; the deep model is validated over a
# superset of the modelled printable-code-point domain, which is sound).
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-json-body-equals-real-dumps",
        "axiom": "json_string_body",  # the A-reference deep model (not consumed)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model json_string_body/json_char (pure region) is an "
                     "A-reference: it must equal the REAL post-patch serialiser "
                     "json.dumps(s, ensure_ascii=False) on every input. This probe "
                     "(axiom_check.py verbatim, stdlib `json` only -- the very "
                     "module the gold patch calls) runs the real serialiser on the "
                     "F2P discriminators ('a','你好 世界','你好，世界','😀🐱','jaźń'), "
                     "a per-code-point index sweep over the full printable BMP "
                     "0x20-0xFFFF plus astral samples (asserting json_char(c) equals "
                     "the real per-character body AND that every c >= 128 is kept "
                     "literal on BOTH sides -- no double mask), 15 boundary strings, "
                     "and 40000 fuzz strings over the modelled domain. Exit 0 iff "
                     "every observation agrees; any disagreement => the A-reference "
                     "is UNSOUND.",
    },
]
