#!/usr/bin/env python3

# needed python libs
import os
import time
import ecdsa
import sys
import smtplib
import binascii
import multiprocessing
from email.message import EmailMessage
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service

# import our configs
import addresses
import env

# send email
def send(lucky_text):
        text = env.email_text + "\n" + lucky_text
        msg = EmailMessage()
        msg.set_content(text)
        msg['Subject'] = env.subject
        msg['From'] = env.SEND_FROM
        msg['To'] = env.SEND_TO
        s = smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT)
        s.login(env.USER, env.PASS)
        s.send_message(msg)
        s.quit()
        print('Lucky Email sent!')

# generate a private key
def priv_key():
    return binascii.hexlify(os.urandom(32)).decode('utf-8')


# do your job !
def hunter(num_seconds, worker_idx, return_dict):
    local_addresses = addresses.addresses.copy()
    i = 0
    start = time.time()
    while ((time.time() - start)) < num_seconds:
        private_key = priv_key()
        key = HDKey(private_key)
        address = key.address()
    
        # override address for testing
        #if worker_idx == 0 and i == 0:
        #    address = '1BamMXZBPLMwBT3UdyAAKy3ctGDbXNKoXk'

        i = i + 1
        for item in local_addresses:        # Second Example
            if address == item:
                try:
                    balance = str((Service().getbalance(address))/1e8) + " BTC"
                except Exception as e:
                    balance = "UNKNOWN"

                lucky_text  = "--------------------------------------\n"
                lucky_text += "FOUND A LUCKY PAIR:\n" 
                lucky_text += "PRIVATE KEY = " + private_key + "\n"
                lucky_text += "ADDRESS = " + address + "\n"
                lucky_text += "BALANCE = " + balance + "\n"
                lucky_text += "--------------------------------------\n"

                if env.SEND_EMAILS:
                    try:
                        send(lucky_text)
                    except Exception as e:
                        print("Sending email failed.")

                fl = open(env.OUT_FILE, "a")
                fl.write(lucky_text)
                fl.close()
    
    return_dict[worker_idx] = i

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    processes = []
    
    if env.NUM_INSTANCES == 0:
        inst_count = multiprocessing.cpu_count()
    else:
        inst_count = env.NUM_INSTANCES

    for i in range(inst_count):
        p= multiprocessing.Process(target=hunter, args=(env.MAX_SECONDS, i, return_dict))
        processes.append(p)
        p.start()

    total = 0
    for i in range(inst_count):
        processes[i].join()
        proc_ret = return_dict[i]
        total += proc_ret

    rate = total/env.MAX_SECONDS
    print("Total keys in (" + str(env.MAX_SECONDS) + ") seconds: " + str(total) + " keys. Search rate: " + str(rate) + " key/s.")
