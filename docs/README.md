# Air Traffic Management - RDC (ATM-RDC)

## Système Intégré de Gestion et de Facturation du Trafic Aérien

### Vue d'ensemble

Ce système est une solution web centralisée destinée à la surveillance en temps réel, 
à l'historisation forensique et à la facturation automatisée de tout mouvement aérien 
interagissant avec l'espace aérien de la République Démocratique du Congo.

### Modules Principaux

1. **Radar de Surveillance Temps Réel (Live Monitor)**
   - Cartographie multi-couches
   - Suivi des aéronefs en temps réel
   - Alertes et notifications

2. **Radar de Survol & Geofencing (Overflight Tracker)**
   - Détection automatique d'entrée/sortie
   - Calcul de trajectoire et distance
   - Historique des survols

3. **Radar Aéroportuaire (ATM Terminal)**
   - Gestion des atterrissages
   - Suivi du stationnement
   - File d'attente des arrivées

4. **Système de Facturation Automatisée**
   - Génération de factures PDF
   - Gestion des tarifs
   - Suivi des paiements

5. **Analyse de Données & Statistiques (BI)**
   - Tableaux de bord dynamiques
   - Exportation avancée
   - Rapports personnalisés

6. **Administration & Audit**
   - Gestion des utilisateurs (RBAC)
   - Journalisation forensique
   - Configuration système

### Structure du Projet

```
atm-rdc/
├── algorithms/      # Algorithmes de calcul (geofencing, etc.)
├── config/          # Configuration de l'application
├── docs/            # Documentation
├── lang/            # Fichiers de traduction
├── models/          # Modèles de données SQLAlchemy
├── routes/          # Routes/Blueprints Flask
├── scripts/         # Scripts utilitaires
├── security/        # Modules de sécurité et audit
├── services/        # Services métier
├── statics/         # Fichiers statiques (CSS, JS, images)
├── templates/       # Templates Jinja2
├── utils/           # Fonctions utilitaires
├── app.py           # Application principale
└── init_db.py       # Script d'initialisation de la base de données
```

### Rôles Utilisateurs

- **SuperAdmin**: Accès complet au système
- **Supervisor**: Vue globale et gestion des incidents
- **Controller**: Surveillance opérationnelle
- **Billing**: Gestion des factures
- **Auditor**: Consultation des logs
- **Observer**: Vue lecture seule

### Comptes par défaut

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| admin | password123 | SuperAdmin |
| supervisor_kin | password123 | Supervisor |
| controller1 | password123 | Controller |
| billing | password123 | Billing |
| auditor | password123 | Auditor |

### Technologies

- **Backend**: Python 3.11+ / Flask
- **Base de données**: PostgreSQL
- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **Cartographie**: Leaflet.js
- **WebSocket**: Flask-SocketIO
