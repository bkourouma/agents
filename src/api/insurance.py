"""
API endpoints pour le système d'assurance.
Toutes les réponses et messages sont en français.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from src.core.database import get_db
from src.models.insurance import (
    Customer, CustomerCreate, CustomerUpdate, CustomerSearchParams,
    CustomerDetailsResponse, CustomerSummaryResponse,
    InsuranceProduct, InsuranceProductCreate, InsuranceProductUpdate, ProductSearchParams, ProductDetailsResponse,
    InsuranceQuote, InsuranceQuoteCreate, InsuranceQuoteUpdate,
    InsuranceOrder, CreateOrderRequest, UpdateOrderRequest, OrderStatusResponse,
    InsuranceContract, ContractSearchParams, ContractDetailsResponse, ContractStatus,
    PremiumPayment, PremiumPaymentCreate, ProcessPaymentRequest,
    PricingRequest, PricingResponse, ApiResponse
)
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.order_service import OrderService
from src.services.claims_service import ClaimsService
from src.services.quotes_service import QuotesService
from src.services.email_service import EmailService

router = APIRouter(prefix="/api/insurance", tags=["Assurance"])


# =============================================
# ENDPOINTS CLIENTS
# =============================================

@router.get("/clients", response_model=ApiResponse)
async def lister_clients(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=500, description="Nombre d'éléments à retourner"),
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les clients avec pagination."""
    try:
        service = CustomerService(db)
        clients = await service.get_customers(skip=skip, limit=limit)

        return ApiResponse(
            success=True,
            data=clients,
            message=f"{len(clients)} clients trouvés"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/clients/recherche", response_model=ApiResponse)
async def rechercher_clients(
    q: str = Query(..., description="Terme de recherche"),
    type_client: Optional[str] = Query(None, description="Type de client"),
    profil_risque: Optional[str] = Query(None, description="Profil de risque"),
    statut_kyc: Optional[str] = Query(None, description="Statut KYC"),
    limite: int = Query(10, description="Nombre maximum de résultats"),
    db: AsyncSession = Depends(get_db)
):
    """Recherche de clients par nom, email, téléphone ou numéro client."""
    try:
        service = CustomerService(db)
        params = CustomerSearchParams(
            query=q,
            customer_type=type_client,
            risk_profile=profil_risque,
            kyc_status=statut_kyc,
            limit=limite
        )
        clients = await service.search_customers(params)
        
        return ApiResponse(
            success=True,
            data=clients,
            message=f"{len(clients)} client(s) trouvé(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")


@router.get("/clients/{client_id}", response_model=ApiResponse)
async def obtenir_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les informations d'un client par son ID."""
    try:
        service = CustomerService(db)
        client = await service.get_customer_by_id(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        return ApiResponse(
            success=True,
            data=client,
            message="Client récupéré avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/clients/{client_id}/details", response_model=ApiResponse)
async def obtenir_details_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'aperçu complet à 360° d'un client."""
    try:
        service = CustomerService(db)
        details = await service.get_customer_details(client_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        return ApiResponse(
            success=True,
            data=details,
            message="Détails du client récupérés avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/clients/{client_id}/resume", response_model=ApiResponse)
async def obtenir_resume_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère un résumé des métriques clés du client."""
    try:
        service = CustomerService(db)
        resume = await service.get_customer_summary(client_id)
        
        if not resume:
            raise HTTPException(status_code=404, detail="Client non trouvé")
        
        return ApiResponse(
            success=True,
            data=resume,
            message="Résumé du client récupéré avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/clients", response_model=ApiResponse)
async def creer_client(
    client_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau client."""
    try:
        service = CustomerService(db)
        client = await service.create_customer(client_data)
        
        return ApiResponse(
            success=True,
            data=client,
            message="Client créé avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.put("/clients/{client_id}", response_model=ApiResponse)
async def modifier_client(
    client_id: str,
    client_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour un client existant."""
    try:
        service = CustomerService(db)
        client = await service.update_customer(client_id, client_data)

        if not client:
            raise HTTPException(status_code=404, detail="Client non trouvé")

        return ApiResponse(
            success=True,
            data=client,
            message="Client mis à jour avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")


@router.delete("/clients/{client_id}", response_model=ApiResponse)
async def supprimer_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Supprime un client (suppression logique)."""
    try:
        service = CustomerService(db)
        success = await service.delete_customer(client_id)

        if not success:
            raise HTTPException(status_code=404, detail="Client non trouvé")

        return ApiResponse(
            success=True,
            data=None,
            message="Client supprimé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


# =============================================
# ENDPOINTS PRODUITS
# =============================================

@router.get("/produits", response_model=ApiResponse)
async def obtenir_produits(
    type_produit: Optional[str] = Query(None, description="Type de produit"),
    categorie_id: Optional[str] = Query(None, description="ID de la catégorie"),
    actif: bool = Query(True, description="Produits actifs seulement"),
    couverture_min: Optional[float] = Query(None, description="Couverture minimum"),
    couverture_max: Optional[float] = Query(None, description="Couverture maximum"),
    db: AsyncSession = Depends(get_db)
):
    """Récupère la liste des produits d'assurance avec filtres."""
    try:
        service = ProductService(db)
        params = ProductSearchParams(
            product_type=type_produit,
            category_id=categorie_id,
            is_active=actif,
            min_coverage=couverture_min,
            max_coverage=couverture_max
        )
        produits = await service.get_products(params)
        
        return ApiResponse(
            success=True,
            data=produits,
            message=f"{len(produits)} produit(s) trouvé(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/produits/{produit_id}/details", response_model=ApiResponse)
async def obtenir_details_produit(
    produit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails complets d'un produit."""
    try:
        service = ProductService(db)
        details = await service.get_product_details(produit_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
        
        return ApiResponse(
            success=True,
            data=details,
            message="Détails du produit récupérés avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/produits", response_model=ApiResponse)
async def creer_produit(
    product_data: InsuranceProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau produit d'assurance."""
    try:
        service = ProductService(db)
        product = await service.create_product(product_data)

        return ApiResponse(
            success=True,
            data=product,
            message="Produit créé avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.put("/produits/{produit_id}", response_model=ApiResponse)
async def modifier_produit(
    produit_id: str,
    product_data: InsuranceProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour un produit d'assurance existant."""
    try:
        service = ProductService(db)
        product = await service.update_product(produit_id, product_data)

        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        return ApiResponse(
            success=True,
            data=product,
            message="Produit mis à jour avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")


@router.delete("/produits/{produit_id}", response_model=ApiResponse)
async def supprimer_produit(
    produit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Supprime un produit d'assurance (suppression logique)."""
    try:
        service = ProductService(db)
        success = await service.delete_product(produit_id)

        if not success:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        return ApiResponse(
            success=True,
            data=None,
            message="Produit supprimé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@router.post("/produits/tarification", response_model=ApiResponse)
async def calculer_tarification(
    request: PricingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calcule la tarification dynamique pour un produit et un client."""
    try:
        service = ProductService(db)
        tarification = await service.calculate_pricing(request)

        if not tarification:
            raise HTTPException(status_code=400, detail="Impossible de calculer la tarification")

        return ApiResponse(
            success=True,
            data=tarification,
            message="Tarification calculée avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul: {str(e)}")


@router.get("/produits/{produit_id}/eligibilite/{client_id}", response_model=ApiResponse)
async def verifier_eligibilite(
    produit_id: str,
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Vérifie l'éligibilité d'un client pour un produit."""
    try:
        service = ProductService(db)
        eligibilite = await service.check_eligibility(produit_id, client_id)
        
        return ApiResponse(
            success=True,
            data=eligibilite,
            message="Éligibilité vérifiée avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification: {str(e)}")


# =============================================
# ENDPOINTS COMMANDES
# =============================================

@router.get("/commandes", response_model=ApiResponse)
async def obtenir_commandes(
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    skip: int = Query(0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, description="Nombre maximum d'éléments à retourner"),
    db: AsyncSession = Depends(get_db)
):
    """Récupère toutes les commandes avec filtres optionnels."""
    try:
        service = OrderService(db)
        commandes = await service.get_all_orders(statut, skip, limit)

        return ApiResponse(
            success=True,
            data=commandes,
            message=f"{len(commandes)} commande(s) trouvée(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/commandes", response_model=ApiResponse)
async def creer_commande(
    request: CreateOrderRequest,
    db: AsyncSession = Depends(get_db)
):
    """Crée une nouvelle commande d'assurance."""
    try:
        service = OrderService(db)
        commande = await service.create_order(request)

        return ApiResponse(
            success=True,
            data=commande,
            message="Commande créée avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.get("/commandes/{numero_commande}/statut", response_model=ApiResponse)
async def obtenir_statut_commande(
    numero_commande: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère le statut d'une commande avec son historique."""
    try:
        service = OrderService(db)
        statut = await service.get_order_status(numero_commande)
        
        if not statut:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        return ApiResponse(
            success=True,
            data=statut,
            message="Statut de la commande récupéré avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.put("/commandes/{commande_id}", response_model=ApiResponse)
async def modifier_commande(
    commande_id: str,
    request: UpdateOrderRequest,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour une commande existante."""
    try:
        service = OrderService(db)
        commande = await service.update_order(commande_id, request)
        
        if not commande:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        return ApiResponse(
            success=True,
            data=commande,
            message="Commande mise à jour avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")


@router.get("/clients/{client_id}/commandes", response_model=ApiResponse)
async def obtenir_commandes_client(
    client_id: str,
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    db: AsyncSession = Depends(get_db)
):
    """Récupère toutes les commandes d'un client."""
    try:
        service = OrderService(db)
        commandes = await service.get_customer_orders(client_id, statut)
        
        return ApiResponse(
            success=True,
            data=commandes,
            message=f"{len(commandes)} commande(s) trouvée(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


# =============================================
# ENDPOINTS DEVIS
# =============================================

@router.get("/devis", response_model=ApiResponse)
async def lister_devis(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(50, ge=1, le=100, description="Nombre d'éléments à retourner"),
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les devis avec pagination et filtrage."""
    try:
        service = QuotesService(db)
        devis = await service.get_quotes(skip=skip, limit=limit, status=statut)

        return ApiResponse(
            success=True,
            data=devis,
            message=f"{len(devis)} devis trouvés"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/devis/{devis_id}", response_model=ApiResponse)
async def obtenir_devis(
    devis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère un devis par son ID."""
    try:
        service = QuotesService(db)
        devis = await service.get_quote_by_id(devis_id)

        if not devis:
            raise HTTPException(status_code=404, detail="Devis non trouvé")

        return ApiResponse(
            success=True,
            data=devis,
            message="Devis récupéré avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/devis", response_model=ApiResponse)
async def creer_devis(
    quote_data: InsuranceQuoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau devis."""
    try:
        service = QuotesService(db)

        # Convertir en format dict pour la méthode generate_quote existante
        quote_request = {
            "customer_id": quote_data.customer_id,
            "product_id": quote_data.product_id,
            "coverage_amount": quote_data.coverage_amount,
            "premium_frequency": quote_data.premium_frequency,
            "additional_features": quote_data.additional_features or []
        }

        devis = await service.generate_quote(quote_request)

        return ApiResponse(
            success=True,
            data=devis,
            message="Devis créé avec succès"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.post("/devis/generer", response_model=ApiResponse)
async def generer_devis(
    quote_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Génère un devis personnalisé pour un client et un produit."""
    try:
        service = QuotesService(db)
        devis = await service.generate_quote(quote_request)

        return ApiResponse(
            success=True,
            data=devis,
            message="Devis généré avec succès"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


@router.put("/devis/{devis_id}", response_model=ApiResponse)
async def modifier_devis(
    devis_id: str,
    quote_data: InsuranceQuoteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Met à jour un devis existant."""
    try:
        service = QuotesService(db)
        devis = await service.update_quote(devis_id, quote_data)

        if not devis:
            raise HTTPException(status_code=404, detail="Devis non trouvé")

        return ApiResponse(
            success=True,
            data=devis,
            message="Devis mis à jour avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")


@router.delete("/devis/{devis_id}", response_model=ApiResponse)
async def supprimer_devis(
    devis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Supprime un devis (suppression logique)."""
    try:
        service = QuotesService(db)
        success = await service.delete_quote(devis_id)

        if not success:
            raise HTTPException(status_code=404, detail="Devis non trouvé")

        return ApiResponse(
            success=True,
            data=None,
            message="Devis supprimé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@router.get("/clients/{client_id}/devis", response_model=ApiResponse)
async def obtenir_devis_client(
    client_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(20, ge=1, le=50, description="Nombre d'éléments à retourner"),
    db: AsyncSession = Depends(get_db)
):
    """Récupère tous les devis d'un client spécifique."""
    try:
        service = QuotesService(db)
        devis = await service.get_customer_quotes(client_id, skip=skip, limit=limit)

        return ApiResponse(
            success=True,
            data=devis,
            message=f"{len(devis)} devis trouvés pour le client"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


# =============================================
# ENDPOINTS RÉCLAMATIONS
# =============================================

@router.get("/reclamations", response_model=ApiResponse)
async def obtenir_reclamations(
    client_id: Optional[str] = Query(None, description="ID du client"),
    statut: Optional[str] = Query(None, description="Statut de la réclamation"),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les réclamations avec filtres optionnels."""
    try:
        service = ClaimsService(db)
        reclamations = await service.get_claims(customer_id=client_id, status=statut)

        return ApiResponse(
            success=True,
            data=reclamations,
            message=f"{len(reclamations)} réclamation(s) trouvée(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/reclamations/statistiques", response_model=ApiResponse)
async def obtenir_statistiques_reclamations(
    db: AsyncSession = Depends(get_db)
):
    """Récupère les statistiques des réclamations."""
    try:
        service = ClaimsService(db)
        statistiques = await service.get_claims_statistics()

        return ApiResponse(
            success=True,
            data=statistiques,
            message="Statistiques récupérées avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/reclamations", response_model=ApiResponse)
async def creer_reclamation(
    claim_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Crée une nouvelle réclamation."""
    try:
        service = ClaimsService(db)
        reclamation = await service.create_claim(claim_data)

        return ApiResponse(
            success=True,
            data=reclamation,
            message="Réclamation créée avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.get("/reclamations/{numero_reclamation}", response_model=ApiResponse)
async def obtenir_reclamation(
    numero_reclamation: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'une réclamation par son numéro."""
    try:
        service = ClaimsService(db)
        reclamation = await service.get_claim_by_number(numero_reclamation)

        if not reclamation:
            raise HTTPException(status_code=404, detail="Réclamation non trouvée")

        return ApiResponse(
            success=True,
            data=reclamation,
            message="Réclamation récupérée avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.put("/reclamations/{reclamation_id}/statut", response_model=ApiResponse)
async def modifier_statut_reclamation(
    reclamation_id: str,
    status_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Met à jour le statut d'une réclamation."""
    try:
        service = ClaimsService(db)
        reclamation = await service.update_claim_status(
            reclamation_id,
            status_data['new_status'],
            status_data.get('notes'),
            status_data.get('approval_amount'),
            status_data.get('rejection_reason')
        )

        if not reclamation:
            raise HTTPException(status_code=404, detail="Réclamation non trouvée")

        return ApiResponse(
            success=True,
            data=reclamation,
            message="Statut de la réclamation mis à jour avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")



# =============================================
# ENDPOINTS PAIEMENTS
# =============================================

@router.get("/paiements", response_model=ApiResponse)
async def obtenir_paiements(
    statut: Optional[str] = Query(None, description="Statut du paiement"),
    contrat_id: Optional[str] = Query(None, description="ID du contrat"),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les paiements avec filtres optionnels."""
    try:
        from src.services.payment_service import PaymentService

        service = PaymentService(db)
        paiements = await service.get_all_payments(status=statut, contract_id=contrat_id)

        return ApiResponse(
            success=True,
            data=paiements,
            message=f"{len(paiements)} paiement(s) trouvé(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/paiements", response_model=ApiResponse)
async def creer_paiement(
    payment_data: PremiumPaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crée un nouveau paiement de prime."""
    try:
        from src.services.payment_service import PaymentService

        service = PaymentService(db)
        paiement = await service.create_payment(payment_data.dict())

        return ApiResponse(
            success=True,
            data=paiement,
            message="Paiement créé avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.get("/paiements/statistiques", response_model=ApiResponse)
async def obtenir_statistiques_paiements(
    db: AsyncSession = Depends(get_db)
):
    """Récupère les statistiques des paiements."""
    try:
        from src.services.payment_service import PaymentService

        service = PaymentService(db)
        statistiques = await service.get_payment_statistics()

        return ApiResponse(
            success=True,
            data=statistiques,
            message="Statistiques récupérées avec succès"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.put("/paiements/{payment_id}/traiter", response_model=ApiResponse)
async def traiter_paiement(
    payment_id: str,
    payment_data: ProcessPaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Traite un paiement (marque comme payé)."""
    try:
        from src.services.payment_service import PaymentService

        service = PaymentService(db)
        paiement = await service.process_payment(payment_id, payment_data.dict())

        if not paiement:
            raise HTTPException(status_code=404, detail="Paiement non trouvé")

        return ApiResponse(
            success=True,
            data=paiement,
            message="Paiement traité avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")


@router.post("/contrats/{contract_id}/generer-paiements", response_model=ApiResponse)
async def generer_paiements_futurs(
    contract_id: str,
    mois_avance: int = Query(12, description="Nombre de mois à l'avance"),
    db: AsyncSession = Depends(get_db)
):
    """Génère les paiements futurs pour un contrat."""
    try:
        from src.services.payment_service import PaymentService

        service = PaymentService(db)
        paiements = await service.generate_upcoming_payments(contract_id, mois_avance)

        return ApiResponse(
            success=True,
            data=paiements,
            message=f"{len(paiements)} paiement(s) généré(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


# =============================================
# ENDPOINTS COMMANDES À PARTIR DE DEVIS
# =============================================

@router.post("/devis/{devis_id}/commander", response_model=ApiResponse)
async def creer_commande_depuis_devis(
    devis_id: str,
    payment_method: str = "bank_transfer",
    send_email: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Crée une commande à partir d'un devis et envoie un email de confirmation au client."""
    try:
        order_service = OrderService(db)
        quotes_service = QuotesService(db)
        customer_service = CustomerService(db)

        # Créer la commande
        order = await order_service.create_order_from_quote(devis_id, payment_method)

        if not order:
            raise HTTPException(status_code=400, detail="Impossible de créer la commande")

        # Récupérer les données du client pour l'email
        customer = await customer_service.get_customer_by_id(order.customer_id)

        if not customer:
            raise HTTPException(status_code=404, detail="Client non trouvé")

        # Envoyer l'email de confirmation si demandé
        email_sent = False
        if send_email and customer.email:
            try:
                email_service = EmailService()

                # Préparer les données pour l'email
                customer_data = {
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'email': customer.email
                }

                order_data = {
                    'order_number': order.order_number,
                    'application_date': order.application_date.strftime('%d/%m/%Y') if order.application_date else '',
                    'order_status': order.order_status,
                    'coverage_amount': order.coverage_amount,
                    'premium_amount': order.premium_amount
                }

                email_sent = email_service.send_order_confirmation_email(customer_data, order_data)

            except Exception as e:
                # L'erreur d'email ne doit pas empêcher la création de la commande
                print(f"Erreur lors de l'envoi de l'email: {e}")

        return ApiResponse(
            success=True,
            data={
                "order": order,
                "email_sent": email_sent
            },
            message=f"Commande {order.order_number} créée avec succès" +
                   (" et email envoyé" if email_sent else " (email non envoyé)")
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la commande: {str(e)}")


@router.post("/devis/{devis_id}/envoyer-email", response_model=ApiResponse)
async def envoyer_devis_par_email(
    devis_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Envoie le devis par email au client."""
    try:
        quotes_service = QuotesService(db)
        customer_service = CustomerService(db)

        # Récupérer le devis
        quote = await quotes_service.get_quote_by_id(devis_id)

        if not quote:
            raise HTTPException(status_code=404, detail="Devis non trouvé")

        # Récupérer les données du client
        customer = await customer_service.get_customer_by_id(quote.customer_id)

        if not customer:
            raise HTTPException(status_code=404, detail="Client non trouvé")

        if not customer.email:
            raise HTTPException(status_code=400, detail="Le client n'a pas d'adresse email")

        # Envoyer l'email
        email_service = EmailService()

        # Préparer les données pour l'email
        customer_data = {
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email
        }

        # Récupérer les données du produit
        product_service = ProductService(db)
        product = await product_service.get_product_by_id(quote.product_id)

        quote_data = {
            'quote_number': quote.quote_number,
            'product': {
                'name': product.name if product else 'Produit inconnu'
            },
            'coverage_amount': quote.coverage_amount,
            'premium_frequency': quote.premium_frequency,
            'final_premium': quote.final_premium,
            'annual_premium': quote.annual_premium,
            'expiry_date': quote.expiry_date.strftime('%d/%m/%Y') if quote.expiry_date else ''
        }

        email_sent = email_service.send_quote_email(customer_data, quote_data)

        if not email_sent:
            raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")

        return ApiResponse(
            success=True,
            data={"email_sent": True},
            message=f"Devis {quote.quote_number} envoyé par email à {customer.email}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email: {str(e)}")


# =============================================
# ENDPOINTS CONTRATS
# =============================================

@router.get("/contrats", response_model=ApiResponse)
async def obtenir_tous_les_contrats(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Récupère tous les contrats avec filtrage optionnel par statut."""
    try:
        from src.services.contract_service import ContractService
        from src.models.insurance import ContractSearchParams

        service = ContractService(db)

        # Créer les paramètres de recherche
        search_params = ContractSearchParams(
            contract_status=status if status and status != 'all' else None,
            page=1,
            page_size=limit
        )

        contracts = await service.search_contracts(search_params)

        return ApiResponse(
            success=True,
            data=contracts,
            message=f"{len(contracts)} contrat(s) trouvé(s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/contrats/{policy_number}/details", response_model=ApiResponse)
async def obtenir_details_contrat(
    policy_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails complets d'un contrat."""
    try:
        from src.services.contract_service import ContractService

        service = ContractService(db)
        details = await service.get_contract_details(policy_number)

        if not details:
            raise HTTPException(status_code=404, detail="Contrat non trouvé")

        return ApiResponse(
            success=True,
            data=details,
            message="Détails du contrat récupérés avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/contrats/from-order", response_model=ApiResponse)
async def creer_contrat_depuis_commande(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_db)
):
    """Crée un contrat à partir d'une commande approuvée."""
    try:
        from src.services.contract_service import ContractService

        order_id = request.get('order_id')
        if not order_id:
            raise HTTPException(status_code=400, detail="ID de commande requis")

        service = ContractService(db)
        contract = await service.create_contract_from_order(order_id)

        if not contract:
            raise HTTPException(status_code=400, detail="Impossible de créer le contrat. Vérifiez que la commande est approuvée.")

        return ApiResponse(
            success=True,
            data=contract,
            message=f"Contrat {contract.policy_number} créé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")


@router.put("/contrats/{policy_number}/status", response_model=ApiResponse)
async def modifier_statut_contrat(
    policy_number: str,
    status_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Met à jour le statut d'un contrat."""
    try:
        from src.services.contract_service import ContractService
        from src.models.insurance import ContractStatus

        new_status = status_data.get('status')
        reason = status_data.get('reason')

        if not new_status:
            raise HTTPException(status_code=400, detail="Nouveau statut requis")

        # Valider le statut
        try:
            status_enum = ContractStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {new_status}")

        service = ContractService(db)
        contract = await service.update_contract_status(policy_number, status_enum, reason)

        if not contract:
            raise HTTPException(status_code=404, detail="Contrat non trouvé")

        return ApiResponse(
            success=True,
            data=contract,
            message=f"Statut du contrat mis à jour vers {new_status}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")


@router.post("/contrats/{policy_number}/renew", response_model=ApiResponse)
async def renouveler_contrat(
    policy_number: str,
    renewal_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Renouvelle un contrat."""
    try:
        from src.services.contract_service import ContractService

        service = ContractService(db)
        renewed_contract = await service.renew_contract(policy_number, renewal_data)

        if not renewed_contract:
            raise HTTPException(status_code=404, detail="Contrat non trouvé ou non renouvelable")

        return ApiResponse(
            success=True,
            data=renewed_contract,
            message=f"Contrat {policy_number} renouvelé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du renouvellement: {str(e)}")


@router.get("/contrats/{policy_number}/payments", response_model=ApiResponse)
async def obtenir_historique_paiements(
    policy_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'historique des paiements d'un contrat."""
    try:
        from src.services.contract_service import ContractService

        service = ContractService(db)
        payments = await service.get_payment_history(policy_number)

        return ApiResponse(
            success=True,
            data=payments,
            message=f"Historique des paiements récupéré ({len(payments)} paiement(s))"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.post("/contrats/{policy_number}/beneficiaries", response_model=ApiResponse)
async def ajouter_beneficiaire(
    policy_number: str,
    beneficiary_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Ajoute un bénéficiaire à un contrat."""
    try:
        from src.services.contract_service import ContractService

        service = ContractService(db)
        beneficiary = await service.add_beneficiary(policy_number, beneficiary_data)

        if not beneficiary:
            raise HTTPException(status_code=404, detail="Contrat non trouvé")

        return ApiResponse(
            success=True,
            data=beneficiary,
            message="Bénéficiaire ajouté avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout: {str(e)}")
