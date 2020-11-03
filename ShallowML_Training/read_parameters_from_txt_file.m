function options = read_parameters_from_txt_file(path_to_txt_file)
% read parameters from a .txt file
% The file needs to look like this
%
%   # this is a comment
%   parameter_name = value
%   parameter2 = value1, value2 
%   parameter3 = value value
%
% The output is a structure, where the patameter names are the fields. 
% If one value is provided, the fieldvalue is a string
% if several values are provided, the fildvalue is a cell array of strings
%
fid = fopen(path_to_txt_file,'r');
tline = fgetl(fid); % get the first line

while ischar(tline)
    if startsWith(tline, '#')
        % ignore comments
    elseif contains(tline, '=')
        tline = strsplit(tline, '=');
        tline = strtrim(tline); % remove leading and tailing whitespaces
        
        parameter = tline{1};
        selection = strsplit(tline{2}, {' ', ','});
        if length(selection) == 1
            selection = selection{1};
        end
        
        options.(parameter) = selection;
    end    
    tline = fgetl(fid); %get new line
end
fclose(fid);

end
