You are writing a Python program that checks one formalization of a task from a software
benchmark against the repository it is about. The formalization is a solution file the checker,
$backend, has accepted: a specification written in $language, and an implementation proved
against it. The program runs the repository's own code on inputs it draws, compares what that
code does with what the formalization says of it, and prints what it found in the lines
Benchproofer reads, which the request gives. Its worth is the disagreement it can find: a
program that cannot disagree, because it computes the repository's side itself or draws only
inputs the two sides agree on, establishes nothing.

$tests_rules

$image_rules
