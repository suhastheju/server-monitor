#!/usr/bin/python

import os
import time
import argparse
from time import sleep
from subprocess import call
import sys


#*************************************************************************
# utils

def str_to_bool(s):
    if s == 'UP':
        return True
    elif s == 'DOWN':
        return False
    else:
        raise ValueError
    #end if
#end str_to_bool()

def rm(_file):
    cmd = "rm -f %s"% (_file)
    call(cmd, shell=True)
#end rm()
    
def valid_line(line):
    if line[0] == '#' or line[0] =='\n':
        return 0
    elif len(line.split()) != 2:
        return 0
    #end if
    return 1
#end valid_line()

#*************************************************************************
def read_status(iptables, stat_file):
    status = {}
    if os.path.exists(stat_file):
        _file = open(stat_file, 'r')
        for line in _file:
            server, ip, link_status = line.split()
            status[server] = str_to_bool(link_status)
        #end for
        _file.close()
    else:
        for server in iptables.keys():
            status[server] = False
        update_status(status, iptables, stat_file)
    #end if

    # update if new server is added to iptables
    for server in iptables.keys():
        if server not in status.keys():
            status[server] = False
    #end for
    update_status(status, iptables, stat_file)
    return status
#end read_status()

def update_status(status, iptables, stat_file):
    _file = open(stat_file, 'w')
    for server in status.keys():
        if(status[server]):
            _file.write("%25s %18s  UP \n"%(server, iptables[server]))
        else:
            _file.write("%25s %18s  DOWN \n"%(server, iptables[server]))
        #end if
    #end for
    _file.close()
#end update_status()

def check_status(iptables):
    status = {}
    for server in iptables.keys():
        cmd = "ping -c 3 %s > /dev/null 2>&1"% (iptables[server])
        ret = call(cmd, shell=True)
        status[server]= not(ret)
    #end for
    return status
#end check_status()

def read_iptables():
    if not os.path.exists(iptables_file):
        print("Error: file 'iptables.txt' not found")
        exit()
    #end if

    _file = open(iptables_file, 'r')
    iptables = {}
    for line in _file:
        if valid_line(line):
            server, ip = line.split()
            iptables[server] = ip
        #end if
    #end for
    _file.close()
    return iptables
#end read_iptables()

def check_diff(_old, _new):
    for server in _old.keys():
        if(_old[server] != _new[server]):
            return 1;
    #end for
    
def gen_report(iptables, status, filename):
    log = open(filename, 'w')
    #log.write("From: %s\n"% (from_mail))
    #log.write("To: %s\n"% (to_mail))
    log.write("Subject: Server status report %s %s \n\n"% 
                (time.strftime("%d/%m/%y"), time.strftime("%H:%M:%S")))
    for server in iptables.keys():
        if(status[server]):
            log.write("%30s %30s  UP \n"%(server, iptables[server]))
        else:
            log.write("%30s %30s  DOWN \n"%(server, iptables[server]))
        #end if
    #end for
    log.close()
#end gen_report()

def init(server_stat_file):
    iptables= read_iptables()
    status= read_status(iptables, server_stat_file)
    return iptables, status
#end init()

#*************************************************************************
def print_report(status, iptables):
    print("\nServer status report %s %s \n"% 
                (time.strftime("%d/%m/%y"), time.strftime("%H:%M:%S")))
    for server in iptables.keys():
        if(status[server]):
            print("%30s %30s  UP"%(server, iptables[server]))
        else:
            print("%30s %30s  DOWN"%(server, iptables[server]))
        #end if
    #end for
# end print_report()

def email_report(email_id, msg):
    cmd = '%s %s < %s'%(email_agent, email_id, msg)
    call(cmd, shell=True)
#end email_report()

def wall_report(msg):
    cmd = 'cat %s| wall'%(msg)
    call(cmd, shell=True)
#end wall_report()

def cmd_parser():
    parser = argparse.ArgumentParser()
    g = parser.add_argument_group('Options')
    g.add_argument('--wall', action='store_true', help='wall status')
    g.add_argument('--print', action='store_true', help='print status')
    g.add_argument('--email', action='store_true', help='email status')
    g.add_argument('--to-mail', nargs='?', required=False, type=str, default='abc@xyz.com')
    return parser
#end cmd_parser()

#*************************************************************************
if __name__ == '__main__':
    parser = cmd_parser()
    opts = vars(parser.parse_args())

    server_stat_file = 'server-stat.txt'
    iptables_file = 'iptables.txt'
    from_mail = 'brahmagupta@mymail.com'
    mail_file= 'email_msg.txt'
    email_agent = '/usr/sbin/ssmtp'

    wall    = opts['wall']
    print_  = opts['print']
    email   = opts['email']
    to_mail = opts['to_mail']

    cwd = os.getcwd()
    os.chdir("./")
    iptables, status = init(server_stat_file)
   
    _change = False

    newstatus = check_status(iptables)
    gen_report(iptables, status, mail_file)
    if check_diff(status, newstatus):
        status = newstatus
        update_status(status, iptables, server_stat_file)
        _change = True
    #end if

    if wall:
        wall_report(mail_file)
    if print_:
        print_report(status, iptables)
    if email and _change:
        email_report(to_mail, mail_file)
    
    rm(mail_file)
    os.chdir(cwd)
# end main()
