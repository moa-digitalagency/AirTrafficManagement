# Configuration & Variables d'Environnement

Ce document détaille les variables d'environnement nécessaires au fonctionnement de l'application ATM-RDC, ainsi que la procédure pour obtenir les clés API requises.

Toutes les variables doivent être définies dans un fichier `.env` à la racine du projet (voir `.env.example`).

---

## 1. Flask Core & Base de Données

Ces variables configurent le cœur de l'application Flask et la connexion à la base de données.

| Variable | Description | Comment obtenir / Valeur type |
|----------|-------------|-------------------------------|
| `SESSION_SECRET` | Clé secrète pour signer les cookies de session. | Générer une chaîne aléatoire longue (ex: `openssl rand -hex 32`). |
| `DATABASE_URL` | URL de connexion PostgreSQL. | Format: `postgresql://user:password@host:port/dbname`. Assurez-vous d'avoir une instance PostgreSQL avec PostGIS. |
| `WTF_CSRF_SECRET_KEY` | Clé pour la protection CSRF des formulaires. | Générer une chaîne aléatoire longue (peut être différente de `SESSION_SECRET`). |
| `DISABLE_POSTGIS` | Désactive les fonctionnalités géospatiales (PostGIS). | `1` ou `true`. Utile pour le développement local avec SQLite ou si PostGIS n'est pas disponible. |

---

## 2. API de Vols Externes (Flight Data)

Ces APIs sont utilisées pour récupérer les positions des avions en temps réel.

### AviationStack (Source Primaire)
*Utilisé pour les données de vol globales et les métadonnées.*

* **Variables :** `AVIATIONSTACK_API_KEY`, `AVIATIONSTACK_API_URL`
* **Procédure :**
    1. Créez un compte sur [aviationstack.com](https://aviationstack.com/).
    2. Accédez à votre [Dashboard](https://aviationstack.com/dashboard).
    3. Copiez votre `API Access Key`.
    4. **Note :** La version gratuite a une limite de requêtes mensuelles.

### ADSBexchange (Source Secondaire/Fallback)
*Utilisé pour une couverture haute fréquence (si abonnement actif).*

* **Variables :** `ADSBEXCHANGE_API_KEY`, `ADSBEXCHANGE_API_URL`
* **Procédure :**
    1. Visitez [ADSBexchange.com API](https://www.adsbexchange.com/data/).
    2. Suivez les instructions pour obtenir un accès (généralement via RapidAPI ou direct pour les partenaires).
    3. Si vous n'avez pas de clé, laissez la variable vide (le système utilisera AviationStack).

---

## 3. Données Météo

Utilisé pour afficher la météo sur la carte radar.

### OpenWeatherMap
* **Variables :** `OPENWEATHERMAP_API_KEY`, `OPENWEATHERMAP_API_URL`
* **Procédure :**
    1. Créez un compte sur [openweathermap.org](https://openweathermap.org/).
    2. Allez dans l'onglet [API Keys](https://home.openweathermap.org/api_keys).
    3. Générez une nouvelle clé.

### Aviation Weather (NOAA)
* **Variables :** `AVIATIONWEATHER_API_URL`
* **Procédure :**
    * Aucune clé requise pour l'accès public aux données METAR/TAF.
    * Valeur par défaut : `https://aviationweather.gov/api/data`

---

## 4. Redis & Celery

Nécessaire pour les tâches en arrière-plan (traitement des vols, notifications).

| Variable | Description | Valeur type |
|----------|-------------|-------------|
| `REDIS_URL` | URL de connexion au serveur Redis. | `redis://localhost:6379/0` (Local) ou URL fournie par votre hébergeur. |

---

## 5. Configuration Email (SMTP)

Utilisé pour l'envoi des factures et alertes critiques.

* **Variables :** `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
* **Procédure (Gmail exemple) :**
    1. Activez l'authentification à deux facteurs (2FA) sur votre compte Google.
    2. Générez un "Mot de passe d'application" (App Password) dans les paramètres de sécurité Google.
    3. Utilisez ce mot de passe pour `MAIL_PASSWORD`.
    4. Serveur : `smtp.gmail.com`, Port : `587`.

---

## 6. Configuration Telegram Bot

Permet l'envoi de notifications (entrées/sorties de zone, facturation) via Telegram.

### Création du Bot
1. Ouvrez Telegram et cherchez l'utilisateur **@BotFather**.
2. Envoyez la commande `/newbot`.
3. Suivez les instructions (nom du bot, nom d'utilisateur).
4. **Important :** BotFather vous donnera un **Token** (ex: `123456789:AbCdeFgHiJkLmNoPqRsTuVwXyZ`). C'est votre `TELEGRAM_BOT_TOKEN`.

### Configuration des Variables

| Variable | Description | Valeur / Procédure |
|----------|-------------|--------------------|
| `TELEGRAM_BOT_ENABLE` | Active ou désactive le service bot. | `true` ou `false`. |
| `TELEGRAM_BOT_TOKEN` | Token d'authentification du bot. | Voir procédure ci-dessus. |
| `TELEGRAM_ADMIN_CHANNEL_ID` | ID d'un canal pour les logs admin (optionnel). | 1. Ajoutez le bot à votre canal/groupe comme admin.<br>2. Envoyez un message dans le canal.<br>3. Transférez ce message au bot [@userinfobot](https://t.me/userinfobot) ou inspectez les mises à jour via l'API (`https://api.telegram.org/bot<TOKEN>/getUpdates`).<br>4. L'ID commence souvent par `-100`. |
