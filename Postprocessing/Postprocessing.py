# %% Find seeds
import os
import random
import ast

import pandas as pd
import SimpleITK as sitk

import Preprocessing.ImageViewer as iv

def get_seed_from_ground_truth_per_slice(mask_gt):
    """
    return a single (random) seed for each slice with tumour
    """
    seed_list = []
    for z in range(mask_gt.GetDepth()):
        valid_positions = []
        for x in range(mask_gt.GetWidth()):
            for y in range(mask_gt.GetHeight()):
                if mask_gt[x, y, z] == 1:
                    valid_positions.append((x, y, z))
        if valid_positions:
            seed_list.append(random.sample(valid_positions, 1)[0])
    return seed_list

def show_seeds_montage(mask_gt, seed_list):
    seed_mask = sitk.Image(mask_gt.GetSize(), sitk.sitkUInt8)
    for seed in seed_list:
        seed_mask[seed]=1

    v = iv.Viewer(view_mode='2', mask_to_show= ['a'])
    v.set_image(mask_gt)
    v.set_mask(seed_mask, 'seeds')
    v.show()


def get_seeds_all_patients(image_folder, patient_prefix,
                           csv_file_name='seeds_postprocessing.csv'):
    """
    Uses get_seed_from_ground_truth_per_slice to create a csv that contains
    the seeds for every patient in image_folder, which is saved as
    csv_file_name in image folder.
    """
    patient_list = [i for i in os.listdir(image_folder) if i.startswith(patient_prefix)]
    seed_list = []
    for patient in patient_list:
        gt_mask_sitk = sitk.ReadImage(
            os.path.join(image_folder, patient, 'Mask.nii'))
        seed_list.append(
            str(get_seed_from_ground_truth_per_slice(gt_mask_sitk)))

    df = pd.DataFrame(seed_list, columns=['seeds'], index=patient_list)
    df.index.name = 'patient'
    df.to_csv(os.path.join(image_folder, csv_file_name))


def read_seeds_from_csv(data_folder, csv_file_name):
    """
    Reads the information about the seeds from the csv file.
    Returns a pd.Series, where the patient names can be used as index
    (for example seeds['Oxytarget_103'])
    """
    path_to_csv_file = os.path.join(data_folder, csv_file_name)
    seeds = pd.read_csv(path_to_csv_file, index_col='patient',
                           converters={'seeds': ast.literal_eval}, squeeze=True)
    return seeds

def postprocess_mask(mask_sitk, seed_list):
    """
    Smooth initial prediction using a median filter
    Use wathershed to seperate connected regions
    Use one seed per slice to find out a 'valid region' Use this region to
    restrict the prediction.
    http://simpleitk.github.io/SimpleITK-Notebooks/32_Watersheds_Segmentation.html
    seed_list: one random seed per slice
    mask_sitk: prediction read with sitk.ReadImage
    """
    median_filter = sitk.BinaryMedianImageFilter()
    median_filter.SetBackgroundValue(1)
    median_filter.SetForegroundValue(0)
    median_filter.SetRadius([1,1,1])
    smoothed_mask =  median_filter.Execute(mask_sitk>0)

    distance_image = sitk.SignedMaurerDistanceMap(smoothed_mask,
                                                  insideIsPositive=False,
                                                  squaredDistance=False,
                                                  useImageSpacing=True)
    label_mask  = sitk.MorphologicalWatershed(distance_image,
                                              markWatershedLine=False,
                                              level=1)

    valid_labels = [label_mask[seed] for seed in seed_list if smoothed_mask[seed]==1]

    pp_mask = sitk.Image(mask_sitk.GetSize(), sitk.sitkUInt8)
    if not valid_labels:
        print('No valid labels found - return empty mask')
    else:
        for label in set(valid_labels):
            pp_mask = sitk.Or(label_mask==label, pp_mask)
        pp_mask = sitk.And(smoothed_mask, pp_mask)

    return pp_mask