"""properties.py — G-PBT falsification battery for django__django-16595 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC_TESTS case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_reduceAlter`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

---------------------------------------------------------------------------
DEFENDED SURFACE
---------------------------------------------------------------------------
ONE obligation: ``correct_reduceAlter``, over ``problem_spec_reduceAlter (self
op : Op) (result : List Op)``. It relates the outcome of pairing an
alter-a-single-field step ``self`` with the step ``op`` that immediately follows
it, and it is a conjunction of THREE independent top-level clauses:

  (C1) ``op`` alters or removes the SAME field  ->  ``result = [op]``
  (C2) ``op`` renames the same field AND ``self`` pins no explicit database
       column name  ->  ``result = [op, <freshly built alter step>]``, where the
       built step carries ``self``'s model name and field definition VERBATIM,
       names the field by ``op``'s NEW name, and is NOT marked elidable
       (the frame half of the clause: every carried-over component pinned)
  (C3) neither of the above  ->  the generic elidable pairing rule, itself three
       sub-arms: ``self`` elidable -> ``[op]``; ``self`` not but ``op``
       elidable -> ``[self]``; neither elidable -> ``[]``

The carrier is transparent: ``OpKind`` is a four-way ``DecidableEq`` tag,
``elidable`` is ``Bool``, ``dbColumn`` is ``Option String``, and the same-field
test is a spelled-out case-insensitive comparison of the model and field names.
Nothing is ``opaque`` and the bundle declares no axiom (meta.json ``axioms ==
[]``, ``deep_model_references == []``), so there is no answer key an
implementation could echo — the postcondition is grounded in ``self`` and ``op``
throughout.

---------------------------------------------------------------------------
ADVERSARIAL READ of each nagini weakness class on THIS carrier
---------------------------------------------------------------------------
  * FRAME / PERMISSION MUTATION — SPLITS IN TWO on this carrier, and the two
    halves get different dispositions. The nagini sibling's two mandatory cases
    overwrite an input field held at a read-only half-permission and are
    rejected for insufficient permission. Lean is referentially transparent, so
    there is no permission to violate — but the OBSERVABLE half of each write
    survives as a local rebinding that shadows an input with a doctored copy,
    which is expressible and is attacked here:

      - the write to the FOLLOWING step's kind has an expressible analogue and
        it lands: ``weak-shadow-op-kind`` rebinds ``op`` to a copy whose kind is
        forced to alter-field and then runs the frozen body verbatim, so the
        collapse arm is claimed by rewriting the input rather than by reading
        it. Refuted at a following RENAME of the same field, where the forced
        tag steals the input from C2's arm.
      - the write to the ALTER step's own kind ALSO has an expressible analogue
        and it also lands: ``weak-shadow-self-kind`` rebinds ``self`` to a copy
        whose kind is forced to the catch-all tag and then runs the frozen body
        verbatim. A previous revision of this manifest recorded this half as
        "genuinely vacuous, because the reduction never READS ``self.kind``
        (zero occurrences in the impl region)" — that reasoning is WRONG and was
        measured wrong under audit. Not reading a component is not the same as
        not carrying it: C3's second sub-arm returns ``[self]``, which carries
        the receiver WHOLESALE into the result, so a doctored kind is observable
        in the OUTPUT at exactly that arm even though no guard ever inspects it.
        Two measurements settle it: ``example : implementation_reduceAlter =
        <shadowed variant> := rfl`` FAILS (the two are not definitionally equal),
        and the rival's witness elaborates against the rival while failing on
        the frozen solution by kernel evaluation. So BOTH halves of the nagini
        sibling's frame-write pair have a live analogue here and both are
        shipped; neither is a carrier collapse.

    What the frame obligation additionally becomes on this backend is a STATED
    property: C2 pins every component of the constructed step to the value it
    must carry over. All SIX components of that record are attacked, one rival
    per component, each corrupting exactly one while leaving the rest of the
    reduction intact (``weak-carry-op-field``, ``weak-carry-old-name``,
    ``weak-carry-elidable``, ``weak-carry-op-model``, ``weak-carry-newname``,
    ``weak-carry-op-kind``) — the referentially transparent analogue of the
    permission lane, and the strictly stronger check, since a wrong carried
    value is a real behavioral defect rather than a proof-side permission error.

    C3's second sub-arm is the OTHER place a whole input is carried into the
    result (``result = [self]``), and it is pinned the same way by
    ``weak-shadow-self-kind``.

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE on this carrier, and measured
    rather than asserted. This bundle sets no ``loom.semantics.termination``
    option at all: ``implementation_reduceAlter`` is a plain total Lean ``def``,
    so Lean's own totality checker is the termination discipline and a
    self-recursive body with no decreasing measure is simply not accepted. The
    one way to write a diverging rival is to mark it ``partial``, and that was
    built under audit. The result: the rival IS rejected by the spec (the module
    fails to elaborate), so there is NO spec hole here — but no witness can
    refute it either, because ``partial`` compiles the definition through an
    opaque escape and the term is irreducible, so ``unfold`` cannot reach the
    body (measured: ``Tactic `unfold` failed to unfold
    `implementation_reduceAlter```) and ``partial`` is a banned witness token in
    any case. So the reject lane has nothing to ship: the class is closed by the
    carrier's totality checker rather than by a case. (This is the lean
    disposition specifically. It is NOT the velvet one, where a partial-semantics
    bundle admits such a rival vacuously — see the corpus-wide termination-semantics finding. The
    nagini sibling carries no divergence case either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason it is vacuous in the
    nagini sibling: the same-field test is spelled out rather than axiomatized,
    so the cheapest way to satisfy a collapse clause is to actually return the
    following step. In its place the battery carries honest positive controls.

  * PARTIAL-DOMAIN / uniqueness — the main lane, and the one the nagini sibling
    spends five cases on. Every clause carries at least one rival that is
    correct on the rest of the domain and wrong on a sub-domain of that clause.

  * CONTROL-FLOW / VALUE-DOUBLE-MASK — APPLIES. C2's result has a fixed length
    of 2, so a rival can hit the length and still be wrong in the element
    (``weak-rename-carry-is-op`` returns the following step twice).

  * AXIOM lane — DROPPED. That is G-AX's job and this gate ignores AXIOM_TESTS;
    the nagini sibling's ``AXIOM_TESTS`` is empty for the same reason (nothing
    axiomatized).

---------------------------------------------------------------------------
WITNESSES
---------------------------------------------------------------------------
On a tactic-proof backend "did not verify" is the DEFAULT outcome of reshaping an
implementation — the frozen script is tuned to the frozen form — so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet proving the rival CONTRADICTS the spec, and each was built
BOTH ways by hand before shipping: it holds of its rival and FAILS on the frozen
solution.

Eighteen of the nineteen are stated at concrete literals. They are not
``decide``-able as written, because the model/field name comparison goes through
a case-folding map that the kernel will not reduce (``String.mapAux`` is
``@[irreducible]``, so ``decide`` gets stuck on the ``Decidable`` instance and
``rfl`` reports the two sides are not definitionally equal). Two tactics get past
that without assuming anything:

  * names that are LITERALLY equal — ``simp`` closes the comparison reflexively
    without ever computing the fold;
  * names that must compare UNEQUAL — the refutation goes through a length
    argument (the fold preserves length, so two names of different lengths cannot
    fold to the same string), which is why the differing-name witnesses use names
    of differing length.

The nineteenth (``weak-carry-op-model``) cannot be stated at literals at all: it
needs two model names that differ but fold to the same string, and no such pair
is provably equal on this carrier (the fold does not reduce in either direction).
That witness therefore CONDITIONS on the carrier — it quantifies over two names
and assumes only that they fold alike and are distinct. Both assumptions are
jointly satisfiable (any two spellings differing in letter case), so the point it
refutes at is a real one; the gate's own consistency probe was run against it by
hand and correctly failed to derive ``False``. Because that is the ONE witness
whose gold-side failure is not a plain kernel evaluation (it is ``unsolved
goals`` with ``⊢ m2 = m1`` left over), a later audit put it through the
type-revealing forgery experiment rather than judging the error by eye: replacing
the final step with a deliberate type ascription on the introduced hypothesis
prints that hypothesis's REAL type on each side, and the two differ in exactly
the component under attack — the carried ``modelName`` reads ``m1`` (the alter
step's own, i.e. what the clause demands) against the frozen solution and ``m2``
(the following step's) against the rival. So the residual goal is the genuine
refutation ``m2 = m1``, not a tactic artifact, and gold's exit code tracks the
claim rather than the shape of the proof. That the conditioning is FORCED
rather than a convenience was re-measured under audit: ``String.toLower "Book" =
String.toLower "bOOK"`` fails under ``decide``, under ``simp [String.toLower]``,
and under ``simp`` with the fold's whole unfolding chain in the simp set
(``String.map``/``String.mapAux``/``Char.toLower``/``Char.isUpper``) — three
builds, all exit 1. It closes only under ``native_decide``, which is banned in a
witness (it would trust the compiler and hold of gold too), so no literal pair is
available and the hypothesis form is the only way to reach the sub-domain.

BINDER / CLAUSE COVERAGE. The spec has two input binders, ``self`` and ``op``,
and both move across the reject witnesses — the rivals are refuted at all four
kinds of following step, at both settings of each step's elidable flag, at both
halves of the explicit-column domain, at same-field AND at differing-model AND at
differing-field name pairs, and with the two steps' field definitions
distinguishable so a swapped carry is observable. No probed point is shared by
two rivals that do not fail there for the same reason: each of the six
``weak-carry-*`` rivals agrees with the spec everywhere except its own
component, so each is refuted at its own point rather than at a shared one, and
the three elidable rivals are refuted at the three distinct flag settings that
separate C3's sub-arms. All three top-level clauses are attacked (C1 by three
rivals, C2 by ten, C3 by five).

C2's constructed step is pinned SIX ways and all six are attacked, one rival per
component: kind (``weak-carry-op-kind``), model name (``weak-carry-op-model``),
field name (``weak-carry-old-name``), new-name slot (``weak-carry-newname``),
elidable flag (``weak-carry-elidable``), and field definition
(``weak-carry-op-field``). The last two of those six were added by audit; before
that the frame was pinned five ways and probed four, so a patch that fabricated
the new-name slot or emitted the wrong step kind would have gone unattacked.

WHAT THE AUDIT PROBED AND DID NOT FIND. Five further wrong implementations were
built against the frozen spec and every one was REJECTED, so none is a spec hole:
the constructed step's new-name slot fabricated, its kind copied from the
following step, the input rebound to a doctored copy (all three kept, above), a
CASE-SENSITIVE same-field test substituted for the case-folding one (rejected;
refuted by a conditioned witness at two names that fold alike and differ, the
same technique ``weak-carry-op-model`` uses), and the degenerate
never-reconcile implementation that always yields the empty result (rejected;
refuted at the F2P shape, and already dominated by ``weak-collapse-removal-only``
so not shipped). Two CORRECT reshapes were also built and both VERIFY once the
tactic script is retuned to their shape — the guard's two conjuncts commuted, and
the same-field test inlined (the latter shipped as ``pos-inline-samefield``) — so
the spec is not too strong on the guard's form either.

A SECOND, independent audit pass re-derived every one of the above from its own
builds rather than from this prose, and reached the same disposition on every
shipped case with one exception, now fixed: the write to the alter step's OWN
kind, recorded above as vacuous, is expressible and ships as
``weak-shadow-self-kind`` (its case comment carries the two measurements that
overturn the vacuity claim). That pass also built SIX further wrong
implementations and every one was REJECTED, so none is a spec hole: C2's two
result elements emitted in the OPPOSITE ORDER (the list order is pinned, not
merely the multiset); C1's arm returning the alter step instead of the following
step; C2's guard with the same-field test deleted, so any following rename
floats; C3's first sub-arm returning the alter step instead of the following
step; a case-SENSITIVE same-field test at both guards; and the constructed step
named by the alter step's own field name rather than the rename's new name. It
built THREE further correct reshapes and all three VERIFY, so the spec is not too
strong on those forms either: C1's kind test written as a ``match`` rather than a
disjunction of tag comparisons (script retuned), C2's guard conjuncts reordered
to test the column pin first (script retuned), and the constructed step built by
POSITIONAL constructor application instead of by named fields (frozen script
unchanged — so C2's frame pin is stated over the record's VALUE and does not
accidentally demand one syntactic spelling of it).
"""
from pathlib import Path

INSTANCE = "django__django-16595"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. `_IMPL` is the FULL body of the impl region and `_PROOF_HEAD`
# the opening of the proof region's tactic body, so every replacement below
# lands entirely inside the region it means to edit. Both are asserted unique at
# load time, so this manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL = """  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
    return [op]
  if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
    return [op,
      { kind := OpKind.alterField,
        modelName := self.modelName,
        name := op.newName,
        newName := "",
        elidable := false,
        field := self.field }]
  if self.elidable then
    return [op]
  if op.elidable then
    return [self]
  return []
"""

# The two guards and the constructed step, named so each rival can say exactly
# which sub-expression it corrupts.
_G_COLLAPSE = ("  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField)"
               " && sameField self op then\n")
_G_RENAME = ("  if op.kind == OpKind.renameField && sameField self op"
             " && self.field.dbColumn.isNone then\n")
_CARRY = """    return [op,
      { kind := OpKind.alterField,
        modelName := self.modelName,
        name := op.newName,
        newName := "",
        elidable := false,
        field := self.field }]
"""
_ELIDE = """  if self.elidable then
    return [op]
  if op.elidable then
    return [self]
  return []
"""

_PROOF_HEAD = """  intro self op
  unfold problem_spec_reduceAlter implementation_reduceAlter
  simp only [Id.run]
"""

for _a in (_IMPL, _G_COLLAPSE, _G_RENAME, _CARRY, _ELIDE, _PROOF_HEAD):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift: {_a!r}")


def _impl(new_body):
    """Variant with the impl region's body replaced wholesale."""
    return _swap(_BASE, _IMPL, new_body)


# The inlined form of the same-field test, spelled out exactly as `sameField`'s
# own body. Used by `pos-inline-samefield`, whose whole point is that this is
# the same boolean while NOT being the same proof problem.
_SF_INLINE = ("(self.modelName.toLower == op.modelName.toLower\n"
              "      && self.name.toLower == op.name.toLower)")

# The frozen script's two fall-through `have`s, stated over the NAMED helper.
_HAVE1 = """    have hne1 : ((op.kind == OpKind.alterField || op.kind == OpKind.removeField)
        && sameField self op) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at hc
      exact h1 ⟨hc.1, hc.2⟩"""
_HAVE2 = """    have hne2 : (op.kind == OpKind.renameField && sameField self op
        && self.field.dbColumn.isNone) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, beq_iff_eq,
        Option.isNone_iff_eq_none] at hc
      exact h2 ⟨hc.1.1, hc.1.2, hc.2⟩"""

for _a in (_HAVE1, _HAVE2, "  simp only [Id.run]\n"):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift: {_a!r}")


def _inline_samefield_case():
    """`pos-inline-samefield`'s module: guards inlined, obligation re-proved.

    Kept as a function because it edits four separate anchors — the two guards
    in the impl region and the two fall-through `have`s plus the head `simp
    only` in the proof region — and each is asserted unique, so drift in the
    frozen solution breaks this loudly rather than silently mis-targeting.
    """
    src = _impl(
        _IMPL.replace(_G_COLLAPSE,
                      "  if (op.kind == OpKind.alterField"
                      " || op.kind == OpKind.removeField) && "
                      + _SF_INLINE + " then\n")
             .replace(_G_RENAME,
                      "  if op.kind == OpKind.renameField && " + _SF_INLINE
                      + " && self.field.dbColumn.isNone then\n"))
    # The head `simp only` gains the helper's unfolding, so the whole goal is
    # stated over the inlined comparison the new guards use.
    src = _swap(src, "  simp only [Id.run]\n", "  simp only [Id.run, sameField]\n")
    # Each fall-through `have` is restated over the inlined form, then bridged
    # back to the clause hypothesis (which still names the helper) by unfolding
    # the helper THERE. The case fold is never computed either way.
    src = _swap(src, _HAVE1, """    have hne1 : ((op.kind == OpKind.alterField || op.kind == OpKind.removeField)
        && (self.modelName.toLower == op.modelName.toLower
            && self.name.toLower == op.name.toLower)) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at hc
      refine h1 ⟨hc.1, ?_⟩
      simp only [sameField, Bool.and_eq_true, beq_iff_eq]
      exact hc.2""")
    return _swap(src, _HAVE2, """    have hne2 : (op.kind == OpKind.renameField
        && (self.modelName.toLower == op.modelName.toLower
            && self.name.toLower == op.name.toLower)
        && self.field.dbColumn.isNone) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, beq_iff_eq,
        Option.isNone_iff_eq_none] at hc
      refine h2 ⟨hc.1.1, ?_, hc.2⟩
      simp only [sameField, Bool.and_eq_true, beq_iff_eq]
      exact hc.1.2""")


# ===========================================================================
# Shared witness fragments.
# ===========================================================================
# The tail every literal-input witness ends with. `simp` discharges the
# same-field comparison reflexively (the case-folding map never has to reduce)
# and normalizes the `Id` monad away; `all_goals decide` finishes whatever
# transparent residue is left, and closes nothing when there is none.
_T = ("  unfold problem_spec_reduceAlter implementation_reduceAlter\n"
      "  simp [sameField, Id.run]\n"
      "  all_goals decide\n")
# Same, for the clauses whose result is a two-element list: the monadic residue
# there needs `pure` in the simp set as well.
_TP = ("  unfold problem_spec_reduceAlter implementation_reduceAlter\n"
       "  simp [sameField, Id.run, pure]\n"
       "  all_goals decide\n")


def _op(kind, model, name, new_name='""', elidable="false",
        db="none", repr_='"f"'):
    return ('{ kind := OpKind.%s, modelName := "%s", name := "%s",\n'
            '  newName := %s, elidable := %s,\n'
            '  field := { dbColumn := %s, repr := %s } }'
            % (kind, model, name, new_name, elidable, db, repr_))


def _ind(text, n):
    return ("\n" + " " * n).join(text.split("\n"))


def _wit(self_op, op_op, tail):
    """`¬ problem_spec_reduceAlter <self> <op> (implementation_... <self> <op>)`."""
    return ("example : ¬ problem_spec_reduceAlter\n"
            f"    {_ind(self_op, 4)}\n    {_ind(op_op, 4)}\n"
            "    (implementation_reduceAlter\n"
            f"      {_ind(self_op, 6)}\n      {_ind(op_op, 6)}) := by\n" + tail)


def _tail_differing_names(self_op, op_op, which):
    """Tail for a witness whose two steps name DIFFERENT model/field names.

    The comparison folds letter case, and the kernel will not reduce that fold,
    so the two names cannot simply be computed apart. Instead: the fold
    preserves LENGTH, so two names of different lengths cannot fold to the same
    string. `which` selects the component that differs ("model" or "name").
    """
    side = "left" if which == "model" else "right"
    return ("  have hsf : sameField\n"
            f"      {_ind(self_op, 6)}\n      {_ind(op_op, 6)} = false := by\n"
            "    simp only [sameField, Bool.and_eq_false_iff, beq_eq_false_iff_ne, ne_eq]\n"
            f"    {side}\n"
            "    intro h\n"
            "    have hlen := congrArg String.length h\n"
            "    simp only [String.toLower, String.length_map] at hlen\n"
            "    exact absurd hlen (by decide)\n"
            "  unfold problem_spec_reduceAlter implementation_reduceAlter\n"
            "  simp [hsf, Id.run]\n"
            "  all_goals decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical; none adds a declaration, an
    # assumption token, or a helper lemma.
    # =====================================================================
    {
        "id": "pos-hoist-samefield",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape: bind the same-field test once and reuse it in
        # both guards. The test is a pure function of the two inputs, so its
        # value is stable and every arm fires on exactly the same inputs as
        # before. Frozen tactic body retained (the `let` zeta-reduces).
        "module": _impl(
            _IMPL.replace(
                _G_COLLAPSE,
                "  let same := sameField self op\n"
                "  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField)"
                " && same then\n")
                 .replace(
                _G_RENAME,
                "  if op.kind == OpKind.renameField && same"
                " && self.field.dbColumn.isNone then\n")),
        # AUDIT NOTE: measured DEFINITIONALLY EQUAL to the frozen implementation
        # — `example : implementation_reduceAlter = <this variant> := rfl`
        # elaborates (exit 0), because the `let` zeta-reduces to the same term.
        # So this case confirms the region surgery is well-formed and the frozen
        # script still applies, but it exercises no re-proof. Kept (it is the
        # direct port of the nagini sibling's `pos-hoist` and costs one build),
        # with `pos-inline-samefield` added as the positive that is NOT defeq and
        # so actually tests SPEC-TOO-STRONG.
        "rationale": "hoisting the same-field test into a local bound once and "
                     "reused across both guards is a pure variable reshape: the "
                     "test is a function of `self` and `op` only, so each arm "
                     "fires on exactly the inputs it fired on before and the "
                     "result is identical on every input. All three clauses "
                     "(C1/C2/C3) must therefore still discharge; if they cannot, "
                     "the obligation is SPEC-TOO-STRONG. This is the direct port "
                     "of the nagini sibling's `pos-hoist`. Proof: frozen tactic "
                     "body retained — the `let` zeta-reduces, so the script sees "
                     "the same term.",
    },
    {
        "id": "pos-explicit-column-test",
        "kind": "soundness",
        "expect": "verify",
        # Spell the "no explicit database column name is pinned" test as a
        # direct comparison against the absent marker instead of the
        # is-absent predicate. Same boolean on every input.
        "module": _impl(_IMPL.replace("self.field.dbColumn.isNone",
                                      "self.field.dbColumn == none")),
        "rationale": "writing the explicit-column test as a comparison against "
                     "the absent marker rather than as the is-absent predicate "
                     "yields the same boolean at every input, so C2 fires on "
                     "exactly the same sub-domain and the result is unchanged. A "
                     "correct reshape of the guard must verify (else "
                     "SPEC-TOO-STRONG on C2's guard). Proof: frozen tactic body "
                     "retained.",
    },
    {
        "id": "pos-reorder-rename-first",
        "kind": "soundness",
        "expect": "verify",
        # Branch reorder — the port of the nagini sibling's `pos-reorder`. A
        # step's kind is a single four-way tag, so the rename arm and the
        # alter/remove arm are mutually exclusive and testing rename FIRST
        # cannot change which arm fires for any input. The frozen script is
        # tuned to the frozen branch order, so the obligation is re-proved for
        # the new shape: same statement, and the new script needs only that the
        # kind tags are distinct (one extra `have`, discharged by `simp` on the
        # hypothesis already in scope). No new declaration, no assumption.
        "module": _swap(
            _impl("  if op.kind == OpKind.renameField && sameField self op"
                  " && self.field.dbColumn.isNone then\n"
                  + _CARRY + _G_COLLAPSE + "    return [op]\n" + _ELIDE),
            """  · rintro ⟨hk, hs⟩
    have hb : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = true := by
      rcases hk with h | h <;> simp [h]
    simp [hb, hs]
    rfl
  · rintro ⟨hk, hs, hc⟩
    have h1 : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = false := by
      simp [hk]
    have h2 : (op.kind == OpKind.renameField) = true := by simp [hk]
    have h3 : self.field.dbColumn.isNone = true := by simp [hc]
    simp [h1, h2, h3, hs]
    rfl
""",
            """  · rintro ⟨hk, hs⟩
    have h2 : (op.kind == OpKind.renameField) = false := by
      rcases hk with h | h <;> simp [h]
    have hb : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = true := by
      rcases hk with h | h <;> simp [h]
    simp [h2, hb, hs]
    rfl
  · rintro ⟨hk, hs, hc⟩
    have h2 : (op.kind == OpKind.renameField) = true := by simp [hk]
    have h3 : self.field.dbColumn.isNone = true := by simp [hc]
    simp [h2, h3, hs]
    rfl
"""),
        "rationale": "the following step's kind is a single four-way tag, so the "
                     "rename arm and the alter-or-remove arm are mutually "
                     "exclusive: testing rename first cannot change which arm "
                     "fires for any input, and the result is identical to the "
                     "frozen one everywhere. All three clauses must still "
                     "discharge (else SPEC-TOO-STRONG). This is the port of the "
                     "nagini sibling's `pos-reorder`. Re-proved because the "
                     "frozen script is tuned to the frozen branch ORDER: the new "
                     "shape needs the kind tags' distinctness, supplied by "
                     "`simp` on the clause hypothesis already in scope. Theorem "
                     "statement byte-identical; no new declaration, lemma, or "
                     "assumption token.",
    },
    {
        "id": "pos-inline-samefield",
        "kind": "soundness",
        "expect": "verify",
        # The load-bearing positive of the battery. `pos-hoist-samefield` and
        # `pos-elidable-nested` were measured DEFINITIONALLY EQUAL to the frozen
        # implementation (`example : implementation_reduceAlter = <variant> :=
        # rfl` elaborates, exit 0), so the frozen tactic script closes them
        # because the elaborated term is literally the same one — they confirm
        # the surgery is well-formed but exercise no re-proof. This case is a
        # reshape that is NOT definitionally equal: the same-field test is
        # INLINED at both guards, so the guards are stated over
        # `String.toLower`-equality directly rather than through the named
        # helper. The frozen script's two fall-through `have`s name the helper
        # and no longer typecheck against the new guards, so the obligation is
        # genuinely REPROVED for the new shape (the fold is never computed —
        # `sameField` is unfolded in the head `simp only`, and the two `have`s
        # are restated over the inlined form and bridged back by unfolding the
        # helper on the clause hypothesis).
        "module": _inline_samefield_case(),
        "rationale": "inlining the same-field test at both guards spells out the "
                     "case-insensitive model+field comparison in place instead of "
                     "calling the named helper. The helper is a plain `def` with "
                     "exactly that body, so the guard's boolean is unchanged at "
                     "every input and all three clauses must still discharge "
                     "(else SPEC-TOO-STRONG). Unlike the other positives this "
                     "one is NOT definitionally equal to the frozen "
                     "implementation as a proof problem: the frozen script's two "
                     "fall-through `have`s are stated over the named helper and "
                     "no longer typecheck against the inlined guards, so the "
                     "obligation is reproved — the head `simp only` gains the "
                     "helper's unfolding and each `have` is restated over the "
                     "inlined form and bridged back to the clause hypothesis by "
                     "unfolding the helper there. Theorem statement "
                     "byte-identical; no new declaration, lemma, or assumption "
                     "token, and the case fold is never computed.",
    },
    {
        "id": "pos-elidable-nested",
        "kind": "soundness",
        "expect": "verify",
        # Rewrite the generic elidable pairing rule's three exits as a nested
        # if/else-if/else chain instead of a sequence of early returns. The arms
        # are tested in the same order and produce the same values, so C3's
        # three sub-arms are unaffected.
        "module": _impl(_IMPL.replace(_ELIDE, """  if self.elidable then
    return [op]
  else if op.elidable then
    return [self]
  else
    return []
""")),
        # AUDIT NOTE: also measured DEFINITIONALLY EQUAL to the frozen
        # implementation (`... := rfl` elaborates, exit 0) — the early-return
        # sequence and the nested if/else-if/else elaborate to the same nested
        # `ite`, as the rationale below already says. Same disposition as
        # `pos-hoist-samefield`: honest and cheap, but not a re-proof.
        "rationale": "recasting the generic elidable pairing rule's three exits "
                     "as a nested if/else-if/else chain rather than a sequence "
                     "of early returns tests the same conditions in the same "
                     "order and returns the same value from each, so all three "
                     "of C3's sub-arms are unchanged and C1/C2 are untouched. A "
                     "correct reshape must verify. Proof: frozen tactic body "
                     "retained (the two shapes elaborate to the same nested "
                     "`ite`).",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, F2P-shaped
    # input rather than only provable in the abstract. The frozen theorem
    # carries NO precondition hypothesis (the modeled behavior is total, so the
    # `∀` is unguarded), which means the nagini sibling's precondition-admission
    # probe has no binder to attack here. The honest analogue: discharge the
    # spec predicate at a ground instance of exactly the pairing the F2P
    # exercises — two same-field alter steps — inside the proof region,
    # alongside the frozen obligation, which is then closed verbatim.
    # =====================================================================
    {
        "id": "admiss-ground-same-field-pair",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_HEAD,
            """  have _ground : problem_spec_reduceAlter
      { kind := OpKind.alterField, modelName := "Book", name := "title",
        newName := "", elidable := false,
        field := { dbColumn := none, repr := "f1" } }
      { kind := OpKind.alterField, modelName := "Book", name := "title",
        newName := "", elidable := false,
        field := { dbColumn := none, repr := "f2" } }
      (implementation_reduceAlter
        { kind := OpKind.alterField, modelName := "Book", name := "title",
          newName := "", elidable := false,
          field := { dbColumn := none, repr := "f1" } }
        { kind := OpKind.alterField, modelName := "Book", name := "title",
          newName := "", elidable := false,
          field := { dbColumn := none, repr := "f2" } }) := by
    unfold problem_spec_reduceAlter implementation_reduceAlter
    simp [sameField, Id.run, pure]
""" + _PROOF_HEAD),
        "rationale": "the obligation is discharged at a GROUND instance of the "
                     "pairing the sole F2P exercises — one model, one field, two "
                     "successive alter steps carrying different field "
                     "definitions, neither marked elidable and neither pinning "
                     "an explicit column — and then the frozen obligation is "
                     "closed verbatim. Verifies unless the spec is unsatisfiable "
                     "at exactly the normal input the fix is about, which is the "
                     "analogue of the nagini sibling's PRECOND-TOO-STRONG probe "
                     "(`admiss-f2p-shaped-input`) on a backend whose obligation "
                     "carries no precondition binder to admit. Nothing is "
                     "assumed: the ground instance is a `have` inside the "
                     "existing tactic body, the theorem statement is "
                     "byte-identical, and no declaration is added.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each shares the frozen spec and MUST
    # be rejected; a verifying rival is a real verify-does-not-imply-resolve
    # break. Every case carries (a) the refinement argument that its faithful
    # real patch would NOT resolve, and (b) a refutation witness, built both
    # ways by hand.
    #
    # ---- C1: the alter-or-remove collapse ----
    # =====================================================================
    {
        "id": "weak-collapse-removal-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Narrow C1's guard so the collapse fires only when the
        # following step REMOVES the field, never when it alters it again. This
        # is the pre-patch behavior the bundle's Solution_prepatch.lean carries.
        "module": _impl(_IMPL.replace(
            _G_COLLAPSE,
            "  if op.kind == OpKind.removeField && sameField self op then\n")),
        "refinement": "this is precisely the pre-existing behavior: a step that "
                      "alters one field of one model is reconciled against a "
                      "following REMOVAL of that field but not against a "
                      "following further ALTERATION of it, so a run of "
                      "successive alterations of one field is left unfused. The "
                      "sole F2P pairs two successive alterations of the same "
                      "field and asserts the pair reduces to just the second; "
                      "this behavior leaves both, so it fails. Its faithful real "
                      "patch — the un-widened guard — is exactly the code that "
                      "does NOT resolve, which is what makes this the "
                      "load-bearing rival of the battery.",
        "rationale": "REJECT from C1: with the following step altering the same "
                      "field, C1 requires `result = [op]`, and this rival falls "
                      "past every arm to the generic rule, which for two "
                      "non-elidable steps yields `[]`. Refuted at the F2P shape "
                      "itself (one model, one field, two successive alterations, "
                      "neither elidable, no explicit column pinned) — the point "
                      "at which the whole instance turns.",
        "witness": _wit(_op("alterField", "Book", "title"),
                        _op("alterField", "Book", "title", repr_='"g"'), _T),
    },
    {
        "id": "weak-collapse-alteration-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual partial-domain miss: widen C1's guard to the alteration case
        # but DROP the removal case it already covered.
        "module": _impl(_IMPL.replace(
            _G_COLLAPSE,
            "  if op.kind == OpKind.alterField && sameField self op then\n")),
        "refinement": "covering the following-alteration case while dropping the "
                      "already-working following-removal case corresponds to a "
                      "patch that REPLACED the guard's step-kind test rather "
                      "than widening it. A removal of a field absorbs an earlier "
                      "alteration of that field — pre-existing, separately "
                      "asserted behavior — and this rival stops fusing that "
                      "pair, so the absorption regresses. It would NOT resolve: "
                      "it trades the F2P for a P2P regression.",
        "rationale": "REJECT from C1: with the following step REMOVING the same "
                     "field, C1 requires `result = [op]`, and this rival falls "
                     "past every arm to `[]`. Refuted with an explicit database "
                     "column name PINNED on the alter step, so the probed point "
                     "sits on the far half of the explicit-column domain from "
                     "the rest of the C1 rivals — the column pin is irrelevant "
                     "to C1 and this rival is wrong there too, so moving it "
                     "costs nothing and the battery stops probing one column "
                     "setting only.",
        "witness": _wit(_op("alterField", "Shop", "price",
                            db='some "price_col"'),
                        _op("removeField", "Shop", "price", repr_='"g"'), _T),
    },
    {
        "id": "weak-collapse-any-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the same-field guard from C1's arm: collapse an alteration
        # against ANY following alteration or removal, including one acting on
        # a different field or a different model.
        "module": _impl(_IMPL.replace(
            _G_COLLAPSE,
            "  if op.kind == OpKind.alterField || op.kind == OpKind.removeField then\n")),
        "refinement": "dropping the same-field guard would fuse an alteration of "
                      "one field with an unrelated alteration or removal of a "
                      "DIFFERENT field, destroying an independent operation and "
                      "silently discarding the earlier alteration. Sequences "
                      "that interleave operations on distinct fields are "
                      "asserted NOT to be merged, so this collapses pairs that "
                      "must survive: it would NOT resolve.",
        "rationale": "REJECT from C3: when the two steps do NOT act on the same "
                     "field, neither C1 nor C2 applies, so C3 governs — and with "
                     "neither step elidable it requires `result = []`. This rival "
                     "returns `[op]`. Refuted at a DIFFERENT field name on the "
                     "same model, which is the sub-domain the guard it deletes "
                     "exists to protect.",
        "witness": _wit(
            _op("alterField", "Book", "title"),
            _op("removeField", "Book", "isbn", repr_='"g"'),
            _tail_differing_names(_op("alterField", "Book", "title"),
                                  _op("removeField", "Book", "isbn",
                                      repr_='"g"'),
                                  "name")),
    },

    # ---- C2: the rename carry-across, and its frame half ----
    {
        "id": "weak-drop-rename-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # Delete C2's arm entirely: a following rename of the same field is no
        # longer floated to the front and the alteration is not re-expressed.
        "module": _impl(_IMPL.replace(_G_RENAME + _CARRY, "")),
        "refinement": "deleting the rename reconciliation corresponds to a patch "
                      "that removed the whole branch handling a following rename "
                      "of the same field. Floating the rename to the front and "
                      "re-expressing the alteration against the field's new name "
                      "is pre-existing, separately asserted behavior; without it "
                      "the pair is left unfused and the swap of a field's name "
                      "no longer optimizes. It would NOT resolve.",
        "rationale": "REJECT from C2: with the following step renaming the same "
                     "field and no explicit column pinned, C2 requires the "
                     "two-element `[op, <re-expressed alter step>]`, and this "
                     "rival falls through to the generic rule, which for two "
                     "non-elidable steps yields `[]`.",
        "witness": _wit(_op("alterField", "Author", "name"),
                        _op("renameField", "Author", "name",
                            new_name='"fullName"', repr_='"g"'), _T),
    },
    {
        "id": "weak-rename-singleton",
        "kind": "uniqueness",
        "expect": "reject",
        # C2's arm returns only the rename, dropping the re-expressed
        # alteration: right branch, wrong length.
        "module": _impl(_IMPL.replace(_CARRY, "    return [op]\n")),
        "refinement": "returning only the rename and dropping the re-expressed "
                      "alteration loses the field's alteration outright: the "
                      "renamed field would keep whatever definition it had "
                      "before. The two-element outcome of this reconciliation is "
                      "asserted directly, so the vanished alteration is "
                      "observable and it would NOT resolve.",
        "rationale": "REJECT from C2: the clause pins a two-element result and "
                     "this rival produces one element. Refuted with the alter "
                     "step marked ELIDABLE — C2 takes precedence over the "
                     "generic elidable rule, so the flag is irrelevant to this "
                     "clause and the rival is wrong there too; probing it there "
                     "moves the elidable binder off the value every other C2 "
                     "rival holds it at, so a rival that mishandled only that "
                     "interaction could not hide.",
        "witness": _wit(_op("alterField", "Store", "label", elidable="true"),
                        _op("renameField", "Store", "label",
                            new_name='"caption"', repr_='"g"'), _TP),
    },
    {
        "id": "weak-rename-carry-is-op",
        "kind": "uniqueness",
        "expect": "reject",
        # Control-flow / value-double-mask: return the following step TWICE.
        # Correct length, wrong second element.
        "module": _impl(_IMPL.replace(_CARRY, "    return [op, op]\n")),
        "refinement": "returning the rename twice instead of the rename followed "
                      "by a re-expressed alteration is a double-mask cheat: the "
                      "outcome has the right length and the right first element, "
                      "so a check that only counted the replacement steps would "
                      "pass, while the field's alteration has been replaced by a "
                      "duplicate rename. The reconciliation's second element is "
                      "asserted to reproduce the alteration under the new name, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from C2: the clause pins the second element to a "
                     "freshly constructed alter step, and this rival puts the "
                     "following step there — a different kind, a different name, "
                     "a different field definition. Length alone is masked; the "
                     "element-wise pin catches it. Refuted with the FOLLOWING "
                     "step marked elidable (again irrelevant to C2), so the "
                     "second binder's flag moves too rather than both flags "
                     "sitting at their default across the C2 lane.",
        "witness": _wit(_op("alterField", "Blog", "slug"),
                        _op("renameField", "Blog", "slug",
                            new_name='"handle"', elidable="true",
                            repr_='"g"'), _TP),
    },
    {
        "id": "weak-rename-ignores-column-pin",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop C2's explicit-column condition: float the rename even when the
        # alter step pins an explicit database column name.
        "module": _impl(_IMPL.replace(
            _G_RENAME,
            "  if op.kind == OpKind.renameField && sameField self op then\n")),
        "refinement": "floating the rename even when the altered field pins an "
                      "explicit database column name re-expresses the "
                      "alteration against the field's new name while the "
                      "underlying column is fixed by that pin — the two names "
                      "then disagree and the reconciliation is unsound. The "
                      "condition exists precisely to keep the fusion off that "
                      "sub-domain, so removing it would NOT resolve.",
        "rationale": "REJECT from C3: with an explicit column pinned, C2's guard "
                     "is false, so C3 governs — and with neither step elidable it "
                     "requires `result = []`. This rival returns the two-element "
                     "reconciliation. The probed point is the pinned-column half "
                     "of the domain, which no other rename rival occupies.",
        "witness": _wit(_op("alterField", "Page", "headline",
                            db='some "headline_db"'),
                        _op("renameField", "Page", "headline",
                            new_name='"caption"', repr_='"g"'), _T),
    },
    {
        "id": "weak-carry-op-field",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME half of C2: the re-expressed step must carry the ALTER step's
        # field definition verbatim. This rival copies the following step's.
        "module": _impl(_IMPL.replace("        field := self.field }]",
                                      "        field := op.field }]")),
        "refinement": "the whole point of the reconciliation is that the "
                      "alteration survives under the field's new name, which "
                      "means the re-expressed step must carry the ALTER step's "
                      "field definition. Carrying the following step's instead "
                      "silently discards the alteration and substitutes whatever "
                      "definition the rename happens to hold, so the optimized "
                      "sequence no longer applies the change the original "
                      "sequence applied. It would NOT resolve.",
        "rationale": "REJECT from C2's frame half: the clause pins the carried "
                     "field definition to `self.field`, and this rival supplies "
                     "`op.field`. Refuted at a point where the two steps' field "
                     "definitions are DISTINGUISHABLE — otherwise the swap is "
                     "invisible and the rival would agree with the spec, which "
                     "is exactly the masked-binder trap. This rival agrees with "
                     "the spec on every other carried component, so it gets its "
                     "own probe point rather than sharing one.",
        "witness": _wit(_op("alterField", "Novel", "summary",
                            repr_='"selfField"'),
                        _op("renameField", "Novel", "summary",
                            new_name='"blurb"', repr_='"opField"'), _TP),
    },
    {
        "id": "weak-carry-old-name",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME half of C2: the re-expressed step must name the field by the
        # following step's NEW name. This rival keeps the old name.
        "module": _impl(_IMPL.replace("        name := op.newName,",
                                      "        name := op.name,")),
        "refinement": "naming the re-expressed step by the field's OLD name "
                      "leaves it pointing at a field that the rename — now "
                      "floated ahead of it — has already renamed away, so the "
                      "optimized sequence alters a name that no longer exists. "
                      "The re-expression against the new name is the substance "
                      "of this reconciliation, so it would NOT resolve.",
        "rationale": "REJECT from C2's frame half: the clause pins the carried "
                     "step's field name to `op.newName`, and this rival supplies "
                     "`op.name`. Refuted at a point where the old and new names "
                     "differ (they must, for a rename to be observable); this "
                     "rival agrees with the spec on every other carried "
                     "component, so its probe point is its own.",
        "witness": _wit(_op("alterField", "Track", "title"),
                        _op("renameField", "Track", "title",
                            new_name='"caption"', repr_='"g"'), _TP),
    },
    {
        "id": "weak-carry-elidable",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME half of C2: the re-expressed step is freshly constructed and so
        # NOT marked elidable. This rival marks it elidable.
        "module": _impl(_IMPL.replace("""        newName := "",
        elidable := false,""", """        newName := "",
        elidable := true,""")),
        "refinement": "marking the re-expressed step elidable makes it "
                      "droppable when the sequence is squashed, so the "
                      "alteration this reconciliation exists to preserve can be "
                      "discarded by a later squash — the change is lost one step "
                      "further downstream instead of immediately. A freshly "
                      "constructed step is not elidable by default, and nothing "
                      "in this pairing makes it so, so a patch that set the flag "
                      "would NOT resolve.",
        "rationale": "REJECT from C2's frame half: the clause pins the carried "
                     "step's elidable flag to `false`, and this rival sets it "
                     "`true`. This is the only rival that touches the carried "
                     "flag, so it is refuted at its own point; it agrees with "
                     "the spec on every other component of the constructed step.",
        "witness": _wit(_op("alterField", "Venue", "city"),
                        _op("renameField", "Venue", "city",
                            new_name='"town"', repr_='"g"'), _TP),
    },
    {
        "id": "weak-carry-op-model",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME half of C2: the re-expressed step must carry the ALTER step's
        # model name verbatim. This rival copies the following step's. The two
        # are compared case-insensitively, so the swap is invisible at any pair
        # of names that are literally equal — the refutation has to be stated at
        # a pair that differs only in letter case, which no literal can express
        # provably on this carrier. So this witness CONDITIONS: it quantifies
        # over two model names and assumes only that they fold alike (so the
        # steps do act on the same field, and C2 fires) and that they are
        # distinct (so the swap is observable). Both hold of any two spellings
        # differing in case, so the point is real, not a contradiction.
        "module": _impl(_IMPL.replace("        modelName := self.modelName,",
                                      "        modelName := op.modelName,")),
        "refinement": "the model name is compared case-insensitively, so two "
                      "steps whose model names differ only in spelling do act on "
                      "the same field and are reconciled — and the re-expressed "
                      "step must then carry the ALTER step's spelling, not the "
                      "following step's, because that is the value the rest of "
                      "the sequence already refers to. Substituting the "
                      "following step's spelling silently re-targets the "
                      "alteration and makes the optimized sequence disagree with "
                      "the original on which model it names. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C2's frame half: the clause pins the carried "
                     "step's model name to `self.modelName`, and this rival "
                     "supplies `op.modelName`. Stated by CONDITIONING on the "
                     "carrier rather than at literals: the case-folding "
                     "comparison does not reduce in the kernel, so no literal "
                     "pair of case-differing names is provably fold-equal. The "
                     "witness instead quantifies over two names and assumes only "
                     "(i) they fold alike — which is what makes C2 fire at all — "
                     "and (ii) they are distinct — which is what makes the "
                     "substitution observable. The two assumptions are jointly "
                     "satisfiable by any two spellings differing in letter case, "
                     "so the refuted point exists; they are assumptions about "
                     "DIFFERENT relations between the two names, not two claims "
                     "about one term. This is the only rival that moves the model "
                     "name binder off a literal, and the only one whose "
                     "divergence is confined to the case-folding sub-domain.",
        "witness": (
            "example (m1 m2 : String) (hlow : m1.toLower = m2.toLower)\n"
            "    (hne : m1 ≠ m2) :\n"
            "    ¬ problem_spec_reduceAlter\n"
            "    { kind := OpKind.alterField, modelName := m1, name := \"body\",\n"
            "      newName := \"\", elidable := false,\n"
            "      field := { dbColumn := none, repr := \"f\" } }\n"
            "    { kind := OpKind.renameField, modelName := m2, name := \"body\",\n"
            "      newName := \"content\", elidable := false,\n"
            "      field := { dbColumn := none, repr := \"g\" } }\n"
            "    (implementation_reduceAlter\n"
            "      { kind := OpKind.alterField, modelName := m1, name := \"body\",\n"
            "        newName := \"\", elidable := false,\n"
            "        field := { dbColumn := none, repr := \"f\" } }\n"
            "      { kind := OpKind.renameField, modelName := m2, name := \"body\",\n"
            "        newName := \"content\", elidable := false,\n"
            "        field := { dbColumn := none, repr := \"g\" } }) := by\n"
            "  unfold problem_spec_reduceAlter implementation_reduceAlter\n"
            "  simp [sameField, Id.run, pure, hlow]\n"
            "  intro h\n"
            "  have h2 : m2 = m1 := by\n"
            "    injection h with _ h3\n"
            "    injection h3 with h4\n"
            "    injection h4\n"
            "  exact hne h2.symm\n"),
    },

    {
        "id": "weak-carry-newname",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME half of C2, ADDED BY AUDIT: the constructed step's own new-name
        # slot must be empty — it is an alter step, which introduces no new name.
        # This rival fills it with the rename's new name. Sixth of the six
        # components of the constructed record; it was the one component no rival
        # touched, so C2's frame was pinned only five ways out of six.
        "module": _impl(_IMPL.replace("""        newName := "",
""", "        newName := op.newName,\n")),
        "refinement": "the new-name slot is meaningful only on a rename; on the "
                      "freshly constructed alter step it carries no information "
                      "and the reconciliation leaves it empty. Filling it with "
                      "the rename's new name fabricates a component the original "
                      "sequence never set, so the optimized sequence carries a "
                      "step that is not equal to the one the reconciliation is "
                      "specified to produce — two alter steps that should "
                      "compare equal no longer do, and a later pairing that "
                      "tests them for equality takes a different arm. It would "
                      "NOT resolve.",
        "rationale": "REJECT from C2's frame half: the clause pins the "
                     "constructed step's new-name slot to the empty string, and "
                     "this rival supplies `op.newName`. Refuted at a rename "
                     "whose new name is NON-empty (it must be, or the corruption "
                     "is invisible — the masked-binder trap). This rival agrees "
                     "with the spec on every other component, so its probe point "
                     "is its own.",
        "witness": _wit(_op("alterField", "Novel", "summary"),
                        _op("renameField", "Novel", "summary",
                            new_name='"blurb"', repr_='"g"'), _TP),
    },
    {
        "id": "weak-carry-op-kind",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME half of C2, ADDED BY AUDIT: the constructed step must BE an
        # alter step. This rival copies the following step's kind, so the
        # "re-expressed alteration" is actually a second rename.
        "module": _impl(_IMPL.replace("      { kind := OpKind.alterField,\n",
                                      "      { kind := op.kind,\n")),
        "refinement": "the step this reconciliation constructs exists to re-apply "
                      "the ALTERATION under the field's new name, so its kind is "
                      "what makes it an alteration at all. Copying the following "
                      "step's kind emits a second rename instead: the field is "
                      "renamed twice and never altered, so the change the "
                      "original sequence applied is lost outright and the "
                      "sequence also renames a field that no longer exists under "
                      "the old name. It would NOT resolve.",
        "rationale": "REJECT from C2's frame half: the clause pins the "
                     "constructed step's kind to the alter-field tag, and this "
                     "rival supplies `op.kind`, which on this arm is the rename "
                     "tag — a different one of the four, so the corruption is "
                     "observable at any input reaching C2. This rival agrees "
                     "with the spec on every other component of the constructed "
                     "step.",
        "witness": _wit(_op("alterField", "Novel", "summary"),
                        _op("renameField", "Novel", "summary",
                            new_name='"blurb"', repr_='"g"'), _TP),
    },
    {
        "id": "weak-shadow-op-kind",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME/PERMISSION lane, ADDED BY AUDIT: the expressible analogue of the
        # nagini sibling's mandatory `frame-write-nxt-kind`. Lean has no heap to
        # violate, but the OBSERVABLE half of that write does survive: rebind
        # `op` to a doctored copy whose kind is forced to alter-field, then run
        # the frozen body verbatim. The reduction then claims the collapse arm by
        # REWRITING its input rather than by reading it — exactly the cheat the
        # nagini case is rejected for, expressed as shadowing instead of
        # mutation. (The mirror write, to the alter step's OWN kind, is ALSO
        # expressible and ships as `weak-shadow-self-kind` below.)
        "module": _impl("  let op := { op with kind := OpKind.alterField }\n"
                        + _IMPL),
        "refinement": "forcing the following step's kind to alter-field before "
                      "testing it makes the collapse arm fire for EVERY "
                      "same-field pairing regardless of what the following step "
                      "actually is — a rename of the field, or an unrelated kind "
                      "of step, is silently treated as an alteration and "
                      "discarded along with the alteration it followed. Both the "
                      "rename reconciliation and the whole fall-through become "
                      "unreachable on the same-field domain. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C2: at a following RENAME of the same field "
                     "with no explicit column pinned, C2 requires the "
                     "two-element `[op, <re-expressed alter step>]`. This rival "
                     "sees a doctored copy tagged alter-field, takes the collapse "
                     "arm, and returns the one-element `[op]` — and note the "
                     "element it returns is the ORIGINAL following step, since "
                     "the shadowing is local to the guard, so the corruption is "
                     "in the arm taken rather than in the value carried. Probed "
                     "at the rename arm because that is where the forced tag "
                     "STEALS an input from another clause; the collapse arm's own "
                     "domain is where the cheat is invisible.",
        "witness": _wit(_op("alterField", "Book", "title"),
                        _op("renameField", "Book", "title",
                            new_name='"caption"', repr_='"g"'), _TP),
    },
    {
        "id": "weak-shadow-self-kind",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME/PERMISSION lane, ADDED BY AUDIT: the second, MIRROR analogue of
        # the nagini sibling's mandatory frame-write pair — the write to the
        # ALTER step's OWN kind. A previous revision of this manifest recorded
        # this case as inexpressible ("the reduction never reads `self.kind`, so
        # any rebinding is unobservable"), and that reason does not hold. Not
        # READING a component is not the same as not CARRYING it: C3's second
        # sub-arm returns `[self]`, which carries the receiver wholesale into the
        # result, so a doctored kind is observable in the OUTPUT at that arm even
        # though no guard inspects it. Measured under audit: the shadowed variant
        # is NOT definitionally equal to the frozen implementation (`example :
        # implementation_reduceAlter = <variant> := rfl` fails), and the witness
        # below elaborates against the rival while failing on the frozen solution
        # by kernel evaluation.
        "module": _impl("  let self := { self with kind := OpKind.otherOp }\n"
                        + _IMPL),
        "refinement": "rebinding the alter step's own kind to the catch-all tag "
                      "before the body runs corrupts the step the reduction "
                      "hands BACK: on the sub-domain where the pair is not "
                      "reconcilable and the following step is droppable, the "
                      "outcome is supposed to be the alter step itself, and this "
                      "rival emits a copy whose kind has been overwritten. The "
                      "optimized sequence then carries a step of the wrong kind "
                      "where the original carried the alteration, so the "
                      "alteration is silently converted into an unrelated kind of "
                      "step and is never applied. A patch that rewrote the "
                      "receiver's own class tag would NOT resolve: it scrambles "
                      "the operation the optimizer still holds.",
        "rationale": "REJECT from C3's second sub-arm: with the pair not "
                     "reconcilable (the following step is of the catch-all kind), "
                     "the alter step not elidable and the following step "
                     "elidable, C3 requires `result = [self]` — the receiver "
                     "VERBATIM, including its kind. This rival returns the "
                     "doctored copy. Probed at that arm specifically because it "
                     "is the only place the receiver is carried into the result, "
                     "and so the only place the rebinding is observable; on every "
                     "other arm the result is built from `op` or from named "
                     "components and the corruption is invisible. That is also "
                     "why this rival is refuted at its own point rather than "
                     "sharing one with `weak-drop-op-elidable-arm`, which fails "
                     "at the same flag setting for the opposite reason (it "
                     "returns nothing where this one returns a corrupted step).",
        "witness": _wit(_op("alterField", "Book", "title"),
                        _op("otherOp", "Book", "title", elidable="true",
                            repr_='"g"'), _T),
    },

    # ---- C3: the generic elidable pairing rule ----
    {
        "id": "weak-drop-self-elidable-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # Delete C3's first sub-arm: an elidable alter step is no longer dropped
        # in favor of the following step.
        "module": _impl(_IMPL.replace("""  if self.elidable then
    return [op]
""", "")),
        "refinement": "a step marked elidable may be dropped entirely when the "
                      "sequence is squashed; the generic pairing rule uses that "
                      "to collapse the pair to just the following step. Deleting "
                      "that sub-arm stops an elidable alteration from being "
                      "dropped, so sequences that used to shorten no longer do — "
                      "pre-existing behavior of the fall-through, unrelated to "
                      "the widened reconciliation. It would NOT resolve.",
        "rationale": "REJECT from C3's first sub-arm: with the two steps not "
                     "reconcilable and the alter step marked elidable, C3 "
                     "requires `result = [op]` and this rival returns `[]`. "
                     "Refuted at flag setting (self elidable, following step "
                     "not) — one of the three settings that separate C3's "
                     "sub-arms, and this rival's own.",
        "witness": _wit(_op("alterField", "Book", "title", elidable="true"),
                        _op("otherOp", "Book", "title", repr_='"g"'), _T),
    },
    {
        "id": "weak-drop-op-elidable-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # Delete C3's second sub-arm: an elidable FOLLOWING step is no longer
        # dropped in favor of the alter step.
        "module": _impl(_IMPL.replace("""  if op.elidable then
    return [self]
""", "")),
        "refinement": "the mirror sub-arm drops an elidable FOLLOWING step and "
                      "keeps the alteration. Deleting it stops that pair "
                      "shortening; the outcome for a non-reconcilable pair with "
                      "an elidable follower is asserted to be the alter step "
                      "alone, so this would NOT resolve.",
        "rationale": "REJECT from C3's second sub-arm: with the alter step not "
                     "elidable and the following step elidable, C3 requires "
                     "`result = [self]` and this rival returns `[]`. Refuted at "
                     "the COMPLEMENTARY flag setting to the previous rival, so "
                     "the two elidable binders are probed independently rather "
                     "than moving together.",
        "witness": _wit(_op("alterField", "Team", "coach"),
                        _op("otherOp", "Team", "coach", elidable="true",
                            repr_='"g"'), _T),
    },
    {
        "id": "weak-elidable-precedence-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # A deliberate NEAR-MISS on C3: both sub-arms are present and each is
        # individually right, but they are tested in the OPPOSITE order. The
        # rival therefore agrees with the spec on every input except the one
        # where BOTH steps are elidable — the single point where the precedence
        # is observable — so it is refuted there and nowhere else.
        "module": _impl(_IMPL.replace("""  if self.elidable then
    return [op]
  if op.elidable then
    return [self]
""", """  if op.elidable then
    return [self]
  if self.elidable then
    return [op]
""")),
        "refinement": "reversing which elidable flag is consulted first "
                      "corresponds to a patch that swapped the two branches of "
                      "the generic pairing rule. It is invisible unless BOTH "
                      "steps are elidable, and there the rule keeps the "
                      "following step while this rival keeps the alteration — so "
                      "a sequence of elidable steps optimizes to a different set "
                      "of operations, and the pair that should have collapsed "
                      "onto the follower collapses onto its predecessor instead. "
                      "It would NOT resolve.",
        "rationale": "REJECT from C3's first sub-arm: the arms are ORDERED — the "
                     "alter step's flag is consulted first, so when both steps "
                     "are elidable C3 requires `result = [op]`, and only the "
                     "second sub-arm's guard adds `self.elidable = false`. This "
                     "rival returns `[self]` there. A deliberate near-miss: it "
                     "agrees with the spec at every OTHER input, including both "
                     "single-flag settings where the two preceding rivals fail, "
                     "so it is refuted at the both-elidable point — the only "
                     "point that distinguishes it — rather than sharing either "
                     "of their witnesses. Between the three C3 rivals all four "
                     "flag combinations are covered.",
        "witness": _wit(_op("alterField", "Item", "sku", elidable="true"),
                        _op("otherOp", "Item", "sku", elidable="true",
                            repr_='"g"'), _TP),
    },
    {
        "id": "weak-fallthrough-returns-op",
        "kind": "uniqueness",
        "expect": "reject",
        # C3's last sub-arm: when NEITHER step is elidable no fused replacement
        # is produced. This rival invents one.
        "module": _impl(_IMPL.replace("""  if op.elidable then
    return [self]
  return []
""", """  if op.elidable then
    return [self]
  return [op]
""")),
        "refinement": "when the two steps are not reconcilable and neither is "
                      "droppable, no fused replacement exists and the pair must "
                      "be left alone. Producing the following step alone "
                      "silently deletes the alteration from the sequence for "
                      "every pairing that reaches the fall-through — the "
                      "broadest possible over-collapse, hitting unrelated steps "
                      "of every kind. It would NOT resolve.",
        "rationale": "REJECT from C3's third sub-arm: with neither step elidable "
                     "and the pair not reconcilable, C3 requires `result = []` "
                     "and this rival returns `[op]`. Refuted at a DIFFERENT "
                     "MODEL name — the one component the other fall-through "
                     "rivals hold equal — so the model-name binder is varied on "
                     "the C3 lane too, and the probed point is reached by "
                     "failing the same-field test rather than by the step kind.",
        "witness": _wit(
            _op("alterField", "Book", "title"),
            _op("otherOp", "Album", "title", repr_='"g"'),
            _tail_differing_names(_op("alterField", "Book", "title"),
                                  _op("otherOp", "Album", "title",
                                      repr_='"g"'),
                                  "model")),
    },
]


# ===========================================================================
# AXIOM lane — EMPTY, and DROPPED rather than ported: axiom soundness is G-AX's
# obligation and this gate ignores AXIOM_TESTS. It would be empty in any case —
# meta.json `axioms == []` and `deep_model_references == []`, since every step of
# the modeled reduction (the step-kind test, the case-insensitive name
# comparison, the explicit-column check, the elidable-flag reads, and the
# construction of replacement steps) is modeled directly rather than
# axiomatized. Matches the nagini sibling, whose AXIOM_TESTS is empty for the
# same reason.
# ===========================================================================
AXIOM_TESTS = []
