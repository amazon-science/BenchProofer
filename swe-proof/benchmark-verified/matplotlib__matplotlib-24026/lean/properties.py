"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24026 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_stackplotColors`` STATEMENT
stays byte-identical). ``expect="verify"`` passes iff (in scope AND the file
elaborates with every obligation closed); ``expect="reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total operation over a container carrier)
---------------------------------------------------------------
A single modeled function assigns colors to ``n`` stacked regions from a
non-empty palette by walking the palette in order and wrapping at its size:

  stackplotColors (colors : List String) (n : Nat) : Except String (List String)
    result = Except.ok ((List.range n).map (fun i => nthColor colors i))

where ``nthColor colors i = colors[i % colors.length]``. The single top-level
postcondition equation packs three INDEPENDENT observable requirements, each of
which some rival attacks:

  (C1) SUCCESS — ``result`` is ``Except.ok _``, never an error. This is exactly
       what the issue + F2P demand: the operation used to reject a palette of
       cycle-reference tokens and now must accept every entry verbatim.
  (C2) LENGTH — the result is the ``n``-long list (``(List.range n).map …`` has
       length ``n``): exactly one color per region.
  (C3) ELEMENT-WISE — region ``i`` gets ``nthColor colors i``: the cyclic
       reading, wrapping at the palette size, indexed from region 0.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models one heap procedure over a mutable Axes object under
fractional permissions. Two of its seven SPEC cases are stated at the PERMISSION
level, which this referentially-transparent carrier does not have. Audit note:
the permission MECHANIC is genuinely inexpressible here, but that does not make
both cases port to nothing — one of them has a value-level shadow that IS
expressible, and it is now carried (``reject-palette-grown``). The ledger:

  * FRAME-MUTATION on ``axes.cycle`` (nagini "frame-mut-axes-cycle") — the
    permission mechanic is INEXPRESSIBLE. Lean has no aliasing and no fractional
    permission: there is no shared cycle object to overwrite and no permission to
    be insufficient, and the modeled carrier has no ``axes`` binder at all. No
    substitute rival is fabricated for the permission mechanic itself. Its
    value-level residue, however, is NOT merely (C1)+(C3)-as-already-attacked, as
    this note first claimed: the nagini rival routes the palette through a
    validator that rejects entries of a particular spelling, so its residue is a
    CONTENT-CONDITIONAL failure, and the two C1 rivals present at the time both
    keyed on call shape rather than on palette content. That residue is now
    carried as ``reject-content-conditional-error``, which is the only case whose
    rival agrees with the frozen impl on ordinary palettes and diverges only on
    what the entries spell.
  * FRAME-MUTATION on ``colors`` (nagini "frame-mut-colors") — the permission
    mechanic is INEXPRESSIBLE (an input ``List String`` cannot be mutated in
    place, so there is no read-only frame to violate). Its VALUE-LEVEL SHADOW is
    expressible and was initially, wrongly, dropped with it: an impl that
    locally extends the palette before walking it computes the wrap at the wrong
    modulus, which the spec's (C3) does forbid. That is now
    ``reject-palette-grown``, and it probes a clause direction no other rival
    reaches — every other (C3) rival perturbs the INDEX ``i`` while holding the
    palette fixed, so none of them tests that the modulus is ``colors.length``
    and not something else.

The nagini positive control (inline the per-layer color, reorder the trailing
discharge steps) and admissibility probe port directly. The nagini partial-domain
rivals port to (C3): the off-by-one cyclic index becomes ``reject-offbyone`` and
the first-layer-only divergence becomes ``reject-first-layer``. The nagini
wrong-length rival ("uniq-short-by-one") ports to (C2) as ``reject-short-by-one``.
The nagini pre-patch failure mode (raise a ValueError instead of coloring) ports
to (C1) as ``reject-error-return`` — the value-level analogue of the reported bug.

BINDER COVERAGE. The spec predicate's input binders are ``colors`` and ``n``.
The six reject witnesses probe SIX distinct input points, varying BOTH binders
rather than sitting at one point (which would say nothing about the spec's
dependence on either):

  * ``reject-error-return``  — colors ``["a"]``,               n ``1``.
  * ``reject-offbyone``      — colors ``["a","b"]``,           n ``2``.
  * ``reject-first-layer``   — colors ``["x","y","z"]``,       n ``3``.
  * ``reject-short-by-one``  — colors ``["p","q"]``,           n ``4``.
  * ``reject-palette-grown`` — colors ``["a","b","c"]``,       n ``5``.
  * ``reject-zero-regions``  — colors ``["c0","c1","c2","c3"]``, n ``0``.
  * ``reject-content-conditional-error`` — colors ``["C0","C1","C2"]``, n ``3``.

``n`` takes six distinct values (0,1,2,3,4,5) and ``colors`` seven distinct
contents, so pts=7 — the battery demonstrates the spec's dependence on both
binders rather than refuting every rival at a single point. The variation is
MEANINGFUL, not two spellings of one point: each witness point is chosen where
its own rival's output differs from the spec's, and ``n=5`` over a 3-palette /
``n=4`` over a 2-palette additionally sit strictly PAST the first wrap, which no
``n <= palette length`` point exercises. ``n = 0`` is the lower domain boundary:
the frozen hypothesis constrains only ``colors ≠ []``, so ``n = 0`` is IN the
spec's domain and the spec demands ``Except.ok []`` there. The last point varies
the palette's CONTENT rather than its length or the region count: it is the only
witness whose rival is separated from the frozen impl by what the entries SPELL,
which is the dimension the "accepted verbatim, no further validation" clause of
the frozen docstring actually lives on.

WHERE THE HYPOTHESIS SITS (audited, not asserted). The frozen obligation assumes
only ``colors ≠ []``, and that hypothesis is load-bearing exactly there and
nowhere else: an impl that returns ``Except.error`` when the palette is EMPTY and
is otherwise the frozen loop VERIFIES (checked by build), because the hypothesis
excludes the only input where it differs. That is in-domain behavior, not a spec
hole — but it is why no rival is stated at ``colors = []``: such a rival cannot be
refuted, and a case built on one would be vacuous rather than adversarial.

THE DIVERGENCE CLASS is shippable-as-rejected and needs no case of its own. This
carrier has no ``loom.semantics.termination`` setting (no ``set_option`` at all in
the frozen file): Lean's own elaborator demands a termination argument for every
``def``, so a rival whose recursion carries no decreasing measure never reaches
the spec obligation — measured, it fails at ``fail to show termination for
implementation_stackplotColors``, i.e. before any postcondition is consulted. A
``partial def`` rival gets past that but then makes its own impl irreducible, so
its witness cannot be stated (``Tactic `unfold` failed to unfold
implementation_stackplotColors``) and the rejection would attribute nothing to the
spec. The class is therefore inexpressible as an ATTRIBUTABLE reject case here,
and it is a carrier property rather than a hole in this spec.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen closing proof is tuned to the frozen
``Id.run do`` loop form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS ``problem_spec_stackplotColors`` at one concrete input, discharged by
``simp [nthColor]`` (plus ``decide`` where the residual list clash needs it).
Each was checked by real builds to hold of its rival AND to FAIL on the frozen
solution (so it discriminates rather than asserting a tautology). Every witness
names only spec-shared symbols (``problem_spec_stackplotColors``,
``implementation_stackplotColors``, ``nthColor``), so its failure on gold is a
genuine "the spec is satisfied here" verdict, not an unknown-identifier
compile error.

AXIOM lane: EMPTY. The cycling behavior is modeled concretely (modular indexing
into the palette); ``Solution.lean`` declares no ``opaque`` callee and no
consumed axiom, so there is no axiom-soundness obligation for this gate. (The
nagini sibling's AXIOM_TESTS probe the deep model ``cyc_prefix ==
itertools.cycle`` — that A-reference lane belongs to G-AX, not G-PBT, and is
dropped here per the porting map.)
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24026"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The frozen impl def (the `Id.run do` accumulator loop) and its individual
# lines, plus the frozen `correct_stackplotColors` tactic body — so every
# replacement lands entirely inside the region it edits.
_IMPL_DEF = (
    "def implementation_stackplotColors\n"
    "    (colors : List String) (n : Nat) : Except String (List String) := Id.run do\n"
    "  let mut r : List String := []\n"
    "  for i in [0:n] do\n"
    "    r := r ++ [nthColor colors i]\n"
    "  return Except.ok r"
)
_LOOP_BODY = "    r := r ++ [nthColor colors i]\n"
_LOOP_GUARD = "  for i in [0:n] do"
_RET_OK = "  return Except.ok r"

_CORRECT_BODY = (
    "  intro colors n _\n"
    "  unfold problem_spec_stackplotColors\n"
    "  have h : implementation_stackplotColors colors n\n"
    "      = Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) []) := by\n"
    "    unfold implementation_stackplotColors\n"
    "    simp [List.range_eq_range']\n"
    "  rw [h, foldl_append_eq_map, List.nil_append]"
)

assert _IMPL_DEF in _BASE, "impl anchor drift: stackplotColors body not verbatim"
assert _CORRECT_BODY in _BASE, "proof anchor drift: correct_stackplotColors body not verbatim"


def _witness(colors, n, extra=""):
    """A refutation `example` stated directly against the spec predicate at a
    concrete (colors, n). `simp [nthColor]` reduces both the range-map RHS and
    the rival's loop to concrete list literals; `extra` supplies the trailing
    `decide` when a residual literal clash remains (`all_goals decide` where
    `simp` closes the rival outright but still leaves gold a goal, so the same
    snippet must work on both sides). Names only spec-shared symbols so failure
    on gold is a genuine spec-satisfied verdict — and on this carrier that is
    verified, not assumed: gold's failure is `decide` REFUTING the concrete
    negation (`proved that the proposition ¬... is false`), and flipping the
    witness's claim flips gold's exit code, so the gold-side build tracks what is
    claimed rather than failing for a fixed structural reason."""
    tail = ("\n" + extra) if extra else ""
    return (
        "example : ¬ problem_spec_stackplotColors\n"
        "    (" + colors + ") (" + n + ")\n"
        "    (implementation_stackplotColors\n"
        "      (" + colors + ") (" + n + ")) := by\n"
        "  unfold problem_spec_stackplotColors implementation_stackplotColors\n"
        "  simp [nthColor]" + tail + "\n"
    )


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls that
# MUST verify. If a faithful correct implementation of the modeled behavior
# cannot satisfy the frozen obligation, the postcondition is SPEC-TOO-STRONG.
# Each keeps the `theorem correct_stackplotColors` STATEMENT byte-identical and
# adds no axiom, no `sorry`, and no lemma beyond the frozen set (the frozen
# `foldl_append_eq_map` is retained; nothing new is introduced).
# ===========================================================================

# (1) Collapse the accumulator `Id.run do` loop into the functional map the spec
#     itself names, returned directly. Same value on every input. The proof
#     reduces to `rfl` (the impl IS the spec's RHS), so the frozen loop-vs-fold
#     lemma is no longer consulted but stays present as a frozen declaration.
_POS_MAP = _swap(
    _swap(
        _BASE, _IMPL_DEF,
        "def implementation_stackplotColors\n"
        "    (colors : List String) (n : Nat) : Except String (List String) :=\n"
        "  Except.ok ((List.range n).map (fun i => nthColor colors i))",
    ),
    _CORRECT_BODY,
    "  intro colors n _\n"
    "  unfold problem_spec_stackplotColors implementation_stackplotColors\n"
    "  rfl",
)

# (2) Keep the fold shape but drop the mutable `do`-notation: return the explicit
#     left fold over `List.range n`. Same value; the proof is the frozen
#     loop-vs-fold lemma applied directly (no `have h` bridge needed).
_POS_FOLD = _swap(
    _swap(
        _BASE, _IMPL_DEF,
        "def implementation_stackplotColors\n"
        "    (colors : List String) (n : Nat) : Except String (List String) :=\n"
        "  Except.ok ((List.range n).foldl (fun r i => r ++ [nthColor colors i]) [])",
    ),
    _CORRECT_BODY,
    "  intro colors n _\n"
    "  unfold problem_spec_stackplotColors implementation_stackplotColors\n"
    "  rw [foldl_append_eq_map, List.nil_append]",
)

# ===========================================================================
# ADMISSIBILITY — the frozen theorem's only hypothesis is `colors ≠ []`, so the
# nagini precondition-admission probe has no numeric binder to attack. The honest
# analogue discharges the spec predicate at a ground, F2P-shaped input (the exact
# 3-color / 3-region case the F2P exercises) as a `have` INSIDE the frozen proof
# body, then closes the frozen obligation verbatim. If that ground instance could
# not be discharged, the modeled operation would be unsatisfiable at the very
# shape the F2P uses (the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no
# new declaration, byte-identical theorem statement, the frozen proof retained
# after the `have`.
# ===========================================================================
_ADMISS = _swap(
    _BASE, _CORRECT_BODY,
    "  have _ground : problem_spec_stackplotColors [\"C0\", \"C1\", \"C2\"] 3\n"
    "      (implementation_stackplotColors [\"C0\", \"C1\", \"C2\"] 3) := by\n"
    "    unfold problem_spec_stackplotColors implementation_stackplotColors\n"
    "    simp [nthColor]\n"
    "    decide\n"
    + _CORRECT_BODY,
)


SPEC_TESTS = [
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": (
            "Structurally-different CORRECT impl: the accumulator loop is "
            "collapsed into the functional map over `List.range n` (no mutable "
            "local, no `Id.run do`), computing the identical result on every "
            "input, so it must satisfy the single postcondition equation "
            "`result = Except.ok ((List.range n).map (fun i => nthColor colors "
            "i))`. Defends all three packed clauses (C1 success, C2 length-n, "
            "C3 element-wise cyclic). If it could not verify the postcondition "
            "would be SPEC-TOO-STRONG. Proof: the impl reduces to the spec RHS, "
            "closed by `rfl`; no lemma/axiom/sorry added (the frozen "
            "loop-vs-fold lemma is retained but unused)."
        ),
    },
    {
        "id": "pos-explicit-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLD,
        "rationale": (
            "A second correct reshape: keep the left-fold that accumulates by "
            "appending each region's color, but express it as an explicit "
            "`(List.range n).foldl … []` rather than the mutable `do` loop. Same "
            "value on every input; the frozen `foldl_append_eq_map` lemma "
            "discharges it directly (`rw [foldl_append_eq_map, List.nil_append]`) "
            "with the byte-identical theorem statement and no new assumption. "
            "Confirms the obligation is not tied to one syntactic impl shape."
        ),
    },
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The obligation is discharged at a ground F2P-shaped input (the "
            "3-color palette over 3 regions the F2P exercises) by evaluating the "
            "spec predicate concretely, then the frozen obligation is closed "
            "verbatim. Verifies (else the modeled operation is unsatisfiable at "
            "the normal input — the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the ground instance is a `have` inside the existing tactic "
            "body and the theorem statement is byte-identical."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete input, checked to hold of the rival
    # and FAIL on gold. The seven rivals attack the three packed clauses C1..C3:
    # C1 three times (an outright error return; an error only at the n=0
    # boundary; and an error conditioned on what the palette ENTRIES SPELL, the
    # only one of the three not keyed on call shape), C2 once (short by one
    # region), and C3 three times along INDEPENDENT directions — a globally
    # shifted index, a wrong index at region 0 only, and a wrong MODULUS with the
    # index reading left intact.
    # =====================================================================
    {
        "id": "reject-error-return",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C1 (success): returns the error result instead of the colored
        # list — the value-level analogue of the reported pre-patch behavior,
        # where the palette was rejected instead of accepted verbatim.
        "module": _swap(
            _BASE, _RET_OK,
            "  return Except.error \"Cannot put cycle reference in prop_cycler\"",
        ),
        "refinement": (
            "Rejecting the palette instead of accepting it reproduces exactly the "
            "pre-existing failure mode the issue reports and the F2P was added to "
            "exclude: the F2P supplies a palette of cycle-reference tokens and "
            "expects the plot to be produced (the render comparison then runs); "
            "an operation that errors out on that palette raises before any plot "
            "is drawn, so the F2P still fails — a faithful real patch that kept "
            "rejecting the palette does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C1 of `result = Except.ok (...)`: the rival "
            "returns `Except.error _`, which is never `Except.ok _`, so the "
            "postcondition equation fails outright regardless of colors/n. "
            "Witnessed at the minimal palette colors=[\"a\"], n=1."
        ),
        "witness": _witness("[\"a\"]", "1"),
    },
    {
        "id": "reject-offbyone",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C3 (element-wise): colors region i with nthColor colors (i+1) —
        # the whole cyclic reading is shifted one step, as if an extra draw was
        # pulled from the palette before the first region.
        "module": _swap(
            _BASE, _LOOP_BODY, "    r := r ++ [nthColor colors (i+1)]\n",
        ),
        "refinement": (
            "Coloring region i with the (i+1)-th palette entry seeds the cyclic "
            "reading one step ahead (a stray pull from the palette before the "
            "first region). For the F2P palette [C0,C1,C2] over 3 regions it "
            "paints C1,C2,C0 instead of C0,C1,C2 — every region gets the wrong "
            "color and the render comparison against the C0,C1,C2 reference "
            "FAILS. A real patch with this off-by-one does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C3: at colors=[\"a\",\"b\"], n=2 the rival yields "
            "[nthColor [\"a\",\"b\"] 1, nthColor [\"a\",\"b\"] 2] = [\"b\",\"a\"] "
            "whereas the spec demands [\"a\",\"b\"], so the equation fails at "
            "region 0. Success (C1) and length (C2) are preserved, isolating the "
            "element-wise clause."
        ),
        "witness": _witness("[\"a\",\"b\"]", "2", "  decide"),
    },
    {
        "id": "reject-first-layer",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C3 at region 0 only: correct on regions 1..n-1 but colors
        # region 0 with nthColor colors 1 (a plausible mis-edit of the dedicated
        # first-region color source, which is split from the loop in the fix).
        "module": _swap(
            _BASE, _LOOP_BODY,
            "    if i == 0 then\n"
            "      r := r ++ [nthColor colors 1]\n"
            "    else\n"
            "      r := r ++ [nthColor colors i]\n",
        ),
        "refinement": (
            "The real code sources the first region's color from a dedicated draw "
            "and the remaining regions from a loop; a faithful mis-edit that gives "
            "region 0 the WRONG cyclic entry (here the second palette color) is "
            "correct on every later region but paints region 0 wrong. For the F2P "
            "3-color case it renders C1,C1,C2 — wrong first region, image mismatch "
            "— so such a patch does NOT resolve. This is a NEAR-MISS of the "
            "off-by-one rival (they agree except at region 0), so it gets its own "
            "witness at a point where only region 0 differs."
        ),
        "rationale": (
            "REJECT from clause C3 at region 0: at colors=[\"x\",\"y\",\"z\"], n=3 "
            "the rival yields [\"y\",\"y\",\"z\"] whereas the spec demands "
            "[\"x\",\"y\",\"z\"], failing at region 0 while regions 1,2 match. "
            "Success and length are preserved, isolating the region-0 element."
        ),
        "witness": _witness("[\"x\",\"y\",\"z\"]", "3", "  decide"),
    },
    {
        "id": "reject-short-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C2 (length): stops the loop at n-1, returning n-1 colors — one
        # region left uncolored.
        "module": _swap(
            _BASE, _LOOP_GUARD, "  for i in [0:n-1] do",
        ),
        "refinement": (
            "Stopping one region short returns n-1 colors: a real patch that "
            "under-counted the stacked regions (e.g. forgot the dedicated first "
            "region, or looped over one fewer series) leaves the last region "
            "uncolored — a visibly different image — so the render comparison "
            "FAILS and the patch does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause C2 (length = n): at colors=[\"p\",\"q\"], n=4 the "
            "rival returns a length-3 list whereas the spec demands the length-4 "
            "`(List.range 4).map …`, so the equation fails on length (and hence "
            "on the missing region's element). Success (C1) is preserved and the "
            "colors present are the correct cyclic entries, isolating length."
        ),
        "witness": _witness("[\"p\",\"q\"]", "4", "  decide"),
    },
    {
        "id": "reject-palette-grown",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C3 from the PALETTE side rather than the index side: the impl
        # locally extends the palette with a repeat of its first entry before
        # walking it, so the wrap happens at the wrong modulus. Every other C3
        # rival perturbs the index `i` while holding the palette fixed; this one
        # holds the index reading fixed and perturbs what is being indexed, so it
        # is the only rival that pins the modulus to `colors.length` itself.
        # (This is the value-level shadow of the nagini read-only-frame rival on
        # `colors`, which the permission-level reading alone would have dropped.)
        "module": _swap(
            _BASE, _IMPL_DEF,
            "def implementation_stackplotColors\n"
            "    (colors : List String) (n : Nat) : Except String (List String) := Id.run do\n"
            "  let colors := colors ++ [colors[0]!]\n"
            "  let mut r : List String := []\n"
            "  for i in [0:n] do\n"
            "    r := r ++ [nthColor colors i]\n"
            "  return Except.ok r",
        ),
        "refinement": (
            "A patch that appended to the caller-supplied palette before walking "
            "it (padding it, or re-adding an entry) lengthens the cycle: the "
            "palette then repeats every k+1 regions instead of every k. It is "
            "INDISTINGUISHABLE from correct on any run that never wraps, which is "
            "why it is plausible, but the moment there are more regions than "
            "palette entries the colors after the first wrap are wrong — so a "
            "faithful real patch carrying it does NOT resolve a case that wraps, "
            "and it also mutates a sequence the caller still owns."
        ),
        "rationale": (
            "REJECT from clause C3 via the MODULUS rather than the index: at "
            "colors=[\"a\",\"b\",\"c\"], n=5 the rival cycles with period 4 and "
            "yields [\"a\",\"b\",\"c\",\"a\",\"a\"] whereas the spec demands "
            "period 3, [\"a\",\"b\",\"c\",\"a\",\"b\"], so the equation fails at "
            "region 4. Success (C1) and length (C2) are preserved. The witness "
            "point sits strictly PAST the first wrap; note that at any n <= 3 "
            "this rival AGREES with the spec, so a witness there would not "
            "discriminate (verified: the n=2 attempt failed on the rival)."
        ),
        "witness": _witness("[\"a\",\"b\",\"c\"]", "5", "  decide"),
    },
    {
        "id": "reject-content-conditional-error",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C1 CONTENT-DEPENDENTLY, which no other rival does. Every other
        # C1 rival errors on a condition read off the SHAPE of the call — always
        # (`reject-error-return`) or at a region count (`reject-zero-regions`) —
        # so each is refutable at an arbitrary palette and none of them attests
        # that the spec forbids screening the palette's own ENTRIES. This rival
        # walks the palette correctly whenever every entry has an unremarkable
        # spelling and errors only when some entry matches a reserved two-character
        # shape, so it agrees with the frozen impl on most palettes and is
        # separated from it only by an input whose CONTENT triggers the screen.
        # That is the "accepted verbatim, with no further validation that could
        # reject otherwise-meaningful color tokens" sentence of the frozen
        # docstring — a clause the battery asserted in prose but never probed.
        "module": _swap(
            _BASE, _IMPL_DEF,
            "def implementation_stackplotColors\n"
            "    (colors : List String) (n : Nat) : Except String (List String) := Id.run do\n"
            "  if colors.any (fun c => match c.toList with\n"
            "                          | ['C', d] => d.isDigit\n"
            "                          | _ => false) then\n"
            "    return Except.error \"unsupported palette entry\"\n"
            "  let mut r : List String := []\n"
            "  for i in [0:n] do\n"
            "    r := r ++ [nthColor colors i]\n"
            "  return Except.ok r",
        ),
        "refinement": (
            "A patch that kept screening the caller's palette and rejected any "
            "entry of a reserved spelling still refuses exactly the palettes the "
            "issue is about, while looking correct on every palette that happens "
            "to avoid that spelling. The F2P supplies a palette whose entries all "
            "have that reserved shape and expects the plot to be produced, so this "
            "impl raises before anything is drawn and the render comparison never "
            "runs — it does NOT resolve. It is a strictly subtler near-miss than "
            "an unconditional failure: a battery that only ever checks palettes of "
            "ordinary tokens cannot tell it from the fixed behavior at all."
        ),
        "rationale": (
            "REJECT from clause C1, at a point selected by palette CONTENT rather "
            "than by call shape: at colors=[\"C0\",\"C1\",\"C2\"], n=3 the rival "
            "returns `Except.error _` while the spec demands `Except.ok "
            "[\"C0\",\"C1\",\"C2\"]`. Verified to AGREE with the frozen impl at "
            "colors=[\"a\",\"b\"], n=2 (the witness there fails on the rival), so "
            "the rejection is attributable to the content screen alone and not to "
            "any length or index difference — C2 and C3 are preserved on every "
            "palette this impl accepts."
        ),
        "witness": _witness("[\"C0\",\"C1\",\"C2\"]", "3", "  all_goals decide"),
    },
    {
        "id": "reject-zero-regions",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C1 at the LOWER DOMAIN BOUNDARY. The frozen hypothesis
        # constrains only `colors ≠ []`, so n = 0 is inside the spec's domain and
        # the spec demands `Except.ok []` there. A rival that is correct on every
        # n >= 1 and errors only at n = 0 is rejected — which is what pins that
        # the obligation is universally quantified over `n` with no implicit
        # n >= 1 side condition.
        "module": _swap(
            _BASE, _RET_OK,
            "  if n = 0 then return Except.error \"no regions\"\n" + _RET_OK,
        ),
        "refinement": (
            "Raising when there is nothing to color, instead of returning the "
            "empty coloring, is a partiality the modeled operation does not have: "
            "the palette is accepted and the per-region walk simply produces no "
            "entries. A patch that raised on the degenerate region count would "
            "turn a no-op call into an exception — a new failure mode on an input "
            "the operation previously handled, so it does NOT resolve; and being "
            "correct on every n >= 1 it is exactly the kind of near-miss that a "
            "battery probing only n >= 1 would certify by accident."
        ),
        "rationale": (
            "REJECT from clause C1 at n=0: at colors=[\"c0\",\"c1\",\"c2\",\"c3\"], "
            "n=0 the rival returns `Except.error _` while the spec demands "
            "`Except.ok []` (`(List.range 0).map … = []`). This is the ONLY case "
            "that probes the n=0 boundary — every other rival is witnessed at "
            "n >= 1, so without it the spec's behavior at the bottom of its own "
            "domain is unattested."
        ),
        "witness": _witness("[\"c0\",\"c1\",\"c2\",\"c3\"]", "0"),
    },
]

# No Docker AXIOM_TESTS: Solution.lean declares no opaque callee and no consumed
# axiom (the cycling behavior is modeled concretely as modular palette indexing).
# The nagini sibling's deep-model A-reference probe (cyc_prefix == itertools.cycle)
# belongs to G-AX, not this gate, and is dropped per the porting map.
AXIOM_TESTS = []
