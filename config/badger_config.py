from dotmap import DotMap
from helpers.eth_registry import registry

curve = registry.curve
pools = registry.curve.pools
convex = registry.convex
whales = registry.whales

sett_config = DotMap(
    cvx=DotMap(
        strategyName="StrategyCvxHelper",
        params=DotMap(
            want=registry.tokens.cvx,
            performanceFeeStrategist=0,
            performanceFeeGovernance=1000,
            withdrawalFee=10,
        ),
        test_config=DotMap(
            path=[registry.tokens.weth, registry.tokens.cvx],
        ),
    ),
    cvxCrv=DotMap(
        strategyName="StrategyCvxCrvHelper",
        params=DotMap(
            want=registry.tokens.cvxCrv,
            performanceFeeStrategist=0,
            performanceFeeGovernance=1000,
            withdrawalFee=10,
        ),
        test_config=DotMap(
            path=[registry.tokens.weth, registry.tokens.crv, registry.tokens.cvxCrv],
        ),
    ),
)

badger_config = DotMap(
    prod_json="deploy-final.json",
)

config = DotMap(
    badger=badger_config,
    sett=sett_config,
)