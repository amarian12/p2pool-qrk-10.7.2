import os
import platform

from twisted.internet import defer

from . import data
from p2pool.util import math, pack

nets = dict(
    quark=math.Object(
        #P2P_PREFIX='fea503dd'.decode('hex'),
        P2P_PREFIX='fca402dc'.decode('hex'),
        P2P_PORT=5810,
        ADDRESS_VERSION=58,
        SCRIPT_ADDRESS_VERSION = 9,
        RPC_PORT=15810,
        RPC_CHECK=defer.inlineCallbacks(lambda bitcoind: defer.returnValue(
            'quarkaddress' in (yield bitcoind.rpc_help()) and
            not (yield bitcoind.rpc_getinfo())['testnet']
        )),
        SUBSIDY_FUNC=lambda height: 2048*100000000 >> (height + 1)//60480,
        BLOCKHASH_FUNC=lambda data: pack.IntType(256).unpack(__import__('quark_hash').getPoWHash(data)),
        POW_FUNC=lambda data: pack.IntType(256).unpack(__import__('quark_hash').getPoWHash(data)),
        BLOCK_PERIOD=30, # s
        SYMBOL='QRK',
        CONF_FILE_FUNC=lambda: os.path.join(os.path.join(os.environ['APPDATA'], 'Quarkcoin') if platform.system() == 'Windows' else os.path.expanduser('~/Library/Application Support/Quarkcoin/') if platform.system() == 'Darwin' else os.path.expanduser('~/.quarkcoin'), 'quarkcoin.conf'),
        BLOCK_EXPLORER_URL_PREFIX='https://chainz.cryptoid.info/qrk/block.dws?',
        ADDRESS_EXPLORER_URL_PREFIX='https://chainz.cryptoid.info/qrk/address.dws?',
        TX_EXPLORER_URL_PREFIX='https://chainz.cryptoid.info/qrk/tx.dws?',
        SANE_TARGET_RANGE=(2**256//2**32//100000 - 1, 2**256//2**20 - 1),
        DUMB_SCRYPT_DIFF=1,
        DUST_THRESHOLD=0.001e5,
    ),
)
for net_name, net in nets.iteritems():
    net.NAME = net_name
