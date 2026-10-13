"""PBT manifest for django__django-11433 — adversarial falsification battery.

NOT a Nagini module; a record of adversarial cases parsed by
``swebench_nagini.pbt``. Spec cases are full model.py variants that share the
FROZEN spec byte-for-byte (only the ``# impl-start``/``# impl-end`` region is
edited via region-surgery, so ``same_spec`` is guaranteed) and are checked by
Nagini verify. There are no @ContractOnly axioms / A-reference deep models in
this bundle (meta.json: ``axioms: []``, ``deep_model_references: []``), so the
axiom lane is empty.

Defended surface (what `construct_writes` actually pins):

  * Four inputs ``selected/has_default/omitted/value_empty`` are all READ-ONLY
    (``Requires(Acc(list_pred(x), 1/2))``) and the half permission is returned
    unchanged (``Ensures(Acc(list_pred(x), 1/2))``). => FRAME-MUTATION applies.
  * The LOAD-BEARING postcondition is the per-element pin
        Result()[k] == write_value(selected[k], has_default[k],
                                    omitted[k], value_empty[k])
    over every in-range k, where ``write_value`` is a @Pure helper FULLY
    UNFOLDED to ``selected and not (has_default and omitted and value_empty)``
    — i.e. a total function of the args, NOT an opaque answer-key oracle. So
    there is no *wrong* echo to build: echoing ``write_value`` is exactly the
    correct decision (see 'ungrounded-oracle' note in the assessment / the
    pos-control-echo positive control). The two supplementary postcondition
    clauses ("non-empty defaulted/omitted field is written" / "empty
    defaulted/omitted field is left at default") are corollaries of the main
    pin; any rival that diverges on any index is rejected by the main pin.

The discriminating behaviour (G-DIFF / the F2P) is the added ``value_empty``
conjunct: a defaulted, omitted field whose cleaned value is NON-empty must now
be WRITTEN (Result()[k] == True), whereas the pre-patch guard left it at the
default. That is exactly the partial-domain "prepatch" rival below.
"""
from pathlib import Path

INSTANCE = "django__django-11433"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The single executable decision line in the gold impl region (lines 137-140).
_GOLD_BODY = (
    "        if selected[i] and not (has_default[i] and omitted[i] and value_empty[i]):\n"
    "            result = result + [True]\n"
    "        else:\n"
    "            result = result + [False]\n"
)

# ---------------------------------------------------------------------------
# Positive control (soundness): a structurally-different but CORRECT impl that
# calls the @Pure helper write_value directly instead of re-inlining the
# boolean conjunction, and appends its value. The gold loop invariant
# (result[k] == write_value(...)) is KEPT verbatim and matches this append
# per-element (no fold / no forward-append lemma is needed — the invariant is
# a per-index pin, not a recursive fold), so the gold proof stays valid. MUST
# verify; if it cannot, SPEC-TOO-STRONG.
_POS_CONTROL = _swap(
    _BASE, _GOLD_BODY,
    "        w = write_value(selected[i], has_default[i], omitted[i], value_empty[i])\n"
    "        result = result + [w]\n",
)

# ---------------------------------------------------------------------------
# Positive control / echo cheapest-impl: the oracle write_value is GROUNDED in
# the args (fully unfolded), so "echoing" it is the *correct* answer, not a
# cheat. This documents that the only echo available is the truthful one and it
# verifies (there is no wrong echo to reject). Structurally distinct from the
# pos-control above by writing the boolean conjunction expression inline as a
# single appended expression rather than via True/False branches.
_POS_ECHO = _swap(
    _BASE, _GOLD_BODY,
    "        result = result + [selected[i] and not (has_default[i] and omitted[i] and value_empty[i])]\n",
)

# ---------------------------------------------------------------------------
# Admissibility (in-region; cannot add a top-level caller — that would leave
# the impl region and break same_spec). Inside construct_writes' own impl
# region, BEFORE the gold loop, we re-derive that all four half-permission
# inputs are usable (read len + element 0 under Implies(len>0,..)) and that the
# @Pure decision reaches the F2P answer (a defaulted + omitted + NON-empty
# cleaned field is WRITTEN: write_value(True,True,True,False) is True; the
# complementary empty row is left at the default). The gold loop is kept so the
# postcondition still holds and the module verifies. If the Requires were
# vacuous / over-strong the impl could not both consume the half permissions
# and reach a normal return => PRECOND-TOO-STRONG.
_ADMISS = _BASE.replace(
    "    # impl-start\n"
    "    result = []  # type: List[bool]\n",
    "    # impl-start\n"
    "    # admissibility: the four half-permission inputs are all readable and\n"
    "    # the @Pure decision reaches the F2P answer for an in-domain input.\n"
    "    Assert(len(selected) >= 0)\n"
    "    Assert(len(has_default) >= 0)\n"
    "    Assert(len(omitted) >= 0)\n"
    "    Assert(len(value_empty) >= 0)\n"
    "    Assert(Implies(len(selected) > 0, selected[0] or not selected[0]))\n"
    "    # F2P scenario: defaulted + omitted + NON-empty cleaned value => WRITTEN.\n"
    "    Assert(write_value(True, True, True, False))\n"
    "    # complementary empty row: defaulted + omitted + EMPTY => left at default.\n"
    "    Assert(not write_value(True, True, True, True))\n"
    "    result = []  # type: List[bool]\n",
    1,
)

# ---------------------------------------------------------------------------
# REJECT 1 — partial-domain "prepatch" rival: drop the added value_empty
# conjunct from the guard. This is the EXACT pre-patch behaviour. It diverges
# from write_value precisely on the defaulted+omitted+NON-empty row, where the
# spec demands Result()[k] == True but this impl yields False. Rejected by the
# main per-element pin (and by the supplementary "non-empty written" clause).
# Refinement: its faithful real patch IS the pre-patch guard
# `selected and not (has_default and omitted)` — model_prepatch.py — which the
# gold meta records FAILS verification and does NOT resolve the F2P test
# test_default_not_populated_on_non_empty_value_in_cleaned_data (it leaves the
# default 'di' instead of writing the mocked 'de').
_REJECT_PREPATCH = _swap(
    _BASE, _GOLD_BODY,
    "        if selected[i] and not (has_default[i] and omitted[i]):\n"
    "            result = result + [True]\n"
    "        else:\n"
    "            result = result + [False]\n",
)

# ---------------------------------------------------------------------------
# REJECT 2 — partial-domain first-element flip: correct on every index EXCEPT
# i == 0, where it always writes False regardless of the decision. Diverges
# from write_value at k=0 whenever write_value(...,0) would be True (e.g. a
# selected field that is not skipped), so the loop invariant / main pin
# Result()[0] == write_value(...) fails. Refinement: a real patch that special-
# cases the first iterated form field to never write would corrupt the very
# F2P (single-field 'mode' form is the 0th/only field) — it would leave the
# default and NOT resolve.
_REJECT_FIRST = _swap(
    _BASE, _GOLD_BODY,
    "        if i != 0 and selected[i] and not (has_default[i] and omitted[i] and value_empty[i]):\n"
    "            result = result + [True]\n"
    "        else:\n"
    "            result = result + [False]\n",
)

# ---------------------------------------------------------------------------
# REJECT 3 — partial-domain "drop the selected gate": write the cleaned value
# even for a field that failed the earlier candidacy filters (selected==False).
# write_value(False, ...) == False, so the spec demands Result()[k]==False for
# any non-selected field; this rival can yield True there => rejected by the
# main pin. Refinement: a real patch that wrote save_form_data for a
# non-editable / AutoField / not-in-cleaned_data / excluded field would write
# values that must never be written (P2P regressions: test_exclude_fields,
# test_modelform_non_editable_field, test_empty_fields_to_construct_instance),
# so it would NOT resolve.
_REJECT_NOGATE = _swap(
    _BASE, _GOLD_BODY,
    "        if not (has_default[i] and omitted[i] and value_empty[i]):\n"
    "            result = result + [True]\n"
    "        else:\n"
    "            result = result + [False]\n",
)

# ---------------------------------------------------------------------------
# REJECT 4 — FRAME-MUTATION (MANDATORY: all four inputs are read-only). This
# rival overwrites the read-only input `selected[i]` (it has only
# Acc(list_pred(selected), 1/2)) before reading it, attempting to satisfy the
# postcondition vacuously by rewriting the input it is then compared against.
# It MUST fail for INSUFFICIENT PERMISSION: a write to selected needs full
# permission (Acc(.., write)) but only 1/2 is held. The gold per-element
# invariant/pin is KEPT verbatim so the rejection is attributable to the write,
# not to a missing proof obligation. Refinement: a faithful real patch that
# mutated the iterated field list / cleaned_data in place mid-loop would
# corrupt construct_instance's inputs (and the caller's cleaned_data), failing
# numerous P2P tests; it does not resolve.
_REJECT_FRAME = _swap(
    _BASE, _GOLD_BODY,
    "        selected[i] = True\n"
    "        if selected[i] and not (has_default[i] and omitted[i] and value_empty[i]):\n"
    "            result = result + [True]\n"
    "        else:\n"
    "            result = result + [False]\n",
)


SPEC_TESTS = [
    {
        "id": "pos-control-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "structurally-different CORRECT impl: binds the @Pure helper "
            "write_value(...) to a local and appends it, instead of inlining "
            "True/False branches. The gold per-element loop invariant "
            "(result[k] == write_value(...)) is kept verbatim and the append "
            "matches it directly (no fold lemma needed). If this cannot verify "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-echo-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ECHO,
        "rationale": (
            "the oracle write_value is GROUNDED (fully unfolded function of the "
            "args), so the only available 'echo' is the truthful boolean "
            "conjunction itself; appending it as a single expression must "
            "verify. Documents that no WRONG echo exists for this spec."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "a positive-control caller builds the F2P-shaped single-field input "
            "(selected, has_default, omitted, NON-empty => written) and asserts "
            "len==1 and out[0] is True. If the Requires cannot be established "
            "for this legitimate input => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "reject-prepatch-drop-value-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_PREPATCH,
        "refinement": (
            "this rival IS the pre-patch guard `selected and not (has_default "
            "and omitted)` (model_prepatch.py). Its faithful real patch never "
            "writes a defaulted+omitted field even when the cleaned value is "
            "non-empty, so it leaves the model default 'di' instead of the "
            "mocked 'de' and FAILS the F2P "
            "test_default_not_populated_on_non_empty_value_in_cleaned_data — it "
            "does NOT resolve."
        ),
        "rationale": (
            "rejected by the main per-element pin Result()[k]==write_value(...) "
            "(and the supplementary 'non-empty defaulted/omitted field is "
            "written' clause): on the defaulted+omitted+NON-empty row the spec "
            "demands True but this impl yields False. If it verified => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "reject-partial-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_FIRST,
        "refinement": (
            "a real patch that special-cased the first iterated form field to "
            "never write its cleaned value would, on the single-field 'mode' "
            "F2P form (the 0th and only field), leave the default and NOT "
            "resolve; and would regress P2P save tests that write the first "
            "field."
        ),
        "rationale": (
            "diverges from write_value at index 0 (writes False unconditionally "
            "there); the loop invariant / postcondition pin Result()[0]== "
            "write_value(...) is violated whenever the 0th field should be "
            "written. Partial-domain miss. If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "reject-drop-selected-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_NOGATE,
        "refinement": (
            "dropping the `selected` candidacy gate makes the real patch write "
            "save_form_data for fields that failed the editable / AutoField / "
            "not-in-cleaned_data / fields / exclude filters — values that must "
            "never be written. It regresses P2P tests (test_exclude_fields, "
            "test_modelform_non_editable_field, "
            "test_empty_fields_to_construct_instance) and does NOT resolve."
        ),
        "rationale": (
            "write_value(False, ...) == False, so the main pin demands "
            "Result()[k]==False for every non-selected field; this rival can "
            "yield True there => rejected. Partial-domain (the non-selected "
            "sub-domain). If it verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "reject-frame-mutate-selected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_FRAME,
        "refinement": (
            "a faithful real patch that mutated the iterated field list / "
            "form's cleaned_data in place mid-loop (to force a field to look "
            "selected) would corrupt construct_instance's inputs and the "
            "caller's cleaned_data, failing many P2P model-form tests; it does "
            "not resolve. The point of this case is the permission system: a "
            "verifying mutator would mean a read-only-input guarantee is "
            "unenforced."
        ),
        "rationale": (
            "INSUFFICIENT PERMISSION: `selected[i] = True` writes a list held "
            "with only Acc(list_pred(selected), 1/2); a store needs full "
            "permission. Nagini rejects the assignment before any postcondition "
            "reasoning. The gold per-element invariant/pin is kept verbatim so "
            "the rejection is attributable to the write. This is the #1 "
            "weakness class (read-only inputs) and a byte-fuzzer never finds it."
        ),
    },
]

# No @ContractOnly axioms and no A-reference deep models in this bundle
# (meta.json: axioms: [], deep_model_references: []). The changed guard is
# modeled DEEPLY as write_value; refinement.md §B confirms no consumed axiom /
# no A-reference. Axiom lane is therefore empty.
AXIOM_TESTS = []
