#!/usr/bin/env python3

from west.manifest import Manifest
from west.manifest import ManifestProject
import subprocess

manifest = Manifest.from_file()

repos = ["zephyr"]
for project in manifest.get_projects([]):
    if not manifest.is_active(project):
        continue

    if isinstance(project, ManifestProject):
        continue

    repos.append(project.name)

repos_arg = ",".join(repos)

subprocess.run(["./update_pr.py", "--repos", repos_arg])
