# APEN Agent MVP — Présentation produit

**Agent conversationnel IA pour l'accueil téléphonique 24h/24**

---

## Résumé exécutif

L'APEN Agent MVP est conçu comme un système d'accueil qui traite les appels entrants 24h/24 sans attente. Il qualifie chaque appel, prend des rendez-vous, transfère vers la bonne équipe ou crée des synthèses de rappel — le tout piloté par vos règles et connecté à votre agenda. L'intégration vocale (ex. Vapi) est en phase de test ; l'API et le tableau de bord sont prêts pour la production (intentions, rappels, calendrier).

Conforme à l'étude de faisabilité, le MVP garantit la transparence : toute la logique réside dans votre codebase et votre configuration, et non dans une boîte noire fournisseur. Vous conservez la propriété des données et pouvez auditer chaque décision.

---

## Fonctionnalités

| Capacité | Description |
|----------|-------------|
| **Accueil 24h/24** | Les appels sont pris immédiatement, à tout moment. Pas de file d'attente, pas de « veuillez patienter ». *(Intégration voix/Vapi en test.)* |
| **Prise de rendez-vous** | Les appelants peuvent réserver des créneaux. L'agent propose des horaires disponibles (9h–18h Paris, max 10 créneaux/jour) et crée l'événement dans Google Calendar automatiquement. |
| **Qualification des appels** | Détecte l'intention selon ce que dit l'appelant : rendez-vous, rappel, info, urgence, SAV, partenaire ou autre. Utilise l'IA quand `OPENAI_API_KEY` est défini, sinon mots-clés. |
| **Transferts intelligents** | Urgence → opérations. SAV → support. Partenaires → commercial. Règles configurables par intention et par site dans `config/routing_rules.yaml`. |
| **Synthèses de rappel** | Pour les demandes de rappel ou autres, l'agent collecte nom, téléphone, motif et site, et enregistre une synthèse pour rappel par l'équipe. L'IA extrait les champs de la transcription quand `OPENAI_API_KEY` est défini. |
| **Planification et e-mail** | API uniquement (pas d'UI) : `POST /planning/upload`, `GET /planning/{id}` ; `POST /email/ack`, `POST /email/send`. Nécessite SMTP pour l'envoi. |

---

## Parcours de bout en bout

```
+-- 1. APPEL ENTRANT
|   L'appelant compose -> Le fournisseur vocal (ex. Vapi) répond 24h/24
+
            |
            v
+-- 2. ACCUEIL
|   "Bonjour, vous êtes en contact avec APEN. Dites le motif..."
+
            |
            v
+-- 3. PAROLE -> TEXTE
|   L'appelant parle -> transcription (STT) -> envoyée à notre API
+
            |
            v
+-- 4. DETECTION D'INTENTION
|   L'IA (ou mots-clés) classe : rdv | rappel | info | urgence |
|   SAV | partenaire | autre
+
            |
    +--------+--------+
    v        v        v
RENDEZ-VOUS  TRANSFERT  RAPPEL
Proposer     Composer   Enregistrer :
créneaux     le bon     nom, tél,
-> Créer     numéro     motif, site
événement    (ops/support/commercial)  pour rappel
```

---

## Intentions et actions

| Intention | Action | Routage |
|-----------|--------|---------|
| **Rendez-vous** | Proposer créneaux, créer dans le calendrier | Reste avec l'agent (`in_agent`) |
| **Rappel** | Collecter synthèse (nom, tél, motif) pour rappel | Réception |
| **Info** | Fournir informations (horaires, adresse) | Reste avec l'agent (`in_agent`) |
| **Urgence** | Transférer vers opérations | Numéro opérations |
| **SAV** | Transférer vers support | Numéro support |
| **Partenaire** | Transférer vers commercial | Numéro commercial |
| **Autre** | Collecter synthèse pour rappel (non classé) | Réception |

---

## Tableau de bord (interface web)

Le MVP inclut un tableau de bord web pour gérer les appels, rappels et rendez-vous.

### 1. Tests intention et audio

- **Texte :** Saisir une phrase (« Je voudrais un rendez-vous pour récupérer ma tenue ») → voir intention, action, routage.
- **Audio :** Envoyer un enregistrement → transcription (Whisper) → même pipeline. Utile pour tester la parole réelle.

### 2. Appel simulé

- Saisir ce que l'appelant a dit (ou envoyer un enregistrement).
- Numéro de l'appelant (optionnel).
- Cliquer sur **Simuler l'appel** → exécute le flux complet : intention → synthèse de rappel ou rendez-vous. Si l'intention est **rendez-vous**, le système réserve automatiquement le premier créneau disponible le lendemain et crée l'événement dans le calendrier. L'appel apparaît dans **Appels** avec transcription et résultat.

### 3. Appels en direct (Vapi)

- Les vrais appels utilisent l'API Vapi : accueil, qualification, réservation, transfert ou rappel. Numéro de test affiché dans le tableau de bord (ex. +1 661 480 9377).
- *Vapi est actuellement en phase de test ; les appels en direct sont pour validation et démos.*

### 4. Liste des appels

- Appels récents (tests simulés et appels Vapi) : transcription, intention, action, résultat, importance, planification.
- Voir quels appels ont abouti à un rendez-vous ou un rappel.

### 5. Rappels

- Liste des demandes en attente de rappel.
- Filtrer par statut : En attente | Rappelé | Clôturé.
- Pour chaque : nom, téléphone, motif, site, urgence.
- **Ajouter au calendrier (IA) :** Un clic → l'IA propose titre et description → crée un événement pour le premier créneau libre dans les 8 prochains jours.
- Mettre à jour le statut : Rappelé, Clôturer.

### 6. Calendrier

- **Événements à venir :** 14 prochains jours (à partir d'aujourd'hui heure Paris), avec liens pour ouvrir dans Google Calendar.
- **Créneaux disponibles :** Choisir une date → charger jusqu'à 10 créneaux (9h–18h Paris, intervalles de 30 min, hors créneaux occupés).
- **Créer un rendez-vous :** Formulaire manuel pour début, fin, objet, description, e-mail du participant (optionnel).

---

## Automatisation IA

Nécessite `OPENAI_API_KEY` dans l'environnement.

- **Détection d'intention :** IA (gpt-4o-mini) en priorité quand la clé est définie, sinon mots-clés — plus précis pour les formulations variées.
- **Synthèse de rappel :** L'IA extrait `caller_name`, `reason`, `urgency`, `site` de la transcription pour les nouvelles synthèses.
- **Ajouter au calendrier (IA) :** À partir d'une synthèse de rappel, l'IA propose titre et description ; le système trouve le premier créneau libre dans les 8 prochains jours (fuseau Paris) et crée l'événement.

---

## Intégration vocale (Vapi)

**Note :** L'intégration Vapi est encore en phase de test. La prise en charge des appels en direct et le routage téléphonique sont en cours de validation ; à utiliser pour des tests jusqu'à validation complète.

---

## Déploiement

Le MVP tourne sur [Render](https://apen-55r5.onrender.com)

---

## Support bilingue

Le tableau de bord est disponible en **anglais** et **français**. Utiliser le sélecteur de langue dans l'en-tête. La détection d'intention et les tests audio acceptent les entrées FR et EN.

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python) |
| Intentions | IA (OpenAI) + config mots-clés |
| Calendrier | API Google Calendar (OAuth ou compte de service) |
| Voix | Indépendant du fournisseur (Vapi, Bland, etc.) |
| Frontend | Vanilla JS, i18n (EN/FR) |
| Déploiement | Render (ou tout hôte Python) |

---

## Alignement avec l'étude de faisabilité

| Exigence de l'étude | MVP |
|---------------------|-----|
| Accueil 24h/24, sans attente | [OK] Via fournisseur vocal + notre API (Vapi en test) |
| Prise de RDV + calendrier | [OK] Créneaux + Google Calendar |
| Transfert après qualification | [OK] Configurable par intention et site |
| Synthèse de rappel | [OK] Auto depuis la voix, liste, statut, Ajouter au calendrier |
| Transparence | [OK] Toute la logique dans notre dépôt et config |
| Planification, e-mail | [OK] API upload/planning, accusé d’envoi/envoi e-mail |

---

## Prochaines étapes

- **Preuve de concept :** Tests sur le numéro de téléphone.
- **Pilote :** Déploiement limité, KPIs, retours utilisateurs.
- **Production :** Déploiement étendu après validation.
