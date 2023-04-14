#!/bin/bash

set -euo pipefail

pytest --cov --cov-report=html --cov-report=term
