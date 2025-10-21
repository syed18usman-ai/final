#!/usr/bin/env python3

import os
from pathlib import Path
from src.pipeline.ingest import IngestItem, run_ingest
from src.utils.config import load_config
from src.store.chroma_store import ChromaStore

def main():
    print("=== Restoring VTU Study Assistant Data ===")
    
    # Load configuration
    cfg = load_config()
    print(f"Project: {cfg.get('project', {}).get('name', 'Unknown')}")
    
    # Check if we have existing processed data
    processed_dir = Path(cfg["data_dirs"]["processed"])
    if not processed_dir.exists():
        print("❌ No processed data found. Need to run ingestion first.")
        return
    
    print(f"✓ Found processed data at: {processed_dir}")
    
    # Find all PDF files in raw directory
    raw_dir = Path(cfg["data_dirs"]["raw"])
    items = []
    
    print("\n📚 Scanning for PDF files...")
    
    # Check for new structure first: data/raw/<semester>/<subject>/<book>/
    for semester_dir in raw_dir.iterdir():
        if not semester_dir.is_dir():
            continue
            
        semester = semester_dir.name
        print(f"  Semester: {semester}")
        
        for subject_dir in semester_dir.iterdir():
            if not subject_dir.is_dir():
                continue
                
            subject = subject_dir.name
            print(f"    Subject: {subject}")
            
            for book_dir in subject_dir.iterdir():
                if not book_dir.is_dir():
                    continue
                    
                book_title = book_dir.name
                print(f"      Book: {book_title}")
                
                # Find PDF files in this book directory
                for pdf_file in book_dir.glob("*.pdf"):
                    print(f"        📄 Found: {pdf_file.name}")
                    item = IngestItem(
                        subject=subject,
                        semester=semester,
                        book_title=book_title,
                        source_path=str(pdf_file)
                    )
                    items.append(item)
    
    # Fallback: Check for legacy structure: data/raw/<subject>/<semester>/<book>/
    if not items:
        print("No files found in new structure, checking legacy structure...")
        for subject_dir in raw_dir.iterdir():
            if not subject_dir.is_dir():
                continue
                
            subject = subject_dir.name
            print(f"  Subject (legacy): {subject}")
            
            for semester_dir in subject_dir.iterdir():
                if not semester_dir.is_dir():
                    continue
                    
                semester = semester_dir.name
                print(f"    Semester (legacy): {semester}")
                
                for book_dir in semester_dir.iterdir():
                    if not book_dir.is_dir():
                        continue
                        
                    book_title = book_dir.name
                    print(f"      Book (legacy): {book_title}")
                    
                    # Find PDF files in this book directory
                    for pdf_file in book_dir.glob("*.pdf"):
                        print(f"        📄 Found (legacy): {pdf_file.name}")
                        item = IngestItem(
                            subject=subject,
                            semester=semester,
                            book_title=book_title,
                            source_path=str(pdf_file)
                        )
                        items.append(item)
    
    print(f"\n📊 Total PDFs found: {len(items)}")
    
    if not items:
        print("❌ No PDF files found to process.")
        return
    
    # Check existing vector database
    store = ChromaStore(cfg["storage"]["chroma_path"])
    print(f"\n🗄️ Vector database location: {cfg['storage']['chroma_path']}")
    
    # Get current counts
    try:
        text_count = store._text.count()
        image_count = store._image.count()
        print(f"Current database: {text_count} text chunks, {image_count} image chunks")
    except Exception as e:
        print(f"Database check failed: {e}")
        print("This is normal for a fresh database.")
    
    # Ask user if they want to proceed
    print(f"\n🚀 Ready to process {len(items)} PDF files...")
    print("This will extract text and images, create embeddings, and populate the vector database.")
    print("This process may take several minutes depending on the size of the PDFs.")
    
    response = input("\nProceed with data ingestion? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cancelled by user.")
        return
    
    print("\n🔄 Starting data ingestion...")
    try:
        run_ingest(items)
        print("✅ Data ingestion completed successfully!")
        
        # Check final counts
        text_count = store._text.count()
        image_count = store._image.count()
        print(f"\n📊 Final database: {text_count} text chunks, {image_count} image chunks")
        
        if text_count > 0 or image_count > 0:
            print("🎉 System is ready! You can now start the servers.")
        else:
            print("⚠️ No data was ingested. Check the logs for errors.")
            
    except Exception as e:
        print(f"❌ Data ingestion failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
