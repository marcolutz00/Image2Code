import os

'''
    For each Test Case (Model, Prompt Strategy) there exist 3 test rounds.
    Each test round consists of 53 images.

    -> Therefore, the final result file for each round has to be averaged 
    over 3 test rounds.
'''


def get_average_results(results):
    """
        Reads the result files from each round and calculates the average
    """
    average_results = {}

    for model, strategies in results.items():
        average_results[model] = {}
        for strategy, rounds in strategies.items():
            total_time = 0
            total_tokens = 0
            total_images = 0

            for round_data in rounds:
                total_time += round_data['time']
                total_tokens += round_data['tokens']
                total_images += round_data['images']

            average_results[model][strategy] = {
                'time': total_time / len(rounds),
                'tokens': total_tokens / len(rounds),
                'images': total_images / len(rounds)
            }

    return average_results