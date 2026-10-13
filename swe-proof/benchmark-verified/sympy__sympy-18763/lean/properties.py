"""properties.py — G-PBT falsification battery for sympy__sympy-18763 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the admissibility positive that re-proves,
inside the ``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the assembled markup as a LIST of code points and defends it with a
grounded ``assembled`` concatenation postcondition PLUS structural take/drop
clauses, under fractional-permission read-only contracts on the two rendered
fragments. This Lean bundle models the same behavior at the value level: a total
function ``renderRestriction(inner, lhs, rhs) : String`` whose one obligation
pins the whole assembled string to a single grounded concatenation of the fixed
literal fragments and the joined assignment subscript. The nagini rivals that
attack the assembled string carry over directly; the mapping of each nagini case
to its Lean counterpart (or its principled omission) is in the module
``assessment`` of the submit payload.

DEFENDED SURFACE (one modeled behavior). The obligation is a single grounded
equality:

    result = PRE ++ inner ++ MID ++ intercalate SEP (subsEntries lhs rhs) ++ SUF

where PRE = "\\left. \\left(", MID = "\\right) \\right|_{\\substack{ ",
SUF = " }}", SEP = "\\\\ ", and subsEntries pairs the two rendered lists as
``l=r`` truncating to the shorter list. It is one top-level string equality with
several independently-attackable segments:

  * the OPEN wrapper ``\\left(`` immediately before ``inner`` (the CHANGED
    fragment — pre-fix the body was dropped in bare, with no wrapping group);
  * the CLOSE wrapper ``\\right)`` immediately after ``inner`` (the matching half
    of the changed pair);
  * the body ``inner`` copied VERBATIM and in full between the wrappers;
  * the joined assignment subscript, built from BOTH ``lhs`` and ``rhs`` in that
    order with the ``l=r`` pairing.

The BEHAVIOURAL DISCRIMINATOR (the fix): wrap the already-rendered body in a
matched scaling-delimiter group before placing it as the restricted quantity, so
that a coefficient multiplying the whole restriction binds to the group rather
than merging with the body. The F2P scenario multiplies such a restriction by a
constant; pre-fix the body rendered bare (``\\left. - x + y \\right|...``) and
the coefficient visually merged with it, post-fix it renders as its own group
(``\\left. \\left(- x + y\\right) \\right|...``). The rivals below attack each
segment of the assembled equality.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and demonstrated so rather than
    asserted. Lean is referentially transparent: the rendered fragments are plain
    ``String`` / ``List String`` inputs carrying no heap permission, there is no
    read-only half-permission to overwrite and no aliasing to exploit. The two
    nagini rivals (write into a read-only input, then restore it, so that only
    the permission system and never the value abstraction can catch it) were
    transliterated as far as this carrier allows — rebind ``inner`` and ``lhs``
    to value-identical copies (``inner.set 0 (inner.get 0)``,
    ``lhs.set 0 (lhs.getD 0 "")``) before the frozen body — and BUILT. The result
    is the reason the lane cannot be ported, and it is not the reason one would
    guess: the file does not verify, but it fails with ``Tactic `rfl` failed ...
    is not definitionally equal``, i.e. an ordinary value-level tactic mismatch
    on a term that is observationally gold. So such a case would PASS as
    ``expect="reject"`` while attesting to nothing at all — the exact vacuous
    rejection the witness requirement exists to catch — and it admits no honest
    witness, since a witness must refute the spec at a concrete input and this
    rival satisfies the spec at every input. That last half was re-measured by
    audit rather than left as an argument: the SPEC PREDICATE was discharged by
    ``decide`` against this rival at EIGHT concrete points spanning this
    battery's reject inputs (the empty body, a one-char body, a two-char body,
    the ragged pair, the two-entry pair and the F2P-shaped input) and the file
    elaborates, exit 0 — the same eight points at which the frozen solution also
    satisfies it. A rival that satisfies the spec everywhere the battery can look
    is not refutable at a concrete input, so the lane has no honest case in it.
    Dropped as vacuous; no substitute is fabricated. (nagini cases 2, 2b.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result`` is
    pinned equal to a term built only from the inputs and fixed literals. There is
    no opaque answer key an implementation could echo, and no ``opaque`` callee on
    this carrier at all — the whole computation is transparent. In its place the
    battery carries honest positive controls (soundness + admissibility) that must
    verify.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean, and re-measured rather than
    asserted. The looser claim ("a diverging implementation cannot be written at
    all") is not quite true and was corrected by audit: one CAN write
    ``partial def implementation_renderRestriction ... := implementation_...``,
    and it passes the mechanical scope check. Three builds settle the class. (a)
    That rival does NOT verify — the frozen proof fails with ``Tactic `unfold`
    failed to unfold `implementation_renderRestriction```, because a ``partial``
    constant has no equations — so the spec is not weak here and nothing verifies
    vacuously. (b) It admits no honest witness either, in both directions: a
    ``decide`` witness fails on the RIVAL (the opaque constant does not reduce),
    which is ``witness-unproven``; and a hypothesis-conditioned witness
    (``example (h : implementation_... ≠ <spec RHS>) : ¬ problem_spec_... := h``)
    elaborates against the frozen solution TOO — exit 0 on both sides,
    i.e. ``witness-vacuous`` — because the goal is literally its own hypothesis.
    So the class is genuinely unshippable on this carrier: a ``partial`` impl is
    an opaque constant that is not provably different from the pinned value, so
    there is no concrete input at which the spec can be refuted of it. VACUOUS
    (not a known hole: nothing verifies). The nagini battery carries no
    divergence case either.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: dropping the wrapping group entirely (the
    pre-fix behavior); dropping it only on an empty body; truncating the copied
    body; corrupting the closing delimiter; and mis-ordering the assignment
    subscript sides.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen
concatenation's syntactic form — so a rejection alone attributes nothing to the
spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating the
spec predicate directly at one concrete input and refuting it. The carrier is
fully transparent (concrete string literals, no opaque term), so each witness
closes by plain ``decide`` after unfolding. Each was checked to HOLD of its rival
and to FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

BINDER / POINT SPREAD. The three spec binders are ``inner : String``,
``lhs : List String`` and ``rhs : List String``. The reject witnesses move all
three: ``inner`` takes a single-char body, a two-char body, an empty body, and
the F2P-shaped body; ``lhs``/``rhs`` take empty lists (where the subscript is
irrelevant to the attacked segment), a non-empty pair ``["x"]``/``["1"]``, a
TWO-entry pair ``["a","c"]``/``["b","d"]``, a THREE-entry pair, and a RAGGED
pair ``["x","y"]``/``["1"]``.

Two corrections landed here by audit, because the earlier text overclaimed:

  * the claim "the eight reject witnesses probe eight DISTINCT inputs, so no
    rival is refuted only at another's point" was FALSE as written.
    ``wrong-join-separator`` and ``reverse-entry-order`` both stated their
    refutation at the identical point ``inner="i"``, ``lhs=["a","c"]``,
    ``rhs=["b","d"]`` — seven distinct points across eight cases, not eight.
    Sharing a point is not by itself a defect (each witness still discriminates:
    each holds of its own rival and fails on gold), but the two clauses are
    genuinely separable and a shared point hides that. ``reverse-entry-order``
    now refutes at a THREE-entry point instead, where reversal and a wrong
    separator have visibly different effects. With the suffix rival added below,
    the NINE reject witnesses now probe nine distinct inputs (re-counted
    mechanically, not by eye), so the claim is true as stated.
  * ``drop-wrap-prepatch-bug`` — the pre-fix rival, the one case whose refinement
    argument is the F2P scenario itself — refuted at ``inner="X"``, a point the
    F2P never visits. It now refutes at the F2P-shaped body (``"- x + y"`` with
    the single assignment ``"x"``=``"1"``), so the case that claims the F2P
    demands the wrapped rendering demonstrates it AT that input rather than at a
    stand-in. Both builds were redone (rival 0, gold 1).

The multi-entry and ragged points are load-bearing rather than decorative, and
were added by audit after the first port shipped without them:

  * with 0 or 1 assignment the join separator ``subsSep`` is emitted ZERO times,
    so no single-entry witness can observe it — a rival that joins with ", "
    agrees with gold on every input the original battery used. Closed by
    ``wrong-join-separator`` at a two-entry point.
  * likewise the ORDER of the stacked entries is a different clause from the
    order of each entry's two sides, and is invisible below two entries. Closed
    by ``reverse-entry-order``; the side-order clause remains
    ``swap-subscript-sides``' job.
  * the pairing TRUNCATES to the shorter list, which is only observable when the
    two lists differ in length. Every case in the original battery used
    equal-length lists, so a rival that pads the shorter side instead was
    unattacked. Closed by ``pad-instead-of-truncate`` at a ragged point.
  * the TRAILING literal fragment (the closing ``" }}"`` of the stacked
    subscript) was pinned by no rival: every case attacked either the wrapper
    pair around the body or the subscript's contents, and a rival that simply
    omits the suffix agrees with gold nowhere but was never asked to. Found by
    audit as a NEW wrong impl (attack D) that the frozen spec correctly rejects;
    shipped as ``drop-trailing-fragment`` rather than left as an untested clause,
    since an unattacked segment is the place a spec hole would sit unnoticed.

POSITIVE CONTROLS, and what each one is worth. ``pos-control-local-reshape``
binds the literal fragments to ``let``s; that zeta-reduces to the frozen term,
so the frozen ``rfl`` closes it unchanged. It is an honest positive but a weak
one — a spec could be arbitrarily too strong and still admit it, because no
reasoning happens. ``pos-control-zipwith-reshape`` is therefore also carried: it
computes the entries with ``List.zipWith`` rather than ``zip``-then-``map``,
which is provably but NOT definitionally the same, so the frozen ``rfl`` fails on
it and the proof has to be genuinely redone. That is the case that actually
exercises the SPEC-TOO-STRONG direction on the pairing clause. Audit re-derived
the "frozen ``rfl`` fails on it" half rather than taking it on trust: the same
impl carrying the FROZEN tactic body verbatim fails with ``Tactic `rfl` failed:
The left-hand side ... is not definitionally equal to the right-hand side``, on
exactly the ``zipWith``/``zip`` mismatch, so the shipped proof is doing real work
and the positive is not a restatement of the first one.

Audit additionally probed the SPEC-TOO-STRONG direction with reshapes this
battery does NOT contain, and found no hole. Two are worth recording because
they are the ones that come closest to the pairing and assembly clauses:

  * REASSOCIATED assembly — the same five fragments appended with the grouping
    moved (``(PRE ++ inner) ++ ((MID ++ subs) ++ SUF)``). Correct, and provable:
    ``simp only [Id.run, Id.pure_eq, String.append_assoc]`` closes it. So the
    obligation pins the assembled STRING, not one bracketing of the appends.
  * SIDE-SWAPPED pairing — entries built from ``(rhs.zip lhs)`` with the
    projections read back in the opposite order, i.e. the same ``l=r`` entries
    computed through a transposed zip. Correct, and provable, though it needs a
    genuine induction: an inner ``have`` establishing
    ``zipWith (fun x y => y ++ "=" ++ x) b a = zipWith (fun x y => x ++ "=" ++ y) a b``
    by induction on the first list (both nil cases collapse, the cons/cons case
    closes by the IH), then ``simp only [Id.run, Id.pure_eq, List.zip,
    List.map_zipWith, Function.comp, key]``. Two shallower attempts at the same
    reshape (a bare ``List.zipWith_comm`` rewrite, and ``List.zip_swap`` +
    ``List.map_map``) do NOT close, so "the proof was hard" would have been the
    wrong reading — the reshape is admissible and the spec is not too strong on
    the pairing clause; it simply demands the commutation be proven.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` callee; the assignment pairing/join and the literal assembly are
modeled deeply (A-reference, validated by G-AX/G-CONF), not axiomatized. The
axiom lane belongs to G-AX; this gate ignores it, and the nagini AXIOM_TESTS are
dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-18763"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the admissibility
# positive that re-proves, the proof region) so same_spec stays byte-identical.

# The whole frozen imperative impl body (impl region).
_I_BODY = (
    '  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)\n'
    '  return "\\\\left. \\\\left(" ++ inner ++ "\\\\right) \\\\right|_{\\\\substack{ "\n'
    '    ++ latexSubs ++ " }}"'
)

# The frozen return statement of the impl (shared anchor for the assembly rivals;
# each _swap runs against the pristine _BASE, so uniqueness holds per case).
_I_RET = (
    '  return "\\\\left. \\\\left(" ++ inner ++ "\\\\right) \\\\right|_{\\\\substack{ "\n'
    '    ++ latexSubs ++ " }}"'
)

# The first line of the frozen proof body (proof region).
_P_HEAD = "  intro inner lhs rhs"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. The
    # theorem statement stays byte-identical; the reshape binds each fixed
    # literal fragment to a typed local before concatenation, which is
    # definitionally equal to the frozen inline form, so the frozen `rfl` still
    # closes (no helper lemma, no axiom, no assumption token introduced).
    #
    # Ports nagini case 1 (pos-control-local-reshape): the nagini positive bound
    # each constant code-point segment to a typed local before concatenation.
    # The analogous reshape here binds each fixed string fragment to a local.
    # =====================================================================
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _I_BODY,
            '  let pre := "\\\\left. \\\\left("\n'
            '  let mid := "\\\\right) \\\\right|_{\\\\substack{ "\n'
            '  let suf := " }}"\n'
            '  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs)\n'
            '  return pre ++ inner ++ mid ++ latexSubs ++ suf',
        ),
        "rationale": "the assembled equality is reshaped by binding each fixed "
                     "literal fragment (the open wrapper prefix, the mid segment, "
                     "the suffix) to a typed local before concatenation; the "
                     "returned string is identical on every (inner, lhs, rhs), so "
                     "`result = PRE ++ inner ++ MID ++ subscript ++ SUF` still "
                     "holds. Must verify, else the one modeled clause is "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body is retained "
                     "(the local-bound form is definitionally equal to the inline "
                     "form, `rfl` closes). Ports nagini's local-reshape positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so the `∀` is unguarded), so the nagini
    # precondition-admission probe has no binder to attack here; the honest
    # analogue is to discharge the spec predicate by evaluation at the ground
    # F2P input (body "- x + y", one assignment "x" = "1") alongside the frozen
    # obligation. Ports nagini case 6 (admissibility-f2p-shaped-input).
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_HEAD,
            '  have _ground : problem_spec_renderRestriction "- x + y" ["x"] ["1"]\n'
            '      (implementation_renderRestriction "- x + y" ["x"] ["1"]) := by\n'
            '    unfold problem_spec_renderRestriction implementation_renderRestriction\n'
            '    rfl\n'
            + _P_HEAD,
        ),
        "rationale": "the obligation is discharged at the F2P-shaped input (body "
                     "'- x + y', one assignment 'x'='1' — the "
                     "3*Subs(-x+y,(x,),(1,)) scenario the F2P exercises) by `rfl` "
                     "in a `have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "the theorem statement is byte-identical, and the ground "
                     "instance is a `have` inside the existing tactic body. Ports "
                     "nagini's F2P-shape admissibility probe. Audit confirmed the "
                     "ground `have` is LOAD-BEARING rather than decoration: the "
                     "same ground instance, stated as a standalone positive claim, "
                     "elaborates against the frozen solution (exit 0) and FAILS "
                     "against the pre-fix rival (exit 1), so this probe would catch "
                     "a spec that was unsatisfiable at exactly the F2P input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================

    # ---- the fix itself: body dropped in bare, no wrapping group (nagini 4) --
    {
        "id": "drop-wrap-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: place the body directly into the layout with no
        # matched wrapping group around it.
        "module": _swap(
            _BASE, _I_RET,
            '  return "\\\\left. " ++ inner ++ " \\\\right|_{\\\\substack{ "\n'
            '    ++ latexSubs ++ " }}"',
        ),
        "refinement": "this IS the pre-fix behavior: the already-rendered body is "
                      "dropped into the layout with no matched wrapping group. The "
                      "gold change exists precisely to add that group so a "
                      "coefficient multiplying the whole restriction does not merge "
                      "with the body. The F2P assertion demands the wrapped "
                      "rendering, so the faithful real patch — which is this very "
                      "pre-fix code — does NOT resolve.",
        "rationale": "REJECT from the assembled equality: the spec pins the open "
                     "wrapper immediately before `inner` and the close wrapper "
                     "immediately after it, while the rival emits neither, so "
                     "`result` differs. Binder spread: the F2P-shaped body "
                     "'- x + y' with the single assignment lhs=['x'] rhs=['1'] — "
                     "this case's refinement argument IS the F2P scenario, so it "
                     "is refuted at that input rather than at a stand-in point.",
        "witness": (
            "-- Refuted at the F2P-shaped input (body '- x + y', one assignment\n"
            "-- 'x'='1'): the spec demands the body wrapped as its own delimited\n"
            "-- group, the rival drops the wrapper. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "- x + y" ["x"] ["1"]\n'
            '    (implementation_renderRestriction "- x + y" ["x"] ["1"]) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- partial-domain: wrap present on non-empty body, dropped on empty ----
    {
        "id": "partial-empty-body-drops-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        # A rival correct on every non-empty body but dropping the wrapping group
        # when the body is empty.
        "module": _swap(
            _BASE, _I_RET,
            '  let wrapped := if inner.isEmpty then inner else "\\\\left(" ++ inner ++ "\\\\right)"\n'
            '  return "\\\\left. " ++ wrapped ++ " \\\\right|_{\\\\substack{ "\n'
            '    ++ latexSubs ++ " }}"',
        ),
        "refinement": "a faithful patch that wraps the body only when it is "
                      "non-empty and drops the group for an empty body produces the "
                      "wrong layout for an empty inner expression, diverging from "
                      "the gold UNCONDITIONAL wrapping. It is correct on the "
                      "non-empty F2P body but wrong on an empty-body restriction, so "
                      "it does not faithfully implement the always-wrap change.",
        "rationale": "REJECT from the assembled equality on the empty-body "
                     "sub-domain: the spec demands the open/close wrapper around "
                     "`inner` for ALL bodies including the empty string, while the "
                     "rival drops it when inner is empty. Distinct point (inner='') "
                     "from the other body rivals.",
        "witness": (
            "-- Refuted at an empty body: the spec still demands the wrapping\n"
            "-- group, the rival drops it. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "" [] []\n'
            '    (implementation_renderRestriction "" [] []) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- partial-domain: copy all but the last char of the body (nagini 3b) --
    {
        "id": "drop-last-body-char",
        "kind": "uniqueness",
        "expect": "reject",
        # Truncate the copied body by one character.
        "module": _swap(
            _BASE, _I_RET,
            '  return "\\\\left. \\\\left(" ++ inner.dropRight 1 ++ "\\\\right) \\\\right|_{\\\\substack{ "\n'
            '    ++ latexSubs ++ " }}"',
        ),
        "refinement": "copying all but the last character of the rendered body "
                      "produces truncated markup (e.g. '- x + ' instead of "
                      "'- x + y'); the F2P string-equality assertion fails. Such a "
                      "patch is not the gold verbatim-body behavior; it agrees with "
                      "gold only on an empty body — a partial-domain miss on every "
                      "non-empty body.",
        "rationale": "REJECT from the assembled equality: the spec copies `inner` "
                     "in full between the wrappers while the rival drops its last "
                     "character, so `result` differs whenever inner is non-empty. "
                     "Distinct point (inner='ab', a two-char body).",
        "witness": (
            "-- Refuted at body 'ab': the spec copies the full body, the rival\n"
            "-- yields 'a'. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "ab" [] []\n'
            '    (implementation_renderRestriction "ab" [] []) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- wrong closing-delimiter fragment (nagini 5, wrong-constant) ---------
    {
        "id": "wrong-close-delim",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the closing wrapper so the body's enclosing pair is unmatched
        # (an opening-shaped delimiter where the closing one belongs).
        "module": _swap(
            _BASE, _I_RET,
            '  return "\\\\left. \\\\left(" ++ inner ++ "\\\\right( \\\\right|_{\\\\substack{ "\n'
            '    ++ latexSubs ++ " }}"',
        ),
        "refinement": "emitting an opening-shaped closing delimiter instead of the "
                      "matching closing one produces an unmatched scaling delimiter "
                      "— invalid markup that renders wrong; the F2P string compare "
                      "fails. A supporting near-miss that still carries a real "
                      "refinement (the closing delimiter must match the opening "
                      "one).",
        "rationale": "REJECT from the assembled equality: the spec pins the exact "
                     "closing wrapper `\\right)` after `inner` while the rival emits "
                     "`\\right(`, so `result` differs. Distinct point (inner='X' "
                     "with empty assignment lists, isolating the closing-wrapper "
                     "segment).",
        "witness": (
            "-- Refuted at body 'X': the spec's closing wrapper is '\\right)',\n"
            "-- the rival emits '\\right('. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "X" [] []\n'
            '    (implementation_renderRestriction "X" [] []) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- assignment subscript sides swapped (attacks lhs/rhs binders) --------
    {
        "id": "swap-subscript-sides",
        "kind": "uniqueness",
        "expect": "reject",
        # Pair the assignment sides in the wrong order: build entries from
        # (rhs, lhs) instead of (lhs, rhs), so each entry reads `rhs=lhs`.
        "module": _swap(
            _BASE, _I_RET,
            '  let latexSubsSwapped := String.intercalate subsSep (subsEntries rhs lhs)\n'
            '  return "\\\\left. \\\\left(" ++ inner ++ "\\\\right) \\\\right|_{\\\\substack{ "\n'
            '    ++ latexSubsSwapped ++ " }}"',
        ),
        "refinement": "a faithful patch that paired the assignment sides in the "
                      "wrong order would render each entry as `value=variable` "
                      "instead of `variable=value` (e.g. '1=x' instead of 'x=1'), "
                      "so the subscript disagrees with gold for every assignment "
                      "with distinct sides. The F2P assertion demands 'x=1', so it "
                      "would NOT resolve. It agrees with gold only when lhs and rhs "
                      "coincide element-wise — a partial-domain miss on every "
                      "unequal assignment.",
        "rationale": "REJECT from the subscript segment of the assembled equality: "
                     "the spec builds the entries from (lhs, rhs) in that order "
                     "while the rival uses (rhs, lhs), so `result` differs whenever "
                     "a pair has distinct sides. This is the only rival that moves "
                     "the lhs/rhs binders off empty, demonstrating both are "
                     "load-bearing. Distinct point (inner='i', lhs=['x'], "
                     "rhs=['1']).",
        "witness": (
            "-- Refuted at one assignment 'x'='1': the spec's subscript entry is\n"
            "-- 'x=1', the rival's is '1=x'. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "i" ["x"] ["1"]\n'
            '    (implementation_renderRestriction "i" ["x"] ["1"]) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- wrong separator BETWEEN stacked entries (audit gap: every shipped
    # ---- witness used 0 or 1 assignment, where the join separator is never
    # ---- emitted at all, so `subsSep` was pinned by no case) ----------------
    {
        "id": "wrong-join-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Join the stacked entries with a comma instead of the markup line break.
        "module": _swap(
            _BASE, _I_BODY,
            '  let latexSubs := String.intercalate ", " (subsEntries lhs rhs)\n'
            + _I_RET,
        ),
        "refinement": "a faithful patch that separated the stacked assignment "
                      "entries with a comma instead of the markup line break "
                      "renders every multi-assignment restriction on one line "
                      "instead of stacked, disagreeing with gold's markup for "
                      "every input carrying two or more assignments. It agrees "
                      "with gold only when at most one entry is emitted (where no "
                      "separator appears), so it is a partial-domain miss on the "
                      "whole multi-assignment sub-domain.",
        "rationale": "REJECT from the join segment of the assembled equality: the "
                     "spec joins the entries with `subsSep` while the rival uses "
                     "', '. Requires TWO entries to observe — the separator is "
                     "emitted zero times for a 0- or 1-entry subscript, so the "
                     "other subscript rival cannot reach this segment. Distinct "
                     "point (lhs=['a','c'], rhs=['b','d']).",
        "witness": (
            "-- Refuted at two assignments 'a'='b' and 'c'='d': the spec joins\n"
            "-- them with the markup line break, the rival with ', '. This is the\n"
            "-- smallest input where a join separator is emitted at all.\n"
            'example : ¬ problem_spec_renderRestriction "i" ["a", "c"] ["b", "d"]\n'
            '    (implementation_renderRestriction "i" ["a", "c"] ["b", "d"]) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- entries emitted in reverse order (audit gap: the ORDER of the stacked
    # ---- entries is a separate clause from the order of each entry's two sides,
    # ---- and only the latter was attacked) ---------------------------------
    {
        "id": "reverse-entry-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the assignment entries bottom-to-top instead of in list order.
        "module": _swap(
            _BASE, _I_BODY,
            '  let latexSubs := String.intercalate subsSep (subsEntries lhs rhs).reverse\n'
            + _I_RET,
        ),
        "refinement": "a faithful patch that stacked the assignment entries in "
                      "reverse order would show the assignments bottom-to-top "
                      "relative to how they were supplied, so a restriction over "
                      "two or more assignments renders in the wrong order. It "
                      "agrees with gold only on 0- or 1-entry subscripts, a "
                      "partial-domain miss on every multi-assignment input. Note "
                      "this is a DIFFERENT clause from the `l=r` side ordering: "
                      "each entry here is built correctly, it is their sequence "
                      "that is wrong.",
        "rationale": "REJECT from the subscript segment: the spec emits the pairs "
                     "in the order `lhs.zip rhs` produces them, the rival reverses "
                     "the entry list. Observable only with two or more entries, so "
                     "the side-swap rival (which is refuted at a single entry) "
                     "cannot cover it. Distinct point (lhs=['a','c','e'], "
                     "rhs=['b','d','f'] — THREE entries). The two-entry point is "
                     "deliberately left to `wrong-join-separator`: audit found both "
                     "cases originally refuting at the SAME two-entry input, which "
                     "hides that these are separable clauses. At three entries the "
                     "reversal moves two entries while the number of emitted "
                     "separators is unchanged, so the clause being refuted here is "
                     "unambiguous.",
        "witness": (
            "-- Refuted at THREE assignments: the spec stacks 'a=b','c=d','e=f',\n"
            "-- the rival stacks them 'e=f','c=d','a=b'. Deliberately a distinct\n"
            "-- point from the join-separator case: at three entries the separator\n"
            "-- is emitted the same number of times either way, so this refutation\n"
            "-- can only be about the ENTRY ORDER. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "i" ["a", "c", "e"] ["b", "d", "f"]\n'
            '    (implementation_renderRestriction "i" ["a", "c", "e"]'
            ' ["b", "d", "f"]) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- pads the shorter side instead of truncating (audit gap: every shipped
    # ---- case used EQUAL-length lists, so the truncating-pair clause — the one
    # ---- place the two subscript binders interact — was unattested) --------
    {
        "id": "pad-instead-of-truncate",
        "kind": "uniqueness",
        "expect": "reject",
        # Pad the right-hand side out to the left-hand side's length with empty
        # renderings rather than truncating the pairing to the shorter list.
        "module": _swap(
            _BASE, _I_BODY,
            '  let padded := rhs ++ List.replicate (lhs.length - rhs.length) ""\n'
            '  let latexSubs := String.intercalate subsSep (subsEntries lhs padded)\n'
            + _I_RET,
        ),
        "refinement": "a faithful patch that padded the shorter rendering list out "
                      "with empty strings instead of letting the pairing truncate "
                      "would emit a spurious `lhs=` entry with an empty right side "
                      "for every unpaired left-hand rendering, where the modeled "
                      "behavior emits nothing at all. It agrees with gold exactly "
                      "when the two lists have equal length — which every other "
                      "case in this battery uses — so it is a partial-domain miss "
                      "on the whole ragged-input sub-domain.",
        "rationale": "REJECT from the pairing clause: the spec pairs via "
                     "`lhs.zip rhs`, which TRUNCATES to the shorter list, while the "
                     "rival pads the shorter side. This is the only case that moves "
                     "the two subscript binders to UNEQUAL lengths, so it is the "
                     "only one that can observe the truncation half of the pairing "
                     "clause. Distinct point (lhs=['x','y'], rhs=['1'] — ragged).",
        "witness": (
            "-- Refuted at a ragged pair: lhs has two renderings, rhs one. The\n"
            "-- spec truncates to the single entry 'x=1'; the rival additionally\n"
            "-- emits 'y='. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "i" ["x", "y"] ["1"]\n'
            '    (implementation_renderRestriction "i" ["x", "y"] ["1"]) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # ---- drops the trailing literal fragment (audit gap: every shipped rival
    # ---- attacked either the wrapper pair around the body or the subscript's
    # ---- CONTENTS; the closing fragment that terminates the stacked subscript
    # ---- was pinned by no case at all) --------------------------------------
    {
        "id": "drop-trailing-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the joined subscript but omit the fragment that closes it.
        "module": _swap(
            _BASE, _I_RET,
            '  return "\\\\left. \\\\left(" ++ inner ++ "\\\\right) \\\\right|_{\\\\substack{ "\n'
            '    ++ latexSubs',
        ),
        "refinement": "a faithful patch that omitted the trailing fragment would "
                      "leave the stacked subscript's grouping unterminated — the "
                      "surrounding braces never close, so the markup is malformed "
                      "for EVERY input rather than only on a sub-domain, and the "
                      "F2P string compare fails on the very first character it "
                      "reaches past the subscript. It is the one segment of the "
                      "assembled equality no other rival in this battery perturbs.",
        "rationale": "REJECT from the trailing segment of the assembled equality: "
                     "the spec pins the suffix after the joined subscript while the "
                     "rival ends the string at the subscript, so `result` differs at "
                     "every input. Distinct point (inner='z', lhs=['p'], rhs=['q'] — "
                     "an otherwise-correct assembly, so the refutation isolates the "
                     "suffix and nothing else).",
        "witness": (
            "-- Refuted at body 'z' with one assignment 'p'='q': the spec pins the\n"
            "-- fragment closing the stacked subscript, the rival stops short of\n"
            "-- it. Every other segment matches gold here, so the refutation is\n"
            "-- attributable to the suffix alone. Fully concrete, decidable.\n"
            'example : ¬ problem_spec_renderRestriction "z" ["p"] ["q"]\n'
            '    (implementation_renderRestriction "z" ["p"] ["q"]) := by\n'
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  decide\n"
        ),
    },

    # =====================================================================
    # SECOND POSITIVE CONTROL (soundness) — a correct reshape that is NOT
    # definitionally equal to the frozen impl. The shipped
    # `pos-control-local-reshape` above only binds the literal fragments to
    # `let`s, which zeta-reduces to the frozen term, so the frozen `rfl` closes
    # it and it exercises no reasoning: it cannot detect SPEC-TOO-STRONG. This
    # case builds the entries with `List.zipWith` instead of `zip`-then-`map`.
    # The two are provably equal but NOT definitionally so — the frozen `rfl`
    # does NOT close it (verified: it fails with `unsolved goals` on the
    # zipWith/zip mismatch) — so the proof must genuinely be redone. The
    # theorem STATEMENT stays byte-identical; only the tactic body changes,
    # which variant_scope permits for a positive that reproves.
    # =====================================================================
    {
        "id": "pos-control-zipwith-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _I_BODY,
                '  let latexSubs := String.intercalate subsSep\n'
                '    (lhs.zipWith (fun l r => l ++ "=" ++ r) rhs)\n'
                + _I_RET,
            ),
            "  unfold problem_spec_renderRestriction implementation_renderRestriction\n"
            "  rfl",
            "  unfold problem_spec_renderRestriction implementation_renderRestriction"
            " subsEntries\n"
            "  simp only [Id.run, Id.pure_eq, List.zip, List.map_zipWith,"
            " Function.comp]",
        ),
        "rationale": "a CORRECT reshape that is not definitionally equal to the "
                     "frozen impl: the assignment entries are built by a single "
                     "`zipWith` pass instead of pairing with `zip` and then mapping "
                     "the `l=r` formatter. The two agree on every (lhs, rhs) "
                     "including ragged ones (both truncate to the shorter list), so "
                     "the assembled string is unchanged and the obligation must "
                     "still hold. Unlike the local-binding positive this one does "
                     "NOT reduce to the frozen term, so the frozen `rfl` fails and "
                     "the proof is genuinely redone via `List.map_zipWith`. Must "
                     "verify, else the pairing clause is SPEC-TOO-STRONG: it would "
                     "be pinning one particular way of computing the pairs rather "
                     "than the pairs themselves.",
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# callee (the assignment pairing/join and the literal assembly are modeled
# deeply, an A-reference validated by G-AX/G-CONF, not a consumed contract). The
# nagini AXIOM_TESTS re-ran the deep-model-vs-real-callee obligation, which is
# G-AX's job here; dropped from this lane.
AXIOM_TESTS = []
