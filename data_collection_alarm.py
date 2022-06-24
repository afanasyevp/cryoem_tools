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
ver='220624'

import smtplib, ssl, os, sys, argparse, time, subprocess, time
from datetime import datetime
from email.message import EmailMessage

def emailSend(port, senderEmail, receiverEmail, smtpServer, password, message, subject, localhost=False):
    # Create a secure SSL context
    if localhost == True:
        port=25 
        senderEmail="krios@ethz.ch"
        msg='Subject: {}\n\n{}'.format(subject, message)
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail(senderEmail, receiverEmail, msg)         
            print("Successfully sent email")
            print(" => An email from the localhost sent")
        except ConnectionRefusedError:
            print ("Error: unable to send email. ConnectionRefusedError: check your localhost settings. ")
    else:
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

#def checkNumOfMov(path, pattern):
#    #returns the number of movies
#    start=time.time()
#    command = 'find %s -name "*%s"| wc -l'%(path, pattern)
#    #print("Running find command in bash")
#    output = subprocess.check_output([command] ,shell=True)
#    #print(output)
#    end=time.time()
#    print(" => Time to estimate the number of movies in seconds: %f"%(end-start))
#    return int(output.decode('utf-8')) 
#def checkFolderSizeBash(path="."):
#    #returns the total size of the folder in GB
#    start=time.time()
#    command = 'du -cs %s'%(path)
#    #print("Running du command in bash")
#    try:
#        output = subprocess.check_output([command] ,shell=True).decode("utf-8").split("\t")[0]
#    except subprocess.CalledProcessError as e:
#        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
#        output=0
#    end=time.time()
#    print(" => Time to estimate the folder size in seconds: %f"%(end-start))
#    return float(output)/1000000000
#More pythonic but slower (same as two commented functions above)... 
def checkFolderSizePython(path="."):
    '''
    Returns the size of the given folder in bytes
    '''
    totalSize = 0
    with os.scandir(path) as it:
        for entry in it:
            #print(entry)
            if entry.is_file():
                totalSize += entry.stat().st_size
                #if entry.name.endswith(pattern) and entry.is_file():
                    #print(entry.name)
            elif entry.is_dir():
                totalSize += checkFolderSizePython(entry.path)
    #print(totalSize)
    return totalSize
def checkNumOfMovPython(path=".", pattern="fractions.tiff"):
    '''
    Returns the number of files ending with the given pattern
    '''
    count=0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                if entry.name.endswith(pattern):
                    #print(entry.name)
                    count+=1
                    #print(count)
            elif entry.is_dir():
                count+=checkNumOfMovPython(entry.path, pattern)
    return count

#def estimateMovieSize(path, pattern):
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
data_collection_alarm.py monitors changes in the folder with the collected data. In case the 
folder size (including subfolders) or the number of movie-files is constant over certain period 
of time (20 min by default), it will send you an email (several email addresses can be used). 
It can also send you an email to confirm the data collection is OK. 

!!! Password and setting up an email account for sending emails:
Option #1:  
- Ask Pavel Afanasyev (by email/DM on twitter) for the password to use the default email account.
Option #2:  
- Create your own yahoo email account to send emails using this script
- If you’re using yahoo mail, go to the "Account Info" => "Account Security" => "App Password" 
- Click on Generate app password => generate a password (in Enter your apps name put any name)
- Copy the password and click "Done". This will be your password to use in this script. 

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
    add('--to', nargs="+", help="Email account to send emails TO - your email(s).")
    add('--smtp', default="smtp.mail.yahoo.com", help="SMTP server. Default: smtp.mail.yahoo.com ")
    add('--port', default="465", help="port for SMTP over SSL. Try 587 if 465 does not work. Default: 465")
    add('--path', default="./", help="Path to the folder with your files. Default value: ./ ")
    add('--time', default="20", help="Time interval in minutes for checking the folder size. Default: 20 mins")
    add('--label', default="fractions.tiff", help="Pattern of names of the movie files to search for")
    add('--restart', default=False, action='store_true', help="Keep sending error emails even if the data collection stops")
    add('--okreport', default=False, action='store_true', help="Keep sending reports that the data is collecting every 7*[time interval] - ~2.5 hours for 20 mins interval")
    add('--delay', default=300, help="Delay in seconds before running the script to make sure some movies are being acquired")
    add('--localhost', default=False, action='store_true', help="Use localhost settings (specific for the ETH Krioses)")
    #parser.add_argument('--no-feature', dest='feature', action='store_false')
    #parser.set_defaults(feature=True)
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    print("Example: data_collection_alarm.py  --to myemail@gmail.com --password mystrongpassword ")
    print(" ")
    #password = input("Type your password and press enter: ")
    senderEmail = args.emailfrom
    receiverEmails = args.to
    #print(receiverEmails)
    if args.to == None:    
        print("\n => ERROR!!! Check your input: Please indicate an email (--to) for sending updates")
        sys.exit(2)
    smtpServer=args.smtp
    password=args.password
    port=args.port
    dataPath=args.path
    dataPathAbs=os.path.abspath(dataPath)
    timeInterval=float(args.time)*60 # in seconds
    if float(args.time) < 0.1:
        print(" => ERROR! Please use --time more than 5 minutes! The program will be terminated")
        sys.exit(2)
    label=args.label
    delay=args.delay

    datetimeStart=now()
    #start=time.time()
    #number=checkNumOfMov(dataPath, label)
    #end=time.time()
    #print(" => Estimation time (in seconds) of the movie number: %f"%(end-start))
    start=time.time()
    number=checkNumOfMovPython(dataPath, label)
    #print("numberPython", numberPython)
    end=time.time()
    print(" => Estimation time (in seconds) of the movie number: %f "%((end-start)))
    start=time.time()
    volume=checkFolderSizePython(dataPath)
    end=time.time()
    print(" => Estimation time (in seconds) of the folder size: %f"%(end-start))
    with open("data_collection_progress.log", "a") as outputFile:
        outputFile.write("%s %i %.3f "%(datetimeStart, number, volume))
    print( " => ", datetimeStart, "Current data size in TB: ", "{:.3f}".format(volume/1000000000000), "Number of movies: ", number, "\n")
    ### messages
    messageStart = '''
    This automatic email is sent to inform about the START of the data collection monitor on %s
    If there are no new files appearing in the %s directory within %s minutes, you will be notified by another email. 
    
    Total size of the folder: %.3f TB
    Total number of the movie files in the folder: %i    
        
    #
    #This message is sent from Python script 
    #https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py
    #version: %s'''%(datetimeStart, dataPathAbs, str(args.time), float(volume/1000000000000), number, ver) 
    subject="DATA COLLECTION MONITOR STARTED [DO NOT REPLY]"
    for email in receiverEmails:
        #print("email:",email)
        emailSend(port, senderEmail, email, smtpServer, password, messageStart, subject, args.localhost)
    print(" => Waiting %s seconds to start the folder size estimation...\n"%delay)
    time.sleep(float(delay)) # wait XX seconds before the first check
    #time.sleep(timeInterval)
    timeCount=0
    while True:
        start=time.time()
        newNumber=checkNumOfMovPython(dataPath, label)
        end=time.time()
        print(" => Estimation time (in seconds) of the movie number: %f "%((end-start)))
        #newVolume=checkFolderSize(dataPath)
        start=time.time()
        newVolume=checkFolderSizePython(dataPath)
        end=time.time()
        print(" => Estimation time (in seconds) of the folder size: %f"%(end-start))
        #print( " => ", datetimeStart, "Current data size in TB: ", newVolume, "Number of movies: ", newNumber)    
        with open("data_collection_progress.log", "a") as outputFile:
            outputFile.write("%s %i %.3f \n"%(now(), number, newVolume))
        if newNumber == number:
            if args.restart == False: statusEmailRestart=' NOT'
            else: statusEmailRestart=''
            messageError = '''    
            This automatic email is sent to inform you about the POTENTIAL ERROR IN THE DATA COLLECTION occured on %s
            
            No changes in the volume size has been registered in the last %s minutes:
            %i movies collected (occupying %.3f TB) in the %s directory. 
            
            #
            #This message is sent from Python script 
            #https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py
            #version: %s'''%(now(), str(args.time), int(newNumber), float(newVolume/1000000000000), dataPathAbs, ver)
            #print(messageError)
            subject='ERROR IN DATA COLLECTION [DO NOT REPLY]'
            for email in receiverEmails:
                emailSend(port, senderEmail, email, smtpServer, password, messageError, subject, args.localhost)    
            if args.restart == False:
                print('''=> ERROR!!! The script is terminated! POTENTIAL ERROR IN THE DATA COLLECTION occured on %s
                No changes in the volume size has been registered in the last %s minutes:
                %i movies collected (occupying %.3f TB) in the %s directory. 
                An email is sent to %s'''%(now(), str(args.time), int(newNumber), float(newVolume/1000000000000), dataPathAbs, email))
                sys.exit(2)
            else:
                time.sleep(timeInterval*7)
        else:
            if newVolume==0: 
                print(" => ", now(), "Current data size in TB: could not be determined (error occured at estimation)", "Number of movies: ", number, "\n => The data_collection_alarm.py script is still running...\n")
            else: 
                number = newNumber
                print(" => ", now(), "Current data size in TB: ", "{:.3f}".format(volume/1000000000000), "Number of movies: ", number, "\n => The data_collection_alarm.py script is still running...\n")
                if args.okreport == True:
                    subject="OK DATA COLLECTION [DO NOT REPLY]"
                    messageOK='''
                    This automatic email is sent to inform you about the GOOD PROGRESS of the data collection monitor on %s
                    If there are no new files appearing in the %s directory within %s minutes, you will be notified by another email. 
    
                    Total size of the folder: %.3f TB
                    Total number of the movie files in the folder: %i    
        
                    #
                    #This message is sent from Python script 
                    #https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py
                    #version %s'''%(now(), dataPathAbs, str(args.time), float(newVolume/1000000000000), number, ver) 
                    timeCount+=1
                    if timeCount % 2 ==0: # to make it less often, increase 7 to 14
                        for email in receiverEmails:
                            emailSend(port, senderEmail, email, smtpServer, password, messageOK, subject, args.localhost)
            time.sleep(timeInterval)    
if __name__ == '__main__':
    main()
