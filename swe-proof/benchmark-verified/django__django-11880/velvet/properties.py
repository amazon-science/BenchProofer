"""properties.py — G-PBT falsification battery for django__django-11880 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed — the consumer spec view elides it, so
``markers.same_spec`` holds and the ``prove_correct deepCopyField`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND the file elaborates with every obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND its
refutation ``witness`` discriminates: the witness ELABORATES against the rival
and FAILS against the frozen solution).

DEFENDED SURFACE (``deepCopyField (source : FormField) (widgetCopy : Obj)
(messagesCopy : Obj) (validatorsCopy : Obj) return (result : FormField)``):
produce an independent clone of a structured value whose components are
themselves objects observed through their IDENTITY (``Obj.ref``) and, where their
type defines value equality, their CONTENTS (``Obj.payload``). The three objects
the copy helpers produced are taken as INPUTS, each constrained by exactly its
helper's guarantee; the clone must install precisely those objects.

THREE ``require`` clauses (the admitted domain: each supplied copy meets its own
helper's guarantee and nothing more) and FOUR input binders (``source``,
``widgetCopy``, ``messagesCopy``, ``validatorsCopy``). SEVEN top-level
postcondition clauses in two layers:

    INDEPENDENCE
    (W) ensures freshDistinct result.widget        source.widget
    (E) ensures freshCopy     result.errorMessages source.errorMessages
    (V) ensures freshCopy     result.validators    source.validators
    DERIVATION
    (DW) ensures result.widget        = widgetCopy
    (DE) ensures result.errorMessages = messagesCopy
    (DV) ensures result.validators    = validatorsCopy
    PRESERVATION
    (C)  ensures result.carried       = source.carried

where ``freshDistinct b a := b.ref ≠ a.ref`` (a NEW object) and ``freshCopy b a
:= b.ref ≠ a.ref ∧ b.payload = a.payload`` (a NEW object that also reads back the
same). The battery attacks each of the seven independently, and both sub-clauses
of each ``freshCopy`` clause.

Clause (E)'s ``ref ≠`` sub-clause is the discriminator of the reported defect
(the source's override-message table must be given its OWN distinct object rather
than being held by shared reference); its faithful real counterpart is the
independent-copy step for that table, whose ABSENCE is what the F2P observes as
an identity assertion (``clone.table is not source.table``). Clauses (W) and (V)
cover the two components the routine already duplicated.

WHY THE DERIVATION LAYER EXISTS, AND WHY IT IS WHAT DEFENDS THE OPAQUE SLOT. The
rendering component is OPAQUE: its type defines no value equality, so a copy of
it reads back equal to NOTHING — not even to the object it was copied from — and
there is therefore no content observation available with which to state what that
slot must hold. An identity-only obligation on it (``freshDistinct`` alone) is
satisfied by ANY object that is not the source's: a copy whose carried state was
wrecked after the helper returned it (measured against this instance's own suite:
F2P passes, 18 PASS_TO_PASS tests FAIL), or an unrelated freshly-built component
that was never copied from anything (44 PASS_TO_PASS FAIL). Both are genuine
wrong implementations, and no CONTENT clause can catch either, because the
component has no readable content to compare. What distinguishes them is
PROVENANCE: the routine must install the object the helper HANDED BACK. That is
what (DW) says, and (DE)/(DV) say the same for the two value-typed slots, closing
post-mutation and substitution there too. Correspondingly the battery carries
reject-widget-wrecked-contents, reject-widget-unrelated-object,
reject-widget-substituted-existing-object and
reject-messages-post-mutated-identity.

THE CARRIER IS TRANSPARENT AND CONCRETE. ``Obj`` is ``{ ref : Nat, payload :
Nat }`` with ``DecidableEq`` and ``FormField`` additionally carries a fourth ``Obj``,
and both copy relations are ``@[reducible]`` so a ``Decidable`` instance for
them reduces. The method is LOOP-FREE and DETERMINISTIC (it makes no
demonic choice: the copies arrive as parameters), so every witness reaches the
post-image through Velvet's own tester machinery — ``extract_program_for`` /
``prove_precondition_decidable_for`` / ``prove_postcondition_decidable_for`` /
``derive_tester_for`` — and asserts ``deepCopyFieldTester <source> <widgetCopy>
<messagesCopy> <validatorsCopy> = false``, i.e. "the extracted program's result
violates the method's postcondition at that concrete input". Every argument is a
closed literal, so ``decide`` reduces the extracted program without getting
stuck; the witness ELABORATES against the rival (whose result really does violate
a clause there) and FAILS against the frozen solution (``decide`` proves the
tester is TRUE there, so the ``= false`` claim is refuted). Each witness input
point satisfies all three ``require`` clauses, so it is in scope. Every witness
was SEEN to discriminate with two real builds (rival EXIT 0, gold EXIT 1:
``decide proved that the proposition … is false``).

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame rivals (write / rebind the read-only source's collection held
    at ``Acc(self.X, 1/2)``) because its input is a heap object an impl can
    illegally mutate. Lean and Velvet are referentially transparent: ``source``
    is an immutable value, this bundle declares NO ``mut`` binder, there is no
    heap and no aliasing — there is no read-only input to overwrite and no
    substitute probe to build. Not fabricated (per the porting map, VACUOUS here).
  * VALUE / CONTENT rivals (alias a collection; copy the wrong contents) — the
    nagini uniqueness rivals live here. They PORT: each is re-expressed against
    the frozen spec and refuted at a concrete input point where the attacked
    clause is false.
  * UNGROUNDED-ORACLE ECHO — PORTED AND SHIPPED as
    reject-synthesised-not-installed. An echo here is an impl that never touches
    the supplied copies and instead SYNTHESISES an object per slot by arithmetic
    on ``source`` that happens to satisfy every ``freshDistinct``/``freshCopy``
    relation. It derives its answer from the arguments without doing the work,
    and the DERIVATION layer is what refutes it.

TOTAL CORRECTNESS. The bundle is checked under ``set_option
loom.semantics.termination "total"`` AND ``open TotalCorrectness DemonicChoice``
— the ``open`` is what selects the semantics, so the two must agree (a ``total``
option under a partial ``open`` reads as total and enforces partial). The method
is loop-free, so no ``decreasing`` measure arises; and because the copies arrive
as PARAMETERS rather than through a demonic ``:|`` choice, no satisfiability
goal arises either — the frozen proof is a bare ``loom_solve``. Every case below
inherits that; see ``_PROOF_UNFOLD`` for why some rivals carry one extra line.

AXIOM lane: DROPPED (``AXIOM_TESTS = []``). The copy-helper contracts carried by
the three ``require`` clauses are G-AX-validated against the real copy callees
(``dict.copy`` / ``list[:]`` / ``copy.deepcopy``) by axiom_check.py; the G-PBT
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11880"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen deepCopyField impl body (the shallow
# ---- duplication, the three installs of the supplied copies, and the return). It
# ---- lies wholly inside the single -- impl-start / -- impl-end region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap), so each
# ---- edit keeps same_spec by construction and leaves the frozen
# ---- `prove_correct deepCopyField` STATEMENT intact.
_IMPL = (
    "    -- Start from a shallow duplication of the field: the clone initially holds\n"
    "    -- the very same attribute objects as the source (duplicating the field\n"
    "    -- copies the references, not the objects they point at).\n"
    "    let mut result := source\n"
    "    -- Install, in each slot, PRECISELY the object that slot's copy helper\n"
    "    -- returned — the opaque rendering component's copy, the override-message\n"
    "    -- table's copy, the validator collection's copy — with nothing interposed\n"
    "    -- and nothing altered afterwards.\n"
    "    result := { result with widget := widgetCopy }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "deepCopyField impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY deepCopyField's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate, so
# ---- a witness reaches the post-image through Velvet's own tester machinery:
# ---- `deepCopyFieldTester source widgetCopy messagesCopy validatorsCopy = false`
# ---- says the extracted program's result violates the method's postcondition at
# ---- that concrete input point. Checked in a file whose `prove_correct` block has
# ---- been stripped and replaced by the tester derivation. Every argument is a
# ---- closed literal and the method is loop-free and choice-free, so `decide`
# ---- reduces the extracted program; the two copy relations are `@[reducible]` in
# ---- the frozen file, which is what lets the derived `Decidable` instance reduce.
def _witness(src, wc, mc, vc):
    return (
        "\n"
        "extract_program_for deepCopyField\n"
        "prove_precondition_decidable_for deepCopyField\n"
        "prove_postcondition_decidable_for deepCopyField\n"
        "derive_tester_for deepCopyField\n\n"
        f"example : deepCopyFieldTester {src} {wc} {mc} {vc} = false := by\n"
        "  decide\n"
    )


# ---- reject impl bodies (each shares the frozen spec; only the impl differs) ----

# hold the rendering component by shared reference: the shallow duplication
# already hands it over, and the rival never installs the supplied copy, so
# `result.widget = source.widget` (the same object).
_ALIAS_WIDGET = (
    "    let mut result := source\n"
    "    -- hold the rendering component by the shared reference the shallow\n"
    "    -- duplication handed over, instead of installing the copy that was made.\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# hold the override-message table by shared reference: the behavior under audit.
# The shallow duplication hands it over and the rival never installs its copy, so
# `result.errorMessages = source.errorMessages` (the same object).
_ALIAS_EM = (
    "    let mut result := source\n"
    "    result := { result with widget := widgetCopy }\n"
    "    -- (no copy of the override-message table is installed — the shared\n"
    "    -- reference the shallow duplication handed over is kept)\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# hold the validator collection by shared reference: install the table's copy
# correctly but leave the validators shared.
_ALIAS_VAL = (
    "    let mut result := source\n"
    "    result := { result with widget := widgetCopy }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    -- (no copy of the validator collection is installed — left shared)\n"
    "    return result"
)

# give the override-message table a DISTINCT object with the WRONG contents:
# distinct identity holds, but the payload is mangled, so `freshCopy`'s content
# sub-clause `payload =` fails (and so does the derivation clause).
_WRONG_PAY_EM = (
    "    let mut result := source\n"
    "    result := { result with widget := widgetCopy }\n"
    "    -- distinct object, but the contents are NOT preserved (payload mangled)\n"
    "    result := { result with errorMessages := "
    "{ ref := source.errorMessages.ref + 1, payload := source.errorMessages.payload + 1 } }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# symmetric content attack on the validator collection.
_WRONG_PAY_VAL = (
    "    let mut result := source\n"
    "    result := { result with widget := widgetCopy }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    -- distinct object, but the contents are NOT preserved (payload mangled)\n"
    "    result := { result with validators := "
    "{ ref := source.validators.ref + 1, payload := source.validators.payload + 1 } }\n"
    "    return result"
)

# ---- the OPAQUE-SLOT PROVENANCE family: the three rivals that motivate the
# ---- DERIVATION clause (DW). Each leaves every independence sub-clause intact
# ---- and shares nothing with the source, so an identity-only obligation on the
# ---- rendering component admits all three; and none can be caught by a content
# ---- clause, because that component HAS no readable content. Measured against
# ---- this instance's real test suite: the first fails 18 PASS_TO_PASS tests, the
# ---- second 44, while both pass the F2P — so each is a genuine wrong
# ---- implementation that (DW), and nothing else, catches.

# the copy helper IS invoked on the source's rendering component (so the supplied
# `widgetCopy` is a real copy), and then that fresh object is altered before being
# installed: what lands in the slot is NOT what the helper handed back.
_WIDGET_WRECKED = (
    "    let mut result := source\n"
    "    -- the copy that was made IS used, then altered before it is installed\n"
    "    -- (identity kept distinct; what the helper produced is not what lands)\n"
    "    result := { result with widget := { widgetCopy with payload := 0 } }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# the supplied copy is IGNORED: the clone is handed a brand-new UNRELATED object,
# built from scratch rather than copied from anything. Distinct from the source's,
# so the independence clause holds, but it is not what any helper produced.
_WIDGET_UNRELATED = (
    "    let mut result := source\n"
    "    -- the copy that was made is ignored: an unrelated object is built from\n"
    "    -- scratch and put in its place (distinct, but copied from nothing).\n"
    "    result := { result with widget := "
    "{ ref := source.widget.ref + 1, payload := source.widget.payload } }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# the supplied copy is ignored and an EXISTING object is reused: the source's own
# override-message table is put in the rendering-component slot. It is distinct
# from the source's rendering component, so the independence clause holds, and it
# is even an object that genuinely exists in the source — but it is not what the
# rendering component's copy helper handed back.
_WIDGET_SUBSTITUTED = (
    "    let mut result := source\n"
    "    -- reuse an EXISTING object (the source's own override-message table) in\n"
    "    -- the rendering-component slot instead of installing the copy made for it.\n"
    "    result := { result with widget := source.errorMessages }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# post-mutate the identity of a VALUE-TYPED copy: the copy helper's answer is
# taken, its contents kept, and its identity changed before installation. Both
# sub-clauses of the independence clause (E) still hold — distinct from the
# source's, equal contents — so only the derivation clause (DE) catches it.
_EM_POST_MUTATED = (
    "    let mut result := source\n"
    "    result := { result with widget := widgetCopy }\n"
    "    -- the copy made for the table is taken and then re-identified: same\n"
    "    -- contents, a different object from the one the helper handed back.\n"
    "    result := { result with errorMessages := "
    "{ messagesCopy with ref := messagesCopy.ref + 1 } }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# UNGROUNDED-ORACLE ECHO: never touch the supplied copies at all. Synthesise one
# object per slot by arithmetic on `source` — a bumped identity carrying the
# source's contents — which satisfies every independence clause by construction.
# The answer is derived from the arguments without the work being done.
_SYNTHESISED = (
    "    let mut result := source\n"
    "    -- none of the copies that were made is used: each slot is filled with an\n"
    "    -- object synthesised from the source so the relations hold by arithmetic.\n"
    "    result := { result with widget := "
    "{ ref := source.widget.ref + 1, payload := source.widget.payload } }\n"
    "    result := { result with errorMessages := "
    "{ ref := source.errorMessages.ref + 1, payload := source.errorMessages.payload } }\n"
    "    result := { result with validators := "
    "{ ref := source.validators.ref + 1, payload := source.validators.payload } }\n"
    "    return result"
)

# CROSS-WIRED installs: every supplied copy IS installed, but two of them land in
# each other's slots. Nothing is shared with the source and each installed object
# is a genuine copy of SOMETHING, so every independence sub-clause on the two
# value-typed slots would be satisfied were their contents alike; the derivation
# clauses pin WHICH copy belongs where.
_CROSSWIRED = (
    "    let mut result := source\n"
    "    result := { result with widget := widgetCopy }\n"
    "    -- cross-wire the two value-typed installs: the table's slot receives the\n"
    "    -- validator collection's copy, and the validators' slot the table's.\n"
    "    result := { result with errorMessages := validatorsCopy }\n"
    "    result := { result with validators := messagesCopy }\n"
    "    return result"
)

# CROSS-WIRED across the opaque slot: the rendering component's slot receives the
# override-message table's copy and vice versa. Every slot holds a fresh object
# that is a real copy of something and nothing is shared, so this probes
# slot-to-helper provenance on the opaque slot, which no content clause can reach.
_CROSSWIRED_WIDGET = (
    "    let mut result := source\n"
    "    -- cross-wire the opaque slot with the table's slot: each receives a\n"
    "    -- genuine copy, of the other one's component.\n"
    "    result := { result with widget := messagesCopy }\n"
    "    result := { result with errorMessages := widgetCopy }\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    return result"
)

# DISCARD THE SHALLOW DUPLICATION: build the clone from a bare record literal,
# installing all three copies correctly but supplying a component the shallow
# duplication would have carried over from its own default rather than from the
# source. Every copy clause holds; only the preservation clause (C) catches it.
_REBUILT_FROM_SCRATCH = (
    "    -- do not start from a shallow duplication: construct the clone from\n"
    "    -- scratch, installing the three copies but RECONSTRUCTING the rest of the\n"
    "    -- field's state instead of handing over the source's own.\n"
    "    return { widget := widgetCopy, errorMessages := messagesCopy,\n"
    "             validators := validatorsCopy,\n"
    "             carried := { ref := source.carried.ref + 1,\n"
    "                          payload := source.carried.payload } }"
)

# ---- positive (correct) reshapes ------------------------------------------

# structurally-different CORRECT reshape: install the three copies in the REVERSE
# order. Observationally identical to the frozen body, so every clause discharges
# and the frozen `loom_solve` closes it.
_REORDER = (
    "    let mut result := source\n"
    "    -- reshape: install the three copies in the reverse order.\n"
    "    result := { result with validators := validatorsCopy }\n"
    "    result := { result with errorMessages := messagesCopy }\n"
    "    result := { result with widget := widgetCopy }\n"
    "    return result"
)

# a SECOND correct reshape: build the clone in ONE record literal, with no
# shallow-duplication seed and no sequential `{ result with ... }` updates at all.
# A genuinely different impl shape — the frozen body's whole skeleton is gone —
# that still installs each copy in its slot and carries the preserved component
# over from the source explicitly.
_ONE_RECORD = (
    "    -- reshape: build the clone in ONE record literal (no shallow-duplication\n"
    "    -- seed, no sequential updates), carrying the preserved component over\n"
    "    -- from the source explicitly.\n"
    "    return { widget := widgetCopy, errorMessages := messagesCopy,\n"
    "             validators := validatorsCopy, carried := source.carried }"
)

# ---- admissibility probe (see the admiss case below) ------------------------
# An in-region `assert` discharged at a CONCRETE F2P-shaped tuple: a source field,
# and the three objects the copy helpers produced for it. Prepended to the frozen
# impl body, so the method's own seven `ensures` still discharge verbatim and the
# assert is an ADDITIONAL live obligation. Its conjuncts are the three `require`
# clauses AND the seven post clauses instantiated at that concrete tuple (with the
# honest clone being the record built from those three copies), PLUS the negative
# companion (the source's own table is NOT an independent copy of itself), which
# is what makes the discharge non-degenerate rather than a clause that holds of
# anything. Each conjunct was measured LIVE: negating any one leaves
# `unsolved goals ... admiss_1 ... ⊢ False`.
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss\n"
    "      (freshDistinct (⟨31, 9⟩ : Obj) (⟨0, 0⟩ : Obj) ∧\n"
    "       freshCopy     (⟨32, 5⟩ : Obj) (⟨1, 5⟩ : Obj) ∧\n"
    "       freshCopy     (⟨33, 7⟩ : Obj) (⟨2, 7⟩ : Obj) ∧\n"
    "       freshDistinct (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).widget        "
    "(⟨⟨0, 0⟩, ⟨1, 5⟩, ⟨2, 7⟩, ⟨200, 1⟩⟩ : FormField).widget ∧\n"
    "       freshCopy     (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).errorMessages "
    "(⟨⟨0, 0⟩, ⟨1, 5⟩, ⟨2, 7⟩, ⟨200, 1⟩⟩ : FormField).errorMessages ∧\n"
    "       freshCopy     (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).validators    "
    "(⟨⟨0, 0⟩, ⟨1, 5⟩, ⟨2, 7⟩, ⟨200, 1⟩⟩ : FormField).validators ∧\n"
    "       (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).widget        = (⟨31, 9⟩ : Obj) ∧\n"
    "       (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).errorMessages = (⟨32, 5⟩ : Obj) ∧\n"
    "       (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).validators    = (⟨33, 7⟩ : Obj) ∧\n"
    "       (⟨⟨31, 9⟩, ⟨32, 5⟩, ⟨33, 7⟩, ⟨200, 1⟩⟩ : FormField).carried       = "
    "(⟨⟨0, 0⟩, ⟨1, 5⟩, ⟨2, 7⟩, ⟨200, 1⟩⟩ : FormField).carried ∧\n"
    "       ¬ freshCopy (⟨⟨0, 0⟩, ⟨1, 5⟩, ⟨2, 7⟩, ⟨200, 1⟩⟩ : FormField).errorMessages   "
    "(⟨⟨0, 0⟩, ⟨1, 5⟩, ⟨2, 7⟩, ⟨200, 1⟩⟩ : FormField).errorMessages))\n"
)

# The frozen proof script, verbatim. The method makes no demonic choice (the
# copies arrive as parameters), so there is no satisfiability goal and a bare
# `loom_solve` closes the frozen body.
_PROOF = "prove_correct deepCopyField by\n  loom_solve"

# The admissibility case adds an in-region `assert`, whose VC the frozen script
# alone does NOT close (measured: EXIT 1, `unsolved goals ... admiss_1`), so that
# case REPROVES with one extra step. variant_scope permits a variant to reprove —
# only the obligation's STATEMENT is frozen — and the extra step is what makes the
# assert a real obligation rather than something the solver was already
# discharging.
_PROOF_RETUNED = (
    "prove_correct deepCopyField by\n"
    "  loom_solve\n"
    "  all_goals try simp_all [freshDistinct, freshCopy]"
)

# A rival whose result is built by a record UPDATE literal or a bare record
# literal can leave the frozen tactic with a residual goal it declines to unfold
# (the goal IS the hypothesis, modulo unfolding the literal) — a PROOF-AUTOMATION
# residual, not a semantic rejection. Recording such a build as "the spec rejects
# it" would invent spec strength that is not there, so every rival that writes a
# literal into a slot is proved with one extra closing line that unfolds those
# literals. It closes only goals that are actually TRUE: each such rival still
# FAILS, on the clause named in its rationale, and the aliasing rivals carry the
# frozen script without becoming provable. variant_scope permits the differing
# tactic body (the obligation STATEMENT and the method header are what must be
# preserved; same_spec confirms they are), and it introduces no axiom, no sorry
# and no new theorem.
_PROOF_UNFOLD = (
    "prove_correct deepCopyField by\n"
    "  loom_solve <;> simp_all [freshDistinct, freshCopy]"
)


def _impl_unfold(new_impl):
    """A rival body PLUS the residual-unfolding proof line (see _PROOF_UNFOLD)."""
    return _swap(_impl(new_impl), _PROOF, _PROOF_UNFOLD)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # `pos-reorder` ARGUMENT ("a faithful, structurally-different correct
    # duplication must verify") onto this carrier: install the three copies in
    # the REVERSE order. Each slot still receives its own copy, so all seven
    # clauses discharge and the frozen `loom_solve` closes it unchanged.
    # =====================================================================
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_REORDER),
        "rationale": "PASS SOURCE = W ∧ E ∧ V ∧ DW ∧ DE ∧ DV ∧ P. Installing the "
                     "validator collection's copy, the override-message table's "
                     "copy and the rendering component's copy in the reverse order "
                     "still puts precisely each helper's answer in its own slot, so "
                     "the three independence clauses, the three derivation clauses "
                     "and the preservation clause all still discharge — the frozen "
                     "`prove_correct` body closes it verbatim. A "
                     "structurally-different faithful reshape MUST verify; if it "
                     "cannot, the postcondition over-constrains the impl SHAPE "
                     "(SPEC-TOO-STRONG). Verified out-of-band (EXIT 0).",
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition must ADMIT a normal input, and the
    # post-image at that input must be SATISFIABLE and NON-DEGENERATE. This
    # bundle DOES declare three `require` clauses (each supplied copy meets its
    # helper's guarantee), so the nagini `admiss` probe ports directly and gains
    # the post-image half as well: a spec whose domain is empty, or one every
    # value satisfies, reads exactly like a spec every impl satisfies.
    #
    # Discharged as an in-region `assert` at a CONCRETE F2P-shaped tuple — source
    # ⟨⟨0,0⟩,⟨1,5⟩,⟨2,7⟩,true⟩ with helper answers ⟨31,9⟩ (the opaque copy: a
    # distinct object, no content claim), ⟨32,5⟩ and ⟨33,7⟩ (distinct objects with
    # the sources' contents) — showing the three `require` clauses HOLD there
    # (the domain is non-empty at an F2P-shaped point) and that the honest clone
    # built from those answers JOINTLY satisfies all seven post clauses, while the
    # source's own table is NOT an independent copy of itself (the negative
    # companion: the clauses are not clauses that hold of anything). The frozen
    # impl body follows verbatim so the method's own seven `ensures` still
    # discharge. The assert VC is LIVE: the frozen proof script alone fails on it
    # (EXIT 1, `unsolved goals ... admiss_1`), so the one extra `simp_all` step is
    # doing real work, and negating any single conjunct leaves `⊢ False`.
    # =====================================================================
    {
        "id": "admiss-f2p-domain-and-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _IMPL, _ADMISS_ASSERT + _IMPL),
                        _PROOF, _PROOF_RETUNED),
        "rationale": "PASS SOURCE = the admitted domain is NON-EMPTY at an "
                     "F2P-shaped input AND the post-image there is SATISFIABLE and "
                     "NON-DEGENERATE. At source ⟨⟨0,0⟩,⟨1,5⟩,⟨2,7⟩,true⟩ the "
                     "helper answers ⟨31,9⟩ / ⟨32,5⟩ / ⟨33,7⟩ satisfy the three "
                     "`require` clauses (freshDistinct on the opaque copy, "
                     "freshCopy on the two value-typed ones), so the precondition "
                     "admits a normal input; the clone "
                     "⟨⟨31,9⟩,⟨32,5⟩,⟨33,7⟩,true⟩ then satisfies W, E, V, DW, DE, "
                     "DV and P ALL AT ONCE, so the seven clauses cannot conflict; "
                     "and the final conjunct shows E is FALSE of the source's own "
                     "table against itself, so it is not a clause every value "
                     "satisfies. If this assert could not discharge, the obligation "
                     "would be out of scope, unsatisfiable or degenerate at exactly "
                     "the shape the change is about — a false pass everywhere. Each "
                     "conjunct measured live (negating any one leaves `⊢ False`).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input point that satisfies all three `require` clauses. They attack
    # ALL SEVEN top-level clauses and, for the two `freshCopy` clauses, both
    # sub-clauses. Each input point is DISTINCT across the reject cases, so every
    # one of the four input binders is varied.
    # =====================================================================

    # ---- (W) the clone's rendering component must be a DISTINCT object ----
    {
        "id": "reject-alias-widget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALIAS_WIDGET),
        "refinement": "holds the rendering component by the shared reference the "
                      "shallow duplication handed over, never installing the copy "
                      "that was made for it. An implementation that dropped that "
                      "install would let a change reached through one field's "
                      "rendering component be observed through every clone of that "
                      "field — the exact cross-clone leakage this routine exists to "
                      "prevent. This instance's suite exercises it directly: tests "
                      "that set a rendering attribute on one form's field and read "
                      "it back off another form's field would surface the change; "
                      "it does NOT resolve.",
        "rationale": "REJECT from W (freshDistinct result.widget source.widget ⇒ "
                     "ref ≠) and from DW (result.widget = widgetCopy): the rival "
                     "leaves result.widget = source.widget, so both are FALSE. "
                     "Witnessed at source = ⟨⟨3,3⟩,⟨4,8⟩,⟨5,9⟩,true⟩ with helper "
                     "answers ⟨40,3⟩, ⟨41,8⟩, ⟨42,9⟩ (all three `require` clauses "
                     "hold): the rival's run leaves result.widget = ⟨3,3⟩ = "
                     "source.widget (W and DW false); the frozen solution installs "
                     "⟨40,3⟩ (both true, so `decide` proves the tester TRUE and the "
                     "`= false` claim is refuted there).",
        "witness": _witness("⟨⟨3,3⟩, ⟨4,8⟩, ⟨5,9⟩, ⟨200, 1⟩⟩",
                            "⟨40,3⟩", "⟨41,8⟩", "⟨42,9⟩"),
    },

    # ---- (E, ref ≠) the clone's override-message table must be a DISTINCT
    # ---- object — this is the PRE-PATCH bug (nagini alias-msg) ----
    {
        "id": "reject-alias-errormessages",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALIAS_EM),
        "refinement": "the override-message table is left as the shallow-copy "
                      "alias, with the copy made for it never installed. A real "
                      "patch that duplicated the field object but re-shared its "
                      "override-message table would leave the clone's table the "
                      "SAME object as the source's, so the F2P identity assertion "
                      "(the clone's table is not the source's table) stays RED. It "
                      "does NOT resolve.",
        "rationale": "REJECT from E's distinct-identity sub-clause (freshCopy "
                     "result.errorMessages source.errorMessages ⇒ ref ≠) and from "
                     "DE (result.errorMessages = messagesCopy): the rival leaves "
                     "result.errorMessages = source.errorMessages. Witnessed at "
                     "source = ⟨⟨0,0⟩,⟨1,5⟩,⟨2,7⟩,true⟩ with helper answers "
                     "⟨50,4⟩, ⟨51,5⟩, ⟨52,7⟩: the rival's run leaves "
                     "result.errorMessages = ⟨1,5⟩ = source.errorMessages (E and DE "
                     "false); the frozen solution installs ⟨51,5⟩ (both true). This "
                     "is the load-bearing clause the change adds (G-DIFF "
                     "discriminator).",
        "witness": _witness("⟨⟨0,0⟩, ⟨1,5⟩, ⟨2,7⟩, ⟨200, 1⟩⟩",
                            "⟨50,4⟩", "⟨51,5⟩", "⟨52,7⟩"),
    },

    # ---- (V, ref ≠) the clone's validator collection must be a DISTINCT object
    # ---- (nagini alias-validators) ----
    {
        "id": "reject-alias-validators",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALIAS_VAL),
        "refinement": "installs the override-message table's copy correctly but "
                      "leaves the validator collection shared by reference. A real "
                      "patch that fixed the table but re-shared the validators "
                      "would leak validator mutations across clones of the same "
                      "field — the P2P validator-independence test asserts "
                      "validators are independent across copies; it does NOT "
                      "resolve. Guards against a wrong impl fixing only one "
                      "collection while re-sharing the other.",
        "rationale": "REJECT from V's distinct-identity sub-clause (freshCopy "
                     "result.validators source.validators ⇒ ref ≠) and from DV "
                     "(result.validators = validatorsCopy): the rival leaves "
                     "result.validators = source.validators. Witnessed at source = "
                     "⟨⟨6,1⟩,⟨7,2⟩,⟨8,4⟩,false⟩ with helper answers ⟨60,3⟩, "
                     "⟨61,2⟩, ⟨62,4⟩: the rival's run leaves result.validators = "
                     "⟨8,4⟩ = source.validators (V and DV false); the frozen "
                     "solution installs ⟨62,4⟩ (both true).",
        "witness": _witness("⟨⟨6,1⟩, ⟨7,2⟩, ⟨8,4⟩, ⟨200, 1⟩⟩",
                            "⟨60,3⟩", "⟨61,2⟩", "⟨62,4⟩"),
    },

    # ---- (E, payload =) the clone's override-message table must hold EQUAL
    # ---- contents — content-level attack (nagini wrong-value / drop-last-msg) ----
    {
        "id": "reject-wrong-payload-errormessages",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_WRONG_PAY_EM),
        "refinement": "builds a DISTINCT object for the override-message table "
                      "(identity guarantee satisfied) but mangles its CONTENTS. A "
                      "real patch that copied the table into a fresh object but "
                      "altered the entries would produce clones whose override "
                      "messages differ from the source's — error-message-content "
                      "P2P tests read the copied messages and would break. It DOES "
                      "pass the F2P identity assertion, which is why the content "
                      "sub-clause, not the identity sub-clause, must catch it; it "
                      "does NOT resolve.",
        "rationale": "REJECT from E's content sub-clause (freshCopy "
                     "result.errorMessages source.errorMessages ⇒ payload =) and "
                     "from DE: the rival gives result.errorMessages a distinct ref "
                     "(identity OK) but bumps its payload. Witnessed at source = "
                     "⟨⟨9,2⟩,⟨10,6⟩,⟨11,3⟩,true⟩ with helper answers ⟨70,1⟩, "
                     "⟨71,6⟩, ⟨72,3⟩: the rival's run gives "
                     "result.errorMessages = ⟨11,7⟩, payload 7 ≠ 6 = "
                     "source.errorMessages.payload (E false, DE false); the frozen "
                     "solution installs ⟨71,6⟩ (both true). Attacks E's OTHER "
                     "sub-clause from reject-alias-errormessages.",
        "witness": _witness("⟨⟨9,2⟩, ⟨10,6⟩, ⟨11,3⟩, ⟨200, 1⟩⟩",
                            "⟨70,1⟩", "⟨71,6⟩", "⟨72,3⟩"),
    },

    # ---- (V, payload =) the clone's validator collection must hold EQUAL
    # ---- contents — symmetric content attack ----
    {
        "id": "reject-wrong-payload-validators",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_WRONG_PAY_VAL),
        "refinement": "builds a DISTINCT object for the validator collection but "
                      "mangles its contents. A real patch that sliced the validator "
                      "list into a fresh object but altered its elements would "
                      "produce clones whose validators differ from the source's, "
                      "breaking any test that relies on the copied validators being "
                      "equal to the originals; it does NOT resolve.",
        "rationale": "REJECT from V's content sub-clause (freshCopy "
                     "result.validators source.validators ⇒ payload =) and from DV: "
                     "the rival gives result.validators a distinct ref but bumps "
                     "its payload. Witnessed at source = "
                     "⟨⟨12,5⟩,⟨13,1⟩,⟨14,8⟩,false⟩ with helper answers ⟨80,2⟩, "
                     "⟨81,1⟩, ⟨82,8⟩: the rival's run gives result.validators = "
                     "⟨15,9⟩, payload 9 ≠ 8 = source.validators.payload (V false, "
                     "DV false); the frozen solution installs ⟨82,8⟩ (both true). "
                     "Attacks V's OTHER sub-clause from reject-alias-validators.",
        "witness": _witness("⟨⟨12,5⟩, ⟨13,1⟩, ⟨14,8⟩, ⟨200, 1⟩⟩",
                            "⟨80,2⟩", "⟨81,1⟩", "⟨82,8⟩"),
    },

    # =====================================================================
    # THE OPAQUE-SLOT PROVENANCE FAMILY. Every rival above breaks a clause by
    # SHARING an object or by mangling the CONTENTS of a value-typed one. Neither
    # move is available on the rendering component: its type defines no value
    # equality, so it has no readable contents to mangle and no content clause
    # can constrain what its slot holds. The three rivals below exploit exactly
    # that gap — each leaves every independence sub-clause intact and shares
    # nothing with the source, so an identity-only obligation on that slot admits
    # all three. Measured against this instance's own suite: the first fails 18
    # PASS_TO_PASS tests and the second 44, while both pass the F2P. They are
    # what makes the DERIVATION clause (DW) load-bearing rather than decorative.
    # =====================================================================
    {
        "id": "reject-widget-wrecked-contents",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_WIDGET_WRECKED),
        "refinement": "uses the copy that was made of the source's rendering "
                      "component — so the clone's is a distinct object, and nothing "
                      "is shared with the source — and then alters that fresh "
                      "object before installing it, discarding the state it "
                      "carried. An implementation that duplicated the component and "
                      "then wiped what it holds gives every clone a component that "
                      "renders differently from the one it was cloned from: the "
                      "attributes a caller set are gone from every copy of that "
                      "field. It DOES satisfy the identity assertion the reported "
                      "defect is about. Measured on this instance's suite: F2P "
                      "passes, 18 PASS_TO_PASS tests FAIL; it does NOT resolve.",
        "rationale": "REJECT from DW (result.widget = widgetCopy): what lands in "
                     "the slot is `{ widgetCopy with payload := 0 }`, not "
                     "`widgetCopy`, so DW is FALSE whenever the copy carries "
                     "anything. Witnessed at source = ⟨⟨18,6⟩,⟨19,3⟩,⟨20,1⟩,true⟩ "
                     "with helper answers ⟨21,9⟩, ⟨22,3⟩, ⟨23,1⟩: the rival's run "
                     "gives result.widget = ⟨21,0⟩ ≠ ⟨21,9⟩ = widgetCopy (DW "
                     "false) while result.widget.ref = 21 ≠ 18 (W HOLDS); the "
                     "frozen solution installs ⟨21,9⟩ (DW true). Attacks the ONLY "
                     "clause that can constrain the opaque slot — no content "
                     "sub-clause exists there to attack, which is the point.",
        "witness": _witness("⟨⟨18,6⟩, ⟨19,3⟩, ⟨20,1⟩, ⟨200, 1⟩⟩",
                            "⟨21,9⟩", "⟨22,3⟩", "⟨23,1⟩"),
    },

    {
        "id": "reject-widget-unrelated-object",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_WIDGET_UNRELATED),
        "refinement": "ignores the copy that was made and builds an unrelated "
                      "object from scratch for the rendering component's slot. "
                      "Distinct from the source's, so nothing is shared and the "
                      "identity guarantee is met, but it was copied from nothing. "
                      "An implementation that replaced the component rather than "
                      "duplicating it would give every clone a component unrelated "
                      "to the field's own — a different kind, a different "
                      "rendering, none of the configured attributes. Measured on "
                      "this instance's suite: F2P passes, 44 PASS_TO_PASS tests "
                      "FAIL; it does NOT resolve. Distinct from "
                      "reject-widget-wrecked-contents in PROVENANCE, not just "
                      "degree: there the copy helper's answer is used and then "
                      "damaged, here it is never used at all, so a spec that "
                      "pinned only 'the installed object differs from the copy' "
                      "would still admit one of the two. Note the fabricated "
                      "object here carries the SOURCE's own contents, so it is not "
                      "reachable by any payload-based clause either.",
        "rationale": "REJECT from DW (result.widget = widgetCopy): the fabricated "
                     "object is ⟨source.widget.ref + 1, source.widget.payload⟩, "
                     "which is not `widgetCopy`. Witnessed at source = "
                     "⟨⟨21,4⟩,⟨22,8⟩,⟨23,5⟩,false⟩ with helper answers ⟨90,7⟩, "
                     "⟨91,8⟩, ⟨92,5⟩: the rival's run gives result.widget = "
                     "⟨22,4⟩ ≠ ⟨90,7⟩ = widgetCopy (DW false) while "
                     "result.widget.ref = 22 ≠ 21 (W HOLDS) and its payload EQUALS "
                     "the source's; the frozen solution installs ⟨90,7⟩ (DW true).",
        "witness": _witness("⟨⟨21,4⟩, ⟨22,8⟩, ⟨23,5⟩, ⟨200, 1⟩⟩",
                            "⟨90,7⟩", "⟨91,8⟩", "⟨92,5⟩"),
    },

    {
        "id": "reject-widget-substituted-existing-object",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_WIDGET_SUBSTITUTED),
        "refinement": "ignores the copy that was made and reuses an EXISTING "
                      "object — the source's own override-message table — in the "
                      "rendering component's slot. It is distinct from the source's "
                      "rendering component, so the identity guarantee is met, and "
                      "it is an object that genuinely exists in the source rather "
                      "than a fabricated one, so it is not reachable by any "
                      "'nothing was copied' reading either. An implementation that "
                      "put some other live object in that slot would give every "
                      "clone a component that is not a rendering component at all; "
                      "it does NOT resolve. Third distinct provenance failure on "
                      "the opaque slot: the answer is damaged (wrecked), fabricated "
                      "(unrelated), or SUBSTITUTED (this one).",
        "rationale": "REJECT from DW (result.widget = widgetCopy): the slot holds "
                     "`source.errorMessages`, not `widgetCopy`. Witnessed at "
                     "source = ⟨⟨24,7⟩,⟨25,2⟩,⟨26,9⟩,true⟩ with helper answers "
                     "⟨100,6⟩, ⟨101,2⟩, ⟨102,9⟩: the rival's run gives "
                     "result.widget = ⟨25,2⟩ ≠ ⟨100,6⟩ = widgetCopy (DW false) "
                     "while result.widget.ref = 25 ≠ 24 (W HOLDS); the frozen "
                     "solution installs ⟨100,6⟩ (DW true). At the witness point DW "
                     "is what refutes it. (Over the whole domain the verifier also "
                     "cannot discharge W for this rival, since nothing forbids the "
                     "substituted object's identity from coinciding with the "
                     "source's rendering component — the build reports both "
                     "ensures_4 and ensures_7. The witness pins the DW-only "
                     "refutation.)",
        "witness": _witness("⟨⟨24,7⟩, ⟨25,2⟩, ⟨26,9⟩, ⟨200, 1⟩⟩",
                            "⟨100,6⟩", "⟨101,2⟩", "⟨102,9⟩"),
    },

    # =====================================================================
    # POST-MUTATION ON A VALUE-TYPED SLOT. The provenance family above is aimed
    # at the opaque slot, where no content clause exists. This rival shows the
    # derivation layer is load-bearing on the value-typed slots too: it takes the
    # copy the helper made for the table, keeps its contents, and changes its
    # identity before installing it. BOTH sub-clauses of E still hold — the
    # installed object is distinct from the source's table and reads back the
    # same — so E cannot catch it; only DE can.
    # =====================================================================
    {
        "id": "reject-messages-post-mutated-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_EM_POST_MUTATED),
        "refinement": "takes the copy that was made of the override-message table "
                      "and re-identifies it before installing: same entries, but a "
                      "different object from the one the copy helper handed back. "
                      "An implementation that copied the table and then swapped the "
                      "result for a second, separately-allocated equal table would "
                      "leave the memo bookkeeping and any other reference to the "
                      "helper's answer pointing at an object the clone does not "
                      "hold, so a later mutation reached through the copy the "
                      "routine actually made is invisible through the clone. It "
                      "passes the F2P identity assertion and every content check; "
                      "it does NOT resolve.",
        "rationale": "REJECT from DE (result.errorMessages = messagesCopy): the "
                     "slot holds `{ messagesCopy with ref := messagesCopy.ref + 1 }`, "
                     "not `messagesCopy`. Witnessed at source = "
                     "⟨⟨27,1⟩,⟨28,4⟩,⟨29,6⟩,false⟩ with helper answers ⟨110,3⟩, "
                     "⟨111,4⟩, ⟨112,6⟩: the rival's run gives "
                     "result.errorMessages = ⟨112,4⟩ ≠ ⟨111,4⟩ = messagesCopy (DE "
                     "false) while BOTH sub-clauses of E hold (112 ≠ 28 and payload "
                     "4 = 4); the frozen solution installs ⟨111,4⟩ (DE true). At "
                     "the witness point this is the only rival refuted by a "
                     "derivation clause on a slot whose independence clause is "
                     "FULLY satisfied — which is the property it exists to "
                     "demonstrate. (Over the whole domain the verifier also cannot "
                     "discharge E for it, since nothing forbids the re-identified "
                     "object's bumped identity from coinciding with the source "
                     "table's; the build reports both ensures_3 and ensures_6. The "
                     "witness pins the DE-only refutation.)",
        "witness": _witness("⟨⟨27,1⟩, ⟨28,4⟩, ⟨29,6⟩, ⟨200, 1⟩⟩",
                            "⟨110,3⟩", "⟨111,4⟩", "⟨112,6⟩"),
    },

    # =====================================================================
    # UNGROUNDED-ORACLE ECHO. An impl that never touches the supplied copies and
    # instead synthesises, per slot, an object whose identity is the source's
    # bumped and whose contents are the source's — so every independence clause
    # holds by ARITHMETIC on the arguments, with none of the work done. This is
    # the echo class: the answer is derived from the inputs rather than produced.
    # =====================================================================
    {
        "id": "reject-synthesised-not-installed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_SYNTHESISED),
        "refinement": "makes no use of any copy that was made: it fills all three "
                      "slots with objects computed from the source, each carrying "
                      "the source's contents under a bumped identity, so every "
                      "distinctness and content relation holds by construction. An "
                      "implementation like this never calls the copy helpers at "
                      "all — for the two value-typed components it would have to "
                      "reconstruct equal ones from nothing, and for the opaque "
                      "rendering component there is nothing to reconstruct, so what "
                      "the clone gets is an object of the wrong kind that merely "
                      "reports the right relations. Every clause that speaks only "
                      "of relations between the clone and the source is satisfied; "
                      "it does NOT resolve.",
        "rationale": "REJECT from ALL THREE derivation clauses (DW, DE, DV): every "
                     "slot holds a synthesised object, not the corresponding "
                     "parameter. Witnessed at source = "
                     "⟨⟨30,2⟩,⟨31,7⟩,⟨32,5⟩,true⟩ with helper answers ⟨120,9⟩, "
                     "⟨121,7⟩, ⟨122,5⟩: the rival's run gives result.widget = "
                     "⟨31,2⟩ ≠ ⟨120,9⟩, result.errorMessages = ⟨32,7⟩ ≠ ⟨121,7⟩ "
                     "and result.validators = ⟨33,5⟩ ≠ ⟨122,5⟩ (DW, DE, DV all "
                     "false) while W, E and V ALL HOLD; the frozen solution "
                     "installs the three parameters (all true). This is the case "
                     "that shows the derivation layer is not implied by the "
                     "independence layer.",
        "witness": _witness("⟨⟨30,2⟩, ⟨31,7⟩, ⟨32,5⟩, ⟨200, 1⟩⟩",
                            "⟨120,9⟩", "⟨121,7⟩", "⟨122,5⟩"),
    },

    # =====================================================================
    # CROSS-WIRED installs — slot-to-helper provenance. Each supplied copy IS
    # installed; two of them land in each other's slots. Nothing is shared and
    # every installed object is a genuine copy of something, so these ask whether
    # the spec pins WHICH copy belongs in WHICH slot. Two rivals: one across the
    # two value-typed slots, one across the opaque slot (which no content clause
    # could reach).
    # =====================================================================
    {
        "id": "reject-crosswired-copies",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CROSSWIRED),
        "refinement": "installs a genuine copy in each value-typed slot, but swaps "
                      "which one goes where: the clone's override-message table "
                      "holds the validator collection's copy and its validator "
                      "collection holds the table's. A real patch that duplicated "
                      "both components into fresh objects but crossed the two "
                      "assignments would produce clones whose override messages and "
                      "validators are each other's — every test that reads a copied "
                      "override message or a copied validator off a cloned field "
                      "would surface the wrong payload. It DOES pass the F2P "
                      "identity assertion (both are distinct objects); it does NOT "
                      "resolve.",
        "rationale": "REJECT from DE and DV (result.errorMessages = messagesCopy, "
                     "result.validators = validatorsCopy), and from the content "
                     "sub-clauses of E and V whenever the two components' contents "
                     "differ. Witnessed at source = "
                     "⟨⟨15,4⟩,⟨16,2⟩,⟨17,9⟩,false⟩ with helper answers ⟨130,1⟩, "
                     "⟨131,2⟩, ⟨132,9⟩: the rival's run gives result.errorMessages "
                     "= ⟨132,9⟩ ≠ ⟨131,2⟩ = messagesCopy and result.validators = "
                     "⟨131,2⟩ ≠ ⟨132,9⟩ = validatorsCopy (DE, DV false; also "
                     "payload 9 ≠ 2 and 2 ≠ 9, so E and V false). Every ref ≠ "
                     "sub-clause HOLDS here.",
        "witness": _witness("⟨⟨15,4⟩, ⟨16,2⟩, ⟨17,9⟩, ⟨200, 1⟩⟩",
                            "⟨130,1⟩", "⟨131,2⟩", "⟨132,9⟩"),
    },

    {
        "id": "reject-crosswired-widget-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CROSSWIRED_WIDGET),
        "refinement": "installs the override-message table's copy in the rendering "
                      "component's slot and the rendering component's copy in the "
                      "table's slot. Every slot holds a fresh object and each is a "
                      "genuine copy of some component, so both the identity "
                      "guarantee and 'a copy helper really ran' are satisfied "
                      "everywhere. An implementation that duplicated both "
                      "components but crossed the two assignments would leave every "
                      "clone rendering from the wrong object and reporting the "
                      "wrong messages; it does NOT resolve. Probes "
                      "slot-to-helper provenance on the opaque slot, which no "
                      "content clause can reach — the copy of a component with no "
                      "value equality is indistinguishable by content from any "
                      "other object, so only DW says which copy belongs there.",
        "rationale": "REJECT from DW and DE (result.widget = widgetCopy, "
                     "result.errorMessages = messagesCopy). Witnessed at source = "
                     "⟨⟨33,7⟩,⟨34,2⟩,⟨35,9⟩,true⟩ with helper answers ⟨140,5⟩, "
                     "⟨141,2⟩, ⟨142,9⟩: the rival's run gives result.widget = "
                     "⟨141,2⟩ ≠ ⟨140,5⟩ = widgetCopy (DW false) and "
                     "result.errorMessages = ⟨140,5⟩ ≠ ⟨141,2⟩ = messagesCopy (DE "
                     "false), while every ref ≠ sub-clause HOLDS AT THAT POINT; the "
                     "frozen solution installs each copy in its own slot (both "
                     "true). (Over the whole domain the verifier additionally "
                     "cannot discharge E or W for this rival — the two copies' "
                     "contents and identities are unrelated in general — so the "
                     "build reports ensures_3, ensures_4, ensures_6 and ensures_7. "
                     "The witness pins the derivation-only refutation.)",
        "witness": _witness("⟨⟨33,7⟩, ⟨34,2⟩, ⟨35,9⟩, ⟨200, 1⟩⟩",
                            "⟨140,5⟩", "⟨141,2⟩", "⟨142,9⟩"),
    },

    # =====================================================================
    # (C) THE SHALLOW-DUPLICATION LEG. The routine's first act is a shallow
    # duplication of the whole field, which is what carries over every component
    # that gets no individual treatment. Every rival above keeps that step; this
    # one discards it and constructs the clone from scratch, installing all three
    # copies correctly but RECONSTRUCTING the carried-over aggregate rather than
    # handing over the source's own. The F2P asserts the clone is still an instance
    # of the field's own subclass, which is exactly this leg — a clone built from
    # scratch is not one. Only C catches it.
    # =====================================================================
    {
        "id": "reject-rebuilt-discards-carried-over",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_unfold(_REBUILT_FROM_SCRATCH),
        "refinement": "does not start from a shallow duplication of the field: it "
                      "constructs the clone from scratch and installs the three "
                      "copies, defaulting every component the shallow duplication "
                      "would have carried over from the source. A real patch that "
                      "replaced the shallow duplication with a fresh construction "
                      "would lose the field's own class and every configured "
                      "attribute that gets no individual treatment — the F2P test's "
                      "first assertion is precisely that the clone is still an "
                      "instance of the field's subclass, and most of the suite "
                      "reads such carried-over attributes off cloned fields. It "
                      "does NOT resolve, and no copy clause catches it, because "
                      "every copy IS installed correctly.",
        "rationale": "REJECT from P (result.carried = source.carried): the rival "
                     "reconstructs the carried-over aggregate instead of handing over "
                     "from the source. Witnessed at source = "
                     "⟨⟨36,3⟩,⟨37,8⟩,⟨38,1⟩,false⟩ with helper answers ⟨150,4⟩, "
                     "⟨151,8⟩, ⟨152,1⟩: the rival's run gives result.carried = "
                     "⟨201,1⟩ ≠ ⟨200,1⟩ = source.carried (C false) while W, E, V, DW, "
                     "DE and DV ALL HOLD; the frozen solution carries `false` over "
                     "(P true). The only rival any copy-related clause is blind to.",
        "witness": _witness("⟨⟨36,3⟩, ⟨37,8⟩, ⟨38,1⟩, ⟨200, 1⟩⟩",
                            "⟨150,4⟩", "⟨151,8⟩", "⟨152,1⟩"),
    },

    # =====================================================================
    # A SECOND soundness positive, in a shape much further from the frozen body
    # than pos-reorder is. pos-reorder keeps the frozen skeleton (mutable
    # accumulator seeded by the shallow duplication, three sequential installs)
    # and only permutes it; a spec that over-fitted that skeleton would still
    # accept it. This one deletes the skeleton: the clone is built in ONE record
    # literal with no `let mut` and no `{ result with ... }` update at all, the
    # carried-over component taken from the source explicitly. Correct and
    # faithful, so it MUST verify.
    # =====================================================================
    {
        "id": "pos-one-record",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_ONE_RECORD),
        "rationale": "PASS SOURCE = W ∧ E ∧ V ∧ DW ∧ DE ∧ DV ∧ P. Building the "
                     "clone as a single record literal ⟨widgetCopy, messagesCopy, "
                     "validatorsCopy, source.carried⟩ puts precisely each helper's "
                     "answer in its own slot and carries the preserved component "
                     "over from the source, exactly as the frozen body does, so all "
                     "seven clauses discharge. Stronger than pos-reorder as a "
                     "SPEC-TOO-STRONG probe: it abandons the frozen impl's shape "
                     "(no mutable accumulator, no shallow-duplication seed, no "
                     "field updates) rather than permuting it, so a spec that had "
                     "over-fitted that shape would reject this one — and note it is "
                     "the CORRECT sibling of reject-rebuilt-discards-carried-over, "
                     "differing only in taking the carried-over component from the "
                     "source, which is what shows P constrains that component's "
                     "VALUE and not the impl's shape. Verified out-of-band "
                     "(EXIT 0).",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals, 2 frame-mutation rivals) plus a
# 1-case AXIOM lane. The nagini sibling models the field with three by-reference
# COLLECTIONS (msg_codes, msg_values, validators, each a `list[int]` with a
# length + per-index content clause). This velvet bundle models the SAME routine
# but abstracts each touched component to a single `Obj` (identity `ref` +
# content fingerprint `payload`), takes the three objects the copy helpers
# produced as INPUTS, and adds a carried-over aggregate `Obj` for the shallow
# duplication leg. Every sibling case is accounted for below.
#
#   nagini case            -> here
#   -----------------------------------------------------------------------
#   pos-reorder            -> pos-reorder                          PORTED
#   admiss                 -> admiss-f2p-domain-and-postimage-…    PORTED
#   alias-msg              -> reject-alias-errormessages           PORTED
#   alias-validators       -> reject-alias-validators              PORTED
#   drop-last-msg          -> (folded into reject-wrong-payload-*) FOLDED
#   wrong-value            -> reject-wrong-payload-errormessages
#                             + reject-wrong-payload-validators    PORTED (x2)
#   frame-mut              -> (none)                               VACUOUS
#   frame-rebind           -> (none)                               VACUOUS
#   (no nagini analogue)   -> reject-alias-widget                  ADDED (clause W)
#   (no nagini analogue)   -> reject-crosswired-copies             ADDED BY AUDIT
#   (no nagini analogue)   -> pos-one-record                       ADDED BY AUDIT
#   (no nagini analogue)   -> reject-widget-wrecked-contents       ADDED (DW)
#   (no nagini analogue)   -> reject-widget-unrelated-object       ADDED (DW)
#   (no nagini analogue)   -> reject-widget-substituted-existing-… ADDED (DW)
#   (no nagini analogue)   -> reject-messages-post-mutated-identity ADDED (DE)
#   (no nagini analogue)   -> reject-synthesised-not-installed     ADDED (echo)
#   (no nagini analogue)   -> reject-crosswired-widget-slot        ADDED (DW/DE)
#   (no nagini analogue)   -> reject-rebuilt-discards-carried-over ADDED (C)
#   AXIOM_TESTS (x1)       -> (none)                               DROPPED (G-AX)
#
# 3 ported (+1 split into 2, +1 ported directly, +8 added, 1 folded), 2 vacuous,
# 1 dropped = 14 velvet cases (3 verify, 11 reject).
#
# COVERAGE. The sole obligation (`prove_correct deepCopyField`) is defended
# (pos-reorder, pos-one-record, admiss-…) and attacked (eleven reject rivals).
# ALL SEVEN independent top-level clauses are attacked:
#   W  — reject-alias-widget
#   E  — reject-alias-errormessages (ref ≠), reject-wrong-payload-errormessages
#        (payload =)
#   V  — reject-alias-validators (ref ≠), reject-wrong-payload-validators
#        (payload =)
#   DW — reject-widget-wrecked-contents (answer damaged),
#        reject-widget-unrelated-object (answer fabricated),
#        reject-widget-substituted-existing-object (answer substituted),
#        reject-crosswired-widget-slot (answer misrouted),
#        reject-synthesised-not-installed (answer never used)
#   DE — reject-messages-post-mutated-identity (the only rival whose slot
#        satisfies BOTH sub-clauses of its independence clause),
#        reject-crosswired-copies, reject-crosswired-widget-slot,
#        reject-synthesised-not-installed
#   DV — reject-crosswired-copies, reject-synthesised-not-installed
#   C  — reject-rebuilt-discards-carried-over
# and BOTH sub-clauses of the two `freshCopy` clauses (E, V) are attacked
# independently. The four input binders are varied across THIRTEEN distinct
# input points (no two reject cases share a `source`, and the three copy
# parameters differ at every point), and within each witness every facet of every
# binder participates in the decided proposition, so no binder position is held
# constant across the battery. Each witness point satisfies all three `require`
# clauses, so every rejection is IN SCOPE. No frame/permission rival is
# fabricated (the class is vacuous on a referentially-transparent carrier).
#
# WHY THE DERIVATION LANE IS SIX OF THE ELEVEN. The opaque rendering component is
# the one slot no CONTENT clause can constrain — its type defines no value
# equality, so its copy reads back equal to nothing and a payload obligation on
# it would assert what the real copy helper does not deliver. What remains
# observable there is PROVENANCE: which object the slot holds. So the rivals that
# can only be caught by a derivation clause are the deepest ones on this surface,
# and they are enumerated by HOW the helper's answer fails to reach the slot —
# damaged, fabricated, substituted, misrouted, unused — rather than by which slot
# they hit. reject-messages-post-mutated-identity carries the same argument onto
# a value-typed slot, where it is provable that no independence clause can see it
# (both of E's sub-clauses hold of the rival's result).
#
# PORTED (pos-reorder): the nagini positive is a structurally-different correct
#   duplication (split the combined loop / reorder the loops). Here the faithful
#   reshape carrying the SAME argument is installing the three copies in the
#   reverse order — each slot still receives its own, so all seven clauses
#   discharge and the frozen `loom_solve` closes it (EXIT 0).
# PORTED (admiss): unlike the earlier revision of this bundle, the method DOES
#   declare `require` clauses, so the nagini "admit an F2P-shaped input" probe
#   ports directly, and is strengthened with the post-image half (satisfiable and
#   non-degenerate at that same input), discharged as an in-region `assert`.
# PORTED (alias-msg -> reject-alias-errormessages): the pre-patch bug verbatim —
#   the override-message table is left as the shallow-duplication alias. Refuted
#   on E's identity sub-clause and on DE. This is the G-DIFF discriminator (the
#   change adds the install of that table's copy); `Solution_prepatch.lean` is
#   this rival and FAILS on `ensures_3: result.errorMessages = messagesCopy` and
#   `ensures_6: freshCopy result.errorMessages source.errorMessages`.
# PORTED (alias-validators -> reject-alias-validators): fix the table, re-share
#   the validators. Refuted on V's identity sub-clause and on DV.
# PORTED (wrong-value -> reject-wrong-payload-errormessages / -validators): the
#   nagini value-level rival (distinct object, wrong CONTENT) ports to BOTH
#   content-bearing clauses as two rivals that give a distinct object with a
#   mangled payload, refuted on the `payload =` sub-clause of E and V
#   respectively. Two rivals so BOTH content sub-clauses are attacked
#   independently of their identity sub-clauses.
# FOLDED (drop-last-msg): the nagini length/per-index rival relies on the
#   collection being an INDEXED list with a `len` and element-wise clause. Here
#   each component's contents are a single `payload` fingerprint (mapping.md §2),
#   not an indexed list — "drop the last entry" is not expressible; any content
#   divergence collapses to a payload mismatch, which is exactly what
#   reject-wrong-payload-* already probes. Folded rather than shipped as a
#   duplicate.
# ADDED (reject-alias-widget): the rendering component's clause (W) is modeled
#   here (it is one of the three touched components) but has no nagini rival,
#   because the nagini surface models the two override arrays + validators. To
#   attack EVERY top-level clause, a widget-alias rival is added. Not fabricated
#   coverage of an unmodeled behavior — W is a real, load-bearing clause.
# VACUOUS (frame-mut, frame-rebind): the nagini sibling carries these MANDATORY
#   because `self` is held at `Acc(self.X, 1/2)` — a HALF, read-only heap
#   permission an impl can illegally write / rebind. This backend is
#   referentially transparent and declares NO `mut` binder; `source` is an
#   immutable value with no heap footprint — there is no read-only field to
#   overwrite and no store to attempt, so there is no substitute probe to build.
#   Not fabricated; VACUOUS by the carrier.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job (axiom_check.py validates
#   the three `require` copy-helper contracts against the real copy callees) and
#   this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
