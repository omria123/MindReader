#!/bin/bash
  
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."


function main {
    python -m virtualenv .env --prompt "[Mind Reader] "
    find .env -name site-packages -exec bash -c 'echo "../../../../" > {}/self.pth' \;
    .env/bin/pip install -U pip
    .env/bin/pip install -r requirements.txt
	cp scripts/run-pipeline.sh .env/bin/run-pipeline
	chmod +x .env/bin/run-pipeline
}


main "$@"

