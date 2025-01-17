import math
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from fast_llm_api.services.content_rank.elo_fight_generator import generate_elo_results
from fast_llm_api.services.models import OneStudentEntry
from datetime import datetime

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for job tracking
jobs: Dict[str, Dict] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict] = None
    elapsed_time: Optional[float] = None  # Add elapsed time to job status
    created_at: Optional[str] = None  # Add creation timestamp


class SubmitJobRequest(BaseModel):
    texts: List[OneStudentEntry]
    num_folds: Optional[int]

# Background task to run the ranking process
async def process_job(job_id: str, student_entries: List[OneStudentEntry], num_folds: int):
    logger.info(f"Starting job {job_id} with {len(student_entries)} entries and {num_folds} folds.")
    jobs[job_id]['status'] = 'running'
    jobs[job_id]['start_time'] = datetime.now()  # Track start time
    try:
        # Asynchronous AI ranking operation
        result = await generate_elo_results(student_entries, num_folds)
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['result'] = result
        jobs[job_id]['end_time'] = datetime.now()  # Track end time
        logger.info(f"Job {job_id} completed successfully.")
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['result'] = str(e)
        jobs[job_id]['end_time'] = datetime.now()  # Track end time
        logger.error(f"Job {job_id} failed with error: {e}", exc_info=True)

def recommend_num_folds(num_texts, reduction_factor=0.20):
    """
    Recommend the number of folds based on the number of bots and a reduction factor
    that accounts for the initial scores already providing some guidance.
    """
    base_folds = math.log2(num_texts)
    adjusted_folds = base_folds * (1 - reduction_factor)
    return max(1, round(adjusted_folds))  # Ensure at least 1 fold

def calculate_elapsed_time(job):
    """
    Calculate elapsed time for running or completed jobs.
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
async def submit_job(request: SubmitJobRequest, background_tasks: BackgroundTasks):
    # Generate a unique job_id
    job_id = str(uuid.uuid4())
    
    # Store job in the system
    jobs[job_id] = {
        'status': 'queued',
        'result': None,
        'start_time': None,
        'end_time': None
    }

    folds = request.num_folds
    if folds is None:
        folds = recommend_num_folds(len(request.texts))

    logger.info(f"Job {job_id} has been queued with {folds} folds.")
    
    # Queue the task in the background
    background_tasks.add_task(process_job, job_id, request.texts, folds)

    return {"job_id": job_id, "status": "Job has been queued"}

# Endpoint to retrieve the status of all jobs
@router.get("/job-status")
async def get_job_status():
    job_statuses = {}
    for job_id, job in jobs.items():
        creation_time = format_time_korean(job['start_time']) if job['start_time'] else None
        job_statuses[job_id] = {
            'status': job['status'],
            'created_at': creation_time,
            'elapsed_time': calculate_elapsed_time(job)
        }
    logger.info("Returning status for all jobs.")
    return job_statuses

# Endpoint to retrieve the status of a specific job
@router.get("/job-status/{job_id}")
async def get_job_status_by_id(job_id: str):
    job = jobs.get(job_id)
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
    job = jobs.get(job_id)
    if job:
        creation_time = format_time_korean(job['start_time']) if job['start_time'] else None
        if job['status'] == 'completed':
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
