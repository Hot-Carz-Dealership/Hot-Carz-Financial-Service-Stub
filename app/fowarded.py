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