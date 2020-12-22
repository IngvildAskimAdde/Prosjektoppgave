"""
@author: franzi-ska
"""


import os

import numpy as np
import matplotlib.pyplot as plt
import SimpleITK as sitk
"""
Further ideas for the Viewer:
[ ] be abble to hide / show the title by pressing "t"
[ ] be able to set images and masks from numpy arrays instead of sitk images
"""
class Viewer(object):
    """
    Display images and masks as montage or individual slices.
    The viewer reacts to the keyboard.
    Press  "h" to show a legend with the avaliable hotkeys.
    """
    colors = {
        'red' :     [230, 25, 75],
        'green' :   [60, 180, 75],
        'yellow' :  [255, 225, 25],
        'blue' :    [0, 130, 200],
        'orange' :  [245, 130, 48],
        'purple' :  [145, 30, 180],
        #'cyan' :    [70, 240, 240],
        'cyan': [0, 255, 255],
        'magenta' : [240, 50, 230],
        'lime' :    [210, 245, 60],
        'pink' :    [250, 190, 190],
        'teal' :    [0, 128, 128],
        'lavender': [230, 190, 255],
        'brown' :   [170, 110, 40],
        'beige' :   [255, 250, 200],
        'maroon' :  [128, 0, 0],
        'mint' :    [170, 255, 195],
        'olive' :   [128, 128, 0],
        'apricot' : [255, 215, 180],
        'navy' :    [0, 0, 128],
        'grey' :    [128, 128, 128],
        'white' :   [255, 255, 255],
        'black' :   [0, 0, 0],
        'mediumseagreen' : [60, 179, 113],
        'skyblue' : [135, 206, 235],
            }
    overlay_opacity = 255//2 #  value between 0 and 255
    contour_opacity = 255    #  value between 0 and 255
    line_width_increase = 1 # use 0, 1, 2, ...  to increase the linewidht

    def __init__(self, ax=None, fig=None,  **kwargs):
        """
        Initilize the viewer.
        Initial dispaly options can be provided:
            - view_mode: '1'(3d viewer) or '2' (montage)
            - idx_slice: slice to show in 3d viewer
            - mask_to_show: list with mask_keys ['a', 'b', ...]
            - mask_mode: list with one or both of  '9'(overlay) and '8' (contour)
        """
        """ input data """
        self.image_data = {}
        self.mask_data = {}
        self.extent_single_slice = None
        self.image_n_slice = None # number of slices in the image

        """ display options """
        self.view_mode = kwargs.get('view_mode', '1')
        self.idx_slice = kwargs.get('idx_slice', None)
        self.mask_to_show = kwargs.get('mask_to_show',[])
        self.image_to_show = None
        self.mask_mode = kwargs.get('mask_mode', ['9', '8'])


        if ax:
            """ Use a predefined figure"""
            self.ax= ax
            self.fig = fig
        else:
            """ Prepare the figure """
            self.fig, self.ax = plt.subplots()
            self.fig.subplots_adjust(bottom=0, top=1, right=1, left=0)
            self.fig.canvas.mpl_connect('key_press_event', self.react_to_key_press)
            self.ax.axis('off')
        self.display = {}



    def show(self):
        """
        Display the viewer with the current setings
        """
        self.fill_legend()
        getattr(self, 'display_view_mode_' + self.view_mode)()

    def display_view_mode_1(self):
        """
        display 3d viewer
        """
        for key, item in self.image_data.items():
            self.display[key] = self.ax.imshow(item['image_npa'][:,:,self.idx_slice],
                                               extent=self.extent_single_slice,
                                               interpolation='none')
            if not item['image_is_color']:
                self.display[key].set_cmap('gray')

        for mode, data, opacity in zip(['_9', '_8'],['array', 'contour'],
                                       [self.overlay_opacity, self.contour_opacity]):
            for key, item  in self.mask_data.items():
                mask_visible = key in self.mask_to_show

                item['slice_rgba'][:,:,3] = item[data][:,:,self.idx_slice]*opacity
                self.display[key+mode] = self.ax.imshow(
                                                item['slice_rgba'],
                                                extent=self.extent_single_slice,
                                                interpolation='none'
                                                            )
        self.__update_mask_visibility()
        self.__update_image_visibility()
        self.fig.canvas.draw()

    def display_view_mode_2(self):
        """
        display montage
        """
        for key, item in self.image_data.items():
            montage_npa, n_row, n_col = self.__get_montage_image(
                                                item['image_npa'],
                                                item['image_is_color'])
            extent =  [a*b for a,b in zip(self.extent_single_slice,
                                          [1,n_col, n_row, 1])]
            self.display[key] = self.ax.imshow(montage_npa,
                                               extent=extent,
                                               interpolation='none')
            if not item['image_is_color']:
                self.display[key].set_cmap('gray')

        for mode, data, opacity in zip(['_9', '_8'],['array', 'contour'],
                                       [self.overlay_opacity, self.contour_opacity]):
            for key, item in self.mask_data.items():
                npa, _, _ = self.__get_montage_image(item[data], False)
                b = np.ones_like(npa)
                npa_montage_rgba = np.stack([c*b for c in item['color']]
                                             +[npa * opacity],
                                            axis = 2)
                self.display[key+mode] = self.ax.imshow(
                                                        npa_montage_rgba,
                                                        extent=extent,
                                                        interpolation='none')
        self.__update_mask_visibility()
        self.__update_image_visibility()
        self.fig.canvas.draw()

    def fill_legend(self, show_legend=False):
        """
        Addy text about the color code for the masks as well as the
        hotkeys to the legend
        """
        for key, item in self.mask_data.items():
            self.ax.plot(np.nan, np.nan, '.',
                         color = [i/255 for i in item['color']],
                         label = key + ': ' + item['label'],
                         markersize=20)
        self.ax.plot(np.nan, np.nan, '-k', label='-'*20 )
        for key, item in self.image_data.items():
            self.ax.plot(np.nan, np.nan, 'sk', label=key+': '+item['label'])
        self.ax.plot(np.nan, np.nan, '-k', label='-'*20 )
        self.ax.plot(np.nan, np.nan, 'sk', label= 'mask_mode: "8" & "9"')
        self.ax.plot(np.nan, np.nan, 'sk', label= 'view_mode: "1" & "2"')
        self.ax.plot(np.nan, np.nan, 'sk', label= 'toggel legend: "h"')
        self.ax.plot(np.nan, np.nan, 'sk', label= 'print: "p"')

        if show_legend:
            self.ax.legend(bbox_to_anchor=(1., 1.), loc='upper left', borderaxespad=0.)

    def add_title(self, title_as_str):
        self.fig.subplots_adjust(top=0.95)
        self.ax.set_title(title_as_str)

    """SETTERS"""
    def set_image(self, image_sitk, label='image'):
        """
        set the image that shall be displayed
        """
        for idx in range(122, 96, -1): # z to a
            try_key = chr(idx)
            if not try_key in self.image_data:
                key = try_key
                break

        if not self.image_data:
            # self.image_sitk = image_sitk
            self.image_n_slice = image_sitk.GetDepth()
            self.extent_single_slice = [
                        0, #left
                        image_sitk.GetWidth()*image_sitk.GetSpacing()[0], #right
                        image_sitk.GetHeight()*image_sitk.GetSpacing()[1], #bottom
                        0] #top
            if not self.idx_slice:
                self.idx_slice = self.image_n_slice//2
            self.image_to_show = key # display the first image that is loaded
        else:
            pass
            ## Todo: check that the images occupy the same physical space



        image_is_color = image_sitk.GetNumberOfComponentsPerPixel() == 3
        dim_order = [1, 2, 0]
        if image_is_color:
            dim_order.append(3)

        self.image_data[key] = {
            'image_npa': np.transpose(sitk.GetArrayFromImage(image_sitk),
                                      dim_order),
            'image_is_color': image_is_color,
            'label' : label
                                }

    def set_mask(self, mask_sitk, label, color_name=None, color_rgb=None):
        """
        set mask to display from sitk image
        label : text to show in get_legend
        color_name : see Viewer.colors for options
        color_rgb: list with rgb values in range 0 to 255
        """
        for idx in range(97, 123): # a to z
            try_key = chr(idx)
            if not try_key in self.mask_data:
                key = try_key
                break

        if color_rgb: pass
        elif color_name: color_rgb = self.colors[color_name]
        else: color_rgb = self.colors['red']

        mask_npa = np.transpose(sitk.GetArrayFromImage(mask_sitk), (1,2,0))
        mask_npa = (mask_npa > 0).astype('uint8')

        contour_npa = np.transpose(sitk.GetArrayFromImage(self.__find_contour(mask_sitk)),
                                   (1,2,0))
        contour_npa = (contour_npa > 0).astype('uint8')

        b = np.ones(mask_npa[:,:,0].shape, dtype='uint8')
        slice_rgba = np.stack([b*c for c in (color_rgb + [1])],
                              axis=2)

        self.mask_data[key] = {'array': mask_npa,
                               'contour': contour_npa,
                               'color': color_rgb,
                               'label': label,
                               'slice_rgba': slice_rgba}

    """ Interactive parts """
    def react_to_key_press(self, event):
        """
        React to keys pressed on the keyboard when the figure is active.
        """
        if event.key in ['right', 'left'] and self.view_mode=='1':
            self.change_slice(event.key)
        elif event.key in ['1', '2'] and self.view_mode != event.key:
            self.change_view_mode(event.key)
        elif event.key in self.mask_data:
            self.change_mask_visibility(event.key)
        elif event.key in self.image_data:
            self.change_image_visibility(event.key)
        elif event.key in ['9', '8']:
            self.change_mask_mode(event.key)
        elif event.key == 'h':
            self.toggle_legend()
        elif event.key == 'p':
            self.print_current_view()

        elif event.key in ['up', 'down'] and len(self.image_data)>1:
            direction, end_image = (-1, 'z') if event.key=='up' else (1, chr(90-len(self.image_data)))
            new_key = chr(ord(self.image_to_show) + direction)
            new_key = new_key if new_key in self.image_data else 'z'
            self.change_image_visibility(new_key)

    def change_slice(self, key):
        """
        change the slice that is displayed in the 3d viewer (view_mode '1')
        with the arrow keys
        """
        old_slice = self.idx_slice*1
        if key in ['right', 'up']:
            self.idx_slice = min(old_slice+1, self.image_n_slice-1)
        elif key in ['left', 'down']:
            self.idx_slice = max(old_slice-1, 0)

        if not old_slice == self.idx_slice:
            for key, item in self.image_data.items():
                self.display[key].set_data(item['image_npa'][:,:,self.idx_slice])
            for key, item in self.mask_data.items():
                for mode, data, opacity in zip(['_9', '_8'],['array', 'contour'],
                                               [self.overlay_opacity, self.contour_opacity]):
                    item['slice_rgba'][:,:,3] = item[data][:,:,self.idx_slice]*opacity
                    self.display[key+mode].set_data(item['slice_rgba'])
            self.fig.canvas.draw()

    def change_view_mode(self, new_mode):
        """
        change between:
        '1': 3d Viewer
        '2': Montage
        Note: Check if numlock is active if you encounter unexpected behaviour
        """
        if not new_mode == self.view_mode:
            self.view_mode = new_mode
            getattr(self, 'display_view_mode_' + self.view_mode)()

    def change_mask_visibility(self, mask_to_toggle):
        """
        Toggel wether a mask is displayed or not by pressing the key
        that was specified in set_mask()
        """
        visible = (mask_to_toggle in self.mask_to_show)
        getattr(self.mask_to_show, 'remove' if visible else 'append')(mask_to_toggle)
        self.__update_mask_visibility()
        self.fig.canvas.draw()

    def change_image_visibility(self, new_image_to_show):
        """
        change which image is displayed
        """
        if not new_image_to_show == self.image_to_show:
            self.image_to_show = new_image_to_show
            self.__update_image_visibility()
            self.fig.canvas.draw()

    def change_mask_mode(self, new_mode):
        """
        Toggel wether masks are displayed as overlay '9' or contour '8' or both
        """
        mode = (new_mode in self.mask_mode)
        getattr(self.mask_mode, 'remove' if mode else 'append')(new_mode)
        self.__update_mask_visibility()
        self.fig.canvas.draw()

    def toggle_legend(self):
        """
        Toggle wether the legend is shown or not
        """
        if not self.ax.get_legend():
            self.ax.legend(bbox_to_anchor=(1., 1.), loc='upper left', borderaxespad=0.)
        else:
            self.ax.get_legend().remove()
        self.fig.canvas.draw()

    def print_current_view(self, file_name = 'viewer_image', image_type='pdf', overwrite=False):
        """
        Print the current view (= content of the figure window) to a file_name
        """
        path_to_file = file_name+'.'+image_type
        if os.path.isfile(path_to_file) and not overwrite:
            count = 1
            while True:
                new_file = '{}_{}.{}'.format(file_name, count, image_type)
                if not os.path.isfile(new_file):
                    path_to_file = new_file
                    break
                else:
                    count += 1

        self.fig.savefig(path_to_file)

    """ Helpers """
    def __get_montage_image(self, npa, is_color):
        pixel_row, pixel_col, n_slice = [int(i) for i in npa.shape[0:3]]
        aspect_ratio = self.extent_single_slice[2] / self.extent_single_slice[1]

        montage_columns = int(np.ceil(aspect_ratio
                                      *np.sqrt(pixel_row*n_slice/pixel_col)))
        montage_rows = int(np.ceil(n_slice / montage_columns))

        npa_montage = np.zeros((pixel_row*montage_rows,
                                pixel_col*montage_columns),
                               dtype = npa.dtype.name)
        if is_color:
            npa_montage = np.repeat(npa_montage[:,:,np.newaxis], 3, axis=2)

        for s in range(n_slice):
            r = int(np.floor(s/montage_columns))
            c = int(s-r*montage_columns)
            npa_montage[r*pixel_row:(r+1)*pixel_row,
                        c*pixel_col:(c+1)*pixel_col] =\
                            npa[:,:,s,:] if is_color else npa[:,:,s]

        return npa_montage, montage_rows, montage_columns

    def __update_mask_visibility(self):
        for key in self.mask_data:
            for mode in ['9', '8']:
                self.display[key+'_'+mode].set_visible(
                        key in self.mask_to_show and mode in self.mask_mode
                                                        )

    def __update_image_visibility(self):
        for key in self.image_data:
            self.display[key].set_visible(key == self.image_to_show)

    def __find_contour(self, mask_sitk):
#         contour_sitk = sitk.Image(mask_sitk.GetSize(), sitk.sitkUInt8)
#         contour_sitk.CopyInformation(mask_sitk)
        size = mask_sitk.GetSize()[0:2]
        dilate = sitk.BinaryDilateImageFilter()
        dilate.SetKernelRadius(self.line_width_increase)

#         for s in range(mask_sitk.GetDepth()):
#             contour_sitk = sitk.Paste(contour_sitk,
#                        sitk.JoinSeries(dilate.Execute(
#                                     sitk.LabelContour(mask_sitk[:,:,s])>0)),
#                        size,
#                        destinationIndex=[0,0,s])
        contour_slices = [dilate.Execute(sitk.LabelContour(mask_sitk[:,:,s]>0))
                            for s in range(mask_sitk.GetDepth())]
#         (m.CopyInformation(contour_slices[0]) for m in contour_slices[1:])
        for s in range(1, len(contour_slices)):
            contour_slices[s].CopyInformation(contour_slices[0])
        contour_sitk = sitk.JoinSeries(contour_slices)
        contour_sitk.CopyInformation(mask_sitk)
        return contour_sitk


""" Functions to combine images and masks """
def combine_masks(mode, mask_sitk_1, mask_sitk_2):
    """
    Get the union or intersection of two masks
    :param mode: 'union' ('u') or 'intersection' ('i')
    :param mask_sitk: sitk images
    :returns: new_mask (sitk_image)
    """
    if mode in ['union', 'u']:
        new_mask = sitk.Or(mask_sitk_1, mask_sitk_2)
    elif mode in ['intersection', 'i']:
        new_mask = sitk.And(mask_sitk_1, mask_sitk_2)
    else:
        raise Exception('Unknown mode: {}'.format(mode))

    return new_mask

def checkerboard(img1, img2, board_size=25):
    """
    Combines both input images in a checkerboard view.
    Can be used to evaluate the results of an image registration
    :param img1: sitk image
    :param img2: sitk image, same origin, spacing and direction as img1
    :param board_size: (optional) number of checkerboard fields
    :returns: sitk image
    """
    img1, img2 = check_spatial_properties(img1, img2, output=True)
    return sitk.CheckerBoard(img1, img2, [board_size, board_size, 1])

def imfuse(img1, img2):
    """
    Fuse the images in different color channels (magenta and green).
    Areas of a agreement are in grayscale
    :param img1: sitk image, displayed in magenta
    :param img2: sitk image, displayed in green
    :returns fused image: sitk (color) image
    """
    check_spatial_properties(img1, img2)

    npa1 = sitk.GetArrayFromImage(sitk.Cast(sitk.RescaleIntensity(img1),
                                            sitk.sitkUInt8))
    npa2 = sitk.GetArrayFromImage(sitk.Cast(sitk.RescaleIntensity(img2),
                                            sitk.sitkUInt8))

    new_img = sitk.GetImageFromArray(np.stack((npa1, npa2, npa1), axis=3),
                                     isVector=None)
    # order to achieve magenta-green overlay
    new_img.CopyInformation(img1)

    return new_img

def imfuse_stack(image_list):
    """
    Overlay a list of images in different colorchannels
    (mainly to inspect groupwise registration)
    """
    colors = [ [255,   0, 255], # Magenta
               [  0, 255,   0], # Green

               [255, 127,   0], # orange
               [  0, 127, 255], # blue Cyan

               [255,   0,   0], # red
               [  0, 255, 255], # cyan

               [  0,  0,  255], # blue
               [255, 255,   0] # yellow
             ]

    np_arrays = [sitk.GetArrayFromImage(sitk.Cast(sitk.RescaleIntensity(img),
                                                  sitk.sitkFloat32))
                    for img in image_list ]
    rgb_arrays = [np.stack((c[0]*npa, c[1]*npa, c[2]*npa), axis=3) \
                    for npa, c in zip(np_arrays, colors)]

    combined_img = sitk.RescaleIntensity(
                     sitk.GetImageFromArray(sum(rgb_arrays), isVector=True),
                     outputMinimum=0, outputMaximum=1)
    combined_img.CopyInformation(image_list[0])

    return combined_img

def check_spatial_properties(img1, img2, tolerance=1e-4, output=False):
    """
    Checks if origin, spacing and direction of two imgaes are the same
    :param img1: sitk image
    :param img2: sitk image
    :param tolerance: tolerance for each individual propertie to be considered
                      equal
    :param output: Sets if an output is returned or not
    :returns: img1, img2.CopyInformation(img1) [if output == True]
    """
    errorText = ''
    for spatial_property in ['Origin', 'Spacing', 'Direction']:
        if abs(np.array(getattr(img1, 'Get'+ spatial_property)())
                   - np.array(getattr(img2, 'Get'+ spatial_property)())
                   ).max() > tolerance:
            errorText += spatial_property + ' not the same\t'
    if len(errorText)>0:
        raise Exception(errorText+'\n\t\t\tTolerance = {}'.format(tolerance))

    if output:
        img2.CopyInformation(img1)
        return img1, img2

def show_folder(path_to_folder, image_prefix='img', mask_prefix='Mask', file_type='.nii'):
    """
    Show all images in one folder
    (All images need to have the same dimensions / spatial properties)
    """

    v = Viewer()
    colors = list(v.colors.keys())

    for f in os.listdir(path_to_folder):
        if f.startswith(image_prefix) and f.endswith(file_type):
            v.set_image(sitk.ReadImage(os.path.join(path_to_folder, f)),
                        label=os.path.basename(f).split('.')[0])

    count = 0
    for f in os.listdir(path_to_folder):
        if f.startswith(mask_prefix) and f.endswith(file_type):
            count += 1
            v.set_mask(sitk.ReadImage(os.path.join(path_to_folder, f)),
                       os.path.basename(f).split('.')[0],
                       color_name=colors[count % len(colors)])
    v.show()
    v.toggle_legend()
    return v

def show_folder_pp(path_to_folder):
    v = Viewer()
    v.line_width_increase = 0
    nii_list = [f for f in os.listdir(path_to_folder) if f.endswith('nii')]
    for f in nii_list:
        print(f)
        if f.startswith('Mask'):
            count+=1
            v.set_mask(sitk.ReadImage(os.path.join(path_to_folder, f))>0,
                       f, color_rgb = 'white')
        elif f.startswith('T1T2SENSE'):
            pass
        else:
            v.set_image(sitk.ReadImage(os.path.join(path_to_folder, f)),
                        label=f)
    v.show()
    v.toggle_legend()
    return v
