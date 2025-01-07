from main import genetic_algorithm
import random
import matplotlib.pyplot as plt
import time

num_generations_list = [50, 100, 250, 500, 1000]

fitness_results = []
generation_results = []
time_results = []
for num_generations in num_generations_list:
    print(f"Benchmarking for {num_generations} generations...")

    random.seed(112233445566778899)

    before = time.time()
    result, fitness, generation = genetic_algorithm(num_generations, benchmark=True)
    after = time.time()

    fitness_results.append(fitness)
    generation_results.append(generation)
    time_results.append(round(after - before, 2))

print(fitness_results)
print(generation_results)
print(time_results)

bar_width = 0.4
x_positions = range(len(num_generations_list))

plt.bar([x - bar_width / 3 for x in x_positions], fitness_results, width=bar_width, label='Max fitness')
plt.bar([x for x in x_positions], generation_results, width=bar_width, label='Last generation improvement')
plt.bar([x + bar_width / 3 for x in x_positions], time_results, width=bar_width, label='Algorithm time (s)')

plt.xticks(ticks=x_positions, labels=[str(num) for num in num_generations_list])
plt.xlabel('Number of generations')
plt.ylabel('Values')
plt.title('Fitness, last improvement and time per number of generation')
plt.legend()
plt.tight_layout()
plt.show()