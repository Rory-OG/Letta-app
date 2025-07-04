"""
Web Search Tool for Letta Agent
Handles web searches for current information and research
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class WebSearchTool:
    """Tool for searching the web for current information"""
    
    def __init__(self):
        self.name = "web_search"
        self.description = "Search the web for current information, news, and research"
        self.search_engines = {
            "duckduckgo": "https://duckduckgo.com/html/",
            "serp": "https://serpapi.com/search"  # Requires API key
        }
        self.default_engine = "duckduckgo"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_function_schema(self) -> Dict[str, Any]:
        """Get the function schema for Letta"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find information on the web"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default: 5, max: 10)"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["general", "news", "academic", "images"],
                        "description": "Type of search to perform"
                    },
                    "time_filter": {
                        "type": "string",
                        "enum": ["any", "day", "week", "month", "year"],
                        "description": "Time filter for search results"
                    },
                    "site": {
                        "type": "string",
                        "description": "Specific site to search within (e.g., 'wikipedia.org')"
                    },
                    "extract_content": {
                        "type": "boolean",
                        "description": "Whether to extract and summarize content from top results"
                    }
                },
                "required": ["query"]
            }
        }
    
    def execute(self, query: str, num_results: int = 5, search_type: str = "general",
                time_filter: str = "any", site: str = None, extract_content: bool = False) -> Dict[str, Any]:
        """Execute web search"""
        try:
            if not query:
                return {"error": "Search query is required"}
            
            # Limit number of results
            num_results = min(max(1, num_results), 10)
            
            # Modify query based on parameters
            search_query = self._build_search_query(query, search_type, time_filter, site)
            
            # Perform search
            search_results = self._search_duckduckgo(search_query, num_results)
            
            if not search_results:
                return {"error": "No search results found"}
            
            # Extract content if requested
            if extract_content:
                search_results = self._extract_content_from_results(search_results)
            
            return {
                "success": True,
                "query": query,
                "search_query": search_query,
                "search_type": search_type,
                "time_filter": time_filter,
                "num_results": len(search_results),
                "results": search_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {"error": str(e)}
    
    def _build_search_query(self, query: str, search_type: str, time_filter: str, site: str) -> str:
        """Build search query with modifiers"""
        search_query = query
        
        # Add site filter
        if site:
            search_query = f"site:{site} {search_query}"
        
        # Add search type modifiers
        if search_type == "news":
            search_query = f"{search_query} news recent"
        elif search_type == "academic":
            search_query = f"{search_query} site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov"
        elif search_type == "images":
            search_query = f"{search_query} images"
        
        # Add time filter (DuckDuckGo doesn't support this directly, but we can add keywords)
        if time_filter == "day":
            search_query = f"{search_query} today"
        elif time_filter == "week":
            search_query = f"{search_query} this week"
        elif time_filter == "month":
            search_query = f"{search_query} this month"
        elif time_filter == "year":
            search_query = f"{search_query} {datetime.now().year}"
        
        return search_query
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        try:
            params = {
                'q': query,
                'b': '',  # Start from first result
                'kl': 'us-en',  # Language/region
                'df': '',  # Date filter
                's': '0',  # Start index
                'v': 'l',  # Layout
                'o': 'json',  # Output format
                'api': '/d.js'
            }
            
            response = self.session.get(self.search_engines["duckduckgo"], params=params, timeout=10)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            result_items = soup.find_all('div', class_='result')[:num_results]
            
            for item in result_items:
                try:
                    # Extract title
                    title_elem = item.find('a', class_='result__a')
                    title = title_elem.get_text(strip=True) if title_elem else "No title"
                    
                    # Extract URL
                    url = title_elem.get('href') if title_elem else ""
                    
                    # Extract snippet
                    snippet_elem = item.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Extract displayed URL
                    url_elem = item.find('span', class_='result__url')
                    display_url = url_elem.get_text(strip=True) if url_elem else url
                    
                    if title and url:
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "display_url": display_url,
                            "source": "DuckDuckGo"
                        })
                
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            return self._fallback_search(query, num_results)
    
    def _fallback_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Fallback search method"""
        try:
            # Simple fallback using a different approach
            search_url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            
            response = self.session.post(search_url, data=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Look for results with different selectors
            for link in soup.find_all('a', href=True)[:num_results * 2]:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href.startswith('http') and text and len(text) > 10:
                    # Skip internal DuckDuckGo links
                    if 'duckduckgo.com' not in href:
                        results.append({
                            "title": text[:100],
                            "url": href,
                            "snippet": f"Search result for: {query}",
                            "display_url": href,
                            "source": "DuckDuckGo (fallback)"
                        })
                        
                        if len(results) >= num_results:
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            return []
    
    def _extract_content_from_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and summarize content from search results"""
        enhanced_results = []
        
        for result in results:
            try:
                # Extract content from the webpage
                content = self._extract_webpage_content(result["url"])
                
                if content:
                    result["content"] = content
                    result["word_count"] = len(content.split())
                else:
                    result["content"] = result.get("snippet", "")
                    result["word_count"] = len(result["content"].split())
                
                enhanced_results.append(result)
                
            except Exception as e:
                logger.warning(f"Error extracting content from {result['url']}: {e}")
                result["content"] = result.get("snippet", "")
                result["word_count"] = len(result["content"].split())
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _extract_webpage_content(self, url: str, max_chars: int = 2000) -> str:
        """Extract main content from a webpage"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find main content areas
            content_selectors = [
                'article',
                'main',
                '[role="main"]',
                '.content',
                '.post-content',
                '.entry-content',
                '.article-content',
                '#content',
                '.main-content'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text(strip=True)
                    break
            
            # Fallback to body if no main content found
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text(strip=True)
            
            # Clean up the text
            content_text = self._clean_extracted_text(content_text)
            
            # Truncate if too long
            if len(content_text) > max_chars:
                content_text = content_text[:max_chars] + "..."
            
            return content_text
            
        except Exception as e:
            logger.warning(f"Error extracting content from {url}: {e}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common unwanted patterns
        text = re.sub(r'Cookie.*?Policy', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Privacy.*?Policy', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Terms.*?Service', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Subscribe.*?Newsletter', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Follow.*?us', '', text, flags=re.IGNORECASE)
        
        # Remove navigation-like text
        text = re.sub(r'\b(Home|About|Contact|Menu|Navigation)\b', '', text, flags=re.IGNORECASE)
        
        # Remove multiple dots and dashes
        text = re.sub(r'\.{3,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)
        
        return text.strip()
    
    def _is_relevant_content(self, text: str, min_length: int = 50) -> bool:
        """Check if extracted content is relevant and substantial"""
        if not text or len(text) < min_length:
            return False
        
        # Check if it's mostly navigation or boilerplate
        navigation_words = ['home', 'about', 'contact', 'menu', 'login', 'register', 'search']
        words = text.lower().split()
        
        if len(words) < 20:
            return False
        
        nav_word_count = sum(1 for word in words if word in navigation_words)
        nav_ratio = nav_word_count / len(words)
        
        return nav_ratio < 0.3  # Less than 30% navigation words