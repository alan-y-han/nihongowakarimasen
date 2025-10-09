# nihongo wakarimasen

High quality translator for foreign language videos and audio, using Whisper and LLM translation. Geared especially towards Japanese to English translation for youtube videos, TV shows and radio.

Uses OpenAI APIs to perform speech to text transcription, and text to text translation.

## Installation

### OpenAI API setup

First you'll need to set up an OpenAPI account:
1. Create an OpenAI account - https://platform.openai.com/
2. Fund the account with credits (a few dollars is enough)
3. Create an API key, and add it to your local computer
   - Follow the instructions here ("Create and export an API key") - https://platform.openai.com/docs/quickstart

### Python setup

1. Make sure you have python installed
2. Install the required dependencies in requirements.txt

## Usage

1. Specify which video to translate in main.py and run (this will change to a proper CLI interface)
2. This will generate a .srt subtitle file, which you can open in your video player (e.g. VLC)

## How it works

Subtitle generation is split into 2 stages:
1. Perform speech to text, currently done using whisper. This can be locally or using OpenAI's API
2. Text to text translation, currently using ChatGPT thanks to its high quality translations, wide knowledge base and ability to take user-provided context to improve translation further. Larger reasoning models (e.g. gpt-5) are also able to fix some text transcript errors, given the right prompting.

### Saving money
For whisper transcription, consider:
- If you have a powerful GPU, running locally will reduce costs but produces worse transcriptions than OpenAI's whisper

For LLM translations, consider:
- Flex mode (default: off) - this can introduce higher latency and timeouts but is 2x cheaper
- LLM model (default: gpt-5) - consider using gpt-5-mini (5x cheaper) or gpt-5-nano (25x cheaper) at cost of increased translation mistakes, less natural sounding text and losing the ability to fix transcript errors
- Reasoning effort (default: low) - consider changing to "minimal" to reduce output token usage (the highest cost driver). However any setting below "low" seems to hinder the LLM's ability to fix transcript mistakes.

## Example output

- ["Mizuki Nana's Smile Gang" - 1226th Meeting](https://youtu.be/n8Vh4KrpgHU)