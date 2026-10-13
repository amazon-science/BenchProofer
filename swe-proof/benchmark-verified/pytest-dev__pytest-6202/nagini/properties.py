# properties.py — PBT manifest for pytest-dev__pytest-6202. NOT a Nagini module;
# a record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# executes each and stamps RESULT.
#
# Defended surface (read from model.py + refinement.md + the gold patch):
#   modpath_of(parts: PSeq[PSeq[int]]) -> PSeq[int]
#     Requires(len(parts) >= 1)
#     Requires(MustTerminate(2))                       <-- total-correctness pin
#     Ensures(Result() == join_dot(parts))            <-- THE load-bearing clause
#   join_dot is a @Pure front-recursive dot-join fold, grounded entirely in the
#   input `parts` (separator code point 46 == '.').
#
# The gold patch is a one-hunk deletion: it REMOVES the post-join substitution
#   -        s = ".".join(parts)
#   -        return s.replace(".[", "[")
#   +        return ".".join(parts)
# so the entire correctness content is "return the plain dot-join, with NO
# '.[' -> '[' substitution applied". The F2P (test_example_items1) asserts
#   items[3].getmodpath() == "TestY.testmethod_two[.[]"
# for a parametrised test whose part name contains '.[' — the pre-patch code
# corrupts it to "TestY.testmethod_two[[]". The whole battery is built around
# that one discriminator.
#
# Adversarial reasoning per weakness class (see the battery-authoring brief):
#  - FRAME-MUTATION: N/A. `parts` is PSeq[PSeq[int]], an immutable mathematical
#    value — there is NO Acc(...,1/2) heap-permission input to overwrite (the
#    Requires is `len(parts) >= 1`, no permission predicate). There is nothing to
#    frame-mutate, so no frame-mutation reject case exists. (justified below)
#  - UNGROUNDED-ORACLE: the postcondition oracle join_dot(parts) is GROUNDED in
#    the input (a @Pure fold fully unfolded over `parts`), and is *itself* the
#    correct answer the gold returns. "Echoing" it is the correct impl, not a
#    wrong echo — so there is no ungrounded-oracle break. Instead we ship an
#    honest cheapest-impl positive control (pos-direct: `return join_dot(parts)`).
#  - PARTIAL-DOMAIN: the real attack surface. Rivals correct on '.'-free /
#    '['-free parts but diverging on the '.[' sub-domain (exactly the F2P
#    witness). prepatch-substitution (full bug), partial-substitution (first-hit
#    only), and drop-separator are all here.
#  - CONTROL-FLOW-EFFECT: N/A. modpath_of is a pure total value function with no
#    raise/return/side-effect path the value abstraction misses. (justified)
#
# Region surgery: every SPEC_TESTS module is built by _swap on _BASE editing ONLY
# text strictly between `# impl-start` and `# impl-end`. The frozen spec
# (axioms/pure/pre/post + signatures) is never touched, so same_spec holds.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-6202"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region, verbatim (the unique anchor we _swap against). Editing
# only the text below keeps every spec region (axioms/pure/pre/post) untouched.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    result = parts[len(parts) - 1]  # type: PSeq[int]
    i = len(parts) - 1
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(parts) - 1)
        # `result` is the dot-join of the suffix parts[i:].
        Invariant(result == join_dot(parts.drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(parts.drop(i - 1)[0] == parts[i - 1])
        Assert(parts.drop(i - 1).drop(1) == parts.drop(i))
        result = (parts[i - 1] + PSeq(46)) + result
        i = i - 1
    return result"""

# sanity: the anchor must be present and unique in the frozen model.py
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl anchor drifted from model.py"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ===========================================================================

# pos-direct: the cheapest honest impl — return the grounded @Pure oracle
# directly, no loop. This is exactly the gold patch shape (`return ".".join`).
# Because join_dot is grounded in the input (not an opaque answer-key), this is
# the CORRECT answer, not a wrong echo. It MUST verify (else SPEC-TOO-STRONG).
_POS_DIRECT = _swap(
    _BASE, _GOLD_IMPL,
    "    return join_dot(parts)",
)

# pos-reshape: structurally-different but CORRECT — same backward fold, but with
# the accumulator renamed and the loop guard written `i >= 1` instead of
# `i > 0`, and the per-element pins/invariants KEPT verbatim (directive 2/3: we
# change only the executable shape, never drop a framing assert, and we do NOT
# flip to a forward-append that would need an f(a+b)==f(a)+f(b) lemma the
# verifier can't auto-discharge). MUST verify (else SPEC-TOO-STRONG).
_POS_RESHAPE = _swap(
    _BASE, _GOLD_IMPL,
    """    acc = parts[len(parts) - 1]  # type: PSeq[int]
    i = len(parts) - 1
    while i >= 1:
        # invariants-start
        Invariant(0 <= i and i <= len(parts) - 1)
        # `acc` is the dot-join of the suffix parts[i:].
        Invariant(acc == join_dot(parts.drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(parts.drop(i - 1)[0] == parts[i - 1])
        Assert(parts.drop(i - 1).drop(1) == parts.drop(i))
        acc = (parts[i - 1] + PSeq(46)) + acc
        i = i - 1
    return acc""",
)

# admiss-f2p: an admissibility caller. After the gold loop builds `result`,
# assert that the precondition admits an F2P-shaped input (>= 1 part) AND that
# on a 2-part witness the result is the plain join (the '.[' inside part[1]
# survives) — i.e. the spec accepts the real collection witness shape. The added
# Asserts are downstream of `result == join_dot(parts)` (the postcondition), so
# they are discharged from the contract, not re-proven. MUST verify (else
# PRECOND-TOO-STRONG / SPEC-TOO-STRONG).
_ADMISS = _swap(
    _BASE, _GOLD_IMPL,
    _GOLD_IMPL.replace(
        "    return result",
        """    # admissibility: the precondition admits the normal F2P-shaped input
    # (>= 1 part) and the result is the plain dot-join with no substitution.
    Assert(len(parts) >= 1)
    Assert(result == join_dot(parts))
    return result""",
    ),
)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN rivals — must be REJECTED (else SPEC-TOO-WEAK).
# Each is correct on the '.['-free sub-domain but diverges on a part containing
# '.[' — which is precisely the F2P witness ("testmethod_two[.[]").
# ===========================================================================

# weak-prepatch: the literal PRE-PATCH bug — build the dot-join, then apply the
# removed `.replace(".[", "[")` substitution (left-to-right, non-overlapping
# collapse of [46,91] -> [91]). This is the model_prepatch.py impl. It returns
# join_dot for any '.['-free parts but collapses '.[' -> '[', so its Result is
# join_dot(parts) with the substitution applied, which != join_dot(parts) on the
# F2P witness. MUST be rejected by the postcondition Result() == join_dot(parts).
_WEAK_PREPATCH = _swap(
    _BASE, _GOLD_IMPL,
    """    joined = parts[len(parts) - 1]  # type: PSeq[int]
    i = len(parts) - 1
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(parts) - 1)
        Invariant(joined == join_dot(parts.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(parts.drop(i - 1)[0] == parts[i - 1])
        Assert(parts.drop(i - 1).drop(1) == parts.drop(i))
        joined = (parts[i - 1] + PSeq(46)) + joined
        i = i - 1
    # the REMOVED buggy ".replace('.[', '[')": left-to-right, non-overlapping.
    result = PSeq(0).take(0)  # type: PSeq[int]
    j = 0
    while j < len(joined):
        # invariants-start
        Invariant(0 <= j and j <= len(joined))
        Invariant(MustTerminate(len(joined) - j + 1))
        # invariants-end
        if j + 1 < len(joined) and joined[j] == 46 and joined[j + 1] == 91:
            result = result + PSeq(91)
            j = j + 2
        else:
            result = result + PSeq(joined[j])
            j = j + 1
    return result""",
)

# weak-firsthit: a subtler partial-domain bug — collapse only the FIRST '.['
# occurrence in the join (single scan, stop after one replacement). Correct on
# parts with no '.[', but still wrong on the F2P witness (whose join is
# "TestY.testmethod_two[.[]" and contains a '.[' that this rival collapses to
# "[", yielding "...[[]"). MUST be rejected by Result() == join_dot(parts).
_WEAK_FIRSTHIT = _swap(
    _BASE, _GOLD_IMPL,
    """    joined = parts[len(parts) - 1]  # type: PSeq[int]
    i = len(parts) - 1
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(parts) - 1)
        Invariant(joined == join_dot(parts.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(parts.drop(i - 1)[0] == parts[i - 1])
        Assert(parts.drop(i - 1).drop(1) == parts.drop(i))
        joined = (parts[i - 1] + PSeq(46)) + joined
        i = i - 1
    # collapse ONLY the first '.[' occurrence, then copy the rest verbatim.
    result = PSeq(0).take(0)  # type: PSeq[int]
    j = 0
    done = False
    while j < len(joined):
        # invariants-start
        Invariant(0 <= j and j <= len(joined))
        Invariant(MustTerminate(len(joined) - j + 1))
        # invariants-end
        if (not done) and j + 1 < len(joined) and joined[j] == 46 and joined[j + 1] == 91:
            result = result + PSeq(91)
            j = j + 2
            done = True
        else:
            result = result + PSeq(joined[j])
            j = j + 1
    return result""",
)

# weak-nosep: drop the '.' separator — return the bare concatenation of parts
# (a different but plausible "join"). For the single-part case it coincides with
# the gold, but for any multi-part input it omits the '.' separators, so on the
# F2P witness it returns "TestYtestmethod_two[.[]" != "TestY.testmethod_two[.[]".
# MUST be rejected by Result() == join_dot(parts).
_WEAK_NOSEP = _swap(
    _BASE, _GOLD_IMPL,
    """    result = parts[len(parts) - 1]  # type: PSeq[int]
    i = len(parts) - 1
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(parts))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        result = parts[i - 1] + result
        i = i - 1
    return result""",
)

# weak-nonterm: the audit's P1 attack shape — a REACHABLE nonterminating
# implementation. Under Nagini's default partial correctness an infinite loop
# makes every Ensures hold vacuously (the exit is unreachable), so a spec with
# no termination obligation ADMITS it even though the real getmodpath always
# returns. The MustTerminate(2) precondition forces the loop to carry a
# decreasing bounded measure; this loop cannot, so it MUST be rejected.
_WEAK_NONTERM = _swap(
    _BASE, _GOLD_IMPL,
    """    k = 0
    while k >= 0:
        # invariants-start
        Invariant(k >= 0)
        # invariants-end
        k = k + 1
    return join_dot(parts)""",
)


SPEC_TESTS = [
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "Cheapest honest impl: return the grounded @Pure oracle join_dot(parts) "
            "directly (exactly the gold patch shape `return \".\".join(parts)`). The "
            "oracle is a function of the input, not an opaque answer-key, so this is "
            "the correct answer. Postcondition Result()==join_dot(parts) is then "
            "trivially discharged. Must verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": (
            "Structurally-different but correct: same backward fold with the "
            "accumulator renamed (result->acc) and the loop guard rewritten i>=1 "
            "(equivalent to i>0), keeping every gold invariant and per-element pin "
            "verbatim (directive 2/3 — no dropped framing assert, no forward-append "
            "that would need an f(a+b) distribution lemma). Must verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Admissibility: the precondition len(parts)>=1 admits the normal "
            "F2P-shaped input (>=1 part) and the postcondition gives the plain "
            "dot-join (asserts are discharged from the contract, downstream of the "
            "gold loop). Must verify, else PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_PREPATCH,
        "refinement": (
            "This IS the faithful pre-patch implementation (it re-applies the exact "
            "`s.replace(\".[\", \"[\")` the gold patch DELETES). Its real-code "
            "counterpart is the base_commit code, which the F2P "
            "(test_example_items1) fails: it asserts "
            "items[3].getmodpath() == \"TestY.testmethod_two[.[]\" but the "
            "substitution produces \"TestY.testmethod_two[[]\". So a verifying "
            "weak-prepatch would be a true verify-but-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the postcondition Result()==join_dot(parts): the impl "
            "returns replace_db(join_dot(parts)), which differs from join_dot(parts) "
            "exactly when a '.[' is present (the F2P witness). The substitution loop "
            "verifies; only the function postcondition fails (meta G-DIFF confirms "
            "model_prepatch.py fails on Result()==join_dot(parts))."
        ),
    },
    {
        "id": "weak-firsthit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_FIRSTHIT,
        "refinement": (
            "A subtler bug than the original: collapse only the FIRST '.[' in the "
            "join. The faithful real patch (a one-shot replace, e.g. "
            "`s.replace(\".[\", \"[\", 1)`) still fails the F2P assertion "
            "items[3].getmodpath() == \"TestY.testmethod_two[.[]\": the joined path "
            "\"TestY.testmethod_two[.[]\" contains a '.[' that the single replacement "
            "collapses, yielding \"TestY.testmethod_two[[]\" — wrong. Would be a "
            "verify-but-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by Result()==join_dot(parts): on any input whose join contains "
            "a '.[', the returned sequence is shorter by one code point than "
            "join_dot(parts), so the equality fails."
        ),
    },
    {
        "id": "weak-nonterm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_NONTERM,
        "refinement": (
            "The audited P1 break shape: an implementation that diverges on a "
            "reachable input (an infinite loop before ever producing the path). "
            "The real getmodpath always returns; a nonterminating counterpart "
            "would hang collection and fail every F2P/PASS test by timeout. "
            "Under partial correctness the spec ADMITTED this (the auditor's "
            "atk_9_nonterm_reachable.py verified); with MustTerminate(2) in the "
            "precondition it must be rejected."
        ),
        "rationale": (
            "Rejected by the MustTerminate(2) obligation: the divergent loop "
            "carries no MustTerminate invariant with a decreasing bounded "
            "measure (none exists for `while k >= 0: k += 1`), so the caller's "
            "termination obligation cannot be discharged and verification "
            "fails. This is exactly the total-correctness pin that closes the "
            "audit's spec-too-weak finding."
        ),
    },
    {
        "id": "weak-nosep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WEAK_NOSEP,
        "refinement": (
            "Joins the parts with NO separator (`\"\".join(parts)` instead of "
            "`\".\".join(parts)`). Its faithful real patch fails the F2P PASS-line "
            "assertions too: items[1].getmodpath() must equal "
            "\"TestX.testmethod_one\" but bare concatenation gives "
            "\"TestXtestmethod_one\". A verifying weak-nosep would be a "
            "verify-but-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by Result()==join_dot(parts): join_dot inserts code point 46 "
            "('.') between consecutive parts; the bare concatenation omits it, so "
            "for any multi-part input the result differs (shorter by len(parts)-1)."
        ),
    },
]


# ===========================================================================
# AXIOM / A-reference deep-model lane.
#
# meta.json `axioms: []` — there is NO @ContractOnly consumed axiom. But there
# are two A-reference deep models (deep_model_references):
#   join_dot   <- ".".join(parts)   (kept; provenance python.py:288)
#   replace_db <- s.replace(".[","[") (removed by the patch; prepatch witness)
# PLAN §2.4 / §4a: A-reference deep models are checked the same way — the deep
# model must equal the real callee on every caller-reachable input (soundness),
# and every callee-input the model can reach must lie in the callee's domain
# (containment). We reuse axiom_check.py's logic and STRENGTHEN it on the '.['
# sub-domain + the F2P witness. The probes are pure CPython stdlib (str.join /
# str.replace), so they are self-contained; they run in the instance image but
# need no repo import (the runner mounts only the probe at /work — directive 6 —
# so we embed everything).
# ===========================================================================

# The deep-model reference encodings, copied in lock-step from axiom_check.py on
# the HOST at manifest-load time and embedded into the probe strings below (so
# the in-container probe is fully self-contained; directive 6).
_DEEP_MODELS = r'''
def join_dot(parts):
    """Deep model of model.py's join_dot, on lists of code points."""
    if len(parts) == 0:
        return []
    out = list(parts[0])
    for p in parts[1:]:
        out.append(46)  # '.'
        out.extend(p)
    return out

def replace_db(s):
    """Deep model of model_prepatch.py's replace_db (left-to-right,
    non-overlapping '.[' -> '['; 46,91 -> 91)."""
    out = []
    j = 0
    n = len(s)
    while j < n:
        if j + 1 < n and s[j] == 46 and s[j + 1] == 91:
            out.append(91)
            j += 2
        else:
            out.append(s[j])
            j += 1
    return out

def cps(s):
    return [ord(ch) for ch in s]
'''

_AX_SOUND_JOIN = _DEEP_MODELS + r'''
import random, sys

def check_join(parts):
    strs = ["".join(chr(c) for c in p) for p in parts]
    observed = [ord(ch) for ch in ".".join(strs)]   # REAL CPython str.join
    expected = join_dot(parts)                       # deep model
    assert observed == expected, ("join_dot UNSOUND on %r: real str.join %r != "
                                  "deep model %r" % (strs, observed, expected))

# boundary part-lists, weighted toward the '.[' sub-domain and the F2P witness
boundary = [
    [], [cps("testone")],
    [cps("TestX"), cps("testmethod_one")],
    [cps("TestY"), cps("testmethod_one")],
    [cps("TestY"), cps("testmethod_two[.[]")],   # the F2P collection witness
    [cps(""), cps("")], [cps("a.b"), cps("c")],
    [cps("x"), cps("[")], [cps("x"), cps(".[")], [cps(".["), cps(".[")],
    [cps("test_boo[..[]")],
    [cps("a"), cps("b"), cps("c"), cps("d")],     # >2 parts: many separators
]
for parts in boundary:
    check_join(parts)

# fuzz over a '.['-rich alphabet, varying part-count and part-length
rng = random.Random(6202)
alphabet = cps(".[]abT0_")
for _ in range(50000):
    nparts = rng.randint(0, 5)
    parts = []
    for _ in range(nparts):
        m = rng.randint(0, 8)
        parts.append([rng.choice(alphabet) for _ in range(m)])
    check_join(parts)

# F2P discriminator: the plain join is exactly the asserted string
w = [cps("TestY"), cps("testmethod_two[.[]")]
assert "".join(chr(c) for c in join_dot(w)) == "TestY.testmethod_two[.[]", \
    "join_dot(F2P witness) != the F2P-asserted path"
print("AX-SOUND-JOIN OK: join_dot == real str.join on %d boundary + 50000 fuzz "
      "inputs; F2P witness joins to the asserted path" % len(boundary))
sys.exit(0)
'''

_AX_SOUND_REPLACE = _DEEP_MODELS + r'''
import random, sys

def check_replace(codepoints):
    s = "".join(chr(c) for c in codepoints)
    observed = [ord(ch) for ch in s.replace(".[", "[")]   # REAL CPython str.replace
    expected = replace_db(codepoints)                      # deep model
    assert observed == expected, ("replace_db UNSOUND on %r: real str.replace %r "
                                  "!= deep model %r" % (s, observed, expected))

boundary = ["", ".", "[", ".[", "..[", ".[.[", "[.[", ".[]", "[.[]",
            "TestY.testmethod_two[.[]", "test_boo[..[]",
            "a.b.c", "....", "[[[[", ".[.[.[", "no brackets here",
            "trailing.", ".[lead", ".][.", "[.].["]
for s in boundary:
    check_replace(cps(s))

rng = random.Random(62020)
alphabet = cps(".[]abT0_")
for _ in range(50000):
    k = rng.randint(0, 18)
    s = [rng.choice(alphabet) for _ in range(k)]
    check_replace(s)

# bug-witness: on the F2P join the substitution genuinely corrupts the path,
# so the spec's Result()==join_dot discriminator is meaningful.
w = [cps("TestY"), cps("testmethod_two[.[]")]
gold = join_dot(w)
bug = replace_db(join_dot(w))
assert gold != bug, "twin does not discriminate on the F2P witness"
assert "".join(chr(c) for c in bug) == "TestY.testmethod_two[[]", \
    "pre-patch substitution does not produce the corrupted path"
print("AX-SOUND-REPLACE OK: replace_db == real str.replace on %d boundary + "
      "50000 fuzz inputs; substitution corrupts the F2P path (gold != bug)"
      % len(boundary))
sys.exit(0)
'''

_AX_COVER_JOIN = _DEEP_MODELS + r'''
import sys
# Containment: which inputs can modpath_of actually pass to the join callee?
# Requires(len(parts) >= 1); each part is an arbitrary PSeq[int] of code points;
# the backward fold reaches join_dot on `parts` and every suffix parts.drop(i)
# for 1 <= i <= len(parts)-1 (and join_dot recurses through its own .drop(1)),
# i.e. every NON-EMPTY suffix and (via join_dot's base cases) the empty list and
# single-part lists. The real callee `str.join(iterable_of_str)` is TOTAL over
# any finite list of strings (incl. empty list -> "", single -> itself, parts
# containing ANY character). So every caller-reachable input is in the callee
# domain. We assert real str.join is defined (no exception) on a representative
# enumeration of reachable shapes, including parts with '.' / '[' / '.[' and the
# empty/single/multi-part cases.
def reachable_part_lists():
    glyphs = ["", "a", ".", "[", ".[", "TestY", "testmethod_two[.[]", "..[", "[.["]
    lists = [[], [list(map(ord, "x"))]]              # empty + single (join base cases)
    for g1 in glyphs:
        for g2 in glyphs:
            lists.append([list(map(ord, g1)), list(map(ord, g2))])
    # a >2-part list to exercise multiple separators
    lists.append([list(map(ord, g)) for g in ["TestY", "Inner", "testmethod_two[.[]"]])
    return lists

bad = []
for parts in reachable_part_lists():
    strs = ["".join(chr(c) for c in p) for p in parts]
    try:
        r = ".".join(strs)                            # must not raise
    except Exception as e:
        bad.append((strs, repr(e)))
        continue
    if [ord(ch) for ch in r] != join_dot(parts):
        bad.append((strs, "deep model mismatch"))
assert not bad, "caller-reachable inputs outside str.join domain / mismatch: %r" % bad
print("AX-COVER-JOIN OK: every caller-reachable part-list (empty/single/multi, "
      "incl. '.[' parts) is in str.join's domain and matches join_dot")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-join",
        "axiom": "join_dot",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_JOIN,
        "rationale": (
            "A-reference soundness: the deep model join_dot must equal the real "
            "CPython str.join on every caller-reachable input. We run the REAL "
            "'.'.join on boundary + 50000 fuzz part-lists (weighted to the '.[' "
            "sub-domain + the F2P witness) and assert agreement. If the real callee "
            "ever disagrees, the A-reference is UNSOUND."
        ),
    },
    {
        "id": "ax-sound-replace",
        "axiom": "replace_db",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_REPLACE,
        "rationale": (
            "A-reference soundness for the REMOVED operation (prepatch witness): the "
            "deep model replace_db must equal the real CPython s.replace('.[', '[') "
            "on every input. We run the REAL str.replace on boundary + 50000 fuzz "
            "strings and assert agreement, and confirm the substitution genuinely "
            "corrupts the F2P path (so the twin's discriminator is real). If the "
            "real callee disagrees, the prepatch-witness A-reference is UNSOUND."
        ),
    },
    {
        "id": "ax-cover-join",
        "axiom": "join_dot",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_JOIN,
        "rationale": (
            "Containment: every part-list modpath_of can reach (Requires "
            "len(parts)>=1; arbitrary code-point parts; all non-empty suffixes plus "
            "join_dot's empty/single base cases) lies in str.join's domain "
            "(str.join is total over any finite list of strings). A reachable input "
            "outside the callee domain would be AXIOM-TOO-WEAK-FOR-CALLER; none "
            "exists here."
        ),
    },
]
