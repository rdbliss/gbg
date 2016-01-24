import pycparser
from pycparser.c_ast import *
from collections import namedtuple

NodeExtra = namedtuple("ExtraNode", "parents offset level node")

def get_main(ast):
    for node in ast.ext:
        if type(node) == FuncDef and node.decl.name == "main":
            return node

    return None

class GotoLabelFinder(NodeVisitor):
    """Visitor that will find every goto or label under a given node.

    The results will be two lists of NodeExtra's, self.gotos and self.labels,
    complete with the offset, level, and parent stack for each.
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
        seld.level -= 1

    def generic_visit(self, node):
        self.parents.append(node)
        for access, child in node.children():
            self.visit(child)

        self.parents.pop()

    def visit_Goto(self, node):
        parents = list(self.parents)
        self.gotos.append(NodeExtra(parents, self.offset, self.level, node))
        self.offset += 1

    def visit_Label(self, node):
        parents = list(self.parents)
        self.labels.append(NodeExtra(parents, self.offset, self.level, node))
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

if __name__ == "__main__":
    ast = pycparser.parse_file("./test.c", use_cpp=True,
                    cpp_args="-I/usr/share/python3-pycparser/fake_libc_include")
    main = get_main(ast)
    t = GotoLabelFinder()
    t.visit(main)
