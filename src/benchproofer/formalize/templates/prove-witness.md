## What the file claims

The `proof` region holds a refutation witness, not the file's own claim: a statement, at
one concrete input, that this implementation violates the specification. Keep every
statement in it exactly as written -- a witness whose statement changed is not kept -- and
write the proofs that make the checker accept it. The witness is false when this
implementation meets the specification at that input: then report `fail`, saying what the
implementation returns there and which clause holds of it. `fail` says the witness cannot
be proved because it is false; `stuck` says you could not close a goal of a witness that
may be true, and is never the report for one you found false.
