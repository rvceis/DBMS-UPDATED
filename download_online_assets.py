#!/usr/bin/env python3
"""
Online Asset Downloader - Download 3D models, datasets, and code from online sources
Integrates with popular repositories
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List


class OnlineAssetDownloader:
    """Download assets from online repositories"""
    
    def __init__(self, download_dir: str = "./downloaded_assets"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    @staticmethod
    def download_file(url: str, filepath: Path, timeout: int = 30) -> bool:
        """Download file from URL"""
        try:
            print(f"⏳ Downloading from {url[:60]}...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"  ⏳ Progress: {percent:.1f}%", end='\r')
                
                print(f"\n✅ Downloaded: {filepath.name}")
                return True
        
        except urllib.error.URLError as e:
            print(f"❌ Download failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def download_github_file(self, repo: str, filepath: str, 
                           branch: str = "main") -> Optional[Path]:
        """Download single file from GitHub
        
        Args:
            repo: GitHub repo (user/repo)
            filepath: Path within repo
            branch: Branch name (main, master, etc.)
        
        Example:
            downloader.download_github_file(
                "tensorflow/tensorflow",
                "README.md"
            )
        """
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{filepath}"
        filename = Path(filepath).name
        output_path = self.download_dir / f"{repo.split('/')[1]}_{filename}"
        
        if self.download_file(url, output_path):
            return output_path
        return None
    
    def download_github_repo(self, repo: str, filetype: str = ".py") -> Optional[Path]:
        """Download filtered files from GitHub repo
        
        Args:
            repo: GitHub repo (user/repo)
            filetype: File extension to download (.py, .js, .json, etc.)
        
        Returns:
            Path to downloaded directory
        """
        try:
            # Create repo directory
            repo_name = repo.split('/')[-1]
            repo_dir = self.download_dir / repo_name
            repo_dir.mkdir(exist_ok=True)
            
            print(f"📦 Downloading {repo} files (type: {filetype})...")
            
            # Get API response
            api_url = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
            request = urllib.request.Request(api_url, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    
                    if 'tree' not in data:
                        print(f"⚠️  Could not fetch repo tree")
                        return repo_dir
                    
                    # Filter files
                    matching_files = [
                        f for f in data['tree']
                        if f['type'] == 'blob' and f['path'].endswith(filetype)
                    ][:5]  # Limit to 5 files
                    
                    print(f"📄 Found {len(matching_files)} files to download")
                    
                    downloaded_count = 0
                    for file_obj in matching_files:
                        try:
                            file_url = file_obj['url'].replace(
                                'https://api.github.com/repos',
                                'https://raw.githubusercontent.com'
                            ).replace('/git/blobs/', '/') + '?raw=true'
                            
                            file_path = repo_dir / Path(file_obj['path']).name
                            
                            if self.download_file(file_url, file_path):
                                downloaded_count += 1
                        
                        except Exception as e:
                            print(f"  ⚠️  Error downloading {file_obj['path']}: {e}")
                    
                    print(f"✅ Downloaded {downloaded_count} files to {repo_dir}")
                    return repo_dir
            
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print(f"⚠️  Repository not found or tree is too large")
                else:
                    print(f"⚠️  Error: {e}")
                return repo_dir
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def download_kaggle_dataset_info(self, dataset: str) -> dict:
        """Get info about Kaggle dataset (requires kaggle CLI)
        
        Dataset format: username/dataset-name
        Example: tedlim/titanic
        """
        try:
            # Check if kaggle CLI is available
            import subprocess
            
            print(f"📊 Kaggle dataset: {dataset}")
            print("ℹ️  To download, install: pip install kaggle")
            print(f"   Then run: kaggle datasets download -d {dataset}")
            
            return {
                "dataset": dataset,
                "download_command": f"kaggle datasets download -d {dataset}",
                "extract_command": f"unzip {dataset.split('/')[1]}.zip"
            }
        
        except Exception as e:
            print(f"ℹ️  Kaggle CLI not installed")
            return {"info": "Install kaggle CLI to download datasets"}
    
    def create_sample_datasets(self) -> List[Path]:
        """Create sample CSV and JSON files for testing"""
        print("\n📝 Creating sample datasets...")
        
        samples = []
        
        # Sample CSV
        csv_file = self.download_dir / "sample_data.csv"
        with open(csv_file, 'w') as f:
            f.write("id,name,age,city,salary\n")
            f.write("1,Alice,28,New York,75000\n")
            f.write("2,Bob,32,San Francisco,95000\n")
            f.write("3,Charlie,26,Boston,65000\n")
            f.write("4,Diana,30,Seattle,85000\n")
            f.write("5,Eve,29,Austin,72000\n")
        print(f"✅ Created: {csv_file}")
        samples.append(csv_file)
        
        # Sample JSON
        json_file = self.download_dir / "sample_data.json"
        data = [
            {"id": 1, "name": "Product A", "price": 99.99, "stock": 50},
            {"id": 2, "name": "Product B", "price": 149.99, "stock": 30},
            {"id": 3, "name": "Product C", "price": 199.99, "stock": 0},
        ]
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Created: {json_file}")
        samples.append(json_file)
        
        # Sample JSONL (newline-delimited JSON)
        jsonl_file = self.download_dir / "sample_data.jsonl"
        with open(jsonl_file, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        print(f"✅ Created: {jsonl_file}")
        samples.append(jsonl_file)
        
        return samples


def interactive_downloader():
    """Interactive downloader menu"""
    
    print("\n" + "=" * 70)
    print("ONLINE ASSET DOWNLOADER")
    print("=" * 70)
    
    downloader = OnlineAssetDownloader()
    
    while True:
        print("\n📚 Options:")
        print("1. Download sample datasets")
        print("2. Download GitHub repository (Python files)")
        print("3. Download GitHub file")
        print("4. Get Kaggle dataset info")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            files = downloader.create_sample_datasets()
            print(f"\n✅ Created {len(files)} sample files")
        
        elif choice == "2":
            repo = input("GitHub repo (user/repo): ").strip()
            if repo:
                downloader.download_github_repo(repo, ".py")
        
        elif choice == "3":
            repo = input("GitHub repo (user/repo): ").strip()
            filepath = input("File path in repo: ").strip()
            if repo and filepath:
                result = downloader.download_github_file(repo, filepath)
                if result:
                    print(f"✅ Downloaded to: {result}")
        
        elif choice == "4":
            dataset = input("Kaggle dataset (user/dataset): ").strip()
            if dataset:
                info = downloader.download_kaggle_dataset_info(dataset)
                print(json.dumps(info, indent=2))
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    interactive_downloader()
