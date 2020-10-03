import os
from pathlib import Path


src_path = Path('/Volumes/Untitled/LARC_T2_cleaned')
dst_path = Path('/Volumes/Untitled/LARC_T2_cleaned_nii')

identifyer = '*/MRS1'
src_list = []
dst_list = []

for folder_path in src_path.glob(identifyer):
    src_list.append(folder_path / 'DICOM')

for folder_path in dst_path.glob(identifyer):
    dst_list.append(folder_path)

for i in range(len(src_list)):
    print(src_list[i])
    print(dst_list[i])
