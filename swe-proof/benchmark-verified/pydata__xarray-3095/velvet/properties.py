"""properties.py — G-PBT falsification battery for pydata__xarray-3095 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
each ``prove_correct <name>`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (two contracted methods over a one-dimensional index wrapper):

  adapterCopy      (self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
  indexVariableCopy(self : IndexAdapter) (deep : Bool) return (out : IndexAdapter)
    ensures out.values       = self.values
    ensures out.storedDtype  = self.storedDtype        <-- LOAD-BEARING
    ensures out.inferredDtype = self.inferredDtype

An ``IndexAdapter`` records an index's element values, the precise element
dtype it PRESENTS (``storedDtype``), and the dtype that would be RE-DERIVED
purely from the underlying representation (``inferredDtype``). For some element
kinds the two differ (the underlying representation cannot carry the precise
stored dtype and falls back to a generic one) and for others they agree.
Copying a wrapper — for EITHER setting of ``deep`` — must carry the stored
dtype through unchanged rather than re-derive it. ``indexVariableCopy``
delegates its data clone to the same operation and must preserve the same
observables.

GROUNDED, NOT AN ORACLE ECHO. Every ``ensures`` is pinned directly to an INPUT
FIELD of ``self`` (``self.values`` / ``self.storedDtype`` / ``self.inferredDtype``),
fully unfolded — there is no opaque answer key to echo, and the cheapest honest
impl IS the field-wise identity copy. The ungrounded-oracle-echo class is
therefore N/A; the positive controls are correct reshapes.

BINDER COVERAGE. Each method's input binders are ``self`` and ``deep``. The
reject witnesses move BOTH: ``deep`` ranges over ``true`` and ``false`` for each
obligation (the real bug is ``deep``-specific — it strikes only under a deep
copy — so a battery pinned at one ``deep`` value would miss a rival that
mishandled the other), and ``self`` ranges over wrappers whose stored/inferred
dtypes agree (numeric) and disagree (the fixed-width-text witness), with varying
value lists. The load-bearing ``storedDtype`` clause is attacked by re-derivation
and constant-dtype rivals; the ``values`` clause by drop-values rivals; every
clause is defended by both ``expect:"verify"`` cases.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling attacks a
    read-only input held at a fractional heap permission by WRITING back into
    it (its ``frame-mutation-write-stored-dtype`` rival). Lean and Velvet are
    referentially transparent: ``self`` and ``deep`` are immutable values (this
    bundle declares no ``mut`` binder), there is no heap and no aliasing, so
    there is no read-only input to overwrite and no discriminating witness could
    exist. Reported as an omission, NOT fabricated.
  * PARTIAL-DOMAIN / RE-DERIVATION — the heart of this instance, PORTED. The
    sibling's prepatch re-derivation rival (rebuild the wrapper without carrying
    the original element type, so the copy's dtype is re-derived from the
    duplicated buffer and collapses to the generic dtype on fixed-width text)
    ports directly: a rival that sets ``out.storedDtype := self.inferredDtype``
    diverges from the post-image exactly on the text sub-domain where the two
    dtypes disagree — the F2P ``test_copy[str-True]``. Given a faithful bug-
    shape here (``deep``-conditional), it is refuted only under a deep copy,
    mirroring that the regression spares the shallow path.
  * PARTIAL-DOMAIN / CONSTANT — PORTED. The sibling's constant-object rival
    (collapse every duplicate to the generic dtype) ports to a rival that always
    reports the generic dtype regardless of the original.
  * UNGROUNDED-ORACLE ECHO — N/A (see above).
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3095"
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
# -- impl-end) and is unique in Solution.lean; both facts are asserted at load
# by _swap. Editing only these keeps markers.same_spec True and every
# prove_correct statement byte-identical (the spec view elides the impl and
# proof regions). The frozen proofs are bare `loom_solve`, which discharges
# every candidate below with no retuning, so no proof-body swap is needed.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the first method (the wrapper copy).
_ADAPTER_BODY = (
    "    let arr := if deep then self.values else self.values\n"
    "    return { values := arr, storedDtype := self.storedDtype,\n"
    "             inferredDtype := self.inferredDtype }")
assert _ADAPTER_BODY in _BASE and _BASE.count(_ADAPTER_BODY) == 1, \
    "impl anchor drift: adapterCopy body not verbatim/unique"

# The first executable line of the wrapper-copy impl region; an in-region
# assert prepended here is discharged by the proof without disturbing the
# method's obligation.
_ADAPTER_TOP = "    let arr := if deep then self.values else self.values"
assert _ADAPTER_TOP in _BASE and _BASE.count(_ADAPTER_TOP) == 1, \
    "impl anchor drift: adapterCopy top line not verbatim/unique"

# The WHOLE executable body of the second method (the index-variable copy,
# which delegates to the wrapper copy).
_INDEXVAR_BODY = ("    let data ← adapterCopy self deep\n"
                  "    return data")
assert _INDEXVAR_BODY in _BASE and _BASE.count(_INDEXVAR_BODY) == 1, \
    "impl anchor drift: indexVariableCopy body not verbatim/unique"


# ---- witness preambles. The spec is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `<name>Tester self deep = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` blocks have been stripped, so no
# ---- tactic script can mask the verdict.
_TESTER_ADAPTER = (
    "extract_program_for adapterCopy\n"
    "prove_precondition_decidable_for adapterCopy\n"
    "prove_postcondition_decidable_for adapterCopy\n"
    "derive_tester_for adapterCopy\n\n")
_TESTER_INDEXVAR = (
    "extract_program_for indexVariableCopy\n"
    "prove_precondition_decidable_for indexVariableCopy\n"
    "prove_postcondition_decidable_for indexVariableCopy\n"
    "derive_tester_for indexVariableCopy\n\n")


def _wrap(values, stored, inferred):
    vlist = "[" + ", ".join(str(v) for v in values) + "]"
    return (f'{{ values := {vlist}, storedDtype := "{stored}", '
            f'inferredDtype := "{inferred}" }}')


def _wit_adapter(values, stored, inferred, deep):
    d = "true" if deep else "false"
    return (_TESTER_ADAPTER +
            f"example : adapterCopyTester {_wrap(values, stored, inferred)} "
            f"{d} = false := by\n  decide\n")


def _wit_indexvar(values, stored, inferred, deep):
    d = "true" if deep else "false"
    return (_TESTER_INDEXVAR +
            f"example : indexVariableCopyTester {_wrap(values, stored, inferred)} "
            f"{d} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. Each keeps its method's `ensures` obligation
    # and only reshapes the executable surface (pointwise over immutable
    # values, no loop / fold), so `loom_solve` closes it unchanged.
    # =====================================================================
    {
        "id": "pos-adapter-reorder-locals",
        "kind": "soundness",
        "expect": "verify",
        # Route each observable through a distinct typed local, in a different
        # order than the frozen body, and reference `deep` explicitly; all three
        # fields are copied field-for-field, so every `ensures` still holds.
        "module": _swap(
            _BASE, _ADAPTER_BODY,
            "    let keptValues : List Int := self.values\n"
            "    let keptStored : String := self.storedDtype\n"
            "    let keptInferred : String := self.inferredDtype\n"
            "    let _ := deep\n"
            "    return { values := keptValues, storedDtype := keptStored,\n"
            "             inferredDtype := keptInferred }"),
        "rationale": "Structurally different but correct: bind each observable "
                     "to its own typed local (reordered) and reconstruct. Every "
                     "field equals the original's, so all three `ensures` "
                     "(values / storedDtype / inferredDtype) hold on every "
                     "input; no loop / fold. Must verify, else SPEC-TOO-STRONG "
                     "(a faithful correct reshape rejected). Defends every "
                     "clause of adapterCopy.",
    },
    {
        "id": "pos-indexvar-inline-construct",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different control flow for the SECOND method: instead of
        # delegating to the wrapper copy, construct the result inline field-for-
        # field. Correct (the delegate itself is the field-wise identity), so
        # every `ensures` of indexVariableCopy still holds.
        "module": _swap(
            _BASE, _INDEXVAR_BODY,
            "    return { values := self.values, storedDtype := self.storedDtype,\n"
            "             inferredDtype := self.inferredDtype }"),
        "rationale": "Structurally different but correct: replace the delegation "
                     "with an inline field-for-field reconstruction. Every field "
                     "equals the original's, so all three `ensures` of "
                     "indexVariableCopy hold. A correct reshape verifying is "
                     "exactly what SPEC-TOO-STRONG would deny. Defends every "
                     "clause of indexVariableCopy from a no-delegation shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — the methods carry NO `require` clause, so the domain is
    # total and no precondition could exclude an F2P-shaped input; the usual
    # "a normal input satisfies the precondition" probe is vacuously met. The
    # residual admissibility risk on a total domain is that the modeled
    # DISCRIMINATOR is degenerate — if the carrier could not even REPRESENT a
    # wrapper whose stored dtype differs from its re-derived dtype, then
    # `out.storedDtype = self.storedDtype` and `out.inferredDtype =
    # self.inferredDtype` would be indistinguishable and the spec would pin
    # nothing the re-derivation bug can violate. This case discharges an
    # in-region assert that the fixed-width-text witness the F2P exercises
    # (stored ≠ inferred) is realizable on this carrier, then reaches the
    # normal gold body so adapterCopy's own obligation still verifies. The
    # assert is LIVE (a false claim leaves an unsolved goal — verified).
    # =====================================================================
    {
        "id": "admiss-text-discriminator-realizable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _ADAPTER_TOP,
            "    assert (with_name_prefix `assert\n"
            "      (({ values := [1], storedDtype := \"U3\", "
            "inferredDtype := \"O\" } : IndexAdapter).storedDtype\n"
            "        ≠ ({ values := [1], storedDtype := \"U3\", "
            "inferredDtype := \"O\" } : IndexAdapter).inferredDtype))\n"
            + _ADAPTER_TOP),
        "rationale": "The modeled discriminator is realizable and non-degenerate: "
                     "there is a wrapper whose presented dtype differs from its "
                     "re-derived dtype (the fixed-width-text witness the F2P "
                     "exercises), so `storedDtype` and `inferredDtype` are "
                     "genuinely distinct observables and the storedDtype clause "
                     "pins something the re-derivation bug can violate. The "
                     "in-region assert must discharge (else the discriminator is "
                     "unrepresentable / PRECOND-TOO-DEGENERATE), and the body is "
                     "kept verbatim so adapterCopy's obligation still verifies.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec, each
    # with a machine-checked refutation witness at a concrete input, and the
    # refinement argument that its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================

    # (partial-domain / re-derivation — the prepatch bug, faithful deep-shape)
    {
        "id": "weak-adapter-rederive-deep",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour, in its faithful deep-conditional shape: on a
        # DEEP copy rebuild the wrapper WITHOUT carrying the stored dtype, so it
        # is re-derived from the duplicated representation (`inferredDtype`);
        # on a shallow copy keep the stored dtype. Correct on the shallow path
        # and on numeric inputs (stored = inferred), wrong on fixed-width text
        # under a deep copy (stored ≠ inferred).
        "module": _swap(
            _BASE, _ADAPTER_BODY,
            "    if deep then\n"
            "      return { values := self.values, storedDtype := self.inferredDtype,\n"
            "               inferredDtype := self.inferredDtype }\n"
            "    else\n"
            "      return { values := self.values, storedDtype := self.storedDtype,\n"
            "               inferredDtype := self.inferredDtype }"),
        "refinement": "a counterpart that on a deep copy rebuilds the wrapper "
                      "from the duplicated representation without carrying the "
                      "original element type re-derives a generic dtype for a "
                      "fixed-width-text index (the representation cannot carry "
                      "the precise dtype), so the deep copy of a text index "
                      "reports the generic dtype instead of the text one. The "
                      "failing test that copies a text index deeply and asserts "
                      "the element dtype is preserved still observes the generic "
                      "dtype, so it would NOT resolve.",
        "rationale": "REJECT from `out.storedDtype = self.storedDtype`: on the "
                     "text sub-domain (stored ≠ inferred) under a DEEP copy the "
                     "impl reports the re-derived dtype where the post-image "
                     "demands the stored one. Refuted at a `<U3`-vs-object "
                     "wrapper with `deep = true` — the deep path the regression "
                     "strikes; it agrees with gold on the shallow path and on "
                     "numeric inputs.",
        "witness": _wit_adapter([1], "U3", "O", True),
    },

    # (partial-domain / constant generic dtype — the lossy fallback)
    {
        "id": "weak-adapter-const-object",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse every copy's presented dtype to the generic dtype ("O")
        # regardless of the original, for either `deep` setting. Correct only on
        # the sub-domain where the original already presents the generic dtype;
        # wrong on every other element kind (numeric, text).
        "module": _swap(
            _BASE, _ADAPTER_BODY,
            "    let _ := deep\n"
            "    return { values := self.values, storedDtype := \"O\",\n"
            "             inferredDtype := self.inferredDtype }"),
        "refinement": "a counterpart that hard-codes the copy's element dtype to "
                      "the generic dtype reports the generic dtype for every "
                      "copied index, so copying a numeric (or text) index no "
                      "longer preserves its element dtype. The pre-existing copy "
                      "tests that assert the original dtype is preserved for "
                      "numeric indices still observe the generic dtype, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out.storedDtype = self.storedDtype`: at a "
                     "numeric wrapper (stored = inferred = a non-generic dtype) "
                     "under a shallow copy the impl reports the generic dtype "
                     "where the post-image demands the stored one. Refuted at a "
                     "numeric `i8` wrapper with `deep = false` — moving `deep` "
                     "to the shallow path and `self` off the text sub-domain, a "
                     "point no other adapter rival probes.",
        "witness": _wit_adapter([7], "i8", "i8", False),
    },

    # (partial-domain / drops the element values — attacks the values clause)
    {
        "id": "weak-adapter-drops-values",
        "kind": "uniqueness",
        "expect": "reject",
        # Discard the element values (return an empty carrier) while preserving
        # both dtype observables. Correct only on the sub-domain where the index
        # is already empty; wrong on every non-empty index. Attacks the `values`
        # clause specifically — the dtype rivals above leave `values` intact.
        "module": _swap(
            _BASE, _ADAPTER_BODY,
            "    let _ := deep\n"
            "    return { values := [], storedDtype := self.storedDtype,\n"
            "             inferredDtype := self.inferredDtype }"),
        "refinement": "a counterpart that drops the element values on copy "
                      "returns an empty index, so a copied index no longer "
                      "carries its elements. Every copy test that asserts the "
                      "copy is identical to the original still observes the "
                      "missing elements, so it would NOT resolve.",
        "rationale": "REJECT from `out.values = self.values`: at a non-empty "
                     "index the impl returns an empty carrier where the "
                     "post-image demands the original values. Refuted at a "
                     "two-element `i8` wrapper with `deep = true` — the only "
                     "adapter rival attacking the `values` clause.",
        "witness": _wit_adapter([5, 7], "i8", "i8", True),
    },

    # (partial-domain / re-derivable dtype clobbered — attacks inferredDtype)
    {
        "id": "weak-adapter-wrong-inferred",
        "kind": "uniqueness",
        "expect": "reject",
        # Preserve values and the stored dtype, but report the copy's RE-DERIVABLE
        # dtype as the stored one instead of the original's re-derived dtype.
        # Correct only where stored = inferred (numeric); wrong on the text
        # sub-domain, where the copy would claim its underlying representation
        # re-derives the precise text dtype rather than the generic one. Attacks
        # the `inferredDtype` clause specifically — the rivals above leave it
        # intact.
        "module": _swap(
            _BASE, _ADAPTER_BODY,
            "    let _ := deep\n"
            "    return { values := self.values, storedDtype := self.storedDtype,\n"
            "             inferredDtype := self.storedDtype }"),
        "refinement": "a counterpart whose copy presents a DIFFERENT re-derivable "
                      "element dtype than the original's has an underlying "
                      "representation of a different element kind — for a "
                      "fixed-width-text index it would claim the representation "
                      "re-derives the precise text dtype where the original's "
                      "re-derives the generic one. A copy whose underlying "
                      "representation differs in element kind is not a faithful "
                      "clone, so the copy-identity assertions (which compare the "
                      "underlying data) still observe the mismatch and it would "
                      "NOT resolve.",
        "rationale": "REJECT from `out.inferredDtype = self.inferredDtype`: on "
                     "the text sub-domain (stored ≠ inferred) the impl reports "
                     "the stored dtype as the re-derivable one where the "
                     "post-image demands the original's re-derived (generic) "
                     "dtype. Refuted at a `<U3`-vs-object wrapper with "
                     "`deep = true`, values `[2]` — the only adapter rival "
                     "attacking the `inferredDtype` clause.",
        "witness": _wit_adapter([2], "U3", "O", True),
    },

    # (partial-domain / re-derivation on the delegating method — shallow path)
    {
        "id": "weak-indexvar-rederive",
        "kind": "uniqueness",
        "expect": "reject",
        # The re-derivation bug on the SECOND method: instead of delegating, the
        # index-variable copy rebuilds its data from the representation and
        # reports the re-derived dtype. Wrong on the text sub-domain, for either
        # `deep` setting. Refuted on the SHALLOW path here, so the two
        # indexVariableCopy rejects between them move `deep` over both values.
        "module": _swap(
            _BASE, _INDEXVAR_BODY,
            "    let _ := deep\n"
            "    return { values := self.values, storedDtype := self.inferredDtype,\n"
            "             inferredDtype := self.inferredDtype }"),
        "refinement": "a counterpart whose index-variable copy re-derives the "
                      "element dtype from the underlying representation rather "
                      "than delegating to a dtype-preserving clone reports the "
                      "generic dtype for a fixed-width-text coordinate. The "
                      "failing test that copies a text-coordinate variable and "
                      "asserts its element dtype is preserved still observes the "
                      "generic dtype, so it would NOT resolve.",
        "rationale": "REJECT from `out.storedDtype = self.storedDtype`: on the "
                     "text sub-domain (stored ≠ inferred) the impl reports the "
                     "re-derived dtype where the post-image demands the stored "
                     "one. Refuted at a `<U3`-vs-object wrapper with "
                     "`deep = false`, varying `deep` on the delegating method.",
        "witness": _wit_indexvar([1], "U3", "O", False),
    },

    # (partial-domain / drops values on the delegating method)
    {
        "id": "weak-indexvar-drops-values",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the element values on the SECOND method. Attacks the `values`
        # clause of indexVariableCopy; refuted at `deep = true` with a distinct
        # value list.
        "module": _swap(
            _BASE, _INDEXVAR_BODY,
            "    let _ := deep\n"
            "    return { values := [], storedDtype := self.storedDtype,\n"
            "             inferredDtype := self.inferredDtype }"),
        "refinement": "a counterpart whose index-variable copy drops the element "
                      "values returns an empty coordinate, so a copied "
                      "index-valued variable no longer carries its elements. "
                      "Every copy test asserting identity to the original still "
                      "observes the missing elements, so it would NOT resolve.",
        "rationale": "REJECT from `out.values = self.values`: at a non-empty "
                     "coordinate the impl returns an empty carrier where the "
                     "post-image demands the original values. Refuted at a "
                     "one-element `i8` wrapper with `deep = true`.",
        "witness": _wit_indexvar([9], "i8", "i8", True),
    },

    # (partial-domain / re-derivable dtype clobbered on the delegating method)
    {
        "id": "weak-indexvar-wrong-inferred",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the `inferredDtype` clause of the SECOND method: report the
        # stored dtype as the re-derivable one. Wrong on the text sub-domain,
        # refuted at `deep = false` with a distinct value list.
        "module": _swap(
            _BASE, _INDEXVAR_BODY,
            "    let _ := deep\n"
            "    return { values := self.values, storedDtype := self.storedDtype,\n"
            "             inferredDtype := self.storedDtype }"),
        "refinement": "a counterpart whose index-variable copy presents a "
                      "re-derivable element dtype different from the original's "
                      "has produced a copy whose underlying representation is of "
                      "a different element kind — not a faithful clone. The "
                      "copy-identity assertions comparing the underlying data "
                      "still observe the mismatch, so it would NOT resolve.",
        "rationale": "REJECT from `out.inferredDtype = self.inferredDtype`: on "
                     "the text sub-domain (stored ≠ inferred) the impl reports "
                     "the stored dtype as the re-derivable one where the "
                     "post-image demands the original's re-derived dtype. "
                     "Refuted at a `<U3`-vs-object wrapper with `deep = false`, "
                     "values `[3]` — the only indexVariableCopy rival attacking "
                     "the `inferredDtype` clause.",
        "witness": _wit_indexvar([3], "U3", "O", False),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2
# soundness positives, 1 admissibility, 3 uniqueness rivals) plus 1 AXIOM_TESTS
# entry. This bundle models the purely functional core as TWO delegating
# methods (the wrapper copy and the index-variable copy), each with three
# structural `ensures`, so the port re-expresses the sibling's reasoning over
# both obligations.
#
#   sibling case                          -> here                              disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-reorder-locals            -> pos-adapter-reorder-locals         PORTED
#   pos-control-direct-carryover          -> pos-indexvar-inline-construct      RE-EXPRESSED
#   admissibility-text-witness            -> admiss-text-discriminator-realizable RE-AIMED
#   frame-mutation-write-stored-dtype     -> (none)                             VACUOUS
#   partial-domain-rederive-prepatch      -> weak-adapter-rederive-deep         PORTED
#                                          + weak-indexvar-rederive             (second obligation)
#   partial-domain-const-object           -> weak-adapter-const-object         PORTED
#   (—)                                   -> weak-adapter-drops-values          ADDED (values clause)
#   (—)                                   -> weak-indexvar-drops-values         ADDED (values clause)
#   (—)                                   -> weak-adapter-wrong-inferred         ADDED (inferredDtype clause)
#   (—)                                   -> weak-indexvar-wrong-inferred        ADDED (inferredDtype clause)
#
# PORTED (rederive / const-object): the sibling's load-bearing rivals — re-derive
#   the dtype from the duplicated buffer (the prepatch bug), and collapse every
#   copy to the generic dtype — carry over directly against the storedDtype
#   clause. The re-derivation rival is given its faithful DEEP-conditional shape
#   (the regression strikes only the deep path), refuted at a text wrapper under
#   a deep copy; a second copy of it attacks the delegating method on the shallow
#   path so `deep` is moved over both values there too.
# RE-EXPRESSED (pos-direct-carryover): the sibling's cheapest honest impl becomes
#   the no-delegation inline reconstruction of the SECOND method — a maximally
#   different control-flow shape that stays correct.
# RE-AIMED (admissibility): the methods have no `require` clause, so the sibling's
#   "a normal input meets the Requires" probe is vacuous. It is re-aimed at the
#   residual total-domain risk — that the modeled discriminator is degenerate —
#   by discharging a LIVE in-region assert that a wrapper whose stored dtype
#   differs from its re-derived dtype (the text witness) is realizable, so the
#   storedDtype clause pins something the re-derivation bug can violate.
# ADDED (4, per-clause coverage): the sibling's rivals all attack the STORED
#   dtype, so the other two independent clauses would go unattacked. Two
#   drops-values rivals attack `out.values = self.values` (an impl that dropped
#   the elements but kept the dtypes would otherwise verify against a
#   dtype-only battery), and two wrong-inferred rivals attack
#   `out.inferredDtype = self.inferredDtype` (an impl that clobbered the
#   re-derivable dtype would otherwise slip through) — one of each per
#   obligation. All are real would-not-resolve rivals: a copy that loses its
#   elements or whose underlying representation is of a different element kind
#   fails the copy-identity assertions.
# VACUOUS (frame-mutation): the sibling's mandatory frame-mutation rival writes
#   back into a read-only input held at a fractional heap permission. This
#   backend is referentially transparent, has no heap or aliasing, and this
#   bundle declares no `mut` binder — there is no read-only input to overwrite
#   and no discriminating witness could exist. Omitted as vacuous, NOT fabricated.
#
# BINDER / CLAUSE COVERAGE. Each obligation binds `self` and `deep`. Across the
#   adapterCopy rejects `deep` takes both true and false and `self` ranges over
#   text (stored ≠ inferred) and numeric (stored = inferred) wrappers with
#   differing value lists; likewise across the indexVariableCopy rejects `deep`
#   takes both values. So `deep` — the binder the real bug turns on — is
#   genuinely varied for BOTH obligations rather than pinned. All three
#   independent top-level clauses are attacked for each obligation: storedDtype
#   (the rederive and const-object rivals), values (the drops-values rivals),
#   and inferredDtype (the wrong-inferred rivals). Both obligations are defended
#   (each has a dedicated `expect="verify"` reshape) and attacked (four rejects
#   each).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   the dtype-preserving-copy A-reference against the real wrapper); the copy is
#   modeled deeply here with no consumed axiom (the `axioms` region declares
#   nothing), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
