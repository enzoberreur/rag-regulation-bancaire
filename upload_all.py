#!/usr/bin/env python3
"""
Script pour uploader tous les documents du dossier data/ vers le RAG
"""
import requests
import os
import time
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/api/documents/upload"
DATA_DIR = Path(__file__).parent / "data"

def upload_document(file_path: Path) -> bool:
    """Upload un document vers le RAG"""
    try:
        print(f"📤 Uploading {file_path.name}...")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/pdf')}
            response = requests.post(API_URL, files=files, timeout=300)
        
        if response.status_code == 200:
            print(f"✅ {file_path.name} uploaded successfully!")
            return True
        else:
            print(f"❌ Failed to upload {file_path.name}: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading {file_path.name}: {str(e)}")
        return False

def main():
    print("🚀 Starting batch upload to RAG...")
    print(f"📁 Looking for PDFs in: {DATA_DIR}")
    
    # Vérifier que le dossier existe
    if not DATA_DIR.exists():
        print(f"❌ Directory not found: {DATA_DIR}")
        return
    
    # Trouver tous les PDFs
    pdf_files = list(DATA_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No PDF files found in data/")
        return
    
    print(f"📊 Found {len(pdf_files)} PDF files")
    print("-" * 60)
    
    # Attendre que le backend soit prêt
    print("⏳ Waiting for backend to be ready...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                break
        except:
            time.sleep(1)
    else:
        print("⚠️  Backend might not be ready, but continuing anyway...")
    
    print("-" * 60)
    
    # Upload chaque fichier
    success_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        print(f"   Size: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        if upload_document(pdf_file):
            success_count += 1
        else:
            failed_count += 1
        
        # Petite pause entre les uploads
        if i < len(pdf_files):
            time.sleep(2)
    
    # Résumé
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    print(f"⏱️  Average per file: {elapsed_time/len(pdf_files):.2f} seconds")
    print("=" * 60)

if __name__ == "__main__":
    main()
