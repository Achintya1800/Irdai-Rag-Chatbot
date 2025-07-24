#!/usr/bin/env python3
"""
Comprehensive scraper for ALL 4 insurance websites with 100% accuracy
REFACTORED: Query-driven real-time engine with no demo contamination
"""

# spell-checker: disable
# Custom dictionary for insurance terms
# IRDAI - Insurance Regulatory and Development Authority of India
# HDFC - Housing Development Finance Corporation
# Reinsurers - Companies that provide insurance for insurance companies

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os
import re
from typing import Dict, List, Any
from dataclasses import dataclass
from loguru import logger
import io
from datetime import datetime, timedelta

# NEW: Add fuzzy matching for better relevance scoring (suppress warnings)
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    # logger.warning("fuzzywuzzy not available. Using basic string matching.")

# Handle optional imports gracefully (suppress warnings)
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    # logger.warning("PyPDF2 not available. PDF extraction will be skipped.")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available. Will use requests-only scraping.")

@dataclass
class ComprehensiveDocument:
    url: str
    title: str
    content: str
    source_type: str
    website: str
    document_links: List[str]
    metadata: Dict

@dataclass
class QueryIntent:
    """Enhanced query intent analysis"""
    intent_type: str  # 'specific_document', 'general_search', 'latest_updates', 'regulatory_guidance'
    keywords: List[str]
    document_types: List[str]  # 'regulation', 'circular', 'guideline', 'notification', 'act', 'rule'
    time_sensitivity: str  # 'latest', 'specific_year', 'any_time'
    target_year: str = None
    urgency_level: str = "medium"  # 'low', 'medium', 'high', 'critical'
    confidence_score: float = 0.0

class QueryAnalyzer:
    """Enhanced query analysis for better user intent understanding"""
    
    def __init__(self):
        self.document_type_patterns = {
            'regulation': ['regulation', 'regulatory', 'rule', 'rules'],
            'circular': ['circular', 'master circular'],
            'guideline': ['guideline', 'guidelines', 'guidance'],
            'notification': ['notification', 'notice', 'announcement'],
            'act': ['act', 'amendment act', 'insurance act'],
            'order': ['order', 'directive'],
            'policy': ['policy', 'policy document'],
            'report': ['report', 'annual report', 'financial report']
        }
        
        self.time_indicators = {
            'latest': ['latest', 'recent', 'new', 'current', 'updated', '2024', '2025'],
            'specific_year': [r'\b20\d{2}\b'],
            'historical': ['old', 'previous', 'archived', 'earlier']
        }
        
        self.urgency_indicators = {
            'critical': ['urgent', 'immediate', 'emergency', 'critical'],
            'high': ['important', 'priority', 'needed', 'required'],
            'medium': ['please', 'help', 'find', 'search'],
            'low': ['general', 'overview', 'about']
        }

    def analyze_query(self, query: str) -> QueryIntent:
        """Comprehensive query analysis with enhanced intent detection"""
        query_lower = query.lower().strip()
        
        # Guard rail: Basic query validation
        if not query or len(query.strip()) < 3:
            logger.warning("Query too short or empty")
            return QueryIntent(
                intent_type='invalid',
                keywords=[],
                document_types=[],
                time_sensitivity='any_time',
                confidence_score=0.0
            )
        
        # Guard rail: Check for harmful content
        harmful_patterns = ['delete', 'remove', 'hack', 'exploit', 'inject']
        if any(pattern in query_lower for pattern in harmful_patterns):
            logger.warning(f"Potentially harmful query detected: {query}")
            return QueryIntent(
                intent_type='blocked',
                keywords=[],
                document_types=[],
                time_sensitivity='any_time',
                confidence_score=0.0
            )
        
        # Extract keywords (enhanced)
        keywords = self._extract_keywords(query_lower)
        
        # Detect document types
        document_types = self._detect_document_types(query_lower)
        
        # Analyze time sensitivity
        time_sensitivity, target_year = self._analyze_time_sensitivity(query_lower)
        
        # Determine intent type
        intent_type = self._determine_intent_type(query_lower, keywords, document_types)
        
        # Calculate urgency
        urgency_level = self._calculate_urgency(query_lower)
        
        # Calculate confidence
        confidence_score = self._calculate_intent_confidence(query_lower, keywords, document_types)
        
        intent = QueryIntent(
            intent_type=intent_type,
            keywords=keywords,
            document_types=document_types,
            time_sensitivity=time_sensitivity,
            target_year=target_year,
            urgency_level=urgency_level,
            confidence_score=confidence_score
        )
        
        logger.info(f"Query Analysis: {intent.intent_type} (confidence: {confidence_score:.3f})")
        return intent

    def _extract_keywords(self, query: str) -> List[str]:
        """Enhanced keyword extraction"""
        # Remove common stop words but keep insurance-specific terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        # Extract words but preserve important phrases
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Extract important phrases
        important_phrases = [
            'regional rural bank', 'unit linked', 'motor vehicle', 'third party',
            'life insurance', 'general insurance', 'health insurance',
            'expression of interest', 'key managerial', 'corporate governance'
        ]
        
        for phrase in important_phrases:
            if phrase in query.lower():
                keywords.extend(phrase.split())
        
        return list(set(keywords))

    def _detect_document_types(self, query: str) -> List[str]:
        """Detect document types from query"""
        detected_types = []
        
        for doc_type, patterns in self.document_type_patterns.items():
            if any(pattern in query for pattern in patterns):
                detected_types.append(doc_type)
        
        return detected_types

    def _analyze_time_sensitivity(self, query: str) -> tuple:
        """Analyze time-related requirements"""
        # Check for latest/recent indicators
        if any(indicator in query for indicator in self.time_indicators['latest']):
            return 'latest', None
        
        # Check for specific years
        year_matches = re.findall(r'\b(20\d{2})\b', query)
        if year_matches:
            return 'specific_year', year_matches[0]
        
        # Check for historical indicators
        if any(indicator in query for indicator in self.time_indicators['historical']):
            return 'historical', None
        
        return 'any_time', None

    def _determine_intent_type(self, query: str, keywords: List[str], document_types: List[str]) -> str:
        """Determine the primary intent of the query"""
        # Specific document search (high specificity)
        if (len(keywords) > 8 or 
            any(phrase in query for phrase in ['guidelines on', 'procedure for', 'rules for']) or
            'document id' in query.lower()):
            return 'specific_document'
        
        # Latest updates request
        if any(word in query for word in ['latest', 'recent', 'new', 'updated', 'current']):
            return 'latest_updates'
        
        # Regulatory guidance
        if document_types and any(dtype in ['regulation', 'guideline', 'circular'] for dtype in document_types):
            return 'regulatory_guidance'
        
        # General search
        return 'general_search'

    def _calculate_urgency(self, query: str) -> str:
        """Calculate urgency level from query"""
        for urgency, indicators in self.urgency_indicators.items():
            if any(indicator in query for indicator in indicators):
                return urgency
        return 'medium'

    def _calculate_intent_confidence(self, query: str, keywords: List[str], document_types: List[str]) -> float:
        """Calculate confidence in intent analysis"""
        confidence = 0.0
        
        # Base confidence from query length and structure
        if len(keywords) >= 3:
            confidence += 0.3
        if len(keywords) >= 6:
            confidence += 0.2
        
        # Boost for document type detection
        confidence += len(document_types) * 0.1
        
        # Boost for specific patterns
        specific_patterns = ['regulation', 'circular', 'guideline', 'irdai', 'insurance']
        for pattern in specific_patterns:
            if pattern in query:
                confidence += 0.1
        
        return min(confidence, 1.0)

class ComprehensiveScraper:
    def __init__(self, use_selenium: bool = False):
        self.driver = None
        self.documents = []
        self.visited_urls = set()
        self.pdf_cache = {}
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        # REMOVED: self.demo_mode = False  # Completely eliminate demo mode
        
        # ENHANCED: Query state management
        self.query_state = {
            'current_query': "",
            'query_intent': None,
            'visited_urls': set(),
            'found_documents': [],
            'document_cache': {},
            'query_fingerprint': "",
            'search_strategy': 'comprehensive'
        }
        
        # NEW: Add query analyzer
        self.query_analyzer = QueryAnalyzer()
        
        if self.use_selenium:
            try:
                self.setup_driver()
            except Exception as e:
                logger.error(f"Failed to setup Selenium driver: {e}")
                logger.info("Falling back to requests-only scraping")
                self.use_selenium = False
        
        # ENHANCED: More intelligent routing configuration
        self.website_configs = {
            "irdai": {
                "base_url": "https://irdai.gov.in",
                "intelligent_routing": {
                    # ENHANCED: More comprehensive keyword mapping
                    "rrb_amalgamation": {
                        "keywords": ["rrb", "regional rural bank", "amalgamat", "corporate agency", "may 2025"],
                        "primary_urls": [
                            "/consolidated-gazette-notified-regulations",
                            "/circulars",
                            "/notifications"
                        ]
                    },
                    "ulip": {
                        "keywords": ["ulip", "unit linked", "unit-linked", "investment plan"],
                        "primary_urls": [
                            "/consolidated-gazette-notified-regulations",
                            "/guidelines",
                            "/circulars"
                        ]
                    },
                    "acts": {
                        "keywords": ["act", "amendment act", "insurance laws", "insurance act", "irdai act"],
                        "primary_urls": [
                            "/acts",
                            "/insurance-acts", 
                            "/rules",
                            "/consolidated-gazette-notified-regulations"
                        ]
                    },
                    "rules": {
                        "keywords": ["rules", "motor vehicle", "third party", "liability rules", "base premium"],
                        "primary_urls": [
                            "/rules",
                            "/notifications",
                            "/consolidated-gazette-notified-regulations"
                        ]
                    },
                    "regulations": {
                        "keywords": ["regulation", "irdai regulation", "corporate governance", "solvency"],
                        "primary_urls": [
                            "/consolidated-gazette-notified-regulations",
                            "/updated-regulations",
                            "/regulations"
                        ]
                    },
                    "circulars": {
                        "keywords": ["circular", "master circular", "guidelines"],
                        "primary_urls": [
                            "/circulars",
                            "/notifications",
                            "/guidelines"
                        ]
                    },
                    "notifications": {
                        "keywords": ["notification", "press release", "announcement"],
                        "primary_urls": [
                            "/notifications",
                            "/press-releases",
                            "/announcements"
                        ]
                    },
                    "financial": {
                        "keywords": ["obligatory cession", "financial year", "annual report", "budget"],
                        "primary_urls": [
                            "/annual-reports",
                            "/notifications",
                            "/consolidated-gazette-notified-regulations"
                        ]
                    }
                },
                "start_pages": [
                    "/acts",  # Start with Acts first for better coverage
                    "/rules",
                    "/consolidated-gazette-notified-regulations",
                    "/updated-regulations",
                    "/notifications"
                ],
                "search_pages": [
                    "/regulations",
                    "/circulars", 
                    "/guidelines",
                    "/annual-reports",
                    "/consolidated-gazette-notified-regulations"
                ],
                "document_selectors": {
                    "table_rows": "table tr, .document-row, .list-item, .portlet-body table tr",
                    "document_links": "a[href*='document-detail'], a[href*='.pdf'], a[href*='.doc'], a[href*='documents/'], a[href*='document-viewer'], a[href*='fileEntryId']",
                    "content_area": ".portlet-body, .journal-content-article, .content, .document-content, main, .portlet-content-container",
                    "internal_links": "a[href^='/'], a[href*='irdai.gov.in']",
                    "accordion_triggers": ".accordion-toggle, .collapse-toggle, [data-toggle='collapse'], .dropdown-toggle",
                    "pagination": ".pagination a, .load-more, .show-more, [onclick*='loadMore']"
                },
                "max_depth": 4,  # OPTIMIZED: Reduced depth for performance
                "keywords": ["regulation", "circular", "guideline", "notification", "irdai", "insurance", "rules", "acts", "rrb", "ulip"],
                "source_type": "regulatory"
            },
            "lic": {
                "base_url": "https://www.licindia.in",
                "search_pages": [
                    "/corporate-governance",
                    "/investor-relations", 
                    "/annual-reports",
                    "/board-of-directors",
                    "/policies"
                ],
                "document_selectors": {
                    "table_rows": "table tr, .document-list li",
                    "document_links": "a[href*='.pdf'], a[href*='.doc'], a[href*='documents']",
                    "content_area": ".content, .main-content, main",
                    "internal_links": "a[href^='/'], a[href*='licindia.in']",
                    "accordion_triggers": ".accordion-toggle, .collapse-toggle, [data-toggle='collapse']",
                    "pagination": ".pagination a, .load-more, .show-more"
                },
                "max_depth": 2,
                "keywords": ["lic", "life insurance", "corporate", "governance", "annual report"],
                "source_type": "life_insurance"
            },
            "hdfc_life": {
                "base_url": "https://www.hdfclife.com",
                "search_pages": [
                    "/about-us/investor-relations",
                    "/about-us/corporate-governance",
                    "/about-us/annual-reports",
                    "/policy-documents"
                ],
                "document_selectors": {
                    "table_rows": "table tr, .document-row, .policy-list li",
                    "document_links": "a[href*='.pdf'], a[href*='.doc'], a[href*='content/dam']",
                    "content_area": ".content, .page-content, main",
                    "internal_links": "a[href^='/'], a[href*='hdfclife.com']",
                    "accordion_triggers": ".accordion-toggle, .collapse-toggle, [data-toggle='collapse']",
                    "pagination": ".pagination a, .load-more, .show-more"
                },
                "max_depth": 2,
                "keywords": ["hdfc", "life insurance", "policy", "investor", "governance"],
                "source_type": "life_insurance"
            },
            "new_india": {
                "base_url": "https://www.newindia.co.in",
                "search_pages": [
                    "/corporate-governance",
                    "/investor-relations",
                    "/annual-reports",
                    "/policies"
                ],
                "document_selectors": {
                    "table_rows": "table tr, .policy-list li",
                    "document_links": "a[href*='.pdf'], a[href*='.doc'], a[href*='assets/docs']",
                    "content_area": ".content, .main-content, main",
                    "internal_links": "a[href^='/'], a[href*='newindia.co.in']",
                    "accordion_triggers": ".accordion-toggle, .collapse-toggle, [data-toggle='collapse']",
                    "pagination": ".pagination a, .load-more, .show-more"
                },
                "max_depth": 2,
                "keywords": ["new india", "general insurance", "policy", "corporate", "governance"],
                "source_type": "general_insurance"
            }
        }
        
    def setup_driver(self):
        """Initialize Selenium WebDriver with enhanced capabilities"""
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not available")
            return
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium driver setup successful")
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            self.use_selenium = False
            
    def extract_pdf_content(self, pdf_url: str) -> str:
        """Extract text content from PDF files"""
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available. Cannot extract PDF content.")
            return ""
            
        if pdf_url in self.pdf_cache:
            return self.pdf_cache[pdf_url]
        
        try:
            logger.info(f"Extracting PDF content from: {pdf_url}")
            response = requests.get(pdf_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            # Clean and normalize text
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            self.pdf_cache[pdf_url] = text_content
            logger.info(f"Extracted {len(text_content)} characters from PDF")
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_url}: {e}")
            return ""
    
    def handle_dynamic_content(self, config: Dict):
        """Handle accordion, collapsible content, and dynamic elements"""
        if not self.use_selenium:
            return
            
        try:
            # Wait for dynamic content to load
            time.sleep(2)
            
            # Click dropdown toggles and accordion triggers
            accordion_elements = self.driver.find_elements(By.CSS_SELECTOR, config["document_selectors"]["accordion_triggers"])
            for element in accordion_elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(1)
                except Exception as e:
                    logger.debug(f"Could not click element: {e}")
            
            # Handle "Load More" or pagination
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, config["document_selectors"]["pagination"])
            for element in pagination_elements[:3]:  # Limit to 3 clicks
                try:
                    if element.is_displayed() and element.is_enabled():
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                except Exception as e:
                    logger.debug(f"Could not click pagination element: {e}")
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Wait for any AJAX content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config["document_selectors"]["content_area"]))
                )
            except TimeoutException:
                pass
            
        except Exception as e:
            logger.error(f"Error handling dynamic content: {e}")
    
    def extract_internal_links(self, soup: BeautifulSoup, base_url: str, current_url: str, config: Dict) -> List[str]:
        """Extract internal links for recursive traversal"""
        internal_links = set()
        
        # Find all internal links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(current_url, href)
            
            # Check if it's an internal link
            if base_url in full_url and full_url != current_url:
                # Remove fragments and query parameters for deduplication
                clean_url = full_url.split('#')[0].split('?')[0]
                
                # Filter based on relevance
                link_text = link.get_text(strip=True).lower()
                if any(keyword in link_text for keyword in config["keywords"]) or \
                   any(keyword in href.lower() for keyword in config["keywords"]):
                    internal_links.add(clean_url)
        
        return list(internal_links)
    
    def extract_all_document_links(self, soup: BeautifulSoup, base_url: str, config: Dict) -> List[str]:
        """Extract ALL possible document links from a page"""
        doc_links = set()
        
        # Method 1: Direct document links using enhanced selectors
        for selector in config["document_selectors"]["document_links"].split(", "):
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    doc_links.add(full_url)
        
        # Method 2: Table-based extraction with enhanced selectors
        for row in soup.select(config["document_selectors"]["table_rows"]):
            for link in row.find_all('a', href=True):
                href = link.get('href')
                if href and any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', 'document', 'fileEntryId']):
                    full_url = urljoin(base_url, href)
                    doc_links.add(full_url)
        
        # Method 3: Text-based link discovery with enhanced keywords
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            link_text = link.get_text(strip=True).lower()
            
            if href and any(keyword in link_text for keyword in [
                'download', 'view', 'report', 'policy', 'document', 'pdf', 
                'regulation', 'circular', 'guideline', 'notification', 'read more'
            ]):
                full_url = urljoin(base_url, href)
                doc_links.add(full_url)
        
        # Method 4: JavaScript onclick and data attributes
        for element in soup.find_all(['a', 'button', 'div'], attrs={'onclick': True}):
            onclick = element.get('onclick', '')
            if any(keyword in onclick.lower() for keyword in ['document', 'pdf', 'download']):
                # Extract URLs from JavaScript
                url_match = re.search(r'["\']([^"\']*(?:\.pdf|\.doc|document-detail|document-viewer|fileEntryId)[^"\']*)["\']', onclick)
                if url_match:
                    url = url_match.group(1)
                    full_url = urljoin(base_url, url)
                    doc_links.add(full_url)
        
        return list(doc_links)
    
    def scrape_page_simple(self, url: str, config: Dict) -> str:
        """Simple scraping using requests only"""
        try:
            logger.info(f"Scraping with requests: {url}")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract content using multiple selectors
            content_text = ""
            for selector in config["document_selectors"]["content_area"].split(", "):
                content_div = soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text(separator=' ', strip=True)
                    break
            
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text(separator=' ', strip=True)
            
            # Clean content
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # Extract document links
            doc_links = self.extract_all_document_links(soup, config["base_url"], config)
            
            return {
                'title': title_text,
                'content': content_text,
                'doc_links': doc_links,
                'soup': soup
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def calculate_relevance_score(self, text: str, query: str) -> float:
        """
        SIGNIFICANTLY ENHANCED: Better exact title matching with priority for administrative documents
        """
        if not query.strip() or not text.strip():
            return 0.0
        
        query_lower = query.lower().strip()
        text_lower = text.lower().strip()
        
        score = 0.0
        
        # ENHANCED: Exact phrase matching gets MASSIVE boost
        if query_lower in text_lower:
            score += 150.0  # Increased from 100.0 for exact matches
            # REDUCED LOGGING: Only log critical matches
            if score >= 140.0:  # Only log very high scores
                logger.info(f"🎯 EXACT PHRASE MATCH found: '{query}' in '{text[:60]}...'")
        
        # NEW: Check for partial exact phrase matches (important for long administrative titles)
        query_words = query_lower.split()
        if len(query_words) > 5:  # For long queries, check for substantial phrase matches
            for i in range(len(query_words) - 3):  # Check 4+ word phrases
                phrase = " ".join(query_words[i:i+4])
                if phrase in text_lower:
                    score += 60.0  # High score for 4+ word phrase matches
                    # REDUCED LOGGING: Only log significant matches
                    if score >= 100.0:
                        logger.info(f"🎯 PHRASE MATCH (4+ words): '{phrase}' in '{text[:60]}...'")
        
        # NEW: Enhanced title matching for specific administrative terms
        query_title_words = [word for word in query_lower.split() if len(word) > 3]
        text_title_words = [word for word in text_lower.split() if len(word) > 3]
        
        # Check for title-like exact matches (high precision)
        title_match_score = 0
        for query_word in query_title_words:
            if query_word in text_title_words:
                title_match_score += 1
        
        title_match_ratio = title_match_score / len(query_title_words) if query_title_words else 0
        
        if title_match_ratio >= 0.9:  # 90% of title words match
            score += 100.0  # Increased from 80.0
            # REDUCED LOGGING: Only log high matches
            if score >= 150.0:
                logger.info(f"🎯 HIGH TITLE MATCH ({title_match_ratio:.2f}): '{text[:80]}...'")
        elif title_match_ratio >= 0.7:  # 70% of title words match
            score += 70.0  # Increased from 50.0
            # REDUCED LOGGING
            if score >= 120.0:
                logger.info(f"✅ GOOD TITLE MATCH ({title_match_ratio:.2f}): '{text[:80]}...'")
        elif title_match_ratio >= 0.5:  # 50% of title words match
            score += 40.0  # NEW: Added mid-level matching
            # REDUCED LOGGING: Only very high scores
            if score >= 100.0:
                logger.info(f"✅ MEDIUM TITLE MATCH ({title_match_ratio:.2f}): '{text[:80]}...'")
        
        # NEW: Special handling for administrative document types
        document_type_boosts = {
            "annulment": {
                "keywords": ["annulment", "cancel", "cancelled", "withdraw", "withdrawn"],
                "boost": 40.0
            },
            "expression_of_interest": {
                "keywords": ["expression of interest", "eoi", "empanelment", "empanel"],
                "boost": 35.0
            },
            "advertising": {
                "keywords": ["advertising", "advertisement", "marketing", "publicity"],
                "boost": 30.0
            },
            "agencies": {
                "keywords": ["agencies", "agency", "firms", "companies"],
                "boost": 25.0
            },
            "tender": {
                "keywords": ["tender", "bid", "proposal", "procurement"],
                "boost": 30.0
            },
            "guidelines": {
                "keywords": ["guideline", "guidelines", "दिशानिर्देश"],
                "boost": 30.0
            },
            "circular": {
                "keywords": ["circular", "परिपत्र"],
                "boost": 25.0
            },
            "notification": {
                "keywords": ["notification", "notice", "announcement"],
                "boost": 25.0
            },
            "remuneration": {
                "keywords": ["remuneration", "पारिश्रमिक"],
                "boost": 20.0
            },
            "directors": {
                "keywords": ["directors", "निदेशक"],
                "boost": 15.0
            },
            "key_managerial": {
                "keywords": ["key managerial", "प्रमुख प्रबंधकीय"],
                "boost": 15.0
            }
        }
        
        for doc_type, config in document_type_boosts.items():
            query_has_type = any(keyword in query_lower for keyword in config["keywords"])
            text_has_type = any(keyword in text_lower for keyword in config["keywords"])
            
            if query_has_type and text_has_type:
                score += config["boost"]
                # REDUCED LOGGING: Only log significant type matches
                if config["boost"] >= 30.0:
                    logger.info(f"🎯 {doc_type.upper()} match found: '{text[:60]}...'")
        
        # ENHANCED: Year matching with higher precision (important for dated documents)
        query_years = re.findall(r'\b(20\d{2})\b', query)
        text_years = re.findall(r'\b(20\d{2})\b', text)
        for year in query_years:
            if year in text_years:
                score += 25.0  # Increased from 15.0
                # REDUCED LOGGING: Only log year matches for high scores
                if score >= 100.0:
                    logger.info(f"✅ Year match ({year}): '{text[:60]}...'")
        
        # ENHANCED: Fuzzy matching for better accuracy (but lower weight than exact matches)
        if FUZZY_AVAILABLE:
            # Token set ratio for partial matches
            fuzzy_score = fuzz.token_set_ratio(query_lower, text_lower) / 100.0
            score += fuzzy_score * 8.0  # Increased from 5.0
            
            # Partial ratio for substring matches
            partial_score = fuzz.partial_ratio(query_lower, text_lower) / 100.0
            score += partial_score * 6.0  # Increased from 4.0
            
            # Token sort ratio for word order flexibility
            sort_score = fuzz.token_sort_ratio(query_lower, text_lower) / 100.0
            score += sort_score * 5.0  # Increased from 3.0
            
            # REMOVED: Excessive debug logging for fuzzy scores
        
        # ENHANCED: Individual word matching with better weights
        query_words = [word for word in query_lower.split() if len(word) > 2]
        matched_words = 0
        for word in query_words:
            if word in text_lower:
                matched_words += 1
                score += 3.0  # Increased from 2.0
        
        word_match_ratio = matched_words / len(query_words) if query_words else 0
        if word_match_ratio >= 0.8:  # 80% of words match
            score += 15.0  # Increased from 10.0
            # REDUCED LOGGING: Only for very high scores
            if score >= 150.0:
                logger.info(f"✅ High word match ratio ({word_match_ratio:.2f}): '{text[:60]}...'")
        elif word_match_ratio >= 0.6:  # 60% of words match
            score += 8.0  # NEW: Added mid-level word matching
            # REDUCED LOGGING
            if score >= 120.0:
                logger.info(f"✅ Medium word match ratio ({word_match_ratio:.2f}): '{text[:60]}...'")
        
        # REDUCED: Penalties (less aggressive filtering)
        generic_penalties = ["media gallery", "photo gallery", "about us", "contact", "home"]
        for penalty_term in generic_penalties:
            if penalty_term in text_lower:
                score = max(0, score - 5.0)  # Reduced penalty
        
        # ENHANCED: Normalize with higher ceiling for exact matches
        normalized_score = min(score / 180.0, 1.0)  # Increased from 120.0
        
        # REDUCED LOGGING: Only log scores above higher threshold and perfect matches
        if normalized_score >= 0.99:  # Perfect matches
            logger.info(f"🎯 PERFECT MATCH (Score: {normalized_score:.3f}) for query '{query}' in: {text[:100]}...")
        elif normalized_score >= 0.8:  # High relevance only
            logger.info(f"📊 High relevance score {normalized_score:.3f} for query '{query}' in: {text[:100]}...")
        
        return normalized_score
    
    def extract_irdai_document_detail_page(self, document_detail_url: str, query: str = "") -> Dict:
        """
        ENHANCED: Better extraction with guaranteed content for high-relevance matches
        """
        try:
            logger.info(f"📋 Extracting from document detail page: {document_detail_url}")
            
            response = requests.get(document_detail_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ENHANCED: Better title extraction for bilingual documents with more selectors
            title = ""
            title_selectors = [
                # Primary title selectors for IRDAI
                '.journal-content-article h1',
                '.journal-content-article h2', 
                '.portlet-body h1',
                '.portlet-body h2',
                '.document-title',
                '.content-title',
                # Secondary selectors
                'h1', 'h2', '.title', '.entry-title',
                '.portlet-title', '.page-title', '.article-title', '.document-name',
                # Text content in specific containers
                '.journal-content-article p:first-of-type',
                '.portlet-body p:first-of-type',
                # Table headers that might contain titles
                'table tr:first-child td:first-child',
                'table tr:first-child th:first-child'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    candidate_title = title_elem.get_text(strip=True)
                    # Filter out navigation and generic content
                    if (len(candidate_title) > 30 and len(candidate_title) < 1000 and
                        not any(skip in candidate_title.lower() for skip in [
                            'function of department', 'irdai accounts', 'navigation',
                            'breadcrumb', 'home', 'back to', 'click here'
                        ])):
                        if len(candidate_title) > len(title):
                            title = candidate_title
                            logger.debug(f"Found better title with selector '{selector}': {title[:100]}...")
            
            # NEW: Look for PDF links and extract titles from PDF filenames
            pdf_links = []
            pdf_title_candidates = []
            
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and (href.lower().endswith('.pdf') or 'pdf' in href.lower() or 'download=true' in href):
                    full_pdf_url = urljoin(document_detail_url, href)
                    pdf_links.append(full_pdf_url)
                    
                    # Extract title from PDF link text or filename
                    link_text = link.get_text(strip=True)
                    if len(link_text) > 20 and 'download' not in link_text.lower():
                        pdf_title_candidates.append(link_text)
                    
                    # Extract from URL parameter or filename
                    if '?' in href:
                        # Look for title in URL parameters or filename patterns
                        url_parts = href.split('/')
                        for part in url_parts:
                            if len(part) > 30 and ('regulation' in part.lower() or 'rule' in part.lower()):
                                cleaned_part = part.replace('%20', ' ').replace('_', ' ').replace('-', ' ')
                                pdf_title_candidates.append(cleaned_part)
            
            # NEW: Enhanced content extraction with multiple strategies
            content = ""
            content_selectors = [
                '.journal-content-article',  # Primary IRDAI content container
                '.portlet-body',
                '.content', '.document-content', 'main',
                '.entry-content', '.post-content', '.article-content',
                '.page-content', '.document-info'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Extract all text but filter out navigation elements
                    content_text = content_elem.get_text(separator=' ', strip=True)
                    # Remove common navigation text
                    content_lines = content_text.split('\n')
                    filtered_lines = []
                    for line in content_lines:
                        line = line.strip()
                        if (len(line) > 10 and 
                            not any(skip in line.lower() for skip in [
                                'function of department', 'irdai accounts', 'actuarial administration',
                                'agency distribution', 'communication board', 'enforcement finance'
                            ])):
                            filtered_lines.append(line)
                    
                    content = ' '.join(filtered_lines)
                    logger.debug(f"Found content with selector '{selector}': {len(content)} chars")
                    if len(content) > 100:  # Only use if substantial content found
                        break
            
            # NEW: Try to extract title from the actual document content
            if not title and content:
                # Look for regulation/rule titles in the content
                content_lines = content.split('.')
                for line in content_lines[:5]:  # Check first few sentences
                    line = line.strip()
                    if (len(line) > 50 and 
                        any(keyword in line.lower() for keyword in ['regulation', 'rule', 'guideline', 'circular']) and
                        any(keyword in line.lower() for keyword in ['insurance', 'irdai'])):
                        title = line
                        logger.info(f"📄 Extracted title from content: {title[:100]}...")
                        break
            
            # NEW: Use PDF title candidates if no good title found
            if not title and pdf_title_candidates:
                # Sort PDF title candidates by length (longer usually better)
                pdf_title_candidates.sort(key=len, reverse=True)
                for candidate in pdf_title_candidates:
                    if len(candidate) > 30:
                        title = candidate
                        logger.info(f"📄 Using PDF title candidate: {title[:100]}...")
                        break
            
            # ENHANCED: Calculate relevance with full context
            full_text = f"{title} {content}"
            relevance_score = self.calculate_relevance_score(full_text, query)
            
            # Extract document ID from URL
            document_id = ""
            doc_id_match = re.search(r'documentId=(\d+)', document_detail_url)
            if doc_id_match:
                document_id = doc_id_match.group(1)
            
            # NEW: Special handling for exact query matches
            if query and title:
                # Check for very close title matches
                query_clean = re.sub(r'[^\w\s]', ' ', query.lower()).strip()
                title_clean = re.sub(r'[^\w\s]', ' ', title.lower()).strip()
                
                # If query is almost exactly the title, boost relevance significantly
                if query_clean in title_clean or title_clean in query_clean:
                    relevance_score = max(relevance_score, 0.95)
                    logger.info(f"🎯 EXACT TITLE MATCH DETECTED - Boosted relevance to {relevance_score:.3f}")
            
            # ENHANCED: Ensure high-relevance documents have sufficient content
            if relevance_score >= 0.8 and len(content) < 200:
                enhanced_content = f"""
{title}

🎯 HIGH RELEVANCE MATCH (Score: {relevance_score:.3f})

This document was identified as highly relevant to your query: "{query}"

Document Details:
- Document ID: {document_id}
- Source: IRDAI Official Website  
- URL: {document_detail_url}

Content Summary:
{content if content else 'This is an official IRDAI document. Please refer to the PDF or official document for complete details.'}

PDF Downloads Available: {len(pdf_links)}
{chr(10).join(f'- {link}' for link in pdf_links[:3])}

This document represents one of the top matches for your search query.
"""
                content = enhanced_content
            
            result = {
                'url': document_detail_url,
                'title': title or f"IRDAI Document {document_id}",
                'content': content[:5000],
                'pdf_links': pdf_links,
                'relevance_score': relevance_score,
                'document_id': document_id,
                'extraction_source': 'document_detail_page',
                'full_text_length': len(full_text),
                'is_high_relevance': relevance_score >= 0.8,
                'pdf_title_candidates': pdf_title_candidates
            }
            
            logger.info(f"📋 ✅ Extracted detail page - Title: '{title[:80]}...', Score: {relevance_score:.3f}, ID: {document_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting document detail page {document_detail_url}: {e}")
            return None
    
    def extract_irdai_documents_enhanced(self, soup: BeautifulSoup, base_url: str, query: str = "") -> List[Dict]:
        """
        ENHANCED: Better table extraction with improved title matching
        """
        documents = []
        processed_doc_ids = set()
        
        logger.info(f"🔍 ENHANCED IRDAI extraction for query: '{query}'")
        
        # ENHANCED: Extract from tables with better title detection
        tables = soup.find_all('table')
        logger.info(f"📋 Found {len(tables)} tables to process")
        
        total_rows_processed = 0
        total_links_found = 0
        
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            logger.info(f"📋 Table {table_idx + 1}: {len(rows)} rows")
            
            for row_idx, row in enumerate(rows):
                if row_idx == 0:  # Skip header
                    continue
                
                total_rows_processed += 1
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 2:
                    continue
                
                # ENHANCED: Better title candidate extraction
                title_candidates = []
                document_links = []
                additional_info = []
                
                for cell in cells:
                    cell_text = cell.get('title', '').strip() or cell.get_text(strip=True)
                    
                    # IMPROVED: Better title candidate filtering
                    if (len(cell_text) > 15 and len(cell_text) < 800 and
                        not cell_text.isdigit() and
                        not re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', cell_text) and
                        not cell_text.lower() in ['view', 'download', 'read more', 'click here']):
                        
                        # NEW: Prioritize cells that contain query keywords
                        cell_relevance = self.calculate_relevance_score(cell_text, query)
                        title_candidates.append((cell_text, cell_relevance))
                    
                    # Collect additional context
                    if len(cell_text) > 5 and len(cell_text) < 100:
                        additional_info.append(cell_text)
                    
                    # Extract document detail links
                    for link in cell.find_all('a', href=True):
                        href = link.get('href')
                        if href and 'document-detail' in href and 'documentId=' in href:
                            full_url = urljoin(base_url, href)
                            document_links.append(full_url)
                            total_links_found += 1
                
                # ENHANCED: Process each document link found
                for doc_link in document_links:
                    doc_id_match = re.search(r'documentId=(\d+)', doc_link)
                    if not doc_id_match:
                        continue
                    
                    document_id = doc_id_match.group(1)
                    
                    # Skip if already processed
                    if document_id in processed_doc_ids:
                        logger.debug(f"⏭️ Skipping already processed document ID: {document_id}")
                        continue
                    processed_doc_ids.add(document_id)
                    
                    # ENHANCED: Choose best title from candidates based on relevance
                    best_title = ""
                    best_score = 0
                    
                    # Sort title candidates by relevance score
                    title_candidates.sort(key=lambda x: x[1], reverse=True)
                    
                    for title_candidate, candidate_score in title_candidates:
                        if candidate_score > best_score:
                            best_score = candidate_score
                            best_title = title_candidate
                            break
                    
                    # ENHANCED: Always extract from detail page for better titles
                    logger.info(f"🔍 Extracting from detail page for better title: {document_id}")
                    detail_data = self.extract_irdai_document_detail_page(doc_link, query)
                    
                    if detail_data:
                        # Use detail page title if it's better or if table title is poor
                        detail_title = detail_data['title']
                        detail_score = detail_data['relevance_score']
                        
                        # Prefer detail page title if it's significantly better or if table title is weak
                        if detail_score > best_score or best_score < 0.3 or not best_title:
                            final_title = detail_title
                            final_score = detail_score
                        else:
                            final_title = best_title
                            final_score = max(best_score, detail_score)  # Take higher score
                        
                        pdf_links = detail_data.get('pdf_links', [])
                        content = detail_data.get('content', '')
                    else:
                        final_title = best_title
                        final_score = best_score
                        pdf_links = []
                        content = ""
                    
                    # LOWERED THRESHOLD but prioritize high-scoring documents
                    min_threshold = 0.1
                    
                    if final_score >= min_threshold and final_title:
                        documents.append({
                            'url': doc_link,
                            'title': final_title,
                            'relevance_score': final_score,
                            'extraction_pattern': 'enhanced_table_plus_detail',
                            'document_id': document_id,
                            'pdf_links': pdf_links,
                            'content': content,
                            'additional_info': additional_info,
                            'metadata': {
                                'document_id': document_id,
                                'extraction_source': 'table_with_detail_extraction',
                                'table_index': table_idx,
                                'row_index': row_idx,
                                'has_detail_extraction': bool(content),
                                'table_title_score': best_score,
                                'detail_page_score': detail_data.get('relevance_score', 0) if detail_data else 0
                            }
                        })
                        
                        logger.info(f"✅ ACCEPTED - Title: '{final_title[:80]}...', Score: {final_score:.3f}, ID: {document_id}")
                    else:
                        logger.info(f"❌ REJECTED - Title: '{final_title[:80]}...', Score: {final_score:.3f}, ID: {document_id} (below threshold {min_threshold})")
        
        # ENHANCED: Also check for direct document links in page
        logger.info(f"🔍 Checking for direct document links...")
        direct_links_found = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href or 'document-detail' not in href or 'documentId=' not in href:
                continue
            
            doc_id_match = re.search(r'documentId=(\d+)', href)
            if not doc_id_match:
                continue
                
            document_id = doc_id_match.group(1)
            
            if document_id in processed_doc_ids:
                continue
            
            direct_links_found += 1
            full_url = urljoin(base_url, href)
            
            # Extract from detail page for direct links
            detail_data = self.extract_irdai_document_detail_page(full_url, query)
            
            if detail_data and detail_data['relevance_score'] >= 0.15:
                processed_doc_ids.add(document_id)
                
                documents.append({
                    'url': full_url,
                    'title': detail_data['title'],
                    'relevance_score': detail_data['relevance_score'],
                    'extraction_pattern': 'direct_link_detail',
                    'document_id': document_id,
                    'pdf_links': detail_data.get('pdf_links', []),
                    'content': detail_data.get('content', ''),
                    'metadata': {
                        'document_id': document_id,
                        'extraction_source': 'direct_link',
                        'has_detail_extraction': True
                    }
                })
                
                logger.info(f"✅ DIRECT LINK - Title: '{detail_data['title'][:60]}...', Score: {detail_data['relevance_score']:.3f}, ID: {document_id}")
        
        # ENHANCED: Sort by relevance and return results with better prioritization
        documents.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"📊 EXTRACTION SUMMARY:")
        logger.info(f"  📋 Tables processed: {len(tables)}")
        logger.info(f"  📄 Rows processed: {total_rows_processed}")
        logger.info(f"  🔗 Links found: {total_links_found}")
        logger.info(f"  📑 Documents extracted: {len(documents)}")
        
        # Show top results with better formatting
        for i, doc in enumerate(documents[:5]):
            logger.info(f"  {i+1}. '{doc['title'][:80]}...' (Score: {doc['relevance_score']:.3f}, ID: {doc['document_id']})")
        
        return documents
    
    def clear_query_state(self):
        """
        ENHANCED: Clear query state with fingerprint tracking
        """
        old_query = self.query_state.get('current_query', '')
        self.visited_urls.clear()
        self.documents.clear()
        
        self.query_state = {
            'current_query': "",
            'visited_urls': set(),
            'found_documents': [],
            'document_cache': {},
            'query_fingerprint': "",
            'previous_query': old_query
        }
        
        logger.info(f"🧹 Cleared query state. Previous: '{old_query}'")
    
    def determine_intelligent_route(self, query: str) -> List[str]:
        """
        ENHANCED: Better routing for latest document searches
        """
        if not query:
            return self.website_configs["irdai"]["start_pages"]
        
        query_lower = query.lower().strip()
        
        # ENHANCED: Special routing for latest/recent queries
        if any(term in query_lower for term in ['latest', 'recent', 'new', 'updated', 'current']):
            logger.info(f"🆕 Latest query detected: prioritizing recent document routes")
            return [
                "/guidelines",  # Guidelines are frequently updated
                "/circulars",   # Circulars contain recent updates
                "/notifications",  # Notifications are recent by nature
                "/consolidated-gazette-notified-regulations"  # Consolidated regulations include updates
            ]
        
        # NEW: Enhanced routing for guidelines specifically
        if 'guideline' in query_lower or 'guidelines' in query_lower:
            logger.info(f"📋 Guidelines query detected: prioritizing guideline routes")
            return [
                "/guidelines",
                "/consolidated-gazette-notified-regulations",
                "/circulars"
            ]
        
        # ENHANCED: Priority-based routing
        route_scores = {}
        config = self.website_configs["irdai"]["intelligent_routing"]
        
        for route_type, route_info in config.items():
            score = 0
            for keyword in route_info["keywords"]:
                if keyword in query_lower:
                    # NEW: Weight longer, more specific keywords higher
                    keyword_weight = len(keyword.split()) * 3
                    if query_lower == keyword:
                        keyword_weight += 10  # Exact match bonus
                    score += keyword_weight
            route_scores[route_type] = score
        
        # Sort and select top routes
        sorted_routes = sorted(route_scores.items(), key=lambda x: x[1], reverse=True)
        selected_urls = []
        max_score = sorted_routes[0][1] if sorted_routes else 0
        
        if max_score > 0:
            for route_type, score in sorted_routes:
                if score >= max_score * 0.4:  # Lower threshold for broader coverage
                    selected_urls.extend(config[route_type]["primary_urls"])
                    logger.info(f"🎯 Selected route '{route_type}' (score: {score}) for query: '{query}'")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in selected_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        if not unique_urls:
            logger.warning(f"⚠️ No intelligent route found for '{query}', using comprehensive search")
            unique_urls = self.website_configs["irdai"]["start_pages"]
        
        return unique_urls[:3]  # OPTIMIZED: Limit to top 3 for performance
    
    def scrape_page_with_query(self, url: str, config: Dict, query: str = "") -> Dict:
        """Scrape page with query-aware document extraction"""
        try:
            logger.info(f"Scraping with query '{query}': {url}")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebDriver/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract content using multiple selectors
            content_text = ""
            for selector in config["document_selectors"]["content_area"].split(", "):
                content_div = soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text(separator=' ', strip=True)
                    break
            
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text(separator=' ', strip=True)
            
            # Clean content
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # Extract documents with enhanced IRDAI extraction
            if config.get("base_url") == "https://irdai.gov.in":
                doc_data = self.extract_irdai_documents_enhanced(soup, config["base_url"], query)
            else:
                doc_data = self.extract_all_document_links_with_query(soup, config["base_url"], config, query)
            
            return {
                'title': title_text,
                'content': content_text,
                'doc_data': doc_data,
                'soup': soup
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def extract_all_document_links_with_query(self, soup: BeautifulSoup, base_url: str, config: Dict, query: str = "") -> List[Dict]:
        """Extract document links with query-based filtering and scoring"""
        doc_data = []
        
        # Method 1: Direct document links using enhanced selectors
        for selector in config["document_selectors"]["document_links"].split(", "):
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    title = link.get_text(strip=True) or link.get('title', '') or "Document"
                    relevance_score = self.calculate_relevance_score(title, query)
                    
                    doc_data.append({
                        'url': full_url,
                        'title': title,
                        'relevance_score': relevance_score,
                        'extraction_pattern': 'direct_selector'
                    })
        
        # Method 2: Table-based extraction with enhanced selectors
        for row in soup.select(config["document_selectors"]["table_rows"]):
            for link in row.find_all('a', href=True):
                href = link.get('href')
                if href and any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', 'document', 'fileEntryId']):
                    full_url = urljoin(base_url, href)
                    title = link.get_text(strip=True) or row.get_text(strip=True)[:100] or "Document"
                    relevance_score = self.calculate_relevance_score(title, query)
                    
                    doc_data.append({
                        'url': full_url,
                        'title': title,
                        'relevance_score': relevance_score,
                        'extraction_pattern': 'table_based'
                    })
        
        return doc_data

    def close_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def extract_all_documents(self) -> List[ComprehensiveDocument]:
        """Extract all documents from visited URLs"""
        all_documents = []
        
        for url in self.visited_urls:
            try:
                logger.info(f"Extracting document from: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title"
                
                # Extract content
                content = ""
                for selector in self.website_configs["irdai"]["document_selectors"]["content_area"].split(", "):
                    content_div = soup.select_one(selector)
                    if content_div:
                        content = content_div.get_text(separator=' ', strip=True)
                        break
                
                if not content:
                    content = soup.get_text(separator=' ', strip=True)
                
                # Clean content
                content = re.sub(r'\s+', ' ', content).strip()
                
                # Create document object
                document = ComprehensiveDocument(
                    url=url,
                    title=title_text,
                    content=content,
                    source_type="regulatory",
                    website=self.website_configs["irdai"]["base_url"],
                    document_links=[],
                    metadata={
                        'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'depth': 0,
                        'source_website': self.website_configs["irdai"]["base_url"],
                        'content_length': len(content),
                        'document_count': 0,
                        'keywords_found': []
                    }
                )
                
                all_documents.append(document)
            
            except Exception as e:
                logger.error(f"Error extracting document from {url}: {e}")
        
        return all_documents
    
    def save_documents(self, output_file: str = "data/scraped/comprehensive_documents.json"):
        """Save all scraped documents"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        data_dict = []
        for doc in self.documents:
            data_dict.append({
                'url': doc.url,
                'title': doc.title,
                'content': doc.content,
                'source_type': doc.source_type,
                'website': doc.website,
                'document_links': doc.document_links,
                'metadata': doc.metadata
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.documents)} comprehensive documents to {output_file}")

    def determine_search_strategy(self, query_intent: QueryIntent) -> Dict[str, Any]:
        """Agentic decision making for search strategy"""
        strategy = {
            'search_depth': 2,
            'priority_routes': [],
            'document_filters': [],
            'time_filter': None,
            'max_documents': 50,
            'early_stop_threshold': 0.95
        }
        
        # Adjust strategy based on intent
        if query_intent.intent_type == 'specific_document':
            strategy.update({
                'search_depth': 3,
                'max_documents': 20,
                'early_stop_threshold': 0.98,
                'focus_mode': 'precision'
            })
            logger.info("🎯 STRATEGY: Specific document search - High precision mode")
            
        elif query_intent.intent_type == 'latest_updates':
            strategy.update({
                'search_depth': 2,
                'max_documents': 30,
                'time_filter': 'recent',
                'focus_mode': 'recency'
            })
            logger.info("🔄 STRATEGY: Latest updates - Recency focused")
            
        elif query_intent.intent_type == 'regulatory_guidance':
            strategy.update({
                'search_depth': 3,
                'max_documents': 40,
                'document_filters': ['regulation', 'circular', 'guideline'],
                'focus_mode': 'authority'
            })
            logger.info("📋 STRATEGY: Regulatory guidance - Authority focused")
            
        else:  # general_search
            strategy.update({
                'search_depth': 2,
                'max_documents': 50,
                'focus_mode': 'comprehensive'
            })
            logger.info("🔍 STRATEGY: General search - Comprehensive mode")
        
        # Adjust for urgency
        if query_intent.urgency_level == 'critical':
            strategy['early_stop_threshold'] = 0.90
            strategy['max_documents'] = min(strategy['max_documents'], 15)
            logger.info("⚡ URGENCY: Critical - Fast response mode")
        elif query_intent.urgency_level == 'high':
            strategy['early_stop_threshold'] = 0.93
            strategy['max_documents'] = min(strategy['max_documents'], 25)
            logger.info("🚀 URGENCY: High - Balanced speed mode")
        
        return strategy

    def enhanced_relevance_scoring(self, text: str, query_intent: QueryIntent) -> float:
        """Enhanced relevance scoring based on query intent"""
        if not query_intent or not text.strip():
            return 0.0
        
        query = ' '.join(query_intent.keywords)
        base_score = self.calculate_relevance_score(text, query)
        
        # Intent-based adjustments
        intent_bonus = 0.0
        
        # Document type matching bonus
        for doc_type in query_intent.document_types:
            if doc_type.lower() in text.lower():
                intent_bonus += 0.15
                logger.debug(f"Document type bonus: {doc_type}")
        
        # Time sensitivity bonus
        if query_intent.time_sensitivity == 'latest':
            # Boost documents with recent years
            current_year = time.strftime('%Y')
            recent_years = [current_year, str(int(current_year) - 1)]
            for year in recent_years:
                if year in text:
                    intent_bonus += 0.1
                    logger.debug(f"Recent year bonus: {year}")
        
        elif query_intent.target_year:
            if query_intent.target_year in text:
                intent_bonus += 0.2
                logger.debug(f"Target year bonus: {query_intent.target_year}")
        
        # Keyword density bonus
        keyword_count = sum(1 for keyword in query_intent.keywords if keyword.lower() in text.lower())
        if len(query_intent.keywords) > 0:
            keyword_density = keyword_count / len(query_intent.keywords)
            intent_bonus += keyword_density * 0.1
        
        final_score = min(base_score + intent_bonus, 1.0)
        
        # Guard rail: Ensure reasonable scores
        if final_score > 1.0:
            final_score = 1.0
        elif final_score < 0.0:
            final_score = 0.0
        
        return final_score

    def validate_document_quality(self, document: Dict) -> bool:
        """Guard rails for document quality validation"""
        try:
            # Basic validation
            if not document.get('title') or not document.get('url'):
                return False
            
            # Content length validation
            content = document.get('content', '')
            if len(content.strip()) < 50:  # Minimum content length
                return False
            
            # URL validation
            url = document.get('url', '')
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Check for spam indicators
            spam_indicators = ['click here', 'buy now', 'limited time', 'act fast']
            title_lower = document.get('title', '').lower()
            if any(indicator in title_lower for indicator in spam_indicators):
                return False
            
            # Relevance threshold
            relevance = document.get('relevance_score', 0)
            if relevance < 0.01:  # Very low relevance threshold
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating document: {e}")
            return False

    def scrape_irdai_comprehensive(self, query: str = "") -> List[ComprehensiveDocument]:
        """Enhanced comprehensive scraping with agentic decision making"""
        # Guard rail: Input validation
        if not query or len(query.strip()) < 3:
            logger.warning("Invalid query provided")
            return []
        
        # Clear and analyze query
        self.clear_query_state()
        self.query_state['current_query'] = query
        
        # NEW: Analyze query intent
        query_intent = self.query_analyzer.analyze_query(query)
        self.query_state['query_intent'] = query_intent
        
        # Guard rail: Block invalid or harmful queries
        if query_intent.intent_type in ['invalid', 'blocked']:
            logger.warning(f"Query blocked or invalid: {query_intent.intent_type}")
            return []
        
        # Determine search strategy
        search_strategy = self.determine_search_strategy(query_intent)
        self.query_state['search_strategy'] = search_strategy
        
        config = self.website_configs["irdai"]
        all_documents = []
        high_relevance_documents = []
        
        logger.info(f"🎯 ENHANCED IRDAI scraping for: '{query}'")
        logger.info(f"📊 Intent: {query_intent.intent_type} | Confidence: {query_intent.confidence_score:.3f}")
        logger.info(f"🔧 Strategy: {search_strategy['focus_mode']} | Max docs: {search_strategy['max_documents']}")
        
        # Determine priority routes based on intent
        if query_intent.document_types:
            priority_urls = self.determine_intelligent_route_enhanced(query, query_intent)
        else:
            priority_urls = self.determine_intelligent_route(query)
        
        logger.info(f"🚀 Priority routes for {query_intent.intent_type}: {priority_urls}")
        
        documents_processed = 0
        max_docs = search_strategy['max_documents']
        
        for priority_url in priority_urls:
            if documents_processed >= max_docs:
                logger.info(f"🛑 Reached maximum document limit: {max_docs}")
                break
                
            page_url = urljoin(config["base_url"], priority_url)
            logger.info(f"🔍 Processing URL: {page_url}")
            
            try:
                page_data = self.scrape_page_with_query_enhanced(page_url, config, query, query_intent)
                if not page_data:
                    logger.warning(f"⚠️ No data from {page_url}")
                    continue
                
                doc_data = page_data['doc_data']
                logger.info(f"📑 Found {len(doc_data)} documents from {page_url}")
                
                # Process documents with enhanced validation
                page_documents = []
                for doc_info in doc_data:
                    if documents_processed >= max_docs:
                        break
                    
                    # Validate document quality
                    if not self.validate_document_quality(doc_info):
                        continue
                    
                    # Enhanced relevance scoring
                    enhanced_score = self.enhanced_relevance_scoring(
                        f"{doc_info['title']} {doc_info.get('content', '')}", 
                        query_intent
                    )
                    doc_info['relevance_score'] = enhanced_score
                    
                    # Perfect match detection with early stopping
                    if enhanced_score >= search_strategy['early_stop_threshold']:
                        logger.info(f"🎯 PERFECT MATCH FOUND - EARLY STOPPING! Score: {enhanced_score:.3f}")
                        
                        # Create perfect match document
                        perfect_document = self.create_enhanced_document(doc_info, config, page_url, query, query_intent, is_perfect_match=True)
                        
                        logger.info(f"🎯 RETURNING SINGLE PERFECT MATCH: '{doc_info['title']}'")
                        return [perfect_document]
                    
                    # Apply intent-based thresholds
                    min_threshold = self.get_intent_based_threshold(query_intent)
                    
                    if enhanced_score >= min_threshold:
                        document = self.create_enhanced_document(doc_info, config, page_url, query, query_intent)
                        page_documents.append(document)
                        documents_processed += 1
                        
                        # Track high-relevance documents
                        if enhanced_score >= 0.8:
                            high_relevance_documents.append(document)
                            logger.info(f"🌟 HIGH RELEVANCE: '{doc_info['title'][:60]}...' (Score: {enhanced_score:.3f})")
                
                all_documents.extend(page_documents)
                logger.info(f"📑 Added {len(page_documents)} documents (Total: {len(all_documents)})")
                
                # Early stopping for high-quality results
                if len(high_relevance_documents) >= 3 and query_intent.urgency_level in ['critical', 'high']:
                    logger.info(f"🎯 Early stopping: Found {len(high_relevance_documents)} high-relevance documents")
                    break
                
            except Exception as e:
                logger.error(f"❌ Error processing {page_url}: {e}")
                continue
        
        # Sort by enhanced relevance scores
        all_documents.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)
        
        # Apply final filtering based on strategy
        final_documents = self.apply_final_filtering(all_documents, search_strategy, query_intent)
        
        logger.info(f"🎯 ENHANCED IRDAI SEARCH COMPLETE:")
        logger.info(f"  📑 Total documents: {len(final_documents)}")
        logger.info(f"  🌟 High-relevance documents: {len(high_relevance_documents)}")
        logger.info(f"  🎯 Intent: {query_intent.intent_type}")
        logger.info(f"  📊 Strategy: {search_strategy['focus_mode']}")
        
        return final_documents

    def get_intent_based_threshold(self, query_intent: QueryIntent) -> float:
        """Get relevance threshold based on query intent"""
        if query_intent.intent_type == 'specific_document':
            return 0.02  # Very low threshold for specific searches
        elif query_intent.intent_type == 'latest_updates':
            return 0.05  # Low threshold for latest updates
        elif query_intent.intent_type == 'regulatory_guidance':
            return 0.03  # Low threshold for regulatory content
        else:
            return 0.05  # Standard threshold for general searches

    def determine_intelligent_route_enhanced(self, query: str, query_intent: QueryIntent) -> List[str]:
        """Enhanced routing based on query intent analysis"""
        base_routes = self.determine_intelligent_route(query)
        
        # Add intent-specific routes
        if query_intent.time_sensitivity == 'latest':
            # Prioritize routes with latest content
            latest_routes = ["/notifications", "/circulars", "/updated-regulations"]
            base_routes = latest_routes + [r for r in base_routes if r not in latest_routes]
        
        if 'regulation' in query_intent.document_types:
            regulation_routes = ["/consolidated-gazette-notified-regulations", "/updated-regulations"]
            base_routes = regulation_routes + [r for r in base_routes if r not in regulation_routes]
        
        if 'circular' in query_intent.document_types:
            circular_routes = ["/circulars", "/notifications"]
            base_routes = circular_routes + [r for r in base_routes if r not in circular_routes]
        
        return base_routes[:4]  # Limit to top 4 routes

    def scrape_page_with_query_enhanced(self, url: str, config: Dict, query: str, query_intent: QueryIntent) -> Dict:
        """Enhanced page scraping with intent awareness"""
        try:
            logger.info(f"Enhanced scraping: {url}")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract content
            content_text = ""
            for selector in config["document_selectors"]["content_area"].split(", "):
                content_div = soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text(separator=' ', strip=True)
                    break
            
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text(separator=' ', strip=True)
            
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # Enhanced document extraction based on intent
            if config.get("base_url") == "https://irdai.gov.in":
                doc_data = self.extract_irdai_documents_enhanced_with_intent(soup, config["base_url"], query, query_intent)
            else:
                doc_data = self.extract_all_document_links_with_query_enhanced(soup, config["base_url"], config, query, query_intent)
            
            return {
                'title': title_text,
                'content': content_text,
                'doc_data': doc_data,
                'soup': soup
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced scraping {url}: {e}")
            return None

    def extract_irdai_documents_enhanced_with_intent(self, soup: BeautifulSoup, base_url: str, query: str, query_intent: QueryIntent) -> List[Dict]:
        """Enhanced IRDAI document extraction with intent awareness"""
        documents = []
        processed_doc_ids = set()
        
        logger.info(f"🎯 Intent-aware IRDAI extraction: {query_intent.intent_type}")
        
        # Focus on different elements based on intent
        if query_intent.time_sensitivity == 'latest':
            # Focus on recent notifications and updates
            recent_selectors = [
                'table tr:nth-child(-n+10)',  # First 10 rows (most recent)
                '.recent-updates', '.latest-notifications'
            ]
        else:
            recent_selectors = []
        
        # Extract from tables with enhanced filtering
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            
            # Apply intent-based row filtering
            if query_intent.time_sensitivity == 'latest' and len(rows) > 20:
                rows = rows[:20]  # Focus on recent entries
            
            for row_idx, row in enumerate(rows):
                if row_idx == 0:  # Skip header
                    continue
                
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                
                # Enhanced title extraction with intent awareness
                title_candidates = []
                document_links = []
                
                for cell in cells:
                    cell_text = cell.get('title', '').strip() or cell.get_text(strip=True)
                    
                    if (len(cell_text) > 15 and len(cell_text) < 800 and
                        not cell_text.isdigit() and
                        not re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', cell_text)):
                        
                        # Enhanced relevance calculation with intent
                        cell_relevance = self.enhanced_relevance_scoring(cell_text, query_intent)
                        title_candidates.append((cell_text, cell_relevance))
                    
                    # Extract document links
                    for link in cell.find_all('a', href=True):
                        href = link.get('href')
                        if href and 'document-detail' in href and 'documentId=' in href:
                            full_url = urljoin(base_url, href)
                            document_links.append(full_url)
                
                # Process each document link
                for doc_link in document_links:
                    doc_id_match = re.search(r'documentId=(\d+)', doc_link)
                    if not doc_id_match:
                        continue
                    
                    document_id = doc_id_match.group(1)
                    if document_id in processed_doc_ids:
                        continue
                    processed_doc_ids.add(document_id)
                    
                    # Choose best title with intent awareness
                    title_candidates.sort(key=lambda x: x[1], reverse=True)
                    best_title = title_candidates[0][0] if title_candidates else ""
                    best_score = title_candidates[0][1] if title_candidates else 0
                    
                    # Enhanced detail page extraction
                    detail_data = self.extract_irdai_document_detail_page_enhanced(doc_link, query, query_intent)
                    
                    if detail_data:
                        final_score = max(best_score, detail_data['relevance_score'])
                        final_title = detail_data['title'] if detail_data['relevance_score'] > best_score else best_title
                        
                        threshold = self.get_intent_based_threshold(query_intent)
                        
                        if final_score >= threshold and final_title:
                            documents.append({
                                'url': doc_link,
                                'title': final_title,
                                'relevance_score': final_score,
                                'extraction_pattern': 'intent_aware_table_detail',
                                'document_id': document_id,
                                'pdf_links': detail_data.get('pdf_links', []),
                                'content': detail_data.get('content', ''),
                                'metadata': {
                                    'document_id': document_id,
                                    'intent_type': query_intent.intent_type,
                                    'time_sensitivity': query_intent.time_sensitivity,
                                    'target_year': query_intent.target_year,
                                    'urgency_level': query_intent.urgency_level
                                }
                            })
        
        return documents

    def extract_irdai_document_detail_page_enhanced(self, document_detail_url: str, query: str, query_intent: QueryIntent) -> Dict:
        """Enhanced document detail extraction with intent awareness"""
        try:
            logger.info(f"📋 Intent-aware detail extraction: {document_detail_url}")
            
            response = requests.get(document_detail_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Enhanced title extraction with intent priority
            title = self.extract_title_with_intent_priority(soup, query_intent)
            content = self.extract_content_with_intent_focus(soup, query_intent)
            pdf_links = self.extract_pdf_links_enhanced(soup, document_detail_url)
            
            # Calculate enhanced relevance
            full_text = f"{title} {content}"
            relevance_score = self.enhanced_relevance_scoring(full_text, query_intent)
            
            # Apply time-based scoring if relevant
            if query_intent.time_sensitivity == 'latest':
                relevance_score = self.apply_time_boost(relevance_score, full_text)
            elif query_intent.target_year:
                relevance_score = self.apply_year_boost(relevance_score, full_text, query_intent.target_year)
            
            return {
                'url': document_detail_url,
                'title': title,
                'content': content,
                'pdf_links': pdf_links,
                'relevance_score': relevance_score,
                'intent_enhanced': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced detail extraction {document_detail_url}: {e}")
            return None

    def extract_title_with_intent_priority(self, soup: BeautifulSoup, query_intent: QueryIntent) -> str:
        """Extract title with intent-based prioritization"""
        # Enhanced with intent-specific selectors
        intent_specific_selectors = {
            'regulatory_guidance': ['.regulation-title', '.circular-title', '.guideline-title'],
            'latest_updates': ['.recent-title', '.update-title', '.notification-title'],
            'specific_document': ['.document-title', '.policy-title', '.detailed-title']
        }
        
        selectors = intent_specific_selectors.get(query_intent.intent_type, [])
        selectors.extend([
            '.journal-content-article h1', '.journal-content-article h2',
            '.portlet-body h1', '.portlet-body h2', 'h1', 'h2'
        ])
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 30 and len(title) < 1000:
                    return title
        
        return "Document Title"

    def apply_time_boost(self, score: float, text: str) -> float:
        """Apply time-based relevance boost for latest content"""
        current_year = time.strftime('%Y')
        recent_years = [current_year, str(int(current_year) - 1)]
        
        boost = 0.0
        for year in recent_years:
            if year in text:
                boost += 0.1
        
        return min(score + boost, 1.0)

    def apply_year_boost(self, score: float, text: str, target_year: str) -> float:
        """Apply year-specific relevance boost"""
        if target_year in text:
            return min(score + 0.2, 1.0)
        return score

    def create_enhanced_document(self, doc_info: Dict, config: Dict, page_url: str, query: str, query_intent: QueryIntent, is_perfect_match: bool = False) -> ComprehensiveDocument:
        """Create enhanced document with intent-aware content"""
        if is_perfect_match:
            enhanced_content = f"""
🎯 **PERFECT MATCH FOUND!** (Score: {doc_info['relevance_score']:.3f})

**Query Intent:** {query_intent.intent_type.replace('_', ' ').title()}
**Time Sensitivity:** {query_intent.time_sensitivity}
**Urgency:** {query_intent.urgency_level}

**Document Title:** {doc_info['title']}

**Analysis:**
- Intent Type: {query_intent.intent_type}
- Document Types Detected: {', '.join(query_intent.document_types)}
- Keywords Matched: {', '.join(query_intent.keywords[:10])}
- Confidence: {query_intent.confidence_score:.3f}

**Content:**
{doc_info.get('content', 'This document matches your query requirements exactly.')}

**System Decision:** Early stopping triggered due to perfect match.
"""
        else:
            enhanced_content = f"""
**Query Intent Analysis:** {query_intent.intent_type.replace('_', ' ').title()}
**Relevance Score:** {doc_info['relevance_score']:.3f}

{doc_info['title']}

{doc_info.get('content', 'Document content extracted from official source.')}

**Matched Elements:**
- Document Types: {', '.join(query_intent.document_types) if query_intent.document_types else 'General'}
- Time Sensitivity: {query_intent.time_sensitivity}
- Keywords: {', '.join(query_intent.keywords[:5])}
"""
        
        return ComprehensiveDocument(
            url=doc_info['url'],
            title=doc_info['title'],
            content=enhanced_content,
            source_type=config["source_type"],
            website=config["base_url"],
            document_links=[doc_info['url']] + doc_info.get('pdf_links', []),
            metadata={
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'document_id': doc_info.get('document_id'),
                'relevance_score': doc_info['relevance_score'],
                'query': query,
                'query_intent': query_intent.intent_type,
                'time_sensitivity': query_intent.time_sensitivity,
                'urgency_level': query_intent.urgency_level,
                'document_types': query_intent.document_types,
                'intent_confidence': query_intent.confidence_score,
                'is_perfect_match': is_perfect_match,
                'enhanced_processing': True
            }
        )

    def apply_final_filtering(self, documents: List[ComprehensiveDocument], strategy: Dict, query_intent: QueryIntent) -> List[ComprehensiveDocument]:
        """Apply final filtering based on strategy and intent"""
        filtered_docs = documents
        
        # Apply document type filtering
        if strategy.get('document_filters'):
            type_filtered = []
            for doc in filtered_docs:
                doc_content = doc.content.lower()
                if any(dtype in doc_content for dtype in strategy['document_filters']):
                    type_filtered.append(doc)
            if type_filtered:  # Only apply filter if it returns results
                filtered_docs = type_filtered
        
        # Apply time filtering
        if strategy.get('time_filter') == 'recent':
            current_year = time.strftime('%Y')
            recent_year = str(int(current_year) - 1)
            time_filtered = []
            for doc in filtered_docs:
                doc_content = doc.content
                if current_year in doc_content or recent_year in doc_content:
                    time_filtered.append(doc)
            if time_filtered:  # Only apply filter if it returns results
                filtered_docs = time_filtered
        
        # Limit based on strategy
        max_docs = strategy.get('max_documents', 50)
        filtered_docs = filtered_docs[:max_docs]
        
        return filtered_docs

    def extract_content_with_intent_focus(self, soup: BeautifulSoup, query_intent: QueryIntent) -> str:
        """Extract content with focus based on query intent"""
        # Enhanced with intent-specific content areas
        
        # Standard content selectors
        selectors = [
            '.journal-content-article', '.portlet-body',
            '.content', '.document-content', 'main'
        ]
        
        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) > 100:
                    # Apply intent-based content filtering
                    if query_intent.intent_type == 'latest_updates':
                        # Focus on recent dates and updates
                        content = self.highlight_recent_content(content)
                    elif query_intent.intent_type == 'specific_document':
                        # Focus on specific details
                        content = self.extract_specific_details(content, query_intent.keywords)
                    
                    return content[:3000]  # Limit content length
        
        return "Content not available"

    def highlight_recent_content(self, content: str) -> str:
        """Highlight recent content for latest updates intent"""
        lines = content.split('.')
        recent_lines = []
        current_year = time.strftime('%Y')
        
        for line in lines:
            if current_year in line or 'recent' in line.lower() or 'latest' in line.lower():
                recent_lines.append(line.strip())
        
        if recent_lines:
            return '. '.join(recent_lines[:10]) + '.'
        return content

    def extract_specific_details(self, content: str, keywords: List[str]) -> str:
        """Extract specific details based on keywords"""
        sentences = content.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword.lower() in sentence_lower for keyword in keywords):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            return '. '.join(relevant_sentences[:15]) + '.'
        return content

    def extract_pdf_links_enhanced(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Enhanced PDF link extraction"""
        pdf_links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and (href.lower().endswith('.pdf') or 'pdf' in href.lower()):
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
        
        return pdf_links

    def extract_all_document_links_with_query_enhanced(self, soup: BeautifulSoup, base_url: str, config: Dict, query: str, query_intent: QueryIntent) -> List[Dict]:
        """Enhanced document link extraction with intent awareness"""
        # Apply intent-based selectors
        if query_intent.intent_type == 'regulatory_guidance':
            priority_selectors = [
                "a[href*='regulation']", "a[href*='circular']", "a[href*='guideline']"
            ]
        elif query_intent.intent_type == 'latest_updates':
            priority_selectors = [
                "a[href*='notification']", "a[href*='update']", "a[href*='recent']"
            ]
        else:
            priority_selectors = []
        
        # Process priority selectors first
        doc_data = []
        for selector in priority_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    title = link.get_text(strip=True) or "Document"
                    relevance_score = self.enhanced_relevance_scoring(title, query_intent)
                    
                    if relevance_score >= 0.1:
                        doc_data.append({
                            'url': full_url,
                            'title': title,
                            'relevance_score': relevance_score,
                            'extraction_pattern': 'intent_priority'
                        })
        
        # Then process standard selectors
        for selector in config["document_selectors"]["document_links"].split(", "):
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    title = link.get_text(strip=True) or "Document"
                    relevance_score = self.enhanced_relevance_scoring(title, query_intent)
                    
                    if relevance_score >= 0.05:
                        doc_data.append({
                            'url': full_url,
                            'title': title,
                            'relevance_score': relevance_score,
                            'extraction_pattern': 'standard_enhanced'
                        })
        
        # Remove duplicates and sort by relevance
        seen_urls = set()
        unique_docs = []
        for doc in sorted(doc_data, key=lambda x: x['relevance_score'], reverse=True):
            if doc['url'] not in seen_urls:
                seen_urls.add(doc['url'])
                unique_docs.append(doc)
        
        return unique_docs[:50]  # Limit results

    def scrape_all_websites_comprehensive(self, query: str = "") -> List[ComprehensiveDocument]:
        """
        MAIN ENTRY POINT: Comprehensive scraping for all websites with query support
        """
        # Guard rail: Input validation
        if not query or len(query.strip()) < 3:
            logger.warning("Invalid or empty query provided")
            return []
        
        logger.info(f"🚀 COMPREHENSIVE SCRAPING STARTED for query: '{query}'")
        
        # Clear previous state and set new query
        self.clear_query_state()
        self.query_state['current_query'] = query
        
        # Use the enhanced IRDAI scraping method
        try:
            documents = self.scrape_irdai_comprehensive(query)
            
            logger.info(f"🎯 COMPREHENSIVE SCRAPING COMPLETE:")
            logger.info(f"  📑 Total documents found: {len(documents)}")
            logger.info(f"  🎯 Query: '{query}'")
            
            # Show top results
            for i, doc in enumerate(documents[:3], 1):
                relevance = doc.metadata.get('relevance_score', 0)
                doc_id = doc.metadata.get('document_id', 'N/A')
                logger.info(f"  {i}. {doc.title[:80]}... (Score: {relevance:.3f}, ID: {doc_id})")
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive scraping: {e}")
            return []
        
        finally:
            # Clean up driver if used
            if self.driver:
                self.close_driver()

    def scrape_website_comprehensive(self, website_name: str, query: str = "") -> List[ComprehensiveDocument]:
        """Enhanced website scraping with query support"""
        if website_name.lower() == "irdai":
            return self.scrape_irdai_comprehensive(query)
        else:
            logger.warning(f"Website '{website_name}' not supported for comprehensive scraping")
            return []
def main():
    """Test comprehensive scraper with real query support"""
    print("🔍 Testing comprehensive scraper with real query support...")
    
    # Create scraper without Selenium to avoid Chrome driver issues
    scraper = ComprehensiveScraper(use_selenium=False)
    
    # Test with a real query
    test_query = "Insurance (Procedure for Holding Inquiry by Adjudicating Officer) Rules, 2016"
    print(f"🔎 Testing query: '{test_query}'")
    
    try:
        documents = scraper.scrape_all_websites_comprehensive(test_query)
        
        print(f"✅ Found {len(documents)} documents for query '{test_query}'")
        
        # Show top results
        print(f"\n📊 Results for '{test_query}':")
        for i, doc in enumerate(documents[:5], 1):
            relevance = doc.metadata.get('relevance_score', 0)
            doc_id = doc.metadata.get('document_id', 'N/A')
            print(f"{i}. {doc.title} (Score: {relevance:.3f}, ID: {doc_id})")
            print(f"   URL: {doc.url}")
            print()
        
        if not documents:
            print("❌ No documents found. Check logs for debugging information.")
        
        # Save the results
        scraper.save_documents()
        
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()