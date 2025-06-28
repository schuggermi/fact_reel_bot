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

## Requirements:  
Music folder (`music/`)

![img.png](images/img.png)  

Fact file (`facts.txt`)
```text
Python is an awesome programming language!
Using this bot makes a lot of fun!
```

### How to use it:
```shell
python3 bot.py
```

### Note:
If the program ends with the word `Killed` then your free memory space is too low.
To fix this, consider unsing the smaller vosk-model:  
```shell
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15/ vosk-model/
```