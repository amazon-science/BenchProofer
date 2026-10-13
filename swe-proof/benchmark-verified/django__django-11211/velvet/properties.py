"""properties.py — G-PBT falsification battery for django__django-11211 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (``preparedValue (value : Val) return (out : Val)``): prepare a
field value for use as a relational lookup key by composing a base preliminary
coercion with a normal-form conversion, so distinct accepted transcriptions of
the same datum yield the SAME prepared key. One input binder, ``value``; one
``require`` and two ``ensures``:

    (R1) require   WellFormed value                 -- domain restriction
    (P1) ensures   out = canonicalize value         -- the load-bearing clause
    (P2) ensures   canonicalize out = out           -- the result is canonical

THE ORACLE IS AXIOM-PINNED; THE CARRIER IS NOT. Both post clauses are equalities
against the axiom ``canonicalize`` (``Val → Val``), whose only pinned property is
idempotence on well-formed input; ``WellFormed`` is an uninterpreted predicate;
``preCoerce`` is pinned by ``preCoerce_id``. So the oracle is opaque — no literal
decides an equation about it. ``Val`` ITSELF IS NOT: it is an ``inductive`` with
four constructors, fully case-analysable, and a rival may branch on it. An
earlier revision of this file called ``Val`` "an opaque carrier ... with no
exposed facets" and dropped a rival class on that basis; that was wrong, and
``reject-rewrap-textual`` is the case the mistaken premise had excluded.

There is no executable content, so the tester+``decide`` witness route
(``derive_tester_for`` → ``…Tester args = false``) is UNAVAILABLE:
``preparedValue`` depends on the non-computable ``canonicalize``, and extraction
fails with "no executable code". That does NOT make the reject lane empty. An
axiom-pinned term has no VALUE to compute, but it is still a term one can
QUANTIFY over. Every reject rival below is refuted by CONDITIONING ON THE
ORACLE: the Hoare triple is refuted at a point described by hypothesis (e.g.
``hne : canonicalize v ≠ v``), so the refutation holds exactly on the sub-domain
where the rival diverges from the spec — a STRONGER statement than any single
literal input could make.

Each witness must be shape-agnostic, and this is not a stylistic point: it is
what separates a real refutation from a hollow one. A witness that navigates the
weakest-precondition term by hand (``rw [triple, wp_bind, ...]`` then a
projection path) fails against the frozen solution because gold's MONADIC SHAPE
differs from the rival's, not because gold satisfies the spec — and both of this
battery's original witnesses did exactly that, one of them failing identically
for a claim and its own negation. Each witness below instead normalises with
``simp only`` (which cannot fail for want of a pattern) and closes with
``simp_all``. Verified per case: ELABORATES against the rival (EXIT 0); FAILS
against the frozen solution with ``unsolved goals ... ⊢ False`` (EXIT 1 — a
semantic refutation, gold leaving no contradiction to derive); the FLIPPED-CLAIM
forgery VERIFIES against gold (EXIT 0), proving the exit code tracks the claim;
and the same failure appears against two correct RESHAPES, proving it
discriminates wrongness rather than shape. Hypotheses are jointly satisfiable
(the ``example … : False`` consistency probe leaves ``False`` unsolved for all
three), so none is a contradiction-forgery.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries two
    MANDATORY framing rivals (overwrite the read-only input's ``key`` / both
    facets, then return it) because its input is held at a fractional heap
    permission ``Acc(value.key,1/2)`` an impl can illegally WRITE. Lean and
    Velvet are referentially transparent: ``value`` is an immutable value, this
    bundle declares no ``mut`` binder, there is no heap and no aliasing — so
    there is no read-only input to overwrite and no substitute probe to build.
    Demonstrated rather than asserted: the impl region cannot express an
    assignment to ``value`` at all, and the frozen ``prove_correct`` goal
    contains no permission obligation — only the two ``ensures``.
  * PARTIAL-DOMAIN / VALUE rivals (drop the normal-form conversion; keep the raw
    datum; fabricate a constant key) — the nagini uniqueness rivals live here,
    all attacking the discriminating clause on the non-canonical sub-domain.
    They PORT, all three: each is re-expressed against the frozen spec and
    refuted by conditioning on ``canonicalize`` at the exact point where the
    rival's returned value differs from the canonical representation. See the
    three ``reject-*`` cases, which condition at three DISTINCT points (a
    non-canonical datum, a fabricated constant, and the F2P constructor shape).
  * UNGROUNDED-ORACLE ECHO — N/A as an ATTACK. ``canonicalize`` IS the
    axiom-pinned oracle here; its behaviour is pinned by the ``axioms`` region
    and validated executably by G-AX (axiom_check.py). We carry an honest
    cheapest-reshape POSITIVE CONTROL (``pos-*``) instead of a wrong echo.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries two
axiom-soundness / containment probes over the real stdlib+repo callees; that is
G-AX's job (axiom_check.py / mapping.md) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11211"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the two comment lines and
# ---- the three statements). It lies wholly inside the single
# ---- -- impl-start .. -- impl-end region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so each edit keeps same_spec by
# ---- construction and leaves the frozen `prove_correct` statement intact.
_IMPL = (
    "    -- Put the value through the base preliminary coercion, then the field's\n"
    "    -- normal-form conversion; return the canonical representation.\n"
    "    let prepped :| prepped = preCoerce value\n"
    "    let canon  :| canon  = canonicalize prepped\n"
    "    return canon"
)


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- WITNESSES. The spec is a `method` CONTRACT whose two post clauses are
# ---- equalities against the axiom-pinned `canonicalize`, so a witness cannot go
# ---- through the tester machinery (extraction fails on `canonicalize`, which
# ---- has no executable code). Each witness instead refutes the method's Hoare
# ---- triple DIRECTLY at a point described by hypothesis — conditioning on
# ---- `canonicalize` so the disequality holds exactly where the rival diverges.
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict; the reduction lemmas (`triple`,
# ---- `wp_bind`, `wp_pure`, `MonadNonDet.wp_pickSuchThat`, `loomLogicSimp`,
# ---- `preCoerce_id`, `canonicalize_idem`) all come from the frozen
# ---- `Velvet.Std` import and the frozen axioms region, so nothing extra is
# ---- imported.
#
# ---- SHAPE-AGNOSTIC BY CONSTRUCTION, and this is the load-bearing property.
# ---- An earlier revision of this battery navigated the weakest-precondition
# ---- term by hand (`rw [triple, wp_bind, MonadNonDet.wp_pickSuchThat]`, then
# ---- `exact hne hval.1.symm`). Those witnesses DID satisfy both halves of the
# ---- gate's check — exit 0 on the rival, exit 1 on the frozen solution — but
# ---- the gold-side exit code carried NO information about the claim, because
# ---- the `rw` chain and the projection path are tuned to the rival's OWN
# ---- monadic shape. Measured, on this cell:
# ----   * the drop witness failed on gold with `Invalid field 'symm': the
# ----     environment does not contain 'Decidable.rec.symm'`, and failed with
# ----     the BYTE-IDENTICAL message against a deliberately WRONG impl that
# ----     merely shares gold's two-bind shape (`return prepped`) — so the error
# ----     tracked the number of `:|` binds, not correctness;
# ----   * the const witness failed on gold with `Tactic 'rewrite' failed: did
# ----     not find an occurrence of the pattern wp (pure ?x) ?post`, i.e. gold
# ----     simply has a `bind` where the rival has a `pure`. A FORGERY asserting
# ----     the OPPOSITE claim (the same statement with the `¬` dropped, i.e.
# ----     "gold IS correct here") failed on gold with the same rewrite error,
# ----     modulo the `¬` echoed in the printed goal. A witness claiming gold is
# ----     CORRECT would therefore have been recorded as a refutation.
# ---- Both witnesses below instead NORMALISE the triple with `simp only` (which
# ---- cannot fail for want of a pattern) and then close by `simp_all`, so the
# ---- build's verdict depends only on whether the residual arithmetic over
# ---- `canonicalize` is contradictory. Re-measured: each elaborates against its
# ---- rival (exit 0), fails on gold with `unsolved goals ... ⊢ False` (exit 1 —
# ---- a SEMANTIC refutation: gold leaves nothing to contradict), and the
# ---- flipped-claim forgery now VERIFIES against gold (exit 0), which is what
# ---- proves the exit code tracks the claim. Each also fails identically
# ---- against two correct RESHAPES (the merge positive and a bare-`return`
# ---- composition), confirming it discriminates wrongness rather than shape.

# drop-the-conversion rival: returns the value straight through the base
# coercion (`preCoerce value`, which by `preCoerce_id` is `value`) WITHOUT the
# normal-form conversion. Its output is `value`; the post-image demands
# `canonicalize value`. Refuted wherever the datum is NOT already canonical
# (`canonicalize v ≠ v`) — the exact sub-domain the fix exists for.
_NORM = (
    "  unfold preparedValue\n"
    "  simp only [triple, wp_bind, wp_pure, MonadNonDet.wp_pickSuchThat,\n"
    "    typeWithName, loomLogicSimp, preCoerce_id]\n"
    "  simp_all [canonicalize_idem]\n"
)

_W_DROP = (
    "example (v : Val) (hw : WellFormed v) (hne : canonicalize v ≠ v) :\n"
    "    ¬ triple (l := Prop) (WellFormed v) (preparedValue v)\n"
    "        (fun out => out = canonicalize v ∧ canonicalize out = out) := by\n"
) + _NORM

# fabricated-constant rival: returns a fixed value (`Val.absent`) regardless of
# the input. Faithful on no non-trivial input; the post-image demands
# `canonicalize value`. Refuted wherever `canonicalize v ≠ Val.absent` — a
# DIFFERENT conditioning point from the drop rival, so the two witnesses probe
# distinct sub-domains of the same clause rather than the same input. The
# disequality is oriented `Val.absent ≠ canonicalize v` to match the residual
# goal the normalisation leaves, so `simp_all` closes it without a `.symm` step
# (a projection path would reintroduce shape-dependence).
_W_CONST = (
    "example (v : Val) (hw : WellFormed v)\n"
    "    (hne : Val.absent ≠ canonicalize v) :\n"
    "    ¬ triple (l := Prop) (WellFormed v) (preparedValue v)\n"
    "        (fun out => out = canonicalize v ∧ canonicalize out = out) := by\n"
) + _NORM

# constructor-domain rival (NEW — added by the audit; see attack D below): the
# rival rebuilds a TEXTUAL transcription as a concrete value by re-wrapping its
# payload, instead of putting it through the normal-form conversion. This is the
# F2P-shaped input (a textual transcription of a freshly generated identifier),
# and it is the one sub-domain the other two rivals leave unattacked: both of
# them are refuted at a `v` described only by a disequality, so neither says
# anything about a particular constructor. Refuted wherever re-wrapping is not
# the conversion (`Val.concrete s ≠ canonicalize (Val.textual s)`).
_W_REWRAP = (
    "example (s : List Char) (hw : WellFormed (Val.textual s))\n"
    "    (hne : Val.concrete s ≠ canonicalize (Val.textual s)) :\n"
    "    ¬ triple (l := Prop) (WellFormed (Val.textual s))\n"
    "        (preparedValue (Val.textual s))\n"
    "        (fun out => out = canonicalize (Val.textual s)\n"
    "          ∧ canonicalize out = out) := by\n"
) + _NORM


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # pos-control-branch-reshape ARGUMENT ("a faithful reshape that still
    # consumes both A-consumed callees must verify") onto this carrier. The
    # nagini reshape branches on `is_none`; `Val` here is opaque with no
    # exposed emptiness observation, so the faithful cheap reshape that DOES
    # survive is COLLAPSING the two `:|` choice binds into a single canonical
    # choice over the composed callees. Both callees are still consumed, the
    # returned value is unchanged, so P1/P2 discharge exactly as for gold.
    # =====================================================================
    {
        "id": "pos-control-compose-merge",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    -- reshape: compose the base coercion and the normal-form\n"
            "    -- conversion in a single canonical choice.\n"
            "    let canon :| canon = canonicalize (preCoerce value)\n"
            "    return canon"),
        "rationale": "PASS SOURCE = P1/P2. Collapsing the two `:|` choice binds "
                     "into a single `canonicalize (preCoerce value)` choice keeps "
                     "both A-consumed callees and returns the same canonical "
                     "value, so `out = canonicalize value` (P1) and "
                     "`canonicalize out = out` (P2) still discharge (via "
                     "preCoerce_id and canonicalize_idem). A structurally- "
                     "different faithful reshape MUST verify; if it cannot, the "
                     "postcondition over-constrains a faithful impl "
                     "(SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — ported from nagini admiss-textual-form-caller, now with
    # an actual PROBE. The previous revision of this case set
    # `module = _BASE`, i.e. it re-built the frozen file byte-for-byte and
    # asserted it verifies. That is not an admissibility test: the frozen
    # solution's own build already establishes it, so the case could not fail
    # for any reason a repair could act on, and it passed while testing
    # NOTHING. The audit replaced it with the shape the lane exists for.
    #
    # The nagini case builds an F2P-shaped Value (is_none=False, canon!=key)
    # and asserts the discriminating guarantee holds for it. The analogue here:
    # `Val` is an INDUCTIVE, not an opaque type, so the F2P-shaped input IS
    # constructible — `Val.textual s`, a textual transcription of a freshly
    # generated identifier, which is exactly what the failing scenario feeds.
    # The probe discharges the two load-bearing obligations AT that concrete
    # input shape, by evaluation, as `have`s inside the impl region, BEFORE
    # closing the frozen obligation verbatim. It verifies iff the axioms are
    # satisfiable at an F2P-shaped input; if the precondition could not be
    # established there, or the callee contracts were unusable at that shape,
    # this fails => PRECOND-TOO-STRONG. The `have`s are real obligations (they
    # are proved from `preCoerce_id` / `canonicalize_idem`, not assumed), and
    # they live wholly inside the impl region so the spec view is untouched.
    # =====================================================================
    {
        "id": "admiss-textual-form-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(
            "    -- admissibility probe: the F2P-shaped input is a TEXTUAL\n"
            "    -- transcription of a freshly generated identifier. Discharge the\n"
            "    -- two load-bearing callee obligations AT that concrete input\n"
            "    -- shape before doing the work, so a precondition or callee\n"
            "    -- contract unusable there would fail this case.\n"
            "    have hpre : ∀ s : List Char,\n"
            "        preCoerce (Val.textual s) = Val.textual s :=\n"
            "      fun s => preCoerce_id _\n"
            "    have hprobe : ∀ s : List Char, WellFormed (Val.textual s) →\n"
            "        canonicalize (canonicalize (Val.textual s))\n"
            "          = canonicalize (Val.textual s) :=\n"
            "      fun s hs => canonicalize_idem _ hs\n"
            "    let prepped :| prepped = preCoerce value\n"
            "    let canon  :| canon  = canonicalize prepped\n"
            "    return canon"),
        "rationale": "PASS SOURCE = R1 admits the F2P-shaped input, and the "
                     "callee contracts are usable AT that shape. The probe "
                     "instantiates both axioms at a textual transcription "
                     "(`Val.textual s`) — the input shape the failing scenario "
                     "actually prepares — proving the base coercion is the "
                     "identity there and that the conversion is idempotent "
                     "there, then closes the frozen obligation unchanged. If "
                     "`WellFormed` could not hold of that shape, or the axioms "
                     "did not apply to it, the precondition would exclude a "
                     "normal input => PRECOND-TOO-STRONG. Distinct from the "
                     "soundness positive: that one varies the impl SHAPE, this "
                     "one pins the input DOMAIN.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected. Each carries a machine-checked refutation witness that
    # CONDITIONS on the opaque `canonicalize` at the point where the rival
    # diverges, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "reject-drop-canonicalize",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the value through the base coercion only, dropping the
        # normal-form conversion. `preCoerce value = value` (preCoerce_id), so
        # the output is the input unchanged.
        "module": _with_impl(
            "    -- partial-domain: base coercion only, NO normal-form\n"
            "    -- conversion. Faithful for a datum already in canonical form;\n"
            "    -- wrong for any transcription whose form differs from it.\n"
            "    let out :| out = preCoerce value\n"
            "    return out"),
        "refinement": "Skipping the normal-form conversion is the PRE-FIX shape "
                      "(the value flows through the base coercion only, keeping "
                      "its as-stored form). A faithful real patch of this shape "
                      "leaves a transcription keyed by itself rather than by the "
                      "canonical datum, so the relational lookup that pairs a "
                      "key derived from one transcription with a value derived "
                      "from another still misses and the failing test still "
                      "observes the empty result. It would NOT resolve.",
        "rationale": "REJECT from P1 (`out = canonicalize value`): the impl "
                     "returns `value`, and at any datum not already in canonical "
                     "form `value ≠ canonicalize value`. The same divergence "
                     "falsifies P2 there (`canonicalize value = value` is false). "
                     "Refuted by conditioning on `canonicalize v ≠ v` — the "
                     "sub-domain the fix exists for.",
        "witness": _W_DROP,
    },
    {
        "id": "reject-constant-return",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the input entirely and return a fixed value. Attacks P1 at a
        # DIFFERENT conditioning point (canonicalize v ≠ Val.absent) than the
        # drop rival, so the two witnesses do not collapse onto one input.
        "module": _with_impl(
            "    -- fabricated key: ignore the input and return a fixed value.\n"
            "    -- The prepared key is invented, not derived from the datum.\n"
            "    return Val.absent"),
        "refinement": "Returning a fixed key regardless of the datum cannot "
                      "match the value it is supposed to be prepared from except "
                      "at the single input that already IS that fixed value; a "
                      "faithful real patch that hard-coded the prepared key "
                      "would break the relational lookup for every real datum "
                      "and would NOT resolve the failing test.",
        "rationale": "REJECT from P1 (`out = canonicalize value`): the impl "
                     "returns the constant `Val.absent`, so for any datum whose "
                     "canonical form is not `Val.absent` the post-image is "
                     "violated. Refuted by conditioning on "
                     "`canonicalize v ≠ Val.absent`, a distinct point from the "
                     "drop rival's `canonicalize v ≠ v`.",
        "witness": _W_CONST,
    },

    # =====================================================================
    # NEW (added by the audit). The two rivals above are both refuted at a
    # `v` described only by a disequality, so neither attests anything about a
    # particular CONSTRUCTOR of `Val` — and `Val` is an inductive, so the
    # constructor-level sub-domain is reachable and was left unattacked. This
    # rival is the near-miss that shape admits: for a textual transcription it
    # rebuilds the datum as a concrete value by RE-WRAPPING the payload,
    # instead of putting it through the normal-form conversion, and falls back
    # to the correct composition on every other shape. So it is faithful
    # everywhere EXCEPT the F2P input shape — the hardest kind of wrong impl
    # for a spec to catch, and the one this lane exists to find.
    # =====================================================================
    {
        "id": "reject-rewrap-textual",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(
            "    -- near-miss: for a textual transcription, rebuild the datum as a\n"
            "    -- concrete value by re-wrapping its payload rather than running\n"
            "    -- the normal-form conversion; correct composition elsewhere.\n"
            "    match value with\n"
            "    | Val.textual s => return Val.concrete s\n"
            "    | _ =>\n"
            "      let canon :| canon = canonicalize (preCoerce value)\n"
            "      return canon"),
        "refinement": "Re-labelling a transcription as though it were already "
                      "the canonical datum, instead of converting it, produces a "
                      "key that carries the transcription's own payload. A "
                      "faithful real patch of this shape would pair a key built "
                      "from one transcription against a stored value built from "
                      "another and still mismatch, so the failing test would "
                      "still observe the empty result. It would NOT resolve — "
                      "and being correct on every OTHER input shape is exactly "
                      "why it needs its own case.",
        "rationale": "REJECT from P1 (`out = canonicalize value`) restricted to "
                     "the textual sub-domain: the impl returns `Val.concrete s` "
                     "for input `Val.textual s`, but the spec demands "
                     "`canonicalize (Val.textual s)`, and nothing in the axioms "
                     "makes re-wrapping the payload equal to the conversion. P2 "
                     "fails there too, since `Val.concrete s` is not pinned as a "
                     "fixed point. Refuted by conditioning on "
                     "`Val.concrete s ≠ canonicalize (Val.textual s)` — a "
                     "CONSTRUCTOR-level point neither other rival reaches.",
        "witness": _W_REWRAP,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING (revised by the audit pass; see CORRECTIONS).
#
#   nagini case                       -> here
#   -----------------------------------------------------------------------
#   pos-control-branch-reshape        -> pos-control-compose-merge     PORTED
#   admiss-textual-form-caller        -> admiss-textual-form-input     PORTED
#   frame-mutate-write-input-key      -> (none)                        VACUOUS
#   frame-mutate-write-input-both     -> (none)                        VACUOUS
#   partial-domain-drop-canonicalize  -> reject-drop-canonicalize      PORTED
#   partial-domain-keep-raw-key       -> reject-rewrap-textual         PORTED
#   support-fabricated-zero-key       -> reject-constant-return        PORTED
#
# 5 ported, 2 vacuous = 5 velvet cases (2 verify, 3 reject).
#
# CORRECTIONS MADE BY THE AUDIT PASS. Three defects were found behind a recorded
# SOUND; all three are fixed above.
#
# (1) BOTH REJECT WITNESSES WERE HOLLOW. They satisfied the gate (exit 0 on the
#     rival, exit 1 on gold) but gold's exit code carried no information about
#     the CLAIM, because each navigated the weakest-precondition term by hand and
#     so failed on gold for a SHAPE reason. Measured: the drop witness produced a
#     byte-identical `Invalid field 'symm' ... Decidable.rec.symm` against gold
#     AND against a deliberately WRONG impl sharing gold's two-bind shape, so the
#     error tracked the bind count; the const witness produced
#     `Tactic 'rewrite' failed ... wp (pure ?x) ?post` on gold, and the FORGERY
#     asserting the OPPOSITE claim produced the same rewrite failure. A witness
#     claiming gold is CORRECT would have been recorded as a refutation. Repaired
#     by normalising with `simp only` (cannot fail for want of a pattern) and
#     closing with `simp_all`: each witness now fails on gold with `unsolved
#     goals ... ⊢ False` (a semantic refutation), and the flipped-claim forgery
#     VERIFIES against gold (exit 0), so the exit code tracks the claim.
#
# (2) THE ADMISSIBILITY CASE WAS A NO-OP. It set `module = _BASE`, re-building the
#     frozen file byte-for-byte and asserting it verifies — something the frozen
#     solution's own build already establishes. It could not fail for any reason a
#     repair could act on. Replaced by a real probe over the F2P-shaped input.
#
# (3) THE CONSTRUCTOR SUB-DOMAIN WAS UNATTACKED, on a FALSE PREMISE. The prior
#     revision asserted repeatedly that `Val` is "an opaque carrier" with "no
#     exposed facets", and dropped/merged cases on that basis. `Val` is an
#     `inductive` with four constructors: it is opaque only in the sense that the
#     axioms say nothing about its payloads, but it is fully case-analysable, and
#     a rival MAY branch on it (`match value with | Val.textual s => ...`).
#     `reject-rewrap-textual` is the case that premise had excluded.
#
# PORTED (positive control): the nagini reshape branches on `is_none` and names a
#   local. There is no emptiness OBSERVATION on `Val` (no axiom relates a
#   constructor to the conversion), so the exact branch-split carries no argument
#   here; the faithful cheap reshape carrying the SAME argument is collapsing the
#   two `:|` choice binds into one canonical choice. Verified: exit 0.
# PORTED (admissibility): nagini admiss-textual-form-caller asserts the
#   discriminating guarantee for a concrete F2P-shaped input. That DOES port —
#   `Val.textual s` is constructible — so the case now instantiates both callee
#   axioms at that shape as `have`s before closing the frozen obligation. What
#   does not port is asserting a VALUE for the prepared key: the axioms pin the
#   conversion's fixed-point behaviour, not its bytes, so the probe asserts the
#   obligations that are actually available at that input rather than a literal.
# PORTED (reject-drop-canonicalize): the pre-fix behaviour (base coercion, no
#   normal-form conversion). The rival returns `preCoerce value` (= `value`); its
#   output diverges from `canonicalize value` on every non-canonical datum.
#   Refuted by conditioning on `canonicalize v ≠ v`.
# PORTED (reject-rewrap-textual): nagini's "preserve the metadata but keep the raw
#   key" rival. The prior revision MERGED this as inexpressible, reasoning that
#   `Val` has "no exposed facets" so it collapses onto returning the value
#   unchanged. That was wrong — see correction (3). The faithful analogue rebuilds
#   a textual transcription as a concrete value by re-wrapping its payload, which
#   is a DIFFERENT impl from the drop rival (it is correct on the absent, concrete
#   and numeric shapes and wrong only on the textual one) and is refuted at a
#   constructor-level point neither other witness reaches.
# PORTED (reject-constant-return): nagini support-fabricated-zero-key fabricates a
#   constant join key. Here the rival returns the constant `Val.absent`, ignoring
#   the input. Refuted by conditioning on `Val.absent ≠ canonicalize v`, a
#   DIFFERENT point from the drop rival.
# VACUOUS (the two frame/permission rivals): nagini carries these as MANDATORY
#   because `value` is held at a fractional heap permission Acc(value.key,1/2) an
#   impl can illegally WRITE. This backend is referentially transparent and
#   declares no `mut` binder, so `value` is an immutable value with no heap
#   footprint — there is no read-only input to overwrite and no substitute probe
#   to build. Demonstrated, not assumed: the impl region cannot even express an
#   assignment to `value`, and no permission obligation appears in the frozen
#   `prove_correct` goal (the only goals are the two `ensures`).
#
# CLAUSE / BINDER COVERAGE. Binder `value`: the three reject witnesses quantify
#   over it at three distinct points — `canonicalize v ≠ v` (non-canonical
#   sub-domain), `Val.absent ≠ canonicalize v` (fabricated-constant point), and
#   `Val.concrete s ≠ canonicalize (Val.textual s)` (the F2P constructor shape).
#   Clause P1 (`out = canonicalize value`): attacked by all three. Clause P2
#   (`canonicalize out = out`): not INDEPENDENTLY attackable — P1 pins `out`
#   exactly to `canonicalize value`, after which P2 follows from
#   canonicalize_idem, so any P2-violating impl also violates P1. Confirmed by
#   construction rather than asserted: an impl returning `Val.concrete s` fails
#   BOTH clauses at that input, and the audit found no impl failing P2 alone.
#   P2 is therefore defended as a dependent clause.
#
# SPEC-STRENGTH PROBES RUN BY THE AUDIT (attacks D and E), none of which found a
#   hole. Correct reshapes that VERIFY (exit 0), confirming the spec is not
#   over-strong: dropping the `preCoerce` call entirely (sound, since
#   `preCoerce_id` makes it the identity); swapping the two callees' order;
#   applying the conversion twice; a bare `return canonicalize (preCoerce
#   value)` with no `:|` bind. Wrong impls that are correctly REJECTED (exit 1):
#   returning the un-canonicalized intermediate under gold's own bind shape;
#   assuming the absent shape is its own canonical form; fabricating
#   `Val.concrete []`; the re-wrap near-miss now shipped as a case. The
#   divergence lane is NOT probed by these attacks: vacuous verification is the
#   `partial` disposition, and this bundle is `total`, under which a diverging
#   rival is REJECTED (an omitted `decreasing` clause is a hard error, and a
#   clause whose measure does not shrink fails its own descent goal).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py); the G-PBT
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
