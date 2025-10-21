#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

def migrate_data_structure():
    """
    Migrate data structure from:
    data/raw/<subject>/<semester>/<book>/  (OLD)
    to:
    data/raw/<semester>/<subject>/<book>/  (NEW)
    
    Also migrates processed data structure accordingly.
    """
    print("🔄 Starting data structure migration...")
    print("From: data/raw/<subject>/<semester>/<book>/")
    print("To:   data/raw/<semester>/<subject>/<book>/")
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    if not raw_dir.exists():
        print("❌ data/raw directory not found!")
        return
    
    # Create backup
    backup_dir = Path("data_backup")
    if backup_dir.exists():
        print(f"⚠️  Backup directory {backup_dir} already exists. Skipping backup.")
    else:
        print(f"📦 Creating backup at {backup_dir}...")
        shutil.copytree("data", backup_dir)
        print("✅ Backup created successfully!")
    
    # Migrate raw data
    print("\n🔄 Migrating raw data structure...")
    migrated_raw = 0
    
    for subject_dir in raw_dir.iterdir():
        if not subject_dir.is_dir():
            continue
            
        subject = subject_dir.name
        print(f"  Processing subject: {subject}")
        
        for semester_dir in subject_dir.iterdir():
            if not semester_dir.is_dir():
                continue
                
            semester = semester_dir.name
            print(f"    Processing semester: {semester}")
            
            # Create new directory structure
            new_semester_dir = raw_dir / semester
            new_semester_dir.mkdir(exist_ok=True)
            
            new_subject_dir = new_semester_dir / subject
            if new_subject_dir.exists():
                print(f"      ⚠️  Target directory already exists: {new_subject_dir}")
                continue
                
            # Move the entire subject directory
            print(f"      Moving: {semester_dir} -> {new_subject_dir}")
            shutil.move(str(semester_dir), str(new_subject_dir))
            migrated_raw += 1
    
    # Clean up empty subject directories
    print("\n🧹 Cleaning up empty directories...")
    for subject_dir in raw_dir.iterdir():
        if subject_dir.is_dir() and not any(subject_dir.iterdir()):
            print(f"  Removing empty directory: {subject_dir}")
            subject_dir.rmdir()
    
    # Migrate processed data
    print("\n🔄 Migrating processed data structure...")
    migrated_processed = 0
    
    if processed_dir.exists():
        for subject_dir in processed_dir.iterdir():
            if not subject_dir.is_dir():
                continue
                
            subject = subject_dir.name
            print(f"  Processing processed subject: {subject}")
            
            for semester_dir in subject_dir.iterdir():
                if not semester_dir.is_dir():
                    continue
                    
                semester = semester_dir.name
                print(f"    Processing processed semester: {semester}")
                
                # Create new directory structure
                new_semester_dir = processed_dir / semester
                new_semester_dir.mkdir(exist_ok=True)
                
                new_subject_dir = new_semester_dir / subject
                if new_subject_dir.exists():
                    print(f"      ⚠️  Target directory already exists: {new_subject_dir}")
                    continue
                    
                # Move the entire subject directory
                print(f"      Moving: {semester_dir} -> {new_subject_dir}")
                shutil.move(str(semester_dir), str(new_subject_dir))
                migrated_processed += 1
        
        # Clean up empty subject directories
        for subject_dir in processed_dir.iterdir():
            if subject_dir.is_dir() and not any(subject_dir.iterdir()):
                print(f"  Removing empty processed directory: {subject_dir}")
                subject_dir.rmdir()
    
    print(f"\n✅ Migration completed!")
    print(f"📊 Migrated {migrated_raw} raw data directories")
    print(f"📊 Migrated {migrated_processed} processed data directories")
    print(f"📦 Backup available at: {backup_dir}")
    
    # Show new structure
    print(f"\n📁 New directory structure:")
    if raw_dir.exists():
        for semester_dir in sorted(raw_dir.iterdir()):
            if semester_dir.is_dir():
                print(f"  {semester_dir.name}/")
                for subject_dir in sorted(semester_dir.iterdir()):
                    if subject_dir.is_dir():
                        print(f"    {subject_dir.name}/")
                        for book_dir in sorted(subject_dir.iterdir()):
                            if book_dir.is_dir():
                                print(f"      {book_dir.name}/")

if __name__ == "__main__":
    migrate_data_structure()
