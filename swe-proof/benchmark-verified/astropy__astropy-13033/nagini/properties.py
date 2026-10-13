# properties.py — PBT falsification battery for astropy__astropy-13033.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside a # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   render_name_run(run: List[int]) -> List[int]      [the helper site A]
#     Requires Acc(list_pred(run), 1/2)               <-- READ-ONLY input (half perm)
#     Requires MustTerminate(len(run) + 2)            <-- LOAD-BEARING (completion)
#     Ensures  Acc(list_pred(run), 1/2)               <-- frame: caller keeps its half
#     Ensures  Acc(list_pred(Result()))
#     Ensures  ToSeq(run) == Old(ToSeq(run))          <-- LOAD-BEARING (preservation)
#     Ensures  ToSeq(Result()) == render_run(ToSeq(run))   <-- LOAD-BEARING
#     Exsures  (Exception, False)                     <-- LOAD-BEARING (delivery)
#
#   compose_leading_run_report(cls_name, demanded, found) -> List[int]  [site B]
#     Requires Acc(list_pred(cls_name),1/2), Acc(list_pred(demanded),1/2),
#              Acc(list_pred(found),1/2)               <-- THREE READ-ONLY inputs
#     Requires MustTerminate(len(demanded)+len(found)+6)  <-- LOAD-BEARING (completion)
#     Ensures  the three Acc(...,1/2) frame clauses (caller keeps its halves)
#     Ensures  Acc(list_pred(Result()))
#     Ensures  ToSeq(cls_name) == Old(ToSeq(cls_name))     <-- LOAD-BEARING
#     Ensures  ToSeq(demanded) == Old(ToSeq(demanded))     <--   (preservation,
#     Ensures  ToSeq(found)    == Old(ToSeq(found))        <--    clause (4))
#     Ensures  ToSeq(Result()) == report_seq(ToSeq(cls_name),
#                                  ToSeq(demanded), ToSeq(found))   <-- LOAD-BEARING
#     Exsures  (Exception, False)                     <-- LOAD-BEARING (delivery)
#
#   The two Exsures(Exception, False) clauses are clause (5): DELIVERY. They are
#   load-bearing for a reason the two MustTerminate clauses do NOT cover, and the
#   distinction is the whole point. MustTerminate rules out a computation that
#   never ends. It does not rule out one that ends WITHOUT AN ANSWER: an impl may
#   declare its own exceptional contract inside the marker-elided impl region and
#   leave by the failure exit, in which case it discharges the measure (it does
#   stop), and the Ensures clauses -- ALL of them, including the Old(...)
#   preservation clauses -- simply do not apply, because a normal postcondition
#   says nothing about an exceptional exit. Such an impl satisfies every other
#   clause of this spec on every input and delivers nothing on any of them; its
#   faithful real patch replaces the assembled message with a bare failure and
#   resolves nothing. The delivery-lane cases below (nondelivery-*) ARE that
#   shape, at BOTH modeled sites and in five distinct spellings, and the site-B
#   one VERIFIED against this spec before clause (5) existed. Note also that a
#   clause added at site A alone would not close it: site A's exceptional exit was
#   already caught incidentally, because site B calls site A and site B declared
#   no exceptional contract, whereas site B -- the assembly the whole report rests
#   on -- has no caller in this module and so nothing to catch it.
#
#   Clause (5) constrains only how a method LEAVES, never what it does inside:
#   internal-signal-caught-admitted below signals trouble internally, handles it,
#   and returns the gold report, and it MUST verify.
#
#   The four Old(...) clauses are clause (4): describing a disagreement only READS
#   the runs it was handed. They are load-bearing for a reason the half-permissions
#   alone do NOT cover. A single Acc(...,1/2) forbids a write, but the value clauses
#   are read in the POST-state, and at site B the three half-permissions may be held
#   on the SAME object: hand `demanded` and `found` over as one collection and the
#   two halves sum to FULL permission, so the assembly can rewrite that collection
#   and then report the rewritten names. Every other clause is satisfied -- the
#   report equals report_seq of what the runs say afterwards -- while the caller's
#   own declared list of names has been silently changed underneath it. Clause (4)
#   pins the report to the runs AS GIVEN. Case aliased-input-rewritten below IS that
#   shape, and it VERIFIED against the spec before clause (4) existed.
#
#   The two MustTerminate clauses are clause (3) of the spec: rendering a run and
#   assembling a report are each carried out TO COMPLETION and handed back, for
#   runs of every admissible length. They are what makes "the value returned is
#   the full-run rendering / the full report" an obligation about a value the
#   caller ACTUALLY RECEIVES rather than about a value that would have been
#   correct had one ever been produced. Without them the value clauses above are
#   discharged vacuously by any computation that never reaches a return -- so a
#   rival could be value-correct on the single-name (legacy) runs and simply
#   never finish on exactly the multi-name run the report exists to describe, and
#   still verify. The termination-rival cases below ARE that shape.
#
#   render_run / joined / quoted / report_seq are @Pure folds GROUNDED ENTIRELY
#   in the inputs (fully unfoldable; NOT an opaque answer-key oracle). The
#   load-bearing equality is checked against the fold itself, so there is no
#   "wrong ungrounded-oracle echo" to build: any value an impl returns must equal
#   report_seq/render_run of its actual args. The ungrounded-oracle class is
#   therefore N/A (see 'assessment'); the cheapest honest impl IS the gold
#   concatenation, so its positive control is a reorder/local-reshape.
#
#   The BEHAVIOURAL DISCRIMINATOR (the bug fix, issue #13009): render the WHOLE
#   leading run of names (every name, in order) — and pluralise — instead of only
#   the FIRST name. The pre-patch echoed only required_columns[0] / colnames[0],
#   producing the misleading "'time' ... but found 'time'" report. report_seq /
#   render_run pin the full run + plural marker; the partial-domain and
#   plural-marker rivals below ARE that pre-patch behaviour.
#
#   No @ContractOnly axioms (meta.axioms == []). The deep models render_run /
#   report_seq are A-references validated == the real as_scalar_or_list_str helper
#   and the real .format(...) by axiom_check.py (G-AX): 9 boundary runs + 6 fixed
#   reports + 20000 fuzz, 0 mismatch. That established real-callee check IS the
#   axiom lane; re-encoding it as a Docker probe would duplicate, not strengthen,
#   it. Hence AXIOM_TESTS = []. See 'assessment'.
from pathlib import Path

INSTANCE = "astropy__astropy-13033"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchors INSIDE the impl regions (between # impl-start / # impl-end). Editing
# only these keeps spec_view (hence same_spec) byte-identical. There are TWO
# impl regions (render_name_run, compose_leading_run_report); each whole impl
# body is a unique anchor.
# ===========================================================================

# --- gold impl body of render_name_run (site A) ---------------------------
_IMPL_A_GOLD = """    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
    return result"""

assert _IMPL_A_GOLD in _BASE, "impl anchor drift: render_name_run body not verbatim"

# --- gold impl body of compose_leading_run_report (site B) ----------------
_IMPL_B_GOLD = """    expected_field = render_name_run(demanded)  # type: List[int]
    found_field = render_name_run(found)  # type: List[int]
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                        ToSeq(demanded), ToSeq(found)))
    return result"""

assert _IMPL_B_GOLD in _BASE, "impl anchor drift: compose_leading_run_report body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — site B, structurally different but CORRECT (verify)
# Reorder the LOCAL assignments: compute the constant connective segments
# (seg1/seg2/seg3) BEFORE the two field renders, and SWAP the two field renders
# (render `found` first, then `demanded`). Same observable value; every gold
# proof obligation that is still needed is kept verbatim (the plural Assert and
# the two render_run field Asserts and the final report_seq Assert). No loop
# direction flip / fold lemma is introduced. If a faithful correct impl could
# NOT verify against this spec => SPEC-TOO-STRONG.
#
# NOTE (proof-engineering, NOT a spec relaxation): `plural` is computed AFTER the
# two render_name_run calls. render_name_run is a method call; in Nagini's
# modular reasoning a call between a list local's construction and its later use
# havocs that local's framed list value, so computing `plural` *before* the two
# calls and only asserting ToSeq(plural) at the final report_seq equality leaves
# the value unframed and the equality undischargeable. Moving `plural` past the
# calls (no intervening call before its use) frames it. This is a framing trigger,
# not a change to WHAT is returned: the returned value is the gold concatenation.
# ===========================================================================
_IMPL_B_POS = """    # constant connective segments computed first (reordered vs gold).
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    # then the two field renders (order swapped vs gold: found first)
    found_field = render_name_run(found)  # type: List[int]
    expected_field = render_name_run(demanded)  # type: List[int]
    # plural marker computed after the renders (no method call intervenes before
    # its use, so its list value is framed at the final equality).
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    # single flat concatenation (same left-assoc grouping as report_seq)
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                        ToSeq(demanded), ToSeq(found)))
    return result"""

# ===========================================================================
# (2) ADMISSIBILITY — site B, the precondition admits a normal F2P-shaped input
# (verify). Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that the three Requires permissions
# are usable (read each input via ToSeq / render the runs) and reach a NORMAL
# non-raising return. If the Requires were vacuous / over-strong, the impl could
# not both consume the half-permissions and return => PRECOND-TOO-STRONG.
# ===========================================================================
_IMPL_B_ADMISS = """    # admissibility: the three half-permission inputs are all usable (read via
    # ToSeq / the renderer) and a normal (non-raising) return is reachable.
    Assert(len(cls_name) >= 0)        # cls_name half-perm readable
    Assert(len(demanded) >= 0)        # demanded half-perm readable
    Assert(len(found) >= 0)           # found half-perm readable
    expected_field = render_name_run(demanded)  # type: List[int]
    found_field = render_name_run(found)  # type: List[int]
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))
    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                        ToSeq(demanded), ToSeq(found)))
    return result"""

# ===========================================================================
# (3) FRAME-MUTATION — site A, write to the read-only input `run` (reject)
# render_name_run holds only Acc(list_pred(run), 1/2). Inside the multi-name
# loop the index run[i-1] is known in-bounds (0 <= i-1 < len(run)), so a WRITE
# run[i-1] = elt is well-typed and value-NEUTRAL — yet it needs FULL permission.
# With only the half-permission the Requires grants, Nagini rejects for
# INSUFFICIENT PERMISSION. The gold invariants/asserts are kept VERBATIM so the
# rejection is attributable to the write, not to a spec change. MANDATORY: the
# inputs are read-only and a byte-fuzzer never thinks to mutate them.
# ===========================================================================
_IMPL_A_FRAME = """    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        # FRAME MUTATION: write back into the read-only half-permission input.
        run[i - 1] = elt
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
    return result"""

# ===========================================================================
# (4) PARTIAL-DOMAIN / first-name-only — site B (reject). THIS IS THE PRE-PATCH
# BUG (issue #13009): render only the FIRST name of each run regardless of run
# length — exactly the old required_columns[0] / self.colnames[0] assembly. It
# agrees with the full-run rendering on length-1 runs but DROPS every name after
# the first on a multi-name run. The load-bearing postcondition
# ToSeq(result) == report_seq(... full render_run(demanded) ... render_run(found))
# therefore fails on any multi-name run. (Both fields are wrapped as the bare
# apostrophe form [QUOTE, name, QUOTE], like quoted(run[0]).)
# ===========================================================================
_IMPL_B_FIRSTONLY = """    expected_field = [NAME_QUOTE, encode_name(demanded[0]), NAME_QUOTE]  # type: List[int]
    found_field = [NAME_QUOTE, encode_name(found[0]), NAME_QUOTE]  # type: List[int]
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    return result"""

# ===========================================================================
# (5) PLURAL-MARKER DROP — site B (reject). Keep the FULL-run field rendering
# (so the demanded/found fields are correct) but ALWAYS emit the empty plural
# marker. On a multi-name demanded run report_seq pins plural == PSeq(115) ("s"),
# so "... as the first column but found ..." is missing the 's' that the F2P
# test asserts ("as the first columns"). The load-bearing postcondition fails on
# the len(demanded) > 1 sub-domain. This isolates the plural-marker clause of the
# fix (a control-flow / structural difference in the message that is NOT the
# first-name-only bug).
# ===========================================================================
_IMPL_B_NOPLURAL = """    expected_field = render_name_run(demanded)  # type: List[int]
    found_field = render_name_run(found)  # type: List[int]
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    # PLURAL DROP: always emit the empty marker, never pluralise.
    plural = []  # type: List[int]
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))
    Assert(ToSeq(found_field) == render_run(ToSeq(found)))
    return result"""

# ===========================================================================
# (6) PARTIAL-DOMAIN / drop-first-name — site A (reject). In the multi-name
# branch loop `while i > 1` instead of `> 0`: every name but the FIRST (index 0)
# is rendered into `inner`; the first name is dropped. At loop exit
# ToSeq(inner) == joined(run_s.drop(1)) != joined(run_s), so
# ToSeq(result) == [LBRACK] + joined(run_s.drop(1)) + [RBRACK] != render_run(run_s)
# on any run of length >= 2. Violates the load-bearing
# ToSeq(Result()) == render_run(ToSeq(run)). The dropped framing Asserts that
# referenced i==len(run) at start are removed only where they no longer typecheck;
# the load-bearing exit Assert is what fails (a SPEC reason, not a proof-trigger
# gap — the invariant simply can no longer close to drop(0)).
# ===========================================================================
_IMPL_A_DROPFIRST = """    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(1 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == render_run(run_s))
    return result"""

# ===========================================================================
# (7) NON-COMPLETION on the multi-name run — site A (reject). Keep the
# single-name branch value-correct (every legacy one-required-column scenario
# still renders exactly right) and, on a run of any OTHER length -- precisely the
# multi-name run the disagreement report exists to describe -- never hand a
# rendering back at all: re-ask the very same question instead of answering it.
# The value clause ToSeq(Result()) == render_run(ToSeq(run)) alone cannot see
# this (it constrains only runs that reach a return, and this one never does).
# Clause (3)'s completion budget is what rejects it: the budget must strictly
# decrease at the call, and re-asking about the SAME run does not decrease it
# (whereas descending to a strictly shorter run does -- see case (10)).
# ===========================================================================
_IMPL_A_NOFINISH = """    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # NON-COMPLETION on every other length: never deliver a rendering.
    return render_name_run(run)"""

# ===========================================================================
# (8) NON-COMPLETION of the report assembly — site B (reject). The SAME
# non-delivery at the OTHER modeled site: the report is never assembled and
# handed back for ANY input. Vacuous under the value clause alone; clause (3)'s
# completion budget rejects it because it does not decrease at the call.
# ===========================================================================
_IMPL_B_NOFINISH = """    # NON-COMPLETION: the report is never assembled and handed back.
    return compose_leading_run_report(cls_name, demanded, found)"""

# ===========================================================================
# (9) NON-COMPLETING RENDER LOOP — site A (reject). The gold construction loop
# with its step removed: `inner` accumulates the names correctly but the index
# never moves, so the bracketed rendering is never finished for a run of length
# >= 2 (and length 0 still exits, keeping the difference squarely on the
# multi-name path). Every value-level Invariant of gold is kept VERBATIM, so the
# rejection is attributable to non-completion and not to a value obligation:
# clause (3)'s loop measure cannot be maintained when `i` does not decrease.
# This distinguishes clause (3) from a self-call ban -- there is no self-call
# here at all.
# ===========================================================================
_IMPL_A_STUCKLOOP = """    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        # NON-COMPLETION: the index never advances, so the rendering of a
        # multi-name run is never finished.
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
    return result"""


# ===========================================================================
# (10) RECURSIVE DESCENT IS ADMITTED - site A (verify). Clause (3) demands that
# a rendering be DELIVERED; it does not dictate how the run is worked through.
# This impl re-enters the renderer on a strictly SHORTER run first -- exactly
# the shape a structurally recursive rendering has -- and then produces the gold
# value. It must VERIFY. If it did not, clause (3) would be banning a correct
# implementation shape (any recursive descent) rather than demanding completion,
# i.e. over-fitting the reference construction's iterative loop. This case is the
# guard against that reading and is what distinguishes a completion obligation
# from a blanket ban on self-calls.
# ===========================================================================
_A_DESCENT = """    if len(run) >= 2:
        # descend: build a strictly shorter run and render THAT first, the way a
        # structurally recursive rendering would.
        shorter = []  # type: List[int]
        j = len(run)
        while j > 1:
            Invariant(Acc(list_pred(run), 1 / 2))
            Invariant(Acc(list_pred(shorter)))
            Invariant(1 <= j and j <= len(run))
            Invariant(len(shorter) == len(run) - j)
            Invariant(run_s == ToSeq(run))
            Invariant(MustTerminate(j))
            shorter = shorter + [run[j - 1]]
            j = j - 1
        Assert(len(shorter) == len(run) - 1)
        sub = render_name_run(shorter)  # type: List[int]
"""

_A_FIRSTLINE = """    run_s = ToSeq(run)  # type: PSeq[int]
"""

_IMPL_A_RECURSE = _swap(_IMPL_A_GOLD, _A_FIRSTLINE, _A_FIRSTLINE + _A_DESCENT)


# ===========================================================================
# (11) ALIASED-INPUT REWRITE — site B (reject). RIGHT VALUE, WRONG EFFECT, on
# the boundary case the half-permissions do not cover: the demanded run and the
# found run handed over as ONE AND THE SAME collection. Two Acc(...,1/2) on the
# same object sum to FULL permission, so this impl is entitled to WRITE — and it
# does, changing a name and then reporting the runs as they read AFTERWARDS.
# Every value clause is then satisfied (result == report_seq of the post-state
# runs, and the gold Asserts all still discharge), and the caller's own declared
# list of names has been rewritten underneath it. This is the case that motivates
# clause (4): before the Old(...) clauses existed this impl VERIFIED. It is
# distinct from frame-mutation-write-run, which is rejected for insufficient
# permission at a site where no aliasing can supply the missing half.
# ===========================================================================
_B_FIRSTLINE = """    expected_field = render_name_run(demanded)  # type: List[int]
"""

_B_ALIASWRITE = """    # ALIASED-INPUT REWRITE: when the demanded run and the found run are one
    # and the same collection, the two read shares coincide and the collection
    # is writable. Rewrite a name in it and then report the rewritten runs.
    if demanded is found:
        if len(demanded) > 0:
            demanded[0] = demanded[0] + 1
"""

_IMPL_B_ALIASWRITE = _swap(_IMPL_B_GOLD, _B_FIRSTLINE, _B_ALIASWRITE + _B_FIRSTLINE)


# ===========================================================================
# (12) DELIVERY LANE — clause (5) / Exsures(Exception, False). Five spellings of
# "stop promptly and hand back nothing", at BOTH modeled sites. Each satisfies
# every MustTerminate measure (they all stop) and every Ensures clause vacuously
# (a normal postcondition says nothing about an exceptional exit), so before
# clause (5) existed the site-B ones VERIFIED.
# ===========================================================================

# The exceptional contract each of these declares INSIDE the impl region is the
# evasion itself: the region is elided by spec_view, so the smuggled declaration
# is invisible to same_spec, and Nagini drops its default "method raises no
# exceptions" check as soon as ANY exceptional contract is declared. Clause (5)
# closes it by conjunction: Nagini keeps every Exsures for a type, so the frozen
# `... , False` is still there to discharge and cannot be talked out of.
_B_PERMS = ("Acc(list_pred(cls_name), 1 / 2) and Acc(list_pred(demanded), 1 / 2)"
            " and Acc(list_pred(found), 1 / 2)")

_IMPL_B_SIGNALAWAY = f"""    # Declare an exceptional contract for the impl region, then leave by it. No
    # report is ever handed back, on any input.
    Exsures(Exception, {_B_PERMS})
    raise Exception()"""

_IMPL_A_SIGNALAWAY = """    # The same non-delivery smuggle at the RENDERING site.
    Exsures(Exception, Acc(list_pred(run), 1 / 2))
    raise Exception()"""

_IMPL_B_TRUE_OVERRIDE = """    # Declare a trivially TRUE exceptional contract for exactly the type the
    # frozen clause names, on the chance that a later declaration REPLACES the
    # frozen one instead of being conjoined with it.
    Exsures(Exception, True)
    raise Exception()"""

_IMPL_B_RERAISE = f"""    # Route the departure through a handler: the object that leaves is a
    # re-raise of a caught one rather than a freshly built one.
    Exsures(Exception, {_B_PERMS})
    try:
        raise Exception()
    except Exception as e:
        raise e"""

_IMPL_B_SIGNAL_MULTINAME = _swap(
    _IMPL_B_GOLD,
    "    expected_field = render_name_run(demanded)  # type: List[int]\n",
    f"""    # PARTIAL-DOMAIN x NON-DELIVERY: byte-for-byte gold whenever at most one
    # name is demanded, and no report at all on exactly the multi-name runs the
    # bracketed full-run rendering of clause (1) exists to describe.
    Exsures(Exception, {_B_PERMS})
    if len(demanded) > 1:
        raise Exception()
    expected_field = render_name_run(demanded)  # type: List[int]
""")

_IMPL_A_LATE_SIGNAL = "    Exsures(Exception, Acc(list_pred(run), 1 / 2))\n" + _swap(
    _IMPL_A_GOLD,
    "        i = i - 1\n",
    """        if i == 1:
            # The rendering is by now fully built and correct; leave by the
            # failure exit instead of handing it back.
            raise Exception()
        i = i - 1
""")

# POSITIVE CONTROL for clause (5): signalling trouble INTERNALLY and handling it
# is not a non-delivery. (5) constrains the exit only.
_IMPL_B_INTERNAL_CAUGHT = """    try:
        raise ValueError()
    except ValueError:
        pass
""" + _IMPL_B_GOLD


# ===========================================================================
# (13) FRESH VALUE-LANE RIVALS — over-approximation, a partial-domain guard on
# the run length the report is most often asked about, two one-token boundary
# swaps, and an echo of the demanded run into the found slot.
# ===========================================================================

# Over-approximation: keep every name, its order and its apostrophes, and coarsen
# away only the "a run of exactly one name renders bare" structure of clause (1).
_IMPL_A_ALLBRACKET = _swap(
    _swap(_IMPL_A_GOLD,
          """    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
""",
          """    # Treat EVERY length uniformly as the bracketed textual list form.
"""),
    "    Assert(ToSeq(result) == render_run(run_s))\n", "")

# Boundary token swap: the two bracket code points exchanged, nothing else.
_IMPL_A_BRACKETSWAP = _swap(
    _IMPL_A_GOLD,
    """    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
""",
    """    result = [RBRACK] + inner + [LBRACK]  # type: List[int]
""")

# Boundary token swap: the plural marker is the ADJACENT code point (116, "t").
# The pluralisation RULE is kept exactly.
_IMPL_B_PLURALTOKEN = _swap(
    _swap(_IMPL_B_GOLD, "        plural = [115]  # type: List[int]\n",
          "        plural = [116]  # type: List[int]\n"),
    "    Assert(ToSeq(plural) == (PSeq(115) if len(demanded) > 1 else empty_seq()))\n",
    "")

# Partial-domain guard on exactly length 2 -- the length the F2P scenario uses.
_IMPL_B_LEN2GUARD = _swap(
    _swap(_IMPL_B_GOLD,
          "    expected_field = render_name_run(demanded)  # type: List[int]\n",
          """    expected_field = []  # type: List[int]
    if len(demanded) == 2:
        expected_field = [NAME_QUOTE, encode_name(demanded[0]), NAME_QUOTE]
    else:
        expected_field = render_name_run(demanded)
"""),
    "    Assert(ToSeq(expected_field) == render_run(ToSeq(demanded)))\n", "")

# Echo: fill the found slot with the field already computed for the demanded run.
_IMPL_B_ECHOFOUND = _swap(
    _swap(_IMPL_B_GOLD,
          "    found_field = render_name_run(found)  # type: List[int]\n",
          "    found_field = expected_field  # type: List[int]\n"),
    "    Assert(ToSeq(found_field) == render_run(ToSeq(found)))\n", "")



SPEC_TESTS = [
    {
        "id": "internal-signal-caught-admitted",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_INTERNAL_CAUGHT),
        "rationale": "Clause (5) asks that the report be DELIVERED, i.e. it "
                     "constrains how the assembly LEAVES -- not what it does "
                     "internally. This impl signals trouble inside itself, handles "
                     "it, and then returns the gold report verbatim. It must verify: "
                     "a spec that rejected it would forbid a correct implementation "
                     "shape (internal failure handling -- the real helper sits inside "
                     "a method whose other branches signal) instead of demanding "
                     "delivery => SPEC-TOO-STRONG / over-fit. Paired with the "
                     "nondelivery-* cases (which leave BY the failure exit and are "
                     "rejected) this pins clause (5) to the exit, not to the presence "
                     "of a raise.",
    },
    {
        "id": "nondelivery-signalled-away-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_SIGNALAWAY),
        "refinement": "The faithful real patch keeps the new rendering helper "
                      "verbatim and replaces the disagreement branch's "
                      "`raise ValueError(<the assembled message>)` with a bare "
                      "`raise Exception()`: the message is never assembled, so "
                      "nothing tells the reader which names were demanded or found. "
                      "It applies cleanly at base_commit and does NOT resolve — F2P "
                      "test_required_columns fails (it matches on the message text) "
                      "and P2P test_empty_initialization_invalid regresses for the "
                      "same reason.",
        "rationale": "THE DELIVERY HOLE. The impl declares its own "
                     "Exsures(Exception, <the three input permissions>) inside the "
                     "marker-elided impl region -- invisible to same_spec -- and "
                     "leaves by that exit. It TERMINATES, so both MustTerminate "
                     "measures are discharged; and every Ensures clause, the three "
                     "Old(...) preservation clauses included, is silent on an "
                     "exceptional exit, so all of them hold vacuously. This impl "
                     "therefore VERIFIED against this spec before clause (5) existed. "
                     "Source: clause (5) / Exsures(Exception, False) at the "
                     "report-assembly site, which Nagini conjoins with the smuggled "
                     "declaration so the False remains to be discharged. Rejection: "
                     "'Postcondition of compose_leading_run_report might not hold. "
                     "Assertion False might not hold.'",
    },
    {
        "id": "nondelivery-signalled-away-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_SIGNALAWAY),
        "refinement": "The faithful real patch makes the new rendering helper signal "
                      "instead of returning a string, so EVERY disagreement message "
                      "-- multi-name and legacy single-name alike -- is replaced by "
                      "an unrelated failure. F2P test_required_columns fails and the "
                      "single-column P2P scenarios regress; the patch does not "
                      "resolve.",
        "rationale": "The same non-delivery smuggle at the RENDERING site. It matters "
                     "that this is now rejected BY THE SPEC: before clause (5) this "
                     "site was protected only INCIDENTALLY, because the assembly "
                     "calls it and the assembly declared no exceptional contract, so "
                     "the caller's own exception-freedom check happened to catch it. "
                     "That protection is an artefact of the call graph and vanishes "
                     "for any site without an in-module caller -- which is exactly "
                     "why the assembly site was open. Source: clause (5) / "
                     "Exsures(Exception, False) on render_name_run; the rejection now "
                     "names render_name_run's own postcondition.",
    },
    {
        "id": "nondelivery-true-contract-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_TRUE_OVERRIDE),
        "refinement": "Same faithful patch as nondelivery-signalled-away-report (the "
                      "assembled message replaced by a bare failure); it does not "
                      "resolve for the same reason.",
        "rationale": "Probes the mechanism clause (5) relies on rather than its "
                     "wording: the impl region declares a trivially TRUE exceptional "
                     "contract for EXACTLY the type the frozen clause names, betting "
                     "that the later declaration replaces the frozen one. Nagini "
                     "collects every Exsures for a type and emits one obligation per "
                     "declaration, so the frozen False is still there to discharge and "
                     "the True adds nothing. Source: clause (5). If this ever VERIFIED "
                     "the clause would be decorative and the hole would be open again "
                     "under a one-line rewrite.",
    },
    {
        "id": "nondelivery-reraise-from-handler",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_RERAISE),
        "refinement": "Same faithful patch as nondelivery-signalled-away-report; the "
                      "message is still never assembled, so it does not resolve.",
        "rationale": "Third spelling of the same exit: the object that leaves is a "
                     "RE-RAISE of a caught one rather than a freshly built one, so the "
                     "departure passes through a handler first. Included because "
                     "internal-signal-caught-admitted must verify while this must not: "
                     "together they show clause (5) discriminates on whether the "
                     "method LEAVES by the failure exit, not on whether a raise or a "
                     "handler appears in the body. Source: clause (5).",
    },
    {
        "id": "nondelivery-partial-multiname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_SIGNAL_MULTINAME),
        "refinement": "The faithful real patch assembles and raises the gold message "
                      "whenever at most one column is required and raises a bare "
                      "failure when more than one is -- i.e. it reproduces every "
                      "legacy single-column message exactly and delivers nothing on "
                      "precisely the multi-name runs the change exists for. All the "
                      "single-column P2P scenarios pass; F2P test_required_columns "
                      "(demanded ['time','a']) fails. The patch does not resolve.",
        "rationale": "The sharpest delivery rival: partial-domain x non-delivery. It "
                     "is byte-for-byte gold on len(demanded) <= 1 and leaves by the "
                     "failure exit on len(demanded) > 1, so a battery that only "
                     "probed value-correctness on the legacy runs would see nothing "
                     "wrong. MustTerminate is discharged on BOTH branches. Source: "
                     "clause (5), which is demanded on every admissible triple and so "
                     "cannot be satisfied on a sub-domain.",
    },
    {
        "id": "nondelivery-late-after-build",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_LATE_SIGNAL),
        "refinement": "The faithful real patch builds the whole textual list form and "
                      "then signals instead of returning it, so the rendering helper "
                      "yields no string and every disagreement message is lost. F2P "
                      "fails, the single-column P2P scenarios regress; it does not "
                      "resolve.",
        "rationale": "Fifth spelling, and the one that shows the clause is about "
                     "DELIVERY rather than about doing the work: every gold loop "
                     "Invariant holds, the accumulated rendering is correct and "
                     "complete at the moment of departure, and the impl still leaves "
                     "by the failure exit on the final iteration. Value-correct "
                     "internally, delivering nothing. Source: clause (5) / "
                     "Exsures(Exception, False) on render_name_run.",
    },
    {
        "id": "overapprox-always-bracketed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_ALLBRACKET),
        "refinement": "A faithful real patch whose helper dropped the len(obj) == 1 "
                      "case and always returned str(obj) renders a lone required "
                      "column as \"['time']\" where the message must read "
                      "\"'time'\". The single-required-column disagreement messages "
                      "the P2P suite asserts on (test_sampled / test_binned "
                      "single-column scenarios) then mismatch, so the patch "
                      "regresses them; it is a coarsening that keeps every name.",
        "rationale": "OVER-APPROXIMATION: every name, its order and its apostrophes "
                     "are kept and only the structural distinction of clause (1) -- "
                     "a run of exactly one name renders BARE, any other length "
                     "renders bracketed -- is coarsened away, so the impl satisfies a "
                     "strictly weaker property than the spec pins. On len(run) == 1 "
                     "it returns [LBRACK] + quoted(run[0]) + [RBRACK] != "
                     "quoted(run[0]) == render_run(run). Source: the render_run "
                     "postcondition, whose len == 1 branch is exactly this "
                     "distinction.",
    },
    {
        "id": "partial-domain-len2-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_LEN2GUARD),
        "refinement": "A faithful real patch guarding on len(required_columns) == 2 "
                      "and emitting only the first name there behaves gold on every "
                      "other length. Length 2 is the F2P scenario itself (demanded "
                      "['time','a']), so test_required_columns sees \"expected "
                      "'time'\" instead of \"expected ['time', 'a']\" and FAILS; "
                      "the patch does not resolve.",
        "rationale": "PARTIAL-DOMAIN GUARD aimed at one length rather than at a "
                     "branch: gold for len(demanded) in {0, 1, 3, 4, ...} and "
                     "first-name-only at exactly 2. Distinct from "
                     "partial-domain-first-name-only, which is wrong at every length. "
                     "A battery that probed lengths 0/1/3 only would miss it. The "
                     "load-bearing ToSeq(Result()) == report_seq(...) is demanded at "
                     "every length, so a single length suffices to fail it. Source: "
                     "the report_seq postcondition.",
    },
    {
        "id": "boundary-bracket-token-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_BRACKETSWAP),
        "refinement": "A faithful real patch that emitted the closing bracket first "
                      "and the opening one last (e.g. building the list form by hand "
                      "with the two delimiters transposed) renders \"]'time', "
                      "'a'[\" where the message must read \"['time', 'a']\". F2P "
                      "test_required_columns matches the message text exactly, so it "
                      "FAILS; the patch does not resolve.",
        "rationale": "BOUNDARY TOKEN SWAP, one edit: the two bracket code points are "
                     "exchanged and nothing else moves -- every name, its order and "
                     "every comma-space separator is byte-identical to gold. Pins "
                     "WHERE the delimiters fall, not merely that they are present. "
                     "Source: the render_run postcondition (PSeq(LBRACK) + joined + "
                     "PSeq(RBRACK), in that order).",
    },
    {
        "id": "boundary-plural-token-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_PLURALTOKEN),
        "refinement": "A faithful real patch using the adjacent letter for the plural "
                      "marker (plural = 't' instead of 's') emits \"as the first "
                      "columnt\" for a multi-name demanded run. F2P "
                      "test_required_columns asserts \"as the first columns\", so "
                      "it FAILS; the patch does not resolve.",
        "rationale": "BOUNDARY TOKEN SWAP on the other modeled site, and a different "
                     "kind of one from plural-marker-drop: the pluralisation RULE is "
                     "kept exactly right (marker iff len(demanded) > 1) and only the "
                     "marker's code point moves by one, 115 -> 116. So this "
                     "discriminates the identity of the token, where "
                     "plural-marker-drop discriminates the rule. Source: the plural "
                     "sub-term of the report_seq postcondition, which names PSeq(115) "
                     "literally.",
    },
    {
        "id": "echo-demanded-into-found",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_ECHOFOUND),
        "refinement": "A faithful real patch passing required_columns to BOTH "
                      "as_scalar_or_list_str calls (a plausible copy-paste of the "
                      "second argument) reports \"expected ['time', 'a'] ... but "
                      "found ['time', 'a']\" -- a report that always claims the "
                      "found names are the demanded ones, which is precisely the "
                      "uninformative shape issue #13009 is about, now at full-run "
                      "granularity. F2P test_required_columns asserts \"but found "
                      "['time', 'b']\" and FAILS; the patch does not resolve.",
        "rationale": "ECHO: the found slot is filled by echoing back the field "
                     "already computed for the demanded run, so the report is "
                     "self-consistent, structurally perfect, correctly pluralised, "
                     "and agrees with report_seq on every input where demanded == "
                     "found -- including every single-column legacy scenario. It is "
                     "wrong exactly where the two runs differ, i.e. on every real "
                     "disagreement. Source: the second render_run(found) sub-term of "
                     "the report_seq postcondition, which is what makes the found run "
                     "an independent observable rather than a restatement of the "
                     "demanded one.",
    },
    {
        "id": "recursive-descent-admitted",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_RECURSE),
        "rationale": "Clause (3) asks that a rendering be DELIVERED for every "
                     "admissible run, not that it be produced by any particular "
                     "traversal. This impl calls the renderer again on a STRICTLY "
                     "SHORTER run before returning the gold value, which is the shape "
                     "a structurally recursive rendering has. It must verify: a spec "
                     "that rejected it would forbid a correct implementation shape "
                     "(recursive descent) instead of demanding completion => "
                     "SPEC-TOO-STRONG / over-fit to the reference loop. Paired with "
                     "non-completion-render-multiname (same-run re-entry, rejected) "
                     "this pins clause (3) to non-delivery rather than to self-calls.",
    },
    {
        "id": "pos-control-reorder-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_POS),
        "rationale": "Structurally different but correct: the constant connective "
                     "segments (seg1/seg2/seg3) are computed BEFORE the two field "
                     "renders, and the two render_name_run calls are swapped (found "
                     "rendered first), with the same left-assoc final concatenation. "
                     "Every still-needed gold proof obligation is kept verbatim (the "
                     "plural Assert, the two render_run field Asserts, the final "
                     "report_seq Assert). plural is computed AFTER the two calls "
                     "(framing trigger: a call between a list local's construction and "
                     "use havocs its framed value), which is a proof-engineering "
                     "ordering, not a spec relaxation -- the returned value is the gold "
                     "concatenation. No loop flip / fold lemma introduced. Must verify, "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-three-readonly-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_ADMISS),
        "rationale": "Re-derives in-region that all three half-permission inputs "
                     "(cls_name, demanded, found) are usable (read via len/ToSeq and "
                     "the renderer) and reaches a normal non-raising return for an "
                     "in-domain (F2P-shaped) input. If any Requires were vacuous or "
                     "over-strong the impl could not both consume the permissions and "
                     "return => PRECOND-TOO-STRONG. Source: the three Acc(...,1/2) "
                     "Requires.",
    },
    {
        "id": "frame-mutation-write-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_FRAME),
        "refinement": "A faithful real patch in which as_scalar_or_list_str wrote "
                      "back into its input list (e.g. obj[i] = obj[i] / obj.sort()) "
                      "would mutate required_columns or the colnames slice that the "
                      "caller still holds. The gold helper only READS obj (str(obj), "
                      "f\"'{obj[0]}'\") and never mutates it; _check_required_columns "
                      "and its callers rely on required_columns / self.colnames being "
                      "untouched while building the message, so a mutating helper "
                      "would corrupt the very lists the F2P assertion is built from "
                      "and would not faithfully resolve test_required_columns.",
        "rationale": "render_name_run holds only Acc(list_pred(run), 1/2). The write "
                     "run[i-1] = elt (value-neutral, in-bounds via the loop bound) "
                     "needs FULL permission => Nagini rejects for INSUFFICIENT "
                     "PERMISSION. Source: the permission system + the Acc(...,1/2) "
                     "Requires. Gold invariants/asserts kept verbatim so the rejection "
                     "is attributable to the write, not a spec change.",
    },
    {
        "id": "partial-domain-first-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_FIRSTONLY),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): render "
                      "only required_columns[0] / self.colnames[0] regardless of run "
                      "length, inside the old expected '{}' ... found '{}' template. "
                      "For the F2P scenario (issue #13009, demanded ['time','a'], "
                      "found ['time','b']) it emits \"... expected 'time' ... but "
                      "found 'time'\" — the misleading first-name-only report the "
                      "issue is about — instead of \"... expected ['time', 'a'] ... "
                      "but found ['time', 'b']\". test_required_columns asserts the "
                      "full-run message, so the faithful patch does NOT resolve.",
        "rationale": "Both fields are rendered as the bare quoted FIRST name "
                     "[NAME_QUOTE, encode_name(x[0]), NAME_QUOTE] = quoted(x[0]). On a "
                     "multi-name run that != render_run(x) (which is the bracketed "
                     "full list), so the load-bearing postcondition "
                     "ToSeq(result) == report_seq(...) fails. Source: the report_seq "
                     "postcondition clause (full render_run of demanded AND found).",
    },
    {
        "id": "plural-marker-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_NOPLURAL),
        "refinement": "A faithful real patch that hard-coded plural = '' (dropped the "
                      "len(required_columns) > 1 test) would emit \"... as the first "
                      "column but found ...\" for a multi-name demanded run. The F2P "
                      "test asserts \"... as the first column*s* ...\" (plural), so "
                      "the message string mismatches and test_required_columns FAILS "
                      "— the patch does not resolve. The legacy single-column "
                      "scenarios (len 1) still pass, so it is a partial-domain miss "
                      "exactly on the new multi-name path.",
        "rationale": "plural is forced to [] regardless of len(demanded). report_seq "
                     "pins plural == PSeq(115) when len(demanded) > 1, so on a "
                     "multi-name demanded run ToSeq(result) != report_seq(...) and the "
                     "load-bearing postcondition fails. Source: the plural sub-term of "
                     "the report_seq postcondition.",
    },
    {
        "id": "partial-domain-drop-first-name-helper",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_DROPFIRST),
        "refinement": "A faithful real patch where as_scalar_or_list_str rendered "
                      "str(obj[1:]) (dropping the first name) would emit \"['a']\" "
                      "instead of \"['time', 'a']\" for the demanded run — the "
                      "disagreement report would omit the leading required column, so "
                      "test_required_columns (which asserts the full ['time', 'a']) "
                      "FAILS. The faithful patch does not resolve.",
        "rationale": "Loop `while i > 1` renders run[1:] only; at exit "
                     "ToSeq(inner) == joined(run_s.drop(1)), so "
                     "ToSeq(result) == [LBRACK] + joined(run_s.drop(1)) + [RBRACK] "
                     "!= render_run(run_s) on any run of length >= 2. The load-bearing "
                     "ToSeq(Result()) == render_run(ToSeq(run)) fails (the invariant "
                     "closes to drop(1), not drop(0)). Source: the render_run "
                     "postcondition clause.",
    },
    {
        "id": "non-completion-render-multiname",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_NOFINISH),
        "refinement": "A faithful real patch in which the new rendering helper's "
                      "multi-name branch re-entered itself on the same object "
                      "instead of producing the textual list form (a one-token "
                      "edit: as_scalar_or_list_str(obj) where the full-run "
                      "rendering belongs) renders every single-required-column "
                      "scenario exactly right and never returns on the "
                      "multi-name run. The F2P scenario (demanded ['time','a'], "
                      "found ['time','b']) then raises RecursionError instead of "
                      "the ValueError test_required_columns asserts on, so the "
                      "faithful patch does NOT resolve -- while the legacy "
                      "single-column P2P scenarios are untouched. This is the "
                      "sharpest partial-domain miss available: value-correct on "
                      "exactly the old behaviour, non-delivering on exactly the "
                      "new one.",
        "rationale": "The single-name branch is byte-for-byte gold; the other-length "
                     "branch never reaches a return. The value clause "
                     "ToSeq(Result()) == render_run(ToSeq(run)) constrains only runs "
                     "that reach a return and so is discharged vacuously here. "
                     "Source: clause (3) / the completion budget at this site, which "
                     "grows with the run so that working it down name by name stays "
                     "admissible: re-asking about a run no shorter than the current one "
                     "does not decrease it.",
    },
    {
        "id": "non-completion-report-assembly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_NOFINISH),
        "refinement": "A faithful real patch where the disagreement branch re-entered "
                      "the check that raises it instead of building and raising the "
                      "message never delivers a report on ANY input: the F2P "
                      "assertion never sees its ValueError, and the legacy "
                      "single-column P2P scenarios that also go through this branch "
                      "(e.g. test_empty_initialization_invalid) regress too. The "
                      "faithful patch does NOT resolve.",
        "rationale": "No return is ever reached, so ToSeq(Result()) == report_seq(...) "
                     "is vacuous. Source: clause (3) / the completion budget at the "
                     "report-assembly site -- the same non-delivery hole at the other "
                     "modeled site, which a clause added at site A alone would not "
                     "close.",
    },
    {
        "id": "non-completion-render-loop-no-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_STUCKLOOP),
        "refinement": "A faithful real patch that built the textual list form with a "
                      "loop whose index never advanced would hang (never return a "
                      "string) whenever the run has two or more names, so the F2P "
                      "scenario never produces its ValueError and "
                      "test_required_columns FAILS by timeout rather than by a "
                      "message mismatch. The faithful patch does NOT resolve.",
        "rationale": "Every value-level gold Invariant is kept VERBATIM and the "
                     "accumulated `inner` is correct at each step, so no value "
                     "obligation is what fails -- and there is no self-call, so this "
                     "is not the same path as the two cases above. Source: clause (3) "
                     "as carried by the loop measure Invariant(MustTerminate(i + 1)), "
                     "which cannot be maintained when `i` does not decrease.",
    },
    {
        "id": "aliased-input-rewritten",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_ALIASWRITE),
        "refinement": "A faithful real patch whose rendering helper NORMALISED the "
                      "names in place before rendering them (e.g. "
                      "obj[0] = obj[0].strip() / obj.sort() at the top of "
                      "as_scalar_or_list_str) rewrites the very list it was handed. "
                      "At the demanded-run call site that list IS the container's "
                      "class-level _required_columns, not a copy, so the rewrite "
                      "outlives the message: test_required_columns builds one series "
                      "and asserts a succession of disagreement messages against the "
                      "same required-columns list, and after the first assertion that "
                      "list no longer holds the names the later assertions expect, so "
                      "their message text mismatches and the test FAILS. The gold "
                      "helper only READS obj (str(obj), f\"'{obj[0]}'\") and the "
                      "surrounding .format(...) only reads, so the faithful patch of "
                      "this impl does NOT resolve.",
        "rationale": "RIGHT VALUE, WRONG EFFECT at the aliased boundary. Two "
                     "Acc(list_pred(x), 1/2) held on the SAME object sum to full "
                     "permission, so when `demanded is found` this impl may write, and "
                     "it does (demanded[0] += 1) before rendering. Every value clause "
                     "still holds -- the returned report equals report_seq of the runs "
                     "as they read at return -- and the gold Asserts all discharge, so "
                     "this impl VERIFIED before clause (4) existed. Source: clause (4) "
                     "/ Ensures ToSeq(demanded) == Old(ToSeq(demanded)), which pins the "
                     "report to the runs AS GIVEN and is what now fails. Distinct from "
                     "frame-mutation-write-run: that one is rejected for insufficient "
                     "permission, which no aliasing at site A can supply.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom). The deep
# models render_run / report_seq are A-references already validated == the REAL
# as_scalar_or_list_str helper and the REAL .format(...) by axiom_check.py (G-AX):
# 9 boundary runs (lengths 0/1/2/3 incl. the F2P scenario) + 6 fixed reports +
# 20000 fuzz reports over an identifier alphabet, expanding each name token to its
# real string and asserting equality, 0 mismatch, stdlib-only, exit 0. That IS the
# real-callee axiom lane for this instance; re-encoding it as a Docker probe would
# duplicate, not strengthen, it. See 'assessment' in the structured return.
AXIOM_TESTS = []
