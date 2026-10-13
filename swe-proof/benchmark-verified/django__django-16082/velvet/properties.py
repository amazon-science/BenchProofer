"""properties.py — G-PBT falsification battery for django__django-16082 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or
inside the ``prove_correct`` tactic body, is changed — both are elided from the
consumer spec view, so ``markers.same_spec`` holds and the ``prove_correct``
obligation survives with a byte-identical statement). ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — ELABORATES against the
rival, FAILS against the witness SUBJECT. The subject here is a declared
``witness_reference`` rather than the frozen solution; see "THE FROZEN IMPL IS
NOT THE WITNESS SUBJECT" below for the measured reason).

DEFENDED SURFACE (one contracted method over two abstract numeric operand
kinds):

  resolveModType (lhs : NumKind) (rhs : NumKind) return (out : Option NumKind)
    ensures out = combinedNumeric lhs rhs            -- the only clause

where ``NumKind`` is one of three abstract numeric kinds — an exact integer
kind, a floating kind, a fixed-precision decimal kind — and ``combinedNumeric``
is a TRANSPARENT ``def`` (directive 8, not an opaque answer-key):

    like-with-like            -> that kind
    integer  × decimal (both) -> decimal   (widen)
    integer  × floating (both)-> floating  (widen)
    floating × decimal (both) -> none      (no common kind)

The whole clause reduces to a pattern match on the two inputs, so ``decide``
computes it and no rival can "echo an oracle" — the only way to satisfy the
postcondition is to actually resolve the two kinds to the correct result kind.

WHAT THE SPEC DEFENDS. The modeled content of the fix is that a MIXED numeric
combination under the remainder operation resolves to the WIDER kind (integer
with decimal -> decimal; integer with floating -> floating), exactly as the
other arithmetic combinations already do — rather than failing to resolve. Those
four mixed widenings are pinned by the whole-``Option``-equality; the reject
rivals attack them along every failure mode the carrier admits: dropping the
mixed widenings entirely, resolving a mix to the NARROWER kind, and resolving
only one of the two mixed sub-domains (decimal vs. floating).

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on BOTH inputs — ``lhs`` and ``rhs`` — each ranging over the three
numeric kinds:

  * the two widening clauses are ORIENTED: (integer, decimal) and (decimal,
    integer) are separate rows, as are (integer, floating) and (floating,
    integer). A rival that mishandles one orientation but not the other is
    refuted only at the orientation it breaks, so the witnesses split across
    both orientations of both widenings.
  * across the four reject witnesses ``lhs`` takes {int, float, dec} and ``rhs``
    takes {int, dec, float} — neither binder is pinned at a single value, so a
    rival mishandling only one input position is caught.

ADVERSARIAL READ of the nagini classes on this NARROWED carrier. The velvet
model captures only the MOD slice over three numeric kinds; nagini's carrier
additionally parameterises the resolver by the arithmetic ``connector`` and adds
a fourth AUTO operand kind. Several nagini cases therefore have no counterpart:

  * CONNECTOR-GATED PARTIAL DOMAIN (nagini ``weak-mod-gated-prepatch`` — the
    literal pre-patch, mixed rows recorded only for the non-remainder
    connectors) — NO COUNTERPART as a distinct rival. This carrier fixes the
    connector to the remainder operation (mapping.md §1: ``resolveModType``
    models the MOD slice only), so there is no ``connector`` binder to gate on;
    a rival that drops the mixed rows "for the remainder connector" is exactly a
    rival that drops them outright. That behaviour IS ported, as
    ``weak-mixed-dropped-all``.
  * AUTO SUB-DOMAIN (nagini ``weak-auto-unresolved``) — VACUOUS. The bijection
    (mapping.md §2) collapses the whole integer family (including the
    auto-increment integer field) onto the single ``NumKind.int`` via the
    resolver's subclass test, so the carrier has no distinct AUTO kind to
    mishandle. The subtype-collapse is validated by G-CONF, not this gate. Not
    fabricated — genuinely absent on this carrier.
  * FRAME-MUTATION — VACUOUS. The nagini sibling carries no frame-mutation case
    either (both operands are immutable ``int`` scalars there), and this backend
    is referentially transparent regardless: the two inputs are immutable
    values, there is no ``mut`` binder and no heap, so there is nothing to
    overwrite. Not fabricated.
  * ADMISSIBILITY (nagini ``admiss-self-call-mod-mixed``) — PORTED, as
    ``admiss-f2p-mixed-grid``. An earlier revision of this manifest recorded the
    lane as VACUOUS because "the bundle declares no ``require`` clause, so there
    is no precondition to admit". That reason is wrong, and the case it dropped is
    a real one: the analogue of PRECOND-TOO-STRONG on a TOTAL carrier is not an
    unsatisfiable ``require`` but an OBLIGATION that is unsatisfiable at exactly
    an F2P-shaped input. A positive that discharges the obligation at that
    concrete input — by evaluation, as an in-region ``assert``, before closing the
    frozen obligation verbatim — tests that directly, and it is neither trivial
    nor tautologous here (see the case's own rationale for the negative control
    that fails).
  * UNGROUNDED-ORACLE ECHO — N/A: ``combinedNumeric`` is a transparent ``def``
    over the two inputs, not an axiomatized oracle; the ``axioms`` region is
    empty (mapping.md §3: no axiom, no ``axiom_check.py``, G-AX skips).
  * AXIOM lane — DROPPED. This gate ignores ``AXIOM_TESTS``; and this bundle has
    no axiom lane at all.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``resolveModTypeTester lhs rhs = false`` says the extracted program's result
violates the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped (so no tactic script can mask the
verdict) and there are no ``require`` clauses, so every input reaches the
postcondition. ``NumKind`` constructors are fully concrete, and the RIVAL impls
are loop-free ``match`` expressions, so ``decide`` settles the whole equality
against every rival — no opaque term, no conditioning, no head binders (hence no
consistency obligation).

THE FROZEN IMPL IS NOT THE WITNESS SUBJECT, and this is load-bearing rather than
incidental. The frozen impl is a ``while`` loop under
``loom.semantics.choice "demonic"``: its extracted tester elaborates through
``Classical.choice``, which the kernel cannot unfold, so ``decide`` on
``resolveModTypeTester …`` against the FROZEN impl is stuck for EVERY claim
regardless of truth::

    Tactic `decide` failed for proposition
      resolveModTypeTester NumKind.float NumKind.int = false
    because its `Decidable` instance … did not reduce to `isTrue` or `isFalse`.

Measured on all four reject cases, and measured against the FORGERY too: the
same statement with ``= false`` flipped to ``= true`` — i.e. asserting the frozen
impl is CORRECT at that input, the opposite of a refutation — fails against the
frozen impl with the byte-identical stuck error (exit 1 both ways). So the frozen
impl's exit code carries NO information about the claim, and "the witness fails
against the frozen solution" would be an attestation to nothing here.

Every reject case therefore names an explicit ``witness_reference``: the
``pos-cheapest-resolve`` impl (``return combinedNumeric lhs rhs``), which is
loop-free, KERNEL-REDUCIBLE, shares the frozen spec byte-for-byte, and VERIFIES
(so it cannot violate its own postcondition anywhere). Against that subject the
exit code tracks the claim, which is the property that makes it evidence:

  * witness (``= false``) vs. the reference -> exit 1, and by a REFUTATION, not a
    stall: ``Tactic `decide` proved that the proposition … = false is false``;
  * forgery (``= true``) vs. the reference -> exit 0.

Recorded here because the same numbers are what a reader needs to tell this cell
from a hollow one, and the stuck-reduction shape is exactly what a hollow cell
looks like from the outside.
"""
from pathlib import Path

INSTANCE = "django__django-16082"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the COMPLETE backward-scan impl body. Lies wholly
# ---- inside the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both asserted at load by _swap), so every surgery stays
# ---- inside the elided region and the frozen spec is never touched. ----
_GOLD_IMPL = (
    "    let combs : List Combinator := modCombinators\n"
    "    let mut res : Option NumKind := none\n"
    "    let mut i := combs.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ combs.length\n"
    "      invariant res = lookup (combs.drop i) lhs rhs\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := combs[i - 1]!\n"
    "      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res\n"
    "      i := i - 1\n"
    "    return res"
)

# ---- proof-region anchor: the frozen tactic body. Unique in Solution.lean.
# ---- Swapped only for soundness positives whose reshaped impl needs a proof
# ---- that closes for the NEW form; the `prove_correct resolveModType`
# ---- STATEMENT (the header) is preserved byte-identically. ----
_GOLD_PROOF = (
    "prove_correct resolveModType by\n"
    "  loom_solve\n"
    "  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]\n"
    "  simp_all"
)


def _impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


def _impl_proof(new_impl: str, new_proof: str) -> str:
    """Replace impl body AND the proof tactic body (header preserved)."""
    return _swap(_impl(new_impl), _GOLD_PROOF, new_proof)


# ---- A structurally-different but behaviourally-equal impl shape reused by the
# ---- positives and (with one row changed) by every reject rival: a direct
# ---- pattern-match dispatch on the two operand kinds. ----
def _match_impl(rows) -> str:
    body = ("    let out : Option NumKind :=\n"
            "      match lhs, rhs with\n")
    for l, r, res in rows:
        body += f"      | .{l}, .{r} => {res}\n"
    body += ("      | _, _ => none\n"
             "    return out")
    return body


_SAME = [("int", "int", "some .int"),
         ("float", "float", "some .float"),
         ("dec", "dec", "some .dec")]
_DEC_MIX = [("int", "dec", "some .dec"), ("dec", "int", "some .dec")]
_FLT_MIX = [("int", "float", "some .float"), ("float", "int", "some .float")]
_DEC_MIX_NARROW = [("int", "dec", "some .int"), ("dec", "int", "some .int")]


# ---- witness preamble: reach the contract through Velvet's tester machinery. ----
_TESTER = (
    "extract_program_for resolveModType\n"
    "prove_precondition_decidable_for resolveModType\n"
    "prove_postcondition_decidable_for resolveModType\n"
    "derive_tester_for resolveModType\n\n"
)


def _witness(lhs: str, rhs: str) -> str:
    return _TESTER + (
        f"example : resolveModTypeTester NumKind.{lhs} NumKind.{rhs} = false := by\n"
        "  decide\n"
    )


# ---- The witness SUBJECT for every reject case. The frozen impl's `while` loop
# ---- elaborates through `Classical.choice` and its tester is `decide`-stuck for
# ---- every claim (the FORGERY asserting `= true` fails identically — see
# ---- "THE FROZEN IMPL IS NOT THE WITNESS SUBJECT" in the module docstring), so
# ---- refuting a witness against the frozen impl would attribute nothing. This
# ---- loop-free impl of the SAME frozen spec is kernel-reducible and VERIFIES
# ---- (it is `pos-cheapest-resolve`, an independently-checked positive of this
# ---- battery), so against it `decide` genuinely returns a verdict and the exit
# ---- code tracks the claim. The gate re-checks both properties (shares the
# ---- frozen spec, and verifies) before honouring it.
_WITNESS_REF = _impl_proof(
    "    return combinedNumeric lhs rhs",
    "prove_correct resolveModType by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both confirmed out-of-band with a
    # real build.
    # =====================================================================
    {
        "id": "pos-cheapest-resolve",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent
        # result-kind relation directly. Because `combinedNumeric` is a
        # spelled-out `def` over the two inputs (not an opaque oracle), this
        # still does the real resolution — there is no wrong echo that verifies.
        # Frozen proof simplifies to `loom_solve` for this shape.
        #
        # This is the SAME source as `_WITNESS_REF`, deliberately and by
        # identity: every reject case refutes its witness against this impl, and
        # the gate's contract for a `witness_reference` is precisely that it
        # shares the frozen spec and VERIFIES. Naming it here as a positive in
        # its own right is what puts that requirement under the gate.
        "module": _WITNESS_REF,
        "rationale": "the cheapest impl satisfying `out = combinedNumeric lhs rhs` "
                     "still performs the real kind resolution, because the "
                     "post-image is a transparent function of the two inputs — not "
                     "an axiomatized answer key. Demonstrates the spec is NOT "
                     "echo-vulnerable and NOT over-fit to the scan shape. Must "
                     "verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-match-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # A genuinely different SHAPE: direct pattern-match dispatch on the two
        # operand kinds instead of the backward first-match scan. Behaviourally
        # equal over the whole 3x3 kind grid (incl. the floating/decimal mix,
        # which resolves to none). The new proof exhausts the nine kind pairs.
        "module": _impl_proof(
            _match_impl(_SAME + _DEC_MIX + _FLT_MIX),
            "prove_correct resolveModType by\n"
            "  loom_solve\n"
            "  cases lhs <;> cases rhs <;> rfl"),
        "rationale": "a structurally-different but correct impl (explicit "
                     "kind-pair dispatch instead of the list scan) that is "
                     "behaviourally equal to gold over the entire 3x3 kind grid "
                     "(incl. the unresolved floating/decimal mix) must verify; "
                     "else the spec is over-fit to the scan shape "
                     "=> SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the PRECOND-TOO-STRONG direction. On a TOTAL carrier the
    # analogue of an unsatisfiable `require` is an OBLIGATION that cannot be
    # discharged at an F2P-shaped input, so this case discharges it AT those
    # inputs, by evaluation, as an in-region `assert`, while keeping the frozen
    # impl byte-for-byte and closing the frozen obligation verbatim.
    # =====================================================================
    {
        "id": "admiss-f2p-mixed-grid",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen impl is kept EXACTLY as-is; only an `assert` is prepended
        # inside the elided impl region, so the method's own `ensures` still has
        # to be discharged for the real scan. The retuned proof sends the extra
        # assert goal to `decide` and then closes the frozen loop-fold goal with
        # the frozen script, unchanged.
        "module": _impl_proof(
            "    assert (with_name_prefix `admiss\n"
            "      ((combinedNumeric NumKind.int NumKind.dec = some NumKind.dec) ∧\n"
            "       (combinedNumeric NumKind.dec NumKind.int = some NumKind.dec) ∧\n"
            "       (combinedNumeric NumKind.int NumKind.float = some NumKind.float) ∧\n"
            "       (combinedNumeric NumKind.float NumKind.int = some NumKind.float) ∧\n"
            "       (combinedNumeric NumKind.float NumKind.dec = none) ∧\n"
            "       (combinedNumeric NumKind.int NumKind.dec\n"
            "          ≠ combinedNumeric NumKind.int NumKind.int)))\n"
            + _GOLD_IMPL,
            "prove_correct resolveModType by\n"
            "  loom_solve\n"
            "  case _ => decide\n"
            "  rw [lookup_drop_step modCombinators i lhs rhs (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": "the obligation must be SATISFIABLE at the F2P-shaped inputs, "
                     "and non-degenerately so; else PRECOND-TOO-STRONG. The assert "
                     "discharges `out = combinedNumeric lhs rhs` by evaluation at "
                     "all four mixed operand pairs the F2P "
                     "test_resolve_output_field_number iterates (both orientations "
                     "of the integer/decimal and integer/floating widenings), plus "
                     "the floating/decimal pair that legitimately has no common "
                     "kind — so the post-image is pinned to a REAL widening at "
                     "exactly the inputs the fix is about, and is simultaneously "
                     "shown not to be the constant `none`. The last conjunct is the "
                     "non-degeneracy check: the mixed result DIFFERS from the "
                     "like-with-like result at the same lhs, so the relation is not "
                     "collapsing every input to one answer. NOT a tautology — it is "
                     "not of the form `combinedNumeric x = combinedNumeric x`, and "
                     "the negative control (the same assert claiming the "
                     "integer/decimal mix resolves to the NARROWER integer kind) "
                     "FAILS to build: `decide` proves that proposition false. The "
                     "frozen impl is retained verbatim so the method's own `ensures` "
                     "must still be discharged for the real scan.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input (ELABORATES against the rival, FAILS against gold — both
    # halves confirmed out-of-band with real builds) and the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-mixed-dropped-all",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (== the pre-patch skeleton, generalised): only the
        # three like-with-like rows resolve; every mixed numeric combination
        # falls through to the unresolved sentinel.
        "module": _impl(_match_impl(_SAME)),
        "refinement": "this is the pre-patch behaviour: the mixed numeric widening "
                      "rows are absent, so a mixed numeric combination under the "
                      "remainder operation fails to resolve. The F2P "
                      "test_resolve_output_field_number iterates the remainder "
                      "operation over mixed numeric operands (e.g. integer with "
                      "decimal, floating with integer) and asserts the combined "
                      "output resolves to the wider numeric type; a faithful real "
                      "counterpart returns no type -> 'Cannot infer type' error, "
                      "so the test still errors. It does NOT resolve.",
        "rationale": "REJECT from `out = combinedNumeric lhs rhs`: on a mixed "
                     "operand pair the post-image is the wider kind but the rival "
                     "returns `none`. Refuted at (floating, integer), where gold "
                     "gives `some .float` and the rival gives `none` — a "
                     "(rhs = integer) point that also varies lhs to the floating "
                     "kind.",
        "witness": _witness("float", "int"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-decimal-narrower",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact defect the issue names ("doesn't resolve to a Decimal"): the
        # integer/decimal mix resolves to the NARROWER integer kind rather than
        # the wider decimal kind. Floating mixes still correct.
        "module": _impl(_match_impl(_SAME + _DEC_MIX_NARROW + _FLT_MIX)),
        "refinement": "this records the integer/decimal mixed rows but with the "
                      "WRONG result kind (the narrower integer kind instead of the "
                      "wider decimal kind) — the precise defect the issue "
                      "describes. test_resolve_output_field_number asserts the "
                      "integer/decimal combination resolves to the decimal type; a "
                      "faithful real counterpart resolves it to the integer type, "
                      "so the assertion fails. It does NOT resolve.",
        "rationale": "REJECT from `out = combinedNumeric lhs rhs`: the post-image "
                     "widens the integer/decimal mix to the decimal kind; the "
                     "rival returns the integer kind. Refuted at (integer, "
                     "decimal), where gold gives `some .dec` and the rival gives "
                     "`some .int` — the (lhs = integer, rhs = decimal) point that "
                     "pins the decimal-widening clause.",
        "witness": _witness("int", "dec"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-only-float-mixed",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial fix WITHIN the mixed sub-domain: only the integer/floating
        # widenings are recorded; the integer/decimal widenings are dropped.
        # Correct on same-type and on floating mixes; wrong on decimal mixes —
        # exactly the half-fix a value-proxy that only spot-checks the floating
        # sub-domain would miss.
        "module": _impl(_match_impl(_SAME + _FLT_MIX)),
        "refinement": "this registers only the integer/floating mixed widenings "
                      "and omits the integer/decimal ones. "
                      "test_resolve_output_field_number's integer/decimal and "
                      "decimal/integer rows fail (a faithful real counterpart "
                      "returns no type for a decimal mix -> 'Cannot infer type' "
                      "error), so the test still errors. It does NOT resolve — "
                      "and this is a NEAR-MISS that passes the floating half of "
                      "the mixed grid.",
        "rationale": "REJECT from `out = combinedNumeric lhs rhs`: the "
                     "decimal/integer mix widens to the decimal kind but the rival "
                     "returns `none`. Refuted at (decimal, integer) — the OTHER "
                     "orientation of the decimal widening (vs. weak-decimal-"
                     "narrower's (integer, decimal)), so the (lhs = decimal) "
                     "position and the reversed row are both exercised.",
        "witness": _witness("dec", "int"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "weak-only-decimal-mixed",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror partial fix: only the integer/decimal widenings are
        # recorded; the integer/floating widenings are dropped. Correct on
        # same-type and on decimal mixes; wrong on floating mixes. Varies the
        # floating kind into the rhs position and attacks the float-widening
        # clause specifically.
        "module": _impl(_match_impl(_SAME + _DEC_MIX)),
        "refinement": "this registers only the integer/decimal mixed widenings and "
                      "omits the integer/floating ones. "
                      "test_resolve_output_field_number's integer/floating and "
                      "floating/integer rows fail (a faithful real counterpart "
                      "returns no type for a floating mix -> 'Cannot infer type' "
                      "error), so the test still errors. It does NOT resolve — the "
                      "mirror near-miss to weak-only-float-mixed.",
        "rationale": "REJECT from `out = combinedNumeric lhs rhs`: the "
                     "integer/floating mix widens to the floating kind but the "
                     "rival returns `none`. Refuted at (integer, floating), which "
                     "puts the floating kind in the rhs position (unseen by the "
                     "other witnesses there) and pins the float-widening clause.",
        "witness": _witness("int", "float"),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling SPEC lane has 8 cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 1-case AXIOM lane.
# This bundle models a NARROWED carrier: the remainder (MOD) slice only, over
# three numeric kinds (the integer family collapsed to one kind), with no
# `connector` binder and no distinct AUTO kind. Case count therefore drops — a
# correct consequence of carrier narrowing, not a thinner battery.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-reorder-mixed-first      -> pos-match-dispatch        RE-EXPRESSED
#   pos-explicit-dispatch        -> pos-match-dispatch        (merged; see below)
#   pos-(cheapest control)       -> pos-cheapest-resolve       ADDED (no-echo floor)
#   admiss-self-call-mod-mixed   -> admiss-f2p-mixed-grid      PORTED
#   weak-mod-gated-prepatch      -> weak-mixed-dropped-all     COLLAPSED (no connector)
#   weak-mixed-dropped-all       -> weak-mixed-dropped-all     PORTED
#   weak-mixed-decimal-narrower  -> weak-decimal-narrower      PORTED
#   weak-only-float-mixed        -> weak-only-float-mixed      PORTED
#   (new — binder/clause cover)  -> weak-only-decimal-mixed    ADDED
#   weak-auto-unresolved         -> (none)                     VACUOUS (no AUTO kind)
#   AXIOM_TESTS (1)              -> (none)                     DROPPED (G-AX lane)
#
# COLLAPSED (weak-mod-gated-prepatch): the nagini rival gates the mixed rows
#   behind `connector != MOD`. This carrier is already specialised to the
#   remainder connector (mapping.md §1), so "drop the mixed rows for MOD" is
#   simply "drop the mixed rows" — the pre-patch skeleton. It is ported as
#   weak-mixed-dropped-all (which is exactly the pre-patch behaviour).
# RE-EXPRESSED / merged (pos-reorder, pos-explicit-dispatch): nagini's two
#   positives are a reorder of mutually-exclusive guards and an explicit code
#   dispatch. On this carrier the backward scan's row guards are not surface-
#   reorderable without also reshaping the proof; the explicit-dispatch positive
#   is the strictly more informative of the two (a genuinely different algorithm
#   shape, not a permutation), so it is carried as pos-match-dispatch and the
#   pure reorder is subsumed. The cheapest-resolve control is added as the
#   no-echo floor (there is no @Pure oracle to echo here — the post-image is a
#   transparent def — so returning it directly is the honest positive control).
# PORTED (admissibility): an earlier revision recorded this lane as VACUOUS on
#   the ground that the bundle declares no `require` clause, so "there is nothing
#   to admit". That reasoning does not hold and the lane is now carried as
#   admiss-f2p-mixed-grid. On a total carrier the PRECOND-TOO-STRONG direction
#   shows up as an obligation that cannot be discharged at an F2P-shaped input,
#   not as an unsatisfiable precondition; the ported case discharges the
#   obligation at exactly the four mixed operand pairs the F2P iterates (plus the
#   legitimately-unresolved floating/decimal pair) by evaluation, keeps the frozen
#   impl verbatim, and closes the frozen obligation with the frozen script. It is
#   not the tautology the old note predicted: the negative control asserting the
#   mixed pair resolves to the NARROWER kind fails to build.
# VACUOUS (weak-auto-unresolved): the bijection collapses the integer family
#   (incl. the auto-increment integer field) onto NumKind.int, so there is no
#   distinct AUTO kind to mishandle; the subtype collapse is a G-CONF concern,
#   not expressible as a reject rival here. Carrier fact, not an effort gap.
# VACUOUS (frame-mutation): referentially transparent carrier, no `mut` binder,
#   no heap — no read-only input to overwrite. (Nagini carried none either.)
#
#   The four reject witnesses probe four DISTINCT input points:
#     (float,int) (int,dec) (dec,int) (int,float).
#   lhs takes {int, float, dec}; rhs takes {int, dec, float} — neither binder
#   pinned. Both widening clauses are attacked in BOTH orientations: decimal
#   widening at (int,dec) [narrower-kind failure] and (dec,int) [dropped];
#   floating widening at (float,int) [dropped] and (int,float) [dropped]. Every
#   rival module was confirmed by a real build to fail verification with the
#   frozen proof retained, by a SEMANTIC `unsolved goals` on the postcondition
#   (not a tactic error). Every witness was confirmed by real builds to ELABORATE
#   against its rival (exit 0) and to be REFUTED against the declared
#   `witness_reference` (exit 1, `decide` proved the proposition false) — NOT
#   against the frozen impl, whose loop makes its tester `decide`-stuck for every
#   claim; see the docstring section on the witness subject for the forgery
#   measurement that establishes this.
#
# AXIOM_TESTS: dropped. This bundle ships no axiom and no axiom_check.py
# (mapping.md §3, G-AX skips); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
