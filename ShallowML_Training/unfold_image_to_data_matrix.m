function [data_matrix, n_channel, n_neighbours] = ...
                           unfold_image_to_data_matrix(image, unfolding_mode)
    % unfold a single image to the data matrix.
    % in this process, take the unfolding radius as well as the unfolding
    % type into account.
    %
    % The result is the 2d data_matrix, where the first n_channel columns
    % correspond to the original image
    %
    [nd1,nd2,nd3, nd4, nd5, nd6] = size(image);
    n_voxel = nd1*nd2*nd3;
    n_channel = nd4*nd5*nd6;

    switch unfolding_mode
        case 'R0_2D'
            slice_range = 0;
            xy_range = 0;
            n_neighbours = 1;
        case 'R1_2D'
            slice_range = 0;
            xy_range = [0,-1,1];
            n_neighbours = 9;
        case 'R1_3D'
            slice_range = [0, -1, 1];
            xy_range = [0,-1,1];
            n_neighbours = 27;
        otherwise
            error('Unknown unfolding option')
    end
    data_matrix = nan(n_voxel, n_channel*n_neighbours);

    img_padded = padarray(image, [1, 1, 1, 0, 0, 0], NaN);
    count = 0;
    for row = xy_range
        for column = xy_range
            for slice = slice_range
                data_matrix(:,(1:n_channel)+count) = ...
                    reshape(...
                        img_padded((row+2):(nd1+1+row),...
                                  (column+2):(nd2+1+column),...
                                  (slice+2):(nd3+1+slice),...
                                  :,:,:),...
                        n_voxel, n_channel);
               count = count+n_channel;
            end
        end
    end
end
