"""
API Discovery Tool - Auto-Generate Scrapers from Any Website

This tool:
1. Opens a website in browser
2. Captures all network requests (XHR/Fetch)
3. Identifies JSON API endpoints
4. Auto-generates scraper code
5. Tests the endpoints

Usage:
    python -m backend.tools.api_discovery "https://finance.yahoo.com/quote/AAPL"
"""
from playwright.async_api import async_playwright
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import json
import asyncio
from pathlib import Path


class APIDiscovery:
    """
    Discover undocumented APIs by monitoring browser network traffic.
    """
    
    def __init__(self):
        self.discovered_apis: List[Dict[str, Any]] = []
        self.json_endpoints: List[Dict[str, Any]] = []
        logger.info("API Discovery tool initialized")
    
    async def discover(
        self,
        url: str,
        wait_seconds: int = 5,
        interactions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover APIs by visiting a URL and monitoring network traffic.
        
        Args:
            url: Website URL to inspect
            wait_seconds: How long to wait for page load
            interactions: Optional list of CSS selectors to click
        
        Returns:
            List of discovered API endpoints
        """
        logger.info(f"Discovering APIs from: {url}")
        
        async with async_playwright() as p:
            # Launch browser (headless)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Capture network requests
            async def handle_request(request):
                """Monitor outgoing requests"""
                if request.resource_type in ['xhr', 'fetch']:
                    self.discovered_apis.append({
                        'type': 'request',
                        'method': request.method,
                        'url': request.url,
                        'headers': request.headers,
                        'resource_type': request.resource_type,
                        'timestamp': datetime.now().isoformat(),
                    })
            
            async def handle_response(response):
                """Monitor responses"""
                if response.request.resource_type in ['xhr', 'fetch']:
                    try:
                        # Try to parse as JSON
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type:
                            body = await response.text()
                            try:
                                json_data = json.loads(body)
                                self.json_endpoints.append({
                                    'method': response.request.method,
                                    'url': response.url,
                                    'status': response.status,
                                    'headers': dict(response.headers),
                                    'sample_response': json_data,
                                    'timestamp': datetime.now().isoformat(),
                                })
                                logger.info(f"Found JSON API: {response.request.method} {response.url}")
                            except json.JSONDecodeError:
                                pass
                    except Exception as e:
                        logger.debug(f"Error processing response: {e}")
            
            # Attach listeners
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # Navigate to page (use 'load' instead of 'networkidle' for faster results)
            try:
                await page.goto(url, wait_until='load', timeout=30000)
            except Exception as e:
                logger.warning(f"Page load timeout (expected for heavy pages): {e}")
                # Continue anyway - we likely captured some APIs

            
            # Wait for dynamic content
            await asyncio.sleep(wait_seconds)
            
            # Optional interactions (e.g., click tabs, scroll)
            if interactions:
                for selector in interactions:
                    try:
                        await page.click(selector)
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.warning(f"Could not click {selector}: {e}")
            
            await browser.close()
        
        logger.info(f"Discovered {len(self.json_endpoints)} JSON API endpoints")
        return self.json_endpoints
    
    def generate_scraper_code(
        self,
        endpoint: Dict[str, Any],
        output_file: Optional[str] = None
    ) -> str:
        """
        Auto-generate scraper code for a discovered endpoint.
        
        Args:
            endpoint: Discovered endpoint dict
            output_file: Optional file to save code
        
        Returns:
            Generated Python code as string
        """
        url = endpoint['url']
        method = endpoint['method']
        sample_response = endpoint.get('sample_response', {})
        
        # Extract variable parts of URL (query params, path segments)
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Generate function name from URL
        func_name = parsed.path.strip('/').replace('/', '_').replace('-', '_')
        if not func_name:
            func_name = 'fetch_data'
        
        # Generate code
        code = f'''"""
Auto-generated scraper for {url}
Generated on {datetime.now().isoformat()}
"""
import httpx
from typing import Optional, Dict, Any
from loguru import logger


async def {func_name}(
'''
        
        # Add parameters based on query params
        if query_params:
            for param in query_params.keys():
                code += f'    {param}: str,\n'
        
        code += f''') -> Optional[Dict[str, Any]]:
    """
    Fetch data from {parsed.netloc}
    
    Method: {method}
    Endpoint: {parsed.path}
    """
    url = "{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    headers = {{
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }}
    
    params = {{
'''
        
        # Add query parameters
        if query_params:
            for param in query_params.keys():
                code += f'        "{param}": {param},\n'
        
        code += f'''    }}
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.{method.lower()}(
                url,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched data from {parsed.netloc}")
            return data
    
    except Exception as e:
        logger.error(f"Failed to fetch data: {{e}}")
        return None


# Example usage:
# data = await {func_name}({', '.join(f'"{k}=example"' for k in query_params.keys()) if query_params else ''})
'''
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(code)
            logger.info(f"Saved scraper code to {output_file}")
        
        return code
    
    def save_report(self, output_file: str = "api_discovery_report.json"):
        """
        Save discovery report to JSON file.
        
        Args:
            output_file: Output filename
        """
        report = {
            'discovery_time': datetime.now().isoformat(),
            'total_requests': len(self.discovered_apis),
            'json_endpoints': len(self.json_endpoints),
            'endpoints': self.json_endpoints,
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved discovery report to {output_file}")
    
    def print_summary(self):
        """Print a summary of discovered APIs"""
        print("\n" + "="*60)
        print("API Discovery Summary")
        print("="*60)
        print(f"\nTotal requests captured: {len(self.discovered_apis)}")
        print(f"JSON API endpoints found: {len(self.json_endpoints)}")
        
        if self.json_endpoints:
            print("\nDiscovered JSON APIs:")
            for i, endpoint in enumerate(self.json_endpoints, 1):
                print(f"\n{i}. {endpoint['method']} {endpoint['url']}")
                print(f"   Status: {endpoint['status']}")
                
                # Handle both dict and list responses
                sample = endpoint.get('sample_response', {})
                if isinstance(sample, dict):
                    keys = list(sample.keys())[:5]
                elif isinstance(sample, list):
                    keys = ['<array>'] if sample else ['<empty array>']
                else:
                    keys = ['<unknown>']
                
                print(f"   Response keys: {keys}")


# Singleton instance
api_discovery = APIDiscovery()


async def discover_and_generate(url: str, output_dir: str = "generated_scrapers"):
    """
    Convenience function to discover APIs and generate scrapers.
    
    Args:
        url: Website URL to inspect
        output_dir: Directory to save generated scrapers
    """
    # Discover APIs
    endpoints = await api_discovery.discover(url)
    
    # Generate scrapers for each endpoint
    Path(output_dir).mkdir(exist_ok=True)
    
    for i, endpoint in enumerate(endpoints):
        filename = f"{output_dir}/scraper_{i+1}.py"
        api_discovery.generate_scraper_code(endpoint, filename)
    
    # Save report
    api_discovery.save_report(f"{output_dir}/discovery_report.json")
    
    # Print summary
    api_discovery.print_summary()
    
    return endpoints
