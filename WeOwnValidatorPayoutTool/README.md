# WeOwnValidatorPayoutTool

## Description

A Python script which can be used to automate TransferChx actions on the WeOwn Public Blockchain.

The primary use case for this script is to automate the composure, submission and notification of transactions containing TransferChx actions from a validator wallet, to one or more beneficiary wallets.

It can be combined with crontab or any other scheduling tools capable of executing python code to provide an end-to-end automation service.

## Stages

There are six stages to this script:

0. Setup variables: define the WeOwn public blockchain node API URL, validator wallet details & CHX reward beneficiaries' wallet details

1. Retrieve information about the validator wallet using the WeOwn public blockchain node api endpoint

2. Import the validator wallet using it's private key, compose, sign & prepare the Tx for submission

3. Submit the signed Tx using the WeOwn public blockchain node api endpoint, receive the json txHash from the response

4. Prepare telegram message variables: get current date & time, get local currency rate using coingecko api, calculate conversion of CHX amount to local currency value

5. Define a telegram message function, send a message to specified chatid with Tx details

## Prerequisites & Installation

TBC