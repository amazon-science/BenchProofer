# properties.py — PBT falsification battery for django__django-9296.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant that shares the FROZEN spec (only the
# impl region — body + nested invariants — differs; guaranteed by region surgery
# below) and is checked by Nagini verify + markers.same_spec. AXIOM_TESTS probe
# the real callee in Docker.
#
# Defended surface (django__django-9296, Paginator.__iter__):
#   paginate_iter(page_numbers: List[int]) -> List[int]
#     Requires/Ensures Acc(list_pred(page_numbers), 1/2)   <- READ-ONLY input
#     Ensures Acc(list_pred(Result()))
#     Ensures ToSeq(Result()) == mapped(ToSeq(page_numbers))   <- LOAD-BEARING
#   mapped(s): @Pure front-recursive fold = PSeq(page_lookup(s[0])) + mapped(s.drop(1))
#   page_lookup(n): @Pure @ContractOnly, Ensures(True)  (opaque pure fn of n)
#
# The load-bearing postcondition pins, for every valid input: (count) one item
# per page number; (order) item k is page_lookup of page number k; (value) each
# item is page_lookup of THAT page number; (empty) [] -> []. The oracle `mapped`
# is GROUNDED in the input (a fully-unfolded fold over ToSeq(page_numbers)), not
# an opaque answer-key — see 'ungrounded-oracle' note in the StructuredOutput
# assessment; there is no wrong echo to build, so #2 is a positive control here.
from pathlib import Path

INSTANCE = "django__django-9296"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The full impl region of the frozen model (body + nested invariants). Every
# variant below edits ONLY text inside this region, so spec_view (and hence
# markers.same_spec) is preserved verbatim.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    result = []  # type: List[int]
    i = len(page_numbers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(page_numbers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(page_numbers))
        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        x = page_numbers[i - 1]
        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
        result = [page_lookup(x)] + result
        i = i - 1
    return result"""

# Sanity: the frozen model must contain this region verbatim (else drift).
assert _GOLD_IMPL in _BASE, "frozen impl region drifted from _GOLD_IMPL"


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY — page_numbers is read-only, Acc(...,1/2)).
#    A rival that WRITES to the read-only input to (re)establish the result.
#    Must REJECT for insufficient permission: the loop holds only Acc(...,1/2)
#    so a store/append to page_numbers is unprovable.  Gold invariants/asserts
#    kept verbatim so the rejection is attributable to the write.
# ===========================================================================
_FRAME_MUT = _swap(
    _BASE, _GOLD_IMPL,
    """    result = []  # type: List[int]
    i = len(page_numbers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(page_numbers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(page_numbers))
        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        x = page_numbers[i - 1]
        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
        result = [page_lookup(x)] + result
        page_numbers[i - 1] = x  # WRITE to the read-only input (needs full perm)
        i = i - 1
    return result""")


# ===========================================================================
# 2. FRAME-MUTATION variant — append to the read-only input (grows it).
#    Also needs full list_pred permission; rejected for insufficient perm.
# ===========================================================================
_FRAME_APPEND = _swap(
    _BASE, _GOLD_IMPL,
    """    result = []  # type: List[int]
    page_numbers.append(0)  # WRITE (append) to the read-only input
    i = len(page_numbers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(page_numbers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(page_numbers))
        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        x = page_numbers[i - 1]
        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
        result = [page_lookup(x)] + result
        i = i - 1
    return result""")


# ===========================================================================
# 3. PARTIAL-DOMAIN — off-by-one: stop the backward loop at i > 1, dropping the
#    final prepend (page_lookup of page_numbers[0], i.e. the FIRST item of the
#    in-order image). Correct on the empty/one-page sub-domain only; for any
#    run of >= 2 page numbers it drops the first page. Must REJECT.
# ===========================================================================
_DROP_FIRST = _swap(_BASE, "    while i > 0:", "    while i > 1:")


# ===========================================================================
# 4. PARTIAL-DOMAIN / value — index the page accessor by the LOOP COUNTER (i)
#    instead of the PAGE NUMBER value (x = page_numbers[i-1]). On a run equal to
#    [1..n] (which page_range always is) these coincide, so it would pass the
#    F2P; but the modeled domain is an arbitrary List[int], and the postcondition
#    pins page_lookup(s[k]) of the VALUE. Must REJECT (else SPEC-TOO-WEAK: a
#    faithful patch yielding self.page(loop_counter) instead of
#    self.page(page_number) is a distinct, generally-incorrect traversal).
# ===========================================================================
_INDEX_NOT_VALUE = _swap(
    _BASE,
    "        result = [page_lookup(x)] + result\n        i = i - 1",
    "        result = [page_lookup(i)] + result\n        i = i - 1")


# ===========================================================================
# 5. ORDER — build the result back-to-front by APPENDING (reverses the order).
#    Same count, same multiset of values, but the order-preservation clause
#    (item k is page_lookup of page number k) fails for any run with >= 2
#    distinct images. Must REJECT.
# ===========================================================================
_REVERSED = _swap(
    _BASE,
    "        result = [page_lookup(x)] + result\n        i = i - 1",
    "        result = result + [page_lookup(x)]\n        i = i - 1")


# ===========================================================================
# 6. POSITIVE CONTROL (soundness) — structurally-different but CORRECT.
#    Local-variable reshape: hoist the page index into `j` and the per-step
#    image into a one-element list `head`, then prepend. Same backward
#    direction (so NO f(a+b)=f(a)+f(b) lemma is needed — directive 3), same
#    front-recursive unfold, gold invariants + framing asserts kept verbatim.
#    Must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_CONTROL = _swap(
    _BASE, _GOLD_IMPL,
    """    result = []  # type: List[int]
    i = len(page_numbers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(page_numbers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(page_numbers))
        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        j = i - 1
        x = page_numbers[j]
        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
        head = [page_lookup(x)]  # type: List[int]
        result = head + result
        i = i - 1
    return result""")


# ===========================================================================
# 7. ADMISSIBILITY — a self-call confirming the precondition admits a normal
#    F2P-shaped input. A fresh caller builds a small List[int], asserts the
#    Acc(...,1/2) precondition can be established (passing the list to
#    paginate_iter), and reads back the ensured permission + that the result is
#    well-formed. Must VERIFY (else PRECOND-TOO-STRONG).
#    Implemented inside the impl region: after the gold loop, do a self-call on
#    a freshly-constructed list so the precondition is exercised on a concrete
#    in-domain input. (The fresh list has full permission, of which 1/2 is lent
#    to the call — exactly the read-only protocol.)
# ===========================================================================
_ADMISS = _swap(
    _BASE, "    return result\n    # impl-end",
    """    probe = [1, 2, 3]  # type: List[int]
    Assert(Acc(list_pred(probe), 1 / 2))   # the lent half-permission returns
    return result
    # impl-end""")


SPEC_TESTS = [
    {
        "id": "frame-mutation-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": (
            "A faithful real patch behind this rival WRITES the page-number run "
            "while traversing (e.g. self.page_range is consumed/mutated). The gold "
            "__iter__ is a read-only generator over self.page_range; a version that "
            "stores back into the page-number sequence is not the gold patch and "
            "would corrupt the shared, reused page_range (PASS_TO_PASS "
            "test_page_range_iterator / test_page_indexes re-read page_range), so it "
            "would NOT resolve. It also produces the same values here, so the ONLY "
            "thing rejecting it is the permission system."),
        "rationale": (
            "page_numbers is read-only: Requires/Invariant hold only "
            "Acc(list_pred(page_numbers), 1/2). A store `page_numbers[i-1] = x` "
            "needs full list_pred permission => unprovable => Nagini rejects for "
            "insufficient permission. Rejection source: the fractional-permission "
            "frame condition, not any value clause."),
    },
    {
        "id": "frame-mutation-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_APPEND,
        "refinement": (
            "A faithful patch that appends to the page-number run before traversing "
            "mutates the shared self.page_range and changes how many pages exist; "
            "the gold __iter__ adds nothing and never mutates page_range, so this is "
            "a different behaviour that would break PASS_TO_PASS page_range/index "
            "tests and not resolve."),
        "rationale": (
            "page_numbers.append(0) needs full list_pred permission; the impl holds "
            "only Acc(...,1/2) (Requires + Invariant). Rejected for insufficient "
            "permission. Supporting frame-mutation case (mutation-by-grow)."),
    },
    {
        "id": "partial-domain-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_FIRST,
        "refinement": (
            "The faithful patch is `for n in self.page_range[1:]: yield self.page(n)` "
            "(or a loop that stops one short) — it OMITS page 1 of every multi-page "
            "collection. The F2P Paginator([1,2,3],2) must yield [1,2] then [3]; this "
            "drops the first page entirely, so list(iter(paginator)) != expected and "
            "the F2P fails. It would NOT resolve."),
        "rationale": (
            "Backward loop `while i > 1` never performs the i==1 iteration that "
            "prepends page_lookup(page_numbers[0]) — the first item of the in-order "
            "image. For len(page_numbers) >= 1 (non-empty run) ToSeq(result) is "
            "missing its head, so ToSeq(Result()) == mapped(ToSeq(page_numbers)) "
            "fails. Rejection source: the load-bearing postcondition equality "
            "(count + leading element)."),
    },
    {
        "id": "partial-domain-index-not-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _INDEX_NOT_VALUE,
        "refinement": (
            "The faithful patch yields self.page(loop_counter) instead of "
            "self.page(page_number) — i.e. it pages by the iteration index, not the "
            "page-number value. These coincide only because page_range happens to be "
            "[1..n]; on the modeled domain (an arbitrary List[int] page-number run) "
            "they differ. It is a distinct, generally-incorrect traversal; a verifying "
            "rival here would be a true verify-not-resolve gap (SPEC-TOO-WEAK), so the "
            "spec must reject it."),
        "rationale": (
            "The postcondition pins page_lookup(s[k]) of the page-number VALUE at "
            "position k (mapped front-recurses on s[0]). Using page_lookup(i) (the "
            "loop counter) is provably unequal to page_lookup(page_numbers[i-1]) for "
            "an arbitrary input, since page_lookup is opaque (no relation between "
            "page_lookup(i) and page_lookup(x) when i != x). Rejection source: the "
            "postcondition value clause via the opaque page_lookup axiom."),
    },
    {
        "id": "order-reversed-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REVERSED,
        "refinement": (
            "The faithful patch yields the pages in REVERSE page-range order "
            "(`for n in reversed(self.page_range): yield self.page(n)`). The F2P "
            "expects page 1 ([1,2]) BEFORE page 2 ([3]); reversed yields [3] then "
            "[1,2], so the F2P assertion fails. It would NOT resolve."),
        "rationale": (
            "Appending in a backward loop builds the list in reverse page-number "
            "order; ToSeq(result) is the reverse of mapped(ToSeq(page_numbers)) for "
            "any run with >= 2 distinct images, violating ToSeq(Result()) == "
            "mapped(...). Rejection source: the order-preservation half of the "
            "postcondition equality."),
    },
    {
        "id": "pos-control-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "A structurally-different but CORRECT impl (local-variable reshape: index "
            "via `j = i-1`, build the per-step image as a one-element list `head` "
            "then prepend). Same backward direction and same front-recursive unfold, "
            "so NO f(a+b)=f(a)+f(b) lemma is needed (directive 3); the gold loop "
            "invariants and the two framing asserts are kept verbatim (directive 2). "
            "Must verify, else the postcondition is SPEC-TOO-STRONG."),
    },
    {
        "id": "admissibility-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "After the gold loop, a concrete F2P-shaped List[int] [1,2,3] "
            "establishes the precondition Acc(probe,1/2): a freshly built list owns "
            "full list_pred, so lending a 1/2 share is admissible. The clause is "
            "asserted AT the witness rather than exercised by a self-call, because "
            "the model carries Requires(MustTerminate(2)) with "
            "Invariant(MustTerminate(i + 1)) on the loop and a same-level self-call "
            "on a non-shrinking argument is an obligation leak Nagini is right to "
            "refuse. If this fails to verify, the precondition rejects a normal "
            "input (PRECOND-TOO-STRONG). NEGATIVE CONTROL: THERE IS NONE, and that "
            "is a fact about this precondition rather than about the probe. "
            "paginate_iter's only frozen clause is Acc(list_pred(page_numbers), "
            "1 / 2), and no VALUE violates a permission clause: measured, the same "
            "assert at probe = [] still reports `Verification successful`. So this "
            "case checks permission admissibility (a caller can lend the half share "
            "the spec demands) plus the fact that the gold body after it verifies "
            "under the obligation; it does NOT pin a value domain, and must not be "
            "read as strong as a case whose precondition carries a length or "
            "element-domain clause a witness can leave."),
    },
]


# ===========================================================================
# AXIOM LANE
# The bundle has ONE @ContractOnly axiom (page_lookup) and ONE A-reference deep
# model (mapped). page_lookup's contract is Ensures(True) — the weakest possible
# obligation: it claims ONLY that page(n) is a well-defined PURE function of the
# page number n (deterministic in n for a fixed collection). axiom-soundness
# therefore = "page(n) is deterministic in n"; there is no value claim to fuzz.
# The A-reference obligation (real __iter__ == [page(n) for n in page_range]) is
# also probed.  axiom-containment: the model can pass page_lookup ONLY page-
# number values drawn from ToSeq(page_numbers) (the run elements); these are
# exactly the n in page_range, all in page_lookup's domain (every int) — covered.
#
# Both probes EXECUTE the real django.core.paginator.Paginator (directive 4: call
# the callee, never scrape source) and read its observed values. The bundle's
# axiom_check.py is the ground truth; its logic is embedded below so the probe is
# self-contained (directive 6: only /work is mounted in-container). Files opened
# with encoding="utf-8" is moot here (no file reads), but stdlib-only is honoured.
# ===========================================================================

_AX_SOUND_PROBE = r'''
import itertools, sys
from django.core.paginator import Paginator

def sig(page):
    return (page.number, list(page.object_list))

def check(object_list, per_page, orphans, allow):
    p = Paginator(object_list, per_page, orphans=orphans, allow_empty_first_page=allow)
    nums = list(p.page_range)
    # (A-consumed) page_lookup soundness: page(n) is a deterministic PURE fn of n
    # (the ONLY property the axiom Ensures(True) needs). Observe twice, also after
    # an unrelated read, and require equality.
    for n in nums:
        a = sig(p.page(n))
        _ = p.page(nums[-1]) if nums else None  # interleave an unrelated lookup
        b = sig(p.page(n))
        if a != b:
            print("AXIOM-UNSOUND: page(%r) not deterministic on (len=%d,pp=%d,orph=%d,allow=%r): %r vs %r"
                  % (n, len(object_list), per_page, orphans, allow, a, b))
            sys.exit(1)
    return len(nums)

f2p = Paginator([1, 2, 3], 2)
if [list(pg) for pg in f2p] != [[1, 2], [3]]:
    print("AXIOM-UNSOUND: F2P witness Paginator([1,2,3],2) did not yield [[1,2],[3]]")
    sys.exit(1)

checked = 0
lengths = [0, 1, 2, 3, 4, 5, 7, 10, 11, 20, 23, 50]
per_pages = [1, 2, 3, 5, 7, 10]
orphans_opts = [0, 1, 2, 3, 5]
allow_opts = [True, False]
for length, pp, orph, allow in itertools.product(lengths, per_pages, orphans_opts, allow_opts):
    if orph >= pp:
        continue
    checked += check(list(range(length)), pp, orph, allow)
print("AXIOM-SOUND: page_lookup deterministic in n over %d configs (incl. F2P witness)" % checked)
sys.exit(0)
'''

_AX_REFERENCE_PROBE = r'''
import itertools, sys
from django.core.paginator import Paginator

def sig(page):
    return (page.number, list(page.object_list))

def check(object_list, per_page, orphans, allow):
    p = Paginator(object_list, per_page, orphans=orphans, allow_empty_first_page=allow)
    nums = list(p.page_range)
    # (A-reference) the deep model mapped(page_range) == real __iter__:
    # iterating the collection yields exactly page(n) for n in page_range, in order.
    expected = [sig(p.page(n)) for n in nums]
    observed = [sig(pg) for pg in p]
    if observed != expected:
        print("A-REF-MISMATCH: __iter__ != [page(n) for n in page_range] on (len=%d,pp=%d,orph=%d,allow=%r): %r vs %r"
              % (len(object_list), per_page, orphans, allow, observed, expected))
        sys.exit(1)
    # containment: the visited page numbers are EXACTLY page_range, in order — so
    # every n the model can feed page_lookup is an in-range page number (covered).
    if [num for (num, _) in observed] != nums:
        print("A-REF-MISMATCH: visited page numbers != page_range on (len=%d): %r vs %r"
              % (len(object_list), [num for (num, _) in observed], nums))
        sys.exit(1)
    return len(nums)

f2p = Paginator([1, 2, 3], 2)
if [list(pg) for pg in f2p] != [[1, 2], [3]]:
    print("A-REF-MISMATCH: F2P witness Paginator([1,2,3],2) did not yield [[1,2],[3]]")
    sys.exit(1)

checked = 0
lengths = [0, 1, 2, 3, 4, 5, 7, 10, 11, 20, 23, 50]
per_pages = [1, 2, 3, 5, 7, 10]
orphans_opts = [0, 1, 2, 3, 5]
allow_opts = [True, False]
for length, pp, orph, allow in itertools.product(lengths, per_pages, orphans_opts, allow_opts):
    if orph >= pp:
        continue
    checked += check(list(range(length)), pp, orph, allow)
print("A-REF-COVERED: mapped(page_range)==real __iter__ and visited nums==page_range over %d configs" % checked)
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-page_lookup",
        "axiom": "page_lookup",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "page_lookup's contract is Ensures(True): the only obligation is that "
            "page(n) is a well-defined PURE function of n (deterministic in n for a "
            "fixed collection). The probe EXECUTES the real Paginator.page(n) twice "
            "(interleaving an unrelated lookup) across 480 configs incl. the F2P "
            "witness and empty/single-page/orphan boundaries; any non-determinism is "
            "AXIOM-UNSOUND. No flag dependence (mapping.md §3.2: default args, no "
            "keyword affects the order-and-image property)."),
    },
    {
        "id": "ax-reference-mapped",
        "axiom": "mapped",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_REFERENCE_PROBE,
        "rationale": (
            "mapped is an A-reference deep model of the changed traversal. The probe "
            "EXECUTES the real Paginator.__iter__ and asserts it equals [page(n) for "
            "n in page_range] page-for-page (number + content), and that the visited "
            "page numbers are EXACTLY page_range. This both validates the deep model "
            "== real callee AND establishes containment: the model feeds page_lookup "
            "only the page numbers in the run (= page_range elements), all in "
            "page_lookup's domain. A reachable input outside the covered domain would "
            "be AXIOM-TOO-WEAK-FOR-CALLER; none exists."),
    },
]
