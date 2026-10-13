#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for astropy__astropy-14539.

The bundle models ONE routine: the per-column computation of the differing-row
index list for a variable-length-array (VLA) table column, inside
`TableDataDiff._diff` (mapping.md). The patch widens the branch predicate that
selects the row-wise VLA comparison so that BOTH variable-length-array format
markers route to it; the row-wise comparison itself is unchanged.

POST-PATCH behaviour for a VLA column (the branch `patch.diff` enables) is:

    diffs = ([idx for idx in range(len(arra))
              if not np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)],)

i.e. the increasing list of row indices whose stored value sequences the per-row
closeness test does not accept.

WHAT THE MODEL ABSTRACTS, AND SO WHAT EACH LEG CAN TEST. `Solution.lean` declares
the per-row closeness test as an UNCHANGED opaque callee, `rowsAgree`, and states
the row-wise report as the set of rows that callee does not accept. It therefore
makes NO claim about that callee's verdicts, and a leg comparing the model's
verdicts against numpy's would be testing a claim the spec does not make. What the
spec does claim, and what is tested here, is (1) the SHAPE of the report given the
callee's verdicts — which rows are eligible, in which order, under which branch —
and (2) that each modeled callee answers on EXACTLY the inputs the spec names as
its domain (`rowsComparable` per row for the per-row test, `rowsAreFixedShape`
per column pair for the flat one). Both domains are ARGUMENTS of the declarations
rather than assumptions about them, so a leg that found a domain wider or narrower
than the real routine's would be reporting a spec that demands a report where none
exists, or refuses one where it does. Three legs, in that order, plus one leg on
the abstraction's necessity:

  LEG "report" — the report's shape. ORACLE is the faithful post-patch replica:
  numpy object arrays of per-row integer arrays and the real `numpy.allclose` at
  the harness tolerances, exactly as `patch.diff` runs it. SHADOW is an op-for-op
  transliteration of `implementation_columnDiffRows`'s impl region (refinement.md)
  with the opaque callee INSTANTIATED by the real per-row test — the one reading
  under which the model is a claim about this routine at all. The leg therefore
  tests the row domain (`range(len(arra))`, nothing dropped), the increasing order,
  the accumulation, and the format branch, and it is deliberately silent about the
  callee's verdicts.

  LEG "domain" — the fidelity of the per-row test's stated domain.
  `rowsComparable xs ys` (equal lengths, or one side of length 1) is asserted to be
  exactly the pairs of rows the real per-row test can answer at all. The leg checks,
  on every generated row pair including the INCOMPARABLE ones, that `rowsComparable`
  holds iff `np.allclose` returns rather than raising. This is the leg that decides
  whether the domain the reporter is handed is honest or whether it fences out rows
  the real routine handles.

  LEG "flat-domain" — the same question for the OTHER callee, on the branch that
  reaches it. `rowsAreFixedShape arra arrb` (the two columns report the same number
  of rows, and every row of either stores the same number of values as every other)
  is asserted to be exactly the column pairs the real flat comparison
  `np.where(arra != arrb)` can report on. Note what this predicate does NOT say: it
  does not say one value per row. A fixed-shape column may store a small block of
  values in each row, the flat comparison relates two such columns position by
  position, and it reports on them without complaint — so a predicate demanding a
  single value per row would fence out column pairs the real routine handles, and
  the spec would then demand nothing at them. What the comparison cannot do is
  relate a RAGGED pair, which has no block to compare and which the storage cannot
  even be built from. The oracle here builds each column the way a fixed-shape one
  is really stored — a rectangular numeric block, not an object array of per-row
  arrays — because the storage is what decides whether the comparison answers.
  The leg checks, on every generated column pair whose format carries NO
  variable-length marker — the pairs the spec routes to the flat comparison — that
  the predicate holds iff that comparison returns rather than raising. It also
  requires the sample to contain BOTH kinds of pair, so a leg that passed only
  because the grammar never generated one of them would fail instead. NO shape is
  excluded, the EMPTY-row one included: on a rectangular block the comparison never
  takes the truth value of an array, so there is no shape here whose partiality
  depends on the numpy version. Pairs holding an empty row are merely counted
  (`rows_nonempty`), and the recorded `numpy_version` says which numpy the counts
  and the verdict were measured on — this leg's counts are identical at the image's
  1.25.2 and at 2.2.6, so no figure here is a one-version accident.

  The leg also runs an EXHAUSTIVE sub-check
  (`exhaustive_flat_domain`, reported as `flat_domain_exhaustive`) over every column
  pair of 1-3 rows with per-row widths 0-3: at equal row counts — the modeled
  domain, since the real routine returns before the per-column loop when the two
  tables' row counts differ — a single disagreement fails the leg; at unequal row
  counts the predicate is narrower than numpy on purpose, and by how much is
  counted rather than argued away.

  LEG "abstraction-necessary" — why the callee is opaque rather than modeled as
  sequence equality. It measures, on the same grammar, the rows where structural
  equality of the two stored sequences DISAGREES with the real per-row test, and
  the whole columns whose reports differ between the two. A modeled-as-equality
  spec demands a difference at each of those rows; the real code reports none. The
  leg FAILS if it finds no such row, because then the grammar no longer reaches
  the divergence the abstraction exists to respect and the evidence would be
  stale.

GRAMMAR. Widened, and the widening is the point: per-row lengths are drawn
INDEPENDENTLY for the two columns, so the sample contains equal-length rows,
ragged broadcast-compatible rows (one side storing a single value — the shape the
real routine relates to every value on the other side) and incomparable rows. The
previous revision of this file drew one length per row for both columns "the
common-column shape FITS yields", which generated only the equal-length rows —
the grammar under which sequence equality and the real test never disagree.

stdlib + numpy only. Pinned seed: 14539 (also mapping.md).
"""
import json
import random
import sys

import numpy as np

SEED = 14539
N = 120_000

FORMATS = ["PJ(2)", "QJ(2)", "QD", "PI(2)", "QJ", "PB", "QK(3)", "J", "D", "10A"]


# ---- the real per-row closeness test, as the patch calls it -------------------
def real_rows_agree(xs, ys):
    """`np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)` on two stored rows.

    This is the interpretation of the model's opaque `rowsAgree`. It is a partial
    function: on a pair of lengths numpy cannot broadcast it RAISES instead of
    answering, which is the partiality `rowsComparable` describes.
    """
    return bool(np.allclose(np.array(xs), np.array(ys), rtol=0.0, atol=0.0))


def real_answers(xs, ys):
    """Whether the real per-row test has an answer at all on this pair of rows."""
    try:
        real_rows_agree(xs, ys)
        return True
    except ValueError:
        return False


def rows_comparable(xs, ys):
    """Transliteration of `rowsComparable` (Solution.lean pure region)."""
    return len(xs) == len(ys) or len(xs) == 1 or len(ys) == 1


def _object_column(rows):
    """Two columns as astropy stores them: object arrays of per-row arrays."""
    col = np.empty(len(rows), dtype=object)
    for i, r in enumerate(rows):
        col[i] = np.array(r)
    return col


def _fixed_shape_column(rows):
    """A column as astropy stores an ORDINARY fixed-shape one.

    NOT an object array of per-row arrays -- that is variable-length storage, and
    it is the storage the OTHER callee's domain leg is about. A fixed-shape column
    is a rectangular block: one row per row, the same number of values in each,
    held in a single numeric array. A pair of per-row lengths that is not
    rectangular has no such block, and numpy says so when asked to build one.
    """
    return np.asarray(rows, dtype=np.int64)


def real_flat_answers(a, b):
    """Whether the real FLAT element-by-element comparison answers on this pair.

    `np.where(arra != arrb)` (diff.py @ base_commit) is the comparison an ordinary
    fixed-shape column gets, and it is partial: it needs the two columns to be
    blocks of one shape. Where they are, the elementwise `!=` is elementwise and
    `np.where` reports -- however many values a row holds, which is the whole
    correction here: a column holding a small BLOCK of values per row is
    fixed-shape, is compared this way, and is reported on without complaint.
    Where the per-row lengths are ragged there is no block to compare and the
    storage cannot even be built. That partiality is what `rowsAreFixedShape`
    describes.
    """
    try:
        list(np.where(_fixed_shape_column(a) != _fixed_shape_column(b))[0])
        return True
    except (ValueError, TypeError):
        return False


def rows_are_fixed_shape(a, b):
    """Transliteration of `rowsAreFixedShape` (Solution.lean axioms region)."""
    if len(a) != len(b):
        return False
    wa = len(a[0]) if a else 0
    wb = len(b[0]) if b else 0
    if any(len(r) != wa for r in a) or any(len(r) != wb for r in b):
        return False
    return rows_comparable(a[0], b[0]) if a else True


def rows_nonempty(a, b):
    """Whether every row of both columns stores at least one value.

    Used to COUNT, not to exclude. A column pair with an empty row is not a shape
    any FITS column realizes — a fixed-shape column stores a value or a block of
    values per row, a variable-length one a sequence — so it is worth reporting how
    much of the sample it is. It is checked like every other shape: the flat
    comparison of two rectangular blocks reports elementwise and never takes the
    truth value of an array, so an empty row gives a width-0 block whose comparison
    answers (or, against an incompatible width, raises) the same way at any numpy.
    """
    return all(len(r) > 0 for r in a) and all(len(r) > 0 for r in b)


def exhaustive_flat_domain():
    """Every column pair of 1-3 rows with per-row widths 0-3, both row-count cases.

    Deterministic, and it separates the two cases because the spec's claim does:

      EQUAL row counts is the modeled domain. `TableDataDiff._diff` returns before
      the per-column loop when `len(self.a) != len(self.b)` (diff.py), and
      `columnDiffRowsContract` carries `arra.length = arrb.length` as a hypothesis,
      so this is the whole population on which a report is demanded. Here the
      predicate is asserted EXACT, and the count of disagreements is part of the
      `flat-domain` verdict.

      UNEQUAL row counts is outside it, and there the predicate is deliberately
      NARROWER than numpy: numpy broadcasts a one-row block across the rows of the
      other column, so `np.where` answers on e.g. `[[1]]` against `[[2], [2]]`,
      while `rowsAreFixedShape` (which demands equal row counts) says no. Nothing is
      demanded of a reporter there, so the narrowing costs no strength — but it is a
      real gap between predicate and routine, so it is COUNTED and reported rather
      than left for a reader to discover.
    """
    import itertools
    widths = range(0, 4)
    out = {"equal_pairs": 0, "equal_mismatches": 0, "equal_in_domain": 0,
           "unequal_pairs": 0, "unequal_predicate_narrower": 0,
           "unequal_predicate_wider": 0}
    examples = []
    for na in (1, 2, 3):
        for nb in (1, 2, 3):
            for la in itertools.product(widths, repeat=na):
                a = [[1] * k for k in la]
                for lb in itertools.product(widths, repeat=nb):
                    b = [[2] * k for k in lb]
                    pred = rows_are_fixed_shape(a, b)
                    real = real_flat_answers(a, b)
                    if na == nb:
                        out["equal_pairs"] += 1
                        if pred:
                            out["equal_in_domain"] += 1
                        if pred != real:
                            out["equal_mismatches"] += 1
                            if len(examples) < 5:
                                examples.append({"a": a, "b": b,
                                                 "rowsAreFixedShape": pred,
                                                 "real_flat_answers": real})
                    else:
                        out["unequal_pairs"] += 1
                        if real and not pred:
                            out["unequal_predicate_narrower"] += 1
                        elif pred and not real:
                            out["unequal_predicate_wider"] += 1
    if examples:
        out["equal_mismatch_examples"] = examples
    return out


def column_pair(rng, nrows, perturb):
    """Two columns of integer row-sequences, with per-row lengths drawn per COLUMN.

    Each row of the first column holds an integer sequence of a randomly chosen
    length. The second column's row usually copies it (optionally perturbed at one
    position, so some rows genuinely differ), but with fixed probability it is
    instead stored at a DIFFERENT length: a single value (broadcast-compatible with
    the other side, and the case the faithfulness of the model turns on), or an
    unrelated length (incomparable, which only the domain leg consumes).
    """
    a, b = [], []
    for _ in range(nrows):
        ln = rng.randint(0, 4)
        rowa = [rng.randint(-3, 3) for _ in range(ln)]
        roll = rng.random()
        if roll < 0.25:
            # ragged, broadcast-compatible: one stored value on the b side. Half
            # the time it repeats a value the a side stores, so the real test
            # ACCEPTS the pair while the two sequences are unequal as sequences.
            v = rowa[0] if (rowa and rng.random() < 0.5) else rng.randint(-3, 3)
            rowb = [v]
        elif roll < 0.35:
            rowb = [rng.randint(-3, 3) for _ in range(rng.randint(0, 4))]
        else:
            rowb = list(rowa)
            if perturb and rowa and rng.random() < 0.5:
                j = rng.randrange(len(rowa))
                rowb[j] = rowb[j] + rng.choice([-2, -1, 1, 2])
        a.append(rowa)
        b.append(rowb)
    return a, b


# ---- ORACLE: faithful post-patch VLA row comparison (real numpy.allclose) -----
def oracle(fmt, a, b):
    # The format predicate the patch installs; the ORACLE only reaches the VLA
    # branch when it holds (mirrors the real `elif` chain — the branches above it
    # are not in the modeled integer VLA domain).
    if not ("P" in fmt or "Q" in fmt):
        return None
    arra = np.empty(len(a), dtype=object)
    arrb = np.empty(len(b), dtype=object)
    for i, r in enumerate(a):
        arra[i] = np.array(r)
    for i, r in enumerate(b):
        arrb[i] = np.array(r)
    return [
        idx
        for idx in range(len(arra))
        if not np.allclose(arra[idx], arrb[idx], rtol=0.0, atol=0.0)
    ]


# ---- SHADOW: transliteration of implementation_columnDiffRows -----------------
def shadow(fmt, a, b):
    if not ("P" in fmt or "Q" in fmt):      # fmt.contains 'P' || fmt.contains 'Q'
        return None                         # the fixed-shape branch: opaque, unmodeled
    acc = []
    for idx in range(len(a)):               # for idx in List.range arra.length
        if not real_rows_agree(a[idx], b[idx]):   # !rowsAgree arra[idx]! arrb[idx]!
            acc.append(idx)                 # acc := acc ++ [idx]
    return acc


def old_model(fmt, a, b):
    """The PREVIOUS revision's model: rows compared by sequence equality."""
    if not ("P" in fmt or "Q" in fmt):
        return None
    return [idx for idx in range(len(a)) if a[idx] != b[idx]]


def main():
    rng = random.Random(SEED)
    report_checked = report_mismatch = 0
    domain_checked = domain_mismatch = 0
    ragged_rows = 0
    incomparable_rows = 0
    nonvla_skipped = 0
    flat_checked = flat_mismatch = flat_single_valued = 0
    flat_empty_row_counted = 0
    outside_domain_skipped = 0
    oldmodel_rows = oldmodel_columns = 0
    examples = []
    oldmodel_example = None

    for i in range(N):
        fmt = rng.choice(FORMATS)
        nrows = rng.randint(0, 6)
        a, b = column_pair(rng, nrows, perturb=(i % 3 != 0))

        # ---- LEG "domain": every row pair, comparable or not.
        all_comparable = True
        for xs, ys in zip(a, b):
            domain_checked += 1
            comp = rows_comparable(xs, ys)
            if comp != real_answers(xs, ys):
                domain_mismatch += 1
                if len(examples) < 10:
                    examples.append({"leg": "domain", "a": xs, "b": ys,
                                     "rowsComparable": comp,
                                     "real_test_answers": not comp})
            if not comp:
                incomparable_rows += 1
                all_comparable = False
            elif len(xs) != len(ys):
                ragged_rows += 1

        if not ("P" in fmt or "Q" in fmt):
            # ---- LEG "flat-domain": the shape of column the FLAT comparison has a
            # report for. This is the population the spec routes to it, so it is
            # the population the claim is about, and the grammar puts both kinds
            # here: columns storing one value per row (a report exists) and ragged
            # or multi-value ones (none does).
            nonvla_skipped += 1
            if not rows_nonempty(a, b):
                # The empty-row shape: unrealizable as a column, so counted — but
                # checked like any other, since a rectangular block's comparison
                # answers or raises the same way at any numpy version.
                flat_empty_row_counted += 1
            flat_checked += 1
            single = rows_are_fixed_shape(a, b)
            if single != real_flat_answers(a, b):
                flat_mismatch += 1
                if len(examples) < 10:
                    examples.append({"leg": "flat-domain", "fmt": fmt,
                                     "a": a, "b": b,
                                     "rowsAreFixedShape": single,
                                     "real_flat_answers": not single})
            if single:
                flat_single_valued += 1
            continue
        if not all_comparable:
            # Outside the contract's domain: the spec demands no report here, so
            # there is nothing to compare. Counted, not silently dropped.
            outside_domain_skipped += 1
            continue

        # ---- LEG "report": the report's shape, callee instantiated by the real test.
        o = oracle(fmt, a, b)
        s = shadow(fmt, a, b)
        report_checked += 1
        if o != s:
            report_mismatch += 1
            if len(examples) < 10:
                examples.append({"leg": "report", "fmt": fmt, "a": a, "b": b,
                                 "oracle": o, "shadow": s})

        # ---- LEG "abstraction-necessary": where sequence equality diverges.
        om = old_model(fmt, a, b)
        for xs, ys in zip(a, b):
            if (xs != ys) != (not real_rows_agree(xs, ys)):
                oldmodel_rows += 1
                # Report the CANONICAL shape of the divergence when one turns up:
                # several stored values on one side, a single one on the other.
                canonical = len(xs) > 1 and len(ys) == 1
                if oldmodel_example is None or (
                        canonical and not oldmodel_example["canonical_broadcast"]):
                    oldmodel_example = {
                        "row_a": xs, "row_b": ys,
                        "canonical_broadcast": canonical,
                        "sequence_equality_says_differ": xs != ys,
                        "real_test_says_differ": not real_rows_agree(xs, ys),
                    }
        if om != o:
            oldmodel_columns += 1

    exh = exhaustive_flat_domain()
    legs = {
        "report": "pass" if report_mismatch == 0 else "fail",
        "domain": "pass" if domain_mismatch == 0 else "fail",
        "flat-domain": "pass" if (flat_mismatch == 0 and flat_checked > 0
                                 and 0 < flat_single_valued < flat_checked
                                 and exh["equal_mismatches"] == 0
                                 and exh["equal_pairs"] > 0)
                       else "fail",
        "abstraction-necessary": "pass" if oldmodel_rows > 0 else "fail",
    }
    result = {
        "instance": "astropy__astropy-14539",
        "seed": SEED,
        "numpy_version": np.__version__,
        "n_generated": N,
        "legs": legs,
        "report_checked": report_checked,
        "report_mismatches": report_mismatch,
        "domain_rows_checked": domain_checked,
        "domain_mismatches": domain_mismatch,
        "ragged_comparable_rows": ragged_rows,
        "incomparable_rows": incomparable_rows,
        "nonvla_format_skipped": nonvla_skipped,
        "flat_domain_column_pairs_checked": flat_checked,
        "flat_domain_mismatches": flat_mismatch,
        "flat_domain_in_domain_pairs": flat_single_valued,
        "flat_domain_empty_row_pairs": flat_empty_row_counted,
        "flat_domain_exhaustive": exh,
        "outside_domain_skipped": outside_domain_skipped,
        "old_model_divergent_rows": oldmodel_rows,
        "old_model_divergent_columns": oldmodel_columns,
        "status": "pass" if all(v == "pass" for v in legs.values()) else "fail",
    }
    if oldmodel_example is not None:
        result["old_model_divergence_example"] = oldmodel_example
    if examples:
        result["examples"] = examples
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
