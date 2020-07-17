import datetime
import requests
from requests.exceptions import HTTPError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from own_blockchain_sdk import Wallet, Tx

####################################################################################################
## STAGE ZERO - DEFINE BLOCKCHAIN NODE API URL, VALIDATOR WALLET DETAILS & CHX REWARD BENEFICIARIES' 
## WALLET DETAILS AS VARIABLES
####################################################################################################

# BLOCKCHAIN NODE API URL
node_api_url = 'https://wallet-node.mainnet.weown.com'

# VALIDATOR WALLET - (DO NOT USE THIS ADDRESS & PRIVATE KEY ON THE NETWORK!!!)
validator_wallet_addr = 'CHa52gXkAcfZ8RNnuTszdE3XvxaNhtrdFrM'
validator_wallet_pvt_key = '48wM487Ti6XGJW1oHopFfLiUKb5FLgArPTrZCcS4QHF3'

# CHX REWARD BENEFICIARY WALLETS
beneficiary1_wallet_addr = 'CHfree5ZSwDwKRh2btFG4UPGSwtSZxyqPeQ'
beneficiary2_wallet_addr = 'CHfree5ZSwDwKRh2btFG4UPGSwtSZxyqPeQ'

####################################################################################################
## STAGE ONE - GATHER INFORMATION ABOUT THE WALLET
####################################################################################################

# RETRY LOOP - ENSURE WEB REQUESTS TO BLOCKCHAIN NODE API ENDPOINT EXECUTE SUCCESSFULLY
retry_strategy = Retry(
total=100,
connect=100,
backoff_factor=1,
status_forcelist=[404, 429, 500, 502, 503, 504],
method_whitelist=["POST", "GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# GET WALLET INFORMATION FROM NODE API - WALLET: CHa52gXkAcfZ8RNnuTszdE3XvxaNhtrdFrM
wallet_info = http.get(node_api_url + "/address/" + validator_wallet_addr)
wallet_info.raise_for_status()

# ACCESS RESPONSE JSON CONTENT, DETERMINE AVAILABLE BALANCE & WALLET NONCE
wallet_info_response_json = wallet_info.json()
tx_nonce = wallet_info_response_json["nonce"]+1 # +1 FOR NEW Tx SUBMISSION
available_balance = wallet_info_response_json["balance"]["available"]-1 # -1 CHX FOR Tx FEES

# DIVIDE available_balance VARIABLE BETWEEN n AMOUNT OF BENEFICIARIES
chx_distribution = round(available_balance/2, 7) # DIVIDE BY 2, ROUND TO 7 . TO AVOID TX REJECTION

####################################################################################################
## STAGE TWO - IMPORT VALIDATOR WALLET, COMPOSE, SIGN & PREPARE Tx FOR SUBMISSION
####################################################################################################

# IMPORT VALIDATOR WALLET USING PRIVATE KEY - WALLET: CHa52gXkAcfZ8RNnuTszdE3XvxaNhtrdFrM
wallet = Wallet(validator_wallet_pvt_key)

# COMPOSE Tx WITH APPROPRIATE NONCE VALUE, SET EACH ACTION FEE AT 0.1 CHX
tx = Tx(wallet.address, tx_nonce, 0.1)
tx.add_transfer_chx_action(beneficiary1_wallet_addr, chx_distribution) # Transfer 50% remaining CHX
tx.add_transfer_chx_action(beneficiary2_wallet_addr, chx_distribution) # Transfer 50% remaining CHX

# SIGN Tx FOR SUBMISSION TO BLOCKCHAIN NODE API ENDPOINT, CREATE Tx JSON PAYLOAD VARIABLE
network_code = 'OWN_PUBLIC_BLOCKCHAIN_MAINNET'
json_tx_payload = tx.sign(network_code, wallet.private_key)

####################################################################################################
## STAGE THREE - SUBMIT Tx USING BLOCKCHAIN NODE API ENDPOINT, RECEIVE JSON TxHash FROM RESPONSE
####################################################################################################

# SEND A POST REQUEST TO THE BLOCKCHAIN NODE API ENDPOINT USING THE JSON PAYLOAD VARIABLE
tx_submission_url = node_api_url + "/tx"
tx_submission = http.post(tx_submission_url, json = json_tx_payload)
tx_submission.raise_for_status()

# ACCESS THE RESPONSE JSON CONTENT
tx_submission_response_json = tx_submission.json()

# DEBUG - COMMENT OUT LINE BELOW TO PRINT JSON RESPONSE FROM NODE API, SHOWS ERRORS IF ANY PRESENT
# print("Response from node API: ", tx_submission_response_json)

# ACCESS THE RESPONSE JSON CONTENT Tx HASH
tx_submission_response_txHash = tx_submission_response_json["txHash"]

####################################################################################################
## STAGE FOUR - PREPARE TELEGRAM MESSAGE VARIABLES
####################################################################################################

# TG MESSAGE - GET CURRENT DATE & TIME, CREATE VARIABLES
dtn = datetime.datetime.now()
dtn_ftime = (dtn.strftime("%d-%m-%Y %H:%M:%S %Z"))

# TG MESSAGE - GET LOCAL CURRENCY RATE USING COINGECKO API, CREATE VARIABLES
cg_chx_local_rate_response = http.get("https://api.coingecko.com/api/v3/simple/price?ids=chainium&vs_currencies=gbp")
cg_chx_local_rate_response.raise_for_status()
cg_chx_local_rate_response_json = cg_chx_local_rate_response.json()
cg_chx_local_rate = cg_chx_local_rate_response_json["chainium"]["gbp"]

# COINGECKO API API DOCUMENTATION: https://www.coingecko.com/api/documentations/v3
# LIST OF CURRENCY CODES: https://api.coingecko.com/api/v3/simple/supported_vs_currencies

# TG MESSAGE - CALCULATE CONVERSION TO LOCAL CURRENCY, APPLY FORMATTING, CREATE VARIABLES
local_available_balance = (format(available_balance*cg_chx_local_rate, '.2f'))
local_chx_distribution = (format(chx_distribution*cg_chx_local_rate, '.2f'))

####################################################################################################
## STAGE FIVE - DEFINE TELEGRAM MESSAGE FUNCTION, SEND MESSAGE TO SPECIFIED CHATID WITH Tx DETAILS
####################################################################################################

# TELEGRAM BOT - SEND MESSAGE FUNCTION
def telegram_bot_send_msg(bot_message):

   bot_token = 'TG_BOT_API_TOKEN'
   bot_chatID = 'TG_CHAT_ID'
   send_msg = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

   response = requests.get(send_msg)

   return response.json()

# TELEGRAM MESSAGE - COMPOSE MESSAGE WITH Tx DETAILS
my_message0 = "_⏰ {}_".format(dtn_ftime) + "\n\n" + "*VAL1 (PRIVATE) SENT A NEW REWARD DISTRIBUTION Tx*\n\n"
my_message1 = "*Total Value of Tx*\n"
my_message2 = "CHX ""{}".format(available_balance) + " 🌟\n£{}".format(local_available_balance) + " 💷\n\n"
my_message3 = "*Value of Each TransferChx Action\n*"
my_message4 = "CHX ""{}".format(chx_distribution) + " 🌟\n£{}".format(local_chx_distribution) + " 💷\n\n"
my_message5 = "*Tx Details*\nhttps://explorer.weown.com/tx/{}".format(tx_submission_response_txHash)
my_message_final = my_message0 + my_message1 + my_message2 + my_message3 + my_message4 + my_message5

# SEND TELEGRAM MESSAGE USING TELEGRAM BOT - SEND MESSAGE FUNCTION & my_message_final VARIABLE
telegram_bot_send_msg(my_message_final)