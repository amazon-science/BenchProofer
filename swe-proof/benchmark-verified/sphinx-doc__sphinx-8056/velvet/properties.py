"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8056 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (two contracted methods over a free flag and a free field
sequence):

  splitSharedNameFields (multiple : Bool) (raw : List Field) return (out : List Field)
      ensures out = expandFields multiple raw
  buildParameterFieldSeq (splitNames : Bool) (raw : List Field) return (out : List Field)
      ensures out = expandFields splitNames raw

A sequence of raw documented fields is turned into the output field sequence:
when the boolean flag is set AND a field's name is non-empty, that field's name
is split into its comma pieces (each trimmed) and every piece becomes its own
field carrying the shared type/description; otherwise the field is kept verbatim,
unless it is entirely empty (in which case it is dropped). ``buildParameterFieldSeq``
is the caller that threads its own selecting flag into the collector.

``expandFields`` (and the per-field ``expandOne``, plus the deep string models
``splitOnComma`` / ``stripWs``) is a total, fully-unfolded pure ``def`` in the
frozen ``pure`` region — hence part of the consumer spec view. Both methods'
sole ``ensures`` pins the whole output to it. Both input binders of each method
are FREE (no ``require`` clause, no ``mut`` binder), which is what makes the
rivals below refutable at a concrete point.

CARRIER NOTE — where the nagini rivals go. The nagini sibling attacks the
per-field split/trim/keep/drop arithmetic directly (its P1 comma-count, P2 trim,
P5 empty-drop, P6 verbatim clauses). On THIS carrier every one of those behaviours
is spelled out INSIDE the frozen ``expandOne`` / ``splitOnComma`` / ``stripWs``
defs, which sit in the spec view: an impl variant cannot re-express them without
editing the spec (which ``same_spec`` forbids). So those internal-clause rivals
collapse under carrier narrowing and are OMITTED (see footer), NOT because they
were hard. What the two impls DO control — and what the fix's F2P discriminator
actually turns on — is (a) which flag is threaded into the expansion (the gold
patch's whole ``_parse_parameters_section`` change is exactly wiring the split
flag on under the relevant configuration) and (b) the traversal/concatenation of
the field sequence. The rivals attack precisely those transparent surfaces.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating loop collapsed to the closed
    form the post-image names; the loop body inlined; the caller inlined) must
    still verify, else the spec is SPEC-TOO-STRONG on impl shape.
  * ADMISSIBILITY — neither method carries a ``require`` clause, so the "a normal
    input satisfies the precondition" probe is degenerate (every input is
    in-domain). The residual risk on a total-domain spec is a DEGENERATE
    post-image — one that does not actually distinguish expand from keep. The
    admissibility case discharges an in-region assert pinning, at concrete
    F2P-shaped points, that the modeled expansion really does produce two fields
    from a comma name under the flag, one field without it, and zero from an
    empty field.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The nagini class exists
    because a read-only heap input carries a fractional permission an impl can
    overwrite. Lean and Velvet are referentially transparent: ``multiple`` /
    ``splitNames`` / ``raw`` are immutable values (none declared ``mut``), there
    is no heap and no aliasing, so there is no read-only input to mutate and no
    permission system to trip. Reported as an omission in the footer; not
    fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``expandFields``, a
    concrete ``def`` computed from the method's own arguments (the ``axioms``
    region declares NO ``axiom``; no opaque answer key). There is no wrong echo to
    build; the honest controls are the cheapest faithful reshapes.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — flag-threading and traversal. A rival that
    ignores the flag (never expands, or always expands), inverts it, or drops a
    raw field diverges on a sub-domain the F2P input reaches and MUST be rejected.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches it through Velvet's own tester
machinery: ``<method>Tester <args> = false`` says the extracted program's result
violates the postcondition at that concrete input, checked in a file whose
``prove_correct`` block has been stripped (no tactic script can mask the verdict).
The frozen ``splitSharedNameFields`` program contains a ``while`` loop, whose
fixpoint does not reduce under the kernel's ``decide``; ``buildParameterFieldSeq``
calls it, so it inherits the same irreducibility. Every reject rival is reshaped
into a LOOP-FREE closed form (returning ``expandFields`` of some flag directly),
so ITS tester ``decide``s while the SAME witness applied to the loop-bearing
frozen solution cannot reduce and so fails to elaborate. The discrimination is
thus structural, not a tactic-tuning artifact. (Verified out of band with
``scripts/lean_verify.sh``: each witness builds green against its rival and red
against the frozen solution.)

WITNESS PLACEMENT. Every witness uses fully concrete decidable literals, so no
witness binds a hypothesis (no consistency question arises). Across the five
rejects both binders of each obligation are moved: the flag ranges over ``true``
and ``false`` and ``raw`` ranges over a single comma-name field, a two-field
sequence, and a distinct comma-name field. A rival that mishandled only a fixed
flag value or a fixed input shape would still be caught.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; the two deep
models (``splitOnComma`` / ``stripWs``) are A-references the G-AX lane
differential-tests against the real ``str.split(',')`` / ``str.strip()``, not
consumed contracts. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8056"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each lies wholly inside an impl region (between -- impl-start
# and -- impl-end) or is a full prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load by _swap. Editing only these
# keeps markers.same_spec True and every prove_correct statement byte-identical
# (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The whole executable body of the collector: a backward accumulating loop over
# the raw field sequence, prepending each field's expansion.
_IMPL1 = """    -- impl-start
    let mut result : List Field := []
    let mut i := raw.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ raw.length
      invariant result = expandFields multiple (raw.drop i)
      done_with i = 0
      decreasing i
    do
      let f := raw[i - 1]!
      result := expandOne multiple f ++ result
      i := i - 1
    return result
    -- impl-end"""

# The frozen collector proof (drop-step lemma + simp_all).
_PROOF1 = """prove_correct splitSharedNameFields by
  loom_solve
  rw [expandFields_drop_step multiple raw i (by omega) (by omega)]
  simp_all"""

# The whole executable body of the caller: delegate to the collector, threading
# its own flag through.
_IMPL2 = """    -- impl-start
    let fields ← splitSharedNameFields splitNames raw
    return fields
    -- impl-end"""

# The frozen caller proof.
_PROOF2 = """prove_correct buildParameterFieldSeq by
  loom_solve"""

for _anchor in (_IMPL1, _PROOF1, _IMPL2, _PROOF2):
    assert _BASE.count(_anchor) == 1, f"anchor drift: {_anchor[:40]!r}"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape an impl region AND retune its tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. Reach a method contract through Velvet's tester
# ---- machinery: `<method>Tester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose prove_correct blocks are stripped.
def _tester1(body):
    return ("extract_program_for splitSharedNameFields\n"
            "prove_precondition_decidable_for splitSharedNameFields\n"
            "prove_postcondition_decidable_for splitSharedNameFields\n"
            "derive_tester_for splitSharedNameFields\n\n" + body)


def _tester2(body):
    return ("extract_program_for buildParameterFieldSeq\n"
            "prove_precondition_decidable_for buildParameterFieldSeq\n"
            "prove_postcondition_decidable_for buildParameterFieldSeq\n"
            "derive_tester_for buildParameterFieldSeq\n\n" + body)


# Concrete Field literals for readable witnesses.
_CF = "{ name := ['x', ',', 'y'], typ := [], desc := [] }"   # a comma name
_SP = "{ name := ['x', ',', ' ', 'y'], typ := [], desc := [] }"  # comma name, padded 2nd piece
_PQ = "{ name := ['p', ',', 'q'], typ := [], desc := [] }"   # a distinct comma name
_A = "{ name := ['a'], typ := [], desc := [] }"              # a plain name
_B = "{ name := ['b'], typ := [], desc := [] }"              # a plain name
_EMPTY = "{ name := ([] : List Char), typ := [], desc := [] }"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps its `ensures out = expandFields ...`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-collector-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator); the loop-specific proof is retuned to `loom_solve` since
        # the impl now matches the post-image syntactically.
        "module": _swap2(
            _IMPL1,
            "    -- impl-start\n"
            "    return expandFields multiple raw\n"
            "    -- impl-end",
            _PROOF1,
            "prove_correct splitSharedNameFields by\n"
            "  loom_solve"),
        "rationale": "a loop-free collector that returns the field-expansion "
                     "directly must satisfy `out = expandFields multiple raw`; a "
                     "correct reshape of the modeled behaviour verifying is exactly "
                     "what SPEC-TOO-STRONG would deny. Exercises the collector "
                     "obligation from a maximally different (loop-free) shape. "
                     "(Sibling: pos-control-branch-reorder.)",
    },
    {
        "id": "pos-collector-inlined-loop",
        "kind": "soundness",
        "expect": "verify",
        # Reshape that KEEPS the loop and the invariant but inlines the indexed
        # field access into the accumulation step. Same value flow; the frozen
        # drop-step proof still closes untouched.
        "module": _swap(
            _BASE,
            "      let f := raw[i - 1]!\n"
            "      result := expandOne multiple f ++ result\n",
            "      result := expandOne multiple raw[i - 1]! ++ result\n"),
        "rationale": "inlining the indexed field access leaves the accumulator "
                     "value-for-value identical with the loop and invariant "
                     "unchanged, so `out = expandFields multiple raw` still holds "
                     "and the frozen proof closes; a correct reshape must verify, "
                     "else SPEC-TOO-STRONG on the loop body's shape.",
    },
    {
        "id": "pos-caller-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Caller reshape: inline the field expansion directly instead of
        # delegating to the collector method. Same threaded flag, same result.
        "module": _swap(
            _BASE, _IMPL2,
            "    -- impl-start\n"
            "    return expandFields splitNames raw\n"
            "    -- impl-end"),
        "rationale": "computing the field sequence inline with the same threaded "
                     "flag produces `out = expandFields splitNames raw`, the "
                     "caller's exact obligation; a correct reshape that bypasses "
                     "the delegation must still verify, else SPEC-TOO-STRONG on "
                     "the caller's shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — neither method has a `require` clause, so the "a normal
    # input satisfies the precondition" probe is degenerate (every input is
    # in-domain). The residual risk is a DEGENERATE post-image — one that does
    # not distinguish expand from keep. This case discharges an in-region assert
    # at concrete F2P-shaped points establishing that the modeled expansion is
    # non-degenerate: under the flag a comma name yields TWO fields, without the
    # flag ONE, and an entirely empty field ZERO. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the proof gains a
    # `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-expansion-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            "    let mut result : List Field := []",
            "    assert (with_name_prefix `admiss\n"
            f"      ((expandFields true [{_CF}]).length = 2 ∧\n"
            f"       (expandFields false [{_CF}]).length = 1 ∧\n"
            f"       (expandFields false [{_EMPTY}]).length = 0))\n"
            "    let mut result : List Field := []",
            _PROOF1,
            "prove_correct splitSharedNameFields by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [expandFields_drop_step multiple raw i (by omega) (by omega)];\n"
            "       simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: under the flag a single comma-name field "
                     "expands to TWO output fields, without the flag it is kept as "
                     "ONE, and an entirely empty field yields ZERO — the three "
                     "behaviours the failing test discriminates. The in-region "
                     "assert must discharge (else the expansion is constant / the "
                     "obligation degenerate); the impl is kept verbatim so "
                     "`out = expandFields multiple raw` still verifies. (Sibling: "
                     "admissibility-readonly-name, re-aimed.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-collector-never-expands",
        "kind": "uniqueness",
        "expect": "reject",
        # The collector ignores its flag and never expands (constant `false`).
        # This is a patch that added the split flag to the collector but never
        # consulted it — every field is kept verbatim regardless.
        "module": _swap(
            _BASE, _IMPL1,
            "    -- impl-start\n"
            "    return expandFields false raw\n"
            "    -- impl-end"),
        "refinement": "a faithful counterpart is the collector that gained the "
                      "split flag but never reads it, so a comma-listed name is "
                      "always kept as one field. Under the configuration that "
                      "requests expansion the failing test asserts a comma name "
                      "becomes SEVERAL fields (each rendered as its own entry); "
                      "keeping it whole reproduces the pre-image rendering, so the "
                      "test still fails. It does NOT resolve.",
        "rationale": "REJECT from `out = expandFields multiple raw`: at "
                     "`multiple = true` over a comma-name field, `expandFields` "
                     "expands into several fields, while the rival keeps one. "
                     "Verifying would be SPEC-TOO-WEAK (the flag is unenforced). "
                     "Refuted at `multiple = true` (the expansion regime). "
                     "(Sibling: partial-domain-count-off-by-one, re-aimed to the "
                     "flag the fix threads.)",
        "witness": _tester1(
            f"example : splitSharedNameFieldsTester true [{_CF}] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-collector-always-expands",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: the collector ignores its flag and ALWAYS expands (constant
        # `true`). Correct on the expansion regime; wrong wherever a field should
        # be kept verbatim.
        "module": _swap(
            _BASE, _IMPL1,
            "    -- impl-start\n"
            "    return expandFields true raw\n"
            "    -- impl-end"),
        "refinement": "a counterpart that always expands regardless of the flag "
                      "splits a comma-listed name even under the configuration "
                      "that must keep the declaration whole — where the failing "
                      "test asserts the field stays a SINGLE verbatim entry. It "
                      "breaks that half of the test, so it does NOT resolve.",
        "rationale": "REJECT from `out = expandFields multiple raw`: at "
                     "`multiple = false` over a comma-name field, `expandFields` "
                     "keeps ONE verbatim field, while the rival splits it. "
                     "Refuted at `multiple = false` — the verbatim regime, the "
                     "mirror of the never-expands rival, so the flag binder is "
                     "moved between the two.",
        "witness": _tester1(
            f"example : splitSharedNameFieldsTester false [{_CF}] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-collector-drops-last-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Traversal rival: expand every raw field EXCEPT the last (dropLast).
        # Threads the flag correctly but processes one fewer input field, so it
        # diverges on any sequence of two or more fields.
        "module": _swap(
            _BASE, _IMPL1,
            "    -- impl-start\n"
            "    return expandFields multiple raw.dropLast\n"
            "    -- impl-end"),
        "refinement": "a counterpart whose collection loop stopped one field "
                      "short would silently omit the final documented parameter "
                      "from the rendered section — a field the test expects to "
                      "appear. Dropping a real parameter fails the section "
                      "rendering, so it does NOT resolve.",
        "rationale": "REJECT from `out = expandFields multiple raw`: `expandFields` "
                     "concatenates the expansion of EVERY raw field, and the rival "
                     "omits the last, so the equality fails on any sequence with "
                     "at least two fields. Refuted at a two-field sequence "
                     "(varying `raw` to a multi-element list, which no other "
                     "witness does).",
        "witness": _tester1(
            f"example : splitSharedNameFieldsTester true [{_A}, {_B}] = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-caller-ignores-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # THE fix's discriminating delta. The caller ignores its selecting flag
        # and always requests the non-expanding behaviour — the pre-patch caller,
        # which collected fields without ever asking for the multi-name split.
        "module": _swap(
            _BASE, _IMPL2,
            "    -- impl-start\n"
            "    return expandFields false raw\n"
            "    -- impl-end"),
        "refinement": "this is the pre-image caller: it collects the parameter "
                      "fields without ever requesting the multi-name expansion, so "
                      "under the configuration that should expand, a comma-listed "
                      "declaration stays a single combined entry — exactly the "
                      "failing scenario. Its faithful counterpart is the unchanged "
                      "caller, which does not resolve.",
        "rationale": "REJECT from `out = expandFields splitNames raw`: at "
                     "`splitNames = true` over a comma-name field the caller must "
                     "expand, but the rival passes the non-expanding flag. "
                     "Verifying would be SPEC-TOO-WEAK (the flag threading is "
                     "unenforced). Refuted at `splitNames = true`.",
        "witness": _tester2(
            f"example : buildParameterFieldSeqTester true [{_CF}] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-caller-inverts-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: the caller INVERTS its selecting flag (expands exactly when
        # it should keep verbatim, and vice versa). Correct on neither regime;
        # refuted at the verbatim regime, moving the caller's flag binder.
        "module": _swap(
            _BASE, _IMPL2,
            "    -- impl-start\n"
            "    return expandFields (!splitNames) raw\n"
            "    -- impl-end"),
        "refinement": "a counterpart that wired the selecting flag the wrong way "
                      "expands when the configuration asks for a verbatim "
                      "declaration and keeps the declaration whole when it asks "
                      "for expansion — inverting the rendered output under both "
                      "configurations. It fails the test under each, so it does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = expandFields splitNames raw`: at "
                     "`splitNames = false` over a comma-name field the caller must "
                     "keep ONE verbatim field, but the inverted flag expands. "
                     "Refuted at `splitNames = false` — the verbatim regime, so "
                     "the caller's flag binder is moved against the ignores-flag "
                     "rival.",
        "witness": _tester2(
            f"example : buildParameterFieldSeqTester false [{_PQ}] = false := by\n"
            "  decide\n"),
    },

    # =====================================================================
    # PER-FIELD SPLIT/TRIM/DROP rivals — recovered from the nagini P2/P5
    # omission (see AUDIT note in footer). The claim that these are
    # "inexpressible without editing the spec" was WRONG: the impl region does
    # not have to CALL `expandOne`, so a variant may inline the per-field logic
    # as a loop-free closed form and mishandle exactly one clause (the trim, or
    # the empty-drop) while leaving `expandOne`/`stripWs`/`splitOnComma` and the
    # whole spec view byte-identical. `same_spec` holds (the inlined body lives
    # entirely inside the impl region), and the rival still diverges from
    # `expandFields multiple raw` on a concrete input the frozen def pins.
    # =====================================================================
    {
        "id": "weak-collector-no-trim",
        "kind": "uniqueness",
        "expect": "reject",
        # Inline the per-field expansion but FORGET the per-piece trim: the
        # comma pieces are mapped in WITHOUT `stripWs`. Correct on the count and
        # on the flag; wrong on any piece carrying surrounding whitespace. This
        # is the P2 rival (the `.strip()` dropped from the patched loop),
        # expressed inline so it stays in scope.
        "module": _swap(
            _BASE, _IMPL1,
            "    -- impl-start\n"
            "    return raw.flatMap (fun f =>\n"
            "      if multiple ∧ f.name ≠ [] then\n"
            "        (splitOnComma f.name).map (fun nm => { f with name := nm })\n"
            "      else if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else [])\n"
            "    -- impl-end"),
        "refinement": "a faithful counterpart is the patched loop with the "
                      "per-piece trim omitted: a comma name whose pieces carry "
                      "surrounding whitespace expands to padded fragments rather "
                      "than the trimmed pieces the section rendering expects, so a "
                      "declaration like `x, y` renders one piece as ` y`. It does "
                      "NOT resolve.",
        "rationale": "REJECT from `out = expandFields multiple raw`: `expandOne` "
                     "under the flag maps each comma piece through `stripWs`, so a "
                     "padded piece is trimmed; the rival keeps it untrimmed and the "
                     "equality fails. Refuted at `multiple = true` over a comma "
                     "name whose second piece has a leading space. (Recovers "
                     "nagini P2 — the split/trim clause — which the port wrongly "
                     "dropped as inexpressible.)",
        "witness": _tester1(
            f"example : splitSharedNameFieldsTester true [{_SP}] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-collector-keeps-empty-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Inline the per-field expansion but DROP the empty-field guard: in the
        # non-expanding branch, always keep `[f]` — even an entirely empty field.
        # Correct wherever a field carries content; wrong on an all-empty field,
        # which `expandOne` drops. This is the P5 rival, expressed inline.
        "module": _swap(
            _BASE, _IMPL1,
            "    -- impl-start\n"
            "    return raw.flatMap (fun f =>\n"
            "      if multiple ∧ f.name ≠ [] then\n"
            "        (splitOnComma f.name).map (fun nm => { f with name := stripWs nm })\n"
            "      else [f])\n"
            "    -- impl-end"),
        "refinement": "a faithful counterpart is the collector with the legacy "
                      "keep-guard removed, so an entirely empty raw field is "
                      "emitted as a spurious blank entry rather than dropped — the "
                      "renderer then produces an extra empty line the section must "
                      "not contain. It does NOT resolve.",
        "rationale": "REJECT from `out = expandFields multiple raw`: `expandOne` "
                     "drops an entirely empty field (no name, type, or "
                     "description) to the empty list; the rival keeps it as one "
                     "field, so the equality fails. Refuted at `multiple = false` "
                     "over a single empty field (moving `raw` to the all-empty "
                     "shape no other witness reaches). (Recovers nagini P5 — the "
                     "empty-drop clause — which the port wrongly dropped as "
                     "inexpressible.)",
        "witness": _tester1(
            f"example : splitSharedNameFieldsTester false [{_EMPTY}] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 1 mandatory frame-mutation rival, 4
# partial-domain uniqueness rivals) plus 2 AXIOM_TESTS. The sibling contracts
# ONE function `emitted_names` over a `List[int]` name carrying a fractional
# heap permission, with a verified backward `while` loop building the per-comma
# split and the split/trim/keep/drop arithmetic as postcondition clauses
# (P1..P6). This bundle models the SAME behaviour as TWO methods —
# `splitSharedNameFields` (the collector) and `buildParameterFieldSeq` (the
# caller that threads the flag, the fix's second edit site) — whose per-field
# split/trim/keep/drop is spelled out in the frozen pure `expandOne` /
# `splitOnComma` / `stripWs` defs. The value surface carries across; the
# permission surface does not, and the per-field arithmetic moves from
# postcondition clauses into the frozen spec view.
#
#   sibling case                          -> here                              disposition
#   -----------------------------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-collector-closed-form         PORTED
#   (—)                                   -> pos-collector-inlined-loop        ADDED
#   (—)                                   -> pos-caller-closed-form            ADDED (2nd method)
#   admissibility-readonly-name           -> admiss-expansion-nondegenerate    RE-AIMED
#   frame-mutation-write-name             -> (none)                            VACUOUS
#   partial-domain-count-off-by-one (P1)  -> weak-collector-never-expands      RE-AIMED (flag)
#                                            + weak-collector-drops-last-field ADDED (traversal)
#   partial-domain-no-trim (P2)           -> weak-collector-no-trim            RECOVERED (audit)
#   partial-domain-legacy-splits-anyway (P6) -> weak-collector-always-expands  RE-AIMED (flag)
#   partial-domain-empty-field-not-dropped (P5) -> weak-collector-keeps-empty-field RECOVERED (audit)
#   (—)                                   -> weak-caller-ignores-flag          ADDED (fix delta)
#   (—)                                   -> weak-caller-inverts-flag          ADDED (near-miss)
#
# 3 positives (1 ported, 2 added — the second method needs its own defence), 1
# admissibility (re-aimed), 5 uniqueness rivals; 1 frame-mutation vacuous.
#
# AUDIT CORRECTION — nagini P2/P5 are EXPRESSIBLE here; recovered as rivals.
#   The original port dropped partial-domain-no-trim (P2) and
#   partial-domain-empty-field-not-dropped (P5) claiming they were
#   "inexpressible without editing the spec": the argument was that trimming and
#   empty-drop live inside the frozen `expandOne`/`stripWs` defs (the spec view),
#   so no in-scope impl variant could mishandle them. That argument is WRONG.
#   The obligation is `out = expandFields multiple raw`, but the IMPL is not
#   required to CALL `expandFields`/`expandOne` — it only has to produce a value
#   equal to it. So a variant may INLINE the per-field split/keep/drop as a
#   loop-free closed form and mishandle exactly one clause (omit the `stripWs`
#   trim, or drop the empty-field guard) while `expandOne`/`stripWs`/
#   `splitOnComma` and the entire spec view stay byte-identical — `same_spec`
#   holds because the change is confined to the impl region. Verified out of
#   band with scripts/lean_verify.sh: both rivals are in scope (same_spec True),
#   FAIL to verify (module exit 1), and their witnesses discriminate (rival
#   build green, gold build red). The two rivals below (weak-collector-no-trim,
#   weak-collector-keeps-empty-field) recover exactly the P2/P5 coverage. The
#   admissibility case still pins these behaviours POSITIVELY as a cross-check (a
#   comma name yields two trimmed fields under the flag; an empty field yields
#   zero), but that positive pin is NOT a substitute for a refuting rival.
#
# RE-AIMED (P1 count, P6 verbatim -> flag rivals): the nagini count (P1) and
#   verbatim (P6) rivals attack the per-field split arithmetic, frozen here. The
#   spirit — "diverge on the expand-vs-keep decision on a sub-domain the F2P
#   input reaches" — is carried by the flag rivals, since on this carrier the
#   expand-vs-keep decision IS the flag threaded into `expandFields`:
#   weak-collector-never-expands keeps a comma name whole under the expansion
#   regime (the P1/expand direction), weak-collector-always-expands splits it
#   under the verbatim regime (the P6/verbatim direction).
#
# ADDED (traversal + second method): weak-collector-drops-last-field attacks the
#   outer traversal (every raw field must be expanded and concatenated) — the one
#   transparent structural clause of the collector beyond the flag, and it moves
#   `raw` to a multi-element list. weak-caller-ignores-flag is the fix's LITERAL
#   discriminating delta on the caller (the pre-patch caller never requested the
#   split); weak-caller-inverts-flag is its near-miss on the verbatim regime.
#   pos-caller-closed-form defends the caller obligation.
#
# RE-AIMED (admissibility): the sibling establishes that the half-permission
#   read-only `name` is readable and a normal return is reachable — a permission
#   fact with no analogue on a referentially-transparent carrier with no `require`
#   clause. Re-aimed to the residual total-domain risk (a degenerate post-image)
#   via an in-region assert pinning the two-field / one-field / zero-field
#   expansion outcomes at concrete F2P-shaped points.
#
# VACUOUS (frame-mutation-write-name): the sibling's mandatory frame-mutation
#   rival writes back into the half-permission read-only `name` and must be
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent; every parameter is an immutable value, no method declares a
#   `mut` binder, there is no heap and no aliasing. No read-only input to
#   overwrite, no permission system to trip — the class is vacuous. No substitute
#   fabricated (per the porting map, legitimately dropped rather than replaced).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses.
#   splitSharedNameFields (multiple, raw): rivals never-expands / always-expands /
#     drops-last-field. `multiple` ∈ {true, false} (both regimes). `raw` ∈
#     {[comma-name field], [two plain fields]} (single vs multi-element). pts = 3.
#   buildParameterFieldSeq (splitNames, raw): rivals ignores-flag / inverts-flag.
#     `splitNames` ∈ {true, false} (both regimes). `raw` ∈ {[x,y field],
#     [p,q field]} (two distinct comma names). pts = 2.
#   Each method's sole `ensures` (the `expandFields` equality) is defended by a
#   positive and attacked by rivals; the collector's flag is attacked from both
#   regimes and its traversal from a multi-field input; the caller's flag is
#   attacked from both regimes. No binder is held fixed across a method's rivals.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the two deep models
#   (`splitOnComma`, `stripWs`) are A-references validated there, and this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
