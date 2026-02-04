# Architecture du Système ATM-RDC

Ce document décrit l'architecture technique de la plateforme de surveillance et de facturation ATM-RDC.

## Vue d'Ensemble

Le système est une application Web monolithique modulaire construite en Python (Flask), conçue pour surveiller l'espace aérien de la RDC, détecter les survols et atterrissages, et générer automatiquement la facturation correspondante.

## Composants Principaux

### 1. Backend (Flask)
*   **Framework** : Flask (Python 3.12+).
*   **ORM** : SQLAlchemy avec GeoAlchemy2 pour la gestion spatiale.
*   **Authentification** : Flask-Login (Sessions sécurisées).
*   **Structure** :
    *   `models/` : Définitions de la base de données (User, Flight, Invoice...).
    *   `routes/` : Contrôleurs Web divisés par Blueprint (auth, admin, radar, invoices...).
    *   `services/` : Logique métier (FlightTracker, InvoiceGenerator, TelegramService...).
    *   `security/` : Middlewares de sécurité, audit et authentification API.

### 2. Base de Données (PostgreSQL + PostGIS)
*   **Rôle** : Stockage persistant et calculs géographiques.
*   **PostGIS** : Extension essentielle pour :
    *   Définir la frontière de la RDC (Polygone).
    *   Détecter l'inclusion de points (`ST_Contains`).
    *   Calculer les distances de vol réelles dans l'espace aérien.

### 3. Tâches Asynchrones (Celery + Redis)
*   **Broker** : Redis.
*   **Usage** :
    *   Récupération périodique des données de vol (AviationStack/ADSBExchange).
    *   Envoi d'emails (SMTP).
    *   Calculs lourds de trajectoires.

### 4. Frontend
*   **Moteur de Template** : Jinja2 (Rendu côté serveur).
*   **Styles** : TailwindCSS (Utilitaire).
*   **Cartographie** : Leaflet.js (Radar et Admin Map).
*   **Temps Réel** : Polling JS (API `/radar/api/*`).

## Flux de Données (Data Flow)

1.  **Ingestion** :
    *   `FlightTracker` interroge l'API Externe toutes les X secondes.
    *   Les positions sont normalisées et comparées à la géométrie de la RDC (`is_point_in_rdc`).

2.  **Traitement (Surveillance)** :
    *   **Entrée** : Si un avion entre dans le polygone -> Création `Overflight` (Session). Notification Telegram.
    *   **Sortie** : Si un avion sort -> Clôture `Overflight`. Calcul distance/durée.
    *   **Atterrissage** : Détection via proximité aéroport + altitude/vitesse basses -> Création `Landing`.

3.  **Facturation (Billing)** :
    *   À la clôture d'un événement (Sortie ou Parking fini), `InvoiceGenerator` est déclenché.
    *   Calcul du montant selon `TariffConfig` (Poids avion, Distance, Jour/Nuit).
    *   Génération PDF (ReportLab) avec QR Code.
    *   Notification Telegram/Email.

4.  **Distribution** :
    *   Les factures sont accessibles via le Portail Web.
    *   API Externe (`/api/v1/external`) pour l'intégration tiers.

## Sécurité

*   **API Externe** : Authentification par `X-API-KEY`, Rate Limiting via Redis.
*   **Web** : CSRF Protection, Secure Cookies, HSTS.
*   **Audit** : Tous les actes sensibles (Facturation, Login, Config) sont enregistrés dans `audit_logs`.
