# properties.py — G-PBT falsification battery for django__django-14771 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   reloaderArgv : String → List String → Bool → List (String × XVal) → List String
#                    → List String
#   Rebuilds the argument vector used to relaunch the interpreter. The single
#   postcondition pins the result to one concatenation, fully grounded in the inputs:
#     result = ([executable] ++ warnoptions.map warnArg)
#                ++ (if isCpython then xoptions.map xoptArg else [])
#                ++ argv
#   i.e. the executable, then one warning token per warning option in order, then —
#   ONLY on the reference implementation — one interpreter-option token per option in
#   supplied order (a bare `-X<key>` for a flag-style option, `-X<key>=<value>` for a
#   valued one), then the original invocation arguments unchanged. Every helper
#   (warnArg / xoptArg) is a total transparent string fold over the input, so `decide`
#   computes the verdict at any literal input — witnesses need no conditioning.
#
# CARRIER NOTE: the nagini sibling abstracted the same decision behind fractional
# read permission over PSeq[PSeq[int]] code-point sequences, with the leading
# executable + `-W` warnings bundled into one opaque `prefix` input and a front-
# recursive `option_tokens` fold guarded on `is_reference_impl`. This backend models
# the identical decision over transparent Lean lists: `isCpython` is the reference
# guard, `xoptions.map xoptArg` is the option fold, and the `-W` warnings are made
# transparent as `warnoptions.map warnArg`. Every clause the nagini battery attacked
# has a direct counterpart here, each refutable at a concrete literal input.
#
# PORTED nagini uniqueness cases (all six re-expressed against this carrier):
#   weak-drop-cpython-guard   -> weak-drop-cpython-guard
#   weak-flip-flag-rule       -> weak-flip-flag-rule
#   weak-reverse-order        -> weak-reverse-order
#   weak-only-first-option    -> weak-only-first-option
#   weak-options-after-cmdline-> weak-options-after-cmdline
#   weak-omit-forwarding-prepatch -> weak-omit-forwarding
# ADDED (carrier exposes clauses nagini bundled opaquely). Nagini folded the leading
#   executable AND the whole `-W` warning segment into ONE opaque `prefix` input, so
#   neither was attackable there; on this carrier both are transparent modeled
#   components, and so is each branch of the rendering rule. Five rivals therefore have
#   no nagini counterpart:
#     weak-drop-warn          -- the -W segment is dropped     (P2P test_warnoptions)
#     weak-reverse-warn-order -- the -W segment is reordered    (spec-strength only:
#                                no shipped test supplies two warning options, so a
#                                single-element list is its own reverse -- see the
#                                case's own refinement, corrected by this audit)
#     weak-drop-executable    -- the leading executable head is dropped
#     weak-drop-cmdline       -- the trailing argv segment is dropped
#     weak-drop-option-value  -- the XVal.val rendering branch loses its `=<value>`
#   The last four were added by the independent AUDIT of this port: the ported six
#   attack the isCpython guard and the option segment's flag-rendering / order /
#   cardinality / placement, which leaves four postcondition components whose verdict
#   no rival's impl turned on -- the `[executable]` head, the ORDER (as opposed to the
#   presence) of the -W segment, the presence (as opposed to the placement) of the
#   trailing argv, and the VALUED branch of xoptArg. Each added rival was built and
#   observed REJECTED, and each witness was built twice: it elaborates against its
#   rival and is refuted on the frozen solution by `decide` evaluating the concrete
#   claim to FALSE (a semantic refutation, not a stuck reduction or a missing name).
#
# LANES THAT DO NOT PORT (see 'assessment' for the full accounting):
#   * FRAME / PERMISSION-MUTATION. Nagini expresses these via fractional permissions
#     (Acc(x,1/2)); this instance already had all-immutable pure-sequence inputs so
#     nagini marked the class N/A, and Lean is referentially transparent regardless —
#     VACUOUS here.
#   * DIVERGENCE / NON-TERMINATION. On lean the class is genuinely VACUOUS:
#     `implementation_reloaderArgv` is a total Lean `def`, so a diverging impl cannot
#     be written. (The nagini sibling carries no diverge-* case anyway.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them (both helpers
#     are modeled DEEPLY, so there is no consumed axiom anyway).
#
# ADMISSIBILITY, RESTORED by the independent audit of this port. The port had dropped
# the lane with the reason "`correct_reloaderArgv` quantifies over all inputs with NO
# precondition hypothesis, so there is nothing that could be PRECOND-TOO-STRONG". That
# reason is WRONG, and it is the systematically-wrong one: on a TOTAL carrier the
# analogue of PRECOND-TOO-STRONG is not a rejected precondition but the obligation
# being UNSATISFIABLE at exactly a normal, exported-behaviour-shaped input. A `∀` with
# no hypothesis can still be met vacuously at every input the exported behaviour
# actually has to serve, and nothing else in this battery evaluates the modeled
# behaviour at a concrete such input: both positives prove a universally quantified
# equation and never compute one vector. `admiss-f2p-shape` closes that by discharging
# the postcondition BY EVALUATION at the reference-interpreter input carrying one
# flag-style and one valued option alongside a real command line, as a `have`, before
# closing the frozen obligation verbatim. Measured load-bearing: the same evaluation
# holds of the frozen solution (exit 0) and FAILS against two of this battery's own
# rivals (exit 1), so it is not a tautology the shape of the spec would give for free.
from pathlib import Path

INSTANCE = "django__django-14771"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). ---------------------------------------------------------------
# The reference-guarded option-forwarding block.
_GUARD = (
    "  if isCpython then\n"
    "    for kv in xoptions do\n"
    "      args := args ++ [xoptArg kv]"
)
# The warning-forwarding loop.
_WARN = (
    "  for o in warnoptions do\n"
    "    args := args ++ [warnArg o]"
)
# The whole imperative impl body (from `Id.run do` to `return args`).
_IMPL_BODY = (
    "Id.run do\n"
    "  -- Start from the executable and append one `-W` token per warning option.\n"
    "  let mut args := [executable]\n"
    "  for o in warnoptions do\n"
    "    args := args ++ [warnArg o]\n"
    "  -- On the CPython implementation, forward every active `-X` interpreter option.\n"
    "  if isCpython then\n"
    "    for kv in xoptions do\n"
    "      args := args ++ [xoptArg kv]\n"
    "  -- On the common relaunch path the original invocation arguments are appended\n"
    "  -- unchanged.\n"
    "  args := args ++ argv\n"
    "  return args"
)
for _a in (_GUARD, _WARN, _IMPL_BODY):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The frozen proof body (tactic lines inside proof-start/proof-end).
_PROOF = (
    "  intro executable warnoptions isCpython xoptions argv\n"
    "  unfold problem_spec_reloaderArgv implementation_reloaderArgv\n"
    "  simp only [Id.run, bind, pure]\n"
    "  cases isCpython <;>\n"
    "    simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,\n"
    "      List.append_assoc, List.singleton_append, List.nil_append]"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"

# The frozen proof's `intro` line, on its own: the admissibility positive prepends a
# ground `have` AFTER the binders are introduced and leaves everything else verbatim.
_INTRO = "  intro executable warnoptions isCpython xoptions argv\n"
assert _BASE.count(_INTRO) == 1, "intro anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-direct: the cheapest HONEST impl. The postcondition RHS is grounded in the
# inputs (a total transparent concatenation of two `.map` folds), so directly
# returning that expression is a fully-grounded correct implementation, not an
# ungrounded-oracle echo (a wrong constant fails the postcondition). The proof
# collapses to `rfl` after unfolding. MUST verify; else SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _swap(
        _BASE, _IMPL_BODY,
        "\n"
        "  ([executable] ++ warnoptions.map warnArg)\n"
        "    ++ (if isCpython then xoptions.map xoptArg else [])\n"
        "    ++ argv",
    ),
    _PROOF,
    "  intro executable warnoptions isCpython xoptions argv\n"
    "  unfold problem_spec_reloaderArgv implementation_reloaderArgv\n"
    "  rfl",
)

# pos-loop-reshape: structurally DIFFERENT but behaviourally identical. Instead of
# GUARDING the option loop with `if isCpython`, iterate over the already-guarded list
# `if isCpython then xoptions else []`. Same result on every input (both fold nothing
# when not on the reference impl); only the branch FORM changes — the shape a faithful
# patch could equally take. The frozen `cases isCpython` proof still closes after
# folding the guarded list with `List.map_nil` (a genuine reproof: the theorem
# STATEMENT is byte-identical, no new axiom/lemma/sorry). If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to one loop shape).
_POS_LOOP = _swap(
    _swap(
        _BASE, _GUARD,
        "  let xs := if isCpython then xoptions else []\n"
        "  for kv in xs do\n"
        "    args := args ++ [xoptArg kv]",
    ),
    _PROOF,
    "  intro executable warnoptions isCpython xoptions argv\n"
    "  unfold problem_spec_reloaderArgv implementation_reloaderArgv\n"
    "  simp only [Id.run, bind, pure]\n"
    "  cases isCpython <;>\n"
    "    simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,\n"
    "      List.append_assoc, List.singleton_append, List.nil_append, List.map_nil]",
)


# ===========================================================================
# ADMISSIBILITY (audit-added) — the obligation must be SATISFIABLE at a normal,
# exported-behaviour-shaped input, not merely provable in the abstract.
# ===========================================================================

# The shape the changed behaviour actually has to serve: the reference interpreter,
# no active warning filters, one flag-style option AND one valued option supplied
# together, and a real two-token command line. The impl region is left FROZEN
# byte-for-byte; only the proof body gains two `have`s ahead of the verbatim frozen
# tactic script, so the case can only ADD a check.
_ADMISS_INPUT = ('"python" [] true [("utf8", XVal.flag), ("a", XVal.val "b")] '
                 '["manage.py", "runserver"]')

_POS_ADMISS = _swap(
    _BASE, _INTRO,
    _INTRO
    # (1) EVALUATE the modeled behaviour at that input down to one concrete vector.
    # This is what makes the admission non-vacuous: it pins WHICH vector the input
    # produces rather than only that some equation holds of it. Measured
    # load-bearing — it fails against a rival that omits the forwarding and against
    # one that drops the `=<value>` part.
    + f"  have _f2p_vec : implementation_reloaderArgv {_ADMISS_INPUT}\n"
      "      = [\"python\", \"-Xutf8\", \"-Xa=b\", \"manage.py\", \"runserver\"] := by\n"
      "    unfold implementation_reloaderArgv\n"
      "    decide\n"
    # (2) Discharge the postcondition itself at that same input, by evaluation.
    + f"  have _f2p : problem_spec_reloaderArgv {_ADMISS_INPUT}\n"
      f"      (implementation_reloaderArgv {_ADMISS_INPUT}) := by\n"
      "    unfold problem_spec_reloaderArgv implementation_reloaderArgv\n"
      "    decide\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# elaborates against the rival and FAILS on the frozen solution.
# ===========================================================================

# Drop the reference guard: forward the option tokens UNCONDITIONALLY.
_RIV_DROP_GUARD = _swap(_BASE, "  if isCpython then\n", "  if true then\n")

# Flip the flag/value rule: always emit `-X<key>=<value>`, rendering the flag
# sentinel as the literal "True" — the pre-change / wrong-echo form.
_RIV_FLIP = _swap(
    _BASE, "      args := args ++ [xoptArg kv]",
    "      args := args ++ [\"-X\" ++ kv.1 ++ \"=\" ++ "
    "(match kv.2 with | XVal.flag => \"True\" | XVal.val v => v)]",
)

# Reverse the supplied option order.
_RIV_REVERSE = _swap(
    _BASE, "    for kv in xoptions do", "    for kv in xoptions.reverse do")

# Forward ONLY the first option.
_RIV_FIRST = _swap(
    _BASE, "    for kv in xoptions do", "    for kv in (xoptions.take 1) do")

# Insert the option tokens AFTER the command line (append argv first).
_RIV_AFTER = _swap(
    _swap(_BASE, _GUARD, ""),
    "  args := args ++ argv\n  return args",
    "  args := args ++ argv\n"
    "  if isCpython then\n"
    "    for kv in xoptions do\n"
    "      args := args ++ [xoptArg kv]\n"
    "  return args",
)

# Omit forwarding entirely (the pre-patch behaviour).
_RIV_OMIT = _swap(_BASE, "  if isCpython then\n", "  if false then\n")

# Drop the `-W` warning segment (attacks the transparent warning clause).
_RIV_DROP_WARN = _swap(_BASE, _WARN + "\n", "")

# --- AUDIT-ADDED rivals. The battery above attacks the isCpython guard, the
# rendering rule's flag branch, and the option segment's order/cardinality/
# placement, but the postcondition has four more components whose verdict no
# rival's impl turned on: the leading `[executable]` head, the ORDER of the
# warning segment, the trailing `argv` segment, and the VALUED (XVal.val) branch
# of the rendering rule. Each is a distinct clause of the same concatenation, so
# a rival that abuses it is refutable at a literal input exactly like the others.
# ------------------------------------------------------------------------------
# Drop the leading executable head.
_RIV_DROP_EXE = _swap(_BASE, "  let mut args := [executable]\n", "  let mut args := []\n")

# Reverse the warning order (the -W segment is present but back-to-front).
_RIV_REVERSE_WARN = _swap(
    _BASE, "  for o in warnoptions do", "  for o in warnoptions.reverse do")

# Never append the original invocation arguments.
_RIV_DROP_ARGV = _swap(
    _BASE, "  args := args ++ argv\n", "  args := args ++ ([] : List String)\n")

# Render a VALUED option as a bare `-X<key>`, dropping the `=<value>` part.
_RIV_DROP_OPTVALUE = _swap(
    _BASE, "      args := args ++ [xoptArg kv]",
    "      args := args ++ [\"-X\" ++ kv.1]")


def _wit(args, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at concrete literal
    inputs, closed by `decide`. `args` is the Lean applied-argument string. Elaborates
    against a rival that diverges from the frozen verdict there, and fails on gold
    (which satisfies the spec at every input). No head binders => nothing to be
    inconsistent."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_reloaderArgv {args}\n"
        f"    (implementation_reloaderArgv {args}) := by\n"
        f"  unfold problem_spec_reloaderArgv implementation_reloaderArgv\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition RHS is GROUNDED in the inputs (a total transparent "
            "concatenation of two .map folds), so `implementation := that expression` "
            "is the honest cheapest CORRECT impl, not an ungrounded echo; the proof "
            "collapses to `rfl`. Must verify (the postcondition is literally that "
            "equation); else SPEC-TOO-STRONG. Also shows the spec is not echo-"
            "vulnerable: any WRONG value fails the postcondition."
        ),
    },
    {
        "id": "pos-loop-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOOP,
        "rationale": (
            "structurally-different but CORRECT impl: instead of guarding the option "
            "loop with `if isCpython`, it iterates over the already-guarded list "
            "`if isCpython then xoptions else []`. Identical result on every input; "
            "only the loop FORM changes. The frozen `theorem correct_reloaderArgv` "
            "statement is kept byte-identical and the proof is honestly re-closed "
            "(no new axiom/lemma/sorry). If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to one loop shape)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ADMISSIBILITY on a TOTAL carrier. The frozen obligation is `∀ executable "
            "warnoptions isCpython xoptions argv, problem_spec … (implementation …)` "
            "with no precondition hypothesis, and this port originally dropped the lane "
            "saying 'nothing could be PRECOND-TOO-STRONG'. That reason is wrong: the "
            "analogue here is the obligation being UNSATISFIABLE at a concrete input of "
            "the shape the exported behaviour must actually handle — the reference "
            "interpreter with one flag-style and one valued option supplied together "
            "and a real command line. Nothing else in this battery evaluates the "
            "modeled behaviour at a concrete input; both positives prove a quantified "
            "equation and never compute one vector. This case keeps the impl region "
            "FROZEN byte-for-byte and prepends two `have`s: the first EVALUATES the "
            "behaviour at that input to one concrete vector (so the admission is "
            "pinned to which vector, not merely to some equation holding), the second "
            "discharges the postcondition there by evaluation. Both close by `decide` "
            "past the `Id.run` residue, i.e. the do-loop really is computed at that "
            "input. The frozen obligation is then closed by the unchanged frozen "
            "tactic body, so the case adds a check and weakens nothing; the statement "
            "is byte-identical and no axiom/lemma/sorry is introduced. Measured "
            "load-bearing: the first `have` holds of the frozen solution and FAILS "
            "against the omit-forwarding and drop-option-value rivals. If it FAILS => "
            "PRECOND-TOO-STRONG (the spec cannot be met at an in-domain input)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-drop-cpython-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_GUARD,
        "refinement": (
            "the reference guard forwards the interpreter options ONLY on the "
            "reference implementation; dropping it forwards the `-X` tokens on a "
            "NON-reference interpreter, where those options were never recorded that "
            "way. The faithful patch (removing the `sys.implementation.name` gate) "
            "changes the child argv on a non-reference run and does NOT resolve — a "
            "verifying rival here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition's `if isCpython then … else []` selector, "
            "which requires the EMPTY option segment when not isCpython; forwarding "
            "unconditionally violates it. Attacks the isCpython binder / the "
            "not-reference sub-domain. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # isCpython=false with a non-empty xoptions: gold appends nothing, rival appends the token.
        "witness": _wit('"py" [] false [("a", XVal.flag)] ["s"]',
                        "not reference + option supplied: gold forwards nothing, rival forwards it"),
    },
    {
        "id": "weak-flip-flag-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLIP,
        "refinement": (
            "the flag-style option (value is the 'on' sentinel) must render as a BARE "
            "`-X<key>`; forcing the name=value form emits `-X<key>=True` instead. The "
            "faithful patch would make a flag option like utf8 emit `-Xutf8=True` "
            "rather than `-Xutf8`, so the F2P test_xoptions equality fails (would not "
            "resolve)."
        ),
        "rationale": (
            "REJECTED by the xoptArg definition consumed in the postcondition: for a "
            "flag-style option the token is `-X`++key, NOT `-X`++key++`=`++value. "
            "Attacks the xoptions binder / the flag-style (XVal.flag) sub-domain. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        # utf8 flag on the reference impl: gold -> "-Xutf8", rival -> "-Xutf8=True".
        "witness": _wit('"py3" ["e"] true [("utf8", XVal.flag)] ["m"]',
                        "flag-style option: gold emits bare -Xutf8, rival emits -Xutf8=True"),
    },
    {
        "id": "weak-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE,
        "refinement": (
            "the options must be forwarded in SUPPLIED order; reversing them yields the "
            "tokens back-to-front. The faithful patch would emit e.g. `-Xa=b -Xutf8` "
            "where the reference expects `-Xutf8 -Xa=b`, so test_xoptions' ordered "
            "equality fails (would not resolve)."
        ),
        "rationale": (
            "REJECTED by the postcondition's `xoptions.map xoptArg` (supplied order); "
            "the reversed accumulation produces a different list. Attacks the xoptions "
            "binder / the multi-option ordering sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # two options: gold -> [-Xa, -Xb=c], rival -> [-Xb=c, -Xa].
        "witness": _wit('"python" [] true [("a", XVal.flag), ("b", XVal.val "c")] ["run"]',
                        "two options: gold preserves order, rival reverses it"),
    },
    {
        "id": "weak-only-first-option",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRST,
        "refinement": (
            "every supplied option must be forwarded; taking only the first drops the "
            "rest. The faithful patch would emit only the first `-X` token, so a "
            "reference run with two options loses the second and test_xoptions fails "
            "(would not resolve)."
        ),
        "rationale": (
            "REJECTED by the postcondition's `xoptions.map xoptArg` covering ALL "
            "options; forwarding one leaves a shorter list. Attacks the xoptions "
            "binder / the multi-option cardinality sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # two flag options: gold -> [-Xa, -Xb], rival -> [-Xa].
        "witness": _wit('"exe" ["w"] true [("a", XVal.flag), ("b", XVal.flag)] ["x", "y"]',
                        "two options: gold forwards both, rival forwards only the first"),
    },
    {
        "id": "weak-options-after-cmdline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_AFTER,
        "refinement": (
            "the option tokens are inserted into the LEADING args, BEFORE the original "
            "invocation arguments; placing them after argv reorders the vector. The "
            "faithful patch would emit [exe, script, runserver, -Xz=1] where the "
            "reference expects [exe, -Xz=1, script, runserver], so test_xoptions fails "
            "(would not resolve)."
        ),
        "rationale": (
            "REJECTED by the postcondition's concatenation order: the option segment "
            "PRECEDES argv; appending it after argv violates the equation. Attacks the "
            "interaction of the xoptions and argv binders / the placement sub-domain. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # one option, non-empty argv: gold puts token before argv, rival after.
        "witness": _wit('"p" [] true [("z", XVal.val "1")] ["sc", "rs"]',
                        "option + argv: gold places option before argv, rival after"),
    },
    {
        "id": "weak-omit-forwarding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OMIT,
        "refinement": (
            "this is the PRE-PATCH behaviour: the interpreter options are never "
            "forwarded, so on the reference impl with options supplied the child argv "
            "omits every `-X` token — exactly the bug the fix repairs. The F2P "
            "test_xoptions fails (would not resolve)."
        ),
        "rationale": (
            "REJECTED by the postcondition: when isCpython the required segment is "
            "`xoptions.map xoptArg`, not the empty list. Attacks the isCpython/xoptions "
            "binders / the reference-with-options sub-domain (the mirror of "
            "weak-drop-cpython-guard). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # reference impl, options supplied: gold forwards them, rival forwards nothing.
        "witness": _wit('"bin" ["err"] true [("utf8", XVal.flag), ("a", XVal.val "b")] ["srv"]',
                        "reference + options: gold forwards them, rival (prepatch) omits them"),
    },
    {
        "id": "weak-drop-warn",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_WARN,
        "refinement": (
            "each warning option must become one `-W<opt>` token; dropping the warning "
            "segment omits them entirely. The faithful patch would relaunch without the "
            "active warning filters, so the PASS_TO_PASS test_warnoptions (which expects "
            "`-Werror` in the vector) fails (would not resolve). This clause is "
            "transparent on this carrier though nagini folded it into an opaque prefix "
            "input, so this rival has no nagini counterpart."
        ),
        "rationale": (
            "REJECTED by the postcondition's `warnoptions.map warnArg` segment; "
            "dropping it produces a vector missing the warning tokens. Attacks the "
            "warnoptions binder / the non-empty-warnings sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # one warning option: gold -> [..., -Werror, ...], rival drops it.
        "witness": _wit('"q" ["error"] false [] ["only"]',
                        "warning supplied: gold emits -Werror, rival drops the warning segment"),
    },

    # ---- AUDIT-ADDED rivals: the four postcondition components no rival above
    # ---- turned its verdict on. Each rival module was built and REJECTED, and
    # ---- each witness was built twice (holds of the rival, refuted on gold by
    # ---- `decide` evaluating the concrete claim to false).
    {
        "id": "weak-drop-executable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_EXE,
        "refinement": (
            "the relaunch vector must START with the interpreter executable; a rival "
            "that omits the head emits a vector whose first token is a `-W`/`-X` "
            "option or an invocation argument instead. Relaunching from such a vector "
            "does not re-execute the interpreter at all, so the whole TestChildArguments "
            "family (every one of which asserts the leading executable entry) fails and "
            "the rival would not resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's leading `[executable]` singleton: the "
            "required result begins with the executable, and the rival's begins with "
            "the first token of the next segment. Attacks the executable binder / the "
            "vector-head sub-domain, which no other rival's impl moves. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # gold -> ["py", "-Ww", "s"], rival -> ["-Ww", "s"].
        "witness": _wit('"py" ["w"] false [] ["s"]',
                        "gold heads the vector with the executable, rival omits it"),
    },
    {
        "id": "weak-reverse-warn-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSE_WARN,
        "refinement": (
            "the warning tokens must appear in SUPPLIED order, one per active warning "
            "option; a rival that reverses them emits the same multiset in the wrong "
            "sequence. Warning filters are applied in order and the later ones win, so "
            "reversing them changes which filter is in force after the reload — a real "
            "behavioural divergence from the modeled function, which is why the spec "
            "must and does reject it. HONEST SCOPE (corrected by the audit of this "
            "port, which found the original claim here false): no SHIPPED test "
            "discriminates this rival. Every relaunch test in the modeled family "
            "supplies either no warning option or exactly ONE, and a single-element "
            "list is its own reverse, so this rival passes the whole visible suite. "
            "It is therefore a spec-strength probe, not a would-not-resolve claim: it "
            "pins the ORDER clause of the warning segment, which the ordered equality "
            "in the postcondition asserts and no shipped test exercises. Distinct from "
            "weak-drop-warn, which removes the segment rather than reordering it: that "
            "one IS test-visible, this one keeps every token and still gets the vector "
            "wrong."
        ),
        "rationale": (
            "REJECTED by the postcondition's `warnoptions.map warnArg`, which pins the "
            "warning tokens to supplied order; the reversed accumulation produces a "
            "different list whenever two or more warnings are active. Attacks the "
            "warnoptions binder / the multi-warning ORDERING sub-domain (the warning "
            "counterpart of weak-reverse-order). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # two warnings: gold -> [-Wa, -Wb], rival -> [-Wb, -Wa].
        "witness": _wit('"py" ["a", "b"] false [] ["s"]',
                        "two warnings: gold keeps supplied order, rival reverses them"),
    },
    {
        "id": "weak-drop-cmdline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_ARGV,
        "refinement": (
            "the original invocation arguments are appended UNCHANGED at the end of the "
            "vector; a rival that never appends them relaunches the interpreter with no "
            "script and no subcommand. The reloaded child would lose the command it was "
            "serving, so every TestChildArguments case that supplies invocation "
            "arguments fails (would not resolve)."
        ),
        "rationale": (
            "REJECTED by the postcondition's trailing `++ argv`: the required result "
            "ends with the invocation arguments, and the rival's ends with the last "
            "option token. Attacks the argv binder / the non-empty-command-line "
            "sub-domain; weak-options-after-cmdline moves argv relative to the option "
            "segment but never removes it, so this is the only rival whose verdict "
            "turns on argv being PRESENT. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # gold -> [..., "sc", "rs"], rival stops after the option token.
        "witness": _wit('"py" ["w"] true [("k", XVal.flag)] ["sc", "rs"]',
                        "argv supplied: gold appends the invocation arguments, rival drops them"),
    },
    {
        "id": "weak-drop-option-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_OPTVALUE,
        "refinement": (
            "a VALUED interpreter option must render as `-X<key>=<value>`; a rival that "
            "emits the bare `-X<key>` keeps the option present but discards what it was "
            "set to, so a valued setting silently reverts to its default across the "
            "reload. The F2P test_xoptions supplies a valued option and asserts the "
            "`=<value>` form, so the rival fails it (would not resolve). This is the "
            "MIRROR of weak-flip-flag-rule: that rival forces the valued form onto a "
            "flag-style option, this one forces the flag form onto a valued option, so "
            "the two together pin both branches of the rendering rule."
        ),
        "rationale": (
            "REJECTED by the xoptArg definition consumed in the postcondition: for "
            "`XVal.val v` the token is `-X`++key++`=`++v, not the bare `-X`++key. "
            "Attacks the xoptions binder / the VALUED (XVal.val) sub-domain, the one "
            "constructor of XVal no other rival's impl discriminates at. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # valued option: gold -> "-Xtracemalloc=5", rival -> "-Xtracemalloc".
        "witness": _wit('"py" [] true [("tracemalloc", XVal.val "5")] ["sc"]',
                        "valued option: gold emits -Xtracemalloc=5, rival drops the =value part"),
    },
]


# No @ContractOnly axioms and no opaque callees: both warnArg and xoptArg are modeled
# DEEPLY over transparent Lean strings/lists, so the axiom lane is vacuous here and
# belongs to G-AX regardless.
AXIOM_TESTS = []
