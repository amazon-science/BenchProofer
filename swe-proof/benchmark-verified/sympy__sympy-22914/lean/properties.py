"""properties.py — G-PBT falsification battery for sympy__sympy-22914 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_printApp`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect:"reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

DEFENDED SURFACE (one total function over a three-input domain):

  printApp (name : String) (args : List String) (fallback : String) : String
      result = (per-name dispatch over the built-in table)
    where
      renderCall fn args = fn ++ "(" ++ String.intercalate ", " args ++ ")"

  The observable is the source text emitted for one function-application node.
  The specification is TOTAL (no domain restriction) and splits the name domain
  into four cases pinned by four independent top-level clauses:

    * (C1) the minimum operation renders as a `min(…)` call over its args;
    * (C2) the maximum operation renders as a `max(…)` call over its args;
    * (C3) the absolute-value operation keeps its pre-existing `abs(…)` render;
    * (C4) EVERY other name is emitted verbatim as the read-only `fallback`
      input — the unchanged surrounding machinery's output — so nothing but the
      minimum/maximum emission may change.

  Every clause pins the result to the inputs (the name, the argument strings,
  and the fallback text), so no part of the output is left free. Two orthogonal
  attack surfaces:

    (i) the DOMAIN PARTITION on `name` {Min, Max, Abs, other} — each clause pins
        a distinct sub-domain, and an impl correct on a subset but diverging on
        one name must be rejected. The partition is attacked in BOTH directions:
        too FEW mapped names (``weak-drop-max``) and too MANY
        (``weak-over-map``, which agrees with the frozen impl on all three
        mapped names and on the `"Foo"` point the other C4 rivals use, so only
        its own witness discriminates it);

    (ii) the CALL ASSEMBLY that each supported clause pins via `renderCall` —
        the target name (``weak-swap-minmax``, ``weak-abs-wrong-name``), the
        argument separator (``weak-bad-separator``), and the argument ORDER
        (``weak-arg-order``). Attacking dispatch alone would leave the rendering
        format unpinned, since a rival that keeps `renderCall` verbatim cannot
        expose it.

  Binder coverage of the reject witnesses (below): `name` at
  Min/Max/Abs/Foo/Sum; `args` at `["a","b"]`, `["x"]`, `["x","y"]`; `fallback`
  load-bearing only on the C4 sub-domain and pinned there at two distinct values
  by the unsupported-path rivals.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack (`joined_args.append(7)`) MANDATORY because its modeled
    inputs are held at fractional (read-only) permission and a rival that
    overwrites one is rejected for insufficient permission. Lean is
    referentially transparent: `name` / `args` / `fallback` are plain immutable
    values, there is no half-permission to violate and no aliasing to exploit,
    so this class has NO expressible instance here. No substitute is fabricated
    for it (see nagini ``weak-frame-mutate``).

  * PARTIAL-DOMAIN (drop a supported name) — APPLIES. A rival that treats the
    maximum operation as unsupported (routes it to `fallback`) violates C2 on the
    Max sub-domain; ported as ``weak-drop-max``.

  * VALUE-LEVEL (swap target names) — APPLIES. A rival that swaps the min/max
    target names violates C1 (and symmetrically C2); ported as
    ``weak-swap-minmax``.

  * PARTIAL-DOMAIN on the pre-existing supported name — APPLIES. A rival that
    renders the absolute-value operation with a wrong target name violates C3;
    ported as ``weak-abs-wrong-name``.

  * UNSUPPORTED-PATH DIVERGENCE — APPLIES (this is exactly the class the
    pre-repair nagini spec ADMITTED, the G-PANEL-1 finding; the frozen lean spec
    pins C4 to `fallback` verbatim). Two rivals: one that decorates the fallback
    text (``weak-unsupported-diverge``) and one that forges a supported call form
    for an unknown name (``weak-unsupported-as-min``); both violate C4.

  * OVER-MAPPING / CALL-ASSEMBLY — APPLIES, and has no nagini analogue. The
    nagini carrier addresses the name by an integer code in a closed domain
    (`0 <= name_code <= 3`), so "an extra name is mapped" is not expressible
    there: there is no fourth code to over-map. This carrier keys the dispatch on
    an unbounded `String`, so the row set is open and the too-many-rows direction
    becomes attackable (``weak-over-map``). Likewise nagini builds the argument
    text by list concatenation on a single `joined_args` input, so the separator
    and the argument order are not separable observables there; here `args : List
    String` is joined by the modeled `renderCall`, which exposes both
    (``weak-bad-separator``, ``weak-arg-order``). These three rivals are ADDED by
    this port rather than ported — the carrier is strictly more attackable on the
    rendering surface than the sibling.

  * AXIOM lane — DROPPED. The lean bundle declares no `opaque`/`axiom` (the
    dispatch, the name→built-in mapping, and the comma-join are modeled DEEPLY as
    the `if` ladder + `renderCall`), so there is no in-model axiom obligation, and
    the axiom lane is G-AX's job, not this gate's. See nagini ``AXIOM_TESTS``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
concrete input; each was built (against the rival) and rebuilt (against the
frozen solution) to confirm it HOLDS of its rival and FAILS on gold (so it
discriminates rather than asserting a tautology). The carrier is fully
transparent (`String` / `List String`, no opaque term), so each witness closes
by `unfold` + `decide` on concrete string literals.

``pts`` = 6 distinct input points across the 8 reject witnesses. The count is
below the case count on purpose: ``weak-swap-minmax``, ``weak-bad-separator`` and
``weak-arg-order`` all refute at the SAME input point (`"Min"`, `["a", "b"]`,
`"Z"`) because they attack three different things the spec pins ABOUT that one
point — the target name, the separator, and the argument order. Distinct points
are not the measure of discrimination here; distinct violated obligations are.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-22914"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  -- the built-in-equivalent table now maps the minimum and maximum operations;\n"
    "  -- the absolute-value mapping is pre-existing\n"
    "  if name = \"Min\" then renderCall \"min\" args\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  -- no built-in equivalent: the node keeps the unchanged machinery's emission\n"
    "  else fallback"
)

_PROOF_BODY = (
    "  intro name args fallback\n"
    "  unfold problem_spec_printApp implementation_printApp\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · intro h; simp [h]\n"
    "  · intro h; simp [h]\n"
    "  · intro h; simp [h]\n"
    "  · intro h1 h2 h3; simp [h1, h2, h3]"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): structurally different but CORRECT — test the
# UNSUPPORTED predicate FIRST (returning fallback), then dispatch the supported
# names by a reordered ladder (abs before min before max). Same value on every
# input; the frozen script is retuned to the reshaped ladder (`subst`/`simp`
# per branch), statement byte-identical, no new lemma/axiom.
_POS_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  -- unsupported-first dispatch, then a reordered supported ladder\n"
    "  if name ≠ \"Min\" ∧ name ≠ \"Max\" ∧ name ≠ \"Abs\" then fallback\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else if name = \"Min\" then renderCall \"min\" args\n"
    "  else renderCall \"max\" args"
)
_POS_PROOF = (
    "  intro name args fallback\n"
    "  unfold problem_spec_printApp implementation_printApp\n"
    "  refine ⟨?_, ?_, ?_, ?_⟩\n"
    "  · intro h; subst h; simp\n"
    "  · intro h; subst h; simp\n"
    "  · intro h; subst h; simp\n"
    "  · intro h1 h2 h3; simp [h1, h2, h3]"
)

# DROP-MAX (partial-domain): only the minimum and absolute-value names are
# supported; the maximum name falls through to `fallback`.
_DROP_MAX_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"min\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else fallback"
)

# SWAP-MINMAX (value-level): the minimum name renders as `max(…)` and the
# maximum name as `min(…)`.
_SWAP_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"max\" args\n"
    "  else if name = \"Max\" then renderCall \"min\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else fallback"
)

# ABS-WRONG-NAME (partial-domain on the pre-existing supported name): the
# absolute-value name renders with the wrong target name `ans(…)`.
_ABS_WRONG_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"min\" args\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"ans\" args\n"
    "  else fallback"
)

# UNSUPPORTED-DIVERGE (C4 violation): the unsupported path decorates the
# machinery's output instead of returning it verbatim.
_UNSUP_DIVERGE_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"min\" args\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else \"#\" ++ fallback"
)

# UNSUPPORTED-AS-MIN (C4 violation): an unknown name is forged into the `min(…)`
# supported call form instead of returning the machinery's output.
_UNSUP_MIN_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"min\" args\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else renderCall \"min\" args"
)

# OVER-MAP (C4 violation at a name the other C4 rivals leave correct): the
# built-in table gains an EXTRA, unauthorized row, so one further name is
# rendered as a built-in call instead of keeping the machinery's emission. This
# rival agrees with the frozen impl on all three mapped names AND on the name
# both other C4 rivals are refuted at, so only a witness aimed at the extra row
# catches it — the "too many rows" direction, which no other rival probes.
_OVER_MAP_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"min\" args\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else if name = \"Sum\" then renderCall \"sum\" args\n"
    "  else fallback"
)

# BAD-SEPARATOR (C1 violation inside the call ASSEMBLY): the right name is
# dispatched and the right arguments are used, but they are joined without the
# space after the comma. Every other rival keeps `renderCall` verbatim and so
# leaves the join/parenthesization format entirely unprobed.
_SEP_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then \"min\" ++ \"(\" ++ String.intercalate \",\" args ++ \")\"\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else fallback"
)

# ARG-ORDER (C1 violation on the argument SEQUENCE): the right name and the
# right separator, but the already-printed arguments are emitted in reverse.
# No other rival varies the argument order, so this is the only case pinning
# `args` as an ORDERED sequence rather than a bag.
_ARG_ORDER_IMPL = (
    "def implementation_printApp\n"
    "    (name : String) (args : List String) (fallback : String) : String :=\n"
    "  if name = \"Min\" then renderCall \"min\" args.reverse\n"
    "  else if name = \"Max\" then renderCall \"max\" args\n"
    "  else if name = \"Abs\" then renderCall \"abs\" args\n"
    "  else fallback"
)

# ADMISSIBILITY: the frozen impl+proof, with a ground instance discharged at the
# F2P-shaped input (the minimum operation, a non-trivial argument list) BEFORE
# the frozen obligation, proving the modeled behavior is satisfiable at exactly
# the input the F2P exercises (`doprint(Min(a, b)) == "min(a, b)"`).
_ADMISS_PROOF = (
    "  have _ground : problem_spec_printApp \"Min\" [\"a\", \"b\"] \"fb\"\n"
    "      (implementation_printApp \"Min\" [\"a\", \"b\"] \"fb\") := by\n"
    "    unfold problem_spec_printApp implementation_printApp; decide\n"
    + _PROOF_BODY
)


# Shared witness tactic: unfold spec + impl + renderCall, close the concrete
# string (in)equality with decide (the carrier is fully transparent).
def _witness(name, args, fallback):
    return (
        f"example : ¬ problem_spec_printApp {name} {args} {fallback}\n"
        f"    (implementation_printApp {name} {args} {fallback}) := by\n"
        "  unfold problem_spec_printApp implementation_printApp renderCall\n"
        "  decide"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_printApp`
    # STATEMENT is byte-identical; the tactic body is retuned to the reshaped
    # (unsupported-first) ladder. No helper lemma, axiom, or assumption token.
    # =====================================================================
    {
        "id": "pos-unsupported-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that tests the unsupported predicate FIRST "
            "(returning `fallback`) and then dispatches the supported names by a "
            "reordered ladder (abs, then min, then max) must satisfy all four "
            "clauses C1–C4; if it cannot, the spec is SPEC-TOO-STRONG. Only the "
            "executable shape changes; each supported branch still yields "
            "`renderCall v args` and the unsupported branch still yields "
            "`fallback`, so the proof closes per-branch by `subst`/`simp` with no "
            "new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # behavior is total, so `∀` is unguarded), so nagini's precondition-admission
    # probe (`admiss-min`) has no binder to attack here; the honest analogue is
    # to discharge the spec predicate at the F2P ground input (the minimum
    # operation over a non-trivial argument list) inside the proof region,
    # alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-min-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (the minimum "
            "operation `\"Min\"` over the argument list `[\"a\", \"b\"]`, the "
            "shape the F2P `doprint(Min(a, b)) == \"min(a, b)\"` exercises) by "
            "`decide` on the concrete strings; then the frozen obligation is "
            "closed verbatim. Verifies (else the spec is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the theorem STATEMENT is byte-identical, the ground instance "
            "is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-drop-max",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_MAX_IMPL),
        "refinement": (
            "the faithful patch adds BOTH built-in rows (minimum ↦ min AND "
            "maximum ↦ max). A patch that adds only the minimum row leaves the "
            "maximum operation to the unchanged later arms, which render it via "
            "the Piecewise rewrite (a non-call form), NOT `max(a, b)`, so it FAILS "
            "the F2P assertion `doprint(Max(a, b)) == \"max(a, b)\"`. A verifying "
            "rival would be a genuine verify-does-not-resolve break."
        ),
        "rationale": (
            "REJECT from clause C2 (`name = \"Max\" → result = renderCall \"max\" "
            "args`): at `name = \"Max\"`, `args = [\"a\", \"b\"]` the spec demands "
            "`max(a, b)`, but the rival routes the maximum name to `fallback` "
            "(`\"Z\"`). Refuted on the Max sub-domain — a direct attack on the "
            "domain partition. If it verifies, the spec does not force the "
            "maximum-call form (partial-domain SPEC-TOO-WEAK)."
        ),
        "witness": _witness('"Max"', '["a", "b"]', '"Z"'),
    },
    {
        "id": "weak-swap-minmax",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SWAP_IMPL),
        "refinement": (
            "a real table mapping the minimum operation to `max` (and vice versa) "
            "would render `doprint(Min(a, b)) == \"max(a, b)\"`, FAILING the F2P "
            "assertion `doprint(Min(a, b)) == \"min(a, b)\"`. Not a faithful patch."
        ),
        "rationale": (
            "REJECT from clause C1 (`name = \"Min\" → result = renderCall \"min\" "
            "args`): at `name = \"Min\"`, `args = [\"a\", \"b\"]` the spec demands "
            "the `min(…)` form, but the rival emits `max(a, b)`. Refuted at the "
            "Min point (and symmetrically C2 would refute at Max). If it verifies, "
            "the spec does not pin the target NAMES to their operations "
            "(SPEC-TOO-WEAK on the value level)."
        ),
        "witness": _witness('"Min"', '["a", "b"]', '"Z"'),
    },
    {
        "id": "weak-abs-wrong-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABS_WRONG_IMPL),
        "refinement": (
            "rendering the absolute-value operation as `ans(x)` instead of "
            "`abs(x)` breaks the long-standing behavior the pre-existing test "
            "suite depends on and is not the gold edit (which leaves the "
            "absolute-value ↦ abs row untouched). Not a faithful patch."
        ),
        "rationale": (
            "REJECT from clause C3 (`name = \"Abs\" → result = renderCall \"abs\" "
            "args`): at `name = \"Abs\"`, `args = [\"x\"]` the spec demands the "
            "literal `abs(` prefix, but the rival emits `ans(x)`. Refuted on the "
            "pre-existing supported sub-domain, exercising `args` at a "
            "single-element shape distinct from the other witnesses. If it "
            "verifies, the spec leaves the pre-existing target name unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness('"Abs"', '["x"]', '"Z"'),
    },
    {
        "id": "weak-unsupported-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNSUP_DIVERGE_IMPL),
        "refinement": (
            "the gold patch changes ONLY the built-in table. An impl that alters "
            "what an unknown name prints (here a `#`-decorated variant of the "
            "unchanged machinery's output) diverges from the real fallback (the "
            "Piecewise rewrite / not-supported text) and would mis-print every "
            "unknown function while leaving the F2P-observed built-in calls "
            "intact. Not a faithful patch — exactly the rival class the "
            "pre-repair spec admitted (the G-PANEL-1 finding)."
        ),
        "rationale": (
            "REJECT from clause C4 (`name ≠ \"Min\" → name ≠ \"Max\" → name ≠ "
            "\"Abs\" → result = fallback`): at `name = \"Foo\"`, `fallback = "
            "\"Z\"` the spec demands the result equal `fallback` verbatim, but the "
            "rival emits `\"#Z\"`. Refuted on the unsupported sub-domain, "
            "exercising `fallback` as the load-bearing binder. If it verifies, the "
            "spec does not pin the no-change half of the contract (SPEC-TOO-WEAK)."
        ),
        # fallback = "Z" here vs "P(q)" in weak-unsupported-as-min below, so the
        # C4 refutation probes `fallback` at two distinct values: a rival that
        # returned a fixed constant on the unsupported path would match at most
        # one of the two and be caught by the other.
        "witness": _witness('"Foo"', '["x"]', '"Z"'),
    },
    {
        "id": "weak-unsupported-as-min",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_UNSUP_MIN_IMPL),
        "refinement": (
            "rendering an unknown name `f(x, y)` as `min(x, y)` is a wrong "
            "printer: an unknown function must not collapse to a supported "
            "target's call form. The gold patch leaves the unsupported path as the "
            "unchanged machinery's fallback; this rival would mis-print every "
            "unknown function. Not a faithful patch."
        ),
        "rationale": (
            "REJECT from clause C4 (`name ≠ \"Min\" → name ≠ \"Max\" → name ≠ "
            "\"Abs\" → result = fallback`): at `name = \"Foo\"`, `args = [\"x\", "
            "\"y\"]`, `fallback = \"P(q)\"` the spec demands the result equal "
            "`fallback`, but the rival forges `min(x, y)`. Refuted on the "
            "unsupported sub-domain at a two-argument shape and a `fallback` value "
            "(`\"P(q)\"`) distinct from the single-argument diverge witness "
            "(`\"Z\"`), so the C4 refutation is exercised at two argument shapes "
            "AND two fallback values — a rival returning a fixed constant on the "
            "unsupported path is caught by whichever witness disagrees. If it "
            "verifies, the spec allows an unknown name to borrow a supported call "
            "form (SPEC-TOO-WEAK)."
        ),
        "witness": _witness('"Foo"', '["x", "y"]', '"P(q)"'),
    },
    {
        "id": "weak-over-map",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OVER_MAP_IMPL),
        "refinement": (
            "the faithful patch adds EXACTLY the minimum and maximum rows to the "
            "built-in table. A patch that also maps a further function to a "
            "built-in call changes the emission of a node the gold edit leaves "
            "alone: that name's node would render as a built-in call instead of "
            "keeping the unchanged machinery's output, silently altering behaviour "
            "the pre-existing suite pins. Not a faithful patch — the "
            "too-many-rows direction, the mirror image of ``weak-drop-max``."
        ),
        "rationale": (
            "REJECT from clause C4 (`name ≠ \"Min\" → name ≠ \"Max\" → name ≠ "
            "\"Abs\" → result = fallback`): at `name = \"Sum\"`, `args = [\"a\", "
            "\"b\"]`, `fallback = \"Z\"` the spec demands the result equal "
            "`fallback`, but the rival emits `sum(a, b)`. This rival agrees with "
            "the frozen impl on all three mapped names AND on `\"Foo\"` — the name "
            "the other two C4 rivals are refuted at — so neither of their "
            "witnesses discriminates it; only a witness aimed at the extra row "
            "does. If it verifies, C4 fails to forbid ADDING a built-in mapping "
            "(SPEC-TOO-WEAK on the over-approximation side)."
        ),
        "witness": _witness('"Sum"', '["a", "b"]', '"Z"'),
    },
    {
        "id": "weak-bad-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_SEP_IMPL),
        "refinement": (
            "the argument text is assembled by joining the already-printed "
            "arguments with a comma AND a space. An impl that drops the space "
            "renders the minimum call as `min(a,b)`, which is not the text the "
            "F2P assertion `doprint(Min(a, b)) == \"min(a, b)\"` demands, so a "
            "faithful patch of this shape would not resolve."
        ),
        "rationale": (
            "REJECT from clause C1 (`name = \"Min\" → result = renderCall \"min\" "
            "args`): at `name = \"Min\"`, `args = [\"a\", \"b\"]` the spec demands "
            "`min(a, b)` but the rival emits `min(a,b)`. This attacks the call "
            "ASSEMBLY (the separator inside `renderCall`) rather than the dispatch "
            "— every other rival keeps `renderCall` verbatim, so the join format "
            "was otherwise unprobed. If it verifies, the spec does not pin the "
            "argument separator (SPEC-TOO-WEAK on the rendering format)."
        ),
        "witness": _witness('"Min"', '["a", "b"]', '"Z"'),
    },
    {
        "id": "weak-arg-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ARG_ORDER_IMPL),
        "refinement": (
            "the already-printed arguments are emitted in their original order. "
            "An impl that reverses them renders the minimum call over two "
            "arguments as `min(b, a)`, failing the F2P assertion "
            "`doprint(Min(a, b)) == \"min(a, b)\"`. Not a faithful patch."
        ),
        "rationale": (
            "REJECT from clause C1 (`name = \"Min\" → result = renderCall \"min\" "
            "args`): at `name = \"Min\"`, `args = [\"a\", \"b\"]` the spec demands "
            "`min(a, b)` but the rival emits `min(b, a)`. This pins `args` as an "
            "ORDERED sequence: no other rival varies the argument order, so a spec "
            "that constrained only the multiset of arguments would have passed the "
            "rest of the battery. If it verifies, the spec leaves the argument "
            "order free (SPEC-TOO-WEAK)."
        ),
        "witness": _witness('"Min"', '["a", "b"]', '"Z"'),
    },
]


# AXIOM lane: EMPTY. The lean bundle declares no `opaque`/`axiom` (meta.json
# axioms == [] and deep_model_references == []); the dispatch test, the
# name→built-in mapping, and the comma-join are modeled DEEPLY as the `if` ladder
# + `renderCall`, so there is no in-model axiom obligation for the PBT axiom lane
# to re-discharge. (The nagini AXIOM_TESTS lane is G-AX's job, not this gate's.)
AXIOM_TESTS = []
