`Outside the bridge`, a section of `correspondence.md`, names the inputs on which the
implementation is not set against the golden patch, each with why, and an input the model's
domain has to admit is left out of it only by an entry there. A precondition, an
`Outside the bridge` entry or a skip in `conformance.py` that shuts out an input the
specification admitted before, or one the model's domain has to admit, is a narrowing. The
entries are of three kinds, and no other:

* a value the model's types admit that the repository never has where the modeled function is
  called -- a mapping without a key the repository always records, say. On it the
  specification's claim is about no run of the repository.
* a repository value the type bridge -- how each of the specification's types maps onto the
  repository's values, written in `correspondence.md` -- reads as another, where none of the
  FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or edits, and no sentence
  of the issue, tells the two apart, and the golden patch returns on both or raises on both --
  a key that is absent and one whose value is `None`, under an `Option`. On it the
  specification's claim is about the value it is read as, and says nothing of the difference.
  Where one of those tests or the issue tells the two apart, the model states the difference,
  and an input the golden patch raises on is never merged with one it returns on: the model
  states what the repository does there, and such a merge is a narrowing, not an entry.
* an input on which the fixed function runs only what the golden patch leaves as it was: it
  returns or raises before any changed line, or it tests a condition the golden patch adds,
  finds it false, and goes on into a branch the patch leaves as it was. The entry names that
  branch, or the line that returns or raises. There the fixed function does what the code
  before the fix did. A behavior checked by a FAIL_TO_PASS test, or by a PASS_TO_PASS test the
  test patch adds or edits, is never left out this way.

None of the three is a narrowing. An entry is checked rather than trusted: for the first kind,
that the repository never has the value there; for the second, that the type bridge reads the
two alike, that none of the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds
or edits tells them apart, and that the golden patch returns on both or raises on both; for the
third, trace one input the entry names through the function before the fix and after it, and
see the same lines run, apart from the false test of a condition the golden patch adds. An
entry of any other kind, or one that fails its check, excuses nothing.
