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

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from email.message import EmailMessage
from datetime import datetime
import time
import argparse
import sys
import os
import ssl
import smtplib

# Global:
VER = 20240121
PROG="data_collection_alarm.py"
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output

#Defaults
DEF_DELAY_BEFORE_START=300 # 300 in seconds
DEF_MIN_TIME_FOR_CHECK=5 # 5 in minutes
DEF_TIME_BETWEEN_CHECKS=10 # in minutes
DEF_OK_REPORT_TIME=90 # 90 in minutes
DEF_DIE=3 # days to run
DEF_PASSWORD="uzsurgjbaxokkmjw"
DEF_SMTP_SER="smtp.mail.yahoo.com"
DEF_EMAIL_FROM="cemkgr1@yahoo.com"
DEF_PORT=465
DEF_PATH="./"
DEF_LABEL=".tiff"
DEF_ERROR_WAIT_TIME=5 # in minutes

def send_email(port, sender_email, receiver_email, smtp_server, password, message, subject, localhost=False):
    # Create a secure SSL context
    '''
    Sends an email.
    '''
    if not localhost:
        context = ssl.create_default_context()
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email
        try:
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, password)
                server.send_message(msg)
                server.quit()
                print(" => %s An e-mail to %s sent: %s" % (now(), receiver_email, subject))
        except smtplib.SMTPDataError as e:
            print("SMTPDataError: ", e, " \n The program will coninue")
    else:
        port = 25
        sender_email = "krios@ethz.ch"
        msg = 'Subject: {}\n\n{}'.format(subject, message)
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail(sender_email, receiver_email, msg)
            print("Successfully sent email")
            print(" => An email from the localhost sent")
        except ConnectionRefusedError:
            print("Error: unable to send email. ConnectionRefusedError: check your localhost settings. ")
        except smtplib.SMTPException:
            print("Error: unable to send email (smtplib.SMTPServerDisconnected)")
        except SMTPDataError:
            print("Error: unable to send email (SMTPDataError)")
        except smtplib.SMTPServerDisconnected:
            print("Error: unable to send email (smtplib.SMTPServerDisconnected)")

def now():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def how_long(start_seconds):
    '''
    Returns the running time since the start (in seconds). Usually defined as datetime.now().timestamp()
    '''
    return datetime.now().timestamp()-start_seconds

def check_folder_size(path, pattern):
    '''
    Returns the size of the given folder in bytes and the number of corresponding files
    '''
    total_size = 0
    count=0
    with os.scandir(path) as folder_content:
        for item in folder_content:
            if item.is_file() and item.name.endswith(pattern):
                count +=1
                total_size += item.stat().st_size
            elif item.is_dir():
                a, b= check_folder_size(item.path, pattern)
                total_size += a
                count += b
    return total_size, count


def email_text(message_type, start, when_sent, folder, time_int, mov_number, volume, die_time):
    '''
    Generates text for the email.
    Requires global variable: VER(version)
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
    message = f"\nThis automatic email is sent to inform you about the "
    if message_type == "Start":
        message += f'START of the data collection monitor on {when_sent}. \n\nIf there are no new files appearing in the {folder} directory within {time_int} minutes, you will be notified by another email. The script will be terminated in {running_left} hours \n.'
        subject = "STARTED data colection monitor [do not reply please]"
    elif message_type == "Error":
        message += f'POTENTIAL ERROR IN THE DATA COLLECTION occured on {when_sent}. \n\nNo changes in the volume size has been registered in the last {time_int} minutes. \n You will be notified by another email about the data colection progress only if the data collection continues. The script will be terminated in {running_left} hours. \n'
        subject = 'ERROR in data collection [do not reply please]'
    elif message_type == "OK":
        message += f'PROGRESS in the data collection on {when_sent}. \n\nIf there are no new files appearing in the directory within {time_int} minutes, you will be notified by another email. The script will be terminated in {running_left} hours. \n'
        subject = "OK data collection [do not reply please]"
    elif message_type == "Stop":
        message += f'POTENTIAL ERROR IN THE DATA COLLECTION occured on {when_sent}. \n\nNo changes in the volume size has been registered in the last {time_int} minutes. The data_collection_alarm.py script will be terminated now. To continue monitoring the process after data collection errors please use --okreport option in data_collection_alarm.py script.  \n'
        subject = "ERROR in data collection FINAL email. [do not reply please]"
    elif message_type == "Finish":
        message += f'TERMINATION of the data collection monitor on {when_sent}. \n\n This happpened after {die_time} day(s) since the beginnig of the monitor of the data collection. To continue monitoring the process, please re-run the data_collection_alarm.py script and consideer using different --die option.\n'
        subject = "STOP data collection monitor. FINAL email. [do not reply please]"
    else:
        sys.exit(" => Unknown message_type!")
    message += f'\nFolder: {folder} \nTotal size of the folder: {float(volume/1000000000000):4f} TB \n Total number of the appearing files: {mov_number}'
    message += f'\n\n#\n#This message is sent from Python script\n#https://github.com/afanasyevp/cryoem_tools/data_collection_alarm.py\n#version: {VER}'
    return message, subject

def progress_message(when_displayed, file_number, volume, time_int, message_type):
    #see instructions of the email_text function
    time_slot=time_int/60
    print(f" => {when_displayed} Status: {message_type} \n    Current data size: {float(volume/1000000000000):3f} TB \n    Number of files: {file_number}")
    if message_type == "Stop" or  message_type == "END of the script":
        pass
    else:
        print(f"    Next message will be displayed in {time_slot:.1f} minutes \n")
    with open("data_collection_progress.log", "a") as output_file:
        output_file.write(f'{when_displayed} {file_number} {float(volume/1000000000000):6f} \n')

def main(password, sender_email, receiver_emails, smtp_server, port, data_path, time_interval, label, restart, okreport, delay, localhost, die, error_wait_time):
    data_path_abs = os.path.abspath(data_path)
    start_seconds = datetime.now().timestamp()
    volume, number = check_folder_size(data_path, label)

    # email about the start
    with open("data_collection_progress.log", "a") as output_file:
        output_file.write(f'\n\n => {now()} Started the data_collection_alarm.py with the following parameters: \npassword: {password} \nemailfrom: {sender_email} \nto: {receiver_emails} \nsmtp: {smtp_server} \nport: {port} \npath: {data_path} \ntime_interval: {time_interval} \nlabel: {label} \nrestart: {restart} \nokreport: {okreport} \ndelay: {delay} \nlocalhost: {localhost} \ndie: {die}\n\n # Date | Time | Numer of files | Size in TB \n')
    progress_message(now(), number, volume, time_interval, "START of the script")
    message_start, subject_start = email_text('Start', start_seconds, now(), data_path_abs, str(round(time_interval/60)), number, volume, die)
    for email in receiver_emails:
        send_email(port, sender_email, email, smtp_server, password, message_start, subject_start, localhost)
    lastSent = start_seconds  # when the last OK report was sent

    # delay to make sure the procedure is running
    print(f' => {now()} Waiting {delay} seconds to start the folder size estimation...\n')
    time.sleep(delay)
    howlong = how_long(start_seconds)
    error_email_status = False #to prevent multiple emails about the same error

    while howlong < die*24*60*60:
        new_volume, new_number = check_folder_size(data_path, label)
        # if everything is fine and the datacollection continues:
        if new_number != number:
            number = new_number
            error_email_status=False
            progress_message(now(), new_number, new_volume, time_interval, "OK")
            if okreport  and (datetime.now().timestamp()-lastSent) > okreport:
                messageOK, subjectOK = email_text("OK", start_seconds, now(), data_path_abs, time_interval, new_number, new_volume, die)
                for email in receiver_emails:
                    send_email(port, sender_email, email, smtp_server,password, messageOK, subjectOK, localhost)
                lastSent = datetime.now().timestamp()
            time.sleep(time_interval)
        # if the data collection stops (checking by the number of "label"-files)
        else:
            if error_email_status==False:
                error_email_status=True
                progress_message(now(), new_number, new_volume, error_wait_time, "ERROR in data collection!")
                if restart:
                    message_error, subject_error = email_text('Error', start_seconds, now(), data_path_abs, error_wait_time, new_number, new_volume, die)
                    for email in receiver_emails:
                        send_email(port, sender_email, email, smtp_server, password, message_error, subject_error, localhost)
                        lastSent = datetime.now().timestamp()
                    time.sleep(error_wait_time)
                else:
                    print(f' => The script is terminated! POTENTIAL ERROR IN THE DATA COLLECTION occured on {now()}. \n No changes in the volume size has been registered in the last {time_interval/60:.1f} minutes in the {data_path_abs} directory! \n')
                    message_stop, subject_stop = email_text('Stop', start_seconds, now(), data_path_abs, error_wait_time, new_number, new_volume, die)
                    for email in receiver_emails:
                        send_email(port, sender_email, email, smtp_server, password, message_stop, subject_stop, localhost)
                    print(f" => The {PROG} program is completed.")
                    sys.exit(2)
                volume, number  = check_folder_size(data_path, label)
        howlong = how_long(start_seconds)

    print(f'\n => WARNING! The program ran to its completion after {die} day(s) of running.')
    message_finish, subject_finish = email_text("Finish", start_seconds, now(), data_path_abs, time_interval, new_volume, number, die)
    for email in receiver_emails:
        send_email(port, sender_email, email, smtp_server, password, message_finish, subject_finish, localhost)
    progress_message(now(), number, new_volume, time_interval, "END of the script")
    print(f" => The {PROG} program is completed.")

if __name__ == '__main__':
    output_text = f"""
=================================== {PROG} ===================================
data_collection_alarm.py monitors changes in the folder with the collected data. In case the
folder size (including subfolders) or the number of appearing files is constant over certain period
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

Check your spam folder after the start of the script - an email indicating the start of the
monitoring should arrive.
Consider using tmux to provide a stable SSH connection. Tmux tutorial is available here:
https://youtu.be/U5nwC0lgFdc?si=rVDTDsBIH-vG2zPf

[version {VER}]
Written and tested in python3.11
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools\n{UNDERLINE}"""

    example="\nExample: data_collection_alarm.py  --to MYEMAIL1@ethz.ch MYEMAIL2@ethz.ch  --path PATHTOMYDATA --label .tiff --die 1 "
    parser = argparse.ArgumentParser(prog=PROG, formatter_class=argparse.RawDescriptionHelpFormatter)
    add = parser.add_argument
    add('--password', default=DEF_PASSWORD, help=f"Password from the email server (see instructions above in the program description)", metavar="")
    add('--emailfrom', default=DEF_EMAIL_FROM,
        help=f"Email account to send emails FROM. (default: {DEF_EMAIL_FROM})", metavar="")
    add('--to', nargs="+", help="Email account to send emails TO - your email(s).", metavar="")
    add('--smtp', default=DEF_SMTP_SER,
        help=f"SMTP server. (default: {DEF_SMTP_SER})", metavar="")
    add('--port', default=DEF_PORT,
        help=f"port for SMTP over SSL. Try 587 if 465 does not work. (default: {DEF_PORT})", metavar="")
    add('--path', default=DEF_PATH,
        help=f"Path to the folder with your files. (default: {DEF_PATH}) ", metavar="")
    add('--time', default=DEF_TIME_BETWEEN_CHECKS,
        help=f"Time interval in minutes for checking the folder size. (default: {DEF_TIME_BETWEEN_CHECKS})", metavar="")
    add('--label', default=DEF_LABEL,
        help=f"Pattern of names of the movie files to search for (default: {DEF_LABEL})", metavar="")
    add('--restart', default=True, action='store_true',
        help="Keep sending error emails even if the data collection stops (default: True")
    add('--okreport', default=DEF_OK_REPORT_TIME,
        help=f"Keep sending reports that the data is collecting every N mins interval (default: {DEF_OK_REPORT_TIME})", metavar="")
    add('--delay', default=DEF_DELAY_BEFORE_START,
        help=f"Delay in seconds before running the script to make sure some movies are being acquiredv (default: {DEF_DELAY_BEFORE_START})", metavar="")
    add('--localhost', default=False, action='store_true',
        help="Use localhost settings; specific for the ETH Krioses (default: False)")
    add('--die', default=DEF_DIE, help=f"Kill program after this number of days (default: {DEF_DIE})", metavar="")
    add('--error_wait_time', default=DEF_ERROR_WAIT_TIME,
        help=f"Time interval in minutes for checking the folder size if error occured. (default: {DEF_ERROR_WAIT_TIME})", metavar="")

    args = parser.parse_args()
    print(output_text)
    parser.print_help()

    if args.to == None:
        sys.exit(f"\n => ERROR!!! Check your input: Please indicate an email (--to) for sending updates. {example} ")
    if float(args.time) < DEF_MIN_TIME_FOR_CHECK:
        sys.exit(f" => ERROR! Please use --time more than {DEF_MIN_TIME_FOR_CHECK} minutes! The program will be terminated")

    print(f'\n => {now()} running the script: \ndata_collection_alarm.py  --to {args.to} --password {args.password} --emailfrom {args.emailfrom} --to {args.to} --smtp {args.smtp} --port {args.port} --path {args.path} --time {args.time} --label {args.label} --restart {args.restart} --okreport {args.okreport} --delay {args.delay} --localhost {args.localhost} --die {args.die} --error_wait_time {args.error_wait_time}\n')
    print(f'\n => NOTE! The program will be terminated in {args.die} day(s). To change the running time use --die option \n')
    main(args.password, args.emailfrom, args.to, args.smtp, args.port, args.path, (float(args.time)*60), args.label, args.restart, (float(args.okreport)*60), float(args.delay), args.localhost, float(args.die), (float(args.error_wait_time))*60)
