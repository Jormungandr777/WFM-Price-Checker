# Warframe Market Price Checker

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
