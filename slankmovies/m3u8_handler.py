import m3u8


class M3U8Handler:


    def get_m3u8_playlists(self, master: m3u8.M3U8) -> list[m3u8.Playlist]:

        playlists: list[m3u8.Playlist] = []

        for playlist in master.playlists:
            playlists.append(playlist)

        return playlists



    def get_m3u8_segments(self, playlist_m3u8: m3u8.M3U8) -> list[m3u8.Segment]:

        segments: list[m3u8.Segment] = []

        for segment in playlist_m3u8.segments:
            segments.append(segment)

        return segments
        