import os
import time
def checkCam():
	os.system('sudo ifup eth0 > /dev/null 2>&1')
	time.sleep(3)
	res = os.system("ping -c 1 192.168.1.103 > /dev/null 2>&1")
	if(res == 0):
		print "Camera Found"
		return 1
	else:
		print "Camera Not Found"
		return 0
def recordvideo(filename,timespan=5):
	#/home/pi/Desktop/recording.ts
	os.system('sudo ifup eth0 > /dev/null 2>&1')
	st = 'cvlc --no-audio rtsp://admin:admin@192.168.1.103:554/ --sout=file/mp4:' + filename + ' --stop-time=' + str(timespan) + ' vlc://quit > /dev/null 2>&1'
	print st
	os.system(st)

#checkCam()
