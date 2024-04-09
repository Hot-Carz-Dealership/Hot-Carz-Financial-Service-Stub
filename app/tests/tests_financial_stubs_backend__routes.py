# tests/tests_financial_stubs_backend_routes.py
# this file contains unit tests for the Financial Operations and Stubs Backend Endpoints

import json
import pytest
import string
import random
from app import app, db
from app.models import Cars, Member, MemberSensitiveInfo, Employee, EmployeeSensitiveInfo, ServiceAppointment

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client
