# properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14983
# (lean backend).
#
# NOT a Lean module: a manifest the G-PBT runner parses and stamps with a
# RECORDED verdict. Each SPEC_TESTS case is a complete `Solution.lean` variant
# built by region surgery — it edits ONLY the impl region (and, for the reshaped
# soundness positives, the proof body), so the frozen spec (docstring / axioms /
# pure helpers / post-conditions) stays byte-identical, `same_spec` holds by
# construction, and the `theorem correct_reprString` STATEMENT is preserved
# verbatim. No case introduces `sorry` / `admit` / `native_decide` / a new
# `axiom` / a new `theorem` or `lemma`; every positive reproves the SAME
# obligation for its new impl shape.
#
# ---------------------------------------------------------------------------
# PORT NOTE — carrier narrowing against the nagini sibling
# ---------------------------------------------------------------------------
# The nagini battery attacks a SCALAR per-parameter value resolver: one integer
# result from (direct attribute, null sentinel, auxiliary-map-present flag,
# auxiliary map, name). This Lean bundle models a WIDER surface — the whole
# constructor-style summary STRING built by mapping that same per-parameter
# resolution over an ordered list of parameter names and joining the rendered
# results — and then the justified LAYOUT of those rendered results inside the
# class name and parentheses. So every nagini value-level rival ports (the
# resolution is still there, now under a traversal), and the widened carrier adds
# four attack classes nagini's scalar carrier could not express: the traversal
# ORDER, the separator/assembly shape, the per-value RENDERING, and the LAYOUT
# (where the lines break, how far the continuations indent, and the elision of an
# over-long rendered parameter). The port therefore lands at 17 cases against
# nagini's 7 ported spec cases — carrier WIDENING here, not parity chasing.
#
# AUDIT NOTE (independent re-derivation of this manifest). The port as first
# written claimed the per-value rendering as one of its three new attack
# classes but shipped no rival against it: `pyRepr` is a three-branch function
# (integer decimal / `None` / single-quoted text) and every rival left it
# byte-identical, so a wrong impl was free to mis-render a text value or the
# null sentinel and no case would have noticed — a claimed attack class with no
# case behind it. Two rivals were ADDED to close it (clause C7 below), each
# machine-checked to hold of its rival and to be refuted semantically against
# the frozen solution.
#
# SECOND AUDIT NOTE (independent adversarial re-derivation). All ten reject
# witnesses were rebuilt from scratch on both subjects: each ELABORATES against
# its rival (exit 0) and FAILS against the frozen solution (exit 1), and every
# gold-side failure is a plain evaluation — `Tactic 'decide' proved that the
# proposition ¬(…)`, i.e. `decide` computed the string and found the spec
# SATISFIED there. The forgery test was run on all ten anyway: the claim was
# flipped (the `¬` dropped) and rebuilt on both sides, and the exit codes INVERT
# exactly (flipped-on-gold 0, flipped-on-rival 1). So gold's exit code tracks
# the claim rather than any syntactic accident. That last sentence held of every
# case BUT ONE, and the exception was found later by a re-measurement rather than
# by this note: `weak-wrap-threshold-off-by-one` did NOT invert, because its
# gold-side build never reached a verdict at all. See the THIRD AUDIT NOTE at
# `_W_THRESHOLD` for the bytes and for the one-line repair. Two
# defects WERE found and are fixed above: the dropped admissibility lane, and a
# false reason recorded for the dropped divergence lane. Two further probes
# found no spec hole:
#   * SPEC-TOO-WEAK — six NEW wrong impls the battery does not contain, aimed at
#     the least-probed clauses: quoting an INTEGER value, replacing the
#     `name=value` joiner with `name:value`, wrapping in brackets instead of
#     parentheses, collapsing duplicate parameter names (`argNames.eraseDups`),
#     rendering only the first two parameters (`argNames.take 2`), and a
#     point-hole impl wrong at ONE class name only. Every one is REJECTED, and
#     each was additionally refuted by its own fresh witness (rival exit 0 /
#     gold exit 1) — so the rejections are the spec's, not tactic breakage.
#   * SPEC-TOO-STRONG — two NEW correct reshapes beyond the two positives here:
#     the fallback guard written as a `match` on the (value, flag) pair, and the
#     traversal written as a `foldr` instead of a `map` or a loop. Both PROVE
#     (exit 0), so the spec admits faithful reshapes it did not anticipate.
# Also re-derived by build: the frozen tactic script does NOT survive either
# soundness positive's reshape (both exit 1 with the frozen proof in place), so
# the claim that each positive was reproven honestly is true and neither is a
# no-op; and rival 6's near-miss claim holds — `_W_MAP_ONLY` does NOT refute
# `weak-fallback-keyed-on-absence` (exit 1), confirming that rival is genuinely
# correct at rival 1's point and so earns its own discriminating input.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / refinement.md)
# ---------------------------------------------------------------------------
# The single obligation is
#     theorem correct_reprString :
#       ∀ className argNames attrs extra hasExtra,
#         problem_spec_reprString className argNames attrs extra hasExtra
#           (implementation_reprString className argNames attrs extra hasExtra)
# with the postcondition a single master clause,
#     (P1) result = reprString className argNames attrs extra hasExtra
# and NO precondition hypothesis (every binder is a `String` / `Bool` /
# association list, well-formed by typing).
#
# `reprString` is FULLY TRANSPARENT in its arguments — it spells out the
# traversal, the per-parameter resolution and the assembly, and is decidable at
# literal inputs. It is NOT an opaque answer-key, so there is no "wrong echo of
# an ungrounded oracle" to build: `return reprString …` performs the real work
# and is simply correct. That is why the cheapest-impl case below is a POSITIVE
# control rather than an attack (it ports nagini's
# `pos-control-grounded-oracle-cheapest` on the same reasoning), and why no
# `witness` here has to condition on the carrier: every rival is refutable by
# `decide` at concrete literals.
#
# Unfolding P1, the independent things an impl must get right — each attacked by
# at least one rival below:
#   (C1) the value of a parameter whose direct attribute is the null sentinel
#        while the auxiliary map is present and records it: the MAP's entry, not
#        the sentinel.                          [rivals 1, 2, 6]
#   (C2) the auxiliary map is consulted ONLY when the object carries one:
#        without one, a null-sentinel attribute stays the null sentinel.
#                                               [rivals 2, 4]
#   (C3) the direct attribute WINS when it is not the null sentinel, even if the
#        auxiliary map also records the name.    [rival 3]
#   (C4) a parameter absent everywhere is reported as the null sentinel, never
#        fabricated.                            [rival 4]
#   (C5) the rendered parameters appear in the GIVEN name order.  [rival 5]
#   (C6) the assembly: `", "`-joined inside the class name and parentheses.
#                                               [rivals 7, 8]
#   (C7) the per-value RENDERING: a text value is enclosed in single quotes and
#        the null sentinel prints as `None` — the value's rendered FORM, which is
#        independent of resolving the value correctly.  [rivals 9, 10]
#   (C8) the layout BREAKS: a parameter whose placement would carry the running
#        line to the width limit opens a continuation line instead of continuing
#        after `", "`.                               [rival 11]
#   (C9) the width limit is INCLUSIVE (reaching it wraps, not only passing it).
#                                                    [rival 12]
#  (C10) the continuation INDENT is one plus half the class name's width, and the
#        running width restarts from that separator.  [rival 13]
#  (C11) a rendered parameter past the elision limit is cut to its head, an
#        ellipsis, and its tail, BEFORE being placed.  [rival 14]
#
# C8–C11 are the clauses this battery had no case against while the model laid
# every rendered parameter out on one unbroken line: under that model the flat
# join now shipped as rival 11 WAS the frozen impl. The four cases were added
# with the model's realignment, each machine-checked to be rejected and to be
# refuted by its own witness at a point the real callee agrees with.
#
# BINDER COVERAGE. The five input binders are `className`, `argNames`, `attrs`,
# `extra`, `hasExtra`. The fourteen reject witnesses probe FOURTEEN DISTINCT
# input points and move every one of them: `hasExtra` is taken at both `true`
# and `false`; `argNames` at one-, two-, three- and five-element lists; `attrs`
# empty, recording a real value, recording the null sentinel EXPLICITLY (rival
# 6's near-miss point), recording a TEXT value (rival 9's point, the only place
# the quoting clause is observable), and recording text values long enough to
# reach the width limit (rivals 11–13) and to pass the elision limit (rival 14);
# `extra` empty, agreeing with `attrs`, disagreeing with it, and recording a name
# `attrs` does not (rival 10's second parameter); and `className` varies per
# point, pinned by rival 8 (which drops it) so a rival mishandling only the
# class-name prefix is caught, and READ for its WIDTH by rival 13, whose
# continuation indent is a function of that width.
#
# The width binder is worth naming separately: before the layout clauses, every
# witness in the battery held its rendered parameters far under both the width
# and the elision limits, so the whole magnitude dimension of the input was
# untouched — the battery could not have distinguished any two renderers that
# agree on short inputs. Rivals 11–14 move it.
#
# ---------------------------------------------------------------------------
# NAGINI CASES WITH NO COUNTERPART HERE (also stated in the payload assessment)
# ---------------------------------------------------------------------------
#   * FRAME / PERMISSION-MUTATION (`frame-mutate-store-insert`,
#     `frame-mutate-store-del`): VACUOUS on this backend. Lean is referentially
#     transparent — the association lists are immutable values, there is no
#     aliasing and no fractional permission to under-hold — so there is no
#     illegal-write rival to author and no substitute is fabricated.
#   * DIVERGENCE (`weak-diverge-before-return`): VACUOUS on lean, but NOT for
#     the reason the port first recorded. The original claim was that `partial`
#     is banned by the variant rules; that is false — `variant_problems` does
#     not screen `partial` (measured: it returns [] for a `partial def` rival),
#     so the ban was imagined. The real reason is that the class is
#     unWITNESSABLE here, demonstrated by build:
#       - A diverging TOTAL `def` (`let rec spin n := spin (n+1)`) is refused by
#         Lean itself: `error: fail to show termination for`. The file does not
#         compile, so there is no rival to refute — a tooling failure, not a
#         spec verdict.
#       - A `partial def` rival DOES elaborate, but `partial` makes the impl
#         opaque to reduction: every literal-input witness dies on
#         `Tactic 'unfold' failed to unfold 'implementation_reprString'`, which
#         is a syntactic failure carrying no information about the spec.
#       - The remaining option, a witness CONDITIONED on the carrier
#         (`(h : implementation_reprString … ≠ reprString …)`), was built against
#         both subjects and elaborates for BOTH the partial rival (exit 0) and
#         the frozen solution (exit 0). It is a tautology — `unfold
#         problem_spec_reprString; exact h` never inspects the impl — so it is
#         `witness-vacuous`, the gate's own name for a non-discriminator, and
#         shipping it would forge a case rather than close one.
#     So the class is genuinely inexpressible on this carrier, not merely hard.
#     (Contrast the velvet sibling, where `loom.semantics.termination "partial"`
#     makes this a KNOWN SPEC HOLE — see the corpus-wide termination-semantics finding. That
#     disposition does not transfer here.)
#   * `weak-store-branch-returns-none`: no SEPARATE counterpart, and the reason
#     is extensional collapse rather than inexpressibility. On nagini the store
#     was a dict with a membership test, so "enter the fallback branch but
#     resolve to `none` anyway" was distinguishable from "never consult the
#     store". Here the fallback branch is guarded by `v0 == PyVal.null`, so
#     writing `v := PyVal.null` inside it assigns v0 back to itself: the impl is
#     EXTENSIONALLY IDENTICAL to `weak-no-map-fallback` on every one of the five
#     binders, not merely similar. It would therefore be refuted by that rival's
#     own witness at that rival's own point, and shipping it would be a vacuous
#     eleventh case. Verified by enumerating the resolution over all
#     (v0, hasExtra, extra-entry) combinations before dropping it. The clause it
#     was meant to defend — the fallback yields the MAP's entry — is what
#     `weak-no-map-fallback` already pins via `_W_MAP_ONLY`.
#   * ADMISSIBILITY (`admiss-empty-store-in-domain`): PORTED, as
#     `admiss-ground-f2p-shaped-input` below. The port originally dropped this
#     lane on the reasoning that `correct_reprString` is an unconditional `∀`
#     with no precondition hypothesis, so there is "nothing to prove usable".
#     That reasoning is WRONG and the second audit rejected it: the analogue of
#     PRECOND-TOO-STRONG on a total carrier is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input — a spec that no
#     implementation could meet there would still pass every reject case in this
#     battery, because a reject case only ever shows some impl FAILS. Dropping
#     the lane silently removed one of the three directions this gate exists to
#     test. The ported case discharges the obligation AT the concrete
#     F2P-shaped input by evaluation, as a `have`, before closing the frozen
#     obligation verbatim.
#   * AXIOM_TESTS: dropped, the axiom lane is G-AX's job. This bundle consumes
#     no callee axiom and declares no `opaque` (G-AX records `skip`).
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14983"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the impl region or the proof region
# of the frozen Solution.lean, and each is unique in the file (enforced by
# `_swap`, so the manifest breaks loudly if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# The per-parameter body of the frozen traversal (impl region, loop body).
_GOLD_BODY = '''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null && hasExtra then
      v := lookupVal extra key
    parts := parts ++ [elideEntry (key ++ "=" ++ pyRepr v)]
'''

# The frozen assembly line (impl region, the `return`).
_GOLD_TAIL = '''  return className ++ "(" ++ layoutEntries className.length parts ++ ")"
'''

# The whole frozen impl declaration (impl region) — replaced by the two
# soundness positives, which change the impl's SHAPE and therefore reprove, and
# by the two layout rivals that need a helper of their own alongside the loop.
_GOLD_DECL = ('''def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
  let mut parts : List String := []
  for key in argNames do
''' + _GOLD_BODY + _GOLD_TAIL)

# The frozen tactic body (proof region). Untouched by every reject case: a
# rival's rejection is attributed by its own `witness`, never by tactic breakage.
_GOLD_PROOF = _BASE[_BASE.index("  intro className argNames attrs extra hasExtra"):
                    _BASE.index("-- proof-end")]
assert _BASE.count(_GOLD_PROOF) == 1


def _body(new_body):
    """Variant that changes only the per-parameter resolution."""
    return _swap(_BASE, _GOLD_BODY, new_body)


def _tail(new_tail):
    """Variant that changes only the final assembly."""
    return _swap(_BASE, _GOLD_TAIL, new_tail)


def _decl(new_decl):
    """Variant that replaces the whole impl declaration, frozen proof kept.

    Used by the two layout rivals that need a helper `def` of their own next to
    the loop (a wrong `placeEntry`): the frozen per-parameter resolution is
    carried verbatim inside `new_decl`, so the refutation is attributable to the
    layout alone. Adding a plain helper `def` is not a spec change and not a new
    obligation — `variant_problems` screens new `theorem`/`lemma`/`axiom`
    declarations, and these are neither (measured: it returns [] for each).
    """
    return _swap(_BASE, _GOLD_DECL, new_decl)


def _reshape(new_decl, new_proof):
    """Variant with a different impl SHAPE plus the proof that closes for it."""
    return _swap(_swap(_BASE, _GOLD_DECL, new_decl), _GOLD_PROOF, new_proof)


def _ground(have_block):
    """Variant that PREPENDS a ground `have` to the frozen tactic body.

    The impl is the frozen one and the frozen proof still closes the obligation
    verbatim after the `have`; the only addition is a discharge of the SAME
    postcondition at one concrete input, by evaluation. Used by the
    admissibility lane.
    """
    return _swap(_BASE, _GOLD_PROOF, have_block + _GOLD_PROOF)


# The F2P-shaped input, in the model's own vocabulary: an object carrying an
# auxiliary parameter map, three name-sorted parameters, one held directly as an
# integer, one held ONLY in the auxiliary map (so the fallback must fire), and
# one held directly as the null sentinel. This is the combination the failing
# tests exercise, and the point at which the obligation must be satisfiable.
_ADM_ARGS = ('"Splitter" ["n_a", "n_b", "n_c"] '
             '[("n_a", PyVal.int 6), ("n_c", PyVal.null)] '
             '[("n_b", PyVal.int 2)] true')


# ---------------------------------------------------------------------------
# Witnesses. Every rival is refuted at CONCRETE literals: the postcondition is
# `result = reprString …` with `reprString` transparent and every carrier type
# (`String`, `Bool`, `List (String × PyVal)`, `PyVal`) `DecidableEq`, so the
# refutation is a plain `decide` after unfolding — no conditioning on an opaque
# term is needed, hence no witness binds anything and none can be inconsistent.
#
# Each snippet was built against its rival and against the frozen solution:
# it ELABORATES for the rival (the rival provably contradicts the spec at that
# input) and FAILS for the frozen solution (so it discriminates rather than
# being a tautology).
# ---------------------------------------------------------------------------

def _witness(className, argNames, attrs, extra, hasExtra, opts=""):
    args = f'"{className}" {argNames} {attrs} {extra} {hasExtra}'
    return (
        opts +
        f"example : ¬ problem_spec_reprString {args}\n"
        f"    (implementation_reprString {args}) := by\n"
        "  unfold problem_spec_reprString implementation_reprString reprString\n"
        "  intro h\n"
        "  exact absurd (h (by decide)) (by decide)\n")


# One parameter, no direct attribute, auxiliary map present and recording it.
# The rule renders the MAP's value; a fallback-less rival renders the sentinel.
_W_MAP_ONLY = _witness("C", '["a"]', "[]", '[("a", PyVal.int 2)]', "true")
# Same shape but the object carries NO auxiliary map: the rule must keep the
# null sentinel, so a rival that reads the map unconditionally is refuted here.
_W_NO_MAP = _witness("D", '["b"]', "[]", '[("b", PyVal.int 7)]', "false")
# Direct attribute PRESENT and non-sentinel while the map records a DIFFERENT
# value: the rule keeps the direct attribute.
_W_ATTR_WINS = _witness("E", '["c"]', '[("c", PyVal.int 1)]',
                        '[("c", PyVal.int 2)]', "true")
# Recorded nowhere, no auxiliary map: the rule reports the null sentinel.
_W_ABSENT = _witness("F", '["d"]', "[]", "[]", "false")
# TWO parameters with distinct values, both direct: pins the traversal ORDER.
_W_ORDER = _witness("G", '["p", "q"]',
                    '[("p", PyVal.int 1), ("q", PyVal.int 2)]', "[]", "true")
# The near-miss point: the direct attribute IS recorded but HOLDS the null
# sentinel, and the map records a real value. Presence-keyed and
# sentinel-keyed fallbacks agree everywhere except here.
_W_NULL_ATTR = _witness("H", '["e"]', '[("e", PyVal.null)]',
                        '[("e", PyVal.int 3)]', "true")
# Two parameters, mixed value shapes: pins the `", "` separator.
_W_SEPARATOR = _witness("I", '["m", "n"]',
                        '[("m", PyVal.str "x"), ("n", PyVal.null)]',
                        "[]", "false")
# One parameter: pins the class-name prefix of the assembly.
_W_PREFIX = _witness("J", '["z"]', '[("z", PyVal.int 9)]', "[]", "true")
# The only point where the QUOTING of a text value is observable: `attrs` holds
# a text value directly (so the resolution is not in question) while the
# auxiliary map is present and records a different value for the same name — so
# a rival that resolved wrongly would ALSO be refuted here, and a rival that
# resolves correctly but strips the quotes is refuted by the rendering alone.
_W_STR_QUOTED = _witness("K", '["s"]', '[("s", PyVal.str "x")]',
                         '[("s", PyVal.int 1)]', "true")
# Two parameters at `hasExtra = true`: the first RESOLVES to the null sentinel
# even after the fallback (the map does not record it), the second is drawn from
# the map. Pins that the sentinel prints as `None` at a point where the fallback
# genuinely fired, so the rendering clause is separated from the resolution.
_W_NULL_RENDERED = _witness("L", '["u", "v"]', '[("u", PyVal.null)]',
                            '[("v", PyVal.int 4)]', "true")

# ---- LAYOUT points. Every witness above keeps the rendered parameters short
# enough to sit on one line, so none of them can observe the layout at all: the
# three points below are the ones where the running-width arithmetic becomes
# visible. Each was also checked against the REAL callee (conformance_check.py
# carries all three as edge cases) so the string the spec predicts here is the
# one the repo actually produces.
#
# WRAPPING. Five text parameters under a 13-wide class name: the running width
# passes the limit at the fourth, which must therefore open a continuation line.
# A renderer that lays every parameter out on one line agrees with the rule on
# every witness above and is wrong exactly here.
_LAYOUT_KEYS = '["alpha", "n_repeats", "n_splits", "random_state", "shuffle"]'
_LAYOUT_ATTRS = ('[("alpha", PyVal.str "balanced"), '
                 '("n_repeats", PyVal.str "balanced"), '
                 '("n_splits", PyVal.str "balanced"), '
                 '("random_state", PyVal.str "balanced"), '
                 '("shuffle", PyVal.str "balanced")]')
_W_WRAPS = _witness("RepeatedKFold", _LAYOUT_KEYS, _LAYOUT_ATTRS, "[]", "false")
# THE THRESHOLD, exactly. The second parameter's placement brings the line to
# precisely the limit, where the rule wraps: a renderer that wraps only STRICTLY
# past the limit differs from the rule at this single width and nowhere else, so
# no other witness — including the wrapping one above — can catch it.
#
# THIRD AUDIT NOTE (build-level re-measurement of THIS witness's gold-side
# failure). The two `decide`s here settle a String equality whose sides are
# EQUAL for the frozen impl, over an 80-character rendered line; walking two
# equal strings to the end costs more recursion than the default budget, while
# against the rival the comparison stops at the first differing character. So
# the shipped witness (no `set_option`) failed on the rival's side for the right
# reason and failed on GOLD's side for the wrong one: `maximum recursion depth
# has been reached`, i.e. the decision procedure returned NO verdict. Measured:
# the OPPOSITE claim — the same statement without the `¬`, closed by
# `intro h; decide`, same unfold prefix — printed the byte-identical three-line
# message against gold, so gold's exit code did not depend on what was claimed
# and the recorded rejection attested nothing. The `set_option` below raises the
# BUDGET only (as `_W_ELIDED` already does, for the same reason); it admits no
# unproved step and the claim is still closed by `decide`. With it, gold fails
# by EVALUATION — ``Tactic `decide` proved that the proposition ¬(… =
# reprString …) is false`` — and the exit codes invert with the claim:
# witness/rival 0, witness/gold 1, opposite/gold 0, opposite/rival 1.
_W_THRESHOLD = _witness(
    "RepeatedKFold", '["a", "b"]',
    f'[("a", PyVal.str "{"z" * 55}"), ("b", PyVal.int 7)]', "[]", "false",
    opts="set_option maxRecDepth 100000 in\n")
# THE CONTINUATION INDENT. Three parameters under a 16-wide class name, wrapping
# once: the indent is HALF the class name's width plus one, so a renderer that
# indents by the full width produces the same line BREAKS with different
# padding. Distinct from the wrapping point, which a full-width indent gets
# right in every respect except that padding.
_W_INDENT = _witness(
    "GradientBoosting", '["p", "q", "r"]',
    '[("p", PyVal.str "aaaaaaaaaaaaaaaaaaaaaaaaa"), '
    '("q", PyVal.str "aaaaaaaaaaaaaaaaaaaaaaaaa"), '
    '("r", PyVal.str "aaaaaaaaaaaaaaaaaaaaaaaaa")]', "[]", "false")
# THE OVERLONG-ENTRY ELISION. One parameter whose rendered form runs past the
# elision limit, so the rule keeps its head, an ellipsis, and its tail. Every
# other witness is far under the limit. `decide` here evaluates string
# operations over a 520-character literal, which exceeds the default recursion
# and heartbeat budgets — those two `set_option`s raise the BUDGET only; neither
# admits an unproved step, and the claim is still closed by `decide` (the
# witness rules ban `sorry`/`admit`/`native_decide`/`axiom`, none of which
# appear).
_W_ELIDED = _witness(
    "C", '["a"]', f'[("a", PyVal.str "{"z" * 520}")]', "[]", "false",
    opts="set_option maxRecDepth 100000 in\nset_option maxHeartbeats 0 in\n")


# ---------------------------------------------------------------------------
# SOUNDNESS positives — structurally different CORRECT impls, each with a proof
# that actually closes for its new shape (the frozen script does NOT survive
# either reshape; both were reproven honestly).
# ---------------------------------------------------------------------------

# POSITIVE 1 — the traversal expressed FUNCTIONALLY (a `map` over the parameter
# names instead of an accumulator loop), with the fallback guard's conjuncts
# COMMUTED. Same string on every input.
_POS_MAP_DECL = '''def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  className ++ "(" ++ layoutEntries className.length
    (argNames.map (fun key =>
      let v0 := lookupVal attrs key
      let v := if hasExtra && v0 == PyVal.null then lookupVal extra key else v0
      elideEntry (key ++ "=" ++ pyRepr v))) ++ ")"
'''
# The accumulator induction the frozen proof needs is gone (there is no loop);
# what remains is the pointwise equality of the mapped function with the spec's
# per-parameter renderer, modulo the commuted guard.
_POS_MAP_PROOF = '''  intro className argNames attrs extra hasExtra
  unfold problem_spec_reprString implementation_reprString reprString
  intro hdom
  clear hdom
  have h : ∀ key : String,
      elideEntry (key ++ "=" ++ pyRepr (if (hasExtra && lookupVal attrs key == PyVal.null) = true
        then lookupVal extra key else lookupVal attrs key))
      = renderParam attrs extra hasExtra key := by
    intro key
    unfold renderParam resolveVal
    simp only [Bool.and_comm]
  simp only [h]
'''

# POSITIVE 2 — the cheapest honest impl. Because the postcondition is stated
# over a TRANSPARENT description of the whole rendering (not an opaque
# answer-key), returning that description directly performs the real work: it
# resolves each parameter from the direct attributes then the auxiliary map and
# assembles the string. This is the port of nagini's grounded-oracle positive
# and STANDS IN PLACE of an echo attack — there is no wrong echo to build here.
_POS_DIRECT_DECL = '''def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String :=
  reprString className argNames attrs extra hasExtra
'''
_POS_DIRECT_PROOF = '''  intro className argNames attrs extra hasExtra
  unfold problem_spec_reprString implementation_reprString
  intro hdom
  clear hdom
  rfl
'''


SPEC_TESTS = [

    # ===================================================================
    # SOUNDNESS — positive controls (must VERIFY; else SPEC-TOO-STRONG)
    # ===================================================================

    {
        "id": "pos-control-functional-map-commuted-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _reshape(_POS_MAP_DECL, _POS_MAP_PROOF),
        "rationale": (
            "Positive control on the master clause "
            "`result = reprString className argNames attrs extra hasExtra`. A "
            "structurally DIFFERENT but correct impl: the traversal is written "
            "functionally as a map over the parameter names rather than as an "
            "accumulator loop, and the fallback guard's two conjuncts are "
            "COMMUTED (map-present tested before the sentinel test). It yields "
            "the identical string on every input, so it must verify. The frozen "
            "tactic script does not survive the reshape — the accumulator "
            "induction has nothing to induct on — so the proof was rewritten: "
            "the goal reduces to a pointwise equality between the mapped "
            "function and the spec's per-parameter renderer, closed by "
            "commuting the guard. Reproven honestly: the `theorem "
            "correct_reprString` statement is byte-identical and no "
            "sorry/admit/native_decide/axiom/helper lemma is introduced. If a "
            "faithful correct reshape could not satisfy the clause, the spec "
            "would be SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-control-transparent-rendering-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _reshape(_POS_DIRECT_DECL, _POS_DIRECT_PROOF),
        "rationale": (
            "Positive control, and the port of the nagini battery's "
            "grounded-oracle case. The postcondition is stated over a "
            "TRANSPARENT description of the rendering — it spells out the "
            "traversal, the per-parameter resolution and the assembly — not "
            "over an opaque answer-key, so returning that description directly "
            "IS the real work rather than an echo. There is consequently no "
            "wrong-echo attack to build, and this stands in its place: the "
            "cheapest correct impl must verify, with P1 becoming a definitional "
            "equality. Else SPEC-TOO-STRONG."
        ),
    },

    # ===================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at an F2P-shaped input
    # (must VERIFY; else the total-carrier analogue of PRECOND-TOO-STRONG)
    # ===================================================================

    # ADDED BY THE SECOND AUDIT. The port dropped nagini's
    # `admiss-empty-store-in-domain` on the reasoning that this obligation has no
    # precondition, so there was "nothing to prove usable". That is the reasoning
    # the audit rejects: on a total carrier the analogue of PRECOND-TOO-STRONG is
    # the obligation being UNSATISFIABLE at exactly an F2P-shaped input, and no
    # reject case can detect that (a reject case only ever shows that some impl
    # FAILS the spec, never that some impl can MEET it there). Without this lane
    # the battery tested two of the three directions the gate exists for.
    {
        "id": "admiss-ground-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ground(
            f'''  have _ground : problem_spec_reprString {_ADM_ARGS}
      (implementation_reprString {_ADM_ARGS}) := by
    unfold problem_spec_reprString
    intro _
    rfl
'''),
        "rationale": (
            "Admissibility: the obligation must be SATISFIABLE — not merely "
            "unfalsified — at a normal, F2P-shaped input. The probe discharges "
            "the postcondition `result = reprString …` at one concrete input by "
            "EVALUATION (`decide`), as a `have`, and only then closes the frozen "
            "obligation verbatim; the impl is the frozen one and the frozen "
            "tactic body is unchanged, so nothing is assumed and the statement is "
            "byte-identical. The input is the shape the failing tests exercise: "
            "an object carrying an auxiliary parameter map, with three "
            "name-sorted parameters — one held directly as an integer, one held "
            "ONLY in the auxiliary map (so the fallback genuinely fires), and one "
            "held directly as the null sentinel. If this `have` could NOT be "
            "discharged, the spec would be unsatisfiable at exactly a normal "
            "input — the total-carrier analogue of PRECOND-TOO-STRONG — and no "
            "reject case in this battery would have revealed it, since a reject "
            "case only shows that some impl fails, never that some impl can "
            "succeed. Ports nagini's `admiss-empty-store-in-domain`."
        ),
    },

    # ===================================================================
    # UNIQUENESS — the value-resolution rivals ported from nagini
    # ===================================================================

    # Port of nagini `weak-prepatch-no-fallback` (the bug delta).
    {
        "id": "weak-no-map-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v := lookupVal attrs key
    parts := parts ++ [key ++ "=" ++ pyRepr v]
'''),
        "refinement": (
            "This is the pre-patch resolution: the value is taken only from the "
            "direct attributes, with no fallback to the auxiliary parameter map. "
            "It is exactly the behavior the issue reports — an object that holds "
            "a construction parameter only in its auxiliary map, and not as a "
            "direct attribute, renders that parameter as the null sentinel "
            "instead of its real value, so the summary string the failing tests "
            "demand does not match. A faithful real patch shaped this way would "
            "therefore NOT resolve the F2P; a verifying rival here would be a "
            "true verify-does-not-imply-resolve break. (It is also the shipped "
            "`Solution_prepatch.lean` behavior, i.e. the G-DIFF delta.)"
        ),
        "rationale": (
            "Violates the master clause C1: on a parameter whose direct "
            "attribute is the null sentinel while the auxiliary map is present "
            "and records a real value, the rule renders the map's value and this "
            "rival renders the sentinel. Witness varies `attrs` (empty) against "
            "`extra` (recording the name) at `hasExtra = true`."
        ),
        "witness": _W_MAP_ONLY,
    },

    # Port of nagini `weak-no-store-returns-sentinel`'s dual: the map-presence
    # observation is dropped instead of the map lookup.
    {
        "id": "weak-ignores-map-presence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null then
      v := lookupVal extra key
    parts := parts ++ [key ++ "=" ++ pyRepr v]
'''),
        "refinement": (
            "Drops the check that the object CARRIES an auxiliary parameter map "
            "and consults it regardless. On an object with no such map the "
            "resolution then reads a map that is not there, so a parameter that "
            "is genuinely absent can render with a value drawn from elsewhere "
            "instead of the null sentinel. A faithful real patch shaped this way "
            "would print a spurious value for plain objects whose parameter is "
            "unset, breaking the summary strings the currently-passing repr "
            "tests pin, so it would NOT resolve."
        ),
        "rationale": (
            "Violates C2: the rule consults the auxiliary map ONLY when "
            "`hasExtra` holds, so with `hasExtra = false` a null-sentinel "
            "attribute must stay the null sentinel. Witness holds `hasExtra` at "
            "FALSE with `extra` non-empty — the only combination that separates "
            "this rival from the rule, and the setting rival 1's witness does "
            "not probe."
        ),
        "witness": _W_NO_MAP,
    },

    # Port of nagini `weak-store-overrides-attr`.
    {
        "id": "weak-map-overrides-direct-attribute",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if hasExtra then
      v := lookupVal extra key
    parts := parts ++ [key ++ "=" ++ pyRepr v]
'''),
        "refinement": (
            "Drops the guard that the direct attribute be the null sentinel, so "
            "the auxiliary map overrides even a parameter the object holds "
            "directly. The direct attribute is the authoritative current value "
            "while the auxiliary map is the original construction snapshot, so a "
            "faithful real patch shaped this way would print the stale snapshot "
            "value wherever the two differ, diverging from the summary strings "
            "the currently-passing repr tests pin. It would NOT resolve."
        ),
        "rationale": (
            "Violates C3: the rule keeps the direct attribute whenever it is not "
            "the null sentinel. Witness holds `attrs` recording a real value AND "
            "`extra` recording a DIFFERENT one at `hasExtra = true` — the only "
            "sub-domain where this rival is wrong, and a point no other witness "
            "probes."
        ),
        "witness": _W_ATTR_WINS,
    },

    # Port of nagini `weak-no-store-returns-sentinel` (fabricate on the
    # nothing-recorded branch).
    {
        "id": "weak-fabricates-absent-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null && hasExtra then
      v := lookupVal extra key
    else if v0 == PyVal.null then
      v := PyVal.str key
    parts := parts ++ [key ++ "=" ++ pyRepr v]
'''),
        "refinement": (
            "Fabricates a value — the parameter's own name — for a parameter "
            "that is genuinely unset on an object carrying no auxiliary map. A "
            "faithful real patch shaped this way would make a plain object whose "
            "parameter is unset render that parameter with a made-up value "
            "rather than the null sentinel, so the currently-passing "
            "summary-string tests over such objects FAIL. It would NOT resolve."
        ),
        "rationale": (
            "Violates C4 (and C2): a parameter recorded nowhere must render as "
            "the null sentinel. Witness holds BOTH `attrs` and `extra` empty at "
            "`hasExtra = false` — the all-absent point, distinct from rival 2's "
            "point (which has a non-empty `extra`) and reached by no other "
            "witness."
        ),
        "witness": _W_ABSENT,
    },

    # NEW on this carrier: the traversal order, which nagini's scalar resolver
    # could not express.
    {
        "id": "weak-reversed-parameter-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null && hasExtra then
      v := lookupVal extra key
    parts := [key ++ "=" ++ pyRepr v] ++ parts
'''),
        "refinement": (
            "Resolves every parameter correctly but accumulates the rendered "
            "parameters in reverse, so the summary lists them in the opposite of "
            "the given order. A faithful real patch shaped this way would emit "
            "the parameters back-to-front; the failing tests assert the summary "
            "string EXACTLY, in the given name order, so the string would "
            "mismatch and the patch would NOT resolve."
        ),
        "rationale": (
            "Violates C5: the rule renders the parameters in the order "
            "`argNames` gives. Witness is the only one to vary `argNames` to a "
            "TWO-element list with distinct values — a one-element list cannot "
            "separate an order rival from the rule at all."
        ),
        "witness": _W_ORDER,
    },

    # NEAR-MISS on the fallback trigger. Agrees with the rule strictly more
    # often than rival 1 does, so it gets its own discriminating point.
    {
        "id": "weak-fallback-keyed-on-absence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if !(attrs.any (fun p => p.1 == key)) && hasExtra then
      v := lookupVal extra key
    parts := parts ++ [key ++ "=" ++ pyRepr v]
'''),
        "refinement": (
            "Triggers the auxiliary-map fallback on the direct attribute being "
            "ABSENT rather than on its value being the null sentinel. The two "
            "agree except where the object records the attribute and its value "
            "IS the null sentinel: the rule then still consults the auxiliary "
            "map, this rival does not. A faithful real patch shaped this way "
            "would leave such a parameter rendering as the null sentinel even "
            "though the auxiliary map holds its real value — the very symptom "
            "the failing tests pin, on the objects that record the parameter "
            "with an unset direct value. It would NOT resolve."
        ),
        "rationale": (
            "Violates C1 on a strictly SMALLER sub-domain than rival 1, so it "
            "gets its own witness rather than sharing rival 1's: at rival 1's "
            "point (`attrs` empty) this rival is CORRECT. Witness varies `attrs` "
            "to record the name EXPLICITLY holding the null sentinel while "
            "`extra` records a real value — the unique point that separates a "
            "presence-keyed fallback from the sentinel-keyed rule."
        ),
        "witness": _W_NULL_ATTR,
    },

    # NEW on this carrier: the assembly shape (separator).
    {
        "id": "weak-join-drops-separator-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tail('''  return className ++ "(" ++ String.intercalate "," parts ++ ")"
'''),
        "refinement": (
            "Resolves and renders every parameter correctly but joins them "
            "without the space after the comma. A faithful real patch shaped "
            "this way would produce a summary string that differs from the "
            "demanded one by that separator on every multi-parameter object; the "
            "failing tests compare the string EXACTLY, so it would NOT resolve — "
            "and it would also break the currently-passing summary-string tests."
        ),
        "rationale": (
            "Violates C6: the rule joins the rendered parameters with `\", \"`. "
            "Witness varies `argNames` to two parameters (one parameter has no "
            "separator to get wrong) with mixed value shapes — a text value and "
            "the null sentinel — at `hasExtra = false`."
        ),
        "witness": _W_SEPARATOR,
    },

    # NEW on this carrier: the assembly shape (class-name prefix). This is the
    # rival that makes `className` a discriminated binder rather than a binder
    # every witness merely carries along.
    {
        "id": "weak-omits-class-name-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tail('''  return "(" ++ String.intercalate ", " parts ++ ")"
'''),
        "refinement": (
            "Resolves and joins correctly but omits the class name before the "
            "parenthesised parameter list. A faithful real patch shaped this way "
            "would render every object's summary without its class name, so the "
            "demanded summary string — which begins with that name — mismatches "
            "for every object. It would NOT resolve, and would break the "
            "currently-passing summary-string tests too."
        ),
        "rationale": (
            "Violates C6 on the prefix rather than the separator: the rule wraps "
            "the joined parameters in the class name and parentheses. This is "
            "the rival that exercises the `className` binder — without it a "
            "wrong impl could ignore `className` entirely and the battery would "
            "never notice. Witness is refuted by the missing prefix alone, at a "
            "single directly-held parameter."
        ),
        "witness": _W_PREFIX,
    },

    # NEW on this carrier, and ADDED BY THE AUDIT: the per-value rendering. The
    # value's rendered FORM is a defended clause independent of resolving the
    # value, and nothing else in the battery attacked it.
    {
        "id": "weak-text-value-loses-quotes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null && hasExtra then
      v := lookupVal extra key
    let s := match v with
      | PyVal.str t => t
      | _ => pyRepr v
    parts := parts ++ [key ++ "=" ++ s]
'''),
        "refinement": (
            "Resolves every parameter correctly — the direct attribute, the "
            "auxiliary-map fallback and the map-presence guard are all kept "
            "verbatim — but renders a TEXT value bare instead of enclosing it in "
            "single quotes. A faithful real patch shaped this way would print a "
            "text-valued parameter unquoted, so the summary string differs from "
            "the demanded one on every object that has one; the tests compare the "
            "string EXACTLY, so it would NOT resolve, and it would break the "
            "currently-passing summary-string tests over text-valued parameters "
            "too."
        ),
        "rationale": (
            "Violates C7: the rule renders a text value in single quotes. This "
            "clause is independent of the value RESOLUTION every other rival "
            "attacks — the resolution here is byte-identical to the frozen one — "
            "so without this case an impl could resolve perfectly and still "
            "render wrongly. Witness is the only one to take `attrs` at a TEXT "
            "value; it holds that value DIRECTLY with the auxiliary map present "
            "and recording a different value for the same name, so the refutation "
            "is attributable to the quoting alone."
        ),
        "witness": _W_STR_QUOTED,
    },

    {
        "id": "weak-null-renders-as-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null && hasExtra then
      v := lookupVal extra key
    let s := match v with
      | PyVal.null => ""
      | _ => pyRepr v
    parts := parts ++ [key ++ "=" ++ s]
'''),
        "refinement": (
            "Resolves every parameter correctly but renders the null sentinel as "
            "nothing at all instead of as `None`. A faithful real patch shaped "
            "this way would emit `name=` for every unset parameter, so the "
            "summary string mismatches the demanded one on every object that has "
            "one — including the objects whose parameter is unset and absent from "
            "the auxiliary map. It would NOT resolve, and it would break the "
            "currently-passing summary-string tests, which pin `None` for unset "
            "parameters."
        ),
        "rationale": (
            "Violates C7 on the sentinel branch of the rendering rather than the "
            "text branch: the rule prints the null sentinel as `None`. Witness "
            "takes TWO parameters at `hasExtra = true` where the first resolves "
            "to the sentinel even after the fallback fires (the map does not "
            "record it) and the second is drawn from the map — so the fallback is "
            "exercised and the refutation still lands on the rendering, not on "
            "the resolution."
        ),
        "witness": _W_NULL_RENDERED,
    },

    # ===================================================================
    # UNIQUENESS — the LAYOUT of the rendered parameters (clauses C8–C10)
    # ===================================================================
    # Rivals 11–14 attack the three layout clauses. They are the cases the
    # battery lacked while the model laid every parameter out on ONE line: under
    # that model rival 11 below WAS the frozen impl, so no case could have been
    # written against it, and the wrap/indent/elision clauses had nothing to
    # defend. Each rival keeps the per-parameter resolution and rendering
    # byte-identical to the frozen one, so each refutation is attributable to the
    # layout alone; each witness was additionally checked against the REAL
    # callee, so the string the spec predicts at these points is the repo's.

    {
        "id": "weak-flat-one-line-layout",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _tail('''  return className ++ "(" ++ String.intercalate ", " parts ++ ")"
'''),
        "refinement": (
            "Lays every rendered parameter out on a single line, joined by "
            "`\", \"`, with no continuation line however long the line becomes. "
            "A faithful real patch shaped this way would emit one unbroken line "
            "for every object with enough parameters to pass the width limit; the "
            "summary strings the tests compare are byte-exact and contain the "
            "line breaks, so those tests FAIL and the patch would NOT resolve. "
            "This is also the shape a modeler is most likely to reach for, since "
            "it is correct on every SHORT input — every other witness in this "
            "battery included."
        ),
        "rationale": (
            "Violates C8: past the width limit the rule opens a continuation "
            "line rather than continuing after `\", \"`. Witness is the first to "
            "take `argNames` at FIVE parameters with text values under a wide "
            "class name — the first input in the battery whose running width "
            "reaches the limit at all, so no earlier witness could separate a "
            "flat layout from the rule."
        ),
        "witness": _W_WRAPS,
    },

    {
        "id": "weak-wrap-threshold-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _decl('''def placeEntryStrict (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
  | (acc, ln, false), e =>
      if ln + e.length > 75 then
        (acc ++ lineSep offset ++ e, (lineSep offset).length + e.length, false)
      else
        (acc ++ ", " ++ e, ln + 2 + e.length, false)

def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
  let mut parts : List String := []
  for key in argNames do
''' + _GOLD_BODY + '''  return className ++ "(" ++
    (parts.foldl (placeEntryStrict className.length)
      ("", className.length, true)).1 ++ ")"
'''),
        "refinement": (
            "Wraps only when the running line would run STRICTLY past the width "
            "limit, instead of when it would reach it. The two agree on every "
            "input except those whose running width lands exactly on the limit. A "
            "faithful real patch shaped this way would keep one parameter on a "
            "line the demanded summary breaks, so an object hitting that width "
            "exactly renders differently and its byte-exact string test FAILS — "
            "and it is precisely the kind of off-by-one a re-implementer of the "
            "layout would introduce and not notice, since almost every input "
            "agrees. It would NOT resolve."
        ),
        "rationale": (
            "Violates C9 — the width limit is inclusive — on a strictly SMALLER "
            "sub-domain than rival 11, which is why it gets its own witness "
            "rather than sharing `_W_WRAPS`: at rival 11's point this rival is "
            "CORRECT (that line passes the limit rather than landing on it). "
            "Witness places a 55-character text value so the second parameter "
            "brings the line to exactly the limit — the unique width that "
            "separates an inclusive limit from an exclusive one."
        ),
        "witness": _W_THRESHOLD,
    },

    {
        "id": "weak-continuation-indent-full-width",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _decl('''def lineSepWide (offset : Nat) : String :=
  ",\\n" ++ String.mk (List.replicate offset ' ')

def placeEntryWide (offset : Nat) : String × Nat × Bool → String → String × Nat × Bool
  | (acc, ln, true),  e => (acc ++ e, ln + e.length, false)
  | (acc, ln, false), e =>
      if ln + e.length ≥ 75 then
        (acc ++ lineSepWide offset ++ e, (lineSepWide offset).length + e.length, false)
      else
        (acc ++ ", " ++ e, ln + 2 + e.length, false)

def implementation_reprString (className : String) (argNames : List String)
    (attrs extra : List (String × PyVal)) (hasExtra : Bool) : String := Id.run do
  let mut parts : List String := []
  for key in argNames do
''' + _GOLD_BODY + '''  return className ++ "(" ++
    (parts.foldl (placeEntryWide className.length)
      ("", className.length, true)).1 ++ ")"
'''),
        "refinement": (
            "Indents each continuation line by the FULL width of the class name "
            "instead of half that width plus one. It decides where to break in "
            "exactly the rule's places — only the padding differs. A faithful "
            "real patch shaped this way would align every continuation line "
            "under the wrong column, so every multi-line summary string differs "
            "from the demanded one by whitespace; the tests compare the string "
            "byte-for-byte, so it would NOT resolve, and it would break the "
            "currently-passing summary-string tests over any object wide enough "
            "to wrap."
        ),
        "rationale": (
            "Violates C10 — the continuation indent is one plus HALF the class "
            "name's width — while satisfying C8 and C9 exactly, so neither "
            "`_W_WRAPS` nor `_W_THRESHOLD` need have caught it. Witness varies "
            "`className` to a 16-wide name (so half-width and full-width padding "
            "differ by 7 spaces) with three parameters that wrap once. Note the "
            "indent depends on the class name's width, making `className` a "
            "binder the layout READS rather than merely prefixes."
        ),
        "witness": _W_INDENT,
    },

    {
        "id": "weak-overlong-entry-not-elided",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _body('''    let v0 := lookupVal attrs key
    let mut v := v0
    if v0 == PyVal.null && hasExtra then
      v := lookupVal extra key
    parts := parts ++ [key ++ "=" ++ pyRepr v]
'''),
        "refinement": (
            "Resolves and renders every parameter correctly and lays them out "
            "correctly, but emits a rendered parameter that runs past the elision "
            "limit in full instead of keeping its head, an ellipsis and its tail. "
            "A faithful real patch shaped this way would print an unbounded "
            "summary for an object holding a large value, so the byte-exact "
            "summary string for such an object mismatches the demanded elided "
            "one. It would NOT resolve. (It is also the clause that makes the "
            "layout's running-width arithmetic well-behaved: an unelided entry "
            "carries a width the layout was never meant to see.)"
        ),
        "rationale": (
            "Violates the elision clause of the rule, which no other rival "
            "touches: rivals 11–13 attack WHERE the parameters are placed, this "
            "one attacks the text of an individual parameter BEFORE placement. "
            "Witness is the only one to take `attrs` at a text value past the "
            "elision limit; every other witness's rendered parameters are two "
            "orders of magnitude under it, so none of them can observe elision."
        ),
        "witness": _W_ELIDED,
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — dropped.
# ---------------------------------------------------------------------------
# The axiom lane is G-AX's job and this gate ignores it. This bundle consumes no
# callee axiom and declares no `opaque` callee: the whole rendering — the
# per-parameter value resolution and the Python-style value formatting — is
# modeled deeply as transparent pure functions over the observable inputs, so
# there is no callee contract that could drift. G-AX records `skip` for exactly
# that reason.
AXIOM_TESTS = []
