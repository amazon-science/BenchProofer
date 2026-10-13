"""properties.py — G-PBT falsification battery for django__django-13195 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
all three ``prove_correct`` headers survive) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE — THREE contracted methods, one shared precondition. Each
routine acts ON a response that already has `filed` clearing directives on it and
returns what is on file afterwards, so the obligation is ONE equation between
records rather than a list of clauses about a single returned value:

  deleteCookie (filed : Filed) (key path : String) (domain samesite : Option String)
      -> Filed
    require acceptedPolicy samesite
    require recordableKey key
    require domainStated domain
    ensures out = fileDirective filed
                    (mkCookie key (secureForClear key samesite) samesite path domain)

  clearMessageCookie (filed : Filed) (cookieName : String)
      (domain configuredPolicy : Option String) -> Filed
    require acceptedPolicy configuredPolicy
    require recordableKey cookieName
    require domainStated domain
    ensures out = fileDirective filed
                    (mkCookie cookieName
                      (secureForClear cookieName configuredPolicy)
                      configuredPolicy "/" domain)

  clearSessionCookie (filed : Filed) (sessionName path : String)
      (domain configuredPolicy : Option String) -> Filed
    require acceptedPolicy configuredPolicy
    require recordableKey sessionName
    require domainStated domain
    ensures out = fileDirective filed
                    (mkCookie sessionName
                      (secureForClear sessionName configuredPolicy)
                      configuredPolicy path domain)

with, in the ``pure`` region,

  secureForClear key s      = hasSecurePrefix key || crossSiteUnrestricted s
  hasSecurePrefix key       = key.startsWith "__Secure-" || key.startsWith "__Host-"
  crossSiteUnrestricted     = (some v => v.toLower == "none" | none => false)
  acceptedPolicy            = the accepted cross-site-policy domain (a require)
  recordableKey k           = a name the low-level attribute-setter will
                              actually record: non-empty, built only from the
                              characters a cookie name admits, and not one of
                              the names reserved for a directive's own
                              attributes (a require)
  domainStated d            = the domain scope is absent or actually names one;
                              the empty text is not a scope (a require)
  mergeDirective old new    = attributes RECORDED, never withdrawn: secure is
                              old.secure || new.secure; an absent policy/domain on
                              the later directive leaves the earlier value standing
  fileDirective filed c     = replace the entry for c.name WHERE IT SITS by
                              `mergeDirective` of the two, or append if absent

A single equation, but it pins SEVEN independent behaviours, and each has at least
one rival below:

  * ADDRESSEE — the directive is addressed to the very cookie the caller named
    (the `.name` projection of the filed entry);
  * DECISION — the secure flag is a genuine disjunction of two sub-tests over two
    DIFFERENT binders (the name and the policy);
  * CARRY-THROUGH / FORWARDING — the policy reaches the filed directive, and for
    the two callers it must reach it THROUGH the clear routine rather than being
    dropped on the way;
  * FRAME (values) — `path`/`domain` flow UNCHANGED, so no verifying impl may
    silently substitute a default;
  * ARITY — EXACTLY ONE directive is filed. A second one for the same cookie is
    not idempotent: `mergeDirective` records and cannot withdraw, so a spurious
    extra directive leaves its flag or its scope on the record permanently;
  * FRAME (record) — what was already on file is neither discarded nor rewritten:
    every OTHER cookie's entry is left exactly as it was, and a re-filed cookie
    keeps its POSITION;
  * NEIGHBOUR ARITY — no directive is filed for a cookie nobody asked to clear;
  * LIFETIME / BODY / FLAGS — the filed entry says what makes it a CLEARING
    directive rather than an ordinary assignment: an empty body, the spent
    lifetime `clearedMaxAge`, the past expiry moment `epochExpiry`, and no
    script-inaccessible flag. These are observables of the SAME filed entry as
    the addressee and the secure flag, so an entry can be perfect in every flag
    and scope and still not clear the cookie.

WHY THE ENTRY'S LIFETIME, BODY AND FLAGS ARE OBSERVED. Added by the MOST RECENT
SPEC-REPAIR pass, after an audit produced a verify-but-not-resolve counterexample
against a carrier that projected only FIVE attributes of a filed entry — the
addressee, the secure flag, the cross-site policy, the path and the domain:

  * the deep model of the unchanged attribute-setter was, at five fields, a
    TRANSPARENT structure constructor, so an implementation could build a record
    with those five fields directly and discharge the equation without going
    through the modelled callee at all. Everything the real clearing call
    determines BEYOND those five — the empty body it hands over, the spent
    lifetime it grants, the past expiry moment it announces, and the absence of a
    script-inaccessible mark — lay outside every postcondition and was therefore
    a free choice. The audit's attack rebuilt the five-field image directly;
    measured with the official harness its faithful counterpart ran
    completed=True, resolved=FALSE, failing tests in BOTH sets: three of the
    behaviour's own checks (which read the granted lifetime and the announced
    expiry back off the cleared cookie, or compare the emitted clearing header
    verbatim) and two previously-passing ones;
  * the same blindness was shared by the two differential oracles, which compared
    only the same five attributes and so agreed with the attack.

The repair WIDENS what a filed entry observes to the nine attributes the real
clearing call actually determines, so the lifetime pair and the body become
observable and the single equation pins them. The lifetime fields are
optional-valued precisely so an OMITTED attribute is a distinct observation
rather than collapsing onto a stated one — an entry that says nothing about the
lifetime is not the same entry as one that grants zero seconds. Both differential
oracles were widened in step, so the model's projection is no longer narrower than
the claim it validates. Four rivals below attack the newly observable behaviours
(`weak-delete-no-spent-lifetime`, `weak-delete-no-past-expiry`,
`weak-delete-nonempty-body`, `weak-delete-adds-httponly`), each holding the other
eight attributes at their correct values, and all four prepatch twins still FAIL
on their own original ``samesite``/``secure`` goals — with the lifetime and expiry
identical on both sides of each twin's goal — so the new observations do not mask
the bug the twins encode.

WHY THE RECORD IS AN INPUT AND AN OUTPUT. Added by a SPEC-REPAIR pass after an
audit produced a verify-but-not-resolve counterexample against the earlier
surface, which handed the caller ONE freshly-built cookie VALUE:

  * because only the last value built was observable, a routine could file a
    directive of its OWN first and then the requested one, and every attribute
    clause still held of the value it returned. Measured with the official
    harness: an attack that filed a prior directive scoped to a domain of its own
    VERIFIED, and its faithful counterpart ran completed=True, resolved=FALSE on
    three consecutive attempts. The mechanism is that the attribute-setter records
    attributes without withdrawing them, so the flag and scope of the spurious
    directive survive into the emitted clearing header, which the hidden tests
    compare verbatim;
  * the same blindness admitted a routine that DISCARDED the directives already on
    the response, and a site that filed a directive for an unrelated cookie.

The repair gives the response record status as an input and an output and states
the never-withdraw semantics its real counterpart has, so those implementations
are now WRONG rather than merely untested. Four rivals below attack the newly
observable behaviours (`weak-delete-extra-directive`,
`weak-delete-discards-record`, `weak-session-site-extra-directive`,
`weak-message-site-extra-cookie`) and all four prepatch twins still FAIL on their
own original ``samesite``/``secure`` goals, so the new obligation does not mask
the bug the twins encode.

AN EARLIER REPAIR PASS added the ADDRESSEE and caller-DECISION behaviours, after
an audit found that the carrier had no ``name`` field at all (so nothing pinned
which cookie a directive was addressed to; two attacks substituted a literal of
their own, VERIFIED, and measured resolved=FALSE) and that neither caller
obligation mentioned the secure flag (so a clear site could emit any flag it
liked). Both now fall out of the single equation, and the three
``*-wrong-addressee`` and two ``*-const-secure`` rivals attack them.

WHY THE ADDRESSEE AND CALLER-DECISION CLAUSES EXIST. Both were added by a
SPEC-REPAIR pass after the P2 audit produced verify-but-not-resolve
counterexamples against the earlier surface, which observed only
``secure``/``samesite``/``path``/``domain`` of the clear routine and only
``samesite``/``domain``/``path`` of the two callers:

  * the carrier had no ``name`` field at all, so NOTHING pinned which cookie a
    clearing directive was addressed to. Two audit attacks substituted a literal
    of their own for the caller-supplied name at a clear site, VERIFIED, and
    their faithful patches were run through the official harness: completed=True,
    resolved=FALSE on three consecutive attempts. Every hidden test of this
    behaviour reads the cleared cookie back BY NAME, so misnaming it fails all of
    them while satisfying every clause the spec had;
  * neither caller obligation mentioned ``c.secure``, so a clear site could emit
    any flag it liked. Recorded as the audit's escalated attack D.

The repair adds the postconditions the real patched routine and its two patched
call sites actually satisfy — the directive names the cookie it was asked to
clear, and its flag is the disjunction of the reserved-namespace test on THAT
name and the unrestricted-policy test on THAT policy — so the counterexamples
are now wrong rather than merely excluded. Five rivals below attack them (three
ADDRESSEE, two caller DECISION), one per independent obligation, and all four
prepatch twins still FAIL on their own original ``samesite``/``secure`` goals,
so the new clauses do not mask the bug the twins encode.

GROUNDED ORACLE. ``secureForClear`` is a total ``def`` over the method's OWN two
arguments — a fully-computable disjunction, not an opaque answer key — and the
``axioms`` region is EMPTY (``mkCookie`` is a deep A-reference validated == the
real attribute-setter by axiom_check.py, never consumed as an axiom). So there is
no wrong echo to build: ``secure := secureForClear key samesite`` is the honest
cheapest impl and is a CORRECT positive control, while a wrong constant or a
wrong sub-decision FAILS the clause (the partial-domain rivals below). This
mirrors the nagini sibling's own GROUNDED-ORACLE NOTE.

THE CARRIER IS PARTLY OPAQUE, and that shapes every witness. A witness reaches a
``method`` contract through Velvet's own tester machinery (``<name>Tester args =
false`` says the extracted program's result violates the postcondition at that
input). TWO string primitives block kernel reduction, not one (corrected by the
audit — the earlier note here claimed ``String.startsWith`` on a literal always
reduces, which is measurably false and contradicted this file's own
``_H_PREFIX``):

  * ``String.toLower`` never reduces: ``String.mapAux`` carries
    ``@[irreducible]``, so for a PRESENT policy both ``crossSiteUnrestricted``
    and the tester's own ``acceptedPolicy`` guard stay stuck. Measured: ``decide``,
    ``decide +kernel``, ``rfl``, ``simp``, ``grind``, ``simp [String.toLower,
    String.map]`` and ``unseal String.mapAux`` all fail on
    ``("none" : String).toLower = "none"``.
  * ``String.startsWith`` reduces only when the mismatch is decided WITHOUT
    walking the shared prefix. Measured: ``hasSecurePrefix "c" = false`` closes
    under a bare ``decide`` (exit 0), while ``hasSecurePrefix "__Host-c" = true``
    and ``("__Secure-c").startsWith "__Host-" = false`` both get stuck
    (``did not reduce to isTrue or isFalse``, exit 1). So a key INSIDE the
    reserved namespace has to be conditioned on too.

So the witnesses split by which terms their point makes the kernel walk:

  * SIXTEEN witnesses are unconditioned: the policy is ABSENT and the key is
    outside the reserved namespace, so the tester computes end-to-end and a bare
    ``decide`` closes. (Seven from the original battery; the first repair pass's five
    ADDRESSEE / caller-DECISION rivals and this pass's four ARITY / record-FRAME
    rivals are all refuted at such a point, since every one of those defects is
    independent of the policy value and of the reserved namespace. One of the
    four, `weak-delete-discards-record`, needs a NON-EMPTY starting record to be
    separated at all — its witness supplies a one-entry record for another
    cookie — but still reduces without a hypothesis, since that entry's own name
    is outside the reserved namespace.)
  * SIX witnesses CONDITION on the one carrier fact their point needs — five on
    the case fold (``h : ("lax" : String).toLower = "lax"``, resp. ``"none"``)
    and ONE (``weak-and-instead-of-or``, whose separating point is a
    reserved-namespace key with the policy ABSENT) on the prefix test
    (``("__Host-c").startsWith "__Host-" = true``). Each states the STRONGER
    claim — whenever that primitive behaves as named, the rival's answer
    contradicts the spec — over exactly the sub-domain where the rival is wrong.
    Verified by the audit that the prefix-conditioned one genuinely needs its
    hypothesis: the same witness with a bare ``decide`` fails against the rival
    (exit 1, stuck reduction), so the hypothesis is load-bearing, not decoration.
    The audit's own added case (``weak-case-sensitive-policy``) is the sixth, and
    conditions on the fold at a NON-lowercase spelling.

Every conditioning hypothesis is a single fact about a single term, and it is the
ACTUAL truth about that literal, so the binders are jointly satisfiable; the
gate's inconsistency probe was re-run by the audit on all three hypothesis shapes
and could not derive ``False`` from any of them (exit 1 on each). No witness binds
two hypotheses about the same term.

ADVERSARIAL READ of the nagini classes on this carrier:
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Nagini's
    drop-the-none-disjunct, AND-instead-of-OR and drop-the-forwarding rivals port
    onto the DECISION and CARRY-THROUGH clauses directly, and the two caller
    methods (which nagini models as pure call-site wirings, not contracted
    functions) admit four more rivals of their own.
  * FRAME / PERMISSION-MUTATION — VACUOUS as a permission attack. Nagini carries
    two MANDATORY rivals here (store through a reference held at half
    permission). Lean and Velvet are referentially transparent: no heap, no
    aliasing, no ``mut`` binder on any input, so there is no read-only input to
    overwrite. The class is NOT fabricated. Its INTENT — a rival must not be able
    to substitute its own value for a caller-supplied one — survives as the
    ``path``/``domain`` frame clauses, which this spec pins exactly and which
    four rivals below attack.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` over immutable
    values, no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * UNGROUNDED-ORACLE ECHO — N/A (see GROUNDED ORACLE above).

THE TWO HOLES THE EARLIER PASS ESCALATED ARE NOW CLOSED. This file previously
recorded both of the following as findings on the frozen spec, unshippable as
reject cases because no witness can refute a rival the spec satisfies:

  * a caller that builds the cleared cookie inline with ``secure := true``. The
    two caller obligations pinned only ``samesite``/``domain``/``path`` — NEITHER
    mentioned ``c.secure`` — so a caller could emit any flag it liked. The
    emitted clearing directive carries a Secure attribute the real one does not,
    and a session cookie cleared over a plain connection survives, so the
    verbatim header comparison in the session tests does not match;
  * a caller that substitutes its OWN literal for the caller-supplied cookie
    name. The name reached no clause of the caller's contract at all.

Both are now REJECTED, each by its own rival with a discriminating witness
(``weak-message-site-const-secure`` / ``weak-session-site-const-secure`` for the
flag; the three ``*-wrong-addressee`` rivals for the name). The earlier pass
prescribed the fix — "an ``ensures c.secure = secureForClear <name>
configuredPolicy`` on each caller (and a name binder the clause can refer to)" —
and the repair pass added exactly that, plus the ``c.name`` clause that gives the
addressee an observation of its own rather than leaving it visible only
indirectly through the reserved-namespace test.

DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE SEMANTICS
against any rival that manufactures it. Every frozen impl region is LOOP-FREE
(straight-line ``let`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: EMPTY. The sibling's two AXIOM_TESTS are dropped — that lane is
G-AX's job (axiom_check.py validates the ``mkCookie`` deep A-reference == the
real attribute-setter, and the containment argument for the accepted-policy
domain is the ``require``), this bundle consumes no axiom ``ensures``, and the
gate ignores AXIOM_TESTS regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13195"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (an impl body
# between -- impl-start / -- impl-end, or a prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and all three prove_correct headers intact.
# ---------------------------------------------------------------------------

# The two lines of the clear routine's own impl region.
_SEC = "    let secure := secureForClear key samesite\n"
_MK = ("    let out := fileDirective filed "
       "(mkCookie key secure samesite path domain)\n")

# The single call line in each caller's impl region.
_MSG_CALL = ('    let out ← deleteCookie filed cookieName "/" domain '
             'configuredPolicy\n')
_SES_CALL = ("    let out ← deleteCookie filed sessionName path domain "
             "configuredPolicy\n")

# The three frozen tactic bodies (each unique, each elided from the spec view).
# Only the soundness positives whose reshaped impl no longer matches its frozen
# script retune one of these; every reject rival keeps all three as-is.
_MSG_PROOF = "prove_correct clearMessageCookie by\n  loom_solve\n"
_SES_PROOF = "prove_correct clearSessionCookie by\n  loom_solve\n"

for _a in (_SEC, _MK, _MSG_CALL, _SES_CALL, _MSG_PROOF, _SES_PROOF):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a!r}")


# ---------------------------------------------------------------------------
# Witness preamble. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches it through Velvet's own tester machinery: `<name>Tester args`
# evaluates the extracted program and decides the postcondition at that input,
# so `= false` says the impl's result CONTRADICTS the contract there. Checked in
# a file whose prove_correct blocks are stripped, so no tactic script can mask
# the verdict.
#
# The generated precondition instance needs one tactic: `acceptedPolicy` is a
# `Prop`-valued match on an `Option`, and the default `infer_instance` cannot see
# through it (measured: "unsolved goals ... Decidable (acceptedPolicy samesite)").
# Splitting on the option first makes both branches inferrable.
# ---------------------------------------------------------------------------
_PRE = ("extract_program_for {n}\n"
        "prove_precondition_decidable_for {n} by\n"
        "  unfold acceptedPolicy; split <;> infer_instance\n"
        "prove_postcondition_decidable_for {n}\n"
        "derive_tester_for {n}\n\n")

_PURE = ("acceptedPolicy, mkCookie, secureForClear, hasSecurePrefix, "
         "crossSiteUnrestricted, fileDirective, mergeDirective, "
         "NonDetT.run, pure")


def _tester(*names):
    return "".join(_PRE.format(n=n) for n in names)


def _simpset(names):
    """The pure defs plus ONLY the testers this witness file actually declares.

    Naming a tester the file does not declare makes `simp` report an unknown
    identifier, which fails BOTH builds for a reason having nothing to do with
    the spec — the gate would record `witness-unproven` for a witness it never
    really tried. (Hit while authoring; this is the fix.)
    """
    return ", ".join(f"{n}Tester, {n}Exec, {n}" for n in names) + ", " + _PURE


def _mk_lit(**over):
    """The thirteen-field directive literal the frozen `mkCookie` builds, with
    named fields overridden.

    A rival that attacks ONE observable of the filed directive has to name all
    thirteen, because the carrier is a record: writing the literal is the only way
    to hold twelve fields at their correct values and move the thirteenth.
    Rendering
    it from one place keeps the twelve untouched fields verbatim across the rivals,
    so each one differs from the frozen behaviour in exactly the field its id
    names and a reader can check that by eye.
    """
    f = {"name": "key", "transmittedName": "key",
         "value": '""', "codedValue": "quotedEmptyBody",
         "maxAge": "clearedMaxAge",
         "expires": "some epochExpiry", "secure": "secure",
         "httpOnly": "false", "samesite": "samesite",
         "path": "path", "domain": "domain",
         "comment": "none", "version": "none"}
    f.update(over)
    return ("    let out := fileDirective filed\n"
            "      { name := %(name)s, transmittedName := %(transmittedName)s,\n"
            "        value := %(value)s,\n"
            "        codedValue := %(codedValue)s, maxAge := %(maxAge)s,\n"
            "        expires := %(expires)s, secure := %(secure)s,\n"
            "        httpOnly := %(httpOnly)s, samesite := %(samesite)s,\n"
            "        path := %(path)s, domain := %(domain)s,\n"
            "        comment := %(comment)s, version := %(version)s }\n" % f)


def _w_plain(names, call):
    """Witness at an ABSENT-POLICY point: the tester computes, `decide` closes."""
    return _tester(*names) + f"example : {call} = false := by\n  decide\n"


def _w_cond(names, call, hyp):
    """Witness CONDITIONED on the one carrier fact the kernel will not reduce.

    `simp` discharges the reducible part and rewrites with `h`; `all_goals
    decide` closes whatever residual literal goal is left (and is a no-op when
    `simp` already closed it, which differs case to case).
    """
    return _tester(*names) + (
        f"example (h : {hyp}) :\n"
        f"    {call} = false := by\n"
        f"  simp [{_simpset(names)}, h]\n"
        "  all_goals decide\n")


# The two conditioning facts, each the ACTUAL truth about its literal (so the
# binders are satisfiable) and each a SINGLE fact about a SINGLE term.
_H_NONE = '("none" : String).toLower = "none"'
_H_LAX = '("lax" : String).toLower = "lax"'
_H_PREFIX = '("__Host-c" : String).startsWith "__Host-" = true'
# The case fold at a NON-lowercase spelling of the unrestricted policy: the fact
# weak-case-sensitive-policy needs, and the only hypothesis in this file whose
# literal differs from its own folded image.
_H_UPPER_NONE = '("NONE" : String).toLower = "none"'


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different CORRECT impls that
    # MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Ports the sibling's pos-control-reorder / -direct.
    # =====================================================================
    {
        "id": "pos-control-commute",
        "kind": "soundness",
        "expect": "verify",
        # The decision is the COMMUTED disjunction. Logically identical (|| is
        # commutative on Bool) and a different executable form; the frozen script
        # is retuned with the commutation lemma, which is not a new obligation.
        "module": _swap(
            _swap(_BASE, _SEC,
                  "    let secure := crossSiteUnrestricted samesite "
                  "|| hasSecurePrefix key\n"),
            "prove_correct deleteCookie by\n  loom_solve <;> simp [mkCookie]\n",
            "prove_correct deleteCookie by\n"
            "  loom_solve <;> simp [mkCookie, secureForClear, Bool.or_comm]\n"),
        "rationale": "structurally-different but CORRECT impl: the secure flag is "
                     "computed as the COMMUTED disjunction (the unrestricted-policy "
                     "test first, the reserved-namespace test second), identical to "
                     "`secureForClear` since `||` is commutative and both sub-tests "
                     "are total pure functions of the arguments. Introduces no new "
                     "obligation. MUST verify; else the DECISION clause "
                     "`c.secure = secureForClear key samesite` is over-fit to the "
                     "disjunct ORDER => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest HONEST impl: inline the decision into the constructor call,
        # dropping the intermediate local entirely.
        "module": _swap(_swap(_BASE, _SEC, ""), _MK,
                        "    let out := fileDirective filed (mkCookie key "
                        "(secureForClear key samesite) samesite path domain)\n"),
        "rationale": "the decision oracle is GROUNDED in the arguments (a total "
                     "pure disjunction over `key` and `samesite`, not an opaque "
                     "answer key), so inlining it into the constructor — dropping "
                     "the intermediate local — is the honest cheapest CORRECT impl, "
                     "not an ungrounded echo. MUST verify (the clause is literally "
                     "`c.secure = secureForClear key samesite`); else "
                     "SPEC-TOO-STRONG. Also demonstrates the spec is NOT "
                     "echo-vulnerable: a wrong constant or wrong sub-decision fails "
                     "the clause (see weak-const-secure / weak-drop-none-disjunct).",
    },
    {
        "id": "pos-control-inline-callsite",
        "kind": "soundness",
        "expect": "verify",
        # A caller that builds the cleared cookie directly instead of delegating.
        # Same observable result, so all three of its clauses still discharge —
        # but via a different route (no callee-under-spec application), which is
        # the structurally-strongest correct reshape available on this surface.
        "module": _swap(
            _swap(_BASE, _SES_CALL,
                  "    let out := fileDirective filed (mkCookie sessionName "
                  "(secureForClear sessionName configuredPolicy) "
                  "configuredPolicy path domain)\n"),
            _SES_PROOF,
            "prove_correct clearSessionCookie by\n  loom_solve <;> simp [mkCookie]\n"),
        "rationale": "structurally-different CORRECT reshape of a caller: it builds "
                     "the cleared cookie directly with the same field-wise values "
                     "instead of delegating to the clear routine, so its three "
                     "clauses (FORWARDING `c.samesite = configuredPolicy`, and the "
                     "`c.path`/`c.domain` FRAME clauses) discharge without applying "
                     "the callee's contract. MUST verify; else the caller's clauses "
                     "are over-fit to the DELEGATION form rather than pinning the "
                     "observable result => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's admiss-selfcall, re-aimed. Nagini's version
    # proves a fresh F2P-shaped input satisfies the fractional-permission
    # precondition. Here the preconditions are `acceptedPolicy`, `recordableKey`
    # and `domainStated`, so the meaningful question is whether they jointly admit
    # a normal F2P-shaped call at all.
    # =====================================================================
    {
        "id": "admiss-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        # A self-call on a reserved-namespace key, threading the caller's OWN
        # accepted policy, then the gold body. The probe's precondition must
        # discharge from the caller's `require` alone.
        "module": _swap(
            _swap(
                _BASE, _SES_CALL,
                '    let _probe ← deleteCookie filed "__Host-probe" "/" none configuredPolicy\n'
                + _SES_CALL),
            _SES_PROOF,
            "prove_correct clearSessionCookie by\n"
            "  loom_solve <;> first | decide | simp_all\n"),
        "rationale": "a self-call on a fresh F2P-shaped input (a reserved-namespace "
                     "key, default path, absent domain) threading the caller's own "
                     "accepted policy, before the gold body runs on the real "
                     "arguments. Its preconditions must discharge from the caller's "
                     "own `require`s alone — the threaded policy from "
                     "`require acceptedPolicy configuredPolicy`, and the probe's "
                     "literal name/absent scope by computation — and both "
                     "obligations must still close. If a precondition rejects this "
                     "normal F2P-shaped call => PRECOND-TOO-STRONG. The tactic is "
                     "retuned (`first | decide | simp_all`) only to CLOSE the two "
                     "extra side goals the added self-call raises, which is a "
                     "soundness-positive's licensed retune, not a weakening: the "
                     "goals are discharged, not dropped. NOTE: the same "
                     "probe pinned to the literal unrestricted policy "
                     "`(some \"none\")` does NOT build here — not because the "
                     "precondition rejects it, but because discharging "
                     "`acceptedPolicy (some \"none\")` needs the case fold to "
                     "reduce, which is the `@[irreducible]` blocker described in "
                     "the docstring; threading the abstract policy tests the same "
                     "admissibility question without depending on it.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each is a wrong impl sharing the frozen
    # spec, carrying a machine-checked refutation witness at a concrete input and
    # the refinement argument for why its faithful real counterpart would NOT
    # resolve the failing tests.
    #
    # DECISION clause (2) -- CARRY-THROUGH clause (1) -- FRAME clauses (4)
    # -- caller FORWARDING clauses (2) -- caller FIXED-PATH clause (1)
    # =====================================================================

    # ---- DECISION clause: the unrestricted-policy disjunct dropped ----
    {
        "id": "weak-drop-none-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEC, "    let secure := hasSecurePrefix key\n"),
        "refinement": "this is the pre-change decision exactly (== the bundle's own "
                      "proven-reject Solution_prepatch_securenone.lean): the secure "
                      "flag derived from the key's namespace ALONE, omitting the "
                      "unrestricted-policy case. A faithful counterpart keeping it "
                      "still leaves the flag unset when a cookie outside the "
                      "reserved namespace is cleared under the unrestricted "
                      "cross-site policy, which the failing test for that exact "
                      "combination requires to be set — so it would NOT resolve. "
                      "verify-not-resolve.",
        "rationale": "REJECT from the DECISION clause `c.secure = secureForClear key "
                     "samesite`. Correct on every reserved-namespace key and every "
                     "non-unrestricted policy, WRONG on the sub-domain where the key "
                     "is outside the namespace AND the policy is the unrestricted "
                     "one (the clause requires true, the rival gives false). Refuted "
                     "at key `\"c\"` with the unrestricted policy — varies BOTH "
                     "decision binders away from the other rivals' points. If it "
                     "verified => SPEC-TOO-WEAK (the disjunction would be hollow).",
        "witness": _w_cond(("deleteCookie",),
                           'deleteCookieTester [] "c" "/" none (some "none")', _H_NONE),
    },

    # ---- DECISION clause: conjunction instead of disjunction (r1's near-miss) ----
    {
        "id": "weak-and-instead-of-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEC,
                        "    let secure := hasSecurePrefix key "
                        "&& crossSiteUnrestricted samesite\n"),
        "refinement": "requiring BOTH conditions leaves the secure flag unset for a "
                      "reserved-namespace key cleared under any non-unrestricted "
                      "policy — behaviour the pre-existing passing test for "
                      "reserved-namespace keys already forbids — AND for a "
                      "non-namespaced key under the unrestricted policy, which the "
                      "new failing test forbids. A faithful counterpart would fail "
                      "both, so it would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the DECISION clause, attacking the CONNECTIVE "
                     "rather than a missing disjunct: correct only on the diagonal. "
                     "A NEAR-MISS of weak-drop-none-disjunct that agrees with it on "
                     "the unrestricted-policy sub-domain, so it gets its OWN witness "
                     "at the input that separates them — a reserved-namespace key "
                     "with the policy ABSENT, where the clause requires true and "
                     "this rival gives false while weak-drop-none-disjunct is "
                     "correct. Varies `key` into the reserved namespace, the one "
                     "point no other witness probes. If it verified => "
                     "SPEC-TOO-WEAK (the disjunction would collapse to conjunction).",
        "witness": _tester("deleteCookie") + (
            f"example (h : {_H_PREFIX}) :\n"
            '    deleteCookieTester [] "__Host-c" "/" none none = false := by\n'
            f"  simp [{_simpset(('deleteCookie',))}, h]\n"
            "  all_goals decide\n"),
    },

    # ---- DECISION clause: the policy compared case-SENSITIVELY ----
    # ADDED BY THE AUDIT. The three pre-existing DECISION rivals all attack the
    # SHAPE of the disjunction (a dropped disjunct, the wrong connective, a
    # constant) and every one of them is refuted at a policy that is already
    # lowercase, so none of them can tell a case-INSENSITIVE unrestricted-policy
    # test from a case-SENSITIVE one. That sub-behaviour was undefended: this
    # rival is correct on every lowercase spelling and wrong only on a
    # differently-cased one.
    {
        "id": "weak-case-sensitive-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEC,
                        "    let secure := hasSecurePrefix key "
                        '|| samesite == some "none"\n'),
        "refinement": "comparing the cross-site policy value verbatim instead of "
                      "under a case fold leaves the secure flag unset whenever the "
                      "configured policy names the unrestricted policy in any "
                      "spelling other than all-lowercase. The accepted domain is "
                      "case-insensitive on both sides — the attribute-setter accepts "
                      "the value in any case, and the setting that supplies it is "
                      "conventionally written capitalised — so a faithful "
                      "counterpart emits a cleared cookie a browser discards over an "
                      "insecure transport for exactly the configuration the failing "
                      "test exercises, and it would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the DECISION clause, attacking the CASE FOLD "
                     "inside `crossSiteUnrestricted` rather than the shape of the "
                     "disjunction. The other three DECISION rivals are each refuted "
                     "at an already-lowercase policy (or at an absent one), so all "
                     "three are satisfied by this rival's answer and none of them "
                     "pins the fold — it was the one sub-decision of "
                     "`secureForClear` with no attack. Refuted at an ordinary key "
                     "with the policy spelled `(some \"NONE\")`, the only witness "
                     "point in the battery whose policy literal is not already its "
                     "own folded image. If it verified => SPEC-TOO-WEAK (the "
                     "case-insensitivity of the unrestricted-policy test would be "
                     "hollow).",
        "witness": _w_cond(("deleteCookie",),
                           'deleteCookieTester [] "c" "/" none (some "NONE")',
                           _H_UPPER_NONE),
    },

    # ---- DECISION clause: a constant, ignoring both binders ----
    {
        "id": "weak-const-secure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEC, "    let secure := true\n"),
        "refinement": "always setting the secure flag marks a cleared cookie as "
                      "secure-transport-only even for an ordinary key under no "
                      "cross-site policy, so a browser on a plain connection would "
                      "discard the clearing directive and the cookie would never be "
                      "cleared. The pre-existing passing test for the default clear "
                      "asserts the flag is UNSET there, so a faithful counterpart "
                      "would regress it and NOT resolve.",
        "rationale": "REJECT from the DECISION clause. This is the echo-vulnerability "
                     "probe the GROUNDED-ORACLE note predicts must fail: a constant "
                     "ignores BOTH decision binders, and the clause pins the flag to "
                     "a function of them, so it is refuted wherever the true "
                     "decision is false. Refuted at an ordinary key with the policy "
                     "ABSENT — the all-negative corner of the decision, which the "
                     "two disjunct rivals (both refuted where the decision is TRUE) "
                     "never reach. If it verified => SPEC-TOO-WEAK (the clause would "
                     "not constrain the flag at all).",
        "witness": _w_plain(("deleteCookie",), 'deleteCookieTester [] "c" "/" none none'),
    },

    # ---- CARRY-THROUGH clause: the policy is not recorded ----
    {
        "id": "weak-drop-carry-through",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK,
                        "    let out := fileDirective filed (mkCookie key secure none path domain)\n"),
        "refinement": "this is the pre-change wiring exactly (== the bundle's own "
                      "proven-reject Solution_prepatch.lean's second defect): the "
                      "cross-site policy never reaches the attribute setter, so the "
                      "cleared cookie carries no policy attribute at all. A faithful "
                      "counterpart keeping it still emits a cleared cookie without "
                      "the policy the caller supplied, which the failing test "
                      "asserting the cleared cookie carries that policy requires — "
                      "so it would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the CARRY-THROUGH clause `c.samesite = samesite`, "
                     "the clause the DECISION rivals leave untouched. The decision "
                     "is kept correct so the rejection is attributable to the "
                     "carry-through alone: on any PRESENT policy the clause requires "
                     "that value and the rival records none. Refuted at a present, "
                     "non-unrestricted policy with a non-default path and a present "
                     "domain — varying `path`, `domain` and `samesite` together, "
                     "and the only `deleteCookie` witness with all three non-default. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _w_cond(("deleteCookie",),
                           'deleteCookieTester [] "c" "/x" (some "e.com") (some "lax")',
                           _H_LAX),
    },

    # ---- FRAME clause: the caller's path replaced by the default ----
    {
        "id": "weak-frame-path-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK,
                        '    let out := fileDirective filed (mkCookie key secure samesite "/" domain)\n'),
        "refinement": "substituting the default path for the caller's silently "
                      "clears the wrong cookie: a cookie scoped to a sub-path is "
                      "identified by name AND path, so the directive would target a "
                      "non-existent cookie and leave the real one in place. The "
                      "failing test that clears a session cookie under a custom path "
                      "asserts the emitted path is the custom one, so a faithful "
                      "counterpart would NOT resolve.",
        "rationale": "REJECT from the FRAME clause `c.path = path`. This is where "
                     "the sibling's MANDATORY frame-mutation INTENT lands on a "
                     "referentially-transparent carrier: there is no read-only "
                     "reference to overwrite, but a rival can still substitute its "
                     "own value for a caller-supplied one, and the exactly-pinned "
                     "frame clause is what forbids it. Refuted at a non-default "
                     "path with the policy absent (so the point computes outright). "
                     "If it verified => SPEC-TOO-WEAK (the path frame would be "
                     "hollow and any impl could rescope the clear).",
        "witness": _w_plain(("deleteCookie",), 'deleteCookieTester [] "c" "/x" none none'),
    },

    # ---- FRAME clause: the caller's domain dropped ----
    {
        "id": "weak-frame-domain-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK,
                        "    let out := fileDirective filed (mkCookie key secure samesite path none)\n"),
        "refinement": "dropping the caller's domain leaves the attribute unset, so "
                      "the directive is host-scoped and cannot clear a cookie that "
                      "was set for a parent domain — the cookie survives. The "
                      "failing test that clears a session cookie under a custom "
                      "domain asserts the emitted directive carries that domain, so "
                      "a faithful counterpart would NOT resolve.",
        "rationale": "REJECT from the FRAME clause `c.domain = domain` — the second, "
                     "INDEPENDENT frame clause, attacked separately because a rival "
                     "mishandling only the domain would satisfy the path clause and "
                     "vice versa. Refuted at a PRESENT domain with the policy "
                     "absent; every other `deleteCookie` witness holds `domain` at "
                     "`none` or pairs it with a present policy, so this is the point "
                     "that makes the clause's dependence on `domain` observable. If "
                     "it verified => SPEC-TOO-WEAK (the domain frame would be "
                     "hollow).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "c" "/" (some "e.com") none'),
    },

    # ---- caller FORWARDING clause: the message site drops the policy ----
    {
        "id": "weak-message-site-drops-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MSG_CALL,
                        '    let out ← deleteCookie filed cookieName "/" domain none\n'),
        "refinement": "this is the pre-change call exactly (== the bundle's own "
                      "proven-reject Solution_prepatch_messages.lean): the clear "
                      "site does not pass the configured policy on, so the cleared "
                      "cookie carries none even though the clear routine is fully "
                      "capable of recording it. This is the reported symptom itself "
                      "— the cookie that is SET carries the policy while the one "
                      "that CLEARS it does not. A faithful counterpart keeping it "
                      "fails the message-storage test asserting the cleared cookie "
                      "carries the configured policy, so it would NOT resolve. Note "
                      "a correct clear routine alone does not make that test pass: "
                      "this site must forward. verify-not-resolve.",
        "rationale": "REJECT from the message caller's FORWARDING clause "
                     "`c.samesite = configuredPolicy`. A rival that fixes only the "
                     "clear routine and leaves this site unwired satisfies every "
                     "`deleteCookie` clause, so this obligation must be attacked "
                     "separately or the caller's contract is untested. Refuted at a "
                     "present configured policy with a present domain. If it "
                     "verified => SPEC-TOO-WEAK (a caller could drop the policy).",
        "witness": _w_cond(("deleteCookie", "clearMessageCookie"),
                           'clearMessageCookieTester [] "m" (some "e.com") (some "lax")',
                           _H_LAX),
    },

    # ---- caller FORWARDING clause: the session site drops the policy ----
    {
        "id": "weak-session-site-drops-policy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SES_CALL,
                        "    let out ← deleteCookie filed sessionName path domain none\n"),
        "refinement": "this is the pre-change call exactly (== the bundle's own "
                      "proven-reject Solution_prepatch_sessions.lean): the session "
                      "clear site does not pass the configured policy on. A "
                      "faithful counterpart keeping it fails the two session tests "
                      "that compare the emitted clearing header verbatim, including "
                      "its cross-site-policy attribute, so it would NOT resolve. "
                      "This is a SEPARATELY-observable behaviour from the message "
                      "site — the two sites are fixed independently and have "
                      "independent failing tests. verify-not-resolve.",
        "rationale": "REJECT from the session caller's FORWARDING clause "
                     "`c.samesite = configuredPolicy` — a DIFFERENT obligation from "
                     "the message caller's, attacked separately because a rival "
                     "wiring one site and not the other satisfies the wired one. "
                     "Refuted at a present configured policy with a non-default "
                     "path and a present domain, varying this method's `path` binder "
                     "away from the message site's fixed `\"/\"`. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _w_cond(("deleteCookie", "clearSessionCookie"),
                           'clearSessionCookieTester [] "s" "/p" (some "e.com") '
                           '(some "lax")', _H_LAX),
    },

    # ---- caller FRAME clause: the session site overrides the caller's path ----
    {
        "id": "weak-session-site-rescopes-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SES_CALL,
                        '    let out ← deleteCookie filed sessionName "/" domain '
                        'configuredPolicy\n'),
        "refinement": "a clear site that hardcodes the default path instead of "
                      "passing the configured one emits a directive scoped to the "
                      "wrong path, so a session cookie installed under a custom path "
                      "is never cleared. The failing test that ends a session under "
                      "a custom domain and path compares the emitted header "
                      "verbatim, including its path, so a faithful counterpart would "
                      "NOT resolve — and it would do so while forwarding the policy "
                      "correctly, which is why the FORWARDING clause alone does not "
                      "catch it.",
        "rationale": "REJECT from the session caller's FRAME clause `c.path = path` "
                     "— the caller-side counterpart of weak-frame-path-default, and "
                     "the reason the session method takes `path` as a binder at all "
                     "while the message method fixes it. The policy is forwarded "
                     "correctly, so the rejection is attributable to the path frame "
                     "alone. Refuted at a non-default path with the policy absent. "
                     "If it verified => SPEC-TOO-WEAK (a caller could rescope the "
                     "clear while appearing to forward correctly).",
        "witness": _w_plain(("deleteCookie", "clearSessionCookie"),
                            'clearSessionCookieTester [] "s" "/p" none none'),
    },

    # ---- caller FRAME clause: the message site drops the domain ----
    {
        "id": "weak-message-site-drops-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MSG_CALL,
                        '    let out ← deleteCookie filed cookieName "/" none '
                        'configuredPolicy\n'),
        "refinement": "a clear site that drops the configured domain emits a "
                      "host-scoped directive, which cannot clear a cookie that was "
                      "installed for a parent domain. The message-storage test "
                      "asserts the cleared cookie carries the configured domain "
                      "alongside the policy, so a faithful counterpart would NOT "
                      "resolve even though it forwards the policy correctly.",
        "rationale": "REJECT from the message caller's FRAME clause "
                     "`c.domain = domain`. The policy is forwarded correctly, so "
                     "the rejection is attributable to the domain frame alone — "
                     "which is what distinguishes this rival from "
                     "weak-message-site-drops-policy on the same method. Refuted at "
                     "a present domain with the policy absent, so the two rivals "
                     "against this method are refuted at genuinely different points "
                     "rather than sharing one. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie", "clearMessageCookie"),
                            'clearMessageCookieTester [] "m" (some "e.com") none'),
    },

    # ---- caller FIXED-PATH clause: the message site uses a non-default path ----
    {
        "id": "weak-message-site-wrong-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MSG_CALL,
                        '    let out ← deleteCookie filed cookieName "/x" domain '
                        'configuredPolicy\n'),
        "refinement": "the message cookie is installed at the site-root path, so a "
                      "clear directive emitted at any other path does not match it "
                      "and the cookie survives — the reported symptom, unfixed. The "
                      "message-storage test reads the cleared cookie back at the "
                      "root path, so a faithful counterpart would NOT resolve.",
        "rationale": "REJECT from the message caller's FIXED-PATH clause "
                     "`c.path = \"/\"` — the one clause that is a LITERAL rather "
                     "than a binder relation, and the only clause of the three "
                     "caller obligations not otherwise attacked. Refuted at absent "
                     "domain and absent policy, i.e. at the method's most default "
                     "input, since the defect is independent of both binders. If it "
                     "verified => SPEC-TOO-WEAK (the fixed path would be hollow).",
        "witness": _w_plain(("deleteCookie", "clearMessageCookie"),
                            'clearMessageCookieTester [] "msg" none none'),
    },

    # ---- caller FRAME clause: the session site drops the domain ----
    {
        "id": "weak-session-site-drops-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SES_CALL,
                        "    let out ← deleteCookie filed sessionName path none "
                        "configuredPolicy\n"),
        "refinement": "a session clear site that drops the configured domain emits "
                      "a host-scoped directive that cannot clear a session cookie "
                      "installed for a parent domain, so the session cookie "
                      "survives logout. The failing test that ends a session under "
                      "a custom domain compares the emitted header verbatim "
                      "including its domain attribute, so a faithful counterpart "
                      "would NOT resolve.",
        "rationale": "REJECT from the session caller's FRAME clause "
                     "`c.domain = domain`, the third and last of that method's "
                     "clauses to be attacked (its FORWARDING and `path` clauses "
                     "have their own rivals above), so every clause of every "
                     "obligation carries at least one attack. The policy and path "
                     "are wired correctly, isolating the domain frame. Refuted at a "
                     "present domain with a non-default path and absent policy. If "
                     "it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie", "clearSessionCookie"),
                            'clearSessionCookieTester [] "sess" "/q" (some "e.com") '
                            'none'),
    },

    # =====================================================================
    # ADDRESSEE clause rivals. The behaviour these attack — WHICH cookie the
    # clearing directive is addressed to — was the surface no clause of the
    # earlier spec mentioned at all, so a rival could clear a cookie of its own
    # choosing and satisfy every remaining obligation. Three rivals, one per
    # obligation, because the addressee of each is an independent behaviour: a
    # rival substituting its own name in ONE of the three still names the right
    # cookie in the other two.
    # =====================================================================

    # ---- ADDRESSEE clause: the clear routine addresses another cookie ----
    {
        "id": "weak-delete-wrong-addressee",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK,
                        '    let out := fileDirective filed (mkCookie "wrong" secure samesite '
                        'path domain)\n'),
        "refinement": "emitting the clearing directive against a name of the "
                      "routine's own choosing rather than the one it was asked to "
                      "clear leaves the requested cookie untouched and installs a "
                      "spurious expired directive for an unrelated name. Every "
                      "test of this behaviour reads the cleared cookie back BY "
                      "NAME, so a faithful counterpart finds nothing under the "
                      "name it asked for and NOT ONE of them can pass — it would "
                      "not resolve. verify-not-resolve.",
        "rationale": "REJECT from the ADDRESSEE clause `c.name = key`. The secure "
                     "flag, policy, path and domain are all wired correctly, so "
                     "the rejection is attributable to the addressee alone. "
                     "Refuted at an ordinary key with the policy absent, where "
                     "the tester computes end-to-end. If it verified => "
                     "SPEC-TOO-WEAK (the routine could clear any cookie it liked "
                     "while satisfying every other clause).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "c" "/" none none'),
    },

    # ---- ADDRESSEE clause: the message site clears someone else's cookie ----
    {
        "id": "weak-message-site-wrong-addressee",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MSG_CALL,
                        '    let out ← deleteCookie filed "wrong" "/" domain '
                        'configuredPolicy\n'),
        "refinement": "a clear site that names a cookie other than its own never "
                      "clears the cookie it is responsible for, so the reported "
                      "symptom persists and an unrelated cookie is expired "
                      "instead. The message-storage test reads the cleared cookie "
                      "back under the storage's own name, so a faithful "
                      "counterpart would NOT resolve even though it forwards the "
                      "policy, domain and path correctly. verify-not-resolve.",
        "rationale": "REJECT from the message caller's ADDRESSEE clause "
                     "`c.name = cookieName` — a DIFFERENT obligation from the "
                     "clear routine's, attacked separately because a rival "
                     "misnaming only at this site leaves `deleteCookie`'s own "
                     "addressee clause satisfied. Refuted at the method's most "
                     "default input. If it verified => SPEC-TOO-WEAK (a caller "
                     "could clear an arbitrary cookie).",
        "witness": _w_plain(("deleteCookie", "clearMessageCookie"),
                            'clearMessageCookieTester [] "m" none none'),
    },

    # ---- ADDRESSEE clause: the session site clears someone else's cookie ----
    {
        "id": "weak-session-site-wrong-addressee",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SES_CALL,
                        '    let out ← deleteCookie filed "wrong" path domain '
                        'configuredPolicy\n'),
        "refinement": "a session clear site that names a cookie other than the "
                      "session's own leaves the session cookie in place, so the "
                      "session survives logout. The two session tests compare the "
                      "emitted clearing header for the session's own cookie name "
                      "verbatim, so a faithful counterpart would NOT resolve. "
                      "SEPARATELY observable from the message site: the two sites "
                      "are named independently. verify-not-resolve.",
        "rationale": "REJECT from the session caller's ADDRESSEE clause "
                     "`c.name = sessionName`, the third independent addressee "
                     "obligation. The policy, path and domain are wired "
                     "correctly, isolating the addressee. Refuted at a "
                     "non-default path with the policy absent, varying this "
                     "method's `path` binder away from the message site's fixed "
                     "`\"/\"`. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie", "clearSessionCookie"),
                            'clearSessionCookieTester [] "s" "/p" none none'),
    },

    # =====================================================================
    # caller DECISION clause rivals. Whether the cleared cookie carries the
    # secure flag is a behaviour of each CLEAR SITE too, not only of the clear
    # routine: a site that builds the directive itself decides the flag itself.
    # Both rivals forward the policy, name their own cookie and keep the frame
    # exactly, so each is wrong ONLY on the flag.
    # =====================================================================

    # ---- caller DECISION clause: the message site forces the flag ----
    {
        "id": "weak-message-site-const-secure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _MSG_CALL,
                  '    let out := fileDirective filed (mkCookie cookieName true '
                  'configuredPolicy "/" domain)\n'),
            _MSG_PROOF,
            "prove_correct clearMessageCookie by\n"
            "  loom_solve <;> simp [mkCookie]\n"),
        "refinement": "a clear site that marks its directive "
                      "secure-transport-only regardless of the name and the "
                      "configured policy makes a browser on a plain connection "
                      "discard the directive, so the cookie is never cleared — "
                      "the reported symptom, replaced by a second one. The "
                      "message-storage test asserts the cleared cookie's flags "
                      "for an ordinary name under the default policy, where the "
                      "flag must be UNSET, so a faithful counterpart would NOT "
                      "resolve.",
        "rationale": "REJECT from the message caller's DECISION clause "
                     "`c.secure = secureForClear cookieName configuredPolicy`. "
                     "The rival builds the directive inline instead of "
                     "delegating, which is a CORRECT reshape on its own (see "
                     "pos-control-inline-callsite) — the defect is purely the "
                     "constant flag, so the rejection is attributable to the "
                     "decision clause and not to the reshape. Refuted at an "
                     "ordinary name with the policy absent, the all-negative "
                     "corner where the true decision is false and this rival "
                     "gives true. If it verified => SPEC-TOO-WEAK (a clear site "
                     "could emit any flag it liked).",
        "witness": _w_plain(("deleteCookie", "clearMessageCookie"),
                            'clearMessageCookieTester [] "m" none none'),
    },

    # ---- caller DECISION clause: the session site forces the flag ----
    {
        "id": "weak-session-site-const-secure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(_BASE, _SES_CALL,
                  '    let out := fileDirective filed (mkCookie sessionName true '
                  'configuredPolicy path domain)\n'),
            _SES_PROOF,
            "prove_correct clearSessionCookie by\n"
            "  loom_solve <;> simp [mkCookie]\n"),
        "refinement": "a session clear site that always marks its directive "
                      "secure-transport-only emits a header a browser on a plain "
                      "connection discards, so the session cookie survives "
                      "logout. The two session tests compare the emitted header "
                      "verbatim and neither expects a Secure attribute, so a "
                      "faithful counterpart would NOT resolve. A SEPARATELY "
                      "observable behaviour from the message site's flag.",
        "rationale": "REJECT from the session caller's DECISION clause "
                     "`c.secure = secureForClear sessionName configuredPolicy` — "
                     "the caller-side counterpart of weak-const-secure, and a "
                     "DIFFERENT obligation from the message site's, attacked "
                     "separately because a rival forcing the flag at one site "
                     "leaves the other site's clause satisfied. Refuted at an "
                     "ordinary name with a non-default path and the policy "
                     "absent. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie", "clearSessionCookie"),
                            'clearSessionCookieTester [] "s" "/p" none none'),
    },
    # =====================================================================
    # SINGLE-DIRECTIVE / PRIOR-RECORD clauses. The behaviour these attack —
    # HOW MANY directives a clearing routine files, and whether it leaves what
    # is already on file alone — was the surface no clause of the earlier spec
    # could see: the contract handed the caller ONE freshly-built cookie value,
    # so a routine could file a second directive of its own (or discard the
    # record it was handed) and every attribute clause still held of the value
    # it returned. Because the attributes a filed directive carries are
    # RECORDED AND NEVER WITHDRAWN, a spurious extra directive is a real defect:
    # the flag or scope it carries survives the correct directive that follows.
    # =====================================================================

    # ---- the clear routine files a SECOND directive for the same cookie ----
    {
        "id": "weak-delete-extra-directive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK,
                        "    let pre := fileDirective filed "
                        '(mkCookie key true samesite path (some ".x.com"))\n'
                        "    let out := fileDirective pre "
                        "(mkCookie key secure samesite path domain)\n"),
        "refinement": "filing an extra clearing directive of the routine's own "
                      "before the requested one leaves that directive's "
                      "attributes on the record: the cookie stays marked "
                      "secure-transport-only and stays scoped to a domain the "
                      "caller never asked for, because a later directive can "
                      "supply a value but cannot withdraw one. A browser on a "
                      "plain connection then discards the clearing header and "
                      "the cookie is never cleared. The tests of this behaviour "
                      "compare the emitted clearing header verbatim, so a "
                      "faithful counterpart would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the clear routine's single-directive clause. "
                     "Every attribute the routine passes on the FINAL directive "
                     "is correct — name, flag, policy, path and domain all "
                     "match the requested ones — so no attribute clause of the "
                     "earlier surface could see this defect at all; only the "
                     "relation between what was on file and what is on file "
                     "after can. Refuted at an ordinary key with the policy "
                     "absent, where the true flag is false and the extra "
                     "directive makes it true. If it verified => SPEC-TOO-WEAK "
                     "(a clear routine could file any number of extra "
                     "directives).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "c" "/" none none'),
    },

    # ---- the clear routine DISCARDS what was already on file ----
    {
        "id": "weak-delete-discards-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK,
                        "    let out := fileDirective [] "
                        "(mkCookie key secure samesite path domain)\n"),
        "refinement": "a clear routine that throws away the directives already "
                      "on the response emits a reply that has forgotten every "
                      "other cookie the response was setting or clearing. Those "
                      "cookies are silently left alone in the browser, and the "
                      "tests that read a response's other cookies back would "
                      "find nothing, so a faithful counterpart would NOT "
                      "resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the routine act "
                     "ON the record it was given: `fileDirective filed ...` "
                     "rather than on an empty one. The directive it files is "
                     "field-wise perfect, so this is the FRAME defect at the "
                     "level of the record — the analogue on this carrier of "
                     "clobbering a caller-supplied value, one level up from the "
                     "path/domain frame rivals. Refuted at an ordinary key "
                     "with the policy absent. If it verified => SPEC-TOO-WEAK "
                     "(the record would be a free input the routine may "
                     "replace).",
        "witness": _tester("deleteCookie") + (
            "example :\n"
            '    deleteCookieTester [mkCookie "other" false none "/" none] "c" '
            '"/" none none = false := by\n'
            "  decide\n"),
    },

    # ---- the session site files a second directive for its own cookie ----
    {
        "id": "weak-session-site-extra-directive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SES_CALL,
                        "    let mid ← deleteCookie filed sessionName path "
                        '(some ".x.com") configuredPolicy\n'
                        "    let out ← deleteCookie mid sessionName path domain "
                        "configuredPolicy\n"),
        "refinement": "a clear site that files a directive of its own before "
                      "the correct one pins the session cookie to a domain the "
                      "configuration never named, and that scope cannot be "
                      "withdrawn by the directive that follows. The session "
                      "tests compare the emitted clearing header verbatim, "
                      "including its domain attribute, so a faithful "
                      "counterpart would NOT resolve even though it forwards "
                      "the policy, names its own cookie and passes the right "
                      "path. verify-not-resolve.",
        "rationale": "REJECT from the session caller's single-directive clause "
                     "— a DIFFERENT obligation from the clear routine's, "
                     "attacked separately because a site filing an extra "
                     "directive leaves `deleteCookie`'s own clause satisfied "
                     "on each individual call. Every value it finally passes "
                     "is correct; the defect is the extra call. Refuted at a "
                     "non-default path with an absent domain and absent "
                     "policy, so the extra directive's domain is the only "
                     "difference. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie", "clearSessionCookie"),
                            'clearSessionCookieTester [] "s" "/p" none none'),
    },

    # ---- the message site files a directive for ANOTHER cookie too ----
    {
        "id": "weak-message-site-extra-cookie",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MSG_CALL,
                        '    let mid ← deleteCookie filed "__Host-x" "/" domain '
                        "configuredPolicy\n"
                        '    let out ← deleteCookie mid cookieName "/" domain '
                        "configuredPolicy\n"),
        "refinement": "a clear site that also files a clearing directive for an "
                      "unrelated cookie tells the browser to drop a cookie "
                      "nobody asked it to drop, so a reserved-namespace cookie "
                      "the application still needs is expired. The record the "
                      "site leaves behind has an entry no correct run would "
                      "have, so a faithful counterpart would NOT resolve. "
                      "verify-not-resolve.",
        "rationale": "REJECT from the message caller's single-directive clause, "
                     "attacking the OTHER way an extra directive can be wrong: "
                     "not a second directive for its own cookie (that is "
                     "weak-session-site-extra-directive) but a first one for "
                     "somebody else's, which leaves its own cookie's entry "
                     "perfect and adds a spurious neighbour. Refuted at the "
                     "method's most default input. If it verified => "
                     "SPEC-TOO-WEAK (a clear site could expire arbitrary "
                     "cookies).",
        "witness": _w_plain(("deleteCookie", "clearMessageCookie"),
                            'clearMessageCookieTester [] "m" none none'),
    },

    # =====================================================================
    # THE FILED DIRECTIVE'S LIFETIME, BODY AND FLAGS. Each of the four rivals
    # below holds the addressee, the secure flag, the cross-site policy, the path
    # and the domain at exactly the values the behaviour calls for, and moves ONE
    # other observable of the entry that is actually filed. That is deliberate:
    # these are the observables a carrier that projected only the addressee, the
    # flag, the policy and the scope could not see at all, and a routine wrong in
    # only one of them satisfies every clause about the other five. Each is
    # refuted at a point where the policy is ABSENT and the key sits OUTSIDE the
    # reserved namespace, so the true secure flag is false and the witness cannot
    # be closing on a flag disagreement — the named field is the only thing that
    # differs. The four points are otherwise distinct (different keys, a
    # non-default path, a present domain, and one with an entry already on file),
    # so no one input point is doing all four refutations.
    # =====================================================================

    # ---- the entry grants no spent lifetime ----
    {
        "id": "weak-delete-no-spent-lifetime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(maxAge="none")),
        "refinement": "an entry that states no remaining lifetime is not a "
                      "clearing directive: the browser is told nothing about how "
                      "long to keep the cookie, so it keeps it for the rest of "
                      "the session and never drops it — the cookie the caller "
                      "asked to have cleared simply stays. The checks of this "
                      "behaviour that compare the emitted clearing header "
                      "verbatim no longer match it, so a faithful counterpart "
                      "would NOT resolve even though the addressee, every flag, "
                      "the policy, the path and the domain are all correct. "
                      "verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the filed entry "
                     "grant the spent lifetime `clearedMaxAge`. This is the "
                     "defect class a directive-as-flags carrier cannot see: the "
                     "five addressee/flag/scope fields are perfect, so every "
                     "DECISION, CARRY-THROUGH, FRAME and ADDRESSEE clause holds "
                     "of it, and only an observation of what the entry says about "
                     "the cookie's lifetime separates it. If it verified => "
                     "SPEC-TOO-WEAK (a clear routine could file an entry that "
                     "clears nothing).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "c" "/" none none'),
    },

    # ---- the entry announces no past expiry moment ----
    {
        "id": "weak-delete-no-past-expiry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(expires="none")),
        "refinement": "an entry that announces no expiry moment leaves the "
                      "browser to decide when the cookie lapses from its own "
                      "state rather than being told the moment has already "
                      "passed, so what is emitted is not the clearing header this "
                      "behaviour calls for. The checks that compare that header "
                      "verbatim see the attribute missing, so a faithful "
                      "counterpart would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry "
                     "announce `epochExpiry`. A SEPARATE obligation from the "
                     "spent lifetime and refuted separately: this rival grants "
                     "the lifetime correctly and is wrong only about the "
                     "announced moment, so weak-delete-no-spent-lifetime's rival "
                     "body does not exhibit this defect and neither witness "
                     "covers the other's field. Both halves of the pair are "
                     "attacked because a spec that pinned only one would leave "
                     "the other free. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "d" "/a" none none'),
    },

    # ---- the entry hands over a body of its own ----
    {
        "id": "weak-delete-nonempty-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(value='"deleted"')),
        "refinement": "an entry that hands over a sentinel body of the routine's "
                      "own instead of an empty one puts that text into the "
                      "browser's cookie jar, and the emitted header carries it, "
                      "so anything reading the cleared cookie back sees the "
                      "routine's invention rather than the empty value this "
                      "behaviour calls for. The checks that compare the emitted "
                      "header verbatim see it, so a faithful counterpart would "
                      "NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry hand "
                     "over an empty body. This is the UNGROUNDED-ECHO shape on "
                     "this carrier — a routine substituting a plausible value of "
                     "its own for the one the behaviour determines — and it is "
                     "distinct from the two lifetime rivals: the entry's lifetime "
                     "is entirely correct and only what it hands over is wrong. "
                     "If it verified => SPEC-TOO-WEAK (the body would be a free "
                     "choice of the implementation).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "e" "/" (some "e.com") none'),
    },

    # ---- the entry marks the cookie script-inaccessible ----
    {
        "id": "weak-delete-adds-httponly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(httpOnly="true")),
        "refinement": "an entry that marks the cookie script-inaccessible "
                      "records an attribute this behaviour never asks for, and "
                      "because a directive's attributes are recorded and never "
                      "withdrawn that mark then stands on the cookie's entry for "
                      "good. The checks that compare the emitted clearing header "
                      "verbatim see the extra attribute, so a faithful "
                      "counterpart would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry carry "
                     "no script-inaccessible flag. The right-value/wrong-effect "
                     "shape: the entry's lifetime, body, policy, scope and secure "
                     "flag are all correct and the defect is an ADDITIONAL "
                     "attribute rather than a wrong one — pinned for the same "
                     "reason as the path/domain frame, that a verifying routine "
                     "may not add attributes the behaviour does not call for. "
                     "Note this is the one moved field whose merge is STICKY, so "
                     "the mark also survives any later directive. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _tester("deleteCookie") + (
            "example :\n"
            '    deleteCookieTester [mkCookie "f" false none "/" none] "f" '
            '"/" none none = false := by\n'
            "  decide\n"),
    },

    # =====================================================================
    # WIRE-FORM and SPURIOUS-ATTRIBUTE rivals. Added by the MOST RECENT
    # SPEC-REPAIR pass, after an audit produced a verify-but-not-resolve
    # counterexample that agreed with the modelled attribute-setter on every
    # ATTRIBUTE of the filed entry and differed only in what the response puts
    # ON THE WIRE for the emptied body. Each rival below holds the other eleven
    # observables at their correct values and moves exactly one.
    # =====================================================================

    # ---- the entry transmits nothing where the real one transmits the quoted
    # ---- empty string ----
    {
        "id": "weak-delete-unencoded-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(codedValue='""')),
        "refinement": "an entry whose emptied body goes out AS NOTHING rather "
                      "than in the form the cookie machinery encodes it to is a "
                      "different directive on the wire: what the response "
                      "transmits for the cookie is its name, then the body's "
                      "encoded form, then the attributes, and an empty body does "
                      "not encode to the empty text. Every attribute of the entry "
                      "is correct — addressee, both halves of the lifetime pair, "
                      "the policy, the flags, the path and the domain — so this is "
                      "the defect a carrier that observed only attributes could "
                      "not see. The checks of this behaviour that compare the "
                      "emitted clearing header verbatim read the transmitted body "
                      "form directly and no longer match, so a faithful "
                      "counterpart would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry carry "
                     "`quotedEmptyBody` as the form its body is transmitted in. "
                     "This is the shape that motivated observing the wire form at "
                     "all: an implementation may agree with the modelled "
                     "attribute-setter on all of its ATTRIBUTES while writing the "
                     "entry itself by hand, and what it then puts on the wire for "
                     "the body is a free choice no attribute clause reaches. If it "
                     "verified => SPEC-TOO-WEAK (a clear routine could emit a "
                     "header no recipient reads as this behaviour's own).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "g" "/" none none'),
    },

    # ---- the entry attaches a free-text note of its own ----
    {
        "id": "weak-delete-adds-comment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(comment='some "cleared"')),
        "refinement": "an entry that attaches a free-text note of the routine's "
                      "own transmits an attribute the real clearing directive "
                      "never states, and because a directive's attributes are "
                      "recorded and never withdrawn the note then stands on that "
                      "cookie's entry for good. The checks that compare the "
                      "emitted clearing header verbatim see the extra attribute, "
                      "so a faithful counterpart would NOT resolve. "
                      "verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry carry "
                     "no note of its own. The right-value/wrong-effect shape on "
                     "the attributes a clearing directive does NOT state: pinned "
                     "for the same reason as the script-inaccessible flag, that a "
                     "verifying routine may not ADD attributes the behaviour does "
                     "not call for. Distinct from weak-delete-adds-httponly — that "
                     "rival moves a flag, this one an attribute carrying text — "
                     "and refuted at a different point. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "h" "/b" none none'),
    },

    # ---- the entry announces a protocol version of its own ----
    {
        "id": "weak-delete-adds-version",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(version='some "1"')),
        "refinement": "an entry that announces a protocol version of its own "
                      "transmits an attribute the real clearing directive never "
                      "states, and that announcement likewise cannot be withdrawn "
                      "by any later directive. The checks that compare the emitted "
                      "clearing header verbatim see it, so a faithful counterpart "
                      "would NOT resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry "
                     "announce no version of its own. Attacked separately from the "
                     "note because the two are independent observables and a spec "
                     "pinning only one would leave the other a free choice; this "
                     "rival states the note correctly and is wrong only about the "
                     "version. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "i" "/" (some "v.com") none'),
    },

    # =====================================================================
    # ADDRESSEE-vs-ANNOUNCED-NAME rivals. Added by the MOST RECENT SPEC-REPAIR
    # pass, after an audit produced a verify-but-not-resolve counterexample that
    # got every ATTRIBUTE of the filed entry right AND filed it against the
    # right cookie, and differed only in the NAME the entry itself announces on
    # the wire. The two observables are independent: where an entry is filed is
    # not what a recipient reads. Each rival below holds the other twelve
    # observables at their correct values and moves exactly that one.
    # =====================================================================

    # ---- the entry is filed against the right cookie but announces no name ----
    {
        "id": "weak-delete-unnamed-on-the-wire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(transmittedName='""')),
        "refinement": "an entry filed against the cookie it was asked to clear "
                      "but announcing NO name of its own goes out naming nothing "
                      "where the real one names that cookie. Every attribute is "
                      "correct — both halves of the lifetime pair, the transmitted "
                      "body form, the policy, the flags, the path and the domain — "
                      "and it is filed under the right cookie, so a check that "
                      "reads the entry back by the cookie it is filed against, or "
                      "reads any single attribute off it, cannot see the defect. "
                      "The checks of this behaviour that compare the emitted "
                      "clearing header verbatim read the announced name directly "
                      "and no longer match, so a faithful counterpart would NOT "
                      "resolve. verify-not-resolve.",
        "rationale": "REJECT from the clause's requirement that the entry announce "
                     "the very cookie it is filed against. This is the shape that "
                     "motivated observing the announced name at all: an "
                     "implementation may agree with the modelled attribute-setter "
                     "on every attribute AND on where the entry is filed while "
                     "writing the entry itself by hand, and the name it then "
                     "announces is a free choice no attribute clause and no "
                     "filed-under clause reaches. If it verified => SPEC-TOO-WEAK "
                     "(a clear routine could emit a header telling the recipient "
                     "to drop nothing at all).",
        "witness": _w_plain(("deleteCookie",),
                            'deleteCookieTester [] "j" "/" none none'),
    },

    # ---- the entry announces some OTHER cookie's name ----
    {
        "id": "weak-delete-announces-other-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MK, _mk_lit(transmittedName='"other"')),
        "refinement": "an entry filed against the cookie it was asked to clear "
                      "but announcing a DIFFERENT cookie's name tells the "
                      "recipient to drop the wrong cookie, so the cookie the "
                      "caller asked to clear is not cleared at all while some "
                      "other name is targeted. Attacked separately from the "
                      "no-name rival because a spec pinning only the "
                      "announced name's non-emptiness would leave WHICH name it "
                      "announces a free choice. The verbatim header checks see it, "
                      "so a faithful counterpart would NOT resolve. "
                      "verify-not-resolve.",
        "rationale": "REJECT from the same clause, at the other end of its "
                     "content: the announced name must be the cookie it is filed "
                     "against and not merely some name. Refuted at a point with a "
                     "present policy and a present domain, distinct from the "
                     "no-name rival's point, so neither witness is doing both "
                     "refutations. If it verified => SPEC-TOO-WEAK.",
        "witness": _w_cond(("deleteCookie",),
                           'deleteCookieTester [] "k" "/c" (some "w.com") '
                           '(some "lax")',
                           _H_LAX),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The sibling battery has 7 SPEC cases (2 soundness positives, 1 admissibility,
# 2 frame-mutation rivals, 3 partial-domain rivals) plus a 2-case AXIOM lane.
# This bundle is NOT the usual narrowed port: where most Lean-family bundles
# model one function against nagini's five, this one contracts THREE methods —
# the clear routine and BOTH call sites — because nagini folds the two call-site
# wirings into prose ("plus two pure call-site wirings") while the velvet spec
# gives each its own `method` with its own obligation. So the port is WIDER than
# the sibling on the caller axis and narrower only on the permission axis.
#
#   sibling case                  -> here                              disposition
#   -----------------------------------------------------------------------------
#   pos-control-reorder           -> pos-control-commute                PORTED
#   pos-control-direct            -> pos-control-direct                 PORTED
#   admiss-selfcall               -> admiss-selfcall                    PORTED (re-aimed)
#   frame-mutate-key              -> (none; intent -> frame rivals)     VACUOUS
#   frame-mutate-policy           -> (none; intent -> frame rivals)     VACUOUS
#   weak-drop-none-disjunct       -> weak-drop-none-disjunct            PORTED
#   weak-and-instead-of-or        -> weak-and-instead-of-or             PORTED
#   weak-drop-forwarding          -> weak-drop-carry-through            PORTED
#   (no sibling)                  -> pos-control-inline-callsite        ADDED
#   (no sibling)                  -> weak-const-secure                  ADDED
#   (no sibling)                  -> weak-frame-path-default            ADDED
#   (no sibling)                  -> weak-frame-domain-dropped          ADDED
#   (no sibling)                  -> weak-message-site-drops-policy     ADDED
#   (no sibling)                  -> weak-session-site-drops-policy     ADDED
#   (no sibling)                  -> weak-session-site-rescopes-path    ADDED
#   (no sibling)                  -> weak-message-site-drops-domain     ADDED
#   (no sibling)                  -> weak-message-site-wrong-path       ADDED
#   (no sibling)                  -> weak-session-site-drops-domain     ADDED
#   (no sibling)                  -> weak-case-sensitive-policy         ADDED (audit)
#   (divergence: no sibling case) -> (none)                             SPEC-CLOSED
#   (no sibling)                  -> weak-delete-wrong-addressee        ADDED (audit)
#   (no sibling)                  -> weak-message-site-wrong-addressee  ADDED (audit)
#   (no sibling)                  -> weak-session-site-wrong-addressee  ADDED (audit)
#   (no sibling)                  -> weak-message-site-const-secure     ADDED (audit)
#   (no sibling)                  -> weak-session-site-const-secure     ADDED (audit)
#   (no sibling)                  -> weak-delete-extra-directive        ADDED (audit)
#   (no sibling)                  -> weak-delete-discards-record        ADDED (audit)
#   (no sibling)                  -> weak-session-site-extra-directive  ADDED (audit)
#   (no sibling)                  -> weak-message-site-extra-cookie     ADDED (audit)
#   (no sibling)                  -> weak-delete-no-spent-lifetime      ADDED (audit)
#   (no sibling)                  -> weak-delete-no-past-expiry         ADDED (audit)
#   (no sibling)                  -> weak-delete-nonempty-body          ADDED (audit)
#   (no sibling)                  -> weak-delete-adds-httponly          ADDED (audit)
#   (no sibling)                  -> weak-delete-unencoded-body          ADDED (audit)
#   (no sibling)                  -> weak-delete-adds-comment            ADDED (audit)
#   (no sibling)                  -> weak-delete-adds-version            ADDED (audit)
#   (no sibling)                  -> weak-delete-unnamed-on-the-wire     ADDED (audit)
#   (no sibling)                  -> weak-delete-announces-other-name    ADDED (audit)
#   AXIOM_TESTS (2)               -> (none)                             DROPPED (G-AX)
#
# 3 ported rivals, 28 added rivals, 2 vacuous, 2 dropped; with the 3 soundness
#   positives and the 1 admissibility case, 35 SPEC cases in all (31 reject, 4
#   expect-verify). The 28 added break down as the 11 of the original pass, the 5
#   ADDRESSEE / caller-DECISION rivals of the second, the 4 ARITY / record-FRAME
#   rivals of the third, the 4 per-entry LIFETIME / BODY / FLAG rivals of the
#   fourth, the 3 WIRE-FORM / SPURIOUS-ATTRIBUTE rivals of the fifth, and this
#   pass's 2 ANNOUNCED-NAME rivals, which separate the name an entry is FILED
#   against from the name it announces on the wire.
#   None of the last 18 has a nagini analogue: the sibling models the two
#   call sites as pure wirings, never gives the response a record, and carries no
#   entry attributes beyond the flag, so none of those defect classes can even be
#   expressed there.
#
# PORTED (positives): the sibling's disjunction reorder becomes the commuted
#   disjunction (its frozen script needs `Bool.or_comm`, which is a retune, not a
#   new obligation); its cheapest-honest-impl control becomes the inlined
#   decision, since `secure := secureForClear key samesite` IS the frozen impl
#   here and would be a no-op case.
# PORTED (admiss-selfcall, RE-AIMED): the sibling establishes that a fresh
#   F2P-shaped input satisfies the fractional-permission precondition. There are
#   no permissions here, so the case is re-aimed at the only precondition that
#   exists — whether `acceptedPolicy` admits a normal F2P-shaped self-call. The
#   policy is threaded abstractly rather than pinned to the literal `(some
#   "none")` because discharging `acceptedPolicy (some "none")` requires the case
#   fold to kernel-reduce, which it cannot (see the docstring); the literal
#   variant was built and fails for that reason ALONE, not because the
#   precondition rejects it. Recorded in the case's own rationale rather than
#   silently substituted.
# PORTED (3 partial-domain rivals): drop-none-disjunct and and-instead-of-or land
#   on the DECISION clause and drop-forwarding on the CARRY-THROUGH clause, each
#   keeping the sibling's refinement argument (and matching, in two cases, a
#   prepatch variant the bundle already proves rejects).
# ADDED (10): the sibling's carrier has nothing to attach these to.
#   * weak-const-secure is the echo-vulnerability probe: the sibling argues no
#     wrong echo exists because the oracle is grounded; a constant decision is
#     the direct test of that claim, and it is the only witness at the corner
#     where the true decision is FALSE.
#   * the four FRAME rivals (path/domain on the clear routine, path/domain on the
#     callers) exist because velvet pins `path`/`domain` exactly — the
#     directive-5 analogue of the sibling's permission discipline. This is where
#     the two vacuous frame-mutation cases' INTENT is actually tested.
#   * the four caller rivals exist because velvet contracts the two call sites as
#     methods; the sibling has no obligation for them at all. Each site's
#     forwarding and its frame are attacked separately, since a rival wiring one
#     site (or one field) and not the other satisfies the wired one.
#   * pos-control-inline-callsite defends a caller obligation by a route that
#     does NOT apply the callee's contract, so the caller's clauses are shown to
#     pin the observable result rather than the delegation form.
# VACUOUS (frame-mutate-key, frame-mutate-policy): the sibling carries both as
#   MANDATORY because each input is held at half permission and a rival can
#   illegally store into it to fabricate a reserved-namespace key or coerce the
#   policy. This backend is referentially transparent: no heap, no aliasing, no
#   `mut` binder on any input, so there is no read-only input to overwrite and no
#   substitute permission probe. Not fabricated. Their INTENT — a rival cannot
#   substitute its own value for a caller-supplied one — is carried by the four
#   FRAME rivals above, which is a value-level test of the same property.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
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
# AXIOM_TESTS: dropped (2 cases). The axiom lane is G-AX's job — axiom_check.py
#   validates the `mkCookie` deep A-reference == the real attribute-setter, and
#   the sibling's containment probe corresponds to this bundle's explicit
#   `require acceptedPolicy`, which is part of the frozen spec rather than
#   something a PBT case can attack. This bundle consumes no axiom `ensures`, and
#   the gate ignores AXIOM_TESTS regardless.
#
# OBSERVABLE / BINDER COVERAGE. The surface is three equations between records,
# and what they pin decomposes into independent OBSERVABLES of the filed entry
# plus the record-level relation. Every one is DEFENDED (the three positives + the
# admissibility case exercise all three methods) and every one is ATTACKED. 26
# reject rivals:
#   deleteCookie entry .secure   <- weak-drop-none-disjunct, weak-and-instead-of-or,
#                                   weak-const-secure, weak-case-sensitive-policy
#                                   (shape of the disjunction x3, plus the case fold)
#   deleteCookie entry .samesite <- weak-drop-carry-through
#   deleteCookie entry .path     <- weak-frame-path-default
#   deleteCookie entry .domain   <- weak-frame-domain-dropped
#   deleteCookie entry .name     <- weak-delete-wrong-addressee
#   deleteCookie entry .maxAge   <- weak-delete-no-spent-lifetime
#   deleteCookie entry .expires  <- weak-delete-no-past-expiry
#   deleteCookie entry .value    <- weak-delete-nonempty-body
#   deleteCookie entry .httpOnly <- weak-delete-adds-httponly
#   deleteCookie record relation <- weak-delete-extra-directive (arity),
#                                   weak-delete-discards-record (record frame)
#   clearMessageCookie   <- weak-message-site-drops-policy, -drops-domain,
#                           -wrong-path, -wrong-addressee, -const-secure,
#                           -extra-cookie (policy / domain / path / addressee /
#                           flag / neighbour arity)
#   clearSessionCookie   <- weak-session-site-drops-policy, -rescopes-path,
#                           -drops-domain, -wrong-addressee, -const-secure,
#                           -extra-directive (policy / path / domain / addressee /
#                           flag / arity)
# The thirteen per-entry observables are attacked SEPARATELY because the equation
# pins them independently: a rival wrong in exactly one of them satisfies every
# clause about the other twelve, which is precisely the defect class that produced
# the most recent spec repairs. The last pair of rivals makes the point sharpest:
# where an entry is FILED and the name it ANNOUNCES on the wire are two
# observables, not one, and a rival can be right about the first and wrong about
# the second.
#
# Every INPUT BINDER is varied by the reject witnesses, none pinned corpus-wide
# to one value:
#   filed       [] | one entry already on file for an unrelated cookie
#               (weak-delete-discards-record) | one already on file for the very
#               cookie being cleared (weak-delete-adds-httponly, which is the
#               only point where the sticky merge of the moved field is exercised)
#   key         "c" | "d" | "e" | "f" | "__Host-c"  (four outside the reserved
#               namespace and one inside — the last is what separates
#               weak-and-instead-of-or from weak-drop-none-disjunct)
#   path        "/" | "/a" | "/x" | "/p" | "/q"     (default and four non-defaults)
#   domain      none | some "e.com"
#   samesite    none | some "none" | some "NONE" | some "lax" (absent,
#               unrestricted lowercase, unrestricted in another case — the
#               spelling that separates weak-case-sensitive-policy — and a
#               present-but-restricted policy)
#   cookieName / sessionName  "m" | "msg" | "s" | "sess"
#   configuredPolicy          none | some "lax"
# The 31 reject witnesses probe 20 DISTINCT input points. Sharing a point is
# sound — the gate asks each witness to discriminate ITS OWN rival, and a shared
# point still separates rivals whose defects differ — and the pairs that could
# have collided but must NOT are deliberately separated: the near-miss
# weak-and-instead-of-or against weak-drop-none-disjunct, the three shape rivals
# against weak-case-sensitive-policy, the two rivals on each caller, and the four
# per-entry rivals against each other (distinct keys, a non-default path, a
# present domain, and a pre-existing entry).
#
# WITNESS DISCRIMINATION — re-derived with two real `scripts/lean_verify.sh`
# builds per reject case (plus the consistency probe for each conditioned one), in
# a file with all three prove_correct blocks stripped: every witness ELABORATES
# against its rival (exit 0) and FAILS against the frozen solution (exit 1), and
# every gold-side failure was read to confirm it is a SEMANTIC refutation — each
# reports ``Tactic `decide` proved that the proposition ... is false`` on the
# tester (or on `False` after the hypothesis rewrite), never an unknown
# identifier, a type error, or a stuck reduction. No consistency probe derives
# `False`, so no witness assumes a contradiction. 20 are unconditioned; 6
# condition on ONE carrier fact each (four on the case fold, one on the prefix
# test, one on the fold at a non-lowercase spelling — see the docstring for which
# primitives actually reduce). The four newest are unconditioned: widening the
# entry to nine fields kept `decide` able to reduce record equality at string and
# numeric literals, including telling an ABSENT lifetime or expiry apart from a
# stated one, which is the reduction the two lifetime rivals need. No
# `sorry`/`admit`/`native_decide`/`axiom` appears in any case or witness.
#
# HOW THE PER-ENTRY RIVALS ARE BUILT. Each writes the filed entry as a
# thirteen-field literal with ONE field moved (`_mk_lit`), rather than mutating the
# call to the modelled attribute-setter. That is forced by the shape of the
# defect: the point is a routine that produces an entry differing from the real
# one in a single observable, and on a record carrier the literal is the only way
# to hold the other twelve verbatim. `_mk_lit()` with NO override was BUILT and
# VERIFIES (exit 0), which confirms the literal is the frozen entry and each
# rival differs from correct behaviour in exactly the field its id names. This is
# also exactly the bypass shape the audits keep finding — assembling the entry by
# hand instead of routing it through the modelled call — so each newly observed
# field is one the bypass could otherwise have chosen freely.

AXIOM_TESTS = []
