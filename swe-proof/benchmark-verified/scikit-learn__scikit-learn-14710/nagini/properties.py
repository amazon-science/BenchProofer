"""properties.py — PBT falsification battery for scikit-learn__scikit-learn-14710.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical"). Every spec variant
is built by REGION-SURGERY that rewrites ONLY the text inside an
`# impl-start` / `# impl-end` body — the frozen spec (signatures, the `pure`
helpers `decode_one` / `in_index_range`, pre-conditions, post-conditions) is
never touched, so `markers.same_spec` is GUARANTEED and any rejection is
attributable to a POSTCONDITION clause or the permission system, never to a
tampered spec. (Nagini's `spec_view` elides the WHOLE impl span, including the
nested invariants region, so reshaping a loop / invariant does not change the
spec signature — verified at authoring time.)

The defended surface
--------------------
Two structurally-independent modeled functions, BYTE-IDENTICAL in body and spec
(modulo `secondary`'s extra `Requires(use_secondary)` guard):

    primary_score_target(is_clf, labels, target)            -> List[int]
    secondary_score_target(use_secondary, is_clf, labels, target) -> List[int]

models the gold patch's two hunks in
`BaseHistGradientBoosting._check_early_stopping_scorer`:

    if is_classifier(self): y_small_train = self.classes_[y_small_train.astype(int)]
    ... and the identical guard on y_val ...

i.e. for a CLASSIFIER, map the internally-held integer target index back to the
ORIGINAL class value (`labels[target[i]]`) before scoring; for a non-classifier
the target is passed through unchanged.

READ-ONLY inputs (`labels`, `target`) — FRAME-MUTATION is MANDATORY
-------------------------------------------------------------------
Both `labels` and `target` are held at HALF permission in BOTH the Requires and
the Ensures (`Acc(list_pred(labels), 1/2)`, `Acc(list_pred(target), 1/2)`), so
they are READ-ONLY. The directive-5 FRAME-MUTATION attack therefore APPLIES and
is MANDATORY: a rival that WRITES to `labels` or `target` (e.g. to overwrite the
input so the postcondition is satisfied vacuously) must be REJECTED for
INSUFFICIENT PERMISSION, before any postcondition is considered. The gold loop /
invariants / framing asserts are kept VERBATIM with only the offending write
inserted, so the rejection is attributable SOLELY to the write.

The load-bearing postcondition clauses (model.py post-conditions region)
------------------------------------------------------------------------
  (P_len)  len(Result()) == len(target)
  (P_dec)  Implies(is_clf,  Forall i in [0,len(target)):
                            Result()[i] == decode_one(labels, target[i]))   <- DISCRIMINATOR
  (P_id)   Implies(not is_clf, ToSeq(Result()) == ToSeq(target))            <- PASSTHROUGH
  (P_acc)  Acc(labels,1/2), Acc(target,1/2) returned; Acc(Result()) full

(P_dec) is the behavioural delta the gold patch introduces and exactly what
`model_prepatch.py` FAILS (classifier target forwarded UNDECODED). Because a
LabelEncoded class table maps distinct original values to distinct positions,
`labels[target[i]] != target[i]` in the generic case, so forwarding the raw
index violates (P_dec). (P_id) pins the regressor no-op.

`decode_one` is a GROUNDED @Pure helper, not an answer-key oracle
-----------------------------------------------------------------
`decode_one(labels, x)` is fully UNFOLDED in the contract (`labels[x]` for a
valid index `x`, identity otherwise) — it is a function of the inputs, not an
opaque marker an impl could echo without doing the work. Echoing it
(`result + [decode_one(labels, target[i])]`) IS the gold behaviour (under
`in_index_range` it equals `labels[target[i]]`), so there is NO wrong
ungrounded-oracle echo to exploit; directive-2 echo does NOT apply. Instead we
supply that as an HONEST grounded-oracle positive control (expect="verify").

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
Both functions are TOTAL over their precondition domain: each always returns a
`List[int]`, never raises, and has no side effect (the inputs are read-only).
The real gathers (`self.classes_[y.astype(int)]`) likewise do not raise on the
in-index-range targets a LabelEncoder always supplies. The value abstraction
(the returned list) fully captures the behaviour, so there is no
capability-token discriminator to build; the control-flow-effect class does NOT
apply (stated in 'assessment').

Axiom lane
----------
meta.axioms = []  — there is NO @ContractOnly axiom the proof consumes (the
`axioms` region is empty). The single kind-A obligation is the A-REFERENCE deep
model `decode_one` == the real numpy fancy-index `self.classes_[y.astype(int)]`
(with `self.classes_` from the real `sklearn.preprocessing.LabelEncoder`). Per
PLAN §2.4 / §4 an A-reference deep model is checked the same way as a consumed
axiom: the deep model must equal the real callee on every caller-reachable
input. The AXIOM_TESTS therefore REUSE + strengthen `axiom_check.py` (the
existing G-AX soundness check). The runner mounts ONLY the probe at /work, so
axiom_check.py's source is read on the HOST at manifest-load time and embedded
into the probe string. The callee (numpy advanced indexing + LabelEncoder) is
UNCHANGED by the gold patch (the patch only inserts a call SITE in
gradient_boosting.py), so apply_gold=False.

Authoring mechanics
-------------------
The two impl bodies are byte-identical, so `_swap_both` replaces BOTH (count==2)
to test both sites at once; `_swap_first` replaces only the PRIMARY body (for the
admissibility self-call, whose callee name is function-specific). Every rival
keeps the gold invariants/asserts VERBATIM except the single targeted change, so
no rejection is a mislabeled proof-trigger gap (pilot trap #2). No bare
`return []  # type:` is introduced (pilot trap #1): the gold already binds a
typed local (`result = []  # type: List[int]`) and rivals reuse it.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14710"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


# --- extract the gold impl block (markers inclusive) verbatim from _BASE ------
# Both functions share this exact block byte-for-byte (verified at authoring).
def _gold_block(src):
    start = src.index("    # impl-start")
    end = src.index("    # impl-end", start) + len("    # impl-end")
    return src[start:end]


_GOLD_BLOCK = _gold_block(_BASE)
assert _BASE.count(_GOLD_BLOCK) == 2, "expected exactly two identical impl bodies"


def _swap_both(new_block):
    """Replace the impl body in BOTH functions (tests both modeled sites)."""
    if _BASE.count(_GOLD_BLOCK) != 2:
        raise AssertionError("drift: gold impl block not present exactly twice")
    return _BASE.replace(_GOLD_BLOCK, new_block, 2)


def _swap_first(new_block):
    """Replace ONLY the primary (first) impl body; secondary stays gold.
    Used where the rewrite references a function-specific symbol (the
    admissibility self-call)."""
    if _BASE.count(_GOLD_BLOCK) != 2:
        raise AssertionError("drift: gold impl block not present exactly twice")
    return _BASE.replace(_GOLD_BLOCK, new_block, 1)


# ---------------------------------------------------------------------------
# Rival impl bodies (markers inclusive; 4-space indented, exactly like gold).
# ---------------------------------------------------------------------------

# (FRAME-MUTATION — MANDATORY) Keep the gold classifier loop VERBATIM, but before
# returning, OVERWRITE the read-only input element `target[0]`. Assigning
# `target[0] = ...` needs FULL Acc(list_pred(target)); the precondition and loop
# invariant grant only Acc(list_pred(target), 1/2). The write is REJECTED for
# INSUFFICIENT PERMISSION before any postcondition is considered. (Guarded by a
# length check so the write is well-typed; the rejection is the permission, not an
# index fault.)
_IMPL_FRAME_MUTATE_TARGET = """    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        # FRAME-MUTATION: overwrite the READ-ONLY input `target` (held at 1/2).
        if len(target) > 0:
            target[0] = labels[0]
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end"""

# (PARTIAL-DOMAIN / PREPATCH) The classifier branch forwards the RAW index
# `target[i]` UNDECODED — the exact pre-patch behaviour (model_prepatch.py). The
# loop invariant carrying `result[k] == decode_one(labels, target[k])` can no
# longer be re-established (the appended element is `target[i]`, not
# `labels[target[i]]`), so (P_dec) is unprovable. Regressor branch kept gold.
_IMPL_PREPATCH_UNDECODED = """    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            # PREPATCH: forward the raw internal index, NOT labels[target[i]].
            result = result + [target[i]]
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end"""

# (PARTIAL-DOMAIN — first element undecoded) Decode every index EXCEPT index 0,
# which is forwarded raw. Correct on the whole domain EXCEPT the first element
# (when labels[target[0]] != target[0]). (P_dec) fails at i==0. The loop appends
# `target[i]` when i==0 and `labels[target[i]]` otherwise; the per-element
# invariant cannot be re-established at i==0.
_IMPL_FIRST_UNDECODED = """    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            # PARTIAL-DOMAIN: leave the FIRST element undecoded; decode the rest.
            if i == 0:
                result = result + [target[i]]
            else:
                result = result + [labels[target[i]]]
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end"""

# (PASSTHROUGH-CLAUSE attack) The NON-classifier branch DECODES instead of
# passing through: it appends `labels[target[j]]` (the classifier behaviour) on
# the `not is_clf` path. Violates (P_id) (Result() must equal target unchanged)
# whenever labels[target[j]] != target[j]. The regressor has NO in_index_range
# precondition, so this also reaches an unconstrained gather; either way (P_id)
# fails. The classifier branch is kept gold so the rejection is solely the
# passthrough clause. (We keep the gold `out == take(j)` invariant; it can no
# longer be re-established because the appended element differs from target[j].)
_IMPL_REGRESSOR_DECODE = """    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            # PASSTHROUGH-CLAUSE attack: decode on the REGRESSOR path too.
            if 0 <= target[j] and target[j] < len(labels):
                out = out + [labels[target[j]]]
            else:
                out = out + [target[j]]
            j = j + 1
        return out
    # impl-end"""

# (POSITIVE CONTROL — grounded-oracle delegate) Classifier branch appends
# `decode_one(labels, target[i])` directly (instead of `labels[target[i]]`).
# Under the loop's `0 <= target[i] < len(labels)` (re-derived from
# in_index_range) `decode_one` UNFOLDS to exactly `labels[target[i]]`, so this is
# the gold behaviour expressed through the grounded oracle. We add the framing
# assert that bridges them so the per-element invariant is preserved. Must verify
# (else SPEC-TOO-STRONG / the postcondition is over-fit to the literal index).
_IMPL_POS_DECODE_ONE = """    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            # grounded-oracle delegate: decode_one(labels, target[i]) unfolds to
            # labels[target[i]] under the asserted in-range index above.
            Assert(decode_one(ToSeq(labels), ToSeq(target)[i]) == labels[target[i]])
            result = result + [decode_one(ToSeq(labels), ToSeq(target)[i])]
            Assert(ToSeq(result) == old_seq + PSeq(decode_one(ToSeq(labels), ToSeq(target)[i])))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end"""

# (POSITIVE CONTROL — local-variable reshape) Same forward loop and identical
# framing asserts, but the decoded value is bound to a typed local `dec` first
# and the SAME `result + [dec]` append is used. Structurally different (an extra
# named local + the bridge assert) but behaviourally identical; keeps every gold
# proof obligation verbatim. Must verify (else SPEC-TOO-STRONG / over-fit to the
# inline-append spelling). No loop-direction flip (pilot trap #3 avoided).
_IMPL_POS_LOCALVAR = """    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            dec = labels[target[i]]  # type: int
            result = result + [dec]
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end"""

# (ADMISSIBILITY — primary only) The PRIMARY body is a self-call to
# primary_score_target on the SAME in-scope F2P-shaped inputs (`is_clf`,
# `labels`, `target`) whose Result is returned. The caller holds
# Acc(labels,1/2) + Acc(target,1/2) + Implies(is_clf, in_index_range(...)) —
# EXACTLY the callee's Requires — so the precondition is established at a REAL
# call site; and the callee's Ensures (signature-identical to this function's)
# discharges this function's own postcondition directly, returning the
# half-permissions. If the Requires could not be established for this legitimate
# label-encoded input => PRECOND-TOO-STRONG.
#
# NB: the probe must be the WHOLE body (return the callee's Result), NOT a probe
# PREPENDED to the gold loop. The frozen Ensures returns Acc(target,1/2) but does
# NOT pin ToSeq(target)/len(target) == old(...), so after a self-call Nagini
# (soundly, modularly) HAVOCS the abstract value of `target`. A prepended probe
# would therefore break the *downstream gold code* (the loop-entry invariant
# in_index_range(target), or the function's own len(Result())==len(target)
# postcondition) — a value-framing PROOF artifact of the prepend placement, NOT a
# precondition failure (the call site itself type-checks and its Requires hold).
# Returning the Result avoids re-deriving any havoced input fact, so it isolates
# the admissibility check to exactly the precondition + result consumption.
# same_spec holds (the whole impl span is elided by spec_view).
_IMPL_ADMISS_PRIMARY = """    # impl-start
    _probe = primary_score_target(is_clf, labels, target)
    return _probe
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-grounded-oracle-decode-one",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_both(_IMPL_POS_DECODE_ONE),
        "rationale": (
            "Grounded-oracle positive control: the classifier branch appends "
            "decode_one(labels, target[i]) directly. `decode_one` is a fully "
            "unfolded @Pure helper that, under the asserted in-range index "
            "(0 <= target[i] < len(labels), re-derived from in_index_range), "
            "equals labels[target[i]] — so this IS the gold behaviour expressed "
            "through the grounded oracle. The bridge Assert keeps the per-element "
            "invariant. Must verify; if it failed the postcondition would be "
            "over-fit to the literal-index spelling => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_both(_IMPL_POS_LOCALVAR),
        "rationale": (
            "Structurally-different but CORRECT impl: the decoded value is bound "
            "to a typed local `dec = labels[target[i]]` and the same forward "
            "append is used, with every gold framing assert kept verbatim. No "
            "loop-direction flip / no new induction lemma (pilot trap #3 avoided). "
            "Must verify; else the spec is over-fit to the inline-append shape => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "admiss-primary-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_first(_IMPL_ADMISS_PRIMARY),
        "rationale": (
            "A self-call primary_score_target(is_clf, labels, target) on the SAME "
            "in-scope F2P-shaped inputs exercises the precondition at a real call "
            "site: the caller holds Acc(labels,1/2) + Acc(target,1/2) + "
            "Implies(is_clf, in_index_range(labels, target)) — exactly the "
            "callee's Requires — and the callee's Ensures (signature-identical to "
            "this function) discharges this function's own postcondition, returning "
            "the half-permissions. The body RETURNS the Result so no havoced input "
            "fact need be re-derived (the frozen Ensures does not pin "
            "ToSeq(target)/len(target) across the call, so a probe prepended to the "
            "gold loop would break downstream gold code on value-framing, not on the "
            "precondition). If the Requires could not be established for a "
            "legitimate label-encoded input => PRECOND-TOO-STRONG. Edits only the "
            "primary impl body (same_spec holds); secondary stays gold."),
    },

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {
        "id": "frame-mutate-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_both(_IMPL_FRAME_MUTATE_TARGET),
        "refinement": (
            "OVERWRITES the read-only input `target[0] = labels[0]` after the gold "
            "loop. The half-permission Acc(list_pred(target), 1/2) abstracts the "
            "gold contract that _check_early_stopping_scorer READS the internal "
            "target and forms a FRESH decoded array "
            "(self.classes_[y.astype(int)]) handed to the scorer, without mutating "
            "the estimator's own stored target. A real 'patch' that overwrote the "
            "stored y_small_train / y_val in place would corrupt the estimator's "
            "internal state used by the rest of fit (the validation split, "
            "subsequent iterations); the early-stopping F2P "
            "(test_string_target_early_stopping) and the regression/classification "
            "early-stopping P2P tests would FAIL. So it would NOT resolve."),
        "rationale": (
            "FRAME-MUTATION (directive 5). Rejection source: the PERMISSION "
            "SYSTEM — assigning target[0] needs full Acc(list_pred(target)) but "
            "the precondition and loop invariant grant only 1/2, so the write "
            "fails for INSUFFICIENT PERMISSION before any postcondition is "
            "considered. If it verified, a mutating impl could satisfy the "
            "postcondition vacuously => SPEC-TOO-WEAK. The gold loop/asserts are "
            "kept verbatim so the rejection is attributable solely to the write."),
    },
    {
        "id": "prepatch-undecoded-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_both(_IMPL_PREPATCH_UNDECODED),
        "refinement": (
            "This is the PRE-PATCH behaviour verbatim (model_prepatch.py): the "
            "classifier branch forwards the raw internal index target[i] UNDECODED "
            "rather than labels[target[i]]. Its faithful real patch is the "
            "UNPATCHED _check_early_stopping_scorer, which hands the integer-coded "
            "y straight to self.scorer_ while predict returns original-domain class "
            "labels — exactly the type mismatch the issue reports "
            "(\"'<' not supported between instances of 'str' and 'float'\"). The "
            "F2P test_string_target_early_stopping[None] then raises and FAILS. It "
            "does NOT resolve."),
        "rationale": (
            "Rejection source: (P_dec) Implies(is_clf, Result()[i] == "
            "decode_one(labels, target[i])). The loop invariant carrying "
            "result[k] == decode_one(labels, target[k]) cannot be re-established "
            "when the appended element is target[i] != labels[target[i]] (distinct "
            "LabelEncoder classes are not equal to their positions), so the "
            "postcondition is unprovable. This is exactly what G-DIFF senses "
            "against model_prepatch.py. If it verified => SPEC-TOO-WEAK."),
    },
    {
        "id": "partial-domain-first-undecoded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_both(_IMPL_FIRST_UNDECODED),
        "refinement": (
            "PARTIAL-DOMAIN: decodes every index EXCEPT the first, which is "
            "forwarded raw (target[0]). Correct on the entire scored target EXCEPT "
            "element 0. Its faithful real patch would decode all but the first "
            "sample of y_small_train / y_val (e.g. an off-by-one slice "
            "self.classes_[y[1:].astype(int)] reassembled). The scored target's "
            "element 0 is then still the integer code while predict's element 0 is "
            "the original class value, so accuracy_score again compares str vs "
            "float on that sample and test_string_target_early_stopping FAILS. It "
            "does NOT resolve. (The issue's fixture is 50 'x' + 50 'y'; the first "
            "sample is a real string label, so the divergence is observable.)"),
        "rationale": (
            "Rejection source: (P_dec) at i==0 — Result()[0] must equal "
            "decode_one(labels, target[0]) == labels[target[0]], but the rival "
            "appends target[0]; the per-element invariant cannot be re-established "
            "at index 0. Demonstrates the spec is tight even on a one-element "
            "divergence (the input that fails first). If it verified => "
            "SPEC-TOO-WEAK."),
    },
    {
        "id": "passthrough-regressor-decode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_both(_IMPL_REGRESSOR_DECODE),
        "refinement": (
            "PASSTHROUGH-CLAUSE attack: the NON-classifier branch decodes "
            "(labels[target[j]]) instead of passing the target through unchanged. "
            "Its faithful real patch drops the `if is_classifier(self):` guard and "
            "ALWAYS applies self.classes_[y.astype(int)]. For a REGRESSOR there is "
            "no classes_ table (the attribute is unset), so the unguarded line "
            "raises AttributeError during early stopping; the regression "
            "early-stopping P2P tests (test_early_stopping_regression[...]) and "
            "test_string_target_early_stopping[loss] FAIL. It does NOT resolve."),
        "rationale": (
            "Rejection source: (P_id) Implies(not is_clf, ToSeq(Result()) == "
            "ToSeq(target)). On the regressor path the rival appends "
            "labels[target[j]] != target[j] in general, so the invariant "
            "ToSeq(out) == ToSeq(target).take(j) cannot be re-established and the "
            "identity postcondition fails. Confirms the spec pins BOTH the decode "
            "(classifier) and the no-op (regressor) behaviours. If it verified => "
            "SPEC-TOO-WEAK."),
    },
]


# ===========================================================================
# AXIOM LANE (Docker) — A-reference soundness + caller-domain containment.
# meta.axioms = [] (NO @ContractOnly axiom). The one kind-A obligation is the
# A-reference deep model decode_one == the REAL numpy fancy-index
# self.classes_[y.astype(int)] (classes_ from the REAL LabelEncoder). Per PLAN
# §2.4/§4 an A-reference is checked like a consumed axiom: the deep model must
# equal the real callee on every caller-reachable input. We REUSE + strengthen
# axiom_check.py. The runner mounts ONLY the probe at /work, so axiom_check.py's
# source is read on the HOST at manifest-load time and embedded (pilot trap #6).
# The callee is UNCHANGED by the gold patch (the patch only inserts a CALL SITE),
# so apply_gold=False.
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# (axiom-soundness) Run the EXACT axiom_check.py battery in-container: it drives
# the GENUINE numpy fancy-index self.classes_[idx] and the REAL
# sklearn.preprocessing.LabelEncoder over 6 boundary + 20000 fuzz gathers and over
# string + numeric round-trip targets (incl. the issue's ['x']*50 + ['y']*50), and
# asserts (1) decode_one-assembly == classes_[idx] element-wise and (2) the
# encode/decode round trip classes_[encoded] == original y is the identity (the
# representation-consistency property the spec pins). Exit 0 iff all sound. Self-
# contained (imports only numpy + sklearn.preprocessing.LabelEncoder).
_AX_SOUNDNESS = _AXIOM_CHECK_SRC

# (axiom-containment) Confirm every callee-input the MODEL can REACH lies in the
# deep model's domain. The model reaches decode_one only with x == target[i] for
# a CLASSIFIER target, and the precondition guarantees in_index_range: every such
# index satisfies 0 <= x < len(labels). So the in-range branch of decode_one (the
# one the gold gather depends on) is exactly the domain the caller reaches; the
# out-of-range fall-through (decode_one(labels, x) == x) is NEVER reached for a
# classifier (sound dead branch, only making the gather total). We assert: for
# targets produced by the REAL LabelEncoder, every code is in [0, len(classes_)),
# so the real numpy gather classes_[code] never indexes out of bounds (the model
# never reaches the out-of-range branch). Covering the out-of-range case is sound
# over-coverage, not a defect. A reachable code outside [0, len(classes_)) would
# be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import random
import sys

import numpy as np
from sklearn.preprocessing import LabelEncoder


def reachable_codes_in_domain(y):
    """The model reaches decode_one(labels, target[i]) only on the CLASSIFIER
    path, whose target is a LabelEncoder-encoded index. Assert every such code is
    in [0, len(classes_)) — i.e. inside decode_one's in-range branch, the exact
    domain the gold gather classes_[code] requires. Also assert the real numpy
    gather succeeds (does not IndexError) on those codes."""
    le = LabelEncoder()
    encoded = le.fit_transform(y)            # the internal integer target
    classes_ = le.classes_                   # the label table (self.classes_)
    k = len(classes_)
    for code in encoded:
        c = int(code)
        if not (0 <= c < k):
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable target code %d outside "
                  "decode_one's in-range domain [0, %d)" % (c, k))
            return False
    # The real numpy fancy-index must not raise for any reachable code: this is
    # precisely the in_index_range precondition the model carries.
    try:
        _ = classes_[encoded.astype(int)]
    except IndexError:
        print("AXIOM-TOO-WEAK-FOR-CALLER: real numpy gather classes_[code] raised "
              "IndexError on a reachable target code")
        return False
    return True


def main():
    rng = random.Random(147102)
    boundary = [
        np.array(['x'] * 50 + ['y'] * 50, dtype=object),   # the issue's fixture
        np.array(['x', 'y', 'x', 'y', 'x'], dtype=object),
        np.array(['only'] * 7, dtype=object),
        np.array(['cat', 'dog', 'cat', 'bird', 'dog', 'cat'], dtype=object),
        np.array([1.0, 2.0, 1.0, 3.0, 2.0]),
        np.array([0, 1, 0, 2, 1, 2]),
    ]
    checked = 0
    for y in boundary:
        if not reachable_codes_in_domain(y):
            return 1
        checked += 1

    pool = ['x', 'y', 'z', 'cat', 'dog', 'alpha', 'beta', 'q', 'foo', 'bar']
    for _ in range(3000):
        kc = rng.randint(2, 6)
        classes = rng.sample(pool, kc)
        n = rng.randint(kc, 40)
        y = np.array([rng.choice(classes) for _ in range(n)], dtype=object)
        if not reachable_codes_in_domain(y):
            return 1
        checked += 1

    print("CONTAINMENT OK: over %d real LabelEncoder targets (boundary incl. the "
          "issue's ['x']*50+['y']*50 + fuzz), every reachable target code lies in "
          "decode_one's in-range domain [0, len(classes_)) and the real numpy "
          "gather classes_[code] never raises. The out-of-range branch of "
          "decode_one is NEVER reached for a label-encoded target (sound dead "
          "branch / over-coverage), so the A-reference deep model covers exactly "
          "the caller-reachable domain." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {
        "id": "ax-decode-sound",
        "axiom": "decode_one",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,
        "probe": _AX_SOUNDNESS,
        "rationale": (
            "REUSES axiom_check.py: drives the REAL numpy fancy-index "
            "self.classes_[idx] and the REAL sklearn LabelEncoder over 6 boundary "
            "+ 20000 fuzz gathers and over string + numeric round-trip targets "
            "(incl. the issue's ['x']*50+['y']*50), asserting (1) the decode_one "
            "deep model == classes_[idx] element-wise and (2) the encode/decode "
            "round trip classes_[encoded] == original y is the identity (the "
            "representation-consistency the spec pins). The callee is UNCHANGED by "
            "the patch (apply_gold=False). Any violation => AXIOM-UNSOUND."),
    },
    {
        "id": "ax-decode-containment",
        "axiom": "decode_one",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAINMENT,
        "rationale": (
            "Every callee-input the model can reach is in-domain: on the "
            "classifier path the model reaches decode_one only with x == target[i] "
            "for a LabelEncoder-encoded target, and in_index_range guarantees "
            "0 <= x < len(labels) — exactly decode_one's in-range branch / the "
            "domain the real gather classes_[code] requires. Confirmed over the "
            "issue's fixture + 3000 fuzz real-LabelEncoder targets: every reachable "
            "code is in [0, len(classes_)) and the real numpy gather never raises. "
            "The out-of-range branch is never reached (sound over-coverage). A "
            "reachable code outside the domain => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
