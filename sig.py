from py_eth_sig_utils import utils
from py_eth_sig_utils.signing import recover_typed_data, signature_to_v_r_s


data = {
    "types": {
        "EIP712Domain": [
            { "name": 'name', "type": 'string' },
            { "name": 'version', "type": 'string' },
            { "name": 'chainId', "type": 'uint256' },
        ],
        "Message": [
            { "name": 'content', "type": 'string' }
        ]
    },
    "primaryType": 'Message',
    "domain": {
        "name": 'DwebLab Alpha',
        "version": '1',
        "chainId": 80001,
    },
    "message": {
        "content": 'Sign this msg to login',
    },
}


def recover_address(signature):
    try:
        signer_address = recover_typed_data(data, *signature_to_v_r_s(bytes.fromhex(signature)))
    except Exception as e:
        print(signature)
        print(e)
        return ''
    return signer_address
