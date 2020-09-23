# %%
from nilearn import plotting
import os
import numpy as np
import nibabel as nib

img = nib.load('/Volumes/Untitled/LARC_T2_cleaned_nii/LARC-RRP-001/MRS1/mask_GTV.nii')

dim = img.header.get_data_shape() #dimension shape of nifty image
print(dim)

#path = '/Volumes/Untitled/LARC_T2_cleaned_nii/LARC-RRP-001/MRS1/image.nii'
#plotting.plot_anat(path)
# %%
