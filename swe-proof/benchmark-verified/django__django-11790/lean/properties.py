"""properties.py — G-PBT falsification battery for django__django-11790 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for the admissibility positive, inside the ``-- proof-start`` / ``-- proof-end``
region — is changed, so ``markers.same_spec`` holds and the single
``theorem correct_authUsernameField`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This ports the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts ``configure_username_field(declared_max_length, widget_attrs)`` over a
mutable ``Dict[int,int]`` widget map with SEVEN separately-stated postcondition
clauses (C1..C7). This Lean bundle models the SAME single purely-functional core
— resolve the identifier field's length limit (declared-or-default 254) and
apply it to BOTH the field's effective max length AND the widget's ``maxlength``
attribute — over an immutable ``UField`` carrier (a ``Nat`` field length + an
association-list attribute map). The nagini widget dict is a referentially
transparent VALUE here: the modeled function returns a fresh ``UField`` rather
than mutating an argument in place.

DEFENDED SURFACE (one modeled behavior; two independent top-level clauses).
``problem_spec_authUsernameField configuredMax initAttrs result`` pins EXACTLY:

  * (C_len)   ``result.maxLength = usernameMaxLength configuredMax`` — the
    field-level effective limit is the resolved bound;
  * (C_attrs) ``result.attrs = setAttr initAttrs "maxlength"
    (usernameMaxLength configuredMax)`` — the widget attribute map is EXACTLY
    the input map with the ``maxlength`` key set to that SAME resolved bound.

C_attrs is a single strong whole-map equality, so it SUBSUMES several distinct
nagini clauses at once:
  - the maxlength key is present (nagini C2);
  - its value equals the resolved bound (nagini C3), which equals the field
    value C_len (nagini C4, the field==widget tie), since both sides read
    ``usernameMaxLength configuredMax``;
  - no other key is added or dropped (nagini C5, membership frame): ``setAttr``
    keeps every non-``maxlength`` binding and adds nothing else;
  - every pre-existing attribute keeps its exact value (nagini C6/C7, value
    frame): ``setAttr`` only rewrites the ``maxlength`` binding.
Pinning the map to the concrete ``setAttr`` update — rather than only its
``maxlength`` lookup — frames the whole result against the input, so no impl
that fails to perform the update, disturbs another attribute, or emits a
spurious key can satisfy the spec.

BEHAVIOURAL DISCRIMINATOR (the fix): the resolved bound must be written into the
widget ``maxlength`` attribute, not merely into the field length. The pre-fix
behavior set only the field length and never populated the widget attribute, so
the rendered input lost its ``maxlength`` — the ``drop-widget-write`` rival below
IS that pre-fix behavior.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``configuredMax``
(the optional configured bound — ``none`` / ``some 0`` map to the 254 fallback,
``some (n+1)`` to ``n+1``) and ``initAttrs`` (the initial widget attribute map).
Both are load-bearing and both are varied across the reject witnesses (see the
point-spread block at the bottom): ``configuredMax`` ranges over
``none, some 0, some 3, some 5, some 6, some 7, some 8, some 255`` — covering both
ways the bound is unset, several declared values below the fallback, and one above
it — and ``initAttrs`` over the empty map and a map carrying a pre-existing
non-``maxlength`` integer-valued attribute.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS as a permission class. The nagini
    sibling holds ``widget_attrs`` at FULL permission (it is mutated in place),
    so its MANDATORY insufficient-permission class is already inapplicable
    THERE; on this referentially transparent carrier there is no ``mut`` input,
    no aliasing, and no read-only heap cell — doubly vacuous. But nagini's
    VALUE-LEVEL analogue (a rival that disturbs a pre-existing attribute, caught
    by the value-preservation postcondition, not by a permission error) DOES
    port: it lands as ``clobber-preexisting-attr`` against C_attrs, stated over an
    INTEGER-VALUED pre-existing attribute so the disturbed binding is inside the
    declared type bijection for the modeled map. No permission substitute is
    fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``usernameMaxLength`` is a grounded total
    ``Option Nat → Nat`` (``none``/``some 0 → 254``; ``some (n+1) → n+1``) and
    C_attrs is a structural equation over the actual input map. There is no
    opaque answer key to echo — producing the resolved bound IS doing the work.
    In its place the battery carries honest positive controls that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the class this carrier rewards most,
    because the resolution splits the input into three regions (unset, at-or-below
    the fallback, above it) that a wrong impl can get right in any combination.
    Rivals correct on part of the domain but diverging where the fix bites:
    hardcoding the 254 fallback for both writes (correct on the ``none``/``some 0``
    branch, wrong on the declared-int branch); writing a constant fallback into the
    widget while the field is correct (field/widget de-tie); clamping the resolved
    bound DOWN to the fallback (correct everywhere at or below it, wrong only above
    — ``cap-at-fallback``); and performing the widget write only when the bound does
    NOT resolve to the fallback (correct on every declared-int point, wrong on the
    unset branch — ``skip-write-on-fallback``).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``exact ⟨rfl, rfl⟩`` is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that states the spec
predicate directly at one CONCRETE input, unfolds the impl (its ``Id.run do``
record updates reduce under ``simp only [Id.run]``) and closes by ``decide``
(all inputs are ground literals over ``Nat``/``String``, so the carrier
computes). Each witness binds NOTHING in its head — no hypotheses whose
consistency could be in question — and each was checked with two real ``lake env
lean`` builds to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
patch whose rendered ``<input>`` loses or misreports the ``maxlength`` HTML
attribute (or whose field cap diverges from the widget cap), so the F2P
assertions ``form.fields['username'].widget.attrs.get('maxlength') == 255/254``
(and ``form.fields['username'].max_length == 255/254``) would mismatch — so the
faithful patch would NOT resolve.

DIVERGENCE / NON-TERMINATION lane — genuinely VACUOUS here (not a spec hole).
``implementation_authUsernameField`` is a total Lean ``def``; a diverging
implementation cannot be written at all, so there is nothing to port and no
known-hole to record (cf. ``the corpus-wide termination-semantics finding``, which concerns velvet
under ``partial`` termination semantics — not this backend).

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the resolution is modeled deeply as ``usernameMaxLength``); the axiom
lane belongs to G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are
dropped.

INDEPENDENT AUDIT (see the AUDIT ADDITIONS / AUDIT NOTE comments below). Every
case was re-derived against the real verifier: all ten theorem statements diff
byte-identical to the frozen file, and each reject case's witness was rebuilt
twice by hand (holds of the rival, fails on gold) with the gold-side failure
confirmed to be the SEMANTIC form -- ``decide`` reporting that the negated spec
predicate is FALSE at the witness input, i.e. gold satisfies the spec there --
never a missing identifier, type error or timeout. Repairs made: the two cases
whose pre-existing widget attribute lay outside the declared integer-valued type
bijection now use an integer-valued attribute instead; two rivals were ADDED for
resolution sub-domains no ported witness reached (above the fallback, and the
falsy-zero unset point).

CARRIER PRECISION NOTE (not a rival; recorded so the next reader does not have to
re-derive it). ``setAttr`` is remove-then-append, so when the input map ALREADY
carries a ``maxlength`` binding the result moves that binding to the END of the
association list, whereas the real dict assignment overwrites a present key IN
PLACE and keeps its position. C_attrs is a whole-LIST equality, so it observes
that order. This is stricter than the modeled reality only on inputs that arrive
with a pre-existing ``maxlength``, which mapping.md records as unreachable on
every F2P path (the integer attribute map starts empty there -- that is precisely
what makes the pre-fix lookup absent), so it costs no F2P discrimination and is
not a rival. It is why no case in this battery states a witness at an input whose
map already binds ``maxlength``: on such an input the frozen spec is order-
sensitive in a way the real behavior is not.
"""
from pathlib import Path

INSTANCE = "django__django-11790"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every impl reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_I_UMAX = "  let umax := usernameMaxLength configuredMax"
_I_INIT = "  let mut field : UField := { maxLength := 0, attrs := initAttrs }"
_I_SETLEN = "  field := { field with maxLength := umax }"
_I_SETATTR = "  field := { field with attrs := setAttr field.attrs \"maxlength\" umax }"

# The frozen proof's intro line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro configuredMax initAttrs"


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one concrete ground input,
# unfolds spec + impl, reduces the `Id.run do` record updates, and closes by
# `decide` (all literals compute on this carrier).
# ---------------------------------------------------------------------------
def _w(cm, attrs):
    # `some N` must be parenthesized to parse as a single argument atom (Lean
    # application), and so the coverage tool reads it as ONE probed value rather
    # than two tokens. `none` is already atomic.
    if " " in cm:
        cm = f"({cm})"
    return (
        f"example : ¬ problem_spec_authUsernameField {cm} {attrs}\n"
        f"    (implementation_authUsernameField {cm} {attrs}) := by\n"
        "  unfold problem_spec_authUsernameField implementation_authUsernameField\n"
        "  simp only [Id.run]\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_authUsernameField` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-widget-first",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different CORRECT reshape: perform the widget-attribute
        # write FIRST (fold it into the initial record literal) and derive the
        # field length AFTERWARD, dropping the separate attrs-update step. Same
        # observable content, only executable order/data-flow changed (no loop,
        # no fold, no lemma). Definitionally the frozen result, so the frozen
        # proof (`simp only [Id.run]; exact ⟨rfl, rfl⟩`) still closes — no proof
        # authoring, no helper lemma, no assumption token. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_INIT,
             "  let mut field : UField := { maxLength := 0, "
             "attrs := setAttr initAttrs \"maxlength\" umax }"),
            (_I_SETATTR + "\n", ""),
        ),
        "rationale": "correct reshape that writes the widget maxlength attribute "
                     "first (in the initial record) and sets the field length "
                     "afterward; it computes the SAME UField on every input, so "
                     "C_len and C_attrs both still hold — else SPEC-TOO-STRONG. "
                     "The result is definitionally the frozen impl, so the frozen "
                     "proof closes; statement byte-identical, no new axiom/lemma. "
                     "Ports the nagini pos-control (there: dict write first, value "
                     "read back out of the map).",
    },
    {
        "id": "pos-single-literal",
        "kind": "soundness",
        "expect": "verify",
        # Second structural positive: collapse the whole procedure into a single
        # returned record literal (no `let mut`, no staged updates). Same values,
        # different control-flow shape; the frozen proof still closes because the
        # result is definitionally identical. (Verified: real build.)
        "module": _swaps(
            _BASE,
            (_I_INIT + "\n", ""),
            (_I_SETLEN + "\n", ""),
            (_I_SETATTR + "\n",
             "  return { maxLength := umax, "
             "attrs := setAttr initAttrs \"maxlength\" umax }\n"),
            ("  return field\n", ""),
        ),
        "rationale": "correct reshape that builds the result in one record literal "
                     "instead of staged mutable updates; identical values, "
                     "different control flow. Must verify, else SPEC-TOO-STRONG. "
                     "Definitionally the frozen result, so the frozen proof closes "
                     "(statement byte-identical, no new axiom/lemma).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition
    # binder, so the nagini precondition-admission self-call re-expresses as:
    # discharge the spec predicate by evaluation at the CustomEmailField branch
    # (declared=255) over a widget map carrying a pre-existing non-maxlength
    # attribute, as a `have`, then close the frozen obligation verbatim. Nothing
    # is assumed: no new declaration, statement byte-identical, ground instance is
    # a `have` prepended to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT NOTE. The pre-existing attribute here is `size` (integer-valued),
        # not the boolean focus hint the port originally used: mapping.md scopes
        # the modeled attribute map to the INTEGER-VALUED projection and
        # explicitly excludes the boolean hint from the type bijection, so a
        # ground instance over `[("autofocus", 1)]` was outside the declared
        # carrier — it type-checks on `List (String × Nat)` but denotes no real
        # widget state. `size` is a genuine integer-valued widget attribute, so
        # the ground instance now names a point that actually exists in the
        # bijection. (Re-verified: real build, exit 0.)
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_authUsernameField (some 255) "
            "[(\"size\", 30)]\n"
            "      (implementation_authUsernameField (some 255) "
            "[(\"size\", 30)]) := by\n"
            "    unfold problem_spec_authUsernameField "
            "implementation_authUsernameField\n"
            "    simp only [Id.run]\n"
            "    exact ⟨rfl, rfl⟩\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the CustomEmailField F2P "
                     "branch (declared=255) over a widget map already carrying a "
                     "non-maxlength attribute, as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input "
                     "— the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, statement byte-identical, ground instance is "
                     "a `have` in the existing tactic body. Ports nagini's "
                     "admissibility self-call. The pre-existing attribute is an "
                     "integer-valued one (`size`), which is inside the declared "
                     "type bijection for the modeled attribute map.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the regression itself: drop the widget write entirely ----
    {
        "id": "drop-widget-write",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior (#27515 regression): configure only the field length,
        # never establish the widget maxlength attribute.
        "module": _swap(_BASE, _I_SETATTR + "\n", ""),
        "refinement": "omits the widget-attribute write entirely — this IS the "
                      "pre-fix behavior: only the field-level limit is set, the "
                      "rendered input's maxlength attribute is never populated. A "
                      "faithful real patch keeping the single field-only assignment "
                      "leaves widget.attrs.get('maxlength') == None, so BOTH F2P "
                      "tests (which assert it == 255 / 254) FAIL — this is exactly "
                      "the bug the patch fixes, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C_attrs: the spec pins result.attrs = "
                     "setAttr initAttrs \"maxlength\" (usernameMaxLength ...), which "
                     "always contains the maxlength binding, but the rival returns "
                     "attrs = initAttrs with no maxlength key. Refuted at "
                     "configuredMax=none, initAttrs=[] (the defaults-to-254 F2P "
                     "branch): the rival's empty attrs map lacks the maxlength "
                     "binding the spec requires.",
        "witness": _w("none", "[]"),
    },

    # ---- widget gets the constant fallback; field correct ----
    {
        "id": "widget-fallback-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns the correctly resolved field length but writes the constant 254
        # fallback into the widget regardless of the declared bound (field/widget
        # de-tie). Correct on the none/some-0 branch; diverges on declared-int.
        "module": _swap(
            _BASE, _I_SETATTR,
            "  field := { field with attrs := setAttr field.attrs "
            "\"maxlength\" 254 }"),
        "refinement": "writes the constant 254 fallback into the widget maxlength "
                      "attribute regardless of the declared bound, while the field "
                      "length is correct (field and widget no longer carry the same "
                      "value). Faithful real patch: widget.attrs['maxlength'] = 254 "
                      "(a literal) instead of the hoisted username_max_length. F2P "
                      "test_username_field_max_length_matches_user_model asserts "
                      "widget.attrs.get('maxlength') == 255 on the declared=255 "
                      "branch -> FAILS, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C_attrs (widget value / field==widget tie): the "
                     "spec pins the maxlength binding to usernameMaxLength "
                     "configuredMax, but the rival writes the constant 254. Refuted "
                     "at configuredMax=some 5, initAttrs=[]: 254 != 5 in the widget "
                     "binding.",
        "witness": _w("some 5", "[]"),
    },

    # ---- field length off by one; widget correct ----
    {
        "id": "field-offby1",
        "kind": "uniqueness",
        "expect": "reject",
        # Writes the correct resolved value into the widget but sets the field
        # length to resolved+1 (field and widget diverge).
        "module": _swap(
            _BASE, _I_SETLEN,
            "  field := { field with maxLength := umax + 1 }"),
        "refinement": "writes the correct resolved value into the widget but sets "
                      "the field-level length to resolved+1 (field and widget "
                      "diverge). Faithful real patch: self.fields['username']"
                      ".max_length = username_max_length + 1 with the widget write "
                      "correct -> the F2P assertion "
                      "form.fields['username'].max_length == 255 FAILS (server-side "
                      "cap one off from the rendered cap), so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C_len: the spec pins result.maxLength = "
                     "usernameMaxLength configuredMax, but the rival returns "
                     "resolved+1. Refuted at configuredMax=some 7, initAttrs=[]: "
                     "field length 8 != 7.",
        "witness": _w("some 7", "[]"),
    },

    # ---- wrong widget key ----
    {
        "id": "wrong-widget-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Writes the resolved value under a mistyped attribute name instead of the
        # HTML `maxlength` token; the dedicated attribute is never established.
        "module": _swap(
            _BASE, _I_SETATTR,
            "  field := { field with attrs := setAttr field.attrs "
            "\"max_length\" umax }"),
        "refinement": "writes the resolved value under a mistyped attribute name "
                      "(an underscore variant) instead of the HTML maxlength token "
                      "the browser honours -- the dedicated attribute is never set. "
                      "Faithful real patch: a typo'd key -> "
                      "widget.attrs.get('maxlength') is still None -> both F2P tests "
                      "FAIL, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C_attrs (membership): the spec pins the maxlength "
                     "binding, but the rival adds a differently-named key and leaves "
                     "maxlength absent, so result.attrs != setAttr initAttrs "
                     "\"maxlength\" .... Refuted at configuredMax=some 8, "
                     "initAttrs=[]: the produced map has a max_length binding and no "
                     "maxlength binding.",
        "witness": _w("some 8", "[]"),
    },

    # ---- clobber a pre-existing widget attribute (value-preservation frame) ----
    {
        "id": "clobber-preexisting-attr",
        "kind": "uniqueness",
        "expect": "reject",
        # Performs the correct maxlength write but ALSO overwrites a pre-existing
        # non-maxlength attribute. This is nagini's VALUE-LEVEL frame-mutation
        # analogue: allowed by any permission system, rejected by the
        # value-preservation half of C_attrs.
        #
        # AUDIT NOTE. The disturbed attribute is `size` (integer-valued), not the
        # boolean focus hint the port originally used. mapping.md scopes the
        # modeled attribute map to the INTEGER-VALUED projection and explicitly
        # excludes the boolean hint from the type bijection, so the old rival
        # disturbed a binding that denotes no real widget state: the rejection was
        # sound on the carrier but the refinement argument behind it (a real patch
        # resetting a boolean hint) had no counterpart in the modeled map. `size`
        # is a genuine integer-valued widget attribute, so the frame violation now
        # sits at a point the bijection actually covers. (Re-verified: real builds,
        # rival witness exit 0 / gold witness exit 1 semantically.)
        "module": _swap(
            _BASE, _I_SETATTR + "\n",
            _I_SETATTR + "\n"
            "  field := { field with attrs := setAttr field.attrs "
            "\"size\" (umax + 1) }\n"),
        "refinement": "performs the correct maxlength write but ALSO overwrites a "
                      "pre-existing non-maxlength widget attribute (an "
                      "integer-valued sizing hint already configured on the input). "
                      "Faithful real patch: a config block that rewrites another "
                      "integer-valued widget attribute while adding maxlength -> "
                      "the rendered input's other attributes change, so the "
                      "PASS_TO_PASS assertions over the widget's rendered "
                      "attributes regress and the faithful patch would NOT resolve.",
        "rationale": "REJECT from C_attrs (value frame): the spec pins result.attrs "
                     "= setAttr initAttrs \"maxlength\" ..., which changes ONLY the "
                     "maxlength binding and preserves every other attribute; the "
                     "rival additionally rewrites the pre-existing attribute's "
                     "value. Refuted at configuredMax=some 5, "
                     "initAttrs=[(\"size\", 30)]: the rival emits size=6 where the "
                     "spec preserves size=30. This is nagini's value-level "
                     "frame-mutation analogue (no permission class exists on this "
                     "carrier -- see module docstring).",
        "witness": _w("some 5", "[(\"size\", 30)]"),
    },

    # ---- spurious extra widget attribute ----
    {
        "id": "spurious-extra-attr",
        "kind": "uniqueness",
        "expect": "reject",
        # Performs the correct maxlength write AND the correct field length, but
        # ALSO writes a spurious additional widget attribute.
        "module": _swap(
            _BASE, _I_SETATTR + "\n",
            _I_SETATTR + "\n"
            "  field := { field with attrs := setAttr field.attrs "
            "\"spurious\" umax }\n"),
        "refinement": "performs the correct maxlength write and the correct field "
                      "length but ALSO establishes an additional widget attribute "
                      "that was not configured before. Faithful real patch: a second "
                      "widget.attrs[...] = username_max_length assignment under some "
                      "other attribute name. The rendered <input> then carries an "
                      "attribute the form never declared, so the PASS_TO_PASS "
                      "assertions over the username widget's rendered attributes see "
                      "a shape they do not expect and regress -- the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C_attrs (membership frame): the spec pins "
                     "result.attrs = setAttr initAttrs \"maxlength\" ..., which adds "
                     "no key other than maxlength, but the rival adds a fresh "
                     "spurious binding that was absent before. Refuted at "
                     "configuredMax=some 6, initAttrs=[]: the produced map carries "
                     "an extra spurious key the spec's map does not.",
        "witness": _w("some 6", "[]"),
    },

    # ---- hardcode the fallback for BOTH writes (partial-domain) ----
    {
        "id": "hardcode-fallback-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the configured bound and uses the constant 254 for BOTH the field
        # and the widget. Correct on the none/some-0 branch; diverges on the
        # declared-int branch.
        "module": _swap(_BASE, _I_UMAX, "  let umax := 254"),
        "refinement": "ignores the configured bound and uses the constant 254 for "
                      "BOTH the field and the widget. Correct on the none/some-0 "
                      "branch (IntegerUsernameUser, F2P defaults-to-254); DIVERGES "
                      "on the declared-int branch. Faithful real patch: the "
                      "resolution collapsed to the literal 254 (dropping the `or`'s "
                      "left operand) -> F2P "
                      "test_username_field_max_length_matches_user_model "
                      "(declared=255) asserts both == 255 -> FAILS, so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from C_len AND C_attrs: on a declared-int input the "
                     "spec resolves to that int for both the field and the widget "
                     "binding, but the rival emits 254 for both. Refuted at "
                     "configuredMax=some 3, initAttrs=[]: 254 != 3 in both clauses "
                     "(partial-domain rival — passes none, fails the int branch).",
        "witness": _w("some 3", "[]"),
    },

    # ---- NEAR-MISS: cap the resolved bound at the fallback (AUDIT ADDITION) ----
    # Added by the audit. Every pre-existing rival that gets the VALUE wrong is
    # wrong on a wide sub-domain (a constant 254, or resolved+1 everywhere). This
    # one agrees with the spec on the whole fallback branch AND on every configured
    # bound at or below the fallback, diverging only ABOVE it -- i.e. at exactly
    # the value the F2P assertions name. Nothing in the ported battery probed a
    # configured bound greater than the fallback at all (the port's declared points
    # were 3, 5, 6, 7, 8 -- all below 254), so the "resolution is used verbatim,
    # never clamped" reading of C_len/C_attrs was untested above the fallback.
    {
        "id": "cap-at-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swaps(
            _BASE,
            (_I_SETLEN, "  field := { field with maxLength := min umax 254 }"),
            (_I_SETATTR,
             "  field := { field with attrs := setAttr field.attrs "
             "\"maxlength\" (min umax 254) }"),
        ),
        "refinement": "treats the fallback as a CEILING rather than a default: the "
                      "resolved bound is clamped down to 254 for both the field and "
                      "the widget, so a configured bound above the fallback is "
                      "silently lowered. Faithful real patch: the resolution wrapped "
                      "in a min against the literal 254 instead of being used "
                      "verbatim. On the declared=255 branch F2P "
                      "test_username_field_max_length_matches_user_model asserts BOTH "
                      "form.fields['username'].max_length == 255 and "
                      "widget.attrs.get('maxlength') == 255; both see 254 -> FAILS, "
                      "so the faithful patch would NOT resolve. It PASSES the "
                      "defaults-to-254 F2P test, which is what makes it a near-miss "
                      "rather than a broad wrong impl.",
        "rationale": "REJECT from C_len AND C_attrs: the spec pins both writes to "
                     "usernameMaxLength configuredMax itself, with no clamp, but the "
                     "rival emits min(resolved, 254). Refuted at "
                     "configuredMax=some 255, initAttrs=[]: 254 != 255 in both "
                     "clauses. Agrees with the spec on the entire fallback branch and "
                     "on every configured bound <= 254, so it isolates the "
                     "used-verbatim reading of the resolution ABOVE the fallback -- "
                     "the sub-domain the ported witnesses never reached.",
        "witness": _w("some 255", "[]"),
    },

    # ---- BRANCH-CONDITIONAL widget write (AUDIT ADDITION) ----
    # Added by the audit. Performs the field write correctly and the widget write
    # with the correct VALUE, but skips the widget write entirely when the bound
    # resolves to the fallback. Distinct from drop-widget-write (which never writes
    # at all): this rival satisfies every other reject case's witness point, since
    # each of those probes the widget write on a DECLARED-int input where this one
    # behaves correctly. It also pins the falsy-zero point (`some 0`), which the
    # ported point spread never probed: nagini's resolve_limit collapsed only
    # `None`, so `some 0 -> 254` is a resolution clause this carrier ADDS and no
    # ported case exercised.
    {
        "id": "skip-write-on-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_SETATTR,
            "  field := { field with attrs := if umax = 254 then field.attrs else "
            "setAttr field.attrs \"maxlength\" umax }"),
        "refinement": "establishes the widget maxlength attribute only when the "
                      "resolved bound differs from the standard fallback, leaving the "
                      "rendered input with NO maxlength attribute whenever the bound "
                      "resolves to the fallback. Faithful real patch: the widget write "
                      "placed under a guard comparing the resolved bound to the "
                      "literal fallback. F2P "
                      "test_username_field_max_length_defaults_to_254 asserts "
                      "widget.attrs.get('maxlength') == 254 on exactly that branch -> "
                      "it is None -> FAILS, so the faithful patch would NOT resolve. "
                      "It PASSES the declared=255 F2P test, so the lost-attribute "
                      "behavior survives on one branch only.",
        "rationale": "REJECT from C_attrs: the spec pins result.attrs = "
                     "setAttr initAttrs \"maxlength\" (usernameMaxLength ...) "
                     "UNCONDITIONALLY, so the maxlength binding must be present on "
                     "every input, the fallback branch included; the rival returns "
                     "attrs = initAttrs there. Refuted at configuredMax=some 0, "
                     "initAttrs=[]: the rival's map lacks the maxlength binding the "
                     "spec requires. The witness point is the FALSY-ZERO fallback "
                     "input (a configured bound of zero is treated as unset) -- the "
                     "resolution branch no other case in this battery probes.",
        "witness": _w("some 0", "[]"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals W1..W7) plus an EMPTY AXIOM
# lane. This bundle models the SAME single purely-functional core and
# re-expresses every sibling case that has a counterpart on this carrier; it
# ADDS one positive control for cheapness/coverage.
#
#   sibling case                 -> here                        disposition
#   -----------------------------------------------------------------------
#   POS (dict write first)       -> pos-widget-first            PORTED (re-expressed)
#   (none)                       -> pos-single-literal          ADDED  (2nd positive)
#   ADMISS (self-call)           -> admiss-f2p-input            RE-EXPRESSED
#   W1 drop widget write         -> drop-widget-write           PORTED
#   W2 widget wrong value        -> widget-fallback-value       PORTED
#   W3 field off-by-one          -> field-offby1                PORTED
#   W4 wrong widget key          -> wrong-widget-key            PORTED
#   W5 clobber pre-existing attr -> clobber-preexisting-attr    PORTED (value frame)
#   W7 spurious extra attr       -> spurious-extra-attr         PORTED
#   W6 hardcode default both     -> hardcode-fallback-partial   PORTED
#   (none)                       -> cap-at-fallback             ADDED  (audit)
#   (none)                       -> skip-write-on-fallback      ADDED  (audit)
#   AXIOM_TESTS (0)              -> (none)                       DROPPED (G-AX)
#
# AUDIT ADDITIONS (two rivals, both re-run with real builds). The ported battery
# left two sub-domains of the resolution unattacked, in both cases because the
# nagini carrier had no corresponding point:
#   * ABOVE the fallback. Nagini's rivals were wrong on wide sub-domains, and the
#     port's declared witness points were 3, 5, 6, 7, 8 -- every one BELOW the
#     fallback of 254. So a rival that uses the resolution verbatim up to the
#     fallback and clamps above it satisfied every ported witness. cap-at-fallback
#     closes that, refuted at exactly the value the F2P assertions name.
#   * The FALSY-ZERO fallback point. Nagini's resolve_limit collapsed only `None`;
#     `some 0 -> 254` is a clause THIS carrier's usernameMaxLength adds, and no
#     ported witness stood on it (drop-widget-write uses `none`).
#     skip-write-on-fallback closes that, and is additionally the only rival whose
#     widget write is branch-conditional -- correct on every declared-int point,
#     so every other reject case's witness passes it.
#
# CLAUSE FOLDING. The nagini spec states SEVEN clauses C1..C7; this carrier's
# spec states TWO (C_len, C_attrs) because a fresh returned UField lets C_attrs
# be one strong whole-map equality (`result.attrs = setAttr initAttrs "maxlength"
# resolved`). That single equality subsumes nagini C2 (key present), C3 (widget
# value), C4 (field==widget, since both read usernameMaxLength), C5 (no key
# added/dropped), and C6/C7 (every other attribute's value preserved). Both
# top-level clauses are attacked: C_len by field-offby1, hardcode-fallback-partial
# and cap-at-fallback; C_attrs by drop-widget-write, widget-fallback-value,
# wrong-widget-key, clobber-preexisting-attr, spurious-extra-attr,
# hardcode-fallback-partial, cap-at-fallback and skip-write-on-fallback.
#
# RE-EXPRESSED (admiss-f2p-input): the sibling's self-call builds an in-domain
#   widget map satisfying three Requires clauses and invokes the function. The
#   frozen lean theorem has NO precondition binder to admit, so the honest
#   analogue discharges the POSTCONDITION at a normal F2P input (declared=255 over
#   a map already carrying a non-maxlength attribute) as a `have`, then closes the
#   frozen obligation verbatim.
#
# VACUOUS (frame / permission mutation as a PERMISSION class): the sibling holds
#   widget_attrs at FULL permission (mutated in place), so its insufficient-
#   permission class is already inapplicable there; this referentially
#   transparent carrier has no mut input, no aliasing, no read-only cell. But the
#   sibling's VALUE-LEVEL analogue (clobbering a pre-existing attribute) DOES port
#   -> clobber-preexisting-attr. No permission substitute is fabricated.
#
# VACUOUS (divergence / non-termination): implementation_authUsernameField is a
#   total Lean def; a diverging impl cannot be written. Genuinely vacuous on this
#   backend (NOT the velvet-partial known-hole of the corpus-wide termination-semantics finding).
#
# POINT SPREAD. The nine reject witnesses probe nine DISTINCT input tuples
# (pts=9):
#   (configuredMax, initAttrs) =
#     (none,     [])               drop-widget-write        C_attrs
#     (some 0,   [])               skip-write-on-fallback   C_attrs (falsy-zero)
#     (some 3,   [])               hardcode-fallback-partial C_len + C_attrs
#     (some 5,   [])               widget-fallback-value    C_attrs
#     (some 5, [("size",30)])      clobber-preexisting-attr C_attrs (value frame)
#     (some 6,   [])               spurious-extra-attr      C_attrs (membership)
#     (some 7,   [])               field-offby1             C_len
#     (some 8,   [])               wrong-widget-key         C_attrs
#     (some 255, [])               cap-at-fallback          C_len + C_attrs
#   configuredMax ∈ {none, some 0, some 3, some 5, some 6, some 7, some 8,
#   some 255} and initAttrs ∈ {empty, carrying a pre-existing integer-valued
#   attribute}, so neither binder is pinned. The variation is MEANINGFUL rather
#   than two spellings of one point: `none` and `some 0` are the two distinct
#   ways the bound is unset (the second reachable only on this carrier), the
#   several small declared values sit BELOW the fallback, and `some 255` sits
#   ABOVE it — the three resolution regions that a clamp, a collapse to the
#   literal, and a branch-conditional write each distinguish.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the resolution is modeled deeply), so there is nothing to probe and the
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
