"""properties.py — G-PBT falsification battery for django__django-12209 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct decideForceInsert`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation, checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted decision over five read-only boolean inputs):

  decideForceInsert (raw forceInsert adding pkDefaultTruthy pkDefaultProvided)
      return (out : Bool)
    ensures out = decidedForceInsert raw forceInsert adding
                                     pkDefaultTruthy pkDefaultProvided        -- C1
    ensures pkHasUsableDefault pkDefaultTruthy pkDefaultProvided
              = (pkDefaultTruthy && pkDefaultProvided)                        -- C2

  with the GROUNDED pure helpers (fully spelled-out boolean functions):

    pkHasUsableDefault td pv        == td && pv
    decidedForceInsert r fi ad td pv == if !r && !fi && ad && (td && pv)
                                        then true else fi

The modeled behaviour is the resolution of a single INSERT-forcing flag for a
persistence request: given five read-only boolean observations, it returns the
boolean controlling whether the row is written by an INSERT-only path. The
INSERT-only path is forced exactly when the request is an ordinary save (not a
direct/unprocessed data load), an INSERT is not already forced, the instance is
freshly added, and its primary key carries a usable default; otherwise the
incoming forcing flag passes through unchanged. All five inputs are read-only
(none `mut`, directive 5).

  C1 is the load-bearing clause: it pins `out` EXACTLY to `decidedForceInsert`,
  a total grounded function of the five inputs. C2 is an impl-INDEPENDENT
  identity about the pure helper (it does not reference `out` and holds
  definitionally for every impl), so no rival can violate it via the impl region;
  it is defended by every positive and is not independently attackable (noted in
  `assessment`). There is no opaque answer-key oracle — the axioms region is
  empty and both helpers are spelled out — so pinning `out = decidedForceInsert`
  is grounded, not an echo.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts a RICHER function ``store_single_table(pk_explicit, force_insert,
pk_set, adding, pk_has_default) -> bool``: the whole update/insert DECISION,
including the identifier-present gate ``pk_set`` and the outcome of the unchanged
UPDATE primitive (``update_matched_row()``, a nullary @ContractOnly axiom). This
bundle models ONLY the purely-functional core the fix actually turns on — the
resolution of the INSERT-forcing flag, i.e. the ``if (...): force_insert = True``
guard the gold patch edits — as a closed boolean function of five booleans. The
downstream update-probe path (``if pk_set and not force_insert:``) and the
``_do_update`` outcome it consults are NOT modeled here (mapping.md §3: the patch
does not change any callee; ``_do_update``/``_do_insert`` fire identically for a
given resolved flag), so there is no axiomatized callee and no ``pk_set`` binder.

Consequently the nagini rivals attached to those UNMODELED behaviours have no
counterpart on this carrier: ``echo-update-row`` echoes an axiom this bundle does
not declare, and ``drop-pk-set`` abuses an identifier-present gate this bundle
does not model. Those are downstream update-decision behaviour the fix does not
touch and this bundle does not model. Carrier narrowing, not a coverage gap —
the footer accounts for every nagini case.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. Lean and Velvet are referentially transparent:
    no heap, no aliasing, no fractional permission. All five inputs are plain
    `Bool` (immutable), none declared `mut`, so there is no read-only frame to
    overwrite. The nagini sibling ALSO records this class as inapplicable (its
    five inputs are immutable primitives passed by value). No substitute probe
    is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A on THIS carrier. The nagini echo surface was
    the nullary @ContractOnly axiom ``update_matched_row()`` (NO Ensures), which
    an impl could bare-echo. This bundle does NOT model that axiom (the update
    primitive is downstream of the modeled flag resolution and is unchanged), so
    there is no answer-key to echo; both helpers are spelled out and C1 is a
    grounded function of the inputs. The positives are honest reshapes.
  * CONTROL-FLOW-EFFECT — N/A: decideForceInsert is a total pure boolean with two
    return paths and no side effect / no raise; the returned bool captures
    everything observable.
  * WRONG-DECISION — the whole reject surface: a rival that drops or inverts one
    of the guard conjuncts, or that drops the pass-through of the incoming
    forcing flag, so `out` diverges from `decidedForceInsert` on the sub-domain
    the mishandled conjunct governs. Six rivals, one per input binder (two on
    `raw`, the fix's discriminator).

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``if`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS PLACEMENT. The method takes FIVE boolean inputs, so its extracted tester
is ``decideForceInsertTester : Bool → Bool → Bool → Bool → Bool → Bool``
(raw forceInsert adding pkDefaultTruthy pkDefaultProvided). Each reject case's
witness asserts ``decideForceInsertTester <pt> = false`` — the extracted program
violates the postcondition at that concrete input. There are NO `require`
clauses, so every input reaches the postcondition (nothing vacuously excluded),
and every literal is a `Bool` so `decide` settles each. The six rivals are
refuted at SIX DISTINCT input points, each varying the binder that rival abuses
(so pts=6, one live probe per binder). Each witness is machine-checked both ways:
it elaborates against its rival's impl and FAILS against the frozen solution.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the decision is
modeled deeply as a spelled-out boolean function — mapping.md §3, no consumed
axiom, G-AX skipped). There is no axiom-soundness obligation to probe, and the
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12209"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen guarded body. Lies wholly inside
# ---- the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). The guard line's
# ---- parenthesised pk-default sub-expression `(pkDefaultTruthy &&
# ---- pkDefaultProvided)` distinguishes it from the pure `decidedForceInsert`
# ---- def (which uses `pkHasUsableDefault ...`), so the anchor is unambiguous.
_IMPL = (
    "    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then\n"
    "      return true\n"
    "    else\n"
    "      return forceInsert\n"
)

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `decideForceInsertTester raw forceInsert adding pkDefaultTruthy
# ---- pkDefaultProvided = false` says the extracted program's result violates
# ---- the postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script can mask the
# ---- verdict. There are no `require` clauses, so every input reaches the
# ---- postcondition. Every literal is a `Bool`, so `decide` settles it.
_TESTER = (
    "extract_program_for decideForceInsert\n"
    "prove_precondition_decidable_for decideForceInsert\n"
    "prove_postcondition_decidable_for decideForceInsert\n"
    "derive_tester_for decideForceInsert\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. The post-image is point-wise over
    # five boolean inputs (no loop, no induction), so each reshape stays within
    # the frozen `loom_solve` script (every reshape reduces to
    # `decidedForceInsert`). Verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-single-disjunction",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: collapse the guarded `if ... then true else forceInsert` into
        # a SINGLE boolean disjunction (the guard OR the incoming forcing flag),
        # in one return with no branch. Semantically identical (matching
        # decidedForceInsert), entirely different executable shape.
        "module": _impl(
            "    return ((!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) || forceInsert)\n"),
        "rationale": "structurally-different but correct: the guarded assignment is "
                     "rewritten as one disjunction (`guard || forceInsert`) in a "
                     "single return with no branch, so `out` still equals "
                     "`decidedForceInsert` on every input (C1 discharges). Pure "
                     "boolean logic the verifier discharges directly — no loop, no "
                     "induction. If it fails to verify, the spec is over-fit to the "
                     "gold if-then-else shape => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-cheapest-grounded",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the cheapest correct impl that still computes the GROUNDED
        # guard via the pure helper `pkHasUsableDefault` and OR-s in the incoming
        # forcing flag. Written as decidedForceInsert's disjunctive normal form.
        "module": _impl(
            "    return (forceInsert || (!raw && !forceInsert && adding && pkHasUsableDefault pkDefaultTruthy pkDefaultProvided))\n"),
        "rationale": "the cheapest CORRECT impl still computes the GROUNDED guard "
                     "(reusing the pure helper `pkHasUsableDefault`) and OR-s in the "
                     "incoming forcing flag — the real decision work — written as "
                     "the disjunctive normal form of `decidedForceInsert`. Must "
                     "verify (else SPEC-TOO-STRONG). Demonstrates the decision is "
                     "grounded in the inputs, not an opaque marker (there is no "
                     "axiom to echo on this carrier).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so the usual "a normal
    # input satisfies the precondition" probe is vacuously satisfied. The
    # residual admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE — a spec no impl can meet reads exactly like a
    # spec every impl meets. This case discharges an in-region `assert` that the
    # decision really DISCRIMINATES: on the exact F2P-shaped explicit-pk re-save
    # input it yields `false` (the UPDATE-probe path stays open), and on the
    # genuinely-new default-pk input it yields `true` (INSERT-only). It
    # establishes the post-image is jointly satisfiable and NON-degenerate (not a
    # constant). The impl is kept as gold so the method's own obligation still
    # discharges and the assert is live.
    # =====================================================================
    {
        "id": "admiss-decision-nonconstant",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      ((decidedForceInsert true false true true true = false) ∧\n"
            "       (decidedForceInsert false false true true true = true)))\n"
            "    if (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then\n"
            "      return true\n"
            "    else\n"
            "      return forceInsert\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate: the decision "
                     "yields `false` on the F2P-shaped explicit-pk re-save (a "
                     "direct/unprocessed data load: raw=true) so the ordinary "
                     "UPDATE-probe path stays open, and `true` on a genuinely-new "
                     "default-pk add (raw=false) so the INSERT-only path fires — a "
                     "genuine two-valued decision, not a constant. The in-region "
                     "assert must discharge (else an unsatisfiable/degenerate "
                     "obligation would read as trivially met); the impl is kept as "
                     "gold so C1 still discharges too. The nagini sibling's "
                     "admissibility control self-called on the F2P-shaped input; "
                     "this carrier has no precondition to establish, so it is "
                     "re-aimed at the total-domain satisfiability/non-degeneracy "
                     "risk over the same discriminating input pair.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT input point (one per binder) and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "prepatch-drop-raw",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating bug: drop the gold-added leading `!raw` conjunct —
        # the EXACT pre-patch guard. Correct on every ordinary-save input, WRONG
        # on the direct/unprocessed data-load sub-domain (raw=true).
        "module": _impl(
            "    if (!forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then\n"
            "      return true\n"
            "    else\n"
            "      return forceInsert\n"),
        "refinement": "drops the gold-added leading conjunct that suppresses the "
                      "INSERT-only path for a direct/unprocessed data load — the "
                      "EXACT pre-patch guard. Its faithful real patch is the "
                      "Django-3.0 regression: re-saving an instance with an "
                      "explicit, already-stored primary key in the "
                      "serializer/loaddata path takes the straight-to-INSERT "
                      "short-cut and issues a second INSERT (duplicate-key failure) "
                      "instead of leaving the UPDATE-probe path open. The "
                      "serializer round-trip F2P (the problem_statement's re-save of "
                      "an explicit-pk instance) FAILS; it would NOT resolve.",
        "rationale": "REJECT from C1: at raw=true, forceInsert=false, adding=true, "
                     "pkDefaultTruthy=true, pkDefaultProvided=true, `decidedForceInsert` "
                     "is false (the data-load leaves the UPDATE path open) but the "
                     "rival, ignoring `raw`, forces the INSERT-only path and returns "
                     "true. Discrimination comes from the `raw` binder. If it "
                     "verified => SPEC-TOO-WEAK (admits the regression).",
        "witness": _witness("decideForceInsertTester true false true true true"),
    },
    {
        "id": "invert-raw",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror bug: use `raw` instead of `!raw`, engaging the short-cut ONLY for
        # a direct/unprocessed data load and SUPPRESSING it for the ordinary
        # freshly-added default-pk save. Opposite-direction to the gold fix.
        "module": _impl(
            "    if (raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided)) then\n"
            "      return true\n"
            "    else\n"
            "      return forceInsert\n"),
        "refinement": "uses `raw` instead of `!raw`, engaging the INSERT-only path "
                      "only for a data load and suppressing it for an ordinary "
                      "freshly-added default-pk save — the mirror of the gold fix. "
                      "Its faithful real patch would re-open the UPDATE probe on a "
                      "genuinely-new default-pk create (the very fast-path the "
                      "original 3.0 commit added, now defeated) and still mishandle "
                      "the data-load re-save; it would NOT resolve.",
        "rationale": "REJECT from C1: at raw=false, forceInsert=false, adding=true, "
                     "pkDefaultTruthy=true, pkDefaultProvided=true, "
                     "`decidedForceInsert` is true (ordinary new default-pk add "
                     "forces INSERT-only) but the rival, requiring `raw`, returns "
                     "the passed-through false. Discrimination comes from the `raw` "
                     "binder in the opposite direction to prepatch-drop-raw. If it "
                     "verified => SPEC-TOO-WEAK (the conjunct's polarity unpinned).",
        "witness": _witness("decideForceInsertTester false false true true true"),
    },
    {
        "id": "drop-adding",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `adding` conjunct: force the INSERT-only path even when the
        # instance is NOT being added for the first time. Correct when adding is
        # true; wrong on the not-adding sub-domain.
        "module": _impl(
            "    if (!raw && !forceInsert && (pkDefaultTruthy && pkDefaultProvided)) then\n"
            "      return true\n"
            "    else\n"
            "      return forceInsert\n"),
        "refinement": "drops the freshly-added conjunct, forcing the INSERT-only "
                      "path even for a NOT-added (already-persisted) default-pk "
                      "instance. Its faithful real patch would take the "
                      "straight-to-INSERT short-cut on an ordinary update of an "
                      "existing default-pk instance, re-inserting instead of "
                      "updating; it would NOT resolve.",
        "rationale": "REJECT from C1: at raw=false, forceInsert=false, adding=false, "
                     "pkDefaultTruthy=true, pkDefaultProvided=true, "
                     "`decidedForceInsert` is false (not adding => pass through) but "
                     "the rival, ignoring `adding`, forces INSERT-only and returns "
                     "true. Discrimination comes from the `adding` binder. If it "
                     "verified => SPEC-TOO-WEAK (the adding conjunct unpinned).",
        "witness": _witness("decideForceInsertTester false false false true true"),
    },
    {
        "id": "drop-pk-default-truthy",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the pk-default TRUTHINESS conjunct, keeping only the "a default was
        # declared" conjunct: force INSERT-only for a declared-but-falsy default.
        # Correct when the default is truthy; wrong on the falsy-default sub-domain.
        "module": _impl(
            "    if (!raw && !forceInsert && adding && pkDefaultProvided) then\n"
            "      return true\n"
            "    else\n"
            "      return forceInsert\n"),
        "refinement": "drops the pk-default TRUTHINESS conjunct, keeping only the "
                      "'a default was declared' conjunct, so a declared-but-falsy "
                      "primary-key default (e.g. a zero/empty default) would force "
                      "the INSERT-only path though its key carries no usable value. "
                      "Its faithful real patch would take the short-cut for such "
                      "models and re-insert an explicit-pk instance; it would NOT "
                      "resolve.",
        "rationale": "REJECT from C1: at raw=false, forceInsert=false, adding=true, "
                     "pkDefaultTruthy=false, pkDefaultProvided=true, "
                     "`decidedForceInsert` is false (pkHasUsableDefault false => "
                     "pass through) but the rival, ignoring the truthiness conjunct, "
                     "forces INSERT-only and returns true. Discrimination comes from "
                     "the `pkDefaultTruthy` binder. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("decideForceInsertTester false false true false true"),
    },
    {
        "id": "drop-pk-default-provided",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the pk-default DECLARED conjunct, keeping only truthiness: force
        # INSERT-only for a pk whose "default" is the truthy no-default sentinel.
        # Correct when a default was declared; wrong on the sentinel sub-domain.
        "module": _impl(
            "    if (!raw && !forceInsert && adding && pkDefaultTruthy) then\n"
            "      return true\n"
            "    else\n"
            "      return forceInsert\n"),
        "refinement": "drops the 'a default was declared' conjunct, keeping only "
                      "truthiness, so a primary key whose default is the truthy "
                      "no-default sentinel would force the INSERT-only path though "
                      "no default was actually provided — the very over-eager "
                      "short-cut the original ticket warned about. Its faithful real "
                      "patch would take the short-cut for defaultless models and "
                      "re-insert; it would NOT resolve.",
        "rationale": "REJECT from C1: at raw=false, forceInsert=false, adding=true, "
                     "pkDefaultTruthy=true, pkDefaultProvided=false, "
                     "`decidedForceInsert` is false (pkHasUsableDefault false => "
                     "pass through) but the rival, ignoring the declared conjunct, "
                     "forces INSERT-only and returns true. Discrimination comes from "
                     "the `pkDefaultProvided` binder (distinct from "
                     "drop-pk-default-truthy). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("decideForceInsertTester false false true true false"),
    },
    {
        "id": "drop-force-insert-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the pass-through of the incoming forcing flag: return ONLY the
        # short-cut guard, so a caller-forced INSERT is DISCARDED whenever the
        # short-cut does not independently fire. Wrong on the forceInsert=true
        # sub-domain where the guard is false.
        "module": _impl(
            "    return (!raw && !forceInsert && adding && (pkDefaultTruthy && pkDefaultProvided))\n"),
        "refinement": "returns only the short-cut guard and DROPS the pass-through "
                      "of the incoming forcing flag, so a caller-forced INSERT is "
                      "silently discarded whenever the short-cut does not fire. Its "
                      "faithful real patch would leave the UPDATE-probe path open on "
                      "a `force_insert=True` save (where the caller demanded an "
                      "INSERT), violating the force_insert contract many saves "
                      "depend on; it would NOT resolve.",
        "rationale": "REJECT from C1: at raw=false, forceInsert=true, adding=false, "
                     "pkDefaultTruthy=false, pkDefaultProvided=false, "
                     "`decidedForceInsert` is true (the incoming forcing flag passes "
                     "through) but the rival, dropping the pass-through, returns the "
                     "short-cut guard's false. Discrimination comes from the "
                     "`forceInsert` binder. If it verified => SPEC-TOO-WEAK (the "
                     "incoming-flag pass-through unpinned).",
        "witness": _witness("decideForceInsertTester false true false false false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals; AXIOM_TESTS = 2, dropped)
# over `store_single_table(pk_explicit, force_insert, pk_set, adding,
# pk_has_default) -> bool` — the WHOLE update/insert decision, whose
# postcondition (clause 1) is `Result == pk_set and not forces_insert(...) and
# update_matched_row()` plus a positive clause 2. THIS bundle models only the
# purely-functional core the fix turns on — the INSERT-forcing FLAG resolution
# `decideForceInsert (raw forceInsert adding pkDefaultTruthy pkDefaultProvided)`
# whose C1 pins `out == decidedForceInsert(...)`. The `pk_set` identifier gate
# and the `update_matched_row()` axiom (the update-DECISION parts, downstream of
# the flag and unchanged by the patch) do NOT exist on this carrier (mapping.md
# §3: no callee changes, no consumed axiom, G-AX skipped). Every nagini case is
# accounted for below.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-reorder                 -> pos-single-disjunction        RE-SHAPED
#   pos-cheapest                -> pos-cheapest-grounded          RE-EXPRESSED
#   admiss-fshape               -> admiss-decision-nonconstant    RE-AIMED
#   prepatch-drop-conjunct      -> prepatch-drop-raw              PORTED (primary)
#   invert-conjunct             -> invert-raw                     PORTED
#   drop-force-insert-factor    -> drop-force-insert-passthrough  RE-EXPRESSED
#   echo-update-row             -> (none)                         NO COUNTERPART
#   drop-pk-set                 -> (none)                         NO COUNTERPART
#                                  (+ drop-adding                 ADDED)
#                                  (+ drop-pk-default-truthy      ADDED)
#                                  (+ drop-pk-default-provided    ADDED)
#
# 2 ported rivals, 1 re-expressed rival, 3 rivals added for binder coverage,
# 2 no-counterpart; 2 re-shaped/re-expressed positives, 1 re-aimed admissibility.
#
# PORTED (2): the GUARD-CONJUNCT rivals carry across. prepatch-drop-conjunct (drop
#   the gold `not pk_explicit`) becomes prepatch-drop-raw (drop the gold `!raw` —
#   the same discriminating fix, mapping.md: nagini pk_explicit ~ velvet raw), the
#   PRIMARY partial-domain rival. invert-conjunct (pk_explicit for not pk_explicit)
#   becomes invert-raw (`raw` for `!raw`). Both carry their nagini refinement
#   argument.
# RE-EXPRESSED rival (drop-force-insert-factor -> drop-force-insert-passthrough):
#   nagini dropped the `force_insert` disjunct of forces_insert; the velvet
#   analogue drops the else-branch pass-through of the incoming forcing flag
#   (`return guard` instead of `if guard then true else forceInsert`), the same
#   force_insert-override defect.
# RE-SHAPED positive (pos-reorder -> pos-single-disjunction): the disjunctive
#   normal form of decidedForceInsert in one branchless return.
# RE-EXPRESSED positive (pos-cheapest -> pos-cheapest-grounded): the cheapest
#   correct impl reusing the grounded pure helper `pkHasUsableDefault`. There is
#   no `update_matched_row()` axiom to AND-in on this carrier (that part is
#   unmodeled), so the grounded analogue is the guard's DNF over the five inputs.
# RE-AIMED (admiss-fshape -> admiss-decision-nonconstant): the nagini self-call
#   established Requires(True) on the F2P-shaped input. This method has no
#   precondition, so that probe is vacuous; it is re-aimed at the residual
#   total-domain risk (an UNSATISFIABLE/degenerate post-image) with a live
#   in-region assert that the decision is genuinely two-valued over the same
#   F2P-shaped input pair (explicit-pk data-load -> false; new default-pk add ->
#   true).
# ADDED (3, no nagini counterpart, for binder coverage): nagini folded the
#   pk-default check into a single `pk_has_default` binder and modeled `adding`
#   without a dedicated drop-rival; velvet models `adding` and SPLITS the
#   pk-default check into two binders (`pkDefaultTruthy` && `pkDefaultProvided`,
#   mapping.md §2). drop-adding, drop-pk-default-truthy and drop-pk-default-provided
#   attack those three guard conjuncts individually, so every velvet binder is
#   varied by some reject witness (see BINDER COVERAGE). Real divergences, each
#   with a machine-checked witness.
# NO COUNTERPART (2): echo-update-row and drop-pk-set both attack the UPDATE
#   DECISION (the `update_matched_row()` axiom echo and the `pk_set`
#   identifier-present gate). Neither the axiom nor the `pk_set` binder is modeled
#   on this carrier — the patch changes only the flag-resolution guard, and the
#   downstream update-probe path fires identically for a given resolved flag
#   (mapping.md §3). Omitted because the modeled surface does not include that
#   behaviour, NOT because it was hard to prove.
# FRAME-MUTATION: VACUOUS. Referentially-transparent backend, no `mut` binder, no
#   heap, no aliasing, no permission system; all five inputs are immutable
#   `Bool`. The nagini sibling itself records this class as inapplicable (five
#   immutable primitives). No substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``if`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# BINDER / CLAUSE / POINT COVERAGE. The method has FIVE boolean binders; each is
#   varied by a reject witness that abuses it: raw (prepatch-drop-raw at raw=true,
#   invert-raw at raw=false), forceInsert (drop-force-insert-passthrough), adding
#   (drop-adding), pkDefaultTruthy (drop-pk-default-truthy), pkDefaultProvided
#   (drop-pk-default-provided). The six witnesses probe SIX DISTINCT input points
#   (pts=6), so no binder is held at one value across every rival. Clause C1
#   (`out = decidedForceInsert`) is attacked by all six and defended by both
#   positives + the admissibility assert. Clause C2 (`pkHasUsableDefault td pv =
#   (td && pv)`) is an impl-INDEPENDENT identity — it does not reference `out` and
#   holds definitionally for every impl region — so no rival can violate it via
#   region surgery; it is not independently attackable (defended by every
#   positive). Each reject witness is elaborated against its own rival impl (six
#   distinct divergences) and each FAILS against the frozen solution
#   (machine-checked both halves out-of-band before submission).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the decision is modeled deeply as a spelled-out boolean function,
# mapping.md §3), so there is nothing there to probe.
AXIOM_TESTS = []
