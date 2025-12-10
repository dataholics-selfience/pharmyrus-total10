"""
Batch Processing Service for Pharmyrus Patent Search
Version: 3.1.0
Handles multiple molecule searches with job tracking and rate limiting
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

from .pipeline_service import PipelineService


class BatchStatus(str, Enum):
    """Status states for batch jobs"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MoleculeJob:
    """Individual molecule search job within a batch"""
    molecule_name: str
    status: BatchStatus = BatchStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data


@dataclass
class BatchJob:
    """Batch job containing multiple molecule searches"""
    batch_id: str
    molecules: List[str]
    country_filter: Optional[str] = None
    limit: int = 10
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jobs: Dict[str, MoleculeJob] = field(default_factory=dict)
    total_molecules: int = 0
    completed_count: int = 0
    failed_count: int = 0
    progress_percentage: float = 0.0
    estimated_time_remaining_seconds: float = 0.0
    
    def __post_init__(self):
        """Initialize jobs for each molecule"""
        self.total_molecules = len(self.molecules)
        for mol in self.molecules:
            self.jobs[mol] = MoleculeJob(molecule_name=mol)
    
    def update_progress(self):
        """Update progress metrics"""
        completed = sum(1 for j in self.jobs.values() 
                       if j.status in [BatchStatus.COMPLETED, BatchStatus.FAILED])
        self.completed_count = sum(1 for j in self.jobs.values() 
                                  if j.status == BatchStatus.COMPLETED)
        self.failed_count = sum(1 for j in self.jobs.values() 
                               if j.status == BatchStatus.FAILED)
        
        if self.total_molecules > 0:
            self.progress_percentage = (completed / self.total_molecules) * 100
            
        # Estimate time remaining
        if completed > 0 and self.started_at:
            elapsed = (datetime.now() - self.started_at).total_seconds()
            avg_time_per_job = elapsed / completed
            remaining_jobs = self.total_molecules - completed
            self.estimated_time_remaining_seconds = avg_time_per_job * remaining_jobs
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'batch_id': self.batch_id,
            'molecules': self.molecules,
            'country_filter': self.country_filter,
            'limit': self.limit,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_molecules': self.total_molecules,
            'completed_count': self.completed_count,
            'failed_count': self.failed_count,
            'progress_percentage': round(self.progress_percentage, 2),
            'estimated_time_remaining_seconds': round(self.estimated_time_remaining_seconds, 1),
            'jobs': {mol: job.to_dict() for mol, job in self.jobs.items()}
        }


class BatchService:
    """Service for managing batch patent searches"""
    
    def __init__(self, max_concurrent: int = 3, batch_size: int = 5):
        """
        Initialize batch service
        
        Args:
            max_concurrent: Maximum concurrent molecule searches
            batch_size: Number of WO patents to process per batch
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.jobs: Dict[str, BatchJob] = {}
        self.pipeline = PipelineService()
        
    def create_batch(self, molecules: List[str], country_filter: Optional[str] = None, 
                    limit: int = 10) -> str:
        """
        Create a new batch job
        
        Args:
            molecules: List of molecule names to search
            country_filter: Optional country filter (BR_US_JP)
            limit: Max WO patents per molecule
            
        Returns:
            batch_id: Unique identifier for the batch
        """
        batch_id = f"batch_{uuid.uuid4().hex[:12]}_{int(time.time())}"
        
        batch = BatchJob(
            batch_id=batch_id,
            molecules=molecules,
            country_filter=country_filter,
            limit=limit
        )
        
        self.jobs[batch_id] = batch
        
        return batch_id
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """
        Get current status of a batch job
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Batch status dictionary or None if not found
        """
        batch = self.jobs.get(batch_id)
        if not batch:
            return None
        
        batch.update_progress()
        return batch.to_dict()
    
    def get_batch_results(self, batch_id: str) -> Optional[Dict]:
        """
        Get results of a completed batch job
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Batch results with all molecule data or None if not found
        """
        batch = self.jobs.get(batch_id)
        if not batch:
            return None
        
        return {
            'batch_id': batch_id,
            'status': batch.status,
            'completed_count': batch.completed_count,
            'failed_count': batch.failed_count,
            'results': {
                mol: job.result for mol, job in batch.jobs.items() 
                if job.result is not None
            },
            'errors': {
                mol: job.error for mol, job in batch.jobs.items() 
                if job.error is not None
            }
        }
    
    async def _process_single_molecule(self, batch: BatchJob, molecule: str):
        """
        Process a single molecule search with rate limiting
        
        Args:
            batch: Parent batch job
            molecule: Molecule name to search
        """
        job = batch.jobs[molecule]
        
        async with self.semaphore:
            try:
                job.status = BatchStatus.PROCESSING
                job.started_at = datetime.now()
                batch.update_progress()
                
                # Execute pipeline search
                result = await self.pipeline.search_molecule(
                    molecule_name=molecule,
                    country_filter=batch.country_filter,
                    limit=batch.limit
                )
                
                job.result = result
                job.status = BatchStatus.COMPLETED
                job.completed_at = datetime.now()
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
                
            except Exception as e:
                job.error = str(e)
                job.status = BatchStatus.FAILED
                job.completed_at = datetime.now()
                if job.started_at:
                    job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            
            finally:
                batch.update_progress()
    
    async def process_batch(self, batch_id: str) -> Dict:
        """
        Process all molecules in a batch concurrently
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            Final batch status
        """
        batch = self.jobs.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        try:
            batch.status = BatchStatus.PROCESSING
            batch.started_at = datetime.now()
            
            # Process all molecules concurrently with rate limiting
            tasks = [
                self._process_single_molecule(batch, molecule)
                for molecule in batch.molecules
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Mark batch as completed
            batch.status = BatchStatus.COMPLETED
            batch.completed_at = datetime.now()
            batch.update_progress()
            
        except Exception as e:
            batch.status = BatchStatus.FAILED
            batch.completed_at = datetime.now()
            raise
        
        return batch.to_dict()
    
    def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel a pending or processing batch
        
        Args:
            batch_id: Batch identifier
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        batch = self.jobs.get(batch_id)
        if not batch:
            return False
        
        if batch.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            return False
        
        batch.status = BatchStatus.CANCELLED
        batch.completed_at = datetime.now()
        return True
    
    def list_batches(self, status_filter: Optional[BatchStatus] = None) -> List[Dict]:
        """
        List all batch jobs
        
        Args:
            status_filter: Optional filter by status
            
        Returns:
            List of batch summaries
        """
        batches = []
        
        for batch_id, batch in self.jobs.items():
            if status_filter and batch.status != status_filter:
                continue
            
            batch.update_progress()
            batches.append({
                'batch_id': batch_id,
                'status': batch.status,
                'total_molecules': batch.total_molecules,
                'completed_count': batch.completed_count,
                'failed_count': batch.failed_count,
                'progress_percentage': round(batch.progress_percentage, 2),
                'created_at': batch.created_at.isoformat(),
                'estimated_time_remaining_seconds': round(batch.estimated_time_remaining_seconds, 1)
            })
        
        return sorted(batches, key=lambda x: x['created_at'], reverse=True)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Remove old completed/failed jobs
        
        Args:
            max_age_hours: Maximum age in hours to keep jobs
        """
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_delete = []
        for batch_id, batch in self.jobs.items():
            if batch.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
                if batch.completed_at and batch.completed_at.timestamp() < cutoff:
                    to_delete.append(batch_id)
        
        for batch_id in to_delete:
            del self.jobs[batch_id]
        
        return len(to_delete)


# Global batch service instance
_batch_service = None


def get_batch_service(max_concurrent: int = 3, batch_size: int = 5) -> BatchService:
    """Get or create global batch service instance"""
    global _batch_service
    if _batch_service is None:
        _batch_service = BatchService(max_concurrent=max_concurrent, batch_size=batch_size)
    return _batch_service
