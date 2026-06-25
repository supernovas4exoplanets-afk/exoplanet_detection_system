from lightkurve import search_lightcurve
import pandas as pd
import numpy as np

df_toi = pd.read_csv("TOI_catalog.csv")

X = []
y = []
metadata = []

PLANET = ['PC', 'CP', 'KP']
NOT_PLANET = ['FP', 'FA']

successful = 0
failed = 0

for _, row in df_toi.iterrows():
    if row["tfopwg_disp"] in PLANET:
        LABEL = 1
    elif row["tfopwg_disp"] in NOT_PLANET:
        LABEL = 0
    else:
        continue
    try:
        search_result = search_lightcurve(
            f"TIC {int(row['tid'])}",
            mission="TESS",
            author="SPOC"
        )

        if len(search_result) == 0:
            raise Exception("No light curve found")

        lcs = search_result.download_all()

        if lcs is None or len(lcs) == 0:
            raise Exception("Download failed")

        lc = lcs.stitch()
        lc = lc.remove_nans()

        period = row["pl_orbper"]

        # TOI epochs are usually BJD
        epoch = row["pl_tranmid"] - 2457000

        folded = lc.fold(
            period=period,
            epoch_time=epoch
        )

        folded = folded.bin(bins=256)

        flux = folded.flux.value

        # Ensure exactly 256 values
        if len(flux) != 256:
            raise Exception(f"Unexpected length {len(flux)}")

        # Skip NaN curves
        if np.isnan(flux).any():
            raise Exception("NaNs after binning")

        X.append(flux)
        y.append(LABEL)

        metadata.append({
            "tic_id": row["tid"],
            "period": period,
            "epoch": epoch,
            "duration_hr": row["pl_trandurh"],
            "depth_ppm": row["pl_trandep"],
            "label": LABEL
        })

        successful += 1

        print(
            f"[{successful}] Done TIC {row['tid']}"
        )

        # Save intermediate progress
        if successful % 100 == 0:

            np.save(
                "X.npy",
                np.array(X, dtype=np.float32)
            )

            np.save(
                "y.npy",
                np.array(y, dtype=np.int32)
            )

            pd.DataFrame(metadata).to_csv(
                "metadata.csv",
                index=False
            )

            print(
                f"Checkpoint saved ({successful} samples)"
            )

    except Exception as e:

        failed += 1

        print(
            f"Failed TIC {row['tid']}: {e}"
        )

# Final save

np.save(
    "X.npy",
    np.array(X, dtype=np.float32)
)

np.save(
    "y.npy",
    np.array(y, dtype=np.int32)
)

pd.DataFrame(metadata).to_csv(
    "metadata.csv",
    index=False
)

print("\nFinished")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"Dataset shape: {np.array(X).shape}")