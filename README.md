# Warframe Market Price Checker

A Python tool with a graphical user interface (GUI) to quickly check item prices on [Warframe Market](https://warframe.market/).

## How it works

The script connects to the Warframe Market v2 APIs to download and display updated prices in real-time, helping you track the value of your items (Prime parts, Mods, Relics, etc.). It uses a local cache to reduce the number of requests and increase speed, and it is capable of showing a preview of item images and their descriptions.

## Requirements

Make sure you have **Python** installed on your system, then install the necessary libraries via `pip`:

```bash
pip install -r requirements.txt
```

## Initial Configuration

To interact with the Warframe Market API without restrictions, the script requires your session cookies.

1. Log in to your account on [warframe.market](https://warframe.market) via your browser.
2. Open the browser's developer tools (F12) -> "Application" or "Storage" tab -> "Cookies".
3. Create a file named `config.json` in the same folder as the script with this structure, inserting your `JWT` and `cf_clearance` cookies:

```json
{
  "auth": {
    "jwt": "YOUR_JWT_COOKIE_HERE",
    "cf_clearance": "YOUR_CF_CLEARANCE_COOKIE_HERE"
  },
  "launches": 0,
  "settings": {
    "refresh_every": 10,
    "fetch_delay_min": 1,
    "fetch_delay_max": 3,
    "top_sellers": 5
  }
}
```

> **Warning:** `jwt` tokens have an expiration date. If the script starts giving API errors (e.g., `401 Unauthorized`), it means the token has expired and you will simply need to update it in `config.json` by repeating the steps.

## File Structure

- `warframe_price_checker.py`: The main file to run.
- `config.json`: Configuration file containing access tokens and settings (created by the user).
- `app_cache.json`: Automatically generated, contains the local cache of items and descriptions to avoid overloading the API. (Delete it to force a reload of all items).
- `items.txt`: Generated and managed by the app to save the list of "favorite" or tracked items.
- `img/`: Folder created automatically to cache downloaded item icons.

## Running the App

To start the application, simply run:

```bash
python warframe_price_checker.py
```
