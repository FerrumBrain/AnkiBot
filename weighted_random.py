import random


def choice(weights: dict, data: list):
    sum_weight = 0
    for name in weights.keys():
        if name not in data:
            continue

        right_guess, total_guess = weights[name]
        if right_guess == 0:
            sum_weight += 1
        else:
            sum_weight += total_guess / right_guess

    random_choice = random.uniform(0, sum_weight)

    sum_weight = 0
    for index, name in enumerate(weights.keys()):
        if name not in data:
            continue

        right_guess, total_guess = weights[name]
        if right_guess == 0:
            sum_weight += 1
        else:
            sum_weight += total_guess / right_guess

        if sum_weight >= random_choice:
            return name
