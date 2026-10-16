"""
Clean packaging script for SIH1639 Final Submission.
Excludes virtual environments, build artifacts, git repositories, and temporary files.
Preserves all source code, trained XGBoost models, datasets, tests, and documentation.
"""
import os
import zipfile
import sys

def package_project(root_dir, output_zip):
    print(f"Creating clean zip archive: {output_zip} from {root_dir}")
    
    exclude_dirs = {
        'venv', '.git', '.pytest_cache', '__pycache__', 
        'build', '.dart_tool', '.idea', '.vscode'
    }
    exclude_extensions = {'.pyc', '.pyo', '.pyd', '.sqlite3-journal', '.log', '.tmp'}
    exclude_files = {
        'AI_Soil_Specific_Fertilizer_Optimizer_Final.zip',
        '.env'  # keep .env.example, exclude actual .env
    }
    
    # Files to specifically ensure are included
    vital_files_found = {
        'models/yield_prediction/yield_model.joblib': False,
        'models/yield_prediction/metadata.json': False,
        'data/agronomy/tnau_stcr_rules.json': False,
        'AUDIT_REPORT.md': False,
        'BUGS_AND_FIXES.md': False,
        'TEST_RESULTS.md': False,
        'FINAL_CHANGELOG.md': False,
        'README.md': False
    }

    total_files = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for current_root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to prune excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Check if current_root itself is inside an excluded directory
            rel_root = os.path.relpath(current_root, root_dir)
            path_parts = rel_root.replace('\\', '/').split('/')
            if any(part in exclude_dirs for part in path_parts):
                continue
            
            for file in files:
                if file in exclude_files:
                    continue
                _, ext = os.path.splitext(file)
                if ext in exclude_extensions:
                    continue
                if file.startswith('.'):
                    if file not in {'.env.example', '.gitignore', '.metadata'}:
                        continue
                
                full_path = os.path.join(current_root, file)
                rel_path = os.path.relpath(full_path, root_dir).replace('\\', '/')
                
                # Check for vital files
                for vfile in vital_files_found:
                    if rel_path.lower() == vfile.lower():
                        vital_files_found[vfile] = True
                
                zipf.write(full_path, arcname=rel_path)
                total_files += 1
                total_uncompressed_bytes += os.path.getsize(full_path)
    
    zip_size = os.path.getsize(output_zip)
    print(f"Archived {total_files} files ({total_uncompressed_bytes / (1024*1024):.2f} MB uncompressed)")
    print(f"Compressed archive size: {zip_size / (1024*1024):.2f} MB")
    
    # Verify vital files
    all_vital_ok = True
    for vfile, found in vital_files_found.items():
        if not found:
            print(f"ERROR: Vital file missing from archive: {vfile}")
            all_vital_ok = False
        else:
            print(f"Verified vital file: {vfile}")
            
    if not all_vital_ok:
        sys.exit(1)
        
    # Verify archive integrity
    with zipfile.ZipFile(output_zip, 'r') as zipf:
        corrupted = zipf.testzip()
        if corrupted:
            print(f"ERROR: Corrupted file in archive: {corrupted}")
            sys.exit(1)
        print("Archive integrity check PASSED successfully.")

if __name__ == '__main__':
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    out = os.path.join(root, 'AI_Soil_Specific_Fertilizer_Optimizer_Final.zip')
    package_project(root, out)
