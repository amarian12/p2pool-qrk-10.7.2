import sys
import time

from twisted.internet import defer

import p2pool
from p2pool.quark import data as quark_data
from p2pool.util import deferral, jsonrpc

@deferral.retry('Error while checking quark connection:', 1)
@defer.inlineCallbacks
def check(quarkd, net):
    if not (yield net.PARENT.RPC_CHECK(quarkd)):
        print >>sys.stderr, "    Check failed! Make sure that you're connected to the right quarkd with --quarkd-rpc-port!"
        raise deferral.RetrySilentlyException()
    if not net.VERSION_CHECK((yield quarkd.rpc_getinfo())['version']):
        print >>sys.stderr, '    quark version too old! Upgrade to 0.11.2.17 or newer!'
        raise deferral.RetrySilentlyException()

@deferral.retry('Error getting work from quarkd:', 3)
@defer.inlineCallbacks
def getwork(quarkd, net, use_getblocktemplate=False):
    def go():
        if use_getblocktemplate:
            return quarkd.rpc_getblocktemplate(dict(mode='template'))
        else:
            return quarkd.rpc_getmemorypool()
    try:
        start = time.time()
        work = yield go()
        end = time.time()
    except jsonrpc.Error_for_code(-32601): # Method not found
        use_getblocktemplate = not use_getblocktemplate
        try:
            start = time.time()
            work = yield go()
            end = time.time()
        except jsonrpc.Error_for_code(-32601): # Method not found
            print >>sys.stderr, 'Error: quark version too old! Upgrade to v0.11.2.17 or newer!'
            raise deferral.RetrySilentlyException()
    packed_transactions = [(x['data'] if isinstance(x, dict) else x).decode('hex') for x in work['transactions']]
    if 'height' not in work:
        work['height'] = (yield quarkd.rpc_getblock(work['previousblockhash']))['height'] + 1
    elif p2pool.DEBUG:
        assert work['height'] == (yield quarkd.rpc_getblock(work['previousblockhash']))['height'] + 1
    defer.returnValue(dict(
        version=work['version'],
        previous_block=int(work['previousblockhash'], 16),
        transactions=map(quark_data.tx_type.unpack, packed_transactions),
        transaction_hashes=map(quark_data.hash256, packed_transactions),
        transaction_fees=[x.get('fee', None) if isinstance(x, dict) else None for x in work['transactions']],
        subsidy=work['coinbasevalue'],
        time=work['time'] if 'time' in work else work['curtime'],
        bits=quark_data.FloatingIntegerType().unpack(work['bits'].decode('hex')[::-1]) if isinstance(work['bits'], (str, unicode)) else quark_data.FloatingInteger(work['bits']),
        coinbaseflags=work['coinbaseflags'].decode('hex') if 'coinbaseflags' in work else ''.join(x.decode('hex') for x in work['coinbaseaux'].itervalues()) if 'coinbaseaux' in work else '',
        height=work['height'],
        last_update=time.time(),
        use_getblocktemplate=use_getblocktemplate,
        latency=end - start,
        payee=quark_data.address_to_pubkey_hash(work['payee'], net.PARENT) if (work['payee'] != '') else None,
        masternode_payments=work['masternode_payments'],
        payee_amount=work['payee_amount'] if (work['payee_amount'] != '') else work['coinbasevalue'] / 5,
    ))

@deferral.retry('Error submitting primary block: (will retry)', 10, 10)
def submit_block_p2p(block, factory, net):
    if factory.conn.value is None:
        print >>sys.stderr, 'No quarkd connection when block submittal attempted! %s%064x' % (net.PARENT.BLOCK_EXPLORER_URL_PREFIX, quark_data.hash256(quark_data.block_header_type.pack(block['header'])))
        raise deferral.RetrySilentlyException()
    factory.conn.value.send_block(block=block)

@deferral.retry('Error submitting block: (will retry)', 10, 10)
@defer.inlineCallbacks
def submit_block_rpc(block, ignore_failure, quarkd, quarkd_work, net):
    if quarkd_work.value['use_getblocktemplate']:
        try:
            result = yield quarkd.rpc_submitblock(quark_data.block_type.pack(block).encode('hex'))
        except jsonrpc.Error_for_code(-32601): # Method not found, for older litecoin versions
            result = yield quarkd.rpc_getblocktemplate(dict(mode='submit', data=quark_data.block_type.pack(block).encode('hex')))
        success = result is None
    else:
        result = yield quarkd.rpc_getmemorypool(quark_data.block_type.pack(block).encode('hex'))
        success = result
    success_expected = net.PARENT.POW_FUNC(quark_data.block_header_type.pack(block['header'])) <= block['header']['bits'].target
    if (not success and success_expected and not ignore_failure) or (success and not success_expected):
        print >>sys.stderr, 'Block submittal result: %s (%r) Expected: %s' % (success, result, success_expected)

def submit_block(block, ignore_failure, factory, quarkd, quarkd_work, net):
    submit_block_p2p(block, factory, net)
    submit_block_rpc(block, ignore_failure, quarkd, quarkd_work, net)
