# properties.py — PBT falsification battery for django__django-14053.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py variant built by region-surgery — we edit
# ONLY text inside the `# impl-start` / `# impl-end` region of the frozen
# model.py, so `markers.same_spec(base, module)` is guaranteed True and any
# verify/reject outcome is attributable to the impl alone, never a spec change.
#
# Defended surface (see model.py / refinement.md / mapping.md):
#   collect_reports(ids, adj, err) abstracts HashedFilesMixin.post_process. All
#   three inputs are READ-ONLY: Requires/Ensures/Invariant carry
#   Acc(list_pred(ids), 1/2), Acc(list_pred(adj), 1/2) and
#   Acc(list_pred(err), 1/2) — half permission (directive 5). The load-bearing
#   postconditions are:
#     (1) ToSeq(Result()) == reported(ToSeq(ids), ToSeq(adj), ToSeq(err))
#         — the exact reported sequence: the FIRST-PASS segment (every plain id,
#         plus every adjustable id whose examination fails, once each, in
#         enumeration order) followed by the SETTLED segment (every adjustable
#         id, once each, same order). This pins BOTH observables at once: the
#         multiplicity of a settled report (the F2P property) AND the position of
#         a failure report (the P2P property — a failure must reach the caller as
#         the first pass gets to it, never deferred to the end and never
#         displaced by the same file's later settled report);
#     (2) len(Result()) == len(ids) + failing_adj_count(...) — count == #files
#         plus one per failing adjustable file. On the no-failure sub-domain this
#         is exactly the F2P property
#         assertCountEqual(post_processed, set(post_processed)); with a failure
#         present it additionally forbids swallowing the failure report.
#   `reported` is a @Pure helper but it is GROUNDED: a fully-unfolded function of
#   the inputs (first_pass_ids ++ adj_ids), not an opaque answer-key oracle. So
#   there is no ECHO lane to author here: "echo the oracle" IS the correct answer,
#   and materialising it into the returned list is exactly the work the impl has
#   to do. No case below is an echo probe and none is labelled one.
#
# WHICH REJECT CASES ARE LEGITIMATE HERE (the reject lane is narrow by
# construction, and pretending otherwise would be the forgery this manifest is
# supposed to prevent):
#   * In the SETTLED dimension the hidden F2P checks (a) no duplicate name in
#     stats['post_processed'] and (b) membership of specific names. It does NOT
#     check the yield ORDER of two distinct names. So a rival that merely permutes
#     order among settled reports WOULD resolve, and we do NOT submit a
#     settled-order swap as a uniqueness break: it is a verify⇒resolve artifact,
#     not a defect. Legitimate breaks here duplicate a report or drop one.
#   * In the FAILURE dimension the caller stops at the FIRST failure report it
#     sees (`raise processed`, collectstatic.py:134), and the hidden P2P fixture
#     for the failure path is a SINGLE-file collection. So the only thing those
#     tests can observe about a failure is whether ANY failure report reaches the
#     caller. A rival that reports the failure at the wrong position, or twice,
#     would still resolve — so we do NOT submit one. Legitimate breaks here are
#     exactly the ones under which NO failure report reaches the caller for a
#     collection whose file fails: the failure is swallowed by that file's own
#     settled report, or erased before the routing test can see it, or the
#     first-pass segment is dropped wholesale on the singleton boundary.
# The spec's postcondition (1) is nevertheless a TOTAL equation on the reported
# sequence — it pins position and multiplicity too, because that is what the real
# patched routine does (mapping.md §2, refinement.md A2/A5). Being stronger than
# the hidden tests can observe is sound for `verify => correct`; what would NOT be
# sound is claiming a reject case is a real defect when its faithful patch
# resolves. Every reject case below therefore carries a refinement argument that
# its faithful real patch would NOT resolve, and each of those arguments names the
# hidden assertion it breaks.

from pathlib import Path

INSTANCE = "django__django-14053"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (each unique in model.py). Editing only these
# keeps the frozen spec byte-identical (same_spec True).
# ---------------------------------------------------------------------------

# The gold routing block: report-now (plain OR failing) and collect-for-settled
# (adjustable). The two tests are INDEPENDENT — an adjustable file whose
# examination fails takes both.
_GOLD_ROUTE = (
    "        if fa == 0 or fe != 0:\n"
    "            # Plain files, and any failing examination, go straight to the\n"
    "            # caller at this position in the enumeration.\n"
    "            first = [fid] + first\n"
    "        if fa != 0:\n"
    "            # Adjustable files are revisited across the internal passes but are\n"
    "            # collected, keyed by file, so each is held only once; they are\n"
    "            # reported at the end with their final outcome.\n"
    "            collected = [fid] + collected\n"
)

# The first-pass report test on its own (the failure disjunct lives here).
_GOLD_REPORT_NOW = "        if fa == 0 or fe != 0:\n"

# The gold concatenation (first-pass segment, then settled segment).
_GOLD_CONCAT = "    result = first + collected\n"

# The gold lemma assertion just before return.
_GOLD_LEMMA = (
    "    Assert(lemma_split_len(ToSeq(ids), ToSeq(adj), ToSeq(err)))\n"
    "    return result\n"
)

# The accumulator declarations at the top of the impl region.
_GOLD_HEAD = (
    "    first = []  # type: List[int]\n"
    "    collected = []  # type: List[int]\n"
)

# The gold loop's value invariants — the pair that establishes postcondition (1).
_GOLD_VALUE_INVARIANTS = (
    "        Invariant(ToSeq(first) == first_pass_ids(\n"
    "            ToSeq(ids).drop(i), ToSeq(adj).drop(i), ToSeq(err).drop(i)))\n"
    "        Invariant(ToSeq(collected) == adj_ids(ToSeq(ids).drop(i), ToSeq(adj).drop(i)))\n"
)


def _require(anchor):
    """Assert an anchor still matches model.py even when no case swaps it, so a
    spec/impl edit that moves it fails at import instead of silently leaving a
    case unbuilt."""
    if _BASE.count(anchor) != 1:
        raise AssertionError(f"drift: anchor not present exactly once: {anchor!r}")
    return anchor


# Anchors asserted but not consumed by a _swap below.
_require(_GOLD_LEMMA)
_require(_GOLD_VALUE_INVARIANTS)


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally different, CORRECT, must verify
# ===========================================================================
# Route-REORDER: test the settled-collection case first and the report-now case
# second. The two tests are independent (not an if/else chain), so swapping them
# is semantically identical; the backward loop, the [fid]+first / [fid]+collected
# front-prepends, every framing Assert, and the front-recursive loop invariants
# are all UNCHANGED, so the gold proof stays valid (no new lemma needed). If a
# faithful correct reshape cannot verify this would be SPEC-TOO-STRONG. We
# deliberately keep the backward/prepend shape (a forward-append would need an
# f(a+b)==f(a)+f(b) lemma the verifier won't auto-discharge against the
# front-recursive @Pure folds — pilot bug #3).
_POS_REORDER = _swap(
    _BASE,
    _GOLD_ROUTE,
    "        if fa != 0:\n"
    "            # Adjustable files are revisited across the internal passes but are\n"
    "            # collected, keyed by file, so each is held only once; they are\n"
    "            # reported at the end with their final outcome.\n"
    "            collected = [fid] + collected\n"
    "        if fa == 0 or fe != 0:\n"
    "            # Plain files, and any failing examination, go straight to the\n"
    "            # caller at this position in the enumeration.\n"
    "            first = [fid] + first\n",
)


# ===========================================================================
# 2. ADMISSIBILITY — the precondition admits a normal F2P/P2P-shaped input
# ===========================================================================
# Add an in-impl Assert deriving facts the Requires must support for a normal
# collection (three aligned non-negative-length streams, half permission
# readable). These follow from the frozen Requires (len(ids)==len(adj),
# len(ids)==len(err); Acc(...,1/2) lets us read len). If the precondition were
# too strong to admit a normal input — in particular if it excluded collections
# that contain a failing file, which is the P2P fixture's shape — this would fail
# to verify (PRECOND-TOO-STRONG). The gold body is otherwise intact.
_ADMISS = _swap(
    _BASE,
    _GOLD_HEAD,
    "    # admissibility: a normal collection (three aligned streams, readable at\n"
    "    # half permission) satisfies the precondition — including one that\n"
    "    # carries a failing examination, so the failure domain is admitted\n"
    "    # rather than excluded.\n"
    "    Assert(len(ids) == len(adj))\n"
    "    Assert(len(ids) == len(err))\n"
    "    Assert(len(ids) >= 0)\n"
    + _GOLD_HEAD,
)


# ===========================================================================
# 3. FRAME-MUTATION (MANDATORY — read-only inputs) — must REJECT (no permission)
# ===========================================================================
# ids, adj and err are all held at HALF permission (read-only). A rival tries to
# satisfy the postcondition by WRITING into the input collection `err` (here:
# overwrite err[0] with 0, i.e. erase the record that a file's examination
# failed). Writing a list element needs FULL permission on list_pred; the caller
# granted only Acc(list_pred(err), 1/2), so the assignment must fail for
# INSUFFICIENT PERMISSION before any postcondition is even reached. The gold
# postconditions/invariants are kept verbatim so the rejection is attributable to
# the write, not to a value mismatch. (This is the project's #1 weakness class; a
# byte-fuzzer never thinks to mutate a read-only input.)
#
# Refinement: the faithful real patch corresponding to this rival would MUTATE the
# input the routine iterates — clearing the per-file failure record so the "report
# it now" test never fires. That is the destructive form of withholding the
# failure: the caller never surfaces it, so post_processing would not indicate the
# origin of the error, and the run would report a settled outcome instead. It
# would not resolve, and the half-permission framing exists to forbid it.
_FRAME_MUT = _swap(
    _BASE,
    _GOLD_HEAD,
    "    # FRAME-MUTATION probe: write to the read-only input (half permission).\n"
    "    if len(err) > 0:\n"
    "        err[0] = 0\n"
    + _GOLD_HEAD,
)


# ===========================================================================
# 4. UNIQUENESS — adjustable file reported TWICE for a settled outcome
# ===========================================================================
# The pre-change shape: a plain file goes to `first`, an adjustable file is BOTH
# reported in the first pass AND collected for the settled segment — so an
# adjustable id appears twice even when nothing failed. This violates
# postcondition (2) (the duplicate makes len > #files + #failing) and
# postcondition (1) (exact sequence). Must REJECT.
#
# Refinement: this is exactly model_prepatch.py's defect and the pre-change
# storage.py behaviour — an adjustable file yielded in the first pass AND again at
# the end. Its faithful real patch is the pre-change code, which is precisely what
# the F2P (assertCountEqual(post_processed, set(post_processed))) FAILS on (a name
# appears twice). It would NOT resolve.
_DUP_ADJ = _swap(
    _BASE,
    _GOLD_ROUTE,
    "        if fa == 0 or fe != 0:\n"
    "            first = [fid] + first\n"
    "        if fa != 0:\n"
    "            # WRONG: report the adjustable file now AND collect it for the\n"
    "            # settled segment (the pre-change multiplicity defect): an\n"
    "            # adjustable file is reported twice for a settled outcome.\n"
    "            first = [fid] + first\n"
    "            collected = [fid] + collected\n",
)


# ===========================================================================
# 5. PARTIAL-DOMAIN — correct except it DROPS the adjustable files (sub-domain)
# ===========================================================================
# Correct on the all-plain sub-domain (collected stays empty -> result == the
# first-pass segment == reported), but on any collection containing an adjustable
# file it omits the settled segment entirely (never appends `collected`). Violates
# postcondition (1) and (2) whenever an adjustable file exists. Must REJECT.
#
# Refinement: the faithful real patch is post_process WITHOUT the final
# `yield from` of the collected adjustable files — they are collected but never
# re-emitted. That drops every adjustable file's name from
# stats['post_processed']; the F2P assertIn(...) for the post-processed css files
# (and the css/window.css membership) would FAIL. It would NOT resolve.
_DROP_ADJ = _swap(
    _BASE,
    _GOLD_CONCAT,
    "    # WRONG (partial-domain): report only the first-pass segment; silently\n"
    "    # drop the collected adjustable files. Correct iff no file is adjustable.\n"
    "    result = first\n",
)


# ===========================================================================
# 6. PARTIAL-DOMAIN (boundary) — drops exactly the FIRST collected adjustable id
# ===========================================================================
# A subtler near-miss: report the first-pass segment, then the adjustable files
# EXCEPT the first one (drop(1) on the collected sub-sequence). Correct on the
# all-plain case, but on any collection with >=1 adjustable file it omits the
# first adjustable id — diverging from reported(...) and from the count only on
# that sub-domain. Must REJECT.
#
# Refinement: the faithful real patch would emit all but the first of the
# collected adjustable files. The dropped file's name never reaches
# stats['post_processed'], so the F2P membership assertions for the
# post-processed css files would FAIL on the multi-adjustable fixture. It would
# NOT resolve.
_DROP_FIRST_ADJ = _swap(
    _BASE,
    _GOLD_CONCAT,
    "    # WRONG (partial-domain, boundary): drop the first collected adjustable\n"
    "    # id. Equals reported(...) only when there are no adjustable files.\n"
    "    tail = collected[1:] if len(collected) > 0 else collected\n"
    "    result = first + tail\n",
)


# ===========================================================================
# 7. WITHHELD FAILURE — the failure report is swallowed by the settled report
# ===========================================================================
# The routing test loses its failure disjunct: only NON-adjustable files are
# reported as the first pass reaches them, so an adjustable file whose
# examination fails is held back with the rest and its failure never reaches the
# caller at all — it is displaced by the same file's later settled report. This is
# correct on every collection in which nothing fails (the sub-domain the
# multiplicity property alone covers) and wrong exactly where a failure exists.
# Must REJECT: `first` can no longer be the first-pass segment the invariant and
# postcondition (1) name, and the reported sequence is short by one entry per
# failing adjustable file (postcondition (2)).
#
# Refinement: the faithful real patch is the gold restructuring with the
# first-pass guard reduced to `name not in adjustable_paths` — the failing triple
# is stored under the file's key instead of being handed on, and the file's later
# settled triple overwrites it, so the caller never sees the failure, never
# re-raises, and records the file as successfully post-processed. That is exactly
# what the P2P test 'post_processing indicates the origin of the error when it
# fails' asserts must not happen (assertRaises + the "Post-processing '...'
# failed!" stderr line). It would NOT resolve.
_WITHHOLD_FAILURE = _swap(
    _BASE,
    _GOLD_REPORT_NOW,
    "        # WRONG: drop the failure disjunct — a failing adjustable file is\n"
    "        # held back instead of being reported as the pass reaches it, so its\n"
    "        # failure is swallowed by its own settled report.\n"
    "        if fa == 0:\n",
)


# ===========================================================================
# 8. BOUNDARY (singleton) — the whole first-pass segment vanishes for one file
# ===========================================================================
# The gold loop and BOTH its value invariants are left verbatim, so `first` really
# is the first-pass segment and `collected` really is the settled segment at the
# end of the loop; only the concatenation is boundary-guarded. On a collection of
# one file the rival returns the settled segment alone. So:
#   * >= 2 files, or 0 files -> identical to gold (correct);
#   * exactly 1 file, adjustable and failing -> reported(...) is [id, id] but the
#     rival returns [id]: the failure report is gone;
#   * exactly 1 plain file  -> reported(...) is [id] but the rival returns [].
# Must REJECT, and — because the invariants are untouched — the rejection lands on
# the POSTCONDITIONS themselves, (1) and (2), not on a proof-shape artefact.
#
# Refinement: the faithful real patch guards the first pass's `yield` on the size
# of the `paths` mapping — for a one-file collection it emits only the final
# `yield from processed_adjustable_paths.values()`. The hidden P2P fixture for the
# failure path is EXACTLY a one-file collection (STATICFILES_DIRS pointed at a
# directory whose only file is the faulty one), so under this patch no failure
# report ever reaches collect(), it never re-raises, and
# `with self.assertRaises(Exception)` in 'post_processing indicates the origin of
# the error when it fails' FAILS — as does the assertion that stderr carries the
# "Post-processing '...' failed!" line. It would NOT resolve. This is the same
# family as case 7 reached from the opposite direction: case 7 withholds the
# failure by narrowing the routing test, this one by discarding the segment the
# routing test fills, and the singleton is where the hidden fixture lives.
_SINGLETON_DROPS_FIRST_PASS = _swap(
    _BASE,
    _GOLD_CONCAT,
    "    # WRONG (boundary, singleton): on a one-file collection return only the\n"
    "    # settled segment, discarding the whole first-pass segment. Identical to\n"
    "    # the correct concatenation for every other collection size.\n"
    "    if len(ids) == 1:\n"
    "        result = collected\n"
    "    else:\n"
    "        result = first + collected\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-route-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the two independent routing "
            "tests are evaluated in the opposite order (collect-for-settled first, "
            "report-now second). The backward loop, the [fid]+first / "
            "[fid]+collected front-prepends, all framing Asserts and the "
            "front-recursive loop invariants are unchanged, so the gold proof still "
            "discharges. Must verify; if not -> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-normal-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "asserts facts a normal collection guarantees (three aligned streams "
            "len(ids)==len(adj)==len(err), non-negative length, readable at half "
            "permission). These follow from the frozen Requires; if they could not "
            "be established the precondition is too strong -> PRECOND-TOO-STRONG. "
            "In particular the precondition admits collections that carry a failing "
            "examination, so the repair pins that behaviour instead of excluding it."
        ),
    },
    {
        "id": "frame-mutation-write-readonly-err",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": (
            "the faithful real patch would mutate the input the routine iterates, "
            "erasing the record that a file's examination failed so the report-now "
            "test never fires. The caller then never surfaces the failure and "
            "records a settled outcome instead — post_processing would not indicate "
            "the origin of the error. It would NOT resolve. The half-permission "
            "framing exists to forbid exactly this."
        ),
        "rationale": (
            "err is read-only (Acc(list_pred(err),1/2)); writing err[0] needs FULL "
            "permission. Must reject for INSUFFICIENT PERMISSION before any "
            "postcondition is reached. Rejection source: the permission system / "
            "the 1/2 framing on the input (directive 5). #1 weakness class."
        ),
    },
    {
        "id": "uniqueness-adjustable-reported-twice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DUP_ADJ,
        "refinement": (
            "this is model_prepatch.py's defect / the pre-change storage.py: an "
            "adjustable file is yielded in the first pass AND re-emitted at the end "
            "-> its name appears twice in stats['post_processed']. The F2P "
            "assertCountEqual(post_processed, set(post_processed)) FAILS on exactly "
            "this. It would NOT resolve."
        ),
        "rationale": (
            "an adjustable id is pushed to BOTH `first` and `collected` even when "
            "nothing failed, so it appears twice in result. Rejection source: "
            "postcondition (1) ToSeq(Result())==reported(...) AND postcondition (2) "
            "len(Result())==len(ids)+failing_adj_count(...) (the duplicate makes len "
            "exceed the budget)."
        ),
    },
    {
        "id": "partial-domain-drop-all-adjustable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_ADJ,
        "refinement": (
            "the faithful real patch is post_process WITHOUT the final `yield from` "
            "of the collected adjustable files: they are collected but never "
            "re-emitted, so their names never reach stats['post_processed']. The F2P "
            "assertIn(...) for the post-processed css files would FAIL. It would NOT "
            "resolve."
        ),
        "rationale": (
            "result == first only: correct on the all-plain sub-domain but drops "
            "every adjustable id on any collection with an adjustable file. "
            "Rejection source: postconditions (1) and (2) diverge whenever an "
            "adjustable file exists."
        ),
    },
    {
        "id": "partial-domain-drop-first-adjustable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DROP_FIRST_ADJ,
        "refinement": (
            "the faithful real patch would emit all but one of the collected "
            "adjustable files — every adjustable file but one reported. The dropped "
            "name never reaches stats['post_processed'], so the F2P membership "
            "assertions for the post-processed css files FAIL on the "
            "multi-adjustable fixture. It would NOT resolve."
        ),
        "rationale": (
            "result == first + collected[1:]: drops exactly the first collected "
            "adjustable id; equals reported(...) only when there are no adjustable "
            "files. Rejection source: postconditions (1) and (2) on the "
            ">=1-adjustable sub-domain (boundary near-miss)."
        ),
    },
    {
        "id": "withheld-failure-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _WITHHOLD_FAILURE,
        "refinement": (
            "the faithful real patch is the gold restructuring with the first-pass "
            "guard reduced to `name not in adjustable_paths`: the failing triple is "
            "stored under the file's key instead of being handed on, and the file's "
            "later settled triple overwrites it, so the caller never sees the "
            "failure, never re-raises, and records the file as successfully "
            "post-processed. That is exactly what the P2P test 'post_processing "
            "indicates the origin of the error when it fails' forbids (assertRaises "
            "+ the exact \"Post-processing '...' failed!\" stderr line). It would NOT "
            "resolve — and it is the counterexample the previous audit found."
        ),
        "rationale": (
            "the report-now test loses its failure disjunct (`if fa == 0` instead of "
            "`if fa == 0 or fe != 0`), so a failing adjustable file is held back and "
            "reported only for its settled outcome. Correct on the whole no-failure "
            "sub-domain and wrong exactly where a failure exists. Rejection source: "
            "the first-pass-segment invariant / postcondition (1) — the reported "
            "sequence is short by one entry per failing adjustable file, which "
            "postcondition (2) also detects."
        ),
    },
    {
        "id": "boundary-singleton-drops-first-pass",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _SINGLETON_DROPS_FIRST_PASS,
        "refinement": (
            "the faithful real patch guards the first pass's `yield` on the size of "
            "the `paths` mapping: for a one-file collection it emits only the final "
            "`yield from processed_adjustable_paths.values()`. The hidden P2P fixture "
            "for the failure path is EXACTLY a one-file collection (STATICFILES_DIRS "
            "pointed at a directory whose only file is the faulty one), so under this "
            "patch no failure report ever reaches collect(), it never re-raises, and "
            "`with self.assertRaises(Exception)` in 'post_processing indicates the "
            "origin of the error when it fails' FAILS — as does the assertion that "
            "stderr carries the \"Post-processing '...' failed!\" line. It would NOT "
            "resolve."
        ),
        "rationale": (
            "BOUNDARY probe on the singleton, and the one case whose rejection is "
            "attributable to the POSTCONDITIONS alone: the gold loop and BOTH its "
            "value invariants are verbatim, so `first`/`collected` really are the two "
            "segments; only the concatenation is size-guarded, returning `collected` "
            "when len(ids)==1. Identical to gold for every other size. Rejection "
            "source: postcondition (1) (and (2)) on the singleton — a lone failing "
            "adjustable file must be reported twice and a lone plain file once, and "
            "the rival reports once and zero times respectively."
        ),
    },
]


# ===========================================================================
# AXIOM lane — NONE. meta.json axioms == [] (no @ContractOnly consumed axiom).
# ===========================================================================
# The deep model (first_pass_ids / adj_ids / failing_adj_count / reported) is an
# A-REFERENCE of the function under change itself (HashedFilesMixin.post_process),
# already validated by axiom_check.py under G-AX (it loads the REAL patched
# post_process and asserts its yielded `name` sequence == reported(ids,adj,err)
# over boundary + exhaustive small + fuzz collections, INCLUDING collections that
# carry failing examinations, plus the non-convergence report arm). That is a
# Docker real-callee A-reference check, not a @ContractOnly-axiom
# soundness/containment obligation, and is owned by G-AX rather than this
# manifest's AXIOM_TESTS lane. There is therefore no axiom-soundness /
# axiom-containment probe to author here.
AXIOM_TESTS = []
