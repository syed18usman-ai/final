#!/usr/bin/env python3

import os
from pathlib import Path
from src.pipeline.ingest import IngestItem, run_ingest

def main():
    print("=== Re-ingesting all PDF data ===")
    
    # Find all PDF files in the data/raw directory
    raw_dir = Path("data/raw")
    items = []
    
    # Check for new structure first: data/raw/<semester>/<subject>/<book>/
    for semester_dir in raw_dir.iterdir():
        if not semester_dir.is_dir():
            continue
            
        semester = semester_dir.name
        print(f"Processing semester: {semester}")
        
        for subject_dir in semester_dir.iterdir():
            if not subject_dir.is_dir():
                continue
                
            subject = subject_dir.name
            print(f"  Processing subject: {subject}")
            
            for book_dir in subject_dir.iterdir():
                if not book_dir.is_dir():
                    continue
                    
                book_title = book_dir.name
                print(f"    Processing book: {book_title}")
                
                # Find PDF files in this book directory
                for pdf_file in book_dir.glob("*.pdf"):
                    print(f"      Found PDF: {pdf_file.name}")
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
            print(f"Processing subject (legacy): {subject}")
            
            for semester_dir in subject_dir.iterdir():
                if not semester_dir.is_dir():
                    continue
                    
                semester = semester_dir.name
                print(f"  Processing semester (legacy): {semester}")
                
                for book_dir in semester_dir.iterdir():
                    if not book_dir.is_dir():
                        continue
                        
                    book_title = book_dir.name
                    print(f"    Processing book (legacy): {book_title}")
                    
                    # Find PDF files in this book directory
                    for pdf_file in book_dir.glob("*.pdf"):
                        print(f"      Found PDF (legacy): {pdf_file.name}")
                        item = IngestItem(
                            subject=subject,
                            semester=semester,
                            book_title=book_title,
                            source_path=str(pdf_file)
                        )
                        items.append(item)
    
    print(f"\nTotal items to process: {len(items)}")
    
    if items:
        print("Starting ingestion process...")
        run_ingest(items)
        print("Ingestion completed!")
    else:
        print("No PDF files found to process.")

if __name__ == "__main__":
    main()
