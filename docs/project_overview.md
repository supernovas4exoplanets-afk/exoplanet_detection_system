# Exoplanet Detection System - Project Overview

A concise guide to the data ingestion, labeling, signal conditioning, feature extraction, multimodal classification, and explainability scripts.

---

## 1. Problem Statement & Objectives
Develop an AI-based data analysis pipeline capable of automatically detecting exoplanet transit signals from noisy astronomical light curve data.

**Key Requirements:**
- Categorize targets into four training classes: Confirmed Planets, Eclipsing Binaries, Null/Noise, and Variable Stars.
- Correctly filter out unverified planet candidates to maintain clean label sets.
- Estimate orbital parameters (transit period, depth, and duration).
- Implement explainability to verify network decision-making on genuine transits.

---

## 2. Target Star Labeling Scheme
The pipeline maps targets into four distinct training classes in `data/labeled_targets.csv` using the following catalog sources:

| Training Class | Name | Catalog Source CSV | Selection Logic |
| :--- | :--- | :--- | :--- |
| **Class 0** | Confirmed Planets | `data/toi/toi_catalog.csv` | Filters for `CP` (Confirmed Planet) and `KP` (Known Planet) in the `tfopwg_disp` column. |
| **Class 1** | Eclipsing Binaries / False Positives | 1. `data/toi/toi_catalog.csv`<br>2. `data/TESS-EB/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv` | Filters for `FP` (False Positive) and `FA` (False Alarm) in the TOI table, plus all targets in the Villanova Eclipsing Binary catalog. |
| **Class 2** | Null / Noise Baseline | Non-catalog stars observed in the target sector | Formed by taking targets observed in TESS Sector 2 and subtracting any ID present in the TOI, EB, or SVC catalogs. |
| **Class 3** | Variable / Other Stars | `data/TESS-SVC/hlsp_tess-svc_tess_lcf_acf-s0001-s0026_tess_v1.0_cat.csv` | Targets listed in the TESS Standard Variable Catalog that do not conflict with Classes 0 or 1. |

*Critical Constraint: `PC` (Planet Candidate) and `APC` (Ambiguous Planet Candidate) targets are strictly filtered out to prevent label noise during training.*

---

## 3. Multimodal Pipeline Workflow (7-Stage Process)
The pipeline is designed to process raw TESS light curves and scalar stellar metadata through 7 sequential stages:

```
+-----------------------------------------------------------------------------+
| Stage 1: Data Ingestion & Contextualization (Lightkurve + TIC query)        |
+------------------------------------+----------------------------------------+
                                     |
                                     v
+------------------------------------+----------------------------------------+
| Stage 2: Synthetic Data Generation (batman transit injection + noise)        |
+------------------------------------+----------------------------------------+
                                     |
                                     v
+------------------------------------+----------------------------------------+
| Stage 3: Signal Conditioning (Sigma clipping & Savitzky-Golay flattening)    |
+------------------------------------+----------------------------------------+
                                     |
                                     v
+------------------------------------+----------------------------------------+
| Stage 4: Feature Extraction (BLS Periodogram + Iterative masking + folding)  |
+------------------------------------+----------------------------------------+
                                     |
                                     v
+------------------------------------+----------------------------------------+
| Stage 5: Multimodal CNN Classification (Phase-folded curve + Stellar metadata)|
+------------------------------------+----------------------------------------+
                                     |
                                     v
+------------------------------------+----------------------------------------+
| Stage 6: Parametric Fitting & Science Extraction (Depth, duration, period)  |
+------------------------------------+----------------------------------------+
                                     |
                                     v
+------------------------------------+----------------------------------------+
| Stage 7: Feature Attribution / XAI (Explainability via Integrated Gradients)  |
+-----------------------------------------------------------------------------+
```

1. **Stage 1 (Ingestion):** Fetch time-series (`PDCSAP_FLUX`) and stellar metadata ($R_*$, $T_{eff}$, $\log(g)$) from MAST and TIC.
2. **Stage 2 (Simulation):** Create synthetic transits with `batman` to simulate edge cases and map detection completeness.
3. **Stage 3 (Conditioning):** Clean cosmic rays ($\sigma$-clipping) and flatten the baseline using a Savitzky-Golay filter.
4. **Stage 4 (Extraction):** Run Box Least Squares (BLS) to extract candidate period ($P$), transit duration, and depth. Uses **Iterative BLS** to sequentially mask transits for multi-planet searches.
5. **Stage 5 (Classification):** Ingest 2048-point binned phase-folded light curves (via 1D CNN) and scalar metadata (via Dense layers) and output a Softmax distribution.
6. **Stage 6 (Extraction):** Extract planetary parameters and compute physical planetary radius ($R_p = R_* \sqrt{\delta}$), applying age-dependent contraction scaling factors.
7. **Stage 7 (Explainability):** Apply **Integrated Gradients** to generate attribution maps on the light curve, verifying CNN focus areas.

---

## 4. Code Organization (Script Visibility)
*   **Production Scripts (`src/code/`)**:
    *   `label_creation.py` — Handles ingestion of TOI, EB, and SVC catalogs, implements catalog overlap resolution, establishes the Class 2 baseline, balances classes, and saves the final target-labels matrix.
    *   `Extract_light_curves.py` — Ingests target light curves, implements sigma clipping, detrending, runs BLS/Iterative BLS, folds the curves, bins them into 2048-point arrays, and extracts orbital metrics.
*   **Development Scripts (`scratch/`)**:
    *   Contains helper scripts like `download_toi.py` (fetching catalog data programmatically from NASA Exoplanet Archive) and `download_light_curves.py` (downloading sample FITS sets from MAST).

---

## 5. Technology Stack
The solution is built using the following core libraries and frameworks:

*   **Data Science Core:** `Python`, `NumPy` (array math), `pandas` (catalog indexing & merging), `SciPy` (statistical processing and signal detrending).
*   **Astro-Data Utilities:** `astropy` (specifically `BoxLeastSquares` and `transit_mask` for transit searches), `lightkurve` (TESS FITS extraction and parsing), `astroquery` (archive search queries).
*   **Physics Modeling:** `batman` (Transit model calculations and limb-darkening estimations).
*   **Deep Learning & Evaluation:** `TensorFlow`/`Keras` or `PyTorch` (dual-stream CNN + Dense networks), `scikit-learn` (implementing `GroupKFold` grouped by `TIC_ID` to prevent leakage and computing verification metrics).
*   **Interpretability:** `Integrated Gradients` (attribution scoring).
*   **Visualization:** `Matplotlib` (generating diagnostic and phase-folded plots).

---

## 6. Setup Guide (For New Clones)
If you are setting up the project from scratch, follow these steps:

### 1. Install Dependencies
Make sure you have the following packages installed:
```powershell
pip install numpy matplotlib astropy scipy pandas lightkurve astroquery
```
*(For synthetic generation and modeling, install batman)*:
```powershell
pip install batman-package
```

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
- **TOI**: Run `python scratch/download_toi.py` to automatically fetch the official catalog from the NASA Exoplanet Archive.

### 4. Fetch Test Light Curves & Run
1. Run `python scratch/download_light_curves.py` to download a balanced test set of 20 stars per class into `data/light_curves`.
2. Configure `base_dir` in `src/code/Extract_light_curves.py` to point to your light curves directory (e.g. `data/light_curves/` for local testing) and run the script:
```powershell
python src/code/Extract_light_curves.py
```
