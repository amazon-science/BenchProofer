"""properties.py — G-PBT falsification battery for django__django-12143 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for a case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — so ``markers.same_spec`` holds and the
``theorem correct_rowKeySelection`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

DEFENDED SURFACE (one total function; one obligation):

    rowKeySelection {α}
        (mark pkName : List Char) (items : List (List Char × α)) : List α

  and the single postcondition clause

    result = (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)

  The carrier is FULLY TRANSPARENT: no ``opaque`` callee, no ``axiom``
  (meta.json ``axioms == []``), and the qualification decision is spelled out in
  the frozen ``pure`` region over the input characters. Every witness below is
  therefore stated at literal inputs and closed by ``decide`` — no witness has
  to condition on the carrier, so none of them binds a hypothesis whose
  satisfiability would need arguing.

  Separately attackable components folded into that one equation:

    * WHICH PAIRS QUALIFY — the per-key decision. Four independent parts of it
      are attackable from the implementation region even though the decision
      predicate itself is frozen spec: whether the marker must occur verbatim at
      the front of the key (attacked in BOTH directions, under-accepting and
      over-accepting, by the two metacharacter rivals), whether the marker is
      required at all (weak-marker-not-required), whether the rest of the
      key shape is required at all (weak-select-every-pair, which also carries
      the pkName binder), and whether the row-index run and the field name must
      be SEPARATED (weak-second-separator-not-required, added by audit — a
      load-bearing conjunct that the marker rivals hold fixed).
    * MULTIPLICITY — EXACTLY one output entry per qualifying pair. Attacked in
      BOTH directions: weak-keep-first-qualifying-only selects a qualifying pair
      and then stops (under-counting), and weak-duplicate-each-qualifying emits
      each qualifying payload twice (over-counting, added by audit). One
      direction alone would leave a spec pinning only "at least the qualifying
      payloads, in order" passing the battery.
    * VALUE + ORDER — carried through unchanged, in submission order. The value
      type is an arbitrary ``α`` with no operations available, so an
      implementation cannot fabricate, inspect, or transform a value: the only
      degrees of freedom left over the payload are which pairs contribute and
      how many times. Multiplicity is attacked above; on ORDER see the OMITTED
      list below.

ADVERSARIAL READ of the nagini classes on this carrier (nagini/properties.py is
the design document; its rivals are expressed over a per-key boolean, this
bundle's obligation is the whole selection over an ordered pair list):

  * FRAME / PERMISSION MUTATION (nagini's mandatory class — three of its ten
    cases: two on the headline function's read-only inputs and one on a
    verified-helper input) — VACUOUS here as a PERMISSION attack. Lean is
    referentially transparent: ``mark``, ``pkName`` and ``items`` are immutable
    values, there is no fractional permission to violate and no aliasing through
    which a rival could normalise an input in place. No substitute is
    fabricated. The SEMANTIC residue of that obligation — "the read-only inputs
    are not silently reshaped into the answer" — survives as the spec's own
    pass-through of the payloads and their order, which the multiplicity rival
    attacks directly.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for exactly the reason the nagini sibling
    records: the decision is not an opaque answer key but a spelled-out function
    of the inputs, so an implementation that returns the spec's own expression is
    the cheapest CORRECT implementation rather than a wrong echo. Ported as the
    honest positive control ``pos-filter-map-direct`` (nagini's
    ``pos-control-echo-grounded``).

  * THE REAL DEFECT (nagini's ``real-bug-dollar-anchor``) — APPLIES and is the
    headline rival, ported in BOTH of its faces. The earlier code assembled the
    row-key pattern by splicing the marker into a pattern language without
    neutralising its metacharacters, so a marker that is not plain text stopped
    matching itself. One face under-accepts (a marker carrying the
    end-of-input metacharacter rejects every key that continues past it:
    ``weak-marker-endanchor-honoured``, the pre-patch skeleton this bundle
    already ships as ``Solution_prepatch.lean``), the other over-accepts (a
    marker character standing for "any single character" is honoured as such:
    ``weak-marker-wildcard-honoured``). Both have the SAME faithful real patch —
    the unfixed pattern construction — and that patch fails the F2P observable,
    so each is a genuine verify-does-not-imply-resolve rival; they are refuted at
    different inputs because they are wrong on disjoint sub-domains.

  * PARTIAL-DOMAIN / dropped-conjunct rivals — nagini ships three
    (``partial-drop-label``, ``partial-drop-digits``, ``partial-drop-hyphen2``).
    Only the first is ported, as ``weak-marker-not-required``; see OMITTED for
    the other two and the reason, which is about the F2P observable and NOT
    about difficulty.

  * DIVERGENCE / NON-TERMINATION — the nagini sibling ships no case in this
    class (its ten cases are three frame-mutation, four decision rivals, two
    positives and one admissibility), so there is nothing to port. On this
    backend the class is in any case genuinely vacuous, and vacuous in the strong
    sense rather than the ``the corpus-wide termination-semantics finding`` sense: the
    implementation is a total Lean ``def``, so a diverging implementation cannot
    be written at all — this is NOT the velvet ``partial``-semantics spec hole,
    which admits a diverging rival that verifies.

  * AXIOM LANE — nagini carries two AXIOM_TESTS over its deep-model reference.
    Dropped by instruction: the axiom lane is G-AX's job and this gate ignores
    ``AXIOM_TESTS``. (For the record, this bundle's G-AX is a skip — no consumed
    axiom — and the deep model is differential-tested by G-CONF: 120,004 cases,
    0 mismatches.)

OMITTED nagini cases, and why (a dropped case is a known gap; a case that passes
for the wrong reason is a corrupt artifact):

  * ``frame-mutation-key``, ``frame-mutation-prefix``, ``helper-frame-mutation``
    — the whole permission class, vacuous on a referentially transparent
    carrier as argued above. Nagini's third case additionally attacks a
    verified-helper surface (``match_literal``) that this bundle does not model
    at all: the Lean-family bundle contracts only the selection, so there is no
    helper obligation to attack.

  * ``partial-drop-hyphen2`` — NOW PORTED, as
    ``weak-second-separator-not-required`` (added by audit). The port's original
    reason for dropping it was that a rival LOOSENING the second separator (a
    pattern accepting any single character there) over-accepts on a sub-domain no
    observable reaches, so its non-resolution argument would be unsupported. That
    reasoning is sound for the loosening realisation but does not cover the
    OMITTING one: a rival that drops the separator from the required shape
    entirely under-accepts, and it under-accepts on exactly the keys every
    observable submits (``<marker>-<index>-<field>``), so the F2P assertion on the
    selected row count and both PASS_TO_PASS row-key observables fail. The
    non-resolution argument holds on the observables, so the case ships.

  * ``partial-drop-digits`` — still DROPPED, and for the reason the port gives,
    which the audit re-derived rather than accepted. The clause is refutable here
    (a rival treating the row-index run as optional is discriminated at
    ``('f--u', 7)``, and a rival restricting the run to the Latin digits is
    discriminated at a non-Latin decimal digit — both were built and both
    rejected). But every faithful real patch of either shape LOOSENS or narrows
    the row-index sub-pattern in a direction no observable sees: every key the
    FAIL_TO_PASS and PASS_TO_PASS submissions carry has a non-empty plain-ASCII
    row index, so those patches still resolve. Shipping them would attach a
    refinement claim this instance's tests do not support. Recorded as a gap: the
    spec is STRONGER than the tests observe on the digit-class and non-emptiness
    sub-clauses, which is correct for a faithful model of the matcher but leaves
    them unattacked here. The same reasoning covers the end-anchor's
    one-trailing-newline tolerance (no observable submits a key ending in a line
    break); a rival dropping it was likewise built and rejected.

  * The ORDER component of the postcondition, for the same reason — the spec
    pins submission order, but every consumer observable in this instance is
    order-insensitive (the selected values are compared as a sorted collection
    or used as a set-membership filter), so an order-reversing rival's faithful
    real patch still resolves. Not attacked; recorded as a gap.

  * ``admissibility-f2p`` — ported in SPIRIT, not mechanically. Nagini's case
    exists because its contract has a real precondition (fractional-permission
    requirements on three list inputs) that could reject a normal submitted key.
    The frozen obligation here is unconditional — ``∀ (mark pkName : List Char)
    (items : List (List Char × α))``, no hypothesis binder — so
    PRECOND-TOO-STRONG has no way to manifest as a rejected call. What survives
    is the other half of nagini's assertion: that the contract is actually
    satisfied at the concrete input the changed behavior is observed on. That is
    shipped as ``admiss-real-submission``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script's ``have h2 : … := rfl`` mirrors
the frozen loop's elaboration exactly), so a rejection alone attributes nothing
to the spec. Every ``expect="reject"`` case therefore carries a Lean snippet
stating the spec predicate at ONE concrete input, checked in a file with the
frozen obligation removed. Each was built by hand against the rival (must
elaborate) and against the frozen solution (must fail) before shipping.

BINDER COVERAGE. Every input binder of ``problem_spec_rowKeySelection`` is moved
by the reject witnesses; no binder is held at one value across all of them.
  * ``mark`` — ``['f','$']`` (metacharacter, end-of-input face), ``['f','.']``
    (metacharacter, wildcard face), ``['f','o']`` (plain, two characters) and
    ``['f']`` (plain, one character). Both the metacharacter/plain axis and the
    length axis move.
  * ``pkName`` — ``['u']`` for the marker-facing rivals and ``['i','d']`` for
    the multiplicity and select-every rivals, so the field-name segment is not
    pinned to one value. The select-every witness is stated at a key whose row
    tail names a DIFFERENT field, which is what makes that witness turn on
    ``pkName`` specifically rather than on the marker.
  * ``items`` — varied in length (one pair, two pairs), in which pairs qualify
    (all / none / the first only), and in key shape (marker present verbatim,
    marker absent, marker over-matched, field name wrong, second separator
    absent).
  * ``α`` and the payloads — instantiated at ``Nat`` with distinct values
    (``7``, ``3``, ``1``/``2``, ``5``) so the selected payload is never
    confusable with a default.
``pts`` = 7 distinct input points across 7 reject cases. Six are pairwise
distinct; the two audit-added rivals are refuted at points that differ from every
other witness in the key's shape or in the expected multiplicity, and the
duplicate rival's point is the only one where the spec and rival agree on WHICH
pairs qualify and disagree only on HOW MANY entries result. No two rivals share a
witness, because each is wrong on a different sub-domain and a shared witness
would claim a sub-domain the manifest never demonstrates.
"""
from pathlib import Path

INSTANCE = "django__django-12143"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_rowKeySelection {α : Type}\n"
    "    (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do\n"
    "  let mut acc : List α := []\n"
    "  for kv in items do\n"
    "    if matchesRowKey mark pkName kv.1 then\n"
    "      acc := acc ++ [kv.2]\n"
    "  return acc\n"
)

_PROOF_BODY = (
    "  intro mark pkName items\n"
    "  unfold problem_spec_rowKeySelection implementation_rowKeySelection\n"
    "  have helper : ∀ (xs : List (List Char × α)) (acc : List α),\n"
    "      Id.run (forIn xs acc (fun kv r =>\n"
    "        (if matchesRowKey mark pkName kv.1 = true\n"
    "          then ForInStep.yield (r ++ [kv.2])\n"
    "          else ForInStep.yield r : Id (ForInStep (List α))))) =\n"
    "        acc ++ (xs.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2) := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro acc; simp [Id.run, List.forIn_nil, pure]\n"
    "    | cons a as ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      by_cases h : matchesRowKey mark pkName a.1 = true\n"
    "      · simp only [h, if_true, List.filter_cons, List.map_cons, ih, List.append_assoc,\n"
    "          List.singleton_append]\n"
    "      · simp only [if_neg h, List.filter_cons, ih]\n"
    "  have h2 : (do\n"
    "      let r ←\n"
    "        forIn items ([] : List α) fun kv r =>\n"
    "            if matchesRowKey mark pkName kv.1 = true then do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield (r ++ [kv.2]))\n"
    "            else do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield r)\n"
    "      pure r : Id (List α)) =\n"
    "      Id.run (forIn items ([] : List α) (fun kv r =>\n"
    "        (if matchesRowKey mark pkName kv.1 = true\n"
    "          then ForInStep.yield (r ++ [kv.2])\n"
    "          else ForInStep.yield r : Id (ForInStep (List α))))) := rfl\n"
    "  show Id.run _ = _\n"
    "  rw [h2, helper]\n"
    "  simp [Id.run]\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """A full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


def _impl_proof(body, proof):
    """A full variant with BOTH the impl body and the tactic body replaced.

    Only for positives that legitimately re-prove: the frozen script mirrors the
    frozen loop's elaboration (`have h2 : … := rfl`), so a reshaped
    implementation needs its own proof of the SAME, byte-identical obligation.
    """
    return _swap(_impl(body), _PROOF_BODY, proof)


_LOOP_HEAD = (
    "def implementation_rowKeySelection {α : Type}\n"
    "    (mark pkName : List Char) (items : List (List Char × α)) : List α := Id.run do\n"
    "  let mut acc : List α := []\n"
    "  for kv in items do\n"
)
_LOOP_TAIL = "  return acc\n"


def _loop(cond, prelude=""):
    """A rival that keeps the frozen traversal and changes only the per-pair
    acceptance test (or, with `prelude`, adds an implementation-region helper)."""
    return (prelude + _LOOP_HEAD
            + f"    if {cond} then\n"
            + "      acc := acc ++ [kv.2]\n"
            + _LOOP_TAIL)


# ---------------------------------------------------------------------------
# Rival implementations. Each is a full impl region; the spec and the theorem
# STATEMENT are untouched, so a rejection is attributable to the postcondition.
# ---------------------------------------------------------------------------

# (1) THE PRE-PATCH SKELETON, under-accepting face. A marker carrying the
# matching engine's end-of-input metacharacter demands the key STOP there, so
# every key that continues past the marker with a well-formed row tail is
# wrongly passed over. On markers made of plain text it coincides with the
# frozen decision, which is what makes it a genuine sub-domain rival rather than
# a blanket refusal. This is the shape this bundle already ships as
# Solution_prepatch.lean, re-expressed inside the traversal.
_MARK_ENDANCHOR = _loop(
    "(!(mark.contains '$')) && matchesRowKey mark pkName kv.1")

# (2) THE PRE-PATCH SKELETON, over-accepting face. A marker character that
# stands for "any single character" in the pattern language is honoured as such
# instead of as ordinary text, so keys whose front merely has the right SHAPE as
# the marker qualify. The helper compares the marker against the key's front
# character-for-character EXCEPT at those positions; the rest of the row shape is
# then required exactly as the frozen decision requires it (the front actually
# present in the key is fed in as the marker, so only the tail is constrained).
_MARK_WILDCARD_HELPER = (
    "/-- Rival helper: compare the marker against the front of the key, treating\n"
    "a marker character that denotes \"any single character\" in the pattern\n"
    "language as matching whatever stands in that position. -/\n"
    "def markerFrontLoose (mark key : List Char) : Bool :=\n"
    "  mark.length ≤ key.length &&\n"
    "    (mark.zip (key.take mark.length)).all (fun p => p.1 == '.' || p.1 == p.2)\n"
    "\n"
)
_MARK_WILDCARD = _loop(
    "markerFrontLoose mark kv.1 && matchesRowKey (kv.1.take mark.length) pkName kv.1",
    prelude=_MARK_WILDCARD_HELPER)

# (3) THE MARKER IS NOT REQUIRED AT ALL. The leading marker segment is simply
# absent from the required shape: a key qualifies as soon as it begins with a
# separator, a row-index run, a separator and the field name. Correct on no
# submission that carries a marker; wrong on every key whose row tail is right
# and whose front is not the marker.
_MARK_NOT_REQUIRED = _loop("matchesRowKey [] pkName kv.1")

# (4) MULTIPLICITY: keep the FIRST qualifying pair and stop. Every selected
# value is one the spec also selects, in the right order — the divergence is
# purely in how many qualifying pairs survive.
_FIRST_ONLY = _loop("acc.isEmpty && matchesRowKey mark pkName kv.1")

# (5) NO PER-KEY TEST AT ALL: every submitted pair contributes its value, so the
# result is the whole payload column in order. Attacks the qualification clause
# wholesale, in the direction of accepting a pair whose key names a different
# field entirely.
_SELECT_EVERY = (_LOOP_HEAD
                 + "    acc := acc ++ [kv.2]\n"
                 + _LOOP_TAIL)

# (6) THE SECOND SEPARATOR IS NOT REQUIRED. The field name is expected to follow
# the row-index run immediately, with nothing between them. The marker is still
# matched verbatim and the row index is still a non-empty decimal run, so this is
# wrong on exactly the sub-domain where the two segments are separated: it
# rejects every key of the specified shape while accepting a differently
# separated one. Added by audit: the second separator is a load-bearing conjunct
# of the frozen decision that no other rival here moves.
_SEP2_HELPER = (
    "/-- Rival helper: the field name is expected to follow the row-index run\n"
    "immediately, with no separator between them. -/\n"
    "def matchesNoSep2 (mark pkName key : List Char) : Bool :=\n"
    "  match stripPrefix? mark key with\n"
    "  | none => false\n"
    "  | some r1 =>\n"
    "    match r1 with\n"
    "    | '-' :: r2 =>\n"
    "      let ds := r2.takeWhile isDecimalDigit\n"
    "      let rest := r2.dropWhile isDecimalDigit\n"
    "      match stripPrefix? pkName rest with\n"
    "      | some tail => !ds.isEmpty && atEnd tail\n"
    "      | none => false\n"
    "    | _ => false\n"
    "\n"
)
_NO_SEP2 = _loop("matchesNoSep2 mark pkName kv.1", prelude=_SEP2_HELPER)

# (7) MULTIPLICITY, the OVER-counting direction. Every qualifying pair
# contributes its payload TWICE. The decision is untouched and the order is
# untouched, so this is wrong only in how many times a qualifying pair is
# counted — the mirror of the keep-first rival, which under-counts. Added by
# audit: the battery attacked multiplicity in one direction only, and a spec
# pinning "at least the qualifying payloads, in order" would admit this.
_DUPLICATE_EACH = _loop("matchesRowKey mark pkName kv.1")
_DUPLICATE_EACH = _DUPLICATE_EACH.replace(
    "      acc := acc ++ [kv.2]\n", "      acc := acc ++ [kv.2, kv.2]\n", 1)


# ---------------------------------------------------------------------------
# Positive controls. Structurally different CORRECT implementations that MUST
# verify; each re-proves the SAME, byte-identical obligation with no helper
# lemma, no new declaration, and no assumption token.
# ---------------------------------------------------------------------------

# (P1) The cheapest honest implementation: the decision is a spelled-out
# function of the inputs, so producing the selection directly — no accumulator,
# no traversal state — is CORRECT, not an echo of an answer key. Proof: both
# sides are the same term once the two definitions are unfolded.
_POS_DIRECT = (
    "def implementation_rowKeySelection {α : Type}\n"
    "    (mark pkName : List Char) (items : List (List Char × α)) : List α :=\n"
    "  (items.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2)\n"
)
_POS_DIRECT_PROOF = (
    "  intro mark pkName items\n"
    "  unfold problem_spec_rowKeySelection implementation_rowKeySelection\n"
    "  rfl\n"
)

# (P2) A different traversal of the same accumulation: a left fold over the
# pairs instead of the imperative loop. Same value on every input; the frozen
# script cannot close it (it is stated over the loop's `forIn` elaboration), so
# the obligation is re-proved by induction on the pair list with the accumulator
# generalized — the same route the frozen proof takes, one layer shallower.
_POS_FOLDL = (
    "def implementation_rowKeySelection {α : Type}\n"
    "    (mark pkName : List Char) (items : List (List Char × α)) : List α :=\n"
    "  items.foldl\n"
    "    (fun acc kv => if matchesRowKey mark pkName kv.1 then acc ++ [kv.2] else acc)\n"
    "    []\n"
)
_POS_FOLDL_PROOF = (
    "  intro mark pkName items\n"
    "  unfold problem_spec_rowKeySelection implementation_rowKeySelection\n"
    "  have helper : ∀ (xs : List (List Char × α)) (acc : List α),\n"
    "      xs.foldl\n"
    "        (fun acc kv => if matchesRowKey mark pkName kv.1 then acc ++ [kv.2] else acc)\n"
    "        acc\n"
    "      = acc ++ (xs.filter (fun kv => matchesRowKey mark pkName kv.1)).map (·.2) := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro acc; simp\n"
    "    | cons a as ih =>\n"
    "      intro acc\n"
    "      by_cases h : matchesRowKey mark pkName a.1 = true\n"
    "      · simp [List.foldl_cons, h, ih]\n"
    "      · simp [List.foldl_cons, h, ih]\n"
    "  simpa using helper items []\n"
)

# (P3) ADMISSIBILITY. The frozen implementation and proof are kept verbatim; the
# proof region additionally states the contract at a concrete submission shaped
# like the one the changed behavior is observed on — a marker that is not plain
# text, one pair whose key qualifies and one whose key names a different field —
# and closes it by computation. The obligation is unconditional (no hypothesis
# binder), so a precondition cannot reject a normal submission here; what this
# checks instead is that the contract is genuinely SATISFIED at that input
# rather than vacuous or wrong there. A failure would be PRECOND-TOO-STRONG in
# the only form this carrier admits.
_ADMISS_PROOF = _PROOF_BODY + (
    "\n"
    "-- The contract at a submission shaped like the observed one: the marker is\n"
    "-- not plain text, the first pair's key carries it verbatim followed by a\n"
    "-- row index and the primary-key field name, the second pair's key names a\n"
    "-- different field. Exactly the first payload is selected.\n"
    "example : problem_spec_rowKeySelection\n"
    "    ['f', '$'] ['u', 'i', 'd']\n"
    "    [(['f', '$', '-', '0', '-', 'u', 'i', 'd'], (4 : Nat)),\n"
    "     (['f', '$', '-', '0', '-', 'l'], (9 : Nat))]\n"
    "    [4] := by\n"
    "  unfold problem_spec_rowKeySelection\n"
    "  decide\n"
)


# ---------------------------------------------------------------------------
# Refutation witnesses. Each states the frozen spec predicate at ONE concrete
# input, over vocabulary the rival and the frozen solution SHARE
# (problem_spec_rowKeySelection / implementation_rowKeySelection only), and is
# closed by computation — the carrier is fully transparent, so no witness needs
# to condition on an opaque term and none binds a hypothesis.
# ---------------------------------------------------------------------------

def _witness(comment, mark, pkname, items):
    return (comment
            + "example : ¬ problem_spec_rowKeySelection\n"
            + f"    {mark} {pkname}\n"
            + f"    {items}\n"
            + "    (implementation_rowKeySelection\n"
            + f"      {mark} {pkname} {items}) := by\n"
            + "  unfold problem_spec_rowKeySelection implementation_rowKeySelection\n"
            + "  decide\n")


_W_ENDANCHOR = _witness(
    "-- The marker carries the end-of-input metacharacter and the key continues\n"
    "-- past it with a well-formed row tail: the marker IS present verbatim at\n"
    "-- the front, so the pair qualifies and its payload must be selected. The\n"
    "-- rival selects nothing.\n",
    "['f', '$']", "['u']", "[(['f', '$', '-', '0', '-', 'u'], (7 : Nat))]")

_W_WILDCARD = _witness(
    "-- The marker carries the single-character wildcard metacharacter and the\n"
    "-- key does NOT carry that character verbatim: the marker is absent from\n"
    "-- the front of the key, so nothing qualifies. The rival selects the pair\n"
    "-- because the front has the right shape.\n",
    "['f', '.']", "['u']", "[(['f', 'X', '-', '0', '-', 'u'], (7 : Nat))]")

_W_NOT_REQUIRED = _witness(
    "-- The key's row tail is well formed but its front is not the marker (the\n"
    "-- key begins at the separator), so nothing qualifies. The rival selects\n"
    "-- the pair, having dropped the marker from the required shape.\n",
    "['f', 'o']", "['u']", "[(['-', '7', '-', 'u'], (3 : Nat))]")

_W_FIRST_ONLY = _witness(
    "-- Two pairs qualify, at different row indices; both payloads must be\n"
    "-- selected, in submission order. The rival stops after the first.\n",
    "['f']", "['i', 'd']",
    "[(['f', '-', '1', '-', 'i', 'd'], (1 : Nat)),\n"
    "     (['f', '-', '2', '-', 'i', 'd'], (2 : Nat))]")

_W_NO_SEP2 = _witness(
    "-- The key carries the marker, a separator, a row index, a separator and\n"
    "-- then the field name — the specified shape exactly — so the pair\n"
    "-- qualifies and its payload must be selected. The rival, which expects the\n"
    "-- field name to abut the row index, selects nothing.\n",
    "['f']", "['i', 'd']", "[(['f', '-', '1', '-', 'i', 'd'], (7 : Nat))]")

_W_DUPLICATE = _witness(
    "-- One pair qualifies, so exactly one payload must be selected. The rival\n"
    "-- selects it twice: same decision, same order, wrong multiplicity.\n",
    "['f']", "['u']", "[(['f', '-', '1', '-', 'u'], (7 : Nat))]")

_W_SELECT_EVERY = _witness(
    "-- The key carries the marker, a separator, a row index and a separator,\n"
    "-- but the field name that closes it is NOT the primary-key field name, so\n"
    "-- the pair does not qualify and nothing is selected. The rival selects it\n"
    "-- anyway, applying no test at all.\n",
    "['f']", "['i', 'd']", "[(['f', '-', '1', '-', 'x'], (5 : Nat))]")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS positives — a correct implementation MUST satisfy the frozen
    # obligation. A rejection here is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-filter-map-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_DIRECT, _POS_DIRECT_PROOF),
        "rationale": (
            "the qualification decision is a spelled-out function of the inputs, "
            "not an opaque answer key, so producing the selection directly — "
            "keep the qualifying pairs, then take their payloads — is the "
            "CHEAPEST CORRECT implementation rather than a wrong echo (this is "
            "the port of nagini's grounded-echo positive, and the reason no "
            "ungrounded-echo rival exists on either carrier). It has no "
            "accumulator and no traversal state, so the frozen script (stated "
            "over the loop's elaboration) cannot close it; the obligation is "
            "re-proved, byte-identical statement, by unfolding the two "
            "definitions, after which both sides are the same term. If this "
            "cannot verify the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-foldl-traversal",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_FOLDL, _POS_FOLDL_PROOF),
        "rationale": (
            "a structurally different but CORRECT traversal: a left fold over "
            "the submitted pairs, threading the same accumulator the frozen loop "
            "mutates and extending it with a payload exactly when the pair "
            "qualifies. Same value on every input, including the empty "
            "submission and submissions where no pair qualifies. The frozen "
            "script is stated over the loop's `forIn` elaboration and cannot "
            "close this shape, so the SAME obligation is re-proved by induction "
            "on the pair list with the accumulator generalized — no helper "
            "lemma, no new declaration, no assumption token. A rejection would "
            "be SPEC-TOO-STRONG: it would mean the postcondition pins the "
            "traversal's internal shape rather than the selection it computes."
        ),
    },
    {
        "id": "admiss-real-submission",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the frozen implementation and proof are kept verbatim and the proof "
            "region additionally states the contract at a submission shaped like "
            "the one the changed behavior is observed on: a marker that is not "
            "plain text, one pair whose key carries that marker verbatim ahead "
            "of a row index and the primary-key field name, and one pair whose "
            "key names a different field — with exactly the first payload "
            "selected, closed by computation. This is the spirit of nagini's "
            "admissibility case on a carrier whose obligation is UNCONDITIONAL "
            "(`∀ mark pkName items`, no hypothesis binder): there is no "
            "precondition that could reject a normal submission, so what is "
            "checked is that the contract is genuinely satisfied at that "
            "concrete input rather than vacuous or wrong there. A failure is "
            "PRECOND-TOO-STRONG in the only form this carrier admits."
        ),
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong implementations sharing the frozen spec, each
    # with (a) the refinement argument that its faithful real patch would NOT
    # resolve, and (b) a witness refuting it at one concrete input.
    # =====================================================================
    {
        "id": "weak-marker-endanchor-honoured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MARK_ENDANCHOR),
        "refinement": (
            "this is the PRE-PATCH behavior — the shape this bundle already "
            "ships as Solution_prepatch.lean, re-expressed inside the "
            "traversal. Its faithful real patch is the unfixed code: the marker "
            "is spliced into the matcher's pattern language as pattern syntax "
            "rather than as ordinary text, so a marker carrying the "
            "end-of-input metacharacter demands the key stop at the marker and "
            "no key that continues past it can ever qualify. The FAIL_TO_PASS "
            "observable is exactly this input — a submission whose marker is "
            "not plain text, with one editable row — and under that patch the "
            "row's key is passed over, so the edited row is not selected and "
            "the assertion that one row was selected fails (nothing is "
            "selected). It does NOT resolve; this is the headline "
            "verify-does-not-imply-resolve rival."
        ),
        "rationale": (
            "REJECT from the qualification clause: the spec requires every "
            "character of `mark` to occur verbatim at the front of the key and "
            "gives the marker no meaning of its own, so a key that carries the "
            "marker followed by a separator, a row-index run, a separator and "
            "the field name QUALIFIES no matter what characters the marker is "
            "made of. At `mark = ['f','$']`, `pkName = ['u']` and the single "
            "pair `('f$-0-u', 7)` the spec selects `[7]` while the rival "
            "selects `[]`. Refuted on the sub-domain where the marker is not "
            "plain text — the sub-domain the rival gets wrong and the only one "
            "where it differs from the frozen decision at all. If it verified, "
            "the spec would admit the pre-patch behavior => SPEC-TOO-WEAK."
        ),
        "witness": _W_ENDANCHOR,
    },
    {
        "id": "weak-marker-wildcard-honoured",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MARK_WILDCARD),
        "refinement": (
            "the same unfixed pattern construction as the rival above, caught on "
            "its OTHER face: where that one wrongly rejects, this one wrongly "
            "accepts. With the marker spliced in as pattern syntax, a marker "
            "character that denotes \"any single character\" matches whatever "
            "stands in that position, so keys whose front merely has the right "
            "SHAPE as the marker are selected — including keys belonging to a "
            "different form whose marker happens to agree elsewhere. Its "
            "faithful real patch is therefore the same unfixed code, which "
            "fails the FAIL_TO_PASS observable for the reason given on the "
            "endanchor rival (that submission's marker carries a "
            "metacharacter, and under the unfixed construction the editable "
            "row's key is passed over, selecting nothing where one row must be "
            "selected). Beyond that observable, the over-accepting face is a "
            "data-integrity fault in its own right: payloads from keys the form "
            "never submitted are fed to the consumer as though they were this "
            "form's primary keys. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same qualification clause, opposite direction: the "
            "spec's marker match is literal in BOTH directions — a key whose "
            "front differs from the marker in even one character does not "
            "qualify, whatever that character is. At `mark = ['f','.']`, "
            "`pkName = ['u']` and the pair `('fX-0-u', 7)` the spec selects "
            "`[]` (the marker's second character is not present) while the "
            "rival selects `[7]`. A DIFFERENT sub-domain and a different input "
            "from the endanchor rival — that one is refuted where the frozen "
            "decision says YES and the rival says no, this one where the frozen "
            "decision says NO and the rival says yes — so the two do not share "
            "a witness. If it verified, the spec would let the marker carry "
            "meaning of its own => SPEC-TOO-WEAK."
        ),
        "witness": _W_WILDCARD,
    },
    {
        "id": "weak-marker-not-required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_MARK_NOT_REQUIRED),
        "refinement": (
            "the port of nagini's dropped-label rival: the leading marker "
            "segment is absent from the required shape, so a key qualifies on "
            "its row tail alone. Its faithful real patch drops the marker from "
            "the assembled pattern while leaving the match anchored at the "
            "start of the key, which is what the surrounding code does — so the "
            "only keys that qualify are those beginning with a separator. No "
            "key any of this instance's tests submits begins with a separator: "
            "the FAIL_TO_PASS observable selects nothing where one row must be "
            "selected, and the PASS_TO_PASS check that three editable rows' "
            "primary keys are returned gets none of them. It does NOT resolve. "
            "(A loosened-anchoring realisation instead selects keys belonging "
            "to any other form with the same field name, miscounting edited "
            "rows across forms — wrong in the other direction, and the reason "
            "the spec pins the marker rather than only the tail.)"
        ),
        "rationale": (
            "REJECT from the marker component of the qualification clause, at a "
            "sub-domain neither metacharacter rival reaches: here the marker is "
            "PLAIN TEXT (`['f','o']`) and the rival is still wrong, because it "
            "never looks at the marker at all. At `pkName = ['u']` and the pair "
            "`('-7-u', 3)` the spec selects `[]` — the marker does not occur at "
            "the front of that key — while the rival selects `[3]`. This is the "
            "witness that moves the `mark` binder off the metacharacter axis "
            "entirely and varies its length, so a rival that mishandled only "
            "plain markers could not slip past. If it verified, the spec would "
            "pin the row tail but not the form the row belongs to => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _W_NOT_REQUIRED,
    },
    {
        "id": "weak-keep-first-qualifying-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FIRST_ONLY),
        "refinement": (
            "attacks MULTIPLICITY rather than the decision: every payload this "
            "rival selects is one the spec also selects, in the right order — "
            "it just stops after the first qualifying pair. Its faithful real "
            "patch returns the first matching submitted value instead of all of "
            "them (a first-match lookup in place of the collection "
            "comprehension). The PASS_TO_PASS check that the primary keys of "
            "THREE edited rows are returned then gets one, so the returned "
            "collection no longer equals the three expected keys and that test "
            "fails; a patch that fails a PASS_TO_PASS observable does not "
            "resolve the instance. It also silently drops every edited row but "
            "one, which is the data-loss failure mode this instance exists to "
            "close."
        ),
        "rationale": (
            "REJECT from the multiplicity component: the spec is an equality "
            "against a FILTER, so it pins one output entry per qualifying pair, "
            "not merely that every selected payload qualifies. At `mark = "
            "['f']`, `pkName = ['i','d']` and two qualifying pairs at row "
            "indices 1 and 2 the spec demands `[1, 2]` while the rival returns "
            "`[1]`. Refuted on the sub-domain that pins multiplicity — a "
            "submission with MORE THAN ONE editable row, which no other witness "
            "here carries — and at a `pkName` distinct from the "
            "marker-facing witnesses. If it verified, the spec would be "
            "satisfied by a sound-but-incomplete selection => SPEC-TOO-WEAK."
        ),
        "witness": _W_FIRST_ONLY,
    },
    {
        "id": "weak-select-every-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SELECT_EVERY),
        "refinement": (
            "no per-key test at all: the whole payload column is returned in "
            "order. Its faithful real patch drops the key test from the "
            "collection comprehension, so every submitted value — the form's "
            "bookkeeping counters, the edited field values, the submit button — "
            "is handed to the consumer as though it were an edited row's primary "
            "key. The FAIL_TO_PASS observable fails: those extra values are not "
            "valid primary-key values, the consumer's validation of the "
            "collection rejects them and it falls back to the unfiltered set of "
            "rows, so the assertion that exactly one row was selected sees the "
            "whole table instead. The PASS_TO_PASS check on the returned "
            "primary keys fails too (it gets the bookkeeping values as well). "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the qualification clause in the membership direction: "
            "the spec pins a payload to be present IFF its key qualifies, so a "
            "pair whose key does not qualify must contribute nothing. The "
            "witness turns on `pkName` specifically: at `mark = ['f']` and the "
            "pair `('f-1-x', 5)` the key carries the marker, a separator and a "
            "row index correctly and fails ONLY on the field name that closes "
            "it (`['x']` where `pkName = ['i','d']`), so the spec selects `[]` "
            "while the rival selects `[5]`. That makes this the witness that "
            "exercises the `pkName` binder as the discriminator rather than the "
            "marker. If it verified, the spec would not pin membership at all "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _W_SELECT_EVERY,
    },
    {
        "id": "weak-second-separator-not-required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_SEP2),
        "refinement": (
            "ADDED BY AUDIT. The separator between the row index and the field "
            "name is dropped from the required shape: the field name is expected "
            "to abut the row-index run. Its faithful real patch omits that "
            "separator from the assembled pattern, so a key of the specified "
            "three-part shape no longer qualifies at all. This does NOT resolve, "
            "and unlike the two sub-clause rivals recorded as gaps below it is "
            "refuted in the UNDER-accepting direction, which is the direction "
            "this instance's observables see: the FAIL_TO_PASS submission's "
            "editable row carries its row index between two separators, so under "
            "that patch nothing is selected where exactly one row must be, and "
            "the assertion on the selected row count fails. The PASS_TO_PASS "
            "check that the primary keys of three editable rows are returned "
            "gets none of them, and the PASS_TO_PASS check on a single edited "
            "row's queryset fails the same way. So the non-resolution argument "
            "holds on the observables, not merely on the model."
        ),
        "rationale": (
            "REJECT from the second-separator conjunct of the qualification "
            "clause — a load-bearing part of the frozen decision that no other "
            "rival here moves (the marker rivals hold the row tail fixed, the "
            "multiplicity and select-every rivals do not decompose it). At "
            "`mark = ['f']`, `pkName = ['i','d']` and the pair `('f-1-id', 7)` "
            "the spec selects `[7]`, because that key decomposes as the marker, "
            "a separator, a non-empty digit run, a separator and the field name; "
            "the rival selects `[]`. If it verified, the spec would leave the "
            "row-index/field-name boundary unpinned => SPEC-TOO-WEAK."
        ),
        "witness": _W_NO_SEP2,
    },
    {
        "id": "weak-duplicate-each-qualifying",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DUPLICATE_EACH),
        "refinement": (
            "ADDED BY AUDIT: multiplicity was attacked in the UNDER-counting "
            "direction only (keep-first), so a spec pinning merely 'every "
            "qualifying payload appears, in order' would have passed the "
            "battery. This rival counts each qualifying pair twice. Its faithful "
            "real patch emits one entry per matched key per pass over the "
            "submitted pairs and makes two passes (or appends to the result "
            "inside a doubly-entered branch). The PASS_TO_PASS check that the "
            "returned primary keys of three edited rows equal exactly those "
            "three gets six entries — a collection of length 6 does not equal "
            "the expected 3, so that observable fails and the patch does not "
            "resolve. Downstream it also feeds each edited row's key twice to "
            "the consumer's validation and membership filter."
        ),
        "rationale": (
            "REJECT from the multiplicity component in the OVER-counting "
            "direction: the spec is an equality against a filter-then-map, so "
            "it pins EXACTLY one output entry per qualifying pair — not at "
            "least one. At `mark = ['f']`, `pkName = ['u']` and the single "
            "qualifying pair `('f-1-u', 7)` the spec demands `[7]` while the "
            "rival returns `[7, 7]`. The decision and the order are untouched, "
            "so this isolates multiplicity alone and is the mirror of "
            "weak-keep-first-qualifying-only. If it verified, the spec would be "
            "satisfied by a duplicating selection => SPEC-TOO-WEAK."
        ),
        "witness": _W_DUPLICATE,
    },
]


# The axiom lane belongs to G-AX and this gate ignores AXIOM_TESTS; nagini's two
# cases over its deep-model reference are dropped by instruction. For the record:
# meta.json `axioms == []` (no consumed axiom, G-AX skips), and the deep model of
# the qualification decision is differential-tested against the real matcher by
# G-CONF (120,004 cases, 0 mismatches).
AXIOM_TESTS = []
