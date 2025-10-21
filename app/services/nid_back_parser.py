"""
NID back image parser specialized for EasyOCR multilingual results.
Extracts address and other information from Bengali and English text.
"""
import re
from typing import Optional, List

from app.logger import logger, log_with_context
from app.schemas import EasyOCRResponse, NIDBackData


class NIDBackParser:
    """
    Specialized parser for NID back side using EasyOCR multilingual results.
    Handles Bengali and English text for address extraction.
    """
    
    # Bengali and English keywords for address identification
    ADDRESS_KEYWORDS_BENGALI = [
        'ঠিকানা',  # Address
        'গ্রাম',    # Village
        'পোস্ট',   # Post
        'থানা',    # Thana
        'জেলা',    # District
        'বিভাগ',   # Division
        'উপজেলা',  # Upazila
    ]
    
    ADDRESS_KEYWORDS_ENGLISH = [
        'address',
        'village',
        'post',
        'thana',
        'district',
        'division',
        'upazila',
        'holding',
        'road',
        'ward',
    ]
    
    # Combined keywords
    ADDRESS_KEYWORDS = ADDRESS_KEYWORDS_BENGALI + ADDRESS_KEYWORDS_ENGLISH
    
    # Keywords to stop address collection
    STOP_KEYWORDS_BENGALI = [
        'জন্ম',      # Birth
        'তারিখ',    # Date
        'রক্ত',     # Blood
        'স্বাক্ষর',  # Signature
    ]
    
    STOP_KEYWORDS_ENGLISH = [
        'date of birth',
        'dob',
        'birth',
        'blood',
        'signature',
        'issue',
        'expire',
    ]
    
    STOP_KEYWORDS = STOP_KEYWORDS_BENGALI + STOP_KEYWORDS_ENGLISH
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean and normalize text while preserving Bengali characters.
        
        Args:
            text: Input text (Bengali/English)
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but keep Bengali, English, numbers, and common punctuation
        # Bengali Unicode range: \u0980-\u09FF
        text = re.sub(r'[^\w\s\-/.,:\u0980-\u09FF]', '', text)
        return text.strip()
    
    @staticmethod
    def _is_likely_address_line(text: str) -> bool:
        """
        Determine if a text line is likely part of an address.
        
        Args:
            text: Text line to check
            
        Returns:
            True if likely an address line
        """
        text_lower = text.lower()
        
        # Check for address keywords
        if any(keyword in text_lower for keyword in NIDBackParser.ADDRESS_KEYWORDS):
            return True
        
        # Check for Bengali characters (likely address in Bengali)
        if re.search(r'[\u0980-\u09FF]', text):
            return True
        
        # Check for common address patterns (numbers, commas, etc.)
        if re.search(r'\d+', text) and any(c in text for c in [',', '-', '/']):
            return True
        
        return False
    
    @staticmethod
    def _should_stop_collection(text: str) -> bool:
        """
        Check if we should stop collecting address lines.
        
        Args:
            text: Text to check
            
        Returns:
            True if should stop
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in NIDBackParser.STOP_KEYWORDS)
    
    @classmethod
    def _extract_address_from_texts(cls, texts: List[str]) -> Optional[str]:
        """
        Extract address from list of texts with Bengali/English support.
        
        Args:
            texts: List of extracted texts
            
        Returns:
            Extracted address as single line or None
        """
        address_parts = []
        in_address_section = False
        address_started = False
        
        for i, text in enumerate(texts):
            text_clean = cls._clean_text(text)
            if not text_clean:
                continue
            
            text_lower = text_clean.lower()
            
            # Check if we should stop collecting
            if address_started and cls._should_stop_collection(text_lower):
                break
            
            # Check if we're entering address section
            if any(keyword in text_lower for keyword in cls.ADDRESS_KEYWORDS):
                in_address_section = True
                address_started = True
                
                # Check if address starts on the same line (after colon)
                if ':' in text_clean:
                    parts = text_clean.split(':', 1)
                    if len(parts) > 1:
                        address_start = parts[1].strip()
                        if address_start:
                            address_parts.append(address_start)
                    continue
                elif '।' in text_clean:  # Bengali danda (।) used as separator
                    parts = text_clean.split('।', 1)
                    if len(parts) > 1:
                        address_start = parts[1].strip()
                        if address_start:
                            address_parts.append(address_start)
                    continue
                
                # If keyword is standalone, continue to next line
                continue
            
            # Collect address lines
            if in_address_section or cls._is_likely_address_line(text_clean):
                in_address_section = True
                address_started = True
                
                # Skip if it looks like a date or very long number (likely NID)
                if re.search(r'\d{10,}', text_clean):
                    continue
                
                # Skip very short texts (likely noise)
                if len(text_clean) < 2:
                    continue
                
                address_parts.append(text_clean)
                
                # Limit address to reasonable number of lines
                if len(address_parts) >= 10:
                    break
        
        if address_parts:
            # Join with comma and space
            address = ', '.join(address_parts)
            
            # Clean up multiple commas and spaces
            address = re.sub(r',\s*,+', ',', address)
            address = re.sub(r'\s+', ' ', address)
            address = re.sub(r',\s*$', '', address)  # Remove trailing comma
            
            return address.strip()
        
        return None
    
    @classmethod
    def _extract_additional_info(cls, texts: List[str]) -> dict:
        """
        Extract additional information from NID back (blood group, etc.).
        
        Args:
            texts: List of extracted texts
            
        Returns:
            Dictionary with additional information
        """
        info = {}
        
        # Blood group patterns
        blood_group_pattern = re.compile(r'\b(A|B|AB|O)[+-]\b', re.IGNORECASE)
        
        for text in texts:
            text_clean = cls._clean_text(text)
            text_lower = text_clean.lower()
            
            # Extract blood group
            if 'blood' in text_lower or 'রক্ত' in text_clean:
                match = blood_group_pattern.search(text_clean)
                if match:
                    info['blood_group'] = match.group(0).upper()
        
        return info
    
    @classmethod
    def parse_nid_back(cls, easyocr_response: EasyOCRResponse) -> NIDBackData:
        """
        Parse NID back side EasyOCR results with Bengali/English support.
        
        Args:
            easyocr_response: EasyOCR response with extracted texts
            
        Returns:
            Parsed NID back data with address and raw text
        """
        if not easyocr_response.success or not easyocr_response.results:
            log_with_context(
                logger,
                "warning",
                "No EasyOCR results to parse for NID back",
                success=easyocr_response.success,
                results_count=len(easyocr_response.results)
            )
            return NIDBackData(raw_text=[])
        
        # Extract all texts
        texts = [result.text for result in easyocr_response.results]
        cleaned_texts = [cls._clean_text(text) for text in texts if text.strip()]
        
        # Log detected texts for debugging
        if logger.level <= 10:  # DEBUG level
            logger.debug(f"EasyOCR detected texts for NID back: {cleaned_texts[:15]}")
        
        # Extract address
        address = cls._extract_address_from_texts(cleaned_texts)
        
        # Extract additional information
        additional_info = cls._extract_additional_info(cleaned_texts)
        
        log_with_context(
            logger,
            "info",
            "Parsed NID back data with EasyOCR",
            address_found=bool(address),
            total_texts=len(cleaned_texts),
            bengali_texts=sum(1 for t in cleaned_texts if re.search(r'[\u0980-\u09FF]', t)),
            english_texts=sum(1 for t in cleaned_texts if not re.search(r'[\u0980-\u09FF]', t)),
            additional_info=list(additional_info.keys())
        )
        
        # Create response with address and raw text
        return NIDBackData(
            address=address,
            raw_text=cleaned_texts
        )
    
    @classmethod
    def get_raw_text_only(cls, easyocr_response: EasyOCRResponse) -> List[str]:
        """
        Get only raw text from EasyOCR response without parsing.
        Useful for debugging or when you need unprocessed text.
        
        Args:
            easyocr_response: EasyOCR response
            
        Returns:
            List of raw texts
        """
        if not easyocr_response.success or not easyocr_response.results:
            return []
        
        return [result.text for result in easyocr_response.results]
    
    @classmethod
    def get_formatted_text(cls, easyocr_response: EasyOCRResponse, separator: str = '\n') -> str:
        """
        Get formatted text from EasyOCR response.
        
        Args:
            easyocr_response: EasyOCR response
            separator: Separator between text lines (default: newline)
            
        Returns:
            Formatted text string
        """
        texts = cls.get_raw_text_only(easyocr_response)
        return separator.join(texts)
