#!/bin/bash

set -euo pipefail

bandit -c pyproject.toml -r slacker
