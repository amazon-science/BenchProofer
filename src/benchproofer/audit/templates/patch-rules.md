The equivalent patch is the golden patch with the code your implementation corresponds to
changed the way your implementation changes it, and nothing else changed. It is applied with
`git apply` at the root of the repository, and the benchmark's tests are run on the result:
if they fail, the specification accepted a wrong implementation, which is the finding.

* It is raw unified-diff text, starting with `diff --git` or with `---`/`+++` file headers:
  never a description of the change, a file name, or a pointer to the fix. What is applied
  is the text itself, and anything that is not a diff decides nothing.
* Keep the fix's context lines and file headers as they are, so that the patch applies to
  the code the task starts from.
* Be faithful to your implementation and to the mapping the bundle declares. If your
  implementation turns out to behave exactly as the fix does -- equivalent to it rather
  than a wrong implementation -- the faithful patch is the fix itself, verbatim. Do not make
  the patch more wrong, or less, than the implementation it represents: it is judged as that
  implementation.
