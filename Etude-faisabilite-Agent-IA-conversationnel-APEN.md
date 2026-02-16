# Étude de faisabilité – Agent conversationnel IA pour APEN

**Objet :** Mise en place d’un agent IA pour la gestion des appels entrants et tâches associées (remplacement du serveur vocal actuel).  
**Référence :** Proposition post-appel ; cadre méthodologique : *Standard AI project management workflow* (Amzil AI).  
**Solution envisagée :** Limova – Agent Tom (https://www.limova.ai/agents/tom) ou équivalent.  
**Date :** Février 2025.

---

## 1. Contexte, objectifs et alignement stratégique

### 1.1 Contexte APEN

APEN est une entreprise de sécurité privée implantée sur plusieurs sites (Paris/Montrouge, Le Havre, Reims, Nancy, Nantes). Les appels entrants concernent notamment : prise de rendez-vous (ex. récupération de tenues), demandes d’information, urgences opérationnelles, partenaires, SAV. Le serveur vocal actuel limite la réactivité et ne permet pas de traiter plusieurs appels sans attente ni d’automatiser des actions simples (agenda, planning, synthèses, transferts ciblés).

### 1.2 Objectifs du projet

| Objectif métier | Indicateur cible (MVP) |
|-----------------|------------------------|
| Réduire le temps d’attente et les appels manqués | Réponse immédiate 24/7 ; 0 file d’attente pour les appels pris en charge par l’agent |
| Automatiser la prise de rendez-vous | Créneaux proposés et inscrits automatiquement dans un agenda (ex. Google Agenda) |
| Améliorer le routage des appels | Transfert vers le bon interlocuteur après qualification du motif d’appel |
| Libérer du temps pour les équipes | Prise en charge des demandes simples (horaires, infos, planning) et synthèses pour rappel |
| Couvrir email et planning | Accusés de réception personnalisés ; envoi/publication de plannings sur périmètre défini |

### 1.3 Alignement avec le cadre Standard AI (workflow d’intégration)

Le projet suit le cycle **Feasibility → Proof of Concept → Pilot → Production** :

- **Feasibility (cette étude) :** coût, viabilité, périmètre MVP, risques, plan préliminaire.
- **Proof of Concept :** validation technique et fonctionnelle en environnement limité (un site ou un numéro pilote).
- **Pilot :** déploiement limité dans le temps et l’espace, collecte de retours utilisateurs et mesure des KPIs.
- **Production :** déploiement stable et scalable sur l’ensemble des sites/numéros.

---

## 2. Évaluation technologique et solution envisagée (Limova – Tom)

### 2.1 Fonctionnalités attendues vs offre Limova Tom

| Besoin APEN | Tom (Limova) | Adéquation |
|-------------|--------------|------------|
| Réception d’appels 24/7, plusieurs appels simultanés | Réception 24/7, pas de file d’attente | ✅ Aligné |
| Prise de rendez-vous + inscription agenda | Intégration Google Agenda, proposition de créneaux | ✅ Aligné |
| Transfert intelligent après analyse du motif | Qualification + transfert vers la bonne personne | ✅ Aligné |
| Synthèse pour rappel | Compte-rendu instantané sur plateforme | ✅ Aligné |
| Envoi/publication de planning | Non couvert nativement par Tom | ⚠️ À traiter en custom ou via autre agent/API |
| Réponse automatique à certains e-mails | Non couvert par Tom (téléphonie) | ⚠️ Mickael (relation client) ou intégration email à préciser |

**Conclusion technologique :** La solution Limova Tom couvre le cœur du besoin (appels, RDV, qualification, transfert, synthèse). Les volets « planning » et « e-mail » relèvent soit d’une extension de périmètre (agents Limova complémentaires, API), soit d’un MVP limité au téléphone + agenda.

### 2.2 Maturité et intégration

- **Maturité :** Solution commerciale française, déployée en production (témoignages type agences immobilières). Technologie vocale IA mature pour accueil et qualification.
- **Intégration :** Google Agenda documentée. Connexion à l’écosystème APEN (agenda, CRM, outils métier) à valider en PoC (APIs, connecteurs, SSO si besoin).
- **Scalabilité :** Architecture cloud ; montée en charge sur plusieurs lignes/sites à confirmer avec Limova (offre multi-sites / multi-numéros).

### 2.3 Alternatives (à garder en vue pour la phase PoC)

- Autres plateformes d’agents vocaux IA (françaises ou EU) pour comparer coûts, intégrations et conformité RGPD.
- Build interne : coût et délai nettement plus élevés ; non recommandé pour un MVP centré sur la réception d’appels.

---

## 3. Périmètre MVP et plan préliminaire

### 3.1 Principes du MVP

- **Objectif :** Valider la valeur métier et l’acceptation (utilisateurs et appelants) avec un périmètre minimal livrable rapidement.
- **Périmètre cible :** Un site ou une ligne pilote ; cas d’usage prioritaires = accueil + qualification + prise de RDV + transfert + synthèse.

### 3.2 Périmètre fonctionnel MVP (recommandé)

| Priorité | Fonctionnalité | Inclus dans MVP | Commentaire |
|----------|----------------|-----------------|-------------|
| P0 | Réception 24/7, pas d’attente | Oui | Remplacement serveur vocal sur la ligne pilote |
| P0 | Qualification du motif d’appel (RDV, info, urgence, SAV, partenaire) | Oui | Règles et scripts à définir avec les équipes |
| P0 | Prise de rendez-vous et inscription dans un agenda | Oui | Ex. récupération de tenues – un agenda partagé (Google ou autre) |
| P0 | Transfert vers le bon interlocuteur / service | Oui | Règles de routage selon motif et site |
| P0 | Synthèse écrite pour rappel (compte-rendu) | Oui | Disponible sur plateforme Limova ou export vers outil interne |
| P1 | Envoi ou publication de planning | Non (post-MVP) | À traiter en phase 2 (API, autre canal) |
| P1 | Réponses automatiques e-mail (accusés de réception) | Non (post-MVP) | À traiter en phase 2 (Mickael ou intégration email) |

**MVP = P0 uniquement**, sur **une ligne / un site** (ex. siège ou site le plus représentatif).

### 3.3 Livrables et jalons préliminaires (alignés Standard AI)

| Phase | Durée indicative | Livrables principaux |
|-------|------------------|------------------------|
| **Feasibility** | 2–3 semaines | Cette étude ; validation direction ; choix fournisseur (Limova ou autre) ; budget et planning prévisionnels |
| **Proof of Concept** | 4–6 semaines | Paramétrage Tom (ou équivalent) sur ligne pilote ; intégration agenda ; scénarios : accueil, RDV, transfert, synthèse ; validation technique et UX |
| **Pilot** | 6–8 semaines | Mise en production pilote ; formation utilisateurs ; collecte retours ; mesure KPIs (taux de résolution sans transfert, satisfaction, nombre de RDV pris) |
| **Décision déploiement** | — | Go / No-go pour généralisation à tous les sites et extension (planning, email) |

Estimation end-to-end jusqu’à décision de généralisation : **environ 3–4 mois** (sous réserve de disponibilité des équipes et de Limova).

---

## 4. Données, compétences, risques et conformité

### 4.1 Données et voix

- **Données utilisées :** Enregistrements d’appels, transcriptions, métadonnées (durée, motif, transfert). Limova traite ces données ; il faut vérifier le lieu d’hébergement et les DPA (Data Processing Agreement).
- **Qualité / biais :** S’assurer que les scripts et scénarios couvrent les cas réels (urgences, accents, bruit). Prévoir un échantillon d’appels pour entraînement/paramétrage et tests.
- **Conservation :** Durée de conservation des enregistrements et transcriptions à définir (conformité RGPD et interne).

### 4.2 Compétences et ressources

- **Interne :** Un référent métier (opérations / standard) pour définir les scénarios, les règles de transfert et valider les comptes-rendus ; un référent IT pour intégration agenda et éventuelles APIs.
- **Externe :** Limova (paramétrage, formation, support) ; éventuellement accompagnement projet (AMOA) si besoin.
- **Coûts à chiffrer :** Abonnement Limova (par numéro / par site), coût de mise en œuvre (paramétrage, intégration), formation.

### 4.3 Risques et mitigation (format Standard AI)

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Rejet par les utilisateurs (équipes) | Échec adoption, retour en arrière | Moyenne | Impliquer les équipes dès le PoC ; formation ; période pilote avec bascule progressive |
| Mauvaise qualification des appels (transferts incorrects) | Frustration appelants, perte de temps | Moyenne | Affiner les scripts et règles avec les opérationnels ; revue régulière des comptes-rendus et des transferts |
| Problème d’intégration agenda (dispo, doublons) | RDV non créés ou conflits | Faible à moyenne | PoC dédié sur un agenda de test ; règles claires de créneaux et de synchronisation |
| Non-conformité RGPD / confidentialité | Sanctions, réputation | Faible si encadré | DPA avec Limova ; information des appelants (message type « cet appel peut être enregistré et traité par IA ») ; durée de rétention définie |
| Coût plus élevé que prévu | Dépasse budget | Moyenne | Fixer un plafond pour le PoC/Pilot ; comparer offres (Limova vs autres) en phase feasibility |

### 4.4 Conformité (RGPD / IA)

- **RGPD :** Finalité, minimisation des données, droit d’accès/rectification/effacement, base légale (intérêt légitime ou consentement selon cas). Documenter dans une fiche traitement « gestion des appels entrants – agent IA ».
- **Règlement IA (EU) :** Classifier le système (probablement « limited risk ») et prévoir transparence vis-à-vis des personnes (information qu’elles parlent à un agent IA).
- **Sectoriel :** Vérifier qu’aucune norme secteur (sécurité privée) n’impose de contraintes spécifiques sur l’enregistrement ou le traitement des appels.

---

## 5. Synthèse et prochaines étapes

### 5.1 Faisabilité

- **Technique :** Faisable avec une solution du type Limova Tom pour l’accueil, la qualification, la prise de RDV, le transfert et la synthèse. Les volets planning et e-mail sont en phase 2.
- **Organisationnelle :** Réalisable sous réserve d’un référent métier et d’un référent IT dédiés au PoC/Pilot.
- **Économique :** À valider par un devis Limova et une estimation interne (temps de paramétrage, intégration, formation).

### 5.2 MVP recommandé (rappel)

- **Périmètre :** Une ligne / un site pilote.
- **Fonctions :** Réception 24/7, qualification, prise de rendez-vous (agenda), transfert intelligent, synthèse pour rappel.
- **Hors MVP pour plus tard :** Envoi/publication de planning ; réponses automatiques e-mail.

### 5.3 Prochaines étapes proposées

1. **Valider** cette étude en interne (direction, opérations, IT) et décider du lancement du PoC.
2. **Contacter Limova** (démo Tom, devis, conditions d’hébergement des données et DPA).
3. **Définir le site/ligne pilote** et le référent métier + IT.
4. **Rédiger le cahier des charges du PoC** (scénarios détaillés, règles de transfert, KPIs de succès).
5. **Lancer le PoC** selon le planning préliminaire (4–6 semaines), puis enchaîner sur le Pilot (6–8 semaines) et la décision de généralisation.

---

*Document préparé dans le cadre de l’étude de faisabilité pour l’intégration d’un agent conversationnel IA chez APEN, en cohérence avec le Standard AI project management workflow (feasibility → PoC → Pilot → Production).*
