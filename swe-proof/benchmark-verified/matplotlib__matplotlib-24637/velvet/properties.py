"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24637 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect="verify"`` passes iff (in scope AND verifies); ``expect="reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over two read-only inputs).

  groupedRender (gid : Option String) (children : List RenderCmd)
        return (out : List RenderCmd)
    ensures out = beginGroup gid :: (children ++ [endGroup])   [C1 master]
    ensures out.head?    = some (beginGroup gid)               [C2 opens on id]
    ensures out.getLast? = some endGroup                       [C3 closes]
    ensures out.tail     = children ++ [endGroup]              [C4 body in order]
    ensures out.length   = children.length + 2                 [C5 length]

There is ONE method, NO ``require`` clause (the admitted domain is total), and a
FULLY TRANSPARENT carrier: ``RenderCmd`` derives ``DecidableEq`` and every clause
reduces under ``decide`` at concrete inputs — there is no opaque leaf, so no
conditioning-on-the-carrier is needed and every reject witness lives at literal
inputs. The two inputs — ``gid`` and ``children`` — are FREE: the post-image must
hold for every value each takes, which is what makes the partial-domain rivals
below refutable at concrete points.

The behaviour the spec pins: the returned command stream must OPEN with a single
grouping element carrying the artist's OWN identifier ``gid``, then reproduce the
children's commands unchanged and in order, then CLOSE that grouping element — so
the identifier reaches the back end and labels the composite as one unit. A
stream that emits the children with no surrounding grouping element (so the
identifier never reaches the output), or opens a group WITHOUT the identifier, or
never closes the group, or reorders the body, violates one or more of C1–C5.

ADVERSARIAL READ of the sibling classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because an input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent, there is no heap and no
    aliasing, and this bundle declares NO ``mut`` binder among the parameters — so
    there is no read-only input to overwrite and no substitute probe to
    fabricate. The two sibling frame-mutation rivals (write the read-only ``gid``,
    write the read-only ``children``) have no counterpart here and are NOT
    replaced. See the accounting note.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own two arguments (constructor-level list surgery in
    the ``pure`` region; the ``axioms`` region is empty — no ``opaque`` leaf, no
    consumed ``axiom``). There is no answer key to echo; the positive controls are
    honest cheapest-reshape controls instead.
  * PARTIAL-DOMAIN / VALUE — APPLIES: the pre-patch behaviour (no grouping element
    at all) and the adjacent near-misses (drop the identifier, omit the close,
    reorder the body).
  * FREE-INPUT PRESERVATION — APPLIES: the post-image carries TWO free inputs (the
    identifier ``gid`` on the opening element, and the ``children`` stream carried
    through). Each is attacked on its own so its witness sits at a value the
    others do not fix.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The four reject witnesses sit at four DISTINCT input points
and between them move BOTH binders off any fixed value: ``gid`` takes both a
present identifier (``some "a"``) and none; ``children`` takes the empty stream, a
one-command stream, and a two-command stream (so the order clause C4 is probed at
a stream whose reversal actually differs). pts = 4 distinct input points.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24637"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). ----
_IMPL_GOLD = (
    "    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]\n"
    "    trace := trace ++ children\n"
    "    trace := trace ++ [RenderCmd.endGroup]\n"
    "    return trace"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: groupedRender body not verbatim"
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor not unique"

# ---- the frozen proof body (tactic script only; elided from the spec view). ----
_PROOF_GOLD = "prove_correct groupedRender by\n  loom_solve"
assert _PROOF_GOLD in _BASE, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `groupedRenderTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script can
# ---- mask the verdict. Every argument is a concrete literal so `decide` reduces
# ---- fully (the carrier is transparent — no opaque leaf to block it). ----
_TESTER = (
    "extract_program_for groupedRender\n"
    "prove_precondition_decidable_for groupedRender\n"
    "prove_postcondition_decidable_for groupedRender\n"
    "derive_tester_for groupedRender\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof
    # script (the post-image is a pointwise list identity, so no reshape here
    # needs a new lemma; loom_solve closes each).
    # =====================================================================
    {
        "id": "pos-cons-prepend",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the opening element and the body by a single `::`
        # prepend instead of appending the opening element as a one-element
        # list first. Same assembled stream, same left-to-right structure.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let mut trace : List RenderCmd := RenderCmd.beginGroup gid :: children\n"
            "    trace := trace ++ [RenderCmd.endGroup]\n"
            "    return trace"),
        "rationale": "prepending the opening command with `::` onto the children "
                     "instead of concatenating a singleton list yields the identical "
                     "stream `beginGroup gid :: (children ++ [endGroup])`, so C1–C5 "
                     "all still hold; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the assembly shape.",
    },
    {
        "id": "pos-named-body",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the opening command and the closed body in `let`s and
        # return the cons directly, with no `mut` accumulator. Same value flow.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let head := RenderCmd.beginGroup gid\n"
            "    let body := children ++ [RenderCmd.endGroup]\n"
            "    return head :: body"),
        "rationale": "naming the opening command and the closed body as local "
                     "bindings and returning `head :: body` leaves the returned "
                     "stream unchanged, so the post-image is unchanged; a correct "
                     "reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed). No method here has a `require` clause, so the
    # sibling's "a normal input satisfies the precondition" probe is vacuous:
    # nothing could exclude an F2P-shaped input. The residual admissibility risk
    # on a total domain is that the post-image is UNSATISFIABLE / DEGENERATE at
    # the interesting point — a spec no impl can meet reads like a spec every
    # impl meets. This case discharges an in-region `assert`, at fully concrete
    # inputs, that the post-image is NON-DEGENERATE: the stream for a PRESENT
    # identifier differs from the stream for none (i.e. the opening element
    # genuinely carries the identifier — the discriminating observable). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the frozen proof body (`loom_solve`) also clears the added
    # assert goal. The assert is live, not decoration: a false claim about the
    # same point leaves an unsolved goal (verified in scratch).
    # =====================================================================
    {
        "id": "admiss-identifier-observable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    assert (with_name_prefix `admiss\n"
            "      (RenderCmd.beginGroup (some \"x\") :: ([] ++ [RenderCmd.endGroup])\n"
            "        ≠ RenderCmd.beginGroup none :: ([] ++ [RenderCmd.endGroup])))\n"
            + _IMPL_GOLD),
        "rationale": "the post-image is satisfiable AND non-degenerate at a concrete "
                     "point: the stream built for a present identifier is distinct "
                     "from the one built for none, so the opening element genuinely "
                     "carries the identifier the behaviour cares about. The in-region "
                     "assert must discharge (else an unsatisfiable/degenerate "
                     "obligation); the impl is kept verbatim so the ensures clauses "
                     "discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-no-group",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BEHAVIOUR: emit the children stream with NO surrounding
        # grouping element, so the identifier never reaches the output.
        "module": _swap(_BASE, _IMPL_GOLD, "    return children"),
        "refinement": "this IS the pre-patch behaviour: the composite's body was "
                      "emitted with no enclosing grouping element, so the artist's "
                      "identifier never reached the rendered output. The failing test "
                      "asserts the identifier-bearing opening element appears in the "
                      "saved output; with no group emitted it is absent, so the "
                      "faithful patch does NOT resolve — exactly the bug the fix "
                      "addresses.",
        "rationale": "REJECT: with the group dropped the output is just `children`, "
                     "violating C1 (master), C2 (head is not `beginGroup gid`), C3 "
                     "(no trailing close), and C5 (`out.length = children.length + 2` "
                     "fails — the bare body is two commands short). Refuted at "
                     "`gid = some \"a\"`, `children = [child 0]`, where the tester "
                     "must be true of a stream opening with the identifier and is "
                     "false of the bare body.",
        "witness": _TESTER +
                   "example : groupedRenderTester (some \"a\") [RenderCmd.child 0] "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-drop-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        # Opens a WELL-FORMED grouping element and closes it, but WITHOUT the
        # identifier: the opening command carries `none` instead of `gid`. The
        # empty-id / "opened a group but forgot to pass the id" near-miss.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let mut trace : List RenderCmd := [RenderCmd.beginGroup none]\n"
            "    trace := trace ++ children\n"
            "    trace := trace ++ [RenderCmd.endGroup]\n"
            "    return trace"),
        "refinement": "a counterpart that opened a group but did not pass the "
                      "artist's identifier would emit a grouping element with no "
                      "identifier attribute (or a default label), NOT the "
                      "identifier-bearing element the failing test greps for. The "
                      "artist's identifier still would not reach the output as the "
                      "group's id, so the patch does NOT resolve.",
        "rationale": "REJECT: the opening command is `beginGroup none`, so at any "
                     "present `gid` it violates C1 (master) and C2 (`out.head?` must "
                     "be `some (beginGroup gid)`, not `beginGroup none`). Refuted at "
                     "`gid = some \"a\"`, `children = []`, the only witness that "
                     "moves the `children` binder to the empty stream — so the "
                     "identifier clause is probed independently of body content.",
        "witness": _TESTER +
                   "example : groupedRenderTester (some \"a\") [] "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-omit-close",
        "kind": "uniqueness",
        "expect": "reject",
        # Opens the group with the identifier and emits the children, but NEVER
        # emits the matching close: the grouping element is left unbalanced.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]\n"
            "    trace := trace ++ children\n"
            "    return trace"),
        "refinement": "a counterpart that opened the group but omitted the matching "
                      "close would leave an unbalanced grouping element open in the "
                      "output — malformed structure that never closes before the "
                      "document end — regressing the structural-validity tests the "
                      "suite keeps green. The identifier still appears, so a naive "
                      "'does the id show up' check would miss it; the full structural "
                      "post-image catches the missing close, so the patch does NOT "
                      "faithfully resolve while keeping the suite green.",
        "rationale": "REJECT: with the close dropped the output is "
                     "`beginGroup gid :: children`, violating C1 (master), C3 "
                     "(`out.getLast?` must be `some endGroup`), and C5 "
                     "(`out.length = children.length + 2` fails — one command short). "
                     "Note C2 (opens on the identifier) STILL holds — which is "
                     "why C3/C5, not just the head clause, are load-bearing. Refuted "
                     "at `gid = none`, `children = [child 0]`, the only witness that "
                     "moves the `gid` binder to none.",
        "witness": _TESTER +
                   "example : groupedRenderTester none [RenderCmd.child 0] "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-reorder-children",
        "kind": "uniqueness",
        "expect": "reject",
        # Brackets the body correctly (opens on the identifier, closes) but emits
        # the children in REVERSED order — the body is not carried through in
        # order. Attacks C4 (`out.tail = children ++ [endGroup]`), the one
        # independent clause no other rival touches (no-group drops the body,
        # omit-close keeps order, drop-identifier keeps order).
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let mut trace : List RenderCmd := [RenderCmd.beginGroup gid]\n"
            "    trace := trace ++ children.reverse\n"
            "    trace := trace ++ [RenderCmd.endGroup]\n"
            "    return trace"),
        "refinement": "a counterpart that reordered the composite's contained "
                      "drawings would emit the sub-artists' commands out of their "
                      "original order, changing the rendered content (e.g. z-order / "
                      "overpainting) — the patch inserts only the enclosing "
                      "open/close around the UNCHANGED body and must reproduce the "
                      "children verbatim and in order, so a reordering counterpart "
                      "would regress the content tests and does NOT faithfully "
                      "resolve.",
        "rationale": "REJECT: the body is `children.reverse`, so at any children "
                     "stream that is not a palindrome it violates C1 (master) and C4 "
                     "(`out.tail` must be `children ++ [endGroup]`). C2/C3/C5 all "
                     "still hold — this isolates the in-order clause. Refuted at "
                     "`gid = some \"a\"`, `children = [child 0, child 1]`, the only "
                     "witness that moves `children` to a length-2 stream whose "
                     "reversal differs.",
        "witness": _TESTER +
                   "example : groupedRenderTester (some \"a\") "
                   "[RenderCmd.child 0, RenderCmd.child 1] "
                   "= false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases across a SINGLE
# contracted function draw_grouped_output(gid, children) over a `List[int]`
# code-point carrier with fractional-permission read-only inputs:
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape-locals            -> pos-cons-prepend + pos-named-body PORTED
#   admissibility-two-readonly-inputs-*   -> admiss-identifier-observable    RE-AIMED
#   frame-mutation-write-gid              -> (none)                          VACUOUS
#   frame-mutation-write-children         -> (none)                          VACUOUS
#   partial-domain-no-group               -> weak-no-group                   PORTED
#   partial-domain-drop-gid-empty-id      -> weak-drop-identifier            PORTED
#   partial-domain-omit-close             -> weak-omit-close                  PORTED
#
# 4 sibling cases ported (2 partial-domain + no-group + drop-gid + omit-close;
# the single reshape positive is ported as TWO honest reshape controls), 1
# re-aimed, 2 vacuous. Plus 1 ADDED (weak-reorder-children) for clause coverage.
#
# CARRIER NARROWING. The sibling models the whole per-code-point stream
# construction (four append loops emitting '<g id="' ++ gid ++ '">' ++ children
# ++ '</g>' over `List[int]`). This bundle abstracts the emission to a single
# command stream of `RenderCmd` (beginGroup gid / child / endGroup): the grouping
# label and the code-point-level framing constants are abstracted away (they do
# not affect the tested behaviour — see mapping.md §2), and the modeled content
# is the ORDER and IDENTITY of the three command kinds. So the sibling's
# character-level rivals (empty-id vs dropped-gid, take(j) prefix invariants)
# collapse onto the same command-stream discriminators here: dropping the
# identifier IS `beginGroup none`, no group IS the bare `children`, omitting the
# close IS the missing `endGroup`. Nothing modeled by the sibling is lost.
#
# RE-AIMED (admissibility): the sibling establishes that both half-permission
#   read-only inputs are usable and the len(gid)>0 branch is reachable. This
#   backend has no permissions and no `require` clause, so nothing could exclude
#   a normal input — that probe is vacuous. Re-aimed at the residual total-domain
#   admissibility risk: that the post-image is UNSATISFIABLE / DEGENERATE at the
#   interesting point. The case discharges a concrete in-region assert that the
#   stream for a present identifier differs from the stream for none (the opening
#   element genuinely carries the identifier).
# VACUOUS (frame-mutation-write-gid, frame-mutation-write-children): the sibling
#   writes into a read-only half-permission input to trip INSUFFICIENT
#   PERMISSION. This backend is referentially transparent, has no heap or
#   aliasing, and declares NO `mut` binder — there is no read-only input to
#   overwrite and no substitute probe. Not fabricated.
#
# ADDED (1, clause coverage): weak-reorder-children. The sibling's per-code-point
#   loop invariants pin the body order implicitly; here the "children carried
#   through unchanged and in order" is an INDEPENDENT top-level clause
#   (C4: out.tail = children ++ [endGroup]) that no ported rival attacks
#   (no-group drops the body, omit-close keeps order, drop-identifier keeps
#   order). Without this rival C4 would be an unattacked clause and the `children`
#   binder would never be moved to a length-2 stream whose reversal differs. Its
#   faithful counterpart (reordering the contained drawings) regresses the
#   content tests, and it carries a machine-checked witness at
#   `gid=some "a", children=[child 0, child 1]`.
#
# COVERAGE. Binders moved by the reject witnesses:
#   gid      {some "a", none};
#   children {[], [child 0], [child 0, child 1]}  -- both varied, pts = 4
#   distinct input points. Independent post-image clauses attacked:
#   C1 master (all four rivals); C2 opens-on-identifier (weak-no-group,
#   weak-drop-identifier); C3 closes (weak-no-group, weak-omit-close);
#   C4 body-in-order (weak-reorder-children); C5 length (weak-no-group,
#   weak-omit-close). All five clauses attacked; no clause left uncovered.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the `axioms` region is empty — the grouping commands are modeled
#   directly, not via an axiomatized callee), so there is nothing here for this
#   gate to probe. See mapping.md §3.
AXIOM_TESTS = []
