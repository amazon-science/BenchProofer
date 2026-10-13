"""properties.py — G-PBT falsification battery for django__django-15037 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_relationField``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models an imperative procedure over ``List[int]`` column/table names with
fractional-permission read-only inputs and a mutable ``RelationField`` record,
contracting FIVE load-bearing postcondition clauses plus a frame guarantee. This
Lean bundle models the SAME single purely-functional core — the relation-column
decision producing a ``RelationField`` (kind, target, optional explicit target
column) from the introspected inputs — over ``String`` / ``Option String``
carriers, with the SAME grounding: the postcondition pins ``result`` to a single
computation over the inputs, no opaque answer key for the decision itself. Each
nagini case carries over as an attack on ONE of the three top-level
postcondition clauses, or as a faithful correct positive; the nagini
frame/permission-mutation class is VACUOUS here (referential transparency). The
per-nagini-case disposition is recorded inline, in the ADVERSARIAL READ section
below — this module defines no ``assessment`` symbol and the gate reads none, so
earlier references to one here were describing something that does not exist.

DEFENDED SURFACE (one modeled behavior; three independent top-level clauses).
``problem_spec_relationField isUnique isPrimaryKey refDbColumn refDbTable
tableName refPkColumn result`` pins EXACTLY:

  * (C1 kind)   ``result.relType`` = the one-to-one kind exactly when the column
    is unique or a primary key, otherwise the plain foreign-key kind;
  * (C2 target) ``result.relTo`` = the self-literal when the relation points back
    at the current table, otherwise the model identifier of the referenced table
    (the sole term routed through the ``opaque`` name transform);
  * (C3 column) ``result.toField`` = the referenced column recorded EXACTLY when
    the field is a plain foreign key AND the referenced table has a detected
    primary-key column that DIFFERS from the referenced column; ``none`` in every
    other case.

The BEHAVIOURAL DISCRIMINATOR (the fix): clause C3 is the changed behavior — the
explicit target column must be recorded on the plain-foreign-key branch, and only
when a distinct detected primary-key column exists. The pre-fix behavior never
recorded it at all; the ``never-emit`` rival below IS that pre-fix behavior, and
on the reported F2P case (a foreign key whose referenced table's primary key
differs from the referenced column) it omits the explicit target column, so the
rendered field lacks it and the F2P test fails.

BINDER STRUCTURE. The spec predicate has SIX input binders: ``isUnique``,
``isPrimaryKey`` (the two kind toggles), ``refDbColumn`` (the referenced column),
``refDbTable`` (the referenced table), ``tableName`` (the current table), and
``refPkColumn`` (the detected primary-key column, ``Option``). All are
load-bearing. The reject witnesses vary them rather than fixing them at one
convenient point: ``isUnique`` takes both settings (the wrong-kind rival flips at
``true``, the C3 rivals hold it ``false``); ``isPrimaryKey`` takes both, with a
rival that drops it from the kind disjunction caught at exactly its ``true``
corner; ``refPkColumn`` ranges over ``none``, ``some pk = refDbColumn`` (the
falsy-guard sub-domain) and ``some pk ≠ refDbColumn`` (the emit sub-domain);
``refDbTable`` vs ``tableName`` takes both the self and the non-self case, in BOTH
failure directions (the latter driving the ``opaque`` clause). The TWELVE reject
witnesses probe ELEVEN distinct input TUPLES over TWELVE distinct refutation
POINTS (re-counted mechanically in each audit; the fourth audit added the two
rivals described below): the three conditioned C2
witnesses state their refutation at a point described by hypothesis rather than by
the tuple alone, and two of them (always-self and wrong-transform-argument) share
the tuple ``false false "c" "t" "u" none`` while discriminating at different
hypotheses — measured, they catch disjoint rivals. Each
rests on its OWN wrong implementation — no two reject cases share a rival module,
so every rejection is attributable to a distinct behavioral divergence rather than
to a second view of one.

The kind toggles additionally take their JOINT corner. The two toggles enter C1
through an inclusive disjunction, so three sub-domains matter and not two:
neither set, exactly one set, and BOTH set. The first three audits probed each
toggle singly and left the both-set corner — the ordinary shape for a primary-key
column — unprobed by any of the ten then-shipped witnesses; the fourth audit's
exclusive-or rival closes it. Likewise C3's first conjunct is probed not only for
WHETHER a primary-key column was detected but for what it is NAMED, which the
conventional-name rival closes.

CROSS-DISCRIMINATION (measured, not argued). Every witness was rebuilt against
every rival — the full square, not just the diagonal. Re-measured independently in
the THIRD audit on the then-shipped 10x10 square (90 off-diagonal builds plus the
ten diagonal ones), and re-measured again in the FOURTH: the diagonal is all-hold,
and every rival is caught by its OWN
witness. Off-diagonal holds occur only where one rival's divergence genuinely
subsumes another's at that input (the inverted-kind rival is caught by seven
witnesses, because inverting the kind is wrong at every input any of them names;
the never-emit and wrong-value rivals catch each other, both differing from the
spec-demanded `some <referenced column>` at the same tuple; the over-emit and
no-detected-pk rivals likewise; and the pk-toggle witness also catches the
one-to-one-branch emitter). Critically, SEVEN rivals — the no-detected-pk emitter,
the pk-toggle, always-self, wrong-transform-argument, never-self, and the fourth
audit's two additions — are caught
by their own witness ALONE, so no rival survives only because no witness aims at
it. That last property is what the second and fourth audits each found broken and
repaired: see the never-self rival, which all nine then-shipped witnesses missed,
and the two fourth-audit rivals, which all ten missed. Both fourth-audit rivals
are own-witness-only, and neither of their witnesses catches the other, so the two
are independent probes rather than two views of one divergence.
Each rival was also machine-checked observably DISTINCT from the frozen impl
(`decide` over the battery's own inputs for the seven transparent rivals; a
conditioned disequality for the THREE whose divergence sits behind the ``opaque``
transform — always-self, wrong-transform-argument and never-self), so no case is
vacuous by definitional collapse on this carrier.

Both CONJUNCTS of clause C3 are probed independently: the distinct-primary-key
test (R1-R4, on the plain-foreign-key branch) and the kind-suppression guard
(the one-to-one-branch emitter, which is correct on the whole plain-foreign-key
sub-domain and diverges only where the field is one-to-one and a distinct
primary key exists).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini frame-mutation rival writes
    into the half-permission read-only input list to "produce" the qualifier
    value. Lean is referentially transparent: the inputs are immutable
    ``String`` / ``Option String`` values, there is no ``mut`` input binder, no
    aliasing, and no read-only cell to overwrite. The rival has no expressible
    instance here; no substitute is fabricated (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by a term built only from the inputs (the two kind toggles, the
    three names, the ``Option`` primary key). The nagini @Pure helpers
    (names_equal / qualifier_required) are likewise grounded there, so nagini
    itself has no WRONG echo to build and ships an honest positive control in its
    place (nagini case 2). The one ``opaque`` leaf here — the table-name → model
    identifier transform in C2 — is an UNCHANGED platform callee whose behavior
    the fix never touches (an A-reference validated by G-AX), NOT an oracle for
    the modeled decision; producing each clause from the inputs IS doing the work.
    In its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify (ports nagini's pos-echo-grounded-oracle).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: never emitting the explicit column (the
    pre-patch bug); over-emitting it for every plain foreign key (ignoring the
    primary-key guard); naming the WRONG column value (the table instead of the
    column); emitting it on the no-detected-primary-key sub-domain; emitting it on
    the one-to-one branch (dropping C3's kind-suppression conjunct); inverting the
    relation kind; dropping ONE disjunct of the kind decision (honouring the
    unique constraint, ignoring the primary-key flag); collapsing the target
    to the self-literal on a non-self relation; mis-routing the name transform's
    ARGUMENT; and dropping the self-vs-non-self test in the OTHER direction, so a
    self relation is targeted through the transform instead of the self-literal.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Nine of the twelve diverge on a fully concrete
(transparent) clause and close by ``decide``. The other three attack the C2 target
clause, either of whose branches can be wrong and one of which routes through the
``opaque`` name transform: each witness CONDITIONS on the carrier (a single weak,
satisfiable hypothesis — that the transform's result on the concrete table name is
not the self-literal, or that it separates two distinct concrete table names) and
refutes at that sub-domain. Each was checked with two real ``lake env lean``
builds to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

All three conditioned C2 witnesses carry the extra evidence their shape requires,
since a gold-side error is only admissible if it CHANGES when the claim changes.
Their gold-side failure is an application type mismatch on ``hrel``, so the claim
was flipped (the ``¬`` dropped, asserting the frozen impl IS correct at that
input) and rebuilt on both sides: the flipped claim ELABORATES against the frozen
solution and FAILS against the rival — the exact inverse of the witness. A
type-revealing variant confirms why: on both sides ``hrel`` retains its concrete
equation between the returned target and the spec's target term (it is NOT
reduced to ``True``), so the mismatch is the refutation being carried out, not a
tactic that silently succeeded. Gold's exit code therefore tracks the claim. The
same flip test was run on a ``decide`` witness as a control and behaves the same
way (flipped claim: gold elaborates, rival fails), confirming the transparent
majority is not passing on a claim-independent error either.

DIVERGENCE (F′). This bundle sets no ``loom.semantics.termination``: it is a
plain Lean/Mathlib artifact whose obligation is a total ``theorem`` over a total
``def``, so the analogue of the total setting applies and a non-terminating rival
IS rejected — but not in a way that can be shipped as a witnessed case. Measured:
a self-recursive impl with no decreasing measure fails at ``fail to show
termination``, and a ``partial def`` fails to compile for want of a ``Nonempty``
instance; supplying that instance in-region makes the file elaborate but renders
the impl irreducible, so the witness's ``unfold`` then fails against the RIVAL —
the half that must succeed. The class is therefore rejected by the carrier
without a landable witness, and is recorded here as a carrier-level rejection
rather than as a shipped case or a silent omission.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
either omits, over-emits, or mis-values the explicit target column (or mis-types
the field / mis-targets the relation), so the rendered relational field diverges
from the F2P-expected output and the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares one ``opaque`` callee (the unchanged
table-name → model-identifier transform) validated executably by G-AX (an
A-reference), and consumes no ``axiom``. The axiom lane belongs to G-AX; this
gate ignores it, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-15037"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. The whole gold `implementation_relationField` def body lies
# strictly inside `-- impl-start`/`-- impl-end`; the proof `intro` line lies
# strictly inside `-- proof-start`/`-- proof-end`. Both are unique in the file
# (verified at load by _swap). Every variant edits ONLY these regions, so
# `same_spec` holds and the `theorem correct_relationField` STATEMENT is
# byte-identical.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

_PROOF_INTRO = "  intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn\n"


def _impl(body):
    """Build a full Solution.lean whose impl def body is `body` (proof frozen)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---------------------------------------------------------------------------
# Rival impl bodies. Each is a complete `implementation_relationField` def,
# structurally the frozen shape with ONE behavioral edit.
# ---------------------------------------------------------------------------

# R1 — never emit the explicit target column (the pre-patch behavior).
_R1_NEVER = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R2 — over-emit: record the referenced column for EVERY plain foreign key,
# ignoring whether a distinct detected primary-key column exists.
_R2_OVEREMIT = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    toField := some refDbColumn
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R3 — wrong column VALUE: record the referenced TABLE name instead of the
# referenced column name.
_R3_WRONGCOL = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbTable
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R4 — emit on the no-detected-primary-key sub-domain (the `none` branch must be
# `none`). Correct on `some`; wrong when the referenced table has no detectable
# primary key.
_R4_NONEEMIT = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => toField := some refDbColumn
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R5 — invert the relation kind.
_R5_WRONGKIND = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "OneToOneField"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "ForeignKey"
  else
    relType := "OneToOneField"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R5B — PARTIAL on the kind axis: honour `isUnique` but IGNORE `isPrimaryKey`.
# Correct on every input where `isPrimaryKey` is false (which is where R1-R4 and
# R6 all sit); wrong at EXACTLY the (isUnique=false, isPrimaryKey=true) corner.
# This is a strictly sharper probe of C1's disjunction than the total inversion
# R5: a rival that drops one disjunct survives every other witness in the
# battery, so the `isPrimaryKey` binder needs its own wrong impl and not merely
# its own witness against R5.
_R5B_IGNOREPK = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R7 — drop the KIND SUPPRESSION on clause C3: record the explicit target column
# whenever a distinct detected primary-key column exists, including on the
# one-to-one branch where C3 demands `none` unconditionally. Correct on the whole
# plain-foreign-key sub-domain (where every other C3 rival sits), wrong exactly
# on the one-to-one-with-distinct-pk corner, which no shipped rival reached: R1-R4
# all hold both kind toggles false, so C3's `if isUnique || isPrimaryKey then
# none` guard was never independently probed.
_R7_O2OEMIT = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
  match refPkColumn with
  | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
  | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R10 — AUDIT ADDITION (fourth audit). Read the kind decision as an EXCLUSIVE or:
# one-to-one exactly when precisely ONE of the two toggles is set. Correct at
# every input the rest of the battery names — all ten shipped witnesses hold at
# most ONE toggle true, and on that sub-domain exclusive-or and inclusive-or
# agree — and wrong at exactly the BOTH-true corner. Measured in this audit: all
# ten shipped witnesses were rebuilt against this rival and every one elaborated
# clean (exit 0), i.e. missed it entirely. The corner is not exotic: a column
# that is a primary key is normally also reported unique, so both-true is the
# ORDINARY shape for a primary-key column rather than an edge case, and the
# rival mis-types precisely those columns while also running the
# explicit-column branch on them.
_R10_KINDXOR = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if (isUnique || isPrimaryKey) && !(isUnique && isPrimaryKey) then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R11 — AUDIT ADDITION (fourth audit). Apply C3's distinct-primary-key test but
# ALSO require the detected key to carry the conventional name, so the explicit
# target column is recorded only for a referenced table whose key happens to be
# spelled that way. Correct on every input the battery names whose detected key
# IS spelled conventionally — which is every `some pk` witness in the shipped
# ten — and wrong wherever a referenced table's detected key is distinct from the
# referenced column but named anything else. Measured in this audit: all ten
# shipped witnesses were rebuilt against it and every one elaborated clean
# (exit 0). This is the sub-domain split C3's first conjunct hides: the shipped
# C3 rivals all vary WHETHER a key was detected, never what it is NAMED, so a
# rival keyed on the name survived the whole battery.
_R11_CONVENTIONALPK = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn && pk = "id" then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

# R6 — collapse the target to the self-literal on EVERY relation (ignore the
# self-vs-non-self test). Attacks C2, whose non-self branch is opaque.
_R6_ALWAYSSELF = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String := "self"
  return { relType := relType, relTo := relTo, toField := toField }"""

# R8 — AUDIT ADDITION. Keep the self-vs-non-self TEST intact but hand the name
# transform the WRONG argument: the current table instead of the referenced one.
# C2 has two separable parts — which branch is taken, and what the non-self
# branch is computed FROM — and every shipped rival attacked only the first: R6
# collapses the branch, so its witness (which only needs the rival's answer to be
# the self-literal) does not fire here, and R1-R5/R7 all sit on self relations
# where the transform is never reached. Measured during the audit: all eight
# shipped witnesses build clean against this rival, i.e. miss it entirely. The
# transform's ARGUMENT is load-bearing (it is the sole term routed through the
# opaque name transform, and the referenced table is the only faithful source),
# so it needs its own wrong impl.
_R8_WRONGXFORMARG = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName tableName
  return { relType := relType, relTo := relTo, toField := toField }"""

# R9 — AUDIT ADDITION (second audit). Drop clause C2's branch TEST in the OTHER
# direction: never take the self-literal branch, always route the referenced table
# through the name transform. This is the exact dual of the always-self rival, and
# the battery had no case for it. Measured during this audit: all NINE
# previously-shipped witnesses were rebuilt against this rival and every one
# elaborated clean (exit 0), i.e. missed it entirely — the always-self witness
# cannot fire because it only needs the rival's answer to BE the self-literal, and
# every transparent witness sits on a self relation where this rival's divergence
# is exactly what is not observed by `decide` (the self-literal is what the spec
# demands there, and the rival returns an opaque term instead). So C2's branch test
# was only ever probed in one direction, and the self sub-domain — which is where
# seven of the nine witnesses live — had no rival attacking it at all.
_R9_NEVERSELF = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  let relTo : String := dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""


# ---------------------------------------------------------------------------
# Positive-control impl bodies (must VERIFY with the frozen proof or a
# re-proof inside the proof region).
# ---------------------------------------------------------------------------

# P1 — structure-literal echo of the grounded decision (no `Id.run do`, no
# mutable state). Definitionally the spec's RHS, so a `refine ⟨rfl, rfl, rfl⟩`
# closes; the theorem STATEMENT is byte-identical.
_P1_ECHO = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField :=
  { relType := if isUnique || isPrimaryKey then "OneToOneField" else "ForeignKey",
    relTo := if refDbTable = tableName then "self" else dbTableToModelName refDbTable,
    toField := if isUnique || isPrimaryKey then none
               else match refPkColumn with
                    | some pk => if pk ≠ refDbColumn then some refDbColumn else none
                    | none => none }"""

_P1_PROOFBODY = """  intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
  unfold problem_spec_relationField implementation_relationField
  refine ⟨rfl, rfl, rfl⟩"""

# P2 — branch REORDER: compute the target first, keep the kind/column decision
# in the else-branch, and pin `toField := none` explicitly on the one-to-one
# branch (same values, different control-flow shape). The frozen proof closes it.
_P2_REORDER = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isUnique || isPrimaryKey then
    relType := "OneToOneField"
    toField := none
  else
    match refPkColumn with
    | some pk => if pk ≠ refDbColumn then toField := some refDbColumn
    | none => pure ()
  return { relType := relType, relTo := relTo, toField := toField }"""

# The frozen proof body carried verbatim into the reorder positive (the STATEMENT
# is unchanged; only the tactic body region is re-used, and it still closes).
_FROZEN_PROOFBODY = """  intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
  unfold problem_spec_relationField implementation_relationField
  simp only [Id.run, bind, pure]
  by_cases h : isUnique || isPrimaryKey
  · simp only [h, if_true, and_self]
  · cases refPkColumn with
    | none => simp only [h, Bool.not_eq_true] at *; exact ⟨rfl, rfl, rfl⟩
    | some pk =>
      by_cases hk : pk = refDbColumn
      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_true_eq_false] at *
        exact ⟨rfl, rfl, rfl⟩
      · simp only [h, hk, Bool.not_eq_true, ne_eq, not_false_eq_true] at *
        exact ⟨rfl, rfl, rfl⟩"""


# P3 — AUDIT ADDITION. Each of the three positives needs its OWN proof script and
# none of the three scripts closes either of the others — measured in the fourth
# audit: the frozen script does not close P1 (`unsolved goals`) and does not close
# P3; P1's `rfl`-triple closes neither P2 nor P3. So the earlier claim that P1 and
# P2 are "definitionally equal to the frozen impl at every branch CONDITION" was
# too strong for P1, which needs its own script precisely because the structure
# literal is not the `Id.run do` term. What remains true, and is what makes P3 the
# sharper probe, is that P1's and P2's branch CONDITIONS are the frozen ones
# verbatim, so no reasoning about the tests themselves is required. This reshape
# commutes BOTH decision
# tests — the kind disjunction and the primary-key inequality — which are
# propositionally but NOT definitionally equal to the frozen forms, so `rfl` no
# longer closes either branch condition and the case needs a real re-proof. That
# makes it the sharper SPEC-TOO-STRONG probe: a spec that admitted only the frozen
# spelling of its own tests would reject this faithful impl.
_P3_COMMUTE = """def implementation_relationField
    (isUnique isPrimaryKey : Bool)
    (refDbColumn refDbTable tableName : String)
    (refPkColumn : Option String) : RelationField := Id.run do
  let mut relType : String := "ForeignKey"
  let mut toField : Option String := none
  if isPrimaryKey || isUnique then
    relType := "OneToOneField"
  else
    relType := "ForeignKey"
    match refPkColumn with
    | some pk => if refDbColumn ≠ pk then toField := some refDbColumn
    | none => pure ()
  let relTo : String :=
    if refDbTable = tableName then "self" else dbTableToModelName refDbTable
  return { relType := relType, relTo := relTo, toField := toField }"""

_P3_PROOFBODY = """  intro isUnique isPrimaryKey refDbColumn refDbTable tableName refPkColumn
  unfold problem_spec_relationField implementation_relationField
  simp only [Id.run, bind, pure]
  cases isUnique <;> cases isPrimaryKey <;> cases refPkColumn <;>
    simp_all [ne_comm] <;> split <;> exact ⟨rfl, rfl, rfl⟩"""


def _impl_and_proof(impl_body, proof_body):
    """Swap both the impl def and the proof tactic body (STATEMENT untouched)."""
    src = _swap(_BASE, _GOLD_IMPL, impl_body)
    return _swap(src, _FROZEN_PROOFBODY, proof_body)


# Admissibility: prepend a ground `have` discharging the spec at a concrete
# F2P-shaped input, then run the frozen proof verbatim.
#
# AUDIT REPAIR (fourth audit), two independent defects at once:
#
#  * The input was a SELF relation (refDbTable = tableName = "t"), which is not
#    the shape the fix's own sub-domain has: the reported case is a CROSS-TABLE
#    foreign key, and on a self relation clause C2 takes its self-literal branch
#    and never reaches the name transform at all. So the lane discharged the
#    obligation at an input that exercises two of the three clauses. The
#    replacement is genuinely cross-table, which makes C2's opaque branch part of
#    what is satisfied — closed by `rfl` on that conjunct, `decide` on the two
#    transparent ones, since `decide` cannot reduce an opaque term.
#  * The referenced-column literal was lifted verbatim from the reported test's
#    expected output. Neutral placeholder names carry exactly the same
#    satisfiability content, so nothing is lost by not quoting it.
_ADMISS_INTRO = (
    "  have _ground : problem_spec_relationField false false "
    "\"uniq_col\" \"other_tbl\" \"this_tbl\" (some \"id\")\n"
    "      (implementation_relationField false false "
    "\"uniq_col\" \"other_tbl\" \"this_tbl\" (some \"id\")) := by\n"
    "    unfold problem_spec_relationField implementation_relationField\n"
    "    refine ⟨by decide, by rfl, by decide⟩\n"
    + _PROOF_INTRO
)


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate directly at one concrete input and
# refutes it. Checked (two real builds) to hold of its rival and fail on gold.
# ---------------------------------------------------------------------------

# R1/R2/R3/R4/R5 diverge on a transparent clause -> `decide` after unfolding.
_W_R1 = """example : ¬ problem_spec_relationField false false "c" "t" "t" (some "id")
    (implementation_relationField false false "c" "t" "t" (some "id")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

_W_R2 = """example : ¬ problem_spec_relationField false false "k" "s" "s" (some "k")
    (implementation_relationField false false "k" "s" "s" (some "k")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

_W_R3 = """example : ¬ problem_spec_relationField false false "col" "v" "v" (some "id")
    (implementation_relationField false false "col" "v" "v" (some "id")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

_W_R4 = """example : ¬ problem_spec_relationField false false "d" "r" "r" none
    (implementation_relationField false false "d" "r" "r" none) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

# R5 attacks C1 via the isUnique toggle; R5B attacks C1 via the isPrimaryKey
# toggle. The two kind inputs enter the spec symmetrically
# (`isUnique || isPrimaryKey`), so each disjunct gets its OWN wrong impl: R5
# inverts the whole decision (caught at isUnique=true), R5B honours `isUnique`
# and drops `isPrimaryKey` (caught only at isUnique=false, isPrimaryKey=true).
_W_R5 = """example : ¬ problem_spec_relationField true false "c" "t" "t" none
    (implementation_relationField true false "c" "t" "t" none) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

# AUDIT REPAIR. This witness previously sat at `refPkColumn = none`, where R5B's
# ONLY divergence is the relation kind: with no detected primary key its
# else-branch leaves the explicit column `none`, exactly as the spec demands. The
# case still discriminated (the kind clause alone falsifies), but the rationale's
# second claim — that the rival ALSO attaches a target column it must not have —
# was false at the witness input, verified by evaluation: R5B returns
# `toField := none` there. Moving the witness to `some "id"` (a detected primary
# key distinct from the referenced column) makes BOTH divergences live at the one
# refuted input, so the prose now describes what the build checks.
_W_R5B = """example : ¬ problem_spec_relationField false true "e" "w" "w" (some "id")
    (implementation_relationField false true "e" "w" "w" (some "id")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

# R10 reads the kind decision as an exclusive or, so its witness must sit at the
# BOTH-toggles-true corner — the only place inclusive and exclusive or disagree,
# and the one corner no shipped witness reached (every other witness holds at most
# one toggle true). Fully transparent, so `decide` closes it.
_W_R10 = """example : ¬ problem_spec_relationField true true "c" "t" "t" (some "id")
    (implementation_relationField true true "c" "t" "t" (some "id")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

# R11 keys C3's guard on the detected key's NAME, so its witness must sit at a
# `some pk` whose pk is distinct from the referenced column and spelled
# UNconventionally — the sub-domain the shipped C3 witnesses never enter, since
# every one of them either has no detected key or names it conventionally.
_W_R11 = """example : ¬ problem_spec_relationField false false "c" "t" "t" (some "k")
    (implementation_relationField false false "c" "t" "t" (some "k")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

# R7 attacks C3's kind-suppression guard, so its witness must sit on the
# one-to-one branch (isUnique=true) WITH a distinct detected primary key — the
# only place R7 diverges. Fully transparent, so `decide` closes it.
_W_R7 = """example : ¬ problem_spec_relationField true false "c" "t" "t" (some "id")
    (implementation_relationField true false "c" "t" "t" (some "id")) := by
  unfold problem_spec_relationField implementation_relationField
  decide"""

# R6 attacks the opaque C2 branch. Condition on the carrier: a single weak,
# satisfiable hypothesis that the name transform's result on "t" is not the
# self-literal. The witness holds of the rival (which returns "self") and fails
# on gold (which returns `dbTableToModelName "t"`, not provably "self").
_W_R6 = """example (h : dbTableToModelName "t" ≠ "self") :
    ¬ problem_spec_relationField false false "c" "t" "u" none
    (implementation_relationField false false "c" "t" "u" none) := by
  unfold problem_spec_relationField implementation_relationField
  simp only [Id.run, bind, pure]
  rintro ⟨_, hrel, _⟩
  exact h hrel.symm"""

# R8 attacks the transform's ARGUMENT, so its witness sits on the NON-SELF branch
# (where the transform is reached at all) and conditions on the carrier the same
# way R6's does — a single weak, satisfiable hypothesis, here that the transform
# separates the two distinct concrete table names. The rival computes it from the
# current table, the spec from the referenced table, and by hypothesis those
# differ. Satisfiable for the same reason R6's is: no tactic can derive `False`
# from a disequality between two applications of an opaque function.
_W_R8 = """example (h : dbTableToModelName "t" ≠ dbTableToModelName "u") :
    ¬ problem_spec_relationField false false "c" "t" "u" none
    (implementation_relationField false false "c" "t" "u" none) := by
  unfold problem_spec_relationField implementation_relationField
  simp only [Id.run, bind, pure]
  rintro ⟨_, hrel, _⟩
  exact h hrel.symm"""

# R9 attacks C2's branch test in the never-self direction, so its witness sits on
# a SELF relation (refDbTable = tableName = "t"), where the spec demands the
# self-literal and the rival returns the transform's result instead. Conditioned on
# the carrier the same way R6/R8 are — one weak, satisfiable hypothesis that the
# transform's result on the concrete table name is not the self-literal. Note the
# hypothesis is the SAME shape as R6's but the refutation point is the opposite
# sub-domain (self here, non-self there), which is why the two witnesses catch
# disjoint rivals: measured, R6's witness misses R9 and R9's witness misses R6.
_W_R9 = """example (h : dbTableToModelName "t" ≠ "self") :
    ¬ problem_spec_relationField false false "c" "t" "t" none
    (implementation_relationField false false "c" "t" "t" none) := by
  unfold problem_spec_relationField implementation_relationField
  simp only [Id.run, bind, pure]
  rintro ⟨_, hrel, _⟩
  exact h hrel"""


# === SPEC LANE =============================================================

SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_relationField` STATEMENT byte-identical.
    # =====================================================================
    {
        "id": "pos-echo-grounded-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_and_proof(_P1_ECHO, _P1_PROOFBODY),
        "rationale": (
            "Grounded-decision positive control: a structure-literal impl that "
            "directly echoes the three grounded clauses (no `Id.run do`, no "
            "mutable state) — a faithful, structurally-different correct impl. "
            "Definitionally the spec's RHS, so `refine ⟨rfl, rfl, rfl⟩` closes it "
            "(statement byte-identical, no new axiom/lemma). MUST verify, else "
            "SPEC-TOO-STRONG. Ports nagini's pos-echo-grounded-oracle: the @Pure "
            "helpers there are grounded so there is no WRONG echo — this is the "
            "honest positive control in its place."),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_and_proof(_P2_REORDER, _FROZEN_PROOFBODY),
        "rationale": (
            "Branch-REORDER positive control: the target is computed up front, "
            "the one-to-one branch pins `toField := none` explicitly, and the "
            "column decision stays in the else-branch — identical values, "
            "different control flow. A faithful reshape MUST verify, else "
            "SPEC-TOO-STRONG. The frozen proof body closes it unchanged (statement "
            "byte-identical, no new axiom/lemma). Ports nagini's "
            "pos-reorder-decisions."),
    },
    {
        "id": "pos-commuted-decisions",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_and_proof(_P3_COMMUTE, _P3_PROOFBODY),
        "rationale": (
            "AUDIT ADDITION — the sharper SPEC-TOO-STRONG probe. The other two "
            "positives keep the frozen branch CONDITIONS verbatim, so the carrier "
            "identifies their tests with the frozen ones for free and neither "
            "requires any reasoning about the tests themselves. This reshape "
            "commutes BOTH decision tests — it reads the "
            "kind disjunction in the opposite order and states the primary-key "
            "comparison from the other side — which are propositionally but not "
            "definitionally equal to the frozen forms, so neither branch condition "
            "closes by `rfl` and the case must genuinely re-prove. Both orders are "
            "equally faithful to the modeled behavior, so it MUST verify; a "
            "rejection would mean the spec admits only its own spelling of its own "
            "tests, i.e. SPEC-TOO-STRONG. Statement byte-identical, no new "
            "axiom/lemma; only the impl and proof-tactic regions differ."),
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. Discharge the spec by evaluation at a concrete
    # plain-foreign-key-with-distinct-pk input (the fix's own sub-domain) as a
    # `have`, then close the frozen obligation verbatim. Nothing assumed: no new
    # declaration, statement byte-identical, ground instance prepended to the
    # existing tactic body.
    # =====================================================================
    {
        "id": "admiss-ground-fk",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_INTRO, _ADMISS_INTRO),
        "rationale": (
            "The obligation is discharged at a normal F2P-shaped input (a plain "
            "CROSS-TABLE foreign key whose referenced table has a detected primary "
            "key differing from the referenced column — exactly the sub-domain the "
            "fix adds) as a `have`: the two transparent clauses by evaluation, the "
            "target clause by `rfl` (it reaches the opaque name transform, which "
            "`decide` cannot reduce, so the conjuncts are discharged separately). "
            "Then the frozen obligation is closed "
            "verbatim. Verifies, else the modeled behavior would be unsatisfiable "
            "at a normal F2P input (PRECOND-TOO-STRONG analogue). Ports nagini's "
            "admiss-precond-available; here the precondition is trivial (total "
            "function over the observable inputs) so admissibility is a ground "
            "satisfaction of the spec, kept in-region to preserve same_spec."),
    },

    # =====================================================================
    # UNIQUENESS (reject) — wrong impls the FROZEN spec refutes. Each carries a
    # witness verified to hold of the rival and fail on gold.
    # =====================================================================
    {
        "id": "never-emit-target-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R1_NEVER),
        "witness": _W_R1,
        "rationale": (
            "Rejection from clause C3 (toField): leaving the explicit target "
            "column `none` on the plain-foreign-key branch where a distinct "
            "detected primary key exists falsifies "
            "`result.toField = some refDbColumn`. Witness at (isUnique=false, "
            "isPrimaryKey=false, refDbColumn=\"c\", refPkColumn=some \"id\", "
            "self relation): spec demands `some \"c\"`, rival gives `none`."),
        "refinement": (
            "This is the pre-patch behavior: the plain-foreign-key branch never "
            "records the explicit target column. On the F2P case (a foreign key "
            "whose referenced table's primary key differs from the referenced "
            "column) the rendered field omits the explicit target column, so the "
            "expected exact output is not produced and the F2P test FAILS — the "
            "faithful patch does NOT resolve."),
    },
    {
        "id": "overemit-target-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R2_OVEREMIT),
        "witness": _W_R2,
        "rationale": (
            "Rejection from clause C3: recording the referenced column for EVERY "
            "plain foreign key ignores the distinct-primary-key guard. Witness at "
            "(refDbColumn=\"k\", refPkColumn=some \"k\" = refDbColumn, FK, self "
            "relation \"s\"): the guard makes the spec demand `none`, but the rival "
            "emits `some \"k\"` (both values confirmed by evaluation)."),
        "refinement": (
            "A faithful patch of this shape would record the explicit target "
            "column on every plain foreign key, even when the referenced table's "
            "primary key IS the referenced column (or is absent). The real guard "
            "suppresses it there; emitting it always produces spurious target "
            "keywords on plain foreign keys across the introspection suite, "
            "breaking PASS_TO_PASS tests that render foreign keys without one — so "
            "the faithful patch does NOT resolve."),
    },
    {
        "id": "wrong-target-column-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R3_WRONGCOL),
        "witness": _W_R3,
        "rationale": (
            "Rejection from clause C3: recording the referenced TABLE name in "
            "place of the referenced COLUMN name. Witness at (FK, refPkColumn=some "
            "\"id\" ≠ refDbColumn=\"col\", refDbTable=\"v\", self relation): spec "
            "demands `some \"col\"`, rival gives `some \"v\"` (both values "
            "confirmed by evaluation)."),
        "refinement": (
            "A faithful patch that recorded the referenced table name as the "
            "explicit target column would render the wrong exact target string; "
            "the F2P test asserts the referenced-column string, so it FAILS — the "
            "faithful patch does NOT resolve."),
    },
    {
        "id": "emit-on-no-detected-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R4_NONEEMIT),
        "witness": _W_R4,
        "rationale": (
            "Rejection from clause C3: the no-detected-primary-key sub-domain must "
            "record NO explicit target column. Witness at (FK, refDbColumn=\"d\", "
            "refPkColumn=none, self relation \"r\"): spec demands `none`, rival "
            "emits `some \"d\"` (both values confirmed by evaluation). Varies the "
            "`refPkColumn` binder to the `none` case that R1/R2/R3 (all `some`) "
            "leave untouched."),
        "refinement": (
            "A faithful patch that recorded the explicit target column when the "
            "referenced table has NO detectable primary key (the falsy case) would "
            "emit a spurious target keyword on such foreign keys; the real guard "
            "suppresses it, so the rendered output diverges and the faithful patch "
            "does NOT resolve."),
    },
    {
        "id": "wrong-relation-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R5_WRONGKIND),
        "witness": _W_R5,
        "rationale": (
            "Rejection from clause C1 (relType): inverting the kind. Witness at "
            "(isUnique=true): spec demands the one-to-one kind, rival gives the "
            "plain foreign-key kind. Varies the `isUnique` binder to `true`, the "
            "one-to-one sub-domain the C3 rivals (all `false`) never probe."),
        "refinement": (
            "Inverting the kind renders every unique/primary-key relation as a "
            "plain foreign key and every plain foreign key as one-to-one — every "
            "relational field in the introspection suite gets the wrong field "
            "type, breaking the PASS_TO_PASS field-type tests; not the gold "
            "behavior, so the faithful patch does NOT resolve."),
    },
    {
        "id": "wrong-relation-kind-pk-toggle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R5B_IGNOREPK),
        "witness": _W_R5B,
        "rationale": (
            "Rejection from clause C1 via the OTHER kind toggle. The spec's kind "
            "decision is the disjunction `isUnique || isPrimaryKey`, so a rival "
            "may honour one disjunct and drop the other: this one reads `isUnique` "
            "and ignores `isPrimaryKey` entirely. It is therefore CORRECT on every "
            "input the rest of the battery uses (all of which hold isPrimaryKey "
            "false) and wrong at exactly one corner. Witness at (isUnique=false, "
            "isPrimaryKey=true): spec demands the one-to-one kind, rival gives the "
            "plain foreign-key kind — and, because the rival also runs the "
            "explicit-column branch there, a distinct target column it must not "
            "have. A DISTINCT wrong impl rather than a second witness against the "
            "inverted-kind rival, so that dropping a single disjunct is what the "
            "case actually detects."),
        "refinement": (
            "A faithful patch that consulted only the unique constraint and never "
            "the primary-key flag would render a primary-key relation as a plain "
            "foreign key (and attach a spurious explicit target column to it), so "
            "the introspected field type is wrong for exactly those columns, "
            "breaking the PASS_TO_PASS field-type tests — the faithful patch does "
            "NOT resolve."),
    },
    {
        "id": "emit-on-one-to-one-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R7_O2OEMIT),
        "witness": _W_R7,
        "rationale": (
            "Rejection from clause C3's KIND-SUPPRESSION guard, which the other C3 "
            "rivals never reach. C3 is a conjunction of two conditions — plain "
            "foreign key AND a distinct detected primary key — and R1-R4 all hold "
            "both kind toggles false, so they only ever probe the second "
            "conjunct. This rival lifts the explicit-column decision out of the "
            "else-branch: it applies the primary-key test on BOTH kind branches, so "
            "it is correct on the entire plain-foreign-key sub-domain and wrong "
            "only where the field is one-to-one and a distinct primary key exists. "
            "Witness at (isUnique=true, refPkColumn=some \"id\" ≠ "
            "refDbColumn=\"c\"): spec demands `none` unconditionally on the "
            "one-to-one branch, rival emits `some \"c\"`."),
        "refinement": (
            "A faithful patch that ran the referenced-table primary-key lookup "
            "outside the plain-foreign-key branch would attach an explicit target "
            "column to unique and primary-key relations as well. Those are "
            "rendered without one, so every such column in the introspection suite "
            "gains a spurious target keyword, breaking the PASS_TO_PASS field "
            "tests while still producing the F2P-expected plain-foreign-key "
            "output — a verify-but-not-resolve break. The faithful patch does NOT "
            "resolve."),
    },
    {
        "id": "wrong-relation-kind-both-toggles",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R10_KINDXOR),
        "witness": _W_R10,
        "rationale": (
            "AUDIT ADDITION (fourth audit) — rejection from clause C1 at the one "
            "corner of the kind decision the battery never reached. C1 reads the "
            "INCLUSIVE disjunction `isUnique || isPrimaryKey`; this rival reads it "
            "as an EXCLUSIVE or, so it agrees with the spec wherever at most one "
            "toggle is set and diverges only where BOTH are. Every one of the ten "
            "previously-shipped witnesses holds at most one toggle true, so all ten "
            "were rebuilt against this rival during the audit and every one "
            "elaborated clean, i.e. missed it: the inverted-kind and pk-toggle "
            "rivals probe each disjunct singly, and neither pins what the "
            "disjunction does when the two agree. Witness at (isUnique=true, "
            "isPrimaryKey=true, refPkColumn=some \"id\" ≠ refDbColumn=\"c\"): the "
            "spec demands the one-to-one kind and no explicit target column, the "
            "rival gives the plain foreign-key kind and `some \"c\"`."),
        "refinement": (
            "The both-set corner is the ordinary shape for a primary-key column, "
            "not an edge case: a column reported as a primary key is normally also "
            "reported unique, so a faithful patch reading the kind test as an "
            "exclusive or would render exactly the primary-key columns as plain "
            "foreign keys — and, because it then also runs the explicit-column "
            "branch on them, attach a spurious explicit target column to each. "
            "Every primary-key relation in the introspection suite gets both the "
            "wrong field type and an extra keyword, breaking the PASS_TO_PASS "
            "field-type tests while the F2P plain-foreign-key case (one toggle "
            "unset) still renders correctly — a verify-but-not-resolve break. The "
            "faithful patch does NOT resolve."),
    },
    {
        "id": "conventional-pk-name-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R11_CONVENTIONALPK),
        "witness": _W_R11,
        "rationale": (
            "AUDIT ADDITION (fourth audit) — rejection from clause C3 across a "
            "sub-domain split the shipped C3 rivals never make. C3's first "
            "conjunct asks only WHETHER the referenced table has a detected "
            "primary-key column distinct from the referenced column; it says "
            "nothing about what that column is NAMED. Every shipped C3 witness "
            "either has no detected key or names it conventionally, so a rival that "
            "additionally requires the conventional spelling is correct at all ten "
            "shipped refutation points: all ten witnesses were rebuilt against it "
            "during the audit and every one elaborated clean. Witness at (FK, "
            "refDbColumn=\"c\", refPkColumn=some \"k\" — distinct from the "
            "referenced column but not the conventional name): the spec demands "
            "`some \"c\"`, the rival gives `none`."),
        "refinement": (
            "A faithful patch that consulted the detected key's name as well as "
            "its identity would record the explicit target column only for "
            "referenced tables whose key happens to carry the conventional name, "
            "and silently omit it for every other table — the same omission as the "
            "pre-fix behavior, restricted to a sub-domain. Introspected tables "
            "whose primary key is named anything else render without the explicit "
            "target column, so those relations diverge from expected output and the "
            "faithful patch does NOT resolve on them."),
    },
    {
        "id": "always-self-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R6_ALWAYSSELF),
        "witness": _W_R6,
        "rationale": (
            "Rejection from clause C2 (relTo): collapsing the target to the "
            "self-literal on EVERY relation ignores the self-vs-non-self test. C2's "
            "non-self branch routes through the opaque name transform, so the "
            "witness CONDITIONS on the carrier — a single weak, satisfiable "
            "hypothesis that the transform's result on the concrete table name is "
            "not the self-literal — and refutes at (refDbTable=\"t\" ≠ "
            "tableName=\"u\"): the rival returns the self-literal, the spec demands "
            "the transform's result, which by hypothesis differs. Varies the "
            "refDbTable-vs-tableName binder pair to the non-self case R1-R5 (all "
            "self) leave untouched."),
        "refinement": (
            "A faithful patch that emitted the self-literal for a relation "
            "pointing at a DIFFERENT table would render the wrong target model "
            "identifier for every cross-table relation, so the introspected "
            "output diverges from expected and the faithful patch does NOT "
            "resolve."),
    },
    {
        "id": "wrong-transform-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R8_WRONGXFORMARG),
        "witness": _W_R8,
        "rationale": (
            "AUDIT ADDITION — rejection from the OTHER half of clause C2. C2 is "
            "separable into which branch is taken (self-literal vs transform) and "
            "what the transform is applied TO; the always-self rival attacks only "
            "the first, and every other rival sits on a self relation where the "
            "transform is never reached. This rival keeps the self test exactly "
            "right and mis-routes only the argument, computing the target "
            "identifier from the CURRENT table instead of the referenced one. All "
            "eight previously-shipped witnesses were rebuilt against it during the "
            "audit and every one of them elaborated clean, i.e. missed it. Witness "
            "at (refDbTable=\"t\" ≠ tableName=\"u\", FK, no detected primary key), "
            "conditioned on the transform separating the two names: the spec "
            "demands the transform of the referenced table, the rival gives the "
            "transform of the current table, which by hypothesis differs."),
        "refinement": (
            "A faithful patch that built the target identifier from the table "
            "being introspected rather than the referenced table would point every "
            "cross-table relation at the WRONG model — each such relation would "
            "resolve to the current model, turning genuine cross-table references "
            "into self-references under a different spelling. The rendered target "
            "is wrong for every cross-table relation in the introspection suite, "
            "breaking the PASS_TO_PASS relation tests, so the faithful patch does "
            "NOT resolve."),
    },
    {
        "id": "never-self-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_R9_NEVERSELF),
        "witness": _W_R9,
        "rationale": (
            "AUDIT ADDITION (second audit) — rejection from clause C2's branch "
            "TEST in the direction the battery never attacked. C2 has two failure "
            "directions: emitting the self-literal where the transform is demanded "
            "(the always-self rival) and routing through the transform where the "
            "self-literal is demanded — this rival. It drops the self-vs-non-self "
            "test entirely in the second direction, always computing the target "
            "from the name transform. All NINE previously-shipped witnesses were "
            "rebuilt against it during this audit and every one of them elaborated "
            "clean, i.e. missed it: the always-self witness only needs the rival's "
            "answer to BE the self-literal, and the seven transparent witnesses sit "
            "on self relations where this rival substitutes an opaque term for the "
            "self-literal that `decide` cannot refute without a hypothesis. So the "
            "self sub-domain — where most of the battery lives — had no rival "
            "attacking its target clause at all. Witness at (refDbTable=\"t\" = "
            "tableName=\"t\", FK, no detected primary key), conditioned on the "
            "transform's result on that name not being the self-literal: the spec "
            "demands the self-literal, the rival gives the transform's result, "
            "which by hypothesis differs."),
        "refinement": (
            "A faithful patch that dropped the self-relation test would render a "
            "self-referential relation as pointing at a separately-named model "
            "identifier rather than at the self-literal. Self-referential relations "
            "are rendered with the self-literal target, so every such column in the "
            "introspection suite would get the wrong target, breaking the "
            "PASS_TO_PASS self-relation tests while still producing the "
            "F2P-expected output on the cross-table foreign key the fix concerns — "
            "a verify-but-not-resolve break. The faithful patch does NOT resolve."),
    },
]


# === AXIOM LANE ============================================================
# EMPTY. The bundle declares one `opaque` callee (the unchanged table-name →
# model-identifier transform) validated executably by G-AX as an A-reference and
# consumes no `axiom`. The axiom lane belongs to G-AX; the nagini AXIOM_TESTS
# (also empty there) are dropped.
AXIOM_TESTS = []
