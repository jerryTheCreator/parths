import pandas as pd
import os


def _txt_cleaner(_file, filename, path):
    # Read the CSV file
    df = pd.read_pickle(_file)

    # Modify the dataframe as needed
    # df['<DATE>'] = df["<DATE>"].astype(str) + ":" + df["<TIME>"].astype(str)
    # df.columns = df.columns.str.strip("<>").str.lower()
    
    new_file_name = os.path.splitext(filename)[0] + '.csv' # create the new filename
    new_file_path = os.path.join(path, new_file_name) # get the full path of the new file

    df.to_csv(new_file_path) # Save new dataframe as pickle file
    os.remove(_file) # Remove Old File

def clean_data(root_dir):
    # Traverse the directory structure
    for dirpath, dirnames, filenames in os.walk(root_dir):
        
        # Loop through all the files in each subfolder
        for file in filenames:
            # Check if the file is a TXT/CSV file
            if file.endswith('.pkl'):
                # Create the full path to the file
                csv_file = os.path.join(dirpath, file)
                # Call the modify_csv function
                _txt_cleaner(csv_file, file, dirpath)

def find_data(symbol, root_dir):
    # The name of the file to search for
    file_name = symbol.lower()
    file_path = None

    # search for the file in the directory and its subdirectories
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if all(item in file for item in [file_name, '.us.csv']):
                # construct the path to the file
                file_path = os.path.join(root, file)
    
    return file_path

# Get the path to the parent directory
parent_dir = os.path.dirname(os.getcwd())
data_folder_path = os.path.join(parent_dir, 'data')

clean_data(data_folder_path)
# find_data('aapl', data_folder_path)