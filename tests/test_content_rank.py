'''
Code below doesn't work, WIP. Job fails, even though manually doing POST requests works
'''

import pytest
import httpx
import pandas as pd
import os
import asyncio

# URL of the FastAPI server (assuming it's running locally)
BASE_URL = "http://localhost:8000/content-rank"

# Test data path
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "demo_data.csv")
CSV_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "job_result.csv")


@pytest.fixture(scope="module")
def read_csv_data():
    """
    Fixture to read the sample CSV data before running the tests.
    """
    data = pd.read_csv(CSV_FILE_PATH)
    return data


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def test_submit_job_returning_job_id(read_csv_data):
    """
    Fixture to submit a job to the /submit-job endpoint and return the job_id.
    """
    # Convert the data into the format expected by the API
    texts = [{"id": row.get("id"), "answer": row["Student Text"]} for _, row in read_csv_data.iterrows()]
    
    # Define the payload to send
    payload = {
        "texts": texts,
        "num_folds": 5
    }

    async with httpx.AsyncClient() as client:
        # Send POST request to /submit-job
        response = await client.post(f"{BASE_URL}/submit-job", json=payload)
    
    assert response.status_code == 200
    response_data = response.json()
    assert "job_id" in response_data
    assert response_data["status"] == "Job has been queued"

    # Return the job_id for further tests
    return response_data["job_id"]


async def check_job_status(job_id):
    """
    Poll the job status every 5 seconds until it is completed.
    """
    async with httpx.AsyncClient() as client:
        while True:
            # Send GET request to /job-status/{job_id}
            response = await client.get(f"{BASE_URL}/job-status/{job_id}")
            assert response.status_code == 200  # Ensure we get a valid response
            response_data = response.json()

            status = response_data.get("status")
            print(f"Job {job_id} status: {status}")

            if status == "completed":
                return True
            elif status == "failed":
                return False
            
            # Wait for 5 seconds before checking again
            await asyncio.sleep(5)


async def fetch_job_result(job_id, csv_output_path):
    """
    Fetch the result of a completed job and save it to a CSV file.
    """
    async with httpx.AsyncClient() as client:
        # Send GET request to /job-result/{job_id}
        response = await client.get(f"{BASE_URL}/job-result/{job_id}")
        assert response.status_code == 200  # Ensure we get a valid response
        response_data = response.json()

        # Check if the job result is available
        if response_data.get("status") == "completed":
            result = response_data.get("result")
            if result:
                # Convert result to a DataFrame and save to CSV
                df = pd.DataFrame(result)
                df.to_csv(csv_output_path, index=False)
                print(f"Results saved to {csv_output_path}.")
            else:
                print(f"No result found for job {job_id}.")
        else:
            print(f"Job {job_id} has not completed yet.")


@pytest.mark.asyncio
async def test_check_job_status(test_submit_job_returning_job_id):
    """
    Test checking the status of a submitted job using the job_id, 
    wait until the job completes, and save the result to a CSV file.
    """
    job_id = await test_submit_job_returning_job_id  # Await the fixture

    # Check job status every 5 seconds
    job_completed = await check_job_status(job_id)
    
    if job_completed:
        # Fetch and save the result to a CSV file if the job is completed
        await fetch_job_result(job_id, CSV_OUTPUT_PATH)
    else:
        pytest.fail(f"Job {job_id} failed.")
