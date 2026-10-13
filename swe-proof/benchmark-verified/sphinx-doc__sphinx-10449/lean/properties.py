"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10449 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models THREE fractional-permission functions — a kind classifier
(``suppress_for_kind``), a return-presence scan (``has_return_field_in``) and
the field-appender (``append_return_type``, the fix site) — with the appender
returning an ``Optional[List[int]]`` (None vs the produced field content). This
Lean bundle models the SINGLE purely-functional core: one total function that,
given the fields already present, the ordered ``(name, annotation)`` pairs, and
the suppress flag, RETURNS the whole resulting field list. The nagini
appender's None/some-content distinction is subsumed into whether the returned
list carries a trailing ``rtype`` field and what body text it carries. Most
nagini cases therefore carry over as attacks on ONE clause of the one modeled
obligation; the mapping of each nagini case to its Lean counterpart (or its
principled omission) is in the module ``assessment`` at the foot of this file.

DEFENDED SURFACE (one modeled behavior). The postcondition pins ``result`` to a
single grounded computation over the inputs — the existing fields, then the
per-name generated fields (in order), then at most one return-type field:

    result = existing
             ++ genParamTypeFields existing annotations
             ++ genReturnField existing annotations suppressTrivialReturn

so it has these independent top-level clauses, selected by the input:

  * (PREFIX) the already-present fields are preserved, in order, at the front;
  * (PERNAME) for each non-return annotation, a type field (unless a type is
    already declared) then a param field (unless already declared), in order;
  * (RETURN) the fix site: a single return-type field is appended only when a
    return entry is present AND no return type is already declared AND it is not
    suppressed — where suppression fires exactly when the flag is set and the
    return annotation is the trivial unit annotation; and when a field IS
    produced its body carries the object's OWN return annotation.

The BEHAVIOURAL DISCRIMINATOR (the fix): for a suppressed target whose return
annotation is the trivial unit, emit NO return-type field, while still emitting
(with the correct body) the return-type field for every non-trivial return
annotation and for non-suppressed targets. The pre-fix routine emitted the
trailing field unconditionally; the (RETURN)-clause rivals below ARE that
pre-fix behavior and its neighbouring mis-suppressions.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS *as a permission attack*. Lean is
    referentially transparent: an input carries no heap permission, there is no
    read-only half-permission to overwrite and no aliasing to exploit, so the
    nagini rivals' actual mechanism (writing into the read-only
    ``return_annotation`` / ``fields`` inputs) has no expressible instance.
    (nagini cases 3 ``frame-mutation-return-annotation`` and
    ``frame-mutation-fields-helper``.)

    But the BEHAVIOUR each of those rivals reached for is expressible, and one of
    them was initially left unprobed. The ``fields``-helper case attacks the
    return-presence scan; on this carrier that clause is attackable directly, on
    VALUE, by narrowing which existing field shapes the scan recognises — see
    ``weak-narrow-return-presence``, added after the scan clause was found to
    carry no rival of its own. The ``return_annotation`` case attacks the content
    of the produced field, which ``weak-content-fixed-unit`` already covers on
    value. So the permission MECHANISM is inexpressible; the clauses are not, and
    both now carry a rival.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs. There is no opaque
    answer key an implementation could echo, and no ``opaque`` callee at all —
    the whole classification/generation is modeled deeply. In its place the
    battery carries honest POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: never suppressing (pre-patch), suppressing
    for ANY return annotation (not just the trivial unit), and rendering a fixed
    unit body instead of the object's own return annotation. Plus the two
    unchanged-but-load-bearing structural clauses (prefix, per-name generation).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. Each was checked to
HOLD of its rival and to FAIL on the frozen solution, so it discriminates rather
than asserting a tautology.

Gold-side failure was not merely READ, it was FORGERY-TESTED, and the
distinction mattered: every witness here closes by handing the kernel a
decidable proposition, so ``decide`` returns a verdict that TRACKS THE CLAIM.
This was measured per case by building a second file differing from the witness
only in what it asserts — the claim with its ``¬`` dropped, i.e. asserting the
frozen solution is CORRECT at that input — against the frozen solution. For
every case the flipped claim VERIFIES on gold (exit 0) while the witness FAILS
(exit 1), and symmetrically the flipped claim fails against the rival: the exit
codes move with the claim, which is what makes them evidence.

Three of these witnesses originally closed with a bare ``simp [...]`` and were
replaced after that test, because they FAILED it. Their gold-side error read
like a refutation — ``unsolved goals ⊢ ¬pure [] = []`` — but the flipped claim
produced the byte-identical error modulo the negation (``⊢ pure [] = []``, also
exit 1): ``simp`` was failing to unfold ``pure`` regardless of what was
asserted, so gold's exit code carried no information and a witness asserting
the spec HOLDS there would have been recorded as a valid rejection. The
per-case notes record the measurement. The lesson generalizes on this carrier:
an ``unsolved goals ⊢ ¬x = x`` signature is NOT self-evidently semantic, since
a goal left standing because the tactic could not reduce it is indistinguishable
by exit code from one left standing because it is false.

Five of the six witnesses fix every input at a literal, so they bind nothing;
all five reduce to a decidable proposition and close by ``decide``.
The sixth (``weak-narrow-return-presence``) must condition: its rival differs
from the frozen impl only in how it TOKENIZES an existing field name, and
``tokenize`` is built on ``String.splitOn``, which does not reduce on this
carrier (measured: `rfl`, `decide` and `simp [tokenize]` all fail on
``tokenize "type return" = ["type", "return"]``). It therefore states the
refutation at a point described by hypothesis — the tokenization of its one
concrete field name — and the gate's consistency probe confirms that hypothesis
is satisfiable.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point: ``existing`` takes the empty
list, a non-empty unrelated already-present field, AND a field that declares a
type for the return position; ``annotations`` takes the empty list, a lone return
entry (trivial-unit AND non-trivial), and a per-name (non-return) entry;
``suppressTrivialReturn`` takes both settings. The six reject witnesses probe six
distinct inputs.

DIVERGENCE lane (F′): the frozen solution sets no
``loom.semantics.termination`` option at all — it is a plain Lean file whose
modeled function is a structurally-total ``Id.run do`` over a ``for`` on a
finite list, and the obligation is closed by an ordinary ``theorem``, with no
separate termination obligation for a verifier to discharge. So the "total"
disposition applies by construction rather than by setting: an impl that does
not terminate is not merely rejected, it is not DEFINABLE in the frozen impl
region without a token the variant scope already bans. Measured rather than
asserted: the only way to write a diverging rival here is ``partial def``, and
a ``partial def`` self-recursive rival was built (exit 1, rejected) — but its
refutation is NOT shippable as a reject case, because ``partial`` makes the
function opaque to the kernel. A witness against it was built and it FAILS the
discrimination requirement in the most direct way: conditioning the refutation
on the rival's output by hypothesis, the witness elaborates against the rival
(exit 0) AND against the frozen solution (exit 0) — vacuous, since it asserts
only that SOME output value contradicts the spec, which the hypothesis supplies
for free. ``partial`` is additionally a banned token for a shipped variant. The
class is therefore genuinely VACUOUS on this carrier, not a known hole: there
is no diverging impl expressible inside the impl region.

AXIOM lane: EMPTY here. The bundle consumes no ``axiom`` and declares no
``opaque`` (everything is modeled deeply). The nagini ``AXIOM_TESTS`` were also
empty; dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10449"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positive that
# re-proves, the proof region) so same_spec stays byte-identical.

# The whole return-type decision block of the impl (the fix site).
_I_RETURN = (
    "  match lookupReturn annotations with\n"
    "  | some ann =>\n"
    "      if !(hasReturnField existing) then\n"
    "        if ann == \"None\" && suppressTrivialReturn then\n"
    "          return fields\n"
    "        fields := fields ++ [⟨\"rtype\", ann⟩]\n"
    "  | none => pure ()\n"
    "  return fields"
)

# The rtype-field append (its body carries the object's own return annotation).
_I_RTYPE_BODY = "        fields := fields ++ [⟨\"rtype\", ann⟩]"

# The prefix seed: the returned list starts from the already-present fields.
_I_PREFIX = "  let mut fields := existing"

# The param-field append of the per-name loop.
_I_PARAM_APPEND = (
    "      if !(declaresParam existing name) then\n"
    "        fields := fields ++ [⟨\"param \" ++ name, \"\"⟩]\n"
)

# The suppress-guard `&&` (commuted by the fix-site positive control).
_I_SUPPRESS_GUARD = "        if ann == \"None\" && suppressTrivialReturn then"

# The whole per-name loop BODY (both generated appends). Reshaped by the
# per-name positive control into `genForName`'s own one-append-per-name form.
_I_LOOP_BODY = (
    "      if !(declaresType existing name) then\n"
    "        fields := fields ++ [⟨\"type \" ++ name, ann⟩]\n"
    "      if !(declaresParam existing name) then\n"
    "        fields := fields ++ [⟨\"param \" ++ name, \"\"⟩]\n"
)

# The return-presence guard of the impl (the scan that decides whether the
# existing fields ALREADY declare a return type).
_I_PRESENCE_GUARD = "      if !(hasReturnField existing) then\n"

# The head of the frozen proof body (admissibility inserts a `have` after it).
_P_HEAD = (
    "  intro existing annotations suppressTrivialReturn\n"
    "  have loop"
)

# The frozen `loop` lemma of the proof region, verbatim: the auxiliary `have`
# that pins the per-name accumulation to `genParamTypeFields`. A positive that
# genuinely reshapes the loop body must restate this `have` in the reshaped
# branch shape, so it is re-proven rather than reused. It is a `have` INSIDE the
# frozen tactic body, so the theorem statement stays byte-identical and no new
# top-level declaration is introduced.
_P_LOOP = (
    "  have loop : ∀ (anns : List (String × String)) (acc : List DocField),\n"
    "      (forIn (m := Id) anns acc (fun entry r =>\n"
    "        if (entry.1 == \"return\") = true then ForInStep.yield r\n"
    "        else if (!declaresType existing entry.1) = true then\n"
    "          if (!declaresParam existing entry.1) = true then\n"
    "            ForInStep.yield (r ++ [⟨\"type \" ++ entry.1, entry.2⟩] ++ "
    "[⟨\"param \" ++ entry.1, \"\"⟩])\n"
    "          else ForInStep.yield (r ++ [⟨\"type \" ++ entry.1, entry.2⟩])\n"
    "        else if (!declaresParam existing entry.1) = true then\n"
    "          ForInStep.yield (r ++ [⟨\"param \" ++ entry.1, \"\"⟩])\n"
    "        else ForInStep.yield r) : Id (List DocField))\n"
    "      = acc ++ genParamTypeFields existing anns := by\n"
    "    intro anns\n"
    "    induction anns with\n"
    "    | nil =>\n"
    "      intro acc\n"
    "      simp only [List.forIn_nil, genParamTypeFields, List.flatMap_nil, "
    "List.append_nil]\n"
    "      rfl\n"
    "    | cons p ps ih =>\n"
    "      intro acc\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [genParamTypeFields, List.flatMap_cons]\n"
    "      split_ifs with hr ht hp <;>\n"
    "        simp only [ForInStep.yield, bind, Id.run] <;>\n"
    "        rw [ih] <;>\n"
    "        simp_all [genForName, genParamTypeFields]"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical; the reshapes below preserve
    # the definitional form so the frozen proof script still closes (no helper
    # lemma, no axiom, no assumption token introduced).
    #
    # Ports nagini case 1 (pos-control-reorder-guard): the nagini positive
    # reordered the short-circuit `and` operands in the append-guard and in the
    # suppressed-none test. Here one positive commutes the suppress-guard `&&`
    # (the exact analogue on the modeled fix site); a second reshapes the
    # per-name loop, which the nagini positive left untouched but which this
    # single-function model must also keep defended.
    # =====================================================================
    {
        "id": "pos-suppress-guard-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Commute the two conjuncts of the suppress guard. `&&` is commutative on
        # Bool, so suppression fires on exactly the same inputs and the result is
        # unchanged; the frozen proof closes (the `by_cases`/`simp` on the guard
        # sees the same boolean).
        "module": _swap(
            _BASE, _I_SUPPRESS_GUARD,
            "        if suppressTrivialReturn && ann == \"None\" then",
        ),
        "rationale": "the (RETURN) fix-site clause is reshaped by commuting the "
                     "two conjuncts of the suppress guard; `&&` is commutative so "
                     "suppression fires on exactly the same (annotation, flag) "
                     "inputs and `result = … ++ genReturnField …` still holds on "
                     "every input. Must verify, else the fix-site clause is "
                     "SPEC-TOO-STRONG. Ports nagini's reorder-guard positive to "
                     "the modeled fix site.",
    },
    {
        "id": "pos-pername-genforname-shape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the per-name loop body from TWO guarded appends into ONE
        # append of `genForName`'s own shape: the two `if`s move from statement
        # position (each guarding a mutation) into term position (each choosing
        # `[]` or a singleton), and the branch structure the frozen `loop` lemma
        # case-splits on disappears. This is NOT definitionally the frozen impl
        # — the frozen `loop` lemma no longer typechecks against it — so the
        # positive also RE-PROVES that lemma in the reshaped shape (a `have`
        # inside the existing tactic body: no new top-level declaration, no
        # axiom, no `sorry`, theorem statement byte-identical).
        #
        # AUDIT NOTE (why this replaced an earlier positive). The case that
        # previously stood here inlined the loop's `name`/`ann` `let` locals into
        # direct `entry.1`/`entry.2` uses. That is a ZETA-REDUCTION only: it was
        # measured definitionally equal to the frozen implementation
        # (`example : @implFrozen = @implInlined := rfl` ELABORATES, exit 0),
        # so it verified by re-running the frozen proof against a term the
        # kernel cannot distinguish from the frozen one. It exercised the
        # (PERNAME) clause's SOUNDNESS not at all — an honest pass that tested
        # nothing. The reshape below is defeq-distinguishable from frozen by the
        # same probe (`rfl` FAILS against it), so its verification is real
        # evidence that the clause admits a differently-shaped correct impl.
        "module": _swap(
            _swap(
                _BASE, _I_LOOP_BODY,
                "      fields := fields\n"
                "        ++ (if declaresType existing name then [] "
                "else [⟨\"type \" ++ name, ann⟩])\n"
                "        ++ (if declaresParam existing name then [] "
                "else [⟨\"param \" ++ name, \"\"⟩])\n",
            ),
            _P_LOOP,
            "  have loop : ∀ (anns : List (String × String)) (acc : List DocField),\n"
            "      (forIn (m := Id) anns acc (fun entry r =>\n"
            "        if (entry.1 == \"return\") = true then ForInStep.yield r\n"
            "        else ForInStep.yield (r\n"
            "          ++ (if declaresType existing entry.1 then [] "
            "else [⟨\"type \" ++ entry.1, entry.2⟩])\n"
            "          ++ (if declaresParam existing entry.1 then [] "
            "else [⟨\"param \" ++ entry.1, \"\"⟩])))\n"
            "        : Id (List DocField))\n"
            "      = acc ++ genParamTypeFields existing anns := by\n"
            "    intro anns\n"
            "    induction anns with\n"
            "    | nil =>\n"
            "      intro acc\n"
            "      simp only [List.forIn_nil, genParamTypeFields, "
            "List.flatMap_nil, List.append_nil]\n"
            "      rfl\n"
            "    | cons p ps ih =>\n"
            "      intro acc\n"
            "      rw [List.forIn_cons]\n"
            "      simp only [genParamTypeFields, List.flatMap_cons]\n"
            "      split_ifs with hr <;>\n"
            "        simp only [ForInStep.yield, bind, Id.run] <;>\n"
            "        rw [ih] <;>\n"
            "        simp_all [genForName, genParamTypeFields, "
            "List.append_assoc]",
        ),
        "rationale": "the (PERNAME) clause is reshaped from two guarded "
                     "mutations into a single append whose two `if`s sit in TERM "
                     "position, choosing `[]` or a singleton exactly as "
                     "`genForName` does. The generated fields, and their order "
                     "within a name (type then param), are unchanged, so `result "
                     "= existing ++ genParamTypeFields … ++ …` still holds on "
                     "every input; the frozen loop lemma is re-proven in the "
                     "reshaped branch shape rather than reused. Must verify, "
                     "else the per-name clause is SPEC-TOO-STRONG — it would be "
                     "pinning a branch STRUCTURE rather than the field sequence. "
                     "Unlike a zeta-only inlining this impl is NOT definitionally "
                     "the frozen one, so its verification is real evidence.",
    },
    {
        "id": "pos-pername-positive-guards",
        "kind": "soundness",
        "expect": "verify",
        # Invert the polarity of BOTH per-name guards: instead of `if !declared
        # then append`, write `if declared then pure () else append`, so the
        # already-declared cases become the taken branch and the negations
        # disappear from the impl entirely. The generated fields and their order
        # are unchanged, so this is CORRECT — but the branch shape the frozen
        # `loop` lemma case-splits on is inverted, so the frozen lemma no longer
        # typechecks against it and the case RE-PROVES that lemma with the
        # branches in the inverted order (a `have` inside the frozen tactic body:
        # no new top-level declaration, no axiom, no `sorry`, theorem statement
        # byte-identical).
        #
        # AUDIT NOTE (why this was added). A prior audit built this reshape,
        # found it REJECTED under the frozen proof script, and recorded it as
        # UNCERTAIN — "a likely-closable tactic gap rather than a spec defect" —
        # without spending the builds to decide which. That left an unresolved
        # possible SPEC-TOO-STRONG hole standing in the record. It is now
        # decided by measurement: the rejection WAS a tactic gap, and re-proving
        # the loop lemma in the inverted branch shape closes it (built
        # standalone, exit 0). Landing it as a permanent positive is what keeps
        # the answer in the artifact instead of in a note. The defeq probe
        # confirms it is a real reshape and not a no-op: `example : @implFrozen =
        # @implPositiveGuards := rfl` FAILS (`Type mismatch ... implA = implB`),
        # so the kernel distinguishes it from the frozen impl.
        "module": _swap(
            _swap(
                _BASE, _I_LOOP_BODY,
                "      if declaresType existing name then\n"
                "        pure ()\n"
                "      else\n"
                "        fields := fields ++ [⟨\"type \" ++ name, ann⟩]\n"
                "      if declaresParam existing name then\n"
                "        pure ()\n"
                "      else\n"
                "        fields := fields ++ [⟨\"param \" ++ name, \"\"⟩]\n",
            ),
            _P_LOOP,
            "  have loop : ∀ (anns : List (String × String)) (acc : List DocField),\n"
            "      (forIn (m := Id) anns acc (fun entry r =>\n"
            "        if (entry.1 == \"return\") = true then ForInStep.yield r\n"
            "        else if declaresType existing entry.1 = true then\n"
            "          if declaresParam existing entry.1 = true then "
            "ForInStep.yield r\n"
            "          else ForInStep.yield (r ++ [⟨\"param \" ++ entry.1, \"\"⟩])\n"
            "        else if declaresParam existing entry.1 = true then\n"
            "          ForInStep.yield (r ++ [⟨\"type \" ++ entry.1, entry.2⟩])\n"
            "        else ForInStep.yield (r ++ [⟨\"type \" ++ entry.1, entry.2⟩] "
            "++ [⟨\"param \" ++ entry.1, \"\"⟩])) : Id (List DocField))\n"
            "      = acc ++ genParamTypeFields existing anns := by\n"
            "    intro anns\n"
            "    induction anns with\n"
            "    | nil =>\n"
            "      intro acc\n"
            "      simp only [List.forIn_nil, genParamTypeFields, "
            "List.flatMap_nil, List.append_nil]\n"
            "      rfl\n"
            "    | cons p ps ih =>\n"
            "      intro acc\n"
            "      rw [List.forIn_cons]\n"
            "      simp only [genParamTypeFields, List.flatMap_cons]\n"
            "      split_ifs with hr ht hp <;>\n"
            "        simp only [ForInStep.yield, bind, Id.run] <;>\n"
            "        rw [ih] <;>\n"
            "        simp_all [genForName, genParamTypeFields, "
            "List.append_assoc]",
        ),
        "rationale": "the (PERNAME) clause is reshaped by inverting the polarity "
                     "of both already-declared guards, so the impl carries no "
                     "boolean negation and the already-declared cases are the "
                     "taken branch. The generated fields and their within-name "
                     "order are unchanged, so `result = existing ++ "
                     "genParamTypeFields … ++ …` still holds on every input; the "
                     "frozen loop lemma is re-proven with the branches inverted "
                     "rather than reused. Must verify, else the per-name clause "
                     "would be pinning guard POLARITY rather than the field "
                     "sequence. Decides an item an earlier audit left UNCERTAIN: "
                     "the reshape's rejection under the frozen script was a "
                     "tactic gap, not a spec defect.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # in the abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so the nagini precondition-
    # admission probe (case 2) has no binder to attack here; the honest analogue
    # is to discharge the spec predicate by evaluation at the ground F2P input (a
    # class-like target: a documented parameter plus a trivial-unit return under
    # the suppress flag) alongside the frozen obligation. Ports nagini case 2
    # (admissibility-f2p-shape).
    # =====================================================================
    {
        "id": "admiss-f2p-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped input by `rfl` (a `have`),
        # then close the frozen obligation verbatim. Nothing is assumed: no new
        # declaration, the theorem statement is byte-identical, and the ground
        # instance is a `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _P_HEAD,
            "  intro existing annotations suppressTrivialReturn\n"
            "  have _ground : problem_spec_render_typehint_fields [] "
            "[(\"x\", \"int\"), (\"return\", \"None\")] true\n"
            "      (implementation_render_typehint_fields [] "
            "[(\"x\", \"int\"), (\"return\", \"None\")] true) := by\n"
            "    rfl\n"
            "  have loop",
        ),
        "rationale": "the obligation is discharged at the ground F2P input (no "
                     "existing fields, one documented parameter annotation, and a "
                     "trivial-unit return entry under the suppress flag — the "
                     "scenario where the fix removes the spurious return-type "
                     "field) by `rfl`, then the frozen obligation is closed "
                     "verbatim. Verifies (else the modeled behavior is "
                     "unsatisfiable at exactly the input the F2P exercises — the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, statement byte-identical, ground instance is a "
                     "`have` inside the existing tactic body. Ports nagini's "
                     "admissibility-f2p-shape probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one concrete
    # input.
    # =====================================================================

    # ---- the fix itself: never suppress (pre-patch) — nagini case 4 ----
    {
        "id": "weak-no-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch skeleton: append the return-type field whenever a return
        # entry is present and no return type is already declared, ignoring the
        # suppress flag and the trivial-unit annotation entirely.
        "module": _swap(
            _BASE, _I_RETURN,
            "  match lookupReturn annotations with\n"
            "  | some ann =>\n"
            "      if !(hasReturnField existing) then\n"
            "        fields := fields ++ [⟨\"rtype\", ann⟩]\n"
            "  | none => pure ()\n"
            "  return fields",
        ),
        "refinement": "this IS the pre-patch behavior: append the trailing "
                      "return-type field unconditionally once a return entry is "
                      "present and none is already declared. For a documented "
                      "class-like target whose return annotation is the trivial "
                      "unit it emits the spurious return-type field the issue is "
                      "about — precisely the lines the F2P test deletes. The "
                      "faithful real patch would NOT resolve.",
        "rationale": "REJECT from the (RETURN) clause on the sub-domain "
                     "{suppress flag set, return annotation is the trivial unit, "
                     "no return type already declared}: the spec produces NO "
                     "trailing field (genReturnField = []) but the rival appends "
                     "one, so `result` differs. Binder spread: existing=[], "
                     "annotations=[(\"return\",\"None\")], suppress=true.",
        # AUDIT NOTE (why this witness was strengthened). The witness that
        # previously stood here closed with a bare `simp [...]`, and its
        # gold-side failure was `unsolved goals ⊢ ¬pure [] = []` — which READS
        # like a semantic refutation (the negation left standing because gold
        # satisfies the spec) but is not evidence of one. Measured by the
        # forgery test: the SAME witness with the `¬` dropped — i.e. asserting
        # gold is CORRECT at this input, the opposite claim — also fails on
        # gold, with the byte-identical error modulo the negation
        # (`unsolved goals ⊢ pure [] = []`, exit 1). So gold's exit code was
        # tracking `simp`'s failure to unfold `pure`, not the truth of the
        # claim, and the gate would have recorded `rejected` for a witness
        # asserting the spec HOLDS here. Replaced with a reduction that hands
        # the kernel a decidable proposition: `decide` then returns a verdict
        # that moves with the claim (measured: rival 0, gold 1, flipped-claim
        # gold 0, flipped-claim rival 1).
        "witness": (
            "example : ¬ problem_spec_render_typehint_fields [] "
            "[(\"return\", \"None\")] true\n"
            "    (implementation_render_typehint_fields [] "
            "[(\"return\", \"None\")] true) := by\n"
            "  unfold problem_spec_render_typehint_fields "
            "implementation_render_typehint_fields\n"
            "  simp only [Id.run, bind, pure, genParamTypeFields, genForName, "
            "genReturnField,\n"
            "             lookupReturn, declaresType, declaresParam, "
            "hasReturnField,\n"
            "             List.flatMap_cons, List.flatMap_nil, List.any_nil, "
            "List.find?_cons,\n"
            "             List.find?_nil, List.append_nil, List.nil_append]\n"
            "  decide\n"
        ),
    },

    # ---- over-suppress: drop the trivial-unit guard — nagini case 5 ----
    {
        "id": "weak-over-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        # Suppress the return-type field for ANY return annotation whenever the
        # flag is set, dropping the trivial-unit guard.
        "module": _swap(
            _BASE, _I_RETURN,
            "  match lookupReturn annotations with\n"
            "  | some ann =>\n"
            "      if !(hasReturnField existing) then\n"
            "        if suppressTrivialReturn then\n"
            "          return fields\n"
            "        fields := fields ++ [⟨\"rtype\", ann⟩]\n"
            "  | none => pure ()\n"
            "  return fields",
        ),
        "refinement": "a patch that suppressed the return-type field for ANY "
                      "return annotation of a suppressed target (not just the "
                      "trivial unit) would strip legitimate return-type fields "
                      "from documented objects with a real return annotation, "
                      "regressing the rendering the P2P tests assert and "
                      "contradicting the gold guard that keys suppression on the "
                      "trivial-unit annotation. It would NOT resolve.",
        "rationale": "REJECT from the (RETURN) clause on the sub-domain "
                     "{suppress flag set, return annotation is NON-trivial, no "
                     "return type already declared}: the spec still produces the "
                     "return-type field (genReturnField = [⟨\"rtype\", ann⟩]) but "
                     "the rival suppresses it, so `result` differs. Moves the "
                     "annotation binder to a non-trivial return "
                     "(annotations=[(\"return\",\"int\")], suppress=true).",
        # AUDIT NOTE. Strengthened for the same measured reason as
        # `weak-no-suppression`: the previous bare-`simp` witness failed on gold
        # with `unsolved goals ⊢ ¬pure [⟨"rtype","int"⟩] = [⟨"rtype","int"⟩]`,
        # and the flipped claim (drop the `¬`, asserting gold is CORRECT here)
        # failed identically (exit 1) — so the exit code carried nothing about
        # the claim. The `decide` form below moves with the claim: rival 0,
        # gold 1, flipped-claim gold 0, flipped-claim rival 1.
        "witness": (
            "example : ¬ problem_spec_render_typehint_fields [] "
            "[(\"return\", \"int\")] true\n"
            "    (implementation_render_typehint_fields [] "
            "[(\"return\", \"int\")] true) := by\n"
            "  unfold problem_spec_render_typehint_fields "
            "implementation_render_typehint_fields\n"
            "  simp only [Id.run, bind, pure, genParamTypeFields, genForName, "
            "genReturnField,\n"
            "             lookupReturn, declaresType, declaresParam, "
            "hasReturnField,\n"
            "             List.flatMap_cons, List.flatMap_nil, List.any_nil, "
            "List.find?_cons,\n"
            "             List.find?_nil, List.append_nil, List.nil_append]\n"
            "  decide\n"
        ),
    },

    # ---- content-wrong return-type body — nagini case 6 ----
    {
        "id": "weak-content-fixed-unit",
        "kind": "uniqueness",
        "expect": "reject",
        # Right decision, wrong body: emit the return-type field on exactly the
        # right inputs but render a fixed trivial-unit body instead of the
        # object's OWN return annotation. (The latent transcription defect the
        # gold also corrects.)
        "module": _swap(
            _BASE, _I_RTYPE_BODY,
            "        fields := fields ++ [⟨\"rtype\", \"None\"⟩]",
        ),
        "refinement": "rendering a fixed trivial-unit body (or any other name's "
                      "annotation) instead of the object's own return annotation "
                      "is the latent transcription defect: a documented object "
                      "returning a real type would render its return-type field "
                      "with the wrong body. Such a patch fails the rendering the "
                      "F2P / P2P assertions pin, so it would NOT resolve.",
        "rationale": "REJECT from the (RETURN) content sub-clause: the decision "
                     "to emit is correct but the body must be the object's own "
                     "return annotation; the rival hardcodes the trivial unit, so "
                     "for a non-trivial return annotation the produced field's "
                     "body — hence `result` — differs. Moves the suppress binder "
                     "to false (annotations=[(\"return\",\"int\")], suppress="
                     "false).",
        "witness": (
            "example : ¬ problem_spec_render_typehint_fields [] "
            "[(\"return\", \"int\")] false\n"
            "    (implementation_render_typehint_fields [] "
            "[(\"return\", \"int\")] false) := by\n"
            "  unfold problem_spec_render_typehint_fields "
            "implementation_render_typehint_fields\n"
            "  simp only [Id.run, bind, pure, genParamTypeFields, genReturnField, "
            "lookupReturn,\n"
            "             hasReturnField, List.flatMap_nil, List.any_nil, "
            "List.find?_cons,\n"
            "             List.find?_nil, List.append_nil, List.nil_append]\n"
            "  decide\n"
        ),
    },

    # ---- the already-present-fields prefix (unchanged but load-bearing) ----
    {
        "id": "weak-drop-existing-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # Seed the result from the empty list instead of the already-present
        # fields, dropping the (PREFIX) clause.
        "module": _swap(
            _BASE, _I_PREFIX,
            "  let mut fields := []",
        ),
        "refinement": "a faithful real patch that discarded the fields already "
                      "present in the list (rebuilding from empty) would delete "
                      "the object's existing documentation — every parameter "
                      "description and prior field the routine is meant to AUGMENT "
                      "— so the rendered output would lose content the P2P tests "
                      "assert. It would NOT resolve.",
        "rationale": "REJECT from the (PREFIX) clause: the spec pins the result "
                     "to begin with the `existing` fields in order, and the rival "
                     "drops them, so at a non-empty `existing` the result differs. "
                     "Moves the `existing` binder to a non-empty already-present "
                     "field and the `annotations` binder to the empty list "
                     "(existing=[⟨\"foo\",\"bar\"⟩], annotations=[], "
                     "suppress=false).",
        # AUDIT NOTE. Strengthened for the same measured reason as
        # `weak-no-suppression`: the previous bare-`simp` witness failed on gold
        # with `unsolved goals ⊢ ¬pure [⟨"foo","bar"⟩] = [⟨"foo","bar"⟩]`, and
        # the flipped claim failed identically (exit 1), so gold's exit code
        # discriminated nothing. The `decide` form moves with the claim: rival 0,
        # gold 1, flipped-claim gold 0, flipped-claim rival 1.
        "witness": (
            "example : ¬ problem_spec_render_typehint_fields [⟨\"foo\", \"bar\"⟩] "
            "[] false\n"
            "    (implementation_render_typehint_fields [⟨\"foo\", \"bar\"⟩] [] "
            "false) := by\n"
            "  unfold problem_spec_render_typehint_fields "
            "implementation_render_typehint_fields\n"
            "  simp only [Id.run, bind, pure, genParamTypeFields, genForName, "
            "genReturnField,\n"
            "             lookupReturn, declaresType, declaresParam, "
            "hasReturnField,\n"
            "             List.flatMap_cons, List.flatMap_nil, List.any_nil, "
            "List.find?_cons,\n"
            "             List.find?_nil, List.append_nil, List.nil_append]\n"
            "  decide\n"
        ),
    },

    # ---- the return-presence scan: narrowed to the bare return-type field ----
    # The Lean counterpart of nagini's `has_return_field_in` attack surface. The
    # nagini bundle could only reach that helper by MUTATING its read-only input
    # (a permission attack with no instance on a referentially transparent
    # carrier), so the port dropped it and left this clause of the modeled scan
    # unprobed by any rival. It is attackable here directly, on VALUE: narrow the
    # scan so it recognises only the bare return-type field name and misses the
    # other field shapes that also record a declaration under the return name.
    {
        "id": "weak-narrow-return-presence",
        "kind": "uniqueness",
        "expect": "reject",
        # Recognise only a bare `rtype …` field as "a return type is already
        # declared", missing the `type return` / `param return` /
        # `param <kind> return` shapes that the scan also records under the
        # return name (see `isReturnField`).
        "module": _swap(
            _BASE, _I_PRESENCE_GUARD,
            "      if !(existing.any (fun f => match tokenize f.name with\n"
            "                                  | \"rtype\" :: _ => true\n"
            "                                  | _ => false)) then\n",
        ),
        "refinement": "a faithful real patch whose return-presence scan keyed "
                      "only on the bare return-type field name would re-append a "
                      "return-type field to an object that already declares its "
                      "return type under one of the other accepted field shapes, "
                      "rendering the return type TWICE. That duplicate contradicts "
                      "the already-declared guard the P2P tests rely on, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from the (RETURN) already-declared sub-clause on the "
                     "sub-domain {a return entry is present, the existing fields "
                     "declare the return type via a shape OTHER than the bare "
                     "return-type field}: `hasReturnField` is true there, so the "
                     "spec produces NO trailing field, but the rival's narrowed "
                     "scan reports false and appends one. Moves the `existing` "
                     "binder to a field that declares a type for the return "
                     "position — a point no other reject case reaches "
                     "(existing=[⟨\"type return\",\"int\"⟩], "
                     "annotations=[(\"return\",\"int\")], suppress=false).",
        # CARRIER NOTE. `tokenize` is built on `String.splitOn`, which does not
        # reduce on this carrier: `tokenize "type return" = ["type", "return"]`
        # closes by neither `rfl` nor `decide` nor `simp [tokenize]` (all three
        # measured failing; `simp [tokenize, String.splitOn, String.splitOnAux]`
        # runs to a whnf heartbeat timeout). So the refutation is stated at a
        # point described by HYPOTHESIS — the tokenization of the one concrete
        # field name — exactly as an opaque guard would require. The hypothesis is
        # satisfiable (the gate's consistency probe cannot derive `False` from it;
        # measured: probe build fails, `simp_all made no progress`), and the
        # witness still discriminates: it elaborates against the rival and
        # `decide` refutes it against the frozen solution.
        "witness": (
            "example (htok : tokenize \"type return\" = [\"type\", \"return\"]) :\n"
            "    ¬ problem_spec_render_typehint_fields [⟨\"type return\", \"int\"⟩] "
            "[(\"return\", \"int\")] false\n"
            "      (implementation_render_typehint_fields "
            "[⟨\"type return\", \"int\"⟩] [(\"return\", \"int\")] false) := by\n"
            "  unfold problem_spec_render_typehint_fields "
            "implementation_render_typehint_fields\n"
            "  simp only [Id.run, bind, pure, genParamTypeFields, genReturnField, "
            "lookupReturn,\n"
            "             hasReturnField, isReturnField, declaresTypeField, "
            "declaresParamField,\n"
            "             htok, List.flatMap_nil, List.any_cons, List.any_nil, "
            "List.find?_cons,\n"
            "             List.find?_nil, List.append_nil, List.nil_append, "
            "beq_self_eq_true,\n"
            "             Bool.true_or, Bool.or_true, if_true, if_false]\n"
            "  decide\n"
        ),
    },

    # ---- the per-name param-field generation (unchanged but load-bearing) ----
    {
        "id": "weak-drop-param-field",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the param-field append in the per-name loop: emit only the type
        # field, never the param field, violating the (PERNAME) clause.
        "module": _swap(
            _BASE, _I_PARAM_APPEND,
            "",
        ),
        "refinement": "a faithful real patch that stopped emitting the per-name "
                      "param field would drop the empty `param <name>` field the "
                      "routine appends for each documented name, so the rendered "
                      "parameter list the P2P tests assert would be missing "
                      "entries. It would NOT resolve.",
        "rationale": "REJECT from the (PERNAME) clause: for a non-return "
                     "annotation whose parameter is not already declared the spec "
                     "generates a type field FOLLOWED BY a param field "
                     "(genForName), and the rival omits the param field, so "
                     "`result` differs. Moves the `annotations` binder to a "
                     "per-name (non-return) entry "
                     "(annotations=[(\"x\",\"int\")], suppress=false).",
        "witness": (
            "example : ¬ problem_spec_render_typehint_fields [] "
            "[(\"x\", \"int\")] false\n"
            "    (implementation_render_typehint_fields [] "
            "[(\"x\", \"int\")] false) := by\n"
            "  unfold problem_spec_render_typehint_fields "
            "implementation_render_typehint_fields\n"
            "  simp only [Id.run, bind, pure, genParamTypeFields, genForName, "
            "genReturnField,\n"
            "             lookupReturn, declaresType, declaresParam, "
            "List.flatMap_cons,\n"
            "             List.flatMap_nil, List.any_nil, List.find?_cons, "
            "List.find?_nil,\n"
            "             List.append_nil, List.nil_append]\n"
            "  decide\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` and declares no `opaque`
# (the whole classification/generation is modeled deeply). The nagini
# AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
