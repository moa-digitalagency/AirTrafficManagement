# Guide de Déploiement

## Sécurité au Démarrage

L'application intègre une validation stricte des variables d'environnement au démarrage pour garantir la sécurité. Si ces conditions ne sont pas remplies, l'application refusera de démarrer.

### Variables Requises

1.  **DATABASE_URL**
    *   **Requis :** Oui, dans tous les environnements.
    *   **Production :** Doit commencer par `postgres://` ou `postgresql://`. SQLite n'est pas autorisé en production (`NODE_ENV=production`).

2.  **SUPER_ADMIN_EMAIL**
    *   **Requis :** Oui.
    *   **Format :** Doit être une adresse email valide.

3.  **SUPER_ADMIN_PASSWORD**
    *   **Requis :** Oui.
    *   **Règles de complexité :**
        *   Minimum 12 caractères.
        *   Au moins 1 lettre majuscule.
        *   Au moins 1 lettre minuscule.
        *   Au moins 1 chiffre.
        *   Au moins 1 caractère spécial (ex: `!@#$%^&*`...).
        *   Ne doit pas être dans la liste des mots de passe faibles (ex: `admin`, `password`, `123456`).

### Échec du Déploiement

Si l'une de ces règles n'est pas respectée, le processus de démarrage s'arrêtera immédiatement avec un message d'erreur critique (CRITICAL log). Cela entraînera l'échec des pipelines CI/CD ou du déploiement sur le serveur.
