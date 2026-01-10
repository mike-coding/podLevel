# YouTube Video Data Cheat Sheet (via `videos.list` / `playlistItems.list`)

This is a reference for the key fields returned by the YouTube Data API and ideas for analysis.

---

## 1. Top-level fields

| Field | Type | Notes |
|-------|------|-------|
| `kind` | string | Resource type (usually `"youtube#video"`). Metadata only. |
| `etag` | string | Version tag, useful for caching/deduplication. |
| `id` | string | **Video ID** (e.g., `dQw4w9WgXcQ`). Core identifier. |

---

## 2. `snippet` – human-readable metadata

| Field | Type | Notes / Ideas |
|-------|------|---------------|
| `publishedAt` | string (ISO 8601) | Upload timestamp. Use for cadence, time-series plots. |
| `channelId` | string | Channel identifier; useful for multi-channel analysis. |
| `title` | string | Video title; can parse for guest names, keywords, etc. |
| `description` | string | Video description; useful for guests, sponsors, hashtags. |
| `thumbnails` | object | Multiple resolutions; optional for UI or correlation studies. |
| `channelTitle` | string | Channel name. Cosmetic. |
| `tags` | array | YouTube-assigned tags; can infer genre/topic. |
| `categoryId` | string | Numeric category; normalize for content type. |
| `liveBroadcastContent` | string | `"none"`, `"live"`, `"upcoming"`. Filter live streams if needed. |
| `defaultLanguage` / `defaultAudioLanguage` | string | Can group by language. |
| `localized` | object | Title and description in default language. |

**Ideas for analysis**:

- Count videos by category/tag
- Track cadence via `publishedAt`
- Word clouds / guest detection from titles/descriptions

---

## 3. `contentDetails` – technical metadata

| Field | Type | Notes / Ideas |
|-------|------|---------------|
| `duration` | string (ISO 8601) | Convert to seconds; analyze duration vs views/retention. |
| `dimension` | string | `"2d"` or `"3d"`; mostly irrelevant for podcasts. |
| `definition` | string | `"hd"` or `"sd"`; see if quality correlates with engagement. |
| `caption` | string | `"true"`/`"false"`; captions vs engagement. |
| `licensedContent` | bool | Mostly true; standard upload indicator. |
| `contentRating` | object | Usually empty; age restrictions. |
| `projection` | string | `"rectangular"`; rarely relevant. |

**Ideas for analysis**:

- Duration vs views
- HD vs SD engagement comparison
- Captions impact

---

## 4. `statistics` – engagement metrics

| Field | Type | Notes / Ideas |
|-------|------|---------------|
| `viewCount` | string | Number of views; main performance metric. Convert to int. |
| `likeCount` | string | Likes; can compute like/view ratio. |
| `favoriteCount` | string | Mostly unused in modern YouTube. |
| `commentCount` | string | Comment volume; engagement proxy. |

**Ideas for analysis**:

- Episode growth curves over time
- Engagement ratios: likes/views, comments/views
- Detect spikes or dips (guest impact, trending episodes)

---

## 5. Suggested analytics pipeline

1. **Time series**: plot `viewCount` vs `publishedAt`. Overlay major events (guest, host changes).
2. **Engagement ratios**: `likeCount/viewCount`, `commentCount/viewCount`.
3. **Episode features**: duration, category, tags, captions, HD/SD.
4. **Cohort analysis**: compare episodes with guests vs without, early vs late episodes.
5. **Trend detection**: rolling averages, inflection points, spikes/dips.

---

## 6. Practical notes

- Numeric values are returned as strings → convert to `int`.
- Thumbnails are mainly for UI; optional for analysis.
- Tags and descriptions may require NLP/regex for structured insights.
- Historical view counts are **not provided** by the API → store snapshots over time if building trends.
- Efficient batching: `videos.list` allows up to **50 video IDs per request**.

---

## 7. Key takeaways

- `id` = canonical video identifier.
- `snippet` = human-readable metadata.
- `contentDetails` = technical metadata (duration, captions, quality).
- `statistics` = engagement metrics (views, likes, comments).
- Combine all to compute metrics, trends, and episode trajectories.
