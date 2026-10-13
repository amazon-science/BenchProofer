import Mathlib
-- imports-end

/-!
Deciding whether an available version string meets a required-minimum version.

A version is compared against a required minimum using a standard
version-string ordering. The required-minimum string, however, may carry a
trailing non-numeric qualifier (for example a pre-release or development
suffix). Such a qualifier makes the ordering ill-defined, so before the
comparison the required-minimum string is reduced to a leading numeric prefix.
`releasePrefix` below is the definition of record for which prefixes are
accepted and how far each one extends; the reduction keeps the prefix it
accepts, and leaves the string unchanged at a string where it accepts none.

The decision is then: the available version is at least the (reduced) required
version — inclusively (`≥`) when `inclusive` holds, strictly (`>`) otherwise.

The version-string ordering is PARTIAL. It has no value on a pair of strings
that are not commensurable: the release numbers run out and a residual
non-numeric qualifier would have to be ordered against a number, which the
ordering does not do. The decision inherits exactly that partiality — it
carries a verdict precisely when the ordering of the available version against
the *reduced* required version carries one, and has no value precisely when that
one comparison has none. So a required minimum whose trailing qualifier leaves
it incommensurable with the available version still yields a verdict, because
the reduction is what the ordering is applied to.

That partiality is carried below as what a partial operation IS — an operation
on its domain — rather than as a total operation that reports `none` somewhere:
the ordering's answer at a pair comes only together with the fact that the pair
is one it answers at. Whether a pair is such a pair is a separate and TOTAL
question: it always has an answer, and "no" is one of its answers rather than a
failure. Two consequences belong to the behavior itself and not to any one way
of realizing it. There is no such thing as the ordering's answer at a pair it
does not answer at, so no part of this behavior can depend on one or be spent
obtaining one. And a behavior that would put the ordering to a pair whose
commensurability it has not established must establish that first — a step that
always completes, whichever way it comes out.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- Where the standard version-string ordering HAS a value: `orderable a b` is
`true` exactly on the pairs of version strings that ordering compares, and
`false` on a pair it does not compare — the release numbers run out and a
residual non-numeric qualifier would have to be ordered against a number, which
the ordering does not do. Whether a pair is one of those is itself a total
question: it always has an answer, and the answer `false` is an answer rather
than a failure.

`versionGe a b h` is the ordering itself: version `a` is at least version `b`.
The ordering is PARTIAL, and is carried here as what a partial operation is — an
operation on its domain. It is applicable only together with `h`, the fact that
the pair is one the ordering has a value at, so no term names the ordering's
answer at a pair where it has none, and nothing below can be made to depend on
one. `versionGt` is the strict variant; both have a value at exactly the same
pairs.

These are unchanged dependency operations — declared opaque so they appear in
the executable implementation. The proof consumes no property of them (they
occur identically in the specification and the implementation), so no contract
axiom is asserted. -/
opaque orderable : List Char → List Char → Bool
opaque versionGe : (a b : List Char) → orderable a b = true → Bool
opaque versionGt : (a b : List Char) → orderable a b = true → Bool
-- axioms-end

-- pure-start
/-- The code-point ranges, as inclusive `(lo, hi)` pairs, whose members count as
digits for the scan below. -/
def decimalDigitRanges : List (Nat × Nat) :=
  [(0x0030, 0x0039), (0x0660, 0x0669), (0x06F0, 0x06F9),
   (0x07C0, 0x07C9), (0x0966, 0x096F), (0x09E6, 0x09EF),
   (0x0A66, 0x0A6F), (0x0AE6, 0x0AEF), (0x0B66, 0x0B6F),
   (0x0BE6, 0x0BEF), (0x0C66, 0x0C6F), (0x0CE6, 0x0CEF),
   (0x0D66, 0x0D6F), (0x0DE6, 0x0DEF), (0x0E50, 0x0E59),
   (0x0ED0, 0x0ED9), (0x0F20, 0x0F29), (0x1040, 0x1049),
   (0x1090, 0x1099), (0x17E0, 0x17E9), (0x1810, 0x1819),
   (0x1946, 0x194F), (0x19D0, 0x19D9), (0x1A80, 0x1A89),
   (0x1A90, 0x1A99), (0x1B50, 0x1B59), (0x1BB0, 0x1BB9),
   (0x1C40, 0x1C49), (0x1C50, 0x1C59), (0xA620, 0xA629),
   (0xA8D0, 0xA8D9), (0xA900, 0xA909), (0xA9D0, 0xA9D9),
   (0xA9F0, 0xA9F9), (0xAA50, 0xAA59), (0xABF0, 0xABF9),
   (0xFF10, 0xFF19), (0x104A0, 0x104A9), (0x11066, 0x1106F),
   (0x110F0, 0x110F9), (0x11136, 0x1113F), (0x111D0, 0x111D9),
   (0x112F0, 0x112F9), (0x11450, 0x11459), (0x114D0, 0x114D9),
   (0x11650, 0x11659), (0x116C0, 0x116C9), (0x11730, 0x11739),
   (0x118E0, 0x118E9), (0x11C50, 0x11C59), (0x16A60, 0x16A69),
   (0x16B50, 0x16B59), (0x1D7CE, 0x1D7FF), (0x1E950, 0x1E959)]

/-- `true` for a character listed in `decimalDigitRanges`. Membership is by
code point and is decided by that table alone, so a character carrying a
numeric value but absent from the table is not one of these. -/
def isDecimalDigit (c : Char) : Bool :=
  decimalDigitRanges.any fun r =>
    Nat.ble r.1 c.toNat && Nat.ble c.toNat r.2

/-- `true` for the characters `'1'`–`'9'`. -/
def isNonZeroDigit (c : Char) : Bool := c.isDigit && c ≠ '0'

/-- Split off the maximal leading run of `isDecimalDigit` characters. -/
def spanDigits : List Char → List Char × List Char
  | [] => ([], [])
  | c :: cs =>
    if isDecimalDigit c then
      let p := spanDigits cs
      (c :: p.1, p.2)
    else
      ([], c :: cs)

/-- Consume one release number from the front, exactly as the code below
defines it. Returns the consumed characters and the remainder, or `none` when
the front is not one. -/
def consumeNumber : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
    if c = '0' then
      some (['0'], cs)
    else if c.isDigit then
      let p := spanDigits cs
      (c :: p.1, p.2)
    else
      none

/-- Consume the optional leading group the code below describes, when one is
present and a release number can still be read after it. Returns the consumed
characters and the remainder, or `none`. -/
def consumeEpoch : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
    if isNonZeroDigit c then
      let p := spanDigits cs
      match p.2 with
      | '!' :: rest =>
        match rest with
        | d :: _ => if d.isDigit then some ((c :: p.1) ++ ['!'], rest) else none
        | [] => none
      | _ => none
    else
      none

/-- Consume any number of `'.'`-separated release numbers from the front,
`fuel`-bounded for totality (call with `fuel := cs.length`). Returns the consumed
characters and the remainder. -/
def scanDots : Nat → List Char → List Char × List Char
  | 0, cs => ([], cs)
  | fuel + 1, cs =>
    match cs with
    | '.' :: rest =>
      match consumeNumber rest with
      | some (num, r) =>
        let q := scanDots fuel r
        ('.' :: (num ++ q.1), q.2)
      | none => ([], cs)
    | _ => ([], cs)

/-- The leading numeric prefix of `version` accepted by the clauses below, or
`none` when they accept none. This is the reduction's definition of record. -/
def releasePrefix (version : List Char) : Option (List Char) :=
  match consumeEpoch version with
  | some (e, r) =>
    match consumeNumber r with
    | some (num, r2) =>
      let q := scanDots r2.length r2
      some (e ++ num ++ q.1)
    | none =>
      -- unreachable: the first clause guarantees a following digit; fall back
      match consumeNumber version with
      | some (num, rest) =>
        let q := scanDots rest.length rest
        some (num ++ q.1)
      | none => none
  | none =>
    match consumeNumber version with
    | some (num, rest) =>
      let q := scanDots rest.length rest
      some (num ++ q.1)
    | none => none

/-- Reduce a required-version string to `releasePrefix` of it, or leave it
unchanged when there is none. -/
def normalizeVersion (version : List Char) : List Char :=
  match releasePrefix version with
  | some p => p
  | none => version
-- pure-end

-- post-conditions-start
/-- The decision is the (inclusive-or-strict) version ordering of `haveVersion`
against the *normalized* required version: the required string is first reduced
by `normalizeVersion`, and that reduced value is the one compared. `inclusive`
selects the non-strict (`versionGe`) versus strict (`versionGt`) comparison.

Since the ordering is partial, this clause pins DEFINEDNESS as well as value,
and both halves are load-bearing. `result` carries a verdict exactly when the
REDUCED pair is one the ordering has a value at, and that verdict is the
ordering's answer there; `result` has no verdict exactly when the reduced pair
is not one of those. Consequently the ordering at the UN-reduced pair cannot
influence the outcome in either direction: on a required minimum that the
reduction strictly shortens, the decision is available whenever the reduced
comparison is, even at a raw pair the ordering says nothing about. And because
the ordering is an operation on its domain, the raw pair is not one this
behavior can consult at all without first settling whether the ordering has a
value there — a question that, wherever it is asked, has an answer. -/
def problem_spec_versionAtLeast (haveVersion version : List Char) (inclusive : Bool)
    (result : Option Bool) : Prop :=
  if h : orderable haveVersion (normalizeVersion version) = true then
    result = some (if inclusive
                   then versionGe haveVersion (normalizeVersion version) h
                   else versionGt haveVersion (normalizeVersion version) h)
  else
    result = none
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the required-version string is compared directly,
-- with NO reduction to its leading release-number prefix. When the required
-- string carries a trailing non-numeric qualifier the comparison is performed on
-- the un-reduced string (the actual bug).
def implementation_versionAtLeast (haveVersion version : List Char) (inclusive : Bool) :
    Option Bool := Id.run do
  let ver := version
  if h : orderable haveVersion ver = true then
    if inclusive then
      return some (versionGe haveVersion ver h)
    else
      return some (versionGt haveVersion ver h)
  else
    return none
-- impl-end

-- proof-start
theorem correct_versionAtLeast :
    ∀ (haveVersion version : List Char) (inclusive : Bool),
      problem_spec_versionAtLeast haveVersion version inclusive
        (implementation_versionAtLeast haveVersion version inclusive) := by
  sorry
-- proof-end
