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
from email.message import EmailMessage
from datetime import datetime
import multiprocessing
import subprocess
import time
import argparse
import sys
import os
import ssl
import smtplib
# Global:
ver = '220718'
nl = '\n'  # new line for f-strings

def emailSend(port, senderEmail, receiverEmail, smtpServer, password, message, subject, localhost=False):
    # Create a secure SSL context
    if localhost == True:
        port = 25
        senderEmail = "krios@ethz.ch"
        msg = 'Subject: {}\n\n{}'.format(subject, message)
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail(senderEmail, receiverEmail, msg)
            print("Successfully sent email")
            print(" => An email from the localhost sent")
        except ConnectionRefusedError:
            print("Error: unable to send email. ConnectionRefusedError: check your localhost settings. ")
    else:
        context = ssl.create_default_context()
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = senderEmail
        msg['To'] = receiverEmail
        with smtplib.SMTP_SSL(smtpServer, port, context=context) as server:
            server.login(senderEmail, password)
            # server.sendmail(senderEmail, receiverEmail, message)
            server.send_message(msg)
            server.quit()
            print(" => %s An e-mail to %s sent: %s" % (now(), receiverEmail, subject))

def now():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def howLong(startSeconds):
    "Returns the running time since the start (in seconds). Usually defined as datetime.now().timestamp()"
    return datetime.now().timestamp()-startSeconds

def checkFolderSizePython(path="."):
    '''
    Returns the size of the given folder in bytes
    '''
    totalSize = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                totalSize += entry.stat().st_size
            elif entry.is_dir():
                totalSize += checkFolderSizePython(entry.path)
    return totalSize

def checkNumOfMovPython(path=".", pattern="fractions.tiff"):
    '''
    Returns the number of files ending with the given pattern
    '''
    count = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                if entry.name.endswith(pattern):
                    count += 1
            elif entry.is_dir():
                count += checkNumOfMovPython(entry.path, pattern)
    return count

def emailText(messageType, start, when_sent, folder, time_int, mov_number, volume, die_time):
    '''Generates text for the email.
    Requires global variables: ver(version) and nl(new line)
    Types of messages:
    1. Start
    2. Error (script continues)
    3. OK
    4. Stop (script terminates)
    5. Finish
    '''
    dt = datetime.now()
    seconds = dt.timestamp()
    running_left = round((die_time*24*60*60-(seconds-start))/3600, 2)
    message = f"{nl}This automatic email is sent to inform you about the "
    if messageType == "Start":
        message += f'START of the data collection monitor on {when_sent}. {nl}{nl}If there are no new files appearing in the {folder} directory within {time_int} minutes, you will be notified by another email. The script will be terminated in {running_left} hours {nl}.'
        subject = "STARTED data colection monitor [do not reply please]"
    elif messageType == "Error":
        message += f'POTENTIAL ERROR IN THE DATA COLLECTION occured on {when_sent}. {nl}{nl}No changes in the volume size has been registered in the last {time_int} minutes. {nl} You will be notified by another email about the data colection progress in {time_int} minutes. The script will be terminated in {running_left} hours. {nl}'
        subject = 'ERROR in data collection [do not reply please]'
    elif messageType == "OK":
        message += f'PROGRESS in the data collection on {when_sent}. {nl}{nl}If there are no new files appearing in the directory within {time_int} minutes, you will be notified by another email. The script will be terminated in {running_left} hours. {nl}'
        subject = "OK data collection [do not reply please]"
    elif messageType == "Stop":
        message += f'POTENTIAL ERROR IN THE DATA COLLECTION occured on {when_sent}. {nl}{nl}No changes in the volume size has been registered in the last {time_int} minutes. The data_collection_alarm.py script will be terminated now. To continue monitoring the process after data collection errors please use --okreport option in data_collection_alarm.py script.  {nl}'
        subject = "ERROR in data collection FINAL email. [do not reply please]"
    elif messageType == "Finish":
        message += f'TERMINATION of the data collection monitor on {when_sent}. {nl}{nl} This happpened after {die_time} day(s) since the beginnig of the monitor of the data collection. To continue monitoring the process, please re-run the data_collection_alarm.py script and consideer using different --die option.{nl}'
        subject = "STOP data collection monitor. FINAL email. [do not reply please]"
    else:
        print(" => Unknown messageType!")
        sys.exit(2)
    message += f'{nl}Folder: {folder} {nl}Total size of the folder: {float(volume/1000000000000):4f} TB {nl} Total number of the movie files: {mov_number}'
    message += f'{nl}{nl}#{nl}#This message is sent from Python script{nl}#https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py{nl}#version: {ver}'
    return message, subject

def progressMessage(when_displayed, mov_number, volume, time_int, messageType):
    #see instructions of the emailText function
    print(f' => {when_displayed} Status: {messageType} {nl}    Current data size: {float(volume/1000000000000):3f} TB {nl}    Number of movies: {mov_number} {nl}    Next message will be displayed in {time_int} minutes {nl}')
    with open("data_collection_progress.log", "a") as outputFile:
        outputFile.write(f'{when_displayed} {mov_number} {float(volume/1000000000000):6f} {nl}')

def main(password, senderEmail, receiverEmails, smtpServer, port, dataPath, timeVar, label, restart, okreport, delay, localhost, die):
    dataPathAbs = os.path.abspath(dataPath)
    timeInterval = timeVar*60  # in seconds
    okreportSeconds = okreport*60  # in seconds
    startSeconds = datetime.now().timestamp()
    number = checkNumOfMovPython(dataPath, label)
    volume = checkFolderSizePython(dataPath)

    # email about the start
    with open("data_collection_progress.log", "a") as outputFile:
        outputFile.write(f'{nl}{nl} => {now()} Started the data_collection_alarm.py with the following parameters: {nl}password: {password} {nl}emailfrom: {senderEmail} {nl}to: {receiverEmails} {nl}smtp: {smtpServer} {nl}port: {port} {nl}path: {dataPath} {nl}timeVar: {timeVar} {nl}label: {label} {nl}restart: {restart} {nl}okreport: {okreport} {nl}delay: {delay} {nl}localhost: {localhost} {nl}die: {die}{nl}{nl} # Date | Time | Numer of files | Size in TB {nl}')
    progressMessage(now(), number, volume, str(timeVar), "START of the script")
    messageStart, subjectStart = emailText('Start', startSeconds, now(), dataPathAbs, str(timeVar), number, volume, die)
    for email in receiverEmails:
        emailSend(port, senderEmail, email, smtpServer, password, messageStart, subjectStart, localhost)
    lastSent = startSeconds  # when the last OK report was sent

    # delay to make sure the procedure is running
    print(f' => {now()} Waiting {delay} seconds to start the folder size estimation...\n')
    time.sleep(delay)
    howlong = howLong(startSeconds)
    while howlong < die*24*60*60:
        newNumber = checkNumOfMovPython(dataPath, label)
        newVolume = checkFolderSizePython(dataPath)
        # if the data collection stops (checking by the number of "label"-files)
        howlong = howLong(startSeconds)
        #print("howlong", howlong)
        if newNumber == number:
            messageError, subjectError = emailText('Error', startSeconds, now(), dataPathAbs, timeVar, newNumber, newVolume, die)
            progressMessage(now(), newNumber, newVolume, str(timeVar), "ERROR in data collection!")
            for email in receiverEmails:
                emailSend(port, senderEmail, email, smtpServer, password, messageError, subjectError, localhost)
                lastSent = datetime.now().timestamp()
            if restart == False:
                print(f'=> The script is terminated! POTENTIAL ERROR IN THE DATA COLLECTION occured on {now()}. {nl} No changes in the volume size has been registered in the last {str(timeVar)} minutes in the {dataPathAbs} directory! {nl}')
                messageStop, subjectStop = emailText('Stop', startSeconds, now(), dataPathAbs, timeVar, newNumber, newVolume, die)
                for email in receiverEmails:
                    emailSend(port, senderEmail, email, smtpServer, password, messageStop, subjectStop, localhost)
                sys.exit(2)
            else:
                number = checkNumOfMovPython(dataPath, label)
                # volume = checkFolderSizePython(dataPath)
        # if everything is fine and the datacollection continues:
        else:
            number = newNumber
            progressMessage(now(), newNumber, newVolume, str(timeVar), "OK")
            # volume= newVolume
            if okreport != 0 and (datetime.now().timestamp()-lastSent) > okreportSeconds:
                messageOK, subjectOK = emailText("OK", startSeconds, now(), dataPathAbs, timeVar, newNumber, newVolume, die)
                for email in receiverEmails:
                    emailSend(port, senderEmail, email, smtpServer,password, messageOK, subjectOK, localhost)
                lastSent = datetime.now().timestamp()
        time.sleep(timeInterval)
        howlong = howLong(startSeconds)

    print(f'{nl} => WARNING! The program ran to its completion after {die} day(s) of running.')
    messageFinish, subjectFinish = emailText("Finish", startSeconds, now(), dataPathAbs, timeVar, newVolume, number, die)
    for email in receiverEmails:
        emailSend(port, senderEmail, email, smtpServer, password, messageFinish, subjectFinish, localhost)
    progressMessage(now(), number, newVolume, timeVar, "END of the script")
    # print(subjectStop)


if __name__ == '__main__':
    output_text = '''
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
Written and tested in python3.8.5 (requires python 3.6 or a later version)
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
=================================================================================================''' % ver
    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--password', help="Password from the email server (see instructions above in the program description)")
    add('--emailfrom', default="cemkgr1@yahoo.com",
        help="Email account to send emails FROM. Default: cemkgr1@yahoo.com")
    add('--to', nargs="+", help="Email account to send emails TO - your email(s).")
    add('--smtp', default="smtp.mail.yahoo.com",
        help="SMTP server. Default: smtp.mail.yahoo.com ")
    add('--port', default="465",
        help="port for SMTP over SSL. Try 587 if 465 does not work. Default: 465")
    add('--path', default="./",
        help="Path to the folder with your files. Default value: ./ ")
    add('--time', default="20",
        help="Time interval in minutes for checking the folder size. Default: 20 mins")
    add('--label', default="fractions.tiff",
        help="Pattern of names of the movie files to search for")
    add('--restart', default=False, action='store_true',
        help="Keep sending error emails even if the data collection stops")
    add('--okreport', default=90,
        help="Keep sending reports that the data is collecting every N mins interval")
    add('--delay', default=300,
        help="Delay in seconds before running the script to make sure some movies are being acquired")
    add('--localhost', default=False, action='store_true',
        help="Use localhost settings (specific for the ETH Krioses)")
    add('--die', default='1', help="Kill program after this number of days")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()

    # inputs check
    if args.to == None:
        print("\n => ERROR!!! Check your input: Please indicate an email (--to) for sending updates")
        print("\nExample: data_collection_alarm.py  --to MYEMAIL1@ethz.ch MYEMAIL2@ethz.ch --password uzsurgjbaxokkmjw --time 20  --okreport 90 --restart --path PATHTOMYDATA --label fractions.tiff --die 1 ")
        sys.exit(2)

    if float(args.time) < 5:
        print(" => ERROR! Please use --time more than 5 minutes! The program will be terminated")
        sys.exit(2)

    print(f'{nl} => {now()} running the script: {nl}data_collection_alarm.py  --to {args.to} --password {args.password} --emailfrom {args.emailfrom} --to {args.to} --smtp {args.smtp} --port {args.port} --path {args.path} --time {args.time} --label {args.label} --restart {args.restart} --okreport {args.okreport} --delay {args.delay} --localhost {args.localhost} --die {args.die}{nl}')
    print(f'{nl} => NOTE! The program will be terminated in {args.die} day(s). To change the running time use --die option {nl}')
    p = multiprocessing.Process(target=main, name="main", args=(args.password, args.emailfrom, args.to, args.smtp, args.port, args.path, float(args.time), args.label, args.restart, float(args.okreport), float(args.delay), args.localhost, float(args.die), ))
    p.start()
    # time.sleep(float(args.die)*60*60*24)
    # p.terminate()
    # p.join

# Bash implementation
# def checkNumOfMov(path, pattern):
#    #returns the number of movies
#    start=time.time()
#    command = 'find %s -name "*%s"| wc -l'%(path, pattern)
#    #print("Running find command in bash")
#    output = subprocess.check_output([command] ,shell=True)
#    #print(output)
#    end=time.time()
#    print(" => Time to estimate the number of movies in seconds: %f"%(end-start))
#    return int(output.decode('utf-8'))
# def checkFolderSizeBash(path="."):
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
# def estimateMovieSize(path, pattern):
#    #Estimates an approximate size of the movie file in bytes
#    command = 'find %s -name "*%s"'%(path, pattern)
#    output = subprocess.check_output([command] ,shell=True)
#    oneMovieName=output.decode('utf-8').split("\n")[0]
#    oneMovieSize=float(os.path.getsize(oneMovieName))
#    print(" => %s file of %4.3f MB was used to estimate the size of the data\n"%(os.path.basename(oneMovieName), oneMovieSize/1000))
#    return oneMovieSize

# More pythonic but slower (same as two commented functions above)...