''' Holds logic necessary for interacting with the online distribution
cache '''

import re
import os

from api.providers.configuration.configuration_provider import ConfigurationProvider
from api.util import sshcmd
from api.system.logger import ilogger as logger


class OnlineCacheException(Exception):
    """ General exception raised from the OnlineCache """
    pass


class OnlineCache(object):
    """ Client code to interact with the LSRD online cache """

    config = ConfigurationProvider()

    __order_path_key = 'online_cache_orders_dir'
    __host_key = 'landsatds.host'
    __user_key = 'landsatds.username'
    __pw_key = 'landsatds.password'

    def __init__(self):
        self.orderpath = self.config.get(self.__order_path_key)

        if not self.orderpath:
            msg = '{} not defined in configurations'.format(self.__order_path_key)
            logger.critical(msg)
            raise OnlineCacheException(msg)

        host, user, pw = self.config.get([self.__host_key,
                                          self.__user_key,
                                          self.__pw_key])

        self.client = sshcmd.RemoteHost(host, user, pw, timeout=5)

        try:
            self.client.execute('ls')
        except Exception as e:
            logger.critical('No connection to OnlineCache host: {}'.format(e))
            raise OnlineCacheException(e)

    def exists(self, orderid, filename=None):
        """ Check if an order [optional filename] exists on the onlinecache

        :param orderid:  associated order to check
        :param filename: file to check inside of an order
        :return: bool
        """
        if filename:
            path = os.path.join(self.orderpath, orderid, filename)
        else:
            path = os.path.join(self.orderpath, orderid)

        try:
            result = self.execute_command('ls -d {0}'.format(path), silent=True)
            ret = tuple(x.rstrip() for x in result['stdout'])
            return ret[-1] == path
        except OnlineCacheException as e:
            return False

    def delete(self, orderid, filename=None):
        """
        Removes an order from physical online cache disk

        :param filename: file to delete inside of an order
        :param orderid: associated order to delete
        """
        if not self.exists(orderid, filename):
            msg = 'Invalid orderid {} or filename {}'.format(orderid, filename)
            logger.critical(msg)
            return False

        if filename:
            path = os.path.join(self.orderpath, orderid, filename)
        else:
            path = os.path.join(self.orderpath, orderid)

        # this should be the dir where the order is held
        logger.info('Deleting {} from online cache'.format(path))
        # TODO: if storage system supports immutable options
        # >>> sudo chattr -fR -i {0};rm -rf {0}
        # However, nfs does not support this extended attributes
        try:
            cmd = 'chmod -R 744 {0};rm -rf {0}'.format(path)
            self.execute_command(cmd)
        except OnlineCacheException as exc:
            logger.critical('Failed to remove files from output cache. '
                            'Command: {} Error: {}'.format(cmd, exc))
            return False
        return True

    def list(self, orderid=None):
        """
        List the orders currently stored on cache, or files listed
        insed of a specific order

        :param orderid: order name to look inside of
        :return: list of folders/files
        """
        if orderid:
            path = os.path.join(self.orderpath, orderid)
        else:
            path = self.orderpath

        cmd = 'ls {}'.format(path)

        result = self.execute_command(cmd)
        ret = tuple(x.rstrip() for x in result['stdout'])

        return ret

    def capacity(self):
        """
        Returns the capacity of the online cache

        :return: dict
        """

        cmd = 'df -mhP {}'.format(self.orderpath)

        result = self.execute_command(cmd)

        line = result['stdout'][1].split(' ')

        clean = [l for l in line if len(l) > 0]

        results = {'capacity': clean[1],
                   'used': clean[2],
                   'available': clean[3],
                   'percent_used': clean[4]}

        return results

    def execute_command(self, cmd, silent=False):
        """
        Execute the given command on the cache

        :param cmd: cmd string to execute
        :return: results of the command
        """
        try:
            result = self.client.execute(cmd)
        except Exception, exception:
            if not silent:
                logger.critical('Error executing command: {} '
                                'Raised exception: {}'.format(cmd, exception))
            raise OnlineCacheException(exception)

        if 'stderr' in result and result['stderr']:
            if not silent:
                logger.critical('Error executing command: {} '
                                'stderror returned: {}'.format(cmd, result['stderr']))

            raise OnlineCacheException(result['stderr'])

        logger.info('call to {} returned {}'.format(cmd, result))

        return result

def exists(orderid):
    return OnlineCache().exists(orderid)


def delete(orderid, filename=None):
    return OnlineCache().delete(orderid, filename)


def capacity():
    return OnlineCache().capacity()
