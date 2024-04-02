# app/routes.py

import random
import re
import string
from datetime import datetime

from flask import jsonify, request, session
from sqlalchemy import text, func

from . import app
from .models import *

''' all the Financial Services APIs/ENDPOINTS are configured and exposed in this .py file '''
''' SESSIONS RN ARE BROKEN, WILL GET TO IT TMM, I LITERALLY JUST FIGURED OUT HOW TO EVEN START THIS'''


@app.route('/')
# test to make sure it runs and is connected to your DB. if it prints "it works" on your screen, you are connected to the DB correctly.
def testdb():
    try:
        db.session.query(text('1')).from_statement(text('SELECT 1')).all()
        return '<h1>It works.</h1>'
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text


@app.route('/api/purchases', methods=['GET'])
def all_purchases():
    # returns all purchases from the purchases Table in the DB
    purchases = Purchases.query.all()  # queries all purchases
    purchases_list = []

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
    # returns all of the vehicle purchases based on the memberID
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


@app.route('/api/vehicle-purchase/new-vehicle-no-finance/bid-accepted', methods=['POST'])
def vehicle_purchase_bid_accepted():
    data = request.json

    member_session_id = session.get('member_session_id')
    if member_session_id is None:
        return jsonify({'message': 'You need to log in to purchase a vehicle.'}), 401

    # Retrieve required data from request.json
    purchase_id = data.get('purchase_id')
    vehicle_vin = data.get('vehicle_vin')
    member_id = data.get('member_id')
    payment_option = data.get('payment_option')  # 'Card' or 'Check'
    payment_amount = data.get('payment_amount')
    bid = Purchases.query.filter_by(purchaseID=purchase_id, paymentType='BID').first()

    # Validate and retrieve card or check information based on payment_option
    if payment_option == 'Card':
        card_number = data.get('card_number')
        cvv = data.get('CVV')
        expiration_date = data.get('expirationDate')
        regex_card_check(card_number, cvv, expiration_date)
        if payment_amount > 5000:
            return jsonify({'message': 'Choose A lower value for Bank Cards'}), 400
    elif payment_option == 'Check':
        routing_number = data.get('routing_number')
        account_number = data.get('account_number')
        regex_bank_acct_check(routing_number, account_number)
    else:
        return jsonify({'message': 'Invalid payment option.'}), 400

    # Retrieve vehicle cost
    # vehicle_cost = return_vehicle_cost(vehicle_vin) # no need because the cost is based on the confirmed bid
    total_valuePaid = bid.bidValue - payment_amount

    # Create a payment entry
    new_payment = Payments(
        paymentStatus='Confirmed',
        paymentPerMonth=None,
        financeLoanAmount=None,
        loanRatePercentage=None,
        valuePaid=payment_amount,
        valueToPay=total_valuePaid,
        initialPurchase=datetime.now(),
        lastPayment=datetime.now(),
        creditScore=None,
        income=None,
        paymentType=payment_option,
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

    # Update the existing bid with the confirmed payment information
    bid = Purchases.query.filter_by(purchaseID=purchase_id, paymentType='BID').first()
    if bid:
        # dont delete | will incl. later
        # signature = get_signature()
        # if signature != 1:
        #     return jsonify({'message': 'Please Insert Signature Value'})
        # bid.signature = signature
        bid.confirmationNumber = confirmation_number_generation()  # Generate confirmation number
        db.session.commit()
        return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200
    else:
        return jsonify({'error': 'Bid not found for the specified member and vehicle, could not purchase vehicle'}), 404


'''This API is used to insert NEW or MODIFY payment data from a customer based on the method and information passed along side of the request'''


@app.route('/api/payments', methods=['GET', 'POST'])
def manage_payments():
    data = request.json
    member_id = data.get('memberID')
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


@app.route('/api/vehicle-purchase/new-vehicle-no-finance', methods=['POST'])
def purchase_vehicle():
    member_session_id = session.get('member_session_id')
    if member_session_id is None:
        # redirect the user at this point to a login screen if they are not logged in to an account to purchase a vehicle
        return jsonify({'message': 'You need to log in to purchase a vehicle.'}), 401

    data = request.json
    vehicle_vin = data.get('vehicle_vin')
    payment_method = data.get('payment_method')
    payment_amount = data.get('payment_amount')
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
            routing_number = None
            account_number = None

            regex_card_check(card_number, cvv, expiration_date)

            if payment_amount > 5000:
                return jsonify({'message': 'Card payments are limited to $5000. The rest must be paid in person at '
                                           'the dealership.'}), 400

            return msrp_vehicle_purchase_no_financing(vehicle_vin, payment_amount, member_id, payment_option,
                                                      card_number, cvv,
                                                      expiration_date, vehicle_cost, routing_number,
                                                      account_number)

        elif payment_option == 'Check':
            routing_number = data.get('routing_number')
            account_number = data.get('account_number')
            card_number = None
            cvv = None
            expiration_date = None

            regex_bank_acct_check(routing_number, account_number)

            return msrp_vehicle_purchase_no_financing(vehicle_vin, payment_amount, member_id, payment_option,
                                                      card_number, cvv,
                                                      expiration_date, vehicle_cost, routing_number,
                                                      account_number)

        else:
            return jsonify({'message': 'Invalid payment option for MSRP.'}), 400
    else:
        bid_value = data.get('bidValue')
        bid_status = 'Processing'  # not sent from the frontend. The change to Confirmed/Denied
        return bid_insert_no_financing(vehicle_vin, payment_method, member_id, bid_value, bid_status)


# return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200


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


def msrp_vehicle_purchase_no_financing(vehicle_vin, payment_amount, member_id, payment_option,
                                       card_number, cvv,
                                       expiration_date, vehicle_cost, routing_number,
                                       account_number):
    # payment_option = check, card
    # payment_method = MSRP, BID

    try:
        # Insert purchase information into the database
        signature_val = get_signature()  # don't worry about this rn i have to fix the DB and tables for this
        if signature_val != 'YES' or signature_val != 'NO':
            return signature_val  # returns an error back to the frontend

        valuePaid_value = payment_amount
        valueToPay_value = vehicle_cost - payment_amount

        new_payment = Payments(
            paymentStatus='Confirmed',
            paymentPerMonth=None,
            financeLoanAmount=None,
            loanRatePercentage=None,
            valuePaid=valuePaid_value,
            valueToPay=valueToPay_value,
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
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
            # signature=signature_val
        )

        db.session.add(new_purchase)
        db.session.commit()
        return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/vehicle-purchase/new-bid-insert-no-finance', methods=['POST'])
def bid_insert_no_financing(vehicle_vin, payment_method, member_id, bid_value, bid_status):
    # payment_option = check, card
    # payment_method = MSRP, BID
    try:
        # Create a new bid entry
        next_payment_id = db.session.query(func.max(Payments.paymentID)).scalar() + 1
        new_bid = Purchases(
            paymentID=next_payment_id,
            VIN_carID=vehicle_vin,
            memberID=member_id,
            paymentType=payment_method,
            bidValue=bid_value,
            bidStatus=bid_status,
            confirmationNumber=None
            # confirmationNumber=confirmation_number_generation()  # You may generate a confirmation number here
            # signature='YES'
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
    # may be scuffed because I need to know more on more accurate rates but this might be ok
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


''' API to use to purchase a vehicle at MSRP with financing from the dealership'''


@app.route('/api/vehicle-purchase/new-vehicle-purchase-finance', methods=['POST'])
def new_vehicle_purchase_finance():
    try:
        member_session_id = session.get('member_session_id')
        if member_session_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        data = request.json
        vehicle_vin = data.get('vehicle_vin')
        payment_method = data.get('payment_method')
        member_id = data.get('member_id')
        down_payment = data.get('down_payment')
        monthly_income = data.get('monthly_income')

        if payment_method == 'CARD':
            card_number = data.get('card_number')
            cvv = data.get('cvv')
            expiration_date = data.get('expirationDate')
            routingNumber = None
            bankAcctNumber = None
            if down_payment > 5000:
                return jsonify({'message': 'Card payments are limited to $5000. The rest must be paid in person at '
                                           'the dealership.'}), 400
        else:
            routingNumber = data.get('routingNumber')
            bankAcctNumber = data.get('bankAcctNumber')
            card_number = None
            cvv = None
            expiration_date = None

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
                financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
                loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
                # if true, we can continue to storing everything and all the values !!.
                if not loan_eligibility:
                    return jsonify({'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400
            else:
                return jsonify({'message': 'Invalid Value'}), 400

        # signature retrival value | ENUM just to ensure we go something and not left blank.
        signature = get_signature()
        if signature != 1:
            return jsonify({'message': 'Please Insert Signature Value'})

        downPayment_value = total_cost - financing_loan_amount
        valueToPay_value = total_cost - downPayment_value
        paymentPerMonth_value = financing_loan_amount / 12

        # DB insert for new purchase with financing
        new_payment = Payments(
            paymentStatus='Confirmed',
            paymentPerMonth=paymentPerMonth_value,
            financeLoanAmount=financing_loan_amount,
            loanRatePercentage=credit_score,
            valuePaid=downPayment_value,
            valueToPay=valueToPay_value,
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
            creditScore=credit_score,
            income=monthly_income,
            paymentType='CARD',
            servicePurchased='Vehicle Purchase',
            cardNumber=card_number,
            expirationDate=expiration_date,
            CVV=cvv,
            routingNumber=routingNumber,
            bankAcctNumber=bankAcctNumber,
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
        # /api/member
        # /api/payments

        return jsonify({'message': 'Vehicle purchase with financing processed successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/vehicle-purchase/signature', methods=['POST'])
def get_signature():
    data = request.json
    signature = int(data.get('signature'))  # yes = 1, no = 0
    if signature == 0:
        return 'NO'
    elif signature == 1:
        return 'YES'
    else:
        return jsonify({'message': 'Invalid VALUE'}), 400


@app.route('/api/vehicle-purchase/bid-confirmed-financed-purchase', methods=['POST'])
def new_bid_purchase_finance():
    try:
        member_session_id = session.get('member_session_id')
        if member_session_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        data = request.json
        purchase_id = data.get(
            'purchase_id')  # value passed from button press from the frontend corresponding to the purchase ID of the Bid
        member_id = data.get('member_id')
        payment_method = data.get('payment_method')
        down_payment = data.get('down_payment')
        monthly_income = data.get('monthly_income')

        bid_information = Purchases.query.filter_by(purchaseID=purchase_id, paymentType='BID').first()
        if bid_information:
            vehicle_vin = bid_information.VIN_carID
            vehicle_information = Cars.query.filter_by(VIN_carID=vehicle_vin).first()
            if vehicle_information:
                if payment_method == 'CARD':
                    card_number = data.get('card_number')
                    cvv = data.get('cvv')
                    expiration_date = data.get('expirationDate')
                    routingNumber = None
                    bankAcctNumber = None
                    if down_payment > 5000:
                        return jsonify(
                            {'message': 'Card payments are limited to $5000. The rest must be paid in person at '
                                        'the dealership.'}), 400
                else:
                    routingNumber = data.get('routingNumber')
                    bankAcctNumber = data.get('bankAcctNumber')
                    card_number = None
                    cvv = None
                    expiration_date = None

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
                        financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
                        loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
                        # if true, we can continue to storing everything and all the values !!.
                        if not loan_eligibility:
                            return jsonify(
                                {'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400
                    else:
                        return jsonify({'message': 'Invalid Value'}), 400

                # signature retrival value | ENUM just to ensure we go something and not left blank.
                signature = get_signature()
                if signature != 1:
                    return jsonify({'message': 'Please Insert Signature Value'})

                downPayment_value = total_cost - financing_loan_amount
                valueToPay_value = total_cost - downPayment_value
                paymentPerMonth_value = financing_loan_amount / 12

                # DB insert for new purchase with financing
                new_payment = Payments(
                    paymentStatus='Confirmed',
                    paymentPerMonth=paymentPerMonth_value,
                    financeLoanAmount=financing_loan_amount,
                    loanRatePercentage=credit_score,
                    valuePaid=downPayment_value,
                    valueToPay=valueToPay_value,
                    initialPurchase=datetime.now(),
                    lastPayment=datetime.now(),
                    creditScore=credit_score,
                    income=monthly_income,
                    paymentType='CARD',
                    servicePurchased='Vehicle Purchase',
                    cardNumber=card_number,
                    expirationDate=expiration_date,
                    CVV=cvv,
                    routingNumber=routingNumber,
                    bankAcctNumber=bankAcctNumber,
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
            else:
                return jsonify({'error': 'Vehicle not found for the specified purchase ID'}), 404
        else:
            return jsonify({'error': 'Bid not found for the specified purchase ID'}), 404
        return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500
