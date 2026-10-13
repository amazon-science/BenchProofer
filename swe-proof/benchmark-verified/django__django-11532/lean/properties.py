"""properties.py — G-PBT falsification battery for django__django-11532 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (a STATE TRANSITION, not a pure function):

  hostName (st : NameHolder) (reportedName : String) : NameHolder × String
      result.1.slot = some result.2
      ∧ (∀ stored, st.slot = some stored → result.2 = stored)
      ∧ (st.slot = none → result.2 = aceEncode reportedName)

  ``NameHolder`` is the holder that serves the metadata name; its whole state is
  one storage slot (``slot : Option String``). A request takes the holder and the
  OS-reported local name and returns BOTH the holder afterwards and the name
  served. So the surface has TWO input binders (``st``, ``reportedName``) and TWO
  output components, and the three clauses pin both components at every input:

    1. OCCUPANCY  — the slot is occupied afterwards, by exactly the served name;
    2. REUSE      — an already-occupied slot is served verbatim;
    3. SETTLING   — an unoccupied slot is settled to the ASCII-compatible
                    (Punycode) representation of the reported name.

  WHY THE STATE IS MODELED, since this is the whole point of the surface. The
  holder's slot is not an internal shortcut: callers hold the holder itself and
  read and clear its stored name through it (mapping.md: the slot IS the
  instance attribute the callee writes), so whether a request left a name stored
  is DIRECTLY OBSERVABLE. A holder that serves the right name while leaving its
  slot unoccupied serves only right names and still does not exhibit the
  specified behavior — and that shape, ``(st, aceEncode reportedName)``, is
  precisely what clause 1 exists to refute (``weak-drop-occupancy`` below). A
  value-only reading of this surface cannot express it.

  ``aceEncode : String → String`` is an ``opaque`` carrier (mapping.md: the
  unchanged standard-library IDNA/ACE encoder). The bundle consumes NO ``axiom``
  about it — clause 3 pins the settled name to ``aceEncode reportedName`` and the
  gold impl computes exactly that. The encoder is therefore an opaque TERM we may
  quantify over but cannot compute with.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS AS PERMISSION, LIVE AS STATE. The
    nagini sibling's two input-write attacks (``frame-mutate-platform-name``,
    ``frame-mutate-domain``) exploit fractional permission on a modeled input;
    Lean is referentially transparent, there is no half-permission to violate and
    no aliasing to exploit, so that mechanism has no instance here. What the
    nagini frame cases were REALLY defending — that a request's effect on state
    is exactly the specified one — is expressible here because the state is a
    modeled value, and it is attacked directly by three state-shaped rivals
    (``weak-drop-occupancy``, ``weak-clear-slot``, ``weak-store-other``) rather
    than by a fabricated permission substitute.

  * UNGROUNDED-ORACLE ECHO — the nagini ``weak-witness-constant`` rival serves
    the hard-coded witness ACE constant. Clause 3 pins the settled name to
    ``aceEncode reportedName`` (a function of the INPUT, not an answer-key
    constant), so a constant-serving rival is refutable at an input whose
    encoding differs from the constant. Because ``aceEncode`` is opaque the
    refutation CONDITIONS on the carrier rather than computing it. Ported as
    ``weak-witness-constant``.

  * ARGUMENT-POSITION and RANGE attacks — no nagini analogue; a clause of the
    form ``result = f input`` has exactly three components a rival can perturb
    (drop ``f``, drop ``input``, perturb the ARGUMENT of ``f``). Landed as
    ``weak-casefold-argument`` (encodes a normalized name — the argument is not
    the reported one) and ``weak-fixed-argument`` (encodes a hard-coded name — the
    answer is in ``aceEncode``'s RANGE, so it satisfies "the served name is an
    ASCII-compatible name" and is refuted only by the grounding in the input).

  * PARTIAL-DOMAIN / RAW PASSTHROUGH — the nagini ``weak-raw-passthrough`` rival
    settles the slot to the reported name unchanged (== the pre-patch behavior).
    Refuted wherever the encoding differs from the input, conditioned on the
    carrier. Ported as ``weak-raw-passthrough``.

  * STALE-STATE / RE-ENTRY — new here, no nagini analogue (the nagini surface is
    a pure function). ``weak-always-resettle`` drops the occupancy guard and
    re-settles on every request, so an occupied slot's held name is discarded;
    clause 2 refutes it. This is the mirror of ``weak-drop-occupancy``: one rival
    never writes the slot, the other always writes it, and the spec pins the slot
    exactly between them.

  * DIVERGENCE — a request that never returns a name at all. This bundle sets no
    ``loom.semantics.termination`` option: it is the plain lean backend, so Lean's
    own termination checking is what the verifier discharges, and a rival must
    either carry a decreasing measure or be marked ``partial``. THE CLASS AS SUCH
    IS A KNOWN HOLE HERE, and the reason is a measured dilemma between the only
    two spellings, neither of which yields a witnessed reject case:

      1. TOTAL spelling — a ``def`` whose body is a bare self-call is refused
         outright, ``fail to show termination for implementation_hostName``. The
         file never elaborates, so the FROZEN SPEC IS NEVER CONSULTED: the
         rejection is Lean's definitional well-formedness check, not this
         bundle's obligation, and it would attest to the spec exactly nothing.
         (Recorded because it is easy to mistake for a live obligation: the
         verifier does say no, but to the definition rather than to the claim.)
      2. ``partial`` spelling — ``partial`` DISCHARGES nothing; it removes the
         termination obligation entirely. Measured: adding a ``partial`` diverging
         helper to the frozen impl elaborates with exit 0. And marking the modeled
         function itself ``partial`` makes it opaque to ``unfold``, so the witness
         then fails IDENTICALLY on gold and on the rival (measured: both
         ```simp` made no progress``, both exit 1) — undiscriminating,
         hence unshippable.

    So no rival in this battery is refuted BY a termination obligation, and none
    can be: on this carrier the two spellings are "rejected before the spec is
    read" and "no obligation at all". That is a hole in the SPEC's reach (it
    cannot require a request to terminate), recorded as such rather than papered
    over — a hole says the spec is incomplete, where calling the class vacuous
    would falsely claim the battery is complete.

    What IS shipped, and is a genuinely distinct contribution, is
    ``weak-settle-diverges``: it puts the non-termination in an impl-region helper
    the served name is read from — the shape a retry loop with no progress
    actually takes — so the modeled function still unfolds. It is refuted by the
    VALUE clauses (2 and 3), not by termination, and its interest is the witness
    TECHNIQUE: a served name no tactic can evaluate is still refutable, because
    clause 2 demands one unevaluable term equal two different held names at two
    occupied slots. Its ``kind`` and rationale say exactly that; it is not
    evidence that this bundle rejects divergence.

  A SHAPE DELIBERATELY NOT LANDED AS A REJECT CASE, recorded so its absence is a
  decision rather than an oversight: an impl that skips the encoding for a name
  that is ALREADY plain ASCII (``if reportedName.all (·.val < 128) then store
  reportedName else store (aceEncode reportedName)``). The frozen spec DOES
  reject it (measured: rejected by 9 distinct tactic scripts), because
  ``aceEncode`` is opaque and nothing in the bundle lets a proof conclude
  ``aceEncode s = s`` for an ASCII ``s``. But its faithful real patch WOULD
  resolve the F2P — the real IDNA codec leaves pure-ASCII labels alone — so
  filing it as a uniqueness refutation would assert a false refinement claim.
  It is excluded on that ground, not because the spec fails to reject it.

  A SECOND SHAPE THE SPEC ADMITS, recorded because it is the one place an auditor
  should NOT read a clean reject lane as completeness. An impl may evaluate the
  encoder on a FABRICATED argument and discard the answer — e.g. bind
  ``aceEncode (reportedName ++ 70×"a")`` to an unused local, then behave exactly
  as gold — and it VERIFIES (measured, exit 0). It is not filed as a rival
  (nothing would reject it) and not filed as a spec hole in this lane either: the
  carrier is TOTAL where the real encoder is partial, so in Lean that term denotes
  a string while its faithful transcription raises, and mapping.md's DOMAIN
  RESTRICTION rules such a transcription out of the refinement relation with
  measured numbers. The mirror shape, which PROPAGATES the fabricated argument's
  answer instead of discarding it, IS rejected (measured, exit 1) — so what the
  spec cannot see is exactly the discarded computation. refinement.md records a
  measured successor model (``aceEncode : String → Option String`` with a
  PROPAGATION clause) that closes it structurally, and why landing it here is out
  of scope. Recorded as a known limitation of the carrier, not of this battery.

POSITIVE / ADMISSIBILITY. The nagini positives (``pos-control-acd-reshape``,
``pos-control-chn-direct``) both defend the value clause, which is clause 3 here,
and collapse to ``pos-functional-direct``. They are joined by two positives the
nagini surface has no room for: one that defends the STATE clauses without
mutating the given holder (``pos-fresh-holder``), and one the frozen tactic body
cannot close, so it re-proves the obligation itself (``pos-helper-rederived``).
The nagini admissibility ``admiss-witness-selfcall`` becomes a ground-instance
discharge, at BOTH slot shapes, inside the frozen proof body.

  A NOTE ON WHY NO POSITIVE HERE IS A DEFINITIONAL-EQUALITY FREEBIE, which is the
  usual way a positive on a tactic backend says nothing. The frozen obligation is
  a CONJUNCTION whose second clause is a ``∀`` and whose third is an implication,
  so ``rfl`` cannot close it for ANY impl, gold included: the frozen tactic body
  is a case analysis on the slot followed by ``simp``, not a form-tuned ``rfl``.
  Every variant below therefore re-derives all three clauses from its own impl.
  Measured breadth of that script: it closes the first two positives here, plus a
  dependent-``if`` reshape over ``Option.get`` and a reshape that accumulates the
  served name with a ``for`` loop over the slot's contents — four structurally
  distinct correct impls, none definitionally equal to the frozen one. So a
  rejection below is not the frozen script being brittle.

  And the third positive (``pos-helper-rederived``) is the one that carries the
  weight, because the frozen script does NOT close it: factoring the served name
  through an impl-region helper ``def`` leaves ``simp`` with a constant it will
  not unfold, so that case FAILS with the frozen body (measured: ``unsolved
  goals``) and must supply its own proof. A positive the frozen script happens to
  close can only detect a spec over-fit to a control-flow shape the script
  already normalizes; that one tests the obligation against an impl whose proof
  has to be redone from scratch.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation, so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly, at one concrete (holder, reported-name) point — or, for the
one rival whose served name is unevaluable, at two such points jointly (see
``weak-settle-diverges``). Each was checked to HOLD of its rival and to FAIL on
the frozen solution (so it discriminates rather than asserting a tautology).

  One witness (``weak-settle-diverges``) states its refutation at TWO points at
  once rather than one, and that is forced rather than stylistic: the rival's
  served name is a term no tactic can evaluate, so no single point exhibits a
  disagreement with a computable answer. What the spec still pins is that the
  served name at an occupied slot is THE HELD NAME, so two occupied slots holding
  DIFFERENT names demand two different values of one and the same term. That
  conjunction is refutable without evaluating anything, and it needs no
  hypothesis, hence no satisfiability burden.

  The two STATE rivals whose violation is of clause 1 need NO hypothesis at all:
  ``none = some x`` is false by construction, so those witnesses are
  UNCONDITIONAL (``weak-drop-occupancy``, ``weak-clear-slot``) and carry no
  satisfiability burden. The rivals whose violation is of clause 2 or 3 concern
  the opaque carrier, where no literal input DECIDES the equality, so each
  conditions on the carrier with a single jointly-satisfiable hypothesis
  (``aceEncode <input> ≠ <the rival's answer>``) — the exact sub-domain where the
  rival is wrong. Each such hypothesis was checked to be CONSISTENT (the
  generated ``… : False`` probe does NOT close), so the counterexample input
  genuinely exists.

  WHY THE GOLD-SIDE FAILURE IS EVIDENCE, not just an error. For the conditional
  witnesses the frozen solution fails with an application type mismatch (the
  clause projection has the gold's answer where the rival's answer is expected);
  for the two unconditional witnesses it fails with ``unsolved goals``, because
  on gold the conjunct is TRUE and ``simp`` cannot derive ``False`` from it —
  i.e. gold's build fails for exactly the reason the witness claims of the rival.
  The claim was also FLIPPED (the ``¬`` dropped) and rebuilt on both sides: the
  flipped claim elaborates against the frozen solution and fails against each
  rival, the exact mirror. So the frozen solution's exit code tracks WHAT IS
  CLAIMED at that point in both directions.

  A witness whose conditioning constant contains ``--`` must write those bytes
  as ``\\x2d\\x2d``. The consistency probe is generated by re-parsing the
  witness's binder groups after stripping Lean comments, and a literal ``--``
  inside a string is indistinguishable from a comment to that stripper: the
  binder is truncated, no probe is emitted, and the case silently loses the one
  check that its hypothesis is satisfiable. ``\\x2d\\x2d`` elaborates to the
  identical string (checked) and keeps the probe. See ``weak-witness-constant``.

BINDER COVERAGE. BOTH input binders are varied across the reject witnesses.
The holder binder ``st`` takes both of its shapes — unoccupied (``⟨none⟩``) and
occupied, at two DIFFERENT held names (``⟨some "held-value"⟩``,
``⟨some "cached.example.org"⟩``) — so the reuse path is refuted separately from
the settle path and no rival is refuted only where the slot happens to be empty.
The name binder ``reportedName`` takes the non-ASCII ``"漢"``, the already-ASCII
``"example.com"``, the mixed-case ``"Example.Com"`` and the F2P-shaped ``"漢字"``.
The divergence case adds a THIRD and FOURTH held name (``⟨some "held-a"⟩``,
``⟨some "held-b"⟩``), used TOGETHER, since what it refutes is the demand that one
unevaluable term equal two distinct held names at once. ``weak-reuse-store-encoded``
adds a FIFTH — an occupied slot holding a NON-ASCII name (``⟨some "漢字"⟩``) —
which is the only point in the lane where the held name is not already its own
ACE form, and that is exactly what makes clause 1's agreement half refutable on
the reuse path.
The variation is MEANINGFUL: each point is one where that rival's answer and the
spec's demand provably come apart, and each is a point where a DIFFERENT rival is
correct (raw passthrough is right on ``"example.com"``, case-folding is right on
``"漢"``, and every value-only rival is right at an occupied slot), so no one
point would refute the lane. In particular the two occupied-slot points are NOT
two spellings of one point: the ASCII held names are points where
``weak-reuse-store-encoded`` cannot be refuted at all (storing the encoding of an
already-ASCII name is not observably wrong on this carrier), which is why it needs
its own.
``pts`` = 7 distinct (holder, reported-name) points.

WHICH CLAUSE-AND-PATH CELLS ARE ATTACKED, since "clause 1 is attacked" hides
where. Clause 1 splits into occupancy and stored-vs-served agreement, and each
half is attacked on BOTH paths: occupancy at the settle path
(``weak-drop-occupancy``) and at the reuse path (``weak-clear-slot``); agreement
at the settle path (``weak-store-other``) and at the reuse path
(``weak-reuse-store-encoded``). Clause 2 is attacked by ``weak-always-resettle``,
clause 3 by the four value rivals (``weak-raw-passthrough``,
``weak-witness-constant``, ``weak-casefold-argument``, ``weak-fixed-argument``,
which between them drop the encoder, drop the input, perturb the argument, and
answer inside the encoder's range). No cell of that grid is unattacked.

AXIOM lane: EMPTY. mapping.md records that no ``axiom aceEncode_prop`` is
consumed (``aceEncode`` is declared ``opaque`` only so the encoder can appear in
the executable impl), so there is no axiom-soundness / axiom-containment
obligation for this gate to re-discharge (that lane belongs to G-AX in any case).
AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-11532"

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
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  -- while no metadata name has been settled, settle one: the reported local\n"
    "  -- name's ASCII-compatible representation, and leave it occupying the slot\n"
    "  if holder.slot = none then\n"
    "    holder := { holder with slot := some (aceEncode reportedName) }\n"
    "  -- serve the name the slot now holds\n"
    "  let served := holder.slot.getD (aceEncode reportedName)\n"
    "  return (holder, served)\n"
)

_PROOF_BODY = (
    "  intro st reportedName\n"
    "  unfold problem_spec_hostName implementation_hostName\n"
    "  obtain ⟨slot⟩ := st\n"
    "  cases slot with\n"
    "  | none => simp\n"
    "  | some stored => simp\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Positive-control / admissibility impl+proof bodies.
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct match on the slot with no `Id.run do` / `let mut` / early return, and no
# `Option.getD`: the occupied and unoccupied cases are written out separately.
# Same holder and same served name on every input. Not definitionally equal to
# the frozen impl (nothing here is: the obligation is a conjunction with a `∀`
# and an implication, so `rfl` closes it for no impl at all), so the frozen
# case-analysis-plus-`simp` body genuinely re-derives all three clauses from this
# impl's own shape.
_POS_IMPL = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  match st.slot with\n"
    "  | some stored => (st, stored)\n"
    "  | none => ({ slot := some (aceEncode reportedName) }, aceEncode reportedName)\n"
)

# POSITIVE CONTROL (soundness), SECOND SHAPE — aimed at the STATE clauses. This
# impl never touches the holder it is given: it builds a FRESH holder around the
# name it decided to serve. That is correct (clause 1 is about the slot's CONTENTS
# afterwards, not about which holder value was reused).
#
# CALIBRATED, because the obvious reading over-claims: this is NOT a live
# provenance detector. `NameHolder` has one field, so after case analysis on the
# slot `{st with slot := some n}` and `⟨some n⟩` are `rfl`-equal up to eta
# (measured: `obtain ⟨slot⟩ := st; cases slot <;> rfl` closes the equation between
# the two impls, exit 0). A spec that tried to pin holder provenance therefore
# could not distinguish them either, so no SPEC-TOO-STRONG failure of that kind is
# reachable here. It remains a legitimate positive — bare `rfl` does NOT close the
# equation (measured, exit 1), so the frozen script re-derives all three clauses
# from this shape — it just is not the load-bearing one. See its rationale.
_POS_FRESH_IMPL = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  ({ slot := some (st.slot.getD (aceEncode reportedName)) },\n"
    "   st.slot.getD (aceEncode reportedName))\n"
)

# POSITIVE CONTROL (soundness), THIRD SHAPE — the one the frozen script does NOT
# close, so this case has to re-prove the obligation from scratch. The served name
# is factored out into an impl-region helper `def`, which is an admissible thing
# for a variant to add (variant_scope bans new theorems/axioms, not helper defs)
# and is exactly how a solver would naturally write this. Extensionally identical
# to gold. With the frozen tactic body it FAILS (measured: `unsolved goals` — the
# helper is a constant `simp` will not unfold), so the case supplies its own
# script, which differs from the frozen one only by naming the helper in the
# `unfold`. If a correct impl that merely NAMES an intermediate value cannot
# satisfy the frozen obligation, the spec is SPEC-TOO-STRONG.
_POS_HELPER_IMPL = (
    "def settledName (st : NameHolder) (reportedName : String) : String :=\n"
    "  st.slot.getD (aceEncode reportedName)\n"
    "\n"
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  (⟨some (settledName st reportedName)⟩, settledName st reportedName)\n"
)
_POS_HELPER_PROOF = (
    "  intro st reportedName\n"
    "  unfold problem_spec_hostName implementation_hostName settledName\n"
    "  obtain ⟨slot⟩ := st\n"
    "  cases slot with\n"
    "  | none => simp\n"
    "  | some stored => simp\n"
)

# ADMISSIBILITY: keep the gold impl and PREPEND ground-instance `have`s to the
# frozen tactic body, discharging the spec predicate at BOTH slot shapes before
# the frozen obligation is closed verbatim. Confirms the modeled behavior is
# satisfiable at the normal inputs.
#
# Both shapes are needed, and this is the lane where that matters most: the
# settle instance witnesses that clause 3 can be met, and the reuse instance
# witnesses that clause 2 can be met AT THE SAME TIME as clause 1 — i.e. that
# "serve the held name" and "leave the served name in the slot" are jointly
# satisfiable at an occupied slot, which is the pair of demands the state model
# adds. A settle-only ground instance would leave that untested.
#
# The reported name is the F2P-shaped one specifically: the public
# problem_statement pins the observable at a two-character non-Latin reported
# name, and that is the name used here.
_ADMISS_PROOF = (
    "  have _ground_settle : problem_spec_hostName ⟨none⟩ \"漢字\"\n"
    "      (implementation_hostName ⟨none⟩ \"漢字\") := by\n"
    "    unfold problem_spec_hostName implementation_hostName\n"
    "    simp\n"
    "  have _ground_reuse : problem_spec_hostName ⟨some \"cached.example.org\"⟩ \"漢字\"\n"
    "      (implementation_hostName ⟨some \"cached.example.org\"⟩ \"漢字\") := by\n"
    "    unfold problem_spec_hostName implementation_hostName\n"
    "    simp\n"
    + _PROOF_BODY
)


# ---------------------------------------------------------------------------
# Rival impl bodies (each is a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# DROP-OCCUPANCY — THE RIVAL THIS BATTERY EXISTS FOR. Serve the right name and
# leave the holder EXACTLY as it was: no name is ever settled into the slot. Every
# name it serves is the correct one, so no value-only reading of this surface can
# refute it; clause 1 refutes it immediately, because an unoccupied slot cannot
# equal `some` of anything.
_RIVAL_DROP_OCCUPANCY = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  (st, aceEncode reportedName)\n"
)

# CLEAR-SLOT: serve the right name and then EMPTY the slot. The other half of the
# occupancy attack — this rival does write the slot, it writes `none` — so it
# separates "the slot is written" from "the slot is left holding the served
# name". A held name is served correctly and then thrown away.
_RIVAL_CLEAR_SLOT = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  let served := holder.slot.getD (aceEncode reportedName)\n"
    "  holder := { holder with slot := none }\n"
    "  return (holder, served)\n"
)

# STORE-OTHER: serve the right name but leave a DIFFERENT name occupying the
# slot. The slot is occupied afterwards (so the first half of clause 1 holds) and
# the served name is right (so clauses 2 and 3 are met on the settle path), and it
# is still wrong: the stored name and the served name disagree, so the NEXT
# request would serve something the reported name never produced.
_RIVAL_STORE_OTHER = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  ({ slot := some \"localhost\" }, aceEncode reportedName)\n"
)

# ALWAYS-RESETTLE: drop the occupancy guard and settle on EVERY request, so a
# name already held is discarded and replaced. The mirror of DROP-OCCUPANCY: that
# rival never writes the slot, this one always writes it.
_RIVAL_ALWAYS_RESETTLE = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  holder := { holder with slot := some (aceEncode reportedName) }\n"
    "  let served := holder.slot.getD (aceEncode reportedName)\n"
    "  return (holder, served)\n"
)

# RAW PASSTHROUGH (= the pre-fix behavior): settle the slot to the reported name
# unchanged, with no ASCII-compatible encoding. Correct only on names already
# equal to their own encoding; wrong for a non-ASCII name.
_RIVAL_PASSTHROUGH = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  if holder.slot = none then\n"
    "    holder := { holder with slot := some reportedName }\n"
    "  let served := holder.slot.getD reportedName\n"
    "  return (holder, served)\n"
)

# WITNESS-CONSTANT (ungrounded echo): settle the slot to a hard-coded ASCII
# constant, ignoring the reported name entirely. Correct only on inputs whose
# encoding happens to equal the constant.
_RIVAL_CONSTANT = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  if holder.slot = none then\n"
    "    holder := { holder with slot := some \"xn--p8s937b\" }\n"
    "  let served := holder.slot.getD \"xn--p8s937b\"\n"
    "  return (holder, served)\n"
)

# CASE-FOLDING: settle the slot to the encoding of the LOWERCASED reported name.
# A plausible-looking normalization (host names are compared case-insensitively),
# and wrong: clause 3 pins the settled name to the encoding of the name AS
# REPORTED, and for a mixed-case name the two differ. Attacks the clause's
# ARGUMENT position, which no other rival in this battery touches.
_RIVAL_CASEFOLD = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  if holder.slot = none then\n"
    "    holder := { holder with slot := some (aceEncode reportedName.toLower) }\n"
    "  let served := holder.slot.getD (aceEncode reportedName.toLower)\n"
    "  return (holder, served)\n"
)

# FIXED-ARGUMENT ECHO: apply the real encoding, but to a hard-coded name instead
# of the reported one. Strictly stronger than the constant rival as a probe: its
# answer is in the RANGE of `aceEncode` (so any "the served name must be an
# encoding of something" reading of the spec is satisfied) and it is still wrong,
# because clause 3 pins the settled name to the encoding OF THIS INPUT.
_RIVAL_FIXED_ARG = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String := Id.run do\n"
    "  let mut holder := st\n"
    "  if holder.slot = none then\n"
    "    holder := { holder with slot := some (aceEncode \"example.com\") }\n"
    "  let served := holder.slot.getD (aceEncode \"example.com\")\n"
    "  return (holder, served)\n"
)


# REUSE-STORE-ENCODED: on the REUSE path, serve the held name (correct) but leave
# the slot holding the ENCODING of it. Added by audit: every shipped rival attacks
# clause 1's stored-vs-served agreement at an UNOCCUPIED slot only
# (weak-store-other), and the two occupied-slot rivals attack clause 2 (the served
# name) or clause 1's occupancy half (weak-clear-slot writes `none`). So the
# agreement half AT AN OCCUPIED SLOT — the slot is occupied, by a plausible
# ASCII-compatible name, and the served name is right — was the one corner of the
# state model no rival touched. This rival is also strictly harder than
# weak-store-other in the same way weak-fixed-argument is harder than
# weak-witness-constant: what it stores is in `aceEncode`'s RANGE and is derived
# from the holder's own contents, so it is not refutable as an unrelated constant.
_RIVAL_REUSE_STORE_ENCODED = (
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  match st.slot with\n"
    "  | some stored => (⟨some (aceEncode stored)⟩, stored)\n"
    "  | none => (⟨some (aceEncode reportedName)⟩, aceEncode reportedName)\n"
)


# SETTLE-DIVERGES: the request never returns a name at all. Written as the shape a
# real "retry the settle until it reports something" patch takes — a helper that
# recurses on the encoding of the name it was handed and so never makes progress
# toward a base case. `partial` is the only way to state the rival at all (the
# same self-call as a total `def` is refused outright, `fail to show termination
# for implementation_hostName`) — but note what that means: `partial` REMOVES the
# termination obligation rather than discharging it, so what rejects THIS rival is
# not the termination checker. Measured: the module fails with `unsolved goals /
# case none ⊢ settleUntilHeld reportedName = aceEncode reportedName` and `case
# some ⊢ settleUntilHeld reportedName = stored` — the VALUE clauses. See the
# docstring's DIVERGENCE paragraph for why the termination class itself is a
# recorded hole, and the case's rationale for what this rival does contribute.
#
# The divergence lives in the HELPER, not in `implementation_hostName`. Marking the
# modeled function itself `partial` makes it opaque to `unfold`, so no refutation
# can be stated about it (measured: the witness build fails identically on gold and
# on the rival, i.e. that spelling is undiscriminating). With the helper carrying
# it, the modeled function still unfolds and the served name reduces to the
# unevaluable helper term, which is exactly what the witness needs.
_RIVAL_DIVERGE = (
    "partial def settleUntilHeld (reportedName : String) : String :=\n"
    "  settleUntilHeld (aceEncode reportedName)\n"
    "\n"
    "def implementation_hostName (st : NameHolder) (reportedName : String) :\n"
    "    NameHolder × String :=\n"
    "  let served := settleUntilHeld reportedName\n"
    "  (⟨some served⟩, served)\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_hostName`
    # STATEMENT is byte-identical; the tactic body is unchanged. No helper
    # lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_IMPL),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` "
            "and the `Option.getD`, writing the occupied and unoccupied cases "
            "out as a direct `match` on the slot. It settles the slot to the "
            "reported name's ASCII-compatible representation when empty and "
            "serves the held name otherwise, so it must satisfy all three "
            "clauses; if it cannot, the spec is SPEC-TOO-STRONG (over-fit to the "
            "exact control-flow FORM). Both nagini positives "
            "(pos-control-acd-reshape, pos-control-chn-direct) defend the value "
            "clause, which is clause 3 here. Proof: the frozen body cases on the "
            "slot and `simp` closes each arm — no new declaration, axiom, or "
            "assumption token. This is NOT a definitional-equality freebie: the "
            "obligation is a conjunction whose second clause is a `∀`, so `rfl` "
            "closes it for no impl (gold included) and all three clauses are "
            "re-derived from this impl's own shape."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL, SECOND SHAPE — aimed at the STATE clauses. Returns a
    # FRESH holder rather than updating the given one. This is the case that
    # detects a state model over-fitted to holder provenance instead of slot
    # occupancy.
    # =====================================================================
    {
        "id": "pos-fresh-holder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_FRESH_IMPL),
        "rationale": (
            "a correct impl that never updates the holder it was given: it "
            "decides the name to serve (the held one if the slot is occupied, "
            "otherwise the reported name's ASCII-compatible representation) and "
            "returns a FRESH holder built around it. Extensionally identical to "
            "gold on every input. It must verify, because clause 1 constrains "
            "the slot's CONTENTS afterwards and not which holder value was "
            "reused. Proof: the frozen body, unchanged. What this case does and "
            "does not establish, measured rather than asserted: it is NOT "
            "definitionally equal to gold as written (bare `rfl` on "
            "`implementation_hostName st r = implFresh st r` fails, 'not "
            "definitionally equal'), so the frozen script does re-derive all three "
            "clauses from this shape — but after `obtain ⟨slot⟩ := st` the two ARE "
            "`rfl`-equal (measured: `cases slot <;> rfl` closes it, exit 0), "
            "because `NameHolder` is a single-field structure and so "
            "`{st with slot := some n}` and `⟨some n⟩` agree up to eta. So the "
            "SPEC-TOO-STRONG hole this case would detect — a state model pinning "
            "holder PROVENANCE rather than slot occupancy — cannot exist on this "
            "carrier, and the case cannot fail for that reason. It is kept as an "
            "honest structural positive (a distinct impl shape the frozen script "
            "must close), not advertised as a provenance detector; the substantive "
            "claim that clause 1 pins slot CONTENTS and not holder identity is "
            "true, it is just true definitionally here rather than by the spec's "
            "choice. `pos-helper-rederived` is the positive that carries weight."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL, THIRD SHAPE — the frozen tactic body does NOT close this
    # one, so the case re-proves the obligation itself. This is the positive that
    # can detect SPEC-TOO-STRONG in a way a script-closed reshape cannot.
    # =====================================================================
    {
        "id": "pos-helper-rederived",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_HELPER_IMPL), _PROOF_BODY, _POS_HELPER_PROOF),
        "rationale": (
            "a correct impl that names the served name via an impl-region helper "
            "`def settledName` and builds the result from it — extensionally "
            "identical to gold, and the shape a solver would naturally write. "
            "Admissible: variant_scope bans new `theorem`/`lemma`/`axiom`, not "
            "helper `def`s in the impl region, and the `theorem correct_hostName` "
            "STATEMENT is byte-identical. It is the one positive here that the "
            "FROZEN tactic body cannot close (measured: `unsolved goals`, because "
            "`simp` will not unfold the helper constant), so this case genuinely "
            "re-derives all three clauses; its script differs from the frozen one "
            "only by naming the helper in the `unfold`. No axiom, `sorry`, or "
            "assumption token. If a correct impl that merely NAMES an "
            "intermediate value cannot satisfy the obligation, the spec is "
            "SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — confirms the obligation is SATISFIABLE (non-vacuous) at
    # the normal, F2P-shaped input, at BOTH slot shapes. The frozen theorem
    # carries NO precondition hypothesis (the behavior is total, so `∀` is
    # unguarded), so nagini's precondition-admission probe
    # (admiss-witness-selfcall) has no binder to attack here; the honest
    # analogue is to discharge the spec predicate at ground inputs inside the
    # proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-witness-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P-shaped reported name (the "
            "non-Latin name the public problem_statement states the observable "
            "at) for BOTH slot shapes — an unoccupied slot, where the spec "
            "requires the slot be settled to that name's ASCII-compatible "
            "representation and left holding it, and an occupied slot, where it "
            "requires the held name be served AND still be in the slot "
            "afterwards. Both are `have` ground instances closed by `simp`; then "
            "the frozen obligation is closed verbatim. The occupied instance is "
            "the one that matters for the state model: it shows clauses 1 and 2 "
            "are jointly satisfiable, i.e. that 'serve the held name' and 'leave "
            "the served name in the slot' do not conflict. Verifies (else the "
            "spec is unsatisfiable at the normal inputs, the analogue of "
            "PRECOND-TOO-STRONG). Nothing is assumed: the theorem STATEMENT is "
            "byte-identical, the ground instances are `have`s inside the existing "
            "tactic body, and no new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete (holder,
    # reported-name) point.
    # =====================================================================
    {
        "id": "weak-drop-occupancy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_DROP_OCCUPANCY),
        "refinement": (
            "serving the correctly-encoded name while leaving the holder "
            "untouched is a real, plausible patch: compute the encoded name from "
            "the reported one and return it, with no storage slot written. Every "
            "name it serves is EXACTLY the gold name, so its returned value is "
            "right on the entire domain. It still does NOT resolve: the F2P test "
            "reaches into the holder and CLEARS its stored name (the modeled "
            "slot IS the instance attribute — mapping.md), which requires that a "
            "request left a name stored. Under this patch nothing was ever "
            "stored, so the clearing raises and the test errors before its "
            "assertion is reached. This is the measured verify-not-resolve break "
            "the state model closes: a value-only reading of this surface "
            "verifies this rival with a clean axiom set."
        ),
        "rationale": (
            "REJECT from clause 1 (OCCUPANCY): afterwards the slot must be "
            "occupied by exactly the served name, and this rival returns the "
            "holder it was given. At an unoccupied slot that is `none = some "
            "(aceEncode reportedName)`, false by construction — so the "
            "refutation needs NO hypothesis about the opaque carrier and carries "
            "no satisfiability burden. If it verified => SPEC-TOO-WEAK in the "
            "precise way this bundle was repaired for: the spec would be a claim "
            "about the served value only, and the request's effect on the "
            "holder — the thing the official test observes — would be "
            "unconstrained."
        ),
        "witness": (
            "-- Refuted at an unoccupied slot, unconditionally: the spec demands "
            "the slot\n"
            "-- be occupied by the served name afterwards, and this impl returns "
            "the holder\n"
            "-- it was handed, whose slot is still empty. `none = some _` is "
            "false by\n"
            "-- construction, so no hypothesis about the opaque encoder is "
            "needed (and\n"
            "-- there is nothing here that could fail to be satisfiable).\n"
            "example : ¬ problem_spec_hostName ⟨none⟩ \"漢字\"\n"
            "    (implementation_hostName ⟨none⟩ \"漢字\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro h\n"
            "  simp at h\n"
        ),
    },
    {
        "id": "weak-clear-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_CLEAR_SLOT),
        "refinement": (
            "serving the held name and then clearing the slot is the "
            "'recompute next time' patch: the value returned by THIS request is "
            "right, and the stored name is dropped so the next request settles "
            "again. It does NOT resolve: after the F2P's own call the attribute "
            "is gone, so the test's clearing of the stored name raises exactly "
            "as in the drop-occupancy shape, and every later reader pays the "
            "reported-name lookup again. A verifying rival here would mean the "
            "spec constrains only that the slot be WRITTEN, not what it is left "
            "holding."
        ),
        "rationale": (
            "REJECT from clause 1 (OCCUPANCY), at an OCCUPIED slot — the other "
            "half of the occupancy attack. This rival does write the slot; it "
            "writes `none`. So it separates 'the slot is written' from 'the slot "
            "is left holding the served name'. `none = some \"held-value\"` is "
            "false by construction, so again no carrier hypothesis is needed. "
            "Refuted at a DISTINCT point from every other rival (an occupied "
            "slot holding a name that is not the reported one's encoding). If it "
            "verified => SPEC-TOO-WEAK (occupancy is not actually pinned "
            "AFTERWARDS, only touched)."
        ),
        "witness": (
            "-- Refuted at an OCCUPIED slot, unconditionally: the impl serves the "
            "held\n"
            "-- name (which is right) and then empties the slot, so afterwards "
            "the slot is\n"
            "-- not occupied by the served name — indeed not occupied at all. "
            "`none = some _`\n"
            "-- is false by construction, so no hypothesis about the opaque "
            "encoder is\n"
            "-- needed. Note the served value here is CORRECT: only the state "
            "effect is\n"
            "-- wrong, which is what makes this a state refutation.\n"
            "example : ¬ problem_spec_hostName ⟨some \"held-value\"⟩ "
            "\"example.com\"\n"
            "    (implementation_hostName ⟨some \"held-value\"⟩ \"example.com\") "
            ":= by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro h\n"
            "  simp at h\n"
        ),
    },
    {
        "id": "weak-store-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_STORE_OTHER),
        "refinement": (
            "storing one name while serving another is the 'wrong variable "
            "assigned' patch — the slot is written, and written with a plausible "
            "host name, but not with the name this request served. It does NOT "
            "resolve: the F2P asserts on the metadata name and the stored name "
            "must be the one later requests serve, so the very next reader gets "
            "a name the reported one never produced, and the stamped metadata "
            "stops matching the machine. A verifying rival here would mean the "
            "spec pins occupancy without pinning WHAT occupies the slot."
        ),
        "rationale": (
            "REJECT from the second half of clause 1: the slot must be occupied "
            "by EXACTLY the served name. This rival satisfies everything else — "
            "the slot is occupied afterwards, and the served name is the correct "
            "encoding of the reported name — so it isolates the agreement "
            "between stored and served. Refuted by conditioning on the carrier "
            "(whenever the reported name's encoding is not the hard-coded stored "
            "name). If it verified => SPEC-TOO-WEAK (stored and served could "
            "disagree, and the memoization would be free to serve stale or "
            "invented names)."
        ),
        "witness": (
            "-- Refuted at an unoccupied slot: the impl serves the right name but "
            "leaves a\n"
            "-- hard-coded DIFFERENT name occupying the slot, so the stored name "
            "and the\n"
            "-- served name disagree. The single hypothesis is jointly "
            "satisfiable: the\n"
            "-- encoder is opaque, so nothing forces a non-Latin name's encoding "
            "to be that\n"
            "-- particular ASCII host name (and the real encoder does not make "
            "them equal).\n"
            "example (h : aceEncode \"漢字\" ≠ \"localhost\") :\n"
            "    ¬ problem_spec_hostName ⟨none⟩ \"漢字\"\n"
            "      (implementation_hostName ⟨none⟩ \"漢字\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (Option.some_inj.mp hspec.1).symm\n"
        ),
    },
    {
        "id": "weak-always-resettle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_ALWAYS_RESETTLE),
        "refinement": (
            "dropping the occupancy guard and settling on every request is the "
            "'always recompute' patch. It DOES leave the slot occupied by the "
            "served name, so it satisfies clause 1, and it serves an "
            "ASCII-compatible name every time. It does not exhibit the specified "
            "behavior: a name already settled is discarded and replaced by one "
            "derived from whatever the operating system reports NOW, so the "
            "metadata name is no longer settled once and held — every reader can "
            "get a different name, and the reported-name lookup the holder exists "
            "to avoid happens on every request. A verifying rival here would "
            "mean the spec says nothing about an already-occupied slot."
        ),
        "rationale": (
            "REJECT from clause 2 (REUSE): when the slot was already occupied, "
            "the served name must be the stored one verbatim. This rival "
            "overwrites it. The mirror of weak-drop-occupancy — that rival never "
            "writes the slot, this one always writes it, and the spec pins the "
            "slot exactly between them. Refuted at an OCCUPIED slot holding a "
            "name distinct from every other rival's point, conditioned on the "
            "carrier. If it verified => SPEC-TOO-WEAK (the settle-once behavior "
            "would be unconstrained, and the reported name would keep influencing "
            "the served name forever)."
        ),
        "witness": (
            "-- Refuted at an occupied slot: the spec demands the held name be "
            "served\n"
            "-- verbatim, and this impl re-settles from the reported name "
            "instead. The\n"
            "-- single hypothesis is jointly satisfiable (the encoder is opaque, "
            "so nothing\n"
            "-- forces a non-Latin name's encoding to equal the unrelated ASCII "
            "name the\n"
            "-- slot happens to hold).\n"
            "example (h : aceEncode \"漢字\" ≠ \"cached.example.org\") :\n"
            "    ¬ problem_spec_hostName ⟨some \"cached.example.org\"⟩ \"漢字\"\n"
            "      (implementation_hostName ⟨some \"cached.example.org\"⟩ "
            "\"漢字\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (hspec.2.1 \"cached.example.org\" rfl)\n"
        ),
    },
    {
        "id": "weak-raw-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_PASSTHROUGH),
        "refinement": (
            "settling the slot to the reported name with no encoding is EXACTLY "
            "the pre-patch behavior. For a non-ASCII reported name the settled "
            "metadata name is then the raw non-ASCII string, which cannot be "
            "emitted in a narrow single-byte header encoding — the precise "
            "failure the change removes. A faithful patch doing this FAILS the "
            "F2P observable (the metadata name must be ASCII-compatible), so it "
            "does NOT resolve: a verifying rival here would be "
            "verify-not-resolve."
        ),
        "rationale": (
            "REJECT from clause 3 (SETTLING): at an unoccupied slot the served "
            "name must be the reported name's ASCII-compatible encoding, and "
            "this rival serves the raw name. Refuted by conditioning on the "
            "carrier — whenever `aceEncode reportedName` differs from "
            "`reportedName`, the rival's answer differs from the spec's. If it "
            "verified => SPEC-TOO-WEAK (the encoding is not actually pinned; "
            "identity would satisfy the spec)."
        ),
        "witness": (
            "-- Refuted at a non-ASCII reported name with an unoccupied slot: "
            "whenever its\n"
            "-- ASCII-compatible encoding differs from the name itself (the whole "
            "point of\n"
            "-- the encoding for a non-ASCII label), settling the slot to the raw "
            "name\n"
            "-- contradicts the spec. The single hypothesis is jointly "
            "satisfiable (a\n"
            "-- non-ASCII name is not its own ASCII-compatible form).\n"
            "example (h : aceEncode \"漢\" ≠ \"漢\") :\n"
            "    ¬ problem_spec_hostName ⟨none⟩ \"漢\"\n"
            "      (implementation_hostName ⟨none⟩ \"漢\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (hspec.2.2 rfl).symm\n"
        ),
    },
    {
        "id": "weak-witness-constant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_CONSTANT),
        "refinement": (
            "settling the slot to a hard-coded ASCII constant PASSES only for a "
            "reported name whose encoding equals that constant, and is wrong for "
            "every other name. A faithful patch hard-coding the metadata name "
            "would break the held host name everywhere it is read (the metadata "
            "name must be the encoding of the ACTUAL reported name), so it does "
            "NOT resolve the general behavior — a verifying rival here is a "
            "partial-domain verify-not-resolve break, diverging from the gold "
            "transform on the whole non-matching sub-domain."
        ),
        "rationale": (
            "REJECT from clause 3 (SETTLING): the settled name is pinned to the "
            "encoding OF THE INPUT, not to any constant. At an (already-ASCII) "
            "reported name whose encoding is not the rival's constant, the rival "
            "contradicts the spec. Refuted at a DISTINCT reported name from the "
            "passthrough rival (`\"example.com\"` vs `\"漢\"`). If it verified => "
            "SPEC-TOO-WEAK (value pin hollow / echo-vulnerable)."
        ),
        "witness": (
            "-- Refuted at an already-ASCII reported name distinct from the "
            "one the\n"
            "-- passthrough rival uses: whenever the name's ASCII-compatible "
            "encoding\n"
            "-- differs from the hard-coded constant, settling the slot to that "
            "constant\n"
            "-- contradicts the spec. The single hypothesis is jointly "
            "satisfiable (an\n"
            "-- ordinary ASCII host name does not encode to that particular "
            "constant).\n"
            "--\n"
            "-- The two hyphens of the constant are written \\x2d\\x2d, which "
            "elaborates\n"
            "-- to the identical string (checked by `rfl`). Written literally, "
            "the `--`\n"
            "-- is indistinguishable from a Lean line comment to the "
            "comment-stripping\n"
            "-- pass that re-parses this witness's binder groups to build its "
            "satisfiability\n"
            "-- probe: the binder gets truncated mid-literal, no probe is "
            "emitted, and the\n"
            "-- case loses the check that its hypothesis can hold at all.\n"
            "example (h : aceEncode \"example.com\" ≠ "
            "\"xn\\x2d\\x2dp8s937b\") :\n"
            "    ¬ problem_spec_hostName ⟨none⟩ \"example.com\"\n"
            "      (implementation_hostName ⟨none⟩ \"example.com\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (hspec.2.2 rfl).symm\n"
        ),
    },
    {
        "id": "weak-casefold-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_CASEFOLD),
        "refinement": (
            "lowercasing the reported name before encoding it is a plausible "
            "normalization — host names compare case-insensitively — and it is "
            "NOT what the modeled behavior does: the name that reaches the mail "
            "metadata is the encoding of the name AS REPORTED. A faithful patch "
            "that folded case first would change the settled metadata name for "
            "every mixed-case reported name, so the value read everywhere the "
            "held name is consumed would no longer be the reported name's own "
            "representation: it does NOT resolve, and a verifying rival here "
            "would be verify-not-resolve on the whole mixed-case sub-domain."
        ),
        "rationale": (
            "REJECT from clause 3 (SETTLING): the clause pins the ARGUMENT of "
            "the encoding to the reported name itself, not to any normalization "
            "of it. At a mixed-case reported name whose encoding differs from its "
            "lowercased form's encoding, the rival contradicts the spec. This is "
            "the only rival in the lane that attacks the ARGUMENT position — the "
            "passthrough rival drops the encoding and the "
            "constant/fixed-argument rivals drop the input — so it probes a "
            "clause component the others leave untouched. Refuted at a DISTINCT "
            "reported name (`\"Example.Com\"`). If it verified => SPEC-TOO-WEAK "
            "(the argument of the encoding is not pinned)."
        ),
        "witness": (
            "-- Refuted at a mixed-case reported name: whenever its "
            "ASCII-compatible\n"
            "-- encoding differs from that of its lowercased form, settling the "
            "slot from\n"
            "-- the folded name contradicts the spec (which demands the encoding "
            "of the\n"
            "-- name AS REPORTED). The single hypothesis is jointly satisfiable: "
            "the\n"
            "-- carrier is opaque, so nothing forces it to agree on two distinct "
            "arguments,\n"
            "-- and the two arguments here are distinct strings.\n"
            "example (h : aceEncode \"Example.Com\" ≠ "
            "aceEncode \"Example.Com\".toLower) :\n"
            "    ¬ problem_spec_hostName ⟨none⟩ \"Example.Com\"\n"
            "      (implementation_hostName ⟨none⟩ \"Example.Com\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (hspec.2.2 rfl).symm\n"
        ),
    },
    {
        "id": "weak-fixed-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_FIXED_ARG),
        "refinement": (
            "applying the real ASCII-compatible encoding to a hard-coded name "
            "produces an ASCII-compatible name for every input, so it satisfies "
            "the DEFINING property of the change while still being wrong: the "
            "metadata name no longer tracks the reported name at all. A faithful "
            "patch of this shape would stamp one fixed name into the metadata of "
            "every message regardless of the machine, which is not the behavior "
            "the held name is read for, so it does NOT resolve the general "
            "behavior — verify-not-resolve on every input other than the "
            "hard-coded one."
        ),
        "rationale": (
            "REJECT from clause 3 (SETTLING): the settled name is pinned to the "
            "encoding OF THIS INPUT. This rival is a strictly stronger probe "
            "than `weak-witness-constant` — its answer lies in the RANGE of "
            "`aceEncode`, so it survives any reading of the spec that only "
            "requires the served name to BE an ASCII-compatible name, and it is "
            "refuted only by the clause's grounding in the argument. Refuted at "
            "the F2P-shaped reported name. If it verified => SPEC-TOO-WEAK (the "
            "served name is tied to the carrier but not to the input)."
        ),
        "witness": (
            "-- Refuted at the F2P-shaped non-ASCII reported name: whenever its "
            "encoding\n"
            "-- differs from the encoding of the rival's hard-coded name, the "
            "name settled\n"
            "-- into the slot differs from what the spec demands at that input. "
            "The single\n"
            "-- hypothesis is jointly satisfiable: `aceEncode` is a carrier we "
            "cannot\n"
            "-- compute with, so nothing forces it to agree on the two distinct "
            "arguments\n"
            "-- (and the real encoder does not — it separates a non-Latin name "
            "from an\n"
            "-- ordinary ASCII one).\n"
            "example (h : aceEncode \"漢字\" ≠ aceEncode \"example.com\") :\n"
            "    ¬ problem_spec_hostName ⟨none⟩ \"漢字\"\n"
            "      (implementation_hostName ⟨none⟩ \"漢字\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (hspec.2.2 rfl).symm\n"
        ),
    },
    {
        "id": "weak-reuse-store-encoded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_REUSE_STORE_ENCODED),
        "refinement": (
            "re-normalizing the held name on the way back into the slot is the "
            "'be defensive about what we cached' patch: the name this request "
            "serves is the held one, verbatim and correct, and what the slot is "
            "left holding is an ASCII-compatible name derived from it. It does NOT "
            "resolve. The stored name is what every LATER request serves, so from "
            "the next request onward the metadata name is a name the reported one "
            "never produced, and it drifts further on each request — the held name "
            "stops being the settled-once value that callers read it as. A "
            "verifying rival here would mean the spec pins the agreement between "
            "the stored and the served name only where the slot started empty, "
            "leaving the reuse path free to rewrite what it hands on."
        ),
        "rationale": (
            "REJECT from the second half of clause 1 (the slot must be occupied by "
            "EXACTLY the served name) ON THE REUSE PATH. Added by audit to close "
            "the one corner of the state model no shipped rival reached: "
            "weak-store-other attacks this same agreement half but only at an "
            "UNOCCUPIED slot, weak-clear-slot attacks the occupancy half at an "
            "occupied slot (it stores `none`), and weak-always-resettle attacks "
            "clause 2 (the served name). This rival satisfies clause 2 verbatim "
            "and clause 1's occupancy half, so the rejection is attributable to "
            "the agreement half alone. Strictly harder than weak-store-other in "
            "the way weak-fixed-argument is harder than weak-witness-constant: "
            "what it stores lies in `aceEncode`'s RANGE and is derived from the "
            "holder's own contents, so no 'the slot must hold an ASCII-compatible "
            "name' reading refutes it. Refuted at a DISTINCT point from every "
            "other rival (an occupied slot whose held name is non-ASCII), "
            "conditioned on the carrier. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted at an occupied slot holding a NON-ASCII name: the impl "
            "serves that\n"
            "-- held name (which clause 2 demands, so clause 2 is satisfied) and "
            "leaves the\n"
            "-- slot holding its encoding instead, so the stored and the served "
            "name disagree.\n"
            "-- Note the reported name is an ALREADY-ASCII one and is never "
            "consulted by\n"
            "-- either side here, which is what isolates the reuse path.\n"
            "--\n"
            "-- The single hypothesis is jointly satisfiable: a non-ASCII name is "
            "not its own\n"
            "-- ASCII-compatible form (the same fact weak-raw-passthrough "
            "conditions on, at\n"
            "-- the same kind of name), and the encoder is opaque so nothing can "
            "force them\n"
            "-- equal. Held at a name distinct from every other case's point.\n"
            "example (h : aceEncode \"漢字\" ≠ \"漢字\") :\n"
            "    ¬ problem_spec_hostName ⟨some \"漢字\"⟩ \"example.com\"\n"
            "      (implementation_hostName ⟨some \"漢字\"⟩ \"example.com\") := by\n"
            "  unfold problem_spec_hostName implementation_hostName\n"
            "  intro hspec\n"
            "  exact h (Option.some_inj.mp hspec.1)\n"
        ),
    },
    {
        "id": "weak-settle-diverges",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_DIVERGE),
        "refinement": (
            "retrying the settle until the slot reports a name is a plausible "
            "patch shape — re-encode and go round again — and written this way it "
            "never makes progress toward a base case, so no request ever returns. "
            "It does NOT resolve, and it fails EVERY test rather than only the "
            "F2P: nothing that stamps mail metadata can obtain a name, so the "
            "first reader of the held name hangs instead of being served. A "
            "verifying rival here would mean the obligation says nothing about a "
            "request TERMINATING, i.e. that a specification of what is served "
            "could be met by never serving anything."
        ),
        "rationale": (
            "REJECT from clause 2 (REUSE) and clause 3 (SETTLING), stated over a "
            "served name that is UNEVALUABLE — the shape a non-terminating settle "
            "takes on this carrier. The rejection SOURCE is measured, and it is "
            "worth stating precisely because the obvious reading is wrong: this "
            "rival's module is refused with `unsolved goals / case none ⊢ "
            "settleUntilHeld reportedName = aceEncode reportedName` and `case some "
            "⊢ settleUntilHeld reportedName = stored`, i.e. by the VALUE clauses, "
            "NOT by a termination obligation. The `partial` keyword is what makes "
            "the helper's own termination obligation go away, so once the rival is "
            "statable at all nothing about termination is left for the verifier to "
            "discharge (measured: adding this exact `partial` helper to the frozen "
            "impl elaborates, exit 0, so `partial def` costs the file nothing). "
            "What the case therefore contributes is a distinct WITNESS TECHNIQUE "
            "rather than a distinct rejection source: an impl whose served name no "
            "tactic can evaluate is still refutable, because clause 2 demands that "
            "one and the same unevaluable term equal two DIFFERENT held names at "
            "two occupied slots. That is the only rival in this lane refuted "
            "without any point where a computable answer is compared. Recorded "
            "honestly because the termination class ITSELF is NOT shipped here and "
            "is not shippable: see the docstring's DIVERGENCE paragraph for the "
            "measured reason (the total spelling is refused before the spec is "
            "consulted, and the `partial`-on-the-modeled-function spelling is "
            "undiscriminating). If this rival verified => SPEC-TOO-WEAK: a served "
            "name pinned to nothing evaluable would satisfy clauses 2 and 3."
        ),
        "witness": (
            "-- Refuted at TWO occupied slots AT ONCE, which is forced rather than\n"
            "-- stylistic. The served name here is a term no tactic can evaluate, so\n"
            "-- no single point exhibits a disagreement with a computable answer. What\n"
            "-- clause 2 still pins is that an occupied slot's served name is THE HELD\n"
            "-- NAME, and this impl's served name does not depend on the holder at\n"
            "-- all — so two slots holding DIFFERENT names demand two different values\n"
            "-- of one and the same term. That is refutable without evaluating\n"
            "-- anything, and it needs no hypothesis, so there is nothing here that\n"
            "-- could fail to be satisfiable.\n"
            "--\n"
            "-- Both halves measured. On the rival the projections reduce to the\n"
            "-- concrete pair `settleUntilHeld \"漢字\" = \"held-a\"` and `... =\n"
            "-- \"held-b\"`, and rewriting one into the other closes the goal. On the\n"
            "-- frozen solution the SAME projection is proven outright by `simp` (it\n"
            "-- reduces to `True`, since gold does serve the held name), so there is\n"
            "-- nothing left to rewrite and the build fails. The claim was also\n"
            "-- FLIPPED — the same conjunction asserted POSITIVELY — and rebuilt on\n"
            "-- both sides: it elaborates against the frozen solution and fails\n"
            "-- against the rival, the exact mirror. So gold's exit code tracks what\n"
            "-- is CLAIMED at these points in both directions.\n"
            "example : ¬ (problem_spec_hostName ⟨some \"held-a\"⟩ \"漢字\"\n"
            "        (implementation_hostName ⟨some \"held-a\"⟩ \"漢字\")\n"
            "      ∧ problem_spec_hostName ⟨some \"held-b\"⟩ \"漢字\"\n"
            "        (implementation_hostName ⟨some \"held-b\"⟩ \"漢字\")) := by\n"
            "  intro hspec\n"
            "  have e1 := hspec.1.2.1 \"held-a\" rfl\n"
            "  have e2 := hspec.2.2.1 \"held-b\" rfl\n"
            "  unfold implementation_hostName at e1 e2\n"
            "  simp at e1 e2\n"
            "  simp [e1] at e2\n"
        ),
    },
]


# No consumed axioms and no deep-model references: `aceEncode` is declared
# `opaque` only so the unchanged encoder can appear in the executable impl, and
# the proof discharges the three clauses by case analysis on the slot, so there
# is no in-model axiom obligation for the PBT axiom lane to re-discharge (that
# lane belongs to G-AX).
AXIOM_TESTS = []
