# app/routes.py

from datetime import datetime
from flask import jsonify, request, session
from sqlalchemy import Text, text, func
from . import app
from .models import *
import random
import re

''' all the Financial Services APIs/ENDPOINTS are configured and exposed in this .py file '''


@app.route('/')
def testdb():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return '<h1>It works.</h1>'
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text


'''returns all purchases from the DB'''


@app.route('/api/purchases', methods=['GET'])
def all_purchases():
    purchases = Purchases.query.all()  # Query all purchases
    purchases_list = []  # List to store formatted purchases data

    for purchase in purchases:
        purchase_data = {
            'purchaseID': purchase.purchaseID,
            'paymentID': purchase.paymentID,
            'VIN_carID': purchase.VIN_carID,
            'memberID': purchase.memberID,
            'paymentType': purchase.paymentType,
            'bidValue': purchase.bidValue,
            'bidStatus': purchase.bidStatus,
            'confirmationNumber': purchase.confirmationNumber
        }
        purchases_list.append(purchase_data)

    return jsonify({'purchases': purchases_list}), 200


@app.route('/api/member/vehicle-purchases/', methods=['GET'])
def member_vehicle_purchases():
    member_session_id = session.get('member_session_id')

    if member_session_id is None:
        return jsonify({'message': 'No session id provided'}), 404

    vehicle_purchases_member = Purchases.query.filter_by(memberID=member_session_id).all()

    if not vehicle_purchases_member:
        return jsonify({'message': 'No purchases found for this member'}), 404

    # Extract necessary purchase details
    purchases_info = []
    for purchase in vehicle_purchases_member:
        car_info = Cars.query.filter_by(VIN_carID=purchase.VIN_carID).first()
        purchases_info.append({
            'purchaseID': purchase.purchaseID,
            'car_make': car_info.make,
            'car_model': car_info.model,
            'car_year': car_info.year,
            'payment_type': purchase.paymentType,
            'bid_value': purchase.bidValue,
            'bid_status': purchase.bidStatus,
            'confirmation_number': purchase.confirmationNumber
        })

    return jsonify(purchases_info), 200


@app.route('/api/member/payments/', methods=['GET'])
def member_purchases():
    member_session_id = session.get('member_session_id')

    if member_session_id is None:
        return jsonify({'message': 'No session id provided'}), 404

    payments_member = Payments.query.filter_by(memberID=member_session_id).all()

    if not payments_member:
        return jsonify({'message': 'No purchases found for this member'}), 404

    # Extract necessary purchase details
    payment_info = []
    for payment in payments_member:
        payment_data = {
            'paymentID': payment.paymentID,
            'paymentStatus': payment.paymentStatus,
            'paymentPerMonth': payment.paymentPerMonth,
            'financeLoanAmount': payment.financeLoanAmount,
            'loanRatePercentage': payment.loanRatePercentage,
            'valuePaid': payment.valuePaid,
            'valueToPay': payment.valueToPay,
            'initialPurchase': payment.initialPurchase,  # Convert to string
            'lastPayment': payment.lastPayment,  # Convert to string
            'creditScore': payment.creditScore,
            'income': payment.income,
            'paymentType': payment.paymentType,
            'servicePurchased': payment.servicePurchased,
            'cardNumber': payment.cardNumber,
            'expirationDate': payment.expirationDate,
            'CVV': payment.CVV,
            'routingNumber': payment.routingNumber,
            'bankAcctNumber': payment.bankAcctNumber
        }
        payment_info.append(payment_data)

    return jsonify(payment_info), 200


@app.route('/api/current-bids', methods=['GET', 'POST'])
def current_bids():
    if request.method == 'GET':
        # Retrieve information about cars with active bids
        cars_with_bids = db.session.query(Cars, Purchases) \
            .join(Purchases, Cars.VIN_carID == Purchases.VIN_carID) \
            .filter(Purchases.paymentType == 'BID', Purchases.bidStatus == 'Processing') \
            .all()

        # Format
        response = [{
            'make': car.make,
            'model': car.model,
            'VIN_carID': car.VIN_carID,
            'paymentType': purchase.paymentType,
            'bidValue': purchase.bidValue,
            'bidStatus': purchase.bidStatus,
            'confirmationDate': purchase.confirmationNumber
        } for car, purchase in cars_with_bids]

        return jsonify(response), 200

    elif request.method == 'POST':
        # we want to either confirm or reject the bid
        data = request.json
        VIN_carID = data.get('VIN_carID')
        bidStatus = data.get('bidStatus')  # pass "Confirmed" or "Denied"

        # Check if both parameters are provided
        if not (VIN_carID and bidStatus):
            return jsonify({'error': 'Both VIN_carID and bidStatus parameters are required.'}), 400

        # Update the bid status
        try:
            purchase = Purchases.query.filter_by(VIN_carID=VIN_carID, paymentType='BID').first()
            if purchase:
                purchase.bidStatus = bidStatus
                db.session.commit()
                return jsonify({'message': 'Bid status updated successfully'}), 200
            else:
                return jsonify({'error': 'No bid found for the specified car'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500


'''This API is used to insert NEW or MODIFY payment data from a customer based on the method and information passed along side of the request'''


@app.route('/api/payments/<int:member_id>', methods=['GET', 'POST'])
def manage_payments(member_id):
    if request.method == 'GET':
        try:
            # Retrieve payment information for the given memberID
            payments = Payments.query.filter_by(memberID=member_id).all()
            payments_info = []
            for payment in payments:
                payment_data = {
                    'paymentID': payment.paymentID,
                    'paymentStatus': payment.paymentStatus,
                    'paymentPerMonth': payment.paymentPerMonth,
                    'financeLoanAmount': payment.financeLoanAmount,
                    'loanRatePercentage': payment.loanRatePercentage,
                    'valuePaid': payment.valuePaid,
                    'valueToPay': payment.valueToPay,
                    'initialPurchase': payment.initialPurchase,  # Convert to string
                    'lastPayment': payment.lastPayment,  # Convert to string
                    'creditScore': payment.creditScore,
                    'income': payment.income,
                    'paymentType': payment.paymentType,
                    'servicePurchased': payment.servicePurchased,
                    'cardNumber': payment.cardNumber,
                    'expirationDate': payment.expirationDate,
                    'CVV': payment.CVV,
                    'routingNumber': payment.routingNumber,
                    'bankAcctNumber': payment.bankAcctNumber
                }
                payments_info.append(payment_data)
            return jsonify({'payments': payments_info}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif request.method == 'POST':
        try:
            # Extract data from the request body
            data = request.json
            payment_status = data.get('paymentStatus')
            payment_per_month = data.get('paymentPerMonth')
            finance_loan_amount = data.get('financeLoanAmount')
            loan_rate_percentage = data.get('loanRatePercentage')
            value_paid = data.get('valuePaid')
            value_to_pay = data.get('valueToPay')
            initial_purchase = data.get('initialPurchase')
            last_payment = data.get('lastPayment')
            credit_score = data.get('creditScore')
            income = data.get('income')
            payment_type = data.get('paymentType')
            service_purchased = data.get('servicePurchased')
            card_number = data.get('cardNumber')
            expiration_date = data.get('expirationDate')
            cvv = data.get('CVV')
            routing_number = data.get('routingNumber')
            bank_acct_number = data.get('bankAcctNumber')

            # Check if the member already has payment information
            existing_payment = Payments.query.filter_by(memberID=member_id).first()

            if existing_payment:
                # Update existing payment information
                existing_payment.paymentStatus = payment_status
                existing_payment.paymentPerMonth = payment_per_month
                existing_payment.financeLoanAmount = finance_loan_amount
                existing_payment.loanRatePercentage = loan_rate_percentage
                existing_payment.valuePaid = value_paid
                existing_payment.valueToPay = value_to_pay
                existing_payment.initialPurchase = initial_purchase
                existing_payment.lastPayment = last_payment
                existing_payment.creditScore = credit_score
                existing_payment.income = income
                existing_payment.paymentType = payment_type
                existing_payment.servicePurchased = service_purchased
                existing_payment.cardNumber = card_number
                existing_payment.expirationDate = expiration_date
                existing_payment.CVV = cvv
                existing_payment.routingNumber = routing_number
                existing_payment.bankAcctNumber = bank_acct_number
            else:
                # Create new payment information
                new_payment = Payments(memberID=member_id,
                                       paymentStatus=payment_status,
                                       paymentPerMonth=payment_per_month,
                                       financeLoanAmount=finance_loan_amount,
                                       loanRatePercentage=loan_rate_percentage,
                                       valuePaid=value_paid,
                                       valueToPay=value_to_pay,
                                       initialPurchase=initial_purchase,
                                       lastPayment=last_payment,
                                       creditScore=credit_score,
                                       income=income,
                                       paymentType=payment_type,
                                       servicePurchased=service_purchased,
                                       cardNumber=card_number,
                                       expirationDate=expiration_date,
                                       CVV=cvv,
                                       routingNumber=routing_number,
                                       bankAcctNumber=bank_acct_number)
                db.session.add(new_payment)

            # Commit changes to the database
            db.session.commit()

            return jsonify({'message': 'Payment information updated successfully'}), 200
        except Exception as e:
            # Rollback the session in case of any exception
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/api/vehiclePurchase', methods=['POST'])
def purchase_vehicle():
    ...


@app.route('/api/purchases/fullPrice', methods=['POST'])
def new_purchase():
    ...


def creditScoreGenerator() -> int:
    # generates a random creditScore
    return random.randint(500, 850)


def financingValue(vehicleCost: int, monthlyIncome: int, creditscore: int) -> float:
    # may be scuffed because i need to know more on more accurate rates but this might be ok
    if creditscore >= 750:
        base_loan_interest_rate = 5
    elif creditscore >= 700:
        base_loan_interest_rate = 10
    elif creditscore >= 650:
        base_loan_interest_rate = 15
    else:
        base_loan_interest_rate = 20

    # Calculate financing value based on vehicle cost and monthly income
    final_financing_percentage = base_loan_interest_rate + ((vehicleCost / monthlyIncome) * 100)
    financing_loan_value = (final_financing_percentage / 100) * vehicleCost

    return financing_loan_value
