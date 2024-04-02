# app/models.py

from . import db
from sqlalchemy import Enum, ForeignKey


# Defined SQLAlchemy models to represent database tables


class Cars(db.Model):
    # cars table model
    __tablename__ = 'Cars'
    VIN_carID = db.Column(db.String(17), primary_key=True)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    body = db.Column(db.String(50))
    year = db.Column(db.Integer)
    color = db.Column(db.String(50))
    mileage = db.Column(db.Integer)
    details = db.Column(db.String(255))
    description = db.Column(db.Text)
    viewsOnPage = db.Column(db.Integer)
    pictureLibraryLink = db.Column(db.Text)
    status = db.Column(Enum('new', 'sold', 'low-mileage', 'being-watched'))
    price = db.Column(db.DECIMAL(10, 2))


class Member(db.Model):
    # Member table model
    __tablename__ = 'Member'
    memberID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    join_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())


class TestDrive(db.Model):
    # TestDrive table model
    __tablename__ = 'TestDrive'
    testdrive_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    VIN_carID = db.Column(db.String(17), ForeignKey('Cars.VIN_carID'))
    appointment_date = db.Column(db.TIMESTAMP)
    confirmation = db.Column(Enum('Confirmed', 'Denied', 'Cancelled', 'Awaiting Confirmation'))


class ServiceAppointment(db.Model):
    # ServiceAppointment table model
    __tablename__ = 'ServiceAppointment'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    appointment_date = db.Column(db.DATE)
    service_name = db.Column(db.String(100))


class Employee(db.Model):
    # Employee table model
    __tablename__ = 'Employee'
    employeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    employeeType = db.Column(Enum('superAdmin', 'Manager', 'Technician'))


class EmployeeSensitiveInfo(db.Model):
    # EmployeeSensitiveInfo table model
    __tablename__ = 'EmployeeSensitiveInfo'
    sensitiveID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employeeID = db.Column(db.Integer, ForeignKey('Employee.employeeID'))
    password = db.Column(db.String(255))
    SSN = db.Column(db.String(255), unique=True)
    driverID = db.Column(db.String(255))
    lastModified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                             onupdate=db.func.current_timestamp())


class MemberSensitiveInfo(db.Model):
    # MemberSensitiveInfo table model
    __tablename__ = 'MemberSensitiveInfo'
    sensitiveID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'), unique=True)
    SSN = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.TEXT)
    driverID = db.Column(db.String(15), unique=True)
    cardInfo = db.Column(db.TEXT)
    lastModified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                             onupdate=db.func.current_timestamp())


class Financing(db.Model):
    # Financing table model
    __tablename__ = 'Financing'
    financingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    income = db.Column(db.Integer)
    credit_score = db.Column(db.Integer)
    loan_total = db.Column(db.Integer)
    down_payment = db.Column(db.Integer)
    percentage = db.Column(db.Integer)
    monthly_sum = db.Column(db.Integer)
    remaining_months = db.Column(db.Integer)


class Payments(db.Model):
    # Payments table model
    __tablename__ = 'Payments'
    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paymentStatus = db.Column(Enum('Completed', 'Pending', 'Failed', 'None'))
    valuePaid = db.Column(db.String(20))
    valueToPay = db.Column(db.String(20))
    initialPurchase = db.Column(db.TIMESTAMP)
    lastPayment = db.Column(db.TIMESTAMP)
    paymentType = db.Column(Enum('Check/Bank Account', 'Card', 'None'))
    cardNumber = db.Column(db.TEXT)
    expirationDate = db.Column(db.TEXT)
    CVV = db.Column(db.TEXT)
    routingNumber = db.Column(db.TEXT)
    bankAcctNumber = db.Column(db.TEXT)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    financingID = db.Column(db.Integer, ForeignKey('Financing.financingID'))


class Bids(db.Model):
    # Bids table model
    __tablename__ = 'Bids'
    bidID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    bidValue = db.Column(db.DECIMAL(10, 2))
    bidStatus = db.Column(Enum('Confirmed', 'Denied', 'Processing', 'None'))
    bidTimestamp = db.Column(db.TIMESTAMP)


class Purchases(db.Model):
    # Purchases table model
    __tablename__ = 'Purchases'
    purchaseID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bidID = db.Column(db.Integer, ForeignKey('Bids.bidID'))
    VIN_carID = db.Column(db.String(17), ForeignKey('Cars.VIN_carID'))
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    confirmationNumber = db.Column(db.String(13), unique=True)


class Addons(db.Model):
    # Addons table model
    __tablename__ = 'Addons'
    itemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemName = db.Column(db.String(100))
    totalCost = db.Column(db.DECIMAL(10, 2))

# not important to use rn, will get these up and running at a later date
# class MemberAuditLog(db.Model):
#     __tablename__ = 'MemberAuditLog'
#     logID = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
#     event_description = db.Column(db.TEXT)
#     event_timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
#
#
# class EmployeeAuditLog(db.Model):
#     __tablename__ = 'EmployeeAuditLog'
#     logID = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     employeeID = db.Column(db.Integer, ForeignKey('Employee.employeeID'))
#     event_description = db.Column(db.TEXT)
#     event_timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
