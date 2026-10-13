"""properties.py — G-PBT falsification battery for django__django-14534 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_idForLabel`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the property over a ``ChoiceContext`` object under fractional-permission
heap grants and pins the result against a GROUNDED oracle: the value recorded in
the option's attribute mapping under the constant id-key token. This Lean bundle
models the SAME single purely-functional core — reporting the identifier that
lives under the ``"id"`` key of the option's attribute table — over a
``WidgetData`` structure whose ``attrs`` field is a distinct-key association
list, with the SAME grounding: the postcondition equates ``result`` to
``attrs.lookup "id"``, a fully-unfolded function of the input carrier, with no
opaque answer key to echo. Every nagini value/partial-domain case carries over
as an attack on one of the two sub-domains the single equation distinguishes
(id-present vs. id-absent); the nagini frame/permission-mutation class is VACUOUS
here (referential transparency — see ``assessment``).

DEFENDED SURFACE (one modeled behavior; one grounding equation, two sub-domains).
``problem_spec_idForLabel data result`` pins EXACTLY:

  * ``result = data.attrs.lookup "id"`` — the reported identifier is precisely
    the value the attribute table stores under the ``"id"`` key.

This one equation covers the three clauses the nagini sibling stated separately:

  * (present ⇒ not none)         when the table maps ``"id"`` to ``v``, the
    result is ``some v`` — not ``none``;
  * (present ⇒ the recorded id)  and it is that recorded ``v`` verbatim, honoring
    any caller-supplied identifier scheme — not a value synthesized from the
    option's ``name``/``index``;
  * (absent ⇒ none)              when the table has no ``"id"`` entry, the result
    is ``none`` — no identifier is fabricated from ``name``/``index``.

BINDER STRUCTURE. The spec predicate ``problem_spec_idForLabel`` has ONE input
binder, ``data`` (a ``WidgetData`` with fields ``attrs``, ``name``, ``index``).
The result is a function of ``data.attrs`` alone; ``data.name`` and
``data.index`` do NOT constrain the modeled result (they fed only the pre-fix
synthesis). The reject witnesses therefore vary the load-bearing sub-field
``attrs`` across both the id-present sub-domain (with DIFFERENT recorded values,
``"A"`` and ``"B"``, so a rival that echoed a fixed string is caught) and the
id-absent sub-domain (a non-``"id"`` key, and the empty table), and they also
vary ``name``/``index`` even though those are irrelevant to the modeled behavior
(so no rival that mishandled only ``name``/``index`` in the PRESENT direction
could hide). The four reject witnesses probe four DISTINCT inputs (``pts=4``);
see the point-spread block at the bottom.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's two frame rivals
    write into a read-only fractional-permission grant (``ctx.attrs[id_key()] =
    …`` needs full ``dict_pred``; ``ctx.name = …`` needs the full field), and are
    rejected for INSUFFICIENT PERMISSION. This carrier is referentially
    transparent: ``data`` is an immutable value, there is no ``mut`` input binder,
    no aliasing, and no read-only cell to overwrite — the mutation a rival would
    perform cannot be expressed. No substitute probe is fabricated (porting map:
    this class is vacuous on Lean).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result`` is
    pinned to ``data.attrs.lookup "id"``, a fully-unfolded function of the input
    carrier. There is no opaque answer key an implementation could echo — reading
    the value out of the option's own attribute table IS doing the work. In its
    place the battery carries an honest cheapest-implementation POSITIVE CONTROL
    and an ADMISSIBILITY positive that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: fabricate on the present sub-domain instead of
    reporting the recorded id (attacks the "recorded verbatim" reading);
    fabricate on the absent sub-domain instead of ``none`` (attacks the
    "absent ⇒ none" reading); always report ``none`` (drops every recorded id);
    and the verbatim pre-fix behavior (synthesize from ``name``/``index``
    unconditionally), which is wrong on BOTH sub-domains.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete ``WidgetData`` literal and refuting it by ``decide``. Each witness binds
NOTHING in its head (all inputs are ground literals with concrete
``attrs``/``name``/``index``), so there are no hypotheses whose consistency could
be in question. Each was checked with two real ``lake env lean`` builds to HOLD
of its rival (the rival provably contradicts the spec at that input) and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart —
reported abstractly, never as a diff line — would report the wrong label target
for one of the pinned form configurations, so a F2P test asserting the
element-carried identifier (or its absence) would mismatch and the faithful patch
would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed operation is modeled deeply as an association-list lookup);
the axiom lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-14534"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The frozen impl body: the single line inside `-- impl-start`/`-- impl-end`
# that returns the looked-up identifier. Every rival reshape lands entirely
# inside the impl region.
_I_BODY = '  return data.attrs.lookup "id"'
assert _BASE.count(_I_BODY) == 1, "impl body anchor drifted from expected gold"

# The frozen proof's intro line (inside `-- proof-start`/`-- proof-end`), unique
# in the file, so the admissibility positive can prepend a ground `have` without
# touching the theorem STATEMENT or the spec view.
_P_INTRO = "  intro data"
assert _BASE.count(_P_INTRO) == 1, "proof intro anchor drifted"

# The frozen proof's closing tactic (inside `-- proof-start`/`-- proof-end`),
# unique in the file. A positive that genuinely reshapes the impl into a form
# that is NOT definitionally the frozen body must re-close the obligation, so it
# swaps this line for the adapted tactic — the theorem STATEMENT and spec view
# stay byte-identical (only the proof-region tactic body changes).
_P_RFL = "  rfl"
assert _BASE.count(_P_RFL) == 1, "proof rfl anchor drifted"


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate directly at one concrete
# WidgetData literal and refutes it by `decide`. Elaborates against a rival
# (rival contradicts the spec there); fails on gold (gold satisfies it).
# ---------------------------------------------------------------------------
def _w(attrs, name, index):
    lit = ('{ attrs := ' + attrs + ', name := "' + name
           + '", index := "' + index + '" }')
    return (
        f"example : ¬ problem_spec_idForLabel\n"
        f"    {lit}\n"
        f"    (implementation_idForLabel {lit}) := by\n"
        "  unfold problem_spec_idForLabel implementation_idForLabel\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else SPEC-TOO-STRONG. Keeps the `correct_idForLabel`
    # statement byte-identical; re-proved with the frozen tactic body (the
    # reshaped impl is definitionally the frozen one, so `rfl` still closes).
    # =====================================================================
    {
        "id": "pos-match-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the single-branch lookup into an explicit case-split that
        # RECONSTRUCTS the Option (`some v => some v | none => none`). This is
        # NOT definitionally the frozen body: the frozen proof (`unfold …; rfl`)
        # does NOT close it (verified — the `match … | some v => pure (some v)`
        # reduct is not defeq to the bare lookup), so the case genuinely
        # exercises SPEC-TOO-STRONG rather than passing on a defeq term that can
        # never be rejected. Re-proved inside the proof region with an adapted
        # `cases … <;> rfl`; theorem STATEMENT and spec view stay byte-identical.
        # (Verified: real build, exit 0.)
        "module": _swap(
            _swap(
                _BASE, _I_BODY,
                '  match data.attrs.lookup "id" with\n'
                "  | some v => return some v\n"
                "  | none => return none"),
            _P_RFL,
            '  cases data.attrs.lookup "id" <;> rfl'),
        "rationale": "correct reshape that case-splits the lookup and rebuilds "
                     "the Option (`some v => some v | none => none`); it computes "
                     "the SAME value on every input, so the grounding equation "
                     "still holds — else SPEC-TOO-STRONG. Crucially this is NOT "
                     "definitionally the frozen body (the frozen `rfl` fails on "
                     "it — verified), so unlike a defeq let-binding it actually "
                     "probes spec strength: it is re-closed with an adapted "
                     "`cases … <;> rfl` inside the proof region, statement "
                     "byte-identical, no new axiom/lemma. Ports the nagini "
                     "pos-control-reorder-early-return positive (there: "
                     "branch-reorder + local-binding; here the single-branch "
                     "lookup admits the case-reconstruction reshape).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so
    # the nagini read-only-grant self-call re-expresses as: discharge the spec
    # predicate by evaluation at a concrete id-present option (the smallest
    # F2P-shaped input) as a `have`, then close the frozen obligation verbatim.
    # Nothing is assumed: no new declaration, statement byte-identical, ground
    # instance is a `have` prepended to the existing tactic body. (Verified.)
    # =====================================================================
    {
        "id": "admiss-ground-present",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_idForLabel '
            '{ attrs := [("id", "A")], name := "n", index := "0" }\n'
            '      (implementation_idForLabel '
            '{ attrs := [("id", "A")], name := "n", index := "0" }) := by\n'
            "    unfold problem_spec_idForLabel implementation_idForLabel\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the smallest F2P-shaped "
                     "input (an option whose attribute table records an id) by "
                     "evaluation as a `have`, then the frozen obligation is closed "
                     "verbatim. Verifies (else the modeled behavior would be "
                     "unsatisfiable at exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, ground instance is a `have` in the "
                     "existing tactic body. Ports nagini's admiss-read-only-grants.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning
    # the violation at one concrete input.
    # =====================================================================

    # ---- fabricate on the PRESENT sub-domain (attacks "recorded verbatim") ----
    {
        "id": "weak-present-fabricates",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the absent sub-domain (returns none), wrong on present:
        # when the table records an id, returns a value synthesized from the
        # option's `name` instead of the recorded id.
        "module": _swap(
            _BASE, _I_BODY,
            '  match data.attrs.lookup "id" with\n'
            "  | some _ => return some data.name\n"
            "  | none => return none"),
        "refinement": "ignores the recorded, scheme-honoring identifier and instead "
                      "synthesizes one from the option's symbolic name. On the "
                      "configuration where a caller supplies a custom identifier "
                      "scheme, the element is rendered with the scheme-derived id "
                      "while this reports the synthesized one, so the label target "
                      "no longer matches the element's id — the F2P test asserting "
                      "the scheme-derived identifier mismatches, so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from the grounding equation on the id-PRESENT "
                     "sub-domain: the spec pins `result = attrs.lookup \"id\"` = "
                     "`some \"A\"`, but the rival emits `some name` = `some \"n\"`; "
                     "these differ whenever the recorded id is not the name. "
                     "Refuted at attrs=[(\"id\",\"A\")], name=\"n\".",
        "witness": _w('[("id", "A")]', "n", "0"),
    },

    # ---- fabricate on the ABSENT sub-domain (attacks "absent ⇒ none") ----
    {
        "id": "weak-absence-fabricates",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on the present sub-domain, wrong on absent: when the table has
        # no id, fabricates a value from the option's name instead of reporting
        # none.
        "module": _swap(
            _BASE, _I_BODY,
            '  match data.attrs.lookup "id" with\n'
            "  | some v => return some v\n"
            "  | none => return some data.name"),
        "refinement": "on the configuration where no identifier is generated (the "
                      "attribute table records no id), the element carries no id at "
                      "all and the label target must be absent; this fabricates a "
                      "name-derived identifier instead. The F2P test asserting the "
                      "absent label target for that configuration mismatches, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from the grounding equation on the id-ABSENT "
                     "sub-domain: the spec pins `result = attrs.lookup \"id\"` = "
                     "`none` (no \"id\" key), but the rival emits `some name` = "
                     "`some \"n\"`. Refuted at attrs=[(\"class\",\"x\")] (no id "
                     "key), name=\"n\".",
        "witness": _w('[("class", "x")]', "n", "2"),
    },

    # ---- always report none (drops every recorded id) ----
    {
        "id": "support-always-none",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct ONLY on the absent sub-domain; when an id IS recorded it must
        # be reported, but this drops it to none.
        "module": _swap(
            _BASE, _I_BODY,
            "  return none"),
        "refinement": "reports no label target regardless of what the element "
                      "carries. On every configuration that DOES generate an id "
                      "(default and custom schemes alike), the element is rendered "
                      "with that id but this reports none, so the F2P test asserting "
                      "the generated identifier mismatches — the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from the grounding equation on the id-PRESENT "
                     "sub-domain: the spec pins `result = attrs.lookup \"id\"` = "
                     "`some \"B\"`, but the rival emits `none`. Refuted at "
                     "attrs=[(\"id\",\"B\")] (a DISTINCT recorded value from the "
                     "present-fabricates witness, so a rival echoing a fixed string "
                     "is not what is being tested), name=\"m\".",
        "witness": _w('[("id", "B")]', "m", "1"),
    },

    # ---- verbatim pre-fix behavior: synthesize from name/index unconditionally ----
    {
        "id": "support-prepatch-synthesis",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix body: always synthesize an identifier from the option's
        # name and index, ignoring the attribute table entirely. Wrong on BOTH
        # sub-domains.
        "module": _swap(
            _BASE, _I_BODY,
            '  return some ("id_" ++ data.name ++ "_" ++ data.index)'),
        "refinement": "the verbatim pre-fix behavior: synthesize the identifier "
                      "from the option's name and index using a fixed format, "
                      "ignoring the attribute table. On the custom-scheme "
                      "configuration it reports the synthesized id where the element "
                      "carries the scheme-derived one; on the no-id configuration it "
                      "reports a synthesized id where the element carries none. It "
                      "is exactly the buggy behavior both F2P tests were added to "
                      "catch, so the faithful patch (= no patch) does NOT resolve.",
        "rationale": "REJECT from the grounding equation on the id-ABSENT "
                     "sub-domain: the spec pins `result = attrs.lookup \"id\"` = "
                     "`none` (empty table), but the rival emits the synthesized "
                     "`some \"id_q_3\"`. Refuted at attrs=[] (empty), name=\"q\", "
                     "index=\"3\" — a point that also varies `index`, which the "
                     "pre-fix synthesis reads but the modeled result ignores.",
        "witness": _w("[]", "q", "3"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 frame-mutation rivals, 2 partial-domain rivals,
# 2 supporting near-miss rivals) plus a NON-EMPTY AXIOM lane (2 axiom probes).
# This bundle models the SAME single purely-functional core (report the value
# under the "id" key of the option's attribute table) and re-expresses every
# sibling case that has a counterpart on this carrier.
#
#   sibling case                        -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder-early-return    -> pos-match-reshape          RE-EXPRESSED
#   admiss-read-only-grants             -> admiss-ground-present      RE-EXPRESSED
#   frame-mutation-write-attrs          -> (none)                     VACUOUS
#   frame-mutation-write-name           -> (none)                     VACUOUS
#   partial-domain-present-fabricates   -> weak-present-fabricates    PORTED
#   partial-domain-absence-fabricates   -> weak-absence-fabricates    PORTED
#   support-always-none                 -> support-always-none        PORTED
#   support-prepatch-fabrication        -> support-prepatch-synthesis PORTED
#   AXIOM_TESTS (2)                     -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (pos-match-reshape): the sibling's positive combines a branch
#   reorder (handle absence first) with local-binding of the lookup. On this
#   carrier the modeled behavior is a SINGLE-branch lookup (no absence branch to
#   reorder — the association-list lookup returns `none` internally), so the
#   analogous structurally-different-but-correct reshape is an explicit
#   case-split that RECONSTRUCTS the Option (`some v => some v | none => none`).
#   This is deliberately NOT definitionally the frozen body — the frozen `rfl`
#   fails on it (verified) — so it genuinely probes SPEC-TOO-STRONG rather than
#   passing on a defeq term that could never be rejected; it is re-closed with
#   an adapted `cases … <;> rfl` in the proof region (verified with a real
#   build). (Audit note: an earlier port used a defeq `let`-binding here, which
#   is unrejectable and therefore tests nothing about spec strength; replaced.)
# RE-EXPRESSED (admiss-ground-present): the sibling asserts the four read-only
#   fractional-permission grants (Acc(ctx.attrs,1/2), …) hold for an F2P-shaped
#   input, then returns the gold result. This carrier has no permission system;
#   the honest analogue of "the precondition admits a normal input" is to
#   discharge the POSTCONDITION at the smallest F2P-shaped input (an id-present
#   option) as a `have`, proving the modeled behavior is satisfiable at a normal
#   input, then close the frozen obligation verbatim.
# VACUOUS (frame-mutation-write-attrs, frame-mutation-write-name): both sibling
#   frame rivals write into a read-only fractional-permission grant and are
#   rejected for INSUFFICIENT PERMISSION — a soundness dimension that exists only
#   under nagini's heap/permission model. This carrier is referentially
#   transparent: `data` is an immutable value, there is no `mut` input binder, no
#   aliasing, and no read-only cell to overwrite. The mutation cannot be
#   expressed, so the class is vacuous; no substitute probe is fabricated
#   (porting map: frame/permission class is vacuous on Lean).
# DROPPED (AXIOM_TESTS): the sibling's two axiom probes validate the A-reference
#   deep model (label_target_id == real BoundWidget.id_for_label == attrs.get('id'))
#   against the real Django callee. That is G-AX's lane, not G-PBT's; this bundle
#   declares no axiom (the lookup is modeled deeply), so there is nothing to probe
#   and the gate ignores AXIOM_TESTS regardless.
#
# COVERAGE. The spec has ONE top-level clause (the grounding equation
# `result = attrs.lookup "id"`) and ONE input binder (`data`, whose load-bearing
# sub-field is `attrs`). The equation is DEFENDED by pos-match-reshape and
# admiss-ground-present, and ATTACKED by all four reject rivals. The binder is
# exercised on BOTH sub-domains it distinguishes: id-present (weak-present-
# fabricates, support-always-none) with DIFFERENT recorded values ("A", "B") so a
# fixed-string echo is caught, and id-absent (weak-absence-fabricates,
# support-prepatch-synthesis) via a non-"id" key and the empty table. The
# irrelevant sub-fields `name`/`index` also vary across the witnesses, so no rival
# mishandling only those in the present direction could hide.
#
# POINT SPREAD. The four reject witnesses probe four DISTINCT inputs (pts=4):
#     attrs=[("id","A")]   name="n" index="0"   weak-present-fabricates    present
#     attrs=[("class","x")]name="n" index="2"   weak-absence-fabricates    absent
#     attrs=[("id","B")]   name="m" index="1"   support-always-none        present
#     attrs=[]             name="q" index="3"   support-prepatch-synthesis absent
#   Across them attrs ranges over id-present (two distinct values), a non-id key,
#   and the empty table; name ∈ {"n","m","q"}, index ∈ {"0","1","2","3"}, so no
#   binder or sub-field is pinned at a single value.
AXIOM_TESTS = []
