import os
import random
import time
from collections import Counter
from pathlib import Path

import nltk
import requests
from moviepy import TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from nltk import word_tokenize, pos_tag, FreqDist, WordNetLemmatizer
from nltk.corpus import stopwords
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
import wave
import json

nltk.download('wordnet')
# nltk.download('stopwords')
# nltk.download('averaged_perceptron_tagger_eng')


def load_facts(facts_file):
    """Reads facts from a file and returns them as a list."""
    with open(facts_file, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def get_longest_word(text):
    """Returns the longest word in the given text."""
    words = text.split()
    return max(words, key=len)


def synthesize_voice(text, output_path="voice.mp3"):
    """Synthesizes text into speech using a TTS API."""
    from gtts import gTTS
    tts = gTTS(text, lang='en', slow=False, tld='com')
    tts.save(output_path)
    return output_path


def get_word_timings(audio_path, transcript_text):
    """Extracts word timings using Vosk speech recognition."""

    wf = wave.open(audio_path, "rb")
    model = Model("vosk-model")
    recognizer = KaldiRecognizer(model, wf.getframerate())
    recognizer.SetWords(True)  # Enable word-level timestamps

    results = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break  # Stop if no more data

        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            results.append(result)

        # Process final result
    final_result = json.loads(recognizer.FinalResult())
    results.append(final_result)

    word_timings = []
    for res in results:
        if "result" in res:  # Check if timestamps exist
            for word in res["result"]:
                word_timings.append((word["word"], word["start"], word["end"]))

    return word_timings


class FactVideoGenerator:
    def __init__(self, facts_file, video_api_key, music_folder, video_cache_dir="cached_videos"):
        self.facts = load_facts(facts_file)
        self.video_api_key = video_api_key
        self.music_folder = music_folder
        self.video_cache_dir = Path(video_cache_dir)
        self.video_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_random_fact(self):
        """Returns a random fact from the list of facts."""
        return random.choice(self.facts)

    @staticmethod
    def generate_hashtags(text, num_hashtags=5):
        # Tokenize the text into words
        words = word_tokenize(text)

        # Remove stopwords (common words like "the", "is", etc.)
        stop_words = set(stopwords.words("english"))
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]

        # Count the frequency of each word
        word_freq = Counter(filtered_words)

        # Get the most common words as hashtags
        most_common_words = word_freq.most_common(num_hashtags)
        hashtag_list = ["#" + word for word, freq in most_common_words]

        return hashtag_list

    @staticmethod
    def get_relevant_word(text):
        """Returns the most relevant word based on frequency, part-of-speech tagging, and stopword removal."""

        # Tokenize and clean the text
        words = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        words = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]

        if not words:
            return None  # Handle empty input after stopword removal

        # Part-of-speech tagging
        tagged_words = pos_tag(words)

        # Lemmatization to get base forms
        lemmatizer = WordNetLemmatizer()
        nouns = [lemmatizer.lemmatize(word) for word, tag in tagged_words if tag.startswith('NN')]

        # Prioritize the most frequent noun
        if nouns:
            return FreqDist(nouns).max()

        # Fallback: Use adjectives if no nouns found
        adjectives = [lemmatizer.lemmatize(word) for word, tag in tagged_words if tag.startswith('JJ')]
        if adjectives:
            return FreqDist(adjectives).max()

        # Final fallback: Return the most common remaining word
        return FreqDist(words).max()

    def get_video_path(self, search_query):
        key_folder = self.video_cache_dir / search_query
        key_folder.mkdir(parents=True, exist_ok=True)
        return key_folder / "video.mp4"

    def get_random_video(self, search_query):
        """Fetches a random video based on the search query from a legal source."""
        random_video_path = self.get_video_path(search_query)

        if random_video_path.exists():
            print(f"Using cached video for: {search_query}")
            return str(random_video_path)

        url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=15"
        headers = {"Authorization": self.video_api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        best_video_url = None

        if response.status_code == 200:
            data = response.json()
            if data["videos"]:
                # Sort videos by the highest resolution available
                sorted_videos = sorted(
                    data["videos"],
                    key=lambda vid: max(file["width"] * file["height"] for file in vid["video_files"]),
                    reverse=True
                )

                # Select the best quality video
                best_video = sorted_videos[0]
                best_video_url = max(best_video["video_files"], key=lambda f: f["width"] * f["height"])["link"]

        self.download_file(best_video_url, random_video_path)
        return str(random_video_path)

    def get_random_music(self):
        """Fetches a random music file from the local folder."""
        music_files = [f for f in os.listdir(self.music_folder) if f.endswith(".mp3")]
        if not music_files:
            raise FileNotFoundError("No music files found in the specified folder.")
        return os.path.join(self.music_folder, random.choice(music_files))

    @staticmethod
    def download_file(url, destination):
        """Downloads a file from the given URL."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

    @staticmethod
    def wait_for_file(file_path, timeout=5):
        """Waits for a file to be fully created before proceeding."""
        start_time = time.time()

        while not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout: File '{file_path}' not fully created within {timeout} seconds.")
            time.sleep(0.1)  # Wait a bit before checking again

        return True

    def create_video(self, new_fact_text, new_video_path, new_voice_path, new_music_path):
        """Combines the video, voice, and music into a final output with word-by-word text animation."""
        output_name = f"{'_'.join(new_fact_text.split(' ')[:8]).lower()}.mp4"
        output_path = os.path.join("output_videos", output_name)
        os.makedirs("output_videos", exist_ok=True)

        try:
            # Load video and audio clips
            video_clip = VideoFileClip(new_video_path)
            voice_clip = AudioFileClip(new_voice_path)
            music_clip = AudioFileClip(new_music_path)

            # Ensure video loops to match or exceed voice duration
            looped_clips = []
            total_duration = 0
            while total_duration < voice_clip.duration:
                looped_clips.append(video_clip.copy())
                total_duration += video_clip.duration

            video_clip = concatenate_videoclips(looped_clips).with_duration(voice_clip.duration)

            # Extract precise word timings
            word_timings = get_word_timings(
                self.convert_audio_to_wav(new_voice_path),
                new_fact_text,
            )

            # Resize and crop video to fit 1080x1920
            target_width, target_height = 1080, 1920
            padding = 50  # Padding around text
            text_area_width = target_width - 2 * padding
            text_area_height = target_height - 2 * padding

            video_clip = video_clip.resized(height=target_height)
            if video_clip.size[0] > target_width:
                excess_width = (video_clip.size[0] - target_width) / 2
                video_clip = video_clip.cropped(x1=excess_width, x2=excess_width + target_width)

            # Adjust audio volumes and combine
            voice_clip = voice_clip.with_volume_scaled(1.0)
            music_clip = music_clip.with_volume_scaled(0.08).subclipped(0, voice_clip.duration)
            final_audio = CompositeAudioClip([voice_clip, music_clip])

            text_clips = []

            for word, start_time, end_time in word_timings:
                # Handle text wrapping if too large
                max_font_size = 100
                word_clip = None
                for fontsize in range(max_font_size, 50, -10):  # Try decreasing font size
                    # Create a TextClip for the current word
                    word_clip = TextClip(
                        text=word,
                        text_align='center',
                        color='white',
                        font_size=fontsize,
                        font=Path('./fonts/Montserrat-Bold.ttf'),
                        size=(text_area_width, text_area_height),
                        method='caption',
                        duration=end_time - start_time,
                    ).with_start(start_time).with_end(end_time)
                    if word_clip.size[0] <= text_area_width:
                        break  # Stop reducing size if it fits
                else:
                    word_clip = TextClip(
                        text=word[:max_font_size // 10] + "-..",
                        text_align='center',
                        color='white',
                        font_size=50,
                        font=Path('./fonts/Montserrat-Bold.ttf'),
                        size=(text_area_width, text_area_height),
                        method='caption',
                        duration=end_time - start_time,
                    ).with_start(start_time).with_end(end_time)

                text_clips.append(word_clip)
                current_time = end_time

            # Combine all word clips into a single CompositeVideoClip
            animated_text = CompositeVideoClip(text_clips).with_position(('center', 'center'))

            # Combine the video and animated text
            final_video = CompositeVideoClip([video_clip, animated_text]).with_audio(final_audio)

            # Write the final video to file
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                preset="veryslow",
                bitrate="8000k"
            )

            return output_path

        except Exception as e:
            print(f"Error creating video: {e}")
            return None

    def convert_audio_to_wav(self, audio_path):
        """Converts any audio file to 16-bit PCM WAV format (mono) for Vosk."""
        sound = AudioSegment.from_file(audio_path)
        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        wav_path = audio_path.rsplit(".", 1)[0] + "_converted.wav"
        sound.export(wav_path, format="wav")
        self.wait_for_file(wav_path)
        return wav_path


if __name__ == "__main__":
    FACTS_FILE = "facts.txt"
    VIDEO_API_KEY = os.getenv('VIDEO_API_KEY')
    MUSIC_FOLDER = "./music"

    generator = FactVideoGenerator(FACTS_FILE, VIDEO_API_KEY, MUSIC_FOLDER)

    for fact in generator.facts:
        try:
            fact_text = f'Did you know that? {fact} Follow us for more and share these fascinating facts with your family and friends!'
            print(f"Processing fact: {fact_text}")

            hashtags = generator.generate_hashtags(fact_text)
            relevant_word = generator.get_relevant_word(fact_text)
            video_path = generator.get_random_video(relevant_word)
            voice_path = synthesize_voice(fact_text)
            music_path = generator.get_random_music()

            final_video_path = generator.create_video(fact_text, video_path, voice_path, music_path)

            if Path(final_video_path).exists():
                print(f"Video successfully created: {final_video_path}")
            else:
                raise Exception("Video creation failed.")
        except Exception as e:
            print(f"Error processing fact: {e}")
