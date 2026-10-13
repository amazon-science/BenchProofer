"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8551 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_makeXref`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models a node-building step ``make_field_ref`` over a ``PSeq[int]`` token
carrier and additionally carries a DEEP RESOLVER model (``resolve_count`` /
``resolve_name``) whose facts (nagini P5/P6) are extra postcondition clauses.
This Lean bundle models the SAME single purely-functional core — turning an
info-field type annotation into a cross-reference node that records the
surrounding namespace context — over a ``RefContext`` / ``XrefNode`` structure
carrier, but WITHOUT the resolver: it does not model ``resolve_count`` /
``resolve_name`` at all, so nagini's P5/P6 have no counterpart here. In their
place this carrier models something nagini's did NOT: the leading-sigil
stripping of the reference target (``strippedTarget``). So the clause map is:

  nagini P1 (target identity)   -> C1 here, GENERALIZED to sigil stripping
  nagini P2 (prefer-specific)   -> C0 here (``refspecific = true``)
  nagini P3 (module context)    -> C2 here (``pyModule = ctx.module``)
  nagini P4 (class context)     -> C3 here (``pyClass = ctx.cls``)
  nagini P5/P6 (resolution)     -> NO counterpart (resolver not modeled here)

DEFENDED SURFACE (one modeled behavior; four independent top-level clauses).
``problem_spec_makeXref ctx target result`` pins EXACTLY:

  * (C0 flag)     ``result.refspecific = true`` — scope-aware resolution is
    requested;
  * (C1 target)   ``result.reftarget = strippedTarget target`` — the reference
    target is the annotation name with any leading ``.``/``~`` sigil removed;
  * (C2 module)   ``result.pyModule = ctx.module`` — LOAD-BEARING: the current
    module context is recorded (identity with the input);
  * (C3 class)    ``result.pyClass = ctx.cls`` — LOAD-BEARING: the enclosing
    class context is recorded (identity with the input).

The BEHAVIOURAL DISCRIMINATOR (the fix): the produced node must RECORD the
surrounding (module, class) namespace context. The pre-fix node left that
context absent, so an unqualified name fell to a whole-project fuzzy search that
matched the name in every (sub)module — the spurious ambiguity the issue
reports. The ``weak-drop-module`` / ``weak-drop-class`` rivals below ARE that
pre-fix behavior on each context half.

BINDER STRUCTURE. The spec predicate has THREE input binders: ``ctx.module``
(``Option String``), ``ctx.cls`` (``Option String``), and ``target``
(``String``). All three are load-bearing and all three are VARIED across the
reject witnesses (see the point-spread block at the bottom): ``ctx.module``
takes ``some "example"``, ``some "mod"``, ``none``, ``some "pkg"``,
``some "foo"``, ``none``, ``some "pkg2"``; ``ctx.cls`` takes ``some "Class"``,
``some "Klass"``, ``none``, ``none``, ``some "Bar"``, ``some "Outer"``,
``some "Cls2"``; ``target`` takes ``"str"``, ``"int"``, ``"name"``, ``".Base"``,
``"cls"``, ``"~Alias"``, ``"!Bang"``. The seven reject witnesses probe seven
DISTINCT input tuples (pts=7), and the target values sit on FOUR sides of the
sigil test (no sigil, ``.`` sigil, ``~`` sigil, and a non-sigil leading
punctuation character that must NOT be stripped).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already notes its
    inputs are pure ``PSeq`` value carriers holding NO heap permission, so its
    frame-mutation class is vacuous THERE; on this referentially transparent
    carrier it is doubly so — ``ctx``/``target`` are immutable values, there is
    no ``mut`` input binder, no aliasing, and no read-only cell to overwrite. No
    substitute probe is fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — NOT SHIPPABLE; corrected by audit (a2). The
    earlier text here said a diverging impl "cannot be written at all". That is
    FALSE as written and was measured so: ``partial def implementation_makeXref
    ctx target := implementation_makeXref ctx target`` elaborates, and
    ``variant_scope.variant_problems`` returns EMPTY for it (``partial`` is not
    an assumption token), so such a rival is both writable and in scope. What is
    true is the weaker, measured claim that it cannot be SHIPPED as a reject
    case, for a reason specific to this carrier: a ``partial def`` is compiled
    to an opaque constant with no equation lemmas, so nothing can compute its
    output. Both witness routes were built and both fail:
      - a GROUND witness (the shape all seven shipped witnesses use) cannot get
        off the ground — its ``have hf`` fails on the RIVAL, the half that must
        succeed (measured EXIT=1, ``unfold`` failed to unfold
        ``implementation_makeXref``), so the case records witness-unproven;
      - a HYPOTHESIS-CONDITIONED witness (the technique that makes an opaque
        carrier attackable) elaborates against the rival, but it also elaborates
        against the FROZEN solution — measured EXIT=0 on BOTH — because a
        hypothesis of the form ``(implementation_makeXref ctx t).pyModule ≠ some
        "example"`` is satisfiable-looking on either side and no tactic can
        refute it for gold either. Gold's exit code therefore carries no
        information and the case is witness-vacuous.
    So the disposition is "no shippable case", established by builds rather than
    by the false syntactic claim it replaces. This is NOT a spec hole either:
    the obligation is over the total ``def`` the frozen file declares, and a
    ``partial`` rival does not verify (measured EXIT=1) — it merely cannot be
    refuted BY A WITNESS, which bounds the battery, not the spec. Contrast the
    velvet sibling, whose bundle sets
    ``loom.semantics.termination "total"`` (checked) and where the analogous
    class is therefore genuinely shippable.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: every
    output component is pinned by a structural equation on the actual inputs
    (a Bool literal, the sigil-strip of ``target``, and identity with each half
    of ``ctx``). There is no opaque answer key an implementation could echo —
    recording the context IS doing the work. The nagini sibling reaches the same
    conclusion (its resolver facts are entailed by the field-identity clauses);
    here that entailment is moot because the resolver is not modeled. In its
    place the battery carries honest cheapest-implementation POSITIVE CONTROLS.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: dropping the module context (C2), dropping
    the class context (C3 — correct only on the ``ctx.cls = none`` sub-domain),
    dropping the prefer-specific flag (C0), and (unique to this carrier)
    mishandling the target — leaving the sigil unstripped, pre-qualifying the
    name, honouring only one of the two sigil characters (correct on every
    target except a ``~``-prefixed one), or honouring one character too many
    (correct on every target except one led by a non-sigil punctuation
    character) — all four attacking C1, from both the under- and the over-strip
    side.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that computes the rival's offending output
component with a ``have hf``, instantiates the corresponding postcondition
conjunct, and closes by ``decide``. Four witnesses bind NOTHING in their head
(all inputs are ground literals); the ``no-strip`` and ``tilde-blind`` witnesses
condition on the carrier because ``String.startsWith`` applications do not reduce
under ``decide``/``rfl`` on this workspace, and their hypotheses are TRUE facts
about the literal target (confirmed by ``#eval``) and jointly satisfiable (the
gate's ``False``-from-binders probe does not close). Each witness was checked
with real ``lake env lean`` builds to HOLD of its rival and to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology.

EVERY ``have hf`` REDUCES THE CARRIER BEFORE CLOSING (``simp only [Id.run, bind,
pure]``, then ``rfl``/``split``). This is load-bearing and was an AUDIT REPAIR,
not a style choice: two of these witnesses originally closed hf with a bare
``unfold implementation_makeXref; rfl``, which does not reduce the frozen impl's
``Id.run do`` block, so the frozen-side build failed on a STUCK term rather than
on a value mismatch. Measured: under that form a forgery asserting something TRUE
of the frozen solution also failed on it (and held of the rivals), so the
frozen-side exit code carried no information for those two cases. With the
reduction added, the same forgery now ELABORATES against the frozen solution, so
a frozen-side FAILURE is a genuine refutation. The check that matters for any
future edit here is that one build: state a TRUE claim about the frozen impl using
the witness's own hf tactic and confirm it succeeds.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is
the corresponding omission/rewrite in the node-building step, which on the
reported scenario makes the emitted ``pending_xref`` carry the wrong metadata,
so the F2P assertion (``py:module``/``py:class`` on the node, or its
``reftarget``) mismatches and the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the node-building step is modeled directly); the axiom lane belongs to
G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8551"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The gold impl is a `Id.run do` block of four field updates then a sigil-guarded
# retarget. Each anchor lies wholly inside `-- impl-start`/`-- impl-end`, so every
# rival reshape keeps `same_spec` and the `correct_makeXref` STATEMENT identical.
_I_FLAG = "    result := { result with refspecific := true }"
_I_MOD = "    result := { result with pyModule := ctx.module }"
_I_CLS = "    result := { result with pyClass := ctx.cls }"
_I_SIGIL = ("    if hasSigil target then\n"
            "      result := { result with reftarget := target.drop 1 }")

# The whole gold impl body + the gold proof body, for the positive controls that
# re-shape control flow. Anchored on the full `def`/proof so the swap lands
# entirely inside the impl / proof regions.
_GOLD_IMPL = (
    "def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=\n"
    "  Id.run do\n"
    "    let mut result : XrefNode :=\n"
    "      { reftarget := target, refspecific := false, pyModule := none, pyClass := none }\n"
    "    result := { result with refspecific := true }\n"
    "    result := { result with pyModule := ctx.module }\n"
    "    result := { result with pyClass := ctx.cls }\n"
    "    if hasSigil target then\n"
    "      result := { result with reftarget := target.drop 1 }\n"
    "    return result")

_GOLD_PROOF = (
    "  intro ctx target\n"
    "  unfold problem_spec_makeXref implementation_makeXref strippedTarget\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : hasSigil target <;> simp [h]")

# The frozen proof's first two lines — unique in the file — so the admissibility
# positive can prepend a ground `have` without touching the theorem STATEMENT or
# the spec view.
_P_INTRO = (
    "  intro ctx target\n"
    "  unfold problem_spec_makeXref implementation_makeXref strippedTarget")


# === POSITIVE CONTROL 1 (soundness, expect=verify) =========================
# Structurally-different CORRECT impl: drop the imperative `Id.run do` scaffold
# and build the node with a single direct record literal that sets every field
# to its final value (reftarget = strippedTarget target). Same value on every
# input, so C0..C3 all hold; a simpler proof closes it (`exact ⟨rfl,rfl,rfl,rfl⟩`).
# The `correct_makeXref` STATEMENT is byte-identical; no new axiom/lemma.
_POS1_IMPL = (
    "def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=\n"
    "  { reftarget := strippedTarget target, refspecific := true,\n"
    "    pyModule := ctx.module, pyClass := ctx.cls }")
_POS1_PROOF = (
    "  intro ctx target\n"
    "  unfold problem_spec_makeXref implementation_makeXref\n"
    "  exact ⟨rfl, rfl, rfl, rfl⟩")

# === POSITIVE CONTROL 2 (soundness, expect=verify) =========================
# Reorder the mutable updates: strip the sigil FIRST, then write class, module,
# flag last. Identical final node, different control-flow shape. The frozen proof
# body still closes it unchanged (it unfolds the impl and case-splits on the
# sigil), so no proof authoring is needed; statement byte-identical.
_POS2_IMPL = (
    "def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=\n"
    "  Id.run do\n"
    "    let mut result : XrefNode :=\n"
    "      { reftarget := target, refspecific := false, pyModule := none, pyClass := none }\n"
    "    if hasSigil target then\n"
    "      result := { result with reftarget := target.drop 1 }\n"
    "    result := { result with pyClass := ctx.cls }\n"
    "    result := { result with pyModule := ctx.module }\n"
    "    result := { result with refspecific := true }\n"
    "    return result")

# === ADMISSIBILITY (obligation satisfiable at a normal input, expect=verify) =
# The frozen theorem carries NO precondition, so nagini's precondition-admission
# self-call re-expresses as: discharge the spec predicate by evaluation at the
# concrete F2P scenario (module "example", class "Class", target "str") as a
# `have`, then close the frozen obligation verbatim. Nothing is assumed: no new
# declaration, statement byte-identical, ground instance is a `have` prepended to
# the existing tactic body.
_ADMISS = (
    "  have _ground : problem_spec_makeXref\n"
    "      { module := some \"example\", cls := some \"Class\" } \"str\"\n"
    "      (implementation_makeXref { module := some \"example\", cls := some \"Class\" } \"str\") := by\n"
    "    unfold problem_spec_makeXref implementation_makeXref strippedTarget\n"
    "    simp only [Id.run, bind, pure]\n"
    "    by_cases h : hasSigil \"str\" <;> simp [h]\n"
    + _P_INTRO)


# === UNIQUENESS rivals (must be REJECTED) ==================================

# --- weak-drop-module: THE gold bug (module half). Record no module context
# (pyModule = none). Exactly the prepatch state. FAILS C2 whenever ctx.module is
# present. expect=reject.
_REJ_DROP_MOD = _swap(_BASE, _I_MOD,
                      "    result := { result with pyModule := none }")

# --- weak-drop-class: THE gold bug (class half). Record no class context
# (pyClass = none). FAILS C3 whenever ctx.cls is present. PARTIAL-DOMAIN: correct
# on the ctx.cls = none sub-domain. expect=reject.
_REJ_DROP_CLS = _swap(_BASE, _I_CLS,
                      "    result := { result with pyClass := none }")

# --- weak-drop-flag: do not request scope-aware resolution (refspecific = false).
# FAILS C0. expect=reject.
_REJ_FLAG = _swap(_BASE, _I_FLAG,
                  "    result := { result with refspecific := false }")

# --- weak-no-strip: leave the leading sigil on the reference target (skip the
# strip entirely). FAILS C1 on any sigil-bearing target. expect=reject.
_REJ_NOSTRIP = _swap(_BASE, _I_SIGIL,
                     "    result := { result with reftarget := target }")

# --- weak-pre-qualify-target: "resolve-by-rewriting-the-target". Instead of
# leaving the (stripped) name and recording context, pre-qualify the target to
# module + target. FAILS C1 (the reftarget is the qualified name, not the
# sigil-stripped input). expect=reject.
_REJ_QUALIFY = _swap(
    _BASE, _I_SIGIL,
    "    result := { result with reftarget := (ctx.module.getD \"\") ++ target }")

# --- weak-tilde-blind: strip only a leading `.`, ignore a leading `~`. Attacks
# the DISJUNCTION inside `hasSigil` (`startsWith "." || startsWith "~"`), which
# no other rival moves: weak-no-strip skips the strip wholesale and
# weak-pre-qualify-target overwrites the target regardless of the sigil, so both
# are refuted at a `.`-target and neither distinguishes the two sigil characters.
# FAILS C1 on exactly the `~`-bearing sub-domain (correct on every other target).
# expect=reject.
_REJ_TILDE = _swap(
    _BASE, _I_SIGIL,
    "    if target.startsWith \".\" then\n"
    "      result := { result with reftarget := target.drop 1 }")

# --- weak-overstrip-bang: treat a THIRD leading character (`!`) as a sigil too,
# so a `!`-prefixed name is stripped when the spec says it must be kept whole.
# Attacks the OVER-strip direction of C1, the mirror of weak-tilde-blind's
# under-strip. ADDED BY AUDIT (a2): measured that this rival's node agrees with
# the frozen one at ALL SIX shipped witness points, so every witness in the
# battery elaborated against it unchanged — it was the one impl-level distinction
# the shipped battery could not reach. Correct on every `.`/`~`-prefixed and
# every sigil-free target; wrong exactly on the `!`-prefixed sub-domain.
# expect=reject.
_REJ_OVERSTRIP = _swap(
    _BASE, _I_SIGIL,
    "    if hasSigil target || target.startsWith \"!\" then\n"
    "      result := { result with reftarget := target.drop 1 }")


# ---------------------------------------------------------------------------
# witnesses. Each computes the offending output component of the rival, then
# instantiates the matching postcondition conjunct and closes by `decide`.
# ---------------------------------------------------------------------------
_W_DROP_MOD = (
    "example : ¬ problem_spec_makeXref\n"
    "    { module := some \"example\", cls := some \"Class\" } \"str\"\n"
    "    (implementation_makeXref { module := some \"example\", cls := some \"Class\" } \"str\") := by\n"
    "  have hf : (implementation_makeXref { module := some \"example\", cls := some \"Class\" } \"str\").pyModule = none := by\n"
    "    unfold implementation_makeXref; simp [Id.run]; split <;> rfl\n"
    "  rintro ⟨_, _, h, _⟩\n"
    "  rw [hf] at h\n"
    "  exact absurd h (by decide)")

_W_DROP_CLS = (
    "example : ¬ problem_spec_makeXref\n"
    "    { module := some \"mod\", cls := some \"Klass\" } \"int\"\n"
    "    (implementation_makeXref { module := some \"mod\", cls := some \"Klass\" } \"int\") := by\n"
    "  have hf : (implementation_makeXref { module := some \"mod\", cls := some \"Klass\" } \"int\").pyClass = none := by\n"
    "    unfold implementation_makeXref; simp [Id.run]; split <;> rfl\n"
    "  rintro ⟨_, _, _, h⟩\n"
    "  rw [hf] at h\n"
    "  exact absurd h (by decide)")

_W_FLAG = (
    "example : ¬ problem_spec_makeXref\n"
    "    { module := none, cls := none } \"name\"\n"
    "    (implementation_makeXref { module := none, cls := none } \"name\") := by\n"
    "  have hf : (implementation_makeXref { module := none, cls := none } \"name\").refspecific = false := by\n"
    "    unfold implementation_makeXref; simp [Id.run]; split <;> rfl\n"
    "  rintro ⟨h, _, _, _⟩\n"
    "  rw [hf] at h\n"
    "  exact absurd h (by decide)")

# AUDIT REPAIR (both target-clause witnesses below). These two `have hf` steps
# were originally `unfold implementation_makeXref; rfl`, with no `Id.run`
# reduction. That form does NOT reduce the gold `Id.run do` block: gold's build
# then failed with the whole unreduced `have result := ...; if hasSigil ... then
# ... else ...` term reported as "not definitionally equal", i.e. `rfl` gave up on
# a stuck term rather than on a value mismatch. Measured with real builds: a
# FORGERY asserting something TRUE of gold
#     example : (implementation_makeXref { module := none, cls := none } "x")
#         .refspecific = true := by unfold implementation_makeXref; rfl
# also exits 1 on gold (and 0 on both target rivals), so the gold-side exit code
# carried NO information for these two cases and a non-refutation would have been
# recorded as a refutation. Adding `simp only [Id.run, bind, pure]` before closing
# fixes it: the same forgery now exits 0 on gold, so a gold-side FAILURE is now a
# genuine value mismatch. `all_goals (first | rfl | (split <;> rfl))` closes both
# subjects — 0 goals remain on a straight-line rival, 2 branch goals on gold's
# sigil-guarded block. Re-measured: rival 0 / gold 1 for both, with gold's error
# now a ground value clash (e.g. `".Base".drop 1 ... ≠ ".Base"`).

# Conditions on the carrier: `hasSigil ".Base"` does not reduce under `decide`
# (`decide` gets stuck on `String.startsWith`'s Decidable instance; `rfl`,
# `decide +kernel` and `simp [String.startsWith]` all fail too, though `#eval`
# gives `true`), so the refutation is stated under the single hypothesis that the
# target does bear a sigil — which holds of ".Base" and is jointly satisfiable
# (the gate's `False`-from-binders probe does not close). Under that hypothesis
# strippedTarget ".Base" = "Base", but the rival keeps ".Base".
_W_NOSTRIP = (
    "example (h : hasSigil \".Base\" = true) : ¬ problem_spec_makeXref\n"
    "    { module := some \"pkg\", cls := none } \".Base\"\n"
    "    (implementation_makeXref { module := some \"pkg\", cls := none } \".Base\") := by\n"
    "  have hf : (implementation_makeXref { module := some \"pkg\", cls := none } \".Base\").reftarget = \".Base\" := by\n"
    "    unfold implementation_makeXref\n"
    "    simp only [Id.run, bind, pure]\n"
    "    all_goals (first | rfl | (split <;> rfl))\n"
    "  have hs : strippedTarget \".Base\" = \"Base\" := by\n"
    "    unfold strippedTarget; rw [h]; rfl\n"
    "  rintro ⟨_, hr, _, _⟩\n"
    "  rw [hf, hs] at hr\n"
    "  exact absurd hr (by decide)")

# The rival's reftarget is the qualified name "foocls", which differs from BOTH
# branches of strippedTarget "cls" ("cls" or "cls".drop 1), so a `split` on the
# unreduced sigil test closes both cases by `decide` without conditioning.
_W_QUALIFY = (
    "example : ¬ problem_spec_makeXref\n"
    "    { module := some \"foo\", cls := some \"Bar\" } \"cls\"\n"
    "    (implementation_makeXref { module := some \"foo\", cls := some \"Bar\" } \"cls\") := by\n"
    "  have hf : (implementation_makeXref { module := some \"foo\", cls := some \"Bar\" } \"cls\").reftarget = \"foocls\" := by\n"
    "    unfold implementation_makeXref\n"
    "    simp only [Id.run, bind, pure]\n"
    "    all_goals (first | rfl | (split <;> rfl))\n"
    "  rintro ⟨_, hr, _, _⟩\n"
    "  rw [hf] at hr\n"
    "  unfold strippedTarget at hr\n"
    "  split at hr <;> exact absurd hr (by decide)")

# weak-tilde-blind. Two hypotheses, both TRUE facts about "~Alias" (`#eval` gives
# `hasSigil "~Alias" = true` and `"~Alias".startsWith "." = false`), needed
# because neither `String.startsWith` application reduces under `decide`/`rfl`
# here. They are jointly satisfiable — they describe the SAME string agreeing with
# the `~` disjunct and disagreeing with the `.` disjunct, and the gate's
# `False`-from-binders probe does not close (measured: exit 1,
# "simp_all made no progress").
#
# The `first | (rw [hd]; rfl) | (rw [ht]; rfl)` closes hf on the RIVAL by
# rewriting its `startsWith "."` branch test to `false`; on gold the same idiom
# rewrites the `hasSigil` test to `true`, leaving the genuinely FALSE ground
# equation `"~Alias".drop 1 = "~Alias"` — so gold fails on a VALUE, not a stuck
# term. Verified informative: a forgery claiming gold's true value
# (`reftarget = "Alias"`) under the identical idiom exits 0 on gold and 1 on the
# rival, the exact mirror of this witness.
_W_TILDE = (
    "example (hd : \"~Alias\".startsWith \".\" = false)\n"
    "    (ht : hasSigil \"~Alias\" = true) : ¬ problem_spec_makeXref\n"
    "    { module := none, cls := some \"Outer\" } \"~Alias\"\n"
    "    (implementation_makeXref { module := none, cls := some \"Outer\" } \"~Alias\") := by\n"
    "  have hf : (implementation_makeXref { module := none, cls := some \"Outer\" } \"~Alias\").reftarget = \"~Alias\" := by\n"
    "    unfold implementation_makeXref\n"
    "    simp only [Id.run, bind, pure]\n"
    "    first | (rw [hd]; rfl) | (rw [ht]; rfl)\n"
    "  have hs : strippedTarget \"~Alias\" = \"Alias\" := by\n"
    "    unfold strippedTarget; rw [ht]; rfl\n"
    "  rintro ⟨_, hr, _, _⟩\n"
    "  rw [hf, hs] at hr\n"
    "  exact absurd hr (by decide)")

# weak-overstrip-bang. Conditioned on the carrier for the same measured reason as
# the two witnesses above (`String.startsWith` applications do not reduce under
# `decide`/`rfl`/`decide +kernel`/`simp [String.startsWith]` on this workspace).
# Both hypotheses are TRUE facts about "!Bang", confirmed by `#eval`:
# `hasSigil "!Bang" = false` and `"!Bang".startsWith "!" = true`. They are jointly
# satisfiable — they describe one string disagreeing with BOTH `hasSigil`
# disjuncts while beginning with `!` — and the gate's `False`-from-binders probe
# does not close (measured: exit 1, "simp_all made no progress").
#
# Discrimination measured with real builds: rival EXIT=0, gold EXIT=1, and gold's
# failure is a ground VALUE clash, not a stuck term — `(if false = true then
# "!Bang".drop 1 else "!Bang").reftarget is not definitionally equal to "Bang"`,
# i.e. gold correctly KEEPS the name whole where the rival strips it. Forgery
# check (attack B'): the same claim with the negation dropped elaborates on gold
# (EXIT=0) and fails on the rival (EXIT=1) — the exact mirror — so gold's exit
# code tracks the claim rather than the file.
_W_OVERSTRIP = (
    "example (hb : hasSigil \"!Bang\" = false)\n"
    "    (hx : \"!Bang\".startsWith \"!\" = true) : ¬ problem_spec_makeXref\n"
    "    { module := some \"pkg2\", cls := some \"Cls2\" } \"!Bang\"\n"
    "    (implementation_makeXref { module := some \"pkg2\", cls := some \"Cls2\" } \"!Bang\") := by\n"
    "  have hf : (implementation_makeXref { module := some \"pkg2\", cls := some \"Cls2\" } \"!Bang\").reftarget = \"Bang\" := by\n"
    "    unfold implementation_makeXref\n"
    "    simp only [Id.run, bind, pure]\n"
    "    first | (rw [hb, hx]; rfl) | (rw [hb]; rfl)\n"
    "  have hs : strippedTarget \"!Bang\" = \"!Bang\" := by\n"
    "    unfold strippedTarget; rw [hb]; simp\n"
    "  rintro ⟨_, hr, _, _⟩\n"
    "  rw [hf, hs] at hr\n"
    "  exact absurd hr (by decide)")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_makeXref` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        "module": _BASE.replace(_GOLD_IMPL, _POS1_IMPL, 1)
                       .replace(_GOLD_PROOF, _POS1_PROOF, 1),
        "rationale": "structurally-different but correct: drop the imperative "
                     "`Id.run do` scaffold and set every field to its final value "
                     "in one record literal (reftarget = strippedTarget target). "
                     "Same node on every input, so C0..C3 all hold — else "
                     "SPEC-TOO-STRONG. Re-proved by `exact ⟨rfl,rfl,rfl,rfl⟩` "
                     "(statement byte-identical, no new axiom/lemma). Ports "
                     "nagini's pos-local-reshape (a value-preserving reshape of "
                     "the same node construction).",
    },
    {
        "id": "pos-reorder-updates",
        "kind": "soundness",
        "expect": "verify",
        "module": _BASE.replace(_GOLD_IMPL, _POS2_IMPL, 1),
        "rationale": "control-flow reshape: strip the sigil first, then write "
                     "class, module and the flag last. Identical final node, "
                     "different statement order. A faithful reshape MUST verify, "
                     "else SPEC-TOO-STRONG; the frozen proof body closes it "
                     "unchanged (it unfolds the impl and case-splits on the "
                     "sigil). Statement byte-identical, no new axiom/lemma. Ports "
                     "nagini's pos-explicit-resolve-asserts as a value-identical "
                     "reshape — the nagini positive added redundant Asserts of the "
                     "RESOLUTION facts P5/P6, which this carrier does not model "
                     "(no resolver), so the analogous 'same value, extra shape' "
                     "positive reorders the writes instead.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at a normal, F2P-shaped input.
    # =====================================================================
    {
        "id": "admiss-f2p-scenario",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS),
        "rationale": "the spec predicate is discharged at the concrete F2P "
                     "scenario (current module \"example\", enclosing class "
                     "\"Class\", annotation target \"str\") by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable "
                     "at exactly a normal F2P input — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new declaration, "
                     "statement byte-identical, the ground instance is a `have` in "
                     "the existing tactic body. Ports nagini's "
                     "admiss-issue-scenario (there a self-call whose precondition "
                     "is discharged; here the frozen theorem has no precondition, "
                     "so the honest analogue discharges the postcondition at the "
                     "F2P input).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-drop-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DROP_MOD,
        "refinement": "the faithful real patch is the node-building step that "
                      "records no current-module context (the prepatch state). "
                      "The later resolution step then receives no module to search "
                      "within, skips the module-qualified lookup, and falls to a "
                      "whole-project fuzzy match that finds the unqualified name in "
                      "every (sub)module — the reported spurious ambiguity. The F2P "
                      "asserts the produced node carries py:module=\"example\"; with "
                      "the module context dropped that attribute is absent and the "
                      "assertion FAILS. So a verifying drop-module rival would be a "
                      "true verify-not-resolve break.",
        "rationale": "REJECT from C2 (module): the spec pins "
                     "`result.pyModule = ctx.module` but the rival emits `none`, "
                     "which differ whenever ctx.module is present. Refuted at "
                     "ctx.module = some \"example\", ctx.cls = some \"Class\", "
                     "target \"str\". If it verifies => SPEC-TOO-WEAK.",
        "witness": _W_DROP_MOD,
    },
    {
        "id": "weak-drop-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_DROP_CLS,
        "refinement": "the faithful real patch records no enclosing-class context. "
                      "The F2P scenario is under a current class and asserts the "
                      "produced node carries py:class=\"Class\"; with the class "
                      "context dropped that attribute is absent and the assertion "
                      "FAILS. (Correct only on the ctx.cls-is-none sub-domain; the "
                      "F2P exercises a present class.) A verifying drop-class rival "
                      "would be verify-not-resolve.",
        "rationale": "PARTIAL-DOMAIN: REJECT from C3 (class): the spec pins "
                     "`result.pyClass = ctx.cls` but the rival emits `none`, "
                     "differing whenever ctx.cls is present. Refuted at "
                     "ctx.cls = some \"Klass\" (with ctx.module = some \"mod\", "
                     "target \"int\" — a distinct point). If it verifies => "
                     "SPEC-TOO-WEAK.",
        "witness": _W_DROP_CLS,
    },
    {
        "id": "weak-drop-specific-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_FLAG,
        "refinement": "a patch that does not request scope-aware resolution leaves "
                      "the node without the specific-resolution marker, so the "
                      "resolution step runs in the non-specific mode and the "
                      "prefer-current-scope module/class cascade never runs; the "
                      "unqualified name does not resolve to the contextual object. "
                      "The F2P's expected single contextual resolution does not "
                      "occur, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0 (flag): the spec pins "
                     "`result.refspecific = true` but the rival emits `false`. "
                     "Refuted at ctx.module = none, ctx.cls = none, target "
                     "\"name\" (the only witness with both context halves absent, "
                     "isolating the flag). If it verifies => SPEC-TOO-WEAK.",
        "witness": _W_FLAG,
    },
    {
        "id": "weak-no-strip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NOSTRIP,
        "refinement": "a patch that omits stripping the leading `.`/`~` sigil "
                      "leaves the reference target as the raw annotation text. The "
                      "sigil is a display/lookup directive, not part of the name, "
                      "so the resolution step then searches for a name that begins "
                      "with a sigil character and finds nothing. The produced node's "
                      "reftarget attribute is the un-stripped string rather than the "
                      "bare name the test expects, so the faithful patch would NOT "
                      "resolve. (This clause has no nagini counterpart — the sigil "
                      "strip is modeled only on this carrier; see assessment.)",
        "rationale": "REJECT from C1 (target): the spec pins "
                     "`result.reftarget = strippedTarget target` but the rival "
                     "emits the raw `target`, differing on any sigil-bearing name. "
                     "Refuted at target \".Base\" (with ctx.module = some \"pkg\", "
                     "ctx.cls = none); the witness conditions on hasSigil \".Base\" "
                     "= true (jointly satisfiable — `.Base` does begin with `.`) "
                     "because String.startsWith does not reduce under `decide`. If "
                     "it verifies => SPEC-TOO-WEAK.",
        "witness": _W_NOSTRIP,
    },
    {
        "id": "weak-pre-qualify-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_QUALIFY,
        "refinement": "an alternative 'fix' that rewrites the reference target to "
                      "the fully-qualified module + name (instead of recording the "
                      "context and leaving the bare name) changes the observable "
                      "node: the F2P asserts the node keeps the ORIGINAL "
                      "(sigil-stripped) reftarget AND separately carries the module "
                      "context; a rewritten reftarget fails that assertion (and "
                      "breaks every other unqualified reference that legitimately "
                      "resolves within scope). So the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 (target): the spec pins "
                     "`result.reftarget = strippedTarget target` but the rival "
                     "emits `ctx.module.getD \"\" ++ target`, a different string. "
                     "Refuted at ctx.module = some \"foo\", ctx.cls = some \"Bar\", "
                     "target \"cls\" (reftarget \"foocls\" ≠ either strip branch); "
                     "the witness `split`s the unreduced sigil test and refutes "
                     "both branches by `decide`. If it verifies => SPEC-TOO-WEAK.",
        "witness": _W_QUALIFY,
    },
    {
        "id": "weak-tilde-blind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_TILDE,
        "refinement": "the faithful real patch handles only ONE of the two sigil "
                      "characters — it strips a leading `.` but leaves a leading "
                      "`~` in place. Both characters are display/lookup directives "
                      "rather than part of the name, so on a `~`-prefixed "
                      "annotation the produced node's reference target retains the "
                      "sigil character and the resolution step searches for a name "
                      "that begins with it, finding nothing. The produced node's "
                      "reftarget attribute is then the un-stripped string rather "
                      "than the bare name, so the faithful patch would NOT resolve "
                      "an annotation written with that sigil. ADDED BY AUDIT: this "
                      "is the one clause-level distinction the shipped battery left "
                      "unattacked (see rationale).",
        "rationale": "PARTIAL-DOMAIN: REJECT from C1 (target), attacking the "
                     "DISJUNCTION inside `hasSigil` rather than the strip as a "
                     "whole. Correct on every `.`-prefixed and every sigil-free "
                     "target; wrong exactly on the `~`-prefixed sub-domain. This "
                     "point is unreachable by the two existing C1 rivals: "
                     "weak-no-strip omits the strip entirely and "
                     "weak-pre-qualify-target overwrites the target regardless of "
                     "sigil, so both are already refuted at a `.`-target and "
                     "neither separates the two sigil characters — a rival blind to "
                     "`~` alone survives every other witness in this battery. "
                     "Refuted at target \"~Alias\" (ctx.module = none, ctx.cls = "
                     "some \"Outer\" — a sixth distinct input tuple, and the only "
                     "one pairing an absent module with a present class). If it "
                     "verifies => SPEC-TOO-WEAK.",
        "witness": _W_TILDE,
    },
    {
        "id": "weak-overstrip-bang",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_OVERSTRIP,
        "refinement": "the faithful real patch treats one MORE leading character "
                      "as a sigil than the annotation syntax defines, stripping "
                      "the first character off a name that legitimately begins "
                      "with it. Only `.` and `~` are display/lookup directives; "
                      "any other leading character is part of the name itself. So "
                      "on such an annotation the produced node's reference target "
                      "has lost its first character, and the resolution step "
                      "searches for a truncated name that no registered object "
                      "carries, finding nothing. The F2P asserts the node's "
                      "reftarget is the annotation name with only a genuine sigil "
                      "removed; a truncated target fails that assertion, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: REJECT from C1 (target), attacking the "
                     "OVER-strip direction — the mirror of weak-tilde-blind's "
                     "under-strip. The spec pins "
                     "`result.reftarget = strippedTarget target`, which keeps a "
                     "name whole unless it begins with `.` or `~`; the rival also "
                     "strips a leading `!`. Correct on every `.`-prefixed, every "
                     "`~`-prefixed and every sigil-free target; wrong exactly on "
                     "the `!`-prefixed sub-domain. ADDED BY AUDIT (a2) because it "
                     "was measurably unreachable: this rival's node agrees with "
                     "the frozen one at ALL SIX other witness points, so every "
                     "other witness in this battery elaborates against it "
                     "unchanged and it survived the shipped battery intact. "
                     "Refuted at target \"!Bang\" (ctx.module = some \"pkg2\", "
                     "ctx.cls = some \"Cls2\" — a seventh distinct input tuple). "
                     "If it verifies => SPEC-TOO-WEAK.",
        "witness": _W_OVERSTRIP,
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus an EMPTY AXIOM lane. This
# bundle models the SAME single purely-functional core (the info-field xref
# node-building step) but over a structure carrier that DROPS the nagini resolver
# model (P5/P6 have no counterpart) and ADDS a sigil-stripping clause (C1). Every
# sibling case is recorded below.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-local-reshape            -> pos-direct-construct       RE-EXPRESSED
#   pos-explicit-resolve-asserts -> pos-reorder-updates        RE-EXPRESSED
#   admiss-issue-scenario        -> admiss-f2p-scenario        RE-EXPRESSED
#   weak-drop-module             -> weak-drop-module           PORTED
#   weak-drop-class              -> weak-drop-class            PORTED
#   weak-drop-specific-flag      -> weak-drop-specific-flag    PORTED
#   weak-pre-qualify-target      -> weak-pre-qualify-target    PORTED
#   (none)                       -> weak-no-strip              ADDED (attacks C1)
#   (none)                       -> weak-tilde-blind           ADDED BY AUDIT (C1)
#   (none)                       -> weak-overstrip-bang        ADDED BY AUDIT a2 (C1)
#   AXIOM_TESTS (0)              -> (none)                     DROPPED (G-AX)
#
# RE-EXPRESSED (pos-reorder-updates): the sibling's second positive adds redundant
#   Asserts of the RESOLUTION facts P5/P6 (that the recorded context resolves to a
#   single, correctly-named object). This carrier models NO resolver — resolve_count
#   / resolve_name and the P5/P6 clauses have no counterpart — so there is no
#   resolution fact to make explicit. The honest analogue keeping "same value,
#   different shape" reorders the mutable field writes; it verifies under the
#   frozen proof unchanged.
# RE-EXPRESSED (admiss-f2p-scenario): the sibling self-calls make_field_ref on a
#   concrete witness and discharges the CALL'S precondition. The frozen theorem
#   here carries no precondition, so the honest analogue discharges the
#   POSTCONDITION at the concrete F2P scenario as a `have`, proving the modeled
#   behavior is satisfiable at a normal input, then closes the frozen obligation
#   verbatim.
# ADDED (weak-no-strip): the sibling models the target as an opaque token and its
#   P1 is a plain identity (Result().target is target); it has no sigil-stripping
#   behavior to attack. This carrier models strippedTarget, so C1 is
#   `reftarget = strippedTarget target` — a compound clause with its own failure
#   mode (leave the sigil on). weak-no-strip attacks exactly that, a real
#   load-bearing conjunct of the SAME modeled spec, not a fabricated behavior.
# VACUOUS (frame/permission mutation): the sibling itself notes this class is
#   vacuous on its pure PSeq carrier (no heap permission to overwrite); on this
#   referentially transparent carrier it is doubly vacuous — no `mut` input, no
#   aliasing, no read-only cell. No substitute probe is fabricated.
# VACUOUS (divergence / non-termination): on lean implementation_makeXref is a
#   total `def`, so a diverging impl cannot be written; genuinely vacuous, not a
#   spec hole. (The sibling carries no diverge-* case either.)
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT tuples (pts=7):
#   (module, cls, target) =
#     (some "example", some "Class", "str")    weak-drop-module         C2
#     (some "mod",     some "Klass", "int")    weak-drop-class          C3
#     (none,           none,         "name")   weak-drop-specific-flag  C0
#     (some "pkg",     none,         ".Base")  weak-no-strip            C1
#     (some "foo",     some "Bar",   "cls")    weak-pre-qualify-target  C1
#     (none,           some "Outer", "~Alias") weak-tilde-blind         C1
#     (some "pkg2",    some "Cls2",  "!Bang")  weak-overstrip-bang      C1
#   Across them ctx.module ranges over {some "example", some "mod", none,
#   some "pkg", some "foo", some "pkg2"}, ctx.cls over {some "Class",
#   some "Klass", none, some "Bar", some "Outer", some "Cls2"}, target over
#   {"str","int","name",".Base","cls","~Alias","!Bang"} — every input binder is
#   moved, and all four postcondition clauses C0..C3 are attacked. The variation
#   is MEANINGFUL rather than two spellings of one point: each Option binder
#   takes both `some` and `none` (and the two present/absent COMBINATIONS are
#   covered in both directions — (none, some) by weak-tilde-blind and
#   (some, none) by weak-no-strip), and the target values sit on FOUR sides of
#   the sigil test (no sigil, `.` sigil, `~` sigil, and a leading non-sigil
#   punctuation character), which is exactly what weak-tilde-blind and
#   weak-overstrip-bang need to be refutable at all — they are the under- and
#   over-strip halves of the same `hasSigil` boundary.
#
# WITNESS REACHABILITY (measured, audit a2). The point spread is not merely
# distinct-looking: for each reject case the OTHER witnesses were checked against
# its rival by evaluating both nodes at all seven tuples. weak-overstrip-bang was
# added because its rival agrees with the frozen impl at all six other points, so
# no other witness discriminates it — it is reachable only from a `!`-prefixed
# target. (The reverse also holds: no shipped witness is redundant, since each
# case's own point is one where its rival is the one that deviates.)
#
# AUDIT NOTE (attack D, spec strength). Four NEW wrong impls the battery did not
# contain were written and built against the frozen spec; all four were REJECTED,
# so no spec hole was found. They were: strip only `.` (which became
# weak-tilde-blind above); SWAP the two context halves (pyModule := ctx.cls and
# vice versa — nothing in the battery crossed the two halves, and the spec catches
# it); strip unconditionally (wrong on sigil-free names); and normalise an absent
# module to `some ""` (wrong exactly at ctx.module = none). The last two are worth
# recording because they confirm C1 and C2 are pinned as EQUATIONS on the input
# rather than merely "some string" / "some Option".
#
# AUDIT NOTE (attack E, spec soundness). Three NEW correct reshapes were built and
# all three VERIFIED, so the spec is not too strong on this carrier: two full
# record literals under a `match hasSigil target`; the sigil test INLINED so
# neither `hasSigil` nor `strippedTarget` is named in the impl at all; and the node
# built by `List.foldl` over a list of field-update functions. Together with the
# two shipped positives that is five independent correct shapes the spec admits.
#
# AUDIT NOTE a2 (independent re-derivation; all builds re-run, none inherited).
# Attack D, six further NEW wrong impls, all REJECTED (EXIT=1), so still no spec
# hole: over-strip a `!` (promoted to weak-overstrip-bang above); strip `drop 2`
# instead of `drop 1`, attacking the strip's MAGNITUDE, which no other rival
# moves; swap the two context halves; normalise an absent module to `some ""`;
# make the flag conditional on the module being present (`refspecific :=
# ctx.module.isSome`), a partial-domain attack on C0 where the battery only
# dropped the flag wholesale; and fall the class context back to the module when
# no class is in force (`ctx.cls.orElse ctx.module`), wrong exactly at
# cls=none & module=some. Each was scope-checked (variant_problems empty) before
# building, and each was tried under a kitchen-sink proof (rfl / simp_all / aesop
# / decide / split, plus the frozen script) so the rejection is not an artifact of
# reusing a tactic tuned to the frozen form.
#
# Attack E, four further correct reshapes, all VERIFIED (EXIT=0): the context
# routed through a REBUILT RefContext with the halves swapped and swapped back
# (so the impl never names ctx.module/ctx.cls in the field positions the spec
# does); the node built by a NEW top-level helper `def` taking the context as a
# tuple (admissible — variant_scope bans a new theorem/lemma, not a new def);
# the `match`-on-inlined-startsWith shape; and the `List.foldl` shape. Two of
# these initially failed and the failures were MINE, not the spec's — a helper
# declared after its use ("Unknown identifier"), and closing with `rfl` where
# `simp only [List.foldl]` had already reduced the conjuncts to `True` (the
# `has type True` signature). Both verified once corrected, which is the reason
# to record them: an E failure is a spec hole only after the proof is ruled out.
#
# CONDITIONING RE-CHECKED (audit a2). The two conditioned witnesses' reliance on
# hypotheses was re-measured, since "the tactic I need is unavailable" is the
# reason most often wrong. `hasSigil ".Base" = true` fails under `decide` (the
# Decidable instance "did not reduce to isTrue or isFalse"), `decide +kernel`,
# `rfl`, `simp [hasSigil]`, `simp [hasSigil, String.startsWith]`,
# `unfold hasSigil; simp`, `norm_num [hasSigil]` and a `by_cases` on the inner
# `startsWith` — eight tactics, all EXIT=1 — while `#eval` returns `true`. So the
# conditioning is forced by the carrier, not chosen for convenience. Every
# hypothesis was separately confirmed a TRUE fact by `#eval`: hasSigil ".Base" =
# true, hasSigil "~Alias" = true, "~Alias".startsWith "." = false,
# hasSigil "!Bang" = false, "!Bang".startsWith "!" = true.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the node-building step is modeled directly), so there is nothing to probe
# and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
