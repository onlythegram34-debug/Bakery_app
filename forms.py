from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, FloatField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class SalesRegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    residence_id = SelectField('Residence', coerce=int, default=0)
    new_residence_name = StringField('New Residence Name')
    new_residence_location = StringField('New Residence Location')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class OrderRequestForm(FlaskForm):
    delivery_date = DateField('Delivery Date', validators=[DataRequired()])
    total_buckets = IntegerField('Number of 5L Buckets', validators=[DataRequired()])
    total_amount = FloatField('Total Amount (R)', validators=[DataRequired()])

class AdminCreateUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
