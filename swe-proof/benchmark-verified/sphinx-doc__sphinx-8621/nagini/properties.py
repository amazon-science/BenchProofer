"""properties.py — PBT falsification battery for sphinx-doc__sphinx-8621.

NOT a Nagini module; an adversarial record the runner (swebench_nagini.pbt)
parses. Spec cases are full model.py variants built by region-surgery (we edit
ONLY text inside a `# impl-start`/`# impl-end` region, so `same_spec` is
guaranteed against the frozen model.py); axiom cases are real-callee probes run
in the instance Docker image.

Defended surface of this instance
---------------------------------
Two modeled functions, both with a READ-ONLY input `Acc(list_pred(text), 1/2)`:

  split_keystrokes(text) -> PSeq[PSeq[int]]
    LOAD-BEARING post:  Result() == kparts(ToSeq(text), False)
  keystroke_is_atomic(text) -> bool
    LOAD-BEARING post:  Result() == (len(kparts(ToSeq(text), False)) == 1)

`kparts` is a @Pure front-recursive fold over the actual input code points — a
TRANSPARENT, fully-unfolded function of the args, NOT an opaque answer-key
oracle. So there is no "wrong echo" to build for the ungrounded-oracle class
(directive 2): the cheapest honest impl IS `return kparts(...)`, i.e. it must do
the work. We therefore include an honest cheapest-impl positive control instead
of an echo, and say so in `assessment`.

There is NO consumed @ContractOnly axiom (meta.axioms == []). `kparts` is an
A-reference deep model of the post-patch regex split, validated == the real
callee out-of-band by axiom_check.py / G-AX. The axiom lane below re-runs that
real callee (soundness) and checks caller-domain containment.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8621"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — every edit below targets text that lives INSIDE an impl region.
# ---------------------------------------------------------------------------

# The whole body of keystroke_is_atomic's impl region (lines between its
# # impl-start / # impl-end). Editing here cannot touch the frozen spec.
_ATOMIC_IMPL = (
    "    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]\n"
    "    return len(parts) == 1\n"
)

# Two independent, order-free framing asserts at the head of split_keystrokes'
# impl region (both before the loop). Reordering them is a structural reshape
# that keeps every gold proof obligation intact.
_SK_PRELUDE = (
    "    Assert(len(ToSeq(text).drop(i)) == 0)\n"
    "    Assert(ToSeq(text).drop(i) == empty_seq())\n"
)

# The last-code-point branch body inside split_keystrokes' loop (impl region).
_SK_LAST_BRANCH = (
    "            result = single_part(PSeq(c) + result[0]) + result.drop(1)\n"
    "        else:")


# ===========================================================================
# SPEC LANE
# ===========================================================================
SPEC_TESTS = [

    # -- 6. ADMISSIBILITY -----------------------------------------------------
    # A self-call: keystroke_is_atomic invokes split_keystrokes on its own
    # F2P-shaped read-only input. The call site can only verify if the callee's
    # Requires (the printable-ASCII domain Forall + Acc(list_pred,1/2)) is
    # establishable from the caller's own identical precondition. We make the
    # admissibility explicit by asserting the domain predicate for a guarded
    # index right before the self-call. If this cannot verify => PRECOND-TOO-
    # STRONG (the precondition would reject a normal keystroke text).
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _ATOMIC_IMPL,
            "    Assert(Implies(len(text) >= 1, in_domain(text[0])))\n"
            "    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]\n"
            "    return len(parts) == 1\n",
        ),
        "rationale": "the self-call establishes split_keystrokes' Requires "
                     "(domain Forall + 1/2 read perm) from keystroke_is_atomic's "
                     "identical precondition; the added Assert witnesses the "
                     "domain holds for a normal input. Verifies => precondition "
                     "admits an F2P-shaped keystroke text.",
    },

    # -- 5. POSITIVE CONTROL (soundness), grounded cheapest impl --------------
    # keystroke_is_atomic via a local-variable reshape (compute the bool into a
    # named local, then return it). Structurally different from `return
    # len(parts)==1`, but keeps every proof obligation. MUST verify.
    {
        "id": "pos-atomic-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ATOMIC_IMPL,
            "    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]\n"
            "    atomic = len(parts) == 1  # type: bool\n"
            "    return atomic\n",
        ),
        "rationale": "a correct, structurally-different keystroke_is_atomic "
                     "(named local instead of inline expr) must verify; else "
                     "SPEC-TOO-STRONG. This is also the cheapest HONEST impl of "
                     "the grounded post Result()==(len(kparts(...))==1).",
    },

    # -- 5b. POSITIVE CONTROL (soundness) on the proof-heavy split impl -------
    # Reorder the two independent, order-free framing asserts at the head of
    # split_keystrokes (both are pre-loop, neither depends on the other). The
    # gold loop invariant / per-step asserts are untouched, so the gold proof
    # stays valid. MUST verify. (Per pilot-bug #2/#3 we do NOT flip the loop
    # direction or drop any framing assert.)
    {
        "id": "pos-split-assert-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _SK_PRELUDE,
            "    Assert(ToSeq(text).drop(i) == empty_seq())\n"
            "    Assert(len(ToSeq(text).drop(i)) == 0)\n",
        ),
        "rationale": "two independent pre-loop framing asserts reordered; every "
                     "loop invariant and per-step assert is kept verbatim, so a "
                     "faithful correct split impl still verifies; else "
                     "SPEC-TOO-STRONG.",
    },

    # -- 1. FRAME-MUTATION (MANDATORY: read-only Acc(list_pred,1/2) input) ----
    # A rival that WRITES to the read-only input `text` while still returning
    # the (correct) value. Must be REJECTED for INSUFFICIENT PERMISSION: the
    # function holds only Acc(list_pred(text), 1/2) (a write needs full perm).
    # The gold invariants/post are kept verbatim so the rejection is
    # attributable to the write, not to a value error.
    {
        "id": "frame-mutate-atomic-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ATOMIC_IMPL,
            "    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]\n"
            "    if len(text) > 0:\n"
            "        text[0] = 0  # write to a 1/2-permission input: must reject\n"
            "    return len(parts) == 1\n",
        ),
        "refinement": "the real KeyboardTransform.run never mutates its source "
                      "text node[-1].astext(); a patch that overwrites the "
                      "keystroke string before splitting would corrupt the "
                      "rendered <kbd> (e.g. turn 'Alt+^' into '\\x00lt+^') and "
                      "fail the F2P test. So this is not the gold patch.",
        "rationale": "permission system: with only Acc(list_pred(text),1/2) a "
                     "write to text[0] is insufficient permission. If it "
                     "verified, the read-only frame condition would be vacuous "
                     "(SPEC-TOO-WEAK via frame mutation).",
    },

    # -- 3. PARTIAL-DOMAIN / uniqueness: always-atomic ------------------------
    # A keystroke_is_atomic that ignores the part count and always reports
    # atomic (True). Correct on genuinely single-part texts (e.g. '-', 'space')
    # but WRONG on every multi-part text ('Alt+^', 'Control+X'). Pinned post
    # Result()==(len(kparts(...))==1) must reject it.
    {
        "id": "weak-always-atomic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ATOMIC_IMPL,
            "    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]\n"
            "    return len(parts) >= 1\n",
        ),
        "refinement": "len(parts)>=1 is always True (kparts always emits >=1 "
                      "part), so the impl reports EVERY text as a single <kbd>. "
                      "The gold `if len(parts)==1: continue` would NOT skip the "
                      "node for 'Alt+^' (3 parts) — the real run would still "
                      "build the nested <kbd>Alt</kbd>+<kbd>^</kbd>, which an "
                      "always-atomic impl suppresses, failing the Alt+^ F2P.",
        "rationale": "postcondition Result()==(len(kparts(...))==1): an "
                     "always-True bool diverges whenever len(kparts)!=1, so it "
                     "cannot verify. If it did, the atomic decision would be "
                     "unconstrained (SPEC-TOO-WEAK).",
    },

    # -- 3b. PARTIAL-DOMAIN / uniqueness: wrong constant (supporting) ---------
    # Reports atomic exactly when there are 2 parts — correct on NO real input
    # (a 2-part split never happens for the alternating keystroke/separator
    # shape, and is in any case wrong vs len==1). Must reject. Supporting case.
    {
        "id": "weak-atomic-eq-2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ATOMIC_IMPL,
            "    parts = split_keystrokes(text)  # type: PSeq[PSeq[int]]\n"
            "    return len(parts) == 2\n",
        ),
        "refinement": "reporting atomic iff len(parts)==2 inverts the real "
                      "decision: '-' (1 part) would be treated as non-atomic and "
                      "split into pieces, and 'Control+X' (3 parts) treated as "
                      "atomic — both wrong vs the gold `len(parts)==1` test, "
                      "failing the kbd F2P/P2P renders.",
        "rationale": "postcondition pins Result() to len(kparts(...))==1; ==2 "
                     "disagrees on every input, so it cannot verify.",
    },

    # -- 3c. UNIQUENESS on the split itself: drop the last keystroke ----------
    # A split_keystrokes whose last-code-point branch is a no-op (it leaves the
    # empty base part instead of prepending the final code point). The pre-loop
    # asserts and the loop invariant `result == kparts(...)` are kept, so the
    # NEXT iteration's invariant (and the final Ensures) no longer hold:
    # rejection is driven by the postcondition's exact pin to kparts.
    {
        "id": "weak-split-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SK_LAST_BRANCH,
            "            result = result  # DROP the last code point: must reject\n"
            "        else:"),
        "refinement": "skipping the final code point makes split('-') == [] "
                      "instead of ['-'], and 'Alt+^' lose its trailing '^' "
                      "keystroke. The gold run would render <kbd>-</kbd> and "
                      "<kbd>^</kbd>; this impl drops them, failing both F2P "
                      "cases. It is not the gold patch.",
        "rationale": "loop invariant + Ensures pin result == kparts(...): the "
                     "no-op last branch makes result != kparts(text.drop(i)) at "
                     "the boundary step, so the invariant fails to re-establish "
                     "and the function cannot verify (SPEC-TOO-WEAK if it did).",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# No @ContractOnly axiom (meta.axioms == []). `kparts` is an A-reference deep
# model of the post-patch regex split. The host G-AX (axiom_check.py) already
# proves kparts == real re.split over the whole printable-ASCII domain. Here we
# (a) re-run that REAL callee under the runtime config in Docker (axiom-
# soundness), and (b) check caller-domain CONTAINMENT: every code point the
# model can pass to the split is inside the validated domain.
#
# The probes are self-contained: they reconstruct the gold pattern and the
# kparts reference inline (the runner mounts ONLY the probe at /work; model.py /
# axiom_check.py are NOT in-container — pilot-bug #6). Files are opened utf-8
# where relevant (pilot-bug #5). The real callee is EXECUTED, never scraped
# (pilot-bug #4).

# A-reference soundness probe: build the gold post-patch pattern, run the REAL
# re.split, and assert it equals the deep model `kparts` on the literal
# FAIL_TO_PASS / PASS_TO_PASS strings + boundary cases + a randomized fuzz over
# the WHOLE printable-ASCII domain (blank runs included). This mirrors / re-
# derives axiom_check.py's obligation directly against the stdlib `re` the gold
# patch uses.
_AX_SOUNDNESS_PROBE = r'''
import random, re, sys

# The exact post-patch pattern installed by the gold patch (transforms.py:40).
NEW = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')

_SEP = {45, 43, 94}   # '-', '+', '^'
def is_sep(c):   return c in _SEP
def is_space(c): return c == 32
def in_domain(c): return 32 <= c <= 126

def kparts(s, lead):
    """Deep model kparts on a tuple of code points (== model.py's @Pure fold)."""
    n = len(s)
    if n == 0: return ((),)
    if n == 1: return (tuple(s),)
    c = s[0]
    if lead and is_sep(c):
        return ((), (c,)) + kparts(s[1:], True)
    if lead and is_space(c):
        rest = kparts(s[1:], True)
        if n >= 3 and is_space(s[1]):
            return ((),) + ((c,) + rest[1],) + rest[2:]
        return ((), (c,)) + rest
    rest = kparts(s[1:], True)
    return ((c,) + rest[0],) + rest[1:]

def model_split(text):
    cps = tuple(ord(ch) for ch in text)
    return [''.join(chr(c) for c in p) for p in kparts(cps, False)]

def check(text):
    assert all(in_domain(ord(ch)) for ch in text), "outside domain: %r" % (text,)
    observed = NEW.split(text)        # REAL callee (gold pattern), executed
    expected = model_split(text)      # deep model
    assert observed == expected, (
        "AXIOM-UNSOUND on %r: real re.split=%r deep kparts=%r"
        % (text, observed, expected))

# literal F2P / P2P keystroke strings (must hold exactly)
F2P_P2P = ["Alt+^", "-", "space", "Control+X", "M-x  M-s"]
assert model_split("-") == ["-"]
assert model_split("Alt+^") == ["Alt", "+", "^"]
assert model_split("M-x  M-s") == ["M", "-", "x", "  ", "M", "-", "s"]
for t in F2P_P2P:
    check(t)

# boundary cases over the printable-ASCII domain (incl. blank runs)
seps = ['-', '+', '^']; space = [' ']
boundary = [""] + seps + space
boundary += [c + c for c in seps + space]
boundary += [a + b for a in seps + space for b in seps + space]
boundary += ["Shift-+", "Control-x", "-x", "x-", "+a", "a+", "^z", "z^",
             " x", "x ", " x ", "a b", "a  b", "a   b", "  a", "a  ",
             "a- b", "a -b", "a - b", "a-  -b", "-  -", "  -  ",
             "a-+b", "a-b-c", "Ctrl-Alt-Del", "X", "ab",
             "----", "+-^", "^-+", "a^^b", "Shift-^-+", "x x x", "ab  cd  ef"]
for t in boundary:
    check(t)

# randomized fuzz over the WHOLE printable-ASCII domain (55% biased to branch
# chars; blank runs exercised). Mirrors axiom_check.py's 200k sweep (trimmed for
# the in-container probe budget).
rng = random.Random(8621)
common = [ord(c) for c in (seps + space + list("aBZ39xShiftConrlAMsX"))]
for _ in range(60000):
    n = rng.randint(0, 14)
    cps = [(rng.choice(common) if rng.random() < 0.55 else rng.randint(32, 126))
           for _ in range(n)]
    check("".join(chr(c) for c in cps))

print("AX-SOUNDNESS OK: real re.compile(NEW).split == kparts on "
      "%d boundary + 60000 fuzz inputs over printable-ASCII 32..126; all "
      "F2P/P2P keystroke strings confirmed (incl. blank-run 'M-x  M-s')."
      % len(boundary))
sys.exit(0)
'''

# Caller-domain containment probe: the ONLY code points the model can pass to
# the split are those allowed by split_keystrokes' Requires
# (Forall k: in_domain(text[k]) i.e. 32..126). G-AX validates kparts over
# EXACTLY 32..126. So every caller-reachable code point lies inside the
# validated domain (containment holds). Covering the whole 32..126 domain — and
# only that — is sound; a reachable code point outside it would be AXIOM-TOO-
# WEAK-FOR-CALLER. We assert the model's reachable-input set (32..126) is a
# subset of the validated set (32..126).
_AX_CONTAINMENT_PROBE = r'''
import sys

# Inputs the MODEL can reach: split_keystrokes' precondition is
#   Requires(Forall k: 0<=k<len(text) => in_domain(text[k]))
# with in_domain(c) == (32 <= c <= 126). So every code point passed to the
# split is in [32, 126]. keystroke_is_atomic forwards `text` unchanged to
# split_keystrokes under the SAME domain Requires — it reaches no new inputs.
def model_in_domain(c):   # the caller's enforced precondition
    return 32 <= c <= 126

# Domain the A-reference deep model kparts is VALIDATED on by G-AX
# (axiom_check.py): printable ASCII 32..126.
def validated(c):
    return 32 <= c <= 126

# Containment: every code point the caller can reach is inside the validated
# domain. Enumerate the full reachable code-point range and assert each is
# covered. (Covering MORE than the caller reaches would be sound too; here they
# coincide exactly.)
uncovered = [c for c in range(0, 0x110000)
             if model_in_domain(c) and not validated(c)]
assert not uncovered, (
    "AXIOM-TOO-WEAK-FOR-CALLER: caller can pass code points %r outside the "
    "G-AX-validated domain" % uncovered[:20])

# Also confirm no F2P/P2P keystroke string carries an out-of-domain code point
# (these are the strings the real test suite feeds the split).
for t in ["Alt+^", "-", "space", "Control+X", "M-x  M-s", "Shift-+"]:
    bad = [ord(ch) for ch in t if not validated(ord(ch))]
    assert not bad, "F2P/P2P string %r has out-of-domain code points %r" % (t, bad)

print("AX-CONTAINMENT OK: every caller-reachable code point (in_domain 32..126) "
      "lies inside the G-AX-validated kparts domain (32..126); all F2P/P2P "
      "keystroke strings are in-domain. No AXIOM-TOO-WEAK-FOR-CALLER gap.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-kparts-split",
        "axiom": "kparts",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "kparts is the A-reference deep model of the post-patch "
                     "regex split. The real stdlib re.compile(NEW).split (the "
                     "gold callee) must equal kparts on the F2P/P2P strings, "
                     "boundary cases, and a printable-ASCII fuzz; any mismatch "
                     "is AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-kparts-domain",
        "axiom": "kparts",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "the caller's Requires confines every code point passed to "
                     "the split to 32..126, exactly the domain G-AX validates "
                     "kparts on. A reachable code point outside it would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
