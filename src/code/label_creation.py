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
    Consolidates catalogs to generate a highly detailed labeled dataset 
    preserving all distinct astronomical states.
    
    Classes:
    0: Confirmed Planets (TOI CP/KP)
    1: Planet Candidates (TOI PC/APC)
    2: False Positives / False Alarms (TOI FP/FA)
    3: Eclipsing Binaries (TESS-EB Catalog)
    4: Variable / Pulsating Stars (TESS-SVC Catalog)
    5: Null / Noise Baseline (Unobserved background stars)
    """
    
    # Ensure IDs are integers
    toi_df['tid'] = toi_df['tid'].astype(int)
    eb_df['tess_id'] = eb_df['tess_id'].astype(int)
    svc_df['tess_id'] = svc_df['tess_id'].astype(int)
    
    # ---------------------------------------------------------
    # Step 1: TOI Catalog Processing (Classes 0, 1, 2)
    # ---------------------------------------------------------
    def map_toi_label(disp):
        if disp in ['CP', 'KP']:
            return 0  # Confirmed Planets
        elif disp in ['PC', 'APC']:
            return 1  # Planet Candidates
        elif disp in ['FP', 'FA']:
            return 2  # False Positives / False Alarms
        return None
        
    toi_df['label'] = toi_df['tfopwg_disp'].apply(map_toi_label)
    
    # Drop rows without matching label map
    toi_mapped = toi_df[toi_df['label'].notna()].copy()
    toi_mapped['label'] = toi_mapped['label'].astype(int)
    
    # Dict mapping TIC -> label
    tic_to_label = dict(zip(toi_mapped['tid'], toi_mapped['label']))
    
    # ---------------------------------------------------------
    # Step 2: Eclipsing Binary (EB) Catalog Processing (Class 3)
    # ---------------------------------------------------------
    for tic in eb_df['tess_id']:
        # Assign Class 3 to Eclipsing Binaries
        # If already mapped in TOI, keep the TOI disposition as authority
        if tic not in tic_to_label:
            tic_to_label[tic] = 3

    # ---------------------------------------------------------
    # Step 3: TESS Standard Variable Catalog (SVC) Processing (Class 4)
    # ---------------------------------------------------------
    for tic in svc_df['tess_id']:
        # Assign Class 4 to Variable stars
        # Keep existing TOI or EB classification if there is a collision
        if tic not in tic_to_label:
            tic_to_label[tic] = 4

    # ---------------------------------------------------------
    # Step 4: Establish the Null/Noise Baseline (Class 5)
    # ---------------------------------------------------------
    all_sector_tics = [int(tic) for tic in all_sector_tics]
    for tic in all_sector_tics:
        if tic not in tic_to_label:
            tic_to_label[tic] = 5

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
        match = re.search(r'_(\d+)-s\d+_', filename)
        if match:
            tic_ids.append(int(match.group(1).lstrip("0") or "0"))
            
    return list(set(tic_ids))

if __name__ == "__main__":
    toi_path = "data/toi/toi_catalog.csv"
    eb_path = "data/TESS-EB/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv"
    svc_path = "data/TESS-SVC/hlsp_tess-svc_tess_lcf_acf-s0001-s0026_tess_v1.0_cat.csv"
    
    # Load catalogs
    print("Loading catalogs...")
    toi_df = pd.read_csv(toi_path)
    eb_df = pd.read_csv(eb_path)
    svc_df = pd.read_csv(svc_path)
    
    # Check for downloaded FITS files (light curves)
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
    print(labeled_df['label'].value_counts().sort_index())
