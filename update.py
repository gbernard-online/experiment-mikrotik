#!/usr/bin/env python3
#--------------------------------------------- ghislain.bernard@gmail.com ---------------------------------------------#

import datetime
import os
import ssl
import time

import routeros_api

import scapy.layers.inet6
import scapy.layers.l2
import scapy.sendrecv

#----------------------------------------------------------------------------------------------------------------------#

DELAY = 60
EXPIRATION = '5m'
TIMEOUT = 1

#----------------------------------------------------------------------------------------------------------------------#

def main():

  print(datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)

  router = routeros_api.RouterOsApiPool(os.environ['MIKROTIK_HOSTNAME'],
                                        password=os.environ['MIKROTIK_PASSWORD'],
                                        username=os.environ['MIKROTIK_USERNAME'],
                                        plaintext_login=True,
                                        ssl_context=ssl.create_default_context(cafile='ca.crt')).get_api()

  #######################

  static = router.get_resource('/ip/dns/static')

  for entry in sorted(static.call('print'), key=lambda entry: entry['name'] + entry['type'] + entry['address']):

    if 'comment' not in entry or entry['comment'] != 'external':
      continue

    if entry['ttl'] != EXPIRATION:
      static.call('set', {'id': entry['id'], 'ttl': EXPIRATION})
      entry['ttl'] = EXPIRATION
      print(entry, flush=True)

    match entry['type']:

      case 'A':

        result = scapy.layers.l2.arping(entry['address'], timeout=TIMEOUT, verbose=False)[0]

        match len(result):
          case 0:
            if entry['disabled'] == 'false':
              static.call('set', {'id': entry['id'], 'disabled': 'true'})
              entry['disabled'] = 'true'
              print(entry, flush=True)
          case 1:
            if entry['disabled'] == 'true':
              static.call('set', {'id': entry['id'], 'disabled': 'false'})
              entry['disabled'] = 'false'
              print(entry, flush=True)

      case 'AAAA':

        result = scapy.sendrecv.srp1(scapy.layers.l2.Ether(dst="ff:ff:ff:ff:ff:ff") /
                                     scapy.layers.inet6.IPv6(dst=entry['address']) /
                                     scapy.layers.inet6.ICMPv6EchoRequest(),
                                     timeout=TIMEOUT,
                                     verbose=False)

        match result:
          case None:
            if entry['disabled'] == 'false':
              static.call('set', {'id': entry['id'], 'disabled': 'true'})
              entry['disabled'] = 'true'
              print(entry, flush=True)
          case _:
            if entry['disabled'] == 'true':
              static.call('set', {'id': entry['id'], 'disabled': 'false'})
              entry['disabled'] = 'false'
              print(entry, flush=True)

  #######################

  print('-', flush=True)

#----------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':

  while True:
    main()
    time.sleep(DELAY)

#--------------------------------------------- ghislain.bernard@gmail.com ---------------------------------------------#
