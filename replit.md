# Amazon.in Product Scraper

## Overview

This is a Flask-based web application that scrapes product information (names and prices) from Amazon.in product pages and exports the data as CSV files. The application provides a simple web interface where users can input Amazon.in URLs and receive downloadable CSV files containing the extracted product data.

## System Architecture

The application follows a traditional Flask web application architecture with a clear separation of concerns:

- **Frontend**: HTML templates with Bootstrap styling and custom CSS
- **Backend**: Flask web framework with Python
- **Web Scraping**: Custom scraper module using BeautifulSoup and requests
- **Data Processing**: CSV generation for data export
- **Deployment**: Gunicorn WSGI server with autoscale deployment

## Key Components

### Web Application (`app.py`)
- **Flask Routes**: Handles web requests and responses
  - `/` - Main page with URL input form
  - `/scrape` - POST endpoint for processing Amazon URLs
- **URL Validation**: Ensures only Amazon.in URLs are processed
- **CSV Generation**: Creates temporary CSV files for download
- **Flash Messages**: User feedback for success/error states

### Web Scraper (`scraper.py`)
- **Anti-Bot Protection**: Implements multiple strategies to avoid detection:
  - Rotating user agents from a predefined list
  - Random delays between requests
  - Anti-bot headers configuration
- **Session Management**: Maintains persistent HTTP sessions
- **Retry Logic**: Handles failed requests with retry mechanisms
- **Request Handling**: Robust HTTP request handling with error management

### Frontend Templates (`templates/index.html`)
- **Bootstrap Integration**: Uses Bootstrap dark theme for modern UI
- **Responsive Design**: Mobile-friendly interface
- **Icon Integration**: Feather icons for visual enhancement
- **Form Validation**: Client-side and server-side validation

### Styling (`static/style.css`)
- **Dark Theme**: Custom dark theme with gradient backgrounds
- **Glass Morphism**: Modern UI effects with backdrop filters
- **Interactive Elements**: Hover effects and transitions
- **Responsive Components**: Ensures proper display across devices

## Data Flow

1. **User Input**: User enters Amazon.in URL in the web form
2. **URL Validation**: Server validates the URL format and domain
3. **Scraping Process**: 
   - AmazonScraper initializes with anti-bot protection
   - Makes HTTP request to the provided URL
   - Parses HTML content using BeautifulSoup
   - Extracts product names and prices
4. **Data Processing**: Creates temporary CSV file with extracted data
5. **File Download**: Serves CSV file to user for download

## External Dependencies

### Core Dependencies
- **Flask 3.1.1**: Web framework for handling HTTP requests and rendering templates
- **BeautifulSoup4 4.13.4**: HTML parsing and web scraping
- **requests 2.32.4**: HTTP library for making web requests
- **Gunicorn 23.0.0**: WSGI HTTP server for production deployment

### Additional Dependencies
- **Flask-SQLAlchemy 3.1.1**: Database ORM (prepared for future database integration)
- **psycopg2-binary 2.9.10**: PostgreSQL adapter (prepared for future database integration)
- **email-validator 2.2.0**: Email validation utilities
- **trafilatura 2.0.0**: Text extraction from web pages

### Frontend Dependencies
- **Bootstrap**: CSS framework via CDN
- **Feather Icons**: Icon library via CDN

## Deployment Strategy

### Development Environment
- **Python 3.11**: Runtime environment
- **Debug Mode**: Enabled for development with auto-reload
- **Local Server**: Runs on `0.0.0.0:5000`

### Production Environment
- **Gunicorn**: WSGI server with the following configuration:
  - Bind to `0.0.0.0:5000`
  - Auto-reload enabled
  - Port reuse for better performance
- **Autoscale Deployment**: Configured for automatic scaling based on demand
- **Environment Variables**: Session secret key from environment variables

### Infrastructure
- **Nix Environment**: Uses stable-24_05 channel
- **System Packages**: OpenSSL and PostgreSQL prepared for future use
- **Container Ready**: Configured for containerized deployment

## Changelog

```
Changelog:
- June 19, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## Technical Notes

### Architecture Decisions

**Web Scraping Approach**: Chose BeautifulSoup over Selenium for lighter resource usage and faster scraping, with comprehensive anti-bot protection to handle Amazon's detection mechanisms.

**Flask Framework**: Selected for its simplicity and rapid development capabilities, suitable for this focused scraping application.

**CSV Export**: Implemented temporary file generation instead of database storage for immediate data delivery and reduced system complexity.

**Responsive Design**: Bootstrap framework chosen for quick, professional UI development with minimal custom CSS requirements.

**Session Management**: Implemented persistent HTTP sessions to maintain cookies and improve scraping reliability.

### Future Considerations

The application is prepared for database integration with SQLAlchemy and PostgreSQL dependencies already included, allowing for future features like user accounts, scraping history, and data persistence.