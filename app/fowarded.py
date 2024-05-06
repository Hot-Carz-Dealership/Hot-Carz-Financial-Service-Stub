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
