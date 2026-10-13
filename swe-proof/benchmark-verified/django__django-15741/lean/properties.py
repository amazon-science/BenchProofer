"""properties.py — G-PBT falsification battery for django__django-15741 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_localizedFormat`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts ONE function over a heap carrier with fractional permissions
(``lookup_format(requested_name)`` returning ``List[int]``, with a per-code-point
copy loop and the ``resolve``/``format_value``/``do_lookup`` machinery). This
Lean bundle models the SAME single behavior, but at value level and stripped of
the loop: a (possibly deferred) format name is realized to its concrete name and
the localized format for that concrete name is resolved, for the active language.
The nagini per-code-point loop and its ``ToSeq(name)==take(i)`` prefix invariant
have no counterpart here — realization is a total value function ``realizeName``
— so the loop-shaped positive controls collapse to value reshapes and the
partial-domain "wrong key" rivals become value-level mis-realizations. The
downstream lookup ``lookupFormat`` is held ``opaque`` (nagini's opaque
``format_value``/``do_lookup``), so the "wrong key" rivals are refuted by
CONDITIONING on that opaque term rather than by computing it.

DEFENDED SURFACE (one modeled behavior; the postcondition is a single equation
with two independent input binders).
``problem_spec_localizedFormat name lang result`` pins EXACTLY:

    result = some (lookupFormat (realizeName name) lang)

which decomposes into three things a rival can get wrong:

  * (K key)   the lookup KEY is ``realizeName name`` — the FULL realized concrete
    name — for BOTH shapes of ``name``. A deferred name is realized just as a
    concrete one is (``realizeName`` is total: both constructors carry the
    underlying string through). This is the behavioural discriminator (the fix):
    pre-fix, a deferred name was NOT realized before the lookup and the routine
    failed to produce a format for it.
  * (L lang)  the SECOND argument to the lookup is the active language ``lang``;
  * (P produce) the result is ``some _`` — the routine ALWAYS produces a format,
    never ``none``.

WHERE THE LOAD-BEARING CLAUSE BITES. ``lookupFormat`` is ``opaque`` (only its
signature is known — no constraining axiom), so the postcondition can be
discharged ONLY by feeding it the argument pair the spec pins: the FULL realized
name and the active language. A rival that feeds it any other key (empty,
truncated, a differently-realized string) or any other language returns
``lookupFormat`` of a DIFFERENT argument, which is not provably equal to
``lookupFormat (realizeName name) lang`` — exactly nagini's "opaque
``format_value`` cannot be proven to agree on two distinct sequences" argument,
re-expressed as a value-level conditioning hypothesis. And a rival that fails to
realize a deferred name (the pre-fix bug) produces ``none``, refuted directly.

BINDER STRUCTURE. The spec predicate has TWO input binders:
  * ``name : FmtName`` — ranges over ``concrete s`` and ``deferred s``;
  * ``lang : String`` — the active language.
The reject witnesses probe BOTH constructors of ``name`` and TWO values of
``lang`` (``"en"`` and ``"de"``), and — after the audit additions — EVERY cell of
the (clause x constructor) grid, which is the coverage unit that matters here
since the spec is one equation quantified over both binders:

    clause \\ constructor   concrete                    deferred
    (K) key                 weak-empty-key,             weak-deferred-wrong-key
                            weak-drop-last,
                            weak-skip-first
    (L) language            weak-wrong-lang,            weak-deferred-wrong-lang
                            weak-lang-conditional         (AUDIT)
    (P) produce             weak-concrete-skip (AUDIT)  weak-deferred-skip

The two AUDIT-added cells matter because each is invisible to a probe that fixes
the OTHER coordinate: ``weak-deferred-wrong-lang`` is correct on every concrete
name (so no amount of varying ``lang`` at a concrete name finds it) and
``weak-concrete-skip`` is correct on every deferred name (so the deferred-shape
probes miss it). So no binder is held fixed across the reject lane, no rival is
refutable only at the default language or only at one constructor, and no clause
is probed at only one constructor.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds
    ``requested_name`` at ``Acc(...,1/2)`` (read-only) and ships two rivals
    (``frame-mut-append``, ``frame-mut-store``) that WRITE it and must fail for
    insufficient permission. On this referentially transparent carrier there is
    no heap, no aliasing, no fractional permission and no ``mut`` input binder:
    ``name`` is an immutable value. Both frame-mutation rivals are inexpressible,
    so this class is vacuous. No substitute probe is fabricated (porting map).

  * UNGROUNDED-ORACLE ECHO — degenerates into the "wrong key" attacks, exactly as
    the nagini docstring states. ``lookupFormat`` is opaque, but in the
    postcondition it is applied to ``realizeName name`` (GROUNDED in the input),
    so there is no free oracle value to echo: an impl cannot return
    ``lookupFormat <cheaper key>`` and have it provably equal
    ``lookupFormat (realizeName name) lang`` unless the key is provably the full
    realized name. So the class is covered by ``weak-empty-key`` /
    ``weak-drop-last`` / ``weak-skip-first`` (all feed a key ≠ ``realizeName
    name``) rather than by a distinct rival.

  * DIVERGENCE / NON-TERMINATION — EXPRESSIBLE AND REJECTED, but NOT WITNESSABLE;
    recorded as a known battery limitation, NOT as a vacuous class (audit
    correction — the earlier text here claimed "a diverging implementation cannot
    be written at all", which is false and was measured false). The bundle sets no
    ``loom.semantics.termination`` option, so this is plain Lean under TOTAL
    semantics. A diverging rival IS writable: replacing the impl region with a
    ``partial def`` whose body is a self-call with no decreasing measure
    (``spin n l := spin n l``) passes ``variant_scope`` with zero problems and is
    genuinely REJECTED (measured exit 1: the frozen ``rfl`` cannot close
    ``problem_spec … (implementation_localizedFormat name lang)`` because the
    ``partial`` body does not reduce). So under the brief's rule the case would
    belong in the reject lane. It is NOT shipped because no ADMISSIBLE witness
    exists for it on this carrier, and that was measured rather than assumed:
      - a witness stated over the divergent helper (``… .spin (.concrete "H:i")
        "en" ≠ …``) holds of the rival (exit 0) but fails on gold with
        ``Unknown constant `implementation_localizedFormat.spin``` (exit 1) — a
        rival-only name, so exactly the SYNTACTIC gold-side failure that makes a
        case hollow (``witness_scope_problems`` exists to catch this);
      - a witness stated only over the frozen vocabulary (``¬ problem_spec …`` at
        a ground input, closed by ``simp [implementation_localizedFormat]``)
        cannot be proven of the RIVAL either (exit 1, goal left as
        ``¬ implementation_localizedFormat.spin (.concrete "H:i") "en" = some …``):
        a ``partial def`` has no equation lemma to reduce, so nothing can decide
        it. Both halves of the discrimination check are therefore unreachable at
        once.
    This is a limitation of the witness mechanism on a non-reducing impl, not a
    spec hole: the diverging rival does NOT verify, so the spec is not too weak
    here. Contrast velvet's ``partial`` semantics, where such an impl verifies
    VACUOUSLY (``the corpus-wide termination-semantics finding``) — there the disposition is a real
    spec hole.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Every ported nagini rival is a
    partial-domain mis-realization: skip realization of the deferred shape
    (``none``); realize to the empty key, to the name minus its last character, or
    minus its first; or key the lookup on the wrong language.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``intro name lang; rfl`` proof is tuned
to the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at ONE concrete input. The deferred-skip witness closes by
``simp`` (``none ≠ some _`` on a ground input, no hypothesis). The "wrong key" /
"wrong lang" witnesses CONDITION on the opaque ``lookupFormat``: each assumes a
SINGLE inequality between the rival's lookup argument and the spec's (e.g.
``lookupFormat "" "en" ≠ lookupFormat "H:i" "en"``) — the exact sub-domain where
the rival is wrong — then derives the contradiction via ``Option.some.inj``. One
hypothesis per witness, about two distinct opaque applications, so the
assumptions are jointly satisfiable (never a contradictory pair about the same
term). Each was checked with two real ``lake env lean`` builds to HOLD of its
rival and to FAIL on the frozen solution, so it discriminates rather than
asserting a tautology.

WITNESS FAILURE REASON ON GOLD (audit requirement). "Fails on gold" is only
evidence if it fails SEMANTICALLY. Every witness here unfolds ONLY names the
frozen solution itself declares, so on gold the spec's equation reduces to
``True`` (gold satisfies the spec at that input) and the negation is then
unprovable — the reported error is an unsolved ``False`` / a mismatch against
the reduced ``True``, never a missing identifier. This was re-derived by
rebuilding each witness against a differently-SPELLED but equally wrong rival:
every witness still holds there, so none of them is keyed to its rival's
syntax. See the AUDIT NOTE on ``_w_none`` for the one scaffold where this was
NOT true and had to be repaired.

SOUNDNESS-LANE STRENGTH (audit correction). The two ported positives are both
closed by a DEFINITIONAL step — ``pos-control-explicit-val`` keeps the frozen
``rfl`` verbatim (its ``let`` is transparent) and ``pos-control-match`` needs only
a ``cases`` split before ``rfl``. Neither can therefore show the spec accepts a
route that is merely propositionally equal to the frozen one, which is the claim
"the spec pins the RESULT, not the route" actually needs.
``pos-control-propositional-key`` (AUDIT-ADDED) supplies it: its key is
``realizeName name ++ ""``, equal to the frozen key by a THEOREM rather than by
reduction, so the frozen ``rfl`` provably fails on it (measured exit 1) and the
case must re-prove by ``simp`` (measured exit 0).

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
patch that resolves the name to the wrong string (or fails to resolve a deferred
name, or keys on the wrong language), so the localized format the F2P tests key
on (the lazy-name render and the lazy-format lookup) diverges from what the tests
assert — so the faithful patch would NOT resolve.

AUDIT PROBES that are NOT shipped as cases (recorded so the coverage claim is
falsifiable rather than asserted). WRONG impls built, all REJECTED (exit 1), none
a spec hole: swap the lookup's two arguments; upper-case the realized key;
upper-case the LANGUAGE; return ``none`` unconditionally; return ``none`` only for
the empty realized key; realize the deferred shape to the empty key; realize the
deferred shape to a fixed plausible name; mangle the key at the CONCRETE
constructor only (the mirror of ``weak-deferred-wrong-key``); plus the four probes
that became ``weak-deferred-wrong-key`` / ``weak-lang-conditional`` /
``weak-deferred-wrong-lang`` / ``weak-concrete-skip``. CORRECT reshapes built, all
VERIFIED (exit 0), so the spec is not too strong on this carrier: use the
directly-usable name when available and realize only otherwise (``match directName
name with | some key => … | none => … realizeName …``) — the honest "handle both
shapes" route, and the spec accepts it; the same via ``(directName name).getD
(realizeName name)``; locally re-bind the input to ``FmtName.concrete (realizeName
name)`` before use; branch on a tautological condition (``if key = key then …``);
round-trip the key through its character list (``String.mk (realizeName
name).toList``, and again through ``.reverse.reverse``). The two that need ``simp``
rather than the frozen ``rfl`` are the informative ones — see
``pos-control-propositional-key``, which ships that shape as a case: on this
backend "did not verify" is frequently mere tactic breakage, which is precisely
why every reject case carries a witness.

AXIOM lane: DROPPED. The bundle declares ``opaque lookupFormat`` but consumes NO
``axiom`` (the proof is a definitional ``rfl`` over ``realizeName`` — see
mapping.md: no ``axiom lookupFormat_prop`` is declared). The axiom lane is G-AX's
job; the nagini ``AXIOM_TESTS`` are dropped (porting map).
"""
from pathlib import Path

INSTANCE = "django__django-15741"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# region anchors (each unique inside Solution.lean; verified at load)
# ---------------------------------------------------------------------------

# The WHOLE impl body (everything strictly inside `-- impl-start`/`-- impl-end`,
# after the `Id.run do` header). Swapping it lands entirely inside the impl
# region, so the spec view and the theorem STATEMENT are untouched.
_IMPL_BODY = (
    "  let key := realizeName name\n"
    "  return some (lookupFormat key lang)"
)

# The frozen proof body (proof region) — unique in the file.
_PROOF_BODY = (
    "  intro name lang\n"
    "  rfl"
)

assert _IMPL_BODY in _BASE and _BASE.count(_IMPL_BODY) == 1
assert _PROOF_BODY in _BASE and _BASE.count(_PROOF_BODY) == 1


def _impl(new_body: str) -> str:
    """Replace ONLY the impl body (rival keeps the frozen proof body, which then
    fails to close for the reshaped impl — the case rejects and its witness
    attributes the rejection to the spec)."""
    return _swap(_BASE, _IMPL_BODY, new_body)


def _reproved(new_impl: str, new_proof: str) -> str:
    """Replace the impl body AND the proof body (positive controls that re-prove
    for the reshaped impl). The theorem STATEMENT is untouched."""
    return _swap(_swap(_BASE, _IMPL_BODY, new_impl), _PROOF_BODY, new_proof)


# ---------------------------------------------------------------------------
# witness scaffolds
# ---------------------------------------------------------------------------
def _w_none(name_lit: str, lang_lit: str) -> str:
    """Refute a rival that returns `none` at a concrete ground input: the spec
    pins `some _`, and `none ≠ some _` closes by `simp` (no hypothesis).

    AUDIT NOTE (why `directName` is a `simp` LEMMA here and not an `unfold`
    TARGET). An earlier form of this scaffold opened with
    ``unfold problem_spec_localizedFormat implementation_localizedFormat
    directName``. That discriminated for the WRONG reason: `directName` occurs in
    the rival's impl region but NOT in the frozen solution, so the gold-side
    build failed with ``Tactic `unfold` failed to unfold `directName```. That is a
    SYNTACTIC failure (a name the frozen impl does not mention), not the semantic
    report "gold satisfies the spec here", and the gate reads either as
    discrimination. Measured: an equally WRONG rival with the same observable
    behaviour (`none` on a deferred name) written WITHOUT `directName` — a bare
    ``match name with | .concrete s => … | .deferred _ => return none`` — also
    FAILED this witness (exit 1, the same unfold error), so the witness was
    tracking the rival's spelling rather than its behaviour. Passing `directName`
    as a simp lemma instead is a no-op where it does not apply: the witness now
    holds of that alternative wrong impl (exit 0) and gold fails with
    ``unsolved goals ⊢ False`` — simp reduces gold's equation to `True` because
    gold really does satisfy the spec at this input, leaving the negation
    unprovable. Semantic on both sides.
    """
    return (
        f"example : ¬ problem_spec_localizedFormat {name_lit} {lang_lit}\n"
        f"    (implementation_localizedFormat {name_lit} {lang_lit}) := by\n"
        "  unfold problem_spec_localizedFormat implementation_localizedFormat\n"
        "  simp [directName]\n"
    )


def _w_none_plain(name_lit: str, lang_lit: str) -> str:
    """As `_w_none`, but for a rival that produces `none` WITHOUT going through
    `directName` (it matches on the constructor directly). Nothing outside the
    frozen vocabulary is named at all, so the gold-side failure cannot be a
    missing identifier even in principle: measured gold error is
    ``unsolved goals ⊢ False`` (simp reduces gold's equation to `True`)."""
    return (
        f"example : ¬ problem_spec_localizedFormat {name_lit} {lang_lit}\n"
        f"    (implementation_localizedFormat {name_lit} {lang_lit}) := by\n"
        "  unfold problem_spec_localizedFormat implementation_localizedFormat\n"
        "  simp\n"
    )


def _w_key(name_lit: str, lang_lit: str, rival_arg: str, spec_arg: str,
           extra_simp: str = "") -> str:
    """Refute a rival whose lookup argument differs from the spec's, by
    CONDITIONING on the opaque `lookupFormat`: assume the single inequality
    `lookupFormat <rival_arg> ≠ lookupFormat <spec_arg>` (the sub-domain where the
    rival is wrong) and derive the contradiction via `Option.some.inj`. `rival_arg`
    / `spec_arg` are the full ` <key> <lang>` argument pairs each side feeds.
    `extra_simp` adds simp lemmas a particular rival's impl shape needs to reduce
    (e.g. `reduceIte` for a rival that branches on `lang`).

    Only names the FROZEN solution also declares are unfolded (`realizeName`,
    the spec and impl constants), so the gold-side build fails because gold's
    equation collapses to `True` — there is nothing left to refute — and not
    because a name is missing. Checked by porting each witness to a
    differently-SHAPED but equally wrong rival: it still holds (exit 0), so it
    discriminates on behaviour rather than spelling."""
    return (
        f"example (h : lookupFormat {rival_arg} ≠ lookupFormat {spec_arg}) :\n"
        f"    ¬ problem_spec_localizedFormat {name_lit} {lang_lit}\n"
        f"      (implementation_localizedFormat {name_lit} {lang_lit}) := by\n"
        "  unfold problem_spec_localizedFormat implementation_localizedFormat\n"
        f"  simp only [realizeName, Id.run, pure{extra_simp}]\n"
        "  intro heq\n"
        "  exact h (Option.some.inj heq)\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_localizedFormat` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-control-match",
        "kind": "soundness",
        "expect": "verify",
        # CORRECT impl reshaped: match on the name's shape and realize each branch
        # in place, instead of calling `realizeName` and then looking up. Both
        # branches feed the SAME full realized name to the lookup, so the behavior
        # is identical; only the control-flow shape differs. Re-proved by
        # `cases name <;> rfl` (each branch is definitionally the spec's equation).
        # Statement byte-identical; no new axiom/lemma. (Verified: real build.)
        # Ports nagini's pos-control-localbound (a pure control-flow reshape that
        # keeps the same forward realization and every framing assertion).
        "module": _reproved(
            "  match name with\n"
            "  | .concrete s => return some (lookupFormat s lang)\n"
            "  | .deferred s => return some (lookupFormat s lang)",
            "  intro name lang\n"
            "  cases name <;> rfl",
        ),
        "rationale": "structurally-different CORRECT impl: match on the name's shape "
                     "and realize each branch in place (both branches feed the FULL "
                     "realized name to the lookup — same behavior, different control "
                     "flow). Must verify else SPEC-TOO-STRONG. Re-proved for the "
                     "reshaped body by `cases name <;> rfl`; statement byte-identical, "
                     "no new axiom/lemma. Ports nagini's pos-control-localbound.",
    },
    {
        "id": "pos-control-explicit-val",
        "kind": "soundness",
        "expect": "verify",
        # CORRECT impl: bind the looked-up value to an intermediate local `val`
        # before returning it — a pure let-inlining that adds a temporary but
        # changes no value. The frozen proof body (`rfl`) still closes because the
        # binding is definitionally transparent. Statement byte-identical; no new
        # axiom/lemma. (Verified: real build.) Ports nagini's
        # pos-control-extra-assert (a different proof shape that ADDS, not removes,
        # a step while keeping the same behavior).
        "module": _impl(
            "  let key := realizeName name\n"
            "  let val := lookupFormat key lang\n"
            "  return some val"
        ),
        "rationale": "CORRECT impl with an intermediate `let val := lookupFormat key "
                     "lang` before the return — a definitionally-transparent "
                     "let-inlining that changes no value. The frozen `rfl` still "
                     "closes. Must verify else SPEC-TOO-STRONG. Statement "
                     "byte-identical, no new axiom/lemma. Ports nagini's "
                     "pos-control-extra-assert.",
    },

    {
        "id": "pos-control-propositional-key",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT-ADDED (attack E). The two ported positives are both closed by a
        # DEFINITIONAL step: `pos-control-explicit-val` keeps the frozen `rfl`
        # verbatim, and `pos-control-match` needs only a `cases` split before
        # `rfl`. So the shipped soundness lane only ever established that the
        # spec tolerates reshapes that reduce definitionally to the frozen body
        # — a much weaker claim than "the spec pins the RESULT, not the route".
        # This positive builds the key so that it is only PROPOSITIONALLY equal
        # to `realizeName name` (`s ++ "" = s` is a theorem, not a reduction),
        # so the frozen `rfl` genuinely cannot close it and the case must
        # re-prove by `simp`. Measured both ways: exit 0 with the `simp` body,
        # exit 1 under the frozen `rfl` body (`Tactic 'rfl' failed`) — so this is
        # the first positive whose acceptance is not a restatement of gold.
        "module": _reproved(
            '  let key := realizeName name ++ ""\n'
            "  return some (lookupFormat key lang)",
            "  intro name lang\n"
            "  simp [problem_spec_localizedFormat, implementation_localizedFormat]",
        ),
        "rationale": "CORRECT impl whose key is only PROPOSITIONALLY (not "
                     "definitionally) the realized name: `realizeName name ++ \"\"`. "
                     "The behavior is identical on every input, but the frozen `rfl` "
                     "cannot close it (measured: exit 1 under the frozen proof body), so "
                     "the case re-proves by `simp`. Must verify else SPEC-TOO-STRONG. "
                     "This is the soundness probe the two ported positives do NOT give: "
                     "both of those reduce definitionally to the frozen body (one keeps "
                     "`rfl` verbatim, the other needs only a `cases` split), so they "
                     "cannot show the spec accepts a route that is merely equal rather "
                     "than reducible. Statement byte-identical; no new axiom/lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at
    # normal, F2P-shaped inputs. The frozen theorem carries NO precondition (the
    # spec is total over `FmtName × String`), so the nagini precondition-admission
    # witness re-expresses as: discharge the spec predicate by evaluation at the
    # two F2P-shaped inputs (a DEFERRED/lazy name, and an already-concrete name) as
    # ground `have`s prepended to the frozen tactic body, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, ground instances are `have`s in the existing tactic body.
    # (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            '  have _lazy : problem_spec_localizedFormat (.deferred "DATE_FORMAT") "en"\n'
            '      (implementation_localizedFormat (.deferred "DATE_FORMAT") "en") := by\n'
            "    unfold problem_spec_localizedFormat implementation_localizedFormat\n"
            "    rfl\n"
            '  have _concrete : problem_spec_localizedFormat (.concrete "H:i") "en"\n'
            '      (implementation_localizedFormat (.concrete "H:i") "en") := by\n'
            "    unfold problem_spec_localizedFormat implementation_localizedFormat\n"
            "    rfl\n"
            "  intro name lang\n"
            "  rfl"),
        "rationale": "the obligation is discharged at the two F2P-shaped inputs (a "
                     "DEFERRED/lazy name and an already-concrete name — the shapes the "
                     "lazy-name F2P tests key on) by evaluation as ground `have`s, then "
                     "the frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior would be unsatisfiable at exactly a normal F2P "
                     "input — the analogue of PRECOND-TOO-STRONG). Nothing is assumed: "
                     "no new declaration, statement byte-identical, ground instances "
                     "are `have`s in the existing tactic body. Ports nagini's "
                     "admiss-f2p-shaped-input (which built a concrete deferred "
                     "FormatType and asserted it satisfies the function's Requires).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- THE bug-delta: fail to realize a deferred name (attacks K/P) ----
    {
        "id": "weak-deferred-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-patch skeleton: use the directly-usable concrete name,
        # which exists ONLY for an already-concrete name — a DEFERRED name yields
        # `none`. Correct on every concrete name; produces `none` (fails to resolve)
        # on a deferred name.
        "module": _impl(
            "  match directName name with\n"
            "  | some key => return some (lookupFormat key lang)\n"
            "  | none     => return none"
        ),
        "refinement": "this IS the pre-patch behaviour: the name is used for the "
                      "lookup only when it already arrives concrete; a DEFERRED (lazy) "
                      "name is never realized and the routine produces no format for "
                      "it. In the real routine that is the un-patched path where the "
                      "lazy proxy reaches the downstream lookup unrealized and the call "
                      "fails. Its faithful real patch (realize only the already-concrete "
                      "shape) is precisely what does NOT resolve the F2P tests keyed on "
                      "a lazy name.",
        "rationale": "REJECT from clauses (K)+(P): the spec pins `result = some "
                     "(lookupFormat (realizeName name) lang)`, but for a deferred name "
                     "the rival returns `none`, and `none ≠ some _`. Refuted at a "
                     "deferred name — the constructor no other reject witness holds — "
                     "so the deferred shape is exercised.",
        "witness": _w_none('(.deferred "H:i")', '"en"'),
    },

    # ---- realize to the EMPTY key (attacks K; ports uniq-empty-key) ----
    {
        "id": "weak-empty-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the name entirely and look up the empty key. do_lookup of the empty
        # key is not provably equal to do_lookup of the realized name.
        "module": _impl('  return some (lookupFormat "" lang)'),
        "refinement": "feeding the lookup an empty key corresponds to a patch that "
                      "passed an unresolved/empty name to the downstream lookup — the "
                      "failure family the bug is about (the lazy name never reaches the "
                      "lookup as its real characters). The looked-up value for the "
                      "empty key differs from the value for the real name, so the F2P "
                      "assertions on the full-name value fail; the faithful patch does "
                      "NOT resolve.",
        "rationale": "REJECT from clause (K): the spec pins the key to `realizeName "
                     "name`, but the rival feeds `\"\"`. Under the opaque `lookupFormat` "
                     "the two are not provably equal — witnessed by conditioning on "
                     "`lookupFormat \"\" \"en\" ≠ lookupFormat \"H:i\" \"en\"`. Refuted at "
                     "a concrete name.",
        "witness": _w_key('(.concrete "H:i")', '"en"', '"" "en"', '"H:i" "en"'),
    },

    # ---- realize to the name minus its LAST char (attacks K; ports uniq-drop-last) ----
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Truncate the realized name by one character on the right. name-minus-last
        # != name; the lookup keyed on the truncated name differs.
        "module": _impl(
            "  let key := (realizeName name).dropRight 1\n"
            "  return some (lookupFormat key lang)"
        ),
        "refinement": "truncating the last character corresponds to a patch that "
                      "resolved the name to the wrong string (a name missing its final "
                      "character). The downstream lookup keyed on the truncated name "
                      "returns a different value, so the F2P assertions on the full-name "
                      "value fail; a faithful such patch does NOT resolve.",
        "rationale": "REJECT from clause (K): the rival's key is `(realizeName "
                     "name).dropRight 1`, not `realizeName name`. Under the opaque "
                     "`lookupFormat` these are not provably equal — witnessed by "
                     "conditioning on `lookupFormat (\"DATE_FORMAT\".dropRight 1) \"en\" ≠ "
                     "lookupFormat \"DATE_FORMAT\" \"en\"`. Refuted at a concrete name.",
        "witness": _w_key(
            '(.concrete "DATE_FORMAT")', '"en"',
            '("DATE_FORMAT".dropRight 1) "en"', '"DATE_FORMAT" "en"'),
    },

    # ---- realize to the name minus its FIRST char (attacks K; ports uniq-skip-first) ----
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the FIRST character of the realized name — the opposite boundary from
        # drop-last. Supporting partial-domain near-miss; refuted at a different
        # (name, lang) point (lang = "de") so the language binder is also varied.
        "module": _impl(
            "  let key := (realizeName name).drop 1\n"
            "  return some (lookupFormat key lang)"
        ),
        "refinement": "dropping the FIRST character resolves the name to a different "
                      "string (its tail); the downstream lookup returns the wrong value "
                      "and the F2P assertions fail. Supporting partial-domain near-miss "
                      "on the opposite boundary from weak-drop-last; a faithful such "
                      "patch does NOT resolve.",
        "rationale": "REJECT from clause (K): the rival's key is `(realizeName "
                     "name).drop 1`, not `realizeName name`. Witnessed by conditioning "
                     "on `lookupFormat (\"DATE_FORMAT\".drop 1) \"de\" ≠ lookupFormat "
                     "\"DATE_FORMAT\" \"de\"`. Refuted at a concrete name under lang "
                     "\"de\" — a distinct input point (and a non-default language, so "
                     "the language binder is varied).",
        "witness": _w_key(
            '(.concrete "DATE_FORMAT")', '"de"',
            '("DATE_FORMAT".drop 1) "de"', '"DATE_FORMAT" "de"'),
    },

    # ---- key the lookup on the WRONG language (attacks L; added for the carrier) ----
    {
        "id": "weak-wrong-lang",
        "kind": "uniqueness",
        "expect": "reject",
        # Realize the name correctly but pass the WRONG language (the empty language)
        # to the lookup. This carrier's spec added `lang` as a second binder (the
        # nagini surface had no language argument); the (L) clause pins the lookup's
        # second argument to the active language. A rival that ignores it must
        # reject, else a wrong-locale resolution would verify. Refuted at a distinct
        # (name, lang) point.
        "module": _impl(
            "  let key := realizeName name\n"
            '  return some (lookupFormat key "")'
        ),
        "refinement": "keying the lookup on a fixed (empty) language instead of the "
                      "active one corresponds to a patch that resolved the format for "
                      "the wrong locale. The localized value differs across languages, "
                      "so the F2P assertions on the value for the active language fail; "
                      "a faithful such patch does NOT resolve.",
        "rationale": "REJECT from clause (L): the spec pins the lookup's second "
                     "argument to `lang`, but the rival passes `\"\"`. Under the opaque "
                     "`lookupFormat` these are not provably equal — witnessed by "
                     "conditioning on `lookupFormat \"H:i\" \"\" ≠ lookupFormat \"H:i\" "
                     "\"de\"`. Refuted at lang \"de\", so the language binder is varied "
                     "and the (L) clause — absent from the nagini surface — is "
                     "attacked on this carrier.",
        "witness": _w_key(
            '(.concrete "H:i")', '"de"',
            '"H:i" ""', '"H:i" "de"'),
    },

    # ---- realize the DEFERRED shape to a WRONG key (attacks K at the deferred
    # constructor; ADDED by audit) ----
    {
        "id": "weak-deferred-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. The ported reject lane attacked the deferred constructor
        # only through the (P) clause (`weak-deferred-skip` returns `none`, refuted
        # by `none ≠ some _` with no hypothesis) and attacked the (K) key clause
        # only at CONCRETE names. So the CROSS of the two — a rival that DOES
        # produce a format for a deferred name, and is correct on every concrete
        # name, but realizes the deferred shape to the wrong string — was
        # unattacked. That is the near-miss closest to a partial fix: it resolves
        # the deferred shape (so the `none` witness cannot see it) but resolves it
        # to a different name. Handles the concrete shape exactly as gold does, so
        # the rejection is attributable purely to the deferred key.
        "module": _reproved(
            "  match name with\n"
            "  | .concrete s => return some (lookupFormat s lang)\n"
            '  | .deferred s => return some (lookupFormat (s ++ "!") lang)',
            "  intro name lang\n"
            "  cases name <;> rfl",
        ),
        "refinement": "realizing a deferred name to a DIFFERENT string than the one "
                      "it denotes corresponds to a patch that does coerce the deferred "
                      "shape but coerces it wrongly — the downstream lookup is keyed on "
                      "a name the caller never asked for, so the format the tests assert "
                      "for a lazily-supplied name is not the format returned. The "
                      "concrete shape is handled exactly as gold does, so a faithful "
                      "such patch resolves nothing the concrete-name tests did not "
                      "already pass and still does NOT resolve the lazy-name F2P tests.",
        "rationale": "REJECT from clause (K) AT THE DEFERRED CONSTRUCTOR: the spec pins "
                     "the key to `realizeName name`, which for `deferred s` is `s`, but "
                     "the rival feeds `s ++ \"!\"`. Under the opaque `lookupFormat` the "
                     "two are not provably equal — witnessed by conditioning on "
                     "`lookupFormat (\"H:i\" ++ \"!\") \"en\" ≠ lookupFormat \"H:i\" "
                     "\"en\"`. This is the (K)x(deferred) cell no ported case covered: "
                     "`weak-deferred-skip` refutes the deferred shape via (P) only, and "
                     "every other key rival is refuted at a concrete name.",
        "witness": _w_key(
            '(.deferred "H:i")', '"en"',
            '("H:i" ++ "!") "en"', '"H:i" "en"'),
    },

    # ---- correct on the DEFAULT language, wrong on every other (attacks L
    # conditionally; ADDED by audit) ----
    {
        "id": "weak-lang-conditional",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. `weak-wrong-lang` ignores `lang` UNCONDITIONALLY, so it is
        # already wrong at the most-tested language. The sharper near-miss is a
        # rival that agrees with gold whenever the active language is the default
        # one and silently falls back to that default otherwise — the shape a
        # locale bug actually takes, and the one a battery that only ever
        # exercised the default language would miss. Rejected because the spec
        # pins the lookup's second argument to `lang` for EVERY language.
        "module": _impl(
            "  let key := realizeName name\n"
            '  if lang = "en" then return some (lookupFormat key lang)\n'
            '  else return some (lookupFormat key "en")'
        ),
        "refinement": "falling back to a fixed default language whenever the active "
                      "language is not that default corresponds to a patch that resolves "
                      "the format for the wrong locale on every non-default locale. The "
                      "localized value differs across languages, so the assertions on "
                      "the value for the active language fail under a non-default "
                      "locale; a faithful such patch does NOT resolve.",
        "rationale": "REJECT from clause (L), CONDITIONALLY: the rival is observably "
                     "identical to gold at lang \"en\" and wrong at every other "
                     "language, so it is refutable only at a non-default language — "
                     "witnessed by conditioning on `lookupFormat \"H:i\" \"en\" ≠ "
                     "lookupFormat \"H:i\" \"de\"` at lang \"de\". Sharper than "
                     "weak-wrong-lang, which is wrong at \"en\" too; this one survives "
                     "any probe that fixes the language at the default.",
        "witness": _w_key(
            '(.concrete "H:i")', '"de"',
            '"H:i" "en"', '"H:i" "de"',
            ", reduceIte, String.reduceEq"),
    },

    # ---- key the lookup on the wrong LANGUAGE only for the DEFERRED shape
    # (attacks L at the deferred constructor; ADDED by audit) ----
    {
        "id": "weak-deferred-wrong-lang",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. Fills the (L clause x deferred constructor) cell. Both
        # shipped (L) rivals — `weak-wrong-lang` and `weak-lang-conditional` —
        # ignore `lang` for EVERY name, so each is already refutable at a
        # concrete name and neither shows the language clause is enforced on the
        # deferred shape. This rival handles the concrete shape exactly as gold
        # does (same key, same language) and drops the active language ONLY when
        # the name arrives deferred: the shape a partial fix takes when the
        # newly-realized branch is resolved against a hardcoded locale instead of
        # the active one. It is therefore invisible to any probe that fixes the
        # constructor at `concrete`, however many languages that probe varies.
        "module": _reproved(
            "  match name with\n"
            "  | .concrete s => return some (lookupFormat s lang)\n"
            '  | .deferred s => return some (lookupFormat s "en")',
            "  intro name lang\n"
            "  cases name <;> rfl",
        ),
        "refinement": "resolving a deferred name against a fixed locale rather than the "
                      "active one corresponds to a patch that does realize the lazily "
                      "supplied name but then resolves its format for the wrong "
                      "language. The localized value differs across languages, so the "
                      "assertions on the value for the active language fail for exactly "
                      "the lazily-supplied names under a non-default locale — while every "
                      "concrete-name test still passes, since the concrete shape is "
                      "handled exactly as gold does. A faithful such patch does NOT "
                      "resolve.",
        "rationale": "REJECT from clause (L) AT THE DEFERRED CONSTRUCTOR: the spec pins "
                     "the lookup's second argument to `lang` for every shape of `name`, "
                     "but for `deferred s` the rival passes `\"en\"`. Under the opaque "
                     "`lookupFormat` these are not provably equal — witnessed by "
                     "conditioning on `lookupFormat \"H:i\" \"en\" ≠ lookupFormat \"H:i\" "
                     "\"de\"` at the point (deferred \"H:i\", \"de\"). This is the "
                     "(L)x(deferred) cell no other case covers: both other (L) rivals "
                     "ignore `lang` for every name and are refuted at a CONCRETE name.",
        "witness": _w_key(
            '(.deferred "H:i")', '"de"',
            '"H:i" "en"', '"H:i" "de"'),
    },

    # ---- fail to produce a format for an already-CONCRETE name (attacks P at
    # the concrete constructor; ADDED by audit) ----
    {
        "id": "weak-concrete-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT-ADDED. Fills the (P clause x concrete constructor) cell. The (P)
        # clause — the result is always `some _`, the routine never fails to
        # produce a format — was probed at the DEFERRED constructor only
        # (`weak-deferred-skip`). So a rival that resolves the deferred shape
        # correctly but stops producing a format for an already-concrete name
        # was unattacked: the regression direction of a fix that reroutes the
        # concrete path while adding the deferred one. Refuted at a fresh input
        # point (concrete "TIME_FORMAT", "de") — a literal no other case uses.
        "module": _reproved(
            "  match name with\n"
            "  | .concrete _ => return none\n"
            "  | .deferred s => return some (lookupFormat s lang)",
            "  intro name lang\n"
            "  cases name <;> rfl",
        ),
        "refinement": "ceasing to produce a format for a name that already arrives "
                      "concrete corresponds to a patch that routes the newly-handled "
                      "shape correctly but breaks the shape that always worked — the "
                      "regression direction. Every assertion keyed on a plainly-named "
                      "format then gets no format at all, so such a patch does NOT "
                      "resolve (it trades one failing family for another).",
        "rationale": "REJECT from clause (P) AT THE CONCRETE CONSTRUCTOR: the spec pins "
                     "`result = some _` for every shape of `name`, but for `concrete _` "
                     "the rival returns `none`, and `none ≠ some _` closes by `simp` with "
                     "no hypothesis. This is the (P)x(concrete) cell no other case "
                     "covers: `weak-deferred-skip` probes (P) at the DEFERRED constructor "
                     "only, and every other rival still returns `some _` everywhere. "
                     "Refuted at (concrete \"TIME_FORMAT\", \"de\") — a fresh input point.",
        "witness": _w_none_plain('(.concrete "TIME_FORMAT")', '"de"'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 uniqueness "wrong key"
# rivals) plus a 3-probe AXIOM lane. This bundle models the SAME single behavior
# at value level (no per-code-point loop), so:
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-localbound       -> pos-control-match          PORTED (re-proved)
#   pos-control-extra-assert     -> pos-control-explicit-val   RE-EXPRESSED
#   (none)                       -> pos-control-propositional-key
#                                                              ADDED by AUDIT (E:
#                                     the only positive not closed definitionally)
#   admiss-f2p-shaped-input      -> admiss-f2p-inputs          RE-EXPRESSED
#   uniq-deferred-skip           -> weak-deferred-skip         PORTED  (attacks K/P)
#   uniq-empty-key               -> weak-empty-key             PORTED  (attacks K)
#   uniq-drop-last               -> weak-drop-last             PORTED  (attacks K)
#   uniq-skip-first              -> weak-skip-first            PORTED  (attacks K)
#   (none)                       -> weak-wrong-lang            ADDED   (attacks L)
#   (none)                       -> weak-deferred-wrong-key    ADDED by AUDIT (K x deferred)
#   (none)                       -> weak-lang-conditional      ADDED by AUDIT (L, non-default only)
#   (none)                       -> weak-deferred-wrong-lang   ADDED by AUDIT (L x deferred)
#   (none)                       -> weak-concrete-skip         ADDED by AUDIT (P x concrete)
#   frame-mut-append             -> (none)                     VACUOUS (no heap)
#   frame-mut-store              -> (none)                     VACUOUS (no heap)
#   AXIOM_TESTS (3 probes)       -> (none)                     DROPPED (G-AX)
#
# VACUOUS (frame-mut-append, frame-mut-store): the sibling holds `requested_name`
#   at Acc(...,1/2) (read-only) and these two rivals WRITE it (append / index
#   store), which must fail for insufficient permission. This carrier is
#   referentially transparent: no heap, no aliasing, no fractional permission, no
#   `mut` input binder — `name` is an immutable value. A write-to-input rival is
#   inexpressible, so the class is vacuous. No substitute is fabricated.
# DROPPED (AXIOM_TESTS): the sibling probes the real callee (resolve==str(),
#   get_format keyed on the resolved name, do_lookup domain containment) in the
#   instance Docker image. That is the axiom lane's job (G-AX). This bundle
#   declares `opaque lookupFormat` but consumes NO axiom (the proof is a
#   definitional `rfl` over `realizeName`; mapping.md declares no
#   `lookupFormat_prop`), so this gate ignores AXIOM_TESTS regardless.
# DIVERGENCE — KNOWN BATTERY LIMITATION, not vacuous (audit correction; the
#   earlier note here claimed a diverging impl "cannot be written", which is false).
#   No `loom.semantics.termination` option is set, so total semantics apply. A
#   `partial def` self-call rival passes variant_scope and IS rejected (exit 1),
#   but it admits no ADMISSIBLE witness: stated over the divergent helper the
#   gold-side failure is `Unknown constant …spin` (a rival-only name — syntactic,
#   hollow), and stated only over frozen vocabulary it cannot be proven of the
#   rival either (a `partial def` has no equation lemma, so nothing reduces).
#   Both measured. Not a spec hole (the rival does not verify); see the ADVERSARIAL
#   READ block for the exact builds and exit codes.
#
# CARRIER NARROWING vs the nagini per-code-point loop. The nagini positives
#   (localbound / extra-assert) and rivals are phrased over a per-code-point copy
#   loop with a `ToSeq(name)==take(i)` prefix invariant; realization is a value
#   function `realizeName` here, so the loop-shaped positives collapse to value
#   reshapes (match-realize; intermediate `let`) and the "wrong key" rivals
#   (empty / drop-last / skip-first) become value-level `dropRight`/`drop`/`""`
#   mis-realizations. The ARGUMENT (opaque lookup of a key ≠ the realized name is
#   not provably equal to the lookup of the realized name) is carried over exactly;
#   the mechanics are value-level.
#
# POINT SPREAD. The nine reject witnesses probe these (name, lang) input points:
#     name                     lang    clause  case
#     deferred "H:i"           "en"    K/P     weak-deferred-skip
#     concrete "H:i"           "en"    K       weak-empty-key
#     concrete "DATE_FORMAT"   "en"    K       weak-drop-last
#     concrete "DATE_FORMAT"   "de"    K       weak-skip-first
#     concrete "H:i"           "de"    L       weak-wrong-lang
#     deferred "H:i"           "en"    K       weak-deferred-wrong-key   (AUDIT)
#     concrete "H:i"           "de"    L       weak-lang-conditional     (AUDIT)
#     deferred "H:i"           "de"    L       weak-deferred-wrong-lang  (AUDIT)
#     concrete "TIME_FORMAT"   "de"    P       weak-concrete-skip        (AUDIT)
#   The `name` binder takes BOTH constructors (concrete and deferred); the `lang`
#   binder takes "en" and "de"; three distinct name literals appear. Some
#   audit-added cases reuse existing POINTS on purpose — coverage of a
#   (clause x constructor) CELL, not of a fresh literal, is what they add. All six
#   cells of the 3-clause x 2-constructor grid are now occupied (see the grid in
#   the docstring). No binder is held fixed across the reject lane, no reject case
#   is refutable only at the default language or only at one constructor, and no
#   clause is probed at only one constructor.
#
# AXIOM lane: none consumed by the proof; the gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
