# AnimeDownloader 🍿📥

Lights, camera, ACTION! 🎬 Ready to embark on an anime-tastic adventure with AnimeDownloader? Grab your popcorn and get ready to download your favorite anime episodes with ease! 🍿✨

## What's the Deal? 🤔

AnimeDownloader is your trusty sidekick in the world of anime. It's your one-stop-shop for fetching those animated gems from the vast internet seas. It's like a Shinkansen (bullet train) for anime episodes, only without the rails! 🚄📺

## Features 🌟

- **Anime Hunt**: Search for your favorite anime like a ninja in the night. 🦸
- **Organized Chaos**: Downloaded episodes neatly organized into folders. No more messy downloads! 📁✨
- **Quality Control**: Choose your video resolution and quality, like a true anime connoisseur. 📐👀
- **No Language Barrier**: Select your preferred language for that authentic experience. 🗣️🌍
- **Modern Web UI**: Beautiful React frontend with black and white theme (NEW! 🎨)
- **CLI & Web**: Use either the terminal interface or the web interface - your choice! 💻🌐

## How to Get Started 🚀

### Option 1: Web Interface (Recommended) 🌐

1. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend API server:**

   ```bash
   python api_server.py
   ```

3. **In a new terminal, set up and start the frontend:**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open your browser to `http://localhost:3000`** and start downloading! 🎉

See [FRONTEND_SETUP.md](./FRONTEND_SETUP.md) for detailed frontend setup instructions.

### Option 2: CLI Interface 💻

1. Clone the repository.
2. Install the required Python libraries using `pip install -r requirements.txt`.
3. Run the `main.py` script and let the anime magic begin! 🧙

### Windows Users

1. Navigate to the script directory.
2. Install the required Python libraries using `pip install -r requirements.txt`.
3. For CLI: Run `main.py`
4. For Web UI: Follow Option 1 above

## AnimePahe Magic ◕⩊◕

We've integrated AnimePahe's superpowers to fetch your episodes seamlessly. Say goodbye to buffering! 🧙‍♂️🎩

## Contribution 💪

We welcome fellow anime enthusiasts to join our crew! Pull requests are like Shuriken; they help us get things done faster! 👒⚔🏴‍☠️🌊

## License 📜

This project is licensed under the GNU License. It's as free as a Pikachu in the wild! ⚡🐭

## Disclaimer ⚠️

Remember to be a responsible anime pirate! Only download content you have the right to access. We don't want to anger the anime gods! 😇🙏

Get ready for an anime-tastic journey with AnimeDownloader! Let the downloading spree begin! 🌟📥

## Note: Updating the Base URL ⚠️

AnimePahe is known to change its base URL from time to time. If you encounter issues with the current base URL (https://animepahe.si/), here's how you can update it to ensure that AnimeDownloader continues to work seamlessly:

1. Open the `pahe.py` file in your project directory.

2. Locate the `url` variable at the beginning of the file, which contains the current AnimePahe base URL:

   `url = "https://animepahe.si/"`
   Update with the Current Url
