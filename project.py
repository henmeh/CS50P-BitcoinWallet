import tkinter as tk
import os
from bitcoinlib.wallets import wallet_create_or_open, wallet_delete_if_exists, WalletError, BCL_DATABASE_DIR
from bitcoinlib.mnemonic import Mnemonic
import json

# First recreate database to avoid already exist errors
test_databasefile = os.path.join(BCL_DATABASE_DIR, 'bitcoinlib.test.sqlite')
test_database = 'sqlite:///' + test_databasefile
#if os.path.isfile(test_databasefile):
#    os.remove(test_databasefile)

# main window
root = tk.Tk()

# label to show all the wallet data for the user
user_wallet_data = tk.Label(root, text="Create your wallet first")
entry_receiver_address = tk.Entry(root)
entry_amount = tk.Entry(root)

scrollbar = tk.Scrollbar(root)


class Table:
    def __init__(self, root, rows, columns, data):
        self.rows = rows
        self.columns = columns
        self.data = data
        i = 0
        # second column depends on the dict value
        for key, value in self.data.items():
            # plotting always the first column
            self.label_1 = tk.Label(
                root, text=f"{key}: ", justify="left", width=20, height=1
            )
            self.label_1.grid(row=i, column=2)

            if key == "receive_addresses" or key == "change_addresses":
                myList = tk.Listbox(root, yscrollcommand=scrollbar.set, width=65, height=5, selectmode="single")
                for address in value:
                    myList.insert(tk.END, f"{address['address']}   balance: {address['balance']}   used: {address['used']}")
                myList.grid(row=i, column=3)
                scrollbar.config(command=myList.yview)
            elif key == "transactions":
                myList = tk.Listbox(root, yscrollcommand=scrollbar.set, width=65, height=5)
                for transaction in value:
                    myList.insert(tk.END, f"txid: {transaction['txid']}   confirmations: {transaction['confirmations']}")
                myList.grid(row=i, column=3)
                scrollbar.config(command=myList.yview)
            else:
                text = tk.StringVar()
                text.set(f"{value}")
                self.label_2 = tk.Entry(
                    root, bd=0, state="readonly", textvariable=text, width=20
                )
                self.label_2.grid(row=i, column=3)
            i += 1


class User_Wallet:
    def __init__(self, wallet_name, new=True, passphrase=False):
        if new:
            self.passphrase = Mnemonic().generate()
            self.wallet_name = wallet_name
            self.wallet = wallet_create_or_open(
            self.wallet_name,
            keys=self.passphrase,
            network='bitcoinlib_test', 
            db_uri=test_database,
            witness_type="segwit",
            )
            self.wallet.utxos_update()
            self.wallet.send_to(self.wallet.get_key(), 50000000)
        
        else:
            self.passphrase = passphrase
            self.wallet_name = wallet_name
            self.wallet = wallet_create_or_open(
            self.wallet_name,
            keys=self.passphrase,
            network='bitcoinlib_test', 
            db_uri=test_database,
            witness_type="segwit",
            )


    def get_user_wallet(self):
        return self.wallet

    def __str__(self):
        #self.wallet.scan()
        return f"{self.wallet.info()}"

    def show_passphrase(self):
        return f"{self.passphrase}"

    def show_wallet_scan(self):
        return f"{self.wallet.scan()}"

    def get_wallet_info(self):
        return self.wallet.as_dict()


def my_wallet(wallet_name, widgets=[], new=False, passphrase=False):
    try:
        # create an instance of the User_Wallet object
        global user_wallet
        user_wallet = User_Wallet(wallet_name, new=new, passphrase=passphrase)
        #user_wallet.get_user_wallet().scan()

        if new:
            # store wallet_name in a separate txt-file
            wallet = {"name": wallet_name, "passphrase": user_wallet.show_passphrase()}
            json_wallet = json.dumps(wallet)
            with open("wallets.json", "a") as file:
                file.write(json_wallet)
                file.write("\n")              

        # fetch all user wallet data
        data = user_wallet.get_wallet_info()

        print(user_wallet.show_passphrase())

        # update the visualization of the wallet data
        user_wallet_data.config(text="")
        receive_addresses = []
        change_addresses = []

        for i in range(len(data["keys"])):
            address = {
                    "address": data["keys"][i]["address"],
                    "used": data["keys"][i]["used"],
                    "balance": data["keys"][i]["balance"],
                }

            if data["keys"][i]["depth"] == 5 and data["keys"][i]["change"] == 0:
                receive_addresses.append(address)
            elif data["keys"][i]["depth"] == 5 and data["keys"][i]["change"] == 1:
                change_addresses.append(address)

        wallet_data = {
            "wallet_id": data["wallet_id"],
            "wallet_name": data["name"],
            "wallet_scheme": data["scheme"],
            "witness_type": data["witness_type"],
            "network": data["main_network"],
            "balance": data["main_balance_str"],
            "transactions": data["transactions"],
            "receive_addresses": receive_addresses,
            "change_addresses": change_addresses,
        }
        
        Table(root, 3, 2, wallet_data)

        # remove the entry widgets for a new wallet
        for widget in widgets:
            widget.grid_remove()

        # show the update wallet data button
        button_update_wallet_data = tk.Button(
            root,
            command=lambda: my_wallet(user_wallet.get_wallet_info()["name"], new=False, passphrase=user_wallet.show_passphrase()),
            text="Update Wallet data",
            state=tk.NORMAL,
            width=15,
        )

        button_update_wallet_data.grid(row=0, column=1, pady=10)

        # show entry receiver address
        entry_receiver_address.grid(row=1, column=1, padx=10, pady=5)
        entry_receiver_address.insert(0, "insert receiver address")

        # show entry ammounts
        entry_amount.grid(row=2, column=1, padx=10, pady=5)
        entry_amount.insert(0, "insert sending amount in BTC")

        # show the send funds button
        button_send_funds = tk.Button(
            root,
            command=lambda: send_funds(
                entry_receiver_address.get(), entry_amount.get(), "normal"
            ),
            text="Send Funds",
            state=tk.NORMAL,
            width=15,
        )

        button_send_funds.grid(row=3, column=1, pady=10)

        # show the delete wallet button
        button_check_tx = tk.Button(
            root,
            command=lambda: delete_wallet(user_wallet.get_wallet_info()["name"]),
            text="Delete Wallet",
            state=tk.NORMAL,
            width=15,
        )

        button_check_tx.grid(row=5, column=1, pady=10)

        # return value for making the function testable with pytest
        return [user_wallet.get_wallet_info(), user_wallet]

    except WalletError:
        error = tk.Label(root, text="Please check your input for wallet creation!!")
        error.grid(row=0, column=1)
        raise WalletError


def delete_wallet(wallet_name):
    if wallet_delete_if_exists(wallet_name, db_uri=test_database, force=True):

        # get all locally stored wallets
        wallets = get_all_stored_user_wallets()

        # remove the wallet that was deleted also from the local storing
        for item in wallets:
            #print(wallets[i]["name"])
            if item.get("name") == wallet_name:
                wallets.remove(item)

        # update local stored wallet names
        if len(wallets) == 0:
            with open("wallets.json", "w") as file:
                file.write("")
        
        else:
            for wallet in wallets:
                json_wallet = json.dumps(wallet)
                with open("wallets.json", "w") as file:
                    file.write(json_wallet)
                    file.write("\n")

        return True
    
    else:
        raise ValueError


def send_funds(receiever, amount, fee):
    tx = user_wallet.get_user_wallet().send([(receiever, int(amount))], network='bitcoinlib_test', offline=False)

    print(tx.info())

    # rescan the wallet to update the balances and other wallet info
    my_wallet(user_wallet.get_wallet_info()["name"], new=False, passphrase=user_wallet.show_passphrase())

    return tx.as_dict()


def get_all_stored_user_wallets():
    # list with all already created wallets
    wallets = []
    with open("wallets.json") as file:
        for line in file:
            json_wallet = json.loads(line)
            wallets.append(json_wallet)
    return wallets
    

def main():
    # window title
    root.title("CS50P-BitcoinWallet")

    # window geometry
    root.geometry("1000x800")

    # entry wallet name
    entry_wallet_name = tk.Entry(root)
    entry_wallet_name.grid(row=0, column=1, padx=10, pady=5)
    entry_wallet_name.insert(0, "default name")

    # button to create a new wallet
    button_create = tk.Button(
        root,
        command=lambda: my_wallet(
            entry_wallet_name.get(), [entry_wallet_name, button_create], new=True, passphrase=False
        ),
        text="Create new Wallet",
        state=tk.NORMAL,
        width=15,
    )
    button_create.grid(row=1, column=1, pady=10)

    # list with all already created wallets
    wallets = get_all_stored_user_wallets()

    for i in range(len(wallets)):
        # buttons to load an existing wallet
        button_load = tk.Button(
            root,
            command=lambda j=i: my_wallet(
                wallets[j]["name"], [entry_wallet_name, button_create], new=False, passphrase=wallets[j]["passphrase"]
            ),
            text=f"{wallets[i]['name']}",
            state=tk.NORMAL,
            width=5,
        )
        button_load.grid(row=i, column=0, pady=10)

    # show main window
    root.mainloop()


if __name__ == "__main__":
    main()
