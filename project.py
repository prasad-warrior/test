import sys
import time
import datetime
import serial
import thread
import os


mcser = serial.Serial('/dev/ttyS0',115200)#communication with microcontroller
mcser.timeout = 0
while(1):
	break
	mcser.write("*CONTROL1#")
	time.sleep(10)

def checkACM():
	print 'Checking ACM'
	if(os.path.exists("/dev/ttyACM0")):
		if(os.path.exists("/dev/ttyACM1")):
			if(os.path.exists("/dev/ttyACM2")):
				return 0
			else:
				return 1
		else:
			return 1		
	else:
		return 1
		
#*********************************check ACM FILES**********************************#
def ACMDetectLoop():
	while(1):
		failCount = 0
		if(checkACM() == 0):
			print 'Usb GSM Found'
			time.sleep(2)
			break
		else:
			print 'Usb GSM Not Found'
			if(failCount > 3):
				failCount = 0
				mcser.write("*APP_RESTART#")
			else:
				mcser.write("*GSM_RESTART#")
				print 'GSM RESTART'
			failCount = failCount + 1
			time.sleep(20)
ACMDetectLoop()

import gsm
import gsmfs
import tcpsoc
import camera

def closeAllPorts():
	gsm.ser.close()
	gsmfs.fsser.close()
	tcpsoc.tcpser.close()
def openAllPorts():
	gsm.ser.open()
	gsmfs.fsser.open()
	tcpsoc.tcpser.open()


#***************************************TCP Task **********************************#
def tcp_task(threadName,delay):
	loop_count = 11
	while(1):
		if(gsm.tcptaskpermission):
			time.sleep(1)
			if(gsm.tcphealthFailCount < 3):
				time.sleep(3)
				print 'TCP Connection Process Started'
				status = tcpsoc.connecttoserver(server = gsm.ftpSERVERIP,port = 6324)
				if(status == 0):
					print 'Conneted to Server'
					gsm.tcpConnectionStatus = 1
					while(1):
						rec = tcpsoc.ReadFromServer()
						
						if("DISCONNECT" in rec):
							print "Disconnect with Server"
							gsm.tcpConnectionStatus = 0
							break
						if("*CONTROL#" in rec):
							print "Control Command Received"
							tcpsoc.WriteToServer("*TS001:CONTROLLING#")
							gsm.controlCommandReceived = 1
						if("*VIDEO_START#" in rec):
							print "Video Start Command Received"
							tcpsoc.WriteToServer("*TS001:VIDEO_START_OK#")
							gsm.ftpLogin=1
							gsm.videoBufferStart = 1
							gsm.ftpFilenameIndex = 1
						if("*VIDEO_STOP#" in rec):
							print "Video Stop Command Received"
							tcpsoc.WriteToServer("*TS001:VIDEO_STOP_OK#")
							gsm.videoBufferStart = 0
							gsm.ftpFilenameIndex  = 1
							gsm.ftpLogout=1
							gsm.cleargsmfilesystem = 1
						if("*HEALTH#" in rec):
							print "Health command"
							gsm.tcphealthFail = 0
						else:
							print "TCP health Fail:" + str(gsm.tcphealthFail)
							gsm.tcphealthFail = gsm.tcphealthFail + 1
						if(gsm.tcphealthFail >= 100):
							print 'TCP server timeout -reconnecting'
							gsm.tcphealthFail = 0
							time.sleep(5)
							tcpsoc.SendTcpCommand("+++",reply="DISCONNECT")
							break
						time.sleep(2)
						if(gsm.controlCommandReceivedDone == 1):
							gsm.controlCommandReceivedDone =0
							tcpsoc.WriteToServer("*TS001:ACK_CONTROL_DONE#")
						#************************SIGNAL CHECK***************************#
						loop_count = loop_count + 1
						if(loop_count > 10):
							loop_count = 0
							gsm.getGsmSignalStrength()
						if(gsm.CameraStatus == 0):
							tcpsoc.WriteToServer("*TS001:CAM NOT FOUND:" + str(gsm.gsmSignalStrength) + "#")
						else:
							tcpsoc.WriteToServer("*TS001:ALL IZ WELL:" + str(gsm.gsmSignalStrength) + "#")
						time.sleep(3)

				else:
					print 'Failed to Connect with Server.. Retring after 5 seconds'
					gsm.tcpConnectionStatus = 0
					gsm.tcphealthFailCount = gsm.tcphealthFailCount + 1
					time.sleep(5)
		else:
			time.sleep(1)
#********************************End of TCP Task **********************************#


#***************************************Camera Task********************************#
def camera_task(threadName,delay):
	print 'Camera Task Started'
	gsm.CameraStatus = camera.checkCam()
	while(1):
		if(gsm.camerataskpermission):
			if(gsm.clearcamerafilesystem == 1):
				gsm.clearcamerafilesystem = 0
				print 'clearing Files'
				for i in range(gsm.fileBufMaxSize):
					os.system('sudo rm r'+ str(i) +'.mp4')
			if(gsm.videoBufferStart == 1 and gsm.CameraStatus == 1):
				if(((gsm.camRecDoneInx1 - gsm.camRecDoneInx) == 1) or ((gsm.camRecDoneInx == gsm.fileBufMaxSize) and (gsm.camRecDoneInx1 == 0))):
					print 'File Buffer ' + str(gsm.fileBufMaxSize) + 'Full'
					time.sleep(5)
				else:
					if(gsm.camRecDoneInx == gsm.fileBufMaxSize):
						gsm.camRecDoneInx = 0
					else:
						if(gsm.camRecDoneInx == 0):
							camera.recordvideo(filename='r'+str(gsm.camRecDoneInx)+'.mp4',timespan = 10)
						else:	
							camera.recordvideo(filename='r'+str(gsm.camRecDoneInx)+'.mp4',timespan = 30)
						gsm.camRecDoneInx = gsm.camRecDoneInx  + 1
			else:
				time.sleep(1)
		else:
			time.sleep(1)
			
#*********************************End of Camera Task*******************************#


#*********************************Gsm File System Task*****************************#
def gsm_fs_task(threadName,delay):
	print 'File System Task Started'
	while(1):
		if(gsm.camerataskpermission):
			
			if(gsm.camRecDoneInx != gsm.camRecDoneInx1):
				if(gsmfs.filesize("") >  1000000):
					gsmfs.storefilesystemtogsm(filename='r'+str(gsm.camRecDoneInx1)+'.mp4')
					gsm.camRecDoneInx1 = gsm.camRecDoneInx1 + 1
					if(gsm.camRecDoneInx1 == gsm.fileBufMaxSize):
						gsm.camRecDoneInx1 = 0
				else:
					print 'No Space on GSM Disk'
					time.sleep(5)
			elif(gsm.cleargsmfilesystem == 1):
				gsm.cleargsmfilesystem = 0
				gsmfs.gsmformat()#delete all the files
			time.sleep(1)
		else:
			time.sleep(1)
	
#**************************End of Gsm File System Task*****************************#	
		
		
#*********************************Basic Initilization******************************#


gsm.Gsminit()

#gsmfs.viewallfiles()
gsmfs.gsmformat()#delete all the files
simFailCount = 0
while(1):
	if(gsm.checkSim()==0):
		break
	simFailCount = simFailCount + 1
	if(simFailCount > 5):
		simFailCount = 0
		closeAllPorts()
		mcser.write("*GSM_RESTART#")
		print 'GSM RESTART'
		time.sleep(30)
		ACMDetectLoop()
		openAllPorts()
		gsm.Gsminit()
	time.sleep(5)
gsm.GPRSStop()
gsm.GPRSStart()

#*********************************Start Threads ***********************************#
thread.start_new_thread(gsm_fs_task,("Thread-1",2,))
thread.start_new_thread(tcp_task,	("Thread-2",2,))
thread.start_new_thread(camera_task,("Thread-3",2,))

#*********************************Main Loop For Ever ******************************#
index=0
loop_count = 0
gsm.ftpFilenameIndex  = 1
gsm.gsmtaskpermission = 1
gsm.tcptaskpermission = 1
gsm.camerataskpermission = 1
CamFailCount = 0
while(1):
	if(gsm.ftpLogin == 1):
		print "ftp Login"
		gsm.GPRSStart()
		gsm.FTPLogin()
		gsm.ftpLogin = 0
	if(gsm.ftpLogout == 1 and gsm.camRecDoneInx1 == gsm.camRecDoneInx2):
		print "ftp Logout"
		gsm.FTPLogout()
		gsm.ftpLogout = 0
	if(gsm.camRecDoneInx1 != gsm.camRecDoneInx2):
		if(gsm.FTPUpload("r" + str(gsm.camRecDoneInx2) + ".mp4","vid_"+str(gsm.ftpFilenameIndex)+".mp4") == 0):
			gsm.ftpFilenameIndex  =  gsm.ftpFilenameIndex + 1
			gsm.camRecDoneInx2 = gsm.camRecDoneInx2 + 1
			if(gsm.camRecDoneInx2 == gsm.fileBufMaxSize):
				gsm.camRecDoneInx2 = 0
		else:
			time.sleep(2)
			print "ftp Re-Login"
		#	gsm.GPRSStop()
			gsm.GPRSStart()
			gsm.FTPLogin()
	time.sleep(1)
	if(gsm.controlCommandReceived == 1):
		gsm.controlCommandReceived = 0
		print '***********************Control 1*********************************'
		mcser.write("*CONTROL1#")
		time.sleep(5)
	rec = mcser.readline()
	print rec
	if("*CONTROL1_DONE#" in rec):
		gsm.controlCommandReceivedDone = 1
	#************************TCP HEALTH CHECK***************************#
	if(gsm.tcphealthFailCount >= 3):
		#gsm.GPRSStop()
		gsm.SendCommand("AT+CFUN=1\r\n" ,"OK",retry=20000)
		gsm.GPRSStart()
		gsm.tcphealthFailCount = 0
	#************************FTP HEALTH CHECK***************************#
	#************************CAM HEALTH CHECK***************************#
	gsm.CameraStatus = camera.checkCam()
	if(gsm.CameraStatus == 0):
		CamFailCount = CamFailCount + 1
		if(CamFailCount > 10):
			CamFailCount = 0
			mcser.write("*CAMERA_RESTART#")
	else:
		CamFailCount = 0
	
	if(checkACM() == 0):
		mcser.write("*APP_HEALTH#")
	print "Loop"
#****************************End  of Main Loop For Ever *****************************#
