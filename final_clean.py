import logging
from tqdm import tqdm
import pandas as pd
from arcgis.geocoding import geocode
from arcgis.gis import GIS
import os

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(file_path, sample_size=None):
    """Load data from CSV or Excel file based on file extension and optionally sample it."""
    logging.info(f"Loading data from {file_path}")
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format.")
    
    if sample_size:
        df = df.sample(n=sample_size, random_state=1)
    return df

def clean_and_prepare_data(df):
    """
    Prepare data by cleaning and transforming the DataFrame.

    Args:
        df (pandas.DataFrame): The input DataFrame to be cleaned and prepared.

    Returns:
        pandas.DataFrame: The cleaned and prepared DataFrame.

    Raises:
        KeyError: If the 'Constituent LookupID' column is not found in the DataFrame.

    """
    logging.info("Starting cleaning and preparing data.")

    # Drop unnecessary columns
    df = df.drop(columns=['Other Country.1', 'Other Major Gift Region.1', 'Other Primary Metro.1', 'Other Zip.1', 'Other State.1', 'Other City.1', 
        'Other Address.1', 'Other Address Incomplete?.1', 'Other Type.1', 'Other Country', 'Other Major Gift Region', 'Other Primary Metro', 
        'Other Zip', 'Other State', 'Other City', 'Other Address', 'Other Address Is Primary?', 'Other Address Incomplete?', 'Other Type', 
        'Home Address Incomplete?', 'Home Address Is Primary?', 'Work Country', 'Work Primary Metro Area', 'Work Major Gift Region',
        'Work Phone', 'Work County', 'Work Zip', 'Work State', 'Work City', 'Work Address', 'Work Address Is Primary?', 'Work Address Incomplete?',
        'Career Level','Full Name', 'Title', 'First Name', 'Last/Name/Org Name', 'Committee Name', 'Committee Role', 'Former Commitee Name', 
        'Former Committee Role', 'Spouse LookupID', 'Formal Mailing Name (Joint/Individual)', 'Informal Mailing Name (Joint/Individual)', 
        'Payments Received', 'Expectancies (Balance Due)', 'Commitments (Balance Due)', '# of Recognition Transactions', 
        'Number of Years of Recognition', 'One-Time Gifts', 'Commitments', 'Expectancies', 'A.6', 'A.7', 'A.5', 'A.4', 
        'A.8', 'Payments Received.1', 'A.9', 'Commitments (Balance Due).1', 'A.10', 'Expectancies (Balance Due).1', 'A.11', 'Last Amount', 
        'Last Designation', '# of Recognition Transactions.1', 'Number of Years of Recognition.1', ' Campaign Recognition', 'A.12', 
        'One-Time Gifts.1', 'Commitments.1', 'A.13', 'A.14', 'Expectancies.1', 'A.15', 'Last Visit/Introduction by', 'Interaction Type', 
        'Job Category', 'Home Phone', 'Monteith Society', 'Primary Capacity Rating Type', 'Primary Capacity Rating Date', 'Primary Inclination Rating Type',
        'Primary Inclination Rating Date', 'Gift Officer Field Rating', 'Gift Officer Field Rating Date', 'Research Rating', 'Research Rating Date', 
        'Capacity Verified Rating', 'Capacity Verified Rating Date', 'Capacity Unverified Rating', 'Capacity Unverified Rating Date', 'Blackbaud Hard Asset',
        'Blackbaud Hard Asset Date', 'Wealth-X Net Worth', 'Wealth-X Net Worth Date', 'Windfall Data Net Worth', 'Windfall Data Net Worth Date', 
        'Target Analytics Net Worth', 'Target Analytics Net Worth Date', 'PDA UM Inclination', 'UM AG Propensity', 'Med Primary Manager'])
    
    # Rename 'Constituent LookupID' to 'LID'
    if 'Constituent LookupID' in df.columns:
        df.rename(columns={'Constituent LookupID': 'LID'}, inplace=True)
    else:
        logging.error("Column 'Constituent LookupID' not found in DataFrame.")

    # Check if renaming was successful
    if 'LID' not in df.columns:
        #Rename 'Constituent LookUpID' to 'LID'
        df.rename(columns={'Constituent LookupID': 'LID'}, inplace=True)
        return df  
    
    # Create Latitude and Longitude columns if they do not exist
    if 'Latitude' not in df.columns or 'Longitude' not in df.columns:
        df['Latitude'] = None
        df['Longitude'] = None

    # Rename 'latitude' and 'longitude' columns to 'Latitude' and 'Longitude' if present
    if 'latitude' in df.columns and 'longitude' in df.columns:
        df.rename(columns={'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)
    
    # Create a 'Primary Address' column from the home address components
    df['Primary Address'] = df.apply(lambda x: f"{x['Home Address']}, {x['Home City']}, {x['Home State']} {x['Home Zip']}, {x['Home Country']}", axis=1)

    # Create a 'donor_status' column based on the 'UM-Wide Lifetime Recognition' column and 'ISR Donor' status
    df['donor_status'] = df['Institute for Social Research\nLifetime Recognition'].map(lambda x: 'ISR Donor', na_action='ignore')

    # Fill missing values in 'donor_status' column based on 'UM-Wide Lifetime Recognition' column
    df['donor_status'] = df.apply(UM_donor, axis=1)
    df['donor_status'].fillna('Non Donor', inplace=True)

    # Convert monetary columns to numeric values
    df['Institute for Social Research Lifetime Recognition Numeric'] = df['Institute for Social Research\nLifetime Recognition'].map(replace)
    df["UM-Wide Lifetime Recognition Numeric"] = df['UM-Wide\nLifetime Recognition'].map(replace)

    # Convert 'Age' column to numeric and fill missing values with 0
    df['Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(0).astype(int)

    return df

def fill_missing_values(df):
    """
    Fill missing values in DataFrame columns based on their data type.

    Args:
        df (pd.DataFrame): The DataFrame whose missing values need to be filled.
    """

    # Determine the fill value based on data type
    fill_values = {
        'object': 'Not Available',  # Use 'Not Available' for string types
        'float64': 0.0,  # Use 0.0 for floats
        'int64': 0,    # Use 0 for integers
        'datetime64[ns]': pd.Timestamp('1900-01-01'),  # A common default date
        'bool': False,  # False for booleans
        'category': 'Not Available'  # Use 'Not Available' for categorical data
    }

    # Iterate over each column in the DataFrame
    for column in df.columns:
        dtype = str(df[column].dtype)
        if df[column].isnull().any():  # Check if there are any nulls to fill
            fill_value = fill_values.get(dtype, 'Not Available')  # Get specific fill value or use 'Not Available'
            if dtype == 'category' and 'Not Available' not in df[column].cat.categories:
                df[column] = df[column].cat.add_categories('Not Available')
            df[column].fillna(fill_value, inplace=True)
            logging.info(f"Filled missing values in {column} with {fill_value}")
        else:
            logging.info(f"No missing values to fill in {column}")

    return df

def UM_donor(row):
    """Determines the donor status based on lifetime recognition columns."""
    if pd.isnull(row.donor_status) and not pd.isnull(row['UM-Wide\nLifetime Recognition']):
        return 'UM Donor'
    return row.donor_status


def replace(num):
    """
    Replaces special characters in a given number and returns the cleaned number.

    Parameters:
    num (int, float, str): The number to be cleaned.

    Returns:
    float: The cleaned number.

    """
    if pd.isna(num):
        return 0
    if isinstance(num, str):
        return float(num.replace(',', '').replace('$', ''))
    elif isinstance(num, (int, float)):
        return num
    return 0

def create_affiliation_columns(df):
    """ Creates individual columns for each affiliation found in the DataFrame. """
    # Ensure 'Constituent Affiliation' exists and handle NaN correctly
    if 'Constituent Affiliation' not in df.columns:
        logging.error("Constituent Affiliation column missing.")
        return df, set()
    
    def clean_affiliations(affiliation):
        if pd.isna(affiliation):
            return []
        # Split by newline, replace commas and split, then flatten the list
        return list(set(affiliation.replace('\n', ',').split(',')))

    df['Affiliation List'] = df['Constituent Affiliation'].apply(clean_affiliations)
    all_affiliations = set()
    for affil_list in df['Affiliation List']:
        all_affiliations.update(affil_list)
    
    for affil in all_affiliations:
        df[f'Affiliation: {affil}'] = df['Affiliation List'].apply(lambda x: affil in x)
    
    return df, all_affiliations

def save_affiliation_files(processed_data, affiliations, output_dir='affiliation_layers'):
    """
    Save affiliation files based on processed data and affiliations.

    Args:
        processed_data (pandas.DataFrame): The processed data containing the affiliation columns.
        affiliations (list): A list of affiliations to create files for.
        output_dir (str, optional): The directory to save the affiliation files. Defaults to 'affiliation_files'.

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)
    for affil in affiliations:
        column_name = f'Affiliation: {affil}'
        if column_name in processed_data.columns:
            sub_df = processed_data[processed_data[column_name]]
            if not sub_df.empty:
                filename = f'{affil.replace(" ", "_").replace("/", "-")}-layer.csv'
                sub_df.to_csv(os.path.join(output_dir, filename), index=False)
                logging.info(f"Affiliation file for {affil} created.")
        else:
            logging.warning(f"Column {column_name} does not exist in the DataFrame.")
            

def handle_interest_data(main_df, interest_file_path):
    """
    Load interest data, create a dictionary from it, and merge it into the main DataFrame.

    Args:
        main_df (pd.DataFrame): The main DataFrame that needs the interest data merged into.
        interest_file_path (str): Path to the CSV file containing interest data.

    Returns:
        pd.DataFrame: The updated main DataFrame with interest data merged.
    """
    # Load interest data
    logging.info("Loading interest data.")
    interest_df = pd.read_csv(interest_file_path)
    interest_df.rename(columns={'Constituent LookupID': 'LID'}, inplace=True)

    # Create interest dictionary
    logging.info("Creating interest dictionary.")
    interest_dic = {}
    for index, row in interest_df.iterrows():
        make_int_dic(row, interest_dic)

    # Merge interest data
    logging.info("Merging interest data.")
    main_df['Interests'] = main_df['LID'].apply(
        lambda id: add_int_data(id, interest_dic))

    # Perform final edits on the merged DataFrame
    logging.info("Applying final edits to merged DataFrame.")
    main_df = merged_df_edits(main_df)

    return main_df

def make_int_dic(row, dic):
    """Updates dictionary with interest data."""
    id = row['LID']
    interest_cat = row['Interest Category']
    interest_subc = row['Interest Subcategory']
    int_level = row['Interest Level']

    if id not in dic:
        dic[id] = {}
    dic[id][interest_cat] = (interest_subc, int_level)

    return dic

def add_int_data(id, interest_dic):
    return interest_dic.get(id, 'No Known Interests')

def merged_df_edits(merged_df):
    """
    Perform edits on the merged_df DataFrame.

    Args:
        merged_df (DataFrame): The DataFrame to be edited.

    Returns:
        DataFrame: The edited DataFrame.
    """
    merged_df = merged_df.rename(columns={
        'Date of Last Recognition Transaction': 'Date of Last UM Recognition Transaction',
        'Date of Last Recognition Transaction.1': 'Date of Last ISR Recognition Transaction'
    })
    merged_df = merged_df.drop_duplicates(subset='LID', keep='first')
    return merged_df

def collect_addresses_to_geocode(df):
    """
    Collects addresses from a DataFrame that need to be geocoded.

    Args:
        df (pandas.DataFrame): The DataFrame containing address information.

    Returns:
        dict: A dictionary where the keys are the indices of the rows in the DataFrame
              and the values are the addresses that need to be geocoded.
    """
    addresses_to_geocode = {}
    for index, row in df.iterrows():
        if pd.isna(row['Latitude']) or pd.isna(row['Longitude']):
            address = f"{row['Home Address']}, {row['Home City']}, {row['Home State']} {row['Home Zip']}, {row['Home Country']}"
            if all(pd.notna(row[field]) and row[field].strip() != "" for field in ['Home Address', 'Home City', 'Home State', 'Home Zip', 'Home Country']):
                addresses_to_geocode[index] = address
    return addresses_to_geocode

def batch_geocode_addresses(addresses_to_geocode, api_key, df):
    """
    Batch geocodes a list of addresses using the ArcGIS Geocoding service.

    Parameters:
    - addresses_to_geocode (dict): A dictionary containing addresses to geocode as keys and their corresponding indices as values.
    - api_key (str): The API key for accessing the ArcGIS Geocoding service.
    - df (pandas.DataFrame): The DataFrame to update with geocoded latitude and longitude values.

    Returns:
    None
    """
    gis = GIS(api_key=api_key)
    # Initialize tqdm progress bar
    progress_bar = tqdm(addresses_to_geocode.items(), total=len(addresses_to_geocode), desc="Geocoding addresses")
    
    for index, address in progress_bar:
        try:
            result = geocode(address, as_featureset=False)[0]
            df.at[index, 'Latitude'] = result['location']['y']
            df.at[index, 'Longitude'] = result['location']['x']
            # Optionally update the progress description with success message
            progress_bar.set_description(f"Geocoded: {address}")
        except Exception as e:
            logging.error(f"Geocoding failed for {address}: {e}")
            # Update progress bar with error info
            progress_bar.set_description(f"Failed geocoding: {address}")

def main():

    # API KEY MAY BE INVALID COME MAY 
    api_key = 'AAPK393b8da67c074504bdc73ed3037e193bYC_cZGRLP9Tf-592LpmQzMqO27or9AbbzYGHX1e5Xjowm3CnSytMzKUZ5uxjzysf'
    #========================================================================================================
    # If you are updating geo-coordinates for existing data, provide the path to the geocoded data file here.
    # If you are starting from scratch, set this to None.
    #========================================================================================================
    geocoded_data_path = '3-18-dataset_copy.csv'
    # geocoded_data_path = None


    file_path = '9.0 MProfile - donors and affiliates Feb. 2024.xlsx' 
    interest_file_path = 'DART Interest Data 2024 - Known interests for ISR Constituents copy.csv'

    # Load main and geocoded data
    logging.info("Loading main data from Excel.")           
    new_data = load_data(file_path)
    logging.info("Loading geocoded data.")

    merged_data = new_data  # Default to new_data in case no geocoded data is merged

    if geocoded_data_path != None and os.path.exists(geocoded_data_path):
        logging.info("Loading geocoded data.")
        geocoded_data = load_data(geocoded_data_path)

        # Ensure columns are correctly named for consistency
        if 'latitude' in geocoded_data.columns and 'longitude' in geocoded_data.columns:
            geocoded_data.rename(columns={'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)

        # Check if essential columns exist before merging
        if 'Latitude' in geocoded_data.columns and 'Longitude' in geocoded_data.columns:
            logging.info("Merging geocoded data into main DataFrame.")
            merged_data = pd.merge(new_data, geocoded_data[['ConstituentSYSTEMID', 'Latitude', 'Longitude']], on='ConstituentSYSTEMID', how='left')
        else:
            logging.error("Geocoded data does not contain 'Latitude' or 'Longitude'. Using original data without merge.")
    else:
        logging.warning("Geocoded data file not found. Full geocoding will be applied to new data.")
        
    # Clean and prepare the main data
    logging.info("Cleaning and preparing data.")
    merged_data = clean_and_prepare_data(merged_data) 

    # Handle affiliations
    logging.info("Handling affiliations.")
    merged_data, all_affiliations = create_affiliation_columns(merged_data)

    # Collect addresses that need geocoding
    addresses_to_geocode = collect_addresses_to_geocode(merged_data)
    
    # Geocode addresses if any need updating
    if addresses_to_geocode:
        logging.info("Starting batch geocoding...")
        batch_geocode_addresses(addresses_to_geocode, api_key, merged_data)
    
    # Integrate interests into the main data
    logging.info("Integrating interest data.")
    processed_data = handle_interest_data(merged_data, interest_file_path)
    
    # Process missing values
    logging.info("Handling missing values.")
    processed_data = fill_missing_values(processed_data)

    # Save processed data
    logging.info("Saving processed data to file.")
    processed_data.to_csv('processed_complete.csv', index=False)

    # Extract unique affiliations from processed_data for file creation
    affiliations = processed_data.columns[processed_data.columns.str.startswith('Affiliation: ')]
    # Remove 'Affiliation: ' prefix to get the actual affiliation names
    affiliations = [affil.replace('Affiliation: ', '') for affil in affiliations]
    
    # Create and save affiliation files
    save_affiliation_files(processed_data, affiliations)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
