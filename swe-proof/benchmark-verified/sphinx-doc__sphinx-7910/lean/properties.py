# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7910 (lean lane).
#
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive legitimately reproves, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on the
# frozen solution, so the rejection is attributable to the spec and not to a tactic
# script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#
#   memberInclusion : IncludeFlags → String → String → PyObj → Option Bool
#
#   The inclusion decision for a documented private / special / init member. The
#   single obligation `correct_memberInclusion` is a biconditional in two arms over
#   the transparent predicate `shouldInclude`:
#     (1) shouldInclude … = true  → result = some false   ("include it")
#     (2) shouldInclude … = false → result = none         (defer)
#   so the result is never `some true`. `shouldInclude` is GROUNDED in the inputs —
#   a total, transparent conjunction over the argument carrier, not an opaque
#   answer-key — and decomposes into five independent top-level conjuncts:
#     * the member is not the weak-reference slot;
#     * it carries a docstring;
#     * its declaring kind is documentable;
#     * a module member bypasses ownership, otherwise the class resolved FROM THE
#       UNDERLYING OBJECT'S DEFINING SCOPE must genuinely declare the member;
#     * the member's category toggle is on (three independent toggles: init, other
#       special, private).
#   Every one of those five is attacked below. The ownership conjunct — the
#   load-bearing one, the only operand the real change touches — is attacked four
#   ways: the scope it resolves through, whether declaring is checked at all, how
#   FAR along the wrapper chain it resolves, and which declaring kinds it covers.
#   The category conjunct is attacked once per toggle in each direction, plus on
#   the disjointness of the three category predicates.
#
# CARRIER NOTE / how the nagini rivals become these. The nagini sibling abstracted
# the same decision behind a `MemberObj` held at fractional read permission, with an
# `@ContractOnly` axiom bridging "the resolved scope's lookup" to a ground-truth
# ownership bit. This backend instead models the scope-resolution DEEPLY: `PyObj`
# carries an `inner` wrapper link and `coreObject` follows it to the end, so the
# ownership bridge nagini had to axiomatize is here a transparent computation. Each
# nagini rival therefore lands on a concrete impl edit, and each is refutable at a
# real input point.
#
# WITNESS MECHANICS on this carrier. Two of the spec's string predicates are
# well-founded recursive (`String.splitOn` behind `clsPathSingle`, and
# `String.startsWith`/`endsWith` behind the special/private category tests) and do
# NOT kernel-reduce: `decide`, `decide +kernel`, `rfl`, `grind` and `simp` with the
# unfolding lemmas all get stuck ("reduction got stuck at the Decidable instance",
# or a whnf heartbeat timeout), while plain String `==` and `isInitName` decide
# fine. So witnesses that touch a stuck predicate CONDITION on it instead of
# computing it — one weak hypothesis per stuck term, stating the refutation on the
# sub-domain where the rival is wrong. Witnesses on the module branch or the init
# category reach no stuck term and need no hypothesis at all. Every conditioned
# witness was checked three ways by hand before shipping: it elaborates against its
# rival, FAILS on the frozen solution, and its hypotheses are jointly satisfiable
# (the gate's `False`-derivation probe fails, as it must).
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME-MUTATION (nagini's mandatory class, 2 cases: a rival that writes back
#     into a half-permission input field). Lean is referentially transparent — no
#     aliasing, no fractional permission — so "store into a read-only input" is not
#     expressible. The class is genuinely VACUOUS here, not a hole.
#   * DIVERGENCE / non-termination — a KNOWN HOLE, not a vacuous class. Measured,
#     because the obvious reason is wrong: a diverging rival IS expressible here.
#     The frozen file sets no `loom.semantics.termination` (this is vanilla Lean +
#     Mathlib, not velvet), and while an ordinary `def` must terminate, a
#     `partial def spin (n : Nat) : Option Bool := spin (n+1)` delegated to from
#     the impl region passes variant_scope and the verifier does REJECT it. But it
#     is rejected unrefutably: `partial def` yields an OPAQUE constant, so the
#     refutation goal reduces only to `¬ spin 0 = some false` and no witness can
#     discharge it. A rejection with no witness attributes nothing to the spec —
#     it is precisely the tactic-mismatch outcome the witness requirement exists
#     to exclude — so the case is not shippable, and the honest disposition is
#     that this direction is UNTESTED here rather than inapplicable.
#     (ADMISSIBILITY is no longer in this list: the audit landed one. See
#     `admiss-f2p-shaped` — the lane's analogue on a total carrier is the
#     obligation being unsatisfiable at an F2P-shaped input, which has nothing to
#     do with whether a precondition hypothesis is present.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. This bundle
#     has no consumed axiom anyway — the scope resolution is modeled deeply, so it is
#     an A-reference validated by G-AX/G-CONF rather than an assumption.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7910"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file, so every _swap edits only the implementation.
# ---------------------------------------------------------------------------
_A_GUARD = '  if name != "__weakref__" && hasDoc && isMember then\n'
_A_ISMEM = ('  let isMember := what == "module" || what == "class" '
            '|| what == "exception"\n')
_A_SCOPE = ("        -- resolve the owning class via the UNDERLYING object's scope\n"
            "        match (obj.coreObject.globalsMap).lookup clsPath with\n")
_A_ATTRS = '        | some cls => clsOwner := cls.attrs.contains name\n'
_A_BYPASS = '    if what == "module" || clsOwner then\n'
_A_CAT = ('      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||\n'
          '         (isInit && cfg.incInit) then\n')
_A_RET = '        return some false\n'
_A_CLSEXC = '    if what == "class" || what == "exception" then\n'
_A_PRIVLET = ('      let isPrivate := (!isInit) && (!isSpecial) '
              '&& name.startsWith "_"\n')
_A_HASDOC = '  let hasDoc := obj.hasDoc\n'
_A_CLSPATH = '      match clsPathSingle obj.qualname with\n'
for _a in (_A_GUARD, _A_ISMEM, _A_SCOPE, _A_ATTRS, _A_BYPASS, _A_CAT, _A_RET,
           _A_CLSEXC, _A_PRIVLET, _A_HASDOC, _A_CLSPATH):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"impl anchor drifted: {_a!r}")

# Region bounds, used by the positives that supply a whole new impl + proof.
_IMPL_S = _BASE.index("-- impl-start\n") + len("-- impl-start\n")
_IMPL_E = _BASE.index("-- impl-end")
_PROOF_S = _BASE.index("-- proof-start\n") + len("-- proof-start\n")
_PROOF_E = _BASE.index("-- proof-end")
_FROZEN_PROOF = _BASE[_PROOF_S:_PROOF_E]

# The frozen `theorem correct_memberInclusion` STATEMENT, carried byte-identical
# into every reproving positive (variant_scope enforces this; keeping it as one
# literal means a drift in the frozen file breaks the manifest loudly).
_CORRECT_STMT = """theorem correct_memberInclusion :
    ∀ (cfg : IncludeFlags) (what name : String) (obj : PyObj),
      problem_spec_memberInclusion cfg what name obj
        (implementation_memberInclusion cfg what name obj) := by
"""
if _CORRECT_STMT not in _FROZEN_PROOF:
    raise AssertionError("frozen correct_memberInclusion statement drifted")


def _rebuild(impl, proof):
    """A full Solution.lean with a new impl region and a new proof region."""
    return _BASE[:_IMPL_S] + impl + _BASE[_IMPL_E:_PROOF_S] + proof + _BASE[_PROOF_E:]


# ---------------------------------------------------------------------------
# Witness construction. `_wit` states `¬ problem_spec … (implementation …)` at a
# concrete input; `binders` conditions on the stuck string predicates when the
# chosen point touches one (see WITNESS MECHANICS above).
# ---------------------------------------------------------------------------
_SIMPSET = ("problem_spec_memberInclusion, shouldInclude, clsIsOwner,\n"
            "        implementation_memberInclusion, Id.run, bind, pure, "
            "PyObj.qualname,\n"
            "        PyObj.hasDoc, PyObj.coreObject, PyObj.globalsMap,\n"
            "        isInitName, isSpecialName, isPrivateName")


def _wit(note, cfg, what, name, obj, binders="", hyps=""):
    head = f"example {binders} :" if binders else "example :"
    return (f"-- {note}\n"
            f"{head}\n"
            f"    ¬ problem_spec_memberInclusion {cfg} \"{what}\" \"{name}\"\n"
            f"    {obj}\n"
            f"    (implementation_memberInclusion {cfg} \"{what}\" \"{name}\"\n"
            f"    {obj}) := by\n"
            f"  simp [{_SIMPSET}{hyps}]")


# Config points. All three toggles are moved independently across the reject
# witnesses, in BOTH directions — each is switched on alone at a point where the
# spec demands inclusion, and off at a point where it demands deferral — so no
# rival that mishandles a single toggle can hide behind another being on, and none
# can hide in the direction the toggle is not exercised.
_CFG_INIT = "{ incInit := true,  incSpecial := false, incPrivate := false }"
_CFG_SPEC = "{ incInit := false, incSpecial := true,  incPrivate := false }"
_CFG_PRIV = "{ incInit := false, incSpecial := false, incPrivate := true  }"
_CFG_OFF = "{ incInit := false, incSpecial := false, incPrivate := false }"

# Module-scope member objects: the ownership resolution is bypassed, so no stuck
# string predicate is reached and these witnesses need no hypothesis.
_M_DOC = '(PyObj.node "m.__init__" true  [] none)'
_M_UNDOC = '(PyObj.node "m.__init__" false [] none)'

# A DECORATED class member — the shape the whole change is about: this object is a
# wrapper whose OWN defining scope is empty, while the underlying object it wraps
# has the declaring class in scope.
_DEC_OWNED = ('(PyObj.node "S.__init__" true []\n'
              '      (some (PyObj.node "S.__init__" true '
              '[("S", ⟨["__init__"]⟩)] none)))')
# …the class is in the underlying scope but does NOT declare this member.
_DEC_NOT_DECLARED = ('(PyObj.node "S.__init__" true []\n'
                     '      (some (PyObj.node "S.__init__" true '
                     '[("S", ⟨["other"]⟩)] none)))')
# …nothing in scope anywhere.
_DEC_NO_SCOPE = ('(PyObj.node "S.__init__" true []\n'
                 '      (some (PyObj.node "S.__init__" true [] none)))')
# …a TWO-LINK wrapper chain: composed decoration, where only the INNERMOST object
# — the end of the chain, not merely the next link — has the class in scope. The
# only point that separates "follow the links to the end" from "take one step".
_DEC_DEEP_OWNED = ('(PyObj.node "S.__init__" true []\n'
                   '      (some (PyObj.node "S.__init__" true []\n'
                   '        (some (PyObj.node "S.__init__" true '
                   '[("S", ⟨["__init__"]⟩)] none)))))')

# The one hypothesis the class-branch witnesses need: the qualified name splits
# into a single dotless owner segment. Satisfiable (it is what that name does).
_H_CLSPATH = '(h : clsPathSingle "S.__init__" = some "S")'


SPEC_TESTS = []

# =====================================================================
#  SOUNDNESS POSITIVES — must VERIFY, else SPEC-TOO-STRONG.
# =====================================================================

# (P1) The direct-verdict impl. `shouldInclude` is the postcondition's own
# predicate and is a TRANSPARENT total function of the arguments, so branching on
# it is a fully-grounded correct implementation — not an ungrounded-oracle echo
# (there is no opaque answer-key here; a wrong constant fails the postcondition
# outright, as the `weak-always-none` / `weak-returns-some-true` rivals show).
# Reproves honestly: the statement is byte-identical, the body discharges both
# arms from the hypothesis. If this FAILS => SPEC-TOO-STRONG.
SPEC_TESTS.append({
    "id": "pos-direct-verdict",
    "kind": "soundness",
    "expect": "verify",
    "module": _rebuild(
        """def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) : Option Bool := Id.run do
  if shouldInclude cfg what name obj then
    return some false
  return none
""",
        _CORRECT_STMT + """  intro cfg what name obj
  unfold problem_spec_memberInclusion implementation_memberInclusion
  constructor
  · intro h
    simp [Id.run, bind, pure, h]
  · intro h
    simp [Id.run, bind, pure, h]
""",
    ),
    "rationale": (
        "The cheapest HONEST impl: branch directly on the postcondition's own "
        "predicate, which is grounded in the arguments (a transparent total "
        "conjunction over the input carrier, no opaque callee). Structurally very "
        "different from the frozen nested-branch shape, so the frozen tactic script "
        "cannot close it; the proof body is honestly re-closed (statement kept "
        "byte-identical, no new axiom/lemma/sorry, both arms discharged from the "
        "hypothesis). Must verify — the postcondition says exactly this. If it "
        "FAILS => SPEC-TOO-STRONG. Also demonstrates the spec is not echo-"
        "vulnerable: substituting any constant for the verdict fails it."),
})

# (P2) Hoist every category flag and the combined category test ABOVE the
# ownership resolution, into straight-line lets. Same value on every input — the
# category test is independent of ownership — only the statement order changes.
# This is the shape a faithful patch could equally take. The frozen proof body is
# carried over unchanged and still closes.
SPEC_TESTS.append({
    "id": "pos-hoist-category",
    "kind": "soundness",
    "expect": "verify",
    "module": _rebuild(
        """def implementation_memberInclusion (cfg : IncludeFlags) (what name : String)
    (obj : PyObj) : Option Bool := Id.run do
  let hasDoc := obj.hasDoc
  let isMember := what == "module" || what == "class" || what == "exception"
  let isInit := name == "__init__"
  let isSpecial := (!isInit) && name.startsWith "__" && name.endsWith "__"
  let isPrivate := (!isInit) && (!isSpecial) && name.startsWith "_"
  let categoryOn := (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||
                    (isInit && cfg.incInit)
  if name != "__weakref__" && hasDoc && isMember then
    let mut clsOwner := false
    if what == "class" || what == "exception" then
      match clsPathSingle obj.qualname with
      | some clsPath =>
        match (obj.coreObject.globalsMap).lookup clsPath with
        | some cls => clsOwner := cls.attrs.contains name
        | none => clsOwner := false
      | none => clsOwner := false
    if what == "module" || clsOwner then
      if categoryOn then
        return some false
  return none
""",
        _FROZEN_PROOF,
    ),
    "rationale": (
        "Structurally different but CORRECT: the three category predicates and their "
        "combined test are hoisted out of the innermost branch into straight-line "
        "lets computed before the ownership resolution. The category test does not "
        "depend on ownership, so the verdict is identical on every input; only the "
        "order of computation changes. Must verify, else the postcondition is "
        "over-fit to one nesting order => SPEC-TOO-STRONG."),
})

# (P3) Commute the three independent conjuncts of the early guard. All three are
# pure boolean tests of distinct inputs, so the conjunction's value is unchanged.
SPEC_TESTS.append({
    "id": "pos-commute-guard",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(
        _BASE, _A_GUARD,
        '  if hasDoc && isMember && name != "__weakref__" then\n'),
    "rationale": (
        "Structurally different but CORRECT: the three conjuncts of the entry guard "
        "are commuted. Each is a pure boolean test of a distinct input (docstring "
        "presence, declaring kind, the weak-reference-slot name), so the "
        "conjunction's value — and hence the verdict — is identical on every input. "
        "Must verify, else the postcondition is over-fit to one conjunct order => "
        "SPEC-TOO-STRONG."),
})

# =====================================================================
#  ADMISSIBILITY — must VERIFY, else PRECOND-TOO-STRONG.
# =====================================================================

# (P4) Added by the audit. The shipped battery recorded this lane as having "no
# counterpart" because the obligation carries no precondition hypothesis. That
# reason is wrong: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
# obligation being UNSATISFIABLE at a concrete, realistic input — an include arm
# that no input can actually make fire is satisfied vacuously, and a spec whose
# demanding branch is unreachable would pass every other case in this battery
# while pinning nothing there. This case discharges the obligation at two
# concrete inputs BY EVALUATION, as `have`s, before closing the frozen obligation
# verbatim, so both are machine-checked rather than asserted.
#
# The two points are chosen to be the two halves of the reachability question:
#   (a) a documented member of a documentable kind with its category toggle on,
#       where the whole decision reduces by `decide` with no hypothesis at all —
#       this shows the include arm FIRES and `shouldInclude` is genuinely
#       satisfiable, not merely non-contradictory;
#   (b) the demanding shape: a member reached through a decoration wrapper whose
#       own defining scope is empty, so ownership is establishable ONLY through
#       the underlying object. This is the input the whole instance turns on, and
#       it is the one an over-strong ownership conjunct would make unreachable.
# Point (b) is stated under the hypothesis naming what the qualified name splits
# to, because that string operation does not kernel-reduce on this carrier (see
# WITNESS MECHANICS) — the hypothesis is discharged as an implication that is
# PROVED, not assumed, and it is the same satisfiable fact the reject witnesses
# condition on.
SPEC_TESTS.append({
    "id": "admiss-f2p-shaped",
    "kind": "admissibility",
    "expect": "verify",
    "module": _rebuild(
        _BASE[_IMPL_S:_IMPL_E],
        _FROZEN_PROOF.replace(
            _CORRECT_STMT + """  intro cfg what name obj
  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
""",
            _CORRECT_STMT + """  -- ADMISSIBILITY: discharge the obligation at CONCRETE inputs first, so the
  -- include arm is shown to be REACHABLE rather than vacuously satisfied.
  -- (a) A documented member whose category toggle is on: decides outright.
  have _adm_fires :
      implementation_memberInclusion
        { incInit := true, incSpecial := false, incPrivate := false }
        "module" "__init__" (PyObj.node "m.__init__" true [] none) = some false := by
    decide
  have _adm_reachable :
      shouldInclude { incInit := true, incSpecial := false, incPrivate := false }
        "module" "__init__" (PyObj.node "m.__init__" true [] none) = true := by
    decide
  have _adm_obligation :
      problem_spec_memberInclusion
        { incInit := true, incSpecial := false, incPrivate := false }
        "module" "__init__" (PyObj.node "m.__init__" true [] none)
        (implementation_memberInclusion
          { incInit := true, incSpecial := false, incPrivate := false }
          "module" "__init__" (PyObj.node "m.__init__" true [] none)) :=
    ⟨fun _ => _adm_fires, fun h => absurd (_adm_reachable.symm.trans h) (by decide)⟩
  -- (b) The demanding shape: ownership establishable only through the underlying
  -- object, i.e. a member reached past a decoration wrapper with an empty scope.
  have _adm_wrapped :
      ∀ _h : clsPathSingle "S.__init__" = some "S",
      implementation_memberInclusion
        { incInit := true, incSpecial := false, incPrivate := false }
        "class" "__init__"
        (PyObj.node "S.__init__" true []
          (some (PyObj.node "S.__init__" true [("S", ⟨["__init__"]⟩)] none)))
        = some false := by
    intro h
    simp [implementation_memberInclusion, Id.run, bind, pure, isInitName,
          PyObj.qualname, PyObj.hasDoc, PyObj.coreObject, PyObj.globalsMap, h]
  have _adm_wrapped_spec :
      ∀ _h : clsPathSingle "S.__init__" = some "S",
      shouldInclude { incInit := true, incSpecial := false, incPrivate := false }
        "class" "__init__"
        (PyObj.node "S.__init__" true []
          (some (PyObj.node "S.__init__" true [("S", ⟨["__init__"]⟩)] none)))
        = true := by
    intro h
    simp [shouldInclude, clsIsOwner, isInitName, isSpecialName, isPrivateName,
          PyObj.qualname, PyObj.hasDoc, PyObj.coreObject, PyObj.globalsMap, h]
  intro cfg what name obj
  refine ⟨include_direction cfg what name obj, exclude_direction cfg what name obj⟩
"""),
    ),
    "rationale": (
        "PRECOND-TOO-STRONG probe, in the form that lane takes on a total carrier: "
        "the obligation carries no precondition hypothesis, so what can go wrong "
        "is not an unsatisfiable `Requires` but an obligation that is "
        "UNSATISFIABLE — vacuously true — at exactly the inputs it is supposed to "
        "constrain. The impl region is the frozen one byte-for-byte and the frozen "
        "obligation is closed verbatim; what is added is that the obligation is "
        "ALSO discharged at two concrete inputs before that, by evaluation, so the "
        "include arm is machine-checked to fire rather than merely to be "
        "non-contradictory. Point (a) is a documented member with its toggle on, "
        "which decides outright; point (b) is the demanding shape where ownership "
        "is establishable only through the underlying object. If this FAILS => "
        "PRECOND-TOO-STRONG: the spec's include arm would be unreachable at a "
        "realistic input, and every reject case's arm-(1) refutation would be "
        "attesting to a branch nothing can enter."),
})

# =====================================================================
#  UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK.
#  Each shares the frozen spec exactly, edits only the impl region, and carries
#  a witness SEEN to elaborate against the rival and fail on the frozen file.
# =====================================================================

# (1) THE operand the real change turns on: resolve the owning class through this
# object's OWN defining scope instead of the underlying object's.
SPEC_TESTS.append({
    "id": "prepatch-own-scope",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _A_SCOPE,
        "        -- resolve the owning class via this object's own scope\n"
        "        match (obj.globalsMap).lookup clsPath with\n"),
    "refinement": (
        "This is the pre-change operand, and the whole point of the instance. When a "
        "member is produced by decoration, the object autodoc hands over is the "
        "WRAPPER: metadata such as the docstring and the qualified name are copied "
        "onto it, but its defining scope is the decorator's, which does not contain "
        "the declaring class. Resolving through that scope finds nothing, ownership "
        "comes out false, and the member is deferred (`none`) instead of included "
        "(`some false`) — exactly the F2P assertion "
        "(SkipMemberTest::test_class_decorated_doc asserts the result IS False for a "
        "decorated documented class member with its category toggle on). A faithful "
        "real patch keeping this operand does NOT resolve, so a verifying rival here "
        "would be a true verify-does-not-imply-resolve break."),
    "rationale": (
        "REJECTED by arm (1) of the biconditional at the decorated-member point: the "
        "ownership conjunct of `shouldInclude` resolves through the UNDERLYING "
        "object's scope, which declares the member, so the spec pins the result to "
        "`some false`; resolving through this object's own (empty) scope yields "
        "`none`. Attacks the ownership conjunct, varying the `obj` binder along its "
        "wrapper-link dimension — the one input dimension no other rival moves. "
        "If it VERIFIES => SPEC-TOO-WEAK (the deep scope model would be hollow)."),
    "witness": _wit(
        "decorated member: the underlying scope declares it (spec => some false), "
        "this object's own scope is empty (rival => none).",
        _CFG_INIT, "class", "__init__", _DEC_OWNED, _H_CLSPATH, ", h"),
})

# (2) Drop the docstring conjunct.
SPEC_TESTS.append({
    "id": "weak-drop-hasdoc",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_GUARD,
                    '  if name != "__weakref__" && isMember then\n'),
    "refinement": (
        "Including an UNDOCUMENTED member inverts the paired half of every skip "
        "test: the suite checks each category twice, asserting the documented member "
        "is included and the undocumented one deferred "
        "(test_class_special_undoc, test_class_private_undoc, "
        "test_module_special_undoc and their exception/module twins all assert "
        "`None`). A real patch dropping the docstring test fails all of them, so it "
        "does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): with no docstring `shouldInclude` is false and the spec "
        "pins the result to `none`, but the rival returns `some false`. Attacks the "
        "docstring conjunct, varying the hasDoc dimension of `obj`. If it VERIFIES "
        "=> SPEC-TOO-WEAK."),
    "witness": _wit(
        "undocumented module member: spec => none, rival => some false.",
        _CFG_INIT, "module", "__init__", _M_UNDOC),
})

# (3) Drop the weak-reference-slot exclusion.
SPEC_TESTS.append({
    "id": "weak-drop-weakref",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_GUARD, '  if hasDoc && isMember then\n'),
    "refinement": (
        "The weak-reference slot is a machine-generated attribute that reads as a "
        "documented special member, so without its exclusion it is emitted into the "
        "docs of every class that has one. A real patch dropping the exclusion "
        "regresses the documented output of the whole suite's class/exception "
        "fixtures — it does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): the weak-reference slot makes `shouldInclude` false "
        "however the toggles stand, so the spec pins the result to `none`; the rival "
        "returns `some false`. Attacks the weak-reference conjunct, varying the "
        "`name` binder onto that reserved name. Conditioned on the two well-founded "
        "string predicates behind the special-category test (they do not "
        "kernel-reduce); the hypotheses only state what that name does and are "
        "jointly satisfiable. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "the weak-reference slot, documented, special toggle on: spec => none "
        "(reserved name excluded), rival => some false.",
        _CFG_SPEC, "module", "__weakref__",
        '(PyObj.node "m.__weakref__" true [] none)',
        '(h1 : "__weakref__".startsWith "__" = true)\n'
        '    (h2 : "__weakref__".endsWith "__" = true)', ", h1, h2"),
})

# (4) Widen the documentable-kind set, and let the new kind bypass ownership the
# way a module member does.
SPEC_TESTS.append({
    "id": "weak-widen-kind",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _swap(_BASE, _A_ISMEM,
              '  let isMember := what == "module" || what == "class" '
              '|| what == "exception"\n'
              '                  || what == "method"\n'),
        _A_BYPASS,
        '    if what == "module" || what == "method" || clsOwner then\n'),
    "refinement": (
        "The decision is only ever meant to fire for the three documentable kinds; "
        "for anything else the hook must defer so the surrounding machinery keeps "
        "its own verdict. Admitting a further kind — and letting it skip the "
        "ownership test as a module member does — makes the hook override decisions "
        "that are not its to make, emitting members the default logic excludes. A "
        "real patch widening the kind set does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): for an undocumentable declaring kind `shouldInclude` is "
        "false and the spec pins the result to `none`, but the rival returns "
        "`some false`. Attacks the documentable-kind conjunct, varying the `what` "
        "binder off the three admitted values. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "an undocumentable declaring kind: spec => none, rival => some false.",
        _CFG_INIT, "method", "__init__", _M_DOC),
})

# (5) Drop the ownership requirement for class members altogether.
SPEC_TESTS.append({
    "id": "weak-drop-ownership",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_BYPASS, '    if true then\n'),
    "refinement": (
        "Without the ownership test a class member is included whether or not the "
        "resolved class declares it, so INHERITED members are documented on every "
        "subclass. That is the regression the ownership test was introduced to stop; "
        "the suite pins it via the namedtuple fixture (test_namedtuple asserts the "
        "inherited private accessor is deferred, i.e. `None`, on modern Python "
        "precisely because ownership cannot be established). A real patch dropping "
        "ownership fails it and does NOT resolve. Note this rival is strictly WEAKER "
        "than the pre-change operand rival: it abandons the test rather than "
        "resolving it through the wrong scope, and it is refuted at a different "
        "input — a member nothing in scope declares."),
    "rationale": (
        "REJECTED by arm (2): with no declaring class anywhere in scope the ownership "
        "conjunct is false, so the spec pins the result to `none`; the rival returns "
        "`some false`. Attacks the ownership conjunct from the opposite side to "
        "prepatch-own-scope, varying `obj` onto an empty-scope point. If it VERIFIES "
        "=> SPEC-TOO-WEAK."),
    "witness": _wit(
        "class member with nothing in scope: spec => none, rival => some false.",
        _CFG_INIT, "class", "__init__", _DEC_NO_SCOPE, _H_CLSPATH, ", h"),
})

# (6) NEAR-MISS on ownership: finding the class in scope is taken as ownership,
# without checking that it actually declares the member.
SPEC_TESTS.append({
    "id": "weak-owner-ignores-declaration",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_ATTRS,
                    '        | some _cls => clsOwner := true\n'),
    "refinement": (
        "A NEAR-MISS: it agrees with the frozen decision wherever the resolved class "
        "does declare the member — including on the decorated-member point the F2P "
        "turns on — and diverges only where the class is in scope but the member is "
        "inherited rather than declared. That is exactly the namedtuple fixture "
        "(test_namedtuple): the class resolves, the inherited accessor is not among "
        "its own declared attributes, and the assertion is `None`. So a real patch "
        "with this body passes the F2P and still does NOT resolve, which is the "
        "sharpest form of verify-does-not-imply-resolve. Given its own witness "
        "rather than sharing one, since it agrees with the frozen solution over "
        "strictly more of the domain than the other ownership rivals."),
    "rationale": (
        "REJECTED by arm (2): the ownership conjunct requires the resolved class to "
        "DECLARE the member, so with the class in scope but the member absent from "
        "its declared attributes the spec pins the result to `none`; the rival "
        "returns `some false`. Attacks the declares-it half of the ownership "
        "conjunct, varying `obj` onto a class-present/member-not-declared point that "
        "no other witness probes. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "resolved class is in scope but does not declare this member: "
        "spec => none, rival => some false.",
        _CFG_INIT, "class", "__init__", _DEC_NOT_DECLARED, _H_CLSPATH, ", h"),
})

# (7) The init category fires regardless of its toggle.
SPEC_TESTS.append({
    "id": "weak-ignore-init-toggle",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _A_CAT,
        '      if (isSpecial && cfg.incSpecial) || (isPrivate && cfg.incPrivate) ||\n'
        '         isInit then\n'),
    "refinement": (
        "Ignoring a category's toggle documents that category even when the user has "
        "switched it off. The suite tests exactly this: every skip test sets its "
        "config value True, asserts inclusion, then sets it back to False and "
        "asserts `None`. A real patch honouring the category unconditionally fails "
        "that second assertion on every init case and does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): with all three toggles off `shouldInclude` is false and "
        "the spec pins the result to `none`, but the rival still returns "
        "`some false`. Attacks the category conjunct through the init toggle, varying "
        "`cfg` to the all-off point. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "init member with every toggle off: spec => none, rival => some false.",
        _CFG_OFF, "module", "__init__", _M_DOC),
})

# (8) The private category fires regardless of its toggle. Separate case from (7)
# because the three toggles are INDEPENDENT: a rival mishandling only this one
# would be invisible to a battery that moved just the init toggle.
SPEC_TESTS.append({
    "id": "weak-ignore-private-toggle",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _A_CAT,
        '      if (isSpecial && cfg.incSpecial) || isPrivate ||\n'
        '         (isInit && cfg.incInit) then\n'),
    "refinement": (
        "The private counterpart of the init-toggle rival, and NOT redundant with it: "
        "the three toggles are independent inputs, so a patch honouring only the "
        "private category unconditionally is a distinct defect. It fails the "
        "toggle-off half of every private test "
        "(test_class_private_doc, test_exception_private_doc, "
        "test_module_private_doc all re-disable the config and assert `None`) and so "
        "does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): with every toggle off the spec pins a documented "
        "private member to `none`, but the rival returns `some false`. Attacks the "
        "category conjunct through the PRIVATE toggle specifically — the independent "
        "dimension the init-toggle rival leaves untested — and varies `name` onto a "
        "private-form name. Conditioned on the two well-founded string predicates "
        "behind the private-category test; the hypotheses state only what that name "
        "does and are jointly satisfiable. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "private member with every toggle off: spec => none, rival => some false.",
        _CFG_OFF, "module", "_helper", '(PyObj.node "m._helper" true [] none)',
        '(h1 : "_helper".startsWith "_" = true)\n'
        '    (h2 : "_helper".startsWith "__" = false)', ", h1, h2"),
})

# (9) PARTIAL DOMAIN: only the init category is honoured; special and private are
# dropped.
SPEC_TESTS.append({
    "id": "weak-init-category-only",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_CAT, '      if isInit && cfg.incInit then\n'),
    "refinement": (
        "Correct on the init sub-domain (the scenario the issue reports) and wrong on "
        "the other two categories: a documented special or private member with its "
        "toggle ON is deferred instead of included. A real patch with this body fails "
        "the inclusion half of every special and private test — including the F2P "
        "itself, which exercises the SPECIAL category with "
        "napoleon_include_special_with_doc enabled — so it does NOT resolve."),
    "rationale": (
        "REJECTED by arm (1) on the special sub-domain: a documented special member "
        "with the special toggle on makes `shouldInclude` true, so the spec pins the "
        "result to `some false`; the rival returns `none`. Attacks the category "
        "conjunct's special disjunct, varying `cfg` and `name` together onto the "
        "special-category point. Conditioned on the well-founded string predicates "
        "behind that test; the hypotheses are jointly satisfiable. If it VERIFIES => "
        "SPEC-TOO-WEAK."),
    "witness": _wit(
        "documented special member, special toggle on: spec => some false, "
        "rival => none.",
        _CFG_SPEC, "module", "__special__",
        '(PyObj.node "m.__special__" true [] none)',
        '(h1 : "__special__".startsWith "__" = true)\n'
        '    (h2 : "__special__".endsWith "__" = true)', ", h1, h2"),
})

# (10) Always defer — the cheapest impl satisfying arm (2) alone.
SPEC_TESTS.append({
    "id": "weak-always-none",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_RET, '        return none\n'),
    "refinement": (
        "Never including anything is the degenerate impl that satisfies the defer arm "
        "for free. A real patch that always defers documents none of these members, "
        "failing the inclusion assertion of the F2P and of all sixteen skip tests — "
        "it does NOT resolve."),
    "rationale": (
        "REJECTED by arm (1): at any point where `shouldInclude` is true the spec "
        "pins the result to `some false`, but this always yields `none`. Attacks arm "
        "(1) as a whole. If it VERIFIES => SPEC-TOO-WEAK (the include arm would be "
        "vacuous)."),
    "witness": _wit(
        "documented init member, init toggle on: spec => some false, rival => none.",
        _CFG_INIT, "module", "__init__", _M_DOC),
})

# (11) Report the wrong verdict VALUE. The spec's "never `some true`" content is a
# consequence of the two arms and needs its own rival.
SPEC_TESTS.append({
    "id": "weak-returns-some-true",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_RET, '        return some true\n'),
    "refinement": (
        "The two verdicts are not interchangeable: deferring leaves the surrounding "
        "machinery's own decision in place, while this value actively suppresses the "
        "member — the opposite of including it. So a real patch returning it "
        "documents nothing and additionally overrides decisions the hook should have "
        "left alone. The suite pins the distinction by identity rather than "
        "truthiness (the test change accompanying this instance tightens the "
        "inclusion assertion to `assertIs(..., False)`), so this does NOT resolve."),
    "rationale": (
        "REJECTED by arm (1), which pins the included verdict to `some false` "
        "specifically — this is where the spec's 'never `some true`' content bites. "
        "Attacks the value side of arm (1) rather than a `shouldInclude` conjunct. If "
        "it VERIFIES => SPEC-TOO-WEAK (the spec would not distinguish suppressing a "
        "member from including it)."),
    "witness": _wit(
        "documented init member, init toggle on: spec => some false, "
        "rival => some true.",
        _CFG_INIT, "module", "__init__", _M_DOC),
})


# (12) NEAR-MISS on the resolution itself: take ONE step along the wrapper link
# instead of following it to the END. Added by the audit: the shipped battery
# moved `obj` along its wrapper dimension only at depth 1, where "one step" and
# "to the end" coincide, so the *chain-following* half of the resolution — the
# part that is more than a single dereference — was never separated from a single
# step. Refuted at depth 2 (composed decoration).
SPEC_TESTS.append({
    "id": "weak-shallow-unwrap",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _A_SCOPE,
        "        -- resolve via ONE wrapper link rather than the end of the chain\n"
        "        match ((obj.inner.getD obj).globalsMap).lookup clsPath with\n"),
    "refinement": (
        "Decoration COMPOSES: a member may carry more than one wrapper, and each "
        "wrapper's defining scope is its own decorator's, not the declaring "
        "class's. Stepping one link reaches another wrapper, whose scope still "
        "lacks the class, so ownership comes out false and a twice-decorated "
        "documented member is deferred rather than included. A real patch that "
        "dereferences one link instead of resolving to the underlying object "
        "handles the singly-decorated member and still fails the moment two "
        "decorators are stacked — so it passes the F2P and does NOT resolve, the "
        "sharpest form of verify-does-not-imply-resolve on this operand. It agrees "
        "with the frozen decision on every input the other three ownership rivals "
        "are refuted at, which is why it needs its own witness at depth 2."),
    "rationale": (
        "REJECTED by arm (1) at a TWO-LINK wrapper chain: the ownership conjunct "
        "resolves through the object at the END of the chain, which declares the "
        "member, so the spec pins the result to `some false`; one step lands on an "
        "intermediate wrapper whose scope is empty and yields `none`. Attacks the "
        "chain-following depth of the ownership conjunct — the `obj` dimension no "
        "other case moves beyond depth 1. If it VERIFIES => SPEC-TOO-WEAK (the "
        "deep chain model would collapse to a single dereference)."),
    "witness": _wit(
        "two-link wrapper chain: only the INNERMOST scope declares the member, so "
        "the spec => some false while one-step unwrapping => none.",
        _CFG_INIT, "class", "__init__", _DEC_DEEP_OWNED, _H_CLSPATH,
        ", PyObj.inner, Option.getD, h"),
})

# (13) Check ownership for "class" only, letting an "exception" member through
# without it. Added by the audit: every shipped witness that reaches the
# ownership branch does so with what="class", so the two kinds the branch admits
# were never separated.
SPEC_TESTS.append({
    "id": "weak-exception-skips-ownership",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_CLSEXC, '    if what == "class" then\n'),
    "refinement": (
        "The two class-like kinds are treated alike throughout: the suite tests "
        "each category against a class AND against an exception subclass "
        "(test_exception_private_doc, test_exception_special_doc and their undoc "
        "twins). Skipping the ownership resolution for one of them means its "
        "inherited members are documented on every subclass — the same regression "
        "the ownership test exists to stop, just restricted to one kind. A real "
        "patch narrowing the resolution to a single kind does NOT resolve."),
    "rationale": (
        "REJECTED by arm (1) on the EXCEPTION sub-domain: for a documented owned "
        "exception member with its toggle on `shouldInclude` is true, so the spec "
        "pins `some false`; skipping the resolution leaves the local ownership "
        "boolean false and the rival yields `none`. Attacks the `what` binder "
        "INSIDE the ownership branch — the one value of it no other witness uses. "
        "If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "documented owned EXCEPTION member, init toggle on: spec => some false, "
        "rival => none.",
        _CFG_INIT, "exception", "__init__", _DEC_OWNED, _H_CLSPATH, ", h"),
})

# (14) Drop the not-special exclusion from the private category, so a dunder name
# also counts as private. Added by the audit: the three category predicates are
# defined by mutual exclusion, and no shipped case attacks that structure.
SPEC_TESTS.append({
    "id": "weak-private-overlaps-special",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_PRIVLET,
                    '      let isPrivate := (!isInit) && name.startsWith "_"\n'),
    "refinement": (
        "The three categories partition the names precisely so each toggle "
        "controls its own kind of member: a dunder name begins with an underscore "
        "too, so without the exclusion the private toggle also switches on every "
        "other special member. The suite pins the separation by moving one toggle "
        "at a time and asserting the others stay off, so a real patch whose "
        "private test overlaps the special names documents special members from "
        "the private setting alone and does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): a special-form name is NOT private, so with only the "
        "private toggle on `shouldInclude` is false and the spec pins `none`; the "
        "rival counts the dunder name as private and returns `some false`. Attacks "
        "the DISJOINTNESS of the category predicates, and is the only case that "
        "sets incPrivate on. Conditioned on the well-founded string predicates "
        "behind the two tests; the hypotheses state only what that name does and "
        "are jointly satisfiable. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "special-form name with ONLY the private toggle on: spec => none "
        "(it is special, not private), rival => some false.",
        _CFG_PRIV, "module", "__special__",
        '(PyObj.node "m.__special__" true [] none)',
        '(h1 : "__special__".startsWith "__" = true)\n'
        '    (h2 : "__special__".endsWith "__" = true)\n'
        '    (h3 : "__special__".startsWith "_" = true)', ", h1, h2, h3"),
})

# (15) The SPECIAL category fires regardless of its toggle. Added by the audit:
# (7) and (8) cover the init and private toggles, leaving the third — the one the
# F2P itself exercises — with no toggle-ignoring rival of its own.
SPEC_TESTS.append({
    "id": "weak-ignore-special-toggle",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _A_CAT,
        '      if isSpecial || (isPrivate && cfg.incPrivate) ||\n'
        '         (isInit && cfg.incInit) then\n'),
    "refinement": (
        "The special counterpart of the init- and private-toggle rivals, and the "
        "category the F2P itself runs under. Every skip test asserts inclusion "
        "with its config value on and then sets it back to False and asserts "
        "deferral; a patch honouring the special category unconditionally fails "
        "that second assertion on every special case, class, exception and module "
        "alike, so it does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): with every toggle off the spec pins a documented "
        "special member to `none`, but the rival returns `some false`. Attacks the "
        "category conjunct through the SPECIAL toggle — the third independent "
        "toggle, which the init- and private-toggle rivals leave untested. "
        "Conditioned on the well-founded string predicates behind that test; the "
        "hypotheses are jointly satisfiable. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "special member with every toggle off: spec => none, rival => some false.",
        _CFG_OFF, "module", "__special__",
        '(PyObj.node "m.__special__" true [] none)',
        '(h1 : "__special__".startsWith "__" = true)\n'
        '    (h2 : "__special__".endsWith "__" = true)', ", h1, h2"),
})

# (16) PARTIAL DOMAIN, the private mirror of (9): drop the private disjunct while
# keeping special and init. Added by the audit — (9) drops two disjuncts at once
# and is refuted on the special sub-domain, so no shipped case is refuted where a
# member must be included BECAUSE the private toggle is on.
SPEC_TESTS.append({
    "id": "weak-drop-private-disjunct",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _A_CAT,
        '      if (isSpecial && cfg.incSpecial) || (isInit && cfg.incInit) then\n'),
    "refinement": (
        "Correct on the init and special categories and wrong on the private one: "
        "a documented private member with its own toggle ON is deferred instead of "
        "included. A real patch with this body fails the inclusion half of every "
        "private test (test_class_private_doc, test_exception_private_doc, "
        "test_module_private_doc), so it does NOT resolve. Distinct from the "
        "init-only rival, which is refuted on the SPECIAL sub-domain and so leaves "
        "the private disjunct's include direction unprobed."),
    "rationale": (
        "REJECTED by arm (1) on the PRIVATE sub-domain: a documented private "
        "member with the private toggle on makes `shouldInclude` true, so the spec "
        "pins `some false`; the rival returns `none`. The only case that exercises "
        "the private disjunct's include direction — every other private-category "
        "witness has incPrivate OFF and tests the defer direction. Conditioned on "
        "the well-founded string predicates behind that test; the hypotheses are "
        "jointly satisfiable. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "documented private member, private toggle on: spec => some false, "
        "rival => none.",
        _CFG_PRIV, "module", "_helper", '(PyObj.node "m._helper" true [] none)',
        '(h1 : "_helper".startsWith "_" = true)\n'
        '    (h2 : "_helper".startsWith "__" = false)', ", h1, h2"),
})


# (17) Read the DOCSTRING through the underlying object instead of this one.
# Added by the audit: every shipped rival that moves `obj` along its wrapper
# dimension does so inside the OWNERSHIP conjunct, so the battery never asked
# which conjuncts the chain-following applies to. It applies to exactly one —
# ownership — and the docstring conjunct must read the object autodoc actually
# handed over. Refuted where the two disagree.
SPEC_TESTS.append({
    "id": "weak-doc-from-core",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_HASDOC,
                    '  let hasDoc := obj.coreObject.hasDoc\n'),
    "refinement": (
        "The resolution to the underlying object exists to answer ONE question — "
        "which scope declares the owning class — and applying it to the docstring "
        "test as well changes which object's documentation status decides "
        "inclusion. Decoration copies the docstring onto the wrapper, so the two "
        "usually agree and this rival is invisible almost everywhere; where they "
        "disagree it takes its verdict from the wrong object, deferring a member "
        "that is documented as handed over. A real patch that widened the "
        "resolution to this operand too would defer members the suite asserts are "
        "included, so it does NOT resolve."),
    "rationale": (
        "REJECTED by arm (1): the docstring conjunct is about the object as "
        "handed over, which HAS a docstring, so `shouldInclude` is true and the "
        "spec pins `some false`; reading the underlying object's flag instead "
        "yields `none`. Attacks WHICH CONJUNCT the chain-following applies to — a "
        "dimension no other case moves, since every other wrapper-chain rival "
        "edits the ownership resolution. Needs no hypothesis: the module branch "
        "reaches no stuck string predicate. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "wrapper documented, underlying object NOT: spec => some false "
        "(the object handed over carries the docstring), rival => none.",
        _CFG_INIT, "module", "__init__",
        '(PyObj.node "m.__init__" true []\n'
        '      (some (PyObj.node "m.__init__" false [] none)))'),
})

# (18) Take the owning class's SHORT NAME from the underlying object's qualified
# name as well. Added by the audit: the resolution has two halves — which NAME to
# look up, and which SCOPE to look it up in — and every shipped ownership rival
# moves only the scope, so a rival that also moves the name was unattacked.
SPEC_TESTS.append({
    "id": "weak-core-qualname",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _A_CLSPATH,
                    '      match clsPathSingle obj.coreObject.qualname with\n'),
    "refinement": (
        "A NEAR-MISS that agrees with the frozen decision on every input the other "
        "ownership rivals are refuted at: decoration copies the qualified name onto "
        "the wrapper, so wrapper and underlying object normally report the SAME "
        "name and this rival is correct there — including on the decorated-member "
        "point the F2P turns on. It diverges only where the underlying object's own "
        "qualified name differs, i.e. where the wrapped callable was defined "
        "elsewhere and re-exposed as a member: the name looked up is then the "
        "definition site's owner rather than the member's, so the resolution "
        "answers a question about the wrong class. A real patch with this body "
        "passes the F2P and still mis-resolves, so it does NOT resolve."),
    "rationale": (
        "REJECTED by arm (2): the ownership conjunct takes the owner's short name "
        "from the object as handed over, which does not declare the member in the "
        "scope reached, so `shouldInclude` is false and the spec pins `none`; "
        "taking the name from the underlying object finds a class that does "
        "declare it and returns `some false`. Attacks the NAME half of the "
        "ownership resolution — every other ownership rival moves only the scope "
        "half. Conditioned on the two well-founded splits (they do not "
        "kernel-reduce); the hypotheses state only what those names do and are "
        "jointly satisfiable. If it VERIFIES => SPEC-TOO-WEAK."),
    "witness": _wit(
        "wrapper and underlying object report DIFFERENT owners: the spec resolves "
        "the handed-over object's owner, which is absent from the scope reached "
        "(=> none), while taking the underlying object's owner finds a declaring "
        "class (rival => some false).",
        _CFG_INIT, "class", "__init__",
        '(PyObj.node "S.__init__" true []\n'
        '      (some (PyObj.node "T.__init__" true '
        '[("T", ⟨["__init__"]⟩)] none)))',
        '(h : clsPathSingle "S.__init__" = some "S")\n'
        '    (h2 : clsPathSingle "T.__init__" = some "T")',
        ", h, h2, List.lookup"),
})


# The axiom lane belongs to G-AX and this gate ignores it. This bundle has no
# consumed axiom in any case: the resolution of an object to the underlying object
# it wraps is modeled deeply, so it is validated against the real operation rather
# than assumed.
AXIOM_TESTS = []
