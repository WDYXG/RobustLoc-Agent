"""Run one audited candidate round using current research state."""
import subprocess
import sys
if __name__=='__main__': subprocess.run([sys.executable,'agent.py','research','--iterations','1'],check=True)
