"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9673 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_augment`` STATEMENT stays
byte-identical). ``expect="verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect="reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

DEFENDED SURFACE — ONE modeled behavior, a pure two-input → one-output map:

    problem_spec_augment (fields : List (List String))
                         (annotations : List (String × String))
                         (result : List (String × String)) : Prop
      := result = augmentSpec fields annotations

  ``fields`` is a documentation field list, each marker already split by the
  caller into whitespace-separated tokens. ``annotations`` is the ordered
  name→declared-type-text table (the result's own type filed under the name
  ``return``). ``result`` is the list of fields the procedure appends.

  The postcondition is a single EQUALITY, so it has no conjuncts to split — but
  the right-hand side ``augmentSpec`` is a composition of FOUR independently
  attackable sub-decisions, and a rival that gets any one of them wrong is a
  rival that satisfies neither the equality nor any weakening of it:

    (C-desc)  the marker cascade's description side — which markers record a
              described name, INCLUDING that BOTH result-keyword spellings (the
              short and the plural) record a result description;
    (C-type)  the marker cascade's declared-type side — which markers record a
              typed name, and that the result-type marker records a TYPED name
              rather than a described one;
    (C-out)   the per-name back-fill predicate over the table — a ``type <name>``
              field is appended exactly for a name that is described AND not
              already typed, with the result keywords (both spellings) skipped,
              in TABLE ORDER;
    (C-rtype) the trailing result-type field — appended exactly when the table
              carries a result type AND the field list shows a result
              description AND no result type already.

  No output component is left free: ``result`` is pinned to a total function of
  the two inputs, so a rival cannot put anything anywhere unconstrained.

CARRIER NOTE — this carrier COMPUTES, so every witness is literal. Unlike the
opaque-callee bundles, this spec is stated entirely over ``List``/``String``
literals and structural operations (``headD``, ``length``, ``drop``,
``List.contains``, ``String.intercalate``, ``List.lookup``, ``++``) that reduce
in the kernel. Every one of the ten refutation witnesses below therefore states
``¬ problem_spec_augment <literal fields> <literal annotations> (implementation_augment …)``
and closes by ``decide`` at a CONCRETE input — no hypothesis binders at all, so
the gate's consistency probe has nothing to probe and no witness can be a
forgery-from-contradiction. Each was built twice by hand before shipping: it
elaborates against its rival, and on the frozen solution ``decide`` reports
"proved that the proposition is false" — i.e. gold demonstrably SATISFIES the
spec at exactly the point the rival violates it.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / INPUT-CLOBBER MUTATION — EXPRESSIBLE, and SHIPPED (corrected in
    audit; the port had recorded this lane VACUOUS with no substitute). Lean is
    referentially transparent, so the nagini sibling's rival LITERALLY — a store
    through a half-permission reference, rejected by the permission system rather
    than by a value mismatch — has no instance here: there is no permission to
    violate. But the BEHAVIOURAL content of that probe does: the procedure must
    classify the field list it was GIVEN, and an impl that rebinds its own input
    and overwrites every marker before walking it is a wrong impl this carrier
    expresses exactly. ``w-input-clobbered-before-classify`` is that rival, and it
    discriminates by evaluation like every other reject case here (measured:
    variant does not verify, witness elaborates against the rival, and on the
    frozen solution ``decide`` reports the proposition false). Recording the lane
    as inexpressible was a false omission, not a carrier limit.

  * DIVERGENCE / NON-TERMINATION — EXPRESSIBLE but NOT WITNESSABLE, i.e. a KNOWN
    LIMITATION of this battery rather than a vacuous class (corrected in audit;
    the port had claimed "a diverging implementation cannot be written at all",
    which is false, and had called the class vacuous, which overstates the
    battery's completeness). The frozen bundle sets no
    ``loom.semantics.termination`` option at all — this is the plain lean carrier
    — and while ``implementation_augment`` is a total ``def``, ``variant_scope``
    admits a ``partial def`` helper, so a diverging rival IS writable and in
    scope:

        partial def spin (n : Nat) : List (String × String) :=
          if n == 0 then spin 1 else spin (n + 1)
        def implementation_augment (fields) (annotations) := spin fields.length

    Measured, that rival is in scope and does NOT verify (`Tactic `rfl` failed:
    ... spin fields.length is not definitionally equal to ...`), so the spec is
    not hollow there. What cannot be built is an ATTRIBUTING witness, which is
    why no reject case is shipped for it:
      - a literal ``decide`` witness gets STUCK rather than deciding —
        ``its `Decidable` instance instDecidableNot did not reduce to `isTrue` or
        `isFalse``` — which is exactly the gate's ``_STUCK_REDUCTION`` screen, so
        the case would be recorded ``witness-undecided`` (a gate FAILURE), not a
        refutation;
      - a HYPOTHESIS-conditioned witness (binding the output and asserting it
        differs from the computed answer) elaborates against the rival AND
        against the frozen solution — measured exit 0 on both — so it is
        ``witness-vacuous``: it holds of gold, hence discriminates nothing. The
        gate's consistency probe cannot rescue it either (probe could not derive
        ``False``, so the hypotheses read as satisfiable).
    So the class is a documented hole in what this battery can attest, stated with
    the errors actually observed rather than asserted to be impossible.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as in nagini and for the same
    reason. The decision logic under specification is modeled DEEPLY
    (``classifyStep`` / ``classify`` / ``outStep`` / ``augmentSpec`` are ordinary
    folds fully unfolded from the two inputs); the bundle declares no
    ``opaque`` and no ``axiom``. There is no answer-key term an implementation
    could echo without doing the per-marker and per-table-entry work. The nagini
    sibling discharged this lane with an honest cheapest-impl positive control
    instead of a reject case, and so does this port (``pos-delegate-spec-folds``).

  * VALUE / PARTIAL-DOMAIN / CONTROL-FLOW / ORDER — the real attacks, and every
    reject case below lives here.

CASE-COUNT vs NAGINI (14 here vs 9 there — but the correspondence, not the count,
is the point). The nagini sibling contracted TWO functions over an abstract
integer field-code carrier: ``augment_return_typefield(field_kinds, ...)`` (a
BOOLEAN "should a result-type field be emitted", with the marker kinds abstracted
to the integer codes 0/2/3/4) and a separate scalar predicate deciding whether a
table name is a result key. This lean bundle folds BOTH of those decisions into
the ONE modeled procedure and widens the carrier from integer codes to actual
token lists and an actual name→type table — so the mapping is:

  - nagini S1 "rtype branch checked first"                -> pos-marker-branch-reorder
  - nagini S2 "description disjunction reordered"         -> pos-spelling-disjunction-reorder
  - nagini S3 "echo-attempt-honest" (grounded oracle)     -> pos-delegate-spec-folds
  - nagini S4 "admissibility, F2P-shaped self-call"       -> admiss-ground-f2p-shaped
  - nagini U2 "short result spelling only" (THE bug)      -> w-short-spelling-only
  - nagini U3 "plural spelling dropped at first field"    -> w-drop-leading-plural
  - nagini U4 "result-type marker treated as description" -> w-rtype-marker-as-description
  - nagini U5 "table result key, short spelling only"     -> w-table-skip-short-only
  - nagini U1 "frame mutation under half permission"      -> w-input-clobbered-before-classify
                                                             (ADDED IN AUDIT: the permission
                                                             MECHANISM has no analogue, but the
                                                             behavioural probe — does the
                                                             procedure classify the input it was
                                                             given? — does, and is shipped.)

FIVE rivals have NO nagini counterpart, because the nagini carrier could not
express them: its hunk-1 function returned a single BOOLEAN over abstract integer
codes, so it had no observable output ORDER, no per-name back-fill predicate, no
``type``-marker path, and no marker TOKEN-COUNT sub-cases at all (one integer code
per marker, hence no multi-token name). Those are (C-out) and (C-type) surface
this bundle really models, so leaving them unattacked would leave two of the four
sub-decisions with no rival built to abuse them:
  w-backfill-ignores-description (C-out predicate), w-backfill-reverse-order
  (C-out order), w-rtype-ignores-description (C-rtype guard),
  w-type-marker-not-recorded (C-type), and w-param3-type-not-recorded (C-type on
  the parameter marker's combined name-and-type form). Their refinement notes
state HONESTLY which of them the listed F2P/P2P set would and would not by itself
distinguish, so the manifest never claims a verify-does-not-resolve break it
cannot demonstrate.

The AXIOM_TESTS lane is dropped: it is G-AX's job and this gate ignores it
(meta.json records no consumed axiom — the decision logic is a deep model, not an
axiomatized callee).

WITNESS SPREAD (binder + sub-decision coverage). pts = 10 distinct probe points,
no two rivals sharing one, and BOTH input binders varied in length and in shape:

  case                             fields                          annotations                     sub-decision
  w-short-spelling-only            [[param,x],[returns]]           [(return,int)]                  (C-desc), plural spelling
  w-drop-leading-plural            [[returns]]                     [(return,int)]                  (C-desc), leading-marker sub-domain
  w-rtype-marker-as-description    [[rtype]]                       [(return,int)]                  (C-type) / (C-desc) crossover
  w-table-skip-short-only          [[param,returns]]               [(returns,int)]                 (C-out) result-key skip, plural
  w-backfill-ignores-description   []                              [(a,int)]                       (C-out) described-and-untyped predicate
  w-rtype-ignores-description      [[param,x]]                     [(return,int)]                  (C-rtype) result-description guard
  w-backfill-reverse-order         [[param,a],[param,b]]           [(a,int),(b,str)]               (C-out) table order
  w-type-marker-not-recorded       [[param,a],[type,a]]            [(a,int)]                       (C-type) declared-type marker
  w-param3-type-not-recorded       [[param,int,my,name]]           [(my name,T)]                   (C-type) param marker's combined name+type form
  w-input-clobbered-before-classify [[param,a]]                    [(a,int)]                       frame analogue: classify the GIVEN input

``fields`` is varied in OUTER length (0, 1, 2) and in marker head (``param``,
``type``, ``return``, ``returns``, ``rtype``); it is ALSO varied in INNER length —
the per-marker token count — across 1 token (``[returns]``, ``[rtype]``), 2
(``[param,x]``, ``[type,a]``) and 4 (``[param,int,my,name]``), which is what
separates the parameter marker's two-token form from its three-or-more-token form
and is the only place ``joinSp``'s multi-token join is observable in a recorded
name. ``annotations`` is varied in length (1, 2), in key (a documented name, a
multi-word documented name, and each result-keyword spelling), and in whether the
probed name is present in the table at all.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9673"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swap_all(src, old, new, count):
    """Replace EVERY occurrence of `old`, asserting the expected multiplicity.

    Used only for the marker cascade, which the frozen proof renders three times
    (the loop-refinement statement, its `hbody` normalisation, and the bridge
    lemma's hypothesis). A reshape of the cascade must edit all three renderings
    together or the proof region no longer typechecks — and all three lie inside
    the proof region, which a re-proving positive control may touch.
    """
    if src.count(old) != count:
        raise AssertionError(f"expected {count} of {old!r}, got {src.count(old)}")
    return src.replace(old, new)


# ---------------------------------------------------------------------------
# Region anchors.
#
# The impl-region anchors use the loop-local `p0` / `name` binders, which occur
# ONLY in the impl region (the proof region renders the same cascade over
# `parts.headD ""` / `entry.1`), so each is unique in _BASE and lies entirely
# inside the region it names. `_GOLD_IMPL` / `_GOLD_PROOF` are the full region
# bodies, extracted rather than spelled out so they cannot drift.
# ---------------------------------------------------------------------------

# (impl) the two adjacent result-keyword branches of the marker cascade.
_I_RESULT_BRANCHES = '''    else if p0 == "return" || p0 == "returns" then
      hasDesc := hasDesc ++ ["return"]
    else if p0 == "rtype" then
      hasType := hasType ++ ["return"]'''

# (impl) just the description branch of the marker cascade.
_I_DESC_BRANCH = '''    else if p0 == "return" || p0 == "returns" then
      hasDesc := hasDesc ++ ["return"]'''

# (impl) the declared-type marker branch of the marker cascade.
_I_TYPE_BRANCH = '''    else if p0 == "type" then
      hasType := hasType ++ [joinSp (parts.drop 1)]'''

# (impl) the THREE-OR-MORE-token form of the `param` marker branch — the only
# path that records a name on BOTH sides of the cascade at once, and the only
# one whose name is a multi-token JOIN rather than a single token.
_I_PARAM3_BRANCH = '''      else if parts.length > 2 then
        let name := joinSp (parts.drop 2)
        hasDesc := hasDesc ++ [name]
        hasType := hasType ++ [name]'''

# (impl) the head of the marker loop (where a per-iteration flag can be seeded).
_I_LOOP1_HEAD = '''  let mut hasDesc : List String := []
  let mut hasType : List String := []
  for parts in fields do'''

# (impl) the tail of the marker loop (where such a flag can be cleared).
_I_LOOP1_TAIL = '''    else
      pure ()
  let mut out : List (String × String) := []'''

# (impl) the back-fill loop's result-key skip + described-and-untyped predicate.
_I_BACKFILL_GUARD = '''    if name == "return" || name == "returns" then
      pure ()
    else if hasDesc.contains name && !hasType.contains name then'''

# (impl) the back-fill loop header (where the traversal order lives).
_I_BACKFILL_HEADER = '''  for entry in annotations do
    let (name, ann) := entry'''

# (impl) the trailing result-type field's guard.
_I_RTYPE_GUARD = '''    if hasDesc.contains "return" && !hasType.contains "return" then
      out := out ++ [("rtype", ann)]'''

for _a in (_I_RESULT_BRANCHES, _I_DESC_BRANCH, _I_TYPE_BRANCH, _I_PARAM3_BRANCH,
           _I_LOOP1_HEAD, _I_LOOP1_TAIL, _I_BACKFILL_GUARD, _I_BACKFILL_HEADER,
           _I_RTYPE_GUARD):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift, not unique: {_a!r}")


def _region(tag):
    a = _BASE.index(f"-- {tag}-start\n") + len(f"-- {tag}-start\n")
    b = _BASE.index(f"\n-- {tag}-end")
    return _BASE[a:b]


_GOLD_IMPL = _region("impl")
_GOLD_PROOF = _region("proof")

# (proof) the frozen obligation's opening two lines — the insertion point for the
# admissibility positive's ground `have`. Inside the proof region; the theorem
# STATEMENT above it is untouched.
_P_OBLIGATION_INTRO = "  intro fields annotations\n  show implementation_augment"
if _BASE.count(_P_OBLIGATION_INTRO) != 1:
    raise AssertionError("anchor drift: obligation intro not unique")


# ===========================================================================
# POSITIVE CONTROLS — structurally different but CORRECT. Each keeps the
# `theorem correct_augment` STATEMENT byte-identical, adds no helper
# theorem/lemma/axiom and no assumption token, and re-closes the obligation
# honestly for its own impl shape. A failure to verify here is SPEC-TOO-STRONG.
# ===========================================================================

# (P1) == nagini S1. Reorder the two ADJACENT result-keyword branches of the
# marker cascade: the declared-result-type marker is tested BEFORE the
# result-description markers. The three marker heads are mutually exclusive per
# marker, so the classification is identical on every input. Because the frozen
# proof renders the cascade three times inside the proof region, all three
# renderings are reordered to match, and the two `split_ifs <;> rfl` discharges
# become `split_ifs <;> first | rfl | simp_all` (reordering the branches makes
# some of the resulting cases need the head-equality hypotheses rather than
# closing by reflexivity alone).
def _pos_marker_branch_reorder():
    m = _swap(_BASE, _I_RESULT_BRANCHES,
              '''    else if p0 == "rtype" then
      hasType := hasType ++ ["return"]
    else if p0 == "return" || p0 == "returns" then
      hasDesc := hasDesc ++ ["return"]''')
    m = _swap(m, '''      else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
        (acc.1 ++ ["return"], acc.2)
      else if (parts.headD "" == "rtype") = true then (acc.1, acc.2 ++ ["return"])''',
              '''      else if (parts.headD "" == "rtype") = true then (acc.1, acc.2 ++ ["return"])
      else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
        (acc.1 ++ ["return"], acc.2)''')
    m = _swap(m, '''      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]''',
              '''      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]
  split_ifs <;> first | rfl | simp_all''')
    m = _swap_all(m, '''          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩
          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩''',
                  '''          else if (parts.headD "" == "rtype") = true then
            ForInStep.yield ⟨r.fst, r.snd ++ ["return"]⟩
          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩''', 3)
    return _swap(m, '''    funext parts r
    simp only [classifyStep]
    split_ifs <;> rfl''',
                 '''    funext parts r
    simp only [classifyStep]
    split_ifs <;> first | rfl | simp_all''')


# (P2) == nagini S2. Reorder the two spellings INSIDE the result-description
# disjunction (the plural spelling tested first). Semantically identical — it is
# membership of the marker head in a two-element set — so this confirms the spec
# is not over-fit to the literal disjunction order. Same three-rendering
# discipline as P1.
def _pos_spelling_disjunction_reorder():
    m = _swap(_BASE, _I_DESC_BRANCH,
              '''    else if p0 == "returns" || p0 == "return" then
      hasDesc := hasDesc ++ ["return"]''')
    m = _swap(m, '''      else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
        (acc.1 ++ ["return"], acc.2)''',
              '''      else if (parts.headD "" == "returns" || parts.headD "" == "return") = true then
        (acc.1 ++ ["return"], acc.2)''')
    m = _swap(m, '''      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]''',
              '''      else (acc.1, acc.2)) = classifyStep acc parts := by
  simp only [classifyStep]
  split_ifs <;> first | rfl | simp_all''')
    m = _swap_all(m, '''          else if (parts.headD "" == "return" || parts.headD "" == "returns") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩''',
                  '''          else if (parts.headD "" == "returns" || parts.headD "" == "return") = true then
            ForInStep.yield ⟨r.fst ++ ["return"], r.snd⟩''', 3)
    return _swap(m, '''    funext parts r
    simp only [classifyStep]
    split_ifs <;> rfl''',
                 '''    funext parts r
    simp only [classifyStep]
    split_ifs <;> first | rfl | simp_all''')


# (P3) == nagini S3 (echo-attempt-honest), re-aimed at this carrier. The oracle
# here is GROUNDED — the spec's right-hand side is an ordinary fold of the two
# inputs, with nothing opaque to echo — so the honest analogue of nagini's
# "cheapest impl that still does the work" is an impl that delegates each loop
# body to the spec's OWN pure step functions instead of re-spelling the cascade
# inline. It collapses the mutable pair into one accumulator and drops the
# `(name, ann)` destructuring; it must still traverse every marker and every
# table entry, which is the point: there is no shortcut that bypasses the
# per-element work. The proof is re-closed for the new loop shape by two
# accumulator-generalising inductions inlined as `have`s (no new top-level
# lemma), replacing the frozen four-lemma chain.
_P3_IMPL = '''def implementation_augment (fields : List (List String))
    (annotations : List (String × String)) : List (String × String) := Id.run do
  let mut acc : List String × List String := ([], [])
  for parts in fields do
    acc := classifyStep acc parts
  let mut out : List (String × String) := []
  for entry in annotations do
    out := outStep acc.1 acc.2 out entry
  match annotations.lookup "return" with
  | some ann =>
    if acc.1.contains "return" && !acc.2.contains "return" then
      out := out ++ [("rtype", ann)]
  | none => pure ()
  return out'''

_P3_PROOF = '''theorem correct_augment : ∀ (fields : List (List String))
    (annotations : List (String × String)),
    problem_spec_augment fields annotations
      (implementation_augment fields annotations) := by
  intro fields annotations
  show implementation_augment fields annotations = augmentSpec fields annotations
  -- The marker loop, delegating its body to `classifyStep`, is that fold.
  have h1 : ∀ (fs : List (List String)) (init : List String × List String),
      (forIn (m := Id) fs init fun parts r => ForInStep.yield (classifyStep r parts))
        = fs.foldl classifyStep init := by
    intro fs
    induction fs with
    | nil => intro init; rfl
    | cons p ps ih => intro init; simp only [List.forIn_cons]; exact ih _
  -- Likewise the back-fill loop and the `outStep` fold, for any fixed pair of
  -- described / typed name collections.
  have h2 : ∀ (hd ht : List String) (es : List (String × String))
      (init : List (String × String)),
      (forIn (m := Id) es init fun entry r => ForInStep.yield (outStep hd ht r entry))
        = es.foldl (outStep hd ht) init := by
    intro hd ht es
    induction es with
    | nil => intro init; rfl
    | cons e rest ih => intro init; simp only [List.forIn_cons]; exact ih _
  unfold implementation_augment
  simp only [Id.run, bind, pure, h1, h2, augmentSpec, classify]
  rfl'''


# (P4) == nagini S4 (admissibility). The frozen obligation quantifies over both
# inputs with NO precondition hypothesis, so there is no `Requires` to admit;
# the honest analogue of nagini's "a normal input establishes the precondition"
# probe is to show the spec is SATISFIABLE at a ground input of exactly the shape
# the F2P exercises (a described name plus a result description under the plural
# spelling, with both a per-name and a result type in the table), discharged by
# `decide`, and then to close the frozen obligation verbatim. Nothing is assumed:
# no new declaration, the theorem statement is byte-identical, the ground
# instance is a `have` inside the existing tactic body.
_P4_GROUND = (
    '  have _ground : problem_spec_augment [["param", "x"], ["returns"]]\n'
    '      [("x", "int"), ("return", "int")]\n'
    '      (implementation_augment [["param", "x"], ["returns"]]\n'
    '        [("x", "int"), ("return", "int")]) := by\n'
    "    unfold problem_spec_augment\n"
    "    decide\n"
    + _P_OBLIGATION_INTRO
)


# ===========================================================================
# UNIQUENESS RIVALS — wrong impls sharing the frozen spec. Each keeps the frozen
# proof body verbatim, which no longer closes for the reshaped impl, so the file
# does not verify; and each carries a `witness` BUILT BOTH WAYS by hand (it
# elaborates against its rival; on the frozen solution `decide` reports the
# proposition false, so gold satisfies the spec at that exact input).
# ===========================================================================

# (U1) == nagini U2, THE discriminating rival. Only the SHORT result-keyword
# spelling records a result description; the plural spelling falls through to the
# cascade's default and records nothing.
_R_SHORT_SPELLING_ONLY = _swap(_BASE, _I_DESC_BRANCH,
                               '''    else if p0 == "return" then
      hasDesc := hasDesc ++ ["return"]''')

# (U2) == nagini U3. The plural spelling IS recognised — except when its marker
# is the FIRST of the field list, where it is ignored. Pins only the sub-domain
# of field lists whose leading marker is not a plural result description.
_R_DROP_LEADING_PLURAL = _swap(
    _swap(
        _swap(_BASE, _I_LOOP1_HEAD,
              '''  let mut hasDesc : List String := []
  let mut hasType : List String := []
  let mut first : Bool := true
  for parts in fields do'''),
        _I_DESC_BRANCH,
        '''    else if p0 == "return" || (p0 == "returns" && !first) then
      hasDesc := hasDesc ++ ["return"]'''),
    _I_LOOP1_TAIL,
    '''    else
      pure ()
    first := false
  let mut out : List (String × String) := []''')

# (U3) == nagini U4. The declared-result-type marker records a DESCRIBED name
# instead of a typed one, so it never records that the result already carries a
# declared type.
_R_RTYPE_MARKER_AS_DESCRIPTION = _swap(_BASE, _I_RESULT_BRANCHES,
                                       '''    else if p0 == "return" || p0 == "returns" then
      hasDesc := hasDesc ++ ["return"]
    else if p0 == "rtype" then
      hasDesc := hasDesc ++ ["return"]''')

# (U4) == nagini U5, the second defended decision, which this bundle folds into
# the same procedure's table walk: the back-fill loop skips a table entry named
# with the SHORT result keyword only, so an entry named with the plural spelling
# is treated as an ordinary documented name.
_R_TABLE_SKIP_SHORT_ONLY = _swap(_BASE, _I_BACKFILL_GUARD,
                                 '''    if name == "return" then
      pure ()
    else if hasDesc.contains name && !hasType.contains name then''')

# (U5) NO nagini counterpart — the nagini hunk-1 surface returned a single
# boolean over abstract integer codes and had no per-name back-fill predicate at
# all. This rival drops the described-name requirement from that predicate,
# appending a `type <name>` field for any table name not already typed, whether
# or not it carries a description.
_R_BACKFILL_IGNORES_DESCRIPTION = _swap(_BASE, _I_BACKFILL_GUARD,
                                        '''    if name == "return" || name == "returns" then
      pure ()
    else if !hasType.contains name then''')

# (U6) NO nagini counterpart (same reason). The trailing result-type field's
# guard drops the result-DESCRIPTION requirement, appending it whenever the
# result is not already typed.
_R_RTYPE_IGNORES_DESCRIPTION = _swap(_BASE, _I_RTYPE_GUARD,
                                     '''    if !hasType.contains "return" then
      out := out ++ [("rtype", ann)]''')

# (U7) NO nagini counterpart: the nagini boolean surface had no observable output
# ORDER. This rival walks the table in reverse, so the appended per-name fields
# come out in reverse table order.
_R_BACKFILL_REVERSE_ORDER = _swap(_BASE, _I_BACKFILL_HEADER,
                                  '''  for entry in annotations.reverse do
    let (name, ann) := entry''')

# (U8) NO nagini counterpart: the nagini integer-code carrier had no
# declared-type marker path. This rival's cascade no longer records a typed name
# for a declared-type marker, so a name whose type is already declared in the
# field list still looks untyped.
_R_TYPE_MARKER_NOT_RECORDED = _swap(_BASE, _I_TYPE_BRANCH,
                                    '''    else if p0 == "type" then
      pure ()''')

# (U9) NO nagini counterpart (the nagini carrier abstracted every marker to a
# single integer code, so it had no token-count sub-cases and no multi-token
# name at all). ADDED IN AUDIT: the parameter marker's three-or-more-token form
# is the ONLY cascade path that records a name on BOTH sides at once, and the
# only one whose recorded name is a multi-token JOIN rather than a bare token.
# Every other rival leaves it untouched, so both properties went unattacked.
# This rival records the described name but not the typed one, so a name whose
# type the marker itself already carries still looks untyped.
_R_PARAM3_TYPE_NOT_RECORDED = _swap(_BASE, _I_PARAM3_BRANCH,
                                    '''      else if parts.length > 2 then
        let name := joinSp (parts.drop 2)
        hasDesc := hasDesc ++ [name]''')

# (U10) == nagini U1, the MANDATORY frame-mutation probe, ported to the analogue
# this carrier actually has. ADDED IN AUDIT: the port had recorded this lane
# VACUOUS with no substitute, on the ground that Lean has no permission to
# violate. The MECHANISM indeed has no analogue — there is no heap, no aliasing
# and no fractional read permission — but the BEHAVIOUR the nagini rival probes
# does: "does the procedure classify the field list it was GIVEN, or something
# else?" This rival shadows its own input binder and overwrites every marker with
# a declared-result-type marker before walking it, so the classification is
# computed from fabricated input rather than from `fields`. In scope
# (`variant_problems` clean: impl region only, statement byte-identical, no new
# declaration or assumption token) and refuted by evaluation like every other
# reject case here.
_R_INPUT_CLOBBERED = _swap(_BASE, _I_LOOP1_HEAD,
                           '''  let mut hasDesc : List String := []
  let mut hasType : List String := []
  let mut fields := fields
  fields := fields.map (fun _ => ["rtype"])
  for parts in fields do''')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS — MUST verify.
    # =====================================================================
    {
        "id": "pos-marker-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_marker_branch_reorder(),
        "rationale": "== nagini S1. The two adjacent result-keyword branches of "
                     "the marker cascade are reordered so the declared-result-type "
                     "marker is tested BEFORE the result-description markers. The "
                     "three marker heads are mutually exclusive per marker, so the "
                     "described/typed name collections — and hence the whole "
                     "equality (C-desc, C-type, C-out, C-rtype) — are identical on "
                     "every input. If this fails to verify, the postcondition is "
                     "over-fit to one branch order => SPEC-TOO-STRONG. The proof "
                     "region renders the same cascade three times (the "
                     "loop-refinement statement, its `hbody` normalisation, and the "
                     "bridge lemma's hypothesis); all three are reordered together "
                     "and the two `split_ifs <;> rfl` discharges widened to "
                     "`first | rfl | simp_all`, since reordering makes some cases "
                     "need the marker-head equalities rather than closing by "
                     "reflexivity. Theorem statement byte-identical; no new "
                     "theorem/lemma/axiom/assumption token.",
    },
    {
        "id": "pos-spelling-disjunction-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_spelling_disjunction_reorder(),
        "rationale": "== nagini S2. The two result-keyword spellings are reordered "
                     "INSIDE the result-description disjunction (the plural tested "
                     "first). This is membership of the marker head in a "
                     "two-element set, so it is semantically identical; verifying "
                     "confirms the spec is not over-fit to the literal disjunction "
                     "order. If it fails => SPEC-TOO-STRONG. Same "
                     "three-rendering-plus-widened-discharge discipline as "
                     "pos-marker-branch-reorder; statement byte-identical, nothing "
                     "new declared.",
    },
    {
        "id": "pos-delegate-spec-folds",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _P3_IMPL), _GOLD_PROOF, _P3_PROOF),
        "rationale": "== nagini S3 (echo-attempt-honest), re-aimed at this carrier. "
                     "The oracle is GROUNDED — the spec's right-hand side is an "
                     "ordinary fold of the two inputs, with no opaque term to echo "
                     "— so the honest analogue of nagini's cheapest-impl control is "
                     "an impl that delegates each loop body to the spec's own pure "
                     "step functions rather than re-spelling the cascade inline, "
                     "collapsing the mutable pair into one accumulator and dropping "
                     "the entry destructuring. It must still traverse every marker "
                     "and every table entry, which is the point: there is no "
                     "shortcut past the per-element work, so this is a reshape and "
                     "not an echo. It must satisfy the equality on every input; if "
                     "it cannot => SPEC-TOO-STRONG. Re-proved for the new loop "
                     "shape by two accumulator-generalising inductions inlined as "
                     "`have`s inside the existing tactic body — no new top-level "
                     "lemma, no axiom, no assumption token, statement "
                     "byte-identical.",
    },
    {
        "id": "admiss-ground-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_OBLIGATION_INTRO, _P4_GROUND),
        "rationale": "== nagini S4. The frozen obligation quantifies over both "
                     "inputs with NO precondition hypothesis, so there is no "
                     "`Requires` to admit; the honest analogue of nagini's "
                     "'a normal input establishes the precondition' probe is to "
                     "show the spec is SATISFIABLE at a ground input of exactly the "
                     "shape the F2P exercises — a described name plus a result "
                     "description under the plural spelling, with both a per-name "
                     "and a result type in the table — discharged by `decide`, and "
                     "then to close the frozen obligation verbatim. Verifies iff "
                     "the spec admits a normal input (else the PRECOND-TOO-STRONG "
                     "analogue: a spec no ordinary input can satisfy). Nothing is "
                     "assumed — the ground instance is a `have` inside the existing "
                     "tactic body, the theorem statement is byte-identical, and no "
                     "declaration is added.",
    },

    # =====================================================================
    # UNIQUENESS RIVALS — MUST be rejected. Every witness is literal and closes
    # by `decide`; each was built against its rival (elaborates) and against the
    # frozen solution (`decide` proves the proposition false, i.e. gold satisfies
    # the spec there). No witness binds a hypothesis, so none can be a
    # forgery-from-contradiction.
    # =====================================================================
    {
        "id": "w-short-spelling-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SHORT_SPELLING_ONLY,
        "refinement": "== nagini U2, and THE discriminating rival. Only the SHORT "
                      "result-keyword spelling records a result description; a "
                      "marker headed by the plural spelling falls through to the "
                      "cascade's default and records nothing, so no trailing "
                      "result-type field is ever appended for it. On the whole "
                      "sub-domain of field lists carrying no plural-spelled result "
                      "marker it agrees with the frozen solution exactly. Its "
                      "faithful real patch is the base-commit code, and the F2P "
                      "(`test_autodoc_typehints_description_no_undoc`) asserts that "
                      "a function whose only documented field is a plural-spelled "
                      "result description still gets a rendered result-type "
                      "section: this rival emits none there, so that patch FAILS "
                      "the F2P and does NOT resolve. A verifying rival here would "
                      "be a true verify-does-not-imply-resolve break.",
        "rationale": "REJECT from (C-desc): the description side of the marker "
                     "cascade must record a result description under EITHER "
                     "spelling, and via (C-rtype) that recording is what licenses "
                     "the trailing result-type field. Refuted at "
                     "fields=[[param,x],[returns]] with annotations=[(return,int)] "
                     "— a plural-spelled result marker present, no per-name type in "
                     "the table — where the frozen solution appends the trailing "
                     "result-type field and this rival appends nothing. Literal "
                     "input, `decide`, no binders. If it verified => SPEC-TOO-WEAK "
                     "(the spec admits recognising only one spelling).",
        "witness": ('example : ¬ problem_spec_augment [["param", "x"], ["returns"]]\n'
                    '    [("return", "int")]\n'
                    '    (implementation_augment [["param", "x"], ["returns"]]\n'
                    '      [("return", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-drop-leading-plural",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_LEADING_PLURAL,
        "refinement": "== nagini U3. A near-miss that DOES recognise the plural "
                      "spelling, everywhere except when its marker is the FIRST of "
                      "the field list. It therefore agrees with the frozen solution "
                      "on strictly more of the domain than "
                      "w-short-spelling-only, which is why it gets its own witness "
                      "at a distinguishing input rather than sharing one. Its "
                      "faithful real patch special-cases the leading marker, and "
                      "the F2P documents a function whose plural-spelled result "
                      "description IS its only (hence leading) field — so that "
                      "patch still emits no result-type section there, FAILS the "
                      "F2P, and does NOT resolve.",
        "rationale": "REJECT from (C-desc) on the leading-marker sub-domain: the "
                     "cascade is a fold with no positional dependence, so a "
                     "plural-spelled result marker must record a result description "
                     "wherever it sits. Refuted at the single-marker field list "
                     "fields=[[returns]] with annotations=[(return,int)] — the "
                     "input this rival's carve-out covers and "
                     "w-short-spelling-only's two-marker witness does not isolate. "
                     "Literal input, `decide`, no binders. If it verified => "
                     "SPEC-TOO-WEAK (domain-incomplete: the spec would not pin the "
                     "leading marker).",
        "witness": ('example : ¬ problem_spec_augment [["returns"]] [("return", "int")]\n'
                    '    (implementation_augment [["returns"]] [("return", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-rtype-marker-as-description",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_RTYPE_MARKER_AS_DESCRIPTION,
        "refinement": "== nagini U4. A marker declaring the result's type records a "
                      "DESCRIBED name instead of a typed one, so the procedure never "
                      "learns that the result already carries a declared type and "
                      "appends a second, redundant result-type field. HONEST "
                      "SCOPE: the listed F2P/P2P set documents no function that "
                      "already carries an explicit result-type marker under the "
                      "documented-only target, so this rival's faithful patch would "
                      "not by itself be distinguished by the listed tests — a patch "
                      "of this shape would emit a duplicate result-type section for "
                      "any real field list that does carry one, which is behaviour "
                      "the modeled surface pins and the listed tests "
                      "under-exercise. Included as a spec-strength attacker on "
                      "(C-type), stated so the manifest does not over-claim an F2P "
                      "break it cannot demonstrate here.",
        "rationale": "REJECT from (C-type), crossing into (C-rtype): the "
                     "declared-result-type marker must record a TYPED name, and it "
                     "is precisely that recording which suppresses the trailing "
                     "result-type field. Refuted at fields=[[rtype]] with "
                     "annotations=[(return,int)] — a result type already declared "
                     "in the field list — where the frozen solution appends nothing "
                     "and this rival, having filed the marker on the description "
                     "side, appends a duplicate result-type field. Literal input, "
                     "`decide`, no binders. If it verified => SPEC-TOO-WEAK (the "
                     "two sides of the cascade would be interchangeable).",
        "witness": ('example : ¬ problem_spec_augment [["rtype"]] [("return", "int")]\n'
                    '    (implementation_augment [["rtype"]] [("return", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-table-skip-short-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TABLE_SKIP_SHORT_ONLY,
        "refinement": "== nagini U5, the SECOND defended decision, which the nagini "
                      "sibling contracted as a separate scalar predicate and this "
                      "bundle folds into the same procedure's table walk: the "
                      "back-fill loop must skip a table entry named with EITHER "
                      "result-keyword spelling, and this rival skips only the short "
                      "one. HONEST SCOPE: the name→type table the F2P builds is "
                      "keyed by parameter names plus the single short result key, so "
                      "no listed test presents a table entry named with the plural "
                      "spelling; this rival's faithful patch is the base-commit "
                      "form of that guard, which the bundle's prepatch reverts, but "
                      "the listed tests would not by themselves distinguish it. "
                      "Included as a spec-strength attacker on the (C-out) "
                      "result-key skip, stated so the manifest claims no F2P break "
                      "it cannot demonstrate.",
        "rationale": "REJECT from (C-out): the per-name back-fill must skip BOTH "
                     "result-keyword spellings, treating neither as an ordinary "
                     "documented name. Refuted at fields=[[param,returns]] with "
                     "annotations=[(returns,int)] — a documented name that happens "
                     "to be spelled with the plural result keyword, described but "
                     "untyped — where the frozen solution appends nothing and this "
                     "rival appends a per-name type field for it. This is the only "
                     "witness whose `annotations` key is the plural spelling, so it "
                     "varies that binder where no other rival does. Literal input, "
                     "`decide`, no binders. If it verified => SPEC-TOO-WEAK.",
        "witness": ('example : ¬ problem_spec_augment [["param", "returns"]] [("returns", "int")]\n'
                    '    (implementation_augment [["param", "returns"]] [("returns", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-backfill-ignores-description",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_BACKFILL_IGNORES_DESCRIPTION,
        "refinement": "NO nagini counterpart: the nagini sibling's first function "
                      "returned a single boolean over abstract integer field codes "
                      "and had no per-name back-fill predicate to attack. This "
                      "rival drops the DESCRIBED requirement from that predicate, "
                      "appending a per-name type field for every table name not "
                      "already typed, whether or not the field list describes it. "
                      "The F2P documents one function with no described fields at "
                      "all and asserts that NOTHING is injected for it; a patch of "
                      "this shape would inject a type field for each of its "
                      "parameters, so it FAILS the F2P and does NOT resolve.",
        "rationale": "REJECT from (C-out): a per-name type field is appended "
                     "exactly for a name that is described AND not already typed, "
                     "so dropping the described conjunct is a strict weakening. "
                     "Refuted at the EMPTY field list fields=[] with "
                     "annotations=[(a,int)] — nothing is described, so the frozen "
                     "solution appends nothing while this rival appends a per-name "
                     "type field. The only witness probing the empty `fields` "
                     "binder, and the only one whose `annotations` key is an "
                     "ordinary documented name absent from the field list. Literal "
                     "input, `decide`, no binders. If it verified => "
                     "SPEC-TOO-WEAK.",
        "witness": ('example : ¬ problem_spec_augment [] [("a", "int")]\n'
                    '    (implementation_augment [] [("a", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-rtype-ignores-description",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_RTYPE_IGNORES_DESCRIPTION,
        "refinement": "NO nagini counterpart: nagini's boolean surface conflated "
                      "this guard with the emission decision itself, so it could "
                      "not be attacked separately. This rival drops the "
                      "result-DESCRIPTION requirement from the trailing "
                      "result-type field's guard, appending that field whenever the "
                      "result is not already typed. The F2P documents a function "
                      "with no result description and asserts no result-type "
                      "section is rendered for it; a patch of this shape renders one "
                      "anyway, so it FAILS the F2P and does NOT resolve.",
        "rationale": "REJECT from (C-rtype): the trailing result-type field is "
                     "appended only when the field list shows a result DESCRIPTION "
                     "and no result type — dropping the description conjunct "
                     "weakens the guard to the untyped test alone. Refuted at "
                     "fields=[[param,x]] with annotations=[(return,int)] — a result "
                     "type in the table but no result description among the markers "
                     "— where the frozen solution appends nothing (and no per-name "
                     "field either, `x` being absent from the table) while this "
                     "rival appends the trailing result-type field. Literal input, "
                     "`decide`, no binders. If it verified => SPEC-TOO-WEAK.",
        "witness": ('example : ¬ problem_spec_augment [["param", "x"]] [("return", "int")]\n'
                    '    (implementation_augment [["param", "x"]] [("return", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-backfill-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_BACKFILL_REVERSE_ORDER,
        "refinement": "NO nagini counterpart: the nagini boolean surface had no "
                      "observable output ORDER at all. This rival walks the "
                      "name→type table in reverse, so the appended per-name fields "
                      "come out in reverse table order. HONEST SCOPE: every function "
                      "the listed F2P/P2P set documents under the documented-only "
                      "target contributes at most ONE per-name type field, so the "
                      "listed tests could not by themselves distinguish this rival "
                      "— its faithful patch would still produce the same output on "
                      "the F2P input. Included as a pure spec-strength attacker on "
                      "the ORDER half of (C-out), which the listed tests "
                      "under-exercise but the spec pins (the table's order is "
                      "observable in the rendered field order), so the ordering "
                      "clause does not go unattacked.",
        "rationale": "REJECT from the ORDER half of (C-out): the per-name type "
                     "fields must be appended in TABLE order, so a traversal-order "
                     "change is observable even when the set of appended fields is "
                     "identical. Refuted at fields=[[param,a],[param,b]] with the "
                     "TWO-entry table annotations=[(a,int),(b,str)] — the only "
                     "witness with more than one table entry, and the only one that "
                     "probes the ordering rather than the membership of the output. "
                     "The frozen solution appends the `a` field then the `b` field; "
                     "this rival appends them the other way round. Literal input, "
                     "`decide`, no binders. If it verified => SPEC-TOO-WEAK (the "
                     "spec would pin only the multiset of appended fields).",
        "witness": ('example : ¬ problem_spec_augment [["param", "a"], ["param", "b"]]\n'
                    '    [("a", "int"), ("b", "str")]\n'
                    '    (implementation_augment [["param", "a"], ["param", "b"]]\n'
                    '      [("a", "int"), ("b", "str")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-type-marker-not-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_TYPE_MARKER_NOT_RECORDED,
        "refinement": "NO nagini counterpart: nagini abstracted the field markers "
                      "to integer codes covering only the parameter, result and "
                      "result-type kinds, so it had no declared-type marker path to "
                      "attack. This rival's cascade no longer records a typed name "
                      "for a marker that declares one, so a name whose type is "
                      "already spelled out in the field list still looks untyped "
                      "and gets a redundant type field appended. HONEST SCOPE: no "
                      "listed test feeds an explicit declared-type marker under the "
                      "documented-only target, so the listed tests would not by "
                      "themselves distinguish this rival; a patch of this shape "
                      "would duplicate the declared type for any real field list "
                      "that does carry one. Included as a spec-strength attacker on "
                      "(C-type) so the cascade's type side is not defended by the "
                      "result-marker rivals alone.",
        "rationale": "REJECT from (C-type): a declared-type marker must record a "
                     "typed name, which is what makes that name fail the "
                     "not-already-typed half of (C-out). Refuted at "
                     "fields=[[param,a],[type,a]] with annotations=[(a,int)] — a "
                     "name both described and already explicitly typed, the only "
                     "witness feeding a declared-type marker — where the frozen "
                     "solution appends nothing and this rival appends a redundant "
                     "per-name type field. Literal input, `decide`, no binders. If "
                     "it verified => SPEC-TOO-WEAK (the declared-type marker path "
                     "would be unconstrained).",
        "witness": ('example : ¬ problem_spec_augment [["param", "a"], ["type", "a"]]\n'
                    '    [("a", "int")]\n'
                    '    (implementation_augment [["param", "a"], ["type", "a"]]\n'
                    '      [("a", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-param3-type-not-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_PARAM3_TYPE_NOT_RECORDED,
        "refinement": "NO nagini counterpart: the nagini carrier abstracted every "
                      "marker to a single integer code, so it had neither a "
                      "token-count sub-case nor a multi-token name. ADDED IN AUDIT — "
                      "the parameter marker's three-or-more-token form was the one "
                      "cascade path no rival touched, and it is the only path that "
                      "records a name on BOTH sides of the cascade at once (the "
                      "marker carries the name AND its type together), as well as the "
                      "only one whose recorded name is a multi-token JOIN rather than "
                      "a bare token. This rival records the described name but not the "
                      "typed one, so a name the marker itself already types still "
                      "looks untyped and gets a redundant type field appended. HONEST "
                      "SCOPE: the listed F2P/P2P set documents its parameters with "
                      "the two-token marker form, so no listed test feeds a "
                      "three-token parameter marker and the listed tests would not by "
                      "themselves distinguish this rival; a patch of this shape would "
                      "duplicate the declared type for any real field list using the "
                      "combined form. Included as a spec-strength attacker so the "
                      "both-sides path and `joinSp`'s multi-token join are not left "
                      "unprobed.",
        "rationale": "REJECT from (C-type) on the parameter marker's multi-token "
                     "form: that form must record the joined name as TYPED as well as "
                     "described, and it is precisely the typed recording that makes "
                     "the name fail the not-already-typed half of (C-out). Refuted at "
                     "fields=[[param,int,my,name]] with annotations=[(my name,T)] — a "
                     "parameter documented with its type in one marker, whose name is "
                     "the two-word join `my name`. The frozen solution appends "
                     "nothing; this rival appends a redundant per-name type field. "
                     "The only witness feeding a marker of more than two tokens and "
                     "the only one whose recorded name is a genuine multi-token join, "
                     "so it varies the inner-list length binder where no other "
                     "witness does. Literal input, `decide`, no binders. If it "
                     "verified => SPEC-TOO-WEAK (the combined name-and-type marker "
                     "path would be unconstrained on its type side).",
        "witness": ('example : ¬ problem_spec_augment [["param", "int", "my", "name"]]\n'
                    '    [("my name", "T")]\n'
                    '    (implementation_augment [["param", "int", "my", "name"]]\n'
                    '      [("my name", "T")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
    {
        "id": "w-input-clobbered-before-classify",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_INPUT_CLOBBERED,
        "refinement": "== nagini U1, the MANDATORY frame-mutation probe, ADDED IN "
                      "AUDIT — the port had recorded this whole lane VACUOUS with no "
                      "substitute, which was a false omission. The nagini rival's "
                      "MECHANISM (a store through a half-permission reference, "
                      "rejected by the permission system rather than by a value "
                      "mismatch) genuinely has no analogue on this carrier: Lean is "
                      "referentially transparent, there is no heap, no aliasing and no "
                      "fractional permission to subvert. But the BEHAVIOUR that probe "
                      "defends does — the procedure must classify the field list it "
                      "was GIVEN — and this carrier expresses an impl that violates it "
                      "exactly: rebind the input binder and overwrite every marker "
                      "before the cascade walks it. HONEST SCOPE: no faithful real "
                      "patch corresponds to this, exactly as in nagini — the modeled "
                      "procedure only READS its field list to classify marker heads "
                      "and never rewrites one — so no listed test distinguishes it and "
                      "the manifest claims no F2P break here. Its purpose is the same "
                      "as the nagini original's: to check that the postcondition ties "
                      "the result to the ACTUAL arguments, so a rival cannot satisfy "
                      "it by computing over input of its own manufacture. A verifying "
                      "rival here would be a pure verify-does-not-resolve artifact.",
        "rationale": "REJECT because the postcondition pins `result` to "
                     "`augmentSpec fields annotations` at the ARGUMENTS the procedure "
                     "was called with — every clause (C-desc, C-type, C-out, C-rtype) "
                     "is evaluated at `fields`, not at whatever the body chooses to "
                     "put in a local of the same name. Refuted at "
                     "fields=[[param,a]] with annotations=[(a,int)] — a described, "
                     "untyped name — where the frozen solution appends the per-name "
                     "type field and this rival, having replaced the marker with a "
                     "declared-result-type marker, records nothing on the description "
                     "side and appends nothing. Literal input, `decide`, no binders. "
                     "If it verified => SPEC-TOO-WEAK (the postcondition would not be "
                     "anchored to its own inputs).",
        "witness": ('example : ¬ problem_spec_augment [["param", "a"]] [("a", "int")]\n'
                    '    (implementation_augment [["param", "a"]] [("a", "int")]) := by\n'
                    "  unfold problem_spec_augment\n"
                    "  decide\n"),
    },
]
