"""Twin-artifact model for django__django-11141.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the loader scans an installed application's migrations module after a
  successful import, it classifies that application into exactly one of two
  groups, encoded here as the result code:

      1  -> the application is treated as having migrations ("migrated")
      0  -> the application is treated as having no migrations ("unmigrated")

  The classification depends only on three observable facts about the imported
  module and one loader flag:

    * whether the module is a package, i.e. exposes a search path
      (``exposes_search_path``) — a plain module that is not a package, such as
      a single ``migrations.py`` file, exposes no search path and is always
      classified as unmigrated;

    * the collection of migration module names discovered on that search path
      (``migration_names``), already filtered down to the genuine migration
      modules — only how many were found bears on the classification;

    * whether the loader has been asked to tolerate the absence of any
      migrations (``treat_empty_as_migrated``).

  An application is classified as migrated exactly when its module exposes a
  search path AND it either has at least one discovered migration name OR the
  tolerate-empty flag is set; otherwise it is classified as unmigrated.

  Crucially, whether the package carries a conventional on-disk file marker
  (``has_regular_file_marker``) does NOT influence the classification at all: a
  package whose search path yields migration names is migrated regardless of
  that marker. Therefore a package directory that exposes its modules only
  through a search path and carries no file marker (an implicit namespace
  package) is classified identically to one that has a file marker.

The migrations module is a rich Python package object in the repository; here
the only fields that bear on the classification are modelled directly — two
booleans for "exposes a search path" / "carries a file marker", and the
discovered-name collection as a ``List[int]`` whose length is all that matters.
The discovered-name collection is read-only; the classification mutates nothing.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axioms: the classification is modelled deeply over concrete booleans and
# the length of the discovered-name collection; nothing opaque is consumed.)
# axioms-end


# pure-start
@Pure
def migrated_code(exposes_search_path: bool, discovered_file_count: int,
                  treat_empty_as_migrated: bool) -> int:
    """The classification outcome as a result code: 1 ("migrated") exactly when
    the module exposes a search path AND either at least one migration name was
    discovered there or the tolerate-empty flag is set; otherwise 0
    ("unmigrated"). The on-disk file marker does not appear, so the outcome is
    independent of it by construction."""
    if exposes_search_path and (discovered_file_count > 0 or
                                treat_empty_as_migrated):
        return 1
    return 0
# pure-end


def is_migrated_app(
    has_regular_file_marker: bool,
    exposes_search_path: bool,
    migration_names: List[int],
    treat_empty_as_migrated: bool,
) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(migration_names), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(migration_names), 1 / 2))
    # The discovered-name collection is read-only: unchanged in length/content.
    Ensures(ToSeq(migration_names) == Old(ToSeq(migration_names)))
    # The result is one of the two classification codes.
    Ensures(Result() == 0 or Result() == 1)
    # The result is exactly the classification outcome over the search-path
    # flag, the number of discovered migration names, and the tolerate flag.
    # The on-disk file marker (has_regular_file_marker) does not appear on the
    # right-hand side, so the result is pinned independently of it: no verifying
    # implementation can let the marker change the classification.
    Ensures(Result() == migrated_code(exposes_search_path,
                                      len(migration_names),
                                      treat_empty_as_migrated))
    # post-conditions-end
    # impl-start
    # Pre-image isolating the empty-package classification: every package that
    # exposes a search path is treated as migrated unconditionally, without
    # consulting how many migration names were discovered or the tolerate flag.
    if not exposes_search_path:
        return 0
    return 1
    # impl-end
