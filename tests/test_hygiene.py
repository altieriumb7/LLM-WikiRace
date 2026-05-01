import subprocess

def test_no_tracked_generated_dirs():
    out=subprocess.run(['git','ls-files'],capture_output=True,text=True).stdout
    assert 'outputs/' not in out and 'logs/' not in out and 'deprecated/' not in out
