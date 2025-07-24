from typing import Dict, List, Optional
from langchain_core.tools import BaseTool
import re

# TODO: Handle multiple matching categories, maybe rank by confidence.
class RegexMatcherTool(BaseTool):
    """
    RegexMatcherTool is a LangChain-compatible tool that scans a transaction text
    and returns a category based on pre-defined keyword patterns loaded from config.
    """
    name: str = "regex_matcher"
    description: str = "Uses regex to match transaction text to known category keywords"
    category_map: Dict[str, List[str]]

    def _run(self, input_text: str) -> Optional[str]:
        """
        Main execution method required by BaseTool.
        Scans input text against category keywords and returns first match.
        """
        normalized_text = self._normalize_text(input_text)

        for category, keywords in self.category_map.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, normalized_text):
                    return category
        return None

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent matching"""
        return text.strip().lower()

    def get_all_matches(self, input_text: str) -> Dict[str, List[str]]:
        """
        Enhanced method to return all matching categories with their keywords.
        Useful for handling multiple matches and confidence ranking.
        """
        normalized_text = self._normalize_text(input_text)
        matches = {}
        
        for category, keywords in self.category_map.items():
            matched_keywords = []
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, normalized_text):
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                matches[category] = matched_keywords
        
        return matches

    def get_best_match(self, input_text: str) -> Optional[str]:
        """
        Returns the best matching category based on number of keyword matches.
        In case of ties, returns the first category encountered.
        """
        all_matches = self.get_all_matches(input_text)
        
        if not all_matches:
            return None
        
        # Find category with most matched keywords
        best_category = max(all_matches.keys(), 
                          key=lambda cat: len(all_matches[cat]))
        return best_category