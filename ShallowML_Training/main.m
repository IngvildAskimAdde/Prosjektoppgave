function main(parameter_txt_file)
    %
    %
    %
    disp('Read options')
    options = get_options(parameter_txt_file);
    
    disp('Load data')
    [train_data,ground_truth, patient_list] = get_train_data(options);
    
    disp('Start leave one out cross validation')
    % perform a leave one out cv
    for idx = 1:length(patient_list)
        disp(patient_list{idx})
        
        if isfile(fullfile(options.folder_to_save_result, ...
                           [patient_list{idx} '.nii']))
            disp('     Already predicted this patient')
        else
            tall_idx = tall(~strcmp(patient_list, patient_list{idx}));
            model = trainModel_xy(cell2mat(train_data(tall_idx)),...
                                  cell2mat(ground_truth(tall_idx)),...
                                  options.model);
            predict_for_patient(model, patient_list{idx}, options);
        end
    end
end

function options = get_options(parameter_txt_file)
    options = read_parameters_from_txt_file(parameter_txt_file);
    if  ~iscell(options.images_to_use)
        options.images_to_use = {options.images_to_use};
    end
    file_parts = strsplit(parameter_txt_file, {filesep, '.'});
    options.folder_to_save_result = fullfile(options.folder_to_save_result, ...
                                            file_parts{end-1});

    if ~strcmp(options.normalise,'ZScore_PerImage_PerPatient')
        error('Fixed normalisation (ZScore_PerImage_PerPatient) required')
    end
    if ~strcmp(options.downsampling, 'Patient-50/50')
        error('Fixed sampling (Patient-50/50) required')
    end
    disp(options)
end

function [data, ground_truth, patient_list] = get_train_data(options)
    %
    %
    %
    patient_folder_content = dir(fullfile(options.folder_patient_image_data, ...
                                          [options.patient_prefix '*']));
    n_patient = size(patient_folder_content,1);

    patient_list = {patient_folder_content.name}';

    %%
    data = tall(cell(n_patient,1));
    ground_truth = tall(cell(n_patient,1));
    for idx_patient = 1:n_patient
        patient_folder = fullfile(patient_folder_content(idx_patient).folder, ...
                                  patient_folder_content(idx_patient).name);
        [x, y] = get_data_patient(patient_folder, options, 'train');
        tall_idx = tall(strcmp(patient_list, patient_list{idx_patient})); % tall logical index for tall array
        data(tall_idx) = {x};
        ground_truth(tall_idx) = {y};
        clear x y tall_idx
    end

end

function [patient_data, response, image_size] = get_data_patient(folder, options, mode)
    %
    %
    image_list = options.images_to_use;
    n_images = length(image_list);

    converter = nii2mat_input_conversion(folder);


    patient_data = cell(1,n_images);
    for idx = 1:n_images
        converter.scanTypes = image_list(idx);
        image_data = converter.convertScans();

        if idx == 1
            image_size = image_data.image_size;
        end

        image_data = image_data.patientStruct.(image_list{idx});

        % normalise the image per patient
        image_data = normalise_image(image_data);

        [data_matrix, n_channel, n_neighbours] =...
                            unfold_image_to_data_matrix(image_data, ...
                                options.([image_list{idx} '_unfolding']));

        data_matrix = sortData(data_matrix, ...
                               options.([image_list{idx} '_sorting']),...
                               n_channel, n_neighbours);

        patient_data{idx} = data_matrix;


        clear image_data data_matrix n_channel n_neighbours
    end
    patient_data = cell2mat(patient_data);

    switch mode
        case 'train'
            converter.replace_0_with_nan = false;
            converter.maskName = options.ground_truth;
            mask = converter.convertMask();
            mask = mask.patientStruct.Contours;
            response = unfold_image_to_data_matrix(double(mask), 'R0_2D');
            clear mask

            [patient_data, response]= downsample_patient_data(patient_data, response);
        case 'test'
            response = nan;
    end
end

function normalised_image = normalise_image (image)
    % Calculate the z-score of the input image
    % Ignore nan values!
    mean_value = nanmean(image(:));
    std_value = nanstd(image(:));
    normalised_image = (image - mean_value)./std_value;
end

function [x, y] = downsample_patient_data(x, y)
    %%TODO get Seed from options
    [x, has_missing] = rmmissing(x,1);
    y(has_missing) = [];

    idx_keep = y==1;
    n_tumour = nnz(idx_keep);

    idx_backbround_keep = datasample(RandStream('mt19937ar', 'Seed', 0),...
                                     find(~idx_keep), n_tumour);
    idx_keep(idx_backbround_keep) = true;

    x(~idx_keep,:) = [];
    y(~idx_keep,:) = [];
end

function model = trainModel_xy(x, y, method)
%%
switch method
    case 'LDA'  % train LDA model
        model = fitcdiscr(x,y,...
                          'DiscrimType','linear',...
                          'SaveMemory','off',...
                          'FillCoeffs','off',...
                          'Prior','uniform');

    case 'QDA'  % train QDA model
        model = fitcdiscr(x,y,...
                          'DiscrimType','quadratic',...
                          'SaveMemory','off',...
                          'FillCoeffs','off',...
                          'Prior','uniform');

    case 'SVM' % train SVM (Support Vector Machine)
        model = fitcecoc(x,y, ...
                        'Learners', 'linear', ...
                        'Prior', 'uniform');

    case 'LDA_optimized'
        model = fitcdiscr(x,y,...
                          'DiscrimType','linear',...
                          'SaveMemory','off',...
                          'FillCoeffs','off',...
                          'Prior','uniform', ...
                          'OptimizeHyperparameters', 'auto');% New!
    case 'LDA_inMemory_optimized'
        % can't use tall arrays if i want to test the hyperparameter optimisation
        x = gather(x); 
        y = gather(y);
        model = fitcdiscr(x,y,...
                          'DiscrimType','linear',...
                          'SaveMemory','off',...
                          'FillCoeffs','off',...
                          'Prior','uniform', ...
                          'OptimizeHyperparameters', {'Delta', 'Gamma'});% New!
    case 'QDA_inMemory_optimized'
        % can't use tall arrays if i want to test the hyperparameter optimisation
        x = gather(x); 
        y = gather(y);
        model = fitcdiscr(x,y,...
                          'DiscrimType','quadratic',...
                          'SaveMemory','off',...
                          'FillCoeffs','off',...
                          'Prior','uniform', ...
                          'OptimizeHyperparameters', {'Delta'});% New!           
    otherwise
        error('Selected method %s is not implemented yet', method)
end

end

function predict_for_patient(model, patient_name, options)
    %%
    %
    %
    patient_folder = fullfile(options.folder_patient_image_data, patient_name);
    [patient_data, ~, image_size] = get_data_patient(patient_folder, options, 'test');

    predicted_label = predict(model, patient_data);
    predicted_label(any(isnan(patient_data), 2)) = 0;

    predicted_label = reshape(predicted_label, image_size);



    if ~isfolder(options.folder_to_save_result)
        mkdir(options.folder_to_save_result)
    end
    niftiwrite(predicted_label, fullfile(options.folder_to_save_result, ...
                                         [patient_name '.nii']));
end
