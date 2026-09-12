from playwright.async_api import Request, async_playwright, Playwright, Browser, Page
from typing import TypedDict, Optional


class M3U8Data(TypedDict):
    url: str
    headers: dict[str, str]


class WebScraper:


    def __init__(self) -> None:
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None


    async def start(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()


    def _fill_m3u8_info(self, data: M3U8Data, request: Request) -> None:
        if not data["url"] and ".m3u8" in request.url:
            data["url"] = request.url
            data["headers"] = request.headers


    async def get_master_m3u8_data(self, movie_url: str, timeout: int = 10) -> M3U8Data:

        assert self.page is not None, "Call WebScraper.start() before calling other functions."

        data: M3U8Data = {
            "url": "",
            "headers": {}
        }

        self.page.on("request", lambda request: self._fill_m3u8_info(data, request))
        await self.page.goto(movie_url)

        # Click through age verification (adjust selector to match the actual button)
        try:
            await self.page.click("text=I am 18 or older", timeout=5000)
        except Exception:
            pass  # modal might not appear every time, or already dismissed

        await self.page.wait_for_selector("video:not(.gifVideo)", state="attached", timeout=timeout * 1000)

        await self.page.evaluate("document.querySelector('video').play()")

        #secs to millisecs
        await self.page.wait_for_timeout(timeout * 1000)

        if not data["url"]:
            raise ValueError("---No master.m3u8 found in given movie url!---")
        
        return data
