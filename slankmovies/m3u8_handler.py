from typing import Callable
from urllib.parse import urljoin

import m3u8


def get_variants(playlist: m3u8.M3U8, base_url: str | None = None) -> dict[str, m3u8.Playlist]:
    """Extract all variant playlists from a master M3U8 playlist.

    Returns a dict keyed by a readable label, with the actual playlist object as the value.
    """

    if not hasattr(playlist, "playlists") or not playlist.playlists:
        return {}

    variants: dict[str, m3u8.Playlist] = {}

    for index, variant in enumerate(playlist.playlists, start=1):
        stream_info = getattr(variant, "stream_info", None)
        resolution = getattr(stream_info, "resolution", None)
        bandwidth = getattr(stream_info, "bandwidth", None)

        if resolution:
            label = f"{resolution[0]}x{resolution[1]}"
        elif bandwidth:
            label = str(bandwidth)
        else:
            label = f"variant_{index}"

        if label in variants:
            label = f"{label}_{index}"

        if base_url and getattr(variant, "uri", None):
            base = base_url.rstrip("/") + "/"
            variant.uri = urljoin(base, variant.uri)

        variants[label] = variant

    return variants


def get_segment_urls(playlist: m3u8.M3U8 | m3u8.Playlist, base_url: str | None = None) -> list[str]:
    """Return all segment URLs for a single playlist object."""

    segments = getattr(playlist, "segments", None) or []
    urls: list[str] = []

    for segment in segments:
        uri = getattr(segment, "uri", None)
        if not uri:
            continue

        urls.append(urljoin(base_url or "", uri) if base_url else uri)

    return urls


def get_variant_segment_map(playlist: m3u8.M3U8, base_url: str | None = None, fetch_variant: Callable[[str], m3u8.M3U8] | None = None) -> dict[str, list[str]]:
    """Return each variant label mapped to that variant's segment download URLs.

    If fetch_variant is not provided, this only works when the master playlist's
    variant URIs are already resolvable to concrete playlists by the caller.
    """

    variants = get_variants(playlist, base_url)
    segment_map: dict[str, list[str]] = {}

    for label, variant_playlist in variants.items():
        if variant_playlist is not None and getattr(variant_playlist, "segments", None):
            segment_map[label] = get_segment_urls(variant_playlist, base_url=base_url)
            continue

        if fetch_variant is None:
            segment_map[label] = []
            continue

        variant_uri = getattr(variant_playlist, "uri", None)
        if not variant_uri:
            segment_map[label] = []
            continue

        fetched_playlist = fetch_variant(variant_uri)
        segment_map[label] = get_segment_urls(fetched_playlist, base_url=base_url)

    return segment_map
