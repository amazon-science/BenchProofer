"""properties.py — G-PBT falsification battery for astropy__astropy-7166 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the ``theorem correct_inheritDocstrings`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect="reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a list of member records):

  inheritDocstrings (members : List Member)
                    (superDoc : List Char → Option (List Char)) : List Member

  A ``Member`` carries a name (``key``), two independent kind flags
  (``isFunction``, ``isDataDescriptor``) and its current documentation string
  (``doc : Option (List Char)``). ``superDoc`` is the resolved view of the base
  classes: the documentation a member of a given name would inherit (itself
  possibly absent). The postcondition has two top-level clauses:

    (C-len)  the result has ONE entry per input member;
    (C-elem) for each index i, the entry's ``key``, ``isFunction`` and
             ``isDataDescriptor`` are the input's VERBATIM, and its ``doc`` is
               ``superDoc (input i).key``   when ``eligible (input i)``,
               ``(input i).doc``            otherwise.

  ``eligible m = (m.isFunction || m.isDataDescriptor) && isPublicMember m.key
  && m.doc.isNone`` is spelled out in the spec view, fully grounded in the
  input record — there is no opaque answer key an impl could echo. Load-bearing
  facts, each attacked by a rival below:

    * the eligibility DECISION is a three-way conjunction whose first conjunct
      is a DISJUNCTION over the two kind flags: EITHER kind admits a member.
      Dropping the descriptor disjunct (R1), the public conjunct (R3) or the
      undocumented conjunct (R4) each narrows or widens the decision on a
      distinct sub-domain;
    * the publicity rule is ITSELF a disjunction, and its dunder arm is a
      three-part conjunction: a name admitted by that arm must carry the double
      underscore at BOTH ends and be longer than four characters. Each of the
      three parts is separately load-bearing, and the arm has two boundaries:
      keeping the prefix test while dropping the suffix test (R12) widens the
      decision on exactly the names that lead with a double underscore and do not
      close with one, and keeping both affix tests while dropping the LENGTH test
      (R13) widens it on exactly the four-character names made only of
      underscores, where the two affix tests overlap;
    * on the eligible branch the filled value is the INHERITED documentation for
      THAT member's own name — not absent (R5), not the member's name (R6), not
      the documentation resolved for some other member's name (R7);
    * every other component of every entry is carried through UNCHANGED — the
      name (R9) and both kind flags (R8) are never rewritten — and the INPUT the
      decision reads is the input the clause indexes, so an impl may not doctor
      its own view of a member before deciding on it (R14 clears a ``doc``, R15
      sets a kind flag);
    * the traversal is total and ORDER- and length-preserving: entry i of the
      result answers to member i of the input. No member is dropped (R10), no
      member is filled unconditionally (R2), and the entries are not permuted
      (R11) — C-elem indexes the input and the output at the SAME i, so a
      traversal that emits the right multiset in the wrong order violates it.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS AS A PERMISSION CLASS, LIVE AS BOTH A
    PRESERVATION AND AN INPUT-DOCTORING CLASS. Lean is referentially transparent:
    the inputs carry no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit, so the LITERAL store that nagini's two
    ``frame-mut-*`` rivals perform has no expressible instance and no substitute
    is fabricated for the permission MECHANISM. That collapse is DEMONSTRATED, not
    asserted: the nearest translation of nagini's ``m.inherited_doc = m.doc`` —
    rebind the member record inside the loop, then build the entry from the
    rebound copy — computes gold's function exactly, so the equation between it
    and the frozen impl closes by ``rfl`` and the "rival" VERIFIES. A store whose
    only effect is a value the impl recomputes identically has no observable
    instance here, which is precisely why the permission half cannot be ported
    rather than merely being hard to port. Two things do port, and both are
    attacked. (i) The frame OBLIGATION the spec states explicitly — C-elem's
    three verbatim-preservation conjuncts — which R8/R9 attack by rewriting a kind
    flag or a name in the OUTPUT. (ii) The MOVE those rivals make: keep the
    decision verbatim and satisfy the postcondition by corrupting the input it
    reads instead of by computing. R14/R15 port that directly — the rival rebuilds
    its own view of the member list (clearing a ``doc``, setting a kind flag) and
    then runs the frozen guard on the doctored view, while C-elem still indexes the
    ORIGINAL member. Unlike the vacuous store above, that corruption IS observable:
    R14 changes the result at an ineligible already-documented member, where it
    carries the cleared field through and the frozen impl carries the original.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason the nagini sibling
    gives. The eligibility predicate is unfolded in the spec view and grounded
    in the member record's own fields, and ``superDoc`` appears applied to the
    member's OWN name, so satisfying C-elem requires computing the same decision
    and selecting the right value. There is nothing to echo.

  * DIVERGENCE / NON-TERMINATION — genuinely VACUOUS here.
    ``implementation_inheritDocstrings`` is a total Lean ``def`` over a bounded
    ``for … in members`` traversal, so a non-terminating rival cannot be written
    at all; the class collapses on the carrier rather than being admitted by the
    spec. (Contrast the velvet sibling, where ``partial`` termination semantics
    make this a known spec HOLE — the corpus-wide termination-semantics finding. Not the situation
    on this backend.)

  * AXIOM lane — DROPPED. The nagini ``AXIOM_TESTS`` are empty and this bundle
    declares no ``axiom`` at all: the eligibility test is modeled deeply and the
    base-class resolution is an INPUT function (an A-reference validated by
    G-CONF/G-AX, which the G-PBT spec lane ignores).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input. Each was built twice and SEEN to discriminate: it elaborates
against its rival and FAILS on the frozen solution (there ``decide`` proves the
spec HOLDS, i.e. the negation is false — a semantic failure, not a tactic gap).
The carrier computes: ``Member`` derives ``DecidableEq``, names are ``List
Char`` literals and ``superDoc`` is passed as a concrete lambda, so every
witness is stated at literal inputs and closed by ``decide``. No witness needs
to condition on an opaque term, so none introduces a hypothesis whose
satisfiability could be in question.

WITNESS INPUT DIVERSITY. The reject witnesses deliberately spread over the
binders rather than reusing one discriminating member. Across the fifteen:
``isFunction``/``isDataDescriptor`` take three of the four combinations
(true/false, false/true and false/false), and the two SET flags are also
observed together within one two-member list (R8: one descriptor plus one
callable). No witness holds a member with BOTH flags set: that combination is
unreachable in the modeled domain (the Python-side bijection in mapping.md notes
a function is not a data descriptor and a descriptor is not a function), and
since the kind test is a DISJUNCTION such a member would decide exactly as
(true/false) does, so it discriminates nothing no rival already faces. ``key``
varies over public, dunder-free private (``_``-leading), a name that leads with a
double underscore but does NOT close with one (R12, the dunder arm's boundary), a
four-character all-underscore name that satisfies BOTH dunder-affix tests and
fails only the length test (R13, the arm's other boundary), and two distinct
names in one list; ``doc`` is both absent and already-present — three witnesses
carry a ``some`` doc (R4 at a single documented member, R11 mixing a documented
entry with an undocumented one, and R14 at a documented member the impl doctors
before deciding); ``superDoc`` is a constant ``some``, a constant ``none``, and a
NAME-DEPENDENT function (``fun k => some k``, used by R7 and R11) that separates
"resolved for this member" from "resolved for some other member"; and ``members``
has length 1 and length 2 with the ineligible entry both first and second. A
rival mishandling any single one of those inputs is caught by some witness
holding the others fixed.

INPUT-DOCTORING as the frame-mutation analogue. Nagini's two ``frame-mut-*``
rivals keep the decision verbatim and additionally WRITE a read-only input field,
so the postcondition is satisfied by clobbering the input rather than by
computing. On a referentially transparent carrier there is no write, but the
MOVE ports exactly: the rival rewrites its own VIEW of the member list before
deciding on it, so the decision is taken against doctored input while C-elem
still indexes the ORIGINAL. R14 doctors the ``doc`` field (clearing it, so an
already-documented member is treated as undocumented) and R15 doctors a kind flag
(setting ``isFunction``, so a member of neither kind is treated as a callable).
Both keep the frozen guard and the frozen filled value untouched, which is what
makes their rejection attributable to the read-only half of C-elem rather than to
a changed decision — the same attribution the permission system gives nagini.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7166"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# region anchors — each verified unique inside Solution.lean at load time
# ---------------------------------------------------------------------------

# The per-member decision inside the impl region's traversal. Every impl reshape
# and every rival lands here; the anchor lies wholly inside `-- impl-start` /
# `-- impl-end`.
_GUARD = (
    "    if eligible m then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]"
)

# The WHOLE impl declaration — used only by the positive that replaces the
# imperative traversal with a functional one.
_IMPL_ALL = (
    "def implementation_inheritDocstrings (members : List Member)\n"
    "    (superDoc : List Char → Option (List Char)) : List Member := Id.run do\n"
    "  let mut result : List Member := []\n"
    "  for m in members do\n"
    + _GUARD + "\n"
    "  return result"
)

# --- proof-region anchors (inside `-- proof-start` / `-- proof-end`) ---------

# The traversal lemma's STATEMENT body, as the frozen proof spells the
# per-member step. A positive that reshapes the impl must restate it to match.
_HELPER_STMT = (
    "          (if eligible m = true then\n"
    "            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))\n"
    "          else\n"
    "            pure (ForInStep.yield (r ++ [m]))))) =\n"
    "        init ++ members.map (fun m => if eligible m then "
    "{ m with doc := superDoc m.key } else m) := by"
)

# The same step as it appears in the `show` that re-types the impl.
_SHOW_STMT = (
    "          (if eligible m = true then\n"
    "            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))\n"
    "          else\n"
    "            pure (ForInStep.yield (r ++ [m]))))) = _"
)

# The inductive step's closing tactic.
_CONS_TAC = "      by_cases h : eligible a <;> simp [h, ih, List.append_assoc]"

# The whole "derive the functional form via the traversal lemma" block, which a
# functional impl makes unnecessary (the equation becomes `rfl`).
_TO_MAP_BLOCK = """  have helper : ∀ (members : List Member) (superDoc : List Char → Option (List Char)) (init : List Member),
      Id.run (forIn members init (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) =
        init ++ members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    intro members superDoc init
    induction members generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil, Id.run]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : eligible a <;> simp [h, ih, List.append_assoc]
  intro members superDoc
  have key : implementation_inheritDocstrings members superDoc =
      members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := by
    show Id.run (forIn members ([] : List Member) (fun m r =>
          (if eligible m = true then
            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))
          else
            pure (ForInStep.yield (r ++ [m]))))) = _
    rw [helper]
    simp
  rw [key]
"""

# The obligation's first tactic line — injection point for the admissibility
# ground instance (a `have` prepended before the frozen body).
_PROOF_HEAD = "  have helper : ∀ (members : List Member)"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (P1) FUNCTIONAL RESHAPE. The imperative accumulate-and-append traversal is
# replaced by a single map over the member list. Same entry at every index, so
# C-len and C-elem both still hold; MUST verify (else the postcondition is
# over-fit to the accumulator shape => SPEC-TOO-STRONG). The proof shrinks
# honestly rather than being weakened: the frozen script's whole purpose is to
# derive the functional form from the traversal, and for this impl that
# derivation IS `rfl`, so the traversal lemma is dropped and the SAME `key`
# equation is established directly. The obligation statement is byte-identical
# and the index-wise reasoning after `rw [key]` is the frozen text verbatim.
_POS_MAP = _swap(
    _BASE, _IMPL_ALL,
    "def implementation_inheritDocstrings (members : List Member)\n"
    "    (superDoc : List Char → Option (List Char)) : List Member :=\n"
    "  members.map (fun m => if eligible m then "
    "{ m with doc := superDoc m.key } else m)")
_POS_MAP = _swap(_POS_MAP, _TO_MAP_BLOCK, """  intro members superDoc
  have key : implementation_inheritDocstrings members superDoc =
      members.map (fun m => if eligible m then { m with doc := superDoc m.key } else m) := rfl
  rw [key]
""")

# (P2) NEGATED-GUARD BRANCH REORDER — the counterpart of nagini's
# guard-clause/De Morgan positive. The decision is tested NEGATED and the two
# arms are swapped, so the carry-through arm comes first and the fill arm second.
# Behaviourally identical (`!eligible m` is the Boolean complement), so both
# clauses still hold; MUST verify (else the spec is over-fit to the
# positive-guard form). The traversal lemma is restated to match the reshaped
# step and its inductive case is closed by `simp_all`, which normalizes the
# negated hypothesis the frozen `simp [h, …]` could not see through. No new
# declaration, no assumption token, statement byte-identical.
_POS_FLIP = _swap(
    _BASE, _GUARD,
    "    if !eligible m then\n"
    "      result := result ++ [m]\n"
    "    else\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]")
_POS_FLIP = _swap(_POS_FLIP, _HELPER_STMT, (
    "          (if (!eligible m) = true then\n"
    "            pure (ForInStep.yield (r ++ [m]))\n"
    "          else\n"
    "            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }])))))"
    " =\n"
    "        init ++ members.map (fun m => if eligible m then "
    "{ m with doc := superDoc m.key } else m) := by"))
_POS_FLIP = _swap(_POS_FLIP, _SHOW_STMT, (
    "          (if (!eligible m) = true then\n"
    "            pure (ForInStep.yield (r ++ [m]))\n"
    "          else\n"
    "            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }])))))"
    " = _"))
_POS_FLIP = _swap(_POS_FLIP, _CONS_TAC,
                  "      by_cases h : eligible a <;> simp_all [List.append_assoc]")

# (P3) VALUE-HOISTING RESHAPE. The entry to append is computed FIRST into a
# local and appended UNCONDITIONALLY — the branch moves from the control flow
# into the value, so the traversal has a single exit. Behaviourally identical;
# MUST verify (else the spec is over-fit to a branching traversal). The
# traversal lemma is restated with the branchless step and its inductive case no
# longer needs the case split, so `by_cases` is dropped — a simplification
# forced by the reshape, not a weakening: the same equation is proved.
_POS_LET = _swap(
    _BASE, _GUARD,
    "    let entry := if eligible m then { m with doc := superDoc m.key } else m\n"
    "    result := result ++ [entry]")
_POS_LET = _swap(_POS_LET, _HELPER_STMT, (
    "          (pure (ForInStep.yield\n"
    "            (r ++ [if eligible m then { m with doc := superDoc m.key } "
    "else m]))))) =\n"
    "        init ++ members.map (fun m => if eligible m then "
    "{ m with doc := superDoc m.key } else m) := by"))
_POS_LET = _swap(_POS_LET, _SHOW_STMT, (
    "          (pure (ForInStep.yield\n"
    "            (r ++ [if eligible m then { m with doc := superDoc m.key } "
    "else m]))))) = _"))
_POS_LET = _swap(_POS_LET, _CONS_TAC, "      simp [ih, List.append_assoc]")

# (P4) DECISION-EXPRESSION RESHAPE — the direct port of the sibling battery's
# operand-REORDER positive, which the three positives above do not cover: each of
# them reuses the frozen `eligible` call verbatim and reshapes only the traversal
# or the control flow, so the eligibility EXPRESSION itself was never varied. Here
# the decision is spelled out inline with its three conjuncts permuted (publicity
# first, undocumented second, kind test last) and the kind DISJUNCTION's operands
# swapped (descriptor before callable). `&&` and `||` on `Bool` are commutative
# and associative, so the decision is the same total function; MUST verify (else
# the spec is over-fit to the exact spelling of the guard rather than to its
# meaning => SPEC-TOO-STRONG). Reproved honestly: the equality of the reshaped
# guard with `eligible` is PROVED as a `have` by exhaustive case analysis on the
# four Booleans, not assumed, and the traversal lemma is then restated over the
# reshaped step and rewritten by it. No new declaration, no assumption token,
# obligation statement byte-identical.
_RESHAPED_GUARD = ("(isPublicMember m.key && m.doc.isNone "
                   "&& (m.isDataDescriptor || m.isFunction))")
_POS_EXPR = _swap(
    _BASE, _GUARD,
    f"    if {_RESHAPED_GUARD} then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")
_POS_EXPR = _swap(_POS_EXPR, _HELPER_STMT, (
    f"          (if {_RESHAPED_GUARD} = true then\n"
    "            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))\n"
    "          else\n"
    "            pure (ForInStep.yield (r ++ [m]))))) =\n"
    "        init ++ members.map (fun m => if eligible m then "
    "{ m with doc := superDoc m.key } else m) := by"))
_POS_EXPR = _swap(_POS_EXPR, _SHOW_STMT, (
    f"          (if {_RESHAPED_GUARD} = true then\n"
    "            pure (ForInStep.yield (r ++ [{ m with doc := superDoc m.key }]))\n"
    "          else\n"
    "            pure (ForInStep.yield (r ++ [m]))))) = _"))
_POS_EXPR = _swap(_POS_EXPR, _PROOF_HEAD, (
    f"  have hEq : ∀ m : Member, {_RESHAPED_GUARD} = eligible m := by\n"
    "    intro m\n"
    "    simp only [eligible]\n"
    "    cases hf : m.isFunction <;> cases hd : m.isDataDescriptor <;>\n"
    "      cases hp : isPublicMember m.key <;> cases hn : m.doc.isNone <;> simp\n"
    + _PROOF_HEAD))
_POS_EXPR = _swap(_POS_EXPR, _CONS_TAC, (
    "      simp only [hEq] at ih ⊢\n"
    "      by_cases h : eligible a <;> simp [h, ih, List.append_assoc]"))

# (ADMISS) ADMISSIBILITY GROUND INSTANCE. The frozen obligation carries NO
# precondition hypothesis (the behavior is total over `∀ members superDoc`), so
# nagini's precondition-admission probe has no binder to attack. The honest
# analogue: discharge the spec predicate by EVALUATION at the input shape the
# F2P exercises — a single public, undocumented member that is a descriptor
# rather than a callable, with its inherited documentation present — as a `have`
# inside the proof region, then close the frozen obligation with the frozen
# tactic body verbatim. If that ground instance could not be discharged the
# modeled behavior would be unsatisfiable at exactly the shape the F2P
# exercises, the analogue of PRECOND-TOO-STRONG. Nothing is assumed: no new
# declaration, the obligation statement is byte-identical, and the ground
# instance is closed by `decide` on literals.
_ADMISS = _swap(_BASE, _PROOF_HEAD, """  have _ground : problem_spec_inheritDocstrings
      [{ key := ['b','a','r'], isFunction := false, isDataDescriptor := true, doc := none }]
      (fun _ => some ['B','A','R'])
      (implementation_inheritDocstrings
        [{ key := ['b','a','r'], isFunction := false, isDataDescriptor := true, doc := none }]
        (fun _ => some ['B','A','R'])) := by
    unfold problem_spec_inheritDocstrings implementation_inheritDocstrings
    decide
""" + _PROOF_HEAD)


# ===========================================================================
# UNIQUENESS / REJECT rivals
# ===========================================================================

def _rival(body):
    return _swap(_BASE, _GUARD, body)


# (R1) THE DISCRIMINATING BUG. The eligibility decision admits only members
# whose CALLABLE flag is set, ignoring the descriptor flag entirely — the
# narrowed decision the modeled behavior is defined to widen.
_R1 = _rival(
    "    if (m.isFunction && isPublicMember m.key && m.doc.isNone) then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R2) NO DECISION AT ALL: every member is filled from the resolved base view,
# regardless of kind, name or existing documentation.
_R2 = _rival("    result := result ++ [{ m with doc := superDoc m.key }]")

# (R3) PARTIAL-DOMAIN: the name-publicity conjunct is dropped. Agrees with the
# spec on every public member; diverges only on the non-public sub-domain.
_R3 = _rival(
    "    if ((m.isFunction || m.isDataDescriptor) && m.doc.isNone) then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R4) PARTIAL-DOMAIN: the currently-undocumented conjunct is dropped. Agrees
# with the spec on every member lacking documentation; diverges only on the
# already-documented sub-domain, replacing documentation the member has.
_R4 = _rival(
    "    if ((m.isFunction || m.isDataDescriptor) && isPublicMember m.key) then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R5) VALUE: the decision is exactly the spec's, but the eligible entry is left
# with NO documentation instead of the inherited string.
_R5 = _rival(
    "    if eligible m then\n"
    "      result := result ++ [{ m with doc := none }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R6) VALUE: the decision is exactly the spec's, but the eligible entry is
# documented with its own NAME instead of the inherited string.
_R6 = _rival(
    "    if eligible m then\n"
    "      result := result ++ [{ m with doc := some m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R7) ARGUMENT: the decision and the source are both right, but the resolved
# view is consulted at the FIRST member's name for every eligible member rather
# than at each member's own name.
_R7 = _rival(
    "    if eligible m then\n"
    "      result := result ++ "
    "[{ m with doc := superDoc (members.headD default).key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R8) PRESERVATION: the eligible entry's two kind flags are rewritten instead
# of carried through.
_R8 = _rival(
    "    if eligible m then\n"
    "      result := result ++ [{ key := m.key, isFunction := true,\n"
    "                             isDataDescriptor := true, doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R9) PRESERVATION: the eligible entry's NAME is rewritten (reversed) instead
# of carried through.
_R9 = _rival(
    "    if eligible m then\n"
    "      result := result ++ "
    "[{ m with key := m.key.reverse, doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R10) TOTALITY: ineligible members are DROPPED from the result rather than
# carried through, so the result is shorter than the input.
_R10 = _rival(
    "    if eligible m then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]")

# (R11) ORDER: every entry is computed correctly and none is lost — the result is
# a PERMUTATION of the right multiset — but the traversal emits it reversed, so
# entry i no longer answers to member i. Attacks the positional half of C-elem,
# which every other rival leaves standing (R10 shortens the list, but nothing
# here reorders a list of the right length).
_R11 = _swap(
    _BASE, _IMPL_ALL,
    "def implementation_inheritDocstrings (members : List Member)\n"
    "    (superDoc : List Char → Option (List Char)) : List Member :=\n"
    "  (members.map (fun m => if eligible m then "
    "{ m with doc := superDoc m.key } else m)).reverse")

# (R12) PARTIAL-DOMAIN inside the PUBLICITY rule: the dunder arm keeps its prefix
# test and its length test but drops the requirement that the name also CLOSE
# with a double underscore. Agrees with the spec on every name the arm decides
# the same way; diverges only on long names that lead with a double underscore
# and do not end with one.
_R12 = _rival(
    "    let pub := (m.key.take 2 == ['_','_'] && m.key.length > 4)\n"
    "               || (m.key.head? != some '_')\n"
    "    if ((m.isFunction || m.isDataDescriptor) && pub && m.doc.isNone) then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# (R13) THE PUBLICITY RULE'S OTHER BOUNDARY. The dunder arm keeps BOTH affix tests
# and drops only the LENGTH test, so it admits the four-character name made purely
# of underscores — the one point where "opens with a double underscore" and "closes
# with a double underscore" are satisfied by the same four characters and only
# `length > 4` separates it from a genuine dunder name. Disjoint from R12, which
# keeps the length test and drops the suffix test: neither rival's witness reaches
# the other's sub-domain.
_R13 = _rival(
    "    let pub := (m.key.take 2 == ['_','_'] "
    "&& m.key.reverse.take 2 == ['_','_'])\n"
    "               || (m.key.head? != some '_')\n"
    "    if ((m.isFunction || m.isDataDescriptor) && pub && m.doc.isNone) then\n"
    "      result := result ++ [{ m with doc := superDoc m.key }]\n"
    "    else\n"
    "      result := result ++ [m]")

# The traversal's source list — the injection point for the two input-doctoring
# rivals, which leave the guard and the filled value verbatim and corrupt only the
# VIEW the traversal decides over. Inside `-- impl-start` / `-- impl-end`.
_FOR_SRC = "  for m in members do"


def _doctored(view):
    """A rival that keeps the frozen decision and the frozen filled value
    byte-for-byte and only rewrites the member list it walks."""
    return _swap(_BASE, _FOR_SRC, f"  for m in members.map (fun m => {view}) do")


# (R14) INPUT-DOCTORING on the documentation field — the referentially transparent
# port of nagini's frame-mutation move. The guard and the filled value are the
# frozen text verbatim; what changes is that the traversal walks a view in which
# every member's own documentation has been CLEARED, so the undocumented conjunct
# is evaluated against a fabricated `none` and an already-documented member is
# treated as eligible. Distinct from R4, which visibly deletes that conjunct: here
# the conjunct is still there and still consulted — the value it consults is the
# corrupted one, and C-elem's `else` arm still demands the ORIGINAL `doc`.
_R14 = _doctored("{ m with doc := none }")

# (R15) INPUT-DOCTORING on a kind flag, the second read-only component. Again the
# guard is verbatim; the traversal walks a view with `isFunction` forced true, so a
# member of NEITHER kind passes the kind test against a fabricated flag. Distinct
# from R8 in the MOVE, not in the surface it breaks: R8 decides correctly and then
# rewrites the flag on the way out, whereas here the corruption happens BEFORE the
# decision and is what changes it. Because the doctored record is also the one
# appended, the fabricated flag is observable in the OUTPUT too — at W15's input
# the entry's `isFunction` is `true` where the member's is `false` — so this rival
# violates C-elem's kind-preservation conjunct as well as its doc clause. That is
# a second reason it must be rejected, not a reason it is redundant: R8 leaves the
# DECISION intact and no existing rival corrupts the value the guard reads.
_R15 = _doctored("{ m with isFunction := true }")


# ---------------------------------------------------------------------------
# refutation witnesses — each built twice and SEEN to discriminate:
#   elaborates against its rival; FAILS on the frozen solution (there `decide`
#   proves the spec holds, so the negation is refuted — semantic, not tactical).
# ---------------------------------------------------------------------------

def _wit(members, super_doc):
    ms = "[" + ", ".join(members) + "]"
    return (
        "example : ¬ problem_spec_inheritDocstrings\n"
        f"    {ms}\n"
        f"    {super_doc}\n"
        "    (implementation_inheritDocstrings\n"
        f"      {ms}\n"
        f"      {super_doc}) := by\n"
        "  unfold problem_spec_inheritDocstrings "
        "implementation_inheritDocstrings\n"
        "  decide\n")


def _m(key, is_fn, is_dd, doc):
    ks = ",".join(f"'{c}'" for c in key)
    return ("{ key := [" + ks + "], isFunction := "
            + ("true" if is_fn else "false") + ", isDataDescriptor := "
            + ("true" if is_dd else "false") + ", doc := " + doc + " }")


def _sd(s):
    """A concrete resolved-base view: constant `none`, constant `some`, or the
    NAME-DEPENDENT `fun k => some k` (each member inherits its own name), which
    is what separates "resolved at this member's name" from "resolved at some
    other member's name"."""
    if s is None:
        return "(fun _ => none)"
    if s == "byname":
        return "(fun k => some k)"
    return "(fun _ => some [" + ",".join(f"'{c}'" for c in s) + "])"


# R1 at a public, undocumented member that is a DESCRIPTOR and NOT a callable —
# the member kind the decision must admit via its second disjunct.
_W1 = _wit([_m("bar", False, True, "none")], _sd("BAR"))
# R2 at a public, undocumented member that is NEITHER kind: the decision's first
# conjunct is false, so it must be carried through untouched.
_W2 = _wit([_m("num", False, False, "none")], _sd("NO"))
# R3 at an undocumented CALLABLE with a non-public (single-underscore) name.
_W3 = _wit([_m("_p", True, False, "none")], _sd("P"))
# R4 at a public callable that ALREADY carries its own documentation.
_W4 = _wit([_m("qux", True, False, "(some ['K','E','E','P'])")], _sd("SUP"))
# R5 at a plainly eligible public callable with inherited documentation present.
_W5 = _wit([_m("call", True, False, "none")], _sd("FOO"))
# R6 at an eligible descriptor whose resolved base view is ABSENT: the entry must
# stay undocumented, so documenting it with the name is visible.
_W6 = _wit([_m("baz", False, True, "none")], _sd(None))
# R7 at TWO eligible members with DIFFERENT names under the name-dependent
# resolved view — the only shape that separates per-member resolution from a
# single shared lookup.
_W7 = _wit([_m("aa", True, False, "none"), _m("bb", True, False, "none")],
           _sd("byname"))
# R8 at one eligible DESCRIPTOR plus one eligible CALLABLE, so both kind flags
# are observed being carried through in one input.
_W8 = _wit([_m("pro", False, True, "none"), _m("meth", True, False, "none")],
           _sd("K"))
# R9 at an eligible callable with a two-character name (so a rewritten name is
# distinguishable from the original).
_W9 = _wit([_m("ab", True, False, "none")], _sd("Z"))
# R10 with an INELIGIBLE member FIRST and an eligible one second: attacks C-len
# and, at the surviving index, the position the dropped member vacated.
_W10 = _wit([_m("_h", True, False, "none"), _m("open", True, False, "none")],
            _sd("D"))
# R11 at two members that stay DISTINCT after the fill, under the name-dependent
# resolved view — an eligible callable and an already-documented one. Both entries
# are present in the reversed result, so only the ORDER can be observed: the
# witness pins entry 0 to member 0, which a reversal breaks.
_W11 = _wit([_m("aa", True, False, "none"),
             _m("bb", False, False, "(some ['X'])")], _sd("byname"))
# R12 at a long name that OPENS with a double underscore and does not close with
# one — the exact sub-domain the dropped suffix test governs. It leads with an
# underscore, so the publicity rule's second arm does not admit it either, and it
# must be carried through untouched.
_W12 = _wit([_m("__abc", True, False, "none")], _sd("S"))
# R13 at the four-character all-underscore name: it OPENS and CLOSES with a double
# underscore (so both affix tests pass and R12's dropped test cannot separate it)
# and fails ONLY `length > 4`. It leads with an underscore, so the second arm does
# not admit it either, and it must be carried through untouched.
_W13 = _wit([_m("____", True, False, "none")], _sd("L"))
# R14 at an already-documented public callable: the member the doctored view
# misreports as undocumented. Same shape as W4 by necessity — the doctoring is only
# observable where the cleared field was non-empty — but the rival differs (R4 has
# no undocumented conjunct; R14 has it and feeds it a fabricated value).
_W14 = _wit([_m("qux", True, False, "(some ['K','E','E','P'])")], _sd("S"))
# R15 at a public undocumented member of NEITHER kind: the member the doctored
# view misreports as a callable. Its own kind flags come out preserved, so the only
# observable divergence is the doc the fabricated flag caused to be filled.
_W15 = _wit([_m("num", False, False, "none")], _sd("G"))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    {
        "id": "pos-functional-traversal",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": "structurally-different CORRECT implementation: the "
        "accumulate-and-append traversal is replaced by a single map over the "
        "member list, producing the same entry at every index. C-len and C-elem "
        "both still hold, so it MUST verify — a rejection would mean the "
        "postcondition is over-fit to the accumulator shape (SPEC-TOO-STRONG). "
        "Reproved honestly for the new shape: the frozen script's traversal "
        "lemma exists only to derive the functional form, which for this impl is "
        "`rfl`, so the same `key` equation is established directly and the "
        "index-wise reasoning after it is the frozen text verbatim. Obligation "
        "statement byte-identical; no new declaration, axiom or assumption "
        "token.",
    },
    {
        "id": "pos-negated-guard-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLIP,
        "rationale": "second correct shape and the counterpart of the sibling "
        "battery's guard-clause positive: the eligibility decision is tested "
        "NEGATED and the two arms are swapped, so the carry-through arm runs "
        "first. `!eligible m` is the Boolean complement, so behaviour is "
        "identical and both clauses still hold; a rejection would mean the spec "
        "is over-fit to the positive-guard form (SPEC-TOO-STRONG). The traversal "
        "lemma is restated to match the reshaped step and its inductive case "
        "closed by `simp_all`, which normalizes the negated hypothesis the "
        "frozen `simp [h, …]` cannot see through. Obligation statement "
        "byte-identical.",
    },
    {
        "id": "pos-hoisted-entry-value",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": "third correct shape: the entry to append is computed into "
        "a local FIRST and appended unconditionally, moving the branch out of "
        "the control flow and into the value so the traversal has a single exit. "
        "Behaviourally identical; must verify (else the spec is over-fit to a "
        "branching traversal). The traversal lemma is restated with the "
        "branchless step, which makes its case split unnecessary — the same "
        "equation is proved, with a step the reshape made uniform. Distinct from "
        "pos-functional-traversal, which changes the traversal itself while "
        "keeping the branch; this keeps the imperative traversal and moves the "
        "branch.",
    },
    {
        "id": "pos-reshaped-decision-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EXPR,
        "rationale": "fourth correct shape, and the one the other three leave "
        "out: each of them calls the frozen `eligible` verbatim and reshapes only "
        "the traversal or the control flow, so the eligibility EXPRESSION itself "
        "was never varied — the direct analogue of the sibling battery's "
        "operand-reorder positive. Here the decision is spelled out inline with "
        "its three conjuncts permuted (publicity, undocumented, kind) and the kind "
        "DISJUNCTION's operands swapped (descriptor before callable). `&&` and "
        "`||` on `Bool` are commutative, so this is the same total decision and it "
        "must verify; a rejection would mean the spec is over-fit to the guard's "
        "exact spelling rather than its meaning (SPEC-TOO-STRONG). Reproved "
        "honestly rather than weakened: the reshaped guard's equality with "
        "`eligible` is PROVED as a `have` by exhaustive case analysis on the four "
        "Booleans, then used to rewrite the restated traversal lemma. Obligation "
        "statement byte-identical; no new declaration or assumption token.",
    },
    {
        "id": "admiss-descriptor-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the frozen obligation carries no precondition hypothesis "
        "(the behavior is total over `∀ members superDoc`), so there is no "
        "binder for a precondition-admission probe to attack. The honest "
        "analogue: the spec predicate is discharged BY EVALUATION at the input "
        "shape the F2P exercises — one public, undocumented member that is a "
        "descriptor rather than a callable, with its inherited documentation "
        "present — as a `have` inside the proof region, after which the frozen "
        "obligation is closed with the frozen tactic body verbatim. Verifies, "
        "else the modeled behavior is unsatisfiable at exactly the shape the F2P "
        "exercises (the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
        "new declaration, statement byte-identical, ground instance closed by "
        "`decide` on literals.",
    },

    # =====================================================================
    # UNIQUENESS / REJECT rivals
    # =====================================================================
    {
        "id": "decision-ignores-descriptor-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R1,
        "refinement": "this IS the pre-existing narrowed behavior: the "
        "eligibility test admits only members whose CALLABLE flag is set and "
        "never consults the descriptor flag, so a public undocumented member "
        "that mediates attribute access is skipped and keeps no documentation. "
        "The F2P builds exactly such a member in a subclass and asserts it "
        "carries the base's documentation string; under this decision it carries "
        "none, so the assertion FAILS. Its faithful real patch is the "
        "before-state of the modeled change and does NOT resolve.",
        "rationale": "REJECT from C-elem, the spec's per-index clause "
        "`∀ i, i < members.length → … (result.getD i default).doc = …`: for a "
        "member the spec deems eligible via the SECOND disjunct of the kind "
        "test, the entry's documentation must be `superDoc m.key`, but this "
        "rival leaves it absent. If it verified the spec would admit the very "
        "behavior the "
        "modeled change removes => SPEC-TOO-WEAK. Witness varies the two kind "
        "flags to (callable=false, descriptor=true), the combination no other "
        "single-member witness uses.",
        "witness": _W1,
    },
    {
        "id": "fills-every-member-unconditionally",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R2,
        "refinement": "drops the eligibility decision entirely and documents "
        "every member from the resolved base view. Its faithful real patch "
        "copies base documentation onto members of any kind, onto non-public "
        "names, and over documentation members already define — so the "
        "already-documented expectation the F2P test also asserts (a member that "
        "defines its own string keeps it) breaks, and members that are neither "
        "callable nor descriptors acquire documentation they should not have. "
        "Plainly not the modeled change; it does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the NEGATIVE arm: when "
        "the member is ineligible the entry's documentation must equal the "
        "member's own, but this rival sets it to the resolved value. If it "
        "verified => SPEC-TOO-WEAK (the decision is unconstrained). Witness "
        "holds a SINGLE member that fails the kind test on BOTH flags "
        "(callable=false, descriptor=false), so that failure alone carries the "
        "refutation; it shows the first conjunct is load-bearing in the "
        "restrictive direction, not just the permissive one R1 attacks.",
        "witness": _W2,
    },
    {
        "id": "decision-ignores-name-publicity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R3,
        "refinement": "PARTIAL-DOMAIN: the name-publicity conjunct is dropped, "
        "so the rival agrees with the modeled behavior on every public member "
        "and diverges only on non-public names. Its faithful real patch removes "
        "the name test from the guard, so members whose names mark them internal "
        "acquire base documentation — a behavioural regression against the "
        "publicity rule the modeled behavior states explicitly, and not the "
        "modeled change; it does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the NEGATIVE arm, "
        "restricted to the non-public sub-domain. Witness varies `key` to a "
        "single-underscore-leading name — the only witness at a non-public name, "
        "so it is what demonstrates the spec's dependence on the name binder. "
        "This is a NEAR-MISS of gold (it agrees everywhere else), so it gets its "
        "own witness rather than sharing R2's: R2's witness input is public and "
        "this rival is correct there. If it verified => SPEC-TOO-WEAK "
        "(domain-incomplete).",
        "witness": _W3,
    },
    {
        "id": "decision-ignores-existing-doc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R4,
        "refinement": "PARTIAL-DOMAIN: the currently-undocumented conjunct is "
        "dropped, so the rival agrees with the modeled behavior on every member "
        "lacking documentation and diverges only on already-documented members, "
        "replacing their string with the base's. Its faithful real patch removes "
        "the existing-documentation test from the guard; the F2P test also "
        "asserts a subclass member that defines its own documentation keeps it, "
        "so that assertion breaks. Not the modeled change; it does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the NEGATIVE arm, "
        "restricted to the already-documented sub-domain. Witness probes the "
        "`doc` binder at `some …` rather than `none` at a SINGLE member, so the "
        "already-documented state is what the refutation turns on with nothing "
        "else varying — which is what demonstrates the spec depends on the "
        "existing-documentation input at all. NEAR-MISS of gold, so it carries "
        "its own witness. If it verified "
        "=> SPEC-TOO-WEAK (domain-incomplete).",
        "witness": _W4,
    },
    {
        "id": "eligible-entry-left-undocumented",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R5,
        "refinement": "the eligibility decision is exactly the modeled one, but "
        "the selected entry is left with NO documentation instead of the "
        "inherited string. Its faithful real patch decides correctly which "
        "members to fill and then clears their documentation instead of copying "
        "the resolved value, so the F2P assertion that the subclass member "
        "carries the base's string FAILS (it would carry none). It does NOT "
        "resolve.",
        "rationale": "REJECT from C-elem's doc clause on the POSITIVE arm: for "
        "an eligible member the entry's documentation must be `superDoc m.key`, "
        "but this rival makes it absent. The decision and every preservation "
        "conjunct are correct, so no decision-attacking witness reaches this — "
        "it is the distinct 'the filled VALUE is the inherited one' fact. Witness "
        "at a plainly eligible callable with the resolved view present, so the "
        "clash is between a `some` and a `none`.",
        "witness": _W5,
    },
    {
        "id": "eligible-entry-documented-with-own-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R6,
        "refinement": "the decision is exactly the modeled one and the entry IS "
        "documented, but with the member's own name rather than the string "
        "resolved through the base classes. Its faithful real patch assigns the "
        "member's name where it should assign the resolved documentation, so the "
        "F2P assertion comparing against the base's string FAILS. It does NOT "
        "resolve.",
        "rationale": "REJECT from C-elem's doc clause on the POSITIVE arm, "
        "distinct from R5: the value is PRESENT but wrong, so a witness that "
        "only separates `some` from `none` at a resolved-present input cannot "
        "reach it. Witness therefore probes the `superDoc` binder at the "
        "constant-ABSENT view — the only witness where the resolved value is "
        "`none`, which is exactly where 'documented with the name' and 'left as "
        "the member had it' diverge. Also varies the kind flags to a descriptor.",
        "witness": _W6,
    },
    {
        "id": "resolves-doc-at-wrong-member-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R7,
        "refinement": "the decision is exactly the modeled one and the resolved "
        "base view IS consulted, but at the first member's name for every "
        "eligible member instead of at each member's own name. Its faithful real "
        "patch looks the base attribute up under a name fixed once per class "
        "rather than per member, so every filled member receives the same "
        "string; the F2P asserts a specific member carries the string resolved "
        "for ITS name, which fails as soon as the class has more than one "
        "member. It does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the POSITIVE arm, "
        "attacking the ARGUMENT rather than the value: `superDoc` is applied to "
        "the wrong name. One of only two witnesses that pass a NAME-DEPENDENT "
        "resolved view (`fun k => some k`; the other is R11's, which reverses "
        "order rather than mis-resolving), and the only one that does so over TWO "
        "members both of which are ELIGIBLE and differently named — a constant view "
        "makes this rival agree with the spec everywhere, so no other witness "
        "here can discriminate it. Varies the `members` binder to length 2 with "
        "both entries eligible. If it verified => SPEC-TOO-WEAK (the spec would "
        "not pin which name is resolved).",
        "witness": _W7,
    },
    {
        "id": "rewrites-entry-kind-flags",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R8,
        "refinement": "the decision and the filled documentation are both "
        "correct, but the entry's two kind flags are rewritten rather than "
        "carried through. Its faithful real patch replaces each selected member "
        "with a differently-kinded object instead of documenting the member in "
        "place, so a member that was a descriptor is no longer observably one "
        "and a plain attribute becomes callable — the class's members change "
        "identity. The F2P reads the member through normal attribute access, "
        "which such a substitution breaks; it does NOT resolve.",
        "rationale": "REJECT from C-elem's two kind-PRESERVATION conjuncts, "
        "which no other rival touches — the referentially transparent analogue "
        "of the sibling battery's read-only-field mutation: an output component "
        "the spec pins to its input value is altered. Witness holds one "
        "descriptor AND one callable in a single list so both flags are observed "
        "being preserved, and varies `members` to length 2 with a kind mix no "
        "other witness uses.",
        "witness": _W8,
    },
    {
        "id": "rewrites-entry-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R9,
        "refinement": "the decision, the resolved lookup and the kind flags are "
        "all correct, but the entry's NAME is rewritten. Its faithful real patch "
        "re-keys the members it documents, so the documented member is no longer "
        "reachable under the name it was defined with; the F2P looks the member "
        "up by name, so it FAILS. It does NOT resolve.",
        "rationale": "REJECT from C-elem's name-PRESERVATION conjunct, the third "
        "verbatim-carry-through fact and the one R8 leaves untouched (R8 rewrites "
        "flags and preserves the name). Separate rival and separate witness "
        "because the two attack independent conjuncts. Witness varies `key` to a "
        "two-character public name, where a rewritten name is distinguishable "
        "from the original.",
        "witness": _W9,
    },
    {
        "id": "drops-ineligible-members",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R10,
        "refinement": "the decision is exactly the modeled one, but members it "
        "rejects are OMITTED from the result rather than carried through. Its "
        "faithful real patch removes from the class every member it does not "
        "document — non-public members, already-documented members and members "
        "of neither kind all disappear — so the class loses most of its "
        "namespace. Both the F2P and the surrounding tests access such members, "
        "so it does NOT resolve.",
        "rationale": "REJECT from C-len — the spec's first top-level conjunct "
        "`result.length = members.length`, one entry per input member — which no "
        "other rival attacks, every other rival being length-preserving. Also "
        "shifts "
        "later entries, so C-elem fails at the surviving index too. Witness "
        "places the INELIGIBLE member FIRST and an eligible one second, the only "
        "witness with that ordering, so both the length loss and the positional "
        "shift are exercised.",
        "witness": _W10,
    },
    {
        "id": "emits-entries-in-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R11,
        "refinement": "every entry is computed correctly and none is lost — the "
        "result is a PERMUTATION of the right multiset — but the traversal emits "
        "it in reverse, so the entry at index i no longer answers to the member "
        "at index i. Its faithful real patch rebuilds the class's members in the "
        "opposite order to the one it walked them in, so each member's "
        "documentation lands on a DIFFERENT member: the F2P reads one specific "
        "member and finds the string resolved for another, so it FAILS as soon as "
        "the class has more than one eligible member. It does NOT resolve.",
        "rationale": "REJECT from the POSITIONAL half of C-elem: the clause "
        "indexes the input and the result at the SAME `i` "
        "(`(result.getD i default).key = (members.getD i default).key`), so "
        "agreeing as a multiset is not enough. No other rival tests this — R10 "
        "shortens the list, and every remaining rival is index-wise "
        "order-preserving, so a permuting impl was previously unattacked. If it "
        "verified the spec would pin only the CONTENTS and not the order => "
        "SPEC-TOO-WEAK. Witness holds two members that remain distinct after the "
        "fill (an eligible callable and an already-documented one, the only "
        "witness mixing those two states in one list) under the name-dependent "
        "resolved view, so the reversal is what the refutation observes.",
        "witness": _W11,
    },
    {
        "id": "publicity-drops-dunder-suffix-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R12,
        "refinement": "PARTIAL-DOMAIN one level deeper than R3: the publicity "
        "rule is kept, but its dunder arm loses the requirement that the name "
        "also CLOSE with a double underscore — the prefix and length tests stay. "
        "The rival therefore agrees with the modeled behavior on every name that "
        "arm decides the same way and diverges only on long names that OPEN with "
        "a double underscore and do not end with one, which the rule treats as "
        "internal. Its faithful real patch tests only how a name begins, so "
        "name-mangled internals acquire base documentation; that is a behavioural "
        "regression against the publicity rule the modeled behavior states "
        "explicitly, and not the modeled change. It does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the NEGATIVE arm, "
        "restricted to the leading-dunder-without-trailing-dunder sub-domain. R3 "
        "deletes the publicity conjunct WHOLESALE and its witness is a "
        "single-underscore name, which this rival handles correctly (it keeps the "
        "second arm verbatim); so R3's witness cannot reach here and the internal "
        "structure of the publicity predicate — a disjunction whose first arm is "
        "itself a three-part conjunction — was otherwise untested at its "
        "boundary. Witness varies `key` to a name that leads with a double "
        "underscore and does not close with one — R13 probes the arm's OTHER "
        "boundary and its name closes with one, so the two witnesses are at "
        "disjoint points. If it verified => SPEC-TOO-WEAK "
        "(domain-incomplete inside the name predicate).",
        "witness": _W12,
    },
    {
        "id": "publicity-drops-dunder-length-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R13,
        "refinement": "PARTIAL-DOMAIN at the publicity rule's OTHER boundary: the "
        "dunder arm keeps BOTH affix tests and loses only the requirement that the "
        "name be longer than four characters. The rival therefore agrees with the "
        "modeled behavior on every longer name and diverges only on the "
        "four-character name made purely of underscores, which satisfies both affix "
        "tests at once and which the rule treats as internal. Its faithful real "
        "patch omits the length test from the name predicate, so that degenerate "
        "name acquires base documentation — a behavioural regression against the "
        "publicity rule the modeled behavior states explicitly, and not the modeled "
        "change. It does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the NEGATIVE arm, "
        "restricted to the four-character all-underscore sub-domain. The dunder arm "
        "is a THREE-part conjunction and R12 attacks only the suffix part: R12's "
        "witness name does not close with a double underscore, which this rival "
        "decides CORRECTLY (it keeps the suffix test), so R12's witness cannot reach "
        "here and the length part was otherwise unprobed. Witness varies `key` to "
        "the battery's only name where the prefix and suffix tests overlap, so the "
        "length test alone carries the decision. If it verified => SPEC-TOO-WEAK "
        "(domain-incomplete inside the name predicate).",
        "witness": _W13,
    },
    {
        "id": "doctors-input-doc-before-deciding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R14,
        "refinement": "the referentially transparent port of the sibling battery's "
        "frame-mutation rival: the decision and the filled value are the modeled "
        "ones VERBATIM, and what the rival changes is the member list it decides "
        "over — it walks a view in which every member's own documentation has been "
        "cleared. Its faithful real patch discards each member's existing "
        "documentation before testing whether the member has any, so a member that "
        "defines its own string is treated as undocumented and has it replaced by "
        "the base's. The F2P also asserts that a subclass member which defines its "
        "own documentation keeps it, so that assertion breaks; it does NOT resolve.",
        "rationale": "REJECT from C-elem's doc clause on the NEGATIVE arm, and the "
        "attack is on the INPUT the clause indexes rather than on the guard: the "
        "spec's `if eligible (members.getD i default)` is evaluated at the ORIGINAL "
        "member, so an impl that decides against a fabricated view diverges even "
        "though its guard text is the frozen one. This is the class nagini rejects "
        "for INSUFFICIENT PERMISSION on a half-permission field, which has no "
        "literal instance here — the move, satisfying the postcondition by "
        "corrupting an input it may only read, ports exactly. Distinct from R4, "
        "which deletes the undocumented conjunct outright: this rival still has it "
        "and still consults it. Witness holds an already-documented public callable, "
        "the point where a cleared field is observable at all.",
        "witness": _W14,
    },
    {
        "id": "doctors-input-kind-flag-before-deciding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R15,
        "refinement": "the same input-doctoring move on the second read-only "
        "component: the guard and the filled value are the modeled ones verbatim, "
        "but the traversal walks a view with the callable flag forced set, so a "
        "member of NEITHER kind passes the kind test. Its faithful real patch treats "
        "every member as callable before testing its kind, so plain attributes "
        "acquire base documentation they should not have. Not the modeled change; it "
        "does NOT resolve.",
        "rationale": "REJECT from C-elem on the NEGATIVE arm, reached via the input "
        "the guard reads rather than via the guard: a member of neither kind is "
        "documented because the flag the kind test consulted was fabricated. "
        "Distinct from R8 in the MOVE rather than in the surface it breaks — R8 "
        "decides correctly and rewrites the flag on the way out, while here the "
        "corruption precedes the decision and is what changes it. Because the "
        "doctored record is also the one appended, the fabricated flag shows up in "
        "the OUTPUT as well, so the kind-preservation conjunct is violated too; "
        "verified by building the rival at this witness's input and evaluating the "
        "entry's `isFunction` (`true`) against the member's (`false`). That is a "
        "second reason to reject, not a reason the case is redundant: no other "
        "rival corrupts the value the decision reads. Witness holds a public "
        "undocumented member with both kind flags clear, the point where a forced "
        "flag changes the decision.",
        "witness": _W15,
    },
]
