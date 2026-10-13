"""properties.py — G-PBT falsification battery for django__django-14672 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or discharges
a ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_m2mIdentity``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a four-input identity-key domain):

  m2mIdentity
      (base : List HVal) (through : HVal)
      (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal
      result = base ++ [through, canonTF throughFields, dbConstraint]

  The result is the relation's comparison/identity KEY: the unchanged inherited
  prefix ``base``, then the ``through`` component, then the field-name sequence
  in CANONICAL HASHABLE form (``canonTF``), then the ``dbConstraint`` flag.
  ``FieldSeq`` has three shapes: ``.absent`` (no sequence supplied),
  ``.astuple xs`` (already-hashable form) and ``.aslist xs`` (the non-hashable
  form). ``canonTF`` sends ``.absent`` to ``hnone`` and BOTH present shapes to
  ``htuple (xs.map hstr)`` — i.e. a present sequence is always canonicalised to
  the SAME hashable tuple regardless of which container it arrived in, which is
  precisely what makes the whole key hashable even for the list shape.

  The single top-level clause is a positional list equality that folds four
  independent, inseparable component decisions, one per input binder:

    * the inherited prefix ``base`` is carried VERBATIM as the key's head
      (attacked by ``weak-drop-base-prefix``);
    * the ``through`` component sits at position ``|base|`` (attacked by
      ``weak-drop-through``);
    * the field-name slot is EXACTLY ``canonTF throughFields`` — present shapes
      canonicalise to a hashable tuple (never a list: ``weak-prepatch-listform``),
      the absent shape stays ``hnone`` (never a present tuple:
      ``weak-absent-as-empty-tuple``), a present TUPLE stays present (never the
      absent marker: ``weak-tuple-as-absent``), the tuple's MEMBERSHIP is the
      full mapped sequence (not the empty tuple: ``weak-drop-names``; not a
      strict suffix: ``weak-truncate-first-name``);
    * the ``dbConstraint`` flag is carried VERBATIM as the key's tail
      (attacked by ``weak-drop-dbconstraint``).

ADVERSARIAL READ of the nagini classes on this carrier (see ``assessment`` for
the full port ledger):

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the input
    sequence at a half (read-only) permission and makes a MANDATORY rival write
    into it (``names.append(0)``), rejected for insufficient permission. Lean is
    referentially transparent: the four inputs are immutable values, there is no
    heap fraction to overwrite and no aliasing to exploit, so this class has NO
    expressible instance here and NO substitute is fabricated for it. The
    behavioral concern behind it — that the UNCHANGED components are carried
    verbatim rather than disturbed — IS defended here, by the frame-preservation
    rivals ``weak-drop-base-prefix`` / ``weak-drop-through`` /
    ``weak-drop-dbconstraint``, which attack exactly the positions a
    non-copy-preserving impl would corrupt. The VALUE-LEVEL image of nagini's
    ``names.append(0)`` is additionally expressible and was checked: an impl that
    canonicalises ``xs ++ ["_"]`` instead of ``xs`` is refuted by this spec at
    ``.aslist ["a"]`` (its witness elaborates on that rival and fails on gold).
    It is not shipped as a separate case because it is subsumed — its divergence
    is a membership error in the field slot, exactly the clause
    ``weak-drop-names`` and ``weak-truncate-first-name`` already pin — but it
    confirms the class is not inexpressible here, only redundant.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. ``canonTF`` is a fully-unfolded ``@[simp]``
    function of the input alone (no ``opaque``/``axiom``; meta.json axioms == []
    and deep_model_references records ``canonTF`` as an A-reference validated by
    G-AX, NOT a consumed answer key). There is no oracle an impl could echo. The
    honest analogue is the POSITIVE CONTROL below.

  * PARTIAL-DOMAIN — APPLIES and is load-bearing. ``weak-prepatch-listform`` is
    the pre-patch reborn (a present LIST left in list form), refuted on the
    ``.aslist`` sub-domain; ``weak-absent-as-empty-tuple`` diverges only on the
    ``.absent`` boundary; ``weak-drop-names`` / ``weak-truncate-first-name``
    attack the membership of a present sequence.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``simp only [...]`` is tuned to the
frozen ``Id.run do`` form — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input. Each witness unfolds the predicate, the
impl and ``canonTF`` at that literal input and lets ``simp`` decide the resulting
concrete ``List HVal`` equation by constructor disjointness / element mismatch:

  * against the RIVAL the equation is FALSE, ``simp`` reduces the hypothesis to
    ``False`` and closes the goal — exit 0;
  * against GOLD the equation is TRUE, ``simp`` PROVES it, the hypothesis
    collapses to ``True``, and ``False`` is left unsolved — exit 1, with the
    gold-side error ``h : True ⊢ False``.

That error is what makes the gold-side exit code admissible evidence: ``h : True``
is a report that ``simp`` DISCHARGED the spec's equation for the frozen impl at
this input, i.e. that gold is correct there. It is a plain evaluation of the
claim, not a scaffolding artifact, and it is reached only because the tactic
script mentions NO value that either side computes — the build's verdict is
decided by the claim and by the impl in the file, and by nothing else.

This is a REPAIR of an earlier witness shape that did not have that property, and
the difference was measured rather than argued, so it is recorded here as the
reason the current shape is what it is. The earlier witnesses reduced the rival's
impl to a hardcoded value list by ``show <impl applied> = <rival's literal> from
rfl`` inside ``simp only``. That literal is the rival's value, so the ``show``
step cannot typecheck against gold — and it fails there BEFORE the claim is ever
consulted. Measured consequence: dropping the ``¬`` (asserting the spec HOLDS at
gold's own true value, the OPPOSITE of a refutation) still produced rival exit 0
and gold exit 1, with a gold-side first error byte-identical to the real
witness's modulo the metavariable index. Gold's exit code therefore carried no
information about what was being claimed, and a forgery asserting gold is CORRECT
at that input cleared both halves of the discrimination check. Lean also reported
the ``show ... from rfl`` as an UNUSED simp argument on the rival build, which is
the same fact from the other side: it contributed nothing to the refutation and
served only to break the gold build.

The current shape was verified to track the claim on both sides, for every reject
case: the refutation elaborates on its rival (exit 0) and fails on gold with
``h : True ⊢ False`` (exit 1), while the FLIPPED claim — the spec asserted to
HOLD at the same input — inverts both, elaborating on gold (exit 0) and failing
on its rival (exit 1). Opposite claims give opposite exit codes on both subjects,
which is what "the witness discriminates" means.

BINDER COVERAGE. All four input binders are attacked by a dedicated rival and
varied across the reject witnesses:
  * ``base`` — moved between ``[]`` and ``[hstr "P"]`` and attacked by
    ``weak-drop-base-prefix``.
  * ``through`` — moved between ``hnone`` and ``hstr "T"`` and attacked by
    ``weak-drop-through``.
  * ``throughFields`` — witnesses pin all three tags: ``.absent``
    (``weak-absent-as-empty-tuple`` and the three frame rivals), ``.aslist``
    (``weak-prepatch-listform`` / ``weak-drop-names`` /
    ``weak-truncate-first-name``, with one- and two-element carried lists) and
    ``.astuple`` (``weak-tuple-as-absent``). Five rivals cover the list-form /
    absent / tuple-form / membership / off-by-one sub-decisions.
  * ``dbConstraint`` — moved between ``hnone`` and ``hstr "F"`` and attacked by
    ``weak-drop-dbconstraint``.
The reject witnesses probe many distinct input points (``pts`` > 1), so the
battery exercises the spec's dependence on each binder rather than one point.

AXIOM lane: EMPTY. The canonicalisation is modeled DEEPLY as ``canonTF`` (an
A-reference validated == the real standard-library routine by G-AX, re-run as its
own gate), not consumed as an axiom; meta.json axioms == []. Nothing in this
bundle's proof rests on a ``@ContractOnly``/``axiom`` contract, so the axiom lane
has nothing to execute here. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-14672"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every replacement
# lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [canonTF throughFields]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

_PROOF_BODY = (
    "  intro base through throughFields dbConstraint\n"
    "  unfold problem_spec_m2mIdentity implementation_m2mIdentity\n"
    "  simp only [Id.run, pure, List.append_assoc, List.cons_append, List.nil_append]"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with ONLY the gold impl body replaced."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each is a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PARTIAL-DOMAIN (= the pre-patch bug): a present sequence supplied as a LIST is
# left in list form in the key instead of being canonicalised to a tuple.
# Correct on the absent/tuple sub-domains, wrong for the list shape.
_LISTFORM = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [(match throughFields with\n"
    "    | .absent => HVal.hnone\n"
    "    | .astuple xs => HVal.htuple (xs.map HVal.hstr)\n"
    "    | .aslist xs => HVal.hlist (xs.map HVal.hstr))]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# ABSENT-AS-EMPTY-TUPLE: an absent sequence is mapped to a present empty tuple
# instead of the absent marker. Correct on every present sequence; diverges only
# on the absent boundary.
_ABSENT_TUPLE = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [(match throughFields with\n"
    "    | .absent => HVal.htuple []\n"
    "    | .astuple xs => HVal.htuple (xs.map HVal.hstr)\n"
    "    | .aslist xs => HVal.htuple (xs.map HVal.hstr))]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# DROP-NAMES: a present sequence is canonicalised to the CONSTANT empty tuple,
# collapsing every distinct sequence to one identity component. Right kind
# (hashable tuple), wrong membership for any non-empty sequence.
_DROP_NAMES = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [(match throughFields with\n"
    "    | .absent => HVal.hnone\n"
    "    | .astuple _ => HVal.htuple []\n"
    "    | .aslist _ => HVal.htuple [])]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# TUPLE-AS-ABSENT: the ALREADY-HASHABLE `.astuple` shape is collapsed to the
# absent marker instead of being carried as its tuple of names. Correct on
# `.absent` and on the `.aslist` shape (so the list-form leg every other rival
# probes still passes); diverges only on the `.astuple` tag.
_TUPLE_ABSENT = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [(match throughFields with\n"
    "    | .absent => HVal.hnone\n"
    "    | .astuple _ => HVal.hnone\n"
    "    | .aslist xs => HVal.htuple (xs.map HVal.hstr))]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# TRUNCATE-FIRST-NAME: off-by-one on the sequence — drops the leading name.
# Correct only on the empty sequence (it agrees with gold at `.aslist []`);
# wrong for EVERY non-empty sequence, including a single-element one.
_TRUNCATE = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [(match throughFields with\n"
    "    | .absent => HVal.hnone\n"
    "    | .astuple xs => HVal.htuple ((xs.map HVal.hstr).drop 1)\n"
    "    | .aslist xs => HVal.htuple ((xs.map HVal.hstr).drop 1))]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# DROP-BASE-PREFIX: the inherited prefix is discarded (started from the empty
# list instead of `base`), so the unchanged head of the key is lost.
_DROP_BASE = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := []\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [canonTF throughFields]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# DROP-THROUGH: the `through` component is omitted from the key entirely.
_DROP_THROUGH = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [canonTF throughFields]\n"
    "  acc := acc ++ [dbConstraint]\n"
    "  return acc"
)

# DROP-DBCONSTRAINT: the trailing flag is omitted from the key entirely.
_DROP_DB = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal := Id.run do\n"
    "  let mut acc : List HVal := base\n"
    "  acc := acc ++ [through]\n"
    "  acc := acc ++ [canonTF throughFields]\n"
    "  return acc"
)

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — the
# mutable-accumulator `Id.run do` is dropped for a direct functional append
# expression. Same value on every input, so it must satisfy the frozen spec
# (statement byte-identical, no new lemma/axiom/assumption token).
#
# Honest about how much this proves: the reshape is close enough to gold that the
# FROZEN tactic body still closes it too (measured — the frozen script elaborates
# against this impl at exit 0, reporting only that its `Id.run` simp argument has
# become unused). So this case is not evidence that the spec admits a proof
# requiring a genuinely different argument; it is evidence of the weaker and still
# necessary thing the soundness lane is for — that a faithful impl written in a
# different SHAPE is not rejected. The bare `simp` below is the honest proof for
# the new shape rather than a re-derivation the frozen script could not do.
# Reshapes that do need their own argument (an explicit `match` on the tag closed
# by `cases throughFields <;> simp [canonTF]`, and a `foldl` spelling closed by
# `simp [List.foldl]`) were checked to verify as well, so the spec is not too
# strong on them either; they are not shipped as separate cases because they
# attest the same one-clause obligation this case already covers.
_POS_IMPL = (
    "def implementation_m2mIdentity\n"
    "    (base : List HVal) (through : HVal)\n"
    "    (throughFields : FieldSeq) (dbConstraint : HVal) : List HVal :=\n"
    "  base ++ [through] ++ [canonTF throughFields] ++ [dbConstraint]"
)
_POS_PROOF = (
    "  intro base through throughFields dbConstraint\n"
    "  unfold problem_spec_m2mIdentity implementation_m2mIdentity\n"
    "  simp"
)


def _witness(base, through, tf, db, lit):
    """A refutation witness stating the spec predicate at one concrete input.

    The tactic unfolds BOTH sides of the spec's equality at the literal input —
    the predicate, the impl, and `canonTF` — and lets `simp` decide the resulting
    concrete `List HVal` equation by constructor disjointness / element mismatch.
    Nothing in the script mentions the value either side computes, so what the
    build reports is decided by the CLAIM and by the impl in the file, and by
    nothing else:

      * against the RIVAL the equation is false, `simp` reduces `h` to `False`
        and closes the goal (exit 0);
      * against GOLD the equation is TRUE, so `simp` proves it, `h` collapses to
        `True`, and the goal `False` is left unsolved (exit 1) — the gold-side
        error is `h : True ⊢ False`, i.e. a report that gold SATISFIES the spec
        at this input, which is exactly the semantic refutation the two-build
        check is entitled to read as "gold is correct here".

    `lit` is the value the rival computes at this input. It is carried as a
    COMMENT only: naming it in the tactic would make the script's success depend
    on a hardcoded literal rather than on the claim, which is how a witness stops
    discriminating (see the WITNESSES note above).
    """
    return (
        f"-- rival's value at this input: {lit}\n"
        f"example : ¬ problem_spec_m2mIdentity {base} {through} {tf} {db}\n"
        f"    (implementation_m2mIdentity {base} {through} {tf} {db}) := by\n"
        "  intro h\n"
        "  simp [problem_spec_m2mIdentity, implementation_m2mIdentity,\n"
        "    canonTF] at h\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify (else SPEC-TOO-STRONG: a faithful correct impl rejected).
    # The `theorem correct_m2mIdentity` STATEMENT is byte-identical; the tactic
    # body is re-proved for the new (non-`Id.run do`) shape. No helper lemma,
    # axiom, or assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-functional-append",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` "
            "scaffold and spells the key as one functional append expression "
            "(`base ++ [through] ++ [canonTF throughFields] ++ [dbConstraint]`) "
            "computes the same list on every input, so it must satisfy `result = "
            "base ++ [through, canonTF throughFields, dbConstraint]`; if it "
            "cannot, the spec is SPEC-TOO-STRONG. Proof: after `unfold`, `simp` "
            "normalises the nested appends to the spec's flat list — no new "
            "declaration, axiom, or assumption token. Scope of the claim, "
            "measured: the frozen tactic body also still closes this impl, so the "
            "case attests that a faithful impl in a different SHAPE is admitted, "
            "not that the spec admits a proof the frozen script could not find. "
            "Two reshapes that DO need their own argument (an explicit `match` on "
            "the tag; a `foldl` spelling) were separately checked to verify."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the normal, F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # behavior is total, so `∀` is unguarded), so nagini's precondition-admission
    # probe has no binder to attack; the honest analogue is to discharge the spec
    # predicate at the F2P ground input (a field-name sequence supplied as a LIST
    # — the exact shape the F2P exercises) inside the proof region, alongside the
    # frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-list-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_m2mIdentity [] HVal.hnone "
            "(.aslist [\"event\", \"invitee\"]) HVal.hnone\n"
            "      (implementation_m2mIdentity [] HVal.hnone "
            "(.aslist [\"event\", \"invitee\"]) HVal.hnone) := by\n"
            "    unfold problem_spec_m2mIdentity implementation_m2mIdentity\n"
            "    simp\n"
            + _PROOF_BODY,
        ),
        "rationale": (
            "the obligation is discharged at the F2P ground input (a field-name "
            "sequence supplied as a LIST, `['event','invitee']`, the exact shape "
            "the F2P exercises) by `simp`, then the frozen obligation is closed "
            "verbatim. Verifies (else the spec is unsatisfiable at the normal "
            "input, the analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
            "theorem STATEMENT is byte-identical, the ground instance is a `have` "
            "inside the existing tactic body, and no new declaration/axiom/`sorry`."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P (so a verifying rival is a
    # true verify-does-not-imply-resolve break, not an artifact) and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-prepatch-listform",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LISTFORM),
        "refinement": (
            "this is exactly the pre-patch behavior: a field-name sequence "
            "supplied as a LIST is placed into the identity key still in list "
            "form (never canonicalised to a hashable tuple). Its faithful real "
            "patch is the unpatched repo, where deriving a hash from the key "
            "raises `TypeError: unhashable type: 'list'` whenever such a relation "
            "is placed in a set during the model system checks — the exact failure "
            "the F2P observable exercises. It does NOT resolve; this is the leg's "
            "prepatch."
        ),
        "rationale": (
            "REJECT from the clause `result = base ++ [through, canonTF "
            "throughFields, dbConstraint]`: at `throughFields = .aslist [\"a\"]` "
            "the spec's field-slot is `htuple [hstr \"a\"]` (a hashable tuple) but "
            "the rival emits `hlist [hstr \"a\"]` (a list). Refuted on the "
            "`.aslist` sub-domain — the shape the fix targets. Q on the other tags "
            "still holds, so the divergence is confined to the list shape."
        ),
        "witness": _witness(
            "[]", "HVal.hnone", "(.aslist [\"a\"])", "HVal.hnone",
            "[HVal.hnone, HVal.hlist [HVal.hstr \"a\"], HVal.hnone]"),
    },
    {
        "id": "weak-absent-as-empty-tuple",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ABSENT_TUPLE),
        "refinement": (
            "mapping an ABSENT sequence to a present empty tuple instead of the "
            "absent marker changes the identity of a relation declared WITHOUT a "
            "field-name sequence, so it no longer compares/hashes equal to the "
            "unchanged sibling relations that genuinely carry the absent marker "
            "there. It diverges from the standard-library routine (absent stays "
            "absent) on the absent sub-domain, so it is not the faithful fix and "
            "would break identity/hash equality for the common no-sequence case. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same clause on the `.absent` sub-domain: the spec's "
            "field-slot is `canonTF .absent = hnone` but the rival emits "
            "`htuple []`. Correct on every present sequence (so this is a true "
            "PARTIAL-DOMAIN break on the absent boundary), caught only because the "
            "field-slot is pinned to `canonTF` and `hnone ≠ htuple []`."
        ),
        "witness": _witness(
            "[]", "HVal.hnone", ".absent", "HVal.hnone",
            "[HVal.hnone, HVal.htuple [], HVal.hnone]"),
    },
    {
        "id": "weak-drop-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_NAMES),
        "refinement": (
            "canonicalising every present sequence to the CONSTANT empty tuple is "
            "hashable but collapses all distinct field-name sequences to the same "
            "identity component, so two relations with different sequences hash "
            "and compare equal — the very distinction the m2m-through checks rely "
            "on. It preserves neither the names nor the ability to tell relations "
            "apart, so it is not the faithful fix and would break the "
            "different-through-fields F2P. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same clause on the MEMBERSHIP of a present sequence: "
            "the field-slot must be `htuple (xs.map hstr)` but the rival emits "
            "`htuple []` for any non-empty `xs`. Right kind (hashable tuple) and "
            "correct on the empty/absent sub-domains, so the divergence is "
            "confined to the element content. Probed with a non-empty `base` and "
            "non-`hnone` `through`/`dbConstraint`, varying those binders too."
        ),
        "witness": _witness(
            "[HVal.hstr \"P\"]", "(HVal.hstr \"T\")", "(.aslist [\"a\",\"b\"])",
            "(HVal.hstr \"F\")",
            "[HVal.hstr \"P\", HVal.hstr \"T\", HVal.htuple [], HVal.hstr \"F\"]"),
    },
    {
        "id": "weak-truncate-first-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_TRUNCATE),
        "refinement": (
            "an off-by-one canonicaliser that drops the leading name yields a "
            "distinct identity component for any sequence of length >= 1 (e.g. "
            "`['x','y']` becomes `('y',)`), breaking hash/identity equality with "
            "the correctly-canonicalised sibling relation. Correct only on the "
            "EMPTY sequence; wrong for every non-empty one, including the "
            "multi-element F2P input. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the same clause on the leading element: `((xs.map "
            "hstr).drop 1)` differs from `xs.map hstr` at the first element for "
            "any sequence of length >= 1, so the field-slot's tuple loses its "
            "head. Right kind, hashable; a boundary a byte-fuzzer would not "
            "isolate. Distinct from `weak-drop-names`, which emits the CONSTANT "
            "empty tuple: this one preserves the tail, so the two differ on any "
            "sequence of length >= 2 — refuted here at a two-element input, "
            "where the surviving tail `('y',)` is itself the wrong membership."
        ),
        "witness": _witness(
            "[]", "HVal.hnone", "(.aslist [\"x\",\"y\"])", "HVal.hnone",
            "[HVal.hnone, HVal.htuple [HVal.hstr \"y\"], HVal.hnone]"),
    },
    {
        "id": "weak-tuple-as-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_TUPLE_ABSENT),
        "refinement": (
            "a canonicaliser that returned the absent marker for a sequence "
            "supplied in the ALREADY-HASHABLE container would erase the field "
            "names of every relation declared with a tuple, making it "
            "hash/compare equal to a relation declared with no sequence at all. "
            "It diverges from the standard-library routine (which returns a "
            "present sequence unchanged apart from canonicalising its elements) "
            "on the tuple sub-domain, so it is not the faithful fix: it would "
            "collapse the two-relations-with-different-sequences distinction for "
            "the tuple shape. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause `result = base ++ [through, canonTF "
            "throughFields, dbConstraint]` on the `.astuple` sub-domain: at "
            "`throughFields = .astuple [\"a\",\"b\"]` the spec's field-slot is "
            "`htuple [hstr \"a\", hstr \"b\"]` but the rival emits `hnone`. This "
            "is the one FieldSeq tag no other rival's witness pins: every other "
            "reject case states its refutation at `.absent` or `.aslist`, so "
            "before this case an impl could mishandle the tuple shape alone and "
            "no witness would have discriminated it."
        ),
        "witness": _witness(
            "[]", "HVal.hnone", "(.astuple [\"a\",\"b\"])", "HVal.hnone",
            "[HVal.hnone, HVal.hnone, HVal.hnone]"),
    },
    {
        "id": "weak-drop-base-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_BASE),
        "refinement": (
            "discarding the inherited prefix builds the key from only the m2m-"
            "specific components, dropping the components every related relation "
            "shares. Two relations that differ ONLY in their inherited prefix "
            "would then hash/compare equal, and relations that should differ from "
            "unrelated ones lose the distinguishing head — corrupting the "
            "comparison key the identity is for. This is not a copy-preserving "
            "canonicalisation of one slot; it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause on the HEAD of the key: the spec pins the "
            "prefix to the input `base`, but the rival starts from `[]`. Refuted "
            "with a non-empty `base = [hstr \"P\"]` — the binder this rival "
            "abuses, held at `[]` by the field-slot rivals — so the frame "
            "component `base` is exercised. This is the referentially-transparent "
            "analogue of the nagini frame-mutation concern: the UNCHANGED prefix "
            "must be carried verbatim."
        ),
        "witness": _witness(
            "[HVal.hstr \"P\"]", "HVal.hnone", ".absent", "HVal.hnone",
            "[HVal.hnone, HVal.hnone, HVal.hnone]"),
    },
    {
        "id": "weak-drop-through",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_THROUGH),
        "refinement": (
            "omitting the `through` component drops the intermediary-model slot "
            "from the key, so two relations that differ only in their through "
            "model would hash/compare equal. The identity must distinguish them; "
            "an impl that leaves the slot out is not a canonicalisation of the "
            "field-name slot at all and would break the two-relations-same-model "
            "F2P. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the clause on the position immediately after `base`: the "
            "spec places `through` there, but the rival's key skips straight to "
            "the field slot. Refuted with a distinct `through = hstr \"T\"` and a "
            "distinct `dbConstraint = hstr \"F\"`, varying both those binders; "
            "`through` is the binder this rival abuses."
        ),
        "witness": _witness(
            "[]", "(HVal.hstr \"T\")", ".absent", "(HVal.hstr \"F\")",
            "[HVal.hnone, HVal.hstr \"F\"]"),
    },
    {
        "id": "weak-drop-dbconstraint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_DB),
        "refinement": (
            "omitting the trailing flag drops the `db_constraint` slot from the "
            "key, so two relations that differ only in that flag would hash and "
            "compare equal. The identity must reflect it; an impl that leaves the "
            "tail off is not a copy-preserving canonicalisation of one slot and "
            "would collapse relations the checks keep distinct. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the clause on the TAIL of the key: the spec ends with "
            "the input `dbConstraint`, but the rival's key omits it. Refuted with "
            "a distinct `dbConstraint = hstr \"F\"` — the binder this rival "
            "abuses, held at `hnone` by the field-slot rivals — so the frame "
            "component `dbConstraint` is exercised."
        ),
        "witness": _witness(
            "[]", "HVal.hnone", ".absent", "(HVal.hstr \"F\")",
            "[HVal.hnone, HVal.hnone]"),
    },
]


# No consumed axioms and no ungrounded oracles: the canonicalisation is modeled
# deeply as `canonTF` (an A-reference validated == the real standard-library
# routine by G-AX, re-run as its own gate) and every clause is grounded in the
# four inputs, so there is no in-model axiom obligation for the PBT axiom lane to
# re-discharge here.
AXIOM_TESTS = []
