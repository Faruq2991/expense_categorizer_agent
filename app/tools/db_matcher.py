import sqlite3
import re
from typing import Optional, Dict, List
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr

class KeywordDBMatcherTool(BaseTool):
    """
    KeywordDBMatcherTool is a LangChain-compatible tool that connects to a SQLite database
    to categorize transaction text based on stored keyword patterns.
    """
    name: str = "keyword_db_matcher"
    description: str = "Uses a database to match transaction text to known category keywords and returns the category. Input is the transaction text."

    _conn: sqlite3.Connection = PrivateAttr()

    def __init__(self, conn: sqlite3.Connection, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, '_conn', conn)
        self._conn.row_factory = sqlite3.Row

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent matching (lowercase, strip whitespace)."""
        return text.strip().lower()

    def _run(self, input_text: str) -> Optional[str]:
        """
        Main execution method required by BaseTool.
        Scans input text against database keywords and returns the first matched category.
        """
        normalized = self._normalize_text(input_text)
        cursor = self._conn.execute("SELECT keyword, category FROM keyword_category")
        for row in cursor:
            pattern = r'\b' + re.escape(row['keyword'].lower()) + r'\b'
            if re.search(pattern, normalized):
                return row['category']
        return None

    async def _arun(self, input_text: str) -> Optional[str]:
        """Asynchronous version of the _run method."""
        return self._run(input_text)

    def get_all_matches(self, input_text: str) -> Dict[str, List[str]]:
        """
        Returns all matching categories with their keywords.
        """
        normalized_text = self._normalize_text(input_text)
        matches: Dict[str, List[str]] = {} 
        cursor = self._conn.execute("SELECT keyword, category FROM keyword_category")
        for row in cursor:
            pattern = r'\b' + re.escape(row['keyword'].lower()) + r'\b'
            if re.search(pattern, normalized_text):
                matches.setdefault(row['category'], []).append(row['keyword'])
        return matches

    def get_best_match(self, input_text: str) -> Optional[str]:
        """
        Returns the best matching category based on number of keyword matches.
        In case of ties, returns the first category encountered.
        """
        all_matches = self.get_all_matches(input_text)
        
        if not all_matches:
            return None
        
        best_category = max(all_matches.keys(), 
                            key=lambda cat: len(all_matches[cat]))
        return best_category