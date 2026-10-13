# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8548 (lean lane).
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
#   gatherMemberDocs (mro : List ClassInfo)
#     (initial : List MemberEntry) → List MemberEntry
#   A class's member attributes are collected by walking its inheritance chain,
#   most-derived first, folding into a running member table that starts from
#   `initial` (the members the earlier collection passes already found). Each class on
#   the chain contributes through TWO sources, consulted together while that class is
#   visited: the names it declares by annotation alone (which carry NO documentation)
#   and the attributes recorded under its own namespace (which carry a docstring). The
#   single postcondition `problem_spec_gatherMemberDocs mro initial result` pins
#     result = gatherMemberDocs mro initial
#   a total, transparent fold over the inputs — no opaque callee and no answer-key
#   (the "oracle" IS the grounded fold, so echoing it is the cheapest CORRECT impl,
#   used as a positive control). Though stated as one equality, the fold has several
#   INDEPENDENT load-bearing behaviours, each separately attackable:
#     (B1) WHOLE-CHAIN: every class in `mro` is consulted for documented attributes,
#          not just its head — this is what lets an attribute documented only for a
#          base class be collected.
#     (B2) OWNERSHIP FILTER: a recorded attribute is folded in for a chain member
#          only when its recorded namespace matches THAT member's own namespace key
#          (`entry.fst = cls.nsKey`).
#     (B3) FIRST-OCCURRENCE-WINS: a name already present in the table is not
#          overwritten (`… ∉ members.map MemberEntry.name`), tested against the GROWING table.
#     (B4) PAYLOAD: the value stored under a collected documented name is its own
#          docstring (`some entry.snd.snd`), not some other field.
#     (B5) PRECEDENCE / ORDER: the chain is walked most-derived-first, so for a name
#          supplied further down the hierarchy the most-derived occurrence wins.
#     (B6) SEEDING: the walk starts from `initial`; the members found by the earlier
#          passes are preserved and participate in the first-occurrence guard.
#     (B7) TABLE ORDER: the table grows at the TAIL (`members ++ [entry]`), so the
#          seeded members precede the collected ones and each class's records appear
#          in the order they were recorded.
#     (B8) PER-CLASS INTERLEAVING OF THE TWO SOURCES: the chain is walked ONCE and
#          each class's annotation-declared names and own recorded attributes are
#          folded in together, that class's annotations first, before moving to the
#          next class. This is the clause that settles a name supplied by one class
#          through one source and by another class through the other: the class nearer
#          the front of the chain wins. Pinned by `weak-flatten-annotations` (the two
#          sources as two separate chain walks) and, WITHIN a class, by
#          `weak-docs-before-annotations`. Added by panel repair — a faithfulness
#          review found an earlier revision of this bundle had flattened the
#          annotation source into `initial` up-front, which predicts NO documentation
#          for a member the real callee documents.
#     (B9) THE ANNOTATION PAYLOAD IS AN ABSENCE: a member contributed by the
#          annotation source is recorded as `none` (no documentation), which the
#          carrier deliberately distinguishes from `some ""` (a documented attribute
#          whose recorded docstring is empty — a real, reachable case). Pinned by
#          `weak-annotation-payload`.
#    (B10) THE ANNOTATION SOURCE CONTRIBUTES AT ALL: a name a class declares by
#          annotation and never documents still becomes a member. Pinned by
#          `weak-drop-annotations`.
#    (B11) THE SUPPLYING CLASS IS RECORDED, AND IT IS THE CLASS BEING VISITED:
#          every entry either source contributes carries `owner := some
#          cls.classKey` — the IDENTITY of the chain member being walked, not the
#          head of the chain and not that member's namespace KEY. Added by panel
#          repair: the recorded break was a rival that made every collection
#          decision, payload and order clause correctly and credited each collected
#          documented attribute to the HEAD of the chain; the earlier carrier
#          projected the supplier away, so that rival verified while its faithful
#          patch broke the assertion that a class lists only the members it supplies
#          itself. Split into five separately attackable readings, since each admits
#          a rival the others agree with:
#            B11a `weak-doc-owner-target`      — documented attributes credited to the head
#            B11b `weak-annotation-owner-target` — declared names credited to the head
#            B11c `weak-owner-is-key`          — the namespace KEY recorded as the identity
#            B11d `weak-owner-dropped`         — no supplier recorded at all
#            B11e `weak-owner-first-matching-key` — the FIRST chain class carrying the
#                 matching namespace key credited, rather than the one being visited
#                 (the residual freedom the repair itself leaves: it agrees with the
#                 spec unless two classes on one chain share a qualified name)
#   The carrier is fully transparent (String / Option / List / structure literals), so
#   every witness reduces by `decide` at concrete literal inputs — no conditioning
#   needed (verified: every reject case's `decide` closes on the rival and the same
#   `decide` REFUTES the negation on the frozen solution, so each gold-side exit code
#   tracks the claim rather than a tactic mismatch).
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled the resolver as an
# int-coded MRO/record-table fold (`resolve_from` / `lookup_owner_doc`) returning a
# single resolved doc code, under fractional read permissions on four parallel
# list inputs. This backend models the collection pass DIRECTLY over its natural
# carrier: an association list `List MemberEntry` threaded through a
# `List ClassInfo` chain. So nagini's partial-domain rivals port onto the behaviours
# above — its `_PARTIAL_OWN_ONLY` (match only the subject's own owner) becomes B1's
# head-only rival; its `_PARTIAL_LATEST` (precedence inversion) becomes B5's
# reversed-chain rival; its `_PARTIAL_GLOBAL_FIRST` (wrong precedence SOURCE: the
# first record in table order whose namespace is anywhere on the chain) ports
# SEPARATELY as `weak-foreign-ownership-source` (B2b). That one is NOT subsumed by
# the B2 rival: it still performs an ownership test, merely keyed on the whole chain
# instead of THIS member, so it AGREES with the spec at B2's witness input and needs
# its own discriminating point (a member whose own record table also carries a
# base-namespace record for the same name, listed first). The richer structural
# carrier ADDITIONALLY exposes B2 (ownership filter), B3 (dedup), B4 (docstring
# payload), B6 (initial seeding) and the two-source clauses B8/B9/B10 — attackable
# clauses the int-coded nagini carrier folded away, so this port carries MORE reject
# cases than nagini, each at a DISTINCT input point so every spec binder is exercised.
#
# The rivals attacking a DOCUMENTED-attribute clause keep the per-class annotation
# step byte-identical (spliced from one shared `_ANN_STEP` constant), so each one
# isolates exactly the behaviour its id names and none of them accidentally diverges
# through B8 as well.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `_FRAME_MUT_ENS` / `_FRAME_MUT_MRO`: an
#     input held at Acc(list_pred(x),1/2) was WRITTEN back to fabricate a
#     resolution). Lean is referentially transparent — no aliasing, no fractional
#     permission — so a "store into a read-only input" rival is not expressible and
#     that lane is VACUOUS here. The FRAME DISCIPLINE it protected (an unchanged
#     input must survive into the result) IS still tested: `weak-drop-initial` (B6)
#     is the lean analogue — a rival that discards the seeded `initial` table.
#   * DIVERGENCE / NON-TERMINATION. This bundle sets no
#     `loom.semantics.termination` option: `implementation_gatherMemberDocs` is an
#     ordinary total Lean `def`, so the verifier discharges a termination obligation
#     and a diverging rival is genuinely REJECTED rather than vacuously accepted.
#     MEASURED with real builds rather than assumed: a self-recursive rival with no
#     decreasing measure (`… (cls :: rest) (addEntries …)`) is rejected at the
#     DEFINITION — `fail to show termination for implementation_gatherMemberDocs …
#     failed to infer structural recursion` — so the file carrying it does not
#     elaborate at all, and a witness against it fails too (`Tactic 'unfold' failed
#     to unfold implementation_gatherMemberDocs`). Routing around the measure with
#     `partial def` fares the same way: the variant is in scope (variant_scope
#     bans no `partial`), but `partial` compiles to an opaque constant, so BOTH the
#     rival's own build and its witness fail with that same unfold error — the
#     rejection is a definitional-opacity artifact, not a refutation, and no witness
#     can discriminate it. So the class is genuinely VACUOUS on this carrier: there
#     is no diverging impl the spec accepts, hence nothing shippable in the reject
#     lane. The nagini sibling carried no such case either.
#   * AXIOM_TESTS (nagini's `aref-resolve-from-soundness`). The axiom lane is G-AX's
#     job; this gate ignores it. The collection logic is modeled DEEPLY
#     (gatherMemberDocs / addAnnotations / addEntries over the bijected ClassInfo
#     chain), so there is no consumed axiom here anyway.
#
# ADMISSIBILITY, re-derived (this lane WAS dropped by the port and is now restored):
#   nagini's `_ADMISS` defended the half-permission Requires at the F2P-shaped input.
#   The port dropped the lane reasoning that the lean obligation carries NO
#   precondition hypothesis, so nothing could be PRECOND-TOO-STRONG. That reason is
#   not sufficient: on a TOTAL carrier the analogue of PRECOND-TOO-STRONG is the
#   obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a positive
#   that discharges `problem_spec …` at that concrete input BY EVALUATION — as a
#   `have`, before closing the frozen obligation verbatim — tests directly. That is
#   `admiss-ground-f2p-chain` below, and it is not subsumed by the reject witnesses:
#   those state a NEGATIVE (`¬ problem_spec …`) about a RIVAL, so none of them ever
#   shows the frozen obligation is satisfiable anywhere, let alone at the shape the
#   F2P exercises.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8548"

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
    "def implementation_gatherMemberDocs\n"
    "    (mro : List ClassInfo) (initial : List MemberEntry) :\n"
    "    List MemberEntry := Id.run do\n"
    "  let mut members := initial\n"
    "  for cls in mro do\n"
    "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨name, none, some cls.classKey⟩]\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (the tactic lines inside proof-start/proof-end that close
# `correct_gatherMemberDocs`). Swapped only by the positives whose different impl
# shape needs an (equally cheap, honest) reproof of the byte-identical statement.
_PROOF = (
    "  intro mro initial\n"
    "  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs\n"
    "  exact outer_helper mro initial"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

_SIG = (
    "def implementation_gatherMemberDocs\n"
    "    (mro : List ClassInfo) (initial : List MemberEntry) :\n"
    "    List MemberEntry := Id.run do\n"
)

# The per-class annotation step, verbatim from the frozen impl. Rivals that attack a
# DOCUMENTED-attribute clause keep this byte-identical so the divergence they carry is
# the one their id names.
_ANN_STEP = (
    "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨name, none, some cls.classKey⟩]\n"
)
assert _BASE.count(_ANN_STEP) == 1, "annotation-step anchor drifted"

# The per-class documented-attribute step, verbatim from the frozen impl. The mirror
# image of _ANN_STEP: a rival attacking an ANNOTATION clause keeps this byte-identical.
_DOC_STEP = (
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
)
assert _BASE.count(_DOC_STEP) == 1, "documented-attribute-step anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-grounded-echo: the postcondition equates the result to the grounded fold
# `gatherMemberDocs mro initial`, which is total and transparent, so the cheapest
# CORRECT impl echoes it. The theorem STATEMENT is byte-identical; its proof is the
# one-liner `rfl` (definitional). No new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG. Doubles as proof that the oracle is grounded (not an opaque
# answer-key), so no WRONG echo exists.
_POS_ECHO = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_gatherMemberDocs\n"
        "    (mro : List ClassInfo) (initial : List MemberEntry) :\n"
        "    List MemberEntry :=\n"
        "  gatherMemberDocs mro initial",
    ),
    _PROOF,
    "  intro mro initial\n"
    "  rfl",
)

# pos-foldl: a structurally DIFFERENT but behaviourally identical CORRECT impl — a
# pure `List.foldl` over the chain (no `Id.run do` monad, no `let mut`, no nested
# `for`), folding each class via the same two accumulator steps the spec fold uses, in
# the same per-class order. Semantics identical on every input. The theorem STATEMENT
# is byte-identical; its proof is reproven honestly by induction on the chain
# (`List.foldl_cons` + the `gatherMemberDocs` recursion), no new axiom/lemma/sorry. If
# it FAILS => SPEC-TOO-STRONG (the postcondition would be bound to the imperative impl
# shape rather than the behaviour).
_POS_FOLD = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_gatherMemberDocs\n"
        "    (mro : List ClassInfo) (initial : List MemberEntry) :\n"
        "    List MemberEntry :=\n"
        "  mro.foldl (fun members cls =>\n"
        "    addEntries cls.nsKey cls.classKey cls.attrDocs\n"
        "      (addAnnotations cls.classKey cls.annNames members))\n"
        "    initial",
    ),
    _PROOF,
    "  intro mro initial\n"
    "  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs\n"
    "  induction mro generalizing initial with\n"
    "  | nil => rfl\n"
    "  | cons a as ih => simp only [List.foldl_cons, gatherMemberDocs, ih]",
)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (kind="admissibility", expect="verify"). The frozen obligation is an
# unconditional `∀ mro initial`, so there is no precondition BINDER to attack; on
# this total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
# UNSATISFIABLE at exactly an F2P-shaped input. This case tests that directly: it
# keeps the frozen impl verbatim and prepends, inside the existing tactic body, two
# `have`s that discharge the obligation BY EVALUATION (`decide`) at one concrete
# F2P-shaped point — a two-class chain whose head redefines a name the tail also
# documents, whose tail additionally documents a name of its own AND declares one by
# annotation, and a NON-EMPTY `initial` standing for the members the earlier passes
# already found — and only then closes the frozen obligation verbatim. The second
# `have` pins the OUTCOME at that input to a concrete table, so the case cannot pass
# by the obligation being trivially true: it exhibits the exact witness value (seed
# preserved, the head's own records in order, the tail's annotation-declared name with
# NO documentation, the tail's base-only record appended, the tail's redefined record
# NOT overriding the head's). Statement byte-identical; no new declaration, axiom,
# lemma or sorry. If this FAILS the modeled behaviour is unsatisfiable at a normal
# input => PRECOND-TOO-STRONG.
_ADM_MRO = (
    '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
    'attrDocs := [("Bar", "attr2", "docstring bar"), '
    '("Bar", "attr3", "docstring bar3")] }, '
    '{ classKey := "Foo#", nsKey := "Foo", annNames := ["attr4"], '
    'attrDocs := [("Foo", "attr1", "docstring foo"), '
    '("Foo", "attr2", "docstring foo2")] }]'
)
_ADM_INIT = '[{ name := "attr0", doc := some "earlier pass", owner := none }]'
_ADM_EXPECT = (
    '[{ name := "attr0", doc := some "earlier pass", owner := none }, '
    '{ name := "attr2", doc := some "docstring bar", owner := some "Bar#" }, '
    '{ name := "attr3", doc := some "docstring bar3", owner := some "Bar#" }, '
    '{ name := "attr4", doc := none, owner := some "Foo#" }, '
    '{ name := "attr1", doc := some "docstring foo", owner := some "Foo#" }]'
)
_POS_ADMISS = _swap(
    _BASE,
    _PROOF,
    f"  have _ground : problem_spec_gatherMemberDocs\n"
    f"      {_ADM_MRO} {_ADM_INIT}\n"
    f"      (implementation_gatherMemberDocs\n"
    f"        {_ADM_MRO} {_ADM_INIT}) := by\n"
    f"    unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs\n"
    f"    decide\n"
    f"  have _outcome : implementation_gatherMemberDocs\n"
    f"      {_ADM_MRO} {_ADM_INIT}\n"
    f"      = {_ADM_EXPECT} := by\n"
    f"    unfold implementation_gatherMemberDocs\n"
    f"    decide\n" + _PROOF,
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the WITNESS — checked
# in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-head-only (B1): consult only the HEAD of the inheritance chain for DOCUMENTED
# attributes. The per-class annotation step is kept byte-identical and still runs for
# every class, so this rival isolates B1 alone. Correct on every documented name owned
# by the most-derived class, WRONG on every attribute documented only for a class
# further along the chain.
_RIV_HEAD = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  let mut isHead := true\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    if isHead then\n"
    "      for entry in cls.attrDocs do\n"
    "        if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "          members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "    isHead := false\n"
    "  return members",
)

# weak-flatten-annotations (B8): keep BOTH sources and the whole-chain walk, but run
# the annotation step for EVERY class to completion FIRST and only then walk the chain
# again for documented attributes, instead of consulting each class's two sources
# together one class at a time. Every collection decision, payload and order clause is
# otherwise identical, and the two agree on every input where no name is supplied by
# two different classes through DIFFERENT sources. It diverges exactly when a class
# further along the chain DECLARES a name that a class nearer the front DOCUMENTS: the
# flattened pass lets the far class's bare declaration land first and, by
# first-occurrence-wins, pre-empt the nearer class's documentation. Added by panel
# repair: this is the divergence a faithfulness review found in an earlier revision of
# this bundle, so it is the near-miss the spec must most explicitly exclude.
_RIV_FLATTEN = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "  for cls in mro do\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-docs-before-annotations (B8b): consult each class's two sources together, one
# class at a time — the whole-chain interleaving is right — but take that class's
# DOCUMENTED attributes before its annotation-declared names. A strictly finer
# near-miss than weak-flatten-annotations: the two sources of DIFFERENT classes are
# ordered correctly, so it agrees with the spec at that rival's witness input. It
# diverges only when ONE class both declares a name by annotation and documents it:
# the declaration must win there (it is consulted first), leaving the member with no
# documentation, while this rival attaches the docstring.
_RIV_DOCSFIRST = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    "  for cls in mro do\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    + _ANN_STEP
    + "  return members",
)

# weak-annotation-payload (B9): make every collection DECISION correctly, in the right
# order, but record an annotation-declared member as carrying an EMPTY docstring
# instead of NO docstring. Attacks only the annotation payload clause — the key set and
# the whole ordering are exactly right on every input, and it agrees with the spec on
# every chain with no annotation-declared names at all.
_RIV_ANNPAYLOAD = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    "  for cls in mro do\n"
    "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨name, some \"\", some cls.classKey⟩]\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-drop-annotations (B10): drop the annotation source entirely, collecting only
# documented attributes. Correct on every chain whose classes declare nothing by
# annotation, WRONG as soon as a class declares a member that way — such a member has
# a name and no documentation and must still appear in the table.
_RIV_NOANN = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    "  for cls in mro do\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-drop-ownership (B2): drop the ownership filter `entry.fst = cls.nsKey`, so
# every recorded attribute is collected regardless of whether its recorded namespace
# is this chain member's own. Correct whenever every recorded entry happens to belong
# to its own class, WRONG as soon as a chain member's record table carries an entry
# recorded under a DIFFERENT namespace (which must not be attributed to this class).
_RIV_NOFILTER = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-foreign-ownership-source (B2b): KEEP an ownership test, but resolve it against
# the WRONG source — accept an entry whose recorded namespace matches ANY class on the
# chain, rather than THIS chain member's own key. This is the lean port of nagini's
# `_PARTIAL_GLOBAL_FIRST` (first record in table order wins, regardless of which chain
# position actually owns it). It is a strictly finer near-miss than weak-drop-ownership:
# an entry recorded under an UNRELATED namespace is still correctly skipped, so it
# agrees with the spec at that rival's witness input. It diverges only when a chain
# member's own record table carries a record whose namespace belongs to a DIFFERENT
# class on the same chain — then the wrong class's documentation is attributed while
# walking this one, and by first-occurrence-wins it keeps the slot.
_RIV_FOREIGNKEY = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  let chainKeys := mro.map ClassInfo.nsKey\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst ∈ chainKeys ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-drop-dedup (B3): drop the first-occurrence guard, appending a matching entry
# even when its name is already present. Correct whenever no name recurs, WRONG the
# moment a name already in the table (e.g. seeded by an earlier pass, or documented
# further along the chain) is re-appended — the earliest occurrence must win.
_RIV_NODEDUP = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-wrong-payload (B4): make the RIGHT collection decision on every input (B1/B2/B3
# all hold) but store the class's namespace key under the collected name instead of the
# attribute's own docstring. Attacks only the PAYLOAD clause — a decision-correct impl
# that still records the wrong documentation text.
_RIV_PAYLOAD = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some cls.nsKey, some cls.classKey⟩]\n"
    "  return members",
)

# weak-reversed-precedence (B5): walk the chain in REVERSE (most-base first), so for a
# name supplied further down the hierarchy the most-BASE occurrence is recorded first
# and, by first-occurrence-wins, keeps its slot. Correct on every singly-supplied name,
# WRONG on an overridden one (the most-derived occurrence must win). Inverts the
# precedence the chain order encodes.
_RIV_REVERSED = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro.reverse do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-drop-initial (B6, frame analogue): discard the seeded `initial` table and start
# from empty. This is the lean counterpart of nagini's mandatory frame-mutation lane —
# it does not WRITE a read-only input (impossible here) but it fails to PRESERVE one:
# the members found by the earlier passes are dropped. Correct only when `initial` is
# empty, WRONG for any non-empty seed.
_RIV_DROPINIT = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members : List MemberEntry := []\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)

# weak-prepend-order (B7, ORDER-only): make every collection DECISION correctly and
# store the right payload, but push each collected record onto the FRONT of the table
# instead of appending it. B1/B2/B3/B4/B6 all hold and the collected key SET is exactly
# right on every input — only the table's insertion ORDER differs. WRONG because the
# member table's order is the order the documentation is emitted in, and prepending
# also inverts the first-occurrence relationship between the seeded members and the
# newly collected ones.
_RIV_PREPEND = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    "  for cls in mro do\n"
    "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := ⟨name, none, some cls.classKey⟩ :: members\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := ⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩ :: members\n"
    "  return members",
)

# weak-dedup-vs-seed-only (B3b): KEEP a first-occurrence guard, but test it against the
# ORIGINAL `initial` table only, never against the records collected during the walk.
# Strictly finer than weak-drop-dedup, which drops the guard entirely. This one still
# suppresses a name the earlier passes already found, so it AGREES with the spec at
# weak-drop-dedup's witness input and is not covered by it. It diverges only when the
# SAME name is supplied by two different classes on the chain: the guard cannot see the
# head's freshly collected record, so the base's occurrence is appended too and the
# most-derived record no longer uniquely holds the slot.
_RIV_DEDUP_SEED = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ initial.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.classKey⟩]\n"
    "  return members",
)


# weak-doc-owner-target (B11a): make every collection DECISION, every payload and the
# whole table order exactly right, but credit each collected DOCUMENTED attribute to
# the HEAD of the chain — the class the documentation was requested for — instead of
# the chain member being visited. This is the recorded break, re-expressed against the
# repaired carrier. The annotation step is kept byte-identical, so the rival isolates
# B11a alone; it AGREES with the spec on every attribute the head itself documents, and
# diverges exactly on one documented only for a base class.
_RIV_OWNER_TARGET = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  let target := (mro.head?).map ClassInfo.classKey\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, target⟩]\n"
    "  return members",
)

# weak-annotation-owner-target (B11b): the mirror image — credit each
# ANNOTATION-declared name to the head of the chain rather than to the class whose
# annotation declared it, keeping the documented-attribute step byte-identical. Not
# covered by B11a: that rival credits declared names correctly, so it AGREES with the
# spec at this witness input, and vice versa.
_RIV_ANNOWNER_TARGET = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  let target := (mro.head?).map ClassInfo.classKey\n"
    + "  for cls in mro do\n"
    + "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨name, none, target⟩]\n"
    + _DOC_STEP
    + "  return members",
)

# weak-owner-is-key (B11c): a boundary token swap between the two fields the repair
# deliberately keeps apart — record the visited class's NAMESPACE KEY as the supplier
# instead of its IDENTITY. Every decision, payload and order clause is right and the
# supplier is even recorded for the right chain member; only the datum is the wrong one
# of the class's two. It agrees with the spec on any chain where the two coincide.
_RIV_OWNER_KEY = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨name, none, some cls.nsKey⟩]\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, some cls.nsKey⟩]\n"
    "  return members",
)

# weak-owner-dropped (B11d): record NO supplying class for anything this pass collects,
# leaving every name, docstring and position exactly right. The coarse rival of the
# B11 family — the counterpart of weak-drop-annotations for the third component — and
# `none` is a REACHABLE value of that component (the earlier passes record members with
# no owning class), so the rival is not ruled out by typing.
_RIV_OWNER_NONE = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + "    for name in cls.annNames do\n"
    "      if name ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨name, none, none⟩]\n"
    "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, none⟩]\n"
    "  return members",
)

# weak-owner-first-matching-key (B11e): the residual freedom the repair itself leaves.
# Credit the FIRST class on the chain whose namespace key equals the matched entry's
# namespace, rather than the class being visited. Since an entry is only collected when
# its namespace equals the visited class's own key, the two coincide unless TWO classes
# on one chain share a qualified name — so this rival agrees with every other witness
# in the file and needs its own discriminating point. It is the sharpest near-miss of
# the family: it does perform a per-member ownership lookup, merely resolved against
# the key rather than the identity.
_RIV_OWNER_LOOKUP = _swap(
    _BASE,
    _IMPL,
    _SIG
    + "  let mut members := initial\n"
    + "  for cls in mro do\n"
    + _ANN_STEP
    + "    for entry in cls.attrDocs do\n"
    "      if entry.fst = cls.nsKey ∧ entry.snd.fst ∉ members.map MemberEntry.name then\n"
    "        let holder := (mro.find? (fun c => c.nsKey == entry.fst)).map ClassInfo.classKey\n"
    "        members := members ++ [⟨entry.snd.fst, some entry.snd.snd, holder⟩]\n"
    "  return members",
)


def _wit(mro, initial, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (mro, initial). `decide` reduces the transparent fold over the String /
    Option / List / structure literals and closes the disequality. Elaborates against a
    rival that diverges from the spec at this point, and FAILS on gold (which satisfies
    the spec everywhere) — SEEN to discriminate both ways with real builds."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_gatherMemberDocs\n"
        f"    {mro} {initial}\n"
        f"    (implementation_gatherMemberDocs\n"
        f"      {mro} {initial}) := by\n"
        f"  unfold problem_spec_gatherMemberDocs implementation_gatherMemberDocs\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-grounded-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ECHO,
        "rationale": (
            "the postcondition equates the result to the grounded, total, transparent "
            "fold, so the cheapest CORRECT impl echoes it; the theorem statement is "
            "byte-identical and its proof is the definitional `rfl` — no reproof "
            "machinery, no new axiom/lemma/sorry. If this cannot verify the spec is "
            "SPEC-TOO-STRONG. Also demonstrates the oracle is grounded (not an opaque "
            "answer-key), so no WRONG echo exists."
        ),
    },
    {
        "id": "pos-foldl",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLD,
        "rationale": (
            "a structurally different CORRECT impl: a pure `List.foldl` over the chain "
            "(no `Id.run do`, no `let mut`, no nested `for`), folding each class via the "
            "same two accumulator steps the spec uses, in the same per-class order. "
            "Semantics identical on every input. The theorem STATEMENT is byte-identical; "
            "its proof is reproven honestly by induction on the chain — no new "
            "axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (the postcondition would "
            "be over-fit to the imperative shape)."
        ),
    },
    {
        "id": "admiss-ground-f2p-chain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "the frozen obligation is an unconditional `∀ mro initial`, so there is no "
            "precondition binder to attack directly; on this total carrier the analogue "
            "of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an "
            "F2P-shaped input. This case discharges `problem_spec_gatherMemberDocs` BY "
            "EVALUATION (`decide`) at one concrete F2P-shaped point — a two-class chain "
            "whose head redefines a name the tail also documents, whose tail additionally "
            "documents a name of its own AND declares one by annotation, and a NON-EMPTY "
            "`initial` standing for the members the earlier passes already found — as a "
            "`have`, and only then closes the frozen obligation verbatim. A second `have` "
            "pins the OUTCOME at that input to a concrete table, so the case cannot pass "
            "by the obligation being trivially true: it exhibits the exact witness value "
            "(seed preserved first, the head's own records in recorded order, the tail's "
            "annotation-declared name with NO documentation, the tail's base-only record "
            "appended, the tail's redefined record NOT displacing the head's). Not "
            "subsumed by the reject witnesses: those state a NEGATIVE about a RIVAL, so "
            "none of them shows the frozen obligation is satisfiable anywhere. Nothing is "
            "assumed — statement byte-identical, no new declaration/axiom/lemma/sorry, "
            "both `have`s sit inside the existing tactic body. If it FAILS => "
            "PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_HEAD,
        "refinement": (
            "consulting only the head of the inheritance chain for documented attributes "
            "IS the pre-patch behaviour — the collection pass keyed on the single "
            "target-class namespace and never consulted the bases' records. Its faithful "
            "real patch is the UNCHANGED repo, which drops an attribute documented only "
            "for a base class, exactly the F2P discriminator "
            "(test_inherited_instance_variable expects the base-only attribute, documented "
            "on the base, to appear on the derived class). It fails that F2P; a verifying "
            "rival is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by behaviour B1 (whole-chain walk for documented attributes). The "
            "per-class annotation step is kept byte-identical, so this rival isolates B1 "
            "alone. For a two-class chain whose base-only documented attribute lives on "
            "the SECOND member, the spec collects it but the rival stops after the head. "
            "If it VERIFIES => SPEC-TOO-WEAK (the base classes' records are unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], attrDocs := [] }, '
            '{ classKey := "Foo#", nsKey := "Foo", annNames := [], attrDocs := [("Foo", "a", "d")] }]',
            "[]",
            "base-only documented attribute on the tail class: gold collects it, "
            "head-only rival drops it",
        ),
    },
    {
        "id": "weak-flatten-annotations",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLATTEN,
        "refinement": (
            "running the annotation step for the whole chain to completion BEFORE any "
            "documented attribute is consulted is what a real patch that kept the two "
            "sources as two separate chain walks would do. Every decision, payload and "
            "order clause is otherwise identical, so it agrees with the correct behaviour "
            "on every hierarchy where no name is supplied by two different classes through "
            "different sources — which is why it is the most dangerous near-miss here. It "
            "diverges exactly when a base class DECLARES a name that a more-derived class "
            "DOCUMENTS: the base's bare declaration lands first and pre-empts the derived "
            "class's docstring, so the member renders with no documentation at all. It "
            "fails the F2P assertion on the rendered docstring text for precisely that "
            "shape. Does NOT resolve for the right reason."
        ),
        "rationale": (
            "REJECTED by behaviour B8 (the two sources are consulted together, one class "
            "at a time). Added by panel repair: a faithfulness review found an earlier "
            "revision of this bundle modelled the annotation source as fully applied "
            "up-front, which predicted NO documentation for a member the real callee "
            "documents — so this is the exact divergence the repaired spec must exclude, "
            "and no other rival covers it (every other one changes a decision, a payload "
            "or the table order, all of which this rival gets right). Witness probes the "
            "reviewer's own input shape: a base class declaring `x` by annotation and a "
            "more-derived class documenting `x`. If it VERIFIES => SPEC-TOO-WEAK (the "
            "per-class interleaving of the two sources is unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Derived#", nsKey := "Derived", annNames := ["y"], '
            'attrDocs := [("Derived", "x", "derived x doc")] }, '
            '{ classKey := "Base#", nsKey := "Base", annNames := ["x"], '
            'attrDocs := [("Derived", "x", "derived x doc")] }]',
            "[]",
            "base class declares `x` by annotation while a more-derived class documents "
            "it: gold keeps the derived documentation, the flattened rival lets the bare "
            "declaration pre-empt it",
        ),
    },
    {
        "id": "weak-docs-before-annotations",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DOCSFIRST,
        "refinement": (
            "swapping the two sources WITHIN each class is what a real patch that placed "
            "the documented-attribute block above the annotation block inside the "
            "per-class body would do. The chain interleaving is right, so it agrees with "
            "the correct behaviour whenever no single class both declares and documents "
            "the same name. It diverges there: the declaration is consulted first and the "
            "member must render with no documentation, while this rival attaches the "
            "docstring. It fails the P2P that pins which of a class's own two sources "
            "supplies a name it provides through both. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B8 read WITHIN a class (B8b). Strictly finer than "
            "weak-flatten-annotations: the two sources of DIFFERENT classes are ordered "
            "correctly, so this rival AGREES with the spec at that rival's witness input "
            "and is not covered by it. The witness therefore moves to the point where the "
            "two differ — ONE class that both declares `x` by annotation and documents "
            "`x`. If it VERIFIES => SPEC-TOO-WEAK (the within-class source order is "
            "unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Only#", nsKey := "Only", annNames := ["x"], '
            'attrDocs := [("Only", "x", "doc")] }]',
            "[]",
            "one class both declares and documents `x`: gold lets the declaration win "
            "(no documentation), the docs-first rival attaches the docstring",
        ),
    },
    {
        "id": "weak-drop-annotations",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOANN,
        "refinement": (
            "dropping the annotation source is what a real patch that collected only "
            "comment-documented attributes would do — a member a class declares by "
            "annotation alone would vanish from the table entirely, so it is not "
            "documented at all. It fails every P2P that expects an annotation-declared "
            "member to be listed. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B10 (the annotation source contributes members). For a "
            "class declaring a name by annotation and documenting nothing, the spec "
            "collects that name with no documentation and the rival returns the seed "
            "unchanged. If it VERIFIES => SPEC-TOO-WEAK (the annotation source is "
            "unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Only#", nsKey := "Only", annNames := ["x"], attrDocs := [] }]',
            "[]",
            "annotation-declared member with no documented attributes: gold collects it "
            "undocumented, the annotation-blind rival drops it",
        ),
    },
    {
        "id": "weak-annotation-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ANNPAYLOAD,
        "refinement": (
            "recording an annotation-declared member as carrying an EMPTY docstring "
            "rather than NO docstring is what a real patch that passed `''` where the "
            "absent-documentation marker belongs would do. Every collection decision and "
            "the whole ordering are right, but a member that was only declared would then "
            "claim to have documentation (an empty one) instead of none, which is a "
            "different rendered outcome — an empty docstring is emitted where the member "
            "should fall back to having no documentation block at all, and it is also "
            "indistinguishable from a genuinely empty comment docstring. It fails the P2P "
            "that pins an annotation-declared member as undocumented. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B9 (the annotation payload is the ABSENCE of "
            "documentation, `none`, not an empty docstring `some \"\"`). This matters "
            "because the carrier deliberately distinguishes the two: a documented "
            "attribute whose recorded docstring is empty is `some \"\"`, and an "
            "annotation-declared member is `none`. Witness probes a single "
            "annotation-declared name. If it VERIFIES => SPEC-TOO-WEAK (the two would be "
            "conflated)."
        ),
        "witness": _wit(
            '[{ classKey := "Only#", nsKey := "Only", annNames := ["x"], attrDocs := [] }]',
            "[]",
            "annotation-declared member: gold records no documentation, the rival records "
            "an empty docstring",
        ),
    },
    {
        "id": "weak-drop-ownership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOFILTER,
        "refinement": (
            "dropping the ownership filter is what a real patch that removed the "
            "`ns == qualname` guard would do — it would attribute to a class every "
            "attribute the module analysis recorded, including those recorded under an "
            "unrelated namespace, so documentation would leak onto classes that do not own "
            "it. That corrupts the (namespace, name) provenance the collection relies on "
            "and fails P2P (test_instance_variable, which pins exactly which attributes "
            "belong to the class). Does NOT resolve for the right reason."
        ),
        "rationale": (
            "REJECTED by behaviour B2 (ownership filter). For a class whose record table "
            "carries an entry recorded under a DIFFERENT namespace, the spec skips it but "
            "the rival collects it. Witness probes a single class with a foreign-namespace "
            "entry. If it VERIFIES => SPEC-TOO-WEAK (the ownership filter is unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], attrDocs := [("Other", "x", "d")] }]',
            "[]",
            "foreign-namespace entry: gold skips it, ownership-blind rival collects it",
        ),
    },
    {
        "id": "weak-foreign-ownership-source",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FOREIGNKEY,
        "refinement": (
            "keeps an ownership test but resolves it against the whole inheritance "
            "chain instead of the class being visited — the lean port of nagini's "
            "wrong-precedence-source rival. Its faithful real patch compares each "
            "recorded entry's namespace against the set of chain qualnames rather than "
            "the visited class's own, so whichever record the analysis happens to have "
            "recorded FIRST for a name wins, regardless of which class in the chain "
            "actually declared it. For an attribute redefined down the hierarchy that "
            "yields the base class's documentation whenever the base's record is "
            "enumerated first — the same wrong output as inverting the chain order, but "
            "reached without touching the walk direction. It fails the P2P that pins "
            "which class each attribute's documentation comes from. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by behaviour B2 read as a per-member test (B2b). Strictly finer "
            "than weak-drop-ownership: an entry recorded under an UNRELATED namespace is "
            "still skipped, so this rival AGREES with the spec at that rival's witness "
            "input and is not covered by it. The witness therefore moves to the point "
            "where the two differ — a chain member whose own record table also carries a "
            "record recorded under a SIBLING chain member's namespace for the same name, "
            "listed first. The spec attributes only the member's own record; the rival "
            "takes the foreign one. If it VERIFIES => SPEC-TOO-WEAK (the ownership test "
            "is pinned only up to 'somewhere on the chain', not to THIS member)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
            'attrDocs := [("Foo", "attr2", "foo"), ("Bar", "attr2", "bar")] }, '
            '{ classKey := "Foo#", nsKey := "Foo", annNames := [], attrDocs := [] }]',
            "[]",
            "sibling-namespace record listed first in the visited class's own table: "
            "gold attributes only the class's own record, chain-keyed rival takes the "
            "foreign one",
        ),
    },
    {
        "id": "weak-drop-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NODEDUP,
        "refinement": (
            "dropping the first-occurrence guard is what a real patch that removed the "
            "`name not in members` check would do — it would append a duplicate for an "
            "attribute already collected by an earlier pass (or by a more-derived class), "
            "so the member table would carry two records for one name and the more-derived "
            "/ earlier documentation would no longer win. It fails a P2P that asserts a "
            "given attribute appears once with the correct (most-derived) docstring. Does "
            "NOT resolve for the right reason."
        ),
        "rationale": (
            "REJECTED by behaviour B3 (first-occurrence-wins). For a name already present "
            "in the seeded table, the spec leaves the existing record in place but the "
            "rival appends a second one. Witness probes a seeded `initial` whose name is "
            "re-owned by a chain class. If it VERIFIES => SPEC-TOO-WEAK (the dedup guard "
            "is unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
            'attrDocs := [("Bar", "attr2", "bar")] }]',
            '[{ name := "attr2", doc := some "init", owner := none }]',
            "name already seeded in `initial`: gold keeps it, dedup-blind rival "
            "re-appends it",
        ),
    },
    {
        "id": "weak-wrong-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PAYLOAD,
        "refinement": (
            "makes the RIGHT collection decision on every input but records the class's "
            "namespace key under the collected name instead of the attribute's own "
            "docstring. Its faithful real patch stores the wrong string for the member's "
            "documentation, so the F2P assertion on the exact rendered docstring text (each "
            "attribute's body line) fails. Does NOT resolve — a decision-correct impl that "
            "still emits the wrong documentation."
        ),
        "rationale": (
            "REJECTED by behaviour B4 (the docstring payload). The spec stores "
            "`entry.snd.snd` (the recovered docstring); the rival stores `cls.nsKey`. "
            "Witness varies the docstring binder at a normally-collected entry whose "
            "docstring differs from the owner's namespace key, so the two payloads differ. "
            "If it VERIFIES => SPEC-TOO-WEAK (the payload is unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
            'attrDocs := [("Bar", "attr3", "doc")] }]',
            "[]",
            "collected entry whose docstring ≠ owner key: gold stores the docstring, "
            "rival stores the key",
        ),
    },
    {
        "id": "weak-reversed-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSED,
        "refinement": (
            "walking the chain most-BASE first (or overwriting a member unconditionally) "
            "yields the most-base docstring for an overridden attribute — the opposite of "
            "Python's override semantics. Its faithful real patch documents a redefined "
            "attribute with the base class's comment rather than the derived class's, so a "
            "P2P asserting the subclass's own attribute documentation wins fails. Does NOT "
            "resolve — it inverts the precedence the chain order encodes."
        ),
        "rationale": (
            "REJECTED by behaviour B5 (most-derived-first precedence). For a name "
            "documented on BOTH the derived head and a base tail, the spec keeps the "
            "head's docstring but the reversed rival keeps the base's. Witness probes the "
            "override sub-domain (a two-class chain, same name on both, distinct "
            "docstrings). If it VERIFIES => SPEC-TOO-WEAK (the precedence direction is "
            "unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
            'attrDocs := [("Bar", "attr2", "bar")] }, '
            '{ classKey := "Foo#", nsKey := "Foo", annNames := [], '
            'attrDocs := [("Foo", "attr2", "foo")] }]',
            "[]",
            "overridden attribute on both classes: gold keeps the derived docstring, "
            "reversed keeps the base one",
        ),
    },
    {
        "id": "weak-drop-initial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPINIT,
        "refinement": (
            "starting the walk from empty rather than the seeded `initial` table is what a "
            "real patch that failed to thread the already-collected members forward would "
            "do — the members found by the earlier passes (directly-defined members, slots, "
            "enum members) would vanish from the result. It fails every P2P that "
            "expects those earlier-collected members to remain present. Does NOT resolve — "
            "this is the frame-preservation failure the read-only-input discipline guards "
            "against (the lean analogue of nagini's mandatory frame-mutation lane)."
        ),
        "rationale": (
            "REJECTED by behaviour B6 (seeding / frame preservation). The spec threads "
            "`initial` through as the base accumulator; the rival discards it. Witness "
            "probes a non-empty `initial` with an empty chain, so the spec returns the "
            "seed and the rival returns []. If it VERIFIES => SPEC-TOO-WEAK (the seeded "
            "table is unpinned — the frame hole)."
        ),
        "witness": _wit(
            "[]",
            '[{ name := "pre", doc := some "seeded", owner := none }]',
            "non-empty initial table with empty chain: gold preserves the seed, "
            "drop-initial rival loses it",
        ),
    },
    {
        "id": "weak-prepend-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPEND,
        "refinement": (
            "prepending rather than appending is what a real patch that built the member "
            "table by pushing onto the front would do. Every collection DECISION is right "
            "and every payload is right, so the set of documented members is exactly "
            "correct — but the table's order is the order the members are emitted in, so "
            "the rendered documentation lists them in the wrong sequence, and the members "
            "the earlier passes had already found no longer precede the ones this pass "
            "adds. It fails the P2P assertions that pin the rendered member sequence. "
            "Does NOT resolve for the right reason."
        ),
        "rationale": (
            "REJECTED by the ORDER clause of the spec's fold (`members ++ [entry]`, so the "
            "table grows at the tail). Every decision-changing rival above leaves the "
            "order clause untouched, so an order-only reshape — right key set, right "
            "payloads, wrong sequence — needs its own case or the spec's insertion order "
            "rests on nothing the battery demonstrates. Witness combines a non-empty seed "
            "with one collected entry, so gold's table is seed-then-collected and the "
            "rival's is collected-then-seed. If it VERIFIES => SPEC-TOO-WEAK (the table "
            "order is unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
            'attrDocs := [("Bar", "attr3", "doc")] }]',
            '[{ name := "pre", doc := some "seeded", owner := none }]',
            "order-only divergence: gold appends the collected record after the seed, "
            "the prepending rival puts it in front",
        ),
    },
    {
        "id": "weak-dedup-vs-seed-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DEDUP_SEED,
        "refinement": (
            "keeps a first-occurrence guard but resolves it against the table as it was on "
            "ENTRY rather than the table as it grows. Its faithful real patch tests the "
            "name against a snapshot of the already-found members, so a name documented by "
            "two classes on the same chain is recorded twice and the most-derived "
            "occurrence no longer uniquely holds the slot — the redefined attribute's "
            "documentation is emitted twice, once from each class. It fails the P2P that "
            "asserts a given attribute appears once with the most-derived documentation. "
            "Does NOT resolve for the right reason."
        ),
        "rationale": (
            "REJECTED by behaviour B3 read as a guard against the GROWING table (B3b). "
            "Strictly finer than weak-drop-dedup, which drops the guard outright. This "
            "rival still suppresses a name the seed already carries, so it AGREES with "
            "the spec at weak-drop-dedup's witness input and that case does not cover it. "
            "The witness therefore moves to the point where the two differ — the same "
            "name documented by BOTH chain classes with an empty seed, where the spec "
            "keeps only the most-derived record and the rival appends the base's too. If "
            "it VERIFIES => SPEC-TOO-WEAK (the dedup guard is pinned only against the "
            "seed, not against the records the walk itself collects)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], '
            'attrDocs := [("Bar", "attr2", "bar")] }, '
            '{ classKey := "Foo#", nsKey := "Foo", annNames := [], '
            'attrDocs := [("Foo", "attr2", "foo")] }]',
            "[]",
            "name collected by an earlier chain member: gold suppresses the later "
            "occurrence, the seed-only-dedup rival re-appends it",
        ),
    },
    {
        "id": "weak-doc-owner-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OWNER_TARGET,
        "refinement": (
            "crediting every collected documented attribute to the class the "
            "documentation was requested for, rather than to the chain member whose own "
            "namespace the record matched, is a ONE-TOKEN real patch: the collected "
            "record names `subject` where the visited class belongs. Every attribute is "
            "still found, with the right docstring, in the right order — so the F2P that "
            "wants a base-only documented attribute to reach the derived class PASSES. It "
            "breaks the P2P instead: the consumer keeps only the members whose recorded "
            "class is the object being documented, so with the base's attribute credited "
            "to the derived class it is emitted for a class that does not supply it and "
            "the assertion pinning a class's own attribute list fails. This IS the "
            "recorded verify-does-not-imply-resolve break (FAIL_TO_PASS 1/1 pass, "
            "PASS_TO_PASS 1/5 fail), measured on the real harness."
        ),
        "rationale": (
            "REJECTED by behaviour B11a (the supplier recorded for a documented attribute "
            "is the class being visited). The annotation step is byte-identical, so this "
            "rival isolates B11a; every other reject case in this file leaves the supplier "
            "clause alone, so without this case that clause would rest on nothing. If it "
            "VERIFIES => SPEC-TOO-WEAK, and by the measurement above the weakness is not "
            "hypothetical: this is exactly the rival that verified against the previous "
            "revision of this spec."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], attrDocs := [] }, '
            '{ classKey := "Foo#", nsKey := "Foo", annNames := [], '
            'attrDocs := [("Foo", "a", "d")] }]',
            "[]",
            "base-only documented attribute: gold credits the base that supplied it, "
            "the target-crediting rival credits the head of the chain",
        ),
    },
    {
        "id": "weak-annotation-owner-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ANNOWNER_TARGET,
        "refinement": (
            "the same one-token substitution on the OTHER source: a real patch whose "
            "annotation branch records the documented class instead of the class whose "
            "annotation declared the name. An annotation-only member inherited from a "
            "base would then be attributed to the derived class, so the consumer emits it "
            "for a class that does not declare it and the P2P pinning a class's own "
            "attribute list fails, while every name, docstring and position stays right."
        ),
        "rationale": (
            "REJECTED by behaviour B11b. Not covered by weak-doc-owner-target: that rival "
            "credits annotation-declared names correctly, so it AGREES with the spec at "
            "this witness input (a chain whose classes document nothing), and this one "
            "credits documented attributes correctly, so it agrees at that rival's input. "
            "If it VERIFIES => SPEC-TOO-WEAK (the supplier of a declared name is "
            "unpinned)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := [], attrDocs := [] }, '
            '{ classKey := "Foo#", nsKey := "Foo", annNames := ["x"], attrDocs := [] }]',
            "[]",
            "base-declared annotation-only member: gold credits the base, the "
            "target-crediting rival credits the head",
        ),
    },
    {
        "id": "weak-owner-is-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OWNER_KEY,
        "refinement": (
            "records the visited class's qualified NAME where the class itself belongs — "
            "the real patch that passes `qualname` into the collected record's class slot. "
            "The consumer tests that slot by identity against the object being "
            "documented, and a name string is never that object, so EVERY member this "
            "pass collects is filtered out and the class documents none of them: the P2P "
            "pinning the collected attribute list fails outright, even though the names, "
            "docstrings and order are all correct."
        ),
        "rationale": (
            "REJECTED by behaviour B11c (the recorded supplier is the class's IDENTITY, "
            "not its namespace key). A boundary token swap between the two fields the "
            "repaired carrier deliberately keeps apart, and the one a reviewer is most "
            "likely to think interchangeable: it is right about WHICH chain member "
            "supplied the member, wrong about which of that member's two data identifies "
            "it. If it VERIFIES => SPEC-TOO-WEAK (the two fields would be conflated, and "
            "the spec would admit a patch that documents nothing at all)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := ["x"], '
            'attrDocs := [("Bar", "a", "d")] }]',
            "[]",
            "a class whose identity token differs from its namespace key: gold records "
            "the identity for both sources, the key-recording rival records the key",
        ),
    },
    {
        "id": "weak-owner-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OWNER_NONE,
        "refinement": (
            "records no supplying class for anything the pass collects — the real patch "
            "that leaves the record's class slot empty. As with weak-owner-is-key the "
            "consumer's identity test then rejects every collected member, so the class "
            "documents none of them and the P2P fails; unlike it, this rival cannot even "
            "be defended as recording the right class by a different name."
        ),
        "rationale": (
            "REJECTED by behaviour B11d (a supplier IS recorded). The coarse member of the "
            "B11 family, kept because `none` is a REACHABLE value of that component — the "
            "earlier collection passes record members with no owning class — so typing "
            "alone does not exclude this rival and the battery must exclude it explicitly. "
            "If it VERIFIES => SPEC-TOO-WEAK (the supplier component would be unconstrained "
            "wherever this pass writes it)."
        ),
        "witness": _wit(
            '[{ classKey := "Bar#", nsKey := "Bar", annNames := ["x"], '
            'attrDocs := [("Bar", "a", "d")] }]',
            "[]",
            "one class supplying through both sources: gold records the supplier, the "
            "owner-dropping rival records none",
        ),
    },
    {
        "id": "weak-owner-first-matching-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OWNER_LOOKUP,
        "refinement": (
            "resolves the supplier by looking up the first class on the chain whose "
            "qualified name equals the matched record's namespace, instead of using the "
            "class being visited — the real patch that recovers the owning class from the "
            "record's namespace rather than from the loop variable. Two classes on one "
            "chain CAN share a qualified name (a class redefined in a nested scope, or one "
            "produced by a factory), and there the attribute is credited to the wrong one "
            "of them, so the consumer emits it for a class that does not supply it and the "
            "P2P pinning a class's own attribute list fails."
        ),
        "rationale": (
            "REJECTED by behaviour B11e. This is the freedom the repair itself leaves: "
            "because an entry is collected only when its namespace equals the visited "
            "class's own key, a lookup keyed on the namespace agrees with the spec at "
            "EVERY other witness input in this file — including both other supplier "
            "rivals — and diverges only when two chain classes share a qualified name. "
            "Without this case the spec would pin the supplier only up to 'some class on "
            "the chain carrying the matching key'. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": _wit(
            '[{ classKey := "Der#", nsKey := "Q", annNames := [], attrDocs := [] }, '
            '{ classKey := "Bas#", nsKey := "Q", annNames := [], '
            'attrDocs := [("Q", "x", "d")] }]',
            "[]",
            "two chain classes sharing one qualified name: gold credits the class being "
            "visited, the key-lookup rival credits the first one carrying that key",
        ),
    },
]


# No @ContractOnly axioms and no opaque callees: the collection logic (whole-chain
# walk, the two per-class sources and their order, ownership filter,
# first-occurrence-wins, precedence) is modeled DEEPLY (gatherMemberDocs /
# addAnnotations / addEntries) over transparent carriers, so the axiom lane is vacuous
# here and belongs to G-AX regardless.
AXIOM_TESTS = []
