"""
NID information parser with intelligent text extraction and preprocessing.
"""
import re
from typing import Optional
from datetime import datetime

from app.logger import logger, log_with_context
from app.schemas import OCRResponse, NIDFrontData, NIDBackData


class NIDParser:
    """
    Parser for extracting structured information from NID OCR results.
    Handles Bangladeshi National ID card format.
    """
    
    # Regex patterns for NID information extraction
    NID_NUMBER_PATTERN = re.compile(r'\b\d{10,17}\b')  # 10-17 digit NID numbers
    DATE_PATTERNS = [
        re.compile(r'\b(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})\b'),  # DD/MM/YYYY or DD-MM-YYYY
        re.compile(r'\b(\d{2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b', re.IGNORECASE),  # DD Mon YYYY eg. 30 Dec 1996
        re.compile(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{2}),?\s+(\d{4})\b', re.IGNORECASE),  # Mon DD, YYYY
    ]
    
    # Keywords to identify different fields
    NAME_KEYWORDS = ['name', 'Namae', 'Name: ']
    DOB_KEYWORDS = ['date of birth', 'dob', 'birth', 'Date of Birth', 'Birth']
    NID_KEYWORDS = ['nid', 'id no', 'id no:', 'ID NO', 'nid no']
    ADDRESS_KEYWORDS = ['address', 'ঠিকানা', 'village', 'post', 'thana', 'district']
    
    @staticmethod
    def _is_valid_birth_year(date_str: str) -> bool:
        """Validate that the extracted date has a reasonable birth year."""
        year_match = re.search(r'\d{4}', date_str)
        if not year_match:
            return False
        year = int(year_match.group())
        current_year = datetime.now().year
        return 1900 <= year <= current_year

    @classmethod
    def _find_date_in_candidates(cls, candidates: list[str]) -> Optional[str]:
        """Search for a date within a list of candidate strings."""
        for candidate in candidates:
            for pattern in cls.DATE_PATTERNS:
                match = pattern.search(candidate)
                if match:
                    date_str = match.group(0)
                    if cls._is_valid_birth_year(date_str):
                        return date_str
        return None
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but keep alphanumeric, spaces, and common punctuation
        text = re.sub(r'[^\w\s\-/.,:]', '', text)
        return text.strip()
    
    @staticmethod
    def _extract_name(texts: list[str]) -> Optional[str]:
        """
        Extract name from OCR texts.
        
        Args:
            texts: List of extracted texts
            
        Returns:
            Extracted name or None
        """
        name_candidates = []
        
        for i, text in enumerate(texts):
            text_lower = text.lower()
            
            # Check if line contains name keywords
            if any(keyword in text_lower for keyword in NIDParser.NAME_KEYWORDS):
                # Name is usually in the next line or after colon
                if ':' in text:
                    name = text.split(':', 1)[1].strip()
                    if name and len(name) > 2:
                        name_candidates.append(name)
                    else:
                        # Gather subsequent lines until another section or invalid line
                        collected_parts = []
                        for next_text in texts[i + 1 :]:
                            next_clean = next_text.strip()
                            if not next_clean:
                                break
                            next_lower = next_clean.lower()
                            if any(keyword in next_lower for keyword in (NIDParser.DOB_KEYWORDS + NIDParser.NID_KEYWORDS)):
                                break
                            if any(char.isdigit() for char in next_clean):
                                break
                            collected_parts.append(next_clean)
                            # Limit to reasonable number of lines for a name
                            if len(collected_parts) >= 3:
                                break
                        if collected_parts:
                            candidate = ' '.join(collected_parts)
                            if len(candidate) > 2:
                                name_candidates.append(candidate)
                elif i + 1 < len(texts):
                    next_text = texts[i + 1].strip()
                    if next_text and len(next_text) > 2 and not any(char.isdigit() for char in next_text):
                        name_candidates.append(next_text)
        
        # Also look for capitalized names in the first few lines (extend to capture multi-line names)
        for text in texts[:10]:
            if text.isupper() and len(text.split()) >= 2 and len(text) > 5:
                # Likely a name if it's all caps and has multiple words
                if not any(char.isdigit() for char in text):
                    name_candidates.append(text)
        
        # Combine consecutive uppercase lines to form a full name if necessary
        for i in range(len(texts) - 1):
            current = texts[i].strip()
            nxt = texts[i + 1].strip()
            if (
                current
                and nxt
                and current.isupper()
                and nxt.isupper()
                and len(current.split()) >= 1
                and len(nxt.split()) >= 1
                and not any(char.isdigit() for char in current + nxt)
            ):
                combined = f"{current} {nxt}"
                if len(combined) > 5:
                    name_candidates.append(combined)
        
        # Return the longest candidate (usually more complete)
        if name_candidates:
            return max(name_candidates, key=len)
        
        return None
    
    @classmethod
    def _extract_date_of_birth(cls, texts: list[str]) -> Optional[str]:
        """
        Extract date of birth from OCR texts.
        
        Args:
            texts: List of extracted texts
            
        Returns:
            Extracted date of birth or None
        """
        # First pass: check for DOB keywords in individual or combined texts
        for i, text in enumerate(texts):
            text_lower = text.lower()
            
            # Check if line contains DOB keywords
            if any(keyword in text_lower for keyword in cls.DOB_KEYWORDS):
                candidates = [text]
                if i + 1 < len(texts):
                    candidates.append(texts[i + 1])

                # Combine subsequent lines to capture split date tokens
                combined_parts = [text]
                for offset in range(1, 6):
                    if i + offset < len(texts):
                        combined_parts.append(texts[i + offset])
                        combined_candidate = " ".join(combined_parts)
                        candidates.append(combined_candidate)

                date_match = cls._find_date_in_candidates(candidates)
                if date_match:
                    return date_match
        
        # Second pass: check for DOB keywords in sliding windows (handles "Date of Birth:" split across tokens)
        for i in range(len(texts) - 2):
            window_3 = " ".join(texts[i:i+3]).lower()
            window_4 = " ".join(texts[i:i+4]).lower() if i + 3 < len(texts) else ""
            
            if any(keyword in window_3 or keyword in window_4 for keyword in cls.DOB_KEYWORDS):
                # Found keyword in window, now look for date in next few tokens
                candidates = []
                for offset in range(0, 8):
                    if i + offset < len(texts):
                        for window_size in range(1, 6):
                            if i + offset + window_size <= len(texts):
                                candidate = " ".join(texts[i + offset: i + offset + window_size])
                                candidates.append(candidate)
                
                date_match = cls._find_date_in_candidates(candidates)
                if date_match:
                    return date_match
        
        # Fallback: look for any date pattern in individual texts
        date_match = cls._find_date_in_candidates(texts)
        if date_match:
            return date_match

        # Additional fallback: sliding window combinations of consecutive texts
        max_window = 5
        for window_size in range(2, max_window + 1):
            sliding_candidates = [
                " ".join(texts[idx: idx + window_size])
                for idx in range(len(texts) - window_size + 1)
            ]
            date_match = cls._find_date_in_candidates(sliding_candidates)
            if date_match:
                return date_match

        return None
    
    @staticmethod
    def _extract_nid_number(texts: list[str]) -> Optional[str]:
        """
        Extract NID number from OCR texts.
        Handles both continuous digits and space-separated formats.
        
        Args:
            texts: List of extracted texts
            
        Returns:
            Extracted NID number or None
        """
        nid_candidates = []
        
        # First pass: Look for NID near keywords
        for i, text in enumerate(texts):
            text_lower = text.lower()
            
            # Check if line contains NID keywords
            if any(keyword in text_lower for keyword in NIDParser.NID_KEYWORDS):
                # NID might be in the same line or next few lines
                search_texts = [text]
                for offset in range(1, 4):  # Check next 3 lines
                    if i + offset < len(texts):
                        search_texts.append(texts[i + offset])
                
                for search_text in search_texts:
                    # Try to extract continuous digits
                    matches = NIDParser.NID_NUMBER_PATTERN.findall(search_text)
                    for match in matches:
                        if len(match) >= 10:
                            nid_candidates.append(match)
                    
                    # Try to extract space-separated digits (e.g., "600 124 4158")
                    # Remove all non-digit and non-space characters, then extract digits
                    cleaned = re.sub(r'[^0-9\s]', '', search_text)
                    # Find sequences of digits separated by spaces
                    space_separated = re.findall(r'\d+(?:\s+\d+)+', cleaned)
                    for match in space_separated:
                        # Remove spaces to get the actual number
                        digits_only = match.replace(' ', '')
                        if len(digits_only) >= 10:
                            nid_candidates.append(digits_only)
        
        # Second pass: Look for space-separated digit patterns anywhere
        if not nid_candidates:
            for text in texts:
                # Look for patterns like "600 124 4158" or "6001244158"
                cleaned = re.sub(r'[^0-9\s]', '', text)
                space_separated = re.findall(r'\d+(?:\s+\d+)+', cleaned)
                for match in space_separated:
                    digits_only = match.replace(' ', '')
                    if len(digits_only) in [10, 13, 17]:
                        nid_candidates.append(digits_only)
        
        # Third pass: Fallback to continuous digit patterns
        if not nid_candidates:
            for text in texts:
                matches = NIDParser.NID_NUMBER_PATTERN.findall(text)
                for match in matches:
                    if len(match) in [10, 13, 17]:
                        nid_candidates.append(match)
        
        # Return the first valid candidate, preferring longer numbers
        if nid_candidates:
            # Remove duplicates and sort by length (prefer longer)
            unique_candidates = list(set(nid_candidates))
            return max(unique_candidates, key=len)
        
        return None
    
    @staticmethod
    def _extract_address(texts: list[str]) -> Optional[str]:
        """
        Extract address from OCR texts and format as single line.
        
        Args:
            texts: List of extracted texts
            
        Returns:
            Extracted address as single line or None
        """
        address_parts = []
        in_address_section = False
        
        for i, text in enumerate(texts):
            text_lower = text.lower()
            
            # Check if we're entering address section
            if any(keyword in text_lower for keyword in NIDParser.ADDRESS_KEYWORDS):
                in_address_section = True
                
                # Check if address starts on the same line
                if ':' in text:
                    address_start = text.split(':', 1)[1].strip()
                    if address_start:
                        address_parts.append(address_start)
                continue
            
            # Collect address lines
            if in_address_section:
                # Stop if we hit another section or empty line
                if not text.strip() or any(keyword in text_lower for keyword in NIDParser.NID_KEYWORDS + NIDParser.DOB_KEYWORDS):
                    break
                
                # Skip if it looks like a date or NID number
                if re.search(r'\d{10,}', text) or any(pattern.search(text) for pattern in NIDParser.DATE_PATTERNS):
                    continue
                
                address_parts.append(text.strip())
                
                # Limit address to reasonable number of lines
                if len(address_parts) >= 5:
                    break
        
        if address_parts:
            # Join with comma and space, clean up multiple commas
            address = ', '.join(address_parts)
            address = re.sub(r',\s*,', ',', address)  # Remove double commas
            address = re.sub(r'\s+', ' ', address)  # Normalize spaces
            return address.strip()
        
        return None
    
    @classmethod
    def parse_nid_front(cls, ocr_response: OCRResponse) -> NIDFrontData:
        """
        Parse NID front side OCR results.
        
        Args:
            ocr_response: OCR response with extracted texts
            
        Returns:
            Parsed NID front data
        """
        if not ocr_response.success or not ocr_response.results:
            log_with_context(
                logger,
                "warning",
                "No OCR results to parse for NID front",
                success=ocr_response.success,
                results_count=len(ocr_response.results)
            )
            return NIDFrontData(raw_text=[])
        
        # Extract all texts
        texts = [result.text for result in ocr_response.results]
        cleaned_texts = [cls._clean_text(text) for text in texts if text.strip()]
        
        # Extract individual fields
        name = cls._extract_name(cleaned_texts)
        dob = cls._extract_date_of_birth(cleaned_texts)
        nid_number = cls._extract_nid_number(cleaned_texts)
        
        log_with_context(
            logger,
            "info",
            "Parsed NID front data",
            name_found=bool(name),
            dob_found=bool(dob),
            nid_found=bool(nid_number),
            total_texts=len(cleaned_texts)
        )
        
        return NIDFrontData(
            name=name,
            date_of_birth=dob,
            nid_number=nid_number,
            raw_text=cleaned_texts
        )
    
    @classmethod
    def parse_nid_back(cls, ocr_response: OCRResponse) -> NIDBackData:
        """
        Parse NID back side OCR results.
        
        Args:
            ocr_response: OCR response with extracted texts
            
        Returns:
            Parsed NID back data
        """
        if not ocr_response.success or not ocr_response.results:
            log_with_context(
                logger,
                "warning",
                "No OCR results to parse for NID back",
                success=ocr_response.success,
                results_count=len(ocr_response.results)
            )
            return NIDBackData(raw_text=[])
        
        # Extract all texts
        texts = [result.text for result in ocr_response.results]
        cleaned_texts = [cls._clean_text(text) for text in texts if text.strip()]
        
        # Extract address
        address = cls._extract_address(cleaned_texts)
        
        log_with_context(
            logger,
            "info",
            "Parsed NID back data",
            address_found=bool(address),
            total_texts=len(cleaned_texts)
        )
        
        return NIDBackData(
            address=address,
            raw_text=cleaned_texts
        )
