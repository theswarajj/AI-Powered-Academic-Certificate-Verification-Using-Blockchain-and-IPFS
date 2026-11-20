"""
STEP 4: Train the Fraud Detection Model.

Standalone script — generates a synthetic training dataset (12 features,
matching Step 3's feature vector exactly) and trains a RandomForest
classifier on it, saving the result to model.pkl.

Why synthetic data: there is no real, labeled, publicly available dataset
of genuine vs. fraudulent academic certificates anywhere — this is a niche
enough problem that nobody has built and released one. Generating
synthetic feature vectors that approximate what genuine vs. tampered
certificates look like is a legitimate, defensible bootstrapping approach
for a student project, as long as you say so plainly in your report
(this docstring is basically that statement, reused).

Run it with:
    python step4_train_model.py

Produces: model.pkl (in the same folder)
"""
import subprocess
import sys


def ensure_package_installed(package_name: str, import_name: str = None):
    import_name = import_name or package_name
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"[..] Installing '{package_name}'...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[FAIL] Could not install '{package_name}': {result.stderr[-1000:]}")
            return False
        print(f"[OK] '{package_name}' installed.")
        return True


for pkg, mod in [("scikit-learn", "sklearn"), ("pandas", "pandas"), ("numpy", "numpy"), ("joblib", "joblib")]:
    if not ensure_package_installed(pkg, mod):
        sys.exit(1)

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

# Must match Step 3's FEATURE_NAMES exactly, same order.
FEATURE_NAMES = [
    "missing_field_count", "ocr_avg_confidence", "register_number_format_valid",
    "certificate_id_format_valid", "issue_date_valid", "issue_date_plausible_range",
    "institution_name_match_score", "text_block_count", "text_position_variance",
    "font_height_variance", "degree_field_recognized", "ela_unevenness_score",
]

RNG = np.random.default_rng(42)


def _genuine_sample():
    return {
        "missing_field_count": RNG.choice([0, 0, 0, 1], p=[0.85, 0.05, 0.05, 0.05]),
        "ocr_avg_confidence": np.clip(RNG.normal(85, 6), 40, 100),
        "register_number_format_valid": RNG.choice([1.0, 0.0], p=[0.95, 0.05]),
        "certificate_id_format_valid": RNG.choice([1.0, 0.0], p=[0.95, 0.05]),
        "issue_date_valid": RNG.choice([1.0, 0.0], p=[0.97, 0.03]),
        "issue_date_plausible_range": RNG.choice([1.0, 0.0], p=[0.97, 0.03]),
        "institution_name_match_score": np.clip(RNG.normal(85, 12), 0, 100),
        "text_block_count": np.clip(RNG.normal(9, 3), 4, 30),
        "text_position_variance": np.clip(RNG.normal(18000, 4000), 500, 40000),
        "font_height_variance": np.clip(RNG.normal(50, 20), 0, 150),
        "degree_field_recognized": RNG.choice([1.0, 0.0], p=[0.96, 0.04]),
        "ela_unevenness_score": np.clip(RNG.normal(4.3, 1.0), 0, 15),
    }


def _tampered_sample():
    return {
        "missing_field_count": RNG.choice([0, 1, 2, 3], p=[0.3, 0.3, 0.25, 0.15]),
        "ocr_avg_confidence": np.clip(RNG.normal(60, 15), 10, 100),
        "register_number_format_valid": RNG.choice([1.0, 0.0], p=[0.5, 0.5]),
        "certificate_id_format_valid": RNG.choice([1.0, 0.0], p=[0.45, 0.55]),
        "issue_date_valid": RNG.choice([1.0, 0.0], p=[0.6, 0.4]),
        "issue_date_plausible_range": RNG.choice([1.0, 0.0], p=[0.65, 0.35]),
        "institution_name_match_score": np.clip(RNG.normal(45, 20), 0, 100),
        "text_block_count": np.clip(RNG.normal(7, 4), 2, 30),
        "text_position_variance": np.clip(RNG.normal(35000, 8000), 500, 60000),
        "font_height_variance": np.clip(RNG.normal(110, 40), 0, 250),
        "degree_field_recognized": RNG.choice([1.0, 0.0], p=[0.6, 0.4]),
        "ela_unevenness_score": np.clip(RNG.normal(7.5, 2.0), 0, 20),
    }


def generate_dataset(n_genuine=600, n_fraud=400) -> pd.DataFrame:
    rows = []
    for _ in range(n_genuine):
        s = _genuine_sample(); s["label"] = 0; rows.append(s)
    for _ in range(n_fraud):
        s = _tampered_sample(); s["label"] = 1; rows.append(s)
    df = pd.DataFrame(rows)[FEATURE_NAMES + ["label"]]
    return df.sample(frac=1, random_state=42).reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 4: Training the Fraud Detection Model")
    print("=" * 60)

    print("\nGenerating synthetic training dataset...")
    df = generate_dataset()
    df.to_csv("synthetic_dataset.csv", index=False)
    print(f"Generated {len(df)} rows (600 genuine, 400 suspicious)")

    X, y = df[FEATURE_NAMES], df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    print("\nTraining RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=5,
        random_state=42, class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("\n--- Classification report (held-out test set) ---")
    print(classification_report(y_test, y_pred, target_names=["genuine", "suspicious"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    print("\n--- Feature importances ---")
    for name, imp in sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {name:35s}: {imp:.4f}")

    joblib.dump(model, "model.pkl")
    print("\n" + "=" * 60)
    print("SUCCESS — model.pkl saved in this folder.")
    print("Reminder: this model is trained on SYNTHETIC data, not real")
    print("certificates. State this plainly in your report.")
    print("=" * 60)