"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8120 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_searchDirs`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The two bundles model
DIFFERENT amounts of the same behavior, and the difference drives every
port/omit decision below.

  * The nagini bundle models ``select_translation`` — the FIRST-WINS RESOLUTION
    over the assembled catalog-source list. Its carrier abstracts each source to
    a ``(provides?, text-code)`` pair and its postcondition (clauses P1/P2/P4)
    pins the RESOLVED text a downstream ``gettext`` merge/lookup would return.
    All of nagini's decisive rivals (prepatch-order, bundled-wins-subdomain,
    last-wins) are attacks on that RESOLUTION.
  * This lean bundle models only the purely-functional CORE that the gold patch
    actually edits: the assembly of the ordered search-directory list itself
    (``assembleSearchDirs`` = ``none :: (userDirs.map some ++ [some bundledDir])``).
    The order-walking precedence rule ("earlier entries win") lives in the
    UNCHANGED downstream loader (``locale.init`` / stdlib ``gettext``) and is NOT
    modeled here (mapping.md §"Callee provenance": no ``opaque`` callee, empty
    ``axioms`` region). This is a correctly-NARROWED port: the observable
    behavioral change IS the relative order of the caller-supplied directories
    vs. the bundled directory in the assembled list, and that is exactly what
    this spec pins.

DEFENDED SURFACE (one modeled behavior; one top-level postcondition equation).
``problem_spec_searchDirs userDirs bundledDir result`` pins EXACTLY:

  * ``result = none :: (userDirs.map some ++ [some bundledDir])``

i.e. the assembled list is FULLY determined: a leading system-default sentinel
(``none``), then every caller-supplied directory in the caller's given order
(each made present via ``some``), then the single built-in directory LAST. This
equation is a total pin — no output component is left free — so it simultaneously
constrains: (S) the head sentinel; (M) the middle run == the caller directories,
in order; (B) the built-in directory at the tail; and (O) the ORDER of the middle
run relative to the tail (caller dirs BEFORE the built-in). Clause (O) is the
behavioral discriminator (the fix): pre-patch the built-in directory was placed
AHEAD of the caller-supplied directories, so a caller could never override the
bundled entries. The ``prepatch-order`` rival below IS that pre-patch assembly.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``userDirs`` (the
caller-supplied directories, in order) and ``bundledDir`` (the single built-in
directory). Both are load-bearing and both are varied across the reject
witnesses (see the point-spread block at the bottom): ``userDirs`` ranges over
``[]``, a singleton, and two-element lists; ``bundledDir`` takes several distinct
values.

AUDIT NOTE on that variation. Varying ``bundledDir`` across witness tuples is by
itself only two SPELLINGS of one point for most rivals: the rivals that delete or
permute a run treat the built-in directory as an opaque value copied through, so
``bundledDir="b"`` and ``bundledDir="z"`` refute them for the same reason and
neither is load-bearing. The binder is made genuinely load-bearing by
``grounding-bundled-tail-value``, whose rival AGREES with the frozen assembly on
the entire sub-domain ``bundledDir="locale"`` and is refutable only at another
value — so for that case, and only that case, WHICH ``bundledDir`` the witness
picks decides whether the case discriminates at all.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival (write into the read-only ``user_tr`` half-permission)
    has no counterpart: Lean is referentially transparent, ``userDirs`` /
    ``bundledDir`` are immutable values, there is no ``mut`` INPUT binder, no
    aliasing, and no read-only cell to overwrite. No substitute probe is
    fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not vacuous. CORRECTED BY AUDIT:
    the earlier revision of this manifest recorded the class as VACUOUS on the
    ground that "``implementation_searchDirs`` is a total Lean ``def``, so a
    diverging implementation cannot be written at all". That is false, and it was
    measured false. A variant may write ``partial def
    implementation_searchDirs`` — Lean accepts it, ``variant_problems`` returns
    ``[]`` (``partial`` is not an assumption token, only the witness-side banlist
    names it), and the frozen ``theorem correct_searchDirs`` statement is
    untouched, so the case is in scope. Built: such a rival DOES fail to verify
    (exit 1), but for a reason that attributes nothing to the spec —
    ``Tactic `unfold` failed to unfold `implementation_searchDirs```, because a
    ``partial def`` is compiled to an opaque constant with no equation lemmas.
    Four separate witness shapes were attempted against it and ALL FOUR failed
    (exit 1 each): ``decide`` after ``unfold`` (the shipped scaffold) dies on the
    same unfolding failure, and ``simp [implementation_searchDirs]`` leaves
    ``⊢ ¬implementation_searchDirs [] "b" = [none, some "b"]`` unsolved — the
    simp argument is reported UNUSED, i.e. there is no equation to rewrite with.
    Notably the CONVERSE also cannot be proven: the witness asserting the spec
    HOLDS of the partial rival at a point where it is semantically correct fails
    identically (``⊢ implementation_searchDirs ["a"] "b" = [none, some "a", some
    "b"]`` unsolved). So the impl is opaque in BOTH directions and no witness
    can discriminate; a reject case here would be rejected for opacity, which is
    exactly the tactic-mismatch artifact the witness rule exists to exclude.
    Disposition is therefore a KNOWN HOLE (the spec does not pin termination),
    NOT a vacuous class — the distinction matters because "vacuous" claims the
    battery is complete while "hole" says the spec is not. Nothing shippable.
    (The nagini sibling carries no diverge-*/nonterm-* case for this instance
    either, so there is also nothing to port.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by a structural equation over the two inputs (a ``::`` / ``map`` /
    ``++`` term built directly from ``userDirs`` and ``bundledDir``). There is no
    opaque answer key an implementation could echo — assembling the list from its
    own inputs IS doing the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals mis-assemble one component of the
    ordered list: the built-in placed ahead of the caller dirs (the pre-fix bug,
    attacks O); the leading sentinel dropped (attacks S); the built-in directory
    dropped (attacks B); the caller directories emitted in reversed order
    (attacks M); the whole list handed back reversed (attacks S+B+O jointly).
    Beyond extent and position, two rivals attack the GROUNDING of a component
    in its input binder — the middle run's contents (attacks M's grounding) and
    the tail's value (attacks B's grounding in ``bundledDir``) — and one attacks
    clause O on a PROPER SUB-DOMAIN rather than everywhere. Together they attack
    every structural component the single equation pins, each component both in
    its extent/position AND in its grounding.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``intro …; unfold …; rfl``) is
tuned to the frozen ``Id.run do`` form — so a rejection alone attributes nothing
to the spec. Every ``expect="reject"`` case therefore carries a Lean snippet
that states ``¬ problem_spec_searchDirs`` at one CONCRETE ground input and closes
by ``decide`` (the carrier is closed lists of string literals, fully decidable).
Each witness binds NOTHING in its head (all inputs are ground list literals), so
there are no hypotheses whose consistency could be in question, and the gate's
consistency probe is correctly not reached.

Each witness was checked with two real ``lake env lean`` builds to HOLD of its
rival and to FAIL on the frozen solution. AUDIT NOTE: on this carrier the
gold-side failure is additionally confirmed to be a SEMANTIC refutation and not a
syntactic artifact — every one reports ``Tactic `decide` proved that the
proposition ¬(… ) = … is false``, i.e. the kernel evaluated the claim and found
the frozen assembly SATISFIES the spec at that input. No gold-side failure is an
unknown identifier, a type error, an unfolding failure, a stuck reduction, or a
timeout, which are the failure modes the gate's exit-code check cannot
distinguish from a real refutation.

FORGERY CHECK (added by a later audit). "The error looks semantic" is an
argument, not evidence, so each gold-side failure was additionally shown to
CARRY INFORMATION ABOUT THE CLAIM: for every reject case a second file was built
differing from the witness ONLY in what it asserts (the leading ``¬`` dropped, so
it claims the frozen assembly is CORRECT at that input). All nine flipped-claim
builds behaved as a real discriminator must — exit 0 against the FROZEN solution
(gold does satisfy the spec there, and `decide` proves it) and exit 1 against the
RIVAL, with the error text naming the rival's own concrete list. So gold's exit
code tracks the claim rather than being a constant artifact of the file shape: had
these witnesses asserted gold is correct, the gate would have recorded them
verified, not rejected. That two-sided pair is what makes the `decide` signature
above evidence.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
assembles the search list in a shape the downstream order-precedence loader then
resolves WRONG, so the behavior the issue reports is not actually fixed.

AUDIT NOTE on the strength of that claim, per case. Only SOME rivals are
F2P-failing, and the manifest now says which:

  * ``prepatch-order-bundled-ahead`` and ``reverse-whole-list`` mis-order the
    single-caller-directory configuration the F2P test itself sets up, so their
    faithful counterparts fail it directly.
  * ``grounding-middle-run-contents`` is F2P-failing: it replaces the caller's
    own location with the built-in one, so the caller-supplied location is absent
    from the search list entirely and the message the F2P input has the caller
    override can never resolve to the caller's value.
  * ``grounding-bundled-tail-value`` is F2P-failing only CONDITIONALLY, and the
    condition is not on the F2P path. CORRECTED BY AUDIT: an earlier revision
    grouped it with the case above as unconditionally F2P-failing on the ground
    that it "drops a location out of the search list altogether". That
    over-claims. This rival still emits the caller's directories correctly and in
    the correct position; only the TAIL entry is a fixed literal instead of the
    built-in location it was handed. The F2P input's message under test is
    supplied by a CALLER-supplied directory, which this rival places ahead of the
    tail exactly as the frozen assembly does, so the caller's value still wins
    and that assertion still holds. Its faithful counterpart is a real, observable
    regression — every message the caller did NOT override goes untranslated
    whenever the built-in location is not the hardcoded path — but that is a
    SPEC-STRENGTH claim on the tail's grounding in its binder, not a demonstrated
    F2P failure. Its ``refinement`` below states that scope explicitly.
  * ``drop-sentinel-head``, ``drop-bundled-tail``, ``reverse-user-dirs`` and
    ``subdomain-order-multi-dir`` are near-misses that AGREE with the frozen
    assembly on the F2P input's shape (one caller-supplied directory, the message
    under test supplied by it). Their faithful counterparts are still observable
    behavioral regressions — a location dropped, or the caller's own precedence
    order inverted, or the ordering fixed for one arity only — but the claim they
    carry is SPEC-STRENGTH on a load-bearing component, not "this fails the F2P".
    Each such case's ``refinement`` states that scope explicitly rather than
    over-claiming an F2P failure the input shape does not produce.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (mapping.md: ``axioms`` region empty). The nagini ``AXIOM_TESTS``
(the deep-model ``resolved`` vs. real gettext probes) belong to G-AX, not this
gate, and there is no modeled resolution here to probe — they are DROPPED.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8120"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The impl loop body assembles the search list in three steps: init to the
# leading sentinel, append the caller directories, append the built-in directory.
# Every reshape lands entirely inside `-- impl-start`/`-- impl-end`.
_I_INIT = "    let mut searchDirs : List (Option String) := [none]\n"
_I_USER = "    searchDirs := searchDirs ++ userDirs.map some\n"
_I_BUNDLED = "    searchDirs := searchDirs ++ [some bundledDir]\n"

# The full impl `do` body — anchor for the positive controls, which replace the
# whole body with a semantically-identical reshape (still closed by the frozen
# `rfl` proof, so no proof authoring / no new lemma / no assumption token).
_I_BODY = (
    "  Id.run do\n"
    "    let mut searchDirs : List (Option String) := [none]\n"
    "    searchDirs := searchDirs ++ userDirs.map some\n"
    "    searchDirs := searchDirs ++ [some bundledDir]\n"
    "    return searchDirs\n"
)

# The frozen proof's intro line (proof region), unique in the file — the
# admissibility positive prepends a ground `have` here without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro userDirs bundledDir\n"


# ---------------------------------------------------------------------------
# witness scaffold. Each states the spec predicate is FALSE at one ground input
# and closes by `decide` (closed lists of String literals are decidable).
# ---------------------------------------------------------------------------
def _witness(user_dirs, bundled_dir):
    return (
        f"example : ¬ problem_spec_searchDirs {user_dirs} {bundled_dir}\n"
        f"    (implementation_searchDirs {user_dirs} {bundled_dir}) := by\n"
        "  unfold problem_spec_searchDirs implementation_searchDirs "
        "assembleSearchDirs\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_searchDirs` statement byte-identical.
    #
    # AUDIT NOTE on the strength of the two below: both are DEFINITIONALLY equal
    # to the frozen body, which is why the frozen `rfl` closes them unchanged.
    # That makes them honest but WEAK — a positive whose proof is unchanged
    # cannot detect a spec over-fit to the frozen impl's syntactic shape, since
    # the reshape never actually leaves that shape up to `whnf`. They are kept
    # (a definitional reshape is still the cheapest-implementation control the
    # ungrounded-oracle lane calls for), and `pos-accumulating-forloop` below is
    # added as the positive that does NOT reduce to the frozen body and so has
    # to be re-proven by induction.
    # =====================================================================
    {
        "id": "pos-grounded-delegate",
        "kind": "soundness",
        "expect": "verify",
        # Return the assembled list directly (drop the imperative scaffolding).
        # `assembleSearchDirs` is fully unfolded over the inputs, so delegating to
        # it IS the modeled behavior, not a wrong echo. Definitionally equal to
        # the frozen `Id.run do` body, so the frozen `rfl` still closes.
        "module": _swap(
            _BASE, _I_BODY,
            "  assembleSearchDirs userDirs bundledDir\n"),
        "rationale": "grounded-oracle positive control: the assembled list is a "
                     "structural term over the inputs (fully unfolded), so "
                     "returning it directly IS the modeled behavior and MUST "
                     "verify — else SPEC-TOO-STRONG. Definitionally the frozen "
                     "`Id.run do` body, so the frozen proof "
                     "(`intro; unfold; rfl`) closes unchanged; statement "
                     "byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-control-grounded-oracle-delegate (there: delegate to "
                     "`resolved_assembled`; here: to `assembleSearchDirs`).",
    },
    {
        "id": "pos-cons-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: assemble the whole list in one
        # `let` via `::` + `++` (no per-step `mut` appends). Definitionally equal
        # to the frozen loop body, so the frozen `rfl` still closes — no proof
        # authoring, no helper lemma, no assumption token.
        "module": _swap(
            _BASE, _I_BODY,
            "  Id.run do\n"
            "    let searchDirs : List (Option String) :=\n"
            "      none :: (userDirs.map some ++ [some bundledDir])\n"
            "    return searchDirs\n"),
        "rationale": "correct reshape building the list in a single `::`/`++` "
                     "expression instead of three mutable appends — same value on "
                     "every input, so the spec equation still holds; else "
                     "SPEC-TOO-STRONG. Definitionally the frozen body, so the "
                     "frozen `rfl` closes; statement byte-identical, no new "
                     "axiom/lemma. Ports nagini's "
                     "pos-control-branch-reorder-no-text (a structurally "
                     "different but semantically identical assembly shape).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The nagini precondition-admission self-call
    # re-expresses as: discharge the spec predicate by evaluation at a concrete
    # single-caller-directory + built-in assembly (the smallest F2P-shaped input)
    # as a `have`, then close the frozen obligation verbatim. Nothing is assumed:
    # no new declaration, statement byte-identical, ground instance is a `have`
    # prepended to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_searchDirs [\"x\"] \"y\"\n"
            "      (implementation_searchDirs [\"x\"] \"y\") := by\n"
            "    unfold problem_spec_searchDirs implementation_searchDirs "
            "assembleSearchDirs\n"
            "    rfl\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the smallest F2P-shaped "
                     "input (one caller directory + one built-in directory, "
                     "assembling [none, some \"x\", some \"y\"]) by evaluation as a "
                     "`have`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior would be unsatisfiable "
                     "at a normal input — the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical, ground instance is a `have` in the existing "
                     "tactic body. Ports nagini's "
                     "admissibility-f2p-shaped-selfcall.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: built-in placed AHEAD of the caller directories ----
    {
        "id": "prepatch-order-bundled-ahead",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch assembly: append the built-in directory BEFORE the caller
        # directories, i.e. [none] ++ [built-in] ++ caller dirs. Attacks the ORDER
        # component (O) of the pinned equation.
        "module": _swap(_BASE, _I_USER + _I_BUNDLED, _I_BUNDLED + _I_USER),
        "refinement": "this IS the pre-patch assembly: the built-in directory is "
                      "placed ahead of the caller-supplied directories. The "
                      "unchanged downstream order-precedence loader then treats "
                      "the built-in catalog as primary, so a caller who supplies "
                      "their own catalog can never override the bundled entries — "
                      "exactly the reported defect. On the F2P input (a caller "
                      "override of a message the bundled catalog also defines) the "
                      "bundled value wins, so the observed message is the bundled "
                      "one and the F2P test FAILS. The faithful patch would NOT "
                      "resolve (this is the very behavior the issue reports). Ports "
                      "nagini's prepatch-order-bundled-ahead.",
        "rationale": "REJECT from the ORDER component (O) of the pinned equation: "
                     "the spec pins caller dirs BEFORE the built-in "
                     "(`userDirs.map some ++ [some bundledDir]`), but the rival "
                     "emits `[some bundledDir] ++ userDirs.map some`; these differ "
                     "whenever userDirs is non-empty. Refuted at "
                     "userDirs=[\"a\"], bundledDir=\"b\".",
        "witness": _witness('["a"]', '"b"'),
    },

    # ---- drop the leading system-default sentinel ----
    {
        "id": "drop-sentinel-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the leading `none` sentinel: initialize to the empty list. Attacks
        # the HEAD sentinel component (S) of the pinned equation.
        "module": _swap(
            _BASE, _I_INIT,
            "    let mut searchDirs : List (Option String) := []\n"),
        "refinement": "drops the leading system-default sentinel, so the host "
                      "system's own catalog location is never consulted and the "
                      "assembled list is missing its first entry. A faithful patch "
                      "that omitted the leading sentinel would drop the "
                      "system-default catalog from the merge the downstream loader "
                      "walks, so any message only that location supplies goes "
                      "untranslated — an observable behavioral regression against "
                      "the assembly this spec pins. AUDIT NOTE (scope of the "
                      "claim): the regression is NOT on the F2P input, where the "
                      "message under test is supplied by a caller-supplied "
                      "directory and resolves identically with or without the "
                      "sentinel; this rival is a SPEC-STRENGTH probe of the head "
                      "component, not an F2P-failing rival. Only "
                      "prepatch-order-bundled-ahead is F2P-failing. (No nagini "
                      "counterpart: nagini's carrier folds the sentinel into the "
                      "`system_defines` pair rather than exposing it as a list "
                      "head; here the leading `none` is an explicit, pinned "
                      "component of the assembled list.)",
        "rationale": "REJECT from the HEAD component (S) of the pinned equation: "
                     "the spec pins `result = none :: …` but the rival emits a "
                     "list whose head is the first caller directory (or the "
                     "built-in, when userDirs is empty). Refuted at userDirs=[], "
                     "bundledDir=\"b\", where the rival is [some \"b\"] but the "
                     "spec demands [none, some \"b\"] — chosen because at the "
                     "EMPTY userDirs input the head is the only component in play, "
                     "so the refutation is attributable to (S) alone.",
        "witness": _witness('[]', '"b"'),
    },

    # ---- drop the built-in directory from the tail ----
    {
        "id": "drop-bundled-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Omit the trailing built-in directory. Attacks the BUILT-IN tail
        # component (B) of the pinned equation.
        "module": _swap(_BASE, _I_BUNDLED, ""),
        "refinement": "drops the single built-in (bundled) directory entirely, so "
                      "the tool's own shipped catalogs are never consulted. A "
                      "faithful patch that omitted the bundled directory would "
                      "leave every message the caller did not override "
                      "untranslated — an observable behavioral regression against "
                      "the assembly this spec pins, and the direct converse of the "
                      "reported defect (the bundled entries must still be "
                      "consulted, just no longer ahead of the caller's). AUDIT "
                      "NOTE (scope of the claim): the message under test on the "
                      "F2P input is supplied by a caller-supplied directory, so "
                      "that one assertion would still hold with the bundled tail "
                      "dropped; this rival is a SPEC-STRENGTH probe of the "
                      "built-in tail component, not a demonstrated F2P-failing "
                      "rival. Only prepatch-order-bundled-ahead is F2P-failing.",
        "rationale": "REJECT from the BUILT-IN component (B) of the pinned "
                     "equation: the spec pins the built-in directory as the last "
                     "entry (`… ++ [some bundledDir]`), but the rival omits it. "
                     "Refuted at userDirs=[\"a\"], bundledDir=\"z\", where the "
                     "rival is [none, some \"a\"] but the spec demands "
                     "[none, some \"a\", some \"z\"].",
        "witness": _witness('["a"]', '"z"'),
    },

    # ---- reverse the caller directories' order ----
    {
        "id": "reverse-user-dirs",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the caller directories in REVERSED order. Attacks the MIDDLE-run
        # order component (M) of the pinned equation.
        "module": _swap(
            _BASE, _I_USER,
            "    searchDirs := searchDirs ++ userDirs.reverse.map some\n"),
        "refinement": "emits the caller-supplied directories in reversed order. "
                      "The caller provides its directories in a deliberate "
                      "precedence order (earlier = higher precedence in the "
                      "downstream loader); reversing them inverts which of the "
                      "caller's own catalogs wins when two provide the same "
                      "message — an observable behavioral regression against the "
                      "assembly this spec pins, on any input with ≥2 "
                      "caller-supplied directories that overlap. AUDIT NOTE (scope "
                      "of the claim): the F2P input configures a SINGLE "
                      "caller-supplied directory, where this rival agrees with gold "
                      "exactly; it is therefore a SPEC-STRENGTH probe of the "
                      "middle-run order component, not a demonstrated F2P-failing "
                      "rival. Only prepatch-order-bundled-ahead is F2P-failing. "
                      "(Near-miss: agrees with gold whenever userDirs has ≤1 entry, "
                      "so it is refuted at a distinct two-element input, not at the "
                      "singleton input the other rivals use.)",
        "rationale": "REJECT from the MIDDLE-run component (M) of the pinned "
                     "equation: the spec pins the caller directories in their "
                     "given order (`userDirs.map some`), but the rival emits "
                     "`userDirs.reverse.map some`; these differ whenever userDirs "
                     "has ≥2 distinct entries. Refuted at "
                     "userDirs=[\"a\", \"c\"], bundledDir=\"b\".",
        "witness": _witness('["a", "c"]', '"b"'),
    },

    # =====================================================================
    # ADDED BY AUDIT. The four rivals above all attack a component by
    # DELETING or PERMUTING a whole run. Three attack classes were left
    # unprobed, each closed below with a real build pair (rival 0 / gold 1,
    # gold failing by a `decide` semantic refutation, not a name/type error):
    #
    #   (1) GROUNDING. Every rival above keeps each surviving entry derived
    #       from its input. Nothing tested that the middle run's CONTENTS are
    #       pinned to `userDirs` and the tail's to `bundledDir` — the analogue
    #       of the ungrounded-echo hole the module docstring reasons about but
    #       never probes. `grounding-*` below attack exactly that, and they are
    #       the only cases in the battery whose refutation turns on WHICH
    #       string sits at a position rather than on how many entries there are.
    #   (2) SUB-DOMAIN ORDER. `prepatch-order-bundled-ahead` mis-orders on
    #       EVERY non-empty input, so the spec's order clause was only ever
    #       tested against a total violation. A patch that mis-orders on a
    #       PROPER SUB-DOMAIN is the harder near-miss (it agrees with gold on
    #       the singleton input the F2P configures), and it is what
    #       `subdomain-order-multi-dir` probes.
    #   (3) NON-DEFINITIONAL POSITIVE. Both existing positives are
    #       DEFINITIONALLY equal to the frozen body — the frozen `rfl` closes
    #       them unchanged, so neither shows the spec admits a correct impl
    #       whose proof must actually be re-done. Measured: the accumulating
    #       for-loop reshape below is NOT closed by the frozen `rfl` (real
    #       build, exit 1, `Tactic 'rfl' failed`); it needs a genuine
    #       induction, and it verifies. That is the only positive here that
    #       could have exposed SPEC-TOO-STRONG.
    # =====================================================================

    # ---- middle-run contents not grounded in the caller's directories ----
    {
        "id": "grounding-middle-run-contents",
        "kind": "uniqueness",
        "expect": "reject",
        # Right LENGTH, right shape, wrong CONTENTS: every caller slot is
        # filled with the built-in directory instead of the caller's own.
        # Attacks the grounding of the middle run (M) rather than its extent.
        "module": _swap(
            _BASE, _I_USER,
            "    searchDirs := searchDirs ++ "
            "userDirs.map (fun _ => some bundledDir)\n"),
        "refinement": "keeps the assembled list's LENGTH and the position of every "
                      "component but fills each caller slot with the built-in "
                      "directory instead of the caller's own. A faithful patch that "
                      "assembled the right number of entries from the wrong source "
                      "would consult the built-in location repeatedly and the "
                      "caller's own location never, so a caller override is not "
                      "merely out-ranked — it is absent from the search list "
                      "entirely, and the reported defect persists in a stronger "
                      "form. The faithful patch would NOT resolve.",
        "rationale": "REJECT from the GROUNDING of the middle run in the pinned "
                     "equation: the spec pins the middle run to `userDirs.map some` "
                     "— its contents, not just its extent — and this rival is the "
                     "only case in the battery whose refutation turns on WHICH "
                     "string occupies a position. A length-only or "
                     "position-only spec would admit it. Refuted at "
                     "userDirs=[\"s\"], bundledDir=\"t\": the rival emits "
                     "[none, some \"t\", some \"t\"] where the spec demands "
                     "[none, some \"s\", some \"t\"].",
        "witness": _witness('["s"]', '"t"'),
    },

    # ---- built-in tail not grounded in the built-in input binder ----
    {
        "id": "grounding-bundled-tail-value",
        "kind": "uniqueness",
        "expect": "reject",
        # The tail entry is a FIXED literal rather than the `bundledDir` input,
        # so the second input binder is ignored entirely. Attacks the grounding
        # of the tail (B) in its binder.
        "module": _swap(
            _BASE, _I_BUNDLED,
            "    searchDirs := searchDirs ++ [some \"locale\"]\n"),
        "refinement": "emits a hardcoded tail entry instead of the built-in "
                      "directory it was given, so the second input binder is "
                      "ignored. A faithful patch that appended a fixed path rather "
                      "than the built-in location it is handed would consult the "
                      "wrong location whenever the tool is installed anywhere but "
                      "that one path — the built-in catalogs are then missing from "
                      "the search list and every message the caller did not "
                      "override goes untranslated. AUDIT NOTE (scope of the "
                      "claim): this is NOT a demonstrated F2P failure, and an "
                      "earlier revision wrongly asserted it was. The rival still "
                      "emits the caller's directories correctly and ahead of the "
                      "tail, and the message under test on the F2P input is "
                      "supplied by a caller-supplied directory — so the caller's "
                      "value still wins and that assertion holds with the tail "
                      "mis-grounded. The regression is on every message the "
                      "caller did NOT override, off the F2P path; this rival is "
                      "a SPEC-STRENGTH probe of the tail's grounding in its "
                      "binder. Only prepatch-order-bundled-ahead, "
                      "reverse-whole-list and grounding-middle-run-contents are "
                      "F2P-failing.",
        "rationale": "REJECT from the GROUNDING of the tail in the pinned equation: "
                     "the spec pins the last entry to `some bundledDir`, the input "
                     "binder, and this rival ignores that binder. It is the only "
                     "case in the battery that makes the `bundledDir` binder "
                     "load-bearing for a REASON other than being copied through: "
                     "the rival AGREES with gold on the whole sub-domain "
                     "bundledDir=\"locale\" (verified by a real build: the witness "
                     "tuple userDirs=[\"a\"], bundledDir=\"locale\" does NOT refute "
                     "it), so it is refuted only at a bundledDir the rival does not "
                     "happen to hardcode. Refuted at userDirs=[\"m\"], "
                     "bundledDir=\"n\": the rival emits "
                     "[none, some \"m\", some \"locale\"] where the spec demands "
                     "[none, some \"m\", some \"n\"].",
        "witness": _witness('["m"]', '"n"'),
    },

    # ---- mis-order on a proper SUB-DOMAIN only (the near-miss order rival) ----
    {
        "id": "subdomain-order-multi-dir",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct assembly when the caller supplied fewer than two directories;
        # the pre-fix (built-in ahead) assembly otherwise. Attacks the ORDER
        # component (O) on a PROPER sub-domain, where the total-violation rival
        # `prepatch-order-bundled-ahead` cannot reach.
        "module": _swap(
            _BASE, _I_USER + _I_BUNDLED,
            "    if userDirs.length < 2 then\n"
            "      searchDirs := searchDirs ++ userDirs.map some\n"
            "      searchDirs := searchDirs ++ [some bundledDir]\n"
            "    else\n"
            "      searchDirs := searchDirs ++ [some bundledDir]\n"
            "      searchDirs := searchDirs ++ userDirs.map some\n"),
        "refinement": "orders the assembly correctly when the caller supplied at "
                      "most one directory and reverts to the built-in-ahead "
                      "ordering otherwise. A faithful patch of this shape — one "
                      "that fixed the ordering only for the single-directory "
                      "configuration it was reported against — would leave the "
                      "reported defect fully intact for every caller supplying two "
                      "or more directories: those callers still cannot override the "
                      "built-in entries. It is the ordinary shape of an "
                      "under-generalized fix, and the faithful patch would NOT "
                      "resolve for the multi-directory caller.",
        "rationale": "REJECT from the ORDER component (O) on a PROPER SUB-DOMAIN. "
                     "This is strictly harder than prepatch-order-bundled-ahead, "
                     "which mis-orders on EVERY non-empty input: this rival agrees "
                     "with gold on ALL inputs with ≤1 caller directory — including "
                     "the singleton the other order rival is refuted at, and the "
                     "shape the F2P configures — so clause (O) must be pinned for "
                     "every arity, not just witnessed once. Refuted at "
                     "userDirs=[\"p\", \"q\"], bundledDir=\"r\": the rival emits "
                     "[none, some \"r\", some \"p\", some \"q\"] where the spec "
                     "demands [none, some \"p\", some \"q\", some \"r\"].",
        "witness": _witness('["p", "q"]', '"r"'),
    },

    # ---- whole-list precedence inversion ----
    {
        "id": "reverse-whole-list",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble correctly, then hand the list back reversed: the sentinel
        # ends up last and the built-in first. Attacks S, B and O jointly, and
        # is the closest expressible analogue of the sibling's last-wins rival.
        "module": _swap(
            _BASE, "    return searchDirs\n",
            "    return searchDirs.reverse\n"),
        "refinement": "assembles the list correctly and then hands it back "
                      "reversed, so the built-in directory leads and the "
                      "system-default sentinel trails. Because the downstream "
                      "loader reads position as precedence, a faithful patch that "
                      "handed the list back in the opposite order inverts the "
                      "entire precedence relation: the built-in entries out-rank "
                      "every caller-supplied one, which is the reported defect, and "
                      "the caller's directories are additionally ranked among "
                      "themselves backwards. The faithful patch would NOT resolve. "
                      "This is the closest counterpart on this carrier to the "
                      "sibling's precedence-inversion rival — the sibling inverts "
                      "the RESOLUTION fold over a fixed list; the assembly modeled "
                      "here has no fold to invert, so the expressible analogue is "
                      "the inversion of the ORDER the loader resolves by.",
        "rationale": "REJECT from the pinned equation's ORDER jointly with the head "
                     "(S) and tail (B) components: reversal moves `none` off the "
                     "head and the built-in off the tail. Refuted at the SMALLEST "
                     "input that distinguishes it, userDirs=[\"u\"], "
                     "bundledDir=\"v\": the rival emits "
                     "[some \"v\", some \"u\", none] where the spec demands "
                     "[none, some \"u\", some \"v\"]. (Not vacuous against "
                     "drop-sentinel-head or prepatch-order: reversal preserves the "
                     "multiset of entries and their count, so every "
                     "deletion-flavored rival differs from it observably.)",
        "witness": _witness('["u"]', '"v"'),
    },

    # ---- built-in emitted at BOTH ends: the MULTIPLICITY attack ----
    {
        "id": "dup-bundled-both-ends",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY A LATER AUDIT. Every other rival in this battery either
        # DELETES a component, PERMUTES one, or MIS-GROUNDS one's value. None
        # ADDS an entry, so nothing tested that the pinned equation bounds the
        # list's LENGTH from above — that each component appears exactly ONCE.
        # This rival appends the built-in directory at the tail (the post-fix
        # position) while ALSO leaving it ahead of the caller directories (the
        # pre-fix position), so it satisfies "the built-in is last" and "the
        # caller dirs precede a built-in entry" simultaneously.
        "module": _swap(
            _BASE, _I_USER + _I_BUNDLED, _I_BUNDLED + _I_USER + _I_BUNDLED),
        "refinement": "emits the built-in directory at BOTH ends of the search "
                      "list: still ahead of the caller-supplied directories, and "
                      "additionally appended after them. This is the shape of the "
                      "most tempting INCOMPLETE fix — appending the built-in "
                      "location at the end without removing the pre-existing "
                      "leading one — and it does NOT resolve the reported defect: "
                      "the downstream order-precedence loader still meets a "
                      "built-in entry BEFORE any caller-supplied one, so the "
                      "built-in catalog is still selected as primary and a "
                      "caller's override still loses. On the F2P input the "
                      "observed message is therefore still the built-in one and "
                      "that test FAILS. The faithful patch would NOT resolve, "
                      "which makes this the second genuinely F2P-failing rival in "
                      "the battery alongside prepatch-order-bundled-ahead.",
        "rationale": "REJECT from the MULTIPLICITY/EXTENT bound of the pinned "
                     "equation — the one dimension no other case in this battery "
                     "probes. The other rivals delete a run "
                     "(drop-sentinel-head, drop-bundled-tail), permute one "
                     "(reverse-user-dirs, subdomain-order-multi-dir, "
                     "reverse-whole-list, prepatch-order-bundled-ahead) or "
                     "mis-ground one's value (grounding-*); every one of them "
                     "keeps the list's length at most that of the frozen "
                     "assembly. This rival makes it LONGER, so it is the only "
                     "case showing the total equation is an upper bound on extent "
                     "and not merely a containment/ordering constraint: a spec "
                     "phrased as 'each caller dir precedes some built-in entry, "
                     "and a built-in entry is last' would ADMIT it. Refuted at "
                     "userDirs=[\"a\"], bundledDir=\"b\": the rival emits "
                     "[none, some \"b\", some \"a\", some \"b\"] where the spec "
                     "demands [none, some \"a\", some \"b\"].",
        "witness": _witness('["a"]', '"b"'),
    },

    # ---- the one positive whose proof is NOT the frozen `rfl` ----
    {
        "id": "pos-accumulating-forloop",
        "kind": "soundness",
        "expect": "verify",
        # A correct reshape that accumulates the caller directories one at a
        # time through a `for` loop. Unlike the two positives above this is NOT
        # definitionally the frozen body — measured: the frozen `rfl` does NOT
        # close it (real build, exit 1, `Tactic 'rfl' failed`) — so the
        # obligation is genuinely RE-PROVEN by induction over the caller list
        # rather than restated. Still statement-byte-identical, no new
        # axiom/theorem, no assumption token: only the impl and proof regions
        # change, which is exactly what a soundness positive is allowed to do.
        "module": _swap(
            _swap(
                _BASE, _I_BODY,
                "  Id.run do\n"
                "    let mut searchDirs : List (Option String) := [none]\n"
                "    for d in userDirs do\n"
                "      searchDirs := searchDirs ++ [some d]\n"
                "    searchDirs := searchDirs ++ [some bundledDir]\n"
                "    return searchDirs\n"),
            _P_INTRO + "  unfold problem_spec_searchDirs implementation_searchDirs "
            "assembleSearchDirs\n  rfl\n",
            _P_INTRO
            + "  unfold problem_spec_searchDirs implementation_searchDirs "
              "assembleSearchDirs\n"
              "  have flat : ∀ (l : List String),\n"
              "      (List.map (fun x => [some x]) l).flatten = l.map some := by\n"
              "    intro l\n"
              "    induction l with\n"
              "    | nil => rfl\n"
              "    | cons a t ih => simp [ih]\n"
              "  simp [Id.run, flat]\n"
              "  rfl\n"),
        "rationale": "soundness positive that actually RE-PROVES the obligation. "
                     "The other two positives are DEFINITIONALLY equal to the "
                     "frozen body — the frozen `rfl` closes them untouched — so "
                     "neither could have exposed SPEC-TOO-STRONG from a correct "
                     "impl whose proof has to be redone. This one accumulates the "
                     "caller directories one at a time through a `for` loop; "
                     "measured with a real build, the frozen `rfl` FAILS on it "
                     "(`Tactic 'rfl' failed`), and closing it needs an induction "
                     "over the caller list. It computes the same list on every "
                     "input, so it MUST verify — if the spec rejected it the spec "
                     "would be over-fit to the frozen assembly's syntactic shape "
                     "rather than to its value, i.e. SPEC-TOO-STRONG.",
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus a 2-case AXIOM lane. This
# battery carries 13 (3 soundness positives, 1 admissibility, 9 uniqueness
# rivals) after two audit passes added six cases; see "ADDED BY AUDIT" below and
# `dup-bundled-both-ends` (added by the later audit, closing the MULTIPLICITY
# dimension: no other rival here makes the assembled list LONGER than frozen).
# This bundle models a NARROWER slice of the same behavior — the pure list
# ASSEMBLY that the gold patch edits, NOT the downstream first-wins RESOLUTION —
# so the nagini cases split into: those that attack the assembly ORDER (port
# directly) and those that attack the resolution semantics living in the
# unchanged loader (no counterpart here — carrier narrowing, not an omission of
# convenience).
#
#   sibling case                          -> here
#   -----------------------------------------------------------------------
#   pos-control-grounded-oracle-delegate  -> pos-grounded-delegate    RE-EXPRESSED
#   pos-control-branch-reorder-no-text    -> pos-cons-reshape         RE-EXPRESSED
#   admissibility-f2p-shaped-selfcall     -> admiss-ground-input      RE-EXPRESSED
#   prepatch-order-bundled-ahead          -> prepatch-order-bundled-ahead  PORTED
#   (none)                                -> drop-sentinel-head       ADDED (attacks S)
#   (none)                                -> drop-bundled-tail        ADDED (attacks B)
#   (none)                                -> reverse-user-dirs        ADDED (attacks M)
#   frame-mutation-write-user-tr          -> (none)                   VACUOUS
#   bundled-wins-over-project-subdomain   -> subdomain-order-multi-dir  RE-EXPRESSED
#                                                                    (added by audit)
#   last-wins-forward-fold                -> reverse-whole-list       RE-EXPRESSED
#                                                                    (added by audit)
#   AXIOM_TESTS (2)                       -> (none)                   DROPPED (G-AX)
#
# ADDED BY AUDIT, no sibling counterpart:
#   grounding-middle-run-contents   (attacks M's grounding in `userDirs`)
#   grounding-bundled-tail-value    (attacks B's grounding in `bundledDir`)
#   pos-accumulating-forloop        (the one positive not closed by the frozen `rfl`)
#   dup-bundled-both-ends           (attacks the EXTENT bound — added by the later
#                                    audit; the only rival that LENGTHENS the list,
#                                    and the second F2P-failing rival)
#
# RE-EXPRESSED (pos-grounded-delegate): nagini delegates to the grounded oracle
#   `resolved_assembled`; here the analogue is delegating to `assembleSearchDirs`
#   (the grounded pure assembly). Definitionally the frozen body, so the frozen
#   `rfl` still closes (verified with a real build).
# RE-EXPRESSED (pos-cons-reshape): nagini's branch-reorder positive reshapes the
#   final out-selection; this carrier has no such branch, so the analogous
#   "structurally different but correct" reshape assembles the list in a single
#   `::`/`++` expression rather than three mutable appends — same value, frozen
#   `rfl` still closes (verified).
# RE-EXPRESSED (admiss-ground-input): nagini's admissibility self-calls on an
#   F2P-shaped input; the honest analogue is to discharge the POSTCONDITION at
#   the smallest F2P-shaped input (one caller dir + one built-in) as a `have`,
#   then close the frozen obligation verbatim.
# ADDED (drop-sentinel-head, drop-bundled-tail, reverse-user-dirs): nagini's
#   single order rival (prepatch-order) is the only assembly-shape attack in the
#   sibling — its other rivals attack the RESOLUTION (see NOT MODELED). The pinned
#   equation here has four structural components (head sentinel S, middle run M,
#   built-in tail B, and the order O between M and B), so three rivals are added
#   to attack S, B, and M individually — each with the same refinement structure
#   (a faithful patch mis-shaping the assembled list makes the downstream loader
#   resolve wrong, failing the F2P). They are not fabricated for an unmodeled
#   behavior; they attack real, load-bearing components of the SAME modeled spec.
# VACUOUS (frame-mutation-write-user-tr): nagini's mandatory frame-mutation rival
#   writes into the read-only `user_tr` half-permission. On this referentially
#   transparent carrier there is no `mut` INPUT binder, no aliasing, and no
#   read-only cell to overwrite — the class is vacuous. No substitute fabricated.
# RE-EXPRESSED, CORRECTING AN EARLIER "NOT MODELED" CALL
#   (bundled-wins-over-project-subdomain, last-wins-forward-fold). Both sibling
#   rivals attack the FIRST-WINS RESOLUTION over the assembled list, and it is
#   true that the resolution itself is not modeled here (mapping.md §"Callee
#   provenance": the order-precedence loop lives in the unchanged downstream
#   loader, not in the fragment this bundle pins). An earlier revision of this
#   manifest concluded from that they have NO counterpart here. That conclusion
#   was too strong, and the audit lane replaced it: what each sibling rival
#   attacks is a PROPERTY OF PRECEDENCE, and precedence on this carrier IS the
#   assembled order — so each has a faithful analogue stated over the order
#   instead of over the fold, and BOTH were landed with real builds:
#     * bundled-wins-over-project-subdomain — the sibling makes the bundled
#       source win on a decisive SUB-DOMAIN while staying correct elsewhere. The
#       analogue is a rival that mis-ORDERS on a proper sub-domain while
#       assembling correctly elsewhere: `subdomain-order-multi-dir`.
#     * last-wins-forward-fold — the sibling inverts the precedence direction.
#       With no fold here to run backwards, the analogue inverts the order the
#       loader resolves by: `reverse-whole-list`.
#   Neither is fabricated for an unmodeled behavior: both are refuted by the
#   SAME single equation this bundle pins, at a concrete input, with a
#   gold-side semantic refutation. Carrier narrowing is real, but it narrows
#   what a rival may be stated OVER, not which sibling rivals have analogues.
# DIVERGENCE lane: nagini carries no diverge-*/nonterm-*/weak-diverge case for
#   this instance, and on lean the class is vacuous anyway (`implementation_*` is
#   a total Lean `def`). Nothing to port.
#
# POINT SPREAD. The nine reject witnesses probe eight DISTINCT input tuples
# (`dup-bundled-both-ends` deliberately shares prepatch-order's point — see the
# note under the table):
#   (userDirs, bundledDir)     rival                          component
#     (["a"],       "b")       prepatch-order-bundled-ahead    O (order, everywhere)
#     ([],          "b")       drop-sentinel-head              S (head sentinel)
#     (["a"],       "z")       drop-bundled-tail               B (built-in tail)
#     (["a","c"],   "b")       reverse-user-dirs               M (middle-run order)
#     (["s"],       "t")       grounding-middle-run-contents   M's GROUNDING
#     (["m"],       "n")       grounding-bundled-tail-value    B's GROUNDING
#     (["p","q"],   "r")       subdomain-order-multi-dir       O (sub-domain only)
#     (["u"],       "v")       reverse-whole-list              S+B+O jointly
#     (["a"],       "b")       dup-bundled-both-ends           EXTENT (multiplicity)
#   `dup-bundled-both-ends` reuses prepatch-order's tuple ON PURPOSE, and that is
#   the honest choice rather than a missed point: the two rivals differ from gold
#   at the SAME input for DIFFERENT reasons (one permutes the runs, one duplicates
#   a run), so a fresh tuple would add a spelling, not a discriminating point,
#   while sharing the tuple makes it visible that the pinned equation rules out
#   both deviations at one input. It is also the tuple whose shape the F2P
#   configures, which is where an incomplete fix would actually be written.
#   Across them userDirs ranges over the empty list, four distinct singletons and
#   two distinct two-element lists; bundledDir takes six distinct values. See the
#   AUDIT NOTE under BINDER STRUCTURE for which of that variation is MEANINGFUL
#   (values that change the spec's verdict) rather than two spellings of one
#   point: for the delete/permute rivals the concrete strings are interchangeable,
#   and it is `grounding-bundled-tail-value` — refuted only OFF the sub-domain its
#   rival hardcodes — that makes the `bundledDir` binder genuinely load-bearing,
#   and `subdomain-order-multi-dir` that makes the LENGTH of `userDirs` genuinely
#   load-bearing rather than incidental.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# opaque callee and consumes no axiom (mapping.md: empty `axioms` region — the
# assembly is plain list construction, modeled directly), so there is nothing to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
