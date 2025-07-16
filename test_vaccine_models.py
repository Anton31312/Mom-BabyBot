"""
Простой скрипт для тестирования моделей вакцин.
"""

from datetime import datetime, timedelta
from botapp.models import db_manager, Base, User
from botapp.models_child import Child
from botapp.models_vaccine import Vaccine, ChildVaccine
from botapp.utils.populate_vaccines import populate_standard_vaccines

def test_vaccine_models():
    """Тестирует модели вакцин."""
    print("Начало тестирования моделей вакцин...")
    
    # Создаем таблицы, если они еще не существуют
    db_manager.create_tables()
    
    # Получаем сессию
    session = db_manager.get_session()
    
    try:
        # Создаем тестовую вакцину
        print("Создание тестовой вакцины...")
        vaccine = Vaccine(
            name='Тестовая вакцина',
            description='Описание тестовой вакцины',
            recommended_age='6 месяцев',
            is_mandatory=True
        )
        session.add(vaccine)
        session.commit()
        
        # Проверяем, что вакцина была создана
        saved_vaccine = session.query(Vaccine).filter_by(id=vaccine.id).first()
        print(f"Вакцина создана: {saved_vaccine}")
        
        # Создаем тестового пользователя и ребенка
        print("Создание тестового пользователя и ребенка...")
        user = User(
            telegram_id=999999,
            username='test_user',
            first_name='Test',
            last_name='User'
        )
        session.add(user)
        session.commit()
        
        child = Child(
            user_id=user.id,
            name='Test Child',
            birth_date=datetime.utcnow() - timedelta(days=180)
        )
        session.add(child)
        session.commit()
        
        # Создаем запись о прививке
        print("Создание записи о прививке...")
        child_vaccine = ChildVaccine(
            child_id=child.id,
            vaccine_id=vaccine.id,
            date=datetime.utcnow(),
            is_completed=True,
            notes='Тестовая запись о прививке'
        )
        session.add(child_vaccine)
        session.commit()
        
        # Проверяем, что запись о прививке была создана
        saved_child_vaccine = session.query(ChildVaccine).filter_by(id=child_vaccine.id).first()
        print(f"Запись о прививке создана: {saved_child_vaccine}")
        
        # Проверяем связи
        session.refresh(child)
        print(f"Количество прививок у ребенка: {len(child.vaccines)}")
        
        # Удаляем тестовые данные
        print("Удаление тестовых данных...")
        session.delete(child_vaccine)
        session.delete(vaccine)
        session.delete(child)
        session.delete(user)
        session.commit()
        
        # Заполняем базу данных стандартными вакцинами
        print("Заполнение базы данных стандартными вакцинами...")
        count = populate_standard_vaccines()
        print(f"Добавлено {count} стандартных вакцин.")
        
        # Проверяем, что вакцины были добавлены
        vaccines_count = session.query(Vaccine).count()
        print(f"Всего вакцин в базе данных: {vaccines_count}")
        
        print("Тестирование завершено успешно!")
        return True
    
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        session.rollback()
        return False
    
    finally:
        db_manager.close_session(session)

if __name__ == "__main__":
    test_vaccine_models()