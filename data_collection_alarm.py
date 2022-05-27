#!/usr/bin/env python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-
ver='220528'

import smtplib, ssl, os, sys, threading, argparse, time, subprocess
from datetime import datetime
from email.message import EmailMessage

from matplotlib.pyplot import new_figure_manager

def emailSend(port, senderEmail, receiverEmail, smtpServer, password, message, subject):
    # Create a secure SSL context
    context = ssl.create_default_context()
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = subject
    msg['From'] = senderEmail
    msg['To'] = receiverEmail
    with smtplib.SMTP_SSL(smtpServer, port, context=context) as server:
        server.login(senderEmail, password)
        #server.sendmail(senderEmail, receiverEmail, message)
        server.send_message(msg)
        server.quit()
    print(" => An e-mail to %s sent: %s" %(receiverEmail, subject))

def now():
    now=datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def checkNumOfMov(path, pattern):
    #returns the number of movies and an approximate size
    command = 'find %s -name "*%s"| wc -l'%(path, pattern)
    #print("Running find command in bash")
    output = subprocess.check_output([command] ,shell=True)
    return int(output.decode('utf-8'))
    
def checkFolderSize(path="."):
    #returns the total size of the folder in GB
    command = 'du -cs %s'%(path)
    #print("Running du command in bash")
    output = subprocess.check_output([command] ,shell=True).decode("utf-8").split("\t")[0]
    return float(output)/1000000000
 
#More pythonic but slower... 
#def checkFolderSize(path=".", pattern="fractions.tiff"):
#    '''
#    Checks for the size of the given folder and returns the size and the number of files ending with the given pattern
#    '''
#    totalSize = 0
#    count=0
#    with os.scandir(path) as it:
#        for entry in it:
#            #print(entry)
#            if entry.is_file():
#                totalSize += entry.stat().st_size
#                if entry.name.endswith(pattern) and entry.is_file():
#                    count+=1
#                    #print(entry.name)
#            elif entry.is_dir():
#                totalSize += checkFolderSize(entry.path)[0]
#                count+=1
#    #print(totalSize, count)
#    return totalSize, count
#def estimateSize(path, pattern):
#    #Estimates an approximate size of the movie file in bytes
#    command = 'find %s -name "*%s"'%(path, pattern)
#    output = subprocess.check_output([command] ,shell=True)
#    oneMovieName=output.decode('utf-8').split("\n")[0]
#    oneMovieSize=float(os.path.getsize(oneMovieName))
#    print(" => %s file of %4.3f MB was used to estimate the size of the data\n"%(os.path.basename(oneMovieName), oneMovieSize/1000))
#    return oneMovieSize
 

def main():
    output_text='''
==================================== data_collection_alarm.py ===================================
data_collection_alarm.py monitors changes in the number of movie-files in the folder. In case the 
number of movie-files is constant over certain period of time (20 min by default), 
it will send you an email. It can also send you an email to confirm the data collection is OK. 

!!! Password and setting up an email account for sending emails:
Option #1:  
- Ask Pavel Afanasyev (by email/DM on twitter) for the password to use the default email account.
Option #2:  
- Create your own yahoo email account to send emails using this script
- If you’re using yahoo mail, go to the "Account Info" => "Account Security" => "App Password" 
- Click on Generate app password => generate a password (in Enter your apps name put any name)
- Copy the password and click "Done". THis will be your password to use in this script. 

Restart the script in case of data collection failure.
Check your spam folder after the start of the script - an email indicating the start of the 
monitoring should arrive. 

[version %s]
Written and tested in python3.8.5 (requires python 3.5 or a later version)
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
=================================================================================================''' % ver 

    parser = argparse.ArgumentParser(description="")
    add=parser.add_argument
    add('--password', help="Password from the email server (see instructions above in the program description)")
    add('--emailfrom', default="cemkgr1@yahoo.com", help="Email account to send emails FROM. Default: cemkgr1@yahoo.com")
    add('--to', default="youremail@mail.com", help="Email account to send emails TO - your email(s).")
    add('--smtp', default="smtp.mail.yahoo.com", help="SMTP server. Default: smtp.mail.yahoo.com ")
    add('--port', default="465", help="port for SMTP over SSL. Try 587 if 465 does not work. Default: 465")
    add('--path', default="./", help="Path to the folder with your files. Default value: ./ ")
    add('--time', default="20", help="Time interval in minutes for checking the folder size. Default: 20 mins")
    add('--label', default="fractions.tiff", help="Pattern of names of the movie files to search for")
    add('--restart', default=False, action='store_true', help="Keep sending error emails even if the data collection stops")
    add('--okreport', default=False, action='store_true', help="Keep sending reports that the data is collecting every 7*[time interval] - ~2.5 hours for 20 mins interval")
    #parser.add_argument('--no-feature', dest='feature', action='store_false')
    #parser.set_defaults(feature=True)
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    print("Example: data_collection_alarm.py  --to myemail@gmail.com --password mystrongpassword ")
    print(" ")
    #password = input("Type your password and press enter: ")
    senderEmail = args.emailfrom
    receiverEmail = args.to
    smtpServer=args.smtp
    password=args.password
    port=args.port
    dataPath=args.path
    dataPathAbs=os.path.abspath(dataPath)
    timeInterval=int(args.time)*60 # in seconds
    if int(args.time) < 20:
        print(" => ERROR! Please use --time more than 10 minutes! The program will be terminated")
        sys.exit(2)
    label=args.label

    datetimeStart=now()
    number=checkNumOfMov(dataPath, label)
    volume=checkFolderSize(dataPath)
    with open("data_collection_progress.log", "a") as outputFile:
        outputFile.write("%s %i %.3f "%(datetimeStart, number, volume))
    print( " => ", datetimeStart, "Current data size in TB: ", "{:.3f}".format(volume), "Number of movies: ", number)
    ### messages
    messageStart = '''
    This email is sent to inform about the START of the data collection monitor on %s
    If there are no new files appearing in the %s directory within %i minutes, you will be notified by another email. 
    
    Total size of the folder: %.3f TB
    Total number of the movie files in the folder: %i    
        
    #
    #This message is sent from Python script 
    https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py'''%(datetimeStart, dataPathAbs, int(args.time), volume, number) 
    subject="DATA COLLECTION MONITOR STARTED"
    emailSend(port, senderEmail, receiverEmail, smtpServer, password, messageStart, subject)
    time.sleep(120) # wait 2 mins before the first check
    #time.sleep(timeInterval)
    timeCount=0
    while True:
        newNumber=checkNumOfMov(dataPath, label)
        newVolume=checkFolderSize(dataPath)
        #print( " => ", datetimeStart, "Current data size in TB: ", newVolume, "Number of movies: ", newNumber)    
        with open("data_collection_progress.log", "a") as outputFile:
            outputFile.write("%s %i %.3f "%(now(), number, volume))
        if newNumber == number:
            if args.restart == False: statusEmailRestart=' NOT'
            else: statusEmailRestart=''
            messageError = '''    
            This email is sent to inform you about the POTENTIAL ERROR IN THE DATA COLLECTION occured on %s
            
            No changes in the volume size has been registered in the last %i minutes:
            %i movies collected (occupying %.3f TB) in the %s directory. 
            
            You WILL%s receive another email in %i minutes. 
            #
            #This message is sent from Python script 
            https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py'''%(now(), int(args.time), int(newNumber), newVolume, dataPathAbs, statusEmailRestart,  int(args.time))
            #print(messageError)
            subject='ERROR IN DATA COLLECTION'
            emailSend(port, senderEmail, receiverEmail, smtpServer, password, messageError, subject)
            if args.restart == False:
                print('''=> ERROR!!! The script is terminated! POTENTIAL ERROR IN THE DATA COLLECTION occured on %s
                No changes in the volume size has been registered in the last %i minutes:
                %i movies collected (occupying %.3f TB) in the %s directory. 
                An email is sent to %s'''%(now(), int(args.time), int(newNumber), newVolume, dataPathAbs, receiverEmail))
                sys.exit(2)
        else: 
            number = newNumber
            print(" => ", now(), "Current data size in TB: ", newVolume, "Number of movies: ", number, "\n => The data_collection_alarm.py script is still running...\n")
            if args.okreport == True:
                subject="OK DATA COLLECTION"
                messageOK='''
                This email is sent to inform about the GOOD PROGRESS of the data collection monitor on %s
                If there are no new files appearing in the %s directory within %i minutes, you will be notified by another email. 
    
                Total size of the folder: %.3f TB
                Total number of the movie files in the folder: %i    
        
                #
                #This message is sent from Python script 
                https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py'''%(now(), dataPathAbs, int(args.time), newVolume, number) 
                timeCount+=1
                if timeCount % 7 ==0: # to make it less often, increase 7 to 14
                    emailSend(port, senderEmail, receiverEmail, smtpServer, password, messageOK, subject)
        time.sleep(timeInterval)    


if __name__ == '__main__':
    main()
