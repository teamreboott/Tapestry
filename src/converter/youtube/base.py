import re
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi


def format_time(seconds_float):
    # 초를 반올림해서 정수로 변환
    total_seconds = int(round(seconds_float))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"


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
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        try:
            transcript = transcript_list.find_manually_created_transcript(['ko', 'en', 'ja', 'zh-Hans'])  
            response = transcript.fetch()
        except Exception as e:
            try:
                transcript = transcript_list.find_generated_transcript(['ko', 'en', 'ja', 'zh-Hans'])
                response = transcript.fetch()
            except Exception as e:
                result = f"Error: {e}"
                return result
        
        result = "### Transcript\n"
        for chunk in response:
            start_time = chunk.start
            end_time = start_time + chunk.duration
            text = chunk.text
            
            start_time_formatted = format_time(start_time)
            end_time_formatted = format_time(end_time)
            result += f"[{start_time_formatted} - {end_time_formatted}]: {text}\n"
        return result
    except Exception as e:
        result = f"Error: {e}"
        return result


if __name__ == "__main__":
    import asyncio
    video_id = get_video_id("https://www.youtube.com/watch?v=A1S19JzHN2M")
    print(asyncio.run(get_transcript(video_id)))