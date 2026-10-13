# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10673 (lean).
# NOT a Lean module; a record of adversarially-reasoned falsification cases,
# PORTED from the nagini sibling's battery. The runner writes each
# SPEC_TESTS["module"] to a temp Solution.lean, rebuilds it under the pin, and
# checks markers.same_spec against the frozen file. Every variant is built by
# region-surgery (_swap) editing ONLY text inside the impl region (and, for the
# soundness positive, the proof body), so the frozen spec — the docstring, the
# `problem_spec_tocEntries` predicate, and the `theorem correct_tocEntries`
# STATEMENT — is never touched and same_spec holds by construction.
#
# Defended surface (from Solution.lean / mapping.md):
#   tocEntries(requested, existingDocs, generatedPages) : List (Option String × String)
#   The result is pinned EXACTLY as a function of the three input lists:
#       result = (requested.filter (fun e => e != "" &&
#                  (existingDocs ++ generatedPages).contains e)).map
#                  (fun e => (none, e))
#   Three independent, load-bearing clauses of that equality:
#     (i)   the blank test `e != ""`  — a blank reference contributes no entry.
#           Note the discriminating mutation here must EMIT on the blank arm: a
#           rival that merely deletes the blank arm and falls through to the
#           membership test is behaviourally identical to gold unless a document
#           is named "" (verified by `decide`), which the modeled domain cannot
#           present — see case 4;
#     (ii)  the acceptance test — membership in the UNION of the two name
#           families (existing documents OR the special reference pages); the
#           discriminating behaviour is that a reference present in
#           `generatedPages` but absent from `existingDocs` must still be kept;
#     (iii) the shape/order — accepted references keep their listed order, each
#           emitted as `(none, e)` (no explicit title, own name as target).
#   The output is grounded entirely in the inputs (a filter+map over the actual
#   carrier), so no wrong echo of an ungrounded oracle is possible; that lane is
#   N/A and we defend with an honest structurally-different positive control.
#
# CARRIER NARROWING vs the nagini battery (see `assessment` in the payload):
#   * The nagini frame-mutation case (a write to a 1/2-permission read-only
#     input) is VACUOUS here: Lean is referentially transparent, there is no
#     fractional-permission carrier, so no rival can attack that surface. Dropped.
#   * The nagini AXIOM_TESTS lane is G-AX's job, not this gate's. Dropped.
#   * The nagini admissibility case witnessed that Acc(.,1/2) admits an F2P input.
#     Lean has no PRECONDITION to be too strong (the obligation is a bare `∀`),
#     but that is NOT a reason to drop the lane: the analogue on a total carrier
#     is the obligation being unsatisfiable at exactly an F2P-shaped input, which
#     case 6 discharges BY EVALUATION at a concrete four-reference input (one
#     ordinary document plus three special reference pages) as a `have`, before
#     closing the frozen obligation verbatim. Ported, not dropped.
#   * The nagini divergence/non-termination class is a KNOWN HOLE here, not a
#     vacuous class, and it is not shippable. Machine-checked: an impl that fails
#     to terminate must be introduced with `partial def` (Lean's elaborator
#     otherwise demands a decreasing measure), and a `partial def` is OPAQUE — it
#     has no equation lemmas, so `unfold implementation_tocEntries` fails on the
#     RIVAL side ("Tactic `unfold` failed to unfold `implementation_tocEntries`").
#     The witness therefore cannot hold of the rival, which is the half that must
#     succeed, so no admissible reject case can be built for this class. The
#     frozen file sets no `loom.semantics.termination`, so no termination
#     obligation is discharged and such a rival would be accepted vacuously.
#   The remaining nagini adversarial arguments — the structurally-different
#   correct control, and the two partial-domain rivals (pre-patch found-only, and
#   drop-a-listed-target) — port directly, and we add four more reject rivals so
#   that each of the three independent spec clauses above is attacked, including
#   the multiplicity and order sub-clauses of the filter/map (cases 6-7).
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10673"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Shared impl-region anchors (each lies entirely inside # impl-start/# impl-end).
_IMPL_FORBODY = (
    "  for entry in requested do\n"
    "    if entry == \"\" then\n"
    "      -- a blank line carries no reference and is ignored\n"
    "      pure ()\n"
    "    else if (existingDocs ++ generatedPages).contains entry then\n"
    "      entries := entries ++ [((none : Option String), entry)]\n"
    "    else\n"
    "      -- a reference to no existing document and no special reference page:\n"
    "      -- rejected, contributing no entry\n"
    "      pure ()\n"
    "  return entries"
)

# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness). A structurally-DIFFERENT but behaviourally
#    IDENTICAL impl: the two nested branches (blank-skip, then union-membership)
#    are fused into a single guard `entry != "" && (…).contains entry`, dropping
#    the explicit reject arms. This is exactly the spec's own `filter` predicate,
#    so the accepted set, its order, and each `(none, e)` pair are unchanged. The
#    obligation statement is byte-identical; only the tactic body is re-authored
#    to fold the single-guard loop against the same `filter`. Must VERIFY — else
#    the spec would be too strong, rejecting a correct implementation.
_POS = _swap(
    _BASE,
    _IMPL_FORBODY,
    "  for entry in requested do\n"
    "    if entry != \"\" && (existingDocs ++ generatedPages).contains entry then\n"
    "      entries := entries ++ [((none : Option String), entry)]\n"
    "  return entries",
)
_POS_PROOF_OLD = (
    "  have key : ∀ (rs : List String) (acc : List (Option String × String)),\n"
    "      (forIn (m := Id) rs acc (fun entry entries =>\n"
    "        if entry == \"\" then pure (ForInStep.yield entries)\n"
    "        else if (existingDocs ++ generatedPages).contains entry then\n"
    "          pure (ForInStep.yield (entries ++ [((none : Option String), entry)]))\n"
    "        else pure (ForInStep.yield entries))) =\n"
    "      acc ++ (rs.filter (fun e => e != \"\" && (existingDocs ++ generatedPages).contains e)).map\n"
    "        (fun e => ((none : Option String), e)) := by\n"
    "    intro rs\n"
    "    induction rs with\n"
    "    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil,\n"
    "        List.append_nil]; rfl\n"
    "    | cons r rs ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [List.filter_cons]\n"
    "      by_cases h1 : (r == \"\") = true\n"
    "      · have hne : (r != \"\") = false := by simp [bne, h1]\n"
    "        simp only [h1, if_true, hne, Bool.false_and, Bool.false_eq_true, if_false]\n"
    "        show (forIn (m := Id) rs acc _) = _\n"
    "        rw [ih]\n"
    "      · have hne : (r != \"\") = true := by simp [bne, h1]\n"
    "        by_cases h2 : ((existingDocs ++ generatedPages).contains r) = true\n"
    "        · simp only [h1, if_false, h2, if_true, hne, Bool.and_self, List.map_cons]\n"
    "          show (forIn (m := Id) rs (acc ++ [((none:Option String), r)]) _) = _\n"
    "          rw [ih]; simp [List.append_assoc]\n"
    "        · simp only [h1, if_false, h2, hne, Bool.and_false, Bool.false_eq_true, if_false]\n"
    "          show (forIn (m := Id) rs acc _) = _\n"
    "          rw [ih]\n"
    "  rw [key]\n"
    "  simp"
)
_POS_PROOF_NEW = (
    "  have key : ∀ (rs : List String) (acc : List (Option String × String)),\n"
    "      (forIn (m := Id) rs acc (fun entry entries =>\n"
    "        if entry != \"\" && (existingDocs ++ generatedPages).contains entry then\n"
    "          pure (ForInStep.yield (entries ++ [((none : Option String), entry)]))\n"
    "        else pure (ForInStep.yield entries))) =\n"
    "      acc ++ (rs.filter (fun e => e != \"\" && (existingDocs ++ generatedPages).contains e)).map\n"
    "        (fun e => ((none : Option String), e)) := by\n"
    "    intro rs\n"
    "    induction rs with\n"
    "    | nil => intro acc; simp only [List.forIn_nil, List.filter_nil, List.map_nil,\n"
    "        List.append_nil]; rfl\n"
    "    | cons r rs ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [List.filter_cons]\n"
    "      by_cases h : (r != \"\" && (existingDocs ++ generatedPages).contains r) = true\n"
    "      · simp only [h, if_true, List.map_cons]\n"
    "        show (forIn (m := Id) rs (acc ++ [((none:Option String), r)]) _) = _\n"
    "        rw [ih]; simp [List.append_assoc]\n"
    "      · simp only [h, Bool.false_eq_true, if_false]\n"
    "        show (forIn (m := Id) rs acc _) = _\n"
    "        rw [ih]\n"
    "  rw [key]\n"
    "  simp"
)
_POS = _swap(_POS, _POS_PROOF_OLD, _POS_PROOF_NEW)

# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN — acceptance against the existing-document family ALONE
#    (this IS the pre-patch behaviour). Clause (ii) attacked: the accept test
#    tests membership in `existingDocs` only, dropping the union with
#    `generatedPages`. Correct on every reference already present as an existing
#    document, but it drops any reference that is a special reference page yet not
#    an existing document — exactly the F2P sub-domain. Must REJECT.
_PARTIAL_UNION = _swap(
    _BASE,
    "    else if (existingDocs ++ generatedPages).contains entry then\n"
    "      entries := entries ++ [((none : Option String), entry)]",
    "    else if existingDocs.contains entry then\n"
    "      entries := entries ++ [((none : Option String), entry)]",
)

# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN — drop the FIRST listed reference unconditionally (iterate
#    over the tail of the reference list). Clause (iii) attacked (order/coverage
#    over the WHOLE input): correct on every input whose first reference is blank
#    or unaccepted (already contributes nothing), but wrong whenever the first
#    reference is an accepted target — a leading accepted reference is silently
#    dropped. Must REJECT.
_PARTIAL_FIRST = _swap(
    _BASE,
    "  for entry in requested do\n",
    "  for entry in requested.drop 1 do\n",
)

# ---------------------------------------------------------------------------
# 4. BLANK-CLAUSE — emit an entry for a blank reference. Clause (i) attacked: the
#    blank-skip arm is replaced by an APPEND, so a blank line contributes an entry
#    `(none, "")` instead of being ignored. Correct on every input with no blank
#    line; wrong at EVERY input that contains one, whatever the two name families
#    hold. Must REJECT.
#
#    Deliberately an unconditional emit rather than "delete the blank arm and let
#    the membership test decide". That weaker mutation only diverges from the spec
#    when the blank name is itself a member of `existingDocs ++ generatedPages` —
#    i.e. only when the project is claimed to contain a document whose name is the
#    empty string. Machine-checked: with `existingDocs = ["a"]` the two agree
#    (`rival [""] ["a"] [] = gold [""] ["a"] []` closes by `decide`), so on every
#    realizable input — `existingDocs`/`generatedPages` being names of documents
#    and of the special reference pages, none of which is empty — the weaker
#    mutation is behaviourally IDENTICAL to the frozen impl, and its refutation
#    would rest on an input the modeled domain cannot present. The unconditional
#    emit is wrong on the blank line alone, so clause (i) is attacked on its own
#    terms.
_ACCEPT_BLANK = _swap(
    _BASE,
    "    if entry == \"\" then\n"
    "      -- a blank line carries no reference and is ignored\n"
    "      pure ()\n",
    "    if entry == \"\" then\n"
    "      entries := entries ++ [((none : Option String), entry)]\n",
)

# ---------------------------------------------------------------------------
# 5. TITLE-COMPONENT — emit the reference name as an explicit title. Clause (iii)
#    attacked (the pair shape): each accepted entry is `(some entry, entry)`
#    instead of `(none, entry)`. Accepted SET and order are identical; only the
#    title component of every accepted pair is wrong. This near-miss agrees with
#    gold on which references are kept, so it is refuted at an input where an
#    entry is emitted at all. Must REJECT.
_TITLE = _swap(
    _BASE,
    "    else if (existingDocs ++ generatedPages).contains entry then\n"
    "      entries := entries ++ [((none : Option String), entry)]",
    "    else if (existingDocs ++ generatedPages).contains entry then\n"
    "      entries := entries ++ [((some entry : Option String), entry)]",
)


# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY. On a total carrier there is no precondition to be too strong,
#    so the analogue is the obligation being UNSATISFIABLE at exactly an
#    F2P-shaped input. This case discharges the obligation at such an input — a
#    reference list holding one ordinary existing document plus three references
#    that are special reference pages only (present in `generatedPages`, absent
#    from `existingDocs`) — BY EVALUATION as a leading `have`, then closes the
#    frozen obligation with the frozen tactic body verbatim. If the spec were
#    unsatisfiable at the F2P shape the `have` could not close by `decide`, so
#    this is a real witness that the modeled domain admits the F2P input, not a
#    restatement. The impl region is the frozen one, so the only difference from
#    the frozen file is the added `have` inside the proof region.
_ADMISS_HAVE = (
    "  have f2p : problem_spec_tocEntries [\"a\", \"p1\", \"p2\", \"p3\"] [\"a\"]\n"
    "      [\"p1\", \"p2\", \"p3\"]\n"
    "      (implementation_tocEntries [\"a\", \"p1\", \"p2\", \"p3\"] [\"a\"]\n"
    "        [\"p1\", \"p2\", \"p3\"]) := by\n"
    "    unfold problem_spec_tocEntries implementation_tocEntries\n"
    "    decide\n"
)
_ADMISS = _swap(
    _BASE,
    "  intro requested existingDocs generatedPages\n",
    _ADMISS_HAVE + "  intro requested existingDocs generatedPages\n",
)

# ---------------------------------------------------------------------------
# 7. MULTIPLICITY — de-duplicate the accepted entries. The spec's `filter`/`map`
#    is multiplicity-preserving: a reference listed twice, and accepted, yields
#    TWO entries. A rival that suppresses an entry whose target is already
#    present agrees with gold on every input whose references are distinct — so
#    it survives all four existing rivals' witnesses — and diverges only at a
#    repeated accepted reference. Must REJECT.
_DEDUP = _swap(
    _BASE,
    _IMPL_FORBODY,
    "  for entry in requested do\n"
    "    if entry != \"\" && (existingDocs ++ generatedPages).contains entry\n"
    "        && !entries.any (fun p => p.2 == entry) then\n"
    "      entries := entries ++ [((none : Option String), entry)]\n"
    "  return entries",
)

# ---------------------------------------------------------------------------
# 8. ORDER — emit the accepted entries in REVERSE listed order (prepend instead
#    of append). The spec pins the accepted entries to the ORDER in which they
#    are listed. This rival keeps exactly the right accepted SET, with the right
#    multiplicity and the right `(none, e)` shape — every existing rival's
#    witness input has at most one accepted entry, where reversal is invisible —
#    and diverges only once two references are accepted. Must REJECT.
_REVERSED = _swap(
    _BASE,
    _IMPL_FORBODY,
    "  for entry in requested do\n"
    "    if entry != \"\" && (existingDocs ++ generatedPages).contains entry then\n"
    "      entries := [((none : Option String), entry)] ++ entries\n"
    "  return entries",
)


SPEC_TESTS = [
    {
        "id": "pos-control-fused-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "A structurally-different but behaviourally-identical impl: the two "
            "nested branches (blank-skip then union-membership) are fused into a "
            "single guard `entry != \"\" && (existingDocs ++ generatedPages)."
            "contains entry`, which is exactly the spec's own filter predicate, "
            "and the explicit reject arms are removed. The accepted set, its "
            "order, and every `(none, e)` pair are unchanged, so the loop still "
            "reduces to the spec's `filter`/`map`. The `correct_tocEntries` "
            "statement is byte-identical; only the tactic body is re-authored to "
            "fold the single-guard loop. Must VERIFY — else the spec is too "
            "strong, rejecting a correct implementation."
        ),
    },
    {
        "id": "reject-existing-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_UNION,
        "refinement": (
            "This is the pre-patch acceptance: a reference is kept only when it "
            "names an existing document, ignoring the special reference pages. On "
            "the F2P scenario the three special pages are provided by the build "
            "yet have no source document of their own, so this rival rejects all "
            "three and emits no entry for them — the resulting entry list is empty "
            "where the test demands the three accepted entries. A faithful patch "
            "that only ever consulted the existing-document family would reproduce "
            "exactly this omission and would NOT resolve the F2P."
        ),
        "rationale": (
            "Clause (ii): the spec pins the result to a filter whose predicate is "
            "membership in the UNION `existingDocs ++ generatedPages`. Testing "
            "`existingDocs.contains` alone diverges from that filter for any "
            "reference in `generatedPages` but not `existingDocs`, so the loop no "
            "longer equals the spec's filter and the equality cannot hold."
        ),
        # requested/generatedPages nonempty, existingDocs EMPTY: the reference "g"
        # is a special page only -> gold keeps [(none,"g")], rival keeps [].
        "witness": (
            "example : ¬ problem_spec_tocEntries [\"g\"] [] [\"g\"]\n"
            "    (implementation_tocEntries [\"g\"] [] [\"g\"]) := by\n"
            "  unfold problem_spec_tocEntries implementation_tocEntries\n"
            "  decide"
        ),
    },
    {
        "id": "reject-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FIRST,
        "refinement": (
            "Iterating over the tail of the reference list drops the first listed "
            "reference unconditionally. On the F2P scenario the first listed "
            "reference is an accepted target that must appear as the leading "
            "entry; a faithful patch that never classified the first content line "
            "would drop that leading entry and NOT resolve the F2P — the entry "
            "list would be short by its first element."
        ),
        "rationale": (
            "Clause (iii), coverage over the WHOLE input: the spec pins the result "
            "to the filter/map over ALL of `requested`. Skipping the head yields "
            "the filter over `requested.drop 1`, which differs whenever the head "
            "is an accepted reference, so the pinned equality fails."
        ),
        # requested has length 2 (varies the requested binder), both names are
        # existing docs: gold keeps both in order, rival drops the head "a".
        "witness": (
            "example : ¬ problem_spec_tocEntries [\"a\", \"b\"] [\"a\", \"b\"] []\n"
            "    (implementation_tocEntries [\"a\", \"b\"] [\"a\", \"b\"] []) := by\n"
            "  unfold problem_spec_tocEntries implementation_tocEntries\n"
            "  decide"
        ),
    },
    {
        "id": "reject-accept-blank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ACCEPT_BLANK,
        "refinement": (
            "Emitting an entry for the blank line makes a blank reference produce "
            "a target. A blank line in a directive body carries no reference; a "
            "faithful patch that emitted an entry for it would inject a spurious "
            "empty-named target into the tree and NOT resolve the F2P — the "
            "collected entries would contain an entry the directive never listed."
        ),
        "rationale": (
            "Clause (i), the blank test `e != \"\"`: the spec filters out every "
            "blank reference before membership is even consulted. Appending an "
            "entry on the blank arm diverges from that filter at EVERY input "
            "containing a blank line — independently of what the two name "
            "families hold — so the pinned equality fails."
        ),
        # A blank line alongside an ordinary accepted reference, with NO document
        # named "": gold keeps [(none,"a")], the rival keeps [(none,""),(none,"a")].
        # The refuting input is realizable — `existingDocs`/`generatedPages` are
        # names of documents and of the special reference pages, none empty — so
        # the refutation does not depend on a document whose name is the empty
        # string. (Varies `requested` to length 2, mixing a blank and a non-blank.)
        "witness": (
            "example : ¬ problem_spec_tocEntries [\"\", \"a\"] [\"a\"] []\n"
            "    (implementation_tocEntries [\"\", \"a\"] [\"a\"] []) := by\n"
            "  unfold problem_spec_tocEntries implementation_tocEntries\n"
            "  decide"
        ),
    },
    {
        "id": "reject-explicit-title",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _TITLE,
        "refinement": (
            "Emitting each accepted entry with the reference name as an explicit "
            "title, rather than no title, changes the shape of every accepted "
            "pair. A faithful patch that attached a title to a bare reference "
            "would render each collected target with a wrong caption and NOT "
            "resolve the F2P, which pins each accepted entry to `(none, name)`."
        ),
        "rationale": (
            "Clause (iii), the pair shape: the spec maps each accepted reference "
            "to `(none, e)`. Emitting `(some e, e)` agrees with gold on WHICH "
            "references are kept and in what order — a near-miss — but the title "
            "component of every accepted pair differs, so the equality fails at "
            "any input where at least one entry is emitted."
        ),
        # a single accepted reference: gold emits (none,"a"), rival emits
        # (some "a","a"). Distinguishes precisely on the title component (this
        # near-miss agrees with gold on the accepted SET, so it is refuted where
        # an entry is actually produced, not at an empty result).
        "witness": (
            "example : ¬ problem_spec_tocEntries [\"a\"] [\"a\"] []\n"
            "    (implementation_tocEntries [\"a\"] [\"a\"] []) := by\n"
            "  unfold problem_spec_tocEntries implementation_tocEntries\n"
            "  decide"
        ),
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The total-carrier analogue of PRECOND-TOO-STRONG: the frozen "
            "obligation is a bare `∀` with no precondition, so the way it could "
            "still be too strong is by being UNSATISFIABLE at an F2P-shaped "
            "input. This case discharges it at exactly such an input — a "
            "reference list holding one ordinary existing document plus three "
            "references that are special reference pages only (in "
            "`generatedPages`, absent from `existingDocs`) — by EVALUATION, as a "
            "leading `have` closed by `decide`, before closing the frozen "
            "obligation with the frozen tactic body verbatim. The impl region is "
            "the frozen one and the obligation statement is byte-identical, so "
            "the case adds a concrete satisfiability witness rather than "
            "restating the theorem. Must VERIFY: if `decide` could not close the "
            "`have`, the spec would be unsatisfiable at the very input shape the "
            "behaviour is defined by."
        ),
    },
    {
        "id": "reject-dedup-entries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DEDUP,
        "refinement": (
            "Suppressing an entry whose target was already collected makes a "
            "reference listed twice contribute only one entry. A faithful patch "
            "that de-duplicated the collected targets would emit a shorter entry "
            "list than the directive body lists and would NOT resolve the F2P, "
            "which pins the entry list to one entry per accepted line."
        ),
        "rationale": (
            "Clause (iii), the multiplicity sub-clause: the spec pins the result "
            "to a `filter`/`map`, and `filter` is multiplicity-preserving — a "
            "reference listed twice and accepted twice yields TWO entries. "
            "Suppressing the second diverges from that filter at any input with "
            "a repeated accepted reference, so the pinned equality fails. This "
            "rival agrees with gold on every input whose references are "
            "distinct, so it survives all four other rivals' witness inputs."
        ),
        # the SAME accepted reference listed twice: gold keeps both copies,
        # the rival keeps one. Varies `requested` at a repeated name — the
        # multiplicity point no other case in this battery reaches.
        "witness": (
            "example : ¬ problem_spec_tocEntries [\"a\", \"a\"] [\"a\"] []\n"
            "    (implementation_tocEntries [\"a\", \"a\"] [\"a\"] []) := by\n"
            "  unfold problem_spec_tocEntries implementation_tocEntries\n"
            "  decide"
        ),
    },
    {
        "id": "reject-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REVERSED,
        "refinement": (
            "Collecting each accepted reference at the FRONT rather than the "
            "back reverses the entry list. A faithful patch that prepended each "
            "accepted target would render the tree entries in the opposite order "
            "from the directive body and would NOT resolve the F2P, which pins "
            "the entries to the order the references are listed in."
        ),
        "rationale": (
            "Clause (iii), the order sub-clause stated on its own terms: this "
            "rival keeps exactly the correct accepted SET, the correct "
            "multiplicity, and the correct `(none, e)` pair shape — it differs "
            "from the frozen impl ONLY in the order of the emitted entries, so "
            "it is refuted only at an input where two or more references are "
            "accepted. Every other rival in this battery is refuted at an input "
            "with at most one accepted entry, where reversal is invisible."
        ),
        # TWO accepted references: gold emits [(none,"a"),(none,"b")], the rival
        # emits [(none,"b"),(none,"a")]. Refutes on order alone.
        "witness": (
            "example : ¬ problem_spec_tocEntries [\"a\", \"b\"] [\"a\", \"b\"] []\n"
            "    (implementation_tocEntries [\"a\", \"b\"] [\"a\", \"b\"] []) := by\n"
            "  unfold problem_spec_tocEntries implementation_tocEntries\n"
            "  decide"
        ),
    },
]
