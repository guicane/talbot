# Talbot - Telegram Bot by @guicane

This is a **Telegram bot** designed for group chats, offering multiple interactive and fun functionalities. The bot is built using **Python** and leverages various APIs to provide jokes, movie information, weather updates, insults, and more.

## 🚀 Features

### 🎭 **Dad Jokes**

- **Command:** `/dadjokes [optional joke]`
- Retrieves a **random dad joke** from [icanhazdadjoke.com](https://icanhazdadjoke.com/api) if no joke is provided.
- If the user **provides a joke**, it will be displayed instead of fetching one.
- Follows up with an **interactive poll** for users to rate the joke.

### 🎬 **Movie Information (IMDb & Rotten Tomatoes)**

- **Command:** `/imdb <movie/series name>`
- Fetches a list of **matching movies and series** from **OMDB API**.
- If only **one result** is returned, it automatically displays **IMDb & Rotten Tomatoes ratings**, synopsis, and a link to IMDb.
- If multiple results, **users select the correct movie/series** via interactive buttons.

### ☁ **Weather Updates**

- **Command:** `/weather <location>`
- Retrieves the **current weather** for a given city or **UK postcode** using **Open-Meteo API**.
- Special support for **Saltney**, fetching data from `http://wx.ja91.uk/` weather station.
- Special support for **Amazingstoke**, fetching data from Basingstoke.

### 🔥 **Insult Generator**

- **Command:** `/insult @username`
- Uses **Evil Insult API** to generate a **random insult** for the mentioned user.

### **BRL/USD Graph**
- **Command:** `/brl_usd` 
- creates a 30 day BRL/USD graph

### **BTC/USD Graph**
- **Command:** `/btc_usd` 
- creates a 30 day BTC/USD graph

### **Currency Convertion**

- **Command:** `/convert 100 USD EUR` 
- Converts 100 US dollars to euros

- **Command:** `/currencies` 
- Shows a list of popular currency codes that can be used

- **Command:** `/brl`
- Return the current exchange rate for GBPBRL.

### **Upcoming features**

#### **Custom Currency Convertion Rates**

- Allows users to specify which currency pair they want to get rates for.

#### **AI-Powered Message Summarization**

- Every hour, the bot collects messages and generates a **summary** of the past hour’s discussion.
- Uses **Anthropic Claude AI** to create concise summaries.

---

## 🔧 Setup & Deployment

### **1️⃣ Install Dependencies**

Ensure you have **Python 3.11+** installed. Install dependencies:

```sh
pip install -r requirements.txt
```

### **2️⃣ Environment Variables**

Create a `.env` file and configure your API keys:

```ini
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
OMDB_API_KEY=your-omdb-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### **3️⃣ Run the Bot Locally**

Start the bot manually:

```sh
bash src/entry.sh
```

### **4️⃣ Run the Bot Using Docker**

If deploying via Docker, build and run the container:

```sh
docker-compose build
docker-compose up -d
```

### **5️⃣ Deploy to Docker Hub (Optional)**

- This is currently being done via GitHub Actions and builds a multi-architecture image for amd64 and arm64.

- If you wish to manually push the container to **Docker Hub**:

```sh
docker login
docker build -t your-dockerhub-user/telegram-bot:latest .
docker push your-dockerhub-user/telegram-bot:latest
```

## 📜 License

This project is open-source and available under the **MIT License**.

## 🤝 Contributing

If you’d like to improve the bot, feel free to fork the repository and submit a pull request.

---

💬 **Created for Telegram groups to enhance conversations with AI, fun, and utilities!** 🚀
