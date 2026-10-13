# properties.py — G-PBT falsification battery for django__django-15561 (lean lane).
#
# PORTED from the nagini sibling's battery. The adversarial ARGUMENTS are carried
# over; the mechanics are re-expressed against this backend's carrier. Each
# SPEC_TESTS entry is a FULL Solution.lean variant that shares the FROZEN spec
# byte-for-byte (only the impl region — and, where a positive genuinely reproves,
# the proof body — is edited), so markers.same_spec holds by construction and any
# rejection is attributable to the postcondition rather than to a tampered spec.
# Every expect="reject" case carries a refutation `witness`: a snippet that
# ELABORATES against the rival and FAILS on the frozen solution, checked in a file
# with the obligation removed. Without it, "did not verify" would only mean the
# frozen tactic script stopped matching a reshaped impl.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
# ---------------------------------------------------------------------------
# ONE obligation: `theorem correct_requiresColumnChange`, over
#
#   problem_spec_requiresColumnChange (old new : FieldDesc) (result : Bool)
#
# with `FieldDesc` observed through four components — `column`, `path`, `args`,
# `kwargs` — and the postcondition pinning `result` to the exact verdict of a
# TWO-CLAUSE disjunction:
#
#   (1) the backend-quoted column names differ, OR
#   (2) the (path, args, kwargs) descriptions still differ after the
#       column-irrelevant keyword arguments are dropped from BOTH sides.
#
# Clause (2) is the point of interest, and it is load-bearing in three separable
# ways a rival can each abuse independently:
#   * WHICH attribute names are dropped. The dropped set is
#     `"choices" :: otherNonColumnAttrs` — the permitted-choices attribute
#     TOGETHER WITH the stable column-irrelevant set. Dropping too FEW leaves a
#     change that should be a no-op looking like a difference; dropping too MANY
#     hides a real column difference. The postcondition is an equality to the
#     exact verdict, so it cuts both ways.
#   * That the drop happens on BOTH descriptions, not one.
#   * WHICH components are compared: `path`, `args` and the surviving `kwargs`
#     are all inside the compared triple, and the combination with clause (1) is
#     a disjunction, not a conjunction.
#
# CARRIER NOTE. The nagini sibling split this decision across two contracted
# functions — a `PSet[int]` of attribute codes and a boolean scan over three
# parallel sequences behind fractional read permission. This bundle models the
# same decision as ONE total function over a transparent `FieldDesc` pair, so the
# nagini cases attached to the set-valued function and to the index-scan loop
# have no separate obligation to attack here; their ARGUMENTS re-land as rivals
# against the single `ignoredAttrs`-driven drop (see the per-case rationales,
# which name the nagini case each one ports). Case-count parity with nagini is
# therefore not the target; coverage of the surface THIS bundle models is.
#
# Nagini-case disposition, so the mapping is checkable rather than asserted:
#   pos-sia-reorder            -> 2b (verify-clauses-commuted)
#   pos-fan-conj               -> 2a (verify-direct-filter)
#   admiss-sia / admiss-fan    -> 3 (admiss-noop-point-reachable)
#   weak-drop-choices          -> 1a (reject-omit-enumeration-attr)
#   weak-drop-verbose          -> 1b (reject-omit-settled-attrs)
#   weak-superset-extra-attr   -> 1d (reject-superset-column-attr)
#   partial-drop-last          -> 1c (reject-drop-last-settled-attr)
#   partial-skip-first         -> 1k (reject-skip-first-surviving-kwarg)
#   frame-mut-non_db-write-perm-> VACUOUS here; see LANES THAT DO NOT PORT.
#
# Cases with no nagini counterpart, justified by THIS carrier's surface:
#   1e (one-sided drop), 1g/1h/1j (the three compared components),
#   1l (unquoted column compare — added by audit, attack D),
#   2c (drop-pass order), 2d (reversed surviving lists — added by audit,
#   attack E).
#
# PARTIALLY-OPAQUE CARRIER. Two spec ingredients are `opaque` with no
# constraining axiom: the identifier-quoting function, and the stable
# column-irrelevant attribute-name list. So `decide` cannot compute the verdict
# at a literal input, and the witnesses instead CONDITION on the carrier: they
# assume just enough about the opaque term to separate rival from spec (one
# hypothesis per opaque term, kept as weak as the refutation needs, so the
# assumptions stay jointly satisfiable). The remaining structure — which
# components are compared, whether the drop is two-sided, how the clauses are
# combined — is fully transparent and refutable at literals.
#
# ---------------------------------------------------------------------------
# LANES THAT DO NOT PORT
# ---------------------------------------------------------------------------
#   * FRAME / PERMISSION-MUTATION (nagini's mandatory class: the read-only input
#     was held at half permission and the rival over-claimed full write
#     permission). Lean is referentially transparent — no aliasing, no fractional
#     permission, nothing an impl could write back into an input — so this class
#     is VACUOUS here, not merely unported. No substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION. VACUOUS on this lean bundle, but the port's
#     original reason ("a diverging implementation cannot be written at all")
#     was WRONG and is corrected here, because the corrected reason is the one a
#     reviewer can check. A diverging impl CAN be written: marking the impl
#     `partial` and letting it call itself is admissible under variant_scope
#     (measured: `variant_problems` returns []). What makes the class vacuous is
#     that such a rival is unshippable for a MECHANICAL reason rather than a
#     semantic one — a `partial def` is opaque to reduction, so the frozen
#     obligation cannot be discharged for it (the variant fails with `Tactic
#     `unfold` failed to unfold implementation_requiresColumnChange`), and no
#     witness can be built either: an unconditioned witness fails with the same
#     unfold error, and a witness CONDITIONED on the impl's value elaborates
#     against gold too (measured: rival exit 0, gold exit 0 — `witness-vacuous`,
#     since the hypothesis is unsatisfiable for gold's actual value and the
#     conditioned claim is then true of anything). So the rejection would attest
#     to irreducibility, not to the spec. This bundle's lean backend has no
#     `loom.semantics.termination` setting at all (the frozen solution declares
#     none — checked); the total-carrier disposition applies, and the nagini
#     sibling carries no divergence case either. On velvet under partial
#     termination semantics the same rival would be a KNOWN SPEC HOLE rather
#     than a vacuous class — see the corpus-wide termination-semantics finding.
#   * AXIOM_TESTS. The axiom lane belongs to G-AX, which this gate ignores; the
#     changed behavior is modeled deeply and consumes no callee axiom anyway.
from pathlib import Path

INSTANCE = "django__django-15561"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl region (or, for the _PROOF_*
# anchors, inside the proof region) and is unique in the file, so every _swap
# keeps the spec view — and hence same_spec — identical.
# ---------------------------------------------------------------------------

_OLD_DROP = ("  for attr in ignoredAttrs do\n"
             "    oldKwargs := oldKwargs.filter (fun kv => kv.1 != attr)\n")
_NEW_DROP = ("  for attr in ignoredAttrs do\n"
             "    newKwargs := newKwargs.filter (fun kv => kv.1 != attr)\n")
_RETURN = ("  return (quoteIdentifier old.column != quoteIdentifier new.column) ||\n"
           "         decide ((old.path, old.args, oldKwargs) ≠ "
           "(new.path, new.args, newKwargs))\n")
_ACC_INIT = "  let mut oldKwargs := old.kwargs\n  let mut newKwargs := new.kwargs\n"
_IMPL_BODY = _ACC_INIT + _OLD_DROP + _NEW_DROP + _RETURN

# The proof region body. Split so a positive can either append to it or replace
# part of it, while the `theorem` STATEMENT stays byte-identical (variant_scope
# rule 2) and no new lemma / axiom / `sorry` is introduced (rule 3).
_PROOF_INTRO = "  intro old new\n"
_PROOF_UNFOLD = ("  unfold problem_spec_requiresColumnChange "
                 "implementation_requiresColumnChange\n")
_PROOF_TAIL = "  simp only [key, popAttrs, isIgnored]\n"

# The FULL proof-region body (everything between the `:= by` and the region's
# end marker), for the one positive whose impl shape makes the frozen script's
# loop-to-filter bridging step inapplicable and so must re-close from scratch.
_PROOF_BODY = _BASE[_BASE.index(":= by\n") + len(":= by\n"):
                    _BASE.index("\n-- proof-end")]

for _a in (_OLD_DROP, _NEW_DROP, _RETURN, _ACC_INIT, _IMPL_BODY,
           _PROOF_INTRO, _PROOF_UNFOLD, _PROOF_TAIL):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted or not unique: {_a[:60]!r}")


# ---------------------------------------------------------------------------
# Witness construction.
#
# A witness states `¬ problem_spec_… old new (implementation_… old new)` at ONE
# concrete input pair: the rival's answer there provably differs from the verdict
# the postcondition demands. Gold satisfies the spec everywhere, so the same
# snippet cannot close against the frozen solution — which is the half that makes
# it a discriminator rather than a tautology.
#
# The attribute names below are neutral placeholders, not repository identifiers:
# the stable ignored-name list is opaque, so a witness that needs to know its
# contents simply ASSUMES a concrete small value for it. That single hypothesis
# is satisfiable (one equation naming one value for one opaque list), so the
# refutation never rests on a contradiction.
# ---------------------------------------------------------------------------

_IGNORED_A = "settledIgnoredFirst"    # a member of the stable ignored set
_IGNORED_B = "settledIgnoredLast"     # its last member (for the near-miss rival)
_COLUMN_ATTR = "columnShapeAttr"      # an attribute that DOES define the column
_COLUMN_ATTR_2 = "otherShapeAttr"     # a SECOND column-defining attribute, so a
                                      # witness can place a surviving difference
                                      # at a chosen POSITION in the kwargs list


def _fd(column, path, args, kwargs):
    """A `FieldDesc` literal."""
    a = "[" + ", ".join(f'"{x}"' for x in args) + "]"
    k = "[" + ", ".join(f'("{n}", "{v}")' for n, v in kwargs) + "]"
    return (f'{{ column := "{column}", path := "{path}", '
            f"args := {a}, kwargs := {k} }}")


def _witness(old, new, binders="", extra_simp=()):
    """`¬ problem_spec … (implementation …)` at the concrete pair (old, new)."""
    head = f"example {binders} :\n" if binders else "example :\n"
    simp = ", ".join(("Id.run", "bind", "pure", "ignoredAttrs", "isIgnored",
                      "popAttrs") + tuple(extra_simp))
    return (
        "-- Refutation at one concrete input pair: the rival's answer there\n"
        "-- contradicts the verdict the postcondition pins. Elaborates against\n"
        "-- the rival; cannot close against the frozen solution.\n"
        + head
        + "    ¬ problem_spec_requiresColumnChange\n"
        + f"        {old}\n        {new}\n"
        + "        (implementation_requiresColumnChange\n"
        + f"          {old}\n          {new}) := by\n"
        + "  " + _PROOF_UNFOLD.strip() + "\n"
        + f"  simp [{simp}]\n")


# The stable ignored-name list is opaque; a witness that must know it names one
# concrete value. Two sizes: a one-element list, and a two-element list for the
# rival that mishandles only the LAST member.
_H_STABLE_1 = f'(hStable : otherNonColumnAttrs = ["{_IGNORED_A}"])'
_H_STABLE_2 = (f'(hStable : otherNonColumnAttrs = ["{_IGNORED_A}", '
               f'"{_IGNORED_B}"])')


SPEC_TESTS = []

# ===========================================================================
# 1. UNIQUENESS RIVALS — wrong impls that share the frozen spec. Each must be
#    REJECTED (a rival that VERIFIES is SPEC-TOO-WEAK), and each ships a witness
#    that has been SEEN to hold of the rival and fail on gold.
# ===========================================================================

# --- 1a. Drops too FEW names: the permitted-choices attribute is left out of the
#     dropped set, so a change touching only it survives as a difference. This is
#     the port of nagini's `weak-drop-choices` (there: the set-valued function
#     omits the enumeration attribute's code, refuted by the pinned membership
#     clause). Here the same argument lands on clause (2)'s drop step.
SPEC_TESTS.append({
    "id": "reject-omit-enumeration-attr",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _swap(_BASE, _OLD_DROP, _OLD_DROP.replace("ignoredAttrs",
                                                  "otherNonColumnAttrs")),
        _NEW_DROP, _NEW_DROP.replace("ignoredAttrs", "otherNonColumnAttrs")),
    "rationale": "REJECT comes from postcondition clause (2). The spec drops "
                 "`\"choices\" :: otherNonColumnAttrs` from both descriptions; "
                 "this impl drops only `otherNonColumnAttrs`. At the witness "
                 "point the two descriptions agree on column, path and args and "
                 "differ ONLY in the permitted-choices keyword argument, so the "
                 "spec's compared triples become equal and it demands `false`, "
                 "while the impl retains the differing entry and yields `true`. "
                 "Binders varied: `old.kwargs` / `new.kwargs` (the value at the "
                 "permitted-choices name); column/path/args held equal so the "
                 "refutation is attributable to the drop set alone.",
    "refinement": "the faithful real patch is the one that leaves the "
                  "permitted-choices attribute out of the column-irrelevant "
                  "set. A change that only adjusts a field's permitted choices "
                  "then still compares unequal, the decision reports that a "
                  "column-level change is required, and the schema editor emits "
                  "the table-rebuild SQL the issue says should not be generated. "
                  "The single FAIL_TO_PASS test asserts that exact alteration "
                  "runs with zero queries, so this rival does NOT resolve — it "
                  "is the behavior the change exists to eliminate.",
    "witness": _witness(
        _fd("name", "CharField", ["255"], [("choices", "[]")]),
        _fd("name", "CharField", ["255"], [("choices", "[(Jane,Jane)]")]),
        binders=_H_STABLE_1, extra_simp=("hStable",)),
})

# --- 1b. The MIRROR omission: drops the permitted-choices attribute but loses
#     the whole stable set. Ports nagini's `weak-drop-verbose` (a subtler pinned
#     member is missing) — the argument being that clause (2)'s drop set is
#     `"choices" :: otherNonColumnAttrs`, and BOTH halves are load-bearing.
SPEC_TESTS.append({
    "id": "reject-omit-settled-attrs",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _swap(_BASE, _OLD_DROP, _OLD_DROP.replace("ignoredAttrs",
                                                  '["choices"]')),
        _NEW_DROP, _NEW_DROP.replace("ignoredAttrs", '["choices"]')),
    "rationale": "REJECT from clause (2), attacking the OTHER half of the drop "
                 "set than 1a: this impl drops only the permitted-choices name "
                 "and keeps every stable column-irrelevant name. The witness "
                 "point differs only in a stable ignored attribute's value, so "
                 "the spec demands `false` and the impl returns `true`. Binders "
                 "varied: `old.kwargs` / `new.kwargs` at a stable ignored name "
                 "(a DIFFERENT kwargs point from 1a, which varied the "
                 "permitted-choices name), with column/path/args held equal.",
    "refinement": "the faithful real patch would narrow the column-irrelevant "
                  "set to the permitted-choices attribute alone, discarding the "
                  "long-settled names. A change touching only one of those — "
                  "presentational and validation-level attributes that have no "
                  "bearing on the stored column — would then wrongly be treated "
                  "as requiring a column change. The PASS_TO_PASS suite pins "
                  "that no queries are performed when changing field attributes "
                  "that do not affect the schema, so this rival regresses a "
                  "test that passes today and does NOT resolve.",
    "witness": _witness(
        _fd("name", "CharField", ["255"], [(_IGNORED_A, "before")]),
        _fd("name", "CharField", ["255"], [(_IGNORED_A, "after")]),
        binders=_H_STABLE_1, extra_simp=("hStable",)),
})

# --- 1c. NEAR-MISS of 1b: keeps almost all of the stable set but loses its LAST
#     member. Ports nagini's `partial-drop-last` off-by-one (its loop stopped one
#     element short). It gets its OWN witness — at the last stable name, the
#     point where the off-by-one bites — rather than sharing 1b's.
#     AUDIT CORRECTION. The port's rationale here claimed this rival "agrees
#     with gold at 1b's point, which is why it needs its own witness". That is
#     FALSE on this carrier and was measured false: 1b's witness, built against
#     THIS rival, elaborates (exit 0). The reason is that `hStable` in 1b's
#     witness pins the stable list to a ONE-element value, and `dropLast` of the
#     two-element `ignoredAttrs` ("choices" :: that one element) drops that
#     element, so this rival retains it there exactly as it retains the last
#     name generally. The witness is still a correct and useful one — it probes
#     a DIFFERENT drop-set value (a two-element stable list, so `dropLast`
#     retains a name 1b's one-element point cannot expose) — so the case stands
#     on that ground rather than on the disproven disjointness claim.
SPEC_TESTS.append({
    "id": "reject-drop-last-settled-attr",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _swap(_BASE, _OLD_DROP,
              _OLD_DROP.replace("ignoredAttrs", "ignoredAttrs.dropLast")),
        _NEW_DROP,
        _NEW_DROP.replace("ignoredAttrs", "ignoredAttrs.dropLast")),
    "rationale": "REJECT from clause (2): an off-by-one on the drop set. This "
                 "impl drops every ignored name EXCEPT the last, so it is "
                 "correct wherever the last name is absent or unchanged, and "
                 "wrong exactly when it carries the sole difference. The "
                 "witness sits at that sub-domain — the descriptions differ only "
                 "in the LAST stable ignored name's value — so the spec demands "
                 "`false` and the impl yields `true`. Binders varied: "
                 "`old.kwargs` / `new.kwargs` at the last stable name, AND the "
                 "assumed value of the opaque stable list — this is the only "
                 "witness in the battery that pins it to a TWO-element value, "
                 "which is what makes `dropLast` retain a genuinely stable name "
                 "rather than the permitted-choices head. (Audited: this rival "
                 "is ALSO refuted by 1b's one-element witness — measured, exit "
                 "0 — so the two points are not disjoint; the case earns its "
                 "place by varying the drop-set SIZE, not by being the sole "
                 "refutation.)",
    "refinement": "the faithful real patch would iterate the column-irrelevant "
                  "names but stop one short of the end, silently retaining the "
                  "final name. A field pair whose only difference is on that "
                  "attribute is then treated as requiring a column-level "
                  "change, so a no-op alteration emits SQL and the PASS_TO_PASS "
                  "test pinning zero queries for schema-neutral attribute "
                  "changes fails. Does NOT resolve.",
    "witness": _witness(
        _fd("name", "CharField", [], [(_IGNORED_B, "before")]),
        _fd("name", "CharField", [], [(_IGNORED_B, "after")]),
        binders=_H_STABLE_2, extra_simp=("hStable",)),
})

# --- 1d. Drops too MANY names: a column-DEFINING attribute is smuggled into the
#     dropped set, hiding a real difference. Ports nagini's
#     `weak-superset-extra-attr` — the exact shape that VERIFIED under an
#     earlier membership-only postcondition and is closed by pinning `result` to
#     the exact verdict.
SPEC_TESTS.append({
    "id": "reject-superset-column-attr",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _swap(_BASE, _OLD_DROP,
              _OLD_DROP.replace("ignoredAttrs",
                                f'"{_COLUMN_ATTR}" :: ignoredAttrs')),
        _NEW_DROP,
        _NEW_DROP.replace("ignoredAttrs",
                          f'"{_COLUMN_ATTR}" :: ignoredAttrs')),
    "rationale": "REJECT from clause (2) in the OPPOSITE direction to 1a-1c: "
                 "the postcondition is an EQUALITY to the exact verdict, so "
                 "dropping a name the spec does NOT drop is refutable too. The "
                 "witness point differs only in an attribute outside the "
                 "column-irrelevant set, so the spec's triples still differ and "
                 "it demands `true`, while this impl removes the entry from both "
                 "sides and yields `false`. Binders varied: `old.kwargs` / "
                 "`new.kwargs` at a name NOT in the drop set — a third distinct "
                 "kwargs point, and the only witness whose expected verdict is "
                 "`true` rather than `false`.",
    "refinement": "the faithful real patch would add a column-defining "
                  "attribute to the column-irrelevant set. The decision then "
                  "strips it before comparing, a change that genuinely alters "
                  "the stored column is reported as a no-op, and the required "
                  "SQL is never emitted. The PASS_TO_PASS suite contains "
                  "alterations that change exactly such an attribute and assert "
                  "the column really changed, so they fail. Does NOT resolve — "
                  "and this is the verify-does-not-imply-resolve shape a "
                  "membership-only postcondition would have admitted.",
    "witness": _witness(
        _fd("name", "CharField", [], [(_COLUMN_ATTR, "255")]),
        _fd("name", "CharField", [], [(_COLUMN_ATTR, "128")]),
        binders=_H_STABLE_1, extra_simp=("hStable",)),
})

# --- 1e. Drops from ONE description only. Clause (2) says "from BOTH
#     descriptions"; nagini had no counterpart (its scan compared parallel
#     sequences elementwise, so one-sidedness was not expressible), so this rival
#     is NEW work justified by this carrier's asymmetry.
SPEC_TESTS.append({
    "id": "reject-one-sided-drop",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _NEW_DROP, ""),
    "rationale": "REJECT from the BOTH-sides requirement inside clause (2). "
                 "This impl drops the column-irrelevant keyword arguments from "
                 "the first description only, so the two compared kwargs lists "
                 "are no longer normalized alike. The witness point has the "
                 "ignored entry present on ONE side only: the spec drops it from "
                 "both, leaving the triples equal and demanding `false`, while "
                 "the impl leaves it on the undropped side and yields `true`. "
                 "Binders varied: the PRESENCE of a kwargs entry, asymmetrically "
                 "between `old.kwargs` and `new.kwargs` — a shape none of the "
                 "other witnesses probes (they all vary a value present on both "
                 "sides).",
    "refinement": "the faithful real patch would strip the column-irrelevant "
                  "keyword arguments from the old field's description but not "
                  "the new one's. Adding a schema-neutral attribute to a field "
                  "then leaves an entry present on one side of the comparison "
                  "and absent from the other, so the decision reports a "
                  "column-level change is required and a no-op alteration emits "
                  "SQL. That is precisely the FAIL_TO_PASS scenario (the "
                  "permitted-choices attribute is absent before the change and "
                  "present after), so this rival does NOT resolve.",
    "witness": _witness(
        _fd("col", "TextField", ["a", "b"], []),
        _fd("col", "TextField", ["a", "b"], [("choices", "[(1,1)]")]),
        binders=_H_STABLE_1, extra_simp=("hStable",)),
})

# --- 1f. Drops clause (1) entirely. The quoting function is `opaque` with no
#     constraining axiom, so there is no literal at which `decide` can compute
#     it; the witness CONDITIONS on the carrier instead — assuming only that the
#     quoted forms of two distinct column names differ, which is exactly the
#     sub-domain where this rival is wrong.
SPEC_TESTS.append({
    "id": "reject-drop-column-clause",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return decide ((old.path, old.args, oldKwargs) ≠ "
                    "(new.path, new.args, newKwargs))\n"),
    "rationale": "REJECT from postcondition clause (1), the disjunct this impl "
                 "deletes. At the witness point the descriptions are otherwise "
                 "identical and only the column differs, so clause (1) alone "
                 "decides: the spec demands `true` and the impl yields `false`. "
                 "The quoting function is opaque, so the witness conditions on "
                 "the carrier — a SINGLE hypothesis, that the two quoted column "
                 "names differ — rather than computing it. Weaker than any "
                 "literal claim and satisfiable (one inequality about one opaque "
                 "function at two distinct points), so the refutation does not "
                 "rest on a contradiction. Binders varied: `old.column` / "
                 "`new.column` — the ONLY witness that moves the column binder; "
                 "every other holds it equal.",
    "refinement": "the faithful real patch would decide purely from the "
                  "deconstructed description and never compare the resolved "
                  "column names. Renaming the database column a field occupies "
                  "while leaving its construction arguments untouched would then "
                  "be reported as a no-op and the rename SQL never emitted. The "
                  "PASS_TO_PASS suite alters fields whose quoted column name is "
                  "what changes, so those tests fail. Does NOT resolve.",
    "witness": _witness(
        _fd("before_col", "IntegerField", [], []),
        _fd("after_col", "IntegerField", [], []),
        binders=('(hQuote : quoteIdentifier "before_col" ≠ '
                 'quoteIdentifier "after_col")'),
        extra_simp=("bne_iff_ne", "hQuote", "Bool.false_eq_true")),
})

# --- 1g. Narrows clause (2)'s compared triple: the class path is dropped from
#     the comparison. Attacks a component of the frame the postcondition pins.
SPEC_TESTS.append({
    "id": "reject-ignore-class-path",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return (quoteIdentifier old.column != "
                    "quoteIdentifier new.column) ||\n"
                    "         decide ((old.args, oldKwargs) ≠ "
                    "(new.args, newKwargs))\n"),
    "rationale": "REJECT from clause (2): the spec compares the full "
                 "`(path, args, kwargs)` triple, and this impl compares only "
                 "`(args, kwargs)`. At the witness point the columns, args and "
                 "kwargs all agree and only the class path differs, so the spec "
                 "demands `true` and the impl yields `false`. No conditioning is "
                 "needed: with both kwargs lists empty the drop step is inert "
                 "and the comparison is fully transparent. Binders varied: "
                 "`old.path` / `new.path` — the only witness that moves the path "
                 "binder.",
    "refinement": "the faithful real patch would compare the positional and "
                  "keyword construction arguments but not the field class "
                  "itself. Changing a field to a DIFFERENT class that happens to "
                  "deconstruct to the same arguments would then be reported as "
                  "a no-op and the column type never migrated. The PASS_TO_PASS "
                  "suite contains exactly such alterations (a field replaced by "
                  "one of another class, asserting the stored column type "
                  "changed), so they fail. Does NOT resolve.",
    "witness": _witness(_fd("data", "CharField", ["10"], []),
                        _fd("data", "TextField", ["10"], [])),
})

# --- 1h. Narrows clause (2)'s compared triple the other way: the positional
#     construction arguments are dropped from the comparison.
SPEC_TESTS.append({
    "id": "reject-ignore-positional-args",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return (quoteIdentifier old.column != "
                    "quoteIdentifier new.column) ||\n"
                    "         decide ((old.path, oldKwargs) ≠ "
                    "(new.path, newKwargs))\n"),
    "rationale": "REJECT from clause (2): the compared triple loses its "
                 "positional-argument component. At the witness point the "
                 "columns, paths and kwargs agree and only the positional "
                 "arguments differ, so the spec demands `true` and the impl "
                 "yields `false`. Binders varied: `old.args` / `new.args` — the "
                 "only witness that moves the args binder. Together with 1g "
                 "(path) and 1j (the surviving keyword arguments) this is the "
                 "third of the three component removals, which is what lets the "
                 "battery claim clause (2) pins all THREE components rather "
                 "than just some of them.",
    "refinement": "the faithful real patch would drop the positional "
                  "construction arguments from the comparison, keeping only the "
                  "class path and the keyword arguments. A field class that "
                  "deconstructs part of its column-defining configuration into "
                  "positional rather than keyword arguments would then have "
                  "changes to that configuration silently reported as no-ops, "
                  "and the column would never be migrated. NOTE, stated plainly "
                  "because it is the weakest refinement claim in this battery: "
                  "the field classes exercised by the FAIL_TO_PASS and "
                  "PASS_TO_PASS tests deconstruct to an EMPTY positional list, "
                  "so no shipped test distinguishes this rival — it is a "
                  "verify-does-not-imply-resolve break against the specified "
                  "behavior (the spec pins all three components) rather than a "
                  "test-visible regression. Does NOT resolve in the sense that "
                  "it silently drops a discrimination the decision is required "
                  "to make; a reviewer treating F2P/P2P as the only oracle "
                  "should read this case as defending the spec's frame rather "
                  "than a test.",
    "witness": _witness(_fd("amount", "DecimalField", ["12", "2"], []),
                        _fd("amount", "DecimalField", ["12", "4"], [])),
})

# --- 1j. Narrows clause (2)'s compared triple the THIRD way: the surviving
#     keyword arguments are dropped from the comparison altogether, so only
#     `path` and `args` are compared. Added by audit: 1g and 1h each removed ONE
#     component of the compared triple (path, args), but no rival removed the
#     `kwargs` component itself — the very component clause (2)'s drop step
#     produces. Without this the battery's claim that clause (2) "pins all three
#     components" rested on two of the three.
SPEC_TESTS.append({
    "id": "reject-ignore-kwargs-component",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return (quoteIdentifier old.column != "
                    "quoteIdentifier new.column) ||\n"
                    "         decide ((old.path, old.args) ≠ "
                    "(new.path, new.args))\n"),
    "rationale": "REJECT from clause (2): the spec compares the surviving "
                 "keyword arguments alongside `path` and `args`, and this impl "
                 "drops that component entirely — it still computes the drop "
                 "step, then never uses its result. At the witness point the "
                 "columns, paths and positional arguments all agree and the "
                 "descriptions differ ONLY in a keyword argument OUTSIDE the "
                 "drop set, so the spec demands `true` and this impl yields "
                 "`false`. Binders varied: `old.kwargs` / `new.kwargs` at a "
                 "column-defining name, with every other binder held equal — "
                 "the complement of 1g (path) and 1h (args), which is what "
                 "lets the battery claim clause (2) pins all THREE components. "
                 "AUDIT: this case previously shipped a witness BYTE-IDENTICAL "
                 "to 1d's and 1i's, so three cases rested on one refutation and "
                 "the manifest's per-case 'distinct kwargs point' claims were "
                 "not backed by distinct evidence. The witness now sits at a "
                 "SECOND column-defining attribute name, which 1d does NOT "
                 "refute (measured: 1d's rival drops only `columnShapeAttr`, so "
                 "this point survives its filter and its build exits 1 while "
                 "this rival's exits 0).",
    "refinement": "the faithful real patch would compare only the class path "
                  "and the positional construction arguments, discarding the "
                  "keyword arguments after normalizing them. Every alteration "
                  "whose column-defining configuration is carried in keyword "
                  "arguments — the ordinary case, since that is where a field's "
                  "column-shaping options live — would then be reported as a "
                  "no-op and the required SQL never emitted, while the drop "
                  "step's whole purpose (deciding WHICH keyword differences "
                  "matter) becomes dead code. The PASS_TO_PASS suite alters "
                  "fields whose keyword configuration is what changes and "
                  "asserts the column really changed, so those tests fail. "
                  "Does NOT resolve.",
    "witness": _witness(
        _fd("name", "CharField", [], [(_COLUMN_ATTR_2, "keep")]),
        _fd("name", "CharField", [], [(_COLUMN_ATTR_2, "altered")]),
        binders=_H_STABLE_1, extra_simp=("hStable",)),
})

# --- 1k. Ports nagini's `partial-skip-first`, the off-by-one at the START of the
#     scan (its loop guarded the disagreement check with `i > 0`, so the first
#     listed attribute was never considered). Added by audit: the port landed
#     nagini's LAST-element off-by-one as 1c but left the FIRST-element one with
#     no counterpart and no recorded reason, even though this carrier expresses
#     it directly — the compared kwargs lists are ordered, so `tail` skips the
#     leading surviving entry exactly as the `i > 0` guard skipped index 0.
#     The witness keeps a SECOND, agreeing column-defining entry after the
#     differing one, so the difference sits at the head position this rival
#     drops while the lists stay non-trivially long — the sub-domain where the
#     rival is wrong and 1a-1j all agree with gold.
SPEC_TESTS.append({
    "id": "reject-skip-first-surviving-kwarg",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return (quoteIdentifier old.column != "
                    "quoteIdentifier new.column) ||\n"
                    "         decide ((old.path, old.args, oldKwargs.tail) ≠ "
                    "(new.path, new.args, newKwargs.tail))\n"),
    "rationale": "REJECT from clause (2): an off-by-one at the FRONT of the "
                 "surviving keyword arguments, the mirror of 1c's off-by-one at "
                 "the end. The spec compares the whole surviving list; this "
                 "impl compares it from the second entry on, so it is correct "
                 "wherever the leading surviving entry agrees and wrong exactly "
                 "when that entry carries the sole difference. At the witness "
                 "point the two descriptions differ only in the FIRST surviving "
                 "keyword argument and agree on a second one that follows it, "
                 "so the spec demands `true` while this impl compares equal "
                 "tails and yields `false`. Binders varied: the POSITION of the "
                 "differing kwargs entry, with the surviving list kept "
                 "non-trivially long (two entries) so the refutation is about "
                 "WHICH entry is compared rather than about the list being "
                 "dropped wholesale. AUDIT CORRECTION. The port's rationale "
                 "here claimed this point is 'a distinct point from 1j, which "
                 "varies a lone entry (there the tails are both empty and this "
                 "rival would agree with gold)'. That is FALSE and was measured "
                 "false: at a lone-entry point both tails are `[]`, so this "
                 "rival compares nothing and returns `false` where the spec "
                 "demands `true` — it is WRONG there, not in agreement. Built "
                 "against 1j's witness (old form and new alike) this rival "
                 "exits 0. The case is kept because the impl is a genuinely "
                 "distinct wrong impl and its own witness exercises a longer "
                 "surviving list than any other case, but it is NOT the sole "
                 "refutation of its rival and the manifest no longer claims so.",
    "refinement": "the faithful real patch would iterate the surviving keyword "
                  "arguments but skip the first one, silently exempting "
                  "whichever attribute the deconstruction happens to emit "
                  "first. A change to that attribute alone is then treated as "
                  "requiring no column-level change, so a genuine column "
                  "alteration emits no SQL — and WHICH attribute is exempted "
                  "depends on deconstruction order rather than on whether it "
                  "affects the column, so the decision becomes order-dependent "
                  "in a way the specified behavior forbids. The PASS_TO_PASS "
                  "alterations that change a leading column-defining keyword "
                  "argument fail. Does NOT resolve.",
    "witness": _witness(
        _fd("name", "CharField", [],
            [(_COLUMN_ATTR, "255"), (_COLUMN_ATTR_2, "keep")]),
        _fd("name", "CharField", [],
            [(_COLUMN_ATTR, "128"), (_COLUMN_ATTR_2, "keep")]),
        binders=_H_STABLE_1, extra_simp=("hStable",)),
})

# --- 1l. ADDED BY AUDIT. Clause (1) compares the columns AFTER the quoting
#     function is applied; this rival compares the RAW column names instead. No
#     existing case probed this: 1f deletes clause (1) wholesale (so it is
#     refuted wherever the quoted names differ, which says nothing about whether
#     the quoting step is applied at all), and every other rival holds the two
#     columns equal, where the two spellings coincide. So the battery's coverage
#     of clause (1) rested entirely on the clause's PRESENCE, never on the
#     application of the opaque quoting step inside it — the one place a real
#     patch could plausibly drop a normalization and still pass every
#     column-equal test.
#
#     The rival is observably WRONG exactly on the sub-domain where the quoting
#     function is non-injective: two distinct raw names it maps together. The
#     quoting function is `opaque` with no axiom, so that sub-domain cannot be
#     exhibited at a literal — the witness CONDITIONS on it with one equation
#     (`quoteIdentifier "colA" = quoteIdentifier "colB"`), which is the weakest
#     assumption that separates the two and is trivially satisfiable for an
#     opaque function (no tactic can derive `False` from it; the gate's
#     consistency probe was run and does not close). Note this is a claim about
#     the SPEC's frame, not about the real quoting callee, which is injective —
#     the point is that the spec pins the comparison to the quoted forms and an
#     impl that skips the quoting step does not satisfy it.
SPEC_TESTS.append({
    "id": "reject-unquoted-column-compare",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return (old.column != new.column) ||\n"
                    "         decide ((old.path, old.args, oldKwargs) ≠ "
                    "(new.path, new.args, newKwargs))\n"),
    "rationale": "REJECT from clause (1): the spec compares the two columns "
                 "through the backend-quoting function, and this impl compares "
                 "the raw names. At the witness point the descriptions are "
                 "otherwise identical and the two raw column names are distinct "
                 "but quote to the same identifier, so the spec's clause (1) is "
                 "false, its clause (2) is false, and it demands `false` — while "
                 "the impl sees distinct raw names and yields `true`. Binders "
                 "varied: `old.column` / `new.column` at a point where the "
                 "quoting step is what decides, which is the complement of 1f "
                 "(1f varies the columns where the QUOTED forms differ, so it "
                 "cannot see whether the quoting is applied). This is the only "
                 "case that conditions on the quoting function COLLAPSING two "
                 "names rather than separating them.",
    "refinement": "the faithful real patch would compare the column names as "
                  "written on the two fields instead of the identifiers the "
                  "backend actually emits. Wherever the backend's quoting maps "
                  "two spellings of a column onto the same identifier, a change "
                  "between those spellings would be reported as requiring a "
                  "column-level change and a no-op alteration would emit rename "
                  "SQL. Stated plainly, as with 1h: the real quoting callee is "
                  "injective, so no shipped F2P/P2P test distinguishes this "
                  "rival — it is a verify-does-not-imply-resolve break against "
                  "the specified behavior (the spec pins the comparison to the "
                  "quoted forms, and this impl does not compute them) rather "
                  "than a test-visible regression. A reviewer should read this "
                  "case as defending clause (1)'s frame, not a test.",
    "witness": _witness(
        _fd("colA", "CharField", [], []),
        _fd("colB", "CharField", [], []),
        binders=('(hQuote : quoteIdentifier "colA" = '
                 'quoteIdentifier "colB")'),
        extra_simp=("hQuote",)),
})

# --- 1i. Keeps both clauses but COMBINES them wrongly: conjunction instead of
#     disjunction. Attacks the top-level combination rather than either clause.
SPEC_TESTS.append({
    "id": "reject-conjoin-clauses",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _RETURN,
                    "  return (quoteIdentifier old.column != "
                    "quoteIdentifier new.column) &&\n"
                    "         decide ((old.path, old.args, oldKwargs) ≠ "
                    "(new.path, new.args, newKwargs))\n"),
    "rationale": "REJECT from the postcondition's top-level structure: the two "
                 "clauses are combined with OR, and this impl uses AND. Both "
                 "clauses are present and computed exactly as the spec states "
                 "them, so no clause-internal witness would catch it. At the "
                 "witness point the columns agree (clause (1) false) while the "
                 "descriptions differ in BOTH the class path and the positional "
                 "arguments (clause (2) true), so the spec demands `true` and "
                 "the conjunction yields `false`. Binders varied: `old.path` and "
                 "`old.args` TOGETHER, with the column held EQUAL and both "
                 "kwargs lists empty — the combination is only observable where "
                 "the two clauses disagree, which is what this point arranges. "
                 "AUDIT: this case previously shipped a witness BYTE-IDENTICAL "
                 "to 1d's and 1j's, so three cases rested on a single "
                 "refutation. The point is now one no OTHER rival in the battery "
                 "refutes — measured: built against 1d, 1g, 1h, 1j and 1k it "
                 "exits 1 on every one, and 0 only against this rival — so the "
                 "rejection is attributable to the top-level connective in "
                 "particular. It also needs no assumption about the opaque "
                 "stable list: both kwargs lists are empty, so the drop step is "
                 "inert and the witness binds nothing.",
    "refinement": "the faithful real patch would require BOTH a column rename "
                  "and a surviving description difference before altering. A "
                  "change that alters a column-defining attribute without "
                  "renaming the column — the ordinary case for every field "
                  "alteration — would then be reported as a no-op and no SQL "
                  "emitted at all. Essentially every alteration test in the "
                  "PASS_TO_PASS suite fails. Does NOT resolve.",
    "witness": _witness(_fd("name", "CharField", ["10"], []),
                        _fd("name", "TextField", ["20"], [])),
})

# ===========================================================================
# 2. SOUNDNESS POSITIVES — structurally DIFFERENT but CORRECT impls that must
#    VERIFY (a rejection is SPEC-TOO-STRONG). On lean each needs a proof that
#    actually closes for the new impl shape; the `theorem` STATEMENT is
#    byte-identical in every case and no helper lemma, axiom or `sorry` is
#    introduced — the tactic body is genuinely re-closed.
# ===========================================================================

# --- 2a. Ports nagini's `pos-fan-conj` (the cheapest correct reshape). The two
#     accumulator loops are replaced by the direct filtering form: the drop is
#     expressed as one pass keeping the non-ignored entries rather than as an
#     iteration removing one name at a time. Same value on every input. The
#     frozen proof's loop-to-filter bridging induction becomes inapplicable (there
#     is no loop left to bridge), so the tactic body is replaced by the residual
#     head that closes the reshaped goal — no lemma, axiom or `sorry` added.
SPEC_TESTS.append({
    "id": "verify-direct-filter",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _swap(_BASE, _IMPL_BODY,
              "  let oldKwargs := popAttrs old.kwargs\n"
              "  let newKwargs := popAttrs new.kwargs\n" + _RETURN),
        _PROOF_BODY,
        _PROOF_INTRO + _PROOF_UNFOLD + "  simp only [Id.run, pure]"),
    "rationale": "a correct reshape of clause (2)'s drop step: one filtering "
                 "pass retaining the non-ignored keyword arguments, instead of "
                 "an accumulator loop removing one ignored name per iteration. "
                 "Identical value at every input, so it must VERIFY (else the "
                 "postcondition is over-fit to one traversal shape — "
                 "SPEC-TOO-STRONG). The proof is re-closed for the new shape: "
                 "the frozen script's loop-to-filter bridging induction has no "
                 "loop left to bridge, so the body becomes the residual head "
                 "that discharges the reshaped goal. Stated plainly, since this "
                 "is the one positive whose proof gets SHORTER: the obligation "
                 "is not weakened — the `theorem` statement is byte-identical, "
                 "no lemma, axiom, `sorry` or `native_decide` is introduced, and "
                 "the full postcondition is still discharged for all inputs. It "
                 "closes cheaply only because this reshape happens to phrase the "
                 "drop the same way the spec does, which is exactly what makes "
                 "it a test of whether the spec over-fits the loop traversal "
                 "rather than a test of proof difficulty.",
})

# --- 2b. Ports nagini's `pos-sia-reorder` (same content, different order). The
#     two top-level clauses are COMMUTED. Boolean `||` is commutative so the
#     value is unchanged, but the frozen script closes by reflexivity on the
#     clause order, so the proof must be re-closed with the commutativity step.
SPEC_TESTS.append({
    "id": "verify-clauses-commuted",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _swap(_BASE, _RETURN,
              "  return decide ((old.path, old.args, oldKwargs) ≠ "
              "(new.path, new.args, newKwargs)) ||\n"
              "         (quoteIdentifier old.column != "
              "quoteIdentifier new.column)\n"),
        _PROOF_TAIL,
        _PROOF_TAIL + "  exact Bool.or_comm _ _\n"),
    "rationale": "the two postcondition clauses are evaluated in the opposite "
                 "order. Boolean disjunction is commutative, so the result is "
                 "identical on every input and a faithful patch could equally "
                 "take this form; it must VERIFY (else SPEC-TOO-STRONG). This is "
                 "the SOUNDNESS control for rival 1i: the same edit site, but "
                 "reordering rather than replacing the connective, so a battery "
                 "that only reshaped this expression could not claim the "
                 "rejection there came from the spec. The proof is re-closed by "
                 "appealing to commutativity — statement byte-identical, no new "
                 "lemma, axiom or `sorry`.",
})

# --- 2c. The two drop passes are independent (they touch different
#     accumulators), so their order is immaterial. Cheapest possible reshape: the
#     frozen tactic script closes it unchanged, which is the point — it isolates
#     "the impl was reshaped" from "the spec was violated".
SPEC_TESTS.append({
    "id": "verify-drop-order-swapped",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _OLD_DROP + _NEW_DROP, _NEW_DROP + _OLD_DROP),
    "rationale": "the two drop passes are performed in the opposite order. They "
                 "read and write disjoint state, so the result is identical on "
                 "every input; it must VERIFY (else SPEC-TOO-STRONG). Paired "
                 "with rival 1e, which edits the same two passes: this control "
                 "shows the postcondition constrains WHICH descriptions are "
                 "normalized, not the order in which they are.",
})

# --- 2d. ADDED BY AUDIT (attack E). A correct reshape that the previous three
#     positives did not reach: clause (2) compares the two SURVIVING kwargs
#     lists, and this impl compares their REVERSALS. `List.reverse` is
#     injective, so `l.reverse ≠ m.reverse ↔ l ≠ m` and the returned Bool is
#     identical on every input — but the reshape is NOT definitionally equal to
#     the frozen form (the frozen tactic script does not close it; the proof
#     needs the injectivity step, supplied in-body with no new lemma, axiom or
#     `sorry`). It matters because the battery's reject lane contains two rivals
#     that MUTILATE the surviving list (1j drops it, 1k takes its tail), and
#     without a positive that transforms the list reversibly, "the spec pins the
#     surviving kwargs list" could not be distinguished from "the spec pins this
#     one syntactic form of it" — i.e. SPEC-TOO-STRONG in exactly the direction
#     1j/1k's rejections would mask. Measured: verifies (exit 0).
SPEC_TESTS.append({
    "id": "verify-kwargs-reversed-both",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _swap(_BASE, _RETURN,
              "  return (quoteIdentifier old.column != "
              "quoteIdentifier new.column) ||\n"
              "         decide ((old.path, old.args, oldKwargs.reverse) ≠ "
              "(new.path, new.args, newKwargs.reverse))\n"),
        _PROOF_TAIL,
        _PROOF_TAIL + "  simp [Prod.ext_iff, List.reverse_inj]\n"),
    "rationale": "the surviving keyword-argument lists are compared in reversed "
                 "order on BOTH sides. Reversal is injective, so the "
                 "inequality it decides is the same inequality and the result is "
                 "identical at every input; it must VERIFY (else the "
                 "postcondition is over-fit to one syntactic presentation of the "
                 "surviving list — SPEC-TOO-STRONG). This is the SOUNDNESS "
                 "control for rivals 1j and 1k, which both attack the surviving "
                 "list itself (1j discards it, 1k drops its head): those "
                 "rejections attribute to the spec only if a list-transforming "
                 "impl that PRESERVES the comparison is still accepted. Unlike "
                 "2c the frozen tactic script does not close this one — the "
                 "proof is re-closed by the injectivity rewrite — statement "
                 "byte-identical, no lemma, axiom, `sorry` or `native_decide`.",
})

# ===========================================================================
# 3. ADMISSIBILITY — the obligation must be satisfiable on a REAL input, not
#    vacuously. Ports nagini's `admiss-sia` / `admiss-fan` (which asserted the
#    load-bearing fact is genuinely reachable at the F2P-shaped call).
# ===========================================================================

# NOTE on the lane's shape here. `correct_requiresColumnChange` binds
# `∀ (old new : FieldDesc)` with NO precondition hypothesis, so there is no
# precondition that could be PRECOND-TOO-STRONG in the nagini sense. What CAN
# still go wrong is the analogue nagini's admissibility cases were really
# checking: that the discriminating verdict is genuinely produced at the
# F2P-shaped input rather than the postcondition being satisfiable only
# elsewhere. So this case proves, inside the existing proof body, that the
# postcondition HOLDS with `false` at a change touching only the
# permitted-choices keyword argument — the no-op the behavior must admit.
SPEC_TESTS.append({
    "id": "admiss-noop-point-reachable",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _PROOF_INTRO,
        "  -- The discriminating verdict is genuinely reachable: at a change\n"
        "  -- touching only the permitted-choices keyword argument (same column,\n"
        "  -- same class path, same positional arguments) the postcondition is\n"
        "  -- satisfied by `false`, i.e. no column-level change is required.\n"
        "  have admits_noop : problem_spec_requiresColumnChange\n"
        '      { column := "name", path := "CharField", args := ["255"],\n'
        '        kwargs := [("choices", "[]")] }\n'
        '      { column := "name", path := "CharField", args := ["255"],\n'
        '        kwargs := [("choices", "[(Jane,Jane)]")] } false := by\n'
        "    unfold problem_spec_requiresColumnChange popAttrs isIgnored\n"
        "    simp [ignoredAttrs]\n"
        + _PROOF_INTRO),
    "rationale": "proves, inside the obligation's own proof, that the "
                 "postcondition is satisfied by `false` at the F2P-shaped input: "
                 "a change touching only the permitted-choices keyword argument, "
                 "with column, class path and positional arguments held equal. "
                 "That is the no-op the behavior must admit, and it is "
                 "established on a CONCRETE input pair, so the postcondition is "
                 "genuinely satisfiable there rather than only away from the "
                 "discriminating point. If this were REJECTED the spec would be "
                 "unsatisfiable exactly where the fix must land. The full "
                 "obligation is still discharged by the frozen tactic script "
                 "that follows — statement byte-identical, nothing assumed. "
                 "AUDIT: the `have` is load-bearing rather than decorative, and "
                 "this was measured rather than argued — flipping its asserted "
                 "verdict from `false` to `true` (the same input pair, the same "
                 "tactic) makes the variant FAIL to build (exit 1). So the case "
                 "genuinely pins WHICH verdict the postcondition admits at the "
                 "F2P-shaped point, and would catch a spec that was satisfiable "
                 "there only with the opposite answer.",
})
