# cibil/utils.py

from wallet.models import Wallet

def check_wallet_balance(user, amount):
    wallet = Wallet.objects.get(user=user)

    if wallet.balance < amount:
        raise Exception("Please recharge wallet first")