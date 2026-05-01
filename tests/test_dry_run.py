import subprocess, sys

def test_dry_run_ok():
    r=subprocess.run([sys.executable,'scripts/run_phase2_ablations.py','--dry-run'],capture_output=True,text=True)
    assert r.returncode==0
