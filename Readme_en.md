# ShoPen app

Шо? Pen?

## Readme

Ukrainian version of this readme is available [here](Readme.md).

## Description

This app is designed to be a system under test (SUT) for API test automation.  
It is a simple e-commerce app that allows users to create an account, log in, and buy pens.  
There are 2 user roles: `admin` and `customer`.  
Admin can manage pens in the shop as well as other users.  
Customers can buy pens.

## Features

- ✅ Stateful API
- ✅ Swagger doc
- ✅ Authentication with BE session token
- ✅ sqlite db, which is does not require installation
- ✅ covered with unit tests

## use cases

- Users can register, log in and log out.
- Users can get and edit info about themselves
- Admins can get and edit info about any user
- Admin can promote customer to become an admin
- Admin can set customer credit amount to buy pens
- Admin can add, delete and change stock amount of pens
- Any user (even without auth) can get list of pens
- Customer can request pens to be bought
- Customer can complete purchase operation within a short period of time (5 min by default)
- Customer can cancel purchase operation
- Customer can request a refund for a short period of time (20 min by default)
- In case customer requests pens for a big amount of money (5000 by default), it gets a wholesale discount (10% by
  default)
- Admin can get a discount in 20% by default for any purchases
- There is a service api to do a factory reset: create only 1 user and bunc of default pens

## Run locally

1. Git clone the repo
2. `pip install -r requirements.txt`
3. `python -m local.py`