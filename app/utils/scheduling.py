from datetime import datetime, timedelta, time

# Horários de funcionamento e duração do slot
BUSINESS_HOURS = {
    "monday": [("08:00", "12:00"), ("13:00", "19:00")],
    "tuesday": [("08:00", "12:00"), ("13:00", "19:00")],
    "wednesday": [("08:00", "12:00"), ("13:00", "19:00")],
    "thursday": [("08:00", "12:00"), ("13:00", "19:00")],
    "friday": [("08:00", "12:00"), ("13:00", "19:00")],
    "saturday": [("08:00", "16:00")],
    "sunday": [] # Fechado aos domingos
}
SLOT_DURATION_MINUTES = 30

def get_day_name(date_obj):
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return days[date_obj.weekday()]

def is_within_business_hours(dt_object):
    day_name = get_day_name(dt_object.date())
    time_object = dt_object.time()

    if day_name not in BUSINESS_HOURS or not BUSINESS_HOURS[day_name]:
        return False # Dia não está configurado ou está fechado

    for start_str, end_str in BUSINESS_HOURS[day_name]:
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        if start_time <= time_object < end_time:
            return True
    return False

def get_available_slots(date_str, existing_appointments_for_day, service_duration_minutes):
    """
    Gera slots disponíveis para um determinado dia, considerando os horários de funcionamento,
    duração do serviço e agendamentos existentes.
    existing_appointments_for_day: lista de objetos datetime dos horários de início dos agendamentos existentes.
    service_duration_minutes: duração do serviço em minutos.
    """
    available_slots = []
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return [] # Data inválida

    day_name = get_day_name(target_date)
    if day_name not in BUSINESS_HOURS or not BUSINESS_HOURS[day_name]:
        return [] # Dia não está configurado ou está fechado

    for start_period_str, end_period_str in BUSINESS_HOURS[day_name]:
        current_time = datetime.combine(target_date, datetime.strptime(start_period_str, "%H:%M").time())
        end_period_time = datetime.combine(target_date, datetime.strptime(end_period_str, "%H:%M").time())

        while current_time < end_period_time:
            slot_start_time = current_time
            slot_end_time = current_time + timedelta(minutes=service_duration_minutes)

            # Verifica se o slot termina dentro do período de funcionamento
            if slot_end_time.time() > end_period_time.time() and slot_end_time.date() == target_date:
                 # Se o slot termina depois do fim do período mas no mesmo dia, não é válido
                 if slot_end_time.time() > datetime.strptime(end_period_str, "%H:%M").time():
                    break
            elif slot_end_time.date() > target_date:
                # Se o slot termina no dia seguinte, não é válido
                break
            
            # Verifica se o slot completo está dentro de um período de funcionamento contínuo
            # (Ex: não começar antes do almoço e terminar depois)
            is_slot_valid_within_period = False
            if is_within_business_hours(slot_start_time) and is_within_business_hours(slot_end_time - timedelta(minutes=1)):
                # Checa se o slot cruza o horário de almoço para dias de semana
                if day_name in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                    lunch_start_dt = datetime.combine(target_date, time(12,0))
                    lunch_end_dt = datetime.combine(target_date, time(13,0))
                    if not (slot_end_time <= lunch_start_dt or slot_start_time >= lunch_end_dt):
                        is_slot_valid_within_period = False
                    else:
                        is_slot_valid_within_period = True
                else:
                    is_slot_valid_within_period = True
            
            if not is_slot_valid_within_period:
                current_time += timedelta(minutes=SLOT_DURATION_MINUTES) # Avança para o próximo slot base
                continue

            # Verificar sobreposição com agendamentos existentes
            is_overlapping = False
            for existing_appointment_start in existing_appointments_for_day:
                # Assumindo que existing_appointments_for_day contém tuplas (start_time, duration_minutes)
                existing_start_dt = existing_appointment_start[0]
                existing_duration = existing_appointment_start[1]
                existing_end_dt = existing_start_dt + timedelta(minutes=existing_duration)
                
                # Verifica sobreposição: (StartA < EndB) and (EndA > StartB)
                if (slot_start_time < existing_end_dt and slot_end_time > existing_start_dt):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                available_slots.append(slot_start_time.strftime("%H:%M"))
            
            current_time += timedelta(minutes=SLOT_DURATION_MINUTES) # Avança para o próximo slot base de 30 min

    return sorted(list(set(available_slots))) # Remove duplicados e ordena

# Exemplo de como usar (para teste)
if __name__ == "__main__":
    # Simula agendamentos existentes para 2025-10-27 (Segunda)
    # (datetime_object, duration_in_minutes)
    existing_today = [
        (datetime(2025, 10, 27, 10, 0), 60), # Das 10:00 às 11:00
        (datetime(2025, 10, 27, 14, 30), 30)  # Das 14:30 às 15:00
    ]
    service_duration = 30 # Serviço de 30 minutos
    print(f"Slots para serviço de {service_duration}min em 2025-10-27 (Segunda):")
    print(get_available_slots("2025-10-27", existing_today, service_duration))

    service_duration_long = 90 # Serviço de 90 minutos
    print(f"\nSlots para serviço de {service_duration_long}min em 2025-10-27 (Segunda):")
    print(get_available_slots("2025-10-27", existing_today, service_duration_long))

    # Teste para Sábado
    existing_saturday = [
        (datetime(2025, 10, 25, 9, 0), 60) # Das 09:00 às 10:00
    ]
    print(f"\nSlots para serviço de {service_duration}min em 2025-10-25 (Sábado):")
    print(get_available_slots("2025-10-25", existing_saturday, service_duration))

    # Teste para Domingo
    print(f"\nSlots para serviço de {service_duration}min em 2025-10-26 (Domingo):")
    print(get_available_slots("2025-10-26", [], service_duration))

    # Teste para horário de almoço
    print(f"\nSlots para serviço de {service_duration}min em 2025-10-27 (Segunda) perto do almoço:")
    existing_near_lunch = [(datetime(2025, 10, 27, 11, 0), 30)]
    print(get_available_slots("2025-10-27", existing_near_lunch, service_duration))

