"""properties.py — PBT falsification manifest for django__django-11276.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    escape_codepoints(text: List[int]) -> List[int]      # = Django's html.escape

with the load-bearing contract

    Requires(Acc(list_pred(text), 1/2))                  # read-only input
    Requires(MustTerminate(2))                           # result is delivered
    Ensures (Acc(list_pred(text), 1/2))
    Ensures (Acc(list_pred(Result())))
    Ensures (ToSeq(Result()) == escaped_seq(ToSeq(text)))  # the WHOLE pin
    Ensures (entity_decode(entity(c)) == PSeq(c))  for c in {38,60,62,34,39}

What the spec actually defends, and the attacks it must survive:

  * The output pin `ToSeq(Result()) == escaped_seq(ToSeq(text))` is GROUNDED in
    the input: `escaped_seq` is a @Pure deep model (NOT @ContractOnly), fully
    unfolded by Viper, equal to real html.escape (G-AX). It is a function OF
    `text`, not an opaque answer-key marker. So there is no "echo the oracle"
    shortcut — you cannot `result = list(escaped_seq(...))` (no executable
    materialization of a @Pure PSeq into a list_pred list); the only way to make
    `ToSeq(result)` equal it is to build the list element-by-element, which IS
    the real per-code-point work. Case `echo-attempt-honest` confirms this: the
    cheapest impl that satisfies the pin still has to do the substitution.

  * The five round-trip clauses are CONSTANTS (independent of text/Result), so
    they do not constrain the impl; the impl-constraining clause is exactly the
    `escaped_seq` equality. Every uniqueness rival therefore targets that pin.

  * `text` is held read-only (1/2). The mandatory attack is FRAME MUTATION
    (`frame-mutate-text`): an impl that WRITES to `text` to try to satisfy the
    pin vacuously must fail for INSUFFICIENT PERMISSION.

  * The `MustTerminate` precondition makes the contract TOTAL: an impl that
    computes the right value but never returns (a frozen trailing loop) can no
    longer discharge the postcondition vacuously — the loop obligations leak
    and verification fails.

Authoring mechanics (preserved from the schema): every spec variant is built by
REGION-SURGERY (`_swap`) that edits ONLY inside `# impl-start`/`# impl-end`
(the nested invariants live there too), so `markers.same_spec` is guaranteed and
a rejection comes from the POSTCONDITION catching wrong behaviour (or the
permission system), never from a tampered spec. Each `expect:"reject"` rival
carries the refinement argument that its faithful real patch would NOT resolve.
Axiom cases run the REAL stdlib callee (`html.escape`/`html.unescape`) in Docker.
"""
from pathlib import Path

INSTANCE = "django__django-11276"
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

# The whole gold impl body (between the invariants-end marker and the return),
# used as a single replaceable block for structural rewrites.
_GOLD_BODY = """        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 38:
            result = [38, 97, 109, 112, 59] + result
        elif c == 60:
            result = [38, 108, 116, 59] + result
        elif c == 62:
            result = [38, 103, 116, 59] + result
        elif c == 34:
            result = [38, 113, 117, 111, 116, 59] + result
        elif c == 39:
            result = [38, 35, 120, 50, 55, 59] + result
        else:
            result = [c] + result
        i = i - 1"""

# single-branch emitted-byte literals (impl region)
_APOS = "result = [38, 35, 120, 50, 55, 59] + result"      # ' -> &#x27; (gold)
_QUOT = "result = [38, 113, 117, 111, 116, 59] + result"   # " -> &quot;


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (4a) Structurally-different but CORRECT: same backward fold, but the if/elif
# chain is REORDERED (39,34,62,60,38,else). Semantically identical, different
# source. If this fails to verify the postcondition is over-fit to one branch
# order => SPEC-TOO-STRONG.
_CHAIN_REORDERED_BODY = """        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 39:
            result = [38, 35, 120, 50, 55, 59] + result
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
_POS_REORDERED = _swap(_BASE, _GOLD_BODY, _CHAIN_REORDERED_BODY)

# (4b) Structurally-different but CORRECT: compute the per-code-point entity
# bytes into a LOCAL `seg` (a different control shape — branch assigns a local,
# a single prepend `result = seg + result`), still the backward fold. Confirms
# the spec admits a different code structure, not just a re-spelling of the
# gold branch. If it fails to verify => SPEC-TOO-STRONG (over-fit to the inline
# prepend form).
_CHAIN_SEG_BODY = """        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
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
            seg = [38, 35, 120, 50, 55, 59]
        result = seg + result
        i = i - 1"""
_POS_SEG = _swap(_BASE, _GOLD_BODY, _CHAIN_SEG_BODY)

# (2) ECHO-ATTEMPT, HONEST. The most direct "echo the @Pure oracle" attack would
# be `result = <materialize escaped_seq(ToSeq(text))>`. There is NO executable
# materialization of a @Pure PSeq into a list_pred list, so the cheapest impl
# that satisfies the GROUNDED pin still has to build the list per code point.
# This control is that cheapest honest impl: it asserts, right before the
# return, that the result it built EQUALS the spec oracle escaped_seq applied to
# the whole input. It is CORRECT (so expect="verify"); its purpose is to show
# there is no wrong echo that verifies — the oracle is grounded in `text`, not an
# opaque marker. (If you could echo a wrong answer and still verify, this would
# instead be a SPEC-TOO-WEAK reject case; here no such echo exists.)
_ECHO_RETURN = "    return result\n    # impl-end"
_ECHO_RETURN_NEW = (
    "    Assert(ToSeq(result) == escaped_seq(ToSeq(text)))\n"
    "    return result\n    # impl-end"
)
_ECHO_HONEST = _swap(_BASE, _ECHO_RETURN, _ECHO_RETURN_NEW)

# (5) ADMISSIBILITY. Construct an F2P-shaped, significant-char input
# [',",<,&,>,a] and ASSERT the value precondition is establishable for it: the
# fresh list literal carries full list_pred, from which the required read
# fraction `Acc(list_pred(.),1/2)` follows (no value restriction). (A literal
# self-call is no longer usable as the witness: the frozen spec now carries a
# termination obligation, and a recursive self-invocation cannot present a
# strictly smaller measure — by design, since a never-returning impl was
# exactly the vacuous-verification escape.) If the assert cannot discharge
# for this normal input => PRECOND-TOO-STRONG.
_ADMISS_HEAD = "    result = []  # type: List[int]\n    i = len(text)"
_ADMISS_HEAD_NEW = (
    "    probe = [39, 34, 60, 38, 62, 97]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    result = []  # type: List[int]\n"
    "    i = len(text)"
)
_ADMISS = _swap(_BASE, _ADMISS_HEAD, _ADMISS_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY, the #1 weakness class. The input is read-only
# (1/2). This rival WRITES `text[i-1] = 38` before reading it, then escapes the
# (now-overwritten) value. The intent is to satisfy the pin vacuously on a
# self-mutated input. Under Acc(list_pred(text),1/2) a store to `text` requires
# FULL permission, so it must fail for INSUFFICIENT PERMISSION (not for a wrong
# value). The gold invariants/asserts are kept verbatim around it, so the
# failure is attributable solely to the write. Rejection source: the permission
# system (the store is unverifiable under 1/2 read-only access).
_FRAME_BODY = _GOLD_BODY.replace(
    "        c = text[i - 1]\n",
    "        text[i - 1] = 38\n        c = text[i - 1]\n",
    1,
)
_RIVAL_FRAME = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)

# (3) PARTIAL-DOMAIN. This rival escapes EVERY significant code point correctly
# at EVERY position EXCEPT the apostrophe at the very FIRST element of the input
# (index 0): there it emits the legacy decimal `&#39;` instead of `&#x27;`. It
# pins only part of the input domain — every input whose first char is not "'",
# and every "'" that is not the leading char, is handled exactly like gold; the
# divergence is confined to inputs of the shape "'..." . A faithful real patch
# of this shape (escape() that special-cases position 0 of its argument) would
# still emit &#39; for inputs beginning with an apostrophe and so FAIL the F2P
# test_escape (which asserts ' -> &#x27; regardless of position). Rejection
# source: the postcondition `ToSeq(Result()) == escaped_seq(ToSeq(text))`, which
# pins the WHOLE sequence — including index 0 — so the i==1 (first-element) loop
# iteration cannot close the `ToSeq(result) == escaped_seq(...)` invariant when
# the leading code point is 39 but the emitted bytes are &#39;.
_PARTIAL_APOS_BODY = _GOLD_BODY.replace(
    "        elif c == 39:\n            result = [38, 35, 120, 50, 55, 59] + result\n",
    "        elif c == 39:\n"
    "            if i == 1:\n"
    "                result = [38, 35, 51, 57, 59] + result\n"
    "            else:\n"
    "                result = [38, 35, 120, 50, 55, 59] + result\n",
    1,
)
_RIVAL_PARTIAL_APOS = _swap(_BASE, _GOLD_BODY, _PARTIAL_APOS_BODY)

# (3b, supporting) The discriminating BUG itself: emit legacy `&#39;` for the
# apostrophe at EVERY position (the exact pre-gold Django behaviour the patch
# fixes; this is model_prepatch.py's apostrophe mapping). Its faithful real
# patch (escape() keeping `' -> &#39;`) is precisely the pre-patch code that
# FAILS the F2P test_escape, so verify⇒resolve would be broken if it verified.
# Rejection source: the `escaped_seq` postcondition (entity(39)==&#x27;).
_RIVAL_APOS_DEC = _swap(_BASE, _APOS, "result = [38, 35, 51, 57, 59] + result")

# (3c, supporting) Drops the double-quote escape (" passes through). A faithful
# patch doing this would emit unsafe attribute markup and fail escape's contract
# (test_escape asserts " -> &quot;). Rejection source: the `escaped_seq` pin
# (entity(34)==&quot;), caught at the iteration reading a 34.
_RIVAL_DROP_QUOT = _swap(_BASE, _QUOT, "result = [34] + result")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different (branch-reordered) but correct backward-fold "
                  "impl must verify; if not, the postcondition is over-fit to one branch "
                  "order => SPEC-TOO-STRONG."},
    {"id": "pos-control-seg-local", "kind": "soundness", "expect": "verify",
     "module": _POS_SEG,
     "rationale": "a correct impl with a DIFFERENT control shape (per-code-point bytes "
                  "into a local `seg`, single prepend) must verify; if not, the spec is "
                  "over-fit to the inline-prepend code form => SPEC-TOO-STRONG."},
    {"id": "echo-attempt-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the cheapest impl satisfying the GROUNDED pin still does the real "
                  "per-code-point work (no executable materialization of the @Pure oracle "
                  "escaped_seq into a list_pred list exists). Asserting result == "
                  "escaped_seq(ToSeq(text)) before return is redundant with the gold proof "
                  "and must verify. Demonstrates the spec is NOT echo-vulnerable: there is "
                  "no wrong oracle-echo that verifies (else this would be a reject case)."},
    {"id": "admiss-significant-input", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call on an F2P-shaped significant-char input [',\",<,&,>,a] must "
                  "establish the precondition Acc(list_pred(.),1/2); if not, "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-text", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: Django's escape() never "
                   "mutates its argument (a str, immutable). The rival exists only to test "
                   "whether the read-only (1/2) precondition can be subverted by writing to "
                   "`text`. There is no resolving patch that overwrites its input, so a "
                   "verifying rival here would be a pure verify⇏resolve artifact (vacuous "
                   "satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `text[i-1] = 38` writes through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (store needs full perm), not a "
                  "value mismatch; the gold invariants/asserts are kept verbatim. If it "
                  "verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "partial-domain-apos-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_APOS,
     "refinement": "escapes the apostrophe correctly (&#x27;) EVERYWHERE except when it is "
                   "the FIRST code point of the input, where it emits legacy &#39;. A "
                   "faithful real patch of this shape (escape() special-casing position 0) "
                   "would still emit &#39; for any input beginning with an apostrophe and so "
                   "FAIL the F2P test_escape (which pins ' -> &#x27; at every position) — "
                   "its patch would NOT resolve.",
     "rationale": "partial-domain: pins only the non-leading-apostrophe sub-domain. "
                  "Rejection source: the whole-sequence postcondition "
                  "ToSeq(Result()) == escaped_seq(ToSeq(text)) — index 0 is included, so "
                  "the first-element (i==1) iteration cannot close the invariant when "
                  "text[0]==39. If it verified => SPEC-TOO-WEAK (domain-incomplete)."},
    {"id": "rival-apos-decimal", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_APOS_DEC,
     "refinement": "emits legacy &#39; for the apostrophe at every position — the exact "
                   "pre-gold Django behaviour (model_prepatch.py); its faithful real patch "
                   "is the pre-patch escape() that FAILS the F2P test_escape (escape() must "
                   "emit &#x27;), so it would NOT resolve.",
     "rationale": "the discriminating bug. Rejection source: the `escaped_seq` pin "
                  "(entity(39)==&#x27;). If it verified => SPEC-TOO-WEAK (admits the bug)."},
    {"id": "rival-drop-quot", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_QUOT,
     "refinement": "lets the double-quote pass through unescaped; a real patch doing this "
                   "would emit unsafe attribute markup and FAIL test_escape (\" -> &quot;), "
                   "so it would NOT resolve.",
     "rationale": "supporting near-miss with a real refinement: double-quote not escaped. "
                  "Rejection source: the `escaped_seq` pin (entity(34)==&quot;)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real stdlib callee)
# ===========================================================================

# (1) axiom-soundness for entity_decode (== real html.unescape). Fuzz AROUND the
# six covered tokens — case variants, partial tokens, adjacent text — trying to
# make the real callee DISAGREE with the axiom on a token IN the axiom's domain.
# The axiom Ensures only constrains the six EXACT tokens; the fuzz that is NOT
# one of the six is used only to confirm the axiom never claims anything about
# it (so a disagreement there is NOT a defect — the axiom is silent). The
# soundness assertion is strictly on the six in-domain tokens.
_AX_DECODE_SOUND = r'''
import html, sys
# entity_decode axiom Ensures: the SIX relied-on tokens -> single code point.
DECODE = {"&amp;":38, "&lt;":60, "&gt;":62, "&quot;":34, "&#x27;":39, "&#39;":39}
bad = []
for tok, cp in DECODE.items():
    obs = [ord(c) for c in html.unescape(tok)]
    if obs != [cp]:
        bad.append((tok, obs, [cp]))
if bad:
    print("AXIOM-UNSOUND entity_decode on in-domain tokens:", bad); sys.exit(1)
# Adversarial fuzz AROUND the domain: case variants / partial / adjacent text.
# These are NOT in the axiom's domain (the axiom is silent on them) so we only
# verify the axiom does not over-claim: each is the equality token only when it
# is byte-identical to a covered token. Confirm the covered tokens stay exact
# even when embedded in surrounding text (the real urlize site passes substrings).
embeds = []
for tok, cp in DECODE.items():
    # the token surrounded by ordinary text must decode the token in place
    s = "x" + tok + "y"
    if html.unescape(s) != "x" + chr(cp) + "y":
        embeds.append((s, html.unescape(s)))
# near-miss tokens the axiom does NOT cover: assert they are genuinely different
# tokens (so widening the axiom to them would be a separate decision, not a
# silent unsoundness). e.g. &AMP; (uppercase) and &#X27; (uppercase X) and a
# truncated &amp (no ;) — html5 unescape may still decode some; that is fine,
# the axiom simply does not speak about them.
near = ["&AMP;", "&#X27;", "&amp", "&#x27", "&apos;", "&#0027;", "&#x0027;"]
print("entity_decode SOUND on all 6 in-domain tokens; embedded-in-text OK:",
      not embeds, "; near-miss probes (axiom silent, informational):",
      {t: html.unescape(t) for t in near})
if embeds:
    print("AXIOM-UNSOUND entity_decode embedded:", embeds); sys.exit(1)
sys.exit(0)
'''

# (2) axiom-soundness for the A-reference escaped_seq (== real html.escape).
# Boundary + HEAVY fuzz: astral chars, already-escaped input, all five
# significant chars, the EXHAUSTIVE BMP-ish sweep 0..0x3000, and astral code
# points (chr > 0xFFFF). Any mismatch => the deep model is unsound.
_AX_ESCAPE_REF_SOUND = r'''
import html, random, sys
ENTITY = {38:[38,97,109,112,59], 60:[38,108,116,59], 62:[38,103,116,59],
          34:[38,113,117,111,116,59], 39:[38,35,120,50,55,59]}
def escaped_seq(cps):
    out = []
    for c in cps: out.extend(ENTITY.get(c, [c]))
    return out
def ok(s):
    return [ord(c) for c in html.escape(s)] == escaped_seq([ord(c) for c in s])
sig = ['&','<','>','"',"'"]
ordn = list("aZ0 ;#x392 7quotlgmp") + ['e','é','•']
bad = []
# boundary: each alone, doubled, all together, reversed, already-escaped,
# astral, and several real-world strings
boundary = [""] + sig + [c+c for c in sig] + ["".join(sig), "".join(reversed(sig)),
    "a&b<c>d\"e'f", "x=1&amp;y=&lt;2&gt;", "&amp;","&#39;","&#x27;","&quot;",
    "Joe's Crab Shack", "<script>alert('xss')</script>", "Can't find my keys",
    "!$&'()*+,;=~:@,", "\U0001F600&'", "\U00010000<>\"", "ab\U0001F4A9'cd"]
for s in boundary:
    if not ok(s): bad.append(repr(s))
# EXHAUSTIVE single-code-point sweep 0..0x3000 (covers all five significant)
for cp in range(0, 0x3000):
    if not ok(chr(cp)): bad.append("U+%04X" % cp)
# astral single code points
for cp in [0xFFFF, 0x10000, 0x1F600, 0x1F4A9, 0x10FFFF]:
    if not ok(chr(cp)): bad.append("U+%05X" % cp)
# randomized fuzz over significant + ordinary + a few astral
rng = random.Random(11276)
alpha = sig + ordn + ['\U0001F600', '\U00010000']
for _ in range(20000):
    s = "".join(rng.choice(alpha) for _ in range(rng.randint(0,24)))
    if not ok(s): bad.append(repr(s))
if bad:
    print("A-REFERENCE-UNSOUND escaped_seq != html.escape on", bad[:8]); sys.exit(1)
print("escaped_seq == html.escape on", len(boundary),
      "boundary + 0x3000 exhaustive + astral + 20000 fuzz"); sys.exit(0)
'''

# (3) axiom-containment for entity_decode. Enumerate EXACTLY the tokens the model
# can pass to entity_decode: from the five round-trip postcondition clauses,
# entity(38),entity(60),entity(62),entity(34),entity(39) = the five EMITTED
# tokens (no &#39;, because the escaper emits the hex apostrophe). The axiom's
# covered domain is six tokens (those five + the legacy &#39;). Reachable must be
# a subset of covered; covering MORE (the legacy &#39;) is SOUND, not a defect
# (the float/int containment rule). Also confirm the real callee agrees on every
# reachable token (soundness tie-in).
_AX_CONTAINMENT = r'''
import html, sys
# entity(c) for the five significant code points = the tokens the escaper EMITS
# and that the round-trip postcondition feeds to entity_decode.
ENTITY = {38:"&amp;", 60:"&lt;", 62:"&gt;", 34:"&quot;", 39:"&#x27;"}
reachable = {ENTITY[c] for c in (38,60,62,34,39)}
# covered = the axiom's specified Ensures domain (six tokens).
covered = {"&amp;","&lt;","&gt;","&quot;","&#x27;","&#39;"}
missing = reachable - covered
if missing:
    print("AXIOM-TOO-WEAK-FOR-CALLER: caller reaches uncovered tokens", missing); sys.exit(1)
# soundness tie-in: real html.unescape agrees on every reachable token.
EXP = {38:[38],60:[60],62:[62],34:[34],39:[39]}
for c, tok in ENTITY.items():
    if [ord(ch) for ch in html.unescape(tok)] != EXP[c]:
        print("containment probe: real callee disagrees on", tok); sys.exit(1)
extra = covered - reachable
print("containment OK: reachable", sorted(reachable),
      "subset of covered; axiom over-covers (sound):", sorted(extra)); sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-decode-sound", "axiom": "entity_decode", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_DECODE_SOUND,
     "rationale": "real html.unescape must match the entity_decode Ensures on all six "
                  "in-domain tokens (incl. embedded-in-text); any mismatch => AXIOM-UNSOUND. "
                  "Near-miss tokens are probed informationally (axiom is silent on them)."},
    {"id": "ax-escape-ref-sound", "axiom": "escaped_seq", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_ESCAPE_REF_SOUND,
     "rationale": "the A-reference deep model escaped_seq must equal real html.escape over "
                  "boundary + the exhaustive 0..0x3000 sweep + astral + 20000 fuzz; any "
                  "mismatch => AXIOM-UNSOUND (deep model unsound)."},
    {"id": "ax-containment", "axiom": "entity_decode", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every token the model can pass to entity_decode (the five EMITTED "
                  "entities) lies in the axiom's specified domain; the axiom over-covers "
                  "(legacy &#39;) which is sound. A reachable uncovered token => "
                  "AXIOM-TOO-WEAK-FOR-CALLER."},
]
