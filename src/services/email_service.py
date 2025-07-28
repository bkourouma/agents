"""
Service d'envoi d'emails pour les devis et commandes d'assurance.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Configuration email (à adapter selon votre fournisseur)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.company_name = os.getenv("COMPANY_NAME", "AssuranceCI")
        
    def _create_connection(self):
        """Crée une connexion SMTP sécurisée."""
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=context)
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Erreur de connexion SMTP: {e}")
            raise
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Envoie un email."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            
            # Ajouter le contenu texte si fourni
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                msg.attach(text_part)
            
            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)
            
            # Envoyer l'email
            with self._create_connection() as server:
                server.send_message(msg)
            
            logger.info(f"Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {e}")
            return False
    
    def send_quote_email(self, customer_data: Dict[str, Any], quote_data: Dict[str, Any]) -> bool:
        """Envoie un email avec le devis au client."""
        
        customer_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}"
        customer_email = customer_data.get('email')
        
        if not customer_email:
            logger.error("Adresse email du client manquante")
            return False
        
        subject = f"Votre devis d'assurance - {quote_data.get('quote_number')}"
        
        # Contenu HTML de l'email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .quote-details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #059669; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{self.company_name}</h1>
                    <h2>Votre Devis d'Assurance</h2>
                </div>
                
                <div class="content">
                    <p>Bonjour {customer_name},</p>
                    
                    <p>Nous avons le plaisir de vous transmettre votre devis d'assurance personnalisé.</p>
                    
                    <div class="quote-details">
                        <h3>Détails du Devis</h3>
                        <table>
                            <tr>
                                <td class="label">Numéro de devis:</td>
                                <td>{quote_data.get('quote_number')}</td>
                            </tr>
                            <tr>
                                <td class="label">Produit:</td>
                                <td>{quote_data.get('product', {}).get('name', 'N/A')}</td>
                            </tr>
                            <tr>
                                <td class="label">Montant de couverture:</td>
                                <td>{quote_data.get('coverage_amount', 0):,} XOF</td>
                            </tr>
                            <tr>
                                <td class="label">Fréquence de paiement:</td>
                                <td>{self._get_frequency_label(quote_data.get('premium_frequency', 'monthly'))}</td>
                            </tr>
                            <tr>
                                <td class="label">Prime {self._get_frequency_label(quote_data.get('premium_frequency', 'monthly')).lower()}:</td>
                                <td class="amount">{quote_data.get('final_premium', 0):,} XOF</td>
                            </tr>
                            <tr>
                                <td class="label">Prime annuelle:</td>
                                <td>{quote_data.get('annual_premium', 0):,} XOF</td>
                            </tr>
                            <tr>
                                <td class="label">Date d'expiration:</td>
                                <td>{quote_data.get('expiry_date')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p><strong>Ce devis est valable jusqu'au {quote_data.get('expiry_date')}.</strong></p>
                    
                    <p>Pour souscrire à cette assurance ou pour toute question, n'hésitez pas à nous contacter.</p>
                    
                    <p>Cordialement,<br>
                    L'équipe {self.company_name}</p>
                </div>
                
                <div class="footer">
                    <p>{self.company_name} - Votre partenaire assurance en Côte d'Ivoire</p>
                    <p>Email: {self.from_email} | Téléphone: +225 XX XX XX XX XX</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Contenu texte simple
        text_content = f"""
        Bonjour {customer_name},
        
        Votre devis d'assurance {quote_data.get('quote_number')} est prêt.
        
        Produit: {quote_data.get('product', {}).get('name', 'N/A')}
        Couverture: {quote_data.get('coverage_amount', 0):,} XOF
        Prime {self._get_frequency_label(quote_data.get('premium_frequency', 'monthly')).lower()}: {quote_data.get('final_premium', 0):,} XOF
        
        Ce devis est valable jusqu'au {quote_data.get('expiry_date')}.
        
        Cordialement,
        L'équipe {self.company_name}
        """
        
        return self._send_email(customer_email, subject, html_content, text_content)
    
    def send_order_confirmation_email(self, customer_data: Dict[str, Any], order_data: Dict[str, Any]) -> bool:
        """Envoie un email de confirmation de commande au client."""
        
        customer_name = f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}"
        customer_email = customer_data.get('email')
        
        if not customer_email:
            logger.error("Adresse email du client manquante")
            return False
        
        subject = f"Confirmation de votre commande - {order_data.get('order_number')}"
        
        # Contenu HTML de l'email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .order-details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .status {{ background-color: #fef3c7; color: #92400e; padding: 10px; border-radius: 5px; text-align: center; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{self.company_name}</h1>
                    <h2>Confirmation de Commande</h2>
                </div>
                
                <div class="content">
                    <p>Bonjour {customer_name},</p>
                    
                    <p>Nous avons bien reçu votre demande d'assurance. Voici les détails de votre commande :</p>
                    
                    <div class="order-details">
                        <h3>Détails de la Commande</h3>
                        <table>
                            <tr>
                                <td class="label">Numéro de commande:</td>
                                <td>{order_data.get('order_number')}</td>
                            </tr>
                            <tr>
                                <td class="label">Date de demande:</td>
                                <td>{order_data.get('application_date')}</td>
                            </tr>
                            <tr>
                                <td class="label">Statut:</td>
                                <td>{self._get_status_label(order_data.get('order_status'))}</td>
                            </tr>
                            <tr>
                                <td class="label">Montant de couverture:</td>
                                <td>{order_data.get('coverage_amount', 0):,} XOF</td>
                            </tr>
                            <tr>
                                <td class="label">Prime:</td>
                                <td>{order_data.get('premium_amount', 0):,} XOF</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="status">
                        <strong>Prochaines étapes:</strong> Notre équipe va examiner votre demande. 
                        Vous recevrez une notification dès que le traitement sera terminé.
                    </div>
                    
                    <p>Pour toute question concernant votre commande, n'hésitez pas à nous contacter en mentionnant le numéro de commande.</p>
                    
                    <p>Cordialement,<br>
                    L'équipe {self.company_name}</p>
                </div>
                
                <div class="footer">
                    <p>{self.company_name} - Votre partenaire assurance en Côte d'Ivoire</p>
                    <p>Email: {self.from_email} | Téléphone: +225 XX XX XX XX XX</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(customer_email, subject, html_content)
    
    def _get_frequency_label(self, frequency: str) -> str:
        """Retourne le libellé de la fréquence en français."""
        labels = {
            'monthly': 'Mensuelle',
            'quarterly': 'Trimestrielle', 
            'semi-annual': 'Semestrielle',
            'annual': 'Annuelle'
        }
        return labels.get(frequency, 'Mensuelle')
    
    def _get_status_label(self, status: str) -> str:
        """Retourne le libellé du statut en français."""
        labels = {
            'draft': 'Brouillon',
            'submitted': 'Soumise',
            'under_review': 'En cours d\'examen',
            'approved': 'Approuvée',
            'rejected': 'Rejetée',
            'cancelled': 'Annulée'
        }
        return labels.get(status, status)
