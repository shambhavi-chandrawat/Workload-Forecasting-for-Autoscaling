
import subprocess
import sys
from pathlib import Path

# Project root directory
ROOT = Path(__file__).resolve().parent

def main():

    print("\n======================================")
    print(" WORKLOAD FORECASTING FOR AUTOSCALING")
    print("======================================\n")

    # Step 1: Run the workload forecasting pipeline
    print("Step 1: Running project pipeline...\n")

    subprocess.run(
        [sys.executable, str(ROOT / "src" / "pipeline.py")],
        cwd=ROOT,
        check=True
    )

    print("\nPipeline completed successfully!")

    # Step 2: Launch Streamlit dashboard
    print("\nStep 2: Launching Streamlit dashboard...\n")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(ROOT / "app.py")
        ],
        cwd=ROOT,
        check=True
    )


if __name__ == "__main__":
    main()
