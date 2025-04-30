from datasets import load_dataset, load_from_disk, concatenate_datasets, Dataset
from huggingface_hub import login
import os
import json
import re


CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
KEYS_PATH = os.path.join(CURRENT_DIR_PATH, '..', 'keys.json')
DATA_INPUT_PATH = os.path.join(CURRENT_DIR_PATH, '..', 'Data', 'Input')
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
            filtered = {
                'image': data_entry['image'],
                'text': data_entry['text']
            }
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

    # add id
    id_counter = 0
    for data_entry in dataset_final:
        data_entry["id"] = id_counter
        id_counter += 1

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


async def get_dataset_hf(hf_dataset_name="marcolutz/Image2Code",):
    with open(KEYS_PATH) as f:
        hf_token = json.load(f)["huggingface"]["reader_token"]

    dataset = load_dataset(
        path=hf_dataset_name, 
        token=hf_token,
        split="train",
    )

    return dataset

async def get_dataset_hf_locally(hf_dataset_path=DATASET_PATH):

    dataset = load_dataset(
        path=hf_dataset_path,
        split="train",
    )

    return dataset


# Citation: https://stackoverflow.com/questions/4813061/non-alphanumeric-list-order-from-os-listdir
def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)


'''
    Updates dataset according to column
    TODO: image
'''
async def update_dataset_hf(hf_dataset_name, column):
    if column == "accessibility":
        accessibility_issues_json_path = os.path.join(DATA_INPUT_PATH, 'json', 'manual')
        return await update_dataset_hf_column(hf_dataset_name, column, accessibility_issues_json_path)
    elif column == "text":
        html_path = os.path.join(DATA_INPUT_PATH, 'html')
        return await update_dataset_hf_column(hf_dataset_name, column, html_path)
    elif column == "image":
        images_path = os.path.join(DATA_INPUT_PATH, 'images')
        pass
    else:
        raise ValueError("There are only 3 columns in the dataset")
    
# Updates dataset Accessibility - Issues will be stored as Strings
async def update_dataset_hf_column(hf_dataset_name, column_name, data_path):
    dataset = await get_dataset_hf(hf_dataset_name)

    # If column already in dataset, then delete
    if column_name in dataset.column_names:
        dataset = dataset.remove_columns(column_name)

    # Add accessibility issues
    length_dataset = len(dataset)

    updated_data_string = []

    name_files_sorted = sorted_alphanumeric(os.listdir(data_path))

    for file in name_files_sorted:
        file_path = os.path.join(data_path, file)
        if file.startswith(".") or os.path.isdir(file_path):
            continue
        if column_name == 'accessibility':
            with open(file_path, 'r') as f:
                accessibility_issue_json = json.load(f)
                # Make sure that they always have the same structure
            accessibility_issue_string = json.dumps(accessibility_issue_json)
            updated_data_string.append(accessibility_issue_string)
        elif column_name == 'text':
            with open(file_path, "r", encoding='utf-8') as f:
                html = f.read()
            updated_data_string.append(html)

    
    # Check if length is the same
    assert(length_dataset == len(updated_data_string))

    dataset = dataset.add_column(column_name, updated_data_string)

    await upload_dataset_hf(dataset, hf_dataset_name)

    print(f"Dataset updated with {column_name} issues...")

    return dataset


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
        with open(os.path.join(html_dir, f"{counter}.html"), "w", encoding='utf-8') as f:
            f.write(text)
        
        counter += 1
    

    
# Tests
# asyncio.run(update_dataset_hf_accessibility())
