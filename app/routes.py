# app/routes.py

import random
import re
import string

from flask import jsonify, request, session
from sqlalchemy import text

from . import app
from .models import *

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


@app.route('/api/member/vehicle-purchases', methods=['GET'])
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


@app.route('/api/member/payments', methods=['GET'])
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


@app.route('/api/vehicle-purchase/new-bid-insert', methods=['POST'])
def purchase_vehicle():
    member_session_id = session.get('member_session_id')
    if member_session_id is None:
        # redirect the user at this point to a login screen if they are not logged in to an account to purchase a vehicle
        return jsonify({'message': 'You need to log in to purchase a vehicle.'}), 401

    data = request.json
    vehicle_vin = data.get('vehicle_vin')
    payment_method = data.get('payment_method')
    member_id = data.get('member_id')
    payment_option = data.get('payment_option')  # Payment option: 'Card' or 'Check'
    vehicle_cost = return_vehicle_cost(vehicle_vin)

    if vehicle_vin == -1:
        return jsonify({'message': "CAR DOESNT EXIST"}), 400

    if payment_method == 'MSRP':
        if payment_option == 'Card':
            card_number = data.get('card_number')
            cvv = data.get('CVV')
            expiration_date = data.get('expirationDate')

            regex_card_check(card_number, cvv, expiration_date)

            if vehicle_cost > 5000:
                return jsonify({'message': 'Card payments are limited to $5000. The rest must be paid in person at '
                                           'the dealership.'}), 400

            msrp_vehicle_purchase_no_financing(vehicle_vin, payment_method, member_id, payment_option, card_number, cvv,
                                               expiration_date, vehicle_cost, routing_number=None, account_number=None)
        elif payment_option == 'Check':
            routing_number = data.get('routing_number')
            account_number = data.get('account_number')

            regex_bank_acct_check(routing_number, account_number)

            msrp_vehicle_purchase_no_financing(vehicle_vin, payment_method, member_id, payment_option, vehicle_cost,
                                               card_number=None, cvv=None, expiration_date=None, routing_number=None,
                                               account_number=None)  # parameter definitions, if there is an error due to
            # positioning just fix i cant tell here alone lol
        else:
            return jsonify({'message': 'Invalid payment option for MSRP.'}), 400
    else:
        bid_value = data.get('bidValue')
        bid_status = 'Processing'  # not sent from the frontend. The change to Confirmed/Denied
        if payment_option == 'Card':
            card_number = data.get('card_number')
            cvv = data.get('CVV')
            expiration_date = data.get('expirationDate')

            regex_card_check(card_number, cvv, expiration_date)

            bid_insert_no_financing(vehicle_vin, payment_method, member_id, bid_value, bid_status, payment_option,
                                    card_number, cvv, expiration_date, routing_number=None, account_number=None)
        else:
            routing_number = data.get('routing_number')
            account_number = data.get('account_number')

            regex_bank_acct_check(routing_number, account_number)
            bid_insert_no_financing(vehicle_vin, payment_method, member_id, bid_value, bid_status, payment_option,
                                    routing_number, account_number, card_number=None, cvv=None, expiration_date=None)

    return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200


def regex_card_check(card_number, cvv, expiration_date):
    # Regex validation for card number, CVV, and expiration date
    card_regex = re.compile(r'^[0-9]{16}$')
    cvv_regex = re.compile(r'^[0-9]{3}$')
    expiration_regex = re.compile(r'^(0[1-9]|1[0-2])/[0-9]{2}$')  # MM/YY experation date format

    if not card_regex.match(card_number):
        return False
    if not cvv_regex.match(cvv):
        return False
    if not expiration_regex.match(expiration_date):
        return False
    return True


def regex_bank_acct_check(routing_number, account_number):
    routing_regex = re.compile(r'^[0-9]{9}$')
    account_regex = re.compile(r'^[0-9]{9,12}$')  # Bank account numbers vary from 9 to 12 char length

    if not routing_regex.match(routing_number):
        return False
    if not account_regex.match(account_number):
        return False
    return True


@app.route('/api/vehicle-purchase/new-vehicle-purchase-no-finance', methods=['POST'])
def msrp_vehicle_purchase_no_financing(vehicle_vin, payment_method, member_id, payment_option, card_number, cvv,
                                       expiration_date, routing_number, account_number):
    # payment_option = check, card
    # payment_method = MSRP, BID

    try:
        # Insert purchase information into the database
        if payment_method == 'CARD':
            new_payment = Payments(
                paymentStatus='Confirmed',
                paymentPerMonth=None,
                financeLoanAmount=None,
                loanRatePercentage=None,
                valuePaid=None,
                valueToPay=None,
                initialPurchase=None,
                lastPayment=None,
                creditScore=None,
                income=None,
                paymentType=payment_option,  # payment_option = check, card
                servicePurchased='Vehicle Purchase',
                cardNumber=card_number,
                expirationDate=expiration_date,
                CVV=cvv,
                routingNumber=routing_number,
                bankAcctNumber=account_number,
                memberID=member_id
            )
        else:
            new_payment = Payments(
                paymentStatus='Confirmed',
                paymentPerMonth=None,
                financeLoanAmount=None,
                loanRatePercentage=None,
                valuePaid=None,
                valueToPay=None,
                initialPurchase=None,
                lastPayment=None,
                creditScore=None,
                income=None,
                paymentType=payment_option,  # payment_option = check, card
                servicePurchased='Vehicle Purchase',
                cardNumber=card_number,
                expirationDate=expiration_date,
                CVV=cvv,
                routingNumber=routing_number,
                bankAcctNumber=account_number,
                memberID=member_id
            )

        db.session.add(new_payment)
        db.session.commit()

        new_purchase = Purchases(
            paymentID=new_payment.paymentID,
            VIN_carID=vehicle_vin,
            memberID=member_id,
            paymentType='MSRP',  # Assuming this is MSRP payment
            bidStatus='Confirmed',  # Assuming the purchase is always confirmed for MSRP
            confirmationNumber=confirmation_number_generation()  # You may generate a confirmation number here
        )

        db.session.add(new_purchase)
        db.session.commit()

        return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/vehicle-purchase/new-bid-insert-no-finance', methods=['POST'])
def bid_insert_no_financing(vehicle_vin, payment_method, member_id, bid_value, bid_status, payment_option, card_number,
                            cvv, expiration_date, routing_number, account_number):
    # payment_option = check, card
    # payment_method = MSRP, BID
    try:
        if payment_option == 'CARD':
            new_payment = Payments(
                paymentStatus='pending',
                paymentPerMonth=None,
                financeLoanAmount=None,
                loanRatePercentage=None,
                valuePaid=None,
                valueToPay=None,
                initialPurchase=None,
                lastPayment=None,
                creditScore=None,
                income=None,
                paymentType=payment_option,
                servicePurchased='Vehicle Purchase',
                cardNumber=card_number,
                expirationDate=expiration_date,
                CVV=cvv,
                routingNumber=None,
                bankAcctNumber=None,
                memberID=member_id
            )
        elif payment_option == 'CHECK':
            # Create a new payment entry for check payments
            new_payment = Payments(
                paymentStatus='pending',
                paymentPerMonth=None,
                financeLoanAmount=None,
                loanRatePercentage=None,
                valuePaid=None,
                valueToPay=None,
                initialPurchase=None,
                lastPayment=None,
                creditScore=None,
                income=None,
                paymentType=payment_option,
                servicePurchased='Vehicle Purchase',
                cardNumber=None,
                expirationDate=None,
                CVV=None,
                routingNumber=routing_number,
                bankAcctNumber=account_number,
                memberID=member_id
            )
        else:
            return jsonify({'message': 'Invalid payment option. Choose CARD or CHECK.'}), 400

        # Add the new payment to the database session and commit
        db.session.add(new_payment)
        db.session.commit()

        # Create a new bid entry
        new_bid = Purchases(
            paymentID=new_payment.paymentID,
            VIN_carID=vehicle_vin,
            memberID=member_id,
            paymentType=payment_method,
            bidValue=bid_value,
            bidStatus=bid_status,
            confirmationNumber=confirmation_number_generation()  # You may generate a confirmation number here
        )

        # Add the new bid to the database session and commit
        db.session.add(new_bid)
        db.session.commit()

        return jsonify({'message': 'Bid successfully inserted.'}), 201

    except Exception as e:
        # Rollback the transaction in case of an error
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


def bid_table_insert(new_payment, vehicle_vin, member_id, payment_method, bid_value, bid_status):
    try:
        new_bid = Purchases(
            paymentID=new_payment.paymentID,
            VIN_carID=vehicle_vin,
            memberID=member_id,
            paymentType=payment_method,
            bidValue=bid_value,
            bidStatus=bid_status,
            confirmationNumber=confirmation_number_generation()  # You may generate a confirmation number here
        )

        # Add the new bid to the database session and commit
        db.session.add(new_bid)
        db.session.commit()

        return jsonify({'message': 'Bid successfully inserted.'}), 201
    except Exception as e:
        # Rollback the transaction in case of an error
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


def return_vehicle_cost(vehicle_vin):
    vehicle = Cars.query.filter_by(VIN_carID=vehicle_vin).first()
    if not vehicle:
        return -1
    return vehicle.price


def charCompany(cardNumber):
    if cardNumber[0] == '4':
        return 'Visa'
    elif cardNumber[0] == '5':
        return 'Mastercard'
    elif cardNumber[0] == '6':
        return 'Discover'
    elif cardNumber[0] == '3':
        return 'American Express'
    else:
        return 'Other'


# this function generates the confirmation number randomely
def confirmation_number_generation():
    totalChars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(totalChars) for i in range(13))


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


def check_loan_eligibility(loan_amount, monthly_income):
    # Calculate yearly income from monthly income
    yearly_income = monthly_income * 12

    # Calculate the loan amount and check if it's less than 10% of the yearly income
    if loan_amount <= (yearly_income * 0.1):
        return True  # User is eligible for the loan
    else:
        return False  # User is not eligible for the loan


def adjust_loan_with_downpayment(vehicle_cost, down_payment):
    # Recalculate the loan amount based on the new down_payment
    loan_amount = vehicle_cost - down_payment
    return loan_amount


@app.route('/api/vehicle-purchase/new-vehicle-purchase-finance/re-evaluate', methods=['POST'])
def reevaluate_finance():
    data = request.json
    reevaluate_loan = data.get('reevaluate_loan')  # no == 0, yes == 1
    return str(reevaluate_loan)


@app.route('/api/vehicle-purchase/new-vehicle-purchase-finance', methods=['POST'])
def new_vehicle_purchase_finance():
    try:
        data = request.json
        vehicle_vin = data.get('vehicle_vin')
        payment_method = data.get('payment_method')
        member_id = data.get('member_id')
        card_number = data.get('card_number')
        cvv = data.get('cvv')
        down_payment = data.get('down_payment')
        expiration_date = data.get('expiration_date')
        monthly_income = data.get('monthly_income')
        credit_score = creditScoreGenerator()
        vehicle_cost = return_vehicle_cost(vehicle_vin)
        total_cost = adjust_loan_with_downpayment(vehicle_cost, down_payment)
        financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)

        loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
        if not loan_eligibility:
            # we want to check if the user wants to re-evaluate their loan through a new downpayment amount
            reevaluate_loan = int(reevaluate_finance())
            if reevaluate_loan == 0:
                return jsonify({'message': 'Your yearly income is not sufficient to take on this loan.'}), 400
            elif reevaluate_loan == 1:
                new_down_payment = data.get('new_down_payment')
                total_cost = adjust_loan_with_downpayment(vehicle_cost, new_down_payment)
                new_financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
                loan_eligibility = check_loan_eligibility(new_financing_loan_amount, monthly_income)
                # if true, we can continue to storing everything and all the values !!.
                if not loan_eligibility:
                    return jsonify({'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400
            else:
                return jsonify({'message': 'Invalid Value'}), 400

        # signature retrival value | ENUM just to ensure we go something and not left blank.
        signature = get_signature()
        if signature != 1:
            return jsonify({'message': 'Please Insert Signature Value'})

        # Perform the purchase with financing
        new_payment = Payments(
            paymentStatus='Confirmed',
            paymentPerMonth=None,
            financeLoanAmount=financing_loan_amount,
            loanRatePercentage=None,  # You may calculate this based on credit score
            valuePaid=None,
            valueToPay=None,
            initialPurchase=None,
            lastPayment=None,
            creditScore=credit_score,
            income=monthly_income,
            paymentType='CARD',
            servicePurchased='Vehicle Purchase',
            cardNumber=card_number,
            expirationDate=expiration_date,
            CVV=cvv,
            routingNumber=None,
            bankAcctNumber=None,
            memberID=member_id
        )

        db.session.add(new_payment)
        db.session.commit()

        new_purchase = Purchases(
            paymentID=new_payment.paymentID,
            VIN_carID=vehicle_vin,
            memberID=member_id,
            paymentType=payment_method,
            bidStatus='Confirmed',  # Assuming the purchase is always confirmed for financing
            confirmationNumber=confirmation_number_generation()  # You may generate a confirmation number here
            # signature='YES'
        )

        db.session.add(new_purchase)
        db.session.commit()

        # payment stub generation can occur through the means of functions above with endpoints
        # /api/member/payments
        # /api/payments/<int:memberid>
        # honestly look at what the difference is in having the member id passed through the get request from the front end
        # vs through accessing it through the link through the value still sent through from the front end.
        # too many ways of doing things gets me confused ahhh

        return jsonify({'message': 'Vehicle purchase with financing processed successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/vehicle-purchase/new-bid-insert-no-finance/signature', methods=['POST'])
def get_signature():
    data = request.json
    signature = int(data.get('signature'))  # yes = 1, no = 0
    if signature == 0:
        return False
    elif signature == 1:
        return True
    else:
        return jsonify({'message': 'Invalid VALUE'}), 400


@app.route('/api/vehicle-purchase/new-bid-insert-no-finance', methods=['POST'])
def new_bid_purchase_finance():
    ...
