import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.Utils import utils_dataset
from practical.Utils import utils_html
from practical.Accessibility import accessibilityIssues

'''
This file is used to prepare all necessary data for the pipeline.
Especially, downloading and storing the dataset

Datasets: 
SALt-NLP/Design2Code-hf -> https://huggingface.co/datasets/SALT-NLP/Design2Code-hf
xcodemind/webcode2m -> https://huggingface.co/datasets/xcodemind/webcode2m 
'''

DATA_PATH = os.path.join(os.path.dirname(__file__), 'Data')
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

        store_in_data_folder = True 
        This stores the dataset in the data folder. Necessary for the pipeline
    '''

    # Configuration
    create_new_dataset = False
    store_in_data_folder = True
    enrich_with_accessibility = False

    dataset = None

    if create_new_dataset:
        dataset = await utils_dataset.create_new_dataset(hf_dataset_name=None)
    else:
        dataset = await utils_dataset.get_dataset_hf(DATASET_HF)

    if store_in_data_folder:
        utils_dataset.store_dataset_in_dir(dataset, DATA_PATH)

    if enrich_with_accessibility:
        dataset = await accessibilityIssues.getAccessibilityIssues(dataset)

    return dataset

if __name__ == "__main__":
    asyncio.run(main())