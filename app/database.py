"""
Firestore Database Client
"""

from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient
from typing import List, Optional
from datetime import datetime
import logging

from models import RunnerApplication, RunnerApplicationCreate
from config import settings

logger = logging.getLogger(__name__)


class FirestoreDB:
    """Firestore database operations"""
    
    def __init__(self):
        """Initialize Firestore client"""
        try:
            self.db = firestore.AsyncClient(project=settings.GCP_PROJECT_ID)
            self.collection = self.db.collection('applications')
            logger.info(f"Firestore client initialized for project: {settings.GCP_PROJECT_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {str(e)}")
            raise
    
    async def create_application(self, application: RunnerApplicationCreate) -> str:
        """
        Crea una nuova application nel database
        
        Args:
            application: RunnerApplicationCreate model
            
        Returns:
            Document ID della nuova application
        """
        try:
            # Prepara i dati
            data = application.model_dump()
            data['created_at'] = datetime.utcnow()
            data['status'] = 'pending'
            
            # Crea documento
            doc_ref = self.collection.document()
            await doc_ref.set(data)
            
            logger.info(f"Created application: {doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Error creating application: {str(e)}")
            raise
    
    async def get_application(self, application_id: str) -> Optional[RunnerApplication]:
        """
        Recupera una singola application per ID
        
        Args:
            application_id: Document ID
            
        Returns:
            RunnerApplication o None se non trovata
        """
        try:
            doc_ref = self.collection.document(application_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data['id'] = doc.id
            
            return RunnerApplication(**data)
            
        except Exception as e:
            logger.error(f"Error fetching application {application_id}: {str(e)}")
            raise
    
    async def get_applications(
        self,
        limit: int = 50,
        level: Optional[str] = None,
        goal: Optional[str] = None
    ) -> List[RunnerApplication]:
        """
        Recupera lista di applications con filtri opzionali
        
        Args:
            limit: Numero massimo di risultati
            level: Filtra per livello
            goal: Filtra per obiettivo
            
        Returns:
            Lista di RunnerApplication
        """
        try:
            query = self.collection.order_by(
                'created_at', 
                direction=firestore.Query.DESCENDING
            )
            
            # Applica filtri
            if level:
                query = query.where('level', '==', level)
            if goal:
                query = query.where('goal', '==', goal)
            
            query = query.limit(limit)
            
            # Esegui query
            docs = query.stream()
            
            applications = []
            async for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                applications.append(RunnerApplication(**data))
            
            logger.info(f"Retrieved {len(applications)} applications")
            return applications
            
        except Exception as e:
            logger.error(f"Error fetching applications: {str(e)}")
            raise
    
    async def delete_application(self, application_id: str) -> bool:
        """
        Elimina una application
        
        Args:
            application_id: Document ID
            
        Returns:
            True se eliminata, False se non trovata
        """
        try:
            doc_ref = self.collection.document(application_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return False
            
            await doc_ref.delete()
            logger.info(f"Deleted application: {application_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting application {application_id}: {str(e)}")
            raise
    
    async def update_application_status(
        self,
        application_id: str,
        status: str
    ) -> Optional[RunnerApplication]:
        """
        Aggiorna lo status di una application
        
        Args:
            application_id: Document ID
            status: Nuovo status (pending/approved/rejected)
            
        Returns:
            RunnerApplication aggiornata o None se non trovata
        """
        try:
            doc_ref = self.collection.document(application_id)
            doc = await doc_ref.get()
            
            if not doc.exists:
                return None
            
            await doc_ref.update({'status': status})
            
            # Recupera documento aggiornato
            return await self.get_application(application_id)
            
        except Exception as e:
            logger.error(f"Error updating application {application_id}: {str(e)}")
            raise
