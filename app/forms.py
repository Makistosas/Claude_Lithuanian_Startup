"""
SąskaitaPro Forms
WTForms definitions
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField,
    SelectField, DecimalField, IntegerField, DateField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional, NumberRange, Regexp
)


# Authentication Forms
class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('El. paštas', validators=[
        DataRequired(message='Įveskite el. pašto adresą'),
        Email(message='Neteisingas el. pašto formatas')
    ])
    password = PasswordField('Slaptažodis', validators=[
        DataRequired(message='Įveskite slaptažodį')
    ])
    remember_me = BooleanField('Prisiminti mane')


class RegistrationForm(FlaskForm):
    """Registration form"""
    email = StringField('El. paštas', validators=[
        DataRequired(message='Įveskite el. pašto adresą'),
        Email(message='Neteisingas el. pašto formatas'),
        Length(max=120)
    ])
    password = PasswordField('Slaptažodis', validators=[
        DataRequired(message='Įveskite slaptažodį'),
        Length(min=8, message='Slaptažodis turi būti bent 8 simbolių')
    ])
    confirm_password = PasswordField('Pakartokite slaptažodį', validators=[
        DataRequired(message='Pakartokite slaptažodį'),
        EqualTo('password', message='Slaptažodžiai nesutampa')
    ])
    first_name = StringField('Vardas', validators=[
        DataRequired(message='Įveskite vardą'),
        Length(max=50)
    ])
    last_name = StringField('Pavardė', validators=[
        DataRequired(message='Įveskite pavardę'),
        Length(max=50)
    ])
    phone = StringField('Telefonas', validators=[
        Optional(),
        Length(max=20)
    ])


class ForgotPasswordForm(FlaskForm):
    """Forgot password form"""
    email = StringField('El. paštas', validators=[
        DataRequired(message='Įveskite el. pašto adresą'),
        Email(message='Neteisingas el. pašto formatas')
    ])


class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('Naujas slaptažodis', validators=[
        DataRequired(message='Įveskite slaptažodį'),
        Length(min=8, message='Slaptažodis turi būti bent 8 simbolių')
    ])
    confirm_password = PasswordField('Pakartokite slaptažodį', validators=[
        DataRequired(message='Pakartokite slaptažodį'),
        EqualTo('password', message='Slaptažodžiai nesutampa')
    ])


# Company/Settings Forms
class CompanyForm(FlaskForm):
    """Company profile form"""
    name = StringField('Įmonės pavadinimas', validators=[
        DataRequired(message='Įveskite pavadinimą'),
        Length(max=200)
    ])
    legal_name = StringField('Oficialus pavadinimas', validators=[
        Optional(),
        Length(max=200)
    ])
    company_code = StringField('Įmonės kodas', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^\d*$', message='Įmonės kodas turi būti skaičiai')
    ])
    vat_code = StringField('PVM mokėtojo kodas', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^(LT)?\d*$', message='PVM kodas turi prasidėti LT ir turėti skaičius')
    ])
    registration_address = StringField('Registracijos adresas', validators=[
        Optional(),
        Length(max=300)
    ])
    business_address = StringField('Buveinės adresas', validators=[
        Optional(),
        Length(max=300)
    ])
    city = StringField('Miestas', validators=[
        Optional(),
        Length(max=100)
    ])
    postal_code = StringField('Pašto kodas', validators=[
        Optional(),
        Length(max=10)
    ])
    country = StringField('Šalis', validators=[
        Optional(),
        Length(max=50)
    ])
    email = StringField('El. paštas', validators=[
        Optional(),
        Email(message='Neteisingas el. pašto formatas'),
        Length(max=120)
    ])
    phone = StringField('Telefonas', validators=[
        Optional(),
        Length(max=20)
    ])
    website = StringField('Svetainė', validators=[
        Optional(),
        Length(max=200)
    ])
    bank_name = StringField('Banko pavadinimas', validators=[
        Optional(),
        Length(max=100)
    ])
    bank_account = StringField('Banko sąskaita (IBAN)', validators=[
        Optional(),
        Length(max=30),
        Regexp(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$|^$',
               message='Neteisingas IBAN formatas')
    ])
    bank_swift = StringField('SWIFT/BIC kodas', validators=[
        Optional(),
        Length(max=11)
    ])
    logo = FileField('Logotipas', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Tik paveikslėliai leidžiami')
    ])


class UserProfileForm(FlaskForm):
    """User profile form"""
    email = StringField('El. paštas', validators=[
        DataRequired(message='Įveskite el. pašto adresą'),
        Email(message='Neteisingas el. pašto formatas')
    ])
    first_name = StringField('Vardas', validators=[
        DataRequired(message='Įveskite vardą'),
        Length(max=50)
    ])
    last_name = StringField('Pavardė', validators=[
        DataRequired(message='Įveskite pavardę'),
        Length(max=50)
    ])
    phone = StringField('Telefonas', validators=[
        Optional(),
        Length(max=20)
    ])


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Dabartinis slaptažodis', validators=[
        DataRequired(message='Įveskite dabartinį slaptažodį')
    ])
    new_password = PasswordField('Naujas slaptažodis', validators=[
        DataRequired(message='Įveskite naują slaptažodį'),
        Length(min=8, message='Slaptažodis turi būti bent 8 simbolių')
    ])
    confirm_password = PasswordField('Pakartokite slaptažodį', validators=[
        DataRequired(message='Pakartokite slaptažodį'),
        EqualTo('new_password', message='Slaptažodžiai nesutampa')
    ])


# Client Forms
class ClientForm(FlaskForm):
    """Client form"""
    name = StringField('Pavadinimas', validators=[
        DataRequired(message='Įveskite pavadinimą'),
        Length(max=200)
    ])
    legal_name = StringField('Oficialus pavadinimas', validators=[
        Optional(),
        Length(max=200)
    ])
    client_type = SelectField('Tipas', choices=[
        ('company', 'Įmonė'),
        ('individual', 'Fizinis asmuo')
    ])
    company_code = StringField('Įmonės kodas', validators=[
        Optional(),
        Length(max=20)
    ])
    vat_code = StringField('PVM kodas', validators=[
        Optional(),
        Length(max=20)
    ])
    contact_person = StringField('Kontaktinis asmuo', validators=[
        Optional(),
        Length(max=100)
    ])
    email = StringField('El. paštas', validators=[
        Optional(),
        Email(message='Neteisingas el. pašto formatas'),
        Length(max=120)
    ])
    phone = StringField('Telefonas', validators=[
        Optional(),
        Length(max=20)
    ])
    address = StringField('Adresas', validators=[
        Optional(),
        Length(max=300)
    ])
    city = StringField('Miestas', validators=[
        Optional(),
        Length(max=100)
    ])
    postal_code = StringField('Pašto kodas', validators=[
        Optional(),
        Length(max=10)
    ])
    country = StringField('Šalis', validators=[
        Optional(),
        Length(max=50)
    ])
    notes = TextAreaField('Pastabos', validators=[
        Optional()
    ])


# Product Forms
class ProductForm(FlaskForm):
    """Product/Service form"""
    name = StringField('Pavadinimas', validators=[
        DataRequired(message='Įveskite pavadinimą'),
        Length(max=200)
    ])
    description = TextAreaField('Aprašymas', validators=[
        Optional()
    ])
    sku = StringField('Kodas (SKU)', validators=[
        Optional(),
        Length(max=50)
    ])
    product_type = SelectField('Tipas', choices=[
        ('service', 'Paslauga'),
        ('product', 'Prekė')
    ])
    unit_price = DecimalField('Kaina', validators=[
        DataRequired(message='Įveskite kainą'),
        NumberRange(min=0, message='Kaina negali būti neigiama')
    ], places=2)
    unit = SelectField('Matavimo vienetas', choices=[
        ('vnt.', 'vnt. (vienetai)'),
        ('val.', 'val. (valandos)'),
        ('d.', 'd. (dienos)'),
        ('mėn.', 'mėn. (mėnesiai)'),
        ('m', 'm (metrai)'),
        ('m²', 'm² (kv. metrai)'),
        ('kg', 'kg (kilogramai)'),
        ('l', 'l (litrai)'),
        ('kompl.', 'kompl. (komplektai)')
    ])
    vat_rate = SelectField('PVM tarifas', choices=[
        (21, '21% (standartinis)'),
        (9, '9% (sumažintas)'),
        (5, '5% (labai sumažintas)'),
        (0, '0% (neapmokestinama)')
    ], coerce=int)


# Invoice Forms
class InvoiceForm(FlaskForm):
    """Invoice form"""
    client_id = SelectField('Klientas', validators=[
        DataRequired(message='Pasirinkite klientą')
    ], coerce=int)
    invoice_date = DateField('Sąskaitos data', validators=[
        DataRequired(message='Pasirinkite datą')
    ])
    notes = TextAreaField('Pastabos sąskaitoje', validators=[
        Optional()
    ])


class InvoiceItemForm(FlaskForm):
    """Invoice item form"""
    description = StringField('Aprašymas', validators=[
        DataRequired(message='Įveskite aprašymą'),
        Length(max=500)
    ])
    quantity = DecimalField('Kiekis', validators=[
        DataRequired(message='Įveskite kiekį'),
        NumberRange(min=0.01, message='Kiekis turi būti teigiamas')
    ], places=2, default=1)
    unit = StringField('Vienetas', validators=[
        Optional(),
        Length(max=20)
    ], default='vnt.')
    unit_price = DecimalField('Kaina', validators=[
        DataRequired(message='Įveskite kainą'),
        NumberRange(min=0, message='Kaina negali būti neigiama')
    ], places=2)
    vat_rate = SelectField('PVM', choices=[
        (21, '21%'),
        (9, '9%'),
        (5, '5%'),
        (0, '0%')
    ], coerce=int, default=21)
