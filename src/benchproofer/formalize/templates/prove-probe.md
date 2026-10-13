## What the file claims

The file is an admissibility probe: the reference implementation, which the checker accepts
on its own, and beside it the probe's claims, each opened by $claims inside `impl`, that the
specification admits an input the task's tests use and promises the expected result there.
Each of those claims stays exactly as written: a probe whose claim changed is not kept.
A claim is false when the specification does not admit its input, or promises something
else there: then report `fail` with that input and the clause that refuses it, which is a
finding about the specification and not about your proof.
