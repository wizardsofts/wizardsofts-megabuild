import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

async def investigate_tbsnews():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Enable console log
        page.on("console", lambda msg: logger.info(f"BROWSER CONSOLE: {msg.text}"))

        # Navigate to TBS news
        logger.info("Navigating to TBS News")
        await page.goto("https://www.tbsnews.net/economy", timeout=60000)
        logger.info("Page loaded")

        # Wait for initial articles to load
        try:
            await page.wait_for_selector('.article-card', timeout=10000)
            initial_article_count = await page.evaluate('''() => {
                return document.querySelectorAll('.article-card').length;
            }''')
            logger.info(f"Initial article count: {initial_article_count}")
        except Exception as e:
            logger.error(f"Error finding article cards: {str(e)}")
            initial_article_count = 0

            # Try alternative selectors
            logger.info("Trying to identify article elements...")
            html = await page.content()
            with open("page_content.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Saved page HTML to page_content.html")

        # Analyze the page structure
        await page.evaluate('''() => {
            function analyzePageStructure() {
                // Find potential article containers
                const potentialArticleContainers = Array.from(document.querySelectorAll('div[class*="article"], div[class*="news"], div[class*="post"], div[class*="card"]'));
                console.log('Potential article containers:', potentialArticleContainers.map(el => el.className));
                
                // Find potential pagination elements
                const paginationElements = Array.from(document.querySelectorAll('div[class*="pager"], div[class*="pagination"], div[class*="load-more"], button[class*="load"]'));
                console.log('Potential pagination elements:', paginationElements.map(el => ({className: el.className, text: el.textContent.trim()})));
                
                // Find scroll event listeners
                console.log('Body has onscroll:', !!document.body.onscroll);
                console.log('Window has onscroll:', !!window.onscroll);
            }
            
            analyzePageStructure();
        }''')

        # Scroll multiple times and observe behavior
        logger.info("Starting scroll tests")
        for i in range(4):
            logger.info(f"\n--- Scroll #{i+1} ---")

            # Get current article count before scrolling
            pre_scroll_count = await page.evaluate('''() => {
                try {
                    return document.querySelectorAll('.article-card, .views-row, article, [class*="article"]').length;
                } catch(e) {
                    console.error(e);
                    return 0;
                }
            }''')

            # Scroll to bottom
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            logger.info(f"Scrolled to bottom")

            # Wait to see if new content loads
            await asyncio.sleep(5)

            # Check if new articles were loaded
            post_scroll_count = await page.evaluate('''() => {
                try {
                    return document.querySelectorAll('.article-card, .views-row, article, [class*="article"]').length;
                } catch(e) {
                    console.error(e);
                    return 0;
                }
            }''')

            logger.info(f"Articles before scroll: {pre_scroll_count}")
            logger.info(f"Articles after scroll: {post_scroll_count}")
            logger.info(f"New articles: {post_scroll_count - pre_scroll_count}")

            # Monitor network activity after scrolling
            logger.info("Checking network requests...")
            await page.evaluate('''() => {
                let originalFetch = window.fetch;
                window.fetch = function() {
                    console.log('Fetch intercepted:', arguments[0]);
                    return originalFetch.apply(this, arguments);
                }
                
                let originalXHR = window.XMLHttpRequest.prototype.open;
                window.XMLHttpRequest.prototype.open = function() {
                    console.log('XHR intercepted:', arguments[1]);
                    return originalXHR.apply(this, arguments);
                }
            }''')

            # Wait a bit more to catch any delayed network activity
            await asyncio.sleep(3)

        logger.info("Investigation completed")
        await browser.close()

asyncio.run(investigate_tbsnews())
