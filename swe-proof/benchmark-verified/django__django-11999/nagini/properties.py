"""properties.py — PBT falsification manifest for django__django-11999.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The change under spec is the gold's hasattr-guard added
around the generated-accessor `setattr` in `Field.contribute_to_class`'s choices
branch (the "Cannot override get_FOO_display()" regression fix). It is modeled as
TWO functions over a class attribute namespace `cls: Dict[int, int]` (an
attribute-name token -> bound-callable-identity token), each sharing one
guarded-installation skeleton:

    if accessor_name not in cls:                 # the name is not yet provided
        cls[accessor_name] = generated_accessor()# install the generated accessor

  preserve_existing_accessor(cls, accessor_name)   # case: name ALREADY present
  install_missing_accessor(cls, accessor_name)     # case: name NOT yet present

DEFENDED SURFACE (the load-bearing postcondition clauses):

  preserve_existing_accessor (precond: accessor_name in cls):
    Pp1  Ensures(accessor_name in cls)                              # still present
    Pp2  Ensures(cls[accessor_name] == Old(cls[accessor_name]))     # NOT overwritten
         (THE discriminating clause: an author-defined get_<f>_display survives;
          the generated accessor is not installed over it — the F2P fix)
    Pf   Ensures(cls[other_name()] == Old(cls[other_name()]))       # frame: an
         unrelated attribute keeps its exact bound identity
    Pq   quantified whole-namespace frame (explicit triggers): NO key's
         membership changes and every pre-existing key keeps its bound value
         (this case performs no write at all)
    Pt   Requires(MustTerminate(2)) — the step is BOUNDED: it runs to completion
         and hands control back, so the accessor claims are TOTAL rather than
         claimed only of runs that reach the end

  install_missing_accessor (precond: accessor_name not in cls):
    Pi1  Ensures(accessor_name in cls)                              # now present
    Pi2  Ensures(cls[accessor_name] == generated_accessor())        # the GENERATED
         accessor is the one installed
    Pf   Ensures(cls[other_name()] == Old(cls[other_name()]))       # frame
    Pq   quantified whole-namespace frame (explicit triggers): membership
         changes for the accessor name ONLY; every other pre-existing key keeps
         its bound value (the operation writes at most the accessor key)
    Pt   Requires(MustTerminate(2))                                   # same
         boundedness obligation as above

  The Pq quantifiers close the spec-admittance gap a G-EQ audit demonstrated
  against the per-key-only frame: a same-spec impl that installed the accessor
  AND wrote one extra unrelated key (e.g. cls[other_name()+1] = ...) verified
  under Pf alone; under Pq it is rejected. Pf is retained as the sharp named
  witness the clobber rivals target (rejection attributable to one clause).

  Pt closes a SEPARATE spec-admittance gap, on a different axis, which a later
  G-EQ / G-PANEL-1 audit demonstrated against the write-only surface above.
  Without a boundedness obligation Viper proves only PARTIAL correctness: every
  Ensures — INCLUDING the Pq whole-namespace frame that closed the earlier gap —
  is claimed only of runs that reach the end, so a step that never hands control
  back satisfies all of them by doing nothing, forever (the frame is "respected"
  vacuously, and no write-axis clause can see it). Under Pt such a step cannot
  discharge its obligation at the outgoing call and is rejected
  (adv-diverge-preserve / adv-diverge-install below). The two axes are
  independent: Pq constrains WHAT is written, Pt constrains WHETHER the step
  finishes, and neither implies the other. Pt costs the honest impls nothing —
  a single guarded namespace write fits the budget (the positive controls below
  are the evidence).

WHICH WEAKNESS CLASSES APPLY, and why:

  * FRAME-MUTATION (overwrite a read-only Acc(x,1/2) input to satisfy the
    postcondition vacuously) does NOT apply: `cls` is held at FULL permission
    (`dict_pred(cls)`, not `Acc(.,1/2)`) and is GENUINELY mutated by the gold
    (the accessor IS installed in the install case). There is no read-only input
    to subvert; `accessor_name` is a pass-by-value `int` immutable. The analogue
    that IS reachable here — corrupting an *unrelated* attribute (other_name())
    to "satisfy" the spec while doing damage — is attacked by adv-clobber-other-*
    and is rejected by the per-key frame postcondition `Pf`, not by the
    permission system. (Per directive: with no read-only input, the mandatory
    frame-mutation case is satisfied by this value-level frame attack; see
    'assessment'.)

  * UNGROUNDED-ORACLE ECHO (echo a @Pure answer-key without doing the work) does
    NOT apply in the answer-key sense: `generated_accessor()` (==0) is not an
    opaque oracle pinned to a hidden answer — it is the literal identity that the
    install case is *supposed* to write. There is no "wrong echo" that verifies:
    in the install case `cls[accessor_name] == generated_accessor()` is the
    correct behaviour, and in the preserve case the spec forbids that very write
    (Pp2). So an "echo" of generated_accessor() into the preserve case is exactly
    the prepatch bug (adv-preserve-overwrite) and is REJECTED. The cheapest honest
    impl is included as a positive control (pos-install-unconditional).

  * PARTIAL-DOMAIN, value-level frame, and the prepatch-overwrite uniqueness
    attacks all apply and are built below.

  * CONTROL-FLOW-EFFECT applies, in its DIVERGENCE form, and is built below
    (adv-diverge-*). The raise/return form does not: both functions return None
    with no raise path, and the only value-level effect is the dict mutation,
    which the value postconditions fully pin. But NOT HANDING CONTROL BACK is a
    control-flow effect that no value postcondition can see, because under
    partial correctness every Ensures is conditioned on reaching the end. Pt is
    what makes it visible, and the adv-diverge-* rivals are what keep Pt honest:
    if either verified, the whole postcondition surface would be satisfiable by
    an assembly step that hangs, and the faithful patch of that step hangs
    model-class assembly for every class (the F2P and every P2P fail).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap_*`)
that edits ONLY inside one function's `# impl-start`/`# impl-end` region. The
two functions share a byte-identical impl body, so each anchor includes that
function's UNIQUE postcondition tail (kept BYTE-IDENTICAL in the replacement) to
make the match unique — the spec text is never altered, so `markers.same_spec`
is GUARANTEED and a rejection is attributable to the postcondition catching wrong
behaviour, never to a tampered spec.

AXIOM_TESTS is empty: meta.json `axioms == []`; the only A-tagged step is an
A-reference deep model (the guarded install spelled out in the impl region),
already validated == the real `Field.contribute_to_class` out-of-band by
axiom_check.py / G-AX over 4 boundary + 2000 fuzz real-Django model assemblies in
BOTH the gold-guarded and base_commit-unguarded states. There is no @ContractOnly
axiom whose Ensures the proof consumes, so nothing to falsify against a real
callee here (G-AX covers it).
"""
from pathlib import Path

INSTANCE = "django__django-11999"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()

# The shared guarded-install impl body (identical text in BOTH functions).
_GOLD_IMPL = (
    "    if accessor_name not in cls:\n"
    "        cls[accessor_name] = generated_accessor()\n"
)

# FROZEN SPEC ANCHOR for the boundedness obligation Pt. The _swap_* anchors
# below are POSTcondition tails, so on their own they would not notice a change
# to the PREcondition region — a spec edit could land in model.py and leave this
# battery silently testing the old surface. This anchor is asserted directly, so
# adding/removing/renumbering Pt fails at import instead.
_PT_ANCHOR = "    Requires(MustTerminate(2))\n"
if _BASE.count(_PT_ANCHOR) != 2:
    raise AssertionError(
        "properties.py drift: expected the boundedness obligation "
        f"{_PT_ANCHOR!r} in BOTH modeled functions of model.py, found "
        f"{_BASE.count(_PT_ANCHOR)}")
if "from nagini_contracts.obligations import MustTerminate\n" not in _BASE:
    raise AssertionError(
        "properties.py drift: model.py states MustTerminate without importing it")

# preserve_existing_accessor's UNIQUE postcondition tail immediately preceding
# its impl region. Kept byte-identical in the replacement so the spec is
# untouched; only the impl body between # impl-start / # impl-end changes.
_PRESERVE_TAIL = (
    "    Ensures(cls[accessor_name] == Old(cls[accessor_name]))\n"
    "    # A representative unrelated attribute keeps its exact bound identity: the\n"
    "    # operation does not disturb a name other than the accessor name.\n"
    "    Ensures(other_name() in cls)\n"
    "    Ensures(cls[other_name()] == Old(cls[other_name()]))\n"
    "    # Whole-namespace frame: in this case the operation performs NO write at\n"
    "    # all, so no name's membership changes and every name that was present\n"
    "    # keeps its exact bound identity. (Explicit triggers keep the quantifiers\n"
    "    # tractable for the verifier.)\n"
    "    Ensures(Forall(int, lambda k: ((k in cls) == Old(k in cls), [[k in cls]])))\n"
    "    Ensures(Forall(int, lambda k: (Implies(k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))\n"
    "    # post-conditions-end\n"
    "    # impl-start\n"
)

# install_missing_accessor's UNIQUE postcondition tail immediately preceding its
# impl region (differs from preserve's by the install clause).
_INSTALL_TAIL = (
    "    Ensures(cls[accessor_name] == generated_accessor())\n"
    "    # A representative unrelated attribute keeps its exact bound identity: the\n"
    "    # operation does not disturb a name other than the accessor name.\n"
    "    Ensures(other_name() in cls)\n"
    "    Ensures(cls[other_name()] == Old(cls[other_name()]))\n"
    "    # Whole-namespace frame: the operation writes AT MOST the accessor name.\n"
    "    # Membership changes for the accessor name only, and every OTHER name that\n"
    "    # was present keeps its exact bound identity. (Explicit triggers keep the\n"
    "    # quantifiers tractable for the verifier.)\n"
    "    Ensures(Forall(int, lambda k: (Implies(k != accessor_name, (k in cls) == Old(k in cls)), [[k in cls]])))\n"
    "    Ensures(Forall(int, lambda k: (Implies(k != accessor_name and k in cls and Old(k in cls), cls[k] == Old(cls[k])), [[cls[k]]])))\n"
    "    # post-conditions-end\n"
    "    # impl-start\n"
)


def _swap_one(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence; assert it matched + is unique so silent
    drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


def _swap_preserve(new_body: str) -> str:
    """Replace ONLY preserve_existing_accessor's impl body. Anchors on its unique
    postcondition tail + the shared gold body; keeps the postcondition tail
    byte-identical (spec untouched)."""
    old = _PRESERVE_TAIL + _GOLD_IMPL
    new = _PRESERVE_TAIL + new_body
    return _swap_one(_BASE, old, new)


def _swap_install(new_body: str) -> str:
    """Replace ONLY install_missing_accessor's impl body (same scheme)."""
    old = _INSTALL_TAIL + _GOLD_IMPL
    new = _INSTALL_TAIL + new_body
    return _swap_one(_BASE, old, new)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S1) preserve: structurally-different but CORRECT. The precondition guarantees
# accessor_name in cls, so the guarded write never fires under the gold body; an
# explicit branch-reorder that makes that explicit (preserve when present, install
# only when absent) is semantically identical and does no write on this domain, so
# cls is unchanged and every postcondition (Pp1/Pp2/Pf) holds trivially. If this
# correct reshape fails to verify => SPEC-TOO-STRONG (over-fit to the negated
# guard spelling). Keeps all gold obligations (no framing lemma needed: no write).
_POS_PRESERVE_REORDER = _swap_preserve(
    "    if accessor_name in cls:\n"
    "        pass\n"
    "    else:\n"
    "        cls[accessor_name] = generated_accessor()\n"
)

# (S2) install: structurally-different but CORRECT and the CHEAPEST honest impl.
# The precondition guarantees accessor_name not in cls, so the guard is redundant
# in the install case; an UNCONDITIONAL install writes exactly the generated
# accessor under the (provably-absent) name, establishing Pi1/Pi2, and touches no
# other key so Pf holds (accessor_name != other_name() by precond). This is the
# gold body with the (here-vacuous) guard removed — it must verify. If not =>
# SPEC-TOO-STRONG. Also the cheapest grounded impl (the oracle is the install
# value, not an answer-key), so it doubles as the no-ungrounded-echo control.
_POS_INSTALL_UNCONDITIONAL = _swap_install(
    "    cls[accessor_name] = generated_accessor()\n"
)

# (S3 / ADMISSIBILITY) An F2P-shaped input for the install case, built fresh and
# checked against the precondition CONJUNCT BY CONJUNCT: a namespace where
# other_name() is present (bound to some token), the accessor name is ABSENT, and
# the two names differ — i.e. a plain field-with-choices class carrying no
# author-written accessor. If any Requires conjunct could not be established for
# this normal input the Assert fails => PRECOND-TOO-STRONG. The real `cls` is
# then handled by the gold body unchanged, so the function is still correct.
# NOTE: the probe exercises the PREDICATE rather than making a self-call. A
# self-call would have to discharge Pt (MustTerminate) with an unchanged measure,
# which needs a Decreases the spec does not carry — that would be a proof gap in
# the probe, not a precondition defect, and would make this case report
# PRECOND-TOO-STRONG for the wrong reason. Bind the dict literal to a typed local
# FIRST (no '# type:' on a bare expression) and use distinct name tokens.
_ADMISS_INSTALL = _swap_install(
    "    probe = {}  # type: Dict[int, int]\n"
    "    probe[other_name()] = 7\n"
    "    Assert(dict_pred(probe))\n"
    "    Assert(other_name() + 1 not in probe)\n"
    "    Assert(other_name() in probe)\n"
    "    Assert(other_name() != other_name() + 1)\n"
    "    cls[accessor_name] = generated_accessor()\n"
)

# (S4 / ADMISSIBILITY) The preserve case admits a normal F2P-shaped input: a class
# that ALREADY provides an author-defined accessor (identity != generated) under
# the name, plus an unrelated attribute — the exact override-present scenario the
# F2P pins. Every preserve Requires conjunct (accessor_name in cls; other_name()
# in cls; other_name() != accessor) is asserted of it, plus the author identity
# being distinct from the generated one, so the probe is the real scenario and not
# a degenerate one. If any conjunct could not be met => PRECOND-TOO-STRONG. Same
# predicate-not-self-call note as S3.
_ADMISS_PRESERVE = _swap_preserve(
    "    probe = {}  # type: Dict[int, int]\n"
    "    probe[other_name()] = 7\n"
    "    probe[other_name() + 1] = 42  # an author-defined accessor (!= generated)\n"
    "    Assert(dict_pred(probe))\n"
    "    Assert(other_name() + 1 in probe)\n"
    "    Assert(probe[other_name() + 1] != generated_accessor())\n"
    "    Assert(other_name() in probe)\n"
    "    Assert(other_name() != other_name() + 1)\n"
    "    if accessor_name not in cls:\n"
    "        cls[accessor_name] = generated_accessor()\n"
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) PRESERVE-OVERWRITE — the EXACT prepatch bug (model_prepatch.py). Drops the
# guard and unconditionally installs the generated accessor, overwriting the
# author-defined one that the precondition guarantees is present. Its faithful
# real patch is the base_commit `setattr(cls, 'get_%s_display'%name,
# partialmethod(...))` with NO hasattr guard — exactly the regression: it clobbers
# a hand-written get_foo_bar_display, so the F2P test
# (FooBar(foo_bar=1).get_foo_bar_display() == 'something') sees the generated
# label 'foo' instead and FAILS — it would NOT resolve.
# Rejection source: Pp2 `cls[accessor_name] == Old(cls[accessor_name])`. The
# overwrite sets cls[accessor_name] == generated_accessor() (==0); the author
# identity Old(cls[accessor_name]) is unconstrained (any token), so the verifier
# cannot prove it equals 0 — Pp2 fails. (This is the clause G-DIFF reports
# model_prepatch.py:97 failing.)
_RIVAL_PRESERVE_OVERWRITE = _swap_preserve(
    "    cls[accessor_name] = generated_accessor()\n"
)

# (U2) INSTALL-NOOP / partial-domain — handles nothing on the install case: leaves
# the namespace untouched, so no accessor is installed. A faithful real patch of
# this shape would guard so tightly that the generated accessor is NEVER installed
# (e.g. the always-true guard), so a plain field-with-choices class has no
# get_<f>_display at all — the choices-and-display P2P tests
# (test_choices_and_field_display, test_iterator_choices, ...) would break: no
# accessor to call. It would NOT resolve.
# Rejection source: Pi1 `accessor_name in cls`. The precondition fixes
# accessor_name not in cls and the impl adds nothing, so the name is provably
# absent post-state — Pi1 fails (and hence Pi2).
_RIVAL_INSTALL_NOOP = _swap_install(
    "    pass\n"
)

# (U3) INSTALL-WRONG-IDENTITY / partial-domain — installs the WRONG callable under
# the accessor name: it binds `other_name()` (==1, a stand-in for some unrelated
# identity) instead of the generated display accessor `generated_accessor()`
# (==0). A faithful real patch of this shape installs a *different* method as the
# field's get_<f>_display, so calling it returns the wrong thing — the
# choices-and-display P2P tests (the generated accessor must return the choice
# label) break. It would NOT resolve.
# Rejection source: Pi2 `cls[accessor_name] == generated_accessor()`. The impl
# makes cls[accessor_name] == other_name() (==1) != generated_accessor() (==0),
# so Pi2 fails. (other_name() != accessor_name by precond, so the write lands
# on the accessor key.)
_RIVAL_INSTALL_WRONG = _swap_install(
    "    cls[accessor_name] = other_name()\n"
)

# (U4) CLOBBER-OTHER (install case) — the value-level frame attack (the reachable
# analogue of frame-mutation, since cls is full-perm not read-only). Installs the
# accessor correctly AND clobbers the unrelated attribute other_name() with the
# generated identity. A faithful real patch of this shape would, while installing
# the display accessor, also overwrite some OTHER attribute the class already
# carries — silently corrupting unrelated class state; the P2P tests that depend
# on those attributes (e.g. an existing method/field binding) break. It would NOT
# resolve.
# Rejection source: Pf `cls[other_name()] == Old(cls[other_name()])`. The impl
# sets cls[other_name()] == generated_accessor() (==0); Old(cls[other_name()]) is
# unconstrained, so the verifier cannot prove it equals 0 — Pf fails. This is the
# frame clause; if it verified, the frame guarantee would be hollow => SPEC-TOO-WEAK.
_RIVAL_CLOBBER_OTHER_INSTALL = _swap_install(
    "    cls[accessor_name] = generated_accessor()\n"
    "    cls[other_name()] = generated_accessor()\n"
)

# (U5) CLOBBER-OTHER (preserve case) — the same value-level frame attack on the
# preserve function: does the correct no-op on the accessor (preserving it) but
# clobbers the unrelated attribute other_name(). Same faithful-patch story as U4
# (corrupts an unrelated class attribute during assembly). It would NOT resolve.
# Rejection source: Pf `cls[other_name()] == Old(cls[other_name()])` — the write
# breaks it; the accessor clauses Pp1/Pp2 still hold, so this isolates the frame
# clause. If it verified => SPEC-TOO-WEAK (frame hollow in the preserve case).
_RIVAL_CLOBBER_OTHER_PRESERVE = _swap_preserve(
    "    if accessor_name not in cls:\n"
    "        cls[accessor_name] = generated_accessor()\n"
    "    cls[other_name()] = generated_accessor()\n"
)

# (U6) DIVERGE (preserve case) — the CONTROL-FLOW-EFFECT rival on the boundedness
# axis, and the one the whole write-only surface above is blind to. The step never
# hands control back: it re-enters itself on the same namespace and the same name.
# Note this is NOT dead code and NOT a permission trick — the self-call's Requires
# is re-established verbatim (the arguments are unchanged and nothing is written,
# so the pre-state still holds), so the recursion is genuinely taken, and each
# level's Ensures would discharge its caller's. Every value clause therefore holds
# VACUOUSLY, including Pq: not writing anything satisfies a frame condition
# perfectly. The clause that must catch it is Pt.
# Rejection source: Pt `Requires(MustTerminate(2))`. The obligation is a
# consumable budget, and the self-call would have to hand the callee an obligation
# of a STRICTLY SMALLER measure to prove progress; with the same arguments there
# is no smaller measure to give, so Viper's obligation-leak check fails at the
# call site. If it verified => SPEC-TOO-WEAK on the termination axis (every
# postcondition satisfiable by an operation that never finishes).
_RIVAL_DIVERGE_PRESERVE = _swap_preserve(
    "    preserve_existing_accessor(cls, accessor_name)\n"
)

# (U7) DIVERGE (install case) — the same rival on the install function, so the
# boundedness obligation is shown load-bearing in BOTH modeled behaviours rather
# than only in the one where gold happens to do no write. Same rejection source
# (Pt / the obligation-leak check at the self-call).
_RIVAL_DIVERGE_INSTALL = _swap_install(
    "    install_missing_accessor(cls, accessor_name)\n"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-preserve-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_PRESERVE_REORDER,
     "rationale": "structurally-different but CORRECT branch-reorder of the preserve "
                  "case (preserve-when-present, install-when-absent made explicit). The "
                  "precondition fixes accessor_name in cls so no write fires; cls is "
                  "unchanged and Pp1/Pp2/Pf hold trivially. No framing lemma is needed "
                  "(no write). If it fails to verify => SPEC-TOO-STRONG (over-fit to the "
                  "negated-guard spelling)."},
    {"id": "pos-install-unconditional", "kind": "soundness", "expect": "verify",
     "module": _POS_INSTALL_UNCONDITIONAL,
     "rationale": "the cheapest honest impl of the install case: an UNCONDITIONAL "
                  "install (the redundant guard removed, since the precondition fixes "
                  "accessor_name not in cls). Establishes Pi1/Pi2 and touches no other "
                  "key (Pf). Must verify; if not => SPEC-TOO-STRONG. The oracle "
                  "generated_accessor() is the intended install value (grounded, not an "
                  "answer-key), so this also serves as the no-ungrounded-echo control."},
    {"id": "admiss-install-fresh", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_INSTALL,
     "rationale": "an F2P-shaped install input (a fresh namespace with other_name() "
                  "present, the accessor name absent, the two names distinct) is built "
                  "and install_missing_accessor's Requires is established on it conjunct "
                  "by conjunct. If the precondition cannot be met for this normal "
                  "field-with-choices-no-author-method input => PRECOND-TOO-STRONG. The "
                  "predicate is exercised directly rather than via a self-call, which "
                  "under the boundedness obligation Pt would need a Decreases measure the "
                  "spec does not carry (a proof gap in the probe, not a spec defect)."},
    {"id": "admiss-preserve-override-present", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_PRESERVE,
     "rationale": "an F2P-shaped preserve input (a namespace that already provides an "
                  "author-defined accessor, identity != generated, plus an unrelated "
                  "attribute) is built and preserve_existing_accessor's Requires is "
                  "established on it conjunct by conjunct. This is the exact "
                  "override-present scenario the F2P pins. If the precondition cannot be "
                  "met => PRECOND-TOO-STRONG. Predicate exercised directly, not via a "
                  "self-call (same Pt-measure note as admiss-install-fresh)."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-preserve-overwrite", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PRESERVE_OVERWRITE,
     "refinement": "this is the EXACT base_commit regression (model_prepatch.py): drop "
                   "the hasattr guard and unconditionally setattr the generated "
                   "partialmethod over an author-defined get_<f>_display. Its faithful "
                   "real patch clobbers the hand-written accessor, so the F2P test "
                   "FooBar(foo_bar=1).get_foo_bar_display() returns the generated label "
                   "'foo' instead of the author's 'something' — it FAILS the F2P, so it "
                   "would NOT resolve.",
     "rationale": "Rejection source: Pp2 `cls[accessor_name] == Old(cls[accessor_name])`. "
                  "The overwrite sets cls[accessor_name] == generated_accessor() (==0) "
                  "while Old(cls[accessor_name]) is the unconstrained author identity, so "
                  "the verifier cannot prove equality — Pp2 fails. This is precisely the "
                  "clause G-DIFF reports model_prepatch.py failing (the preserve clause). "
                  "If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-install-noop", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INSTALL_NOOP,
     "refinement": "leaves the namespace untouched in the install case — no accessor is "
                   "installed. A faithful real patch of this shape (a guard that never "
                   "fires) never installs get_<f>_display for a plain choices field, so "
                   "the choices-and-display P2P tests (test_choices_and_field_display, "
                   "test_iterator_choices, the translated-display tests) have no accessor "
                   "to call and break — it would NOT resolve.",
     "rationale": "Rejection source: Pi1 `accessor_name in cls`. The precondition fixes "
                  "accessor_name not in cls; the impl adds nothing, so the name is "
                  "provably absent post-state — Pi1 fails (and Pi2). If it verified => "
                  "SPEC-TOO-WEAK (the install obligation is hollow / partial-domain)."},
    {"id": "rival-install-wrong-identity", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INSTALL_WRONG,
     "refinement": "installs the WRONG callable identity under the accessor name "
                   "(other_name() instead of the generated display accessor). A faithful "
                   "real patch of this shape binds get_<f>_display to a different method "
                   "than partialmethod(cls._get_FIELD_display, field=self), so calling it "
                   "returns the wrong value (not the choice label) — the "
                   "choices-and-display P2P tests break. It would NOT resolve.",
     "rationale": "Rejection source: Pi2 `cls[accessor_name] == generated_accessor()`. "
                  "The impl makes cls[accessor_name] == other_name() (==1), which "
                  "!= generated_accessor() (==0); the write lands on the accessor key "
                  "(other_name() != accessor_name by precond). Pi2 fails. If it verified "
                  "=> SPEC-TOO-WEAK (the install identity is unpinned / partial-domain)."},
    {"id": "rival-clobber-other-install", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CLOBBER_OTHER_INSTALL,
     "refinement": "installs the accessor correctly but ALSO overwrites the unrelated "
                   "attribute other_name(). This is the reachable analogue of "
                   "frame-mutation (cls is full-perm, so the attack is value-level "
                   "corruption of an unrelated attribute, not a permission subversion). A "
                   "faithful real patch would, during display-accessor installation, "
                   "silently overwrite some OTHER attribute the class already carries; "
                   "P2P tests that depend on that attribute break — it would NOT resolve.",
     "rationale": "Rejection source: Pf `cls[other_name()] == Old(cls[other_name()])`. "
                  "The impl sets cls[other_name()] == generated_accessor() (==0) while "
                  "Old(cls[other_name()]) is unconstrained, so the verifier cannot prove "
                  "equality — Pf fails. The accessor clauses Pi1/Pi2 still hold, isolating "
                  "the frame clause. If it verified => SPEC-TOO-WEAK (frame guarantee "
                  "hollow)."},
    {"id": "rival-clobber-other-preserve", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CLOBBER_OTHER_PRESERVE,
     "refinement": "preserves the accessor correctly (the gold no-op) but clobbers the "
                   "unrelated attribute other_name() — same value-level frame attack on "
                   "the preserve function. A faithful real patch corrupts an unrelated "
                   "class attribute during assembly; the dependent P2P tests break. It "
                   "would NOT resolve.",
     "rationale": "Rejection source: Pf `cls[other_name()] == Old(cls[other_name()])` — "
                  "the extra write breaks it while Pp1/Pp2 still hold, isolating the "
                  "frame clause in the preserve case. If it verified => SPEC-TOO-WEAK "
                  "(frame guarantee hollow in the preserve case)."},
    {"id": "rival-diverge-preserve", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE_PRESERVE,
     "refinement": "the assembly step never hands control back: it re-enters itself on "
                   "the same namespace and the same accessor name. Its faithful real "
                   "patch is the choices branch re-entering the same contribute_to_class "
                   "step instead of installing, so model-class assembly never finishes "
                   "for ANY class with a choices field. The F2P "
                   "(test_overriding_FIELD_display) never runs to an assertion and every "
                   "choices-related P2P hangs with it — it would NOT resolve, and this "
                   "was measured: 0/1 F2P, 0/30 P2P.",
     "rationale": "Rejection source: Pt `Requires(MustTerminate(2))`. The recursion is "
                  "genuinely taken (the self-call re-establishes its own Requires "
                  "verbatim: same arguments, unchanged pre-state), and every VALUE clause "
                  "holds vacuously — Pp1/Pp2/Pf and even the quantified Pq frame, since "
                  "doing nothing forever respects a frame perfectly. Only the boundedness "
                  "obligation can see it: the self-call cannot hand the callee a strictly "
                  "smaller measure, so the obligation-leak check fails at the call site. "
                  "If it verified => SPEC-TOO-WEAK on the termination axis (the entire "
                  "postcondition surface satisfiable by a step that never finishes)."},
    {"id": "rival-diverge-install", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE_INSTALL,
     "refinement": "the same non-returning assembly step in the install case, where gold "
                   "does perform the write — so the rival is not merely 'gold's no-op "
                   "spelled as a loop'. Its faithful real patch hangs assembly of every "
                   "plain choices field (the common case), so nothing in the suite "
                   "completes. It would NOT resolve.",
     "rationale": "Rejection source: Pt, as for rival-diverge-preserve — the self-call "
                  "leaks the boundedness obligation. Carried in BOTH functions so the "
                  "obligation is shown load-bearing in both modeled behaviours, not only "
                  "in the one where gold happens to write nothing. If it verified => "
                  "SPEC-TOO-WEAK on the termination axis."},
]

# ===========================================================================
# AXIOM LANE — none.
# ===========================================================================
# meta.json: axioms == [] (no @ContractOnly axiom whose Ensures the proof
# consumes). The single A-tagged refinement step is an A-REFERENCE deep model —
# the guarded install spelled out in the impl region — NOT a consumed axiom.
# axiom_check.py / G-AX already validates that deep model == the real
# `Field.contribute_to_class` display-accessor binding (preserve vs install,
# both declaration orders) over 4 boundary + 2000 fuzz real-Django model-class
# assemblies, driving BOTH the gold-guarded and the base_commit-unguarded states
# at runtime. There is therefore nothing to falsify against a real callee in this
# lane (G-AX is the operative check, not PBT).
AXIOM_TESTS = []
