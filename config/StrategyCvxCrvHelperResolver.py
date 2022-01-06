from helpers.StrategyCoreResolver import StrategyCoreResolver
from brownie import interface
from rich.console import Console
from helpers.utils import val
from tabulate import tabulate

console = Console()


class StrategyCvxCrvHelperResolver(StrategyCoreResolver):

    # ===== override default =====
    def confirm_harvest_events(self, before, after, tx):
        key = "Harvest"
        assert key in tx.events
        assert len(tx.events[key]) == 1
        event = tx.events[key][0]
        keys = [
            "harvested",
        ]
        for key in keys:
            assert key in event

        console.print("[blue]== CvxCrv Helper Strat harvest() State ==[/blue]")
        self.printState(event, keys)

    def printState(self, event, keys):
        table = []
        for key in keys:
            table.append([key, val(event[key])])

        print(tabulate(table, headers=["account", "value"]))

    # ===== Strategies must implement =====
    def confirm_harvest(self, before, after, tx):
        console.print("=== Compare CvxCrv Helper Harvest() ===")

        self.confirm_harvest_events(before, after, tx)

        super().confirm_harvest(before, after, tx)

        # Strategy want should increase
        assert after.get("strategy.balanceOf") >= before.get("strategy.balanceOf")

        # PPFS should not decrease
        assert after.get("sett.pricePerFullShare") >= before.get(
            "sett.pricePerFullShare"
        )

        ## Custom check, bcvxCRV sent funds to badgerTree
        assert after.balances("bveCVX", "badgerTree") > before.balances("bveCVX", "badgerTree")
        
        ## Verify event triggered with the same amount
        tx.events["TreeDistribution"]["amount"] == after.balances("bveCVX", "badgerTree") - before.balances("bveCVX", "badgerTree")

        # Verify Governance got some bveCVX
        assert after.balances("bveCVX", "governanceRewards") > before.balances("bveCVX", "governanceRewards")
        
        # Strategist may have gotten some (as we tend to have strategist fees to 0)
        assert after.balances("bveCVX", "strategist") >= before.balances("bveCVX", "strategist")


    def get_strategy_destinations(self):
        """
        Track balances for all strategy implementations
        (Strategy Must Implement)
        """

        strategy = self.manager.strategy
        return {}

    def add_entity_balances_for_tokens(self, calls, tokenKey, token, entities):
        entities["strategy"] = self.manager.strategy.address
        entities["cvxCrvRewardsPool"] = self.manager.strategy.cvxCrvRewardsPool()
        entities["badgerTree"] = self.manager.strategy.BADGER_TREE()

        super().add_entity_balances_for_tokens(calls, tokenKey, token, entities)
        return calls

    def add_balances_snap(self, calls, entities):
        super().add_balances_snap(calls, entities)
        strategy = self.manager.strategy

        crv = interface.IERC20(strategy.crv())
        cvx = interface.IERC20(strategy.cvx())
        threeCrv = interface.IERC20(strategy.threeCrv())
        cvxCrv = interface.IERC20(strategy.cvxCrv())
        usdc = interface.IERC20(strategy.usdc())
        bveCVX = interface.IERC20(strategy.CVX_VAULT())

        calls = self.add_entity_balances_for_tokens(calls, "bveCVX", bveCVX, entities)
        calls = self.add_entity_balances_for_tokens(calls, "crv", crv, entities)
        calls = self.add_entity_balances_for_tokens(calls, "cvx", cvx, entities)
        calls = self.add_entity_balances_for_tokens(calls, "3Crv", threeCrv, entities)
        calls = self.add_entity_balances_for_tokens(calls, "cvxCrv", cvxCrv, entities)
        calls = self.add_entity_balances_for_tokens(calls, "usdc", usdc, entities)

        return calls
