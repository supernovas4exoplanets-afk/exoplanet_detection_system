# Exoplanet Detection System

A concise guide to the data ingestion, labeling, and signal extraction scripts.

## Code Organization (Script Visibility)
*   **Production Script**:
    *   `src/code/label_creation.py` — Ingests catalogs and creates the unified target mapping.
    *   `src/code/Extract_light_curves.py` — Conditions raw FITS curves (detrends, folds, and runs BLS).
*   **Development Scripts**:
    *   `scratch/` — Contains temporary utilities (e.g. `download_light_curves.py` for downloading test sets from MAST, local tests).

## Target Star Labeling Scheme
The pipeline maps targets into four distinct training classes in `data/labeled_targets.csv` using the following catalog sources:

| Training Class | Name | Catalog Source CSV | Selection Logic |
| :--- | :--- | :--- | :--- |
| **Class 0** | Confirmed Planets | `data/toi/toi_catalog.csv` | Filters for `CP` (Confirmed Planet) and `KP` (Known Planet) in the `tfopwg_disp` column. |
| **Class 1** | Eclipsing Binaries / False Positives | 1. `data/toi/toi_catalog.csv`<br>2. `data/TESS-EB/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv` | Filters for `FP` (False Positive) and `FA` (False Alarm) in the TOI table, plus all targets in the Villanova Eclipsing Binary catalog. |
| **Class 2** | Null / Noise Baseline | Non-catalog stars observed in the target sector | Formed by taking targets observed in TESS Sector 2 and subtracting any ID present in the TOI, EB, or SVC catalogs. |
| **Class 3** | Variable / Other Stars | `data/TESS-SVC/hlsp_tess-svc_tess_lcf_acf-s0001-s0026_tess_v1.0_cat.csv` | Targets listed in the TESS Standard Variable Catalog that do not conflict with Classes 0 or 1. |

*Note: `PC` (Planet Candidate) and `APC` (Ambiguous Planet Candidate) targets are filtered out rn, will have to discuss about it.*

---

## Setup Guide (For New Clones)
If you are setting up the project from scratch, follow these steps:

### 1. Install Dependencies
Make sure you have the following packages installed:
```powershell
pip install numpy matplotlib astropy scipy pandas
```
*(Optional for downloading data)*: `pip install lightkurve astroquery`

### 2. Prepare Data Directories
Since `/data/` is gitignored, create the following directory structure inside the project root:
```
data/
├── toi/
├── TESS-EB/
└── TESS-SVC/
```

### 3. Place Catalogs
Place the three source CSV catalogs inside their respective folders (refer to [data_folder_structure.txt](file:///d:/programming/exoplanet_detection_system/data/data_folder_structure.txt) for the exact layout).
*   **TOI**: Run the gitignored `scratch/download_toi.py` to automatically fetch the official catalog from the NASA Exoplanet Archive.

### 4. Fetch Test Light Curves & Run
1. Run `python scratch/download_light_curves.py` to download a balanced test set of 20 stars per class into `data/light_curves`.
2. Configure `base_dir` in `src/code/Extract_light_curves.py` to point to your light curves directory (e.g. `data/light_curves/` for local testing) and run the script:
```powershell
python src/code/Extract_light_curves.py
```
