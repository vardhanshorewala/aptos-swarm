from aptos_sdk.async_client import RestClient, FaucetClient
from aptos_sdk.account import Account
from aptos_sdk.transactions import EntryFunction
from aptos_sdk.transactions import TransactionPayload, TransactionArgument
from aptos_sdk.bcs import Serializer
import asyncio
import requests


class Client:
    def __init__(self):
        self.rest_client = RestClient("https://api.devnet.aptoslabs.com/v1")
        self.faucet_client = FaucetClient(
            "https://faucet.devnet.aptoslabs.com", self.rest_client)

    def create_account(self):
        return Account.generate()

    def fund_account(self, address, amount):
        return self.faucet_client.fund_account(address, amount)

    async def get_balance(self, address):
        return await self.rest_client.account_balance(address)

    async def fetch_account_transactions(self, account_address: str, limit: int = 10):
        url = "https://api.devnet.aptoslabs.com/v1/graphql"
        headers = {"Content-Type": "application/json"}
        query = """
            query GetAccountTransactions($account: String, $limit: Int) {
                account_transactions(
                    where: {account_address: {_eq: $account}},
                    order_by: {transaction_version: desc},
                    limit: $limit
                ) {
                    transaction_version
                    __typename
                }
            }
        """
        variables = {"account": str(account_address), "limit": limit}
        payload = {"query": query, "variables": variables}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            transactions = data.get("data", {}).get("account_transactions", [])
            return transactions
        except requests.exceptions.RequestException as e:
            print(f"Error fetching transactions: {e}")
            return None
        except ValueError:
            print("Error parsing response as JSON.")
            return None

    async def fetch_fungible_asset_activities(self, version: int):
        url = "https://api.devnet.aptoslabs.com/v1/graphql"
        headers = {"Content-Type": "application/json"}
        query = """
            query GetFungibleAssetActivities($version: bigint!) {
                fungible_asset_activities(where: { transaction_version: { _eq: $version } }) {
                    asset_type
                    amount
                    entry_function_id_str
                    owner_address
                    transaction_version
                }
            }
        """
        variables = {"version": version}
        payload = {"query": query, "variables": variables}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("fungible_asset_activities", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching fungible asset activities: {e}")
            return None
        except ValueError:
            print("Error parsing response as JSON.")
            return None

    async def fetch_account_balances(self, account_address: str):
        url = "https://api.devnet.aptoslabs.com/v1/graphql"
        headers = {"Content-Type": "application/json"}
        query = """
        query GetFungibleAssetBalances($account: String) {
            current_fungible_asset_balances(
                where: {owner_address: {_eq: $account}},
                limit: 100,
                order_by: {amount: desc}
            ) {
                asset_type
                amount
            }
        }
        """
        variables = {"account": account_address}
        payload = {"query": query, "variables": variables}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            balances = data.get("data", {}).get(
                "current_fungible_asset_balances", [])
            print(f"Balances for {account_address}:")
            for balance in balances:
                print(
                    f"  Asset Type: {balance['asset_type']}, Amount: {balance['amount']}")
            return balances
        except requests.exceptions.RequestException as e:
            print(f"Error fetching balances: {e}")
            return None
        except ValueError:
            print("Error parsing response as JSON.")
            return None

    async def create_token(self, creator_account: Account, name: str, symbol: str, supply: int):
        try:
            transaction = EntryFunction.natural(
                module="0x1::managed_coin",
                function="create",
                args=[name, symbol, supply, True],
            )
            signed_txn = creator_account.sign_transaction(transaction)
            result = await self.rest_client.submit_transaction(signed_txn)
            print(f"Token creation submitted. Hash: {result['hash']}")
            return result
        except Exception as e:
            print(f"Error creating token: {e}")
            return None

    async def perform_token_swap(self, sender_account: Account, swap_contract_address: str, token_in: str, token_out: str, amount: int):
        try:
            transaction = EntryFunction.natural(
                module=f"{swap_contract_address}::swap",
                function="swap_tokens",
                args=[token_in, token_out, amount],
            )
            signed_txn = sender_account.sign_transaction(transaction)
            result = await self.rest_client.submit_transaction(signed_txn)
            print(f"Token swap submitted. Hash: {result['hash']}")
            return result
        except Exception as e:
            print(f"Error performing token swap: {e}")
            return None

    async def transfer(self, sender: Account, recipient: str, amount: int):
        try:
            transaction_arguments = [
                TransactionArgument(recipient, Serializer.struct),
                TransactionArgument(amount, Serializer.u64),
            ]
            payload = EntryFunction.natural(
                "0x1::aptos_account",
                "transfer",
                [],
                transaction_arguments,
            )
            signed_transaction = await self.rest_client.create_bcs_signed_transaction(
                sender, TransactionPayload(payload)
            )
            txn_hash = await self.rest_client.submit_bcs_transaction(signed_transaction)
            await self.rest_client.wait_for_transaction(txn_hash)
            return txn_hash
        except Exception as e:
            print(f"Error transferring coins: {e}")
            return None


# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         blockchain = Client()

#         # Create accounts
#         alice = blockchain.create_account()
#         bob = blockchain.create_account()

#         print("Alice's address:", alice.address())
#         print("Bob's address:", bob.address())

#         # Fund accounts
#         await blockchain.fund_account(alice.address(), 100_000_000)
#         await blockchain.fund_account(bob.address(), 0)

#         # Get initial balances
#         print("Initial Balances:")
#         print("Alice's balance:", await blockchain.get_balance(alice.address()))
#         print("Bob's balance:", await blockchain.get_balance(bob.address()))

#         # Transfer coins
#         await blockchain.transfer(alice, bob.address(), 1_000_000)

#         # Get updated balances
#         print("Updated Balances:")
#         print("Alice's balance:", await blockchain.get_balance(alice.address()))
#         print("Bob's balance:", await blockchain.get_balance(bob.address()))

#         # Fetch transactions
#         transactions = await blockchain.fetch_account_transactions(str(alice.address()))
#         print("Alice's transactions:", transactions)

#         for tx in transactions:
#             details = await blockchain.fetch_fungible_asset_activities(tx["transaction_version"])
#             print(
#                 f"Details for transaction {tx['transaction_version']}: {details}")

#     asyncio.run(main())
