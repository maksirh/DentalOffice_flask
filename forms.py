from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, PasswordField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, EqualTo, Email
from flask_wtf.file import FileAllowed


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3,64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm  = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit   = SubmitField('Зареєструватись')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Увійти')

class AppointmentForm(FlaskForm):
    name = StringField('Ім’я', validators=[DataRequired()])
    age = IntegerField('Вік', validators=[DataRequired()])
    phoneNumber = StringField('Телефон', validators=[DataRequired()])
    reason = TextAreaField('Причина запису', validators=[DataRequired()])
    dentist = SelectField('Стоматолог', coerce=int, validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Записатися')


class ReviewForm(FlaskForm):
    review = TextAreaField('Ваш відгук', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Надіслати відгук')

class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField('Підтвердити видалення')

class DentistForm(FlaskForm):
    name = StringField('Ім\'я', validators=[DataRequired(), Length(max=100)])
    age = IntegerField('Вік', validators=[DataRequired(), NumberRange(18, 100)])
    experience = IntegerField('Досвід (років)', validators=[DataRequired(), NumberRange(0,80)])
    phoneNumber = StringField('Телефон', validators=[DataRequired(), Length(max=20)])
    image = FileField('Фото', validators=[FileAllowed(['jpg','png','jpeg'], 'Тільки зображення!')])
    submit = SubmitField('Зберегти')

class PatientForm(FlaskForm):
    name = StringField('Ім\'я', validators=[DataRequired(), Length(max=100)])
    age = IntegerField('Вік', validators=[DataRequired(), NumberRange(0,150)])
    phoneNumber = StringField('Телефон', validators=[DataRequired(), Length(max=20)])
    image = FileField('Фото', validators=[FileAllowed(['jpg','png','jpeg'], 'Тільки зображення!')])
    submit = SubmitField('Зберегти')

class ServiceForm(FlaskForm):
    name = StringField('Назва', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Опис', validators=[DataRequired()])
    image = FileField('Фото', validators=[FileAllowed(['jpg','png','jpeg'], 'Тільки зображення!')])
    submit = SubmitField('Зберегти')