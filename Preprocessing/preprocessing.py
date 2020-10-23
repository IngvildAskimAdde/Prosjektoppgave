# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 13:18:08 2019

@author: franzihk
"""
import os

import numpy as np
import SimpleITK as sitk

import ImageViewer as iv

class Register(object):
    """
    Image Registration using simple Elastix

    """
    def __init__(self):
        self.elastix = sitk.ElastixImageFilter()
        self.is_groupwise = False

    def set_fixed_image(self, fixed_image):
        """
        Set the fixed image (sitk image)
        (The moving image is registered towards the fixed image)

        """
        self.elastix.SetFixedImage(fixed_image)

    def set_moving_image(self, moving_image):
        """
        Set the moving image (as sitk image)
        (The moving image is registered towards the fixed image)

        """
        self.elastix.SetMovingImage(moving_image)

    def set_registration_masks(self, fixed_mask, moving_mask=None):
        """
        Use masks to focus the registration on a roi and/or avoid problems
        from artifical edges

        Details about masks: Elastix manual, chapter 5.4
        '... a fixed mask is suffficient to focus the registration on a ROI...'
        in case you a using a mask to prevent bad karma from an arificial edge,
        you also need to set the parameter (ErodeMask "true") ...'
              -> see :meth:`get_parameters`

        :param fixed_mask: sitk image (binary mask)
        :param moving_mask: (optional) sitk image (binary mask)

        """
        self.elastix.SetFixedMask(sitk.Cast(fixed_mask, sitk.sitkUInt8))

        if moving_mask:
            self.elastix.SetMovingMask(sitk.Cast(moving_mask, sitk.sitkUInt8))

    def set_registration_parameters(self, path_to_folder_parameterfiles):
        """
        parameter files have to be in one folder and named as
        <number>_<Description>.txt

        """
        if not os.path.isdir(path_to_folder_parameterfiles):
            raise IOError('{} is not a valid folder'.format(
                    path_to_folder_parameterfiles))
        file_list = [file for file in os.listdir(path_to_folder_parameterfiles)
                     if file.endswith('.txt') and file.split('_')[0].isdigit()]
        if not file_list:
            raise IOError('The folder contains no parameter files that are'\
                          'named in the correct format ({})'.format(
                                              path_to_folder_parameterfiles))

        parameter_map_vector = sitk.VectorOfParameterMap()
        for file in sorted(file_list):
            parameter_map_vector.append(sitk.ReadParameterFile(
                os.path.join(path_to_folder_parameterfiles, file)))
        self.elastix.SetParameterMap(parameter_map_vector)

    def set_registration_parameter_single_file(self, path_to_parameter_file):
        """
        Use a single parameter file to set the registration parameters

        """
        if not os.path.isfile(path_to_parameter_file):
            raise IOError('The file does not exist')

        self.elastix.SetParameterMap(sitk.ReadParameterFile(path_to_parameter_file))

    def execute(self):

        # self.elastix.LogToConsoleOn()
        # self.elastix.LogToFileOn()
        self.elastix.Execute()

    def get_result_image(self):
        """
        returns the result image either as a single sitk image or
        (in case of a groupwise registration) as a list of sitk images

        """
        if not self.is_groupwise:
            return self.elastix.GetResultImage()
        else:
            return self.image4d_to_imagelist(self.elastix.GetResultImage())

    def transform_image(self, image_to_transform):
        """
        Transform another image by using the resutling deformation vector field
        of the registration.

        """
        trafo = sitk.TransformixImageFilter()
        trafo.SetTransformParameterMap(self.elastix.GetTransformParameterMap())
        trafo.SetMovingImage(image_to_transform)
        return trafo.Execute()

    def transform_mask(self, mask_to_transform):
        """
        Transform a mask with the deformation vector field that was found in
        the registration.
        """
        mask_to_transform = sitk.Cast(mask_to_transform>0, sitk.sitkFloat64)
        deformed_mask = self.transform_image(mask) >= 0.5
        return deformed_mask

    def show(self, **kwargs):
        if self.is_groupwise:
            print('group')
            v = self.show_group()
        else:
            print('single')
            v = self.show_single(**kwargs)
        return v

    def show_single(self, mask_on_fixed_image=None, mask_on_moving_image=None):
        """
        show input and result of the registration

        :param mask_on_fixed_image: mask that is defined on the fixed image
        :param mask_on_moving_image: mask that is defined on the moving image
        """
        v = {}
        # show input
        for idx, item in enumerate(['Fixed', 'Moving']):
            v[item] = iv.Viewer()
            img =  getattr(self.elastix, 'Get'+item+'Image')()
            v[item].set_image(img if isinstance(img, sitk.Image) else img[0],
                              label = item+' image')
            try:
                v[item].set_mask(getattr(self.elastix, 'Get'+item+'Mask')()[0],
                                'ROI Mask', 'teal')
            except:
                print('No mask for ', item )
                pass #no mask set
            if item == 'Moving' and mask_on_moving_image:
                v[item].set_mask(mask_on_moving_image, 'mask', color_name='navy')
            if item == 'Fixed' and mask_on_fixed_image:
                v[item].set_mask(mask_on_fixed_image, 'mask', color_name='orange')
            v[item].show()
            v[item].toggle_legend()

        # show result
        fixed_img = self.elastix.GetFixedImage()[0]
        def_moving_img = sitk.Cast(self.elastix.GetResultImage(),
                                   fixed_img.GetPixelID())
        v['Result'] = iv.Viewer()
        v['Result'].set_image(fixed_img, label='Fixed image')
        v['Result'].set_image(def_moving_img, label='Deformed moving image')
        v['Result'].set_image(iv.checkerboard(fixed_img, def_moving_img),
                              label='checkerboard')
        v['Result'].set_image(iv.imfuse(fixed_img, def_moving_img),
                              label='imfuse')
        if mask_on_fixed_image:
            v['Result'].set_mask(mask_on_fixed_image, 'mask on fixed image', color_name='orange')
        if mask_on_moving_image:
            v['Result'].set_mask(self.transform_mask(mask_on_moving_image)>0,
                                'mask on moving image (deformed)', color_name='navy')
        v['Result'].show()
        v['Result'].toggle_legend()

        return v

    def show_group(self):
        """
        Visualize the groupwise registration
        - show the input images as overlay in different color channels
        - show the output image in the same way

        """
        v = iv.Viewer()
        img = iv.imfuse_stack(self.image4d_to_imagelist(
                                self.elastix.GetMovingImage()[0]))
        v.set_image(iv.imfuse_stack(self.image4d_to_imagelist(
                                self.elastix.GetMovingImage()[0])),
                    label='Input')
        v.set_image(iv.imfuse_stack(self.get_result_image()),
                    label='Result')
        v.show()
        v.toggle_legend()
        return v

    def set_image_group(self, image_list_sitk, use_mask_for_black_boarders=False):
        """
        Set the input images for a groupwise registration

        (Only moving image is used, fixed image is only needed as dummy input)

        """
        self.is_groupwise = True
        combined_image = sitk.JoinSeries(sitk.VectorOfImage(image_list_sitk))

        self.elastix.SetFixedImage(combined_image)
        self.elastix.SetMovingImage(combined_image)

        if use_mask_for_black_boarders:
            combined_mask = sitk.JoinSeries(sitk.VectorOfImage(
                                            [m!=0 for m in image_list_sitk]))

            self.elastix.SetFixedMask(combined_mask)
            self.elastix.SetMovingMask(combined_mask)

    @staticmethod
    def image4d_to_imagelist(image4d):
        size_4d = list(image4d.GetSize())

        extract = sitk.ExtractImageFilter()
        extract.SetSize(size_4d[0:3] + [0])

        image_list = []
        for idx in range(size_4d[3]):
            extract.SetIndex([0,0,0,idx])
            image_list.append(extract.Execute(image4d))
        return image_list

    def write_transformation_parameter(self, path_to_dest_folder, file_prefix):
        """
            Write the 'found' transformation parameters to disk, so that they
            can be checked later if neccessary

            """
        parameter_maps = self.elastix.GetTransformParameterMap()
        parameter_maps = [parameter_maps[idx]
                          for idx in range(len(parameter_maps))]

        for idx, pmap in enumerate(parameter_maps):
            sitk.WriteParameterFile(pmap,
                                    os.path.join(path_to_dest_folder,
                                                 '{}_{}.txt'.format(file_prefix, idx)))


    def apply_inverse_euler_to_mask(self, mask, transformation_parameter_file=None):

        if transformation_parameter_file:
            transformation = sitk.ReadParameterFile(transformation_parameter_file)
        else:
            transformation = self.elastix.GetTransformParameterMap()

        if not transformation['Transform'][0]=='EulerTransform':
            raise Exception('Transfomation is not an Euler transformation')

        mu_vector = [float(i) for i in transformation['TransformParameters']]
        center_of_roataion = [float(i) for i in transformation['CenterOfRotationPoint']]

        euler_trafo = sitk.Euler3DTransform()
        euler_trafo.SetCenter(center_of_roataion)
        euler_trafo.SetRotation(*mu_vector[0:3])
        euler_trafo.SetTranslation(mu_vector[3:6])

        inverse_euler = euler_trafo.GetInverse()

        resampler = Resample_And_Crop()
        resampler.set_transform(inverse_euler)
        resampler.set_roi(self.elastix.GetMovingImage()[0])

        return resampler.process_mask(mask)


# def printParameterMap(inp): ##TODO check if it is needed ore usefull
#     singleMap = False
#     # extract the parameter map vector
#     try:
#         # inp is an elastix image filter
#         mapVec = inp.GetParameterMap()
#     except AttributeError:
#         try:
#             # ino is an transformix image filter
#             mapVec = inp.GetTransformParameterMap()
#         except:
#             # input is the parameter map itself
#             singleMap = True and (len(inp)==1)
#             print(singleMap)
#             mapVec = inp
#
#     if singleMap:
#         for key in inp:
#             print('\t', key, ':', inp[key])
#     else:
#         # find how many parameter maps there are
#         n = len(mapVec)
#         for idx in range(n):
#             print('\nParameterMap', idx, ':')
#             for key in mapVec[idx]:
#                 print('\t', key, ':', mapVec[idx][key])
# # end printParameterMap

class Resample_And_Crop(object):
    """
    Use to crop an image to a region of interest
    and or resample the image to a different spacing

    """
    default_pixel_value = 0
    def __init__(self):
        self.FOV = None
        self.new_spacing = None
        self.reference_image = None
        self.transformation = None

        self.update_ref_image = True

        self.interpolator = sitk.sitkBSplineResamplerOrder3
    def set_roi(self, roi_image):
        """
        define the FOV as an sitk image that has the desired FOV.

        Use Image.get_roi_box_cropped() to get the FOV as box around masks with
        the desired margin
        """
        self.FOV =  roi_image
        self.update_ref_image = True

    def set_spacing(self, new_spacing):
        """
        set the spacing of the resulting image as [sx, sy, sz] in mm
        (sz is the slice direction).

        """
        self.new_spacing = new_spacing
        self.update_ref_image = True

    def use_nearest_neighbor_interpolation(self):
        """
        Use nearest sitkNearestNeighbor instead of 3rd order bspline

        """
        self.interpolator = sitk.sitkNearestNeighbor

    def set_roi_as_box_around_mask(self, mask_sitk, margin_in_mm=[0,0,0]):
        """

        mask_sitk: sitk image
        (can be an individual doctor or the union, intersection, ...)

        """
        mask_npa = sitk.GetArrayFromImage(mask_sitk)
        margin_in_voxel = np.ceil(np.array(margin_in_mm)
                                    / np.array(mask_sitk.GetSpacing())
                                 )[::-1] # match dim order (sitk and np)

        roi_mask_extent = np.zeros((3,2), dtype=int)
        index_combinations = np.indices(mask_npa.shape)
        for dim in range(mask_sitk.GetDimension()):
            idx_mask = index_combinations[dim, mask_npa>0]
            roi_mask_extent[dim, :] = [max(idx_mask.min() - margin_in_voxel[dim],
                                           0),
                                       min(idx_mask.max() + margin_in_voxel[dim],
                                           mask_npa.shape[dim] - 1)]

        # roi_mask_extent[:, 1] += 1  # correct to use it as index for slicing

        roi_mask = mask_sitk[roi_mask_extent[2][0]:roi_mask_extent[2][1]+1,
                             roi_mask_extent[1][0]:roi_mask_extent[1][1]+1,
                             roi_mask_extent[0][0]:roi_mask_extent[0][1]+1]
        self.set_roi(roi_mask)

    def process_image(self, image):
        if self.update_ref_image:
            self.__calculate_reference_image(image)

        resampler = sitk.ResampleImageFilter()
        resampler.SetDefaultPixelValue(self.default_pixel_value)
        resampler.SetInterpolator(self.interpolator)
        resampler.SetReferenceImage(self.reference_image)
        if self.transformation:
            resampler.SetTransform(self.transformation)

        return resampler.Execute(image)

    def process_mask(self, mask):
        mask = sitk.Cast(mask>0, sitk.sitkFloat64)
        resampled_mask = self.process_image(mask)
        resampled_mask = resampled_mask>=0.5
        return resampled_mask

        # if self.update_ref_image:
        #     self.__calculate_reference_image(mask)
        # resampler.SetDefaultPixelValue(self.default_pixel_value)
        # resampler.SetInterpolator(sitk.sitkNearestNeighbor)
        # resampler.SetReferenceImage(self.reference_image)
        # return resampler.Execute(mask)
        # return mask

    def __calculate_reference_image(self, input_object):
        if self.FOV:
            ref = self.FOV
        else:
            ref = input_object

        if self.new_spacing:
            old_size = np.array(ref.GetSize())
            old_spacing = np.array(ref.GetSpacing())
            new_size = np.floor(old_spacing / self.new_spacing * old_size)
            self.reference_image = sitk.Image([int(n) for n in new_size],
                                               sitk.sitkUInt16)
            self.reference_image.SetSpacing(self.new_spacing)
            self.reference_image.SetDirection(ref.GetDirection())
            self.reference_image.SetOrigin(ref.GetOrigin())
        else:
            self.reference_image = ref

        self.update_ref_image = False




    def set_transform(self, transformation):
        self.transformation = transformation
#%%
