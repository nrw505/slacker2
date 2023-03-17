#!/bin/bash

set -euo pipefail

coverage run --source=. -m pytest

coverage html

