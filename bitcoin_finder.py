#!/usr/bin/env python3

# needed python libs
import os
import time
import ecdsa
import sys
import smtplib
import binascii
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
def main(num_seconds):
    i = 0
    start = time.time()
    while ((time.time() - start)) < num_seconds:
        private_key = priv_key()
        key = HDKey(private_key)
        address = key.address()
    
        # override for testing
        #if i == 0:
        #    address = '1BamMXZBPLMwBT3UdyAAKy3ctGDbXNKoXk'
        #if i == 0:
        #    print("Started with private key: " + private_key)
        #    print("Its address: " + address)

        i = i + 1
        for item in addresses.addresses:        # Second Example
            if address == item:
                try:
                    balance = str((Service().getbalance(address))/10e7) + " BTC"
                except Exception as e:
                    balance = "UNKNOWN"

                lucky_text  = "--------------------------------------\n"
                lucky_text += "FOUND LUCKY PAIR:\n" 
                lucky_text += "PRIVATE KEY = " + private_key + "\n"
                lucky_text += "ADDRESS = " + address + "\n"
                lucky_text += "BALANCE = " + balance + "\n"
                lucky_text += "--------------------------------------\n"

                try:
                    send(lucky_text)
                except Exception as e:
                    print("Sending email failed.")

                fl = open(env.OUT_FILE, "a")
                fl.write(lucky_text)
                fl.close()

    print("Finished " + str(i) + " random private keys in " + str((time.time() - start)) + " seconds.")

if __name__ == '__main__':
    num_seconds = 55
    main(num_seconds)
