"""
Possible bug:

```
first:
    if (1) goto second;
```

pycparser doesn't seem to visit the statement that a label captures?
"""

import pycparser
from pycparser.c_ast import *
from pycparser import c_generator
from collections import namedtuple

def get_function(ast, name):
    for node in ast.ext:
        if type(node) == FuncDef and node.decl.name == name:
            return node

    return None

def pair_goto_labels(labels, conditional_gotos):
    """Return a dictionary of (label, [goto_partners]) pairs.
    The dictionary's keys are label names, and the values are
    lists of If nodes containing whose goto statements targets are the label.
    """
    label_dict = {}

    for label in labels:
        label_dict[label.name] = []

        for cond in conditional_gotos:
            goto = cond.iftrue
            target = goto.name
            if target == label.name:
                label_dict[label.name].append(cond)

    return label_dict

def is_conditional_goto(node):
    """
    Return if `node` is a conditional whose only child is a goto statement.
    """
    return (type(node) == If and type(node.iftrue) == Goto and
                node.iffalse == None)

def update_parents(compound):
    """
    Find every label or conditional goto under the top-level of `compound` and
    make sure their parent is `compound`.
    """
    for node in compound.block_items:
        if type(node) == Goto or is_conditional_goto(node):
            node.parents[-1] = compound

def remove_siblings(label, conditional):
    """Remove a conditional goto/label node pair that are siblings.

    Bug: Parents will need to be updated after this function.
    """
    assert(are_siblings(label, conditional))

    compound = label.parents[-1]
    label_index, cond_index = None, None

    for index, node in enumerate(compound.block_items):
        if node == conditional:
            cond_index = index
        elif node == label:
            label_index = index

    assert(label_index >= 0 and cond_index >= 0)
    assert(label_index != cond_index)

    if label_index > cond_index:
        # Goto is before the label.
        # In this case, we guard the statements from the goto to the label in a
        # new conditional.
        cond = UnaryOp("!", conditional.cond)
        in_between = compound.block_items[cond_index+1:label_index]
        between_compound = Compound(in_between)
        update_parents(between_compound)
        guard = If(cond, between_compound, None)
        pre_goto = compound.block_items[:cond_index]
        post_conditional = compound.block_items[label_index:]
        compound.block_items = pre_goto + [guard] + post_conditional
    else:
        # Goto is after the label (or the goto _is_ the label, which means
        # something has gone terribly wrong).
        # In this case, we place a do-while loop directly after the label that
        # will execute the statements as long as we're jumping.
        # Also, we'll need to make sure we grab the statement that the label
        # itself captures.
        cond = conditional.cond
        between_statements = [label.stmt] + compound.block_items[label_index+1:cond_index]
        between_compound = Compound(between_statements)
        update_parents(between_compound)
        do_while = DoWhile(cond, between_compound)
        label.stmt = do_while
        pre_to_label = compound.block_items[:label_index+1]
        after_goto = compound.block_items[cond_index+1:]
        compound.block_items = pre_to_label + after_goto

def are_siblings(one, two):
    """Check if two nodes with parents are siblings.
    If they don't have parents, this should raise an AttributeError.

    They are siblings iff they both exist unnested in a sequence of
    statements. Currently, this is checked by looking to see if
        1. Both are under a Compound node, and
        2. Both have the _same_ Compound node as a parent.
    I justify this by saying that there can't be any sequence of statements if
    they aren't inside of a Compound.
    """
    one_parent = one.parents[-1]
    two_parent = two.parents[-1]

    under_compound = (type(one_parent) == Compound and
                        type(two_parent) == Compound)

    return under_compound and one_parent == two_parent

class GotoLabelFinder(NodeVisitor):
    """Visitor that will find every goto or label under a given node.

    The results will be two lists of Nodes, self.gotos and self.labels,
    complete with the offset, level, and parent stack monkey patched on for
    each.  The self.gotos list is actually a list of If Nodes, with the offset,
    level, and parent stack of the If. This isn't so strange, as we're treating
    the conditional and goto as one unit.
    """

    def __init__(self):
        self.offset = 0
        self.level = 0
        self.gotos = []
        self.labels = []
        self.parents = []

    def level_visit(self, node):
        self.level += 1
        self.generic_visit(node)
        self.level -= 1

    def generic_visit(self, node):
        self.parents.append(node)
        for access, child in node.children():
            self.visit(child)

        self.parents.pop()

    def visit_Goto(self, node):
        """
        Append the conditonal parent of the goto to self.gotos, or raise a
        NotImplementedError if that isn't possible.

        The conditional parent will have some extra attributes:
            parents: List of nodes above the conditional.

        The goto will also have some extra attributes:
            offset: The offset of the goto.
            level: The level of the goto.
        """
        parents = list(self.parents)
        parent = parents[-1]

        if type(parent) != If:
            line = node.coord.line
            raise NotImplementedError("unsupported unconditional goto statement at line {}".format(line))

        # The parent doesn't have itself as a parent.
        parent.parents = list(self.parents)[:-1]
        # Add some goto-specific data to the goto.
        node.offset = self.offset
        node.level = self.level
        self.gotos.append(parent)

        self.offset += 1

    def visit_Label(self, node):
        """Append the label to self.labels with some extra attributes.
        Attributes:
            parents: Nodes above the label.
            Offset: Offset of the label.
            Level: Level of the label.
        """
        node.parents = list(self.parents)
        node.offset = self.offset
        node.level = self.level
        self.labels.append(node)
        self.offset += 1

    def visit_If(self, node):
        self.level_visit(node)
    def visit_While(self, node):
        self.level_visit(node)
    def visit_DoWhile(self, node):
        self.level_visit(node)
    def visit_Switch(self, node):
        self.level_visit(node)
    def visit_For(self, node):
        self.level_visit(node)

    def visit_Compound(self, node):
        # Only increment the level if we're not a part of a "leveler."
        if not type(self.parents[-1]) in [If, While, DoWhile, Switch, For]:
            self.level += 1
            self.generic_visit(node)
            self.level -= 1
        else:
            self.generic_visit(node)

def do_it(func_node):
    t = GotoLabelFinder()
    t.visit(func_node)
    labels = t.labels
    gotos = t.gotos
    d = pair_goto_labels(labels, gotos)

    for label in t.labels:
        for conditional in d[label.name]:
            if are_siblings(label, conditional):
                print("Siblings!")
                remove_siblings(label, conditional)
            else:
                print("Not!")

if __name__ == "__main__":
    import sys

    filename = ""
    function_name = ""
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "./test.c"

    try:
        function_name = sys.argv[2]
    except IndexError:
        function_name = "main"

    ast = pycparser.parse_file(filename, use_cpp=True,
                    cpp_args="-I/usr/share/python3-pycparser/fake_libc_include")
    func = get_function(ast, function_name)
    generator = c_generator.CGenerator()

    print(generator.visit(func))
    do_it(func)
    print(generator.visit(func))
