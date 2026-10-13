# properties.py — PBT falsification battery for sphinx-doc__sphinx-8035.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside a # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   keep_private_member(mode, names, membername, has_doc, undoc_members,
#                       filtered_inherited) -> bool                  [site A]
#     Requires Acc(list_pred(names), 1/2)            <-- READ-ONLY input (half perm)
#     Requires 0 <= mode <= 2
#     Ensures  Acc(list_pred(names), 1/2)            <-- frame: caller keeps its half
#     Ensures  Result() == keep_private(mode, ToSeq(names), membername,
#                                       has_doc, undoc_members,
#                                       filtered_inherited)          <-- LOAD-BEARING
#     Ensures  not documentable(...) -> Result() is False
#     Ensures  mode == 0 -> Result() is False
#     Ensures  mode == 1 -> Result() == documentable(...)
#     Ensures  mode == 2 and documentable and not filtered_inherited
#                 -> Result() == (membername in ToSeq(names))        <-- DISCRIMINATOR
#
#   keep_private is a @Pure fold GROUNDED ENTIRELY in the args (fully
#   unfoldable; NOT an opaque answer-key oracle). The load-bearing equality is
#   checked against the fold itself, so there is no "wrong ungrounded-oracle
#   echo" to build: any value an impl returns must equal keep_private of its
#   actual args. The ungrounded-oracle class is therefore N/A (see 'assessment').
#   The DISCRIMINATING content (the bug fix, the F2P): mode 2 keeps a
#   documentable, non-filtered private member iff its OWN name is in the explicit
#   list — NOT every private member. The pre-patch boolean collapse
#   `keep = private_members and (has_doc or undoc)` kept EVERY documentable
#   private member whenever the option was truthy (a non-empty list always is);
#   model_prepatch.py reproduces that collapse and the partial-domain rival below
#   IS that pre-patch behaviour. The mode-1/mode-2 asymmetry (the inherited
#   filter applies ONLY to the explicit-list state) is its own defended clause.
#
#   merge_selector_names(members_is_all, members, extra) -> List[int]  [site B]
#     Requires Acc(list_pred(members), 1/2)          <-- READ-ONLY input (half perm)
#     Requires Acc(list_pred(extra), 1/2)            <-- READ-ONLY input (half perm)
#     Ensures  Acc(list_pred(members),1/2), Acc(list_pred(extra),1/2)  <-- frame
#     Ensures  Acc(list_pred(Result()))
#     Ensures  members_is_all -> ToSeq(Result()) == ToSeq(members)    <-- no-op clause
#     Ensures  not members_is_all -> ToSeq(Result()).take(len(members))
#                                        == ToSeq(members)            <-- prefix clause
#     Ensures  not members_is_all -> every members[k] in Result()     <-- all-orig clause
#     Ensures  not members_is_all -> every extra[k] in Result()       <-- all-extra clause
#
#   merge_selector_names is forward-append (result + [members[i]]) against a
#   take(i)-prefix @Pure invariant, so a forward-append positive control keeps
#   the gold proof valid (no f(a+b) fold lemma is needed — the spec is itself
#   forward). Note: the postcondition does NOT pin "no duplicates"; an impl that
#   appended an already-present extra still satisfies every clause (prefix kept,
#   all present). That is a genuine spec-permissiveness, but it is NOT a
#   verify⇏resolve break — see 'assessment' — so no rival exploits it.
#
#   No @ContractOnly axioms (meta.axioms == []). Both deep models keep_private /
#   merge_selector_names are A-references already validated == the REAL
#   sphinx.ext.autodoc filter_members keep branch and the REAL
#   merge_members_option by axiom_check.py (G-AX): 512 option-state x member x
#   flag combos + the F2P discriminator witness + 5000 randomized merge inputs,
#   0 mismatch. The axiom lane is re-encoded below as a Docker probe over the
#   REAL callees (members_option / merge_members_option) so the suite carries an
#   independent in-container soundness + caller-domain-containment check.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8035"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchors INSIDE the impl regions (between # impl-start / # impl-end). Editing
# only these keeps spec_view (hence same_spec) byte-identical. There are TWO
# impl regions (keep_private_member, merge_selector_names).
# ===========================================================================

# --- gold impl body of keep_private_member (site A) -----------------------
_IMPL_A_GOLD = """    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    if filtered_inherited:
        return False
    return membername in ToSeq(names)"""

assert _IMPL_A_GOLD in _BASE, "impl anchor drift: keep_private_member body not verbatim"

# --- gold impl body of merge_selector_names (site B) ----------------------
_IMPL_B_GOLD = """    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            # invariants-start
            Invariant(Acc(list_pred(members), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(members))
            Invariant(ToSeq(result) == ToSeq(members).take(i))
            Invariant(MustTerminate(len(members) - i + 1))
            # invariants-end
            result = result + [members[i]]
            i = i + 1
        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
        return result
    result = []
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        Invariant(MustTerminate(len(extra) - j + 1))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result"""

assert _IMPL_B_GOLD in _BASE, "impl anchor drift: merge_selector_names body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — site A, structurally different but CORRECT (verify).
# Re-shape the flat early-return cascade into the NESTED if/elif tree of the
# gold SOURCE (documentable guard wrapping the mode dispatch, the explicit-list
# branch wrapping the filtered_inherited test), and stage the final decision
# through a named local instead of a bare return. Same observable boolean for
# every input; the postcondition equality with keep_private holds because the
# control flow computes exactly the same three-state rule. No loop / fold lemma.
# If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_A_POS = """    keep = False  # type: bool
    if has_doc or undoc_members:
        if mode == 0:
            keep = False
        elif mode == 1:
            keep = True
        else:
            if filtered_inherited:
                keep = False
            else:
                keep = membername in ToSeq(names)
    else:
        keep = False
    return keep"""

# ===========================================================================
# (2) ADMISSIBILITY — site A, the precondition admits a normal F2P-shaped input
# (verify). Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that the read-only `names` half-
# permission is usable (read membership via ToSeq) and that the mode bound the
# Requires gives (0 <= mode <= 2) reaches a normal return on every branch — i.e.
# an F2P-shaped input (mode 2, a one-name list, documentable, not filtered) is in
# domain and returns normally. If the Requires were vacuous / over-strong the
# impl could not both consume the half-permission and return => PRECOND-TOO-STRONG.
# ===========================================================================
_IMPL_A_ADMISS = """    # admissibility: mode is within the Requires bound and `names` (half-perm)
    # is readable; a normal non-raising return is reachable for the F2P input
    # shape (mode 2, documentable, not filtered, name maybe in the list).
    Assert(0 <= mode and mode <= 2)
    decided = membername in ToSeq(names)  # type: bool   # names half-perm readable
    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    if filtered_inherited:
        return False
    Assert(decided == (membername in ToSeq(names)))
    return decided"""

# ===========================================================================
# (3) FRAME-MUTATION — site A, write to the read-only input `names` (reject).
# keep_private_member holds only Acc(list_pred(names), 1/2). In the explicit-list
# branch (mode 2, not filtered) the membership read membername in ToSeq(names) is
# preceded by a value-NEUTRAL write back into names: when the list is non-empty,
# names[0] = names[0] is well-typed and in-bounds, yet a WRITE needs FULL
# permission. With only the half the Requires grants, Nagini rejects for
# INSUFFICIENT PERMISSION. The decision value is unchanged, so the rejection is
# attributable to the write, not to a spec change. MANDATORY: the input is
# read-only and a byte-fuzzer never thinks to mutate it.
# ===========================================================================
_IMPL_A_FRAME = """    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    if filtered_inherited:
        return False
    # FRAME MUTATION: write back into the read-only half-permission input.
    if len(names) > 0:
        names[0] = names[0]
    return membername in ToSeq(names)"""

# ===========================================================================
# (4) PARTIAL-DOMAIN / pre-patch boolean collapse — site A (reject). THIS IS
# THE PRE-PATCH BUG (model_prepatch.py): collapse the three-state option to a
# truthy flag, `return (mode != 0) and (has_doc or undoc_members)`. It AGREES
# with the gold rule on mode 0 (never kept) and mode 1 (kept iff documentable),
# but in mode 2 it keeps EVERY documentable member regardless of whether its name
# is in the list and regardless of filtered_inherited. The load-bearing
# postcondition Result() == keep_private(...) and the discriminating clause
# (mode 2: Result() == (membername in ToSeq(names))) therefore fail exactly on
# the sub-domain mode==2 with a name NOT in the list (or a filtered inherited).
# ===========================================================================
_IMPL_A_COLLAPSE = """    return (mode != 0) and (has_doc or undoc_members)"""

# ===========================================================================
# (5) ASYMMETRY-FLIP / mode-2 ignores the inherited filter — site A (reject).
# A subtler partial-domain miss than the collapse: keep the documentable guard,
# the mode-0 drop and the mode-1 all-form, but in the explicit-list branch DROP
# the filtered_inherited test, returning `membername in ToSeq(names)` directly.
# This keeps a filtered inherited member that happens to be named in the list —
# the gold rule drops it (the inherited filter applies in the explicit-list
# state). Violates keep_private on the sub-domain mode==2, documentable,
# filtered_inherited==True, name in list. (The discriminating clause itself is
# satisfied — it is guarded by `not filtered_inherited` — so this isolates the
# mode-1/mode-2 inherited-filter asymmetry clause via the master equality
# Result() == keep_private(...).)
# ===========================================================================
_IMPL_A_NOINHERIT = """    if not (has_doc or undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    return membername in ToSeq(names)"""

# ===========================================================================
# (6) POSITIVE CONTROL — site B, structurally different but CORRECT (verify).
# Keep the forward-append shape (the spec invariant is take(i)-prefix, so a
# forward copy is what the gold proof needs — NO fold lemma) but RESTRUCTURE:
# fold the members_is_all no-op into the SAME copy loop (copy members either way),
# then guard the extra-merge loop behind `if not members_is_all`. Every gold
# invariant/assert that is still needed is kept VERBATIM. Same observable result
# (members_is_all -> copy of members; else copy ++ new extras). Must verify, else
# SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_B_POS = """    result = []  # type: List[int]
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    if members_is_all:
        return result
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        Invariant(MustTerminate(len(extra) - j + 1))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result"""

# ===========================================================================
# (7) FRAME-MUTATION — site B, write to the read-only input `members` (reject).
# merge_selector_names holds only Acc(list_pred(members), 1/2). Inside the copy
# loop the index members[i] is in-bounds (0 <= i < len(members)), so a value-
# NEUTRAL write members[i] = members[i] is well-typed, yet a WRITE needs FULL
# permission. With only the half the Requires grants, Nagini rejects for
# INSUFFICIENT PERMISSION. Gold invariants/asserts kept verbatim so the rejection
# is attributable to the write. MANDATORY: `members` (and `extra`) are read-only.
# ===========================================================================
_IMPL_B_FRAME = """    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            # invariants-start
            Invariant(Acc(list_pred(members), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(members))
            Invariant(ToSeq(result) == ToSeq(members).take(i))
            Invariant(MustTerminate(len(members) - i + 1))
            # invariants-end
            result = result + [members[i]]
            i = i + 1
        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
        return result
    result = []
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        # FRAME MUTATION: write back into the read-only half-permission input.
        members[i] = members[i]
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        Invariant(MustTerminate(len(extra) - j + 1))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result"""

# ===========================================================================
# (8) PARTIAL-DOMAIN / drop-extra-names — site B (reject). Keep the no-op
# all-form branch and the members copy, but in the merge loop NEVER append (treat
# every extra as already present), so result == copy of members. The all-extra
# postcondition (every extra[k] in Result()) then fails on any extra name not
# already in members. This is a real merge regression: the supplementary
# selector's names would be dropped.
# ===========================================================================
_IMPL_B_DROPEXTRA = """    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            # invariants-start
            Invariant(Acc(list_pred(members), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(members))
            Invariant(ToSeq(result) == ToSeq(members).take(i))
            Invariant(MustTerminate(len(members) - i + 1))
            # invariants-end
            result = result + [members[i]]
            i = i + 1
        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
        return result
    result = []
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    return result"""

# ===========================================================================
# (9) NO-OP-DROP / merge runs on the all-form too — site B (reject). Remove the
# members_is_all early no-op: always run BOTH the members copy AND the extra
# merge. On the members_is_all sub-domain with an extra name not already in
# members, the result grows beyond `members`, so the no-op clause
# (members_is_all -> ToSeq(Result()) == ToSeq(members)) fails. This is the
# `if options.get('members') is ALL: return` guard that the gold helper has and
# this rival drops.
# ===========================================================================
_IMPL_B_NONOOP = """    result = []  # type: List[int]
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        Invariant(MustTerminate(len(extra) - j + 1))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-A-nested-tree",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_POS),
        "rationale": "Structurally different but correct: the flat early-return "
                     "cascade is re-shaped into the NESTED if/elif tree of the gold "
                     "SOURCE (documentable guard wrapping the mode dispatch; the "
                     "explicit-list branch wrapping the filtered_inherited test) and "
                     "the decision is staged through a named local `keep`. Computes "
                     "exactly the same three-state rule, so Result() == "
                     "keep_private(...) holds. No loop / fold lemma introduced. Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-A-readonly-names",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_ADMISS),
        "rationale": "Re-derives in-region that the half-permission input `names` is "
                     "usable (membership read via ToSeq) and that the Requires bound "
                     "0 <= mode <= 2 reaches a normal non-raising return on the F2P "
                     "input shape (mode 2, documentable, not filtered). If the "
                     "Requires were vacuous or over-strong the impl could not both "
                     "consume the half-permission and return => PRECOND-TOO-STRONG. "
                     "Source: the Acc(list_pred(names),1/2) + 0<=mode<=2 Requires.",
    },
    {
        "id": "frame-mutation-A-write-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_FRAME),
        "refinement": "A faithful real patch in which the keep decision wrote back "
                      "into self.options.private_members (the explicit name list) — "
                      "e.g. private_members[0] = private_members[0] / .sort() — would "
                      "mutate the option list that the SAME converter result is shared "
                      "across every member iteration of filter_members and across the "
                      "module/class documenters. filter_members only READS "
                      "private_members (membername in self.options.private_members); "
                      "mutating it would corrupt the per-member keep decisions and the "
                      "shared options dict, so the faithful patch would not resolve "
                      "test_private_members (the list must be read intact for every "
                      "member).",
        "rationale": "keep_private_member holds only Acc(list_pred(names), 1/2). The "
                     "value-neutral write names[0] = names[0] (in-bounds via len>0) "
                     "needs FULL permission => Nagini rejects for INSUFFICIENT "
                     "PERMISSION. Source: the permission system + the Acc(...,1/2) "
                     "Requires. Decision value unchanged so the rejection is "
                     "attributable to the write, not a spec change.",
    },
    {
        "id": "partial-domain-A-boolean-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_COLLAPSE),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): the "
                      "pre-patch line keep = self.options.private_members and (has_doc "
                      "or self.options.undoc_members), which under the new "
                      "members_option converter collapses None/ALL/List to a truthy "
                      "flag — a non-empty list is always truthy, so it keeps EVERY "
                      "documentable private member. For the F2P scenario "
                      "(private-members='_public_function') it KEEPS private_function "
                      "(a documentable private member NOT in the list), which "
                      "test_private_members asserts must be DROPPED. The faithful "
                      "pre-patch behaviour does NOT resolve — this is the exact "
                      "F2P-discriminating regression.",
        "rationale": "On mode==2 with a name not in the list the collapse returns "
                     "True but keep_private returns (membername in ToSeq(names)) == "
                     "False, so the load-bearing Result() == keep_private(...) and the "
                     "discriminating clause Result() == (membername in ToSeq(names)) "
                     "both fail. Source: the keep_private equality + the mode-2 "
                     "discriminator postcondition clause.",
    },
    {
        "id": "asymmetry-A-mode2-ignores-inherited-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_A_GOLD, _IMPL_A_NOINHERIT),
        "refinement": "A faithful real patch that dropped the "
                      "`elif is_filtered_inherited_member(membername): keep = False` "
                      "branch (returning `membername in self.options.private_members` "
                      "directly) would KEEP a filtered inherited private member that "
                      "happens to be named in the explicit list. The gold patch added "
                      "that branch precisely so the inherited filter applies in the "
                      "explicit-list state; dropping it reintroduces the documented "
                      "wrong behaviour on inherited members and would fail the "
                      "inherited-member filtering the patch establishes (it diverges "
                      "from the real filter_members decision validated by G-AX).",
        "rationale": "On mode==2, documentable, filtered_inherited==True, name in "
                     "list: this impl returns True but keep_private returns (not "
                     "filtered_inherited) and ... == False, so the master equality "
                     "Result() == keep_private(...) fails. Source: the mode-1/mode-2 "
                     "inherited-filter asymmetry encoded in keep_private (the filter "
                     "applies ONLY to the explicit-list state).",
    },
    {
        "id": "pos-control-B-merged-noop-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_POS),
        "rationale": "Structurally different but correct: the members_is_all no-op is "
                     "folded into the SAME forward copy loop (members are copied "
                     "either way), then the extra-merge loop is guarded behind `if "
                     "not members_is_all`. Forward-append against the take(i)-prefix "
                     "invariant (no fold lemma needed). Every still-needed gold "
                     "invariant/assert is kept verbatim. Same observable result. Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-B-write-members",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_FRAME),
        "refinement": "A faithful real patch in which merge_members_option wrote back "
                      "into the source `members` list it is copying (rather than only "
                      "reading it) would mutate options['members'] mid-merge; the real "
                      "helper only READS members[i] while growing the result and the "
                      "options dict is shared across the documenter, so a mutating "
                      "merge would corrupt the very members option the directive later "
                      "consumes — it would not faithfully reproduce merge_members_option "
                      "(validated by G-AX over 5000 inputs) and would not resolve.",
        "rationale": "merge_selector_names holds only Acc(list_pred(members), 1/2). "
                     "The value-neutral write members[i] = members[i] (in-bounds via "
                     "the loop bound) needs FULL permission => Nagini rejects for "
                     "INSUFFICIENT PERMISSION. Gold invariants/asserts kept verbatim "
                     "so the rejection is attributable to the write. Source: the "
                     "permission system + the Acc(...,1/2) Requires.",
    },
    {
        "id": "partial-domain-B-drop-extra-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_DROPEXTRA),
        "refinement": "A faithful real patch where the merge loop never appended (the "
                      "`if member not in members: members.append(member)` body "
                      "removed) would DROP every supplementary-selector name — exactly "
                      "the behaviour merge_members_option was added to fix (it must "
                      "merge private-members/special-members explicit lists into "
                      "members). The real merge_members_option grows members with the "
                      "new names; a non-appending merge diverges from it (G-AX checks "
                      "equality over 5000 inputs) and would not resolve a test that "
                      "documents a *-members name that is absent from members.",
        "rationale": "result == copy of members, so on any extra name not already in "
                     "members the all-extra clause (not members_is_all -> every "
                     "extra[k] in Result()) fails. Source: the all-extra-present "
                     "postcondition clause.",
    },
    {
        "id": "partial-domain-B-noop-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_B_GOLD, _IMPL_B_NONOOP),
        "refinement": "A faithful real patch that dropped the `if options.get('members') "
                      "is ALL: return` guard would run the merge even when members is "
                      "ALL, appending the *-members names onto the ALL sentinel path. "
                      "The real merge_members_option returns early for members: ALL "
                      "(no-op) — the documented contract — so a merge that grows the "
                      "list on the all-form diverges from the real callee (G-AX) and "
                      "would mis-handle the common members: ALL case (the F2P shape) by "
                      "altering the members option it must leave untouched.",
        "rationale": "On members_is_all with an extra name not in members the result "
                     "grows beyond members, so the no-op clause (members_is_all -> "
                     "ToSeq(Result()) == ToSeq(members)) fails. Source: the no-op "
                     "postcondition clause.",
    },
]


# ===========================================================================
# AXIOM lane — no @ContractOnly axioms (meta.axioms == []), but TWO A-reference
# deep models (keep_private, merge_selector_names) validated == the REAL
# sphinx.ext.autodoc callees by axiom_check.py (G-AX). We re-encode that
# real-callee soundness + caller-domain-containment check as in-container Docker
# probes over the REAL members_option / merge_members_option, executed against
# the post-gold image (apply_gold=True). The probe CALLS the real callees (never
# scrapes source), opens nothing on disk, imports only stdlib + the patched
# sphinx.ext.autodoc, and exits 0 iff every obligation holds.
# ===========================================================================

_PROBE_KEEP = r'''
import sys

# model.py deep-model reference (kept in lock-step with the pure region)
def model_documentable(has_doc, undoc):
    return has_doc or undoc

def model_keep_private(mode, names, membername, has_doc, undoc, finh):
    if not model_documentable(has_doc, undoc):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    return (not finh) and (membername in names)

# Gold-source oracle: the post-patch filter_members private branch VERBATIM.
def gold_keep(private_members, ALL, membername, has_doc, undoc, finh):
    if has_doc or undoc:
        if private_members is None:
            return False
        elif private_members is ALL:
            return True
        elif finh:
            return False
        else:
            return membername in private_members
    else:
        return False

try:
    from sphinx.ext.autodoc import members_option, ALL
except Exception as exc:
    print("AXIOM-PROBE FAIL: cannot import real sphinx.ext.autodoc (%r)" % (exc,))
    sys.exit(1)

failures = 0
checked = 0
name_pool = ["_a", "_b", "_secret", "_public_function", "private_function",
             "x", "__init__", "foo"]

# Caller-domain containment + soundness. The MODEL can reach exactly three
# option states (mode 0/1/2). For each, build the REAL converter output that the
# directive would pass, and assert the deep model == the gold-source decision
# over every member x has_doc x undoc x filtered_inherited combination.

# mode 0: option absent -> private_members is None
states = [(0, [], None)]
# mode 1: bare option (no arg) -> members_option(None) IS the ALL sentinel
allval = members_option(None)
if allval is not ALL:
    print("AXIOM-PROBE FAIL: members_option(None) is not ALL (got %r)" % (allval,))
    sys.exit(1)
states.append((1, [], allval))
# mode 2: explicit comma lists via the REAL converter
for spec in ["_public_function", "_a,_b", "_secret", "_public_function,_a",
             "x,foo,__init__", "private_function"]:
    lst = members_option(spec)
    # CONTAINMENT: the real converter yields a plain list of name tokens — the
    # exact domain the model's mode-2 reaches (names: List[int] of tokens).
    if not isinstance(lst, list):
        print("AXIOM-PROBE FAIL: members_option(%r) not a list (%r)" % (spec, lst))
        sys.exit(1)
    states.append((2, list(lst), lst))

for (mode, model_names, real_pm) in states:
    for membername in name_pool:
        for has_doc in (True, False):
            for undoc in (True, False):
                for finh in (True, False):
                    m = model_keep_private(mode, model_names, membername,
                                            has_doc, undoc, finh)
                    g = gold_keep(real_pm, ALL, membername, has_doc, undoc, finh)
                    checked += 1
                    if m != g:
                        failures += 1
                        print("MISMATCH keep: mode=%r name=%r has_doc=%r undoc=%r "
                              "finh=%r model=%r gold=%r"
                              % (mode, membername, has_doc, undoc, finh, m, g))

# F2P discriminator witness through the REAL converter.
pm = members_option("_public_function")
drop = model_keep_private(2, list(pm), "private_function", True, False, False)
if drop is not False:
    print("AXIOM-PROBE FAIL: F2P discriminator broken (drop=%r)" % (drop,))
    failures += 1
keepit = model_keep_private(2, list(pm), "_public_function", True, False, False)
if keepit is not True:
    print("AXIOM-PROBE FAIL: named member not kept (keep=%r)" % (keepit,))
    failures += 1

print("AXIOM-PROBE keep_private: %d combos checked, %d failures" % (checked, failures))
sys.exit(0 if failures == 0 else 1)
'''

_PROBE_MERGE = r'''
import random
import sys

def model_merge(members_is_all, members, extra):
    if members_is_all:
        return list(members)
    result = list(members)
    for m in extra:
        if m not in result:
            result.append(m)
    return result

try:
    from sphinx.ext.autodoc import merge_members_option, ALL
except Exception as exc:
    print("AXIOM-PROBE FAIL: cannot import real sphinx.ext.autodoc (%r)" % (exc,))
    sys.exit(1)

failures = 0
name_pool = ["_a", "_b", "_secret", "_public_function", "private_function",
             "x", "__init__", "foo"]
rng = random.Random(8035)

for _ in range(5000):
    members_is_all = (rng.randint(0, 2) == 0)
    members = [rng.choice(name_pool) for _ in range(rng.randint(0, 4))]
    extra = [rng.choice(name_pool) for _ in range(rng.randint(0, 4))]

    model_out = model_merge(members_is_all, members, extra)

    # Build the options dict exactly as the directive does; merge in place.
    opts = {}
    if members_is_all:
        opts["members"] = ALL
    else:
        opts["members"] = list(members)
    # one supplementary selector as an explicit (non-ALL) list
    opts["private-members"] = list(extra)
    merge_members_option(opts)

    if members_is_all:
        # CONTAINMENT/soundness: the no-op leaves members as the ALL sentinel;
        # the model returns a copy of `members` (the pre-merge content) — both
        # encode "no change to the member list" for the all-form.
        if opts["members"] is not ALL:
            failures += 1
            print("MISMATCH merge(all): expected ALL untouched, got %r"
                  % (opts["members"],))
        real_out = list(members)
    else:
        real_out = list(opts["members"])

    if model_out != real_out:
        failures += 1
        print("MISMATCH merge: all=%r members=%r extra=%r model=%r real=%r"
              % (members_is_all, members, extra, model_out, real_out))

print("AXIOM-PROBE merge_members_option: 5000 randomized inputs, %d failures"
      % (failures,))
sys.exit(0 if failures == 0 else 1)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-keep_private",
        "axiom": "keep_private",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_KEEP,
        "rationale": "A-reference: the keep_private deep model must equal the REAL "
                     "post-patch filter_members private-member branch over every "
                     "option state x member x flag combination, with the three option "
                     "states produced through the REAL members_option converter "
                     "(mode 0 None, mode 1 = members_option(None) IS ALL, mode 2 = the "
                     "converter's list). Containment: mode-2 is exactly the plain "
                     "name-token list the model reaches. Any mismatch => AXIOM-UNSOUND. "
                     "Also witnesses the F2P discriminator through the real converter "
                     "(drop private_function, keep _public_function).",
    },
    {
        "id": "ax-sound-merge_members_option",
        "axiom": "merge_selector_names",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_MERGE,
        "rationale": "A-reference: the merge_selector_names deep model must equal the "
                     "REAL sphinx.ext.autodoc.merge_members_option over 5000 randomized "
                     "inputs (both branches), with option dicts built exactly as the "
                     "directive does (members ALL or an explicit list; one "
                     "private-members supplementary list). Containment: the model's "
                     "(members_is_all, members, extra) cover the no-op and the "
                     "append-if-absent path the real callee exercises. Any mismatch => "
                     "AXIOM-UNSOUND.",
    },
]
