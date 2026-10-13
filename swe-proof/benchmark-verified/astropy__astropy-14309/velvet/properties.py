"""properties.py — G-PBT falsification battery for astropy__astropy-14309 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct classifyFitsOrigin`` obligation survives) and swaps in a
candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method, one obligation):

  classifyFitsOrigin (stream, path, extra)
    ensures out = originSpec stream path extra

An origin is classified by consulting three observations in a fixed PRIORITY
order, and the outcome carrier is ``Except Crash Bool`` — either a verdict is
returned (``ok b``) or the absent-observation failure escapes (``error``):

  (L1) stream = some s        -> out = ok s
       a present readable-stream observation yields its signature verdict, and
       it is consulted FIRST — before the path — so it decides even when a path
       is also present;
  (L2) stream = none, path = some p -> out = ok (hasKnownExt p)
       with no stream but a path present, the path's case-insensitive
       known-extension verdict is returned OUTRIGHT, for every path, matching or
       not, and the trailing sequence is never reached — so the failure can NEVER
       escape on this leg;
  (L3) stream = none, path = none   -> out = the first trailing observation, or
       the escaping failure when the trailing sequence is empty.

L2 is the discriminating behaviour the public problem statement reports: a
path-only consultation on a non-matching name must yield a plain negative
verdict, not fall through to a positional observation that is not there and let
the failure escape. The F2P regression is exactly that single point. But the
spec pins all three legs, the ORDER among them, the extension test's own suffix
set AND case fold, and the escaping failure's exact domain (L3-with-empty only),
and the battery attacks each of those independently — the P2P suite pins L1, L3
and the priority order just as hard as the F2P pins L2, so a rival that "fixes"
L2 by disturbing any of the rest does not resolve.

``originSpec`` and ``hasKnownExt`` are TRANSPARENT ``def``s in the ``pure``
region over the method's own arguments — the ``axioms`` region declares only the
outcome inductive ``Crash``, no ``axiom`` at all — so pinning
``out = originSpec …`` is GROUNDED in the inputs, not an echo of an opaque
answer key. That is why the cheapest honest impl (report ``originSpec`` directly)
is a legitimate POSITIVE CONTROL rather than a cheat: every wrong leg still fails
the equality.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
contracts a six-input int/bool predicate ``is_recognised_input`` returning an int
code R_TRUE/R_FALSE/R_FAULT, with four postcondition clauses (C1 totality, C2/C3
the present-path verdict, C4 the no-fault guarantee) plus a MustTerminate
precondition. Here the three sentinel codes are replaced by the honest carrier
``Except Crash Bool`` (so C4 — "a present path never faults" — is not a separate
clause but a consequence of L2 being an ``ok``), and nagini's six scalar inputs
become three structured ones: the stream's boolean collapses to ``Option Bool``,
the path becomes a real ``List Char`` the extension test runs on, and the
trailing-argument COUNT plus first-accepted flag become one ``List Bool``. That
last widening is a strict GAIN: nagini could only say "n_trailing == 0 or not",
whereas here the traversal itself is attackable.

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini class needs
    a read-only input carrying a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent and this method
    declares NO ``mut`` binder: all three inputs are immutable values, there is
    no heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe to build. Not fabricated. (The nagini sibling reached the
    same disposition for the same reason, one carrier earlier.)
  * DIVERGENCE — the spec REJECTS this class; it is NOT a spec hole here, and
    it is not shippable as a reject case either. This bundle sets
    ``set_option loom.semantics.termination "total"`` (line 4 of the frozen
    file), and in Loom that option is itself what opens ``TotalCorrectness``
    scope, so a postcondition is claimed of ALL runs, not only terminating ones,
    and every loop owes a measure that STRICTLY DECREASES.
    Measured directly, twice: a ``while true do pure ()`` prefix ahead of gold's
    own body, and the same prefix returning an unambiguously wrong value, are
    BOTH rejected (exit 1) with ``error: Decreasing annotations are required in
    total correctness semantics`` — the total-correctness obligation, i.e. a
    rejection attributable to the spec. The nagini sibling's
    divergence-self-recursion is therefore closed here by the same direction of
    obligation it was closed by there (MustTerminate(2)).
    It is nonetheless NOT shipped, for a demonstrated MECHANICAL reason rather
    than a spec one: on this backend a reject case must carry a witness that
    ELABORATES against the rival, and the missing-measure error is raised on the
    METHOD DECLARATION, which the witness file retains after the
    ``prove_correct`` block is stripped (this disposition tracks the termination
    option and must be re-derived if it ever moves). So every witness build against a
    diverging rival fails on that same error before reaching its claim (measured
    on three rivals — the two above and a rival diverging only on the
    ``(none, none, [])`` sub-domain, whose witness sits outside it: all exit 1 on
    the loop error, and the unguarded pair additionally shows ``decide`` stuck,
    ``did not reduce to `isTrue` or `isFalse```). Witness half 1 is unmeetable,
    so the case could only ever record ``witness-unproven``. The class is closed
    by the spec and unrepresentable in the manifest — not an admitted rival. See
    the footer.
  * UNGROUNDED-ORACLE ECHO — N/A, and carried as a positive control instead
    (pos-report-spec-directly), exactly as the nagini sibling did: the post-image
    is a total unfolded function of the inputs, so "echoing" it IS gold.
  * PARTIAL-DOMAIN / VALUE / PRIORITY-ORDER — the whole reject surface, spread
    over all three legs and the order among them, at two grains each (a WIDE
    rival wrong on most of a leg, and a NARROW one wrong only on a sub-domain).

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``classifyFitsOriginTester stream path extra = false`` says the extracted
program's result violates the method's postcondition at that concrete input,
closed by ``decide``. Every input type is fully decidable (``Option Bool``,
``List Char``, ``List Bool``; ``Crash`` derives ``DecidableEq``), so every
witness pins all three inputs to CONCRETE literals — no witness conditions on the
carrier, hence no witness binds a hypothesis and no consistency probe is needed
(there are no assumptions that could be jointly unsatisfiable).
``prove_postcondition_decidable_for`` needs equality of the outcome carrier
``Except Crash Bool`` decidable, so the preamble derives that instance first — an
instance, not an assumption (no ``axiom``/``sorry``/``native_decide``). Each
witness is checked in a file whose ``prove_correct`` block has been stripped, so
no tactic script can mask the verdict; each was checked out-of-band with
scripts/lean_verify.sh and SEEN to discriminate — it ELABORATES against its rival
(exit 0) and FAILS against the frozen solution with the SEMANTIC error ``Tactic
`decide` proved that the proposition classifyFitsOriginTester … = false is
false`` (i.e. gold's tester ACCEPTS the point), never an unknown identifier, type
error or timeout.

AXIOM lane: DROPPED. The nagini sibling ships an empty ``AXIOM_TESTS`` (its
axioms region is empty). Here the ``hasKnownExt`` deep model is an A-REFERENCE
validated against the real case-folding suffix test by axiom_check.py — that is
G-AX's job, not this gate's, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14309"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end`. Every variant
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- impl region and same_spec holds by construction (both facts asserted at
# ---- load by _swap).
_IMPL = """    -- Branch in order on the available observations. A present stream yields its
    -- signature verdict; a present path yields its known-extension verdict
    -- DIRECTLY (returned in full, matching or not, never falling through); only
    -- when neither is present is the first trailing positional observation read,
    -- and an empty trailing sequence lets the absent-observation failure escape.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p => Except.ok (hasKnownExt p)
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""

# The frozen proof, verbatim. A correct RESHAPE whose residual goal the frozen
# script no longer closes may retune this block (elided from the spec view)
# WITHOUT touching the spec or dropping the obligation — the
# `prove_correct classifyFitsOrigin` header survives, which is what
# variant_scope requires on velvet. Rivals leave it exactly as-is: their
# rejection is carried by the witness, never by a retuned tactic script.
_PROOF = """prove_correct classifyFitsOrigin by
  loom_solve
  simp_all [originSpec]"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a correct reshape whose
    residual goal no longer closes under the frozen `simp_all`)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. `prove_postcondition_decidable_for` needs equality of
# ---- the outcome carrier `Except Crash Bool` decidable, so derive that
# ---- instance first. The tester names (`classifyFitsOriginExec` /
# ---- `classifyFitsOriginTester`) are brought into scope by directives inside
# ---- the witness itself, which is appended to BOTH the rival and the frozen
# ---- file, so both sides share the vocabulary by construction.
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for classifyFitsOrigin\n"
    "prove_precondition_decidable_for classifyFitsOrigin\n"
    "prove_postcondition_decidable_for classifyFitsOrigin\n"
    "derive_tester_for classifyFitsOrigin\n\n"
)


def _wit(stream, path, extra):
    """`<name>Tester s p e = false` — the extracted program's result violates the
    method's postcondition at that concrete, fully-literal input."""
    return (_PREAMBLE
            + f"example : classifyFitsOriginTester {stream} {path} {extra}"
              " = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation statement and reshapes only the
    # executable surface; where the reshape moves the residual goal, the tactic
    # body is retuned (elided from the spec view) — never weakened, and both
    # were confirmed to close with the real verifier.
    # =====================================================================
    {
        "id": "pos-joint-match-flattened",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the two nested scrutinees are FLATTENED into one joint match
        # on the pair `stream, path`, so the priority order is expressed by arm
        # order over a product rather than by nesting. Same three legs, same
        # order, same outcome on every input. The flattened match no longer
        # reduces under the frozen `simp_all`, so the tactic body is retuned with
        # an explicit case split on the three scrutinees.
        "module": _impl_reproved(
            """    -- Same priority cascade, expressed as ONE joint match on the pair of
    -- leading observations instead of two nested ones.
    let result : Except Crash Bool :=
      match stream, path with
      | some s, _      => Except.ok s
      | none,   some p => Except.ok (hasKnownExt p)
      | none,   none   =>
        match extra with
        | []     => Except.error Crash.indexOOB
        | a :: _ => Except.ok a
    return result""",
            """prove_correct classifyFitsOrigin by
  loom_solve
  cases stream <;> cases path <;> cases extra <;> simp_all [originSpec]"""),
        "rationale": (
            "Flattening the two nested scrutinees into a joint match over the "
            "pair preserves the priority order (the `some s, _` arm still wins "
            "over `none, some p`) and computes the identical "
            "`Except Crash Bool` on all three legs, so `out = originSpec …` "
            "still holds pointwise. A correct reshape MUST verify, else "
            "SPEC-TOO-STRONG on the syntactic form of the cascade. Ports the "
            "nagini pos-control-localvar-reshape argument (same first-match "
            "semantics, different control shape) onto this carrier — where the "
            "cheap reshape is match-flattening rather than a single-return "
            "local, since the impl is already an expression."),
    },
    {
        "id": "pos-report-spec-directly",
        "kind": "soundness",
        "expect": "verify",
        # The honest cheapest impl: report the transparent pure post-image
        # directly. Because `originSpec` is a total `def` fully unfolded over the
        # method's own arguments — NOT an opaque answer key — this IS the gold
        # behaviour, so it is a positive control and not an echo cheat. With the
        # inline match gone the residual goal is closed by `loom_solve` alone and
        # the frozen `simp_all [originSpec]` tail becomes `No goals to be
        # solved`, so the tail is dropped (a retune, not a weakening: the
        # obligation header is untouched).
        "module": _impl_reproved(
            """    -- Report the intended outcome of the classification directly.
    let result : Except Crash Bool := originSpec stream path extra
    return result""",
            """prove_correct classifyFitsOrigin by
  loom_solve"""),
        "rationale": (
            "The post-image `originSpec stream path extra` is GROUNDED in the "
            "method's own inputs (a total `def` in the `pure` region; the "
            "`axioms` region declares no `axiom`, only the outcome inductive), "
            "so reporting it directly is the honest cheapest CORRECT impl and "
            "MUST verify, else SPEC-TOO-STRONG. Doubles as the directive-2 "
            "control that the spec is not echo-vulnerable: there is no opaque "
            "answer key to echo, and any wrong leg still fails the equality — "
            "which the eight rivals below demonstrate. Ports the nagini "
            "pos-control-grounded-oracle-delegate verbatim in argument."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admissibility-f2p-shaped case.
    # That case asserted, inside the impl region, that the F2P-shaped facts
    # establish every Requires clause. This method's `pre-conditions` region is
    # EMPTY (no `require` at all), so nothing could exclude any input and the
    # classic "a legitimate input satisfies the precondition" probe is vacuous.
    # Re-aimed at the residual total-domain risk: that the post-image is jointly
    # SATISFIABLE at every input SHAPE (a spec no impl can meet reads exactly
    # like a spec every impl meets). The witness is deliberately NOT the frozen
    # impl — resubmitting gold would re-run the gold build and attest nothing
    # this manifest is responsible for — but an independent total computation
    # that splits every scrutinee down to its CONSTRUCTORS.
    # =====================================================================
    {
        "id": "admiss-every-input-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            """    -- Independent total computation: every scrutinee is split down to its
    -- constructors and each leaf verdict is rebuilt explicitly, so the
    -- obligation is discharged separately at every shape of every input.
    let result : Except Crash Bool :=
      match stream with
      | some true  => Except.ok true
      | some false => Except.ok false
      | none =>
        match path with
        | some p => if hasKnownExt p then Except.ok true else Except.ok false
        | none =>
          match extra with
          | []         => Except.error Crash.indexOOB
          | true  :: _ => Except.ok true
          | false :: _ => Except.ok false
    return result""",
            """prove_correct classifyFitsOrigin by
  have f2pShape : originSpec none (some "data.txt".toList) [] = Except.ok false := by
    rfl
  have f2pMatch : originSpec none (some "table.FITS".toList) [] = Except.ok true := by
    rfl
  have f2pEscape : originSpec none none [] = Except.error Crash.indexOOB := by
    rfl
  loom_solve
  cases stream <;> cases path <;> cases extra <;>
    simp_all [originSpec] <;> split <;> simp_all"""),
        "rationale": (
            "The method carries NO `require`, so it is total over every "
            "(stream, path, extra); this case witnesses that the post-image "
            "`out = originSpec …` is jointly SATISFIABLE at every input shape "
            "rather than only at the gold impl's syntactic form. The witness is "
            "an INDEPENDENT computation, not the frozen impl: it splits `stream` "
            "at {some true, some false, none}, `path` at {some, none} with the "
            "extension verdict case-split, and `extra` at {[], true::_, "
            "false::_}, rebuilding each leaf verdict explicitly — so the "
            "equality is discharged at all of them. "
            "The analogue of PRECOND-TOO-STRONG on a TOTAL carrier is the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input, so "
            "the tactic body discharges that input CONCRETELY and by evaluation "
            "before closing the frozen obligation verbatim: three `have`s pin "
            "`originSpec none (some \"data.txt\".toList) [] = ok false` (the "
            "F2P-shaped point — no stream, a present NON-matching path, an empty "
            "trailing sequence — where the demanded answer is a plain negative "
            "verdict and NOT an escaping failure), `originSpec none (some "
            "\"table.FITS\".toList) [] = ok true` (the same shape at an "
            "upper-case MATCHING name, so the case-folded leg is reachable too), "
            "and `originSpec none none [] = error` (the escape is still "
            "satisfiable on its own one-column domain). Each closes by `rfl`, "
            "i.e. the post-image REDUCES to those values rather than being "
            "assumed; if any were unsatisfiable the `have` would not close and "
            "the case would fail. Then the frozen obligation is closed "
            "unchanged. Else SPEC-UNSATISFIABLE / PRECOND-TOO-STRONG."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input SEEN to discriminate, and the refinement argument for why
    # its faithful real counterpart would NOT resolve.
    #
    # Every rival below leaves the frozen `prove_correct` block untouched, so
    # none of them can "reject" by having retuned a tactic script.
    # =====================================================================

    # ---- L2: the present-path leg (the discriminating F2P behaviour) ----
    {
        "id": "weak-path-falls-through-on-no-match",
        "kind": "uniqueness",
        "expect": "reject",
        # The EXACT pre-image behaviour (Solution_prepatch.lean): a present path
        # short-circuits only on a MATCH; a non-matching path falls THROUGH to
        # read a trailing positional observation, and the failure escapes when
        # the sequence is empty. Correct on L1, on L3, and on the matching half
        # of L2; wrong exactly on a present NON-matching path.
        "module": _impl(
            """    -- A present path short-circuits ONLY on a match; a non-matching path
    -- falls through to the trailing positional observation.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p =>
          if hasKnownExt p then Except.ok true
          else
            match extra with
            | []     => Except.error Crash.indexOOB
            | a :: _ => Except.ok a
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "This is the pre-image behaviour verbatim — the state of the "
            "classifier BEFORE the change. Its faithful real patch is therefore "
            "the unchanged routine, on which the single F2P regression (a "
            "path-only consultation with a non-matching name and no trailing "
            "positional observation) does not return a negative verdict at all "
            "but lets the absent-observation failure escape as the very error "
            "the public problem statement reports. The F2P asserts a plain "
            "negative verdict, so it FAILS and the instance does NOT resolve. "
            "This is exactly the defect the change corrects, so a verifying "
            "rival here would mean the spec cannot see the bug."),
        "rationale": (
            "REJECT from L2 (`stream = none, path = some p -> out = ok "
            "(hasKnownExt p)`): on a present NON-matching path the impl reaches "
            "the trailing sequence and, finding it empty, produces the escaping "
            "failure where the post-image demands `ok false`. Refuted at "
            "`(none, some \"data.txt\", [])` — a present non-matching path with "
            "an empty trailing sequence, the F2P-shaped point, where gold "
            "returns `ok false`. If it verified => SPEC-TOO-WEAK (the spec would "
            "admit the pre-image, and G-DIFF's premise would be false)."),
        "witness": _wit("none", '(some "data.txt".toList)', "[]"),
    },
    {
        "id": "weak-path-always-affirmative",
        "kind": "uniqueness",
        "expect": "reject",
        # A present path yields the AFFIRMATIVE verdict unconditionally: the
        # extension test is never consulted. Total (never lets the failure
        # escape on L2, so it satisfies the no-escape half of the leg) yet wrong
        # on the VERDICT for every non-matching path.
        "module": _impl(
            """    -- A present path yields the affirmative verdict unconditionally.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some _ => Except.ok true
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "Its faithful real patch returns the affirmative verdict for every "
            "present path instead of the extension test's result. On the F2P "
            "input (a path-only consultation with a non-matching name) it "
            "returns the affirmative where the test asserts the negative, so the "
            "F2P FAILS outright. It additionally misclassifies every "
            "non-candidate name as a candidate, which breaks the "
            "format-identification dispatch the unchanged P2P suite exercises "
            "throughout. It does NOT resolve."),
        "rationale": (
            "REJECT from L2 on the VERDICT rather than the escape: the impl "
            "takes the right leg and returns an `ok`, but not of `hasKnownExt "
            "p`. This is the complement of the fall-through rival — it satisfies "
            "the 'a present path never lets the failure escape' half of L2 (the "
            "clause nagini spelled separately as C4) and still violates the leg, "
            "showing the spec pins the verdict and not merely the outcome "
            "constructor. Refuted at `(none, some \"data.txt\", [true, false])` "
            "— a NON-EMPTY, length-2 trailing sequence, so the point also "
            "demonstrates the trailing sequence is irrelevant on this leg and "
            "varies that binder away from the fall-through rival's `[]`. Ports "
            "the nagini value-swap-unrecognised-true. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _wit("none", '(some "data.txt".toList)', "[true, false]"),
    },
    {
        "id": "weak-path-escapes-when-trailing-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # NARROW near-miss on L2: a present path yields its correct extension
        # verdict whenever a trailing observation EXISTS, and lets the failure
        # escape only when the trailing sequence is empty. Agrees with gold on
        # the whole of L1, the whole of L3, and all of L2 with a non-empty
        # trailing sequence — i.e. everywhere the two wide L2 rivals above are
        # refuted except the one column that matters.
        "module": _impl(
            """    -- A present path yields its known-extension verdict, EXCEPT that an
    -- empty trailing sequence still lets the failure escape.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | _ :: _ => Except.ok (hasKnownExt p)
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "The surgically-minimal rival: its faithful real patch keeps the "
            "fall-through but guards it so that a present path is only answered "
            "when a trailing positional observation happens to be available. The "
            "F2P consultation supplies NO trailing positional observation at "
            "all, so on exactly that input the absent-observation failure still "
            "escapes and the F2P FAILS. It does NOT resolve — and it is the "
            "rival most likely to look like a fix, since it answers every "
            "path-only consultation that has a trailing argument correctly."),
        "rationale": (
            "REJECT from L2 on a NARROW sub-domain: the impl is correct on L1, "
            "on L3, and on L2 whenever the trailing sequence is non-empty, and "
            "wrong only where a path is present AND the trailing sequence is "
            "empty — the sub-domain that decides the F2P. Refuted at `(none, "
            "some \"test.fits\", [])`, a point chosen so the path is a MATCHING "
            "name: it shows the leg is violated even where the extension test "
            "succeeds, so the defect is the reachability of the trailing "
            "sequence and not the verdict, and it varies `path` to a matching "
            "value no other witness uses. Ports the nagini "
            "narrow-fault-leak-f2p-only. If it verified => SPEC-TOO-WEAK (the "
            "spec would be blind to a one-column escape leak)."),
        "witness": _wit("none", '(some "test.fits".toList)', "[]"),
    },
    {
        "id": "weak-path-recognises-one-suffix-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The remaining L2 grain: the leg is reached correctly and answered
        # OUTRIGHT (never escaping), but the extension test itself is narrowed to
        # a single recognised suffix. Wrong only on paths bearing one of the
        # other recognised suffixes — a sub-domain the three rivals above all
        # get right.
        "module": _impl(
            """    -- A present path is answered outright, but only ONE recognised suffix
    -- is accepted by the test.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p => Except.ok (".fits".toList.isSuffixOf (p.map Char.toLower))
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "Its faithful real patch answers every present path outright — so it "
            "DOES fix the escaping failure and the F2P passes — but narrows the "
            "recognised-suffix set to a single member. The unchanged P2P suite "
            "round-trips files written under the other recognised suffixes and "
            "reads them back without an explicit format, so those reads no "
            "longer identify a format and FAIL. It does NOT resolve. This rival "
            "is the reason the spec must pin the extension test itself and not "
            "just 'a present path yields some verdict outright'."),
        "rationale": (
            "REJECT from L2 on the extension TEST: the impl reaches the leg, "
            "answers outright (never escaping) and returns an `ok`, but of a "
            "STRICTLY NARROWER predicate than `hasKnownExt p`. Refuted at "
            "`(none, some \"test.fts\", [true])` — a path bearing a recognised "
            "suffix OTHER than the one kept, where gold returns `ok true` and "
            "the rival `ok false`; the three L2 rivals above all agree with gold "
            "at this point, so the battery genuinely varies the `path` binder "
            "across matching-and-narrowed, matching, and non-matching names "
            "rather than probing one name repeatedly. The trailing sequence is "
            "pinned NON-EMPTY here on purpose: at `[]` the "
            "escapes-when-trailing-empty rival also diverges from gold, so this "
            "rival would not be separated from it. No nagini counterpart: "
            "nagini collapsed the whole extension test into the single boolean "
            "input `path_recognised`, so it could not express a rival that "
            "computes that boolean WRONGLY. If it verified => SPEC-TOO-WEAK."),
        "witness": _wit("none", '(some "test.fts".toList)', "[true]"),
    },
    {
        "id": "weak-path-ext-test-case-sensitive",
        "kind": "uniqueness",
        "expect": "reject",
        # The last unattacked grain of the extension test: the full recognised
        # suffix SET is kept, the leg is reached and answered outright, but the
        # test is applied WITHOUT the case fold. Wrong only on paths whose
        # recognised suffix is not already lowercase — a sub-domain every other
        # rival in the battery gets right, and the one clause the `path` binder's
        # case-insensitivity actually rests on.
        "module": _impl(
            """    -- A present path is answered outright against the full recognised
    -- suffix set, but the test is applied WITHOUT folding case.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p => Except.ok (knownExts.any (fun ext => ext.isSuffixOf p))
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "Its faithful real patch answers every present path outright — so "
            "the escaping failure is fixed and the F2P passes — but compares the "
            "path against the recognised suffixes without first folding it to "
            "lower case. The unchanged P2P suite round-trips files whose names "
            "carry a recognised suffix in upper or mixed case, and those reads no "
            "longer identify a format and FAIL. It does NOT resolve, which is "
            "why the spec must pin the CASE-INSENSITIVE test and not merely "
            "suffix membership."),
        "rationale": (
            "REJECT from L2 on the case-fold half of the extension test — the "
            "grain the one-suffix rival leaves untouched (it narrows the SET "
            "while keeping the fold; this one keeps the set and drops the fold). "
            "Refuted at `(none, some \"TEST.FITS\", [])`, an upper-case matching "
            "name where gold returns `ok true` and the rival `ok false`, and the "
            "only witness in the battery that varies the path's CASE. The "
            "one-suffix rival agrees with gold at this point and this rival "
            "agrees with gold at that one, so the two are mutually separated. "
            "Attacks the `hasKnownExt` A-reference clause mapping.md §3.1 binds "
            "to the real case-folding suffix test. If it verified => "
            "SPEC-TOO-WEAK (the spec would pin suffix membership but not the "
            "case fold)."),
        "witness": _wit("none", '(some "TEST.FITS".toList)', "[]"),
    },

    # ---- L1: the present-stream leg (untouched by the change, still pinned) ----
    {
        "id": "weak-stream-verdict-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # A leg the change does not touch, but which the same frozen spec pins:
        # the stream's signature verdict is reported INVERTED.
        "module": _impl(
            """    -- The present stream's signature verdict is reported inverted.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok (!s)
      | none =>
        match path with
        | some p => Except.ok (hasKnownExt p)
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "Its faithful real patch inverts the readable-stream branch's "
            "signature comparison. The change does not touch that branch, but a "
            "rival sharing the frozen spec must still honour it: on a genuine "
            "stream of the format under recognition the classifier would return "
            "the negative verdict, so the unchanged P2P round-trips that read "
            "from an open stream no longer identify a format and FAIL. It does "
            "NOT resolve. Ports the nagini unchanged-branch-stream-swap "
            "argument."),
        "rationale": (
            "REJECT from L1 (`stream = some s -> out = ok s`): the impl returns "
            "the complement of the observation. Refuted at `(some false, none, "
            "[])`, the only witness pinning `stream` to `some false`; taken with "
            "the priority rival's `some true` and the six `none` points, the "
            "`stream` binder is observed at ALL THREE of its shapes across the "
            "battery, so no rival could mishandle it unnoticed. Confirms the "
            "spec pins the whole cascade and not only the changed leg. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness": _wit("(some false)", "none", "[]"),
    },

    # ---- the ORDER among the legs ----
    {
        "id": "weak-path-consulted-before-stream",
        "kind": "uniqueness",
        "expect": "reject",
        # Every leg computed correctly in isolation; only their PRIORITY is
        # swapped, so the path decides when both a stream and a path are
        # present. Invisible to any input where at most one leading observation
        # is present — which is every other witness in this battery.
        "module": _impl(
            """    -- The path is consulted BEFORE the readable-stream observation.
    let result : Except Crash Bool :=
      match path with
      | some p => Except.ok (hasKnownExt p)
      | none =>
        match stream with
        | some s => Except.ok s
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok a
    return result"""),
        "refinement": (
            "Its faithful real patch consults the path before the stream. It "
            "answers every present path outright, so the F2P passes — but the "
            "unchanged caller supplies BOTH a path and an opened stream for the "
            "same origin, and the P2P suite contains a round-trip whose file has "
            "no recognised suffix at all and is identified purely from its "
            "stream contents. Under the swapped order that read consults the "
            "suffix, gets the negative verdict, identifies no format and FAILS. "
            "It does NOT resolve."),
        "rationale": (
            "REJECT from the priority ORDER between L1 and L2, which no other "
            "rival attacks: each leg's own verdict is computed exactly as the "
            "post-image demands, and only their precedence differs, so the impl "
            "is indistinguishable from gold on every input where at most one "
            "leading observation is present. Refuted at `(some true, some "
            "\"data.txt\", [])` — the ONLY point in the battery where a stream "
            "and a path are BOTH present and disagree, so it is also the only "
            "point that exercises the two binders jointly. `originSpec` matches "
            "on `stream` first, so gold returns `ok true` and the rival `ok "
            "false`. Re-sites the nagini priority-cascade attack, which had no "
            "dedicated case there. If it verified => SPEC-TOO-WEAK (the spec "
            "would pin three verdicts but not which one wins)."),
        "witness": _wit("(some true)", '(some "data.txt".toList)', "[]"),
    },

    # ---- L3: the trailing-observation leg and the escape domain ----
    {
        "id": "weak-trailing-never-consulted",
        "kind": "uniqueness",
        "expect": "reject",
        # With neither leading observation present the trailing sequence is
        # never consulted at all: a constant negative verdict is returned, and
        # the failure never escapes. Correct on L1 and L2.
        "module": _impl(
            """    -- With neither leading observation present, the trailing sequence is
    -- never consulted: a negative verdict is returned.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p => Except.ok (hasKnownExt p)
        | none   => Except.ok false
    return result"""),
        "refinement": (
            "Its faithful real patch answers every present path outright (so the "
            "F2P passes) and replaces the trailing-observation consultation with "
            "a constant negative verdict. The unchanged P2P suite consults the "
            "classifier with NEITHER a path nor a stream — passing an in-memory "
            "object of the format as the sole positional argument — and relies on "
            "the class-membership check to identify the format. Under this rival "
            "those consultations always answer negatively, so those reads "
            "identify no format and FAIL. It does NOT resolve."),
        "rationale": (
            "REJECT from L3 (`stream = none, path = none -> the first trailing "
            "observation decides`): the impl discards the trailing sequence "
            "entirely. Refuted at `(none, none, [true])` — a non-empty trailing "
            "sequence whose head is affirmative, where gold returns `ok true` "
            "and the rival `ok false`. This is the only witness that observes "
            "the trailing HEAD deciding the outcome. Re-sites the nagini "
            "C1-totality attack onto the leg nagini encoded as the "
            "first_trailing_accepted input. If it verified => SPEC-TOO-WEAK "
            "(the trailing observation would be unpinned)."),
        "witness": _wit("none", "none", "[true]"),
    },
    {
        "id": "weak-trailing-verdict-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on L3: the trailing sequence IS traversed, the empty case
        # still escapes exactly where it should, and only the head's verdict is
        # reported inverted. Agrees with gold wherever the previous rival is
        # refuted in shape (it does consult the head) and differs only in value.
        "module": _impl(
            """    -- The first trailing observation is consulted, but its verdict is
    -- reported inverted.
    let result : Except Crash Bool :=
      match stream with
      | some s => Except.ok s
      | none =>
        match path with
        | some p => Except.ok (hasKnownExt p)
        | none =>
          match extra with
          | []     => Except.error Crash.indexOOB
          | a :: _ => Except.ok (!a)
    return result"""),
        "refinement": (
            "Its faithful real patch negates the class-membership check on the "
            "trailing positional argument. The F2P passes (a present path is "
            "answered outright), and the escaping failure still occurs on "
            "exactly the right domain, but every consultation that identifies "
            "the format from an in-memory object of that format now answers "
            "negatively — and every consultation with an object of some OTHER "
            "class answers affirmatively. The unchanged P2P reads that pass such "
            "an object directly therefore FAIL. It does NOT resolve."),
        "rationale": (
            "REJECT from L3 on the trailing VALUE rather than on whether the "
            "sequence is consulted: the impl traverses correctly and lets the "
            "failure escape on exactly the empty case, so it satisfies the "
            "escape-domain half of L3 and the whole of L1 and L2, and is wrong "
            "only in the head's verdict. Refuted at `(none, none, [false])` — a "
            "distinct point from the never-consulted rival's `[true]`, chosen "
            "because at `[false]` THAT rival coincides with gold while this one "
            "diverges, so the two are genuinely separated and the trailing "
            "head is observed at both booleans. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness": _wit("none", "none", "[false]"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING
#
# The nagini sibling ships 8 SPEC cases (2 soundness, 1 admissibility, 5
# uniqueness) and an EMPTY AXIOM_TESTS. It contracts a six-input int/bool
# predicate returning one of three sentinel codes, with four postcondition
# clauses C1-C4 plus a MustTerminate(2) precondition. This bundle contracts ONE
# method over the same behaviour with an honest `Except Crash Bool` carrier and
# three structured inputs. The carrier is not merely narrowed here — on the path
# and trailing-sequence binders it is WIDER, which is where the two added cases
# come from.
#
#   nagini case                        -> here                              status
#   ---------------------------------------------------------------------------
#   (divergence-self-recursion is answered by the spec's `total` termination
#    obligation but cannot be carried as a manifest case; see the DIVERGENCE
#    block below for the three measured rivals.)
#   partial-domain-prepatch-fallthrough-> weak-path-falls-through-on-no-match PORTED
#   value-swap-unrecognised-true       -> weak-path-always-affirmative        PORTED
#   narrow-fault-leak-f2p-only         -> weak-path-escapes-when-trailing-    PORTED
#                                         empty
#   unchanged-branch-stream-swap       -> weak-stream-verdict-inverted        PORTED
#   divergence-self-recursion          -> (none)                    SPEC-CLOSED/UNSHIPPABLE
#   pos-control-localvar-reshape       -> pos-joint-match-flattened          RE-SHAPED
#   pos-control-grounded-oracle-delegate-> pos-report-spec-directly           PORTED
#   admissibility-f2p-shaped           -> admiss-every-input-shape            RE-AIMED
#   (no nagini source)                 -> weak-path-recognises-one-suffix-only ADDED
#   (no nagini source)                 -> weak-path-ext-test-case-sensitive     ADDED
#   (no nagini source)                 -> weak-path-consulted-before-stream    ADDED
#   (no nagini source)                 -> weak-trailing-never-consulted        ADDED
#   (no nagini source)                 -> weak-trailing-verdict-inverted       ADDED
#   AXIOM_TESTS (0)                    -> (none)                             N/A
#
# 12 velvet SPEC cases: 2 soundness, 1 admissibility, 9 uniqueness.
#
# PORTED (5): the four nagini rivals whose attacked clause survives on this
#   carrier, plus the grounded-oracle positive. The nagini C4 clause ("a present
#   path never faults") is not a separate clause here — the honest `Except`
#   carrier makes it a consequence of L2 being an `ok` — so the two rivals
#   nagini split across C3-vs-C4 (value-swap and narrow-fault-leak) land on the
#   same leg here but at DIFFERENT grains, and are kept separate for that
#   reason: one violates the verdict while satisfying no-escape, the other
#   violates no-escape while satisfying the verdict.
# RE-SHAPED (1): pos-control-localvar-reshape -> pos-joint-match-flattened. The
#   nagini positive reshaped two returns into a single assign-once local; the
#   frozen impl here is already an expression, so the cheap behaviour-preserving
#   reshape is flattening the nested scrutinees into a joint match. Same
#   argument: same semantics, different control shape, must verify.
# RE-AIMED (1): admissibility-f2p-shaped -> admiss-every-input-shape. The nagini
#   case asserted the Requires clauses are establishable for F2P-shaped facts.
#   This method's pre-conditions region is EMPTY, so that probe is vacuous here
#   (nothing can exclude an input); re-aimed at post-image joint satisfiability,
#   witnessed by an independent constructor-split computation rather than by
#   resubmitting gold. The F2P-shaped point the nagini case pinned is one of the
#   shapes it discharges.
# ADDED (5, by the adversarial audit of this port — the carrier here is WIDER
#   than nagini's on two binders, so these attack clauses nagini could not even
#   state):
#  * weak-path-recognises-one-suffix-only. Nagini collapsed the whole extension
#    test into ONE boolean input `path_recognised`, so a rival that computes that
#    boolean wrongly was inexpressible there. Here `path : List Char` and the
#    test is a real `def`, so a narrowed suffix set is a rival — and without it
#    the battery would pin only "a present path is answered outright", not WHAT
#    it is answered with.
#  * weak-path-ext-test-case-sensitive (added by the INDEPENDENT audit of this
#    battery, which found the case fold was the one clause of the extension test
#    no shipped rival attacked: every rival either kept `hasKnownExt` whole or
#    narrowed its suffix SET, so a rival keeping the set and dropping the FOLD
#    verified nothing about mapping.md §3.1's case-insensitivity claim. Built and
#    measured: rejected (exit 1, `unsolved goals`), witness discriminates at an
#    upper-case matching name.
#  * weak-path-consulted-before-stream. No nagini rival attacked the PRIORITY
#    order; every nagini rival changed a verdict. This one changes nothing but
#    precedence and is invisible at every input where at most one leading
#    observation is present — i.e. at seven of this battery's eight witness
#    points. It is the case that forces the (stream, path) binders to be
#    exercised JOINTLY.
#  * weak-trailing-never-consulted / weak-trailing-verdict-inverted. Nagini's
#    trailing sequence was two scalars (a count and a first-accepted flag), so it
#    could attack only "does it fault". Here `extra : List Bool` leaves the
#    traversal and the head's value transparent, giving a shape rival (the
#    sequence is never consulted) and a value rival (the head is inverted) that
#    separate at complementary points.
# DIVERGENCE: CLOSED BY THE SPEC, and unrepresentable as a manifest case. NOT a
#   spec hole. An earlier revision of this file recorded it as one, on the basis
#   that this bundle runs `partial`; that was simply WRONG. Line 4 of the frozen
#   file reads `set_option loom.semantics.termination "total"`, and in Loom that
#   option is itself what opens `TotalCorrectness` scope
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the setting and the scope
#   cannot disagree. Under `total` a postcondition is claimed of ALL runs, not
#   only terminating ones, and the total loop generator emits a per-iteration
#   side condition that the measure STRICTLY DECREASES, so a diverging rival is
#   rejected rather than admitted. The disposition is a function of that option,
#   which is exactly why it is re-derived below from real builds rather than
#   inherited.
#   Re-derived here with the real verifier rather than inherited:
#     * `while true do pure ()` ahead of gold's own body   -> exit 1
#     * the same prefix returning an unambiguously wrong value -> exit 1
#     both with `error: Decreasing annotations are required in total correctness
#     semantics` — the total-correctness obligation, i.e. a rejection
#     attributable to the spec, exactly the direction MustTerminate(2) supplies
#     in the nagini sibling. So the nagini divergence-self-recursion case's
#     ATTACK is answered here; the spec does not admit a diverging impl.
#   It is still not shipped as a reject case, for a MECHANICAL reason that was
#   measured, not assumed: a velvet reject case needs a witness that ELABORATES
#   against the rival, and the missing-measure error is raised on the METHOD
#   DECLARATION, which survives into the witness file (only the `prove_correct`
#   block is stripped). So the witness build fails on the loop error before it
#   ever reaches its claim. Measured on three rivals — the two above, plus one
#   diverging ONLY on the `(none, none, [])` sub-domain with its witness placed
#   outside that sub-domain: all three exit 1 on the declaration error, and the
#   two unguarded ones additionally show `decide` stuck (`did not reduce to
#   `isTrue` or `isFalse``). Witness half 1 is unmeetable, so such a case could
#   only ever record `witness-unproven` — a malformed case, not an attestation.
#   Disposition: the class is closed by the frozen spec and cannot be expressed
#   in this manifest. Nothing is owed here and no hole is claimed.
# FRAME / PERMISSION-MUTATION — VACUOUS (see the module docstring): no `mut`
#   binder, no heap, no aliasing, so no read-only input to overwrite. The nagini
#   sibling recorded the same disposition for the same reason and shipped no such
#   case either, so nothing was dropped.
# AXIOM lane — nothing to drop: the nagini sibling's AXIOM_TESTS is already
#   empty. This bundle's `hasKnownExt` A-reference is validated against the real
#   case-folding suffix test by axiom_check.py (G-AX), which is that gate's job;
#   G-PBT ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE (what replaces case-count parity).
#   The single obligation `out = originSpec stream path extra` is DEFENDED by
#   three `expect="verify"` cases (two reshapes plus the constructor-split
#   admissibility computation) and ATTACKED by nine rivals. Its three
#   independent legs plus the ORDER among them are each attacked separately, and
#   every leg at two or more grains:
#     L1 (stream)          : weak-stream-verdict-inverted
#     L2 (path)            : falls-through (escape) / always-affirmative (verdict)
#                            / escapes-when-trailing-empty (narrow escape column)
#                            / recognises-one-suffix-only (the test's suffix SET)
#                            / ext-test-case-sensitive (the test's CASE FOLD)
#     L3 (trailing)        : never-consulted (shape) / verdict-inverted (value)
#     ORDER (L1 before L2) : consulted-before-stream
#   The nine reject witnesses probe NINE DISTINCT input points, and every input
#   binder is varied across them rather than held fixed:
#     stream : none (x7), some false, some true       — all three shapes
#     path   : none (x3), some "data.txt" (x3, non-matching),
#              some "test.fits" (matching), some "test.fts" (matching under a
#              suffix the narrowed rival drops), some "TEST.FITS" (matching only
#              under the case fold)
#     extra  : [] (x5), [true] (x2), [false], [true, false] — empty, both head
#              booleans, and length 2
#   No binder is held at one value by every witness, which is the failure mode
#   that hid both of the real breaks found so far.
#
#   SEPARATION — what is and is NOT claimed. Each witness point is one where its
#   own rival diverges from gold; that much is machine-checked for all nine (the
#   `decide` refutation on the frozen file names the point). Being refuted at a
#   point where EVERY sibling coincides with gold is a stronger property, and it
#   holds for FOUR of the nine, not all of them — measured, not asserted:
#     escapes-when-trailing-empty  @(none, "test.fits", [])   uniquely divergent
#     recognises-one-suffix-only   @(none, "test.fts", [true]) uniquely divergent
#     stream-verdict-inverted      @(some false, none, [])    uniquely divergent
#     trailing-verdict-inverted    @(none, none, [false])     uniquely divergent
#   The other five share their point with one or two siblings, which is harmless
#   (a witness attests that ITS rival violates the spec there, not that no other
#   rival does) but is not the stronger claim, so it is not made:
#     falls-through @(none,"data.txt",[])      also divergent: always-affirmative,
#                                              escapes-when-trailing-empty
#     always-affirmative @(none,"data.txt",[true,false]) also: falls-through
#     ext-test-case-sensitive @(none,"TEST.FITS",[]) also: escapes-when-trailing-empty
#     consulted-before-stream @(some true,"data.txt",[]) also: stream-verdict-inverted
#     trailing-never-consulted @(none,none,[true]) also: trailing-verdict-inverted
#   Where PAIRWISE separation is the point it is checked pairwise and holds: the
#   two L3 rivals separate at complementary heads (never-consulted diverges at
#   `[true]` where inverted-trailing also does, but at `[false]` ONLY
#   inverted-trailing diverges, and never-consulted agrees with gold there); and
#   the two extension-test rivals separate exactly (one-suffix diverges at
#   "test.fts" where case-sensitive agrees with gold, case-sensitive diverges at
#   "TEST.FITS" where one-suffix agrees with gold).
#   The one-suffix witness pins `extra = [true]` rather than `[]` for this
#   reason: at `[]` the escapes-when-trailing-empty rival diverges too, and the
#   point would not isolate the extension test from the escape leak. That was a
#   real defect in the first port of this battery, found by the audit.
#
# DROPPED (1 rival, and why — a known gap, deliberately not shipped):
#  * A rival whose L3 empty-trailing case returns `ok false` instead of letting
#    the failure escape (i.e. it SUPPRESSES the escape rather than misreporting
#    it) was built and measured: it is rejected by the verifier and its witness
#    at `(none, none, [])` was SEEN to discriminate (elaborates against the
#    rival, fails on gold). It is nonetheless NOT shipped, because its
#    `refinement` argument does not hold: its faithful real patch answers every
#    present path outright AND guards the trailing access, so the F2P passes and
#    no unchanged test in the P2P set consults the classifier with neither a path
#    nor a stream nor any positional argument. It therefore appears to RESOLVE,
#    which makes it a plausible alternative fix rather than a
#    verify-does-not-imply-resolve break — and shipping it would assert a
#    refinement claim this manifest cannot support. The escape DOMAIN is still
#    attacked from the other side, by weak-path-escapes-when-trailing-empty
#    (which makes the failure escape where it must not).
#
# VERIFIER EVIDENCE (out-of-band, with scripts/lean_verify.sh, before handoff;
#   the gate's own run is authoritative):
#   * frozen Solution.lean: exit 0.
#   * the 3 `expect="verify"` cases: exit 0 each. Two needed a retuned tactic
#     body (the flattened match and the constructor split move the residual
#     goal); the obligation header is byte-identical in all three and no case
#     adds a lemma, an axiom, or a `sorry`.
#   * the 9 rivals: exit 1 each, `error: unsolved goals` — a real residual
#     obligation, not a parse or elaboration failure.
#   * the 9 witnesses, both halves: each ELABORATES against its own rival (exit
#     0) and FAILS against the frozen solution (exit 1) with the semantic error
#     ``Tactic `decide` proved that the proposition classifyFitsOriginTester …
#     = false is false`` — gold's tester ACCEPTS the point, which is the
#     discrimination the gate re-runs. No witness binds a hypothesis, so no
#     consistency probe applies and none can be inconsistent.
#
# INDEPENDENT AUDIT of this battery (all builds re-run with
#   scripts/lean_verify.sh; exit codes observed, not predicted):
#   * All 11 original cases re-built: 3 positives exit 0, 8 rivals exit 1
#     (`unsolved goals`); frozen Solution.lean exit 0.
#   * All 8 original witness pairs re-built: rival exit 0 / gold exit 1, every
#     gold-side failure a SINGLE semantic `decide` refutation naming the exact
#     point the rationale claims. No stuck reduction, no unknown identifier, no
#     type error, no timeout on any of the 16 builds.
#   * SPEC-TOO-WEAK probe (attack D) — 7 NEW wrong impls the battery did not
#     contain, all REJECTED (exit 1, `unsolved goals`): the L3-empty leg
#     returning `ok true`; reading the LAST trailing observation instead of the
#     first; the case-fold dropped; the suffix test widened to match a recognised
#     extension ANYWHERE in the name (via `tails`/`isPrefixOf`); the trailing
#     sequence consulted BEFORE the path; an empty path `some []` treated as
#     absent. No new impl verified, so no spec hole was found on the value legs.
#     The case-fold one was good enough to keep and is now shipped as
#     weak-path-ext-test-case-sensitive.
#   * SPEC-TOO-STRONG probe (attack E) — 3 NEW correct reshapes, all VERIFIED
#     (exit 0): a `Nat`-free `if h : stream.isSome` ladder using `Option.get`;
#     an `Option.map`/`getD` composition over the two leading legs; the trailing
#     head read via `extra.head?`. Each needed only the same
#     `cases … <;> simp_all [originSpec]` retune the shipped positives use, so
#     the spec is not tuned to the frozen impl's syntactic form.
#   * Two prose defects were FOUND AND FIXED, both over-claims a gate cannot
#     see: the one-suffix witness sat at `extra = []`, where the
#     escapes-when-trailing-empty rival ALSO diverges from gold, so its
#     rationale's "the three L2 rivals above all agree with gold at this point"
#     was false — repaired by moving the point to `[true]`, where it is now true
#     and the rival is uniquely divergent; and the blanket claim that EVERY
#     near-miss is refuted where its siblings coincide with gold held for only
#     four of the points, so the separation block above now states per-point
#     which are unique and which are shared.
#
# SECOND INDEPENDENT AUDIT (a later, separate pass; every exit code below was
#   OBSERVED with scripts/lean_verify.sh, none predicted):
#   * Statement integrity (attack A): for all 12 cases the method header through
#     `ensures` is BYTE-IDENTICAL to the frozen file, as are the axioms+pure and
#     pre/post regions, and every case's obligation header is
#     `prove_correct classifyFitsOrigin by`. No case reformats the statement.
#   * All 12 cases rebuilt: 3 positives exit 0, 9 rivals exit 1 (`unsolved
#     goals`); frozen Solution.lean exit 0.
#   * All 9 witness pairs rebuilt: rival exit 0, gold exit 1, and every gold-side
#     log holds EXACTLY ONE error, the plain-evaluation refutation ``Tactic
#     `decide` proved that the proposition … = false is false``. No stuck
#     reduction, no unknown identifier, no type error, no timeout.
#   * FORGERY test (attack B′) run on all 9 witnesses even though each gold
#     signature is a plain evaluation: flipping the claim to `= true` and
#     rebuilding against the FROZEN solution gives exit 0 for all nine. Gold's
#     exit code therefore TRACKS the claim (0 for the true claim, 1 for the false
#     one) rather than being claim-independent, so no witness is hollow.
#   * Observable-difference check (attack C): each rival was re-modeled
#     independently and compared against the post-image over a 150-point grid
#     (stream x 3, path x 10 including empty/multi-dot/mixed-case names, extra x
#     5). All 9 differ from gold somewhere AND at their own witness point (3 to
#     100 divergent points each), so no rival is a mere reshape. The per-point
#     separation table above was re-derived and matches exactly: the same 4
#     uniquely-divergent points and the same 5 shared ones.
#   * SPEC-TOO-WEAK probe (attack D) — 8 further NEW wrong impls, all REJECTED
#     (exit 1): L3-empty returning `ok true`; L3-empty returning `ok false`
#     (the escape SUPPRESSED — the rival documented as DROPPED below); the LAST
#     trailing observation instead of the first; the trailing sequence consulted
#     BEFORE the path; `some []` treated as an absent path; the suffix test
#     widened to match anywhere in the name (`tails`/`isPrefixOf`); only the
#     `.gz`-bearing suffixes recognised; and the case fold applied to the
#     SUFFIXES instead of the path. No new wrong impl verified — no spec hole.
#   * SPEC-TOO-STRONG probe (attack E) — 4 further NEW correct reshapes, all
#     VERIFIED (exit 0): an `Option.map`/`getD` cascade over both leading legs;
#     an `if h : stream.isSome` ladder using `Option.get`; the trailing head via
#     `extra.head?`; and a joint match on the pair with the arms written
#     `path, stream` (scrutinees in the opposite order). Each closed with only
#     the same `cases … <;> simp_all [originSpec]` retune the shipped positives
#     use, so the spec is not tuned to the frozen impl's syntactic form.
#   * TWO DEFECTS FOUND AND FIXED, both invisible to the gate:
#     (1) The divergence disposition was STALE, and stale in the direction that
#         claims a defect the artifact does not have. This file asserted twice
#         that the bundle runs `partial` and recorded the class as a KNOWN SPEC
#         HOLE, but the frozen file's line 4 reads `"total"` (the corpus-wide
#         flip to total semantics, applied to this cell outside this lane), and
#         the diverging rival is in fact REJECTED, measured on three rivals; see
#         the DIVERGENCE block. A battery asserting a hole in a spec that closes
#         the class is a false finding on the artifact, so the disposition is now
#         "closed by the spec, unrepresentable as a case" with the mechanical
#         reason measured. NOTE for re-ports: this disposition is a function of
#         the termination option and must be re-derived, never inherited, if that
#         option ever moves again.
#     (2) The admissibility case discharged the obligation only GENERICALLY (a
#         constructor split over all shapes) and its rationale nonetheless
#         claimed it covered "the F2P-shaped point the nagini admissibility case
#         pinned". Nothing in the case named that input, so the claim was not
#         demonstrated. Repaired by discharging it CONCRETELY and by evaluation:
#         three `have`s now pin the post-image at the F2P-shaped input and at two
#         neighbours (an upper-case matching name; the escape's own one-column
#         domain), each closing by `rfl`, BEFORE the frozen obligation is closed
#         verbatim. `decide` does NOT work here (`failed to synthesize Decidable`
#         for an `Except` equation) — `rfl` does, and was measured to.
AXIOM_TESTS = []
