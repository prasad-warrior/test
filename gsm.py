import time
import serial
import re


ser = serial.Serial('/dev/ttyACM0',115200)
ser.timeout = 0

#************************    Flags    ****************************/
gsmdebug = 1
gsmfsdebug = 1
gsmtcpdebug = 1

gsmAPN		=	"airtelgprs.com"
ftpSERVER	=	"ftp.filegenie.com"
ftpSERVERIP	=	"49.207.20.11"
ftpUSER		=	"prasadtest"
ftpPASSWORD	=	"prasadtest"


gsmSignalStrength=0
controlCommandReceived = 0
videoBufferStart = 0
tcpConnectionStatus = 0
ftpLogin=0
ftpLogout=0
ftpFilenameIndex = 0

tcphealthFailCount = 0
tcphealthFail = 0
ftphealthFail = 0
cleargsmfilesystem = 1
clearcamerafilesystem = 1

fileBufMaxSize 		= 10
fileGsmBufMaxSize 	= 8

camRecDone 			= 	[]
camRecDoneInx 		= 	0
camRecDoneInx1 		= 	0
camRecDoneInx2 		= 	0

fileToGsmDone		=	[]
fileToGsmDoneInx	=	0
fileToGsmDoneInx1	=	0

gsmToFtpDoneInx		=	0

CameraStatus = 0
tcptaskpermission = 0
camerataskpermission = 0
gsmfstaskpermission = 0

for i in range(fileBufMaxSize):
	camRecDone.append(0)

for i in range(fileGsmBufMaxSize):
	fileToGsmDone.append(0)

logfile = open('log.txt','w+')
#************************    Functions    ************************/

def SendCommand(command,reply='',timeout=100,retry=5,expected_error="ERROR"):#timeout in milli seconds
	rec = ""
	
	while(retry):
		timeout1 = timeout
		retry = retry - 1
		if(gsmdebug == 1):
			print "GSM>>" + command.replace("\r\n","")
			logfile.write("GSM>>" + command)
		else:
			logfile.write("GSM>>" + command)
		ser.flushInput()
		ser.write(command)
		while(timeout1):
			timeout1 = timeout1 - 1
			time.sleep(0.001)#1 milli second delay
			rec = ser.readline()#read a line
			if(rec != "" and rec != "\r\n" and rec != "\r" and rec != "\n"):
				if(gsmdebug == 1):
					print "GSM<<" + rec.replace("\r\n","")
					logfile.write("GSM>>" + rec)
				else:
					logfile.write("GSM>>" + rec)
			if(reply in rec):
				return 0 ,rec#success
			elif(expected_error in rec):
				return 2,rec
		print "Retrying:"+str(retry)
		time.sleep(1)
	print "No response"
	return 1,rec #no response

def Gsminit():
	ser.flushInput()
	SendCommand("AT\r\n","OK")
	SendCommand("ATE0\r\n","OK")
	#gsmfs.SendFsCommand("ATE0\r\n",reply="OK")
	#tcpsoc.SendTcpCommand("ATE0\r\n",reply="OK")
	SendCommand("AT+CMGF=1\r\n","OK")
	SendCommand("AT+CMEE=2\r\n","OK")
	getGsmSignalStrength()
	print "gsmSignalStrength:"+str(gsmSignalStrength)
	
def checkSim():
	status,replay = SendCommand("AT+CPIN?\r\n" ,"+CPIN: READY")
	if(status == 0):
		print "Sim Detected"
	else:
		print "Sim Not Detected"
	return status
	
def FTPLogin():
	SendCommand('AT+UFTP=0,"' + ftpSERVERIP 	+ '"\r\n',"OK")
	#SendCommand('AT+UFTP=1,"' + ftpSERVER 	+ '"\r\n',"OK")
	SendCommand('AT+UFTP=2,"' + ftpUSER	 	+ '"\r\n',"OK")
	SendCommand('AT+UFTP=3,"' + ftpPASSWORD 	+ '"\r\n',"OK")
	SendCommand("AT+UFTP=5,0\r\n" ,"OK")
	SendCommand("AT+UFTP=6,1\r\n" ,"OK")
	SendCommand("AT+UFTP=7,21\r\n","OK")
	SendCommand("AT+UFTP=8,0\r\n" ,"OK")
	SendCommand("AT+UFTPC=1\r\n" ,"+UUFTPCR: 1,1",timeout = 15000,retry = 5)			
		
def FTPLogout():	
	SendCommand("AT+UFTPC=0\r\n" ,"+UUFTPCR: 0,1",timeout = 5000,expected_error = "+UUFTPCR: 0,0")
	
def CheckGPRS():
	status,reply = SendCommand("AT+UPSND=0,8\r\n","+UPSND: 0,8,1",expected_error="+UPSND: 0,8,0")
	if(status  == 0):
		return 1
	if(status == 2):
		return 0
	return 0
	
def GPRSStart():
	retry =5
	while(retry):
		retry = retry - 1
		status = CheckGPRS()
		if(status == 0):#expected error no internet
			SendCommand('AT+UPSD=0,1,"'+gsmAPN+'"\r\n',"OK")
			#connect to Intenet
			status,reply = SendCommand('AT+UPSDA=0,3\r\n',"OK",timeout=20000)
			if(status == 0):
				print 'Internet connected'
				return 0
			time.sleep(1)

			print 'Problem wile conneccting internet'
			return 1
		if(status == 1):
			print 'Internet already connected'

def GPRSStop():
	status = CheckGPRS()
	if(status == 1):#expected error no internet
		#disconnect to Intenet
		SendCommand('AT+UPSDA=0,4\r\n',"OK",timeout=20000)
		print 'Internet disconnected'
	if(status == 0):
		print 'Internet already disconnected'

def getGsmSignalStrength():
	global gsmSignalStrength
	status,reply = SendCommand("AT+CSQ\r\n","+CSQ")
	if(status == 0):
		gsmSignalStrength = int(re.search(r'\d+',reply).group())
		

def FTPUpload(filenamelocal,filenameremote):
	filesizeinbytes = 0
	status,reply = SendCommand('AT+ULSTFILE=2,"' + filenamelocal + '"\r\n',"+ULSTFILE: ",timeout = 5000)
	if(status == 0):
		out = reply.replace("+ULSTFILE: ","")
		filesizeinbytes = int(out)
		print "filesizeinbytes:" + str(filesizeinbytes)
	if(filesizeinbytes > 1 and filesizeinbytes < 3*1024*1024):
		status,reply = SendCommand('AT+UFTPC=5,"' + filenamelocal + '","' + filenameremote + '"' + '\r\n' ,"+UUFTPCR: 5,1",expected_error="+UUFTPCR: 5,0",timeout = 60000)
		if(status == 0):
			return 0
		else:
			print "Upload "+ filenameremote +" Fail"
			return 1
	else:
		print 'no file or error'
		return 1

#Gsminit()
#GPRSStart()
