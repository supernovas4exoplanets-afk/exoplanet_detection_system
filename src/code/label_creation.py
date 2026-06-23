import pandas as pd
import os
import glob
import re

def create_labeled_dataset(
    toi_df: pd.DataFrame, 
    eb_df: pd.DataFrame, 
    svc_df: pd.DataFrame, 
    all_sector_tics: list
) -> pd.DataFrame:
    """
    Consolidates catalogs to generate a labeled dataset for the exoplanet pipeline.
    
    Classes:
    0: Confirmed Planets
    1: False Positives / Eclipsing Binaries
    2: Null / Noise Baseline
    3: Variable / Other Astrophysical Objects
    """
    
    # ---------------------------------------------------------
    # Step 1: TOI Catalog Processing
    # ---------------------------------------------------------
    # Keep only specific dispositions and drop 'PC' and 'APC'
    # Official column in downloaded TOI catalog: 'tfopwg_disp', TIC ID: 'tid'
    valid_toi_mask = toi_df['tfopwg_disp'].isin(['CP', 'KP', 'FP', 'FA'])
    toi_filtered = toi_df[valid_toi_mask].copy()
    
    # Map to classes
    # CP (Confirmed Planet), KP (Known Planet) -> Class 0
    # FP (False Positive), FA (False Alarm) -> Class 1
    def map_toi_label(disp):
        if disp in ['CP', 'KP']:
            return 0
        elif disp in ['FP', 'FA']:
            return 1
        return None
        
    toi_filtered['label'] = toi_filtered['tfopwg_disp'].apply(map_toi_label)
    
    # Dictionary to keep track of TIC to Label mapping to handle collisions easily
    # Ensure TIC IDs are integers
    toi_filtered['tid'] = toi_filtered['tid'].astype(int)
    tic_to_label = dict(zip(toi_filtered['tid'], toi_filtered['label']))
    
    # ---------------------------------------------------------
    # Step 2: Eclipsing Binary (EB) Catalog Processing
    # ---------------------------------------------------------
    # Official column in EB catalog: 'tess_id'
    eb_df['tess_id'] = eb_df['tess_id'].astype(int)
    for tic in eb_df['tess_id']:
        # Assign Class 1 to EB stars
        # Default to TOI authority if collision exists (only overwrite if not in TOI)
        if tic not in tic_to_label:
            tic_to_label[tic] = 1

    # ---------------------------------------------------------
    # Step 3: TESS Standard Variable Catalog (SVC) Processing
    # ---------------------------------------------------------
    # Official column in SVC catalog: 'tess_id'
    svc_df['tess_id'] = svc_df['tess_id'].astype(int)
    for tic in svc_df['tess_id']:
        # Assign Class 3 to Variable stars
        # Discard if it overlaps with planetary or binary sets
        if tic not in tic_to_label:
            tic_to_label[tic] = 3

    # ---------------------------------------------------------
    # Step 4: Establish the Null/Noise Baseline
    # ---------------------------------------------------------
    # Convert list elements to int
    all_sector_tics = [int(tic) for tic in all_sector_tics]
    for tic in all_sector_tics:
        if tic not in tic_to_label:
            # Check if this TIC was discarded from TOI (i.e. it was a PC or APC)
            # We want to fully discard those, not even include them in noise
            is_pc_or_apc = not toi_df[(toi_df['tid'] == tic) & (toi_df['tfopwg_disp'].isin(['PC', 'APC']))].empty
            
            if not is_pc_or_apc:
                tic_to_label[tic] = 2

    # ---------------------------------------------------------
    # Step 5: Consolidate
    # ---------------------------------------------------------
    final_df = pd.DataFrame(list(tic_to_label.items()), columns=['TIC_ID', 'label'])
    
    return final_df

def balance_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Undersamples majority classes to match the size of the minority class.
    """
    class_counts = df['label'].value_counts()
    print("Original Class Distribution:")
    print(class_counts)
    
    # Find the size of the smallest class
    min_class_size = class_counts.min()
    print(f"Minority class size is {min_class_size}. Balancing all classes to this size...")
    
    # Sample each class to match the min_class_size
    balanced_df = df.groupby('label').sample(n=min_class_size, random_state=42)
    
    print("\nBalanced Class Distribution:")
    print(balanced_df['label'].value_counts())
    
    return balanced_df

def extract_tics_from_filenames(fits_dir: str) -> list:
    """
    Scans fits_dir for FITS files and extracts TIC IDs.
    """
    tic_ids = []
    if not os.path.exists(fits_dir):
        print(f"Directory {fits_dir} does not exist.")
        return tic_ids
        
    fits_files = glob.glob(os.path.join(fits_dir, "**", "*.fits"), recursive=True)
    print(f"Found {len(fits_files)} FITS files in {fits_dir}.")
    
    for fits_path in fits_files:
        filename = os.path.basename(fits_path)
        # Extract TIC ID (e.g., search for a series of digits in the filename)
        match = re.search(r'_(\d+)-s\d+_', filename)
        if match:
            tic_ids.append(int(match.group(1).lstrip("0") or "0"))
            
    return list(set(tic_ids))

if __name__ == "__main__":
    # Define file paths
    toi_path = "data/toi/toi_catalog.csv"
    eb_path = "data/TESS-EB/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv"
    svc_path = "data/TESS-SVC/hlsp_tess-svc_tess_lcf_acf-s0001-s0026_tess_v1.0_cat.csv"
    
    # Load catalogs
    print("Loading catalogs...")
    toi_df = pd.read_csv(toi_path)
    eb_df = pd.read_csv(eb_path)
    svc_df = pd.read_csv(svc_path)
    
    # Check for downloaded FITS files (light curves)
    # Defaulting to the Downloads folder or a specific target directory
    light_curves_dir = os.path.expanduser("~/Downloads/light_curves")
    downloaded_tics = extract_tics_from_filenames(light_curves_dir)
    
    # Run labeling
    print("Labeling dataset...")
    labeled_df = create_labeled_dataset(toi_df, eb_df, svc_df, downloaded_tics)
    
    # Save the full mapping
    output_path = "data/labeled_targets.csv"
    labeled_df.to_csv(output_path, index=False)
    print(f"Saved full labeled mapping ({len(labeled_df)} entries) to {output_path}")
    
    # Show class counts
    print("\nClass Counts:")
    print(labeled_df['label'].value_counts())
