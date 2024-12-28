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

    # Gets the shortest completion path of the dungeon (reaching the finish from the start, getting only the required keys)
    def shortest_path_least_keys(self):
        graph = self.graph.to_undirected() # undirected because in real play you can go in any direction

        # TODO

        pass

    # Calculates fitness
    def fitness(self):
        value = 0

        start_nodes = [node for node, attr in self.graph.nodes(data=True) if attr.get('type') == Types.START]
        finish_nodes = [node for node, attr in self.graph.nodes(data=True) if attr.get('type') == Types.FINISH]

        # Validity criterion #1: one and only one start room and finish room
        if len(start_nodes) != 1 or len(finish_nodes) != 1:
            return -100

        start_node = start_nodes[0]
        finish_node = finish_nodes[0]

        # Validity criterion #2: the finish room has one and only one entrance, and no exits
        if len(self.graph.in_edges(finish_node)) != 1 or len(self.graph.out_edges(finish_node)) != 0:
            return -50

        locked_edges = [edge for edge, attr in self.graph.edges(data=True) if attr.get('locked')]

        # Penalty criterion #1: the number of locked edges must be around 1/3 of number of rooms
        value -= abs((NUM_ROOMS // 3) - len(locked_edges)) * 5

        # Penalty criterion #2: the number of edges must be around the number of rooms + 33%
        value -= abs(len(self.graph.edges) - (NUM_ROOMS + (NUM_ROOMS // 3))) * 2

        for node in self.graph.nodes:
            in_edges = self.graph.in_edges(node, data=True)

            # Reward criterion #1: more edges a node has, more that room is meaningful, but never more than 4 edges
            interconnection_factor = len(in_edges) + self.graph.out_degree(node)
            if interconnection_factor > 4:
                value -= 25
            else:
                value += interconnection_factor * 2

        return value

    # Prints an individual
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