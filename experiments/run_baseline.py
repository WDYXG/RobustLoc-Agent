"""Run from repository root: python -m experiments.run_baseline."""
import subprocess
import sys
if __name__=='__main__': subprocess.run([sys.executable,'agent.py','baseline'],check=True)
