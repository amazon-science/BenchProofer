"""properties.py — G-PBT falsification battery for django__django-10999 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_durationFromText``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate over one input
binder). A textual duration is interpreted into an optional quantity of
microseconds. The behavior is pinned to a two-way dispatch:

  problem_spec_durationFromText (v : List Char) (result : Option Int) : Prop
    asciiText v = true →                      -- side condition 1 (see below)
    primaryInRange v = true →                 -- side condition 2 (see below)
    result = (match primaryFormatMicros v with
              | some us => some us            -- ARM 1: primary notation applies
              | none    => fallbackFormatMicros v)  -- ARM 2: defer to secondary

TWO SIDE CONDITIONS DELIMIT THE DOMAIN, and every case below is aimed INSIDE it.
``asciiText v`` (all code points below 128) is where this file's digit class —
the ASCII run ``0``-``9`` — agrees with the real interpreter's whole-Unicode
decimal-digit repertoire; ``primaryInRange v`` is where the day part, the signed
clock part and their sum each land inside the range a duration value can hold,
which is where the real interpreter returns a duration rather than signalling an
out-of-range condition. Both are stated in ``Solution.lean``'s header. They
matter to THIS file in one specific way: a case aimed at text the conditions
exclude would be judged against a hypothesis that is false there, so the
obligation would hold vacuously and the case would attribute nothing. Every
witness input below is therefore plain ASCII and of small magnitude — checked by
``decide`` inside the witnesses themselves, which supply the two hypotheses
rather than assuming them — and the ``admiss-f2p-shapes`` positive additionally
proves both conditions HOLD at its two inputs, so its discharge is not vacuous.

``primaryFormatMicros`` is a TRANSPARENT pure helper (part of the frozen spec
view): it decodes the primary clock notation — a day-prefix, a single leading
minus that negates the WHOLE clock quantity, and 1–3 colon-separated NON-negative
fields — and returns ``some µs`` when that notation applies, else ``none``.
``fallbackFormatMicros`` is the OPAQUE secondary interpreter (no constraining
axiom); its value at any input is unknown to the tactics.

BINDER STRUCTURE (read this before judging binder/clause coverage). The spec has
ONE input binder, ``v : List Char``, and TWO independent top-level arms selected
by whether the primary notation applies:

  * ARM 1 (``primaryFormatMicros v = some us``): the result must be EXACTLY that
    primary interpretation ``some us`` — the secondary interpreter is not
    consulted, and the value is pinned bit-for-bit.
  * ARM 2 (``primaryFormatMicros v = none``): the result must be EXACTLY the
    secondary interpretation ``fallbackFormatMicros v`` — no value is
    substituted for it and it is not replaced by ``none``.

Both arms are attacked, and so is the BOUNDARY between them. The load-bearing
binder ``v`` is varied across SIX DISTINCT witness inputs (counted from the
witness snippets, audit-verified): four whose primary notation applies — a
signed clock literal ``"-15:30"``, a bare-seconds literal ``"30"``, a signed
fractional-seconds literal ``"-30.1"``, and a NEGATIVE-DAY-prefixed clock
literal ``"-4 15:30"`` (ARM 1) — and two whose primary notation does not apply —
a day-time-interval literal ``"3 days 04:05:06"`` and an inner-minus clock
literal ``"-01:-01"`` (ARM 2). The inner-minus literal is the arm boundary:
``rival-inner-sign-value`` widens the notation so that input moves from ARM 2 to
ARM 1, which is the changed sub-domain no other case reaches.

THE DAY-SIGN INDEPENDENCE CLAUSE IS NOW ATTACKED (second audit repair). An
earlier revision of this paragraph counted only FIVE points and recorded, as a
correction to a still earlier revision, that the day-prefixed literal
``"-4 15:30"`` was NOT a rival's refutation point — "the day-prefix path is
exercised, but by the ``admiss-f2p-shapes`` positive and by the
``rival-perfield-sign`` decoder, not by a rival's refutation point." That
accounting was accurate but it recorded a real GAP rather than closing it: the
frozen notation gives the day count its OWN independent sign, so a negative day
count must NOT also negate the clock quantity that follows it, and no rival
tested that. ``rival-day-sign-couple`` below closes it, measured with real
builds: the coupled decoder reads ``"-4 15:30"`` as ``-346530000000`` where the
frozen notation reads ``-344670000000`` (both by ``decide``), and the latter is
exactly the total the F2P negative table pins for that literal.

THE SIGN / INNER-SIGN BEHAVIOR *IS* ATTACKED HERE (audit repair). An earlier
revision of this battery recorded the three sibling sign / inner-sign rivals as
NOT EXPRESSIBLE on this carrier, reasoning that the sign arithmetic lives inside
the frozen pure helper ``primaryFormatMicros`` and so cannot be reshaped without
breaking ``same_spec``. That reasoning was WRONG, and the audit refuted it with
real builds. A variant may not edit the frozen helper — but it may DECLARE ITS
OWN decoder inside the impl region and dispatch on that instead: ``same_spec``
elides the impl region entirely and ``variant_scope`` bans only a new
``axiom``/``theorem``/``lemma``, not a new ``def``. The frozen
``Solution_prepatch.lean`` in this very bundle does exactly that.

So the three sign rivals below (``rival-perfield-sign``, ``rival-drop-sign``,
``rival-inner-sign-value``) each ship an alternative in-region decoder and are
refuted at a concrete input, which puts the CHANGED behavior — not merely the
dispatch plumbing — under attack:

  * ``rival-perfield-sign``: each colon-separated field carries its own sign
    instead of one leading minus negating the whole clock quantity.
  * ``rival-drop-sign``: the leading minus is consumed but never applied.
  * ``rival-inner-sign-value``: the notation is WIDENED so that a clock whose
    inner (post-separator) fields carry their own minus signs is accepted and
    yields a value, where the frozen notation does not apply at all.

ADVERSARIAL READ of the remaining nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the input
    list at a half-permission (``Acc(.,1/2)``) and its MANDATORY frame-mutation
    rival WRITES through it. Lean is referentially transparent: ``v`` is an
    immutable value with no heap footprint, no ``mut`` binder, no aliasing —
    there is no read-only field to overwrite and no substitute probe. Not
    fabricated (per the porting map, this class is vacuous here); see
    ``assessment``.

  * ADMISSIBILITY — LANDED (audit repair). An earlier revision omitted this lane
    on the ground that ``correct_durationFromText`` carries no precondition
    hypothesis, so "there is nothing to admit". That is the wrong analogue on a
    TOTAL carrier: the failure this lane detects is the obligation being
    UNSATISFIABLE at an F2P-shaped input, which an unguarded ``∀ v`` does not
    rule out (a spec can be true only vacuously, or contradictory at exactly the
    input the behavior turns on, and still elaborate). The positive
    ``admiss-f2p-shapes`` therefore discharges the frozen obligation at two
    concrete F2P-shaped inputs BY EVALUATION, as ``have``s, before closing the
    frozen obligation verbatim: a leading-minus clock (primary notation applies —
    the value is decided by ``decide``) and an inner-minus clock (primary
    notation does NOT apply, so the obligation there reduces to the secondary
    interpretation and is still discharged). If either ``have`` could not be
    closed, the spec would be unsatisfiable at an input the real behavior must
    handle — PRECOND-TOO-STRONG in the form this carrier can express.

  * UNGROUNDED-ORACLE ECHO — N/A on ARM 1: the post-image ``some us`` is grounded
    in the input via the transparent ``primaryFormatMicros``. ARM 2 legitimately
    equals the opaque ``fallbackFormatMicros v`` (the unchanged secondary
    interpreter, validated == the real callee by G-CONF), which is the frame
    obligation on that arm — the result must be that interpretation, unaltered.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases primaryFormatMicros v <;> rfl``
is tuned to the frozen ``some us``/``fallback`` do-block — so a rejection alone
attributes nothing to the spec. Every ``expect="reject"`` case therefore carries
a Lean snippet proving the rival CONTRADICTS the spec at one concrete input. Each
was checked (two real ``lake env lean`` builds) to ELABORATE against its rival
and to FAIL against the frozen solution (so it discriminates rather than
asserting a tautology). ARM 1 is ground and ``decide``-able, so the FOUR rivals
whose refutation lands there (``perturb-primary-value`` at ``"30"``,
``rival-perfield-sign`` at ``"-15:30"``, ``rival-drop-sign`` at ``"-30.1"``, and
``rival-day-sign-couple`` at ``"-4 15:30"``) state the spec at a literal with no
hypothesis at all; the remaining THREE (``ignore-primary``, ``drop-fallback``,
``rival-inner-sign-value``) are CONDITIONED.

WITNESS ACCOUNTING CORRECTED (fourth audit repair). An earlier revision of this
paragraph listed ``ignore-primary`` among the ground witnesses — "``and
ignore-primary``'s primary value at ``"-15:30"``" — and then said "the TWO that
turn on the opaque ``fallbackFormatMicros``". Both counts were wrong by one, and
in the direction that UNDERSTATES the battery's exposure: ``ignore-primary``'s
witness binds ``(h : fallbackFormatMicros "-15:30".toList ≠ some (-930000000))``
and so is conditioned like the other two, which is exactly why the gate runs a
consistency probe for it. Re-derived mechanically rather than read off the prose:
``consistency_probe`` returns a probe for three of the seven reject witnesses
(``ignore-primary``, ``drop-fallback``, ``rival-inner-sign-value``) and ``None``
for the other four, and three probe builds were run, each exit 1. The count
matters because the conditioned witnesses are precisely the ones carrying the
obligation the gate cannot check (see the next paragraph), so miscounting them
as ground hides one case from the check that a re-porter is told to apply.

The witnesses whose refutation turns on the opaque ``fallbackFormatMicros`` are
CONDITIONED on the carrier — one weak hypothesis about the opaque term at the
witness input, kept jointly satisfiable (a single assumption per term), which the
gate's consistency probe confirms it cannot refute.

A CONDITIONED witness carries an obligation the gate structurally cannot check,
and a third audit found this battery failing it, so it is now recorded as a rule
for anyone re-porting this cell. The consistency probe asks only whether the
hypothesis is UNREFUTABLE, and on an opaque term it always is — no tactic can
derive `False` from ``fallbackFormatMicros v ≠ none``. So a conditioned witness
can pass every mechanical check while standing at an input where its hypothesis
is FALSE of the interpreter the opaque term is validated against, in which case
the "counterexample input" does not exist behind the opacity and the case
attributes nothing. Each conditioned witness below is therefore additionally
aimed at an input where its hypothesis is true of the REAL secondary
interpreter, and the reason is written into that case:
``drop-fallback`` stands at a day-time-interval literal the secondary notation
accepts (so ``≠ none`` holds), and ``ignore-primary`` /
``rival-inner-sign-value`` stand at literals NEITHER secondary notation accepts,
where the secondary interpretation is therefore ``none`` and their hypotheses
(``≠ some <a concrete value>``) hold for that reason.

Each gold-side failure was additionally FORGERY-TESTED (audit): a second file
differing from the witness only in what it CLAIMS — asserting the spec HOLDS at
the same input — was built against the frozen solution and ELABORATES (exit 0)
where the refutation FAILS (exit 1). Gold's exit code therefore tracks the claim
rather than a syntactic accident, so each rejection is real evidence.

AXIOM lane: EMPTY. The changed behavior is modeled DEEPLY in the frozen pure
region (no consumed axiom); the only opaque callee is the unchanged secondary
interpreter, whose soundness is G-CONF's / G-AX's job, not this gate's.
``AXIOM_TESTS`` is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-10999"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The dispatch match block is the load-bearing shape of the impl region; every
# rival reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_DISPATCH = (
    "  match primaryFormatMicros v with\n"
    "  | some us => return some us\n"
    "  | none => return fallbackFormatMicros v"
)
# The whole impl def (comments included) — used by the scaffold-drop positive,
# which also retunes the proof body.
_IMPL_DEF = (
    "def implementation_durationFromText (v : List Char) : Option Int := Id.run do\n"
    "  -- Try the primary clock notation first; on no match, defer to the secondary\n"
    "  -- notation (the unchanged alternative interpreter).\n"
    "  match primaryFormatMicros v with\n"
    "  | some us => return some us\n"
    "  | none => return fallbackFormatMicros v"
)
# Frozen tactic body (lies wholly inside `-- proof-start`/`-- proof-end`). Only a
# case that legitimately re-proves touches this; the reject rivals leave it frozen
# (they are judged by their witness, not by whether this script happens to break).
_PROOF = (
    "  intro v\n"
    "  unfold problem_spec_durationFromText implementation_durationFromText\n"
    "  intro _ _\n"
    "  simp only [Id.run]\n"
    "  cases primaryFormatMicros v <;> rfl"
)


def _with_dispatch(new_dispatch: str) -> str:
    """Solution.lean with ONLY the dispatch body replaced (spec + proof intact)."""
    return _swap(_BASE, _DISPATCH, new_dispatch)


def _dispatch_on(decoder: str) -> str:
    """The frozen impl def, dispatching on `decoder` instead of the frozen helper."""
    return (
        "def implementation_durationFromText (v : List Char) : Option Int := Id.run do\n"
        f"  match {decoder} v with\n"
        "  | some us => return some us\n"
        "  | none => return fallbackFormatMicros v")


def _with_decoder(decls: str, decoder: str) -> str:
    """Solution.lean whose impl region declares its OWN decoder and dispatches on it.

    The frozen pure helpers stay byte-identical (they are spec view); the variant
    simply stops CONSULTING them. Admissible: `same_spec` elides the impl region
    and `variant_scope` bans new axiom/theorem/lemma, not a new `def` — the
    frozen `Solution_prepatch.lean` uses the same technique.
    """
    return _swap(_BASE, _IMPL_DEF, decls.rstrip() + "\n\n" + _dispatch_on(decoder))


# ---- alternative in-region decoders used by the sign / inner-sign rivals ----
# Each mirrors the frozen day-prefix handling exactly and differs ONLY in how the
# clock's sign is decoded, so the rival is a near-miss on the changed behavior
# rather than a wholesale replacement.
_PERFIELD_DECLS = """/-- An alternative clock decoding in which EACH colon-separated field carries
its own sign and contributes with that sign, rather than a single leading minus
negating the whole clock quantity. -/
def clockPerFieldMicros? (body : List Char) : Option Int :=
  match splitOnChar ':' body with
  | [a] =>
      match signedIntToInt? a with
      | some s => some (s * 1000000)
      | none => none
  | [m, a] =>
      match signedIntToInt? m, signedIntToInt? a with
      | some mm, some s => some (mm * 60 * 1000000 + s * 1000000)
      | _, _ => none
  | [h, m, a] =>
      match signedIntToInt? h, signedIntToInt? m, signedIntToInt? a with
      | some hh, some mm, some s =>
          some (hh * 3600 * 1000000 + mm * 60 * 1000000 + s * 1000000)
      | _, _, _ => none
  | _ => none

def primaryPerFieldMicros (v : List Char) : Option Int :=
  match splitFirstSpace v with
  | some (before, after) =>
      match signedIntToInt? before with
      | some d =>
          match clockPerFieldMicros? (stripUnit after) with
          | some t => some (d * 86400 * 1000000 + t)
          | none => none
      | none => clockPerFieldMicros? v
  | none => clockPerFieldMicros? v"""

_DROPSIGN_DECLS = """/-- An alternative clock decoding that CONSUMES a leading minus but never
applies it: the clock quantity comes back unsigned. -/
def clockUnsignedMicros? (rest : List Char) : Option Int :=
  let body := match rest with
    | '-' :: t => t
    | _ => rest
  match splitOnChar ':' body with
  | [a] =>
      match parseSecMicro? a with
      | some (s, us) => some (clockUs 0 0 s us)
      | none => none
  | [m, a] =>
      match digitsToNat? m, parseSecMicro? a with
      | some mm, some (s, us) => some (clockUs 0 mm s us)
      | _, _ => none
  | [h, m, a] =>
      match digitsToNat? h, digitsToNat? m, parseSecMicro? a with
      | some hh, some mm, some (s, us) => some (clockUs hh mm s us)
      | _, _, _ => none
  | _ => none

def primaryUnsignedMicros (v : List Char) : Option Int :=
  match splitFirstSpace v with
  | some (before, after) =>
      match signedIntToInt? before with
      | some d =>
          match clockUnsignedMicros? (stripUnit after) with
          | some t => some (d * 86400 * 1000000 + t)
          | none => none
      | none => clockUnsignedMicros? v
  | none => clockUnsignedMicros? v"""

_INNERSIGN_DECLS = """/-- A WIDER primary notation: the frozen one, and — where that one does not
apply — a per-field-signed reading of the same colon-separated shape, so a clock
whose inner (post-separator) fields carry their own minus signs is ALSO accepted
and yields a value. -/
def clockInnerSignedMicros? (body : List Char) : Option Int :=
  match splitOnChar ':' body with
  | [m, a] =>
      match signedIntToInt? m, signedIntToInt? a with
      | some mm, some s => some (mm * 60 * 1000000 + s * 1000000)
      | _, _ => none
  | [h, m, a] =>
      match signedIntToInt? h, signedIntToInt? m, signedIntToInt? a with
      | some hh, some mm, some s =>
          some (hh * 3600 * 1000000 + mm * 60 * 1000000 + s * 1000000)
      | _, _, _ => none
  | _ => none

def primaryWiderMicros (v : List Char) : Option Int :=
  match primaryFormatMicros v with
  | some us => some us
  | none => clockInnerSignedMicros? v"""

_DAYCOUPLE_DECLS = """/-- An alternative day-prefix handling in which the day count's sign is COUPLED
to the clock quantity: a negative day count also negates the clock that follows
it, instead of the two carrying independent signs. The clock decoding itself is
the frozen `parseClockMicros?`, unchanged, so this rival differs from the frozen
notation on exactly one clause. -/
def primaryDayCoupledMicros (v : List Char) : Option Int :=
  match splitFirstSpace v with
  | some (before, after) =>
      match signedIntToInt? before with
      | some d =>
          match parseClockMicros? (stripUnit after) with
          | some t => some (if d < 0 then d * 86400 * 1000000 - t else d * 86400 * 1000000 + t)
          | none => none
      | none => parseClockMicros? v
  | none => parseClockMicros? v"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_durationFromText` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-drop-scaffold",
        "kind": "soundness",
        "expect": "verify",
        # Functional reshape: drop the `Id.run do` scaffold and the early
        # `return`s, computing the dispatch directly. Definitionally identical, so
        # it must satisfy `result = <dispatch>`. The `simp only [Id.run]` step is
        # no longer needed (there is no `Id.run`), so the proof body is retuned by
        # dropping exactly that one line; the statement is byte-identical, no new
        # axiom/lemma, no assumption token. Verified with a real build.
        "module": _swap(
            _swap(_BASE, _IMPL_DEF,
                  "def implementation_durationFromText (v : List Char) : Option Int :=\n"
                  "  match primaryFormatMicros v with\n"
                  "  | some us => some us\n"
                  "  | none => fallbackFormatMicros v"),
            _PROOF,
            "  intro v\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  intro _ _\n"
            "  cases primaryFormatMicros v <;> rfl"),
        "rationale": "correct reshape of the mutable-do dispatch into a direct "
                     "match; it computes the same Option on every input, so it "
                     "satisfies `result = (match primaryFormatMicros v with some us "
                     "=> some us | none => fallback v)` — else SPEC-TOO-STRONG. "
                     "Proof retuned only by removing the now-vacuous `simp only "
                     "[Id.run]` line; statement unchanged, no new assumption.",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: SAME `Id.run do` scaffold, the
        # two match arms written in the opposite order (none-first). The frozen
        # `cases primaryFormatMicros v <;> rfl` still closes both arms because the
        # decision is definitionally the same. Only the impl region changes; the
        # theorem STATEMENT and the proof body are byte-identical.
        "module": _with_dispatch(
            "  match primaryFormatMicros v with\n"
            "  | none => return fallbackFormatMicros v\n"
            "  | some us => return some us"),
        "rationale": "structurally different CORRECT reshape: the two dispatch arms "
                     "written in the opposite order; the value returned on each arm "
                     "is unchanged, so `result = <dispatch>` holds on both. A "
                     "faithful reshape MUST verify, else SPEC-TOO-STRONG. Proof: the "
                     "frozen `cases ... <;> rfl` still closes both arms (the "
                     "decision is definitionally identical); no new axiom/lemma.",
    },

    {
        "id": "pos-arm2-opaque-work",
        "kind": "soundness",
        "expect": "verify",
        # ARM-2 SOUNDNESS CONTROL (fourth audit repair — this direction had no
        # case). Both shipped positives touch ARM 2 only REFLEXIVELY: they leave
        # `fallbackFormatMicros v` standing as the literal term the spec names, so
        # the frozen `rfl` closes that arm without any reasoning about the opaque
        # secondary interpreter, and the SPEC-TOO-STRONG direction was therefore
        # untested on the arm where the carrier is opaque. A spec that pinned ARM 2
        # to the SYNTACTIC term rather than to its VALUE would reject every honest
        # impl that transforms it and this battery would not have noticed.
        #
        # This positive routes the secondary interpretation through `.map id` — a
        # value-preserving transformation the frozen tactic script cannot close by
        # reflexivity, so the proof must discharge it (`Option.map_id`) instead.
        # The impl is correct (`.map id` is the identity on `Option`), so it MUST
        # verify. Measured with a real build: exit 0.
        "module": _swap(
            _swap(_BASE, _IMPL_DEF,
                  "def implementation_durationFromText (v : List Char) : Option Int := Id.run do\n"
                  "  match primaryFormatMicros v with\n"
                  "  | some us => return some us\n"
                  "  | none => return (fallbackFormatMicros v).map id"),
            _PROOF,
            "  intro v\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  intro _ _\n"
            "  simp only [Id.run, Option.map_id]\n"
            "  cases primaryFormatMicros v <;> rfl"),
        "rationale": "SPEC-TOO-STRONG control ON THE OPAQUE ARM, which the other two "
                     "positives do not reach: they leave `fallbackFormatMicros v` "
                     "standing verbatim, so the frozen `rfl` closes ARM 2 without any "
                     "reasoning about the secondary interpreter at all. This impl "
                     "routes that interpretation through `.map id` — value-preserving, "
                     "hence still exactly `fallbackFormatMicros v`, but no longer the "
                     "same TERM — so the arm can only be closed by discharging "
                     "`Option.map_id` rather than by reflexivity. A faithful impl that "
                     "transforms the opaque value without changing it MUST verify; if "
                     "it did not, the spec would be pinning ARM 2 to the syntactic "
                     "shape of the secondary interpreter's call rather than to its "
                     "value, which is SPEC-TOO-STRONG on the one arm no other positive "
                     "exercises. Statement byte-identical; only the impl region and the "
                     "proof's one `simp only` line change; no new axiom/lemma.",
    },

    {
        "id": "admiss-f2p-shapes",
        "kind": "admissibility",
        "expect": "verify",
        # ADMISSIBILITY on a total carrier: the obligation must be SATISFIABLE at
        # the concrete input shapes the behavior turns on, not merely true
        # vacuously over the quantifier. Two `have`s discharge the frozen
        # obligation at two F2P-shaped inputs BY EVALUATION, and only then is the
        # general obligation closed with the frozen script verbatim. The impl
        # region is untouched; the statement is byte-identical; no new
        # axiom/lemma/assumption token. Verified with a real build.
        #
        # THE OBLIGATION IS NOW GUARDED by the two side conditions, so "satisfied"
        # and "satisfied vacuously" have come apart, and this case must rule the
        # second one out where it is aimed: each `have` first discharges the guarded
        # obligation (supplying the two hypotheses), and then a companion `have`
        # DECIDES that both side conditions actually HOLD at that same input. So the
        # two implications above were discharged on the model's domain rather than
        # off it — which is precisely the PRECOND-TOO-STRONG reading of a guard.
        "module": _swap(
            _BASE, _PROOF,
            "  -- The obligation is satisfiable at a leading-minus clock literal\n"
            "  -- (primary notation applies; the pinned value is decided).\n"
            "  have hneg : problem_spec_durationFromText \"-15:30\".toList\n"
            "      (implementation_durationFromText \"-15:30\".toList) := by\n"
            "    unfold problem_spec_durationFromText implementation_durationFromText\n"
            "    simp only [Id.run]\n"
            "    intro _ _\n"
            "    decide\n"
            "  -- ...NON-VACUOUSLY: both side conditions hold at that input, so the\n"
            "  -- two hypotheses just supplied are true there and `hneg` says\n"
            "  -- something about the pinned value rather than about an empty guard.\n"
            "  have hdom1 : asciiText \"-15:30\".toList = true ∧\n"
            "      primaryInRange \"-15:30\".toList = true := by decide\n"
            "  -- ...and at an inner-minus clock literal, where the primary notation\n"
            "  -- does NOT apply, so the obligation reduces to the secondary\n"
            "  -- interpretation and is still discharged (no guard excludes it).\n"
            "  have hpin : primaryFormatMicros \"-01:-01\".toList = none := by decide\n"
            "  have hdom2 : asciiText \"-01:-01\".toList = true ∧\n"
            "      primaryInRange \"-01:-01\".toList = true := by decide\n"
            "  have hinner : problem_spec_durationFromText \"-01:-01\".toList\n"
            "      (implementation_durationFromText \"-01:-01\".toList) := by\n"
            "    unfold problem_spec_durationFromText implementation_durationFromText\n"
            "    simp only [Id.run]\n"
            "    intro _ _\n"
            "    rw [hpin]\n"
            "    rfl\n"
            + _PROOF),
        "rationale": "ADMISSIBILITY (PRECOND-TOO-STRONG probe) in the form this total "
                     "carrier expresses it: the obligation is discharged at two "
                     "CONCRETE F2P-shaped inputs by evaluation, as `have`s, before the "
                     "frozen obligation is closed verbatim. One input is a "
                     "leading-minus clock literal, where the primary notation applies "
                     "and the pinned value is decided outright; the other is an "
                     "inner-minus clock literal, where the primary notation does NOT "
                     "apply, so the obligation there reduces to the secondary "
                     "interpretation. If either `have` failed to close, the spec would "
                     "be unsatisfiable at exactly an input the modeled behavior must "
                     "handle — the total-carrier analogue of a precondition that "
                     "excludes a normal input. The `∀ v` is NOT itself the reason this "
                     "lane is testable: a spec can elaborate while being true only "
                     "vacuously, and these `have`s are what rule that out at the "
                     "load-bearing inputs. Since the obligation is guarded by the two "
                     "side conditions (asciiText / primaryInRange), each discharge is "
                     "paired with a `have` that DECIDES both conditions hold at that "
                     "same input, so neither one is closed by an empty guard.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P tests. The three witnesses
    # attack both dispatch arms and vary the sole binder `v` across three points.
    # =====================================================================
    {
        "id": "ignore-primary",
        "kind": "uniqueness",
        "expect": "reject",
        # ARM 1 attack: even when the primary notation APPLIES, defer to the
        # secondary interpreter, discarding the primary interpretation. Correct
        # only when the two interpretations happen to agree; wrong wherever the
        # primary notation should win.
        "module": _with_dispatch(
            "  match primaryFormatMicros v with\n"
            "  | some _ => return fallbackFormatMicros v\n"
            "  | none => return fallbackFormatMicros v"),
        "refinement": "a faithful real patch that made the parser IGNORE a matching "
                      "primary (standard) notation and always fall through to the "
                      "secondary interpreter would mis-interpret every standard-form "
                      "literal — including the signed clock literals the F2P negative "
                      "tests fix (e.g. the leading-minus clock whose value the test "
                      "now pins). It would NOT resolve: the standard-form assertions "
                      "would read the secondary interpreter's answer instead.",
        "rationale": "REJECT from ARM 1 (`primaryFormatMicros v = some us` => result "
                     "= some us): the rival returns `fallbackFormatMicros v` on the "
                     "some-arm. Refuted at a signed clock literal whose primary value "
                     "is known: conditioned on the opaque fallback differing from "
                     "that value, the rival's result differs from the spec's. Binder "
                     "`v` at the ARM-1 signed-literal point.",
        "witness": (
            "example (h : fallbackFormatMicros \"-15:30\".toList ≠ some (-930000000)) :\n"
            "    ¬ problem_spec_durationFromText \"-15:30\".toList\n"
            "        (implementation_durationFromText \"-15:30\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  intro hspec\n"
            "  -- the two side conditions are SUPPLIED (decided true at this ASCII,\n"
            "  -- small-magnitude input), so the refutation lands INSIDE the domain\n"
            "  -- rather than being handed a hypothesis that is false there.\n"
            "  have h2 := hspec (by decide) (by decide)\n"
            "  have hp : primaryFormatMicros \"-15:30\".toList = some (-930000000) := by decide\n"
            "  rw [hp] at h2\n"
            "  exact h h2\n"),
    },
    {
        "id": "perturb-primary-value",
        "kind": "uniqueness",
        "expect": "reject",
        # ARM 1 value-pin attack: the primary notation applies, but the returned
        # microsecond quantity is perturbed by one. Correct branch selection, wrong
        # value — the tightest possible near-miss on the value pin.
        "module": _with_dispatch(
            "  match primaryFormatMicros v with\n"
            "  | some us => return some (us + 1)\n"
            "  | none => return fallbackFormatMicros v"),
        "refinement": "a faithful real patch that produced a duration off by a fixed "
                      "amount from the standard-notation value would fail every "
                      "standard-form assertion (the F2P tests pin exact totals, e.g. "
                      "the bare-seconds and signed-clock literals). It would NOT "
                      "resolve: the pinned totals would each be wrong by that amount.",
        "rationale": "REJECT from ARM 1 value pin (`= some us`): the rival returns "
                     "`some (us + 1)`. Refuted at a bare-seconds literal whose primary "
                     "value is ground and decidable, so the witness `decide`s the spec "
                     "directly (no opaque term). Binder `v` at a second, distinct ARM-1 "
                     "point; a near-miss the branch-selection rival does not subsume, "
                     "so it carries its own distinguishing input.",
        "witness": (
            "example : ¬ problem_spec_durationFromText \"30\".toList\n"
            "        (implementation_durationFromText \"30\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  -- `decide` settles the whole guarded implication: both side conditions\n"
            "  -- are ground and TRUE at this input, so the refutation is in-domain.\n"
            "  decide\n"),
    },
    {
        "id": "drop-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # ARM 2 attack: when the primary notation does NOT apply, return `none`
        # instead of consulting the secondary interpreter. Drops every value the
        # secondary interpreter would have produced (the unchanged alternative
        # notations).
        "module": _with_dispatch(
            "  match primaryFormatMicros v with\n"
            "  | some us => return some us\n"
            "  | none => return none"),
        "refinement": "a faithful real patch that made the parser return `no "
                      "interpretation` whenever the primary notation did not match "
                      "— dropping the secondary (alternative-notation) interpreters "
                      "— would fail the F2P tests that assert those alternative forms "
                      "still parse (the day-time interval format test). It would NOT "
                      "resolve: an alternative-notation literal would come back as no "
                      "result. The witness is stated at EXACTLY such a literal, which is "
                      "what ties this case to that F2P assertion rather than to an "
                      "arbitrary no-match point (see the witness-input note below).",
        "rationale": "REJECT from ARM 2 (`primaryFormatMicros v = none` => result = "
                     "fallbackFormatMicros v): the rival returns `none` on the "
                     "none-arm. Refuted at a day-time-interval literal — primary does "
                     "not apply there, but the SECONDARY notation does, so the "
                     "conditioning hypothesis (`fallbackFormatMicros ... ≠ none`) is "
                     "TRUE of the interpreter this opaque term is validated against by "
                     "G-CONF, not merely satisfiable. Binder `v` at the ARM-2 "
                     "secondary-applies point.\n"
                     "WITNESS INPUT CORRECTED (third audit repair). An earlier revision "
                     "refuted at the non-numeric literal \"z\", and that case PASSED the "
                     "gate: the witness elaborated against the rival, failed on gold, and "
                     "its consistency probe could not derive `False` (no tactic can, since "
                     "`fallbackFormatMicros` is opaque). But NEITHER of the two secondary "
                     "notations applies at \"z\" — so the hypothesis it conditioned on is "
                     "in fact FALSE of the real secondary interpreter, and the refutation "
                     "held only at an input that does not exist behind the opaque term. "
                     "The gate cannot see this (opacity is exactly what makes the probe "
                     "pass) and neither can the `refinement`, which cited the "
                     "alternative-form F2P test while the witness stood at a point no "
                     "alternative form reaches. Re-aimed at a literal the day-time "
                     "interval notation DOES accept, so the conditioning hypothesis is "
                     "satisfied by the actual carrier. Measured with real builds: rival "
                     "exit 0, gold exit 1, probe exit 1, and the flipped claim (spec HOLDS "
                     "there) exit 0 on gold / exit 1 on the rival.",
        "witness": (
            "example (h : fallbackFormatMicros \"3 days 04:05:06\".toList ≠ none) :\n"
            "    ¬ problem_spec_durationFromText \"3 days 04:05:06\".toList\n"
            "        (implementation_durationFromText \"3 days 04:05:06\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  intro hspec\n"
            "  -- the two side conditions are SUPPLIED (decided true at this ASCII,\n"
            "  -- small-magnitude input), so the refutation lands INSIDE the domain.\n"
            "  have h2 := hspec (by decide) (by decide)\n"
            "  have hp : primaryFormatMicros \"3 days 04:05:06\".toList = none := by decide\n"
            "  rw [hp] at h2\n"
            "  exact h h2.symm\n"),
    },

    # =====================================================================
    # SIGN / INNER-SIGN rivals (audit repair). Each declares its OWN clock
    # decoder inside the impl region and dispatches on it, so the CHANGED
    # behavior — not just the dispatch plumbing — is under attack. The frozen
    # pure helpers stay byte-identical; the rival simply stops consulting them.
    # =====================================================================
    {
        "id": "rival-perfield-sign",
        "kind": "uniqueness",
        "expect": "reject",
        # Each colon-separated field carries its OWN sign and contributes with
        # it, instead of one leading minus negating the whole clock quantity.
        #
        # DIVERGENCE DOMAIN, measured (audit) rather than asserted. This decoder
        # reads its final field with `signedIntToInt?`, which accepts only a
        # signed digit run — so it also stops accepting a FRACTIONAL final field.
        # Checked with real builds: it agrees with the frozen behavior at "30",
        # "15:30", "10:15:30" and "4 15:30", and DIVERGES at the minus-free
        # "30.1" (`primaryPerFieldMicros "30.1" = none` while
        # `primaryFormatMicros "30.1" = some 30100000`, both by `decide`). So it
        # is NOT a clean partial-domain near-miss confined to the leading-minus
        # sub-domain; it is wrong on the sign clause AND coarser than that. An
        # earlier revision of this entry claimed "identical on every minus-free
        # input", which the measurement refutes; corrected here. The narrower
        # near-miss on the same clause is carried by `rival-drop-sign`, which was
        # measured to agree at all five of those points including "30.1".
        "module": _with_decoder(_PERFIELD_DECLS, "primaryPerFieldMicros"),
        "refinement": "a faithful real patch with this decomposition attaches the minus "
                      "to the LEADING clock field only, so a leading-minus clock "
                      "literal comes back with its later fields still added positively "
                      "rather than the whole quantity negated. It would NOT resolve: the "
                      "F2P negative-duration assertions pin the whole-quantity totals "
                      "for exactly those literals, and each would be off by twice the "
                      "trailing fields' contribution. (It would additionally lose the "
                      "fractional-second readings, so it fails the pinned totals on more "
                      "than the negative literals — a coarser miss, still not a resolve.)",
        "rationale": "REJECT on the ARM-1 value pin, at the CHANGED clause: the whole "
                     "clock quantity is negated by one leading minus, not each field "
                     "independently. Refuted at a leading-minus two-field clock literal, "
                     "where both readings are ground, so the witness `decide`s the spec "
                     "directly (no opaque term, no hypothesis). NOT a clean "
                     "partial-domain near-miss: measured divergence also at the "
                     "minus-free \"30.1\" (this decoder's final field admits no "
                     "fractional part), so it is wrong on the sign clause and coarser "
                     "besides — see the comment above. `rival-drop-sign` is the narrow "
                     "near-miss on the same clause.",
        "witness": (
            "example : ¬ problem_spec_durationFromText \"-15:30\".toList\n"
            "        (implementation_durationFromText \"-15:30\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  -- `decide` settles the whole guarded implication: both side conditions\n"
            "  -- are ground and TRUE at this input, so the refutation is in-domain.\n"
            "  decide\n"),
    },
    {
        "id": "rival-drop-sign",
        "kind": "uniqueness",
        "expect": "reject",
        # The leading minus is CONSUMED (so the notation still applies) but never
        # applied, so the clock quantity comes back unsigned. Diverges from the
        # frozen behavior on exactly the leading-minus sub-domain.
        #
        # AGREEMENT MEASURED (audit), not asserted: this decoder was built against
        # the frozen spec at five minus-free points — "30", "30.1", "15:30",
        # "10:15:30" and "4 15:30" — and the spec HOLDS of it at every one (five
        # real builds, each exit 0, the `decide` settling the equation outright).
        # So this is the clean partial-domain near-miss on the sign clause: it
        # reproduces the frozen reading everywhere a minus is absent, including
        # the fractional and day-prefixed shapes, and is wrong only where the
        # leading minus must be applied.
        "module": _with_decoder(_DROPSIGN_DECLS, "primaryUnsignedMicros"),
        "refinement": "a faithful real patch that recognised the leading minus but never "
                      "multiplied the clock quantity by it would return a POSITIVE "
                      "duration for every negative literal. It would NOT resolve: the "
                      "F2P negative-duration assertions pin negative totals, and this "
                      "returns their magnitudes.",
        "rationale": "REJECT on the ARM-1 value pin, at the CHANGED clause: the single "
                     "leading minus must negate the clock quantity, not merely be "
                     "consumed. Refuted at a leading-minus fractional-seconds literal — a "
                     "THIRD distinct ARM-1 point, and one that also exercises the "
                     "fractional-second decoding — where both readings are ground, so the "
                     "witness `decide`s the spec directly. Partial-domain near-miss, "
                     "measured: the spec holds of this rival at five minus-free points "
                     "(\"30\", \"30.1\", \"15:30\", \"10:15:30\", \"4 15:30\"), so it "
                     "diverges only where the leading minus must be applied.",
        "witness": (
            "example : ¬ problem_spec_durationFromText \"-30.1\".toList\n"
            "        (implementation_durationFromText \"-30.1\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  -- `decide` settles the whole guarded implication: both side conditions\n"
            "  -- are ground and TRUE at this input, so the refutation is in-domain.\n"
            "  decide\n"),
        },
    {
        "id": "rival-inner-sign-value",
        "kind": "uniqueness",
        "expect": "reject",
        # ARM-BOUNDARY attack: the notation is WIDENED so a clock whose inner
        # (post-separator) fields carry their own minus signs is accepted and
        # yields a value, where the frozen notation does not apply at all. This
        # moves an input from ARM 2 to ARM 1 — the only rival here that attacks
        # which arm is selected on the changed sub-domain.
        "module": _with_decoder(_INNERSIGN_DECLS, "primaryWiderMicros"),
        "refinement": "a faithful real patch whose notation still admitted a minus after "
                      "a separator would return a VALUE for an inner-minus clock literal "
                      "instead of deferring, since no other notation matches such a "
                      "literal either. It would NOT resolve: the F2P negative-duration "
                      "assertions require exactly that literal to come back with no "
                      "interpretation.",
        "rationale": "REJECT on the ARM-1/ARM-2 BOUNDARY at the changed clause: an "
                     "inner post-separator minus must make the primary notation NOT "
                     "apply, so the result is the secondary interpretation; this rival "
                     "widens the notation and answers with its own value instead. "
                     "Refuted at an inner-minus clock literal — a FOURTH distinct binder "
                     "point, on the sub-domain no other case reaches — conditioned on the "
                     "opaque secondary interpreter differing from the rival's value "
                     "there; one weak, satisfiable hypothesis, never computed.",
        "witness": (
            "example (h : fallbackFormatMicros \"-01:-01\".toList ≠ some (-61000000)) :\n"
            "    ¬ problem_spec_durationFromText \"-01:-01\".toList\n"
            "        (implementation_durationFromText \"-01:-01\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  intro hspec\n"
            "  -- the two side conditions are SUPPLIED (decided true at this ASCII,\n"
            "  -- small-magnitude input), so the refutation lands INSIDE the domain.\n"
            "  have h2 := hspec (by decide) (by decide)\n"
            "  have hp : primaryFormatMicros \"-01:-01\".toList = none := by decide\n"
            "  rw [hp] at h2\n"
            "  exact h h2.symm\n"),
    },
    {
        "id": "rival-day-sign-couple",
        "kind": "uniqueness",
        "expect": "reject",
        # DAY-SIGN INDEPENDENCE attack (audit repair — this clause had no rival).
        # The day count and the clock quantity carry INDEPENDENT signs in the
        # frozen notation; this rival couples them, so a negative day count also
        # negates the clock that follows it. The clock decoder itself is the
        # frozen `parseClockMicros?` verbatim, so the rival differs from the
        # frozen behavior on exactly one clause.
        #
        # DIVERGENCE DOMAIN, measured (audit) rather than asserted: it agrees
        # with the frozen reading on every input with NO day prefix and on every
        # input whose day count is non-negative (both take the untouched `+ t`
        # arm), and diverges exactly where a NEGATIVE day count is followed by a
        # non-zero clock. At "-4 15:30" it reads -346530000000 where the frozen
        # notation reads -344670000000 (both by `decide`, real builds). So this
        # is a clean partial-domain near-miss on the day-sign clause.
        "module": _with_decoder(_DAYCOUPLE_DECLS, "primaryDayCoupledMicros"),
        "refinement": "a faithful real patch that let the day count's sign carry over "
                      "into the clock fields that follow it would return the wrong total "
                      "for every negative-day literal: the clock quantity would be "
                      "SUBTRACTED from the day quantity instead of added to it. It would "
                      "NOT resolve: the F2P negative-duration table pins a negative-day "
                      "literal whose clock fields contribute POSITIVELY (the day count is "
                      "negative while the trailing clock is not), and this returns that "
                      "total off by twice the clock's contribution.",
        "rationale": "REJECT on the ARM-1 value pin, at the DAY-SIGN INDEPENDENCE clause: "
                     "the day count carries its OWN sign and the clock quantity carries a "
                     "separate one, so a negative day count must not negate the clock. "
                     "Refuted at a negative-day-prefixed clock literal — a FIFTH distinct "
                     "ARM-1 point, and the only case whose refutation lands on the "
                     "day-prefix path — where both readings are ground, so the witness "
                     "`decide`s the spec directly (no opaque term, no hypothesis). "
                     "Partial-domain near-miss, measured: identical to the frozen reading "
                     "wherever there is no day prefix or the day count is non-negative.",
        "witness": (
            "example : ¬ problem_spec_durationFromText \"-4 15:30\".toList\n"
            "        (implementation_durationFromText \"-4 15:30\".toList) := by\n"
            "  unfold problem_spec_durationFromText implementation_durationFromText\n"
            "  simp only [Id.run]\n"
            "  -- `decide` settles the whole guarded implication: both side conditions\n"
            "  -- are ground and TRUE at this input, so the refutation is in-domain.\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases
# (pos-control-direct-oracle, pos-control-local-reshape, admiss-negative-clock,
# frame-mutate-fields, partial-perfield-sign, partial-drop-sign,
# partial-inner-sign-value) plus a 2-case AXIOM lane. That sibling contracts
# `parse_clock_seconds(fields, leading_minus, inner_sign_seen)` — a decomposed
# helper whose sign/inner-sign arithmetic IS the editable body. This bundle models
# a broader surface, `durationFromText(v : List Char)`. Its sign/inner-sign
# arithmetic is decoded inside the FROZEN pure helper `primaryFormatMicros`, which
# a variant may not edit — but a variant MAY declare its own decoder in the impl
# region and dispatch on that, which is how all three sibling sign rivals are
# carried here. Every sibling case is recorded below.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-control-direct-oracle    -> pos-drop-scaffold           RE-EXPRESSED
#   pos-control-local-reshape    -> pos-branch-reorder          RE-EXPRESSED
#   admiss-negative-clock        -> admiss-f2p-shapes           RE-EXPRESSED
#   frame-mutate-fields          -> (none)                      VACUOUS (no heap)
#   partial-perfield-sign        -> rival-perfield-sign         PORTED
#   partial-drop-sign            -> rival-drop-sign             PORTED
#   partial-inner-sign-value     -> rival-inner-sign-value      PORTED
#   (added: ARM-1/ARM-2 dispatch rivals ignore-primary,
#           perturb-primary-value, drop-fallback; and the day-sign
#           independence rival rival-day-sign-couple, which has no sibling
#           analogue because the sibling's decomposed helper takes its clock
#           fields already separated from the day count)
#   AXIOM_TESTS (2)              -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED (positive controls): the sibling's "return the grounded oracle
#   directly" and "reshape the final step into a local, single return" both carry
#   the ARGUMENT that a structurally different but faithful impl must verify. Here
#   the editable surface is the dispatch, so that argument is carried by (a)
#   dropping the `Id.run do` scaffold and computing the dispatch directly
#   (pos-drop-scaffold; proof retuned by removing the now-vacuous `simp only
#   [Id.run]`), and (b) writing the two dispatch arms in the opposite order
#   (pos-branch-reorder; the frozen `cases ... <;> rfl` still closes it). A FOURTH
#   audit added (c) pos-arm2-opaque-work, which has no sibling analogue at all:
#   both (a) and (b) leave the secondary interpretation standing as the literal
#   term the spec names, so the frozen `rfl` closes ARM 2 without reasoning about
#   the opaque callee, and the SPEC-TOO-STRONG direction was untested on that arm.
#   (c) routes it through `.map id` — value-preserving but not the same term — so
#   the arm must be discharged by `Option.map_id` instead of by reflexivity.
# RE-EXPRESSED (admissibility): the sibling self-calls on an F2P-shaped input to
#   show its precondition ADMITS that input. `correct_durationFromText` carries no
#   precondition hypothesis, but that does NOT make the lane vacuous — the
#   total-carrier analogue of PRECOND-TOO-STRONG is the obligation being
#   unsatisfiable at an F2P-shaped input, which an unguarded `∀ v` does not rule
#   out. `admiss-f2p-shapes` tests it directly: it discharges the frozen
#   obligation at two concrete F2P-shaped inputs by EVALUATION, as `have`s, before
#   closing the frozen obligation verbatim — a leading-minus clock literal (the
#   primary notation applies; `decide` settles the pinned value) and an
#   inner-minus clock literal (the primary notation does not apply, so the
#   obligation reduces to the secondary interpretation there).
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because its input
#   list is held at Acc(.,1/2) an impl can illegally write. This backend is
#   referentially transparent and declares no `mut` binder over the input — `v`
#   is an immutable value with no heap footprint — so there is no read-only field
#   to overwrite and no substitute probe. Not fabricated (porting map: vacuous).
# PORTED (the three sign / inner-sign rivals): an earlier revision of this file
#   recorded all three as NOT EXPRESSIBLE, on the ground that the sign arithmetic
#   lives inside the frozen `primaryFormatMicros` and so cannot be reshaped
#   without breaking `same_spec`. The audit refuted that with real builds. The
#   frozen helper indeed cannot be edited — but a variant may DECLARE ITS OWN
#   decoder inside the impl region and dispatch on that: `same_spec` elides the
#   impl region entirely, and `variant_scope` bans a new `axiom`/`theorem`/`lemma`
#   but not a new `def`. The frozen `Solution_prepatch.lean` in this bundle uses
#   exactly that technique. So all three are carried, each refuted at a concrete
#   input, which puts the CHANGED behavior under attack rather than only the
#   dispatch plumbing.
#
#   The seven witnesses probe SIX DISTINCT inputs of the sole binder `v` (counted
#   from the snippets): "-15:30", "30", "-30.1" and "-4 15:30" (primary notation
#   applies — ARM 1), "3 days 04:05:06" and "-01:-01" (primary does not apply —
#   ARM 2).
#   "-15:30" carries two different rivals (ignore-primary's branch swap and
#   rival-perfield-sign's sign clause), so seven witnesses land on six points.
#   Both top-level arms are attacked, the ARM-1 value pin is attacked on its own,
#   the ARM boundary on the inner-minus sub-domain is attacked by
#   rival-inner-sign-value (which moves an input from ARM 2 to ARM 1), and the
#   day-sign independence clause is attacked by rival-day-sign-couple — the only
#   case whose refutation lands on the day-prefix path. FOUR witnesses are fully
#   ground and `decide` the spec outright; the THREE that turn on the opaque
#   `fallbackFormatMicros` (ignore-primary, drop-fallback,
#   rival-inner-sign-value) are refuted by CONDITIONING on that term (one weak,
#   satisfiable hypothesis each, confirmed satisfiable by the gate's consistency
#   probe), never by computing it. The 5/2 split an earlier revision recorded here
#   and in the WITNESSES paragraph was wrong: ignore-primary binds a hypothesis
#   about the opaque term and is conditioned, not ground. Re-derived mechanically
#   from `consistency_probe`, which yields a probe for exactly those three.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the only opaque callee here
# is the unchanged secondary interpreter (validated == the real callee by G-CONF),
# and the changed behavior is modeled deeply in the frozen pure region with no
# consumed axiom, so there is nothing for this gate to probe.
AXIOM_TESTS = []
