"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8120 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct buildLocaleDirs`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method assembling an ordered search list over
a ``List Dir`` carrier, ``Dir = String``):

  buildLocaleDirs (repoDirs : List Dir) (sysNone : Dir) (packageLocale : Dir)
      return (out : List Dir)
    ensures out = sysNone :: (repoDirs ++ [packageLocale])   -- THE clause

The method assembles the ordered lookup-source list from three parts: the
system-default entry (a sentinel), the user-provided entries, and the bundled
package entry. The ORDER of that list is precedence — an earlier entry wins a
lookup and a later one only fills in what no earlier entry defined (the pure
``resolve`` fold and ``resolve_user_precedence`` lemma state the behavioral
consequence). So the single structural clause pins four independently-attackable
sub-behaviours of the assembled list:

  * HEAD      — the system-default sentinel is FIRST (``sysNone :: …``);
  * USER-BODY — the user-provided entries appear next, in their own order and
                COMPLETE (``repoDirs`` spliced in, none dropped);
  * TRAILER   — the bundled package entry is LAST (``… ++ [packageLocale]``),
                present exactly once;
  * ORDER     — the user entries precede the bundled entry, so a user override
                of a message the bundled catalog also defines takes effect (the
                exact behavior the issue demands and the failing test observes).

``sysNone :: (repoDirs ++ [packageLocale])`` is a total, fully-unfolded
expression over the method's own inputs; the ``axioms`` region is empty (there is
no opaque answer key to echo — directive 8, the post-image is grounded in the
actual inputs). THREE input binders, all free: ``repoDirs`` (contents, length,
order), ``sysNone`` (the head), ``packageLocale`` (the trailer). The post-image
must hold for every value of each.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * DIVERGENCE / TERMINATION: REJECTED BY THE SPEC, unshippable for a WITNESS
    reason, and not a spec hole (not vacuous either, and not a "hard proof"
    excuse; measured with 19 builds). An earlier revision of this bullet labelled
    the class a KNOWN HOLE; that label is withdrawn, since what is missing is a
    witness the gate can score, not a clause the spec fails to pin. The frozen
    solution sets
    ``loom.semantics.termination "total"``, so this class would normally be
    SHIPPABLE: a rival whose loop carries no decreasing measure IS genuinely
    rejected, and it is — the diverging rival fails with the unsolved measure goal
    ``spin + 1 < spin`` at its own ``decreasing`` annotation, i.e. on the
    termination obligation and not on a tactic mismatch. What blocks it is the
    WITNESS half, and only that. A refutation on this carrier goes through
    ``buildLocaleDirsTester``, and against a loop-bearing impl the tester does not
    reduce: ``decide``, ``decide +kernel``, ``rfl``, ``simp``,
    ``unfold; simp`` and ``simp_all`` were each built against the diverging rival
    for the claim AND its negation (10 builds), and every pair failed with the
    byte-identical error — so no tester witness's exit code can carry information
    about the claim, which is exactly the ``witness-undecided`` shape the gate
    refuses. A ``witness_reference`` does not rescue it either: the reference
    replaces the GOLD side, while the unreducible term here is on the RIVAL side,
    which is the half that must SUCCEED. And the violation is of termination, not
    of the post-image — the diverging rival's assembled list IS gold's, so there is
    no value-level disagreement for any witness to state. Recorded as a limit of
    what THIS gate can witness on this carrier, with the spec-side verdict on a
    diverging rival being REJECT. Under ``termination "total"`` a postcondition is
    claimed of ALL runs rather than only of terminating ones, so nothing here is
    satisfied vacuously: the measure obligation shown above is a real proof goal,
    and G-VERIFY is the lane in which it is discharged.
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame-mutation rival (it writes into the read-only project-source carrier
    held at ``Acc(list_pred(user_tr), 1/2)``, rejected for insufficient
    permission). Lean/Velvet are referentially transparent: every input is an
    immutable value, this method declares NO ``mut`` binder over any input, and
    there is no heap and no aliasing — so there is no read-only cell to overwrite
    and no substitute probe. Not fabricated (per the porting map, vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a concrete list expression
    over the method's own arguments (empty ``axioms`` region; no opaque callee),
    so the only satisfier is the grounded assembly itself; there is nothing to
    echo. The sibling's grounded-oracle positive control ports as the direct
    positive control.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each rival gets part of the
    assembly right (usually the right length or the right head) and diverges on
    one structural sub-behaviour above.

CARRIER NARROWING (why this battery is smaller than the nagini sibling). The
nagini sibling models the FULL pipeline: assemble the ordered source list AND
resolve a message through it by first-wins precedence, over a rich
``(provides?, text-code)`` carrier with a deep ``resolved`` fold. This velvet
bundle models ONLY the purely-functional core the patch actually changes — the
ASSEMBLY and ORDER of the search list (``out = sysNone :: (repoDirs ++
[packageLocale])``). The message-resolution behavior is NOT in this bundle's
carrier: ``resolve`` is present in the ``pure`` region only as the A-reference
deep model validated by G-AX, and no ``ensures`` clause resolves a message. So
the sibling's resolution-level rivals (bundled-wins-over-project, last-wins)
have no ``ensures`` clause to violate here — the discriminator that distinguishes
them from gold lives in the resolution the spec does not compute. What DOES
survive is the ORDER attack: the pre-patch bug (bundled entry AHEAD of the user
entries) is directly visible as an assembled-list mismatch, and it is exactly the
edit the gold patch makes. The resolution rivals therefore collapse onto the
single ORDER sub-behaviour at this carrier, which the prepatch-order rival
attacks; the extra rivals attack the structural sub-behaviours the assembly
clause pins that the sibling folds into its list construction.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is LOOP-FREE (two list
appends), so its extracted tester reduces under ``decide`` — the astropy-12907
pattern. Each reject rival is likewise a loop-free expression, so its tester
also ``decide``s. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement ``buildLocaleDirsTester repoDirs sysNone
packageLocale = false`` at ONE concrete input, checked in a file whose
``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its rival (the tester ``decide``s to ``false``
— the rival's assembled list violates the postcondition there) and FAILS against
the frozen solution (gold's tester ``decide``s to ``true``, so ``= false`` is
refuted). The method declares no ``require`` clause, so every input is in-domain
and no witness is vacuously excluded. No witness binds a hypothesis (the carrier
is fully transparent — literal ``String``/``List`` inputs), so there is no
joint-satisfiability obligation. No ``sorry``/``admit``/``native_decide``/
``axiom`` appears in any witness.

AXIOM lane: EMPTY. ``resolve`` is a deep A-reference validated == the real
message-catalog loader by axiom_check.py — that is G-AX's job, and this gate
ignores ``AXIOM_TESTS`` regardless.

INDEPENDENT AUDIT (second pass, adversarial — supersedes the first). Every case
was re-derived against the real verifier from scratch: 8 module builds, the two
witness builds per reject case, and a FORGERY build per reject case that flips
the witness's claim (``= false`` -> ``= true``) and changes nothing else. The
forgery pair is what establishes the gold-side exit code carries information
about the CLAIM rather than about the file: flipping the claim inverted BOTH exit
codes on all six shipped reject cases (gold 1->0, rival 0->1), so every gold-side
``decide`` genuinely evaluated the proposition. Statement integrity was checked by
diffing each variant against the frozen file byte-for-byte: all differences are
confined to the impl region, and the ``ensures`` clause and ``prove_correct``
header are byte-identical everywhere.

This pass found and fixed THREE defects the first audit's prose had asserted
away. They are recorded here because the docstring previously claimed the
opposite:

  * A FALSE PARTIAL-DOMAIN CLAIM. The case then called
    ``weak-bundled-wins-subdomain`` branched on ``repoDirs.isEmpty`` and was sold
    as "the only rival gold-correct on a proper sub-domain". Its two branches are
    ONE function, and that function is ``weak-prepatch-order``'s body:
    ``cases repoDirs <;> simp`` closes the equality (real build, exit 0). It was a
    RESHAPE of an existing rival, so the battery had NO partial-domain rival while
    the accounting said it had one. Replaced by
    ``weak-nearmiss-empty-drops-trailer``, whose sub-domain claim is checked in
    three directions including a build asserting it SATISFIES the spec off the
    empty case.
  * A MISSING ADMISSIBILITY LANE recorded as vacuous on the reason that has been
    measured wrong ("no ``require`` clause, so nothing to admit"). Landed as
    ``admiss-f2p-shaped-order``; see that case.
  * The DIVERGENCE lane, which under ``termination "total"`` is normally
    shippable, is a demonstrated carrier limit here — see the footer, which now
    records what was built rather than asserting the class away.

Spec-hole probes beyond the shipped cases, all rebuilt this pass:

  * SPEC-TOO-WEAK (7 new wrong impls, ALL correctly REJECTED on the postcondition
    goal itself): user segment reversed; trailer duplicated; head duplicated;
    trailer replaced by the head value; user segment missing its last entry; the
    assembled list de-duplicated; and the empty-case near-miss (now shipped). Each
    was additionally confirmed excluded by building its own tester refutation
    against it (7 builds, all exit 0). No spec hole.
  * SPEC-TOO-STRONG (6 new CORRECT reshapes, ALL VERIFIED with the frozen
    ``loom_solve`` untouched): ``[sysNone] ++ repoDirs ++ [packageLocale]``;
    ``(sysNone :: repoDirs) ++ [packageLocale]``;
    ``(sysNone :: repoDirs).concat packageLocale``; a ``foldr``-built tail consed
    onto the head; ``List.cons`` written explicitly; and a two-step
    ``[sysNone] ++ repoDirs`` then ``++ [packageLocale]``. The clause is not
    over-fit to the frozen append shape.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8120"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (both markers live inside the elided impl region). Every
# rival and reshape edits ONLY this block (and, for reshapes, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec
# holds by construction.
_IMPL = (
    "    let mut localeDirs : List Dir := [sysNone]\n"
    "    localeDirs := localeDirs ++ repoDirs\n"
    "    localeDirs := localeDirs ++ [packageLocale]\n"
    "    return localeDirs"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as `loom_solve`, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct buildLocaleDirs by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `buildLocaleDirsTester repoDirs sysNone packageLocale = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict; both the rival and the frozen impl
# ---- are loop-free, so both testers reduce under `decide`. No `require` clause
# ---- exists, so every input is in-domain.
def _witness(call):
    return ("extract_program_for buildLocaleDirs\n"
            "prove_precondition_decidable_for buildLocaleDirs\n"
            "prove_postcondition_decidable_for buildLocaleDirs\n"
            "derive_tester_for buildLocaleDirs\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — the cheapest HONEST impl: return the
    # post-image expression directly. `sysNone :: (repoDirs ++ [packageLocale])`
    # is GROUNDED in the inputs (a concrete list expression, no opaque answer
    # key), so returning it is a correct fully-grounded implementation. The
    # frozen proof (`loom_solve`) still closes the byte-identical obligation (the
    # body is definitionally the ensures RHS). Verified out-of-band with a real
    # build. If this CORRECT impl failed => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl("    return sysNone :: (repoDirs ++ [packageLocale])"),
        "rationale": "the post-image `sysNone :: (repoDirs ++ [packageLocale])` "
                     "is GROUNDED in the inputs (a concrete list expression, no "
                     "opaque answer key), so returning it directly is the honest "
                     "cheapest CORRECT impl. It MUST verify — the clause is "
                     "literally `out = sysNone :: (repoDirs ++ [packageLocale])` "
                     "— else the single postcondition clause is SPEC-TOO-STRONG. "
                     "Also shows the spec is not echo-vulnerable: any wrong "
                     "constant/echo would fail the clause.",
    },
    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a structurally DIFFERENT but CORRECT impl
    # that builds the tail first (user entries ++ bundled) and then conses the
    # head, instead of the frozen head-first two-append shape. Identical values,
    # different control flow. The frozen proof (`loom_solve`) still closes the
    # byte-identical obligation. Verified out-of-band with a real build. A
    # faithful reshape that could NOT verify would mean the postcondition is
    # over-fit to the append ORDER of the frozen body => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-cons-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let mut localeDirs : List Dir := repoDirs ++ [packageLocale]\n"
            "    localeDirs := sysNone :: localeDirs\n"
            "    return localeDirs"),
        "rationale": "structurally different CORRECT reshape: build the tail "
                     "(`repoDirs ++ [packageLocale]`) first, then cons the "
                     "`sysNone` head, instead of the frozen head-first two-append "
                     "shape. Observationally identical, so `out = sysNone :: "
                     "(repoDirs ++ [packageLocale])` still holds on the whole "
                     "domain. A faithful reshape MUST verify, else the clause is "
                     "over-fit to the frozen append order => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- ORDER clause: the pre-patch bug — bundled entry AHEAD of user entries.
    {
        "id": "weak-prepatch-order",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug: the bundled package entry is placed BEFORE the user
        # entries — order [head] ++ [bundled] ++ user instead of [head] ++ user
        # ++ [bundled]. Correct head and correct membership, wrong precedence.
        "module": _impl("    return sysNone :: ([packageLocale] ++ repoDirs)"),
        "refinement": "this IS the pre-patch assembly: the bundled entry is put "
                      "ahead of the user-provided entries. Under first-wins "
                      "precedence the bundled catalog then supplies any message "
                      "it defines, so a user override of a message the bundled "
                      "catalog ALSO defines never takes effect — exactly the bug "
                      "the issue reports (the user's own value is shadowed by the "
                      "bundled one). The failing test asserts the user "
                      "override wins, so a faithful counterpart keeping this "
                      "order would NOT resolve.",
        "rationale": "REJECT from `out = sysNone :: (repoDirs ++ [packageLocale])` "
                     "via the ORDER sub-behaviour: the post-image places the user "
                     "entries before the bundled entry; the rival inverts them. "
                     "Refuted at repoDirs=[\"u\"], sysNone=\"s\", packageLocale=\"p\": "
                     "gold's list is [\"s\",\"u\",\"p\"], the rival's [\"s\",\"p\",\"u\"]. "
                     "Discrimination comes from the relative order of `repoDirs` "
                     "and `packageLocale`.",
        "witness": _witness('buildLocaleDirsTester ["u"] "s" "p"'),
    },

    # ---- TRAILER clause: drop the bundled entry entirely.
    {
        "id": "weak-drop-bundled-trailer",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the trailing bundled package entry: assemble only [head] ++ user.
        # Correct head and correct user body, but the bundled fallback is missing,
        # so messages only the bundled catalog defines are never found.
        "module": _impl("    return sysNone :: repoDirs"),
        "refinement": "dropping the trailing bundled package entry removes the "
                      "shipped fallback catalog from the search list, so any "
                      "message that ONLY the bundled catalog defines (the vast "
                      "majority of the built-in strings) is left untranslated. "
                      "The passing localization tests rely on the bundled "
                      "catalog being present as the final fallback, so a faithful "
                      "counterpart that omitted it would regress those and NOT "
                      "resolve.",
        "rationale": "REJECT from the clause via the TRAILER sub-behaviour: the "
                     "post-image appends `[packageLocale]`; the rival omits it. "
                     "Refuted at repoDirs=[], sysNone=\"d\", packageLocale=\"q\": "
                     "gold's list is [\"d\",\"q\"], the rival's [\"d\"]. This is the "
                     "ONLY witness at the empty-`repoDirs` input, and the only one "
                     "that abuses the presence of `packageLocale`.",
        "witness": _witness('buildLocaleDirsTester ([] : List Dir) "d" "q"'),
    },

    # ---- USER-BODY clause: drop the user entries entirely.
    {
        "id": "weak-drop-user-body",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble only [head] ++ [bundled], dropping the user-provided entries.
        # Correct head and correct trailer, but the user override sources are
        # absent, so no user-provided catalog can ever win.
        "module": _impl("    return sysNone :: [packageLocale]"),
        "refinement": "dropping the user-provided entries removes exactly the "
                      "override sources the fix is about: with them gone, a "
                      "message the user redefines can never take effect (there is "
                      "no user catalog in the search list at all). The failing "
                      "test adds a user catalog and asserts its value wins, so a "
                      "faithful counterpart that omitted the user entries would "
                      "NOT resolve.",
        "rationale": "REJECT from the clause via the USER-BODY sub-behaviour: the "
                     "post-image splices `repoDirs` in; the rival drops them. "
                     "Refuted at repoDirs=[\"a\",\"b\"], sysNone=\"x\", "
                     "packageLocale=\"y\": gold's list is [\"x\",\"a\",\"b\",\"y\"], the "
                     "rival's [\"x\",\"y\"]. Discrimination comes from a non-empty "
                     "`repoDirs` of length 2 — a length no other witness probes.",
        "witness": _witness('buildLocaleDirsTester ["a","b"] "x" "y"'),
    },

    # ---- HEAD clause: move the system-default sentinel to the end.
    {
        "id": "weak-head-at-end",
        "kind": "uniqueness",
        "expect": "reject",
        # Place the system-default sentinel LAST instead of first: assemble
        # user ++ [bundled] ++ [head]. Correct membership, wrong head position.
        "module": _impl(
            "    return (repoDirs ++ [packageLocale]) ++ [sysNone]"),
        "refinement": "moving the system-default entry to the end demotes it "
                      "below every other source in precedence. AUDIT-CORRECTED "
                      "SCOPE: this rival's list is observationally DISTINCT from "
                      "the post-image as a list (the clause is structural, and "
                      "`sysNone`'s index differs), which is what the witness "
                      "refutes. Its RESOLUTION-level consequence, however, is "
                      "conditional, and the earlier claim here that it "
                      "unconditionally breaks the tests was WRONG: whenever the "
                      "system-default entry defines nothing for a message "
                      "(`cat sysNone k = none`), first-wins resolution over "
                      "`user ++ [bundled] ++ [sysNone]` agrees with gold's order "
                      "on that message. Machine-checked both ways during the "
                      "audit: with the sentinel non-defining the two orders are "
                      "provably equal for every catalog and message, and with a "
                      "system-installed catalog that DOES define the message the "
                      "orders differ (gold takes the system value, this rival "
                      "takes the user value). So a faithful counterpart is "
                      "order-nonconformant and diverges from gold exactly on the "
                      "sub-domain where the system-default tree supplies the "
                      "message; it is retained as a STRUCTURAL rival on the HEAD "
                      "sub-behaviour, not as a claim about the failing test.",
        "rationale": "REJECT from the clause via the HEAD sub-behaviour: the "
                     "post-image conses `sysNone` at the FRONT; the rival appends "
                     "it at the end. Refuted at repoDirs=[\"m\"], sysNone=\"z\", "
                     "packageLocale=\"w\": gold's list is [\"z\",\"m\",\"w\"], the "
                     "rival's [\"m\",\"w\",\"z\"]. Discrimination comes from the "
                     "position of `sysNone`.",
        "witness": _witness('buildLocaleDirsTester ["m"] "z" "w"'),
    },

    # ---- ORDER clause, whole-list inversion. ADDED BY AUDIT. The earlier
    # accounting recorded the sibling's last-wins rival as NARROWED ("no clause
    # here to violate — at the assembly level it assembles the SAME list gold
    # does"). That is FALSE on this carrier: last-wins over the assembled list is
    # first-wins over the REVERSED list, and the reversal is a different list, so
    # the structural clause does violate it directly. Landed with two real builds.
    {
        "id": "weak-last-wins-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble the right entries in the exactly-inverted order, so the entry
        # the post-image puts LAST is consulted FIRST. Membership and length are
        # both correct; every relative precedence is inverted.
        "module": _impl(
            "    return (sysNone :: (repoDirs ++ [packageLocale])).reverse"),
        "refinement": "inverting the whole search order makes the LAST source "
                      "consulted first, i.e. lowest-priority-wins. A faithful "
                      "counterpart treats the ordered list as if later entries "
                      "overrode earlier ones (the opposite of the loader's "
                      "first-defining-entry-wins semantics), so the bundled entry "
                      "— last in the correct order — shadows a user override of a "
                      "message the bundled catalog also defines. The failing test "
                      "asserts the user override wins, so it would NOT resolve; it "
                      "additionally regresses every message two sources define.",
        "rationale": "REJECT from `out = sysNone :: (repoDirs ++ [packageLocale])` "
                     "via total ORDER inversion — a strictly different attack from "
                     "weak-prepatch-order, which swaps only the user/bundled "
                     "segments and leaves the head in place; here the head moves "
                     "too and the user entries are internally reversed. Refuted at "
                     "repoDirs=[\"g\",\"h\"], sysNone=\"i\", packageLocale=\"j\": "
                     "gold's list is [\"i\",\"g\",\"h\",\"j\"], the rival's "
                     "[\"j\",\"h\",\"g\",\"i\"]. Length-2 `repoDirs` is what makes "
                     "the internal reversal of the user segment observable, so this "
                     "witness also probes a point no other rival reaches.",
        "witness": _witness('buildLocaleDirsTester ["g","h"] "i" "j"'),
    },

    # ---- ORDER clause, PROPER SUB-DOMAIN near-miss. RE-AIMED BY THIS AUDIT.
    # The previous occupant of this slot branched on `repoDirs.isEmpty` and
    # hoisted the trailer ahead of the user entries in the else-branch. Its
    # `rationale` claimed to be the battery's one PARTIAL-DOMAIN rival — "at
    # repoDirs=[] the rival's tester AGREES with gold". That claim was FALSE and
    # was disproved with two real builds:
    #   * asserting the rival SATISFIES the spec at repoDirs=[] (tester `= true`)
    #     built with exit 0, i.e. it agreed with gold there — as claimed; but
    #   * `[sysNone] ++ [packageLocale]` on the empty branch and
    #     `([sysNone] ++ [packageLocale]) ++ repoDirs` on the other are ONE
    #     function, and that function is exactly weak-prepatch-order's body:
    #       (if repoDirs.isEmpty then [sysNone] ++ [packageLocale]
    #        else ([sysNone] ++ [packageLocale]) ++ repoDirs)
    #         = sysNone :: ([packageLocale] ++ repoDirs)
    #     is closed by `cases repoDirs <;> simp` (exit 0, machine-checked).
    # So the branch was cosmetic: the case was a RESHAPE of weak-prepatch-order,
    # not a second attack, and its "gold-correct on a proper sub-domain" claim
    # described a point where weak-prepatch-order is equally gold-correct
    # (at repoDirs=[] BOTH assemble [sysNone, packageLocale]). The battery had NO
    # partial-domain rival and the accounting said it had one.
    #
    # Replaced with a genuine near-miss that is gold-identical on a NON-trivial
    # sub-domain and wrong only off it: keep gold's assembly whenever any user
    # entry is configured, and drop the trailer when none is. Machine-checked all
    # three directions (see `rationale`).
    {
        "id": "weak-nearmiss-empty-drops-trailer",
        "kind": "uniqueness",
        "expect": "reject",
        # Gold's exact assembly when user entries exist; when there are none,
        # omit the bundled trailer, so the shipped fallback catalog is absent
        # from the search list for precisely the no-user-entry configuration.
        "module": _impl(
            "    let mut localeDirs : List Dir := [sysNone]\n"
            "    if repoDirs.isEmpty then\n"
            "      localeDirs := localeDirs\n"
            "    else\n"
            "      localeDirs := (localeDirs ++ repoDirs) ++ [packageLocale]\n"
            "    return localeDirs"),
        "refinement": "a counterpart that assembles the corrected order (user "
                      "entries ahead of the bundled entry) whenever any user entry "
                      "is configured, but omits the bundled entry entirely when "
                      "none is. It is observationally IDENTICAL to gold on the "
                      "whole sub-domain where a user entry exists — including the "
                      "input the failing test exercises, so it WOULD resolve that "
                      "one — and it diverges exactly on the default configuration, "
                      "where it drops the shipped fallback catalog and leaves every "
                      "message that only that catalog defines untranslated. So a "
                      "faithful counterpart regresses the passing localization "
                      "tests that build with no user entry configured, and does NOT "
                      "resolve overall. It is the surgically-minimal rival: right "
                      "where the fix is observed, wrong where the fix must not "
                      "break anything.",
        "rationale": "REJECT from `out = sysNone :: (repoDirs ++ [packageLocale])` "
                     "on a PROPER SUB-DOMAIN — the battery's only rival that is "
                     "gold-correct somewhere, so it is the one showing the clause "
                     "is tight POINTWISE rather than merely excluding "
                     "globally-wrong shapes. Machine-checked in three directions: "
                     "(i) refuted at repoDirs=[], sysNone=\"s\", packageLocale=\"p\" "
                     "— gold's list is [\"s\",\"p\"], the rival's [\"s\"]; (ii) at "
                     "repoDirs=[\"u\",\"v\"] the rival's tester `= true` BUILDS, so "
                     "it genuinely satisfies the spec there and the sub-domain is "
                     "proper; (iii) `repoDirs ≠ [] → (its body) = sysNone :: "
                     "(repoDirs ++ [packageLocale])` is provable, so the agreement "
                     "is total off the empty case rather than coincidental at one "
                     "point. Discrimination comes from `repoDirs` being EMPTY, and "
                     "it is the only rival whose witness needs that input.",
        "witness": _witness('buildLocaleDirsTester ([] : List Dir) "s" "p"'),
    },

    # =====================================================================
    # ADMISSIBILITY. ADDED BY THIS AUDIT. The battery shipped with NO
    # `kind="admissibility"` case, so it tested SPEC-TOO-WEAK and
    # SPEC-TOO-STRONG but not PRECOND-TOO-STRONG — one of the three directions
    # this gate exists to cover. The previous accounting called the lane VACUOUS
    # because "this bundle declares NO `require` clause, so there is no
    # precondition to admit". That is the reason that has been measured wrong:
    # the analogue on a require-free TOTAL carrier is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    # discharges the obligation at that concrete input — by evaluation, as a
    # `have`, before closing the frozen obligation verbatim — tests directly.
    #
    # The impl region is byte-identical to the frozen one here; only the elided
    # `prove_correct` tactic body changes, and the `prove_correct buildLocaleDirs`
    # header is retyped byte-for-byte, so `same_spec` holds and the obligation
    # survives. The `have` is `clear`ed before `loom_solve` runs, so the frozen
    # proof closes from an UNCHANGED context — the obligation is reproven
    # verbatim, not weakened by a hypothesis left in scope.
    #
    # LIVENESS was checked with a real build rather than assumed: flipping one
    # conjunct to a false claim (the user-first order resolving to the bundled
    # value) makes the file FAIL with "`decide` proved that the proposition ... is
    # false", so the `have` is a live obligation and not a decoration.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-order",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct buildLocaleDirs by\n"
            "  have hadmiss :\n"
            "      (\"s\" :: ([\"u\"] ++ [\"p\"])) = [\"s\", \"u\", \"p\"]\n"
            "      ∧ resolve (fun (d : Dir) (_ : String) => "
            "if d = \"u\" then some \"USER\" else if d = \"p\" then some \"PKG\" else none) "
            "(\"s\" :: ([\"u\"] ++ [\"p\"])) \"m\" = some \"USER\"\n"
            "      ∧ resolve (fun (d : Dir) (_ : String) => "
            "if d = \"u\" then some \"USER\" else if d = \"p\" then some \"PKG\" else none) "
            "(\"s\" :: ([\"p\"] ++ [\"u\"])) \"m\" = some \"PKG\"\n"
            "      ∧ resolve (fun (d : Dir) (_ : String) => "
            "if d = \"u\" then some \"USER\" else if d = \"p\" then some \"PKG\" else none) "
            "(\"s\" :: ([\"u\"] ++ [\"p\"])) \"m\"\n"
            "          ≠ resolve (fun (d : Dir) (_ : String) => "
            "if d = \"u\" then some \"USER\" else if d = \"p\" then some \"PKG\" else none) "
            "(\"s\" :: ([\"p\"] ++ [\"u\"])) \"m\" := by\n"
            "    decide\n"
            "  clear hadmiss\n"
            "  loom_solve"),
        "rationale": "PRECOND-TOO-STRONG probe, re-aimed at what that direction IS "
                     "on a total carrier with an empty pre-conditions region: not "
                     "\"does a `require` admit this input\" (there is no `require`) "
                     "but \"is the obligation SATISFIABLE, and non-degenerate, at "
                     "an F2P-shaped input\". Three ground facts are discharged by "
                     "EVALUATION at the smallest input that has the shape the "
                     "failing test exercises — one system-default entry, one user "
                     "entry that defines a message, one bundled entry that ALSO "
                     "defines it: (i) the post-image evaluates to the concrete list "
                     "[\"s\",\"u\",\"p\"] there, so the clause is satisfiable at "
                     "that point rather than only in principle; (ii) first-wins "
                     "resolution over that assembled order yields the USER value; "
                     "(iii) over the inverted order it yields the BUNDLED value, "
                     "and (iv) those two differ. Conjunct (iv) is what makes the "
                     "probe non-degenerate: it certifies the ORDER the clause pins "
                     "is the order that changes the observable outcome, so the "
                     "obligation is not vacuously satisfiable by any assembly. If "
                     "any of these could not be discharged, the clause would be "
                     "unsatisfiable at exactly the input the failing test observes "
                     "— the require-free analogue of PRECOND-TOO-STRONG. Nothing is "
                     "assumed: no new declaration, the impl region is byte-identical "
                     "to the frozen one, the `prove_correct buildLocaleDirs` header "
                     "is byte-identical, the facts are `have`s inside the existing "
                     "tactic body, and they are `clear`ed so `loom_solve` closes the "
                     "frozen obligation from an unchanged context.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 3 partial-domain rivals)
# plus a 2-case AXIOM lane. This bundle models only the purely-functional CORE
# the patch changes — the ASSEMBLY and ORDER of the search list — NOT the
# message resolution the sibling also models. So the resolution-level rivals lose
# the clause they violate and collapse onto the single ORDER sub-behaviour of the
# assembly clause; the assembly's own structural sub-behaviours get dedicated
# rivals.
#
#   sibling case                       -> here                         disposition
#   ---------------------------------------------------------------------------
#   pos-control-grounded-oracle-delegate -> pos-control-direct         PORTED
#   pos-control-branch-reorder-no-text   -> pos-control-cons-reorder   PORTED (re-aimed)
#   admissibility-f2p-shaped-selfcall    -> admiss-f2p-shaped-order    PORTED (audit 2)
#   frame-mutation-write-user-tr         -> (none)                     VACUOUS
#   prepatch-order-bundled-ahead         -> weak-prepatch-order        PORTED
#   bundled-wins-over-project-subdomain  -> weak-nearmiss-empty-drops-trailer
#                                                                     RE-AIMED (audit 2)
#   last-wins-forward-fold               -> weak-last-wins-reversed    PORTED (audit)
#   (no sibling)                         -> weak-drop-bundled-trailer  ADDED
#   (no sibling)                         -> weak-drop-user-body        ADDED
#   (no sibling)                         -> weak-head-at-end           ADDED
#   (no sibling; carrier's own oblig.)   -> (none)      diverge: SPEC-CLOSED
#                                             [divergence; see the docstring]
#   AXIOM_TESTS (2)                      -> (none)                     DROPPED (G-AX)
#
# 6 ported (2 positives + prepatch-order + last-wins + admissibility + the
# re-aimed sub-domain rival), 3 added, 1 vacuous, 1 spec-closed (divergence), 2 dropped
# = 9 SPEC cases (2 soundness, 6 uniqueness, 1 admissibility).
#
# AUDIT-2 CORRECTION (supersedes the first audit's entry for
#   bundled-wins-over-project). The first audit recovered that sibling rival as
#   `weak-bundled-wins-subdomain` and advertised it as the battery's only
#   PARTIAL-DOMAIN rival: "gold-identical on the empty-`repoDirs` sub-domain and
#   wrong exactly where a user entry exists". The sub-domain half of that was true
#   and the NOVELTY half was false. Its body
#     if repoDirs.isEmpty then [sysNone] ++ [packageLocale]
#     else ([sysNone] ++ [packageLocale]) ++ repoDirs
#   is definitionally `sysNone :: ([packageLocale] ++ repoDirs)` — proved by
#   `cases repoDirs <;> simp`, exit 0 — which is `weak-prepatch-order`'s body
#   verbatim. So the two cases were the SAME rival in two spellings, the second
#   contributing only a different witness input, and the "gold-correct on a proper
#   sub-domain" property it was credited with is one `weak-prepatch-order` already
#   has (at repoDirs=[] both assemble [sysNone, packageLocale] — checked, exit 0).
#   The battery therefore had no partial-domain rival at all. RE-AIMED to
#   `weak-nearmiss-empty-drops-trailer`, which agrees with gold on the whole
#   non-empty sub-domain (proved as an implication, and separately confirmed by a
#   build asserting its tester `= true` at repoDirs=["u","v"]) and is wrong only at
#   repoDirs=[]. The lesson generalizes: on this carrier a rival that BRANCHES is
#   not thereby a partial-domain rival — the branches have to compute different
#   functions, and `simp` is the check.
#
# PORTED (positives): the sibling's grounded-oracle delegate returns the fully
#   unfolded resolution directly — here the grounded post-image is the assembly
#   expression, so the direct control is `return sysNone :: (repoDirs ++
#   [packageLocale])`. The sibling's branch-reorder reshapes the final
#   out-selection — here the analogous reshape builds the tail first and conses
#   the head, keeping every value identical, so `loom_solve` closes the frozen
#   obligation. Both verified out-of-band with real builds.
# PORTED (prepatch-order): the sibling's prepatch-order rival places the bundled
#   source ahead of the project sources; that is the SAME edit the gold patch
#   reverses, and at this carrier it is directly a mismatched assembled list
#   (`sysNone :: [packageLocale] ++ repoDirs` vs `sysNone :: repoDirs ++
#   [packageLocale]`). Witness discriminates (verified).
# PORTED-BY-AUDIT (weak-last-wins-reversed): the sibling states this against a
#   RESOLUTION postcondition (P2/P4), which this carrier indeed lacks. But its
#   ASSEMBLED LIST already differs from the post-image, so the structural clause
#   refutes it without any resolution clause: last-wins over the assembled list is
#   first-wins over the REVERSED list, and the reversal is a different list.
#   (The sibling's bundled-wins rival was recovered by the same reasoning and the
#   reasoning was right about EXPRESSIBILITY but wrong about novelty — see the
#   AUDIT-2 CORRECTION above. It is now re-aimed.)
# RE-AIMED BY AUDIT-2 (weak-nearmiss-empty-drops-trailer): the battery's only
#   PARTIAL-DOMAIN rival, and the one that certifies the clause is tight POINTWISE
#   rather than merely against globally-wrong shapes. Gold-identical wherever a
#   user entry exists — proved as the implication `repoDirs ≠ [] → its body =
#   sysNone :: (repoDirs ++ [packageLocale])`, and independently confirmed by a
#   build asserting its tester `= true` at repoDirs=["u","v"] (exit 0) — and wrong
#   only at repoDirs=[], where it drops the bundled trailer. Note the direction of
#   its refinement argument differs from every other rival's: it is right ON the
#   input the failing test exercises and wrong on the DEFAULT configuration, so
#   what it would break is the passing localization tests, not the failing one.
# ADDED (weak-drop-bundled-trailer, weak-drop-user-body, weak-head-at-end): the
#   assembly clause pins three structural sub-behaviours the sibling folds into
#   its list construction rather than testing with a rival — the bundled trailer
#   must be present, the user body must be spliced in complete, and the
#   system-default sentinel must lead. Each added rival drops/moves exactly one,
#   is correct on the rest of the shape, and carries a machine-checked witness
#   that ELABORATES against the rival and FAILS against gold (two real builds
#   per case). Included so every top-level structural sub-behaviour of the
#   single clause is attacked.
# PORTED BY AUDIT-2 (admissibility-f2p-shaped-selfcall -> admiss-f2p-shaped-order):
#   the sibling self-calls on an F2P-shaped input to prove the precondition admits
#   it. The first accounting recorded this lane VACUOUS on the ground that "this
#   bundle declares NO `require` clause, so there is no precondition to admit" —
#   which is precisely the reason that has been measured wrong across this corpus.
#   The lane is what detects PRECOND-TOO-STRONG, and its analogue on a require-free
#   TOTAL carrier is not "does a guard admit the input" but "is the obligation
#   SATISFIABLE, and non-degenerate, at an F2P-shaped input". The second clause of
#   that is what the old reasoning missed: "satisfiable everywhere by construction"
#   is an argument, and this gate prefers a build. Landed as a positive that
#   discharges the post-image by EVALUATION at the smallest F2P-shaped input (one
#   system-default entry, one user entry defining a message, one bundled entry
#   defining it too), conjoined with the two resolution facts that make the point
#   non-degenerate — the user-first order resolves to the USER value, the inverted
#   order to the BUNDLED value, and the two differ — before closing the frozen
#   obligation verbatim from a `clear`ed context. Liveness checked by flipping one
#   conjunct false (build FAILS, exit 1), so the `have` is load-bearing.
#   Note on tactic choice, since it is a per-carrier fact: `decide` closes this
#   conjunction and so does `simp [resolve]`; `rfl` FAILS on it and `norm_num` is
#   an unknown tactic in this workspace. `decide` is what ships.
# VACUOUS (frame-mutation-write-user-tr): the sibling carries this MANDATORY
#   because a project-source carrier is held at Acc(list_pred(.),1/2) and a rival
#   can illegally store into it. This backend is referentially transparent and
#   declares no `mut` binder over any input — every input is an immutable value
#   with no heap footprint — so there is no read-only cell to overwrite and no
#   substitute probe. Not fabricated (porting map: vacuous here).
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job (axiom_check.py validates
#   the deep A-reference `resolve` == the real message-catalog loader's
#   precedence). This bundle consumes no axiom `ensures`, and the gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 6 distinct input
# points, one per rival, no two shared):
#     repoDirs      — ["u"], [], ["a","b"], ["m"], ["g","h"], []: length
#                     varied (1, 0, 2, 1, 2, 0) and contents varied. TWO witnesses
#                     now sit at the empty list, and they are not redundant: they
#                     are the two OPPOSITE readings of that input.
#                     weak-drop-bundled-trailer is wrong there and everywhere else
#                     too, whereas weak-nearmiss-empty-drops-trailer is wrong there
#                     and CORRECT everywhere else — the empty list is the single
#                     point that separates "globally wrong" from "wrong only in the
#                     default configuration", so the clause's tightness at that
#                     point is what both probe from opposite sides. The two
#                     length-2 points are likewise not two spellings of one:
#                     ["a","b"] shows the user segment is spliced in at all, while
#                     ["g","h"] shows it is not internally reversed — a distinction
#                     length 1 cannot express, which is why last-wins needs it.
#     sysNone       — "s", "d", "x", "z", "i", "s": varied; the head-at-end rival
#                     is the one that actually depends on its position.
#     packageLocale — "p", "q", "y", "w", "j", "p": varied; the drop-trailer and
#                     near-miss rivals are the ones that depend on its presence.
#   Sub-domain coverage: five rivals are wrong on every input; exactly one
#   (weak-nearmiss-empty-drops-trailer) is gold-correct on a proper sub-domain
#   (every non-empty `repoDirs`) and wrong off it, so the battery probes pointwise
#   tightness and not only globally-wrong shapes. That property is PROVED, not
#   inferred from one agreeing point — see its `rationale` (iii).
#   Every top-level structural sub-behaviour of `out = sysNone :: (repoDirs ++
#   [packageLocale])` is attacked: ORDER (weak-prepatch-order segment swap,
#   weak-last-wins-reversed total inversion), TRAILER (weak-drop-bundled-trailer
#   globally, weak-nearmiss-empty-drops-trailer on a proper sub-domain), USER-BODY
#   (weak-drop-user-body), HEAD (weak-head-at-end). No binder is held at the same
#   value by every witness, and no two rivals share an input tuple.
#   NOT attacked, and named rather than elided: the TERMINATION obligation the
#   `total` semantics creates. See the docstring's divergence entry — the class is
#   real and the rival is genuinely rejected; what fails is the witness half, for a
#   demonstrated carrier reason (19 builds).
# WITNESS DISCRIMINATION (re-verified by AUDIT-2 with three real builds per reject
#   case, from scratch): each witness ELABORATES against its loop-free rival (the
#   extracted tester `decide`s to `false`, exit 0) and FAILS against the frozen
#   solution (gold's tester `decide`s to `true`, so `= false` is refuted, exit 1).
#   The THIRD build per case is the forgery control: the same file with the claim
#   flipped to `= true` and nothing else changed, which inverts both exit codes
#   (gold 0, rival 1) on every case — so each gold-side error is a function of the
#   CLAIM and not of the file, and none of these rejections rests on a tactic
#   mismatch, a missing identifier, a stuck reduction, or a timeout. No witness
#   binds a hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation and the gate's consistency probe is a no-op
#   here. No `sorry`/`admit`/`native_decide`/`axiom` appears in any witness.
AXIOM_TESTS = []
