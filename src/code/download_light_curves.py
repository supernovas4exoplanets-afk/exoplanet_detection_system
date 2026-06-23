import pandas as pd
import os
import subprocess
import sys

# Ensure required libraries are installed
try:
    import lightkurve as lk
    from astroquery.mast import Observations
except ImportError:
    print("Installing lightkurve and astroquery...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lightkurve", "astroquery"])
    import lightkurve as lk
    from astroquery.mast import Observations

# Paths
labeled_csv_path = "data/labeled_targets.csv"
output_fits_dir = "data/light_curves"
os.makedirs(output_fits_dir, exist_ok=True)

# Load target list
print(f"Loading target list from {labeled_csv_path}...")
df = pd.read_csv(labeled_csv_path)

# Target Sector
sector = 2
sample_size_per_class = 20

print("Querying MAST in bulk for all TESS Sector 2 observations to speed up downloads...")
try:
    obs = Observations.query_criteria(obs_collection="TESS", sequence_number=sector, project="TESS")
    obs_tics = set()
    for name in obs['target_name']:
        if str(name).isdigit():
            obs_tics.add(int(name))
    print(f"Found {len(obs_tics)} unique TIC IDs observed in Sector {sector}.")
except Exception as e:
    print(f"Failed to query MAST bulk observations: {e}")
    sys.exit(1)

# Categorize candidates that are observed in Sector 2
class0_candidates = list(set(df[df['label'] == 0]['TIC_ID']).intersection(obs_tics))
class1_candidates = list(set(df[df['label'] == 1]['TIC_ID']).intersection(obs_tics))
class3_candidates = list(set(df[df['label'] == 3]['TIC_ID']).intersection(obs_tics))

# Class 2 (Noise) candidates are stars observed in Sector 2 that are NOT in our labeled targets catalog
class2_candidates = list(obs_tics - set(df['TIC_ID']))

print(f"\nSector 2 Overlap Candidates:")
print(f"  Class 0 (Confirmed Planets): {len(class0_candidates)}")
print(f"  Class 1 (False Positives):   {len(class1_candidates)}")
print(f"  Class 3 (Variables):         {len(class3_candidates)}")
print(f"  Class 2 (Noise Baseline):    {len(class2_candidates)}")

downloaded_info = []

def download_class_stars(tic_list, label, max_download):
    downloaded_count = 0
    for tic in tic_list:
        if downloaded_count >= max_download:
            break
        tic_str = f"TIC {tic}"
        print(f"Downloading {tic_str} for Class {label}...")
        try:
            search_result = lk.search_lightcurve(tic_str, sector=sector, author="SPOC")
            if len(search_result) > 0:
                # Download lightcurve to output_fits_dir
                search_result.download(download_dir=output_fits_dir)
                downloaded_info.append({"TIC_ID": int(tic), "label": label})
                downloaded_count += 1
            else:
                print(f"  No SPOC light curve found for {tic_str}")
        except Exception as e:
            print(f"  Failed to download {tic_str}: {e}")
    return downloaded_count

print("\n--- Downloading Class 0 (Confirmed Planets) ---")
download_class_stars(class0_candidates, 0, sample_size_per_class)

print("\n--- Downloading Class 1 (False Positives) ---")
download_class_stars(class1_candidates, 1, sample_size_per_class)

print("\n--- Downloading Class 3 (Variable Stars) ---")
download_class_stars(class3_candidates, 3, sample_size_per_class)

print("\n--- Downloading Class 2 (Noise Baseline) ---")
download_class_stars(class2_candidates, 2, sample_size_per_class)

print("\nDownload Summary:")
downloaded_df = pd.DataFrame(downloaded_info)
if not downloaded_df.empty:
    print(downloaded_df['label'].value_counts())
    downloaded_df.to_csv("data/downloaded_mapping.csv", index=False)
    print("Saved downloaded mapping to data/downloaded_mapping.csv")
else:
    print("No files downloaded.")
