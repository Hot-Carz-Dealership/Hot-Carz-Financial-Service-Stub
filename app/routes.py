# app/routes.py

import random
import re
import string
from datetime import datetime

from flask import jsonify, request, session
from sqlalchemy import text, desc, func

from . import app
from .models import *

''' all the Financial Services APIs/ENDPOINTS are configured and exposed in this .py file '''

'''ALL PURCHASES ARE NOW ONLY MADE WITH BANK ROUTING AND ACCT NUMBER'''


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
# this endpoint returns all of the purchase information to be viewed by the manager or superAdmin
def all_purchases():
    # returns all purchases from the purchases Table in the DB
    purchases = Purchases.query.all()  # queries all purchases
    purchases_list = []

    for purchase in purchases:
        purchase_data = {
            'purchaseID': purchase.purchaseID,
            'bidID': purchase.bidID,
            'VIN_carID': purchase.VIN_carID,
            'memberID': purchase.memberID,
            'confirmationNumber': purchase.confirmationNumber
        }
        purchases_list.append(purchase_data)

    return jsonify({'purchases': purchases_list}), 200


@app.route('/api/member/vehicle-purchases', methods=['GET'])
# this endpoint is used to return all vehicle purchase information for an authorized customer to view their past vehicle purchases
def member_vehicle_purchases():
    member_session_id = session.get('member_session_id')  # sessions with Auth for a member who has bought a customer
    if member_session_id is None:
        return jsonify({'message': 'No session id provided'}), 404

    vehicle_purchases_member = Purchases.query.filter_by(
        memberID=member_session_id).all()  # returns vehicles purchased by the customer/member
    if not vehicle_purchases_member:
        return jsonify({'message': 'No purchases found for this member'}), 404

    # Extract necessary purchase details
    purchases_info = []
    for purchase in vehicle_purchases_member:
        car_info = CarInfo.query.filter_by(VIN_carID=purchase.VIN_carID).first()
        bid_info = Bids.query.filter_by(bidID=purchase.bidID).first()

        # Access payment type directly from purchase object
        payment_type = purchase.payment.paymentType

        purchases_info.append({
            'purchaseID': purchase.purchaseID,
            'car_make': car_info.make,
            'car_model': car_info.model,
            'car_year': car_info.year,
            'payment_type': payment_type,
            'bid_value': bid_info.bidValue,
            'bid_status': bid_info.bidStatus,
            'confirmation_number': purchase.confirmationNumber
        })
    return jsonify(purchases_info), 200


@app.route('/api/member/payments', methods=['GET'])
# this endpoint is used to return the payment informations of the member who is authorized into the dealership and logged in
def member_purchases():
    member_session_id = session.get('member_session_id')
    if member_session_id is None:
        return jsonify({'message': 'No session id provided'}), 404

    payments_member = Payments.query.filter_by(
        memberID=member_session_id).all()  # returns all payment information of the member
    if not payments_member:
        return jsonify({'message': 'No purchases found for this member'}), 404

    # returns necessary purchase details
    payment_info = []
    for payment in payments_member:
        payment_data = {
            'paymentID': payment.paymentID,
            'paymentStatus': payment.paymentStatus,
            'valuePaid': payment.valuePaid,
            'valueToPay': payment.valueToPay,
            'initialPurchase': payment.initialPurchase,  # Convert to string
            'lastPayment': payment.lastPayment,  # Convert to string
            'paymentType': payment.paymentType,
            'cardNumber': payment.cardNumber,
            'expirationDate': payment.expirationDate,
            'CVV': payment.CVV,
            'routingNumber': payment.routingNumber,
            'bankAcctNumber': payment.bankAcctNumber,
            'memberID': payment.memberID,
            'financingID': payment.financingID
        }
        payment_info.append(payment_data)
    return jsonify(payment_info), 200


@app.route('/api/current-bids', methods=['GET', 'POST'])
def current_bids():
    if request.method == 'GET':
        # GET Protocol, you want to return all current bids
        bids = Bids.query.all()
        bid_data = []
        for bid in bids:
            purchase = Purchases.query.filter_by(bidID=bid.bidID).first()
            if purchase:
                car = CarInfo.query.filter_by(VIN_carID=purchase.VIN_carID).first()
                if car:
                    bid_info = {
                        'make': car.make,
                        'model': car.model,
                        'VIN': car.VIN_carID,
                        'MSRP': car.price,
                        'bidValue': bid.bidValue,
                        'bidStatus': bid.bidStatus
                    }
                    bid_data.append(bid_info)
        return jsonify(bid_data)
    elif request.method == 'POST':
        # this POST request is to be used by managers to Confirm or Decline Bids
        data = request.json
        bid_id = data.get('bidID')
        confirmation_status = data.get('confirmationStatus')
        bid = Bids.query.get(bid_id)
        if bid:
            bid.bidStatus = confirmation_status
            db.session.commit()
            return jsonify({'message': 'Bid status updated successfully'})
        else:
            return jsonify({'error': 'Bid not found'}), 404


@app.route('/api/vehicle-purchase/new-vehicle-no-finance/bid-accepted', methods=['POST'])
# this endpoint is used for the customer to Purchase their cars AFTER their bid had been accepted
# here we only deal with the Purchases and Payments Table
def vehicle_purchase_bid_accepted():
    try:
        # make sure the member is logged in and has an account to purchase a vehicle and it logged in
        member_session_id = session.get('member_session_id')
        if member_session_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        # get information sent from the frontend to here
        # Frontend needs to send: bid_id, payment_option, member_id, payment_amount
        data = request.json
        bid_id = data.get('bid_id')
        payment_option = data.get('payment_option')  # 'Card' or 'Check'
        member_id = data.get('member_id')
        payment_amount = data.get('payment_amount')

        # returns the row in BID table that matches with our bid_id
        bid = Bids.query.get(bid_id)
        if not bid or bid.bidStatus != 'Confirmed':
            return jsonify({'message': 'Bid not found or is Not Confirmed, Cannot continue with Purchase'}), 404

        # returns vehicle information for purchase for the vehicle to be bought
        vehicle = CarInfo.query.filter_by(VIN_carID=bid.VIN_carID).first()
        if not vehicle:
            return jsonify({'message': 'Vehicle not found for this bid'}), 404

        # Validate and retrieve card or check information based on payment_option
        if payment_option == 'Card':
            card_number = data.get('card_number')
            cvv = data.get('CVV')
            expiration_date = data.get('expirationDate')
            routing_number = None
            account_number = None
            regex_card_check(card_number, cvv, expiration_date)
            if payment_amount > 5000:  # cards cannot pay more than 5000
                return jsonify({'message': 'Choose A lower value for Bank Cards'}), 400
        elif payment_option == 'Check':
            routing_number = data.get('routing_number')
            account_number = data.get('account_number')
            card_number = None
            cvv = None
            expiration_date = None
            regex_bank_acct_check(routing_number, account_number)
        else:
            return jsonify({'message': 'Invalid payment option.'}), 400

        # Retrieve vehicle cost
        # vehicle_cost = return_vehicle_cost(vehicle_vin) # no need because the cost is based on the confirmed bid
        total_valuePaid = bid.bidValue - payment_amount
        # signature = get_signature()

        # create a payment entry to insert into the DB for the new payment/purchase information
        new_payment = Payments(
            paymentStatus='Confirmed',
            valuePaid=payment_amount,
            valueToPay=total_valuePaid,
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
            paymentType=payment_option,
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
            VIN_carID=vehicle.VIN_carID,
            memberID=member_id,
            confirmationNumber=confirmation_number_generation(),  # You may generate a confirmation number here
            # signature=signature_val
        )
        db.session.add(new_purchase)
        db.session.commit()
        return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200
    except Exception as e:
        return jsonify({'error': 'Bid not found for the specified member and vehicle, could not purchase vehicle'}), 404


@app.route('/api/manager/customer-payment-report', methods=['GET'])
def payment_report():
    # GET protocol returns all payment information based on the passed memberID to be used as payment reports from
    # any specific customer
    try:
        # checks if a manager is logged in to view the information
        employee_id = session.get('employee_session_id')
        if not employee_id:
            return jsonify({'message': 'Unauthorized access'}), 401

        # ensures that the employee is a Technician
        employee = Employee.query.filter_by(employeeID=employee_id, employeeType='Manager').first()
        if not employee:
            return jsonify({'message': 'Unauthorized access'}), 401

        data = request.json
        member_id = data.get('memberID')
        # payments = Payments.query.all() # for debugging
        payments = Payments.query.filter_by(memberID=member_id).all()
        payments_info = []
        for payment in payments:
            payment_data = {
                'paymentID': payment.paymentID,
                'paymentStatus': payment.paymentStatus,
                'valuePaid': payment.valuePaid,
                'valueToPay': payment.valueToPay,
                'initialPurchase': payment.initialPurchase,  # Convert to string
                'lastPayment': payment.lastPayment,  # Convert to string
                'paymentType': payment.paymentType,
                'cardNumber': payment.cardNumber,
                'expirationDate': payment.expirationDate,
                'CVV': payment.CVV,
                'routingNumber': payment.routingNumber,
                'bankAcctNumber': payment.bankAcctNumber,
                'memberID': payment.memberID,
                'financingID': payment.memberID
            }
            payments_info.append(payment_data)
        return jsonify({'payments': payments_info}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/manager/monthly-sales-report', methods=['GET'])
# this API generates monthly sales reports on all payments made in the dealership
# Scufffedd but i think it works
def monthly_sales_report():
    # checks if a manager is logged in to view the information | uncomment when we have it working for sure 100% on frontend in implementation
    # employee_id = session.get('employee_session_id')
    # if not employee_id:
    #     return jsonify({'message': 'Unauthorized access'}), 401
    #
    # ensures that the employee is a Technician
    # employee = Employee.query.filter_by(employeeID=employee_id, employeeType='Manager').first()
    # if not employee:
    #     return jsonify({'message': 'Unauthorized access'}), 401

    # request the parameters for monthly reports and in which year as well
    # have these values return in some like tab like or drop down value from the manager dashboard view
    month = request.args.get('month')  # have it be from 1-12
    year = request.args.get('year')  # have it be in YYYY format

    # use for value testing and debugging
    # month = 2
    # year = 23

    # the only table that stores purchases is the 'Purchases' table.
    # the finance, bids and purchases table only hold value but aren't needed for the total calculation
    # of revenue bought into the dealership as they are not the tables used for when payment transactions made
    # only for storing additional info on these transactions made
    purchases = Purchases.query.filter(db.extract('month', Purchases.purchaseDate) == month,
                                       db.extract('year', Purchases.purchaseDate) == year).all()

    # Prepare sales report data
    total_sales = 0
    sales_report = []

    # Calculate total sales from purchases
    for purchase in purchases:
        total_sales += purchase.bid.bidValue
        sales_report.append({
            'purchase_id': purchase.purchaseID,
            'member_id': purchase.memberID,
            'vehicle_id': purchase.VIN_carID,
            'confirmation_number': purchase.confirmationNumber,
            'purchase_type': purchase.purchaseType,
            'purchase_timestamp': purchase.purchaseDate.isoformat(),
            'bid_value': str(purchase.bid.bidValue)  # Convert Decimal to string for JSON serialization
        })

    return jsonify({
        'total_sales': str(total_sales),  # Convert total sales to string for JSON serialization
        'sales_report': sales_report
    }), 200


@app.route('/api/customer/make-payment', methods=['POST'])
def manage_payments():
    # POST protocol is to be used by user for inserting new payments for their purchases. All the information for these
    try:
        # ensure that members are logged in and exist
        member_id = session.get('member_session_id')
        if not member_id:
            return jsonify({'message': 'Unauthorized access'}), 401

        # Ensure that the employee is a Manager
        member = Member.query.filter_by(memberID=member_id).first()
        if member is None:
            return jsonify({'message': 'Unauthorized access'}), 401

        data = request.json  # Assuming JSON data is sent in the request

        # Check if it's a vehicle purchase or a service payment
        purchase_type = data.get('paymentType')
        if purchase_type == 'Vehicle/Add-on Continuing Payment':
            # Vehicle purchase payment
            purchase_id = data.get('purchaseID')

            # this search is done for continuing purchases on vehicles already bought
            # we match the incomming sent from the frontend purchase ID with the memberID to make sure they match
            purchase = Purchases.query.filter_by(purchaseID=purchase_id, memberID=member_id).first()

            if purchase is None:
                return jsonify({'message': 'Invalid purchase ID for additional payments to be made on the car'}), 400

            value_paid = data.get('valuePaid')

            # update the value to continue paying
            purchase.valueToPay -= value_paid
            purchase.save()

            # Create a new payment record
            new_payment = Payments(
                paymentStatus='Completed',
                valuePaid=value_paid,
                valueToPay=purchase.valueToPay,
                initialPurchase=purchase.initialPurchase,
                lastPayment=datetime.now(),
                paymentType='Check/Bank Account',
                cardNumber=None,
                expirationDate=None,
                CVV=None,
                routingNumber=purchase.routingNumber,
                bankAcctNumber=member.bankAcctNumber,
                memberID=member_id,
                financingID=purchase.financingID
            )
            db.session.add(new_payment)
        elif purchase_type == 'Service Payment':
            value_paid = data.get('valuePaid')
            routing_number = data.get('routingNumber')
            bank_acc_number = data.get('bankAcctNumber')
            VIN_carID = data.get('VIN_carID')

            # checks if there is a service appointment for the given VIN_carID and memberID
            # ensures also that the car belongs to the member without further checking
            service_appointment = ServiceAppointment.query.filter_by(
                VIN_carID=VIN_carID,
                memberID=member_id,
                status='Done'
            ).first()

            if not service_appointment:
                return jsonify({
                    'message': 'No completed service appointment found for the provided VIN for payment to be made'}), 400

            # create a new payment record
            new_payment = Payments(
                paymentStatus='Completed',
                valuePaid=value_paid,
                valueToPay=0,
                initialPurchase=datetime.now(),
                lastPayment=datetime.now(),
                paymentType='Check/Bank Account',
                routingNumber=routing_number,
                bankAcctNumber=bank_acc_number,
                memberID=member_id,
                financingID=11  # for all payments that do not involve financing
            )
            db.session.add(new_payment)

            new_purchase = Purchases(
                bidID=4,  # for all payments that do not involve bidding
                VIN_carID=VIN_carID,
                memberID=member_id,
                confirmationNumber=confirmation_number_generation(),
                purchaseType='Vehicle/Add-on Continuing Payment'
            )
            db.session.add(new_purchase)
        else:
            return jsonify({'message': 'Invalid purchase type'}), 400

        db.session.commit()
        return jsonify({'message': 'Payment information updated successfully'}), 200
    except Exception as e:
        # Rollback the session in case of any exception
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/vehicle-purchase/new-vehicle-no-finance', methods=['POST'])
# POST request is used by the customer to purchase a new Vehicle at BID or MSRP with NO FINANCING
def purchase_vehicle():
    # ensure that the member is logged in and has an account
    member_session_id = session.get('member_session_id')
    if member_session_id is None:
        # redirect the user at this point to a login screen if they are not logged in to an account to purchase a vehicle
        return jsonify({'message': 'You need to log in to purchase a vehicle.'}), 401

    # information from the frontend they have to pass to the backend is all below
    data = request.json
    vehicle_vin = data.get('vehicle_vin')
    if vehicle_vin == -1:
        return jsonify({'message': "CAR DOESNT EXIST"}), 400

    payment_method = data.get('payment_method')
    payment_amount = data.get('payment_amount')
    member_id = data.get('member_id')
    payment_option = data.get('payment_option')  # Payment option: 'Card' or 'Check'
    vehicle_cost = return_vehicle_cost(vehicle_vin)

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
        # BIDDING and not purchasing right then and there.
        bid_value = data.get('bidValue')
        bid_status = 'Processing'  # not sent from the frontend. The change to Confirmed/Denied
        return bid_insert_no_financing(member_id, bid_value, bid_status)


def regex_card_check(card_number: str, cvv: str, expiration_date: str) -> bool:
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


def regex_bank_acct_check(routing_number: str, account_number: str) -> bool:
    # regec validation for the routing number and account number to be correct
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
    # here we only deal with Purchases and Payments table
    # we insert these values into the table
    # we do grab a signature and store but that will be later in development

    try:
        # Insert purchase information into the database

        # dont worry about signature this round ######
        # signature_val = get_signature()  # don't worry about this rn i have to fix the DB and tables for this
        # if signature_val != 'YES' or signature_val != 'NO':
        #     return signature_val  # returns an error back to the frontend

        valuePaid_value = payment_amount
        valueToPay_value = vehicle_cost - payment_amount

        # no need to add into financing

        new_payment = Payments(
            paymentStatus='Confirmed',
            valuePaid=valuePaid_value,
            valueToPay=valueToPay_value,
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
            paymentType=payment_option,  # payment_option = check, card
            servicePurchased='Vehicle Purchase',
            cardNumber=card_number,
            expirationDate=expiration_date,
            CVV=cvv,
            routingNumber=routing_number,
            bankAcctNumber=account_number,
            memberID=member_id,
            financingID=None
        )

        db.session.add(new_payment)
        db.session.commit()

        new_purchase = Purchases(
            VIN_carID=vehicle_vin,
            memberID=member_id,
            confirmationNumber=confirmation_number_generation(),  # You may generate a confirmation number here
            # signature=signature_val
        )

        db.session.add(new_purchase)
        db.session.commit()
        return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/vehicle-purchase/new-bid-insert', methods=['POST'])
def bid_insert_no_financing(member_id, bid_value, bid_status):
    # Here we only deal with the Bids Table
    # Here we only deal with inserting NEW bids into the backend with no financing
    try:
        # Create a new bid entry
        new_bid = Bids(
            memberID=member_id,
            bidValue=bid_value,
            bidStatus=bid_status,
            bidTimestamp=datetime.now()
        )

        db.session.add(new_bid)
        db.session.commit()
        return jsonify({'message': 'Bid successfully inserted.'}), 201
    except Exception as e:
        # Rollback the transaction in case of an error
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


def return_vehicle_cost(vehicle_vin):
    # we return the cost of the vehicle here based on the vehicle_vin passed into the function
    vehicle = CarInfo.query.filter_by(VIN_carID=vehicle_vin).first()
    if not vehicle:
        return -1
    return vehicle.price


def charCompany(cardNumber: str) -> str:
    # this function returns the credit card company of the card input by the customer
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


def confirmation_number_generation() -> str:
    # this function generates the confirmation number randomely
    total_chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(total_chars) for i in range(13))


def creditScoreGenerator() -> int:
    # generates a random creditScore
    return random.randint(500, 850)


def interest_rate(creditScore: int) -> int:
    # calculates the base interest rate
    if creditScore >= 750:
        return 5
    elif creditScore >= 700:
        return 10
    elif creditScore >= 650:
        return 15
    else:
        return 20


def financingValue(vehicleCost: int, monthlyIncome: int, creditscore: int) -> float:
    # may be scuffed because I need to know more on more accurate rates but this might be ok
    # generates the finance loan value

    base_loan_interest_rate = interest_rate(creditscore)
    # Calculate financing value based on vehicle cost and monthly income
    final_financing_percentage = base_loan_interest_rate + ((vehicleCost / monthlyIncome) * 100)
    financing_loan_value = (final_financing_percentage / 100) * vehicleCost
    return financing_loan_value


def check_loan_eligibility(loan_amount: float, monthly_income: int) -> bool:
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
    # used as a means of re evaluating the loan and whether the user wants to or not and it will lead to a new downpayment
    data = request.json
    reevaluate_loan = data.get('reevaluate_loan')  # no == 0, yes == 1
    return str(reevaluate_loan)


''' API to use to purchase a vehicle at MSRP with financing from the dealership'''


@app.route('/api/vehicle-purchase/new-vehicle-purchase-finance', methods=['POST'])
def new_vehicle_purchase_finance():
    # here we deal with Financing, Purchases and Payments table
    # HERE we deal with purchases of vehicles WITH FINANCING
    try:
        # customer auth for making sure they are logged in and have an account
        member_session_id = session.get('member_session_id')
        if member_session_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        # frontend needs to send these values to the backend
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
        if vehicle_cost == -1:
            return jsonify({'message': 'Vehicle Not Listed'}), 400

        total_cost = adjust_loan_with_downpayment(vehicle_cost, down_payment)
        financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)

        # Loan eligibility
        loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
        if not loan_eligibility:
            # we want to check if the user wants to re-evaluate their loan through a new down payment amount
            reevaluate_loan = int(reevaluate_finance())
            if reevaluate_loan == 0:  # they cannot purchase the vehicle
                return jsonify({'message': 'Your yearly income is not sufficient to take on this loan.'}), 400
            elif reevaluate_loan == 1:  # they can and the frontend needs to send a new downpayment, this may need a new endpoint so LMK frontend
                new_down_payment = data.get('new_down_payment')
                total_cost = adjust_loan_with_downpayment(vehicle_cost, new_down_payment)
                financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
                loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
                # if true, we can continue to storing everything and all the values !!.
                if not loan_eligibility:
                    return jsonify({
                        'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400  # they cannot purchase this vehicle
            else:
                return jsonify({'message': 'Invalid Value'}), 400

        # signature retrival value | ENUM just to ensure we go something and not left blank. | dont worry about this now, we are not that far into development
        # signature = get_signature()
        # if signature != 1:
        #     return jsonify({'message': 'Please Insert Signature Value'})

        # ik its long here but im tight on time imma just make it here and MAY refactor later

        downPayment_value = total_cost - financing_loan_amount
        valueToPay_value = total_cost - downPayment_value
        paymentPerMonth_value = financing_loan_amount / 12

        # insertion of new Financing, Payments and Purchases Tables
        new_financing = Financing(
            memberID=member_id,
            income=int(monthly_income) * 12,
            credit_score=credit_score,
            loan_total=financing_loan_amount,
            down_payment=downPayment_value,
            percentage=interest_rate(credit_score),
            monthly_sum=paymentPerMonth_value,
            remaining_months=48
        )
        db.session.add(new_financing)
        db.session.commit()

        # DB insert for new purchase with financing
        new_payment = Payments(
            paymentStatus='Confirmed',
            valuePaid=downPayment_value,
            valueToPay=valueToPay_value,
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
            paymentType=payment_method,
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
            # no Bid ID since this is not a BID Operation
            VIN_carID=vehicle_vin,
            memberID=member_id,
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


# not in use yet
# @app.route('/api/vehicle-purchase/signature', methods=['POST'])
# def get_signature():
#     data = request.json
#     signature = int(data.get('signature'))  # yes = 1, no = 0
#     if signature == 0:
#         return 'NO'
#     elif signature == 1:
#         return 'YES'
#     else:
#         return jsonify({'message': 'Invalid VALUE'}), 400


@app.route('/api/vehicle-purchase/bid-confirmed-financed-purchase', methods=['POST'])
def new_bid_purchase_finance():
    # here we deal with the bid, purchases, payments and finance tables
    # HERE we deal with Bid that are confimed and being purchased with FINANCING
    try:
        # customer auth for making sure they are logged in and have an account
        member_session_id = session.get('member_session_id')
        if member_session_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        # frontend needs to send these values to the backend
        data = request.json
        bid_id = data.get('bid_id')
        member_id = data.get('member_id')
        payment_method = data.get('payment_method')
        down_payment = data.get('down_payment')
        monthly_income = data.get('monthly_income')

        # returns data on the bid we need that the customer is purchasing
        bid = Bids.query.get(bid_id)
        if not bid or bid.bidStatus != 'Confirmed':
            return jsonify({'message': 'Bid not found or is Not Confirmed, Cannot continue with Purchase'}), 404

        # return purchasing information on the vehicle to be purchased, we need the information not COST since we are buying based on an approved BID
        vehicle = CarInfo.query.filter_by(VIN_carID=bid.VIN_carID).first()
        if not vehicle:
            return jsonify({'message': 'Vehicle not found for this bid'}), 404

        # more processing
        if payment_method == 'CARD':
            card_number = data.get('card_number')
            cvv = data.get('cvv')
            expiration_date = data.get('expirationDate')
            routingNumber = None
            bankAcctNumber = None
            if down_payment > 5000:
                return jsonify({
                    'message': 'Card payments are limited to $5000. The rest must be paid in person at the dealership.'}), 400
        else:
            routingNumber = data.get('routingNumber')
            bankAcctNumber = data.get('bankAcctNumber')
            card_number = None
            cvv = None
            expiration_date = None

        credit_score = creditScoreGenerator()  # Assuming this function exists and works correctly
        vehicle_cost = vehicle.price
        total_cost = adjust_loan_with_downpayment(vehicle_cost, down_payment)

        # Loan Eligibility | the same as the other loan operations in buying the vehicle at MSRP with financing
        financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
        loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
        if not loan_eligibility:
            reevaluate_loan = int(reevaluate_finance())
            if reevaluate_loan == 0:
                return jsonify({'message': 'Your yearly income is not sufficient to take on this loan.'}), 400
            elif reevaluate_loan == 1:
                new_down_payment = data.get('new_down_payment')
                total_cost = adjust_loan_with_downpayment(vehicle_cost, new_down_payment)
                financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
                loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
                if not loan_eligibility:
                    return jsonify({'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400
            else:
                return jsonify({'message': 'Invalid Value'}), 400

        # signature = get_signature()  # Assuming this function exists and works correctly
        # if signature != 1:
        #     return jsonify({'message': 'Please Insert Signature Value'}), 400

        downPayment_value = total_cost - financing_loan_amount
        valueToPay_value = total_cost - downPayment_value
        paymentPerMonth_value = financing_loan_amount / 12

        # inserts new values on the purchase based on Financing, Payments, Purchases
        new_financing = Financing(
            memberID=member_id,
            income=monthly_income,
            credit_score=credit_score,
            loan_total=financing_loan_amount,
            down_payment=downPayment_value,
            percentage=interest_rate(credit_score),
            monthly_sum=paymentPerMonth_value,
            remaining_months=48
        )
        db.session.add(new_financing)
        db.session.commit()

        new_payment = Payments(
            paymentStatus='Confirmed',
            valuePaid=downPayment_value,
            valueToPay=valueToPay_value,
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
            paymentType=payment_method,
            cardNumber=card_number,
            expirationDate=expiration_date,
            CVV=cvv,
            routingNumber=routingNumber,
            bankAcctNumber=bankAcctNumber,
            memberID=member_id,
            financingID=new_financing.financingID
        )
        db.session.add(new_payment)
        db.session.commit()

        new_purchase = Purchases(
            bidID=bid.bidID,
            VIN_carID=vehicle.VIN_carID,
            memberID=member_id,
            confirmationNumber=confirmation_number_generation(),  # You may generate a confirmation number here
            # signature=signature_val
        )
        db.session.add(new_purchase)
        db.session.commit()

        # no need to modify Bid Status since its already been confirmed.
        return jsonify({'message': 'Vehicle purchase with financing processed successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500
