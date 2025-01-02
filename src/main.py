from constants import Types, ROOT, FINISH, NUM_ROOMS
from dungeon import Dungeon
from copy import deepcopy
import random
import networkx as nx

def selection(population, population_size):
    tournament = random.sample(population, population_size // 4)
    return sorted(tournament, key=lambda ind: ind.fitness(), reverse=True)[0]

def crossover(parent1, parent2):
    child1 = deepcopy(parent1)
    child2 = deepcopy(parent2)

    child1.clear_fitness_cache()
    child2.clear_fitness_cache()

    child1_leaves = [node for node, attr in child1.graph.nodes(data=True) if child1.graph.out_degree(node) == 0 and attr.get('type') != Types.FINISH]
    child2_leaves = [node for node, attr in child2.graph.nodes(data=True) if child2.graph.out_degree(node) == 0 and attr.get('type') != Types.FINISH]

    if not child1_leaves or not child2_leaves:
        return child1, child2

    random_leaf1 = random.choice(child1_leaves)
    random_leaf2 = random.choice(child2_leaves)

    leaf1_predecessors = list(child1.graph.predecessors(random_leaf1))
    leaf2_predecessors = list(child2.graph.predecessors(random_leaf2))

    if not leaf1_predecessors or not leaf2_predecessors:
        return child1, child2

    random_leaf1_predecessor = random.choice(leaf1_predecessors)
    random_leaf2_predecessor = random.choice(leaf2_predecessors)

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

            node = random.choice(range(ROOT, FINISH))

            possible_connections = [poss_node for poss_node, attr in individual.graph.nodes(data=True)
                                    if attr.get('type') != Types.FINISH
                                    and node != poss_node
                                    and not individual.graph.has_edge(poss_node, node)
                                    and not individual.graph.has_edge(node, poss_node)]
            if not possible_connections:
                continue

            node_to_connect = random.choice(possible_connections)

            individual.graph.add_edge(node, node_to_connect, locked=should_lock(individual))
        elif action == 2: # remove an edge
            if len(individual.graph.edges) < (NUM_ROOMS + (NUM_ROOMS // 3)):
                continue

            bridges = list(nx.bridges(individual.graph.to_undirected()))

            possible_edges = [(node1, node2) for node1, node2, attr in individual.graph.edges(data=True)
                              if individual.graph.nodes[node1]['type'] != Types.START
                              and individual.graph.nodes[node2]['type'] != Types.FINISH
                              and (node1, node2) not in bridges
                              and (node2, node1) not in bridges]
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

    individual.clear_fitness_cache()
    return individual

def genetic_algorithm(generations = 500, population_size = 15, elite_size = 3):
    # Initialize population
    population = [Dungeon() for i in range(population_size)]

    for gen in range(generations): # for each generation
        new_population = []

        # Elitism: select the top 'elite_size' individuals
        population.sort(key=lambda ind: ind.fitness(), reverse=True)
        elite_individuals = population[:elite_size]

        # Generate the new generation
        while len(new_population) < (population_size - elite_size):
            # Selection: two of them for crossover (using tournament selection)
            parent1 = selection(population, population_size)
            parent2 = selection(population, population_size)

            # Cross-over
            child1, child2 = crossover(parent1, parent2)

            # Mutation
            child1 = mutation(child1)
            child2 = mutation(child2)

            new_population.extend([child1, child2])

        new_population.extend(elite_individuals)

        # Replace old population
        population = new_population

    return max(population, key=lambda ind: ind.fitness())

best_individual = genetic_algorithm(250)
best_individual.print()