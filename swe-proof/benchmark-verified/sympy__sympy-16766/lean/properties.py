"""properties.py — G-PBT falsification battery for sympy__sympy-16766 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant produced by region surgery: only text strictly inside
``-- impl-start``/``-- impl-end`` — and, for the one case that legitimately
re-proves, inside ``-- proof-start``/``-- proof-end`` — is changed. So
``markers.same_spec`` holds by construction, the single
``theorem correct_indexedCode`` STATEMENT stays byte-identical, and no case adds
an ``axiom``/``theorem``/``lemma`` or reaches for ``sorry``/``admit``/
``native_decide``. ``expect:"verify"`` passes iff the file elaborates with the
frozen obligation closed; ``expect:"reject"`` passes iff it does NOT verify AND
the case's refutation ``witness`` holds of the rival while FAILING on the frozen
solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``); that manifest is the design document, not a text
to translate. The nagini sibling models the same single behavior over a
``PSeq[int]`` / ``PSeq[PSeq[int]]`` code-point carrier with a front-recursive
pure separator fold and a backward materialization loop, so most of its case
mechanics are about that loop's invariant. This bundle models the SAME purely
functional core — assembling a rendered array element access out of an already
rendered name and an already rendered list of subscripts — over Lean ``String``
/ ``List String``, where the join is a single library call and there is no loop
invariant to break. Each nagini case therefore carries over as its ARGUMENT
(which postcondition component it attacks, and why its faithful real
counterpart would not resolve), re-mechanized against this carrier.

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_indexedCode base subscripts result`` pins result to a single
equation over BOTH input binders:

    result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]"

Read as independent components of one concatenation chain, each separately
attackable and each attacked below:

  * (K0 prefix)     the result opens with exactly ``base`` and nothing else —
                    no surrounding text before it, and the name is not dropped;
  * (K1 brackets)   the subscript block is wrapped in the literal ``"["`` /
                    ``"]"`` pair, for EVERY admitted subscript list;
  * (K2 separator)  adjacent subscripts are separated by exactly ``", "``
                    (comma then space), never by a bare comma;
  * (K3 order)      the subscripts appear in their INPUT order.

This is a GROUNDED postcondition: the right-hand side is spelled out over the
actual input carriers with library operations, not equated to an opaque
answer key, so there is no "wrong echo" hole — the cheapest honest
implementation literally returns that chain and is CORRECT
(``pos-inline-chain`` below). Consequently the nagini
UNGROUNDED-ORACLE-ECHO worry is vacuous here too, and its place is taken by
honest cheapest-implementation positive controls.

BINDER STRUCTURE. The predicate has exactly two input binders, ``base`` and
``subscripts``, and both are load-bearing. Both are VARIED across the reject
witnesses rather than pinned: ``base`` takes seven distinct values and
``subscripts`` ranges over the empty, single-element, two-element and
three-element lists of distinct strings (see the point-spread block at the end,
``pts=7``). One rival exists specifically to abuse ``base``
(``weak-name-dropped``) and one specifically to abuse the ORDER within
``subscripts`` (``weak-order-reversed``), so neither binder is a binder no rival
was built to exploit. The ``subscripts`` binder's BOUNDARY (the empty list) is
attacked from both directions — ``pos-empty-cased`` in the verify lane,
``weak-partial-domain-empty-subscripts`` in the reject lane — so it is not a
point that merely appears in a witness without changing any verdict.

F2P GROUND TRUTH. The added test asserts that an access on a base rendered
``p`` at subscripts rendered ``0`` and ``1`` prints exactly ``p[0, 1]``. The
observable discriminators in that one assertion are precisely the four
components above: the bare name prefix, the square brackets, the comma-SPACE
separator, and the subscript order. Every reject case below attacks one of them
and argues in ``refinement`` that its faithful real counterpart would fail that
assertion, so a rival that VERIFIED would be a true
verify-does-not-imply-resolve break rather than an artifact.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is ``intro`` + ``unfold`` +
``rfl``, tuned to the frozen syntactic form — so a rejection alone attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet that states ``¬ problem_spec_indexedCode`` of the rival's own output at
one concrete input and closes by ``decide``. Both binders are ground string /
list literals, so no witness head binds anything and there are no hypotheses
whose joint satisfiability could be in question (the gate's
consistency probe is not even reached). Every witness was checked with two real
``lake env lean`` builds: it ELABORATES against its rival and FAILS on the
frozen solution, so it discriminates rather than asserting a tautology.

VACUOUS CLASSES on this carrier (no substitute probe is fabricated):

  * FRAME / PERMISSION MUTATION — the nagini sibling's two mandatory
    frame-mutation rivals write into a read-only half-permission input and are
    rejected by the permission system, which the value postcondition cannot even
    see. Lean is referentially transparent: ``base`` and ``subscripts`` are
    immutable values, there is no aliasing, no fractional permission and no
    read-only cell to overwrite, so the class has no counterpart at all.
  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. (The
    nagini sibling carries no ``diverge-*``/``nonterm-*`` case either, so
    nothing was dropped in the port; but the class is not empty here and the
    reason it ships unattacked is measured, not assumed.)

    The frozen ``implementation_indexedCode`` is a total ``def``, but a rival is
    NOT confined to that shape: replacing the whole impl region with a
    ``partial def`` that calls itself is admissible under ``variant_scope``
    (``partial`` is not an assumption token — it is banned in a WITNESS, not in
    a variant impl) and it does not verify, so a diverging rival IS expressible
    on this carrier. What is not expressible is a witness that REFUTES it. A
    ``partial def`` compiles to an opaque constant with no equation lemma, so
    the kernel cannot reduce ``implementation_indexedCode "q" ["0"]`` at all:
    measured, ``decide`` fails with ``instDecidableNot did not reduce to
    isTrue or isFalse`` for ``¬ problem_spec_indexedCode …`` AND, identically,
    for the exact opposite claim ``problem_spec_indexedCode …``. That is the
    gate's own ``witness-undecided`` signature: the exit code carries no
    information about the claim, so such a case would be inconclusive rather
    than a refutation.

    Nor does the hypothesis-conditioned escape hatch work, and this was tried
    rather than assumed. A witness of the shape ``(hv : impl … = v) (hne : v ≠
    "q[0]") : ¬ problem_spec_indexedCode "q" ["0"] v`` ELABORATES against the
    diverging rival — but it also elaborates against the FROZEN solution (both
    exit 0), because the refutation follows from ``hne`` alone and never
    mentions which impl produced ``v``. That is ``witness-vacuous``: it
    discriminates nothing. There is no third shape, because the rival's defect
    is the ABSENCE of a value and this spec's only clause is an equation ON the
    value; a total-carrier spec cannot separate "diverges" from "returns
    something I cannot compute". So the honest disposition is a hole in the
    SPEC's expressive reach, recorded here, not a completed lane.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` — the assembly is modeled deeply and the two sub-renderings enter as
the inputs themselves — so the nagini ``AXIOM_TESTS`` (also empty) are dropped;
the axiom lane belongs to G-AX and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16766"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# Solution.lean (asserted by _swap at import time, so the manifest breaks loudly
# if the frozen solution ever drifts).
# ---------------------------------------------------------------------------
# impl region: the join binding and the assembly/return line.
_I_LET = '  let joined := String.intercalate ", " subscripts\n'
_I_RET = '  return base ++ "[" ++ joined ++ "]"'

# proof region: the whole frozen tactic body, and its opening intro line.
_P_INTRO = "  intro base subscripts\n"
_P_BODY = (
    "  intro base subscripts\n"
    "  unfold problem_spec_indexedCode implementation_indexedCode\n"
    "  rfl\n"
)


def _w(base, subscripts):
    """Refutation witness: the rival's own output fails the spec predicate at one
    concrete (base, subscripts) point. Both binders are ground literals, so the
    head binds nothing and `decide` settles it on the closed term."""
    return (
        f"example : ¬ problem_spec_indexedCode {base} {subscripts}\n"
        f"    (implementation_indexedCode {base} {subscripts}) := by\n"
        "  unfold problem_spec_indexedCode implementation_indexedCode\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_indexedCode` statement byte-identical and adds no
    # declaration.
    # =====================================================================
    {
        "id": "pos-inline-chain",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest implementation: drop the intermediate binding and
        # return the assembled chain in one expression. Definitionally the
        # frozen body, so the frozen proof still closes untouched.
        # (Confirmed by a real build.)
        "module": _swaps(
            _BASE,
            (_I_LET, ""),
            (_I_RET,
             '  return base ++ "[" ++ String.intercalate ", " subscripts ++ "]"'),
        ),
        "rationale": (
            "Ports nagini's pos-control-oracle-direct. The postcondition is "
            "GROUNDED — its right-hand side is spelled out over the input "
            "binders with library operations, not an opaque answer key — so an "
            "implementation that returns exactly that chain is doing the work, "
            "not echoing an oracle, and is CORRECT. It must verify; if it did "
            "not, the spec would be SPEC-TOO-STRONG (unsatisfiable by the very "
            "witness it names). The intermediate binding is dropped, so this is "
            "definitionally the frozen body and the frozen tactic body closes "
            "with no re-proof, no new lemma and no assumption token."
        ),
    },
    {
        "id": "pos-accumulator",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: build the result by mutating a
        # local accumulator one piece at a time (name, open bracket, joined
        # subscripts, close bracket) instead of one concatenation expression.
        # Different control/data flow, same value; frozen proof still closes.
        # (Confirmed by a real build.)
        "module": _swaps(
            _BASE,
            (_I_LET,
             "  let mut s := base\n"
             '  s := s ++ "["\n'
             '  s := s ++ String.intercalate ", " subscripts\n'
             '  s := s ++ "]"\n'),
            (_I_RET, "  return s"),
        ),
        "rationale": (
            "Ports nagini's pos-control-branch-reorder in its role as 'a "
            "faithful but structurally DIFFERENT correct shape must still "
            "verify'. The nagini reshape reorders the branch of its "
            "materialization loop; this carrier has no such loop (the join is a "
            "single library call), so the analogous reshape is a mutable "
            "accumulator appended to piecewise rather than one concatenation "
            "expression — genuinely different data flow, identical value on "
            "every input, so all four components (prefix / brackets / separator "
            "/ order) still hold. Must verify, else SPEC-TOO-STRONG against a "
            "faithful different shape. Statement byte-identical; no new "
            "declaration."
        ),
    },
    {
        "id": "pos-empty-cased",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape with a real BRANCH: the
        # no-subscript case is emitted directly as the name followed by an empty
        # bracket pair, the general case unchanged. Observationally identical to
        # the frozen impl (the join of an empty list is empty), but the frozen
        # `rfl` no longer closes, so the proof region is honestly re-proved by
        # case analysis on the subscript list. The `correct_indexedCode`
        # STATEMENT is byte-identical and no lemma/axiom is added.
        # (Confirmed by a real build.)
        "module": _swaps(
            _BASE,
            (_I_RET,
             "  if subscripts.isEmpty then\n"
             '    return base ++ "[]"\n'
             '  return base ++ "[" ++ joined ++ "]"'),
            (_P_BODY,
             "  intro base subscripts\n"
             "  unfold problem_spec_indexedCode implementation_indexedCode\n"
             "  cases subscripts with\n"
             "  | nil => simp [Id.run, String.intercalate]\n"
             '           rw [show ("[]" : String) = "[" ++ "]" from rfl, '
             "String.append_assoc]\n"
             "           rfl\n"
             "  | cons a t => rfl\n"),
        ),
        "rationale": (
            "A second, harder soundness positive: the reshape adds a real "
            "BRANCH that special-cases the empty subscript list, emitting the "
            "name followed by an empty bracket pair. It agrees with the "
            "postcondition on the whole domain (the join of an empty list is "
            "empty, so both branches produce the same string), so it must "
            "verify — else the spec would be SPEC-TOO-STRONG at exactly the "
            "boundary of the `subscripts` binder. Unlike the other two "
            "positives this one is NOT definitionally the frozen body, so the "
            "obligation is genuinely re-proved inside the proof region by case "
            "analysis on `subscripts`; the theorem statement is byte-identical "
            "and nothing is assumed (no new axiom/lemma, no sorry/admit/"
            "native_decide). This is the case that shows an `expect=verify` "
            "pass here comes from reproving the obligation, not from leaving it "
            "syntactically undisturbed."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
    # F2P-shaped input. The frozen theorem carries NO precondition hypothesis
    # (it is a bare ∀ over both binders), so nagini's "the precondition admits
    # the in-domain input" probe re-expresses as: discharge the spec predicate
    # by evaluation at the concrete F2P-shaped point as a `have`, then close the
    # frozen obligation verbatim. Nothing is assumed; the ground instance is a
    # `have` prepended to the existing tactic body, the statement is
    # byte-identical. (Confirmed by a real build.)
    # =====================================================================
    {
        "id": "admiss-ground-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_indexedCode "p" ["0", "1"]\n'
            '      (implementation_indexedCode "p" ["0", "1"]) := by\n'
            "    unfold problem_spec_indexedCode implementation_indexedCode\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": (
            "Ports nagini's admiss-in-domain. There the probe asserts the "
            "precondition (a minimum subscript count) admits a normal input; "
            "the frozen obligation here has no precondition hypothesis at all, "
            "so the honest analogue is to show the POSTCONDITION is actually "
            "satisfiable at the F2P-shaped point (a name rendered `p` with two "
            "subscripts rendered `0` and `1`) by evaluating it as a `have`, "
            "then close the frozen obligation verbatim. Must verify: if the "
            "modeled relation were unsatisfiable at exactly a normal in-domain "
            "input, the obligation would be vacuous or over-constrained (the "
            "analogue of PRECOND-TOO-STRONG). Nothing is assumed and no "
            "declaration is added."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve the F2P, and (b) a witness
    # pinning the violation at one concrete input, checked to hold of the rival
    # and to FAIL on the frozen solution.
    # =====================================================================
    {
        "id": "weak-bare-comma-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Joins adjacent subscripts with a bare comma, omitting the space.
        "module": _swap(
            _BASE, _I_LET,
            '  let joined := String.intercalate "," subscripts\n'),
        "refinement": (
            "This is the canonical near-miss real counterpart: the subscripts "
            "are joined with a bare comma instead of comma-then-space. For a "
            "two-subscript access it emits the name, bracket, first subscript, "
            "comma, second subscript, bracket — one character short of the "
            "asserted output. The F2P assertion compares the printed line to a "
            "literal containing the space, so it FAILS and the faithful patch "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from K2 (separator): the spec pins "
            '`String.intercalate ", " subscripts` and the rival produces '
            '`String.intercalate "," subscripts`, which differ for every '
            "subscript list of length >= 2. Refuted at the F2P-shaped point "
            "(base rendered `p`, two subscripts) — the smallest input at which "
            "the separator is observable at all, since a single-subscript list "
            "has no adjacent pair."
        ),
        "witness": _w('"p"', '["0", "1"]'),
    },
    {
        "id": "weak-round-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        # Wraps the subscript block in round brackets instead of square ones.
        "module": _swap(
            _BASE, _I_RET, '  return base ++ "(" ++ joined ++ ")"'),
        "refinement": (
            "A faithful counterpart that wrapped the subscript block in round "
            "brackets emits a call-like line rather than a subscripted one — "
            "not merely cosmetically wrong but a different Python expression. "
            "The F2P assertion pins the square-bracket form, so it FAILS and "
            "the faithful patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from K1 (brackets): the spec pins the literal `\"[\"` / "
            "`\"]\"` pair around the joined subscripts; the rival emits the "
            "round pair, so the equation fails for EVERY input. Refuted at a "
            "distinct point from the separator rival — a different base "
            "(rendered `q`) and a single-subscript list — showing the bracket "
            "component is pinned independently of the subscript count, i.e. "
            "even where the separator is unobservable."
        ),
        "witness": _w('"q"', '["0"]'),
    },
    {
        "id": "weak-surrounding-text",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepends extra text ahead of the name — the shape of the pre-fix
        # placeholder-annotation behavior this bundle's prepatch variant models.
        "module": _swap(
            _BASE, _I_RET, '  return "# " ++ base ++ "[" ++ joined ++ "]"'),
        "refinement": (
            "Emitting anything ahead of the name is the shape of the PRE-FIX "
            "behavior this bundle's prepatch variant models: the rendered line "
            "carries an extra annotation prefix rather than being exactly the "
            "access. Any leading content makes the printed line differ from the "
            "asserted literal, which is precisely the state the change is "
            "supposed to repair, so the faithful patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from K0 (prefix): the spec pins the result to OPEN with "
            "exactly `base` — the equation admits no surrounding text — and the "
            "rival prepends two characters. Refuted at a third distinct point "
            "(base rendered `a`, THREE subscripts) so this witness also "
            "exercises the longest subscript list in the battery."
        ),
        "witness": _w('"a"', '["i", "j", "k"]'),
    },
    {
        "id": "weak-name-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Omits the name entirely, emitting only the bracketed subscript block.
        # This is the rival built specifically to abuse the `base` binder.
        "module": _swap(_BASE, _I_RET, '  return "[" ++ joined ++ "]"'),
        "refinement": (
            "A faithful counterpart that assembled only the bracketed subscript "
            "block would emit a line with no array name at all — a bare "
            "subscript expression that is not even the same kind of Python "
            "expression. The F2P assertion pins the name as the prefix, so it "
            "FAILS and the faithful patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from K0 (prefix), attacking the OTHER input binder: the "
            "spec pins the result to begin with exactly `base`, and this rival "
            "IGNORES `base` completely. It exists so the battery does not leave "
            "`base` an unexploited binder — without it every rival would "
            "reproduce the name correctly and an implementation that mishandled "
            "only the name would go unnoticed. Refuted at a base rendered `pp` "
            "(deliberately not a single character, so the omission is not "
            "confusable with a length coincidence) with a single subscript."
        ),
        "witness": _w('"pp"', '["x"]'),
    },
    {
        "id": "weak-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Joins the subscripts in reverse input order. Attacks the ORDER
        # structure of the `subscripts` binder rather than its rendering.
        "module": _swap(
            _BASE, _I_LET,
            '  let joined := String.intercalate ", " subscripts.reverse\n'),
        "refinement": (
            "A faithful counterpart that emitted the subscripts in reverse "
            "order indexes a different element of the array for every access "
            "with two or more subscripts — silently wrong generated code, not a "
            "formatting slip. The F2P assertion uses two DISTINCT subscripts, so "
            "the printed line comes out with them transposed and the assertion "
            "FAILS; the faithful patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from K3 (order): the spec pins the join over `subscripts` "
            "in input order, and the rival joins `subscripts.reverse`, which "
            "agrees only when the rendered subscript sequence is a palindrome. "
            "This is the rival built to abuse the ORDER structure of the "
            "`subscripts` binder — the other rivals all preserve it, so without "
            "this case a permutation bug would pass the battery. Refuted at "
            "base rendered `z` with three pairwise-distinct subscripts, a "
            "non-palindromic list."
        ),
        "witness": _w('"z"', '["a", "b", "c"]'),
    },
    {
        "id": "weak-partial-domain-single-subscript",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the multi-subscript F2P input but WRONG on the
        # single-subscript sub-domain, where the brackets are dropped.
        "module": _swap(
            _BASE, _I_RET,
            "  if subscripts.length = 1 then\n"
            "    return base ++ joined\n"
            '  return base ++ "[" ++ joined ++ "]"'),
        "refinement": (
            "PARTIAL-DOMAIN rival, and the near-miss of the battery: on the "
            "literal F2P input (two subscripts) it is IDENTICAL to the frozen "
            "behavior, so it passes the one asserted value. It diverges only on "
            "the single-subscript sub-domain, where it drops the brackets and "
            "concatenates the name and the subscript directly — producing "
            "source that is not the access at all. A real patch shaped this way "
            "would satisfy the added assertion while emitting wrong code for "
            "every single-subscript access, contradicting the relation the spec "
            "fixes over the whole admitted domain; it is not the intended "
            "behavior and would regress single-subscript rendering. Its own "
            "witness therefore sits at the sub-domain it gets wrong, not at the "
            "F2P point, so this case's rationale claims no more than the "
            "manifest demonstrates."
        ),
        "rationale": (
            "REJECT from K1 (brackets) over the FULL domain of the `subscripts` "
            "binder: the spec's equation pins the bracket pair for every list, "
            "including the one-element list, and the rival omits it exactly "
            "there. This is a strict near-miss of `weak-round-brackets` (which "
            "is wrong everywhere), so it does not share that rival's witness: "
            "it is refuted at a one-element subscript list with a base rendered "
            "`m`, the sub-domain where it and gold actually differ. At the "
            "two-subscript F2P point it would be indistinguishable from gold, "
            "which is precisely the property that makes it dangerous."
        ),
        "witness": _w('"m"', '["0"]'),
    },
    {
        "id": "weak-partial-domain-empty-subscripts",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on EVERY non-empty subscript list — including the F2P input and
        # including the single-element sub-domain the rival above attacks — but
        # WRONG on the empty list, where the bracket pair is dropped entirely.
        # (Confirmed by a real build: the rival does not verify, its witness
        # elaborates against the rival, fails on the frozen solution, and the
        # flipped claim inverts both exit codes.)
        "module": _swap(
            _BASE, _I_RET,
            "  if subscripts.isEmpty then\n"
            "    return base\n"
            '  return base ++ "[" ++ joined ++ "]"'),
        "refinement": (
            "The STRICTEST near-miss in the battery: this rival agrees with the "
            "frozen behavior on every subscript list of length >= 1, so it "
            "passes the F2P assertion AND the single-subscript sub-domain that "
            "`weak-partial-domain-single-subscript` catches. It diverges only "
            "where the subscript list is EMPTY, emitting the bare name with no "
            "bracket pair at all. A real patch shaped this way would satisfy "
            "every asserted value while rendering a no-subscript access as a "
            "plain name — a different expression, not a formatting slip — so it "
            "is not the intended behavior over the domain the spec fixes. Its "
            "witness therefore sits at the empty list, the only point where it "
            "and the frozen impl differ, so this case claims no more than the "
            "manifest demonstrates."
        ),
        "rationale": (
            "REJECT from K1 (brackets) at the BOUNDARY of the `subscripts` "
            "binder. The spec's equation pins the literal `\"[\"` / `\"]\"` pair "
            "for EVERY list, and the empty list is in the domain (the predicate "
            "is a bare forall over `List String` with no length precondition), "
            "so the frozen relation requires `base ++ \"[]\"` there. This closes "
            "a real gap the rest of the battery left open: the empty list was "
            "touched only by the `pos-empty-cased` POSITIVE, so before this case "
            "the boundary was exercised in the verify direction only and an impl "
            "that mishandled exactly the no-subscript input would have been "
            "rejected for no demonstrated reason. Refuted at a base rendered "
            "`w` with the empty subscript list — a seventh distinct input point, "
            "and the only one at which this rival is observably wrong."
        ),
        "witness": _w('"w"', '[]'),
    },
    {
        "id": "pos-loop-free-foldl-join",
        "kind": "soundness",
        "expect": "verify",
        # A THIRD structurally different CORRECT reshape, and the one whose proof
        # is furthest from the frozen script: the separator join is written out by
        # hand as a fold over the tail seeded with the head, instead of calling
        # the library join. Observationally identical on every input, but NOT
        # definitionally equal — the frozen `rfl` fails on it (confirmed by a
        # real build), so the obligation is genuinely re-proved by case analysis
        # plus an induction bridging the hand-rolled fold to the library join.
        # Statement byte-identical; no new declaration (the bridge is a `have`
        # inside the existing tactic body, not a top-level lemma).
        "module": _swaps(
            _BASE,
            (_I_LET,
             "  let joined := match subscripts with\n"
             '    | [] => ""\n'
             '    | h :: t => t.foldl (fun a s => a ++ ", " ++ s) h\n'),
            (_P_BODY,
             "  intro base subscripts\n"
             "  unfold problem_spec_indexedCode implementation_indexedCode\n"
             "  have inter : ∀ (h : String) (t : List String),\n"
             '      String.intercalate ", " (h :: t)\n'
             '        = t.foldl (fun a s => a ++ ", " ++ s) h := by\n'
             "    intro h t\n"
             "    induction t generalizing h with\n"
             "    | nil => rfl\n"
             "    | cons a u ih => simp only [List.foldl_cons]; exact ih _\n"
             "  cases subscripts with\n"
             "  | nil => rfl\n"
             "  | cons h t =>\n"
             '    show base ++ "[" ++ t.foldl (fun a s => a ++ ", " ++ s) h ++ "]"\n'
             '      = base ++ "[" ++ String.intercalate ", " (h :: t) ++ "]"\n'
             "    rw [inter h t]\n"),
        ),
        "rationale": (
            "The soundness positive that attacks the SEPARATOR clause from the "
            "verify side. The other three positives all obtain the joined "
            "subscript block from the same library call the spec names, so none "
            "of them tests whether the spec accepts an implementation that "
            "COMPUTES the comma-space join itself — and an over-strong spec that "
            "had accidentally pinned the library call rather than its value "
            "would still have passed the battery. This reshape spells the join "
            "out as a left fold over the tail seeded with the head, which is the "
            "faithful functional counterpart of the real separator-join loop, "
            "and it must verify because it agrees with the frozen relation on "
            "the whole domain (both branches of the match). It is not "
            "definitionally the frozen body — the frozen `rfl` does not close it "
            "— so the obligation is genuinely re-proved: a case split on "
            "`subscripts` plus an induction, stated as a `have`, that bridges "
            "the hand-rolled fold to the library join. Nothing is assumed (no "
            "new axiom/lemma, no sorry/admit/native_decide) and the "
            "`correct_indexedCode` statement is byte-identical."
        ),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 MANDATORY frame-mutation rivals, 4 value
# rivals) plus an EMPTY axiom lane. This bundle models the SAME single purely
# functional core, so every non-frame sibling case has a counterpart; the two
# frame cases do not, for a carrier reason spelled out below. THREE rivals are
# ADDED to close binder-coverage gaps the sibling did not have to worry about,
# and TWO soundness positives are ADDED to make the verify lane prove something.
# (The third rival and the second added positive came out of the audit pass; the
# `ADDED (audit)` rows below say which.)
#
#   sibling case                          -> here
#   -----------------------------------------------------------------------
#   pos-control-oracle-direct             -> pos-inline-chain        PORTED
#   pos-control-branch-reorder            -> pos-accumulator         RE-EXPRESSED
#   (none)                                -> pos-empty-cased         ADDED
#   admiss-in-domain                      -> admiss-ground-point     RE-EXPRESSED
#   frame-mut-name-append                 -> (none)                  VACUOUS
#   frame-mut-index-append                -> (none)                  VACUOUS
#   rival-wrong-separator                 -> weak-bare-comma-separator      PORTED
#   rival-paren-not-bracket               -> weak-round-brackets            PORTED
#   rival-surrounding-prefix              -> weak-surrounding-text          PORTED
#   rival-partial-domain-single-index     -> weak-partial-domain-single-subscript
#                                                                    PORTED
#   (none)                                -> weak-name-dropped       ADDED
#   (none)                                -> weak-order-reversed     ADDED
#   (none)                                -> weak-partial-domain-empty-subscripts
#                                                                    ADDED (audit)
#   (none)                                -> pos-loop-free-foldl-join
#                                                                    ADDED (audit)
#   AXIOM_TESTS (0)                       -> (none)                  DROPPED (G-AX)
#
# RE-EXPRESSED (pos-accumulator): the sibling's structurally-different positive
#   reorders the branch of a backward materialization loop, and every one of its
#   loop invariants is part of the mechanics. This carrier has no loop — the
#   join is one library call — so there is no branch to reorder and no invariant
#   to preserve. The argument being ported is "a faithful but structurally
#   different correct implementation must still verify", and the analogous
#   reshape here is piecewise accumulation into a mutable local.
# RE-EXPRESSED (admiss-ground-point): the sibling asserts its minimum-count
#   precondition admits a normal input. The frozen obligation here is a bare ∀
#   over both binders with NO precondition hypothesis, so there is no
#   precondition to probe; the honest analogue is to show the postcondition is
#   satisfiable at the F2P-shaped point by evaluation, then close the frozen
#   obligation verbatim.
# ADDED (pos-empty-cased): the two ported positives are both DEFINITIONALLY
#   equal to the frozen body, so the frozen `rfl` closes them and neither
#   demonstrates that a verify here survives a genuine re-proof. This third
#   positive changes the impl enough that `rfl` no longer closes and the
#   obligation is re-proved by case analysis, with the statement byte-identical
#   and nothing assumed. (Measured: pairing this positive's IMPL with the frozen
#   tactic body fails with `Tactic 'rfl' failed`, so the re-proof is doing work
#   rather than decorating a body the frozen script would have closed anyway.)
# ADDED (pos-loop-free-foldl-join, audit): the three positives above all obtain
#   the joined block from the SAME `String.intercalate ", "` call the spec names,
#   so none of them tests whether the spec accepts an impl that computes the
#   comma-space join itself — a spec that had pinned the library call rather than
#   its value would have passed the battery unchallenged. This fourth positive
#   spells the join out as a left fold over the tail seeded with the head (the
#   faithful functional counterpart of the real separator-join loop), is not
#   definitionally the frozen body, and re-proves the obligation with a case
#   split plus an induction bridging the hand-rolled fold to the library join.
#   The bridge is a `have` inside the existing tactic body, so no top-level
#   lemma is added and the statement stays byte-identical.
#
#   NOTE on a reshape that is NOT shipped: the same join written as an
#   `Id.run do` + `let mut` + `for` accumulator with a first-element flag — the
#   idiom prompts/lean/spec_guide.md marks PREFERRED — is a faithful correct
#   impl whose proof could not be closed here in ~12 attempts (Route B helper
#   generalized over the accumulator, `show`-bridge, `congrArg`, `simp +revert`).
#   The wall is not the join lemma (proved, and reused above) but bridging the
#   desugared `List.forIn'.loop` term the `let mut` pair elaborates to; every
#   attempt failed on `Expected type must not contain free variables` or on a
#   `show` that was not definitionally equal. That is reported as UNCERTAIN, not
#   as a spec hole: failing to find a proof is not evidence the spec rejects the
#   impl, and the loop-free fold above covers the same argument (a hand-computed
#   separator join must verify) with a proof that closes.
# ADDED (weak-name-dropped, weak-order-reversed): the four sibling rivals all
#   reproduce the name correctly AND preserve subscript order, attacking only
#   the separator, the brackets, and surrounding text. That leaves the `base`
#   binder and the ORDER structure of `subscripts` unexploited — a rival that
#   mishandled only one of those would verify and the battery would never
#   notice. Both additions attack real, load-bearing components of the SAME
#   modeled equation (the prefix and the join order), and both are pinned by the
#   F2P assertion, so neither is fabricated for an unmodeled behavior.
# VACUOUS (frame/permission mutation, 2 sibling cases): the sibling's rivals
#   write into a read-only half-permission input and are rejected by the
#   permission system, not by the value postcondition. Lean is referentially
#   transparent — `base` and `subscripts` are immutable values, there is no
#   aliasing, no fractional permission and no read-only cell — so the class has
#   no counterpart and no substitute probe is fabricated.
# VACUOUS (divergence): the sibling carries no `diverge-*`/`nonterm-*` case, and
#   on this backend the class could not be expressed anyway —
#   `implementation_indexedCode` is a total Lean `def`, so a non-terminating
#   implementation cannot be written. (This is the lean disposition; the velvet
#   `partial`-semantics KNOWN HOLE recorded in the corpus-wide termination-semantics finding does
#   not apply to a total `def`.)
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input points
# (pts=7), and BOTH binders vary across them:
#
#   (base, subscripts)                  case                                comp
#   ("p",  ["0", "1"])   weak-bare-comma-separator                          K2
#   ("q",  ["0"])        weak-round-brackets                                K1
#   ("a",  ["i","j","k"])weak-surrounding-text                              K0
#   ("pp", ["x"])        weak-name-dropped                                  K0
#   ("z",  ["a","b","c"])weak-order-reversed                                K3
#   ("m",  ["0"])        weak-partial-domain-single-subscript               K1
#   ("w",  [])           weak-partial-domain-empty-subscripts               K1
#
#   `base` takes seven distinct values of two different lengths; `subscripts`
#   ranges over zero-, one-, two- and three-element lists with pairwise-distinct
#   elements. No rival shares a witness with another: the two K0 rivals fail for
#   different reasons (extra prefix vs. missing name) and the three K1 rivals are
#   refuted at three different points because they form a strict near-miss CHAIN
#   — `weak-round-brackets` is wrong everywhere, `-single-subscript` is wrong
#   only on one-element lists, `-empty-subscripts` is wrong only on the empty
#   list — so each is refuted in the sub-domain where it and gold actually
#   differ, and the two partial-domain rivals do not refute each other's point.
#
#   The empty list is now probed in BOTH directions: `pos-empty-cased` shows the
#   spec ACCEPTS a correct impl that special-cases it, and
#   `weak-partial-domain-empty-subscripts` shows the spec REJECTS one that gets
#   it wrong. Before the second of those the boundary was verify-only, which is
#   the shape of a binder point that looks covered and tests nothing.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# opaque callee and consumes no axiom (the assembly is modeled deeply), so there
# is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
