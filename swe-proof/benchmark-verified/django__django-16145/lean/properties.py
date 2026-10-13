"""properties.py — G-PBT falsification battery for django__django-16145 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a positive that legitimately re-proves the
obligation for a reshaped impl, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
``theorem correct_displayAddr`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``/new axiom);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function of two inputs; String carrier — mapping.md:
value-level string formatting, identity on the character sequence):

  displayAddr (rawIpv6 : Bool) (addr : String) : String
      result = "[" ++ addr ++ "]"   if rawIpv6
             = "0.0.0.0"            elif addr = "0"
             = addr                 otherwise

  The postcondition is stated as three INDEPENDENT top-level clauses, one per
  reachable branch (directive 5: no case left unconstrained):

    * BRACKET clause — ``rawIpv6 = true → result = "[" ++ addr ++ "]"``. A raw
      IPv6 host is wrapped so it composes into a valid URL authority. Pinned by
      ``rawIpv6`` (the true branch) and by ``addr`` (the wrapped content).
    * SHORTHAND clause — ``rawIpv6 = false → addr = "0" → result = "0.0.0.0"``.
      The unspecified-address shorthand is shown in its canonical dotted form —
      the form a browser will actually follow. This is the discriminating
      decision the fix adds; it is reached ONLY when ``rawIpv6`` is false.
    * IDENTITY clause — ``rawIpv6 = false → addr ≠ "0" → result = addr``. Every
      other host is presented verbatim. Pinned by ``addr``.

GROUNDED POSTCONDITION: every clause equates the result to a term built only
from the two inputs (string concatenation, equality against two literals). The
bundle declares NO ``opaque``/``axiom`` (mapping.md: no consumed callee), so the
carrier is fully transparent — ``decide`` computes every clause at a concrete
input, and there is no answer key an impl could echo without doing the work. The
uniqueness lane is therefore about whether a rival can satisfy the surviving
clauses while diverging on a discriminating sub-domain (the shorthand host — the
pre-patch behaviour; a malformed bracket wrap; a gutted identity branch).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and DEMONSTRATED rather than asserted
    (the reason has to be shown, not claimed, because "the carrier cannot express
    it" is the most commonly mis-measured excuse for a dropped rival). The nagini
    sibling makes an input-write attack MANDATORY: ``addr`` is held at fractional
    (read-only) permission and a rival that overwrites it (``addr[i] = 48``) is
    rejected for insufficient permission, independent of any value mismatch. Two
    facts were checked with real builds here, not argued:
      1. ``theorem no_input_write (g : Bool → String → String) (r : Bool)
         (a : String) : (g r a = g r a) ∧ a = a := ⟨rfl, rfl⟩`` elaborates for an
         ARBITRARY ``g`` — the caller still holds ``a`` after the call, for every
         impl of this signature, so there is no observation an input-write could
         produce and nothing for a frame clause to protect.
      2. The nearest expressible thing, a local ``let mut addr := addr; addr :=
         "0"``, was built and is simply a DIFFERENT total function (``shadow
         false "127.0.0.1" = "0"`` closes by ``decide``). It is refuted by an
         ordinary value-level witness, i.e. it collapses into the gut/echo rival
         classes this battery already carries — it is not a permission violation
         and would not attest to a frame property.
    So the class has no expressible instance that is not already covered. No
    substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the two
    inputs (see above); there is no opaque oracle to echo. The honest analogue
    is the cheapest-correct POSITIVE CONTROL below.

  * BRACKET-CLOSE RESHAPE positive (nagini ``pos-control-bracket-reshape``) —
    DROPPED, because on this carrier it is not a reshape at all. Nagini's version
    builds the closing fragment as its own typed ``List[int]`` and concatenates
    it, which on the code-point carrier is a genuinely different construction the
    verifier must re-discharge. Built here and measured: the analogous Lean impl
    (bind ``close``, then ``"[" ++ addr ++ close``) is DEFINITIONALLY the frozen
    impl — ``example : reshape = g := rfl`` closes — because the fragment is a
    closed literal the kernel computes. An impl defeq to the frozen one satisfies
    exactly what the frozen one satisfies, so the case could never detect a spec
    over-fit; it would verify honestly and test nothing. Its intent (the shorthand
    /bracket result is pinned by VALUE, not by construction FORM) is carried
    instead by ``pos-shorthand-split-literal``, which uses the guard-orientation
    flip the carrier does NOT collapse. See the DEFEQ HAZARD note below.

  * PARTIAL-DOMAIN (the pre-patch behaviour) — APPLIES, load-bearing. The pre-fix
    code lacked the shorthand branch and showed the shorthand host verbatim; it
    is correct on every input EXCEPT the shorthand, where it is refuted. This is
    the exact verify-not-resolve discriminator the bundle exists to encode.

  * DROP-A-CLAUSE rivals (malformed bracket wrap; gutted identity branch) —
    APPLY. Each violates one independent top-level clause on a distinct
    sub-domain and is refuted with a witness at a distinct input.

  * CLAUSE-PRECEDENCE rival (guards reordered) — APPLIES, and has no nagini
    counterpart: the sibling's oracle is a single piecewise ``@Pure`` function
    whose branch order is fixed inside the oracle itself, so a rival there cannot
    reorder the decision without editing the frozen pure region. Here the three
    clauses are INDEPENDENT top-level implications, so their relative priority is
    a separate claim the spec makes and a rival can break it while leaving every
    branch body intact. Added by audit.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen script (``refine ⟨…⟩`` + per-branch ``rfl``) is
tuned to the frozen form, so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``-able concrete input; each was checked to HOLD
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). Inputs are concrete string/bool literals — the carrier
is transparent, so no conditioning-on-an-opaque-term is needed and every
witness is closed by ``decide``.

BINDER COVERAGE. Both input binders are varied across the reject witnesses:
  * ``rawIpv6`` — refuted at ``false`` (prepatch-shorthand, gut-identity) AND at
    ``true`` (drop-close-bracket, swap-guard-precedence).
  * ``addr`` — refuted at ``"0"`` (prepatch-shorthand, drop-close-bracket,
    swap-guard-precedence) AND at ``"127.0.0.1"`` (gut-identity), so it is not
    pinned to one value.
``pts`` = 3 distinct input points: (false,"0"), (true,"0"), (false,"127.0.0.1").
Each of the three independent top-level clauses is attacked in isolation by one
rival, and the CLAUSE INTERACTION — the precedence of the bracket rule over the
shorthand rule, i.e. that the bracket clause is unconditional in ``addr`` — is
attacked by a fourth (``weak-swap-guard-precedence``), which is refutable only at
the input where both guards fire and which the three isolated rivals all leave
unprobed. Note that (true,"0") carries two DISTINCT refutations: the bracket
BODY (drop-close) and the bracket PRECEDENCE (swap-guards), so the shared input
point is not a duplicate spelling of one attack.

The four rivals are NOT of equal standing, and the difference is recorded rather
than smoothed over. CORRECTED BY AUDIT: the earlier text here claimed three of
the four were verify-not-resolve discriminators "caught by the observable test
set". That claim was FALSE and is withdrawn. Re-measured input by input against
the observable suite rather than asserted, the standing is:

  * ``weak-prepatch-no-shorthand`` — the ONLY verify-not-resolve discriminator.
    It diverges at the single input the suite both reaches AND inspects the
    displayed host at, so its faithful patch fails an observable.
  * ``weak-drop-close-bracket`` (diverges on 2 reached inputs),
    ``weak-gut-identity-branch`` (4), ``weak-swap-guard-precedence`` (0) — NOT
    verify-not-resolve discriminators, and not offered as such.

The reason is a property of the suite, not of the rivals: the observable set
contains exactly ONE assertion on the displayed host string (the F2P one). The
pre-existing cases assert the RESOLVED bind host and the flags instead, and
several of them do not render the banner line at all because they stub out the
server-start step, so a wrong display string is unobservable to them. Grepping
the whole test tree at base_commit for the banner text returns no test at all.

So the latter three are included on the NARROWER basis the precedence rival
already documented: each is an observable divergence from the modeled behaviour
on a reachable input that the suite leaves UNASSERTED — and a gap in the tests
is exactly where a spec has to be stronger than its tests. The rivals themselves
are unaffected by the correction: each is genuinely WRONG against the spec, and
each ships a witness that was rebuilt and confirmed to discriminate (holds of
the rival, semantically refuted on gold). Only the prose overclaimed.

DEFEQ HAZARD ON THIS CARRIER (measured, and the reason the positives are shaped
as they are). String literals are closed terms the kernel computes, so several
"different shapes" collapse to the frozen impl definitionally and test nothing
while passing honestly:
  * ``"0.0." ++ "0.0"`` vs ``"0.0.0.0"`` — ``rfl`` closes;
  * ``"[" ++ (addr ++ "]")`` vs ``("[" ++ addr) ++ "]"`` — ``rfl`` closes, since
    the left operand is a literal and ``List.append`` reduces;
  * ``Id.run do``/early ``return`` vs the functional cascade — ``rfl`` closes.
What the carrier does NOT collapse is the ORIENTATION of the guard equation
(``"0" = addr`` vs ``addr = "0"``) for a variable ``addr``, nor ``==`` vs ``=``:
both are genuinely different instance applications requiring real re-proof. The
positives are therefore built on the guard flip, not on literal splitting.

AXIOM lane: EMPTY. mapping.md — no consumed callee axiom and no deep-model
reference; the derivation is primitive string formatting over the two inputs.
AXIOM_TESTS is empty (the axiom lane is G-AX's job in any case).

SPEC EXACTNESS (added by audit; the strongest statement available here, and it
bounds the whole SPEC-TOO-WEAK lane). The three clauses do not merely constrain
the result — they pin it UNIQUELY. This was proven with a real build against the
frozen spec, as a theorem over an ARBITRARY impl of the signature:

    theorem spec_pins_gold (f : Bool → String → String)
        (hf : ∀ r a, problem_spec_displayAddr r a (f r a)) :
        ∀ r a, f r a = implementation_displayAddr r a

It elaborates (case-split on `rawIpv6`, then on `addr = "0"`; each clause hands
back the frozen value directly). Consequently NO wrong implementation of this
signature can satisfy the frozen spec: any `f` that verifies is pointwise equal
to the frozen impl, so a SPEC-TOO-WEAK hole is impossible rather than merely
unobserved. Five NEW wrong rivals written to probe for such a hole (an over-broad
shorthand guard matching the two-character zero host; a near-miss dotted value
one octet short; a length-keyed guard expanding every one-character host; a wrap
with the wrong delimiters; the shorthand expansion leaking into the bracketed
branch) were each REFUTED by the spec at a concrete input, as that theorem
predicts. Four NEW correct reshapes (a `match` on the flag; a `==`/`BEq` guard
instead of `=`; interpolation for the wrap; a negated-guard early-return cascade)
were each PROVEN against the frozen spec, so the spec is not over-fit either.
"""
from pathlib import Path

INSTANCE = "django__django-16145"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit and the frozen
# spec + theorem STATEMENT stay byte-identical.
_IMPL_GOLD = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do\n"
    "  if rawIpv6 then\n"
    "    return \"[\" ++ addr ++ \"]\"\n"
    "  else if addr = \"0\" then\n"
    "    return \"0.0.0.0\"\n"
    "  else\n"
    "    return addr\n"
)

_PROOF_BODY = (
    "  intro rawIpv6 addr\n"
    "  unfold problem_spec_displayAddr implementation_displayAddr\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h\n"
    "    subst h\n"
    "    rfl\n"
    "  · intro h haddr\n"
    "    subst h\n"
    "    subst haddr\n"
    "    rfl\n"
    "  · intro h haddr\n"
    "    subst h\n"
    "    simp only [Id.run, Bool.false_eq_true, if_false, if_neg haddr]\n"
    "    rfl\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body only
    (spec + theorem statement + frozen proof unchanged)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical). The frozen proof stays
# in place — it will not close against the reshaped impl, which is why each
# reject case ships a discriminating witness rather than relying on the failed
# build alone.
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN (= pre-fix behaviour): drop the shorthand branch, so the
# shorthand host is shown verbatim instead of expanded to its dotted form.
# Diverges exactly on rawIpv6=false, addr="0" (the F2P sub-domain).
_PREPATCH = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do\n"
    "  if rawIpv6 then\n"
    "    return \"[\" ++ addr ++ \"]\"\n"
    "  else\n"
    "    return addr\n"
)

# DROP-CLOSE: the bracket branch omits the trailing terminator, producing an
# unbalanced host part. Violates the bracket clause on every raw-IPv6 input.
_DROP_CLOSE = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do\n"
    "  if rawIpv6 then\n"
    "    return \"[\" ++ addr\n"
    "  else if addr = \"0\" then\n"
    "    return \"0.0.0.0\"\n"
    "  else\n"
    "    return addr\n"
)

# GUT-IDENTITY: the else branch is gutted to the empty string, so every
# non-bracket, non-shorthand host renders empty. Violates the identity clause.
_GUT_IDENTITY = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do\n"
    "  if rawIpv6 then\n"
    "    return \"[\" ++ addr ++ \"]\"\n"
    "  else if addr = \"0\" then\n"
    "    return \"0.0.0.0\"\n"
    "  else\n"
    "    return \"\"\n"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional expression (no `Id.run do` / early `return`), spelling the
# branch cascade as nested `if … then … else`. Same value on every input; the
# frozen `refine`+`rfl` script no longer applies to the new shape, so the
# obligation is re-proved (statement byte-identical; no new lemma/axiom/token).
_POS_FUNCTIONAL = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String :=\n"
    "  if rawIpv6 then \"[\" ++ addr ++ \"]\"\n"
    "  else if addr = \"0\" then \"0.0.0.0\"\n"
    "  else addr\n"
)
_POS_FUNCTIONAL_PROOF = (
    "  intro rawIpv6 addr\n"
    "  unfold problem_spec_displayAddr implementation_displayAddr\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h; subst h; rfl\n"
    "  · intro h haddr; subst h; subst haddr; rfl\n"
    "  · intro h haddr; subst h; simp only [Bool.false_eq_true, if_false, if_neg haddr]\n"
)

# POSITIVE CONTROL (soundness): the shorthand branch is reshaped in a way this
# carrier does NOT collapse. Two changes, both inside the `Id.run do` form:
#   * the shorthand GUARD is written with the equation oriented the other way
#     (`"0" = addr` rather than `addr = "0"`), which for a VARIABLE `addr` is a
#     different application of the `String` `DecidableEq` instance — measured
#     NOT definitionally equal to the frozen impl (`example : n = g := rfl`
#     fails), so the identity branch genuinely needs `Ne.symm` to re-orient the
#     hypothesis before `if_neg` applies;
#   * the shorthand RESULT is BUILT by concatenating two string literals
#     (`"0.0." ++ "0.0"`) instead of one flat literal.
#
# NOTE on why the guard flip is load-bearing, measured on this carrier: a
# reshape that only splits the result literal is DEFINITIONALLY the frozen impl
# (`"0.0." ++ "0.0"` and `"0.0.0.0"` are both closed literals, so the kernel
# computes the concatenation and `rfl` closes `implSplit = implGold`). Such a
# case verifies honestly but tests nothing — an impl defeq to the frozen one
# satisfies whatever the frozen one satisfies, so it cannot detect a spec
# over-fit. The same collapse hits every literal-led append reshape here
# (`"[" ++ (addr ++ "]")` vs `("[" ++ addr) ++ "]"` is also closed by `rfl`,
# because the left operand is a concrete literal and `List.append` reduces).
# Flipping the guard is the reshape the carrier does not absorb, so the value
# equality has to be re-established rather than computed.
_POS_SPLIT = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do\n"
    "  if rawIpv6 then\n"
    "    return \"[\" ++ addr ++ \"]\"\n"
    "  else if \"0\" = addr then\n"
    "    return \"0.0.\" ++ \"0.0\"\n"
    "  else\n"
    "    return addr\n"
)
_POS_SPLIT_PROOF = (
    "  intro rawIpv6 addr\n"
    "  unfold problem_spec_displayAddr implementation_displayAddr\n"
    "  refine ⟨?_, ?_, ?_⟩\n"
    "  · intro h; subst h; rfl\n"
    "  · intro h haddr; subst h; subst haddr; rfl\n"
    "  · intro h haddr; subst h\n"
    "    simp only [Id.run, Bool.false_eq_true, if_false, if_neg (Ne.symm haddr)]\n"
    "    rfl\n"
)

# PRECEDENCE rival: the two guards are REORDERED so the shorthand test is made
# first and the bracket rule only applies when the host is not the shorthand.
# Every clause of the spec still holds on the sub-domains the other three
# rivals probe; the divergence is exactly the input where BOTH guards fire.
_SWAP_PRECEDENCE = (
    "def implementation_displayAddr (rawIpv6 : Bool) (addr : String) : String := Id.run do\n"
    "  if addr = \"0\" then\n"
    "    return \"0.0.0.0\"\n"
    "  else if rawIpv6 then\n"
    "    return \"[\" ++ addr ++ \"]\"\n"
    "  else\n"
    "    return addr\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify; else the postcondition is over-fit to the impl FORM =>
    # SPEC-TOO-STRONG. The theorem STATEMENT is byte-identical in each; no
    # helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-cascade",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_FUNCTIONAL), _PROOF_BODY, _POS_FUNCTIONAL_PROOF),
        "rationale": (
            "a correct reshape that drops the `Id.run do` / early-`return` shape and "
            "spells the branch cascade as one functional `if … then … else` "
            "expression must satisfy all three clauses (bracket / shorthand / "
            "identity). Same value on every input. The proof region is re-stated "
            "because the frozen script's identity branch ends in a trailing `rfl` "
            "that the reshape makes redundant (`Id.run` is no longer there to "
            "unfold, so `simp only` closes the goal outright and the frozen `rfl` "
            "then reports `No goals to be solved`); the reshaped script drops that "
            "one line and is otherwise the frozen script. Measured caveat, recorded "
            "so this case is not over-credited: `Id.run do` with early `return` "
            "ELABORATES to the same term as the functional cascade on this carrier, "
            "so the two impls are definitionally equal (`example : casc = g := rfl` "
            "closes) and the frozen script minus its trailing `rfl` verifies against "
            "this impl unchanged. The case is therefore a genuine test that the spec "
            "does not pin the SURFACE SYNTAX of the impl, but it is NOT evidence "
            "about the spec's semantic tightness; `pos-shorthand-split-literal` "
            "carries the non-defeq reshape. If it cannot verify => the spec is "
            "over-fit to the impl FORM (SPEC-TOO-STRONG). No new "
            "declaration/axiom/`sorry`."
        ),
    },
    {
        "id": "pos-shorthand-split-literal",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_SPLIT), _PROOF_BODY, _POS_SPLIT_PROOF),
        "rationale": (
            "a correct reshape of the shorthand branch that this carrier does NOT "
            "collapse: the guard equation is oriented the other way (`\"0\" = addr`) "
            "AND the result is built by concatenating two string literals "
            "(`\"0.0.\" ++ \"0.0\"`). Same value on every input. The guard flip is what "
            "makes the case load-bearing — for a variable `addr` it is a different "
            "application of the `String` `DecidableEq` instance, measured NOT "
            "definitionally equal to the frozen impl, so the identity branch must "
            "re-orient the hypothesis (`Ne.symm haddr`) before `if_neg` applies and "
            "the value equality is re-established rather than computed by the kernel. "
            "Must verify; else the shorthand clause is over-fit to the guard "
            "ORIENTATION and the literal FORM (SPEC-TOO-STRONG). A reshape that only "
            "split the literal would be defeq to the frozen impl and would test "
            "nothing — see the note above `_POS_SPLIT`."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped input, not only provable in the abstract.
    # The frozen theorem carries NO precondition hypothesis (the behavior is
    # total, `∀` unguarded), so nagini's precondition-admission probe has no
    # binder to attack; the honest analogue is to discharge the spec predicate at
    # the F2P ground input (rawIpv6=false, addr="0" — exactly addrport="0:8000")
    # inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-shorthand-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, "  intro rawIpv6 addr\n",
            "  have _ground : problem_spec_displayAddr false \"0\"\n"
            "      (implementation_displayAddr false \"0\") := by\n"
            "    unfold problem_spec_displayAddr implementation_displayAddr\n"
            "    decide\n"
            "  intro rawIpv6 addr\n",
        ),
        "rationale": (
            "the obligation is discharged at the F2P ground input (rawIpv6=false, "
            "addr=\"0\" — exactly addrport=\"0:8000\"), where the spec's shorthand "
            "clause demands the dotted form \"0.0.0.0\", by `decide`; then the frozen "
            "obligation is closed verbatim. Verifies (else the spec is unsatisfiable "
            "at the normal F2P input — the analogue of PRECOND-TOO-STRONG). Nothing "
            "is assumed: the theorem STATEMENT is byte-identical, the ground instance "
            "is a `have` inserted at the head of the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input,
    # checked to HOLD of the rival and FAIL on gold.
    # =====================================================================
    {
        "id": "weak-prepatch-no-shorthand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH),
        "refinement": (
            "this is EXACTLY the pre-fix behaviour: the shorthand host is shown "
            "verbatim instead of expanded to its dotted form. A faithful patch "
            "lacking the shorthand branch renders the banner with the shorthand host "
            "unchanged for the F2P input and FAILS the F2P observable (which asserts "
            "the dotted form). It does NOT resolve — this is the precise "
            "verify-not-resolve discriminator the bundle exists to encode.\n"
            "\n"
            "Re-checked by audit against the observable suite, and this rival is the "
            "ONLY one of the four for which the claim holds: the F2P input is the sole "
            "input the suite both renders the banner for AND asserts the displayed host "
            "at, and it is exactly where this rival diverges. The other three rivals "
            "diverge only on inputs the suite leaves unasserted, and their refinements "
            "now say so rather than claiming a test failure."
        ),
        "rationale": (
            "REJECT from the SHORTHAND clause `rawIpv6 = false → addr = \"0\" → "
            "result = \"0.0.0.0\"`: at rawIpv6=false, addr=\"0\" the spec demands "
            "\"0.0.0.0\" but the rival returns \"0\". Refuted on the shorthand "
            "sub-domain, with rawIpv6 held at false. If it verified => SPEC-TOO-WEAK "
            "(the bundle would no longer sense the change it exists to encode)."
        ),
        "witness": (
            "-- Refuted at the F2P input (rawIpv6=false, addr=\"0\"): the shorthand\n"
            "-- host must be shown in its dotted form, but the pre-patch impl echoes\n"
            "-- it verbatim.\n"
            "example : ¬ problem_spec_displayAddr false \"0\"\n"
            "    (implementation_displayAddr false \"0\") := by\n"
            "  unfold problem_spec_displayAddr implementation_displayAddr\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-close-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_CLOSE),
        "refinement": (
            "dropping the closing terminator yields an unbalanced host part (\"[\" "
            "prefix with no matching close), so a faithful patch of this shape renders "
            "a malformed URL authority for every raw-IPv6 host.\n"
            "\n"
            "HONEST SCOPE (corrected by audit — the earlier text claimed this rival "
            "FAILS the pre-existing bracketed-IPv6 cases, and that is FALSE). Those "
            "cases assert the RESOLVED bind host and the flags, not the displayed "
            "string, and they stub out the server-start step so the banner line is "
            "never even rendered; the whole observable set contains exactly one "
            "assertion on the displayed host, and it is the F2P one, which this rival "
            "agrees with. Re-measured: the rival diverges from the modeled behaviour on "
            "2 inputs the suite REACHES (the raw-literal hosts) and on 0 that it "
            "ASSERTS. So this is NOT a verify-not-resolve discriminator and is not "
            "offered as one.\n"
            "\n"
            "It is included on the narrower basis that it is an observable divergence "
            "on a reachable input the suite leaves unasserted — the bracket clause's "
            "BODY, which no other rival attacks and which a spec must pin even where "
            "the tests are silent."
        ),
        "rationale": (
            "REJECT from the BRACKET clause `rawIpv6 = true → result = \"[\" ++ addr "
            "++ \"]\"`: at rawIpv6=true, addr=\"0\" the spec demands \"[0]\" but the "
            "rival returns \"[0\". Refuted on the raw-IPv6 sub-domain, varying rawIpv6 "
            "to true (off the value the other two rivals use). If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted on a raw-IPv6 host (rawIpv6=true): the wrap must be balanced,\n"
            "-- but the rival omits the closing terminator.\n"
            "example : ¬ problem_spec_displayAddr true \"0\"\n"
            "    (implementation_displayAddr true \"0\") := by\n"
            "  unfold problem_spec_displayAddr implementation_displayAddr\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-gut-identity-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_GUT_IDENTITY),
        "refinement": (
            "gutting the identity branch to the empty string returns \"\" for every "
            "non-bracket, non-shorthand host — every ordinary hostname / IPv4 the "
            "command can pass — so a faithful patch of this shape renders a banner with "
            "a missing host part.\n"
            "\n"
            "HONEST SCOPE (corrected by audit — the earlier text claimed this rival "
            "FAILS the pre-existing verbatim-address cases, and that is FALSE). Those "
            "cases assert the RESOLVED bind host and the flags, not the displayed "
            "string, and most of them stub out the server-start step so the banner is "
            "never rendered; the one pre-existing case that does render it asserts only "
            "whether a system-checks line is present. Re-measured: the rival diverges "
            "from the modeled behaviour on 4 inputs the suite REACHES and on 0 that it "
            "ASSERTS. So this is NOT a verify-not-resolve discriminator and is not "
            "offered as one.\n"
            "\n"
            "It is included on the narrower basis that it is an observable divergence "
            "on reachable inputs the suite leaves unasserted — it is the only rival "
            "attacking the identity clause, the widest sub-domain of the three."
        ),
        "rationale": (
            "REJECT from the IDENTITY clause `rawIpv6 = false → addr ≠ \"0\" → result "
            "= addr`: at rawIpv6=false, addr=\"127.0.0.1\" the spec demands "
            "\"127.0.0.1\" but the rival returns \"\". Refuted on the identity "
            "sub-domain, varying addr to an ordinary host (off the \"0\" the other "
            "rivals use). If it verified => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted on an ordinary host (rawIpv6=false, addr=\"127.0.0.1\"): the\n"
            "-- host must be shown verbatim, but the gutted branch drops it.\n"
            "example : ¬ problem_spec_displayAddr false \"127.0.0.1\"\n"
            "    (implementation_displayAddr false \"127.0.0.1\") := by\n"
            "  unfold problem_spec_displayAddr implementation_displayAddr\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-swap-guard-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP_PRECEDENCE),
        "refinement": (
            "the two guards are REORDERED: the shorthand test is made first, so the "
            "bracket rule is reached only for a host that is not the shorthand. Every "
            "other rival here breaks ONE clause on a sub-domain where the other guard "
            "is inactive; this one keeps all three branch BODIES intact and breaks "
            "only their PRECEDENCE, so it is refutable exclusively at the input where "
            "both guards fire (rawIpv6=true, addr=\"0\").\n"
            "\n"
            "HONEST SCOPE OF THIS RIVAL (checked against the suite, not asserted): "
            "unlike the other three, a faithful patch of this shape is NOT sensed by "
            "the observable test set. It agrees with the frozen behaviour on the F2P "
            "input and on every raw-literal host the pre-existing cases exercise "
            "(those hosts are \"::1\", \"::\", and a full 2001:db8 literal — none is "
            "the one-character text \"0\", so the reordered guard never fires early "
            "for them). So this case is NOT a verify-not-resolve discriminator and is "
            "not offered as one.\n"
            "\n"
            "It is included because it is nonetheless an OBSERVABLE divergence from "
            "the modeled real behaviour on a reachable input — a resolved host whose "
            "text is \"0\" reached with the raw-literal flag set (the flag is set by "
            "upstream bracket parsing, which is independent of the host's text, so the "
            "combination is reachable at this function's boundary). mapping.md binds "
            "the modeled inputs as arbitrary for exactly this reason, and the frozen "
            "spec pins that input to the bracketed form, agreeing with the real "
            "post-fix code. The rival returns the expanded shorthand instead. The case "
            "therefore probes whether the spec pins the CLAUSE PRECEDENCE that the "
            "test suite happens to leave unobserved — a gap in the tests is exactly "
            "where a spec has to be stronger than its tests, so this is the rival that "
            "keeps the bracket clause from being weakened to "
            "`rawIpv6 = true → addr ≠ \"0\" → …` without any test noticing."
        ),
        "rationale": (
            "REJECT from the BRACKET clause `rawIpv6 = true → result = \"[\" ++ addr "
            "++ \"]\"`, which is UNCONDITIONAL in `addr`: at rawIpv6=true, addr=\"0\" "
            "the spec demands \"[0]\" (the bracket rule takes precedence over the "
            "shorthand rule) but the rival returns \"0.0.0.0\". This is the only rival "
            "that probes the INTERACTION of two clauses rather than one clause in "
            "isolation — it is why the spec's bracket clause may not be weakened to "
            "`rawIpv6 = true → addr ≠ \"0\" → …`. If it verified => SPEC-TOO-WEAK "
            "(clause precedence unpinned)."
        ),
        "witness": (
            "-- Refuted where BOTH guards fire (rawIpv6=true, addr=\"0\"): the bracket\n"
            "-- rule takes precedence, so the result must be the bracketed host and\n"
            "-- not the expanded shorthand.\n"
            "example : ¬ problem_spec_displayAddr true \"0\"\n"
            "    (implementation_displayAddr true \"0\") := by\n"
            "  unfold problem_spec_displayAddr implementation_displayAddr\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the derivation is primitive
# string formatting over the two inputs, so there is no in-model axiom
# obligation for the PBT axiom lane to re-discharge (and the axiom lane belongs
# to G-AX in any case).
AXIOM_TESTS = []
