"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9711 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_verifyExtensionVersions``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior, a pure input→output map):

  verifyExtensionVersions (entries : List (String × Option String)) : Option Nat
        result = position of the FIRST entry whose requirement is not met,
                 or none when every present version meets its requirement.

  Each entry is ``(required, present?)``: ``present?`` is ``none`` when nothing
  is loaded (no failure), or ``some v`` for a loaded version string ``v`` (which
  may be the sentinel ``"unknown version"``). An entry is UNMET iff a version is
  present and the required minimum is not satisfied — where satisfaction compares
  the two as VERSIONS (``parseVersion``: era marker, then release components with
  trailing-zero equality, then the pre/revision/development qualifier tags, then
  the build tag) when both are readable as versions, else as raw strings; the
  sentinel always fails.

  ADMITTED DOMAIN. The obligation is guarded by
  ``problem_pre_verifyExtensionVersions``: every version string an entry mentions
  is ASCII text. Everything ASCII is admitted, unreadable strings and the
  sentinel included; the one excluded class, and why the modeled callee is not
  stable there, is stated in the spec's own ``pre-conditions`` region and in
  mapping.md. Every witness below is stated at ASCII literals, so every
  refutation site is inside the admitted domain — a rival refuted only outside it
  would attest to nothing, since the theorem makes no claim there.

  The postcondition is a total case split with THREE independent top-level
  clauses over TWO input binders (``entries`` and, inside the ``some k`` arm, the
  index ``k``):

    (C-none)   result = none  ⟹  every entry is met;
    (C-exists) result = some k ⟹  entry ``k`` is unmet (existence);
    (C-first)  result = some k ⟹  every earlier entry is met (minimality /
               first-ness — the returned index is the FIRST failure, not any).

  No output component is left free: on a met configuration the result must be
  exactly ``none``, and on an unmet one it must be exactly the first failing
  index.

CARRIER NOTE — what reduces on this carrier, MEASURED, not assumed. The version
strings are modeled as Lean ``String``. Two facts about kernel reduction shape
every witness below, and both were measured by building the claim, not reasoned
about:

  - ``parseVersion`` on a LITERAL DOES reduce, but only by ``rfl``, not by
    ``decide``: ``VerKey`` carries no ``DecidableEq`` instance, so
    ``decide`` reports ``failed to synthesize Decidable (parseVersion "3.11" =
    some {...})`` while ``show parseVersion "3.11" = some {...} from by rfl``
    closes. Each witness that needs a parse therefore supplies it as an
    ``rfl``-proved ``show`` rewrite inside the ``simp`` set.
  - ``verGt`` on literal ``VerKey`` VALUES reduces by ``decide`` (the fields are
    ``Nat``/``List Nat``), so the version verdict is dischargeable once the two
    parses are rewrites.
  - ``stringGt`` on literals does NOT reduce by ``decide`` (``String.decidableLT'``
    gets stuck: ``did not reduce to isTrue or isFalse``). It is provable via
    ``simp only [stringGt, decide_eq_true_eq, String.lt_iff_toList_lt]; decide``,
    which is how the two witnesses that need the raw-string order state it.
  - ``entryUnmet`` on a literal SENTINEL or ABSENT entry reduces outright
    (``entryUnmet ("1.0", some "unknown version") = true`` and
    ``entryUnmet ("1.0", none) = false`` both close by ``decide``), and the frozen
    impl reduces at literal entry lists by ``rfl``. So the structural witnesses
    need no hypotheses at all.

Consequently EVERY witness in this battery is stated at LITERAL inputs — no
witness quantifies over an opaque ``req``/``ver`` conditioned by hypothesis. That
is stronger than a conditioned refutation (nothing has to be argued jointly
satisfiable, and the gate's consistency probe has nothing to reject), and it is
only possible because ``parseVersion`` reduces at a literal — an earlier revision
of this bundle modeled the comparison with a helper that did not, which is why its
witnesses had to condition on an opaque string instead.

CARRIER NOTE 2 — the discrimination measurement. Every witness was rebuilt four
ways: against the rival, against the frozen solution, and — as the control that
separates a semantic refutation from a tactic artifact — the same witness with its
refutation ``¬`` DROPPED (i.e. asserting the frozen solution IS correct at that
input, which is TRUE of it) against BOTH. If a claim that is true of the frozen
solution ALSO fails to build, the case's gold-side exit code carries no
information and the case attests to nothing. Measured for all eight reject cases
on this carrier: rival 0 / gold 1 / flipped-on-gold 0 / flipped-on-rival 1 —
gold's exit code tracks the claim's polarity in every case, so each rejection is
a refutation rather than a tactic mismatch.
  - the frozen impl DOES reduce at ``[]`` (``implementation_… [] = none`` closes
    by ``rfl``), so the empty configuration needs no hypotheses at all.

Two consequences for how a witness here must be written. First, a witness must
not route its refutation through a ``have hres : implementation_… = <value>``
that is FALSE of the frozen solution: such a step fails on gold in the equation
compiler (an unreduced ``forIn`` term) rather than by refutation, and it fails
identically for a TRUE claim, so it discriminates nothing. State the refutation
against ``implementation_…`` directly and let the spec's own case split do the
work. Second, a conditioned witness needs the sentinel guard in BOTH forms — the
Bool ``(ver == "unknown version") = false`` for ``requirementUnmet`` and the Prop
``¬ ver = "unknown version"`` for the impl's own ``if`` — or the impl's branch
stays unreduced and ``decide`` reports free variables in the target.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — the PERMISSION VIOLATION is inexpressible, but
    its OBSERVABLE EFFECT is not, and the port was wrong to drop the case on the
    first half alone. Lean is referentially transparent: the sole input
    ``entries`` is passed by value, so there is no read-only half-permission to
    overwrite and no aliasing to exploit, and nothing here can be rejected FOR
    the write the way Viper rejects it. But what the nagini rival actually probed
    is that the configured minimum must be the one compared against: it zeroed
    ``reqversion`` before comparing, so a too-old present version came out met.
    That behavior IS expressible — see w-neutralized-minimum, which substitutes
    the required string with a fixed low one and is refuted at required 3.11 /
    present 3.10. Added by audit; the port had recorded this omission as
    inexpressible, which was true of the mechanism and false of the behavior.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as in nagini. The comparison is the
    behavior under specification, so it is modeled DEEPLY (``parseVersion`` /
    ``verGt`` / ``stringGt`` fully unfolded from the inputs), not
    axiomatized; the bundle declares no ``opaque``/``axiom``. There is nothing an
    implementation could echo without doing the work. The positive control is an
    honest cheapest-correct reshape instead.

  * PARTIAL-DOMAIN / VALUE / CONTROL-FLOW — the real attacks. The discriminating
    content of the fix is comparing versions as RELEASE NUMBERS rather than as
    TEXT; that lives in the release-number clause. Every rival whose faithful
    real patch would fail the F2P must diverge there or on one of the structural
    clauses the returned-index carries.

CASE-COUNT vs NAGINI. The nagini sibling contracted a single-entry guard
``verify_requirement(reqversion, extversion, ext_known) -> bool`` with a
normal-vs-exceptional (return vs raise) postcondition, and ran seven cases: a
positive control, an admissibility probe, a MANDATORY frame-mutation rival, and
four value/partial-domain rivals (pre-patch textual compare, ignore-ext_known,
always-return, leading-segment-only). This Lean carrier models the WHOLE loop
over a ``List (String × Option String)`` returning the first-unmet index rather
than a per-entry boolean, so the correspondence is:

  - nagini "ext_known / unknown-version guard" (Ensures ext_known)   → w-ignore-unknown
  - nagini "pre-patch textual compare" (THE bug, Exsures on 3.9<3.10)→ w-prepatch-string-compare
  - nagini "leading-segment-only" (misjudges 3.11 vs 3.10)           → w-leading-segment-only
  - nagini "always-return / never abort" (control-flow)              → w-always-met (result=none)
  - nagini positive control (De-Morgan reshape) + admissibility      → pos-delegate-entryUnmet, admiss-ground
  - nagini frame-mutation rival (1/2-permission write)               → w-neutralized-minimum (behavioral substitute; see above)

Two additional rivals have NO nagini counterpart because the nagini function
returned a bool while this one returns an INDEX, exposing two structural clauses
the boolean surface never had: w-report-when-met attacks (C-exists) (reports a
failing index over a fully-met configuration), and w-report-last attacks
(C-first) (reports the LAST failing index instead of the first). These are pure
spec-strength cases; their refinement notes state honestly that the single-entry
F2P config would not by itself distinguish them (their faithful patches would
still raise on the F2P input), so they defend clauses the F2P under-exercises
rather than the F2P boundary directly — included so no top-level clause and
neither binder goes unattacked.

The AXIOM_TESTS lane is dropped: it is G-AX's job and this gate ignores it
(meta.json records the comparison as an A-reference deep model, no consumed
axiom).

WITNESS SPREAD (binder + clause coverage). The reject witnesses probe distinct
input points so no two share a refutation site and each binder is varied:
  - w-always-met            : one literal sentinel entry, fully reducing          → (C-exists)
  - w-report-when-met       : the empty configuration ``[]``, fully decidable      → (C-exists)/(C-none)
  - w-report-last           : two literal sentinel entries, fully reducing        → (C-first), index binder k
  - w-ignore-unknown        : one ``some "unknown version"`` entry                → sentinel branch of the met/unmet predicate
  - w-absent-is-failure     : one literal ``none`` entry, fully reducing          → the absent-provider arm of the met/unmet predicate
  - w-prepatch-string-compare: parses [3,9] vs [3,10] + raw-string order true     → release-number clause (THE bug)
  - w-leading-segment-only  : ``[3,11]`` vs ``[3,10]`` (equal leading segment)     → release-number clause, later-segment sub-domain
  - w-neutralized-minimum   : ``[3,11]`` vs ``[3,10]`` with the minimum replaced  → the compared minimum is the configured one
The ``entries`` binder is varied in length (0, 1, 2) and in entry shape (absent
vs present vs sentinel vs release number); the index binder ``k`` is varied by
w-report-last (k=1) against every other rival's k=0. That is 8 distinct
refutation sites, no two shared — the ``loaded? = none`` arm having been added by
the second audit, which found it the one branch of ``entryUnmet`` no rival
attacked. Every refutation site is a LITERAL entry list, so the distinguishing
values are read directly off the witness: required 3.9 / present 3.10 (the
version order and the raw-string order disagree — the issue's own case),
required 3.11 / present 3.10 (they agree, and the later component decides),
required 0.1 / present the sentinel, an absent provider, one and two sentinel
entries, and the empty list.

MEASURED DISCRIMINATION on the current carrier (four builds per reject case:
witness-vs-rival / witness-vs-gold / flipped-claim-vs-gold / flipped-claim-vs-rival,
where the flipped claim drops the refutation ``¬`` and so is TRUE of gold):

  - w-always-met              rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-report-when-met         rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-report-last             rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-ignore-unknown          rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-absent-is-failure       rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-prepatch-string-compare rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-leading-segment-only    rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST
  - w-neutralized-minimum     rival 0 / gold 1 / flip-gold 0 / flip-rival 1  HONEST

In every case gold's exit code INVERTS with the claim's polarity (1 for the
refutation, 0 for the flipped claim), which is what makes the rejection
attributable to the spec rather than to a tactic mismatch. This is the property
the previous revision of this battery could not establish for the three
version-order cases: their witnesses ended in a hand-built step (an
anonymous-constructor ``exact ⟨…⟩``, a bare trailing ``decide``, a manual
``intro hall`` elimination) applied to a goal in which gold's ``forIn`` term was
still unreduced, so BOTH polarities died in the same step. The present witnesses
state every version fact as an explicit rewrite in the ``simp`` set
(``parseVersion`` by ``rfl``, ``verGt`` by ``decide``, ``stringGt`` via
``String.lt_iff_toList_lt``) and let ``simp`` carry gold's reduction to a fully
reduced ``⊢ False``; no hand step remains.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9711"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. `_IMPL` is the FULL gold impl-region body (the `def`), unique
# in _BASE and entirely inside the impl region. `_PROOF_INTRO` is the first two
# lines of the gold proof BODY (inside the proof region), used to prepend a
# ground `have` for the admissibility positive without touching the theorem
# statement.
# ---------------------------------------------------------------------------
_IMPL = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion req, parseVersion ver with
        | some a, some b => if verGt a b then fulfilled := false
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none'''

assert _BASE.count(_IMPL) == 1, "anchor drift: gold impl not found verbatim"

_PROOF_INTRO = "  intro entries _hpre\n  rw [impl_eq_loopFrom0 entries]"
assert _BASE.count(_PROOF_INTRO) == 1, "anchor drift: proof intro not unique"


# ---------------------------------------------------------------------------
# (A) POSITIVE CONTROL — structurally different but CORRECT. Collapse the
# in-line unknown-version / release-number / string-fallback decision into a
# single delegation to the spec's own `entryUnmet`, dropping the `(req, loaded)`
# destructuring and the nested `fulfilled` flag. Same value on every input; the
# proof is re-closed for the new loop shape (the `impl_eq_loopFrom0` induction is
# rewritten to reduce `entryUnmet e` directly instead of unfolding the flag).
# Reuses ONLY the frozen lemma names (loopSpec / loopFrom / loop_char_ind /
# impl_eq_loopFrom0) — no NEW theorem/lemma, axiom, or assumption token.
# ---------------------------------------------------------------------------
_IMPL_POS = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for e in entries do
    if entryUnmet e then
      return some idx
    idx := idx + 1
  return none'''

_PROOF_POS = '''def loopSpec (base : Nat) (rest : List (String × Option String))
    (r : Option Nat) : Prop :=
  match r with
  | none => ∀ e ∈ rest, entryUnmet e = false
  | some k =>
      k ≥ base ∧
      (∃ e, rest[k - base]? = some e ∧ entryUnmet e = true) ∧
      (∀ j, j < k - base → ∀ e, rest[j]? = some e → entryUnmet e = false)

def loopFrom (base : Nat) : List (String × Option String) → Option Nat
  | [] => none
  | e :: rest => if entryUnmet e then some base else loopFrom (base + 1) rest

theorem loop_char_ind (base : Nat) (rest : List (String × Option String)) :
    loopSpec base rest (loopFrom base rest) := by
  induction rest generalizing base with
  | nil => simp [loopFrom, loopSpec]
  | cons e rest' ih =>
    unfold loopFrom
    cases h : entryUnmet e with
    | true =>
      simp only [if_true]
      simp only [loopSpec]
      refine ⟨le_refl base, ⟨e, ?_, h⟩, ?_⟩
      · simp
      · intro j hj; omega
    | false =>
      simp only [Bool.false_eq_true, if_false]
      have IH := ih (base + 1)
      cases hr : loopFrom (base + 1) rest' with
      | none =>
        rw [hr] at IH
        simp only [loopSpec] at IH ⊢
        intro e' he'
        rcases List.mem_cons.mp he' with rfl | hmem
        · exact h
        · exact IH e' hmem
      | some k =>
        rw [hr] at IH
        simp only [loopSpec] at IH ⊢
        obtain ⟨hk, ⟨e', hek, hue'⟩, hbefore⟩ := IH
        refine ⟨by omega, ⟨e', ?_, hue'⟩, ?_⟩
        · have hkb : k - base = (k - (base + 1)) + 1 := by omega
          rw [hkb, List.getElem?_cons_succ]
          exact hek
        · intro j hj e'' hje
          cases j with
          | zero =>
            simp only [List.getElem?_cons_zero] at hje
            rw [Option.some_inj] at hje
            subst hje
            exact h
          | succ n =>
            rw [List.getElem?_cons_succ] at hje
            exact hbefore n (by omega) e'' hje

theorem impl_eq_loopFrom0 (entries : List (String × Option String)) :
    implementation_verifyExtensionVersions entries = loopFrom 0 entries := by
  unfold implementation_verifyExtensionVersions
  generalize (0 : ℕ) = base
  induction entries generalizing base with
  | nil => rfl
  | cons e rest ih =>
    simp only [List.forIn_cons]
    rw [loopFrom]
    cases h : entryUnmet e with
    | true => simp only [if_true, Id.run]; rfl
    | false => simp only [Bool.false_eq_true, if_false, Id.run_bind]; exact ih (base + 1)


theorem correct_verifyExtensionVersions :
    ∀ entries : List (String × Option String),
      problem_pre_verifyExtensionVersions entries →
      problem_spec_verifyExtensionVersions entries
        (implementation_verifyExtensionVersions entries) := by
  intro entries _hpre
  rw [impl_eq_loopFrom0 entries]
  have h := loop_char_ind 0 entries
  simp only [loopSpec, Nat.sub_zero] at h
  unfold problem_spec_verifyExtensionVersions
  cases hr : loopFrom 0 entries with
  | none => simpa [hr] using h
  | some k =>
      rw [hr] at h
      exact ⟨h.2.1, h.2.2⟩'''


def _pos_module():
    """Full positive-control Solution.lean: swap impl AND the whole proof body.
    The theorem STATEMENT (byte-identical) sits inside `_PROOF_POS`; the frozen
    proof body is replaced wholesale, so extract it from _BASE and swap."""
    a = _BASE.index("-- proof-start\n") + len("-- proof-start\n")
    b = _BASE.index("\n-- proof-end")
    frozen_proof = _BASE[a:b]
    mod = _swap(_BASE, _IMPL, _IMPL_POS)
    return _swap(mod, frozen_proof, _PROOF_POS)


# ---------------------------------------------------------------------------
# (B) ADMISSIBILITY — the theorem is guarded by a precondition
# (`problem_pre_verifyExtensionVersions`: every version string an entry mentions
# is ASCII text), so the probe has two halves, and BOTH are needed for the case
# to attest anything:
#   (i)  the precondition is SATISFIED at a ground, F2P-shaped input — if it were
#        not, the obligation could be vacuously true and the whole battery would
#        be proving nothing (PRECOND-TOO-STRONG in its sharpest form);
#   (ii) the spec is SATISFIABLE at that same admitted input.
# Both are `have`s prepended inside the existing proof body, then the frozen
# obligation runs verbatim: the theorem statement stays byte-identical and
# nothing is assumed. The input is a present sentinel version, which reduces via
# string-literal equality.
# ---------------------------------------------------------------------------
_ADMISS_GROUND = (
    '  have _admits : problem_pre_verifyExtensionVersions [("1.0", some "unknown version")] := by\n'
    "    unfold problem_pre_verifyExtensionVersions\n"
    "    decide\n"
    '  have _ground : problem_spec_verifyExtensionVersions [("1.0", some "unknown version")]\n'
    '      (implementation_verifyExtensionVersions [("1.0", some "unknown version")]) := by\n'
    "    unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
    "    simp only [entryUnmet, requirementUnmet, List.forIn_cons, List.forIn_nil]\n"
    "    norm_num\n"
    + _PROOF_INTRO
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — wrong impls sharing the frozen spec (they keep the gold
# proof body verbatim, which no longer closes for the reshaped impl, so the file
# does NOT verify). Each carries (a) a refinement note and (b) a witness BUILT
# against its rival (elaborates) and against gold (fails).
# ---------------------------------------------------------------------------

# (1) always-met: never reports a failure. == the control-flow "always return /
# never abort" family. Attacks (C-exists).
_R_ALWAYS_MET = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := none'''

# (2) ignore-unknown: drops the `"unknown version"` sentinel guard, keeping the
# release-number compare and the string fallback. On a present sentinel it no
# longer fails. == nagini's ignore-ext_known rival.
_R_IGNORE_UNKNOWN = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      match parseVersion req, parseVersion ver with
      | some a, some b => if verGt a b then fulfilled := false
      | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none'''

# (3) prepatch-string-compare: the ORIGINAL bug. Compares the required/present
# versions as raw strings for the present-version case, never as release numbers.
# == nagini's pre-patch textual compare. THE F2P discriminator.
_R_PREPATCH = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none'''

# (4) leading-segment-only: a "major version" shortcut — compares only the first
# release segment, ignoring later ones. == nagini's leading-segment-only rival.
# Misjudges 3.11 vs 3.10 (equal leading segment) as met.
_R_LEADING = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion req, parseVersion ver with
        | some a, some b =>
          match a.release, b.release with
          | x :: _, y :: _ => if x > y then fulfilled := false
          | _, _ => pure ()
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none'''

# (5) report-when-met: reports a failure at index 0 even for a fully-met (or
# empty) configuration. No nagini counterpart (nagini returned a bool). Attacks
# (C-exists): the returned `some k` claims an unmet entry that does not exist.
_R_REPORT_WHEN_MET = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion req, parseVersion ver with
        | some a, some b => if verGt a b then fulfilled := false
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return some 0'''

# (7) neutralized-minimum: compares against a FIXED low minimum instead of the
# entry's own required string, so any present version that parses comes out met.
# The behavioral substitute for nagini's frame-mutation rival (which zeroed the
# required list under a read-only permission): the permission violation is
# inexpressible here, but the observable effect — the compared minimum is not the
# configured one — is. Added by audit.
_R_NEUTRALIZED = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => pure ()
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion "0", parseVersion ver with
        | some a, some b => if verGt a b then fulfilled := false
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none'''

# (8) absent-is-failure: reports a failure for an entry with NO present version
# (`loaded? = none`), which imposes no requirement. Added by audit: the `none` arm
# of `entryUnmet` was the only branch of the met/unmet predicate no rival probed.
# Fully reducing (a literal `none` entry needs no hypotheses).
_R_ABSENT_FAILS = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  for (req, loaded) in entries do
    match loaded with
    | none => return some idx
    | some ver =>
      let mut fulfilled := true
      if ver == "unknown version" then
        fulfilled := false
      else
        match parseVersion req, parseVersion ver with
        | some a, some b => if verGt a b then fulfilled := false
        | _, _ => if stringGt req ver then fulfilled := false
      if !fulfilled then
        return some idx
    idx := idx + 1
  return none'''

# (6) report-last: reports the LAST failing index instead of the first (keeps
# scanning rather than early-returning). No nagini counterpart. Attacks
# (C-first): the minimality clause is violated when an earlier entry is also
# unmet.
_R_REPORT_LAST = '''def implementation_verifyExtensionVersions
    (entries : List (String × Option String)) : Option Nat := Id.run do
  let mut idx := 0
  let mut found := none
  for e in entries do
    if entryUnmet e then
      found := some idx
    idx := idx + 1
  return found'''


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS — MUST verify, else the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical and adds no helper/axiom/token.
    # =====================================================================
    {
        "id": "pos-delegate-entryUnmet",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_module(),
        "rationale": "a correct reshape that collapses the in-line "
                     "unknown-version / release-number / string-fallback "
                     "decision into a single delegation to the spec's own "
                     "`entryUnmet` computes the same first-unmet index on every "
                     "input, so it must satisfy all three clauses (C-none / "
                     "C-exists / C-first); if it cannot, the postcondition is "
                     "SPEC-TOO-STRONG. The proof re-closes for the new loop shape "
                     "by reducing `entryUnmet e` directly in the "
                     "`impl_eq_loopFrom0` induction; the theorem statement is "
                     "byte-identical and only the frozen lemma names are reused "
                     "(no new theorem/lemma/axiom/assumption token).",
    },
    {
        "id": "admiss-ground-present-sentinel",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_INTRO, _ADMISS_GROUND),
        "rationale": "the theorem is GUARDED by "
                     "`problem_pre_verifyExtensionVersions`, so this probe does "
                     "both halves of the nagini precondition-admission case at a "
                     "ground F2P-shaped input (a single entry with a present "
                     "version): it DISCHARGES the precondition there by `decide`, "
                     "and it discharges the spec there by `norm_num`, before "
                     "closing the frozen obligation verbatim. The first half is "
                     "what rules out the sharpest failure mode of adding a "
                     "precondition — a hypothesis no normal configuration "
                     "satisfies would make the obligation vacuous and every other "
                     "case in this battery meaningless (PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, both instances are `have`s "
                     "inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — MUST be rejected. Each carries a
    # refinement argument + a refutation witness (elaborates against the rival,
    # fails against gold). Witnesses over the opaque string carrier CONDITION on
    # the comparison rather than computing it (see CARRIER NOTE); their binder
    # sets are jointly satisfiable.
    # =====================================================================
    {
        "id": "w-prepatch-string-compare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_PREPATCH),
        "refinement": "this is THE original defect: for a present version it "
                      "compares the required and present versions as raw strings, "
                      "never as release numbers. On the F2P fulfilled block "
                      "(required 3.9, present 3.10) the raw-string order reports "
                      "3.9 > 3.10 and the entry is wrongly flagged as unmet, so a "
                      "patch of this shape reintroduces the 'not new enough' false "
                      "failure the issue reports and FAILS the F2P — it does NOT "
                      "resolve.",
        "rationale": "REJECT from the version-order clause: on a present "
                     "version the result must follow the version comparison, but "
                     "this rival follows the raw-string comparison. Refuted at "
                     "the exact F2P boundary (required 3.9, present 3.10) — the "
                     "one input where the two orders DISAGREE: the raw-string "
                     "order puts 3.9 above 3.10 (so this rival reports `some 0`) "
                     "while the version order finds the entry met (so gold "
                     "reports `none`). Stated at that literal entry: both parses "
                     "are `rfl` rewrites, the version verdict is `decide`d, and "
                     "the raw-string verdict goes through "
                     "`String.lt_iff_toList_lt`; nothing is conditioned.",
        # DISCRIMINATION (four builds): rival 0 / gold 1 / flipped-claim-on-gold
        # 0 / flipped-claim-on-rival 1. Gold's residual is a fully reduced
        # `⊢ False`. The previous revision ended with an anonymous-constructor
        # `exact ⟨…⟩` step that could not elaborate against gold's unreduced
        # `forIn` term for EITHER polarity, so gold's exit code carried no
        # information; every version fact is now an explicit `simp` rewrite.
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions [("3.9", some "3.10")]\n'
            '      (implementation_verifyExtensionVersions [("3.9", some "3.10")]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet, requirementUnmet,\n"
            '    show parseVersion "3.9" = some { epoch := 0, release := [3, 9], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            '    show parseVersion "3.10" = some { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            "    show verGt { epoch := 0, release := [3, 9], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } = false from by decide,\n"
            '    show stringGt "3.9" "3.10" = true from by\n'
            "      simp only [stringGt, decide_eq_true_eq, String.lt_iff_toList_lt]; decide]\n"
        ),
    },
    {
        "id": "w-leading-segment-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_LEADING),
        "refinement": "a 'major version only' shortcut that compares just the "
                      "leading release segment accepts any present version with "
                      "the same leading number regardless of the later segments — "
                      "e.g. required 3.11 vs present 3.10 is judged met (leading "
                      "3 == 3). The F2P not-fulfilled block requires required "
                      "3.11 / present 3.10 to be reported as a failure; this "
                      "shortcut reports met instead, so a patch of this shape "
                      "FAILS the F2P and does NOT resolve.",
        "rationale": "REJECT from the version-order clause on the "
                     "later-component sub-domain: at required 3.11 / present "
                     "3.10 the required minimum exceeds the present version at "
                     "the SECOND component (`verGt` is true), so gold reports "
                     "`some 0`, but this rival compares only the leading "
                     "component (3 vs 3) and reports `none`. Refuted at that "
                     "literal entry; the two parses are supplied as `rfl` "
                     "rewrites and the order verdict by `decide`, so nothing is "
                     "conditioned and there is no satisfiability side-condition.",
        # DISCRIMINATION (four builds): rival 0 / gold 1 / flipped-claim-on-gold
        # 0 / flipped-claim-on-rival 1. Gold's residual is a fully reduced
        # `⊢ False`; the flipped claim (true of gold) BUILDS against gold, so
        # gold's exit code tracks the claim rather than a tactic mismatch.
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions [("3.11", some "3.10")]\n'
            '      (implementation_verifyExtensionVersions [("3.11", some "3.10")]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet, requirementUnmet,\n"
            '    show parseVersion "3.11" = some { epoch := 0, release := [3, 11], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            '    show parseVersion "3.10" = some { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            "    show verGt { epoch := 0, release := [3, 11], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } = true from by decide]\n"
        ),
    },
    {
        "id": "w-ignore-unknown",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_IGNORE_UNKNOWN),
        "refinement": "dropping the `\"unknown version\"` sentinel guard lets an "
                      "extension whose version is unreported be treated as "
                      "satisfying the minimum (the sentinel string does not parse "
                      "as a release number, so it falls to the string fallback, "
                      "which need not fail). The modeled behavior — matching the "
                      "issue and the gold code — is that an unknown present "
                      "version must be reported as a failure; a patch missing the "
                      "guard changes that behavior and does NOT resolve.",
        "rationale": "REJECT from the sentinel branch of the met/unmet predicate: "
                     "on a present `\"unknown version\"` entry gold reports "
                     "`some 0`, but this rival, having dropped the guard, reports "
                     "`none`. Refuted at that entry, conditioned on the sentinel "
                     "not parsing as a release number (hv) and the string "
                     "fallback not firing for the given required string (hs) — "
                     "the exact sub-domain the guard covers; the two binders are "
                     "jointly satisfiable.",
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions [("0.1", some "unknown version")]\n'
            '      (implementation_verifyExtensionVersions [("0.1", some "unknown version")]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet, requirementUnmet,\n"
            '    show parseVersion "unknown version" = none from by rfl,\n'
            '    show stringGt "0.1" "unknown version" = false from by\n'
            "      simp only [stringGt, decide_eq_false_iff_not,\n"
            "        String.lt_iff_toList_lt]; decide]\n"
        ),
    },
    {
        "id": "w-always-met",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_ALWAYS_MET),
        "refinement": "an implementation that never reports a failure would let "
                      "the build proceed for a too-old (or unknown) extension. "
                      "The F2P not-fulfilled block requires required 3.11 / "
                      "present 3.10 to be reported as a failure; an always-met "
                      "patch reports none instead, so it FAILS the F2P and does "
                      "NOT resolve. (Control-flow analogue of nagini's "
                      "always-return / never-abort rival.)",
        "rationale": "REJECT from clause (C-exists): on any configuration with an "
                     "unmet entry the result must be `some k`, but this rival "
                     "always returns `none`, which by clause (C-none) claims every "
                     "entry is met. Refuted at a LITERAL sentinel entry, which is "
                     "the cheapest fully-reducing unmet entry on this carrier (the "
                     "sentinel branch decides by string-literal equality), so the "
                     "refutation needs no hypotheses at all.",
        # AUDIT NOTE. The original witness conditioned on an OPAQUE entry
        # (`entryUnmet e = true` for an abstract `e`), which left gold's goal an
        # unreduced `forIn` term over `e`: gold failed with `unsolved goals`, but a
        # FORGERY asserting the rival was CORRECT at a met entry failed on gold the
        # same way (rival 0 / gold 1), so the exit code carried no information.
        # Replaced with a literal sentinel entry: everything reduces, and the
        # ¬-dropped control now BUILDS against gold (exit 0), i.e. gold provably
        # satisfies the spec at exactly this input.
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions [("1.0", some "unknown version")]\n'
            '      (implementation_verifyExtensionVersions [("1.0", some "unknown version")]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet, requirementUnmet]\n"
        ),
    },
    {
        "id": "w-report-when-met",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_REPORT_WHEN_MET),
        "refinement": "reporting a failure at index 0 for a fully-met (or empty) "
                      "configuration would abort the build when every extension "
                      "is adequate. The F2P fulfilled block (required 3.9, "
                      "present 3.10) and the empty-needs block both require the "
                      "function NOT to report a failure; this rival reports one, "
                      "so a patch of this shape FAILS the F2P and does NOT "
                      "resolve. (No nagini counterpart: the nagini function "
                      "returned a bool, never an index, so it had no way to "
                      "'report a failure that does not exist'.)",
        "rationale": "REJECT from clause (C-exists): a returned `some k` must "
                     "witness an unmet entry at position k, but on the empty list "
                     "there is no entry `0` at all — gold returns `none`, this "
                     "rival returns `some 0`. Refuted at the empty configuration "
                     "`[]`, which is fully decidable (no carrier, no binders).",
        # AUDIT NOTE. The original witness opened with `have hres :
        # implementation_… [] = some 0`, which is FALSE of the frozen solution, so
        # gold's build died on that step (`Tactic rfl failed`, an unreduced `forIn`
        # term) rather than by refutation — and a forgery routed through the same
        # false `hres` also cleared both halves. The frozen impl DOES reduce at
        # `[]` (measured: `implementation_… [] = none` closes by `rfl`), so the
        # refutation is now stated directly against `implementation_…` with no
        # intermediate claim. The ¬-dropped control BUILDS against gold (exit 0).
        "witness": (
            "example :\n"
            "    ¬ problem_spec_verifyExtensionVersions []\n"
            "      (implementation_verifyExtensionVersions []) := by\n"
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp\n"
        ),
    },
    {
        "id": "w-report-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_REPORT_LAST),
        "refinement": "reporting the LAST failing index instead of the first "
                      "would, on a configuration with more than one unmet entry, "
                      "name the wrong entry as the cause. The single-entry F2P "
                      "config would not by itself distinguish this rival (with one "
                      "entry, first == last), so its faithful patch would still "
                      "abort on the F2P input; this case is included as a pure "
                      "spec-strength attacker on the first-ness clause the "
                      "returned index carries — a clause the single-entry F2P "
                      "under-exercises — rather than an F2P-boundary "
                      "discriminator. Stated honestly so the manifest does not "
                      "over-claim an F2P break it cannot demonstrate here.",
        "rationale": "REJECT from clause (C-first): when two entries are both "
                     "unmet the result must be the FIRST index (0), but this "
                     "rival keeps scanning and returns the last (1); the "
                     "minimality clause `∀ j < k, entry j is met` then requires "
                     "entry 0 to be met, contradicting that it is unmet. Refuted "
                     "on two LITERAL sentinel entries — both unmet by the sentinel "
                     "branch, which reduces — so the rival returns index 1 while "
                     "the spec pins 0. Varies the returned-index binder k to 1 "
                     "(every other rival probes k=0).",
        # AUDIT NOTE. The original witness conditioned on two OPAQUE entries and
        # routed through `have hres : implementation_… [e0, e1] = some 1`, false of
        # the frozen solution; gold died on that step, and a forgery asserting the
        # rival was CORRECT at a single-entry agreement point cleared both halves
        # identically (rival 0 / gold 1 / probe 1). Replaced with two literal
        # sentinel entries so the whole claim reduces: gold now fails with a fully
        # reduced `⊢ False`, and the ¬-dropped control BUILDS against gold (exit 0).
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions\n'
            '        [("1.0", some "unknown version"), ("2.0", some "unknown version")]\n'
            "      (implementation_verifyExtensionVersions\n"
            '        [("1.0", some "unknown version"), ("2.0", some "unknown version")]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet, requirementUnmet]\n"
        ),
    },
    {
        "id": "w-neutralized-minimum",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_NEUTRALIZED),
        "refinement": "comparing against a fixed low minimum instead of the "
                      "entry's own required string silently drops the configured "
                      "requirement: every present version that parses as a release "
                      "number comes out met, so a too-old extension is accepted. "
                      "The F2P not-fulfilled block requires required 3.11 / present "
                      "3.10 to be reported as a failure; this rival reports none "
                      "instead, so a patch of this shape FAILS the F2P and does NOT "
                      "resolve. This is the behavioral substitute for the nagini "
                      "sibling's mandatory frame-mutation rival, which neutralized "
                      "the minimum by writing to a read-only input: the permission "
                      "violation has no instance on a referentially transparent "
                      "carrier, but the observable effect it probed does.",
        "rationale": "REJECT from the release-number clause: the minimum compared "
                     "against must be the entry's own required string. Refuted at a "
                     "present-version input whose release components are [3,11] vs "
                     "[3,10] — where the configured minimum exceeds the present "
                     "version, so gold reports `some 0`, while this rival compares "
                     "the substituted low minimum against [3,10], finds it met, and "
                     "reports `none`. Refuted at that literal entry: the three "
                     "parses (3.11, 3.10, and the substituted \"0\") are `rfl` "
                     "rewrites and both order verdicts are `decide`d, so nothing "
                     "is conditioned.",
        # DISCRIMINATION (four builds): rival 0 / gold 1 / flipped-claim-on-gold
        # 0 / flipped-claim-on-rival 1. Gold's residual is a fully reduced
        # `⊢ False`. The previous revision closed with a hand-built
        # `intro hall; have hu := hall ...` elimination that failed against
        # gold's unreduced `forIn` term for BOTH polarities, so gold's exit
        # code said nothing; every version fact is now an explicit rewrite.
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions [("3.11", some "3.10")]\n'
            '      (implementation_verifyExtensionVersions [("3.11", some "3.10")]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet, requirementUnmet,\n"
            '    show parseVersion "3.11" = some { epoch := 0, release := [3, 11], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            '    show parseVersion "3.10" = some { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            '    show parseVersion "0" = some { epoch := 0, release := [], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } from by rfl,\n'
            "    show verGt { epoch := 0, release := [3, 11], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } = true from by decide,\n"
            "    show verGt { epoch := 0, release := [], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } { epoch := 0, release := [3, 10], suffix := [4, 0, 0, 0, 1, 0], localSegs := [] } = false from by decide]\n"
        ),
    },
    {
        "id": "w-absent-is-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R_ABSENT_FAILS),
        "refinement": "an entry whose `loaded?` is `none` means no extension "
                      "providing that requirement is present at all, which imposes "
                      "no version failure here — the modeled behavior is to move on. "
                      "A patch that instead reported a failure at such an entry "
                      "would abort for every configured requirement whose provider "
                      "is simply absent, including the F2P empty-needs and "
                      "not-loaded blocks, so it does NOT resolve.",
        "rationale": "REJECT from clause (C-exists) on the ABSENT-provider "
                     "sub-domain, which no other rival in this battery probes: at "
                     "`[(\"1.0\", none)]` gold returns `none` (nothing is unmet) "
                     "while this rival returns `some 0`, and clause (C-exists) then "
                     "demands an unmet entry at position 0 — but `entryUnmet` is "
                     "`false` on a `none` entry by definition. Refuted at a literal "
                     "`none` entry, which reduces fully (measured: the whole claim "
                     "closes by `simp [entryUnmet]`, no hypotheses, no opaque "
                     "string touched). Added by this audit: the `loaded? = none` "
                     "arm of `entryUnmet` was the one branch of the met/unmet "
                     "predicate the battery left unattacked.",
        # AUDIT NOTE. Discrimination measured with four builds before landing:
        # rival 0 / gold 1 (gold's residual is a fully reduced `⊢ False`), and the
        # FLIPPED claim — assert gold IS correct at this input — builds against
        # gold (0) and fails against the rival (1). Gold's exit code therefore
        # tracks the claim, which is what makes this a refutation rather than a
        # tactic mismatch.
        "witness": (
            "example :\n"
            '    ¬ problem_spec_verifyExtensionVersions [("1.0", none)]\n'
            '      (implementation_verifyExtensionVersions [("1.0", none)]) := by\n'
            "  unfold problem_spec_verifyExtensionVersions implementation_verifyExtensionVersions\n"
            "  simp [entryUnmet]\n"
        ),
    },
]
