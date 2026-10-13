"""properties.py — G-PBT falsification battery for astropy__astropy-14539 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over BOTH kinds of column):

  columnDiffRows (fmt : List Char) (arra arrb : List (List Int))
                 (hcmp : every stored row is a pair the per-row test can relate)
                 (hfix : a column of non-variable-length format stores one value
                         per row) : List Nat
      isVariableLengthFormat fmt  -> result = rowDiffIndices arra arrb hcmp
            = ((List.finRange arra.length).filter
                 (fun i => !rowsAgree arra[i]! arrb[i]! (hcmp i i.isLt))).map Fin.val
      ¬isVariableLengthFormat fmt -> result = elementwiseDiff arra arrb (hfix ‹..›)
    demanded for every pair of columns with equal row counts. Each of the two
    unchanged callees is applicable only on its own shape of input, and that
    shape is an ARGUMENT of the callee — handed to the reporter, and through the
    reporter to the callee, rather than assumed on the side. So a reporter is
    entitled to ask each callee exactly about the inputs it was given, and about
    nothing else.

  A column stores, per row, a sequence of integer values. A VARIABLE-LENGTH
  column's rows may hold sequences of different lengths, and comparing two such
  columns is a row-by-row question: report the row indices at which the per-row
  closeness test — the UNCHANGED library routine, applied once per row to the two
  WHOLE stored sequences — does not report the two rows as agreeing. An ORDINARY
  FIXED-SHAPE column is not compared that way at all — it is compared by the
  flat element-by-element routine, which this behavior does not modify.

  Load-bearing postcondition clauses (in ``problem_spec_columnDiffRows``):

    (P-VLA)   isVariableLengthFormat fmt -> result = rowDiffIndices arra arrb
              hcmp. A row is reported EXACTLY when the per-row closeness test,
              applied to its whole stored sequence in the first column and its
              whole stored sequence in the second, does not accept them; and rows
              are reported in increasing index order over the FULL row range
              `List.finRange arra.length` — the positions OF the first column, so
              that every row the report is built from is a stored one. This pins
              the membership criterion (the
              test's own verdict, negated, on the two whole sequences — genuine
              dependence on BOTH `arra` and `arrb`), the domain (every row, none
              dropped), and the order. It does NOT pin what that test answers:
              `rowsAgree` is `opaque`, so which pairs of sequences count as
              agreeing — under which tolerance, at which magnitudes, across which
              pairs of lengths — is left to the callee this behavior only calls.

    (P-FIX)   ¬isVariableLengthFormat fmt -> result = elementwiseDiff arra arrb
              (hfix ‹..›). A fixed-shape column's report is EXACTLY what the
              unchanged flat
              routine returns — whatever that is. The clause says nothing about
              that routine's VALUE (it too is `opaque`, and pinning its value
              would over-claim about a callee this behavior does not touch); what
              it pins is that the fixed-shape column gets THAT answer and not
              some other one, and in particular is not re-routed through the
              row-wise comparison.

    (P-DOM)   the two callees' domains, each carried as an ARGUMENT of the
              reporter and of the callee rather than as a side condition. Neither
              modeled routine is total. The per-row test, presented with two
              stored sequences whose lengths are neither equal nor
              one-against-many, has no verdict to give, and a row like that has no
              differing-or-not answer to report; the flat comparison, presented
              with a column whose rows store several values, has no report to
              give at all. Both domains are exactly what the real routines accept
              — measured, not assumed (mapping.md §2).

              Making each domain an argument is what keeps the demand honest in
              BOTH directions. Read as a hypothesis it would only weaken the
              demand, and it would leave a reporter free to consult a callee
              anywhere it liked: at a row it was not given, at a column of the
              wrong shape, or twice at arguments chosen so the two answers cancel.
              Read as an argument, asking a callee about anything but the input
              the reporter was handed is not a thing a rival can write down. The
              admissibility lane below is what shows the demand is still inhabited
              at reporting-shaped inputs, including a RAGGED one, on BOTH clauses.

  (P-FIX) is what makes (P-VLA) a claim about variable-length columns
  SPECIFICALLY rather than about columns in general. Without it the two clauses
  collapse into "row-wise comparison is an acceptable answer everywhere", which
  is satisfied by an implementation that has lost the distinction the behavior
  exists to draw — see the FIXED-SHAPE lane below, which is the lane this battery
  had missing.

  The per-row test's IDENTITY is the other thing (P-VLA) pins, and it is what
  this revision of the spec added. An earlier revision modeled the per-row test
  as structural inequality on `List Int` — `arra[idx]! ≠ arrb[idx]!` — which is
  not what the code computes: the code calls a numeric closeness routine that
  relates a one-value sequence to every value on the other side, so at the ragged
  row [1, 1] vs [1] the old spec DEMANDED a difference the real code does not
  report. Modeling that routine as an unchanged opaque callee, and moving its
  domain into (P-DOM), is the repair; ``compare-rows-by-structural-equality``
  is the old model turned into a rival, and it is the only case in the battery
  that separates the two.

ADVERSARIAL READ of the nagini case classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — EXPRESSIBLE and CARRIED (``frame-*``). An
    earlier revision of this file recorded this lane as VACUOUS, on the reasoning
    that Lean is referentially transparent so the input columns carry no heap
    permission, no read-only half-permission to overwrite and no aliasing to
    exploit. The PERMISSION mechanism is indeed absent, but that is the rejection
    MECHANISM, not the defect the nagini case tests: what that rival actually
    attacks is a comparison performed against a CLOBBERED input rather than the
    input it was given. That has a direct expressible instance here — take a
    local copy of the first column, overwrite one row's stored sequence in the
    copy, and compare the copy — and it is REJECTED, with a plain-evaluation
    witness that discriminates. It is carried as ``frame-compare-clobbered-copy``.
    Lean's referential transparency removes the aliasing, not the defect: the
    write is behaviorally wrong (an identical column reports a spurious
    difference at the clobbered row), which is exactly what the nagini
    ``refinement`` said made the store wrong independently of the permission
    artifact.

  * ROUTING / MIS-SELECTION — EXPRESSIBLE and CARRIED, in BOTH directions, and
    this is where the battery changed. Mis-selection has two halves, because the
    selector picks between two DIFFERENT comparisons:

      (a) a variable-length column sent to the flat fixed-shape routine — the
          pre-patch bug itself (``route-p-only-misses-Q``,
          ``route-q-only-misses-P``, ``route-always-fixed-shape``);
      (b) a FIXED-SHAPE column sent to the row-wise comparison, or given some
          other answer entirely — the mirror image (``route-*-to-rowwise``,
          ``always-rowwise-ignores-format``, ``fixed-shape-report-*``).

    An earlier revision of this file carried only (a), and recorded (b) as
    UNCONSTRAINED BY CONSTRUCTION on the grounds that the obligation's hypothesis
    admitted only recognized formats. That reasoning was wrong in a way that
    mattered: a selector that OVER-recognizes is just as mis-selecting as one that
    under-recognizes, and a battery that tests only under-recognition certifies a
    spec under which "recognize everything" is a correct answer. Both halves are
    now carried, and (P-FIX) is the clause that rejects half (b).

    The branch selector is a binder of ``problem_spec_columnDiffRows`` and is
    instantiated at a concrete value in every witness. Because the fixed-shape
    answer is an OPAQUE term ``decide`` cannot reduce, the routing witnesses in
    both directions are HYPOTHESIS-CONDITIONED: they state the refutation at the
    routed input under a hypothesis about the opaque routine's value there (the
    value the spec demands, or the value the rival produces). Each ELABORATES
    against its rival, FAILS on the frozen solution, and the gate's consistency
    probe cannot derive `False` from the hypothesis (satisfiable — no tactic
    refutes an opaque atom). The nagini raise-vs-return EFFECT of the real
    fixed-shape path is what collapses under referential transparency; the
    mis-selection VALUE defect does not.

    ``route-always-fixed-shape`` is NOT redundant with the two near-misses, as an
    earlier revision claimed: each near-miss still recognizes one marker and is
    therefore refutable only at the marker it misses, so a spec constraining the
    result at only ONE marker would reject both while admitting the unconditional
    one. Its witness is stated at a format carrying BOTH markers, the one input
    class where the near-misses agree with the frozen impl and only the
    marker-blind rival diverges. See ``_WIT_AEW``.

  * UNGROUNDED-ORACLE ECHO — the lane to read carefully now that BOTH modeled
    callees are opaque, since "the spec mentions an opaque function" is the shape
    an answer-key echo takes. It is still not one, and the reason is structural:
    an echo spec would let the implementation return an opaque function OF THE
    WHOLE PROBLEM — some `answer fmt arra arrb` — so that returning it is
    vacuously correct and nothing about the row report is claimed. Neither clause
    does that.

      - (P-VLA) is GROUNDED in the inputs at the level the patch operates on:
        `rowDiffIndices arra arrb hcmp` is a `List.filter` over the concrete row
        positions of the first column,
        so WHICH rows may be reported, HOW MANY, and IN WHAT ORDER are all fixed
        by the input, and the opaque callee appears only INSIDE the filter's
        predicate, applied once per row to the caller's own two stored sequences
        at that row. An impl may not choose the rows, drop one, reorder them, or
        answer per row from anything but those two sequences — which is exactly
        what the seven row-wise rivals demonstrate, every one of them refuted
        under a hypothesis fixing the callee's value at named rows rather than by
        exploiting the callee's freedom.
      - (P-FIX) equates the fixed-shape result to an opaque term, but that term is
        the UNCHANGED callee for the branch this patch does not touch; its value
        is never claimed, and an impl "echoing" it THERE is precisely the correct
        behavior. What (P-FIX) forbids is echoing it on the OTHER branch, or
        answering the fixed-shape branch with anything else.

    The distinction is measured, not argued: an echo rival that returns a fresh
    whole-problem oracle (an opaque `answerKey fmt arra arrb`, or the row-wise
    branch replaced by a guarded call to the flat routine) does NOT verify against this
    spec — the row-wise branch has to compute the filter. In this lane's place the
    battery carries honest cheapest / reshaped POSITIVE CONTROLS (``pos-*``).

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is a substantive attack surface here.
    Rivals correct on part of the row domain but diverging elsewhere: one that
    reports the EQUAL rows instead of the unequal ones (the spurious-difference
    failure mode, generalized), one that reports every row, one that drops the
    first row, one that compares a column with ITSELF (ignoring `arrb`). (P-VLA)
    rejects each, and their witnesses probe distinct inputs varying both `arra`
    and `arrb`. The FIXED-SHAPE lane is the partial-domain attack one level up:
    those rivals are correct on the whole variable-length half of the domain and
    diverge only on the other kind of column.

  * WHOLE-SEQUENCE GRANULARITY — APPLIES, and now has TWO rivals, because the
    per-row side of (P-VLA) has two independent things to get wrong. Every
    membership rival above corrupts WHICH rows are considered; none corrupts HOW a
    row's two stored sequences are handed to the test, so all of them would still
    be rejected by a spec that fed the test a per-row proxy or that used a
    different test entirely. The two rivals that do:

      - ``compare-first-element-only`` — the ARGUMENT attack: the right test,
        applied to the wrong thing (each row's one-value prefix instead of its
        whole stored sequence). Refuted at two rows agreeing on their first value
        and differing later, an input every other rival handles correctly.
      - ``compare-rows-by-structural-equality`` — the TEST-IDENTITY attack: the
        right arguments, the wrong test (sequence equality instead of the numeric
        closeness routine the code calls). Refuted at a ragged row the real
        routine accepts. This is the rival the previous revision of this spec
        WAS, and no other case in the battery rejects it.

    Both keep the row domain and the report order exactly the frozen impl's, so
    neither rejection can be attributed to any other clause.

  * RAGGED-ROW ADMISSION — CARRIED, one rival, and it is the guard that keeps the
    faithfulness repair from being undone from the other side. The repair gave the
    per-row test its comparability domain, and the way to abuse a domain is to read
    it as licence to ignore the inputs it does not exclude:
    ``skip-ragged-rows-from-the-report`` keeps the row range, the order, the test
    and its arguments, and reports only the rows whose two stored sequences have
    EQUAL length. (P-DOM) excludes the rows the per-row test cannot answer at all
    (measured: it raises there), not the rows whose sequences differ in length —
    a single stored value against a longer sequence is a row it answers readily.
    So the two ragged rivals pin the class from both directions at the same input
    shape: ``compare-rows-by-structural-equality`` is refuted at a ragged row the
    test ACCEPTS (spec [], rival [0]) and this one at a ragged row it REJECTS
    (spec [0], rival []). A spec that quantified its row-wise clause over
    equal-length rows only would still reject every other rival in the battery
    while admitting this one.

  * ORDER — APPLIES, and is a SEPARATE half of (P-VLA) from membership. Every
    membership rival changes WHICH rows are reported, so all of them would still
    be rejected by a spec that pinned only the membership set. The order
    requirement is exercised by exactly one rival,
    ``report-rows-in-decreasing-order``, whose membership set is correct and whose
    order is reversed.

  * ADMISSIBILITY — CARRIED, and it is now load-bearing rather than hygienic,
    because the obligation carries TWO domain arguments. (P-DOM) hands the
    reporter the comparability of its rows and, on the fixed-shape branch, the
    single-valuedness of its columns; a domain that excluded the F2P's own inputs
    would make the whole obligation vacuous — the classic way a faithfulness
    repair over-corrects. Being arguments rather than hypotheses does not make
    them safe from that: an unsatisfiable argument is a report nobody can ask for,
    which is the same vacuity reached by a different door. The admissibility case
    discharges the postcondition at FIVE concrete reporting-shaped points as
    `have`s, before closing the frozen obligation verbatim, and the points are
    chosen to cover the ways the demand could have been emptied:

      - both clauses: three variable-length points (empty report, both-rows
        report, first-row-only report) and one fixed-shape point whose demanded
        answer is the unchanged flat routine's own result, so (P-FIX) is shown
        INHABITED and not merely non-contradictory;
      - (P-DOM) specifically: a RAGGED point, two stored sequences of different
        lengths at the same row, which `rowsComparable` admits and the real test
        accepts. This is the input class the faithfulness review found, and it is
        inside the demand — the new hypothesis did not fence it out.

    A `∀`-obligation-only positive (such as ``pos-let``) attests none of this: it
    never evaluates the postcondition anywhere. Each `have` is controlled against
    the FALSE claim at the same input and against `False` from its own hypothesis
    group; see the nine measured controls at ``_ADM_HAVES``. See
    ``adm-obligation-satisfiable-at-report-shaped-inputs``.

  * DOMAIN BINDER (`arrb.length` vs `arra.length`) — DELIBERATELY NOT CARRIED, and
    the reason is measured, not assumed. Iterating the row range over
    `arrb.length` instead of `arra.length` looks like an attack on the domain half
    of (P-VLA), but the frozen obligation's hypothesis is
    `arra.length = arrb.length`, so on the whole admitted domain the two ranges are
    EQUAL and such a rival is observably identical to the frozen impl. Under the
    current model it is not merely a tactic mismatch: walking the positions of the
    SECOND column means the per-row test's comparability argument no longer arrives
    with the position, since what the reporter is handed is comparability at the
    positions of the FIRST column, so the reshape has to re-derive it from the
    length hypothesis (`hcmp i.val (by omega)`) before it can ask about a row at
    all. Re-measured against the current model: the frozen script does NOT close
    it (exit 1 — the Route-B helper no longer matches the reshaped range). What
    closes it is naming the length hypothesis — the FIRST of the obligation's
    three binders, `intro fmt arra arrb hlen hcmp hfix` — and rewriting by it
    after the unfold (`rw [← hlen]`, or folding `← hlen` into the
    `simp only [hc, dif_pos]` step). So it is a correct reshape, not a rival:
    carrying it as an ``expect="reject"`` case would be vacuous, attesting only to
    a tactic mismatch. Recorded with the spelling that works so a later port
    neither re-adds it as a rival nor concludes from a failed frozen script that
    the spec rejects it.

  * FIXED-SHAPE BRANCH — CARRIED, and the record of why it must be. An earlier
    revision of this file recorded this branch as "UNCONSTRAINED BY CONSTRUCTION,
    and recorded here so no later port mistakes it for a spec hole", on the
    strength of a measurement: an obligation hypothesized over recognized formats
    only, so a rival returning ANYTHING on the other branch — including `[]` —
    satisfied the postcondition and verified. The measurement was right and the
    conclusion was not. Leaving that branch free does not merely under-test the
    other half of the routing decision; it also releases the SELECTOR, because a
    selector that sends every column to the row-wise comparison is then correct.
    That is a wrong implementation of this behavior — it re-introduces on ordinary
    columns exactly the comparison the fixed-shape path exists to avoid, and it
    does not resolve — and it verified. The spec now pins both branches (P-FIX),
    and this battery carries five rivals over the fixed-shape branch's VALUE:
    ``always-rowwise-ignores-format``, ``route-any-format-to-rowwise``,
    ``route-extra-marker-to-rowwise``, ``fixed-shape-report-empty``, and
    ``fixed-shape-report-every-row``. Note what (P-FIX) does NOT do: it makes no
    claim about the opaque routine's value, so it over-fits nothing about the
    unchanged callee.

  * CORRECT RESHAPES that the spec ADMITS, measured rather than assumed, so a
    later port does not read a tactic failure as a spec rejection. FOUR are
    carried as positive controls below, and they are chosen to cover the shapes a
    port is likeliest to try: the two-branch one-liner that returns the row-wise
    helper directly (``pos-cheap-two-branch-oneliner``), the same loop with the
    row positions bound to a local (``pos-let-local-reshape-admiss``), and the
    branches written in the opposite order behind a negated selector
    (``pos-branch-reorder``), which also answers the fixed-shape branch first and
    so re-derives the flat routine's shape argument from the negated guard rather
    than from the positive one. Each was measured, and the reorder needed its own
    script (`simp only [hc, dif_pos, Bool.not_true, ...]`): a reshape that fails
    under the frozen script is the shape that gets misfiled as SPEC-TOO-STRONG,
    which is why each is carried as a case rather than as a note.

  * A RESHAPE THE SPEC DOES *NOT* ADMIT, recorded because it is the honest cost of
    modeling the per-row test as an opaque callee. Calling that test with its two
    arguments SWAPPED — `!rowsAgree arrb[i.val]! arra[i.val]! ..` — is behaviorally
    identical in the repository, because the real routine is symmetric at the
    tolerances the comparison uses. Under the current model such a call also has
    to supply the swapped pair's comparability, which the reporter is not handed
    and must derive (`rowsComparable` is symmetric, so `simp [rowsComparable]` and
    `omega` do it). Even so this spec does not admit the reshape: re-measured, the
    swapped impl fails under the frozen script, because
    `rowsAgree x y ..` and `rowsAgree y x ..` are DISTINCT opaque atoms. That is
    deliberate and it is not a defect of the shape this battery reports: the
    alternative is to assume the callee's symmetry, which would be an unfounded
    property claimed of an unchanged callee (the thing G-AX exists to stop) and
    would license every argument-order confusion in a routine where the order
    does matter. It is NOT carried as an ``expect="reject"`` case, because it is a
    CORRECT implementation and a reject case for it would be unsound; it is
    recorded here so a later port neither adds it as a rival nor reads its
    rejection as evidence the spec over-fits the modeled behavior.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form —
so a rejection alone attributes nothing to the spec. Every ``expect="reject"``
case therefore carries a Lean snippet proving the rival CONTRADICTS the spec at
one concrete input.

Every witness in this revision is HYPOTHESIS-CONDITIONED, and that changed with
the model: nothing here evaluates by ``decide`` any more, because both modeled
callees are opaque. The two kinds of hypothesis are:

  * the PER-ROW test's value at the rows the witness names, e.g.
    ``rowsAgree [1, 2] [3, 4] = false``. Every such value stated anywhere in this
    file is the value the REAL routine returns on that pair of stored sequences,
    measured (`np.allclose(xs, ys, rtol=0, atol=0)`, mapping.md §2) rather than
    assumed — including the ragged pairs, which is what makes the ragged
    refutation a claim about an input that actually occurs;
  * the FLAT routine's value at the routed input, e.g.
    ``elementwiseDiff [[1]] [[3]] (by decide) ≠ [0]``, used by the routing
    witnesses in both directions because on exactly one side of a routing
    disagreement the value is that opaque routine's. The routed input stores one
    value per row, which is what makes the flat routine askable there at all — a
    routing claim can only be stated where both destinations have an answer.

Both kinds of hypothesis name the callee's DOMAIN argument alongside its two
value arguments, discharged by decision at the concrete rows the witness fixes.
That is not decoration: it is what makes the hypothesis about the very
application the report is built from, since Lean identifies any two proofs of the
same domain fact.

A conditioned witness attests less than an evaluated one, so each was checked
three ways: it ELABORATES against its rival, it FAILS on the frozen solution (so
it discriminates rather than asserting a tautology), and its hypothesis group is
SATISFIABLE — the gate's consistency probe cannot derive `False` from it, since
each group fixes distinct applications of an opaque callee. All three checks are
run by the gate, and every one of the twenty-one cases was measured locally before
shipping: the variant build for all of them, plus the two witness builds and the
consistency probe for each of the seventeen reject cases.

AXIOM lane: DROPPED. The nagini bundle's ``AXIOM_TESTS`` belong to G-AX, which
the G-PBT spec lane ignores; this bundle consumes no callee axiom (meta.json:
G-AX skip — the two opaque callees are declared with signatures ONLY, and no
axiom, `sorry`, or assumed property about either is stated anywhere, in the
solution or in any case here; every witness that needs a value of one states it
as a local hypothesis of that witness and pays for it with the consistency
probe).
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14539"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The reporter's SIGNATURE, shared by every case. Both modeled callees carry
# their domain as a proof ARGUMENT, so the reporter is handed the two domain
# facts and every case is written against the same header. The proof arguments
# are erased at run time, so no case pays a test for carrying them.
_SIG_DO = (
    "def implementation_columnDiffRows\n"
    "    (fmt : List Char) (arra arrb : List (List Int))\n"
    "    (hcmp : \u2200 idx, idx < arra.length \u2192 rowsComparable arra[idx]! arrb[idx]! = true)\n"
    "    (hfix : isVariableLengthFormat fmt = false \u2192 rowsAreFixedShape arra arrb = true) :\n"
    "    List Nat := Id.run do\n"
)
_SIG_PURE = _SIG_DO.replace("List Nat := Id.run do\n", "List Nat :=\n")

# The flat routine is only applicable to a pair of columns whose rows each store
# one value, and only a reporter holding that fact may consult it. A case whose
# selector is NOT the format predicate cannot obtain the fact from `hfix`, so it
# TESTS for it, which is what makes such a case expressible at all.
_FLAT_GUARDED = (
    "    if hg : rowsAreFixedShape arra arrb = true then\n"
    "      return elementwiseDiff arra arrb hg\n"
    "    else\n"
    "      return []"
)
# The flat routine reached through the format predicate itself: `hfix` supplies
# the fact, exactly as in the frozen impl.
_FLAT_VIA_HFIX = (
    "    return elementwiseDiff arra arrb "
    "(hfix (by simpa [isVariableLengthFormat] using hb))"
)

# The FULL body of the impl region: every impl reshape lands entirely inside it.
_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX

# The FULL body of the proof region (Route-B helper + the obligation). A case
# that reshapes the branch layout reproves inside here; the
# `theorem correct_columnDiffRows` STATEMENT is preserved byte-identically (only
# tactic bodies change — `columnDiffRows_loop` stays in the frozen declaration
# set, so no NEW theorem/lemma is introduced).
_PROOF = (
    "/-- The conditional-append loop over `l`, generalized over the accumulator and\n"
    "over the row predicate, computes `init` followed by the filtered positions\n"
    "(Route B helper). -/\n"
    "theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))\n"
    "    (init : List Nat) :\n"
    "      Id.run (forIn l init (fun i r =>\n"
    "        (if p i then ForInStep.yield (r ++ [i.val])\n"
    "         else ForInStep.yield r : Id (ForInStep (List Nat)))))\n"
    "      = init ++ (l.filter p).map Fin.val := by\n"
    "  induction l generalizing init with\n"
    "  | nil => simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons, List.filter_cons]\n"
    "    simp only [Id.run, bind] at ih ⊢\n"
    "    by_cases h : p a = true\n"
    "    · rw [if_pos h]; simp only [ih, h, if_true, List.map_cons]; simp [List.append_assoc]\n"
    "    · rw [if_neg h]; simp only [Bool.not_eq_true] at h; simp only [ih, h]; simp\n"
    "\n"
    "theorem correct_columnDiffRows :\n"
    "    columnDiffRowsContract implementation_columnDiffRows := by\n"
    "  intro fmt arra arrb _ hcmp hfix\n"
    "  unfold problem_spec_columnDiffRows implementation_columnDiffRows\n"
    "    isVariableLengthFormat rowDiffIndices\n"
    "  by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true\n"
    "  · simp only [hc, dif_pos]\n"
    "    have h2 : (Id.run (do\n"
    "        let r ← forIn (List.finRange arra.length) ([] : List Nat) fun i r =>\n"
    "              if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then do\n"
    "                pure PUnit.unit\n"
    "                pure (ForInStep.yield (r ++ [i.val]))\n"
    "              else do\n"
    "                pure PUnit.unit\n"
    "                pure (ForInStep.yield r)\n"
    "        pure r))\n"
    "        = Id.run (forIn (List.finRange arra.length) ([] : List Nat) (fun i r =>\n"
    "          (if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "             ForInStep.yield (r ++ [i.val])\n"
    "           else ForInStep.yield r : Id (ForInStep (List Nat))))) := rfl\n"
    "    rw [h2, columnDiffRows_loop]\n"
    "    simp\n"
    "  · simp only [hc]\n"
    "    rfl"
)

# The obligation STATEMENT, split out so every re-proving case reuses it verbatim
# rather than retyping it: variant_scope requires the `theorem correct_*`
# statement byte-identical, and a retyped copy is the one thing in this file that
# silently drifts. `_HELPER` is the frozen Route-B lemma, carried unchanged by
# every case so the declaration set never grows.
_STMT_AT = _PROOF.index("theorem correct_columnDiffRows")
_HELPER = _PROOF[:_STMT_AT]
_STMT = _PROOF[_STMT_AT:_PROOF.index(":= by\n", _STMT_AT) + len(":= by\n")]
if "columnDiffRowsContract implementation_columnDiffRows" not in _STMT:
    raise AssertionError("drift: obligation statement anchor")
# The obligation's statement is now a single application of `columnDiffRowsContract`,
# and that `def` — with its `∀ fmt` and its one hypothesis — lives in the SPEC VIEW.
# That is what this battery leans on: the quantification over FORMATS and the
# hypothesis list are no longer written in the (elided) proof region where a case
# could restate them, but in the shared spec, where `same_spec` holds them fixed.
# A case may still reprove freely; what it can no longer do is narrow the set of
# formats its impl is answerable for.
_CONTRACT_ANCHOR = (
    "def columnDiffRowsContract\n"
    "    (report : (fmt : List Char) → (arra arrb : List (List Int)) →\n"
    "      (∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true) →\n"
    "      (isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) →\n"
    "      List Nat) : Prop :=\n"
    "  ∀ (fmt : List Char) (arra arrb : List (List Int)),\n"
    "    arra.length = arrb.length →\n"
    "    ∀ (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)\n"
    "      (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true),\n"
    "      problem_spec_columnDiffRows fmt arra arrb hcmp hfix (report fmt arra arrb hcmp hfix)"
)
if _CONTRACT_ANCHOR not in _BASE:
    raise AssertionError("drift: contract def anchor")



# === POSITIVE CONTROLS (soundness) — structurally different but CORRECT ======
# implementations that MUST verify. If a faithful correct implementation cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG.

# --- pos-cheap: the cheapest impl that still DRAWS THE DISTINCTION. -----------
# Branch on the selector and hand each kind of column its own answer directly:
# the grounded row-difference set on one side, the unchanged flat routine's
# result on the other. No loop at all, so it is structurally as far from the
# frozen impl as a correct impl of this behavior can get — and it must verify,
# because both clauses hold definitionally. Note what is NOT a positive control
# any more: the one-liner that returns `rowDiffIndices arra arrb hcmp`
# UNCONDITIONALLY. Under (P-VLA) alone it was correct and was carried here; under
# (P-FIX) it is a rival (`always-rowwise-ignores-format`), because it applies the
# row-wise comparison to a fixed-shape column.
_CHEAP_IMPL = _SIG_PURE + (
    "  if h : isVariableLengthFormat fmt = true then rowDiffIndices arra arrb hcmp\n"
    "  else elementwiseDiff arra arrb (hfix (by simpa using h))"
)
_CHEAP_PROOF = _HELPER + _STMT + (
    "  intro fmt arra arrb _ hcmp hfix\n"
    "  unfold problem_spec_columnDiffRows implementation_columnDiffRows\n"
    "  by_cases hc : isVariableLengthFormat fmt = true\n"
    "  \u00b7 rw [dif_pos hc, dif_pos hc]\n"
    "  \u00b7 rw [dif_neg hc, dif_neg hc]"
)
POS_CHEAP = _swap(_swap(_BASE, _IMPL, _CHEAP_IMPL), _PROOF, _CHEAP_PROOF)

# --- pos-let: bind the list of row positions to a local (gold branch order). --
# A local-variable reshape that keeps the row-wise loop, the per-row call with its
# domain argument, and the branch order identical to the frozen impl, so the
# frozen proof closes it VERBATIM. Same
# value on every input; must verify (else SPEC-TOO-STRONG). This is a SOUNDNESS
# control only: it discharges the same `∀`-obligation and never evaluates the
# postcondition at any concrete input, so it does not test satisfiability. The
# admissibility lane is carried by its own case
# (`adm-obligation-satisfiable-at-report-shaped-inputs`).
_LET_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let idxs := List.finRange arra.length\n"
    "    let mut acc : List Nat := []\n"
    "    for i in idxs do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
POS_LET = _swap(_BASE, _IMPL, _LET_IMPL)

# --- adm-obligation-satisfiable: a REAL admissibility case. -------------------
# The impl region is left FROZEN; only the proof region gains five `have`s that
# DISCHARGE the postcondition at concrete inputs shaped like the ones the F2P
# exercises — four over the row-wise clause, one over the fixed-shape clause —
# before the frozen general proof runs verbatim.
#
# This is the lane a total carrier still needs. The obligation's hypotheses (equal
# row counts, and rows the per-row test can compare) cannot be too strong in the
# nagini sense, but the analogue is the obligation being UNSATISFIABLE at an
# F2P-shaped point: a `problem_spec` no concrete input can discharge (an
# inconsistent or vacuously-unreachable postcondition) would still let the general
# theorem close for the wrong reason. Discharging it at named points proves it is
# genuinely inhabited there, which the general `∀`-proof alone does not show.
#
# Each row-wise point pins the demanded report to a CONCRETE list rather than to
# the impl's own value, which is the stronger form: it says what the spec DEMANDS
# at that input, not merely that the impl and the spec agree there. Since the
# per-row closeness test is an unchanged opaque callee, no input decides it, so
# each point states what that routine answers at the rows it names. Every value
# stated is the value the REAL routine returns on that pair —
# `np.allclose(xs, ys, rtol=0, atol=0)`, mapping.md §2, measured with numpy — so
# the point is an input that actually occurs, not a fictional one. Five points:
#   * two identical rows under a 64-bit marker  -> the report must be EMPTY;
#   * the same two rows made to differ          -> the report must be BOTH rows;
#   * a first-row-only difference under the 32-bit marker -> report is row 0 only;
#   * a RAGGED row the real per-row test accepts by broadcasting (a two-value
#     sequence against a one-value sequence) -> the report must be EMPTY. This is
#     the input class the faithfulness review found: the rows are not equal as
#     sequences, the real routine reports them as agreeing, and the spec demands
#     the empty report there;
#   * a format carrying NEITHER marker -> the fixed-shape clause, whose demanded
#     answer is the unchanged flat routine's own result. This point is what shows
#     (P-FIX) is INHABITED rather than merely non-contradictory: it cannot be
#     decided (the value is opaque) but it can be discharged, and an impl is
#     obliged to produce exactly it.
#
# None of these close by `decide` any more (an opaque callee does not evaluate),
# and `simp`-closed `have`s under hypotheses are exactly the shape a vacuous one
# takes, so all five were controlled with real builds before being carried. Nine
# controls, every one measured to FAIL (exit 1):
#   * the same tactic on the FALSE claim at each of the five inputs — `[0]` for
#     the identical-row point, `[]` for the both-rows-differ point, `[]` for the
#     first-row-only point, `[0]` for the ragged point, `[]` for the fixed-shape
#     point — so the tactic is not closing these goals regardless of the value
#     claimed;
#   * `False` from each of the four hypothesis groups
#     (`first | simp_all | omega | decide`), so no point is discharged out of a
#     contradictory context.
# So each `have` discharges a claim the tactic could not have closed had it been
# false, at a hypothesis group that is satisfiable.
_ADM_HAVES = (
    "  -- The postcondition is SATISFIABLE at concrete reporting-shaped inputs, on\n"
    "  -- BOTH clauses: each `have` discharges it before the general proof runs.\n"
    "  -- The per-row closeness test is an unchanged opaque callee, so each point\n"
    "  -- states the value the REAL routine returns at the rows it names, and the\n"
    "  -- two domain facts each point needs are settled by decision at its own\n"
    "  -- concrete columns.\n"
    "  have adm_identical_rows :\n"
    "      rowsAgree [0, 1] [0, 1] (by decide) = true \u2192\n"
    "      rowsAgree [2, 3] [2, 3] (by decide) = true \u2192\n"
    "      problem_spec_columnDiffRows ['Q']\n"
    "        [[0, 1], [2, 3]] [[0, 1], [2, 3]] (by decide) (by decide) [] := by\n"
    "    intro h0 h1\n"
    "    unfold problem_spec_columnDiffRows isVariableLengthFormat rowDiffIndices\n"
    "    simp [List.finRange_succ, h0, h1]\n"
    "  have adm_both_rows_differ :\n"
    "      rowsAgree [0, 1] [1, 2] (by decide) = false \u2192\n"
    "      rowsAgree [2, 3] [3, 4] (by decide) = false \u2192\n"
    "      problem_spec_columnDiffRows ['Q']\n"
    "        [[0, 1], [2, 3]] [[1, 2], [3, 4]] (by decide) (by decide) [0, 1] := by\n"
    "    intro h0 h1\n"
    "    unfold problem_spec_columnDiffRows isVariableLengthFormat rowDiffIndices\n"
    "    simp [List.finRange_succ, h0, h1]\n"
    "  have adm_first_row_only :\n"
    "      rowsAgree [9] [0] (by decide) = false \u2192\n"
    "      rowsAgree [7] [7] (by decide) = true \u2192\n"
    "      problem_spec_columnDiffRows ['P'] [[9], [7]] [[0], [7]]\n"
    "        (by decide) (by decide) [0] := by\n"
    "    intro h0 h1\n"
    "    unfold problem_spec_columnDiffRows isVariableLengthFormat rowDiffIndices\n"
    "    simp [List.finRange_succ, h0, h1]\n"
    "  have adm_ragged_broadcast_row :\n"
    "      rowsAgree [1, 1] [1] (by decide) = true \u2192\n"
    "      problem_spec_columnDiffRows ['Q'] [[1, 1]] [[1]]\n"
    "        (by decide) (by decide) [] := by\n"
    "    intro h0\n"
    "    unfold problem_spec_columnDiffRows isVariableLengthFormat rowDiffIndices\n"
    "    simp [List.finRange_succ, h0]\n"
    "  have adm_fixed_shape_column :\n"
    "      problem_spec_columnDiffRows ['I'] [[9], [7]] [[0], [7]]\n"
    "        (by decide) (by decide)\n"
    "        (elementwiseDiff [[9], [7]] [[0], [7]] (by decide)) := by\n"
    "    unfold problem_spec_columnDiffRows isVariableLengthFormat\n"
    "    simp\n"
)
_ADM_PROOF = _PROOF.replace(
    "  intro fmt arra arrb _ hcmp hfix\n", "  intro fmt arra arrb _ hcmp hfix\n" + _ADM_HAVES, 1)
if _ADM_PROOF == _PROOF:
    raise AssertionError("drift: admissibility proof anchor")
POS_ADMISS = _swap(_BASE, _PROOF, _ADM_PROOF)

# --- pos-reorder: negate the selector and swap the two branches. --------------
# Structurally different but correct: the fixed-shape column is answered FIRST,
# behind the negated selector, and the row-wise side is written as the filter over
# row positions itself instead of an accumulating loop. Same value on every input.
# Two things only this positive exercises: the flat routine's shape argument is
# re-derived from the NEGATED guard, and the per-row domain argument is carried
# straight into the filter predicate. The reshaped layout reduces differently, so
# the obligation is RE-PROVED for the new shape (statement reused verbatim from
# `_STMT`; the frozen Route-B helper is retained unchanged even though this layout
# has no loop to apply it to, and no new declaration is introduced). Must verify
# (else SPEC-TOO-STRONG).
_REORDER_IMPL = _SIG_PURE + (
    "  if hb : (!(fmt.contains 'P' || fmt.contains 'Q')) = true then\n"
    "    elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))\n"
    "  else\n"
    "    ((List.finRange arra.length).filter\n"
    "        (fun i => !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt))).map Fin.val"
)
_REORDER_PROOF = _HELPER + _STMT + (
    "  intro fmt arra arrb _ hcmp hfix\n"
    "  unfold problem_spec_columnDiffRows implementation_columnDiffRows\n"
    "    isVariableLengthFormat rowDiffIndices\n"
    "  by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true\n"
    "  \u00b7 simp only [hc, dif_pos, Bool.not_true, Bool.false_eq_true, dif_neg,\n"
    "      not_false_eq_true]\n"
    "  \u00b7 simp only [Bool.not_eq_true] at hc\n"
    "    simp only [hc, Bool.not_false, dif_pos, Bool.false_eq_true]\n"
    "    simp"
)
POS_REORDER = _swap(_swap(_BASE, _IMPL, _REORDER_IMPL), _PROOF, _REORDER_PROOF)


# === UNIQUENESS / REJECT rivals ==============================================
# Wrong implementations sharing the frozen spec that MUST be rejected. Each
# corrupts one of the two modeled comparisons or the selection between them, and
# carries a refutation witness pinning the violation at one concrete input,
# checked to hold of the rival and to FAIL on the frozen solution.
#
# A note on what a rival may WRITE, since the two callees carry their domains as
# arguments. A rival that asks a callee about exactly the input the reporter was
# handed gets the domain fact from `hcmp` / `hfix` and reads like the frozen impl.
# A rival that asks about anything else — a row it built itself, a column it did
# not receive, an argument order it chose — does not get the fact and must
# ESTABLISH it: by deciding it at a shape it constructed (`by simp
# [rowsComparable]` for a row compared with itself, whose comparability is
# provable outright) or by TESTING it and having an answer ready for the other
# case (`if hg : rowsComparable .. = true then ..`). Both spellings are used
# below, and each keeps the rival a total function that returns a value at every
# input, which is what makes it a rival rather than a type error. So the domain
# arguments do not shrink this lane: they change the syntax a fabricated call is
# written in, and every rival that mattered before is still expressible.

# --- report the EQUAL rows instead of the unequal ones (the spurious-diff
#     failure mode, generalized): invert the membership test. -----------------
_EQUAL_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_EQUAL = _swap(_BASE, _IMPL, _EQUAL_IMPL)

# --- report EVERY row regardless of whether the sequences differ. -------------
_ALL_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_ALL = _swap(_BASE, _IMPL, _ALL_IMPL)

# --- drop the first row from the report (off-by-one over the row domain). -----
_DROP_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in (List.finRange arra.length).drop 1 do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_DROP = _swap(_BASE, _IMPL, _DROP_IMPL)

# --- compare the first column with ITSELF, ignoring the second column. --------
# Always reports the empty set; correct only when the two columns are identical.
# This rival ignores the `arrb` binder entirely.
_IGNB_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arra[i.val]! (by simp [rowsComparable]) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_IGNB = _swap(_BASE, _IMPL, _IGNB_IMPL)

# --- route P-only: recognize ONLY the 'P' descriptor, missing 'Q' (the actual
#     pre-patch bug). A Q-format VLA column then falls through to the opaque
#     `elementwiseDiff` instead of the row-wise loop. -----------------------
_PONLY_IMPL = _SIG_DO + (
    "  if hb : fmt.contains 'P' = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_GUARDED
RIVAL_PONLY = _swap(_BASE, _IMPL, _PONLY_IMPL)

# --- route Q-only: symmetric near-miss — recognize ONLY 'Q', missing 'P'.
#     A P-format VLA column falls through to the opaque routine. ------------
_QONLY_IMPL = _SIG_DO + (
    "  if hb : fmt.contains 'Q' = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_GUARDED
RIVAL_QONLY = _swap(_BASE, _IMPL, _QONLY_IMPL)

# --- report the differing rows in DECREASING index order. ---------------------
# Prepend instead of append: the same MEMBERSHIP set, the wrong ORDER. (P-VLA)
# claims to pin increasing index order, and until this rival nothing in the
# battery demonstrated that half of the clause — every other membership rival
# changes which rows are reported, so all of them would still reject if the order
# requirement were dropped. Observably different from the frozen impl whenever
# two or more rows differ.
_ORDER_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := [i.val] ++ acc\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_ORDER = _swap(_BASE, _IMPL, _ORDER_IMPL)

# --- drop the format recognition entirely: ALWAYS use the fixed-shape routine.
# The maximally-broken routing in direction (a). It is NOT redundant with the two
# near-misses: those still recognize one marker, so each is refuted only at the
# marker it misses, and a spec that constrained the result on `'P'` alone would
# still reject them. This rival is wrong at EVERY variable-length format, which is
# the distinct claim.
_AEW_IMPL = _SIG_DO + (
    "  if hg : rowsAreFixedShape arra arrb = true then\n"
    "    return elementwiseDiff arra arrb hg\n"
    "  else\n"
    "    return []"
)
RIVAL_AEW = _swap(_BASE, _IMPL, _AEW_IMPL)

# --- compare rows by their FIRST STORED ELEMENT instead of as whole sequences.
# The per-row GRANULARITY attack, and the only rival in the battery that leaves
# the row domain and the report order exactly right. Every other membership rival
# corrupts WHICH rows are considered; this one considers precisely the right rows
# in the right order and weakens only the per-row test, so it is the sole case
# that rejects because rows must be compared as WHOLE SEQUENCES. Observably
# different from the frozen impl at any two rows that agree on their first
# element and diverge later — the shape a variable-length row makes routine.
_HEAD_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if hg : rowsComparable (arra[i.val]!.take 1) (arrb[i.val]!.take 1) = true then\n"
    "        if !rowsAgree (arra[i.val]!.take 1) (arrb[i.val]!.take 1) hg then\n"
    "          acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_HEAD = _swap(_BASE, _IMPL, _HEAD_IMPL)

# --- compare rows by STRUCTURAL EQUALITY of the two stored sequences instead of
#     by the per-row closeness test the code actually calls. -------------------
# The per-row test's IDENTITY attack, and the rival this spec revision exists to
# reject: the previous revision of this file modeled the per-row test AS `≠` on
# `List Int`, i.e. its frozen impl WAS this rival. Structural inequality is a
# faithful-looking proxy — it agrees with the real routine on every pair of
# equal-length sequences of small integers, which is every input the old
# conformance grammar generated — and diverges on exactly the rows a
# variable-length column makes routine: a pair the real routine relates by
# broadcasting a one-value sequence against a longer one. There the real routine
# reports agreement and this rival reports a difference. Correct where the old
# battery pinned it, wrong where the old model was relaxed.
_STRUCTEQ_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if arra[i.val]! \u2260 arrb[i.val]! then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_STRUCTEQ = _swap(_BASE, _IMPL, _STRUCTEQ_IMPL)

# --- keep the real test and the real arguments, but DROP the ragged rows. -----
# The mirror image of the rival above, and the one that guards the faithfulness
# repair from being undone in the other direction. Nothing about this rival's
# handling of an equal-length row differs from the frozen impl: same row range,
# same order, same test, same two whole stored sequences. It differs only on a row
# whose two sequences are stored at DIFFERENT lengths, which it silently reports
# as agreeing, as if a ragged row were outside what a differing-row report can
# describe. That is exactly the reading the added `rowsComparable` hypothesis
# could have been mistaken for — and it is wrong: `rowsComparable` excludes only
# the rows the real routine cannot compare AT ALL, while a one-value sequence
# against a longer one is a row it compares happily, by relating that value to
# every value on the other side. So a ragged row whose values do NOT match is a
# real difference the real routine reports and this rival hides.
_SKIPRAG_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if arra[i.val]!.length == arrb[i.val]!.length\n"
    "          && !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_SKIPRAG = _swap(_BASE, _IMPL, _SKIPRAG_IMPL)

# --- compare against a CLOBBERED local copy of the first column. --------------
# The FRAME lane's expressible instance (see the header). Copy the first column
# into a local, overwrite row 0's stored sequence in the copy, then run the
# frozen row-wise loop against the copy. Referential transparency removes the
# aliasing and the permission machinery, not the defect: the comparison is
# performed against data the caller did not supply, so a column identical to
# itself reports a spurious difference at the clobbered row — behaviorally wrong
# independently of any permission artifact, which is exactly what the nagini
# case's own refinement argued. The clobbered row is not one of the rows the
# reporter was handed comparability for, so this rival must ESTABLISH that the
# copy's row can be compared before it may ask about it, which it does by testing
# — the only shape in which a fabricated call is expressible at all. Refuted under
# hypotheses fixing the per-row test at the two stored rows and at the clobbered
# pair, all three measured values of the real routine.
_FRAME_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut a := arra\n"
    "    a := a.set 0 [9]\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if hg : rowsComparable a[i.val]! arrb[i.val]! = true then\n"
    "        if !rowsAgree a[i.val]! arrb[i.val]! hg then\n"
    "          acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_VIA_HFIX
RIVAL_FRAME = _swap(_BASE, _IMPL, _FRAME_IMPL)

# === the FIXED-SHAPE lane: routing in direction (b) ==========================
# Five rivals whose variable-length behavior is EXACTLY the frozen impl's and
# which are wrong only on an ordinary fixed-shape column. Every one of them was
# accepted by the previous revision of this spec (measured), which is why the
# lane exists: leaving that branch free releases the selector, so "treat every
# column as variable-length" was a correct answer. (P-FIX) rejects them.

# --- always row-wise: ignore the format and run the row-wise comparison. ------
# The mirror image of `route-always-fixed-shape`, and the cheapest impl that
# satisfies (P-VLA) alone — which is exactly why it used to be a POSITIVE
# control here. It applies the row-granular comparison to EVERY column,
# including ordinary fixed-shape ones, i.e. it has lost the distinction the
# behavior exists to draw.
_ROWWISE_ALWAYS_IMPL = _SIG_PURE + "  rowDiffIndices arra arrb hcmp"
RIVAL_ROWWISE_ALWAYS = _swap(_BASE, _IMPL, _ROWWISE_ALWAYS_IMPL)

# --- over-recognize every format: the selector is always true. ----------------
# Keeps both markers in the predicate and adds a disjunct that is unconditionally
# true, so a column with NO variable-length marker still takes the row-wise
# branch. Distinct from the rival above in that the branch structure and the
# marker tests survive intact — only the selector's outcome is widened — which is
# the shape a real over-broad guard takes.
_ANYFMT_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q' || true) = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_GUARDED
RIVAL_ANYFMT = _swap(_BASE, _IMPL, _ANYFMT_IMPL)

# --- over-recognize ONE extra marker: a fixed-shape descriptor letter. --------
# The narrowest possible over-recognition, and the one a widening edit actually
# risks: recognize the two variable-length markers AND one more letter that
# ordinary fixed-shape columns carry. Correct on every variable-length column and
# on every format not carrying that letter, wrong only on the fixed-shape columns
# that do — a near-miss in direction (b) exactly as `route-p-only` is one in
# direction (a). A spec that pinned only "some fixed-shape column is not
# re-routed" while leaving the selector otherwise free would reject the two
# rivals above and admit this one.
_EXTRA_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q' || fmt.contains 'A') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
) + _FLAT_GUARDED
RIVAL_EXTRA = _swap(_BASE, _IMPL, _EXTRA_IMPL)

# --- answer the fixed-shape column with the EMPTY report. ---------------------
# The selector is exactly right; the fixed-shape branch simply reports no
# differences at all. Distinct from the over-recognizing rivals: those substitute
# the WRONG comparison, this one substitutes NO comparison, so a fixed-shape
# column that genuinely differs is reported identical.
_FIXEMPTY_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
    "    return []"
)
RIVAL_FIXEMPTY = _swap(_BASE, _IMPL, _FIXEMPTY_IMPL)

# --- answer the fixed-shape column with EVERY row. ----------------------------
# The opposite corruption of the same branch: report the whole row range, so a
# fixed-shape column identical to itself is reported as differing everywhere.
# Carried alongside the empty-report rival because the two fail in opposite
# directions, and a clause that pinned only "the fixed-shape report is
# non-empty" (or only "is empty when the columns agree") would admit one of them.
_FIXALL_IMPL = _SIG_DO + (
    "  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then\n"
    "    let mut acc : List Nat := []\n"
    "    for i in List.finRange arra.length do\n"
    "      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then\n"
    "        acc := acc ++ [i.val]\n"
    "    return acc\n"
    "  else\n"
    "    return List.range arra.length"
)
RIVAL_FIXALL = _swap(_BASE, _IMPL, _FIXALL_IMPL)


# ---- witnesses (each checked: elaborates vs rival, fails vs frozen) ----------
_P = "problem_spec_columnDiffRows"
_I = "implementation_columnDiffRows"


def _sel(fmt):
    """The format the witness states its claim at, ascribed to `List Char`.

    The spec takes the FORMAT itself, not a pre-computed selector boolean, and
    decides the branch internally via `isVariableLengthFormat`. So a witness names
    the format literal and nothing else: the claim it makes is exactly the one the
    contract makes at that format. Passing a reduced boolean here would not
    typecheck, and passing a hand-computed selector would state a claim about a
    different predicate than the one the obligation is quantified over.
    """
    return f"({fmt} : List Char)"


def _rows(triples):
    """Binder group fixing the per-row closeness test's value at named rows.

    The per-row test is an UNCHANGED opaque callee, so no input literal decides
    it and a witness over (P-VLA) has to say what it answers at the rows it names.
    Every value stated in this file is the value the REAL routine returns on that
    pair of stored sequences — `np.allclose(xs, ys, rtol=0, atol=0)` at the
    harness tolerances (mapping.md §2), measured with numpy, not assumed — so each
    refutation is stated at an input that actually occurs. Ragged pairs are
    included deliberately: the real routine relates a one-value sequence to every
    value on the other side, so `rowsAgree [1, 1] [1] = true` is a real row, and
    it is the row the faithfulness review's counterexample was built from.

    The test takes the pair of lengths it can be applied to as an ARGUMENT, so
    each binder names that argument too. At concrete stored sequences the argument
    is settled by decision, and any two proofs of it are the same proof, so a
    binder written this way fixes the value of the very application the report is
    built from.

    The hypotheses are about DISTINCT applications of the opaque callee, so no
    group can be contradictory (the gate's consistency probe checks this).
    """
    return " ".join(f"(h{i} : rowsAgree {xs} {ys} (by decide) = {val})"
                    for i, (xs, ys, val) in enumerate(triples))


def _hnames(triples, extra=""):
    names = [f"h{i}" for i in range(len(triples))]
    if extra:
        names.append(extra)
    return ", ".join(names)


# The two domain facts every claim about the report carries: that each stored row
# is a pair the per-row test can relate, and that a column reaching the flat
# routine stores one value per row. At the concrete columns a witness names, both
# are settled by decision, and Lean identifies any two proofs of the same fact —
# so this discharges exactly the argument the frozen contract quantifies over.
_DOM = "(by decide) (by decide)"


def _wit(arra, arrb, rows, fmt="['Q']"):
    """Witness over (P-VLA), conditioned on the per-row test's values.

    `unfold` exposes both the demanded report and the rival's, and
    `simp [List.finRange_succ, ...]` evaluates the row positions, the row lookups
    and the conditional append, rewriting the opaque per-row applications by the
    hypotheses. The two domain predicates are unfolded alongside them because a
    rival may test a row's comparability itself before asking about it, and that
    test has to reduce for the rival's report to be a value. Checked for every
    case: elaborates against the rival, and on the frozen solution the goal
    reduces to `False` (the spec HOLDS there), so the refutation discriminates
    instead of asserting a tautology.
    """
    return (
        f"example {_rows(rows)} :\n"
        f"    ¬ {_P} {_sel(fmt)}\n"
        f"      {arra} {arrb} {_DOM}\n"
        f"      ({_I} {fmt} {arra} {arrb} {_DOM}) := by\n"
        f"  unfold {_P} {_I} isVariableLengthFormat rowDiffIndices\n"
        f"  simp [List.finRange_succ, rowsComparable, rowsAreFixedShape,"
        f" {_hnames(rows)}]\n"
    )


# two rows the per-row test ACCEPTS -> spec []; report-equal rival reports [0, 1].
_WIT_EQUAL = _wit("[[0, 1], [2, 3]]", "[[0, 1], [2, 3]]",
                  [("[0, 1]", "[0, 1]", "true"), ("[2, 3]", "[2, 3]", "true")])
# row 0 accepted, row 1 not -> spec [1]; report-every-row rival reports [0, 1].
_WIT_ALL = _wit("[[5], [6]]", "[[5], [9]]",
                [("[5]", "[5]", "true"), ("[6]", "[9]", "false")])
# row 0 not accepted, row 1 accepted -> spec [0]; drop-first rival reports [].
_WIT_DROP = _wit("[[9], [7]]", "[[0], [7]]",
                 [("[9]", "[0]", "false"), ("[7]", "[7]", "true")])
# single row the test does not accept -> spec [0]; the self-comparing rival tests
# row 0 against ITSELF, which the test does accept, so it reports [].
_WIT_IGNB = _wit("[[1, 2]]", "[[3, 4]]",
                 [("[1, 2]", "[3, 4]", "false"), ("[1, 2]", "[1, 2]", "true")])
# rows 0 and 2 not accepted, row 1 accepted -> spec [0, 2]; the prepending rival
# reports [2, 0]. The same MEMBERSHIP set, so this input refutes the ORDER half of
# (P-VLA) and nothing else: three rows are needed (with two differing) because at
# fewer than two differing rows a reversed report is indistinguishable.
_WIT_ORDER = _wit("[[1], [4], [5]]", "[[2], [4], [6]]",
                  [("[1]", "[2]", "false"), ("[4]", "[4]", "true"),
                   ("[5]", "[6]", "false")])
# one row the per-row test does NOT accept, whose two stored sequences agree on
# their first value and diverge after it -> spec [0]; the first-value-only rival
# applies the test to the two one-value prefixes, which it DOES accept, and
# reports []. Chosen so the refutation isolates per-row GRANULARITY and nothing
# else: the row domain is the full range, one row, and the report order is
# trivially correct, so no other clause of (P-VLA) can be what fails here.
_WIT_HEAD = _wit("[[1, 2]]", "[[1, 9]]",
                 [("[1, 2]", "[1, 9]", "false"), ("[1]", "[1]", "true")])
# two rows the test accepts -> spec []; the clobbering rival compares row 0
# against an overwritten copy, which the test does not accept, and reports [0]. A
# spurious difference on a column identical to itself: the exact shape the
# row-wise comparison exists to avoid.
_WIT_FRAME = _wit("[[1], [3]]", "[[1], [3]]",
                  [("[1]", "[1]", "true"), ("[3]", "[3]", "true"),
                   ("[9]", "[1]", "false")])
# one RAGGED row that the real per-row test ACCEPTS (a two-value sequence against
# a one-value one, related by broadcasting) but whose stored sequences are not
# equal as sequences -> spec []; the structural-equality rival reports [0]. This
# is the faithfulness review's own counterexample turned into a rival: the
# previous revision of this spec compared rows by `arra[idx]! ≠ arrb[idx]!`, i.e.
# it WAS this rival, and it demanded [0] where the real routine reports no
# difference. Nothing else in the battery pins the per-row test's identity.
_WIT_STRUCTEQ = _wit("[[1, 1]]", "[[1]]", [("[1, 1]", "[1]", "true")])
# the OTHER ragged row: one the real per-row test does NOT accept, a two-value
# sequence against a one-value one whose value matches neither
# (`np.allclose([1, 2], [3], rtol=0, atol=0)` is False, measured — and measured
# again through the real column comparison, which reports row 0) -> spec [0]; the
# rival that drops ragged rows reports []. Together with `_WIT_STRUCTEQ` this pins
# both directions at the SAME input class: a ragged row is neither always a
# difference nor never one, it is whatever the per-row test says about it.
_WIT_SKIPRAG = _wit("[[1, 2]]", "[[3]]", [("[1, 2]", "[3]", "false")])


def _opaque_wit(fmt_lit, demanded, rows=(), unfold_rowwise=True):
    """Hypothesis-conditioned witness for a MIS-ROUTING rival, either direction.

    The two branches answer with values of different kinds — one computed from the
    inputs, one produced by the `opaque` fixed-shape routine — so on exactly one
    side of every routing refutation there is a term no tactic can reduce. The
    refutation is therefore stated under a hypothesis that the opaque routine's
    value at the witness input is NOT `demanded`, where `demanded` is whichever
    concrete list the two impls disagree over:

      * direction (a) — a variable-length column mis-sent to the flat routine.
        The spec demands the row-wise set `[0]` at [[1]] vs [[3]]; the rival's
        result IS the opaque term. Hypothesis: that term ≠ [0].
      * direction (b) — a fixed-shape column mis-sent elsewhere. The spec demands
        the opaque term; the rival's result is a concrete list. Hypothesis: the
        opaque term ≠ that list.

    Either way the witness ELABORATES against the rival, FAILS on the frozen
    solution (which routes each column to its own comparison, making the spec
    hold), and the gate's consistency probe cannot derive `False` from an
    inequation about an opaque atom (satisfiable). No `sorry`/`axiom`/`opaque`
    token appears in the witness itself.

    Every routing refutation is stated at a column storing ONE value per row. That
    is not incidental: the flat routine's shape requirement is an argument of it,
    so a claim about where a column gets routed can only be made where both
    destinations are askable at all. A ragged column has no flat answer to be
    wrong about, and a rival that mis-routes one has nothing to return.

    `fmt_lit` is the WHOLE format literal, not a single marker: which format the
    refutation is stated at is exactly what separates the near-misses from the
    unconditional rivals — see `_WIT_AEW` and `_WIT_EXTRA`.

    `unfold_rowwise` is False for the two rivals whose fixed-shape branch returns
    a concrete list built without the row-wise helper: the refutation reaches the
    goal it needs without naming it, and the two cases are the ones where the
    helper survives on neither side once the branch is settled.

    `rows` fixes the per-row closeness test's value where the ROW-WISE side of the
    disagreement is one of the two values (every routing case except the two that
    answer a fixed-shape column with a constant): the row-wise report at
    [[1]] vs [[3]] is `[0]` precisely because the real routine does not accept
    that pair, which is what the hypothesis states. Both hypotheses are about
    DIFFERENT opaque callees, so the group cannot be contradictory.
    """
    rdi = " rowDiffIndices" if unfold_rowwise else ""
    binders = (_rows(rows) + " ") if rows else ""
    extra = ("," + " " + _hnames(rows)) if rows else ""
    return (
        f"example {binders}"
        f"(h : elementwiseDiff [[1]] [[3]] (by decide) ≠ ({demanded} : List Nat)) :\n"
        f"    ¬ {_P} {_sel(fmt_lit)}\n"
        f"      [[1]] [[3]] {_DOM}\n"
        f"      ({_I} {fmt_lit} [[1]] [[3]] {_DOM}) := by\n"
        f"  unfold {_P} {_I} isVariableLengthFormat{rdi}\n"
        f"  simp [List.finRange_succ, rowsComparable, rowsAreFixedShape{extra}]\n"
        "  first\n"
        "  | (intro hc; first | exact h hc | exact h hc.symm)\n"
        "  | (refine ⟨rfl, ?_⟩; first | exact h | exact fun hc => h hc.symm)\n"
        "  | exact fun hc => h hc\n"
        "  | exact fun hc => h hc.symm\n"
        "  | (intro hc; simp_all)\n"
        "  | simp_all\n"
    )


# The row the routing witnesses state their claim at: the real per-row test does
# not accept [1] against [3] (`np.allclose([1], [3], rtol=0, atol=0)` -> False),
# so the row-wise report there is [0]. One value per row, so the FLAT routine can
# be asked about this column too — which is what makes the two destinations
# comparable and the routing question meaningful.
_ROUTE_ROW = [("[1]", "[3]", "false")]


# --- direction (a): a variable-length column sent to the flat routine. --------
# P-only rival mis-routes a 'Q' column to the opaque callee; spec demands [0].
_WIT_PONLY = _opaque_wit("['Q']", "[0]", _ROUTE_ROW)
# Q-only rival mis-routes a 'P' column to the opaque callee; spec demands [0].
_WIT_QONLY = _opaque_wit("['P']", "[0]", _ROUTE_ROW)
# The always-fixed-shape rival is refuted at a format carrying BOTH markers.
#
# This is deliberately NOT the single-marker witness the two near-misses use, and
# the choice is what makes this case non-vacuous rather than a third copy of
# route-p-only. Stated at `['Q']`, the refutation holds of the P-only rival too,
# so the witness would attest only "some routing rival mishandles a Q column" —
# a claim route-p-only already carries, with a byte-identical witness. At
# `['P', 'Q']` BOTH near-misses recognize their marker and route to the row-wise
# loop, i.e. they agree with the frozen impl there, so the witness FAILS against
# them exactly as it fails against gold; only the rival that recognizes NO marker
# is refuted. Measured, both directions: at `['P', 'Q']` this witness elaborates
# against the unconditional rival and fails against the frozen solution AND
# against each near-miss, with gold's and the near-misses' goal state alike
# reduced to `False` (`simp` discharged the spec for all three). So this case's
# rejection is attributable to the clause the near-misses do NOT pin: that a
# variable-length column must take the row-wise branch at EVERY format carrying a
# variable-length marker, not merely at one.
_WIT_AEW = _opaque_wit("['P', 'Q']", "[0]", _ROUTE_ROW)

# --- direction (b): a fixed-shape column sent somewhere other than the flat
#     routine. Stated at a format carrying NO variable-length marker, where
#     (P-FIX) demands the opaque routine's own answer. --------------------------
# always-row-wise rival returns the row-wise set [0] on a fixed-shape column.
_WIT_ROWWISE_ALWAYS = _opaque_wit("([] : List Char)", "[0]", _ROUTE_ROW)
# selector always true: same divergence, reached through the widened guard.
_WIT_ANYFMT = _opaque_wit("([] : List Char)", "[0]", _ROUTE_ROW)
# The one-extra-marker rival is refuted at a format carrying ONLY that extra
# letter, the single input class where it diverges from both the frozen impl and
# from the two rivals above (which are wrong at EVERY marker-free format,
# including this one — so this witness holds of them too and, unlike `_WIT_AEW`,
# is not claimed to separate the three). What it does establish is the narrow
# claim: recognizing one MORE format than the two variable-length markers is
# already a violation, so (P-FIX) pins the selector's negative side exactly and
# not merely "somewhere".
_WIT_EXTRA = _opaque_wit("['A']", "[0]", _ROUTE_ROW)
# empty-report rival: the spec demands the opaque answer, the rival returns [].
# `unfold rowDiffIndices` is omitted — nothing on either side needs it here.
_WIT_FIXEMPTY = _opaque_wit("([] : List Char)", "[]", unfold_rowwise=False)
# every-row rival: on one row the whole range is [0], so the demanded/produced
# pair is the same shape as above with the opposite corruption.
_WIT_FIXALL = _opaque_wit("([] : List Char)", "[0]", unfold_rowwise=False)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness)
    # =====================================================================
    {
        "id": "pos-cheap-two-branch-oneliner",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CHEAP,
        "rationale": "honest cheapest implementation that still DRAWS THE "
        "DISTINCTION: branch on the selector and hand each kind of column its own "
        "answer directly — the GROUNDED row-difference set `rowDiffIndices arra "
        "arrb hcmp` for a variable-length column, the unchanged flat routine's result "
        "for a fixed-shape one. No loop at all, so it is as structurally far from "
        "the frozen impl as a correct impl of this behavior gets; both clauses hold "
        "definitionally, so it MUST verify. If it cannot, the postcondition is "
        "SPEC-TOO-STRONG. Note it is NOT the unconditional `rowDiffIndices` "
        "one-liner: that impl satisfies (P-VLA) but violates (P-FIX) and is "
        "carried below as `always-rowwise-ignores-format`.",
    },
    {
        "id": "pos-let-local-reshape-admiss",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_LET,
        "rationale": "local-variable reshape: bind the list of row positions to a "
        "local, keeping the row-wise loop, the comparison (including the domain "
        "argument each per-row call carries), and the branch order identical to the "
        "frozen impl. Same value on every input, so both clauses still hold and the "
        "FROZEN proof closes it verbatim; must verify (else SPEC-TOO-STRONG). SOUNDNESS only — it discharges the same `∀`-obligation "
        "and never evaluates the postcondition at a concrete input, so it attests "
        "nothing about satisfiability; that is the separate admissibility case.",
    },
    {
        "id": "adm-obligation-satisfiable-at-report-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": POS_ADMISS,
        "rationale": "ADMISSIBILITY on a total carrier: the impl region is left "
        "FROZEN and the proof region additionally DISCHARGES the postcondition at "
        "FIVE concrete reporting-shaped inputs before closing the frozen obligation "
        "verbatim — two identical rows under the 64-bit marker (report must be "
        "EMPTY), the same two rows made to differ (report must be BOTH rows), a "
        "first-row-only difference under the 32-bit marker (report is row 0 only), a "
        "RAGGED row the per-row test accepts (report must be EMPTY), and a format "
        "carrying NEITHER marker, where the demanded answer is the unchanged flat "
        "routine's own result. The per-row test is an opaque callee, so the first "
        "four points state the value the REAL routine returns at their own rows as "
        "a local hypothesis and evaluate the report from it; every such value is "
        "measured (mapping.md §2). Each point also discharges the two domain "
        "arguments at its own concrete columns, by decision. The obligation's "
        "hypothesis (equal row counts) cannot be too strong in the nagini sense, "
        "but the analogue is the obligation being UNSATISFIABLE at an F2P-shaped "
        "point — and the domain ARGUMENTS the repair added are a second way to "
        "reach it, since a domain no real input inhabits is a report nobody can ask "
        "for. Evaluating the postcondition at named points shows it is genuinely "
        "inhabited there, which the `∀`-proof alone does not; the ragged point is "
        "the input class the faithfulness review found, and the fifth point is what "
        "shows the FIXED-SHAPE clause is inhabited rather than merely "
        "non-contradictory. Must verify; if any point fails the postcondition is "
        "unsatisfiable at a normal input (PRECOND-TOO-STRONG in this carrier's "
        "form). Controlled: at each of these five inputs the FALSE report is not "
        "provable by the same script, and no point's hypothesis group derives "
        "`False` — nine controls, all measured (all nine exit 1).",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different but CORRECT: negate the branch "
        "selector and swap the two branches, so the FIXED-SHAPE column is answered "
        "first and the row-wise side is written as the filter over row positions "
        "itself rather than as an accumulating loop. Same value on every input, so "
        "both clauses still hold; must verify (else SPEC-TOO-STRONG). Two things "
        "this case exercises that the other positives do not: the flat routine's "
        "shape argument is re-derived from the NEGATED guard rather than from the "
        "positive one, and the per-row domain argument is carried into the filter "
        "predicate directly. Re-proved because the reshaped layout reduces "
        "differently (`simp only [hc, dif_pos, Bool.not_true, ...]`); the frozen "
        "Route-B helper `columnDiffRows_loop` is retained unchanged in the "
        "declaration set even though this layout has no loop to apply it to, and "
        "the `correct_` statement is reused verbatim; no new declaration, axiom, or "
        "assumption token is introduced.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals — the ROW-WISE comparison (P-VLA)
    # =====================================================================
    {
        "id": "report-equal-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_EQUAL,
        "refinement": "inverting the membership test reports the rows that are "
        "EQUAL rather than those that differ — the spurious-difference failure "
        "mode generalized (an identical column reported as fully differing). The "
        "F2P checks that a column identical to itself yields NO differing rows and "
        "that specific differing rows are reported with exact indices and totals; "
        "an inverted comparison reports the complementary set, so those totals and "
        "the identical-file assertion both come out wrong — it does NOT resolve.",
        "rationale": "REJECT from (P-VLA): on a variable-length column the result "
        "must be `rowDiffIndices arra arrb hcmp` (the UNEQUAL rows), but this "
        "rival "
        "collects the equal rows. partial-domain / value: at two identical rows the "
        "spec is [] and the rival reports [0, 1].",
        "witness": _WIT_EQUAL,
    },
    {
        "id": "report-every-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_ALL,
        "refinement": "reporting every row regardless of the comparison drops the "
        "membership criterion entirely, so a column compared to itself would be "
        "reported as differing in every row and the difference totals would be "
        "inflated; the identical-file and exact-total F2P assertions FAIL — it does "
        "NOT resolve.",
        "rationale": "REJECT from (P-VLA): the report must be restricted to the "
        "UNEQUAL rows; reporting the whole row range over-reports whenever any row "
        "is equal. partial-domain: correct only when every row differs. At rows "
        "[[5],[6]] vs [[5],[9]] the spec is [1] and the rival reports [0, 1].",
        "witness": _WIT_ALL,
    },
    {
        "id": "drop-first-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_DROP,
        "refinement": "iterating over the row range with the first index dropped "
        "undercounts whenever row 0 differs, so a difference in the first row goes "
        "unreported and the difference total is short by one; the exact-total and "
        "per-row-index F2P assertions FAIL — it does NOT resolve.",
        "rationale": "REJECT from (P-VLA): the report must range over the FULL "
        "`List.finRange arra.length`; dropping the first position yields a subset "
        "whenever row 0 is a differing row. partial-domain: the boundary (first) "
        "row. At rows [[9],[7]] vs [[0],[7]] the spec is [0] and the rival reports "
        "[].",
        "witness": _WIT_DROP,
    },
    {
        "id": "self-compare-ignores-second-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_IGNB,
        "refinement": "comparing the first column with itself never reports a "
        "difference, so genuinely differing columns would be reported as identical "
        "and every difference-total and per-row F2P assertion for a differing table "
        "would collapse to zero — it does NOT resolve.",
        "rationale": "REJECT from (P-VLA): the criterion depends on BOTH `arra` and "
        "`arrb`, but this rival ignores the second column, always producing the "
        "empty report. It demonstrates the spec's dependence on the `arrb` binder: "
        "at [[1, 2]] vs [[3, 4]] the spec is [0] and the rival reports [].",
        "witness": _WIT_IGNB,
    },
    {
        "id": "report-rows-in-decreasing-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_ORDER,
        "refinement": "prepending instead of appending reports exactly the same "
        "differing rows in REVERSED index order. The F2P pins the per-row report "
        "entries positionally and in increasing row order for each differing "
        "column — the entry for row 0 of a column is asserted to come before the "
        "entry for row 1 of that same column — so a column with two differing rows "
        "emits its two entries transposed and those positional assertions FAIL "
        "even though the difference total is right. It does NOT resolve.",
        "rationale": "REJECT from (P-VLA): the result must EQUAL `rowDiffIndices "
        "arra arrb hcmp`, which is a `filter` over `List.finRange arra.length` "
        "and so is "
        "in increasing index order. This rival has the correct membership set and "
        "the wrong order, so it is the only case in the battery that exercises the "
        "ORDER half of the clause — every other membership rival changes WHICH rows "
        "are reported and would still be rejected if the order requirement were "
        "dropped. At rows [[1],[4],[5]] vs [[2],[4],[6]] (rows 0 and 2 differ) the "
        "spec is [0, 2] and the rival reports [2, 0].",
        "witness": _WIT_ORDER,
    },
    {
        "id": "compare-first-element-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_HEAD,
        "refinement": "testing only each row's FIRST stored value instead of the "
        "whole stored sequence misses every difference that occurs after the first "
        "position, so two rows agreeing at the front and diverging later are "
        "reported as identical. The F2P pins exact difference totals and the "
        "per-row entries for columns whose rows carry several values each, so a "
        "row differing only past its first value goes unreported and the total "
        "comes out short — it does NOT resolve.",
        "rationale": "REJECT from (P-VLA): the membership criterion is inequality "
        "of the rows' stored sequences AS WHOLE SEQUENCES, and this rival replaces "
        "it with a proxy that inspects only the first stored value. It is the only "
        "case in the battery that exercises that half of the clause: it iterates "
        "the FULL row range in increasing order and appends, so its row domain and "
        "its report order are both exactly the frozen impl's, and a spec that "
        "compared rows by any per-row proxy rather than as whole sequences would "
        "still reject every other rival here while admitting this one. At the "
        "single row [[1, 2]] vs [[1, 9]] — the sequences agree on their first "
        "value and differ after it — the spec is [0] and the rival reports [].",
        "witness": _WIT_HEAD,
    },
    {
        "id": "compare-rows-by-structural-equality",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_STRUCTEQ,
        "refinement": "deciding each row by whether the two stored sequences are "
        "EQUAL AS SEQUENCES, instead of by the numeric closeness test the code "
        "calls on them, reports a difference at every row whose two sequences are "
        "stored with different lengths — including the rows the closeness test "
        "relates by matching a single stored value against each value on the other "
        "side, where it reports agreement. A variable-length column is exactly the "
        "kind of column whose rows store sequences of differing lengths, so on the "
        "column in the report this is stated at the difference total is inflated "
        "and rows the comparison accepts are listed as differing: the "
        "identical-comparison and exact-total assertions FAIL — it does NOT "
        "resolve.",
        "rationale": "REJECT from (P-VLA): the membership criterion is the per-row "
        "closeness test's own verdict on the two whole stored sequences, and this "
        "rival substitutes a DIFFERENT test that happens to agree with it on the "
        "equal-length rows. It is the per-row test's IDENTITY case, and the reason "
        "this revision of the spec exists: the PREVIOUS revision modeled the "
        "per-row test as structural inequality on `List Int`, so its frozen impl "
        "WAS this rival and it demanded a difference at a row the real routine "
        "accepts. Every other row-wise rival here corrupts the row domain, the "
        "order, or the granularity while leaving the test's identity alone, so all "
        "of them would still reject under the old unfaithful model; this one "
        "separates the two models and nothing else in the battery does. At the "
        "single ragged row [[1, 1]] vs [[1]] — which the real routine accepts, "
        "measured — the spec is [] and the rival reports [0]. The row is inside "
        "the contract's domain: `rowsComparable [1, 1] [1] = true`, since one side "
        "stores a single value. Conditioned on the real routine's measured value "
        "at that row (`rowsAgree [1, 1] [1] = true`), which is satisfiable — an "
        "equation about one application of an opaque callee.",
        "witness": _WIT_STRUCTEQ,
    },
    {
        "id": "skip-ragged-rows-from-the-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_SKIPRAG,
        "refinement": "reporting only those rows whose two stored sequences happen "
        "to be stored at the SAME length, and passing over every other row as "
        "though it agreed, hides real differences: a row holding several values in "
        "one column and a single non-matching value in the other is a difference "
        "the comparison reports, and this rival omits it. The F2P pins exact "
        "difference totals and the per-row entries for a column whose rows are "
        "stored at differing lengths, so the total comes out short and the entry is "
        "missing — it does NOT resolve.",
        "rationale": "REJECT from (P-VLA), and the guard on the DOMAIN half of the "
        "faithfulness repair. This rival keeps everything else exactly as the frozen "
        "impl has it — the full row range, increasing order, the same per-row test "
        "applied to the same two whole stored sequences — and narrows only WHICH "
        "rows may appear in the report, to those whose sequences have equal length. "
        "It is the reading (P-DOM) must not be confused with: the comparability "
        "hypothesis excludes the rows the per-row test cannot answer at all, not the "
        "rows whose sequences merely have different lengths, and a single stored "
        "value related to every value on the other side is a row the test answers "
        "readily. Nothing else in the battery rejects it: the granularity rivals "
        "corrupt the test or its arguments, the membership rivals corrupt the row "
        "set unconditionally, and a spec whose row-wise clause quantified only over "
        "equal-length rows would still reject all of them while admitting this one. "
        "At the single ragged row [[1, 2]] vs [[3]] the spec is [0] and the rival "
        "reports []. Conditioned on the real routine's measured value there "
        "(`rowsAgree [1, 2] [3] = false`, i.e. `np.allclose([1, 2], [3], rtol=0, "
        "atol=0)` is False — confirmed through the real column comparison, which "
        "reports row 0 for that column), which is satisfiable: one equation about "
        "one application of an opaque callee.",
        "witness": _WIT_SKIPRAG,
    },
    {
        "id": "frame-compare-clobbered-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_FRAME,
        "refinement": "comparing against a locally CLOBBERED copy of the first "
        "column — one row's stored sequence overwritten with a different one — "
        "makes that row compare unequal whatever the two columns actually hold, so a "
        "table compared with itself reports a difference it does not have. The "
        "F2P asserts that identical tables compare identical and pins exact "
        "difference totals; a spurious entry at the clobbered row breaks both — it "
        "does NOT resolve.",
        "rationale": "REJECT from (P-VLA): the criterion must be evaluated on the "
        "stored sequences the caller supplied in BOTH columns, and this rival "
        "evaluates it against a modified copy of the first one. This is the FRAME "
        "lane's expressible instance on a referentially transparent carrier: the "
        "permission mechanism that rejects it under a heap discipline is absent, "
        "but the defect that mechanism guards — a comparison performed against "
        "data the caller did not provide — is a plain value defect here and (P-VLA) "
        "catches it directly. At two IDENTICAL rows [[1], [3]] vs [[1], [3]] the "
        "spec is [] (the per-row test accepts each row against itself, measured) "
        "and the rival reports [0], because it tests the clobbered [9] against "
        "[1], which the test does not accept — a spurious difference on a column "
        "identical to itself.",
        "witness": _WIT_FRAME,
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals — MIS-ROUTING, direction (a):
    # a variable-length column sent to the flat fixed-shape routine.
    # =====================================================================
    {
        "id": "route-p-only-misses-Q",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_PONLY,
        "refinement": "narrowing the branch predicate to recognize only the "
        "32-bit descriptor (missing the 64-bit one) routes a variable-length "
        "column to the UNCHANGED fixed-shape routine instead of the row-wise "
        "comparison. On such a column the fixed-shape routine does not compute the "
        "row-wise difference set, so the reported differing rows are wrong and the "
        "difference totals come out wrong — it does NOT resolve. This is the "
        "pre-patch bug, made adversarial.",
        "rationale": "REJECT from (P-VLA): on a variable-length column the result "
        "must be `rowDiffIndices arra arrb hcmp`, but this rival routes that column "
        "to `elementwiseDiff` (the opaque fixed-shape routine) whose value the spec "
        "never claims. The witness is hypothesis-conditioned because the routed "
        "result is an opaque term, and it is stated at a column storing ONE value "
        "per row so that the flat routine is applicable there at all: at [[1]] vs "
        "[[3]] the spec demands [0], and under the hypothesis that "
        "`elementwiseDiff [[1]] [[3]] .. ≠ [0]` the rival violates (P-VLA) while "
        "the frozen solution (which routes to the row-wise loop and computes [0]) "
        "satisfies it. Consistency probe: the opaque hypothesis is satisfiable.",
        "witness": _WIT_PONLY,
    },
    {
        "id": "route-q-only-misses-P",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_QONLY,
        "refinement": "symmetric near-miss: recognize only the 64-bit descriptor "
        "and miss the 32-bit one, so a 32-bit-format variable-length column falls "
        "through to the UNCHANGED fixed-shape routine instead of the row-wise "
        "comparison. Its reported differing rows and totals are then wrong on that "
        "column — it does NOT resolve.",
        "rationale": "REJECT from (P-VLA): mirror of route-p-only. A "
        "variable-length column is routed to the opaque `elementwiseDiff` whose "
        "value the spec never claims. Hypothesis-conditioned witness at the "
        "single-valued column [[1]] vs [[3]] (spec demands [0]): under "
        "`elementwiseDiff [[1]] [[3]] .. ≠ [0]` the rival violates (P-VLA), the "
        "frozen solution satisfies it, and the opaque hypothesis is satisfiable.",
        "witness": _WIT_QONLY,
    },
    {
        "id": "route-always-fixed-shape",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_AEW,
        "refinement": "dropping the format recognition entirely sends EVERY "
        "column, including a variable-length one, to the UNCHANGED fixed-shape "
        "routine, which does not compute the row-wise difference set on such a "
        "column. Both the identical-column assertion and the exact difference "
        "totals then come out wrong on every such column, not merely on one marker "
        "— it does NOT resolve.",
        "rationale": "REJECT from (P-VLA): on any format carrying a variable-length "
        "marker the result must be `rowDiffIndices arra arrb hcmp`, but this rival "
        "returns the opaque fixed-shape result unconditionally. NOT redundant with "
        "the two near-misses, and the witness is what shows it: it is stated at the "
        "format ['P', 'Q'] carrying BOTH markers, where each near-miss recognizes "
        "its own marker and routes to the row-wise loop — agreeing with the frozen "
        "impl — so the refutation FAILS against both of them exactly as it fails "
        "against gold, and holds ONLY of the rival that recognizes no marker at "
        "all. A single-marker witness would not separate the two: refuted at ['Q'] "
        "this rival's counterexample is also route-p-only's, which is why an "
        "earlier revision's witness (byte-identical to route-p-only's) attested to "
        "nothing extra. The clause pinned here is that a variable-length column "
        "must take the row-wise branch at EVERY format carrying such a marker, not "
        "merely at one. Hypothesis-conditioned because the routed result is an "
        "opaque term: at the single-valued column [[1]] vs [[3]] the spec demands "
        "[0], and under `elementwiseDiff [[1]] [[3]] .. ≠ [0]` the rival violates (P-VLA) while "
        "the frozen solution computes [0] and satisfies it; the opaque hypothesis "
        "is satisfiable.",
        "witness": _WIT_AEW,
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals — MIS-ROUTING, direction (b):
    # an ordinary FIXED-SHAPE column sent somewhere other than the flat
    # routine. This whole lane was missing, and every rival in it VERIFIED
    # against the previous revision of this spec.
    # =====================================================================
    {
        "id": "always-rowwise-ignores-format",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_ROWWISE_ALWAYS,
        "refinement": "applying the row-granular comparison to EVERY column, "
        "whatever its format, replaces the flat element-by-element comparison on "
        "ordinary fixed-shape columns with a different one. On such a column the "
        "row-wise test compares each row's whole stored sequence, which is not the "
        "comparison the fixed-shape path performs (it compares elements, under the "
        "floating-point tolerance where that applies), so the reported differences "
        "and the difference totals for ordinary columns come out wrong. The "
        "PASS_TO_PASS suite exercises exactly those ordinary columns — it does NOT "
        "resolve.",
        "rationale": "REJECT from (P-FIX): a fixed-shape column's report must be "
        "exactly the unchanged flat routine's result, and this rival hands it the "
        "row-wise difference set instead. It satisfies (P-VLA) perfectly, which is "
        "the point of carrying it: under the previous revision of this spec, which "
        "constrained only the variable-length branch, this exact implementation was "
        "a POSITIVE CONTROL and VERIFIED. Hypothesis-conditioned witness at a "
        "format carrying NO variable-length marker: on [[1]] vs [[3]] the "
        "spec demands `elementwiseDiff [[1]] [[3]] ..` and the rival returns [0], "
        "so under the hypothesis that those differ the rival violates (P-FIX) while "
        "the frozen solution returns the opaque result itself and satisfies it. The "
        "hypothesis is satisfiable (an inequation about an opaque atom).",
        "witness": _WIT_ROWWISE_ALWAYS,
    },
    {
        "id": "route-any-format-to-rowwise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_ANYFMT,
        "refinement": "widening the branch predicate with an unconditionally true "
        "disjunct sends every column down the row-wise path even when its format "
        "carries no variable-length marker, so ordinary fixed-shape columns are "
        "compared row-by-row instead of element-by-element and their reported "
        "differences and totals come out wrong. The PASS_TO_PASS suite compares "
        "such columns — it does NOT resolve.",
        "rationale": "REJECT from (P-FIX): distinct from "
        "`always-rowwise-ignores-format` in that the branch structure and both "
        "marker tests survive intact and only the SELECTOR's outcome is widened, "
        "which is the shape a real over-broad guard takes; a spec that pinned the "
        "row-wise branch's contents but not the selector's negative side would "
        "reject the other rival and admit this one. Hypothesis-conditioned witness "
        "at a marker-free format: the spec demands the opaque routine's answer, the "
        "rival computes [0], and under the hypothesis that those differ the rival "
        "violates (P-FIX) while the frozen solution satisfies it. Satisfiable "
        "hypothesis. Measured: this rival VERIFIED against the previous revision of "
        "this spec.",
        "witness": _WIT_ANYFMT,
    },
    {
        "id": "route-extra-marker-to-rowwise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_EXTRA,
        "refinement": "recognizing the two variable-length descriptors AND one "
        "further format letter sends the ordinary fixed-shape columns that carry "
        "that letter down the row-wise path, so their reported differences and "
        "totals come out wrong while every variable-length column is handled "
        "correctly. The narrowest over-recognition a widening edit can produce, and "
        "the PASS_TO_PASS suite compares columns of that ordinary kind — it does "
        "NOT resolve.",
        "rationale": "REJECT from (P-FIX): the near-miss in direction (b), exactly "
        "as `route-p-only` is one in direction (a) — correct on every "
        "variable-length column and on every format not carrying the extra letter, "
        "wrong only on the ordinary columns that do. It is carried because a spec "
        "pinning merely that SOME fixed-shape column is not re-routed, while "
        "leaving the selector otherwise free, would reject the two unconditional "
        "rivals above and admit this one; (P-FIX) pins the selector's negative side "
        "exactly. Hypothesis-conditioned witness at a format carrying only the "
        "extra letter: the spec demands the opaque routine's answer, the rival "
        "computes [0]. This witness holds of the two unconditional rivals as well "
        "(they are wrong at every marker-free format, including this one), so "
        "unlike `route-always-fixed-shape`'s it is not claimed to separate them — "
        "what it establishes is the narrow claim that recognizing ONE format more "
        "than the variable-length markers is already a violation. It still "
        "discriminates against the frozen solution, which is what the gate checks, "
        "and the hypothesis is satisfiable.",
        "witness": _WIT_EXTRA,
    },
    {
        "id": "fixed-shape-report-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_FIXEMPTY,
        "refinement": "answering an ordinary fixed-shape column with the empty "
        "report discards its comparison entirely, so two such columns that "
        "genuinely differ are reported as identical and the difference totals "
        "collapse to zero for every ordinary column. The PASS_TO_PASS suite "
        "asserts differences on exactly those columns — it does NOT resolve.",
        "rationale": "REJECT from (P-FIX): the fixed-shape report must be exactly "
        "the unchanged routine's result, and this rival substitutes NO comparison "
        "rather than the wrong one — distinct from the over-recognizing rivals, "
        "whose selector is what fails while both branches still compare something. "
        "The selector here is exactly right. Hypothesis-conditioned witness at a "
        "marker-free format: the spec demands `elementwiseDiff [[1]] [[3]] ..`, the "
        "rival returns [], so under the hypothesis that the opaque result is not [] "
        "the rival violates (P-FIX) while the frozen solution satisfies it; "
        "satisfiable hypothesis. Measured: this rival VERIFIED against the previous "
        "revision of this spec.",
        "witness": _WIT_FIXEMPTY,
    },
    {
        "id": "fixed-shape-report-every-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RIVAL_FIXALL,
        "refinement": "answering an ordinary fixed-shape column with its whole row "
        "range reports every row as differing, so such a column compared with "
        "itself is reported as differing everywhere and the difference totals are "
        "inflated for every ordinary column. The PASS_TO_PASS suite asserts that "
        "identical columns compare identical — it does NOT resolve.",
        "rationale": "REJECT from (P-FIX): the opposite corruption of the same "
        "branch from `fixed-shape-report-empty`, carried alongside it because a "
        "clause pinning only that the fixed-shape report is NON-EMPTY (or only that "
        "it is empty when the columns agree) would admit one of the two. Pinning "
        "the report to the unchanged routine's own result rejects both without "
        "claiming anything about that routine's value. Hypothesis-conditioned "
        "witness at a marker-free format: on one row the whole range is [0], the "
        "spec demands the opaque answer, and under the hypothesis that those differ "
        "the rival violates (P-FIX) while the frozen solution satisfies it; "
        "satisfiable hypothesis.",
        "witness": _WIT_FIXALL,
    },
]
