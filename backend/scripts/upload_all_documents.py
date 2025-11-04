#!/usr/bin/env python3
"""
Script to upload all documents from the data directory to the RAG system.
This script processes documents with progress tracking and error handling.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from typing import List


async def upload_document(client: httpx.AsyncClient, file_path: Path) -> dict:
    """Upload a single document to the API."""
    print(f"\n📤 Uploading: {file_path.name}")
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        response = await client.post(
            "http://localhost:8000/api/documents/",
            files=files,
            timeout=300.0,  # 5 minutes timeout for large files
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Uploaded successfully (ID: {data['id']})")
        return data
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        return None


async def main():
    """Upload all PDF documents from the data directory."""
    # Path to data directory
    data_dir = Path(__file__).parent.parent.parent / "data"
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Find all PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {data_dir}")
        return
    
    print(f"🔍 Found {len(pdf_files)} PDF files to upload")
    print(f"📁 Directory: {data_dir}")
    print("\n" + "="*60)
    
    # Upload documents
    async with httpx.AsyncClient() as client:
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            try:
                result = await upload_document(client, pdf_file)
                results.append((pdf_file.name, result is not None))
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                results.append((pdf_file.name, False))
    
    # Summary
    print("\n" + "="*60)
    print("\n📊 UPLOAD SUMMARY")
    print("="*60)
    
    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful
    
    print(f"\n✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    
    if failed > 0:
        print("\n⚠️  Failed files:")
        for filename, success in results:
            if not success:
                print(f"   - {filename}")
    
    print("\n" + "="*60)
    print("\n💡 Note: Check the backend logs for detailed processing progress")
    print("   The system uses optimized batch processing (32 chunks at a time)")
    print("   Large documents may take a few minutes to process.\n")


if __name__ == "__main__":
    asyncio.run(main())
