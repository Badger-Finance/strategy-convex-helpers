import brownie
from brownie import MockToken, accounts, chain, Wei, interface, history
from helpers.constants import MaxUint256
from helpers.SnapshotManager import SnapshotManager
from helpers.time import days
from config.badger_config import sett_config
import pytest
from conftest import deploy
from rich.console import Console

console = Console()

## NOTE: Test is made redundant by StrategyCvxCrvHelperResolver
@pytest.mark.parametrize(
    "sett_id",
    sett_config.helpers,
)
def test_deposit_withdraw_single_user_flow(sett_id):
    if sett_id == "cvx":
        return 
    # Setup
    deployed = deploy(sett_config.helpers[sett_id])

    deployer = deployed.deployer
    sett = deployed.sett
    want = deployed.want
    strategy = deployed.strategy
    controller = deployed.controller
    settKeeper = accounts.at(sett.keeper(), force=True)

    snap = SnapshotManager(sett, strategy, controller, "StrategySnapshot")
    randomUser = accounts[6]
    # End Setup

    # Deposit
    assert want.balanceOf(deployer) > 0

    depositAmount = int(want.balanceOf(deployer) * 0.8)
    assert depositAmount > 0

    want.approve(sett.address, MaxUint256, {"from": deployer})

    snap.settDeposit(depositAmount, {"from": deployer})

    shares = sett.balanceOf(deployer)

    # Earn
    with brownie.reverts("onlyAuthorizedActors"):
        sett.earn({"from": randomUser})

    snap.settEarn({"from": settKeeper})

    chain.sleep(5000)
    chain.mine(1)

    ## Before Harvest, check the initial bveCVX balance
    tree = strategy.BADGER_TREE()
    veCVX = interface.ISett(strategy.CVX_VAULT())
    beforeBalance = veCVX.balanceOf(tree)
    
    ## Harvest
    snap.settHarvest({"from": settKeeper})

    ## Check that Badger Tree has more bveCVX
    assert veCVX.balanceOf(tree) > beforeBalance
    assert history[-1].events["TreeDistribution"]["amount"] == veCVX.balanceOf(tree) - beforeBalance



    snap.settWithdraw(shares // 2, {"from": deployer})

    chain.sleep(10000)
    chain.mine(1)

    snap.settWithdraw(shares // 2 - 1, {"from": deployer})