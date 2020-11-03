
classdef nii2mat_input_conversion
    % Convert a set of nifti files to the matlab patient structure
    % Assumes a certain folder naiming sheme!

    properties
       scanTypes % cell array with image names to be loaded
       maskName % name of the nii file for the mask (no .nii!)
       saveFolder_mat % where the result is saved
       dataFolder_nii % folder with the nii files
       patientStruct % store the images
       
       image_size = nan
       
       replace_0_with_nan = true 
    end

    methods
        function obj = nii2mat_input_conversion(dataFolder)
            % constructure
            if exist(dataFolder, 'dir') == 7
                obj.dataFolder_nii = dataFolder;
            else
                error('Data folder does not exist\n\t%s', dataFolder)
            end
        end

        function obj = convertScans(obj)
            for scan = obj.scanTypes
                files = dir(fullfile(obj.dataFolder_nii, [ scan{1}, '*.nii']));

                switch size(files, 1)
                    case 0
                        error('No files found\n\tScan: %s\n\tFolder %s', scan{1}, obj.dataFolder_nii)
                    case 1
                        obj.patientStruct.(scan{1})= nii2mat_input_conversion.load_nifti(fullfile(files(1).folder, ...
                                                                         files(1).name));
                    otherwise
                        % different b, e, and or t values
                        % sort images into 6d matrix (x y z, t, e, b)
                        obj.patientStruct.(scan{1})= nii2mat_input_conversion.load_6D_image_from_nifi(files);
                end
                
                if isnan(obj.image_size)
                   info = niftiinfo(fullfile(files(1).folder,files(1).name));
                   obj.image_size = info.ImageSize;
                end
                
                
                if obj.replace_0_with_nan
                   
                   obj.patientStruct.(scan{1}) = obj.set_0_to_nan( obj.patientStruct.(scan{1}) );
                end
                
            end
        end

        function obj = convertMask(obj)

            file = fullfile(obj.dataFolder_nii, [obj.maskName,'.nii']);

            obj.patientStruct.Contours = nii2mat_input_conversion.load_nifti(file) > 0  ;
                % mask is logical!

            if isnan(obj.image_size)
               info = niftiinfo(file);
               obj.image_size = info.ImageSize;
            end
        end

        function savePatientStruct(obj, saveFolder)
            if exist(saveFolder, 'dir') ~= 7
                error('Save folder does not exist\n\t%s', saveFolder)
            end

            % define the save name = patient name = dataFolder name
            [~,patient,~] = fileparts(obj.dataFolder_nii);

            patStruct = obj.patientStruct;
            save(fullfile(saveFolder, [patient '.mat']),'-struct', 'patStruct')
        end
        

  
    end

    methods(Static, Access=private)
        function img = load_nifti(filename)
            img = niftiread(filename);
            % convert to dicom coordinates
            % just to make the images look the same as before
%             img = imrotate(flip(img), -90);
        end

        function bigImg = load_6D_image_from_nifi(files)
            filelist = {files.name};

            % split and remove .nii ending
            filelist = cellfun(@(c) split(c(1:end-4), '_'), filelist, ...
                               'UniformOutput', false);

            e_values = cellfun( @(c) nii2mat_input_conversion.extract_number(c, 'e'), filelist);
            t_values = cellfun( @(c) nii2mat_input_conversion.extract_number(c, 't'), filelist);
            b_values = cellfun( @(c) nii2mat_input_conversion.extract_number(c, 'b'), filelist);
            
            
            [~, ~, t_index] = unique(t_values);
            
            nE = length(unique(e_values));
            nT = length(unique(t_values));
            nB = length(unique(b_values));

            %a quick check
            if nE*nT*nB ~= size(files,1)
                error('Missing some files to fill all dimensions')
            end


            for idx = 1:size(files,1)
                if idx == 1
                    info = niftiinfo(fullfile(files(idx).folder, files(idx).name));
                    bigImg = zeros( [info.ImageSize, nE, nT, nB]);
                end
                bigImg(:,:,:,e_values(idx), t_index(idx), b_values(idx)) = ...
                                nii2mat_input_conversion.load_nifti(fullfile(files(idx).folder, files(idx).name));
            end
        end

        function varIdx = extract_number(cells, varID)
            for idx = 1:length(cells)
                if startsWith(cells{idx}, varID, 'IgnoreCase', false)
                    varIdx = str2double(cells{idx}(2:end)) +1 ;
                    break
                end
            end
            if exist('varIdx','var')~=1
                varIdx = 1;
            end
        end
        
        function img = set_0_to_nan(img)
            %%
           % if the resampling is outside the original FOV, the image is 
           % all black (value == 0)
           % set this values to nan for the further analysis
           %
           % :param img: matrix 
           % :return: img, where 0's are replaced with nan
           %
           
           idx_zeros = img == 0;
           img(idx_zeros) = nan;
        end
    end
end

