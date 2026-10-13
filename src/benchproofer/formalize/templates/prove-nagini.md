Nagini proves the contracts from the code and the proof annotations in it: a loop's
`Invariant`, an `Assert` stating a fact the next step needs, and `Fold` and `Unfold` of a
predicate. Close every obligation with those, never with `Assume` or `Refute`, which take a
fact for granted. Each error names the line of the construct Viper could not show -- a
postcondition, an invariant, an assertion, a call's precondition -- so read which one, and
what it needs there, before the next edit.
