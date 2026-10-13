"""properties.py — G-PBT falsification battery for sympy__sympy-23262 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end``, and — for a case that legitimately re-proves — inside
``-- proof-start`` / ``-- proof-end``, so ``markers.same_spec`` holds and the
single ``theorem correct_renderArg`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a FLAT single-level renderer — ``render_container(elems: PSeq[PSeq[int]],
is_paren: bool) -> PSeq[int]``, an already-rendered element list plus a
kind flag, assembled by an accumulator loop whose ``joined`` invariant carries
the proof. This Lean bundle models the same behaviour RECURSIVELY over a nested
carrier: one total function ``implementation_renderArg : Arg → String`` on the
inductive ``Arg`` (a printed leaf, a bracketed node, a parenthesised node), with
the kind flag REPLACED by the constructor and the element list replaced by the
node's children. So nagini's ``is_paren`` binder becomes the choice of
constructor and nagini's ``elems`` becomes the child list — plus a third axis
nagini does not have at all (nesting depth / the leaf arm), which this battery
attacks with two rivals that have no nagini counterpart. Per-case disposition is
in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior, one obligation). ``theorem
correct_renderArg : ∀ arg : Arg, problem_spec_renderArg arg
(implementation_renderArg arg)``, where the postcondition is the single grounded
pin ``result = specRender arg``. ``specRender`` is a TRANSPARENT, total,
front-recursive ``def`` over the function's own input — no ``opaque`` callee, no
axiom, no answer-key oracle — so pinning ``result = specRender arg`` is grounded
rather than an echo, and there is no "wrong echo" rival to build (echoing
``specRender`` IS the correct answer, so that shape ships as a POSITIVE control
instead).

WHICH CLAUSES CONSTRAIN THE IMPL. The pin is one equation, but ``specRender`` is
defined by cases, so it decomposes into three INDEPENDENT top-level arms, one per
constructor, and every rival below targets one of them:

  * C-leaf  — a printed leaf renders to its own string, verbatim.
  * C-list  — a bracketed node renders as its children, comma-and-space
              separated, wrapped in ``[`` … ``]``.
  * C-tuple — a parenthesised node renders the same way but wrapped in ``(`` …
              ``,)``: a comma BEFORE the closing parenthesis, at EVERY arity
              including one child.

Within C-list / C-tuple the pin further fixes, at every position: the opening
delimiter, the separator between children (comma AND space), the recursive
rendering of each child (so a nested node's own arm applies), and the closing
delimiter — including the trailing comma and the ORDER of its two characters.
The behavioural discriminator the failing test observes lives in C-tuple's
closer: a one-child parenthesised node must render as a container (with the
trailing comma), not as its bare child.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * SOUNDNESS / positive controls — APPLY, and are the real work here. On a
    tactic-proof backend a structurally different CORRECT impl needs a proof that
    actually closes for the NEW shape, with the theorem statement untouched.
    FOUR ship: the constructor arms permuted; the delimiter pair bound as a
    local tuple; the ``let parts`` locals inlined; and the parenthesised closer
    built by concatenating its two characters. Each is behaviourally identical on
    every input, so the pin still holds and each MUST verify — else the spec is
    SPEC-TOO-STRONG (over-fit to the frozen impl's syntactic form).

    The fourth is load-bearing and the first three are weaker than they look: all
    three of those are closed by the frozen tactic body BYTE-VERBATIM, i.e. each
    is definitionally equal to the frozen impl, so the frozen script never has to
    adapt and none of them can detect an obligation over-fit to the frozen
    PROOF. ``pos-closer-concat`` is the one whose residual goal the frozen body
    leaves OPEN (an associativity mismatch) and which therefore has to be
    genuinely re-proven inside the tactic region.

  * ADMISSIBILITY — the obligation carries NO precondition hypothesis (``∀ arg :
    Arg`` is unguarded; the modeled behaviour is total on the carrier), so
    nagini's "a normal input satisfies the precondition" probe has no binder to
    attack. The residual risk is a DEGENERATE post-image: a pin that no
    gold-shaped computation can meet at the interesting point reads like a pin
    every impl meets. ``admiss-shape-instances`` discharges three LIVE ground
    ``have``s inside the proof region — a one-child parenthesised node renders
    WITH the trailing comma, a one-child bracketed node renders WITHOUT one, and
    a two-child parenthesised node renders with it — alongside the frozen
    obligation, kept verbatim, so the real obligation still discharges. Nothing
    is assumed: no new declaration, statement byte-identical.

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini defended surface already
    has no heap input and no fractional permission (its inputs are pure
    immutable sequences plus a bool), so nagini itself declares the class
    inapplicable. Here it is doubly so: Lean is referentially transparent, the
    input is an immutable value, and there is no aliasing or permission system.
    No substitute is fabricated.

  * DIVERGENCE — VACUOUS in the shippable sense, with the reason corrected by
    measurement (see the DIVERGENCE note in the accounting block). The nagini
    sibling carries no ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case, so
    there is nothing to port. This bundle sets no
    ``loom.semantics.termination``: ``implementation_renderArg`` is a plain Lean
    ``def``, so totality is enforced by the DEFINITION checker. A measure-less
    self-recursive arm is refused outright (``fail to show termination``), which
    is the "total" disposition — genuinely rejected. A ``partial`` arm does
    elaborate and is also rejected, but no witness can discriminate it: a
    ``partial def`` is an opaque constant, so ``decide`` gets stuck. Nothing is
    shippable either way. NOT the known spec hole of
    ``the corpus-wide termination-semantics finding``, which applies to velvet under
    ``termination "partial"`` and not here.

  * PARTIAL-DOMAIN / VALUE — APPLY, and carry the battery. NINE rivals, each
    correct on part of the domain and diverging exactly where one arm of the pin
    bites.

WITNESS MECHANICS (specific to this carrier). On a tactic-proof backend "did not
verify" is the DEFAULT outcome of reshaping an impl — the frozen script's
``simp only`` + ``rw`` is tuned to the frozen form — so a rejection alone
attributes nothing to the spec. Every ``expect="reject"`` case therefore states
the spec predicate DIRECTLY at one concrete ``Arg`` and refutes it, in a file
whose proof region has been emptied so no tactic script can interfere.

The tactic needed one measured detour. ``decide`` alone does NOT close these
goals: the carrier is ``String``, and reducing the ``Decidable`` instance gets
stuck at ``String.decEq`` on the un-normalised concatenation (observed:
"reduction got stuck at the Decidable instance (implementation_renderArg
…).data.hasDecEq …"), while plain ``simp``/``norm_num`` leave a goal over the
unreduced ``String.intercalate.go`` accumulator. Handing the intercalate
unfolding and the ``List.map`` lemmas to ``simp only`` FIRST normalises both
sides to ground string literals, after which ``decide`` closes them:

    unfold problem_spec_renderArg
    simp only [implementation_renderArg, specRender, List.map_cons, List.map_nil,
               String.intercalate]
    decide

Against a rival this elaborates; against the frozen solution the same snippet
fails with ``decide proved that the proposition ¬True is false`` — i.e. gold
satisfies the pin at that input, which is exactly the discriminating half. No
witness binds a hypothesis in its head (every input is a ground ``Arg``
literal), so no consistency probe is needed and none of the hypotheses can be
inconsistent. No banned token (``sorry``/``admit``/``native_decide``/``axiom``/
``opaque``). Every witness below was checked out of band with
``scripts/lean_verify.sh``: each ELABORATES against its own rival (exit 0) and
FAILS on the frozen solution (exit 1, the ``¬True`` error above).

BINDER / POINT SPREAD. The single spec binder is ``arg : Arg``, and a battery
that refuted every rival at one convenient ``Arg`` would say nothing about the
pin's dependence on the carrier's shape. The eight witnesses probe eight
DISTINCT inputs, moving all three axes of the carrier independently:

  * CONSTRUCTOR — parenthesised nodes (four rivals), a bracketed node
    (``rej-list-as-tuple``), a bare leaf (``rej-leaf-not-verbatim``), and
    bracketed-wrapping-parenthesised nesting (``rej-nested-not-recursive``,
    ``rej-closer-order``). No arm of the pin is left unprobed.
  * ARITY — zero-depth (leaf), one child, two children, three children. The
    arity axis is load-bearing precisely because one rival
    (``rej-single-drops-comma``) is correct at every arity but one, so it is
    refuted at the one-child point where it diverges, while
    ``rej-prepatch-no-trailing-comma`` is refuted at a two-child point where the
    partial-domain rival AGREES with gold.
  * NESTING DEPTH — depth 0 (leaf), 1, and 2. Depth is what makes C-list/C-tuple
    RECURSIVE rather than flat, and ``rej-nested-not-recursive`` is refuted at a
    depth-2 input where the outer arm is correct and only the inner rendering is
    wrong, so a rival that mishandled only nesting cannot hide.

Two rivals share no refutation point; the near-miss ``rej-single-drops-comma``
gets its own one-child point rather than borrowing the pre-patch rival's, so its
``rationale``'s claimed sub-domain is the one the manifest actually demonstrates.

AXIOM lane: EMPTY. mapping.md §"doprint refinement" records that the only
unchanged callee is refined AWAY (type-only R, never called in the impl), so the
bundle declares no ``opaque`` and consumes no ``axiom``; ``axiom_check.py`` is a
skip stub. The nagini ``AXIOM_TESTS`` is likewise empty. Nothing to port, and
the gate ignores that lane regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23262"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl region (between
# `-- impl-start` and `-- impl-end`) or inside the proof region, and each is
# unique in Solution.lean — both facts asserted at load time by `_swap` /
# the asserts below. Editing only these keeps markers.same_spec True and the
# `theorem correct_renderArg` STATEMENT byte-identical (the spec view elides
# both regions).
# ---------------------------------------------------------------------------

# The bracketed-node arm of the impl. NOTE the two-space alignment after
# `.list` — it is what makes this text impl-region-only (the pure `specRender`
# def spells its arms on one line each), so the anchor cannot stray into the
# frozen spec.
_I_LIST = ('  | .list xs  =>\n'
           '      let parts := xs.map implementation_renderArg\n'
           '      "[" ++ String.intercalate ", " parts ++ "]"')

# The parenthesised-node arm of the impl — the arm carrying the discriminating
# closer.
_I_TUPLE = ('  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      "(" ++ String.intercalate ", " parts ++ ",)"')

# The WHOLE impl declaration (all three arms). Used by variants that permute or
# restructure the arms, where a per-arm anchor would not be enough.
_I_ALL = ('def implementation_renderArg : Arg → String\n'
          '  | .leaf s   => s\n' + _I_LIST + '\n' + _I_TUPLE)

# The impl's leaf arm, anchored together with the declaration head so the
# substring is unique (the bare arm text also occurs in the pure region).
_I_HEAD_LEAF = ('def implementation_renderArg : Arg → String\n'
                '  | .leaf s   => s')

# The parenthesised arm of the frozen PROOF. This text lies wholly after the
# first `:=` of the declaration, i.e. wholly inside the tactic body that
# variant_scope lets a variant retune; the pinned STATEMENT is everything up to
# that `:=` and is never touched.
_P_TUPLE = ('  | .tuple xs => by\n'
            '      simp only [problem_spec_renderArg, implementation_renderArg, specRender]\n'
            '      have : xs.map implementation_renderArg = xs.map specRender :=\n'
            '        List.map_congr_left (fun a _ => correct_renderArg a)\n'
            '      rw [this]')

for _a in (_I_LIST, _I_TUPLE, _I_ALL, _I_HEAD_LEAF, _P_TUPLE):
    assert _BASE.count(_a) == 1, f"anchor drifted or not unique: {_a[:60]!r}"


# ---------------------------------------------------------------------------
# Witness builder. State the spec predicate directly at one ground `Arg` and
# refute it. The carrier is `String`, so `decide` alone gets stuck reducing
# `String.decEq` over the un-normalised concatenation; `simp only` with the
# intercalate + List.map lemmas normalises both sides to ground literals first,
# and then `decide` closes. Elaborates on a rival; on gold the same snippet
# fails with `decide proved that the proposition ¬True is false`.
# ---------------------------------------------------------------------------

def _witness(arg):
    return (f"example : ¬ problem_spec_renderArg {arg}\n"
            f"    (implementation_renderArg {arg}) := by\n"
            "  unfold problem_spec_renderArg\n"
            "  simp only [implementation_renderArg, specRender, List.map_cons, "
            "List.map_nil,\n"
            "             String.intercalate]\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot, the spec is
    # SPEC-TOO-STRONG. Each keeps the `correct_renderArg` STATEMENT
    # byte-identical and re-proves honestly inside the tactic body where the
    # reshape needs it; none adds a declaration, an axiom, or a sorry.
    # =====================================================================
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the three constructor arms are written in a different ORDER
        # (parenthesised, bracketed, leaf) instead of (leaf, bracketed,
        # parenthesised). Lean pattern matching on distinct constructors is
        # order-insensitive, so the function is pointwise identical; the frozen
        # per-arm proof still applies arm-by-arm and closes unchanged.
        "module": _swap(
            _BASE, _I_ALL,
            'def implementation_renderArg : Arg → String\n'
            + _I_TUPLE + '\n' + _I_LIST + '\n'
            '  | .leaf s   => s'),
        "rationale": (
            "a correct impl with the constructor arms PERMUTED matches on three "
            "distinct constructors, so it is pointwise identical to the frozen "
            "impl and the pin `result = specRender arg` still holds at every "
            "input; it must verify. Defends all three arms (C-leaf, C-list, "
            "C-tuple) at once, since the whole declaration is reshaped. Ports "
            "the nagini pos-control-branch-reorder, whose flat `is_paren` "
            "branch order becomes the constructor arm order on this recursive "
            "carrier. If it cannot verify => SPEC-TOO-STRONG (the spec, or the "
            "obligation, is over-fit to the frozen arm order)."
        ),
    },
    {
        "id": "pos-delim-pair-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: each container arm binds its delimiter PAIR as one local
        # tuple and projects the two components, instead of writing the two
        # delimiter literals inline; the `parts` local is dropped and the
        # recursive map inlined. Same string on every input. The frozen proof
        # closes unchanged (the locals zeta-reduce and the projections reduce).
        "module": _swap(
            _BASE, _I_ALL,
            'def implementation_renderArg : Arg → String\n'
            '  | .leaf s   => s\n'
            '  | .list xs  =>\n'
            '      let d := ("[", "]")\n'
            '      d.1 ++ String.intercalate ", " (xs.map implementation_renderArg) ++ d.2\n'
            '  | .tuple xs =>\n'
            '      let d := ("(", ",)")\n'
            '      d.1 ++ String.intercalate ", " (xs.map implementation_renderArg) ++ d.2'),
        "rationale": (
            "binding each arm's delimiter PAIR as a single local tuple and "
            "projecting its components is a different construction of the "
            "identical delimiter values (the locals zeta-reduce and the "
            "projections reduce), so the pin `result = specRender arg` still "
            "holds and it must verify. This is the re-expression of the nagini "
            "pos-control-concat-delim on this carrier: the nagini control builds "
            "the closing delimiter by a different constructor call of the same "
            "value, here the whole pair is bound and projected. If it cannot "
            "verify => SPEC-TOO-STRONG (over-fit to inline delimiter literals)."
        ),
    },
    {
        "id": "pos-closer-concat",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the parenthesised closer is BUILT by concatenating its two
        # characters (`"," ++ ")"`) instead of being written as the single
        # literal `",)"`. Unlike the other three positives this one is NOT
        # closed by the frozen tactic body — the residual goal is the
        # associativity mismatch `… ++ ("," ++ ")")` vs `… ++ ",)"` — so it is
        # the one positive here that forces an ACTUAL reproof for the new shape
        # rather than riding on definitional equality. Measured: with the frozen
        # body verbatim the file fails (exit 1, `unsolved goals … ("," ++ ")") =
        # … ",)"`); with a single added `rfl` it closes (exit 0).
        "module": _swap(
            _swap(_BASE, _I_TUPLE,
                  '  | .tuple xs =>\n'
                  '      let parts := xs.map implementation_renderArg\n'
                  '      "(" ++ String.intercalate ", " parts ++ ("," ++ ")")'),
            _P_TUPLE,
            _P_TUPLE.replace('      rw [this]', '      rw [this]\n      rfl')),
        "rationale": (
            "building the parenthesised closer by CONCATENATING its two "
            "characters instead of writing the single two-character literal "
            "computes the identical string at every input, so the pin `result = "
            "specRender arg` still holds and it must verify. This case exists "
            "because the other three positives are all closed by the frozen "
            "tactic body UNCHANGED — i.e. each is definitionally equal to the "
            "frozen impl, so none of them tests whether the obligation is "
            "over-fit to the frozen impl's PROOF shape, only to its syntactic "
            "form. This one is not defeq: the frozen body leaves an "
            "associativity goal open, and the case discharges it inside the "
            "tactic region (one added `rfl`), with the STATEMENT byte-identical "
            "and no new declaration. So it is the battery's only real "
            "SPEC-TOO-STRONG probe against a reshape that must be RE-PROVEN. If "
            "it cannot verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-inline-locals",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the `let parts := …` locals are INLINED into the returned
        # concatenation in both container arms, so each arm is a single
        # expression. Same value on every input; the frozen proof closes
        # unchanged.
        "module": _swap(
            _BASE, _I_ALL,
            'def implementation_renderArg : Arg → String\n'
            '  | .leaf s   => s\n'
            '  | .list xs  => "[" ++ String.intercalate ", " (xs.map implementation_renderArg) ++ "]"\n'
            '  | .tuple xs => "(" ++ String.intercalate ", " (xs.map implementation_renderArg) ++ ",)"'),
        "rationale": (
            "inlining the per-arm `parts` local into the returned concatenation "
            "leaves both container arms single expressions computing the "
            "identical string, so the pin still holds and it must verify. Since "
            "the pin's post-image `specRender` is GROUNDED in the input (a "
            "total transparent recursion, not an opaque answer key), this "
            "doubles as the nagini pos-control-via-helpers argument on this "
            "carrier: the cheapest honest impl is the one that does exactly the "
            "spec's own work, and any WRONG delimiter, separator, or recursion "
            "still fails the pin — which the nine rivals below demonstrate. If "
            "it cannot verify => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation has NO precondition hypothesis, so the
    # nagini precondition-admission probe has no binder to attack; the honest
    # analogue is to show the post-image is SATISFIABLE and NON-DEGENERATE at
    # the interesting concrete points. Three live ground `have`s are discharged
    # inside the proof region, alongside the frozen obligation kept verbatim.
    # =====================================================================
    {
        "id": "admiss-shape-instances",
        "kind": "admissibility",
        "expect": "verify",
        # Prepend three ground `have`s to the parenthesised arm of the proof
        # (wholly inside the tactic body): the spec predicate itself holds of a
        # one-child parenthesised node at the trailing-comma rendering, of a
        # one-child bracketed node at the rendering WITHOUT one, and of a
        # two-child parenthesised node with it. Then the frozen tactic body runs
        # verbatim, so the real obligation still discharges.
        "module": _swap(
            _BASE, _P_TUPLE,
            '  | .tuple xs => by\n'
            '      have _shape_tuple1 : problem_spec_renderArg (Arg.tuple [Arg.leaf "1"]) "(1,)" := by\n'
            '        unfold problem_spec_renderArg\n'
            '        simp only [specRender, List.map_cons, List.map_nil, String.intercalate]\n'
            '        decide\n'
            '      have _shape_list1 : problem_spec_renderArg (Arg.list [Arg.leaf "1"]) "[1]" := by\n'
            '        unfold problem_spec_renderArg\n'
            '        simp only [specRender, List.map_cons, List.map_nil, String.intercalate]\n'
            '        decide\n'
            '      have _shape_tuple2 : problem_spec_renderArg (Arg.tuple [Arg.leaf "1", Arg.leaf "2"]) "(1, 2,)" := by\n'
            '        unfold problem_spec_renderArg\n'
            '        simp only [specRender, List.map_cons, List.map_nil, String.intercalate]\n'
            '        decide\n'
            + _P_TUPLE[len('  | .tuple xs => by\n'):]),
        "rationale": (
            "the obligation binds `∀ arg : Arg` with NO precondition hypothesis "
            "(the modeled behaviour is total on the carrier), so nagini's "
            "'a normal input satisfies the precondition' probe has no binder to "
            "attack; the residual admissibility risk is a DEGENERATE post-image. "
            "This discharges three LIVE ground instances of the spec predicate "
            "itself: a one-child parenthesised node is admitted at the rendering "
            "WITH the trailing comma, a one-child bracketed node at the "
            "rendering WITHOUT one, and a two-child parenthesised node with it — "
            "so the post-image is satisfiable AND actually demands the "
            "discriminating behaviour at the shape the failing test observes, "
            "rather than being met by anything. The frozen tactic body is kept "
            "verbatim so the real obligation still discharges; nothing is "
            "assumed and the STATEMENT is byte-identical. Re-aims the nagini "
            "admiss-f2p-witness. If these cannot be established, the spec "
            "rejects a legitimate input shape (PRECOND-TOO-STRONG / "
            "SPEC-UNSATISFIABLE)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # ground `Arg` (the witness elaborates against the rival and FAILS on gold).
    # Each carries the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "rej-prepatch-no-trailing-comma",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: the parenthesised closer is the lone `)` with
        # NO trailing comma. Attacks C-tuple's closer on the WHOLE
        # parenthesised sub-domain.
        "module": _swap(
            _BASE, _I_TUPLE,
            '  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      "(" ++ String.intercalate ", " parts ++ ")"'),
        "refinement": (
            "this is the pre-change behaviour: the parenthesised closer is the "
            "lone closing parenthesis with no trailing comma. Its faithful real "
            "counterpart is the unpatched code, under which a one-element "
            "parenthesised container is emitted without the trailing comma and "
            "therefore re-reads as its bare element rather than as a "
            "one-element container. The failing test pins exactly that shape — "
            "a one-element container must still be a container — so the "
            "counterpart would NOT resolve. It is the precise defect the change "
            "exists to correct, so a verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from C-tuple of the pin `result = specRender arg`: "
            "`specRender` fixes the parenthesised closer to the two characters "
            "',' then ')', so a rival closing with the lone ')' diverges from "
            "the post-image on EVERY parenthesised input. Refuted at a "
            "TWO-child parenthesised node — deliberately not the one-child "
            "point, so this witness and the partial-domain rival's below probe "
            "different arities and each rival is refuted where it actually "
            "diverges. If it verified => SPEC-TOO-WEAK (the spec would admit "
            "the very behaviour the change exists to fix)."
        ),
        "witness": _witness('(Arg.tuple [Arg.leaf "1", Arg.leaf "2"])'),
    },
    {
        "id": "rej-single-drops-comma",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss: correct on every input EXCEPT the one-child
        # parenthesised node, where the closer drops the trailing comma. Agrees
        # with gold on all bracketed nodes, all leaves, and every parenthesised
        # node of arity != 1.
        "module": _swap(
            _BASE, _I_TUPLE,
            '  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      let closer := if xs.length == 1 then ")" else ",)"\n'
            '      "(" ++ String.intercalate ", " parts ++ closer'),
        "refinement": (
            "PARTIAL-DOMAIN: correct on every input EXCEPT the one-element "
            "parenthesised container, where it drops the trailing comma. A "
            "faithful real counterpart of this shape keeps the trailing comma "
            "for containers of two or more elements but special-cases the "
            "one-element container to emit it without one — so that container "
            "re-reads as its bare element and the failing test FAILS, even "
            "though every other container rendering, of either kind and any "
            "other arity, still matches and every currently-passing test still "
            "passes. It does NOT resolve. This is the exact reported regression "
            "sub-domain, which is why a spec that missed it would be weak in "
            "the one place that matters."
        ),
        "rationale": (
            "REJECT from C-tuple of the pin: `specRender` fixes the "
            "parenthesised closer to ',)' at EVERY arity including one, so a "
            "rival that special-cases the one-child node to the lone ')' "
            "diverges from the post-image on exactly that sub-domain. Refuted at "
            "a ONE-child parenthesised node — the input that DISTINGUISHES this "
            "near-miss from rej-prepatch-no-trailing-comma, since at the "
            "two-child point used there this rival AGREES with gold. Its own "
            "point is therefore the sub-domain its refinement claims, not a "
            "borrowed one. If it verified => SPEC-TOO-WEAK on precisely the "
            "regression sub-domain."
        ),
        "witness": _witness('(Arg.tuple [Arg.leaf "1"])'),
    },
    {
        "id": "rej-closer-order",
        "kind": "uniqueness",
        "expect": "reject",
        # SUPPORTING near-miss: the parenthesised closer emits its two
        # characters in the REVERSED order, ')' then ','. Same multiset, wrong
        # sequence.
        "module": _swap(
            _BASE, _I_TUPLE,
            '  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      "(" ++ String.intercalate ", " parts ++ ")," '.rstrip()),
        "refinement": (
            "SUPPORTING near-miss: the parenthesised closer's two characters are "
            "emitted in the reversed order — the closing parenthesis before the "
            "comma. Its faithful real counterpart emits a one-element "
            "parenthesised container with the comma trailing OUTSIDE the "
            "parenthesis, which is not the container literal the failing test "
            "pins (and re-parses differently in the position the emitted source "
            "uses it), so it would NOT resolve. Its value is that it confirms "
            "the pin fixes the ORDER of the closer's characters and not merely "
            "which characters occur."
        ),
        "rationale": (
            "REJECT from C-tuple of the pin: `specRender` fixes the closer as "
            "',' THEN ')', so a rival emitting ')' then ',' diverges from the "
            "post-image on every parenthesised input even though the multiset of "
            "characters matches. Refuted at a parenthesised node NESTED inside a "
            "bracketed node — a depth-2 input distinct from every other rival's, "
            "which additionally shows the wrong closer is observable through an "
            "enclosing container rather than only at the top level. If it "
            "verified => SPEC-TOO-WEAK on the closer's character order."
        ),
        "witness": _witness('(Arg.list [Arg.tuple [Arg.leaf "z"]])'),
    },
    {
        "id": "rej-tuple-as-list",
        "kind": "uniqueness",
        "expect": "reject",
        # The parenthesised arm borrows the BRACKETED arm's delimiters, so a
        # parenthesised node renders as a bracketed one. Attacks C-tuple's
        # opening AND closing delimiter (kind fidelity).
        "module": _swap(
            _BASE, _I_TUPLE,
            '  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      "[" ++ String.intercalate ", " parts ++ "]"'),
        "refinement": (
            "the parenthesised kind borrows the bracketed kind's delimiters. Its "
            "faithful real counterpart emits a parenthesised container as a "
            "bracketed one, so the generated source returns the WRONG container "
            "kind — a mutable sequence where the failing test requires the "
            "immutable one — and the test's equality against a "
            "parenthesised-kind value fails. Currently-passing tests that pin "
            "parenthesised-kind results fail too, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from C-tuple of the pin: `specRender` opens a parenthesised "
            "node with '(' and closes it with ',)', so a rival using the "
            "bracketed pair diverges from the post-image on every parenthesised "
            "input. Refuted at a ONE-child parenthesised node whose leaf text "
            "differs from every other witness's, so the point is distinct even "
            "where the arity is shared. Attacks kind fidelity — a different "
            "failure mode from the closer rivals, which keep the correct opening "
            "delimiter. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('(Arg.tuple [Arg.leaf "a"])'),
    },
    {
        "id": "rej-list-as-tuple",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror rival: the BRACKETED arm borrows the parenthesised
        # delimiters. Correct on every parenthesised node, wrong on every
        # bracketed one — the only rival attacking C-list's delimiters, so the
        # constructor binder is genuinely exercised on that arm.
        "module": _swap(
            _BASE, _I_LIST,
            '  | .list xs  =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      "(" ++ String.intercalate ", " parts ++ ",)"'),
        "refinement": (
            "the bracketed kind borrows the parenthesised kind's delimiters, "
            "including the trailing comma. Its faithful real counterpart emits a "
            "bracketed container as a parenthesised one, so the generated source "
            "returns the immutable container kind where the mutable one is "
            "required; the currently-passing tests that pin bracketed-kind "
            "results (including the nested-container ones) fail, so it does NOT "
            "resolve. Note this rival is CORRECT on the whole parenthesised "
            "sub-domain the failing test exercises — which is exactly why the "
            "spec must pin the bracketed arm too, and why a spec that pinned "
            "only the changed arm would be weak here."
        ),
        "rationale": (
            "REJECT from C-list of the pin: `specRender` opens a bracketed node "
            "with '[' and closes it with ']', so a rival using the parenthesised "
            "pair diverges from the post-image on every bracketed input. This is "
            "the ONLY rival attacking C-list's delimiters, and it is refuted at "
            "a one-child BRACKETED node — the arm of the constructor binder that "
            "no other delimiter rival reaches. Without it, an impl that "
            "mishandled only the unchanged arm would verify and the battery "
            "would never notice. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness('(Arg.list [Arg.leaf "1"])'),
    },
    {
        "id": "rej-separator-no-space",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the SEPARATOR rather than the delimiters: children are joined
        # by a bare comma instead of comma-and-space. Both delimiters, including
        # the trailing comma, are correct — so this isolates the join clause.
        "module": _swap(
            _BASE, _I_TUPLE,
            '  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      "(" ++ String.intercalate "," parts ++ ",)"'),
        "refinement": (
            "the children are joined by a bare comma instead of "
            "comma-and-space. Its faithful real counterpart changes the "
            "separator the container's elements are joined with, so the emitted "
            "source text differs from what the tests that inspect generated "
            "source expect, while the container VALUES still compare equal. That "
            "is why it is shipped as a separator-clause probe rather than as a "
            "primary rival: what it demonstrates is that the pin constrains the "
            "join and not only the delimiters, so an impl free to choose the "
            "separator could not slip through. A rival that verified here would "
            "show the pin leaves the join unconstrained."
        ),
        "rationale": (
            "REJECT from the JOIN sub-clause inside C-tuple: `specRender` fixes "
            "the separator to comma-AND-space, so a rival joining with a bare "
            "comma diverges from the post-image at every arity of two or more, "
            "while keeping BOTH delimiters (including the trailing comma) "
            "correct — which isolates the separator from the delimiter clauses "
            "every other rival attacks. Refuted at a THREE-child parenthesised "
            "node, the highest arity any witness probes, where two separator "
            "positions are wrong at once. If it verified => SPEC-TOO-WEAK on "
            "the join."
        ),
        "witness": _witness(
            '(Arg.tuple [Arg.leaf "a", Arg.leaf "b", Arg.leaf "c"])'),
    },
    {
        "id": "rej-leaf-not-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C-leaf, the arm no nagini case reaches (nagini's carrier
        # receives its elements ALREADY rendered, so the leaf arm does not exist
        # there). A leaf is wrapped in quotes instead of rendered verbatim.
        "module": _swap(
            _BASE, _I_HEAD_LEAF,
            'def implementation_renderArg : Arg → String\n'
            '  | .leaf s   => "\'" ++ s ++ "\'"'),
        "refinement": (
            "a printed leaf is wrapped in quotes instead of being emitted "
            "verbatim. Its faithful real counterpart re-quotes every already-"
            "printed element before splicing it into the container text, so "
            "every emitted element becomes a string literal: the generated "
            "source returns quoted text where the tests require the values "
            "themselves, and both the failing test and a broad set of "
            "currently-passing ones fail. It does NOT resolve. It is included "
            "because this arm has NO nagini counterpart — nagini's carrier "
            "receives its elements already rendered, so nothing there could "
            "have abused the leaf rendering."
        ),
        "rationale": (
            "REJECT from C-leaf of the pin: `specRender` renders a leaf to its "
            "own string VERBATIM, so a rival that decorates it diverges from the "
            "post-image on every leaf — and, by recursion, inside every "
            "container too. Refuted at a BARE LEAF, a depth-0 input no other "
            "witness probes, so the arm is attacked in isolation from any "
            "delimiter or join behaviour. This closes the third of the pin's "
            "three arms; without it C-leaf would be defended by the positives "
            "but attacked by nothing. If it verified => SPEC-TOO-WEAK on leaf "
            "rendering."
        ),
        "witness": _witness('(Arg.leaf "1")'),
    },
    {
        "id": "rej-empty-tuple-no-comma",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN near-miss at the ARITY-0 corner: the parenthesised
        # closer keeps the trailing comma at every arity EXCEPT zero, where it
        # emits the lone ')'. Correct on every other input in the whole carrier,
        # including the one-child point the F2P-shaped rivals are refuted at, so
        # no other witness in this battery reaches it.
        "module": _swap(
            _BASE, _I_TUPLE,
            '  | .tuple xs =>\n'
            '      let parts := xs.map implementation_renderArg\n'
            '      let closer := if xs.isEmpty then ")" else ",)"\n'
            '      "(" ++ String.intercalate ", " parts ++ closer'),
        "refinement": (
            "PARTIAL-DOMAIN at arity zero: the childless parenthesised container "
            "renders without the trailing comma, so it re-reads as an empty "
            "grouping rather than as a container of no elements, while every "
            "container of one or more children — of either kind — still matches "
            "gold exactly. Its faithful real counterpart therefore leaves the "
            "reported one-element behaviour correct and still emits the wrong "
            "text for the childless container, so the tests that pin a "
            "childless container's rendering fail and it does NOT resolve. It is "
            "the mirror of the one-child near-miss: same clause, opposite end of "
            "the arity axis."
        ),
        "rationale": (
            "REJECT from C-tuple of the pin: `specRender` fixes the "
            "parenthesised closer to ',)' at EVERY arity, and arity ZERO is the "
            "one point where that is observable without any child rendering "
            "being involved at all. Refuted at the childless parenthesised node "
            "— an input NO other witness in this battery probes, which is why "
            "the case was added: every shipped rival agrees with gold there, so "
            "the arity axis was silently pinned at >= 1 and an impl special-"
            "casing the empty container would have verified unnoticed. Confirms "
            "the pin's arity coverage is total rather than only covering the "
            "arities the rivals happened to diverge at. If it verified => "
            "SPEC-TOO-WEAK at arity 0."
        ),
        "witness": _witness('(Arg.tuple [])'),
    },
    {
        "id": "rej-nested-not-recursive",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the RECURSION itself, the other axis nagini's flat carrier
        # cannot express: inside a bracketed node, a child that is itself a
        # container is rendered by a non-recursive placeholder instead of by its
        # own arm. Correct whenever every child is a leaf.
        "module": _swap(
            _BASE, _I_LIST,
            '  | .list xs  =>\n'
            '      let parts := xs.map (fun a => match a with | .leaf s => s | _ => "...")\n'
            '      "[" ++ String.intercalate ", " parts ++ "]"'),
        "refinement": (
            "inside a bracketed container, a child that is itself a container is "
            "rendered by a fixed placeholder instead of by the same rendering "
            "applied recursively. Its faithful real counterpart stops recursing "
            "at the first level, so a NESTED container is emitted as a "
            "placeholder rather than as its own source text: the "
            "currently-passing nested-container tests, which pin results for "
            "containers holding containers, fail outright, and any nested "
            "occurrence of the parenthesised kind loses its trailing comma too. "
            "It does NOT resolve. This rival has no nagini counterpart, since "
            "nagini's flat carrier receives elements already rendered and has no "
            "recursion to break."
        ),
        "rationale": (
            "REJECT from the RECURSIVE sub-clause of C-list: `specRender` maps "
            "each child through itself, so a rival that renders a non-leaf child "
            "as a placeholder diverges from the post-image on every input with "
            "nesting depth >= 2, while agreeing with gold on every flat input. "
            "Refuted at a bracketed node holding a parenthesised child, a "
            "DEPTH-2 input where the outer arm's delimiters are correct and only "
            "the inner rendering is wrong — so the recursion is attacked "
            "independently of every delimiter clause. This is the axis nagini's "
            "flat carrier cannot express; without it an impl that handled only "
            "one level would verify. If it verified => SPEC-TOO-WEAK on "
            "nesting."
        ),
        "witness": _witness('(Arg.list [Arg.tuple [Arg.leaf "1"]])'),
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING. The nagini sibling ships 9 SPEC cases (3 soundness,
# 1 admissibility, 5 uniqueness) plus AXIOM_TESTS = []. This battery ships 14
# (4 soundness, 1 admissibility, 9 uniqueness) after the audit added
# pos-closer-concat and rej-empty-tuple-no-comma.
#
# The carriers differ in shape, not in breadth. nagini models a FLAT renderer
# `render_container(elems: PSeq[PSeq[int]], is_paren: bool)` over
# already-rendered elements, proved by an accumulator loop; this bundle models
# the same behaviour RECURSIVELY as `implementation_renderArg : Arg → String`,
# where nagini's `is_paren` flag becomes the choice of constructor and nagini's
# `elems` becomes the node's children. So there is no carrier NARROWING here
# (the one nagini contract maps to the one lean obligation), but there IS a
# carrier WIDENING: the recursive carrier has a leaf arm and a nesting depth
# that nagini's flat one does not, which is where the two extra rivals come
# from. Case count is not the target either way — clause, binder, and point
# coverage is.
#
#   nagini case                        -> here                            disposition
#   ------------------------------------------------------------------------------------
#   pos-control-branch-reorder         -> pos-arm-reorder                 PORTED
#   pos-control-concat-delim           -> pos-delim-pair-local            RE-EXPRESSED
#   pos-control-via-helpers            -> pos-inline-locals               RE-EXPRESSED
#   admiss-f2p-witness                 -> admiss-shape-instances          RE-AIMED
#   rej-prepatch-no-trailing-comma     -> rej-prepatch-no-trailing-comma   PORTED
#   rej-paren-as-bracket               -> rej-tuple-as-list                PORTED
#   rej-list-as-paren                  -> rej-list-as-tuple                PORTED
#   rej-single-drops-comma-partial-... -> rej-single-drops-comma           PORTED
#   rej-delim-order-supporting         -> rej-closer-order                 PORTED
#   (no counterpart — flat carrier)    -> rej-separator-no-space           NEW (carrier)
#   (no counterpart — flat carrier)    -> rej-leaf-not-verbatim            NEW (carrier)
#   (no counterpart — flat carrier)    -> rej-nested-not-recursive         NEW (carrier)
#   AXIOM_TESTS ([])                   -> (none)                          already empty
#
# PORTED (5 uniqueness + 1 soundness) — each nagini rival's ARGUMENT carries over
#   unchanged; only the mechanics are re-expressed. nagini's flat delimiter
#   selection (`if is_paren: left, right = …`) becomes the constructor arm, so
#   "the paren kind's closer loses its trailing comma" becomes "the `.tuple`
#   arm's closer loses its trailing comma", and so on. The nagini fold skeleton
#   (`_FOLD_SKELETON`, the `joined` invariant plus its per-step unfold asserts)
#   has NO counterpart and is deliberately not carried: gold here is a
#   structural recursion whose proof is `List.map_congr_left` over the frozen
#   arms, so there is no loop invariant a variant could accidentally drop. That
#   removes nagini's failure mode #2/#3 (a positive that fails for a PROOF
#   reason) by construction rather than by discipline.
# RE-EXPRESSED (pos-control-concat-delim -> pos-delim-pair-local): the nagini
#   control rebuilds the closing delimiter by a different constructor call of the
#   same sequence value. Lean string literals are not built from character
#   constructors, so the equivalent "same value, different construction" reshape
#   here binds the delimiter PAIR as a local tuple and projects it.
# RE-EXPRESSED (pos-control-via-helpers -> pos-inline-locals): the nagini control
#   assembles the result through the same pure delimiter helpers the spec's
#   post-image uses. Here the post-image is one recursive `def` rather than a
#   pair of helpers, and an impl that literally called it would be a different
#   declaration; the faithful counterpart is the impl that does exactly the
#   post-image's own work inline. The nagini argument it carries — the pin is
#   GROUNDED, so the cheapest honest impl verifies and no wrong echo can — is
#   discharged jointly with the nine rivals, which demonstrate that every wrong
#   delimiter, separator, and recursion still fails the pin.
# RE-AIMED (admiss-f2p-witness -> admiss-shape-instances): nagini injects an
#   in-region assert pinning the one-element parenthesised shape. The
#   precondition half has no counterpart (the obligation binds `∀ arg : Arg`
#   unguarded — no `require`, no heap permission on a referentially transparent
#   carrier), so this is re-aimed at the residual risk that survives: a
#   degenerate post-image. Strengthened to three ground instances of the spec
#   predicate — one-child parenthesised WITH the trailing comma, one-child
#   bracketed WITHOUT, two-child parenthesised WITH — so the pin is shown
#   satisfiable and non-degenerate at the shapes that matter.
# NEW, from the carrier widening (3 uniqueness): rej-leaf-not-verbatim attacks
#   the leaf arm and rej-nested-not-recursive attacks the recursion — neither
#   exists in nagini, whose elements arrive already rendered. rej-separator-no-
#   space isolates the join clause, which nagini's spelled-out `joined` fold
#   covers implicitly but no nagini rival attacks on its own. These are not
#   parity padding: each closes a clause of THIS pin that no ported rival
#   reaches, and each was verified to discriminate.
# FRAME-MUTATION: VACUOUS, and already vacuous upstream. The nagini defended
#   surface has no heap input, no fractional permission, and no `list_pred` — its
#   own docstring declares the class inapplicable — so there is nothing to port.
#   On this carrier it is doubly vacuous: Lean is referentially transparent, the
#   input is an immutable value, there is no aliasing and no permission system.
#   No substitute is fabricated.
# DIVERGENCE: VACUOUS here, but the earlier reason ("a diverging implementation
#   cannot be written at all") was too strong and is corrected. The nagini sibling
#   carries no `diverge-*` / `nonterm-*` / `weak-diverge` case, so nothing is
#   dropped. On the expressibility question, two shapes were actually BUILT:
#     * a self-recursive tuple arm with no decreasing measure. Lean refuses the
#       DEFINITION (exit 1, `fail to show termination for implementation_renderArg`
#       / `failed to infer structural recursion`), so the file never elaborates.
#       This bundle carries no `loom.semantics.termination` line at all — it is a
#       plain Lean `def`, and totality is enforced by the definition checker
#       rather than by a discharged obligation, so the "total" disposition applies:
#       a measure-less loop is genuinely rejected.
#     * the same arm marked `partial`, which DOES elaborate. This is the shape
#       worth being precise about: it is rejected too (exit 1), but for the frozen
#       proof's sake, not the spec's — and a witness cannot rescue it, because
#       `partial def` is compiled as an opaque constant, so `decide` gets stuck
#       (measured: `reduction got stuck at the Decidable instance
#       (implementation_renderArg (Arg.tuple [Arg.leaf "1"])).data.hasDecEq …`,
#       the `witness-undecided` shape). So a `partial` rival is not shippable as a
#       reject case on this carrier — not because it is admitted, but because no
#       witness can discriminate it.
#   The class is therefore vacuous in the shippable sense (nothing to add), and
#   this is NOT the known spec hole of the corpus-wide termination-semantics finding, which is a
#   velvet-under-`termination "partial"` phenomenon.
# AXIOM_TESTS: already empty in the nagini sibling, and empty here for the same
#   reason — the only unchanged callee is refined AWAY (type-only R, never called
#   in the impl; mapping.md), so the bundle declares no `opaque` and consumes no
#   `axiom`. Nothing to drop; the axiom lane belongs to G-AX and this gate
#   ignores it.
# NOTHING DROPPED FOR PROOF DIFFICULTY — and the closer-concat reshape is now
#   SHIPPED rather than discarded. An earlier revision of this file recorded it as
#   "built and discarded on the merits", on the argument that the retunes closing
#   its associativity goal are all `simp [String.append_assoc]` shapes whose value
#   is a string-append lemma rather than anything about this spec, and that
#   pos-delim-pair-local carries the same argument without the noise. Re-measured,
#   both halves of that were wrong:
#     * the goal closes with a bare `rfl` (exit 0), no append lemma needed, so
#       there is no noise to avoid; and
#     * the three original positives are ALL closed by the frozen tactic body
#       BYTE-VERBATIM (measured: proof region identical to the frozen file in
#       pos-arm-reorder, pos-delim-pair-local, pos-inline-locals). That means each
#       is definitionally equal to the frozen impl, so the frozen script never had
#       to adapt and none of them probes whether the obligation is over-fit to the
#       frozen impl's PROOF shape — only to its surface syntax. The reshape whose
#       residual goal the frozen body leaves OPEN is precisely the one carrying
#       the SPEC-TOO-STRONG information the other three cannot, which is the
#       opposite of a duplicate.
#   It ships as `pos-closer-concat`. Measured both ways: frozen body verbatim =>
#   exit 1 (`unsolved goals … ("," ++ ")") = … ",)"`); frozen body plus one `rfl`
#   => exit 0.
#
# TWO CORRECT RESHAPES REMAIN UNLANDED, and neither is a spec hole. Both are
#   reported as `uncertain` rather than claimed:
#     * a `where`-bound `wrap l r ps` helper assembling both containers. The
#       frozen body fails on it (the helper is not unfolded), and adding
#       `implementation_renderArg.wrap` to the existing `simp only` list closes it
#       (exit 0) — so it is landable, and is omitted only as a duplicate of
#       pos-closer-concat's "reproof for a new shape" argument, not as a
#       limitation.
#     * an arity-branching tuple arm (`match xs with | [] => … | _ :: _ => …`)
#       whose recursion is on the ORIGINAL binder. Lean cannot infer structural
#       recursion through the re-scrutinised binder, and neither the default
#       measure nor `termination_by sizeOf a` + `decreasing_by simp_wf; omega`
#       discharged it (exit 1, `omega could not prove the goal`). That is a
#       TERMINATION-inference limit of the reshape, NOT the spec rejecting a
#       correct impl: the spec's pin is never reached. Recorded as uncertain.
#
# CLAUSE / BINDER / POINT COVERAGE. The one obligation `correct_renderArg` is
#   DEFENDED by five expect="verify" cases (four soundness reshapes, each
#   exercising all three arms, plus the admissibility case) and ATTACKED by nine
#   expect="reject" rivals. The pin `result = specRender arg` decomposes into
#   three constructor arms, and every one is attacked: C-leaf by
#   rej-leaf-not-verbatim; C-list by rej-list-as-tuple (delimiters) and
#   rej-nested-not-recursive (the recursion); C-tuple by rej-prepatch-no-
#   trailing-comma and rej-single-drops-comma (the trailing comma, globally and
#   on the one-child sub-domain), rej-closer-order (character order),
#   rej-tuple-as-list (kind fidelity), and rej-separator-no-space (the join).
#   The sole spec binder `arg : Arg` is varied along all three of its axes across
#   eight DISTINCT witness points (pts=8): `Arg.leaf "1"`;
#   `Arg.tuple [leaf "1"]`; `Arg.tuple [leaf "a"]`;
#   `Arg.tuple [leaf "1", leaf "2"]`; `Arg.tuple [leaf "a", leaf "b", leaf "c"]`;
#   `Arg.list [leaf "1"]`; `Arg.list [tuple [leaf "1"]]`;
#   `Arg.list [tuple [leaf "z"]]` — so the constructor ranges over all three,
#   the arity over 0/1/2/3, and the nesting depth over 0/1/2. No axis is held
#   fixed by every witness, and the near-miss rival is refuted at the one-child
#   point that distinguishes it from the global one rather than sharing that
#   rival's two-child point.
#
# WITNESS MECHANICS: all nine witnesses use the same shape — state
#   `¬ problem_spec_renderArg <arg> (implementation_renderArg <arg>)` at a ground
#   `Arg`, `unfold` the predicate, `simp only` with the intercalate + `List.map`
#   lemmas to normalise both sides to ground string literals, then `decide`.
#   `decide` ALONE does not work here and the detour is measured, not guessed:
#   the carrier is `String`, so reducing the `Decidable` instance gets stuck at
#   `String.decEq` on the un-normalised concatenation, and plain `simp` /
#   `norm_num` leave a goal over the unreduced `String.intercalate.go`
#   accumulator. Each witness binds NOTHING in its head (all inputs are ground
#   literals), so there are no hypotheses whose consistency could be in question
#   and the gate's consistency probe is not even triggered. No banned token. All
#   eight were checked out of band with scripts/lean_verify.sh: each ELABORATES
#   against its own rival (exit 0) and FAILS on the frozen solution (exit 1,
#   `decide proved that the proposition ¬True is false` — i.e. gold satisfies the
#   pin at that input), so each is a real discriminator and not a tautology.
AXIOM_TESTS = []
