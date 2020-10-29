import get_data
from Preprocessing import ImageViewer as iv
import SimpleITK as sitk
import numpy as np

main_folder = r'/Volumes/Untitled/LARC_T2_preprocessed'
image_prefix = 'image'
mask_suffix = 'label.nii'
result_suffix='.nii'

patientsPaths, patientsNames, patientsPaths_image, patientsPaths_groundTruth = get_data.get_paths(main_folder, image_prefix, mask_suffix)


img_array, imsize = get_data.get_array(patientsPaths_image[89])
mask_array, masksize = get_data.get_array(patientsPaths_groundTruth[89])
result_array, resultsize = get_data.get_array('/Volumes/Untitled/Results/ID_0/LARC-RRP-001.nii')
org_array, org_size = get_data.get_array('/Volumes/Untitled/LARC_T2_cleaned_nii/LARC-RRP-001/MRS1/image.nii')
orgmask_array, orgmask_size = get_data.get_array('/Volumes/Untitled/LARC_T2_cleaned_nii/LARC-RRP-001/MRS1/1 RTSTRUCT LARC_MRS1-label.nii')

#Creates an image object from a 1D array
def create_image_from_array(array, imsize):
    im = np.reshape(array,imsize)
    im = im.astype(int)
    im = sitk.GetImageFromArray(im)
    return im

im = create_image_from_array(img_array,imsize)
mask = create_image_from_array(mask_array,masksize)
result = create_image_from_array(result_array,resultsize)
org = create_image_from_array(org_array, org_size)
orgmask = create_image_from_array(orgmask_array, orgmask_size)

def show_image(image, mask, image_prefix, mask_suffix):
    v = iv.Viewer(view_mode='1', mask_to_show=['a'])
    v.set_image(image, label=image_prefix)
    v.set_mask(mask, label=mask_suffix)
    v.show()

#Displays the image and mask in figure
v = iv.Viewer(view_mode='1', mask_to_show=['a'])
v.set_image(im, label=image_prefix)
v.set_mask(mask, label=mask_suffix)
v.show()
