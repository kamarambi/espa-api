# Source: https://pymotw.com/2/smtpd/
import smtpd
import asyncore

server = smtpd.DebuggingServer(('127.0.0.1', 25), None)

asyncore.loop()
