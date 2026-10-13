# properties.py — PBT manifest for sphinx-doc__sphinx-10466. NOT a Nagini module;
# a record of adversarial cases the runner (swebench_nagini.pbt) executes + stamps.
#
# Defended surface (read model.py):
#   * canonical_positions(recorded)  — the modeled changed behaviour. recorded is
#       READ-ONLY: Requires/Ensures Acc(list_pred(recorded), 1/2). Load-bearing
#       postcondition:  ToSeq(Result()) == dedup_sort(ToSeq(recorded))
#       (the deduplicated, strictly-ascending ordered set of the recorded keys).
#   * insert_sorted(xs, key)         — verified imperative skeleton of ONE
#       ordered-set insertion step. xs is READ-ONLY: Acc(list_pred(xs), 1/2).
#       Load-bearing postcondition:  ToSeq(Result()) == ins(key, ToSeq(xs)).
#
#   Both oracles (`ins`, `dedup_sort`) are GROUNDED: pure front-recursive folds
#   fully unfolded over the function's OWN arguments (recorded/xs, key). There is
#   no opaque answer-key marker to echo — so the ungrounded-oracle-echo attack is
#   N/A (see 'assessment'); instead the positive controls below are honest
#   cheapest/structurally-different correct impls.
#
#   No @ContractOnly axioms in this bundle (meta.axioms == []). The single deep-
#   model reference is the A-reference dedup_sort == sorted(set(...)); axiom_check.py
#   (G-AX) validates it. AXIOM_TESTS carries one A-reference soundness probe that
#   re-runs that real callee, since the verify=>resolve chain rests on it.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10466"
FLOAT_ENCODING = None  # meta.float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
# Every variant edits text ONLY inside an # impl-start / # impl-end region, so
# the frozen spec (axioms/pure/pre/post-conditions + signatures) is untouched and
# same_spec holds. The frozen postcondition / permission system is what each
# reject case is attributed to.

# --- 1. FRAME-MUTATION on canonical_positions (MANDATORY: read-only input) ----
# Rival mutates the read-only `recorded` (Acc(...,1/2)) at the top of the impl,
# before the fold. With only 1/2 permission any mutation is illegal, so this
# MUST fail to verify for INSUFFICIENT PERMISSION (not for a value mismatch).
# The gold invariants/asserts are kept verbatim so the rejection is attributable
# to the mutation alone. (Shape note: an earlier form put a subscript-store
# `recorded[i] = recorded[i]` inside the invariant-laden loop body; that shape
# sits on a Z3 convergence cliff — it rejected in ~39s on one run and then
# timed out at 1200s at the gate. The pre-loop `append` form is semantically the
# same frame violation against the same frozen Acc(...,1/2) precondition but
# rejects deterministically in ~15s.)
_frame_canon = _swap(
    _BASE,
    "    # impl-start\n    result = []  # type: List[int]\n",
    "    # impl-start\n"
    "    recorded.append(0)  # illegal mutation: only Acc(...,1/2) held\n"
    "    result = []  # type: List[int]\n",
)

# --- 2. FRAME-MUTATION on insert_sorted (read-only input xs) -----------------
# Supporting frame-mutation probe on the helper: overwrite the half-permission
# `xs` before reading it. Must reject for insufficient permission.
_frame_ins = _swap(
    _BASE,
    "        cur = xs[j]\n",
    "        xs[j] = xs[j]  # illegal write: only Acc(xs, 1/2) held\n"
    "        cur = xs[j]\n",
)

# --- 3. PARTIAL-DOMAIN: no dedup / no sort (the PRE-PATCH behaviour) ----------
# Rival appends every recorded position verbatim in scan order, skipping the
# ordered-set insertion entirely. This is exactly the pre-patch
# `positions = [(source, line) for ...]` (duplicates kept, scan order). It must
# reject: postcondition pins dedup_sort, the strict-ascending DISTINCT keys.
# Refinement: a faithful real patch that emits the verbatim projection is the
# UNPATCHED code; F2P test_Catalog_duplicated_message records ('/path/to/filename',1)
# twice and expects msg1.locations == [(...,1),(...,2),(yetanother,1)] (deduped,
# sorted) — the verbatim projection yields the duplicate, so the test FAILS.
_no_dedup = _swap(
    _BASE,
    "        result = insert_sorted(result, key)\n",
    "        result = result + [key]  # verbatim projection: no dedup, no sort\n",
)

# --- 4. PARTIAL-DOMAIN: insert_sorted never drops an already-present key ------
# Rival inserts `key` at its sorted slot but ALSO keeps a present duplicate
# (handles the `cur == key` case as a plain insert, not a drop). It is correct on
# every input where `key` is absent but wrong when `key` already occurs. Must
# reject: postcondition is ins(key, xs), which DROPS key if present.
# Refinement: as a real patch this is `sorted(list(positions)+[key])` style
# (sort without set / multiset insert) — keeps duplicates, so the deduped F2P
# expectation fails the moment a position recurs (it does: ('/path/to/filename',1)).
_ins_keepdup = _swap(
    _BASE,
    "        else:\n"
    "            # `cur == key`: `ins(key, suffix) == suffix`; `key` already present.\n"
    "            out = out + [cur]\n"
    "            placed = True\n",
    "        else:\n"
    "            # WRONG: keep both cur and key when equal (no dedup).\n"
    "            out = out + [key]\n"
    "            out = out + [cur]\n"
    "            placed = True\n",
)

# --- 5. PARTIAL-DOMAIN: drop the LAST recorded position (off-by-one bound) ----
# Rival folds over recorded[:-1], correct on the prefix but silently dropping the
# final recorded occurrence. Must reject: postcondition is over ALL of recorded.
# Refinement: as a real patch this is `sorted(set(positions[:-1]))` — it loses
# the last recorded position; on the F2P 'world' message (single occurrence
# ('/path/to/filename',1)) it would yield [] != [('/path/to/filename',1)], so the
# test FAILS.
_drop_last = _swap(
    _BASE,
    "    while i < len(recorded):\n",
    "    while i < len(recorded) - 1:  # WRONG: drops the last recorded position\n",
)

# --- 6. POSITIVE CONTROL (soundness): structurally-different CORRECT impl -----
# In insert_sorted, the `placed` branch and the `cur < key` branch perform the
# identical action `out = out + [cur]`. Merge them into one branch (a pure
# branch-reorder / control-flow reshape) — semantics and every proof obligation
# (invariants + framing asserts) are preserved. MUST verify (else SPEC-TOO-STRONG).
# This is NOT a forward-append-vs-front-recursive-fold trap: the loop shape, the
# invariant peel, and the per-step `drop` unfolds are all kept verbatim; only two
# equal-action branches are coalesced.
_pos_merge = _swap(
    _BASE,
    "        if placed:\n"
    "            out = out + [cur]\n"
    "        elif cur < key:\n"
    "            out = out + [cur]\n"
    "        elif cur > key:\n",
    "        if placed or cur < key:\n"
    "            # merged: in both cases `cur` is emitted unchanged.\n"
    "            out = out + [cur]\n"
    "        elif cur > key:\n",
)

# --- 7. ADMISSIBILITY (precond accepts a normal F2P-shaped input) -------------
# The unmodified gold impl: the frozen Requires Acc(list_pred(recorded),1/2) /
# Acc(list_pred(xs),1/2) must admit the normal call sites (canonical_positions
# calling insert_sorted on a half-permission list, of any length incl. 0 and the
# F2P shape). If this DID NOT verify the precondition would be too strong. Using
# the verbatim model.py is the cleanest admissibility positive control: it proves
# the spec accepts the real, F2P-shaped input domain.
_admiss = _BASE


SPEC_TESTS = [
    {
        "id": "frame-mutation-canonical",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_canon,
        "refinement": (
            "Writing to `recorded` has no faithful real counterpart: the patched "
            "Catalog.__iter__ never mutates self.metadata[message]; it only reads "
            "the projected positions. A real patch that mutated the recorded "
            "occurrences would corrupt the catalogue and not produce the deduped/"
            "sorted locations the F2P test asserts. This rival can only 'satisfy' "
            "the postcondition by clobbering its read-only input."
        ),
        "rationale": (
            "Permission system: recorded is held at Acc(list_pred(recorded),1/2) "
            "(Requires + Invariant). A mutation (list append) needs full "
            "permission, so Nagini rejects for INSUFFICIENT PERMISSION, not a "
            "value mismatch."
        ),
    },
    {
        "id": "frame-mutation-insert-sorted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_ins,
        "refinement": (
            "insert_sorted models one ordered-set insertion step of sorted(set(.)); "
            "the real operation never mutates the input list. A write to xs has no "
            "faithful real patch and could not produce sorted(set(...)) of the "
            "original positions in __iter__."
        ),
        "rationale": (
            "Permission system: xs is held at Acc(list_pred(xs),1/2) "
            "(Requires + loop Invariant). The store xs[j]=... requires full "
            "permission => rejected for insufficient permission."
        ),
    },
    {
        "id": "partial-domain-no-dedup-no-sort",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_dedup,
        "refinement": (
            "This IS the pre-patch behaviour (verbatim projection, duplicates kept, "
            "scan order) — see model_prepatch.py / refinement.md A2. F2P "
            "test_Catalog_duplicated_message records ('/path/to/filename',1) twice "
            "and expects msg1.locations == [(.../filename,1),(.../filename,2),"
            "(.../yetanother,1)] (deduped, sorted). The verbatim projection yields "
            "the duplicate ('/path/to/filename',1) twice and in scan order => the "
            "F2P assertion fails. Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "Postcondition ToSeq(Result()) == dedup_sort(ToSeq(recorded)) pins the "
            "DEDUPED, strictly-ascending ordered set. result = result + [key] over "
            "scan order keeps duplicates and original order, so result != "
            "dedup_sort whenever recorded has a repeat or is unsorted."
        ),
    },
    {
        "id": "partial-domain-keep-duplicate-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ins_keepdup,
        "refinement": (
            "As a real patch this is a sort-without-set / multiset insert "
            "(`sorted(list(positions))` keeping repeats). It is correct only on "
            "messages whose positions are all distinct; the F2P 'hello' message "
            "records ('/path/to/filename',1) twice, so it would emit that location "
            "twice while the test expects it ONCE => F2P fails. Faithful patch does "
            "NOT resolve."
        ),
        "rationale": (
            "Postcondition is ins(key, xs), which DROPS key when it already occurs "
            "(the `x == s[0] => return s` branch of ins). Emitting both key and the "
            "equal element makes ToSeq(Result()) longer than ins(key, ToSeq(xs)) "
            "on the equal sub-domain => verification fails."
        ),
    },
    {
        "id": "partial-domain-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop_last,
        "refinement": (
            "As a real patch this is sorted(set(positions[:-1])) — it silently "
            "drops the last recorded occurrence. On the F2P 'world' message (a "
            "single occurrence ('/path/to/filename',1)) it yields [] whereas the "
            "test expects msg2.locations == [('/path/to/filename',1)] => F2P fails. "
            "Faithful patch does NOT resolve."
        ),
        "rationale": (
            "The loop folds insert_sorted over recorded; bounding it by "
            "len(recorded)-1 leaves result == dedup_sort(take(len-1)) at exit, but "
            "the postcondition demands dedup_sort(ToSeq(recorded)) (the full "
            "sequence). On any non-empty recorded whose last key is not already in "
            "the prefix's ordered set, the two differ => verification fails. (On "
            "empty recorded the bound is vacuous and the answer coincides, so this "
            "is genuinely a partial-domain divergence, not a total wrong answer.)"
        ),
    },
    {
        "id": "pos-control-merge-equal-branches",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_merge,
        "rationale": (
            "Structurally-different but CORRECT: the `placed` and `cur < key` "
            "branches both do `out = out + [cur]`, so merging them into "
            "`if placed or cur < key` is a pure control-flow reshape. All loop "
            "invariants and the per-step drop-unfold framing asserts are kept "
            "verbatim, so the gold proof still discharges. Must verify (else "
            "SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admissibility-gold-impl",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "The frozen spec + gold impl. Confirms Requires "
            "Acc(list_pred(recorded),1/2) / Acc(list_pred(xs),1/2) ADMITS the "
            "normal F2P-shaped call domain (canonical_positions folding "
            "insert_sorted over a half-permission list of any length, incl. 0 and "
            "the duplicated-message shape). If it failed, the precondition would be "
            "too strong (PRECOND-TOO-STRONG)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — A-reference deep model (no consumed @ContractOnly axioms)
# ---------------------------------------------------------------------------
# meta.axioms == []; the only callee correspondence is the A-reference
# dedup_sort == sorted(set(...)). Re-run the REAL operation in-container and assert
# the deep model matches it across boundary + fuzz, AND that the (source,line)->int
# key abstraction is faithful (the verify=>resolve chain rests on this). The probe
# is self-contained (stdlib `random` only) — it embeds the model.py-lockstep
# reference encodings of ins/dedup_sort, mirroring axiom_check.py.

# Reuse axiom_check.py's logic by embedding its reference encodings + checks.
_PROBE_DEDUP_SORT = r'''
import random, sys

# model.py pure-region reference encodings (kept in lock-step with model.py).
def ins(x, s):
    if len(s) == 0:
        return [x]
    if x < s[0]:
        return [x] + s
    if x == s[0]:
        return s
    return [s[0]] + ins(x, s[1:])

def dedup_sort(s):
    if len(s) == 0:
        return []
    return ins(s[-1], dedup_sort(s[:-1]))

def check_dedup_sort(xs):
    observed = dedup_sort(list(xs))     # deep model (model.py pure region)
    expected = sorted(set(xs))          # the REAL operation in the gold patch
    assert observed == expected, (
        "AXIOM-UNSOUND: dedup_sort(%r)=%r != sorted(set(...))=%r"
        % (xs, observed, expected))

def check_position_abstraction(positions):
    real = sorted(set(positions))                  # over the real (source,line) tuples
    universe = sorted(set(positions))
    key_of = {t: k for k, t in enumerate(universe)}
    keys = [key_of[t] for t in positions]          # model carrier: int keys
    model_keys = dedup_sort(keys)
    inv = {k: t for t, k in key_of.items()}
    decoded = [inv[k] for k in model_keys]
    assert decoded == real, (
        "AXIOM-UNSOUND: integer-key abstraction on %r: decoded %r != real %r"
        % (positions, decoded, real))

rng = random.Random(10466)

# boundary: empty / all-dup / reversed / sorted / mixed / negatives / palindrome
boundary = [[], [0], [5, 5, 5], [3, 2, 1], [1, 2, 3],
            [2, 1, 2, 3, 1], [-1, -1, 0, 7, 7, 7, 2], [10, 9, 8, 8, 9, 10]]
for xs in boundary:
    check_dedup_sort(xs)

# integer-key fuzz: small value range => frequent duplicates (the dedup path).
for _ in range(20000):
    n = rng.randint(0, 16)
    xs = [rng.randint(0, 8) for _ in range(n)]
    check_dedup_sort(xs)

# the exact F2P scenario: same (source,line) recorded several times, scan order.
f2p = [('/path/to/filename', 1), ('/path/to/filename', 1),
       ('/path/to/filename', 2), ('/path/to/yetanother', 1)]
check_position_abstraction(f2p)
assert sorted(set(f2p)) == [('/path/to/filename', 1),
                            ('/path/to/filename', 2),
                            ('/path/to/yetanother', 1)], "F2P expectation drift"

# (source,line) fuzz: small alphabets => collisions/dups common.
sources = ['/a.rst', '/b.rst', '/c.rst', '../../m/hair.rst', '../../m/metas.rst']
lines = [0, 1, 2, 38, 92, 96, 121, 125]
for _ in range(20000):
    n = rng.randint(0, 20)
    positions = [(rng.choice(sources), rng.choice(lines)) for _ in range(n)]
    check_position_abstraction(positions)

print("G-AX OK: dedup_sort deep model == sorted(set(...)) on %d boundary + 20000 "
      "int fuzz; integer-key abstraction faithful on 1 F2P + 20000 position fuzz"
      % len(boundary))
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "axref-dedup-sort-sound",
        "axiom": "dedup_sort",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_DEDUP_SORT,
        "rationale": (
            "A-reference soundness: dedup_sort (the deep model in model.py's pure "
            "region) must equal the REAL sorted(set(...)) the gold patch applies, "
            "and the (source,line)->int key abstraction must be order/equality "
            "faithful. Runs the real CPython sorted/set on boundary + 40000 fuzz "
            "inputs (incl. the exact F2P scenario). Any disagreement => the deep "
            "model / abstraction is unsound, breaking verify=>resolve. Mirrors "
            "axiom_check.py (G-AX). The dedup_sort domain is total over PSeq[int] "
            "(no quantified Requires), so every caller-reachable input is covered "
            "by construction — containment is trivially satisfied, hence no "
            "separate axiom-containment case."
        ),
    },
]
