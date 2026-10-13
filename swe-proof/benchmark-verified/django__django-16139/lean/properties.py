# properties.py — G-PBT falsification battery for django__django-16139 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each SPEC case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, for the reshaped soundness positive, the proof body), so the frozen spec
# (imports / axioms / pure / post-conditions) stays byte-identical, same_spec
# holds by construction, and the single `theorem correct_passwordHelpText`
# STATEMENT is preserved verbatim. No case introduces sorry / admit /
# native_decide / a new axiom or any new theorem/lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts a relative-reference BUILDER over a
# path-segment-id list carrier: it produces a step list and pins it against a
# grounded fold of a current location keyed by an access token, a per-instance
# identifier, a current action and a secondary action, quantified over the
# access token. Its rivals attack that fold — token-keying, pop depth, wrong
# trailing action.
#
# This Lean bundle models the SAME behavioral fix on a MUCH narrower purely
# functional carrier: the per-record help-text computation, i.e. substituting the
# single positional placeholder of a template with the relative URL built from
# the record's own numeric identifier. The load-bearing relation is
#     result = formatFirst template (mkUrl pk)
# where `mkUrl pk` is the grounded three-component relative reference built from
# the record's own identifier and `formatFirst` splices it into the first `{}`.
# The nagini "access token" has no counterpart here at all: this carrier takes
# only the record's own identifier `pk`, so the token/pk-keying distinction the
# nagini token-echo / token-keyed rivals turn on is not expressible. What DOES
# survive is the SHAPE of the reference (`mkUrl`) — its component count, its
# leading parent-directory depth, and its trailing action segment — and the
# preservation of the surrounding template. Every nagini reference-shape rival
# re-expresses as an attack on one of those.
#
# DEFENDED SURFACE (one modeled behavior, two independent facets of the one
# top-level clause `result = formatFirst template (mkUrl pk)`):
#   * URL VALUE — the substituted reference is exactly `mkUrl pk`: two
#     parent-directory steps, then the record's OWN decimal identifier, then the
#     `password` action segment. Wrong pop-depth, a fixed identifier-free
#     reference, or the wrong trailing action all violate it.
#   * TEMPLATE PRESERVATION — the reference is spliced into the FIRST placeholder
#     and every other character of the template is kept in order; an impl that
#     discards the surrounding template violates it.
#   * PLACEHOLDER DISCIPLINE — the reference is consumed ONLY at a placeholder:
#     on a template carrying none, the text comes back untouched. This is the
#     sub-domain on which every reference-shape rival above collapses onto gold,
#     so it is attacked separately (`no-placeholder-append`).
#
# BINDER STRUCTURE. The spec predicate has two input binders: `template`
# (the help-text template carrying one `{}`) and `pk` (the record's own numeric
# identifier). Both are load-bearing and both are varied across the reject
# witnesses: `pk ∈ {5, 7, 3, 2, 9, 1000, 4}` and `template` ranges over several
# distinct shapes ("{}", "a{}b", "x{}", "q{}", "no field"). The seven reject
# witnesses probe seven DISTINCT input tuples (pts=7).
#
# The `template` variation is MEANINGFUL, not two spellings of one point: the
# templates split into three classes with different spec behavior — a bare
# placeholder ("{}"), a placeholder with surrounding text that the preservation
# clause must carry through ("a{}b", "x{}", "q{}"), and a template with NO
# placeholder ("no field"), where `formatFirst` never consumes the replacement at
# all and every reference-shape rival becomes indistinguishable from gold. The
# `pk` variation likewise separates the identity range from the point where a
# derived key diverges (999 agrees, 1000 does not).
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
#     an input carries no heap permission, there is no read-only half-permission
#     to overwrite and no aliasing to exploit. The nagini prefix-write rival has
#     no expressible instance here; no substitute is fabricated.
#   * DIVERGENCE / NON-TERMINATION — nothing to ship, for a reason re-measured
#     with real builds rather than argued. This bundle sets no
#     `loom.semantics.termination` option at all: it is vanilla Lean 4, where
#     totality is enforced by the elaborator itself, so the class is closed from
#     BOTH sides and neither side yields a shippable case.
#       - A plain self-recursive impl with no decreasing measure does not
#         elaborate: `fail to show termination for implementation_passwordHelpText`
#         (exit 1). The variant is rejected by the TERMINATION checker before any
#         obligation is reached, so the rejection attests to Lean's totality
#         requirement and not to this spec — there is no input at which a witness
#         could state a refutation.
#       - Escaping that with `partial def` makes the impl writable (variant_scope
#         bans sorry/axiom/native_decide, not `partial`), but its witness cannot be
#         built: measured, `Tactic 'unfold' failed to unfold
#         'implementation_passwordHelpText'` — a `partial def` has no equation
#         lemma — so the witness never reaches a value comparison and the case
#         would land as `witness-unproven` (inconclusive), not as a finding.
#     The known partial-semantics spec hole is a VELVET phenomenon
#     (`loom.semantics.termination "partial"`), already measured and recorded in
#     `the corpus-wide termination-semantics finding`; it is not re-derived or re-reported here.
#   * TOKEN-KEYED / TOKEN-ECHO rivals (nagini W1 as token-keyed, W5) — the
#     access-token binder itself does not exist on this carrier (only the
#     record's own `pk` is modeled), so token-vs-pk keying is not literally
#     expressible. But W5's LOAD-BEARING content is not the token per se: it is
#     that the substituted identifier may be a DERIVED function of the record's
#     identifier that agrees with it on a sub-domain and diverges outside it.
#     That IS expressible here and is now ported as `derived-identifier-key`
#     below, so the partial-domain / double-mask attack class is no longer
#     dropped. The BEHAVIORAL content of W1 (the pre-patch fixed,
#     identifier-free reference) is ported as `prepatch-fixed-ref`.
#   * ADMISSIBILITY positive — NOT dropped (an earlier revision of this manifest
#     dropped it on the grounds that `correct_passwordHelpText` is an
#     unconditional `∀ template pk` with no precondition hypothesis, so there was
#     "no precondition to prove usable"; that reason is wrong). The absence of a
#     precondition binder is not what makes the lane vacuous: on a TOTAL carrier
#     the analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at
#     exactly an F2P-shaped input, and that is directly testable by discharging
#     the spec predicate at that concrete input BY EVALUATION before closing the
#     frozen obligation verbatim. Ported as `admiss-ground-f2p-shaped` below.
#   * AXIOM_TESTS — dropped: the axiom lane is G-AX's job. The one unchanged
#     callee (positional single-field substitution) is modeled DEEPLY as
#     `formatFirst` (an A-reference validated by G-AX), not consumed as an axiom.
from pathlib import Path

INSTANCE = "django__django-16139"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the impl / proof regions of the frozen
# Solution.lean, each unique in the file.
# ---------------------------------------------------------------------------

# The line that builds the relative reference (impl region). URL-shape rivals
# swap this single line, leaving the substitution + return verbatim so the
# violation is attributable solely to the reference VALUE.
_GOLD_URL = "  let url := mkUrl pk"

# The line that splices the reference into the template (impl region). The
# template-preservation rival swaps this.
_GOLD_SUBST = "  helpText := formatFirst helpText url"

# The full impl body (impl region) and proof body (proof region) — replaced
# together by the soundness positive, which reshapes the impl and therefore
# needs a proof that closes for the new shape.
_GOLD_IMPL_BODY = (
    "  let mut helpText := template\n"
    "  let url := mkUrl pk\n"
    "  helpText := formatFirst helpText url\n"
    "  return helpText"
)
_GOLD_PROOF_BODY = (
    "  intro template pk\n"
    "  unfold problem_spec_passwordHelpText implementation_passwordHelpText\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — structurally different but CORRECT.
# Drops the mutable local and the intermediate binding: inlines the reference
# builder to its definition and returns the substitution directly. Same value,
# different executable shape. `rfl` still closes because both sides reduce to the
# same normal form. Must verify; if a faithful correct reshape cannot satisfy
# `result = formatFirst template (mkUrl pk)`, the spec is SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_IMPL_BODY = (
    "  -- structurally-different correct impl: no mutable local; the reference\n"
    "  -- builder is inlined to its definition and the substitution returned\n"
    "  -- directly. Same value, different shape.\n"
    "  return formatFirst template\n"
    '    ("../../".toList ++ (toString pk).toList ++ "/password/".toList)'
)
_POS_PROOF_BODY = (
    "  intro template pk\n"
    "  unfold problem_spec_passwordHelpText implementation_passwordHelpText mkUrl\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# SECOND POSITIVE CONTROL (soundness) — a reshape that is NOT definitionally
# equal to the frozen impl, so `rfl` genuinely cannot close it.
#
# Why a second one: the positive above inlines `mkUrl` to its own definition, so
# it reduces to the frozen normal form and `rfl` still works. That is an honest
# positive but a WEAK one — it cannot detect a spec that only admits impls
# definitionally equal to the frozen one. This positive replaces `formatFirst`
# with a four-clause traversal carrying an extra singleton clause, so the two
# functions are only EXTENSIONALLY equal: measured, the frozen `rfl` script fails
# against it (`splice template url` is not definitionally equal to
# `formatFirst template (mkUrl pk)`), and it is proven instead by a functional
# induction bridging lemma. If a faithful correct impl of a different recursion
# shape could NOT be proven, the spec would be SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS2_IMPL_BODY = (
    "  -- correct impl whose traversal is only EXTENSIONALLY equal to\n"
    "  -- `formatFirst`: a four-clause match with an extra singleton clause, so\n"
    "  -- the two have different recursion shapes and `rfl` cannot close.\n"
    "  let url := mkUrl pk\n"
    "  return splice template url\n"
    "where\n"
    "  splice : List Char -> List Char -> List Char\n"
    "    | [], _ => []\n"
    "    | [c], _ => [c]\n"
    "    | '{' :: '}' :: rest, r => r ++ rest\n"
    "    | c :: cs, r => c :: splice cs r"
)
_POS2_PROOF_BODY = (
    "  intro template pk\n"
    "  unfold problem_spec_passwordHelpText implementation_passwordHelpText\n"
    "  have key : forall (t r : List Char),\n"
    "      implementation_passwordHelpText.splice t r = formatFirst t r := by\n"
    "    intro t r\n"
    "    fun_induction formatFirst t r with\n"
    "    | case1 => simp [implementation_passwordHelpText.splice]\n"
    "    | case2 => simp [implementation_passwordHelpText.splice]\n"
    "    | case3 c cs repl hne ih =>\n"
    "      cases cs with\n"
    "      | nil => simp [implementation_passwordHelpText.splice, formatFirst]\n"
    "      | cons d ds =>\n"
    "        rw [show implementation_passwordHelpText.splice (c :: d :: ds) repl\n"
    "              = c :: implementation_passwordHelpText.splice (d :: ds) repl from by\n"
    "              conv_lhs => unfold implementation_passwordHelpText.splice\n"
    "              split <;> simp_all]\n"
    "        rw [ih]\n"
    "  simp only [Id.run, key]\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY — non-vacuity of the obligation at F2P-shaped inputs.
#
# The frozen obligation is an unconditional `∀ template pk`, so there is no
# precondition binder to attack directly. On a TOTAL carrier the analogue of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly the shape
# of input the failing test exercises — a spec that no concrete input can
# actually witness. This case discharges the spec predicate BY EVALUATION
# (`decide`) at three concrete F2P-shaped inputs as `have`s, and only then closes
# the frozen obligation verbatim:
#   * a single-digit identifier inside a template whose placeholder is surrounded
#     by prose on BOTH sides (the real help-text shape: text, one `{}`, text);
#   * a MULTI-DIGIT identifier in the same template — the decimal rendering of the
#     identifier is where an unsatisfiable-at-realistic-inputs spec would bite,
#     since a single-digit-only spec would still look fine above;
#   * the placeholder-FREE template, the sub-domain the reject lane attacks, so
#     the obligation is shown satisfiable there too and not merely refutable.
# Impl region untouched; only the proof body grows (the theorem STATEMENT stays
# byte-identical, no new top-level declaration, no assumption token). If any
# `have` failed, the spec would be unsatisfiable at a realistic input.
# ---------------------------------------------------------------------------
def _ground_have(name, tmpl, pk):
    return (
        "  have %s : problem_spec_passwordHelpText\n"
        "      (%s) (%s)\n"
        "      (implementation_passwordHelpText (%s) (%s)) := by\n"
        "    unfold problem_spec_passwordHelpText "
        "implementation_passwordHelpText\n"
        "    decide\n" % (name, tmpl, pk, tmpl, pk))


_F2P_TEMPLATE = '"follow {} to continue".toList'

_ADMISS_PROOF_BODY = (
    "  intro template pk\n"
    + _ground_have("_ground_short", _F2P_TEMPLATE, "1")
    + _ground_have("_ground_multidigit", _F2P_TEMPLATE, "1234")
    + _ground_have("_ground_nofield", '"no field here".toList', "1234")
    + "  unfold problem_spec_passwordHelpText implementation_passwordHelpText\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# UNIQUENESS / REJECT rivals — each swaps ONE impl line, keeping the rest of the
# impl (and the whole spec) verbatim.
# ---------------------------------------------------------------------------

# W-PREPATCH — the pre-patch behavior. A FIXED, identifier-free reference that
# ignores `pk` entirely (one parent step then the action). This is the nagini
# W1 token-keyed rival's behavioral content on this carrier: the produced
# reference does not embed the record's own identifier at all.
_REJ_PREPATCH = '  let url := "../password/".toList'

# W-WRONG-ACTION — correct pop-depth and identifier, but the WRONG trailing
# action segment (ports nagini W4 wrong-action). Correct only on the degenerate
# sub-domain where the two action segments coincide; wrong otherwise.
_REJ_WRONG_ACTION = (
    '  let url := "../../".toList ++ (toString pk).toList ++ "/change/".toList'
)

# W-PARTIAL-POP — one parent-directory step too few (ports nagini W2
# partial-pop). The reference nests under an extra segment instead of replacing
# it; the produced string differs from `mkUrl pk`.
_REJ_PARTIAL_POP = (
    '  let url := "../".toList ++ (toString pk).toList ++ "/password/".toList'
)

# W-OVER-POP — one parent-directory step too many (ports nagini W3 over-pop).
_REJ_OVER_POP = (
    '  let url := "../../../".toList ++ (toString pk).toList ++ "/password/".toList'
)

# W-DERIVED-KEY — the partial-domain / double-mask attack (the expressible core
# of nagini W5). Correct pop-depth and correct trailing action, and the
# identifier IS derived from the record's own identifier — but through a
# reduction that agrees with it only on a sub-domain (small identifiers) and
# diverges above it. Verifying would mean the spec pins the reference only on
# that sub-domain; measured, it does not.
_REJ_DERIVED_KEY = (
    '  let url := "../../".toList ++ (toString (pk % 1000)).toList'
    ' ++ "/password/".toList'
)

# W-NO-FIELD-APPEND — attacks the placeholder clause from the other side: on a
# template that DOES carry a placeholder this rival behaves exactly like gold, so
# every witness above passes it; it diverges only on the placeholder-free
# sub-domain, where it appends the reference instead of returning the template
# unchanged. This is the sub-domain the `prepatch-fixed-ref` rationale was
# silently relying on being untested, so it is now attacked directly.
_REJ_NO_FIELD_APPEND = (
    "  helpText := if template.contains '{' then formatFirst helpText url\n"
    "              else helpText ++ url"
)

# W-DROP-TEMPLATE — builds the CORRECT reference but discards the surrounding
# template, returning the reference alone instead of splicing it into the
# placeholder. Attacks the template-preservation facet. (No direct nagini
# counterpart — nagini's builder returns a bare step list with no surrounding
# template; this rival exercises the carrier-specific preservation clause the
# `formatFirst` model introduces, keeping every top-level facet attacked.)
_REJ_DROP_TEMPLATE = "  helpText := url"


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate directly at a concrete (template, pk)
# input. `decide` closes because both `formatFirst` and the numeral rendering
# reduce on concrete literals. Each witness ELABORATES against its rival
# (the rival's result differs from `formatFirst template (mkUrl pk)`) and FAILS
# against the frozen solution (gold agrees, so the negation is false).
# ---------------------------------------------------------------------------

def _witness(tmpl, pk):
    return (
        "example : ¬ problem_spec_passwordHelpText\n"
        "    (%s) (%s)\n"
        "    (implementation_passwordHelpText (%s) (%s)) := by\n"
        "  unfold problem_spec_passwordHelpText implementation_passwordHelpText\n"
        "  decide" % (tmpl, pk, tmpl, pk)
    )


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness) ------------------------------------
    {
        "id": "pos-control-inlined-direct-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL_BODY, _POS_IMPL_BODY),
            _GOLD_PROOF_BODY, _POS_PROOF_BODY),
        "rationale": (
            "A structurally-different but CORRECT impl: no mutable local and no "
            "intermediate binding; the reference builder is inlined to its "
            "definition and the substitution returned directly. Same value, "
            "different executable shape. The proof unfolds the (now inlined) "
            "reference builder alongside the spec and closes by `rfl` — no new "
            "lemma. It must verify against `result = formatFirst template "
            "(mkUrl pk)`; if a faithful correct reshape cannot satisfy it, the "
            "spec is SPEC-TOO-STRONG."
        ),
    },

    # --- POSITIVE CONTROL #2 (soundness, non-defeq reshape) --------------
    {
        "id": "pos-control-extensional-splice",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL_BODY, _POS2_IMPL_BODY),
            _GOLD_PROOF_BODY, _POS2_PROOF_BODY),
        "rationale": (
            "A CORRECT impl that is only EXTENSIONALLY equal to the frozen one: "
            "the placeholder traversal is a four-clause match with an extra "
            "singleton clause, a different recursion shape. Measured: the frozen "
            "`rfl` script FAILS against this impl (`splice template url` is not "
            "definitionally equal to `formatFirst template (mkUrl pk)`, build "
            "exit 1), so unlike the inlining positive above this one is not "
            "carried by definitional unfolding — it is discharged by an explicit "
            "functional-induction bridging lemma inside the proof region (no new "
            "top-level theorem, no sorry). This is the positive that actually "
            "tests whether the spec admits a faithful impl of a DIFFERENT shape; "
            "if it could not be proven, the spec would be SPEC-TOO-STRONG."
        ),
    },

    # --- ADMISSIBILITY (non-vacuity at F2P-shaped inputs) ----------------
    {
        "id": "admiss-ground-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF_BODY, _ADMISS_PROOF_BODY),
        "rationale": (
            "The frozen obligation is an unconditional `∀ template pk`, so there "
            "is no precondition hypothesis to attack directly — but that is NOT a "
            "reason to drop this lane. On a total carrier the analogue of "
            "PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly "
            "an F2P-shaped input, and this case tests that directly: it discharges "
            "`problem_spec_passwordHelpText` BY EVALUATION (`decide`, no appeal to "
            "the frozen proof script) at three concrete inputs before closing the "
            "frozen obligation verbatim — a single-digit identifier in a template "
            "whose placeholder is surrounded by prose on both sides (the realistic "
            "help-text shape), the same template with a MULTI-DIGIT identifier "
            "(where a spec satisfiable only for single digits would bite), and the "
            "placeholder-free template the reject lane attacks (so that sub-domain "
            "is shown SATISFIABLE, not merely refutable). Only the proof body "
            "grows: the impl region is byte-identical to the frozen one, the "
            "theorem statement is preserved verbatim, and no new top-level "
            "declaration or assumption token appears. If any `have` failed, the "
            "spec would admit no realistic input and the cell would be "
            "PRECOND-TOO-STRONG."
        ),
    },

    # --- UNIQUENESS #1: pre-patch fixed identifier-free reference --------
    {
        "id": "prepatch-fixed-ref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_URL, _REJ_PREPATCH),
        "refinement": (
            "This is the pre-patch behavior: a fixed, identifier-free relative "
            "reference that never embeds the record's own numeric identifier. The "
            "failing test reaches the record's change page by a non-identifier "
            "route and asserts the substituted link resolves to the record's own "
            "identifier-keyed target; a fixed reference resolves elsewhere, so a "
            "faithful patch keeping it would NOT resolve — it is the original bug. "
            "A verifying rival here would be a true verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the URL-value facet of `result = formatFirst template "
            "(mkUrl pk)`: `mkUrl pk` embeds the decimal identifier, whereas this "
            "rival substitutes a constant string independent of `pk`. The results "
            "differ on every template that CARRIES a placeholder (the real "
            "template's shape); on a placeholder-free template `formatFirst` "
            "ignores the replacement entirely, so both agree there and the "
            "refutation must be stated at a template with a `{}` — measured: the "
            "spec HOLDS of this rival at (\"abc\", 5) (build exit 0), so a "
            "witness must not be placed there. Witness at (\"{}\", 5)."
        ),
        # Holds of the rival (constant ref != mkUrl 5), fails on gold.
        "witness": _witness('"{}".toList', "5"),
    },

    # --- UNIQUENESS #2: wrong trailing action segment --------------------
    {
        "id": "wrong-action-segment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_URL, _REJ_WRONG_ACTION),
        "refinement": (
            "Correct pop-depth and identifier, but the trailing action segment "
            "names the wrong action. A faithful patch building the reference to "
            "the wrong action page would send the help-text link to a different "
            "action than the one the failing test resolves against, so it would "
            "NOT resolve. Correct only on the degenerate sub-domains where the "
            "two action segments coincide, or where the template carries no "
            "placeholder at all (in which case the reference is never consumed)."
        ),
        "rationale": (
            "Rejected by the URL-value facet: `mkUrl pk` pins the trailing "
            "segment to the intended action; this rival emits a different "
            "segment, so `formatFirst template (mkUrl pk)` differs from the "
            "rival's result. Witness at (\"a{}b\", 7)."
        ),
        # Holds of the rival (wrong trailing segment), fails on gold.
        "witness": _witness('"a{}b".toList', "7"),
    },

    # --- UNIQUENESS #3: partial pop (one parent step too few) ------------
    {
        "id": "partial-pop-shallow-ref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_URL, _REJ_PARTIAL_POP),
        "refinement": (
            "One parent-directory step too few. A faithful patch with this "
            "reference nests the target under an extra path segment instead of "
            "replacing it, producing an invalid location the failing test does "
            "not resolve against — so it would NOT resolve."
        ),
        "rationale": (
            "Rejected by the URL-value facet: the reference built by this rival "
            "has one fewer leading parent-directory step than `mkUrl pk`, so the "
            "substituted string differs. Witness at (\"{}\", 3)."
        ),
        # Holds of the rival (one fewer '../'), fails on gold.
        "witness": _witness('"{}".toList', "3"),
    },

    # --- UNIQUENESS #4: over-pop (one parent step too many) --------------
    {
        "id": "over-pop-deep-ref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_URL, _REJ_OVER_POP),
        "refinement": (
            "One parent-directory step too many. A faithful patch with this "
            "reference pops above the intended base, dropping a shared path "
            "segment, so the resolved location is not the record's target and it "
            "would NOT resolve. The complementary boundary to the partial-pop "
            "rival."
        ),
        "rationale": (
            "Rejected by the URL-value facet: the reference has one MORE leading "
            "parent-directory step than `mkUrl pk`, so the substituted string "
            "differs. Witness at (\"x{}\", 2) — a distinct point and template "
            "shape from the partial-pop rival."
        ),
        # Holds of the rival (one extra '../'), fails on gold.
        "witness": _witness('"x{}".toList', "2"),
    },

    # --- UNIQUENESS #5: discards the surrounding template ----------------
    {
        "id": "drop-template-context",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_SUBST, _REJ_DROP_TEMPLATE),
        "refinement": (
            "Builds the CORRECT reference but returns it alone, discarding the "
            "surrounding template text (the anchor markup and prose the help text "
            "is embedded in). A faithful patch that replaced the whole help text "
            "with the bare reference would drop the rendered link markup the "
            "template supplies, so the field's help text would not render the "
            "intended link and it would NOT resolve/render as the test expects."
        ),
        "rationale": (
            "Rejected by the template-preservation facet of `result = "
            "formatFirst template (mkUrl pk)`: the spec keeps every non-"
            "placeholder character of the template in order and splices the "
            "reference into the first placeholder, whereas this rival returns the "
            "reference alone. Witness at (\"a{}b\", 9), whose surrounding "
            "characters 'a' and 'b' are dropped."
        ),
        # Holds of the rival (bare url != "a" ++ url ++ "b"), fails on gold.
        "witness": _witness('"a{}b".toList', "9"),
    },

    # --- UNIQUENESS #6: derived-identifier key (partial domain) ----------
    {
        "id": "derived-identifier-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_URL, _REJ_DERIVED_KEY),
        "refinement": (
            "The reference has the right depth and the right trailing action, and "
            "its identifier IS derived from the record's own identifier — but "
            "through a reduction that agrees with it only for small identifiers. "
            "A faithful patch that keyed the link by a reduced/truncated form of "
            "the record's identifier would resolve correctly on the small-record "
            "sub-domain a test fixture usually occupies, and silently resolve to a "
            "DIFFERENT record's target once identifiers grow past the reduction's "
            "range — so it would NOT resolve in general. This is the "
            "partial-domain / double-mask class: the most dangerous kind of wrong "
            "impl, because it passes the obvious cases."
        ),
        "rationale": (
            "Rejected by the URL-value facet: the spec pins the substituted "
            "identifier to `toString pk` for EVERY `pk`, not merely on a "
            "sub-domain, so any reduction of `pk` that is not the identity "
            "violates it above the reduction's range. Measured: the rival's build "
            "of the spec at an AGREEMENT point (\"q{}\", 999) succeeds (exit 0), "
            "confirming the case is a genuine partial-domain rival rather than a "
            "uniformly-wrong one; the witness is therefore placed strictly above "
            "the agreement range, at (\"q{}\", 1000)."
        ),
        # Holds of the rival (1000 % 1000 = 0 != 1000), fails on gold.
        "witness": _witness('"q{}".toList', "1000"),
    },

    # --- UNIQUENESS #7: placeholder-free sub-domain ----------------------
    {
        "id": "no-placeholder-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_SUBST, _REJ_NO_FIELD_APPEND),
        "refinement": (
            "Indistinguishable from a faithful impl on every template that "
            "carries a placeholder, so it passes all five reference-shape "
            "witnesses above; it diverges only where the template has no "
            "placeholder, appending the reference instead of leaving the text "
            "alone. A faithful patch behaving this way would tack a stray "
            "relative reference onto the end of any help text that carried no "
            "substitution field, emitting text the field is not supposed to "
            "contain — the rendered help text would not match what a test "
            "asserting on the field's exact text expects."
        ),
        "rationale": (
            "Rejected by the placeholder clause: `formatFirst` returns the "
            "template UNCHANGED when there is no `{}` (its `[]` and no-brace "
            "clauses never consume the replacement), whereas this rival appends "
            "the reference. This case exists because the placeholder-free "
            "sub-domain is the one every other reject witness leaves untouched — "
            "measured, the spec HOLDS of the pre-patch rival at (\"abc\", 5) — so "
            "without it the spec's behavior on that sub-domain would be attested "
            "by nothing. Witness at (\"no field\", 4), a template with no "
            "placeholder and a distinct identifier."
        ),
        # Holds of the rival (template ++ url != template), fails on gold.
        "witness": _witness('"no field".toList', "4"),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# The one unchanged callee (positional single-field template substitution) is
# modeled DEEPLY as `formatFirst` (an A-reference validated == the real callee by
# G-AX), and the changed reference expression is reconstructed deeply as `mkUrl`;
# the proof consumes no opaque callee contract.
AXIOM_TESTS = []
