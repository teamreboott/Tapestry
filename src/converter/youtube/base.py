import re
import datetime
from youtube_transcript_api import YouTubeTranscriptApi


def regex_search(pattern: str, string: str, group: int) -> str:
    """Shortcut method to search a string for a given pattern.

    :param str pattern:
        A regular expression pattern.
    :param str string:
        A target string to search.
    :param int group:
        Index of group to return.
    :rtype:
        str or tuple
    :returns:
        Substring pattern matches.
    """
    regex = re.compile(pattern)
    results = regex.search(string)
    if not results:
        return None

    return results.group(group)


def get_video_id(url: str) -> str:
    """Extract the ``video_id`` from a YouTube url.

    This function supports the following patterns:

    - :samp:`https://youtube.com/watch?v={video_id}`
    - :samp:`https://youtube.com/embed/{video_id}`
    - :samp:`https://youtu.be/{video_id}`

    :param str url:
        A YouTube url containing a video id.
    :rtype: str
    :returns:
        YouTube video id.
    """
    return regex_search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url, group=1)


async def get_transcript(video_id: str) -> str:
    result = ""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en', 'ja', 'zh-Hans'])
        if transcript:
            # 포맷 변경
            result = "### Transcript\n"
            for t in transcript:
                start_time = str(datetime.timedelta(seconds=int(t['start'])))
                end_time = str(datetime.timedelta(seconds=int(t['start'] + t['duration'])))
                if start_time[0] == '2':
                    break
                result += f"[{start_time} - {end_time}]: {t['text']}\n"
            return result
        else:
            result = "### Transcript\n No transcript found."
            return result
    except Exception as e:
        result = "### Transcript\n No transcript found."
        return result
