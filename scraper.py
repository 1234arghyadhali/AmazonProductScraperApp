import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from urllib.parse import urljoin, urlparse

class AmazonScraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Set up session with default headers
        self.setup_session()
    
    def setup_session(self):
        """Configure session with anti-bot headers"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'DNT': '1',
        }
        self.session.headers.update(headers)
    
    def get_random_user_agent(self):
        """Get a random user agent from the list"""
        return random.choice(self.user_agents)
    
    def make_request(self, url, retries=3):
        """Make a request with enhanced anti-bot protection"""
        for attempt in range(retries):
            try:
                # Rotate user agent and update additional headers
                user_agent = self.get_random_user_agent()
                self.session.headers.update({
                    'User-Agent': user_agent,
                    'Referer': 'https://www.amazon.in/',
                    'Origin': 'https://www.amazon.in'
                })
                
                # Add random delay between requests
                time.sleep(random.uniform(2, 5))
                
                # Make request with longer timeout
                response = self.session.get(url, timeout=20, allow_redirects=True)
                
                if response.status_code == 200:
                    # Check for common blocking indicators
                    response_text = response.text.lower()
                    blocking_indicators = [
                        'robot check', 'captcha', 'blocked', 'access denied',
                        'sorry, we just need to make sure you\'re not a robot',
                        'enter the characters you see below'
                    ]
                    
                    if any(indicator in response_text for indicator in blocking_indicators):
                        logging.warning(f"Detected blocking content on attempt {attempt + 1}")
                        if attempt < retries - 1:
                            time.sleep(random.uniform(5, 10))
                            continue
                        else:
                            return None
                    
                    return response
                elif response.status_code == 503:
                    logging.warning(f"Service unavailable (503) for {url}, attempt {attempt + 1}")
                    time.sleep(random.uniform(5, 10))
                elif response.status_code == 429:
                    logging.warning(f"Rate limited (429) for {url}, attempt {attempt + 1}")
                    time.sleep(random.uniform(10, 20))
                else:
                    logging.warning(f"Unexpected status code {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                logging.error(f"Request failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(3, 8))
        
        return None
    
    def parse_product_data(self, soup):
        """Parse product data from Amazon page"""
        products = []
        
        # Multiple selectors to try for different Amazon page layouts
        product_selectors = [
            # Search results page - most common
            '[data-component-type="s-search-result"]',
            # Alternative search result selectors
            '.s-result-item[data-asin]',
            '.s-widget-container[data-asin]',
            # Category pages
            '.s-result-item',
            # Product grid variations
            '.sg-col-inner .s-widget-container',
            # Fallback selectors
            '[data-asin]:not([data-asin=""])',
            '.s-item-container',
            '.celwidget[data-asin]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                # Filter out elements without meaningful content
                valid_elements = [e for e in elements if len(e.get_text(strip=True)) > 20]
                if valid_elements:
                    product_elements = valid_elements
                    logging.info(f"Found {len(valid_elements)} products using selector: {selector}")
                    break
        
        if not product_elements:
            logging.warning("No product elements found with any selector")
            # Try to log what we found for debugging
            all_data_asin = soup.select('[data-asin]')
            logging.info(f"Found {len(all_data_asin)} elements with data-asin attribute")
            return products
        
        for element in product_elements:
            try:
                product_data = self.extract_product_info(element)
                if product_data and product_data['name'] and product_data['price']:
                    products.append(product_data)
            except Exception as e:
                logging.debug(f"Error parsing product element: {str(e)}")
                continue
        
        return products
    
    def extract_product_info(self, element):
        """Extract name and price from a product element"""
        product = {'name': '', 'price': ''}
        
        # Try multiple selectors for product name - expanded list
        name_selectors = [
            'h2 a span',
            'h2 span',
            'h3 a span',
            'h3 span',
            '.s-size-mini .s-link-style a span',
            '[data-cy="title-recipe-title"]',
            '.a-size-base-plus',
            '.a-size-base',
            '.a-size-medium',
            '.a-size-small',
            'a .a-text-normal',
            '.a-link-normal span',
            '.s-link-style a span',
            '.a-color-base',
            '[data-asin] h2 span',
            '[data-asin] h3 span'
        ]
        
        for selector in name_selectors:
            name_element = element.select_one(selector)
            if name_element and name_element.get_text(strip=True):
                name_text = name_element.get_text(strip=True)
                # Skip if it's just a number or very short text
                if len(name_text) > 5 and not name_text.isdigit():
                    product['name'] = name_text
                    break
        
        # Try multiple selectors for price - expanded and reordered
        price_selectors = [
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.a-price-symbol + .a-price-whole',
            '.a-price-range .a-price .a-offscreen',
            '.a-text-price .a-offscreen',
            '.a-color-price',
            '[data-a-color="price"] .a-offscreen',
            '.a-price .a-price-whole',
            '.a-text-price',
            '.a-price-symbol',
            '.sx-price .a-price .a-offscreen',
            '.a-price.a-text-price .a-offscreen'
        ]
        
        for selector in price_selectors:
            price_element = element.select_one(selector)
            if price_element and price_element.get_text(strip=True):
                price_text = price_element.get_text(strip=True).replace('\u00a0', ' ').strip()
                # Clean up price text and validate
                if ('₹' in price_text or 'Rs' in price_text.upper() or any(char.isdigit() for char in price_text)):
                    # Remove extra spaces and normalize
                    price_text = ' '.join(price_text.split())
                    if any(char.isdigit() for char in price_text):
                        # Replace problematic currency symbols with Rs
                        clean_price = price_text.replace('₹', 'Rs ').replace('â', 'Rs ')
                        product['price'] = clean_price if 'Rs' in clean_price else f"Rs {price_text}"
                        break
        
        # Fallback: look for any numeric content that might be price
        if not product['price']:
            all_text = element.get_text()
            import re
            # Look for Indian currency patterns
            price_patterns = [
                r'₹\s*[\d,]+(?:\.\d{2})?',
                r'Rs\.?\s*[\d,]+(?:\.\d{2})?',
                r'INR\s*[\d,]+(?:\.\d{2})?'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, all_text)
                if match:
                    price_text = match.group().strip()
                    # Replace problematic currency symbols with Rs
                    clean_price = price_text.replace('₹', 'Rs ').replace('â', 'Rs ')
                    product['price'] = clean_price
                    break
        
        return product
    
    def scrape_products(self, url):
        """Main scraping function"""
        logging.info(f"Starting to scrape: {url}")
        
        # Validate URL
        parsed_url = urlparse(url)
        if 'amazon.in' not in parsed_url.netloc.lower():
            raise ValueError("URL must be from amazon.in")
        
        # First, visit the main Amazon page to establish session
        try:
            logging.info("Establishing session with Amazon.in")
            main_response = self.session.get('https://www.amazon.in/', timeout=15)
            time.sleep(random.uniform(1, 2))
        except:
            logging.warning("Could not establish initial session")
        
        response = self.make_request(url)
        if not response:
            raise Exception("Failed to fetch the page after multiple attempts")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse products
        products = self.parse_product_data(soup)
        
        logging.info(f"Successfully scraped {len(products)} products")
        
        # Filter out products with missing data
        valid_products = [p for p in products if p['name'] and p['price']]
        
        logging.info(f"Found {len(valid_products)} valid products with both name and price")
        
        return valid_products
