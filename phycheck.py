#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import click
import os
import subprocess
import time
import syslog
import traceback
import logging.handlers
from ragileutil import CompressedRotatingFileHandler

FILE_NAME = "/var/log/phycheck.log"
MAX_LOG_BYTES = 20*1024*1024
BACKUP_COUNT = 9

logger = logging.getLogger("phycheck")
logger.setLevel(logging.DEBUG)
phycheck_log = CompressedRotatingFileHandler(FILE_NAME, mode='a', maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding=None, delay=0)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
phycheck_log.setFormatter(formatter)
logger.addHandler(phycheck_log)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

def os_system(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return status, output

def run():
    logger.warning("do phy register checking...")
    while True:
        try:
            command_line = "busybox devmem 0x334100c8"
            ret, ret_t = os_system(command_line)
            if int(ret_t,16) & 0xf != 6:
                set_line = "busybox devmem 0x33410088 32 0x647939"
                ret, set_t = os_system(set_line)
                down = "ifconfig eth0 down"
                up = "ifconfig eth0 up"
                ret,down_t = os_system(down)
                time.sleep(2)
                ret,up_t = os_system(up)
                ret, ret_r = os_system(command_line)
                if int(ret_r,16) & 0xf == 6:
                    logger.info("do rest eth0 ok!")
        except Exception as e:
            traceback.print_exc()
            logger.error(str(e))
            ret = -1
        time.sleep(10)


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
def main():
    '''device operator'''


@main.command()
def start():
    '''start device monitor'''
    logger.info("do eth0 phy check start")
    run()


@main.command()
def stop():
    '''stop device monitor '''
    logger.info("stop")


# device_i2c operation
if __name__ == '__main__':
    main()