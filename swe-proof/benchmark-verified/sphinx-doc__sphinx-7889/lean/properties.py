# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7889 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   mockSubscript : List Char → PyKey → Except Unit (List Char)
#   A placeholder is indexed by a key. A key is either already text
#   (`PyKey.str s`, rendering to code points `s`) or non-text (`PyKey.other r`,
#   whose textual rendering has code points `r`). The single postcondition
#   `problem_spec_mockSubscript displayName key result` pins the WHOLE outcome:
#     result = Except.ok (displayName ++ '.' :: strChars key)
#   Three things are pinned with NO slack:
#     (C1) SUCCESS: the result is `Except.ok` for EVERY key — including a
#          non-text key. There is no error branch in the outcome; a rival that
#          leaves the operation failing for a non-text key fails C1. This is the
#          load-bearing clause the fix introduces.
#     (C2) SHAPE: the ok payload is exactly `displayName` ++ separator ++ the
#          key's textual rendering. Its three pieces are each pinned:
#            - the parent display name `displayName` (prefix, unchanged input),
#            - the single separator code point '.',
#            - the key's rendering `strChars key`.
#          A rival that drops or corrupts ANY piece fails C2.
#   strChars and the join are total, transparent functions over the input (no
#   opaque callee, no answer-key), so witnesses need no conditioning on the
#   carrier — `simp` reduces them at any literal input.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled the operation
# as `subscript_placeholder(key_is_text, key_text, module) -> List[int]`, with
# the fabricator's textual precondition (name_is_text) discharged by the fix and
# the display content pinned as `module ++ [46] ++ render_text(key_text)`. This
# backend models the SAME observable — the derived display name — but as
# `Except Unit (List Char)`, where the non-text key that raised in nagini's
# fabricator becomes the `Except.error ()` branch of `concatName`. So:
#   * nagini's W3 `raw-index-no-coercion` (hand the raw index to the string-only
#     fabricator, whose Requires(name_is_text) is undischarged for a non-text
#     index — the modeled TypeError, and the load-bearing discriminator of the
#     fix) ports onto clause C1 here: the raw key flows into `concatName`, whose
#     `.other` arm yields `Except.error ()` instead of the demanded `.ok`.
#     weak-blank-nontext-render then attacks the OTHER half of that sub-domain:
#     succeeding on a non-text key but rendering it blank, which the raw-key rival
#     (still failing there) can never reach.
#   * nagini's W4 `wrong-separator`, W5 `drop-separator`, W6 `omit-key-render`
#     (partial-domain value rivals) port onto clause C2's three pieces.
#   * a THIRD C2 piece the nagini value rivals did not isolate — the parent
#     `displayName` prefix — is attacked here too (weak-drop-module), varying the
#     `displayName` binder so no binder is held constant across all witnesses.
#   * the two DEGENERATE sub-domains the partial-domain rivals above name as the
#     places where they are accidentally CORRECT — the empty key rendering and the
#     empty parent — are pinned by their own rivals (weak-empty-key-errors,
#     weak-empty-parent-drops-separator). Without those, "correct only on the
#     degenerate case" is an unchecked claim about a point no witness visits, and
#     the empty `displayName` in particular is a binder value no other witness uses.
#
# ADMISSIBILITY — PORTED, not dropped. An earlier pass recorded this lane as N/A
# because the frozen obligation carries NO precondition hypothesis, so "nothing
# could be PRECOND-TOO-STRONG". That reason is wrong: on a TOTAL carrier the
# analogue of a too-strong precondition is the obligation being UNSATISFIABLE at
# exactly an F2P-shaped input — a spec that is vacuously unprovable there, or
# provable only by the ∀ never being instantiated at that point. A positive that
# discharges the spec predicate BY EVALUATION at that concrete input, as a `have`,
# before closing the frozen obligation verbatim, tests that directly, and it is
# landable here: `strChars`/`concatName` are transparent, so `simp` decides the
# ground instance. Shipped below as admiss-f2p-generic-index (measured: verifies,
# exit 0; and the control asserting the NEGATION of that same ground instance
# FAILS with `unsolved goals ⊢ False`, so the `have` is load-bearing rather than
# a decoration `simp` would close either way).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY W1 `frame-module-write` / W2
#     `frame-key-write`: `module` and `key_text` were Acc(list_pred,1/2) read-only
#     and the rival wrote back into them). Lean is referentially transparent — no
#     aliasing, no fractional permission — so a "store into a read-only input"
#     rival is not expressible and the whole lane is VACUOUS here. The read-only
#     discipline it protected is instead pinned structurally by clause C2: the
#     `displayName` prefix and the key rendering must appear UNCHANGED in the
#     result, which weak-drop-module / weak-omit-key / weak-blank-nontext-render
#     attack directly (each measured: rival exit 0, gold exit 1 with ⊢ False).
#   * DIVERGENCE / NON-TERMINATION. Nothing to ship here, but NOT because the
#     rival is unwritable: a `partial def implementation_mockSubscript ... :=
#     implementation_mockSubscript displayName key` IS expressible and clears the
#     variant scope check (measured: scope-ok). What it cannot do is VERIFY — a
#     `partial def` is opaque to `unfold`/`simp`, so the obligation is left as
#     `implementation_mockSubscript displayName key = Except.ok …` with no way to
#     reduce it, and the build fails (measured exit 1 with the frozen proof and
#     again with a `simp` reproof). This bundle sets NO
#     `loom.semantics.termination` option at all — it is a plain total-`def`
#     carrier, where a `partial` impl is REJECTED rather than admitted vacuously.
#     Under the total disposition such a rival would be shippable in the reject
#     lane, and it is NOT shipped for a measured reason rather than a disposition
#     one: a reject case on this backend must carry a witness that HOLDS of the
#     rival, and the witness cannot — re-measured, the refutation against the
#     `partial` rival fails at exit 1 with `Tactic 'unfold' failed to unfold
#     implementation_mockSubscript in ¬implementation_mockSubscript ['m'] …`,
#     because the same opacity that blocks the obligation blocks the witness. So
#     the case would land as `witness-unproven` (inconclusive => gate error), not
#     as a rejection attributable to the spec, and there is no rival to add. The
#     vacuous-verification spec hole in that class belongs to the velvet
#     `partial` bundles and is already recorded — see the corpus-wide termination-semantics finding;
#     it is deliberately NOT re-reported here.
#   * AXIOM_TESTS (nagini's ax-sound / ax-contain / ax-ref probes). The axiom lane
#     is G-AX's job; this gate ignores them. Both operations (`strChars`, the
#     join `concatName`) are modeled DEEPLY over transparent carriers, so there is
#     no consumed axiom here anyway.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7889"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  -- Render the key to its textual form before forming the derived display name,\n"
    "  -- so the display-name join always receives a textual component.\n"
    "  let name : PyKey := PyKey.str (strChars key)\n"
    "  return concatName displayName name"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Two of the
# positives keep it byte-identical — those restructurings reduce to the same normal
# form, so `rfl` still closes. The THIRD positive (pos-case-split) must REPROVE:
# its impl case-splits on the key, which is not definitionally the frozen shape, so
# the frozen script fails on it (measured: `Tactic 'unfold' failed to unfold
# concatName`) and the tactic body — and only the tactic body, the obligation
# STATEMENT stays byte-identical — is replaced.
_PROOF = (
    "  intro displayName key\n"
    "  unfold problem_spec_mockSubscript implementation_mockSubscript concatName\n"
    "  rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-let-bound-rendering: structurally-DIFFERENT but behaviourally identical. The
# key's rendering is bound to a local `rendered` before the textual key is built;
# the join and the result are otherwise unchanged, so the output equals the frozen
# impl's on every input. The frozen `theorem correct_mockSubscript` statement is kept
# byte-identical AND the frozen proof body still closes (the `let` binding is
# definitionally transparent). No reproof, no new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape).
_POS_LET = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  let rendered : List Char := strChars key\n"
    "  let name : PyKey := PyKey.str rendered\n"
    "  return concatName displayName name",
)

# pos-pure-expression: a structurally different CORRECT impl written as a pure
# expression (no `Id.run do` monad, no early `return`), directly returning the join
# of the textual key. Semantics identical on every input. The theorem STATEMENT is
# byte-identical and the FROZEN proof body still closes (the pure form reduces to the
# same normal form the monadic one does). No new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape).
_POS_PURE = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) :=\n"
    "  concatName displayName (PyKey.str (strChars key))",
)

# pos-case-split: a CORRECT impl whose shape is NOT definitionally the frozen one.
# It case-splits on the key and builds the derived display name in each arm, so it
# never calls the join at all; the frozen `unfold … concatName; rfl` script cannot
# close it (the goal has a `match` where the join used to be). Both other positives
# reduce to the frozen normal form, which means the frozen `rfl` still closes them
# and they never exercise the spec against a genuinely different TERM. This one
# does: the obligation STATEMENT is kept byte-identical and the tactic body is
# replaced by a case split + `simp`, which is exactly the reproof a variant is
# allowed. If it FAILS => SPEC-TOO-STRONG (the postcondition is provable only for
# terms definitionally equal to the frozen impl, i.e. it pins the SHAPE of the
# computation and not the behaviour).
_POS_CASES = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_mockSubscript\n"
        "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) :=\n"
        "  match key with\n"
        "  | .str s => Except.ok (displayName ++ '.' :: s)\n"
        "  | .other r => Except.ok (displayName ++ '.' :: r)",
    ),
    _PROOF,
    "  intro displayName key\n"
    "  cases key <;>\n"
    "    simp [problem_spec_mockSubscript, implementation_mockSubscript, strChars]",
)


# ===========================================================================
# ADMISSIBILITY (non-vacuity) — must VERIFY (else PRECOND-TOO-STRONG).
# ===========================================================================

# admiss-f2p-generic-index: the frozen obligation is universally quantified with no
# hypothesis, so the thing that could still be wrong is SATISFIABILITY at the input
# class the failing scenario actually exercises — a NON-TEXT key whose textual
# rendering is the parametrised-generic form (two code points, a tilde-style prefix
# plus a name character), against a non-empty parent. This positive discharges the
# spec predicate at exactly that ground input by EVALUATION, as a `have` prepended
# to the existing tactic body, and only then closes the frozen obligation verbatim.
# The theorem STATEMENT is byte-identical, the frozen proof body is retained
# unchanged after the `have`, and nothing is assumed (no new axiom/lemma/sorry, no
# new declaration). If it FAILS => the modeled behaviour is unsatisfiable at a
# normal F2P-shaped input, the total-carrier analogue of PRECOND-TOO-STRONG.
_ADMISS_GROUND = _swap(
    _BASE,
    _PROOF,
    "  have _ground : problem_spec_mockSubscript ['m','o','d'] (PyKey.other ['~','T'])\n"
    "      (implementation_mockSubscript ['m','o','d'] (PyKey.other ['~','T'])) := by\n"
    "    unfold problem_spec_mockSubscript implementation_mockSubscript\n"
    "    simp [concatName, Id.run, strChars, pure]\n"
    + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-raw-key (the pre-patch / load-bearing discriminator): hand the key to the join
# UNCHANGED, with no textual coercion. For a text key the join succeeds as before,
# but for a NON-TEXT key the join's non-text arm yields `Except.error ()` instead of
# the demanded `Except.ok`. This is the modeled image of the raise the fix removes.
_RIV_RAW = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  return concatName displayName key",
)

# weak-wrong-separator: builds the ok payload with separator code point '/' (47)
# instead of '.' (46). Correct success, correct prefix and key rendering, wrong ONLY
# on the one separator code point (partial-domain).
_RIV_SEP = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  return Except.ok (displayName ++ '/' :: strChars key)",
)

# weak-drop-separator: builds `displayName ++ strChars key` with NO separator. Off by
# one element vs the pinned shape; correct only on the degenerate case where the
# separator would be invisible (never, for a fixed literal join).
_RIV_DROPSEP = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  return Except.ok (displayName ++ strChars key)",
)

# weak-omit-key: returns `displayName ++ ['.']` and never appends the key's rendering.
# Correct on the degenerate empty-key sub-domain, WRONG on every non-empty key — every
# distinct key would collapse onto the same display name.
_RIV_OMITKEY = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  return Except.ok (displayName ++ ['.'])",
)

# weak-drop-module: returns `'.' :: strChars key` and DROPS the parent display name
# prefix. Correct on the degenerate empty-parent sub-domain, WRONG whenever the parent
# display name is non-empty. This attacks the `displayName` binder — the unchanged-
# input piece the nagini frame lane protected via permissions.
_RIV_DROPMOD = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  return Except.ok ('.' :: strChars key)",
)

# weak-blank-nontext-render: the NEAR-MISS on clause C1 the raw-key rival does not
# reach. weak-raw-key attacks only the ok-vs-error half — it leaves the operation
# FAILING for a non-text key. This rival SUCCEEDS for every key (so it satisfies C1's
# `Except.ok` half and the whole error branch is gone) but renders a non-text key as
# the EMPTY text, emitting `displayName ++ ['.']`. So it is byte-identical to gold on
# every text key and wrong only in the non-text key's rendering CONTENT — the piece
# `strChars key` contributes. Without it, "succeeds on a non-text key" and "renders
# that key faithfully" are attested by one rival that only ever tests the first.
_RIV_BLANKOTHER = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  match key with\n"
    "  | .str s => return Except.ok (displayName ++ '.' :: s)\n"
    "  | .other _ => return Except.ok (displayName ++ ['.'])",
)

# weak-empty-key-errors: agrees with gold EVERYWHERE except the degenerate EMPTY-key
# sub-domain, where it fails instead of yielding `displayName ++ ['.']`. weak-omit-key's
# rationale calls the empty key its "correct" sub-domain, so nothing in the battery
# ever CHECKED what the spec demands there; this pins it. The narrowest partial-domain
# rival in the battery: one input class, everything else byte-identical to gold.
_RIV_EMPTYKEY = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  if strChars key = [] then\n"
    "    return Except.error ()\n"
    "  else\n"
    "    return Except.ok (displayName ++ '.' :: strChars key)",
)

# weak-empty-parent-drops-separator: the dual near-miss, on the other degenerate
# sub-domain weak-drop-module's rationale names as its "correct" one — the EMPTY
# parent display name. There the rival drops the separator (`strChars key` alone,
# not `'.' :: strChars key`); everywhere else it is gold. So the separator is pinned
# even where the prefix it separates is absent, which no other rival establishes.
_RIV_EMPTYPARENT = _swap(
    _BASE,
    _IMPL,
    "def implementation_mockSubscript\n"
    "    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do\n"
    "  if displayName = [] then\n"
    "    return Except.ok (strChars key)\n"
    "  else\n"
    "    return Except.ok (displayName ++ '.' :: strChars key)",
)


def _wit(dn, key, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (displayName, key). `simp` reduces strChars/concatName/Id.run/pure and
    closes the disequality of the two literal `List Char`s (or the ok/error
    mismatch). Elaborates against a rival that diverges from the spec there, and
    FAILS on gold (which satisfies the spec at every input) — SEEN to discriminate
    both ways. `concatName` is fed to simp for the raw-key rival that calls it; it is
    a harmless unused-simp-arg for the value rivals that build the payload directly."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_mockSubscript {dn} {key}\n"
        f"    (implementation_mockSubscript {dn} {key}) := by\n"
        f"  unfold problem_spec_mockSubscript implementation_mockSubscript\n"
        f"  simp [concatName, Id.run, strChars, pure]"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-let-bound-rendering",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "structurally-different but CORRECT impl: the key's rendering is bound to a "
            "local `rendered` before the textual key is built, keeping the join and the "
            "result, so the output equals the frozen impl's on every input. The theorem "
            "statement is byte-identical and the FROZEN proof body still closes (the let "
            "binding is definitionally transparent) — a faithful restructure with no reproof "
            "and no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition "
            "over-fit to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-pure-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure expression (no "
            "`Id.run do`, no early return), directly returning the join of the textual key. "
            "Semantics identical on every input. The theorem STATEMENT is byte-identical and "
            "the FROZEN proof body still closes (the pure form reduces to the same normal "
            "form as the monadic one) — no new axiom/lemma/sorry. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape rather "
            "than the behaviour). NOTE: because the frozen `rfl` closes it, this positive "
            "and pos-let-bound-rendering are both DEFINITIONALLY EQUAL to the frozen impl "
            "— they show the spec is not over-fit to surface syntax, but not that it "
            "admits a genuinely different term. pos-case-split is the positive that does."
        ),
    },
    {
        "id": "pos-case-split",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CASES,
        "rationale": (
            "the positive that is NOT definitionally the frozen impl. It case-splits on "
            "the key and builds the derived display name directly in each arm, so the "
            "join never appears in the term and the frozen `unfold … concatName; rfl` "
            "script cannot close it — a REPROOF is required (case split + `simp`), which "
            "is what a variant is allowed to change. The obligation STATEMENT stays "
            "byte-identical and no axiom/lemma/sorry is introduced. This is the case that "
            "tests whether the postcondition pins BEHAVIOUR rather than the shape of the "
            "computation: the other two positives reduce to the frozen normal form, so "
            "they would verify even if the spec demanded that exact term. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility / non-vacuity (must VERIFY) ----
    {
        "id": "admiss-f2p-generic-index",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_GROUND,
        "rationale": (
            "NON-VACUITY at an F2P-shaped input. The frozen obligation is universally "
            "quantified with no hypothesis, so it cannot be PRECOND-TOO-STRONG in the "
            "literal sense — but the total-carrier analogue is the obligation being "
            "UNSATISFIABLE at exactly the input class the failing scenario exercises: a "
            "NON-TEXT key whose textual rendering is the parametrised-generic form "
            "(`PyKey.other ['~','T']`) against a non-empty parent. This case discharges "
            "the spec predicate at that ground input BY EVALUATION as a `have`, then "
            "closes the frozen obligation verbatim; the statement is byte-identical and "
            "nothing is assumed. The `have` is load-bearing, not decorative: the same "
            "file asserting the NEGATION of that ground instance fails with `unsolved "
            "goals ⊢ False`, so `simp` is deciding the concrete claim rather than "
            "closing anything handed to it. If it FAILS => the spec demands something "
            "unsatisfiable at a normal input of the very class the fix is about, which "
            "is the PRECOND-TOO-STRONG direction this lane exists to test. Ports "
            "nagini's admiss-tilde-T, whose F2P-shaped '~T' index rendering this is the "
            "direct analogue of (nagini asserted the Requires predicates held there; "
            "here, with no Requires, the obligation itself is discharged there)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-raw-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_RAW,
        "refinement": (
            "this IS the pre-change behaviour: the key flows into the display-name join "
            "UNCHANGED, with no textual coercion. For a non-text key (a type parameter used "
            "to index a generic) the join's text-only path raises — exactly the error the "
            "public issue reports when documenting a generically-typed class. A faithful "
            "patch of this shape leaves the generic-index case raising, so the failing test "
            "cannot construct its parametrized subclass; it does NOT resolve. A verifying "
            "rival here is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause C1 (SUCCESS). On a non-text key the spec demands "
            "`Except.ok (displayName ++ '.' :: strChars key)`, but the rival's join takes "
            "its non-text arm and returns `Except.error ()`. Witness probes the non-text "
            "sub-domain (`PyKey.other`), the discriminating input class. If it VERIFIES => "
            "SPEC-TOO-WEAK (the success-on-non-text-key clause is unpinned)."
        ),
        # non-text key `.other ['T']`: gold -> ok "mod.T"; rival -> error.
        "witness": _wit("['m','o','d']", "(PyKey.other ['T'])",
                        "non-text key (generic index): gold succeeds, raw-key rival errors"),
    },
    {
        "id": "weak-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SEP,
        "refinement": (
            "a faithful patch joining with '/' instead of '.' would give the derived "
            "placeholder a display name like `mod/T` instead of `mod.T` — the wrong dotted "
            "path in the field whose whole purpose is the display name. The spec pins the "
            "exact separator, so a display-name consumer reads the wrong value; the "
            "constructed class carries the wrong derived name. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (SHAPE, separator piece). The spec fixes the separator "
            "at code point '.', but the rival emits '/'. Witness varies a text key "
            "(`PyKey.str`) with a non-empty parent so the one differing code point is "
            "visible. If it VERIFIES => SPEC-TOO-WEAK (the separator is unpinned). "
            "(partial-domain: one wrong code point.)"
        ),
        # text key: gold -> "mod.x"; rival -> "mod/x".
        "witness": _wit("['m','o','d']", "(PyKey.str ['x'])",
                        "text key: gold uses '.', wrong-separator rival uses '/'"),
    },
    {
        "id": "weak-drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPSEP,
        "refinement": (
            "a faithful patch joining the parent name straight onto the key's rendering "
            "with no dot names the placeholder `modT` instead of `mod.T`, losing the "
            "dotted parent path the "
            "display-name field requires — every derived name loses its separator. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (SHAPE, separator piece — dual to wrong-separator). The "
            "PSeq-of-one '.' is mandatory; the rival's result is off by one element (prefix "
            "immediately followed by the rendering). Witness varies a multi-char text key "
            "with a distinct parent so the missing element is unambiguous. If it VERIFIES => "
            "SPEC-TOO-WEAK (the separator's presence is unpinned)."
        ),
        # gold -> "a.bc"; rival -> "abc".
        "witness": _wit("['a']", "(PyKey.str ['b','c'])",
                        "text key: gold inserts '.', drop-separator rival concatenates"),
    },
    {
        "id": "weak-omit-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OMITKEY,
        "refinement": (
            "a faithful patch fabricating `displayName + '.'` (dropping the rendered key) "
            "would name EVERY derived placeholder `mod.` regardless of the index; two "
            "distinct subscripts would collide on the same display name. The subscript "
            "tests build distinct subclasses and would observe an indistinguishable "
            "(wrong) display name. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (SHAPE, key-rendering piece). The `strChars key` tail is "
            "mandatory; dropping it leaves `displayName ++ ['.']`, which fails the pin for "
            "any non-empty key. Witness varies a non-empty text key so the missing tail is "
            "visible. If it VERIFIES => SPEC-TOO-WEAK (the key rendering is unpinned). "
            "(partial-domain: correct only on the degenerate empty key.)"
        ),
        # gold -> "m.q"; rival -> "m.".
        "witness": _wit("['m']", "(PyKey.str ['q'])",
                        "non-empty key: gold appends the rendering, omit-key rival stops at '.'"),
    },
    {
        "id": "weak-drop-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPMOD,
        "refinement": (
            "a faithful patch fabricating just the separator plus the key's rendering "
            "(dropping the parent display name) would name EVERY derived placeholder `.T`, "
            "`.U`, … with no parent path — the derived name would no longer be rooted at "
            "the placeholder it was indexed from, so the chained subscript/attribute-access "
            "tests would observe the wrong display name. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (SHAPE, parent-prefix piece). The `displayName` prefix is "
            "an UNCHANGED input that must appear verbatim in the result — the referential-"
            "transparency analogue of the nagini frame obligation on the read-only `module`. "
            "The rival drops it. Witness varies the `displayName` BINDER at a non-empty "
            "parent so no binder is held constant across all reject witnesses. If it "
            "VERIFIES => SPEC-TOO-WEAK (the parent prefix is unpinned)."
        ),
        # non-empty parent, non-text key: gold -> "pkg.U"; rival -> ".U".
        "witness": _wit("['p','k','g']", "(PyKey.other ['U'])",
                        "non-empty parent: gold keeps the prefix, drop-module rival drops it"),
    },
    {
        "id": "weak-blank-nontext-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_BLANKOTHER,
        "refinement": (
            "a faithful patch of this shape would make the non-text index case stop "
            "raising — so it looks fixed — while naming the derived placeholder `mod.` "
            "with the index rendering blank. Every distinct non-text index would collide "
            "on that one display name, and the derived name would no longer record WHICH "
            "index produced it. Text-key subscripts are untouched, so the pre-existing "
            "textual behaviour still passes; only the generic-index display name is wrong. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (SHAPE, key-rendering piece) on the sub-domain clause "
            "C1 is about. This is the NEAR-MISS weak-raw-key cannot reach: weak-raw-key "
            "leaves the operation FAILING for a non-text key, so it only ever tests the "
            "ok-vs-error half. This rival succeeds for EVERY key — the error branch is "
            "gone entirely — and is byte-identical to gold on every text key, diverging "
            "only in what a non-text key RENDERS to. Witness probes a non-text key with a "
            "non-empty rendering, where the spec demands the rendering appear. If it "
            "VERIFIES => SPEC-TOO-WEAK (success on a non-text key is pinned but the "
            "faithfulness of its rendering is not)."
        ),
        # non-text key: gold -> "m.U"; rival -> "m.".
        "witness": _wit("['m']", "(PyKey.other ['U'])",
                        "non-text key: gold appends its rendering, blank-render rival stops at '.'"),
    },
    {
        "id": "weak-empty-key-errors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTYKEY,
        "refinement": (
            "a faithful patch that special-cased a key whose rendering is empty (guarding "
            "the join instead of feeding it) would leave that one index class raising, so "
            "subscripting with it still fails to build a placeholder while every other "
            "index works. The spec demands the operation succeed for EVERY key, so this "
            "reintroduces the same class of failure on a narrower domain. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (SUCCESS) on the degenerate EMPTY-key sub-domain. "
            "weak-omit-key's rationale names the empty key as the sub-domain where it is "
            "CORRECT, which means no case in the battery checked what the spec demands "
            "there; this rival pins it. It agrees with gold on every other input, so it is "
            "the narrowest partial-domain rival here: one input class. Witness probes an "
            "empty text key, where the spec still demands `Except.ok (displayName ++ "
            "['.'])`. If it VERIFIES => SPEC-TOO-WEAK (the empty-key point is unpinned)."
        ),
        # empty key: gold -> ok "m."; rival -> error.
        "witness": _wit("['m']", "(PyKey.str [])",
                        "empty key rendering: gold still succeeds, this rival errors"),
    },
    {
        "id": "weak-empty-parent-drops-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_EMPTYPARENT,
        "refinement": (
            "a faithful patch that skipped the separator when the parent display name is "
            "empty would name the derived placeholder `T` instead of `.T` in exactly that "
            "case — an inconsistent display-name format that depends on the parent, so a "
            "consumer splitting the derived name on the separator sees a different number "
            "of components for the same operation. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C2 (SHAPE, separator piece) on the degenerate EMPTY-parent "
            "sub-domain — the dual of weak-empty-key-errors, and the sub-domain "
            "weak-drop-module's rationale names as the one where IT is correct. The spec's "
            "separator is unconditional: `displayName ++ '.' :: strChars key` keeps the "
            "'.' even when `displayName` is `[]`. Witness varies the `displayName` binder "
            "to the empty list — the one point no other witness in this battery visits, "
            "since all of them use a non-empty parent. If it VERIFIES => SPEC-TOO-WEAK "
            "(the separator is pinned only when the prefix is non-empty)."
        ),
        # empty parent: gold -> ok ".x"; rival -> ok "x".
        "witness": _wit("[]", "(PyKey.str ['x'])",
                        "empty parent: gold keeps the separator, this rival drops it"),
    },
]


# No consumed axioms and no opaque callees: the key rendering (strChars) and the
# display-name join (concatName) are modeled DEEPLY over transparent carriers, so the
# axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
