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

identifyer = '**/*image.nii'
src_list = []

for folder_path in src_path.glob(identifyer):
    src_list.append(folder_path)

#Extract the dimensions and the voxel size of the images from the header information
dim_list = []
vox_list = []

for i in range(len(src_list)): 
    img = nib.load(src_list[i])
    dim = img.header.get_data_shape() #Gives the dimension of the image
    vox = img.header.get_zooms() #Gives the voxel size in a image
    dim_list.append([dim])
    vox_list.append([vox])

dim_overview = Counter(chain(*dim_list)) #A dictionary with all the different dimensions and the number of images with a given dimension
vox_overview = Counter(chain(*vox_list)) #A dictionary of voxel sizes

#Creating a DataFrame to represent the dimension data
df_dim = pd.DataFrame.from_dict(dim_overview, orient='index')
df_dim = df_dim.reset_index()
df_dim = df_dim.rename(columns={'index':'Image dimension', 0:'Number of images'})
print(df_dim)

#Creating a DataFrame to represent the voxel data
df_vox = pd.DataFrame.from_dict(vox_overview, orient='index')
df_vox = df_vox.reset_index()
df_vox = df_vox.rename(columns={'index':'Voxel size', 0:'Number of images'})
print(df_vox)


