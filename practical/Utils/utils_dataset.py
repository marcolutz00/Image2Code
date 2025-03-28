from datasets import load_dataset, load_from_disk, concatenate_datasets, Dataset
from huggingface_hub import login
from PIL import Image
import os
import json
import asyncio


CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
KEYS_PATH = os.path.join(CURRENT_DIR_PATH, '..', 'keys.json')
DATASET_PATH = os.path.join(CURRENT_DIR_PATH, '..', '..', '..', 'Dataset')
DATASETS_HF = ["SALT-NLP/Design2Code-hf", "xcodemind/webcode2m"]


async def login_hugging_face():
    with open(KEYS_PATH) as f:
        huggingface_token = json.load(f)["huggingface"]["reader_token"]

    login(huggingface_token)


async def filter_entries(dataset, picks):
    """
        Filters the dataset based on the id
    """
    filtered_entries = []
    # Counter as ID per data entry
    counter = 1

    for data_entry in dataset:
        if counter in picks:
            filtered = {k: data_entry[k] for k in ['image', 'text']}
            # TODO: Fill with accessibility issues
            filtered["accessibility"] = ""
            filtered_entries.append(filtered)

            # break if max picks reached
            if len(filtered_entries) == len(picks):
                break

        counter += 1

    return Dataset.from_list(filtered_entries)


async def create_new_dataset(hf_dataset_name=None):
    # cherry-picks 
    # Design2Code - amount picked: 28
    picks_design2code = [ 2, 3, 5, 6, 14, 18, 23, 28, 32, 34, 38, 48, 51, 58, 77, 81, 111, 116, 120, 125, 129, 136, 145, 147, 158, 164, 169, 176 ]
    # WebCode2M - amount picked: 25
    picks_webcode2m = [ 16, 22, 34, 37, 39, 44, 47, 63, 66, 67, 69, 74, 81, 99, 123, 132, 143, 154, 161, 182, 191, 324, 348, 428, 435 ]

    # login
    await login_hugging_face()

    # dataset = load_dataset(dataset_name, split="train")
    design2code = load_dataset(DATASETS_HF[0], split="train", streaming=True)
    webcode2m = load_dataset(DATASETS_HF[1], split="train", streaming=True)

    # Filter entries
    design2code_filtered = await filter_entries(design2code, picks_design2code)
    webcode2m_filtered = await filter_entries(webcode2m, picks_webcode2m)

    # Concatenate datasets
    dataset_final = concatenate_datasets([design2code_filtered, webcode2m_filtered])

    # Save dataset
    if hf_dataset_name:
        # upload dataset to huggingface
        await upload_dataset_hf(dataset_final, hf_dataset_name)
    else:
        dataset_final.save_to_disk(DATASET_PATH)

    print("Dataset stored.")
    return dataset_final


async def upload_dataset_hf(dataset, hf_dataset_name="marcolutz/Image2Code"):
    with open(KEYS_PATH) as f:
        hf_writer_token = json.load(f)["huggingface"]["writer_token"]

    dataset.push_to_hub(
        repo_id=hf_dataset_name,
        token=hf_writer_token,
        private=True,
        embed_external_files=True
    )

    print("Upload done ...")


async def get_dataset_hf(hf_dataset_name="marcolutz/Image2Code"):
    with open(KEYS_PATH) as f:
        hf_token = json.load(f)["huggingface"]["reader_token"]

    dataset = load_dataset(
        path=hf_dataset_name, 
        token=hf_token,
        split="train",
    )

    return dataset

# Updates dataset with accessibility issues
async def update_dataset_hf_accessibility():
    dataset = get_dataset_hf("marcolutz/Image2Code")

    # TODO: Add accessibility issues
    print(dataset)


# Store dataset in directory
def store_dataset_in_dir(dataset, path):
    input_dir = os.path.join(path, "input")
    html_dir = os.path.join(input_dir, "html")
    image_dir = os.path.join(input_dir, "images")

    counter = 1
    
    for data_entry in dataset:
        image = data_entry["image"]
        text = data_entry["text"]

        # Save image in imaage_dir
        image.save(os.path.join(image_dir, f"{counter}.png"))

        # Save html
        with open(os.path.join(html_dir, f"{counter}.html"), "w") as f:
            f.write(text)
        
        counter += 1
    

    
# Tests
# asyncio.run(update_accessibility_dataset())
