from nilearn import plotting
import os
import numpy as np
import nibabel as nib
from pathlib import Path
import pandas as pd
from collections import Counter
from itertools import chain

#Iterate through all the folders and get the full path of each .nii file
src_path = Path('/Volumes/Untitled/LARC_T2_cleaned_nii')

identifyer = '**/*.nii'
src_list = []

for folder_path in src_path.glob(identifyer):
    src_list.append(folder_path)

#Extract the dimensions of the images from the header information
dim_list = []

for i in range(len(src_list)): 
    img = nib.load(src_list[i])
    dim = img.header.get_data_shape() #Gives the dimension of the image
    dim_list.append([dim])

dim_overview = Counter(chain(*dim_list)) #A dictionary with all the different dimensions and the number of images with a given dimension

#Creating a DataFrame to represent the dimension data
df = pd.DataFrame.from_dict(dim_overview, orient='index')
df_new = df.rename(columns={' ':'Image', 0:'Number of images'})
print(df_new)