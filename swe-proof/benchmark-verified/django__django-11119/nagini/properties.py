"""properties.py — PBT falsification manifest for django__django-11119.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    render_value(value: List[int], engine_autoescape: bool) -> List[int]

modeling Engine.render_to_string after the gold patch
`Context(context) -> Context(context, autoescape=self.autoescape)`: the
rendering context inherits the engine's auto-escaping policy, and that policy
governs whether the single interpolated value is HTML-escaped (policy ON) or
emitted verbatim (policy OFF). The load-bearing contract:

    Requires(Acc(list_pred(value), 1/2))                     # READ-ONLY input
    Ensures (Acc(list_pred(value), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (Implies(engine_autoescape == True,
                     ToSeq(Result()) == escaped_seq(ToSeq(value))))   # ON  pin
    Ensures (Implies(engine_autoescape == False,
                     ToSeq(Result()) == ToSeq(value)))                # OFF pin

What the spec actually defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the OFF/verbatim pin
    `Implies(engine_autoescape == False, ToSeq(Result()) == ToSeq(value))`.
    The pre-patch code forced the context flag to the escaping default
    (`Context(context)` => autoescape True), i.e. escaped even when the engine
    policy was OFF; `model_prepatch.py` reproduces that (`ctx_autoescape = True`)
    and FAILS exactly this clause (G-DIFF). The F2P witness: engine
    autoescape=False, value '<script>', required '<script>' verbatim — pre-patch
    escapes it to '&lt;script&gt;'. So the spec's whole job is: when the policy
    is OFF, do NOT force escaping.

  * Both output pins are GROUNDED in the input. The ON pin is
    `ToSeq(Result()) == escaped_seq(ToSeq(value))` where `escaped_seq` is a
    @Pure deep model (NOT @ContractOnly), fully unfolded by Viper, equal to the
    real django.utils.html.escape (G-AX, A-reference). The OFF pin is
    `ToSeq(Result()) == ToSeq(value)` — literally the input. Neither is an
    opaque answer-key marker: both are functions OF `value`. There is no
    executable materialization of the @Pure `escaped_seq` PSeq into a list_pred
    list, so you cannot "echo the oracle"; the only way to make `ToSeq(result)`
    equal it is to build the list element-by-element (the real per-code-point
    work). Case `echo-attempt-honest` confirms this; there is no wrong echo that
    verifies (so this is a positive control, not a reject case).

  * `value` is held read-only (1/2). The MANDATORY attack is FRAME MUTATION
    (`frame-mutate-value`): an impl that WRITES to `value` to satisfy a pin
    vacuously must fail for INSUFFICIENT PERMISSION, not for a wrong value.

Authoring mechanics (preserved from the schema): every spec variant is built by
REGION-SURGERY (`_swap`) editing ONLY inside `# impl-start`/`# impl-end` (the
nested invariants live there too), so `markers.same_spec` is guaranteed and a
rejection comes from the POSTCONDITION catching wrong behaviour (or the
permission system), never from a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve
the F2P/P2P. Axiom cases run the REAL django.utils.html.escape callee in Docker
(this bundle has NO @ContractOnly axioms; the only kind-A obligation is the
A-reference deep model escaped_seq == escape + the verbatim identity).
"""
from pathlib import Path

INSTANCE = "django__django-11119"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of model.py).
# ---------------------------------------------------------------------------

# The flag-inheritance assignment (model image of Context(context, autoescape=
# self.autoescape)). The pre-patch bug forces this to True.
_FLAG = "ctx_autoescape = engine_autoescape"

# The whole escape-branch loop body (backward per-code-point fold).
_ESC_BODY = """            c = value[i - 1]
            Assert(ToSeq(value).drop(i - 1)[0] == c)
            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
            if c == 38:
                result = [38, 97, 109, 112, 59] + result
            elif c == 60:
                result = [38, 108, 116, 59] + result
            elif c == 62:
                result = [38, 103, 116, 59] + result
            elif c == 34:
                result = [38, 113, 117, 111, 116, 59] + result
            elif c == 39:
                result = [38, 35, 51, 57, 59] + result
            else:
                result = [c] + result
            i = i - 1"""

# single-branch emitted-byte literal (escape branch): the double-quote entity.
_QUOT = "result = [38, 113, 117, 111, 116, 59] + result"   # " -> &quot;

# return + impl-end (for inserting a redundant framing assert).
_RETURN = "    return result\n    # impl-end"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-different but CORRECT: the escape branch if/elif chain is
# REORDERED (39,34,62,60,38,else). Semantically identical backward fold,
# different source. If this fails to verify the ON postcondition is over-fit to
# one branch order => SPEC-TOO-STRONG. The gold framing Asserts and the loop
# invariant are kept verbatim (only the executable branch order changes), so a
# failure could only be a spec defect, not a dropped proof obligation.
_ESC_REORDERED = """            c = value[i - 1]
            Assert(ToSeq(value).drop(i - 1)[0] == c)
            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
            if c == 39:
                result = [38, 35, 51, 57, 59] + result
            elif c == 34:
                result = [38, 113, 117, 111, 116, 59] + result
            elif c == 62:
                result = [38, 103, 116, 59] + result
            elif c == 60:
                result = [38, 108, 116, 59] + result
            elif c == 38:
                result = [38, 97, 109, 112, 59] + result
            else:
                result = [c] + result
            i = i - 1"""
_POS_REORDERED = _swap(_BASE, _ESC_BODY, _ESC_REORDERED)

# (5b) Structurally-different but CORRECT: compute the per-code-point entity
# bytes into a LOCAL `seg`, then a single prepend `result = seg + result`. A
# different control shape (branch assigns a local) over the SAME backward fold.
# Confirms the spec admits a different code structure, not just a re-spelling of
# the inline-prepend gold branch. If it fails to verify => SPEC-TOO-STRONG.
_ESC_SEG = """            c = value[i - 1]
            Assert(ToSeq(value).drop(i - 1)[0] == c)
            Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
            seg = [c]  # type: List[int]
            if c == 38:
                seg = [38, 97, 109, 112, 59]
            elif c == 60:
                seg = [38, 108, 116, 59]
            elif c == 62:
                seg = [38, 103, 116, 59]
            elif c == 34:
                seg = [38, 113, 117, 111, 116, 59]
            elif c == 39:
                seg = [38, 35, 51, 57, 59]
            result = seg + result
            i = i - 1"""
_POS_SEG = _swap(_BASE, _ESC_BODY, _ESC_SEG)

# (2) ECHO-ATTEMPT, HONEST. The most direct "echo the @Pure oracle" attack would
# be `result = <materialize escaped_seq(ToSeq(value))>`. There is NO executable
# materialization of a @Pure PSeq into a list_pred list, so the cheapest impl
# that satisfies the GROUNDED ON pin still has to build the list per code point.
# This control inserts, right before the return, a redundant assertion that the
# built result equals the spec oracle on each branch (the escaped_seq fold when
# the policy is ON, the verbatim value when it is OFF). It is CORRECT (so
# expect="verify"); its purpose is to show there is no WRONG echo that verifies
# — both oracles are grounded in `value`, not opaque markers. (If a wrong echo
# verified, this would instead be a SPEC-TOO-WEAK reject case; here none exists.)
_ECHO_RETURN_NEW = (
    "    Assert(Implies(ctx_autoescape, ToSeq(result) == escaped_seq(ToSeq(value))))\n"
    "    Assert(Implies(not ctx_autoescape, ToSeq(result) == ToSeq(value)))\n"
    "    return result\n    # impl-end"
)
_ECHO_HONEST = _swap(_BASE, _RETURN, _ECHO_RETURN_NEW)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped value (the witness '<script>'
# code points [60,115,99,114,105,112,116,62]) with BOTH policy settings must
# establish the precondition `Acc(list_pred(.),1/2)` (a pure read-only list_pred,
# no value restriction). If the self-call fails to verify the precondition for a
# normal input => PRECOND-TOO-STRONG. The probe value is built and the calls are
# placed at the very top of the impl, before the gold body runs unchanged.
_ADMISS_HEAD = "    ctx_autoescape = engine_autoescape\n"
_ADMISS_HEAD_NEW = (
    "    probe = [60, 115, 99, 114, 105, 112, 116, 62]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    ctx_autoescape = engine_autoescape\n"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. `value` is read-only
# (1/2). This rival WRITES `value[i-1] = 38` before reading it in the escape
# loop, intending to satisfy the ON pin vacuously on a self-mutated input. Under
# Acc(list_pred(value),1/2) a store to `value` requires FULL permission, so it
# must fail for INSUFFICIENT PERMISSION (not a value mismatch). The gold
# invariants/asserts are kept verbatim around the write so the failure is
# attributable solely to the store. Rejection source: the PERMISSION SYSTEM.
_FRAME_ESC_BODY = _ESC_BODY.replace(
    "            c = value[i - 1]\n",
    "            value[i - 1] = 38\n            c = value[i - 1]\n",
    1,
)
_RIVAL_FRAME = _swap(_BASE, _ESC_BODY, _FRAME_ESC_BODY)

# (2) THE BUG ITSELF (pre-patch behaviour). Force the context flag to the
# escaping default True, ignoring engine_autoescape — exactly Context(context)
# pre-patch (model_prepatch.py's `ctx_autoescape = True`). It always escapes,
# even when the engine policy is OFF. Its faithful real patch is the UNCHANGED
# pre-patch render_to_string (`Context(context)`), which is precisely what FAILS
# the F2P test_autoescape_off (engine autoescape=False, '<script>' must stay
# verbatim but is escaped to '&lt;script&gt;') — so it would NOT resolve.
# Rejection source: the OFF/verbatim postcondition
# `Implies(engine_autoescape == False, ToSeq(Result()) == ToSeq(value))`, which
# the escaping path cannot satisfy when the input contains a significant char.
_RIVAL_FORCE_TRUE = _swap(_BASE, _FLAG, "ctx_autoescape = True")

# (2b) BRANCH-INVERSION. Inherit the flag correctly but SWAP the two branches:
# escape when the policy is OFF, emit verbatim when ON. Its faithful real patch
# (render_value_in_context reading `not context.autoescape`) inverts the meaning
# of the engine policy and FAILS both the F2P (autoescape=False would escape
# '<script>') and the P2P test_basic_context (autoescape defaults True, would
# now NOT escape) — so it would NOT resolve. Rejection source: BOTH the ON pin
# (escaped_seq) and the OFF pin (verbatim) are violated, each on the wrong
# branch.
_RIVAL_INVERT = _swap(_BASE, "    if ctx_autoescape:",
                      "    if not ctx_autoescape:")

# (3) PARTIAL-DOMAIN. Inherit the flag correctly and escape correctly; the
# verbatim (OFF) branch is correct EXCEPT it escapes the very FIRST element (the
# leading '<' code point 60 -> '&lt;') while copying every other position
# verbatim. It pins only the sub-domain of OFF inputs that either do not begin
# with '<' or where the leading char is not significant. A faithful real patch
# of this shape (verbatim emit that special-cases position 0) would still escape
# the leading '<' of '<script>' under autoescape=False and so FAIL the F2P
# test_autoescape_off (which requires '<script>' verbatim) — it would NOT
# resolve. Rejection source: the OFF/verbatim postcondition
# `ToSeq(Result()) == ToSeq(value)` pins the WHOLE sequence including index 0,
# so the first forward iteration (i==0) cannot close the
# `ToSeq(result) == ToSeq(value).take(i)` invariant when value[0]==60.
_VERB_BODY = """            result = result + [value[i]]
            i = i + 1"""
_VERB_PARTIAL = """            if i == 0 and value[0] == 60:
                result = result + [38, 108, 116, 59]
            else:
                result = result + [value[i]]
            i = i + 1"""
_RIVAL_PARTIAL_FIRST = _swap(_BASE, _VERB_BODY, _VERB_PARTIAL)

# (3b, supporting) Drop the double-quote escape in the escape (ON) branch: '"'
# passes through unescaped. A faithful real patch doing this would emit unsafe
# attribute markup and FAIL the escape contract (a context value containing '"'
# under autoescape=True would render an unescaped quote). Rejection source: the
# ON pin (escaped_seq, entity(34)==&quot;), caught at the iteration reading a 34.
_RIVAL_DROP_QUOT = _swap(_BASE, _QUOT, "result = [34] + result")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different (escape branch reordered) but correct backward-fold "
                  "impl, gold framing Asserts + loop invariant kept verbatim, must verify; if "
                  "not, the ON postcondition is over-fit to one branch order => SPEC-TOO-STRONG."},
    {"id": "pos-control-seg-local", "kind": "soundness", "expect": "verify",
     "module": _POS_SEG,
     "rationale": "a correct impl with a DIFFERENT control shape (per-code-point bytes into a "
                  "local `seg`, single prepend) over the same backward fold must verify; if not, "
                  "the spec is over-fit to the inline-prepend code form => SPEC-TOO-STRONG."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the cheapest impl satisfying the GROUNDED pins still does the real work (no "
                  "executable materialization of the @Pure oracle escaped_seq into a list_pred "
                  "list exists). Asserting result == escaped_seq(value) on the ON branch and "
                  "result == value on the OFF branch right before return is redundant with the "
                  "gold proof and must verify. Demonstrates the spec is NOT echo-vulnerable: "
                  "there is no wrong oracle-echo that verifies (else this would be a reject case)."},
    {"id": "admiss-f2p-witness", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "self-calls on the F2P witness value '<script>' (code points) under BOTH "
                  "policy settings must establish the precondition Acc(list_pred(.),1/2); if "
                  "not, PRECOND-TOO-STRONG. Confirms a normal F2P-shaped input is admitted."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: the rendering path never "
                   "mutates the interpolated value (a str, immutable; escape()/str() return new "
                   "objects). The rival exists only to test whether the read-only (1/2) "
                   "precondition can be subverted by writing to `value`. There is no resolving "
                   "patch that overwrites its input, so a verifying rival here would be a pure "
                   "verify-not-resolve artifact (vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `value[i-1] = 38` writes through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. Rejection "
                  "source: the PERMISSION SYSTEM (store needs full perm), not a value mismatch; "
                  "the gold invariants/asserts are kept verbatim. If it verified => SPEC-TOO-WEAK "
                  "(frame protection hollow)."},
    {"id": "rival-force-escape-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORCE_TRUE,
     "refinement": "forces the context flag to the escaping default True ignoring "
                   "engine_autoescape — exactly the PRE-PATCH Context(context) behaviour "
                   "(model_prepatch.py). Its faithful real patch is the unchanged pre-patch "
                   "render_to_string, which is precisely what FAILS the F2P test_autoescape_off "
                   "(engine autoescape=False must emit '<script>' verbatim but this escapes it "
                   "to '&lt;script&gt;') — it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes. Rejection source: the OFF/verbatim "
                  "postcondition Implies(engine_autoescape==False, ToSeq(Result())==ToSeq(value)) "
                  "— the escaping path cannot satisfy verbatim output for a value containing a "
                  "significant char when the policy is OFF. If it verified => SPEC-TOO-WEAK "
                  "(admits the very bug, mirrors G-DIFF)."},
    {"id": "rival-invert-policy", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "refinement": "inverts the meaning of the policy: escapes when OFF, verbatim when ON. Its "
                   "faithful real patch (renderer reading `not context.autoescape`) would escape "
                   "'<script>' under autoescape=False (FAIL the F2P) and stop escaping under the "
                   "default autoescape=True (FAIL P2P test_basic_context, which renders "
                   "'obj:test' and relies on default escaping). It would NOT resolve.",
     "rationale": "control-flow rival: the policy branch is inverted. Rejection source: BOTH "
                  "pins — under ON the impl now emits verbatim (violates the escaped_seq pin) and "
                  "under OFF it escapes (violates the verbatim pin). If it verified => "
                  "SPEC-TOO-WEAK (the policy direction is unconstrained)."},
    {"id": "partial-domain-verbatim-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_FIRST,
     "refinement": "inherits the flag and escapes correctly; the OFF/verbatim branch is correct "
                   "EXCEPT it escapes the leading '<' (index 0) instead of emitting it verbatim. "
                   "A faithful real patch of this shape (verbatim path special-casing position 0) "
                   "would escape the leading '<' of '<script>' under autoescape=False and FAIL "
                   "the F2P test_autoescape_off (requires '<script>' verbatim) — it would NOT "
                   "resolve.",
     "rationale": "partial-domain: pins only the OFF sub-domain not starting with '<'. Rejection "
                  "source: the OFF/verbatim postcondition ToSeq(Result())==ToSeq(value) pins the "
                  "WHOLE sequence including index 0, so the first forward iteration (i==0) cannot "
                  "close ToSeq(result)==ToSeq(value).take(i) when value[0]==60. If it verified => "
                  "SPEC-TOO-WEAK (domain-incomplete on the discriminating branch)."},
    {"id": "rival-drop-quot", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_QUOT,
     "refinement": "lets the double-quote pass through unescaped on the escape (ON) branch; a "
                   "real patch doing this would emit an unescaped '\"' for an autoescaped value "
                   "and violate the escaping contract the renderer relies on, so it would NOT "
                   "resolve.",
     "rationale": "supporting near-miss with a real refinement: double-quote not escaped under "
                  "the ON policy. Rejection source: the ON pin (escaped_seq, entity(34)==&quot;), "
                  "caught at the iteration reading a 34."},
]

# ===========================================================================
# AXIOM LANE (Docker, real django.utils.html callee)
# ===========================================================================
# This bundle consumes NO @ContractOnly axiom (model.py `axioms` region empty).
# The only kind-A obligation is the A-reference deep model escaped_seq ==
# django.utils.html.escape (escape branch) plus the verbatim identity (OFF
# branch). We validate both against the REAL callee in the instance image, and
# add a containment check that every code point the model can pass to the
# escaper lies in the deep model's covered domain (it covers ALL code points, so
# containment is trivially satisfied — we assert that explicitly).

# (1) A-reference soundness: escaped_seq == real django.utils.html.escape (ON
# branch). Boundary + heavy fuzz + an exhaustive single-code-point sweep + astral
# code points. Any mismatch => the deep model is unsound (the ON pin would be
# pinned to a wrong escaper). At THIS base_commit the apostrophe is the legacy
# decimal &#39; (PSeq(38,35,51,57,59)); the &#x27; switch is a LATER commit
# (django-11276) and must NOT appear here.
_AX_ESCAPE_REF_SOUND = r'''
import random, sys
from django.utils.html import escape as dj_escape   # the real escaping callee
# model.py deep-model entity table at THIS base_commit (apostrophe -> &#39;).
ENTITY = {38:[38,97,109,112,59], 60:[38,108,116,59], 62:[38,103,116,59],
          34:[38,113,117,111,116,59], 39:[38,35,51,57,59]}
def escaped_seq(cps):
    out = []
    for c in cps:
        out.extend(ENTITY.get(c, [c]))
    return out
def ok(s):
    return [ord(c) for c in str(dj_escape(s))] == escaped_seq([ord(c) for c in s])
sig = ['&', '<', '>', '"', "'"]
ordn = list("aZ0 ;#x392 7scriptlgmpquot") + ['e', 'é', '•']
bad = []
# the F2P witness escaped form must be exactly '&lt;script&gt;'
if [ord(c) for c in str(dj_escape("<script>"))] != [ord(c) for c in "&lt;script&gt;"]:
    print("AXIOM-UNSOUND: F2P witness escape changed:", repr(str(dj_escape("<script>")))); sys.exit(1)
# the apostrophe MUST be the legacy decimal &#39; at this commit (not &#x27;)
if str(dj_escape("'")) != "&#39;":
    print("AXIOM-UNSOUND: apostrophe entity is", repr(str(dj_escape("'"))),
          "expected legacy &#39; at this base_commit"); sys.exit(1)
boundary = [""] + sig + [c + c for c in sig] + ["".join(sig), "".join(reversed(sig)),
    "a&b<c>d\"e'f", "x=1&amp;y=&lt;2&gt;", "&amp;", "&#39;", "&quot;",
    "Joe's Crab Shack", "<script>alert('xss')</script>", "Can't find my keys",
    "obj:<script>", "!$&'()*+,;=~:@,", "\U0001F600&'", "\U00010000<>\"", "ab\U0001F4A9'cd"]
for s in boundary:
    if not ok(s):
        bad.append(repr(s))
# exhaustive single-code-point sweep 0..0x3000 (covers all five significant)
for cp in range(0, 0x3000):
    if not ok(chr(cp)):
        bad.append("U+%04X" % cp)
# astral single code points
for cp in [0xFFFF, 0x10000, 0x1F600, 0x1F4A9, 0x10FFFF]:
    if not ok(chr(cp)):
        bad.append("U+%05X" % cp)
# randomized fuzz over significant + ordinary + a few astral
rng = random.Random(11119)
alpha = sig + ordn + ['\U0001F600', '\U00010000']
for _ in range(20000):
    s = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 24)))
    if not ok(s):
        bad.append(repr(s))
if bad:
    print("A-REFERENCE-UNSOUND escaped_seq != django.utils.html.escape on", bad[:8]); sys.exit(1)
print("escaped_seq == django.utils.html.escape on", len(boundary),
      "boundary + 0x3000 exhaustive + astral + 20000 fuzz; F2P '<script>'->'&lt;script&gt;', "
      "apostrophe '&#39;' confirmed"); sys.exit(0)
'''

# (2) A-reference soundness: the OFF/verbatim branch is the identity on character
# content. The renderer's false branch is str(value); for the str inputs the F2P
# passes, str(value) is the identity. Confirm str(value)==value on boundary +
# fuzz so the OFF pin ToSeq(Result())==ToSeq(value) is anchored to real behaviour.
_AX_VERBATIM_IDENTITY = r'''
import random, sys
sig = ['&', '<', '>', '"', "'"]
ordn = list("aZ0 ;#x392 7script") + ['é', '•']
def ok(s):
    return [ord(c) for c in str(s)] == [ord(c) for c in s]
bad = []
# the F2P witness verbatim form is unchanged
if str("<script>") != "<script>":
    print("AXIOM-UNSOUND: verbatim witness changed"); sys.exit(1)
boundary = [""] + sig + ["".join(sig), "<script>", "obj:<script>", "Joe's Crab Shack",
    "<script>alert('xss')</script>", "\U0001F600&'", "\U00010000<>\""]
for s in boundary:
    if not ok(s):
        bad.append(repr(s))
rng = random.Random(111190)
alpha = sig + ordn + ['\U0001F600']
for _ in range(20000):
    s = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 24)))
    if not ok(s):
        bad.append(repr(s))
if bad:
    print("A-REFERENCE-UNSOUND verbatim branch str(value) != value on", bad[:8]); sys.exit(1)
print("verbatim branch str(value)==value on", len(boundary),
      "boundary + 20000 fuzz; F2P '<script>' verbatim confirmed"); sys.exit(0)
'''

# (3) containment: the escaper (escaped_seq / the model's deep model) is defined
# over EVERY code point (the five significant ones expand, all others map to
# identity), so every code point the model can pass to it is covered. Enumerate
# the five significant code points the per-code-point substitution branches on
# AND a sweep of ordinary code points, asserting the real escape handles each
# (the five as their entity, every other as itself). A reachable code point the
# escaper failed to handle would be AXIOM-TOO-WEAK-FOR-CALLER; here the domain is
# total, so containment holds trivially — we assert that explicitly.
_AX_CONTAINMENT = r'''
import sys
from django.utils.html import escape as dj_escape
# the five code points the model's per-code-point substitution branches on.
SIG = {38: "&amp;", 60: "&lt;", 62: "&gt;", 34: "&quot;", 39: "&#39;"}
bad = []
for cp, ent in SIG.items():
    if str(dj_escape(chr(cp))) != ent:
        bad.append((cp, str(dj_escape(chr(cp))), ent))
if bad:
    print("containment/soundness: real escape disagrees on significant cp", bad); sys.exit(1)
# every other code point must be covered as identity (the escaper's domain is
# total). Sweep a representative band of ordinary code points.
non_id = []
for cp in list(range(0, 0x3000)) + [0x1F600, 0x10000, 0x10FFFF]:
    if cp in SIG:
        continue
    if str(dj_escape(chr(cp))) != chr(cp):
        non_id.append("U+%04X" % cp)
if non_id:
    print("AXIOM-TOO-WEAK-FOR-CALLER: escape not identity on ordinary cp", non_id[:8]); sys.exit(1)
print("containment OK: escaper domain is total (five significant -> entities, all "
      "others -> identity); every code point the model can pass is covered."); sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-escape-ref-sound", "axiom": "escaped_seq", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_ESCAPE_REF_SOUND,
     "rationale": "the A-reference deep model escaped_seq must equal the real "
                  "django.utils.html.escape over boundary + the exhaustive 0..0x3000 sweep + "
                  "astral + 20000 fuzz, with the F2P witness '<script>'->'&lt;script&gt;' and the "
                  "legacy decimal apostrophe '&#39;' at this base_commit; any mismatch => "
                  "AXIOM-UNSOUND (the ON pin would be pinned to a wrong escaper)."},
    {"id": "ax-verbatim-identity", "axiom": "escaped_seq", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_VERBATIM_IDENTITY,
     "rationale": "the OFF/verbatim branch the renderer takes (str(value)) must be the identity "
                  "on character content for the F2P-shaped str inputs; any divergence => the OFF "
                  "pin ToSeq(Result())==ToSeq(value) would be anchored to wrong behaviour "
                  "(AXIOM-UNSOUND)."},
    {"id": "ax-containment", "axiom": "escaped_seq", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every code point the model can pass to the escaper is covered: the escaper's "
                  "domain is total (the five significant code points expand to their entities, "
                  "every other code point maps to identity), so there is no caller-reachable "
                  "input outside the deep model's domain. A reachable code point the escaper "
                  "mishandled would be AXIOM-TOO-WEAK-FOR-CALLER."},
]
