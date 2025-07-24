# app/auth/forms.py
"""
Formularios para autenticación de usuarios.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""
    
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es obligatorio'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    """Formulario de registro de usuarios."""
    
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es obligatorio'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
    ])
    
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    password2 = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='Confirma tu contraseña'),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    
    submit = SubmitField('Registrarse')
    
    def validate_username(self, username):
        """Validar que el usuario no exista."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este usuario ya existe. Elige otro.')
    
    def validate_password2(self, password2):
        """Validar que las contraseñas coincidan."""
        if self.password.data != password2.data:
            raise ValidationError('Las contraseñas no coinciden.')