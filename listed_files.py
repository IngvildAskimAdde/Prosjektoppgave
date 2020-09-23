import os
from pathlib import Path

src = Path('/Volumes/Untitled/LARC_T2_cleaned')
identifyer = 'MRS1'

for folder_path in src.glob('*/MRS1'):
    print(folder_path)