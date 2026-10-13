"""properties.py — G-PBT falsification battery for django__django-15814 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct resolveKeys`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec — here the ``witness_reference``
rather than the frozen solution, for the reason set out under WITNESS MECHANICS
below).

DEFENDED SURFACE. One contracted method over a read-only relation chain
``entities : List Entity`` (``Entity`` carries two identity tokens: ``ident``,
the model exactly as reached through the relation, and ``canon``, that model's
canonical underlying identity — they coincide for an ordinary model and DIFFER
for a derived view). The method returns the sequence of keys the chain
contributes to the downstream field-restriction map, one per model reached:

  resolveKeys (entities : List Entity)   ensures out = keysOf entities

``keysOf`` is the front-recursive fold that keys every entity by ``canonOf e =
e.canon`` — its CANONICAL identity, never the surface ``ident``. This is the SOLE
load-bearing clause and it is fully GROUNDED in the method's own input (directive
8): there is no opaque answer key to echo — evaluating ``keysOf entities`` IS the
correct answer, computed from ``entities``. The behavior pinned is the single
change the operation requires: a model reached as a derived view keys the SAME as
its underlying model, so the downstream consumer (which indexes by the canonical
identity) finds every reached model's entry. Keying by the surface ``ident``
instead scatters a derived view under a key the consumer never looks up — the
reported crash.

BINDER STRUCTURE. ``entities`` is the sole INPUT BINDER; it is read-only (no
``mut``). Its two projections carry independent behavior: ``.canon`` is the
answer the fold must produce, and ``.ident`` is the pre-normalization identity a
wrong impl keys by. The load-bearing discrimination is that on a chain containing
a derived view (``.ident ≠ .canon``) the correct key is ``.canon`` and NOT
``.ident``. The reject witnesses vary ``entities`` across: a single derived view
(``.ident ≠ .canon``), a plain model (``.ident = .canon``), lengths one and two,
and distinct-vs-shared tokens — so both projections and the length take multiple
values and the central ``.ident ≠ .canon`` sub-domain is exercised.

The failing scenario is a relation chain whose target is a derived view of an
underlying model, optimized so the downstream consumer looks up the underlying
model's key. In carrier terms that is a single ``Entity`` with ``.ident ≠
.canon``: ``keysOf`` keys it by ``.canon`` (found), while keying by ``.ident``
(the pre-change behavior) misses. Any rival that keys such an entity by its
surface identity does NOT resolve.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries this MANDATORY
    because its read-only input is held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: every parameter is an immutable value, this bundle
    declares no ``mut`` binder on ``entities``, there is no heap and no aliasing —
    so there is no read-only input to mutate and no substitute probe. Not
    fabricated (per the porting map: this class is vacuous here). The sibling's
    "the input map must not be mutated" obligation is structurally guaranteed by
    the ABSENCE of a ``mut`` on ``entities``, which the frozen spec encodes.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully-unfolded
    function of the method's own input (``keysOf``/``canonOf`` are concrete
    ``def``s in the ``pure`` region; the ``axioms`` region declares nothing).
    There is no opaque answer key to echo — evaluating ``keysOf`` IS the correct
    answer — so there is no WRONG echo to build. Honest cheapest-reshape positive
    controls stand in.
  * PARTIAL-DOMAIN / RAW-KEYING — APPLIES and is CENTRAL: a rival keying by the
    surface ``ident`` is correct on the sub-domain of plain models
    (``ident = canon``) and wrong exactly on a chain containing a derived view.
    ``weak-key-by-ident`` attacks this — it is the sibling's central pre-patch
    defect (``weak-prepatch-raw-keying``).
  * PARTIAL-DOMAIN / LENGTH & CONTENT — APPLIES: rivals right on part of the
    domain but dropping / over-listing / mis-keying a produced key.
    ``weak-drop-first``, ``weak-drop-all``, ``weak-over-fetch`` and
    ``weak-scatter-ident`` attack these, each at a distinct input point.

WITNESS MECHANICS on this carrier, and why every reject case carries a
``witness_reference``. Each reject rival is written straight-line, so ITS tester
reduces and ``decide`` settles it; the witness states ``resolveKeysTester
<entities> = false`` at a concrete point where the rival's keys violate the
post-image while the correct keys satisfy it. No ``sorry``/``admit``/
``native_decide``/``axiom``. ``Entity`` is a two-``Int``-field structure, so
``⟨i, c⟩`` is a concrete entity and ``decide`` settles every equality; there is
no ``require`` clause, so the precondition is ``True`` and every input reaches
the postcondition (nothing is vacuously excluded, and the witnesses bind nothing,
so there is no consistency obligation).

The FROZEN impl, however, cannot serve as the discrimination half's subject. It
keeps a ``while`` loop, and under ``loom.semantics.choice "demonic"`` that loop's
fixpoint elaborates through ``Classical.choice``, which the kernel cannot unfold.
So ``decide`` against the frozen program is STUCK for EVERY claim, true or false:
measured here, the gold-side build of ``weak-key-by-ident``'s witness reports

    Tactic `decide` failed for proposition
      resolveKeysTester [{ ident := 2, canon := 1 }] = false
    ... did not reduce to `isTrue` or `isFalse`.
    ... reduction got stuck at the `Decidable` instance

which is a build failure that attributes NOTHING — the identical error appears
for a claim that is true of the frozen impl, so a forged witness asserting the
rival is CORRECT would clear both halves. That is not a refutation, and reading
it as one is exactly the hollow attestation this lane exists to prevent.

Route 1 (state the refutation over a computable projection) is NOT available on
this carrier: the method's sole output is the key sequence itself, and every
projection of it — an element, the length, a membership — is a projection OF the
loop's result, so its reduction still goes through the same irreducible fixpoint.
There is no sum or coordinate that bypasses the loop. So each reject case names a
``witness_reference`` instead: ``_LOOPFREE``, the loop-free impl that returns the
modeled fold directly. It shares the frozen spec byte-for-byte, it VERIFIES
(so it cannot violate its own spec, which is what makes refuting a witness
against it sound), and it REDUCES — the same five witnesses come back from it as
``decide`` *proved that the proposition ... is false*, a real verdict rather than
a stuck one. ``_LOOPFREE`` is also shipped as the ``pos-collapse-direct``
positive, so the battery itself records that loop-freeness is not what any rival
is being rejected for. See the gate's ``witness-undecided`` contract.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. ``weak-key-by-ident`` is refuted on a single derived view
``[⟨2, 1⟩]`` (``ident ≠ canon`` — the ONLY shape on which raw keying bites; on a
plain model it agrees with the spec). ``weak-drop-first`` is the sharper
near-miss of ``weak-drop-all``: it drops one produced key, so it is refuted on a
two-distinct-model chain ``[⟨1, 1⟩, ⟨2, 2⟩]`` where it returns the tail while
``weak-drop-all`` returns empty — the sub-domain that SEPARATES them — rather than
on the singleton where they coincide. ``weak-drop-all`` is refuted on the
singleton ``[⟨1, 1⟩]``. ``weak-over-fetch`` is refuted on a plain model
``[⟨7, 7⟩]`` where it appends a spurious key. ``weak-scatter-ident`` is refuted
on a derived view ``[⟨5, 3⟩]`` where it emits both the canonical AND the surface
key. Five distinct points; ``.ident`` vs ``.canon`` and the length are varied
across them.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom`` and no A-reference
deep model — the canonical-identity normalization is modeled DEEPLY in the
``pure`` region as ``canonOf``/``keysOf`` over the input carrier, not borrowed
from an oracle; see mapping.md §3). There is nothing to probe and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15814"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one impl region and is
# ---- unique inside Solution.lean; both facts asserted at load by _swap) ----

# The whole executable body: the backward accumulator loop that prepends each
# reached entity's CANONICAL key. Reshaped wholesale by the rivals and the
# loop-free positive control.
_IMPL = (
    "    let mut keys : List Int := []\n"
    "    let mut i := entities.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ entities.length\n"
    "      invariant keys = keysOf (entities.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := entities[i - 1]!\n"
    "      keys := canonOf e :: keys\n"
    "      i := i - 1\n"
    "    return keys\n"
)

# The single loop-body key-recording step (a substring of _IMPL; unique in the
# file). Reshaped by the loop-preserving positive control.
_STEP = "      keys := canonOf e :: keys\n"

# The accumulator initializer (unique). Anchor for the admissibility assert.
_INIT = "    let mut keys : List Int := []\n"

# ---- proof-body anchors. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its tactic script without
# ---- touching the spec or dropping the obligation. ----

# The full frozen tactic script (retuned by the loop-free positive, whose no-loop
# body leaves none of the loop-invariant goals the frozen script closes).
_PROOF = (
    "prove_correct resolveKeys by\n"
    "  loom_solve\n"
    "  rw [keysOf_drop_step entities i (by omega) (by omega)]\n"
    "  simp_all\n"
)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester machinery:
# ---- `resolveKeysTester <entities> = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script can
# ---- mask the verdict. There is no `require` clause, so the precondition is
# ---- `True` and decides trivially.
_TESTER = (
    "extract_program_for resolveKeys\n"
    "prove_precondition_decidable_for resolveKeys\n"
    "prove_postcondition_decidable_for resolveKeys\n"
    "derive_tester_for resolveKeys\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : resolveKeysTester {call} = false := by\n  decide\n"


# ---- the witness_reference shared by the whole reject lane. A LOOP-FREE impl of
# ---- the frozen spec: it returns the modeled fold directly, so it VERIFIES
# ---- (`out = keysOf entities` holds definitionally) and — unlike the frozen
# ---- `while` impl, whose demonic-choice fixpoint routes through
# ---- `Classical.choice` and blocks `decide` for every claim — its tester
# ---- REDUCES, so a witness refuted against it gets a real verdict instead of a
# ---- stuck one. The proof retunes to `loom_solve` alone because the no-loop body
# ---- leaves none of the loop-invariant goals the frozen script discharges.
# ---- Shipped as `pos-collapse-direct` too, so the battery records that
# ---- loop-freeness is not what any rival is rejected for.
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL, "    return keysOf entities\n"),
    _PROOF, "prove_correct resolveKeys by\n  loom_solve\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the identical
    # theorem statement; only the executable surface and (where needed) the
    # tactic script move. Both were confirmed to build out-of-band.
    # =====================================================================
    {
        "id": "pos-collapse-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the modeled fold directly.
        # Observationally identical (the loop's post-state IS the fold), so the
        # clause holds definitionally; the tactic script is retuned because the
        # no-loop body leaves none of the loop-invariant goals the frozen script
        # discharges, so `loom_solve` alone closes it.
        "module": _LOOPFREE,
        "rationale": "returning the modeled fold directly satisfies "
                     "`out = keysOf entities` definitionally; a correct loop-free "
                     "reshape MUST verify, else SPEC-TOO-STRONG on the loop FORM. "
                     "The proof retunes to `loom_solve` alone because the no-loop "
                     "body leaves no loop-invariant goal. This same source is the "
                     "`witness_reference` the whole reject lane is refuted "
                     "against, so shipping it as a positive is what records that "
                     "loop-freeness is not why any rival is rejected.",
    },
    {
        "id": "pos-canon-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the loop body prepends `e.canon` (the canonical field read
        # inline) instead of going through the named `canonOf` combinator. Same
        # accumulator, same order, so the clause still holds; the frozen invariant
        # proof needs one extra unfold of `canonOf` to see the two agree.
        "module": _swap(
            _swap(_BASE, _STEP, "      keys := e.canon :: keys\n"),
            _PROOF,
            "prove_correct resolveKeys by\n"
            "  loom_solve\n"
            "  rw [keysOf_drop_step entities i (by omega) (by omega)]\n"
            "  simp_all [canonOf]\n"),
        "rationale": "a correct reshape of the loop body (reading the canonical "
                     "field inline rather than via the `canonOf` combinator) "
                     "records the same key per entity, so `out = keysOf entities` "
                     "still discharges with the frozen invariant; must verify else "
                     "SPEC-TOO-STRONG. The proof adds one `canonOf` unfold so the "
                     "inline read and the combinator are seen equal.",
    },

    # =====================================================================
    # ADMISSIBILITY. This method has NO `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # DEGENERATE at the interesting point — a spec no impl can meet reads
    # exactly like a spec every impl meets. This case discharges an in-region
    # `assert` pinning the fold's discriminating behavior at the F2P-shaped
    # inputs: a single derived view `⟨2, 1⟩` keys to `[1]` (its CANONICAL
    # identity, NOT `2`), and a plain model `⟨9, 9⟩` keys to `[9]` (surface and
    # canonical coincide). The surrounding impl is kept verbatim so the method's
    # own obligation still discharges; the assert is live (a false claim about
    # the same points leaves an unsolved goal). Confirmed to build.
    # =====================================================================
    {
        "id": "admiss-canon-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `admiss\n"
                "      (keysOf [⟨2, 1⟩] = [1] ∧ keysOf [⟨9, 9⟩] = [9]))\n"
                + _INIT),
            _PROOF,
            "prove_correct resolveKeys by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (refine ⟨by decide, by decide⟩)\n"
            "    | (rw [keysOf_drop_step entities i (by omega) (by omega)]; simp_all)\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped inputs: a derived view `⟨2, 1⟩` keys to its "
                     "CANONICAL identity `[1]` (not the surface `2`), and a plain "
                     "model `⟨9, 9⟩` keys to `[9]`. The in-region assert must "
                     "discharge (else the obligation is degenerate); the impl is "
                     "kept verbatim so `out = keysOf entities` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is written
    # straight-line so its tester reduces under `decide`. Every witness was
    # confirmed out-of-band to ELABORATE against the rival and FAIL (get stuck)
    # against the frozen solution.
    # =====================================================================
    {
        "id": "weak-key-by-ident",
        "kind": "uniqueness",
        "expect": "reject",
        # The central pre-change defect: key every reached model by its SURFACE
        # identity `ident` rather than its canonical identity `canon`. Correct on
        # a chain of plain models (ident = canon), wrong exactly on a chain
        # containing a derived view.
        "module": _swap(_BASE, _IMPL, "    return entities.map Entity.ident\n"),
        "refinement": "keying a reached model by the identity it is reached AS "
                      "(the surface view) rather than its canonical underlying "
                      "identity is the exact pre-change behavior: for a chain whose "
                      "target is a derived view the passthrough key is recorded "
                      "under the view, and the downstream consumer — which indexes "
                      "by the canonical model — looks up the underlying model's key "
                      "and does not find it, raising the reported crash. A faithful "
                      "patch that kept surface keying is the unfixed code: the "
                      "select-related-with-field-restriction test on a derived-view "
                      "target FAILS. It would NOT resolve.",
        "rationale": "REJECT from `out = keysOf entities`: on a chain containing a "
                     "derived view (`ident ≠ canon`) the rival records `ident` "
                     "where the fold demands `canon`. Refuted on `[⟨2, 1⟩]` "
                     "(ident 2 ≠ canon 1) — the ONLY shape on which raw keying "
                     "bites; on a plain model it agrees. Discrimination comes from "
                     "`.ident` vs `.canon`. If it verified => SPEC-TOO-WEAK (the "
                     "canonical-keying fix would be unenforced).",
        "witness": _witness("[⟨2, 1⟩]"),
        # Refuted against the loop-free reference, not gold: the frozen
        # `while` impl's demonic-choice fixpoint blocks `decide` for every
        # claim, so a gold-side failure would attribute nothing.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: the keys are correct, but the first produced key is dropped.
        # Correct only when the chain has at most one entity; attacks the exact
        # post-image at a point distinct from weak-drop-all.
        "module": _swap(_BASE, _IMPL, "    return (keysOf entities).drop 1\n"),
        "refinement": "a counterpart that omits the first reached model's key "
                      "leaves that model out of the downstream field-restriction "
                      "map, so its restrictions are never recorded — the reported "
                      "key is short by one on any chain of length ≥ 1. A faithful "
                      "patch behaving this way changes which columns the query "
                      "restricts and the select-related test does not reconstruct "
                      "the object as expected. It would NOT resolve.",
        "rationale": "REJECT from `out = keysOf entities`: on any chain of length "
                     "≥ 1 the rival drops the first key the fold requires. Refuted "
                     "on a two-distinct-model chain `[⟨1, 1⟩, ⟨2, 2⟩]`, where it "
                     "returns the tail `[2]` while `weak-drop-all` returns empty — "
                     "the point that SEPARATES the two near-misses (on the "
                     "singleton they coincide). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("[⟨1, 1⟩, ⟨2, 2⟩]"),
        # Refuted against the loop-free reference, not gold: the frozen
        # `while` impl's demonic-choice fixpoint blocks `decide` for every
        # claim, so a gold-side failure would attribute nothing.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-drop-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits nothing: correct only on the empty chain, drops every produced key
        # otherwise.
        "module": _swap(_BASE, _IMPL, "    return []\n"),
        "refinement": "a counterpart that produces no keys records nothing in the "
                      "downstream field-restriction map for any reached model, so "
                      "no restriction is applied and the optimized query is "
                      "malformed. It would NOT resolve.",
        "rationale": "REJECT from `out = keysOf entities`: on any non-empty chain "
                     "the rival emits the empty key list where the fold demands the "
                     "produced keys. Correct only on the empty chain. Refuted on "
                     "the singleton `[⟨1, 1⟩]`, the smallest point that separates "
                     "it from the frozen keys. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("[⟨1, 1⟩]"),
        # Refuted against the loop-free reference, not gold: the frozen
        # `while` impl's demonic-choice fixpoint blocks `decide` for every
        # claim, so a gold-side failure would attribute nothing.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-over-fetch",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct keys plus a spurious extra key appended to the sequence. Presence
        # and canonical keying hold, but the produced sequence has an extra entry
        # the fold never yields.
        "module": _swap(_BASE, _IMPL, "    return keysOf entities ++ [888]\n"),
        "refinement": "a counterpart that records an extra key never reached along "
                      "the chain adds a spurious entry to the field-restriction "
                      "map, so the downstream consumer builds an init-list of the "
                      "wrong shape and the positional pk lookup breaks — the same "
                      "family of failure the fix removes. It would NOT resolve.",
        "rationale": "REJECT from `out = keysOf entities`: the rival appends a key "
                     "`888` the fold never produces, so the sequences differ in "
                     "length on every input. Refuted on a plain model `[⟨7, 7⟩]`, "
                     "where the fold yields `[7]` and the rival yields `[7, 888]`. "
                     "If it verified => SPEC-TOO-WEAK (no over-report guarantee).",
        "witness": _witness("[⟨7, 7⟩]"),
        # Refuted against the loop-free reference, not gold: the frozen
        # `while` impl's demonic-choice fixpoint blocks `decide` for every
        # claim, so a gold-side failure would attribute nothing.
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-scatter-ident",
        "kind": "uniqueness",
        "expect": "reject",
        # "Paper over the symptom": key each model by its canonical identity
        # (so the canonical entry is present) but ALSO emit the surface identity
        # for a derived view — scattering an extra key under the view. Correct on
        # plain models; wrong on a derived view.
        "module": _swap(
            _BASE, _IMPL,
            "    return entities.flatMap "
            "(fun e => if e.ident = e.canon then [e.canon] else [e.canon, e.ident])\n"),
        "refinement": "a counterpart that recorded a reached model's key under "
                      "BOTH its canonical identity and its surface view (rather "
                      "than cleanly under the canonical identity alone) reports an "
                      "extra entry keyed by a model identity the downstream "
                      "consumer does not expect, diverging from the single-key "
                      "shape the consumer relies on. It does not faithfully "
                      "implement the canonical-keying fix the failing test "
                      "exercises. It would NOT resolve.",
        "rationale": "REJECT from `out = keysOf entities`: on a derived view "
                     "(`ident ≠ canon`) the rival emits both `canon` and `ident` "
                     "where the fold yields only `canon`, so the sequences differ. "
                     "Refuted on `[⟨5, 3⟩]`, where the fold yields `[3]` and the "
                     "rival yields `[3, 5]`. Correct on plain models, so it is a "
                     "near-miss distinct from weak-key-by-ident (which drops the "
                     "canonical key entirely). If it verified => SPEC-TOO-WEAK.",
        "witness": _witness("[⟨5, 3⟩]"),
        # Refuted against the loop-free reference, not gold: the frozen
        # `while` impl's demonic-choice fixpoint blocks `decide` for every
        # claim, so a gold-side failure would attribute nothing.
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 mandatory frame-mutation, 4 uniqueness rivals)
# plus a 2-case AXIOM lane; every one is accounted for below. The sibling
# contracts a richer surface — `related_reported_fields(canonical, related,
# related_pk, chosen_attr)` returning a nested Dict[int, Dict[int,int]] whose
# outer KEY is the canonical identity and whose inner bucket's CONTENTS are pinned
# (presence + closure + anti-scatter). This bundle models only the KEYING step of
# the same operation: the ordered sequence of canonical keys a whole relation
# chain contributes (`out = keysOf entities`). The bucket-contents machinery
# (chosen_attr / related_pk presence, closure) is NOT modeled here — it is the
# nested inner Dict the velvet carrier folds away — so nagini cases attached to
# those inner clauses re-express as sequence-shaped keying rivals or are folded.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-direct-build        -> pos-collapse-direct        RE-EXPRESSED
#   pos-control-reorder             -> pos-canon-inline           RE-EXPRESSED
#   admiss-selfcall-proxy           -> admiss-canon-nondegenerate RE-AIMED
#   frame-mutate-canonical          -> (none)                     VACUOUS (no heap)
#   weak-prepatch-raw-keying        -> weak-key-by-ident          PORTED (central)
#   weak-over-fetch                 -> weak-over-fetch            PORTED
#   weak-scatter-injection          -> weak-scatter-ident         PORTED
#   (length/drop family, new)       -> weak-drop-first/-all       ADDED (carrier)
#   AXIOM_TESTS (1)                 -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (positives): the sibling's direct-build (skip the two-accumulator
#   merge, build the canonical bucket directly) and its statement-reorder (record
#   the pk before the chosen attr) both defend "a structurally different but
#   faithful impl must verify" over the bucket CONTENTS — which this carrier does
#   not model. The ARGUMENT is carried by the two reshapes that ARE expressible on
#   the keying fold: return the modeled fold directly (loop-free), and read the
#   canonical field inline rather than via the combinator. Both build (two real
#   builds each).
# RE-AIMED (admissibility): the sibling self-calls on an F2P-shaped proxy scenario
#   (canonical map {2:1,1:1}) to establish the precondition and assert the pk
#   lands in the canonical bucket. This bundle declares NO `require` clause, so
#   the "establish the precondition" reading is vacuous; it is re-aimed at the
#   residual total-domain risk (a degenerate post-image) via an in-region assert
#   that a derived view `⟨2, 1⟩` keys to its canonical `[1]` (not surface `2`) —
#   preserving the sibling's exact F2P witness point (proxy token 2 -> concrete 1).
# VACUOUS (frame-mutation): the sibling's MANDATORY probe writes
#   `canonical[related] = related` through a half-permission reference and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent, there is no heap, no aliasing, and this bundle declares no `mut`
#   binder on `entities`, so there is no read-only input to overwrite and no
#   substitute probe. Not fabricated (porting map: vacuous here). The "input must
#   not be mutated" obligation is structurally guaranteed by the absent `mut`.
# PORTED / ADDED (value rivals): weak-prepatch-raw-keying ports DIRECTLY as
#   weak-key-by-ident (key by surface `ident` instead of `canon`) — the central
#   pre-change defect, refuted on a derived view where ident ≠ canon.
#   weak-over-fetch ports as appending a spurious key (the sibling's spurious
#   inner-bucket attribute becomes a spurious sequence entry, since the inner
#   bucket is folded into the sequence carrier). weak-scatter-injection ports as
#   weak-scatter-ident (emit the canonical key AND the surface key for a derived
#   view — the "paper over the symptom" rival that keeps the canonical entry yet
#   still scatters under the raw identity). Two length rivals (weak-drop-first,
#   weak-drop-all) are ADDED to exercise the sequence/length structure the richer
#   List carrier exposes and to separate the near-miss pair at the point that
#   distinguishes them; no case was added or dropped for proof cost.
#
# WITNESS DISTINCTNESS. The five rivals probe five distinct points of the sole
#   binder `entities`: weak-key-by-ident at a derived view `[⟨2, 1⟩]` (ident ≠
#   canon — the only shape on which raw keying bites, and the exact F2P shape),
#   weak-drop-first at a two-distinct-model chain `[⟨1, 1⟩, ⟨2, 2⟩]` (where it
#   diverges from weak-drop-all, which returns empty there), weak-drop-all at the
#   singleton `[⟨1, 1⟩]`, weak-over-fetch at a plain model `[⟨7, 7⟩]`,
#   weak-scatter-ident at a derived view `[⟨5, 3⟩]`. So `entities` is varied
#   across derived-view / plain-model / length-1 / length-2, both projections
#   (`.ident` and `.canon`) take multiple values, the central `ident ≠ canon`
#   sub-domain is exercised by two rivals at distinct tokens, and the near-miss
#   pair is separated at the point that distinguishes them. pts = 5.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model (the canonical-identity normalization is
# modeled deeply in the pure region as canonOf/keysOf over the input carrier — see
# mapping.md §3), so there is nothing there to probe and the gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
