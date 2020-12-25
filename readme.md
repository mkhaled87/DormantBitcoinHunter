# INFORMATION

This script will guess bitcoin public and private keys and compare them with a list of addresses which have large amount of bitcoin in them ([Dormant List](https://bitinfocharts.com/top-100-dormant_8y-bitcoin-addresses.html)).

It is hunting for treasure :).

If the program finds a matching paid it will send an email.

## SETUP

1. rename the env.example file to env.py (it contains a list of variables which will be used to send you an email)

2. change the variables to suit your needs. 

3. run the program with `python3 bitcoin_finder.py` or set up a job to hit it every few seconds. It currently examines 10000 random private keys and looks for matches which takes much less then a minute in Intel Core i9 9th gen processor.

4. You may need to run the following command: `chmod -R 777 keys-found.txt`. This will make sure your keys-found.txt file is writable. You may even want to run a cron job to constantly change this if you are pulling a later version from github.

Have Fun !
