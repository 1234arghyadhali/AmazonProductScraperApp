import os
import logging
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from scraper import AmazonScraper
import tempfile
import csv

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_dev")

@app.route('/')
def index():
    """Main page with URL input form"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle URL submission and scraping"""
    url = request.form.get('url', '').strip()
    
    if not url:
        flash('Please enter a valid Amazon.in URL', 'error')
        return redirect(url_for('index'))
    
    # Validate that it's an Amazon.in URL
    if 'amazon.in' not in url.lower():
        flash('Please enter a valid Amazon.in URL', 'error')
        return redirect(url_for('index'))
    
    try:
        # Initialize scraper and get products
        scraper = AmazonScraper()
        products = scraper.scrape_products(url)
        
        if not products:
            flash('No products found. The page might be blocked or contain no products.', 'warning')
            return redirect(url_for('index'))
        
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='', encoding='utf-8')
        
        try:
            writer = csv.writer(temp_file)
            writer.writerow(['Product Name', 'Price'])  # Header
            
            for product in products:
                writer.writerow([product['name'], product['price']])
            
            temp_file.close()
            
            flash(f'Successfully scraped {len(products)} products!', 'success')
            
            # Send file for download
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name='amazon_products.csv',
                mimetype='text/csv'
            )
            
        except Exception as e:
            logging.error(f"Error creating CSV: {str(e)}")
            flash('Error creating CSV file', 'error')
            return redirect(url_for('index'))
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file.name)
            except:
                pass
    
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        flash('Error scraping the page. Please try again or check if the URL is accessible.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
