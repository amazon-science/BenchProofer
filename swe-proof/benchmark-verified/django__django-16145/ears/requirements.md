# Requirements: consistent bind-host display in the development server's start-up banner

## Introduction

Django's lightweight development server is launched by the management command
`runserver` (`django/core/management/commands/runserver.py`, the `Command`
class). When the server starts it prints a start-up banner of the form
`Starting development server at <protocol>://<host>:<port>/`, where `<host>` is
derived from the bind address the user supplied (or from the command's
defaults).

The command accepts the shorthand bind host `0` (as in `runserver 0:8000`),
which is documented to be equivalent to `0.0.0.0` — i.e. "bind on every
available interface". However, the banner echoes the resolved bind host
verbatim, so `runserver 0:8000` announces
`Starting development server at http://0:8000/`. That URL is not usable in a
browser, contradicting the documented equivalence with `0.0.0.0`.

The goal is to make the banner present the shorthand host `0` in its canonical
dotted form `0.0.0.0`, while leaving the presentation of every other kind of
host (IPv4 literals, host names, raw IPv6 literals, and the built-in defaults)
exactly as it is today. The behavior lives in the banner-rendering path of
`Command.inner_run`, which formats the host component that is substituted into
the `Starting development server at …` line.

## Requirement 1: Present the unspecified-address shorthand `0` as `0.0.0.0`

**User story:** As a developer running the development server with the
documented shorthand `runserver 0:<port>`, I want the start-up banner to show a
clickable address, so that I can open the printed link directly in my browser
and rely on the documented equivalence of `0` and `0.0.0.0`.

**Acceptance criteria**

1. WHEN the resolved bind host is the shorthand string `0` and that host is not
   a raw IPv6 literal, THEN `Command.inner_run` SHALL render the host component
   of the start-up banner as the string `0.0.0.0`.
2. WHEN the resolved bind host is the shorthand string `0`, THEN the start-up
   banner line SHALL read `Starting development server at
   http://0.0.0.0:<port>/`, using the same port the user supplied.
3. The system SHALL apply this substitution only to the displayed banner text;
   IF the bind host is the shorthand `0`, THEN the address actually used to bind
   and serve SHALL remain unchanged from prior behavior (the substitution is
   presentation-only).

## Requirement 2: Preserve display of all other hosts

**User story:** As a developer who binds to an explicit interface, a host name,
or an IPv6 literal, I want the banner to keep showing the address exactly as it
does today, so that existing behavior and tooling that reads the banner are not
disturbed.

**Acceptance criteria**

1. WHEN the resolved bind host is a raw IPv6 literal, THEN `Command.inner_run`
   SHALL render the host component of the banner wrapped in square brackets
   (`[<host>]`), regardless of the textual content of that host.
2. IF the resolved bind host is a raw IPv6 literal, THEN the bracket-wrapping
   rule SHALL take precedence over the shorthand-`0` rule (a raw IPv6 literal is
   always bracketed and is never rewritten to `0.0.0.0`).
3. WHEN the resolved bind host is neither a raw IPv6 literal nor the exact
   shorthand string `0`, THEN `Command.inner_run` SHALL render the host
   component of the banner as that host unchanged, character for character.
4. The system SHALL keep presenting an explicit IPv4 literal (for example a
   full dotted-quad supplied on the command line) verbatim in the banner.
5. The system SHALL keep presenting a host name / fully-qualified domain name
   supplied on the command line verbatim in the banner.
6. WHEN no bind address is supplied on the command line and IPv6 is not
   requested, THEN the banner SHALL show the command's default IPv4 bind host
   unchanged.
7. WHEN no bind address is supplied on the command line and IPv6 is requested,
   THEN the banner SHALL show the command's default IPv6 bind host wrapped in
   square brackets, as before.
8. WHEN a subclass overrides the default bind host and/or default port and no
   address is supplied, THEN the banner SHALL show those overridden defaults
   using the same presentation rules (IPv4 default verbatim; IPv6 default
   bracketed).

## Requirement 3: Preserve the surrounding start-up and address-parsing behavior

**User story:** As a maintainer, I want the rest of the `runserver` start-up
path — address parsing, error reporting, port handling, and the auxiliary
`testserver` command — to behave exactly as before, so that this change is
strictly limited to how the bind host is displayed.

**Acceptance criteria**

1. The system SHALL continue to substitute the correct port, protocol, Django
   version, and settings module into the start-up banner unchanged.
2. WHEN the supplied `addrport` argument is not a valid port number or
   `address:port` pair, THEN `Command` SHALL raise a command error as it does
   today, with no change to that behavior.
3. WHEN a bind address is ambiguous or otherwise invalid (for example an
   IPv6-only address supplied without IPv6 mode), THEN `Command` SHALL raise the
   same command error as before.
4. IF the `skip_checks` option is set, THEN the command SHALL still skip the
   system checks and print the banner, and the banner's host component SHALL
   follow the same display rules described above.
5. The system SHALL keep the `testserver` command's handling of its address and
   port parameters unchanged.
