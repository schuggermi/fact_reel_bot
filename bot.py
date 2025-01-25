import os
import random
import requests
from moviepy import TextClip, CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip


class FactVideoGenerator:
    def __init__(self, facts, video_api_key, music_folder):
        self.facts = facts
        self.video_api_key = video_api_key
        self.music_folder = music_folder

    def get_random_fact(self):
        """Returns a random fact from the list of facts."""
        return random.choice(self.facts)

    def get_longest_word(self, text):
        """Returns the longest word in the given text."""
        words = text.split()
        return max(words, key=len)

    def get_random_video(self, search_query):
        """Fetches a random video based on the search query from a legal source."""
        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=1"
        headers = {"Authorization": self.video_api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        video_url = response.json()['videos'][0]['video_files'][0]['link']
        video_path = "temp_video.mp4"
        self.download_file(video_url, video_path)
        return video_path

    def get_random_music(self):
        """Fetches a random music file from the local folder."""
        music_files = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
        if not music_files:
            raise FileNotFoundError("No music files found in the specified folder.")
        return os.path.join(self.music_folder, random.choice(music_files))

    @staticmethod
    def synthesize_voice(text, output_path="voice.mp3"):
        """Synthesizes text into speech using a TTS API."""
        from gtts import gTTS
        tts = gTTS(text)
        tts.save(output_path)
        return output_path

    @staticmethod
    def download_file(url, destination):
        """Downloads a file from the given URL."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

    @staticmethod
    def create_video(fact_text, video_path, voice_path, music_path):
        """Combines the video, voice, and music into a final output."""
        output_name = f"{fact_text.replace(' ', '_').lower()}.mp4"
        output_path = os.path.join("output_videos", output_name)
        os.makedirs("output_videos", exist_ok=True)

        try:
            video_clip = VideoFileClip(video_path)
            voice_clip = AudioFileClip(voice_path)
            music_clip = AudioFileClip(music_path)

            if video_clip is None:
                raise ValueError("video_clip is None")
            if voice_clip is None:
                raise ValueError("voice_clip is None")
            if music_clip is None:
                raise ValueError("music_clip is None")

            music_clip = music_clip.with_volume_scaled(0.05)
            voice_clip = voice_clip.with_volume_scaled(1.0)
            music_clip = music_clip.subclipped(0, voice_clip.duration)
            final_audio = CompositeAudioClip([voice_clip, music_clip])

            if final_audio is None:
                raise ValueError("final_audio is None")

            video_clip = video_clip.subclipped(0, final_audio.duration)

            try:
                text_clip = TextClip(
                    "HussarBoldWebEdition-xq5O",
                    text=fact_text,
                    font_size=50,
                    color='white',
                    size=video_clip.size,
                    method='caption',
                    text_align='center',
                    duration=final_audio.duration,
                )
                if text_clip is None:
                    raise ValueError("Failed to create TextClip.")

                text_clip.preview()

                final_video = CompositeVideoClip([video_clip, text_clip]).with_audio(final_audio)
                if final_video is None:
                    raise ValueError("Failed to create CompositeVideoClip.")

                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)
                return output_path
            except Exception as e:
                print(f"Error in text overlay or final video creation: {e}")
                return None
        except Exception as e:
            print(f"Error loading video or audio clips: {e}")
            return None


if __name__ == "__main__":
    FACTS = [
        "About 20% of small businesses fail within their first year, and around 50% fail within five years.",
        "Lack of market need is the top reason startups fail, accounting for 42% of failures.",
        "Companies that track key performance indicators (KPIs) are 50% more likely to achieve their goals.",
        "Poor cash flow management causes 82% of business failures.",
        "Customer retention is five times cheaper than acquiring new customers.",
        "Automating repetitive tasks can increase productivity by up to 40%.",
        "Businesses that implement data-driven decision-making are 23 times more likely to acquire customers.",
        "70% of digital transformation initiatives fail due to lack of user adoption and poor strategy.",
        "Inefficient processes cost companies 20-30% of their annual revenue.",
        "Businesses that use CRM software experience an average sales increase of 29%.",
        "79% of customers will switch brands due to poor customer service.",
        "Failure to adapt to market changes is a leading reason why established businesses decline.",
        "80% of businesses that focus on employee engagement see improved performance and retention.",
        "A clear value proposition can improve conversion rates by up to 90%.",
        "Only 50% of businesses have a documented marketing strategy, despite its proven benefits.",
        "Scaling too quickly can lead to resource mismanagement and financial strain.",
        "Leveraging artificial intelligence in operations can reduce costs by up to 20%.",
        "Small businesses that use social media marketing grow their revenue 2.3 times faster than those that don't.",
        "Over 60% of businesses that fail lack a clear business plan and defined objectives.",
        "Companies that invest in training and development programs see a 24% increase in profits."
    ]

    VIDEO_API_KEY = os.getenv('VIDEO_API_KEY')
    MUSIC_FOLDER = "./music"

    generator = FactVideoGenerator(FACTS, VIDEO_API_KEY, MUSIC_FOLDER)

    try:
        fact = 'Did you know, that ' + generator.get_random_fact()
        print(f"Selected Fact: {fact}")

        longest_word = generator.get_longest_word(fact)
        print(f"Longest Word: {longest_word}")

        video_path = generator.get_random_video(longest_word)
        print(f"Downloaded Video: {video_path}")

        voice_path = generator.synthesize_voice(fact)
        print(f"Synthesized Voice: {voice_path}")

        music_path = generator.get_random_music()
        print(f"Selected Music: {music_path}")

        final_video_path = generator.create_video(fact, video_path, voice_path, music_path)
        print(f"Created Video: {final_video_path}")

    except Exception as e:
        print(f"Error: {e}")
