"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7748 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or
instantiates the obligation, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_collectSignatures`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the reading behavior as an integer-stream abstraction: a continuation-flag
list ``cont`` and a per-line value list ``val``, with the two fractional
half-permissions that abstraction needs, and a postcondition split into three
clauses (whole-sequence equality, length, head). This Lean bundle models the
behavior at its real carrier — blocks of text lines and the candidate-name list —
in ONE total function, and the postcondition is a SINGLE structural equality
(``result = collectSpec validNames docstrings``) that subsumes all three nagini
clauses at once: length, order, and each entry's argument string and return
annotation are pinned together. So the nagini cases carry over as attacks on that
one equality, and the carrier is RICHER rather than narrower: the flag/value
abstraction had collapsed the marker-stripping step, the recognition step and the
candidate-name filter into "the flag" and "the value", and each of those is a
separately attackable decision here. The per-case mapping (ported / omitted, and
why) is in ``assessment``.

DEFENDED SURFACE (one modeled behavior, one obligation). The result is exactly
the ordered list of signatures the documentation comment offers at its start. The
single postcondition equality is grounded in the inputs — ``collectSpec`` and
``scanDoc`` are concrete recursive functions over the actual block list, whose
only opaque leaf is the line-recognition matcher, which the implementation
invokes IDENTICALLY — so it is dischargeable only by performing the same scan.
Although the postcondition is one top-level clause, the grounding term is a
recursion with several INDEPENDENT decisions, and each is separately attackable:

  * the empty line ends the run of the block it is in;
  * a line carrying a continuation marker is matched in its STRIPPED form (the
    marker and the whitespace under it are dropped before recognition);
  * a recognised line counts only when its thing name is a candidate;
  * a recognised candidate line WITHOUT a continuation marker is the last one of
    the run — collected, and then the run stops;
  * a recognised candidate line WITH a continuation marker is collected and the
    reading continues onto the next line;
  * the first block that offers any signature supplies the WHOLE result, and no
    later block contributes.

The BEHAVIOURAL DISCRIMINATOR (the desired behavior): a block whose leading line
carries a continuation marker must yield EVERY signature of its leading run, in
order, and not just the first — and the first one must have had its marker
stripped before recognition. That is the F2P shape: the two ``__init__``
signature lines of the fixture class, the first continued. The nagini sibling
encodes exactly this as ``cont[0] != 0 => run_len >= 2``.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and demonstrated so rather than
    asserted. Lean is referentially transparent: an input carries no heap
    permission, so there is no read-only half-permission to write through and no
    aliasing to exploit. Measured, so the vacuity is not merely argued: the
    closest expressible analogue — rebind both inputs and "write through" the
    rebound copies (``docs := docs ++ []``, ``names := names ++ []``) before
    scanning — is OBSERVATIONALLY IDENTICAL to the frozen impl, so it is a
    correct reshape and not a rival at all. Built against the frozen proof script
    it fails only because the representation bridge rewrites on ``forIn
    docstrings`` while the reshape presents ``forIn (docstrings ++ [])``
    (``Tactic `rewrite` failed: Did not find an occurrence``); adding
    ``List.append_nil`` to that one ``simp only`` closes it (exit 0). A rival
    that cannot be made to disagree with the frozen impl on any input is vacuous
    by attack C, so no substitute is fabricated for this class.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE in the reject lane, not a
    vacuous class. This disposition is corrected by the post-port audit; the
    previous text claimed "a non-terminating implementation cannot be written at
    all", and that claim is FALSE. Measured: an impl region declaring
    ``partial def implementation_collectSignatures`` over an unbounded helper
    (``partial def spin ... | n => spin ... (n + 1)``) passes
    ``variant_scope.variant_problems`` — ``partial`` is not an assumption-bearing
    token there — and elaborates as an admissible variant. So the rival IS
    expressible on this carrier. It is also genuinely REJECTED (exit 1,
    ``simp`` made no progress at the obligation): this bundle sets no
    ``loom.semantics.termination`` option at all, the frozen obligation is an
    ordinary total-carrier equation, and a ``partial`` constant does not reduce,
    so nothing discharges it vacuously.

    What blocks the case is the WITNESS requirement, not expressibility. The
    refutation may only use vocabulary the rival and the frozen solution SHARE
    (``pbt_witness.witness_scope_problems`` rejects naming the rival's own
    helper), so the only statable witness conditions on the diverging impl's
    result at a concrete input
    (``hout : implementation_collectSignatures [["A(y)"]] ["A"] = []``). That
    hypothesis is false of the frozen solution, so the witness proves its
    refutation there too: rebuilt, it holds of the rival (exit 0) AND of the
    frozen solution (exit 0), which the gate records as ``witness-vacuous`` — an
    inconclusive outcome, i.e. a gate ERROR rather than a passing case. The
    consistency probe does not catch it either (exit 1 on both sides: no tactic
    derives ``False`` from an opaque-conditioned hypothesis). So there is nothing
    shippable here, and the class is recorded as an admitted hole rather than
    fabricated into a case that would fail the gate. (The nagini sibling carries
    no divergence rival either.) Backend contrast:
    ``the corpus-wide termination-semantics finding`` covers the velvet situation, where a
    partial-termination setting makes the same class a spec hole that VERIFIES.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason the nagini sibling
    gives: the grounding term is a fully spelled-out recursion over the input
    lists, not an opaque answer key, so there is no value an implementation could
    echo without performing the scan. In its place the battery carries honest
    positive controls that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole reject lane lives.
    Each rival is correct on a sub-domain and diverges where one of the decisions
    above bites. Three of the nine are the direct descendants of nagini's three
    partial-domain rivals (``first-only`` -> ``keep-only-first``;
    ``over-collect-all`` -> ``never-stop-at-terminator``; ``drop-terminator`` ->
    ``omit-final-line``); the other six attack decisions the nagini carrier had
    abstracted away and could not express.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the
postcondition predicate directly at one concrete input and refuting it. Each was
checked by hand, before shipping, to HOLD of its rival and to FAIL on the frozen
solution.

A property of this carrier drives the witness shape. The recognition matcher is
``opaque`` and the trailing-marker test on a string LITERAL does not reduce
either: measured, ``example : "A(y)".endsWith "\\" = false := by decide`` fails
with ``reduction got stuck at the Decidable instance
instDecidableEqBool ("A(y)".endsWith "\\") false``, and ``simp`` on the same goal
reports ``made no progress``. So no witness here can be stated purely by
evaluation. Each witness therefore CONDITIONS on the carrier: it assumes the
marker test's value at its literal lines and the matcher's outcome at the exact
strings the scan will hand it, and refutes the equality on the sub-domain those
assumptions describe. The assumptions are kept as weak as each refutation needs —
one per opaque term per line, never two about the same term — so they are jointly
satisfiable (each was probed for that, and the gate probes it too). Everything
else in the carrier IS transparent and is left to compute: the empty-line test,
the marker-stripping function, the candidate-name membership test, the traversal
order, and the block-to-block hand-off.

BINDER / POINT SPREAD. The postcondition has two input binders, ``docstrings``
and ``validNames``, and the nine reject witnesses move BOTH rather than pinning
either at one convenient value. ``docstrings`` ranges over a one-block/one-line
comment, a one-block/two-line continued run, a two-line run with NO continuation
marker, a block whose first line is empty, a two-line block opening on a line the
matcher REJECTS, a two-line block whose lines carry two different thing names,
and a two-BLOCK comment; ``validNames`` ranges over a matching single candidate,
a non-matching candidate (the name filter's own refutation), a candidate matching
only the block's SECOND line, and a two-candidate list. Nine rivals, nine
distinct input points — no two rivals share a refutation point, so each
``rationale``'s sub-domain claim is the one its own witness demonstrates.

AUDIT 2 (independent, post-port, adversarial). All 12 shipped cases re-derived
with real builds. Statement integrity: the ``theorem correct_collectSignatures``
statement is byte-identical to the frozen file in all 12 modules (extracted and
hashed), and every module is ``same_spec`` + in ``variant_scope``. Witnesses: all
nine rebuilt against the rival (exit 0), the frozen solution (exit 1), and as a
bare consistency probe (exit 1). The gold-side failure is ``⊢ False`` with the
witness's own hypotheses in context in ALL NINE — ``simp`` reduced the spec fully
and PROVED the equality of the frozen impl at that input. FORGERY test (attack
B′) run on all nine even though the signature is a plain evaluation: the
claim-flipped witness (``¬`` dropped, i.e. asserting the frozen impl is CORRECT
there) builds CLEAN on gold (exit 0) and FAILS on every rival (exit 1) — the
exact anti-diagonal of the real witness, so gold's exit code demonstrably tracks
the claim and none of the nine is hollow. Nine distinct refutation points
confirmed (no two rivals share one); the ``validNames`` binder takes four
distinct values. Attack D: eight NEW wrong impls the battery did not contain
(reversed subsequent order, primary-signature-last, swapped Sig fields, dedup of
repeated signatures, strip-on-every-line, marker-only strip leaving the
whitespace, empty-line test deleted, run capped at two) — ALL EIGHT REJECTED, so
no spec hole in the too-weak direction. Attack E: three correct reshapes; the
hoisted-marker nesting verifies against the frozen script untouched, and the two
negated-guard reshapes verify once the analogous ``Bool.not_*`` rewrites are
supplied (``!result.isSome`` for the primary/subsequent split, exit 0 via a
``cases`` on the ``Option``; the negated hand-off, exit 0) — so both are
proof-script tuning, NOT a soundness hole in the spec. One repair landed from
attack E: ``pos-negated-handoff`` (above), the soundness control the outer
hand-off decision had been missing. Two prose dispositions corrected, both
measured wrong: the divergence class (a ``partial def`` rival IS expressible and
IS rejected — a known hole, not a vacuous class) and the frame-mutation class
(vacuous because its only expressible analogue is observationally identical to
the frozen impl, which is now demonstrated with builds rather than asserted).

AUDIT (independent, post-port). Every reject witness was rebuilt from scratch
against its rival, against the frozen solution, and as a bare consistency probe:
all nine hold of the rival (exit 0), fail on the frozen solution (exit 1), and
fail to derive ``False`` from their own hypotheses (exit 1, so the refutation
points exist). The gold-side failure is the strongest available shape in every
case — ``simp`` reduces the spec fully and leaves ``⊢ False``, i.e. it PROVES the
equality holds of the frozen solution at that input rather than getting stuck on
an opaque term. Two defects were found and repaired: one positive control's
"needs a reproven obligation" claim was false (its impl verified against the
byte-untouched frozen script, so its paired proof edit was inert) and is replaced
by ``pos-negated-marker-test``, which does fail against the frozen script; and
the two run-continuation decisions of the matcher's ``none`` branch and the
name filter's reject arm were unprobed, now covered by ``stop-at-unrecognised``
and ``stop-at-noncandidate``. Four further wrong impls were written and all four
were REJECTED by the frozen spec (stop-at-unrecognised, stop-at-noncandidate,
reversed subsequent-signature order, primary-signature-last), so no spec hole was
found in the too-weak direction.

AXIOM lane: EMPTY. ``AXIOM_TESTS`` is dropped per the port contract — the axiom
lane is G-AX's job. (This bundle consumes no axiom in any case: the one
``opaque`` leaf is an A-reference used identically in the spec helper and the
implementation, so it cancels in the correctness argument.)
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7748"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly at
    load rather than shipping a case that no longer says what it claims."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swap_n(src: str, old: str, new: str, n: int) -> str:
    """`_swap` for an anchor that legitimately occurs exactly ``n`` times, all
    of which must change together. Used by the negated-marker positive, whose
    proof repair applies to BOTH `by_cases he` arms of the representation
    bridge; asserting the count pins the drift check just as tightly as
    `_swap` does for a unique anchor."""
    if src.count(old) != n:
        raise AssertionError(f"drift: expected {n} of {old!r}, "
                             f"got {src.count(old)}")
    return src.replace(old, new)


# ---------------------------------------------------------------------------
# Surgery anchors — verbatim slices, each lying ENTIRELY inside the impl region
# (except _AT_PROOF_END, which anchors the proof region for the instantiation
# case) and each unique in the file.
# ---------------------------------------------------------------------------

# The tail of the accept branch: what to do after a candidate line has been
# recorded — keep reading (marker present) or stop the run (marker absent).
_TAIL = ("          if multiline then\n"
         "            continue\n"
         "          else\n"
         "            break\n")

# The whole accept branch: the candidate-name test, the primary/subsequent
# split, and the tail above.
_ACCEPT = ("        if validNames.contains m.base then\n"
           "          if result.isNone then\n"
           "            result := some ⟨m.args, m.retann⟩\n"
           "          else\n"
           "            signatures := signatures ++ [⟨m.args, m.retann⟩]\n"
           "          if multiline then\n"
           "            continue\n"
           "          else\n"
           "            break\n"
           "        else\n"
           "          continue\n")

# The empty-line terminator.
_EMPTY = ("      if line0.isEmpty then\n"
          "        break\n")

# The marker-stripping step feeding the recognition matcher.
_STRIP = ("      let line := if multiline then stripContinuation line0 else line0\n"
          "      match matchSig line with\n"
          "      | none => continue\n")

# The block-to-block hand-off: stop once a block has offered a signature.
_HANDOFF = ("    if result.isSome then\n"
            "      break\n")

_AT_PROOF_END = "-- proof-end"


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [

    # ======================= UNIQUENESS (reject) ===========================

    # (1) KEEP-ONLY-FIRST — the direct port of nagini's `first-only`, which is
    # the behavior the desired change replaces: record the run's first
    # signature and stop, whether or not the line carried a continuation
    # marker. Correct exactly on the sub-domain where the leading run is one
    # line long; wrong wherever a continuation marker asks for more.
    {"id": "keep-only-first", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _TAIL, "          break\n"),
     "rationale": "attacks the continuation decision of the grounding "
                  "recursion (`scanDoc`'s marker branch, which conses the "
                  "signature onto the run of the REST). The witness probes a "
                  "one-block comment whose first line carries a marker and "
                  "whose second terminates: the postcondition demands both "
                  "signatures in order, this rival hands back only the first, "
                  "so the equality fails. It holds on the run_len==1 "
                  "sub-domain, which is why nothing cheaper than the marker "
                  "branch refutes it. Binders: `docstrings` a two-line "
                  "continued run, `validNames` the matching single candidate.",
     "refinement": "a faithful real patch of this shape reads every leading "
                   "line but still keeps at most ONE signature per comment. On "
                   "the F2P fixture — the class whose __init__ documentation "
                   "offers two signature lines, the first continued — the "
                   "expected rendering is the two-line block "
                   "(`E(foo: int, ...) -> None` followed by the indented "
                   "`E(foo: str, ...) -> None`), and this renders only the "
                   "first line. Both F2P tests assert the full two-line "
                   "rendering, so it would NOT resolve.",
     "witness": r'''
example (he1 : "A(x)\\".endsWith "\\" = true)
        (he2 : "A(y)".endsWith "\\" = false)
        (hm1 : matchSig (stripContinuation "A(x)\\") = some ⟨"A", "x", ""⟩)
        (hm2 : matchSig "A(y)" = some ⟨"A", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["A(x)\\", "A(y)"]] ["A"]
        (implementation_collectSignatures [["A(x)\\", "A(y)"]] ["A"]) := by
  have h1 : "A(x)\\".isEmpty = false := by decide
  have h2 : "A(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he1, he2, hm1, hm2, h1, h2]
'''},

    # (2) NEVER-STOP-AT-TERMINATOR — the port of nagini's `over-collect-all`:
    # keep reading after EVERY recognised candidate line, marker or not, so the
    # run runs to the end of the block. Correct exactly where every line of the
    # leading run carries a marker; wrong as soon as one does not.
    {"id": "never-stop-at-terminator", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _TAIL, "          continue\n"),
     "rationale": "attacks the OTHER arm of the same decision — the "
                  "no-marker branch of `scanDoc`, which returns the singleton "
                  "run and stops. The witness probes a two-line block where "
                  "NEITHER line carries a marker: the postcondition demands "
                  "just the first line's signature, this rival collects both, "
                  "so the equality fails on length and content. Deliberately "
                  "the mirror image of keep-only-first, and refuted at a "
                  "different point (no marker anywhere, versus a marker on the "
                  "leading line) because the two rivals agree with the frozen "
                  "solution on disjoint halves of the marker domain. Binders: "
                  "`docstrings` a two-line UNcontinued block, `validNames` the "
                  "matching single candidate.",
     "refinement": "a real patch that omits the stop condition keeps "
                   "scanning after a signature line that offers no "
                   "continuation, so it absorbs whatever follows in the "
                   "documentation comment — prose the recogniser happens to "
                   "accept, or a second unrelated signature — into the "
                   "rendered signature block. The P2P fixtures whose leading "
                   "documentation line is a lone signature followed by "
                   "descriptive text (the single-signature classes, and the "
                   "method whose first line is a signature and second is prose) "
                   "assert a ONE-line rendering, so this both fails the F2P "
                   "expectations and breaks passing tests: it would NOT resolve.",
     "witness": r'''
example (he1 : "A(x)".endsWith "\\" = false)
        (he2 : "A(y)".endsWith "\\" = false)
        (hm1 : matchSig "A(x)" = some ⟨"A", "x", ""⟩)
        (hm2 : matchSig "A(y)" = some ⟨"A", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["A(x)", "A(y)"]] ["A"]
        (implementation_collectSignatures [["A(x)", "A(y)"]] ["A"]) := by
  have h1 : "A(x)".isEmpty = false := by decide
  have h2 : "A(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he1, he2, hm1, hm2, h1, h2]
'''},

    # (3) OMIT-FINAL-LINE — the port of nagini's `drop-terminator`: collect the
    # marker-carrying lines but stop WITHOUT recording the line that ends the
    # run. Off-by-one on the run's last element; a NEAR-MISS of
    # keep-only-first, so it gets its own, sharper refutation point (a single
    # uncontinued line, where this rival returns nothing at all and
    # keep-only-first is correct).
    {"id": "omit-final-line", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _ACCEPT,
                     "        if validNames.contains m.base then\n"
                     "          if multiline then\n"
                     "            if result.isNone then\n"
                     "              result := some ⟨m.args, m.retann⟩\n"
                     "            else\n"
                     "              signatures := signatures ++ [⟨m.args, m.retann⟩]\n"
                     "            continue\n"
                     "          else\n"
                     "            break\n"
                     "        else\n"
                     "          continue\n"),
     "rationale": "attacks the same no-marker branch as "
                  "never-stop-at-terminator but from the opposite side: that "
                  "branch says the last line of the run is COLLECTED and then "
                  "reading stops, and this rival stops without collecting it. "
                  "Refuted at the smallest input that isolates the off-by-one — "
                  "a single-line block with no marker, where the postcondition "
                  "demands the one-element list and this rival returns the "
                  "empty one. Given its own point rather than sharing "
                  "keep-only-first's: on that two-line continued run both "
                  "rivals are wrong, but here keep-only-first is CORRECT and "
                  "this one is not, which is the sub-domain its rationale "
                  "claims. Binders: `docstrings` a one-line block, "
                  "`validNames` the matching single candidate.",
     "refinement": "a real patch of this shape records a signature only from "
                   "a line that promises a continuation, so the final "
                   "signature of every run is dropped — and a documentation "
                   "comment offering a single, uncontinued signature line "
                   "yields no signature at all. That regresses the P2P "
                   "single-signature fixtures (whose rendering carries the "
                   "signature read from the docstring) as well as rendering "
                   "the F2P fixture one signature short, so it would NOT "
                   "resolve.",
     "witness": r'''
example (he : "A(y)".endsWith "\\" = false)
        (hm : matchSig "A(y)" = some ⟨"A", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["A(y)"]] ["A"]
        (implementation_collectSignatures [["A(y)"]] ["A"]) := by
  have h1 : "A(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he, hm, h1]
'''},

    # (4) NO-MARKER-STRIP — feed the recognition matcher the RAW line instead
    # of the stripped one. New on this carrier: nagini's flag/value abstraction
    # had already collapsed "the marker" into a boolean and "the value" into an
    # integer, so the stripping step it stands for was inexpressible there.
    {"id": "no-marker-strip", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _STRIP,
                     "      let line := line0\n"
                     "      match matchSig line with\n"
                     "      | none => continue\n"),
     "rationale": "attacks the stripping step of the grounding recursion: "
                  "`scanDoc` matches a marker-carrying line in its STRIPPED "
                  "form, so the signature recorded from it carries no trailing "
                  "marker or the whitespace under it. The witness probes a "
                  "line whose raw and stripped forms are recognised "
                  "DIFFERENTLY — the raw form's return annotation ends in the "
                  "marker, the stripped form's does not — and the "
                  "postcondition demands the stripped reading. The two "
                  "assumptions are about two DISTINCT terms (the matcher at "
                  "the raw string and at the stripped string), so they are "
                  "jointly satisfiable; the stripping function itself is "
                  "computed, not assumed. Binders: `docstrings` a one-line "
                  "continued block, `validNames` the matching single candidate.",
     "refinement": "a real patch that recognises the raw line records the "
                   "trailing marker as part of the signature it read, so the "
                   "F2P fixture's first signature renders with a stray "
                   "trailing marker (and trailing whitespace) inside it. Both "
                   "F2P tests assert the exact rendered signature strings, "
                   "which carry no marker, so it would NOT resolve. (The real "
                   "recogniser does accept the raw line here — its return "
                   "annotation group is permissive enough to swallow the "
                   "marker — which is why the rival produces a wrong signature "
                   "rather than no signature.)",
     "witness": r'''
example (he : "E(a) -> None \\".endsWith "\\" = true)
        (hraw : matchSig "E(a) -> None \\" = some ⟨"E", "a", "None \\"⟩)
        (hstripped : matchSig (stripContinuation "E(a) -> None \\")
          = some ⟨"E", "a", "None"⟩) :
    ¬ problem_spec_collectSignatures [["E(a) -> None \\"]] ["E"]
        (implementation_collectSignatures [["E(a) -> None \\"]] ["E"]) := by
  have h1 : "E(a) -> None \\".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he, hraw, hstripped, h1]
'''},

    # (5) ACCEPT-ANY-NAME — drop the candidate-name filter, accepting every
    # recognised line. Also new on this carrier: nagini's `val` stream carried
    # no thing name, so it had no filter to remove.
    {"id": "accept-any-name", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _ACCEPT,
                     "        if result.isNone then\n"
                     "          result := some ⟨m.args, m.retann⟩\n"
                     "        else\n"
                     "          signatures := signatures ++ [⟨m.args, m.retann⟩]\n"
                     "        if multiline then\n"
                     "          continue\n"
                     "        else\n"
                     "          break\n"),
     "rationale": "attacks the candidate-name decision: `scanDoc` SKIPS a "
                  "recognised line whose thing name is not among "
                  "`validNames`, so a comment offering only non-candidate "
                  "signature lines yields nothing. This is the only rival "
                  "whose witness moves the `validNames` binder off a matching "
                  "value — it probes a recognised line whose thing name is NOT "
                  "the candidate, where the postcondition demands the empty "
                  "list and this rival returns the signature anyway. Without "
                  "it, a rival mishandling the name filter would verify "
                  "unnoticed. Binders: `docstrings` a one-line block, "
                  "`validNames` a NON-matching candidate.",
     "refinement": "a real patch that drops the name check reads a signature "
                   "off any leading line the recogniser accepts, including one "
                   "naming a different object. The P2P fixture whose "
                   "documentation begins with descriptive prose that the "
                   "permissive recogniser still accepts as a signature would "
                   "then acquire a bogus signature, and the fixtures that "
                   "document one class while naming another in the leading "
                   "line would take the wrong one — so passing tests break and "
                   "it would NOT resolve.",
     "witness": r'''
example (he : "A(q)".endsWith "\\" = false)
        (hm : matchSig "A(q)" = some ⟨"A", "q", ""⟩) :
    ¬ problem_spec_collectSignatures [["A(q)"]] ["Z"]
        (implementation_collectSignatures [["A(q)"]] ["Z"]) := by
  have h1 : "A(q)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he, hm, h1]
'''},

    # (6) SKIP-BLANK-LINE — treat an empty line as a skip rather than as the
    # end of the block's run. Also new here: nagini's stream had no empty-line
    # element.
    {"id": "skip-blank-line", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _EMPTY,
                     "      if line0.isEmpty then\n"
                     "        continue\n"),
     "rationale": "attacks the empty-line decision: `scanDoc` returns the "
                  "EMPTY run for a block whose first line is empty, so nothing "
                  "past it is read. The witness probes a block whose first "
                  "line is empty and whose second is a recognised candidate: "
                  "the postcondition demands the empty list, this rival steps "
                  "over the blank and returns the later signature. This is the "
                  "only witness that moves `docstrings` onto a block with an "
                  "empty line, and the refutation is entirely transparent — "
                  "the empty-line test computes, so only the second line's "
                  "recognition is assumed. Binders: `docstrings` a block "
                  "opening on an empty line, `validNames` the matching single "
                  "candidate.",
     "refinement": "a real patch that skips blank lines keeps reading past "
                   "the end of a documentation comment's leading region and "
                   "picks up signatures out of the body — a line deeper in the "
                   "prose that the recogniser accepts becomes the object's "
                   "signature. The P2P fixture whose documentation is a "
                   "signature line, a blank, then an indented body asserts a "
                   "rendering built from the leading region alone, so this "
                   "breaks a passing test and it would NOT resolve.",
     "witness": r'''
example (he : "A(y)".endsWith "\\" = false)
        (hm : matchSig "A(y)" = some ⟨"A", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["", "A(y)"]] ["A"]
        (implementation_collectSignatures [["", "A(y)"]] ["A"]) := by
  have h0 : "".isEmpty = true := by decide
  have h1 : "A(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he, hm, h0, h1]
'''},

    # (7) MERGE-ALL-BLOCKS — keep scanning later blocks and append their runs,
    # instead of letting the first block that offers anything supply the whole
    # result. Also new here: nagini's model had a single stream, hence no
    # block-to-block hand-off.
    {"id": "merge-all-blocks", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _HANDOFF,
                     "    if result.isNone then\n"
                     "      continue\n"),
     "rationale": "attacks the block-to-block hand-off: `collectSpec` returns "
                  "the FIRST block's non-empty run and never consults a later "
                  "block, so no later block may contribute. The witness probes "
                  "a TWO-block comment where each block offers one signature "
                  "and both names are candidates: the postcondition demands "
                  "the first block's singleton, this rival appends the second "
                  "block's signature too. This is the only witness that moves "
                  "`docstrings` to more than one block and the only one whose "
                  "`validNames` holds two candidates — a rival mishandling "
                  "either would otherwise go uncaught. Binders: `docstrings` a "
                  "two-block comment, `validNames` a two-candidate list.",
     "refinement": "a real patch that keeps going after a block has yielded "
                   "its run merges signatures from unrelated documentation "
                   "blocks into one rendering — for an inherited object, the "
                   "base's documentation block would be appended to its own. "
                   "The P2P fixtures covering inherited documentation and the "
                   "content-mode combinations assert renderings from a single "
                   "block, so this breaks passing tests and it would NOT "
                   "resolve.",
     "witness": r'''
example (he1 : "A(x)".endsWith "\\" = false)
        (he2 : "B(y)".endsWith "\\" = false)
        (hm1 : matchSig "A(x)" = some ⟨"A", "x", ""⟩)
        (hm2 : matchSig "B(y)" = some ⟨"B", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["A(x)"], ["B(y)"]] ["A", "B"]
        (implementation_collectSignatures [["A(x)"], ["B(y)"]] ["A", "B"]) := by
  have h1 : "A(x)".isEmpty = false := by decide
  have h2 : "B(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he1, he2, hm1, hm2, h1, h2]
'''},

    # (8) STOP-AT-UNRECOGNISED — an unrecognised line ENDS the run instead of
    # being skipped over. Added by the audit: the spec's prose names "lines that
    # are not recognised ... are skipped WITHOUT stopping" as its own clause, and
    # no shipped rival moved it — every one of the seven either changed what
    # happens to an ACCEPTED line or changed a test the accept path reaches
    # first, so the skip-and-continue arm of the matcher's `none` branch was
    # unprobed. Correct exactly where the leading run has no unrecognised line
    # before its signatures; wrong as soon as one intervenes.
    {"id": "stop-at-unrecognised", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, "      | none => continue\n",
                     "      | none => break\n"),
     "rationale": "attacks the matcher's `none` branch of the grounding "
                  "recursion: `scanDoc` recurses on the REST when the matcher "
                  "rejects a line, so an unrecognised line is stepped over and "
                  "the run continues past it. The witness probes a two-line "
                  "block whose first line the matcher rejects and whose second "
                  "is a recognised candidate: the postcondition demands the "
                  "second line's signature, this rival stops at the first and "
                  "returns the empty list. Distinct from skip-blank-line, which "
                  "moves the EMPTY-line test (a transparent test on a different "
                  "term) — here the line is non-empty and it is the matcher's "
                  "own verdict that must not terminate the run. Binders: "
                  "`docstrings` a two-line block opening on an unrecognised "
                  "line, `validNames` the matching single candidate.",
     "refinement": "a real patch that breaks on the first unrecognised line "
                   "reads a signature only from a documentation comment whose "
                   "very first leading line is already a signature. Any object "
                   "whose comment opens with a line the recogniser does not "
                   "accept — a one-word summary, a directive — then yields no "
                   "signature at all, so the P2P fixtures documenting such "
                   "objects lose the signature they assert. It also renders the "
                   "F2P fixture no better than the pre-change reader, so it "
                   "would NOT resolve.",
     "witness": r'''
example (he1 : "Q".endsWith "\\" = false)
        (he2 : "A(y)".endsWith "\\" = false)
        (hm1 : matchSig "Q" = none)
        (hm2 : matchSig "A(y)" = some ⟨"A", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["Q", "A(y)"]] ["A"]
        (implementation_collectSignatures [["Q", "A(y)"]] ["A"]) := by
  have h1 : "Q".isEmpty = false := by decide
  have h2 : "A(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he1, he2, hm1, hm2, h1, h2]
'''},

    # (9) STOP-AT-NONCANDIDATE — a recognised line whose thing name is NOT a
    # candidate ends the run instead of being skipped. Added by the audit as the
    # other half of the same gap: accept-any-name deletes the name filter's
    # EFFECT (it accepts what should be skipped) but nothing probed the filter's
    # CONTROL FLOW — that a rejected name skips onward rather than terminating.
    # A rival confusing "skip" with "stop" there passed unnoticed.
    {"id": "stop-at-noncandidate", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, "        else\n          continue\n",
                     "        else\n          break\n"),
     "rationale": "attacks the candidate-name branch's CONTINUATION, as "
                  "distinct from its verdict: `scanDoc` recurses on the REST "
                  "when a recognised line's thing name is not in `validNames`, "
                  "so a non-candidate signature line is skipped and the run "
                  "goes on. The witness probes a two-line block whose first "
                  "line is recognised under a NON-candidate name and whose "
                  "second is the candidate: the postcondition demands the "
                  "second signature, this rival stops at the first and returns "
                  "nothing. Complementary to accept-any-name, which probes the "
                  "same filter at a one-line block and asks whether the "
                  "non-candidate is wrongly COLLECTED; this asks whether it "
                  "wrongly ENDS the run, and the two are refuted at different "
                  "points. Binders: `docstrings` a two-line block whose lines "
                  "carry two different thing names, `validNames` the single "
                  "candidate matching only the SECOND.",
     "refinement": "a real patch that breaks on a non-candidate name stops "
                   "reading at the first leading line that documents something "
                   "else — an inherited or neighbouring object's signature line "
                   "sitting above the object's own. The object then renders "
                   "with no signature read from its documentation at all, "
                   "regressing the P2P fixtures whose leading region mixes "
                   "names, and it leaves the F2P fixture no better than before, "
                   "so it would NOT resolve.",
     "witness": r'''
example (he1 : "Z(q)".endsWith "\\" = false)
        (he2 : "A(y)".endsWith "\\" = false)
        (hm1 : matchSig "Z(q)" = some ⟨"Z", "q", ""⟩)
        (hm2 : matchSig "A(y)" = some ⟨"A", "y", ""⟩) :
    ¬ problem_spec_collectSignatures [["Z(q)", "A(y)"]] ["A"]
        (implementation_collectSignatures [["Z(q)", "A(y)"]] ["A"]) := by
  have h1 : "Z(q)".isEmpty = false := by decide
  have h2 : "A(y)".isEmpty = false := by decide
  unfold problem_spec_collectSignatures implementation_collectSignatures
  simp [collectSpec, scanDoc, he1, he2, hm1, hm2, h1, h2]
'''},

    # ======================= SOUNDNESS (verify) ============================

    # (8) POSITIVE CONTROL — the port of nagini's `honest-grounded`: a
    # local-variable reshape that binds the accepted signature once and uses
    # that binding in both arms, instead of rebuilding it per arm. Same work,
    # different shape; the obligation is reproven with the frozen tactic script
    # (the reshape is definitionally transparent to it).
    {"id": "pos-bind-signature", "kind": "soundness", "expect": "verify",
     "module": _swap(_BASE, _ACCEPT,
                     "        if validNames.contains m.base then\n"
                     "          let s : Sig := ⟨m.args, m.retann⟩\n"
                     "          if result.isNone then\n"
                     "            result := some s\n"
                     "          else\n"
                     "            signatures := signatures ++ [s]\n"
                     "          if multiline then\n"
                     "            continue\n"
                     "          else\n"
                     "            break\n"
                     "        else\n"
                     "          continue\n"),
     "rationale": "the grounded-oracle positive control (nagini's "
                  "`honest-grounded`): because the postcondition is pinned to a "
                  "spelled-out recursion over the inputs rather than to an "
                  "answer key, the cheapest faithful implementation still walks "
                  "the run and builds the list element by element. This one "
                  "binds the accepted signature into a local and reuses it in "
                  "both the primary and the subsequent arm — identical real "
                  "work, different shape. Must verify, else SPEC-TOO-STRONG."},

    # (9) POSITIVE CONTROL — the port of nagini's `pos-commute-break`: NEGATE
    # the marker test, so the tail reads "if NOT a continuation then stop else
    # keep reading". Same behavior, opposite polarity of the same branch.
    #
    # AUDIT NOTE. This slot previously held a different reshape — the marker
    # test hoisted ABOVE the primary/subsequent split, paired with an exchange
    # of the two `by_cases` in the representation bridge — and claimed the
    # obligation had to be REPROVEN for it. That claim was false and is the
    # defect this repair fixes: the hoisted-nesting impl was rebuilt against the
    # FROZEN proof script, byte-untouched, and it verified (exit 0). Its two
    # branch arms are definitionally equal to the frozen nesting, so the bridge
    # reduced without help and the paired proof edit was inert decoration — a
    # positive control that passed while demonstrating nothing about reproof.
    # This replacement is the reshape that does NOT reduce for free: rebuilt
    # against the frozen script it FAILS (exit 1, `unsolved goals` at the two
    # `by_cases he` arms of `impl_run_bridge`, case pos), because `!multiline`
    # is not syntactically the `if_true`/`if_false` pair those `simp only`s
    # discharge. Verifying therefore requires the `Bool.not_true`/
    # `Bool.not_false` rewrites this case adds, which is what makes the
    # reproof load-bearing rather than ornamental.
    {"id": "pos-negated-marker-test", "kind": "soundness", "expect": "verify",
     "module": _swap_n(
         _swap(_BASE, _TAIL,
               "          if !multiline then\n"
               "            break\n"
               "          else\n"
               "            continue\n"),
         # reprove the representation bridge: the negated guard needs the
         # `Bool.not_*` rewrites before the `if_true`/`if_false` pair applies.
         # The frozen file carries this block TWICE (the isNone and the
         # non-isNone arm), and both need the same repair, so `.replace` is
         # used rather than `_swap`'s uniqueness assertion.
         "              by_cases he : line0.endsWith \"\\\\\" = true <;>\n"
         "                simp only [he, Bool.false_eq_true, if_true, if_false]\n",
         "              by_cases he : line0.endsWith \"\\\\\" = true <;>\n"
         "                simp only [he, Bool.false_eq_true, if_true, if_false,\n"
         "                  Bool.not_true, Bool.not_false]\n", 2),
     "rationale": "structurally-different but CORRECT (nagini's "
                  "`pos-commute-break`): the tail's marker test is NEGATED and "
                  "its two arms swapped, so the branch reads \"if this line is "
                  "not a continuation, stop; otherwise keep reading\" — the "
                  "same decision at the opposite polarity, collecting the same "
                  "signatures in the same order. The obligation is REPROVEN, "
                  "not weakened: its statement is byte-identical, and the "
                  "tactic body adds the `Bool.not_true`/`Bool.not_false` "
                  "rewrites the negated guard needs for the representation "
                  "bridge's `if_true`/`if_false` reduction to fire. Checked "
                  "with real builds that the reproof is load-bearing: this "
                  "impl against the FROZEN script fails with `unsolved goals` "
                  "at both `by_cases he` arms of `impl_run_bridge`, and "
                  "verifies only with the rewrites added. Must verify, else "
                  "SPEC-TOO-STRONG: the postcondition would be pinning the "
                  "implementation's branch polarity rather than its result."},

    # (10) POSITIVE CONTROL — added by the post-port audit (attack E). The two
    # shipped positives both reshape the INNER loop's accept branch, so the outer
    # block-to-block hand-off had no soundness control on it: every case that
    # touched `if result.isSome then break` was a REJECT (merge-all-blocks), which
    # tests that changing the hand-off's BEHAVIOUR is caught but not that a
    # correct hand-off written in a different shape is still accepted. This
    # negates that guard and swaps its arms — "if a signature has NOT been found,
    # keep going; otherwise stop" — the same decision at the opposite polarity.
    #
    # Its reproof is load-bearing at a proof site neither shipped positive
    # reaches. Measured: against the FROZEN script this impl fails with
    # `unsolved goals` at BOTH arms (case pos AND case neg) of the outer
    # `by_cases hs : pa.isSome = true` in `impl_run_bridge` — the negated guard is
    # not syntactically the `if_true`/`if_false` pair those `simp only`s
    # discharge — and verifies (exit 0) once the `Bool.not_true`/`Bool.not_false`
    # rewrites are added there. pos-negated-marker-test repairs the two INNER
    # `by_cases he` arms; this repairs the OUTER `by_cases hs` arm, so the two
    # cases are not two spellings of one reproof.
    {"id": "pos-negated-handoff", "kind": "soundness", "expect": "verify",
     "module": _swap(
         _swap(_BASE, _HANDOFF,
               "    if !result.isSome then\n"
               "      continue\n"
               "    else\n"
               "      break\n"),
         # reprove the outer arm of the representation bridge: the negated guard
         # needs the `Bool.not_*` rewrites before `if_true`/`if_false` applies.
         "    by_cases hs : pa.isSome = true\n"
         "    · simp only [hs, if_true]\n"
         "    · simp only [hs, Bool.false_eq_true, if_false]\n",
         "    by_cases hs : pa.isSome = true\n"
         "    · simp only [hs, Bool.not_true, Bool.false_eq_true, if_false,\n"
         "        if_true]\n"
         "    · simp only [hs, Bool.not_false, Bool.false_eq_true, if_false,\n"
         "        if_true]\n"),
     "rationale": "structurally-different but CORRECT, on the one decision the "
                  "soundness lane had left uncontrolled: the block-to-block "
                  "hand-off. The guard is negated and its arms swapped, so the "
                  "outer loop reads \"if no signature has been found yet, go on "
                  "to the next block; otherwise stop\" — the same first-block-"
                  "wins behavior, the same result. The obligation is REPROVEN, "
                  "not weakened: its statement is byte-identical, and the tactic "
                  "body adds the `Bool.not_true`/`Bool.not_false` rewrites the "
                  "negated guard needs for the representation bridge's outer "
                  "`by_cases hs` reduction to fire. Checked with real builds "
                  "that the reproof is load-bearing AND lands at a different "
                  "site than pos-negated-marker-test's: against the frozen "
                  "script this impl fails with `unsolved goals` at both arms of "
                  "the OUTER `by_cases hs` (case pos and case neg), where the "
                  "negated-marker positive fails at the two INNER `by_cases he` "
                  "arms. Must verify, else SPEC-TOO-STRONG: the postcondition "
                  "would be pinning the polarity in which the hand-off is "
                  "written rather than which block supplies the result."},

    # ==================== ADMISSIBILITY (verify) ===========================

    # (10) The port of nagini's `admiss-class-e`: instantiate the modeled
    # behavior at the shape the desired behavior is about — a block whose
    # leading line carries a continuation marker and whose second line
    # terminates the run — and derive the concrete two-signature answer FROM
    # the obligation. The obligation has no precondition binder to be too
    # strong (it is `∀ docstrings validNames`), so what nagini checks as
    # "Requires is establishable" becomes "the obligation is USABLE at the
    # F2P-shaped input and yields the answer the desired behavior names".
    # Appended as an `example` inside the proof region: it declares no name, so
    # the variant scope check admits it and the frozen obligation is untouched.
    {"id": "admiss-continued-run", "kind": "admissibility", "expect": "verify",
     "module": _swap(_BASE, _AT_PROOF_END, r'''
-- The modeled behavior instantiated at the shape the desired behavior is about:
-- a block whose leading line carries a continuation marker and whose second
-- line terminates the run. The obligation must hand back BOTH signatures, in
-- order, with the marker dropped from the first.
example (he1 : "E(a) -> None \\".endsWith "\\" = true)
        (he2 : "E(b) -> None".endsWith "\\" = false)
        (hm1 : matchSig (stripContinuation "E(a) -> None \\")
          = some ⟨"E", "a", "None"⟩)
        (hm2 : matchSig "E(b) -> None" = some ⟨"E", "b", "None"⟩) :
    implementation_collectSignatures [["E(a) -> None \\", "E(b) -> None"]] ["E"]
      = [⟨"a", "None"⟩, ⟨"b", "None"⟩] := by
  have h1 : "E(a) -> None \\".isEmpty = false := by decide
  have h2 : "E(b) -> None".isEmpty = false := by decide
  have hgoal := correct_collectSignatures [["E(a) -> None \\", "E(b) -> None"]] ["E"]
  unfold problem_spec_collectSignatures at hgoal
  rw [hgoal]
  simp [collectSpec, scanDoc, he1, he2, hm1, hm2, h1, h2]
-- proof-end'''.lstrip("\n")),
     "rationale": "admissibility at the F2P-shaped input (nagini's "
                  "`admiss-class-e`, re-expressed): the obligation is applied "
                  "to a one-block comment whose leading line carries a "
                  "continuation marker and whose second line terminates, and "
                  "the concrete two-signature answer — both signatures, in "
                  "order, the first with its marker stripped — is derived FROM "
                  "it by rewriting with the obligation and computing the "
                  "grounding recursion. This obligation quantifies over all "
                  "inputs with no precondition, so there is no `Requires` to "
                  "be unsatisfiable; what is checked instead is that the "
                  "obligation is USABLE at the discriminating input and pins "
                  "the answer the desired behavior names, rather than being "
                  "vacuous or unreachable there. If it did not verify, the "
                  "obligation would not reach the shape the change is about."},
]

# ===========================================================================
# AXIOM CASES — dropped by the port contract (the axiom lane is G-AX's job).
# ===========================================================================
AXIOM_TESTS = []
