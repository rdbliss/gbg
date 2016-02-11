# Goto Removal

## Overview

Goto statements move code execution from one place to another, in a
non-structured way. They are rarely good things. Bouncing program flow makes
analysis and maintenance difficult, so gotos have been recommended against in
most cases.

To help fix this, _Taming Control Flow: A Structured Approach to Eliminating
Goto Statements_ offers methods to remove every goto statement from a C
program. It lists every possible situation in which a goto statement could find
itself, then shows how to remove it. Here is a partial implementation of its
algorithm in Python.

The paper itself gives an excellent overview of the removal techniques, so I
won't repeat those here. Here is for commentary. Implementation decisions,
quirky bits, etc. The git commit history offers a "line-by-line" commentary on
what happened, so this is mostly a bigger-picture view.

## Implementation Goals

The authors focused on program analysis. Here, I want to parse a C file, remove
the goto statements, and then output the C code again.

## Tools

The main tool used is the pycparser library. Benefits of using pycparser:

- Parses standard C99 code

It's hard to overstate how complicated C code is. Someone else writing the
parser is a burden removed.

- Flexible `NodeVisitor` classes modeled after python's own `api` module

Although lacking the ability to modify nodes, the `NodeVisitor` class comes in
handy when trying to find every type of a certain node.

- Built-in support for printing C code from an AST

## Difficulties

After understanding the algorithm and getting pycparser working, the issues
seemed to come from the design of the pycparser library. It was designed to
_look into_ the AST, not to modify it.

- No simple way to navigate the AST

There are no siblings or parents, only children. Given a node, it is impossible
to tell if it is the child of a certain type of node, or has other nodes beside
it. This makes moving nodes around hard. As a subproblem, updating parents is
hard if you store them as a list.

- `__slots__`

The `__slots__` variable, present on every node, disables attribute adding for
memory efficiency.

To solve these, I modified pycparser's parser generator code to remove the
`__slots__` variable. This was a rough solution. Later in the implementation,
parents are added to nodes that need them.

## Paper Notes

Here are some things the paper doesn't clear up.

- For each label, there is exactly _one_ logical variable.

- If a goto branch is taken, then the logical variable for the target label is
  1. The statement after each label sets its logical variable to 0 so that
  later goto branches aren't taken by accident.
