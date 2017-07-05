import os
import time
import serial
import gsm

tcpser = serial.Serial('/dev/ttyACM2',115200)
tcpser.timeout = 0

def SendTcpCommand(command,reply='',timeout=100,retry=5,expected_error="ERROR"):#timeout in milli seconds
	rec = ""
	
	while(retry):
		timeout1 = timeout
		retry = retry - 1
		if(gsm.gsmtcpdebug == 1):
			print "GTS>>" + command.replace("\r\n","")
			gsm.logfile.write("GTS>>" + command)
		else:
			gsm.logfile.write("GTS>>" + command)
		tcpser.flushInput()
		tcpser.write(command)
		while(timeout1):
			timeout1 = timeout1 - 1
			time.sleep(0.001)#1 milli second delay
			rec = tcpser.readline()#read a line
			if(rec != "" and rec != "\r\n" and rec != "\r" and rec != "\n"):
				if(gsm.gsmtcpdebug == 1):
					print "GTS<<" + rec.replace("\r\n","")
					gsm.logfile.write("GTS>>" + rec)
				else:
					gsm.logfile.write("GTS>>" + rec)
			if(reply in rec):
				return 0 ,rec#success
			elif(expected_error in rec):
				return 2,rec
		print "Retrying:"+str(retry)
	print "No response"
	return 1,rec #no response

def connecttoserver(port,server):
	SendTcpCommand("AT\r\n",reply="OK")
	SendTcpCommand("ATE0\r\n",reply="OK")
	status,reply = SendTcpCommand("AT\r\n",reply="OK")
	if(status == 0):
		SendTcpCommand("AT+USOCL=0\r\n",reply="OK")#close the socket if connected
		status,reply = SendTcpCommand("AT+USOCR=6\r\n",reply="+USOCR: 0",timeout = 1000)
		if(status == 0):
			status,reply = SendTcpCommand('AT+USOCO=0,"' + server + '",' + str(port) + '\r\n',reply="OK",timeout = 3000)
			if(status == 0):
				status,reply = SendTcpCommand('AT+USODL=0\r\n',reply="CONNECT",timeout = 3000)
				if(status == 0):
					return 0
				else:
					return 1
			else:
				return 1
		else:
			return 1
	else:
		print "No Response"
		return 1

def ReadFromServer():
	
	rec = tcpser.readline()
	print rec
	return rec
	

def WriteToServer(cmd):
	print cmd
	tcpser.write(cmd)
