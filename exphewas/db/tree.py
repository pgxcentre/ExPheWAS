"""
Utilities to process hierarchical data.

tree = tree_from_hierarchy_id("ICD10")

"""


from .models import Hierarchy


class Node(object):
    def __init__(self):
        self.is_root = False

        self.parent = None
        self.children = []

        self.code = None
        self.description = None
        self._data = None

    def __repr__(self):
        parent_code = self.parent.code if self.parent else None

        if self.is_root:
            return "<Root Node>"

        return (
            "<Node '{}' - `{}` [parent is '{}' | {} children]>"
            "".format(self.code, self.description, parent_code,
                      len(self.children))
        )

    def iter_depth_first(self, level=0):
        """Depths first tree traversal rooted at this node."""
        if level > 0:
            yield level, self

        for child in self.children:
            yield from child.iter_depth_first(level + 1)


    def iter_parents(self):
        """Returns the chain of parents up to the root."""
        if self.parent is None:
            return

        else:
            yield self.parent
            yield from self.parent.iter_parents()

    def search_one(self, predicate):
        """Search for the first occurence verifying the predicate in the
           subtree rooted at this node.

        """
        for _, n in self.iter_depth_first():
            if predicate(n):
                return n

        return None

    def formatted_ancestors(self, sep=" > "):
        ancestors = [i.description for i in self.iter_parents()]

        # Remove the root node
        ancestors.pop()

        return sep.join(ancestors[::-1] + [self.description])


def tree_from_hierarchies(hierarchies):
    root = Node()
    root.is_root = True

    nodes_dict = {}

    # Create all nodes.
    for h in hierarchies:
        n = Node()
        n.code = h.code
        n.description = h.description

        # We hold a pointer to the hierarchy if needed.
        n._data = h

        nodes_dict[n.code] = n

    # Set all the hierarchies.
    for h in hierarchies:
        n = nodes_dict[h.code]

        if h.parent is None:
            n.parent = root
            root.children.append(n)

        else:
            # Set the parent and children.
            n.parent = nodes_dict[h.parent]
            nodes_dict[h.parent].children.append(n)

    return root
