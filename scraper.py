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
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # Set up session with default headers
        self.setup_session()
    
    def setup_session(self):
        """Configure session with anti-bot headers"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
    
    def get_random_user_agent(self):
        """Get a random user agent from the list"""
        return random.choice(self.user_agents)
    
    def make_request(self, url, retries=3):
        """Make a request with anti-bot protection"""
        for attempt in range(retries):
            try:
                # Rotate user agent
                self.session.headers.update({'User-Agent': self.get_random_user_agent()})
                
                # Add random delay
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 503:
                    logging.warning(f"Service unavailable (503) for {url}, attempt {attempt + 1}")
                    time.sleep(random.uniform(3, 6))
                else:
                    logging.warning(f"Unexpected status code {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                logging.error(f"Request failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(2, 5))
        
        return None
    
    def parse_product_data(self, soup):
        """Parse product data from Amazon page"""
        products = []
        
        # Multiple selectors to try for different Amazon page layouts
        product_selectors = [
            # Search results page
            '[data-component-type="s-search-result"]',
            # Category pages
            '.s-result-item',
            # Product grid
            '.sg-col-inner .s-widget-container',
            # Alternative selectors
            '[data-asin]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                logging.info(f"Found {len(elements)} products using selector: {selector}")
                break
        
        if not product_elements:
            logging.warning("No product elements found with any selector")
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
        
        # Try multiple selectors for product name
        name_selectors = [
            'h2 a span',
            'h2 span',
            '.s-size-mini .s-link-style a span',
            '[data-cy="title-recipe-title"]',
            '.a-size-base-plus',
            '.a-size-base',
            '.a-size-medium',
            'a .a-text-normal'
        ]
        
        for selector in name_selectors:
            name_element = element.select_one(selector)
            if name_element and name_element.get_text(strip=True):
                product['name'] = name_element.get_text(strip=True)
                break
        
        # Try multiple selectors for price
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '.a-price-symbol + .a-price-whole',
            '.a-price-range .a-price .a-offscreen',
            '.a-text-price .a-offscreen',
            '.a-color-price',
            '[data-a-color="price"] .a-offscreen'
        ]
        
        for selector in price_selectors:
            price_element = element.select_one(selector)
            if price_element and price_element.get_text(strip=True):
                price_text = price_element.get_text(strip=True)
                # Clean up price text
                if '₹' in price_text or 'Rs' in price_text.upper():
                    product['price'] = price_text
                    break
        
        # If no symbol found, try to find numeric price and add currency
        if not product['price']:
            for selector in price_selectors:
                price_element = element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    # Check if it looks like a price (contains digits and common price patterns)
                    if any(char.isdigit() for char in price_text) and (',' in price_text or len(price_text) >= 2):
                        product['price'] = f"₹{price_text}"
                        break
        
        return product
    
    def scrape_products(self, url):
        """Main scraping function"""
        logging.info(f"Starting to scrape: {url}")
        
        # Validate URL
        parsed_url = urlparse(url)
        if 'amazon.in' not in parsed_url.netloc.lower():
            raise ValueError("URL must be from amazon.in")
        
        response = self.make_request(url)
        if not response:
            raise Exception("Failed to fetch the page after multiple attempts")
        
        # Check if we got blocked
        if 'robot' in response.text.lower() or 'captcha' in response.text.lower():
            raise Exception("Request was blocked by Amazon's anti-bot protection")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse products
        products = self.parse_product_data(soup)
        
        logging.info(f"Successfully scraped {len(products)} products")
        
        # Filter out products with missing data
        valid_products = [p for p in products if p['name'] and p['price']]
        
        logging.info(f"Found {len(valid_products)} valid products with both name and price")
        
        return valid_products
