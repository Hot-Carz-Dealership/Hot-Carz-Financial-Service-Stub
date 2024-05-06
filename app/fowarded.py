import re
import random
import string
import bcrypt
from . import app
from .models import *
from datetime import datetime
from sqlalchemy import text, desc, func
from flask import jsonify, request, session
from sqlalchemy.exc import IntegrityError
import calendar

#### GOING TO DELETE THIS FILE LATER JUST USING IT FOR NOW TO CHECK IF EVERYTHING WORKS WITH /FORWARD

#Worked with /foward
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


#FOR MANAGER TO GET THE FINANCING INFO OF A SPECIFIC MEMBER
@app.route('/api/manager/get-financing', methods=['POST'])
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