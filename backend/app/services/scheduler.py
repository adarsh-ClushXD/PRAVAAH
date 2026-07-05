import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.services.flood_analysis_service import FloodAnalysisService

class AnalysisScheduler:
    """
    Background scheduler to run periodic state-wide flood analysis.
    """
    def __init__(self, interval_seconds: int = 900):
        self.interval_seconds = interval_seconds
        self._running = False
        self._task = None

    def start(self):
        """Start the background scheduling loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"AnalysisScheduler started. Running every {self.interval_seconds // 60} minutes.")

    async def stop(self):
        """Stop the background scheduling loop gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AnalysisScheduler stopped.")

    async def _run_loop(self):
        """The main periodic loop."""
        # Safeguard: Skip running the scheduler loop on Render (production) if provider is local Ollama
        from app.config import get_settings
        settings = get_settings()
        if settings.app_env == "production" and settings.ai_provider == "ollama":
            logger.warning(
                "AnalysisScheduler: Skipping background loop on Render because AI_PROVIDER is set to local 'ollama'. "
                "Set AI_PROVIDER=gemma_api and provide GEMMA_API_KEY to enable background syncs in the cloud."
            )
            return

        # Optional: wait a bit before first run to let the server fully boot
        await asyncio.sleep(10)
        
        while self._running:
            try:
                logger.info("AnalysisScheduler: Triggering scheduled sync_all_districts.")
                service = FloodAnalysisService()
                
                # Create a fresh database session for the background task
                # We manually iterate the generator from get_db_session()
                session_gen = get_db_session()
                db = await session_gen.__anext__()
                
                try:
                    from app.geospatial.district_registry import DistrictRegistry
                    districts = DistrictRegistry.get_all_districts()
                    
                    for district in districts:
                        try:
                            # Run the analysis with delta optimization (force_refresh=False)
                            # The delta check inside run_analysis makes this lightning fast if unchanged
                            await service.run_analysis(district.id, db=db, force_refresh=False)
                            await asyncio.sleep(2)  # small pause to avoid locking DB/CPU
                        except Exception as e:
                            logger.error(f"Scheduler failed to analyze {district.name}: {e}")
                            
                finally:
                    # Ensure DB connection is released
                    try:
                        await session_gen.__anext__()
                    except StopAsyncIteration:
                        pass
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"AnalysisScheduler encountered an error: {e}")
            
            # Sleep until next interval
            if self._running:
                logger.debug(f"AnalysisScheduler: Sleeping for {self.interval_seconds} seconds.")
                await asyncio.sleep(self.interval_seconds)

# Global singleton instance
scheduler = AnalysisScheduler(interval_seconds=900)  # 15 minutes
