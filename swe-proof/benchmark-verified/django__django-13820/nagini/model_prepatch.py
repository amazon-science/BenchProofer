"""Twin-artifact model for django__django-13820.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A loader inspects a candidate module that has just been imported and decides
  whether the module is a genuine source of submodules to enumerate, or whether
  it should be skipped. The decision is taken from three observable facts about
  the imported module:

    * whether the module is a PACKAGE (it exposes a child-search location) as
      opposed to a single non-package module;
    * whether the module records a concrete source-file LOCATION (some valid
      packages, e.g. those loaded in environments that synthesise no on-disk
      file, legitimately record none);
    * whether the module's child-search location is an ORDINARY LIST, as every
      regular package uses, rather than the custom iterable that marks a
      directory-spanning package with no concrete contents of its own.

  The desired classification:

    (1) a module that is NOT a package is always skipped;

    (2) a package is skipped ONLY when it BOTH records no source-file location
        AND its child-search location is not an ordinary list — i.e. only the
        contentless directory-spanning kind is skipped;

    (3) every other package is a source to enumerate. In particular a regular
        package that records no source-file location but whose child-search
        location IS an ordinary list must NOT be skipped: the absence of a
        recorded location alone is not enough to reject it.

  Equivalently: the module is a source to enumerate exactly when it is a package
  AND (it records a source-file location OR its child-search location is an
  ordinary list).

The three facts are modelled as ``bool`` (Nagini cannot introspect a real
module object; each runtime attribute query refines to its truth value — see
mapping.md / refinement.md). The decision is the corresponding ``bool``. No
callee is axiomatized: the classification is boolean predicate logic, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. The changed operation is a boolean classification
# over three observable module facts, modelled deeply as bool algebra. The
# attribute queries it refines (is-a-package, has-a-source-location,
# child-search-location-is-an-ordinary-list) are unchanged Python builtins
# refined to their truth values (kind R), not callees the proof consumes — see
# refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def is_source(is_package: bool, file_is_set: bool, path_is_ordinary_list: bool) -> bool:
    """The module is a source to enumerate exactly when it is a package AND it
    either records a source-file location OR uses an ordinary-list child-search
    location. The only package that is rejected is the contentless
    directory-spanning kind: no source-file location AND a non-list child-search
    location."""
    return is_package and (file_is_set or path_is_ordinary_list)
# pure-end


def treat_as_migration_source(
    is_package: bool, file_is_set: bool, path_is_ordinary_list: bool
) -> bool:
    # pre-conditions-start
    # A non-package exposes no child-search location, so its list-ness is
    # vacuous; pin it so the input space stays faithful to reality.
    Requires(Implies(not is_package, not path_is_ordinary_list))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The classification equals the deep boolean decision.
    Ensures(Result() == is_source(is_package, file_is_set, path_is_ordinary_list))
    # A non-package is always skipped.
    Ensures(Implies(not is_package, not Result()))
    # A package is skipped exactly when it records no source-file location AND
    # its child-search location is not an ordinary list.
    Ensures(Implies(is_package,
                    Result() == (file_is_set or path_is_ordinary_list)))
    # A package recording no source-file location but using an ordinary-list
    # child-search location is STILL a source (the discriminating case).
    Ensures(Implies(is_package and (not file_is_set) and path_is_ordinary_list,
                    Result()))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: a missing source-file location alone rejects the
    # module, before the package check and WITHOUT consulting whether the
    # child-search location is an ordinary list.
    if not file_is_set:
        return False
    if not is_package:
        return False
    return True
    # impl-end
