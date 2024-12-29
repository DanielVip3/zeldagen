from constants import Types, ROOT, FINISH, NUM_ROOMS
from dungeon import Dungeon
from copy import deepcopy
import random

import networkx as nx

def selection(population, population_size):
    tournament = random.sample(population, population_size // 3)
    return sorted(tournament, key=lambda ind: ind.fitness(), reverse=True)[0]

def crossover(parent1, parent2):
    child1 = deepcopy(parent1)
    child2 = deepcopy(parent2)

    child1_leaves = child1.leaves()
    child2_leaves = child2.leaves()

    if not child1_leaves or not child2_leaves:
        return child1, child2

    random_leaf1 = random.choice(child1_leaves)
    random_leaf2 = random.choice(child2_leaves)

    random_leaf1_predecessor = random.choice(list(child1.graph.predecessors(random_leaf1)))
    random_leaf2_predecessor = random.choice(list(child2.graph.predecessors(random_leaf2)))

    leaf1_type = child1.graph.nodes[random_leaf1]['type']
    leaf2_type = child2.graph.nodes[random_leaf2]['type']

    child1.graph.nodes[random_leaf1]['type'] = leaf2_type
    child2.graph.nodes[random_leaf2]['type'] = leaf1_type

    edge1_locked = child1.graph.edges[random_leaf1_predecessor, random_leaf1]['locked']
    edge2_locked = child2.graph.edges[random_leaf2_predecessor, random_leaf2]['locked']

    child1.graph.edges[random_leaf1_predecessor, random_leaf1]['locked'] = edge2_locked
    child2.graph.edges[random_leaf2_predecessor, random_leaf2]['locked'] = edge1_locked

    return child1, child2

def should_lock(individual):
    locked_edges = [(node1, node2) for node1, node2, attr in individual.graph.edges(data=True) if attr.get('locked')]
    return len(locked_edges) < (NUM_ROOMS // 3)

def mutation(individual):
    while True:
        action = random.randint(1, 4)

        if action == 1: # add an edge
            if len(individual.graph.edges) >= (NUM_ROOMS + (NUM_ROOMS // 3)):
                continue

            node = random.choice(range(ROOT + 1, FINISH))

            connected = set(nx.all_neighbors(individual.graph, node))
            connected.add(node)

            possible_connections = [node for node, attr in individual.graph.nodes(data=True) if node not in connected and attr.get('type') not in [Types.START, Types.FINISH]]
            if not possible_connections:
                continue

            node_to_connect = random.choice(possible_connections)

            individual.graph.add_edge(node, node_to_connect, locked=should_lock(individual))
        elif action == 2: # remove an edge
            if len(individual.graph.edges) < (NUM_ROOMS + (NUM_ROOMS // 3)):
                continue

            possible_edges = [(node1, node2) for node1, node2, attr in individual.graph.edges(data=True)
                              if individual.graph.nodes[node2]['type'] != Types.FINISH and individual.graph.in_degree(node2) > 1]
            if not possible_edges:
                continue

            edge = random.choice(possible_edges)
            individual.graph.remove_edge(*edge)
        elif action == 3: # change node type
            node = random.choice(range(ROOT + 1, FINISH))
            individual.graph.nodes[node]['type'] = random.choice([Types.NORMAL, Types.KEY])
        elif action == 4: # toggle edge lock
            to_lock = should_lock(individual)

            possible_edges = [(node1, node2) for node1, node2, attr in individual.graph.edges(data=True)
                              if individual.graph.nodes[node2]['type'] != Types.FINISH and attr.get('locked') != to_lock]
            if not possible_edges:
                continue

            edge = random.choice(possible_edges)
            individual.graph.edges[edge]['locked'] = to_lock
        break

def genetic_algorithm(population_size = 10):
    # Initialize population
    population = [Dungeon() for i in range(population_size)]

genetic_algorithm()

d1 = Dungeon()
d1.print()
mutation(d1)
d1.print()
# print(d.shortest_path_least_keys(0))
