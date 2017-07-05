import re
import os
import serial
import time
import gsm

fsser = serial.Serial('/dev/ttyACM1',115200)
fsser.timeout = 0

def SendFsCommand(command,reply='',timeout=100,retry=5,expected_error="ERROR"):#timeout in milli seconds
	rec = ""
	
	while(retry):
		timeout1 = timeout
		retry = retry - 1
		if(gsm.gsmfsdebug == 1):
			print "GFS>>" + command.replace("\r\n","")
			gsm.logfile.write("GFS>>" + command)
		else:
			gsm.logfile.write("GFS>>" + command)
		fsser.flushInput()
		fsser.write(command)
		while(timeout1):
			timeout1 = timeout1 - 1
			time.sleep(0.001)#1 milli second delay
			rec = fsser.readline()#read a line
			if(rec != "" and rec != "\r\n" and rec != "\r" and rec != "\n"):
				if(gsm.gsmfsdebug == 1):
					print "GFS<<" + rec.replace("\r\n","")
					gsm.logfile.write("GFS>>" + rec)
				else:
					gsm.logfile.write("GFS>>" + rec)
			if(reply in rec):
				return 0 ,rec#success
			elif(expected_error in rec):
				return 2,rec
		print "Retrying:"+str(retry)
	print "No response"
	return 1,rec #no response
	
def gsmformat():
	while(1):
		time.sleep(3)
		status,reply = SendFsCommand('AT+ULSTFILE=0\r\n',"+ULSTFILE",timeout = 2000,retry = 5)
		if(status == 0):
			try:
			#filename = re.findall('"(.*)"',reply)[0]
				out = reply.split('"')
				filename = out[1]
			except:
				print 'Exception'
				break
			print filename
			SendFsCommand('AT+UDELFILE="'+filename+'"\r\n',"OK")
		else:
			break
	SendFsCommand('AT+ULSTFILE=1\r\n',"OK",timeout = 2000,retry = 5)

def deletefile(filename):
	SendFsCommand('AT+UDELFILE="'+filename+'"\r\n',"OK")

def filesize(filename):
	if(filename == ""):
		status,reply = SendFsCommand('AT+ULSTFILE=1\r\n',"+ULSTFILE")
	else:
		status,reply = SendFsCommand('AT+ULSTFILE=2,"'+filename+'"\r\n',"+ULSTFILE")
	if(status == 0):
		try:
			res = 0
			res = int(re.findall(r'\b\d+\b',reply)[0])
		except:
			pass
		return res
	else:
		return 0
	
def storefilesystemtogsm(filename):
	filesize = os.stat(filename).st_size
	SendFsCommand('AT+UDWNFILE="' + filename + '",'+ str(filesize) +'\r\n',">")
	fil = open(filename,"rb")
	cnt=0
	#try:
	
	br = fil.read(1024)
	while(br):
		#cnt = cnt + 1
		#print cnt
		fsser.write(br)
		br=fil.read(1024)
	#finally:
	fsser.flushInput()
	fil.close()

def viewallfiles():
	SendFsCommand('AT+ULSTFILE=0\r\n',"OK",timeout=5000,retry = 10)

SendFsCommand("ATE0\r\n",reply="OK")
#viewallfiles()
#viewallfiles()
#gsmformat()
#storefilesystemtogsm("1.pdf")
#time.sleep(0.5)
#viewallfiles()
