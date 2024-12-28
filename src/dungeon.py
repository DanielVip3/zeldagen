from constants import ROOT, NUM_ROOMS, Types

import random
from matplotlib import pyplot as plt
import networkx as nx

class Dungeon():
    # Generates a new dungeon randomly
    def __init__(self):
        # Generate random rooted tree with labels 0 .. K-1, where 0 is the root
        self.graph = nx.random_labeled_rooted_tree(NUM_ROOMS, seed=1234)

        # Does BFS on the tree, to make it oriented
        self.graph = nx.bfs_tree(self.graph, ROOT)

        # Root will be the start
        self.graph.nodes[ROOT]['type'] = Types.START

        # The middle rooms (between 1 and K-2) will be randomly normal rooms and key rooms
        for i in range(1, NUM_ROOMS - 1):
            self.graph.nodes[i]['type'] = random.choice([Types.NORMAL, Types.KEY])

        # The last room will be the finish
        self.graph.nodes[NUM_ROOMS - 1]['type'] = Types.FINISH

        # The last room needs to have only a single entrance (in-edge)
        final_edge = None
        for edge in self.graph.in_edges(NUM_ROOMS - 1):
            if not final_edge:
                final_edge = edge
            else:
                self.graph.remove_edge(*edge)

        # The single entrance of the final room needs to be locked
        self.graph.edges[final_edge]['locked'] = True

        # For each remaining edge, it is randomly selected to be locked or not, up to a maximum of (number of rooms - 2)
        # (because all rooms except start and finish can be key rooms)
        locked_num = 1
        for edge in (self.graph.edges - [final_edge]):
            if locked_num >= (NUM_ROOMS - 2):
                break

            locked = random.random() < 0.5

            if locked:
                locked_num += 1

            self.graph.edges[edge]['locked'] = locked

    def print(self):
        print(self.graph)

        node_labels = nx.get_node_attributes(self.graph, 'type')
        edge_labels = nx.get_edge_attributes(self.graph, 'locked')

        for node in node_labels:
            node_labels[node] = node_labels[node].name.upper()[0]

        for edge in edge_labels:
            edge_labels[edge] = "L" if edge_labels[edge] else ""

        pos = nx.bfs_layout(self.graph, ROOT, scale=0.5)
        label_pos = {}

        for k, v in pos.items():
            label_pos[k] = (v[0], v[1] + 0.05)

        nx.draw(self.graph, pos, with_labels=True, node_color='skyblue', node_size=500, font_size=15, font_weight='bold')

        nx.draw_networkx_labels(self.graph, label_pos, labels=node_labels, font_size=12, font_color='black', verticalalignment="center")
        nx.draw_networkx_edge_labels(self.graph, label_pos, edge_labels=edge_labels, font_size=12, font_color='black', verticalalignment="center")

        plt.show()