import os

import numpy as np
import SimpleITK as sitk
import pydicom
from PIL import Image as pil_Image
from PIL import ImageDraw as pil_ImageDraw


class DICOM_Folder_Converter():
    """
    Class to load a folder with a 3d dicom image and an rt struct file into
    sitk images and gives the option to save them as nifti files.
    Works with images anomyzed with DicomCleaner.
    NOTE: Currently not implemented for 4d images (as for example DW images with
    several b values)
    """
    def __init__(self, path_to_folder):
        self.folder = path_to_folder
        self.image_dcm_file_list = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(
            path_to_folder)
        self.rtstruct_dcm_file = self.__identify_rt_struct_file__()

        self.image = None # sitk image
        self.masks = None # dict with mask_names as key with sitk images as items

    def load_image(self):
        """
        Load the dicom fiels into an sitk image
        """
        dcm_reader = sitk.ImageSeriesReader()
        dcm_reader.SetFileNames(self.image_dcm_file_list)
        self.image = dcm_reader.Execute()


    def load_masks(self):
        """
        Load the mask(s) from the rt struct file and store them into a dict
        where the key is the contour name and the contour is stored as binary
        mask as an sitk image
        """
        if not self.rtstruct_dcm_file:
            print('No structure to load')
            return

        if not self.image:
            print('Need to load image first..')
            self.load_image()

        rtstruct_data = pydicom.dcmread(self.rtstruct_dcm_file)
        contour_data = {item.ROINumber: {'name': item.ROIName,
                                         'mask': sitk.Image(self.image.GetSize(),
                                                            sitk.sitkUInt8)}
                        for item in rtstruct_data.StructureSetROISequence}

        for contour in rtstruct_data.ROIContourSequence:
            roi_number = contour.ReferencedROINumber
            for c_slice in contour.ContourSequence:
                s_idx, s_mask = self.__get_mask_from_points(c_slice.ContourData)
                contour_data[roi_number]['mask'] = sitk.Paste(contour_data[roi_number]['mask'],
                                                              s_mask, s_mask.GetSize(),
                                                              destinationIndex=[0,0,s_idx])
            # Make sure that image and mask match
            contour_data[roi_number]['mask'].CopyInformation(self.image)

        self.masks = {c['name']:c['mask'] for _, c in contour_data.items()}

    def save_image(self, dst, filename='image'):
        """Save the image under the specified destination"""
        sitk.WriteImage(self.image, os.path.join(dst, filename + '.nii'))

    def save_mask(self, dst, filename='mask'):
        """Save the masks in the destination folder"""
        for name, mask in self.masks.items():
            sitk.WriteImage(mask, os.path.join(dst,'{}_{}.nii'
                                                .format(filename, name)))

    def get_image(self):
        return self.image

    def get_masks(self):
        return self.masks

    def __identify_rt_struct_file__(self):
        """
        Identify the rt struct file
        DICOM cleaner changes the file name, so the file is identified as file
        that is not part of the image itself.
        Dicom cleaner also removes the .dcm ending, so this can not be used to
        'filter' for real files.
        Note: currently only implemented for a single rt struct file (or none)
        """
        files_in_folder = os.listdir(self.folder)
        img_files = [os.path.basename(i) for i in self.image_dcm_file_list]
        rt_file = [i for i in files_in_folder if (
            not i in img_files and not i.startswith('.'))]

        if not rt_file:
            print('No structure file found')
            rt_file_name = None
        elif len(rt_file) == 1:
            rt_file_name = os.path.join(self.folder, rt_file[0])
        else:
            raise Exception(
                'More than one other file. This is not implemented')

        return rt_file_name

    def __get_mask_from_points(self, points_list):
        """
        Convert the list of contour points into a binary mask which is stored
        in an sitk image
        """
        # convert list of xyzxyz into list of tubles (xyz)(xzy) and transform
        # from physical point (patient coordinates) to image (pixel) coordinates
        pixel_point = []
        for point in zip(*([iter(points_list)] * 3)):
            pixel_point.append(self.image.TransformPhysicalPointToIndex(point))

        # check that everything is in the same slice
        s = np.unique([p[2] for p in pixel_point])
        if not len(s) == 1:
            raise Exception('Something went wrong.. contour not on same slice')
        s_index = s[0]

        # Convert the contour to a mask
        mask = pil_Image.new(mode='L',
                             size=(self.image.GetWidth(),
                                   self.image.GetHeight()),
                             color=0)
        pil_ImageDraw.Draw(mask).polygon([p[0:2] for p in pixel_point],
                                         outline=1, fill=1)
        mask = sitk.GetImageFromArray(np.array(mask)) > 0
        return int(s_index), sitk.JoinSeries(mask)


def convert_folder_dcm_to_nii(src, dst):
    """
    Converts a folder (src) with a single 3d dicom image and a rt struct file into
    a nifti file for the image (image.nii) and one nifti file for each struchtur
    (mask_<contour name>.nii) which are saved in the destination folder (dst)
    """

    data = DICOM_Folder_Converter(src)
    data.load_image()
    data.load_masks()
    data.save_image(dst)
    data.save_mask(dst)


convert_folder_dcm_to_nii(r'/Volumes/Untitled/LARC_T2_cleaned/LARC-RRP-001/MRS1/DICOM', '/Volumes/Untitled/LARC_T2_cleaned_nii/LARC-RRP-001/MRS1')