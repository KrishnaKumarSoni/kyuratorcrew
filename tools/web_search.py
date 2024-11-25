from crewai.tools import BaseTool
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote_plus
import urllib.parse

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = """Advanced web search tool specializing in finding primary sources."""

    def _run(self, query: str, args: Optional[str] = None, kwargs: Optional[str] = None) -> str:
        try:
            results = self._basic_search(query)
            if not results:
                return "No results found. Please try a different search term."
            
            return self._format_results(results)
        except Exception as e:
            return f"Search error: {str(e)}. Please try a different search term."

    def _is_primary_source(self, url: str, title: str, description: str) -> tuple[bool, str]:
        """Determine if a source is likely a primary source"""
        primary_indicators = {
            'domains': [
                '.gov', '.edu', '.org', 
                'research.', 'data.', 'archive.',
                'official.', 'primary.'
            ],
            'title_keywords': [
                'official', 'original', 'primary', 'source',
                'data', 'report', 'study', 'research',
                'proceedings', 'documentation'
            ],
            'content_keywords': [
                'published', 'authored', 'conducted',
                'research', 'study', 'report', 'findings',
                'original', 'primary source'
            ]
        }
        
        reasons = []
        
        # Check domain
        if any(ind in url.lower() for ind in primary_indicators['domains']):
            reasons.append("Authoritative domain")
            
        # Check title
        if any(kw in title.lower() for kw in primary_indicators['title_keywords']):
            reasons.append("Primary source indicators in title")
            
        # Check description
        if any(kw in description.lower() for kw in primary_indicators['content_keywords']):
            reasons.append("Primary source indicators in content")
            
        is_primary = len(reasons) > 0
        reason = " | ".join(reasons) if reasons else "Not identified as primary source"
        
        return is_primary, reason

    def _basic_search(self, query: str) -> List[Dict]:
        """Enhanced search focusing on primary sources"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        results = []
        
        try:
            # Primary source-focused search queries
            search_queries = [
                f"{query} primary source",
                f"{query} official source",
                f"{query} original research",
                f"{query} official data",
                f"{query} source document"
            ]
            
            for search_query in search_queries:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for result in soup.select('.result'):
                    title = result.select_one('.result__title')
                    snippet = result.select_one('.result__snippet')
                    
                    if title and snippet:
                        title_text = title.get_text(strip=True)
                        snippet_text = snippet.get_text(strip=True)
                        raw_url = title.find('a')['href']
                        clean_url = self.process_url(raw_url)
                        
                        # Check if it's a primary source
                        is_primary, primary_reason = self._is_primary_source(
                            clean_url, title_text, snippet_text
                        )
                        
                        if is_primary and not any(r['url'] == clean_url for r in results):
                            results.append({
                                'title': title_text,
                                'url': clean_url,
                                'description': snippet_text,
                                'primary_source_indicators': primary_reason,
                                'search_variant': search_query
                            })
                
                time.sleep(1)
            
            return results[:15]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _format_results(self, results: List[Dict]) -> str:
        """Format results in the required structure"""
        formatted = []
        for result in results:
            formatted.append(
                f"Item URL: {result['url']}\n"
                f"Item Note: {result['description']}\n"
                f"Item Tags: {result['title']}\n"
                f"Primary Source Indicators: {result.get('primary_source_indicators', '')}"
            )
        return "\n\n".join(formatted)

    def process_url(self, url: str) -> str:
        """Clean and process URLs"""
        if "//duckduckgo.com/l/?uddg=" in url:
            direct_url = url.split("uddg=")[1].split("&")[0]
            return urllib.parse.unquote(direct_url)
        return url

    def clean_results(self, results: list) -> list:
        """Clean and format search results"""
        cleaned = []
        for result in results:
            cleaned.append({
                'url': self.process_url(result['url']),
                'description': result.get('description', ''),
                'tags': result.get('tags', [])[:4]  # Limit to 4 tags
            })
        return cleaned[:5]  # Return only top 5 results

    def search(self, query: str) -> dict:
        """Perform search and return cleaned results"""
        raw_results = self._search(query)
        return self.clean_results(raw_results)

# Create an instance of the tool to export
web_search_tool = WebSearchTool()