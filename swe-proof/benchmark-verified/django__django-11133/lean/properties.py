"""properties.py — G-PBT falsification battery for django__django-11133 (lean).

NOT a Lean module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte — region surgery touches only text inside ``-- impl-start`` /
``-- impl-end`` or inside ``-- proof-start`` / ``-- proof-end``, both of which
the consumer spec view elides, so ``markers.same_spec`` holds by construction —
and the ``theorem correct_toBytestring`` STATEMENT is carried over verbatim in
every case (only tactic bodies differ). ``expect:"verify"`` passes iff (in scope
AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND
its refutation ``witness`` discriminates).

DEFENDED SURFACE (one obligation, over two inputs).

  problem_spec_toBytestring (charset : List Char) (value : PyValue)
                            (result : List UInt8) : Prop

  theorem correct_toBytestring : ∀ (charset : List Char) (value : PyValue),
      problem_spec_toBytestring charset value
        (implementation_toBytestring charset value)

The routine turns an input value into its output byte sequence, DISPATCHING on
the value's shape (``value : PyValue``, four disjoint constructors). The spec is
a four-arm ``match``, so it has FOUR independent top-level clauses — one per
constructor — and each is a bare equation pinning that arm's output:

  (C1) ``.bytesV b        => result = b``            byte sequence, verbatim
  (C2) ``.memoryviewV b _ => result = b``            a view over a byte
                                                     sequence: its UNDERLYING
                                                     bytes, verbatim — and NOT
                                                     the textual rendering the
                                                     constructor's second field
                                                     carries. The
                                                     discriminating clause.
  (C3) ``.strV s          => result = encode charset s``
  (C4) ``.otherV text     => result = encode charset text``

WHICH BINDER EACH CLAUSE READS. C1 and C2 read ``value``'s payload ONLY —
``charset`` is irrelevant on the two byte-sequence-like arms, which is itself
part of what the spec pins (nothing is re-encoded there). C3 and C4 read BOTH
``charset`` and the payload, through the unchanged encoding callee. C2 further
pins that the constructor's SECOND field (the textual rendering) is NOT what the
result may be: it appears in the pattern as ``_`` on the right of the equation,
so a result derived from it is refuted. Every rival below attacks exactly one of
these four clauses, and between them ``value`` is moved across all four shapes
while ``charset`` is moved off any fixed value.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's MANDATORY
    ``frame-mutate-data`` / ``frame-mutate-kind`` rivals write through a
    half-permission reference to a field of the read-only input and are rejected
    for INSUFFICIENT PERMISSION. Lean is referentially transparent: the inputs
    are immutable values, there is no heap, no aliasing, and no permission
    system to subvert, so there is no read-only input to overwrite. The class is
    vacuous here and NO substitute probe is fabricated. The frame obligation's
    Lean analogue — "an output component the spec leaves unconstrained is a hole
    a wrong impl can fill" — is not a hole in this spec: the postcondition is a
    total equation on every one of the four arms, so no component of the result
    is unpinned on any input. weak-view-valuemask is the probe that would find
    such a hole on the discriminating arm if one existed.

  * DIVERGENCE — GENUINELY VACUOUS on this backend (and the nagini sibling
    carries no ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case to port
    anyway). ``implementation_toBytestring`` is a total Lean ``def``, so a
    diverging implementation cannot be WRITTEN at all: the elaborator rejects
    non-termination rather than admitting it vacuously. This is NOT the velvet
    situation (the corpus-wide termination-semantics finding), where under
    ``loom.semantics.termination "partial"`` a non-terminating impl satisfies
    every ``ensures`` vacuously and verifies while its faithful real patch hangs
    the failing test — a known SPEC HOLE in 401 of 500 bundles. On lean the
    carrier forecloses the rival, so the class collapses for a reason that says
    the battery is complete rather than that the spec is weak.

  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the nagini sibling
    argues. The only callee the postcondition names is ``encode charset ·``, and
    it is GROUNDED in the inputs: a function of the same ``charset`` and the same
    character payload the impl passes. There is no opaque answer key / exact
    marker an impl could echo to satisfy C3 or C4 with a WRONG value — the only
    value satisfying them IS ``encode`` applied to those arguments, which the
    gold impl returns. So there is no wrong echo to build, and the honest
    cheapest-correct controls are carried as POSITIVES instead. What IS
    attackable about the opaque callee is which ARGUMENTS reach it and on which
    arms it is reached at all, and that is what weak-str-charset-pinned (wrong
    charset argument) and weak-bytes-render (the callee reached on an arm that
    must not encode anything) probe.

  * PARTIAL-DOMAIN / VALUE-MASK — the whole reject surface. A rival can be right
    on three arms and divert the fourth, or emit the RIGHT SHAPE with the WRONG
    VALUE on the discriminating arm.

WITNESS MECHANICS. The spec is a bare ``Prop``-valued predicate, so each witness
states ``¬ problem_spec_toBytestring <charset> <value> (implementation_toBytestring
<charset> <value>)`` at a concrete input, in a file whose ``proof`` region the
gate has emptied (so the frozen tactic script cannot mask the verdict).

Five of the six witnesses must CONDITION ON THE CARRIER rather than compute it:
``encode`` is ``opaque``, so no literal input decides an equation mentioning it
and ``decide`` would simply get stuck on the opaque term. Each such witness
therefore binds ONE hypothesis separating the two answers at that point — e.g.
``(h : encode ['l'] ['m'] ≠ [1, 2])`` — and concludes that the rival's output
differs from what the clause requires. That is a STRONGER claim than any literal
input could make: it says that wherever the callee's result differs from the
constant the rival substitutes, the rival is wrong. One hypothesis per witness,
about ONE opaque term, never two about the same term — so the assumptions are
jointly satisfiable and the gate's ``False``-from-the-binders consistency probe
cannot close (checked out-of-band for all five: the probe leaves
``h : ... ⊢ False`` unsolved).

weak-view-valuemask needs no hypothesis: its rival's error is visible in the
LIST STRUCTURE (a spurious leading byte), so the refutation is decidable at
literal ``UInt8`` values and closes with plain ``decide``.

Every witness was checked out-of-band with ``scripts/lean_verify.sh``: each
ELABORATES against its own rival (exit 0) and FAILS against the frozen solution
(exit 1, the hypothesis or ``decide`` no longer reaching ``False``). None uses
any of the banned tokens.

AUDIT — WHY THE GOLD-SIDE FAILURES ARE REFUTATIONS AND NOT SYNTACTIC ACCIDENTS.
Every conditioned witness fails on the frozen solution with a ``Type mismatch:
After simplification, term h has type ¬<the concrete equation> but is expected to
have type False``. That message is ABOUT the claim, but "it looks semantic" is not
evidence, so each was re-measured two ways against the frozen solution:

  * FLIP THE CLAIM. The same witness with the ``¬`` dropped — asserting the
    frozen impl is CORRECT at that point — ELABORATES (exit 0) against the frozen
    solution and FAILS (exit 1) against the rival: the exact mirror of the
    witness. So gold's exit code tracks what is claimed rather than being a
    constant, and a witness asserting gold is correct there would NOT have been
    recorded as a rejection.
  * REVEAL THE TYPE. Replacing the closing step with a deliberate type error
    (``exact True.intro``) prints the goal's real type on each side. Against the
    frozen solution: ``True.intro has type True but is expected to have type
    False`` — ``simp`` CLOSED the equation, i.e. gold satisfies the clause at
    that point. Against the rival: ``... but is expected to have type ¬encode
    ['l'] ['m'] = [1, 2]`` — the refutation is still live. The two differ, which
    is the genuine-refutation pair rather than a tactic mismatch.

weak-view-valuemask needs neither: its gold-side failure is a plain evaluation
(``decide`` PROVED the un-negated proposition false), and its flipped claim
elaborates against gold by ``decide`` as well.

AUDIT — THE ADMISSIBILITY CLAIMS ARE LIVE, measured three ways rather than
asserted once. Each ``have`` in admiss-nondegenerate was replaced in turn by a
FALSE claim about the SAME point: the non-degeneracy conjunct made to deny the
underlying bytes themselves, the byte-arm satisfiability claim pointed at a
different byte, and the string-arm universal given the encoder's two arguments
swapped. All three leave ``unsolved goals`` (exit 1), so none of the claims is
decoration that ``simp`` would discharge regardless of what it says.

AXIOM lane: DROPPED. ``AXIOM_TESTS = []``. The nagini sibling carries
axiom-soundness / axiom-containment probes over the real string-encoding callee;
that is G-AX's job (recorded here as a skip — this bundle consumes NO axiom, the
one callee being declared by signature and applied identically on both sides of
each clause, discharged by reflexivity) and the G-PBT gate ignores AXIOM_TESTS
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11133"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen executable dispatch, i.e. everything
# ---- strictly inside `-- impl-start` / `-- impl-end` below the leading comment.
# ---- The postcondition's own four-arm match uses `result = ...` on the right
# ---- (no `return`), so this `return`-bearing block is unique in the file — both
# ---- facts asserted at load time. Every impl variant replaces exactly this
# ---- text, so each edit lies wholly inside the one impl region.
_IMPL = """\
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return b
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# ---- proof-region anchor: the frozen TACTIC BODY only (everything after the
# ---- theorem's `:= by`). The `theorem correct_toBytestring` statement itself is
# ---- never touched, so the obligation survives byte-identically in every case.
_PROOF = """\
  intro charset value
  cases value <;>
    simp only [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the executable dispatch replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_impl, new_proof):
    """Full variant with the dispatch AND the tactic body replaced (a reshaped
    correct impl legitimately reproves the same obligation)."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _proof(new_proof):
    """Full variant with ONLY the tactic body replaced (impl kept verbatim)."""
    return _swap(_BASE, _PROOF, new_proof)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. A correct impl the spec rejects is SPEC-TOO-STRONG.
    # Each keeps the obligation statement byte-identical; where the reshape
    # moves the goal out of the frozen script's reach the tactic body is
    # honestly reproven (no new lemma, no assumption, no weakening).
    # =====================================================================
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: permute the dispatch arms so the two encoding arms are tested
        # first and the two verbatim-byte arms last. A match over disjoint
        # constructors is order-independent, so every arm's output is unchanged.
        "module": _impl("""\
  match value with
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text
  | .bytesV b        => return b
  | .memoryviewV b _ => return b"""),
        "rationale": (
            "permuting the dispatch arms over disjoint constructors leaves every "
            "arm's output unchanged, so all four clauses (C1..C4) still hold "
            "point-wise and the frozen tactic body closes as-is. Ports the "
            "nagini pos-helper-reorder (branch-reorder, behaviourally "
            "identical). If it fails => SPEC-TOO-STRONG, or the obligation is "
            "over-fit to the frozen arm ORDER rather than to the behaviour."
        ),
    },
    {
        "id": "pos-let-bound",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the answer into a local binding and return it once,
        # instead of returning from inside each arm — AND route the two encoding
        # arms through extensional identities on a byte sequence, so the reshape
        # is not merely a re-plumbing the elaborator erases.
        #
        # AUDIT NOTE. The single-exit `let` reshape ALONE was measured
        # DEFINITIONALLY EQUAL to the frozen dispatch: `example :
        # implementation_toBytestring = alt := rfl` ELABORATES (exit 0) when
        # `alt` is the plain `let`-bound four-arm match. The elaborator erases
        # `Id.run`'s bind, so "one exit point rather than four" is not a
        # different term at all and such a case verifies while testing nothing —
        # the frozen impl by another spelling. The encoding arms are therefore
        # routed through `.reverse.reverse` / `++ []`, which makes the term
        # genuinely distinct: the same `rfl` probe now FAILS (exit 1, `rfl has
        # type ?m = ?m but is expected to have type implementation_toBytestring
        # = alt`), the FROZEN tactic body no longer closes the obligation (exit
        # 1, `unsolved goals`), and the case verifies only under the reproven
        # body below (exit 0).
        "module": _impl_proof("""\
  let out : List UInt8 :=
    match value with
    | .bytesV b        => b
    | .memoryviewV b _ => b
    | .strV s          => (encode charset s).reverse.reverse
    | .otherV text     => (encode charset text) ++ []
  return out""", """\
  intro charset value
  cases value <;>
    simp [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]"""),
        "rationale": (
            "single-exit reshape with the encoding arms routed through "
            "extensional identities: the four-arm dispatch is bound to a local "
            "and returned once, and the two ENCODING arms are wrapped in "
            "operations that are the identity on a byte sequence, so the value "
            "on every input is identical and all four clauses hold. This is the "
            "complement of pos-extensional, which perturbs the two "
            "VERBATIM-BYTE arms instead; between them every one of the four "
            "arms is returned through a syntactically different term at least "
            "once. Measured NOT definitionally equal to the frozen impl and NOT "
            "closable by the frozen tactic body, so the reproven body is doing "
            "real work rather than restating the frozen proof. If it fails => "
            "SPEC-TOO-STRONG (the clause would demand a particular way of "
            "naming the encoded bytes rather than the bytes themselves)."
        ),
    },
    {
        "id": "pos-extensional",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the two verbatim-byte arms through operations that are
        # EXTENSIONALLY the identity on a byte sequence (reverse twice; append
        # the empty sequence). Behaviourally identical, but no longer closed by
        # `simp only` on the frozen lemma set, so the tactic body is honestly
        # reproven with full `simp` — same obligation, same statement, no new
        # lemma and nothing assumed.
        "module": _impl_proof("""\
  match value with
  | .bytesV b        => return b.reverse.reverse
  | .memoryviewV b _ => return b ++ []
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text""", """\
  intro charset value
  cases value <;>
    simp [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]"""),
        "rationale": (
            "the two verbatim-byte arms are routed through extensional "
            "identities on a byte sequence, so C1 and C2 still hold exactly "
            "(`b.reverse.reverse = b`, `b ++ [] = b`) while the syntactic form "
            "of the returned term changes. This is the case that separates 'the "
            "spec pins the VALUE' from 'the frozen script pins the SYNTAX': it "
            "must verify under a reproven body. If it fails => SPEC-TOO-STRONG "
            "(the clause would demand a particular way of naming the bytes "
            "rather than the bytes themselves)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-shape. That case
    # established that a normal F2P/P2P-shaped input satisfies the read-only
    # precondition (the half-permission domain facts) and that the four
    # representation tags dispatch as specified. This obligation has NO
    # precondition at all — `correct_toBytestring` binds `∀ charset value` with
    # no hypothesis — so nothing could exclude an in-domain input and the
    # precondition half is vacuous (a PRECOND-TOO-STRONG finding is
    # unreachable, which is the honest reading, not a gap).
    #
    # Re-aimed at the residual admissibility risk on a total domain: that the
    # obligation is UNSATISFIABLE or DEGENERATE at the interesting point — a
    # spec no impl can meet, and a spec every impl meets, read identically from
    # the gate's side. The tactic body carries in-proof claims at concrete,
    # test-shaped points stating that the spec is satisfiable on each of the
    # four shapes AND non-degenerate on the discriminating one (only the
    # underlying bytes qualify there; a byte list merely DERIVED from them does
    # not). The impl is kept VERBATIM so the real obligation still discharges.
    # The claims are LIVE, not decoration: replacing the non-degeneracy claim
    # with a false one about the same point leaves `⊢ False` unsolved (checked
    # out-of-band).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof("""\
  intro charset value
  -- Admissibility: the obligation is SATISFIABLE at each of the four value
  -- shapes the tests exercise, and NON-DEGENERATE on the byte-view shape (only
  -- the underlying bytes qualify there, not a byte list merely derived from
  -- them). If any of these could not be established the obligation would be
  -- unsatisfiable/degenerate at the interesting point.
  have adm_view :
      problem_spec_toBytestring ['u', '8'] (.memoryviewV [(1 : UInt8)] ['x']) [(1 : UInt8)]
        ∧ ¬ problem_spec_toBytestring ['u', '8'] (.memoryviewV [(1 : UInt8)] ['x'])
              [(0 : UInt8), (1 : UInt8)] := by
    refine ⟨?_, ?_⟩ <;> simp [problem_spec_toBytestring]
  have adm_bytes :
      problem_spec_toBytestring ['a', 's'] (.bytesV [(9 : UInt8)]) [(9 : UInt8)] := by
    simp [problem_spec_toBytestring]
  have adm_str : ∀ (cs s : List Char),
      problem_spec_toBytestring cs (.strV s) (encode cs s) := by
    intro cs s; simp [problem_spec_toBytestring]
  have adm_other : ∀ (cs t : List Char),
      problem_spec_toBytestring cs (.otherV t) (encode cs t) := by
    intro cs t; simp [problem_spec_toBytestring]
  cases value <;>
    simp only [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]"""),
        "rationale": (
            "the obligation is SATISFIABLE at every one of the four value shapes "
            "(a witness output is exhibited for each, at concrete test-shaped "
            "points for the two byte-sequence-like shapes and for all charsets "
            "and payloads on the two encoding shapes) AND NON-DEGENERATE on the "
            "discriminating shape: a view over a byte sequence admits its "
            "UNDERLYING bytes and provably does NOT admit a byte list derived "
            "from them, which is precisely the behaviour the failing test "
            "demands. The impl is kept verbatim so the real obligation "
            "discharges too. Re-aimed from the nagini admiss-shape, whose "
            "read-only-precondition half has no counterpart on this "
            "referentially-transparent, precondition-free carrier. If it fails "
            "=> the spec is UNSATISFIABLE/DEGENERATE at the point the tests "
            "care about, which would make every 'verified' reading of it hollow."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input, plus the refinement argument for why its faithful real
    # counterpart would NOT resolve the tests. Between them: all FOUR clauses
    # are attacked, `value` is moved across all four constructors, `charset`
    # takes five distinct values, and the second field of the view constructor
    # is moved as well.
    # =====================================================================
    {
        "id": "weak-prepatch-view",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image behaviour: a view over a byte sequence is not recognised
        # as byte-like and is instead rendered to text and that text encoded, so
        # it yields the bytes of its textual representation rather than its
        # underlying bytes. Exactly the behaviour the failing test observes.
        "module": _impl("""\
  match value with
  | .bytesV b        => return b
  | .memoryviewV _ r => return encode charset r
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text"""),
        "refinement": (
            "this is the pre-image behaviour. A faithful real counterpart is the "
            "unpatched repo: a response body given as a view over a byte buffer "
            "is not treated as binary, so the emitted content is the encoding of "
            "the view's textual representation rather than the buffer's bytes. "
            "The failing test asserts the content equals those underlying bytes "
            "exactly, and a textual representation is not them, so the "
            "counterpart does NOT resolve. This is the defect the change "
            "corrects, so a rival that verified here would mean the fix is "
            "unobservable through this spec."
        ),
        "rationale": (
            "REJECT from clause C2 (`.memoryviewV b _ => result = b`): the "
            "clause pins the view arm to its UNDERLYING bytes and leaves the "
            "constructor's second field (the textual rendering) as `_`, so a "
            "result computed FROM that second field is refuted. Attacks the "
            "discriminating clause on the discriminating input shape. Refuted at "
            "charset ['l'] and a view carrying bytes [1,2] with rendering ['m'], "
            "conditioned on the encoding of that rendering differing from those "
            "bytes — i.e. on exactly the sub-domain where the rival is wrong. If "
            "it verified => SPEC-TOO-WEAK."
        ),
        "witness": """\
example (h : encode ['l'] ['m'] ≠ [(1 : UInt8), (2 : UInt8)]) :
    ¬ problem_spec_toBytestring ['l'] (.memoryviewV [(1 : UInt8), (2 : UInt8)] ['m'])
        (implementation_toBytestring ['l'] (.memoryviewV [(1 : UInt8), (2 : UInt8)] ['m'])) := by
  unfold problem_spec_toBytestring implementation_toBytestring
  simpa using h
""",
    },
    {
        "id": "weak-view-valuemask",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-MASK near-miss on the SAME arm as weak-prepatch-view, but a
        # strictly closer miss: the answer is still derived from the underlying
        # bytes and still has the right shape (a byte sequence built from them),
        # only with a spurious leading byte. Catches a clause that pinned merely
        # "some byte sequence derived from the buffer" rather than the bytes
        # themselves. Because it agrees with gold over more of the domain than
        # weak-prepatch-view does, it gets its OWN witness at its own point.
        "module": _impl("""\
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return 0 :: b
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text"""),
        "refinement": (
            "transforms the view's bytes rather than carrying them verbatim (one "
            "spurious byte prepended). A faithful real counterpart materialises "
            "such a body into something other than its underlying bytes, so the "
            "emitted content differs byte-for-byte from the buffer. The failing "
            "test asserts equality with the buffer's bytes EXACTLY, so any "
            "deviation — including one extra leading byte — fails it, and the "
            "length-sensitive passing cases that write binary chunks and then "
            "assert the accumulated content and position would fail too. Does "
            "NOT resolve."
        ),
        "rationale": (
            "VALUE-MASK near-miss against C2: same SHAPE (a byte sequence "
            "derived from the view's own bytes), wrong VALUE. C2 requires "
            "`result = b` EXACTLY, not a transform of `b`. Distinct from "
            "weak-prepatch-view, which is wrong for a different reason (it reads "
            "the rendering field instead of the bytes) and agrees with gold on "
            "LESS of the domain; this one agrees except for the extra byte, so "
            "it is refuted at its OWN point — charset ['u','8'], a view carrying "
            "[7] with rendering ['x'] — rather than sharing that witness. Needs "
            "no hypothesis: the error is in the list structure, so it decides at "
            "literal values. If it verified => SPEC-TOO-WEAK (C2 would have "
            "pinned only 'a function of the buffer')."
        ),
        "witness": """\
example :
    ¬ problem_spec_toBytestring ['u', '8'] (.memoryviewV [(7 : UInt8)] ['x'])
        (implementation_toBytestring ['u', '8'] (.memoryviewV [(7 : UInt8)] ['x'])) := by
  unfold problem_spec_toBytestring implementation_toBytestring
  decide
""",
    },
    {
        "id": "weak-bytes-render",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER verbatim-byte arm: a value that already IS a byte
        # sequence is rendered to text and that text encoded, instead of being
        # carried through. The complement of weak-prepatch-view over the second
        # byte-sequence-like shape, and the rival that pushes the encoding
        # callee onto an arm which must not encode anything at all.
        "module": _impl("""\
  match value with
  | .bytesV b        =>
      return encode charset (['b', '\\''] ++ b.map (fun x => Char.ofNat x.toNat) ++ ['\\''])
  | .memoryviewV b _ => return b
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text"""),
        "refinement": (
            "renders a value that is already a byte sequence into its textual "
            "form and encodes that, instead of emitting it unchanged. A faithful "
            "real counterpart breaks the long-standing behaviour that a "
            "byte-sequence body is emitted verbatim: the passing cases that "
            "write binary chunks to a response and then assert both the "
            "accumulated content and the stream position would see the quoted "
            "textual form (longer, and different bytes) instead. Does NOT "
            "resolve those tests, so it is not a candidate real patch."
        ),
        "rationale": (
            "REJECT from clause C1 (`.bytesV b => result = b`): the clause pins "
            "this arm to the bytes themselves and, crucially, forbids routing it "
            "through the encoding callee at all. This is the CONTAINMENT-shaped "
            "attack the nagini sibling's axiom lane argued for from the other "
            "side — the callee must never be reached on a byte-sequence arm — "
            "expressed here as a refutable spec violation rather than as a probe. "
            "Refuted at charset ['a','s'] and the byte sequence [65], "
            "conditioned on the encoding of that arm's rendered text differing "
            "from the byte itself. Moves `value` to the `.bytesV` shape, which "
            "no other rival occupies. If it verified => SPEC-TOO-WEAK (C1 "
            "unconstrained)."
        ),
        "witness": """\
example (h : encode ['a', 's'] ['b', '\\'', 'A', '\\''] ≠ [(65 : UInt8)]) :
    ¬ problem_spec_toBytestring ['a', 's'] (.bytesV [(65 : UInt8)])
        (implementation_toBytestring ['a', 's'] (.bytesV [(65 : UInt8)])) := by
  unfold problem_spec_toBytestring implementation_toBytestring
  simpa using h
""",
    },
    {
        "id": "weak-str-charset-pinned",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the CHARSET BINDER, not the value: a character string is
        # encoded under a FIXED charset rather than the configured one. Right
        # arm, right callee, wrong ARGUMENT — the only rival that mishandles
        # `charset` itself, which is otherwise never load-bearing on the two
        # byte-sequence-like arms.
        "module": _impl("""\
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return b
  | .strV s          => return encode [] s
  | .otherV text     => return encode charset text"""),
        "refinement": (
            "encodes a character-string body under a hardcoded charset instead "
            "of the response's configured one. A faithful real counterpart pins "
            "the encoding name at the call site: it then either fails outright "
            "for an unknown name or emits bytes for the wrong encoding whenever "
            "the configured charset is not the hardcoded one. The passing "
            "string-content and non-ascii content cases assert specific bytes "
            "produced under the configured charset, so they would fail. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause C3 (`.strV s => result = encode charset s`): the "
            "clause pins BOTH arguments of the encoding callee, so passing a "
            "different charset is a violation even though the callee is opaque "
            "and the arm is right. This is the ARGUMENT attack rather than a "
            "result attack — refutable without knowing anything about what the "
            "callee computes, by conditioning on the two calls being "
            "distinguishable at one point. It is the ONLY rival for which "
            "`charset` is load-bearing (C1/C2 ignore it by design), so without "
            "it a wrong impl that mishandled only the charset would verify and "
            "the battery would never notice. Refuted at charset ['c','p'] on the "
            "string ['a']. If it verified => SPEC-TOO-WEAK (the charset binder "
            "would be decorative)."
        ),
        "witness": """\
example (h : encode ['c', 'p'] ['a'] ≠ encode [] ['a']) :
    ¬ problem_spec_toBytestring ['c', 'p'] (.strV ['a'])
        (implementation_toBytestring ['c', 'p'] (.strV ['a'])) := by
  unfold problem_spec_toBytestring implementation_toBytestring
  simpa using h.symm
""",
    },
    {
        "id": "weak-other-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the fourth arm: an arbitrary value's rendered text is dropped
        # and the empty byte sequence emitted instead of its encoding.
        "module": _impl("""\
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return b
  | .strV s          => return encode charset s
  | .otherV _        => return []"""),
        "refinement": (
            "drops an arbitrary value's rendered text and emits nothing. A "
            "faithful real counterpart returns an empty body where a non-empty "
            "encoded rendering is required: the passing case that sets a "
            "non-string body and asserts the content equals that value's digits "
            "would see empty content instead. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C4 (`.otherV text => result = encode charset "
            "text`): the clause pins this arm to the encoding of the rendered "
            "text, so emitting the empty sequence diverges wherever that "
            "encoding is non-empty. Moves `value` to the `.otherV` shape, which "
            "no other rival occupies, and completes the attack on all four "
            "clauses. Refuted at charset ['u','t','f'] on rendered text ['0'], "
            "conditioned on that encoding being non-empty. If it verified => "
            "SPEC-TOO-WEAK (C4 unconstrained)."
        ),
        "witness": """\
example (h : encode ['u', 't', 'f'] ['0'] ≠ []) :
    ¬ problem_spec_toBytestring ['u', 't', 'f'] (.otherV ['0'])
        (implementation_toBytestring ['u', 't', 'f'] (.otherV ['0'])) := by
  unfold problem_spec_toBytestring implementation_toBytestring
  simpa using h.symm
""",
    },
    {
        "id": "weak-swap-arms",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. The port dropped the nagini weak-swap-arms as
        # "redundant on this carrier, every arm is already attacked". That reason
        # does not hold: the per-arm rivals each divert ONE arm and are refuted
        # on that arm, so between them they never test whether a rival that is
        # wrong on ALL FOUR arms at once is caught — a spec whose clauses were
        # somehow mutually compensating would still be attacked only one clause
        # at a time. Landed here rather than agreed with: it builds and
        # discriminates (rival exit 0, gold exit 1 with a SEMANTIC refutation,
        # consistency probe leaves `h ⊢ False` unsolved, and the flipped-claim
        # forgery ELABORATES on gold — so gold's exit code tracks the claim).
        # Inverted dispatch: the two verbatim-byte arms are pushed through the
        # encoding callee (on the rendering, for the view) and the two encoding
        # arms are emptied.
        "module": _impl("""\
  match value with
  | .bytesV b        => return encode charset (b.map (fun x => Char.ofNat x.toNat))
  | .memoryviewV _ r => return encode charset r
  | .strV _          => return []
  | .otherV _        => return []"""),
        "refinement": (
            "an inverted dispatch: byte-sequence-like bodies get routed through "
            "the encoder while character-string and arbitrary bodies emit "
            "nothing. A faithful real counterpart re-encodes binary bodies and "
            "returns an empty body for text, so it fails on BOTH sides at once — "
            "the failing test asserting a view's underlying bytes, and the "
            "passing cases asserting a string body's and a non-string body's "
            "encoded content. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from ALL FOUR clauses simultaneously (C1..C4 are each "
            "violated), which is the one combination the four per-arm rivals do "
            "not probe: each of those is correct on three arms by construction, "
            "so none of them can detect a spec whose clauses only constrain the "
            "result jointly rather than arm-by-arm. Refuted at its OWN point — "
            "charset ['s','w'] on the string ['a'], a sixth distinct input point "
            "and a sixth distinct charset — conditioned on that encoding being "
            "non-empty, i.e. on exactly the sub-domain where the emptied string "
            "arm is wrong. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": """\
example (h : encode ['s', 'w'] ['a'] ≠ []) :
    ¬ problem_spec_toBytestring ['s', 'w'] (.strV ['a'])
        (implementation_toBytestring ['s', 'w'] (.strV ['a'])) := by
  unfold problem_spec_toBytestring implementation_toBytestring
  simpa using h.symm
""",
    },
]

AXIOM_TESTS = []


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 12 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 7 uniqueness rivals) over
# a `Value` carrier with an integer `kind` tag in {OCTETS, VIEW, TEXT, OTHER}
# plus separate raw-octet and code-point fields. This bundle models the SAME
# dispatch as ONE obligation whose `value : PyValue` is the faithful carrier of
# the sibling's `kind` reduced to four disjoint constructors, each carrying
# exactly the payload its arm consumes, with the charset an explicit input.
#
#   sibling case                  -> here
#   -----------------------------------------------------------------------
#   pos-helper-reorder            -> pos-arm-reorder            PORTED
#   pos-oracle-grounded           -> pos-let-bound              PORTED (re-aimed)
#                                    + pos-extensional          (added)
#   admiss-shape                  -> admiss-nondegenerate       RE-AIMED
#   frame-mutate-data             -> (none)                     OMITTED (vacuous)
#   frame-mutate-kind             -> (none)                     OMITTED (vacuous)
#   weak-prepatch-view            -> weak-prepatch-view         PORTED
#   weak-view-encodes             -> weak-prepatch-view         COLLAPSED (carrier)
#   weak-encode-buffer            -> weak-view-valuemask        PORTED (re-aimed)
#                                    + weak-bytes-render        (the other arm)
#   weak-always-encode            -> weak-bytes-render          PORTED (split)
#                                    + weak-prepatch-view       (view half)
#   weak-always-buf               -> weak-other-dropped         PORTED (split)
#   weak-swap-arms                -> weak-swap-arms             PORTED (by audit)
#   (no sibling counterpart)      -> weak-str-charset-pinned    ADDED (binder)
#   AXIOM_TESTS (2)               -> (none)                     DROPPED (G-AX lane)
#
# OMITTED — frame-mutate-data / frame-mutate-kind (2). VACUOUS on this backend,
#   not skipped for difficulty. Both sibling rivals write through a
#   half-permission reference to a field of the read-only input and are rejected
#   by the PERMISSION SYSTEM. Lean is referentially transparent: immutable
#   values, no heap, no aliasing, no fractional permissions, so there is no
#   read-only input to overwrite and the rival cannot be expressed. No
#   substitute probe is fabricated. The Lean analogue of the frame obligation
#   (an unconstrained output component) is separately checked: the
#   postcondition is a total equation on all four arms, and
#   weak-view-valuemask is the probe that would expose such a hole on the
#   discriminating arm.
#
# COLLAPSED — weak-view-encodes. On nagini it special-cases the view kind to
#   encode while the plain-octets kind passes through, isolating the single
#   discriminating sub-domain. Here the view analogue is the ONE `.memoryviewV`
#   constructor, and weak-prepatch-view already makes exactly that arm wrong by
#   routing it to the encoding of the rendering field — the same single-arm
#   attack on the same constructor, so no distinct sub-domain remains. Its
#   value-level distinctness is separately covered by weak-view-valuemask, which
#   is wrong on the same arm for a different reason and is refuted at its own
#   point. Collapsed under carrier narrowing.
#
# SPLIT — weak-always-encode / weak-always-buf / weak-encode-buffer. Each
#   sibling rival violates a whole BRANCH CLASS at once (both buffer kinds, or
#   both non-buffer kinds). On this four-constructor carrier the same violations
#   are expressed per-arm and split into independent rivals, so `value` is moved
#   across all four shapes and each clause is attacked separately: strictly
#   finer probes than the sibling's all-or-nothing rivals.
#
# PORTED BY AUDIT — weak-swap-arms (1). This slot previously read "OMITTED
#   (redundant): every one of the four arms is already attacked independently,
#   so a combined arm-swap would add no clause coverage". That reason was WRONG
#   and the case is now carried. Each per-arm rival is correct on three of four
#   arms by construction, so the battery never exercised a rival wrong on all
#   four AT ONCE, and a spec whose clauses constrained the result only jointly
#   would be attacked one clause at a time forever without noticing. The rival
#   was built and landed rather than argued away: it fails to verify, its witness
#   holds of it and fails on the frozen solution with a semantic refutation
#   (`Ne.symm h has type ¬encode ['s','w'] ['a'] = [] but is expected to have
#   type False`), its consistency probe leaves `h ⊢ False` unsolved, and the
#   flipped-claim forgery ELABORATES against the frozen solution — so gold's
#   exit code tracks what the witness claims rather than a syntactic accident.
#   It also adds a sixth distinct input point and a sixth distinct charset.
#
# ADDED — weak-str-charset-pinned. No sibling counterpart: nagini's
#   `charset_encode(v.cps)` takes no charset argument (the charset is folded
#   into the pure reference), so the sibling battery has no rival that can
#   mishandle it. Here `charset` is an explicit INPUT BINDER of the spec
#   predicate, and one that clauses C1/C2 ignore by design — so without this
#   rival every witness would hold it in a non-load-bearing position and a wrong
#   impl that mishandled only the charset would verify unnoticed. This is the
#   carrier-specific gap the port had to close rather than inherit.
#
# DROPPED — no soundness positive was dropped for an unclosable proof. All three
#   positives were built and their proofs close honestly: pos-arm-reorder under
#   the FROZEN tactic body unchanged, and pos-extensional and pos-let-bound under
#   a reproven body (`simp` in place of `simp only`, same lemma set, no helper
#   lemma, nothing assumed, obligation statement byte-identical).
#
# AUDIT — POSITIVE NON-TRIVIALITY, measured rather than asserted. Each positive's
#   impl was probed against the frozen one with `example :
#   implementation_toBytestring = alt := rfl` in a proof-stripped file. A probe
#   that ELABORATES means the reshape is the frozen impl by another spelling and
#   the case verifies while testing nothing. Results: pos-arm-reorder exit 1
#   (genuinely distinct), pos-extensional exit 1 (genuinely distinct), and
#   pos-let-bound as originally written exit 0 — DEFINITIONALLY EQUAL, because
#   the elaborator erases `Id.run`'s bind, so "one exit point rather than four"
#   was not a different term at all. pos-let-bound was accordingly REBUILT to
#   perturb the two ENCODING arms extensionally (see its own note); the probe on
#   the new form is exit 1 and the frozen tactic body no longer closes it. The
#   two reshaped positives now perturb complementary halves of the dispatch —
#   pos-extensional the two verbatim-byte arms, pos-let-bound the two encoding
#   arms — so every one of the four arms is returned through a syntactically
#   different term in at least one positive.
#
# COVERAGE. FOUR independent top-level clauses (the four arms of the
#   postcondition's match). Each is DEFENDED by three soundness positives plus
#   the admissibility case (all four clauses discharge in every positive) and
#   each is ATTACKED by at least one rival: C1 by weak-bytes-render, C2 by
#   weak-prepatch-view and weak-view-valuemask, C3 by weak-str-charset-pinned,
#   C4 by weak-other-dropped, and ALL FOUR AT ONCE by weak-swap-arms. The `value`
#   binder is moved across ALL FOUR constructors and, within the view
#   constructor, both fields are moved (bytes [1,2]/[7], rendering ['m']/['x']).
#   The `charset` binder takes SIX DISTINCT values across the reject witnesses —
#   ['l'], ['u','8'], ['a','s'], ['c','p'], ['u','t','f'], ['s','w'] — and is
#   load-bearing in weak-str-charset-pinned, the rival built specifically to
#   abuse it. Six DISTINCT input points: no rival is refuted at the same point as
#   another, and the two rivals that share the view arm are separated
#   deliberately because weak-view-valuemask is the NEAR-MISS (it agrees with
#   gold except for one byte) and would otherwise claim a sub-domain the manifest
#   never demonstrated.
#
# AUDIT — SPEC-TOO-WEAK probes beyond this battery (attack D). Eight further
#   wrong impls the battery does not contain were built against the frozen spec,
#   aimed at what the existing rivals leave unattacked: the charset argument on
#   the OTHER encoding arm; a view arm transformed by `.reverse` rather than by
#   prepending; a string arm encoding a doubled payload; the byte arm truncated
#   by `.take 4`; and — the narrowest sub-domain attacks, the ones a clause that
#   only "mostly" pinned its arm would survive — a view arm wrong ONLY when its
#   buffer is empty, ONLY when its rendering is non-empty, ONLY at one literal
#   buffer value, and a string arm wrong ONLY at one literal charset. ALL EIGHT
#   were REJECTED (exit 1, `unsolved goals` on the obligation). No spec hole was
#   found: the four clauses are bare equations quantified over `∀ charset value`,
#   so a rival wrong anywhere in a sub-domain is wrong at that point.
#
# AUDIT — SPEC-TOO-STRONG probes beyond this battery (attack E). Four further
#   CORRECT reshapes were built and PROVEN against the frozen spec: extensional
#   identities on the two ENCODING arms (now carried as pos-let-bound); a view
#   arm guarded by a trivially-true test on the rendering field (`if r = r`); a
#   nested two-level dispatch with an unreachable catch-all arm; and `take`/`drop`
#   plus `List.map id` identities on the byte arms. All four VERIFY (exit 0) under
#   a body reproven with full `simp`. No soundness hole in the spec: it pins the
#   value, not the syntax.
