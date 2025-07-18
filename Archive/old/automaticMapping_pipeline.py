import asyncio
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from practical.Utils import utils_dataset
from practical.Accessibility import accessibilityIssues


DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'Data')
DATASET_HF = "marcolutz/Image2Code"


async def main():
    '''
        Important: Change the configuration as you need it.

        create_new_dataset = True
        This creates a dataset using some 'cherry-picked' examples of the datasets above.
        If the hf_dataset_name is None, the dataset will be stored on disk

        If it is still necessary to enrich the dataset with accessibility information, set
        enrich_with_accessibility = True

        If you do not need to create a new dataset or enrich it with accessibility information,
        set both to False.

        store_dataset_in_data_dir = True 
        This stores the dataset in the data directory. Necessary for the pipeline
    '''



    dataset = await utils_dataset.get_dataset_hf(DATASET_HF)
    # dataset = await utils_dataset.get_dataset_hf_locally(DATASET_HF)
        

    counter = 1
    for data_entry in dataset:
        print("Start: ", counter)
        generated_accessibility_map = await accessibilityIssues.create_automatic_mapping(os.path.join(DATA_PATH, "Input", "html", f"{counter}.html"))
        counter += 1

    return generated_accessibility_map

if __name__ == "__main__":
    asyncio.run(main()) 