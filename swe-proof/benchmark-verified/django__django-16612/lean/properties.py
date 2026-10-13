# properties.py — G-PBT falsification battery for django__django-16612 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# AUDITED TWICE (independent adversarial passes over the ported battery).
#
# FIRST PASS: re-derived the six ported cases with real builds and appended three
# attack-D gap closures (assembly ORDER, encoder IDENTITY, the empty-query TRUE
# branch), all REJECTED.
#
# SECOND PASS (independent; this is the record that matters where the two differ):
# all NINE reject cases were rebuilt three ways — witness vs rival (exit 0), witness
# vs the frozen solution (exit 1), consistency probe (exit 1) — reproducing every
# recorded outcome. The gold-side failures were then established as SEMANTIC by
# experiment rather than by reading, which is the part the first pass argued instead
# of measuring:
#   * FORGERY pair: for each of the nine, a file differing from the witness ONLY in
#     dropping the `¬` (i.e. claiming the frozen construction is WRONG's opposite —
#     that the postcondition HOLDS there) was built against the frozen solution. All
#     nine fail with `No goals to be solved`, never the witness's own error, so
#     gold's exit code tracks the CLAIM and not the tactic script.
#   * TYPE/GOAL REVEAL pair: truncating each witness at its first `rw`/`intro` and
#     forcing a type error prints the goal on each side. Against the frozen solution
#     it is uniformly `¬True` — `simp` PROVED the postcondition equation — while
#     against each rival it is the concrete, visibly DIFFERENT pair of
#     concatenations (e.g. `¬(esc path ++ slash) ++ "" = (esc path ++ slash) ++
#     ("?" ++ enc "b")`). That pair is the refutation.
#   * MIRROR claims: the frozen construction SATISFIES the postcondition at each
#     witness input, and universally (exit 0).
# Statement integrity (attack A) re-checked at BYTE level, not just modulo
# whitespace: every case's `theorem correct_*` statement is byte-identical to the
# frozen one.
#
# What the second pass CHANGED:
#   * ADMISSIBILITY was recorded as N/A on a reason that does not hold ("no
#     precondition hypothesis, so nothing can be PRECOND-TOO-STRONG"). The lane is
#     shippable here and is now shipped (`admiss-f2p-query-nondegenerate`), with its
#     claim measured load-bearing against a FALSE control. See LANES below.
#   * Added `pos-match-slash-branch`: a correct reshape that is NOT definitionally
#     equal to the frozen impl (the frozen `rfl` FAILS on it, exit 1), so it carries
#     a real obligation.
#
# THIRD PASS (independent adversarial audit; corrections it landed are marked
# [A3] at their site). It reproduced every recorded outcome with real builds —
# all 13 variants, and for each of the nine reject cases the witness against the
# rival (exit 0), the witness against the frozen solution (exit 1), the
# consistency probe (exit 1), the FORGERY with the `¬` dropped on BOTH sides
# (exit 1 each), and the TYPE-REVEAL pair — and it fixed two PROSE claims that
# real builds contradict:
#   * [A3-1] The second pass's ranking of the three positives was WRONG on
#     pos-flip-slash-branch. It claimed pos-match was the only positive the
#     frozen script cannot discharge, describing the other two as ones "the
#     frozen script's reduction still reaches" / that "still reduce
#     branch-wise". Measured: putting the frozen proof body back on
#     pos-flip's impl FAILS, exit 1 — `Tactic `rfl` failed … (!path.endsWith
#     "/") = true then "/" else "" … is not definitionally equal to`. So TWO of
#     the three positives carry a real obligation, and only pos-direct is
#     closed by the frozen `rfl` (it is the frozen impl with the `Id.run do`
#     wrapper inlined). Corrected in both rationales below.
#   * [A3-2] The admissibility case's carrier note quoted the wrong stall term
#     for `String.endsWith` at a literal. The CONCLUSION is confirmed —
#     `decide`, `decide +kernel`, `rfl` and `simp [String.endsWith]` all fail on
#     `("/x/y" : String).endsWith "/" = false`, four builds, exit 1 each — and
#     the `decide` pair stalls at the `Decidable` instance:
#     `instDecidableEqBool ("/x/y".endsWith "/") false did not reduce to
#     `isTrue` or `isFalse``. Corrected at the note.
#
# FOURTH PASS (independent adversarial audit; corrections marked [A4]). It
# reproduced all 13 recorded variant outcomes and, for each of the nine reject
# cases, the witness vs rival (exit 0), witness vs the frozen solution (exit 1),
# the consistency probe (exit 1), the FORGERY with `¬` dropped on BOTH sides
# (exit 1 each) and a GOAL/TYPE-REVEAL pair — 84 builds in the first sweep, ~130
# in total. Every recorded outcome held. It landed one gap closure and corrected
# two PROSE claims that real builds contradict:
#   * [A4-1] The [A3-2] correction OVERSHOT. It is true that `decide` and
#     `decide +kernel` stall at `instDecidableEqBool`, but the claim that the
#     `takeRight`/`Substring` term "appears in none of the four logs" is FALSE:
#     `simp [String.endsWith]` unfolds precisely to it and leaves
#     `⊢ ("/x/y".toSubstring.takeRight "/".length == "/".toSubstring) = false`
#     (measured, exit 1). BOTH stall terms are real; they belong to different
#     tactics, and the second pass's original note was describing the `simp`
#     route rather than being simply wrong. The CONCLUSION that mattered — no
#     available tactic decides `String.endsWith` at a literal, so the path axis
#     must be stated over a universally bound `p` — is unaffected and is what
#     the case actually rests on. Corrected at the note.
#   * [A4-2] The FRAME-MUTATION lane's demonstration cited the wrong spelling
#     and inverted its exit code. `let mut path := path` … `path := path ++ "/"`
#     does NOT verify: measured exit 1, `Tactic `rfl` failed: The left-hand side
#     (have path := path; have path := path ++ "/"; …)`. That spelling SHADOWS
#     the input binding, so everything downstream reads the written value and the
#     write IS observable — it is an ordinary wrong-value rival, not a frame
#     violation. The spelling that verifies (exit 0, frozen `rfl` untouched) is a
#     write to a FRESH local that the result never reads. The lane's CONCLUSION
#     is unchanged and is now demonstrated on the right pair: in a language with
#     no aliasing a write either escapes into the value (and is an ordinary
#     value rival, already covered) or does not (and is unobservable, so it
#     verifies). Either way there is no FRAME obligation to violate, which is
#     what makes the lane vacuous. Corrected at the lane note.
# Attack D, fourth pass: `escape (path ++ "/")` with the slash decision left on
# the ORIGINAL path (a single-axis attack on the path encoder's ARGUMENT — the
# one piece no shipped rival isolated) is REJECTED with a discriminating witness,
# and is now SHIPPED as `pd-path-encoder-argument`. Four more — the escaped path
# replaced by `""`, by a CONSTANT path, the query suffix moved to the FRONT of
# the target, and the emptiness guard tested on the ENCODED query — all REJECTED,
# exit 1. Attack E, fourth pass: right-associated concatenation, a 4-way nested
# `if` with no `let`s, an `isEmpty` guard, `cond` on the slash Bool, an explicit
# `= true` slash test, `String.join`, a `List.foldl` over the three pieces and a
# `let mut` accumulator all VERIFY, exit 0. The `queryString.length = 0` guard
# also verifies (exit 0) but NOT with a `String.length_eq_zero_iff` rewrite —
# that identifier does not resolve under this pin, and `simp` makes no progress
# on `s.length = 0 ↔ s = ""`; it needs an explicit case split on
# `queryString = ""` with the length side discharged by `cases queryString`.
# Recorded because the third pass's list named the reshape without the proof it
# actually needs. No spec hole in either direction.
# Attack D, third pass: seven MORE wrong impls beyond the seventeen already
# recorded — trailing slash folded into the ESCAPER'S ARGUMENT (`escape (path ++
# "/")` with the slash piece emptied), the slash decision tested on the ESCAPED
# path, the emptiness guard tested on the ENCODED query, the slash PREFIXED to
# the whole target rather than appended to the path, the `?` folded INTO the
# encoder's argument (`encode ("?" ++ q)`), a bare `?` emitted on the empty-query
# branch while the non-empty branch stays correct, and the guard on the ENCODED
# query's LENGTH — all REJECTED, exit 1. Attack E, third pass: a 4-way nested
# `if` with no `let`s, `cond` on the slash Bool, `String.join` over the three
# pieces, explicit `String.append` calls right-nested, and a `queryString.length
# = 0` guard all VERIFY, exit 0 (each needed its own proof; the frozen `rfl`
# closes none of them). Still no spec hole in either direction.
#   * The first pass's attack-E list named an accumulator `for` loop as verifying.
#     Re-measured: that reshape does NOT verify with a plain `simp`/`rfl` proof (the
#     `forIn`/`ForInStep` term does not reduce); it verifies only once the loop is
#     unfolded explicitly (`simp only [Id.run, List.forIn_cons, List.forIn_nil, …]`),
#     exit 0. Recorded so the claim matches what a build actually does.
# Attack D, second pass: eight NEW wrong impls beyond the shipped nine — slash
# decision testing CONTAINS-'/' / STARTS-WITH-'/' / entangled with query emptiness,
# query suffix DOUBLED, query TRUNCATED at 3 chars (correct on every query any
# shipped witness probes), path through the QUERY encoder, path encoder applied
# TWICE, query guard tested on the PATH — all REJECTED, exit 1. Attack E, second
# pass: `String.isEmpty`, right-associated concatenation, a `==` (BEq) guard, a
# `match` on the Bool, and the unfolded accumulator loop all VERIFY, exit 0. No
# faithful reshape is rejected and no wrong impl is admitted: no spec hole.
#
# FIFTH PASS (independent adversarial audit; corrections marked [A5]). It
# reproduced every recorded outcome with real builds — all 14 variants; for each
# of the ten reject cases the witness vs rival (exit 0), the witness vs the
# frozen solution (exit 1), the consistency probe (exit 1), the FORGERY with the
# `¬` dropped on BOTH sides (exit 1 each, and on gold the error is `No goals to
# be solved`, NOT the witness's own error, so gold's exit code tracks the CLAIM),
# a GOAL-REVEAL pair (gold uniformly `¬True`, i.e. `simp` PROVED the
# postcondition equation there; each rival a concrete pair of visibly different
# concatenations), and a MIRROR claim (the frozen construction SATISFIES the
# postcondition at each witness input, exit 0) — 123 builds. It re-checked
# statement integrity at BYTE level, and additionally diffed every region
# OUTSIDE impl/proof line-for-line: identical for all 14. It re-measured all
# four prior prose corrections ([A3-1], [A3-2]/[A4-1], [A4-2]) and every one
# holds as written. It landed one lane gap closure:
#   * [A5-1] Every shipped soundness positive reshapes the SLASH decision
#     (pos-flip: branch polarity; pos-match: elimination form) or is the frozen
#     impl with the `Id.run do` wrapper inlined (pos-direct). NONE reshaped the
#     QUERY guard — the clause this specification exists to pin, and the clause
#     five of the ten rivals attack. So the SOUNDNESS direction on the query
#     axis was undefended: had the query clause been over-fit to the
#     `if queryString = "" then … else …` spelling, a faithful patch writing
#     the guard with the opposite polarity would be REJECTED and nothing in this
#     battery would have noticed. Measured and now SHIPPED as
#     `pos-flip-query-branch`: the negated guard VERIFIES (exit 0) with its own
#     proof, and carries a REAL obligation — the frozen proof body on that impl
#     FAILS, exit 1 (`Tactic `rfl` failed … if (queryString ≠ "") = true then
#     "?" ++ … is not definitionally equal to`). Two further query-axis
#     reshapes were measured and are NOT shipped (one positive per axis is the
#     point): `String.isEmpty` as the guard VERIFIES (exit 0) and also fails the
#     frozen `rfl` (exit 1), while the `dite` spelling
#     (`if h : queryString = "" then …`) verifies under the frozen `rfl`
#     UNCHANGED (exit 0) and so would carry no obligation.
# Attack D, fifth pass: ten MORE wrong impls beyond everything above — a DOUBLE
# slash on the append branch, a trailing `?` after the encoded query, the slash
# piece emitted a second time at the END of the target, the slash decision
# tested on the QUERY string, the escaped path emitted TWICE, a
# `queryString.length = 1` guard, the emptiness guard tested on the ENCODED
# query, the `?` folded into the encoder argument, the RAW query in place of the
# encoded one, and the slash piece moved to the FRONT of the target — all
# REJECTED, exit 1. Attack E, fifth pass: the negated query guard, the `dite`
# query guard, an `isEmpty` query guard, right-associated concatenation and an
# `++ ""` on the query encoder's argument all VERIFY, exit 0. A `match
# queryString = "" with | true => … | false => …` spelling was NOT closed by the
# audit's `by_cases` proof (`Dependent elimination failed`), which is a matter of
# the tactic script rather than of the spec — the same axis is demonstrated
# verifiable by the shipped `pos-flip-query-branch` and by the `dite` and
# `isEmpty` measurements, so it is recorded as UNCERTAIN, not as a hole. No spec
# hole in either direction.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   redirectTargetWithTrailingSlash : String → String → String
#   The redirect-target string built from the requested path and the accompanying
#   query string. The single postcondition pins the result to the concatenation of
#   three grounded pieces:
#     (A) the ESCAPED path (an opaque URI-path encoder applied to the input path);
#     (B) a trailing "/" appended IFF the path does not already end in "/"
#         (conditional on `path.endsWith "/"`);
#     (C) a query suffix "?" ++ ENCODED query appended IFF the query is non-empty
#         (conditional on `queryString = ""`), where the encoder is an opaque
#         URI-query encoder applied to the input query. When the query is empty,
#         nothing is appended.
#
# CARRIER NOTE: the nagini sibling abstracted this construction to a fold over a
# `List[int]` of code points behind fractional read permission, with a fully
# unfolded `redirect_target` oracle. This backend models the SAME construction over
# `String`, but the two URI encoders are OPAQUE leaves (`escapePathComponent`,
# `encodeQueryString`) validated against the real callees by G-AX. The value each
# encoder returns cannot be computed, so the reject witnesses CONDITION on the
# carrier (route 3/1 of the spec guide): they attack the transparent COMBINATION of
# the opaque results — the trailing-slash decision, the "?" introducer, whether the
# escaped path is used at all, and which argument is passed to the query encoder —
# none of which needs the encoder's value.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's #1 mandatory class: `path`/`query` were held at
#     Acc(list_pred(...),1/2) read-only, and the rival wrote back into them —
#     `fm-write-path`, `fm-write-query`). Lean is referentially transparent — no
#     aliasing, no fractional permission — so a "store into a read-only input" rival
#     is not expressible and the whole lane is VACUOUS here. DEMONSTRATED during the
#     audit rather than asserted, and [A4-2] on the RIGHT pair of builds — the
#     third pass cited one spelling and inverted its exit code. A "write to a
#     read-only input" has exactly two expressible spellings here, and neither is a
#     frame violation:
#       - the write SHADOWS the binding (`let mut path := path` … `path := path ++
#         "/"`), so everything downstream reads the written value. Measured: exit
#         1, `Tactic `rfl` failed: The left-hand side (have path := path; have path
#         := path ++ "/"; …)`. The write escapes into the RESULT, so this is an
#         ordinary wrong-value rival — the same defect `pd-path-encoder-argument`
#         and `pd-always-slash` already attack — not a permission violation.
#       - the write lands in a FRESH local the result never reads (`let mut p :=
#         path` … `p := p ++ "/"`, with the escaper still applied to `path`).
#         Measured: VERIFIES, exit 0, frozen `rfl` untouched — the write changes no
#         observable, so the impl is CORRECT and there is nothing to reject.
#     With no aliasing a write either escapes into the value (already covered by
#     the value lane) or it does not (and the impl is correct). There is no third
#     case, hence no FRAME obligation to violate and no reject case for this lane
#     to carry. See 'assessment'.
#   * ADMISSIBILITY — NOT a lane that fails to port. SECOND-AUDIT CORRECTION: the
#     prior pass recorded this lane N/A because "the lean obligation carries NO
#     precondition hypothesis, so nothing could be PRECOND-TOO-STRONG". That reason
#     is REJECTED and the case is now SHIPPED (`admiss-f2p-query-nondegenerate`).
#     The absence of a precondition binder is not what would make the lane vacuous:
#     the analogue of PRECOND-TOO-STRONG on a TOTAL carrier is the obligation being
#     unsatisfiable or DEGENERATE at exactly an F2P-shaped input, which no other
#     case here tests. Both positive controls discharge the obligation UNIVERSALLY,
#     and that is strictly weaker than the fact that its post-image at the
#     interesting point is the value the behavior actually requires — a universally
#     satisfiable clause can collapse at the one point that matters and nothing else
#     in this battery would notice. See the case's own rationale for what it
#     discharges and for the measured proof that its claim is load-bearing.
#   * DIVERGENCE / non-termination. This bundle is vanilla Lean 4 + Mathlib: it sets
#     NO `loom.semantics.termination` option (that option belongs to the other
#     lean-family backend), and the modeled construction is straight-line string
#     assembly with no loop and no recursion, so there is no measure to omit. The
#     only expressible diverging shape is a self-recursive `partial def`, and
#     re-measured with real builds in the second pass: such a rival is REJECTED
#     (exit 1) because `partial` makes the definition irreducible, so the frozen
#     obligation cannot be closed at all. It is NOT shippable as a reject case,
#     though, because the rejection is not attributable to the spec: a witness
#     against that rival fails on the RIVAL side too, with the same
#     `Tactic 'unfold' failed to unfold implementation_…` (exit 1, measured), so no
#     witness can discriminate and the case would be recorded `witness-unproven`.
#     Disposition: nothing to ship, and the class is genuinely vacuous here (no loop
#     to strip a measure from) rather than a hole in this spec. Distinct from the
#     partial-semantics vacuity already escalated for the OTHER lean-family backend
#     (the corpus-wide termination-semantics finding, scope "401 of 500 velvet bundles. Lean and nagini
#     are unaffected") — cited, not re-derived, and not a spec_holes entry here.
#   * AXIOM_TESTS (`ax-refine-redirect-target-identity`). The axiom lane is G-AX's
#     job; this gate ignores it (the two URI encoders are the A-reference leaves G-AX
#     validates against the real callees).
from pathlib import Path

INSTANCE = "django__django-16612"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- impl-region anchors (each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file). One per grounded piece of the construction. -----------------
_A_PATH = "  let escapedPath := escapePathComponent path\n"
_A_SLASH = '  let trailingSlash := if path.endsWith "/" then "" else "/"\n'
_A_QUERY = ('  let querySuffix := if queryString = "" then "" else "?" '
            "++ encodeQueryString queryString\n")
for _a in (_A_PATH, _A_SLASH, _A_QUERY):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"

# The frozen proof body (only the tactic lines, inside proof-start/proof-end).
_PROOF = (
    "  intro path queryString\n"
    "  unfold problem_spec_redirectTargetWithTrailingSlash "
    "implementation_redirectTargetWithTrailingSlash\n"
    "  rfl"
)
assert _BASE.count(_PROOF) == 1, "proof body anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-flip-slash-branch: structurally DIFFERENT but behaviourally identical. The
# trailing-slash decision `if path.endsWith "/" then "" else "/"` is rewritten as the
# negated test `if !(path.endsWith "/") then "/" else ""`, which selects the same
# branch on every input; only the branch FORM changes — the shape a faithful patch
# could equally take. The frozen `rfl` proof no longer closes the negated branch, so
# the proof body is honestly re-closed by case-splitting on `path.endsWith "/"` (no
# new axiom/lemma/sorry; the `theorem correct_*` STATEMENT is byte-identical). [A3-1]
# This carries a REAL obligation, not a near-reducible one: the frozen proof body on
# this impl fails, exit 1, `Tactic `rfl` failed: … (!path.endsWith "/") = true then
# "/" else "" … is not definitionally equal to …` (measured in the third audit,
# correcting the second's description of this case). If it FAILS => SPEC-TOO-STRONG
# (postcondition over-fit to one branch form).
_POS_FLIP = _swap(
    _swap(_BASE, _A_SLASH,
          '  let trailingSlash := if !(path.endsWith "/") then "/" else ""\n'),
    _PROOF,
    "  intro path queryString\n"
    "  unfold problem_spec_redirectTargetWithTrailingSlash "
    "implementation_redirectTargetWithTrailingSlash\n"
    "  simp only [Id.run, pure, Bool.not_eq_true']\n"
    '  rcases Bool.eq_false_or_eq_true (path.endsWith "/") with hp | hp <;> simp [hp]',
)

# pos-direct: the cheapest HONEST impl. The postcondition RHS is fully GROUNDED in
# the two inputs (path/query threaded through the opaque encoders and the two
# transparent conditionals), so returning that exact expression is a fully-grounded
# correct impl, NOT an ungrounded-oracle echo — there is no opaque answer-key to
# echo (any WRONG constant/argument fails the postcondition, as the rivals show).
# The `Id.run do` wrapper is inlined to the bare expression; the proof collapses to
# `rfl`. MUST verify (postcondition is literally result = <that expression>); else
# SPEC-TOO-STRONG.
_POS_DIRECT = _swap(
    _BASE,
    _A_PATH + _A_SLASH + _A_QUERY
    + "  return escapedPath ++ trailingSlash ++ querySuffix\n",
    '  escapePathComponent path\n'
    '    ++ (if path.endsWith "/" then "" else "/")\n'
    '    ++ (if queryString = "" then "" else "?" ++ encodeQueryString queryString)\n',
)

# pos-match-slash-branch: a THIRD correct reshape, added by the second audit,
# whose impl is NOT definitionally equal to the frozen one — the trailing-slash
# decision is written as a `match` on the Bool rather than an `if`, so the frozen
# `rfl` no longer closes it (measured: exit 1 with the frozen proof body, "Tactic
# `rfl` failed … is not definitionally equal to"). The proof is honestly re-closed
# by case-splitting on the same Bool. It probes a DIFFERENT axis from
# pos-flip-slash-branch — the elimination FORM (`match` vs `if`) rather than the
# branch polarity — and both carry a real obligation. [A3-1] The second pass
# claimed this was the ONLY positive the frozen script cannot discharge, calling
# the other two ones the frozen reduction "still reaches"; that is FALSE for
# pos-flip-slash-branch, whose impl also fails under the frozen proof body (exit
# 1, measured in the third audit). Only pos-direct is closed by the frozen `rfl`,
# and that is by construction — it IS the frozen impl with the `Id.run do`
# wrapper inlined. If it FAILS => SPEC-TOO-STRONG (the slash clause over-fit
# to the `if` spelling rather than to the behavior).
_POS_MATCH = _swap(
    _swap(_BASE, _A_SLASH,
          '  let trailingSlash := match path.endsWith "/" with\n'
          '    | true => ""\n'
          '    | false => "/"\n'),
    _PROOF,
    "  intro path queryString\n"
    "  unfold problem_spec_redirectTargetWithTrailingSlash "
    "implementation_redirectTargetWithTrailingSlash\n"
    "  simp only [Id.run, pure]\n"
    '  cases hp : path.endsWith "/" <;> simp [hp]',
)

# pos-flip-query-branch [A5-1]: the SOUNDNESS control on the QUERY axis, which
# the three positives above leave undefended (each of them reshapes the SLASH
# decision, or is the frozen impl with the `Id.run do` wrapper inlined). The
# emptiness guard `if queryString = "" then "" else "?" ++ enc queryString` is
# rewritten with the OPPOSITE polarity, `if queryString ≠ "" then "?" ++ enc
# queryString else ""`, which selects the same branch on every input; only the
# guard FORM changes — and it is exactly the shape a faithful patch would take if
# it tested for a query string being PRESENT rather than absent. This is the
# clause the specification exists to pin and the clause five of the ten rivals
# attack, so leaving its soundness direction untested meant an over-fit query
# clause would have gone unnoticed: the reject lane cannot distinguish "the spec
# pins the behavior" from "the spec pins this spelling of the guard".
# It carries a REAL obligation, measured: the frozen proof body on this impl
# FAILS, exit 1 (`Tactic `rfl` failed … `if (queryString ≠ "") = true then "?" ++
# encodeQueryString queryString else ""` … not definitionally equal`), so the
# proof is honestly re-closed by a case split on `queryString = ""` (no new
# axiom/lemma/sorry; the `theorem correct_*` STATEMENT stays byte-identical).
# If it FAILS => SPEC-TOO-STRONG (query clause over-fit to the guard's polarity).
_POS_FLIP_QUERY = _swap(
    _swap(_BASE, _A_QUERY,
          '  let querySuffix := if queryString ≠ "" then "?" '
          '++ encodeQueryString queryString else ""\n'),
    _PROOF,
    "  intro path queryString\n"
    "  unfold problem_spec_redirectTargetWithTrailingSlash "
    "implementation_redirectTargetWithTrailingSlash\n"
    "  simp only [Id.run, pure, ne_eq]\n"
    '  by_cases hq : queryString = "" <;> simp [hq]',
)


# ===========================================================================
# ADMISSIBILITY (non-degeneracy at the F2P-shaped input) — must VERIFY.
# ===========================================================================

# admiss-f2p-query-nondegenerate: discharge, BY EVALUATION and in-region ahead of
# the frozen obligation, that at an F2P-shaped input — a request carrying a
# NON-EMPTY query string — the obligation's post-image is (a) exactly the
# query-preserving destination (escaped path ++ the slash decision ++ `?` ++ the
# ENCODED query, with the query branch RESOLVED by deciding `"id=1" ≠ ""`) and
# (b) DISTINCT from the image at the same path with NO query. Only then is the
# frozen obligation closed verbatim.
#
# Why (b) is the load-bearing half: (a) alone would follow from the universal
# clause the two positives already discharge. (b) says the modeled construction
# actually SEPARATES the two query regimes at a shared path — i.e. the query
# component is not a degenerate collapse at the point the behavior is observed —
# which no other case in this battery states. It is proven on the transparent
# combination (append + length), never on an encoder's value, so it needs no
# property of either opaque leaf.
#
# The claim is load-bearing, not decoration: the SAME case with a FALSE claim
# about the same point (the destination written WITHOUT its `?` introducer) leaves
# `⊢ (… ++ ("?" ++ enc "id=1")) = (… ++ enc "id=1")` unsolved and the
# length argument's `omega` unprovable, and fails to build (exit 1) — measured.
#
# NOTE ON THE CARRIER: the path side of this is stated over a UNIVERSALLY bound
# `p` rather than a literal F2P path, because `String.endsWith` does not reduce on
# a string literal under this pin (`decide`, `decide +kernel`, `rfl`, and
# `simp [String.endsWith]` all fail on `"/x/y".endsWith "/" = false`; measured
# again in the fourth audit, exit 1 on all four). [A4-1] WHERE it stalls depends on
# the TACTIC, and the two prior passes each described one route and denied the
# other; both terms are real:
#   * `decide` / `decide +kernel` stall at the `Decidable` instance —
#     `instDecidableEqBool ("/x/y".endsWith "/") false did not reduce to `isTrue`
#     or `isFalse``, after unfolding `decEq`, `instDecidableEqBool`, `Bool.decEq`,
#     `Nat.decEq`, `String.instDecidableLePos` and the rest.
#   * `simp [String.endsWith]` DOES reach the substring comparison the second pass
#     named, and leaves it unsolved:
#     `⊢ ("/x/y".toSubstring.takeRight "/".length == "/".toSubstring) = false`.
#     So the third pass's "that term appears in none of the four logs" was wrong;
#     it appears in exactly the `simp` log.
#   * `rfl` reports the left-hand side is not definitionally equal to `false`.
# Only `native_decide` closes it, and that is banned. What the case rests on is
# the shared conclusion — no admissible tactic decides `String.endsWith` at a
# literal — which all four builds confirm. The
# universally-bound form is strictly stronger on that axis anyway — it holds at
# every path, including the F2P-shaped ones — and the query axis, which is the
# component this specification exists to pin, IS decided at the literal.
_ADMISS_HAVES = (
    '  have hq : ("id=1" : String) ≠ "" := by decide\n'
    "  have hf2p : ∀ p : String,\n"
    '      implementation_redirectTargetWithTrailingSlash p "id=1"\n'
    '        = escapePathComponent p ++ (if p.endsWith "/" then "" else "/")\n'
    '          ++ ("?" ++ encodeQueryString "id=1") := by\n'
    "    intro p\n"
    "    unfold implementation_redirectTargetWithTrailingSlash\n"
    "    simp only [Id.run, pure, if_neg hq]\n"
    "  have hnondeg : ∀ p : String,\n"
    '      implementation_redirectTargetWithTrailingSlash p "id=1"\n'
    '        ≠ implementation_redirectTargetWithTrailingSlash p "" := by\n'
    "    intro p\n"
    "    rw [hf2p p]\n"
    "    unfold implementation_redirectTargetWithTrailingSlash\n"
    "    simp only [Id.run, pure, if_pos]\n"
    "    intro hcon\n"
    "    have hlen := congrArg String.length hcon\n"
    "    simp only [String.length_append] at hlen\n"
    '    have h1 : ("?" : String).length = 1 := by decide\n'
    '    have h0 : ("" : String).length = 0 := by decide\n'
    "    simp only [h1, h0] at hlen\n"
    "    omega\n"
)
_ADMISS = _swap(_BASE, _PROOF, _ADMISS_HAVES + _PROOF)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; each carries a witness that
# elaborates against the rival and FAILS on the frozen solution.
# ===========================================================================

# RIVAL pd-drop-query (the EXACT pre-patch bug): never append the query suffix
# (build only escaped-path ++ slash). Correct on the empty-query sub-domain, WRONG
# whenever the query is non-empty.
_RIV_DROP_QUERY = _swap(_BASE, _A_QUERY, '  let querySuffix := ""\n')

# RIVAL pd-drop-qmark: append the encoded query but NOT the leading "?" introducer.
# Diverges on every non-empty query (produces ".../articleid=1" not
# ".../article?id=1").
_RIV_DROP_QMARK = _swap(
    _BASE, _A_QUERY,
    ('  let querySuffix := if queryString = "" then "" '
     "else encodeQueryString queryString\n"),
)

# RIVAL pd-drop-slash: never append the trailing slash. Correct only when the path
# already ends in "/"; WRONG for the F2P inputs (admin path WITHOUT trailing slash).
_RIV_DROP_SLASH = _swap(_BASE, _A_SLASH, '  let trailingSlash := ""\n')

# RIVAL pd-always-slash: append "/" UNCONDITIONALLY. Correct when the path lacks a
# trailing slash; WRONG when the path already ends in "/" (double slash).
_RIV_ALWAYS_SLASH = _swap(_BASE, _A_SLASH, '  let trailingSlash := "/"\n')

# RIVAL pd-drop-first-query-char: encode the query with its FIRST character dropped
# (queryString.drop 1). Correct only for empty query; diverges on every non-empty
# query whose first char changes the encoded output ("id=1" -> "d=1").
_RIV_DROP_FIRST_Q = _swap(
    _BASE, _A_QUERY,
    ('  let querySuffix := if queryString = "" then "" '
     "else \"?\" ++ encodeQueryString (queryString.drop 1)\n"),
)

# RIVAL pd-raw-path: use the RAW path instead of the escaped path (drop the URI-path
# encoder). Correct only where the encoder is the identity; WRONG on any path the
# encoder changes.
_RIV_RAW_PATH = _swap(_BASE, _A_PATH, "  let escapedPath := path\n")

# --- rivals added by the ADVERSARIAL AUDIT of this battery. The six above leave
# three pieces of the construction unattacked, each of which a faithful-looking
# patch could plausibly get wrong; all three were confirmed REJECTED by the frozen
# spec with a discriminating witness (so they are gap closures, not spec holes).

# RIVAL pd-suffix-order: emit the three pieces in the WRONG ORDER — the query suffix
# BEFORE the trailing slash. Every piece is present and correctly computed; only the
# assembly order is wrong. Attacks the CONCATENATION ORDER, which no rival above
# touches (each of those drops or alters one piece instead).
_RIV_SUFFIX_ORDER = _swap(
    _BASE,
    "  return escapedPath ++ trailingSlash ++ querySuffix\n",
    "  return escapedPath ++ querySuffix ++ trailingSlash\n",
)

# RIVAL pd-query-through-path-encoder: run the query string through the URI-PATH
# encoder instead of the URI-QUERY encoder. Both pieces are present, the `?` is
# there and the argument is the whole query — only the CHOICE OF ENCODER is wrong.
# The two encoders escape different reserved sets, so they disagree on real query
# strings; pd-drop-first-query-char attacks the encoder's ARGUMENT, this attacks
# WHICH encoder is applied.
_RIV_QUERY_PATH_ENC = _swap(
    _BASE, _A_QUERY,
    ('  let querySuffix := if queryString = "" then "" '
     'else "?" ++ escapePathComponent queryString\n'),
)

# RIVAL pd-path-encoder-argument [A4]: fold the trailing slash into the path
# ENCODER'S ARGUMENT (`escapePathComponent (path ++ "/")`) while leaving the
# trailing-slash decision itself on the ORIGINAL path, so the slash piece is still
# emitted. Single axis: this is the only rival that attacks WHICH ARGUMENT the
# PATH encoder receives. pd-raw-path drops that encoder entirely and
# pd-drop-first-query-char attacks the QUERY encoder's argument, so the path
# encoder's argument was the one grounded piece no shipped rival isolated — and a
# faithful-looking patch that pre-composed the slash onto the string it escapes is
# exactly the shape that lands there.
_RIV_PATH_ENC_ARG = _swap(
    _BASE, _A_PATH,
    '  let escapedPath := escapePathComponent (path ++ "/")\n',
)

# RIVAL pd-invert-query-test: INVERT the emptiness test — append the query suffix
# when the query IS empty and nothing when it is not. This is the only rival that
# attacks the `queryString = ""` TRUE branch (the "no query string present, append
# NOTHING" clause). Every query rival above lives on the false branch, so the spec's
# empty-query clause was previously undefended: a patch that mishandled the absent
# query (emitting a bare trailing `?`) would have gone unattacked.
_RIV_INVERT_QUERY = _swap(
    _BASE, _A_QUERY,
    ('  let querySuffix := if queryString = "" '
     'then "?" ++ encodeQueryString queryString else ""\n'),
)


# --- witness builders. Each states `¬ problem_spec … (implementation …)` at a
# point where the rival provably diverges from the frozen construction, closed by
# reasoning on the transparent COMBINATION (string length / append-cancellation),
# never on an opaque encoder's value. Each elaborates against its rival and FAILS on
# gold; conditioning hypotheses (below) are individually satisfiable.

_HEADER = (
    "  unfold problem_spec_redirectTargetWithTrailingSlash "
    "implementation_redirectTargetWithTrailingSlash\n"
)

# Length clash on a non-empty query: gold carries "?" (+encoded query); a rival that
# drops the suffix is one character (at least) shorter. Path is free.
_WIT_DROP_QUERY = (
    "-- non-empty query: gold appends `?`+encoded query, rival appends nothing;\n"
    "-- the lengths cannot match. Path free (prefix cancels).\n"
    'example (path : String) :\n'
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path "b"\n'
    '      (implementation_redirectTargetWithTrailingSlash path "b") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure]\n"
    '  have hq : ("b" : String) ≠ "" := by decide\n'
    "  rw [if_neg hq]\n"
    "  intro heq\n"
    "  have hlen := congrArg String.length heq\n"
    "  simp only [String.length_append] at hlen\n"
    '  have he : ("" : String).length = 0 := by decide\n'
    '  have hqm : ("?" : String).length = 1 := by decide\n'
    "  simp only [he, hqm] at hlen\n"
    "  omega"
)

# Length clash on the "?" introducer: gold's suffix is "?"++enc, the rival's is enc;
# they differ in length by exactly the one "?" character. Path free.
_WIT_DROP_QMARK = (
    "-- non-empty query: gold's query suffix carries the leading `?`, the rival's\n"
    "-- does not, so the two results differ in length by one. Path free.\n"
    'example (path : String) :\n'
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path "b"\n'
    '      (implementation_redirectTargetWithTrailingSlash path "b") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure]\n"
    '  have hq : ("b" : String) ≠ "" := by decide\n'
    "  rw [if_neg hq, if_neg hq]\n"
    "  intro heq\n"
    "  have hlen := congrArg String.length heq\n"
    "  simp only [String.length_append] at hlen\n"
    '  have hqm : ("?" : String).length = 1 := by decide\n'
    "  simp only [hqm] at hlen\n"
    "  omega"
)

# Conditioned on the carrier: a path that does NOT end in "/" (h). Empty query so the
# query suffix cancels on both sides. Gold appends "/", the rival appends "";
# lengths differ by one. `h` is satisfiable (e.g. path = "a").
_WIT_DROP_SLASH = (
    '-- path with NO trailing slash (h satisfiable, e.g. "a"), empty query: gold\n'
    "-- appends `/`, the rival appends nothing; lengths differ by one.\n"
    'example (path : String) (h : path.endsWith "/" = false) :\n'
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path ""\n'
    '      (implementation_redirectTargetWithTrailingSlash path "") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure, h, Bool.false_eq_true, if_false]\n"
    "  intro heq\n"
    "  have hlen := congrArg String.length heq\n"
    "  simp only [String.length_append] at hlen\n"
    '  have he : ("" : String).length = 0 := by decide\n'
    '  have hs : ("/" : String).length = 1 := by decide\n'
    "  simp only [he, hs] at hlen\n"
    "  omega"
)

# Conditioned on the carrier: a path that DOES end in "/" (h). Empty query. Gold
# appends "" (already slashed), the rival appends "/" unconditionally; lengths differ
# by one. `h` is satisfiable (e.g. path = "a/").
_WIT_ALWAYS_SLASH = (
    '-- path that DOES end in `/` (h satisfiable, e.g. "a/"), empty query: gold\n'
    "-- appends nothing (already slashed), the rival appends `/` anyway.\n"
    'example (path : String) (h : path.endsWith "/" = true) :\n'
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path ""\n'
    '      (implementation_redirectTargetWithTrailingSlash path "") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure, h, if_true]\n"
    "  intro heq\n"
    "  have hlen := congrArg String.length heq\n"
    "  simp only [String.length_append] at hlen\n"
    '  have he : ("" : String).length = 0 := by decide\n'
    '  have hs : ("/" : String).length = 1 := by decide\n'
    "  simp only [he, hs] at hlen\n"
    "  omega"
)

# Conditioned on the carrier (route 3, on the encoder ARGUMENT): a non-empty query
# whose first-char-dropped encoding differs from its full encoding (h). Gold encodes
# the whole query; the rival encodes `queryString.drop 1`. Left-cancel the shared
# prefix and the shared "?" to expose the encoder disagreement. Both hyps
# individually satisfiable (e.g. query = "id", encoder injective on the tail).
_WIT_DROP_FIRST_Q = (
    "-- non-empty query whose first-char-dropped encoding differs from the full\n"
    "-- encoding (h). Gold encodes the whole query, the rival encodes the tail;\n"
    "-- after cancelling the shared prefix and `?` the encoder outputs must match.\n"
    'example (path queryString : String) (hne : queryString ≠ "")\n'
    "    (h : encodeQueryString (queryString.drop 1) ≠ encodeQueryString queryString) :\n"
    "    ¬ problem_spec_redirectTargetWithTrailingSlash path queryString\n"
    "      (implementation_redirectTargetWithTrailingSlash path queryString) := by\n"
    + _HEADER +
    "  simp only [Id.run, pure]\n"
    "  rw [if_neg hne, if_neg hne]\n"
    "  intro heq\n"
    "  apply h\n"
    "  have hd := congrArg String.data heq\n"
    "  simp only [String.data_append] at hd\n"
    "  have h1 := List.append_cancel_left hd\n"
    "  have h2 := List.append_cancel_left h1\n"
    "  exact String.ext h2"
)

# Conditioned on the carrier (route 1, on the path encoder): a path the encoder does
# NOT fix (h). Empty query so the suffix cancels. Gold uses `escapePathComponent
# path`, the rival uses the raw `path`; right-cancel the shared slash to expose the
# disagreement. `h` is satisfiable (the encoder is a non-identity map somewhere).
_WIT_RAW_PATH = (
    "-- a path the URI-path encoder does not fix (h). Empty query so the suffix\n"
    "-- cancels; the trailing slash is shared. Gold uses the escaped path, the\n"
    "-- rival uses the raw path; right-cancelling the slash exposes the mismatch.\n"
    "example (path : String) (h : escapePathComponent path ≠ path) :\n"
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path ""\n'
    '      (implementation_redirectTargetWithTrailingSlash path "") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure, if_true, String.append_empty]\n"
    "  intro heq\n"
    "  apply h\n"
    "  have hd := congrArg String.data heq\n"
    "  simp only [String.data_append] at hd\n"
    "  have h1 := List.append_cancel_right hd\n"
    "  exact (String.ext h1).symm"
)


# Conditioned on the carrier: a path that does NOT end in "/" (h), non-empty query.
# Gold's tail is the encoded query, the rival's tail is "/". Left-cancel the shared
# escaped path, then the two tails cannot match (one begins with "/", the other with
# "?"). `h` is satisfiable (e.g. path = "a") — no assumption about either encoder.
_WIT_SUFFIX_ORDER = (
    '-- path with NO trailing slash (h satisfiable, e.g. "a"), non-empty query:\n'
    "-- gold emits path++`/`++`?`enc, the rival emits path++`?`enc++`/`. After\n"
    "-- left-cancelling the shared escaped path the two remainders start with a\n"
    "-- different character, so the assembly ORDER is what is refuted.\n"
    'example (path : String) (h : path.endsWith "/" = false) :\n'
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path "b"\n'
    '      (implementation_redirectTargetWithTrailingSlash path "b") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure, h, Bool.false_eq_true, if_false]\n"
    '  have hq : ("b" : String) ≠ "" := by decide\n'
    "  rw [if_neg hq]\n"
    "  intro heq\n"
    "  have hd := congrArg String.data heq\n"
    "  simp only [String.data_append, List.append_assoc] at hd\n"
    "  have h1 := List.append_cancel_left hd\n"
    "  simp at h1"
)

# Conditioned on the carrier (route 3, on WHICH encoder is applied): a non-empty
# query the two encoders do not agree on (h). Left-cancel the shared prefix and the
# shared "?" to expose the encoder disagreement. Both hyps individually satisfiable
# (the two encoders escape different reserved sets, so they differ on real queries).
_WIT_QUERY_PATH_ENC = (
    "-- non-empty query on which the path encoder and the query encoder disagree\n"
    "-- (h). Gold applies the query encoder, the rival applies the path encoder;\n"
    "-- after cancelling the shared prefix and `?` their outputs must match.\n"
    'example (path queryString : String) (hne : queryString ≠ "")\n'
    "    (h : escapePathComponent queryString ≠ encodeQueryString queryString) :\n"
    "    ¬ problem_spec_redirectTargetWithTrailingSlash path queryString\n"
    "      (implementation_redirectTargetWithTrailingSlash path queryString) := by\n"
    + _HEADER +
    "  simp only [Id.run, pure]\n"
    "  rw [if_neg hne, if_neg hne]\n"
    "  intro heq\n"
    "  apply h\n"
    "  have hd := congrArg String.data heq\n"
    "  simp only [String.data_append] at hd\n"
    "  have h1 := List.append_cancel_left hd\n"
    "  have h2 := List.append_cancel_left h1\n"
    "  exact String.ext h2"
)

# Conditioned on the carrier (route 1, on the path encoder's ARGUMENT): a path
# whose escaping CHANGES when a "/" is appended to the encoder's argument (h).
# Empty query so the suffix cancels; the trailing-slash piece is computed from the
# ORIGINAL path on both sides, so it is shared and right-cancels, leaving exactly
# the two encoder applications. `h` is satisfiable — no tactic can derive False
# from a disagreement between two applications of an opaque map (probe measured
# exit 1, residual goal `h : ¬escapePathComponent (path ++ "/") =
# escapePathComponent path ⊢ False`).
_WIT_PATH_ENC_ARG = (
    "-- a path whose escaping is changed by appending a `/` to the ENCODER'S\n"
    "-- ARGUMENT (h). Empty query so the suffix cancels; the trailing-slash piece\n"
    "-- is computed from the original path on both sides, so right-cancelling it\n"
    "-- exposes the encoder-argument mismatch.\n"
    'example (path : String)\n'
    '    (h : escapePathComponent (path ++ "/") ≠ escapePathComponent path) :\n'
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path ""\n'
    '      (implementation_redirectTargetWithTrailingSlash path "") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure, if_true, String.append_empty]\n"
    "  intro heq\n"
    "  apply h\n"
    "  have hd := congrArg String.data heq\n"
    "  simp only [String.data_append] at hd\n"
    "  have h1 := List.append_cancel_right hd\n"
    "  exact String.ext h1"
)


# The EMPTY-query branch, at a literal input — no hypotheses at all (so no
# consistency probe is even needed). Gold appends nothing; the rival appends
# "?"++enc "", which is at least the one "?" character longer. Path is free.
_WIT_INVERT_QUERY = (
    "-- EMPTY query at a literal input: gold appends nothing, the rival appends\n"
    "-- `?`+the encoded empty query, so the results differ in length by at least\n"
    "-- the one `?` character. Path free (prefix cancels); no hypotheses.\n"
    "example (path : String) :\n"
    '    ¬ problem_spec_redirectTargetWithTrailingSlash path ""\n'
    '      (implementation_redirectTargetWithTrailingSlash path "") := by\n'
    + _HEADER +
    "  simp only [Id.run, pure, if_true]\n"
    "  intro heq\n"
    "  have hlen := congrArg String.length heq\n"
    "  simp only [String.length_append] at hlen\n"
    '  have hqm : ("?" : String).length = 1 := by decide\n'
    '  have he : ("" : String).length = 0 := by decide\n'
    "  simp only [hqm, he] at hlen\n"
    "  omega"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-flip-slash-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLIP,
        "rationale": (
            "structurally-different but CORRECT impl: the trailing-slash decision "
            "`if path.endsWith \"/\" then \"\" else \"/\"` is rewritten as the "
            "negated `if !(path.endsWith \"/\") then \"/\" else \"\"`, which selects "
            "the same branch on every input; only the branch FORM changes. The "
            "frozen `theorem correct_redirectTargetWithTrailingSlash` statement is "
            "kept byte-identical and the proof body is honestly re-closed by a case "
            "split on `path.endsWith \"/\"` (no new axiom/lemma/sorry). It carries "
            "a REAL obligation, measured: the frozen proof body on this impl "
            "FAILS, exit 1 (`Tactic \\`rfl\\` failed … `(!path.endsWith \"/\") = "
            "true then \"/\" else \"\"` … not definitionally equal`), so the "
            "reshape is not one the frozen reduction merely walks through. If it "
            "FAILS => SPEC-TOO-STRONG (postcondition over-fit to one branch form)."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the postcondition RHS is fully GROUNDED in the two inputs (path/query "
            "through the opaque encoders and the two transparent conditionals), so "
            "returning that exact expression (the `Id.run do` wrapper inlined) is "
            "the honest cheapest CORRECT impl, not an ungrounded echo; the proof "
            "collapses to `rfl`. Must verify (postcondition is literally result = "
            "<that expression>); else SPEC-TOO-STRONG. Also shows the spec is not "
            "echo-vulnerable: any wrong constant/argument fails the postcondition, "
            "as the rivals demonstrate."
        ),
    },
    {
        "id": "pos-match-slash-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MATCH,
        "rationale": (
            "a CORRECT reshape that is NOT definitionally equal to the frozen "
            "impl: the trailing-slash decision is written as a `match` on "
            "`path.endsWith \"/\"` rather than an `if`, so the frozen `rfl` no "
            "longer closes it (measured: the frozen proof body FAILS on this impl, "
            "exit 1, `Tactic \\`rfl\\` failed … not definitionally equal`) and the "
            "proof is honestly re-closed by a case split on the same Bool. It "
            "shows the slash clause pins BEHAVIOR and not the spelling of the "
            "branch, on a different axis from pos-flip-slash-branch: the "
            "ELIMINATION FORM (`match` vs `if`) rather than the branch polarity. "
            "A third audit CORRECTED the second's ranking here: the claim that "
            "this was the only positive the frozen script cannot discharge, the "
            "other two being reshapes 'the frozen script's reduction still "
            "reaches', is FALSE for pos-flip-slash-branch — its impl also fails "
            "under the frozen proof body (exit 1, measured). Only pos-direct is "
            "closed by the frozen `rfl`, by construction. Statement "
            "byte-identical; no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-flip-query-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLIP_QUERY,
        "rationale": (
            "the SOUNDNESS control on the QUERY axis, added by a fifth audit "
            "[A5-1] because the other three positives all reshape the SLASH "
            "decision (or are the frozen impl with the `Id.run do` wrapper "
            "inlined), leaving the clause this specification exists to pin "
            "untested in the soundness direction. The emptiness guard "
            "`if queryString = \"\" then \"\" else \"?\" ++ enc queryString` is "
            "rewritten with the OPPOSITE polarity, `if queryString ≠ \"\" then "
            "\"?\" ++ enc queryString else \"\"`, which selects the same branch "
            "on every input; only the guard FORM changes, and it is exactly the "
            "shape a faithful patch takes if it tests for a query string being "
            "PRESENT rather than absent. Five of the ten rivals attack this "
            "clause, so without this case the battery could not distinguish "
            "'the spec pins the behavior' from 'the spec pins this spelling of "
            "the guard'. It carries a REAL obligation, measured: the frozen "
            "proof body on this impl FAILS, exit 1 (`Tactic \\`rfl\\` failed … "
            "`if (queryString ≠ \"\") = true then \"?\" ++ encodeQueryString "
            "queryString else \"\"` … not definitionally equal`), so the proof "
            "is honestly re-closed by a case split on `queryString = \"\"`. "
            "Statement byte-identical; no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (query clause over-fit to the guard's polarity)."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-f2p-query-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The frozen obligation is an unconditional `∀ path queryString`, so "
            "there is no precondition binder to attack directly; on a TOTAL "
            "carrier the analogue of PRECOND-TOO-STRONG is the obligation being "
            "unsatisfiable or DEGENERATE at exactly an F2P-shaped input. This "
            "case tests that directly, in-region and ahead of the frozen "
            "obligation: it discharges as two `have`s that at an F2P-shaped input "
            "(a request carrying a NON-EMPTY query string) the post-image is (a) "
            "exactly the query-preserving destination — the query branch RESOLVED "
            "by deciding `\"id=1\" ≠ \"\"`, so the `?`+encoded query is actually "
            "present rather than merely conditionally so — and (b) DISTINCT from "
            "the image at the same path with NO query, i.e. non-degenerate in the "
            "query component, which is the component this specification exists to "
            "pin. Only then is the frozen obligation closed verbatim. Half (b) is "
            "what nothing else here states: the two soundness positives discharge "
            "the clause UNIVERSALLY, which is strictly weaker than its post-image "
            "at the interesting point being the value the behavior requires — a "
            "universally satisfiable clause can collapse at that one point "
            "unnoticed. Proven on the transparent combination (append + length), "
            "so it consumes no property of either opaque encoder. Load-bearing, "
            "measured: the same case with a FALSE claim about the same point (the "
            "destination written WITHOUT its `?` introducer) fails to build. "
            "Nothing is assumed — statement byte-identical, no new declaration, "
            "the ground facts are `have`s prepended to the frozen tactic body. If "
            "it FAILS => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "pd-drop-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_QUERY,
        "refinement": (
            "This is exactly the pre-patch skeleton: the target is built from the "
            "path plus a trailing slash, with the query string DROPPED. The whole "
            "point of the fix is to carry the query into the redirect; a faithful "
            "patch that drops it sends a request carrying `?id=1` to a target with "
            "no query, so the F2P assertion that the 301 target still carries "
            "`?id=1` fails => does NOT resolve. A verifying rival here is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition query clause (C): on a non-empty query "
            "the result must carry `?`++encoded query, so a result lacking it "
            "cannot equal the spec RHS. Attacks clause (C) / the `queryString = "
            "\"\"` false branch / the queryString binder. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _WIT_DROP_QUERY,
    },
    {
        "id": "pd-drop-qmark",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_QMARK,
        "refinement": (
            "Appending the encoded query WITHOUT the leading `?` introducer yields "
            "a target like `.../articleid=1` instead of `.../article?id=1`: the "
            "query is no longer a distinct component. A faithful patch doing this "
            "produces a redirect target the F2P assertion does not match => does "
            "NOT resolve — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition query clause (C), which pins the `?` "
            "introducer: the suffix on a non-empty query is `?`++encoded query, one "
            "character longer than the rival's. Attacks clause (C) / the `?` "
            "introducer / the queryString binder. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_DROP_QMARK,
    },
    {
        "id": "pd-drop-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_SLASH,
        "refinement": (
            "Never appending the trailing slash produces the wrong target for the "
            "F2P inputs (an admin path WITHOUT a trailing slash): the expected 301 "
            "target ends in `/` before the query. A faithful patch omitting the "
            "slash sends the browser to a path the resource does not canonically "
            "carry => the redirect assertion fails => does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition slash clause (B): on a path not ending "
            "in `/` the result must include the appended `/`, so a result lacking "
            "it cannot equal the spec RHS. Attacks clause (B) / the `path.endsWith "
            "\"/\"` = false branch / the path binder. Witness CONDITIONS on the "
            "carrier (`path.endsWith \"/\" = false`) since the encoder value is "
            "opaque. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_DROP_SLASH,
    },
    {
        "id": "pd-always-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALWAYS_SLASH,
        "refinement": (
            "Appending `/` UNCONDITIONALLY double-slashes a path that already ends "
            "in `/` (`.../article//?id=1`). A faithful patch doing this regresses "
            "the already-slashed sub-domain: the emitted target no longer matches "
            "the canonical URL, so redirect assertions on such paths fail => does "
            "NOT resolve / regresses."
        ),
        "rationale": (
            "REJECTED by the postcondition slash clause (B): on a path already "
            "ending in `/` the result must append the EMPTY string, so an appended "
            "`/` cannot equal the spec RHS. Attacks clause (B) / the `path.endsWith "
            "\"/\"` = true branch / the path binder (the OPPOSITE branch from "
            "pd-drop-slash). Witness CONDITIONS on `path.endsWith \"/\" = true`. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_ALWAYS_SLASH,
    },
    {
        "id": "pd-drop-first-query-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROP_FIRST_Q,
        "refinement": (
            "Encoding the query with its FIRST character dropped emits e.g. "
            "`.../article?d=1` instead of `.../article?id=1`: the query is carried "
            "but mangled. A faithful patch passing a truncated query to the encoder "
            "produces a target the F2P assertion (target still carries the ORIGINAL "
            "`?id=1`) does not match => does NOT resolve — verify-does-not-imply-"
            "resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition query clause (C), which pins the encoder "
            "ARGUMENT to the whole query string, not a truncation. Attacks clause "
            "(C) / the encoder argument / the queryString binder. Witness CONDITIONS "
            "on the carrier (route 3, on the encoder argument): "
            "`encodeQueryString (queryString.drop 1) ≠ encodeQueryString "
            "queryString` — the sub-domain where the truncation is observable. If "
            "it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_DROP_FIRST_Q,
    },
    {
        "id": "pd-raw-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RAW_PATH,
        "refinement": (
            "Using the RAW path instead of running it through the URI-path encoder "
            "emits an unescaped path component. A faithful patch that skips the "
            "encoder sends the browser to a target with reserved/unsafe characters "
            "left un-escaped; on any path the encoder changes, the emitted target "
            "differs from the canonical one and the redirect assertion fails => "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition path clause (A): the result's path "
            "component must be `escapePathComponent path`, not the raw path. "
            "Attacks clause (A) / the path binder / the previously-unattacked "
            "escaped-path piece. Witness CONDITIONS on the carrier (route 1, on the "
            "path encoder): `escapePathComponent path ≠ path` — the sub-domain "
            "where the encoder is non-trivial. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_RAW_PATH,
    },

    # ---- rivals added by the adversarial audit (also must be REJECTED) ----
    {
        "id": "pd-suffix-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SUFFIX_ORDER,
        "refinement": (
            "Assembling the pieces in the wrong order emits a target like "
            "`.../article?id=1/` — the slash lands INSIDE the query component "
            "instead of terminating the path. A faithful patch that concatenated "
            "the pieces in this order carries the query but sends the browser to "
            "a different URL than the canonical one, and the query value itself "
            "is corrupted by the appended slash, so the redirect-target "
            "assertion fails => does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's CONCATENATION ORDER: the RHS is "
            "escaped-path ++ slash-part ++ query-part in that order, so a result "
            "with the last two transposed cannot equal it. Attacks the assembly "
            "order — the one part of the construction that the six rivals above "
            "leave untouched (each of those alters or drops a PIECE, none "
            "reorders them). Witness CONDITIONS on `path.endsWith \"/\" = "
            "false` and needs no assumption about either encoder. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _WIT_SUFFIX_ORDER,
    },
    {
        "id": "pd-query-through-path-encoder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_QUERY_PATH_ENC,
        "refinement": (
            "Running the query string through the URI-PATH encoder instead of "
            "the URI-QUERY encoder escapes the wrong reserved set: the two "
            "encoders keep different characters safe, so a query like `id=1` "
            "comes back with its `=` (and `&`, `?`, `;`, `[`, `]`) "
            "percent-escaped. A faithful patch that reached for the path "
            "encoder here emits a target whose query is mangled rather than "
            "carried verbatim => the redirect assertion fails => does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition query clause (C), which pins WHICH "
            "encoder is applied to the query, not merely that some encoder is. "
            "Complements pd-drop-first-query-char (which attacks the encoder's "
            "ARGUMENT) and pd-drop-qmark (the introducer): this is the "
            "previously-unattacked encoder IDENTITY. Witness CONDITIONS on the "
            "carrier (route 3): `escapePathComponent queryString ≠ "
            "encodeQueryString queryString` — the sub-domain where the two "
            "encoders are distinguishable. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_QUERY_PATH_ENC,
    },
    {
        "id": "pd-path-encoder-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PATH_ENC_ARG,
        "refinement": (
            "Pre-composing the trailing slash onto the string handed to the "
            "URI-path encoder escapes a DIFFERENT string than the one the "
            "canonical target's path component is built from, and then still "
            "emits the separately-computed slash piece on top. On any path the "
            "encoder does not treat the two arguments alike, the emitted target's "
            "path component differs from the canonical one, so the browser is "
            "sent somewhere other than the canonical URL and the redirect-target "
            "assertion fails => does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition path clause (A), which pins the path "
            "component to `escapePathComponent path` — the encoder applied to the "
            "requested path ITSELF, not to some string derived from it. Attacks "
            "the path encoder's ARGUMENT, which is the one grounded piece no "
            "other rival isolates: pd-raw-path removes that encoder altogether "
            "and pd-drop-first-query-char attacks the QUERY encoder's argument, "
            "so clause (A)'s argument position was previously undefended. "
            "Witness CONDITIONS on the carrier (route 1): "
            "`escapePathComponent (path ++ \"/\") ≠ escapePathComponent path` — "
            "the sub-domain where the substituted argument is observable — and "
            "assumes nothing about the encoder beyond that disagreement. Measured: "
            "witness vs rival exit 0, vs the frozen solution exit 1 (`heq has "
            "type True`, i.e. `simp` PROVED the equation for the frozen impl), "
            "consistency probe exit 1, and the forgery dropping the `¬` fails on "
            "gold with `No goals to be solved` rather than the witness's own "
            "error, so gold's exit code tracks the CLAIM. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _WIT_PATH_ENC_ARG,
    },
    {
        "id": "pd-invert-query-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INVERT_QUERY,
        "refinement": (
            "Inverting the emptiness test appends the query suffix exactly when "
            "there is NO query string — emitting a target with a bare dangling "
            "`?` on every ordinary no-query request — and drops it whenever a "
            "query IS present. A faithful patch with the test inverted both "
            "fails the query-carrying case and regresses every plain redirect "
            "to a URL with a spurious `?` => does NOT resolve / regresses."
        ),
        "rationale": (
            "REJECTED by the postcondition query clause (C) on its `queryString "
            "= \"\"` TRUE branch: when no query string is present the spec "
            "appends the EMPTY string, so an appended `?`+encoding cannot equal "
            "the spec RHS. This is the only case that defends the empty-query "
            "branch — every other query rival (pd-drop-query, pd-drop-qmark, "
            "pd-drop-first-query-char, pd-query-through-path-encoder) diverges "
            "only on the FALSE branch, so the 'append nothing' clause was "
            "previously undemonstrated. Witness needs NO hypotheses: it refutes "
            "at the literal empty query. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_INVERT_QUERY,
    },
]


# No consumed @ContractOnly axioms: the two URI encoders are A-reference opaque
# leaves validated == the real callees by G-AX. The construction (trailing-slash
# decision, `?` introducer, query preservation) is modeled DEEPLY over the
# transparent String carrier, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
