"""properties.py — G-PBT falsification battery for django__django-14752 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. Two contracted methods over the modeled functional core:

  serializeResult (it : Item) return (out : Serialized)
    ensures out = defaultSerialized it

  buildResults (items : List Item) (serialize : Item → Serialized)
      return (out : List Serialized)
    ensures out = items.map serialize

``Item`` carries the two observables the default conversion reads (``idText`` /
``displayText``); ``Serialized = List (String × String)`` is the ordered
key/value object produced for one item; ``defaultSerialized it`` is the concrete
default object ``[("id", it.idText), ("text", it.displayText)]``.

Two independent load-bearing behaviours live here:

  (A) THE DEFERRAL. ``buildResults`` applies WHATEVER per-item conversion is in
      effect (the free total function ``serialize``) to EVERY item, in order:
      ``out = items.map serialize``. ``serialize`` is a caller-supplied input
      (its default is ``serializeResult``); the postcondition quantifies over
      ALL such functions, so the result must be *produced by* the injected
      conversion — an impl that inlines the default instead of calling
      ``serialize`` agrees only on the sub-domain where the caller did not
      customize, and is wrong for every override. This is exactly the
      extension-point the fix introduces.

  (B) THE DEFAULT OBJECT. ``serializeResult`` produces exactly the identifier
      field then the display-text field, in that order:
      ``out = defaultSerialized it``. A conversion that transposes the two
      fields violates it.

``defaultSerialized`` is NOT an opaque answer-key: it is a concrete ``def`` over
the item's own observables, so there is no wrong value an impl could "echo" —
constructing the pair list correctly IS the work. The ``axioms`` region is
empty (mapping.md §3: no consumed callee contract). Hence no echo case; the
soundness lane carries honest structurally-different positive controls — one of
which (``pos-build-foldr``) is deliberately NOT definitionally equal to the
frozen body, so that the lane contains at least one positive whose verification
re-proves the obligation instead of reducing to it.

WITNESS MECHANICS on this carrier. Both frozen impls are STRAIGHT-LINE, and the
whole carrier is transparent (``String`` / ``List`` / a two-field structure), so
each reject rival is refuted by a Velvet tester statement
(``<method>Tester <input> = false``) at ONE concrete input, checked in a file
whose ``prove_correct`` block has been stripped so no tactic script can mask the
verdict. No conditioning on an opaque term is needed: every probed value is a
concrete literal and ``decide`` settles it. The function-valued input
``serialize`` is supplied as a concrete lambda at each probe. Both halves were
checked out-of-band with ``scripts/lean_verify.sh``: every witness ELABORATES
against its rival and FAILS (``decide`` proves the proposition false) against the
frozen solution. No ``sorry`` / ``admit`` / ``native_decide`` / ``axiom``.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` (mapping.md §3);
``defaultSerialized`` is a deep-model reference, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14752"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl-region and proof-body anchors. Each lies ENTIRELY inside a region
# the consumer spec view elides (an `-- impl-start`/`-- impl-end` block, or a
# `prove_correct` tactic body) and is UNIQUE in the file; `_swap` asserts both
# facts, so any drift breaks the manifest at load and every edit stays inside an
# elided region (same_spec holds by construction).
# ---------------------------------------------------------------------------

# serializeResult impl body (the single returned pair-list, 4-space indent).
_SER_IMPL = '    return [("id", it.idText), ("text", it.displayText)]'

# buildResults impl body (bind the mapped list, then return it).
_BR_IMPL = "    let results := items.map serialize\n    return results"

# serializeResult frozen proof (retuned by reshapes that leave `simp` no work).
_SER_PROOF = ("prove_correct serializeResult by\n  loom_solve\n"
              "  simp [defaultSerialized]")

# buildResults frozen proof.
_BR_PROOF = "prove_correct buildResults by\n  loom_solve"

assert _BASE.count(_SER_IMPL) == 1, "serializeResult impl anchor drifted"
assert _BASE.count(_BR_IMPL) == 1, "buildResults impl anchor drifted"
assert _BASE.count(_SER_PROOF) == 1, "serializeResult proof region drifted"
assert _BASE.count(_BR_PROOF) == 1, "buildResults proof region drifted"


# ---- witness preambles. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `<method>Tester <input> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` block has been stripped. Neither method has a
# ---- `require` clause, so the precondition is `True` and decides trivially.
_BR_TESTER = (
    "extract_program_for buildResults\n"
    "prove_precondition_decidable_for buildResults\n"
    "prove_postcondition_decidable_for buildResults\n"
    "derive_tester_for buildResults\n\n"
)
_SER_TESTER = (
    "extract_program_for serializeResult\n"
    "prove_precondition_decidable_for serializeResult\n"
    "prove_postcondition_decidable_for serializeResult\n"
    "derive_tester_for serializeResult\n\n"
)

# Concrete Item literals used in the probes.
_A = '({ idText := "a", displayText := "b" } : Item)'
_C = '({ idText := "c", displayText := "d" } : Item)'


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the byte-identical theorem statement;
    # only the executable surface and (where needed) the tactic script move.
    # =====================================================================
    {
        "id": "pos-build-eta",
        "kind": "soundness",
        "expect": "verify",
        # Reshape buildResults: return the map directly, applying `serialize`
        # through an explicit per-item lambda instead of binding a local. Same
        # value on every input (eta-expansion of the injected conversion), so
        # `out = items.map serialize` still holds and `loom_solve` closes.
        "module": _swap(
            _BASE, _BR_IMPL,
            "    return items.map (fun it => serialize it)"),
        "rationale": "a correct reshape of buildResults (return the map through an "
                     "explicit per-item lambda, no intermediate local) still "
                     "applies the injected conversion to every item in order, so "
                     "`out = items.map serialize` holds on the whole domain; a "
                     "faithful correct impl must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-build-foldr",
        "kind": "soundness",
        "expect": "verify",
        # Build the results by a right fold that conses the injected conversion
        # of each item onto the accumulated tail, instead of mapping. Same value
        # on every input, but NOT definitionally equal to the frozen body: the
        # goal `items.foldr (fun it acc => serialize it :: acc) [] =
        # items.map serialize` does not close by reduction and needs a real
        # induction on the list, so the frozen tactic script does not carry over
        # and the case exercises the obligation instead of re-spelling it. This
        # is the battery's only positive whose equality with gold is not a
        # delta/eta-unfold (see the note on the two reshape positives below).
        "module": _swap(
            _swap(_BASE, _BR_IMPL,
                  "    let results := items.foldr "
                  "(fun it acc => serialize it :: acc) []\n"
                  "    return results"),
            _BR_PROOF,
            "prove_correct buildResults by\n  loom_solve\n"
            "  induction items with\n"
            "  | nil => simp\n"
            "  | cons hd tl ih => simp [ih]"),
        "rationale": "a right fold that conses the injected conversion of each "
                     "item onto the accumulated tail applies that conversion to "
                     "every item in order, so `out = items.map serialize` holds "
                     "on the whole domain — but only PROVABLY so, by induction "
                     "on the list, not by reduction: this positive is not "
                     "definitionally equal to the frozen body, so it is the one "
                     "that actually tests SPEC-TOO-STRONG rather than "
                     "re-spelling the frozen impl.",
    },
    {
        "id": "pos-serialize-viadefault",
        "kind": "soundness",
        "expect": "verify",
        # Reshape serializeResult: return the modeled default object by name
        # instead of respelling the pair list inline. Definitionally equal, so
        # `out = defaultSerialized it` holds; the `simp` step is dropped because
        # the reshaped body leaves `loom_solve` nothing further to normalize.
        "module": _swap(
            _swap(_BASE, _SER_IMPL, "    return defaultSerialized it"),
            _SER_PROOF, "prove_correct serializeResult by\n  loom_solve"),
        "rationale": "returning the modeled default object by name satisfies "
                     "`out = defaultSerialized it` DEFINITIONALLY (it is a "
                     "delta-unfold of the frozen body, and `pos-build-eta` is an "
                     "eta-expansion of its own), so this positive only checks "
                     "that unfolding the default's name does not disturb the "
                     "obligation — it is a cheap control, and the load-bearing "
                     "SPEC-TOO-STRONG probe is `pos-build-foldr`, whose equality "
                     "with gold needs an induction rather than reduction.",
    },

    # =====================================================================
    # ADMISSIBILITY. Neither method carries a `require` clause, so the sibling's
    # "a normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like a spec every impl meets. This case discharges an
    # in-region `assert` pinning the default object's DISCRIMINATING shape at a
    # concrete item: the identifier field comes first and the display-text field
    # second, and that order is NOT symmetric (the transposed object differs).
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim leaves an unsolved goal).
    # =====================================================================
    {
        "id": "admiss-default-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _SER_IMPL,
                "    assert (with_name_prefix `admiss\n"
                "      (defaultSerialized { idText := \"1\", displayText := \"Q\" }\n"
                "         = [(\"id\", \"1\"), (\"text\", \"Q\")] ∧\n"
                "       defaultSerialized { idText := \"1\", displayText := \"Q\" }\n"
                "         ≠ [(\"id\", \"Q\"), (\"text\", \"1\")]))\n"
                + _SER_IMPL),
            _SER_PROOF,
            "prove_correct serializeResult by\n  loom_solve\n"
            "  all_goals first | (refine ⟨by decide, by decide⟩) "
            "| simp [defaultSerialized]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "interesting point: the default object places the identifier "
                     "field first and the display-text field second, an order that "
                     "is not symmetric (the transposed object differs). The "
                     "in-region assert must discharge (else the obligation is "
                     "degenerate); the impl is kept verbatim so "
                     "`out = defaultSerialized it` still verifies.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each refuted at a concrete input by a witness that
    # FAILS on the frozen solution, with the refinement argument that its
    # faithful real counterpart would NOT resolve the F2P.
    # =====================================================================

    # --- (A) deferral rivals: ignore the injected conversion / mis-apply it. ---
    {
        "id": "weak-inline-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the injected conversion entirely; apply the DEFAULT to every
        # item (the pre-change behaviour). Correct only when the caller did not
        # customize; wrong for any override.
        "module": _swap(_BASE, _BR_IMPL,
                        "    let results := items.map defaultSerialized\n"
                        "    return results"),
        "refinement": "applying the default conversion to every item, ignoring "
                      "the injected one, is the pre-change behaviour: the results "
                      "are built without consulting a caller-supplied conversion, "
                      "so a subclass that adds an extra field to each entry has no "
                      "effect. The failing test overrides the per-item conversion "
                      "to add an extra key and asserts every entry carries it; "
                      "with the override ignored no entry carries it => it would "
                      "NOT resolve (it is the bug being fixed).",
        "rationale": "REJECT from `out = items.map serialize`: the post-image "
                     "demands each entry be the injected conversion applied to the "
                     "item, but the rival emits the default. Refuted at a "
                     "single-item list under a conversion (`fun _ => [(\"x\", "
                     "\"y\")]`) that DIFFERS from the default — the sub-domain "
                     "where a customized caller is served wrong.",
        "witness": _BR_TESTER +
                   f"example : buildResultsTester [{_A}] "
                   "(fun _ => [(\"x\", \"y\")]) = false := by\n  decide\n",
    },
    {
        "id": "weak-partial-firstitem-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: defer for every item EXCEPT the first, where it inlines the
        # default. Correct on all but the head — a value-proxy checking only the
        # tail would miss it. Diverges on any list whose head's injected
        # conversion differs from the default.
        "module": _swap(_BASE, _BR_IMPL,
                        "    let results := match items with\n"
                        "      | [] => []\n"
                        "      | x :: xs => defaultSerialized x :: xs.map serialize\n"
                        "    return results"),
        "refinement": "a faithful patch that special-cases the first matched item "
                      "to the inline default but defers the rest would, for the "
                      "first row, IGNORE a caller override. The failing test "
                      "asserts the added key on EVERY entry including the first; "
                      "the first entry would lack it => it would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: correct on the tail, diverges only on the "
                     "head. REJECT from `out = items.map serialize` at index 0: "
                     "the head must be the injected conversion of the first item, "
                     "not the default. Refuted at a TWO-item list — the smallest "
                     "shape that separates this near-miss from weak-inline-default "
                     "(which is wrong at every index) — under an override-shaped "
                     "conversion that adds a key, VARYING both the list length and "
                     "the `serialize` binder (a non-constant lambda here vs. the "
                     "constant one in weak-inline-default).",
        "witness": _BR_TESTER +
                   f"example : buildResultsTester [{_A}, {_C}] "
                   "(fun it => [(\"id\", it.idText), (\"text\", it.displayText), "
                   "(\"posted\", \"p\")]) = false := by\n  decide\n",
    },

    # --- alignment rival: drop the last item. ---
    {
        "id": "weak-skip-last-item",
        "kind": "uniqueness",
        "expect": "reject",
        # Defer correctly but over items.dropLast: produces one fewer entry than
        # there are items. Violates the length/alignment content of the map.
        "module": _swap(_BASE, _BR_IMPL,
                        "    let results := items.dropLast.map serialize\n"
                        "    return results"),
        "refinement": "a builder that drops the final matched item returns one "
                      "fewer entry than there are items. The failing test asserts "
                      "the results list has one entry per source object; a missing "
                      "last entry makes the asserted list mismatch => it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = items.map serialize`: over a non-empty "
                     "list the rival maps only the prefix, so it has length "
                     "`items.length - 1` where the post-image demands "
                     "`items.length`, and the two lists differ. Refuted at a "
                     "singleton (where the rival returns `[]`) under a conversion "
                     "(`fun _ => [(\"z\", \"w\")]`) distinct from the deferral "
                     "rivals' — a distinct input point and a distinct `serialize`.",
        "witness": _BR_TESTER +
                   f"example : buildResultsTester [{_C}] "
                   "(fun _ => [(\"z\", \"w\")]) = false := by\n  decide\n",
    },

    # --- ORDER rival: build every entry, in the wrong order. ---
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Apply the injected conversion to EVERY item — the deferral is honoured
        # and the length is right — but emit the entries back-to-front. This is
        # the one arm the alignment/deferral rivals leave open: they are all
        # refutable by a length or a per-entry-content check, whereas this rival
        # produces exactly the right MULTISET of entries and differs only in
        # ORDER. Without it, the ordering half of `items.map serialize` (which
        # the spec view's own prose claims: "preserving order", "the count and
        # order of the results equal those of the items") is asserted and never
        # demonstrated.
        "module": _swap(_BASE, _BR_IMPL,
                        "    let results := (items.map serialize).reverse\n"
                        "    return results"),
        "refinement": "a builder that emits the entries in the opposite order to "
                      "the source objects returns the right entries against the "
                      "wrong positions. The failing test compares the results "
                      "list to a list built from the objects in their queried "
                      "order, entry by entry; two objects in the reverse order "
                      "make that comparison fail => it would NOT resolve.",
        "rationale": "REJECT from `out = items.map serialize` on ORDER alone: the "
                     "rival emits the correct entry for every item and the "
                     "correct count, so no length check and no per-entry "
                     "membership check refutes it — only the positional content "
                     "of the map does. Refuted at a TWO-item list whose two items "
                     "have distinct observables (the shortest input at which a "
                     "reversal is observable) under the DEFAULT-shaped conversion, "
                     "a fourth distinct `serialize` point for this binder.",
        "witness": _BR_TESTER +
                   f"example : buildResultsTester [{_A}, {_C}] "
                   "(fun it => [(\"id\", it.idText), "
                   "(\"text\", it.displayText)]) = false := by\n  decide\n",
    },

    # --- (B) default-object rival: transpose the two fields. ---
    {
        "id": "weak-default-swap-fields",
        "kind": "uniqueness",
        "expect": "reject",
        # serializeResult transposes the identifier and display-text fields:
        # id-slot carries the display text and text-slot the identifier. Wrong on
        # every item whose two observables differ.
        "module": _swap(
            _BASE, _SER_IMPL,
            '    return [("id", it.displayText), ("text", it.idText)]'),
        "refinement": "a faithful default conversion with the two field values "
                      "transposed emits the display text under the identifier key "
                      "and vice-versa. The failing test asserts the identifier key "
                      "carries the object's identifier and the text key its "
                      "display text; the transposition makes both assertions fail "
                      "=> it would NOT resolve.",
        "rationale": "REJECT from `out = defaultSerialized it`: the post-image "
                     "pins the identifier field first and the display-text field "
                     "second, both violated by the swap. Refuted at an item whose "
                     "two observables differ (`idText := \"a\"`, `displayText := "
                     "\"b\"`), so the transposition is observable — attacking the "
                     "(B) default-object clause, independent of the (A) deferral "
                     "clause the buildResults rivals attack.",
        "witness": _SER_TESTER +
                   f"example : serializeResultTester {_A} = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-default-const-id",
        "kind": "uniqueness",
        "expect": "reject",
        # serializeResult ignores the item's identifier observable and emits a
        # constant in the id slot (keeping the display text correct). Correct
        # only for an item whose identifier happens to equal that constant; wrong
        # for every other item. A value-proxy checking only the text slot would
        # miss it.
        "module": _swap(
            _BASE, _SER_IMPL,
            '    return [("id", "0"), ("text", it.displayText)]'),
        "refinement": "a default conversion that emits a fixed value for the "
                      "identifier field instead of the item's own identifier "
                      "renders the wrong id for every object whose identifier is "
                      "not that constant. The failing test asserts the identifier "
                      "key carries the object's identifier; a constant id makes "
                      "that assertion fail => it would NOT resolve.",
        "rationale": "REJECT from `out = defaultSerialized it` on the identifier "
                     "field: the post-image pins `it.idText` in the id slot, but "
                     "the rival emits a constant. Refuted at an item whose "
                     "identifier is not that constant (`idText := \"5\"`), VARYING "
                     "the `it` binder against weak-default-swap-fields (idText "
                     "\"a\") so the pair demonstrates the post-image's dependence "
                     "on `it` at two distinct points, not one.",
        "witness": _SER_TESTER +
                   'example : serializeResultTester '
                   '({ idText := "5", displayText := "6" } : Item) = false := by\n'
                   "  decide\n",
    },
    {
        "id": "weak-default-extra-field",
        "kind": "uniqueness",
        "expect": "reject",
        # serializeResult emits BOTH correct fields and then a third one. Every
        # value the other (B) rivals check is right: the id slot carries the
        # identifier, the text slot the display text, in that order. Only the
        # EXACTNESS of the default object refutes it. This closes the arm where
        # the spec view's prose claims the default carries "exactly" those two
        # fields — a claim no other case demonstrates, since swap-fields and
        # const-id both attack a field's VALUE rather than the field set.
        "module": _swap(
            _BASE, _SER_IMPL,
            '    return [("id", it.idText), ("text", it.displayText), '
            '("posted", "")]'),
        "refinement": "a default conversion that appends a third field of its own "
                      "makes every object's entry carry a key the default is not "
                      "supposed to add. The failing test compares each entry to a "
                      "dict of exactly the keys the override is expected to "
                      "produce; an uninvited extra key makes the comparison fail "
                      "=> it would NOT resolve. It also silently pre-empts the "
                      "customization the extension point exists to enable.",
        "rationale": "REJECT from `out = defaultSerialized it` on the EXACT field "
                     "set: both default fields are present, correct, and in the "
                     "right order, so no per-field value check refutes this rival "
                     "— only the default object's exactness does. Refuted at the "
                     "same item as weak-default-swap-fields, where the surplus "
                     "field is the sole difference from the frozen default.",
        "witness": _SER_TESTER +
                   f"example : serializeResultTester {_A} = false := by\n"
                   "  decide\n",
    },
    {
        "id": "weak-default-drop-text-field",
        "kind": "uniqueness",
        "expect": "reject",
        # serializeResult emits ONLY the identifier field, omitting the display-
        # text field entirely. The mirror of weak-default-extra-field: that rival
        # is a superset of the default object, this one a strict subset, so the
        # two together pin the field set from both sides. Nothing else in the
        # battery detects a MISSING default field — const-id keeps both slots and
        # swap-fields keeps both slots.
        "module": _swap(_BASE, _SER_IMPL,
                        '    return [("id", it.idText)]'),
        "refinement": "a default conversion that omits the display-text field "
                      "emits an entry with no display text at all. The failing "
                      "test asserts each entry carries the object's display text "
                      "under its own key; a missing key makes that assertion fail "
                      "=> it would NOT resolve, and every existing test over the "
                      "default entry fails with it.",
        "rationale": "REJECT from `out = defaultSerialized it` on the field set "
                     "from BELOW: the identifier field is present and correct, so "
                     "the rival is refuted only by the display-text field the "
                     "post-image also demands. Refuted at a THIRD `it` point "
                     "(`idText := \"7\"`, `displayText := \"8\"`), distinct from "
                     "both weak-default-swap-fields (\"a\"/\"b\") and "
                     "weak-default-const-id (\"5\"/\"6\").",
        "witness": _SER_TESTER +
                   'example : serializeResultTester '
                   '({ idText := "7", displayText := "8" } : Item) = false := by\n'
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 9 SPEC cases plus 2
# AXIOM_TESTS. The sibling contracts TWO functions — `build_results(view, recs,
# to_field_name)` and `default_record_entry(view, rec, to_field_name)` — over a
# heap-permissioned queryset, with the per-item dispatch behind an OPAQUE,
# late-bound callee `record_entry` (Ensures(True)) reached by reference identity
# (`is`). This velvet bundle models the same functional core with two methods:
# `buildResults(items, serialize)` — where the opaque late-bound dispatch is
# abstracted to a FREE total function `serialize` and the deferral is pinned by
# `out = items.map serialize` (quantified over all serializers) — and
# `serializeResult(it)` pinned by `out = defaultSerialized it`. The map is:
#
#   sibling case                     -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-localvar             -> pos-build-eta                 PORTED (build)
#                                    -> pos-build-foldr               ADDED (build)
#   pos-control-default-localvar     -> pos-serialize-viadefault      PORTED (default)
#   admiss-default-precond-admits    -> admiss-default-nondegenerate  RE-AIMED
#   weak-inline-default              -> weak-inline-default           PORTED (A arm)
#   weak-partial-firstrow-inline     -> weak-partial-firstitem-default PORTED (A arm)
#   weak-default-swap-fields         -> weak-default-swap-fields      PORTED (B arm)
#   weak-skip-last-record            -> weak-skip-last-item           PORTED (alignment)
#   reject-frame-mutation-rec        -> (none)                        VACUOUS
#   reject-frame-mutation-list-elem  -> (none)                        VACUOUS
#
# 5 uniqueness rivals ported (both behaviours A and B defended, plus the
# alignment support), 2 positives ported, 1 admissibility re-aimed, 2
# frame-mutation vacuous. AXIOM_TESTS dropped (G-AX's lane; empty here).
#
# ADDED: weak-default-const-id — a second `serializeResult` rival (constant in
#   the identifier slot) with no 1:1 sibling. It attacks the (B) default-object
#   clause on the IDENTIFIER field specifically (weak-default-swap-fields hits
#   both fields jointly), at a distinct `it` point, so the post-image's
#   dependence on `it` is demonstrated at two points rather than one.
#
# ADDED (order arm, no sibling): weak-reverse-order. Every ported (A) rival is
#   refutable by a LENGTH check (skip-last) or by a per-entry CONTENT check
#   (inline-default, firstitem-default): none of them produces the right entries
#   in the wrong order, so the ordering half of `out = items.map serialize` was
#   claimed by the spec view's prose ("preserving order"; "the count and order of
#   the results equal those of the items") and by this file's own clause-coverage
#   note, and demonstrated by nothing. This rival honours the deferral and the
#   count exactly and differs from gold ONLY positionally.
#
# ADDED (field-set arm, no sibling): weak-default-extra-field and
#   weak-default-drop-text-field. The sibling's single (B) rival transposes the
#   two field VALUES, and const-id replaces one value; all three leave the default
#   object's field SET at exactly the two default keys. So "carries exactly the
#   identifier field and the display-text field" — the frozen spec view's own
#   words for `defaultSerialized`, and the property that makes the extension point
#   meaningful (the default must not pre-empt an override's extra key) — was
#   undemonstrated in both directions. The pair pins it from above (a surplus
#   third field) and from below (the display-text field omitted).
#
# RE-AIMED (admissibility). The sibling asserts, inside default_record_entry,
#   that the (fractional) precondition ADMITS the default conversion call. Neither
#   method here carries a `require` clause, so that probe is vacuous. It is
#   re-aimed at the residual total-domain risk — a degenerate post-image — by
#   discharging an in-region assert that the default object's field ORDER is
#   non-symmetric at a concrete item (identifier first, display-text second; the
#   transposed object differs). This keeps the modeled default meaningful, which
#   is what makes weak-default-swap-fields a real refutation rather than a
#   vacuous one.
#
# VACUOUS (both frame-mutation rivals). The sibling's MANDATORY frame-mutation
#   rivals keep the gold body then WRITE into a read-only input that carries only
#   a fractional heap permission (rec.id_text at 1/2; recs[i].id_text at 1/8) and
#   are rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
#   transparent: `it` / `items` / `serialize` are immutable values, neither method
#   declares a `mut` binder, there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class is
#   vacuous — the directive-5 frame obligation is discharged by the ABSENCE of any
#   `mut` binder, which the frozen spec already encodes. No substitute fabricated.
#   DEMONSTRATED rather than asserted: writing the read-only binder in the impl
#   region (`it := { idText := it.displayText, .. }`, and `items := items.reverse`
#   in the other method) does not elaborate to a wrong-but-well-formed rival at
#   all — the front end rejects the assignment itself, "`it` cannot be mutated,
#   only variables declared using `let mut` can be mutated", and the file then
#   fails to build with "Failed to parse an assertion without names: WPGen sorry".
#   Such a variant could only ever be "rejected" for a SYNTACTIC reason, so no
#   witness could discriminate it and shipping it would be a decorative reject
#   case. That is the demonstration the vacuity claim needs; the mutation class is
#   not merely unmodeled here, it is unstatable.
#
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
#   frozen impl region is LOOP-FREE (straight-line ``let`` over immutable
#   values, no loop and no recursion), so there is no control flow here to make
#   diverge: a diverging rival cannot be obtained by mutating this body, it has
#   to bring a loop of its own. When it does, the semantics refuse it. This
#   bundle sets ``loom.semantics.termination "total"`` AND carries
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
# UNGROUNDED-ORACLE ECHO — N/A. Both post-images are total functions of each
#   method's own input (`items.map serialize`; `defaultSerialized it`), and the
#   `axioms` region is empty. `serialize` is a free INPUT, not an answer-key: the
#   post-image quantifies over it, so an impl cannot "echo" a fixed oracle — it
#   must apply whatever function was passed. There is no wrong value to echo, so
#   the honest cheapest reshapes stand as the positives.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (8 rivals, 8 distinct probes):
#   - buildResults.items — singleton (weak-inline-default, weak-skip-last-item),
#       two-item list (weak-partial-firstitem-default, weak-reverse-order): list
#       length VARIED, and the near-miss pair (inline-default vs firstitem-
#       default) separated at the length that distinguishes them.
#   - buildResults.serialize — VARIED across four distinct functions: a constant
#       `fun _ => [("x","y")]` (weak-inline-default), a non-constant
#       override-shaped lambda adding a key (weak-partial-firstitem-default), a
#       different constant `fun _ => [("z","w")]` (weak-skip-last-item), and the
#       default-shaped lambda (weak-reverse-order). No rival holds this binder
#       fixed, so the spec's dependence on the INJECTED conversion — the whole
#       point of the extension — is demonstrated.
#   - serializeResult.it — VARIED across three distinct items: one whose two
#       observables differ (idText "a" / displayText "b"; weak-default-swap-fields
#       and weak-default-extra-field), one probing the identifier field alone
#       (idText "5"; weak-default-const-id), and a third (idText "7"; weak-
#       default-drop-text-field). Not held fixed, so the post-image's dependence
#       on `it` is demonstrated at three points.
#   Both independent clauses are attacked, and each on every axis it has:
#     (A) the deferral `out = items.map serialize` — WHICH function is applied
#         (inline-default, first-item), HOW MANY entries (skip-last), and in WHAT
#         ORDER (reverse-order, which is right on the first two axes and wrong
#         only on the third).
#     (B) the default object `out = defaultSerialized it` — a field's VALUE
#         (swap-fields on both jointly, const-id on the identifier alone) and the
#         exact FIELD SET (extra-field from above, drop-text-field from below).
#   The order of the two default fields is pinned by admiss-default-nondegenerate
#   and weak-default-swap-fields. NOTE the two clauses' order axes are distinct
#   and both now covered: (A)'s is the order of ENTRIES across items, (B)'s is the
#   order of KEYS within one entry.
#
# POSITIVE-CONTROL STRENGTH. pos-build-eta and pos-serialize-viadefault are
#   definitional reshapes (an eta-expansion and a delta-unfold), so each verifies
#   by reduction and neither really re-proves the obligation; they are kept as
#   cheap controls. pos-build-foldr is the load-bearing SPEC-TOO-STRONG probe: a
#   right fold is equal to the map only by induction on the list, `loom_solve`
#   alone leaves the goal `List.foldr (fun it acc => serialize it :: acc) [] items
#   = List.map serialize items` open, and the case supplies that induction. A
#   spec too strong for a non-definitional correct impl would fail there and
#   nowhere else in the soundness lane.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (mapping.md §3), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
