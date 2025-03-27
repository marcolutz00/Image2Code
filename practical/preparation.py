import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.Utils import huggingFace

'''
This file is used to prepare all necessary data for the pipeline.
Especially, downloading and storing the dataset


Important: 
SALt-NLP/Design2Code-hf -> 77.6 MB -> https://huggingface.co/datasets/SALT-NLP/Design2Code-hf
xcodemind/webcode2m -> 1.1 TB -> https://huggingface.co/datasets/xcodemind/webcode2m 
'''


async def main():
    dataset = await huggingFace.create_new_dataset()

if __name__ == "__main__":
    asyncio.run(main())