'''Anything I thought Wasnt used was moved down here'''

# @app.route('/api/vehicle-purchase/new-vehicle-purchase-finance/re-evaluate', methods=['POST'])
# def reevaluate_finance():
#     # used as a means of re evaluating the loan and whether the user wants to or not and it will lead to a new downpayment
#     data = request.json
#     reevaluate_loan = data.get('reevaluate_loan')  # no == 0, yes == 1
#     return str(reevaluate_loan)


# ''' API to use to purchase a vehicle at MSRP with financing from the dealership'''


# @app.route('/api/vehicle-purchase/new-vehicle-purchase-finance', methods=['POST'])
# def new_vehicle_purchase_finance():
#     # here we deal with Financing, Purchases and Payments table
#     # HERE we deal with purchases of vehicles WITH FINANCING
#     try:
#         # customer auth for making sure they are logged in and have an account
#         member_session_id = session.get('member_session_id')
#         if member_session_id is None:
#             return jsonify({'message': 'Invalid session'}), 400

#         # frontend needs to send these values to the backend
#         data = request.json
#         vehicle_vin = data.get('vehicle_vin')
#         payment_method = data.get('payment_method')
#         member_id = data.get('member_id')
#         down_payment = data.get('down_payment')
#         monthly_income = data.get('monthly_income')

#         if payment_method == 'CARD':
#             card_number = data.get('card_number')
#             cvv = data.get('cvv')
#             expiration_date = data.get('expirationDate')
#             routingNumber = None
#             bankAcctNumber = None
#             if down_payment > 5000:
#                 return jsonify({'message': 'Card payments are limited to $5000. The rest must be paid in person at '
#                                            'the dealership.'}), 400
#         else:
#             routingNumber = data.get('routingNumber')
#             bankAcctNumber = data.get('bankAcctNumber')
#             card_number = None
#             cvv = None
#             expiration_date = None

#         credit_score = creditScoreGenerator()
#         vehicle_cost = return_vehicle_cost(vehicle_vin)
#         if vehicle_cost == -1:
#             return jsonify({'message': 'Vehicle Not Listed'}), 400

#         total_cost = adjust_loan_with_downpayment(vehicle_cost, down_payment)
#         financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)

#         # Loan eligibility
#         loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
#         if not loan_eligibility:
#             # we want to check if the user wants to re-evaluate their loan through a new down payment amount
#             reevaluate_loan = int(reevaluate_finance())
#             if reevaluate_loan == 0:  # they cannot purchase the vehicle
#                 return jsonify({'message': 'Your yearly income is not sufficient to take on this loan.'}), 400
#             elif reevaluate_loan == 1:  # they can and the frontend needs to send a new downpayment, this may need a new endpoint so LMK frontend
#                 new_down_payment = data.get('new_down_payment')
#                 total_cost = adjust_loan_with_downpayment(vehicle_cost, new_down_payment)
#                 financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
#                 loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
#                 # if true, we can continue to storing everything and all the values !!.
#                 if not loan_eligibility:
#                     return jsonify({
#                         'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400  # they cannot purchase this vehicle
#             else:
#                 return jsonify({'message': 'Invalid Value'}), 400

#         # signature retrival value | ENUM just to ensure we go something and not left blank. | dont worry about this now, we are not that far into development
#         # signature = get_signature()
#         # if signature != 1:
#         #     return jsonify({'message': 'Please Insert Signature Value'})

#         # ik its long here but im tight on time imma just make it here and MAY refactor later

#         downPayment_value = total_cost - financing_loan_amount
#         valueToPay_value = total_cost - downPayment_value
#         paymentPerMonth_value = financing_loan_amount / 12

#         # insertion of new Financing, Payments and Purchases Tables
#         new_financing = Financing(
#             memberID=member_id,
#             income=int(monthly_income) * 12,
#             credit_score=credit_score,
#             loan_total=financing_loan_amount,
#             down_payment=downPayment_value,
#             percentage=interest_rate(credit_score),
#             monthly_sum=paymentPerMonth_value,
#             remaining_months=48
#         )
#         db.session.add(new_financing)
#         db.session.commit()

#         # DB insert for new purchase with financing
#         new_payment = Payments(
#             paymentStatus='Confirmed',
#             valuePaid=downPayment_value,
#             valueToPay=valueToPay_value,
#             initialPurchase=datetime.now(),
#             lastPayment=datetime.now(),
#             paymentType=payment_method,
#             servicePurchased='Vehicle Purchase',
#             cardNumber=card_number,
#             expirationDate=expiration_date,
#             CVV=cvv,
#             routingNumber=routingNumber,
#             bankAcctNumber=bankAcctNumber,
#             memberID=member_id
#         )
#         db.session.add(new_payment)
#         db.session.commit()

#         new_purchase = Purchases(
#             # no Bid ID since this is not a BID Operation
#             VIN_carID=vehicle_vin,
#             memberID=member_id,
#             confirmationNumber=confirmation_number_generation()  # You may generate a confirmation number here
#             # signature='YES'
#         )
#         db.session.add(new_purchase)
#         db.session.commit()

#         # payment stub generation can occur through the means of functions above with endpoints
#         # /api/member
#         # /api/payments

#         return jsonify({'message': 'Vehicle purchase with financing processed successfully.'}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'message': f'Error: {str(e)}'}), 500




# @app.route('/api/vehicle-purchase/bid-confirmed-financed-purchase', methods=['POST'])
# def new_bid_purchase_finance():
#     # here we deal with the bid, purchases, payments and finance tables
#     # HERE we deal with Bid that are confimed and being purchased with FINANCING
#     try:
#         # customer auth for making sure they are logged in and have an account
#         member_session_id = session.get('member_session_id')
#         if member_session_id is None:
#             return jsonify({'message': 'Invalid session'}), 400

#         # frontend needs to send these values to the backend
#         data = request.json
#         bid_id = data.get('bid_id')
#         member_id = data.get('member_id')
#         payment_method = data.get('payment_method')
#         down_payment = data.get('down_payment')
#         monthly_income = data.get('monthly_income')

#         # returns data on the bid we need that the customer is purchasing
#         bid = Bids.query.get(bid_id)
#         if not bid or bid.bidStatus != 'Confirmed':
#             return jsonify({'message': 'Bid not found or is Not Confirmed, Cannot continue with Purchase'}), 404

#         # return purchasing information on the vehicle to be purchased, we need the information not COST since we are buying based on an approved BID
#         vehicle = CarInfo.query.filter_by(VIN_carID=bid.VIN_carID).first()
#         if not vehicle:
#             return jsonify({'message': 'Vehicle not found for this bid'}), 404

#         # more processing
#         if payment_method == 'CARD':
#             card_number = data.get('card_number')
#             cvv = data.get('cvv')
#             expiration_date = data.get('expirationDate')
#             routingNumber = None
#             bankAcctNumber = None
#             if down_payment > 5000:
#                 return jsonify({
#                     'message': 'Card payments are limited to $5000. The rest must be paid in person at the dealership.'}), 400
#         else:
#             routingNumber = data.get('routingNumber')
#             bankAcctNumber = data.get('bankAcctNumber')
#             card_number = None
#             cvv = None
#             expiration_date = None

#         credit_score = creditScoreGenerator()  # Assuming this function exists and works correctly
#         vehicle_cost = vehicle.price
#         total_cost = adjust_loan_with_downpayment(vehicle_cost, down_payment)

#         # Loan Eligibility | the same as the other loan operations in buying the vehicle at MSRP with financing
#         financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
#         loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
#         if not loan_eligibility:
#             reevaluate_loan = int(reevaluate_finance())
#             if reevaluate_loan == 0:
#                 return jsonify({'message': 'Your yearly income is not sufficient to take on this loan.'}), 400
#             elif reevaluate_loan == 1:
#                 new_down_payment = data.get('new_down_payment')
#                 total_cost = adjust_loan_with_downpayment(vehicle_cost, new_down_payment)
#                 financing_loan_amount = financingValue(total_cost, monthly_income, credit_score)
#                 loan_eligibility = check_loan_eligibility(financing_loan_amount, monthly_income)
#                 if not loan_eligibility:
#                     return jsonify({'message': 'Your yearly income is still not sufficient to take on this loan.'}), 400
#             else:
#                 return jsonify({'message': 'Invalid Value'}), 400

#         # signature = get_signature()  # Assuming this function exists and works correctly
#         # if signature != 1:
#         #     return jsonify({'message': 'Please Insert Signature Value'}), 400

#         downPayment_value = total_cost - financing_loan_amount
#         valueToPay_value = total_cost - downPayment_value
#         paymentPerMonth_value = financing_loan_amount / 12

#         # inserts new values on the purchase based on Financing, Payments, Purchases
#         new_financing = Financing(
#             memberID=member_id,
#             income=monthly_income,
#             credit_score=credit_score,
#             loan_total=financing_loan_amount,
#             down_payment=downPayment_value,
#             percentage=interest_rate(credit_score),
#             monthly_sum=paymentPerMonth_value,
#             remaining_months=48
#         )
#         db.session.add(new_financing)
#         db.session.commit()

#         new_payment = Payments(
#             paymentStatus='Confirmed',
#             valuePaid=downPayment_value,
#             valueToPay=valueToPay_value,
#             initialPurchase=datetime.now(),
#             lastPayment=datetime.now(),
#             paymentType=payment_method,
#             cardNumber=card_number,
#             expirationDate=expiration_date,
#             CVV=cvv,
#             routingNumber=routingNumber,
#             bankAcctNumber=bankAcctNumber,
#             memberID=member_id,
#             financingID=new_financing.financingID
#         )
#         db.session.add(new_payment)
#         db.session.commit()

#         new_purchase = Purchases(
#             bidID=bid.bidID,
#             VIN_carID=vehicle.VIN_carID,
#             memberID=member_id,
#             confirmationNumber=confirmation_number_generation(),  # You may generate a confirmation number here
#             # signature=signature_val
#         )
#         db.session.add(new_purchase)
#         db.session.commit()

#         # no need to modify Bid Status since its already been confirmed.
#         return jsonify({'message': 'Vehicle purchase with financing processed successfully.'}), 200
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'message': f'Error: {str(e)}'}), 500



# @app.route('/api/vehicle-purchase/new-vehicle-no-finance', methods=['POST'])
# # POST request is used by the customer to purchase a new Vehicle at BID or MSRP with NO FINANCING
# def purchase_vehicle():
#     member_id = session.get('member_session_id')
#     if member_id is None:
#         return jsonify({'message': 'You need to log in to purchase a vehicle.'}), 403

#     data = request.json
#     vehicle_vin = data.get('vehicle_vin')
#     if vehicle_vin is None:
#         return jsonify({'message': "Vehicle VIN is missing."}), 400

#     # card_number = None
#     # cvv = None
#     # expiration_date = None

#     payment_method = data.get('payment_method')
#     payment_amount = data.get('payment_amount')
#     payment_option = "Check"

#     try:
#         vehicle_cost = return_vehicle_cost(vehicle_vin)
#     except ValueError as ve:
#         return jsonify({'error': str(ve)}), 404  # Vehicle not found
    
#     if payment_method == 'MSRP':
#         routing_number = data.get('routing_number')
#         account_number = data.get('account_number')

#         if check_ssn() is False:
#             return jsonify({'message': 'SSN number is in Invalid Format.'}), 401

#         if regex_bank_acct_check(routing_number, account_number) is False:
#             return jsonify({'message': 'Routing Number and/or Account Number are in Invalid Formats.'}), 401

#         try:
#             return msrp_vehicle_purchase_no_financing(vehicle_vin, payment_amount, member_id, payment_option, vehicle_cost, routing_number, account_number)
#         except Exception as e:
#             return jsonify({'error': f'Error processing MSRP payment: {str(e)}'}), 500

#     else:
#         bid_value = data.get('bidValue')
#         bid_status = 'Processing'
#         try:
#             return bid_insert_no_financing(member_id, bid_value, bid_status)
#         except Exception as e:
#             return jsonify({'error': f'Error processing bid: {str(e)}'}), 500


# def msrp_vehicle_purchase_no_financing(vehicle_vin, payment_amount, member_id, payment_option, vehicle_cost, routing_number, account_number):
#     try:
#         # Validate signature
#         signature_val = get_signature()
#         if signature_val not in ['Yes', 'No']:
#             return jsonify({'error': 'Invalid signature value.'}), 400
#         elif signature_val == 'No':
#             return jsonify({'error': 'You must provide a signature to purchase a vehicle.'}), 401

#         # Calculate payment values
#         valuePaid_value = payment_amount
#         valueToPay_value = vehicle_cost - payment_amount

#         # Add payment record
#         new_payment = Payments(
#             paymentStatus='Confirmed',
#             valuePaid=valuePaid_value,
#             valueToPay=valueToPay_value,
#             initialPurchase=datetime.now(),
#             lastPayment=datetime.now(),
#             paymentType=payment_option,
#             servicePurchased='Vehicle Purchase',
#             # cardNumber=card_number,
#             # expirationDate=expiration_date,
#             # CVV=cvv,
#             routingNumber=routing_number,
#             bankAcctNumber=account_number,
#             memberID=member_id,
#             financingID=None
#         )
#         db.session.add(new_payment)

#         # Commit payment record
#         db.session.commit()

#         # Add purchase record
#         new_purchase = Purchases(
#             VIN_carID=vehicle_vin,
#             memberID=member_id,
#             confirmationNumber=confirmation_number_generation(),
#             # purchaseType='Vehicle/Add-on Purchase',
#             # purchaseDate=datetime.now(),
#             # signature=signature_val
#         )
#         db.session.add(new_purchase)

#         # Commit purchase record
#         db.session.commit()

#         return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200

#     except IntegrityError:
#         db.session.rollback()
#         return jsonify({'error': 'Integrity error occurred. Please check your input data.'}), 400

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'error': f'Error processing vehicle purchase: {str(e)}'}), 500

# @app.route('/api/vehicle-purchase/new-vehicle-no-finance/bid-accepted', methods=['POST'])
# # this endpoint is used for the customer to Purchase their cars AFTER their bid had been accepted
# # here we only deal with the Purchases and Payments Table
# def vehicle_purchase_bid_accepted():
#     try:
#         # make sure the member is logged in and has an account to purchase a vehicle and it logged in
#         member_session_id = session.get('member_session_id')
#         if member_session_id is None:
#             return jsonify({'message': 'Invalid session'}), 400

#         # get information sent from the frontend to here
#         # Frontend needs to send: bid_id, payment_option, member_id, payment_amount
#         data = request.json
#         bid_id = data.get('bid_id')
#         payment_option = data.get('payment_option')  # 'Card' or 'Check'
#         member_id = data.get('member_id')
#         payment_amount = data.get('payment_amount')

#         # returns the row in BID table that matches with our bid_id
#         bid = Bids.query.get(bid_id)
#         if not bid or bid.bidStatus != 'Confirmed':
#             return jsonify({'message': 'Bid not found or is Not Confirmed, Cannot continue with Purchase'}), 404

#         # returns vehicle information for purchase for the vehicle to be bought
#         vehicle = CarInfo.query.filter_by(VIN_carID=bid.VIN_carID).first()
#         if not vehicle:
#             return jsonify({'message': 'Vehicle not found for this bid'}), 404

#         # Validate and retrieve card or check information based on payment_option
#         if payment_option == 'Card':
#             card_number = data.get('card_number')
#             cvv = data.get('CVV')
#             expiration_date = data.get('expirationDate')
#             routing_number = None
#             account_number = None
#             regex_card_check(card_number, cvv, expiration_date)
#             if payment_amount > 5000:  # cards cannot pay more than 5000
#                 return jsonify({'message': 'Choose A lower value for Bank Cards'}), 400
#         elif payment_option == 'Check':
#             routing_number = data.get('routing_number')
#             account_number = data.get('account_number')
#             card_number = None
#             cvv = None
#             expiration_date = None
#             regex_bank_acct_check(routing_number, account_number)
#         else:
#             return jsonify({'message': 'Invalid payment option.'}), 400

#         # Retrieve vehicle cost
#         # vehicle_cost = return_vehicle_cost(vehicle_vin) # no need because the cost is based on the confirmed bid
#         total_valuePaid = bid.bidValue - payment_amount
#         # signature = get_signature()

#         # create a payment entry to insert into the DB for the new payment/purchase information
#         new_payment = Payments(
#             paymentStatus='Confirmed',
#             valuePaid=payment_amount,
#             valueToPay=total_valuePaid,
#             initialPurchase=datetime.now(),
#             lastPayment=datetime.now(),
#             paymentType=payment_option,
#             cardNumber=card_number,
#             expirationDate=expiration_date,
#             CVV=cvv,
#             routingNumber=routing_number,
#             bankAcctNumber=account_number,
#             memberID=member_id
#         )
#         db.session.add(new_payment)
#         db.session.commit()

#         new_purchase = Purchases(
#             VIN_carID=vehicle.VIN_carID,
#             memberID=member_id,
#             confirmationNumber=confirmation_number_generation(),  # You may generate a confirmation number here
#             # signature=signature_val
#         )
#         db.session.add(new_purchase)
#         db.session.commit()
#         return jsonify({'message': 'Vehicle purchase processed successfully.'}), 200
#     except Exception as e:
#         return jsonify({'error': 'Bid not found for the specified member and vehicle, could not purchase vehicle'}), 404

# @app.route('/api/member/check-ssn', methods=['POST'])
# # frontend: this api is made so before they put in their financial information, we ask the user for their SSN
# # but we need to check first if they have it in their info. use this before sending ssn value and redirecting to a page to do that
# # in order to not make more work for yourselves
# # this function is to be used before any '/api/vehicle-purchase/...' api's
# def check_ssn():
#     member_session_id = session.get('member_session_id')
#     if member_session_id is None:
#         return jsonify({'message': 'Need a member ID to check if they have an SSN in the DB.'}), 401
#     member_sensitive_info = MemberSensitiveInfo.query.filter_by(memberID=member_session_id).first()
#     if member_sensitive_info.SSN is None:
#         return False  # no SSN
#     else:
#         return True  # yes SSN stored

# @app.route('/api/member/update-ssn', methods=['POST'])
# def update_ssn(member_session_id):
#     data = request.json
#     ssn = data.get('ssn')
#     if regex_ssn(ssn):
#         return False
#     member_sensitive_info = MemberSensitiveInfo.query.filter_by(memberID=member_session_id).first()
#     member_sensitive_info.SSN = ssn
#     db.session.commit()
#     return True



'''i DONT THINK THIS ROUTE IS EVER CALLED'''
# # Get to it after vehicle purchases are actually going thru succesfully
# @app.route('/api/member/vehicle-purchases', methods=['GET'])
# # this endpoint is used to return all vehicle purchase information for an authorized customer to view their past vehicle purchases
# def member_vehicle_purchases():
    
#     member_session_id = session.get('member_session_id')  # sessions with Auth for a member who has bought a customer

#     if member_session_id is None:
#         return jsonify({'message': 'No session id provided'}), 404

#     vehicle_purchases_member = Purchases.query.filter_by(
#         memberID=member_session_id).all()  # returns vehicles purchased by the customer/member
#     if not vehicle_purchases_member:
#         return jsonify({'message': 'No purchases found for this member'}), 404

#     # Extract necessary purchase details
#     purchases_info = []
#     for purchase in vehicle_purchases_member:
#         car_info = CarInfo.query.filter_by(VIN_carID=purchase.VIN_carID).first()
#         bid_info = Bids.query.filter_by(bidID=purchase.bidID).first()

#         # Access payment type directly from purchase object
#         # payment_type = purchase.payment.paymentType

#         purchases_info.append({
#             'purchaseID': purchase.purchaseID,
#             'car_make': car_info.make,
#             'car_model': car_info.model,
#             'car_year': car_info.year,
#             # 'payment_type': payment_type,
#             'bid_value': bid_info.bidValue,
#             'bid_status': bid_info.bidStatus,
#             'confirmation_number': purchase.confirmationNumber
#         })
#     return jsonify(purchases_info), 200


'''i DONT THINK THIS ROUTE IS EVER CALLED'''

# @app.route('/api/member/payment-purchases-finance-bid-data', methods=['GET'])
# # this endpoint is used to return all data of members regarding payment, purchases, finance and bids informations of
# # the member who is authorized into the dealership and logged in and has a history here in the dealership
# def member_purchases():
    # member_session_id = session.get('member_session_id')
    # if member_session_id is None:
    #     return jsonify({'message': 'No session id provided'}), 400

    # # return payments, financing, bids, and purchase history for the member
    # payments = Payments.query.filter_by(memberID=member_session_id).all()
    # financing = Financing.query.filter_by(memberID=member_session_id).all()
    # bids = Bids.query.filter_by(memberID=member_session_id).all()
    # purchases = Purchases.query.filter_by(memberID=member_session_id).all()

    # # for testing purposes
    # # payments = Payments.query.all()
    # # financing = Financing.query.all()
    # # bids = Bids.query.all()
    # # purchases = Purchases.query.all()

    # # Payment information
    # payment_info = []
    # for payment in payments:
    #     payment_data = {
    #         'paymentID': payment.paymentID,
    #         'paymentStatus': payment.paymentStatus,
    #         'valuePaid': payment.valuePaid,
    #         'valueToPay': payment.valueToPay,
    #         'initialPurchase': str(payment.initialPurchase),  # Convert to string
    #         'lastPayment': str(payment.lastPayment),  # Convert to string
    #         'paymentType': payment.paymentType,
    #         # 'cardNumber': payment.cardNumber,
    #         # 'expirationDate': payment.expirationDate,
    #         # 'CVV': payment.CVV,
    #         'routingNumber': payment.routingNumber,
    #         'bankAcctNumber': payment.bankAcctNumber,
    #         'memberID': payment.memberID,
    #         'financingID': payment.financingID
    #     }
    #     payment_info.append(payment_data)

    # # Financing information
    # financing_data = []
    # for finance in financing:
    #     financing_info = {
    #         'financingID': finance.financingID,
    #         'income': finance.income,
    #         'credit_score': finance.credit_score,
    #         'loan_total': finance.loan_total,
    #         'down_payment': finance.down_payment,
    #         'percentage': finance.percentage,
    #         'monthly_sum': finance.monthly_payment_sum,
    #         'remaining_months': finance.remaining_months
    #     }
    #     financing_data.append(financing_info)

    # # Bid information
    # bid_info = []
    # for bid in bids:
    #     bid_data = {
    #         'bidID': bid.bidID,
    #         'bidValue': bid.bidValue,
    #         'Vin_carID': bid.VIN_carID,
    #         'bidStatus': bid.bidStatus,
    #         'bidTimestamp': str(bid.bidTimestamp)  # Convert to string
    #     }
    #     bid_info.append(bid_data)

    # # Purchase history
    # purchase_history = []
    # for purchase in purchases:
    #     purchase_data = {
    #         'purchaseID': purchase.purchaseID,
    #         'bidID': purchase.bidID,
    #         'VIN_carID': purchase.VIN_carID,
    #         'memberID': purchase.memberID,
    #         'confirmationNumber': purchase.confirmationNumber,
    #         'purchaseType': purchase.purchaseType,
    #         'purchaseDate': str(purchase.purchaseDate)  # Convert to string
    #     }
    #     purchase_history.append(purchase_data)

    # # Construct the response
    # response_data = {
    #     'payments': payment_info,
    #     'financing': financing_data,
    #     'bids': bid_info,
    #     'purchase_history': purchase_history
    # }

    # return jsonify(response_data), 200

'''i DONT THINK THIS ROUTE IS EVER CALLED'''

# @app.route('/api/member-or-employee/finance-loan-payments', methods=['GET'])
# # this API provides a monthly payments view/report for requested loan
# # this can be used by both members and employee
# def member_finance_loan_payments():
#     member_id = session.get('member_session_id')
#     if not member_id:
#         employee_id = session.get('employee_session_id')
#         if not employee_id:
#             return jsonify({'message': 'Unauthorized login or access for member/manager'}), 401
#         employee = Employee.query.filter_by(employeeID=employee_id, employeeType='Manager').first()
#         if not employee:
#             return jsonify({'message': 'This login does not belong to a Manager'}), 401
#         data = request.json
#         member_id = data.get('memberID')
#     member = Member.query.filter_by(memberID=member_id).first()
#     if member is None:
#         return jsonify({'message': 'Unauthorized access'}), 401

#     # for debugging purposes
#     # member_id = 2

#     # join and filter the tables to fetch payments on the member's loan
#     payments = db.session.query(Payments) \
#         .join(Financing, Payments.financingID == Financing.financingID) \
#         .filter(Financing.memberID == member_id) \
#         .filter(Financing.financingID != 6) \
#         .all()

#     # format the data for json
#     payments_data = []
#     for payment in payments:
#         payments_data.append({
#             'paymentID': payment.paymentID,
#             'paymentStatus': payment.paymentStatus,
#             'valuePaid': payment.valuePaid,
#             'valueToPay': payment.valueToPay,
#             'initialPurchase': str(payment.initialPurchase),
#             'lastPayment': str(payment.lastPayment),
#             'paymentType': payment.paymentType,
#             'cardNumber': payment.cardNumber,
#             'expirationDate': payment.expirationDate,
#             'CVV': payment.CVV,
#             'routingNumber': payment.routingNumber,
#             'bankAcctNumber': payment.bankAcctNumber,
#             'memberID': payment.memberID,
#             'financingID': payment.financingID
#         })
#     return jsonify({'payments': payments_data}), 200


'''i DONT THINK THIS ROUTE IS EVER CALLED'''

# @app.route('/api/manager/customer-payment-report', methods=['GET'])
# def payment_report():
#     # GET protocol returns all payment information based on the passed memberID to be used as payment reports from
#     # any specific customer
#     try:
#         # checks if a manager is logged in to view the information
#         employee_id = session.get('employee_session_id')
#         if not employee_id:
#             return jsonify({'message': 'Unauthorized access'}), 401

#         # ensures that the employee is a Technician
#         employee = Employee.query.filter_by(employeeID=employee_id, employeeType='Manager').first()
#         if not employee:
#             return jsonify({'message': 'Unauthorized access'}), 401

#         data = request.json
#         member_id = data.get('memberID')
#         # payments = Payments.query.all() # for debugging
#         payments = Payments.query.filter_by(memberID=member_id).all()
#         payments_info = []
#         for payment in payments:
#             payment_data = {
#                 'paymentID': payment.paymentID,
#                 'paymentStatus': payment.paymentStatus,
#                 'valuePaid': payment.valuePaid,
#                 'valueToPay': payment.valueToPay,
#                 'initialPurchase': payment.initialPurchase,  # Convert to string
#                 'lastPayment': payment.lastPayment,  # Convert to string
#                 'paymentType': payment.paymentType,
#                 'cardNumber': payment.cardNumber,
#                 'expirationDate': payment.expirationDate,
#                 'CVV': payment.CVV,
#                 'routingNumber': payment.routingNumber,
#                 'bankAcctNumber': payment.bankAcctNumber,
#                 'memberID': payment.memberID,
#                 'financingID': payment.memberID
#             }
#             payments_info.append(payment_data)
#         return jsonify({'payments': payments_info}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

'''i DONT THINK THIS ROUTE IS EVER CALLED'''

# @app.route('/api/customer/make-payment', methods=['POST'])
# def manage_payments():
#     # POST protocol is to be used by user for inserting new payments for their purchases. All the information for these
#     try:
#         # ensure that members are logged in and exist
#         member_id = session.get('member_session_id')
#         if not member_id:
#             return jsonify({'message': 'Unauthorized access'}), 401

#         # Ensure that the employee is a Manager
#         member = Member.query.filter_by(memberID=member_id).first()
#         if member is None:
#             return jsonify({'message': 'Unauthorized access'}), 401

#         data = request.json  # Assuming JSON data is sent in the request

#         # Check if it's a vehicle purchase or a service payment
#         purchase_type = data.get('paymentType')
#         if purchase_type == 'Vehicle/Add-on Continuing Payment':
#             # Vehicle purchase payment
#             purchase_id = data.get('purchaseID')

#             # this search is done for continuing purchases on vehicles already bought
#             # we match the incomming sent from the frontend purchase ID with the memberID to make sure they match
#             purchase = Purchases.query.filter_by(purchaseID=purchase_id, memberID=member_id).first()

#             if purchase is None:
#                 return jsonify({'message': 'Invalid purchase ID for additional payments to be made on the car'}), 400

#             value_paid = data.get('valuePaid')

#             # update the value to continue paying
#             purchase.valueToPay -= value_paid
#             purchase.save()

#             # Create a new payment record
#             new_payment = Payments(
#                 paymentStatus='Completed',
#                 valuePaid=value_paid,
#                 valueToPay=purchase.valueToPay,
#                 initialPurchase=purchase.initialPurchase,
#                 lastPayment=datetime.now(),
#                 paymentType='Check/Bank Account',
#                 cardNumber=None,
#                 expirationDate=None,
#                 CVV=None,
#                 routingNumber=purchase.routingNumber,
#                 bankAcctNumber=member.bankAcctNumber,
#                 memberID=member_id,
#                 financingID=purchase.financingID
#             )
#             db.session.add(new_payment)
#         elif purchase_type == 'Service Payment':
#             value_paid = data.get('valuePaid')
#             routing_number = data.get('routingNumber')
#             bank_acc_number = data.get('bankAcctNumber')
#             VIN_carID = data.get('VIN_carID')

#             # checks if there is a service appointment for the given VIN_carID and memberID
#             # ensures also that the car belongs to the member without further checking
#             service_appointment = ServiceAppointment.query.filter_by(
#                 VIN_carID=VIN_carID,
#                 memberID=member_id,
#                 status='Done'
#             ).first()

#             if not service_appointment:
#                 return jsonify({
#                     'message': 'No completed service appointment found for the provided VIN for payment to be made'}), 400

#             # create a new payment record
#             new_payment = Payments(
#                 paymentStatus='Completed',
#                 valuePaid=value_paid,
#                 valueToPay=0,
#                 initialPurchase=datetime.now(),
#                 lastPayment=datetime.now(),
#                 paymentType='Check/Bank Account',
#                 routingNumber=routing_number,
#                 bankAcctNumber=bank_acc_number,
#                 memberID=member_id,
#                 financingID=11  # for all payments that do not involve financing
#             )
#             db.session.add(new_payment)

#             new_purchase = Purchases(
#                 bidID=4,  # for all payments that do not involve bidding
#                 VIN_carID=VIN_carID,
#                 memberID=member_id,
#                 confirmationNumber=confirmation_number_generation(),
#                 purchaseType='Vehicle/Add-on Continuing Payment'
#             )
#             db.session.add(new_purchase)
#         else:
#             return jsonify({'message': 'Invalid purchase type'}), 400

#         db.session.commit()
#         return jsonify({'message': 'Payment information updated successfully'}), 200
#     except Exception as e:
#         # Rollback the session in case of any exception
#         db.session.rollback()
#         return jsonify({'error': str(e)}), 500


'''i DONT THINK THIS ROUTE IS EVER CALLED'''


# # not in use yet
# @app.route('/api/vehicle-purchase/signature', methods=['POST'])
# def get_signature():
#     data = request.json
#     signature = int(data.get('signature'))  # yes = 1, no = 0
#     if signature == 0:
#         return 'No'
#     elif signature == 1:
#         return 'Yes'
#     else:
#         return jsonify({'message': 'Invalid VALUE'}), 400





# @app.route("/@me")
# # Gets user for active session for Members
# def get_current_user():
#     user_id = session.get("member_session_id")

#     # if it is none, basically we then begin the login for employees and NOT members here.
#     # all in one endpoint, thx patrick. This data belongs to him but it's under my commit because I fucked up.
#     if not user_id:
#         user_id = session.get("employee_session_id")

#         if not user_id:
#             return jsonify({"error": "Unauthorized"}), 401
#         employee = Employee.query.filter_by(employeeID=user_id).first()
#         return jsonify({
#             'employeeID': employee.employeeID,
#             'first_name': employee.first_name,
#             'last_name': employee.last_name,
#             'email': employee.email,
#             'phone': employee.phone,
#             'address': employee.address,
#             'employeeType': employee.employeeType,
#         }), 200

#     member = Member.query.filter_by(memberID=user_id).first()
#     sensitive_info = MemberSensitiveInfo.query.filter_by(memberID=user_id).first()  # for returning their Driver ID
#     return jsonify({
#         'memberID': member.memberID,
#         'first_name': member.first_name,
#         'last_name': member.last_name,
#         'email': member.email,
#         'phone': member.phone,
#         'address': member.address,
#         'state': member.state,
#         'zipcode': member.zipcode,
#         'driverID': sensitive_info.driverID,
#         'join_date': member.join_date
#         # in the future will add Address, Zipcode and State on where the member is from
#     }), 200


# @app.route('/api/logout', methods=['POST'])
# def logout():
#     # THE FRONTEND NEEDS TO REDIRECT WHEN U CALL THIS ENDPOINT BACK TO THE LOGIN SCREEN ON that END.
#     # LMK if IT WORKS OR NOT
#     session.clear()
#     return jsonify({'message': 'Logged out successfully'}), 200


# # Route for user authentication
# @app.route('/api/login', methods=['POST'])
# def login():
#     re_string = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
#     try:
#         data = request.json
#         username = data.get('username')

#         # the basis on this check is to better ensure who we are checking for when logging in
#         # Emails = employees
#         # regular Text = members
#         if re.search(re_string, username) is None:
#             # username is not an email, we check for member logging in

#             # checks if the provided data belongs to a member
#             # 'username' parameter is used interchangeably with email for employee and username for member
#             password = data.get('password').encode('utf-8')

#             # if none, then there is no username associated with the account
#             member_match_username = db.session.query(MemberSensitiveInfo).filter(
#                 MemberSensitiveInfo.username == username).first()

#             if member_match_username is None:
#                 return jsonify({'error': 'Invalid username or password.'}), 401

#             stored_hash = member_match_username.password.encode('utf-8')

#             # Check if password matches
#             if bcrypt.checkpw(password, stored_hash):
#                 member_info = db.session.query(Member, MemberSensitiveInfo). \
#                     join(MemberSensitiveInfo, Member.memberID == MemberSensitiveInfo.memberID). \
#                     filter(MemberSensitiveInfo.username == username).first()

#                 if member_info:
#                     member, sensitive_info = member_info
#                     session['member_session_id'] = member.memberID

#                     # just in case because the member create doesn't force them to enter a SSN, so if nothign returns from the DB,
#                     # better to have a text to show on the frontend then just nothing.
#                     return jsonify({
#                         'type': 'member',
#                         'memberID': member.memberID,
#                         'first_name': member.first_name,
#                         'last_name': member.last_name,
#                         'email': member.email,
#                         'phone': member.phone,
#                         'address': member.address,
#                         'state': member.state,
#                         'zipcode': member.zipcode,
#                         'join_date': member.join_date,
#                         'SSN': sensitive_info.SSN,
#                         'driverID': sensitive_info.driverID,
#                         'cardInfo': sensitive_info.cardInfo
#                     }), 200
#             else:
#                 return jsonify({'error': 'Invalid username or password.'}), 401
#         else:
#             # the username is an email, we check for employee logging in

#             email = username
#             password = data.get('password').encode('utf-8')

#             # if none, then there is no username associated with the account
#             sensitive_info_username_match = db.session.query(EmployeeSensitiveInfo). \
#                 join(Employee, Employee.employeeID == EmployeeSensitiveInfo.employeeID). \
#                 filter(Employee.email == email).first()

#             if sensitive_info_username_match is None:
#                 return jsonify({'error': 'Invalid username or password.'}), 401

#             stored_hash = sensitive_info_username_match.password.encode('utf-8')
#             # Check if password matches
#             if bcrypt.checkpw(password, stored_hash):
#                 employee_data = db.session.query(Employee, EmployeeSensitiveInfo). \
#                     join(EmployeeSensitiveInfo, Employee.employeeID == EmployeeSensitiveInfo.employeeID). \
#                     filter(Employee.email == email).first()

#                 if employee_data:
#                     employee, sensitive_info = employee_data
#                     session['employee_session_id'] = employee.employeeID
#                     response = {
#                         'employeeID': employee.employeeID,
#                         'first_name': employee.first_name,
#                         'last_name': employee.last_name,
#                         'email': employee.email,
#                         'phone': employee.phone,
#                         'address': employee.address,
#                         'employeeType': employee.employeeType,
#                     }
#                     return jsonify(response), 200
#             else:
#                 return jsonify({'error': 'Invalid username or password.'}), 401

#         # If neither member nor employee, return error
#         return jsonify({'error': 'Invalid credentials or user type'}), 404
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
