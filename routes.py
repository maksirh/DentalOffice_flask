from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user, login_user, logout_user
from models import db, User, Dentist, Patient, Appointment, Review, Service
from forms import LoginForm, RegistrationForm, AppointmentForm, ReviewForm, ConfirmDeleteForm, ServiceForm
from functools import wraps
import os
from werkzeug.utils import secure_filename
from forms import DentistForm, PatientForm
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message, Mail
from flask import current_app
from sqlalchemy.exc import IntegrityError


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


bp = Blueprint('main', __name__)

# Сторінка адмін: список послуг
@bp.route('/admin/services')
@admin_required
def admin_services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

# Додавання / редагування послуги
@bp.route('/admin/services/new', methods=['GET','POST'])
@bp.route('/admin/services/edit/<int:service_id>', methods=['GET','POST'])
@admin_required
def admin_edit_service(service_id=None):
    if service_id:
        service = Service.query.get_or_404(service_id)
        form = ServiceForm(obj=service)
    else:
        service = None
        form = ServiceForm()

    if form.validate_on_submit():
        filename = service.image if service else None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads', filename))
        if service:
            form.populate_obj(service)
            service.image = filename
        else:
            service = Service(
                name=form.name.data,
                description=form.description.data,
                image=filename
            )
            db.session.add(service)
        db.session.commit()
        flash('Послугу збережено', 'success')
        return redirect(url_for('main.admin_services'))

    return render_template('admin/service_form.html', form=form, service=service)


@bp.route('/')
def home():
    services = Service.query.all()
    return render_template('home.html', services=services)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Успішний вхід', 'success')
            next_page = request.args.get('next') or url_for('main.home')
            return redirect(next_page)
        flash('Невірний логін або пароль', 'danger')
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви успішно вийшли з системи.', 'info')
    return redirect(url_for('main.home'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Якщо вже авторизований — перенаправляємо на головну
    if current_app.login_manager._load_user() is not None:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data

        # Перевіряємо унікальність
        if User.query.filter_by(username=username).first():
            flash('Користувач з таким іменем вже існує.', 'warning')
        elif User.query.filter_by(email=email).first():
            flash('Користувач з таким email вже зареєстрований.', 'warning')
        else:
            # Створюємо нового користувача
            new_user = User(
                username=username,
                email=email,
                role='user',
                email_confirmed=False
            )
            new_user.set_password(password)
            db.session.add(new_user)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Проблема при створенні користувача. Спробуйте пізніше.', 'danger')
                return render_template('register.html', form=form)

            # Генеруємо токен підтвердження
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps(email, salt='email-confirm')
            confirm_url = url_for('main.confirm_email', token=token, _external=True)

            # Підготовка листа
            msg = Message(
                subject='Підтвердіть вашу реєстрацію',
                recipients=[email],
                body=(
                    f"Привіт, {username}!\n\n"
                    f"Щоб завершити реєстрацію, перейдіть за цим посиланням:\n"
                    f"{confirm_url}\n\n"
                    "Якщо це були не ви — просто проігноруйте цей лист."
                )
            )

            # Відправка через Flask-Mail
            mail = current_app.extensions['mail']
            try:
                mail.send(msg)
            except Exception as e:
                # Якщо лист не пішов — повідомимо, але користувача створено
                flash('Не вдалося надіслати листа підтвердження. Зверніться до підтримки.', 'warning')
                current_app.logger.error(f"Mail send failed: {e}")

            flash('На вашу пошту відправлено листа для підтвердження.', 'info')
            return redirect(url_for('main.login'))

    return render_template('register.html', form=form)



@bp.route('/confirm/<token>')
def confirm_email(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('Термін дії посилання минув.', 'danger')
        return redirect(url_for('main.login'))
    except BadSignature:
        flash('Неправильне або пошкоджене посилання.', 'danger')
        return redirect(url_for('main.register'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.email_confirmed:
        flash('Ваш email уже підтверджено.', 'info')
    else:
        user.email_confirmed = True
        db.session.commit()
        flash('Email успішно підтверджено! Тепер можете увійти.', 'success')

    return redirect(url_for('main.login'))



@bp.route('/appointment', methods=['GET', 'POST'])
def appointment():
    form = AppointmentForm()
    if form.validate_on_submit():
        appt = Appointment(
            user_id=current_user.get_id() if current_user.is_authenticated else None,
            name=form.name.data,
            age=form.age.data,
            phoneNumber=form.phoneNumber.data,
            reason=form.reason.data
        )
        db.session.add(appt)
        db.session.commit()

        msg = Message(
            subject='Ваш запис підтверджено',
            recipients=[form.email.data]  # або current_user.email
        )
        msg.body = f"Ви записані на {appt.date_time}"
        mail = current_app.extensions['mail']
        mail.send(msg)

        flash('Запис створено успішно!', 'success')
        return redirect(url_for('main.home'))
    return render_template('appointment.html', form=form)


@bp.route('/dentists')
def dentists():
    dentists = Dentist.query.all()
    return render_template('dentists.html', dentists=dentists)


@bp.route('/patients')
def patients():
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)


@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@bp.route('/reviews', methods=['GET', 'POST'])
def reviews():
    form = ReviewForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Будь ласка, увійдіть, щоб залишити відгук.', 'warning')
            return redirect(url_for('main.login'))
        new_review = Review(user_id=current_user.id, review=form.review.data)
        db.session.add(new_review)
        db.session.commit()
        flash('Відгук додано', 'success')
        return redirect(url_for('main.reviews'))
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('reviews.html', form=form, reviews=all_reviews)


@bp.route('/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def review_edit(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        abort(403)
    form = ReviewForm(obj=review)
    if form.validate_on_submit():
        review.review = form.review.data
        db.session.commit()
        flash('Відгук оновлено', 'success')
        return redirect(url_for('main.reviews'))
    return render_template('review_edit.html', form=form)


@bp.route('/reviews/delete/<int:review_id>', methods=['GET', 'POST'])
@login_required
def review_delete(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        abort(403)
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        db.session.delete(review)
        db.session.commit()
        flash('Відгук видалено', 'info')
        return redirect(url_for('main.reviews'))
    return render_template('review_confirm_delete.html', form=form, review=review)


# Адмінка: список записів
@bp.route('/admin/appointments')
@admin_required
def admin_appointments():
    appts = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template('admin/appointments.html', appointments=appts)

# Додавання стоматолога
@bp.route('/admin/dentists/new', methods=['GET','POST'])
@admin_required
def admin_new_dentist():
    form = DentistForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            # приклад збереження файлу
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads', filename))
        dent = Dentist(
            name=form.name.data,
            age=form.age.data,
            experience=form.experience.data,
            phoneNumber=form.phoneNumber.data,
            image=filename
        )
        db.session.add(dent)
        db.session.commit()
        flash('Стоматолога додано', 'success')
        return redirect(url_for('main.dentists'))
    return render_template('admin/dentist_form.html', form=form)


@bp.route('/admin/patients/new', methods=['GET','POST'])
@admin_required
def admin_new_patient():
    form = PatientForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join('static/uploads', filename))
        pat = Patient(
            name=form.name.data,
            age=form.age.data,
            phoneNumber=form.phoneNumber.data,
            image=filename
        )
        db.session.add(pat)
        db.session.commit()
        flash('Пацієнта додано', 'success')
        return redirect(url_for('main.admin_patients'))
    return render_template('admin/patient_form.html', form=form)

# Список пацієнтів (для адміна)
@bp.route('/admin/patients')
@admin_required
def admin_patients():
    list_ = Patient.query.all()
    return render_template('admin/patients.html', patients=list_)



@bp.route('/search')
def search():
    query = request.args.get('q', '')
    # TODO: реалізувати логіку пошуку
    return render_template('search_results.html', query=query)


@bp.route('/contacts')
def contacts():
    return render_template('contacts.html')
