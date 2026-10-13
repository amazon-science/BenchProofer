"""properties.py — G-PBT falsification battery for django__django-11999 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct registerAccessor`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  registerAccessor (lookup : Namespace) (key : String) (gen : Nat)
      return (out : Namespace)
    ensures out = registerDisplay lookup key gen

The method registers a generated accessor onto a class namespace, modeled as the
total map ``Namespace = String → Option Nat`` (``some t`` at a name bound to an
attribute of identity-kind ``t``, ``none`` at a free name). The single
load-bearing ``ensures`` pins the WHOLE post-namespace, as a function, to the
transparent ``def registerDisplay`` — the set-if-absent update:

    registerDisplay lookup key gen
      = if (lookup key).isNone then (set key := some gen) else lookup

There is NO opaque answer-key oracle in the clause: ``registerDisplay`` is a
total ``def`` over the method's own arguments, so pinning ``out =
registerDisplay lookup key gen`` is grounded, not an echo. Two independent
top-level outcomes are folded into the one equality, and every rival attacks one:

  * FREE branch — when ``key`` is currently free the accessor ``gen`` is
    installed AT ``key`` and NOWHERE else.
  * BOUND branch — when ``key`` is already bound the namespace is returned
    UNCHANGED, so an existing (author-supplied) accessor at ``key`` SURVIVES —
    the behaviour the F2P observes: a model that supplies its own display
    accessor keeps it, rather than being displaced by the generated one.

THREE INPUT BINDERS, all load-bearing: ``lookup`` selects the branch (via
``(lookup key).isNone``) and supplies every unchanged entry; ``key`` is the name
tested and (on the free branch) written; ``gen`` is the installed identity on the
free branch. The reject witnesses drive the triple to SEVEN distinct input points
so the manifest demonstrates the post-image's dependence on which branch fires,
on the installed identity, on the WRITE TARGET, on the untouched frame in BOTH
directions (no binding added at another name, and no binding at another name
erased), and on the preserved binding at ``key`` — not on a single pinned shape
(pts = 7).

CARRIER NOTE — WHY WITNESSES ARE POINTWISE. The post-image is a FUNCTION equality
(``out = registerDisplay lookup key gen`` over ``String → Option Nat``), which is
not decidable: ``prove_postcondition_decidable_for`` / ``derive_tester_for``
cannot yield a computable tester, so the ``…Tester = false := by decide`` path is
DEAD here. But every rival and gold alike is a LOOP-FREE impl (no ``while``), so
its extracted program ``registerAccessorExec`` reduces fully under ``decide`` at a
concrete input. Each witness therefore refutes the equality POINTWISE — it states
that the rival's extracted output, applied to one concrete name, DIFFERS from
``registerDisplay …`` applied to that same name:

    (match registerAccessorExec <lookup> <key> <gen> with
       | DivM.res r => r | _ => (fun _ => none)) <probe>
      ≠ registerDisplay <lookup> <key> <gen> <probe>

A single differing point disproves the function equality, so this IS a genuine
violation of the ``ensures``. Against the FROZEN solution the same statement fails
(``decide`` proves the proposition is FALSE) — gold agrees with ``registerDisplay``
at every point — which is the required FAIL-on-gold half. No witness binds any
hypothesis (every input is a concrete literal that decides the point), so no
consistency probe is needed, and no banned token (sorry/admit/native_decide/
axiom/opaque) appears. Every witness was checked out-of-band with
``scripts/lean_verify.sh``: each ELABORATES against its rival (exit 0) and FAILS
against gold (a ``decide`` error).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but CORRECT
    impl (return the grounded model directly; make the free/bound split explicit
    via ``isSome``) must verify, else the spec is SPEC-TOO-STRONG on the shape of
    the impl.
  * ADMISSIBILITY — the method carries NO ``require`` (the pre-conditions region
    is empty), so the nagini "a normal F2P-shaped input satisfies the
    precondition" probe is degenerate: nothing could exclude a normal input. The
    residual admissibility risk on this total domain is a DEGENERATE post-image, a
    spec no impl distinguishes. ``admiss-nondegenerate`` discharges an in-region
    ``assert`` pinning BOTH outcomes (install-when-free / preserve-when-bound) at
    F2P-shaped inputs; the impl is kept verbatim so the method's own obligation
    still discharges.
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling holds ``cls`` at full
    permission and, per its own DEFENDED SURFACE prose, has no read-only input to
    subvert; its reachable analogue is a VALUE-level clobber of an unrelated
    attribute, which IS ported here (rival-clobber-* below). Lean/Velvet are
    referentially transparent — ``lookup`` is an immutable value, no ``mut``
    parameter escapes the ``do`` block, there is no heap, aliasing, or permission
    system — so the permission-subversion class proper has no carrier analogue.
    The value-level frame attack it reduces to is carried; no permission substitute
    is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image is
    ``registerDisplay lookup key gen``, a transparent ``def`` over the method's own
    arguments; there is no answer key to echo. The cheapest correct impl returns
    it directly and is carried as a POSITIVE control (it doubles as proof the spec
    is not echo-vulnerable: any wrong install/preserve fails the function equality
    at some point).
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
  * CONTROL-FLOW-EFFECT (raise/return difference) — N/A: the method returns a
    ``Namespace`` with no raise path; the only observable is the returned map,
    which the function-equality ensures fully pins.
"""
from pathlib import Path

INSTANCE = "django__django-11999"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE frozen impl block (markers INCLUDED): a single anchor lying
# ---- wholly inside the one -- impl-start .. -- impl-end region and unique in
# ---- the file (both asserted at load by _swap). Every variant replaces exactly
# ---- this text, keeping the two marker lines, so each edit lies inside the impl
# ---- region and same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    let mut result := lookup\n"
    "    if (lookup key).isNone then\n"
    "      result := (fun n => if n = key then some gen else lookup n)\n"
    "    return result\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the frozen proof (tactic body only; elided from the spec view). Rivals
# ---- KEEP it: it fails to close for a reshaped/wrong impl, which is what makes
# ---- the case "rejected", and the witness is what attributes that rejection to
# ---- the spec. A correct reshape whose residual goal changes shape retunes it.
_PROOF = "prove_correct registerAccessor by\n  loom_solve <;> simp_all [registerDisplay]"
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"


def _impl(new_block):
    """Full variant: whole impl block replaced (markers kept), proof frozen."""
    return _swap(_BASE, _IMPL, new_block)


def _impl_reproved(new_block, new_proof):
    """Impl block replaced AND the proof retuned (for a correct reshape whose
    residual goal no longer matches the frozen tactic script)."""
    return _swap(_impl(new_block), _PROOF, new_proof)


# ---- witness preamble. The post-image is a FUNCTION equality (not decidable),
# ---- so the tester+`decide` path is dead; instead extract the executable
# ---- program and refute the equality POINTWISE against the transparent
# ---- `registerDisplay`. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can mask the verdict. Every argument is a
# ---- concrete literal so the loop-free `…Exec` reduces under `decide`.
_EXTRACT = "extract_program_for registerAccessor\n\n"


def _witness(lookup_lit, key_lit, gen_lit, probe_lit):
    """A pointwise refutation: the rival's extracted output at `probe_lit`
    differs from `registerDisplay`'s at the same point."""
    return (
        _EXTRACT +
        "example :\n"
        f"    (match registerAccessorExec ({lookup_lit}) {key_lit} {gen_lit} with\n"
        "      | DivM.res r => r | _ => (fun _ => none)) " + probe_lit + "\n"
        f"      ≠ registerDisplay ({lookup_lit}) {key_lit} {gen_lit} {probe_lit} := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded model directly, no
        # branch at all — maximally structurally different from the gold guarded
        # update. `out` IS `registerDisplay lookup key gen`, so the ensures holds
        # on the whole domain and the frozen proof closes as-is. Grounded (the
        # model is the real set-if-absent work, not an opaque answer key), so this
        # is also the no-ungrounded-echo control: any wrong install/preserve fails
        # the function equality at some point.
        "module": _impl(
            "    -- impl-start\n"
            "    return registerDisplay lookup key gen\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`registerDisplay lookup key gen` directly (no branch). `out` IS that "
            "model, so the single `ensures` holds on the whole domain and the "
            "frozen proof closes unchanged. If this fails to verify the spec is "
            "over-fit to the guarded-update code shape (SPEC-TOO-STRONG). Also the "
            "no-ungrounded-echo control: the model is transparent over the inputs, "
            "so a direct return is correct, not a cheat. Ports the nagini "
            "pos-install-unconditional / echo argument."),
    },
    {
        "id": "pos-control-explicit-split",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different correct impl: make the free/bound split EXPLICIT
        # via `isSome` (preserve-when-bound handled first, install-when-free in the
        # else), mirroring the nagini preserve-reorder positive. Same value flow;
        # the residual goal changes shape (an `isSome` split rather than the
        # frozen `isNone` guard), so the proof is retuned with the Option
        # none/some bridging lemmas.
        "module": _impl_reproved(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isSome then\n"
            "      result := lookup\n"
            "    else\n"
            "      result := (fun n => if n = key then some gen else lookup n)\n"
            "    return result\n"
            "    -- impl-end",
            "prove_correct registerAccessor by\n"
            "  loom_solve <;> simp_all [registerDisplay, "
            "Option.isNone_iff_eq_none, Option.isSome_iff_ne_none]"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape: the free/bound split "
            "is made explicit via `(lookup key).isSome` (preserve-when-bound first, "
            "install-when-free in the else) instead of the frozen `isNone` guard. "
            "The value flow is unchanged so `out = registerDisplay lookup key gen` "
            "still holds on the whole domain; the reproof bridges `isSome`/`isNone` "
            "to `= none`/`≠ none`. Ports the nagini pos-preserve-reorder: if it "
            "fails => SPEC-TOO-STRONG (over-fit to the negated-guard spelling)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require`, so the nagini "a normal
    # input satisfies the precondition" probe is degenerate. Re-aimed at the
    # residual risk on this total domain: that the post-image is NON-DEGENERATE at
    # the F2P-shaped inputs. This case discharges an in-region `assert`, at fully
    # concrete inputs, that `registerDisplay` yields DISTINCT outcomes on the two
    # branches — installs `gen` at a free name (and touches no other name) AND
    # preserves an existing binding at a bound name. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the proof gains a
    # `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss (\n"
            "      registerDisplay (fun _ => none) \"k\" 5 \"k\" = some 5 ∧\n"
            "      registerDisplay (fun _ => none) \"k\" 5 \"other\" = none ∧\n"
            "      registerDisplay (fun s => if s = \"k\" then some 0 else none) \"k\" 5 \"k\" = some 0))\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isNone then\n"
            "      result := (fun n => if n = key then some gen else lookup n)\n"
            "    return result\n"
            "    -- impl-end",
            "prove_correct registerAccessor by\n"
            "  loom_solve <;> first\n"
            "    | decide\n"
            "    | simp_all [registerDisplay]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at F2P-shaped "
            "inputs: on a FREE name the generated identity `gen` (=5) is installed "
            "at `key` and NOWHERE else (`\"k\" ↦ some 5`, `\"other\" ↦ none`), and "
            "on an already-BOUND name the existing author identity (=0) is "
            "PRESERVED (`\"k\" ↦ some 0`, not overwritten by 5) — two genuinely "
            "distinct outcomes, the exact override-present scenario the F2P pins. "
            "The in-region assert must discharge (else the obligation is "
            "degenerate); the impl is kept verbatim so `out = registerDisplay …` "
            "still verifies. Re-aimed from the nagini admiss-* cases (no `require` "
            "and no permission surface on this carrier), else SPEC-UNSATISFIABLE / "
            "degenerate."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked pointwise refutation witness at
    # a DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack the one `ensures`
    # (`out = registerDisplay lookup key gen`); the three binders `lookup`, `key`,
    # `gen` are varied across the reject set (pts = 7).
    # =====================================================================
    {
        "id": "rival-preserve-overwrite",
        "kind": "uniqueness",
        "expect": "reject",
        # The EXACT pre-change regression: drop the guard and unconditionally
        # install the generated accessor, overwriting an author-defined one that
        # is already bound at `key`.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    result := (fun n => if n = key then some gen else lookup n)\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-change behaviour: the generated accessor is installed "
            "unconditionally, overwriting a hand-written accessor already bound at "
            "the name. Its faithful real patch is the unguarded registration; the "
            "failing test defines a model that supplies its own display accessor "
            "and asserts that its own accessor is what runs — the overwrite makes "
            "the generated accessor run instead (the wrong value), so it FAILS the "
            "F2P and would NOT resolve. This is exactly the defect the fix corrects."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` on the BOUND "
            "branch: when `key` is already bound the spec keeps `lookup` unchanged, "
            "but this rival overwrites `key` with `some gen`. Refuted at "
            "`lookup = (\"k\" ↦ some 3)`, `key = \"k\"`, `gen = 5`, probed at "
            "`\"k\"`: gold keeps `some 3`, the rival returns `some 5`. If it "
            "verified => SPEC-TOO-WEAK (admits the regression). Ports nagini U1 "
            "preserve-overwrite."),
        "witness": _witness(
            'fun s => if s = "k" then some 3 else none', '"k"', "5", '"k"'),
    },
    {
        "id": "rival-install-noop",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: handle nothing — return the namespace untouched, so on
        # the FREE branch no accessor is installed.
        "module": _impl(
            "    -- impl-start\n"
            "    return lookup\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful real patch of this shape guards so tightly the generated "
            "accessor is NEVER installed, so a plain choices field has no display "
            "accessor at all; the choices-and-display tests would have no accessor "
            "to call and break — it would NOT resolve. A partial-domain break: "
            "correct on every already-bound name (nothing to do), wrong on every "
            "free name."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` on the FREE branch: "
            "when `key` is free the spec installs `some gen` at `key`, but this "
            "rival leaves `lookup` unchanged (still `none` there). Refuted at "
            "`lookup = (fun _ => none)`, `key = \"a\"`, `gen = 7`, probed at "
            "`\"a\"`: gold gives `some 7`, the rival `none`. If it verified => "
            "SPEC-TOO-WEAK (the install outcome hollow). Ports nagini U2 "
            "install-noop."),
        "witness": _witness("fun _ => none", '"a"', "7", '"a"'),
    },
    {
        "id": "rival-install-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: on the FREE branch install the WRONG identity — `gen + 1`
        # instead of the generated `gen`. Picks the right branch and the right
        # name; only the installed value is wrong.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isNone then\n"
            "      result := (fun n => if n = key then some (gen + 1) else lookup n)\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "installs a DIFFERENT callable identity under the accessor name than "
            "the generated one. A faithful real patch of this shape binds the "
            "display accessor to a different method, so calling it returns the "
            "wrong thing — the choices-and-display tests break. It would NOT "
            "resolve. Correct on the branch and the name; wrong only on the "
            "installed identity."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` on the FREE branch "
            "via the installed IDENTITY: the spec installs `some gen`, this rival "
            "installs `some (gen + 1)`. Refuted at `lookup = (fun _ => none)`, "
            "`key = \"d\"`, `gen = 9`, probed at `\"d\"`: gold gives `some 9`, the "
            "rival `some 10` — a distinct point from install-noop (which mishandles "
            "the branch, not the value), varying `key`/`gen`. If it verified => "
            "SPEC-TOO-WEAK (the installed identity unpinned). Ports nagini U3 "
            "install-wrong-identity."),
        "witness": _witness("fun _ => none", '"d"', "9", '"d"'),
    },
    {
        "id": "rival-install-wrong-name",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. The reject set above varies the branch, the installed
        # VALUE, and the frame, but no rival attacks `key`'s role as the name
        # WRITTEN on the free branch: install-noop drops the write entirely,
        # install-wrong-identity keeps the name and changes the value, and the
        # clobber pair ADD a second name while still writing `key` correctly. So
        # "the accessor lands AT `key`" was pinned by no rival. This one takes the
        # right branch and installs the right identity at a name DERIVED from
        # `key` but not equal to it, leaving `key` itself free.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isNone then\n"
            "      result := (fun n => if n = key ++ \"!\" then some gen else lookup n)\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "registers the generated accessor under a name that is not the one "
            "queried, so the name that was tested for freedom stays free. A "
            "faithful real patch of this shape generates the accessor but binds "
            "it under a mis-derived name: the attribute the caller looks up is "
            "still absent, so a plain choices field has no usable display "
            "accessor while an unrelated name gains a stray one. It would NOT "
            "resolve. Correct on the branch and on the installed identity; wrong "
            "only on WHERE the binding lands."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` on the FREE "
            "branch via the WRITTEN NAME: the spec binds `some gen` at `key` "
            "itself, this rival binds it at `key ++ \"!\"` and leaves `key` "
            "`none`. Refuted at `lookup = (fun _ => none)`, `key = \"c\"`, "
            "`gen = 8`, probed at `key` itself: gold gives `some 8`, the rival "
            "`none`. Distinct from install-noop (which writes nothing at all) and "
            "from install-wrong-identity (which writes the right name), and it "
            "varies `key`/`gen` again. If it verified => SPEC-TOO-WEAK (the "
            "written name unpinned — `key` would be load-bearing only as the "
            "branch selector, not as the write target)."),
        "witness": _witness("fun _ => none", '"c"', "8", '"c"'),
    },
    {
        "id": "rival-clobber-other-install",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level frame attack (the reachable analogue of frame-mutation): on
        # the FREE branch install the accessor CORRECTLY at `key` but ALSO clobber
        # an unrelated name ("z") with `gen`.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isNone then\n"
            "      result := (fun n => if n = key then some gen else lookup n)\n"
            "      result := (fun n => if n = \"z\" then some gen else result n)\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "installs the accessor correctly but ALSO overwrites an unrelated name "
            "the class already carries. A faithful real patch of this shape "
            "silently corrupts an unrelated class attribute during registration; "
            "tests depending on that attribute break — it would NOT resolve. "
            "Correct at `key` and on the branch; wrong only on the frame (an "
            "unrelated name)."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` via the FRAME: the "
            "spec touches ONLY `key` on the free branch and leaves every other name "
            "as `lookup`, but this rival also writes `\"z\"`. Refuted at "
            "`lookup = (fun _ => none)`, `key = \"k\"`, `gen = 2`, probed at the "
            "UNRELATED name `\"z\"`: gold gives `none`, the rival `some 2`. The "
            "install outcome at `key` still holds, isolating the frame. If it "
            "verified => SPEC-TOO-WEAK (frame guarantee hollow). Ports nagini U4 "
            "clobber-other (install case) — the value-level analogue of the nagini "
            "frame-mutation class."),
        "witness": _witness("fun _ => none", '"k"', "2", '"z"'),
    },
    {
        "id": "rival-clobber-other-preserve",
        "kind": "uniqueness",
        "expect": "reject",
        # The same value-level frame attack on the BOUND branch: preserve the
        # bound accessor correctly (the gold no-op) but clobber an unrelated name
        # ("z") with `gen`.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isNone then\n"
            "      result := (fun n => if n = key then some gen else lookup n)\n"
            "    else\n"
            "      result := (fun n => if n = \"z\" then some gen else lookup n)\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "does the correct no-op on the already-bound accessor but clobbers an "
            "unrelated name. Same faithful-patch story as clobber-other-install "
            "(corrupts an unrelated class attribute during assembly), on the "
            "override-present branch — it would NOT resolve. Correct at `key` "
            "(preserved); wrong only on the frame."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` via the FRAME on "
            "the BOUND branch: when `key` is bound the spec returns `lookup` "
            "unchanged everywhere, but this rival writes the unrelated name `\"z\"`. "
            "Refuted at `lookup = (\"m\" ↦ some 4)`, `key = \"m\"`, `gen = 6`, "
            "probed at `\"z\"`: gold gives `none`, the rival `some 6`. The "
            "preserved binding at `key` still holds, isolating the frame in the "
            "preserve case — a DISTINCT input from clobber-other-install (which "
            "sits on the free branch), varying `lookup`/`key`/`gen`. If it verified "
            "=> SPEC-TOO-WEAK (frame guarantee hollow in the preserve case). Ports "
            "nagini U5 clobber-other (preserve case)."),
        "witness": _witness(
            'fun s => if s = "m" then some 4 else none', '"m"', "6", '"z"'),
    },
    {
        "id": "rival-frame-erase-others",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION (second pass). The two clobber rivals attack the frame by
        # ADDING a binding at an unrelated name, and both are witnessed at a probe
        # where `lookup` is `none`. So across the whole shipped reject set no
        # witness ever evaluates a point that is (a) different from `key` and
        # (b) already BOUND in the input — the direction "an existing binding at
        # some OTHER name SURVIVES" was pinned by nothing. Cross-checked: all six
        # shipped witnesses were built against this rival and every one of them
        # FAILS to elaborate (exit 1), so none of them catches it. This rival takes
        # the right branch and installs the right identity at the right name, then
        # DROPS every other binding (the `else` arm returns `none` instead of
        # `lookup n`), which is the dual of the clobber pair: erasure rather than
        # addition.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut result := lookup\n"
            "    if (lookup key).isNone then\n"
            "      result := (fun n => if n = key then some gen else none)\n"
            "    return result\n"
            "    -- impl-end"),
        "refinement": (
            "installs the generated accessor correctly at the queried name but "
            "wipes every OTHER name the namespace carried. A faithful real patch "
            "of this shape registers the accessor while discarding the rest of the "
            "class namespace it was handed, so every previously-bound attribute "
            "and method vanishes during assembly — far more than the display "
            "tests break, and it would NOT resolve. Correct on the branch, on the "
            "installed identity, and on the write target; wrong only on whether "
            "PRE-EXISTING bindings at other names are carried through."),
        "rationale": (
            "REJECT from `out = registerDisplay lookup key gen` via the FRAME in "
            "the PRESERVATION direction: on the free branch the spec's `else` arm "
            "returns `lookup n` at every name other than `key`, so a binding "
            "already present at another name must SURVIVE; this rival returns "
            "`none` there. Refuted at `lookup = (\"p\" ↦ some 3)`, `key = \"e\"`, "
            "`gen = 1`, probed at the unrelated but BOUND name `\"p\"`: gold gives "
            "`some 3`, the rival `none`. This is the first witness point in the "
            "reject set where the probed name is both distinct from `key` and "
            "non-`none` in the input — the clobber pair probe names that are "
            "`none` in `lookup` and catch only ADDED bindings, so an impl that "
            "ERASES the frame slipped past all of them (verified: all six other "
            "witnesses fail to elaborate against this rival). The install at "
            "`key` still holds for this rival (machine-checked), isolating the "
            "frame-preservation clause. If it verified => SPEC-TOO-WEAK (the "
            "frame guarantee only forbids additions, not erasures)."),
        "witness": _witness(
            'fun s => if s = "p" then some 3 else none', '"e"', "1", '"p"'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling models the fix as TWO functions over a class-attribute
# namespace `cls: Dict[int,int]` — `preserve_existing_accessor` (precond: name
# ALREADY present) and `install_missing_accessor` (precond: name ABSENT) —
# sharing one guarded-installation skeleton, and ships 9 SPEC cases (4 positives:
# 2 soundness + 2 admissibility; 5 uniqueness) plus an EMPTY axiom lane. This
# velvet bundle NARROWS the carrier to ONE total method `registerAccessor` whose
# single `ensures` pins the whole post-namespace (as a `String → Option Nat`
# function) to the set-if-absent `registerDisplay`. The two nagini functions are
# the two BRANCHES of that one equality here (bound ↔ preserve, free ↔ install),
# so every nagini case attaching to one function maps onto one branch of the one
# clause — a legitimate carrier narrowing, not a dropped surface.
#
#   nagini case                     kind          -> here                          disposition
#   ---------------------------------------------------------------------------------------------
#   pos-install-unconditional       soundness     -> pos-control-direct-model      RE-EXPRESSED
#   pos-preserve-reorder            soundness     -> pos-control-explicit-split     PORTED
#   admiss-install-fresh            admissibility -\
#   admiss-preserve-override-present admissibility -> admiss-nondegenerate (merged) RE-AIMED
#   rival-preserve-overwrite (U1)   uniqueness    -> rival-preserve-overwrite       PORTED
#   rival-install-noop (U2)         uniqueness    -> rival-install-noop             PORTED
#   rival-install-wrong-identity(U3) uniqueness   -> rival-install-wrong-identity   PORTED
#   rival-clobber-other-install(U4) uniqueness    -> rival-clobber-other-install    PORTED
#   rival-clobber-other-preserve(U5) uniqueness   -> rival-clobber-other-preserve   PORTED
#   (no nagini source)              uniqueness    -> rival-install-wrong-name       AUDIT-ADDED
#   (no nagini source)              uniqueness    -> rival-frame-erase-others       AUDIT-ADDED
#   AXIOM_TESTS (empty)             axiom         -> (none)                         N/A (G-AX)
#
# 10 velvet SPEC cases: 2 soundness, 1 admissibility, 7 uniqueness. EVERY nagini
# uniqueness rival is ported (each attacks a modeled branch of the one clause),
# plus TWO rivals with no nagini counterpart that audits of this battery added.
#
# AUDIT-ADDED (rival-frame-erase-others): a second audit pass found that BOTH
#   clobber rivals attack the frame only by ADDING a binding, and that both are
#   witnessed at a probe point where `lookup` is `none`. So no shipped witness ever
#   evaluated a name that is simultaneously distinct from `key` and already BOUND,
#   leaving "a pre-existing binding at another name SURVIVES" unpinned. Confirmed by
#   cross-check: all six then-shipped witnesses were built against a frame-ERASING
#   rival (install correctly at `key`, return `none` elsewhere) and every one failed
#   to elaborate. The new rival's own witness probes the bound name `"p"` (gold
#   `some 3`, rival `none`). No nagini counterpart: the nagini frame clauses are
#   per-key `Ensures(cls[other_name()] == Old(cls[other_name()]))` plus a quantified
#   Pq frame, which already forbid erasure there, so the gap is specific to how this
#   carrier folds the frame into one function equality.
#
# AUDIT-ADDED (rival-install-wrong-name): the ported reject set varies the branch,
#   the installed VALUE and the frame, but left `key`'s role as the WRITE TARGET
#   on the free branch unpinned — install-noop writes nothing, U3 writes the right
#   name with the wrong value, and U4/U5 write `key` correctly and add a second
#   name. A rival that installs the right identity at `key ++ "!"`, leaving `key`
#   free, closes that gap; its witness probes `key` itself (gold `some 8`, rival
#   `none`). The nagini sibling models the name as an `int` key it never perturbs,
#   so this attack has no nagini source case — it is a carrier-specific gap that
#   only the `String` key makes reachable.
#
# RE-EXPRESSED (pos-install-unconditional -> pos-control-direct-model): the nagini
#   cheapest-honest install control drops the (vacuous under its precond) guard.
#   Here the maximally-different correct impl is a branch-free direct return of
#   the grounded model `registerDisplay lookup key gen`; it doubles as the
#   no-ungrounded-echo control (the model is transparent over the inputs, so no
#   wrong impl echoes it and verifies).
# PORTED (pos-preserve-reorder -> pos-control-explicit-split): the nagini positive
#   makes the guard explicit (preserve-when-present, install-when-absent). Here it
#   becomes the explicit `isSome` split (preserve-when-bound first, install in the
#   else) — a structurally-different correct impl whose reproof bridges
#   `isSome`/`isNone`.
# RE-AIMED + MERGED (admiss-install-fresh + admiss-preserve-override-present ->
#   admiss-nondegenerate): both nagini admissibility cases establish that an
#   F2P-shaped input meets a function's `Requires`. This method has NO `require`
#   and no permission surface, so that probe is degenerate; the two collapse into
#   ONE case that instead pins post-image NON-DEGENERACY across BOTH branches
#   (install-at-free-name-only, preserve-existing-at-bound-name) via an in-region
#   assert on the frozen impl.
# PORTED (the five uniqueness rivals): each carries its nagini refinement
#   argument onto the corresponding branch of the one function-equality clause,
#   now backed by a machine-checked POINTWISE witness. U1 preserve-overwrite (the
#   exact regression) → bound branch; U2 install-noop → free branch (install
#   outcome); U3 install-wrong-identity → free branch (installed value); U4/U5
#   clobber-other → the frame on the free / bound branch respectively (the
#   value-level analogue of the nagini frame-mutation class, which the nagini
#   DEFENDED SURFACE itself flags as the reachable analogue since `cls` is
#   full-permission with no read-only input).
#
# FRAME/PERMISSION-MUTATION: the permission-subversion class proper is VACUOUS —
#   Velvet is referentially transparent, `lookup` is an immutable value, there is
#   no `mut` escaping the `do` block, no heap, no aliasing, no permission system.
#   The nagini sibling's own prose records that it too has no read-only input to
#   subvert and that the reachable analogue is a VALUE-level clobber of an
#   unrelated attribute — which IS carried here (rival-clobber-other-{install,
#   preserve}). No permission substitute is fabricated.
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
# AXIOM lane: dropped. AXIOM_TESTS = []. mapping.md §3 records the changed op is
#   modeled DEEPLY (the `registerDisplay` set-if-absent update) with no consumed
#   axiom, so G-AX is vacuous; the nagini AXIOM_TESTS is likewise empty. This gate
#   ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole `ensures` clause
#   `out = registerDisplay lookup key gen` folds TWO independent outcomes, both
#   attacked: the FREE branch (install-noop drops it, install-wrong-identity
#   mis-installs, clobber-other-install corrupts its frame) and the BOUND branch
#   (preserve-overwrite displaces the binding, clobber-other-preserve corrupts its
#   frame). All THREE input binders are varied by the reject witnesses:
#     * rival-preserve-overwrite       lookup=("k"↦3)  key="k" gen=5  probe "k"
#     * rival-install-noop             lookup=none     key="a" gen=7  probe "a"
#     * rival-install-wrong-identity   lookup=none     key="d" gen=9  probe "d"
#     * rival-install-wrong-name       lookup=none     key="c" gen=8  probe "c"
#     * rival-clobber-other-install    lookup=none     key="k" gen=2  probe "z"
#     * rival-clobber-other-preserve   lookup=("m"↦4)  key="m" gen=6  probe "z"
#     * rival-frame-erase-others       lookup=("p"↦3)  key="e" gen=1  probe "p"
#   So `lookup` ranges over both branch-selecting shapes (bound: overwrite,
#   clobber-preserve; free: the other five), `key` over {k,a,d,c,k,m,e}, `gen` over
#   {5,7,9,8,2,6,1}, and the probe point over {key itself, an unrelated FREE name,
#   an unrelated BOUND name} — pts=7, no binder pinned at one value across the
#   reject set. On the free branch all THREE roles of the write are separately
#   pinned: that it happens at all (install-noop), WHERE it lands
#   (install-wrong-name), and WHAT it binds (install-wrong-identity). The FRAME is
#   pinned in both directions: nothing added at another name (clobber-other-*,
#   probing a name that is `none` in `lookup`) and nothing erased at another name
#   (frame-erase-others, the only witness probing a name that is BOUND in `lookup`
#   and distinct from `key`). Both positives and the admissibility case defend
#   both branches of the clause.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (the post-image is a
#   FUNCTION equality over `String → Option Nat`, not decidable). Every witness
#   instead extracts the loop-free program and refutes the equality POINTWISE
#   (`registerAccessorExec … <probe> ≠ registerDisplay … <probe>`): each rival's
#   `…Exec` reduces under `decide` at the concrete input, and gold's does too
#   (gold agrees with `registerDisplay` at every point, so the `≠` is FALSE and
#   the witness fails on gold). No witness binds a hypothesis, so no consistency
#   probe is needed. All seven checked with scripts/lean_verify.sh: rival exit 0,
#   gold build fails (`decide` proves the proposition is false) — and that gold
#   failure is a SEMANTIC refutation in every case ("Tactic `decide` proved that
#   the proposition … is false"), never an unknown name or an unfolding gap.
AXIOM_TESTS = []
