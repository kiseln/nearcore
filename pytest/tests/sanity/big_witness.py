#!/usr/bin/env python3
# This test checks the ultimate undercharding scenario where a chunk takes
# long time to apply but consumes little gas. This is to simulate real
# undercharing in a more controlled manner.

import sys
import json
import unittest
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / 'lib'))

from transaction import sign_payment_tx, sign_function_call_tx
from configured_logger import logger
from cluster import start_cluster
from utils import load_test_contract, poll_blocks

GGAS = 10**9


class SlowChunkTest(unittest.TestCase):

    def test(self):
        n = 2
        val_client_config_changes = {i: {"tracked_shards": []} for i in range(n)}
        rpc_client_config_changes = {n: {"tracked_shards": [0]}}

        client_config_changes = {
            **val_client_config_changes,
            **rpc_client_config_changes,
        }

        genesis_config_changes = [["epoch_length", 100]]
        [node1, node2, rpc] = start_cluster(
            num_nodes=n,
            num_observers=1,
            num_shards=2,
            config=None,
            genesis_config_changes=genesis_config_changes,
            client_config_changes=client_config_changes,
        )

        for height, hash in poll_blocks(rpc, __target=6):
            chunk_mask = self.__get_chunk_mask(rpc, hash)
            logger.info(f"#{height} chunk mask: {chunk_mask}")

        self.__call_function(rpc)

        for height, hash in poll_blocks(rpc, __target=10000):
            block = rpc.json_rpc("block", {"block_id": hash})
            chunk_mask = block['result']['header']['chunk_mask']
            height = block['result']['header']["height"]
            logger.info(f"#{height} chunk mask: {chunk_mask}")


    def __call_function(self, node):
        logger.info("Calling contract.")

        block_hash = node.get_latest_block().hash_bytes

        tx = sign_function_call_tx(
            node.signer_key,
            node.signer_key.account_id,
            'internal_record_storage_garbage_11',
            [],
            300000000000000,
            300000000000000,
            10,
            block_hash,
        )
        result = node.send_tx(tx)

        logger.info(json.dumps(result, indent=2))


    def __get_chunk_mask(self, node, block_hash):
        block = node.json_rpc("block", {"block_id": block_hash})
        return block['result']['header']['chunk_mask']


if __name__ == '__main__':
    unittest.main()
