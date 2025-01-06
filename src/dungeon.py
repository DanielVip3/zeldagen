from constants import ROOT, NUM_ROOMS, Types

from collections import Counter
import random
from math import exp
from matplotlib import pyplot as plt
import networkx as nx
from copy import deepcopy

class Dungeon:
    # Generates a new dungeon randomly
    def __init__(self, graph=None):
        if not graph:
            # Generate random rooted tree with labels 0 .. K-1, where 0 is the root
            self.graph = nx.random_labeled_rooted_tree(NUM_ROOMS)

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
                    self.graph.edges[edge]['locked'] = False
                    continue

                locked = random.random() < 0.5

                if locked:
                    locked_num += 1

                self.graph.edges[edge]['locked'] = locked
        else:
            self.graph = graph

        self.fitness_cached = None

    # Gets the shortest completion path of the dungeon (reaching the finish from the start, getting only the required keys)
    def shortest_path_least_keys(
        self,
        start,                  # the start node from which to compute the shortest path
        und_graph      = None,  # the undirected graph
        keys           = 0,     # the number of keys we've got at this point of the search
        excluded       = None,  # a set of nodes we excluded from exploring until now (we've already explored them, or they're dead ends)
        unlocked       = None,  # a set of edges we've already unlocked until now
        keys_taken     = None,  # a set of keys we've already taken (to avoid key loops)
        path           = None   # an ordered list of nodes, representing the complete path until now
    ):
        excluded = excluded or set()
        unlocked = unlocked or set()
        keys_taken = keys_taken or set()
        path = path or []

        shortest_path = None
        for (u, v) in und_graph.edges(start): # tries all possible immediate paths from current room
            if v in excluded: # ... except excluded ones
                continue

            # u represents the source room, v the destination room

            # we create clones of the state, for this specific branch (path tried)
            keys_branch = keys
            excluded_branch = set(excluded)
            unlocked_branch = set(unlocked)
            keys_taken_branch = set(keys_taken)
            path_until_now_branch = list(path)

            edge_locked = und_graph[u][v]['locked'] # whether this edge is locked
            destination_room_type = und_graph.nodes[v]['type'] # the type of the destination room

            # first, we'll have to check if the path is unlocked, otherwise nothing to do

            can_go = not edge_locked # whether the path's unlocked (we can proceed) or not
            if not can_go: # if the edge is locked...
                if (u, v) in unlocked: # ... we either unlocked it before
                    can_go = True
                elif keys > 0: # ... or we need a key
                    keys_branch -= 1
                    unlocked_branch.add((u, v)) # and we unlock it for later
                    can_go = True

            if can_go: # if the path is unlocked, we can try to proceed from there
                path_until_now_branch.append(v) # we proceed, by adding the destination room to the path

                # if our destination room is the boss room, we've reached the end
                if destination_room_type == Types.FINISH:
                    return path_until_now_branch

                # if our destination room is a key, we have one more key now, and it's
                # a good idea to try backtracking (so we don't exclude the source room)
                # - we have to check for keys we already took before, though
                if destination_room_type == Types.KEY and v not in keys_taken_branch:
                    keys_branch += 1
                    keys_taken_branch.add(v)
                else: # we exclude the source room, because it makes no sense to return back if we have no new keys
                    excluded_branch.add(u)

                # if the destination node is a dead end, we exclude it, it'll be useless to return later
                if und_graph.degree(v) <= 1:
                    excluded_branch.add(v)

                # we get the shortest path now starting from the destination room
                path_branch = self.shortest_path_least_keys(v, und_graph, keys_branch, excluded_branch, unlocked_branch, keys_taken_branch, path_until_now_branch)
                if path_branch is None:
                    continue

                # we update the final shortest path only if the path we found here was shorter
                if shortest_path is None or len(path_branch) < len(shortest_path):
                    shortest_path = path_branch

        return shortest_path

    def clear_fitness_cache(self):
        self.fitness_cached = None

    # Calculates fitness
    def fitness(self, cache_clear = False):
        if not cache_clear and self.fitness_cached is not None: # computing fitness is expensive, we cache it
            return self.fitness_cached

        value = 0

        graph_und = self.to_undirected()

        start_nodes = []
        finish_nodes = []
        key_nodes = []

        for node, attr in self.nodes(data=True):
            if attr.get('type') == Types.START:
                start_nodes.append(node)
            elif attr.get('type') == Types.FINISH:
                finish_nodes.append(node)
            elif attr.get('type') == Types.KEY:
                key_nodes.append(node)

        # Validity criterion #1 and #2: one and only one start room and finish room
        if len(start_nodes) != 1 or len(finish_nodes) != 1:
            return -100

        start_node = start_nodes[0]
        finish_node = finish_nodes[0]

        # Validity criterion #3: the finish room has one and only one entrance, and no exits
        if len(self.in_edges(finish_node)) != 1 or len(self.out_edges(finish_node)) != 0:
            return -50

        locked_edges = [(node1, node2) for node1, node2, attr in self.edges(data=True) if attr.get('locked')]

        # Penalty criterion #1: the number of locked edges must be around 1/3 of number of rooms
        value -= abs((NUM_ROOMS // 3) - len(locked_edges)) * 5

        # Penalty criterion #2: the number of edges must be around the number of rooms + 33%
        value -= abs(len(self.edges) - (NUM_ROOMS + (NUM_ROOMS // 3))) * 2

        # Penalty criterion #3: the shortest path distance between start and finish room must be at least 2
        if nx.shortest_path_length(graph_und, start_node, finish_node) < 2:
            return -15

        for node in self.nodes:
            in_edges = self.in_edges(node, data=True)

            # Reward criterion #1: more edges a node has, more that room is meaningful, but never more than 4 edges
            interconnection_factor = len(in_edges) + self.out_degree(node)
            if interconnection_factor > 4:
                value -= 25
            else:
                value += interconnection_factor * 2

        # Calculating the shortest path solution to account for solvability, difficulty and linearity
        solution = self.shortest_path_least_keys(ROOT, graph_und) # undirected graph because in real play you can go in any direction

        # Validity criterion #4: the dungeon is solvable
        if solution is None or len(solution) == 0:
            return -100

        # Reward criterion #2: the dungeon's difficulty is balanced (number of rooms required is around half the dungeon)
        value += 5 * round(exp(-NUM_ROOMS * pow((len(solution) - (NUM_ROOMS // 2)) / (NUM_ROOMS // 2), 2)), 2)

        # Reward criterion #3: the dungeon is enough non-linear, but not too much
        backtracking_factor = sum(1 for count in Counter(solution).values() if count > 1) # number of unique repetitions
        value += 5 * round(exp(-(NUM_ROOMS // 2) * pow((backtracking_factor - (NUM_ROOMS // 4)) / (NUM_ROOMS // 4), 2)), 2)

        # Reward criterion #4: the number of key rooms is around the number of locked edges
        value += 5 * round(exp(-NUM_ROOMS * pow((len(key_nodes) - len(locked_edges)) / (len(locked_edges)), 2)), 2)

        self.fitness_cached = value
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

        pos = nx.nx_agraph.graphviz_layout(self.graph, prog="dot") # , scale=0.5
        label_pos = {}

        for k, v in pos.items():
            label_pos[k] = (v[0], v[1] + 15)

        nx.draw(self.graph, pos, with_labels=True, node_color='skyblue', node_size=500, font_size=15, font_weight='bold')

        nx.draw_networkx_labels(self.graph, label_pos, labels=node_labels, font_size=12, font_color='black', verticalalignment="center")
        nx.draw_networkx_edge_labels(self.graph, label_pos, edge_labels=edge_labels, font_size=12, font_color='black', verticalalignment="center")

        plt.show()

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls(deepcopy(self.graph))
        return result

    # Delegate attribute access to the internal graph object, for ease of use, akin to inheritance
    def __getattr__(self, name):
        if name == "graph":
            return self.graph
        elif hasattr(self.graph, name):
            return getattr(self.graph, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")