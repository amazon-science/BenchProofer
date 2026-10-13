"""properties.py — G-PBT falsification battery for django__django-14007 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO functions with fractional-permission contracts: an inner per-row
converter fold (``apply_row``) and an outer per-row driver (``execute_returning``),
each over immutable ``PSeq`` sequences. This Lean bundle collapses that pair into
a SINGLE total function over the observable inputs — the returning fields (each
carrying its converter chain), the two capability flags selecting the backend
pathway, and the three candidate raw row batches — returning the post-processed
rows. The two nagini functions therefore fuse into one modeled obligation, and
every nagini case carries over either as an attack on one clause of that single
obligation or is a principled omission recorded in the module ``assessment``.

A carrier difference that matters for the whole battery: nagini models a
converter step as an OPAQUE callee (``step`` with ``Ensures(True)``), so its
reject arguments turn on "a raw value is not PROVABLY the fold over a non-empty
chain". Here a converter chain is modeled TRANSPARENTLY as ``List (Int → Int)``
and the fold (``applyChain``/``convertRow``) is a plain computation, so a rival's
violation is not merely unprovable-equal — it is DECIDABLY unequal at a concrete
converter (e.g. ``(· + 1000)``). Every reject witness below is fully
``decide``-able; no carrier term blocks refutation, so the conditioning-on-an-
opaque-term machinery is unnecessary here.

DEFENDED SURFACE (one modeled behavior). ``insertReturnedRows`` pins ``result``
to a single grounded computation over the inputs, with these independent
top-level clauses selected by the input:

  * (E)  no returning fields ⇒ ``result = []`` (empty-fields clause);
  * (S)  otherwise ``result`` is drawn from the pathway the two capability flags
         select — ``batchRows`` when ``canBatch``; else ``[columnsRow]`` when
         ``canColumns``; else ``[lastIdRow]`` (pathway-selection clause);
  * (C)  if some field declares a converter (``anyConverter``), each cell of each
         selected row is passed through its field's converter chain
         (``result = selected.map (convertRow returningFields)``) — the CHANGED
         clause, the fix;
  * (Cn) if no field declares a converter, the selected rows are handed back
         untouched (``result = selected``).

The BEHAVIOURAL DISCRIMINATOR (the fix): the fetched rows of a creating write are
run through the returning fields' converter chains, exactly as read values are,
instead of being handed back raw. The pre-patch returned the raw rows; the
raw-passthrough rivals below ARE that pre-patch behavior, and they diverge
decidably from the spec at any non-identity converter. Clause (C) pins the fold
element-wise, so the per-cell / per-column near-misses (convert only the first
cell; drop the head converter of the chain) are refutable too.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. Nagini's note that the frame-mutation
    class does NOT apply to this bundle (its ``PSeq`` inputs are immutable) holds
    a fortiori here; no substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — NOTHING TO SHIP, and the reason matters.
    ``implementation_insertReturnedRows`` is a total Lean ``def`` elaborated
    without ``partial``, so its termination is checked and no diverging rival is
    admissible here. The known partial-semantics spec hole (a non-terminating
    impl verifying vacuously) is a VELVET-side issue under
    ``set_option loom.semantics.termination "partial"``, already measured and
    recorded in ``the corpus-wide termination-semantics finding``; it is cited, not re-reported,
    and it does not describe this bundle. (The nagini sibling carries no
    ``diverge-*`` case either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (``selected`` and the
    ``convertRow`` fold over the actual chains). There is no opaque answer key an
    implementation could echo — matching nagini's own note that the only "echo"
    of the raw value IS the pre-patch, which correctly fails clause (C). In its
    place the battery carries honest cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery. Rivals
    correct on part of the domain but diverging where the fix bites: raw
    passthrough (skip the whole fold); convert only the first row; convert only
    the first cell of each row; drop the head converter of each chain; a wrong
    pathway selection; a wrong row count; and the unchanged-but-load-bearing
    empty-fields clause.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it by ``decide``. Each was checked to HOLD of its
rival and to FAIL on the frozen solution, so it discriminates rather than
asserting a tautology. Because the carrier computes, every witness uses a
concrete non-identity converter and closes by ``decide``; the hypotheses are
empty, so ``witness-inconsistent`` cannot arise.

AUDIT (independent, post-port). Every reject witness was rebuilt by hand against
the rival and against the frozen solution: all elaborate on the rival (exit 0)
and all fail on gold (exit 1), and each gold-side failure is the SEMANTIC form
``Tactic `decide` proved that the proposition … is false`` — a refutation of the
concrete claim, not a missing identifier, type error, or unfolding failure. So
no witness passes for a syntactic reason. Every value asserted in a ``rationale``
below was additionally re-derived by ``decide`` against the frozen spec
(``problem_spec_… … <claimed result>``), so the prose matches the carrier.

One defect was found and repaired: a positive control whose "different shape"
was DEFINITIONALLY EQUAL to the frozen impl (see the audit note on
``pos-control-zipwith-convert``, which replaced it). Positives are now checked
against that failure mode: each is required either to be non-defeq to the frozen
impl (probed by appending ``example : ∀ …, impl_alt … = implementation_… := by
rfl`` and requiring it to FAIL) or to carry a distinct load-bearing role.
``pos-control-selected-let`` is non-defeq and PASSES that probe (exit 1, "is not
definitionally equal to"), so it is load-bearing as written.

SPEC PROBES (attacks D and E) found no hole. Three further wrong impls not in the
battery — reversing the ``canBatch``/``canColumns`` precedence, dropping the
``anyConverter`` guard so empty chains still map, and folding the chain
right-to-left — were each REJECTED by the frozen spec, and each is refuted by a
``decide`` witness that fails on gold; the fold-direction one was strong enough
to keep and is now the ``weak-chain-foldr-wrong-order`` case. Three further
CORRECT reshapes were proven against the frozen spec, so it is not too strong:
a non-monadic pure ``if``-expression, a ``match`` on the flag pair, and a
``reverse``/``map``/``reverse`` round-trip (the last two non-defeq, so each
genuinely re-proves).

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
predicate rather than fixing them at one convenient point:
``returningFields`` ranges over ``[]`` (empty-fields clause), one field with a
one-converter chain, one field with a TWO-converter chain, and two fields (one
empty + one wrapping) — so both the field-count and the chain-length binders
vary; ``canBatch`` takes both settings (the batch pathway feeds the multi-row
witnesses; the last-id pathway feeds the single-row ones); ``canColumns`` takes
both settings and is the sole discriminator of one rival; ``batchRows`` carries a
two-row batch where the row-count and first-row rivals bite; ``columnsRow`` is the
value the wrong-pathway rival drops; and ``lastIdRow`` carries the raw cell(s) the
passthrough / per-cell rivals fail to convert. No two rivals share a refutation
point unless they fail there for the same reason.

The variation is MEANINGFUL, not two spellings of one point: the two-converter
chains are the only inputs on which chain EXTENT and chain ORDER are separable
(at length <= 1 the drop-head and foldr rivals are correct), and the audit
confirmed the converter pool is non-commuting where it needs to be —
``[(·*2), (·+1)]`` folds to 11 left-to-right and 12 right-to-left, so the
order-attacking witness is not merely a re-spelling of the extent-attacking one.
Two witnesses deliberately use an EMPTY chain (``anyConverter`` false, clause
(Cn)), which isolates the pathway-selection and row-count divergences from the
fold entirely — machine-confirmed: ``anyConverter [⟨[]⟩] = false`` by ``decide``.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` callee — the converter application is modeled deeply — so G-AX skips.
The nagini ``AXIOM_TESTS`` belong to G-AX and are dropped from this gate.
"""
from pathlib import Path

INSTANCE = "django__django-14007"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The WHOLE frozen impl def (entirely inside the -- impl-start / -- impl-end
# region). Rivals and positive controls replace it wholesale; same_spec is
# preserved because the swap lies strictly inside the impl region.
_IMPL = (
    "def implementation_insertReturnedRows\n"
    "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
    "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
    "  if returningFields.isEmpty then\n"
    "    return []\n"
    "  let mut rows : List Row := []\n"
    "  if canBatch then\n"
    "    rows := batchRows\n"
    "  else if canColumns then\n"
    "    rows := [columnsRow]\n"
    "  else\n"
    "    rows := [lastIdRow]\n"
    "  if anyConverter returningFields then\n"
    "    rows := rows.map (convertRow returningFields)\n"
    "  return rows"
)

# The first two lines of the frozen proof body (intro + unfold), unique in the
# file. The admissibility case inserts a ground `have` AFTER these lines, leaving
# the rest of the frozen tactic script — and the theorem STATEMENT — untouched.
_PROOF_HEAD = (
    "  intro returningFields canBatch canColumns batchRows columnsRow lastIdRow\n"
    "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows"
)

# The WHOLE frozen tactic body (everything inside -- proof-start / -- proof-end
# after the `theorem correct_… := by` line). A positive control whose reshaped
# impl is NOT definitionally equal to the frozen one must re-prove, which means
# replacing this body; the theorem STATEMENT is untouched, so `variant_scope`'s
# obligation-preserved rule still holds (only the tactic body may differ).
_PROOF_BODY = (
    "  intro returningFields canBatch canColumns batchRows columnsRow lastIdRow\n"
    "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
    "  by_cases he : returningFields.isEmpty\n"
    "  · simp only [he, Id.run, if_true]; rfl\n"
    "  · by_cases hb : canBatch <;> by_cases hc : canColumns <;>\n"
    "      by_cases ha : anyConverter returningFields <;>\n"
    "      simp only [he, hb, hc, ha, Id.run, if_true] <;> rfl"
)


def _impl(body: str) -> str:
    return _swap(_BASE, _IMPL, body)


def _impl_proof(body: str, proof: str) -> str:
    """Swap the impl region AND re-prove. Both swaps lie strictly inside the
    impl / proof regions, so `same_spec` holds and the `theorem` statement stays
    byte-identical."""
    return _swap(_swap(_BASE, _IMPL, body), _PROOF_BODY, proof)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify with the frozen proof body unchanged
    # (the frozen `by_cases … <;> … <;> rfl` closes both reshapes after the
    # extra locals zeta-reduce). If a faithful correct implementation cannot
    # satisfy the frozen obligation the spec is SPEC-TOO-STRONG. No helper
    # lemma, axiom, or assumption token is introduced.
    #
    # Ports nagini pos-control-apply-row-reshape + pos-control-exec-reshape
    # (both "structurally reshape a correct impl and keep the obligation")
    # onto the single fused modeled function.
    # =====================================================================
    {
        "id": "pos-control-selected-let",
        "kind": "soundness",
        "expect": "verify",
        # Bind the pathway-selected rows to a single `let` (mirroring the spec's
        # own `selected`) instead of a mutable `if`-chain. Same value flow, so
        # `result = …` holds on every input; the frozen proof closes.
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let sel : List Row :=\n"
            "    if canBatch then batchRows else if canColumns then [columnsRow] else [lastIdRow]\n"
            "  let mut rows : List Row := sel\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (convertRow returningFields)\n"
            "  return rows"
        ),
        "rationale": "the pathway-selection clause (S) is reshaped by binding the "
                     "selected rows to a single `let` (as the spec's `selected` "
                     "is) rather than a mutable `if`-chain; the assembled value is "
                     "identical on every input, so `result = …` still holds. Must "
                     "verify, else the pathway/convert obligation is "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body is retained "
                     "(the `let` zeta-reduces under the frozen `by_cases … <;> "
                     "rfl`). Ports nagini's apply_row/exec structural-reshape "
                     "positives to the fused site.",
    },
    {
        "id": "pos-control-zipwith-convert",
        "kind": "soundness",
        "expect": "verify",
        # Compute the per-cell conversion with `List.zipWith` instead of the
        # spec's `zip`-then-`map` (`convertRow`). Extensionally identical, but
        # NOT definitionally equal: `rfl` alone does not identify the two, so
        # this positive forces a real re-proof (the `hz` bridging induction)
        # rather than riding on the frozen script.
        #
        # AUDIT NOTE. This case replaces an earlier `pos-control-early-return-
        # convert`, which returned the mapped rows directly from the
        # `anyConverter` branch instead of assigning and falling through. That
        # reshape was measured DEFINITIONALLY EQUAL to the frozen impl — an
        # appended `example : ∀ …, impl_alt … = implementation_insertReturnedRows …
        # := by rfl` elaborated (exit 0) — so `Id.run`'s do-block elaboration
        # collapses the early `return` to the very same term. It verified
        # honestly and tested nothing: no obligation was re-discharged, because
        # there was no distinction for the spec to see. The `zipWith` reshape
        # below is the same "clause (C) is reshaped" intent made load-bearing;
        # the identical `rfl` defeq probe FAILS on it ("is not definitionally
        # equal to", exit 1), so the frozen tactic script genuinely does not
        # close it and the proof below has to do work.
        "module": _impl_proof(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (fun row =>\n"
            "      List.zipWith (fun f c => applyChain f.converters c) returningFields row)\n"
            "  return rows",
            # Re-proves: bridge `zipWith` to the spec's `zip`-then-`map` by
            # induction on the field list, then take the frozen case-split.
            # No helper lemma, axiom, `sorry`, or new theorem is introduced —
            # the bridge is a `have` inside the existing tactic body.
            "  intro returningFields canBatch canColumns batchRows columnsRow lastIdRow\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  have hz : ∀ (row : Row), List.zipWith (fun f c => applyChain f.converters c)\n"
            "      returningFields row = convertRow returningFields row := by\n"
            "    intro row\n"
            "    unfold convertRow\n"
            "    induction returningFields generalizing row with\n"
            "    | nil => simp\n"
            "    | cons f fs ih => cases row with\n"
            "      | nil => simp\n"
            "      | cons c cs => simp [ih]\n"
            "  by_cases he : returningFields.isEmpty <;>\n"
            "    by_cases hb : canBatch <;> by_cases hc : canColumns <;>\n"
            "    by_cases ha : anyConverter returningFields <;>\n"
            "    simp [he, hb, hc, ha, Id.run, hz] <;> rfl"
        ),
        "rationale": "the converter clause (C) is reshaped to compute each row's "
                     "conversion with `List.zipWith` over the fields and cells "
                     "instead of the spec's `zip`-then-`map` (`convertRow`). The "
                     "two agree on every input — pointwise on each cell, and both "
                     "truncate at the shorter of fields/row — so `result = …` "
                     "still holds; but they are NOT definitionally equal, so the "
                     "frozen `rfl` script does NOT close it and the case re-proves "
                     "(a `have hz` induction bridging `zipWith` to "
                     "`zip`-then-`map`, then the frozen case-split). Must verify, "
                     "else clause (C) is SPEC-TOO-STRONG: it would be pinning the "
                     "fold's SPELLING rather than its per-cell VALUE. This is the "
                     "load-bearing counterpart to the first positive, which "
                     "reshapes clause (S)'s pathway selection.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so the `∀` is unguarded), so nagini's
    # precondition-admission probe (admiss-self-call) has no precondition binder
    # to attack here; the honest analogue is to discharge the spec predicate by
    # evaluation at the F2P-shaped input (one returning field with a single
    # wrapping converter, over the columns pathway) alongside the frozen
    # obligation. Ports nagini admiss-self-call.
    # =====================================================================
    {
        "id": "admiss-ground-f2p-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped input (one field whose chain
        # is a single wrapping converter, one returned cell, columns pathway) by
        # `decide` inside a `have`, then close the frozen obligation verbatim.
        # Nothing is assumed: no new declaration, statement byte-identical, the
        # ground instance is a `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _PROOF_HEAD,
            _PROOF_HEAD + "\n"
            "  have _ground : problem_spec_insertReturnedRows [⟨[(· + 1000)]⟩] false true [] [7] []\n"
            "      (implementation_insertReturnedRows [⟨[(· + 1000)]⟩] false true [] [7] []) := by\n"
            "    unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "    decide",
        ),
        "rationale": "the obligation is discharged at the F2P-shaped input (a "
                     "single returning field whose converter chain is one "
                     "wrapping converter, one raw returned cell, the "
                     "single-row columns pathway) by `decide`, then the frozen "
                     "obligation is closed verbatim. Verifies, else the modeled "
                     "behavior is unsatisfiable at exactly the input the F2P "
                     "exercises (the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: the ground instance is a `have` inserted after the "
                     "frozen intro/unfold, and the theorem statement is "
                     "byte-identical. Ports nagini's self-call admissibility "
                     "probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, and (b) a
    # `decide` witness pinning the violation at one concrete input, checked to
    # hold of the rival and fail on gold.
    # =====================================================================

    # ---- THE bug-delta: raw passthrough (nagini weak-exec-raw-passthrough /
    #      weak-row-raw-passthrough — the two nagini passthrough rivals fuse
    #      here, since row-level and driver-level passthrough are the same skip
    #      of the single fold). ----
    {
        "id": "weak-raw-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behavior: return the selected raw rows, never applying the
        # converter chains (drop the `anyConverter` map entirely).
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  return rows"
        ),
        "refinement": "this is the pre-patch behavior: each backend pathway "
                      "returns its raw fetched rows immediately, never running "
                      "them through the returning fields' converter chains. The "
                      "F2P test creates an object whose primary-key field wraps "
                      "the raw integer via a read-time hook and asserts the "
                      "created id is that wrapper; raw passthrough leaves a plain "
                      "integer, so the faithful real patch (no converter "
                      "application) does NOT resolve the F2P.",
        "rationale": "REJECT from the converter clause (C): with one field whose "
                     "chain is a single wrapping converter, the spec pins "
                     "`result = selected.map (convertRow …)` = [[1005]] while the "
                     "rival returns the raw [[5]]. Binder spread: last-id pathway "
                     "(canBatch=canColumns=false), one field, one-converter chain.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[(· + 1000)]⟩] false false [] [] [5]\n"
            "    (implementation_insertReturnedRows [⟨[(· + 1000)]⟩] false false [] [] [5]) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- convert only the FIRST row (nagini weak-row-first-col-only, ported to
    #      the fused function's ROW axis: correct for a single-row pathway, wrong
    #      for a multi-row batch). ----
    {
        "id": "weak-convert-first-row-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the converter chains to the first selected row only; emit the rest
        # raw. Correct for any single-row pathway (the issue's create case) but
        # wrong for a multi-row batch whose later rows carry a wrapping converter.
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := match rows with\n"
            "            | r :: rest => convertRow returningFields r :: rest\n"
            "            | [] => []\n"
            "  return rows"
        ),
        "refinement": "this converts only the first returned row and leaves the "
                      "rest raw. A batch-returning write (multiple created "
                      "objects) assigns one converted row per object; leaving the "
                      "trailing rows raw keeps a converter-bearing field a plain "
                      "integer instead of the wrapper on every object past the "
                      "first, so the converted-vs-raw assertion fails on those "
                      "rows and the faithful real patch does NOT resolve such a "
                      "case.",
        "rationale": "REJECT from clause (C): over a two-row batch with a wrapping "
                     "converter the spec maps `convertRow` over BOTH rows "
                     "([[1001],[1002]]) while the rival converts only the first "
                     "([[1001],[2]]). Binder spread: batch pathway "
                     "(canBatch=true), two-row `batchRows`.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[(· + 1000)]⟩] true false [[1],[2]] [] []\n"
            "    (implementation_insertReturnedRows [⟨[(· + 1000)]⟩] true false [[1],[2]] [] []) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- convert only the FIRST cell/column of each row (nagini
    #      weak-row-first-col-only, ported to the fused function's COLUMN axis:
    #      correct where only column 0 bears a converter, wrong for a later
    #      converter-bearing column). ----
    {
        "id": "weak-convert-first-cell-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Convert only the first cell of each row against the first field's chain;
        # leave the remaining cells raw. Correct for a single-column returning set
        # but wrong when a non-first column carries a wrapping converter.
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (fun row =>\n"
            "      match returningFields, row with\n"
            "      | f :: _, c :: cs => applyChain f.converters c :: cs\n"
            "      | _, _ => row)\n"
            "  return rows"
        ),
        "refinement": "this converts only the first cell of each row and leaves "
                      "every later column raw. A multi-field returning set whose "
                      "converter-bearing field is not the first (e.g. a "
                      "from_db_value hook on a second returned column) would keep "
                      "that column a plain integer instead of the wrapper, so the "
                      "assertion on that column fails; the faithful real patch "
                      "(applying the chain only to column 0) does NOT resolve. The "
                      "real converter application folds EVERY converter-bearing "
                      "column.",
        "rationale": "REJECT from clause (C), the per-CELL structure of the fold: "
                     "with an empty first field and a wrapping second field over a "
                     "two-cell row the spec converts the second cell "
                     "([[3,1004]]) while the rival converts only the first "
                     "([[3,4]]). Binder spread: two returning fields (moves the "
                     "field-count binder), last-id pathway, two-cell `lastIdRow`.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[]⟩, ⟨[(· + 1000)]⟩] false false [] [] [3, 4]\n"
            "    (implementation_insertReturnedRows [⟨[]⟩, ⟨[(· + 1000)]⟩] false false [] [] [3, 4]) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- drop the HEAD converter of each field's chain (nagini
    #      weak-row-drop-head-converter). Under-applies the chain. To keep this a
    #      NEAR-MISS distinct from raw passthrough, the witness uses a TWO-
    #      converter chain, where drop-head is neither the full fold nor raw. ----
    {
        "id": "weak-drop-head-converter",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the fold over each field's chain with its FIRST converter dropped.
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (fun row =>\n"
            "      (returningFields.zip row).map (fun fc => applyChain (fc.1.converters.drop 1) fc.2))\n"
            "  return rows"
        ),
        "refinement": "this skips the first converter of each field's chain. A "
                      "field's converter chain is the backend converters followed "
                      "by the field converters; dropping the head applies a "
                      "truncated (wrong) conversion — for a single-converter field "
                      "it degrades to raw, and for a longer chain it produces the "
                      "wrong wrapped value. The F2P (and any read-parity check) "
                      "asserts the value produced by the FULL chain, so the "
                      "faithful real patch does NOT resolve.",
        "rationale": "REJECT from clause (C), the per-cell fold VALUE: with a "
                     "two-converter chain [(·+1000),(·+1)] the spec folds both "
                     "(5 ↦ 1006) while the rival drops the head and folds only the "
                     "second (5 ↦ 6). A distinct point from the raw-passthrough "
                     "rival — a TWO-converter chain, where drop-head differs from "
                     "both raw and the full fold. Binder spread: chain-length ≥ 2.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[(· + 1000), (· + 1)]⟩] false false [] [] [5]\n"
            "    (implementation_insertReturnedRows [⟨[(· + 1000), (· + 1)]⟩] false false [] [] [5]) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- fold the chain in the WRONG ORDER (added by audit). The existing
    #      drop-head rival attacks the chain's EXTENT (which converters run); no
    #      rival attacked its ORDER (the direction they run in). A chain is the
    #      backend converters followed by the field converters and is applied
    #      left-to-right, so order is load-bearing for any non-commuting pair.
    #      Distinct from drop-head: this rival runs EVERY converter in the chain. ----
    {
        "id": "weak-chain-foldr-wrong-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Fold each field's chain RIGHT-to-left instead of left-to-right. Applies
        # exactly the same converters, the same number of times — only the order
        # differs, so it is correct for a chain of length <= 1 and for any chain of
        # mutually commuting converters, and wrong otherwise.
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (fun row =>\n"
            "      (returningFields.zip row).map (fun fc =>\n"
            "        fc.1.converters.foldr (fun f v => f v) fc.2))\n"
            "  return rows",
        ),
        "refinement": "this runs a field's converter chain in the reverse order. "
                      "A chain is ordered — the backend's own value converters run "
                      "first and the field-declared ones after — so for any pair "
                      "that does not commute (the common case: a converter that "
                      "wraps a raw scalar in an object cannot meaningfully be "
                      "applied after one that rescales it) reversing the order "
                      "yields a different value, and one of the two orders feeds a "
                      "converter an input of a shape it was never meant to see. "
                      "A read-parity check asserts the value produced by the chain "
                      "in declaration order, so the faithful real patch does NOT "
                      "resolve.",
        "rationale": "REJECT from clause (C), the fold's DIRECTION (a point the "
                     "extent-attacking drop-head rival leaves open, since this "
                     "rival applies every converter in the chain): with the "
                     "non-commuting chain [(·*2), (·+1)] the spec folds "
                     "left-to-right (5 ↦ 10 ↦ 11) while the rival folds "
                     "right-to-left (5 ↦ 6 ↦ 12). Binder spread: chain-length 2 "
                     "with a MULTIPLICATIVE head, so the divergence is the order "
                     "alone — both orders apply both converters, unlike drop-head "
                     "which applies fewer.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[(· * 2), (· + 1)]⟩] false false [] [] [5]\n"
            "    (implementation_insertReturnedRows [⟨[(· * 2), (· + 1)]⟩] false false [] [] [5]) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- wrong pathway selection (no direct nagini counterpart: nagini's grounded
    #      rows enter pre-selected, so the pathway choice is not a nagini clause;
    #      it is a genuine clause of THIS fused spec (S) and must be attacked to
    #      keep the canColumns binder varied and every top-level clause covered). ----
    {
        "id": "weak-wrong-pathway-ignore-columns",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the columns pathway: fall through to the last-id row even when
        # canColumns holds. Correct whenever canColumns is false; wrong when it
        # holds and the columns row differs from the last-id row.
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (convertRow returningFields)\n"
            "  return rows"
        ),
        "refinement": "this drops the single-row columns pathway and always falls "
                      "back to the last-inserted-id row when the batch pathway is "
                      "unavailable. On a backend that can return columns for a "
                      "single-row write, the created object's returned values come "
                      "from that columns row — the last-id fallback yields only "
                      "the pk cell and loses the other returned columns, so the "
                      "faithful real patch (wrong pathway) does NOT resolve.",
        "rationale": "REJECT from the pathway-selection clause (S): with "
                     "canColumns=true the spec selects `[columnsRow]` = [[7]] "
                     "while the rival selects `[lastIdRow]` = [[9]]. This rival is "
                     "the ONLY one moving the canColumns binder to true, so that "
                     "input is demonstrated live. Uses an empty converter chain so "
                     "the divergence is purely the selection, not the fold.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[]⟩] false true [] [7] [9]\n"
            "    (implementation_insertReturnedRows [⟨[]⟩] false true [] [7] [9]) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- drop the last returned row (nagini weak-exec-drop-last-row): correct
    #      per-cell fold, wrong row COUNT. ----
    {
        "id": "weak-drop-last-row",
        "kind": "uniqueness",
        "expect": "reject",
        # Convert every row correctly but emit one fewer (drop the last).
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return []\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (convertRow returningFields)\n"
            "  return rows.dropLast"
        ),
        "refinement": "this returns one fewer row than it received (drops the "
                      "last). A batch-returning create assigns one returned row "
                      "per input object; dropping the last row loses an object's "
                      "returned values, so a bulk-create check would see a missing "
                      "row and the faithful real patch does NOT resolve.",
        "rationale": "REJECT from the row-count implicit in clauses (S)/(C): the "
                     "spec returns `selected.map (convertRow …)`, whose length "
                     "equals the number of selected rows (2 here), while the rival "
                     "returns one fewer. Uses an empty converter chain so the "
                     "divergence is purely the count. Binder spread: batch "
                     "pathway, two-row `batchRows` (distinct from the "
                     "first-row-only rival, which fails on the per-row VALUE, not "
                     "the count).",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [⟨[]⟩] true false [[1],[2]] [] []\n"
            "    (implementation_insertReturnedRows [⟨[]⟩] true false [[1],[2]] [] []) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },

    # ---- the empty-fields no-op clause (unchanged but load-bearing). No direct
    #      nagini counterpart (nagini's spec has no empty-fields early return);
    #      it is a genuine top-level clause (E) of THIS spec and must be attacked. ----
    {
        "id": "weak-empty-fields-nonempty",
        "kind": "uniqueness",
        "expect": "reject",
        # When no fields are returned, emit a non-empty result instead of [].
        "module": _impl(
            "def implementation_insertReturnedRows\n"
            "    (returningFields : List RetField) (canBatch canColumns : Bool)\n"
            "    (batchRows : List Row) (columnsRow lastIdRow : Row) : List Row := Id.run do\n"
            "  if returningFields.isEmpty then\n"
            "    return [lastIdRow]\n"
            "  let mut rows : List Row := []\n"
            "  if canBatch then\n"
            "    rows := batchRows\n"
            "  else if canColumns then\n"
            "    rows := [columnsRow]\n"
            "  else\n"
            "    rows := [lastIdRow]\n"
            "  if anyConverter returningFields then\n"
            "    rows := rows.map (convertRow returningFields)\n"
            "  return rows"
        ),
        "refinement": "this returns a row when no fields are being returned, "
                      "instead of the empty result. A creating write with no "
                      "returning fields must hand back nothing; fabricating a row "
                      "would inject a spurious returned value into the caller (the "
                      "created-object machinery would try to assign a nonexistent "
                      "returned column), so the faithful real patch does NOT "
                      "resolve.",
        "rationale": "REJECT from the empty-fields clause (E): with "
                     "`returningFields = []` the spec pins `result = []` while the "
                     "rival returns `[lastIdRow]`. Fully concrete, decidable. The "
                     "only rival moving the returningFields binder to the empty "
                     "list — so that clause is demonstrated live rather than held "
                     "at a non-empty value by every other witness.",
        "witness": (
            "example : ¬ problem_spec_insertReturnedRows [] false false [] [] [5]\n"
            "    (implementation_insertReturnedRows [] false false [] [] [5]) := by\n"
            "  unfold problem_spec_insertReturnedRows implementation_insertReturnedRows\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# callee (the converter application is modeled deeply), so G-AX skips. The
# nagini AXIOM_TESTS belong to G-AX and are dropped from this gate.
AXIOM_TESTS = []
