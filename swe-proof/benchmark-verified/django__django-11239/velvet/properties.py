"""properties.py — G-PBT falsification battery for django__django-11239 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region is changed — which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct clientEnv`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method over five read-only option values, each
a ``List Char`` that is SET (non-empty) or UNSET (the empty list). It returns the
list of forwarded ``(name, value)`` entries and carries ONE load-bearing
post-image:

    clientEnv password sslmode sslrootcert sslcert sslkey
        ensures out = forwardedEnv password sslmode sslrootcert sslcert sslkey

``forwardedEnv`` is the in-order concatenation of the five per-option
contributions, each ``forwardOne name value = if value ≠ [] then [(name,value)]
else []``. So this single equality pins ALL of the sibling's separate clauses at
once, and pins them more tightly than the sibling did:

  * PRESENCE — an option's entry is present iff its value is non-empty (the
    sibling's five biconditionals ``(Bx)``);
  * VALUE — when present, the entry carries the option value verbatim (``(Vx)``);
  * NAME — each option contributes under its OWN canonical name, never another's
    (the sibling's cross-wiring guard);
  * NO-SPURIOUS — the result equals EXACTLY the concatenation of the five
    contributions, so no entry outside the five may appear (the sibling's ``(NS)``
    forall);
  * ORDER — the five contributions appear in source order (password first, then
    the four transport-security options). This clause is STRICTLY STRONGER THAN
    THE REPO BEHAVIOUR and is a recorded over-constraint of the frozen spec, not
    a property of the defended surface. The real observable is an
    ORDER-IMMATERIAL mapping (mapping.md §2 says so in as many words: "the test
    compares the forwarded mapping as a set/dict, so order is immaterial"), and
    the sibling models it as a dict, which is why its reorder positive is a
    CORRECT impl there. Because this carrier is an ordered ``List`` and the
    post-image is a list equality, a faithful impl that forwards the same five
    options in a different order is REJECTED even though its real counterpart
    passes every test. Measured, not argued — see the accounting footer and the
    SPEC-OVER-CONSTRAINT note there. No case below relies on the ORDER facet;
    the battery neither exploits nor certifies it.

The five option values are the sole INPUT BINDERS. All are read-only (none
``mut``). Every reject witness below varies them: five witnesses set exactly one
of the five binders, one sets NONE of them (the all-unset corner), and one sets
TWO to distinct values, so no binder is held at one value by every rival and the
variation changes the spec's verdict at each point (pts = 5).

ADVERSARIAL READ of the sibling's classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling's MANDATORY probe
    writes back onto an input held at a fractional heap permission and is
    rejected for INSUFFICIENT PERMISSION. This backend is referentially
    transparent: every parameter is an immutable value, this bundle declares no
    ``mut`` binder on any of the five options, there is no heap and no aliasing —
    so there is no read-only input to overwrite and no substitute probe to build.
    Not fabricated (spec_guide directive 5: the read-only frame obligation is
    discharged here by the ABSENCE of a ``mut`` on the option binders, which the
    frozen spec already encodes structurally).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully-unfolded
    function (``forwardedEnv``/``forwardOne`` are concrete ``def``s in the
    ``pure`` region; the ``axioms`` region declares nothing). There is no opaque
    answer key to echo — evaluating ``forwardedEnv`` IS the work — so honest
    cheapest-reshape positive controls stand in.
  * PRESENCE / VALUE / NAME / NO-SPURIOUS — all APPLY and are attacked below.
  * ADMISSIBILITY / PRECOND-TOO-STRONG — APPLIES, re-aimed, and LANDED (see
    `admiss-post-image-nondegenerate`). The frozen method has no `require`, so the
    sibling's "a normal input establishes the precondition" shape claims nothing
    here; the analogue that bites on a total carrier is the obligation being
    UNSATISFIABLE or DEGENERATE at a concretely interesting input, which a
    positive discharging it AT that input tests directly. Earlier waves recorded
    this lane as vacuous on the ground that the soundness positives already
    demonstrate satisfiability — measured FALSE by wave a7b: a positive discharges
    a universally-quantified equation and never pins the post-image's VALUE
    anywhere, so it passes whether or not the spec is degenerate at the failing
    scenario's own shape.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery: ``clientEnvTester
<five args> = false`` says the extracted program's result violates the method's
postcondition at that concrete input. Checked in a file whose ``prove_correct``
block has been stripped, so no tactic script can mask the verdict. There is no
``require`` clause, so the precondition is ``True`` and decides trivially. Every
witness input is a concrete ``List Char`` literal so the tester reduces under
``decide``; no ``sorry``/``admit``/``native_decide``/``axiom``.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the construction is a
closed function of the five values — no callee is owed a contract). The gate
ignores ``AXIOM_TESTS`` regardless; the sibling's AXIOM_TESTS are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-11239"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one impl region and is
# ---- unique inside Solution.lean; both facts asserted at load by _swap) ----

# The whole executable body: init the empty forwarded set, then five guarded
# appends in source order, then return. Reshaped wholesale by the positives and
# the prepatch rival; edited surgically by the targeted rivals.
_IMPL = (
    "    let mut env : List Entry := []\n"
    "    if password ≠ [] then\n"
    "      env := env ++ [(\"password\", password)]\n"
    "    if sslmode ≠ [] then\n"
    "      env := env ++ [(\"sslmode\", sslmode)]\n"
    "    if sslrootcert ≠ [] then\n"
    "      env := env ++ [(\"sslrootcert\", sslrootcert)]\n"
    "    if sslcert ≠ [] then\n"
    "      env := env ++ [(\"sslcert\", sslcert)]\n"
    "    if sslkey ≠ [] then\n"
    "      env := env ++ [(\"sslkey\", sslkey)]\n"
    "    return env\n"
)

# The accumulator initializer (unique). Anchor for the no-spurious rival.
_INIT = "    let mut env : List Entry := []\n"

# The password append line (unique). Anchor for the value-clause rival.
_PW_APPEND = "      env := env ++ [(\"password\", password)]\n"

# The sslmode guarded branch (unique). Anchor for the cross-wiring rival.
_SSLMODE_BRANCH = (
    "    if sslmode ≠ [] then\n"
    "      env := env ++ [(\"sslmode\", sslmode)]\n"
)

# The sslcert guarded branch (unique). Removed by the cross-wiring rival.
_SSLCERT_BRANCH = (
    "    if sslcert ≠ [] then\n"
    "      env := env ++ [(\"sslcert\", sslcert)]\n"
)

# The sslkey guarded branch (unique). Removed by the partial-domain rival.
_SSLKEY_BRANCH = (
    "    if sslkey ≠ [] then\n"
    "      env := env ++ [(\"sslkey\", sslkey)]\n"
)

# The sslcert append line (unique). Anchor for the value-crosswire rival.
_SSLCERT_APPEND = "      env := env ++ [(\"sslcert\", sslcert)]\n"

# The sslkey append line (unique). Anchor for the value-crosswire rival.
_SSLKEY_APPEND = "      env := env ++ [(\"sslkey\", sslkey)]\n"


# ---- witness preamble. Velvet's tester machinery: `clientEnvTester <args> =
# ---- false` at a concrete point means the extracted program violates the
# ---- method's postcondition there. Appended to a file whose `prove_correct`
# ---- block has been stripped, so the frozen tactic script cannot interfere. ----
_TESTER = (
    "extract_program_for clientEnv\n"
    "prove_precondition_decidable_for clientEnv\n"
    "prove_postcondition_decidable_for clientEnv\n"
    "derive_tester_for clientEnv\n\n"
)


# ---- positive-control bodies (structurally different but CORRECT) ----

# (P1) BRANCHLESS reshape. Drop the five `if` guards and append each option's
# per-option contribution unconditionally via `forwardOne` (which carries the
# same set-then-keep rule inside it). The result is definitionally the same
# in-order concatenation as `forwardedEnv`, so the post-image holds and the
# frozen proof (`loom_solve <;> simp_all [forwardedEnv, forwardOne]`) discharges
# unchanged. If a correct branchless reshape cannot verify => SPEC-TOO-STRONG
# (over-fit to the guarded-append form).
_POS_BRANCHLESS = (
    "    let mut env : List Entry := []\n"
    "    env := env ++ forwardOne \"password\" password\n"
    "    env := env ++ forwardOne \"sslmode\" sslmode\n"
    "    env := env ++ forwardOne \"sslrootcert\" sslrootcert\n"
    "    env := env ++ forwardOne \"sslcert\" sslcert\n"
    "    env := env ++ forwardOne \"sslkey\" sslkey\n"
    "    return env\n"
)

# (P2) LOCAL-RESHAPE. For each option read the value into a typed local first,
# then append it — a read-then-write data shape instead of the inline append.
# Same order, same behaviour. If it cannot verify => SPEC-TOO-STRONG (over-fit
# to the inline-write form). Mirrors the sibling's local-reshape positive.
_POS_LOCAL = (
    "    let mut env : List Entry := []\n"
    "    if password ≠ [] then\n"
    "      let p : List Char := password\n"
    "      env := env ++ [(\"password\", p)]\n"
    "    if sslmode ≠ [] then\n"
    "      let m : List Char := sslmode\n"
    "      env := env ++ [(\"sslmode\", m)]\n"
    "    if sslrootcert ≠ [] then\n"
    "      let r : List Char := sslrootcert\n"
    "      env := env ++ [(\"sslrootcert\", r)]\n"
    "    if sslcert ≠ [] then\n"
    "      let c : List Char := sslcert\n"
    "      env := env ++ [(\"sslcert\", c)]\n"
    "    if sslkey ≠ [] then\n"
    "      let k : List Char := sslkey\n"
    "      env := env ++ [(\"sslkey\", k)]\n"
    "    return env\n"
)


# ---- admissibility prefix (ADDED BY AUDIT wave a7b) ----

# An in-region `assert`, discharged BY EVALUATION at concrete option values,
# that the post-image is SATISFIABLE and NON-DEGENERATE at exactly the shape the
# failing scenario has: the four transport-security options all SET (to distinct
# values) with the credentials option UNSET, plus the all-unset corner. It is
# prepended before the accumulator initializer so the frozen body — and hence the
# method's own `ensures` — still discharges verbatim underneath it. The frozen
# tactic body needs no retune (measured): `loom_solve <;> simp_all [forwardedEnv,
# forwardOne]` closes the extra goal as well.
#
# This is the PRECOND-TOO-STRONG lane, re-aimed for a total carrier. The method
# carries no `require`, so "a normal input satisfies the precondition" would
# indeed claim nothing — but that is NOT a reason to drop the lane, and the
# analogue that does bite here is the obligation being UNSATISFIABLE or
# DEGENERATE at an interesting input. A spec no impl can meet reads exactly like
# a spec every impl meets, and neither the two soundness positives nor any rival
# detects it: the positives discharge a UNIVERSALLY-quantified equation whose
# every instance could in principle be vacuous, while a rival only ever shows
# some impl FAILS. Only pinning the post-image's value at a concrete point rules
# that out.
#
# The assert is LIVE, not decoration: measured, a variant asserting the same
# equation with the client-key entry dropped from the right-hand side fails with
# `unsolved goals … case «admiss_1: …» ⊢ False` (exit 1). So the case can only
# pass by the post-image genuinely evaluating to the four-entry forwarded set.
_ADMISS_PREFIX = (
    "    assert (with_name_prefix `admiss\n"
    "      (forwardedEnv [] ['v'] ['r'] ['c'] ['k']\n"
    "        = [(\"sslmode\", ['v']), (\"sslrootcert\", ['r']),\n"
    "           (\"sslcert\", ['c']), (\"sslkey\", ['k'])]\n"
    "       ∧ forwardedEnv [] [] [] [] [] = []))\n"
)


# ---- reject bodies ----

# (R1 prepatch) Forward ONLY the credentials option and never the four
# transport-security options — the pre-fix behaviour.
_RIVAL_PREPATCH = (
    "    let mut env : List Entry := []\n"
    "    if password ≠ [] then\n"
    "      env := env ++ [(\"password\", password)]\n"
    "    return env\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify, else SPEC-TOO-STRONG. Each keeps the identical
    # `prove_correct clientEnv` statement and the frozen tactic body.
    # =====================================================================
    {
        "id": "pos-branchless-forwardone",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_BRANCHLESS),
        "rationale": "a correct BRANCHLESS reshape: each option's contribution is "
                     "appended unconditionally through the per-option rule "
                     "(`forwardOne`), whose own set-then-keep test recovers the "
                     "guard. The accumulated result is definitionally the same "
                     "in-order concatenation as `forwardedEnv`, so "
                     "`out = forwardedEnv …` holds and the frozen proof discharges "
                     "unchanged; must verify, else the spec is over-fit to the "
                     "guarded-append form => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_LOCAL),
        "rationale": "a correct read-then-write reshape: each option value is read "
                     "into a typed local then appended (instead of the inline "
                     "append). Same order, same result, so the post-image holds; "
                     "must verify, else the spec is over-fit to the inline-write "
                     "form => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane) — ADDED BY AUDIT wave a7b. The
    # port dropped this lane as "vacuous because the frozen obligation has no
    # precondition", which is the one reason that does NOT carry: the analogue on
    # a total carrier is the obligation being unsatisfiable/degenerate at a
    # concretely interesting input, and a positive that discharges it AT that
    # input tests it directly. Measured to land: exit 0 with the frozen tactic
    # body unchanged, and its false-claim control fails at the assert goal.
    # =====================================================================
    {
        "id": "admiss-post-image-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INIT, _ADMISS_PREFIX + _INIT),
        "rationale": "the post-image is SATISFIABLE and NON-DEGENERATE at exactly "
                     "the shape the failing scenario has: with the four "
                     "transport-security options set to DISTINCT values and the "
                     "credentials option unset, `forwardedEnv` evaluates to the "
                     "full four-entry forwarded set — each option under its own "
                     "name carrying its own value — and at the all-unset corner it "
                     "evaluates to the empty set. Both are discharged by "
                     "EVALUATION as an in-region `assert`, before the frozen body "
                     "closes the method's own `ensures` verbatim underneath. This "
                     "is the lane the two soundness positives cannot cover: they "
                     "discharge a universally-quantified equation, every instance "
                     "of which could in principle be vacuous, whereas a rival only "
                     "shows some impl FAILS. If the obligation could not be "
                     "discharged at this concrete in-domain point => "
                     "PRECOND-TOO-STRONG (a spec no impl can meet at the "
                     "interesting input reads exactly like a spec every impl "
                     "meets). The assert is LIVE: asserting the same equation with "
                     "the client-key entry dropped from the right-hand side leaves "
                     "`⊢ False` on the `admiss_1` goal (measured, exit 1), so this "
                     "case can only pass by the post-image genuinely evaluating to "
                     "the four-entry set.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each witness sets a
    # DIFFERENT one of the five option binders non-empty (pts = 5).
    # =====================================================================
    {
        "id": "rival-prepatch-only-credentials",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _RIVAL_PREPATCH),
        "refinement": "forwards ONLY the credentials option and never the four "
                      "transport-security options — the pre-fix behaviour. Its "
                      "faithful real counterpart forwards no transport-security "
                      "option, so a TLS-configured connection has an EMPTY forwarded "
                      "set where the failing test demands all four entries: the "
                      "assertEqual observes {} instead of the four-entry mapping and "
                      "FAILS. It would NOT resolve (this is exactly the bug the "
                      "change fixes).",
        "rationale": "REJECT from the PRESENCE facet of `out = forwardedEnv …`: "
                     "whenever a transport-security option is set the equality "
                     "requires its entry, which the rival never emits. Refuted at "
                     "the point where `sslrootcert` alone is set — the rival returns "
                     "the empty forwarded set while the spec requires "
                     "`[(\"sslrootcert\", …)]`. Probes the `sslrootcert` binder.",
        "witness": _TESTER +
                   "example : clientEnvTester [] [] ['r'] [] [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-drop-sslkey",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SSLKEY_BRANCH, ""),
        "refinement": "PARTIAL-DOMAIN: forwards the credentials option and the first "
                      "three transport-security options correctly but OMITS the "
                      "client-key option — a partial feature implementation. Its "
                      "faithful counterpart forgets that one option, so a connection "
                      "that configures the client key gets a forwarded set MISSING "
                      "that entry: the failing test asserts the full four-entry "
                      "mapping and FAILS. It would NOT resolve.",
        "rationale": "REJECT from the PRESENCE facet: when `sslkey` is set the "
                     "equality requires its entry, which the rival dropped. Refuted "
                     "at the point where `sslkey` alone is set — the rival returns "
                     "the empty set while the spec requires `[(\"sslkey\", …)]`. "
                     "Probes the `sslkey` binder.",
        "witness": _TESTER +
                   "example : clientEnvTester [] [] [] [] ['k'] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-spurious-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Seed the forwarded set with an entry under a name outside the five, then
        # forward the five correctly. Everything the spec wants is present, but so
        # is one extra entry.
        "module": _swap(_BASE, _INIT,
                        "    let mut env : List Entry := [(\"extra\", ['X'])]\n"),
        "refinement": "forwards all five options correctly but ALSO emits one extra "
                      "entry under a name outside the five. Its faithful counterpart "
                      "publishes some additional variable beyond the recognised set. "
                      "The failing/regression tests assert the forwarded mapping "
                      "EQUALS the exact expected set (assertEqual, not subset), so an "
                      "extra entry makes the mapping unequal and the test FAILS. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the NO-SPURIOUS facet of the equality: the result "
                     "must equal EXACTLY the concatenation of the five "
                     "contributions, so a sixth entry breaks it. Refuted at the "
                     "point where `sslmode` alone is set — the spec requires exactly "
                     "`[(\"sslmode\", …)]` but the rival prepends the extra entry. "
                     "Probes the `sslmode` binder.",
        "witness": _TESTER +
                   "example : clientEnvTester [] ['v'] [] [] [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Forward the credentials entry with a CONSTANT value instead of the
        # supplied one (presence correct, value wrong).
        "module": _swap(_BASE, _PW_APPEND,
                        "      env := env ++ [(\"password\", ['X'])]\n"),
        "refinement": "forwards the credentials entry with a fixed placeholder value "
                      "instead of the configured one (presence right, value wrong). "
                      "Its faithful counterpart forwards a constant string rather "
                      "than the configured value, so the regression test that "
                      "asserts the configured credential value observes the "
                      "placeholder and FAILS. It would NOT resolve (presence alone "
                      "does not pin the value).",
        "rationale": "REJECT from the VALUE facet of the equality: when the "
                     "credentials option is set the entry must carry its value "
                     "verbatim, but the rival carries a constant. Refuted at the "
                     "point where `password = ['p']` (≠ the constant `['X']`) — the "
                     "spec requires `[(\"password\", ['p'])]` and the rival gives "
                     "`[(\"password\", ['X'])]`. Probes the `password` binder.",
        "witness": _TESTER +
                   "example : clientEnvTester ['p'] [] [] [] [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-crosswire-sslcert",
        "kind": "uniqueness",
        "expect": "reject",
        # Cross-wire the client-certificate entry: emit it (carrying the
        # connection-mode value) inside the connection-mode branch, and drop the
        # genuine client-certificate branch. So the cert entry's presence tracks
        # the WRONG option.
        "module": _swap(
            _swap(_BASE, _SSLMODE_BRANCH,
                  "    if sslmode ≠ [] then\n"
                  "      env := env ++ [(\"sslmode\", sslmode)]\n"
                  "      env := env ++ [(\"sslcert\", sslmode)]\n"),
            _SSLCERT_BRANCH, ""),
        "refinement": "CROSS-WIRES the client-certificate entry: it is emitted from "
                      "the connection-mode branch carrying the connection-mode "
                      "value, and the genuine client-certificate branch is dropped. "
                      "So the cert entry's presence and value track the wrong "
                      "option. Its faithful counterpart is a copy-paste wiring bug; "
                      "under the failing test (which configures BOTH options) the "
                      "cert entry carries the connection-mode value, not the cert "
                      "path: the assertEqual FAILS. It would NOT resolve. Pins that "
                      "each option maps to its OWN name.",
        "rationale": "REJECT from the NAME/PRESENCE facet: the client-certificate "
                     "entry must be present iff THAT option is set, and carry ITS "
                     "value. Refuted at the point where `sslcert = ['c']` is set and "
                     "the connection-mode option is UNSET — the spec requires "
                     "`[(\"sslcert\", ['c'])]`, but the rival (cert entry only fires "
                     "from the mode branch, which is skipped) returns the empty set. "
                     "Probes the `sslcert` binder.",
        "witness": _TESTER +
                   "example : clientEnvTester [] [] [] ['c'] [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-unguarded-sslmode",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the SET test on the connection-mode option: emit its entry
        # unconditionally, so an UNCONFIGURED option is still forwarded (with the
        # empty value). Attacks the "iff" in the presence biconditional from the
        # side the existing rivals leave open: they all DROP an entry that is
        # owed, this one ADDS an entry that is not.
        "module": _swap(_BASE, _SSLMODE_BRANCH,
                        "    env := env ++ [(\"sslmode\", sslmode)]\n"),
        "refinement": "forwards the connection-mode option UNCONDITIONALLY — the "
                      "set-then-keep test is dropped, so the entry appears even when "
                      "the option was never configured. Its faithful counterpart "
                      "forwards the option with no truthiness test at all, so a "
                      "connection that configures NO transport-security option still "
                      "gets a mode entry (carrying the empty value). The regression "
                      "test for the unconfigured case asserts the forwarded mapping "
                      "equals EXACTLY the expected set, which for that connection "
                      "contains no mode entry, so the assertEqual observes an extra "
                      "entry and FAILS. It would NOT resolve.",
        "rationale": "REJECT from the PRESENCE facet in its NEGATIVE direction: "
                     "`forwardOne` contributes NOTHING when the value is empty, so "
                     "the equality forbids the entry for an unset option. Refuted at "
                     "the point where ALL FIVE options are unset — the spec requires "
                     "the empty forwarded set, but the rival returns "
                     "`[(\"sslmode\", [])]`. The only witness here that holds every "
                     "binder empty. AUDIT-CORRECTED: an earlier draft said every "
                     "other rival AGREES with the spec at the all-unset point. "
                     "Measured false — `rival-spurious-entry` seeds its extra entry "
                     "UNCONDITIONALLY, so it violates the equality there too (its "
                     "witness at that point elaborates, exit 0). What is true, and "
                     "is what this case contributes, is the FACET: the six other "
                     "rivals all break the equality by getting one of the FIVE "
                     "per-option contributions wrong (missing, mis-valued, "
                     "mis-named) or by adding a SIXTH entry outside the five, "
                     "whereas this rival is the only one whose own five "
                     "contributions are individually right and which is refuted "
                     "solely because the set-then-keep TEST is gone — the negative "
                     "direction of the presence biconditional.",
        "witness": _TESTER +
                   "example : clientEnvTester [] [] [] [] [] = false := by\n"
                   "  decide\n",
    },
    {
        "id": "rival-swap-cert-key-values",
        "kind": "uniqueness",
        "expect": "reject",
        # Both entries are present under the RIGHT names and gated on the RIGHT
        # options; only the two VALUES are exchanged. Strictly sharper than
        # rival-crosswire-sslcert, whose entry also went missing.
        "module": _swap(
            _swap(_BASE, _SSLCERT_APPEND,
                  "      env := env ++ [(\"sslcert\", sslkey)]\n"),
            _SSLKEY_APPEND,
            "      env := env ++ [(\"sslkey\", sslcert)]\n"),
        "refinement": "SWAPS the two values: the client-certificate entry carries the "
                      "key value and the key entry carries the certificate value. "
                      "Presence and names are both correct — only the payloads are "
                      "exchanged. Its faithful counterpart is a copy-paste bug that "
                      "reads the wrong variable on two adjacent lines; the failing "
                      "test configures BOTH options to DISTINCT values and asserts "
                      "each entry carries its own, so both entries are wrong and the "
                      "assertEqual FAILS. It would NOT resolve.",
        "rationale": "REJECT from the VALUE facet at a point NO other rival reaches: "
                     "`rival-wrong-value` substitutes a constant (detectable from one "
                     "binder alone) and `rival-crosswire-sslcert` makes an entry "
                     "DISAPPEAR, so both are already caught by presence-shaped "
                     "reasoning. This rival emits exactly the right names for exactly "
                     "the right options, so only the value pairing can refute it. "
                     "Refuted where `sslcert = ['c']` and `sslkey = ['k']` are both "
                     "set to DIFFERENT values — the spec requires "
                     "`[(\"sslcert\", ['c']), (\"sslkey\", ['k'])]` and the rival "
                     "gives the two values exchanged. Note a witness setting them to "
                     "the SAME value would NOT discriminate; the two binders vary "
                     "together here for that reason.",
        "witness": _TESTER +
                   "example : clientEnvTester [] [] [] ['c'] ['k'] = false := by\n"
                   "  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, and 6 uniqueness — the mandatory frame-mutation
# probe plus prepatch-only-password, drop-sslkey, spurious-key, wrong-value and
# crosswire-sslcert). Plus 2 AXIOM_TESTS. (AUDIT-CORRECTED: the header previously
# said "8 SPEC cases … 4 uniqueness rivals" while its own parenthetical then
# listed five and counted the frame probe separately; the manifest enumerates 9
# and 6. An arithmetic slip in the prose only — the mapping below always listed
# every sibling case, and nothing was left unaccounted for.) All accounted for:
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------
#   pos-reorder (5a)                 -> (none)                     DROPPED — see below
#   pos-local-reshape (5b)           -> pos-local-reshape          PORTED
#   admiss-selfcall (6)              -> admiss-post-image-nondegenerate  RE-AIMED
#                                                                  (see below)
#   rival-frame-mutate-input         -> (none)                     VACUOUS (frame)
#   rival-prepatch-only-password     -> rival-prepatch-only-credentials  PORTED
#   rival-drop-sslkey                -> rival-drop-sslkey          PORTED
#   rival-spurious-key               -> rival-spurious-entry       PORTED
#   rival-wrong-value                -> rival-wrong-value          PORTED
#   rival-crosswire-sslcert          -> rival-crosswire-sslcert    PORTED
#   ax-publication-sound             -> (none)                     DROPPED (axiom lane)
#   ax-publication-containment       -> (none)                     DROPPED (axiom lane)
#
# Added: pos-branchless-forwardone (a second structural positive, no sibling twin
#   — it exercises the `forwardOne` per-option rule directly, the shape closest to
#   the pure model).
#
# DROPPED as a CASE, RECORDED as a SPEC OVER-CONSTRAINT — pos-reorder (5a).
#   The sibling models the observable as an ORDER-IMMATERIAL dict, so forwarding
#   the five options in reverse order is a CORRECT impl there. It cannot ship as
#   an `expect="verify"` case here, because it does not verify: measured, exit 1,
#   `unsolved goals` on `ensures_1: out = forwardedEnv …`, the guards all
#   discharged and only the list ORDER left unequal.
#
#   The honest reading of that measurement is NOT "order is part of the
#   observable on this carrier". It is that the frozen post-image is STRONGER
#   THAN THE BEHAVIOUR BEING DEFENDED. The evidence is in this bundle's own
#   documentation: mapping.md §2 records the forwarded set as "order-preserving;
#   the test compares the forwarded mapping as a set/dict, so order is
#   immaterial", and conformance_check.py compares ORACLE and SHADOW as `dict`s,
#   so G-CONF would not notice a reordering either. A reordering impl is
#   therefore a FAITHFUL impl of the defended behaviour that the frozen spec
#   rejects — the SPEC-TOO-STRONG direction, on the one facet of the equality
#   that has no counterpart in the repo.
#
#   Recorded here rather than repaired: fixing it means weakening the post-image
#   to an order-insensitive comparison (a permutation or multiset equality, both
#   expressible on this carrier), which edits the frozen `Solution.lean` and must
#   re-clear the equivalence, conformance and panel gates. That is outside this
#   lane, so it is ESCALATED as a spec finding and no case here depends on the
#   ORDER facet. Severity is bounded: the over-constraint can only cause a
#   correct impl to be REJECTED (a lost resolve, never a false verify), so it
#   cannot mint an unsound pass. pos-local-reshape + pos-branchless-forwardone
#   are the two order-preserving structural positives that DO port.
#
# RE-AIMED — admiss-selfcall (6) -> admiss-post-image-nondegenerate.
#   CORRECTED BY AUDIT WAVE a7b. Earlier waves recorded this lane as VACUOUS on
#   two grounds; the first is right about the SIBLING's case and wrong about the
#   LANE, and the second was simply false.
#
#   What is true: the sibling's own case shape does not port. It self-calls the
#   function to establish the callee's half-permission `Requires`; this method has
#   NO `require` clause, so "a normal input establishes the precondition" claims
#   nothing here, and the self-call does not even elaborate (`fail to show
#   termination for clientEnv … it is unchanged in the recursive calls`, plus a
#   cascading `Tactic 'unfold' failed to unfold 'clientEnv'` — measured, exit 1).
#
#   What was FALSE: that the residual risk "does not arise" because the two
#   soundness positives already demonstrate satisfiability. They do not. A
#   positive discharges the UNIVERSALLY-QUANTIFIED equation `∀ inputs, out =
#   forwardedEnv …`, and a spec can be degenerate at the interesting point while
#   still being dischargeable everywhere — the positives would pass either way,
#   because they never pin the post-image's VALUE anywhere. A rival is no help in
#   the other direction: it only shows some impl FAILS. So the lane that detects
#   PRECOND-TOO-STRONG was carried by NO case, and dropping it removed one of the
#   three directions this gate exists to test. The coverage reporter says so in as
#   many words (`kind lane 'admissibility' is in the nagini sibling but in no case
#   here … not PRECOND-TOO-STRONG`).
#
#   So the lane is LANDED, re-aimed at the analogue that bites on a total
#   carrier: the obligation being UNSATISFIABLE or DEGENERATE at a concretely
#   interesting input. The case discharges, by EVALUATION, an in-region `assert`
#   that `forwardedEnv` at the failing scenario's own shape (the four
#   transport-security options set to DISTINCT values, credentials unset) equals
#   the full four-entry forwarded set, and equals the empty set at the all-unset
#   corner — then closes the frozen obligation verbatim underneath. Measured: exit
#   0 with the frozen tactic body UNCHANGED (no retune needed), and the assert is
#   live — the same variant asserting the equation with the client-key entry
#   dropped from the right-hand side fails `unsolved goals … case «admiss_1: …» ⊢
#   False`, exit 1. Sibling cells that carry this lane over a no-`require` method
#   (astropy 12907 / 13236 / 14096) use the same in-region-assert shape.
#
# VACUOUS — frame-mutation: the sibling's MANDATORY probe writes back onto an
#   input held at fractional heap permission and is rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent — no heap, no aliasing,
#   and this bundle declares no `mut` binder on any of the five option values — so
#   there is no read-only input to overwrite and no substitute probe. The sibling's
#   "the input must not be mutated" obligation is structurally guaranteed by the
#   absence of `mut`, which the frozen spec already encodes (spec_guide directive
#   5). Not fabricated.
#
# DROPPED — AXIOM_TESTS: the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS. mapping.md §3 records NO axiom / no A-reference (the construction
#   is a closed function of the five values), so there is nothing to probe here
#   anyway.
#
# ADDED BY AUDIT. Two rivals close facets the ported five leave unattacked; both
#   were built and measured before being written in (rival build exit 0, gold
#   build exit 1 with `decide` refuting the concrete claim, in both cases):
#
#   rival-unguarded-sslmode — the ported five all attack presence in ONE
#     direction: an owed entry is MISSING. None attacks the other direction (an
#     entry present that is NOT owed), and no ported WITNESS reaches the all-unset
#     point: every ported witness sets some binder non-empty. So the negative half
#     of the biconditional — an unset option contributes nothing — was carried by
#     no case.
#
#     AUDIT CORRECTION (wave a6). This entry, and the case's own rationale,
#     previously added "and at the all-empty input each ported rival AGREES with
#     the spec". That is FALSE and was measured false: rival-spurious-entry seeds
#     its extra entry UNCONDITIONALLY, so it violates the post-image at the
#     all-unset point as well (this case's witness, rebuilt against the
#     spurious-entry rival, elaborates — exit 0 — where against gold it is refuted
#     by `decide`). The claim that survives measurement is about the FACET, not
#     about the point: rival-unguarded-sslmode is the only rival whose five
#     per-option contributions are each individually correct and which the
#     equality refutes purely for having dropped the set-then-keep TEST. Both
#     texts now say that instead.
#
#   rival-swap-cert-key-values — the ported VALUE attack substitutes a CONSTANT,
#     which presence-shaped reasoning already catches, and the ported NAME attack
#     makes an entry DISAPPEAR, so it is caught by presence too. Neither pins the
#     value PAIRING with names and guards all correct. This rival gets every name
#     and every guard right and exchanges only the two payloads, so nothing but
#     the value pairing can refute it. It is also the only witness that sets TWO
#     binders non-empty, and to DISTINCT values — necessarily, since equal values
#     make the swap unobservable.
#
# BINDER / WITNESS COVERAGE. Seven rivals, seven distinct witness points:
#     rival-wrong-value            password    (['p'] [] [] [] [])
#     rival-spurious-entry         sslmode     ([] ['v'] [] [] [])
#     rival-prepatch-only-cred.    sslrootcert ([] [] ['r'] [] [])
#     rival-crosswire-sslcert      sslcert     ([] [] [] ['c'] [])
#     rival-drop-sslkey            sslkey      ([] [] [] [] ['k'])
#     rival-unguarded-sslmode      ALL UNSET   ([] [] [] [] [])
#     rival-swap-cert-key-values   cert+key    ([] [] [] ['c'] ['k'])
#   So every one of the five INPUT BINDERS takes a non-empty value in some reject
#   witness and empty in the others — no binder is held at a single value by every
#   rival — and the all-unset corner plus a two-binder-distinct-values point are
#   both covered, so the variation is behaviourally MEANINGFUL and not two
#   spellings of one point. The single top-level clause `out = forwardedEnv …` is
#   attacked on each of its facets, in BOTH directions where it has two:
#   PRESENCE-missing (prepatch, drop-sslkey), PRESENCE-spurious
#   (unguarded-sslmode), VALUE-constant (wrong-value), VALUE-pairing
#   (swap-cert-key-values), NAME (crosswire), NO-SPURIOUS (spurious-entry). The
#   ORDER facet is deliberately unattacked: it is the over-constraint recorded
#   above, so a case turning on it would attest to a spec defect, not the spec.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT (wave a6) — what was re-derived, and with what exit codes.
# The port's outcomes were not trusted; every build below was re-run.
#
# STATEMENT INTEGRITY (attack A). All 9 variants diffed against the frozen file
#   line-by-line: each differs ONLY inside the `impl` region (lines 86..103) and
#   is byte-identical everywhere else, the `method clientEnv` header, the single
#   `ensures out = forwardedEnv …`, `forwardOne`/`forwardedEnv` and the
#   `prove_correct clientEnv` header all included. No case restates or reformats
#   the obligation, so no weakened hypothesis can be hiding in a reformatting.
#
# WITNESS DISCRIMINATION (attack B), all 7 reject cases rebuilt by hand:
#   rival build exit 0 / gold build exit 1 in every case, and — the part the
#   gate's exit code cannot show — each gold-side failure is a POSITIVE semantic
#   refutation, `Tactic 'decide' proved that the proposition
#   clientEnvTester <the witness point> = false is false`. Not a stuck reduction,
#   not an unknown identifier, not a type error, not a timeout. No witness binds
#   anything in its head, so no consistency probe is owed (and none is run).
#
# IS THE RIVAL WRONG, OR JUST DIFFERENT (attack C). Each of the seven differs
#   from the frozen impl OBSERVABLY at its own witness point, which is exactly
#   what its `decide`-refuted witness certifies. None is a definitional-equality
#   artifact of the carrier.
#
# SPEC-TOO-WEAK probes (attack D) — NEW wrong impls the battery does not carry.
#   All REJECTED, so none is a spec hole:
#     near-miss guard `sslmode.length > 1` (set-but-length-1 forwarded wrongly) 1
#     duplicate password entry (same entry emitted twice)                       1
#     conditional partial domain (`sslcert ≠ [] ∧ sslkey = []`)                 1
#     misspelled canonical name on the rootcert entry                          1
#     value truncated (`sslrootcert.tail`) — the VALUE facet on a binder the
#       shipped value rivals do not touch                                      1
#     spurious entry under one of the FIVE names, not an outside name           1
#
#   The last one is the interesting negative result and is deliberately NOT
#   added as a case even though it discriminates mechanically (rival 0, gold 1
#   with a clean `decide` refutation at `[] ['v'] ['r'] [] []`). It is the
#   attack-C trap: it emits a second entry under an ALREADY-USED canonical name,
#   which this carrier's ordered `List` keeps as a distinct element, but the real
#   forwarded set is keyed — the observable is a mapping — so the genuine
#   per-option entry that follows OVERWRITES it and the faithful counterpart is
#   observably EQUAL to gold at the F2P input and at the witness point alike
#   (checked both ways). Its rejection would attest to the List-vs-mapping
#   carrier gap, i.e. to the same ORDER/multiplicity over-constraint already
#   recorded above, not to the spec. A case that can only be refuted by a facet
#   the defended behaviour does not have is vacuous, so it stays out.
#
# SPEC-TOO-STRONG probes (attack E) — NEW correct reshapes:
#     return `forwardedEnv …` directly (the cheapest correct impl)      VERIFIES 0
#     PREPEND accumulation iterating the five in reverse (same final
#       order as gold, opposite data shape)                            VERIFIES 0
#     guards written `xs.length > 0` instead of `xs ≠ []`               exit 1 on
#       the frozen tactic script, but NOT a spec hole: `variant_scope`
#       permits a variant to rewrite the tactic body (only the
#       `prove_correct` header must survive), and adding a single
#       length/nil bridging lemma to the `simp_all` set closes it —
#       measured VERIFIES 0 with each of `List.length_pos_iff`,
#       `List.length_pos` and `List.length_pos_iff_ne_nil`. A tactic-hint
#       gap, reported as such rather than as a spec defect.
#     REORDERED appends (the dropped nagini pos-reorder)                exit 1,
#       and this one IS a spec-level rejection, not a tactic gap: the
#       reorder impl VIOLATES the post-image at a concrete input
#       (`['p'] ['v'] [] [] []` — its witness elaborates against the
#       reorder impl, exit 0, and is `decide`-refuted against gold,
#       exit 1). So the port's SPEC-OVER-CONSTRAINT record above is
#       CONFIRMED by independent measurement, and its disposition
#       (escalate, do not repair, ship no case depending on ORDER) is
#       right. It is a lost-resolve risk only — it can never mint a false
#       verify — and repairing it means weakening the frozen post-image
#       to a permutation/multiset equality, which is outside this lane.
#
# OMISSIONS (attack F), re-derived rather than taken on the port's word:
#     frame-mutation: CONFIRMED inexpressible. Assigning to an option binder is
#       not a permission error here, it is a COMPILE error — `password cannot be
#       mutated, only variables declared using 'let mut' can be mutated` — so
#       there is no rival to build, only an uncompilable file. The obligation is
#       discharged structurally by the absence of `mut`, as recorded.
#     admiss-selfcall: the SIBLING'S SHAPE is confirmed unbuildable (the method
#       has no `require`, and the self-call does not elaborate: `fail to show
#       termination for clientEnv … it is unchanged in the recursive calls`).
#       SUPERSEDED BY WAVE a7b on the conclusion drawn from that: "so no honest
#       admissibility case exists to port" does not follow, and was wrong. The
#       LANE ports even though the CASE does not — see
#       `admiss-post-image-nondegenerate` and the RE-AIMED note above.
#     pos-reorder: expressible and MEASURED — see attack E above. Correctly kept
#       out of SPEC_TESTS (it does not verify) and correctly recorded as a spec
#       over-constraint rather than repaired.
#     AXIOM_TESTS: this gate ignores them and the bundle declares no axiom.
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# CORRECTED BY THE AUDIT: one false prose claim (the "every other rival agrees
#   with the spec at the all-unset point" assertion in this case's rationale and
#   in the footer). No case's module, expectation or witness needed changing.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT (wave a7b) — 63 real builds, nothing taken on a prior wave's
# word. What it found, and what it changed.
#
# THE DEFECT (fixed): the battery had NO admissibility case, so of the three
#   directions this gate exists to test it tested two. Both prior waves recorded
#   that as VACUOUS, and the load-bearing half of the reason was measurably
#   false — "the two soundness positives exhibit inputs the post-image is
#   satisfiable at, so satisfiability is already demonstrated". A positive
#   discharges `∀ inputs, out = forwardedEnv …` and never pins the post-image's
#   VALUE at any point, so it passes whether or not the spec is degenerate at the
#   failing scenario's shape. LANDED as `admiss-post-image-nondegenerate`, an
#   in-region `assert` discharged by EVALUATION at the F2P-shaped input (the four
#   transport-security options set to DISTINCT values, credentials unset) plus the
#   all-unset corner, with the frozen obligation closed verbatim underneath.
#     variant build, frozen tactic body unchanged                    VERIFIES 0
#     false-claim control (client-key entry dropped from the RHS)    exit 1,
#       `unsolved goals … case «admiss_1: …» ⊢ False` — so the assert is LIVE
#       and the case cannot pass by decoration
#     variant_scope: in scope (impl-region-only; obligation preserved)
#
# WITNESS FORGERY TEST (attack B′), all 7 reject cases, 28 builds. Every
#   gold_signature here is a plain evaluation (`Tactic 'decide' proved that the
#   proposition clientEnvTester <point> = false is false`), so the forgery pair
#   was not strictly owed — run anyway, because "it looks semantic" is not
#   evidence. FLIPPED-CLAIM form: each witness's `= false` swapped for `= true`,
#   i.e. asserting the frozen impl is CORRECT at that point.
#     witness vs rival     0    |  witness vs gold      1
#     FORGERY vs gold      0    |  FORGERY vs rival     1
#   All four legs, all seven cases, no exception. Gold's exit code therefore
#   TRACKS THE CLAIM — it flips when the claim flips — which is the property that
#   makes it admissible evidence, and the forgery is refuted against the rival by
#   the mirror-image `decide` message. Not one hollow case.
#
# ATTACK D (new wrong impls, none in the battery). All REJECTED — no spec hole:
#     guard `sslmode.length = 1` (set-but-longer dropped)                       1
#     rootcert entry guarded on the credentials option instead                  1
#     the four transport values ALL carrying the credentials value              1
#     rootcert entry emitted TWICE (multiplicity)                               1
#     client-key value truncated by `dropLast` (non-constant VALUE attack)      1
#     client key forwarded under the client-CERT name (name collapse)           1
#     credentials guard INVERTED (forward iff unset)                            1
#     the three later options gated on the mode option being set too            1
#     the two order-adjacent entries emitted in swapped order                   1
#   The last is the ORDER facet and its rejection attests to the recorded
#   over-constraint, not to the spec, which is why it stays out as a case.
#
# ATTACK E (new correct reshapes). All VERIFY except where noted:
#     return `forwardedEnv …` directly                                 VERIFIES 0
#     PREPEND accumulation, five iterated in reverse, same final order VERIFIES 0
#     one concatenation expression, no accumulator                     VERIFIES 0
#     guards spelled `!xs.isEmpty` instead of `xs ≠ []`                VERIFIES 0
#       — frozen tactic body UNCHANGED. (An earlier wave reported this shape as
#       needing a bridging lemma; that was an artifact of a stray space in its
#       probe, `password .isEmpty`, which is a SYNTAX error — `Function expected
#       at password`. Re-measured correctly here: nothing to retune.)
#     `pairs.filter (fun e => e.2 ≠ [])` over the five pairs           VERIFIES 0
#       with the tactic body retuned (a `by_cases` split on the five guards).
#       Frozen body alone leaves the `List.filter` match unreduced — a
#       tactic-hint gap, NOT a spec hole: `variant_scope` lets a variant reprove.
#     REORDERED appends (the dropped nagini pos-reorder)                exit 1 and
#       SPEC-LEVEL, re-confirmed twice over: a fully case-split tactic
#       (`by_cases` on all five guards, `List.append_assoc`) still leaves
#       `⊢ False`, and a witness at `['p'] ['v'] [] [] []` elaborates against the
#       reorder impl (0) and is `decide`-refuted against gold (1). The
#       SPEC-OVER-CONSTRAINT record stands, now independently measured a second
#       time. Recorded as the SPEC-OVER-CONSTRAINT finding stated just above;
#       NOT re-filed anywhere else.
#
# ATTACK A: re-diffed all 10 variants (the 9 shipped plus the new admissibility
#   case) against the frozen file. Every one differs ONLY inside the impl region;
#   the method header, the single `ensures`, `forwardOne`/`forwardedEnv` and the
#   `prove_correct clientEnv` header are byte-identical throughout.
#
# ATTACK F: frame-mutation re-derived and CONFIRMED inexpressible with the error
#   text (`sslmode` cannot be mutated … plus a cascading `Failed to parse an
#   assertion without names: WPGen sorry`) — an uncompilable file, not a rival.
AXIOM_TESTS = []
