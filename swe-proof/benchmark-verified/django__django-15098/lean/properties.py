"""properties.py — G-PBT falsification battery for django__django-15098 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function; ONE input binder ``path : List Char``):

  langCodeFromPath (path : List Char) : Option (List Char)
    result = (if allAscii path then
                match langPrefix path with
                | none    => none
                | some lc => resolveVariant lc
              else nonAsciiOutcome path)

  A URL path may carry a language tag as its leading component. For an all-ASCII
  path the admissible candidate is the maximal well-formed prefix — a primary
  subtag plus UP TO TWO further subtags (script and region), each a separator
  followed by a non-empty word run, terminated by ``/`` or end of path — and the
  result is the supported variant that candidate resolves to (``none`` when no
  candidate prefixes the path, or when the candidate resolves to no supported
  variant). For a path carrying a non-ASCII code point the result is a fixed
  deterministic outcome exposed by signature only.

  The carrier is largely OPAQUE. Two callees are ``opaque`` with NO asserted
  property: ``resolveVariant`` (the candidate→variant map) and
  ``nonAsciiOutcome`` (the whole-routine outcome off the ASCII plane). The DEEP
  structural parse (``langPrefix = langPrefixN 2``, ``grabSubtags``, the
  terminator match, ``allAscii``) lives ENTIRELY in the frozen spec/pure region;
  a variant may edit only the impl body, which controls three sub-decisions:

    * WHICH BRANCH fires — the ``allAscii`` split.
    * HOW MANY trailing subtags the candidate admits — which ``langPrefixN``
      budget the impl consumes. This is the ENTIRE behavioural delta of the
      change: the admissible-subtag budget went from ONE to TWO, i.e. from
      ``language[-one]`` to ``language[-script][-region]``.
    * HOW the recognised candidate is turned into a result — whether the opaque
      ``resolveVariant`` is applied, or the raw candidate is echoed instead.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and this was DEMONSTRATED rather than
    asserted. The nagini sibling makes an input-write attack MANDATORY because
    ``path`` is held at fractional (read-only) permission and a rival that writes
    it is rejected for insufficient permission. Lean is referentially
    transparent: ``path`` is a plain immutable ``List Char``, there is no
    half-permission to violate and no aliasing to exploit. Measured: the only
    way to express "this impl writes its input" is to change the RETURN TYPE to a
    state monad (``StateM (List Char) (Option (List Char))`` with ``set path``),
    and that variant does not fail on the spec — it fails to ELABORATE, at the
    theorem statement, with an application type mismatch on
    ``implementation_langCodeFromPath path``, because the frozen obligation no
    longer typechecks against it. That is a signature change, i.e. a different
    defended surface, not a rival for THIS spec. The nearest in-type analogue
    (rebinding ``let path := path`` before the body) is pure shadowing and
    verifies, correctly: it observes nothing. So the class has no expressible
    instance here and no substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE (not a vacuous class). This bundle
    sets NO ``loom.semantics.termination`` option: that option is a velvet-side
    setting and no lean ``Solution.lean`` in the corpus carries one, so there is
    no termination obligation for the verifier to discharge on this carrier. A
    rival that diverges is therefore not refutable BY the spec: the frozen
    obligation is a plain functional equation ``result = …``, and a
    non-terminating impl neither satisfies nor is refuted by it at any concrete
    input, so no witness can separate it. Measured for the record: a rival whose
    ``langPrefix = none`` branch calls a ``partial def spin (n) := spin (n+1)``
    is in variant scope and DOES fail to build — but it fails with ``Tactic
    'rfl' failed`` on the unreduced ``spin 0`` term, which is exactly the
    tactic-mismatch signature a merely reshaped CORRECT rival produces, so its
    rejection would attribute nothing to the spec. Recorded as a HOLE in the
    spec's reach, deliberately NOT shipped as a reject case, because shipping it
    would manufacture a passing case out of a tactic gap.

  * PRECONDITION ADMISSIBILITY — APPLIES, as the total-carrier analogue. It is
    TRUE that the frozen ``theorem correct_langCodeFromPath`` carries no
    precondition hypothesis (the behavior is total: ``∀ path, …``), but that is
    NOT a reason to drop the lane: "no precondition binder" removes the nagini
    SHAPE of the test, not the thing it detects. What PRECOND-TOO-STRONG means on
    a total carrier is that the obligation is UNSATISFIABLE at exactly an
    F2P-shaped input — the spec's own RHS failing to reduce to any value there,
    so no impl could match it. That is a live risk here precisely because the
    RHS is stated over an ``opaque`` resolver behind a deep structural parse: if
    the parse did not reduce at a real request path, the obligation would be
    unusable at the input the change is about, and the ``∀``-quantified positive
    could still close by a generic case split without ever touching it. The
    ``admiss-f2p-ground`` case below tests it directly: it discharges the
    obligation at the concrete F2P-shaped path ``/de-ch-1901/`` BY EVALUATION as
    a ``have`` (the parse must actually reduce to the two-subtag candidate) and
    only then closes the frozen obligation verbatim.

  * UNGROUNDED-ORACLE ECHO — APPLIES here, unlike nagini. On nagini's carrier the
    parse was a fully-pure function so there was no opaque answer-key to echo. On
    THIS carrier the candidate→variant map is the ``opaque resolveVariant``; an
    impl that returns the recognised candidate ITSELF instead of applying the
    resolver echoes the wrong value. The spec pins the result to
    ``resolveVariant lc`` of the SAME candidate, so echoing is refuted (case
    ``weak-echo-candidate``). This is the honest carrier-specific analogue, not an
    invented case.

  * PARTIAL-DOMAIN / BUDGET (the pre-patch guard and its upper edge) — APPLIES,
    and is the load-bearing pair. Under-budget (``budget 1`` = the pre-patch
    single-subtag matcher) rejects a script+region candidate that must resolve;
    over-budget (``budget 3``) accepts a candidate with a third trailing subtag
    that must NOT resolve. Both are refuted at their exact F2P inputs.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen script is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
carries a Lean snippet stating the spec predicate at one CONCRETE ``path``. The
spec RHS is stated over the ``opaque resolveVariant``, which no literal input
computes, so each witness CONDITIONS on the carrier: it assumes only what it
needs to SEPARATE rival from spec — a single hypothesis of the form
``resolveVariant <candidate> ≠ <value>`` — and closes. Each was checked to HOLD
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology), and each single hypothesis is jointly satisfiable (one
assumption per witness about one opaque term).

A stronger requirement than "fails on gold" is enforced on every witness here,
because "fails on gold" is satisfiable by an error that has nothing to do with
the claim. Each witness reduces the impl through the GOAL — via ``norm_num``/
``simp only`` over identities of the FROZEN pure functions (``allAscii``,
``langPrefix``, ``List.takeWhile``/``grabSubtags``), which hold on BOTH sides —
and never via a rewrite naming the rival's own return value. The test that this
is real: FLIP the witness's claim (drop the ``¬``) and rebuild on gold. Because
the impl is reduced through the goal, gold's residual goal differs between the
two (``¬pure none = none`` vs ``pure none = none``; or ``False`` vs a concrete
equation), so gold's exit code carries information about WHAT IS CLAIMED. A
witness whose gold-side error is a rewrite/``rfl`` failure that appears
identically under the flipped claim would be hollow — the gate would record
``rejected`` even for a witness asserting gold is CORRECT at that input — and is
not admissible here.

BINDER COVERAGE. The sole spec input binder is ``path``. The reject witnesses
vary it across five distinct inputs — ``/de-ch-1901/`` (under-budget),
``/de-simple-page-test/`` (over-budget), ``/en-gb/`` (echo), ``/aaa.bbb/``
(drop-terminator), ``//`` (empty run) — exercising the parse at both budget
edges, the resolver application, the terminator anchor, and the
non-empty-primary-subtag boundary. The load-bearing clauses of the ASCII-branch
candidate are attacked: the subtag budget (both edges), the resolver
application, the `(/|$)` terminator, and the non-empty primary subtag.

  NOT isolated by any shipped rival, and recorded rather than claimed: (a) the
  ``['\n']`` trailing-line-terminator alternative of the end-of-input anchor, and
  (b) the ``isSep`` alphabet (``'-'`` vs ``'@'``). Both were probed with real
  builds — an inlined-parse rival that drops the ``['\n']`` alternative, and one
  whose separator test accepts only ``'-'`` — and both are correctly REJECTED,
  so neither is a spec hole. They are not shipped as cases because each rejection
  arrives as ``Tactic `rfl` failed`` on the inlined parse, the same signature a
  reshaped CORRECT rival gives, and pinning a discriminating witness for them
  requires conditioning on a resolver value at an input the F2P set never
  reaches. Their sub-domains are unreachable from the graded observable (no F2P
  path carries a trailing newline or an ``'@'``), so the residual risk is
  cosmetic rather than behavioural — but it is a GAP, not coverage.

The non-ASCII branch (``nonAsciiOutcome``) is
deliberately NOT attacked — it is pinned to an opaque outcome exposed by
signature only, no F2P input is non-ASCII, and a rival mishandling it would
still resolve every F2P test, so it is not a verify-does-not-resolve break.

OMITTED nagini cases (see 'assessment'): FRAME-MUTATION (vacuous — no fractional
permission and no aliasing on a referentially transparent carrier). ADMISS-READS
is NOT omitted: it is carried as ``admiss-f2p-ground``, the total-carrier
analogue described above. WEAK-DROP-TERMINATION and
WEAK-ALLOW-EMPTY-RUN ARE expressible here after all: an impl variant may INLINE
the prefix parse (the edit still lands entirely inside the impl region) and then
omit the terminator check or the non-empty-primary-subtag guard, so the frozen
spec's `langPrefix` still demands both and the rival diverges. Both are now
carried below (``weak-drop-terminator``, ``weak-allow-empty-run``), each with a
witness that HOLDS of the rival and FAILS on the frozen solution.

AXIOM lane: EMPTY. meta.json axioms == []; the two opaque symbols are
deep-model / A-reference callees with no consumed ``_prop`` axiom (they appear
identically on both sides of the spec equation). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-15098"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit. (The spec's
# `match langPrefix path with` block is NOT a safe anchor: an indentation-only
# variant of it also appears in the post-conditions region.)
_IMPL_GOLD = (
    "def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=\n"
    "  Id.run do\n"
    "    if allAscii path then\n"
    "      match langPrefix path with\n"
    "      | none => return none\n"
    "      | some lc => return resolveVariant lc\n"
    "    else\n"
    "      return nonAsciiOutcome path\n"
)

_PROOF_BODY = (
    "  intro path\n"
    "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
    "  by_cases h : allAscii path <;> simp [h, Id.run] <;>\n"
    "    cases langPrefix path <;> rfl\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival / positive impl bodies (each is a full impl region; only the impl
# changes, so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl.
#
# The obvious reshape here — drop the `Id.run do` and spell the branch/`match`
# directly — is NOT usable as a positive, and the reason is worth recording
# because it looks like a real test and is not one. `Id.run do` over the `Id`
# monad is DEFINITIONALLY EQUAL to the direct expression: that variant closes
# under the FROZEN tactic body unchanged, and the frozen impl itself closes by a
# bare `rfl`. A positive whose "different shape" is defeq to the frozen impl
# exercises no tolerance in the spec at all — it passes honestly while testing
# nothing, so it cannot discharge the SPEC-TOO-STRONG direction.
#
# So the positive is the `Option.bind` reshape instead: the branch's `match` is
# replaced by `(langPrefix path).bind resolveVariant`, which is the same function
# on every input but is NOT definitionally equal to the frozen `match` term
# (`rfl` alone fails on it — the `bind` has to be unfolded through the `Option`
# instance per constructor). The obligation is therefore genuinely RE-PROVED for
# the new shape: `simp [h]` splits the branch and `cases langPrefix path <;> rfl`
# discharges each constructor. Statement byte-identical; no new lemma, axiom, or
# assumption token.
_POS_IMPL = (
    "def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=\n"
    "  if allAscii path then (langPrefix path).bind resolveVariant\n"
    "  else nonAsciiOutcome path\n"
)
_POS_PROOF = (
    "  intro path\n"
    "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
    "  by_cases h : allAscii path <;> simp [h] <;>\n"
    "    cases langPrefix path <;> rfl\n"
)

# ADMISSIBILITY (total-carrier analogue of nagini's `admiss-reads`): keep the
# gold impl and the frozen tactic tail VERBATIM, but first discharge the
# obligation at one concrete F2P-shaped input as a `have`, BY EVALUATION. The
# `decide`s force the deep structural parse to actually reduce at that path
# (`langPrefix "/de-ch-1901/" = some "de-ch-1901"` — the two-subtag candidate the
# widened budget admits), so the case fails if the obligation is unsatisfiable
# there. Only the proof region changes; the impl and the theorem statement are
# untouched, and no new declaration/axiom/assumption token is introduced.
_ADMISS_PROOF = (
    "  intro path\n"
    "  have hasc : allAscii \"/de-ch-1901/\".data = true := by decide\n"
    "  have hcand : langPrefix \"/de-ch-1901/\".data = some \"de-ch-1901\".data := by decide\n"
    "  have hF2P : problem_spec_langCodeFromPath \"/de-ch-1901/\".data\n"
    "      (implementation_langCodeFromPath \"/de-ch-1901/\".data) := by\n"
    "    unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
    "    rw [hasc, hcand]\n"
    "    rfl\n"
    "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
    "  by_cases h : allAscii path <;> simp [h, Id.run] <;>\n"
    "    cases langPrefix path <;> rfl\n"
)

# UNDER-BUDGET (= the pre-patch matcher): admit only ONE trailing subtag
# (`langPrefixN 1`) instead of up to two. Rejects a script+region candidate.
_BUDGET1 = _IMPL_GOLD.replace(
    "match langPrefix path with", "match langPrefixN 1 path with")

# OVER-BUDGET: admit up to THREE trailing subtags (`langPrefixN 3`), accepting a
# candidate with one subtag too many.
_BUDGET3 = _IMPL_GOLD.replace(
    "match langPrefix path with", "match langPrefixN 3 path with")

# ECHO: return the recognised candidate itself instead of the variant it
# resolves to (skip the opaque `resolveVariant`).
_ECHO = _IMPL_GOLD.replace(
    "| some lc => return resolveVariant lc", "| some lc => return some lc")

# DROP-TERMINATOR: the impl INLINES the prefix parse (so the edit stays entirely
# inside the impl region) but omits the terminator requirement — it accepts the
# primary/trailing-subtag run regardless of what follows, instead of demanding a
# `/` or end-of-path. On a run followed by other punctuation (e.g. `/aaa.bbb/`,
# run `aaa` stops at `.`) it recognises a candidate the spec rejects. This
# attacks the terminator clause, which no budget/echo rival touches.
_DROPTERM = (
    "def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=\n"
    "  if allAscii path then\n"
    "    match path with\n"
    "    | '/' :: rest =>\n"
    "      match rest.span isWord with\n"
    "      | (seg0, r0) =>\n"
    "        if seg0 = [] then none\n"
    "        else match grabSubtags 2 r0 with\n"
    "          | (subs, _) => resolveVariant (seg0 ++ subs)\n"
    "    | _ => none\n"
    "  else nonAsciiOutcome path\n"
)

# ALLOW-EMPTY-RUN: the impl inlines the prefix parse (keeping the terminator
# match) but DROPS the non-empty-primary-subtag guard, so a path with no leading
# word run (e.g. `//`) is accepted with an EMPTY candidate instead of yielding no
# candidate. Attacks the non-empty-primary-subtag clause, again untouched by the
# budget/echo rivals.
_EMPTYRUN = (
    "def implementation_langCodeFromPath (path : List Char) : Option (List Char) :=\n"
    "  if allAscii path then\n"
    "    match path with\n"
    "    | '/' :: rest =>\n"
    "      match rest.span isWord with\n"
    "      | (seg0, r0) =>\n"
    "        match grabSubtags 2 r0 with\n"
    "        | (subs, rrest) =>\n"
    "          match rrest with\n"
    "          | [] => resolveVariant (seg0 ++ subs)\n"
    "          | '/' :: _ => resolveVariant (seg0 ++ subs)\n"
    "          | ['\\n'] => resolveVariant (seg0 ++ subs)\n"
    "          | _ => none\n"
    "    | _ => none\n"
    "  else nonAsciiOutcome path\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The `theorem correct_*` STATEMENT
    # is byte-identical; the tactic body is re-proved for the new shape. No
    # helper lemma, axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that expresses the ASCII branch as "
            "`(langPrefix path).bind resolveVariant` instead of the spec's own "
            "`match` must still satisfy `result = (if allAscii path then match "
            "langPrefix path …)`; if it cannot, the spec is SPEC-TOO-STRONG. The "
            "reshape is NOT definitionally equal to the frozen impl — a bare "
            "`rfl` fails on it, because the `Option.bind` has to be unfolded "
            "through the monad instance per constructor — so the obligation is "
            "genuinely RE-PROVED for the new shape rather than inherited: "
            "`simp [h]` splits the `allAscii` branch and `cases langPrefix path "
            "<;> rfl` discharges `none`/`some` separately. This matters for what "
            "the case attests: the DEFEQ reshape (dropping `Id.run do`, which is "
            "defeq over the `Id` monad) closes under the frozen tactic body "
            "unchanged, so it would pass while exercising no tolerance in the "
            "spec whatsoever. No new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY (total-carrier analogue) — the obligation must be
    # SATISFIABLE at a concrete F2P-shaped input, not merely closable by a
    # generic case split. If this fails => PRECOND-TOO-STRONG in the only sense
    # a total carrier has: the spec is unusable at exactly the input the change
    # is about.
    # =====================================================================
    {
        "id": "admiss-f2p-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the frozen obligation is `∀ path, …` with no precondition binder, so "
            "the nagini shape of admissibility (does the precondition admit the "
            "reads a real request needs?) has no direct analogue. The thing that "
            "lane DETECTS still does: on a total carrier PRECOND-TOO-STRONG means "
            "the obligation is unsatisfiable at exactly an F2P-shaped input. This "
            "case discharges it at the concrete path `/de-ch-1901/` by EVALUATION "
            "before closing the frozen obligation verbatim: `allAscii … = true` and "
            "`langPrefix … = some \"de-ch-1901\"` are both proved `by decide`, so "
            "the deep structural parse must genuinely reduce to the two-subtag "
            "candidate at that path and `problem_spec` must be inhabited there. If "
            "this fails => the spec is not usable at the input the change is about, "
            "even though the ∀-positive would still close. Only the proof region "
            "changes; impl and statement are byte-identical and no new declaration, "
            "axiom, or assumption token is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation
    # witness pinning the violation at one concrete input, conditioned on the
    # opaque carrier only as strongly as the separation needs.
    # =====================================================================
    {
        "id": "weak-under-budget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BUDGET1),
        "refinement": (
            "this is exactly the pre-change behaviour: the candidate admits only "
            "ONE trailing subtag, so a script+region candidate is not recognised. "
            "Its faithful real patch is the unchanged single-subtag matcher, "
            "under which a path like `/de-ch-1901/` yields NO candidate and the "
            "routine returns nothing instead of the supported variant "
            "`de-ch-1901`. That is precisely the graded observable the change "
            "adds (a language-script-region tag must resolve), so the rival does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the ASCII-branch `match langPrefix path` clause: on "
            "`/de-ch-1901/` the spec's two-subtag candidate is `de-ch-1901`, so "
            "the result must be `resolveVariant \"de-ch-1901\"`, but the "
            "one-subtag rival finds no candidate and returns `none`. Refuted at "
            "the LOWER edge of the subtag budget. If it verifies => SPEC-TOO-WEAK "
            "(the widened budget would not be enforced)."
        ),
        "witness": (
            "-- Under-budget rival returns `none` on a script+region path whose\n"
            "-- two-subtag candidate the spec resolves; conditioned only on that\n"
            "-- candidate resolving to SOMETHING (one hypothesis about the opaque\n"
            "-- resolver), which separates `none` from the spec's `resolveVariant`.\n"
            "example (h : resolveVariant \"de-ch-1901\".data ≠ none) :\n"
            "    ¬ problem_spec_langCodeFromPath \"/de-ch-1901/\".data\n"
            "      (implementation_langCodeFromPath \"/de-ch-1901/\".data) := by\n"
            "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
            "  simp only [Id.run, pure]\n"
            "  norm_num [show allAscii \"/de-ch-1901/\".data = true from by decide,\n"
            "            show langPrefix \"/de-ch-1901/\".data = some \"de-ch-1901\".data from by decide,\n"
            "            show langPrefixN 1 \"/de-ch-1901/\".data = none from by decide]\n"
            "  exact fun heq => h heq.symm\n"
        ),
    },
    {
        "id": "weak-over-budget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BUDGET3),
        "refinement": (
            "admitting up to THREE trailing subtags over-accepts: a real patch "
            "with the looser bound would recognise a candidate with a third "
            "trailing subtag and try to resolve it. A path like "
            "`/de-simple-page-test/` would be treated as carrying a language tag "
            "instead of correctly carrying none, so the routine would attempt to "
            "resolve `de-simple-page-test` rather than returning nothing — "
            "failing the graded observable that such a path is NOT a language "
            "code. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the ASCII-branch `match langPrefix path` clause: on "
            "`/de-simple-page-test/` the spec's two-subtag candidate does not "
            "terminate, so `langPrefix` is `none` and the result must be `none`, "
            "but the three-subtag rival recognises `de-simple-page-test` and "
            "returns `resolveVariant` of it. Refuted at the UPPER edge of the "
            "subtag budget. If it verifies => SPEC-TOO-WEAK (the upper bound of "
            "the budget would not be enforced)."
        ),
        "witness": (
            "-- Over-budget rival recognises a three-subtag candidate the spec\n"
            "-- rejects (`langPrefix … = none`), so it returns `resolveVariant …`\n"
            "-- where the spec returns `none`; conditioned only on that candidate\n"
            "-- resolving to SOMETHING, which separates it from the spec's `none`.\n"
            "example (h : resolveVariant \"de-simple-page-test\".data ≠ none) :\n"
            "    ¬ problem_spec_langCodeFromPath \"/de-simple-page-test/\".data\n"
            "      (implementation_langCodeFromPath \"/de-simple-page-test/\".data) := by\n"
            "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
            "  simp only [Id.run, pure]\n"
            "  norm_num [show allAscii \"/de-simple-page-test/\".data = true from by decide,\n"
            "            show langPrefix \"/de-simple-page-test/\".data = none from by decide,\n"
            "            show langPrefixN 3 \"/de-simple-page-test/\".data = some \"de-simple-page-test\".data from by decide]\n"
            "  exact h\n"
        ),
    },
    {
        "id": "weak-echo-candidate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ECHO),
        "refinement": (
            "returning the recognised candidate itself instead of the supported "
            "variant it resolves to corresponds to a real patch that skipped the "
            "unchanged variant-resolution step. On a path like `/en-gb/` the "
            "candidate `en-gb` is recognised but the supported variant is the "
            "more generic `en`; echoing the candidate would surface `en-gb` "
            "where the graded observable demands `en`. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the ASCII-branch `some lc => resolveVariant lc` clause: "
            "the spec pins the result to `resolveVariant` of the recognised "
            "candidate, not the candidate itself, so on `/en-gb/` the rival's "
            "`some \"en-gb\"` disagrees with `resolveVariant \"en-gb\"` whenever "
            "the resolver maps the candidate elsewhere. Attacks the "
            "resolver-application clause (distinct from the budget clause). If it "
            "verifies => SPEC-TOO-WEAK (the result could echo the answer key "
            "without resolving)."
        ),
        "witness": (
            "-- Echo rival returns the raw candidate `some \"en-gb\"`; the spec\n"
            "-- returns `resolveVariant \"en-gb\"`. Conditioned only on the\n"
            "-- resolver mapping this candidate to a DIFFERENT value (a generic\n"
            "-- variant), which separates the echo from the resolved result.\n"
            "example (h : resolveVariant \"en-gb\".data ≠ some \"en-gb\".data) :\n"
            "    ¬ problem_spec_langCodeFromPath \"/en-gb/\".data\n"
            "      (implementation_langCodeFromPath \"/en-gb/\".data) := by\n"
            "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
            "  simp only [Id.run, pure]\n"
            "  norm_num [show allAscii \"/en-gb/\".data = true from by decide,\n"
            "            show langPrefix \"/en-gb/\".data = some \"en-gb\".data from by decide]\n"
            "  exact fun heq => h heq.symm\n"
        ),
    },
    {
        "id": "weak-drop-terminator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROPTERM),
        "refinement": (
            "dropping the requirement that the candidate be terminated by `/` or "
            "the end of the path over-accepts: a real patch that omitted the "
            "terminator would treat a word run followed by other punctuation as a "
            "recognised tag. A path like `/aaa.bbb/` (run `aaa`, next char `.`) "
            "would be treated as carrying the language tag `aaa` and the routine "
            "would try to resolve it, instead of correctly carrying no tag. Does "
            "NOT resolve — it diverges from the routine on every run terminated by "
            "non-`/` punctuation."
        ),
        "rationale": (
            "REJECT from the terminator clause of the ASCII-branch candidate: the "
            "spec's candidate must be delimited by `/` or end of path, so on "
            "`/aaa.bbb/` the candidate does not terminate and `langPrefix` is "
            "`none` => result `none`, but the drop-terminator rival recognises "
            "`aaa` and returns `resolveVariant \"aaa\"`. Attacks the terminator "
            "clause, distinct from the budget and resolver-application clauses. If "
            "it verifies => SPEC-TOO-WEAK (the `(/|$)` anchor would not be enforced)."
        ),
        "witness": (
            "-- Drop-terminator rival: impl inlines the prefix parse but omits the\n"
            "-- terminator, so on `/aaa.bbb/` (run `aaa` stops at `.`) it returns\n"
            "-- `resolveVariant \"aaa\"` while the spec returns `none` (langPrefix\n"
            "-- requires a `/`/end terminator). Conditioned only on that candidate\n"
            "-- resolving to SOMETHING.\n"
            "--\n"
            "-- NOTE (discrimination): every `show` below is an identity of a FROZEN\n"
            "-- pure function, so it holds on BOTH sides; the impl is reduced through\n"
            "-- the GOAL rather than by a rewrite that names the rival's own value.\n"
            "-- That is what makes gold's failure track the claim: on gold the spec\n"
            "-- side reduces to `pure none` and the residual goal is\n"
            "-- `¬pure none = none` (and `pure none = none` when the claim is\n"
            "-- flipped), so the exit code carries information about what is claimed.\n"
            "example (h : resolveVariant \"aaa\".data ≠ none) :\n"
            "    ¬ problem_spec_langCodeFromPath \"/aaa.bbb/\".data\n"
            "      (implementation_langCodeFromPath \"/aaa.bbb/\".data) := by\n"
            "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
            "  norm_num [Id.run, show allAscii \"/aaa.bbb/\".data = true from by decide,\n"
            "            show langPrefix \"/aaa.bbb/\".data = none from by decide,\n"
            "            show List.takeWhile isWord \"aaa.bbb/\".data = \"aaa\".data from by decide,\n"
            "            show (grabSubtags 2 (List.dropWhile isWord \"aaa.bbb/\".data)).1 = ([] : List Char)\n"
            "              from by decide,\n"
            "            show isWord 'a' = true from by decide]\n"
            "  simpa using h\n"
        ),
    },
    {
        "id": "weak-allow-empty-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_EMPTYRUN),
        "refinement": (
            "accepting a path with no leading word run corresponds to a real patch "
            "that treated an empty primary subtag as a match: on a path like `//` "
            "it would feed an empty candidate to the resolver instead of carrying "
            "no tag. The primary subtag is required to be a non-empty word run, so "
            "this over-accepts at the no-candidate boundary. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from the non-empty-primary-subtag clause: the spec requires a "
            "non-empty leading word run, so on `//` `langPrefix` is `none` => "
            "result `none`, but the empty-run rival accepts the empty candidate and "
            "returns `resolveVariant \"\"`. Attacks the no-candidate boundary, "
            "distinct from the budget/terminator/echo clauses. If it verifies => "
            "SPEC-TOO-WEAK (the non-empty primary-subtag requirement would not be "
            "enforced)."
        ),
        "witness": (
            "-- Allow-empty-run rival: impl inlines the parse but drops the\n"
            "-- non-empty guard, so on `//` (no leading word run) it accepts an\n"
            "-- EMPTY candidate and returns `resolveVariant \"\"`, while the spec\n"
            "-- returns `none`. Conditioned only on the empty candidate resolving.\n"
            "--\n"
            "-- NOTE (discrimination): as for `weak-drop-terminator`, the impl is\n"
            "-- reduced through the GOAL and every `show` is an identity of a frozen\n"
            "-- pure function, valid on both sides. On gold the residual goal is\n"
            "-- `¬pure none = none`, and flipping the claim changes it to\n"
            "-- `pure none = none` — so gold's failure tracks what is claimed\n"
            "-- instead of being the same rewrite failure either way.\n"
            "example (h : resolveVariant \"\".data ≠ none) :\n"
            "    ¬ problem_spec_langCodeFromPath \"//\".data\n"
            "      (implementation_langCodeFromPath \"//\".data) := by\n"
            "  unfold problem_spec_langCodeFromPath implementation_langCodeFromPath\n"
            "  norm_num [Id.run, show allAscii \"//\".data = true from by decide,\n"
            "            show langPrefix \"//\".data = none from by decide]\n"
            "  exact h\n"
        ),
    },
]


# No consumed axioms: the two opaque callees are deep-model / A-reference
# symbols used identically on both sides of the spec equation, so the PBT axiom
# lane has no in-model axiom obligation to re-discharge.
AXIOM_TESTS = []
