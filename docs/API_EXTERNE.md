# Documentation de l'API Externe ATM-RDC

## 1. Introduction

L'API ATM-RDC Data ("External API") permet aux partenaires agréés (compagnies aériennes, autorités de l'aviation civile, prestataires de services) d'accéder de manière sécurisée et programmatique aux données de surveillance aérienne et de facturation de la RDC.

Cette interface RESTful fournit des informations en temps réel sur les vols, les alertes de sécurité et les données financières associées.

**Note de Sécurité :** L'accès à cette API est strictement réservé aux partenaires disposant d'un contrat de service actif et d'une clé d'API valide.

## 2. Authentification

L'authentification se fait via le header HTTP `X-API-KEY`. Chaque requête doit inclure ce header avec une clé d'API valide fournie par l'administration ATM-RDC.

### Headers Requis

| Header | Description |
|--------|-------------|
| `X-API-KEY` | Clé d'API unique (32+ caractères alphanumériques). |

### Réponses d'Erreur d'Authentification

*   **401 Unauthorized** : Le header `X-API-KEY` est manquant.
*   **403 Forbidden** : La clé fournie est invalide, inactive ou révoquée.

## 3. Rate Limiting

Pour garantir la stabilité du service, l'API impose une limite de requêtes par minute (quota) associée à chaque clé d'API.

*   **Quota** : Défini par contrat (ex: 60 requêtes/minute).
*   **Dépassement** : Si le quota est atteint, l'API renvoie un code HTTP **429 Too Many Requests**.

### Headers de Réponse

L'API inclut des headers standards pour indiquer l'état actuel du quota :

*   `X-RateLimit-Limit` : Le nombre maximum de requêtes autorisées par minute.
*   `X-RateLimit-Remaining` : Le nombre de requêtes restantes dans la fenêtre actuelle.

### Exemple de réponse (Erreur 429)

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit of 60 requests/minute exceeded"
}
```

## 4. Référence des Endpoints

Tous les endpoints sont préfixés par `/api/v1/external`.

### 4.1 Surveillance des Vols

Récupère la liste des vols surveillés (en vol, en approche ou atterris) selon des critères.

*   **Méthode** : `GET`
*   **URL** : `/api/v1/external/surveillance/flights`

#### Paramètres de Requête (Query Params)

| Paramètre | Type | Obligatoire | Description |
|-----------|------|-------------|-------------|
| `active` | string | Non | Mettre à `true` pour filtrer uniquement les vols actifs (en vol, approche). |
| `date` | string | Non | Filtrer par date de vol (Format: `YYYY-MM-DD`). |

#### Exemple de Réponse JSON

```json
{
  "count": 1,
  "data": [
    {
      "aircraft": "9Q-CBA",
      "alerts_count": 0,
      "callsign": "CAA123",
      "distance_km": 450.25,
      "duration_minutes": 45.5,
      "ground_time_minutes": 0,
      "operator": "Compagnie Africaine d'Aviation",
      "position_entry": "-4.325, 15.308",
      "position_exit": "-11.660, 27.479",
      "status": "in_flight"
    }
  ]
}
```

#### Champs Clés

*   `callsign` : Indicatif du vol.
*   `distance_km` : Distance parcourue dans l'espace aérien RDC.
*   `position_entry` / `position_exit` : Coordonnées (Lat, Lon) d'entrée et de sortie de l'espace aérien ou point d'atterrissage.
*   `status` : Statut du vol (`scheduled`, `in_flight`, `approaching`, `landed`).

---

### 4.2 Alertes de Surveillance

Récupère les dernières alertes de sécurité ou opérationnelles générées par le système.

*   **Méthode** : `GET`
*   **URL** : `/api/v1/external/surveillance/alerts`

#### Paramètres de Requête
Aucun.

#### Exemple de Réponse JSON

```json
{
  "data": [
    {
      "alert_type": "flight_emergency",
      "category": "safety",
      "created_at": "2023-10-27T10:30:00",
      "flight_id": 12345,
      "id": 1,
      "is_acknowledged": false,
      "is_active": true,
      "message": "Squawk 7700 detected for flight CAA123",
      "priority": 10,
      "severity": "critical",
      "source": "radar_system",
      "title": "Emergency Squawk Detected"
    }
  ]
}
```

---

### 4.3 Résumé de Facturation

Fournit un aperçu financier global (facturé vs payé) pour l'entité associée à la clé API (ou global selon les droits).

*   **Méthode** : `GET`
*   **URL** : `/api/v1/external/billing/summary`

#### Paramètres de Requête
Aucun.

#### Exemple de Réponse JSON

```json
{
  "currency": "USD",
  "generated_at": "2023-10-27T12:00:00",
  "outstanding": 1500.00,
  "total_invoiced": 50000.00,
  "total_paid": 48500.00
}
```

---

### 4.4 Grille Tarifaire

Récupère la configuration actuelle des tarifs (redevances survol, atterrissage, etc.).

*   **Méthode** : `GET`
*   **URL** : `/api/v1/external/billing/pricing`

#### Paramètres de Requête
Aucun.

#### Exemple de Réponse JSON

```json
{
  "data": [
    {
      "category": "overflight",
      "code": "OVF_INTL",
      "currency": "USD",
      "description": "Redevance de survol international",
      "effective_date": "2023-01-01",
      "id": 1,
      "is_active": true,
      "is_percentage": false,
      "name": "Survol International",
      "unit": "per_km",
      "value": 0.75
    }
  ]
}
```

## 5. Codes d'Erreur

L'API utilise les codes de statut HTTP standards pour indiquer le succès ou l'échec d'une requête.

| Code | Signification | Description |
|------|---------------|-------------|
| **200** | OK | La requête a été traitée avec succès. |
| **400** | Bad Request | La requête est mal formée (ex: format de date invalide). |
| **401** | Unauthorized | Authentification échouée (Clé API manquante). |
| **403** | Forbidden | Accès refusé (Clé API invalide ou inactive). |
| **429** | Too Many Requests | Limite de requêtes (rate limit) dépassée. |
| **500** | Internal Server Error | Erreur interne du serveur. |
