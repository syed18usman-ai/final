#!/usr/bin/env python3

from src.store.chroma_store import ChromaStore

def main():
    store = ChromaStore('storage/vector')
    
    print("=== Vector Store Data Check ===")
    
    # Check semesters
    semesters = store.get_semesters()
    print(f"Available semesters: {semesters}")
    
    # Check subjects for semester 7
    if '7' in semesters:
        subjects = store.get_subjects('7')
        print(f"Subjects in semester 7: {subjects}")
        
        # Check data for each subject
        for subject in subjects:
            print(f"\n--- Subject: {subject} ---")
            results = store.list_text(where={"semester": "7", "subject": subject}, limit=5)
            if results["metadatas"]:
                print(f"Found {len(results['metadatas'])} text chunks")
                for i, meta in enumerate(results["metadatas"][:3]):  # Show first 3
                    print(f"  Chunk {i+1}: {meta.get('book_title', 'Unknown')} - Page {meta.get('page', 'Unknown')}")
            else:
                print("No text chunks found")
    
    # Check total counts
    all_text = store.list_text(limit=1000)
    all_images = store.list_image(limit=1000)
    print(f"\n=== Summary ===")
    print(f"Total text chunks: {len(all_text['metadatas']) if all_text['metadatas'] else 0}")
    print(f"Total image chunks: {len(all_images['metadatas']) if all_images['metadatas'] else 0}")

if __name__ == "__main__":
    main()
