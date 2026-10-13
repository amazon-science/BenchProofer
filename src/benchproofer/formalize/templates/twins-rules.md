The pre-fix implementation is the code before the fix -- each function the golden patch
changes, as it read before the fix -- written in the specification's language. The
specification must reject it: that is what shows the specification is about this task rather
than about something the bug already satisfied.

Constraints:

$regions
* Keep the same entry points and signatures the solution file's `spec` regions expect.
  Where it models several functions, a function the fix did not change keeps its body
  from the solution file.
* Copy the defect. Do not fix it, do not exaggerate it, and do not replace it
  with a different mistake such as returning a constant.
* Keep the reference implementation's loop invariants and other proof annotations
  wherever the pre-fix code keeps the same loop. A pre-fix implementation the checker
  rejects only because a loop lost its invariants was rejected for its proof, which says
  nothing about whether the specification tells the two programs apart.
