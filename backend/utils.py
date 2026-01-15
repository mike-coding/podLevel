import requests
import json
import pandas as pd
import re
from datetime import datetime, timezone
from sklearn.preprocessing import StandardScaler

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
    def get_channel_videos_request(channel_or_handle, debug_shape=False):
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
    @staticmethod
    def videos_to_dataframe(videos_json):
        rows = []
        for video in videos_json:
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            content_details = video.get('contentDetails', {})

            # Raw fields
            published_at = snippet.get('publishedAt')
            duration_iso = content_details.get('duration')
            caption_raw = content_details.get('caption')  # 'true'/'false' or missing
            category_id = snippet.get('categoryId')
            tags = snippet.get('tags') or []

            row = {
                'videoId': video.get('id'),
                'title': snippet.get('title'),
                'publishedAt': published_at,
                'description': snippet.get('description'),
                'viewCount': int(statistics.get('viewCount', 0) or 0),
                'likeCount': int(statistics.get('likeCount', 0) or 0),
                'commentCount': int(statistics.get('commentCount', 0) or 0),
                'duration': duration_iso,
                'categoryId': category_id,
                'hasCaptionsRaw': caption_raw,
                'numTags': len(tags),
                'titleLength': len(snippet.get('title') or ''),
                'descriptionLength': len(snippet.get('description') or ''),
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # Parse publishedAt to timezone-aware datetime (UTC) and epoch seconds
        if 'publishedAt' in df.columns:
            df['publishedAt_dt'] = pd.to_datetime(df['publishedAt'], utc=True, errors='coerce')
            # Unix timestamp seconds using Timestamp.timestamp() which handles tz-aware
            df['publishedTimestamp'] = (
                df['publishedAt_dt'].apply(lambda x: int(x.timestamp()) if pd.notnull(x) else pd.NA)
            ).astype('Int64')

            # Derived time-based features
            if df['publishedAt_dt'].notna().any():
                min_dt = df['publishedAt_dt'].min(skipna=True)
                max_dt = df['publishedAt_dt'].max(skipna=True)

                # Days since first upload (channel sequence index in days)
                ds_orig_secs = (df['publishedAt_dt'] - min_dt).astype('timedelta64[s]')
                ds_orig_days = ds_orig_secs / (24 * 3600)
                df['daysSinceOrigination'] = (
                    pd.to_numeric(ds_orig_days, errors='coerce')
                    .round()
                    .fillna(0)
                    .astype('Int64')
                )

                # Cadence: days since previous upload (chronological diff)
                df_sorted = df.sort_values('publishedAt_dt')
                diffs = df_sorted['publishedAt_dt'].diff()
                diffs_secs = diffs.astype('timedelta64[s]')
                diffs_days_num = diffs_secs / (24 * 3600)
                diffs_days_num = (
                    pd.to_numeric(diffs_days_num, errors='coerce')
                    .round()
                    .fillna(0)
                    .astype('Int64')
                )
                # Map back to original order
                df.loc[df_sorted.index, 'daysSinceLastVideo'] = diffs_days_num

                # Use apply to avoid static analysis complaints on datetime accessors
                df['hourOfDay'] = df['publishedAt_dt'].apply(lambda x: x.hour if pd.notnull(x) else pd.NA).astype('Int64')
                df['dayOfWeek'] = df['publishedAt_dt'].apply(lambda x: x.dayofweek if pd.notnull(x) else pd.NA).astype('Int64')
            else:
                df['daysSinceOrigination'] = pd.Series([None] * len(df), dtype='Int64')
                df['daysSinceLastVideo'] = pd.Series([None] * len(df), dtype='Int64')
                df['hourOfDay'] = pd.Series([None] * len(df), dtype='Int64')
                df['dayOfWeek'] = pd.Series([None] * len(df), dtype='Int64')

        # ISO 8601 duration to seconds
        def parse_iso8601_duration_to_seconds(s: str) -> int:
            if not isinstance(s, str) or not s:
                return 0
            # Pattern like PT#H#M#S (any subset)
            m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
            if not m:
                # Sometimes YouTube may include days: P#DT#H#M#S; handle D optionally
                m2 = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
                if not m2:
                    return 0
                days = int(m2.group(1) or 0)
                hours = int(m2.group(2) or 0)
                minutes = int(m2.group(3) or 0)
                seconds = int(m2.group(4) or 0)
                return days * 86400 + hours * 3600 + minutes * 60 + seconds
            hours = int(m.group(1) or 0)
            minutes = int(m.group(2) or 0)
            seconds = int(m.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds

        df['durationSeconds'] = df['duration'].apply(parse_iso8601_duration_to_seconds).astype('Int64')

        # has_captions -> bool derived from contentDetails.caption ('true'/'false')
        def to_bool(x):
            if isinstance(x, bool):
                return x
            if isinstance(x, str):
                x = x.strip().lower()
                if x in ('true', '1', 'yes'):
                    return True
                if x in ('false', '0', 'no'):
                    return False
            return None

        df['hasCaptions'] = df['hasCaptionsRaw'].apply(to_bool)

        # category -> categoryId (one-hot encoded)
        if 'categoryId' in df.columns:
            # Keep raw categoryId as string for consistency
            df['categoryId'] = df['categoryId'].astype(str)
            cat_dummies = pd.get_dummies(df['categoryId'], prefix='cat', dtype='Int64')
            df = pd.concat([df, cat_dummies], axis=1)

        # dayOfWeek -> one-hot encoded (dow_0..dow_6)
        if 'dayOfWeek' in df.columns:
            dow_dummies = pd.get_dummies(df['dayOfWeek'], prefix='dow', dtype='Int64')
            # Ensure consistent 7 columns even if some days are missing
            for d in range(7):
                col = f'dow_{d}'
                if col not in dow_dummies.columns:
                    dow_dummies[col] = 0
            dow_dummies = dow_dummies[[f'dow_{d}' for d in range(7)]]
            df = pd.concat([df, dow_dummies], axis=1)

        # Convert hasCaptions to binary int 0/1
        df['hasCaptions'] = df['hasCaptions'].map({True: 1, False: 0}).fillna(0).astype('Int64')

        # Build scikit-learn ready features: numeric-only, no NaNs
        feature_cols = [
            'viewCount', 'likeCount', 'commentCount', 'durationSeconds',
            'numTags', 'titleLength', 'descriptionLength',
            'publishedTimestamp', 'daysSinceOrigination', 'daysSinceLastVideo',
            'hourOfDay', 'hasCaptions'
        ]
        feature_cols += [c for c in df.columns if c.startswith('cat_')]
        feature_cols += [c for c in df.columns if c.startswith('dow_')]

        df_features = df[feature_cols].copy()
        # Ensure numeric dtypes and fill missing with 0.0
        df_features = df_features.apply(pd.to_numeric, errors='coerce').fillna(0.0)
        # Cast to float64 for uniformity across estimators
        df_features = df_features.astype('float64')

        return df_features

class ML_Tools:

    @staticmethod
    def compute_trend_slope(
        df: pd.DataFrame,
        target_column: str,
        time_column: str = 'daysSinceOrigination',
    ) -> dict | None:
        """Compute an overall linear trend (best-fit slope) of target vs time.

        Returns a JSON-serializable dict with slope/intercept/r2, or None if
        there isn't enough usable data.

        Slope units are: (target units) per (time_column units).
        For the default time_column, slope is "per day".
        """
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score

        if df is None or df.empty:
            return None
        if target_column not in df.columns:
            return None
        if time_column not in df.columns:
            return None

        x = pd.to_numeric(df[time_column], errors='coerce')
        y = pd.to_numeric(df[target_column], errors='coerce')
        valid = x.notna() & y.notna()
        x = x[valid]
        y = y[valid]

        if len(x) < 2:
            return None
        if x.nunique(dropna=True) < 2:
            return None

        X = x.to_numpy().reshape(-1, 1)
        y_arr = y.to_numpy()

        model = LinearRegression()
        model.fit(X, y_arr)
        y_pred = model.predict(X)

        slope = float(model.coef_[0])
        intercept = float(model.intercept_)
        r2 = float(r2_score(y_arr, y_pred))

        direction = 'up' if slope > 0 else ('down' if slope < 0 else 'flat')
        avg = float(y.mean()) if len(y) else 0.0
        pct_per_unit = float((slope / avg) * 100.0) if avg != 0 else None

        return {
            'timeColumn': time_column,
            'targetColumn': target_column,
            'slope': slope,
            'intercept': intercept,
            'r2': r2,
            'n': int(len(x)),
            'direction': direction,
            'avgTarget': avg,
            'pctChangePerTimeUnit': pct_per_unit,
        }

    @staticmethod
    def standardize_features(df: pd.DataFrame) -> pd.DataFrame:
        # Assumes df is numeric-only (as returned by Formatter.videos_to_dataframe)
        if df.empty:
            return df.copy()

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df.values)
        # Preserve column names and index
        df_scaled = pd.DataFrame(X_scaled, columns=df.columns, index=df.index)
        return df_scaled
    
    @staticmethod
    def run_linear_regression(
        df: pd.DataFrame,
        target_column: str,
        trend_df: pd.DataFrame | None = None,
        trend_time_column: str = 'daysSinceOrigination',
    ):
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
        from sklearn.model_selection import train_test_split

        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame")

        X = df.drop(columns=[target_column])
        y = df[target_column]

        if X.shape[1] == 0:
            raise ValueError("No feature columns available after dropping target")

        # Train/test split when dataset is large enough
        n_samples = len(df)
        if n_samples >= 5:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        else:
            # For tiny datasets, fit on all data and evaluate on train
            X_train, y_train = X, y
            X_test, y_test = X, y

        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = mse ** 0.5
        metrics = {
            'r2': float(r2_score(y_test, y_pred)),
            'mae': float(mean_absolute_error(y_test, y_pred)),
            'mse': float(mse),
            'rmse': float(rmse),
        }

        coef_map = {col: float(coef) for col, coef in zip(X.columns, model.coef_)}

        result = {
            'model': model,
            'coefficients': coef_map,
            'intercept': float(model.intercept_),
            'metrics': metrics,
            'n_train': int(len(X_train)),
            'n_test': int(len(X_test)),
        }

        # Overall up/down trend: best-fit slope of target vs time
        try:
            trend_source = trend_df if trend_df is not None else df
            result['trend'] = ML_Tools.compute_trend_slope(
                trend_source,
                target_column=target_column,
                time_column=trend_time_column,
            )
        except Exception:
            result['trend'] = None

        return result
    
    @staticmethod
    def print_regression_summary(lr_result: dict):
        print("Linear Regression Summary:")
        print(f"Number of training samples: {lr_result['n_train']}")
        print(f"Number of testing samples: {lr_result['n_test']}")
        print("Metrics:")
        for metric, value in lr_result['metrics'].items():
            print(f"  {metric}: {value:.4f}")
        trend = lr_result.get('trend')
        if isinstance(trend, dict) and trend.get('slope') is not None:
            slope = trend.get('slope')
            direction = trend.get('direction')
            time_col = trend.get('timeColumn')
            pct = trend.get('pctChangePerTimeUnit')
            print("Overall Trend:")
            print(f"  direction: {direction}")
            print(f"  slope ({trend.get('targetColumn')} per {time_col}): {slope:.4f}")
            if isinstance(pct, (int, float)):
                print(f"  pctChangePerTimeUnit: {pct:.4f}%")
        print("Coefficients:")
        for feature, coef in lr_result['coefficients'].items():
            print(f"  {feature}: {coef:.4f}")
        print(f"Intercept: {lr_result['intercept']:.4f}")
