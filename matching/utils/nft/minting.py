from nftlabs.sdk import NftlabsSdk
from nftlabs.options import SdkOptions
from nftlabs.modules import nft_types

from django.conf import settings

def mint_nft_util(
        image_url,
        user1_name,
        user2_name
):

    nft_addy = settings.CRYPTO_NFT_ADDRESS

    pkey = settings.CRYPTO_PRIVATE_KEY

    # mainnet_url = "https://mainnet.infura.io/v3/e6d29871e62547acbfcc6b21601ff0e5"
    # testnet_url = "https://rpc-mumbai.maticvigil.com"

    url = settings.CRYPTO_HTTP_NODE_ENDPOINT
    print(f"URL: {url}")
    options = SdkOptions()
    sdk = NftlabsSdk(options=options, url=url, private_key=pkey)
    nft_module = sdk.get_nft_module(address=nft_addy)

    print(nft_module)

    mint_arg = nft_types.MintArg(
        name=f'{user1_name} meets {user2_name}',
        description=f"{user1_name} meets {user2_name} for the first time!",
        image_uri=image_url
    )

    ret_val = nft_module.mint(arg=mint_arg)
    print(ret_val.__dict__)

    return ret_val