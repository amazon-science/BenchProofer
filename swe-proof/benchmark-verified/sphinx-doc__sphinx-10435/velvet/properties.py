"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10435 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — which the consumer spec view elides — is changed, plus
the ``prove_correct`` proof body where a reshape needs it, so ``markers.same_spec``
holds and the single ``prove_correct`` obligation survives) and swaps in a
candidate implementation; it is checked by the real verifier. ``expect:"verify"``
passes iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND
does NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method,
``wrapInlineCode (snippet : List Char) return (out : List Char)``, which renders
one inline code snippet through the syntax highlighter (the UNCHANGED opaque
callee ``renderedInline``) and wraps it in the inline-code LaTeX macro. There is
NO ``require`` clause: the domain is total over every ``snippet : List Char``.
The postcondition is a SINGLE master equality:

  (M) out = wrapped (renderedInline snippet)

where ``wrapped body = codeOpen ++ ['%', '\\n'] ++ body ++ ['%', '\\n', '}', '}']``.
So the observable is pinned exactly: the code-macro opening ``codeOpen``, then a
line-break-suppressing marker ``'%'``, then a newline, then the rendered body,
then a SECOND suppressor ``'%'``, then a newline and the closing ``'}}'``. The
two ``'%'`` markers are the load-bearing detail — they make the line breaks the
highlighter places around the body render as no spurious whitespace. ``snippet``
is a FREE input, but it is consumed ONLY under the opaque ``renderedInline``, so
the master equality's dependence on it is entirely mediated by that axiom (see
the BINDER-COVERAGE note in the footer).

CARRIER NOTE (why the witnesses are SEMANTIC, not tester-based). The sibling
velvet batteries drive a refutation through Velvet's executable tester
(``extract_program_for`` … ``derive_tester_for`` … ``decide``). That machinery
is UNAVAILABLE here: ``renderedInline`` is an ``axiom`` (``noncomputable``), so
``extract_program_for wrapInlineCode`` fails outright ("depends on declaration
'renderedInline', which has no executable code"). Every witness below is instead
a SEMANTIC refutation of the Hoare triple itself: it reduces
``triple True (wrapInlineCode L) (fun out => out = wrapped (renderedInline L))``
via the frozen ``Velvet.Std`` lemmas (``wp_bind`` / ``MonadNonDet.wp_pickSuchThat``
/ ``wp_pure`` / the ``loomLogicSimp`` Prop-lattice set), instantiates the demonic
choice at the highlighter's framed value, and shows the rival's output is NOT
``wrapped (renderedInline L)`` at that concrete point. No ``sorry`` / ``admit`` /
``native_decide`` / new ``axiom`` / ``opaque`` — the discrimination is genuine
(each rival build exits 0, each gold build exits 1). Two of these witnesses
were REWRITTEN during the audit: their reductions spelled the rival's opening
token literally, so against the frozen solution they died at a program-shape
`rw` before the claim was engaged, and the gold exit code carried no
information about what was claimed (a claim TRUE of gold failed with the
byte-identical error). They now quantify over the opening prefix; see
`_REDUCE_GENERIC`.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling MANDATES it
    because ``content`` is held at ``Acc(list_pred(content), 1/2)`` (read-only)
    and an impl that WRITES to it must be rejected for insufficient permission.
    Lean/Velvet is referentially transparent: ``snippet`` is an immutable value,
    there is no ``mut`` binder, no heap and no aliasing, so there is no read-only
    input to overwrite and no substitute probe to build. Not fabricated. (Footer.)
  * UNGROUNDED-ORACLE ECHO — N/A. The oracle ``wrapped`` / ``codeOpen`` /
    ``endTok`` are concrete ``def``s fully unfolded in the ``pure`` region; the
    body ``renderedInline snippet`` is the literal input under the axiom. The
    master clause is a grounded function of the arg + fixed literals — there is
    no opaque answer-key to echo (materialising the concatenation IS the work).
    The positive controls are honest cheapest-reshape controls instead.
  * CONTROL-FLOW-EFFECT — N/A. The method is a pure value producer (returns a
    ``List Char``; the real writer raises ``SkipNode`` unconditionally on this
    path regardless of the assembled string), so there is no value-invisible
    control-flow effect to discriminate.
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is most of the battery. A rival
    correct on the shape of the wrapper but diverging on one pinned code point
    of the master equality: dropping the trailing suppressor, dropping the
    opening suppressor, both (the full pre-fix behaviour), trimming one code
    point too many, or emitting the trailer's two code points in the wrong
    ORDER. Each attacks the single master clause at a distinct offset and is
    refuted at a concrete input. The last is the only one length cannot refute,
    and it is there for exactly that reason.
  * ADMISSIBILITY — PORTED, re-aimed to the total carrier (see the footer): the
    obligation is discharged at a concrete F2P-shaped input before the frozen
    obligation is closed verbatim, which is what PRECOND-TOO-STRONG means when
    there is no `require` clause to violate.
  * DIVERGENCE (termination) — this bundle is `total`, so a measure-less loop IS
    rejected; it is recorded as a KNOWN HOLE of this gate rather than as a
    vacuous class, because the rejection is a module-level elaboration failure
    that no witness file can survive. Demonstrated in the footer.

AXIOM lane: EMPTY. ``renderedInline`` is an UNCHANGED callee owed the weakest
sufficient frame (its structural form is not even pinned here — the spec holds
for EVERY value it returns); probing it is G-AX's job, not this gate's. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10435"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single method's
# ---- `-- impl-start` / `-- impl-end` region and is unique in the file (both
# ---- facts asserted at load by _swap). The three surgery lines are the opening
# ---- substitution, the trailer trim, and the final append; the positive
# ---- controls reshape the block around them WITHOUT touching the frozen proof.
_OPEN = "    let hlcode := openTok ++ hlcode.drop beginTok.length\n"
_TAKE = "    let hlcode := stripped.take (stripped.length - 15)\n"
_RETURN = "    return hlcode ++ ['%', '\\n', '}', '}']\n"
_TAIL_BLOCK = _OPEN + \
    "    let stripped := rstrip hlcode\n" + \
    _TAKE + _RETURN

for _a in (_OPEN, _TAKE, _RETURN, _TAIL_BLOCK):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"


# ===========================================================================
# WITNESSES. Each is a SEMANTIC refutation of the method's Hoare triple at one
# concrete input point (a distinct `snippet` literal per witness — see the
# footer's binder note for why the point is structural, not body-dependent).
# The `prove_correct` block is stripped by the gate before the witness is
# appended, so no tactic script can mask the verdict; the tactics come from the
# frozen `Velvet.Std` import, so nothing extra is imported.
# ---------------------------------------------------------------------------
# trailing-suppressor drop: the wrapper is built correctly up to the trailer,
# so the output has the RIGHT SHAPE but is one code point short of `wrapped`
# (the closing '%' is missing). A pure LENGTH argument refutes it: `compute`
# fixes the gold length, the rival's is one less.
_W_TRAIL = r"""example : ¬ triple True (wrapInlineCode ['x'])
    (fun out => out = wrapped (renderedInline ['x'])) := by
  unfold wrapInlineCode
  rw [triple, wp_bind, MonadNonDet.wp_pickSuchThat]
  simp only [typeWithName, wp_pure, loomLogicSimp]
  push_neg
  intro _
  refine ⟨beginTok ++ ['\n'] ++ renderedInline ['x'] ++ ['\n'] ++ endTok ++ ['\n'], rfl, ?_⟩
  set body := renderedInline ['x']
  intro hEq
  have hcp := congrArg List.length (compute body)
  have hlen := congrArg List.length hEq
  simp only [List.length_append, List.length_cons, List.length_nil] at hcp hlen
  omega"""

# SHAPE-GENERIC reduction, shared by the two witnesses whose rival substitutes a
# DIFFERENT opening token than gold. Written as a `∀ p` lemma over the opening
# prefix `p` so the rewrite matches whatever token the impl under test
# substituted (`codeOpen` in the rival, `openTok` in the frozen solution).
#
# WHY THIS SHAPE IS LOAD-BEARING (audit finding; do not "simplify" it back).
# The earlier form of these two witnesses stated its `have`s with `codeOpen`
# spelled literally, mirroring the rival's program text. Against the FROZEN
# solution — whose program says `openTok` — the very first such rewrite has no
# occurrence to act on, so the build died at `rw [hre]` with
#   Tactic `rewrite` failed: Did not find an occurrence of the pattern
#   codeOpen ++ (['\n'] ++ body ++ ...)
# BEFORE the claim was ever engaged. That exit code carried no information about
# the claim: re-measured with the claim replaced by one that is TRUE of gold
# (`out = wrapped body ++ ['Q']`), the gold build failed with the byte-identical
# error at the byte-identical line — so a witness asserting the frozen solution
# is CORRECT there would also have been recorded as a refutation. Quantifying
# the prefix removes the program-shape dependence: the reduction now applies to
# both impls, and gold's failure lands on the arithmetic (`omega`), which does
# track the claim (the same forgery now ELABORATES against gold, exit 0).
_REDUCE_GENERIC = r"""  have hdrop : List.drop beginTok.length
      (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'] := by
    have h : beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']
        = beginTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']) := by
      simp [List.append_assoc]
    rw [h, List.drop_left]
  rw [hdrop]
  have hgen : ∀ p : List Char,
      rstrip (p ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']))
        = p ++ ['\n'] ++ body ++ ['\n'] ++ endTok := by
    intro p
    have h : p ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
        = (p ++ ['\n'] ++ body ++ ['\n'] ++ endTok) ++ ['\n'] := by
      simp [List.append_assoc]
    rw [h]; unfold rstrip endTok; simp [List.reverse_append]
  rw [hgen]"""

# opening-suppressor drop: substitutes `codeOpen` (no '%') for the leading token
# but keeps the gold `-15` trim, so the output is `codeOpen ++ '\n' ++ body ++
# '%\n}}'` — the OPENING '%' is absent. After the shape-generic reduction the
# output is in normal form and a LENGTH argument refutes (M): the rival's output
# is one code point shorter than `wrapped body`.
_W_OPEN = r"""example : ¬ triple True (wrapInlineCode ['y'])
    (fun out => out = wrapped (renderedInline ['y'])) := by
  unfold wrapInlineCode
  rw [triple, wp_bind, MonadNonDet.wp_pickSuchThat]
  simp only [typeWithName, wp_pure, loomLogicSimp]
  push_neg
  intro _
  refine ⟨beginTok ++ ['\n'] ++ renderedInline ['y'] ++ ['\n'] ++ endTok ++ ['\n'], rfl, ?_⟩
  set body := renderedInline ['y']
""" + _REDUCE_GENERIC + r"""
  intro hEq
  have hlen := congrArg List.length hEq
  simp only [List.length_append, List.length_take, List.length_cons,
             List.length_nil, endTok_len, wrapped, openTok, codeOpen] at hlen
  omega"""

# the full pre-fix behaviour: opening substituted WITHOUT '%' (`codeOpen`), the
# trailer trimmed at `-14` (dropping only `endTok`, so the trailing '\n' before
# '}}' survives) and appended without the closing '%'. Output is
# `codeOpen ++ '\n' ++ body ++ '\n}}'` — NEITHER '%'. Uses the same shape-generic
# reduction as `_W_OPEN` (this rival also substitutes `codeOpen`, so a witness
# that spells the opening token literally dies on gold at a program-shape rewrite
# before engaging the claim — see the `_REDUCE_GENERIC` note), then refutes (M)
# by length: two code points short of `wrapped body`.
_W_PRE = r"""example : ¬ triple True (wrapInlineCode ['a', 'b'])
    (fun out => out = wrapped (renderedInline ['a', 'b'])) := by
  unfold wrapInlineCode
  rw [triple, wp_bind, MonadNonDet.wp_pickSuchThat]
  simp only [typeWithName, wp_pure, loomLogicSimp]
  push_neg
  intro _
  refine ⟨beginTok ++ ['\n'] ++ renderedInline ['a', 'b'] ++ ['\n'] ++ endTok ++ ['\n'], rfl, ?_⟩
  set body := renderedInline ['a', 'b']
""" + _REDUCE_GENERIC + r"""
  intro hEq
  have hlen := congrArg List.length hEq
  simp only [List.length_append, List.length_take, List.length_cons,
             List.length_nil, endTok_len, wrapped, openTok, codeOpen] at hlen
  omega"""

# off-by-one trailer over-trim: trims at `-16` instead of `-15`, dropping ONE
# extra code point off the stripped body. Refuted by a pure LENGTH argument
# after the same structural reduction as the opening witness.
_W_OFF16 = r"""example : ¬ triple True (wrapInlineCode ['z'])
    (fun out => out = wrapped (renderedInline ['z'])) := by
  unfold wrapInlineCode
  rw [triple, wp_bind, MonadNonDet.wp_pickSuchThat]
  simp only [typeWithName, wp_pure, loomLogicSimp]
  push_neg
  intro _
  refine ⟨beginTok ++ ['\n'] ++ renderedInline ['z'] ++ ['\n'] ++ endTok ++ ['\n'], rfl, ?_⟩
  set body := renderedInline ['z']
  have hdrop : List.drop beginTok.length
      (beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'] := by
    have : beginTok ++ ['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']
        = beginTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n']) := by
      simp [List.append_assoc]
    rw [this, List.drop_left]
  rw [hdrop]
  have hre : openTok ++ (['\n'] ++ body ++ ['\n'] ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'] := by
    simp [List.append_assoc]
  rw [hre]
  have hrs : rstrip ((openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok ++ ['\n'])
      = (openTok ++ ['\n'] ++ body ++ ['\n']) ++ endTok := by
    unfold rstrip endTok; simp [List.reverse_append]
  rw [hrs]
  intro hEq
  have hlen := congrArg List.length hEq
  simp only [List.length_append, List.length_take, endTok_len, wrapped, openTok, codeOpen,
             List.length_cons, List.length_nil] at hlen
  omega"""


# trailer-order swap: the output has the RIGHT LENGTH and the wrong CONTENT, so
# no length argument can refute it. The reduction is carried all the way to the
# output's normal form (the shape-generic `∀ p` prefix rewrites, then the trim
# arithmetic and the `take`), after which `simp` decides the concatenation
# disequality on code points. Against the FROZEN solution the same `simp` PROVES
# the equation (it reduces gold's output to `wrapped body`), so the goal left
# unproven is the negation's own `⊢ False` — a semantic refutation, not a tactic
# mismatch, and it tracks the claim: with a claim that is true of gold the build
# elaborates (exit 0).
_W_SWAP = r"""example : ¬ triple True (wrapInlineCode ['w'])
    (fun out => out = wrapped (renderedInline ['w'])) := by
  unfold wrapInlineCode
  rw [triple, wp_bind, MonadNonDet.wp_pickSuchThat]
  simp only [typeWithName, wp_pure, loomLogicSimp]
  push_neg
  intro _
  refine ⟨beginTok ++ ['\n'] ++ renderedInline ['w'] ++ ['\n'] ++ endTok ++ ['\n'], rfl, ?_⟩
  set body := renderedInline ['w']
""" + _REDUCE_GENERIC + r"""
  have hcut : ∀ p : List Char, (p ++ ['\n'] ++ body ++ ['\n'] ++ endTok).length - 15
      = (p ++ ['\n'] ++ body).length := by
    intro p
    simp only [List.length_append, List.length_cons, List.length_nil, endTok_len]; omega
  rw [hcut]
  have htake : ∀ p : List Char,
      List.take (p ++ ['\n'] ++ body).length (p ++ ['\n'] ++ body ++ ['\n'] ++ endTok)
        = p ++ ['\n'] ++ body := by
    intro p
    have h : p ++ ['\n'] ++ body ++ ['\n'] ++ endTok
        = (p ++ ['\n'] ++ body) ++ (['\n'] ++ endTok) := by simp [List.append_assoc]
    rw [h, List.take_left]
  rw [htake]
  unfold wrapped openTok codeOpen
  simp"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. Each reshapes only the surface syntax of the
    # trailer block, leaving the value flow (and thus the `compute`-shaped
    # obligation the frozen proof discharges) intact. If a faithful correct
    # reshape could not verify, the spec would be SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-bind-result-local",
        "kind": "soundness",
        "expect": "verify",
        # Bind the final concatenation to a local `result`, then return it —
        # instead of returning the append expression directly. Same value; the
        # obligation `loom_solve` leaves is byte-identical, so the frozen proof
        # (`rw [choice_1, compute (renderedInline snippet)]`) still closes.
        "module": _swap(
            _BASE, _RETURN,
            "    let result := hlcode ++ ['%', '\\n', '}', '}']\n"
            "    return result\n"),
        "rationale": "a correct reshape that binds the final wrapper to a local "
                     "before returning it computes the same output, so the "
                     "master equality (M) `out = wrapped (renderedInline snippet)` "
                     "still discharges; must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-control-rename-locals",
        "kind": "soundness",
        "expect": "verify",
        # Rename every trailer local (substituted / stripped / cut / trimmed)
        # and split the trim length into its own `let`. Pure alpha-variation of
        # the block: identical value flow, identical residual obligation.
        "module": _swap(
            _BASE, _TAIL_BLOCK,
            "    let substituted := openTok ++ hlcode.drop beginTok.length\n"
            "    let stripped := rstrip substituted\n"
            "    let cut := stripped.length - 15\n"
            "    let trimmed := stripped.take cut\n"
            "    return trimmed ++ ['%', '\\n', '}', '}']\n"),
        "rationale": "alpha-renaming the trailer locals and hoisting the trim "
                     "length into a named `let` leaves the output unchanged, so "
                     "the master equality (M) still holds; a faithful correct "
                     "reshape must verify.",
    },
    {
        # The sibling's own positive shape, LANDED. The footer previously
        # recorded this reshape as not portable ("OVER-NORMALIZES the inner
        # list under the frozen proof's `List.append_assoc` and breaks the
        # `compute` match"). Re-measured during the audit: that is a statement
        # about ONE tactic script, not about the spec, and re-associating the
        # goal before appealing to `compute` closes it (exit 0). Editing the
        # proof body is in scope — the obligation and the spec are untouched —
        # so the honest port of the sibling positive is shippable and this is
        # it. Splitting the trailer is the cheapest reshape that changes the
        # TERM STRUCTURE of the output rather than just its variable names,
        # which is what the other two positives leave untested.
        "id": "pos-control-split-suffix",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _RETURN,
                  "    let tail := ['%', '\\n']\n"
                  "    return hlcode ++ tail ++ ['}', '}']\n"),
            "prove_correct wrapInlineCode by\n"
            "  loom_solve\n"
            "  rw [choice_1, compute (renderedInline snippet)]\n",
            "prove_correct wrapInlineCode by\n"
            "  loom_solve\n"
            "  rw [choice_1]\n"
            "  have h := compute (renderedInline snippet)\n"
            "  simp only [List.append_assoc] at h ⊢\n"
            "  exact h\n"),
        "rationale": "splitting the single trailer append into `['%','\\n']` "
                     "then `['}','}']` emits the same code points in the same "
                     "order, so the master equality (M) still holds. This is a "
                     "faithful correct reshape whose output TERM is associated "
                     "differently from gold's, so it must verify (else "
                     "SPEC-TOO-STRONG); the residual goal is closed by "
                     "re-associating before appealing to `compute`.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation must be SATISFIABLE at an F2P-shaped
    # input, not merely provable in general. The method has no `require`
    # clause, so the total-carrier analogue is what is tested here: discharge
    # the master equality's target at one concrete F2P-shaped snippet BY
    # EVALUATION, as a `have`, before closing the frozen obligation verbatim.
    # If (M) were unsatisfiable at that point (an over-strong pin no real
    # rendering can meet), the `have` would fail and the case would fail,
    # which is exactly the PRECOND-TOO-STRONG signal. The footer previously
    # recorded this lane as vacuous "because there is no `require`"; that is
    # the reason the lane's own definition excludes, and the case below was
    # measured to land (exit 0), so it is shipped rather than documented away.
    # =====================================================================
    {
        "id": "admissibility-fshaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "prove_correct wrapInlineCode by\n"
            "  loom_solve\n"
            "  rw [choice_1, compute (renderedInline snippet)]\n",
            "prove_correct wrapInlineCode by\n"
            "  have hadm := compute (renderedInline ['x'])\n"
            "  have hne : wrapped (renderedInline ['x']) ≠ [] := by\n"
            "    unfold wrapped codeOpen; simp\n"
            "  loom_solve\n"
            "  rw [choice_1, compute (renderedInline snippet)]\n"),
        "rationale": "PRECOND-TOO-STRONG probe on a total carrier: at the "
                     "F2P-shaped single-code-point snippet `['x']` the master "
                     "equality's obligation is DISCHARGED by evaluation "
                     "(`compute` instantiated at that input) and its target is "
                     "non-degenerate (`wrapped … ≠ []`, i.e. the spec does not "
                     "pin the output to the empty list at that point). The "
                     "frozen obligation is then closed verbatim, so the case "
                     "adds a satisfiability demonstration without weakening "
                     "anything. If the obligation were unsatisfiable at this "
                     "normal input the `have`s would fail.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a SEMANTIC refutation `witness` that
    # holds of the rival and FAILS on gold (verified: rival build exit 0, gold
    # build exit 1), plus the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "partial-drop-trailing-suppressor",
        "kind": "uniqueness",
        "expect": "reject",
        # Appends the closing trailer WITHOUT the trailing '%' — the pre-fix
        # bug on the CLOSING side. Correct in shape, one suppressor short.
        "module": _swap(_BASE, _RETURN, "    return hlcode ++ ['\\n', '}', '}']\n"),
        "refinement": "this is the pre-fix CLOSING-side defect: the rendered "
                      "output is `…body\\n}}` instead of `…body%\\n}}`, so the "
                      "closing line break renders as a spurious trailing space "
                      "in the inline code. The F2P test matches the wrapped "
                      "fragment (which carries `%\\n}}`) verbatim as a substring "
                      "of the generated LaTeX; a build producing `\\n}}` fails "
                      "that substring assertion, so it would NOT resolve.",
        "rationale": "REJECT from the master equality (M): `wrapped body` pins a "
                     "'%' immediately before the closing break, but this rival "
                     "omits it, so the output is exactly one code point short of "
                     "`wrapped (renderedInline snippet)`. The witness instantiates "
                     "the demonic choice at the highlighter's framed value and "
                     "refutes (M) by a length argument against `compute`.",
        "witness": _W_TRAIL,
    },
    {
        "id": "prepatch-no-suppressors",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal pre-fix behaviour: opening substituted WITHOUT '%'
        # (codeOpen), trailer trimmed at -14 and appended without the closing
        # '%'. NEITHER suppressor is emitted.
        "module": _swap(
            _swap(_swap(_BASE, _OPEN,
                        "    let hlcode := codeOpen ++ hlcode.drop beginTok.length\n"),
                  _TAKE, "    let hlcode := stripped.take (stripped.length - 14)\n"),
            _RETURN, "    return hlcode ++ ['}', '}']\n"),
        "refinement": "literal pre-fix behaviour: output is "
                      "`codeOpen ++ '\\n' ++ body ++ '\\n}}'` with NEITHER '%'. "
                      "Both adjacent line breaks render as spurious spaces at the "
                      "start and end of the inline code. The F2P test expects the "
                      "wrapped fragment carrying `{%\\n` at the open and `%\\n}}` "
                      "at the close; the pre-fix output has `{\\n` and `\\n}}`, so "
                      "it fails the substring assertion — this is exactly the bug "
                      "the fix corrects, so it would NOT resolve.",
        "rationale": "REJECT from the master equality (M): `wrapped body` pins a "
                     "'%' both at offset `codeOpen.length` (opening) and before "
                     "the closing break, and this rival emits neither. The "
                     "witness reduces the triple at the framed value and refutes "
                     "(M): the normal-form output `codeOpen ++ '\\n' ++ body ++ "
                     "'\\n}}'` is not `wrapped body`.",
        "witness": _W_PRE,
    },
    {
        "id": "partial-drop-opening-suppressor",
        "kind": "uniqueness",
        "expect": "reject",
        # Substitutes codeOpen (no '%') for the leading token but keeps the gold
        # -15 trim and the '%\n}}' trailer. The OPENING suppressor alone is
        # dropped — the closing side is correct.
        "module": _swap(
            _BASE, _OPEN,
            "    let hlcode := codeOpen ++ hlcode.drop beginTok.length\n"),
        "refinement": "the opening-side half of the pre-fix defect: output is "
                      "`codeOpen ++ '\\n' ++ body ++ '%\\n}}'`, so the OPENING "
                      "line break renders as a spurious LEADING space while the "
                      "closing side is correct. The F2P test matches the wrapped "
                      "fragment (which carries `{%\\n` at the open) verbatim; a "
                      "build producing `{\\n` there fails the substring assertion, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from the master equality (M), attacked at the "
                     "OPENING offset alone (distinct from the trailing- and "
                     "no-suppressor rivals): `wrapped body` pins '%' at offset "
                     "`codeOpen.length`, absent here. The witness reduces the "
                     "triple at the framed value and refutes (M) by putting the "
                     "output in normal form and discharging the disequality.",
        "witness": _W_OPEN,
    },
    {
        "id": "partial-offbyone-overtrim-trailer",
        "kind": "uniqueness",
        "expect": "reject",
        # Trims the stripped body at -16 instead of -15, dropping ONE extra code
        # point. Correct on the wrapper shape, wrong by one on the trailing
        # edge of the body — the value analogue of the nagini off-by-one.
        "module": _swap(
            _BASE, _TAKE,
            "    let hlcode := stripped.take (stripped.length - 16)\n"),
        "refinement": "trimming one code point too many drops the final code "
                      "point of the rendered body (e.g. the closing brace of a "
                      "`\\PYG{…}{…}` token), so the wrapped fragment the F2P test "
                      "matches verbatim no longer occurs as a substring of the "
                      "generated LaTeX. It would NOT resolve.",
        "rationale": "REJECT from the master equality (M), which pins the FULL "
                     "rendered body between the suppressors; over-trimming leaves "
                     "the output one code point short of `wrapped body`. The "
                     "witness reduces the triple at the framed value and refutes "
                     "(M) by a length argument (rival length = gold length − 1). "
                     "Correct on every shorter prefix, wrong on the final edge — "
                     "partial-domain.",
        "witness": _W_OFF16,
    },
    {
        # AUDIT ADDITION — the only rival whose refutation is NOT a length
        # argument. Every other reject case here emits an output of the wrong
        # LENGTH, so all four of their witnesses close by `omega` on lengths;
        # a spec that pinned only `out.length` would have satisfied them all.
        # This rival emits the correct number of code points in the wrong
        # ORDER ('\n' before '%' in the trailer), so length is no evidence and
        # the witness must refute on CONTENT. Gold-side failure is
        # `unsolved goals ... ⊢ False`: `simp` reduced the frozen impl's output
        # to `wrapped body` and closed the equation, leaving the negation's
        # `False` unprovable — the strongest gold-side evidence available, and
        # it tracks the claim (the same witness with a claim TRUE of gold
        # elaborates against gold, exit 0).
        "id": "partial-swap-trailer-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RETURN,
                        "    return hlcode ++ ['\\n', '%', '}', '}']\n"),
        "refinement": "the two trailing code points are emitted in the wrong "
                      "order: `…body\\n%}}` instead of `…body%\\n}}`. The "
                      "suppressor must PRECEDE the line break to suppress it; "
                      "after the break it is a comment marker on the following "
                      "line instead, so the break still renders as a spurious "
                      "trailing space AND a stray marker reaches the output. "
                      "The F2P test matches the wrapped fragment carrying "
                      "`%\\n}}` verbatim as a substring of the generated LaTeX, "
                      "which `\\n%}}` does not contain, so it would NOT resolve.",
        "rationale": "REJECT from the master equality (M), attacked on ORDER "
                     "rather than on count: `wrapped body` pins the suppressor "
                     "before the closing break, and this rival emits exactly as "
                     "many code points with those two transposed. Length is "
                     "therefore no evidence here — this is the one rival the "
                     "battery's length arguments could not have caught, so it "
                     "closes the gap where a length-only spec would pass. The "
                     "witness reduces the triple at the framed value, puts the "
                     "output in normal form and refutes (M) on content.",
        "witness": _W_SWAP,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 frame-
# mutation reject, 3 partial-domain rejects, 1 soundness positive, 1
# admissibility positive). This bundle models the SAME single behaviour (wrap
# one rendered inline snippet), collapsed onto ONE master equality, so the port
# is close to one-for-one on the partial-domain lane.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   frame-mut-write-content               -> (none)                    VACUOUS
#   partial-drop-trailing-suppressor      -> partial-drop-trailing-suppressor
#                                                                        PORTED
#   prepatch-no-suppressors               -> prepatch-no-suppressors    PORTED
#   partial-offbyone-drop-last-codepoint  -> partial-offbyone-overtrim-trailer
#                                                                    RE-EXPRESSED
#   pos-control-split-suffix              -> pos-control-bind-result-local
#                                                                    RE-EXPRESSED
#   admissibility-selfcall-fshaped        -> (none)                     DROPPED
#
# VACUOUS (frame-mutation): the sibling rejects an impl that WRITES to a
#   read-only 1/2-permission input `content`. This backend is referentially
#   transparent and the method declares no `mut` binder, so there is no
#   read-only input to overwrite and no substitute probe. Not fabricated (per
#   the porting map: this class is vacuous on Lean/Velvet).
# RE-EXPRESSED (off-by-one): the nagini rival stops a copy LOOP one iteration
#   short. There is no copy loop here (the body flows through `renderedInline`
#   under an opaque axiom and the surgery is a single `take`), so the same
#   partial-domain fault is re-expressed as an off-by-one on the TRIM length
#   (`-16` vs `-15`), which drops the final code point of the body. Same
#   failure mode (one code point of the body lost), refuted by length.
# PORTED (positive): the nagini positive splits a suffix append in two, and so
#   does `pos-control-split-suffix` here. An earlier revision of this footer
#   recorded the split as NOT portable, on the ground that it over-normalizes
#   the inner list under `List.append_assoc` and breaks the `compute` match.
#   The AUDIT re-measured that: it describes one tactic script, not the spec.
#   Re-associating the goal before appealing to `compute`
#   (`simp only [List.append_assoc] at h ⊢; exact h`) closes it, and editing the
#   proof body is in scope because the spec and the obligation are untouched.
#   So the sibling's positive is shipped rather than substituted, alongside the
#   two cheapest-reshape controls (bind-result-local, rename-locals). It is the
#   only positive whose output TERM is associated differently from gold's, which
#   is the part alpha-renaming cannot test.
# PORTED, RE-AIMED (admissibility): `admissibility-fshaped-input`. The nagini
#   case is a self-call on an F2P-shaped `content` establishing the
#   fractional/length/tail precondition. An earlier revision of this footer
#   dropped the lane because this method has NO `require` clause, so "there is
#   nothing to admit". The AUDIT rejects that reason: it is the reason the
#   lane's own definition excludes. On a TOTAL carrier the analogue of an
#   over-strong precondition is the OBLIGATION being unsatisfiable at exactly an
#   F2P-shaped input, and a positive that discharges the obligation at that
#   concrete input — by evaluation, as a `have`, before closing the frozen
#   obligation verbatim — tests it directly. That is what the case does at the
#   single-code-point snippet `['x']`: it instantiates `compute` there and shows
#   the pinned target is non-degenerate at that point (`wrapped … ≠ []`). The
#   frozen proof is still run verbatim afterwards, so nothing is reshaped to
#   make it pass; measured to verify. PRECOND-TOO-STRONG is therefore tested
#   rather than documented as a gap.
# UNTESTED BY THIS GATE, not a spec hole and not vacuous (divergence / F'):
#   "KNOWN HOLE" was the wrong label and is withdrawn, since the spec REJECTS the
#   class. This bundle sets `loom.semantics.termination "total"` (and the
#   `set_option` elaborator itself runs `openScope `TotalCorrectness`,
#   Loom/MonadAlgebras/WP/Options.lean:169-186, so it cannot drift from the file's
#   `open`). Under `total` a postcondition is claimed of ALL runs, so every loop
#   owes a decreasing measure AND its descent, and BOTH diverging shapes are
#   rejected:
#     * loop with NO measure: rejected at the `method` DECLARATION, measured, with
#       `Decreasing annotations are required in total correctness semantics`. That
#       error is MODULE-level and the witness file retains the `method` (it strips
#       only the `prove_correct` obligations), so the witness file does not
#       elaborate either: a trivial witness (`example : (1:Nat) + 1 = 2 := by
#       decide`) appended to the diverging module fails with that identical error
#       (exit 1). The rival build is the half a witness MUST pass, so no witness
#       whatsoever can succeed and the case could only be `witness-unproven`.
#     * loop CARRYING a measure that does not decrease: rejected on the measure's
#       OWN goal, `case «decreasing_1: ...»`, so it cannot be dismissed as merely
#       missing the annotation. Here the refusal lands at the `prove_correct` site,
#       which the witness file DOES strip, so that module elaborates; but the
#       rival's post-image is then an unreduced `forIn Lean.Loop.mk` term carrying
#       `invariantGadget` / `onDoneGadget` / `decreasingGadget`, which the kernel
#       will not normalise to something a concrete-input tester can decide, so a
#       real witness still comes back `witness-unproven`.
#   Recorded so the artifact says the divergence lane is untested by THIS gate for
#   witness-channel reasons, NOT that the spec admits the rival: the termination
#   obligation really does reject those impls, and G-VERIFY is where that shows.
# ADDED (1, clause coverage). `partial-drop-opening-suppressor` isolates the
#   OPENING '%' offset of the master equality — the sibling folds the opening-
#   suppressor attack into its full pre-fix rival; splitting it out gives one
#   rival per pinned '%' offset (opening / closing / both), so the master
#   equality is attacked at each suppressor position independently.
# ADDED (2, audit). `partial-swap-trailer-order` is the battery's only rival
#   that is refuted on CONTENT rather than on length. Every other reject case
#   emits an output of the wrong LENGTH and every one of their witnesses closes
#   by `omega` on lengths, so a spec pinning only `out.length` would have
#   satisfied all of them; this rival transposes the trailer's two code points,
#   keeping the count exact, and its witness decides the concatenation
#   disequality on code points instead.
#
# WITNESS DISCRIMINATION (re-derived by audit, with the forgery test). Because
#   `renderedInline` is `noncomputable`, the
#   tester route (`extract_program_for` … `decide`) is UNAVAILABLE — it fails to
#   extract. Every reject witness is instead a SEMANTIC refutation of the Hoare
#   triple, reduced via the frozen `Velvet.Std` wp-lemmas, that holds of the
#   rival and FAILS on gold (gold satisfies (M) at every input, so no genuine
#   "(M) is violated here" statement can hold of it). Verified during authoring:
#   rival build exit 0, gold build exit 1, for all five. Each gold-side failure
#   was additionally checked to TRACK THE CLAIM, by rebuilding the same witness
#   against the frozen solution with the claim replaced by one that is TRUE of
#   it: every such forgery ELABORATES (exit 0), so no case rests on a gold exit
#   code that a claim-independent tactic failure would have produced. Two cases
#   failed exactly that test before repair (see `_REDUCE_GENERIC`).
#
# BINDER COVERAGE. The sole input `snippet` is consumed ONLY under the opaque
#   `renderedInline`, so the master equality's dependence on it is fully mediated
#   by that axiom: the spec pins the surrounding FRAME (opening, suppressors,
#   trailer) and says nothing about body CONTENT, and every witness's reduction
#   is generic in `renderedInline <lit>` (it never inspects the body). Varying
#   the literal therefore does not change the discriminating power — the four
#   witnesses nonetheless use FOUR distinct points (['x'], ['y'], ['a','b'],
#   ['z']) so the battery probes more than one input, but the genuine axis of
#   attack is the wrapper OFFSET (opening '%', closing '%', both, body edge),
#   not the body value. This is inherent to the carrier, not a coverage gap.
#
# AXIOM_TESTS: dropped. `renderedInline` is an UNCHANGED callee owed only the
#   weakest sufficient frame (its form is not even pinned in this spec), which
#   is G-AX's lane; this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
