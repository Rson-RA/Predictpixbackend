from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
from decimal import Decimal

class Web3Service:
    def __init__(self):
        # Initialize Web3 with your provider (e.g., Infura, Alchemy, or local node)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER_URL")))
        
        # Add middleware for POA networks if needed
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Load contract ABI and address
        contract_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "contracts", "PredictionMarket.json")
        with open(contract_path) as f:
            contract_data = json.load(f)
            self.contract_abi = contract_data["abi"]
            self.contract_address = os.getenv("CONTRACT_ADDRESS")
        
        # # Initialize contract
        # self.contract = self.w3.eth.contract(
        #     address=self.contract_address,
        #     abi=self.contract_abi
        # )

    def create_market(
        self,
        title: str,
        description: str,
        end_time: datetime,
        resolution_time: datetime,
        creator_fee_percentage: int,
        platform_fee_percentage: int,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Create a new prediction market on the blockchain.
        """
        # Convert datetime to Unix timestamp
        end_timestamp = int(end_time.timestamp())
        resolution_timestamp = int(resolution_time.timestamp())
        
        # Prepare transaction
        transaction = self.contract.functions.createMarket(
            title,
            description,
            end_timestamp,
            resolution_timestamp,
            creator_fee_percentage,
            platform_fee_percentage
        ).build_transaction({
            'from': self.w3.eth.account.from_key(private_key).address,
            'nonce': self.w3.eth.get_transaction_count(
                self.w3.eth.account.from_key(private_key).address
            ),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Get market ID from event
        market_created_event = self.contract.events.MarketCreated().process_receipt(receipt)
        market_id = market_created_event[0]['args']['marketId']
        
        return {
            'market_id': market_id,
            'transaction_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber']
        }

    def place_prediction(
        self,
        market_id: int,
        predicted_outcome: bool,
        amount: Decimal,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Place a prediction on a market.
        """
        # Convert amount to wei
        amount_wei = self.w3.to_wei(float(amount), 'ether')
        
        # Prepare transaction
        transaction = self.contract.functions.placePrediction(
            market_id,
            predicted_outcome
        ).build_transaction({
            'from': self.w3.eth.account.from_key(private_key).address,
            'value': amount_wei,
            'nonce': self.w3.eth.get_transaction_count(
                self.w3.eth.account.from_key(private_key).address
            ),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'transaction_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber']
        }

    def resolve_market(
        self,
        market_id: int,
        outcome: bool,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Resolve a market with the given outcome.
        """
        # Prepare transaction
        transaction = self.contract.functions.resolveMarket(
            market_id,
            outcome
        ).build_transaction({
            'from': self.w3.eth.account.from_key(private_key).address,
            'nonce': self.w3.eth.get_transaction_count(
                self.w3.eth.account.from_key(private_key).address
            ),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'transaction_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber']
        }

    def claim_reward(
        self,
        market_id: int,
        private_key: str
    ) -> Dict[str, Any]:
        """
        Claim rewards for a resolved market.
        """
        # Prepare transaction
        transaction = self.contract.functions.claimReward(
            market_id
        ).build_transaction({
            'from': self.w3.eth.account.from_key(private_key).address,
            'nonce': self.w3.eth.get_transaction_count(
                self.w3.eth.account.from_key(private_key).address
            ),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, private_key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'transaction_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber']
        }

    def get_market_info(self, market_id: int) -> Dict[str, Any]:
        """
        Get information about a market.
        """
        market_info = self.contract.functions.getMarket(market_id).call()
        
        return {
            'title': market_info[0],
            'description': market_info[1],
            'end_time': datetime.fromtimestamp(market_info[2]),
            'resolution_time': datetime.fromtimestamp(market_info[3]),
            'total_pool': self.w3.from_wei(market_info[4], 'ether'),
            'yes_pool': self.w3.from_wei(market_info[5], 'ether'),
            'no_pool': self.w3.from_wei(market_info[6], 'ether'),
            'is_resolved': market_info[7],
            'outcome': market_info[8]
        }

    def get_user_predictions(
        self,
        market_id: int,
        user_address: str
    ) -> Decimal:
        """
        Get user's total predictions for a market.
        """
        predictions = self.contract.functions.getUserPredictions(
            market_id,
            user_address
        ).call()
        
        return self.w3.from_wei(predictions, 'ether')

    def calculate_reward(
        self,
        market_id: int,
        user_address: str,
        outcome: bool
    ) -> Decimal:
        """
        Calculate potential reward for a user's predictions.
        """
        reward = self.contract.functions.calculateReward(
            market_id,
            user_address,
            outcome
        ).call()
        
        return self.w3.from_wei(reward, 'ether') 