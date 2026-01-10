import requests
import json

class Requester:
    api_key = ""
    API_BASE = "https://www.googleapis.com/youtube/v3"

    @staticmethod
    def store_key_from_env():
        from dotenv import load_dotenv
        import os

        load_dotenv()
        Requester.api_key = os.getenv('KEY', '')

    @staticmethod
    def resolve_channel_id(channel_or_handle: str) -> str:
        """Return a channelId for either a raw channelId or a YouTube @handle.
        If resolution fails, return the original input.
        """
        if isinstance(channel_or_handle, str) and channel_or_handle.startswith('@'):
            handle = channel_or_handle.lstrip('@')
            data = Requester.request_json(
                f"{Requester.API_BASE}/channels",
                {
                    "part": "id",
                    "forHandle": handle,
                    "key": Requester.api_key,
                },
            )
            try:
                return data['items'][0]['id']
            except (KeyError, IndexError):
                return channel_or_handle
        return channel_or_handle

    @staticmethod
    def request_json(url: str, params: dict, timeout: int = 10):
        """Perform a GET request and return parsed JSON with status checks."""
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_channel_details(channel_id: str):
        """Fetch channel metadata (contentDetails) for a channel and return JSON."""
        return Requester.request_json(
            f"{Requester.API_BASE}/channels",
            {
                "part": "contentDetails",
                "id": channel_id,
                "key": Requester.api_key,
            },
        )

    @staticmethod
    def get_uploads_playlist_id(channel_id: str):
        """Return the uploads playlist ID for a given channel, or None if unavailable."""
        ch_data = Requester.get_channel_details(channel_id)
        ch_items = ch_data.get('items', [])
        if not ch_items:
            return None
        uploads_playlist_id = (
            ch_items[0]
            .get('contentDetails', {})
            .get('relatedPlaylists', {})
            .get('uploads')
        )
        return uploads_playlist_id

    @staticmethod
    def get_all_video_ids(playlist_id: str):
        """Return all video IDs from a given playlist via paginated playlistItems requests."""
        video_ids = []
        pl_params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": Requester.api_key,
        }
        while True:
            pl_data = Requester.request_json(
                f"{Requester.API_BASE}/playlistItems",
                pl_params,
            )
            for item in pl_data.get('items', []):
                vid = item.get('contentDetails', {}).get('videoId')
                if vid:
                    video_ids.append(vid)
            token = pl_data.get('nextPageToken')
            if not token:
                break
            pl_params["pageToken"] = token
        return video_ids

    @staticmethod
    def get_video_details(video_ids):
        """Fetch detailed video data for a list of video IDs (chunks of 50)."""
        all_video_data = []
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            v_data = Requester.request_json(
                f"{Requester.API_BASE}/videos",
                {
                    "part": "snippet,contentDetails,statistics",
                    "id": ",".join(chunk),
                    "key": Requester.api_key,
                },
            )
            all_video_data.extend(v_data.get('items', []))
        return all_video_data
    
    @staticmethod
    def get_channel_videos_request(channel_or_handle, debug_shape=True):
        # Ensure we have an API key available for testing
        if not Requester.api_key:
            try:
                Requester.store_key_from_env()
            except Exception:
                return []

        try:
            # Resolve handle to channel ID if needed
            channel_id = Requester.resolve_channel_id(channel_or_handle)
            # Get uploads playlist ID
            uploads_playlist_id = Requester.get_uploads_playlist_id(channel_id)
            if not uploads_playlist_id:
                return []

            # Get all video IDs from the uploads playlist
            video_ids = Requester.get_all_video_ids(uploads_playlist_id)
            # Fetch detailed video data for those IDs
            all_video_data = Requester.get_video_details(video_ids)
            if debug_shape:
                DebugTools.create_response_shape_debug_example(all_video_data)
            return all_video_data
        except requests.RequestException:
            # On network/API errors, return an empty list for testing simplicity
            return []
    
class DebugTools:
    @staticmethod
    def create_response_shape_debug_example(data, outfile='response_shape_debug.json'):
        # Produce a readable "shape" summary of nested JSON data.
        def type_name(v):
            if v is None:
                return 'null'
            if isinstance(v, bool):
                return 'bool'
            if isinstance(v, int):
                return 'int'
            if isinstance(v, float):
                return 'float'
            if isinstance(v, str):
                return 'str'
            if isinstance(v, list):
                return 'list'
            if isinstance(v, dict):
                return 'dict'
            return type(v).__name__

        def merge_shapes(a, b):
            if a is None:
                return b
            if b is None:
                return a

            # Primitive type name unions (e.g., 'int' vs 'str')
            if isinstance(a, str) and isinstance(b, str):
                if a == b:
                    return a
                return sorted(set([a, b]))

            # List of primitive type names + single primitive
            if isinstance(a, list) and all(isinstance(x, str) for x in a) and isinstance(b, str):
                if b in a:
                    return a
                return sorted(a + [b])

            # Dict merge (used for nested object shapes and list item shapes)
            if isinstance(a, dict) and isinstance(b, dict):
                result = dict(a)
                for key in set(a.keys()) | set(b.keys()):
                    result[key] = merge_shapes(a.get(key), b.get(key))
                return result

            # Mixed shapes (e.g., dict vs primitive): represent as anyOf
            def to_anyof(x):
                if isinstance(x, dict) and 'anyOf' in x and isinstance(x['anyOf'], list):
                    return x['anyOf']
                return [x]

            anyof = to_anyof(a) + to_anyof(b)
            # Deduplicate primitive entries
            prims = set()
            deduped = []
            for x in anyof:
                if isinstance(x, str):
                    if x in prims:
                        continue
                    prims.add(x)
                    deduped.append(x)
                else:
                    deduped.append(x)
            return {'anyOf': deduped}

        def shape_of(v):
            if isinstance(v, dict):
                result = {}
                for k, val in v.items():
                    result[k] = merge_shapes(result.get(k), shape_of(val))
                return result
            if isinstance(v, list):
                item_shape = None
                for item in v:
                    item_shape = merge_shapes(item_shape, shape_of(item))
                if item_shape is None:
                    item_shape = 'empty'
                return {'list_item': item_shape}
            return type_name(v)

        shape = shape_of(data)
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(shape, f, indent=2, ensure_ascii=False)

class Formatter:
    pass