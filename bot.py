import os
import random

import nltk
import requests
from moviepy import TextClip, CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords

nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger_eng')


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

    def get_relevant_word(self, text):
        """Returns the most relevant word based on part-of-speech tagging and filtering out stopwords."""
        # Tokenize the text into words
        words = word_tokenize(text)

        # Remove stop words (common words like 'the', 'is', etc.)
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.lower() not in stop_words]

        # Get part-of-speech tags
        tagged_words = pos_tag(filtered_words)

        # Filter for nouns (NN, NNP, etc.), which are typically the most meaningful for video search
        nouns = [word for word, tag in tagged_words if tag in ('NN', 'NNS', 'NNP', 'NNPS')]

        # Return the first noun (or best choice) from the filtered list
        if nouns:
            return nouns[0]  # You can also return the most frequent noun if needed
        else:
            return filtered_words[0]

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
        tts = gTTS(text, lang='en', slow=False, tld='com')
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
        output_name = f"{'_'.join(fact_text.split(' ')[:8]).lower()}.mp4"
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

            target_width, target_height = 1080, 1920
            video_clip = video_clip.resized(height=target_height)

            # If the resized width is greater than the target, crop it from the center
            if video_clip.size[0] > target_width:  # video_clip.size[0] is the width
                excess_width = (video_clip.size[0] - target_width) / 2
                video_clip = video_clip.cropped(x1=excess_width, x2=excess_width + target_width)

            voice_clip = voice_clip.with_volume_scaled(1.0)
            music_clip = music_clip.with_volume_scaled(0.08).subclipped(0, voice_clip.duration)
            final_audio = CompositeAudioClip([voice_clip, music_clip])

            if final_audio is None:
                raise ValueError("final_audio is None")

            video_clip = video_clip.subclipped(0, final_audio.duration)

            try:
                text_clip = TextClip(
                    "HussarBoldWebEdition-xq5O",
                    text=fact_text,
                    font_size=98,
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

                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=30, preset="slow",
                                            bitrate="4000k")
                return output_path
            except Exception as e:
                print(f"Error in text overlay or final video creation: {e}")
                return None
        except Exception as e:
            print(f"Error loading video or audio clips: {e}")
            return None


if __name__ == "__main__":
    FACTS = [
        "Africa is a country.",
        # "identical twins don’t have the same fingerprints. You can’t blame your crimes on your twin, after all. This is because environmental factors during development in the womb (umbilical cord length, position in the womb, and the rate of finger growth) impact your fingerprint.",
    ]

    VIDEO_API_KEY = os.getenv('VIDEO_API_KEY')
    MUSIC_FOLDER = "./music"

    generator = FactVideoGenerator(FACTS, VIDEO_API_KEY, MUSIC_FOLDER)

    try:
        fact = 'Did you know that ' + generator.get_random_fact()
        print(f"Selected Fact: {fact}")

        longest_word = generator.get_relevant_word(fact)
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
