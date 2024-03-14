#!/usr/bin/bash

#
# Script that loads the python ctf environment.
#

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check that 'ctf-env' is not a file.
if [ -f "ctf-env" ]
then
    printf "${RED}'ctf-env' must be a directory, not a file. Remove it with 'rm ctf-env' and try again.${NC}\n"
    return
fi

# Check if the 'ctf-env' environment was already created
if [ -d "ctf-env" ] 
then
    # Check that it is a valid python environment
    if ! [ -f "ctf-env/bin/activate" ]
    then
        printf "${RED}'ctf-env' does not appear to be a valid python environment. Remove it with 'rm -rf ctf-env' and try again.${NC}\n"
        return
    fi
    printf "Virtual environment already exists, reusing...\n" 
else
  # Create the environment
  printf "${GREEN}Creating virtual environment in 'ctf-env'.${NC}\n"
  python3 -m venv ctf-env
fi

# Activate the environment
source ctf-env/bin/activate

# Make sure the required libraries are installed
pip install pymunk==6.5.1
pip install pygame==2.5.0
pip install pycodestyle
