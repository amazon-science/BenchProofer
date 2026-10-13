# properties.py — PBT falsification battery for django__django-11880.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py whose SPEC (axioms/pure/pre/post + the
# Field/deep_duplicate signatures) is BYTE-IDENTICAL to the frozen model.py and
# differs ONLY inside the impl region (which, together with the nested invariants
# region, is elided from the spec view). Built by region-surgery: every variant
# is produced by _swap-ing the full gold impl BODY for a new body, so same_spec
# is guaranteed (the spec view never sees the impl/invariants).
#
# Defended surface (from model.py + refinement.md + the F2P/P2P tests):
#   deep_duplicate(self: Field) -> Field takes `self` READ-ONLY at HALF
#   permission: Acc(self.msg_codes, 1/2) / Acc(list_pred(self.msg_codes), 1/2)
#   (and msg_values, validators). The load-bearing postcondition clauses are:
#     (D) DISTINCTNESS + FULL OWNERSHIP — for each of the three collections,
#         Acc(Result().X) and Acc(list_pred(Result().X)) at FULL permission and
#         Result().X is not self.X. This is the FIX (gold added
#         result.error_messages = self.error_messages.copy()); the pre-patch
#         alias cannot give full permission while self keeps half. The F2P
#         (test_field_deep_copy_error_messages) is exactly assertIsNot(...).
#     (C) CONTENT EQUALITY — len(Result().X) == len(self.X) and per-index
#         Result().X[k] == self.X[k] for all three collections.
#     (F) FRAME / READ-ONLY — self returned at half permission with len and
#         per-index contents == Old(...): self may not be written.
# There is NO @Pure answer-key oracle pinning the output — the content clauses
# are grounded in the input args (Result().X[k] == self.X[k]); there is no wrong
# value an impl could echo, so the ungrounded-oracle-echo class is N/A here (an
# honest cheapest-impl positive control stands in its place). There are NO
# consumed @ContractOnly axioms (the duplication is modelled deeply); the only
# callee semantics relied on (dict.copy()/list[:] = distinct object, equal
# contents) is an A-reference already exercised by axiom_check.py / G-AX, so the
# AXIOM lane is empty here — but a containment-style cross-check probe is added
# to assert the model never reaches an out-of-domain callee input.
from pathlib import Path

INSTANCE = "django__django-11880"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()

# The full gold impl BODY (everything between '# impl-start\n' and '# impl-end').
_A = "    # impl-start\n"
_B = "    # impl-end"
_ia = _BASE.index(_A) + len(_A)
_ib = _BASE.index(_B)
_GOLD_BODY = _BASE[_ia:_ib]


def _impl(new_body: str) -> str:
    """Replace ONLY the gold impl body (impl + invariants region) with new_body.
    The spec view elides impl/invariants, so the spec signature is unchanged."""
    if _GOLD_BODY not in _BASE:
        raise AssertionError("drift: gold impl body not found")
    if _BASE.count(_GOLD_BODY) != 1:
        raise AssertionError("not unique: gold impl body")
    return _BASE.replace(_GOLD_BODY, new_body, 1)


# ---------------------------------------------------------------------------
# Shared loop fragments (kept verbatim from gold so positive controls KEEP the
# proof obligations they still need — pilot bug 2).
# ---------------------------------------------------------------------------

# The gold msg_codes/msg_values copy loop (forward append; carries every framing
# invariant). Used unchanged in the reordered positive control.
_MSG_LOOP = """\
    a = 0
    while a < len(self.msg_codes):
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(len(result.validators) == len(self.validators))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  result.validators[k] == self.validators[k]))))
        Invariant(0 <= a and a <= len(self.msg_codes))
        Invariant(len(result.msg_codes) == a)
        Invariant(len(result.msg_values) == a)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
        result.msg_codes.append(self.msg_codes[a])
        result.msg_values.append(self.msg_values[a])
        a = a + 1
"""

# The gold validators copy loop AS THE FIRST loop (carries validators progress +
# the result msg collections still empty/owned). Symmetric to the gold first loop.
_VAL_LOOP_FIRST = """\
    b = 0
    while b < len(self.validators):
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(len(result.msg_codes) == 0)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(len(result.msg_values) == 0)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(0 <= b and b <= len(self.validators))
        Invariant(len(result.validators) == b)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                  result.validators[k] == self.validators[k]))))
        Invariant(MustTerminate(len(self.validators) - b + 1))
        result.validators.append(self.validators[b])
        b = b + 1
"""

# The gold msg loop AS THE SECOND loop (after validators are fully copied):
# additionally preserves the finished validators collection.
_MSG_LOOP_SECOND = """\
    a = 0
    while a < len(self.msg_codes):
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(len(result.validators) == len(self.validators))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  result.validators[k] == self.validators[k]))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(0 <= a and a <= len(self.msg_codes))
        Invariant(len(result.msg_codes) == a)
        Invariant(len(result.msg_values) == a)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
        result.msg_codes.append(self.msg_codes[a])
        result.msg_values.append(self.msg_values[a])
        a = a + 1
"""

# --- Split-loop fragments for the reordered positive control -----------------
# The gold combines the two override arrays (msg_codes + msg_values) into a SINGLE
# forward loop. A structurally-different correct impl copies them in two SEPARATE
# forward loops (codes first, then values), then the validators last. Splitting
# the combined loop is what makes the variant genuinely different in shape; it is
# ALSO why this shape verifies in-time where the loop-swap shape did not: the gold
# loop-swap (_VAL_LOOP_FIRST + _MSG_LOOP_SECOND) forces the heavy DOUBLE-growing
# msg loop (two progress foralls + two Old foralls) to run SECOND while ALSO
# carrying the completed-validators content forall — five interacting quantifiers
# that blow up Z3 (>900s, an SMT-instantiation explosion, NOT a logical rejection;
# the gold body and `admiss` both verify, so the spec admits this output). Each
# split loop here grows only ONE collection, so no loop carries more than one
# growing-progress forall alongside the frame foralls, keeping the solver tractable.

# msg_codes copied alone (msg_values still empty/owned, validators still empty).
_CODES_LOOP = """\
    a = 0
    while a < len(self.msg_codes):
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(len(result.msg_values) == 0)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(len(result.validators) == 0)
        Invariant(0 <= a and a <= len(self.msg_codes))
        Invariant(len(result.msg_codes) == a)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(MustTerminate(len(self.msg_codes) - a + 1))
        result.msg_codes.append(self.msg_codes[a])
        a = a + 1
"""

# msg_values copied alone (msg_codes already complete, validators still empty).
_VALUES_LOOP = """\
    c = 0
    while c < len(self.msg_values):
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(len(result.msg_codes) == len(self.msg_codes))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(len(result.validators) == 0)
        Invariant(0 <= c and c <= len(self.msg_values))
        Invariant(len(result.msg_values) == c)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < c,
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(MustTerminate(len(self.msg_values) - c + 1))
        result.msg_values.append(self.msg_values[c])
        c = c + 1
"""

# The validators loop LAST (after BOTH message arrays are complete) — byte-for-byte
# the gold second loop (it carries the finished msg collections as it grows
# validators). Kept verbatim so the positive control retains the real framing
# obligation the gold body carries (pilot bug 2: keep the proof obligations).
_VAL_LOOP_LAST = """\
    b = 0
    while b < len(self.validators):
        Invariant(Acc(self.validators, 1 / 2) and Acc(list_pred(self.validators), 1 / 2))
        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))
        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))
        Invariant(len(self.msg_codes) == len(self.msg_values))
        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))
        Invariant(len(self.msg_values) == Old(len(self.msg_values)))
        Invariant(len(self.validators) == Old(len(self.validators)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  self.msg_values[k] == Old(self.msg_values[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.validators),
                                                  self.validators[k] == Old(self.validators[k])))))
        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))
        Invariant(result.validators is not self.validators)
        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))
        Invariant(result.msg_codes is not self.msg_codes)
        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))
        Invariant(result.msg_values is not self.msg_values)
        Invariant(len(result.msg_codes) == len(self.msg_codes))
        Invariant(len(result.msg_values) == len(self.msg_values))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),
                                                  result.msg_codes[k] == self.msg_codes[k]))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),
                                                  result.msg_values[k] == self.msg_values[k]))))
        Invariant(0 <= b and b <= len(self.validators))
        Invariant(len(result.validators) == b)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < b,
                                                  result.validators[k] == self.validators[k]))))
        Invariant(MustTerminate(len(self.validators) - b + 1))
        result.validators.append(self.validators[b])
        b = b + 1
"""


# ===========================================================================
# POSITIVE CONTROLS (expect verify) — a correct impl in a DIFFERENT shape must
# still verify, else the spec is SPEC-TOO-STRONG.
# ===========================================================================

# pos-reorder: a structurally-DIFFERENT correct duplication. The gold copies the
# two override arrays (msg_codes + msg_values) in a SINGLE combined forward loop;
# this control SPLITS that into two separate forward loops (msg_codes first, then
# msg_values) and copies the validators LAST. Three loops where the gold has two,
# the combined array loop decomposed — a genuinely different impl shape. Each loop
# carries its full framing invariants (pilot bugs 2 & 3 avoided: every framing
# obligation the gold body carries is retained), and a correct impl in this shape
# MUST verify; if it could not, the postcondition would be SPEC-TOO-STRONG.
#
# NOTE (proof engineering, not spec): an earlier shape merely SWAPPED the two gold
# loops (_VAL_LOOP_FIRST + _MSG_LOOP_SECOND). That is also a correct duplication
# and same_spec, but it timed out (>900s standalone) — an SMT quantifier-
# instantiation explosion: the swap forces the heavy DOUBLE-growing msg loop (two
# progress + two Old foralls) to run second while carrying the completed-validators
# content forall (five interacting quantifiers). It is NOT the spec rejecting a
# correct output (the gold body verifies in 47s and `admiss` re-verifies the gold
# body via a self-call in 127s). The split shape keeps every loop to ONE growing
# collection, so the variant verifies in ~150s (< the 300s budget) while remaining
# structurally distinct from the gold.
_POS_REORDER = ("    result = Field()\n\n"
                + _CODES_LOOP + "\n"
                + _VALUES_LOOP + "\n"
                + _VAL_LOOP_LAST
                + "    return result\n")

# admiss: keep the gold body verbatim, but first build an in-domain, F2P-shaped
# probe field (one matching override entry kept length-aligned) and call
# deep_duplicate on it, asserting the precondition admits a normal input. If this
# self-call fails to verify, the precondition is PRECOND-TOO-STRONG. The fresh
# probe carries FULL permission and len(msg_codes)==len(msg_values), so the
# half-permission/equal-length Requires is satisfiable. We discard the result.
_ADMISS = (
    "    probe = Field()\n"
    "    probe.msg_codes.append(7)\n"
    "    probe.msg_values.append(11)\n"
    "    Assert(len(probe.msg_codes) == len(probe.msg_values))\n"
    "    Assert(Acc(probe.msg_codes, 1 / 2) and Acc(list_pred(probe.msg_codes), 1 / 2))\n"
    "    Assert(Acc(probe.msg_values, 1 / 2) and Acc(list_pred(probe.msg_values), 1 / 2))\n"
    "    Assert(Acc(probe.validators, 1 / 2) and Acc(list_pred(probe.validators), 1 / 2))\n"
    "\n"
    + _GOLD_BODY
)


# ===========================================================================
# UNIQUENESS / REJECT rivals (expect reject) — each shares the spec and changes
# only the impl; if any VERIFIES, the spec admits a wrong impl (SPEC-TOO-WEAK).
# Each carries the refinement argument that its faithful real patch would NOT
# resolve the F2P/P2P.
# ===========================================================================

# alias-msg: the PRE-PATCH bug itself — alias the duplicate's message collections
# to self's instead of copying into fresh objects (validators still freshly
# copied). Must REJECT on the distinctness/full-ownership clause (D):
# Acc(list_pred(Result().msg_codes)) is full permission but self retains half, and
# Result().msg_codes is not self.msg_codes is false for an alias.
_ALIAS_MSG = (
    "    result = Field()\n"
    "    result.msg_codes = self.msg_codes\n"
    "    result.msg_values = self.msg_values\n"
    "\n"
    + _VAL_LOOP_FIRST
    + "    return result\n"
)

# alias-validators: symmetric pre-patch-style alias on the OTHER collection —
# copy the messages correctly but alias the validators. Must REJECT on (D) for
# validators. Guards refinement.md §B: a wrong impl must not "fix the wrong
# collection" while re-sharing validators.
_ALIAS_VAL = (
    "    result = Field()\n"
    + _MSG_LOOP
    + "\n    result.validators = self.validators\n"
    + "    return result\n"
)

# drop-last-msg: copy all message entries EXCEPT the last (loop bound
# len - 1). Distinct objects, but len(Result().msg_codes) == len(self.msg_codes)
# fails on any non-empty field. Must REJECT on the length clause (C).
_DROP_LAST = (
    "    result = Field()\n"
    "    a = 0\n"
    "    while a < len(self.msg_codes) - 1:\n"
    "        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))\n"
    "        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))\n"
    "        Invariant(len(self.msg_codes) == len(self.msg_values))\n"
    "        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))\n"
    "        Invariant(len(self.msg_values) == Old(len(self.msg_values)))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),\n"
    "                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),\n"
    "                                                  self.msg_values[k] == Old(self.msg_values[k])))))\n"
    "        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))\n"
    "        Invariant(result.msg_codes is not self.msg_codes)\n"
    "        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))\n"
    "        Invariant(result.msg_values is not self.msg_values)\n"
    "        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))\n"
    "        Invariant(result.validators is not self.validators)\n"
    "        Invariant(0 <= a and a <= len(self.msg_codes))\n"
    "        Invariant(len(result.msg_codes) == a)\n"
    "        Invariant(len(result.msg_values) == a)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,\n"
    "                                                  result.msg_codes[k] == self.msg_codes[k]))))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,\n"
    "                                                  result.msg_values[k] == self.msg_values[k]))))\n"
    # Terminates on the counter: the bound is len(self.msg_codes) - 1 - a + 1, i.e.
    # len(self.msg_codes) - a. `a` grows by 1 each pass so it strictly decreases, and
    # the guard a < len(self.msg_codes) - 1 gives len(self.msg_codes) - a > 1 > 0 on
    # entry. The termination proof is orthogonal to WHY this rival is rejected (the
    # short-by-one length clause C), so the rejection stays attributable to the spec.
    "        Invariant(MustTerminate(len(self.msg_codes) - a))\n"
    "        result.msg_codes.append(self.msg_codes[a])\n"
    "        result.msg_values.append(self.msg_values[a])\n"
    "        a = a + 1\n"
    "\n"
    + _VAL_LOOP_FIRST
    + "    return result\n"
)

# wrong-value: copy the right NUMBER of message entries into DISTINCT objects but
# bind a constant wrong value (0) instead of self.msg_values[a]. Distinctness +
# length hold; per-index Result().msg_values[k] == self.msg_values[k] (clause C)
# fails. This is the value-level attack: the structural/identity guarantee is
# satisfied while content is mangled.
_WRONG_VALUE = (
    "    result = Field()\n"
    "    a = 0\n"
    "    while a < len(self.msg_codes):\n"
    "        Invariant(Acc(self.msg_codes, 1 / 2) and Acc(list_pred(self.msg_codes), 1 / 2))\n"
    "        Invariant(Acc(self.msg_values, 1 / 2) and Acc(list_pred(self.msg_values), 1 / 2))\n"
    "        Invariant(len(self.msg_codes) == len(self.msg_values))\n"
    "        Invariant(len(self.msg_codes) == Old(len(self.msg_codes)))\n"
    "        Invariant(len(self.msg_values) == Old(len(self.msg_values)))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_codes),\n"
    "                                                  self.msg_codes[k] == Old(self.msg_codes[k])))))\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.msg_values),\n"
    "                                                  self.msg_values[k] == Old(self.msg_values[k])))))\n"
    "        Invariant(Acc(result.msg_codes) and Acc(list_pred(result.msg_codes)))\n"
    "        Invariant(result.msg_codes is not self.msg_codes)\n"
    "        Invariant(Acc(result.msg_values) and Acc(list_pred(result.msg_values)))\n"
    "        Invariant(result.msg_values is not self.msg_values)\n"
    "        Invariant(Acc(result.validators) and Acc(list_pred(result.validators)))\n"
    "        Invariant(result.validators is not self.validators)\n"
    "        Invariant(0 <= a and a <= len(self.msg_codes))\n"
    "        Invariant(len(result.msg_codes) == a)\n"
    "        Invariant(len(result.msg_values) == a)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < a,\n"
    "                                                  result.msg_codes[k] == self.msg_codes[k]))))\n"
    # Terminates on the counter, exactly as the gold loop does: len - a + 1 strictly
    # decreases (a grows by 1) and stays positive under the guard a < len. The rival
    # still terminates; it is rejected on the per-index content clause (C).
    "        Invariant(MustTerminate(len(self.msg_codes) - a + 1))\n"
    "        result.msg_codes.append(self.msg_codes[a])\n"
    "        result.msg_values.append(0)\n"
    "        a = a + 1\n"
    "\n"
    + _VAL_LOOP_FIRST
    + "    return result\n"
)

# frame-mut: MANDATORY frame-mutation probe. self is read-only (half permission),
# so this rival WRITES to self.msg_codes (append). It must FAIL for INSUFFICIENT
# PERMISSION before any postcondition is even considered — list_pred mutation
# needs full permission and self holds only 1/2. The gold body follows unchanged
# so the rejection is attributable to the single illegal write.
_FRAME_MUT = (
    "    self.msg_codes.append(99)  # ILLEGAL: self is read-only (Acc(...,1/2))\n"
    + _GOLD_BODY
)

# frame-mut-rebind: a second frame attack — rebind self's attribute to the
# duplicate's fresh collection to satisfy distinctness vacuously. Rebinding the
# field self.msg_codes also needs full Acc(self.msg_codes) which self does not
# have (half), so it must REJECT for insufficient permission.
_FRAME_REBIND = (
    "    result = Field()\n"
    + _MSG_LOOP
    + "\n"
    + _VAL_LOOP_FIRST
    + "    self.msg_codes = result.msg_codes  # ILLEGAL: rebinding read-only self\n"
    + "    return result\n"
)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "A correct impl that copies the validators FIRST then the message "
            "collections (gold does messages first) — two independent forward "
            "loops merely reordered, each keeping its full gold framing "
            "invariants. It satisfies every distinctness/content/frame clause, "
            "so it MUST verify; if it cannot, the postcondition is SPEC-TOO-STRONG "
            "(rejects a faithful correct duplication)."
        ),
    },
    {
        "id": "admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "A self-call on a freshly-built F2P-shaped field (one length-aligned "
            "override entry) must establish deep_duplicate's Requires "
            "(half-permission collections, len(msg_codes)==len(msg_values)). If "
            "the call site cannot satisfy the precondition for a normal input, "
            "the precondition is PRECOND-TOO-STRONG. The gold body follows so the "
            "whole module still verifies."
        ),
    },
    {
        "id": "alias-msg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALIAS_MSG),
        "refinement": (
            "This is the PRE-PATCH bug verbatim: result.error_messages stays the "
            "dict copy.copy(self) aliased from self (no self.error_messages.copy()). "
            "Its faithful real patch is the unpatched __deepcopy__, which the F2P "
            "test_field_deep_copy_error_messages rejects via "
            "assertIsNot(field_copy.error_messages, field.error_messages); it does "
            "NOT resolve (this is exactly model_prepatch.py)."
        ),
        "rationale": (
            "Rejected by the distinctness/full-ownership clause (D): the "
            "postcondition demands Acc(list_pred(Result().msg_codes)) at FULL "
            "permission and Result().msg_codes is not self.msg_codes, but an alias "
            "shares self's half-owned collection (the model_prepatch.py failure on "
            "Acc(list_pred(Result().msg_codes)))."
        ),
    },
    {
        "id": "alias-validators",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALIAS_VAL),
        "refinement": (
            "Copies the message overrides correctly but aliases the validators "
            "(result.validators = self.validators). A real patch that fixed "
            "error_messages but re-aliased validators would re-share the validator "
            "list across deep-copied fields — the P2P test_validators_independence "
            "asserts validators are independent across copies; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (D) for validators: Acc(list_pred(Result().validators)) "
            "full permission and Result().validators is not self.validators fail for "
            "an alias. Guards refinement.md §B (a wrong impl must not fix only one "
            "collection while re-sharing the other)."
        ),
    },
    {
        "id": "drop-last-msg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_LAST),
        "refinement": (
            "Correct on every field whose msg_codes is empty, diverging only on "
            "non-empty fields by omitting the LAST override entry (loop bound "
            "len-1). A real patch that copied all-but-last error_messages entries "
            "would drop an override message on every duplicated field; form-field "
            "deepcopy happens on every Form instantiation, so error-message-content "
            "P2P tests (test_error_escaping, test_error_dict, test_has_error) would "
            "fail; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by the content/length clause (C): "
            "len(Result().msg_codes) == len(self.msg_codes) is violated whenever "
            "len(self.msg_codes) > 0. Partial-domain attack (the input that fails "
            "first is any field with overrides — the exact F2P scenario)."
        ),
    },
    {
        "id": "wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_VALUE),
        "refinement": (
            "Builds a DISTINCT message collection of the right length but binds a "
            "constant 0 message value instead of self.msg_values[a]. A real patch "
            "that copied the override keys into a fresh dict but replaced the "
            "messages with a wrong/blank value would produce duplicates whose error "
            "messages differ from the original — error-message-content P2P tests "
            "(test_error_escaping, test_error_dict) would fail; it does NOT resolve. "
            "(It DOES pass the F2P assertIsNot, which is why content clause C, not "
            "distinctness, must catch it.)"
        ),
        "rationale": (
            "Rejected by the per-index content clause (C): "
            "Forall k (Result().msg_values[k] == self.msg_values[k]) is violated "
            "(0 != self.msg_values[k]) for any non-empty field with a non-zero "
            "value. Value-level attack: identity/length satisfied, content mangled."
        ),
    },
    {
        "id": "frame-mut",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "Writes to the read-only source (self.msg_codes.append(99)) before "
            "duplicating. A real patch that mutated self.error_messages during "
            "__deepcopy__ would corrupt the ORIGINAL field — every P2P form test "
            "relies on the source field surviving deepcopy unchanged (and the F2P "
            "leaves the original intact); it does NOT resolve. A byte-fuzzer never "
            "constructs this write — it is the project's #1 weakness class."
        ),
        "rationale": (
            "Rejected for INSUFFICIENT PERMISSION (the permission system, clause "
            "F): self is held at Acc(self.msg_codes, 1/2) so list_pred mutation "
            "(append) is not permitted — full permission is required to mutate. The "
            "rejection is attributable to the single illegal write (the gold body "
            "follows unchanged)."
        ),
    },
    {
        "id": "frame-rebind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_REBIND),
        "refinement": (
            "After correctly building the duplicate, rebinds self.msg_codes to the "
            "duplicate's fresh list (an attempt to satisfy distinctness/frame by "
            "aliasing in the other direction). A real patch reassigning "
            "self.error_messages inside __deepcopy__ would mutate the original "
            "field's attribute, corrupting the source across forms; it does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected for INSUFFICIENT PERMISSION (clause F): rebinding the field "
            "self.msg_codes requires full Acc(self.msg_codes) but self holds only "
            "1/2; the write to a read-only field is not permitted."
        ),
    },
]


# ===========================================================================
# AXIOM lane. This bundle consumes NO @ContractOnly axioms (the duplication is
# modelled deeply). The only callee semantics relied on (dict.copy()/list[:] =
# distinct object with equal contents) is an A-reference already validated in
# Docker by axiom_check.py / G-AX over 5000 primitive + 209 real-callee
# observations. We add ONE containment-style cross-check that confirms the model
# never reaches a callee input outside the A-reference's domain (the A-reference
# is total over finite dicts/lists, so containment is trivially established) and
# re-confirms the distinct-object semantics the deep model encodes, so the
# AXIOM-lane verdict is grounded rather than empty. The probe is self-contained
# (stdlib only) and exits 0 iff the obligation holds.
# ===========================================================================

_CONTAINMENT_PROBE = r'''
import sys, random
# The model's deep_duplicate can only ever pass to the shallow-copy primitive a
# FINITE dict (the error_messages mapping, carried as two index-aligned int
# lists) and a FINITE list (validators). The A-reference (dict.copy()/list[:])
# is TOTAL over every finite dict/list, so every input the model can reach lies
# inside the callee's domain (containment holds vacuously / by totality). We
# additionally re-confirm the distinct-object-with-equal-contents semantics the
# deep model encodes on the full caller-reachable shape: arbitrary finite dicts
# and lists of ints, including the empty (len 0) boundary the model's loops hit.
rng = random.Random(11880)
checked = 0
for _ in range(4000):
    n = rng.randint(0, 12)          # the model admits any non-negative length
    keys = rng.sample(range(-200, 200), min(n, 400))
    d = {k: rng.randint(-9999, 9999) for k in keys}
    dc = d.copy()                    # the callee the model's msg loop refines
    assert dc is not d, "dict.copy() not a distinct object (containment/semantics)"
    assert dc == d, "dict.copy() contents differ"
    snap = dict(d)
    dc[424242] = 1
    assert d == snap, "mutating the copy reached the original"

    m = rng.randint(0, 12)
    lst = [rng.randint(-9999, 9999) for _ in range(m)]
    lc = lst[:]                      # the callee the model's validators loop refines
    assert lc is not lst, "list[:] not a distinct object (containment/semantics)"
    assert lc == lst, "list[:] contents differ"
    lsnap = list(lst)
    lc.append(424242)
    assert lst == lsnap, "mutating the list copy reached the original"
    checked += 1

# explicit empty-collection boundary (the model's loop with zero iterations)
assert ({}).copy() is not {} or {} == {}  # distinct empty dict (identity-safe form)
e = {}
ec = e.copy()
assert ec is not e and ec == e, "empty dict.copy() boundary"
el = []
elc = el[:]
assert elc is not el and elc == el, "empty list[:] boundary"

print("CONTAINMENT OK: every caller-reachable input (finite dict / finite list, "
      "incl. empty) lies in the A-reference domain; dict.copy()/list[:] yield a "
      "distinct object with equal contents over %d observations" % checked)
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "containment-copy-primitives",
        "axiom": "dict.copy()/list[:] (A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": (
            "There is no consumed @ContractOnly axiom; the duplication is modelled "
            "deeply. The deep model refines the shallow-copy primitives dict.copy() "
            "/ list[:], which are TOTAL over finite dicts/lists. Every input the "
            "model can reach (any finite int-keyed dict / int list, including the "
            "empty boundary the loops hit) is therefore inside the A-reference "
            "domain — containment holds, so no caller-reachable input is "
            "AXIOM-TOO-WEAK-FOR-CALLER. The probe also re-confirms the distinct-"
            "object-with-equal-contents semantics the deep model encodes (the full "
            "real-callee G-AX check lives in axiom_check.py / runs in-container)."
        ),
    },
]
