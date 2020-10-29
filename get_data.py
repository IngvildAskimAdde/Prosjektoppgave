from nilearn import plotting
import os
import numpy as np
import nibabel as nib
from pathlib import Path
import pandas as pd
from collections import Counter
from itertools import chain
import SimpleITK as sitk
import matplotlib.pyplot as plt

#Iterate through all the folders and get the full path of each .nii file
#main_folder = Path('/Volumes/Untitled/LARC_T2_preprocessed')
main_folder = '/Volumes/Untitled/LARC_T2_preprocessed'
identifyer_image = '**/*image.nii'
identifyer_mask = '**/*label.nii'

image_prefix = 'image'
mask_suffix = 'label.nii'

def get_paths(main_folder, image_prefix, mask_suffix):

    patientsPaths = []
    patientsPaths_image = []
    patientsPaths_groundTruth = []
    patientsNames = []

    for entry in os.listdir(main_folder):
        patientsPath = os.path.join(main_folder, entry)
        if os.path.isdir(patientsPath):
            patientsPaths.append(patientsPath)
            patientsNames.append(entry)

        if main_folder.endswith('preprocessed'):

            for i in os.listdir(patientsPath):
                if i.startswith(image_prefix):
                    patientsPaths_image.append(os.path.join(patientsPath,i))
                else:
                    patientsPaths_groundTruth.append(os.path.join(patientsPath,i))

        else:
            patientsPath = patientsPath + '/MRS1'
            for i in os.listdir(patientsPath):
                if i.startswith(image_prefix):
                    patientsPaths_image.append(os.path.join(patientsPath,i))
                elif i.endswith(mask_suffix):
                    patientsPaths_groundTruth.append(os.path.join(patientsPath,i))

    if main_folder.endswith('preprocessed'):
        # Fixing bug in the label string of patient 001
        patientsPaths_groundTruth[len(patientsPaths_groundTruth) - 1].replace('._1', '1')
        patientsPaths_groundTruth.remove(patientsPaths_groundTruth[len(patientsPaths_groundTruth) - 1])

    return patientsPaths, patientsNames, patientsPaths_image, patientsPaths_groundTruth

patientsPaths, patientsNames, patientsPaths_image, patientPaths_groundTruth = get_paths(main_folder, image_prefix, mask_suffix)


def data_dimensions(src_path, identifyer):
    """
    A function which displays the image dimensions and voxel dimensions in Panda dataframes.
     - src_path: path to patient folder
     - identifyer: a string which identify the file which will be processed
    """

    src_list = []

    for folder_path in src_path.glob(identifyer):
        src_list.append(folder_path)

    if identifyer == 'label.nii':
        src_list[len(src_list) - 1].replace('._1', '1')
        src_list.remove(src_list[len(src_list) - 1])

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

    return src_list, df_dim, df_vox

#src_list_img, df_dim_img, df_vox_img = data_dimensions(main_folder, identifyer_image)
#src_list_mask, df_dim_mask, df_vox_mask = data_dimensions(main_folder, identifyer_mask)




def get_array(path):
    img = sitk.ReadImage(path)
    array = sitk.GetArrayFromImage(img)
    imsize = np.shape(array)
    array = array.flatten()
    return array, imsize


def data_balance(paths):

    tumor_voxels = []
    non_tumor_voxels = []

    for i in paths:
        print(i)
        array, imsize = get_array(i)
        tumor_voxels.append(np.count_nonzero(array==1))
        non_tumor_voxels.append(np.count_nonzero(array==0))

    total_voxels = np.sum(tumor_voxels) + np.sum(non_tumor_voxels)
    tumor_percentage = (np.sum(tumor_voxels)/total_voxels)*100
    non_tumor_percentage = (np.sum(non_tumor_voxels)/total_voxels)*100

    return tumor_percentage, non_tumor_percentage

#tumor, non_tumor = data_balance(patientPaths_groundTruth)

img_array, imsize = get_array('/Volumes/Untitled/LARC_T2_preprocessed/LARC-RRP-003/image.nii')

#Creates an image object from a 1D array
def create_image_from_array(array, imsize):
    im = np.reshape(array,imsize)
    im = im.astype(int)
    im = sitk.GetImageFromArray(im)
    return im