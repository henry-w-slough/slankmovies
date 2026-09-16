from __future__ import annotations

import asyncio
from typing import TypedDict

from playwright.async_api import (
	Browser,
	BrowserContext,
	Page,
	Playwright,
	Request,
	async_playwright,
)


class M3U8Data(TypedDict):
	url: str
	headers: dict[str, str]


class WebScraper:
	"""Resolve an HLS playlist requested by a movie page in a real browser."""

	def __init__(self, headless: bool = True) -> None:
		self.headless = headless
		self.playwright: Playwright | None = None
		self.browser: Browser | None = None
		self.context: BrowserContext | None = None
		self.pages: set[Page] = set()
		self.playlist_requests: list[Request] = []

	async def start(self) -> None:
		self.playwright = await async_playwright().start()
		self.browser = await self.playwright.chromium.launch(headless=self.headless)
		self.context = await self.browser.new_context()
		self.context.on("page", self._register_page)

	async def close(self) -> None:
		if self.browser is not None:
			await self.browser.close()
			self.browser = None

		if self.playwright is not None:
			await self.playwright.stop()
			self.playwright = None

		self.context = None
		self.pages.clear()

	async def resolve_m3u8(
		self,
		movie_url: str,
		timeout: float = 30.0,
	) -> M3U8Data:
		"""Load a movie page, start playback, and return the HLS request details."""
		if self.context is None:
			raise RuntimeError("Call start() before resolve_m3u8().")

		self.playlist_requests.clear()
		page = await self.context.new_page()
		self._register_page(page)

		try:
			await page.goto(
				movie_url,
				wait_until="domcontentloaded",
				timeout=int(timeout * 1000),
			)
			await self._dismiss_common_prompts(page)
			await self._start_playback(page)

			deadline = asyncio.get_running_loop().time() + timeout
			while not self.playlist_requests:
				if asyncio.get_running_loop().time() >= deadline:
					raise TimeoutError(
						f"No m3u8 request was observed for '{movie_url}'. "
						"A site verification may require user interaction."
					)
				await asyncio.sleep(0.25)

			request = self._select_playlist_request()
			return {
				"url": request.url,
				"headers": dict(request.headers),
			}
		finally:
			await page.close()
			self.pages.discard(page)

	def _register_page(self, page: Page) -> None:
		if page in self.pages:
			return

		self.pages.add(page)
		page.on("request", self._capture_request)

	def _capture_request(self, request: Request) -> None:
		url = request.url.lower()
		if ".m3u8" in url or "/hls/" in url or "/manifest" in url:
			self.playlist_requests.append(request)

	def _select_playlist_request(self) -> Request:
		def score(request: Request) -> int:
			url = request.url.lower()
			return sum(
				marker in url
				for marker in ("master", "playlist", "manifest")
			)

		return max(self.playlist_requests, key=score)

	async def _start_playback(self, page: Page) -> None:
		await page.evaluate(
			"""
			async () => {
				const videos = [...document.querySelectorAll('video')];
				const video = videos.find((item) => !item.classList.contains('gifVideo'));
				if (video) {
					video.muted = true;
					await video.play();
				}
			}
			"""
		)

	async def _dismiss_common_prompts(self, page: Page) -> None:
		selectors = (
			"button:has-text('I am 18')",
			"button:has-text('Accept')",
			"button:has-text('Agree')",
			"button:has-text('Continue')",
		)

		for selector in selectors:
			try:
				await page.locator(selector).first.click(timeout=1000)
			except Exception:
				pass
