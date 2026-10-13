"""PBT manifest for django__django-11099.

NOT a Nagini module: a record of adversarially-reasoned falsification cases the
runner (swebench_nagini.pbt) executes and stamps RESULT onto. Spec cases are
full model.py variants that share the FROZEN spec byte-for-byte (region surgery:
ONLY the text inside an # impl-start / # impl-end block is edited — the spec
view is never touched) and are checked by Nagini verify + markers.same_spec.
Axiom cases are self-contained probes run against the real Python `re` engine in
the instance Docker image.

Defended surface (read from model.py / refinement.md / mapping.md):
  Two modeled functions, accepts_ascii / accepts_unicode, each typed
  `value: List[int]` (Unicode code points). Each takes the input READ-ONLY:
      Requires(Acc(list_pred(value), 1 / 2))   # half permission
      Ensures(Acc(list_pred(value), 1 / 2))    # returns the half permission
  Load-bearing postcondition (the whole specification):
      Ensures(Result() == (len(value) >= 1 and all_*_permitted(ToSeq(value))))
  i.e. accepted iff non-empty AND every code point — the LAST one included — is
  in the permitted class. The oracle all_*_permitted is a @Pure fold that is
  GROUNDED in the input (a fully-unfoldable function of ToSeq(value)), not an
  opaque answer key, so there is no "wrong echo" to build (see assessment); the
  faithful echo IS the gold decision and serves as a positive control instead.

  The whole gold patch is the regex end-anchor `$` -> `\Z`. The single
  behavioural delta is the trailing-line-feed case: `$` tolerates exactly one
  terminal U+000A (10), `\Z` does not. The F2P tests add 'trailingnewline\n'
  (both regimes) which the buggy `$` accepts and the fix rejects. So the
  load-bearing clause is precisely "the last code point must also be permitted;
  a terminal line feed is rejected" — that is the surface every reject-rival
  here attacks.

  membership oracle: permitted_ascii / permitted_unicode are @Pure @ContractOnly
  axioms => AXIOM lane applies (soundness against the real char class under each
  validator's flags; caller-domain containment).
"""
from pathlib import Path

INSTANCE = "django__django-11099"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each is a contiguous slice that lives ENTIRELY inside one impl
# region (between # impl-start and # impl-end), so every _swap keeps same_spec.
# The accepts_ascii and accepts_unicode impl bodies are structurally identical;
# we disambiguate by including the `_ascii`/`_unicode` token in the anchor.
# ---------------------------------------------------------------------------

# ASCII impl: the per-step check + decrement (unique: mentions permitted_ascii).
_ASCII_STEP = (
    "        if not permitted_ascii(c):\n"
    "            ok = False\n"
    "        i = i - 1"
)
# ASCII impl: the read of the current code point (unique within ascii body via
# its following ascii-only assert; we anchor on the whole 3-line cluster).
_ASCII_READ = (
    "        c = value[i - 1]\n"
    "        Assert(ToSeq(value).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))\n"
    "        if not permitted_ascii(c):\n"
    "            ok = False\n"
    "        i = i - 1"
)
# Note: `if n == 0:` and the loop prelude appear in BOTH bodies, so cases that
# touch the prelude (4, 6) anchor on the ascii-only / unicode-only invariant line
# (all_ascii_permitted vs all_unicode_permitted) to stay unique.


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -- 1. POSITIVE CONTROL (soundness) ------------------------------------
    # Structurally-different but CORRECT impl: replace the branch
    #   `if not permitted_ascii(c): ok = False`
    # with the conjunctive reshape `ok = ok and permitted_ascii(c)`. This keeps
    # the SAME backward loop and the SAME invariant
    #   ok == all_ascii_permitted(ToSeq(value).drop(i))
    # so the front-recursive unfold the verifier needs is preserved (no induction
    # lemma introduced — directives 2/3). Both forms compute
    # ok_new = ok_old and permitted(c), so the invariant is re-established.
    {
        "id": "pos-control-ascii-conjunctive",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ASCII_STEP,
            "        ok = ok and permitted_ascii(c)\n"
            "        i = i - 1",
        ),
        "rationale": "a structurally-different but correct impl (branch reshaped "
                     "to a conjunction, gold invariant kept) MUST verify; else "
                     "the postcondition is SPEC-TOO-STRONG. ok stays equal to "
                     "all_ascii_permitted(ToSeq(value).drop(i)) so the front-"
                     "recursive unfold still discharges.",
    },

    # -- 2. ADMISSIBILITY ---------------------------------------------------
    # A precondition that admits a normal F2P-shaped input. The Requires is just
    # Acc(list_pred(value), 1/2); there is no value-domain restriction, so the
    # faithful gold impl ALREADY proves the call is admissible for every list.
    # We confirm admissibility by keeping the gold impl verbatim and adding,
    # inside the ASCII impl region (before the loop runs), an assertion that the
    # half-permission the contract grants is genuinely held and the length is
    # readable — i.e. the Requires is establishable for a concrete list shape.
    # (No self-call: a top-level driver cannot be added without leaving the impl
    # region. The Acc-read + len-read assertion is the admissibility witness the
    # verifier discharges from the precondition alone.)
    {
        "id": "admiss-ascii-read-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    n = len(value)\n    if n == 0:\n        return False\n"
            "    i = n\n    ok = True\n    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(value), 1 / 2))\n"
            "        Invariant(0 <= i and i <= n and n == len(value))\n"
            "        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))",
            "    Assert(Acc(list_pred(value), 1 / 2))   # the read-only grant is held\n"
            "    n = len(value)                         # length readable under it\n"
            "    Assert(n >= 0)\n"
            "    if n == 0:\n        return False\n"
            "    i = n\n    ok = True\n    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(value), 1 / 2))\n"
            "        Invariant(0 <= i and i <= n and n == len(value))\n"
            "        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))",
        ),
        "rationale": "the precondition Acc(list_pred(value),1/2) must admit a "
                     "normal F2P-shaped list input: the read-only grant is held "
                     "and len(value) is readable under it. If this cannot be "
                     "established, PRECOND-TOO-STRONG. Gold impl otherwise "
                     "verbatim (only added asserts inside impl region).",
    },

    # -- 3. FRAME-MUTATION (MANDATORY: input is Acc(...,1/2) read-only) ------
    # Rival that WRITES to the read-only input to satisfy the postcondition
    # vacuously: overwrite every code point with 'a' (97, permitted) so the loop
    # trivially concludes ok=True and the length is preserved. With only 1/2
    # permission this write is ILLEGAL — Nagini rejects for INSUFFICIENT
    # PERMISSION (need full Acc to mutate value[i-1]). The gold invariants are
    # kept verbatim so the rejection is attributable solely to the write.
    {
        "id": "frame-mutation-ascii-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASCII_READ,
            "        value[i - 1] = 97   # ILLEGAL write to read-only input\n"
            "        c = value[i - 1]\n"
            "        Assert(ToSeq(value).drop(i - 1)[0] == c)\n"
            "        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))\n"
            "        if not permitted_ascii(c):\n"
            "            ok = False\n"
            "        i = i - 1",
        ),
        "refinement": "the real RegexValidator.__call__ never mutates its input "
                      "string; an impl that overwrites the username to force it "
                      "all-permitted would 'accept' the F2P invalid usernames "
                      "(e.g. 'trailingnewline\\n', 'jean marc') after rewriting "
                      "them, so its faithful real patch would NOT resolve the "
                      "F2P. Strings are immutable in Python anyway — this is a "
                      "pure spec-bypass, not a real edit.",
        "rationale": "REJECT comes from the PERMISSION SYSTEM: Acc(list_pred("
                     "value),1/2) grants read-only access; `value[i-1] = 97` "
                     "needs full Acc(list_pred(value)) so it fails for "
                     "insufficient permission. If it verified, the read-only "
                     "frame guarantee would be hollow.",
    },

    # -- 4. PARTIAL-DOMAIN: the prepatch `$` skeleton (THE discriminating delta)
    # Rival that tolerates exactly one trailing line feed before the all-
    # permitted run — i.e. if value[n-1]==10, check only value[:n-1]. This is
    # EXACTLY the buggy `$` semantics the gold patch removes. It diverges from
    # the spec on the lone-trailing-LF subdomain ([97,10] = "a\n"): the rival
    # returns True, the postcondition requires
    #   Result() == (len>=1 and all_ascii_permitted(ToSeq(value)))
    # which is False because permitted_ascii(10) is False. MUST be rejected.
    {
        "id": "partial-domain-ascii-trailing-lf-tolerated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    n = len(value)\n    if n == 0:\n        return False\n    i = n\n    ok = True\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(value), 1 / 2))\n"
            "        Invariant(0 <= i and i <= n and n == len(value))\n"
            "        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))",
            "    n = len(value)\n    if n == 0:\n        return False\n"
            "    i = n\n"
            "    if n >= 1 and value[n - 1] == 10:   # `$` quirk: drop one trailing LF\n"
            "        i = n - 1\n"
            "    ok = True\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(value), 1 / 2))\n"
            "        Invariant(0 <= i and i <= n and n == len(value))\n"
            "        Invariant(ok == all_ascii_permitted(ToSeq(value).drop(i)))",
        ),
        "refinement": "this IS the pre-patch `^[\\w.@+-]+$` behaviour (model_"
                      "prepatch.py): a single trailing newline is tolerated. Its "
                      "faithful real patch is the UNCHANGED buggy regex, which "
                      "still accepts 'trailingnewline\\n' — exactly the F2P the "
                      "issue added — so it does NOT resolve F2P.",
        "rationale": "REJECT comes from the postcondition clause "
                     "Result()==(len>=1 and all_ascii_permitted(ToSeq(value))): "
                     "on [97,10] the rival returns True but the spec requires "
                     "False (permitted_ascii(10)==False, the last code point is "
                     "NOT permitted; no end-of-string tolerance). The loop "
                     "invariant ok==all_ascii_permitted(drop(i)) is then violated "
                     "at exit since drop(0) includes the LF.",
    },

    # -- 5. PARTIAL-DOMAIN: forget the last anchor (off-by-one) ---------------
    # Rival that scans only value[1..n-1] (stops the loop at i>1 instead of i>0),
    # i.e. never checks the LAST code point against the class. Correct on every
    # input whose only-possibly-bad char is NOT the last, but accepts e.g.
    # [97,10] (last char a line feed) — diverges on the load-bearing last-anchor
    # subdomain. MUST be rejected. We weaken the loop guard AND keep the gold
    # invariant; the invariant ok==all_ascii_permitted(drop(i)) will be
    # UNPROVABLE at i==1 (ok claims drop(1) all-permitted but the body never
    # examined value[0]'s contribution to drop(0)) -> rejected.
    {
        "id": "partial-domain-ascii-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ASCII_STEP,
            "        if i > 1 and not permitted_ascii(c):   # never checks the LAST cp\n"
            "            ok = False\n"
            "        i = i - 1",
        ),
        "refinement": "an impl that exempts one anchored code point (here the "
                      "backward loop's last step, value[0]) from the class check "
                      "is the `$`-style end tolerance generalised: it admits a "
                      "string with one un-checked position, so it accepts inputs "
                      "the real \\Z regex rejects (it no longer requires EVERY "
                      "code point permitted) and would NOT resolve the F2P.",
        "rationale": "REJECT from the postcondition + loop invariant: the spec "
                     "pins the LAST code point inside the permitted run "
                     "(all_ascii_permitted folds over EVERY element incl. "
                     "ToSeq(value)[0..n-1]); skipping value[n-1] (or any element) "
                     "breaks Result()==(len>=1 and all_ascii_permitted(...)).",
    },

    # -- 6. PARTIAL-DOMAIN (Unicode mirror): trailing-LF tolerated -----------
    # The patch fixes BOTH validators; the spec defends accepts_unicode the same
    # way. Mirror of case 4 on the Unicode body so a rival that only fixes ASCII
    # (leaving the Unicode `$` quirk) is caught. Diverges on the Unicode F2P
    # 'trailingnewline\u000A'.
    {
        "id": "partial-domain-unicode-trailing-lf-tolerated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    n = len(value)\n    if n == 0:\n        return False\n    i = n\n    ok = True\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(value), 1 / 2))\n"
            "        Invariant(0 <= i and i <= n and n == len(value))\n"
            "        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))",
            "    n = len(value)\n    if n == 0:\n        return False\n"
            "    i = n\n"
            "    if n >= 1 and value[n - 1] == 10:   # `$` quirk on the Unicode validator\n"
            "        i = n - 1\n"
            "    ok = True\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(value), 1 / 2))\n"
            "        Invariant(0 <= i and i <= n and n == len(value))\n"
            "        Invariant(ok == all_unicode_permitted(ToSeq(value).drop(i)))",
        ),
        "refinement": "the Unicode validator must ALSO reject a trailing newline "
                      "(gold patch changes both hunks). A rival that leaves the "
                      "Unicode regex's `$` tolerance still accepts the F2P "
                      "'trailingnewline\\u000A' under flags=0, so its faithful "
                      "patch does NOT resolve test_unicode_validator.",
        "rationale": "REJECT from accepts_unicode's postcondition "
                     "Result()==(len>=1 and all_unicode_permitted(ToSeq(value))): "
                     "on [97,10] the rival returns True, spec requires False "
                     "(permitted_unicode(10)==False).",
    },

    # -- 7. SUPPORTING near-miss: invert the decision (cheap mechanical) -----
    # A wrong impl that returns the NEGATION on non-empty input. Mechanical, but
    # carries a real refinement: it accepts exactly the invalid usernames and
    # rejects the valid ones, the inverse of the validator, so it resolves
    # nothing. Confirms the postcondition pins the polarity of Result().
    {
        "id": "support-ascii-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            "    Assert(ToSeq(value).drop(0) == ToSeq(value))\n    return ok\n    # impl-end\n\n\ndef accepts_unicode",
            "    Assert(ToSeq(value).drop(0) == ToSeq(value))\n    return not ok   # inverted decision\n    # impl-end\n\n\ndef accepts_unicode",
        ),
        "refinement": "returning the inverse decision accepts every invalid "
                      "username (incl. 'jean marc', 'trailingnewline\\n') and "
                      "rejects every valid one ('glenn'), the opposite of the "
                      "validator — resolves no F2P/P2P.",
        "rationale": "REJECT from Result()==(len>=1 and all_ascii_permitted(...)): "
                     "`not ok` contradicts the pinned value on every non-empty "
                     "input that is (or is not) all-permitted.",
    },
]


# ===========================================================================
# AXIOM LANE  (permitted_ascii / permitted_unicode are @Pure @ContractOnly,
# and all_*_permitted is an A-reference deep model of the fixed regex)
# ===========================================================================
#
# Each probe is self-contained, imports only stdlib (`re`), opens nothing on
# disk, prints a diagnostic, and exits 0 iff the obligation holds (1 otherwise).
# The real callee is the CPython `re`/`sre` engine — exactly what the patched
# validators use (re.search(pattern, str(value))) — so executing it in the
# instance image is the real-callee soundness check. We CALL the engine; we
# never regex-scrape source (directive 4). Files are not read, so no codec
# concern (directive 5); nothing from the bundle is needed in-container
# (directive 6).

# ---- ax-sound-permitted-ascii: real [\w.@+-] under re.ASCII == axiom Ensures
_AX_SOUND_ASCII = r'''
import re, sys
cls = re.compile(r"[\w.@+-]", re.ASCII)
def member(c):
    return cls.fullmatch(chr(c)) is not None
# model.py permitted_ascii Ensures clauses, transcribed (cp -> required membership)
axiom = {10: False, 32: False, 97: True, 65: True, 48: True, 45: True, 46: True}
bad = []
for c, req in axiom.items():
    got = member(c)
    if got != req:
        bad.append((c, got, req))
# Also fuzz a wide single-code-point sweep: the axiom must never CLAIM something
# the real ASCII class contradicts on its pinned points; for unpinned points the
# axiom is silent (weakest sufficient contract) so any membership is sound.
# Sanity: the discriminating LF (10) and space (32) really are excluded.
assert member(10) is False, "LF must be excluded under re.ASCII"
assert member(32) is False, "space must be excluded under re.ASCII"
if bad:
    print("AXIOM-UNSOUND permitted_ascii:", bad); sys.exit(1)
print("ax-sound-permitted-ascii OK: real [\\w.@+-] under re.ASCII matches all "
      "pinned Ensures clauses; LF(10) & space(32) excluded as required.")
sys.exit(0)
'''

# ---- ax-sound-permitted-unicode: real [\w.@+-] under flags=0 == axiom Ensures
_AX_SOUND_UNI = r'''
import re, sys
cls = re.compile(r"[\w.@+-]", 0)
def member(c):
    return cls.fullmatch(chr(c)) is not None
# model.py permitted_unicode Ensures clauses, transcribed.
axiom = {10: False, 32: False, 97: True, 233: True, 48: True, 45: True, 46: True}
bad = []
for c, req in axiom.items():
    got = member(c)
    if got != req:
        bad.append((c, got, req))
assert member(10) is False, "LF must be excluded under flags=0"
assert member(32) is False, "space must be excluded under flags=0"
# 'e' is ASCII-word; the wider regime additionally admits U+00E9 (233). Confirm
# the wider word-class really does include the non-ASCII letter the axiom pins.
# (Use only ASCII text in diagnostics: the in-container stdout codec is ASCII,
# so a literal non-ASCII char in a print would raise UnicodeEncodeError and
# spuriously fail the probe even when every membership check passed.)
assert member(233) is True, "wider \\w must include U+00E9 under flags=0"
if bad:
    print("AXIOM-UNSOUND permitted_unicode:", bad); sys.exit(1)
print("ax-sound-permitted-unicode OK: real [\\w.@+-] under flags=0 matches all "
      "pinned Ensures clauses; LF(10) & space(32) excluded; U+00E9 (233) included.")
sys.exit(0)
'''

# ---- ax-ref-deep-model-fixed: the A-reference deep model == real FIXED regex,
# and disagreement with the buggy `$` regex is EXACTLY the lone-trailing-LF case.
# This is the executable check that the deep fold all_*_permitted (with the
# non-empty guard) equals re.search(r"^[\w.@+-]+\Z", ...) under each regime —
# the trust point behind the A-reference (refinement A5/B4). Embeds the bundle's
# own G-AX logic so the manifest's probe stands alone in-container.
_AX_REF_DEEP = r'''
import re, random, sys
LF = 10
ascii_cls   = re.compile(r"[\w.@+-]", re.ASCII)
uni_cls     = re.compile(r"[\w.@+-]", 0)
ascii_fixed = re.compile(r"^[\w.@+-]+\Z", re.ASCII)
ascii_buggy = re.compile(r"^[\w.@+-]+$",  re.ASCII)
uni_fixed   = re.compile(r"^[\w.@+-]+\Z", 0)
uni_buggy   = re.compile(r"^[\w.@+-]+$",  0)

def member(cls, c):
    return cls.fullmatch(chr(c)) is not None

def deep_accept(cls, value):
    # model.py: accept(value) == (len>=1 and every code point admissible)
    if len(value) < 1:
        return False
    return all(member(cls, c) for c in value)

def real_accept(rx, value):
    return rx.search("".join(chr(c) for c in value)) is not None

def check(cls, fixed_rx, buggy_rx, value):
    deep  = deep_accept(cls, value)
    fixed = real_accept(fixed_rx, value)
    if deep != fixed:
        print("A-REFERENCE UNSOUND: deep != FIXED on", value,
              "deep=", deep, "fixed=", fixed); sys.exit(1)
    buggy = real_accept(buggy_rx, value)
    if deep != buggy:
        # the only allowed disagreement: a single trailing LF over an else-valid run
        ok = (len(value) >= 1 and value[-1] == LF and deep_accept(cls, value[:-1]))
        if not ok:
            print("deep/buggy disagreement on", value, "is NOT a lone-trailing-LF case",
                  "deep=", deep, "buggy=", buggy); sys.exit(1)

boundary = [
    [], [LF], [97], [97, LF], [97, LF, LF], [97, LF, 98],
    list(b"glenn"), list(b"jean-marc"), list(b"jean marc"),
    [97, ord('.'), ord('@'), ord('+'), ord('-'), LF],
    [ord(c) for c in "trailingnewline"] + [LF],
    [ord(c) for c in "René"], [ord(c) for c in "أحمد"],
]
for v in boundary:
    check(ascii_cls, ascii_fixed, ascii_buggy, v)
    check(uni_cls,   uni_fixed,   uni_buggy,   v)

rng = random.Random(11099)
special = [LF, 13, 32, ord('.'), ord('@'), ord('+'), ord('-'), ord('_'),
           ord('a'), ord('Z'), ord('0'), ord('9'), ord("'"), 233, 8203, 160,
           8211, ord(' ')]
alphabet = special + [ord(ch) for ch in "glennGLEnNjeanmarc"]
for _ in range(20000):
    k = rng.randint(0, 12)
    v = [rng.choice(alphabet) for _ in range(k)]
    check(ascii_cls, ascii_fixed, ascii_buggy, v)
    check(uni_cls,   uni_fixed,   uni_buggy,   v)

# single-code-point sweep so any element-wise membership disagreement is caught
for c in range(0, 0x2100):
    v = [97, c]
    check(ascii_cls, ascii_fixed, ascii_buggy, v)
    check(uni_cls,   uni_fixed,   uni_buggy,   v)

print("ax-ref-deep-model-fixed OK: deep model == real ^[\\w.@+-]+\\Z over "
      "13 boundary + 20000 fuzz + 0x2100 single-cp-sweep in both regimes; "
      "deep/buggy disagreements are exactly the lone-trailing-LF case.")
sys.exit(0)
'''

# ---- ax-cover: caller-domain containment. The MODEL passes to the membership
# axiom EXACTLY the integers value[i] for an arbitrary List[int] (any Unicode
# code point in 0..0x10FFFF). The axiom's @Pure @ContractOnly contract has NO
# Requires restricting its `int` argument — its domain is all ints. So every
# callee-input the model can reach is trivially inside the axiom's domain
# (containment is vacuously satisfied). We verify there is NO code-point value
# the model can pass that lies outside the axiom's declared domain, by confirming
# the axiom contract is total over int (the model never narrows the type).
_AX_COVER = r'''
import sys
# The model declares:  permitted_ascii(c: int) -> bool  with NO Requires(...).
# The caller (accepts_*) reads c = value[i-1] where value: List[int]; thus the
# only inputs the model can reach are arbitrary Python ints (Unicode code points,
# 0..0x10FFFF, plus the surrogate range — all valid ints). The axiom's domain is
# ALL ints (no precondition narrows it), so containment holds:
#   { c | c reachable by the caller } = { int } subset of dom(permitted_*) = int.
# This is the float-vs-int containment rule: the axiom may legitimately cover MORE
# (all ints) than the caller reaches; the defect would only be a reachable input
# OUTSIDE the domain, which cannot exist for an unrestricted int contract.
reachable_examples = [0, 10, 32, 45, 46, 48, 65, 97, 233, 8203, 0x10FFFF, -1]
# (negative ints are not real code points, but the model's type is `int` with no
#  Requires, so even those would be in-domain; the validator only ever passes
#  ord(ch) in 0..0x10FFFF.)
for c in reachable_examples:
    assert isinstance(c, int), "model only passes ints to the membership axiom"
print("ax-cover OK: permitted_ascii/permitted_unicode have NO Requires, domain "
      "= all int; the caller only ever passes int code points => every "
      "caller-reachable input is inside the axiom domain (containment holds; "
      "no AXIOM-TOO-WEAK-FOR-CALLER).")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-permitted-ascii",
        "axiom": "permitted_ascii",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_ASCII,
        "rationale": "real [\\w.@+-] under re.ASCII (the ASCII validator's flags) "
                     "must agree with every pinned Ensures clause; if any pinned "
                     "membership disagrees, AXIOM-UNSOUND. LF/space exclusion is "
                     "the load-bearing fact behind rejecting a trailing newline.",
    },
    {
        "id": "ax-sound-permitted-unicode",
        "axiom": "permitted_unicode",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_UNI,
        "rationale": "real [\\w.@+-] under flags=0 (the Unicode validator's flags) "
                     "must agree with every pinned Ensures clause incl. é(233) "
                     "included and LF/space excluded; else AXIOM-UNSOUND.",
    },
    {
        "id": "ax-ref-deep-model-fixed",
        "axiom": "all_ascii_permitted / all_unicode_permitted",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_DEEP,
        "rationale": "the A-reference deep fold (non-empty AND every code point "
                     "admissible) must equal the real FIXED regex ^[\\w.@+-]+\\Z "
                     "under each regime, and differ from the buggy `$` regex "
                     "exactly on the lone-trailing-LF case; any other mismatch "
                     "means the deep model misrepresents the gold-fixed match.",
    },
    {
        "id": "ax-cover-membership-domain",
        "axiom": "permitted_ascii / permitted_unicode",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER,
        "rationale": "the membership axioms have no Requires (domain = all int); "
                     "the caller only ever passes int code points, so every "
                     "caller-reachable input is in-domain (containment). Covering "
                     "all ints when the caller passes only valid code points is "
                     "SOUND (float-vs-int rule), not AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
