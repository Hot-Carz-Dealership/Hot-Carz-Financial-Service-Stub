# tests/test_backend_routes.py
# this file contains unit tests for the Non-Financial Backend Endpoints here in this repo in routes.py

import os
import json
import secrets
import time
import pytest
import string
import random

import sqlalchemy.sql

from app import app, db
from app.models import CarInfo, Member, MemberSensitiveInfo, Employee, EmployeeSensitiveInfo, ServiceAppointment, \
    CarVINs, Services
from config import Config

'''

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!DONT EVER RUN PYTEST ALONE. ALWAYS RUN WITH THIS LINE BELOW!!!!
!!!!               'FLASK_ENV=testing pytest'                  !!!!
!!!!           OR ELSE OUR PRODUCTION DB IS FUCKED             !!!! 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

'''

# HOST_URL = "https://hot-carz-dealership-backend-production.up.railway.app"
app.config['SECRET_KEY'] = 'test'


@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client


def generate_random_string():  # generates the vin
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(17))


def test_entire_connection(client):
    # TEST API: /
    # ensures that the new push to dev does indeed connect to our hosting DB
    response = client.get('/')
    assert response.status_code == 200
    assert b"It works." in response.data


# def test_current_bids(client):
#     # TEST API: /api/member/current-bids
#
#     # Simulate a logged-in session
#     with client.session_transaction() as session:
#         session['member_session_id'] = 1  # Set the member session ID
#         member_id = session.get('member_session_id')
#
#     api_response = client.get('/api/member/current-bids', headers={'member_session_id': member_id})
#     assert api_response.status_code == 200
#     data = api_response.get_json()
#     assert isinstance(data, list)
#     data_columns = ["MSRP", "VIN", "bidID", "bidStatus", "bidValue", "make", "memberID", "model"]
#     for bid in data:
#         for key in data_columns:
#             assert key in bid
#             assert bid[key] is not None
#
#     # Simulate a POST request
#     confirmations = ['Processing', 'None', 'Member Processing', 'Processing', 'Denied', 'Confirmed']
#     for i in confirmations:
#         post_data = {
#             "bid_id": 1,
#             "new_bid_value": i
#         }
#         post_response = client.post('/api/member/current-bids', headers={'member_session_id': member_id}, json=post_data)
#         assert post_response.status_code == 200


def test_current_bids(client):
    # TEST API: /api/vehicle-purchase/new-bid-insert

    insert_data = {
        "member_id": 1,
        "vin": "SALSF2D47CA305941",
        "bid_value": 9999999
    }

    api_response = client.post('/api/vehicle-purchase/new-bid-insert', json=insert_data)
    assert api_response.status_code == 201
    data = api_response.get_json()
    assert data['message'] == 'Bid successfully inserted.'


def test_manager_current_bids(client):
    # TEST API: /api/manager/current-bids
    with client.session_transaction() as session:
        session['manager_session_id'] = 1  # Set the member session ID
        manager_id = session.get('manager_session_id')

    get_response = client.get("/api/manager/current-bids", headers={'manager_session_id': manager_id})
    assert get_response.status_code == 200
    data = get_response.get_json()
    assert data is not None
    assert isinstance(data, list)
    columns = ['bidID', 'make', 'model', 'VIN', 'MSRP', 'bidValue', 'bidStatus', 'memberID']
    for bid in data:
        for key in columns:
            assert key in bid
            assert bid[key] is not None

    confirmations = ['Confirmed', 'Denied', 'Processing', 'None', 'Member Processing']
    for i in confirmations:
        insert_data = {
            'bidID': 1,
            'confirmationStatus': i
        }
        post_response = client.post("/api/manager/current-bids", json=insert_data)
        assert post_response.status_code == 200
        data = post_response.get_json()
        assert data['message'] == 'Bid status updated successfully'

    insert_data = {
        'bidID': 999999999,
        'confirmationStatus': "None"
    }
    post_response = client.post("/api/manager/current-bids", headers={'manager_session_id': manager_id},
                                json=insert_data)
    assert post_response.status_code == 404
    data = post_response.get_json()
    assert data['error'] == 'Bid not found'


def test_get_financing(client):
    # TEST API: /api/manager/get-financing
    insert_data = {
        'member_id': 1
    }

    api_response = client.post('/api/manager/get-financing', json=insert_data)
    assert api_response.status_code == 200
    data = api_response.get_json()
    columns = ['VIN_carID', 'income', 'credit_score', 'loan_total', 'down_payment', 'percentage', 'monthly_payment_sum',
               'remaining_months', 'first_name', 'last_name', 'phone']

    for finance in data:
        for key in columns:
            assert key in finance

    api_response = client.post('/api/manager/get-financing', json={})
    assert api_response.status_code == 400
    data = api_response.get_json()
    assert data['message'] == 'Member ID is required'


def test_get_financing_details(client):
    # TEST API: /api/vehicle-purchase/apply-for-financing
    insert_data = {
        'member_id': 1,
        'Vin_carID': 'SALSF2D47CA305941',
        'down_payment': 30000.00,
        'monthly_income': 1500.00,
        'vehicle_cost': 35955.00
    }

    api_response = client.post('/api/vehicle-purchase/apply-for-financing', json=insert_data)
    assert api_response.status_code == 400
    data = api_response.get_json()
    assert data[
               'message'] == 'Your yearly income is not sufficient to take on this loan. Reapply with more down payment'

    insert_data['monthly_income'] = 5500.00

    api_response = client.post('/api/vehicle-purchase/apply-for-financing', json=insert_data)
    assert api_response.status_code == 200
    data = api_response.get_json()
    assert data is not None

    finance = data['financing_terms']
    columns = ['income', 'credit_score', 'loan_total', 'down_payment', 'percentage', 'monthly_payment_sum',
               'remaining_months', 'Vin_carID', 'financed_amount', 'interest_total']
    for key in columns:
        assert key in finance
        assert finance[key] is not None


def test_order_history(client):
    # TEST API: /api/member/order_history
    insert_data = {
        'member_id': 1,
    }

    api_response = client.get('/api/member/order_history', json=insert_data)
    assert api_response.status_code == 404
    assert api_response.get_json()['message'] == 'No orders found for the logged-in member.'

    insert_data = {
        'member_id': 2,
    }

    api_response = client.get('/api/member/order_history', json=insert_data)
    assert api_response.status_code == 200
    data = api_response.get_json()
    assert data is not None

    payment_columns = ["Amount Paid", "Confirmation Number", "Subtotal", "Taxes", "Total Financed", "items"]
    item_columns = ["Financed Amount", "Item Name", "Item Price"]

    for purchase in data:
        for key in payment_columns:
            assert key in purchase
            assert purchase[key] is not None
        for item in purchase['items']:
            for item_key in item_columns:
                assert item_key in item
                assert item[item_key] is not None
