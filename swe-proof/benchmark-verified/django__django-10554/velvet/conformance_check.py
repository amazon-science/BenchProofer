#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-10554 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `resolveOrderingTerm` (the
per-ordering-term binding scan modeled in Solution.lean). There are NO axioms in
this bundle: every op is a concrete structural decision over the select-column
sequence, so the whole impl region is R/I-tagged (conf_skip=false).

ORACLE CHOICE — why we transliterate the patched control flow instead of running
the real `SQLCompiler.get_order_by`:
  Reaching the modeled `for … else` branch in the real `get_order_by` requires a
  fully configured DB backend, a combined (union/intersection/difference) query,
  resolved order-by expressions, and a populated `self.select` with real column
  objects — essentially the F2P Django test harness. Building that purely to read
  back which disposition each ordering term received is impractical and would not
  isolate the modeled behavior. Per the worker prompt, the ORACLE is the PATCHED
  term-binding control flow transliterated VERBATIM (compiler.py:343-364,
  post-patch):

      for idx, (sel_expr, _, col_alias) in enumerate(self.select):
          if is_ref and col_alias == src.refs:
              src = src.source
          elif col_alias:
              continue
          if src == sel_expr:
              resolved.set_source_expressions([RawSQL('%d' % (idx + 1), ())])
              break
      else:
          if col_alias:
              raise DatabaseError('ORDER BY term does not match any column ...')
          self.query.add_select_col(src)
          resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])

  The unchanged per-candidate resolution (`resolve_expression`,
  `get_source_expressions`, `RawSQL`, `compile`, `add_select_col`'s
  output-field bookkeeping) is folded out: each candidate is reduced to the two
  structural booleans the branch actually inspects — `aligns` (whether
  `src == sel_expr` for this term, after the ref/alias unwrapping) and
  `labelled` (`bool(col_alias)`). mapping.md §2/§3.

  CRUCIAL DISTINCT SEQUENCE: the scanned sequence is `self.select` (the
  COMPILER's result-set columns: extra select + fields + annotations) but the
  appended position is `len(self.query.select)` AFTER `add_select_col` — the
  QUERY's select tuple, a different sequence whose length may differ (e.g.
  `.extra(select=...)` grows `self.select` but not `self.query.select`). The
  model therefore carries the query-select pre-append length as a separate
  input `query_select_len`, and the appended disposition is
  `query_select_len + 1`, NOT `len(self.select) + 1`.

  The SHADOW is the model from Solution.lean (`firstAligned` / `lastLabelled` /
  `disposition`) transliterated to Python. SHADOW and ORACLE are differential-
  tested over randomly-generated non-empty candidate sequences and exhaustive
  small cases. Exit 0 iff zero disagreements. stdlib only.
"""
import random
import sys

SEED = 10554
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def first_aligned(cands):
    """`firstAligned` (Solution.lean): 0-based index of the first aligned
    candidate, or None."""
    for i, c in enumerate(cands):
        if c["aligns"]:
            return i
    return None


def last_labelled(cands):
    """`lastLabelled` (Solution.lean): trailing candidate's label, False if
    the sequence is empty."""
    if not cands:
        return False
    return cands[-1]["labelled"]


def disposition(cands, query_select_len):
    """`disposition` (Solution.lean): the modeled term-binding decision.
    Returns a tagged tuple matching the Lean `Disposition`. `query_select_len`
    is the QUERY's select-tuple length before any append (a sequence distinct
    from the scanned compiler candidates)."""
    fa = first_aligned(cands)
    if fa is not None:
        return ("position", fa + 1)               # (firstAligned …).map (· + 1)
    if last_labelled(cands):
        return ("rejected",)
    return ("appended", query_select_len + 1)


# ---- ORACLE: patched get_order_by term-binding flow transliterated --------

def oracle_disposition(cands, query_select_len):
    """Patched compiler.py:343-364 term binding, transliterated. Each candidate
    is (sel_expr-match, col_alias) folded to booleans aligns/labelled. The
    'src'/'is_ref' ref-unwrapping and the `elif col_alias: continue` skip are
    already folded into `aligns` (a candidate the loop skips or that does not
    match has aligns=False). `query_select_len` = len(self.query.select) BEFORE
    add_select_col (the query's select tuple, distinct from the compiler's
    self.select being scanned). Returns the tagged disposition; raising is
    modeled as the ('rejected',) tag (mapping.md §2)."""
    select = cands
    query_select = ["<col>"] * query_select_len   # self.query.select stand-in
    # the `for … else`:
    for idx, c in enumerate(select):
        if c["aligns"]:
            # `if src == sel_expr:` succeeds -> bind to idx+1 and break
            return ("position", idx + 1)
        # not a match -> continue scanning
    else:
        # no-break fall-through (post-patch split on col_alias of the trailing
        # candidate — the variable `col_alias` from the last loop iteration)
        col_alias = select[-1]["labelled"] if select else False
        if col_alias:
            return ("rejected",)                  # raise DatabaseError(...)
        # self.query.add_select_col(src): self.select += col,
        query_select = query_select + ["<src>"]
        # position = len(self.query.select) after the append
        return ("appended", len(query_select))


# ---- candidate-sequence generator -----------------------------------------

def gen_cands(rng):
    """A non-empty list of candidates (each with random aligns/labelled) plus
    an independent query-select length 0..8 — independent because the query's
    select tuple and the compiler's select list genuinely differ in length
    when extra-select / annotation columns are in play."""
    n = rng.randint(1, 6)
    cs = [{"aligns": rng.random() < 0.35, "labelled": rng.random() < 0.5}
          for _ in range(n)]
    return cs, rng.randint(0, 8)


def enumerate_small():
    """Exhaustive boundary cases: every (aligns,labelled) combination for
    sequences of length 1..3, crossed with query-select lengths 0..4 —
    covers the discriminating no-match branch with labelled vs unlabelled
    trailing column, first-match positioning, and query-select lengths both
    shorter and longer than the scanned candidate list."""
    out = []
    for length in (1, 2, 3):
        for mask in range(4 ** length):
            cs = []
            m = mask
            for _ in range(length):
                bits = m % 4
                m //= 4
                cs.append({"aligns": bool(bits & 1), "labelled": bool(bits & 2)})
            for qlen in range(5):
                out.append((cs, qlen))
    return out


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for cs, qlen in enumerate_small():
        count += 1
        if disposition(cs, qlen) != oracle_disposition(cs, qlen):
            disagreements.append(
                (cs, qlen, disposition(cs, qlen), oracle_disposition(cs, qlen)))

    for _ in range(N_FUZZ):
        cs, qlen = gen_cands(rng)
        count += 1
        if disposition(cs, qlen) != oracle_disposition(cs, qlen):
            disagreements.append(
                (cs, qlen, disposition(cs, qlen), oracle_disposition(cs, qlen)))
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d cases:"
              % (len(disagreements), count))
        for cs, qlen, sh, orc in disagreements[:8]:
            print("  cands=%r qlen=%d shadow=%r oracle=%r"
                  % (cs, qlen, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveOrderingTerm (firstAligned/"
          "lastLabelled/disposition over candidates + query-select length) "
          "agrees with the patched get_order_by term-binding flow on %d cases "
          "(420 exhaustive + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
