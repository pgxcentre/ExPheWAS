#!/usr/bin/env python


import csv
import gzip

import pandas as pd

from exphewas.db.tree import Node


def create_nodes(row, nodes):
    levels = list(range(1, 5))


    for i in levels:
        node = nodes.get(getattr(row, f"level{i}"))
        
        level = f"level{i}"

        if node is None:
            node = Node()
            node.code = getattr(row, level)
            node.description = getattr(row, f"level{i}_description")

            nodes[getattr(row, level)] = node

            # Set parent and children relationship.
            if i == 1:
                node.parent = nodes["root"]
            else:
                node.parent = nodes[getattr(row, f"level{i-1}")]

            node.parent.children.append(node)

    return nodes


def main():
    atc = pd.read_csv("chembl_24/raw_atc.csv")

    root = Node()
    root.is_root = True

    nodes = {"root": root}

    for i, row in atc.iterrows():
        nodes = create_nodes(row, nodes)

    tree = nodes["root"]

    with gzip.open("hierarchy_atc.csv.gz", "wt") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "code", "parent", "description"])

        for level, node in tree.iter_depth_first():
            writer.writerow([
                "ATC", node.code, node.parent.code, node.description
            ])


if __name__ == "__main__":
    main()
