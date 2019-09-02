from p2pool.quark import networks
from p2pool.util import math

# CHAIN_LENGTH = number of shares back client keeps
# REAL_CHAIN_LENGTH = maximum number of shares back client uses to compute payout
# REAL_CHAIN_LENGTH must always be <= CHAIN_LENGTH
# REAL_CHAIN_LENGTH must be changed in sync with all other clients
# changes can be done by changing one, then the other

nets = dict(
    quark=math.Object(
        PARENT=networks.nets['quark'],
        SHARE_PERIOD=10, # seconds
        CHAIN_LENGTH=24*60*60//10, # shares
        REAL_CHAIN_LENGTH=24*60*60//10, # shares
        TARGET_LOOKBEHIND=200, # shares //with that the pools share diff is adjusting faster, important if huge hashing power comes to the pool
        SPREAD=30, # blocks
        IDENTIFIER='fc70135c7a81bc6f'.decode('hex'),
        PREFIX='9472ef181efcd37b'.decode('hex'),
        COINBASEEXT='0A2F5032506F6F6C2D51524B2D452D506F6F6C2F'.decode('hex'),
        P2P_PORT=5890,
        MIN_TARGET=0,
        MAX_TARGET=2**256//2**32 - 1,
        PERSIST=False,
        WORKER_PORT=5860,
        BOOTSTRAP_ADDRS=''.split('p2pool.e-pool.net'),
        ANNOUNCE_CHANNEL='#p2pool-qrk',
        VERSION_CHECK=lambda v: True,
    ),
)
for net_name, net in nets.iteritems():
    net.NAME = net_name
