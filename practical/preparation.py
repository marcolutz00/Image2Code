import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.Utils import huggingFace

'''
This file is used to prepare all necessary data for the pipeline.
Especially, downloading and storing the dataset
'''

async def main():
    await huggingFace.load_and_store_dataset()

if __name__ == "__main__":
    asyncio.run(main())