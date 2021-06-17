"""
Utilities to process hierarchical data.

tree = tree_from_hierarchy_id("ICD10")

"""

import collections


from .models import Hierarchy
from .engine import Session


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

    def search_all(self, predicate):
        """Search for all occurence verifying the predicate in the subtree
           rooted at this node.

        """
        return filter(predicate, self.iter_depth_first())

    def formatted_ancestors(self, sep=" > "):
        ancestors = [
            i.description if i.description is not None else i.code
            for i in self.iter_parents()
        ]

        # Remove the root node
        ancestors.pop()

        return sep.join(
            ancestors[::-1] +
            [self.description if self.description is not None else self.code]
        )

    def to_primitive(self):
        """Converts a tree into a nested dict representation."""

        out = {
            "code": self.code if not self.is_root else "root",
            "description": self.description if self.description else "",
            "data": self._data,
        }

        for child in self.children:
            if "children" not in out:
                out["children"] = []

            out["children"].append(child.to_primitive())

        return out


def tree_from_hierarchies(hierarchies, keep_hierarchy=False):
    root = Node()
    root.is_root = True

    # We use {code -> {parent_code: node}} for fast indexing.
    nodes_dict = collections.defaultdict(dict)

    # Create all nodes.
    for h in hierarchies:
        n = Node()
        n.code = h.code
        n.description = h.description

        # We hold a pointer to the hierarchy if needed.
        if keep_hierarchy:
            n._data = h

        nodes_dict[h.code][h.parent] = n

    # Set all the hierarchies.
    for h in hierarchies:
        n = nodes_dict[h.code][h.parent]

        if h.parent != Hierarchy.DEFAULT_PARENT:
            # Find parent if needed.
            parent = list(nodes_dict[h.parent].values())

            if len(parent) == 0:
                raise ValueError(f"Could not find parent for node {n}")

            elif len(parent) == 1:
                parent = parent[0]

            else:
                raise ValueError(f"Ambiguous parent for node {n}")

            # Set the parent and children.
            n.parent = parent
            parent.children.append(n)

        else:
            n.parent = root
            root.children.append(n)

    return root


def tree_from_hierarchy_id(id):
    hierarchies = Session()\
        .query(Hierarchy)\
        .filter_by(id=id)\
        .order_by(Hierarchy.code)\
        .all()

    return tree_from_hierarchies(hierarchies)
