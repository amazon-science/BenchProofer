"""PBT falsification battery for scikit-learn__scikit-learn-15100.

NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec exactly
(region-surgery: only the text strictly between `# impl-start` and `# impl-end`
is edited; the spec_view elides that region, so same_spec is guaranteed) with a
swapped impl. AXIOM_TESTS entries are self-contained probes run in the instance
Docker image against the REAL stdlib callees.

Defended surface (see model.py / refinement.md / mapping.md):

  strip_marks(s: List[int]) -> List[int]
    Requires(Acc(list_pred(s), 1/2))                       # s is READ-ONLY
    Ensures(Acc(list_pred(s), 1/2))                        # returns the borrow
    Ensures(Acc(list_pred(Result())))                      # full perm on output
    Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))   # LOAD-BEARING

The load-bearing postcondition pins the output to `strip_combining(nfkd(s))`,
i.e. (1) canonically decompose, then (2) drop every combining mark. Both
`nfkd` and `strip_combining` are GROUNDED @Pure functions of the argument `s`
(fully unfolded), NOT an opaque answer-key oracle -- so there is no "wrong echo"
to build (see assessment); instead the uniqueness lane uses partial-domain and
control-flow rivals. `s` carries only Acc(.,1/2), so the frame-mutation probe
is mandatory.

The F2P discriminator (test_strip_accents, the gold test_patch) is the
ALREADY-DECOMPOSED-with-combining-marks input, e.g. "ö" -> "o",
"̀́̂̃" -> "", "ȫ" -> "o". The pre-patch guard
`if normalize(NFKD,s)==s: return s` returned such inputs untouched; the gold
patch's strict-ASCII guard does not fire on them, so they fall through to the
mark-dropping general path. Every reject rival's refinement is grounded in one
of these F2P inputs.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-15100"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The verbatim gold impl-region BODY (the text strictly between the
# `# impl-start` and `# impl-end` markers). Everything we swap lives here, so
# the frozen spec (axioms/pure/pre/post) is never touched and same_spec holds.
# ---------------------------------------------------------------------------
_GOLD_BODY = '''\
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        # Already-final-form input: canonically stable and mark-free, so its
        # decomposition carries no combining marks and equals the input -- the
        # fast path returns the input string unchanged (modelled as its
        # code-point copy, str being immutable: returning s == returning a
        # copy of s).
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            # invariants-start
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            # invariants-end
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
        # invariants-end
        c = normalized[i - 1]
        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
        if not is_combining(c):
            result = [c] + result
        i = i - 1
    return result'''

# Sanity: the gold body must appear verbatim & uniquely in the frozen model.
assert _BASE.count(_GOLD_BODY) == 1, "gold impl body drifted from model.py"


def _with_body(new_body):
    """Return a full model.py whose impl-region body is `new_body`, every other
    region (incl. the spec) byte-identical to the frozen model."""
    return _swap(_BASE, _GOLD_BODY, new_body)


# ===========================================================================
# SPEC LANE
# ===========================================================================

# --- 1. FRAME-MUTATION (mandatory; s is Acc(.,1/2) read-only) ---------------
# Attack: an impl that WRITES to the read-only input `s` to "produce" the
# answer in place. The store `s[0] = s[0]` requires FULL permission on
# list_pred(s); the precondition grants only Acc(.,1/2), so Nagini must reject
# for INSUFFICIENT PERMISSION. The rest of the body is the verbatim gold body
# so the rejection is attributable solely to the write (not to a proof gap).
_FRAME_MUT_BODY = '''\
    s[0] = s[0]
''' + _GOLD_BODY

# --- 2. FRAME-MUTATION via append -------------------------------------------
# Supporting variant: append to `s` (also needs full permission). Distinct
# permission-violation surface (length-changing mutation) from the store above.
_FRAME_APPEND_BODY = '''\
    s.append(0)
''' + _GOLD_BODY

# --- 3. PARTIAL-DOMAIN: drop the combining-mark filter (general path) --------
# Attack: keep the ASCII fast path verbatim, but on the general path KEEP every
# code point (never test is_combining). Correct on pure-ASCII (handled by fast
# path) and on inputs with NO combining marks, but WRONG on every input that
# carries a combining mark -- precisely the F2P discriminator. Postcondition
# ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))) is violated because the
# rival returns nfkd(s) (combining marks intact) instead of stripping them.
_NO_FILTER_BODY = '''\
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        c = normalized[i - 1]
        result = [c] + result
        i = i - 1
    return result'''

# --- 4. PARTIAL-DOMAIN: inverted filter (keep marks, drop bases) -------------
# Attack: filter with the WRONG predicate -- keep combining marks, drop
# non-combining code points. Returns the marks-only subsequence; correct only
# on the empty/all-combining edge, wrong on every real word. Violates the
# postcondition (strip_combining KEEPS non-combining, DROPS combining).
_INVERTED_FILTER_BODY = '''\
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        c = normalized[i - 1]
        if is_combining(c):
            result = [c] + result
        i = i - 1
    return result'''

# --- 5. PARTIAL-DOMAIN: skip-the-decomposition (prepatch-shaped) -------------
# Attack: skip decomposition on the general path and return the RAW input
# code points filtered by is_combining -- i.e. strip_combining(s) instead of
# strip_combining(nfkd(s)). Correct whenever nfkd(s)==s (already decomposed),
# but WRONG on a PRECOMPOSED accented input (e.g. chr(241) n-tilde) where
# nfkd(s) != s: the precomposed glyph is never decomposed, so the accent is
# never separated and dropped. Violates ToSeq(Result()) == strip_combining(
# nfkd(ToSeq(s))) because the rival omits the nfkd step.
_SKIP_DECOMPOSE_BODY = '''\
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    result = []  # type: List[int]
    i = len(s)
    while i > 0:
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(s))
        c = s[i - 1]
        if not is_combining(c):
            result = [c] + result
        i = i - 1
    return result'''

# --- 6. CONTROL-FLOW / FAST-PATH SCOPE: fast path on the wrong condition -----
# Attack: take the unchanged-return fast path UNCONDITIONALLY (ignore the
# guard) -- return a copy of `s`. This is exactly the prepatch family of bug
# (return s untouched) generalised: correct only when s is already mark-free
# in decomposed form, WRONG on every accented/combining input. Violates the
# postcondition on the F2P discriminator "ö" (returns it untouched
# instead of "o"). Distinct from the prepatch (which guards on nfkd(s)==s);
# here there is no guard at all, exercising the fast-path materialisation as a
# standalone wrong impl.
_ALWAYS_RETURN_INPUT_BODY = '''\
    out = []  # type: List[int]
    j = 0
    while j < len(s):
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(s))
        Invariant(ToSeq(out) == ToSeq(s).take(j))
        Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
        out = out + [s[j]]
        j = j + 1
    Assert(ToSeq(s).take(len(s)) == ToSeq(s))
    return out'''

# --- 7. POSITIVE CONTROL (soundness): structurally-different CORRECT impl ----
# A correct impl that differs structurally from the gold: the ASCII fast path
# is REORDERED so the early `return out` is replaced by control flow that falls
# through to a single tail (no early return inside the guard); the general path
# is kept verbatim (backward fold = strip_combining's front-recursion, the only
# shape the verifier auto-discharges -- a forward-append would need an
# f(a+b)=f(a)+f(b) lemma, AVOID per directive 3). All gold framing
# Asserts/Invariants are PRESERVED so no proof obligation is dropped. The only
# change is local: a single `result` local (declared ONCE at the top, since
# Nagini hoists locals to function scope and rejects a second `# type:`
# annotation on the same name) is shared by both paths; the fast-path branch
# writes into it and the function returns once at the end, instead of the gold's
# two separately-named (`out`/`result`) returns.
_POS_CONTROL_BODY = '''\
    result = []  # type: List[int]
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        # Same fast-path proof, but build into the single `result` local and
        # fall through to the single tail return (structural reorder; identical
        # obligations kept).
        Assert(all_ascii(ToSeq(s)))
        j = 0
        while j < len(s):
            # invariants-start
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(result) == ToSeq(s).take(j))
            # invariants-end
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            result = result + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return result
    normalized = decompose(s)
    i = len(normalized)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
        # invariants-end
        c = normalized[i - 1]
        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
        # Reordered branch test (== vs not): keep iff classifier is False.
        if is_combining(c):
            i = i - 1
            continue
        result = [c] + result
        i = i - 1
    return result'''

# --- 8. ADMISSIBILITY: precondition admits a normal F2P-shaped input ---------
# A self-call caller proving the Requires (Acc(.,1/2)) is establishable for a
# concrete F2P-shaped input. We build a fresh list `arg` (full permission),
# then call strip_marks(arg) -- the call needs only Acc(.,1/2), which we hold,
# and the post returns the borrow so we keep using `arg`. If the precondition
# were too strong, this legitimate call would fail to verify. After the
# admissibility self-call we run the verbatim gold body so the function still
# satisfies its OWN postcondition for the parameter `s` (the self-call is on a
# DIFFERENT local `arg`, so it cannot satisfy the post about `s`).
_ADMISS_BODY = '''\
    arg = []  # type: List[int]
    arg.append(111)   # 'o'  (a normal F2P code point, < 128)
    arg.append(0x308)  # combining diaeresis -> the F2P discriminator "o\\u0308"
    Assert(len(arg) == 2)
    res = strip_marks(arg)
    Assert(Acc(list_pred(arg), 1 / 2))   # the borrow came back
    Assert(ToSeq(res) == strip_combining(nfkd(ToSeq(arg))))  # the post holds
''' + _GOLD_BODY


SPEC_TESTS = [
    {
        "id": "frame-mut-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_body(_FRAME_MUT_BODY),
        "refinement": (
            "A real patch that writes into the input string to compute the "
            "answer in place cannot exist for `str` (immutable) and would not "
            "match strip_accents_unicode's contract of returning a fresh value "
            "while leaving the caller's string untouched; semantically it does "
            "not produce strip_combining(nfkd(s)) for the F2P input 'o\\u0308'."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM: `s` is Acc(list_pred(s),"
            " 1/2) (read-only); the store `s[0] = s[0]` requires full permission. "
            "Must fail for insufficient permission, not a proof gap."
        ),
    },
    {
        "id": "frame-mut-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_body(_FRAME_APPEND_BODY),
        "refinement": (
            "Appending to the input is a length-changing mutation of a borrowed "
            "read-only argument; no faithful str-based patch mutates its input, "
            "and it does not compute strip_combining(nfkd(s)) on 'o\\u0308'."
        ),
        "rationale": (
            "PERMISSION SYSTEM: s.append(...) needs full permission on "
            "list_pred(s); only Acc(.,1/2) is granted. Insufficient permission."
        ),
    },
    {
        "id": "partial-no-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_body(_NO_FILTER_BODY),
        "refinement": (
            "The faithful real patch -- decompose then keep EVERY char without "
            "the `if not combining(c)` test -- returns NFKD(s) with combining "
            "marks intact. On F2P input 'o\\u0308' it yields 'o\\u0308' (and on "
            "'\\u0300\\u0301\\u0302\\u0303' the four marks) instead of 'o' (resp. "
            "''); test_strip_accents asserts == 'o' / '', so it would NOT resolve."
        ),
        "rationale": (
            "POSTCONDITION ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))): "
            "strip_combining DROPS combining marks; this rival keeps them, so the "
            "result diverges on any input with a combining mark."
        ),
    },
    {
        "id": "partial-inverted-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_body(_INVERTED_FILTER_BODY),
        "refinement": (
            "Inverting the predicate (`if combining(c)`) keeps marks and drops "
            "bases: a faithful patch like this returns only the combining marks. "
            "On 'o\\u0308' it returns '\\u0308' instead of 'o'; test_strip_accents "
            "asserts 'o', so it would NOT resolve."
        ),
        "rationale": (
            "POSTCONDITION: strip_combining keeps NON-combining points; the rival "
            "keeps the complement, contradicting the load-bearing equality."
        ),
    },
    {
        "id": "partial-skip-decompose",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_body(_SKIP_DECOMPOSE_BODY),
        "refinement": (
            "Omitting unicodedata.normalize('NFKD', s) and filtering the RAW "
            "input -- strip_combining(s) instead of strip_combining(nfkd(s)) -- "
            "leaves a PRECOMPOSED accent (e.g. chr(241) n-tilde, chr(233) e-acute) "
            "untouched because it is a single non-combining code point that is "
            "never decomposed. test_strip_accents/test_to_ascii expect the accent "
            "stripped, so a faithful patch dropping the NFKD call would NOT "
            "resolve."
        ),
        "rationale": (
            "POSTCONDITION: the result is pinned to strip_combining(NFKD(s)); a "
            "rival that filters s directly drops the nfkd composition and diverges "
            "wherever nfkd(s) != s (precomposed glyphs)."
        ),
    },
    {
        "id": "cf-always-return-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_body(_ALWAYS_RETURN_INPUT_BODY),
        "refinement": (
            "Returning the input unchanged unconditionally (no decomposition, no "
            "filtering) is the prepatch bug generalised. On the F2P discriminator "
            "'o\\u0308' it returns 'o\\u0308' instead of 'o'; test_strip_accents "
            "fails, so it would NOT resolve. (The guarded prepatch variant is "
            "G-DIFF's own prepatch; this is an unconditional standalone wrong "
            "impl exercising the fast-path materialisation in isolation.)"
        ),
        "rationale": (
            "POSTCONDITION: returning s gives ToSeq(Result())==ToSeq(s), which "
            "equals strip_combining(nfkd(s)) only when s is already mark-free in "
            "decomposed form -- false on accented/combining inputs."
        ),
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_body(_POS_CONTROL_BODY),
        "rationale": (
            "A structurally-different but CORRECT impl: fast path builds into "
            "`result` and falls through (no early `out` return); general path "
            "uses the same backward fold (matching strip_combining's "
            "front-recursion -- no induction lemma needed) with the branch test "
            "reordered (`if is_combining: continue` then keep). All gold framing "
            "Asserts/Invariants preserved, so no proof obligation is dropped. "
            "Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_body(_ADMISS_BODY),
        "rationale": (
            "A positive-control caller builds a fresh F2P-shaped input "
            "['o', combining-diaeresis] (the exact test_strip_accents 'o\\u0308' "
            "case), establishes Acc(.,1/2), calls strip_marks, and asserts the "
            "borrow returns and the postcondition holds. If the Requires could "
            "not be met for this normal input, PRECOND-TOO-STRONG."
        ),
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# The bundle carries three @ContractOnly axioms whose Ensures the proof
# CONSUMES (nfkd, is_combining, is_fixed_form_guard) plus one A-reference deep
# model (strip_combining). All four are stdlib-grounded (unicodedata + str
# .encode). Probes execute the REAL callees (NOT source-scraping) and assert
# soundness + caller-domain containment. No flag_dependency: the callees are
# pure stdlib with no runtime config (text.py imports unicodedata directly).
# Probes import only stdlib, open files with encoding='utf-8', and never assume
# any bundle file is mounted in-container.

AXIOM_TESTS = [
    {
        "id": "ax-sound-is_combining",
        "axiom": "is_combining",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, unicodedata\n"
            "# A-consumed axiom: Implies(c < 128, not is_combining(c)).\n"
            "# REAL callee: unicodedata.combining(chr(c)) != 0. Assert every\n"
            "# 7-bit code point has combining class 0 (the only consumed clause),\n"
            "# exhaustively over the boundary domain.\n"
            "bad = [c for c in range(128) if unicodedata.combining(chr(c)) != 0]\n"
            "print('is_combining: ASCII non-combining violations =', bad)\n"
            "if bad:\n"
            "    sys.exit(1)\n"
            "# Sweep further (no obligation above 128, just record the classifier\n"
            "# is well-defined and the implication stays vacuously true).\n"
            "for c in range(0, 0x2000):\n"
            "    if c < 128 and unicodedata.combining(chr(c)) != 0:\n"
            "        print('UNEXPECTED ASCII combining at', c); sys.exit(1)\n"
            "print('is_combining axiom sound on 128 ASCII + 0x2000 sweep')\n"
            "sys.exit(0)\n"
        ),
        "rationale": (
            "If any ASCII code point were combining, the lemma "
            "lemma_ascii_is_fixed_point (strip_combining(s)==s for all_ascii s) "
            "would be unsound -> AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-sound-nfkd",
        "axiom": "nfkd",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, unicodedata, random\n"
            "# A-consumed axiom: Implies(all_ascii(s), nfkd(s) == s).\n"
            "# REAL callee: unicodedata.normalize('NFKD', s). Assert NFKD is the\n"
            "# identity on every pure-ASCII string (the only consumed clause).\n"
            "viol = []\n"
            "# boundary: empty, each ASCII char alone, full ASCII range, words\n"
            "ascii_full = ''.join(chr(c) for c in range(128))\n"
            "boundary = ['', ascii_full, 'hello', 'this is a test', 'abc123 !@#']\n"
            "boundary += [chr(c) for c in range(128)]\n"
            "for s in boundary:\n"
            "    if unicodedata.normalize('NFKD', s) != s:\n"
            "        viol.append(repr(s))\n"
            "# fuzz: random ASCII strings\n"
            "rng = random.Random(15100)\n"
            "for _ in range(20000):\n"
            "    n = rng.randint(0, 20)\n"
            "    s = ''.join(chr(rng.randint(0, 127)) for _ in range(n))\n"
            "    if unicodedata.normalize('NFKD', s) != s:\n"
            "        viol.append(repr(s))\n"
            "print('nfkd identity-on-ASCII violations =', viol[:10], 'count', len(viol))\n"
            "sys.exit(1 if viol else 0)\n"
        ),
        "rationale": (
            "If NFKD altered any pure-ASCII string, the ASCII fast path "
            "(returning s == nfkd(s)) would be wrong -> AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-sound-is_fixed_form_guard",
        "axiom": "is_fixed_form_guard",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "# Runtime guard axiom: Result() == all_ascii(s), i.e. the REAL guard\n"
            "# str.encode('ASCII', errors='strict') succeeds iff every code point\n"
            "# is < 128. Fuzz the boundary (codepoint 127 vs 128) and the raise\n"
            "# path (UnicodeEncodeError).\n"
            "def guard(s):\n"
            "    try:\n"
            "        s.encode('ASCII', errors='strict'); return True\n"
            "    except UnicodeEncodeError:\n"
            "        return False\n"
            "viol = []\n"
            "boundary = ['', 'abc', chr(127), chr(128), chr(127)+chr(128),\n"
            "            'o'+chr(0x308), chr(0x300)+chr(0x301), 'caf'+chr(233)]\n"
            "for s in boundary:\n"
            "    if guard(s) != all(ord(ch) < 128 for ch in s):\n"
            "        viol.append(repr(s))\n"
            "rng = random.Random(151002)\n"
            "for _ in range(20000):\n"
            "    n = rng.randint(0, 16)\n"
            "    s = ''.join(chr(rng.randint(0, 600)) for _ in range(n))\n"
            "    if guard(s) != all(ord(ch) < 128 for ch in s):\n"
            "        viol.append(repr(s))\n"
            "print('is_fixed_form_guard (encode-strict == all<128) violations =',\n"
            "      viol[:10], 'count', len(viol))\n"
            "sys.exit(1 if viol else 0)\n"
        ),
        "rationale": (
            "If encode-strict succeeded on a non-ASCII string (or failed on an "
            "ASCII one), the fast-path branch condition (all_ascii) would not "
            "coincide with the guard -> AXIOM-UNSOUND. This is the genuinely "
            "changed operation in the gold patch."
        ),
    },
    {
        "id": "ax-ref-strip_combining",
        "axiom": "strip_combining",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, unicodedata, random\n"
            "# A-reference deep model: strip_combining(nfkd(s)) must equal the\n"
            "# REAL post-patch transform ''.join(c for c in normalize('NFKD',s)\n"
            "# if not combining(c)). Execute BOTH on the same inputs (incl. the\n"
            "# F2P discriminators) and compare. This is the whole function under\n"
            "# change, modeled deeply (not consumed as an axiom about itself).\n"
            "def model_strip(cps):\n"
            "    return [c for c in cps if unicodedata.combining(chr(c)) == 0]\n"
            "def deep_model(s):\n"
            "    norm = [ord(ch) for ch in unicodedata.normalize('NFKD', s)]\n"
            "    return model_strip(norm)\n"
            "def real(s):\n"
            "    norm = unicodedata.normalize('NFKD', s)\n"
            "    return [ord(ch) for ch in norm if not unicodedata.combining(ch)]\n"
            "viol = []\n"
            "boundary = ['', 'o'+chr(0x308), chr(0x300)+chr(0x301)+chr(0x302)+chr(0x303),\n"
            "            'o'+chr(0x308)+chr(0x304), chr(241), chr(110)+chr(771),\n"
            "            chr(0x301), 'this is a test', 'caf'+chr(233),\n"
            "            'caf'+'e'+chr(0x301)]\n"
            "for s in boundary:\n"
            "    if deep_model(s) != real(s):\n"
            "        viol.append(repr(s))\n"
            "rng = random.Random(151003)\n"
            "alpha = ([chr(c) for c in range(0, 128)]\n"
            "         + [chr(c) for c in range(0x80, 0x500)]\n"
            "         + [chr(c) for c in range(0x300, 0x370)]\n"
            "         + [chr(241), chr(110), chr(771), chr(0x308), chr(0x304)])\n"
            "for _ in range(40000):\n"
            "    n = rng.randint(0, 16)\n"
            "    s = ''.join(rng.choice(alpha) for _ in range(n))\n"
            "    if deep_model(s) != real(s):\n"
            "        viol.append(repr(s))\n"
            "print('deep model strip_combining(nfkd(.)) vs real transform "
            "violations =', viol[:10], 'count', len(viol))\n"
            "sys.exit(1 if viol else 0)\n"
        ),
        "rationale": (
            "If the deep model diverged from the real comprehension on any "
            "caller-reachable input, the postcondition would be pinned to the "
            "wrong transform -> the A-reference would be unsound."
        ),
    },
    {
        "id": "ax-contain-callees",
        "axiom": "nfkd,is_combining,is_fixed_form_guard",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys, unicodedata\n"
            "# Containment: every callee-input the MODEL can reach lies in the\n"
            "# axiom's Requires domain.\n"
            "#  * is_combining(c): model only ever calls it on c = a code point\n"
            "#    of nfkd(s) or of s -- i.e. any int in [0, 0x10FFFF]. The axiom's\n"
            "#    Requires is TRUE (no domain restriction); its Ensures only\n"
            "#    CONSTRAINS c<128 but the predicate is total. So every reachable\n"
            "#    c is covered (the axiom is total over ints). Confirm the real\n"
            "#    callee is defined (no exception) on the full reachable range.\n"
            "#  * nfkd(s) / decompose(s): Requires Acc(list_pred(s),1/2); domain\n"
            "#    is any code-point sequence. Confirm normalize('NFKD',.) is total\n"
            "#    on arbitrary strings.\n"
            "#  * is_fixed_form_guard(s): Requires Acc(.,1/2); total over strings.\n"
            "# A reachable input OUTSIDE a covered domain would be AXIOM-TOO-WEAK;\n"
            "# here every axiom Requires is unrestricted, so containment is trivial\n"
            "# -- we verify the real callees never raise on the reachable domain\n"
            "# (which would expose an implicit domain restriction the model omits).\n"
            "fail = []\n"
            "for c in list(range(0, 0x2000)) + [0x10FFFF, 0xFFFD, 0x1F600]:\n"
            "    try:\n"
            "        unicodedata.combining(chr(c))\n"
            "    except Exception as e:\n"
            "        fail.append(('combining', c, repr(e)))\n"
            "samples = ['', 'a'*20, 'o'+chr(0x308), chr(241)*5, chr(0x10FFFF),\n"
            "           chr(0x300)*8, ''.join(chr(c) for c in range(128))]\n"
            "for s in samples:\n"
            "    try:\n"
            "        unicodedata.normalize('NFKD', s)\n"
            "    except Exception as e:\n"
            "        fail.append(('normalize', repr(s), repr(e)))\n"
            "    try:\n"
            "        s.encode('ASCII', errors='strict')\n"
            "    except UnicodeEncodeError:\n"
            "        pass\n"  # expected on non-ascii; not a domain failure
            "    except Exception as e:\n"
            "        fail.append(('encode', repr(s), repr(e)))\n"
            "print('containment domain-failures =', fail[:10], 'count', len(fail))\n"
            "sys.exit(1 if fail else 0)\n"
        ),
        "rationale": (
            "Every axiom's Requires is unrestricted (the callees are total over "
            "the code-point/string domain the model reaches via s and nfkd(s)). "
            "No caller-reachable input falls outside any axiom domain -> covered; "
            "a raise on the reachable domain would expose AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
