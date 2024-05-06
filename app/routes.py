# app/routes.py

import re
import random
import string
import hashlib

import bcrypt
from . import app
from .models import *
from datetime import datetime, timedelta
from sqlalchemy import text, desc, func
from flask import jsonify, request, session
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, ROUND_HALF_UP


import calendar

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

### I couldn't figure out how to transfer the session id over so for now this works for testing at least
### I'll just have the login frontend also make a request to this until i figure out some better solution

@app.route("/@me")
# Gets user for active session for Members
def get_current_user():
    user_id = session.get("member_session_id")

    # if it is none, basically we then begin the login for employees and NOT members here.
    # all in one endpoint, thx patrick. This data belongs to him but it's under my commit because I fucked up.
    if not user_id:
        user_id = session.get("employee_session_id")

        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        employee = Employee.query.filter_by(employeeID=user_id).first()
        return jsonify({
            'employeeID': employee.employeeID,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'email': employee.email,
            'phone': employee.phone,
            'address': employee.address,
            'employeeType': employee.employeeType,
        }), 200

    member = Member.query.filter_by(memberID=user_id).first()
    sensitive_info = MemberSensitiveInfo.query.filter_by(memberID=user_id).first()  # for returning their Driver ID
    return jsonify({
        'memberID': member.memberID,
        'first_name': member.first_name,
        'last_name': member.last_name,
        'email': member.email,
        'phone': member.phone,
        'address': member.address,
        'state': member.state,
        'zipcode': member.zipcode,
        'driverID': sensitive_info.driverID,
        'join_date': member.join_date
        # in the future will add Address, Zipcode and State on where the member is from
    }), 200



@app.route('/api/logout', methods=['POST'])
def logout():
    # THE FRONTEND NEEDS TO REDIRECT WHEN U CALL THIS ENDPOINT BACK TO THE LOGIN SCREEN ON that END.
    # LMK if IT WORKS OR NOT
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


# Route for user authentication
@app.route('/api/login', methods=['POST'])
def login():
    re_string = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    try:
        data = request.json
        username = data.get('username')

        # the basis on this check is to better ensure who we are checking for when logging in
        # Emails = employees
        # regular Text = members
        if re.search(re_string, username) is None:
            # username is not an email, we check for member logging in

            # checks if the provided data belongs to a member
            # 'username' parameter is used interchangeably with email for employee and username for member
            password = data.get('password').encode('utf-8')

            # if none, then there is no username associated with the account
            member_match_username = db.session.query(MemberSensitiveInfo).filter(
                MemberSensitiveInfo.username == username).first()

            if member_match_username is None:
                return jsonify({'error': 'Invalid username or password.'}), 401

            stored_hash = member_match_username.password.encode('utf-8')

            # Check if password matches
            if bcrypt.checkpw(password, stored_hash):
                member_info = db.session.query(Member, MemberSensitiveInfo). \
                    join(MemberSensitiveInfo, Member.memberID == MemberSensitiveInfo.memberID). \
                    filter(MemberSensitiveInfo.username == username).first()

                if member_info:
                    member, sensitive_info = member_info
                    session['member_session_id'] = member.memberID

                    # just in case because the member create doesn't force them to enter a SSN, so if nothign returns from the DB,
                    # better to have a text to show on the frontend then just nothing.
                    return jsonify({
                        'type': 'member',
                        'memberID': member.memberID,
                        'first_name': member.first_name,
                        'last_name': member.last_name,
                        'email': member.email,
                        'phone': member.phone,
                        'address': member.address,
                        'state': member.state,
                        'zipcode': member.zipcode,
                        'join_date': member.join_date,
                        'SSN': sensitive_info.SSN,
                        'driverID': sensitive_info.driverID,
                        'cardInfo': sensitive_info.cardInfo
                    }), 200
            else:
                return jsonify({'error': 'Invalid username or password.'}), 401
        else:
            # the username is an email, we check for employee logging in

            email = username
            password = data.get('password').encode('utf-8')

            # if none, then there is no username associated with the account
            sensitive_info_username_match = db.session.query(EmployeeSensitiveInfo). \
                join(Employee, Employee.employeeID == EmployeeSensitiveInfo.employeeID). \
                filter(Employee.email == email).first()

            if sensitive_info_username_match is None:
                return jsonify({'error': 'Invalid username or password.'}), 401

            stored_hash = sensitive_info_username_match.password.encode('utf-8')
            # Check if password matches
            if bcrypt.checkpw(password, stored_hash):
                employee_data = db.session.query(Employee, EmployeeSensitiveInfo). \
                    join(EmployeeSensitiveInfo, Employee.employeeID == EmployeeSensitiveInfo.employeeID). \
                    filter(Employee.email == email).first()

                if employee_data:
                    employee, sensitive_info = employee_data
                    session['employee_session_id'] = employee.employeeID
                    response = {
                        'employeeID': employee.employeeID,
                        'first_name': employee.first_name,
                        'last_name': employee.last_name,
                        'email': employee.email,
                        'phone': employee.phone,
                        'address': employee.address,
                        'employeeType': employee.employeeType,
                    }
                    return jsonify(response), 200
            else:
                return jsonify({'error': 'Invalid username or password.'}), 401

        # If neither member nor employee, return error
        return jsonify({'error': 'Invalid credentials or user type'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500



'''
I dont want to fuck with this one for now cause its being worked on. 
There is a copy of this in backend right now


        # Get the member ID from the request JSON data
        request_data = request.json
        member_id = request_data.get('member_id')

        # Validate the member ID
        if not member_id:
            return jsonify({'message': 'Member ID is required'}), 400


'''
@app.route('/api/member/current-bids', methods=['GET', 'POST'])
def current_member_bids():
    # check if the member is logged in, if not redirect them to log in
    member_id = session.get('member_session_id')
    if not member_id:
        return jsonify({'message': 'Unauthorized access. Please log in.'}), 401

    # check if the member exists
    member = Member.query.get(member_id)
    if not member:
        return jsonify({'message': 'Member not found'}), 404

    # GET Request: returns all bid information based on the logged in member and their memberID
    if request.method == 'GET':
        bids = Bids.query.filter_by(memberID=member_id).all()
        if not bids:
            return jsonify({'message': 'No bids found for this member'}), 404
        bid_info = [{'bidID': bid.bidID,
                     'memberID': bid.memberID,
                     'VIN_carID': bid.VIN_carID,
                     'bidValue': bid.bidValue,
                     'bidStatus': bid.bidStatus,
                     'bidTimestamp': bid.bidTimestamp
                     }
                    for bid in bids]
        return jsonify(bid_info), 200
    elif request.method == 'POST':
        # frontend needs to pass these values in for it to work
        data = request.json
        bid_id = data.get('bid_id') # these should work as a button accociated with the bid value/row
        new_bid_value = data.get('new_bid_value')

        if bid_id is None or new_bid_value is None:
            return jsonify({'message': 'Bid ID and new Bid Value is required in the request'}), 400

        # finds the denied bid and then copies all other relevant meta data in a nice manner to avoid stupid overworking things
        denied_bid = Bids.query.filter_by(memberID=member_id, bidID=bid_id, bidStatus='Denied').first()
        if denied_bid:
            new_bid = Bids(memberID=member_id, VIN_carID=denied_bid.VIN_carID, bidValue=new_bid_value,
                           bidStatus='Processing', bidTimestamp=datetime.now())
            db.session.add(new_bid)
            db.session.commit()
            return jsonify({'message': 'New bid placed successfully'}), 201
        else:
            return jsonify({'message': 'Denied bid not found for this member with the provided bid ID'}), 404


#WORKED WITH /FORWARD
@app.route('/api/vehicle-purchase/new-bid-insert', methods=['POST'])
# Adds a new bid to bid table
def bid_insert_no_financing():
    try:
        # Extract data from the request
        data = request.get_json()
        required_fields = ['member_id', 'vin', 'bid_value']
        
        # Check if all required fields are present
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'message': f'Error: Missing fields - {", ".join(missing_fields)}'}), 400
        
        # Extract data
        member_id = data['member_id']
        vin = data['vin']
        bid_value = data['bid_value']
        bid_status = 'Processing'
        
        # Create a new bid entry
        new_bid = Bids(
            memberID=member_id,
            VIN_carID=vin,
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

#WORKED WITH /FORWARD
@app.route('/api/manager/current-bids', methods=['GET', 'POST'])
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
                        'bidID' : bid.bidID,
                        'make': car.make,
                        'model': car.model,
                        'VIN': car.VIN_carID,
                        'MSRP': car.price,
                        'bidValue': bid.bidValue,
                        'bidStatus': bid.bidStatus,
                        'memberID' : bid.memberID
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
            return jsonify({'message': 'Bid status updated successfully'}),200
        else:
            return jsonify({'error': 'Bid not found'}), 404

#WORKED WITH /FORWARD
@app.route('/api/manager/get-financing', methods=['POST'])
#FOR MANAGER TO GET THE FINANCING INFO OF A SPECIFIC MEMBER
def get_financing_for_member():
    try:
        # Get the member ID from the request JSON data
        request_data = request.json
        member_id = request_data.get('member_id')

        # Validate the member ID
        if not member_id:
            return jsonify({'message': 'Member ID is required'}), 400

        # Query financing information for the specified member
        financing_info = Financing.query \
            .filter_by(memberID=member_id) \
            .all()

        # Check if any financing information is found
        if not financing_info:
            return jsonify({'message': 'No financing information found for the member'}), 404

        # Serialize the financing information
        serialized_data = []
        for financing in financing_info:
            # Fetch member details using a separate query
            member = Member.query.get(financing.memberID)
            if member:
                serialized_data.append({
                    'VIN_carID': financing.VIN_carID,
                    'income': financing.income,
                    'credit_score': financing.credit_score,
                    'loan_total': financing.loan_total,
                    'down_payment': financing.down_payment,
                    'percentage': financing.percentage,
                    'monthly_payment_sum': financing.monthly_payment_sum,
                    'remaining_months': financing.remaining_months,
                    'first_name': member.first_name,
                    'last_name': member.last_name,
                    'phone': member.phone
                })

        return jsonify(serialized_data), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

'''Currently workes with /forward but potentially might need chnaging'''
@app.route('/api/manager/monthly-sales-report', methods=['GET'])
# this API generates monthly sales reports on all payments made in the dealership
# Scufffedd but i think it works
def monthly_sales_report():
    # checks if a manager is logged in to view the information | uncomment when we have it working for sure 100% on frontend in implementation | commented manager session out for testing and ensuring it works
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
    # Get month and year from request parameters
    month = request.args.get('month')  # 1-12 for selected month
    year = request.args.get('year')    # YYYY format for selected year

    # Validate month and year inputs
    if not month or not year:
        return jsonify({'message': 'Month and year are required parameters'}), 400

    try:
        month = int(month)
        year = int(year)
    except ValueError:
        return jsonify({'message': 'Invalid month or year format'}), 400

    # Validate month range
    if month < 1 or month > 12:
        return jsonify({'message': 'Invalid month value. Month should be between 1 and 12'}), 400


    # Debugging statements for month and year
    print("Selected month:", month)
    print("Selected year:", year)

    # Get current date
    current_date = datetime.now()

    # Debugging statement for current date
    print("Current date:", current_date)

    # Get the last day of the selected month dynamically
    last_day_of_month = calendar.monthrange(int(year), int(month))[1]

    # Set the start date and end date using the last day of the month
    start_date = datetime(int(year), int(month), 1)
    end_date = datetime(int(year), int(month), last_day_of_month)

    # Hardcoded definitions for dates
    start_of_year = datetime(int(year), 1, 1)
    last_year_start = datetime(int(year) - 1, 1, 1)
    last_year_end = datetime(int(year) - 1, 12, 31)
    last_year_month_start = datetime(int(year) - 1, int(month), 1)
    
    # Check if it's February and the last day of the month is 29 (indicating a leap year)
    if int(month) == 2 and last_day_of_month == 29:
        # Adjust the last day of February to 28 for non-leap years
        last_day_of_month = 28
        
    last_year_month_end = datetime(int(year) - 1, int(month), last_day_of_month)

    # Debugging statements for dates
    print("Start date of selected month:", start_date)
    print("End date of selected month:", end_date)
    print("Start date of last year:", last_year_start)
    print("End date of last year:", last_year_end)
    print("Start date of last year's selected month:", last_year_month_start)
    print("End date of last year's selected month:", last_year_month_end)
    # Query purchases for monthly report
    purchases = Purchases.query.filter(db.extract('month', Purchases.purchaseDate) == month,
                                       db.extract('year', Purchases.purchaseDate) == year).all()

    # Prepare sales report data for monthly report
    total_sales = 0
    sales_report = []

    # Calculate total sales and populate sales report for monthly report
    for purchase in purchases:
        bid_value = 0  # Default value if bid is None
        bid_id = None  # Default value for bid ID
        if purchase.bidID is not None:
            # If a bid is associated with the purchase, retrieve the bid value and ID
            bid = Bids.query.get(purchase.bidID)
            if bid:
                bid_value = bid.bidValue
                bid_id = bid.bidID
            else:
                print(f"Bid not found for Purchase ID: {purchase.purchaseID}")

        total_sales += bid_value

        sales_report.append({
            'purchase_id': purchase.purchaseID,
            'member_id': purchase.memberID,
            'vehicle_id': purchase.VIN_carID,
            'confirmation_number': purchase.confirmationNumber,
            'purchase_type': purchase.purchaseType,
            'purchase_timestamp': purchase.purchaseDate.isoformat(),
            'bid_id': bid_id,
            'bid_value': str(bid_value)  # Convert Decimal to string for JSON serialization
        })

    # Query purchases for other types of reports
    all_time_sales = Purchases.query.all()
    yearly_sales = Purchases.query.filter(Purchases.purchaseDate >= start_date, Purchases.purchaseDate <= end_date).all()
    last_year_sales = Purchases.query.filter(Purchases.purchaseDate >= last_year_start, Purchases.purchaseDate <= last_year_end).all()
    last_year_month_sales = Purchases.query.filter(Purchases.purchaseDate >= last_year_month_start, Purchases.purchaseDate <= last_year_month_end).all()

    yearly_purchases = Purchases.query.filter(db.extract('year', Purchases.purchaseDate) == year).all()

    # Calculate total sales for other types of reports
    total_all_time_sales = sum(Bids.query.get(purchase.bidID).bidValue if (purchase.bidID is not None and Bids.query.get(purchase.bidID) is not None) else 0 for purchase in all_time_sales)
    total_yearly_sales = sum(Bids.query.get(purchase.bidID).bidValue if (purchase.bidID is not None and Bids.query.get(purchase.bidID) is not None) else 0 for purchase in yearly_sales)
    total_last_year_sales = sum(Bids.query.get(purchase.bidID).bidValue if (purchase.bidID is not None and Bids.query.get(purchase.bidID) is not None) else 0 for purchase in last_year_sales)
    total_last_year_month_sales = sum(Bids.query.get(purchase.bidID).bidValue if (purchase.bidID is not None and Bids.query.get(purchase.bidID) is not None) else 0 for purchase in last_year_month_sales)

    # Calculate total sales for the current year
    total_this_year = sum(Bids.query.get(purchase.bidID).bidValue if (purchase.bidID is not None and Bids.query.get(purchase.bidID) is not None) else 0 for purchase in yearly_purchases)



    return jsonify({
        'total_sales': str(total_sales),  # Convert total sales to string for JSON serialization
        'total_this_year': str(total_this_year),  # Total sales for the selected year
        'all_time_sales': str(total_all_time_sales),
        'yearly_sales': str(total_yearly_sales),
        'last_year_sales': str(total_last_year_sales),
        'last_year_month_sales': str(total_last_year_month_sales),
        'sales_report': sales_report
    }), 200

'''I don't think this actually ever called but it is referenced in managerPage.js'''
# @app.route('/api/purchases', methods=['GET'])
# # this endpoint returns all of the purchase information to be viewed by the manager or superAdmin
# def all_purchases():
#     # returns all purchases from the purchases Table in the DB
#     purchases = Purchases.query.all()  # queries all purchases
#     purchases_list = []

#     for purchase in purchases:
#         purchase_data = {
#             'purchaseID': purchase.purchaseID,
#             'bidID': purchase.bidID,
#             'VIN_carID': purchase.VIN_carID,
#             'memberID': purchase.memberID,
#             'confirmationNumber': purchase.confirmationNumber
#         }
#         purchases_list.append(purchase_data)

#     return jsonify({'purchases': purchases_list}), 200


'''ONE SMALL STEP 🧑‍🚀'''


'''
        # Get the member ID from the request JSON data
        data = request.json
        member_id = data.get('member_id')

'''

@app.route('/api/vehicle-purchase/apply-for-financing', methods=['POST'])
# Route just to apply for financing and returns terms if user is eligible
# This wont add to any tables yet,
# we'll have the front end send back the same terms if users accepts in another route
##The user will accept by typing in their name or initials(aka signing)
def apply_for_financing():
    try:
        # customer auth for making sure they are logged in and have an account
        # member_id = session.get('member_session_id')
        # Get the member ID from the request JSON data
        data = request.json
        member_id = data.get('member_id')
        if member_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        # frontend needs to send these values to the backend
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        Vin_carID = data.get('Vin_carID')
        down_payment = float(data.get('down_payment'))
        monthly_income = float(data.get('monthly_income'))
        vehicle_cost = float(
            data.get('vehicle_cost'))  # Front end can send this based on if the user won a bid or buying at MSRP

        credit_score = creditScoreGenerator(member_id, monthly_income)
        total_cost = adjust_loan_with_downpayment(vehicle_cost, down_payment)
        finance_interest = calculateInterest(total_cost, monthly_income, credit_score)

        # Loan eligibility
        loan_eligibility = check_loan_eligibility(total_cost, monthly_income)
        if not loan_eligibility:
            return jsonify({
                               'message': 'Your yearly income is not sufficient to take on this loan. Reapply with more down payment'}), 400

        # downPayment_value = total_cost - financing_loan_amount
        valueToPay_value = round(total_cost + finance_interest, 2)
        paymentPerMonth_value = round(valueToPay_value / 48, 2)

        # Create a dictionary with financing terms
        financing_terms = {
            'member_id': member_id,
            'income': int(monthly_income) * 12,
            'credit_score': credit_score,
            'loan_total': valueToPay_value,
            'down_payment': down_payment,
            'percentage': interest_rate(credit_score),
            'monthly_payment_sum': paymentPerMonth_value,
            'remaining_months': 48,
            'Vin_carID': Vin_carID,
            'financed_amount': total_cost,
            'interest_total': finance_interest
        }

        # Return the financing terms as JSON
        # Front End should save this somewhere
        # If the user accepts by signing then use the /insert-financing route

        return jsonify({'financing_terms': financing_terms}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500


@app.route('/api/vehicle-purchase/insert-financing', methods=['POST'])
# Use this route whenever the user accepts the loan to add it to the db
def insert_financing():
    try:

        # customer auth for making sure they are logged in and have an account
        # member_id = session.get('member_session_id')
        # Get the member ID from the request JSON data
        data = request.json
        member_id = data.get('member_id')
        if member_id is None:
            return jsonify({'message': 'Invalid session'}), 400

        # Validate required fields
        data = request.json
        required_fields = ['VIN_carID', 'income', 'credit_score', 'loan_total', 'down_payment', 'percentage',
                           'monthly_payment_sum', 'remaining_months']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400

        # Retrieve data from the request
        data = request.json
        VIN_carID = data.get('VIN_carID')
        income = data.get('income')
        credit_score = data.get('credit_score')
        loan_total = data.get('loan_total')
        down_payment = data.get('down_payment')
        percentage = data.get('percentage')
        monthly_payment_sum = data.get('monthly_payment_sum')
        remaining_months = data.get('remaining_months')

        if VIN_carID:
            # Check if the provided VIN exists in the carinfo table
            car = CarInfo.query.filter_by(VIN_carID=VIN_carID).first()
            if not car:
                return jsonify({'error': 'Car with provided VIN not found'}), 404

        # Insert data into the database
        new_financing = Financing(
            memberID=member_id,
            VIN_carID=VIN_carID,
            income=income,
            credit_score=credit_score,
            loan_total=loan_total,
            down_payment=down_payment,
            percentage=percentage,
            monthly_payment_sum=monthly_payment_sum,
            remaining_months=remaining_months
        )
        db.session.add(new_financing)
        db.session.commit()

        return jsonify({'message': 'Financing information inserted successfully.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/vehicle-purchase/make-purchase', methods=['POST'])
# Route Where all purchases will be made for car,addons, or service center
def make_purchase():
    # here we deal with Purchases and Payments table    
    try:
        member_id = session.get('member_session_id')
        if not member_id:
            return jsonify({'message': 'Unauthorized access. Please log in.'}), 403

        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['routingNumber', 'bankAcctNumber', 'Amount Due Now', 'Financed Amount']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            error_message = f'Missing required field(s): {", ".join(missing_fields)}'
            return jsonify({'error': error_message}), 400

        # Gen a single confirmation number for the purchase
        confirmation_number = confirmation_number_generation()

        # Retrieve cart items
        cart_items = CheckoutCart.query.filter_by(memberID=member_id).all()

        # Extract data from JSON request

        # Needed for purchases table
        VIN_carID = None
        addon_ID = None
        serviceID = None
        bidID = None
        # purchaseType = None

        # Needed for payments table
        financed_amount = Decimal(data.get('Financed Amount', 0))
        valuePaid = Decimal(data.get('Amount Due Now', 0))
        routingNumber = data.get('routingNumber')
        bankAcctNumber = data.get('bankAcctNumber')
        financingID = None
        # Add validation on front end for routing and acct numbers

        # Lists to accumulate VINs and addon IDs
        vin_with_addons = None
        addons = []

        # Add cart items to the Purchases table
        for item in cart_items:
            bidID = None
            addon_ID = item.addon_ID
            # Check if VIN_carID exists in the bids table and get bidID if it does
            VIN_carID = item.VIN_carID
            if VIN_carID:
                vin_with_addons = VIN_carID
                bid = Bids.query.filter_by(VIN_carID=VIN_carID).first()
                if bid:
                    bidID = bid.bidID
                if item.financed_amount:
                    # looks up the financing id of the car being financed
                    financing = Financing.query.filter_by(VIN_carID=VIN_carID).first()
                    if financing:
                        financingID = financing.financingID
            # If the item is an addon, add addon to the lists
            if addon_ID:
                addons.append(addon_ID)

            new_purchase = Purchases(
                bidID=bidID,
                memberID=member_id,
                VIN_carID=VIN_carID,
                addon_ID=item.addon_ID,
                serviceID=item.serviceID,
                confirmationNumber=confirmation_number,
                purchaseType='Vehicle/Add-on Purchase' if not item.serviceID else 'Service Payment',
                purchaseDate=datetime.now(),
                signature='No'
            )
            # Check if provided IDs exist
            if VIN_carID and not CarInfo.query.filter_by(VIN_carID=VIN_carID).first():
                return jsonify({'error': 'Car with provided VIN not found'}), 404
            elif addon_ID and not Addons.query.filter_by(itemID=addon_ID).first():
                return jsonify({'error': 'Addon with provided ID not found'}), 404
            elif serviceID and not Services.query.filter_by(serviceID=serviceID).first():
                return jsonify({'error': 'Service with provided ID not found'}), 404

            # Update CarInfo status to 'sold'
            db.session.query(CarInfo).filter_by(VIN_carID=VIN_carID).update({'status': 'sold'})
            # Update CarVINs purchase_status to 'Dealership - Purchased' and memberID to current memberID
            db.session.query(CarVINs).filter_by(VIN_carID=VIN_carID).update(
                {'purchase_status': 'Dealership - Purchased', 'memberID': member_id})

            db.session.commit()

            db.session.add(new_purchase)
            db.session.commit()

        # Create Warranty instances for each addon associated with the VIN
        for addon in addons:
            new_warranty = Warranty(
                VIN_carID=vin_with_addons,
                addon_ID=addon
            )
            db.session.add(new_warranty)

        # Add cart items to the OrderHistory table
        for item in cart_items:
            new_order_history = OrderHistory(
                memberID=member_id,
                item_name=item.item_name,
                item_price=item.item_price,
                financed_amount=item.financed_amount,
                confirmationNumber=confirmation_number,
                purchaseDate=datetime.now()
            )
            db.session.add(new_order_history)
            db.session.commit()

        # Hash the bank info
        routingNumber = bcrypt.hashpw(routingNumber.encode('utf-8'), bcrypt.gensalt())
        bankAcctNumber = bcrypt.hashpw(bankAcctNumber.encode('utf-8'), bcrypt.gensalt())

        new_payment = Payments(
            paymentStatus='Completed',
            valuePaid=valuePaid.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            valueToPay=financed_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            initialPurchase=datetime.now(),
            lastPayment=datetime.now(),
            routingNumber=routingNumber,
            bankAcctNumber=bankAcctNumber,
            memberID=member_id,
            financingID=financingID
        )
        db.session.add(new_payment)
        db.session.commit()

        # payment stub generation can occur through the means of functions above with endpoints
        # /api/member
        # /api/payments

        # need to clear the cart after wards using delete cart route on front end

        return jsonify({'message': 'Purchase made successfully.',
                        'confirmation_number':confirmation_number}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error: {str(e)}'}), 500


















                                #################################
                                #                               #
                                #   ''' Helper Functions'''     #
                                #                               #
                                #################################
                                
def regex_bank_acct_check(routing_number: str, account_number: str) -> bool:
    # regex validation for the routing number and account number to be correct
    routing_regex = re.compile(r'^[0-9]{9}$')
    account_regex = re.compile(r'^[0-9]{9,12}$')  # Bank account numbers vary from 9 to 12 char length

    if not routing_regex.match(routing_number):
        return False
    if not account_regex.match(account_number):
        return False
    return True


def regex_ssn(ssn: str) -> bool:
    # regex validation for SSN values
    ssn_regex = re.compile(r'(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}$')
    if not ssn_regex.match(ssn):
        return False
    return True



def return_vehicle_cost(vehicle_vin):
    # Validate vehicle VIN
    # if not is_valid_vin(vehicle_vin):
    #     raise ValueError("Invalid VIN format.")

    # Retrieve vehicle price from the database
    vehicle = CarInfo.query.filter_by(VIN_carID=vehicle_vin).first()
    
    if not vehicle:
        raise ValueError("Vehicle with VIN {} not found.".format(vehicle_vin))

    return vehicle.price





def creditScoreGenerator(member_id: int, monthly_income: float) -> int:
    # Creates a random credit score based on id and income so that the same is always returned
    # Create a unique seed based on member_id and monthly_income
    seed = hashlib.sha256(f"{member_id}-{monthly_income}".encode()).hexdigest()
    # Convert the seed to an integer for seeding the random number generator
    seed_int = int(seed, 16) % (10 ** 8)  # Modulo to keep the number within an appropriate range
    # Seed the random number generator
    random.seed(seed_int)
    # Generate a random credit score
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

def calculateInterest(vehicleCost: int, monthlyIncome: int, creditscore: int) -> float:
    # generates the total amount financed after interest 

    base_loan_interest_rate = interest_rate(creditscore)
    # Calculate financing value based on vehicle cost and monthly income
    final_financing_percentage = base_loan_interest_rate + ((vehicleCost / monthlyIncome) * 100)
    financing_loan_value = (final_financing_percentage / 100) * vehicleCost
    return round(financing_loan_value, 2)


def confirmation_number_generation() -> str:
    try:
        total_chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(total_chars) for i in range(13))
    except Exception as e:
        # Log the exception or handle it appropriately
        print(f"Error generating confirmation number: {e}")
        return None



