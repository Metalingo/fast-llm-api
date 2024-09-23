import subprocess
import time
import signal
import os
import sys

def start_server():
    """
    Start the FastAPI server in a separate process.
    """
    # Start the FastAPI server using Uvicorn
    server_process = subprocess.Popen(
        ["uvicorn", "fast_llm_api.main:app", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return server_process

def run_tests():
    """
    Run pytest tests.
    """
    result = subprocess.run(["pytest", "tests/"], stdout=sys.stdout, stderr=sys.stderr)
    return result.returncode

def stop_server(server_process):
    """
    Stop the FastAPI server.
    """
    # Terminate the server process
    os.kill(server_process.pid, signal.SIGTERM)
    server_process.wait()

if __name__ == "__main__":
    print("Starting FastAPI server...")
    server_process = start_server()
    
    # Give the server a few seconds to start up
    time.sleep(3)

    try:
        print("Running tests...")
        test_exit_code = run_tests()
    finally:
        print("Shutting down FastAPI server...")
        stop_server(server_process)
    
    sys.exit(test_exit_code)
