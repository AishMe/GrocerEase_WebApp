#! /bin/sh
echo "=================================================================="
echo "Welcome to the setup. This will setup the local virtual env."
echo "And then it will install all the required python libraries."
echo "You can re-run this without any issues."
echo "------------------------------------------------------------------"

if [ -d ".env" ];
then 
	echo "Enabling virtual env"
else
	echo "No virtual env. Please run setup.sh first"
	exit N
fi

# Activate virtual env
. .env/bin/activate

export ENV=development
python main.py

# Work done. So deactivate the virtual env
deactivate