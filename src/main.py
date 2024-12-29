from constants import Types
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

def genetic_algorithm(population_size = 10):
    # Initialize population
    population = [Dungeon() for i in range(population_size)]

genetic_algorithm()

d1 = Dungeon()
d2 = Dungeon()
d1.print()
d2.print()
c1, c2 = crossover(d1, d2)
c1.print()
c2.print()
# print(d.shortest_path_least_keys(0))
