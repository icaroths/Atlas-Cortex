import os
import subprocess
import json
from pathlib import Path

EVIDENCE_DIR = Path("audit-evidence")
EVIDENCE_DIR.mkdir(exist_ok=True)

def run(cmd, shell=False, cwd=None):
    try:
        res = subprocess.run(cmd, shell=shell, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
        return res.stdout, res.stderr, res.returncode
    except Exception as e:
        return "", str(e), 1

# 1. Higiene do Repo
stdout, _, code = run(["git", "ls-files", "engine/target"])
(EVIDENCE_DIR / "git-ls-files-target.txt").write_text(stdout, encoding="utf-8")

# file command is not natively on windows powershell easily, let's just read the file manually
try:
    with open(".gitignore", "rb") as f:
        content = f.read()
    if b'\x00' in content: # simple UTF-16 check
        git_enc = "UTF-16"
    else:
        git_enc = "UTF-8 Unicode text"
except:
    git_enc = "ERROR"
(EVIDENCE_DIR / "gitignore-encoding.txt").write_text(git_enc, encoding="utf-8")

# 2. Rust
stdout, _, code = run(["cargo", "fmt", "--check"], cwd="engine")
(EVIDENCE_DIR / "cargo-fmt.txt").write_text(stdout + f"\nExit code: {code}", encoding="utf-8")

stdout, stderr, code = run(["cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"], cwd="engine")
(EVIDENCE_DIR / "cargo-clippy.txt").write_text(stdout + stderr + f"\nExit code: {code}", encoding="utf-8")

stdout, stderr, code = run(["cargo", "test", "--release"], cwd="engine")
(EVIDENCE_DIR / "cargo-test.txt").write_text(stdout + stderr + f"\nExit code: {code}", encoding="utf-8")

# Ignorando RUSTSEC-2025-0020 e RUSTSEC-2026-0177 (pyo3 v0.21.2) por quebra de build em versões superiores.
# Documentado em SECURITY.md.
stdout, stderr, code = run(["cargo", "audit", "--ignore", "RUSTSEC-2025-0020", "--ignore", "RUSTSEC-2026-0177"], cwd="engine")
(EVIDENCE_DIR / "cargo-audit.txt").write_text(stdout + stderr + f"\nExit code: {code}", encoding="utf-8")

# 3. Python Security Greps
import re
shell_true_issues = []
os_system_issues = []
for root, _, files in os.walk("scripts"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as f_obj:
                lines = f_obj.readlines()
                for i, line in enumerate(lines):
                    if re.search(r"shell\s*=\s*True", line):
                        shell_true_issues.append(f"{path}:{i+1}:{line.strip()}")
                    if "os.system" in line:
                        os_system_issues.append(f"{path}:{i+1}:{line.strip()}")
(EVIDENCE_DIR / "grep-shell-true.txt").write_text("\n".join(shell_true_issues), encoding="utf-8")
(EVIDENCE_DIR / "grep-os-system.txt").write_text("\n".join(os_system_issues), encoding="utf-8")

# 4. Benchmark Drift
stdout, stderr, code = run(["git", "diff", "--exit-code", "docs/benchmarks"])
(EVIDENCE_DIR / "bench-drift.txt").write_text(stdout + stderr + f"\nExit code: {code}", encoding="utf-8")

# 5. MOC Artifact Drift
run(["python", "scripts/generate_mocs.py"])
stdout_moc, stderr_moc, code_moc = run(["git", "diff", "--exit-code", "docs/core-protocol_benchmark_corpus.moc.json", "docs/Paper_Atlas_Cortex_PT.moc.json"])
(EVIDENCE_DIR / "moc-drift.txt").write_text(stdout_moc + stderr_moc + f"\nExit code: {code_moc}", encoding="utf-8")


# Generate Scorecard Base
scorecard = f"""
P0-01 (target fora do git): {'PASS' if not (EVIDENCE_DIR/'git-ls-files-target.txt').read_text(encoding="utf-8").strip() else 'FAIL'}
P0-02 (.gitignore UTF-8): {'PASS' if 'UTF-8' in git_enc else 'FAIL'}
P0-04 (cargo fmt): {'PASS' if 'Exit code: 0' in (EVIDENCE_DIR/'cargo-fmt.txt').read_text(encoding="utf-8") else 'FAIL'}
P0-05 (cargo clippy): {'PASS' if 'Exit code: 0' in (EVIDENCE_DIR/'cargo-clippy.txt').read_text(encoding="utf-8") else 'FAIL'}
P0-06 (cargo test): {'PASS' if 'Exit code: 0' in (EVIDENCE_DIR/'cargo-test.txt').read_text(encoding="utf-8") else 'FAIL'}
P0-07 (cargo audit): {'PASS' if 'Exit code: 0' in (EVIDENCE_DIR/'cargo-audit.txt').read_text(encoding="utf-8") else 'FAIL'}
P0-10 (sem shell=True): {'PASS' if not shell_true_issues else 'FAIL'}
P0-11 (sem os.system): {'PASS' if not os_system_issues else 'FAIL'}
P0-15 (benchmark sem drift): {'PASS' if 'Exit code: 0' in (EVIDENCE_DIR/'bench-drift.txt').read_text(encoding="utf-8") else 'FAIL'}
P0-16 (MOC artifact sem drift): {'PASS' if 'Exit code: 0' in (EVIDENCE_DIR/'moc-drift.txt').read_text(encoding="utf-8") else 'FAIL'}
"""
print(scorecard)
