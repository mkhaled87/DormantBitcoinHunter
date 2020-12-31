# Dormant Bitcoin Hunter

This script will generate bitcoin private keys, extract their bitcoin addresses and compare them with a list of addresses which have large amount of bitcoins (i.e., the [Dormant List](https://bitinfocharts.com/top-100-dormant_8y-bitcoin-addresses.html)). It is hunting for treasure. If it finds a match, it will send an email. This project is based on the repos [Henshall/BitcoinPrivateKeyHunter](https://github.com/Henshall/BitcoinPrivateKeyHunter) and [dodiitt/bitcoin_finder_python](https://github.com/dodiitt/bitcoin_finder_python). Several modifications are made to make it better and correct !

> **_NOTE:_**  This project is developed for fun. There is an almost-zero probability you can find the private key of a given BTC address using your normal computer (or even many average-computing-power machines).

## SETUP

1. Make sure you have `Python 3.x` installed. Install the following packages: `ecdsa`, and `bitcoinlib`.

2. Rename the `env.example` file to `env.py`. It contains a list of variables used by the script. Change the variables related to the email-system to suit your needs as they will be used to send you an email. The variable `MAX_SECONDS` sets the maximum number of seconds the script should run. You should usually set it to some value and then keep calling the script (e.g., using Unix crontab jobs) using the same frequency. The script will use automatically all available CPU cores. To set set an explicit number of processes, change the variable `NUM_INSTANCES`. You can turn-off email sending by setting `SEND_EMAILS` to `False`.

3. In your scheduled run job (or if run manually), call the script with: `python3 hunt.py`. If you are running Linux or MacOS, you may use the script `start.sh`.

4. Running many instances of the script in as many machines as you can, should hopefully increase the probability of catching a match. Do not worry about seeding the RNG. The used `os.urandom()` will [take care of this](https://realpython.com/python-random/#osurandom-about-as-random-as-it-gets).

5. Have Fun ! If you were lucky and got some BTCs, remember to donate a little to any of my addresses below.

## DONATIONS

BTC: 1MKHALEDqXhBzqa86hj8FbDGW5HvDdA5Tq

ETH: 0x14551935EDf4aF06909336084412dd805aE14b26

## DISCLAIMER

The developer shall not be, by any means, held responsible for any damage this software can cause to users of others.
