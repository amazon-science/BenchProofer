"""properties.py — G-PBT falsification battery for django__django-14349 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves the
obligation, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a single string input):

  validateUrl (value : List Char) : Bool
      problem_spec:
        (containsForbidden value = true  → result = false) ∧
        (containsForbidden value = false → result = structurallyValid value)

  A candidate address (modeled per-code-point as ``List Char``) is judged
  acceptable or not (``Bool``; ``true`` = accepted, ``false`` = rejected). Two
  independent conditions govern acceptance and the spec has one top-level clause
  per condition:

    * SAFETY (clause 1) — if the address contains ANY of the designated
      disallowed control characters (``containsForbidden``, a fully-unfolded
      per-character membership test over horizontal tab / carriage return / line
      feed) it is rejected outright: the verdict is ``false``, regardless of the
      structural verdict.
    * STRUCTURE (clause 2) — otherwise the verdict is EXACTLY the structural
      acceptance condition ``structurallyValid value``. ``structurallyValid`` is
      an ``opaque`` carrier for the unchanged address-grammar check; the modeled
      behavior is how the safety screen COMBINES with the structural verdict, not
      the grammar itself.

  The two clauses together decide every input, so the verdict is never free.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY (``value`` is held at a half-permission, so a
    rival that writes it is rejected for insufficient permission). Lean is
    referentially transparent: ``value : List Char`` is a plain immutable value,
    there is no fractional permission to violate and no aliasing to exploit, so
    this class has NO expressible instance here. No substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION (nagini ``weak-diverge``) — nothing to ship, but
    NOT because it is unwritable. The port claimed "a diverging implementation
    cannot be written at all"; that is false, and the audit measured it. A
    ``partial def spin (n : Nat) : Bool := spin (n + 1)`` deferred to on the clean
    path compiles fine, and this spec REJECTS it (exit 1, residual goal
    ``spin 0 = structurallyValid value``) — clause 2 pins the result to
    ``structurallyValid value``, and a non-reducing term is not that. So the
    correct statement is that on THIS bundle the divergence rival is already
    covered by clause 2 rather than being inexpressible. The velvet
    ``partial``-semantics hole is a separate, already-recorded finding
    (``the corpus-wide termination-semantics finding``); it does not apply to a plain Lean ``def``
    bundle and is not re-reported here.

  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. Clause 1's decision is pinned
    to ``containsForbidden``, a fully-unfolded predicate over the argument (no
    answer-key). Clause 2 defers to ``structurallyValid value``, the opaque
    carrier applied to the SAME input the caller passed — so no echo can satisfy
    the postcondition while doing different work; the unique satisfier IS the
    grounded decision. The honest analogue is the cheapest correct impl (the
    POSITIVE CONTROL below).

  * CONTROL-FLOW FORK / PARTIAL-DOMAIN — APPLY and are the load-bearing lane.
    The single behavior is the two-way fork between the two clauses; the rivals
    below each mishandle one clause on a distinct sub-domain.

  * AXIOM lane (nagini ``AXIOM_TESTS``) — DROPPED. The axiom lane is G-AX's job;
    this gate ignores it. AXIOM_TESTS is empty.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script (a ``refine``/``simp only``
tuned to the ``Id.run do`` form) breaks on any reshaped impl — so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet stating the spec predicate directly at ONE concrete
input; each was checked to HOLD of its rival and to FAIL on the frozen solution
(so it discriminates rather than asserting a tautology).

CONDITIONING ON THE CARRIER. ``structurallyValid`` is ``opaque``, so on a clean
address clause 2 equates the result to a term with no computable value. Every
witness that must reach clause 2 (or that must compare against a clean-address
verdict) states its refutation at a point described by a SINGLE hypothesis
``structurallyValid <lit> = true`` / ``= false``. That is exactly the sub-domain
where the rival is wrong: whenever the structural verdict takes the assumed
value, the rival's answer differs from the spec's. Each witness carries at most
ONE hypothesis about ONE opaque term, so the assumptions cannot be
contradictory.

BINDER / CLAUSE COVERAGE (the gate does NOT check this; documented here):
  * The single input binder ``value`` is varied across SIX distinct points: a
    leading-tab address, a mid-string-CR address, a line-feed address, an address
    containing a space, and two forbidden-char-FREE addresses. So no rival is
    refuted at a value another shares.
  * The opaque channel ``structurallyValid value`` is varied ``= true``
    (prepatch, first-char, always-reject, charset-subset, overscreen) AND
    ``= false`` (drop-structure), so that carrier is not pinned to a single
    verdict across the lane.
  * CLAUSE 1 (safety screen) is attacked in BOTH directions and on both of its
    axes. Under-screening: ``weak-prepatch`` (no screen at all, leading tab),
    ``weak-first-char-only`` (POSITION axis — mid-string CR, the
    not-first-position sub-domain), ``weak-charset-subset`` (MEMBER axis — a
    line-feed address, the group member the other cases never make load-bearing).
    Over-screening: ``weak-overscreen-space`` bounds the screen from ABOVE, so the
    spec is shown to disqualify on the designated characters AND NO OTHERS.
  * CLAUSE 2 (defer to structural verdict) is attacked by ``weak-drop-structure``
    (returns accept where the verdict is reject) and ``weak-always-reject``
    (returns reject where the verdict is accept) — both directions of the
    deferral. A non-reducing (``partial``) impl deferred to on the clean path is
    also rejected by this clause; see the DIVERGENCE note above.
  Every top-level clause is attacked, each in both directions.
  ``pts`` = 6 distinct input points.

AUDIT PROVENANCE. The ``weak-charset-subset`` and ``weak-overscreen-space`` cases
and the ``pos-functional-if`` reshape were added/repaired by an independent audit
of this battery; the prose above reflects what that audit re-derived with real
builds, including two claims the original port stated and the audit measured to
be false (the positive's "the frozen tactic no longer applies", and divergence
being inexpressible). Both are corrected in place rather than left standing.
"""
from pathlib import Path

INSTANCE = "django__django-14349"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  if containsForbidden value then\n"
    "    return false\n"
    "  return structurallyValid value"
)

_PROOF_BODY = (
    "  intro value\n"
    "  unfold problem_spec_validateUrl implementation_validateUrl\n"
    "  refine ⟨fun h => ?_, fun h => ?_⟩ <;>\n"
    "    simp only [Id.run, h, if_true, if_false, Bool.false_eq_true, pure, bind]"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with only the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — a structurally different CORRECT impl that
# drops the mutable `Id.run do` and spells the two-way decision as one
# functional `if … then false else structurallyValid value`. Same value on
# every input; the frozen tactic script (tuned to the `Id.run do` form) no
# longer applies, so the obligation is RE-PROVEN by case analysis on
# `containsForbidden` (statement byte-identical, no new lemma/axiom).
# ---------------------------------------------------------------------------
# AUDIT NOTE (measured, not argued). The original positive here was
#   `if containsForbidden value then false else structurallyValid value`
# and its rationale claimed the frozen tactic "no longer applies". That claim was
# FALSE: building that impl under the FROZEN proof body verbatim exits 0 — the
# `simp only [Id.run, h, ...]` closes it unchanged (the `Id.run do` sugar reduces
# to exactly that `if`, so the two impls are definitionally equal and the reshape
# was cosmetic). A positive whose proof is the frozen script tests only that the
# script still runs. Replaced with a reshape that is NOT defeq to the frozen impl
# and that the frozen script provably CANNOT close.
#
# `!containsForbidden value && structurallyValid value` computes the same Bool on
# every input, but its head symbol is `&&` rather than `ite`, so no amount of
# `Id.run`/`if_true`/`if_false` rewriting reaches it. Measured: with the FROZEN
# proof body it FAILS (exit 1, `⊢ (!true && structurallyValid value) = false`);
# with the re-proof below it VERIFIES (exit 0). So this case exercises the spec's
# two clauses through a genuinely different computation shape.
_POS_IMPL = (
    "def implementation_validateUrl (value : List Char) : Bool :=\n"
    "  !containsForbidden value && structurallyValid value"
)
_POS_PROOF = (
    "  intro value\n"
    "  unfold problem_spec_validateUrl implementation_validateUrl\n"
    "  by_cases h : containsForbidden value = true\n"
    "  · simp [h]\n"
    "  · simp only [Bool.not_eq_true] at h\n"
    "    simp [h]"
)

# ADMISSIBILITY — the frozen theorem carries NO precondition hypothesis (the
# behavior is total, `∀` unguarded), so nagini's precondition-admission probe
# has no binder to attack. The honest analogue: discharge the spec predicate at
# the F2P ground input (a mid-string CR address, which must be rejected) inside
# the proof region as a `have`, alongside the frozen obligation kept verbatim.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_validateUrl ['a', '\\r', 'b']\n"
    "      (implementation_validateUrl ['a', '\\r', 'b']) := by\n"
    "    unfold problem_spec_validateUrl implementation_validateUrl\n"
    "    decide\n"
    + _PROOF_BODY
)


# ---------------------------------------------------------------------------
# UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
# MUST be rejected. Each carries (a) the refinement argument that its faithful
# real patch would NOT resolve the F2P, and (b) a refutation witness pinning the
# violation at one concrete input (checked to hold of the rival, fail on gold).
# ---------------------------------------------------------------------------

# CLAUSE-1, whole-screen removed = the LITERAL pre-patch: no safety screen, defer
# straight to the structural verdict.
_PREPATCH = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  return structurallyValid value"
)

# CLAUSE-1, PARTIAL-DOMAIN: screen only the FIRST code point. Catches a leading
# forbidden char but misses one anywhere past index 0.
_FIRST_CHAR = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  if (value.headD ' ') == '\\t' || (value.headD ' ') == '\\r'"
    " || (value.headD ' ') == '\\n' then\n"
    "    return false\n"
    "  return structurallyValid value"
)

# CLAUSE-2 dropped: keep the safety screen but on a clean address ACCEPT
# unconditionally instead of deferring to the structural verdict.
_DROP_STRUCTURE = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  if containsForbidden value then\n"
    "    return false\n"
    "  return true"
)

# CONTROL-FLOW: always reject (the accept fork removed).
_ALWAYS_REJECT = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  return false"
)

# CLAUSE-1, MEMBER sub-domain (added by audit): the screen enumerates only two of
# the three designated characters, so a line-feed address slips through. The
# ported lane varied the forbidden character's POSITION but never its IDENTITY.
_CHARSET_SUBSET = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  if value.any (fun c => c == '\\t' || c == '\\r') then\n"
    "    return false\n"
    "  return structurallyValid value"
)

# CLAUSE-2, OVER-rejection direction (added by audit): the screen is widened to a
# character the designated group does not contain, so an address the structural
# condition governs is rejected outright. Nothing else in the lane bounds the
# safety screen from ABOVE.
_OVERSCREEN = (
    "def implementation_validateUrl (value : List Char) : Bool := Id.run do\n"
    "  if containsForbidden value || value.any (fun c => c == ' ') then\n"
    "    return false\n"
    "  return structurallyValid value"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-functional-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the `Id.run do` control flow entirely "
            "and spells the two-way decision as one BOOLEAN CONJUNCTION "
            "(`!containsForbidden value && structurallyValid value`). It computes "
            "the same Bool on every input, so it must satisfy both clauses — the "
            "safety screen forces `false`, and on a clean address `!false && x` "
            "is `x`, exactly `structurallyValid value`. What makes this a real "
            "soundness probe rather than a cosmetic one: its head symbol is `&&`, "
            "not `ite`, so it is NOT definitionally equal to the frozen impl and "
            "the frozen tactic script provably cannot close it — measured, the "
            "frozen proof body against this impl exits 1 with residual goal "
            "`(!true && structurallyValid value) = false`. (An earlier version of "
            "this case used `if containsForbidden value then false else "
            "structurallyValid value`, which the `Id.run do` sugar reduces to "
            "definitionally; the frozen script closed it verbatim, so the case "
            "tested only that the script still runs. Replaced by audit.) The "
            "theorem STATEMENT is byte-identical; the obligation is re-proven by "
            "case analysis on `containsForbidden value`, each branch closing by "
            "`simp`, with no new lemma, axiom, or assumption token. If it FAILS "
            "=> SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at the F2P ground input.
    # =====================================================================
    {
        "id": "admiss-forbidden-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the frozen theorem carries no precondition hypothesis (the behavior "
            "is total), so there is no binder for nagini's precondition-admission "
            "probe to attack; the honest analogue discharges the spec predicate at "
            "the F2P ground input — a mid-string carriage-return address "
            "`['a', '\\r', 'b']`, which the safety screen must reject (`result = "
            "false`) — by `decide` inside the existing tactic body as a `have`, "
            "then closes the frozen obligation verbatim. Verifies (else the "
            "modeled behavior is unsatisfiable at exactly the input the F2P "
            "exercises). Nothing is assumed: the STATEMENT is byte-identical, the "
            "ground instance is a `have`, no new declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals.
    # =====================================================================
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH),
        "refinement": (
            "this IS the pre-patch behavior: no raw-character safety screen — the "
            "address is handed straight to the unchanged structural check. On a "
            "runtime patched for the upstream splitter fix, the disallowed control "
            "characters are stripped before the structural check ever sees them, "
            "so a forbidden-char address whose structural check would ACCEPT is "
            "accepted rather than rejected. That fails the F2P cases asserting the "
            "address is rejected (e.g. a leading-tab or mid-string-CR address). "
            "Does NOT resolve — the precise change the spec senses."
        ),
        "rationale": (
            "REJECT from clause 1 (`containsForbidden value = true → result = "
            "false`): on a leading-tab address whose structural verdict is accept, "
            "the rival returns the structural verdict (accept) instead of the "
            "mandated reject. CONTROL-FLOW: the early-reject fork is removed. If it "
            "VERIFIES => SPEC-TOO-WEAK (the safety screen is not enforced)."
        ),
        "witness": (
            "-- Refuted on a LEADING-tab address whose structural verdict is\n"
            "-- accept: the safety screen must reject it regardless.\n"
            "example (h : structurallyValid ['\\t', 'a'] = true) :\n"
            "    ¬ problem_spec_validateUrl ['\\t', 'a']\n"
            "      (implementation_validateUrl ['\\t', 'a']) := by\n"
            "  unfold problem_spec_validateUrl implementation_validateUrl\n"
            "  simp_all [containsForbidden, Id.run]\n"
        ),
    },
    {
        "id": "weak-first-char-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FIRST_CHAR),
        "refinement": (
            "screening only the first code point is what a real patch that tested "
            "just the leading character would do. It rejects a LEADING forbidden "
            "char but ACCEPTS one anywhere past index 0 — so it does NOT reject a "
            "mid-string-CR address, a literal F2P input asserting the address is "
            "rejected. A genuine PARTIAL-DOMAIN break on the not-first-position "
            "sub-domain; does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 1 (`containsForbidden value = true → result = "
            "false`): for an address whose only forbidden char is at index ≥ 1 "
            "(the CR in `['a', '\\r', 'b']`) with an accept structural verdict, the "
            "rival's first-char test is clean, so it returns accept, but clause 1 "
            "demands reject. PARTIAL-DOMAIN: the rival pins only the first-position "
            "sub-domain. Refuted at a DISTINCT point from weak-prepatch's leading "
            "tab (which this rival would correctly reject), so its distinguishing "
            "sub-domain is demonstrated. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted where the only forbidden char is mid-string (index 1),\n"
            "-- with an accept structural verdict: first-char screening misses it.\n"
            "example (h : structurallyValid ['a', '\\r', 'b'] = true) :\n"
            "    ¬ problem_spec_validateUrl ['a', '\\r', 'b']\n"
            "      (implementation_validateUrl ['a', '\\r', 'b']) := by\n"
            "  unfold problem_spec_validateUrl implementation_validateUrl\n"
            "  simp_all [containsForbidden, Id.run]\n"
        ),
    },
    {
        "id": "weak-drop-structure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_STRUCTURE),
        "refinement": (
            "keeping the safety screen but ACCEPTING every forbidden-char-free "
            "address is what a real patch that added the new screen but deleted the "
            "rest of validation (scheme/regex/host checks) would do. It would "
            "accept every clean address regardless of well-formedness, failing "
            "every pre-existing invalid-address case the unchanged structural check "
            "rejects. Does NOT resolve (the deferral to the structural verdict is "
            "part of the unchanged behavior the patch must preserve)."
        ),
        "rationale": (
            "REJECT from clause 2 (`containsForbidden value = false → result = "
            "structurallyValid value`): on a clean address whose structural verdict "
            "is REJECT, the rival returns accept, but clause 2 demands the result "
            "equal the structural verdict. It pins the safety half of the decision "
            "but unpins the structural half — the only rival refuted where "
            "`structurallyValid value = false`. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted on a forbidden-char-FREE address whose structural verdict\n"
            "-- is reject: the result must equal that verdict (reject), not accept.\n"
            "example (h : structurallyValid ['a', 'b'] = false) :\n"
            "    ¬ problem_spec_validateUrl ['a', 'b']\n"
            "      (implementation_validateUrl ['a', 'b']) := by\n"
            "  unfold problem_spec_validateUrl implementation_validateUrl\n"
            "  simp_all [containsForbidden, Id.run]\n"
        ),
    },
    {
        "id": "weak-always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_REJECT),
        "refinement": (
            "always rejecting is what a real patch that hard-coded the guard true "
            "(or compared against an always-matching set) would do — it rejects "
            "EVERY address, including every well-formed one the project must "
            "accept, failing every valid-address case that requires acceptance. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 2 (`containsForbidden value = false → result = "
            "structurallyValid value`): on a clean address whose structural verdict "
            "is ACCEPT, the rival returns reject, but clause 2 demands the result "
            "equal the structural verdict (accept). CONTROL-FLOW (dual of "
            "weak-prepatch): the accept fork is removed. If it VERIFIES => "
            "SPEC-TOO-WEAK (the accept condition is unpinned)."
        ),
        "witness": (
            "-- Refuted on a forbidden-char-FREE address whose structural verdict\n"
            "-- is accept: the result must equal that verdict (accept), not reject.\n"
            "example (h : structurallyValid ['x'] = true) :\n"
            "    ¬ problem_spec_validateUrl ['x']\n"
            "      (implementation_validateUrl ['x']) := by\n"
            "  unfold problem_spec_validateUrl implementation_validateUrl\n"
            "  simp_all [containsForbidden, Id.run]\n"
        ),
    },

    # =====================================================================
    # ADDED BY AUDIT — two sub-domains the ported lane left unattacked.
    # =====================================================================
    {
        "id": "weak-charset-subset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_CHARSET_SUBSET),
        "refinement": (
            "screening horizontal tab and carriage return but NOT line feed is what "
            "a real patch that enumerated the disallowed group incompletely would do "
            "— it rejects tab and CR addresses but accepts a line-feed one, which is "
            "just as splittable and which the safety condition disqualifies. It fails "
            "every case asserting a line-feed address is rejected. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 1 (`containsForbidden value = true → result = "
            "false`): `containsForbidden` disqualifies on ANY of the three "
            "characters, so on a line-feed address with an accept structural verdict "
            "clause 1 demands reject while the rival's two-character screen is clean "
            "and returns accept. This is the MEMBER sub-domain of the disallowed "
            "group: the ported lane varied the POSITION of the forbidden character "
            "(leading vs mid-string) but only ever used tab and CR, so the line-feed "
            "member of clause 1's set was never load-bearing in any case. Refuted at "
            "a point no other case uses. If it VERIFIES => SPEC-TOO-WEAK (clause 1's "
            "set is under-enforced)."
        ),
        "witness": (
            "-- Refuted on a LINE-FEED address with an accept structural verdict:\n"
            "-- clause 1 disqualifies on any member of the group, line feed included.\n"
            "example (h : structurallyValid ['\\n'] = true) :\n"
            "    ¬ problem_spec_validateUrl ['\\n']\n"
            "      (implementation_validateUrl ['\\n']) := by\n"
            "  unfold problem_spec_validateUrl implementation_validateUrl\n"
            "  simp_all [containsForbidden, Id.run]\n"
        ),
    },
    {
        "id": "weak-overscreen-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_OVERSCREEN),
        "refinement": (
            "disqualifying on a plain space in ADDITION to the three designated "
            "characters is what a real patch that widened the disallowed group (e.g. "
            "screening all whitespace rather than the designated group) would do. It "
            "rejects addresses containing a space that the unchanged structural check "
            "governs, so it fails the pre-existing cases whose verdict on such an "
            "address must come from the structural condition alone. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause 2 (`containsForbidden value = false → result = "
            "structurallyValid value`): a space is NOT in the disallowed group, so on "
            "an address containing one `containsForbidden` is false and clause 2 pins "
            "the result to the structural verdict; the rival's widened screen returns "
            "reject regardless. This is the OVER-rejection direction: every other "
            "rival in the lane errs by accepting too much (or rejects unconditionally, "
            "which no faithful patch resembles), so nothing tested that the safety "
            "screen is bounded ABOVE — that it disqualifies on the designated "
            "characters and no others. If it VERIFIES => SPEC-TOO-WEAK (clause 1's "
            "set is not pinned from above and a wider screen would satisfy the spec)."
        ),
        "witness": (
            "-- Refuted on an address whose only unusual character is a SPACE, which\n"
            "-- is not in the disallowed group: the verdict must come from clause 2.\n"
            "example (h : structurallyValid ['a', ' ', 'b'] = true) :\n"
            "    ¬ problem_spec_validateUrl ['a', ' ', 'b']\n"
            "      (implementation_validateUrl ['a', ' ', 'b']) := by\n"
            "  unfold problem_spec_validateUrl implementation_validateUrl\n"
            "  simp_all [containsForbidden, Id.run]\n"
        ),
    },
]


# AXIOM lane: DROPPED — the axiom lane belongs to G-AX, not this gate.
AXIOM_TESTS = []
