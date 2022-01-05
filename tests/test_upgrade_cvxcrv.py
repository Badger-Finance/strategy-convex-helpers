import brownie
from brownie import (
    accounts,
    interface,
    Contract,
    StrategyCvxCrvHelper,
    ERC20Upgradeable,
)
import pytest
from helpers.SnapshotManager import SnapshotManager

STRATEGIES = [
    "0x826048381d65a65DAa51342C51d464428d301896",  # CVX_CRV
]


@pytest.fixture
def proxy_admin():
    """
     Verify by doing web3.eth.getStorageAt("STRAT_ADDRESS", int(
        0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103
    )).hex()
    """
    yield interface.IProxyAdmin("0x20dce41acca85e8222d6861aa6d23b6c941777bf")


@pytest.fixture
def proxy_admin_gov():
    """
    Also found at proxy_admin.owner()
    """
    yield accounts.at("0x21cf9b77f88adf8f8c98d7e33fe601dc57bc0893", force=True)


@pytest.fixture
def bcvxCrv():
    yield interface.ISett("0x2B5455aac8d64C14786c3a29858E43b5945819C0")


@pytest.fixture
def bveCvx():
    yield interface.ISett("0xfd05D3C7fe2924020620A8bE4961bBaA747e6305")


@pytest.fixture
def badger_tree():
    yield interface.IBadgerTreeV2("0x660802fc641b154aba66a62137e71f331b6d787a")


@pytest.mark.parametrize(
    "strategy_address",
    STRATEGIES,
)
def test_upgrade_and_harvest(
    strategy_address, proxy_admin, proxy_admin_gov, bveCvx, badger_tree, bcvxCrv
):
    # Get deployed version from etherscan
    strategy_proxy = Contract.from_explorer(strategy_address)

    # Check some state variables to ensure upgrade doesn't mess up storage
    governance = strategy_proxy.governance()
    keeper = strategy_proxy.keeper()
    guardian = strategy_proxy.guardian()
    controller = strategy_proxy.controller()
    want = strategy_proxy.want()
    crvCvxCrvSlippageTolerance = strategy_proxy.crvCvxCrvSlippageToleranceBps()

    # Sanity checks
    assert strategy_proxy.version() == "1.1"

    # Deploy new logic
    new_logic = StrategyCvxCrvHelper.deploy({"from": governance})

    # Upgrade logic
    proxy_admin.upgrade(strategy_proxy, new_logic, {"from": proxy_admin_gov})
    strategy_proxy = StrategyCvxCrvHelper.at(strategy_address)

    # Approve contract access
    bveCvx.approveContractAccess(strategy_address, {"from": bveCvx.governance()})

    ## Checking all variables are as expected
    assert strategy_proxy.version() == "1.2"

    assert governance == strategy_proxy.governance()
    assert keeper == strategy_proxy.keeper()
    assert guardian == strategy_proxy.guardian()
    assert controller == strategy_proxy.controller()
    assert want == strategy_proxy.want()
    assert crvCvxCrvSlippageTolerance == strategy_proxy.crvCvxCrvSlippageToleranceBps()

    assert bveCvx.address == strategy_proxy.CVX_VAULT()
    assert badger_tree.address == strategy_proxy.BADGER_TREE()

    # Do a test harvest
    balance_tree_before = bveCvx.balanceOf(badger_tree)

    snap = SnapshotManager(
        bcvxCrv, strategy_proxy, interface.IController(controller), "StrategySnapshot"
    )

    snap.settHarvest({"from": accounts.at(keeper, force=True)})

    ## Check that Badger Tree has more bveCvx
    assert bveCvx.balanceOf(badger_tree) > balance_tree_before
    assert (
        brownie.history[-1].events["TreeDistribution"]["amount"]
        == bveCvx.balanceOf(badger_tree) - balance_tree_before
    )
