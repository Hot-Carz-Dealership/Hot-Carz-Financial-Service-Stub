# app/models.py
from . import db
from sqlalchemy import Enum, ForeignKey

# states

# Define SQLAlchemy models to represent database tables

'''example code on how to use models in flask'''


class Cars(db.Model):
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
    inStock = db.Column(Enum('yes', 'no'))
    stockAmount = db.Column(db.Integer)
    viewsOnPage = db.Column(db.Integer)
    pictureLibraryLink = db.Column(db.Text)
    status = db.Column(Enum('new', 'sold', 'low-mileage', 'being-watched'))
    price = db.Column(db.DECIMAL(10, 2))


class Member(db.Model):
    __tablename__ = 'Member'
    memberID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    status = db.Column(Enum('Confirmed', 'Denied', 'Cancelled'))
    join_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())


class TestDrive(db.Model):
    __tablename__ = 'TestDrive'
    testdrive_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'))
    car_id = db.Column(db.String(17), ForeignKey('cars.VIN_carID'))
    appointment_date = db.Column(db.TIMESTAMP)
    confirmation = db.Column(Enum('confirm', 'deny', 'Awaiting Confirmation'))


class Financing(db.Model):
    __tablename__ = 'Financing'
    financing_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'))
    credit_score = db.Column(db.Integer)
    loan_total = db.Column(db.Integer)
    down_payment = db.Column(db.Integer)
    percentage = db.Column(db.Integer)
    monthly_sum = db.Column(db.Integer)
    remaining_months = db.Column(db.Integer)


class ServiceAppointment(db.Model):
    __tablename__ = 'ServiceAppointment'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'))
    technician_id = db.Column(db.Integer)
    appointment_date = db.Column(db.DATE)
    service_name = db.Column(db.String(100))


class Employee(db.Model):
    __tablename__ = 'Employee'
    employeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    employeeType = db.Column(Enum('superAdmin', 'manager', 'technician'))


class EmployeeSensitiveInfo(db.Model):
    __tablename__ = 'EmployeeSensitiveInfo'
    sensitiveID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employeeID = db.Column(db.Integer, ForeignKey('employee.employeeID'))
    password = db.Column(db.String(255))
    SSN = db.Column(db.String(255), unique=True)
    driverID = db.Column(db.String(255))
    lastModified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                             onupdate=db.func.current_timestamp())


class MemberSensitiveInfo(db.Model):
    __tablename__ = 'MemberSensitiveInfo'
    sensitiveID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'), unique=True)
    SSN = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.TEXT)
    driverID = db.Column(db.String(15), unique=True)
    cardInfo = db.Column(db.TEXT)
    lastModified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                             onupdate=db.func.current_timestamp())


class Payments(db.Model):
    __tablename__ = 'Payments'
    paymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paymentStatus = db.Column(Enum('completed', 'pending', 'failed', 'none'))
    paymentPerMonth = db.Column(db.String(20))
    financeLoanAmount = db.Column(db.String(20))
    loanRatePercentage = db.Column(db.String(20))
    valuePaid = db.Column(db.String(20))
    valueToPay = db.Column(db.String(20))
    initialPurchase = db.Column(db.TIMESTAMP)
    lastPayment = db.Column(db.TIMESTAMP)
    creditScore = db.Column(db.String(3))
    income = db.Column(db.String(20))
    paymentType = db.Column(Enum('check', 'card', 'none'))
    servicePurchased = db.Column(Enum('Vehicle Purchase/Payment', 'Vehicle Purchase'))
    cardNumber = db.Column(db.TEXT)
    expirationDate = db.Column(db.TEXT)
    CVV = db.Column(db.TEXT)
    routingNumber = db.Column(db.TEXT)
    bankAcctNumber = db.Column(db.TEXT)
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'))


class Purchases(db.Model):
    __tablename__ = 'Purchases'
    purchaseID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paymentID = db.Column(db.Integer, ForeignKey('payments.paymentID'))
    VIN_carID = db.Column(db.String(17), ForeignKey('cars.VIN_carID'))
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'))
    paymentType = db.Column(db.Enum('MSRP', 'BID'))
    bidValue = db.Column(db.String(20))
    bidStatus = db.Column(db.Enum('Confirmed', 'Denied', 'Processing'))
    confirmationNumber = db.Column(db.String(13))


class Addons(db.Model):
    __tablename__ = 'Addons'
    itemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemName = db.Column(db.String(100))
    totalCost = db.Column(db.DECIMAL(10, 2))


class MemberAuditLog(db.Model):
    __tablename__ = 'MemberAuditLogs'
    logID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('member.memberID'))
    event_description = db.Column(db.TEXT)
    event_timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())


class EmployeeAuditLog(db.Model):
    __tablename__ = 'EmployeeAuditLogs'
    logID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employeeID = db.Column(db.Integer, ForeignKey('employee.employeeID'))
    event_description = db.Column(db.TEXT)
    event_timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
