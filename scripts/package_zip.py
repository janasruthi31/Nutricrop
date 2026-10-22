import os
import zipfile
import sys

def package_project():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    zip_name = "AI_Soil_Specific_Fertilizer_Optimizer_Final.zip"
    zip_path = os.path.join(base_dir, zip_name)

    exclude_dirs = {
        ".git",
        ".dart_tool",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".vscode",
        ".idea",
        ".pub-cache",
        ".pub"
    }
    exclude_files = {
        zip_name,
        ".env",
        ".DS_Store",
        "Thumbs.db",
        "package_zip.py"  # optional
    }
    exclude_exts = {".pyc", ".pyo", ".pyd", ".log"}

    print(f"Creating clean release ZIP: {zip_path}")
    count = 0
    total_bytes = 0

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]

            rel_root = os.path.relpath(root, base_dir)
            if rel_root != "." and any(part in exclude_dirs or part.startswith(".") for part in rel_root.split(os.sep)):
                continue

            for file in files:
                if file in exclude_files:
                    continue
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                if file.startswith(".env") and file != ".env.example":
                    continue

                full_path = os.path.join(root, file)
                if rel_root != ".":
                    clean_rel = rel_root.replace(os.sep, "/")
                    arc_name = f"AI_Soil_Specific_Fertilizer_Optimizer/{clean_rel}/{file}"
                else:
                    arc_name = f"AI_Soil_Specific_Fertilizer_Optimizer/{file}"

                zipf.write(full_path, arc_name)
                count += 1
                total_bytes += os.path.getsize(full_path)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    total_size_mb = total_bytes / (1024 * 1024)

    print(f"Packaging SUCCESS!")
    print(f"Total files included: {count}")
    print(f"Uncompressed size: {total_size_mb:.2f} MB")
    print(f"Final ZIP size: {zip_size_mb:.2f} MB")
    print(f"ZIP path: {zip_path}")

    # Validation
    print("\nValidating ZIP archive integrity...")
    with zipfile.ZipFile(zip_path, "r") as test_zip:
        bad_file = test_zip.testzip()
        if bad_file:
            print(f"ERROR: Corrupted file detected in ZIP: {bad_file}")
            sys.exit(1)
        namelist = test_zip.namelist()
        print(f"Integrity check passed! {len(namelist)} entries tested without error.")

        # Check critical files
        critical_files = [
            "AI_Soil_Specific_Fertilizer_Optimizer/README.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/SETUP_AND_RUN.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/docs/historical_audits/PROJECT_AUDIT_REPORT.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/docs/historical_audits/BUG_FIX_REPORT.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/docs/historical_audits/TEST_RESULTS.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/API_ENDPOINTS.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/docs/historical_audits/DATASET_AND_MODEL_PROVENANCE.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/AGRONOMIC_RULE_SOURCES.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/KNOWN_LIMITATIONS.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/RELEASE_NOTES.md",
            "AI_Soil_Specific_Fertilizer_Optimizer/.env.example",
            "AI_Soil_Specific_Fertilizer_Optimizer/requirements.txt",
            "AI_Soil_Specific_Fertilizer_Optimizer/data/agronomy/tnau_stcr_rules.json",
            "AI_Soil_Specific_Fertilizer_Optimizer/data/tn_district_yield_model_dataset.csv",
            "AI_Soil_Specific_Fertilizer_Optimizer/models/yield_prediction/yield_model.joblib",
            "AI_Soil_Specific_Fertilizer_Optimizer/flutter_app/pubspec.yaml",
            "AI_Soil_Specific_Fertilizer_Optimizer/flutter_app/lib/main.dart",
            "AI_Soil_Specific_Fertilizer_Optimizer/phase3_soil/main.py",
            "AI_Soil_Specific_Fertilizer_Optimizer/phase5_nutrient/service.py",
            "AI_Soil_Specific_Fertilizer_Optimizer/phase6_fertilizer/service.py",
            "AI_Soil_Specific_Fertilizer_Optimizer/phase7_integration/extra_api.py"
        ]

        missing = [f for f in critical_files if f not in namelist]
        if missing:
            print(f"ERROR: Critical files missing from ZIP: {missing}")
            sys.exit(1)
        print("All critical files verified present in archive!")

        # Verify no secrets
        for name in namelist:
            if name.endswith("/.env") or name == "AI_Soil_Specific_Fertilizer_Optimizer/.env":
                print(f"ERROR: Private .env file detected in ZIP: {name}")
                sys.exit(1)
        print("Verified: No secret files or .env files found in archive!")

if __name__ == "__main__":
    package_project()
