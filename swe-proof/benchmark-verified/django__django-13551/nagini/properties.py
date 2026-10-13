# properties.py — PBT falsification battery for django__django-13551.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of make_hash_value for a new
# body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides the entire impl region (nested
# invariants included), so same_spec is GUARANTEED for every case regardless of
# the proof scaffolding inside.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   make_hash_value(user, timestamp) -> List[int] pins, on the verified output:
#     (P1) ToSeq(Result()) ==
#            ToSeq(user.pk) + ToSeq(user.password) + ToSeq(user.login_repr) +
#            ToSeq(timestamp) + effective_address(user.address)
#          -- the EXACT in-order 5-component concatenation, the contact address
#             last; this is the discriminating fix (email now in the fingerprint).
#     (P2) ToSeq(Result()).drop(len(pk)+len(password)+len(login_repr)+len(timestamp))
#            == effective_address(user.address)
#          -- redundant trailing-segment clause; an anti-double-mask guard pinning
#             that what follows the four fixed components is EXACTLY the resolved
#             address (no value-proxy can drop a disagreeing tail index).
#   effective_address(addr): the empty sequence when addr is None or len(addr)==0,
#   else ToSeq(addr). It is @Pure and fully GROUNDED/transparent in its argument
#   (no opaque answer-key) -- so there is no "wrong echo": any impl that satisfies
#   P1/P2 has actually built the concatenation. See 'assessment'.
#
#   The behaviour the F2P "Updating the user email address invalidates the token"
#   exercises is precisely (P1)+(P2): a token minted before an email change no
#   longer matches the post-change fingerprint, because the email is a fingerprint
#   component. The pre-patch body returned only the 4-component concatenation
#   (model_prepatch.py) and FAILS P1/P2 whenever the resolved address is non-empty.
#
# READ-ONLY INPUTS (Acc(...,1/2)) -> FRAME-MUTATION IS MANDATORY:
#   user.pk, user.password, user.login_repr (each Acc(field,1/2) + Acc(list_pred,1/2)),
#   user.address (Acc(user.address,1/2) + guarded Acc(list_pred,1/2)),
#   timestamp (Acc(list_pred(timestamp),1/2)). The fingerprint mutates nothing it
#   is given, and the Ensures hands every fraction back. An impl that WRITES to any
#   of these holds only half permission and must be rejected for INSUFFICIENT
#   PERMISSION (frame-mutation case below).
from pathlib import Path

INSTANCE = "django__django-13551"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of make_hash_value (verified verbatim from model.py). Each variant re-emits
# `# impl-start` first and `# impl-end` last so the region boundary is preserved
# exactly -- only the body between them changes, and spec_view elides all of it.
# ---------------------------------------------------------------------------

_GOLD_IMPL = (Path(__file__).parent / "model.py").read_text()
_S = _GOLD_IMPL.index("# impl-start")
_E = _GOLD_IMPL.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _GOLD_IMPL[_S:_E]
assert _GOLD_IMPL.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace make_hash_value's whole impl block with a new body. `body_lines`
    is the source BETWEEN the markers (no markers); we wrap it back in the exact
    `# impl-start` / `# impl-end` markers so the region is intact."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The four leading per-component loops + their asserts, verbatim from gold. Reused
# by several variants so attacks differ only in how they treat the trailing
# address segment (or in a deliberate corruption). Indentation matches model.py.
_GOLD_PREFIX_LOOPS = """    # Ghost snapshots of the component sequences, so the loop invariants read
    # only locals (each field's fractional permission is held by the frame).
    pk_s = ToSeq(user.pk)
    pw_s = ToSeq(user.password)
    lr_s = ToSeq(user.login_repr)
    ts_s = ToSeq(timestamp)

    result = []  # type: List[int]
    i = 0
    while i < len(user.pk):
        # invariants-start
        Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
        Invariant(pk_s == ToSeq(user.pk))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.pk))
        Invariant(ToSeq(result) == pk_s.take(i))
        Invariant(MustTerminate(len(user.pk) - i + 1))
        # invariants-end
        result.append(user.pk[i])
        i = i + 1
    Assert(pk_s.take(len(user.pk)) == pk_s)

    i = 0
    while i < len(user.password):
        # invariants-start
        Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
        Invariant(pw_s == ToSeq(user.password))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.password))
        Invariant(ToSeq(result) == pk_s + pw_s.take(i))
        Invariant(MustTerminate(len(user.password) - i + 1))
        # invariants-end
        result.append(user.password[i])
        i = i + 1
    Assert(pw_s.take(len(user.password)) == pw_s)

    i = 0
    while i < len(user.login_repr):
        # invariants-start
        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
        Invariant(lr_s == ToSeq(user.login_repr))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.login_repr))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
        Invariant(MustTerminate(len(user.login_repr) - i + 1))
        # invariants-end
        result.append(user.login_repr[i])
        i = i + 1
    Assert(lr_s.take(len(user.login_repr)) == lr_s)

    i = 0
    while i < len(timestamp):
        # invariants-start
        Invariant(Acc(list_pred(timestamp), 1 / 2))
        Invariant(ts_s == ToSeq(timestamp))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(timestamp))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
        Invariant(MustTerminate(len(timestamp) - i + 1))
        # invariants-end
        result.append(timestamp[i])
        i = i + 1
    Assert(ts_s.take(len(timestamp)) == ts_s)
"""

# The trailing address loop, verbatim from gold (the discriminating segment).
_GOLD_ADDR_LOOP = """    addr = user.address
    if addr is not None:
        addr_s = ToSeq(addr)
        j = 0
        while j < len(addr):
            # invariants-start
            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))
            Invariant(addr_s == ToSeq(addr))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(addr))
            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))
            Invariant(MustTerminate(len(addr) - j + 1))
            # invariants-end
            result.append(addr[j])
            j = j + 1
        Assert(addr_s.take(len(addr)) == addr_s)
    return result
"""


SPEC_TESTS = [

    # ------------------------------------------------------------- soundness (1)
    # POSITIVE CONTROL A (low-risk reshape): keep the gold proof structure and
    # every gold invariant/assert VERBATIM, but change the executable shape:
    # the address loop is entered only when the address is non-None AND non-empty
    # (gold runs a 0-iteration loop on an empty address; this skips it). When the
    # address is empty, effective_address(addr) is the empty sequence and the
    # prefix already equals the spec RHS -- so this is a genuinely different
    # control flow that is still CORRECT. No fold/append-direction lemma is
    # introduced (forward append against a front-take spec is exactly the gold
    # shape, kept intact). If this cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-empty-addr-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _GOLD_PREFIX_LOOPS +
            "\n"
            "    addr = user.address\n"
            "    if addr is not None and len(addr) > 0:\n"
            "        addr_s = ToSeq(addr)\n"
            "        j = 0\n"
            "        while j < len(addr):\n"
            "            # invariants-start\n"
            "            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))\n"
            "            Invariant(addr_s == ToSeq(addr))\n"
            "            Invariant(Acc(list_pred(result)))\n"
            "            Invariant(0 <= j and j <= len(addr))\n"
            "            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))\n"
            "            Invariant(MustTerminate(len(addr) - j + 1))\n"
            "            # invariants-end\n"
            "            result.append(addr[j])\n"
            "            j = j + 1\n"
            "        Assert(addr_s.take(len(addr)) == addr_s)\n"
            "    return result\n"
        ),
        "rationale": "a correct impl with a DIFFERENT control flow (explicit "
                     "non-empty guard vs gold's 0-iteration loop on []) must verify; "
                     "effective_address([]) is the empty sequence so the 4-component "
                     "prefix already equals the spec RHS. Keeps every gold "
                     "invariant/assert (no dropped framing); no fold lemma. Else "
                     "SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------- soundness (2)
    # POSITIVE CONTROL B (honest cheapest, grounded oracle): the oracle
    # effective_address is GROUNDED/transparent (no opaque answer-key), so the
    # cheapest correct impl simply rebuilds the concatenation -- which is the real
    # work. This control renames the loop index in the address loop (j -> k),
    # rebinds the snapshot, and rewrites `i = i + 1` as the equivalent forward
    # step, keeping every invariant. Stands IN PLACE of an ungrounded-oracle echo
    # (there is no wrong echo to build). If it cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-rename-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _GOLD_PREFIX_LOOPS +
            "\n"
            "    addr = user.address\n"
            "    if addr is not None:\n"
            "        addr_s = ToSeq(addr)\n"
            "        k = 0\n"
            "        while k < len(addr):\n"
            "            # invariants-start\n"
            "            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))\n"
            "            Invariant(addr_s == ToSeq(addr))\n"
            "            Invariant(Acc(list_pred(result)))\n"
            "            Invariant(0 <= k and k <= len(addr))\n"
            "            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(k))\n"
            "            # The address-appending loop runs to the element count, so\n"
            "            # len(addr) - k + 1 stays positive and strictly decreases.\n"
            "            Invariant(MustTerminate(len(addr) - k + 1))\n"
            "            # invariants-end\n"
            "            result.append(addr[k])\n"
            "            k = k + 1\n"
            "        Assert(addr_s.take(len(addr)) == addr_s)\n"
            "    return result\n"
        ),
        "rationale": "grounded-oracle honest positive control: the cheapest correct "
                     "impl rebuilds the exact concatenation (the real work); a "
                     "local-variable reshape (j->k) that keeps every gold invariant "
                     "must verify. No wrong echo exists (effective_address is "
                     "transparent in its arg). Else SPEC-TOO-STRONG.",
    },

    # --------------------------------------------------------- admissibility (1)
    # ADMISSIBILITY: a self-call caller constructs a fresh Account (the constructor
    # establishes full permission to all four fields + address is None) and a fresh
    # timestamp list, then invokes make_hash_value on this F2P-shaped input. The
    # call must establish the Requires (the constructor's Ensures give full perms;
    # passing halves is admissible) and the post facts must be derivable. If the
    # Requires cannot be met for a normal input => PRECOND-TOO-STRONG. The caller
    # lives strictly inside the impl region (spec untouched).
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            _GOLD_PREFIX_LOOPS + _GOLD_ADDR_LOOP +
            "    # admissibility probe (after `return result`, unreachable code is\n"
            "    # not verified; instead we self-call BEFORE returning via a guard).\n"
        ),
        "rationale": "placeholder replaced below by admiss body; see note.",
    },

    # ---------------------------------------------------------------- uniqueness
    # ATTACK 1 (FRAME-MUTATION, MANDATORY -- the #1 weakness class). The impl
    # OVERWRITES the read-only input user.pk (clears it) before building the
    # fingerprint, attempting to make the prefix trivially controllable. Only
    # Acc(user.pk, 1/2) is held, so a WRITE to user.pk requires full permission and
    # the verifier MUST reject this for INSUFFICIENT PERMISSION -- not for a value
    # mismatch. The gold postcondition/invariants are kept verbatim so the
    # rejection is attributable solely to the illegal write.
    {
        "id": "frame-mutate-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input.\n"
            "    user.pk = []\n" +
            _GOLD_PREFIX_LOOPS + _GOLD_ADDR_LOOP
        ),
        "refinement": "in the real django code user.pk is the account primary key; "
                      "_make_hash_value is a pure read-only fingerprint and must "
                      "never reassign user.pk. A patch that clears user.pk corrupts "
                      "the in-memory user object that the caller (the password-reset "
                      "flow) still holds and would mint a fingerprint over an empty "
                      "pk -- every token-generation P2P test (test_make_token, "
                      "test_check_token_*) and the F2P would diverge. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(user.pk, 1/2); a write needs full permission. Insufficient "
                     "permission, not a value mismatch. This is the mandatory "
                     "frame-mutation probe.",
    },

    # ATTACK 2 (FRAME-MUTATION on the address). Same class, on the Optional input,
    # but against the OTHER HALF of its grant: the address's CONTENTS. The impl
    # appends a code point to the account's live address list before building the
    # fingerprint. The precondition grants only
    # Implies(user.address is not None, Acc(list_pred(user.address), 1/2)), and
    # append needs FULL permission on the list => insufficient permission, not a
    # value mismatch. Gold postcondition/invariants verbatim, so the rejection is
    # attributable solely to the illegal write.
    #
    # It writes the CONTENTS rather than reassigning the FIELD because neither
    # field-write spelling reaches Viper on this bundle, and a rival that never
    # reaches Viper attributes nothing to the spec (nagini leaves with the same
    # exit 1 for a front-end failure as for a rejection):
    #   `user.address = None` -- mypy narrows the attribute to None-only, so the
    #     gold trailing loop's `if addr is not None:` body is unreachable and the
    #     front end stops at `Type error: dead.code (@179.0)`, no Viper verdict;
    #   `user.address = []`   -- translates, then silicon's prover aborts on its
    #     own encoding ("Expected 'success' but found: (error ... invalid function
    #     application, wrong number of arguments)") and nagini prints no verdict.
    # The FIELD write is probed by the frame-mutate-pk sibling above, on the
    # non-Optional user.pk, where it does reach a verdict ("Assignment might fail.
    # There might be insufficient permission to access user.pk."). The two cases
    # together cover Acc(user.<field>, 1/2) and Acc(list_pred(...), 1/2).
    #
    # The `addr0 is not None` guard is NOT vacuous -- an infeasible guard would
    # verify while proving nothing about the frame. The nonvac- case below is the
    # control: Assert(False) at this same write site, and it must be REFUTED.
    {
        "id": "frame-mutate-address",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to the read-only (Acc(list_pred(...), 1/2)) address input.\n"
            "    addr0 = user.address\n"
            "    if addr0 is not None:\n"
            "        addr0.append(0)\n" +
            _GOLD_PREFIX_LOOPS + _GOLD_ADDR_LOOP
        ),
        "refinement": "this extends the user's email attribute in place -- it appends "
                      "a code point to the live address value -- inside the "
                      "fingerprint routine. The real _make_hash_value only READS "
                      "getattr(user, email_field, ''); rewriting the attribute mutates "
                      "the live user that the caller (the password-reset flow) still "
                      "holds, so every subsequent fingerprint is taken over a "
                      "corrupted email -- the F2P 'updating the user email address "
                      "invalidates the token' relies on the email being READ, not "
                      "rewritten. The faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: for a non-None address the "
                     "precondition grants only Acc(list_pred(user.address), 1/2); "
                     "append needs full permission on the list. Insufficient "
                     "permission, not a value mismatch. Second mandatory "
                     "frame-mutation probe (the sibling probes the field, this the "
                     "contents).",
    },

    # NON-VACUITY CONTROL for ATTACK 2. Same prefix, same guard, with the illegal
    # append replaced by Assert(False): the one claim that can only be discharged
    # where control never arrives. If this VERIFIED, the guarded region would be
    # unreachable and ATTACK 2's insufficient-permission rejection would be an
    # artefact of an infeasible path rather than evidence about the frame -- so the
    # control belongs in the manifest next to it, not in a one-off measurement. It
    # must be REFUTED ("Assert might fail. Assertion False might not hold."), which
    # is what places the write on a path the precondition admits.
    {
        "id": "nonvac-frame-mutate-address-site",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # REACHABILITY CONTROL: unprovable at ATTACK 2's write site.\n"
            "    addr0 = user.address\n"
            "    if addr0 is not None:\n"
            "        Assert(False)\n" +
            _GOLD_PREFIX_LOOPS + _GOLD_ADDR_LOOP
        ),
        "refinement": "not a rival patch: a reachability control on the case above. "
                      "An account whose contact address is present is an ordinary "
                      "input of the real _make_hash_value (the F2P mints a token for "
                      "a user WITH an email), so the branch the frame-mutation probe "
                      "writes in is one the routine really takes, and False cannot be "
                      "proved there.",
        "rationale": "must be rejected because Assert(False) is unprovable on a "
                     "REACHABLE path. Verifying instead would mean the precondition "
                     "cannot supply a non-None address at all, i.e. ATTACK 2 rests on "
                     "an infeasible guard and certifies nothing about the frame.",
    },

    # ATTACK 3 (PARTIAL-DOMAIN -- the bug-delta / prepatch). Drop the email
    # entirely: build ONLY the four-component concatenation (exactly the pre-patch
    # body / model_prepatch.py). CORRECT on every account whose resolved address is
    # absent/empty, WRONG whenever the address is non-empty. Must reject: P1's
    # trailing effective_address(user.address) segment is absent, and P2's
    # drop(prefix_len) is empty rather than the resolved address.
    {
        "id": "weak-drop-email",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_PREFIX_LOOPS +
            "    return result\n"
        ),
        "refinement": "this is the PRE-PATCH body: "
                      "str(user.pk)+user.password+str(login_timestamp)+str(timestamp) "
                      "with NO email. The fingerprint is then invariant under an "
                      "email change, so a token minted before the change still "
                      "matches afterwards. The F2P "
                      "'Updating the user email address invalidates the token' "
                      "asserts the token is REJECTED after the email changes => the "
                      "faithful real patch (no email) FAILS the F2P; it does NOT "
                      "resolve. (= model_prepatch.py, G-DIFF.)",
        "rationale": "violates P1 (missing trailing effective_address(user.address) "
                     "segment) and P2 (drop(prefix_len) is empty, not the resolved "
                     "address) whenever the resolved address is non-empty.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN, off-by-one tail). Append the email but DROP its
    # last code point (loop to len(addr)-1). CORRECT on every empty/length-0/
    # length... no: correct only when the address is empty; WRONG on every
    # non-empty address (the trailing segment is one code point short). Targets P2
    # specifically: drop(prefix_len) would equal addr_s.take(len-1) != addr_s.
    {
        "id": "weak-email-truncated-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_PREFIX_LOOPS +
            "\n"
            "    addr = user.address\n"
            "    if addr is not None:\n"
            "        addr_s = ToSeq(addr)\n"
            "        j = 0\n"
            "        while j < len(addr) - 1:\n"
            "            # invariants-start\n"
            "            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))\n"
            "            Invariant(addr_s == ToSeq(addr))\n"
            "            Invariant(Acc(list_pred(result)))\n"
            "            Invariant(0 <= j and j <= len(addr))\n"
            "            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))\n"
            "            Invariant(MustTerminate(len(addr) - j + 1))\n"
            "            # invariants-end\n"
            "            result.append(addr[j])\n"
            "            j = j + 1\n"
            "    return result\n"
        ),
        "refinement": "this drops the final character of the email from the "
                      "fingerprint (e.g. 'a@b.com' contributes 'a@b.co'). Two "
                      "distinct emails sharing a (len-1)-prefix, e.g. 'a@b.com' vs "
                      "'a@b.con', would then collide -- a token minted before such an "
                      "email change would NOT be invalidated, and a normal email "
                      "change generally alters the dropped last char's position so "
                      "the fingerprint differs from the real f-string output. The "
                      "real f-string interpolates the WHOLE email; a truncated email "
                      "differs from the gold output and the F2P / token P2P diverge => "
                      "the faithful real patch does NOT resolve.",
        "rationale": "violates P1 and P2: the trailing segment equals "
                     "addr_s.take(len(addr)-1), not effective_address(addr) == addr_s, "
                     "on any non-empty address.",
    },

    # ATTACK 5 (VALUE DOUBLE-MASK / wrong order). The trailing-segment clause P2
    # exists precisely to stop a value-proxy from accepting a re-ordered output.
    # This impl emits password BEFORE pk (swaps the first two components) but still
    # appends the email last. The multiset of code points can match the gold for
    # many inputs, but P1 pins the EXACT in-order concatenation and P2 pins the
    # tail; either rejects. Must reject.
    {
        "id": "weak-reorder-pk-password",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    pk_s = ToSeq(user.pk)\n"
            "    pw_s = ToSeq(user.password)\n"
            "    lr_s = ToSeq(user.login_repr)\n"
            "    ts_s = ToSeq(timestamp)\n"
            "\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < len(user.password):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))\n"
            "        Invariant(pw_s == ToSeq(user.password))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(user.password))\n"
            "        Invariant(ToSeq(result) == pw_s.take(i))\n"
            "        # This value-building loop runs to the element count, so\n"
            "        # len(user.password) - i + 1 stays positive and strictly decreases.\n"
            "        Invariant(MustTerminate(len(user.password) - i + 1))\n"
            "        # invariants-end\n"
            "        result.append(user.password[i])\n"
            "        i = i + 1\n"
            "\n"
            "    i = 0\n"
            "    while i < len(user.pk):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))\n"
            "        Invariant(pk_s == ToSeq(user.pk))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(user.pk))\n"
            "        Invariant(ToSeq(result) == pw_s + pk_s.take(i))\n"
            "        # As above, over the primary-key component.\n"
            "        Invariant(MustTerminate(len(user.pk) - i + 1))\n"
            "        # invariants-end\n"
            "        result.append(user.pk[i])\n"
            "        i = i + 1\n"
            "\n"
            "    i = 0\n"
            "    while i < len(user.login_repr):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))\n"
            "        Invariant(lr_s == ToSeq(user.login_repr))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(user.login_repr))\n"
            "        Invariant(ToSeq(result) == pw_s + pk_s + lr_s.take(i))\n"
            "        # As above, over the sign-in component.\n"
            "        Invariant(MustTerminate(len(user.login_repr) - i + 1))\n"
            "        # invariants-end\n"
            "        result.append(user.login_repr[i])\n"
            "        i = i + 1\n"
            "\n"
            "    i = 0\n"
            "    while i < len(timestamp):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(timestamp), 1 / 2))\n"
            "        Invariant(ts_s == ToSeq(timestamp))\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= len(timestamp))\n"
            "        Invariant(ToSeq(result) == pw_s + pk_s + lr_s + ts_s.take(i))\n"
            "        # As above, over the issuing-timestamp component.\n"
            "        Invariant(MustTerminate(len(timestamp) - i + 1))\n"
            "        # invariants-end\n"
            "        result.append(timestamp[i])\n"
            "        i = i + 1\n"
            "\n"
            "    addr = user.address\n"
            "    if addr is not None:\n"
            "        addr_s = ToSeq(addr)\n"
            "        j = 0\n"
            "        while j < len(addr):\n"
            "            # invariants-start\n"
            "            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))\n"
            "            Invariant(addr_s == ToSeq(addr))\n"
            "            Invariant(Acc(list_pred(result)))\n"
            "            Invariant(0 <= j and j <= len(addr))\n"
            "            Invariant(ToSeq(result) == pw_s + pk_s + lr_s + ts_s + addr_s.take(j))\n"
            "            # As above, over the contact-address component.\n"
            "            Invariant(MustTerminate(len(addr) - j + 1))\n"
            "            # invariants-end\n"
            "            result.append(addr[j])\n"
            "            j = j + 1\n"
            "    return result\n"
        ),
        "refinement": "this concatenates password before pk: "
                      "f'{user.password}{user.pk}{login_timestamp}{timestamp}{email}'. "
                      "The real gold f-string is "
                      "f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'; "
                      "for any user where pk != password (the overwhelming common "
                      "case -- pk is a small integer, password is a salted hash) the "
                      "fingerprint string differs, so salted_hmac yields a different "
                      "token and token check/round-trip P2P tests (test_make_token, "
                      "test_check_token_*) FAIL. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates P1: ToSeq(Result()) == pw ++ pk ++ ... != "
                     "pk ++ pw ++ ... whenever pk != password. P2's tail still holds, "
                     "so P1 is the discriminator -- the order is load-bearing.",
    },

    # ATTACK 6 (PARTIAL-DOMAIN, address echoed when EMPTY too). Subtle: emit the
    # email loop but use the RAW address even when it is empty -- harmless there --
    # AND, when the address is None, append a fixed sentinel code point. CORRECT
    # only when address is non-None; WRONG when address is None (effective_address
    # is empty but the impl appends a sentinel). Targets the None branch of P1/P2.
    {
        "id": "weak-none-address-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_PREFIX_LOOPS +
            "\n"
            "    addr = user.address\n"
            "    if addr is not None:\n"
            "        addr_s = ToSeq(addr)\n"
            "        j = 0\n"
            "        while j < len(addr):\n"
            "            # invariants-start\n"
            "            Invariant(addr is not None and Acc(list_pred(addr), 1 / 2))\n"
            "            Invariant(addr_s == ToSeq(addr))\n"
            "            Invariant(Acc(list_pred(result)))\n"
            "            Invariant(0 <= j and j <= len(addr))\n"
            "            Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s + addr_s.take(j))\n"
            "            Invariant(MustTerminate(len(addr) - j + 1))\n"
            "            # invariants-end\n"
            "            result.append(addr[j])\n"
            "            j = j + 1\n"
            "        Assert(addr_s.take(len(addr)) == addr_s)\n"
            "    else:\n"
            "        # WRONG: a None (absent) address must contribute the EMPTY\n"
            "        # sequence, but this appends a sentinel code point.\n"
            "        result.append(88)\n"
            "    return result\n"
        ),
        "refinement": "this appends a spurious sentinel character for accounts with "
                      "NO email attribute (getattr(...,'') or '' yields ''). The real "
                      "f-string interpolates an empty email -> the four-component "
                      "fingerprint with nothing appended. Adding a sentinel makes the "
                      "fingerprint differ from the real output for every email-less "
                      "user, so their tokens never round-trip; the token P2P tests "
                      "(test_make_token / test_check_token with a user whose email is "
                      "blank) FAIL. The faithful real patch does NOT resolve.",
        "rationale": "violates P1/P2 on the addr-None branch: effective_address(None) "
                     "is the empty sequence, so the result must equal the 4-component "
                     "prefix; appending code point 88 makes the tail non-empty.",
    },
]


# ---------------------------------------------------------------------------
# Replace the admissibility placeholder with the probe body. A fresh Account
# (constructor establishes full permission to pk/password/login_repr and address
# is None) plus a freshly-built empty timestamp list is a legitimate F2P-shaped
# input. CONSTRUCTING it is itself part of the probe — the call must establish the
# constructor's own Requires — and the probe then ASSERTS each Requires clause of
# make_hash_value at that witness (halves of the constructor's full permissions).
#
# A self-call on the probe is no longer usable as the witness: the method carries
# a termination obligation and is never strictly below ITSELF, so Nagini reports
# `Obligation leak check failed. Callee make_hash_value might not take all
# unsatisfied obligations from the caller.` — a termination fact, not a fact about
# the precondition's domain, so it would attribute nothing. (Measured: with the
# method's level raised so the CONSTRUCTOR call is legal, the self-call is the one
# remaining leak.) Asserting the establishability of each Requires clause is the
# same substitution django__django-14580 uses for this reason.
#
# NEGATIVE CONTROL (proves the probe can fail, i.e. is not a tautology): moving
# the witness OUTSIDE what the constructed account establishes — claiming
# Assert(probe_user.address is not None) of an account built WITHOUT a contact
# address — is REJECTED by the verifier with
#   error: Assert might fail. Assertion (probe_user.address is not None) might not
#   hold.
# and, independently, claiming Assert(len(probe_ts) >= 1) of the freshly-built
# empty timestamp is REJECTED with
#   error: Assert might fail. Assertion (len(probe_ts) >= 1) might not hold.
# So the asserts below are discharged by the witness, not by triviality.
# ---------------------------------------------------------------------------
_ADMISS_BODY = (
    _GOLD_PREFIX_LOOPS + _GOLD_ADDR_LOOP.rstrip("\n").rsplit("\n    return result", 1)[0] +
    "\n"
    "    # Admissibility probe: a fresh Account + empty timestamp is an F2P-shaped\n"
    "    # in-domain input. Building it must establish the constructor's own\n"
    "    # Requires, and each Requires clause of make_hash_value must then hold of\n"
    "    # it; if the precondition could not be established for this normal input\n"
    "    # the asserts would fail => PRECOND-TOO-STRONG.\n"
    "    probe_user = Account()\n"
    "    probe_ts = []  # type: List[int]\n"
    "    # Requires clauses 1-3: each component field and its container are\n"
    "    # accessible at the half share the call consumes.\n"
    "    Assert(Acc(probe_user.pk, 1 / 2) and Acc(list_pred(probe_user.pk), 1 / 2))\n"
    "    Assert(Acc(probe_user.password, 1 / 2) and\n"
    "           Acc(list_pred(probe_user.password), 1 / 2))\n"
    "    Assert(Acc(probe_user.login_repr, 1 / 2) and\n"
    "           Acc(list_pred(probe_user.login_repr), 1 / 2))\n"
    "    # Requires clauses 4-5: the contact-address field is accessible, and the\n"
    "    # guarded container clause holds vacuously for an account with none.\n"
    "    Assert(Acc(probe_user.address, 1 / 2))\n"
    "    Assert(probe_user.address is None)\n"
    "    Assert(Implies(probe_user.address is not None,\n"
    "                   Acc(list_pred(probe_user.address), 1 / 2)))\n"
    "    # Requires clause 6: the timestamp container is accessible.\n"
    "    Assert(Acc(list_pred(probe_ts), 1 / 2))\n"
    "    Assert(len(probe_ts) == 0)\n"
    "    return result\n"
)
for _c in SPEC_TESTS:
    if _c["id"] == "admiss-self-call":
        _c["module"] = _impl(_ADMISS_BODY)
        _c["rationale"] = (
            "the precondition must admit a normal F2P-shaped input: a fresh "
            "Account (no contact address; full perms from the constructor) and an "
            "empty timestamp list. Building it must establish the constructor's "
            "own Requires, and the probe then ASSERTS each Requires clause of "
            "make_hash_value at that witness — the three component fields and "
            "their containers at the half share the call consumes, the "
            "contact-address field plus its guarded container clause (vacuous for "
            "an account with none), and the timestamp container. The gold body is "
            "kept verbatim, so the postcondition obligation is unchanged. If the "
            "Requires could not be established for this normal input => "
            "PRECOND-TOO-STRONG. A self-call is no longer usable as the witness: "
            "the method is never strictly below ITSELF, so it fails with "
            "`Obligation leak check failed. Callee make_hash_value might not take "
            "all unsatisfied obligations from the caller.` — a termination fact "
            "attributing nothing about the domain (measured). NEGATIVE CONTROL "
            "(the probe is a real check, not a tautology): claiming "
            "Assert(probe_user.address is not None) of an account built without a "
            "contact address is REJECTED with `error: Assert might fail. Assertion "
            "(probe_user.address is not None) might not hold.`, and "
            "Assert(len(probe_ts) >= 1) of the empty timestamp is REJECTED with "
            "`error: Assert might fail. Assertion (len(probe_ts) >= 1) might not "
            "hold.` (both measured)."
        )


# No @ContractOnly axioms and no consumed-axiom proof step in this bundle
# (meta.axioms == [], axioms region is an empty singleton). The ONLY callee-level
# obligation is the A-reference deep model (effective_address + the 5-component
# concatenation == the real getattr(...,'') or '' + f-string derivation), which is
# already validated on the HOST by axiom_check.py / G-AX (10 boundary + 20000 fuzz,
# exit 0). effective_address itself is in the verified spec module as a transparent
# @Pure function -- there is no separate runtime callee whose Ensures could drift,
# so there is no axiom-soundness obligation to re-probe and no caller-reachable
# input outside any axiom domain (no axiom domain exists). We therefore re-run the
# bundle's host-validated G-AX oracle in-container as the single axiom-lane probe,
# so the A-reference deep model is grounded in the REAL python getattr + f-string
# construction (not a regex over source), per the plan. It CALLS the real
# construction; it reads no files (no utf-8 codec concern); the runner mounts only
# this probe script (axiom_check.py is embedded verbatim from the HOST at load).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-effective-address-concatenation",
        "axiom": "effective_address+5-component-concatenation (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness/containment: the deep model "
                     "(effective_address + the in-order 5-component concatenation) "
                     "must equal the REAL gold derivation -- get_email_field_name + "
                     "getattr(user, field, '') or '' + the f-string -- at the "
                     "code-point level, on every input the model can reach (None / "
                     "'' / missing-attr / renamed EMAIL_FIELD / non-ASCII / empty "
                     "components + 20000 fuzz). It also asserts the trailing-segment "
                     "clause on the REAL output (no double-mask) and the F2P "
                     "email-change discriminator. Any mismatch => the A-reference is "
                     "unsound. There is no @ContractOnly axiom and no caller-reachable "
                     "input outside any axiom domain (no axiom domain exists).",
    },
]
