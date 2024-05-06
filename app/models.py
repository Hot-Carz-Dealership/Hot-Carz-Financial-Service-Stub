# app/models.py

from . import db
from sqlalchemy import Enum, ForeignKey


# Defined SQLAlchemy models to represent database tables

class Member(db.Model):
    # Member table model
    __tablename__ = 'Member'
    memberID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(20))
    state = db.Column(db.String(2))
    zipcode = db.Column(db.String(5))
    join_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Define relationship with MemberSensitiveInfo
    sensitive_info = db.relationship('MemberSensitiveInfo', back_populates='member')


class CarVINs(db.Model):
    __tablename__ = 'CarVINs'
    itemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    VIN_carID = db.Column(db.String(17), unique=True)
    purchase_status = db.Column(Enum('Dealership - Not Purchased', 'Dealership - Purchased', 'Outside Dealership'))
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))


class CarInfo(db.Model):
    # cars table model
    __tablename__ = 'CarInfo'
    itemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    VIN_carID = db.Column(db.String(17), ForeignKey('CarVINs.VIN_carID'))
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
    status = db.Column(Enum('new', 'sold', 'low-mileage', 'being-watched', 'Outside Dealership'))
    price = db.Column(db.DECIMAL(10, 2))


class TestDrive(db.Model):
    # TestDrive table model
    __tablename__ = 'TestDrive'
    testdrive_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    VIN_carID = db.Column(db.String(17), ForeignKey('CarVINs.VIN_carID'))
    appointment_date = db.Column(db.TIMESTAMP)
    confirmation = db.Column(Enum('Confirmed', 'Denied', 'Cancelled', 'Awaiting Confirmation'))


class Services(db.Model):
    __tablename__ = 'Services'
    serviceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_name = db.Column(db.String(255))
    price = db.Column(db.DECIMAL(10, 2))



class ServiceAppointment(db.Model):
    # ServiceAppointment table model
    __tablename__ = 'ServiceAppointment'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    VIN_carID = db.Column(db.String(17), ForeignKey('CarVINs.VIN_carID'))  # new for service Appointments
    serviceID = db.Column(db.Integer, ForeignKey('Services.serviceID'))
    appointment_date = db.Column(db.DATE)
    comments = db.Column(db.TEXT)
    status = db.Column(Enum('Scheduled', 'Done', 'Cancelled', 'Pending Confirmation'))
    last_modified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())


class ServiceAppointmentEmployeeAssignments(db.Model):
    __tablename__ = 'ServiceAppointmentEmployeeAssignments'
    assignmentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_id = db.Column(db.Integer, ForeignKey('ServiceAppointment.appointment_id'))
    employeeID = db.Column(db.Integer, ForeignKey('Employee.employeeID'))


class Employee(db.Model):
    # Employee table model
    __tablename__ = 'Employee'
    employeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    city = db.Column(db.String(20))
    state = db.Column(db.String(2))
    zipcode = db.Column(db.String(5))
    employeeType = db.Column(Enum('superAdmin', 'Manager', 'Technician'))


class EmployeeSensitiveInfo(db.Model):
    # EmployeeSensitiveInfo table model
    __tablename__ = 'EmployeeSensitiveInfo'
    sensitiveID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employeeID = db.Column(db.Integer, ForeignKey('Employee.employeeID'))
    password = db.Column(db.String(255))
    SSN = db.Column(db.String(255), unique=True)
    driverID = db.Column(db.String(255), unique=True)
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
    lastModified = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(),
                             onupdate=db.func.current_timestamp())
    # Define relationship with Member
    member = db.relationship('Member', back_populates='sensitive_info')


class Financing(db.Model):
    # Financing table model
    __tablename__ = 'Financing'
    financingID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    VIN_carID = db.Column(db.String(17), db.ForeignKey('CarInfo.VIN_carID'))
    income = db.Column(db.Integer)
    credit_score = db.Column(db.Integer)
    loan_total = db.Column(db.Integer)
    down_payment = db.Column(db.Integer)
    percentage = db.Column(db.Integer)
    monthly_payment_sum = db.Column(db.Integer)
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
    routingNumber = db.Column(db.TEXT)
    bankAcctNumber = db.Column(db.TEXT)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    financingID = db.Column(db.Integer, ForeignKey('Financing.financingID'))


class Bids(db.Model):
    # Bids table model
    __tablename__ = 'Bids'
    bidID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    VIN_carID = db.Column(db.String(17), db.ForeignKey('CarInfo.VIN_carID')) #Bids Should be attached to some vehicle
    bidValue = db.Column(db.DECIMAL(10, 2))
    bidStatus = db.Column(Enum('Confirmed', 'Denied', 'Processing', 'None', 'Member Processing'))
    bidTimestamp = db.Column(db.TIMESTAMP)
    last_updated_by = db.Column(db.Integer, ForeignKey('Employee.employeeID'))


class Purchases(db.Model):
    # Purchases table model
    __tablename__ = 'Purchases'
    purchaseID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bidID = db.Column(db.Integer, ForeignKey('Bids.bidID'))
    VIN_carID = db.Column(db.String(17), ForeignKey('CarVINs.VIN_carID'))
    memberID = db.Column(db.Integer, ForeignKey('Member.memberID'))
    addon_ID = db.Column(db.Integer)
    serviceID = db.Column(db.Integer)
    confirmationNumber = db.Column(db.String(13), unique=True)
    purchaseType = db.Column(Enum('Vehicle/Add-on Purchase', 'Vehicle/Add-on Continuing Payment', 'Service Payment'))
    purchaseDate = db.Column(db.TIMESTAMP)
    signature = db.Column(Enum('Yes', 'No', 'ONLYCUSTOMER'))



class Addons(db.Model):
    # Addons table model
    __tablename__ = 'Addons'
    itemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemName = db.Column(db.String(100))
    totalCost = db.Column(db.DECIMAL(10, 2))


class CheckoutCart(db.Model):
    # CheckoutCart table model
    __tablename__ = 'CheckoutCart'
    
    cart_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, db.ForeignKey('Member.memberID'), nullable=False)
    VIN_carID = db.Column(db.String(45), db.ForeignKey('CarInfo.VIN_carID'))
    addon_ID = db.Column(db.Integer, db.ForeignKey('Addons.itemID'))
    serviceID = db.Column(db.Integer, db.ForeignKey('Services.serviceID'))
    item_name = db.Column(db.String(120), nullable=False)
    item_price = db.Column(db.DECIMAL(10, 2), nullable=False)
    financed_amount = db.Column(db.DECIMAL(10, 2), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp(),
                          onupdate=db.func.current_timestamp())

class Warranty(db.Model):
    # Warranty table model
    __tablename__ = 'Warranty'
    
    Warranty_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    VIN_carID = db.Column(db.String(17))# there should be fk here but idk why it didnt work
    addon_ID = db.Column(db.Integer, db.ForeignKey('Addons.itemID'))
    # memberID = db.Column(db.Integer, db.ForeignKey('Member.memberID'), nullable=False)


class WarrantyService(db.Model):
    # WarrantyService table model
    __tablename__ = 'WarrantyService'
    
    addon_ID = db.Column(db.Integer, db.ForeignKey('Addons.itemID'),primary_key=True)
    serviceID = db.Column(db.Integer, db.ForeignKey('Services.serviceID'))
    
class OrderHistory(db.Model):
    # OrderHistory table model
    __tablename__ = 'OrderHistory'
    
    order_item_ID =  db.Column(db.Integer, primary_key=True, autoincrement=True)
    memberID = db.Column(db.Integer, db.ForeignKey('Member.memberID') )
    item_name = db.Column(db.String(120))
    item_price = db.Column(db.DECIMAL(10, 2))
    financed_amount = db.Column(db.DECIMAL(10, 2))
    confirmationNumber = db.Column(db.String(13))
    purchaseDate = db.Column(db.TIMESTAMP)