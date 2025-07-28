# Système d'Assurance - Service Client

## 🎯 Vue d'ensemble

Le système d'assurance est une solution complète de gestion de service client pour les compagnies d'assurance. Il permet aux agents de service client de gérer efficacement les clients, produits, devis, commandes, contrats, réclamations et paiements. **TOUTES LES DONNÉES SIMULÉES ONT ÉTÉ SUPPRIMÉES** - le système utilise maintenant uniquement des API réelles avec une base de données SQLite.

## ✨ Fonctionnalités Principales

### 🧑‍💼 Gestion des Clients
- **Recherche avancée** : Par nom, email, téléphone ou numéro client
- **Aperçu 360°** : Vue complète du client avec contrats actifs, commandes récentes et interactions
- **Profil de risque** : Évaluation automatique (faible, moyen, élevé)
- **Statut KYC** : Suivi de la vérification d'identité
- **Résumé financier** : Couverture totale, primes, statut de paiement

### 📦 Catalogue de Produits
- **Types de produits** : Vie, Santé, Auto, Habitation, Entreprise
- **Tarification dynamique** : Calcul automatique basé sur les facteurs de risque
- **Niveaux de prix** : Différents tiers de couverture
- **Vérification d'éligibilité** : Contrôle automatique des critères
- **Fonctionnalités modulaires** : Options standard et supplémentaires

### 🛒 Gestion des Commandes
- **Workflow complet** : Du brouillon à l'approbation
- **Suivi en temps réel** : Historique détaillé des changements de statut
- **Validation automatique** : Vérification des documents et examens médicaux
- **Assignation d'agents** : Gestion des responsabilités
- **Notifications** : Alertes pour les actions requises

### 🛡️ Gestion des Contrats
- **Polices actives** : Vue d'ensemble des contrats en cours
- **Renouvellements** : Suivi automatique des échéances
- **Bénéficiaires** : Gestion des ayants droit
- **Valeurs de rachat** : Calcul des valeurs de rachat et de prêt
- **Alertes d'expiration** : Notifications préventives

### 💰 Gestion des Paiements
- **Suivi des primes** : Échéances et paiements effectués
- **Paiements en retard** : Identification et gestion des impayés
- **Période de grâce** : Gestion automatique des délais
- **Méthodes de paiement** : Support de multiples moyens de paiement

### 📋 Gestion des Réclamations
- **Workflow de traitement** : De la soumission au règlement
- **Assignation d'experts** : Gestion des enquêtes
- **Suivi des documents** : Gestion des pièces justificatives
- **Historique complet** : Traçabilité de tous les événements

### 💰 Génération de Devis
- **Devis personnalisés** : Calcul automatique basé sur le profil client
- **Facteurs de tarification** : Application des multiplicateurs par âge, genre, risque
- **Options supplémentaires** : Sélection de fonctionnalités additionnelles
- **Validation d'éligibilité** : Vérification automatique des critères
- **Export PDF** : Génération de documents professionnels

### 📞 Service Client
- **Journalisation des interactions** : Appels, emails, chats, visites
- **Suivi des tâches** : Gestion des actions à effectuer
- **Escalade** : Processus de remontée des problèmes
- **Évaluation de satisfaction** : Collecte des retours clients

## 🏗️ Architecture Technique

### Backend (FastAPI + SQLite)
```
src/
├── api/
│   └── insurance.py          # Endpoints API REST
├── services/
│   ├── customer_service.py   # Logique métier clients
│   ├── product_service.py    # Logique métier produits
│   ├── order_service.py      # Logique métier commandes
│   ├── contract_service.py   # Logique métier contrats
│   ├── claims_service.py     # Logique métier réclamations
│   └── quotes_service.py     # Logique métier devis
├── models/
│   └── insurance.py          # Modèles Pydantic
└── migrations/
    └── create_insurance_tables.py  # Schéma de base de données
```

### Frontend (React + TypeScript)
```
frontend/src/
├── pages/
│   └── AssurancePage.tsx     # Page principale
├── components/Insurance/
│   ├── CustomerManagement.tsx    # Gestion clients
│   ├── ProductManagement.tsx     # Gestion produits
│   ├── QuotesManagement.tsx      # Génération devis
│   ├── OrderManagement.tsx       # Gestion commandes
│   └── ClaimsManagement.tsx      # Gestion réclamations
└── lib/
    └── insurance-api.ts      # Client API
```

### Base de Données (SQLite)
- **customers** : Informations clients
- **insurance_products** : Catalogue de produits
- **pricing_tiers** : Niveaux de prix
- **pricing_factors** : Facteurs de tarification
- **insurance_orders** : Commandes
- **insurance_contracts** : Contrats
- **premium_payments** : Paiements
- **insurance_claims** : Réclamations
- **customer_interactions** : Interactions

## 🚀 Installation et Configuration

### 1. Configuration de la Base de Données
```bash
# Créer les tables et insérer les données de test
python setup_insurance_db.py
```

### 2. Démarrage du Backend
```bash
# Activer l'environnement virtuel
venv\Scripts\activate

# Démarrer le serveur FastAPI
python main.py
```
Le serveur démarre sur `http://localhost:3006`

### 3. Démarrage du Frontend
```bash
# Aller dans le dossier frontend
cd frontend

# Installer les dépendances (si nécessaire)
npm install

# Démarrer le serveur de développement
npm run dev
```
L'interface démarre sur `http://localhost:3003`

## 🎨 Interface Utilisateur

### Navigation
L'interface est organisée en onglets :
- **Tableau de bord** : Vue d'ensemble et statistiques
- **Clients** : Recherche et gestion des clients
- **Produits** : Catalogue et tarification
- **Devis** : Génération de devis personnalisés
- **Commandes** : Suivi des demandes
- **Contrats** : Gestion des polices
- **Réclamations** : Traitement des sinistres
- **Paiements** : Suivi financier

### Fonctionnalités Clés
- **Recherche intelligente** : Recherche en temps réel
- **Vues détaillées** : Informations complètes sur 2 colonnes
- **Statuts visuels** : Badges colorés pour les états
- **Actions rapides** : Boutons d'action contextuels
- **Interface responsive** : Adaptation mobile et desktop

## 📊 Données de Test

Le système inclut des données de démonstration :
- **3 clients** avec profils variés
- **4 produits** d'assurance (Vie, Santé, Auto, Habitation)
- **Facteurs de tarification** par âge, genre, risque
- **Niveaux de prix** multiples par produit

## 🔧 API Endpoints

### Clients
- `GET /api/insurance/clients/recherche` - Recherche de clients
- `GET /api/insurance/clients/{id}` - Détails d'un client
- `GET /api/insurance/clients/{id}/details` - Vue 360° du client
- `GET /api/insurance/clients/{id}/resume` - Résumé financier
- `POST /api/insurance/clients` - Création d'un client
- `PUT /api/insurance/clients/{id}` - Modification d'un client

### Produits
- `GET /api/insurance/produits` - Liste des produits
- `GET /api/insurance/produits/{id}/details` - Détails d'un produit
- `POST /api/insurance/produits/tarification` - Calcul de prix
- `GET /api/insurance/produits/{id}/eligibilite/{client_id}` - Vérification d'éligibilité

### Commandes
- `POST /api/insurance/commandes` - Création d'une commande
- `GET /api/insurance/commandes/{numero}/statut` - Statut d'une commande
- `PUT /api/insurance/commandes/{id}` - Modification d'une commande
- `GET /api/insurance/clients/{id}/commandes` - Commandes d'un client

## 🌐 Internationalisation

Toute l'interface utilisateur est en français :
- Labels et boutons
- Messages d'erreur et de succès
- Descriptions et tooltips
- Formats de date et nombre (français)

## 🔒 Sécurité

- **Validation des données** : Contrôles côté client et serveur
- **Types stricts** : TypeScript pour la sécurité des types
- **Gestion d'erreurs** : Fallbacks et messages utilisateur
- **Logs détaillés** : Traçabilité des actions

## 📈 Évolutions Futures

- **Intégration paiements** : Passerelles de paiement réelles
- **Notifications** : Système d'alertes en temps réel
- **Rapports** : Génération de documents PDF
- **Mobile** : Application mobile native
- **IA** : Assistant intelligent pour les agents

## 🤝 Support

Pour toute question ou problème :
1. Vérifier les logs du serveur backend
2. Consulter la console du navigateur
3. Tester la connectivité API avec `/health`
4. Vérifier la base de données SQLite

Le système est conçu pour être robuste avec des fallbacks en cas d'erreur API, permettant une utilisation continue même en mode dégradé.
