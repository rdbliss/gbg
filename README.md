# Goto-Be-Gone

`gbg` is a python program that partially implements the goto-removal algorithm
from _Taming Control Flow: A Structured Approach to Eliminating Goto
Statements_ using a modified pycparser library.

It reads in a C file, searches for a function, prints the function, eliminates
the gotos that it can, then prints the function post-removal.

## Setup

The implementation relies on a slightly modified version of the pycparser
library. A virtualenv will need to be setup in the directory of the project.

    $ virtualenv .
    $ source ./env/bin/activate
    $ (env) pip3 install ./pycparser

This should get it up and running if you're in the virtualenv.

## Usage

`./parse.py infile [function]`

## Supported

- Sibling removal
- Outwards transformations
- Inwards transformations

## Not Supported

- Unconditional gotos

A conditional goto is `if (cond) goto foo`. Wrap unconditionals in `if (true)`.
Hopefully this will be a part of the implementation.

- Statements directly "under" a label

    // The if statement is directly "under" the label, so this won't work.
    bad:
        if (cond) {
            if (jump()) goto bad;
        }

    // No gotos are under the label, so this is fine.
    good:
        foo();
        if (cond) {
            if (jump()) goto good;
        }

- Indirectly related nodes

- Nested inwards transformations
