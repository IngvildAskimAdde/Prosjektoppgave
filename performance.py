
"""
Functions to analyse results
Note:
when you load a mask.nii file (both ground truth and predicted mask)
use
sitk.ReadImage(path_to_file)>0
in order to get a binary image!
"""
import os
import numpy as np
import SimpleITK as sitk
import pandas as pd
import get_data as gd

def calculate_dice(mask_a, mask_b):
    """
    Calculate DICE score for two binary masks (=sitk images)
    """
    npa1 = sitk.GetArrayFromImage(mask_a)
    npa2 = sitk.GetArrayFromImage(mask_b)

    dice = 2*np.count_nonzero(npa1 & npa2) / (np.count_nonzero(npa1) + np.count_nonzero(npa2))
    return dice

def calculate_msd(mask_a, mask_b):
    """
    Calulate mean average surface distance between mask a and b
    """
    mask_b.CopyInformation(mask_a)
    # masks need to occupy exactly the same space and no spacial information is
    # saved in the matlab script

    contour_list =[sitk.LabelContour(m) for m in [mask_a, mask_b]]

    n_voxel = []
    mean_val = []

    for a, b in [(0,1), (1,0)]:
        distance_map = sitk.Abs(sitk.SignedMaurerDistanceMap(contour_list[a],
                                                         squaredDistance=False,
                                                         useImageSpacing=True))
        stat_intensity_filter = sitk.LabelIntensityStatisticsImageFilter()
        stat_intensity_filter.Execute(contour_list[b], distance_map)
        n_voxel.append(stat_intensity_filter.GetNumberOfPixels(1))
        mean_val.append(stat_intensity_filter.GetMean(1))

    # combine the two values to get 'symmetric' values
    MSD=(n_voxel[0]*mean_val[0]+n_voxel[1]*mean_val[1])/(n_voxel[0]+n_voxel[1])

    return MSD

def mean_columns(dataframe):
    dict = {}
    for column in dataframe:
        dict[column] = [dataframe[column].mean()]
    return dict


result_folder = '/Volumes/Untitled/Results/'

resultPaths = {}


for experiment in os.listdir(result_folder):
    experimentPath = os.path.join(result_folder, experiment)
    if os.path.isdir(experimentPath):
        for patient in os.listdir(experimentPath):
            patientResultPath = os.path.join(experimentPath, patient)
            if experiment in resultPaths:
                resultPaths[experiment].append(patientResultPath)
            else:
                resultPaths[experiment] = [patientResultPath]

patientsPaths, patientsNames, patientsPaths_image, patientPaths_groundTruth = gd.get_paths('/Volumes/Untitled/LARC_T2_preprocessed', image_prefix='image', mask_suffix='label.nii')
patientPaths_groundTruth.insert(0, patientPaths_groundTruth.pop(len(patientPaths_groundTruth) - 1))

dice = {}
msd = {}

for key in resultPaths:
    for i in range(len(patientPaths_groundTruth)):
        mask_pred = sitk.ReadImage(resultPaths[key][i]) > 0
        mask_truth = sitk.ReadImage(patientPaths_groundTruth[i]) > 0
        dice_score = calculate_dice(mask_pred, mask_truth)
        msd_score = calculate_msd(mask_pred, mask_truth)
        if key in dice:
            dice[key].append(dice_score)
            msd[key].append(msd_score)
        else:
            dice[key] = [dice_score]
            msd[key] = [msd_score]

df_dice = pd.DataFrame(dice)
df_msd = pd.DataFrame(msd)
mean_dice = mean_columns(df_dice)
mean_msd = mean_columns(df_msd)

df_dice_mean = pd.DataFrame(mean_dice)
df_msd_mean = pd.DataFrame(mean_msd)

boxplot_dice = df_dice_mean.boxplot()
boxplot_msd = df_msd_mean.boxplot()