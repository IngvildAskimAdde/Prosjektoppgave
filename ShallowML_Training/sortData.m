function x = sortData(x, sorting_mode, nC, nN)
% x is the data matrix for one scan type
%   can be one or multiple patients
% 
% sorting_mode = 'Yes' or 'No'
% nC = number of channels
% nN = number of neighbours
%%
switch sorting_mode
    case 'No'
       % nothing to do

    case 'Yes'
%         [nC, nN] = getNumChanelsAndNumNeighbours(opt);
        count = 0;
        for idx = 1:nC
           x(:,idx:nC:nC*nN) = sort(x(:,idx:nC:nC*nN),2 , 'descend',...
                                    'MissingPlacement', 'last');
           count = count + nC;
        end

    otherwise
        errror('Unknown sorting option');
end
end
