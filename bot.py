import os
import requests
import openai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
from pydub import AudioSegment
from instabot import Bot  # Or use Instagram Graph API


class FactVideoGenerator:
    def __init__(self, openai_api_key, video_api_key, music_folder):
        self.openai_api_key = openai_api_key
        self.video_api_key = video_api_key
        self.music_folder = music_folder

    def generate_fact(self):
        """Generates an interesting fact using OpenAI."""
        openai.api_key = self.openai_api_key
        prompt = "Give me an interesting and little-known fact:"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=50
        )
        return response['choices'][0]['text'].strip()

    def get_random_video(self):
        """Fetches a random video from a legal source."""
        url = "https://api.pexels.com/videos/search?query=random&per_page=1"
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
        return os.path.join(self.music_folder, music_files[0])

    @staticmethod
    def synthesize_voice(text, output_path="voice.mp3"):
        """Synthesizes text into speech using a TTS API."""
        from gtts import gTTS  # Example TTS library
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

    def create_video(self, fact_text, video_path, voice_path, music_path, output_path="final_video.mp4"):
        """Combines the video, voice, and music into a final output."""
        video_clip = VideoFileClip(video_path)
        voice_clip = AudioFileClip(voice_path)
        music_clip = AudioFileClip(music_path).subclip(0, video_clip.duration)

        # Set volumes
        voice_audio = voice_clip.volumex(1.0)  # Voice louder
        music_audio = music_clip.volumex(0.3)  # Music softer

        # Combine audio
        combined_audio = CompositeVideoClip([video_clip.set_audio(voice_audio)])
        final_audio = combined_audio.audio.set_audio(music_audio)

        # Create final video
        final_video = video_clip.set_audio(final_audio)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        return output_path

    def post_to_instagram(self, video_path, caption):
        """Posts the video to Instagram."""
        bot = Bot()
        bot.login(username="your_username", password="your_password")  # Replace with real credentials
        bot.upload_video(video_path, caption=caption)


if __name__ == "__main__":
    # Set your keys and paths
    OPENAI_API_KEY = "your_openai_api_key"
    VIDEO_API_KEY = "your_video_api_key"
    MUSIC_FOLDER = "./music"

    # Initialize the generator
    generator = FactVideoGenerator(OPENAI_API_KEY, VIDEO_API_KEY, MUSIC_FOLDER)

    try:
        fact = generator.generate_fact()
        print(f"Generated Fact: {fact}")

        video_path = generator.get_random_video()
        print(f"Downloaded Video: {video_path}")

        voice_path = generator.synthesize_voice(fact)
        print(f"Synthesized Voice: {voice_path}")

        music_path = generator.get_random_music()
        print(f"Selected Music: {music_path}")

        final_video_path = generator.create_video(fact, video_path, voice_path, music_path)
        print(f"Created Video: {final_video_path}")

        generator.post_to_instagram(final_video_path, caption=fact)
        print("Posted to Instagram!")

    except Exception as e:
        print(f"Error: {e}")
