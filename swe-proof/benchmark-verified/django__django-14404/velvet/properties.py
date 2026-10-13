"""properties.py — G-PBT falsification battery for django__django-14404 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — the one region the consumer spec view elides — is
changed, so ``markers.same_spec`` holds and the ``prove_correct
appendSlashRedirect`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method assembling a redirect destination over a
per-character string carrier, ``List Char``):

  appendSlashRedirect (mountPrefix : List Char) (localPath : List Char)
      return (out : List Char)
    ensures out = redirectTarget mountPrefix localPath        -- C1
    ensures out = mountPrefix ++ localPath ++ ['/']           -- C2
    ensures ∃ rest, out = mountPrefix ++ rest                 -- C3

where ``redirectTarget mp lp = fullPath mp lp ++ ['/']`` and ``fullPath mp lp =
mp ++ lp``. Both ``redirectTarget`` and ``fullPath`` are TRANSPARENT ``def``s
spelled out over the two inputs (directive 8), NOT an opaque answer-key: the
load-bearing clause reduces to an ordered concatenation of the two inputs and a
single trailing separator, so ``decide`` computes it and no rival can "echo an
oracle" — the only way to satisfy it is to build the exact string. The deep
model of the request's full path (``fullPath``) is an A-reference validated ==
the real framework attribute by G-AX; this gate ignores that lane.

WHAT THE SPEC DEFENDS. The entire content of the modeled fix is that the
destination is assembled from the request's FULL client-facing path — the
deployment mount-point prefix followed by the per-request local path — rather
than from the local path alone. Assembling it from the local path drops the
prefix, sending a client served under a non-root mount point outside that mount
point. That prefix-preservation is pinned three ways:

  * C1 / C2 pin the WHOLE destination string, position by position: the prefix,
    then the local path, then exactly one trailing separator (code point '/').
    C1 is stated via the transparent ``redirectTarget`` def and C2 spells the
    same concatenation out; they are equivalent and either one refutes any
    wrong assembly.
  * C3 is the weaker STRUCTURAL clause: the destination begins with the
    mount-point prefix (``∃ rest, out = mountPrefix ++ rest``). A rival that
    drops the prefix, or emits the local path first, fails C3 even if C1/C2 were
    somehow satisfiable — so C3 is attacked independently below.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on BOTH inputs — ``mountPrefix`` and ``localPath``:

  * ``mountPrefix`` is the prefix that must be preserved. The pre-patch bug
    (wrong-source) and the local-path-first (swap) rivals mishandle it; they are
    caught by C1/C2/C3.
  * ``localPath`` is the local component that must follow the prefix and precede
    the separator. The drop-local rival omits it; it is caught by C1/C2 (and
    varies ``localPath`` in the witness set — it is the rival that does NOT
    depend on ``mountPrefix`` for its refutation).

The five reject witnesses probe five DISTINCT input tuples, so neither binder is
held fixed across the battery. Four of them use a NON-EMPTY prefix; the fifth
(``weak-empty-prefix-drop-sep``) is the only one on the empty-prefix side of the
single boundary this carrier has, and it exists because the audit found that
boundary otherwise unprobed.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame rivals (``frame-mutate-fullpath`` / ``frame-mutate-relpath``)
    that write through a read-only (``Acc(.,1/2)``) reference to an input and are
    rejected for INSUFFICIENT PERMISSION. Lean/Velvet are referentially
    transparent: both inputs here are immutable values, this bundle declares NO
    ``mut`` binder, and there is no heap, aliasing, or permission system to
    subvert. There is no read-only input to overwrite, so the class is vacuous
    and no substitute probe is fabricated (per the porting map).
  * CONTROL-FLOW GUARD rivals (nagini ``weak-drop-optin-guard`` /
    ``weak-drop-trailing-guard``) — NO COUNTERPART. The nagini sibling contracts
    the WHOLE surrounding request-dispatch control flow: a four-guard conjunction
    deciding whether a value is returned or ``NotFound`` is raised. This bundle is
    a CARRIER-NARROWED model of only the purely-functional redirect-destination
    ASSEMBLY (the changed expression); it has no guard inputs, no exception
    return, and no ``require`` — the branch structure is simply not modeled here.
    A rival dropping a guard has nothing to attach to. Omitted as carrier
    narrowing, NOT as an effort gap (the guards are outside the modeled surface).
  * ADMISSIBILITY (nagini's F2P-shaped self-call proving the read-only
    precondition) — VACUOUS as a precondition probe. This bundle declares NO
    ``require`` clause (the pre-conditions region is empty), so there is no
    precondition to admit. Re-aimed at the residual total-domain risk: that the
    three-clause post-image is jointly SATISFIABLE by a gold-shaped computation
    (the frozen impl discharging all three ensures is that witness).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is a transparent ``def`` over
    the two inputs, not an axiomatized oracle; the ``axioms`` region is empty.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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

WITNESS MECHANICS. The tester path (``derive_tester_for`` → ``…Tester args =
false := by decide``) is DEAD here: the existential clause C3
(``∃ rest, out = mountPrefix ++ rest``) makes ``prove_postcondition_decidable_for
appendSlashRedirect`` yield a ``Decidable`` instance with no executable code, so
``derive_tester_for`` emits a stuck tester and ``decide`` cannot reduce it
(measured: the tester build fails identically for a wrong rival and for gold,
discriminating nothing). But the carrier is fully transparent, so each witness
reaches the impl through Velvet's extractor instead: ``appendSlashRedirectExec mp
lp`` is ``NonDetT.run (appendSlashRedirect mp lp)``, and the witness states, at a
concrete input,

    appendSlashRedirectExec <mp> <lp> ≠ DivM.res (redirectTarget <mp> <lp>)

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator can see. This bundle's GOLD impl is ALSO
straight-line (the modeled surface is a bare assembly, no loop), so the
discrimination does not rely on gold being stuck: against the frozen solution
``appendSlashRedirectExec mp lp`` reduces to exactly ``redirectTarget mp lp``, so
the ``≠`` is provably FALSE and ``decide`` reports the negation is false — the
witness FAILS on gold, exactly the discrimination the gate requires. Each rival
is a straight-line closed form whose extracted program reduces to a literal that
differs from the post-image at the probed input, so the witness ELABORATES
against the rival. ``List Char`` literals via ``"…".toList`` are fully concrete,
so ``decide`` settles the residual equality — no opaque term, no carrier
conditioning, no head binders (hence no consistency obligation). Every witness
was checked out-of-band with ``scripts/lean_verify.sh``: rival exit 0, gold build
fails (``decide`` proves the negation false).
"""
from pathlib import Path

INSTANCE = "django__django-14404"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE two-line impl body; lies wholly inside
# ---- the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap). Anchoring on the
# ---- whole body keeps every surgery inside the elided region — the frozen spec
# ---- (the `method` header, the three `ensures`, and the `pure` region that
# ---- defines `fullPath`/`redirectTarget`) is never touched, so same_spec holds
# ---- and the prove_correct statement stays byte-identical. ----
_IMPL = (
    "    let result := fullPath mountPrefix localPath ++ ['/']\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble + builder. The tester+`decide` path is DEAD (the
# ---- existential C3 makes the postcondition's Decidable instance noncomputable),
# ---- so extract the executable program and refute C1 directly against the
# ---- TRANSPARENT `redirectTarget`. Checked in a file whose `prove_correct` block
# ---- is stripped, so no tactic script can mask the verdict. The rival's
# ---- straight-line `…Exec` reduces under `decide` to a literal that differs from
# ---- the post-image; gold's `…Exec` reduces to exactly `redirectTarget mp lp`, so
# ---- the `≠` is provably false and the witness FAILS on gold. ----
_EXTRACT = "extract_program_for appendSlashRedirect\n\n"


def _witness(mp: str, lp: str) -> str:
    return _EXTRACT + (
        "example :\n"
        f"    appendSlashRedirectExec {mp} {lp}"
        f" ≠ DivM.res (redirectTarget {mp} {lp}) := by\n"
        "  unfold appendSlashRedirectExec appendSlashRedirect\n"
        "  simp [NonDetT.run, pure]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify against the frozen `prove_correct` script, else
    # SPEC-TOO-STRONG. Both verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-cheapest-render",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying the clause: return the transparent
        # `redirectTarget` directly. Because `redirectTarget` is a spelled-out
        # `def` over the two inputs (not an opaque oracle), this still does the
        # real string assembly — there is no wrong echo that verifies.
        # Re-expresses the nagini honest-echo/grounded-oracle control (the
        # cheapest impl satisfying the grounded pin, showing the spec is not
        # echo-vulnerable: any wrong assembly fails `out = redirectTarget …`).
        "module": _with_impl(
            "    let result := redirectTarget mountPrefix localPath\n"
            "    return result"),
        "rationale": "the post-image `redirectTarget mountPrefix localPath` is "
                     "GROUNDED in the two inputs (a transparent concatenation, no "
                     "opaque answer key), so returning it directly is the honest "
                     "cheapest CORRECT impl; C1 is literally `out = redirectTarget "
                     "…`, so it MUST verify, else C1 is SPEC-TOO-STRONG. Also shows "
                     "the spec is not echo-vulnerable: any wrong assembly fails "
                     "`out = redirectTarget …`. Scope of the claim, stated exactly: "
                     "this body is gold's modulo delta-unfolding `redirectTarget` "
                     "and is DEFINITIONALLY equal to it (`rfl` closes the "
                     "equation), so it is a cheap control, not a reshape probe — "
                     "`pos-branch-empty-prefix` carries the non-defeq reshape.",
    },
    {
        "id": "pos-explicit-concat",
        "kind": "soundness",
        "expect": "verify",
        # A different SOURCE form: spell the concatenation out explicitly
        # (`mountPrefix ++ localPath ++ ['/']`) rather than routing through
        # `fullPath`/`redirectTarget`. Note honestly what this does and does not
        # test: `++` is infixl in Lean 4, so this parses as
        # `(mountPrefix ++ localPath) ++ ['/']`, which is gold's body after
        # delta-unfolding `fullPath` — DEFINITIONALLY equal, `rfl`-closable
        # (measured: `example (mp lp : List Char) : (mp ++ lp ++ ['/']) =
        # fullPath mp lp ++ ['/'] := rfl` elaborates). So it pins that the spec
        # is not over-fit to the `redirectTarget`-CALL form, and nothing more.
        # The positive that carries a genuinely non-defeq reshape is
        # `pos-branch-empty-prefix` below; that is the one defending against a
        # proof script tuned to the frozen TERM.
        "module": _with_impl(
            "    return (mountPrefix ++ localPath ++ ['/'])"),
        "rationale": "a correct impl with a DIFFERENT source form (the "
                     "concatenation spelled out explicitly rather than routed "
                     "through `fullPath`/`redirectTarget`) must verify against C1 "
                     "and C2. Scope of the claim, stated exactly: `++` is infixl, "
                     "so this term is gold's after delta-unfolding `fullPath` and "
                     "is DEFINITIONALLY equal to it (`rfl` closes the equation). "
                     "It therefore refutes over-fitting to the `redirectTarget`-call "
                     "FORM only; it does NOT show the proof survives a non-defeq "
                     "reshape — `pos-branch-empty-prefix` does that. If it fails "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-branch-empty-prefix",
        "kind": "soundness",
        "expect": "verify",
        # The load-bearing positive: a CORRECT impl that is NOT definitionally
        # equal to gold. It introduces a genuine case split on whether the
        # mount-point prefix is empty and returns the separately-spelled correct
        # answer on each branch (when the prefix is empty, `mountPrefix ++
        # localPath ++ ['/']` IS `localPath ++ ['/']`, so both branches are
        # faithful). `rfl` does NOT close this against gold's body — measured:
        # `example (mp lp : List Char) : (if mp.isEmpty then lp ++ ['/'] else
        # mp ++ lp ++ ['/']) = fullPath mp lp ++ ['/'] := rfl` FAILS — so the
        # frozen proof script has to discharge the branch rather than reduce it
        # away. This is the real counterpart of the nagini
        # `pos-control-earlyexit` positive (a structurally different CONTROL
        # shape), which the accounting below previously recorded as having no
        # counterpart on this carrier; a branch on an input carrier is expressible
        # here, so the case is ported rather than dropped.
        "module": _with_impl(
            "    let result := if mountPrefix.isEmpty then localPath ++ ['/']\n"
            "                  else mountPrefix ++ localPath ++ ['/']\n"
            "    return result"),
        "rationale": "the strongest SPEC-TOO-STRONG probe in this battery: a "
                     "CORRECT impl that is NOT definitionally equal to the frozen "
                     "one. It case-splits on whether the mount-point prefix is "
                     "empty and spells the correct destination out per branch "
                     "(both branches agree with `redirectTarget`, since an empty "
                     "prefix contributes nothing to the concatenation). `rfl` does "
                     "not close it against gold's body, so verifying requires the "
                     "frozen proof to discharge an honest case split — which is "
                     "exactly what the two delta-reduction positives above cannot "
                     "test. If it fails => SPEC-TOO-STRONG (the obligation is "
                     "over-fit to the frozen TERM shape, not merely to a call "
                     "form). Ports the nagini structurally-different "
                     "control-shape positive onto this carrier.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-selfcall. That case established
    # the read-only precondition `Acc(list_pred(.),1/2)` on an F2P-shaped input.
    # This method carries NO `require` clause (the pre-conditions region is
    # empty), so nothing could exclude a normal input and the classic "a normal
    # input is admitted" probe is vacuous. Re-aimed at the residual total-domain
    # risk: that the three-clause post-image (C1, C2, C3) is jointly SATISFIABLE
    # by a gold-shaped computation. The frozen impl discharging all three ensures
    # IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": "the input carries no `require`, so the assembly is total over "
                     "every (mountPrefix, localPath) pair; the gold impl "
                     "discharging all three ensures is the admissibility witness "
                     "that the post-image (C1 whole-string equality, C2 explicit "
                     "concatenation, C3 prefix-preservation) is jointly satisfiable. "
                     "Near-trivial precisely because the precondition is empty. "
                     "Re-aimed from the nagini admiss-selfcall, whose read-only "
                     "precondition half has no counterpart on this referentially-"
                     "transparent carrier. Else SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line closed form with a
    # machine-checked refutation witness at a concrete input (ELABORATES against
    # the rival, FAILS against gold — both halves confirmed out-of-band with real
    # builds) and the refinement argument for why its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-wrong-source",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug: assemble the destination from the local path alone,
        # dropping the mount-point prefix. Correct only when the prefix is empty
        # (server-root mount), wrong on every non-empty-prefix input.
        "module": _with_impl(
            "    let result := localPath ++ ['/']\n"
            "    return result"),
        "refinement": "this is the pre-change behaviour: the destination is built "
                      "from the per-request local path alone, so the deployment "
                      "mount-point prefix is dropped. Its faithful real counterpart "
                      "is the unpatched expression, which redirects a client served "
                      "under a non-empty mount point to a URL OUTSIDE that mount "
                      "point (the prefix is gone). The two failing tests serve the "
                      "app under a non-empty mount point and assert the redirect "
                      "target still carries the prefix; a destination missing the "
                      "prefix does not, so it would NOT resolve. This is the exact "
                      "defect the fix corrects.",
        "rationale": "REJECT from C1/C2/C3: with the prefix dropped, the assembled "
                     "string differs from `redirectTarget mountPrefix localPath` "
                     "(C1/C2) AND does not begin with `mountPrefix` (C3) whenever "
                     "`mountPrefix` is non-empty and not a prefix of `localPath`. "
                     "Correct only on the empty-prefix sub-domain, wrong on every "
                     "non-empty prefix (partial-domain). Refuted at "
                     "`mountPrefix=\"p\"`, `localPath=\"x\"`. If it verified => "
                     "SPEC-TOO-WEAK (admits the bug).",
        "witness": _witness('"p".toList', '"x".toList'),
    },
    {
        "id": "weak-no-trailing-slash",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble from the FULL path (prefix preserved, C3 holds) but WITHOUT the
        # trailing separator. Pins the source correctly; the destination is the
        # bare full path, not the slash-terminated form.
        "module": _with_impl(
            "    let result := fullPath mountPrefix localPath\n"
            "    return result"),
        "refinement": "returning the full path WITHOUT the appended separator is "
                      "not a slash-appending redirect at all — the whole point of "
                      "the append-slash branch is to redirect the slash-LESS URL to "
                      "its slash-terminated form. A faithful counterpart returning "
                      "the bare full path redirects to the same slash-less URL, an "
                      "immediate redirect loop, and the failing tests assert the "
                      "target ends with the separator, so it would NOT resolve.",
        "rationale": "REJECT from C1/C2: the prefix IS preserved (so C3 still "
                     "holds), but the destination lacks the trailing separator "
                     "(code point '/') the post-image `redirectTarget … = fullPath "
                     "… ++ ['/']` pins. A distinct failure mode from wrong-source "
                     "(right source, missing separator vs. wrong source). Refuted "
                     "at `mountPrefix=\"q\"`, `localPath=\"y\"`. If it verified => "
                     "SPEC-TOO-WEAK (the trailing separator is load-bearing).",
        "witness": _witness('"q".toList', '"y".toList'),
    },
    {
        "id": "weak-drop-local",
        "kind": "uniqueness",
        "expect": "reject",
        # Placement attack on the OTHER binder: assemble prefix + separator only,
        # omitting the local path entirely. Independent of the prefix (C3 still
        # holds, `rest = ['/']`), so it varies `localPath` and is refutable via
        # the whole-string clauses C1/C2.
        "module": _with_impl(
            "    let result := mountPrefix ++ ['/']\n"
            "    return result"),
        "refinement": "drops the per-request local path from the destination, "
                      "leaving only the mount-point prefix and a separator. Its "
                      "faithful real counterpart redirects to the mount point root "
                      "rather than to the requested resource's slash-terminated "
                      "form, so the failing tests (which assert the target is the "
                      "requested URL plus a slash) still fail; it would NOT "
                      "resolve.",
        "rationale": "REJECT from C1/C2, whose post-image places `localPath` "
                     "between the prefix and the trailing separator. The rival "
                     "omits it, so the assembled string differs whenever "
                     "`localPath` is non-empty. C3 still holds here (`rest = "
                     "['/']`), so this rival is caught ONLY by the whole-string "
                     "clauses — it is what VARIES the `localPath` binder and does "
                     "NOT depend on `mountPrefix` for its refutation. Refuted at "
                     "`mountPrefix=\"a\"`, `localPath=\"b\"`. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness('"a".toList', '"b".toList'),
    },
    {
        "id": "weak-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Ordering attack: emit the local path BEFORE the prefix. Both inputs are
        # present and the separator is correct, but the prefix-first ordering C3
        # demands is violated (the destination begins with the local path).
        "module": _with_impl(
            "    let result := localPath ++ mountPrefix ++ ['/']\n"
            "    return result"),
        "refinement": "emits the local path before the mount-point prefix. Its "
                      "faithful real counterpart produces a destination whose "
                      "leading component is the local path, not the mount point, so "
                      "a client served under a non-empty mount point is redirected "
                      "to a URL that does not begin under that mount point — the "
                      "failing tests assert the target begins with the prefix, so "
                      "it would NOT resolve.",
        "rationale": "REJECT from C1/C2/C3: both inputs are present and the "
                     "separator is correct, but the ordering is wrong. The "
                     "destination `localPath ++ mountPrefix ++ ['/']` differs from "
                     "the pinned `mountPrefix ++ localPath ++ ['/']` (C1/C2) AND, "
                     "when `localPath` is not itself prefixed by `mountPrefix`, "
                     "does not begin with `mountPrefix` (C3). A distinct failure "
                     "mode (right pieces, wrong order) that attacks the "
                     "prefix-first structural clause C3 as well. Refuted at "
                     "`mountPrefix=\"m\"`, `localPath=\"n\"`. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness('"m".toList', '"n".toList'),
    },
    {
        "id": "weak-empty-prefix-drop-sep",
        "kind": "uniqueness",
        "expect": "reject",
        # SUB-DOMAIN rival, added by the audit. Every rival above is refuted at a
        # NON-EMPTY mount-point prefix, so the four witness points {p,q,a,m} x
        # {x,y,b,n} all live on the same side of the one boundary this carrier
        # has: whether the prefix is empty. That left the empty-prefix
        # sub-domain — the server-root mount, which is the COMMON deployment —
        # entirely unprobed, and a rival can be wrong there while being correct
        # everywhere the rest of the battery looks.
        #
        # This rival is correct on EVERY non-empty prefix and drops the trailing
        # separator only when the prefix is empty. Measured: the standard witness
        # at `mountPrefix="p"` does NOT refute it (build exit 1 — `decide` proves
        # the negation false, i.e. the rival AGREES with the post-image there), so
        # it is refutable only at the empty-prefix point, which is why the witness
        # below probes `""`.
        "module": _with_impl(
            "    let result := if mountPrefix.isEmpty then localPath\n"
            "                  else mountPrefix ++ localPath ++ ['/']\n"
            "    return result"),
        "refinement": "its faithful real counterpart omits the trailing separator "
                      "exactly when the application is served at the server root "
                      "(empty mount-point prefix) and is otherwise correct. That "
                      "redirects a root-mounted client back to the same "
                      "slash-less URL — an immediate redirect loop — on the most "
                      "common deployment, while behaving correctly under a "
                      "non-empty mount point. The failing tests assert the target "
                      "ends with the separator, so it would NOT resolve; and note "
                      "it is a strictly HARDER rival than the others, because it "
                      "agrees with the spec at every input the rest of the battery "
                      "probes.",
        "rationale": "REJECT from C1/C2 on the EMPTY-PREFIX sub-domain, the one "
                     "boundary this carrier has and the one no other rival "
                     "touches. When `mountPrefix` is empty the post-image is "
                     "`localPath ++ ['/']` but the rival returns `localPath`, so "
                     "the trailing separator is missing; when `mountPrefix` is "
                     "non-empty the rival is exactly gold, so C1/C2/C3 all hold "
                     "there. Refuted at `mountPrefix=\"\"`, `localPath=\"x\"` — a "
                     "FIFTH, genuinely distinct input tuple that is the only point "
                     "in the battery with an empty binder. If it verified => "
                     "SPEC-TOO-WEAK (the spec would be blind to a partial-domain "
                     "defect on the server-root mount).",
        "witness": _witness('"".toList', '"x".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 uniqueness rivals) plus
# a 1-case AXIOM lane. This velvet bundle is a CARRIER-NARROWED model of only the
# purely-functional redirect-DESTINATION ASSEMBLY (the changed expression) — it
# does NOT model the surrounding control flow (the four-guard conjunction / the
# NotFound exception), which is outside the modeled surface. So the two
# control-flow-guard rivals have NO counterpart, the two frame rivals are vacuous
# on a referentially-transparent carrier, and the two value rivals port; two
# rivals are ADDED for binder/clause coverage of the assembly.
#
#   nagini case                 -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-control-flatten         -> pos-explicit-concat          RE-EXPRESSED (defeq)
#   pos-control-earlyexit       -> pos-branch-empty-prefix       PORTED (non-defeq branch)
#   admiss-selfcall             -> admiss-gold-total             RE-AIMED
#   frame-mutate-fullpath       -> (none)                       VACUOUS (no heap/mut)
#   frame-mutate-relpath        -> (none)                       VACUOUS (no heap/mut)
#   weak-wrong-source (the bug) -> weak-wrong-source            PORTED
#   weak-drop-optin-guard       -> (none)                       NO COUNTERPART (guard unmodeled)
#   weak-drop-trailing-guard    -> (none)                       NO COUNTERPART (guard unmodeled)
#   weak-no-trailing-slash      -> weak-no-trailing-slash       PORTED
#   (no sibling — binder cover) -> weak-drop-local              ADDED
#   (no sibling — binder cover) -> weak-swap-order              ADDED
#   (no sibling — empty-prefix) -> weak-empty-prefix-drop-sep    ADDED (sub-domain)
#   AXIOM_TESTS (1)             -> (none)                       DROPPED (G-AX lane)
#
# 9 velvet SPEC cases: 3 soundness, 1 admissibility, 5 uniqueness.
#
# DEFINITIONAL-EQUALITY ACCOUNTING (added by audit; this is the fact that decides
#   what each positive actually tests). `pos-cheapest-render` and
#   `pos-explicit-concat` are both DEFINITIONALLY equal to the frozen body —
#   measured, `rfl` closes both equations against `fullPath mp lp ++ ['/']`
#   (`++` is infixl, so `mp ++ lp ++ ['/']` IS `(mp ++ lp) ++ ['/']`). A defeq
#   positive verifies by delta-reduction, so it cannot detect a proof script
#   tuned to the frozen TERM; it only rules out over-fitting to the CALL form.
#   `pos-branch-empty-prefix` is the non-defeq positive (`rfl` FAILS against
#   gold's body — measured), so it is the case that actually exercises the
#   frozen script on a different term shape. All three verify.
#
# RE-EXPRESSED (pos-cheapest-render, pos-explicit-concat): the nagini file carries
#   two positive controls that RESHAPE the four-guard control flow (flatten the
#   nested ifs; raise-early per disjunct) while keeping the gold construction
#   verbatim. The ASSEMBLY reshapes here are: return the transparent
#   `redirectTarget` directly (the echo-honest / grounded-oracle control: cheapest
#   correct impl, showing the spec is not echo-vulnerable), and spell the
#   concatenation out explicitly. Both are defeq to gold (see above), so the
#   structural-difference claim the nagini positives made is carried by
#   pos-branch-empty-prefix, not by these two. All verify under the frozen proof
#   (real builds).
# PORTED (pos-control-earlyexit -> pos-branch-empty-prefix): the nagini
#   early-exit positive's content is "a structurally DIFFERENT control shape,
#   behaviourally identical, still verifies". That IS expressible here: branch on
#   whether the mount-point prefix is empty and spell the correct destination per
#   branch. Not defeq to gold, so the frozen script must discharge the split.
#   Previously recorded as NO COUNTERPART on the ground that this carrier has no
#   control flow to reshape; the audit found a branch on an input carrier is
#   expressible, so the case is ported rather than dropped.
# RE-AIMED (admiss-selfcall -> admiss-gold-total): the nagini case established the
#   read-only fractional-permission precondition on an F2P-shaped input. This
#   method has no `require` and no heap permission, so that probe is vacuous;
#   re-aimed at the residual total-domain risk (joint satisfiability of the three
#   ensures), witnessed by the frozen impl discharging all three.
# PORTED (2 value rivals): weak-wrong-source (assemble from the local path alone —
#   EXACTLY the pre-patch bug, the prefix-dropping expression the fix removes) and
#   weak-no-trailing-slash (right source, missing separator) carry their nagini
#   refinement arguments across intact — only the carrier changes from a nagini
#   `List[int]` construction to a Velvet `List Char` assembly. Each is backed by a
#   machine-checked witness.
# ADDED (2): weak-drop-local (omit the local path — attacks C1/C2 with C3 holding,
#   varies the `localPath` binder) and weak-swap-order (local path before prefix —
#   attacks the prefix-first structural clause C3 as well). Real divergences with
#   machine-checked witnesses, added so both input binders are attacked and each
#   independent postcondition clause (the whole-string equality C1/C2 and the
#   prefix-preservation C3) is attacked by some rival. Not fabricated wrongness.
# NO COUNTERPART (weak-drop-optin-guard, weak-drop-trailing-guard): these two
#   nagini cases attach to the FOUR-GUARD CONTROL FLOW of the surrounding
#   request-dispatch routine (whether a value is returned or NotFound is raised,
#   and on which guard sub-domain). This velvet bundle models only the
#   redirect-DESTINATION expression — there are no guard inputs, no exception
#   return, and no `require` — so those cases have nothing to attach to. This is
#   carrier narrowing (the Lean-family bundle contracts only the purely-functional
#   core, 433/500 with a single `prove_correct`), NOT an effort gap; chasing them
#   would mean fabricating rivals for behaviour this bundle does not model.
#   (pos-control-earlyexit is NO LONGER in this class — see PORTED below.)
# FRAME-MUTATION (frame-mutate-fullpath, frame-mutate-relpath): VACUOUS. The
#   nagini rivals write through a read-only (1/2) reference to an input and are
#   rejected for insufficient permission. Velvet is referentially transparent,
#   both inputs are immutable values, no `mut` binder, no heap, no aliasing, no
#   permission system. There is no read-only input to overwrite. No substitute
#   fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
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
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness premise probe (that
#   the request's full client-facing path carries the deployment mount-point
#   prefix) is G-AX's job (axiom_check.py / mapping.md validate the `fullPath`
#   deep A-reference == the real framework attribute); the G-PBT gate ignores
#   AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The postcondition has two INPUT binders
#   (`mountPrefix`, `localPath`) and two independent top-level obligations: the
#   whole-string equality (C1 ≡ C2) and the prefix-preservation existential (C3).
#   - C1/C2 attacked by all five rivals (wrong-source, no-slash, drop-local,
#     swap-order, empty-prefix-drop-sep) — every one produces a string ≠
#     `mountPrefix ++ localPath ++ ['/']` at its witness point.
#   - C3 (prefix preservation) attacked by wrong-source (drops the prefix) and
#     swap-order (prefix no longer leading); drop-local deliberately KEEPS C3
#     (`rest = ['/']`) so it isolates the C1/C2-only failure mode, and no-slash
#     keeps C3 so it isolates the missing-separator mode.
#   - `mountPrefix` is mishandled by wrong-source (dropped) and swap-order
#     (misplaced); `localPath` is mishandled by drop-local (dropped) and
#     swap-order (misplaced). Neither binder is held fixed: across the five
#     witnesses `mountPrefix` takes {"p","q","a","m",""} and `localPath` takes
#     {"x","y","b","n","x"}, five DISTINCT input tuples.
#   - SUB-DOMAIN. The single boundary the carrier has is whether `mountPrefix` is
#     empty (server-root mount vs. a genuine mount point). The first four rivals
#     all sit on the non-empty side; `weak-empty-prefix-drop-sep` is the only
#     probe on the empty side, and it is a rival that AGREES with the spec at
#     every one of the other four points. Without it the battery's point set was
#     one-sided, which the advisory coverage reporter does not detect (it counts
#     distinct tuples, not distinct sub-domains).
#   All three positives and the admissibility case defend all three clauses; only
#   `pos-branch-empty-prefix` does so from a non-defeq term (see above).
# WITNESS DISCRIMINATION (verified during authoring with two real builds per
#   reject case): the tester+`decide` path is DEAD (the existential C3 makes the
#   postcondition's Decidable instance noncomputable, so `derive_tester_for`
#   yields a stuck tester — measured to fail identically for rival and gold).
#   Every witness instead extracts the executable program and refutes C1 directly
#   against the TRANSPARENT `redirectTarget`: each rival's straight-line `…Exec`
#   reduces under `decide` to a literal ≠ the post-image (ELABORATES), while gold's
#   `…Exec` reduces to exactly `redirectTarget mp lp`, making the `≠` provably
#   false so `decide` reports the negation false (FAILS on gold). No witness binds
#   a hypothesis (every input is a concrete literal), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears. All five confirmed with scripts/lean_verify.sh: rival exit 0, gold
#   build fails.
#
# AUDIT RE-DERIVATION (independent, real builds; exit codes recorded so a reader
#   need not re-run them). Every claim above was re-checked rather than trusted:
#   - Each of the five witnesses rebuilt twice: rival exit 0, gold exit 1, for all
#     five. Gold's failure text is a SEMANTIC refutation in every case —
#     "Tactic `decide` proved that the proposition ¬fullPath [..] ++ ['/'] =
#     redirectTarget [..] is false" — not an unknown identifier, type error,
#     unfolding failure, or timeout, so each is a real discriminator.
#   - STUCK-REDUCTION control: the OPPOSITE claim (`=` in place of `≠`) at the
#     same point builds against gold at exit 0. So `decide` genuinely evaluates
#     here and gold's exit 1 is a refutation the kernel performed, not a term it
#     failed to reduce (the `witness-undecided` trap).
#   - FALSE-POSITIVE control: the wrong-source witness was rebuilt against a
#     CORRECT non-defeq reshape (`(mp ++ lp ++ ['/']).reverse.reverse`) and FAILS
#     there (exit 1), as it must — the witnesses discriminate WRONG impls, not
#     merely reshaped ones.
#   - The "tester path is DEAD" claim is confirmed as stated: with
#     `extract_program_for` present, `prove_postcondition_decidable_for` leaves
#     `⊢ Decidable (∃ rest, out = mountPrefix ++ rest)` unsolved and the tester's
#     `decide` reports it "did not reduce to `isTrue` or `isFalse`" — identically
#     for rival and gold (both exit 1). So the extractor route the witnesses use
#     is necessary, not a convenience.
#   - SPEC-TOO-WEAK probe: eight NEW wrong impls beyond this battery's rivals were
#     built against the frozen spec — double separator; duplicated prefix (C3
#     holds); separator between prefix and local path; a non-'/' separator (C3
#     holds); empty output; and three sub-domain near-misses branching on an empty
#     prefix / empty local path. ALL EIGHT were rejected (exit 1). No spec hole
#     found. Two of the sub-domain near-misses were adopted/derived into
#     `weak-empty-prefix-drop-sep`.
#   - SPEC-TOO-STRONG probe: eight NEW correct impls were built — `List.append`,
#     `Char.ofNat 47`, both associativities, `List.concat`, `.reverse.reverse`,
#     and two branch-on-empty-binder shapes. ALL EIGHT verified (exit 0),
#     including the three that are NOT definitionally equal to gold
#     (`.reverse.reverse`, `.concat`, the branching ones — `rfl` fails on each),
#     so the frozen proof is not over-fit to the frozen term. No soundness hole.
#   - The DIVERGENCE lane needs no re-measurement: this bundle is `total`, under
#     which a diverging rival is REJECTED rather than verifying vacuously.
AXIOM_TESTS = []
