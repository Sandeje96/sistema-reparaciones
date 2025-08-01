# app/auth/routes.py
"""
Rutas de autenticación y gestión de usuarios.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User
from app import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Iniciar sesión."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            
            # Redirigir a la página solicitada o al dashboard
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('repairs.index')
            
            flash(f'¡Bienvenido, {user.username}!', 'success')
            return redirect(next_page)
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión."""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registrar nuevo usuario."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('¡Registro exitoso! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar usuario. Inténtalo de nuevo.', 'error')
    
    return render_template('auth/register.html', title='Registrarse', form=form)