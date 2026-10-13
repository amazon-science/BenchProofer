"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-7985 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant sharing the FROZEN spec byte-for-byte: region surgery
touches only text inside ``-- impl-start`` / ``-- impl-end`` and — for a case
that legitimately re-proves — inside ``-- proof-start`` / ``-- proof-end``. So
``markers.same_spec`` holds by construction and the single
``theorem correct_checkLink`` STATEMENT stays byte-identical.
``expect:"verify"`` passes iff the variant is in scope AND the file elaborates
with the obligation closed (no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff the variant is
in scope AND does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini sibling
contracts THREE functions over a ``List[int]`` code-point carrier with fractional
read permissions (a prefix test, an explicit-scheme test, and the classifier that
consumes both). This Lean bundle models the SAME purely functional core as ONE
triple: ``problem_spec_checkLink`` / ``implementation_checkLink`` /
``correct_checkLink``, over a ``List Char`` carrier, with the two prefix tests and
the explicit-scheme test as ``pure``-region helpers rather than separately
contracted functions. So the nagini cases attached to those helpers' own
contracts have no separate obligation to attack here; they are re-expressed as
attacks on the ONE classifier obligation, at inputs that route through the helper
in question. Case-count parity is not the target — per-binder and per-arm
coverage of the modeled surface is.

DEFENDED SURFACE. ``problem_spec_checkLink uri localFileExists ignoreMatch
httpResult result`` is a total decision over five nested arms; the postcondition
pins ``result`` COMPLETELY on every arm (frame discipline — no arm is left free):

  * (S1 skip)    empty reference, or one carrying a leading in-page-anchor or
                 mail-address marker            -> ``.unchecked``;
  * (S2 scheme)  otherwise, a NON-web reference carrying an explicit scheme of
                 the shape "one-or-more lowercase letters immediately followed by
                 ``://``"                        -> ``.unchecked``;
  * (S3 present) otherwise, a non-web reference whose source-relative path is
                 present                         -> ``.working``;
  * (S4 skipped) otherwise, absent but matching a configured skip pattern
                                                 -> ``.ignored``;
  * (S5 absent)  otherwise, absent and matching none
                                                 -> ``.broken``;
  * (S6 web)     a web reference                 -> ``httpResult`` verbatim
                 (the resolution stage's outcome is frame-pinned through).

The postcondition is a single nested ``if``, not a conjunction, so there is one
top-level clause; the ADVERSARIALLY meaningful decomposition is the six arms
above, and the reject lane below attacks S1, S2, S3, S4, S5 and S6 individually
— plus, since an arm is only reached if the routing predicates send it there,
the two GUARDS that choose between arms (the skip-prefix test and the web-prefix
test) each carry a rival of their own.

STRUCTURAL NOTE (established by the audit lane with two real builds, both exit
0, against a proof-region-stripped copy of the frozen file). The postcondition is
FUNCTIONAL and TOTAL:

  * functional — ``∀ u l i h r1 r2, spec u l i h r1 → spec u l i h r2 → r1 = r2``
    closes by ``split_ifs at h1 h2 <;> simp_all``;
  * total — ``∀ u l i h, ∃ r, spec u l i h r`` closes with the frozen impl as
    the witness.

Together those say the spec admits EXACTLY ONE result per input, so a SPEC-TOO-WEAK
hole is impossible in principle here: any impl disagreeing with the frozen one at
any input is refutable at that input, and any impl agreeing everywhere is provable.
That is why the reject lane's job on this cell is COVERAGE of the arms and guards
rather than a hunt for an unpinned degree of freedom — there is none to find. It
also means each rival below is genuinely WRONG rather than merely reshaped: the
witnesses are the machine-checked demonstration, and reject cases are the only
place the distinction could hide.

Oracle-grounding note (carried from the sibling's "Oracle-grounding note"): the
helpers are SPELLED OUT over the input carrier — a prefix test per character and
a maximal-lowercase-run test — not opaque answer keys. So "echoing the helper" IS
performing the modeled decision and the UNGROUNDED-ORACLE-ECHO class does not
apply. The battery instead attacks the arms themselves: which arm fires on which
input, and what each arm answers.

BINDER STRUCTURE. Four input binders: ``uri`` (the reference), ``localFileExists``
and ``ignoreMatch`` (the two local boolean observations), ``httpResult`` (the
resolution stage's outcome, an input on the web arm). All four are load-bearing
and all four are VARIED across the reject witnesses — see the point-spread block
at the bottom. Nine reject witnesses probe nine DISTINCT input tuples
(``pts=9``), with ``localFileExists`` and ``ignoreMatch`` each taking both values
and ``httpResult`` taking five distinct statuses.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The sibling's mandatory case writes
    through a reference it holds only read permission on, and is rejected for
    INSUFFICIENT PERMISSION. Lean is referentially transparent: ``uri`` is an
    immutable value, there is no ``mut`` input binder, no aliasing, and no
    read-only cell to overwrite, so no analogous rival can be written. No
    substitute probe is fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. The sibling carries
    no ``diverge-*`` case, and none could be ported: ``implementation_checkLink``
    is a total Lean ``def`` (a branch cascade with no recursion and no loop), so a
    diverging implementation cannot be written at all. This is the genuinely
    vacuous disposition, NOT the ``partial``-semantics spec hole documented in
    ``the corpus-wide termination-semantics finding`` — that hole is a velvet phenomenon and does
    not arise here.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Every rival
    below is correct on most of the domain and diverges on exactly one arm.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
CONCRETE input and closing by ``decide``. The carrier is fully transparent (a
``List Char`` literal plus two ``Bool``s plus a ``LinkStatus``), so no witness
needs to condition on an opaque term and NO witness binds anything in its head —
there are therefore no hypotheses whose joint satisfiability could be in
question. Each witness was checked with two real ``lean_verify.sh`` builds: it
ELABORATES against its rival and FAILS on the frozen solution, so it
discriminates rather than asserting a tautology.

The gold-side failure is a SEMANTIC refutation in every case, not a syntactic
accident: the audit lane rebuilt all of these itself and read the logs, and each
gold build fails with ``Tactic `decide` proved that the proposition ... is
false`` — the kernel evaluating the claim and rejecting it. So none of the
``witness-undecided`` failure modes (a stuck ``decide``, a missing ``Decidable``
instance, a unification failure on an unreduced term) is in play on this carrier;
the exit codes carry real information. Confirmed by a FORGERY probe: dropping the
``¬`` from a witness — asserting the rival is CORRECT at its refutation point —
inverts both exit codes (rival 1, gold 0) instead of leaving them unchanged,
which is exactly what an informative carrier does and a stuck one does not.

AXIOM lane: EMPTY. ``meta.json`` records ``axioms: []`` and no ``opaque`` callee;
the explicit-scheme test is a deep model (A-reference) validated by G-AX, which
owns that lane. The sibling's two ``AXIOM_TESTS`` are DROPPED per the porting map.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7985"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. EVERY anchor below carries a `return` (or is the whole proof
# tactic body), so each lies STRICTLY inside `-- impl-start`/`-- impl-end` or
# `-- proof-start`/`-- proof-end` — the postcondition's own branch cascade uses
# `result = ...`, never `return`, so no anchor can reach the frozen spec. Each is
# asserted unique at import time by `_swap`.
# ---------------------------------------------------------------------------

# S1 — the skip-prefix arm.
_I_SKIP = ("  if uri.isEmpty || startsWithHashMailto uri then\n"
           "    return LinkStatus.unchecked")

# S2 — the explicit-scheme guard and its answer.
_I_SCHEME = "    if hasUriScheme uri then\n      return LinkStatus.unchecked"

# S4/S5 — the absent-path split (skip-pattern match vs. no match).
_I_ABSENT = """        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.broken"""

# S2..S5 — the whole non-web branch.
_I_NONWEB = """  if !startsWithHttp uri then
    if hasUriScheme uri then
      return LinkStatus.unchecked
    else
      if localFileExists then
        return LinkStatus.working
      else
        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.broken
"""

# S6 — the web arm's answer.
_I_WEB = "  return httpResult\n"

# The complete impl body, for the two positives that reshape the whole cascade.
_I_BODY = """  if uri.isEmpty || startsWithHashMailto uri then
    return LinkStatus.unchecked
  if !startsWithHttp uri then
    if hasUriScheme uri then
      return LinkStatus.unchecked
    else
      if localFileExists then
        return LinkStatus.working
      else
        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.broken
  return httpResult"""

# The frozen proof's tactic body (inside `-- proof-start`/`-- proof-end`), and
# its first line alone — so a positive may re-prove, and the admissibility case
# may prepend a ground `have`, without touching the theorem STATEMENT.
_P_BODY = """  intro uri localFileExists ignoreMatch httpResult
  unfold problem_spec_checkLink implementation_checkLink
  simp only [Id.run, bind, pure]
  split <;> rename_i h1
  · rfl
  · split <;> rename_i h2
    · split <;> rename_i h3
      · rfl
      · split <;> rename_i h4
        · rfl
        · split <;> rfl
    · rfl"""
_P_INTRO = "  intro uri localFileExists ignoreMatch httpResult"

# A re-proof that is robust to an arbitrary reshape of the branch cascade: peel
# every conditional on both sides, then discharge each leaf by congruence. Uses
# only core tactics — no new lemma, no assumption token. (Verified: real builds.)
_P_SPLIT = (_P_INTRO + """
  unfold problem_spec_checkLink implementation_checkLink
  simp only [Id.run, bind, pure]
  split_ifs <;> simp_all""")


# ---------------------------------------------------------------------------
# Witness scaffold. The carrier is fully transparent, so every witness states
# the spec predicate at literal inputs and closes by `decide`. Nothing is bound
# in the head, so there are no hypotheses to be jointly satisfiable.
# ---------------------------------------------------------------------------
def _w(uri, local_file_exists, ignore_match, http_result):
    a = f'"{uri}".toList {local_file_exists} {ignore_match} {http_result}'
    return (f"example : ¬ problem_spec_checkLink {a}\n"
            f"    (implementation_checkLink {a}) := by\n"
            "  unfold problem_spec_checkLink implementation_checkLink\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS POSITIVES — structurally different but CORRECT implementations
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_checkLink` STATEMENT byte-identical and re-proves inside
    # the proof region with core tactics only.
    # =====================================================================
    {
        "id": "pos-flat-cascade",
        "kind": "soundness",
        "expect": "verify",
        # Ports the sibling's flat-early-return positive. The nested cascade
        # becomes a flat sequence of early returns: the web arm is tested
        # POSITIVELY and taken first (instead of negatively and last), and the
        # absent-path split is INVERTED (the no-skip-pattern case is tested
        # first). Same decision on every input, different control flow.
        "module": _swaps(
            _BASE,
            (_I_BODY, """  if uri.isEmpty || startsWithHashMailto uri then
    return LinkStatus.unchecked
  if startsWithHttp uri then
    return httpResult
  if hasUriScheme uri then
    return LinkStatus.unchecked
  if localFileExists then
    return LinkStatus.working
  if !ignoreMatch then
    return LinkStatus.broken
  return LinkStatus.ignored"""),
            (_P_BODY, _P_SPLIT),
        ),
        "rationale": (
            "Same six-arm decision, reshaped: the web arm is hoisted to a "
            "positive early return and the absent-path split is inverted "
            "(no-skip-pattern first). Behaviourally identical on every input, so "
            "all six arms of the postcondition still hold and it MUST verify; if "
            "it could not, the spec would be pinning the frozen cascade's SHAPE "
            "rather than its behavior (SPEC-TOO-STRONG). Re-proved by peeling "
            "every conditional on both sides (`split_ifs`) and closing each leaf "
            "by congruence (`simp_all`) — core tactics only, statement "
            "byte-identical, no new axiom/lemma. Ports the sibling's "
            "pos-control-check-flat-branches."),
    },
    {
        "id": "pos-fold-absent-arm",
        "kind": "soundness",
        "expect": "verify",
        # Ports the sibling's "fold the guard chain into one expression"
        # positive. The explicit-scheme decision becomes a `match` on the boolean
        # instead of an `if`, and the two absent-path returns fold into a SINGLE
        # return of a selected outcome. Same values, different syntactic form.
        "module": _swaps(
            _BASE,
            (_I_BODY, """  if uri.isEmpty || startsWithHashMailto uri then
    return LinkStatus.unchecked
  if !startsWithHttp uri then
    match hasUriScheme uri with
    | true => return LinkStatus.unchecked
    | false =>
      if localFileExists then
        return LinkStatus.working
      else
        return (if ignoreMatch then LinkStatus.ignored else LinkStatus.broken)
  return httpResult"""),
            (_P_BODY, _P_SPLIT),
        ),
        "rationale": (
            "The explicit-scheme decision is written as a `match` on the boolean "
            "rather than an `if`, and the two absent-path early returns are "
            "folded into ONE return of a selected outcome. Identical answer on "
            "every input, so it MUST verify — else the spec would be over-fitted "
            "to the frozen branch syntax (SPEC-TOO-STRONG). Re-proved with the "
            "same core-tactic script; statement byte-identical, no new "
            "axiom/lemma. Ports the sibling's pos-control-scheme-tail-boolean, "
            "re-expressed against the one obligation this bundle carries (the "
            "sibling folds a separately-contracted helper's post-loop guard "
            "chain; this carrier has no such helper contract to reshape, so the "
            "equivalent fold is applied to the arm the helper feeds)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
    # F2P-shaped input. The frozen theorem carries NO precondition hypothesis
    # (the binder is a bare ∀ over a total domain), so the sibling's
    # "the precondition admits a real input" case has no precondition to admit;
    # the honest analogue is to discharge the postcondition by EVALUATION at the
    # F2P-shaped reference as a `have`, then close the frozen obligation
    # verbatim. Nothing is assumed: no new declaration, statement byte-identical.
    # =====================================================================
    {
        "id": "admiss-ground-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_checkLink "path/to/notfound".toList '
            'false false\n'
            '      LinkStatus.working (implementation_checkLink '
            '"path/to/notfound".toList\n'
            '        false false LinkStatus.working) := by\n'
            "    unfold problem_spec_checkLink implementation_checkLink\n"
            "    decide\n" + _P_INTRO),
        "rationale": (
            "The obligation is discharged by evaluation at the F2P-shaped input "
            "— a source-relative reference that is absent and matches no "
            "configured skip pattern — as a ground `have`, then the frozen "
            "obligation is closed verbatim. It verifies, so the modeled decision "
            "is satisfiable at exactly a normal F2P input rather than only "
            "vacuously; had it not, the spec would be unsatisfiable on the very "
            "sub-domain the F2P tests exercise (the analogue of "
            "PRECOND-TOO-STRONG, which is how the sibling's admissibility case "
            "reads on a carrier that HAS a precondition). Nothing is assumed: "
            "the ground instance is a `have` inside the existing tactic body, "
            "statement byte-identical, no new declaration. Ports the sibling's "
            "admiss-check-readable-target."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) a `refinement` arguing its faithful
    # real counterpart would NOT resolve an F2P test, and (b) a `witness` pinning
    # the violation at one concrete input, SEEN to discriminate.
    # =====================================================================

    # ---- S5: the unresolved outcome reported as working (the fix itself) ----
    {
        "id": "weak-absent-as-working",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ABSENT,
            """        if ignoreMatch then
          return LinkStatus.ignored
        else
          return LinkStatus.working"""),
        "refinement": (
            "This is the exact sub-domain the fix is FOR. A faithful patch that "
            "reported an absent, non-skip-matching source-relative reference as "
            "working would leave the deliberately-absent reference in the test "
            "corpus off the failure report entirely: the '[broken] "
            "path/to/notfound' line test_defaults asserts would be absent and "
            "the report's line count would stay at 5 instead of rising to 6. "
            "test_defaults would fail, so a verifying rival here is a true "
            "verify-does-not-imply-resolve break."),
        "rationale": (
            "REJECT from arm S5: with the reference non-web and non-scheme, the "
            "path absent (`localFileExists = false`) and no skip pattern matched "
            "(`ignoreMatch = false`), the postcondition pins `result = .broken`, "
            "but the rival answers `.working`. Refuted at the F2P-shaped "
            "reference with both observations false. If this VERIFIED the spec "
            "would be SPEC-TOO-WEAK on the fix's own sub-domain."),
        "witness": _w("path/to/notfound", "false", "false",
                      "LinkStatus.redirected"),
    },

    # ---- S4: the skip-pattern arm collapsed into the unresolved outcome ----
    {
        "id": "weak-skipmatch-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_ABSENT, "        return LinkStatus.broken"),
        "refinement": (
            "Drops the skip-pattern consultation for absent references, so every "
            "absent source-relative reference is reported unresolved even when "
            "the configuration lists it as one to skip. test_anchors_ignored "
            "configures exactly that reference into the skip-pattern set and "
            "asserts the report comes out EMPTY; an unresolved entry there is a "
            "non-empty report, so that F2P test would fail. The faithful patch "
            "therefore would not resolve."),
        "rationale": (
            "REJECT from arm S4: absent (`localFileExists = false`) AND matching "
            "a configured skip pattern (`ignoreMatch = true`) pins "
            "`result = .ignored`, but the rival answers `.broken`. Refuted at "
            "the same reference as weak-absent-as-working but with "
            "`ignoreMatch = true` — the distinguishing point, since the two "
            "rivals agree with each other and with gold everywhere else and this "
            "is the only input separating S4 from S5."),
        "witness": _w("path/to/notfound", "false", "true",
                      "LinkStatus.working"),
    },

    # ---- S2..S5: the whole non-web branch collapsed to one outcome ----
    {
        "id": "weak-collapse-nonweb",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NONWEB,
            "  if !startsWithHttp uri then\n"
            "    return LinkStatus.unchecked\n"),
        "refinement": (
            "Collapses the entire non-web branch to a single catch-all outcome, "
            "consulting neither the explicit-scheme shape nor either local "
            "observation — i.e. it declines to classify source-relative "
            "references at all, which is the behavior the issue reports as "
            "missing. Both the absent reference (which must be reported "
            "unresolved) and the present one (which must be reported working) "
            "fall into the catch-all, so test_defaults sees neither the "
            "'[broken] path/to/notfound' line nor the sixth report line. That "
            "F2P test would fail. This mirrors the pre-fix shape the bundle's "
            "own prepatch variant carries."),
        "rationale": (
            "REJECT from arms S3/S4/S5 jointly: for a non-web, non-scheme "
            "reference the postcondition pins `.working` / `.ignored` / `.broken` "
            "according to the two boolean observations, but the rival answers "
            "`.unchecked` regardless. Refuted at a PRESENT source-relative "
            "reference (`localFileExists = true`), which is the S3 arm — a "
            "sub-domain no other rival in this battery touches, and a distinct "
            "reference literal from the absent-path rivals."),
        "witness": _w("conf.py", "true", "false", "LinkStatus.unchecked"),
    },

    # ---- S2: the explicit-scheme test replaced by an over-broad one ----
    {
        "id": "weak-scheme-test-overbroad",
        "kind": "uniqueness",
        "expect": "reject",
        # The explicit-scheme shape test is replaced by a much laxer test that
        # fires on ANY reference containing a path separator.
        "module": _swap(
            _BASE, _I_SCHEME,
            "    if uri.contains '/' then\n"
            "      return LinkStatus.unchecked"),
        "refinement": (
            "Widens the explicit-scheme test from 'lowercase letters "
            "immediately followed by ://' to 'contains a path separator "
            "anywhere', so a perfectly ordinary multi-segment source-relative "
            "reference is treated as one the checker cannot inspect. The absent "
            "reference in the test corpus is exactly such a multi-segment path: "
            "a faithful patch with the over-broad test would skip it instead of "
            "reporting it unresolved, so '[broken] path/to/notfound' would not "
            "appear and test_defaults' line count would not reach 6. That F2P "
            "test would fail."),
        "rationale": (
            "REJECT from arm S2 (and hence S3): the postcondition routes a "
            "non-web reference to the skip answer ONLY when the explicit-scheme "
            "shape holds, and this reference has no lowercase-letters-then-`://` "
            "prefix, so the spec pins the local classification instead. Refuted "
            "at the multi-segment reference with the path PRESENT "
            "(`localFileExists = true`), where the spec demands `.working` and "
            "the rival answers `.unchecked` — a third distinct "
            "(observation, status) tuple."),
        "witness": _w("path/to/notfound", "true", "false",
                      "LinkStatus.ignored"),
    },

    # ---- S2: the explicit-scheme test inverted ----
    {
        "id": "weak-scheme-test-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_SCHEME,
            "    if !hasUriScheme uri then\n"
            "      return LinkStatus.unchecked"),
        "refinement": (
            "Inverts the explicit-scheme test, so the checker skips exactly the "
            "references it should inspect and inspects exactly the ones it "
            "cannot. Every plain source-relative reference in the test corpus "
            "lacks an explicit scheme and so is skipped: the absent one is never "
            "reported unresolved and the present one is never reported working, "
            "so test_defaults sees no '[broken] path/to/notfound' line and no "
            "sixth line. That F2P test would fail."),
        "rationale": (
            "REJECT from arm S2: the postcondition answers `.unchecked` on a "
            "non-web reference precisely WHEN the explicit-scheme shape holds; "
            "the rival answers it precisely when the shape does NOT hold. "
            "Refuted at a reference that DOES carry an explicit scheme, where "
            "the spec pins `.unchecked` and the rival falls through to the local "
            "classification. This is a NEAR-MISS relative to "
            "weak-scheme-test-overbroad — the two disagree with gold on "
            "complementary halves of the scheme test — so it is refuted at the "
            "opposite kind of reference (scheme-shaped, not plain path), the "
            "input that actually separates them. Ports the reasoning of the "
            "sibling's partial-domain-drop-scheme-branch and "
            "partial-domain-scheme-empty-run onto a point whose faithful patch "
            "genuinely fails an F2P test (see assessment)."),
        "witness": _w("gopher://h", "false", "false", "LinkStatus.working"),
    },

    # ---- S1: the skip-prefix guard widened past a leading marker ----
    {
        "id": "weak-skip-guard-overbroad",
        "kind": "uniqueness",
        "expect": "reject",
        # The in-page-anchor test is widened from a LEADING marker to the marker
        # occurring ANYWHERE in the reference.
        "module": _swap(
            _BASE, _I_SKIP,
            "  if uri.isEmpty || uri.contains '#' || "
            '"mailto:".toList.isPrefixOf uri then\n'
            "    return LinkStatus.unchecked"),
        "refinement": (
            "Widens the in-page-anchor test from a LEADING marker to the marker "
            "occurring anywhere, so a web reference carrying a fragment is "
            "skipped instead of being handed to the resolution stage. The test "
            "corpus contains several such fragment-bearing web references, and "
            "test_defaults asserts the resolution stage's findings about them "
            "appear in the report (the \"Anchor 'top' not found\" and \"Anchor "
            "'does-not-exist' not found\" lines). A faithful patch with the "
            "over-broad guard skips those references, so those lines are absent "
            "and the line count is wrong. test_defaults would fail."),
        "rationale": (
            "REJECT from arm S1 (and hence S6): the postcondition answers "
            "`.unchecked` only for an empty reference or one whose LEADING "
            "characters are the anchor/mail marker; a fragment-bearing web "
            "reference matches neither, so the spec routes it to the web arm and "
            "pins `result = httpResult`. The rival answers `.unchecked`. Refuted "
            "at a fragment-bearing web reference — the only witness in the "
            "battery whose reference both begins with the web prefix AND carries "
            "a fragment. Ports the reasoning of the sibling's frozen skip-prefix "
            "set, re-aimed at a point with real F2P consequences (see "
            "assessment)."),
        "witness": _w("https://www.google.com/#top", "false", "false",
                      "LinkStatus.broken"),
    },

    # ---- S6: the web arm answers a constant instead of the given outcome ----
    {
        "id": "weak-web-arm-unpinned",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_WEB, "  return LinkStatus.working\n"),
        "refinement": (
            "Discards the resolution stage's outcome on the web arm and answers "
            "a constant, so every web reference is reported working regardless "
            "of what the resolution stage found. test_defaults asserts the "
            "report CONTAINS the resolution stage's failure findings for several "
            "web references (a connection failure and two not-found responses) "
            "and that the report has exactly 6 lines; a faithful patch that "
            "reported them all working would emit none of those lines. "
            "test_defaults would fail."),
        "rationale": (
            "REJECT from arm S6: the postcondition FRAME-PINS the web arm to "
            "`result = httpResult`, so the resolution stage's outcome must be "
            "passed through verbatim; the rival substitutes a constant. This is "
            "the one rival attacking the frame-pinning clause — the guide's "
            "read-only-input analogue on a referentially transparent carrier. "
            "Refuted at a web reference whose given outcome differs from the "
            "constant, and `httpResult` is load-bearing at that point: "
            "re-pointing this witness's `httpResult` at the rival's own constant "
            "makes it FAIL against the rival (measured, exit 1), so it is the "
            "binder and not the reference that discriminates here. "
            "`weak-skip-guard-overbroad` routes through the same arm and is "
            "likewise `httpResult`-sensitive (measured), so this is not the only "
            "case exercising the binder — it is the one that isolates the "
            "pass-through itself, with the S1 guard left intact."),
        "witness": _w("http://a", "false", "false", "LinkStatus.redirected"),
    },

    # ---- S2..S5: the whole non-web branch answers the UNCLASSIFIED status ----
    # ADDED BY AUDIT. weak-collapse-nonweb already collapses the non-web branch,
    # but to `.unchecked` — so `.localLink`, the one status in the closed set no
    # case in the battery ever reaches, was unprobed. That status is exactly the
    # unclassified outcome the pre-fix shape reports, which makes this the arm
    # collapse whose faithful counterpart is the reported behavior itself.
    {
        "id": "weak-nonweb-as-unclassified",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_NONWEB,
            "  if !startsWithHttp uri then\n"
            "    return LinkStatus.localLink\n"),
        "refinement": (
            "Reports every non-web reference under a single unclassified "
            "outcome rather than deciding it, which is precisely the behavior "
            "the issue asks to replace: the reference is listed but never "
            "resolved against the source tree. test_defaults asserts the "
            "unresolved multi-segment reference appears under the unresolved "
            "heading and that the report grows to 6 lines; an unclassified "
            "outcome yields neither, so that F2P test would fail."),
        "rationale": (
            "REJECT from arms S3/S4/S5 jointly, at the status no other case in "
            "this battery reaches. The postcondition pins `.working` / "
            "`.ignored` / `.broken` per the two observations for a non-web "
            "non-scheme reference; the rival answers `.localLink` regardless. "
            "Refuted at the absent multi-segment reference with the "
            "skip-pattern set consulted and matching (`ignoreMatch = true`) — a "
            "tuple no other witness uses, and the S4 arm reached with a "
            "reference literal distinct from the S4 rival's."),
        "witness": _w("path/to/notfound", "false", "true",
                      "LinkStatus.redirected"),
    },

    # ---- S6: the web-routing predicate itself narrowed ----
    # ADDED BY AUDIT. Every shipped rival keeps `startsWithHttp` intact and
    # attacks what happens INSIDE an arm; the predicate that CHOOSES between the
    # local cascade and the web arm was the one guard with no rival of its own.
    {
        "id": "weak-web-prefix-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, "  if !startsWithHttp uri then",
            '  if !("http:".toList.isPrefixOf uri) then'),
        "refinement": (
            "Narrows the web-resource test to the unsecured prefix alone, so "
            "every secured web reference is diverted into the local cascade and "
            "resolved as a source-relative path instead of being handed to the "
            "resolution stage. Most references in the test corpus are secured "
            "ones, and test_defaults asserts the resolution stage's findings "
            "about them appear in the report; diverted, they are absent from it "
            "and the line count is wrong. test_defaults would fail."),
        "rationale": (
            "REJECT from arm S6: the postcondition routes to the web arm — and "
            "frame-pins `result = httpResult` — for EITHER web prefix, so a "
            "secured reference must pass the resolution stage's outcome "
            "through; the rival instead falls into the local cascade and "
            "answers from the two observations. Refuted at a secured web "
            "reference carrying no fragment, which separates this rival from "
            "weak-skip-guard-overbroad (that one reaches S6 via a "
            "fragment-bearing reference and leaves the routing predicate "
            "intact). An eighth distinct input tuple."),
        "witness": _w("https://www.google.com/image.png", "false", "false",
                      "LinkStatus.ignored"),
    },
]

# ---------------------------------------------------------------------------
# Sibling -> lean accounting. The nagini battery has 9 SPEC cases (1 frame
# mutation, 5 partial-domain rivals, 2 soundness positives, 1 admissibility)
# plus 2 AXIOM_TESTS, spread over THREE contracted functions. This bundle carries
# ONE obligation over the same purely functional core, so the sibling's
# helper-contract cases have no separate obligation to attack and are
# re-expressed as attacks on the classifier at inputs routing through the helper.
#
#   sibling case                          -> here
#   -----------------------------------------------------------------------
#   frame-mutation-check-target           -> (none)                     VACUOUS
#   partial-domain-ignored-as-missing     -> weak-skipmatch-as-absent   PORTED
#   partial-domain-missing-as-working     -> weak-absent-as-working     PORTED
#   partial-domain-drop-scheme-branch     -> weak-scheme-test-inverted  RE-AIMED
#   collapse-nonweb-to-constant           -> weak-collapse-nonweb       PORTED
#   partial-domain-scheme-empty-run       -> weak-scheme-test-overbroad RE-AIMED
#   pos-control-check-flat-branches       -> pos-flat-cascade           PORTED
#   pos-control-scheme-tail-boolean       -> pos-fold-absent-arm        RE-EXPRESSED
#   admiss-check-readable-target          -> admiss-ground-f2p-point    RE-EXPRESSED
#   (none)                                -> weak-skip-guard-overbroad  ADDED (S1)
#   (none)                                -> weak-web-arm-unpinned      ADDED (S6)
#   (none)                       -> weak-nonweb-as-unclassified  ADDED BY AUDIT
#   (none)                       -> weak-web-prefix-narrowed     ADDED BY AUDIT
#   AXIOM_TESTS (2)                       -> (none)                    DROPPED
#
# VACUOUS (frame-mutation-check-target): the sibling's MANDATORY case writes
#   through a reference held at partial read permission and is rejected for
#   insufficient permission. Lean is referentially transparent — `uri` is an
#   immutable value, there is no `mut` binder, no aliasing, no read-only cell —
#   so no analogous rival exists. Per the porting map, no substitute is
#   fabricated.
#
# RE-AIMED (the two scheme rivals). The sibling's literal rivals — drop the
#   explicit-scheme arm outright, and accept an EMPTY leading letter run — were
#   BUILT AND MEASURED here first: both reject, and both carry witnesses that
#   discriminate (at a scheme-shaped reference and at '://x' respectively; two
#   builds each, seen). They are NOT shipped in that literal form because their
#   `refinement` obligation cannot be met honestly: the F2P/P2P corpus contains
#   NO reference carrying a non-web explicit scheme and none whose leading run is
#   empty, so a faithful patch making either error still resolves both F2P tests.
#   Shipping them would claim a verify-does-not-imply-resolve break that does not
#   exist. Instead the SAME clause (S2, the explicit-scheme test) is attacked by
#   two rivals whose errors DO bite on corpus inputs — an over-broad test that
#   swallows a plain multi-segment path, and an inverted test that swallows every
#   plain path — so the clause is genuinely defended and every shipped refinement
#   is true. Same disposition for a rival narrowing the skip-prefix set (dropping
#   the mail-address prefix): built, rejects, witness discriminates, but no
#   mail-address reference exists in the corpus, so it is replaced by
#   weak-skip-guard-overbroad, which errs in the direction the corpus DOES
#   exercise.
#
# RE-EXPRESSED (pos-fold-absent-arm): the sibling's second positive folds a
#   separately-contracted helper's post-loop guard chain into one boolean. That
#   helper is a `pure`-region `def` here with no contract of its own, so there is
#   no guard chain to reshape; the equivalent "fold a guard chain into one
#   selected value" reshape is applied to the arm the helper feeds (the two
#   absent-path returns become one), plus a `match`-for-`if` rewrite of the
#   helper's own consumption site.
# RE-EXPRESSED (admiss-ground-f2p-point): the sibling admits its PRECONDITION
#   (partial read permission suffices to read the input). The frozen obligation
#   here has no precondition hypothesis at all — the binder is a bare ∀ over a
#   total domain — so there is nothing to admit. The honest analogue is to show
#   the postcondition is satisfiable by EVALUATION at a normal F2P-shaped input,
#   which is what the case does.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS. `meta.json` records `axioms: []` and no `opaque` callee; the
#   explicit-scheme test is an A-reference deep model already validated by a
#   passing G-AX.
# NO soundness positive was dropped for proof difficulty. Both shipped positives
#   close with core tactics (`split_ifs <;> simp_all`) under the frozen theorem
#   statement, confirmed by real builds.
#
# ---------------------------------------------------------------------------
# AUDIT LANE (independent re-derivation; every exit code below was observed).
#
# The port's claims were re-measured rather than read. What held:
#
#   * STATEMENT INTEGRITY. The `theorem correct_checkLink` statement is
#     byte-identical to the frozen file in all 10 shipped cases (sha-compared),
#     and each case's text OUTSIDE the impl/proof regions is byte-identical too —
#     so no case reshapes a hypothesis under cover of `same_spec`.
#   * WITNESS DISCRIMINATION, re-derived. All 7 original reject witnesses were
#     rebuilt from scratch, twice each: rival exit 0, gold exit 1, 14/14 as
#     declared. Every gold-side log was READ, and each is `decide` proving the
#     proposition false — a semantic refutation, not a missing identifier, type
#     error, stuck reduction or timeout.
#   * POSITIVES ARE NOT DEFEQ-TRIVIAL. Restoring the FROZEN tactic script onto
#     each positive's reshaped impl fails (exit 1 for both), so each reshape is a
#     real change of form that had to be genuinely re-proved, not a term the
#     frozen script still closes.
#   * ADMISSIBILITY IS LOAD-BEARING. Re-pointing the ground `have` at a status
#     the spec does NOT pin at that input fails (exit 1) while the status it DOES
#     pin succeeds (exit 0), so the case evaluates a real obligation.
#
# What the audit changed:
#
#   * `weak-web-arm-unpinned`'s rationale claimed to be "the only" case whose
#     witness exercises `httpResult` as load-bearing. FALSE, and measured so:
#     re-pointing `weak-skip-guard-overbroad`'s witness `httpResult` at that
#     rival's answer makes its witness fail (exit 1), i.e. that case is
#     `httpResult`-sensitive too. The claim is corrected in place rather than
#     deleted, since the underlying point (this is the case ISOLATING the
#     pass-through) is true.
#   * Two rivals ADDED for genuinely unattacked surface, both with witnesses
#     rebuilt by the audit (rival 0 / gold 1 each):
#       - `weak-nonweb-as-unclassified` — `.localLink` was the one status in the
#         closed set no case reached;
#       - `weak-web-prefix-narrowed` — every shipped rival left `startsWithHttp`
#         intact, so the predicate CHOOSING between the local cascade and the web
#         arm had no rival of its own.
#
# SPEC-TOO-WEAK probe (attack D): 8 NEW wrong impls, none verified (all exit 1) —
#   the web prefix losing its secured disjunct; the present-path arm answering
#   unresolved; the empty-reference disjunct dropped; the skip-marker set narrowed
#   to the anchor alone; the scheme run made non-maximal (accepting an empty
#   leading run, at '://x'); the S1/S6 guards' precedence swapped; and the two
#   `.localLink` collapses now shipped. No spec hole. The sibling's literal
#   "drop the explicit-scheme arm" rival was also rebuilt (exit 1, witness
#   discriminates at 'gopher://h'), independently confirming the port's RE-AIMED
#   disposition above was a refinement-honesty call and not a proof-difficulty one.
# SPEC-TOO-STRONG probe (attack E): 3 NEW correct reshapes, ALL verified (exit 0)
#   — a fully de-monadified nested-`if` expression with no `Id.run` at all; a
#   6-way `match` on a 5-tuple of the guard booleans; and the S1/S6 precedence
#   swap, which is correct because the two guards are disjoint and needed that
#   disjointness proved inline as a ground `have` (no new top-level declaration).
#   So the spec pins behavior, not shape, on all three.
#
# POINT SPREAD. The nine reject witnesses probe nine DISTINCT input tuples
# (pts=9); no input binder is held fixed:
#   (uri, localFileExists, ignoreMatch, httpResult)      case               arm
#   ("path/to/notfound",         false, false, redirected) weak-absent-as-working    S5
#   ("path/to/notfound",         false, true,  working)    weak-skipmatch-as-absent  S4
#   ("path/to/notfound",         true,  false, ignored)    weak-scheme-overbroad     S2/S3
#   ("path/to/notfound",         false, true,  redirected) weak-nonweb-as-unclassified S4
#   ("conf.py",                  true,  false, unchecked)  weak-collapse-nonweb      S3
#   ("gopher://h",               false, false, working)    weak-scheme-inverted      S2
#   ("https://www.google.com/#top", false, false, broken)  weak-skip-guard-overbroad S1/S6
#   ("https://www.google.com/image.png", false, false, ignored) weak-web-prefix-narrowed S6
#   ("http://a",                 false, false, redirected) weak-web-arm-unpinned     S6
#   uri takes 6 distinct values spanning all six arms' routing conditions;
#   localFileExists ∈ {false, true}; ignoreMatch ∈ {false, true}; httpResult takes
#   5 distinct statuses (redirected, working, ignored, unchecked, broken). The
#   three near-miss pairs are separated deliberately: the S4/S5 pair differs only
#   in `ignoreMatch` (the sole input distinguishing them), and the two scheme
#   rivals — which err on complementary halves of the same test — are refuted at
#   opposite kinds of reference (plain path vs. scheme-shaped).
AXIOM_TESTS = []
