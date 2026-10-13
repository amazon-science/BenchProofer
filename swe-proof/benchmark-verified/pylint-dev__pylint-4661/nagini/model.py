"""Twin-artifact model for pylint-dev__pylint-4661.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A program selects the directory in which it keeps its persistent per-user
  data. The location is resolved from the user's environment by three mutually
  exclusive cases, tried in order:

    (1) an explicit per-user override is present in the environment  -> that
        override value is used verbatim as the directory;
    (2) otherwise, if the user's home directory is unknown (it resolves to the
        literal placeholder "~")  -> a bare relative directory ".pylint.d" in
        the current working directory is used;
    (3) otherwise (a real home directory is known and no override is set)  ->
        the directory is the per-user CACHE base of the host, with the program
        name appended as a single path segment. On an XDG-style host the cache
        base is the resolved user cache root (e.g. the value of XDG_CACHE_HOME,
        or the conventional ~/.cache when that variable is unset); the appended
        segment is the program name "pylint". The directory is therefore the
        cache root joined, as one further path component, with "pylint".

The directory the program-data path is rooted at, in case (3), is the per-user
cache base (NOT the home directory) and the appended leaf segment is the plain
program name "pylint" (NOT a dotted ".pylint.d" segment).

Paths and path segments are modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); the specification is carried over `PSeq[int]`.
The single unchanged callee the code uses to compose a directory from a base
and a leaf segment (`os.path.join` on a base with no trailing separator and a
relative, non-empty leaf) is axiomatized as `path_join` (A-consumed). Case (3)'s
target directory is modelled deeply as `home_dir_for_cache_root` (the cache
root joined with the literal program-name segment); that deep model is checked
== the real per-user-cache resolver out-of-band by axiom_check.py (G-AX), as an
A-reference, not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def path_join(base: PSeq[int], leaf: PSeq[int]) -> PSeq[int]:
    """Compose a directory path from a base directory and a single relative
    leaf segment (the unchanged stdlib path-join callee, on the only inputs
    this bundle uses it with: a non-empty base that does not end in the path
    separator '/', and a non-empty leaf that is itself relative — contains no
    leading separator). On such inputs the result is exactly the base, the
    separator '/', then the leaf. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(len(base) > 0)
    Requires(base[len(base) - 1] != 47)        # base does not end with '/'
    Requires(len(leaf) > 0)
    Requires(leaf[0] != 47)                     # leaf is relative
    Ensures(Result() == base + PSeq(47) + leaf)
# axioms-end


# pure-start
@Pure
def seq_pylint() -> PSeq[int]:
    # the program-name leaf segment "pylint"
    return PSeq(112, 121, 108, 105, 110, 116)


@Pure
def seq_dot_pylint_d() -> PSeq[int]:
    # the bare relative directory ".pylint.d"
    return PSeq(46, 112, 121, 108, 105, 110, 116, 46, 100)


@Pure
def home_dir_for_cache_root(cache_root: PSeq[int]) -> PSeq[int]:
    """Case (3)'s data directory, modelled deeply: the per-user cache root with
    the program-name segment "pylint" appended as one path component. Requires
    the cache root to be a usable base (non-empty, no trailing separator)."""
    Requires(len(cache_root) > 0)
    Requires(cache_root[len(cache_root) - 1] != 47)
    return path_join(cache_root, seq_pylint())
# pure-end


def compute_pylint_home(env_has_override: bool, override_value: List[int],
                        home_is_placeholder: bool, user_home: List[int],
                        cache_root: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(override_value), 1 / 2))
    Requires(Acc(list_pred(user_home), 1 / 2))
    Requires(Acc(list_pred(cache_root), 1 / 2))
    # The cache root is a usable base directory (non-empty, no trailing '/').
    Requires(len(ToSeq(cache_root)) > 0)
    Requires(ToSeq(cache_root)[len(ToSeq(cache_root)) - 1] != 47)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(override_value), 1 / 2))
    Ensures(Acc(list_pred(user_home), 1 / 2))
    Ensures(Acc(list_pred(cache_root), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The cache root is preserved as a usable base (re-framed for the case-3
    # clause, which mentions the cache root via home_dir_for_cache_root).
    Ensures(len(ToSeq(cache_root)) > 0)
    Ensures(ToSeq(cache_root)[len(ToSeq(cache_root)) - 1] != 47)
    # Case (1): explicit override is used verbatim.
    Ensures(Implies(env_has_override,
                    ToSeq(Result()) == ToSeq(override_value)))
    # Case (2): unknown home -> the bare relative ".pylint.d".
    Ensures(Implies(not env_has_override and home_is_placeholder,
                    ToSeq(Result()) == seq_dot_pylint_d()))
    # Case (3): real home, no override -> the per-user cache root joined with
    # the program-name segment "pylint" (rooted at the cache base, leaf
    # "pylint"); NOT the home directory and NOT a dotted ".pylint.d" leaf.
    Ensures(Implies(not env_has_override and not home_is_placeholder,
                    ToSeq(Result()) == home_dir_for_cache_root(ToSeq(cache_root))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
