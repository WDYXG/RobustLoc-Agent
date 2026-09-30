"""Final benchmark is guarded by method freeze, never accessible via research."""
import subprocess
import sys
if __name__=='__main__': subprocess.run([sys.executable,'agent.py','finalize'],check=True)
