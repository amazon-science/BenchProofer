
Under this checker a control the checker refuses can come with a refutation witness, in a file of
its own passed to `$tools try` with `--refutation` and filed with the control, and a witness
test, passed with `--test`:

$witness_rules

The control's witness test is a Python program Benchproofer runs once where the benchmark's
tests run, with the golden patch applied. It passes only where the fixed code returns, at the
witness's input, what your control returns there: build that input and that result as
`correspondence.md` maps the specification's types onto the repository's values, call the fixed
code on the input, and compare.
When the checker proves the witness and the test passes, the specification refuses a correct
implementation, which is the finding a control exists for.
