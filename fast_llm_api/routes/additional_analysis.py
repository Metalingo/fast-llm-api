import math
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from fast_llm_api.services.additional_analyis import evaluate_all_entries_story_plagiarism, cross_check_similarity
from fast_llm_api.services.models import OneStudentEntry
from datetime import datetime

# Global Variables
THRESHOLD_FOR_COPYING = 0.2

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for job tracking
additional_analysis_jobs: Dict[str, Dict] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict] = None
    elapsed_time: Optional[float] = None  # Add elapsed time to job status
    created_at: Optional[str] = None  # Add creation timestamp

class SubmitAdditionalAnalysisJobRequest(BaseModel):
    texts: List[OneStudentEntry]
    similarity_threshold: Optional[float] = THRESHOLD_FOR_COPYING

# Background task to run the ranking process
async def process_job(job_id: str, text_entries: List[SubmitAdditionalAnalysisJobRequest], similarity_threshold: float):
    logger.info(f"Starting additional analysis job {job_id} with {len(text_entries)} entries.")
    additional_analysis_jobs[job_id]['status'] = 'running'
    additional_analysis_jobs[job_id]['start_time'] = datetime.now()  # Track start time
    try:
        # Evaluate story plagiarism and cross-check similarity
        result_story_probs = await evaluate_all_entries_story_plagiarism(text_entries)
        result_story_similarity_probs = await cross_check_similarity(text_entries, similarity_threshold)

        result = result_story_similarity_probs

        additional_analysis_jobs[job_id]['status'] = 'completed'
        additional_analysis_jobs[job_id]['result'] = result
        additional_analysis_jobs[job_id]['end_time'] = datetime.now()  # Track end time
        logger.info(f"Additional analysis job {job_id} completed successfully.")
    except Exception as e:
        additional_analysis_jobs[job_id]['status'] = 'failed'
        additional_analysis_jobs[job_id]['result'] = str(e)
        additional_analysis_jobs[job_id]['end_time'] = datetime.now()  # Track end time
        logger.error(f"Additional analysis job {job_id} failed with error: {e}", exc_info=True)

def calculate_elapsed_time(job):
    """
    Calculate elapsed time for running or completed additional_analysis_jobs.
    """
    if 'start_time' in job and job['start_time'] is not None:
        if job.get('end_time') is not None:
            elapsed_time = (job['end_time'] - job['start_time']).total_seconds()
        else:
            elapsed_time = (datetime.now() - job['start_time']).total_seconds()
        return elapsed_time
    return None

# Helper function to format the date in Korean format
def format_time_korean(dt):
    return dt.strftime("%Y년 %-m월 %-d일 %H:%M")

# Endpoint to submit a large list of texts (creates a new job)
@router.post("/submit-job")
async def submit_job(request: SubmitAdditionalAnalysisJobRequest, background_tasks: BackgroundTasks):
    # Generate a unique job_id
    job_id = str(uuid.uuid4())
    
    # Store job in the system
    additional_analysis_jobs[job_id] = {
        'status': 'queued',
        'result': None,
        'start_time': None,
        'end_time': None
    }

    logger.info(f"Job {job_id} has been queued with similarity threshold: {request.similarity_threshold}")
    
    # Queue the task in the background
    background_tasks.add_task(process_job, job_id, request.texts, request.similarity_threshold)

    return {"job_id": job_id, "status": "Job has been queued"}

# Endpoint to retrieve the status of all additional_analysis_jobs
@router.get("/job-status")
async def get_job_status():
    job_statuses = {}
    for job_id, job in additional_analysis_jobs.items():
        creation_time = format_time_korean(job['start_time']) if job['start_time'] else None
        job_statuses[job_id] = {
            'status': job['status'],
            'created_at': creation_time,
            'elapsed_time': calculate_elapsed_time(job)
        }
    logger.info("Returning status for all additional analysis jobs.")
    return job_statuses

# Endpoint to retrieve the status of a specific job
@router.get("/job-status/{job_id}")
async def get_job_status_by_id(job_id: str):
    job = additional_analysis_jobs.get(job_id)
    if job:
        creation_time = format_time_korean(job['start_time']) if job['start_time'] else None
        return {
            'status': job['status'],
            'created_at': creation_time,
            'elapsed_time': calculate_elapsed_time(job),
            'result': job.get('result', None)
        }
    else:
        logger.warning(f"Job {job_id} not found.")
        return {"error": "Job not found"}

# Endpoint to retrieve the result of a specific job by job_id
@router.get("/job-result/{job_id}")
async def get_job_result(job_id: str):
    job = additional_analysis_jobs.get(job_id)
    if job:
        creation_time = format_time_korean(job['start_time']) if job['start_time'] else None
        if job['status'] == 'completed':
            logger.info(f"Returning result for job {job_id}.")
            return {
                "job_id": job_id,
                "result": job['result'],
                "created_at": creation_time,
                "elapsed_time": calculate_elapsed_time(job)
            }
        else:
            return {
                "job_id": job_id,
                "status": job['status'],
                "created_at": creation_time,
                "elapsed_time": calculate_elapsed_time(job)
            }
    else:
        logger.warning(f"Job {job_id} not found when fetching results.")
        return {"error": "Job not found"}
