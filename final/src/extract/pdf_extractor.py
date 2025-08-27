from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, List, Optional
import logging

import fitz  # PyMuPDF
from PIL import Image
import io

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    page_index: int
    text: str


@dataclass
class PageImage:
    page_index: int
    image_index: int
    image_bytes: bytes
    ext: str


def extract_text(pdf_path: str | Path) -> List[PageText]:
    try:
        doc = fitz.open(str(pdf_path))
        results: List[PageText] = []
        for page_index in range(len(doc)):
            try:
                page = doc.load_page(page_index)
                text = page.get_text("text")
                if text and text.strip():
                    results.append(PageText(page_index=page_index, text=text))
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_index} in {pdf_path}: {e}")
                continue
        doc.close()
        return results
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return []


def extract_images(pdf_path: str | Path) -> List[PageImage]:
    try:
        doc = fitz.open(str(pdf_path))
        images: List[PageImage] = []
        for page_index in range(len(doc)):
            try:
                page = doc.load_page(page_index)
                for img_index, img in enumerate(page.get_images(full=True)):
                    try:
                        xref = img[0]
                        base = doc.extract_image(xref)
                        image_bytes: bytes = base["image"]
                        ext: str = base.get("ext", "png")
                        images.append(PageImage(page_index=page_index, image_index=img_index, image_bytes=image_bytes, ext=ext))
                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_index} in {pdf_path}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Failed to process page {page_index} for images in {pdf_path}: {e}")
                continue
        doc.close()
        return images
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return []
