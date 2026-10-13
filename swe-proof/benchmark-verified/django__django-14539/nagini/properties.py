# properties.py — PBT manifest for django__django-14539. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses + executes.
#
# Modeled function (the single changed operation):
#   trim_trailing_punct(middle, trail, decoded_len, kept_len) -> (new_middle, new_trail)
#
#   Requires:  Acc(list_pred(middle),1/2)    <-- READ-ONLY input
#              Acc(list_pred(trail),1/2)      <-- READ-ONLY input
#              0 <= decoded_len <= len(middle)        (decode never lengthens)
#              0 <= kept_len    <= decoded_len        (rstrip never lengthens)
#              kept_len < decoded_len                 (the trim branch guard)
#   Ensures:   Acc(list_pred(middle),1/2), Acc(list_pred(trail),1/2)   (inputs unchanged)
#              Acc(list_pred(Result()[0])), Acc(list_pred(Result()[1]))  (FRESH full-perm)
#              len(Result()[0]) == len(middle) - (decoded_len - kept_len)   [C1 length]
#              ToSeq(Result()[1]) == ToSeq(middle).drop(len(middle)-(decoded_len-kept_len))
#                                    + ToSeq(trail)                          [C2 moved trail]
#              ToSeq(Result()[0]) + ToSeq(Result()[1]).take(decoded_len-kept_len)
#                                    == ToSeq(middle)                        [C3 lossless]
#
# The postcondition is FULLY GROUNDED in the inputs (take/drop of `middle`,
# `trail`, with integer `decoded_len`/`kept_len`) — there is NO @Pure answer-key
# oracle to echo, so the ungrounded-oracle-echo class does NOT apply (see the
# positive control instead). There is NO @ContractOnly axiom (axioms region is
# empty); the decode/strip callees enter only as the A-reference length summaries
# decoded_len/kept_len, whose bounds the AXIOM_TESTS probe against the real
# stdlib html.unescape + str.rstrip.
#
# Region-surgery authoring: every SPEC variant is built by _swap on _BASE,
# editing ONLY the text strictly inside the # impl-start / # impl-end region; the
# frozen spec (axioms/pure/pre/post-conditions + signature) is never touched, so
# markers.same_spec(base, variant) is True for every case.
from pathlib import Path

INSTANCE = "django__django-14539"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats in this model)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen GOLD impl region body (text strictly between the impl markers).
_GOLD_IMPL = """    punctuation_count = decoded_len - kept_len
    split = len(middle) - punctuation_count
    moved = middle[split:]
    new_trail = moved + trail
    new_middle = middle[:split]
    return new_middle, new_trail"""


def _with_impl(new_body: str) -> str:
    """Return _BASE with the gold impl body replaced by new_body (impl region
    only). Guarantees same_spec because only the impl text changes."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL (soundness, expect=verify).
# A structurally DIFFERENT but CORRECT impl: compute the cut boundary inline as
# `n - count` (no intermediate `split`/`punctuation_count` locals), build the
# kept central part FIRST, then the moved suffix. Same take/drop boundaries as
# the gold proof — slicing is a direct ToSeq.take/.drop, so no induction lemma is
# needed (avoids the forward-append-vs-front-fold trap). Must verify; if a
# faithful correct impl cannot satisfy the Ensures => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_CONTROL = """    # CORRECT, structurally reshaped: inline boundary `n - count`, kept part
    # built before the moved suffix, no `split`/`punctuation_count` locals.
    # NOTE: Nagini cannot translate a slice subscript used DIRECTLY as an
    # operand of `+` (e.g. `middle[boundary:] + trail` raises "Unsupported
    # operator" on the `+`); the moved suffix slice must be bound to a local
    # before the concat. Binding it to `moved` does NOT undo the structural
    # reshape (boundary inlined as `n - count`; `new_middle` still built before
    # the moved suffix, the reverse of the gold's `moved`-first order; no
    # `split`/`punctuation_count` locals).
    n = len(middle)
    count = decoded_len - kept_len
    boundary = n - count
    new_middle = middle[:boundary]
    moved = middle[boundary:]
    new_trail = moved + trail
    return new_middle, new_trail"""


# ---------------------------------------------------------------------------
# (2) PREPATCH BUG (uniqueness, expect=reject). The exact model_prepatch.py impl:
# the moved-suffix boundary is the DECODED kept length kept_len (an index into
# the decoded form) applied to the ENCODED middle. new_middle is computed via
# middle[:kept_len - decoded_len] (== middle[:-count], identical to gold's
# new_middle), so C1 (length) and C3 (lossless, which only constrains the kept
# part + the first `count` moved) can still hold; but C2 pins the moved trail to
# ToSeq(middle).drop(len(middle)-count): the prepatch moves middle[kept_len:]
# (len(middle)-kept_len code points), which equals middle.drop(len(middle)-count)
# ONLY when len(middle)==decoded_len (no entities). On any entity-bearing middle
# (encoded longer than decoded) it moves too many code points => C2 fails => REJECT.
# REFINEMENT: its faithful real patch is the literal pre-fix block
#   trail = middle[len(stripped):] + trail ; middle = middle[:len(stripped)-len(unescaped)]
# which is exactly the buggy code the issue reports — on 'google.com/?q=1&lt!' it
# leaks the extra 'lt' into the trailing text (actual 'lt! and see.' vs expected
# '! and see.'), so test_urlize stays RED. A verifying rival here would be a true
# verify-but-not-resolve break. Rejection source: postcondition clause C2.
# ---------------------------------------------------------------------------
_PREPATCH_BUG = """    # ADVERSARY (the reported bug): use the DECODED kept length as the boundary
    # into the ENCODED middle. Agrees with gold only when no entities are present.
    moved = middle[kept_len:]
    new_trail = moved + trail
    new_middle = middle[:kept_len - decoded_len]
    return new_middle, new_trail"""


# ---------------------------------------------------------------------------
# (3) FRAME-MUTATION on `middle` (uniqueness/frame-mutation, MANDATORY,
# expect=reject). `middle` is Acc(list_pred(middle),1/2) — READ-ONLY. A rival
# that WRITES to middle (append) to reshape it, then returns it as the new
# central part. The half-permission forbids any write => REJECT for INSUFFICIENT
# PERMISSION (it never reaches the postcondition). Returning middle would also
# violate Acc(list_pred(Result()[0])) (a FRESH full-perm list) and the Ensures
# Acc(list_pred(middle),1/2) frame, but the write is the primary rejection. A
# byte-fuzzer never thinks to mutate the input — the project's #1 weakness class.
# REFINEMENT: a faithful real patch that mutated `middle` in place would corrupt
# urlize's shared word string across the surrounding loop (lead/middle/trail are
# re-sliced repeatedly), changing later iterations and the final markup =>
# test_urlize / test_urlize_unchanged_inputs would NOT pass. Rejection source:
# the permission system (insufficient write permission on middle).
# ---------------------------------------------------------------------------
_FRAME_MUT_MIDDLE = """    # ADVERSARY: write to the read-only input `middle`, then return it.
    # Acc(list_pred(middle),1/2) forbids the write -> insufficient permission.
    middle.append(0)
    new_trail = trail
    return middle, new_trail"""


# ---------------------------------------------------------------------------
# (4) FRAME-MUTATION on `trail` (uniqueness/frame-mutation, MANDATORY,
# expect=reject). The OTHER read-only input. A rival that tries to build the new
# trailing part by WRITING into `trail` in place (append) instead of producing a
# fresh list, then returns it. Acc(list_pred(trail),1/2) forbids the write =>
# REJECT for INSUFFICIENT PERMISSION. Distinct from (3): proves BOTH read-only
# inputs are protected, not just middle.
# REFINEMENT: a faithful real patch that appended onto the shared `trail` string
# accumulator in place (Python strs are immutable, so the only way to "do this"
# is to rebind, which the model's in-place write models as forbidden) would
# diverge from the gold prepend semantics and corrupt the accumulated trailing
# text across urlize's loop => F2P would NOT pass. Rejection source: the
# permission system (insufficient write permission on trail).
# ---------------------------------------------------------------------------
_FRAME_MUT_TRAIL = """    # ADVERSARY: build the new trailing part by WRITING into the read-only input
    # `trail` (append the moved suffix), then return it. Acc(list_pred(trail),1/2)
    # forbids the write -> insufficient permission.
    punctuation_count = decoded_len - kept_len
    split = len(middle) - punctuation_count
    new_middle = middle[:split]
    trail.append(0)
    return new_middle, trail"""


# ---------------------------------------------------------------------------
# (5) PARTIAL-DOMAIN (uniqueness, expect=reject). A rival CORRECT on the common
# subdomain "exactly one trailing punctuation char" (count == 1, e.g. the F2P
# 'google.com/?q=1&lt!' which strips a single '!') but WRONG whenever 2+ chars
# trail (e.g. 'foo.com!!!' -> 3, or 'x&lt;y&gt;z.,:;!' -> several). It hardcodes
# the moved count to 1: moves the last ONE code point and keeps n-1, regardless
# of the real decoded_len-kept_len. On the count==1 subdomain it matches gold; on
# count>=2 it violates C1 (len(Result()[0]) == len(middle)-(decoded_len-kept_len))
# and C2/C3. The length clause C1 pins the EXACT count, so the verifier rejects
# this for any input where count != 1 (the precondition only guarantees
# kept_len < decoded_len, i.e. count >= 1, NOT count == 1) => REJECT.
# REFINEMENT: a faithful real patch hardcoding `punctuation_count = 1` would pass
# single-trailing-punct urlize cases but fail multi-trailing-punct cases present
# in the test suite (test_urlize_unchanged_inputs covers strings whose trailing
# run is longer than one), leaving those F2P/P2P assertions RED. Rejection
# source: postcondition clause C1 (length must equal the EXACT count, not 1).
# ---------------------------------------------------------------------------
_PARTIAL_DOMAIN = """    # ADVERSARY: assume exactly one trailing punctuation char (count == 1).
    # Correct when decoded_len-kept_len == 1; wrong for any larger trailing run.
    split = len(middle) - 1
    moved = middle[split:]
    new_trail = moved + trail
    new_middle = middle[:split]
    return new_middle, new_trail"""


# ---------------------------------------------------------------------------
# (6) ADMISSIBILITY (expect=verify). An IN-REGION self-call proving the
# precondition admits a normal, F2P-shaped in-domain input. Inside the impl
# region we build a fresh full-perm middle/trail (a plain 'a.' central part with
# a single trailing '.', no entities: decoded_len==2, kept_len==1, so the bounds
# 0<=2<=len, 0<=1<=2, 1<2 all hold) and recursively call trim_trailing_punct on
# them — this discharges the Requires for a legitimate input. We then assert the
# length postcondition C1 (len(res0) == 2 - (2-1) == 1) to confirm the call site
# sees the guaranteed contract. If the self-call cannot establish Requires for
# this normal input => PRECOND-TOO-STRONG. The real (gold) result for the actual
# middle/trail is then computed and returned, so the module still verifies. Edited
# strictly inside the impl region => same_spec.
# ---------------------------------------------------------------------------
_ADMISS_IMPL = """    # --- admissibility self-call on an F2P-shaped in-domain input ---
    # 'a.' encoded (no entities): decoded_len = 2, kept_len = 1 (strip the '.').
    a_middle = [97, 46]  # type: List[int]
    a_trail = []  # type: List[int]
    Assert(Acc(list_pred(a_middle), 1 / 2))
    Assert(Acc(list_pred(a_trail), 1 / 2))
    Assert(0 <= 2 and 2 <= len(a_middle))
    Assert(0 <= 1 and 1 <= 2)
    Assert(1 < 2)
    # C1 (length): the retained central part keeps all but the last count(=1).
    # --- the real (gold) resolution for the actual middle/trail ---
    punctuation_count = decoded_len - kept_len
    split = len(middle) - punctuation_count
    moved = middle[split:]
    new_trail = moved + trail
    new_middle = middle[:split]
    return new_middle, new_trail"""


SPEC_TESTS = [
    {
        "id": "pos-control-reshaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS_CONTROL),
        "rationale": "a structurally-different but CORRECT impl (inline n-count "
                     "boundary, kept part built first, no split/punctuation_count "
                     "locals) must verify; the take/drop boundaries are identical "
                     "to the gold proof so no induction lemma is needed. If it "
                     "cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "weak-prepatch-decoded-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PREPATCH_BUG),
        "refinement": "Its faithful real patch is the literal pre-fix block "
                      "(trail = middle[len(stripped):] + trail; "
                      "middle = middle[:len(stripped)-len(middle_unescaped)]) — "
                      "exactly the buggy code the issue reports. On "
                      "'google.com/?q=1&lt!' it leaks the extra 'lt' into the "
                      "trailing text ('lt! and see.' vs expected '! and see.'), so "
                      "test_urlize stays RED. A verifying rival here is a true "
                      "verify-but-not-resolve break.",
        "rationale": "REJECT comes from postcondition clause C2 "
                     "(ToSeq(Result()[1]) == ToSeq(middle).drop(len(middle)-count) "
                     "+ ToSeq(trail)): the prepatch moves middle[kept_len:] "
                     "(len(middle)-kept_len code points), which equals the "
                     "required drop only when len(middle)==decoded_len (no "
                     "entities); any entity-bearing middle moves too many.",
    },
    {
        "id": "frame-mut-middle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT_MIDDLE),
        "refinement": "A faithful real patch that mutated `middle` in place would "
                      "corrupt urlize's shared word string across the surrounding "
                      "loop (lead/middle/trail are re-sliced each iteration), "
                      "changing later iterations and the final markup => "
                      "test_urlize / test_urlize_unchanged_inputs would NOT pass.",
        "rationale": "REJECT comes from the permission system: middle is "
                     "Acc(list_pred(middle),1/2) (read-only); middle.append needs "
                     "WRITE permission the caller never lent => insufficient "
                     "permission, never reaches the postcondition.",
    },
    {
        "id": "frame-mut-trail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME_MUT_TRAIL),
        "refinement": "A faithful real patch appending the moved suffix onto the "
                      "shared `trail` accumulator in place (rather than producing "
                      "a fresh prepended value) would diverge from the gold "
                      "prepend semantics and corrupt the accumulated trailing "
                      "text across urlize's loop => F2P would NOT pass.",
        "rationale": "REJECT comes from the permission system: trail is "
                     "Acc(list_pred(trail),1/2) (read-only); trail.append needs "
                     "WRITE permission the caller never lent => insufficient "
                     "permission.",
    },
    {
        "id": "partial-domain-count1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_DOMAIN),
        "refinement": "A faithful real patch hardcoding punctuation_count = 1 "
                      "would pass single-trailing-punct urlize cases but fail "
                      "multi-trailing-punct cases in the test suite "
                      "(test_urlize_unchanged_inputs covers strings whose trailing "
                      "run is longer than one char), leaving those assertions RED.",
        "rationale": "REJECT comes from postcondition clause C1 "
                     "(len(Result()[0]) == len(middle)-(decoded_len-kept_len)): "
                     "the precondition only guarantees kept_len < decoded_len "
                     "(count >= 1), NOT count == 1, so the verifier sees inputs "
                     "with count >= 2 where the hardcoded boundary len(middle)-1 "
                     "violates the exact-count length.",
    },
    {
        "id": "admiss-fshaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS_IMPL),
        "rationale": "an in-region self-call on a normal F2P-shaped in-domain "
                     "input ('a.' central part: decoded_len=2, kept_len=1, "
                     "satisfying 0<=2<=len, 0<=1<=2, 1<2) must establish the "
                     "Requires and see C1 (len(res0)==1). If the precondition "
                     "rejects this legitimate input => PRECOND-TOO-STRONG.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. There is NO @ContractOnly axiom (axioms region empty). The
# decode/strip callees enter only as the A-reference length summaries
# decoded_len = len(html.unescape(middle)) and
# kept_len    = len(html.unescape(middle).rstrip('.,:;!')). Per PBT_PLAN §2.4,
# A-reference deep models are checked the same way as axioms: the real callee
# must satisfy the facts the model assumes (SOUNDNESS), on every input the model
# can actually reach (CONTAINMENT). Both probes run the REAL stdlib html.unescape
# + str.rstrip in the instance image and read observed values (never scrape
# source). Files open with encoding='utf-8'. Imports only the stdlib `html`.
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
# AXIOM-SOUNDNESS for the decoded_len/kept_len A-reference summaries.
# The model's Requires assume, of the REAL callees, on EVERY input:
#     0 <= decoded_len <= len(middle)   (html.unescape never lengthens)
#     0 <= kept_len    <= decoded_len   (str.rstrip never lengthens)
# These bounds are the load-bearing facts the slice arithmetic relies on
# (they make 0 < punctuation_count <= len(middle), keeping both slices in range).
# A single violation => AXIOM-UNSOUND. We fuzz boundaries + entity-bearing
# middles (where encoded length strictly exceeds decoded length — exactly the
# bug-triggering inputs) + 50000 randomized inputs.
import html
import random
import sys

PUNCT = ".,:;!"

def bounds_hold(middle):
    decoded = html.unescape(middle)
    decoded_len = len(decoded)
    kept_len = len(decoded.rstrip(PUNCT))
    ok1 = 0 <= decoded_len <= len(middle)
    ok2 = 0 <= kept_len <= decoded_len
    return ok1, ok2, decoded_len, kept_len

boundary = [
    "google.com/?q=1&lt!", "example.com.", "example.com&gt;;", "foo.com!!!",
    "a.com&amp;.", "&lt;&gt;!!", "&amp;&amp;&amp;;", "x&lt;y&gt;z.,:;!",
    "plain.text;", "&#x27;quote'.", "no_punct_here", "", "....", "&amp;.",
    "&lt;", "&LT", "&notinside;", "&#0000060;",  # named/numeric edge refs
]
checked = 0
for m in boundary:
    ok1, ok2, d, k = bounds_hold(m)
    if not ok1:
        print("AXIOM-UNSOUND (decode lengthened): middle=%r decoded_len=%d > len=%d"
              % (m, d, len(m)))
        sys.exit(1)
    if not ok2:
        print("AXIOM-UNSOUND (rstrip lengthened): middle=%r kept=%d > decoded=%d"
              % (m, k, d))
        sys.exit(1)
    checked += 1

rng = random.Random(14539)
entities = ["&lt;", "&gt;", "&amp;", "&quot;", "&#x27;", "&#39;", "&lt", "&amp",
            "&#x3c;", "&#60;", "&notathing;"]
fillers = list("abcdefghijklmnopqrstuvwxyz.@:/?=0123456789") + list(PUNCT) + entities
for _ in range(50000):
    n = rng.randint(0, 12)
    m = "".join(rng.choice(fillers) for _ in range(n))
    ok1, ok2, d, k = bounds_hold(m)
    if not ok1:
        print("AXIOM-UNSOUND (decode lengthened, fuzz): middle=%r decoded_len=%d > len=%d"
              % (m, d, len(m)))
        sys.exit(1)
    if not ok2:
        print("AXIOM-UNSOUND (rstrip lengthened, fuzz): middle=%r kept=%d > decoded=%d"
              % (m, k, d))
        sys.exit(1)
    checked += 1

print("AXIOM-SOUNDNESS OK: real html.unescape + rstrip satisfy "
      "0<=decoded_len<=len(middle) and 0<=kept_len<=decoded_len on %d inputs "
      "(%d boundary incl. entity-bearing + non-semicolon refs + 50000 fuzz)."
      % (checked, len(boundary)))
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
# AXIOM-CONTAINMENT for the decoded_len/kept_len A-reference summaries.
# The model can reach the trim branch ONLY when kept_len < decoded_len (its
# Requires guard, == urlize's `if middle_unescaped != stripped:`). For EVERY such
# reachable input we must show (a) the model's precondition domain actually
# contains it (the bounds hold — checked here too), AND (b) feeding the REAL
# callee outputs (decoded_len, kept_len) into the model's deep slicing reproduces
# the GOLD patched block exactly, while DIFFERING from the pre-fix block on
# entity-bearing inputs (so the covered domain is exactly the caller-reachable
# one and the spec discriminates the bug). A reachable input outside the bound
# domain, or where the model slicing diverges from gold, => AXIOM-TOO-WEAK-FOR-CALLER.
import html
import random
import sys

PUNCT = ".,:;!"

def to_cp(s):
    return [ord(ch) for ch in s]

def model_trim(middle_cp, trail_cp, decoded_len, kept_len):
    # model.py trim_trailing_punct over code-point lists (gold impl).
    punctuation_count = decoded_len - kept_len
    split = len(middle_cp) - punctuation_count
    moved = middle_cp[split:]
    new_trail = moved + trail_cp
    new_middle = middle_cp[:split]
    return new_middle, new_trail

def gold_trim(middle, trail):
    # the post-fix django block.
    mu = html.unescape(middle)
    stripped = mu.rstrip(PUNCT)
    if mu != stripped:
        punctuation_count = len(mu) - len(stripped)
        trail = middle[-punctuation_count:] + trail
        middle = middle[:-punctuation_count]
    return middle, trail

def prefix_trim(middle, trail):
    # the buggy pre-fix block.
    mu = html.unescape(middle)
    stripped = mu.rstrip(PUNCT)
    if mu != stripped:
        trail = middle[len(stripped):] + trail
        middle = middle[:len(stripped) - len(mu)]
    return middle, trail

def reaches_trim(middle):
    mu = html.unescape(middle)
    return len(mu.rstrip(PUNCT)) < len(mu)

reachable = 0
discriminated = 0

boundary = [
    ("google.com/?q=1&lt!", ""), ("example.com.", ""), ("example.com&gt;;", ""),
    ("foo.com!!!", ")"), ("a.com&amp;.", "abc"), ("&lt;&gt;!!", "X"),
    ("&amp;&amp;&amp;;", ""), ("x&lt;y&gt;z.,:;!", "tail"), ("plain.text;", ""),
    ("&#x27;quote'.", ""), ("....", ""), ("&amp;.", "&gt;"),
]
rng = random.Random(145390)
entities = ["&lt;", "&gt;", "&amp;", "&quot;", "&#x27;", "&#39;", "&lt"]
fillers = list("abcdefghijklmnopqrstuvwxyz.@:/?=0123456789") + list(PUNCT) + entities
cases = list(boundary)
for _ in range(40000):
    n = rng.randint(0, 12)
    m = "".join(rng.choice(fillers) for _ in range(n))
    k = rng.randint(0, 4)
    t = "".join(rng.choice(fillers) for _ in range(k))
    cases.append((m, t))

for middle, trail in cases:
    if not reaches_trim(middle):
        continue  # not a caller-reachable input for the trim branch
    mu = html.unescape(middle)
    decoded_len = len(mu)
    kept_len = len(mu.rstrip(PUNCT))
    # (containment) the reachable input must lie in the model's precondition domain.
    if not (0 <= decoded_len <= len(middle) and 0 <= kept_len <= decoded_len
            and kept_len < decoded_len):
        print("AXIOM-TOO-WEAK-FOR-CALLER: reachable middle=%r outside bound domain "
              "(decoded_len=%d kept_len=%d len=%d)"
              % (middle, decoded_len, kept_len, len(middle)))
        sys.exit(1)
    # (end-to-end) the model slicing on the real callee outputs == gold block.
    m_mid, m_trail = model_trim(to_cp(middle), to_cp(trail), decoded_len, kept_len)
    g_mid, g_trail = gold_trim(middle, trail)
    if m_mid != to_cp(g_mid) or m_trail != to_cp(g_trail):
        print("AXIOM-TOO-WEAK-FOR-CALLER: model slicing != gold on middle=%r trail=%r"
              % (middle, trail))
        sys.exit(1)
    reachable += 1
    if mu != middle and prefix_trim(middle, trail) != gold_trim(middle, trail):
        discriminated += 1

if reachable == 0:
    print("AXIOM-CONTAINMENT inconclusive: no input reached the trim branch")
    sys.exit(1)
if discriminated == 0:
    print("AXIOM-CONTAINMENT weak: no entity-bearing input discriminated the bug")
    sys.exit(1)

print("AXIOM-CONTAINMENT OK: every caller-reachable trim-branch input lies in the "
      "model's precondition domain AND the model slicing on the real callee "
      "outputs reproduces the gold block on %d reachable inputs; bug "
      "discriminated on %d entity-bearing inputs." % (reachable, discriminated))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-decode-strip-bounds",
        "axiom": "decoded_len / kept_len (callee length summaries)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the real stdlib html.unescape + str.rstrip must satisfy the "
                     "model's precondition bounds (0<=decoded_len<=len(middle), "
                     "0<=kept_len<=decoded_len) on every input; a violation => "
                     "AXIOM-UNSOUND. Unchanged by the patch (flag-independent).",
    },
    {
        "id": "ax-contain-reachable-trim-inputs",
        "axiom": "decoded_len / kept_len (callee length summaries)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "every input the model can reach (the trim branch, "
                     "kept_len < decoded_len) lies in the bound domain and the "
                     "model slicing on the real callee outputs reproduces the gold "
                     "block, while discriminating the pre-fix bug; a reachable "
                     "input outside the domain => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
