"""properties.py — G-PBT falsification battery for django__django-13794 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: every case changes text inside the ``-- impl-start`` / ``-- impl-end``
region, and ``admiss-ground`` alone additionally prepends ``have``s to the
``-- proof-start`` / ``-- proof-end`` tactic body — so ``markers.same_spec`` holds
and the single ``theorem correct_lazyConcat`` STATEMENT stays byte-identical in
every case, which is what the scope check requires; see REGION SCOPE below).
``expect:"verify"`` passes
iff (in scope AND the file elaborates with the obligation closed, no
``sorry``/``admit``/``native_decide`` and no new ``axiom``/``theorem``);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO functions over a ``List[int]`` code-point carrier —
``forward_combine(realized, other)`` pinning ``realized ++ other`` and
``reverse_combine(realized, other)`` pinning ``other ++ realized`` — because the
gold patch adds two proxy methods (a forward operator and a reflected one). This
Lean bundle models the SAME purely-functional core as ONE total function,
``implementation_lazyConcat (a b : Operand) : String``, where the operand carrier
distinguishes an ordinary concrete value from an on-demand (forced) one, and
which operand is on-demand selects the code path. The single postcondition

    problem_spec_lazyConcat a b result :=  result = force a ++ force b

pins the observable result to the concatenation of the two forced underlying
texts, in left-to-right order — fully grounded in the inputs, no opaque oracle.

CARRIER NARROWING (why this is not a 9-case port). The nagini battery's operand
order is split across two separately-contracted functions; here BOTH directions
live in the single ``force a ++ force b`` clause, so a rival can only be built by
reshaping the ONE impl. The nagini frame/permission-mutation class
(``frame-mut-realized-fwd``, ``frame-mut-other-rev``) is INEXPRESSIBLE on this
carrier, and that is a MEASURED claim, not an assumption. Two probes were built:
(a) a variant whose impl assigns to the input binder directly (``a := ...``) does
not compile at all — Lean reports ```a` cannot be mutated, only variables declared
using `let mut` can be mutated``, so the rival cannot even be posed; (b) a variant
that takes a ``let mut`` LOCAL copy of each operand and clobbers the copies still
VERIFIES (exit 0), because the write is to a fresh local and is unobservable in
the returned value. There is no fractional permission and no aliasable mutable
input to violate, so a write-back rival is either uncompilable or observationally
equal to gold — never a rival that this spec should reject. There is no
divergence/non-termination lane in the nagini sibling, and it would be vacuous
here anyway (``implementation_lazyConcat`` is a total Lean ``def``).
``AXIOM_TESTS`` is dropped (the axiom lane is G-AX's job; the frozen ``axioms``
region declares no ``opaque``/``axiom`` callee).

ADMISSIBILITY (added by audit; the port dropped this lane and the reason it gave
was not sufficient). The dropped-lane reason on record was "the frozen obligation
has NO precondition, so there is nothing for an admissibility case to probe" —
true about preconditions, but the wrong test on a TOTAL carrier. The lane detects
PRECOND-TOO-STRONG, whose analogue here is the obligation being UNSATISFIABLE at
exactly an F2P-shaped input: a spec can be universally quantified and still be
unsatisfiable at the very operand pairs the change is about, in which case
``correct_lazyConcat`` would only ever be closable vacuously and the whole battery
would be attesting to nothing. ``admiss-ground`` tests that directly and
positively — it discharges ``problem_spec_lazyConcat`` BY EVALUATION at three
concrete F2P-shaped operand pairs (on-demand left, on-demand right, and both
on-demand — the three code paths the modeled change is about) as ``have``s, and
only then closes the frozen obligation verbatim. Because each ``have`` is closed
by ``decide`` on concrete literals, its success is a positive exhibition of a
satisfying result at that pair, not an appeal to the universal statement.

REGION SCOPE. Every case here edits the ``impl`` region; ``admiss-ground``
additionally PREPENDS ``have``s to the ``proof`` region's tactic body, which
``variant_scope`` permits (only the obligation STATEMENT is frozen — verified:
``variant_problems`` == [] for it). No case anywhere rewrites the
``theorem correct_lazyConcat`` statement, which is what ``same_spec`` and the
obligation-preserved check actually require.

DEFENDED SURFACE (one modeled behavior; one top-level clause with two operand
sub-terms). The single equation ``result = force a ++ force b`` has two INPUT
binders, ``a`` and ``b``, each of which independently carries an underlying text
AND a concrete/deferred tag that selects the branch. The reject witnesses vary
BOTH binders across all four concrete/deferred combinations so no branch and no
operand position is left unprobed. Two dimensions are attacked separately:

* WHICH OPERAND SLOT is mishandled — ``weak-drop-left`` discards the left slot,
  ``weak-drop-right`` the right, ``weak-swap-order`` keeps both but inverts them,
  ``weak-dup-right`` emits a right slot twice (a SUPERSET of the required text,
  not a subset — the other rivals all lose or reorder content).
* HOW MUCH of a slot is lost — the slot-level rivals above lose a WHOLE operand,
  so an off-by-one needs its own rivals, and it needs one PER SLOT:
  ``weak-drop-last-other`` truncates the right operand's trailing character and
  ``weak-drop-first-left`` the left operand's leading one. Each is witnessed at a
  TWO-character operand so its refutation cannot be confused with whole-slot loss.
* WHICH BRANCH is mishandled — the slot rivals are uniformly wrong across all
  four tag combinations, which leaves "a rival wrong in only ONE branch" a claim
  the battery would not have demonstrated. Three branch-selective rivals close
  that, and they are chosen to attack from BOTH sides so no over-fitting
  direction is left open. ``weak-branch-both-deferred`` is CORRECT in three of
  the four tag combinations and wrong only when both operands are on-demand.
  ``weak-unforced-deferred`` is exactly correct on the all-concrete path and
  treats an un-forced on-demand operand as empty, i.e. it is the genuine
  pre-change image (see that case's refinement). ``weak-swap-only-concrete`` is
  the complement of both: correct on all three on-demand paths and wrong ONLY on
  the all-concrete one, which is what attacks a spec over-fitted to pin just the
  paths the modeled change touches — the other two would leave that spec
  standing.

WITNESS DISCRIMINATION (checked empirically before shipping, and re-derived by an
independent audit). Each reject case carries a ``witness`` — a Lean ``example``
stating the spec predicate is FALSE of the rival at one concrete operand pair. It
was built against the rival (must elaborate — the rival provably contradicts the
spec at that pair) and against the frozen ``Solution.lean`` (must FAIL). On gold
every witness fails with ``Tactic `decide` proved that the proposition ¬(...) is
false`` — a SEMANTIC refutation of the concrete claim (the spec demonstrably HOLDS
of gold at that pair), never a missing identifier, type error or unfolding
failure. ``decide`` closes both halves on these small string literals.

WITNESS POINTS ARE CHOSEN TO SEPARATE THE CLAIMED SUB-DOMAIN FROM ITS NEIGHBOURS.
A witness must refute the clause the case's ``rationale`` actually names, which
constrains the literal: ``weak-drop-last-other`` claims the TRAILING-CHARACTER
sub-domain, so its right operand must be at least TWO characters long. Witnessed
at a one-character right operand, ``.dropRight 1`` yields the empty text and the
rival's output would be indistinguishable from ``weak-drop-right``'s — the build
would still discriminate against gold, but it would attest to "the right operand
was lost" rather than to the off-by-one the rationale claims. Its witness
therefore uses a two-character right operand, where gold gives ``"PQR"`` and the
rival gives ``"PQ"``: one character short, and provably not the whole slot.
"""

from pathlib import Path

INSTANCE = "django__django-13794"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The FROZEN impl block, verbatim (everything from `def implementation_lazyConcat`
# through the final branch, INSIDE the `-- impl-start` / `-- impl-end` region).
# Every variant _swap()s ONLY this block, so the edit never touches the spec
# (pure/post-conditions regions + the `problem_spec_lazyConcat` predicate + the
# `theorem correct_lazyConcat` STATEMENT). same_spec is guaranteed by construction.
# The block is unique in Solution.lean.
# ---------------------------------------------------------------------------
_IMPL = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s =>
      -- left operand is on-demand: force it, then concatenate with the right
      return s ++ force b
  | .concrete s =>
      match b with
      | .deferred t =>
          -- left concrete, right on-demand: force the right and append it
          return s ++ t
      | .concrete t =>
          -- both concrete: ordinary text concatenation
          return s ++ t"""

assert _BASE.count(_IMPL) == 1, "implementation_lazyConcat impl region drifted"

# The FROZEN proof body (inside `-- proof-start` / `-- proof-end`). A soundness
# positive that changes the impl SHAPE must still re-close the obligation. The
# three impl-reshaping positives below keep this exact body, and that is a
# MEASURED fact for each of them (own build, exit 0): their reshaped impls —
# including the representation-level one, which does not use `String` `++` at all
# — reduce definitionally under `cases a <;> cases b <;> rfl`.
#
# SCOPE OF THAT FACT (corrected by audit; the earlier text over-generalized it).
# It is a claim about these three impls, NOT about every correct reshape on this
# carrier: `cases a <;> cases b <;> rfl` is NOT universal here. Two correct
# reshapes were re-measured and both FAIL under this body (exit 1, `Tactic `rfl`
# failed: ... is not definitionally equal to ...`): folding the right operand's
# characters onto the left with `String.push`, and the double-reverse route
# `⟨((force b).data.reverse ++ (force a).data.reverse).reverse⟩`. Both are
# nonetheless PROVABLE — each verifies with a bespoke tactic body (a `foldl`
# induction lemma / `String.push` unfolding), so neither is a soundness hole in
# the spec, only a limit of this particular script. `variant_scope` permits a
# case to replace the tactic body (only the obligation STATEMENT is frozen), and
# `admiss-ground` below does prepend to it. What keeps `same_spec` and the
# obligation-preserved check true for every case is that no case rewrites the
# theorem STATEMENT — not that every case leaves the body untouched.
_PROOF = """\
  intro a b
  unfold problem_spec_lazyConcat implementation_lazyConcat
  cases a <;> cases b <;> rfl"""

assert _BASE.count(_PROOF) == 1, "correct_lazyConcat proof body drifted"


def _impl(new_block):
    """Solution.lean variant with ONLY the impl block replaced."""
    return _swap(_BASE, _IMPL, new_block)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY with the obligation genuinely
# re-closed (no weakening, no sorry, no new lemma).
# ===========================================================================

# pos-direct: the most structurally-different CORRECT impl — no case analysis at
# all, just `force a ++ force b` directly. Nagini's positive control caches loop
# bounds while keeping the two-phase append loop; that machinery has no counterpart
# here, so the faithful analogue is "produce the concatenation by the shortest
# correct route". The frozen proof body still closes it (both sides reduce to
# `force a ++ force b`). If it FAILED => SPEC-TOO-STRONG (a faithful correct impl
# rejected). Exercises the load-bearing clause `result = force a ++ force b`.
_POS_DIRECT = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  return force a ++ force b"""

# pos-matchb: a correct impl that branches on the RIGHT operand instead of the
# left (the frozen impl matches `a` outermost; this matches `b`). Same result on
# every operand pair, different control-flow shape. Reproven by the frozen body
# (`cases a <;> cases b <;> rfl` closes both shapes). If it FAILED =>
# SPEC-TOO-STRONG. Confirms the spec does not secretly depend on WHICH operand is
# scrutinised first — only on the forced values and their order.
_POS_MATCHB = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match b with
  | .deferred t =>
      return force a ++ t
  | .concrete t =>
      return force a ++ t"""

# pos-repr-shift: a correct impl that abandons the `Id.run do` / `return` monadic
# wrapper entirely and builds the result at the REPRESENTATION level, from the
# operands' underlying character lists (`⟨(force a).data ++ (force b).data⟩`). The
# other two positives keep a `String`-level `++` and differ only in control flow;
# this one changes what the result term is MADE of, which is the deepest reshape
# available on this carrier. Measured: the frozen proof body still closes it (the
# representation-level append and `String` `++` are definitionally equal, so
# `cases a <;> cases b <;> rfl` discharges all four goals) — so the case is
# recorded as re-checking a genuinely different term, NOT as needing a new script.
# CORRECTED BY AUDIT. Two further reshapes were probed, and the earlier text
# claimed they "also verify under the frozen body". Re-measured, they do NOT:
# building the result by folding the right operand's characters onto the left with
# `String.push`, and the double-reverse route
# (`⟨((force b).data.reverse ++ (force a).data.reverse).reverse⟩`), each fail under
# `cases a <;> cases b <;> rfl` (exit 1, `Tactic `rfl` failed: ... is not
# definitionally equal to ...`). Both ARE provable with a bespoke tactic body
# (measured, exit 0 — a `foldl` induction lemma resp. representation unfolding),
# so the spec ADMITS them and neither is a SPEC-TOO-STRONG hole; the frozen script
# simply is not universal. Neither is shipped: they add no sub-domain this case
# does not already cover, and a case whose only distinction is needing a longer
# tactic tests the script rather than the spec. If this
# case FAILED => SPEC-TOO-STRONG (the spec tied to the frozen impl's
# representation rather than its observable result).
_POS_REPR = """\
def implementation_lazyConcat (a b : Operand) : String :=
  ⟨(force a).data ++ (force b).data⟩"""


# admiss-ground: the ADMISSIBILITY positive (see the header). Keeps the frozen impl
# untouched and PREPENDS three ground `have`s to the frozen tactic body, one per
# code path the modeled change is about, each discharged by `decide` on concrete
# literals — so the obligation is exhibited as SATISFIED at concrete F2P-shaped
# operand pairs before being closed verbatim in general. If this FAILED, the
# modeled behavior would be unsatisfiable at exactly a normal input (the total-
# carrier analogue of PRECOND-TOO-STRONG) and every other positive here would be
# closing the obligation vacuously. Nothing is assumed: no new declaration, no new
# axiom, statement byte-identical, `variant_problems` == [] (measured).
_ADMISS_GROUND = """\
  have _ground_deferred_left :
      problem_spec_lazyConcat (.deferred "lazy") (.concrete "!")
        (implementation_lazyConcat (.deferred "lazy") (.concrete "!")) := by
    unfold problem_spec_lazyConcat implementation_lazyConcat
    decide
  have _ground_deferred_right :
      problem_spec_lazyConcat (.concrete "value: ") (.deferred "lazy")
        (implementation_lazyConcat (.concrete "value: ") (.deferred "lazy")) := by
    unfold problem_spec_lazyConcat implementation_lazyConcat
    decide
  have _ground_both_deferred :
      problem_spec_lazyConcat (.deferred "4") (.deferred "5")
        (implementation_lazyConcat (.deferred "4") (.deferred "5")) := by
    unfold problem_spec_lazyConcat implementation_lazyConcat
    decide
"""


def _proof_prefix(extra):
    """Solution.lean variant with `extra` prepended to the frozen tactic body.

    The impl and the obligation STATEMENT are untouched; only the tactic body
    grows, which `variant_scope` permits.
    """
    return _swap(_BASE, _PROOF, extra + _PROOF)


# ===========================================================================
# UNIQUENESS / ORDER RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each carries a witness (validated: elaborates on rival, fails on gold).
# ===========================================================================

# weak-swap-order: returns the WRONG operand order — `force b ++ force a` instead
# of `force a ++ force b`. Elements match as a multiset; only the ORDER differs.
# This is the port of BOTH nagini order-swap rivals (weak-swap-order-fwd/-rev):
# on this carrier the two directions collapse into the one clause, so a single
# rival that flips the concatenation attacks the load-bearing order in every
# branch. Witness at (deferred "X", concrete "Y") — the branch where the left
# operand is on-demand: gold gives "XY", the rival gives "YX".
_SWAP = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s =>
      return force b ++ s
  | .concrete s =>
      match b with
      | .deferred t =>
          return t ++ s
      | .concrete t =>
          return t ++ s"""

_W_SWAP = """\
example : ¬ problem_spec_lazyConcat (.deferred "X") (.concrete "Y")
    (implementation_lazyConcat (.deferred "X") (.concrete "Y")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-drop-last-other: PARTIAL-DOMAIN / off-by-one. Copies the left forced text
# in full, then appends the right forced text MINUS its last character
# (`.dropRight 1`). Correct only when the right operand's text is empty; wrong for
# every non-empty right operand — the result is one character short. Port of
# nagini's weak-drop-last-other-fwd (drop other's trailing element). Witness at
# (concrete "P", deferred "QR") — the concrete-left / on-demand-right branch: gold
# gives "PQR", the rival gives "PQ". The right operand is deliberately TWO
# characters: at a one-character right operand `.dropRight 1` empties the slot and
# the refutation would be indistinguishable from weak-drop-right's (whole slot
# lost), attesting to the wrong sub-domain. At two characters the rival still emits
# part of the right operand, so the witness pins the TRAILING-CHARACTER clause this
# case's rationale claims. This ALSO varies the operand tags oppositely to the swap
# witness, so the concrete-left branch is probed here.
_DROP_LAST = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s =>
      return s ++ (force b).dropRight 1
  | .concrete s =>
      match b with
      | .deferred t =>
          return s ++ t.dropRight 1
      | .concrete t =>
          return s ++ t.dropRight 1"""

_W_DROP_LAST = """\
example : ¬ problem_spec_lazyConcat (.concrete "P") (.deferred "QR")
    (implementation_lazyConcat (.concrete "P") (.deferred "QR")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-drop-left: drops the LEFT operand entirely — returns `force b` alone. This
# is the port of nagini's operand-dropping family aimed at the first operand slot:
# a rival that ignores `force a` verifies only when the left forced text is empty.
# Witness at (deferred "M", deferred "N") — the BOTH-on-demand combination, the
# one operand-tag pairing the other three witnesses do not cover: gold gives "MN",
# the rival gives "N". Distinct sub-domain from weak-drop-last (that one keeps the
# left operand and truncates the right; this one discards the left), so the two
# do not share a witness.
_DROP_LEFT = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  return force b"""

_W_DROP_LEFT = """\
example : ¬ problem_spec_lazyConcat (.deferred "M") (.deferred "N")
    (implementation_lazyConcat (.deferred "M") (.deferred "N")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-empty: collapses EVERY operand pair to the empty text unconditionally.
# Correct only when both operands' forced texts are empty; wrong for every
# non-empty case. Port of nagini's weak-empty-fwd. Witness at (concrete "A",
# concrete "B") — the all-concrete pair, which is the strongest choice available
# for THIS rival precisely because that pair is the one an on-demand-only failure
# would leave alone: a rival that collapses even there is over-broad relative to
# the modeled change, and the spec must still reject it. NOTE this rival is
# therefore NOT the faithful pre-change image (it breaks the always-worked
# all-concrete path too); the faithful pre-change image is the separate
# weak-unforced-deferred case below, which keeps that path exactly right.
_EMPTY = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  return \"\""""

_W_EMPTY = """\
example : ¬ problem_spec_lazyConcat (.concrete "A") (.concrete "B")
    (implementation_lazyConcat (.concrete "A") (.concrete "B")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-unforced-deferred: the FAITHFUL pre-change image, and a BRANCH-SELECTIVE
# rival. It never forces an on-demand operand — it substitutes the empty text for
# one — while the all-concrete path stays byte-for-byte correct. That is exactly the
# pre-change observable: only the paths involving an on-demand operand are wrong,
# and the path that always worked keeps working (which is why the always-worked
# concatenation cases are preserved across the change and the on-demand ones are
# not). Distinct sub-domain from weak-empty (which collapses all four branches):
# this one is CORRECT on one branch, so it is the rival that catches a spec which
# pinned only the all-concrete path. Witness at (deferred "M", concrete "N") —
# on-demand LEFT operand, where gold gives "MN" and the rival gives "N".
_UNFORCED = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  let fa := match a with | .concrete s => s | .deferred _ => ""
  let fb := match b with | .concrete t => t | .deferred _ => ""
  return fa ++ fb"""

_W_UNFORCED = """\
example : ¬ problem_spec_lazyConcat (.deferred "M") (.concrete "N")
    (implementation_lazyConcat (.deferred "M") (.concrete "N")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-branch-both-deferred: the sharpest BRANCH-SELECTIVE rival — correct in
# THREE of the four concrete/deferred combinations, wrong only when BOTH operands
# are on-demand (there it drops the right operand). Every other rival in this
# battery is uniformly wrong across branches, so without this case "a rival that
# mishandled only one branch is caught" would be an undemonstrated claim. Witness
# at (deferred "M", deferred "N") — the both-on-demand pair: gold "MN", rival "M".
_BRANCH = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s =>
      match b with
      | .deferred _ => return s
      | .concrete t => return s ++ t
  | .concrete s =>
      return s ++ force b"""

_W_BRANCH = """\
example : ¬ problem_spec_lazyConcat (.deferred "M") (.deferred "N")
    (implementation_lazyConcat (.deferred "M") (.deferred "N")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-drop-right: discards the RIGHT operand — returns `force a` alone. The exact
# mirror of weak-drop-left, which the port shipped for the left slot only; without
# this the claim "no operand position is left unprobed" holds for one slot only.
# Witness at (concrete "A", deferred "B"): gold "AB", rival "A".
_DROP_RIGHT = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  return force a"""

_W_DROP_RIGHT = """\
example : ¬ problem_spec_lazyConcat (.concrete "A") (.deferred "B")
    (implementation_lazyConcat (.concrete "A") (.deferred "B")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-dup-right: emits the right operand TWICE (`force a ++ force b ++ force b`).
# A SUPERSET of the required text — every other rival here either reorders content
# or loses it, so a spec that only bounded the result from below (e.g. pinned the
# required text as a prefix/substring rather than as an equality) would admit this
# one. Witness at (concrete "A", deferred "B"): gold "AB", rival "ABB".
_DUP_RIGHT = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  return force a ++ force b ++ force b"""

_W_DUP_RIGHT = """\
example : ¬ problem_spec_lazyConcat (.concrete "A") (.deferred "B")
    (implementation_lazyConcat (.concrete "A") (.deferred "B")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-drop-first-left: off-by-one on the LEFT slot (`(force a).drop 1`). Added by
# audit: every truncation rival here attacked the RIGHT slot
# (weak-drop-last-other), so "an off-by-one is caught" was demonstrated for one
# operand position only — the same asymmetry weak-drop-right closed for whole-slot
# loss, one level finer. Correct only when the left text is empty. Witness at
# (concrete "PQ", deferred "R") with a TWO-character LEFT operand for the same
# reason weak-drop-last-other uses a two-character right one: at one character
# `.drop 1` empties the slot and the refutation would restate weak-drop-left's.
# Gold gives "PQR", the rival gives "QR" — a leading character short, and provably
# not the whole slot.
_DROP_FIRST_LEFT = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  return (force a).drop 1 ++ force b"""

_W_DROP_FIRST_LEFT = """\
example : ¬ problem_spec_lazyConcat (.concrete "PQ") (.deferred "R")
    (implementation_lazyConcat (.concrete "PQ") (.deferred "R")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""

# weak-swap-only-concrete: the COMPLEMENT of weak-branch-both-deferred. It is
# correct on all three paths involving an on-demand operand and wrong ONLY on the
# all-concrete path, where it inverts the operand order. Added by audit: the
# battery's branch-selective rivals were all wrong on an on-demand path and right
# on the all-concrete one, so a spec that pinned only the on-demand paths — the
# obvious way to over-fit a spec to the modeled change — was unattacked from this
# side. It is also the strictest possible test that the always-worked path stays
# pinned: unlike weak-empty it breaks that path and NOTHING else. Witness at
# (concrete "A", concrete "B"): gold "AB", rival "BA".
_SWAP_ONLY_CONCRETE = """\
def implementation_lazyConcat (a b : Operand) : String := Id.run do
  match a with
  | .deferred s => return s ++ force b
  | .concrete s =>
      match b with
      | .deferred t => return s ++ t
      | .concrete t => return t ++ s"""

_W_SWAP_ONLY_CONCRETE = """\
example : ¬ problem_spec_lazyConcat (.concrete "A") (.concrete "B")
    (implementation_lazyConcat (.concrete "A") (.concrete "B")) := by
  unfold problem_spec_lazyConcat implementation_lazyConcat
  decide
"""


SPEC_TESTS = [
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DIRECT),
        "rationale": (
            "structurally-different CORRECT impl: no case analysis, returns "
            "`force a ++ force b` directly. Keeps the load-bearing clause "
            "`result = force a ++ force b` and is re-closed by the frozen proof "
            "body (both sides reduce definitionally). If it FAILED => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected). Port of nagini's "
            "pos-cached-bound positive control, re-expressed for this carrier."
        ),
    },
    {
        "id": "pos-matchb",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_MATCHB),
        "rationale": (
            "correct impl that scrutinises the RIGHT operand first (frozen impl "
            "scrutinises the left). Same result on every pair; different "
            "control-flow shape. Reproven by the frozen `cases a <;> cases b <;> "
            "rfl`. Confirms the spec depends only on the forced values and their "
            "order, not on branch structure. If it FAILED => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-repr-shift",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REPR),
        "rationale": (
            "the DEEPEST correct reshape this carrier admits: drops the `Id.run "
            "do`/`return` wrapper and builds the result at the representation "
            "level from the operands' underlying character lists "
            "(`⟨(force a).data ++ (force b).data⟩`), rather than with a "
            "`String`-level `++` as both other positives do. Observably the same "
            "String on every operand pair. The frozen proof body closes it "
            "unchanged (measured): the representation-level append is "
            "definitionally equal to `String` `++`, so no new tactic is needed and "
            "the case carries none. Its value is that the impl TERM is built "
            "differently — pos-direct and pos-matchb only vary control flow. If it "
            "FAILED => SPEC-TOO-STRONG (the spec tied to the frozen impl's "
            "representation rather than to its observable result)."
        ),
    },
    {
        "id": "admiss-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof_prefix(_ADMISS_GROUND),
        "rationale": (
            "ADMISSIBILITY: the obligation is exhibited as SATISFIABLE at "
            "concrete F2P-shaped inputs, not merely closed in general. Three "
            "ground `have`s — one per code path the modeled change covers "
            "(on-demand left operand, on-demand right operand, both on-demand) — "
            "discharge `problem_spec_lazyConcat` by `decide` on concrete string "
            "literals, and only then is the frozen obligation closed verbatim. "
            "On this total carrier there is no precondition to admit, so the "
            "PRECOND-TOO-STRONG analogue is the obligation being unsatisfiable at "
            "exactly a normal input: a universally-quantified spec can still be "
            "vacuous at the pairs the change is about, and then every positive "
            "here would attest to nothing. Because each `have` is decided on "
            "literals, its success positively exhibits a satisfying result at "
            "that pair rather than appealing to the universal statement. If it "
            "FAILED => the modeled behavior is unsatisfiable at an F2P-shaped "
            "input. Nothing is assumed: no new declaration or axiom, statement "
            "byte-identical, impl untouched, `variant_problems` == []."
        ),
    },
    {
        "id": "weak-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP),
        "refinement": (
            "returns `force b ++ force a` (the operands swapped). Its faithful "
            "real counterpart is a concatenation operator that combines the forced "
            "value with the other operand in the reverse of the source order. For "
            "the failing test that concatenates a concrete text with an on-demand "
            "one, such an operator emits the reversed text (the on-demand value "
            "placed before the concrete prefix instead of after), so the asserted "
            "result — the two texts in source order — is not produced and the test "
            "does NOT resolve. A verifying swap rival would be a genuine "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the sole clause `result = force a ++ force b`: the rival "
            "proves `result = force b ++ force a`, which differs whenever the two "
            "forced texts are not equal (any distinct non-empty operands). The "
            "elements match as a multiset but the ORDER does not — the precise "
            "content the two added operators exist to pin. If it verifies => "
            "SPEC-TOO-WEAK (operand order unpinned)."
        ),
        "witness": _W_SWAP,
    },
    {
        "id": "weak-drop-last-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_LAST),
        "refinement": (
            "off-by-one: appends the right operand's forced text minus its final "
            "character. Its faithful real counterpart builds the concatenation "
            "from a truncated slice of the right operand (equivalently a loop "
            "bound short by one), dropping its trailing character. The failing "
            "test that expects the full concatenation of a prefix with an "
            "on-demand text loses that text's last character, so the asserted "
            "result is one character short and the test does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the rival proves "
            "`result = force a ++ (force b).dropRight 1`, which is one character "
            "short of the required text for every non-empty right operand. If it "
            "verifies => SPEC-TOO-WEAK on the trailing-character sub-domain."
        ),
        "witness": _W_DROP_LAST,
    },
    {
        "id": "weak-drop-left",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_LEFT),
        "refinement": (
            "discards the LEFT operand — returns the right operand's forced text "
            "alone. Its faithful real counterpart is a concatenation operator that "
            "ignores one of its two operands and returns only the other, omitting "
            "the combination entirely. The failing test that concatenates two "
            "non-empty texts loses the entire left operand, so the asserted joined "
            "result is not produced and the test does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the rival proves "
            "`result = force b`, which drops the `force a` prefix whenever the "
            "left operand's forced text is non-empty. Distinct sub-domain from "
            "weak-drop-last-other (that keeps the left operand and truncates the "
            "right). If it verifies => SPEC-TOO-WEAK (left operand unpinned)."
        ),
        "witness": _W_DROP_LEFT,
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTY),
        "refinement": (
            "returns the empty text for EVERY operand pair. Its faithful real "
            "counterpart is a combining helper that swallows the concatenation and "
            "yields an empty result unconditionally — including for the pairs of "
            "ordinary concrete values that concatenate correctly both before and "
            "after the change. Those always-worked concatenations are asserted by "
            "tests that must keep passing, so this rival breaks them as well as "
            "the on-demand ones and does NOT resolve. It is an over-broad "
            "near-miss, deliberately kept because the spec must reject a collapse "
            "even on the branch no part of the modeled change touches; the "
            "faithful pre-change image is weak-unforced-deferred, which leaves "
            "that branch exactly right."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the empty string equals "
            "the concatenation only when both forced texts are empty; for any "
            "non-empty operand it fails. Witnessed at the all-concrete pair, so "
            "the refutation is attributed to the branch this rival breaks that the "
            "pre-change image did not. If it verifies => SPEC-TOO-WEAK."
        ),
        "witness": _W_EMPTY,
    },
    {
        "id": "weak-unforced-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNFORCED),
        "refinement": (
            "the FAITHFUL pre-change image and a BRANCH-SELECTIVE rival: it never "
            "forces an on-demand operand (substituting the empty text for one) "
            "while keeping the all-concrete concatenation byte-for-byte correct. "
            "That is precisely the pre-change observable — the paths involving an "
            "on-demand operand produce an empty result, and the path that always "
            "worked keeps working. Its faithful real counterpart is the unchanged "
            "code, which yields an empty text for exactly the failing tests' "
            "inputs while the always-worked concatenation tests still pass. Does "
            "NOT resolve; this is the behaviour the change exists to correct."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the rival proves the "
            "result is the concatenation of the operands' texts with any on-demand "
            "operand replaced by the empty text, which differs from the required "
            "text whenever an on-demand operand's text is non-empty. Because it is "
            "CORRECT on the all-concrete branch, it is the rival that catches a "
            "spec pinning only that branch — a sub-domain weak-empty (wrong "
            "everywhere) cannot isolate. If it verifies => SPEC-TOO-WEAK on the "
            "forcing of an on-demand operand."
        ),
        "witness": _W_UNFORCED,
    },
    {
        "id": "weak-branch-both-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BRANCH),
        "refinement": (
            "correct in THREE of the four concrete/deferred combinations and wrong "
            "only when BOTH operands are on-demand, where it drops the right one. "
            "Its faithful real counterpart is an operator pair that handles the "
            "mixed concrete/on-demand cases correctly but mishandles the case where "
            "the operand it is handed is itself an on-demand value, returning only "
            "the forced left text. The failing test that combines two on-demand "
            "values loses the second, so the asserted joined result is not produced "
            "and that test does NOT resolve, while the other cases still pass — the "
            "hardest near-miss to catch, since only one branch is observably wrong."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: at the both-on-demand pair "
            "the rival proves `result = force a`, dropping `force b`. Every other "
            "rival here is uniformly wrong across branches, so this case is what "
            "makes the battery's branch-coverage claim demonstrated rather than "
            "asserted. If it verifies => SPEC-TOO-WEAK on the both-on-demand "
            "branch (a spec that pinned only the mixed and all-concrete paths)."
        ),
        "witness": _W_BRANCH,
    },
    {
        "id": "weak-drop-right",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_RIGHT),
        "refinement": (
            "discards the RIGHT operand — returns the left operand's forced text "
            "alone; the exact mirror of weak-drop-left. Its faithful real "
            "counterpart is a concatenation operator that returns its forced value "
            "and silently ignores the operand handed to it. The failing test that "
            "joins a prefix with an on-demand text loses that text entirely, so "
            "the asserted result is not produced and the test does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the rival proves "
            "`result = force a`, dropping the `force b` suffix whenever the right "
            "operand's forced text is non-empty. Pairs with weak-drop-left so BOTH "
            "operand slots are independently shown to be pinned, rather than the "
            "left slot only. If it verifies => SPEC-TOO-WEAK (right operand "
            "unpinned)."
        ),
        "witness": _W_DROP_RIGHT,
    },
    {
        "id": "weak-drop-first-left",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_FIRST_LEFT),
        "refinement": (
            "off-by-one on the LEFT operand: copies its forced text minus its "
            "FIRST character, then appends the right operand in full. Its faithful "
            "real counterpart builds the concatenation from a slice of the left "
            "operand that starts one position in, dropping its leading character. "
            "The failing test that expects a prefix joined to an on-demand text "
            "loses that prefix's first character, so the asserted result is one "
            "character short and the test does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the rival proves "
            "`result = (force a).drop 1 ++ force b`, one character short for every "
            "non-empty left operand. Pairs with weak-drop-last-other so the "
            "off-by-one class is probed on BOTH operand slots rather than the "
            "right one only — the finer-grained analogue of the "
            "weak-drop-left/weak-drop-right pairing. Witnessed at a TWO-character "
            "left operand so the refutation pins the LEADING-CHARACTER sub-domain "
            "and is not indistinguishable from whole-slot loss. If it verifies => "
            "SPEC-TOO-WEAK on the leading-character sub-domain."
        ),
        "witness": _W_DROP_FIRST_LEFT,
    },
    {
        "id": "weak-swap-only-concrete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP_ONLY_CONCRETE),
        "refinement": (
            "correct on all three paths where an operand is on-demand, and wrong "
            "ONLY on the all-concrete path, where it inverts the operand order. "
            "Its faithful real counterpart handles the on-demand operands exactly "
            "as required but reverses ordinary concatenation of two plain values. "
            "The always-worked concatenations are asserted by tests that must keep "
            "passing, and this rival reverses their result, so those tests do NOT "
            "resolve even though every on-demand case is correct."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: at the all-concrete pair "
            "the rival proves `result = force b ++ force a`. This is the exact "
            "COMPLEMENT of weak-branch-both-deferred — every other "
            "branch-selective rival here is wrong on an on-demand path and correct "
            "on the all-concrete one, so a spec over-fitted to pin ONLY the "
            "on-demand paths (the natural way to over-fit to the modeled change) "
            "was unattacked from this side. Unlike weak-empty it breaks the "
            "always-worked path and nothing else, making it the strictest test "
            "that that path is still pinned. If it verifies => SPEC-TOO-WEAK on "
            "the all-concrete branch."
        ),
        "witness": _W_SWAP_ONLY_CONCRETE,
    },
    {
        "id": "weak-dup-right",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DUP_RIGHT),
        "refinement": (
            "emits the right operand's forced text TWICE. Its faithful real "
            "counterpart is an operator that appends the other operand once more "
            "after the combination (a duplicated append), producing more text than "
            "asked for. The failing test asserts an exact joined result, so a "
            "result with the second operand repeated is not equal to it and the "
            "test does NOT resolve."
        ),
        "rationale": (
            "REJECTED by `result = force a ++ force b`: the rival proves "
            "`result = force a ++ force b ++ force b`, which differs whenever the "
            "right operand's forced text is non-empty. This is the only rival here "
            "that produces a SUPERSET of the required text — the others reorder or "
            "lose content — so it is what shows the clause is an EQUALITY and not a "
            "lower bound: a spec that merely required the correct text to appear as "
            "a prefix or substring would admit this rival. If it verifies => "
            "SPEC-TOO-WEAK (result bounded below only)."
        ),
        "witness": _W_DUP_RIGHT,
    },
]

# The axiom lane is G-AX's job; the frozen `axioms` region declares no
# `opaque`/`axiom` callee (forcing an on-demand operand is modeled DIRECTLY by
# `force`), so there is nothing for this gate's axiom lane to execute.
AXIOM_TESTS = []
