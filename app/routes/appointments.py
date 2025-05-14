from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Appointment, Service, User
from app.utils.scheduling import get_available_slots # SLOT_DURATION_MINUTES, BUSINESS_HOURS are not directly used here but in scheduling.py
from app.forms import AppointmentForm # Assuming AppointmentForm is in app.forms
from datetime import datetime, timedelta
import calendar # For getting month details

appointments_bp = Blueprint("appointments", __name__)

@appointments_bp.route("/get_available_slots", methods=["POST"])
@login_required
def available_slots_api():
    data = request.get_json()
    date_str = data.get("date")
    service_id = data.get("service_id")

    if not date_str or not service_id:
        return jsonify({"error": "Missing date or service_id"}), 400

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "Service not found"}), 404

    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    existing_appts_for_day_query = Appointment.query.filter(
        Appointment.appointment_time >= start_of_day,
        Appointment.appointment_time <= end_of_day
    ).all()

    formatted_existing_appointments = []
    for appt in existing_appts_for_day_query:
        appt_service = Service.query.get(appt.service_id)
        if appt_service:
            formatted_existing_appointments.append((appt.appointment_time, appt_service.duration_minutes))

    slots = get_available_slots(date_str, formatted_existing_appointments, service.duration_minutes)
    return jsonify({"available_slots": slots})

@appointments_bp.route("/book", methods=["GET", "POST"])
@login_required
def book_appointment():
    form = AppointmentForm()
    services = Service.query.all()
    if hasattr(form, 'service_id') and hasattr(form.service_id, 'choices'): # Check if form has service_id and it has choices attribute
        form.service_id.choices = [(s.id, s.name) for s in services]
    
    if form.validate_on_submit():
        service_id = form.service_id.data
        date_str = form.date.data.strftime("%Y-%m-%d")
        time_str = form.time.data.strftime("%H:%M")
        
        service = Service.query.get(service_id)
        if not service:
            flash("Selected service not found.", "danger")
            return render_template("book_appointment.html", title="Book Appointment", form=form, services=services)

        try:
            appointment_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return render_template("book_appointment.html", title="Book Appointment", form=form, services=services)

        start_of_day = datetime.combine(appointment_dt.date(), datetime.min.time())
        end_of_day = datetime.combine(appointment_dt.date(), datetime.max.time())
        existing_appts_for_day_query = Appointment.query.filter(
            Appointment.appointment_time >= start_of_day,
            Appointment.appointment_time <= end_of_day
        ).all()
        formatted_existing_appointments = []
        for appt in existing_appts_for_day_query:
            appt_service_model = Service.query.get(appt.service_id) # Renamed to avoid conflict
            if appt_service_model:
                formatted_existing_appointments.append((appt.appointment_time, appt_service_model.duration_minutes))
        
        available_slots_for_service = get_available_slots(date_str, formatted_existing_appointments, service.duration_minutes)

        if time_str not in available_slots_for_service:
            flash("The selected time slot is no longer available or invalid for the chosen service.", "danger")
            return render_template("book_appointment.html", title="Book Appointment", form=form, services=services)

        new_appointment = Appointment(
            user_id=current_user.id,
            service_id=service.id,
            appointment_time=appointment_dt,
            status="Scheduled"
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash(f"Appointment for {service.name} on {date_str} at {time_str} booked successfully!", "success")
        # TODO: Send WhatsApp notification here
        return redirect(url_for("appointments.my_appointments"))

    return render_template("book_appointment.html", title="Book Appointment", form=form, services=services)

@appointments_bp.route("/my_appointments")
@login_required
def my_appointments():
    user_appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.appointment_time.asc()).all()
    return render_template("my_appointments.html", title="My Appointments", appointments=user_appointments)

@appointments_bp.route("/admin/all_appointments") # Basic admin view, needs role check
@login_required
def admin_all_appointments():
    # A real app would have role checking: if not current_user.is_admin:
    #    flash("Access denied.", "danger")
    #    return redirect(url_for("main.index")) 
    all_appts = Appointment.query.order_by(Appointment.appointment_time.asc()).all()
    return render_template("admin_all_appointments.html", title="All Appointments (Admin)", appointments=all_appts)

@appointments_bp.route("/calendar")
@login_required
def appointment_calendar():
    return render_template("calendar.html", title="Appointment Calendar")

@appointments_bp.route("/api/month_appointments", methods=["GET"])
@login_required
def month_appointments_api():
    year_str = request.args.get("year")
    month_str = request.args.get("month")

    if not year_str or not month_str:
        return jsonify({"error": "Year and month parameters are required"}), 400

    try:
        year = int(year_str)
        month = int(month_str)
        if not (1 <= month <= 12):
            raise ValueError("Month out of range")
    except ValueError as e:
        return jsonify({"error": f"Invalid year or month: {e}"}), 400

    # Determine date range for the month
    start_of_month = datetime(year, month, 1)
    # Get the number of days in the month
    num_days_in_month = calendar.monthrange(year, month)[1]
    end_of_month = datetime(year, month, num_days_in_month, 23, 59, 59)

    # Query appointments
    # For admin, show all. For users, show their own. (Simplified for now: show all for testing)
    # TODO: Implement role-based data fetching for calendar
    # For now, let's assume an admin is viewing, or a simplified view for all users.
    # A proper implementation would check current_user.is_admin or similar role.
    
    # query = Appointment.query.filter(
    #     Appointment.appointment_time >= start_of_month,
    #     Appointment.appointment_time <= end_of_month
    # )
    # if not current_user.is_admin: # This requires an is_admin attribute on User model
    #     query = query.filter(Appointment.user_id == current_user.id)
    
    # Simplified: Fetch all appointments for the month for now
    appointments_in_month = Appointment.query.filter(
        Appointment.appointment_time >= start_of_month,
        Appointment.appointment_time <= end_of_month
    ).order_by(Appointment.appointment_time.asc()).all()

    events = []
    for appt in appointments_in_month:
        service_name = appt.service.name if appt.service else "Unknown Service"
        client_name = appt.customer.username if appt.customer else "Unknown Client"
        events.append({
            "id": appt.id,
            "title": f"{service_name} - {client_name}", # Adjust title as needed
            "start": appt.appointment_time.isoformat(), 
            # FullCalendar or other libraries might need an 'end' time too
            # "end": (appt.appointment_time + timedelta(minutes=appt.service.duration_minutes)).isoformat() if appt.service else appt.appointment_time.isoformat(),
            "day": appt.appointment_time.day,
            "time": appt.appointment_time.strftime("%H:%M"),
            "service": service_name,
            "client": client_name,
            "user_id": appt.user_id
        })
    
    return jsonify(events)


