"""properties.py — G-PBT falsification battery for django__django-16502 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside a
``-- impl-start`` / ``-- impl-end`` region, or inside a ``prove_correct`` tactic
body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and both ``prove_correct`` headers survive with
byte-identical statements) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (two independent contracted operations, both total, neither
carrying a ``require`` clause — the pre-conditions regions are empty):

  prepareMeta (isHead : Bool) (isThreadingServer : Bool) (m : ResponseMeta)
              return (out : ResponseMeta)
    ensures out = adjustMeta isHead isThreadingServer m

  responseBody (isHead : Bool) (chunks : List (List Char))
               return (out : List Char)
    ensures out = bodyFor isHead chunks

Both post-images are fully-unfolded ``def``s in the ``pure`` region, GROUNDED in
the method's own arguments (directive 8) — not opaque answer keys, so there is
no ungrounded-oracle echo to build and the nagini sibling's echo analysis
carries over unchanged. The ``axioms`` region is empty: the two unchanged
lower-layer callees are free INPUTS (``m.hasLength`` and ``chunks``), A-references
validated against the real callees by axiom_check.py — that is G-AX's job.

``adjustMeta`` decomposes into THREE independent top-level clauses, one per
field of the returned record, and the battery attacks each separately:

  (a) LENGTH   ``hasLength := if isHead then false else m.hasLength``
                 — cleared for a bodyless request, else left exactly as found;
  (b) TERMINATE ``terminate := if (!isHead && !len) then true
                               else if !isThreadingServer then true
                               else m.terminate``
                 — note it reads the POST-CLEAR ``len``, not ``m.hasLength``, and
                   it PRESERVES the entry mark in the fall-through arm;
  (c) COMMIT   ``willTerminate := if term then true else m.willTerminate``
                 — a monotone mirror of (b) onto the entry commitment.

``bodyFor`` is a single clause with two arms: total suppression for a bodyless
request, order-preserving concatenation otherwise.

THE CARRIER IS FULLY TRANSPARENT AND BOTH FROZEN IMPLS ARE LOOP-FREE. That
second fact is what makes this bundle's reject lane unusually clean, and it is
worth stating because it is NOT the common case in this corpus. Where a frozen
``while`` loop's extracted program does not kernel-reduce — so a loop-free
rival's witness "fails on gold" by STALLING rather than by refutation, attesting
nothing on its own — here both frozen bodies are straight-line ``if`` ladders.
Every witness below was observed to fail on gold with

    error: Tactic `decide` proved that the proposition ... is false

i.e. a genuine SEMANTIC refutation: gold satisfies its postcondition at that
input, so the "spec is violated here" claim is decided FALSE. Non-reduction was
ruled out directly — ``prepareMetaTester``/``responseBodyTester`` were both
observed to ``decide`` to ``true`` on gold at concrete inputs, and each rival's
``<name>Exec`` was observed to land in ``DivM.res <concrete value>`` (so a
``Tester = false`` cannot be coming from the tester's ``| _ => false`` arm).
Both halves of every witness below were run with scripts/lean_verify.sh: rival
exit 0, gold exit 1.

BINDER COVERAGE (read before judging a pinned binder). ``prepareMeta`` has four
input binders — ``isHead``, ``isThreadingServer``, and the three fields of ``m``
— and the reject witnesses vary every one of them across their input points,
including ``m.terminate`` at BOTH values (``rival-prepatch-terminate`` probes
``m.terminate = true``, where clause (b)'s fall-through arm must PRESERVE the
mark; every other witness probes ``false``). ``responseBody``'s two binders are
varied by arity as well as by value: a single-chunk body, and a two-chunk body
whose flattening is order-sensitive.

THE REFINEMENT ARGUMENTS ARE EMPIRICAL, NOT ASSERTED — and this is where the
port did most of its real work. Each reject case's ``refinement`` claim ("its
faithful real patch would NOT resolve") was CHECKED by building that patch
against the repo at ``base_commit`` and running the failing test plus all four
passing tests. The baseline was reproduced first (no patch => the failing test
fails; gold => everything passes). That exercise disqualified FOUR otherwise
attractive rivals, which are documented as omissions below rather than shipped:
a rival is only admissible here if its faithful patch was OBSERVED not to
resolve. Every ``refinement`` below cites the assertion that actually killed it.

ADVERSARIAL READ of the nagini classes on this carrier:
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. The sibling's
    value-level rivals re-express onto the clause decomposition above.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries this as its
    MANDATORY probe (a store into an input held at half permission, which needs
    full permission to write). Lean and Velvet are referentially transparent:
    both inputs are immutable values, this bundle declares NO ``mut`` binder over
    any parameter, and there is no heap and no aliasing — so there is no
    read-only input to overwrite. Not fabricated; the class genuinely collapses.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * ADMISSIBILITY — APPLIES, RE-AIMED (this entry previously read "folded into
    the soundness positives" and the lane carried no case; the independent audit
    corrected that and landed ``admiss-f2p-points-satisfiable``). Neither method
    has a ``require`` clause, so the sibling's "a normal input satisfies the
    precondition" probe has no counterpart — but that only kills the
    can-a-normal-input-get-IN half. The half that survives on a TOTAL carrier is
    the obligation being unsatisfiable, or satisfiable only degenerately, at
    exactly an F2P-shaped input; a soundness positive quantifies over all inputs
    and does not test it. See the accounting note at the foot of this file.
  * UNGROUNDED-ORACLE ECHO — N/A (both post-images are total ``def``s over the
    methods' own inputs; no answer key to echo).

AXIOM lane: EMPTY (``meta.json`` declares ``axioms: []``; the two A-references
are validated by axiom_check.py, which is G-AX's job). The gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16502"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside an impl region (between -- impl-start and
# -- impl-end) or inside a prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only these
# keeps markers.same_spec True and both prove_correct statements byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of prepareMeta: the three staged mutable locals and
# the nested if-ladder that resolves them.
_IMPL_META = """    let mut len := m.hasLength
    let mut term := m.terminate
    let mut willTerm := m.willTerminate
    if isHead then
      if len then
        len := false
      else
        len := len
    else
      len := len
    if (!isHead && !len) then
      term := true
    else
      if !isThreadingServer then
        term := true
      else
        term := term
    if term then
      willTerm := true
    else
      willTerm := willTerm
    return { hasLength := len, terminate := term, willTerminate := willTerm }"""

# The WHOLE executable body of responseBody: the two-arm branch on the bodyless
# flag.
_IMPL_BODY = """    let out ← if isHead then
        pure ([] : List Char)
      else
        pure chunks.flatten
    return out"""

# The two frozen proof bodies. Both are elided from the spec view, so retuning
# one is a proof reshape and not a spec change; only the two positive controls
# whose impl shape changes what the residual goal looks like touch these.
_PROOF_META = "prove_correct prepareMeta by\n  loom_solve <;> simp_all [adjustMeta]"
_PROOF_BODY = "prove_correct responseBody by\n  loom_solve <;> simp_all [bodyFor]"


# ---- rival builders. Each collapses one impl region to a straight-line closed
# ---- form, so the extracted program still reduces and the witness can decide.
def _meta_rival(len_e, term_e, will_e):
    """prepareMeta whose three result fields are the given closed forms."""
    return _swap(
        _BASE, _IMPL_META,
        f"    let len := {len_e}\n"
        f"    let term := {term_e}\n"
        f"    let willTerm := {will_e}\n"
        "    return { hasLength := len, terminate := term, willTerminate := willTerm }")


def _body_rival(expr):
    """responseBody returning the given closed form."""
    return _swap(_BASE, _IMPL_BODY,
                 f"    let out ← pure ({expr})\n    return out")


# The gold closed forms, so each rival below differs from correct in exactly one
# named clause and the diff is legible.
_GOLD_LEN = "if isHead then false else m.hasLength"
_GOLD_TERM = ("if (!isHead && !len) then true "
              "else if !isThreadingServer then true else m.terminate")
_GOLD_WILL = "if term then true else m.willTerminate"


# ---- witness preambles. Each spec is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `<name>Tester <args> = false` says the extracted program's result violates
# ---- the postcondition at that concrete input. Checked in a file whose
# ---- prove_correct blocks have been stripped, so no tactic script can mask the
# ---- verdict. Both frozen impls are loop-free, so the gold-side leg of every
# ---- witness below is a genuine `decide`-refutation, not a stall.
_PRE_META = ("extract_program_for prepareMeta\n"
             "prove_precondition_decidable_for prepareMeta\n"
             "prove_postcondition_decidable_for prepareMeta\n"
             "derive_tester_for prepareMeta\n\n")
_PRE_BODY = ("extract_program_for responseBody\n"
             "prove_precondition_decidable_for responseBody\n"
             "prove_postcondition_decidable_for responseBody\n"
             "derive_tester_for responseBody\n\n")


def _w_meta(is_head, threading, has_len, term, will_term):
    b = lambda x: str(x).lower()  # noqa: E731
    return _PRE_META + (
        f"example : prepareMetaTester {b(is_head)} {b(threading)} "
        f"{{ hasLength := {b(has_len)}, terminate := {b(term)}, "
        f"willTerminate := {b(will_term)} }} = false := by\n  decide\n")


def _w_body(is_head, chunks):
    return _PRE_BODY + (
        f"example : responseBodyTester {str(is_head).lower()} {chunks} "
        "= false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # over-fit to the frozen impl's SHAPE => SPEC-TOO-STRONG. Each keeps its
    # byte-identical `ensures` obligation; two retune only the tactic body,
    # which the spec view elides.
    # =====================================================================
    {
        "id": "pos-meta-boolean-form",
        "kind": "soundness",
        "expect": "verify",
        # Same decision, different ALGEBRA: the nested if-ladder becomes a flat
        # boolean disjunction, and the commitment mirror becomes an `||`. The
        # residual goal is then an or-associativity identity, so the frozen
        # tactic needs `Bool.or_assoc` added — a proof retune inside the elided
        # tactic body, with the obligation statement untouched.
        "module": _swap(
            _meta_rival(
                _GOLD_LEN,
                "(!isHead && !len) || !isThreadingServer || m.terminate",
                "term || m.willTerminate"),
            _PROOF_META,
            "prove_correct prepareMeta by\n"
            "  loom_solve <;> simp_all [adjustMeta, Bool.or_assoc]"),
        "rationale": "soundness on `out = adjustMeta isHead isThreadingServer m`: "
                     "the three-way if-ladder is re-expressed as a flat boolean "
                     "disjunction and the commitment as `term || m.willTerminate`, "
                     "which is the same function of the four input binders on the "
                     "whole 2^4 cube (the fall-through arm `m.terminate` becomes "
                     "the final disjunct, and the monotone mirror becomes `||`). It "
                     "MUST verify; if a faithful re-algebraisation cannot, the "
                     "clause is over-fit to the if-ladder FORM => SPEC-TOO-STRONG. "
                     "A bare `loom_solve <;> simp_all [adjustMeta]` was observed to "
                     "leave an or-associativity goal OPEN, so the retune is "
                     "load-bearing and this control is not decorative.",
    },
    {
        "id": "pos-meta-reorder-guards",
        "kind": "soundness",
        "expect": "verify",
        # Evaluate the multiplexing guard FIRST and the bodyless-unknown-length
        # guard second — the opposite order to the frozen ladder, same result
        # set (the two guards' true-arms agree, so the order is immaterial).
        # Keeps the frozen mutable-local shape and the frozen proof verbatim.
        "module": _swap(
            _BASE, _IMPL_META,
            """    let mut len := m.hasLength
    let mut term := m.terminate
    let mut willTerm := m.willTerminate
    if isHead then
      if len then
        len := false
      else
        len := len
    else
      len := len
    if !isThreadingServer then
      term := true
    else
      if (!isHead && !len) then
        term := true
      else
        term := term
    if term then
      willTerm := true
    else
      willTerm := willTerm
    return { hasLength := len, terminate := term, willTerminate := willTerm }"""),
        "rationale": "soundness, branch-reorder (ports the sibling's guard-reorder "
                     "control): the multiplexing guard is tested BEFORE the "
                     "bodyless-unknown-length guard, the opposite order to the "
                     "frozen ladder. Both guards' true-arms set the same value, so "
                     "the reorder is semantically transparent on every input. It "
                     "MUST verify, else clause (b) is over-fit to the frozen guard "
                     "ORDER => SPEC-TOO-STRONG. The frozen proof body is kept "
                     "verbatim, so this control also shows the obligation does not "
                     "depend on the tactic being tuned to one branch order.",
    },
    {
        "id": "pos-body-foldr",
        "kind": "soundness",
        "expect": "verify",
        # Build the emitted sequence by an explicit right fold instead of naming
        # the library concatenation, and test the negated flag first. Equality to
        # the post-image is then a THEOREM (an induction over the chunk list),
        # not reflexivity — which is what makes this control load-bearing.
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  """    let out ← if !isHead then
        pure (chunks.foldr (fun c acc => c ++ acc) ([] : List Char))
      else
        pure ([] : List Char)
    return out"""),
            _PROOF_BODY,
            "prove_correct responseBody by\n"
            "  loom_solve <;> simp_all [bodyFor] <;> induction chunks <;> simp_all"),
        "rationale": "soundness on `out = bodyFor isHead chunks`: the emitted "
                     "sequence is built by an explicit right fold rather than by "
                     "naming the library concatenation, and the branch is inverted "
                     "(negated flag first). Extensionally identical on every input. "
                     "Load-bearing rather than decorative: a bare `loom_solve <;> "
                     "simp_all [bodyFor]` was observed to leave "
                     "`List.foldr (fun c acc => c ++ acc) [] chunks = chunks.flatten` "
                     "OPEN, so equality to the post-image is a real induction, not "
                     "reflexivity. It MUST verify, else the clause is over-fit to "
                     "the frozen impl's choice of concatenation SPELLING => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — landed by the independent audit; the port had recorded
    # this lane as VACUOUS on the ground that neither method carries a
    # `require`, which is NOT a sufficient reason (see the accounting note
    # below). "No precondition" removes the classic can-a-normal-input-get-IN
    # probe, but the analogue on a TOTAL carrier is the obligation being
    # unsatisfiable — or degenerate — at exactly an F2P-shaped input, and that
    # is what this case tests directly.
    #
    # Both `prove_correct` bodies get four `have`s that discharge, BY
    # EVALUATION at the two concrete input points the failing scenario
    # actually drives, that each post-image is INHABITED there, pins its value,
    # and DIFFERS from the answers a degenerate rule would give. The frozen
    # obligations are then closed VERBATIM by the frozen tactics, so both
    # `method` headers and both `ensures` lines stay byte-identical and only
    # the elided tactic bodies change.
    #
    # The two input points are the F2P-shaped ones, not arbitrary: the
    # scenario drives one bodyless and one body-bearing request against the
    # SAME single-chunk application over a MULTIPLEXING server, i.e.
    # `isThreadingServer = true` on both legs, entering at
    # `(hasLength=true, terminate=false, willTerminate=false)`.
    #
    # THE `have`s ARE LIVE, NOT DECORATION — measured with four real builds,
    # one per `have`. Substituting a claim that is FALSE at the SAME point
    # (pinning the bodyless meta answer to the entry record; pinning the
    # body-bearing meta answer to the cleared record; pinning the bodyless body
    # to the chunk contents; pinning the body-bearing body to empty) makes the
    # file FAIL to elaborate — exit 1 in all four — while the case as written
    # elaborates at exit 0. So a false claim about these points leaves an
    # unsolved goal rather than passing quietly.
    #
    # If a post-image were unsatisfiable or degenerate at an F2P-shaped input
    # => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-f2p-points-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _PROOF_META,
                "prove_correct prepareMeta by\n"
                "  have admissBodylessF2P :\n"
                "      ∃ out : ResponseMeta,\n"
                "        out = adjustMeta true true\n"
                "                { hasLength := true, terminate := false, willTerminate := false }\n"
                "          ∧ out = { hasLength := false, terminate := false, willTerminate := false }\n"
                "          ∧ out ≠ { hasLength := true, terminate := false, willTerminate := false }\n"
                "          ∧ out ≠ { hasLength := false, terminate := true, willTerminate := true } :=\n"
                "    ⟨adjustMeta true true\n"
                "        { hasLength := true, terminate := false, willTerminate := false },\n"
                "     rfl, by decide, by decide, by decide⟩\n"
                "  have admissBodyBearingF2P :\n"
                "      ∃ out : ResponseMeta,\n"
                "        out = adjustMeta false true\n"
                "                { hasLength := true, terminate := false, willTerminate := false }\n"
                "          ∧ out = { hasLength := true, terminate := false, willTerminate := false }\n"
                "          ∧ out ≠ { hasLength := false, terminate := true, willTerminate := true }\n"
                "          ∧ out ≠ { hasLength := false, terminate := false, willTerminate := false } :=\n"
                "    ⟨adjustMeta false true\n"
                "        { hasLength := true, terminate := false, willTerminate := false },\n"
                "     rfl, by decide, by decide, by decide⟩\n"
                "  loom_solve <;> simp_all [adjustMeta]"),
            _PROOF_BODY,
            "prove_correct responseBody by\n"
            "  have admissBodylessF2P :\n"
            "      ∃ out : List Char,\n"
            "        out = bodyFor true [['h', 'i']]\n"
            "          ∧ out = ([] : List Char) ∧ out ≠ ['h', 'i'] :=\n"
            "    ⟨bodyFor true [['h', 'i']], rfl, by decide, by decide⟩\n"
            "  have admissBodyBearingF2P :\n"
            "      ∃ out : List Char,\n"
            "        out = bodyFor false [['h', 'i']]\n"
            "          ∧ out = ['h', 'i'] ∧ out ≠ ([] : List Char) :=\n"
            "    ⟨bodyFor false [['h', 'i']], rfl, by decide, by decide⟩\n"
            "  loom_solve <;> simp_all [bodyFor]"),
        "rationale": "ADMISSIBILITY on a total carrier, aimed at the direction "
                     "an empty pre-conditions region does NOT make vacuous. "
                     "Neither method declares a `require`, so nothing can "
                     "EXCLUDE a normal input and the sibling's "
                     "does-the-precondition-admit-an-F2P-input probe has no "
                     "precondition to interrogate; the residual risk this case "
                     "closes is the other direction — that an obligation is "
                     "UNSATISFIABLE, or satisfiable only DEGENERATELY, at "
                     "exactly the inputs the failing scenario drives. Four "
                     "`have`s discharge by evaluation, at the two F2P-shaped "
                     "points (a bodyless and a body-bearing request against the "
                     "same single-chunk application over a multiplexing server, "
                     "entering at `hasLength=true, terminate=false, "
                     "willTerminate=false`), that each post-image is INHABITED "
                     "there, that its value is exactly the one demanded, and "
                     "that it DIFFERS from the answers a degenerate rule would "
                     "give (the entry record unchanged; the always-terminate "
                     "record; and for the body, the opposite arm's answer). So "
                     "the obligations are non-degenerately satisfiable where it "
                     "matters, not merely satisfiable somewhere. The frozen "
                     "obligations are then closed VERBATIM by the frozen "
                     "tactics, so both `method` headers and both `ensures` "
                     "lines are byte-identical and only the elided tactic "
                     "bodies differ. Measured live, four builds: substituting a "
                     "FALSE claim at the SAME point for any one of the four "
                     "`have`s fails to elaborate (exit 1 each) while the case "
                     "as written is exit 0, so these `have`s carry information "
                     "rather than decorating a positive that would pass anyway. "
                     "Must verify, else PRECOND-TOO-STRONG / "
                     "SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line closed form carrying a
    # machine-checked refutation witness at a concrete input, and each with a
    # refinement argument that was CHECKED by building the faithful patch and
    # running the test suite (never merely asserted).
    # =====================================================================

    # ---- clause (a) LENGTH + clause (b), together: the pre-image behaviour ----
    {
        "id": "rival-prepatch-terminate",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image resolution: never clear the length declaration, and drive
        # the terminate mark from the length alone with no bodyless guard.
        "module": _meta_rival(
            "m.hasLength",
            "if !len then true else if !isThreadingServer then true else m.terminate",
            _GOLD_WILL),
        "refinement": "this is the pre-image resolution: no bodyless clearing of "
                      "the length declaration, and the terminate mark driven by "
                      "the length alone. CHECKED by building that faithful patch "
                      "at base_commit and running the suite: the failing test "
                      "FAILS at `self.assertIs(any([line.startswith(b'Content-"
                      "Length:') for line in lines]), False)` with `AssertionError: "
                      "True is not False` — the bodyless response still carries the "
                      "length declaration the lower layer injected. (The 4 "
                      "otherwise-passing tests still pass, so the failing test is "
                      "what discriminates.) So it would NOT resolve.",
        "rationale": "REJECT from clause (a) `hasLength := if isHead then false "
                     "else m.hasLength` (and clause (b), which reads the post-clear "
                     "length): for a bodyless request the rival leaves the "
                     "declaration as found. Refuted at `isHead=true, "
                     "isThreadingServer=true, m=(hasLength=true, terminate=TRUE, "
                     "willTerminate=false)`. This witness is the one that probes "
                     "`m.terminate = true` — the value at which clause (b)'s "
                     "fall-through arm must PRESERVE the entry mark — so the binder "
                     "is exercised at both values across the battery. If it "
                     "verified => SPEC-TOO-WEAK (admits the pre-image behaviour).",
        "witness": _w_meta(True, True, True, True, False),
    },

    # ---- clause (a) alone: correct terminate rule, no clearing ----
    {
        "id": "rival-no-length-clear",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the CORRECT bodyless-gated terminate rule, but never clear the
        # length declaration. Isolated to clause (a): the terminate expression
        # reads `m.hasLength` (the entry value) instead of the post-clear `len`,
        # which for a bodyless request is the same decision, so only (a) breaks.
        "module": _meta_rival(
            "m.hasLength",
            _GOLD_TERM.replace("!len", "!m.hasLength"),
            _GOLD_WILL),
        "refinement": "keeps the correct bodyless-gated terminate rule but omits "
                      "the length-declaration clearing entirely. CHECKED by "
                      "building that faithful patch (gold's close guard kept, the "
                      "clearing hunk deleted) and running the suite: the failing "
                      "test FAILS at `self.assertIs(any([line.startswith("
                      "b'Content-Length:') for line in lines]), False)` with "
                      "`AssertionError: True is not False`. The lower layer "
                      "declares a zero length for a bodyless request, so without "
                      "the clearing the header survives onto the wire. So it would "
                      "NOT resolve.",
        "rationale": "REJECT from clause (a) ALONE — a strictly narrower defect "
                     "than rival-prepatch-terminate, which also breaks (b). The "
                     "terminate expression is rewritten to read the ENTRY length so "
                     "that clause (b) still holds, isolating the violation to the "
                     "length field. Refuted at `isHead=true, "
                     "isThreadingServer=FALSE, m=(hasLength=true, terminate=false, "
                     "willTerminate=false)` — a distinct input point from the "
                     "prepatch rival's (it varies `isThreadingServer`), as the "
                     "near-miss deserves: it agrees with gold wherever the entry "
                     "and post-clear lengths coincide. If it verified => "
                     "SPEC-TOO-WEAK (the bodyless clearing unenforced).",
        "witness": _w_meta(True, False, True, False, False),
    },

    # ---- clause (b): drop the bodyless guard on the unknown-length branch ----
    {
        "id": "rival-overterminate-bodyless",
        "kind": "uniqueness",
        "expect": "reject",
        # Clear the length correctly, but drop the `!isHead` guard on the
        # unknown-length terminate branch — so a bodyless request, whose length
        # was JUST cleared, is always marked terminate. The narrowest form of the
        # pre-image bug, isolated to clause (b).
        "module": _meta_rival(
            _GOLD_LEN,
            "if !len then true else if !isThreadingServer then true else m.terminate",
            _GOLD_WILL),
        "refinement": "drops the bodyless guard on the unknown-length terminate "
                      "branch, so a bodyless request is marked terminate merely for "
                      "lacking a length declaration (which the clearing step just "
                      "removed). CHECKED by building that faithful patch (the "
                      "clearing step kept, but the close guard left ungated by the "
                      "method) and running the suite: the failing test FAILS at its "
                      "`assertNotIn` for the connection-close header, which is "
                      "`unexpectedly found in` the bodyless response's header "
                      "block. So it would NOT resolve.",
        "rationale": "REJECT from clause (b) `terminate := if (!isHead && !len) "
                     "...`: the rival omits the `!isHead` conjunct, so for a "
                     "bodyless request — whose `len` clause (a) has just cleared — "
                     "it marks terminate where the post-image preserves "
                     "`m.terminate`. Refuted at `isHead=true, "
                     "isThreadingServer=true, m=(hasLength=FALSE, terminate=false, "
                     "willTerminate=TRUE)`: varies `m.hasLength` to false and "
                     "`m.willTerminate` to true, so this witness is the only one "
                     "probing an already-committed entry state. If it verified => "
                     "SPEC-TOO-WEAK (the discriminating bodyless cell unconstrained).",
        "witness": _w_meta(True, True, False, False, True),
    },

    # ---- clause (a), the OTHER direction: over-clearing ----
    {
        "id": "rival-clear-length-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Clear the length declaration UNCONDITIONALLY, not just for a bodyless
        # request. The mirror-image of rival-no-length-clear: it satisfies the
        # bodyless half of clause (a) and breaks the body-bearing half, which no
        # other rival attacks.
        "module": _meta_rival("false", _GOLD_TERM, _GOLD_WILL),
        "refinement": "clears the length declaration for EVERY method rather than "
                      "only a bodyless one. CHECKED by building that faithful patch "
                      "(the clearing hunk's method guard removed) and running the "
                      "suite: the failing test FAILS at `self.assertIn(f'Content-"
                      "Length: {content_length}\\r\\n'.encode(), lines)` with "
                      "`AssertionError: b'Content-Length: 52\\r\\n' not found in "
                      "[...]` — the body-bearing response loses the length "
                      "declaration it must keep. So it would NOT resolve.",
        "rationale": "REJECT from clause (a)'s BODY-BEARING half `hasLength := ... "
                     "else m.hasLength` — the else-arm that must leave the "
                     "declaration exactly as found. Every other length rival errs "
                     "by under-clearing; this one over-clears, so it is the only "
                     "case pinning the else-arm, and without it an impl that "
                     "cleared unconditionally would satisfy every other witness "
                     "here. Refuted at `isHead=FALSE, isThreadingServer=true, "
                     "m=(hasLength=true, terminate=false, willTerminate=false)` — "
                     "the only prepareMeta witness at `isHead=false`, so the "
                     "battery probes both values of that binder. If it verified => "
                     "SPEC-TOO-WEAK (the body-bearing frame unpinned).",
        "witness": _w_meta(False, True, True, False, False),
    },

    # ---- bodyFor, bodyless arm: the issue's symptom ----
    {
        "id": "rival-body-emitted-for-bodyless",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image emission: always emit the application's chunks, with no
        # bodyless suppression at all. This is the issue's reported symptom.
        "module": _body_rival("chunks.flatten"),
        "refinement": "this is the pre-image emission: the finishing step does not "
                      "distinguish a bodyless request, so the application's output "
                      "is always written. CHECKED by building that faithful patch "
                      "(the finishing override removed entirely) and running the "
                      "suite: the failing test FAILS at `self.assertEqual(body, "
                      "b'\\r\\n')` with `AssertionError: b'<!DOCTYPE html>...' != "
                      "b'\\r\\n'` — byte-identical to the no-patch baseline "
                      "failure, i.e. exactly the reported symptom. So it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = bodyFor isHead chunks`, bodyless arm "
                     "(`bodyFor true chunks = []`): the rival emits the "
                     "concatenation regardless of the flag. Refuted at "
                     "`isHead=true` with a single non-empty chunk. If it verified "
                     "=> SPEC-TOO-WEAK (admits the very behaviour the issue "
                     "reports).",
        "witness": _w_body(True, "[['h', 'i']]"),
    },

    # ---- bodyFor, body-bearing arm: truncation ----
    {
        "id": "rival-body-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Suppress correctly for a bodyless request, but emit all but the LAST
        # element for a body-bearing one. Attacks the body-bearing arm, which the
        # bodyless rivals leave entirely untested.
        "module": _body_rival(
            "if isHead then ([] : List Char) else chunks.flatten.dropLast"),
        "refinement": "suppresses correctly for a bodyless request but truncates "
                      "the body-bearing emission by its final element. CHECKED by "
                      "building that faithful patch and running the suite: the "
                      "failing test FAILS at `self.assertEqual(body, "
                      "hello_world_body)` with `AssertionError: b'<!DOCTYPE "
                      "html><html><body>Hello World</body></html' != b'<!DOCTYPE "
                      "html><html><body>Hello World</body></html>'` — and it "
                      "additionally breaks one of the four otherwise-passing tests "
                      "(`b'HTTP_SOME_HEADER:goo' != b'HTTP_SOME_HEADER:good'`), so "
                      "it is refuted twice over. So it would NOT resolve.",
        "rationale": "REJECT from `out = bodyFor isHead chunks`, BODY-BEARING arm "
                     "(`bodyFor false chunks = chunks.flatten`): the emitted "
                     "sequence is one element short. Refuted at `isHead=FALSE` with "
                     "a single non-empty chunk — the complementary flag value to "
                     "the bodyless rivals, so both arms of the clause are attacked. "
                     "If it verified => SPEC-TOO-WEAK (the body-bearing content "
                     "unpinned, e.g. an off-by-one in the emission).",
        "witness": _w_body(False, "[['h', 'i']]"),
    },

    # ---- bodyFor, body-bearing arm: total suppression ----
    {
        "id": "rival-suppress-body-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Suppress the body for EVERY method, not just a bodyless request — the
        # mirror-image of rival-body-emitted-for-bodyless. Its witness uses a
        # TWO-chunk body, so the arity of the chunk list is varied too.
        "module": _body_rival("([] : List Char)"),
        "refinement": "suppresses the body for every method rather than only a "
                      "bodyless one. CHECKED by building that faithful patch (the "
                      "bodyless path taken unconditionally) and running the suite: "
                      "the failing test FAILS at `self.assertEqual(body, "
                      "hello_world_body)` with `AssertionError: b'\\r\\n' != "
                      "b'<!DOCTYPE html>...'`, and it also breaks one of the four "
                      "otherwise-passing tests (`b'\\r\\n' != "
                      "b'HTTP_SOME_HEADER:good'`) — a body-bearing response would "
                      "carry no body at all. So it would NOT resolve.",
        "rationale": "REJECT from `out = bodyFor isHead chunks`, body-bearing arm — "
                     "the OVER-suppression direction, complementary to "
                     "rival-body-emitted-for-bodyless's under-suppression. Without "
                     "it the constant `[]` impl would be refuted by no witness "
                     "attacking suppression. Refuted at `isHead=false` with a TWO-"
                     "chunk body `[['a'], ['b']]`, which also varies the chunk "
                     "list's ARITY (every other responseBody witness uses one "
                     "chunk), so the traversal is probed past its first step. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _w_body(False, "[['a'], ['b']]"),
    },
]


# ===========================================================================
# Nagini -> velvet accounting.
# ===========================================================================
# The sibling battery has 12 SPEC cases (3 soundness positives, 1 admissibility,
# 4 value-level uniqueness rivals on its site A, 4 on its site B — one of which
# is the mandatory frame-mutation probe) plus an EMPTY axiom lane. This bundle
# models the SAME two functions over the same two decisions, so the port is
# unusually close to 1:1 by carrier. Four sibling cases are NOT ported, and they
# fail for three DIFFERENT reasons, which is worth separating: one (the
# admissibility probe) and one rival (the frame-mutation probe) are vacuous
# because the carrier has no `require` clause and no mutable frame; one
# (rival-body-head-emits-body) collapses onto an already-shipped rival because
# the carrier leaves no impl-shape distinction between the two; and exactly ONE
# (rival-headers-flag-not-mirrored) is withheld for a reason that has nothing to
# do with the carrier — its refinement argument does not survive contact with
# this instance's suite. That last one is the substance of this port.
#
#   sibling case                      -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-headers-local-bool            -> pos-meta-boolean-form        PORTED
#   pos-headers-reorder-guards        -> pos-meta-reorder-guards      PORTED
#   pos-body-hoist-len                -> pos-body-foldr               PORTED (reshaped)
#   admiss-gold-verbatim              -> admiss-f2p-points-satisfiable RE-AIMED (audit)
#   rival-headers-prepatch-terminate  -> rival-prepatch-terminate     PORTED
#   rival-headers-no-size-drop        -> rival-no-length-clear        PORTED
#   rival-headers-overterminate-head  -> rival-overterminate-bodyless PORTED
#   rival-headers-flag-not-mirrored   -> (none)                       DROPPED (resolves)
#   rival-body-nonempty-head          -> rival-body-emitted-for-bodyless PORTED
#   rival-body-head-emits-body        -> (merged)                     DROPPED (duplicate)
#   rival-body-drop-last              -> rival-body-drop-last         PORTED
#   rival-body-frame-mutation         -> (none)                       VACUOUS
#   (no sibling)                      -> rival-clear-length-always    ADDED
#   (no sibling)                      -> rival-suppress-body-always   ADDED
#   AXIOM_TESTS (0)                   -> (none)                       EMPTY both sides
#
# 9 ported (3 soundness + 1 admissibility + 5 uniqueness) + 2 added = 11 SPEC
# cases shipped (3 soundness, 1 admissibility, 7 uniqueness); on the sibling side
# 1 was vacuous (the frame probe) and 2 dropped, which accounts for all 12
# sibling cases. No omission is "it was hard to prove".
#
# Counts corrected by the independent audit: this note previously read "8 ported
# ... = 10 SPEC cases ... 2 were vacuous", counting the admissibility probe as
# the second vacuous case. It was not vacuous — see the RE-AIMED entry below.
#
# DROPPED — rival-headers-flag-not-mirrored (clause (c), the COMMITMENT mirror).
#   The sibling rival computes the length and terminate decisions correctly but
#   never mirrors the terminate mark onto the commitment flag, and its refinement
#   argues the persistent-connection behaviour would regress. On THIS instance
#   that argument does not survive contact with the suite. The faithful patch
#   (final mirror deleted) was built and run: the failing test PASSES and all
#   four otherwise-passing tests PASS. Instrumenting gold showed why — the
#   commitment flag is ALREADY set at entry to the modeled step for both methods
#   in this fixture (the request handler sets it before dispatch, and the
#   fixture's requests are HTTP/1.0, which is close-by-default), so the mirror
#   can only re-raise an already-raised flag and is unobservable. Two further
#   shapes were built and are equally green: making the mirror unconditional (so
#   it can LOWER an already-set flag — observed to do so, driving an extra
#   no-op request iteration that writes nothing) and overwriting the connection
#   header in the fall-through arm. Since clause (c)'s post-image
#   `willTerminate := if term then true else m.willTerminate` is monotone in an
#   input that is already true at every point the suite reaches, NO rival
#   confined to clause (c) has a faithful patch that fails to resolve. Shipping
#   one would be a reject case whose `refinement` claim is false — precisely the
#   corrupt artifact this gate exists to avoid — so clause (c) is left ATTACKED
#   ONLY INDIRECTLY (the three prepareMeta rivals that break clause (a) or (b)
#   also propagate into (c) through `term`) and this is recorded as a KNOWN GAP:
#   the modeled surface is strictly wider than the failing test observes, and
#   verify-implies-resolve is not at risk in that sub-domain because a rival
#   confined to it resolves.
#   AUDIT NOTE (independent re-derivation, machine-checked). The withheld rival
#   was BUILT and its witness run both ways, because "we chose not to ship it"
#   and "it could not be shipped" are different claims and only the first is true
#   here. Rival = clause (c) replaced by `willTerm := m.willTerminate` (the mirror
#   deleted); witness `prepareMetaTester false false { hasLength := true,
#   terminate := false, willTerminate := false } = false`. Observed: rival exit 0,
#   frozen solution exit 1 with `Tactic `decide` proved that the proposition ...
#   is false` — a genuine semantic refutation. So clause (c) IS directly
#   attackable on this carrier and the omission is NOT an expressiveness or
#   tooling limit; it rests solely on the refinement argument above (a rival
#   confined to (c) RESOLVES, so shipping it would assert a false `refinement`).
#   Recorded because a reader can otherwise not tell those two cases apart.
# DROPPED — rival-body-head-emits-body. The sibling distinguishes "no bodyless
#   branch at all" from "a bodyless branch that copies anyway", but both are the
#   SAME closed form on this carrier (`chunks.flatten` irrespective of the flag):
#   there is no impl-shape distinction left once the loop is a library
#   concatenation, so it would be a second case with an identical module and an
#   identical witness. Merged into rival-body-emitted-for-bodyless rather than
#   shipped as a duplicate that would inflate the case count without probing a
#   new input point.
# VACUOUS — rival-body-frame-mutation. The sibling's MANDATORY frame probe writes
#   into an input held at half permission. There is no heap, no aliasing, no
#   `mut` binder on any parameter here, and both inputs are immutable values, so
#   there is no read-only frame to violate. Per the porting map, no substitute is
#   fabricated.
# RE-AIMED (was recorded VACUOUS; CORRECTED by the independent audit) —
#   admiss-gold-verbatim -> admiss-f2p-points-satisfiable. The sibling verifies
#   its unmodified model to show the preconditions are satisfiable. The port
#   dropped the lane entirely, reasoning that both methods here declare NO
#   `require` clause and both post-images are TOTAL, so "every obligation is
#   satisfiable at every input by construction" and "the soundness positives
#   already witness it". That reason is NOT sufficient, and the coverage
#   reporter flags it independently: an empty pre-conditions region removes only
#   the can-a-normal-input-get-IN half of the lane. The half that survives on a
#   total carrier is the obligation being unsatisfiable — or satisfiable only
#   DEGENERATELY — at exactly an F2P-shaped input, and no soundness positive
#   tests it: a positive quantifies over ALL inputs and would pass just as
#   happily if the demanded answer at the F2P points were the degenerate one.
#   Dropping the lane therefore removed one of the three directions this gate
#   exists to test (PRECOND-TOO-STRONG), which is why the audit LANDED a case
#   rather than agreeing with the omission. admiss-f2p-points-satisfiable
#   discharges the post-images by evaluation at the two points the failing
#   scenario drives; its four `have`s were each shown live to be load-bearing
#   (a false claim at the same point => exit 1). Nothing about this carrier made
#   the lane inexpressible.
# ADDED — rival-clear-length-always and rival-suppress-body-always. Both attack a
#   clause ARM the sibling never attacks: the sibling's rivals all err by doing
#   too little (not clearing, not suppressing), so an impl that cleared or
#   suppressed UNCONDITIONALLY would satisfy every ported witness. These pin the
#   preserve-as-found else-arm of clause (a) and the body-bearing arm of
#   `bodyFor`. Both were confirmed to have faithful patches that do NOT resolve
#   (assertions quoted in their `refinement`).
# NOT PORTED, and NOT a hole -- the DIVERGENCE lane. The sibling carries no
#   `diverge-*` case, so there is nothing to port, and the reason it is not ported
#   is not a weakness of the spec. An earlier revision of this note said this
#   bundle sets `loom.semantics.termination "partial"`, under which a
#   non-terminating impl satisfies both `ensures` clauses vacuously and VERIFIES,
#   and recorded that as a KNOWN SPEC HOLE. Both halves are withdrawn: line 4 of
#   the frozen file sets `"total"` and line 7 opens `TotalCorrectness`, as in all
#   500 velvet bundles, and under `total` a postcondition is claimed of ALL runs so
#   the verifier demands a decreasing measure on every loop and discharges its
#   descent. See the DIVERGENCE bullet in the module docstring for the builds: a
#   spliced loop carrying a measure its body never changes is REJECTED on the
#   measure's own goal (`case «decreasing_1: q»`, residual `q < q`), and one
#   carrying no measure is refused earlier by the elaborator. No reject case is
#   shipped, for a witness-contract reason rather than a spec one: the rejection
#   fires at the `method`, so the rival's module never compiles and the witness the
#   gate derives from it cannot elaborate.
# ALSO CONSIDERED AND DROPPED (no sibling; would have been an addition) — a rival
#   emitting the chunks in REVERSED order, attacking the order-preservation half
#   of `bodyFor false chunks = chunks.flatten`. It is genuinely wrong on this
#   carrier and its witness discriminates cleanly at `[['a'], ['b']]` (rival exit
#   0, gold refuted by `decide`). It is dropped because its REFINEMENT argument is
#   false: the faithful patch was built and the whole suite PASSES (5/5), since
#   every fixture in the relevant test file returns a single-chunk body and
#   reversing a one-element list is a no-op. A separate harness over a real
#   patched handler with a three-chunk app confirmed the corruption is observable
#   in principle (`b'AAABBBCCC'` under gold vs `b'CCCBBBAAA'` under the rival) —
#   so this is a coverage gap in the failing test, not a semantics-preserving
#   mutant. Recording it here rather than shipping it: as an `expect="reject"`
#   case it would assert a `refinement` that a real run contradicts.

# ===========================================================================
# INDEPENDENT AUDIT RECORD (adversarial re-derivation; machine-checked).
# ===========================================================================
# Every claim below is an observed exit code, not an argument.
#
# STATEMENT INTEGRITY. All case modules were diffed against the frozen file:
#   every difference lies inside an `-- impl-start`/`-- impl-end` region or a
#   `prove_correct` tactic body. Both `method` headers and both `ensures` lines
#   are byte-identical in every case. No case weakens or restates an obligation.
#
# WITNESS DISCRIMINATION, RE-DERIVED (all 7 reject cases, rebuilt from scratch):
#   rival exit 0 and frozen-solution exit 1 for all 7, and every gold-side
#   failure was `Tactic `decide` proved that the proposition ... is false` —
#   a SEMANTIC refutation, not a missing identifier, type error, or stall.
#   No witness binds anything, so no consistency probe is owed.
#
# NOT-DEFINITIONALLY-EQUAL (the vacuity trap this carrier invites). For each of
#   the 7 rivals, `<name>Exec` was pinned by `rfl` to a CONCRETE value at the
#   witness input, and the frozen impl was pinned at the SAME input to a
#   DIFFERENT concrete value — 14 builds, all exit 0. So each rival is observably
#   wrong there, and no rival's `Tester = false` can be coming from the tester's
#   `| _ => false` non-reduction arm. No case is vacuous.
#
# POSITIVE CONTROLS ARE LOAD-BEARING (the two `rationale`s that claim it were
#   verified, not taken on trust). Reverting each retune to the frozen tactic
#   leaves exactly the goal the comment names OPEN (both exit 1):
#     pos-meta-boolean-form -> an or-associativity goal;
#     pos-body-foldr        -> `List.foldr (fun c acc => c ++ acc) [] chunks
#                               = chunks.flatten`.
#   Neither positive is decorative.
#
# ATTACK D — 9 NEW wrong impls the battery does not contain, aimed at the arms
#   the shipped rivals leave unattacked. ALL 9 were REJECTED (exit 1): commitment
#   mirror deleted; mirror clobbered to `term`; terminate fall-through clobbered
#   to `false`; multiplexing-guard polarity flipped; body emitted in REVERSED
#   order; a one-cell near-miss wrong only at (isHead=F, threading=T,
#   hasLength=T, terminate=T); body truncated to its FIRST chunk (agrees with
#   gold on every 0/1-chunk input); commitment driven by `len` instead of `term`;
#   length-clearing polarity inverted. No spec hole found.
#
# ATTACK E — 4 NEW correct reshapes, all provable, so the spec is not over-fit:
#   `!isHead && m.hasLength` for the length clause (exit 0 under the frozen
#   tactic); `chunks.flatMap id` (exit 0 with `List.flatMap_id`); the terminate
#   ladder split on `isHead` first (exit 0 once the proof does `cases isHead`);
#   a left fold with an accumulator (exit 0 once the proof supplies the
#   `foldl … acc = acc ++ cs.flatten` step). The last two do NOT verify under the
#   frozen tactic — but the residual goals are true identities that a retune
#   closes, i.e. a proof-tactic gap, NOT a spec rejection. No soundness hole.
#
# The DIVERGENCE lane is no hole at all: under this bundle's `total` semantics the
#   verifier rejects a diverging rival, including one that supplies a constant
#   measure (rejected on the descent goal itself). See the docstring bullet.

# ===========================================================================
# SECOND, INDEPENDENT AUDIT (a different auditor; every line below is an exit
# code this auditor observed, not a re-reading of the record above).
# ===========================================================================
# ONE DEFECT FOUND AND FIXED: the missing admissibility lane. Detail under
# RE-AIMED above; the coverage reporter flags it independently. Everything else
# examined here re-derived clean, and the record above re-derived as TRUE.
#
# WITNESS DISCRIMINATION (attack B) — all 7 reject witnesses rebuilt from the
#   manifest via the gate's own `witness_file`, 14 builds: rival exit 0, frozen
#   solution exit 1, for all 7. Every gold-side first error is
#   `Tactic `decide` proved that the proposition <the tester at the concrete
#   input> = false is false` — a plain EVALUATION refutation, the strongest
#   signature available, and none of the stuck-reduction classes the gate
#   screens for (no `did not reduce to isTrue or isFalse`, no
#   `Dependent elimination failed`, no missing `Decidable`, no
#   `Application type mismatch`/`forIn Lean.Loop.mk`). Both frozen bodies are
#   straight-line `if` ladders, so nothing here can stall.
#
# THE FORGERY TEST (attack B′) — run on all 7 even though a plain evaluation
#   signature does not strictly require it, because it is the only check that
#   proves gold's exit code tracks the CLAIM. Each witness was rebuilt with its
#   claim FLIPPED (`= false` -> `= true`, i.e. asserting gold is CORRECT at that
#   input) and built against BOTH subjects. Result, 14 builds, perfectly
#   INVERTED: flipped-on-gold exit 0 with an EMPTY log (the flipped claim is
#   simply true of gold, so it elaborates), flipped-on-rival exit 1. So gold's
#   exit code carries full information about the claim: the truthful claim fails
#   on gold and holds on the rival, the flipped claim holds on gold and fails on
#   the rival. No case is hollow.
#
# ATTACK D, INDEPENDENTLY (12 NEW wrong impls, not the 9 above — including 3
#   arms those leave alone): all REJECTED (exit 1). commitment mirror deleted;
#   mirror clobbered to `term`; terminate fall-through clobbered to `false`;
#   multiplexing-guard polarity flipped; length-clearing polarity inverted;
#   length forced TRUE on the body-bearing arm; commitment forced `true`;
#   commitment driven by `len`; a one-cell near-miss (fall-through arm
#   `m.terminate && !m.willTerminate`); body reversed; body truncated to its
#   FIRST chunk. No impl verified => no SPEC-TOO-WEAK hole found.
#   One probe was WITHDRAWN as not actually wrong: suppressing the body only for
#   a bodyless request with a NON-EMPTY chunk list
#   (`if isHead && !chunks.isEmpty then [] else chunks.flatten`) is
#   EXTENSIONALLY EQUAL to the post-image — when the list is empty its flatten
#   is already `[]` — so it is a correct reshape, and it duly VERIFIES (exit 0)
#   once the proof does `cases chunks`. Recorded because mistaking it for a
#   surviving mutant would have been a false spec hole.
#
# ATTACK E, INDEPENDENTLY (5 NEW correct reshapes): all provable, so the spec is
#   not over-fit. `!isHead && m.hasLength` for the length clause, `term ||
#   m.willTerminate` for the commitment, and `chunks.flatMap id` with
#   `List.flatMap_id` all verify under a same-or-lightly-retuned tactic (exit 0).
#   Two need a real retune and GET one: the terminate ladder reading the ENTRY
#   length (`!m.hasLength` in place of `!len` — sound because for a bodyless
#   request the guard is already false) and the ladder split on `isHead` first
#   both leave a residual that is a TRUE boolean identity, and both verify at
#   exit 0 after `cases isHead <;> cases isThreadingServer <;> cases m <;>
#   simp_all`. Proof-tactic gaps, NOT spec rejections. No SPEC-TOO-STRONG hole.
#
# POSITIVE CONTROLS RE-CHECKED (the two load-bearing claims, rebuilt): reverting
#   pos-meta-boolean-form's retune to the frozen tactic leaves an
#   or-associativity goal open, and reverting pos-body-foldr's leaves exactly
#   `List.foldr (fun c acc => c ++ acc) [] chunks = chunks.flatten` open — both
#   exit 1, both residuals matching what the `rationale`s name, word for word.
#   Neither positive is decorative, as claimed.
#
# THE CLAUSE-(c) OMISSION, RE-DERIVED INDEPENDENTLY. The port's own AUDIT NOTE
#   says the withheld mirror-deleted rival IS attackable here and is withheld
#   only because a rival confined to (c) RESOLVES, making its `refinement` false.
#   Re-derived rather than trusted: rival = `willTerm := m.willTerminate`,
#   witness `prepareMetaTester false false { hasLength := true, terminate :=
#   false, willTerminate := false } = false`. Observed rival exit 0, gold exit 1
#   with the plain `decide` refutation. So the note is accurate in BOTH
#   directions — expressible, and correctly withheld on refinement grounds, not
#   on a carrier or tooling excuse. Clause (c) remains attacked only indirectly;
#   that is a KNOWN GAP honestly recorded, not a hollow case.
#
# REFINEMENT PROSE SPOT-CHECKED against the real failing test. Every assertion
#   quoted in a `refinement` appears in the scenario with the quoted text and in
#   the quoted direction, and the two legs the scenario drives (bodyless and
#   body-bearing, same single-chunk application, multiplexing server) are the
#   points the new admissibility case pins. No `refinement` cites an assertion
#   the scenario does not contain.
AXIOM_TESTS = []
