from project import my_wallet, delete_wallet, send_funds
from bitcoinlib.wallets import WalletError
import pytest

def test_my_wallet_for_new_valid_wallet():
    wallet = my_wallet("btc", new=True)[0]
    assert(wallet["name"]) == "btc"

def test_my_wallet_for_new_invalid_wallet():
    with pytest.raises(WalletError):
        my_wallet("", new=True)

def test_delete_existing_wallet():
    # delete wallet
    assert(delete_wallet("btc")) == True

def test_delete_nonexisting_wallet():
    # delete wallet
    with pytest.raises(ValueError):
        delete_wallet("btc1")


def test_send_funds():
    # create a wallet
    wallet = my_wallet("btc", new=True)

    passphrase = wallet[1].show_passphrase()
    
    receiver = "blt1qx30mmn2u2mf2ptyd3cavs7zq2dmunqnf950n2p"
    sending_amount = 1000
    
    balance_before_sending = float(wallet[0]["main_balance_str"].split(" ")[0])

    sending = send_funds(receiver, sending_amount, "normal")

    wallet = my_wallet("btc", new=False, passphrase=passphrase)
    
    balance_after_sending = float(wallet[0]["main_balance_str"].split(" ")[0])

    fees = float(sending["fee"]) / 100000000
    assert (balance_after_sending) == balance_before_sending - fees - (sending_amount / 100000000)
    