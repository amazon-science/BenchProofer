"""PBT manifest for django__django-15563 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  assign_columns(chain: List[int]) -> List[int]
    Requires (frame): Acc(list_pred(chain), 1/2)      -- chain is READ-ONLY (1/2 perm)
    Requires (domain): every chain[k] in {0,1}
    Ensures  (frame): Acc(list_pred(chain), 1/2)      -- the 1/2 perm is returned
    Ensures  (frame): Acc(list_pred(Result()))        -- full perm on the new list
    Ensures  (len):   len(Result()) == len(chain)
    Ensures  (BICONDITIONAL, load-bearing):
        for all k in [0,len): (Result()[k] == 0) == (ToSeq(chain)[k] == 1)
        -- a primary-key-chain ancestor (chain[k]==1) reuses column 0; any other
           ancestor (chain[k]==0) gets a non-zero column.
    Ensures  (DENSE-INDEX pin, load-bearing):
        for all k with chain[k]==0:
            Result()[k] == 1 + (count_fresh(chain) - count_fresh(chain.drop(k)))
        -- the fresh column at k is EXACTLY 1 + (number of fresh ancestors strictly
           before k), i.e. the contiguous block 1,2,...,F (F = count_fresh(chain)).
           This is the physical offset the consumer reads as r[index] into a source
           row of width 1+F; a sparse/colliding assignment over-runs the row.

  count_fresh(s: PSeq[int]) -> int  (@Pure, front-recursive fold)
    = the number of indices m with s[m]==0 (the fresh / non-reuse targets).

This models the gold patch of SQLUpdateCompiler.pre_sql_setup: for each ancestor
in self.query.related_updates, if the whole path up to it is a primary-key chain
( all(p.join_field.primary_key for p in meta.get_path_to_parent(related)) ) reuse
column 0 (meta.pk), else append a fresh column at index len(fields) and record it.

GROUNDED-ORACLE NOTE: the postcondition oracle count_fresh(chain) is GROUNDED in
the argument -- a @Pure fold fully computable from `chain`, with no opaque answer
key. So there is NO *wrong* echo a rival can return; the dense-index clause is a
function of the args, fully unfolded. The uniqueness lane is therefore about
whether a rival can satisfy the biconditional/dense pins on the F2P domain while
diverging on a discriminating sub-domain (a fresh ancestor placed in column 0;
sparse fresh columns 1,3,5,...; a colliding constant fresh column) -- the exact
behaviours the gold fix newly forbids and that IndexError/mis-filter the F2P
tests. No ungrounded-oracle echo is constructible; instead a cheapest-honest
positive control (local-variable reshape) is included (directive 2).

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region empty).
The path-primary-key predicate driving chain[k] is an A-reference deep model,
validated == the REAL Django get_path_to_parent / join_field.primary_key
out-of-band by axiom_check.py (G-AX). PBT re-runs that real-callee equivalence as
an axiom-soundness probe: axiom_check.py's logic is read on the HOST at load time
and embedded verbatim into the probe string (the runner mounts only the probe at
/work). Run with apply_gold=True (it reproduces the post-patch column assignment)
inside the instance container against real Django 4.1; it also runs a stdlib-only
20000-vector deep-model-==-gold fuzz that passes even when Django is absent. A
containment probe is N/A: there is no consumed-axiom Requires domain to fall
outside; the A-reference's domain is the full {0,1} flag space the model accepts,
which the fuzz sweeps exhaustively in shape.

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the invariants are nested inside that region, so
editing them is still inside impl and preserves same_spec). The frozen spec
(axioms/pure/pre/post-conditions/signatures) is never touched.
"""
from pathlib import Path

INSTANCE = "django__django-15563"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_READ_FLAG = "        Assert(ToSeq(chain)[i] == chain[i])\n"
_TRUE_BRANCH = "        if chain[i] == 1:\n            result = result + [0]\n"
_FALSE_TAIL = ("            result = result + [width]\n"
               "            width = width + 1\n")
_DENSE_ASSERT = ("            Assert(width == 1 + (count_fresh(ToSeq(chain)) - "
                 "count_fresh(ToSeq(chain).drop(i))))\n")
_INV_DENSE = ("        Invariant(Forall(int, lambda k: Implies(0 <= k and k < i and "
              "result[k] != 0,\n"
              "                  result[k] == 1 + (count_fresh(ToSeq(chain)) - "
              "count_fresh(ToSeq(chain).drop(k))))))\n")
_INV_WIDTH_SUFFIX = ("        Invariant(count_fresh(ToSeq(chain)) == (width - 1) + "
                     "count_fresh(ToSeq(chain).drop(i)))\n")

for _a in (_READ_FLAG, _TRUE_BRANCH, _FALSE_TAIL, _DENSE_ASSERT,
           _INV_DENSE, _INV_WIDTH_SUFFIX):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5) POSITIVE CONTROL -- local-variable reshape. The two branch bodies are
# rewritten to bind the appended column value to a fresh local `col` first, then
# append it; the false branch keeps `width = width + 1` AFTER the append (so `col`
# captures the pre-increment width, identical to the gold `result + [width]`).
# Every invariant and the dense framing Assert(width == ...) are kept VERBATIM, so
# the gold proof obligations (the suffix-count invariant, the per-element dense
# pin, the biconditional invariant) all still discharge -- only the executable
# shape of the two appends changed (no loop-direction flip, no dropped lemma).
# MUST verify; else the postcondition is over-fit to the literal append FORM =>
# SPEC-TOO-STRONG.
_POS_RESHAPE = _swap(
    _BASE,
    "        if chain[i] == 1:\n"
    "            result = result + [0]\n"
    "        else:\n"
    "            # The fresh column placed here is the running `width`, which the\n"
    "            # suffix invariant pins to 1 + (fresh strictly before i) — exactly\n"
    "            # the dense index for target i.\n"
    "            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))\n"
    "            result = result + [width]\n"
    "            width = width + 1\n",
    "        if chain[i] == 1:\n"
    "            col = 0\n"
    "            result = result + [col]\n"
    "        else:\n"
    "            # local-variable reshape: bind the running width, then append.\n"
    "            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))\n"
    "            col = width\n"
    "            result = result + [col]\n"
    "            width = width + 1\n",
)

# (6) ADMISSIBILITY -- entry asserts that the Requires facts hold on a fresh,
# F2P-shaped input. The F2P scenarios (Congressman / Senator .update(title=...))
# reach a single non-pk-chain ancestor (the title-bearing Politician), modelled as
# chain == [0]. A fresh local probe = [0] is constructed and BOTH precondition
# clauses are re-derived in-region for it: the frame Acc(list_pred(probe),1/2) and
# the {0,1}-domain Forall (ToSeq(probe)[0]==0 is in {0,1}). This proves the
# precondition ADMITS that normal input -- the precondition is not contradictory /
# over-restrictive -- without a recursive self-call.
#
# WHY NOT A RECURSIVE SELF-CALL `assign_columns(probe)`: the gold body already
# verifies in ~221s (meta.json model_wall_time_s == 221.0), close to the runner's
# 300s VERIFY_TIMEOUT; a recursive self-call re-instantiates the FULL contract
# (all four quantified Ensures, the count_fresh fold) on top of the heavy
# dense-index loop, which reliably overruns 300s (measured: rejected(timeout) at
# 301.7s in the flagged run, and >700s under load). The entry-assert form is the
# established admissibility shape (cf. astropy__astropy-14369 _IMPL_ADMISS) and
# verifies in ~110-220s. It tests the SAME thing the self-call would test for the
# precondition lane (does Requires admit a normal F2P-shaped input), without the
# budget-induced false reject. MUST verify; else the precondition rejects a normal
# F2P-shaped input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE,
    "    result = []  # type: List[int]\n",
    "    # ADMISSIBILITY: a normal F2P-shaped input (the single non-pk-chain\n"
    "    # title-bearing Politician ancestor both F2P scenarios reach is\n"
    "    # chain == [0]) is in-domain: BOTH Requires clauses hold for it.\n"
    "    probe = [0]  # type: List[int]\n"
    "    Assert(Acc(list_pred(probe), 1 / 2))\n"
    "    Assert(len(probe) == 1)\n"
    "    Assert(ToSeq(probe)[0] == 0)\n"
    "    Assert(Forall(int, lambda k: Implies(0 <= k and k < len(probe),\n"
    "                                         ToSeq(probe)[k] == 0 or ToSeq(probe)[k] == 1)))\n"
    "    result = []  # type: List[int]\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). chain is read-only at 1/2.
# This rival WRITES `chain[i] = 1` before reading it, attempting to normalize the
# input so that every ancestor LOOKS like a primary-key chain and the
# biconditional is vacuously satisfiable by returning all-zeros. Under
# Acc(list_pred(chain),1/2) a store needs FULL permission, so it MUST be rejected
# for INSUFFICIENT PERMISSION (not a value mismatch). All gold invariants and the
# dense framing assert are kept verbatim, so the rejection is attributable solely
# to the write.
_RIVAL_FRAME = _swap(
    _BASE, _READ_FLAG,
    "        chain[i] = 1\n"
    "        Assert(ToSeq(chain)[i] == chain[i])\n",
)

# (3a) PARTIAL-DOMAIN -- everyone reuses column 0 (== model_prepatch.py behaviour:
# the pre-patch `query.add_fields([pk.name])` selects ONLY column 0, so every
# ancestor is implicitly filtered by column 0). The false branch is rewritten to
# also append 0 (and the now-unreachable dense Assert + width increment removed so
# the rival is internally consistent / no dead-code framing). Correct on a chain
# of ALL primary-key chains (all 1s), wrong the instant any ancestor is fresh
# (chain[k]==0): the biconditional (Result()[k]==0)==(chain[k]==1) demands a NON
# zero column there. The verifier cannot close the biconditional on a 0-entry.
_RIVAL_ALL_ZERO = _swap(
    _BASE,
    "        else:\n"
    "            # The fresh column placed here is the running `width`, which the\n"
    "            # suffix invariant pins to 1 + (fresh strictly before i) — exactly\n"
    "            # the dense index for target i.\n"
    "            Assert(width == 1 + (count_fresh(ToSeq(chain)) - count_fresh(ToSeq(chain).drop(i))))\n"
    "            result = result + [width]\n"
    "            width = width + 1\n",
    "        else:\n"
    "            result = result + [0]\n",
)

# (3b) PARTIAL-DOMAIN -- SPARSE fresh columns (width += 2): fresh ancestors get
# columns 1,3,5,... instead of the dense 1,2,3,.... This is the former G-MUT
# survivor (closed by the D1 dense-index strengthening). The biconditional still
# holds (fresh => non-zero), but the dense-index postcondition
# Result()[k]==1+(count_fresh(chain)-count_fresh(chain.drop(k))) is violated for
# the 2nd+ fresh ancestor (it expects 2, the rival produces 3). Correct on any
# chain with <=1 fresh ancestor (the F2P scenarios have exactly one!), wrong with
# >=2 fresh ancestors. The suffix-count invariant width==1+prefix-fresh also
# breaks. NOTE the dense Assert(width==...) is retained but width drifts after the
# first +2, so that very Assert fails -- the rejection is attributable to the
# dense pin.
_RIVAL_SPARSE = _swap(_BASE, _FALSE_TAIL,
                      "            result = result + [width]\n"
                      "            width = width + 2\n")

# (3c) PARTIAL-DOMAIN -- COLLIDING constant fresh column: every fresh ancestor
# gets column 1 (no width bump). The biconditional still holds (1 != 0). Correct
# on any chain with <=1 fresh ancestor (incl. both F2P scenarios), wrong with >=2
# fresh ancestors: the 2nd fresh ancestor's dense index must be 2 but the rival
# returns 1, and the two fresh columns collide (both read source column 1, so two
# distinct ancestors would be filtered by the same column's values). The
# dense-index postcondition cannot be closed; the suffix-count invariant
# width==1+prefix-fresh breaks too. The dense Assert is kept verbatim.
_RIVAL_CONST1 = _swap(_BASE, _FALSE_TAIL,
                      "            result = result + [1]\n")


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {"id": "pos-control-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RESHAPE,
     "rationale": "structurally-different (each branch binds the column value to a "
                  "fresh local `col` before appending; the false branch keeps "
                  "width=width+1 AFTER the append so col captures the pre-increment "
                  "width, identical to the gold result+[width]) but CORRECT impl. "
                  "Every invariant and the dense framing Assert(width==...) are kept "
                  "verbatim, so the suffix-count invariant, the per-element dense pin "
                  "and the biconditional invariant all still discharge -- only the "
                  "append SHAPE changed (no loop-direction flip, no dropped lemma, so "
                  "no auto-undischargeable proof gap). Must verify; else the "
                  "postcondition is over-fit to the literal append FORM => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "entry asserts on a fresh F2P-shaped input probe==[0] (the single "
                  "non-pk-chain title-bearing Politician ancestor both F2P scenarios "
                  "reach) re-derive BOTH Requires clauses in-region: the frame "
                  "Acc(list_pred(probe),1/2) and the {0,1}-domain Forall "
                  "(ToSeq(probe)[0]==0 is in {0,1}), proving the precondition ADMITS a "
                  "normal input. A recursive self-call assign_columns(probe) was "
                  "DROPPED because the gold body alone verifies in ~221s and the "
                  "self-call re-instantiates the full contract on top of the heavy "
                  "dense-index loop, overrunning the 300s VERIFY_TIMEOUT (it was the "
                  "rejected(timeout) at 301.7s that flagged this instance); the "
                  "entry-assert form (cf. astropy__astropy-14369 _IMPL_ADMISS) tests "
                  "the same precondition-admissibility property within budget. If the "
                  "precondition rejects this normal F2P-shaped input => "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-chain", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: pre_sql_setup never "
                   "mutates the path-classification result it reads; the predicate "
                   "all(p.join_field.primary_key for p in meta.get_path_to_parent(rel)) "
                   "is computed from immutable model metadata, not written back. The "
                   "rival exists solely to test whether the read-only (1/2) precondition "
                   "can be subverted by overwriting `chain` so every ancestor LOOKS like "
                   "a pk-chain and the all-zeros return vacuously satisfies the "
                   "biconditional. There is no resolving patch that rewrites its input "
                   "flags, so a verifying rival here would be a pure verify-not-resolve "
                   "artifact (vacuous satisfaction via self-normalization).",
     "rationale": "MANDATORY frame-mutation probe. `chain[i] = 1` writes through a 1/2 "
                  "(read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store needs full Acc(list_pred(chain))), NOT a value mismatch; the "
                  "gold invariants and the dense framing assert are kept verbatim so the "
                  "rejection is attributable to the write. Rejection source: the "
                  "PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK (frame protection "
                  "hollow)."},
    {"id": "weak-all-column-0", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALL_ZERO,
     "refinement": "appending 0 in BOTH branches is EXACTLY the pre-patch behaviour "
                   "(== model_prepatch.py): the old query.add_fields([pk.name]) selects "
                   "only column 0 and every ancestor is implicitly filtered by the "
                   "source row's own pk. A faithful patch doing this leaves the "
                   "title-bearing Politician ancestor (a non-pk-chain, chain[k]==0) "
                   "reading column 0 -- the source row's CHILD pk, which differs from "
                   "the Politician pk -- so Congressman/Senator .update(title=...) "
                   "filters the parent UPDATE by the wrong ids and the title is never "
                   "written. This is the EXACT F2P failure both tests assert against "
                   "(get().title == 'senator 1') -- verify-not-resolve.",
     "rationale": "rejection source: the BICONDITIONAL postcondition "
                  "(Result()[k]==0)==(ToSeq(chain)[k]==1). A fresh ancestor (chain[k]==0) "
                  "is assigned column 0, so the verifier cannot close the biconditional "
                  "(it demands a non-zero column there); the dense-index postcondition is "
                  "also violated (0 != 1+prefix-fresh for a fresh target). If it verified "
                  "=> SPEC-TOO-WEAK."},
    {"id": "weak-sparse-columns", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SPARSE,
     "refinement": "incrementing width by 2 places fresh ancestors at columns "
                   "1,3,5,... while the pre-selection row built by the gold has width "
                   "1+F (one column per fresh ancestor, contiguous). The k-th fresh "
                   "ancestor's recorded index then over-runs the row: with 2 fresh "
                   "ancestors the 2nd index is 3 into a width-3 row [0,1,2] -- a faithful "
                   "patch (related_ids_index.append((rel, len(fields)+extra))) reads "
                   "r[3] for r in rows and IndexErrors at runtime, failing the F2P. "
                   "(This was the former G-MUT survivor, closed by the D1 dense-index "
                   "strengthening.) -- verify-not-resolve.",
     "rationale": "rejection source: the DENSE-INDEX postcondition "
                  "Result()[k]==1+(count_fresh(chain)-count_fresh(chain.drop(k))) and the "
                  "suffix-count loop invariant count_fresh(chain)==(width-1)+"
                  "count_fresh(chain.drop(i)). After the first +2, width drifts above the "
                  "true running fresh count, so both the per-element dense pin (expects 2, "
                  "rival gives 3 for the 2nd fresh target) and the retained "
                  "Assert(width==1+prefix-fresh) fail. Correct on any <=1-fresh chain "
                  "(incl. the F2P), wrong on >=2 fresh. If it verified => SPEC-TOO-WEAK."},
    {"id": "weak-const-column-1", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CONST1,
     "refinement": "appending the constant 1 for every fresh ancestor (no width bump) "
                   "collides their columns: two distinct non-pk-chain ancestors both read "
                   "source column 1, so a faithful patch "
                   "(related_ids_index.append((rel, 1))) filters two different parent "
                   "UPDATEs by the SAME column's values -- the second ancestor is "
                   "constrained by the first ancestor's identifying ids and its rows are "
                   "mis-updated. On a 2-fresh MTI tree the title write lands on the wrong "
                   "parent rows, failing an F2P-shaped assertion -- verify-not-resolve. "
                   "(Both shipped F2P scenarios have exactly one fresh ancestor, so this "
                   "rival is CORRECT on them yet wrong on the >=2-fresh sub-domain.)",
     "rationale": "rejection source: the DENSE-INDEX postcondition "
                  "Result()[k]==1+(count_fresh(chain)-count_fresh(chain.drop(k))). The 2nd "
                  "fresh ancestor's dense index must be 2 but the rival returns 1; the "
                  "suffix-count invariant width==1+prefix-fresh also breaks (width never "
                  "advances). The verifier cannot close the dense pin on a >=2-fresh "
                  "chain. If it verified => SPEC-TOO-WEAK (dense distinctness hollow)."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed (axioms region empty). The
# path-primary-key predicate driving chain[k] is an A-reference deep model
# validated == the REAL Django get_path_to_parent / join_field.primary_key. We
# re-run that real-callee equivalence (axiom_check.py's logic, read on the HOST and
# embedded verbatim into a self-contained probe) as an axiom-soundness check: if
# the deep model assign_columns ever disagrees with the real-predicate-driven gold
# column construction on the F2P MTI scenarios (real Django in-container) OR on the
# 20000-vector stdlib fuzz, the A-reference is unsound. The probe also fails loud
# if either F2P scenario produces no related-update target (false-pass guard).
# A containment probe is N/A: there is no consumed-axiom Requires domain; the
# A-reference's domain is the full {0,1}^n flag space the model's Requires admits,
# which the fuzz sweeps in shape (n in 0..12) and the two real F2P scenarios pin
# concretely.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-assign-columns-equals-real-gold",
        "axiom": "assign_columns",  # the A-reference deep model (not a consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model assign_columns is an A-reference: it must equal the "
                     "REAL post-patch column assignment driven by the real Django "
                     "predicate all(p.join_field.primary_key for p in "
                     "meta.get_path_to_parent(rel)). This probe (axiom_check.py verbatim, "
                     "encoding-safe, stdlib-only fuzz + real Django when present) builds "
                     "the concrete MTI tree the F2P tests exercise (Politician <- "
                     "Congressman(Person, Politician) <- Senator), drives the REAL "
                     "UpdateQuery.add_update_values({'title':...}) to populate "
                     "related_updates for both F2P scenarios, evaluates the REAL predicate "
                     "per target, reproduces the GOLD fields/related_ids_index column "
                     "construction from those real values, and asserts it == "
                     "assign_columns(real_flags) AT THE INDEX LEVEL "
                     "(model_index[k]==0 <=> real_is_pk_chain[k], no double mask) with "
                     "distinct positive fresh columns; plus 20000 random flag vectors == "
                     "the gold construction. It FAILS LOUD if a scenario yields no "
                     "related-update target. Exit 0 iff every obligation holds; any "
                     "disagreement => the A-reference is UNSOUND. apply_gold=True (the "
                     "real predicate/construction is the post-patch behaviour).",
    },
]
