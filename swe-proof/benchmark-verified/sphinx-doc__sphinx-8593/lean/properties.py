"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-8593 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY the implementation region (and,
for the positives, the proof body), so `variant_scope.same_spec` holds by
construction and every rejection is attributable to the postcondition or to the
obligation's precondition hypotheses, never to a tampered spec.

DEFENDED SURFACE
----------------
One obligation, one modeled function — the routine that collects a module's
documentable entries and resolves them for the requested mode:

    implementation_collectModuleEntries
        (wantAll : Bool) (allNames : Option (List String))
        (memberlist dirNames annotNames : List String) (val doc : String → String)
      : Bool × List Member

    theorem correct_collectModuleEntries : ∀ …, dirNames.Nodup → annotNames.Nodup →
      problem_spec_collectModuleEntries … (implementation_collectModuleEntries …)

pinned by the single load-bearing clause

    result = expectedResult wantAll allNames memberlist dirNames annotNames val doc

`expectedResult` is a FULLY TRANSPARENT deep model — `baseTable` builds one entry
per visible name (carrying `some (val n)` and `doc n`), appends one entry per
annotation-only name not already visible (carrying the annotation-only sentinel
`none` and `doc n`), and then resolves the pair by mode. There is no `opaque`
callee anywhere in the carrier (`val`/`doc` are ordinary input functions, so a
witness may instantiate them at a literal `fun _ => "…"`), which is why every
rival below is refuted by `decide` at a concrete input — no conditioning on the
carrier is needed and no witness binds a hypothesis.

Though it is a single equality, the clause pins TWELVE independent facts, and
each is attacked by its own rival:

  * the `doc` field of every VISIBLE-name entry               -> drop-recorded-doc
  * the `doc` field of every ANNOTATION-ONLY entry            -> doc-visible-only
  * per-name CORRESPONDENCE of the recorded text on the
    VISIBLE population: each entry carries the text recorded
    for ITS OWN name, not merely some collected name's text   -> doc-hoisted-lookup
  * per-name CORRESPONDENCE of the recorded text on the
    ANNOTATION-ONLY population, which is a separate loop and
    a separately violable half of the same claim              -> annot-doc-hoisted-lookup
  * the `value` field of every visible-name entry             -> visible-as-sentinel
  * per-name CORRESPONDENCE of the looked-up value            -> value-hoisted-lookup
  * the `name` field of every entry                           -> entry-name-mangled
  * table MEMBERSHIP: an annotation-only name already visible
    contributes no second entry                               -> duplicate-annot-entry
  * table ORDER: the entries come back in collection order    -> table-order-reversed
  * which MODE an empty export list selects (the flag AND
    whether suppression happens at all)                       -> empty-export-suppresses
  * the `skipped` flag under a non-empty export list          -> no-suppression
  * the ORDER and multiplicity of the request-mode result,
    and that a requested name with no collected entry is
    DROPPED rather than fabricated                            -> request-order-ignored,
                                                                 absent-request-fabricated

BINDER COVERAGE
---------------
The thirteen reject witnesses probe thirteen DISTINCT input points (verified by
comparing the argument tuples, not by inspection), and no binder is held at one
value across all of them: `wantAll` moves (`false` in request-order-ignored and
absent-request-fabricated), `allNames` takes all three admissible shapes
(`none` / `some []` / `some [_]`), `memberlist` is non-empty in exactly the cases
that read it — once naming only collected names, once naming a name with no entry
at all, and once naming a name TWICE — `dirNames` varies in length and content and
is EMPTY in annot-doc-hoisted-lookup, `annotNames` is empty,
disjoint-from-`dirNames`, equal-to-`dirNames`, and two-names-with-no-visible-name
across the set, and `doc` takes a non-empty text, a different non-empty text, and
the empty text.

`val` and `doc` need a sharper statement than "they vary", because varying them
between CONSTANT functions is not the same as probing them. A witness holding
`doc` at `fun _ => "D"` cannot tell `doc name` from `doc n'` for any other
collected name `n'`: both evaluate to `"D"`. So the constant-function witnesses
pin only that SOME recorded text is attached, never that each entry got its OWN
— which is the whole of the modeled behaviour. `doc-hoisted-lookup`,
`annot-doc-hoisted-lookup` and `value-hoisted-lookup` are the three rivals that
close this, and their witnesses are the three that instantiate `doc` / `val` at a
NON-constant function (`fun n => if n == "a" then "A" else "B"`), which is the
only shape at which a per-name-correspondence rival is refutable at all. The
correspondence claim has to be attacked TWICE on the `doc` side because the table
is built by two separate loops: a rival may hoist the lookup in one and not the
other, and a witness placed on the visible population leaves the annotation-only
population's copy of the claim untested (measured — the annot-side rival agrees
with the frozen impl at every other witness input in this battery).

PORTING NOTES (which nagini cases ported, which were omitted and why)
---------------------------------------------------------------------
The nagini sibling models a DIFFERENT and narrower slice of the same fix: two
functions over the downstream retention decision (`member_effective_doc`,
`keep_module_member`), i.e. how a member's effective documentation is chosen and
how the visibility filter consumes it. This bundle models the UPSTREAM half —
the construction of the entry table that carries each name's recorded
documentation, plus the three-way mode resolution — and the downstream filter is
explicitly out of scope here (see mapping.md: it is unchanged by the fix). So the
nagini cases port as ARGUMENTS, not as mechanics, and the case list is
re-derived against this carrier:

  * nagini `med-wrong-always-value` / `med-wrong-swap` / `kmm-wrong-classify-value`
    all attack the same underlying claim: an entry must carry the documentation
    recorded for its own name rather than an empty/substituted text. That
    argument ports to `drop-recorded-doc` (the pre-patch shape on this carrier:
    every entry's `doc` is the empty text) and, on the second entry population,
    to `doc-visible-only`.
  * nagini `med-wrong-len1` (a partial-domain NEAR-MISS, correct on most inputs,
    wrong only on a narrow sub-domain) ports as `doc-visible-only`: it attaches
    the recorded text correctly to every visible name and only drops it on the
    annotation-only entries, so it agrees with gold across the whole
    `annotNames ⊆ dirNames` domain. It gets its own witness at the input that
    distinguishes it from `drop-recorded-doc` (a visible name AND a separate
    annotation-only name), so its claimed sub-domain is actually demonstrated.
  * nagini `kmm-wrong-drop-wantall` attacks a MODE guard being dropped so the
    wrong branch fires. That argument ports twice, to the two mode guards this
    carrier has: `empty-export-suppresses` (the empty-export-list guard) and
    `no-suppression` (the suppression pass itself).
  * nagini `kmm-wrong-always-keep` (ignore the discriminating input entirely)
    ports as `request-order-ignored`: the requested-name list is reduced to a
    membership test, so the request's order and repetitions stop mattering.
  * `duplicate-annot-entry`, `table-order-reversed`, `visible-as-sentinel`,
    `entry-name-mangled` and `absent-request-fabricated` have NO nagini
    counterpart — the nagini carrier has no entry table, so table membership,
    table order, the annotation-only sentinel, the per-entry name and the
    drop-an-unresolvable-request rule are not expressible there. They are added
    because this spec pins each and a rival mishandling any one of them would
    otherwise verify.
  * `doc-hoisted-lookup` / `value-hoisted-lookup` likewise have no nagini
    counterpart, and they close the gap the nagini port's arguments cannot see:
    nagini's functions take the two documentation blocks as ARGUMENTS, so
    "the right block for this member" is not a claim its spec can even miss. Here
    the recorded text is a FUNCTION of the name, so "some collected name's text"
    and "this name's text" are distinct claims, and a rival satisfying the first
    while violating the second is invisible to any witness that instantiates
    `doc` at a constant function. Both were landed as builds before shipping.
  * nagini `med-pos-reorder` / `med-pos-locals` / `kmm-pos-bool` (structurally
    different CORRECT impls) port as `pos-functional-table` (the imperative
    do-block replaced by a pure functional expression, proof re-closed by `rfl`)
    and `pos-suppress-branch-swap` (the suppression branch tested in the inverted
    sense, proof re-closed by reproving the existing helper for the new shape).
    Both keep the `theorem correct_collectModuleEntries` statement byte-identical
    and add no lemma, axiom, or `sorry`.
  * nagini `med-admiss` / `kmm-admiss` port as `admiss-request-shaped`: the
    obligation here carries two precondition hypotheses (`dirNames.Nodup`,
    `annotNames.Nodup`), so unlike most lean bundles the admissibility class is
    NOT vacuous — an unsatisfiable or over-narrow pair would empty the obligation.
    Only ONE of the two is load-bearing, and which one was measured rather than
    assumed, by enumerating the frozen impl against `expectedResult` over 2,304,000
    inputs (a three-name universe, lists up to length 3, four `val`/`doc` shapes,
    all five modes): where `annotNames` has a repeat the frozen impl DIVERGES from
    the model on at least one input, so `annotNames.Nodup` is genuinely required;
    where only `dirNames` has a repeat the frozen impl still satisfies the spec on
    every one of the 552,960 such inputs, so `dirNames.Nodup` is REDUNDANT — it
    could be dropped and the obligation would still hold. That is a hypothesis
    STRONGER than the impl needs, and it is worth being explicit that it is not a
    spec hole in the falsifiable sense: a redundant hypothesis narrows the
    obligation, so it can only make the spec harder to satisfy, never admit a wrong
    impl. It was probed for exploitability directly — a rival returning `(true, [])`
    exactly where `dirNames.Nodup` FAILS and gold's answer elsewhere verifies (exit
    0), as it must, since the obligation says nothing at those inputs; but it is
    unshippable as a reject case for precisely that reason (no witness can refute
    it, the obligation not being asserted there), and it is not a spec defect
    because the excluded inputs are not reachable behaviour — the modeled name
    source enumerates a module's names, which are distinct by construction. Recorded
    here so the redundancy is visible in the artifact rather than discovered later.
    The case exhibits a request-shaped input satisfying both, discharged by
    `decide`, AND applies
    `correct_collectModuleEntries` at that input, so what elaborates is the
    obligation itself instantiated at a normal input rather than a subtype
    inhabitant standing next to it. The distinction matters: a satisfiable
    hypothesis pair proves only that the hypotheses are not contradictory, while
    the application proves the whole obligation is non-empty at a concrete point
    of the F2P shape.
  * nagini's THREE frame/permission-mutation cases (`med-frame-mut-attr`,
    `med-frame-mut-value`, `kmm-frame-mut-attr`) are OMITTED as VACUOUS on this
    carrier. They rely on fractional permissions over a mutable list argument;
    Lean is referentially transparent, the inputs are a `List String` value and
    two total functions, and there is no aliased state an impl could write. There
    is no substitute rival to fabricate: the frame obligation is discharged
    structurally instead, by the spec pinning every field of every returned entry
    (which is what `drop-recorded-doc` / `visible-as-sentinel` attack).
  * the nagini sibling carries NO `diverge-*` / `nonterm-*` / `weak-diverge`
    case, and this bundle ships none either — but the reason is a TOOLING bound,
    not vacuity, and it was measured rather than assumed. A diverging impl CAN be
    written here (`partial def spinForever (n : Nat) : Bool × List Member :=
    spinForever (n+1)`, with the impl delegating to it); `partial` is accepted by
    Lean and the resulting module does fail to build, so the case would be
    RECORDED as rejected. But that rejection would attest to nothing, for two
    independent reasons, both observed as builds. First, `partial` is a banned
    witness/variant token (variant_scope's assumption-token screen and
    pbt_witness's `_WITNESS_BANNED` both list it), because a `partial def` is
    introduced by an unproven inhabitant — so the case is inadmissible by rule,
    not merely unhelpful. Second, the witness that would have to justify it cannot
    discriminate: built against the diverging rival it fails with ``Tactic
    `decide` failed … its `Decidable` instance instDecidableNot did not reduce to
    `isTrue` or `isFalse` … reduction got stuck``, i.e. the kernel never evaluates
    the claim, which is exactly the `witness-undecided` stuck-reduction shape the
    gate screens for. So this is a KNOWN HOLE rather than a vacuous class: an impl
    that diverges is not refutable by any evaluating witness on this carrier, and
    a `witness_reference` does not help because the unreducible term is the
    RIVAL's, not gold's. The frozen bundle sets no
    `set_option loom.semantics.termination`, and `implementation_*` is an ordinary
    total `def` for which Lean discharges termination structurally, so nothing in
    the shipped artifact depends on this hole.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.
    (mapping.md records that this bundle declares no consumed callee axiom, so
    there is nothing there to port even in principle.)
  * No soundness positive was dropped for proof difficulty. Both positives below
    close honestly; neither weakens the obligation.

Every reject case carries a `witness`: a Lean snippet negating the spec predicate
at one concrete input, checked in a file with the frozen obligation removed. Each
must (1) ELABORATE against the rival and (2) FAIL against the frozen solution.
All thirteen were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold
exit 1), and both positives plus the admissibility case were built as full
modules (exit 0). No witness binds a hypothesis, so none can be
`witness-inconsistent` and none needs a consistency probe.

The gold-side failure was READ, not just counted: every one of the thirteen is
`Tactic 'decide' proved that the proposition ¬(… ) = expectedResult … is false`,
i.e. the kernel DECIDED the concrete claim and found the negation false. None is
an unknown identifier, a type error, a stuck reduction or a timeout — the four
shapes at which a gold-side exit 1 would attest to nothing. The carrier is
`String`/`List`/`Bool`/`Option String` with `DecidableEq`, and both function
binders are instantiated at literals, so every witness input reduces in the
kernel; there is no `witness_reference` and none is needed.

That reading was then CONFIRMED rather than trusted, because "the error looks
semantic" is not evidence. For each of the thirteen, a forgery differing from the
witness in nothing but the claim — the same input with the leading `¬` dropped, so
it asserts gold is CORRECT there — was built against the frozen solution, and all
thirteen ELABORATE (exit 0). So on this carrier gold's exit code is a function of
what is claimed and not of the impl's shape: it is 0 for the true claim and 1 for
its negation at the same input. That is the strongest form of the discrimination
evidence and it rules out the hollow case in which gold's exit 1 would have been
recorded for a witness asserting gold is correct.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8593"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence of an impl/proof-region substring; assert
    it actually matched and is unique, so silent drift (Solution.lean edited)
    fails loudly instead of shipping a case that tests nothing."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src, new_body):
    """Replace everything strictly between the proof markers. The
    `theorem correct_collectModuleEntries` STATEMENT is re-emitted
    byte-identically inside `new_body`; only the tactic body (and the helper
    lemmas a shorter proof no longer needs) change, which variant_scope permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_body + "\n" + src[e:]


# ---------------------------------------------------------------------------
# Region landmarks. Every anchor lies ENTIRELY inside the impl region except
# `_A_BRANCH_SUPPRESS_THM`, which lies entirely inside the proof region (used
# only by the positive that reproves it). Each is asserted unique file-wide.
# ---------------------------------------------------------------------------

# The whole gold impl body (the `Id.run do` block), replaced wholesale by the
# functional positive.
_A_IMPL_ALL = (
    "def implementation_collectModuleEntries (wantAll : Bool)\n"
    "    (allNames : Option (List String)) (memberlist dirNames annotNames : List String)\n"
    "    (val doc : String → String) : Bool × List Member := Id.run do\n"
    "  -- build the entry table, each entry carrying its recorded documentation text\n"
    "  let mut members : List Member := []\n"
    "  for name in dirNames do\n"
    "    members := members ++ [⟨name, some (val name), doc name, false⟩]\n"
    "  for name in annotNames do\n"
    "    if members.find? (fun m => m.name == name) |>.isNone then\n"
    "      members := members ++ [⟨name, none, doc name, false⟩]\n"
    "  -- resolve into the result for the requested mode\n"
    "  if wantAll then\n"
    "    match allNames with\n"
    "    | some names =>\n"
    "      if names ≠ [] then\n"
    "        let mut ret : List Member := []\n"
    "        for m in members do\n"
    "          if m.name ∈ names then\n"
    "            ret := ret ++ [m]\n"
    "          else\n"
    "            ret := ret ++ [{ m with skipped := true }]\n"
    "        return (false, ret)\n"
    "      else\n"
    "        return (true, members)\n"
    "    | none => return (true, members)\n"
    "  else\n"
    "    let mut ret : List Member := []\n"
    "    for name in memberlist do\n"
    "      match members.find? (fun m => m.name == name) with\n"
    "      | some m => ret := ret ++ [m]\n"
    "      | none => pure ()\n"
    "    return (false, ret)"
)

# The impl's declaration head alone (anchor for prepending an impl-region def).
_A_IMPL_HEAD = "def implementation_collectModuleEntries (wantAll : Bool)"

# One entry appended for a VISIBLE name.
_A_DIR_ENTRY = "    members := members ++ [⟨name, some (val name), doc name, false⟩]\n"

# One entry appended for an ANNOTATION-ONLY name.
_A_ANNOT_ENTRY = "      members := members ++ [⟨name, none, doc name, false⟩]\n"

# The whole second population loop, including its "not already present" guard.
_A_ANNOT_LOOP = (
    "  for name in annotNames do\n"
    "    if members.find? (fun m => m.name == name) |>.isNone then\n"
    "      members := members ++ [⟨name, none, doc name, false⟩]\n"
)

# The export-list dispatch: empty list vs non-empty list.
_A_EXPORT_BRANCH = (
    "      if names ≠ [] then\n"
    "        let mut ret : List Member := []\n"
    "        for m in members do\n"
    "          if m.name ∈ names then\n"
    "            ret := ret ++ [m]\n"
    "          else\n"
    "            ret := ret ++ [{ m with skipped := true }]\n"
    "        return (false, ret)\n"
    "      else\n"
    "        return (true, members)\n"
)

# The suppression pass alone (the non-empty-export-list arm).
_A_SUPPRESS_LOOP = (
    "        let mut ret : List Member := []\n"
    "        for m in members do\n"
    "          if m.name ∈ names then\n"
    "            ret := ret ++ [m]\n"
    "          else\n"
    "            ret := ret ++ [{ m with skipped := true }]\n"
    "        return (false, ret)\n"
)

# The requested-name resolution loop (the `wantAll = false` arm).
_A_REQUEST_LOOP = (
    "    let mut ret : List Member := []\n"
    "    for name in memberlist do\n"
    "      match members.find? (fun m => m.name == name) with\n"
    "      | some m => ret := ret ++ [m]\n"
    "      | none => pure ()\n"
    "    return (false, ret)\n"
)

# The "requested name has no collected entry" arm alone: the request is dropped.
_A_REQUEST_ABSENT = "      | none => pure ()\n"

for _a in (_A_IMPL_ALL, _A_IMPL_HEAD, _A_DIR_ENTRY, _A_ANNOT_ENTRY,
           _A_ANNOT_LOOP, _A_EXPORT_BRANCH, _A_SUPPRESS_LOOP, _A_REQUEST_LOOP,
           _A_REQUEST_ABSENT):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift (count={_BASE.count(_a)}): {_a[:70]!r}")

# The frozen helper lemma about the suppression loop, spanning from its own
# `theorem` keyword to the next helper. Reproved (same name, new statement
# matching the reshaped loop) by `pos-suppress-branch-swap`.
_A_BRANCH_SUPPRESS_THM = "theorem branch_suppress"
_A_NEXT_THM = "theorem branch_filtermap"
if _BASE.count(_A_BRANCH_SUPPRESS_THM) != 1 or _BASE.count(_A_NEXT_THM) != 1:
    raise AssertionError("proof-region helper anchors drifted")


def _reprove_branch_suppress(src, new_thm):
    start = src.index(_A_BRANCH_SUPPRESS_THM)
    end = src.index(_A_NEXT_THM)
    return src[:start] + new_thm + "\n\n" + src[end:]


# The obligation statement, re-emitted byte-identically by every positive that
# rewrites the proof region wholesale.
_THM_STMT = (
    "theorem correct_collectModuleEntries :\n"
    "    ∀ (wantAll : Bool) (allNames : Option (List String))\n"
    "      (memberlist dirNames annotNames : List String) (val doc : String → String),\n"
    "      dirNames.Nodup → annotNames.Nodup →\n"
    "      problem_spec_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc\n"
    "        (implementation_collectModuleEntries wantAll allNames memberlist dirNames annotNames val doc) := by"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-functional-table) A structurally different CORRECT impl: the imperative
# `Id.run do` skeleton (two mutable accumulation loops + three imperative return
# branches) replaced by a pure functional expression that builds the table with
# `map`/`filter` and resolves it with `map`/`filterMap`. No `for`, no `let mut`,
# no early `return`. The whole 15-lemma proof collapses to `rfl` because impl and
# reference model become definitionally equal. If this fails to verify the spec
# is over-fit to the imperative shape => SPEC-TOO-STRONG.
_POS_FUNCTIONAL_IMPL = (
    "def implementation_collectModuleEntries (wantAll : Bool)\n"
    "    (allNames : Option (List String)) (memberlist dirNames annotNames : List String)\n"
    "    (val doc : String → String) : Bool × List Member :=\n"
    "  let table : List Member :=\n"
    "    dirNames.map (fun n => ⟨n, some (val n), doc n, false⟩)\n"
    "    ++ (annotNames.filter (fun n => n ∉ dirNames)).map\n"
    "          (fun n => ⟨n, none, doc n, false⟩)\n"
    "  if wantAll then\n"
    "    match allNames with\n"
    "    | some names =>\n"
    "      if names ≠ [] then\n"
    "        (false, table.map (fun m => if m.name ∈ names then m else { m with skipped := true }))\n"
    "      else\n"
    "        (true, table)\n"
    "    | none => (true, table)\n"
    "  else\n"
    "    (false, memberlist.filterMap (fun n => table.find? (fun m => m.name == n)))"
)
_POS_FUNCTIONAL = _swap_proof(
    _swap(_BASE, _A_IMPL_ALL, _POS_FUNCTIONAL_IMPL),
    _THM_STMT
    + "\n  intro wantAll allNames memberlist dirNames annotNames val doc _ _\n  rfl\n",
)

# (pos-suppress-branch-swap) A second correct impl: the suppression pass tests
# the export-list membership in the INVERTED sense (non-member first), so the
# two loop arms are exchanged. Semantically identical; the spec's equality is
# agnostic to which arm is written first. The proof is re-closed by reproving the
# EXISTING helper `branch_suppress` for the reshaped loop (same name, same tactic
# skeleton, `split_ifs` replaced by an explicit `by_cases` on the membership so
# the negated guard normalizes) — no new lemma, no weakening, and
# `theorem correct_collectModuleEntries` is untouched. If this fails to verify
# the spec is over-fit to one branch order => SPEC-TOO-STRONG.
_POS_SWAP_LOOP = (
    "        let mut ret : List Member := []\n"
    "        for m in members do\n"
    "          if m.name ∉ names then\n"
    "            ret := ret ++ [{ m with skipped := true }]\n"
    "          else\n"
    "            ret := ret ++ [m]\n"
    "        return (false, ret)\n"
)
_POS_SWAP_THM = (
    "theorem branch_suppress (dirNames annotNames : List String) (val doc : String → String)\n"
    "    (hd : dirNames.Nodup) (ha : annotNames.Nodup) (names : List String) :\n"
    "    (forIn (m := Id) (membersFinal dirNames annotNames val doc) ([] : List Member)\n"
    "      (fun m r =>\n"
    "        if m.name ∉ names then ForInStep.yield (r ++ [{ m with skipped := true }])\n"
    "        else ForInStep.yield (r ++ [m])))\n"
    "    = (baseTable dirNames annotNames val doc).map\n"
    "        (fun m => if m.name ∈ names then m else { m with skipped := true }) := by\n"
    "  rw [table_eq dirNames annotNames val doc hd ha]\n"
    "  have key : ∀ (l acc : List Member),\n"
    "      (forIn (m := Id) l acc\n"
    "        (fun m r =>\n"
    "          if m.name ∉ names then ForInStep.yield (r ++ [{ m with skipped := true }])\n"
    "          else ForInStep.yield (r ++ [m])))\n"
    "      = acc ++ l.map (fun m => if m.name ∈ names then m else { m with skipped := true }) := by\n"
    "    intro l\n"
    "    induction l with\n"
    "    | nil => intro acc; simp only [List.forIn_nil, List.map_nil, List.append_nil, pure]\n"
    "    | cons a as ih =>\n"
    "        intro acc\n"
    "        simp only [List.forIn_cons, List.map_cons]\n"
    "        by_cases h : a.name ∈ names <;> (simp only [bind]; simp only [h, if_true, if_false,\n"
    "          not_true_eq_false, not_false_eq_true, if_neg, if_pos]; rw [ih]; simp)\n"
    "  have := key (baseTable dirNames annotNames val doc) []\n"
    "  simpa using this"
)
_POS_SWAP = _reprove_branch_suppress(
    _swap(_BASE, _A_SUPPRESS_LOOP, _POS_SWAP_LOOP), _POS_SWAP_THM)


# ===========================================================================
# ADMISSIBILITY — the obligation's precondition hypotheses must admit a normal
# F2P-shaped input. NOT vacuous here: `correct_collectModuleEntries` really does
# assume `dirNames.Nodup → annotNames.Nodup →`, so an over-strong (or outright
# unsatisfiable) hypothesis pair would make the whole obligation empty.
# ===========================================================================

# Two checks, because the weaker one alone leaves a gap. The subtype exhibits an
# input shaped like the discriminating scenario — a module exposing a
# leading-underscore name and a plain name, plus one annotation-only name — and
# discharges both distinctness hypotheses by `decide`; that shows the pair is
# SATISFIABLE. But satisfiable hypotheses are not yet a non-vacuous obligation:
# what has to elaborate is `correct_collectModuleEntries` APPLIED at that input,
# with both hypotheses supplied. The `example` below does exactly that, so the
# case fails if the hypothesis pair is unsatisfiable, if it is narrower than a
# normal input, OR if the obligation cannot actually be instantiated there
# => PRECOND-TOO-STRONG. The `example` is anonymous, so it declares no new
# theorem/lemma name (variant_scope rule 3) and sits in the proof region, where a
# variant may freely reprove.
_ADMISS_DEF = (
    "/-- Admissibility probe: the two distinctness hypotheses the obligation\n"
    "assumes are jointly satisfiable at an input shaped like the discriminating\n"
    "scenario. Lives in the implementation region, so the spec view is unchanged. -/\n"
    "def admissibleCollectionInput :\n"
    "    { p : List String × List String // p.1.Nodup ∧ p.2.Nodup } :=\n"
    "  ⟨([\"_marked\", \"plain\"], [\"annotatedOnly\"]), by decide⟩\n"
    "\n"
)
# The obligation instantiated at that same input: a module exposing a
# leading-underscore name carrying a non-empty recorded text and a plain name
# carrying none, plus one annotation-only name, taken in all-members mode with no
# export list. `doc` is deliberately NON-constant here, so the instantiated
# statement is the discriminating one rather than a degenerate reading of it.
_ADMISS_APPLY = (
    "\nexample : problem_spec_collectModuleEntries true none []\n"
    "    [\"_marked\", \"plain\"] [\"annotatedOnly\"] (fun _ => \"v\")\n"
    "    (fun n => if n == \"_marked\" then \"M\" else \"\")\n"
    "    (implementation_collectModuleEntries true none []\n"
    "      [\"_marked\", \"plain\"] [\"annotatedOnly\"] (fun _ => \"v\")\n"
    "      (fun n => if n == \"_marked\" then \"M\" else \"\")) :=\n"
    "  correct_collectModuleEntries true none [] [\"_marked\", \"plain\"] [\"annotatedOnly\"]\n"
    "    (fun _ => \"v\") (fun n => if n == \"_marked\" then \"M\" else \"\") (by decide) (by decide)\n"
)
_ADMISS = _swap(_BASE, _A_IMPL_HEAD, _ADMISS_DEF + _A_IMPL_HEAD)
_ADMISS = _swap(_ADMISS, _PROOF_TAIL, _ADMISS_APPLY + "\n" + _PROOF_TAIL)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (drop-recorded-doc) Attach NO recorded documentation text to any entry: every
# entry's `doc` field is the empty text regardless of what the source records.
# This is the PRE-PATCH shape on this carrier (cf. Solution_prepatch.lean) and
# the whole of the modeled defect. Wrong on every input where some collected name
# has a non-empty recorded text.
_R_DROP_DOC = _swap(
    _swap(_BASE, _A_DIR_ENTRY,
          '    members := members ++ [⟨name, some (val name), "", false⟩]\n'),
    _A_ANNOT_ENTRY,
    '      members := members ++ [⟨name, none, "", false⟩]\n')

# (doc-visible-only) A partial-domain NEAR-MISS: attach the recorded text to
# every VISIBLE-name entry (correctly) but not to the annotation-only entries.
# Agrees with gold on the whole `annotNames ⊆ dirNames` domain — including every
# input `drop-recorded-doc` is refuted at — and diverges only where a name has a
# declared annotation, no visible value, and a non-empty recorded text. Its
# witness is placed at exactly that input, so its claimed sub-domain is
# demonstrated rather than asserted.
_R_DOC_VISIBLE_ONLY = _swap(
    _BASE, _A_ANNOT_ENTRY,
    '      members := members ++ [⟨name, none, "", false⟩]\n')

# (duplicate-annot-entry) Drop the "not already collected" guard on the second
# population loop, so a name that is BOTH visible and annotation-only gets a
# second entry carrying the annotation-only sentinel. Correct whenever the two
# name sets are disjoint; wrong on every overlap.
_R_NO_DEDUP = _swap(
    _BASE, _A_ANNOT_LOOP,
    "  for name in annotNames do\n"
    "    members := members ++ [⟨name, none, doc name, false⟩]\n")

# (empty-export-suppresses) Drop the empty-export-list guard, so an EMPTY export
# list is treated as a real one: the flag flips to `false` and every entry is
# marked suppressed (no name is in the empty list). Correct on a non-empty export
# list and on no export list at all; wrong precisely on the empty one — which is
# the configuration the discriminating scenario runs in.
_R_EMPTY_EXPORT = _swap(
    _BASE, _A_EXPORT_BRANCH,
    "      let mut ret : List Member := []\n"
    "      for m in members do\n"
    "        if m.name ∈ names then\n"
    "          ret := ret ++ [m]\n"
    "        else\n"
    "          ret := ret ++ [{ m with skipped := true }]\n"
    "      return (false, ret)\n")

# (no-suppression) Under a non-empty export list, return the table untouched:
# the correct flag, the correct entries, but nothing ever marked suppressed.
# Attacks the `skipped` component alone — every other field agrees with gold.
_R_NO_SUPPRESS = _swap(
    _BASE, _A_SUPPRESS_LOOP, "        return (false, members)\n")

# (request-order-ignored) In request mode, reduce the requested-name list to a
# membership test and walk the TABLE instead: the returned entries are correct as
# a set, but they come back in collection order rather than request order, and a
# name requested twice is returned once. Attacks the order/multiplicity component
# of the request-mode result.
_R_REQUEST_ORDER = _swap(
    _BASE, _A_REQUEST_LOOP,
    "    let mut ret : List Member := []\n"
    "    for m in members do\n"
    "      if m.name ∈ memberlist then\n"
    "        ret := ret ++ [m]\n"
    "    return (false, ret)\n")

# (visible-as-sentinel) Record every VISIBLE name with the annotation-only
# sentinel instead of its looked-up value, keeping the recorded documentation
# text intact. Attacks the `value` component alone — the one field the two
# doc-attachment rivals leave correct.
_R_DROP_VALUE = _swap(
    _BASE, _A_DIR_ENTRY,
    "    members := members ++ [⟨name, none, doc name, false⟩]\n")

# (doc-hoisted-lookup) HOIST the recorded-text lookup out of the collection loop:
# every visible entry carries the text recorded for the FIRST visible name
# instead of the text recorded for its own name. Attacks per-name CORRESPONDENCE,
# which is a strictly stronger claim than "some recorded text is attached" and the
# one the two doc-attachment rivals above cannot reach: they are refuted by a
# witness holding `doc` at a constant function, and at a constant function this
# rival is INDISTINGUISHABLE from gold. Wrong on every input with two collected
# names whose recorded texts differ.
_R_DOC_HOISTED = _swap(
    _BASE, _A_DIR_ENTRY,
    '    members := members ++ [⟨name, some (val name), doc (dirNames.headD ""), false⟩]\n')

# (annot-doc-hoisted-lookup) The same hoist on the SECOND population loop: every
# ANNOTATION-ONLY entry carries the text recorded for the first annotation-only
# name instead of the text recorded for its own name. `doc-hoisted-lookup` hoists
# only the VISIBLE loop, so it leaves per-name correspondence on the
# annotation-only entries unattacked, and every other rival that touches those
# entries either drops their text entirely (`doc-visible-only`) or is refuted by
# a constant-`doc` witness — at a constant `doc` this rival equals gold. Refutable
# only at TWO annotation-only names whose recorded texts differ, an input no other
# witness in the battery visits (measured: this rival agrees with the frozen impl
# at all twelve of the other witness inputs).
_R_ANNOT_DOC_HOISTED = _swap(
    _BASE, _A_ANNOT_ENTRY,
    '      members := members ++ [⟨name, none, doc (annotNames.headD ""), false⟩]\n')

# (value-hoisted-lookup) The same hoist on the VALUE lookup: every visible entry
# carries the value looked up for the first visible name. Attacks per-name
# correspondence of the `value` component, which `visible-as-sentinel` (whose
# witness holds `val` at a constant function) cannot reach either.
_R_VALUE_HOISTED = _swap(
    _BASE, _A_DIR_ENTRY,
    '    members := members ++ [⟨name, some (val (dirNames.headD "")), doc name, false⟩]\n')

# (entry-name-mangled) Record each visible entry under its looked-up VALUE rather
# than under its name. Attacks the `name` component — the fourth field of every
# entry, which the spec pins and which no other rival here touches.
_R_NAME_MANGLED = _swap(
    _BASE, _A_DIR_ENTRY,
    "    members := members ++ [⟨val name, some (val name), doc name, false⟩]\n")

# (table-order-reversed) Collect the visible entries by PREPENDING, so the table
# comes back in reverse collection order. Every entry is individually correct and
# the table is correct as a set; only the stable collection ORDER is violated.
# Distinct from request-order-ignored, which attacks ordering on the request-mode
# arm — this attacks the order of the table itself, which the two all-members
# modes return directly.
_R_TABLE_ORDER = _swap(
    _BASE, _A_DIR_ENTRY,
    "    members := [⟨name, some (val name), doc name, false⟩] ++ members\n")

# (absent-request-fabricated) In request mode, a requested name with NO collected
# entry gets a fabricated annotation-only entry instead of being dropped.
# Attacks the "silently dropping names with no collected entry" half of the
# request-mode arm — correct on every request naming only collected names, so
# request-order-ignored's witness does not reach it.
_R_ABSENT_FABRICATED = _swap(
    _BASE, _A_REQUEST_ABSENT,
    "      | none => ret := ret ++ [⟨name, none, doc name, false⟩]\n")


# --- witnesses -------------------------------------------------------------
# Each negates the spec predicate at ONE concrete input. The carrier is fully
# transparent (`val`/`doc` are instantiated at literal constant functions), so
# `decide` closes and no witness binds a hypothesis — there is nothing that
# could be inconsistent. All thirteen were built against the rival (exit 0) and
# against the frozen solution (exit 1), and each was additionally built against
# gold with its claim FLIPPED (exit 0), so gold's exit code is known to track the
# claim rather than the impl's syntactic shape.

def _wit(args):
    return (
        "example : ¬ problem_spec_collectModuleEntries\n"
        f"    {args}\n"
        "    (implementation_collectModuleEntries\n"
        f"      {args}) := by\n"
        "  unfold problem_spec_collectModuleEntries implementation_collectModuleEntries\n"
        "  decide")


# One visible leading-underscore name carrying a non-empty recorded text, taken
# in all-members mode with no export list — the discriminating configuration.
# gold: doc = "D"; rival: doc = "".
_W_DROP_DOC = _wit('true none [] ["_a"] [] (fun _ => "v") (fun _ => "D")')

# A visible name AND a separate annotation-only name, both with a non-empty
# recorded text. Distinguishes this near-miss from drop-recorded-doc: the visible
# entry is correct here, only the annotation-only entry loses its text. Varies
# `annotNames` (non-empty, disjoint from `dirNames`).
_W_DOC_VISIBLE_ONLY = _wit('true none [] ["b"] ["_a"] (fun _ => "v") (fun _ => "D")')

# A name that is BOTH visible and annotation-only: gold collects one entry, the
# rival collects two. Varies `annotNames` to equal `dirNames`.
_W_NO_DEDUP = _wit('true none [] ["a"] ["a"] (fun _ => "v") (fun _ => "note")')

# An EMPTY export list: gold returns (true, table); the rival returns (false,
# table-all-suppressed). Varies `allNames` to `some []`.
_W_EMPTY_EXPORT = _wit(
    'true (some ([] : List String)) [] ["a"] [] (fun _ => "v") (fun _ => "note")')

# A non-empty export list naming only the first of two visible names: gold marks
# the second suppressed, the rival marks nothing. Varies `allNames` to `some [_]`
# and `dirNames` to length 2.
_W_NO_SUPPRESS = _wit(
    'true (some ["a"]) [] ["a", "b"] [] (fun _ => "v") (fun _ => "note")')

# Request mode with the names requested in the REVERSE of collection order AND
# one of them requested TWICE: gold returns [b, a, b] (request order, repeats
# honoured), the rival returns [a, b] (collection order, repeat collapsed). Both
# halves of the clause this rival attacks are exercised at one input — a witness
# at `["b", "a"]` alone refutes it only on ORDER and leaves the multiplicity claim
# in the rationale undemonstrated.
_W_REQUEST_ORDER = _wit(
    'false none ["b", "a", "b"] ["a", "b"] [] (fun _ => "v") (fun _ => "note")')

# Two collected names whose recorded texts DIFFER, so `doc` is instantiated at a
# non-constant function: gold gives the second entry its own text "B", the rival
# gives it the first name's text "A". The first of the two witnesses that can see
# per-name correspondence at all.
_W_DOC_HOISTED = _wit(
    'true none [] ["a", "b"] [] (fun _ => "v") (fun n => if n == "a" then "A" else "B")')

# TWO ANNOTATION-ONLY names whose recorded texts DIFFER, and no visible name at
# all, so `annotNames.headD ""` is the first annotation-only name: gold gives the
# second annotation-only entry its own text "B", the rival gives it "A". The only
# witness in the battery whose `dirNames` is empty and whose `annotNames` has two
# names, which is the only shape at which per-name correspondence on the SECOND
# population loop is visible.
_W_ANNOT_DOC_HOISTED = _wit(
    'true none [] [] ["a", "b"] (fun _ => "v") (fun n => if n == "a" then "A" else "B")')

# The same shape on the value lookup: `val` non-constant, so gold gives the second
# entry `some "B"` and the rival `some "A"`.
_W_VALUE_HOISTED = _wit(
    'true none [] ["a", "b"] [] (fun n => if n == "a" then "A" else "B") (fun _ => "d")')

# One visible name whose looked-up value differs from the name itself: gold
# records the entry under "a", the rival under "v".
_W_NAME_MANGLED = _wit('true none [] ["a"] [] (fun _ => "v") (fun _ => "d")')

# Two visible names, all-members mode, no export list: gold returns them in
# collection order, the rival reversed. Every field of every entry agrees.
_W_TABLE_ORDER = _wit('true none [] ["a", "b"] [] (fun _ => "v") (fun _ => "d")')

# Request mode naming a single name that is NOT collected: gold returns the empty
# list, the rival fabricates an entry for it. The only witness whose `memberlist`
# names a name with no collected entry.
_W_ABSENT_FABRICATED = _wit(
    'false none ["zz"] ["a"] [] (fun _ => "v") (fun _ => "note")')

# One visible name with a looked-up value and NO recorded text: gold records
# `some "V"`, the rival records the annotation-only sentinel. The only witness
# that moves `val` off "v" and the only one with an empty recorded text, so it
# also varies the `doc` binder at its boundary.
_W_DROP_VALUE = _wit('true none [] ["a"] [] (fun _ => "V") (fun _ => "")')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----------------------------------
    {"id": "pos-functional-table", "kind": "soundness", "expect": "verify",
     "module": _POS_FUNCTIONAL,
     "rationale": "a structurally different but CORRECT impl: the imperative "
                  "accumulation skeleton (two `let mut` loops, three imperative "
                  "return branches) replaced by a pure functional expression that "
                  "builds the entry table with `map`/`filter` and resolves it with "
                  "`map`/`filterMap`. It becomes definitionally equal to the "
                  "reference model, so the whole helper-lemma chain collapses and "
                  "`correct_collectModuleEntries` re-closes with `rfl` — same "
                  "statement, no new lemma, no assumption. The carrier is fully "
                  "transparent so there is no oracle to echo; this stands purely as "
                  "a soundness positive of a different impl form. If it fails to "
                  "verify the spec is over-fit to the imperative shape => "
                  "SPEC-TOO-STRONG. Built as a full module: exit 0."},
    {"id": "pos-suppress-branch-swap", "kind": "soundness", "expect": "verify",
     "module": _POS_SWAP,
     "rationale": "a second correct impl: inside the export-list mode the "
                  "suppression pass tests membership in the INVERTED sense "
                  "(non-member arm first), exchanging the two loop bodies. "
                  "Semantically identical — the spec's equality is agnostic to which "
                  "arm is written first — and it exercises the reverse guard that "
                  "`no-suppression` attacks. The proof is re-closed by reproving the "
                  "EXISTING helper for the reshaped loop (same name, `split_ifs` "
                  "replaced by an explicit `by_cases` so the negated guard "
                  "normalizes); no lemma is added, nothing is weakened, and the "
                  "obligation statement is byte-identical. If it fails to verify the "
                  "spec is over-fit to one branch order => SPEC-TOO-STRONG. Built as "
                  "a full module: exit 0."},

    # ---- admissibility (must VERIFY) -------------------------------------
    {"id": "admiss-request-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "unlike most lean bundles this obligation carries REAL "
                  "precondition hypotheses (`dirNames.Nodup → annotNames.Nodup →`), "
                  "so the admissibility class is not vacuous: an unsatisfiable or "
                  "over-narrow hypothesis pair would make the whole obligation empty "
                  "and every case above meaningless. `annotNames.Nodup` is the "
                  "load-bearing one — measured by enumeration, the frozen impl "
                  "violates the spec at a repeated annotation-only name, and holds at "
                  "a repeated visible name, so `dirNames.Nodup` is redundant (see the "
                  "porting notes; a redundant hypothesis narrows the obligation and so "
                  "cannot admit a wrong impl, which is why it is recorded rather than "
                  "attacked). That is exactly why the probe discharges BOTH by "
                  "`decide` at one concrete input instead of arguing about which is "
                  "needed. Two checks, because the weaker "
                  "one alone is not enough: (1) an implementation-region `def` whose "
                  "subtype proof component exhibits an input shaped like the "
                  "discriminating scenario — a module exposing a leading-underscore "
                  "name and a plain name, plus one annotation-only name — and "
                  "discharges both hypotheses by `decide`, showing the pair is "
                  "SATISFIABLE; and (2) an anonymous `example` that APPLIES "
                  "`correct_collectModuleEntries` at that same input with both "
                  "hypotheses supplied, so what elaborates is the obligation itself "
                  "instantiated at a normal input rather than a subtype inhabitant "
                  "standing next to it. Satisfiable hypotheses only say the pair is "
                  "not contradictory; the application is what shows the obligation is "
                  "non-empty at a concrete F2P-shaped point. `doc` is non-constant "
                  "there, so the instantiated statement is the discriminating one. If "
                  "either fails to verify => PRECOND-TOO-STRONG. Built as a full "
                  "module: exit 0."},

    # ---- uniqueness rivals (must be REJECTED, with a seen witness) -------
    {"id": "drop-recorded-doc", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROP_DOC, "witness": _W_DROP_DOC,
     "refinement": "its faithful real patch collects each module entry WITHOUT the "
                   "documentation text recorded for that name, leaving every entry's "
                   "text empty. The unchanged downstream step that decides whether to "
                   "render an entry reads exactly that text, so a leading-underscore "
                   "module variable whose recorded text marks it for export is "
                   "classified by the name convention alone and dropped. That is the "
                   "behaviour the issue reports and the FAIL_TO_PASS tests assert "
                   "against (they expect that variable rendered together with its "
                   "recorded text), so the patch would NOT resolve — a rival "
                   "verifying here would be a true verify-does-not-imply-resolve "
                   "break.",
     "rationale": "attacks the `doc` component of EVERY entry in the pinned "
                  "`result = expectedResult …` equality, i.e. the load-bearing half "
                  "of the clause. Witness at one visible leading-underscore name with "
                  "a non-empty recorded text, all-members mode, no export list: gold "
                  "records that text, the rival records the empty text. Built both "
                  "ways (rival exit 0, gold exit 1)."},
    {"id": "doc-visible-only", "kind": "uniqueness", "expect": "reject",
     "module": _R_DOC_VISIBLE_ONLY, "witness": _W_DOC_VISIBLE_ONLY,
     "refinement": "its faithful real patch attaches the recorded documentation text "
                   "when collecting entries for the names visible on the module, but "
                   "leaves it off the entries added for names that carry only a "
                   "declared annotation. Such a member's recorded text then never "
                   "reaches the downstream render/skip decision, so an "
                   "annotation-only member documented for export is still dropped "
                   "while an ordinary one is fixed — a partial fix that leaves the "
                   "reported behaviour in place for that member shape, so it does not "
                   "faithfully resolve the issue.",
     "rationale": "a partial-domain NEAR-MISS: agrees with gold on every input where "
                  "the annotation-only names are already visible — including the input "
                  "`drop-recorded-doc` is refuted at — so it needs its own witness. "
                  "Placed at a visible name PLUS a separate annotation-only name, both "
                  "with a non-empty recorded text: gold gives the second entry that "
                  "text, the rival gives it the empty text. This is the only witness "
                  "that varies `annotNames` to a non-empty set disjoint from "
                  "`dirNames`. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "duplicate-annot-entry", "kind": "uniqueness", "expect": "reject",
     "module": _R_NO_DEDUP, "witness": _W_NO_DEDUP,
     "refinement": "its faithful real patch omits the check that a declared-annotation "
                   "name was not already collected, so any member that both is visible "
                   "on the module and carries a declared annotation is collected twice "
                   "— once with its looked-up value and once with the annotation-only "
                   "sentinel. Every such member would be rendered twice, and the "
                   "sentinel copy renders without its value; the FAIL_TO_PASS tests "
                   "compare the rendered output line-for-line against an exact "
                   "expected list, so the duplicate entry fails them and the patch "
                   "does NOT resolve.",
     "rationale": "attacks table MEMBERSHIP in `result = expectedResult …`: "
                  "`baseTable` appends an annotation-only entry only for names NOT "
                  "already visible. Witness at a name that is both visible and "
                  "annotation-only (the only witness holding `annotNames = dirNames`): "
                  "gold collects one entry, the rival two. Built both ways (rival exit "
                  "0, gold exit 1)."},
    {"id": "empty-export-suppresses", "kind": "uniqueness", "expect": "reject",
     "module": _R_EMPTY_EXPORT, "witness": _W_EMPTY_EXPORT,
     "refinement": "its faithful real patch treats an EMPTY export list as a real "
                   "one, so on a module that declares no export list (or an empty "
                   "one) every collected entry is marked suppressed and the "
                   "all-members flag comes back false. Nothing would be rendered for "
                   "such a module at all — which is the configuration the reported "
                   "scenario and the FAIL_TO_PASS tests run in — so it does NOT "
                   "resolve.",
     "rationale": "attacks the MODE dispatch of the clause: which branch of "
                  "`expectedResult` an empty export list selects, and therefore both "
                  "the returned flag and whether any entry is marked suppressed. "
                  "Correct on a non-empty export list and on no export list at all. "
                  "Witness at `allNames = some []` (the only witness at that shape): "
                  "gold => (true, table unsuppressed), rival => (false, table all "
                  "suppressed). Built both ways (rival exit 0, gold exit 1)."},
    {"id": "no-suppression", "kind": "uniqueness", "expect": "reject",
     "module": _R_NO_SUPPRESS, "witness": _W_NO_SUPPRESS,
     "refinement": "its faithful real patch never marks an entry suppressed under a "
                   "non-empty export list, so a module that declares an export list "
                   "would render every name it exposes rather than only the exported "
                   "ones. The PASS_TO_PASS suite pins the rendered output of such "
                   "modules exactly, so the extra entries fail it and the patch does "
                   "NOT resolve.",
     "rationale": "attacks the `skipped` component alone — name, value and recorded "
                  "text all agree with gold, so only the suppression flag in "
                  "`expectedResult`'s export-list branch refutes it. Witness at an "
                  "export list naming the first of two visible names: gold marks the "
                  "second suppressed, the rival marks nothing. Varies `allNames` to "
                  "`some [_]` and `dirNames` to length 2. Built both ways (rival exit "
                  "0, gold exit 1)."},
    {"id": "request-order-ignored", "kind": "uniqueness", "expect": "reject",
     "module": _R_REQUEST_ORDER, "witness": _W_REQUEST_ORDER,
     "refinement": "its faithful real patch answers an explicit list of requested "
                   "names by filtering the collected table for membership instead of "
                   "resolving the request name by name, so the requested entries come "
                   "back in collection order rather than in the order asked for (and a "
                   "name asked for twice comes back once). The FAIL_TO_PASS tests "
                   "compare the rendered output against an exact ordered list, so a "
                   "reordered result fails them and the patch does NOT resolve.",
     "rationale": "attacks the ORDER and multiplicity of the request-mode arm "
                  "(`memberlist.filterMap …`, which is indexed by the REQUEST, not by "
                  "the table). The returned entries are correct as a set, so only the "
                  "ordering and multiplicity halves of the equality refute it, and the "
                  "witness demonstrates BOTH at one input rather than claiming the "
                  "second: the request is `[\"b\", \"a\", \"b\"]` against a table "
                  "collected as `[\"a\", \"b\"]`, so gold returns `[b, a, b]` (request "
                  "order, the repeat honoured) and the rival returns `[a, b]` "
                  "(collection order, the repeat collapsed). Built both ways (rival "
                  "exit 0, gold exit 1)."},
    {"id": "visible-as-sentinel", "kind": "uniqueness", "expect": "reject",
     "module": _R_DROP_VALUE, "witness": _W_DROP_VALUE,
     "refinement": "its faithful real patch records every name visible on the module "
                   "with the annotation-only sentinel instead of the value looked up "
                   "for it, so every module variable is rendered as though it had a "
                   "declared type and no bound value — its value is omitted from the "
                   "rendered output. The FAIL_TO_PASS tests assert the rendered value "
                   "line for the variables in question, so it does NOT resolve.",
     "rationale": "attacks the `value` component alone — the one field the two "
                  "doc-attachment rivals leave correct, so without this case a rival "
                  "mishandling only the value lookup would verify. Witness at one "
                  "visible name with a looked-up value and no recorded text: gold "
                  "records `some \"V\"`, the rival the sentinel `none`. The only "
                  "witness that moves the `val` binder off its shared value, and the "
                  "only one holding `doc` at the empty text, so it varies both "
                  "function binders. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "doc-hoisted-lookup", "kind": "uniqueness", "expect": "reject",
     "module": _R_DOC_HOISTED, "witness": _W_DOC_HOISTED,
     "refinement": "its faithful real patch looks up the recorded documentation text "
                   "ONCE, outside the loop that collects the entries, and attaches that "
                   "one text to every entry it builds. Every collected member is then "
                   "documented with some other member's text: the leading-underscore "
                   "variable whose recorded text marks it for export gets whichever "
                   "text the first collected name happened to have, and conversely a "
                   "member with no recorded text inherits a marker meant for someone "
                   "else. The unchanged downstream step reads each entry's text to "
                   "decide whether to render it, so members are kept and dropped "
                   "essentially at random relative to what the source records; the "
                   "FAIL_TO_PASS tests compare the rendered output against an exact "
                   "expected list and would fail, so it does NOT resolve.",
     "rationale": "attacks per-name CORRESPONDENCE of the `doc` component: the pinned "
                  "`result = expectedResult …` requires each entry's text to be `doc n` "
                  "for ITS OWN `n`, which is strictly stronger than "
                  "`drop-recorded-doc`'s claim that some non-empty text is attached. "
                  "This is the gap a constant-function witness cannot see — at "
                  "`doc = fun _ => \"D\"` this rival is indistinguishable from gold, so "
                  "neither doc-attachment rival above refutes it. Its witness is "
                  "therefore the first to instantiate `doc` at a NON-constant function "
                  "(two collected names with different texts): gold gives the second "
                  "entry \"B\", the rival gives it \"A\". Built both ways (rival exit 0, "
                  "gold exit 1)."},
    {"id": "annot-doc-hoisted-lookup", "kind": "uniqueness", "expect": "reject",
     "module": _R_ANNOT_DOC_HOISTED, "witness": _W_ANNOT_DOC_HOISTED,
     "refinement": "its faithful real patch looks up the recorded documentation "
                   "text once for the whole second population pass, so every member "
                   "that has only a declared annotation and no bound value is "
                   "documented with the text recorded for whichever such member came "
                   "first. The unchanged downstream step reads each entry's text to "
                   "decide whether to render it, so among the annotation-only members "
                   "the render/skip decision is driven by one arbitrary member's text "
                   "rather than each member's own: one documented for export drags the "
                   "rest along, and an undocumented one is dropped even when its own "
                   "text marks it. The FAIL_TO_PASS tests compare the rendered output "
                   "against an exact expected list, so it does NOT resolve.",
     "rationale": "attacks per-name CORRESPONDENCE of the `doc` component on the "
                  "SECOND population loop — the annotation-only entries that "
                  "`baseTable` appends. `doc-hoisted-lookup` hoists only the VISIBLE "
                  "loop and so leaves this half of the same clause unattacked, and no "
                  "other rival reaches it: `doc-visible-only` drops those entries' text "
                  "outright (a claim refutable at a constant `doc`), whereas at a "
                  "constant `doc` THIS rival is indistinguishable from gold. Its "
                  "witness is therefore the only one with an empty `dirNames` and two "
                  "annotation-only names carrying DIFFERENT texts: gold gives the "
                  "second entry \"B\", the rival gives it \"A\". Measured before "
                  "shipping: this rival agrees with the frozen impl at all twelve other "
                  "witness inputs in this battery, so without this case a patch "
                  "mishandling it would verify. Built both ways (rival exit 0, gold "
                  "exit 1); the flipped-claim forgery builds against gold at exit 0, so "
                  "gold's exit code tracks the claim rather than the shape."},
    {"id": "value-hoisted-lookup", "kind": "uniqueness", "expect": "reject",
     "module": _R_VALUE_HOISTED, "witness": _W_VALUE_HOISTED,
     "refinement": "its faithful real patch hoists the per-name value lookup out of "
                   "the collection loop, so every collected entry carries the value "
                   "looked up for the first name rather than its own. Every module "
                   "variable would render with some other variable's value; the "
                   "FAIL_TO_PASS tests assert the rendered value line for the variables "
                   "in question, so it does NOT resolve.",
     "rationale": "the same per-name correspondence attack on the `value` component. "
                  "`visible-as-sentinel` replaces the value with the annotation-only "
                  "sentinel and is refuted by a constant-`val` witness, which leaves "
                  "'each entry carries the value looked up for ITS OWN name' "
                  "unattacked: at `val = fun _ => \"v\"` this rival equals gold. Witness "
                  "with `val` non-constant over two collected names: gold records "
                  "`some \"B\"` for the second, the rival `some \"A\"`. Built both ways "
                  "(rival exit 0, gold exit 1)."},
    {"id": "entry-name-mangled", "kind": "uniqueness", "expect": "reject",
     "module": _R_NAME_MANGLED, "witness": _W_NAME_MANGLED,
     "refinement": "its faithful real patch keys each collected entry on the member's "
                   "rendered value instead of on the member's name. Every entry would "
                   "be titled with its own value, so the requested-name lookup finds "
                   "nothing and the rendered heading for every module variable is "
                   "wrong; the FAIL_TO_PASS tests pin those headings exactly, so it "
                   "does NOT resolve.",
     "rationale": "attacks the `name` component of every entry — the fourth field the "
                  "clause pins and the only one no other rival here touches, so without "
                  "this case a rival mishandling only the entry key would verify. "
                  "Witness at one visible name whose looked-up value differs from it: "
                  "gold records the entry under \"a\", the rival under \"v\". Built both "
                  "ways (rival exit 0, gold exit 1)."},
    {"id": "table-order-reversed", "kind": "uniqueness", "expect": "reject",
     "module": _R_TABLE_ORDER, "witness": _W_TABLE_ORDER,
     "refinement": "its faithful real patch accumulates the collected entries in "
                   "reverse, so a module's members are returned — and rendered — in the "
                   "opposite of the stable order the collection is specified to use. "
                   "Every entry is individually correct, but the FAIL_TO_PASS and "
                   "PASS_TO_PASS tests compare the rendered output against an exact "
                   "ORDERED list, so a reversed member order fails them and it does NOT "
                   "resolve.",
     "rationale": "attacks the ORDER of the entry table itself. `request-order-ignored` "
                  "attacks ordering only on the request-mode arm, which is indexed by "
                  "the request rather than by the table; the two all-members modes "
                  "return the table directly, and its order was pinned but unattacked. "
                  "Witness at two visible names in all-members mode with no export "
                  "list, where every field of every entry agrees with gold and only the "
                  "sequence differs. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "absent-request-fabricated", "kind": "uniqueness", "expect": "reject",
     "module": _R_ABSENT_FABRICATED, "witness": _W_ABSENT_FABRICATED,
     "refinement": "its faithful real patch answers a requested name that the module "
                   "does not have by fabricating an entry for it — carrying the "
                   "annotation-only sentinel and whatever text the source records — "
                   "instead of skipping it. A documentation build naming a nonexistent "
                   "member would render a phantom entry for it rather than omitting it, "
                   "so the rendered output no longer matches the exact expected list the "
                   "tests pin, and it does NOT resolve.",
     "rationale": "attacks the drop-unresolvable-requests half of the request-mode arm "
                  "(`memberlist.filterMap …`, which yields NOTHING for a name with no "
                  "collected entry). `request-order-ignored`'s witness names only "
                  "collected names, so this half of the clause was pinned but "
                  "unattacked; this rival is correct on every such request and wrong "
                  "exactly where a request names a name the table does not have. It is "
                  "the only witness whose `memberlist` names an uncollected name: gold "
                  "returns the empty list, the rival one fabricated entry. Built both "
                  "ways (rival exit 0, gold exit 1)."},
]
