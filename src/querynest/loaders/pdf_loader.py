"""
Is file ka kaam:
- PDF files ko LangChain ke through load karna
- Full loading use karna taaki saare pages properly load ho jaaye
- Single PDF ya poore directory dono support karta hai ye

Ye loader sirf DOCUMENTS ie document objects deta hai,
text splitting baad mein karange.

NOTE: Lazy loading se issues aa rahe the (later pages ka QnA kaam nahi kar raha tha)
Isliye ab hum full loading kar rahe hain - saare pages ek saath memory mein load hote hain
"""

import sys
from pathlib import Path
from typing import List

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document


def load_pdfs(path: str) -> List[Document]:
    """
    PDF file(s) ko load karke LangChain Documents return karta hai.

    Path can be:
    - Single PDF file ka path
    - Ya ek directory jisme multiple PDFs ho

    Returns:
    - List[Document] (fully loaded, not lazy)

    NOTE:
    - Saare pages ek saath memory mein load hote hain
    - Ye ensure karta hai ki QnA later pages ke liye bhi kaam kare
    """

    input_path = Path(path)

    # Validate path exists
    if not input_path.exists():
        print("\nError: Path not found")
        print(f"Path: {path}")
        print("\nPlease check:")
        print("The path is correct")
        print("You have permission to access the file/directory")
        print("Exiting...\n")
        sys.exit(1)

    # Case 1: Single PDF file
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            print("\nError: Not a PDF file")
            print(f"Path: {path}")
            print(f"File type: {input_path.suffix}")
            print("\nPlease provide a valid PDF file (.pdf extension)")
            print("Exiting...\n")
            sys.exit(1)

        try:
            print(f"\nLoading PDF: {input_path.name}")
            loader = PyPDFLoader(str(input_path))
            documents = loader.load()  # Full load, not lazy

            if not documents:
                print("\nError: PDF file is empty or unreadable")
                print(f"Path: {path}")
                print("\nPlease check:")
                print("- The PDF file is not corrupted")
                print("- The PDF contains readable text (not just images)")
                print("Exiting...\n")
                sys.exit(1)

            print(f"Loaded {len(documents)} page(s) from PDF")
            return documents

        except Exception as e:
            print("\nError: Failed to load PDF")
            print(f"Path: {path}")
            print(f"Error: {str(e)}")
            print("\nPossible reasons:")
            print("-PDF file is corrupted")
            print("-PDF is password-protected")
            print("-PDF format is not supported")
            print("Exiting...\n")
            sys.exit(1)

    # Case 2: Directory of PDFs
    if input_path.is_dir():
        try:
            print(f"\nLoading PDFs from directory: {input_path.name}")

            # Check if directory has any PDF files
            pdf_files = list(input_path.glob("**/*.pdf"))

            if not pdf_files:
                print("\nError: No PDF files found in directory")
                print(f"Path: {path}")
                print("\nPlease ensure:")
                print("- The directory contains PDF files (.pdf extension)")
                print("- You have permission to read the files")
                print("Exiting...\n")
                sys.exit(1)

            print(f"Found {len(pdf_files)} PDF file(s)")

            loader = DirectoryLoader(
                path=str(input_path),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True,  # Shows progress bar in terminal
            )

            documents = loader.load()  # Full load, not lazy

            if not documents:
                print("\nError: No content could be extracted from PDFs")
                print(f"Path: {path}")
                print("\nPossible reasons:")
                print("- All PDFs are empty or corrupted")
                print("- PDFs contain only images (no text)")
                print("Exiting...\n")
                sys.exit(1)

            print(f"✅ Loaded {len(documents)} page(s) from {len(pdf_files)} PDF(s)")
            return documents

        except Exception as e:
            print("\nError: Failed to load PDFs from directory")
            print(f"Path: {path}")
            print(f"Error: {str(e)}")
            print("\nPlease check:")
            print("- You have permission to read the directory")
            print("- PDF files are not corrupted")
            print("Exiting...\n")
            sys.exit(1)

    # Should never reach here, but just in case
    print("\nError: Unsupported path type")
    print(f"Path: {path}")
    print("Path must be either a PDF file or a directory")
    print("Exiting...\n")
    sys.exit(1)
