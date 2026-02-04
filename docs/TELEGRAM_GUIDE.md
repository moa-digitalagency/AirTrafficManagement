# Guide du Bot Telegram ATM-RDC

Le Bot Telegram est une composante essentielle du système ATM-RDC, permettant aux contrôleurs et gestionnaires de recevoir des notifications en temps réel concernant les mouvements aériens et la facturation.

## 1. Installation et Configuration

Pour configurer le bot, assurez-vous que les variables d'environnement suivantes sont définies dans `.env` (voir `ENV_VARIABLES.md`) :

*   `TELEGRAM_BOT_ENABLE=true`
*   `TELEGRAM_BOT_TOKEN=<votre_token>`
*   `TELEGRAM_ADMIN_CHANNEL_ID=<id_canal_admin>` (Optionnel)

### Comment créer le bot ?
1.  Contactez **@BotFather** sur Telegram.
2.  Utilisez `/newbot` pour créer un nouveau bot.
3.  Récupérez le **Token API**.

## 2. Parcours Utilisateur

Le système utilise un modèle de **sécurité par approbation manuelle** (Waiting Room).

### Étape 1 : Demande d'Accès
*   L'utilisateur cherche le bot sur Telegram et clique sur **Démarrer** (ou tape `/start`).
*   Le bot répond : *"Votre demande est en attente. Pour finaliser l'activation, communiquez le code suivant à votre administrateur..."*.
*   Un code à 6 chiffres (OTP) est affiché.

### Étape 2 : Validation Administrateur
*   L'administrateur se connecte au **Tableau de Bord Admin** de l'application Web.
*   Il accède à la section **Gestion Telegram** (`/admin/telegram`).
*   Il voit la demande en statut **PENDING** avec le nom d'utilisateur et le code.
*   Si le code correspond à celui fourni par l'utilisateur (par téléphone/email), l'admin clique sur **Approuver**.

### Étape 3 : Activation
*   Dès l'approbation, le bot envoie un message de bienvenue à l'utilisateur : *"✅ Bienvenue... Tapez /settings pour configurer..."*.
*   Le statut passe à **APPROVED**.

## 3. Commandes Disponibles

| Commande | Description |
|----------|-------------|
| `/start` | Lance le bot et initie la demande d'accès (ou affiche le statut actuel). |
| `/settings` | Ouvre le menu interactif pour activer/désactiver les types de notifications. |

## 4. Types de Notifications

Les utilisateurs peuvent s'abonner aux événements suivants (via `/settings` ou configuré par l'admin) :

*   **🛬 Entrées Zone (`notify_entry`)** : Avertit lorsqu'un avion entre dans l'espace aérien RDC.
*   **🛫 Sorties Zone (`notify_exit`)** : Avertit lorsqu'un vol quitte la zone (inclus distance et durée).
*   **💰 Facturation (`notify_billing`)** : Notifie la génération d'une nouvelle facture (Survol ou Atterrissage).
*   **🚨 Alertes (`notify_alerts`)** : Urgences (Squawk 7700), météo critique, etc.
*   **📊 Rapport 24h (`notify_daily_report`)** : Résumé quotidien (à implémenter).

## 5. Gestion Administrative

L'interface Web permet aux administrateurs de :
*   Voir la liste des abonnés et leur statut.
*   **Approuver** ou **Rejeter** les nouvelles demandes.
*   **Révoquer** l'accès d'un utilisateur existant (le bot cessera d'envoyer des messages).
*   **Configurer** les préférences de notification d'un utilisateur à sa place.
*   **Tester** la connexion avec le bot.
