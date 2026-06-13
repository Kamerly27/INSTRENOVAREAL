from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from models.usuario import Usuario


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        correo = request.form.get('correo')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and check_password_hash(usuario.password, password):

            login_user(usuario)

            if usuario.rol == 'admin':
                return redirect(url_for('admin.dashboard'))

            if usuario.rol == 'docente':
                return redirect(url_for('docente.dashboard'))

            if usuario.rol == 'estudiante':
                return redirect(url_for('estudiante.dashboard'))

        flash('Correo o contraseña incorrectos')

        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(url_for('auth.login'))