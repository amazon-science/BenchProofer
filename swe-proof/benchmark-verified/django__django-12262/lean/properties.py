# properties.py — G-PBT falsification battery for django__django-12262 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for the soundness positive, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the spec and not
# to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   parseTagArgs (params : List String) (hasVarArgs hasVarKeyword : Bool)
#                (defaults : Option Nat) (keywordOnly : List String)
#                (keywordDefaults : Option (List String)) (takesContext : Bool)
#                (name : String) (toks : List Tok)
#     -> Except String (List String × List (String × String))
#   Binds a run of already-classified argument tokens to a callable's declared
#   parameters, returning either the bound (positional-values, keyword-pairs) pair
#   on success or the exact formatted diagnostic text on every rejection. The single
#   postcondition pins the result to an EXACT functional equality with a reference
#   that is fully grounded in the inputs (no opaque oracle) — so any deviation on any
#   input is observable. The load-bearing clauses the reference decides, each an
#   independent attackable arm here:
#     * the accepted-keyword test (a supplied keyword names a declared positional OR
#       a declared keyword-only name — DEFAULT-INDEPENDENT — or a var-keyword catch-
#       all is present), else the unexpected-keyword diagnostic;
#     * the repeated-keyword test, whose diagnostic is DISTINCT from the unexpected
#       one and is checked only after acceptance;
#     * the positional-after-keyword ordering rule;
#     * the too-many-positional rule (suppressed only by a var-positional catch-all);
#     * the trailing-defaults truncation before the final completeness check;
#     * the leading context-parameter shape check.
#
# CARRIER NOTE (why this port is WIDER than nagini's): the nagini sibling abstracted
# the whole routine to a single int code (0/1/2) for the keyword-acceptance vs
# duplicate decision, with the read-only token run behind fractional permissions and
# the positional / defaults / context machinery unmodeled. This backend models the
# FULL routine over a transparent `Tok`/`BindState`/`Except` carrier, so every
# independent clause above (not just the keyword arm) is an attackable postcondition
# clause here. The port therefore attacks each modeled clause directly — the four
# positional/defaults/context rivals below reach arms nagini's int-code carrier could
# not express, exactly analogous to the wider django-13568 lean port.
#
# THE FIX (issue + FAIL_TO_PASS): the accepted-keyword test must consult the FULL
# declared keyword-only set, not the residual subset that still requires a value
# (keyword-only names WITHOUT their own default, minus those already bound). The
# pre-change routine consulted the residual subset, so a defaulted keyword-only name
# supplied explicitly was misclassified as unexpected. `weak-prepatch` below is
# exactly that reverted decision.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submission for the full account):
#   * FRAME-MUTATION (nagini's #1 class: the token run was Acc(list_pred,1/2) read-
#     only). Lean is referentially transparent — no aliasing, no permissions — so a
#     "write-back into a read-only input" rival is not expressible; the whole lane is
#     VACUOUS here.
#   * DIVERGENCE / NON-TERMINATION (nagini's diverge-before-answer, the P1 attack).
#     AUDIT CORRECTION: a diverging impl IS expressible on this backend — `partial def
#     spin (n : Nat) : Except … := spin (n+1)` passes variant_scope and elaborates, so
#     the earlier claim "cannot be written at all" was wrong. What is unavailable is a
#     WITNESS for it: measured, the variant is rejected with
#     `unsolved goals ⊢ spin 0 = parseTagArgsRef …` (exit 1), i.e. the obligation is an
#     unprovable equality rather than a refutable one, and a refutation witness needs
#     the rival's value to REDUCE at a concrete input, which a non-reducing `partial`
#     term never does. So the lane ships nothing here for a mechanical reason, not
#     because the rival is inexpressible. The divergence lane is SETTLED corpus-wide
#     and is not re-derived here: see the corpus-wide termination-semantics finding (measured on all
#     401 `partial` bundles, already escalated). Nothing to ship, and not a new
#     spec_holes entry.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them.
#
# ADMISSIBILITY — LANDED (second audit). The first audit recorded this lane as N/A
# on the reasoning "the lean obligation has NO precondition hypothesis, so nothing
# could be PRECOND-TOO-STRONG". That reason is WRONG, and it is the single
# systematically-dropped lane in this corpus. The analogue of a precondition-
# admission probe on a TOTAL carrier is not "is there a precondition" but "is the
# obligation SATISFIABLE at an F2P-shaped input" — an obligation that is
# unsatisfiable exactly where the reported behaviour lives is vacuously strong in
# precisely the way this lane exists to detect. `admiss-f2p-ground` below tests
# that directly, by discharging `problem_spec_parseTagArgs` at three concrete
# F2P/P2P-shaped points against LITERAL result values before closing the frozen
# obligation verbatim. Measured: the natural `decide` form does NOT work here
# (`failed to synthesize Decidable (implementation_… = parseTagArgsRef …)` — the
# `Except String (List String × List (String × String))` carrier has no derived
# decidable-equality instance in scope), but the carrier IS kernel-reducible, so
# `rfl` closes each point; full build exit 0.
#
# AUDIT ADDITIONS (independent adversarial audit of this port). The original port left
# five modeled decisions unattacked; each is now a rival below with its own
# machine-checked witness (rival build exit 0, gold build exit 1 on the concrete input,
# gold's failure being the `rfl` on the impl VALUE — a semantic refutation, not a name
# or type error):
#   * `weak-accept-every-keyword`  — nagini's `always-ok-supporting` near-miss, which
#     the port dropped without recording it. It is expressible here and lands.
#   * `weak-fence-empty-defaults`  — the `some 0` negative-slice quirk.
#   * `weak-keyword-skips-positional-slot` — a keyword filling a declared POSITIONAL
#     slot (the `pendingPositional` erase arm).
#   * `weak-kwonly-ignore-own-defaults` — the `requiredKeywordOnly` own-default filter,
#     i.e. the `keywordDefaults` binder, which no original case varied meaningfully.
#   * `weak-context-crash-as-diagnostic` — the empty-`params` context shape, where the
#     two failure values are DISTINCT.
# A second, stronger soundness positive (`pos-functional-fold`) was added because the
# original one is definitionally transparent and therefore reproves nothing.
#
# SECOND AUDIT (independent re-audit of the above). Re-derived every reject case's
# discrimination from scratch rather than reading the recorded outcomes, because all
# 12 gold-side signatures are `Type mismatch rfl has type ?m = ?m` — an application
# type mismatch, which is exactly the signature class that has been HOLLOW elsewhere
# in this corpus. The forgery experiment settles it here, and the four-cell table is
# the evidence: at each case's own input, `implementation_parseTagArgs <args> = <the
# REFERENCE value>` closes by `rfl` on gold (all 12 in one file, exit 0) and FAILS on
# the rival, while `= <the RIVAL value>` FAILS on gold (exit 1, `Tactic rfl failed:
# The left-hand side … is not definitionally equal to …`, a concrete value clash, not
# a metavariable) and closes on the rival. So gold's exit code TRACKS the claim: flip
# which value is asserted and the verdict flips on both sides. The `?m = ?m` shape is
# an artifact of the witness stating its value claim inside a `rw [show … from rfl]`,
# where the rewrite's motive is still a metavariable when `rfl` is checked; the
# underlying refutation is a real evaluation on both sides. No case was hollow.
# The one defect found was an OMISSION, now repaired: the admissibility lane, added
# above as `admiss-f2p-ground`.
from pathlib import Path

INSTANCE = "django__django-12262"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()

# The impl region as a whole is UNIQUE in the file (its logic is deliberately
# mirrored, verbatim, by the proof-region helpers implStep/implFold — so a whole-file
# _swap on any single guard line is NOT unique). Every variant therefore edits ONLY
# inside this block, which guarantees same_spec by construction.
_IMPL = _BASE[_BASE.index("-- impl-start"):_BASE.index("-- impl-end") + len("-- impl-end")]
assert _BASE.count(_IMPL) == 1, "impl region anchor drifted"


def _impl_swap(old, new):
    """Replace `old` -> `new` INSIDE the impl region only, then splice the edited
    region back into the frozen file. `old` must be unique within the impl region."""
    if old not in _IMPL:
        raise AssertionError(f"drift: {old!r}")
    if _IMPL.count(old) != 1:
        raise AssertionError(f"not unique in impl region: {old!r}")
    return _BASE.replace(_IMPL, _IMPL.replace(old, new, 1), 1)


def _reproof(module, new_body):
    """Replace the proof region body while keeping the frozen `theorem correct_*`
    STATEMENT byte-identical (only the tactic body may differ). Used by soundness
    positives that reprove; here the frozen proof already closes for the reshaped
    impl, so `new_body` re-uses it verbatim."""
    ps = module.index("-- proof-start")
    pe = module.index("-- proof-end") + len("-- proof-end")
    return module[:ps] + new_body + module[pe:]


def _witness(args, impl_val, ref_val):
    """A refutation witness stated at ONE concrete input. It reduces the rival's
    `implementation_parseTagArgs` to `impl_val` and the grounded reference to
    `ref_val` (both by `rfl`, since the carrier is fully transparent) and closes
    `impl_val ≠ ref_val` by `simp`. Elaborates against a rival that diverges from the
    reference there; FAILS on gold (whose impl equals the reference everywhere, so the
    rewrite to `impl_val` — an unequal value — cannot hold of it). No head binders =>
    no consistency probe needed."""
    return (
        f"example : ¬ problem_spec_parseTagArgs {args}\n"
        f"    (implementation_parseTagArgs {args}) := by\n"
        f"  unfold problem_spec_parseTagArgs\n"
        f"  rw [show implementation_parseTagArgs {args}\n"
        f"        = {impl_val} from rfl,\n"
        f"      show parseTagArgsRef {args}\n"
        f"        = {ref_val} from rfl]\n"
        f"  simp\n"
    )


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVE (expect="verify") — a structurally-different but CORRECT impl.
# The frozen impl decides the accepted-keyword arm with a single inline conjunctive
# guard; this control hoists that condition into a typed boolean `let` before
# branching, which is a shape a faithful patch could equally take. The result value
# is identical on every input; the `let` is definitionally transparent, so the frozen
# `correct_parseTagArgs` proof still closes verbatim (verified: full build, proof
# included). If it FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected).
# ---------------------------------------------------------------------------
_POS_HOIST_MODULE = _impl_swap(
    "        if ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword then\n"
    "          return Except.error (msgUnexpectedKeyword name param)",
    "        let unexpected := ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword\n"
    "        if unexpected then\n"
    "          return Except.error (msgUnexpectedKeyword name param)")
# Keep the frozen proof body verbatim (it closes for the reshaped impl unchanged).
_FROZEN_PROOF = _BASE[_BASE.index("-- proof-start"):_BASE.index("-- proof-end") + len("-- proof-end")]
_POS_HOIST = _reproof(_POS_HOIST_MODULE, _FROZEN_PROOF)


# ---------------------------------------------------------------------------
# SECOND SOUNDNESS POSITIVE (expect="verify") — a CORRECT impl whose shape the frozen
# proof does NOT close, so the obligation has to be re-earned rather than inherited.
#
# Why the hoisting positive above is not enough: `let unexpected := <cond>` is
# definitionally transparent, so the frozen tactic script closes it verbatim and the
# case exercises no proof work at all. This one replaces the whole imperative
# `Id.run do` + `for` + early-`return` body with a direct monadic fold — no mutable
# state, no loop, `Except`'s own bind for the short-circuit — which is exactly the
# shape a faithful reimplementation would take, and which the frozen
# `implFold`/`loopFold`/`context_stage_eq` chain no longer describes (those lemmas are
# about the `forIn` term this impl does not contain). The `theorem
# correct_parseTagArgs` STATEMENT is kept byte-identical; only the tactic body is
# rewritten, and the determinism corollary is kept. If it FAILS => SPEC-TOO-STRONG (the
# spec would be pinned to the frozen impl's syntactic form rather than its behavior).
# ---------------------------------------------------------------------------
_FUNCTIONAL_IMPL = """-- impl-start
def implementation_parseTagArgs (params : List String) (hasVarArgs hasVarKeyword : Bool)
    (defaults : Option Nat) (keywordOnly : List String)
    (keywordDefaults : Option (List String)) (takesContext : Bool) (name : String)
    (toks : List Tok) :
    Except String (List String × List (String × String)) :=
  let run (ps : List String) : Except String (List String × List (String × String)) :=
    (List.foldlM (stepTok ps keywordOnly hasVarKeyword hasVarArgs name)
        ({ args := [], kwargs := [], pendingPositional := ps,
           pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults } : BindState)
        toks) >>= fun st => finalizeBind defaults name st
  if takesContext then
    match params with
    | p :: rest => if p == "context" then run rest else Except.error (msgContext name)
    | [] => Except.error msgIndexError
  else run params
-- impl-end"""

# The frozen `theorem correct_parseTagArgs` STATEMENT, byte-for-byte (everything from
# the `theorem` keyword up to the proof-introducing `:= by`), so the reproof cannot
# weaken the obligation.
_CORRECT_STMT = _FROZEN_PROOF[_FROZEN_PROOF.index("theorem correct_parseTagArgs"):
                              _FROZEN_PROOF.index(":= by", _FROZEN_PROOF.index(
                                  "theorem correct_parseTagArgs"))]
# The frozen determinism corollary, kept verbatim: it is the machine-checked statement
# that the spec pins `result` uniquely, and a positive that dropped it would be
# reproving less than the frozen file does.
_DETERMINISM = _FROZEN_PROOF[_FROZEN_PROOF.index("/-- The spec is DETERMINISTIC"):
                             _FROZEN_PROOF.index("-- proof-end")]
_POS_FUNCTIONAL = _reproof(
    _BASE.replace(_IMPL, _FUNCTIONAL_IMPL, 1),
    "-- proof-start\n" + _CORRECT_STMT + """:= by
  intro params hasVarArgs hasVarKeyword defaults keywordOnly keywordDefaults takesContext name toks
  unfold problem_spec_parseTagArgs implementation_parseTagArgs parseTagArgsRef
  cases takesContext with
  | false => rfl
  | true =>
      cases params with
      | nil => rfl
      | cons p rest => by_cases hp : p == "context" <;> simp only [hp, if_true] <;> rfl

""" + _DETERMINISM + "-- proof-end")


# ---------------------------------------------------------------------------
# ADMISSIBILITY (expect="verify") — the obligation is SATISFIABLE at F2P-shaped
# inputs. The impl region is UNCHANGED and the `theorem correct_parseTagArgs`
# STATEMENT is byte-identical; three `have`s are prepended inside the existing
# tactic body, each applying `problem_spec_parseTagArgs` itself at a concrete
# point against a LITERAL result value (so none of them is a definitional
# tautology of the form `x = x` — the value is written out and must be the one the
# reference actually computes there), plus a fourth pinning the implementation's
# own value at the first point. Nothing new is declared.
#
# The three points, in the vocabulary of the defended surface only:
#   (1) a keyword-only parameter that CARRIES ITS OWN DEFAULT, supplied
#       explicitly by name — the sub-domain the reported behaviour is about; the
#       value must BIND (`Except.ok (["37"], [("two", "hi")])`) rather than be
#       diagnosed. If the obligation were unsatisfiable exactly here, every
#       uniqueness case above could still pass while the spec described nothing
#       usable at the input that matters.
#   (2) the same declaration with that defaulted keyword-only name OMITTED —
#       still admissible (`Except.ok (["37"], [])`).
#   (3) a context-decorated declaration in its WELL-FORMED shape (first declared
#       parameter is the context parameter) — the positive counterpart of the two
#       context rivals, which only pin the two mis-shapes.
# If any `have` FAILS => PRECOND-TOO-STRONG / spec-shape regression: the spec
# would be unsatisfiable at an input the real routine accepts.
# ---------------------------------------------------------------------------
_ADMISS_HAVES = '''  have _admit_kwonly_defaulted_supplied :
      problem_spec_parseTagArgs ["one"] false false none ["two"] (some ["two"]) false
        "one_default" [Tok.positional "37", Tok.keyword "two" "hi"]
        (Except.ok (["37"], [("two", "hi")])) := by
    unfold problem_spec_parseTagArgs
    rfl
  have _admit_kwonly_defaulted_omitted :
      problem_spec_parseTagArgs ["one"] false false none ["two"] (some ["two"]) false
        "one_default" [Tok.positional "37"]
        (Except.ok (["37"], [])) := by
    unfold problem_spec_parseTagArgs
    rfl
  have _admit_context_wellformed :
      problem_spec_parseTagArgs ["context", "one"] false false none [] none true
        "ctx_tag" [Tok.positional "37"]
        (Except.ok (["37"], [])) := by
    unfold problem_spec_parseTagArgs
    rfl
  have _admit_impl_meets_it :
      implementation_parseTagArgs ["one"] false false none ["two"] (some ["two"]) false
        "one_default" [Tok.positional "37", Tok.keyword "two" "hi"]
        = Except.ok (["37"], [("two", "hi")]) := by rfl
'''
_INTRO_LINE = ("  intro params hasVarArgs hasVarKeyword defaults keywordOnly "
               "keywordDefaults takesContext name toks\n")
assert _BASE.count(_INTRO_LINE) == 1, "intro anchor drifted"
_ADMISS = _BASE.replace(_INTRO_LINE, _ADMISS_HAVES + _INTRO_LINE, 1)


SPEC_TESTS = [
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is SATISFIABLE at F2P-shaped inputs. On this total "
            "carrier the frozen obligation carries no precondition binder, so the "
            "honest analogue of a precondition-admission probe is that the "
            "postcondition can actually be DISCHARGED where the reported behaviour "
            "lives: three `have`s apply `problem_spec_parseTagArgs` at concrete "
            "points against LITERAL result values — (1) a keyword-only parameter "
            "carrying its own default supplied explicitly by name, which must bind "
            "to `Except.ok ([\"37\"], [(\"two\", \"hi\")])`; (2) the same "
            "declaration with that name omitted; (3) a context-decorated "
            "declaration in its well-formed shape — and a fourth pins the "
            "implementation's own value at point (1). Because each result value is "
            "written out rather than left as `implementation_… = implementation_…`, "
            "none of them is a tautology that would hold in any file. Impl region "
            "unchanged, `theorem correct_parseTagArgs` statement byte-identical, "
            "nothing new declared. If any FAILS => PRECOND-TOO-STRONG / spec-shape "
            "regression (the spec would be unsatisfiable at an input the real "
            "routine accepts). NOTE: `decide` does NOT work at these points — the "
            "`Except String (List String × List (String × String))` carrier has no "
            "decidable-equality instance in scope — but it is kernel-reducible, so "
            "`rfl` closes each one."
        ),
    },

    {
        "id": "pos-hoisted-keyword-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HOIST,
        "rationale": (
            "structurally-different but CORRECT impl: the accepted-keyword arm's "
            "inline conjunctive guard is hoisted into a typed boolean `let` before the "
            "branch, producing the identical result on every input. The frozen "
            "`theorem correct_parseTagArgs` statement is kept byte-identical and its "
            "proof still closes (the `let` is definitionally transparent). If it FAILS "
            "=> SPEC-TOO-STRONG (a faithful correct impl rejected). NOTE (audit): "
            "because the `let` IS definitionally transparent, this case re-earns "
            "nothing — the frozen script closes it unchanged. It is kept as the cheap "
            "control; `pos-functional-fold` below is the one that reproves."
        ),
    },

    {
        "id": "pos-functional-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FUNCTIONAL,
        "rationale": (
            "a CORRECT impl in a genuinely different shape: the imperative `Id.run do` "
            "loop with early `return` is replaced by a direct monadic `List.foldlM` in "
            "`Except` plus a bind into the finalize step — no mutable state, no loop, "
            "the short-circuit carried by `Except`'s own bind. The frozen proof's "
            "`implFold`/`loopFold`/`context_stage_eq` chain describes a `forIn` term "
            "this impl does not contain, so the obligation is RE-PROVEN (byte-identical "
            "`theorem correct_parseTagArgs` statement, new tactic body, determinism "
            "corollary kept). If it FAILS => SPEC-TOO-STRONG: the spec would be pinned "
            "to the frozen impl's syntactic form rather than to its behaviour."
        ),
    },

    {
        "id": "weak-prepatch-residual-keyword-set",
        "kind": "uniqueness",
        "expect": "reject",
        # THE FIX, reverted: the accepted-keyword test consults the RESIDUAL keyword-
        # only subset (names still requiring a value) instead of the FULL declared
        # keyword-only set.
        "module": _impl_swap("¬ keywordOnly.contains param", "¬ st.pendingKeyword.contains param"),
        "refinement": (
            "this IS the pre-change decision: acceptability is tested against the "
            "residual keyword-only subset (names that still require a value) rather "
            "than the full declared keyword-only set. Its faithful real counterpart is "
            "the unchanged repo, which raises the unexpected-keyword diagnostic when a "
            "keyword-only name that carries its own default is supplied explicitly — "
            "exactly the FAIL_TO_PASS test_simple_tags / test_inclusion_tags cases that "
            "now expect the value to bind (result 37, not an error). It does NOT "
            "resolve, so a verifying rival here would be a true verify-does-not-imply-"
            "resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition's exact equality to the reference: on the "
            "discriminating sub-domain where a keyword names a DEFAULTED keyword-only "
            "parameter (in `keywordOnly`, absent from the residual subset), the "
            "reference binds it (Except.ok) but the rival raises the unexpected-keyword "
            "diagnostic. Attacks the accepted-keyword clause on the `keywordOnly`-vs-"
            "residual binder distinction — the precise behaviour the change introduces. "
            "If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # keywordOnly=["kwarg"] with a default declared (keywordDefaults=some ["kwarg"])
        # => residual subset empty; gold binds, rival raises.
        "witness": _witness(
            '[] false false none ["kwarg"] (some ["kwarg"]) false "tagA" [Tok.keyword "kwarg" "v"]',
            'Except.error "\'tagA\' received unexpected keyword argument \'kwarg\'"',
            'Except.ok ([], [("kwarg", "v")])'),
    },

    {
        "id": "weak-ignore-var-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the var-keyword catch-all disjunct from the accepted-keyword guard.
        "module": _impl_swap(" ∧ ¬ hasVarKeyword then", " then"),
        "refinement": (
            "dropping the var-keyword catch-all disjunct is what a real patch that "
            "removed the `hasVarKeyword` conjunct would do: a callable declaring a "
            "var-keyword catch-all that legitimately accepts an arbitrary extra keyword "
            "is wrongly rejected. It fails the PASS_TO_PASS unlimited-args-kwargs family "
            "that relies on a catch-all accepting arbitrary keyword arguments. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: the accepted-keyword clause disjoins the "
            "var-keyword catch-all, so on an unknown keyword with a catch-all present "
            "the reference binds (Except.ok) while the rival raises. Attacks the "
            "`hasVarKeyword` binder of the accepted-keyword clause. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # unknown keyword "x", no declared params/keyword-only, but hasVarKeyword=true:
        # gold binds, rival raises unexpected.
        "witness": _witness(
            '[] false true none [] none false "tagB" [Tok.keyword "x" "v"]',
            'Except.error "\'tagB\' received unexpected keyword argument \'x\'"',
            'Except.ok ([], [("x", "v")])'),
    },

    {
        "id": "weak-duplicate-as-unexpected",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the unexpected-keyword diagnostic where a repeated (already-bound)
        # keyword should yield the DISTINCT multiple-values diagnostic.
        "module": _impl_swap(
            "return Except.error (msgMultipleValues name param)",
            "return Except.error (msgUnexpectedKeyword name param)"),
        "refinement": (
            "emitting the unexpected-keyword diagnostic for a repeated acceptable "
            "keyword is what a real patch that reused the wrong message would do. It "
            "fails the FAIL_TO_PASS error assertions that pin the distinct "
            "'received multiple values for keyword argument' text for a doubly-supplied "
            "keyword. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: the reference pins the repeated-keyword "
            "case to the multiple-values diagnostic, a DISTINCT string from the "
            "unexpected-keyword one; the rival returns the latter. Attacks the "
            "repeated-keyword clause via the `toks` binder (two bindings of the same "
            "name). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # kwarg supplied twice, accepted (in keywordOnly): gold => multiple-values,
        # rival => unexpected.
        "witness": _witness(
            '[] false false none ["kwarg"] none false "tagC" [Tok.keyword "kwarg" "a", Tok.keyword "kwarg" "b"]',
            'Except.error "\'tagC\' received unexpected keyword argument \'kwarg\'"',
            'Except.error "\'tagC\' received multiple values for keyword argument \'kwarg\'"'),
    },

    {
        "id": "weak-drop-positional-after-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        # Remove the positional-after-keyword ordering guard: a positional token that
        # follows a keyword binding is silently accepted.
        "module": _impl_swap(
            "if ¬ st.kwargs.isEmpty then\n"
            "          return Except.error (msgPositionalAfterKeyword name)\n"
            "        else\n",
            ""),
        "refinement": (
            "dropping the ordering guard removes an unchanged sub-check, so a "
            "positional value supplied after a keyword binding is silently accepted "
            "rather than diagnosed. It fails the PASS_TO_PASS assertion pinning the "
            "'received some positional argument(s) after some keyword argument(s)' "
            "diagnostic. Does NOT resolve (this clause is unchanged by the fix and must "
            "be preserved)."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins a positional-after-keyword input "
            "to the ordering diagnostic; the rival binds it instead (Except.ok). "
            "Attacks the ordering clause via the `toks` binder (a positional after a "
            "keyword) with `hasVarArgs=true`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # keyword then positional, hasVarArgs=true so the positional would otherwise be
        # accepted: gold => ordering error, rival => ok.
        "witness": _witness(
            '["a"] true false none [] none false "tagD" [Tok.keyword "a" "v", Tok.positional "p"]',
            'Except.ok (["p"], [("a", "v")])',
            'Except.error "\'tagD\' received some positional argument(s) after some keyword argument(s)"'),
    },

    {
        "id": "weak-drop-too-many-positional",
        "kind": "uniqueness",
        "expect": "reject",
        # Turn the too-many-positional guard into a no-op: an extra positional with no
        # var-positional catch-all is silently accepted.
        "module": _impl_swap(
            "| [] => if ¬ hasVarArgs then return Except.error (msgTooManyPositional name)",
            "| [] => pure ()"),
        "refinement": (
            "neutering the too-many-positional guard removes an unchanged sub-check, so "
            "a positional value beyond the declared arity — with no var-positional "
            "catch-all — is silently accepted rather than diagnosed. It fails the "
            "PASS_TO_PASS assertion pinning the 'received too many positional arguments' "
            "diagnostic. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins an over-arity positional input "
            "(no var-positional catch-all) to the too-many-positional diagnostic; the "
            "rival binds it instead. Attacks the too-many-positional clause via the "
            "`params`/`toks` binders (two positionals, one declared slot). If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # one declared positional, two supplied, hasVarArgs=false:
        # gold => too-many error, rival => ok.
        "witness": _witness(
            '["a"] false false none [] none false "tagE" [Tok.positional "p1", Tok.positional "p2"]',
            'Except.ok (["p1", "p2"], [])',
            'Except.error "\'tagE\' received too many positional arguments"'),
    },

    {
        "id": "weak-ignore-trailing-defaults",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the declared trailing positional defaults at finalize: an unfilled
        # positional slot covered by a default is wrongly reported missing.
        "module": _impl_swap(
            "return finalizeBind defaults name st",
            "return finalizeBind none name st"),
        "refinement": (
            "ignoring the trailing-defaults truncation removes an unchanged sub-check, "
            "so a declared positional parameter that carries a default and is not "
            "supplied is wrongly reported as a missing required argument. It fails the "
            "PASS_TO_PASS one-default tag family, where the defaulted parameter may be "
            "omitted. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition, which applies the trailing-defaults "
            "truncation before the completeness check; on an omitted defaulted "
            "positional the reference succeeds (Except.ok) while the rival raises the "
            "missing-argument diagnostic. Attacks the `defaults` binder. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # one declared positional with a default (defaults=some 1), none supplied:
        # gold => ok, rival => missing.
        "witness": _witness(
            '["a"] false false (some 1) [] none false "tagF" []',
            'Except.error "\'tagF\' did not receive value(s) for the argument(s): \'a\'"',
            'Except.ok ([], [])'),
    },

    {
        "id": "weak-skip-context-shape-check",
        "kind": "uniqueness",
        "expect": "reject",
        # Always strip the leading parameter when context-decorated, without checking
        # it is actually the context parameter.
        "module": _impl_swap(
            '        if p == "context" then\n'
            "          params := rest\n"
            "        else\n"
            "          return Except.error (msgContext name)",
            "        params := rest"),
        "refinement": (
            "stripping the leading parameter unconditionally under context decoration "
            "removes the context-shape check: a context-decorated callable whose first "
            "declared parameter is NOT the context parameter is silently accepted "
            "rather than diagnosed. It fails the PASS_TO_PASS missing-context assertions "
            "that pin the takes_context shape diagnostic. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition, which pins a context-decorated mis-shape "
            "(first param not 'context') to the takes_context diagnostic; the rival "
            "strips the parameter and proceeds, diverging on both the diagnostic and "
            "the eventual result. Attacks the `takesContext`/`params` binders. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # takesContext=true, first param 'notctx' (not 'context'):
        # gold => context diagnostic, rival => proceeds and reports the tail as missing.
        "witness": _witness(
            '["notctx", "b"] false false none [] none true "tagG" []',
            'Except.error "\'tagG\' did not receive value(s) for the argument(s): \'b\'"',
            'Except.error "\'tagG\' is decorated with takes_context=True so it must have a first argument of \'context\'"'),
    },

    # -----------------------------------------------------------------------
    # AUDIT ADDITIONS — five modeled decisions the original port left unattacked.
    # Each was built and measured independently: rival witness build exit 0, gold
    # witness build exit 1 with the failure landing on the `rfl` that reduces
    # `implementation_parseTagArgs` at the concrete input (a semantic refutation).
    # -----------------------------------------------------------------------

    {
        "id": "weak-accept-every-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        # Both keyword guards removed: every keyword token is bound, so neither the
        # unexpected-keyword nor the multiple-values diagnostic is ever raised.
        "module": _impl_swap(
            "        if ¬ params.contains param ∧ ¬ keywordOnly.contains param ∧ ¬ hasVarKeyword then\n"
            "          return Except.error (msgUnexpectedKeyword name param)\n"
            "        else if st.kwargs.any (fun kv => kv.1 == param) then\n"
            "          return Except.error (msgMultipleValues name param)\n"
            "        else\n"
            "          st := { st with kwargs := st.kwargs ++ [(param, value)] }\n"
            "          if st.pendingPositional.contains param then\n"
            "            st := { st with pendingPositional := st.pendingPositional.erase param }\n"
            "          else if st.pendingKeyword.contains param then\n"
            "            st := { st with pendingKeyword := st.pendingKeyword.erase param }",
            "        st := { st with kwargs := st.kwargs ++ [(param, value)] }\n"
            "        if st.pendingPositional.contains param then\n"
            "          st := { st with pendingPositional := st.pendingPositional.erase param }\n"
            "        else if st.pendingKeyword.contains param then\n"
            "          st := { st with pendingKeyword := st.pendingKeyword.erase param }"),
        "refinement": (
            "this is the nagini sibling's `always-ok-supporting` near-miss, ported: a "
            "binder that never diagnoses a keyword accepts every malformed invocation. "
            "Its faithful real counterpart fails the whole error family — the "
            "FAIL_TO_PASS assertions that pin the unexpected-keyword and the "
            "multiple-values texts, and the PASS_TO_PASS ones for an undeclared keyword "
            "on a tag with no catch-all. Does NOT resolve. The original port dropped "
            "this case silently; it is expressible here and lands."
        ),
        "rationale": (
            "REJECTED by the postcondition's exact equality: on an undeclared keyword "
            "with no declared parameter of that name and no var-keyword catch-all the "
            "reference raises the unexpected-keyword diagnostic while the rival binds it "
            "(Except.ok). Attacks the accepted-keyword and repeated-keyword clauses "
            "jointly via the `toks` binder. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '[] false false none [] none false "tagN" [Tok.keyword "z" "v"]',
            'Except.ok ([], [("z", "v")])',
            'Except.error "\'tagN\' received unexpected keyword argument \'z\'"'),
    },

    {
        "id": "weak-fence-empty-defaults",
        "kind": "uniqueness",
        "expect": "reject",
        # "Fence" the declared-but-empty defaults case: treat `some 0` as if no
        # defaults were declared at all, instead of modeling the truncation faithfully.
        "module": _impl_swap(
            "  return finalizeBind defaults name st",
            "  match defaults with\n"
            "  | some 0 => return finalizeBind none name st\n"
            "  | _ => return finalizeBind defaults name st"),
        "refinement": (
            "a real patch that 'tidied' the trailing-defaults truncation by special-"
            "casing an empty defaults tuple diverges from the routine's actual "
            "behaviour: the truncation is a negative slice, and at length 0 a negative "
            "slice keeps NOTHING rather than everything. A callable whose declared "
            "defaults collection is present but empty therefore behaves differently "
            "from one that declares none at all, and this rival conflates the two. "
            "Does NOT resolve (it changes an unchanged sub-check)."
        ),
        "rationale": (
            "REJECTED by the postcondition: `finalizeBind` pins the present-but-empty "
            "defaults case to dropping every still-pending positional name (reference => "
            "Except.ok), whereas the rival keeps them and raises the missing-argument "
            "diagnostic. Attacks the `defaults` binder at its `some 0` point — a value "
            "no other case in this battery reaches (the trailing-defaults case uses "
            "`some 1`). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '["a"] false false (some 0) [] none false "tagH" []',
            'Except.error "\'tagH\' did not receive value(s) for the argument(s): \'a\'"',
            'Except.ok ([], [])'),
    },

    {
        "id": "weak-keyword-skips-positional-slot",
        "kind": "uniqueness",
        "expect": "reject",
        # A keyword naming a declared POSITIONAL parameter no longer fills that slot;
        # only the keyword-only pending list is consulted.
        "module": _impl_swap(
            "          if st.pendingPositional.contains param then\n"
            "            st := { st with pendingPositional := st.pendingPositional.erase param }\n"
            "          else if st.pendingKeyword.contains param then",
            "          if st.pendingKeyword.contains param then"),
        "refinement": (
            "dropping the positional-slot fill is what a real patch that consulted only "
            "the keyword-only pending list would do: a declared positional parameter "
            "supplied BY NAME is bound into the keyword map but its slot stays "
            "outstanding, so the final completeness check reports it missing. It fails "
            "the FAIL_TO_PASS / PASS_TO_PASS cases that supply a declared positional "
            "parameter as a keyword and expect the value to bind. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: the reference erases a bound name from the "
            "pending POSITIONAL list as well as the pending keyword-only list, so a "
            "declared positional supplied by name completes the binding (Except.ok), "
            "while the rival raises the missing-argument diagnostic. Attacks the "
            "positional-slot arm of the keyword branch via the `params`/`toks` binders — "
            "an arm no other case in this battery reaches. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '["a"] false false none [] none false "tagI" [Tok.keyword "a" "v"]',
            'Except.error "\'tagI\' did not receive value(s) for the argument(s): \'a\'"',
            'Except.ok ([], [("a", "v")])'),
    },

    {
        "id": "weak-kwonly-ignore-own-defaults",
        "kind": "uniqueness",
        "expect": "reject",
        # Every declared keyword-only name is treated as still requiring a value,
        # ignoring which of them carry their own default.
        "module": _impl_swap(
            "pendingKeyword := requiredKeywordOnly keywordOnly keywordDefaults }",
            "pendingKeyword := keywordOnly }"),
        "refinement": (
            "ignoring which keyword-only names carry their own default is a distinct "
            "wrong decision from the pre-change one above: acceptance is left correct, "
            "but the final completeness check now demands a value for a keyword-only "
            "parameter that has a default and may legitimately be omitted. It fails the "
            "FAIL_TO_PASS keyword-only-default cases that render successfully with the "
            "parameter absent. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: the reference's pending keyword-only list is "
            "`requiredKeywordOnly keywordOnly keywordDefaults`, which FILTERS OUT the "
            "names carrying their own default, so omitting such a name succeeds "
            "(Except.ok) while the rival raises the missing-argument diagnostic. This is "
            "the only case that varies the `keywordDefaults` binder for its own sake — "
            "the pre-change rival varies it only to make the acceptance arm bite. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '[] false false none ["k"] (some ["k"]) false "tagJ" []',
            'Except.error "\'tagJ\' did not receive value(s) for the argument(s): \'k\'"',
            'Except.ok ([], [])'),
    },

    {
        "id": "weak-context-crash-as-diagnostic",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapse the two distinct context-shape failure values: report the formatted
        # context diagnostic where the routine actually crashes uncaught.
        "module": _impl_swap(
            "    | [] => return Except.error msgIndexError",
            "    | [] => return Except.error (msgContext name)"),
        "refinement": (
            "a context-decorated callable that declares NO parameter at all is a "
            "different observable failure from one whose first declared parameter is "
            "merely the wrong name: the first is an unhandled crash escaping the "
            "template layer, the second a formatted template diagnostic. A real patch "
            "that reported the diagnostic for both would change observable behaviour on "
            "the no-parameter shape (a caller catching template-syntax errors would "
            "swallow what is currently an uncaught crash). Does NOT resolve; the "
            "distinction is recorded in the bundle's own refinement row for the context "
            "stage."
        ),
        "rationale": (
            "REJECTED by the postcondition: the reference returns the dedicated "
            "`msgIndexError` failure value on the empty-parameter context shape, a "
            "DISTINCT value from `msgContext`, and the rival returns the latter. Attacks "
            "the `takesContext`/`params` binders at the empty-`params` point — the "
            "degenerate arm the frozen obligation's own comment calls out and which no "
            "other case reaches (`weak-skip-context-shape-check` exercises the "
            "non-empty mis-shape). If it VERIFIES => SPEC-TOO-WEAK, since the two "
            "failure modes would be interchangeable."
        ),
        "witness": _witness(
            '[] false false none [] none true "tagK" []',
            'Except.error "\'tagK\' is decorated with takes_context=True so it must have a first argument of \'context\'"',
            'Except.error "IndexError: list index out of range"'),
    },
]


# No @ContractOnly axioms and no opaque callees consumed by the proof: the whole
# binding decision is modeled DEEPLY over the transparent Tok/BindState/Except
# carrier (the only boundary callees are the lexical/compile bridge, validated by
# G-CONF, not axiomatized). The axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
