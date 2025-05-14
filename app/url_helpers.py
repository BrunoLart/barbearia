from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db, bcrypt
from app.forms import LoginForm, RegistrationForm # AppointmentForm is in appointments_bp
from app.models import User, Service, Appointment # Ensure Appointment is imported if used here
from datetime import datetime

@app.route('/')
@app.route('/index')
def index(): # Login not strictly required for index, but can be added
    return render_template('index.html', title='Página Inicial')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            flash('Login bem-sucedido!', 'success')
            return redirect(next_page)
        else:
            flash('Login sem sucesso. Verifique o email e a senha.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data) # Uses the method from model
        db.session.add(user)
        db.session.commit()
        flash('Parabéns, você agora é um usuário registrado! Por favor, faça o login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registrar', form=form)

@app.route('/services')
def services_page():
    all_services = Service.query.all()
    return render_template('services.html', title='Nossos Serviços', services=all_services)

@app.route('/user/<username>')
@login_required
def user_profile(username):
    user_obj = User.query.filter_by(username=username).first_or_404()
    if user_obj != current_user:
        flash("Você só pode visualizar seu próprio perfil.", "warning")
        # Option: redirect to current_user's profile or just show a limited view / error
        return redirect(url_for('user_profile', username=current_user.username))

    now_utc = datetime.utcnow()
    # Assuming Appointment model is imported and user_obj.appointments relationship is set up
    future_appointments_query = Appointment.query.with_parent(user_obj).filter(Appointment.appointment_time >= now_utc).order_by(Appointment.appointment_time.asc())
    
    return render_template('user_profile.html', 
                           title=f'Perfil de {user_obj.username}', 
                           user=user_obj, 
                           future_appointments=future_appointments_query.all())

