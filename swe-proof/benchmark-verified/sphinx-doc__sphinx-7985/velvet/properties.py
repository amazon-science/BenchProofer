"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7985 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct classifyLocalLink`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over three read-only inputs).

  classifyLocalLink (uri : List Char) (fileExists anyIgnore : Bool)
      require isHttp uri = false
      ensures out = classify uri fileExists anyIgnore                 -- the pin

A non-network link text is CLASSIFIED into a verdict by its shape (``uri``) and
two environment observations: whether a file of that name is present
(``fileExists``) and whether the text matches a configured skip pattern
(``anyIgnore``). Desired behaviour (``classify``): a skip-without-resolution
link (empty / in-page fragment / mail address) is ``unchecked``; a link opening
with an explicit unsupported access-method marker is likewise ``unchecked``;
otherwise the text names a LOCAL target that MUST be resolved — present file ⇒
``working``, else a configured skip ⇒ ``ignored``, else the target is absent ⇒
``missing``. A non-network link is therefore NEVER left under the legacy blanket
non-resolving verdict (``localLink``). ``classify``, ``isUnchecked``,
``hasUriScheme``, ``isHttp`` are total, fully-unfolded ``def``s over the method's
own arguments (the ``axioms`` region declares NO ``axiom`` — no opaque answer key
to echo), and ``Status`` derives ``DecidableEq``, so the post-image DECIDES at
every concrete input, which is what makes the partial-domain rivals refutable at
a point.

WHICH CLAUSE CONSTRAINS THE IMPL. There is exactly one ``ensures`` — the master
pin ``out = classify uri fileExists anyIgnore`` — and it is a total function of
all three inputs. Every escaping decision (which verdict each ``(uri-shape,
fileExists, anyIgnore)`` region maps to) is pinned by it, so every uniqueness
rival targets it, at the sub-domain region it corrupts. ``classify`` internally
dispatches through several nested branches (skip-without-resolution → scheme →
file-present → skip-pattern → absent); the rivals attack every one of those
branches — the resolution verdicts the fix introduces, the scheme guard AND its
run-length boundary, the skip-without-resolution guard, and the precedence
between the two environment observations — and the reject witnesses move all
three input binders across seven distinct points.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutation-check-target`` rival writes through a read-only
    (``Acc(list_pred(target),1/2)``) reference to ``target`` and is rejected for
    INSUFFICIENT PERMISSION. This backend is referentially transparent: ``uri``
    is an immutable value, this method declares no ``mut`` binder, and there is
    no heap, aliasing, or permission system to subvert. There is no read-only
    input to overwrite, so the class is vacuous. No substitute probe fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image ``classify`` is a
    transparent ``def`` over the method's own arguments; there is no answer key
    to echo. The honest cheapest CORRECT impl (``return classify uri fileExists
    anyIgnore``) is carried as a POSITIVE control instead — it doubles as proof
    the spec is not echo-vulnerable, since any WRONG per-region verdict fails the
    pin.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against the master
    pin. A rival can be right on every region EXCEPT one resolution branch
    (collapse ``missing`` into ``working``; collapse ``ignored`` into
    ``missing``; drop the scheme guard so a scheme-marked target is resolved as a
    file; corrupt that guard's run-length boundary so a separator with no leading
    letters is skipped; narrow the skip-without-resolution guard so a mail
    address is resolved; invert the precedence of the two environment
    observations; or the pre-patch collapse of the entire non-network arm to the
    blanket ``localLink`` verdict).
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
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

WITNESS MECHANICS ON THIS BUNDLE. The post-image is DECIDABLE — ``classify`` and
its callees are transparent ``def``s and ``Status`` derives ``DecidableEq`` —
so each witness reaches the method's postcondition through Velvet's own tester
machinery: ``classifyLocalLinkTester uri fileExists anyIgnore = false`` says the
extracted program's result VIOLATES the ``ensures`` at that concrete input. It is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. Every argument is a concrete literal that
``decide`` reduces fully. Against a rival that corrupts a resolution branch the
statement elaborates (the rival's verdict differs from ``classify`` there);
against the FROZEN solution the same ``…Tester … = false`` is REFUTED by
``decide`` (gold's verdict IS ``classify`` at that point, so the tester returns
``true``), so the witness FAILS on gold — exactly the discrimination the gate
requires. No witness binds any hypothesis (every input is a concrete literal), so
no consistency probe is needed. No banned token (sorry/admit/native_decide/
axiom/opaque). Each witness was checked out-of-band with scripts/lean_verify.sh:
every one ELABORATES against its rival (exit 0) and FAILS against gold (a
``decide`` refutation, not a parse/unknown-name error). The literals are neutral
placeholders (``"readme"``, ``"abc://x"``) chosen to DECIDE the right branch, not
copied from the task's test fixtures (no leakage).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real stdlib callees (``str.startswith`` /
``re.match('[a-z]+://')``); that is G-AX's job (axiom_check.py / mapping.md) and
the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7985"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the nested-if verdict
# ---- cascade), everything strictly BETWEEN the method's `-- impl-start` /
# ---- `-- impl-end`. Every variant replaces exactly this text, so each edit lies
# ---- wholly inside the one -- impl-start .. -- impl-end region and same_spec
# ---- holds by construction (both facts asserted at load by _swap). The `pure`
# ---- region's `classify` def uses a different layout, so this `let out :
# ---- Status :=` / `return out` block is unique in the file.
_IMPL = (
    "    let out : Status :=\n"
    "      if isUnchecked uri then Status.unchecked\n"
    "      else\n"
    "        (if hasUriScheme uri then Status.unchecked\n"
    "         else\n"
    "           (if fileExists then Status.working\n"
    "            else\n"
    "              (if anyIgnore then Status.ignored\n"
    "               else Status.missing)))\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a positive that reshapes the impl or an admissibility case that adds an
# ---- in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). Rivals leave it as-is — the rejection is carried
# ---- by the witness, not the tactic script.
_PROOF = (
    "prove_correct classifyLocalLink by\n"
    "  loom_solve\n"
    "  simp only [classify]"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes whose
    residual goal no longer matches the frozen `simp only [classify]` script)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `classifyLocalLinkTester uri fileExists anyIgnore = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. Every argument is a
# ---- concrete literal so `decide` reduces the (loop-free) extracted program.
_TESTER = (
    "extract_program_for classifyLocalLink\n"
    "prove_precondition_decidable_for classifyLocalLink\n"
    "prove_postcondition_decidable_for classifyLocalLink\n"
    "derive_tester_for classifyLocalLink\n\n"
)


def _witness(uri_lit, file_exists, any_ignore):
    return (
        _TESTER +
        f'example : classifyLocalLinkTester ({uri_lit}) {file_exists} {any_ignore}'
        " = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model DIRECTLY,
        # no branch cascade at all. `out` IS `classify uri fileExists anyIgnore`,
        # so the pin holds trivially; the loop-free residual goal closes under
        # `loom_solve` alone (the frozen `simp only [classify]` is unneeded).
        # Since the post-image is GROUNDED in the arguments (not an opaque answer
        # key), this doubles as proof the spec is not echo-vulnerable — any WRONG
        # per-region verdict fails `out = classify …`.
        "module": _impl_reproved(
            "    let out : Status := classify uri fileExists anyIgnore\n"
            "    return out",
            "prove_correct classifyLocalLink by\n  loom_solve"),
        "rationale": (
            "the post-image `classify uri fileExists anyIgnore` is GROUNDED in the "
            "inputs (a total unfolded `def`, no opaque answer key), so returning it "
            "directly is the honest cheapest CORRECT impl; the pin is literally "
            "`out = classify …`, so it MUST verify, else the spec is SPEC-TOO-STRONG. "
            "Re-expresses the nagini honest-echo control: the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable."),
    },
    {
        "id": "pos-control-staged-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage the resolved-local verdict in a typed local `resolved`
        # before combining it with the skip-without-resolution / scheme guards.
        # Same value on every input region, different control shape; the frozen
        # proof `loom_solve; simp only [classify]` still closes unchanged.
        "module": _impl(
            "    let resolved : Status :=\n"
            "      if fileExists then Status.working\n"
            "      else (if anyIgnore then Status.ignored else Status.missing)\n"
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else (if hasUriScheme uri then Status.unchecked else resolved)\n"
            "    return out"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (stage the resolved-local "
            "verdict in a typed local, then combine) must verify; the verdict of "
            "every input region is unchanged, so the pin still discharges and the "
            "frozen proof closes as-is. Ports the nagini pos-control-check-flat-"
            "branches (branch reshape of the verdict cascade). Else SPEC-TOO-STRONG "
            "(over-fit to the inline nested-if code form)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require isHttp uri = false`, but that
    # scopes the model to the non-network arm; the nagini admiss-check-readable-
    # target case established that a fractional-permission READ of the input is
    # usable, which has no counterpart on this referentially-transparent carrier
    # (no heap permission to establish). Re-aimed at the residual admissibility
    # risk on this domain: that the post-image is DEGENERATE at the interesting
    # points — a spec no impl distinguishes reads exactly like one every impl
    # meets. This case discharges an in-region `assert`, at concrete F2P-shaped
    # points, that the classification is NON-DEGENERATE: an absent local target is
    # `missing` (and, crucially, NOT the blanket `localLink`), a skip-pattern
    # match is `ignored`, a present file is `working`, a scheme-marked target is
    # `unchecked` — the distinctions the failing tests demand. The impl is kept
    # verbatim so the method's own obligation still discharges; the proof is
    # retuned only to clear the extra assert goal by `decide` (allowed — the
    # tactic body is elided from the spec view). The assert is live, not
    # decoration: a false claim about the same points leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-classification-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss (\n"
            "      classify \"readme\".toList false false = Status.missing\n"
            "      ∧ classify \"readme\".toList false true = Status.ignored\n"
            "      ∧ classify \"readme\".toList true false = Status.working\n"
            "      ∧ classify \"abc://x\".toList false false = Status.unchecked\n"
            "      ∧ classify \"readme\".toList false false ≠ Status.localLink))\n"
            + _IMPL,
            "prove_correct classifyLocalLink by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp only [classify]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at concrete F2P-shaped "
            "points: an absent local target classifies to `missing` (and is NOT left "
            "under the blanket `localLink` verdict), a skip-pattern match to "
            "`ignored`, a present file to `working`, and a scheme-marked target to "
            "`unchecked` — the four distinctions the failing tests demand. The "
            "in-region assert must discharge (else the obligation is degenerate at "
            "the interesting points); the impl is kept verbatim so `out = classify "
            "uri fileExists anyIgnore` discharges too. Re-aimed from the nagini "
            "admiss-check-readable-target, whose fractional-permission-read half has "
            "no counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE / degenerate."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests. All attack the master pin
    # `out = classify uri fileExists anyIgnore`; the three input binders (`uri`,
    # `fileExists`, `anyIgnore`) are varied across the four reject witnesses.
    # =====================================================================
    {
        "id": "rival-missing-as-working",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse `missing` into `working`: an absent, non-skip local target is
        # reported as resolving instead of absent. This is the exact
        # discriminating region the fix introduces.
        "module": _impl(
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else\n"
            "        (if hasUriScheme uri then Status.unchecked\n"
            "         else\n"
            "           (if fileExists then Status.working\n"
            "            else\n"
            "              (if anyIgnore then Status.ignored\n"
            "               else Status.working)))\n"
            "    return out"),
        "refinement": (
            "a faithful real patch that reported an absent, non-skip local target "
            "as resolving would mark the invalid local file present instead of "
            "absent: the failing test asserts such a target appears in the report as "
            "broken and that the report line count rises accordingly, which a "
            "resolving verdict does not produce, so it would NOT resolve. This is the "
            "exact behaviour the fix corrects (the pre-patch left it unclassified)."),
        "rationale": (
            "REJECT from the master pin `out = classify uri fileExists anyIgnore`: "
            "`classify` returns `missing` for an absent, non-skip local target, and "
            "this rival returns `working` there. Refuted at (`\"readme\"`, false, "
            "false) — the absent-non-skip region. If it verified => SPEC-TOO-WEAK "
            "(admits the bug)."),
        "witness": _witness('"readme".toList', "false", "false"),
    },
    {
        "id": "rival-ignored-as-missing",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse `ignored` into `missing`: an absent local target that matches a
        # configured skip pattern is reported absent instead of ignored. Drops the
        # skip-pattern arm entirely.
        "module": _impl(
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else\n"
            "        (if hasUriScheme uri then Status.unchecked\n"
            "         else\n"
            "           (if fileExists then Status.working\n"
            "            else Status.missing))\n"
            "    return out"),
        "refinement": (
            "a faithful real patch that dropped the skip-pattern arm would report "
            "every absent local target as broken even when the text matches a "
            "configured skip pattern. The failing test adds such a target to the "
            "skip-pattern configuration and expects it treated as ignored (absent "
            "from the broken report); a broken verdict there fails that test, so it "
            "would NOT resolve. A genuine partial-domain break — correct on every "
            "non-skip target."),
        "rationale": (
            "REJECT from the master pin: `classify` returns `ignored` for an absent "
            "target that matches a skip pattern (anyIgnore = true), and this rival "
            "returns `missing` there. Refuted at (`\"readme\"`, false, true) — a "
            "DISTINCT point from rival-missing-as-working (it moves the `anyIgnore` "
            "binder to true), so the battery varies that binder. Ports nagini "
            "partial-domain-ignored-as-missing. If it verified => SPEC-TOO-WEAK "
            "(domain-incomplete)."),
        "witness": _witness('"readme".toList', "false", "true"),
    },
    {
        "id": "rival-drop-scheme-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the scheme guard: a target opening with an explicit unsupported
        # access-method marker (`abc://…`) is resolved as a local file instead of
        # being left unchecked. This is the guard the fix introduces.
        "module": _impl(
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else\n"
            "        (if fileExists then Status.working\n"
            "         else\n"
            "           (if anyIgnore then Status.ignored\n"
            "            else Status.missing))\n"
            "    return out"),
        "refinement": (
            "a faithful real patch without the access-method-marker guard would "
            "treat a target carrying an explicit unsupported scheme as a local file "
            "and report it broken/working rather than unchecked, diverging from the "
            "post-fix classification of such a target (which must be skipped without "
            "resolution). It would NOT resolve the behaviour the fix establishes for "
            "scheme-marked targets."),
        "rationale": (
            "REJECT from the master pin: `classify` returns `unchecked` when the "
            "target opens with an explicit access-method marker (hasUriScheme), and "
            "this rival returns a resolution verdict (`missing` at an absent target) "
            "there. Refuted at (`\"abc://x\"`, false, false) — moves the `uri` "
            "binder to a scheme-marked shape. Ports nagini "
            "partial-domain-drop-scheme-branch. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness('"abc://x".toList', "false", "false"),
    },
    {
        "id": "rival-collapse-to-blanket",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch shape: the entire non-network arm collapses to the single
        # blanket non-resolving verdict `localLink` without ever resolving the
        # target. Mirrors G-DIFF (this is the prepatch skeleton).
        "module": _impl(
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else Status.localLink\n"
            "    return out"),
        "refinement": (
            "this is the pre-patch shape: every non-network link that is not "
            "skipped-without-resolution is recorded under the single blanket "
            "non-resolving verdict without any file-presence or skip-pattern test. "
            "A present valid local file is left under the blanket verdict instead of "
            "resolving to working, and an absent one is never reported broken; the "
            "failing tests pin both, so it would NOT resolve — the exact "
            "non-resolution G-DIFF reproduces."),
        "rationale": (
            "REJECT from the master pin: `classify` resolves a present local file to "
            "`working`, and this rival returns the blanket `localLink` there. Refuted "
            "at (`\"readme\"`, true, false) — moves the `fileExists` binder to true "
            "(the present-file region no other reject witness probes). Ports nagini "
            "collapse-nonweb-to-constant. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness('"readme".toList', "true", "false"),
    },
    {
        "id": "rival-scheme-empty-run",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. The access-method detector's run-length boundary: accept a
        # ZERO-length leading lowercase run (`k >= 0`) instead of requiring one or
        # more letters, so a text that carries the `://` separator with NO
        # letters before it is mis-routed into the skip-without-resolution
        # verdict. The port recorded this class as inexpressible on the ground
        # that the detector `hasUriScheme` is a frozen `def` in the spec region;
        # that is true of the DEF but not of the CLASS — the impl need not call
        # the frozen detector at all, it can inline a corrupted copy of the
        # boundary test over the equally-frozen `lowerRun`, which is what this
        # rival does. same_spec still holds (the edit is wholly inside the impl
        # region) and the witness discriminates at `"://x"`.
        "module": _impl(
            "    let k : Nat := lowerRun uri\n"
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else\n"
            "        (if List.isPrefixOf \"://\".toList (uri.drop k) then\n"
            "           Status.unchecked\n"
            "         else\n"
            "           (if fileExists then Status.working\n"
            "            else\n"
            "              (if anyIgnore then Status.ignored\n"
            "               else Status.missing)))\n"
            "    return out"),
        "refinement": (
            "the real access-method detector requires ONE OR MORE letters before "
            "the separator; a faithful patch that accepted zero-or-more would "
            "classify a text whose separator is not preceded by any letter as "
            "carrying an access-method marker and skip it without resolution, so "
            "an absent local target of that shape would never be reported broken "
            "and a present one never resolved. It would NOT resolve, and the "
            "boundary is exactly the one the axiom lane fuzzes."),
        "rationale": (
            "REJECT from the master pin: `classify` resolves `\"://x\"` as a local "
            "target (the frozen detector demands `lowerRun uri ≥ 1`, and here the "
            "run is 0), returning `missing` at (false, false); this rival returns "
            "`unchecked` there. Refuted at (`\"://x\"`, false, false) — a `uri` "
            "shape no other witness reaches. Ports nagini "
            "partial-domain-scheme-empty-run, which the port had recorded as "
            "inexpressible: the frozen detector cannot be RESHAPED, but a rival "
            "need not call it, and inlining a corrupted boundary over the frozen "
            "`lowerRun` stays inside the impl region. If it verified => "
            "SPEC-TOO-WEAK (the run-length boundary would be unpinned)."),
        "witness": _witness('"://x".toList', "false", "false"),
    },
    {
        "id": "rival-drop-mailto-arm",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. Narrow the skip-without-resolution guard: keep the empty
        # and in-page-fragment arms, DROP the mail-address arm, so a mail address
        # is resolved as though it named a local file. The battery's four ported
        # rivals all attack the resolution branches; none attacks the
        # skip-without-resolution guard itself, so the `isUnchecked` region of the
        # pin was defended only by positives.
        "module": _impl(
            "    let out : Status :=\n"
            "      if uri.isEmpty || List.isPrefixOf \"#\".toList uri then\n"
            "        Status.unchecked\n"
            "      else\n"
            "        (if hasUriScheme uri then Status.unchecked\n"
            "         else\n"
            "           (if fileExists then Status.working\n"
            "            else\n"
            "              (if anyIgnore then Status.ignored\n"
            "               else Status.missing)))\n"
            "    return out"),
        "refinement": (
            "a faithful patch whose skip-without-resolution guard omitted the "
            "mail-address arm would try to resolve a mail address as a file under "
            "the source tree and report it broken instead of skipping it "
            "unchecked, adding a spurious broken entry for every mail link in the "
            "documentation. It would NOT resolve: the skip set is behaviour the "
            "change preserves, not behaviour it alters."),
        "rationale": (
            "REJECT from the master pin: `classify` returns `unchecked` for a mail "
            "address (`isUnchecked` holds), and this rival falls through to the "
            "resolution cascade and returns `missing` there. Refuted at "
            "(`\"mailto:x\"`, false, false) — the skip-without-resolution region of "
            "the pin, which no ported rival attacked. AUDIT-ADDED (attack D): the "
            "class was unprobed, not omitted. If it verified => SPEC-TOO-WEAK "
            "(the skip set would be unpinned)."),
        "witness": _witness('"mailto:x".toList', "false", "false"),
    },
    {
        "id": "rival-ignore-before-file",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. Keep every arm, but REORDER the two resolution tests: test
        # the skip pattern BEFORE file presence. Observably wrong only on the
        # overlap region (a PRESENT file that also matches a skip pattern), where
        # the frozen order resolves to `working` and this one to `ignored`. No
        # existing witness sets both booleans true, so the precedence between the
        # two environment observations was unpinned by the reject lane.
        "module": _impl(
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else\n"
            "        (if hasUriScheme uri then Status.unchecked\n"
            "         else\n"
            "           (if anyIgnore then Status.ignored\n"
            "            else\n"
            "              (if fileExists then Status.working\n"
            "               else Status.missing)))\n"
            "    return out"),
        "refinement": (
            "a faithful patch that consulted the skip patterns before the "
            "file-presence test would record a target that BOTH resolves and "
            "matches a configured skip pattern as deliberately-skipped rather "
            "than as resolving, changing the reported verdict (and the report "
            "line count) for every such target. The post-fix behaviour resolves "
            "presence first, so it would NOT resolve."),
        "rationale": (
            "REJECT from the master pin: `classify` tests `fileExists` BEFORE "
            "`anyIgnore`, so a present file that also matches a skip pattern is "
            "`working`; this rival returns `ignored` there. Refuted at "
            "(`\"readme\"`, true, true) — the only input point where the two "
            "orders differ, and the first witness in the battery to set BOTH "
            "booleans true. AUDIT-ADDED (attack D): the precedence between the "
            "two environment observations was probed by no ported rival. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness": _witness('"readme".toList', "true", "true"),
    },

    # =====================================================================
    # AUDIT-ADDED POSITIVE (soundness). Re-derived from the nagini
    # pos-control-scheme-tail-boolean, which the port recorded as inexpressible:
    # the frozen detector `hasUriScheme` cannot be RESHAPED in place (it lives in
    # the spec region), but the nagini case's content — a correct impl that folds
    # the detector's run-length/separator test into its own boolean expression
    # instead of calling the packaged predicate — ports fine, because the impl
    # may inline an EQUIVALENT copy over the frozen `lowerRun`. This is the
    # SPEC-TOO-STRONG probe for the scheme guard: if the spec accepted only
    # literal calls to `hasUriScheme`, it would be over-fit to the frozen code
    # form. Machine-checked: verifies with the frozen script plus the detector's
    # own unfolding.
    # =====================================================================
    {
        "id": "pos-control-inline-scheme",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    let k : Nat := lowerRun uri\n"
            "    let out : Status :=\n"
            "      if isUnchecked uri then Status.unchecked\n"
            "      else\n"
            "        (if decide (k ≥ 1) && List.isPrefixOf \"://\".toList (uri.drop k)"
            " then\n"
            "           Status.unchecked\n"
            "         else\n"
            "           (if fileExists then Status.working\n"
            "            else\n"
            "              (if anyIgnore then Status.ignored\n"
            "               else Status.missing)))\n"
            "    return out",
            "prove_correct classifyLocalLink by\n"
            "  loom_solve\n"
            "  simp only [classify, hasUriScheme]"),
        "rationale": (
            "a correct impl that INLINES the access-method test (stage the "
            "front-run length in a local, then apply the run-length and separator "
            "conditions directly) instead of calling the packaged predicate must "
            "verify: it computes the same Bool at every input, so the pin still "
            "discharges once the predicate is unfolded. Re-derives the nagini "
            "pos-control-scheme-tail-boolean, which the port recorded as "
            "inexpressible — the frozen `def` cannot be reshaped, but an "
            "equivalent inline copy in the impl region can, and that is what the "
            "nagini case actually tested. Else SPEC-TOO-STRONG (over-fit to "
            "calling `hasUriScheme` by name)."),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling has 9 SPEC cases (2 soundness, 1 admissibility, 6
# uniqueness) over THREE contracted functions: `starts_with`, `scheme_present`,
# and `check`. This velvet bundle models only the PURELY FUNCTIONAL CORE as ONE
# method `classifyLocalLink` (mapping.md §1): `check`'s non-network arm. Its
# supporting predicates `isUnchecked` / `hasUriScheme` / `isHttp` — the nagini
# `starts_with` / `scheme_present` surface — are FROZEN `def`s in the `pure`
# spec region (referenced by the postcondition), NOT the one method's impl
# region, so rivals that reshape or corrupt THEM cannot be written without
# breaking `same_spec`. That carrier narrowing removes the two nagini cases
# attached to `scheme_present`'s internals; the rest port cleanly.
#
#   nagini case                          -> here
#   -----------------------------------------------------------------------
#   frame-mutation-check-target          -> (none)                     VACUOUS
#   partial-domain-ignored-as-missing    -> rival-ignored-as-missing   PORTED
#   partial-domain-missing-as-working    -> rival-missing-as-working   PORTED
#   partial-domain-drop-scheme-branch    -> rival-drop-scheme-guard    PORTED
#   collapse-nonweb-to-constant          -> rival-collapse-to-blanket  PORTED
#   partial-domain-scheme-empty-run      -> rival-scheme-empty-run     PORTED (audit)
#   pos-control-check-flat-branches      -> pos-control-staged-local   PORTED (reshape)
#   pos-control-scheme-tail-boolean      -> pos-control-inline-scheme  PORTED (audit)
#   admiss-check-readable-target         -> admiss-classification-...  RE-AIMED
#   (nagini echo surface)                -> pos-control-direct         RE-EXPRESSED
#   AXIOM_TESTS (2)                       -> (none)                     DROPPED (G-AX lane)
#   (no nagini counterpart)              -> rival-drop-mailto-arm      AUDIT-ADDED
#   (no nagini counterpart)              -> rival-ignore-before-file   AUDIT-ADDED
#
# 11 velvet SPEC cases: 3 soundness, 1 admissibility, 7 uniqueness.
#
# AUDIT CORRECTION (independent adversarial audit; supersedes the OMITTED
# (carrier) claim this table used to carry for the two `scheme_present`-internals
# cases). The port reasoned that `hasUriScheme` / `lowerRun` are frozen `def`s in
# the `pure` spec region and so cannot be reshaped or corrupted by any in-scope
# variant. The premise is true; the conclusion does not follow. An impl is not
# obliged to CALL the frozen detector: it may inline its own copy of the
# run-length / separator test over the (equally frozen, equally callable)
# `lowerRun`, wholly inside the impl region, so same_spec holds by construction.
# Corrupting that copy yields a rival wrong exactly on the zero-length-run
# boundary the nagini case attacked (rival-scheme-empty-run, discriminated at
# `"://x"`); keeping it faithful yields the reshape positive
# (pos-control-inline-scheme). Both were built: the rival is rejected and its
# witness elaborates against it (exit 0) while `decide` REFUTES the same
# statement against the frozen solution (exit 1, "Tactic `decide` proved that the
# proposition ... is false"); the positive verifies (exit 0) under the frozen
# script plus the detector's own unfolding. The class was expressible, so the
# omission was a defect, now closed. Two further rivals close regions the ported
# four left unattacked: the skip-without-resolution guard (rival-drop-mailto-arm,
# refuted at a mail address) and the precedence between the two environment
# observations (rival-ignore-before-file, refuted at the present-AND-skipped
# overlap, the first witness to set both booleans true). The admissibility assert
# was checked LOAD-BEARING by flipping one conjunct to a false claim about the
# same point: the variant then fails to verify, so the assert is not decoration.
#
# PORTED (4 rivals): the partial-domain / collapse rivals carry across intact —
#   only the carrier changes from a nagini `List[int]` cascade to a Velvet
#   `List Char` verdict cascade. rival-ignored-as-missing, rival-missing-as-
#   working, rival-drop-scheme-guard, and rival-collapse-to-blanket each carry
#   their nagini refinement argument (F2P non-resolution), now backed by a
#   machine-checked tester witness.
# PORTED (positive): pos-control-check-flat-branches -> pos-control-staged-local
#   (branch reshape of the verdict cascade; the nagini flat/early-return reshape
#   becomes a staged-local reshape here, keeping the frozen proof).
# RE-EXPRESSED (echo-honest): the nagini file argues classify/prefix_eq/
#   has_uri_scheme are @Pure functions SPELLED OUT over the inputs, so "echoing
#   classify(...) IS performing the modeled decision" — there is no wrong echo to
#   build. On this carrier the same argument is the honest cheapest correct impl
#   `return classify uri fileExists anyIgnore` (pos-control-direct): the grounded
#   pin is satisfiable only by the real classification; no wrong per-region
#   verdict verifies.
# RE-AIMED (admissibility): admiss-check-readable-target established a fractional-
#   permission READ of the read-only `target` is usable for an F2P-shaped input.
#   This backend has no heap permission, so that probe is vacuous; re-aimed at the
#   residual total-domain risk (post-image non-degeneracy at the F2P-shaped
#   points), discharged by an in-region assert.
# OMITTED: NONE on the scheme-internals class. This slot previously recorded
#   partial-domain-scheme-empty-run and pos-control-scheme-tail-boolean as omitted
#   under carrier narrowing, on the argument that the scheme detector
#   `hasUriScheme` (with `lowerRun`) is a FROZEN `def` in the `pure` spec region
#   and so cannot be reshaped by any in-scope variant. The audit re-derived the
#   class and landed both cases, so that argument is WITHDRAWN. What is true is
#   only that the frozen `def` cannot be EDITED; what does not follow is that the
#   distinction it draws is unattackable, because an impl may ignore the packaged
#   predicate and inline its own copy of the run-length / separator test over the
#   frozen `lowerRun`, entirely within the impl region. The empty-run distinction
#   (a required non-empty leading run vs an accepted empty one) is therefore
#   observable on this carrier after all: gold and the corrupted-inline rival
#   disagree at `"://x"`, and `decide` separates them. Ported as
#   rival-scheme-empty-run (reject, witness discriminates) and
#   pos-control-inline-scheme (verify). G-AX independently validates hasUriScheme
#   == the real access-method detector including this boundary (mapping.md §3.1);
#   that is a separate obligation, and the G-PBT lane now also pins it.
# FRAME-MUTATION (frame-mutation-check-target): VACUOUS. The nagini rival writes
#   through a read-only (1/2) reference to `target` and is rejected for
#   insufficient permission. This backend is referentially transparent, `uri` is
#   an immutable value, no `mut` binder, no heap, no aliasing, no permission
#   system. There is no read-only input to overwrite. No substitute fabricated.
# DIVERGENCE: nothing to port (the nagini sibling carries no diverge-*/nonterm-*/
#   weak-diverge case) and nothing shippable, but the class is CLOSED BY THE
#   SEMANTICS rather than open. TWO earlier reasons are withdrawn.
#   (1) The port said the modeled behaviour is loop-free, so no non-terminating
#   impl can be written against it. That is false: a rival owns the whole impl
#   region and may INTRODUCE a loop the frozen impl never had.
#   (2) A later revision then said that under `partial` termination semantics the
#   pin is claimed only of terminating runs, so a `while True do pure ()` prefix
#   returning a blanket wrong verdict VERIFIES (exit 0) and the class is a known
#   escalated spec hole in an internal findings doc covering a `partial` cohort.
#   That is the PARTIAL rule stated against a TOTAL file. Line 4 reads
#   `set_option loom.semantics.termination "total"`, as it does in all 500 velvet
#   bundles, and the option cannot drift from the file's `open TotalCorrectness`
#   because the `set_option` elaborator itself runs `openScope `TotalCorrectness`
#   (Loom/MonadAlgebras/WP/Options.lean:169-186). The cited cohort has no referent
#   and the doc no longer exists.
#   Under `total` a postcondition is claimed of ALL runs, so every loop owes a
#   descent obligation `measure b' < measure b`. Re-measured on THIS bundle with
#   real builds, proofs reduced to a bare `loom_solve`: an unmeasured spun loop is
#   refused at elaboration (`Decreasing annotations are required in total
#   correctness semantics`), and the sharper shape that CARRIES a measure it never
#   shrinks (`while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q`,
#   body `q := q`) is REJECTED on the measure's own goal, `case «decreasing_1: q»`
#   with the residual `q < q` unsolved. So no diverging rival is admitted.
#   It is still not SHIPPABLE as a reject case, and that is a witness-protocol
#   limit rather than a spec one: a reject case needs a witness that ELABORATES
#   against the rival, and the rival's module does not compile at all (the descent
#   obligation fails at the `method`, ahead of any appended tester), so the gate
#   reads even a trivial witness as `witness-unproven`. Recorded as
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   REJECTED-BY-SPEC, not as a hole.
# DROPPED (AXIOM_TESTS): the nagini file's two axiom-soundness/containment probes
#   over the real stdlib callees (str.startswith / re.match) are G-AX's job
#   (axiom_check.py / mapping.md); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The only impl-constraining clause is the
#   master pin `out = classify uri fileExists anyIgnore` (there is exactly one
#   `ensures`). Every region of it is now attacked by a rival:
#   `working` region (rival-collapse-to-blanket, at fileExists = true),
#   `ignored` region (rival-ignored-as-missing), `missing` region
#   (rival-missing-as-working), the scheme→`unchecked` guard
#   (rival-drop-scheme-guard) and its run-length BOUNDARY (rival-scheme-empty-run),
#   the skip-without-resolution guard (rival-drop-mailto-arm), and the PRECEDENCE
#   of the two environment observations (rival-ignore-before-file). The three input
#   binders are varied across the seven reject witnesses: `uri` ∈ {"readme",
#   "abc://x", "://x", "mailto:x"} (ordinary local; scheme-marked; separator with
#   an EMPTY leading run; mail address), `fileExists` ∈ {false, true}, `anyIgnore`
#   ∈ {false, true} — including the (true, true) overlap point no ported witness
#   reached. Seven distinct input points, pts = 7, and no binder is held fixed by
#   every witness. The variation is MEANINGFUL, not two spellings of one point:
#   each witness's point is one where gold's verdict and its rival's verdict are
#   different Status constructors, machine-separated by `decide`. All three
#   positives and the admissibility case defend the pin across all regions.
#
# WITNESS MECHANICS: the post-image DECIDES (classify and its callees are
#   transparent `def`s; Status derives DecidableEq), so every witness uses the
#   tester+`decide` path: `classifyLocalLinkTester uri fileExists anyIgnore =
#   false` refutes the pin at a concrete input. Each rival's tester `decide`s to
#   false there; gold's tester is `true` at the same point, so the same statement
#   is refuted by `decide` against gold and the witness FAILS on gold. No witness
#   binds a hypothesis, so no consistency probe is needed. All SEVEN rebuilt
#   independently with scripts/lean_verify.sh during the audit: rival exit 0
#   (elaborates), gold exit 1 with "Tactic `decide` proved that the proposition
#   classifyLocalLinkTester <point> = false is false" — a semantic refutation of
#   the concrete claim, not a parse error, unknown name, unfolding failure, stuck
#   reduction, or timeout.
AXIOM_TESTS = []
