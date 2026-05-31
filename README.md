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

-----------------------------------------------------

# Warframe Market Price Checker (Italiano)

Un tool in Python con interfaccia grafica (GUI) per controllare rapidamente i prezzi degli oggetti su [Warframe Market](https://warframe.market/).

## Come funziona

Lo script si collega alle API v2 di Warframe Market per scaricare e mostrare i prezzi aggiornati in tempo reale, aiutandoti a tenere traccia del valore dei tuoi oggetti (Prime, Mod, Reliquie, ecc.). Utilizza una cache locale per ridurre il numero di richieste ed essere più rapido, ed è in grado di mostrare un'anteprima delle immagini degli oggetti e le relative descrizioni.

## Requisiti

Assicurati di avere **Python** installato sul tuo sistema, dopodiché installa le librerie necessarie tramite `pip`:

```bash
pip install -r requirements.txt
```

## Configurazione Iniziale

Per interagire con le API di Warframe Market senza restrizioni, lo script necessita dei tuoi cookie di sessione.

1. Esegui l'accesso al tuo account su [warframe.market](https://warframe.market) tramite il browser.
2. Apri gli strumenti per sviluppatori del browser (F12) -> tab "Application" o "Storage" -> "Cookies".
3. Crea un file chiamato `config.json` nella stessa cartella dello script con questa struttura, inserendo i tuoi cookie `JWT` e `cf_clearance`:

```json
{
  "auth": {
    "jwt": "IL_TUO_COOKIE_JWT_QUI",
    "cf_clearance": "IL_TUO_COOKIE_CF_CLEARANCE_QUI"
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

> **Attenzione:** I token `jwt` hanno una scadenza. Se lo script inizia a dare errori API (es. `401 Unauthorized`), significa che il token è scaduto e dovrai semplicemente riaggiornarlo nel `config.json` ripetendo i passaggi.

## Struttura dei File

- `warframe_price_checker.py`: Il file principale da avviare.
- `config.json`: File di configurazione contenente i token di accesso e le impostazioni (creato dall'utente).
- `app_cache.json`: Generato automaticamente, contiene la cache locale degli oggetti e delle descrizioni per non appesantire l'API. (Eliminalo per forzare un ricaricamento di tutti gli oggetti).
- `items.txt`: Generato e gestito dall'app per salvare la lista degli oggetti "preferiti" o tracciati.
- `img/`: Cartella creata automaticamente per salvare in cache le icone degli oggetti scaricate.

## Avvio

Per avviare l'applicazione, esegui semplicemente:

```bash
python warframe_price_checker.py
```
