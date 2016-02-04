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
    Return if `node` is a conditional whose only branch is a goto statement.
    """
    return (type(node) == If and type(node.iftrue) == Goto and
                node.iffalse == None)

def update_parents(compound):
    """
    Find every label or conditional goto under the top-level of `compound` and
    make sure their parent is `compound`.
    Normally used after a transformation.
    """
    for node in compound.block_items:
        if type(node) == Goto or is_conditional_goto(node):
            node.parents[-1] = compound

def remove_siblings(label, conditional):
    """Remove a conditional goto/label node pair that are siblings.
    Parents need to be updated after the removal, and this function does that."""
    assert(are_siblings(label, conditional))

    compound = label.parents[-1]
    label_index = compound.block_items.index(label)
    cond_index = compound.block_items.index(conditional)

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

def are_directly_related(one, two):
    """Check if two nodes are directly related.
    If they don't have parents, this should raise an AttributeError.

    Two nodes are siblings iff there exists some sequence of statements such that
    one is present in one, and the other is either present or nested inside of
    one of the statements.

    Note: Being siblings is a special case of being related.

    The check is this:
        - At least one has a Compound parent.
        - The other has that same compound parent somewhere in its parent
          stack.
    """
    parent_one = one.parents[-1]
    parent_two = two.parents[-1]
    if type(parent_one) == Compound and parent_one in two.parents:
        # `two` exists in or is nested in the compound that `one` is in.
        return True
    elif type(parent_two) == Compound and parent_two in one.parents:
        # `one` exists in or is nested in the compound that `two` is in.
        return True

    return False

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

def is_loop(node):
    return type(node) in [While, DoWhile, For]

def under_loop(node):
    """Test if a node is under a compound that is under a loop.
    A node is under a loop if its parents are compound, then (loop).
    If the node doesn't have parents, this will raise an AttributeError.
    """
    parent = node.parents[-1]
    above_parent = node.parents[-2]
    return type(parent) == Compound and is_loop(above_parent)

def under_switch(node):
    """Test if a node is under a switch statement.
    This happens if its parents are case, then compound, then switch.
    If the node doesn't have parents, this will raise an AttributeError.
    """
    switch, above_parent, parent = node.parents[-3:]
    return (type(parent) == Case and type(above_parent) == Compound and
                type(switch) == Switch)

def move_goto_out_switch(conditional):
    """Move a conditional goto out of a switch statement."""
    assert(under_switch(conditional))

    above_compound, switch, switch_compound, case = conditional.parents[-4:]

    if type(above_compound) != Compound:
        raise NotImplementedError("Only support switch statements under "
                                    "compounds!")

    cond = conditional.cond
    goto = conditional.iftrue
    name = logical_label_name(goto)
    # Set the logical value to the condition of the goto.
    set_logical = create_assign(name, cond)

    # If the logical variable is true, then break out of the switch.
    guard = If(ID(name), Break(), None)

    cond_index = case.stmts.index(conditional)
    assert(cond_index >= 0)

    case.stmts[cond_index] = set_logical
    case.stmts.insert(cond_index+1, guard)

    switch_index = above_compound.block_items.index(switch)
    above_compound.block_items.insert(switch_index+1, conditional)

    # We moved above three parents, so remove three of them from the conditional
    # to make sure that later checks work.
    conditional.parents = conditional.parents[:-3]

def move_goto_out_loop(conditional):
    """Move a conditional goto out of a loop statement."""
    assert(under_loop(conditional))

    if type(above_parent) != Compound:
        raise NotImplementedError("Can only pull gotos out of loops that are "
                                    "under a compound!")

    cond = conditional.cond
    goto = conditional.iftrue
    name = logical_label_name(goto)
    # Set the logical value to the condition of the goto.
    set_logical = create_assign(name, cond)

    # If the logical variable is true, then break out of the loop.
    guard = If(ID(name), Break(), None)

    cond_index = loop_compound.block_items.index(conditional)
    assert(cond_index >= 0)

    loop_compound.block_items[cond_index] = set_logical
    loop_compound.block_items.insert(cond_index+1, guard)

    loop_index = above_parent.index(loop)
    above_parent.block_items.insert(loop_index+1, conditional)

    # We moved above two parents, so remove two of them from the conditional to
    # make sure that later checks work.
    conditional.parents = conditional.parents[:-2]

def declare_regular_variable(var_id, type_name, init, function):
    """Declare `type_name var_id = init` at the top of `function`.
    This is "regular" in the sense that there are no storage qualifiers.

    :var_id: A node of type ID.
    :type_name: A string specificing what type the variable is.
    :init: A node specifiying what the initial value is.
    :function: The FuncDef node where this variable will be declared.
    :returns: Nothing.
    """
    id_type = IdentifierType([type_name])
    type_decl = TypeDecl(var_id.name, [], id_type)
    decl = Decl(var_id, [], [], [], type_decl, init, None)

    function.body.block_items.insert(0, decl)

def declare_logic_variable(name, function):
    """Declare the variable `int name = 0` at the top of `function`."""
    var_id = ID(name)
    type_name = "int"
    logical_value = Constant(type_name, "0")
    declare_regular_variable(var_id, type_name, logical_value, function)

def create_assign(name, val):
    var_id = ID(name)
    return Assignment("=", var_id, val)

def logical_label_name(goto_label):
    return "goto_{}".format(goto_label.name)

def logic_init(labels, func):
    """
    Declare a logical variable `goto_LABEL = 0` for each label in `labels` at
    the top of `func`. Also, reinitialize it to 0 at the label.
    This is only useful if each label is actually _in_ the function.
    """

    for label in labels:
        compound = label.parents[-1]
        if type(compound) != Compound:
            raise NotImplementedError("Can only initialize labels under compounds for now!")
        declare_logic_variable("goto_{}".format(label.name), func)

        val = Constant("int", "0")
        clear_logical_var = create_assign(logical_label_name(label), val)
        label_index = compound.block_items.index(label)

        # Move the statement that the label holds to after the label,
        # and the setting to 0 into the label.
        compound.block_items.insert(label_index + 1, label.stmt)
        label.stmt = clear_logical_var

def do_it(func_node):
    t = GotoLabelFinder()
    t.visit(func_node)
    labels = t.labels
    gotos = t.gotos
    d = pair_goto_labels(labels, gotos)
    logic_init(t.labels, func_node)

    for label in t.labels:
        for conditional in d[label.name]:
            while not are_siblings(label, conditional):
                if not are_directly_related(label, conditional):
                    print("Skipping two indirectly related nodes...")
                    break

                if under_loop(conditional):
                    move_goto_out_loop(conditional)
                else:
                    print("Nothing we can do for the non-looped...")
                    break

                print("One iteration done...")

            if are_siblings(label, conditional):
                print("Siblings!")
                remove_siblings(label, conditional)
            else:
                print("Well, we tried.")

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

    # Copy contents of `do_it` just for interpreter convenience.
    t = GotoLabelFinder()
    t.visit(func)
    labels = t.labels
    gotos = t.gotos
    d = pair_goto_labels(labels, gotos)
