from crewai.tools import BaseTool
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urlparse

class ContentAnalyzerTool(BaseTool):
    name: str = "content_analyzer"
    description: str = """Deep content analysis tool for verifying primary sources."""

    def _run(self, url: str, args: Optional[str] = None, kwargs: Optional[str] = None) -> str:
        try:
            # Handle both direct URL input and dictionary input
            if isinstance(url, dict) and 'url' in url:
                target_url = url['url']
            else:
                target_url = url
            
            content_data = self._analyze_content(target_url)
            return self._format_analysis(content_data)
        except Exception as e:
            return f"Analysis error: {str(e)}"

    def _analyze_content(self, url: str) -> Dict:
        try:
            # Download content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {"error": "Could not fetch content"}

            # Extract main content
            content = trafilatura.extract(downloaded, include_comments=False, 
                                        include_tables=True, 
                                        include_links=True,
                                        include_images=False)
            
            if not content:
                return {"error": "No content extracted"}

            # Analyze metadata
            metadata = trafilatura.extract_metadata(downloaded)
            
            return {
                "content": content,
                "metadata": metadata,
                "domain": urlparse(url).netloc,
                "content_length": len(content)
            }
        except Exception as e:
            return {"error": str(e)}

    def _format_analysis(self, analysis: Dict) -> str:
        if "error" in analysis:
            return analysis["error"]
            
        return {
            "domain_authority": self._assess_domain_authority(analysis["domain"]),
            "content_metrics": {
                "length": analysis["content_length"],
                "has_references": "references" in analysis["content"].lower(),
                "has_citations": "cited" in analysis["content"].lower()
            },
            "metadata": analysis["metadata"]
        }

    def _assess_domain_authority(self, domain: str) -> Dict:
        academic_domains = ['.edu', '.gov', '.org', 'research.', 'science.']
        authority_score = sum([2 for d in academic_domains if d in domain])
        
        return {
            "score": min(authority_score, 10),
            "is_academic": any(d in domain for d in academic_domains),
            "domain_type": "academic" if any(d in domain for d in academic_domains) else "general"
        }

content_analyzer_tool = ContentAnalyzerTool()