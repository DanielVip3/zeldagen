from constants import Types
from dungeon import Dungeon
import random

import networkx as nx

def selection(population, population_size):
    tournament = random.sample(population, population_size // 3)
    return sorted(tournament, key=lambda ind: ind.fitness(), reverse=True)[0]

def genetic_algorithm(population_size = 10):
    # Initialize population
    population = [Dungeon() for i in range(population_size)]

genetic_algorithm()

d = Dungeon()
d.print()
print(d.shortest_path_least_keys(0))
