from brownie import (
    accounts,
    interface,
    Controller,
    SettV4,
    StrategyCvxCrvHelper,
    StrategyCvxHelper,
    Wei,
    accounts
)
from config import (
    BADGER_DEV_MULTISIG,
)
from dotmap import DotMap
import pytest
from rich.console import Console
from helpers.test.test_utils import generate_test_assets

console = Console()


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def deploy(sett_config):
    """
    Deploys, vault, controller and strats and wires them up for you to test
    """
    deployer = accounts[0]

    strategist = deployer
    keeper = deployer
    guardian = deployer

    governance = accounts.at(BADGER_DEV_MULTISIG, force=True)

    controller = Controller.deploy({"from": deployer})
    controller.initialize(BADGER_DEV_MULTISIG, strategist, keeper, BADGER_DEV_MULTISIG)

    # Get Sett arguments:
    args = [
        sett_config.params.want,
        controller,
        BADGER_DEV_MULTISIG,
        keeper,
        guardian,
        False,
        "",
        "",
    ]

    sett = SettV4.deploy({"from": deployer})
    sett.initialize(*args)

    sett.unpause({"from": governance})
    controller.setVault(sett.token(), sett)

    # Get Strategy arguments:
    args = [
        BADGER_DEV_MULTISIG,
        strategist,
        controller,
        keeper,
        guardian,
        [
            sett_config.params.performanceFeeGovernance,
            sett_config.params.performanceFeeStrategist,
            sett_config.params.withdrawalFee,
        ],
    ]

    ## Start up Strategy
    if sett_config.strategyName == "StrategyCvxHelper":
        strategy = StrategyCvxHelper.deploy({"from": deployer})
    elif sett_config.strategyName == "StrategyCvxCrvHelper":
        strategy = StrategyCvxCrvHelper.deploy({"from": deployer})
    strategy.initialize(*args)

    # Call patchPaths and setCrvCvxCrvSlippageToleranceBps on Strategy
    strategy.patchPaths({"from": governance})
    strategy.setCrvCvxCrvSlippageToleranceBps(500, {"from": governance})

    ## Set up tokens
    want = interface.IERC20(strategy.want())

    ## Wire up Controller to Strart
    ## In testing will pass, but on live it will fail
    controller.approveStrategy(want, strategy, {"from": governance})
    controller.setStrategy(want, strategy, {"from": deployer})

    # Generate test want for user
    generate_test_assets(deployer, sett_config.test_config.path, Wei("5 ether"))

    assert want.balanceOf(deployer.address) > 0

    ## Whitelist from CVX Vault
    veCVX = interface.ISett(strategy.CVX_VAULT())
    veGov = accounts.at(veCVX.governance(), force=True)
    veCVX.approveContractAccess(strategy, {"from": veGov})

    return DotMap(
        deployer=deployer,
        controller=controller,
        sett=sett,
        strategy=strategy,
        want=want,
    )
