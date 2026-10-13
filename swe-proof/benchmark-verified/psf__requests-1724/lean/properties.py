"""properties.py — G-PBT falsification battery for psf__requests-1724 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_normalizeMethod`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models ``normalize_method`` over a ``PSeq[int]`` code-point carrier with a heap
input held at ``Acc(list_pred(chars), 1/2)`` and pins two load-bearing clauses:
a GROUNDED content clause (``ToSeq(Result().chars) == upper_seq(ToSeq(chars))``)
and a constant flavour clause (``Result().native == True``). This Lean bundle
models the SAME single purely-functional core — normalizing a request method
name to its upper-cased, native (non-wide) form — over a ``PyStr`` carrier
(``{ chars : List Char, wide : Bool }``) and pins the SAME two clauses:

  * (C0 content)  ``result.chars = method.chars.map Char.toUpper`` — every code
    point is the upper-cased input code point at the same position (the analogue
    of nagini's grounded ``upper_seq`` content pin; grounded structurally in the
    input, no opaque answer key to echo);
  * (C1 flavour)  ``result.wide = false`` — the stored method is native, never
    wide, independent of the input's width (the analogue of nagini's constant
    ``Result().native == True`` flavour pin — the bug-sensing clause).

The BEHAVIOURAL DISCRIMINATOR (the fix): the stored method must be forced to the
native (non-wide) flavour regardless of the supplied name's width. The pre-fix
behavior carried the supplied width forward; the ``wide-echo`` rival below IS
that pre-fix behavior, and on a wide-supplied method it stores a wide method that
later contaminates request assembly — exactly the reported defect.

BINDER STRUCTURE. The spec predicate has ONE input binder, ``method : PyStr``,
with two load-bearing FIELDS: ``method.chars`` (the code-point sequence) and
``method.wide`` (the width flag). Both are varied across the reject witnesses:
``method.wide`` takes both ``true`` (the ``wide-echo`` witness, where the flag is
the discriminator) and ``false`` (the content witnesses, which hold width fixed
so the only divergence is the content clause), and ``method.chars`` ranges over
``['a']`` and ``['a','b']``. The three reject witnesses probe three DISTINCT
inputs (``pts=3``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds ``chars`` at
    ``Acc(list_pred(chars), 1/2)`` and makes in-place-write / append rivals a
    MANDATORY class (``frame-mutate-input-inplace``, ``frame-append-input``).
    Those rivals reject THERE from the Viper permission system: writing a
    half-permission input is insufficient-permission. This Lean carrier is
    referentially transparent — ``method`` is an immutable value, there is no
    ``mut`` input binder, no aliasing, and no read-only heap cell to overwrite —
    so the entire permission-mutation class collapses. No substitute probe is
    fabricated (porting map: vacuous here). See ``assessment``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The nagini sibling notes its two clauses
    are grounded (the content pin is a fully-unfolded fold, the flavour pin a
    literal constant), so there is no answer-key oracle to echo. The same holds
    here: C0 is a structural per-position equation over ``method.chars`` and C1
    is the literal ``false``. Producing the upper-cased native result IS doing
    the work. In its place the battery carries honest cheapest-implementation
    POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where a clause bites: carrying the supplied width forward (the
    pre-fix bug, attacks C1); dropping the upper-casing entirely (identity,
    attacks C0); and upper-casing every code point except the first (off-by-one,
    attacks C0). These are the direct ports of the nagini content/flavour rivals.

  * LENGTH — APPLIES, and is an AUDIT ADDITION. The nagini sibling pins the
    length as its own clause (`len(Result().chars) == len(chars)`); this bundle
    folds it into the single list equation C0. That subsumption is real but the
    three ported rivals are all length-PRESERVING, so nothing exercised it. The
    `pad-extra-codepoint` rival closes that: it is correct on C1 and correct
    per-position on C0, and diverges only by emitting one extra code point.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate directly at one
CONCRETE ground ``PyStr`` literal and refutes it by ``decide``. Each witness
binds NOTHING in its head (the input is a ground structure literal), so there are
no hypotheses whose consistency could be in question. Each was checked with two
real ``lake env lean`` builds (via ``scripts/lean_verify.sh`` + the gate's own
``witness_file`` surgery) to HOLD of its rival and to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology.

Re-derived independently at audit (rival exit 0 / gold exit 1 for all four):
``wide-echo``, ``identity-no-upper``, ``skip-first-upper``,
``pad-extra-codepoint``. On every gold-side build the failure is a SEMANTIC
refutation — ``Tactic `decide` proved that the proposition ¬(... ) is false``,
i.e. the kernel evaluated the concrete claim and found the frozen impl satisfies
the spec there — never a missing identifier, a type error, or a stuck reduction.
The whole carrier (``List Char`` + ``Char.toUpper`` + ``Bool``) is closed under
kernel reduction, so ``decide`` genuinely decides and no
``witness_reference`` is needed.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
diverges from gold on the F2P method-case / native-flavour behavior, so the
faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed operation — native coercion — and the unchanged
upper-casing are both modeled DEEPLY; see ``mapping.md``). The axiom lane belongs
to G-AX, so the nagini ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "psf__requests-1724"
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


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The two per-field impl updates and the def header. Every impl reshape lands
# entirely inside `-- impl-start`/`-- impl-end`.
_I_DEF = "def implementation_normalizeMethod (method : PyStr) : PyStr := Id.run do"
_I_WIDE = "  m := { m with wide := false }\n"
_I_CHARS = "  m := { m with chars := m.chars.map Char.toUpper }\n"

# The whole gold impl body (def header + `do` block) for the structure-literal
# reshape. Lies wholly inside the impl region.
_I_BODY = (
    "def implementation_normalizeMethod (method : PyStr) : PyStr := Id.run do\n"
    "  -- Coerce the supplied name to a native text string, then upper-case it.\n"
    "  let mut m := method\n"
    "  m := { m with wide := false }\n"
    "  m := { m with chars := m.chars.map Char.toUpper }\n"
    "  return m\n")

# The frozen proof's intro line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro method\n"

# The frozen proof's whole tactic body (proof region). A positive whose impl is
# NOT definitionally the frozen result has to re-prove the obligation, and it
# replaces this block. The theorem STATEMENT above it is untouched, so
# `variant_scope`'s obligation-preserved rule still holds byte-for-byte.
_P_BODY = (
    "  intro method\n"
    "  unfold problem_spec_normalizeMethod implementation_normalizeMethod\n"
    "  simp [Id.run, pure]\n")


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one ground `PyStr` literal and
# refutes it by `decide` (the carrier is fully computable — `List Char` +
# `Char.toUpper` + a `Bool` — so no conditioning on an opaque term is needed).
# ---------------------------------------------------------------------------
def _w(chars, wide):
    lit = f"{{ chars := {chars}, wide := {wide} }}"
    return (
        f"example : ¬ problem_spec_normalizeMethod\n"
        f"    {lit}\n"
        f"    (implementation_normalizeMethod {lit}) := by\n"
        "  unfold problem_spec_normalizeMethod implementation_normalizeMethod\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_normalizeMethod` statement byte-identical and the frozen
    # proof body unchanged (both reshapes are definitionally the frozen result,
    # so `unfold ...; simp [Id.run, pure]` still closes — no proof authoring, no
    # helper lemma, no assumption token). (Verified: real builds.)
    # =====================================================================
    {
        "id": "pos-field-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two independent field updates: upper-case the code points
        # first, then clear the width flag. Same result, different write order.
        "module": _swaps(
            _BASE,
            (_I_WIDE + _I_CHARS, _I_CHARS + _I_WIDE),
        ),
        "rationale": "correct reshape that swaps the order of the two independent "
                     "per-field updates (upper-case first, then clear the width "
                     "flag). It computes the SAME result on every input, so C0 and "
                     "C1 both still hold — else SPEC-TOO-STRONG. Definitionally the "
                     "frozen result, so the frozen proof still closes; statement "
                     "byte-identical, no new axiom/lemma. Ports the nagini "
                     "pos-control-inline-elem positive (a local-shape reshape of the "
                     "same correct computation).",
    },
    {
        "id": "pos-struct-literal",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: drop the `Id.run do` / `let mut`
        # imperative scaffold entirely and build the result as a single structure
        # literal. Definitionally identical to the frozen body, so the frozen proof
        # still closes.
        "module": _swaps(
            _BASE,
            (_I_DEF, "def implementation_normalizeMethod (method : PyStr) : PyStr :="),
            (
                "  -- Coerce the supplied name to a native text string, then "
                "upper-case it.\n"
                "  let mut m := method\n"
                "  m := { m with wide := false }\n"
                "  m := { m with chars := m.chars.map Char.toUpper }\n"
                "  return m\n",
                "  { chars := method.chars.map Char.toUpper, wide := false }\n",
            ),
        ),
        "rationale": "correct reshape that abandons the imperative `Id.run do` / "
                     "`let mut` scaffold and constructs the result in one structure "
                     "literal. It produces the SAME upper-cased native result on "
                     "every input, so C0 and C1 both still hold — else "
                     "SPEC-TOO-STRONG. Definitionally the frozen result, so the "
                     "frozen proof still closes; statement byte-identical, no new "
                     "axiom/lemma. Ports the nagini pos-control-literal-native "
                     "positive (a structurally different correct impl of the same "
                     "behavior).",
    },

    # ---- AUDIT ADDITION (soundness): a correct reshape that is NOT
    # definitionally the frozen result, so it must genuinely RE-PROVE ----
    # Both positives above are definitional reshapes: `simp [Id.run, pure]`
    # closes them unchanged, which means neither exercises the spec's tolerance
    # for a DIFFERENT computation — only for a different spelling of the same
    # one. The two cases below close that gap. Each routes the content clause
    # through a genuinely different Lean term whose equality to
    # `List.map Char.toUpper` is a THEOREM, not `rfl`, and each supplies its own
    # proof of the frozen obligation inside the proof region (statement
    # byte-identical, no new top-level axiom/theorem/lemma — the bridging step is
    # an inline `have`). If either were rejected the spec would be
    # SPEC-TOO-STRONG: it would be pinning one particular *derivation* of the
    # upper-cased content rather than the content itself.
    {
        "id": "pos-string-roundtrip",
        "kind": "soundness",
        "expect": "verify",
        # Compute the content by round-tripping through the carrier's `String`
        # type and using `String.toUpper`, rather than mapping the list directly.
        # `(String.mk l).toUpper.data` is NOT definitionally `l.map Char.toUpper`
        # (it reduces through `String.mapAux`), so the frozen tactic body does
        # not close and the case re-proves via `String.map_eq`.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             "def implementation_normalizeMethod (method : PyStr) : PyStr :=\n"
             "  { chars := (String.mk method.chars).toUpper.data, wide := false }\n"),
            (_P_BODY,
             "  intro method\n"
             "  have hstr : ∀ l : List Char,\n"
             "      (String.mk l).toUpper.data = l.map Char.toUpper := by\n"
             "    intro l\n"
             "    simp [String.toUpper, String.map_eq]\n"
             "  unfold problem_spec_normalizeMethod implementation_normalizeMethod\n"
             "  simp [hstr]\n"),
        ),
        "rationale": "correct reshape that computes the content by round-tripping "
                     "the code points through the carrier's `String` type and "
                     "applying `String.toUpper`, instead of mapping the list. This "
                     "is NOT definitionally the frozen result — it reduces through "
                     "`String.mapAux`, so the frozen tactic body does NOT close and "
                     "the case supplies a real proof (`String.map_eq`) of the same "
                     "byte-identical statement. It produces the SAME upper-cased "
                     "native result on every input, so C0 and C1 both still hold — "
                     "else SPEC-TOO-STRONG, i.e. the spec would be pinning one "
                     "particular derivation of the content rather than the content. "
                     "Strengthens the two definitional positives above, which the "
                     "frozen tactic closes unchanged and which therefore only vary "
                     "the SPELLING of the frozen computation. (Verified: real build, "
                     "exit 0.)",
    },
    {
        "id": "pos-guarded-upper",
        "kind": "soundness",
        "expect": "verify",
        # Upper-case only the code points that are lower-case, leaving the rest
        # alone: `fun c => if c.isLower then c.toUpper else c`. Extensionally
        # equal to `Char.toUpper` (which is already the identity off 'a'..'z'),
        # but the equality needs the `Char.isLower` / `Char.toUpper` numeric
        # ranges to be reconciled, so it is a theorem rather than `rfl`.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             "def implementation_normalizeMethod (method : PyStr) : PyStr :=\n"
             "  { chars := method.chars.map "
             "(fun c => if c.isLower then c.toUpper else c),\n"
             "    wide := false }\n"),
            (_P_BODY,
             "  intro method\n"
             "  have hkey : ∀ c : Char,\n"
             "      (if c.isLower then c.toUpper else c) = c.toUpper := by\n"
             "    intro c\n"
             "    by_cases hc : c.isLower\n"
             "    · simp [hc]\n"
             "    · simp only [Char.isLower, Bool.and_eq_true, decide_eq_true_eq,\n"
             "        not_and] at hc\n"
             "      simp only [Char.toUpper, Char.toNat, ge_iff_le]\n"
             "      have h97 : (UInt32.toNat 97) = 97 := by decide\n"
             "      have h122 : (UInt32.toNat 122) = 122 := by decide\n"
             "      have hneg : ¬(97 ≤ c.val.toNat ∧ c.val.toNat ≤ 122) := by\n"
             "        rintro ⟨h1, h2⟩\n"
             "        simp only [UInt32.le_iff_toNat_le, ge_iff_le, h97, h122] at hc\n"
             "        omega\n"
             "      rw [if_neg hneg]\n"
             "      simp\n"
             "  unfold problem_spec_normalizeMethod implementation_normalizeMethod\n"
             "  simp [hkey]\n"),
        ),
        "rationale": "correct reshape that guards the case fold — it upper-cases "
                     "only the code points that ARE lower-case and passes the rest "
                     "through, which is extensionally `Char.toUpper` (already the "
                     "identity outside 'a'..'z') but not definitionally so: the "
                     "equality has to reconcile the `Char.isLower` and "
                     "`Char.toUpper` numeric ranges, so the frozen tactic body does "
                     "NOT close and the case supplies a real proof. It produces the "
                     "SAME result on every input, so C0 and C1 both still hold — "
                     "else SPEC-TOO-STRONG. The second of the two audit-added "
                     "non-definitional positives; together they show the spec "
                     "accepts a DIFFERENT computation of the content, not merely a "
                     "different spelling of the frozen one. (Verified: real build, "
                     "exit 0.)",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so the
    # nagini precondition-admission case (admiss-f2p-shaped, which witnessed that a
    # normal lowercase non-native method is in-domain) re-expresses as: discharge
    # the spec predicate by evaluation at a concrete F2P-shaped input — a lowercase
    # method name supplied as a WIDE string (the exact non-native shape the bug
    # concerns) — as a `have`, then close the frozen obligation verbatim. Nothing is
    # assumed: no new declaration, statement byte-identical, the ground instance is
    # a `have` prepended to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_normalizeMethod\n"
            "      { chars := ['p','o','s','t'], wide := true }\n"
            "      (implementation_normalizeMethod "
            "{ chars := ['p','o','s','t'], wide := true }) := by\n"
            "    unfold problem_spec_normalizeMethod implementation_normalizeMethod\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the smallest F2P-shaped input "
                     "(a lowercase method name 'post' supplied as a WIDE string — the "
                     "non-native flavour the bug concerns) by evaluation as a `have`, "
                     "then the frozen obligation is closed verbatim. Verifies (else "
                     "the modeled behavior would be unsatisfiable at exactly a normal "
                     "F2P input — the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, statement byte-identical, the "
                     "ground instance is a `have` in the existing tactic body. Ports "
                     "nagini's admiss-f2p-shaped.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the fix itself: carry the supplied width forward (attacks C1) ----
    {
        "id": "wide-echo",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: drop the native coercion, so the result carries the
        # supplied width flag forward instead of forcing native.
        "module": _swap(_BASE, _I_WIDE, ""),
        "refinement": "this IS the pre-fix behavior: the stored method carries the "
                      "SUPPLIED width forward instead of being coerced to native. A "
                      "faithful real patch omitting the native coercion keeps a "
                      "wide-supplied method wide; that wide method then contaminates "
                      "the assembled request with wide text downstream — the exact "
                      "reported defect. The pre-patch source is this impl and the "
                      "issue's failing behaviour, so the faithful patch would NOT "
                      "resolve the F2P.",
        "rationale": "REJECT from C1 (flavour): the spec pins `result.wide = false` "
                     "but the rival emits `result.wide = method.wide`, which differ "
                     "whenever the input is wide. Refuted at a wide-supplied input "
                     "(wide := true), the field that is the discriminator.",
        "witness": _w("['a']", "true"),
    },

    # ---- identity: drop the upper-casing (attacks C0) ----
    {
        "id": "identity-no-upper",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the upper-casing map entirely: the result copies the input code
        # points unchanged (still coerced native, so ONLY the content clause is
        # attacked). Verifies only on inputs with no lowercase code point.
        "module": _swap(_BASE, _I_CHARS, ""),
        "refinement": "a real patch that coerced the method to native WITHOUT "
                      "upper-casing it sends a lowercase method ('post' instead of "
                      "'POST'); the request method-case behaviour the F2P tests "
                      "exercise (e.g. uppercase-scheme redirect handling and the "
                      "method carried into the prepared request) would diverge from "
                      "gold, so this faithful impl would NOT resolve.",
        "rationale": "REJECT from C0 (content): the spec pins "
                     "`result.chars = method.chars.map Char.toUpper` but the rival "
                     "emits `result.chars = method.chars`, which differ whenever the "
                     "input has a lowercase code point. Refuted at chars := ['a'] "
                     "(a lowercase input), width held at false so only C0 is at "
                     "issue.",
        "witness": _w("['a']", "false"),
    },

    # ---- off-by-one: skip the first code point's upper-casing (attacks C0) ----
    {
        "id": "skip-first-upper",
        "kind": "uniqueness",
        "expect": "reject",
        # Upper-case every code point EXCEPT the first (leave chars[0] raw). Would
        # verify on inputs whose first code point is not lowercase, but the content
        # clause must reject it for a lowercase-leading input.
        "module": _swap(
            _BASE, _I_CHARS,
            "  m := { m with chars := match m.chars with\n"
            "                | [] => []\n"
            "                | c :: cs => c :: cs.map Char.toUpper }\n"),
        "refinement": "a real patch that case-normalised all but the FIRST code "
                      "point of the method ('pOST' from 'post') sends a malformed "
                      "method; the carried request method would be wrong on "
                      "lowercase-leading method names, diverging from gold on the "
                      "F2P method-case behaviour, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C0 (content): the spec pins "
                     "`result.chars = method.chars.map Char.toUpper` but the rival "
                     "leaves the first code point raw, so for a lowercase-leading "
                     "input `result.chars[0] = method.chars[0] ≠ "
                     "Char.toUpper method.chars[0]`. Refuted at chars := ['a','b'] "
                     "(a distinct two-element point exercising the un-mapped head), "
                     "width held at false so only C0 is at issue.",
        "witness": _w("['a', 'b']", "false"),
    },

    # ---- AUDIT ADDITION: LENGTH divergence (attacks C0's shape, not its
    # per-position content) ----
    # The nagini sibling pins the length as its OWN clause
    # (`len(Result().chars) == len(chars)`) alongside the content clause. This
    # port folds both into the single equation C0 and asserts, in its coverage
    # note, that C0 pins "every code point at the same position" — but no case in
    # the original battery ever emits a result of the WRONG LENGTH. Both content
    # rivals (identity-no-upper, skip-first-upper) are length-preserving, so the
    # claim that C0 also subsumes the sibling's length clause was argued and
    # never demonstrated. This rival demonstrates it: it upper-cases every code
    # point correctly and forces the native flavour — so it satisfies the
    # per-position content pin at every position the input HAS, and satisfies C1
    # outright — and diverges only by appending one extra code point. It must be
    # rejected, and the only clause that can reject it is C0 read as a full list
    # equality.
    {
        "id": "pad-extra-codepoint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_CHARS,
            "  m := { m with chars := m.chars.map Char.toUpper ++ ['X'] }\n"),
        "refinement": "a real patch that appended a stray code point to the "
                      "normalized method name would send a method token that is not "
                      "any of the HTTP verbs ('GETX' for 'get'); the method carried "
                      "into the assembled request would be wrong on EVERY input, so "
                      "the F2P method-case behaviour diverges from gold and the "
                      "faithful patch would NOT resolve. Note this rival is correct "
                      "on the flavour clause and correct per-position on the content "
                      "clause, so it is rejected purely by the LENGTH consequence of "
                      "C0 — the sibling's separate length pin.",
        "rationale": "REJECT from C0 (content), specifically its LENGTH consequence: "
                     "the spec pins `result.chars = method.chars.map Char.toUpper`, "
                     "a full LIST equality, but the rival emits that list with one "
                     "extra code point appended, so the two lists differ in length "
                     "for every input. This is the port's demonstration that the "
                     "single equation C0 subsumes the nagini sibling's separate "
                     "`len(Result().chars) == len(chars)` clause — the other two "
                     "content rivals are both length-preserving, so without this "
                     "case that subsumption was argued and never exercised. Refuted "
                     "at chars := ['g','e','t'] (a third distinct input, and the "
                     "first multi-character F2P-shaped method token in the battery), "
                     "width held at false so only C0 is at issue.",
        "witness": _w("['g', 'e', 't']", "false"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 3 content/flavour rivals,
# 1 documented N/A note) plus a 4-case AXIOM lane. This bundle models the SAME
# single purely-functional core (normalize the method name to upper-cased native
# form) and re-expresses every sibling case that has a counterpart on this
# carrier; the frame-mutation class is genuinely vacuous here and the axiom lane
# is dropped. Every sibling case is recorded below.
#
#   sibling case                     -> here
#   -----------------------------------------------------------------------
#   pos-control-literal-native       -> pos-struct-literal        RE-EXPRESSED
#   pos-control-inline-elem          -> pos-field-reorder         RE-EXPRESSED
#   admiss-f2p-shaped                -> admiss-f2p-shaped         RE-EXPRESSED
#   flavour-echo-supplied            -> wide-echo                 PORTED (attacks C1)
#   partial-identity-no-upper        -> identity-no-upper         PORTED (attacks C0)
#   partial-skip-first-upper         -> skip-first-upper          PORTED (attacks C0)
#   frame-mutate-input-inplace       -> (none)                    VACUOUS
#   frame-append-input               -> (none)                    VACUOUS
#   control-flow-effect N/A note     -> (none)                    N/A (same as nagini)
#   AXIOM_TESTS (4)                  -> (none)                    DROPPED (G-AX)
#   Ensures len(Result().chars) ==
#     len(chars)  (sibling clause)   -> pad-extra-codepoint       AUDIT ADDITION
#   (no sibling counterpart)         -> pos-string-roundtrip      AUDIT ADDITION
#   (no sibling counterpart)         -> pos-guarded-upper         AUDIT ADDITION
#
# AUDIT ADDITIONS (3). An independent audit re-derived every witness and probed
# the spec with six NEW wrong impls and three NEW correct reshapes. The spec held
# on all nine (no SPEC-TOO-WEAK, no SPEC-TOO-STRONG), but two gaps in the BATTERY
# were found and are now closed:
#   * Both original positives are DEFINITIONALLY the frozen result, so the frozen
#     tactic body closes them unchanged. They vary the SPELLING of the frozen
#     computation, not the computation, and so could not have detected a spec that
#     pinned one particular derivation of the content. pos-string-roundtrip (via
#     `String.toUpper`/`String.map_eq`) and pos-guarded-upper (via a guarded
#     per-char fold reconciled through the `Char.isLower`/`Char.toUpper` numeric
#     ranges) each need a REAL re-proof of the byte-identical statement, and both
#     verify.
#   * All three original rivals are length-PRESERVING, so the claim that the
#     single equation C0 subsumes the sibling's separate length clause was argued
#     and never exercised. pad-extra-codepoint is the demonstration.
#
# RE-EXPRESSED (pos-struct-literal): the sibling's cheapest correct impl passes
#   the literal True for the flavour instead of routing through the to_native
#   axiom, keeping the verified backward fold for content. This carrier has no
#   axiom to route around (native coercion is modeled deeply), so the analogous
#   "structurally different but correct" reshape drops the imperative scaffold and
#   builds the result as one structure literal. Definitionally the frozen body, so
#   the frozen proof still closes (verified with a real build).
# RE-EXPRESSED (pos-field-reorder): the sibling's second positive is a local-shape
#   reshape of the same correct computation (inline the element, drop the
#   intermediate). Here the analogous local reshape swaps the order of the two
#   independent field updates — same result, different write order.
# RE-EXPRESSED (admiss-f2p-shaped): the sibling reads the half-permission input
#   under the precondition to witness a normal input is in-domain. This carrier's
#   theorem carries no precondition, so the honest analogue discharges the
#   POSTCONDITION at the smallest F2P-shaped input (a lowercase method supplied as
#   a wide string) as a `have`, proving the modeled behavior is satisfiable at a
#   normal input, then closes the frozen obligation verbatim.
# VACUOUS (frame-mutate-input-inplace, frame-append-input): the sibling holds
#   `chars` at Acc(list_pred(chars), 1/2) and these rivals reject from the Viper
#   permission system (writing/appending a half-permission input is insufficient
#   permission). This Lean carrier is referentially transparent — `method` is an
#   immutable value, there is no `mut` input binder, no aliasing, no read-only heap
#   cell to overwrite — so the entire permission-mutation class collapses. There is
#   nothing to reject and no witness could refute a rival that does not exist. No
#   substitute probe is fabricated.
# N/A (control-flow-effect): the sibling documents this class as N/A (no observable
#   raise / side-effect channel beyond the value abstraction). Same here.
# DROPPED (AXIOM_TESTS): the sibling's 4 axiom probes (to_native soundness +
#   containment, upper_seq soundness + containment) belong to the G-AX lane. This
#   bundle declares no `opaque` callee and consumes no `axiom` (both operations
#   modeled deeply — see mapping.md), so there is nothing to probe and the G-PBT
#   gate ignores AXIOM_TESTS regardless.
#
# COVERAGE. The spec has ONE input binder `method : PyStr` with two load-bearing
# FIELDS and two top-level clauses:
#   C0 content:  result.chars = method.chars.map Char.toUpper
#   C1 flavour:  result.wide = false
# Both clauses are DEFENDED (four positives + admiss verify) and ATTACKED (C1 by
# wide-echo; C0 by identity-no-upper, skip-first-upper and pad-extra-codepoint).
# Both fields of the binder are varied across the four reject witnesses:
#   method                                 rival                 clause
#     { chars := ['a'],         wide := true  }  wide-echo            C1
#     { chars := ['a'],         wide := false }  identity-no-upper    C0 content
#     { chars := ['a','b'],     wide := false }  skip-first-upper     C0 position
#     { chars := ['g','e','t'], wide := false }  pad-extra-codepoint  C0 length
#   method.wide ∈ {true, false} (wide-echo's refutation depends on wide=true; the
#   content rivals hold wide=false so their only divergence is C0), and
#   method.chars ∈ {['a'], ['a','b'], ['g','e','t']}. The four reject witnesses
#   probe four DISTINCT inputs (pts=4), so no field of the binder is pinned across
#   all rivals, and the three C0 rivals attack three DIFFERENT consequences of the
#   one equation (whether the map is applied at all; whether it is applied at
#   every position; whether the emitted list has the right length) rather than
#   three spellings of one point.
#
# The DEFENDING side is likewise varied by construction, not by spelling: two of
# the four positives (pos-field-reorder, pos-struct-literal) are definitionally
# the frozen result and reuse the frozen tactic body, while two
# (pos-string-roundtrip, pos-guarded-upper) compute the content through a
# different term and must RE-PROVE the byte-identical obligation. A spec that
# accepted only the frozen derivation would pass the first pair and fail the
# second.
AXIOM_TESTS = []
