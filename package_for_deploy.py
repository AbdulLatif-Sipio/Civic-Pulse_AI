import os
import tarfile
import zipfile
import shutil

# Files and directories to exclude from deployment archive
EXCLUDE_DIRS = {
    'venv', '.venv', '__pycache__', '.pytest_cache', '.git', '.idea', '.vscode'
}

EXCLUDE_EXTS = {
    '.pyc', '.pyo', '.pyd'
}

EXCLUDE_FILES = {
    'cleancity.db-shm', 'cleancity.db-wal', 'test_cleancity.db',
    'cleancity_deploy.tar.gz', 'cleancity_deploy.zip'
}

def should_exclude(rel_path: str) -> bool:
    parts = rel_path.replace('\\', '/').split('/')
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    filename = os.path.basename(rel_path)
    if filename in EXCLUDE_FILES:
        return True
    ext = os.path.splitext(filename)[1].lower()
    if ext in EXCLUDE_EXTS:
        return True
    return False

def package_project():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    tar_path = os.path.join(root_dir, 'cleancity_deploy.tar.gz')
    zip_path = os.path.join(root_dir, 'cleancity_deploy.zip')
    
    print(f"Creating deployment package from: {root_dir}")
    
    # Create tar.gz (standard for Linux/Alibaba Cloud ECS)
    count = 0
    with tarfile.open(tar_path, "w:gz") as tar:
        for root, dirs, files in os.walk(root_dir):
            rel_dir = os.path.relpath(root, root_dir)
            if rel_dir != "." and should_exclude(rel_dir):
                dirs[:] = []
                continue
            for f in files:
                rel_file = os.path.relpath(os.path.join(root, f), root_dir)
                if not should_exclude(rel_file):
                    tar.add(os.path.join(root, f), arcname=rel_file)
                    count += 1

    size_mb = os.path.getsize(tar_path) / (1024 * 1024)
    print(f"Deployment tarball created: {tar_path} ({count} files, {size_mb:.2f} MB)")
    return tar_path

if __name__ == '__main__':
    package_project()
