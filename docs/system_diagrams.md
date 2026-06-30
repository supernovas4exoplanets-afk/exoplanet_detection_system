# Exoplanet Detection System - Diagram Specifications

This file contains the ASCII art design specifications for the system's operations, software architecture, and front-end interface layout.

---

## 1. Process Flow Diagram (Pipeline Workflow)
This diagram maps the logical data flow from raw ingestion at MAST/TIC databases through conditioning, iterative transit extraction, multimodal classification, and scientific explainability.

```
                    +---------------------------+
                    |    Input Target TIC ID    |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | 1. Data Ingestion         |
                    |    - Ingest FITS via MAST |
                    |    - Ingest stellar metadata|
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | 2. Synthetic Injection    | <--- batman modeling library
                    |    (Validation / Testing) |      (Optional validation step)
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | 3. Signal Conditioning    |
                    |    - Rolling 3-sigma clip | <--- Removes cosmic ray spikes
                    |    - Savitzky-Golay filter| <--- Detrends stellar activity
                    +-------------+-------------+
                                  |
                                  v
       +------------> 4. Feature Extraction     |
       |             - Run BLS Periodogram     | <--- Computes orbital period (P)
       |             +------------+-------------+
       |                          |
       |                          v
       |             +---------------------------+
       |             | 5. Phase Fold & Bin       |
       |             |    - Fold curve around P  |
       |             |    - Bin to 2048 array    |
       |             +------------+-------------+
       |                          |
       |                          v
       |             +---------------------------+
       |             | 6. Multimodal ML Classifier|
       |             |    - 1D CNN (Folded curve)|
       |             |    - Dense (TIC metadata) |
       |             +------------+-------------+
       |                          |
       |                          +---------------------------+
       |                          |                           |
       |                 Classified Class 0 (Planet)   Class 1, 2, or 3
       |                          v                           v
       |             +---------------------------+     +--------------+
       |             | 7. Parametric Fitting     |     | Log results  |
       |             |    - Fit physical radius  |     | & exit       |
       |             +------------+-------------+     +--------------+
       |                          |
       |                          v
       |             +---------------------------+
       |             | 8. Feature Attribution    |
       |             |    - Integrated Gradients | <--- Maps CNN focus areas
       |             +------------+-------------+
       |                          |
       |                          v
  Multi-planet?                   |
  (Iterative BLS)                 |
       |                          v
       +---------------- Mask transit dip
```

---

## 2. Software Architecture Diagram
This diagram outlines the component layout, modules, external dependencies, data storage, and their connectivity.

```
+---------------------------------------------------------------------------------+
|                                PRESENTATION LAYER                               |
|                                                                                 |
|        +---------------------------------------------------------------+        |
|        |                     Streamlit Dashboard App                   |        |
|        |                     (Interactive Web Interface)               |        |
|        +-------------------------------+-------------------------------+        |
+----------------------------------------|----------------------------------------+
                                         |
                                         | Imports & Calls Pipeline
                                         v
+---------------------------------------------------------------------------------+
|                                APPLICATION LAYER                                |
|                                                                                 |
|   +------------------------------------+------------------------------------+   |
|   |                        Pipeline Script Engine                           |   |
|   |                   (src/code/Extract_light_curves.py)                    |   |
|   +------------------------------------+------------------------------------+   |
|        |                          |                              |              |
|        | Imports                  | Invokes                      | Queries      |
|        v                          v                              v              |
|   +------------+            +------------+                 +------------+       |
|   |  PyTorch   |            |  & batman  |                 | & astroquery|      |
|   +----+-------+            +------------+                 +-----+------+       |
+--------|---------------------------------------------------------|--------------+
         | Loads .h5/.pt file                                      | Downloads
         v                                                         v FITS / Metadata
+---------------------------------------------------------------------------------+
|                                  DATABASE LAYER                                 |
|                                                                                 |
|   +------------+            +----------------------------+  +------------+      |
|   | Local CSV  |            |        MAST Server         |  | NASA/VizieR|      |
|   | Storage    |            |      (FITS Repository)     |  | TIC Catalog|      |
|   +------------+            +----------------------------+  +------------+      |
+---------------------------------------------------------------------------------+
```

---

## 3. Streamlit UI Dashboard Wireframe (Mock Visualizer Layout)
This wireframe illustrates the interactive Streamlit web dashboard for loading targets, viewing stellar metadata, evaluating predictions, and visualizing results.

```
===================================================================================
|| [ EXOPLANET TRANSIT SEARCH VISUALIZER (Streamlit) ]               Sector: 02  ||
===================================================================================
|| Target TIC ID: [ 141913160     ] [ Run Pipeline ]  Inference: Class 0         ||
|| Stellar Radius: 0.14 R_sun                         Confidence:99.2% (Planet)  ||
|| Host Stellar Temp: 3000 K                          Est. Rp:   1.08 R_earth    ||
===================================================================================
||                                                                               ||
||  Normalized Detrending Curve (Stage 3)                                        ||
||  1.02 | . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   ||
||  1.00 |______________________   ________________________   ________________   ||
||  0.98 |                      \_/                        \_/                   ||
||       +--------------------------------------------------------------------+  ||
||      0.0                                                                 27.4 ||
||                                  Time (Days)                                  ||
===================================================================================
||                                       ||                                      ||
||  Phase-Folded Transit Fit (Stage 6)   ||  BLS Power Periodogram (Stage 4)     ||
||  1.00 |__________     __________      ||   Power |                            ||
||  0.99 |          \___/                ||         |          |                 ||
||  0.98 |                               ||         |     |    |                 ||
||       +-------------------------      ||         |_____|____|___________      ||
||     -0.05       0.0        0.05       ||        0.5    P    10          50    ||
||             Phase (Days)              ||             Period (Days)            ||
===================================================================================
|| Explainability: Integrated Gradients Feature Attribution Map (Stage 7)        ||
|| Attribution                                                                   ||
||  Score |          ***     ***                                                 ||
||        |         *   *   *   *                                                ||
||        |________*_____*_*_____*____________________________________________   ||
||       -0.05                 0.0                 0.05  (Phase)                 ||
||                                                                               ||
||   Analysis: Integrated Gradients flags transit ingress and egress slopes      ||
||             as the most contributing features to the exoplanet prediction.    ||
===================================================================================
```
