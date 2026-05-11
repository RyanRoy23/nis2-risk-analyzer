# Compte de service Azure — Sécurisation et bonnes pratiques

Ce document décrit la configuration sécurisée du compte de service Azure utilisé par le bridge CloudSec Audit Toolkit pour interroger l'API Microsoft Graph et collecter les données de conformité technique.

## Contexte

Le bridge CloudSec interroge l'API Microsoft Graph pour collecter automatiquement des informations sur la posture de sécurité du tenant Azure / Entra ID : MFA déployé, comptes administrateurs, politiques d'accès conditionnel, alertes de sécurité, etc. Ces informations alimentent les questions techniques du référentiel NIS 2 (20 contrôles techniques sur les 35 questions au total).

Pour appeler l'API Microsoft Graph, l'outil utilise un **compte de service** (application registration dans Azure AD / Entra ID) avec un client secret. Ce compte devient mécaniquement un actif sensible : s'il est compromis, un attaquant obtient un accès en lecture aux informations de sécurité du tenant.

## Risque associé

Cette préoccupation a été soulevée par un RSSI senior consulté pendant le développement de l'outil :

> "Vous décidez de prendre un compte de service de votre solution. Ce compte de service deviendra une cible de haute valeur. Comment est-il sécurisé ? Comment garantissez-vous qu'il n'est jamais utilisé en dehors de son périmètre prévu ?"

La présente documentation répond à cette critique.

## Principes de sécurisation

### 1. Permissions minimales (principle of least privilege)

Le compte de service ne doit **jamais** disposer de permissions d'écriture sur le tenant. Les rôles strictement nécessaires sont :

- **Global Reader** : lecture des configurations Azure AD / Entra ID, des utilisateurs, des groupes, des policies
- **Security Reader** : lecture des alertes de sécurité, des incidents, des scores de sécurité Microsoft Defender

Permissions API Microsoft Graph recommandées (toutes en lecture seule) :

- `Application.Read.All`
- `Directory.Read.All`
- `Policy.Read.All`
- `SecurityEvents.Read.All`
- `IdentityRiskEvent.Read.All`
- `User.Read.All`

**À ne jamais accorder** :
- Toute permission `.ReadWrite.*` ou `.Write.*`
- `Directory.AccessAsUser.All` (impersonation)
- Les rôles `Global Administrator`, `Privileged Role Administrator`, `User Administrator`

### 2. Création du compte de service

Dans le portail Azure :

1. **Azure Active Directory** → **App registrations** → **New registration**
2. Nom : `NIS2-RiskAnalyzer-ReadOnly` (ou équivalent explicite)
3. Supported account types : Single tenant
4. Redirect URI : aucun (application non-interactive)
5. Une fois créée, noter l'Application (client) ID et le Directory (tenant) ID
6. **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**
7. Sélectionner les permissions listées ci-dessus
8. **Grant admin consent** pour le tenant
9. **Certificates & secrets** → générer un client secret avec durée de vie courte (6 mois maximum)
10. Copier la valeur du secret immédiatement (elle ne sera plus visible ensuite)

### 3. Durcissement par Conditional Access

Créer une policy d'accès conditionnel ciblant spécifiquement ce compte de service :

- **Users** : l'application `NIS2-RiskAnalyzer-ReadOnly`
- **Conditions — Locations** : restreindre aux plages IP de l'environnement où l'outil tourne (machine du consultant, serveur dédié)
- **Conditions — Client apps** : limiter aux clients modernes uniquement
- **Grant** : require approved application
- **Session** : sign-in frequency restreinte

Cette restriction garantit que même si le client secret est compromis, il ne peut pas être utilisé depuis n'importe quelle adresse IP.

### 4. Gestion du secret

Le client secret **ne doit jamais** être :

- Commité dans un repository Git (même privé)
- Stocké en clair dans un fichier `.env` non chiffré
- Transmis par email ou messagerie non sécurisée
- Partagé entre plusieurs utilisateurs

Bonnes pratiques recommandées :

- **Stockage local** : utiliser une variable d'environnement (`AZURE_CLIENT_SECRET`) chargée depuis un fichier `.env` ajouté au `.gitignore`
- **Stockage en équipe** : utiliser un coffre-fort (1Password, Bitwarden, HashiCorp Vault, Azure Key Vault)
- **Rotation** : remplacer le secret tous les 3 à 6 mois maximum
- **Révocation immédiate** : en cas de suspicion de compromission, révoquer le secret dans Azure AD avant toute autre action

### 5. Audit et surveillance

Le compte de service doit faire l'objet d'une surveillance active :

- **Azure AD sign-in logs** : alerte si connexion depuis une IP non listée dans le Conditional Access
- **Audit logs** : vérifier mensuellement les appels API effectués par le compte
- **Microsoft Defender for Cloud Apps** : règle de détection si volume d'appels anormal
- **Revue trimestrielle** : auditer les permissions du compte et confirmer qu'aucune permission excessive n'a été ajoutée

### 6. Cycle de vie

Le compte de service doit être :

- **Documenté** : propriétaire identifié, périmètre d'usage défini, durée de vie prévue
- **Revu annuellement** : vérifier qu'il est toujours nécessaire, ses permissions encore pertinentes
- **Désactivé immédiatement** si l'outil n'est plus utilisé : ne pas laisser de comptes orphelins

## Mode local sans Azure

Si l'organisation ne souhaite pas créer de compte de service Azure ou n'utilise pas Microsoft 365, l'outil reste pleinement fonctionnel en mode **questionnaire intégral** (sans bridge CloudSec). Toutes les questions sont alors remplies de manière déclarative par l'utilisateur, et le rapport indique explicitement que la couche "prouvé" est vide via la section "Périmètre d'évaluation".

C'est un choix de transparence : un outil sans audit technique est plus honnête qu'un outil qui simule un audit qu'il n'a pas réellement effectué.

## Références

- [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [Azure AD Conditional Access](https://learn.microsoft.com/en-us/entra/identity/conditional-access/)
- [CIS Microsoft 365 Foundations Benchmark](https://www.cisecurity.org/benchmark/microsoft_365)
- [ANSSI — Recommandations de sécurité relatives à Active Directory](https://www.cyber.gouv.fr/publications/recommandations-de-securite-relatives-active-directory)

---

*Document maintenu par Ryan Roy TASSEH TAGNY — Mis à jour : 11 mai 2026*