import subprocess
import multiprocessing

def run_script(script_name):
    print(f"Running {script_name}...")
    subprocess.run(["python3", script_name])

if __name__ == "__main__":
    scripts_to_run = ["client.py", "img.py"]
    
    processes = []
    for script in scripts_to_run:
        process = multiprocessing.Process(target=run_script, args=(script,))
        processes.append(process)
        process.start()
    
    for process in processes:
        process.join()
