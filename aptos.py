import asyncio
import random
import dotenv
import os
from swarm import Swarm, Agent
from client import Client  # Importing the Aptos Client from the other file
from swarm.repl import run_demo_loop

dotenv.load_dotenv()


class FinancialAgent:
    def __init__(self):
        self.blockchain_client = Client()

    async def transaction_monitoring_agent(self, account_address):
        transactions = await self.blockchain_client.fetch_account_transactions(account_address, limit=5)
        unusual_activity = [
            tx for tx in transactions if tx.get('amount', 0) > 1_000_000
        ]
        return f"Unusual activity detected: {unusual_activity}" if unusual_activity else "No unusual activity detected."

    async def portfolio_analysis_agent(self, account_address):
        """Analyze the token balances of an account."""
        balances = await self.blockchain_client.fetch_account_balances(account_address)
        return balances

    async def risk_assessment_agent(self, account_address):
        """Perform a detailed risk assessment based on transaction patterns and portfolio composition."""
        transactions = await self.blockchain_client.fetch_account_transactions(account_address, limit=20)
        balances = await self.blockchain_client.fetch_account_balances(account_address)

        total_tokens = sum(int(balance['amount']) for balance in balances)
        high_value_txs = [
            tx for tx in transactions if tx.get('amount', 0) > 500_000]
        risk_score = random.uniform(0, 1)

        return {
            "total_tokens": total_tokens,
            "high_value_transactions": len(high_value_txs),
            "risk_score": round(risk_score, 2)
        }


def transaction_monitoring(context_variables, account_address):
    """Risk assessment tool function"""
    agent = FinancialAgent()
    result = asyncio.run(agent.transaction_monitoring_agent(account_address))
    return result


def portfolio_analysis(context_variables, account_address):
    agent = FinancialAgent()
    result = asyncio.run(agent.portfolio_analysis_agent(account_address))
    return result


def risk_assessment(context_variables, account_address):
    agent = FinancialAgent()
    result = asyncio.run(agent.risk_assessment_agent(account_address))
    return result


agent = Agent(
    name="Financial Monitoring Agent",
    model="gpt-3.5-turbo",
    instructions="You are an AI agent that autonomously manages financial tasks, including monitoring, analysis, and risk assessment.",
    api_key=os.getenv("OPENAI_API_KEY"),
    functions=[transaction_monitoring, portfolio_analysis, risk_assessment]
)

if __name__ == "__main__":
    async def main():
        blockchain = Client()

        alice = blockchain.create_account()
        bob = blockchain.create_account()
        charles = blockchain.create_account()

        print("Alice's address:", alice.address())
        print("Bob's address:", bob.address())
        print("Charles's address:", charles.address())

        await blockchain.fund_account(alice.address(), 100_000_000)
        await blockchain.fund_account(bob.address(), 50_000_000)
        await blockchain.fund_account(charles.address(), 10_000_000)

        await blockchain.transfer(alice, bob.address(), 5_000_000)
        await blockchain.transfer(bob, charles.address(), 1_000_000)
        await blockchain.transfer(charles, alice.address(), 500_000)

    asyncio.run(main())

    run_demo_loop(agent, stream=True)
