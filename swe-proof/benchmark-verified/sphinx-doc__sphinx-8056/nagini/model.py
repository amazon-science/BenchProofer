"""Twin-artifact model for sphinx-doc__sphinx-8056.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documented entry consumed from a parameter section carries a *name field*
  (a run of text), a *type* and a *description*. The name field may name more
  than one entry at once, the individual names being separated by literal
  commas (for example ``"x1, x2"`` names two entries). When this "one entry per
  comma-separated name" expansion is requested AND the name field is non-empty,
  the consumer emits ONE entry per comma-separated name, each name trimmed of
  surrounding whitespace and each carrying the SHARED type and description of
  the original field. So a name field holding ``c`` commas yields ``c + 1``
  emitted entries, in left-to-right order, the k-th being the trimmed k-th
  comma-separated run.

  When the expansion is NOT requested, the field is emitted as a single entry
  whenever any of its name / type / description is non-empty (the name kept
  verbatim, commas and surrounding whitespace included); an entirely empty
  field is dropped.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of Unicode code points
(Nagini bans ``str`` indexing); the emitted sequence of names is carried as a
pure ``PSeq[PSeq[int]]``. The comma split and the whitespace trim are unchanged
stdlib string operations the consumer CALLS; they are axiomatized
(``split_on_comma`` / ``trim``) and their soundness is checked against the real
callees out-of-band by axiom_check.py (G-AX). The emitted sequence of names is
the modelled, F2P-discriminating output (type and description are shared
verbatim across every emitted entry, so the name sequence carries the whole
change).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def num_commas(s: PSeq[int]) -> int:
    """Number of comma (code point 44) separators in ``s``. The count of
    comma-separated runs is ``num_commas(s) + 1`` (an empty run still counts),
    matching ``len(text.split(',')) == text.count(',') + 1``."""
    Ensures(Result() >= 0)
    Ensures(Implies(len(s) == 0, Result() == 0))


@Pure
@ContractOnly
def split_on_comma(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """Splitting ``s`` on every literal comma (unchanged ``str.split(',')``).
    Always yields ``num_commas(s) + 1`` runs, the k-th being the text between
    the k-th and (k+1)-th separator. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Ensures(len(Result()) == num_commas(s) + 1)


@Pure
@ContractOnly
def trim(s: PSeq[int]) -> PSeq[int]:
    """Whitespace-trimmed ``s`` (unchanged ``str.strip()``): the leading and
    trailing runs of whitespace are removed and interior content is preserved.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
# axioms-end


# pure-start
# (no extra pure helpers: the changed operation is the control-flow choice to
#  expand the name field; split/trim are the axiomatized unchanged callees.)
# pure-end


def emitted_names(name: List[int], multiple: bool,
                  type_nonempty: bool, desc_nonempty: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    # When the per-comma expansion is requested and the name is non-empty, one
    # entry is emitted per comma-separated run (so num_commas + 1 in total),
    # the k-th being the whitespace-trimmed k-th run, in order. This is the
    # behaviour the multi-name field demands.
    Ensures(Implies(multiple and len(name) > 0,
                    len(Result()) == num_commas(ToSeq(name)) + 1))
    Ensures(Forall(int, lambda k: (
        Implies(multiple and len(name) > 0 and 0 <= k and k < len(Result()),
                Result()[k] == trim(split_on_comma(ToSeq(name))[k])),
        [[Result()[k]]])))
    # Otherwise the field is emitted as at most one entry: a single verbatim
    # name when any of name/type/description is non-empty, else nothing. The
    # name is NOT split (commas and surrounding whitespace are kept).
    Ensures(Implies(not (multiple and len(name) > 0),
                    len(Result()) <= 1))
    Ensures(Implies(not (multiple and len(name) > 0) and
                    (len(name) > 0 or type_nonempty or desc_nonempty),
                    len(Result()) == 1))
    Ensures(Implies(not (multiple and len(name) > 0) and
                    not len(name) > 0 and not type_nonempty and not desc_nonempty,
                    len(Result()) == 0))
    Ensures(Implies(not (multiple and len(name) > 0) and len(Result()) == 1,
                    Result()[0] == ToSeq(name)))
    # post-conditions-end
    # impl-start
    result = PSeq(ToSeq(name)).take(0)  # type: PSeq[PSeq[int]]
    if multiple and len(name) > 0:
        parts = split_on_comma(ToSeq(name))  # type: PSeq[PSeq[int]]
        n = num_commas(ToSeq(name)) + 1
        Assert(len(parts) == n)
        i = 0
        while i < n:
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 2))
            Invariant(multiple and len(name) > 0)
            Invariant(0 <= i and i <= n)
            Invariant(n == num_commas(ToSeq(name)) + 1)
            Invariant(parts == split_on_comma(ToSeq(name)))
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == trim(parts[k])),
                [[result[k]]])))
            Invariant(MustTerminate(n - i + 1))
            # invariants-end
            piece = trim(parts[i])  # type: PSeq[int]
            old_result = result  # type: PSeq[PSeq[int]]
            result = result + PSeq(piece)
            Assert(len(result) == i + 1)
            Assert(result[i] == piece)
            Assert(Forall(int, lambda k: (
                Implies(0 <= k and k < i, result[k] == old_result[k]),
                [[result[k]]])))
            i = i + 1
        return result
    else:
        if len(name) > 0 or type_nonempty or desc_nonempty:
            result = result + PSeq(ToSeq(name))
            Assert(len(result) == 1)
            Assert(result[0] == ToSeq(name))
        return result
    # impl-end
