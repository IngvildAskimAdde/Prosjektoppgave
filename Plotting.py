"""
@author: IngvildAskimAdde
"""

import get_data
from Preprocessing import ImageViewer as iv
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt

main_folder = r'/Volumes/Untitled/LARC_T2_preprocessed'
image_prefix = 'image'
mask_suffix = 'label.nii'
result_suffix='.nii'


#Creates an image object from a 1D array
def create_image_from_array(array, imsize):
    im = np.reshape(array,imsize)
    im = im.astype(int)
    im = sitk.GetImageFromArray(im)
    return im


def show_image(image, mask, image_prefix, mask_suffix):
    """
    Uses the ImageViewer to show the image
    """
    v = iv.Viewer(view_mode='2', mask_to_show=['a'])
    v.set_image(image, label=image_prefix)
    v.set_mask(mask, label=mask_suffix)
    v.show()

#Show image with matplotlib
def view_png(path):
    image = plt.imread(path)
    plt.figure()
    plt.imshow(image)
    plt.axis('off')



