# Goto Removal

## Overview

Goto statements are discouraged because they allow for program flow to be
dramatically altered from the usual structured format. This can make programs
harder to maintain and analyze with optimization tools.

To combat this, _Taming Control Flow: A Structured Approach to Eliminating Goto
Statements_ offers methods to remove every goto statement from a C program. This
is done by listing every possible situation in which a goto statement could
occur, then by giving the method to remove it.

The paper itself gives an excellent overview of the removal techniques, so I
won't repeat its text here. What I _will_ do is offer commentary about how I
implemented this algorithm and the issues that came up. The git commit history
offers a "line-by-line" commentary on what happened, so this is only a
bigger-picture view.

## Implementation Goals

The goals of the implementation are a little different from the original
paper's. The authors' intended to remove gotos during compilation to make
program analysis easier. Here, I want to parse a C file, remove the goto
statements, and then output the C code again.

Because of time constraints, the entire algorithm will not be implemented, but
only up to and including directly related label/goto pairs.

## Tools

The language I chose to implement this algorithm in is Python, and to parse C
code into an AST, I chose to use the pycparser library. The flexibility and
interactivity of python made the project very easy to play with and test.

The benefits of using pycparser are outlined here:

- Parses standard C99 code (it's hard to overstate how useful this is);
- Flexible `NodeVisitor` classes modeled after python's own `api` module;
- Built-in support for printing C code from an AST;

## Difficulties

After understanding the algorithm and getting pycparser working, the issues came
almost solely from the design of the pycparser library. The library was designed
to offer a _look into_ an AST, not to offer an easy way to modify it.

Here's a short list of the issues with pycparser for my purposes:

- Nodes in the AST do not have parents;
- Without parents, there isn't a simple way to move nodes around;
- Use of the special `__slots__` variable for Nodes makes it impossible to add
  parents to nodes;

To solve these, I took the very clunky approach of cloning pycparser and
modifying the parser generator by hand to remove the `__slots__` variable.
Later, in the implementation, parents are added to nodes that need them. This is
probably a Very Bad Thing.

## Paper Notes

Here are some things the paper doesn't always clear up.

- For each label, there is exactly _one_ logical variable.

- If a goto branch is taken, then the logical variable for the target label is
  true. The statement after each label sets its logical variable to 0 so that
  later goto branches aren't taken by accident.
