# Fact Bot - Generate Instagram Reel Facts

![example__did_you_know_that_python_is_an_awesome-ezgif.com-video-to-gif-converter.gif](images/example__did_you_know_that_python_is_an_awesome-ezgif.com-video-to-gif-converter.gif)

## Setup:
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
sudo apt-get install unzip
unzip vosk-model-en-us-0.22.zip
mv vosk-model-en-us-0.22/ vosk-model/

mv .env.example .env
vim .env
```

- Create a Pexels API Account at: https://www.pexels.com/api/  
- Insert your Pexels API Key into the `.env` file:
```dotenv
VIDEO_API_KEY=# Replace with API Key from https://www.pexels.com/api/
```


## How to use it:

### Requirements:
- Music folder (`music/`)  
Example:
![img.png](images/img.png)
- Fact file (`facts.txt`)  
Example:
```text
Python is an awesome programming language!
Using this bot makes a lot of fun!
```

### Generate a fact Reel:
```shell
python3 bot.py
```
