"""properties.py — G-PBT falsification battery for pydata__xarray-4094 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text strictly inside ``-- impl-start``/``-- impl-end`` and — for a
case that legitimately re-proves — inside ``-- proof-start``/``-- proof-end`` is
changed, so ``markers.same_spec`` holds by construction and the single
``theorem correct_toUnstackedDataset`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff the variant is
in scope AND it does NOT verify AND the case's refutation ``witness`` HOLDS of
the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier — the nagini manifest
is the design document, not a text to translate. The nagini bundle models the
reconstruction over a heap-allocated ``List[int]`` carrier with FRACTIONAL
PERMISSIONS and an abstract capability-token postcondition granted only by a
contracted recombination callee; this Lean bundle models the SAME functional core
— walk the list of variable labels, extract each label's slice in the
label-removing mode, and assemble the in-order list of (label, slice) entries —
over an immutable ``List (κ × ν)`` carrier with the extraction step left
UNIVERSALLY QUANTIFIED. Several nagini classes therefore have no counterpart
here; each such omission is named in the ADVERSARIAL READ section below, with the
demonstrated reason it does not port, never silently dropped.

AUDIT CORRECTION. Earlier revisions of this docstring referred the reader to an
``assessment`` section for those omission reasons. No such section, key, or
object ever existed in this file or in ``meta.json`` — the reasons were in the
ADVERSARIAL READ prose all along, so every ``see assessment`` pointed at nothing
and the omission argument read as documented-elsewhere when it was not. All five
references are now retargeted to the section that actually carries the argument.
The same audit found ONE nagini case genuinely absent rather than argued:
``atk-fabricate-allequal-resid``, which was not mentioned anywhere in this
manifest. It is expressible on this carrier and has been ADDED below as
``atk-fabricate-allequal``, so the porting map is now complete: all 12 nagini
SPEC_TESTS ids are either ported or named with a reason. (nagini's two
``AXIOM_TESTS`` are G-AX's lane and are correctly out of scope for this gate.)

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_toUnstackedDataset extractSlice vars result`` pins EXACTLY one
top-level equation, with no conjunction to decompose:

    result = vars.map (fun k => (k, extractSlice true k))

That single clause is simultaneously load-bearing in FOUR independent ways, and
each is attacked by its own rival below:

  * (D1 mode)      every entry's slice is the one produced by the extraction
    invoked with the label-removing mode (``extractSlice true k``), never the
    label-retaining one (``extractSlice false k``);
  * (D2 argument)  the extraction for an entry is invoked on THAT entry's own
    label, not on some other label drawn from the list;
  * (D3 pairing)   the label recorded beside a slice is the label that slice was
    extracted for;
  * (D4 structure) the result lists exactly the labels — one entry per label,
    all of them, in the order the labels are listed. This covers cardinality
    (nothing dropped, nothing invented) and order.

BINDER STRUCTURE. The spec predicate has exactly TWO input binders:
``extractSlice : Bool → κ → ν`` (the per-label extraction step, whose ``Bool``
is the extraction mode) and ``vars : List κ`` (the labels). Both are load-bearing
and BOTH are varied across the reject witnesses: the eight witnesses instantiate
eight ``(extractSlice, vars)`` pairs that are distinct AS EVALUATED, with ``vars``
ranging over lengths 1, 2 and 3 and over seven label sets, and ``extractSlice``
ranging over two mode-sensitive functions (which separate the two modes by
different offsets) and five mode-insensitive ones (which isolate the
argument/pairing/structure failures from the mode failure). Holding either binder
fixed would leave a whole family of rivals undetected: a mode-insensitive
``extractSlice`` cannot witness D1 at all, and a single-label ``vars`` cannot
witness D2, D3 or the order half of D4.

"Distinct as evaluated" is the load-bearing qualifier, and it is what an earlier
revision got wrong. The spec applies ``extractSlice`` at ``true`` and nowhere
else, so what a witness can observe is the step's ``true`` branch alone; two
steps differing only in their ``false`` branch are ONE point, however different
their source text. See the POINT SPREAD note at the foot of this file for the
measurement that corrected it. A mode-sensitive step buys a genuinely new point
only for the rivals that themselves invoke the ``false`` branch.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION (nagini ``frame-mutate-data``,
    ``frame-mutate-resid``) — VACUOUS here. Those two rivals are rejected by
    Viper for holding only half of a heap predicate while index-assigning into a
    read-only input. Lean is referentially transparent: ``vars`` and
    ``extractSlice`` are immutable values, there is no aliasing, no fractional
    permission, and no read-only cell an implementation could overwrite. Per the
    porting map no substitute probe is fabricated. Directive-5 frame discipline
    is instead already discharged by the spec itself: the single equation pins
    the result TOTALLY (every entry, its order, its label and its slice), so
    there is no unconstrained output component for a rival to fill freely —
    which is what the frame obligation becomes on this carrier.

  * CAPABILITY-TOKEN BYPASS / LAUNDERING (nagini ``atk-bypass-assemble``,
    ``atk-launder-fresh-copy``) — NOT EXPRESSIBLE, and the reason is
    informative rather than incidental. Nagini's decisive clause is an abstract
    contract-only predicate that only its contracted recombination step grants,
    to discriminate a difference that is invisible in the VALUES (the pre-fix
    failure there is "raises rather than returns", so the per-entry values agree
    either way). This bundle does not model the recombination step at all — the
    modeled surface ends at the assembled list of entries — so there is no token
    to bypass, and on a referentially transparent carrier a value-equal rebuild
    of the assembled list IS the same list, so the LAUNDER rival is not wrong
    here. Rather than drop that case, it is carried over INVERTED, as the
    ``pos-rebuild-elementwise`` positive: the case that nagini needs the token to
    reject is one this carrier must ACCEPT, and shipping it as a positive is what
    records that difference honestly. See the ``pos-rebuild-elementwise`` case.

  * DIVERGENCE / NON-TERMINATION — GENUINELY VACUOUS on this carrier, and now
    MEASURED rather than asserted. This bundle is plain Lean 4 with no
    ``set_option loom.semantics.termination`` line at all (that option is a
    Velvet construct; the 500 velvet Solutions carry one, the lean ones carry
    none), so neither the "total" nor the "partial" disposition applies as
    written — there is no termination obligation to discharge and no partial
    mode to verify vacuously. Instead the CARRIER refuses the case at
    elaboration: a diverging impl is not expressible as an admissible variant.
    Both routes were tried as real builds by the audit:
      - a self-recursive plain ``def`` fails with ``fail to show termination
        for implementation_toUnstackedDataset / failed to infer structural
        recursion``, i.e. Lean's own totality checker rejects the FILE, so the
        variant never reaches the obligation;
      - marking it ``partial`` makes the impl opaque, and the frozen obligation
        then fails with ``Tactic `unfold` failed to unfold
        `implementation_toUnstackedDataset```. That is a rejection, but a
        rejection no witness can attribute to the spec: the same ``unfold``
        failure blocks the witness too (rival build exit 1), because a
        ``partial def`` has no equation to reduce. So it cannot be shipped as a
        reject case even though the verifier says no.
    "Vacuous" is therefore the right word for a reason stronger than
    totality-by-construction: the class has no admissible, witnessable member.
    (The nagini sibling carries no such case either.)

  * MODE / PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole battery
    lives. ``atk-retaining-mode`` is the pre-fix behavior itself (D1);
    ``atk-first-label-only-removing`` is its NEAR-MISS, agreeing with the frozen
    behavior on the first label and diverging on every later one, so it gets its
    own witness at a strictly larger input rather than sharing one;
    ``atk-extract-wrong-label`` (D2), ``atk-pair-wrong-label`` (D3),
    ``atk-drop-last-entry``, ``atk-empty-collection`` and
    ``atk-reversed-order`` (D4) round out the surface, and
    ``atk-fabricate-allequal`` attacks all three of D2/D3/D4 jointly with a
    self-consistent degenerate collection that none of them alone catches.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, as it is in nagini for the same reason
    stated differently. The postcondition is GROUNDED: the result is pinned by a
    structural equation over the two inputs, with the extraction step
    universally quantified rather than axiomatized, so there is no opaque
    answer-key an implementation could echo instead of doing the work. Its place
    is taken by the honest positive controls, which must verify.

  * AXIOM LANE — DROPPED. ``meta.json`` records ``axioms: []`` (the extraction
    step is universally quantified, so the proof consumes no callee property);
    the nagini ``AXIOM_TESTS`` belong to G-AX and this gate ignores them.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof's ``rw [show … from rfl]`` is
tuned to the frozen loop's syntactic form, so a merely RESHAPED but CORRECT impl
fails to build exactly as loudly as a wrong one (all four positive controls below
had to re-prove or be shape-preserving for precisely this reason). A rejection
alone therefore attributes nothing to the spec. Every ``expect="reject"`` case
accordingly carries a Lean snippet that instantiates the spec predicate at one
CONCRETE input — a small ``Nat`` label list and a closed-form extraction step —
and refutes it by ``decide``, which computes the rival's loop and the spec's
``List.map`` side by side. Because the carrier is fully transparent at such an
instance (no ``opaque`` term is involved), no witness needs to CONDITION on the
carrier: every witness head binds NOTHING, so there are no hypotheses whose
joint satisfiability could be in question and no ``witness-inconsistent`` risk.
Each witness was checked with two real ``lake env lean`` builds and was SEEN to
hold of its rival (exit 0) and to FAIL on the frozen solution (exit 1, the error
being ``decide`` proving the negated proposition false) — so each discriminates
rather than asserting a tautology.

AUDIT: THE GOLD-SIDE ERROR CARRIES INFORMATION ABOUT THE CLAIM. The above is
necessary but not sufficient — a gold-side exit 1 is evidence only if it would
CHANGE had the claim changed. An independent audit rebuilt all eight witnesses
plus a FORGERY of each: the same file with the leading ``¬`` dropped, i.e.
asserting that the frozen solution IS correct at that input. Every forgery
ELABORATES against the frozen solution (exit 0) while the real witness FAILS
there (exit 1), so gold's exit code tracks the claim rather than the file's shape,
and a forged witness could not have been recorded as a rejection. Each forgery
also fails against its RIVAL (exit 1), which is the same discrimination read in
the opposite direction. The gold-side signature is a plain evaluation in all
eight cases — ``Tactic `decide` proved that the proposition ¬(…) is false``, the
strongest available form, since the kernel actually computed both sides — so none
of the stuck-reduction classes (``witness-undecided``, missing ``Decidable``
instance, loop unification) is in play and no ``witness_reference`` is needed.

The admissibility positive was probed the same way, because a ground ``have``
closed by ``decide`` is exactly the kind of step that can pass while proving
nothing: replacing its claimed result with ``[]`` makes the file FAIL at the
``have`` (``decide`` proving ``[] = List.map … [0, 1]`` false), so that ``have``
is discharging a real equation and is not a no-op.

REFINEMENT. Each reject case's ``refinement`` argues why its faithful real
counterpart would NOT make the F2P test pass, so a rival that nevertheless
verified would be a true verify-does-not-imply-resolve break rather than an
artifact of the modeling. The F2P test asserts that the expansion is identical to
the original labelled collection it was built from (and repeats that assertion on
a single-sample slice), so any rival that changes which slice is stored under
which label, or which labels appear, or in what order, fails that identity check
— and the mode rivals fail it in the harsher way the report describes, by making
the recombination reject conflicting retained markers instead of returning.

AUDIT PROBES BEYOND THIS BATTERY (recorded so the next reader does not re-spend
the builds). An independent audit wrote NEW rivals and NEW correct reshapes that
this manifest does not contain, to look for a hole in the FROZEN spec in either
direction. No hole was found; the spec is exactly as strong as the equation reads.

  * WRONG impls that the spec must reject, and did (each also witnessed, rival
    exit 0 / gold exit 1): walk ``vars.tail`` (drops the FIRST entry, the mirror
    of ``atk-drop-last-entry``); emit each entry TWICE, so cardinality doubles
    while every entry is individually correct; select the extraction mode from
    ``vars.length != 1``, which is correct on every multi-label input and wrong
    only at a single label — the sharpest near-miss tried, and it is rejected.
  * A wrong impl that is NOT expressible and must not be mistaken for a gap:
    de-duplicating the label list (``vars.eraseDups``) needs ``BEq κ``, which the
    frozen signature's bare ``{κ : Type}`` does not provide, so the variant does
    not elaborate at all (``failed to synthesize BEq κ``). That is a typing limit
    of the carrier, not a rejection by the spec, so it is not shippable as a
    reject case; the polymorphic signature simply forecloses the rival.
  * CORRECT reshapes the spec must accept, and did — four, each re-proved inside
    the proof region with no new declaration: ``vars.map`` directly (closes by
    ``rfl``); a left fold with an accumulator lemma; ``vars.zip (vars.map …)``;
    and ``(vars.map (fun k => [entry])).flatten``. Together with the four shipped
    positives that is eight independent correct shapes accepted, which is the
    evidence that rejection here tracks wrongness rather than syntax.
  * A correct reshape whose proof the audit could NOT close, reported as UNCERTAIN
    rather than as a hole: accumulating front-to-back over ``vars.reverse``. The
    accumulator lemma goes through, but the residual goal is left as
    ``pure (pure (List.map …)) = List.map …`` — an ``Id``-monad ``pure``-stacking
    mismatch, not a disagreement about entries, order or labels. This looks like a
    tactic-plumbing gap in the audit's own proof rather than a spec defect (the
    impl is observably the frozen function), and it is recorded here as such
    instead of being claimed either way.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-4094"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it is meant to edit and
# is unique in the frozen file (both facts asserted by `_swap` at import time,
# so this manifest breaks loudly if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# --- impl region ---
# the accumulator declaration.
_I_MUT = "  let mut dataDict : List (κ × ν) := []\n"
# the loop header (which labels are walked).
_I_FOR = "  for k in vars do\n"
# the loop body: extract this label's slice in the label-removing mode and
# record the (label, slice) entry at the end of the accumulator.
_I_BODY = "    dataDict := dataDict ++ [(k, extractSlice true k)]\n"
# the return of the assembled collection.
_I_RET = "  return dataDict\n"
# the whole implementation definition (for the functional-shape positive).
_I_DEF = """def implementation_toUnstackedDataset {κ ν : Type}
    (extractSlice : Bool → κ → ν) (vars : List κ) :
    List (κ × ν) := Id.run do
  let mut dataDict : List (κ × ν) := []
  for k in vars do
    dataDict := dataDict ++ [(k, extractSlice true k)]
  return dataDict
"""

# --- proof region ---
# the opening line of the frozen tactic body (an anchor a positive can prepend a
# ground `have` to without touching the theorem STATEMENT or the spec view).
_P_OPEN = ("  unfold problem_spec_toUnstackedDataset "
           "implementation_toUnstackedDataset\n")
# the ENTIRE frozen tactic body after that opening line (for positives whose
# reshaped impl needs a genuinely different closing argument).
_P_TAIL = _BASE[_BASE.index(_P_OPEN) + len(_P_OPEN):_BASE.index("-- proof-end")]


# ---------------------------------------------------------------------------
# Witness scaffold. The spec predicate is instantiated at a concrete extraction
# step and a concrete label list, and refuted by `decide`: with `κ = ν = Nat`
# and a closed-form `extractSlice`, both the rival's `Id.run do` loop and the
# spec's `List.map` compute, so the two sides are decidably comparable and no
# hypothesis about the carrier is needed. Nothing is bound in the head, so the
# consistency probe has no assumptions to test.
# ---------------------------------------------------------------------------
def _w(extract, labels):
    return (
        "example : ¬ problem_spec_toUnstackedDataset\n"
        f"    ({extract}) ({labels} : List Nat)\n"
        "    (implementation_toUnstackedDataset\n"
        f"      ({extract}) ({labels} : List Nat)) := by\n"
        "  unfold problem_spec_toUnstackedDataset "
        "implementation_toUnstackedDataset\n"
        "  decide\n")


# Extraction steps used by the witnesses. The first three are MODE-SENSITIVE
# (they separate the label-removing from the label-retaining invocation, by two
# different offsets and by a collapse-to-constant shape) and are what makes a
# mode rival refutable; the last two are MODE-INSENSITIVE, which is what isolates
# an argument / pairing / structure failure from any mode failure.
_E_OFF1 = "fun (m : Bool) (k : Nat) => if m then k else k + 1"
_E_OFF100 = "fun (m : Bool) (k : Nat) => if m then k else k + 100"
_E_ID = "fun (_ : Bool) (k : Nat) => k"
_E_DOUBLE = "fun (_ : Bool) (k : Nat) => k * 2"
_E_SHIFT = "fun (_ : Bool) (k : Nat) => k + 10"
_E_TRIPLE = "fun (_ : Bool) (k : Nat) => k * 3"
_E_PLUS5 = "fun (_ : Bool) (k : Nat) => k + 5"

# AUDIT NOTE (mode-sensitivity is only meaningful where the spec READS the mode).
# An earlier revision of this manifest used a third "mode-sensitive" step here,
# `fun (m : Bool) (k : Nat) => if m then k else 0`, for `atk-reversed-order`, and
# claimed it probed "a carrier point no other witness probes". That claim was
# FALSE and is withdrawn. Every witness instantiates the spec, and the spec only
# ever applies the step at `true`, so a step's `false` branch is never evaluated
# by any witness: at `m = true` that step reduces to `_E_ID`, which
# `atk-extract-wrong-label` already uses — at the SAME label list `[1, 2]`. So
# two witnesses were two spellings of one carrier point, and the advisory
# `pts=7` was counting source text rather than distinct points. Measured, not
# argued: `example : List.map (fun k => (k, (…if m then k else 0…) true k)) [1,2]
# = List.map (fun k => (k, (fun _ k => k) true k)) [1,2] := by decide`
# elaborates (exit 0), and re-running the reversed-order witness with `_E_ID`
# substituted discriminates IDENTICALLY (rival exit 0, gold exit 1) — the
# collapse branch was inert. `atk-reversed-order` now witnesses at `_E_TRIPLE`
# and `[8, 3]`, a label list and an extraction step no other case uses, so the
# point is genuinely new. A mode-sensitive step is load-bearing ONLY for the two
# cases that attack the mode position itself (`atk-retaining-mode`,
# `atk-first-label-only-removing`), where the RIVAL applies the step at `false`.


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Every one keeps
    # the `theorem correct_toUnstackedDataset` statement byte-identical and
    # introduces no new axiom / theorem / lemma / assumption token; where the
    # reshape moves the loop out from under the frozen closing argument, the
    # proof is genuinely RE-PROVED inside the proof region rather than weakened.
    # Each was confirmed to verify by a real build.
    # =====================================================================

    # Ports nagini's `pos-local-reshape`: there, hoist the index arithmetic into
    # a local `idx`; here the loop has no index arithmetic to hoist, so the
    # equivalent minimal reshape names the extracted slice in a local before the
    # entry is recorded. Definitionally the frozen body, so the frozen closing
    # argument still applies unchanged.
    {
        "id": "pos-slice-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_BODY,
            "    let slice := extractSlice true k\n"
            "    dataDict := dataDict ++ [(k, slice)]\n"),
        "rationale": "behaviourally identical reshape: the label-removing "
                     "extraction is bound to a local before the entry is "
                     "recorded, so the same entry is appended for the same "
                     "label in the same order and the single spec equation "
                     "still holds on every input. MUST verify (else "
                     "SPEC-TOO-STRONG). Definitionally the frozen loop body, so "
                     "the frozen tactic body closes it unchanged; statement "
                     "byte-identical, nothing assumed. Ports nagini's "
                     "pos-local-reshape (its `idx` local has no counterpart "
                     "here — this loop does no index arithmetic).",
    },

    # Ports nagini's `pos-singleton-local`: materialise the one-element list in
    # a typed local before the concatenation, instead of inlining it.
    {
        "id": "pos-entry-list-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_BODY,
            "    let entry : List (κ × ν) := [(k, extractSlice true k)]\n"
            "    dataDict := dataDict ++ entry\n"),
        "rationale": "materialising the singleton entry list in a typed local "
                     "before the concatenation is behaviourally identical (the "
                     "concatenated sequence is unchanged), so the spec equation "
                     "still holds everywhere. MUST verify (else "
                     "SPEC-TOO-STRONG). Statement byte-identical, nothing "
                     "assumed. Direct port of nagini's pos-singleton-local.",
    },

    # A genuinely different SHAPE (not merely a renamed local): the accumulator
    # loop is replaced by a front-recursive fold, which is how the same behavior
    # would be written functionally. The frozen closing argument is about the
    # loop and no longer applies, so the proof region is RE-PROVED honestly by
    # list induction — no helper lemma, no new declaration, statement
    # byte-identical. This is the case that would have been tempting to fake, so
    # it is stated explicitly: the obligation is closed for the NEW impl.
    {
        "id": "pos-functional-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(
            _BASE,
            (_I_DEF,
             "def implementation_toUnstackedDataset {κ ν : Type}\n"
             "    (extractSlice : Bool → κ → ν) (vars : List κ) :\n"
             "    List (κ × ν) :=\n"
             "  vars.foldr (fun k acc => (k, extractSlice true k) :: acc) []\n"),
            (_P_TAIL,
             "  induction vars with\n"
             "  | nil => simp\n"
             "  | cons a as ih => simp [ih]\n"),
        ),
        "rationale": "structurally different CORRECT implementation: the "
                     "mutable accumulator loop is replaced by a front-recursive "
                     "fold building the entries head-first. Same entries, same "
                     "labels, same order on every input, so the spec equation "
                     "holds — MUST verify (else SPEC-TOO-STRONG). The frozen "
                     "tactic body is specific to the loop's syntactic form, so "
                     "the proof region is RE-PROVED by list induction on the "
                     "labels; the `correct_toUnstackedDataset` STATEMENT is "
                     "byte-identical and no lemma/axiom/sorry is introduced. "
                     "This is the port's evidence that a reshaped impl is "
                     "rejected only when it is WRONG, not merely when it moves "
                     "out from under the frozen script.",
    },

    # The INVERTED port of nagini's `atk-launder-fresh-copy`. There, obtaining
    # the capability token and then returning a fresh value-equal copy must be
    # REJECTED, because the token sits on the contracted callee's own output. On
    # this referentially transparent carrier there is no token and a value-equal
    # rebuild IS the same value, so the same shape must be ACCEPTED. Shipping it
    # as a positive is what records that carrier difference instead of hiding
    # it. Re-proved: the rebuild loop needs its own copy-loop argument, supplied
    # as a local `have` inside the proof region.
    {
        "id": "pos-rebuild-elementwise",
        "kind": "soundness",
        "expect": "verify",
        "module": _swaps(
            _BASE,
            (_I_RET,
             "  let mut fresh : List (κ × ν) := []\n"
             "  for e in dataDict do\n"
             "    fresh := fresh ++ [e]\n"
             "  return fresh\n"),
            (_P_TAIL,
             "  have hmain := toUnstackedDataset_forIn_helper "
             "(fun k => extractSlice true k) vars []\n"
             "  have hcopy : ∀ (xs acc : List (κ × ν)),\n"
             "      (Id.run (forIn xs acc (fun e r =>\n"
             "        (do pure PUnit.unit; pure (ForInStep.yield "
             "(r ++ [e])))))) = acc ++ xs := by\n"
             "    intro xs\n"
             "    induction xs with\n"
             "    | nil => intro acc; simp only [List.forIn_nil, Id.run, "
             "List.append_nil]; rfl\n"
             "    | cons a as ih =>\n"
             "      intro acc\n"
             "      rw [List.forIn_cons]\n"
             "      simp only [Id.run, bind] at ih ⊢\n"
             "      rw [ih]\n"
             "      simp\n"
             "  simp only [Id.run, bind] at hmain hcopy ⊢\n"
             "  simp [hcopy, hmain]\n"
             "  rfl\n"),
        ),
        "rationale": "re-materialising the assembled collection entry-by-entry "
                     "before returning it produces the SAME list of entries, so "
                     "the spec equation still holds and it MUST verify (else "
                     "SPEC-TOO-STRONG). Re-proved inside the proof region: the "
                     "copy loop is discharged by a LOCAL `have` (no top-level "
                     "lemma, no axiom, no sorry) and composed with the frozen "
                     "loop helper; statement byte-identical. This is nagini's "
                     "atk-launder-fresh-copy INVERTED — see the module "
                     "docstring's ADVERSARIAL READ: nagini rejects it via a "
                     "capability token this bundle does not model, and on an "
                     "immutable carrier a value-equal rebuild is not a distinct "
                     "value, so the honest disposition here is ACCEPT.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, F2P-shaped
    # input, i.e. non-vacuous. The frozen theorem carries no precondition
    # hypothesis (the behavior is total), so nagini's `admiss-precond-holds`
    # (assert the Requires facts in scope for a normal input) re-expresses as:
    # discharge the spec predicate by EVALUATION at a concrete two-label input
    # with a mode-sensitive extraction step, as a local `have` prepended to the
    # frozen tactic body, then close the frozen obligation verbatim. If the
    # modeled behavior were unsatisfiable at a normal input — the analogue of
    # PRECOND-TOO-STRONG — this would not elaborate.
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_OPEN,
            "  have _ground : problem_spec_toUnstackedDataset\n"
            f"      ({_E_OFF1}) ([0, 1] : List Nat)\n"
            "      (implementation_toUnstackedDataset\n"
            f"        ({_E_OFF1}) ([0, 1] : List Nat)) := by\n"
            "    unfold problem_spec_toUnstackedDataset "
            "implementation_toUnstackedDataset\n"
            "    decide\n"
            + _P_OPEN),
        "rationale": "the obligation is discharged by evaluation at the "
                     "smallest F2P-shaped input (two labels, an extraction step "
                     "that genuinely distinguishes the two modes) as a local "
                     "`have`, and the frozen obligation is then closed "
                     "verbatim. It verifies, so the modeled behavior is "
                     "satisfiable at a normal input and the spec is not "
                     "vacuously unsatisfiable there (the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, statement byte-identical, the ground "
                     "instance is a `have` inside the existing tactic body. "
                     "Ports nagini's admiss-precond-holds (its Requires facts "
                     "have no counterpart — this obligation binds no "
                     "precondition hypothesis).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec, which MUST be rejected. Each carries (a) the `refinement`
    # argument that its faithful real counterpart would NOT resolve the F2P, and
    # (b) a `witness` pinning the violation at one concrete input, seen by real
    # build to hold of the rival and to FAIL on the frozen solution.
    # =====================================================================

    # ---- D1: the reported behavior itself — the label-RETAINING mode ---------
    # Ports nagini's `atk-discard-false`, the single-knob rival that IS the
    # pre-fix behavior. There the rejection comes from the contracted merge
    # callee's guard (the retained markers are not all equal); here it comes
    # directly from the spec equation, which pins the extraction mode.
    {
        "id": "atk-retaining-mode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_BODY,
            "    dataDict := dataDict ++ [(k, extractSlice false k)]\n"),
        "refinement": "this IS the reported pre-fix behavior: every slice is "
                      "extracted in the label-retaining mode, so each slice "
                      "keeps the selecting label attached to it as a scalar "
                      "marker. A faithful real patch retaining that marker is "
                      "exactly the state the report describes — recombining the "
                      "slices then finds each one carrying a DIFFERENT value "
                      "for that marker and refuses to combine them, raising "
                      "instead of returning, which is precisely the failure the "
                      "F2P test reproduces on a single-sample-axis input. So "
                      "the faithful patch does not resolve; it is the bug.",
        "rationale": "REJECT from the spec equation's mode position (D1): the "
                     "spec pins entry slices to `extractSlice true k` and the "
                     "rival emits `extractSlice false k`, which differ for any "
                     "extraction step that is sensitive to its mode argument. "
                     "Refuted at a single label with a mode-sensitive step (the "
                     "retaining mode shifts by 1), so the divergence is "
                     "attributed to the mode alone and to nothing about the "
                     "label list. If it verified, the spec would leave the "
                     "extraction mode free — SPEC-TOO-WEAK on the whole "
                     "behavioral content of the fix.",
        "witness": _w(_E_OFF1, "[7]"),
    },

    # ---- D1 NEAR-MISS: only the FIRST label gets the label-removing mode -----
    # A strictly harder rival than the wholesale flip: it AGREES with the frozen
    # behavior on the first label and diverges only from the second onward, so it
    # is correct on the whole single-label sub-domain. It therefore gets its own
    # witness at a two-label input rather than sharing the previous one, which
    # would have claimed a sub-domain the manifest never demonstrated.
    {
        "id": "atk-first-label-only-removing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swaps(
            _BASE,
            (_I_MUT, _I_MUT + "  let mut firstLabel : Bool := true\n"),
            (_I_BODY,
             "    dataDict := dataDict ++ [(k, extractSlice firstLabel k)]\n"
             "    firstLabel := false\n"),
        ),
        "refinement": "applies the label-removing mode to the first label only "
                      "and the label-retaining mode to every later one. A "
                      "faithful real patch that fixed only the first extraction "
                      "leaves every subsequent slice carrying its own attached "
                      "marker; recombination then still finds conflicting "
                      "values for that marker across the remaining slices and "
                      "still refuses, so the reported roundtrip still fails "
                      "whenever there is more than one variable — which is the "
                      "F2P case (it builds a collection of two variables). The "
                      "faithful patch does not resolve.",
        "rationale": "REJECT from the mode position (D1) on a STRICT SUB-DOMAIN: "
                     "this rival is correct for every one-label input and wrong "
                     "from the second label onward, so it is a near-miss of "
                     "atk-retaining-mode and cannot honestly share its witness. "
                     "Refuted at a TWO-label input with a mode-sensitive "
                     "extraction step (the retaining mode shifts by 100), where "
                     "the second entry's slice is the retaining extraction the "
                     "spec forbids. If it verified, the spec would pin the mode "
                     "only for the first label — SPEC-TOO-WEAK.",
        "witness": _w(_E_OFF100, "[2, 9]"),
    },

    # ---- D2: extract on the WRONG label ------------------------------------
    # The nagini analogue is `atk-wrong-roundtrip-data` (assemble the position
    # labels instead of the member values): a rival with the right cardinality
    # and shape whose per-entry content is drawn from the wrong place. Here the
    # sharpest form on this carrier is to invoke the extraction on the FIRST
    # label for every entry while still recording each entry's own label — so
    # the structure is perfect and only the extraction argument is wrong.
    {
        "id": "atk-extract-wrong-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_BODY,
            "    dataDict := dataDict ++ "
            "[(k, extractSlice true (vars.headD k))]\n"),
        "refinement": "records, for every label, the slice extracted for the "
                      "FIRST label. A faithful real patch that selected the "
                      "same slice for every label returns a collection in which "
                      "every variable holds the first variable's data, so the "
                      "expansion is not identical to the collection it was "
                      "built from and the F2P identity assertion fails (that "
                      "assertion compares each variable's data, not just the "
                      "set of names). The faithful patch does not resolve.",
        "rationale": "REJECT from the spec equation's extraction-ARGUMENT "
                     "position (D2): the spec pins the slice in entry `k` to the "
                     "extraction invoked on `k`, and this rival invokes it on the "
                     "head label instead. Refuted at a TWO-label input with a "
                     "MODE-INSENSITIVE extraction step, which isolates the "
                     "argument error from any mode error — the rival uses the "
                     "correct (label-removing) mode throughout, so the "
                     "rejection is attributable to the argument alone. If it "
                     "verified, the spec would not pin WHICH label each slice "
                     "is extracted for — SPEC-TOO-WEAK.",
        "witness": _w(_E_ID, "[1, 2]"),
    },

    # ---- D3: pair a slice with the WRONG label -----------------------------
    # The mirror of D2: extract correctly per label, but record every entry
    # under the first label. Attacks the pairing half of the equation, which no
    # nagini rival isolates (nagini's carrier is a bare value list with the
    # positions passed separately, so label/slice pairing is not expressible
    # there — see the docstring's ADVERSARIAL READ).
    {
        "id": "atk-pair-wrong-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_BODY,
            "    dataDict := dataDict ++ "
            "[(vars.headD k, extractSlice true k)]\n"),
        "refinement": "extracts each label's own slice but files every one of "
                      "them under the FIRST label. A faithful real patch keying "
                      "the assembled collection by the wrong label produces a "
                      "collection whose names do not match the original's (one "
                      "name repeated, the others missing), so the expansion is "
                      "not identical to the collection it was built from and the "
                      "F2P identity assertion fails. The faithful patch does "
                      "not resolve.",
        "rationale": "REJECT from the spec equation's PAIRING position (D3): the "
                     "spec pins entry `i` to `(vars[i], extractSlice true "
                     "vars[i])`, tying the recorded label to the label the slice "
                     "was extracted for; this rival records the head label "
                     "beside every correctly-extracted slice. Refuted at a "
                     "two-label input with a mode-insensitive doubling "
                     "extraction step, whose distinct outputs make the mismatched "
                     "pairing visible while the mode stays correct. If it "
                     "verified, the spec would leave the label/slice "
                     "correspondence free — SPEC-TOO-WEAK.",
        "witness": _w(_E_DOUBLE, "[3, 5]"),
    },

    # ---- D4: drop the last entry (cardinality, partial domain) --------------
    # Direct port of nagini's `atk-drop-last-member`.
    {
        "id": "atk-drop-last-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_FOR, "  for k in vars.dropLast do\n"),
        "refinement": "walks every label but the last, so the assembled "
                      "collection is missing the final variable. A faithful "
                      "real patch that skipped the last label returns a "
                      "collection with one fewer variable than the original, so "
                      "the expansion is not identical to it and the F2P identity "
                      "assertion fails. The faithful patch does not resolve.",
        "rationale": "REJECT from the spec equation's STRUCTURE (D4, "
                     "cardinality): the spec pins the result to have exactly one "
                     "entry per label, and this rival produces one fewer. "
                     "Refuted at a THREE-label input with a mode-insensitive "
                     "shifting extraction step — the longest label list in the "
                     "battery, chosen so the omission is of a genuine interior "
                     "collection rather than of the only element. Correct on "
                     "every earlier entry, so it is a partial-domain rival. If "
                     "it verified, the spec would not pin that all labels are "
                     "covered — SPEC-TOO-WEAK. Direct port of nagini's "
                     "atk-drop-last-member.",
        "witness": _w(_E_SHIFT, "[1, 2, 3]"),
    },

    # ---- D4: return nothing at all -----------------------------------------
    # Direct port of nagini's `atk-empty` cheap near-miss.
    {
        "id": "atk-empty-collection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_RET, "  return []\n"),
        "refinement": "assembles the entries and then returns an empty "
                      "collection, recovering nothing. A faithful real patch "
                      "returning an empty collection is not identical to the "
                      "original (which has variables in it), so the F2P "
                      "identity assertion fails immediately. The faithful patch "
                      "does not resolve.",
        "rationale": "REJECT from the spec equation's STRUCTURE (D4): the spec "
                     "pins the result to the list of all labels' entries, which "
                     "is non-empty whenever there is at least one label, and "
                     "this rival returns the empty list. Refuted at a "
                     "SINGLE-label input with a mode-insensitive identity "
                     "extraction step — the cheapest possible discriminator, "
                     "deliberately at a different label value and list length "
                     "from every other witness. Direct port of nagini's "
                     "atk-empty.",
        "witness": _w(_E_ID, "[4]"),
    },

    # ---- D4: right entries, wrong ORDER ------------------------------------
    # No nagini counterpart: nagini's postcondition compares sequences whose
    # construction direction is fixed by its loop invariant, and its rivals
    # attack values and the capability token rather than order. Order is an
    # independent load-bearing half of this spec's structural clause (the spec
    # says "in the order the labels are listed"), so it gets its own rival.
    {
        "id": "atk-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_RET, "  return dataDict.reverse\n"),
        "refinement": "assembles every entry correctly and then returns them in "
                      "reverse label order. A faithful real patch that reversed "
                      "the assembled collection changes the order of the "
                      "variables relative to the original, so the expansion is "
                      "not identical to the collection it was built from and the "
                      "F2P identity assertion fails. The faithful patch does not "
                      "resolve.",
        "rationale": "REJECT from the spec equation's ORDER (D4): the spec pins "
                     "the result to the labels' entries in the order the labels "
                     "are listed, and this rival emits them reversed — every "
                     "entry individually correct, the sequence wrong. Refuted at "
                     "a two-label input with a MODE-SENSITIVE extraction step "
                     "that collapses the retaining mode to a constant, a third "
                     "distinct shape of extraction step, so the order failure is "
                     "demonstrated on a carrier point no other witness probes. "
                     "If it verified, the spec would leave the entry order free "
                     "— SPEC-TOO-WEAK on the ordering half of the structural "
                     "clause. No nagini counterpart (see the module "
                     "docstring's porting map).",
        "witness": _w(_E_TRIPLE, "[8, 3]"),
    },

    # ---- FABRICATED (all-equal) COLLECTION ----------------------------------
    # Ports nagini's `atk-fabricate-allequal-resid`, which the first revision of
    # this port dropped WITHOUT recording it — the only nagini case that was
    # silently absent rather than argued vacuous, found by this audit. There, the
    # rival tries to slip past the merge guard by feeding a FABRICATED all-equal
    # position list instead of the real one. The carrier analogue is exact and
    # expressible: fabricate a degenerate all-equal collection by taking the head
    # label's entry for every position, so both halves of every pair are
    # fabricated together and the result is a constant list.
    #
    # Not a duplicate of D2 or D3, and that is the point of adding it. D2
    # (`atk-extract-wrong-label`) keeps each entry's own LABEL and corrupts only
    # the extraction argument; D3 (`atk-pair-wrong-label`) keeps each entry's own
    # SLICE and corrupts only the recorded label. Each leaves one component of
    # every pair correct, so each is refutable by a witness that only has to see
    # one half. This rival corrupts BOTH components coherently: every entry is a
    # genuine, correctly-paired (label, slice) entry of the frozen function — just
    # the WRONG one, repeated. It is internally consistent in a way neither D2 nor
    # D3 is, which is precisely the "degenerate but self-consistent" shape
    # nagini's guard existed to catch.
    {
        "id": "atk-fabricate-allequal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_BODY,
            "    let fake := vars.headD k\n"
            "    dataDict := dataDict ++ [(fake, extractSlice true fake)]\n"),
        "refinement": "records the FIRST label's entry — its label and its slice "
                      "together — once per label, producing a degenerate "
                      "collection in which every variable is a copy of the first. "
                      "A faithful real patch that assembled one variable's entry "
                      "repeatedly returns a collection whose names are one name "
                      "repeated and whose data is one variable's data repeated, "
                      "so the expansion is not identical to the collection it was "
                      "built from and the F2P identity assertion fails on both "
                      "counts. The faithful patch does not resolve.",
        "rationale": "REJECT from the spec equation read as a WHOLE (D2+D3+D4 "
                     "jointly): the spec pins entry `i` to `(vars[i], "
                     "extractSlice true vars[i])`, and this rival emits "
                     "`(vars[0], extractSlice true vars[0])` at every position. "
                     "Unlike atk-extract-wrong-label and atk-pair-wrong-label, "
                     "each of which leaves one component of every pair correct, "
                     "this rival corrupts both components COHERENTLY — every "
                     "entry it emits is a well-formed entry of the frozen "
                     "function, just the wrong one — so it is self-consistent and "
                     "cannot be refuted by inspecting either component alone. "
                     "Refuted at a two-label input with a mode-insensitive "
                     "shift-by-5 step, at a label list and step no other witness "
                     "uses. If it verified, the spec would pin only that entries "
                     "are well-formed, not WHICH entry sits at each position — "
                     "SPEC-TOO-WEAK. Ports nagini's "
                     "atk-fabricate-allequal-resid, whose omission this audit "
                     "found unrecorded.",
        "witness": _w(_E_PLUS5, "[2, 6]"),
    },
]


# ---------------------------------------------------------------------------
# POINT SPREAD of the reject witnesses (what `pbt_coverage.py` reports as
# `pts=`). Both input binders of `problem_spec_toUnstackedDataset` are varied;
# no binder is held at one value across the battery.
#
#   case                            extractSlice at `true`    vars
#   ------------------------------  ------------------------  ---------
#   atk-retaining-mode              id (mode-sensitive: +1)   [7]
#   atk-first-label-only-removing   id (mode-sensitive: +100) [2, 9]
#   atk-extract-wrong-label         id                        [1, 2]
#   atk-pair-wrong-label            ×2                        [3, 5]
#   atk-drop-last-entry             +10                       [1, 2, 3]
#   atk-empty-collection            id                        [4]
#   atk-reversed-order              ×3                        [8, 3]
#   atk-fabricate-allequal          +5                        [2, 6]
#
# Eight (extractSlice, vars) pairs, all distinct AS EVALUATED. The column is
# deliberately headed "at `true`" rather than "shape", because that is the only
# thing a witness can observe: the spec applies the step exclusively at `true`,
# so a step's `false` branch is invisible to every witness and two steps that
# agree at `true` are the SAME carrier point however differently they are
# written. The mode-sensitivity noted in parentheses for the first two cases is
# load-bearing only there — those are the rivals that themselves apply the step
# at `false`, so their witnesses discriminate BECAUSE the two branches differ.
#
# This table was corrected by audit. It previously listed `atk-reversed-order`
# at `if m then k else 0` with `vars = [1, 2]`, described as a third distinct
# mode-sensitive shape; at `true` that step IS the identity, so it coincided
# exactly with `atk-extract-wrong-label`'s point, label list included. Two of the
# then-seven `pts` were one point. `atk-reversed-order` was moved to `×3` at
# `[8, 3]` and both were re-verified by real builds (rival exit 0, gold exit 1,
# flipped-claim forgery on gold exit 0). `vars` now spans lengths 1/2/3 over
# seven distinct label sets.
#
# AXIOM LANE: intentionally absent. `meta.json` records `axioms: []` — the
# per-label extraction step is universally quantified, not axiomatized — and the
# axiom lane is G-AX's job, which this gate ignores. The nagini sibling's four
# AXIOM_TESTS are dropped per the porting map.
# ---------------------------------------------------------------------------
