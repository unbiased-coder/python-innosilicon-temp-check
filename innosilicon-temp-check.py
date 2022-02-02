#!/usr/bin/env python

import sys
import time
import json
import logging
import httplib
import urllib2
import datetime

sys.path.append('.')

# if you need this email libraries will be happy to provide them otherwise
# you can skip the notification 
# you can ping me on my twitter account twitter.com/unbiasedcoder

from lib.email_helper import EmailHelper
from lib.logger_helper import setup_logger

class A4WorkerMon(EmailHelper):
    """
    Class that monitors workers in A4 innosilicon workers
    """
    
    def __init__(self, poll_time = 600, temp_threshold = 55):
        """
        Poll time specifies how long to wait between checks
        """

        super(A4WorkerMon, self).__init__()
        
        self.poll_time         = poll_time

        setup_logger('a4_worker_mon', 'a4_worker_mon.txt')
        self.log = logging.getLogger(__name__)

        self.src_email = 'info@unbiased-coder.com'
        self.dst_email = 'mining@unbiased-coder.com'

        self.temp_threshold = temp_threshold

        # if you have any handicapped miners like I did replace the IPs here
        self.handicapped_ips = [
            '192.168.1.246',
            '192.168.1.245'
        ]
        
        # replace this with your list
        self.ip_list = [
            '192.168.1.241',
            '192.168.1.242',
            '192.168.1.243',
            '192.168.1.244',
            '192.168.1.245',
            '192.168.1.246',
            '192.168.1.247',
            '192.168.1.248',
            '192.168.1.250',
            '192.168.1.251',
            '192.168.1.252',
            '192.168.1.253'
        ]

    def send_notification_email(self, subject, email_msg):
        """
        Sends notification email
        """
        self.log.warning(email_msg)
        self.send_email(self.src_email, self.dst_email, subject, email_msg)

    def monitor_workers(self):
        """
        Monitors if all works are alive
        """

        try:
            while True:
                
                # iterate through all IPs
                for ip in self.ip_list:

                    # Download the JSON with the content information
                    try:
                        response = urllib2.urlopen('http://%s/cgi-bin/temper.py'%ip)
                    except (urllib2.URLError, httplib.BadStatusLine), e:
                        self.log.error('Failed downloading API data from innosilicon A4 IP: %s'%ip)
                        continue

                    # Parse JSON result from litecoinpool
                    try:
                        data = json.load(response)
                    except ValueError:
                        self.log.error('Failed parsing json data from IP: %s'%ip)
                        continue

                    # Check if JSON has worker field
                    if not data.has_key('DEVS'):
                        self.log.error('Result has no DEVS field from IP: %s'%ip)
                        continue


                    dateformat = str(datetime.datetime.now())
                                     
                    # Iterate through all the available workers
                    asc_count = 0
                    for asc in data['DEVS']:
                        asc_count += 1
                                            
                        # Check if we have not exceeded an avg temp of the threshold we specified above
                        if not asc.has_key('TempAVG'):
                            self.log.error('Worker has no TempAVG field IP: %s'%ip)
                            continue
                        else:
                            avg_temp = int(asc['TempAVG'])
                            if avg_temp >= self.temp_threshold:
                                subject = '%s is overheating (%d C.)'%(ip, avg_temp)
                                email_msg = '[%s] - WARNING IP: %s is overheating ASIC: %d Temp: %d C.'%(dateformat, ip, asc['ASC'], avg_temp)
                                self.send_notification_email(subject, email_msg)

                        # check if an ASIC has died
                        if not asc.has_key('Status'):
                            self.log.error('Worker has no Status field IP: %s'%ip)
                            continue
                        else:
                            status = asc['Status']
                            if status == 'Dead':
                                subject = '%s has an ASC dead consider rebooting'%ip
                                email_msg = '[%s] - WARNING IP: %s has an ASC dead number: %d'%(dateformat, ip, asc['ASC'])
                                self.send_notification_email(subject, email_msg)

                    # If we have less than 4 ASICs active send email (except for .246 which is temporarily handicapped
                    if asc_count != 4:
                        subject = '%s has only %d ASICS'%(ip, asc_count)
                        email_msg = '[%s] - WARNING IP: %s has only %d ASICs active'%(dateformat, ip, asc_count)

                        # Make sure this isn't .246 and .245
                        if ip not in self.handicapped_ips:
                            self.send_notification_email(subject, email_msg)
                        else:
                            if ip == '192.168.1.245' and asc_count != 3:
                                self.send_notification_email(subject, email_msg)
                            elif ip == '192.168.1.246' and asc_count != 3:
                                self.send_notification_email(subject, email_msg)

                time.sleep(self.poll_time)
                
        except KeyboardInterrupt:
            self.log.warning('Keyboard interrupt caught exiting')
            return

if __name__ == '__main__':
    a4m = A4WorkerMon(temp_threshold = 55)
    a4m.monitor_workers()
