import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.Utils import huggingFace

'''
This file is used to prepare all necessary data for the pipeline.
Especially, downloading and storing the dataset

Datasets: 
SALt-NLP/Design2Code-hf -> https://huggingface.co/datasets/SALT-NLP/Design2Code-hf
xcodemind/webcode2m -> https://huggingface.co/datasets/xcodemind/webcode2m 
'''


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
    '''

    # Configuration
    create_new_dataset = False
    enrich_with_accessibility = True

    dataset = None

    if create_new_dataset:
        dataset = await huggingFace.create_new_dataset(hf_dataset_name=None)
    else:
        dataset = await huggingFace.get_dataset()

    if enrich_with_accessibility:
        dataset = await huggingFace.enrich_dataset(dataset)
    
    return dataset

if __name__ == "__main__":
    asyncio.run(main())