"""
Runner Platform API - Main Application
FastAPI backend for managing runner applications
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime

from models import RunnerApplication, RunnerApplicationCreate, HealthResponse
from database import FirestoreDB
from config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Runner Platform API",
    description="API per gestire richieste di partecipazione alla running community",
    version="1.0.0"
)

# CORS - permetti tutti i domini in dev, restrizione in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = FirestoreDB()


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Runner Platform API is running",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    try:
        # Test Firestore connection
        db.get_applications(limit=1)
        
        return HealthResponse(
            status="healthy",
            message="All systems operational",
            version="1.0.0",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "message": f"Service unavailable: {str(e)}",
                "version": "1.0.0"
            }
        )


@app.post("/api/applications", response_model=RunnerApplication, status_code=status.HTTP_201_CREATED)
async def create_application(application: RunnerApplicationCreate):
    """
    Crea una nuova richiesta di partecipazione
    
    - **name**: Nome completo
    - **email**: Email valida
    - **age**: Età (18-100)
    - **level**: Livello (beginner/intermediate/advanced)
    - **goal**: Obiettivo (5k/10k/half_marathon/marathon/fitness)
    - **availability**: Giorni disponibili
    - **dublin_zone**: Zona preferita di Dublino
    - **experience**: Esperienza precedente (opzionale)
    - **current_pace**: Ritmo attuale (opzionale)
    """
    try:
        logger.info(f"Creating application for {application.email}")
        
        # Crea l'applicazione nel database
        app_id = await db.create_application(application)
        
        # Recupera l'applicazione completa
        created_app = await db.get_application(app_id)
        
        if not created_app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created application"
            )
        
        logger.info(f"Application created successfully: {app_id}")
        return created_app
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )


@app.get("/api/applications", response_model=List[RunnerApplication])
async def list_applications(
    limit: int = 50,
    level: Optional[str] = None,
    goal: Optional[str] = None
):
    """
    Lista tutte le richieste (endpoint admin - da proteggere in futuro)
    
    Query params:
    - **limit**: Numero massimo di risultati (default: 50)
    - **level**: Filtra per livello (beginner/intermediate/advanced)
    - **goal**: Filtra per obiettivo
    """
    try:
        logger.info(f"Fetching applications (limit: {limit}, level: {level}, goal: {goal})")
        
        applications = await db.get_applications(
            limit=limit,
            level=level,
            goal=goal
        )
        
        return applications
        
    except Exception as e:
        logger.error(f"Error fetching applications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch applications"
        )


@app.get("/api/applications/{application_id}", response_model=RunnerApplication)
async def get_application(application_id: str):
    """Recupera una singola richiesta per ID"""
    try:
        application = await db.get_application(application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch application"
        )


@app.delete("/api/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: str):
    """Elimina una richiesta (admin endpoint - da proteggere)"""
    try:
        success = await db.delete_application(application_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found"
            )
        
        logger.info(f"Application {application_id} deleted")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application {application_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete application"
        )


@app.get("/api/stats")
async def get_stats():
    """Statistiche base sulla community"""
    try:
        all_apps = await db.get_applications(limit=1000)
        
        stats = {
            "total_applications": len(all_apps),
            "by_level": {},
            "by_goal": {},
            "by_zone": {}
        }
        
        for app in all_apps:
            # Count by level
            stats["by_level"][app.level] = stats["by_level"].get(app.level, 0) + 1
            
            # Count by goal
            stats["by_goal"][app.goal] = stats["by_goal"].get(app.goal, 0) + 1
            
            # Count by zone
            stats["by_zone"][app.dublin_zone] = stats["by_zone"].get(app.dublin_zone, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error computing stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute statistics"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
