"""
NIS 2 Risk Analyzer — Authentication Module
Gère l'identité et l'accès aux APIs Microsoft de façon sécurisée.
"""

import logging
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

# Configuration du logging pour la traçabilité (Audit Trail)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nis2_analyzer.auth")

class AzureAuthManager:
    """
    Gère l'authentification Azure sans secrets "en dur".
    Implémente le principe du "Least Privilege" en centralisant l'accès.
    """
    
    def __init__(self):
        self.credential = None
        self._initialize_credential()

    def _initialize_credential(self):
        """
        Initialise le credential par défaut.
        Tente dans l'ordre : Managed Identity, Environnement, Azure CLI, VS Code.
        """
        try:
            # C'est ici que réside l'intelligence : aucune clé n'est nécessaire
            self.credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=False
            )
            logger.info("Authentification Azure initialisée (DefaultAzureCredential).")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'identité : {e}")
            raise

    def get_token(self, scope: str = "https://graph.microsoft.com/.default"):
        """Récupère un jeton d'accès pour un scope spécifique (ex: MS Graph)."""
        try:
            return self.credential.get_token(scope)
        except ClientAuthenticationError as e:
            logger.error(f"Échec de l'obtention du token : {e}")
            raise