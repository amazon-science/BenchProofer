import Mathlib
-- imports-end

/-!
Normalizing the *method name* of an outgoing HTTP request before the request is
assembled.

A request's method (`GET`, `POST`, …) is supplied by the caller. It may arrive
either as ordinary text or as a raw byte token (some callers encode all of their
arguments to bytes before handing them over). Whatever its incoming form, the
method that is finally stored on the request must:

* carry the **textual content** of the supplied token — i.e. for a byte token the
  bytes are decoded back to their text characters, NOT rendered as some printable
  description of the byte object; and
* be upper-cased (HTTP method tokens are case-insensitive and are canonicalized
  to upper case).

So a method supplied as the byte token for `GET` must be stored as the three
characters `G`, `E`, `T` (upper-cased), exactly as if the caller had passed the
text `"get"`. Rendering the byte token as a printable description of the object
(prefixing/quoting it) would corrupt the method and the request would be directed
at a different resource than the one named.

A supplied method is modeled by its sequence of characters together with a tag
recording whether the caller passed text or a raw byte token. The behavior is
pinned below as an input → output relation on the supplied method; the
implementation and the correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two operations the
-- behavior performs — recovering the textual content of the supplied token and
-- upper-casing it — are modeled DEEPLY (selecting the underlying characters and
-- `List.map Char.toUpper`), so there is no `opaque`/`axiom` callee contract for
-- the proof to consume. Recovering ASCII text from an ASCII byte token and ASCII
-- upper-casing are both total and are exercised end-to-end by the differential
-- check.

/-- A supplied HTTP method: either ordinary text carrying a sequence of
characters (`PyMethod.text`), or a raw byte token carrying a sequence of bytes
(`PyMethod.bytes`) — the form produced by a caller that encodes its arguments
before handing them over. The byte token holds the actual bytes, NOT a
pre-decoded character sequence. -/
inductive PyMethod where
  | text  (chars : List Char)
  | bytes (bytes : List UInt8)
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- The textual content carried by a supplied method, independent of its
incoming form: text passes through unchanged, while a raw byte token is decoded
to its characters one byte at a time (the method tokens of interest are ASCII, so
each byte maps to the character at its code point). -/
def nativeContent : PyMethod → List Char
  | .text cs  => cs
  | .bytes bs => bs.map (fun b => Char.ofNat b.toNat)
-- pure-end

-- post-conditions-start
/-- The stored method is fully pinned to the supplied token: it is the upper-cased
form of the textual content the token carries — for a byte token, the decoded
characters, NOT any printable description of the byte object. The result is pinned
element-wise to the upper-cased input character at each position (and hence to the
same length), leaving no output component free. -/
def problem_spec_normalizeMethod (method : PyMethod) (result : List Char) : Prop :=
  result = (nativeContent method).map Char.toUpper
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: a byte token is rendered as its printable object
-- description — the characters `b` and `'`, then the token's characters, then a
-- closing `'` — instead of being decoded back to text. A method supplied as the
-- byte token for `GET` therefore becomes the literal `B'GET'` after upper-casing,
-- corrupting the request, while a text method is unaffected.
def implementation_normalizeMethod (method : PyMethod) : List Char := Id.run do
  let mut m := match method with
    | .text cs  => cs
    | .bytes bs => ['b', '\''] ++ bs.map (fun b => Char.ofNat b.toNat) ++ ['\'']
  m := m.map Char.toUpper
  return m
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: for a
-- byte token the spec demands the decoded, upper-cased characters, but the buggy
-- impl yields the upper-cased printable description (`B'…'`), so the `bytes` case
-- leaves an unsolved goal.
theorem correct_normalizeMethod :
    ∀ (method : PyMethod),
      problem_spec_normalizeMethod method
        (implementation_normalizeMethod method) := by
  intro method
  unfold problem_spec_normalizeMethod implementation_normalizeMethod
  cases method <;> simp [Id.run, nativeContent]
-- proof-end
