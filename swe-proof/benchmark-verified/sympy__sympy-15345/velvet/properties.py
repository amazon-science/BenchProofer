"""properties.py — G-PBT falsification battery for sympy__sympy-15345 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct renderNode`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over three read-only inputs).

  renderNode (head : List Char) (args : List Char) (kind : NodeKind)
      ensures out = render head args kind                             -- master
      ensures kind = .functionApp → out = head ++ ['['] ++ args ++ [']']  -- C2
      ensures kind = .extremum    → out = head ++ ['['] ++ args ++ [']']  -- C3
      ensures kind = .plainExpr   → out = head ++ ['('] ++ args ++ [')']  -- C4

One expression node is rendered into target-language source text. ``head`` is
the node's head name and ``args`` is its already-rendered, comma-joined argument
text; both are INPUTS, computed elsewhere and unchanged here. The only decision
under specification is which delimiter pair surrounds ``args``: a named-function
application and the maximum/minimum operators both take the square-bracket form
``head[args]``; every other node takes the round-parenthesis fallback
``head(args)``. ``render`` is a total, fully unfolded function of the method's
own three arguments (a concrete ``def`` in the ``pure`` region; the ``axioms``
region declares NO ``axiom`` — there is no opaque answer key to echo). All three
inputs are FREE (no ``require`` clause, no ``mut`` binder), which is what makes
the per-kind rivals below refutable at a concrete point.

CARRIER NARROWING vs the nagini sibling. The nagini battery contracts the WHOLE
renderer: a fold that comma-joins the operand list AND surrounds it with a
delimiter pair. This bundle models only the purely functional CORE the fix
touches — the delimiter-pair dispatch on the node's kind — and treats the head
name and the comma-joined argument text as fixed INPUTS (mapping.md: the
comma-join is an unchanged helper whose output is consumed as ``args``, owed no
contract; the arguments render identically before and after the change).

That narrowing does NOT, however, make the four nagini JOIN rivals (a trailing
separator, a comma-only separator, dropping the first operand, reversing the
operand order) inexpressible, and an earlier revision of this manifest was wrong
to drop them as such. The join being unmodeled removes the ability to build a
WRONG JOIN; it does not remove the ability to CORRUPT the joined text on its way
into the output, and the master clause pins ``out`` to embed ``args`` verbatim,
so every one of those four corruptions is refutable here. All four are now
carried as rivals (``weak-trailing-sep``, ``weak-comma-only``,
``weak-drop-first-arg``, ``weak-reverse-args``), each refuted at an ``args``
literal that carries the ", " structure the corruption reacts to
(``['a', ',', ' ', 'b']``). They also buy coverage the per-kind rivals cannot:
``weak-reverse-args`` agrees with the frozen impl at every PALINDROMIC argument
text — including all five single-character points the original witnesses use — and
``weak-drop-first-arg`` agrees at every comma-free one, so neither is refutable
without a structured, multi-field ``args`` value. That is what makes the ``args``
binder's variation MEANINGFUL here rather than two spellings of one point: the
spec's verdict on these two rivals genuinely changes between a one-character
argument text and a two-field one.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    a by-value/by-reference input may carry a fractional heap permission an impl
    can overwrite. This backend is referentially transparent, there is no heap
    and no aliasing, and this bundle declares no ``mut`` binder — so there is no
    read-only input to overwrite and no substitute probe to fabricate. Reported
    as an omission, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``render`` is a total, fully
    unfolded function of the method's own arguments (a ``def`` in the ``pure``
    region, empty ``axioms`` region), so there is no opaque answer key an impl
    could echo without doing the work. The positive controls are honest
    cheapest-reshape controls instead.
  * PARTIAL-DOMAIN / VALUE — the heart of this surface. Each rival is right on
    part of the kind domain (or the structural shape of the rendering) and
    diverges on a sub-domain: the extremum arm surrounded with round parens (the
    pre-fix behaviour), the function-application arm with round parens, the
    fallback arm with square brackets, or the head/args substring dropped. The
    sharpest members are the two argument-text rivals whose sub-domain is a
    property of the ARGUMENT VALUE rather than of the kind: ``weak-reverse-args``
    is correct at every palindromic argument text and ``weak-drop-first-arg`` at
    every comma-free one, so each is invisible to a single-character probe and
    refutable only at a structured multi-field point.
  * DIVERGENCE: INAPPLICABLE to this impl, and CLOSED BY THE SEMANTICS against
    any rival that manufactures it. The nagini sibling carries a
    ``weak-nonterminating`` rival (a spinning loop that satisfies every value
    ensures vacuously, rejected there by the ``MustTerminate`` obligation). An
    earlier revision of this bullet said this bundle runs under
    ``set_option loom.semantics.termination "partial"`` and that a
    non-terminating impl therefore satisfies every ``ensures`` VACUOUSLY and
    verifies. That is false and is retracted: the bundle sets that option to
    ``"total"``, and in Loom the option is itself what opens
    ``TotalCorrectness`` scope. Under total correctness a postcondition is
    claimed of ALL runs, not only terminating ones, and every ``while`` owes a
    measure that STRICTLY DECREASES, so a diverging rival is REJECTED rather
    than admitted. Two further reasons no case ships. First, this impl is
    LOOP-FREE, so there is no control flow here to make diverge; a rival would
    have to bring a loop of its own. Second — and this is the reason the class
    cannot be SHIPPED even though the semantics reject it — a velvet reject case
    needs a witness that ELABORATES against the rival, and no witness can be
    proven against a diverging rival here. An earlier revision of this bullet
    said the reason was that such a rival's module "does not compile at all, the
    descent obligation failing upstream of any appended tester". That is FALSE
    and is retracted: the witness file has the ``prove_correct`` block stripped
    (``pbt_witness.witness_file``), which is precisely where the descent
    obligation lives, so the ``method`` elaborates FINE in the witness file and
    the tester directives succeed. Measured: a witness file built over a
    ``while spin > 0 ... decreasing spin`` rival produces exactly ONE error, and
    it is at the witness's own ``decide`` — ``Tactic `decide` failed ... its
    `Decidable` instance ... did not reduce to `isTrue` or `isFalse`. After
    unfolding ... reduction got stuck at the `Decidable` instance``. That is the
    gate's own ``_STUCK_REDUCTION`` shape: the extracted program's loop term
    does not reduce, so the tester decides NOTHING against a diverging rival and
    the case would land ``witness-unproven`` (a gate FAILURE, not a pass).
    ``witness_reference`` does not help — it substitutes the GOLD-side subject,
    while the half that fails here is the RIVAL side. And the refutation is not
    a value refutation in the first place: the diverging rival is rejected by
    the descent obligation, which no tester claim expresses. So the class is
    genuinely unshippable on this carrier for a WITNESS-SHAPE reason, not
    because the rival compiles or verifies — the rival IS rejected, measured
    twice: carrying ``decreasing spin`` it fails on the measure's own goal
    (``case «decreasing_1: spin» ... ⊢ spin < spin``) and omitting the clause is
    refused even earlier by the elaborator (``Decreasing annotations are
    required in total correctness semantics``). Recorded as documentation
    defended by the semantics, not as a shipped case and not as a spec hole.

WITNESS MECHANICS. The frozen impl and every rival are LOOP-FREE (a ``match`` on
``kind``), and the postcondition mentions only the TRANSPARENT ``render`` (no
opaque term), so the tester+``decide`` path is live: a witness reaches the
method's post-image through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``) and ``renderNodeTester head
args kind = false`` decides against the rival's extracted program. Every argument
is a concrete literal (a small ``String.toList`` and a ``NodeKind`` constructor)
so ``decide`` reduces fully. Against the FROZEN solution the SAME witness FAILS
(``decide`` proves the tester is NOT ``false`` — gold meets the post-image at that
point), which is exactly the required discrimination. No witness binds a
hypothesis (every input is a concrete literal), so no consistency probe is
needed. All checked out-of-band with scripts/lean_verify.sh: each rival witness
elaborates (exit 0), each gold witness fails (exit 1) with ``Tactic `decide`
proved that the proposition ... is false`` — i.e. gold's failure is a SEMANTIC
verdict on the concrete claim, not a stuck reduction, an unknown identifier or a
timeout. The carrier is fully kernel-reducible here (no loop, no ``Rat``, no
opaque term), confirmed independently: the POSITIVE form of the same claim,
``renderNodeTester "M".toList "x".toList NodeKind.extremum = true``, elaborates
against the frozen solution (exit 0), so the gold-side exit codes carry
information rather than reflecting a ``decide`` that never evaluated anything.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and the gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` (the dispatch is
modeled deeply as ``render``; meta.json axioms == []), so there is nothing here
for this spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15345"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). The
# ---- `render` def in the `pure` region uses `| .case =>` syntax with no
# ---- `let result :=` / `return result` framing, so this block is unique. ----
_IMPL_GOLD = (
    "    let result : List Char :=\n"
    "      match kind with\n"
    "      | .functionApp => head ++ ['['] ++ args ++ [']']\n"
    "      | .extremum    => head ++ ['['] ++ args ++ [']']\n"
    "      | .plainExpr   => head ++ ['('] ++ args ++ [')']\n"
    "    return result"
)
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor drift: renderNode body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so a
# ---- positive control that reshapes the impl or an admissibility case that adds
# ---- an in-region assert may retune it without touching the spec or dropping
# ---- the `prove_correct renderNode` header). Unique in the file. ----
_PROOF_GOLD = (
    "prove_correct renderNode by\n"
    "  loom_solve\n"
    "  cases kind <;> simp_all [render]"
)
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `renderNodeTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script can
# ---- mask the verdict. Every argument is a concrete literal so `decide` reduces
# ---- fully (List Char and NodeKind both derive DecidableEq). ----
_TESTER = (
    "extract_program_for renderNode\n"
    "prove_precondition_decidable_for renderNode\n"
    "prove_postcondition_decidable_for renderNode\n"
    "derive_tester_for renderNode\n\n"
)


def _witness(head, args, kind):
    return _TESTER + (
        f"example : renderNodeTester {head} {args} {kind} = false := by\n"
        "  decide\n"
    )


def _rival(fa, ex, pl):
    """A rival impl body varying the three match arms; the surrounding
    `let result := match kind with ... return result` frame is the frozen frame,
    so the edit lies wholly inside the one impl region."""
    return _swap(
        _BASE, _IMPL_GOLD,
        "    let result : List Char :=\n"
        "      match kind with\n"
        f"      | .functionApp => {fa}\n"
        f"      | .extremum    => {ex}\n"
        f"      | .plainExpr   => {pl}\n"
        "    return result")


_BR = "head ++ ['['] ++ args ++ [']']"   # square-bracket form  head[args]
_PA = "head ++ ['('] ++ args ++ [')']"   # round-paren fallback head(args)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the rendering DIRECTLY via the transparent `render`
        # def, no per-kind match in the impl region. The master clause is
        # literally `out = render head args kind`, so this is the cheapest HONEST
        # correct impl — and, since `render` is GROUNDED in the arguments (not an
        # opaque answer key), it doubles as proof the spec is not echo-vulnerable
        # (any WRONG delimiter choice fails `out = render head args kind`). The
        # impl-region match is gone, so the frozen proof's post-`loom_solve`
        # `cases kind` is applied to the residual goals via `<;>` instead.
        "module": _swap(
            _swap(_BASE, _IMPL_GOLD, "    return (render head args kind)"),
            _PROOF_GOLD,
            "prove_correct renderNode by\n"
            "  loom_solve <;> cases kind <;> simp_all [render]"),
        "rationale": (
            "the post-image `render head args kind` is GROUNDED in the inputs (a "
            "total dispatch over the finite NodeKind, no opaque answer key), so "
            "`return render head args kind` is the honest cheapest CORRECT impl; "
            "the master clause is literally `out = render head args kind`, so it "
            "MUST verify, else the master clause is SPEC-TOO-STRONG. Re-expresses "
            "the nagini pos-cheapest honest-oracle control: the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-grouped-wildcard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the two square-bracket arms (functionApp, extremum) are
        # collapsed into one grouped `_` wildcard and the round-paren fallback is
        # tested first. Same value on every kind; the frozen proof (`cases kind
        # <;> simp_all [render]`) closes unchanged.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let result : List Char :=\n"
            "      match kind with\n"
            "      | .plainExpr   => head ++ ['('] ++ args ++ [')']\n"
            "      | _            => head ++ ['['] ++ args ++ [']']\n"
            "    return result"),
        "rationale": (
            "collapsing the two square-bracket arms into one grouped wildcard "
            "(testing the round-paren fallback first) surrounds every kind with "
            "the SAME delimiter pair as the frozen dispatch, so `out = render head "
            "args kind` and all three discriminating clauses still hold and the "
            "frozen proof closes as-is; a correct reshape must verify, else "
            "SPEC-TOO-STRONG on arm grouping. Ports the nagini pos-branch-reorder "
            "(a structurally different but value-identical impl)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so the usual "a normal
    # input satisfies the precondition" probe is vacuous: nothing could exclude
    # an F2P-shaped input. The residual admissibility risk on a total domain is
    # that the post-image is UNSATISFIABLE / DEGENERATE at the interesting point
    # — a spec no impl can meet reads exactly like a spec every impl meets. This
    # case discharges an in-region `assert`, at a concrete F2P-shaped point, that
    # the extremum node is rendered with square brackets AND that this DIFFERS
    # from the round-paren fallback (so the fix is non-degenerate: the two
    # delimiter forms are genuinely distinct). The impl is kept verbatim so the
    # method's own obligation still discharges; the proof body is retuned only to
    # clear the extra assert goal by `decide` (allowed — the tactic body is
    # elided). The assert is live: a false claim leaves an unsolved goal.
    # RE-AIMED from nagini admiss-ge1-operand, whose read-only precondition half
    # has no counterpart on this referentially-transparent, require-free carrier.
    # =====================================================================
    {
        "id": "admiss-render-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "    assert (with_name_prefix `admiss\n"
                "      (render \"M\".toList \"x\".toList NodeKind.extremum\n"
                "         = \"M\".toList ++ ['['] ++ \"x\".toList ++ [']']\n"
                "       ∧ render \"M\".toList \"x\".toList NodeKind.extremum\n"
                "         ≠ render \"M\".toList \"x\".toList NodeKind.plainExpr))\n"
                + _IMPL_GOLD),
            _PROOF_GOLD,
            "prove_correct renderNode by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (cases kind <;> simp_all [render])"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "point: an extremum node renders to the square-bracket form and that "
            "form is DISTINCT from the round-paren fallback (the two delimiter "
            "pairs are genuinely different), which is exactly the behaviour the "
            "failing test demands. The in-region assert must discharge (else the "
            "obligation is unsatisfiable/degenerate at the interesting point); the "
            "impl is kept verbatim so `out = render head args kind` discharges "
            "too. Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the argument that its faithful real counterpart would
    # NOT resolve the failing test (test_Function asserts
    # mcode(Max(x,y,z)*Min(y,z)) == "Max[x, y, z]*Min[y, z]": the issue demands
    # the extremum operators print with SQUARE brackets, not round parens).
    # =====================================================================
    {
        "id": "weak-extremum-parens",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-fix behaviour: the extremum arm is surrounded with ROUND
        # parens instead of square brackets. This is the single behavioural
        # change the F2P observes.
        "module": _rival(_BR, _PA, _PA),
        "refinement": (
            "this is the pre-fix behaviour: the maximum/minimum operators are "
            "surrounded with round parens, so the extremum node prints "
            "'Max(x, y, z)' instead of 'Max[x, y, z]'. The failing test asserts "
            "the extremum operators print with SQUARE brackets (valid "
            "target-language call syntax) and the issue demands exactly that; a "
            "faithful counterpart that keeps the extremum arm on round parens "
            "reproduces the pre-fix behaviour, so the test still fails. It does "
            "NOT resolve — this is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` and from "
            "C3 (kind = .extremum → out = head ++ ['['] ++ args ++ [']']): "
            "`render` pins the extremum arm to the square-bracket form, so a rival "
            "emitting round parens diverges from the post-image at every extremum "
            "node. Refuted at (\"M\", \"x\", .extremum) — C3's exact antecedent. "
            "If it verified => SPEC-TOO-WEAK (admits the bug). Ports nagini "
            "weak-round-parens."
        ),
        "witness": _witness('"M".toList', '"x".toList', "NodeKind.extremum"),
    },
    {
        "id": "weak-funcapp-parens",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on a distinct arm: the function-application arm is surrounded
        # with round parens instead of square brackets, leaving the extremum arm
        # correct. Attacks C2 (and the master clause) on the functionApp binder.
        "module": _rival(_PA, _BR, _PA),
        "refinement": (
            "surrounds a named-function application with round parens, so a call "
            "node prints 'f(x, y, z)' instead of 'f[x, y, z]'. A faithful "
            "counterpart of this shape emits invalid call syntax for every "
            "function application, and the failing test pins the "
            "square-bracket call form (the '%s[%s]' template), so it does NOT "
            "resolve. A genuine partial-domain break — correct on the extremum "
            "arm, wrong on the function-application arm."
        ),
        "rationale": (
            "REJECT from the master clause and from C2 (kind = .functionApp → out "
            "= head ++ ['['] ++ args ++ [']']): `render` pins the "
            "function-application arm to the square-bracket form, so a rival "
            "emitting round parens diverges there. Refuted at (\"f\", \"y\", "
            ".functionApp) — a DISTINCT input point and a distinct kind arm from "
            "weak-extremum-parens, moving all three binders. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness('"f".toList', '"y".toList', "NodeKind.functionApp"),
    },
    {
        "id": "weak-plain-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        # Complementary near-miss: the generic fallback arm is surrounded with
        # SQUARE brackets instead of round parens, leaving the two call arms
        # correct. Attacks C4 (and the master clause) — ensures the fallback form
        # is pinned to round parens, not merely "some delimiter pair".
        "module": _rival(_BR, _BR, _BR),
        "refinement": (
            "surrounds the generic fallback node with square brackets, so a node "
            "with no dedicated rendering prints 'g[z]' instead of the generic "
            "'g(z)'. A faithful counterpart that routes un-dispatched nodes to the "
            "bracketed call form mis-renders every non-call expression as though "
            "it were a call, diverging from the inherited generic parenthesised "
            "form the pass-to-pass tests rely on, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause and from C4 (kind = .plainExpr → out = "
            "head ++ ['('] ++ args ++ [')']): `render` pins the fallback arm to "
            "the round-paren form, so a rival emitting square brackets diverges "
            "there. Refuted at (\"g\", \"z\", .plainExpr) — the third kind arm, so "
            "every arm of `render` is attacked by some rival. If it verified => "
            "SPEC-TOO-WEAK (the fallback delimiter is unpinned)."
        ),
        "witness": _witness('"g".toList', '"z".toList', "NodeKind.plainExpr"),
    },
    {
        "id": "weak-drop-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Structural rival: drop the head name from every arm, so the rendering
        # loses its leading head substring ('[x]' instead of 'f[x]'). Attacks the
        # master clause on the `head` binder specifically — the three per-kind
        # rivals all render `head` correctly, so this is the only rival built to
        # abuse that input.
        "module": _rival("['['] ++ args ++ [']']",
                         "['['] ++ args ++ [']']",
                         "['('] ++ args ++ [')']"),
        "refinement": (
            "drops the node's head name from the rendering, so a call node prints "
            "'[x, y, z]' instead of 'Max[x, y, z]'. A faithful counterpart that "
            "omits the head name loses the operator/function name entirely, and "
            "the failing test pins the full 'Head[args]' form (head name then "
            "bracketed args), so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` (and from "
            "every arm clause, whose right-hand side leads with `head ++`): a "
            "rival that drops the head substring diverges from the post-image "
            "whenever `head` is non-empty. Refuted at (\"H\", \"q\", "
            ".functionApp) — the only rival that moves the `head` binder off a "
            "faithfully-rendered value, so the `head` input is attacked. If it "
            "verified => SPEC-TOO-WEAK (head substring unpinned)."
        ),
        "witness": _witness('"H".toList', '"q".toList', "NodeKind.functionApp"),
    },
    {
        "id": "weak-drop-args",
        "kind": "uniqueness",
        "expect": "reject",
        # Structural rival: drop the argument text from every arm, so the
        # rendering keeps the head and empty delimiters ('K[]' instead of 'K[w]').
        # Attacks the master clause on the `args` binder specifically.
        "module": _rival("head ++ ['['] ++ [']']",
                         "head ++ ['['] ++ [']']",
                         "head ++ ['('] ++ [')']"),
        "refinement": (
            "drops the comma-joined argument text from the rendering, so a call "
            "node prints 'Max[]' instead of 'Max[x, y, z]'. A faithful "
            "counterpart that omits the arguments emits an empty argument list for "
            "every node, and the failing test pins the arguments inside the "
            "brackets, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` (and from "
            "every arm clause, whose right-hand side contains `++ args ++`): a "
            "rival that drops the args substring diverges from the post-image "
            "whenever `args` is non-empty. Refuted at (\"K\", \"w\", .extremum) — "
            "the only rival that moves the `args` binder off a faithfully-rendered "
            "value, so the `args` input is attacked. If it verified => "
            "SPEC-TOO-WEAK (args substring unpinned)."
        ),
        "witness": _witness('"K".toList', '"w".toList', "NodeKind.extremum"),
    },

    # =====================================================================
    # ARGUMENT-TEXT CORRUPTION rivals. These are the four nagini join rivals,
    # RE-AIMED onto this carrier rather than dropped. An earlier revision of this
    # manifest recorded them as inexpressible here on the grounds that `args` is
    # an INPUT and the comma-join is not modeled, so there was "no modeled join
    # behaviour to corrupt". That reasoning is wrong, and was measured wrong: the
    # master clause pins `out` to contain `args` VERBATIM, so an impl is free to
    # corrupt the argument text on its way INTO the output (append a separator,
    # strip the spaces, drop the leading field, reverse it) without the join
    # itself being modeled. Each of the four is refutable at a concrete point
    # whose `args` literal carries the ", " structure the corruption reacts to,
    # and each gold-side witness fails by `decide` DECIDING the tester is not
    # `false` — a semantic refutation, not a stuck reduction. Every arm is
    # corrupted identically, so these attack the master clause and all three
    # per-kind clauses on the `args` binder at a STRUCTURED (multi-field) value,
    # which the single-field `weak-drop-args` point cannot reach.
    # =====================================================================
    {
        "id": "weak-trailing-sep",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit a trailing ", " after the handed-in argument text, INSIDE the
        # delimiters: 'Max[x, y, z, ]'.
        "module": _rival("head ++ ['['] ++ args ++ [',', ' '] ++ [']']",
                         "head ++ ['['] ++ args ++ [',', ' '] ++ [']']",
                         "head ++ ['('] ++ args ++ [',', ' '] ++ [')']"),
        "refinement": (
            "appends a trailing separator after the last argument, so a call node "
            "prints 'Max[x, y, z, ]' instead of 'Max[x, y, z]'. The failing test "
            "pins the exact rendered string with NO trailing separator before the "
            "closing bracket, so a faithful counterpart of this shape does NOT "
            "resolve. Ports the nagini weak-trailing-sep onto this carrier: the "
            "corruption is applied to the argument text on its way into the "
            "output, which needs no modeled join."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` (and from "
            "every arm clause, whose right-hand side is `... ++ args ++ [close]` "
            "with nothing between `args` and the closing delimiter): the extra two "
            "characters make `out` longer than the post-image at every input. "
            "Refuted at (\"T\", ['a', ',', ' ', 'b'], .extremum) — a STRUCTURED args "
            "value "
            "(two comma-separated fields), a point no other rival's witness "
            "reaches. If it verified => SPEC-TOO-WEAK (args not pinned verbatim "
            "against a trailing separator)."
        ),
        "witness": _witness('"T".toList', "['a', ',', ' ', 'b']", "NodeKind.extremum"),
    },
    {
        "id": "weak-comma-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Strip the spaces out of the handed-in argument text, turning the ", "
        # separator into a bare comma: 'Max[x,y,z]'.
        "module": _rival(
            "head ++ ['['] ++ args.filter (fun c => c != ' ') ++ [']']",
            "head ++ ['['] ++ args.filter (fun c => c != ' ') ++ [']']",
            "head ++ ['('] ++ args.filter (fun c => c != ' ') ++ [')']"),
        "refinement": (
            "strips the spaces out of the argument text, so a call node prints "
            "'Max[x,y,z]' instead of 'Max[x, y, z]'. The failing test pins the "
            "', '-separated form (the spaced join), so a faithful counterpart that "
            "squeezes the separator does NOT resolve. Ports the nagini "
            "weak-comma-only: the rival corrupts the handed-in text rather than "
            "the join that produced it."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` (and every "
            "arm clause): `render` embeds `args` VERBATIM, so an impl that deletes "
            "characters from it diverges whenever `args` contains a space. Refuted "
            "at (\"N\", ['a', ',', ' ', 'b'], .extremum) — a structured args value; the "
            "single-field points used by the other rivals contain no space and "
            "would NOT refute this, which is exactly why this case needs its own "
            "point. If it verified => SPEC-TOO-WEAK (args content unpinned)."
        ),
        "witness": _witness('"N".toList', "['a', ',', ' ', 'b']", "NodeKind.extremum"),
    },
    {
        "id": "weak-drop-first-arg",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the leading comma-delimited field of the argument text: 'Max[y, z]'
        # for args 'x, y, z'. Genuinely PARTIAL-DOMAIN, and guarded to make it so:
        # the truncation fires ONLY when a comma is actually present, so a
        # single-argument text is rendered faithfully. (The unguarded
        # `args.dropWhile (· != ',') |>.drop 2` form is NOT partial-domain —
        # dropWhile consumes a comma-free text entirely, leaving '', so it is wrong
        # on the single-argument sub-domain too. Measured both ways: with the guard,
        # a witness at args="q" FAILS against this rival, i.e. the rival agrees with
        # the frozen impl there, which is what makes the sub-domain claim below
        # true rather than decorative.)
        "module": _rival(
            "head ++ ['['] ++ (if args.any (fun c => c == ',') then "
            "(args.dropWhile (fun c => c != ',')).drop 2 else args) ++ [']']",
            "head ++ ['['] ++ (if args.any (fun c => c == ',') then "
            "(args.dropWhile (fun c => c != ',')).drop 2 else args) ++ [']']",
            "head ++ ['('] ++ (if args.any (fun c => c == ',') then "
            "(args.dropWhile (fun c => c != ',')).drop 2 else args) ++ [')']"),
        "refinement": (
            "drops the first argument from the rendered text, so a call node "
            "prints 'Max[y, z]' instead of 'Max[x, y, z]'. The failing test pins "
            "every argument, in order, so a faithful counterpart that loses the "
            "leading one does NOT resolve. Ports the nagini weak-drop-first."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` (and every "
            "arm clause): `args` is embedded verbatim, so an impl that truncates "
            "its leading field diverges. A genuine PARTIAL-DOMAIN rival — a "
            "single-argument text (no comma) is rendered FAITHFULLY, so the rival "
            "is correct on that sub-domain and wrong from two arguments on, which "
            "is the near-miss shape the other rivals do not have; a refutation "
            "therefore REQUIRES a multi-field point. Refuted at "
            "(\"P\", ['a', ',', ' ', 'b'], .functionApp). If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness('"P".toList', "['a', ',', ' ', 'b']", "NodeKind.functionApp"),
    },
    {
        "id": "weak-reverse-args",
        "kind": "uniqueness",
        "expect": "reject",
        # Reverse the argument text. Partial-domain in the sharpest way: a
        # palindromic (in particular a single-character) argument text is rendered
        # faithfully, so this rival AGREES with gold at the points every other
        # rival's witness uses.
        "module": _rival("head ++ ['['] ++ args.reverse ++ [']']",
                         "head ++ ['['] ++ args.reverse ++ [']']",
                         "head ++ ['('] ++ args.reverse ++ [')']"),
        "refinement": (
            "reverses the rendered argument text, so a call node prints "
            "'Max[z ,y ,x]' instead of 'Max[x, y, z]'. The argument order is fixed "
            "upstream and identical on both sides of the change, and the failing "
            "test pins that order, so a faithful counterpart that reverses it does "
            "NOT resolve. Ports the nagini weak-reverse."
        ),
        "rationale": (
            "REJECT from the master clause `out = render head args kind` (and every "
            "arm clause): `render` embeds `args` in its given order. The sharpest "
            "partial-domain rival in the battery — it is CORRECT at every "
            "palindromic argument text, including all FIVE single-character `args` "
            "points the other witnesses use (\"x\", \"y\", \"z\", \"q\", \"w\"), and "
            "measured so: a witness at (\"R\", \"x\", .extremum) FAILS against this "
            "rival with `decide` DECIDING the tester is not `false`, i.e. the rival "
            "meets the post-image there. So it is refutable only at a structured "
            "value: (\"R\", ['a', ',', ' ', 'b'], .extremum). If it verified => "
            "SPEC-TOO-WEAK "
            "(args order unpinned)."
        ),
        "witness": _witness('"R".toList', "['a', ',', ' ', 'b']", "NodeKind.extremum"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals — one of which is a divergence
# rival) over the WHOLE renderer `print_lattice_call(name, operands)`: a fold
# that comma-joins the operand list AND surrounds it with a delimiter pair. This
# bundle models only the purely functional CORE the fix touches —
# `renderNode(head, args, kind)`, the delimiter-pair dispatch on the node's kind
# — treating the head name and the comma-joined argument text as fixed INPUTS
# (mapping.md: the join is an unchanged helper, owed no contract). So the four
# nagini rivals that attack the JOIN have no counterpart on this carrier; what
# replaces them is per-kind coverage of the dispatch the fix changes.
#
#   nagini case            -> here
#   -----------------------------------------------------------------------
#   pos-cheapest           -> pos-direct                     RE-EXPRESSED
#   pos-branch-reorder     -> pos-grouped-wildcard           PORTED (reshaped)
#   admiss-ge1-operand     -> admiss-render-nondegenerate    RE-AIMED
#   weak-round-parens      -> weak-extremum-parens           PORTED (the bug)
#   weak-trailing-sep      -> weak-trailing-sep              PORTED (re-aimed)
#   weak-comma-only        -> weak-comma-only                PORTED (re-aimed)
#   weak-drop-first        -> weak-drop-first-arg            PORTED (re-aimed)
#   weak-reverse           -> weak-reverse-args              PORTED (re-aimed)
#   weak-nonterminating    -> (none)                         SPEC-CLOSED
#   (no sibling)           -> weak-funcapp-parens            ADDED
#   (no sibling)           -> weak-plain-brackets            ADDED
#   (no sibling)           -> weak-drop-head                 ADDED
#   (no sibling)           -> weak-drop-args                 ADDED
#   AXIOM_TESTS ([])       -> (none)                         DROPPED (G-AX lane)
#
# 12 velvet SPEC cases: 2 soundness, 1 admissibility, 9 uniqueness.
#
# RE-EXPRESSED (pos-cheapest -> pos-direct): the nagini honest cheapest control
#   returns the grounded oracle `rendered(name, operands)` directly. On this
#   carrier the oracle IS the transparent `render` and the master clause already
#   IS `out = render head args kind`, so the honest cheapest impl is simply
#   `return render head args kind` — the same argument (the grounded pin is
#   satisfiable only by the real dispatch work; no wrong echo verifies), with the
#   proof retuned to the one-liner the loop-free impl needs.
# PORTED (pos-branch-reorder -> pos-grouped-wildcard): a structurally different
#   but value-identical impl (group the two square-bracket arms under a wildcard,
#   test the fallback first); the frozen proof closes unchanged.
# RE-AIMED (admiss-ge1-operand -> admiss-render-nondegenerate): the nagini case
#   re-derives the read-only precondition (>= 1 operand). This method has no
#   `require` and no heap permission, so that probe is vacuous; re-aimed at the
#   residual total-domain risk (post-image joint satisfiability AND
#   non-degeneracy), witnessed by an in-region assert that the extremum rendering
#   is the square-bracket form and is DISTINCT from the round-paren fallback.
# PORTED (weak-round-parens -> weak-extremum-parens): THE bug. The extremum arm
#   surrounded with round parens is the exact pre-fix behaviour; its faithful
#   counterpart is the unpatched printer, which prints 'Max(x, y, z)' and fails
#   test_Function's 'Max[x, y, z]' assertion. Now backed by a machine-checked
#   witness at (\"M\", \"x\", .extremum).
# PORTED, RE-AIMED (4): weak-trailing-sep, weak-comma-only, weak-drop-first-arg,
#   weak-reverse-args. In nagini these corrupt the operand-list comma-JOIN. This
#   bundle does not model the join (`args` is a fixed INPUT — mapping.md), so they
#   are re-aimed one step downstream: each corrupts the joined argument text on
#   its way INTO the output. That is refutable here because the master clause pins
#   `out` to embed `args` VERBATIM — the corruption needs no modeled join, only a
#   modeled embedding. Each is refuted at an `args` literal carrying the ", "
#   structure the corruption reacts to (['a', ',', ' ', 'b'] — written as an
#   explicit char list, not "a, b".toList, so the coverage reporter's argument
#   splitter can read the point instead of breaking on the embedded comma), which
#   is also coverage the
#   single-character points cannot buy: weak-reverse-args in particular AGREES
#   with the frozen impl at every palindromic argument text, so it is invisible to
#   all five single-character witnesses and is the sharpest partial-domain rival
#   in the battery. An earlier revision recorded these four as inexpressible under
#   carrier narrowing; that was false — measured, each rival's witness elaborates
#   (exit 0) and each gold-side witness fails by `decide` DECIDING the tester is
#   not `false` (exit 1), a semantic refutation.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
#   impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
#   no recursion), so there is no control flow here to make diverge: a
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
#   introduces it. Why it is nonetheless NOT SHIPPED as a reject case is a
#   WITNESS-SHAPE fact, measured, and not the "the module does not compile"
#   claim an earlier revision gave (see the retraction in the module docstring):
#   the witness file strips the ``prove_correct`` block, which is exactly where
#   the descent obligation lives, so the diverging ``method`` elaborates fine
#   there and the tester directives succeed — but the extracted program's loop
#   term does not reduce, so the witness's ``decide`` gets STUCK (``did not
#   reduce to `isTrue` or `isFalse` ... reduction got stuck at the `Decidable`
#   instance``, the gate's own ``_STUCK_REDUCTION`` shape) and the case would
#   land ``witness-unproven`` — a gate FAILURE. ``witness_reference`` cannot
#   rescue it: it substitutes the GOLD-side subject, and the half that fails
#   here is the RIVAL side. Nor is the refutation a value refutation at all —
#   the rejection comes from the descent obligation, which no tester claim
#   expresses. Unshippable on this carrier, and shown so rather than asserted.
# ADDED (4): weak-funcapp-parens (function-application arm on round parens,
#   attacking C2), weak-plain-brackets (fallback arm on square brackets, attacking
#   C4 — so every arm of `render` is attacked and the fallback delimiter is
#   pinned), weak-drop-head and weak-drop-args (structural rivals attacking the
#   `head` and `args` substrings so those two binders are each abused by a rival
#   built for them). Real divergences with machine-checked witnesses, not
#   fabricated wrongness.
# FRAME-MUTATION: VACUOUS. Nagini notes both inputs are pure PSeq values (no
#   Acc(.,1/2)); on this referentially-transparent backend with no heap, no
#   aliasing and no `mut` binder it is doubly vacuous — no read-only input to
#   overwrite, no substitute probe. Not fabricated.
# DROPPED (AXIOM_TESTS): the nagini file ships none (its `rendered`/`joined`
#   oracle is plain Python, validated by axiom_check.py); the changed dispatch is
#   modeled deeply here (no `axiom`), and the G-PBT gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The master clause `out = render head args
#   kind` is attacked by every rival. C2 (functionApp → brackets) by
#   weak-funcapp-parens; C3 (extremum → brackets) by weak-extremum-parens; C4
#   (plainExpr → parens) by weak-plain-brackets — so all three kind arms and all
#   three implication clauses are attacked. The three input binders are each
#   varied AND each abused by a rival built for it: `kind` ∈ {extremum,
#   functionApp, plainExpr} (three per-kind rivals), `head` (weak-drop-head), and
#   `args` (weak-drop-head, weak-drop-args, and the four argument-text corruption
#   rivals). The nine reject witnesses sit at nine DISTINCT input points —
#   (\"M\",\"x\",.extremum), (\"f\",\"y\",.functionApp), (\"g\",\"z\",.plainExpr),
#   (\"H\",\"q\",.functionApp), (\"K\",\"w\",.extremum), and the four structured
#   points (\"T\",AB,.extremum), (\"N\",AB,.extremum), (\"P\",AB,.functionApp),
#   (\"R\",AB,.extremum) where AB = ['a', ',', ' ', 'b'] — so pts=9 and no binder
#   is held fixed across every
#   witness. The `args` binder is varied MEANINGFULLY, not merely re-spelled: the
#   four AB points carry a two-field comma-separated structure, and the
#   verdict of four rivals CHANGES between a single-character args value and a
#   structured one (weak-reverse-args is correct at every palindromic args, so the
#   distinction is load-bearing rather than cosmetic).
AXIOM_TESTS = []
