import asyncio
import os
import sys
import json
from PIL import Image

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

        store_dataset_in_data_dir = True 
        This stores the dataset in the data directory. Necessary for the pipeline
    '''

    # Configuration
    # If no own dataset exists in HuggingFace yet
    create_new_dataset = False
    # Store the dataset locally in Data Directory
    store_dataset_in_data_dir = False
    # Print Images of Dataset
    show_images_dataset = False
    # Update Column in Dataset
    update_column_dataset = False
    update_column = None

    dataset = None

    if create_new_dataset:
        dataset = await utils_dataset.create_new_dataset(hf_dataset_name=DATASET_HF)
        enrich_with_accessibility_issues(dataset)
    else:
        dataset = await utils_dataset.get_dataset_hf(DATASET_HF)
        # dataset = await utils_dataset.get_dataset_hf_locally(DATASET_HF)

    if store_dataset_in_data_dir:
        utils_dataset.store_dataset_in_dir(dataset, DATA_PATH)

    if show_images_dataset:
        for data_entry in dataset:
            image = data_entry.get("image")
            image.show()
    
    if update_column_dataset and update_column != None:
        dataset = await utils_dataset.update_dataset_hf(DATASET_HF, update_column)
       

    return dataset


async def enrich_with_accessibility_issues(dataset):
    counter = 1
    for data_entry in dataset:
        # image = data_entry.get("image")
        # image.show()
        # print(counter)

        # if counter < 8:
        #     counter += 1 
        #     continue

        accessibility_issues_json = await accessibilityIssues.get_accessibility_issues(os.path.join(DATA_PATH, "Input", "html", f"{counter}.html"))
        
        # with open(os.path.join(DATA_PATH, "Input", "json", f"{counter}.json"), "w") as f:
        #     json.dump(accessibility_issues_json, f)
        
        counter += 1
    
    await utils_dataset.update_dataset_hf_accessibility(DATASET_HF)



if __name__ == "__main__":
    dataset = asyncio.run(main())    
    asyncio.run(enrich_with_accessibility_issues(dataset))
