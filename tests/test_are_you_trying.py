import brownie
from brownie import *
from helpers.constants import MaxUint256
from helpers.SnapshotManager import SnapshotManager
from helpers.time import days
from helpers.utils import (
    approx,
)
from config.badger_config import sett_config
import pytest
from conftest import deploy

@pytest.mark.parametrize(
    "sett_id",
    sett_config.helpers,
)
def test_are_you_trying(sett_id):
    """
    Verifies that you set up the Strategy properly
    """
    # Setup
    deployed = deploy(sett_config.helpers[sett_id])

    deployer = deployed.deployer
    sett = deployed.sett
    want = deployed.want
    strategy = deployed.strategy

    startingBalance = want.balanceOf(deployer)

    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    assert startingBalance >= 0
    assert want.balanceOf(sett) == 0

    want.approve(sett, MaxUint256, {"from": deployer})
    sett.deposit(depositAmount, {"from": deployer})

    available = sett.available()
    assert available > 0

    sett.earn({"from": deployer})

    chain.sleep(10000 * 13)  # Mine so we get some interest

    ## TEST 1: Does the want get used in any way?
    assert want.balanceOf(sett) == depositAmount - available

    # Did the strategy do something with the asset?
    assert want.balanceOf(strategy) < available

    ## End Setup

    harvest = strategy.harvest({"from": deployer})

    harvest.events["Harvest"]["harvested"] > 0