"""
Тесты для моделей календаря прививок.

Этот модуль содержит тесты для моделей Vaccine и ChildVaccine.
"""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from botapp.models import Base, User
from botapp.models_child import Child
from botapp.models_vaccine import Vaccine, ChildVaccine


class TestVaccineModels(unittest.TestCase):
    """Тестовые случаи для моделей календаря прививок."""
    
    def setUp(self):
        """Настройка тестовой базы данных и сессии."""
        # Создаем базу данных SQLite в памяти для тестирования
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        
        # Создаем сессию
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Создаем тестового пользователя
        self.test_user = User(
            telegram_id=123456789,
            username='test_user',
            first_name='Test',
            last_name='User',
            is_pregnant=True,
            pregnancy_week=30
        )
        self.session.add(self.test_user)
        
        # Создаем тестового ребенка
        self.test_child = Child(
            user_id=1,  # ID будет 1 после коммита
            name='Test Child',
            birth_date=datetime.utcnow() - timedelta(days=180),  # 6 месяцев
            gender='female'
        )
        self.session.add(self.test_child)
        self.session.commit()
    
    def tearDown(self):
        """Очистка после тестов."""
        self.session.close()
        Base.metadata.drop_all(self.engine)
    
    def test_vaccine_model(self):
        """Тест модели Vaccine."""
        # Создаем тестовую вакцину
        vaccine = Vaccine(
            name='БЦЖ',
            description='Вакцина против туберкулеза',
            recommended_age='При рождении',
            is_mandatory=True
        )
        self.session.add(vaccine)
        self.session.commit()
        
        # Проверяем, что вакцина была создана
        saved_vaccine = self.session.query(Vaccine).filter_by(id=vaccine.id).first()
        self.assertIsNotNone(saved_vaccine)
        self.assertEqual(saved_vaccine.name, 'БЦЖ')
        self.assertEqual(saved_vaccine.description, 'Вакцина против туберкулеза')
        self.assertEqual(saved_vaccine.recommended_age, 'При рождении')
        self.assertTrue(saved_vaccine.is_mandatory)
    
    def test_child_vaccine_model(self):
        """Тест модели ChildVaccine."""
        # Создаем тестовую вакцину
        vaccine = Vaccine(
            name='АКДС',
            description='Вакцина против дифтерии, коклюша и столбняка',
            recommended_age='2 месяца',
            is_mandatory=True
        )
        self.session.add(vaccine)
        self.session.commit()
        
        # Создаем запись о прививке для ребенка
        child_vaccine = ChildVaccine(
            child_id=self.test_child.id,
            vaccine_id=vaccine.id,
            date=datetime.utcnow() - timedelta(days=30),
            is_completed=True,
            notes='Перенес хорошо, без побочных эффектов'
        )
        self.session.add(child_vaccine)
        self.session.commit()
        
        # Проверяем, что запись о прививке была создана
        saved_child_vaccine = self.session.query(ChildVaccine).filter_by(id=child_vaccine.id).first()
        self.assertIsNotNone(saved_child_vaccine)
        self.assertEqual(saved_child_vaccine.child_id, self.test_child.id)
        self.assertEqual(saved_child_vaccine.vaccine_id, vaccine.id)
        self.assertTrue(saved_child_vaccine.is_completed)
        self.assertEqual(saved_child_vaccine.notes, 'Перенес хорошо, без побочных эффектов')
        
        # Проверяем связи
        self.assertEqual(saved_child_vaccine.child, self.test_child)
        self.assertEqual(saved_child_vaccine.vaccine, vaccine)
    
    def test_child_vaccine_relationship(self):
        """Тест связи между моделями Child и ChildVaccine."""
        # Создаем несколько вакцин
        vaccines = [
            Vaccine(name='БЦЖ', recommended_age='При рождении', is_mandatory=True),
            Vaccine(name='АКДС', recommended_age='2 месяца', is_mandatory=True),
            Vaccine(name='Полиомиелит', recommended_age='2 месяца', is_mandatory=True)
        ]
        self.session.add_all(vaccines)
        self.session.commit()
        
        # Создаем записи о прививках для ребенка
        child_vaccines = [
            ChildVaccine(
                child_id=self.test_child.id,
                vaccine_id=vaccines[0].id,
                date=datetime.utcnow() - timedelta(days=180),
                is_completed=True
            ),
            ChildVaccine(
                child_id=self.test_child.id,
                vaccine_id=vaccines[1].id,
                date=datetime.utcnow() - timedelta(days=120),
                is_completed=True
            ),
            ChildVaccine(
                child_id=self.test_child.id,
                vaccine_id=vaccines[2].id,
                is_completed=False
            )
        ]
        self.session.add_all(child_vaccines)
        self.session.commit()
        
        # Обновляем ребенка из базы данных
        self.session.refresh(self.test_child)
        
        # Проверяем, что прививки доступны через связь с ребенком
        self.assertEqual(len(self.test_child.vaccines), 3)
        
        # Проверяем, что можно получить выполненные и запланированные прививки
        completed_vaccines = [cv for cv in self.test_child.vaccines if cv.is_completed]
        upcoming_vaccines = [cv for cv in self.test_child.vaccines if not cv.is_completed]
        self.assertEqual(len(completed_vaccines), 2)
        self.assertEqual(len(upcoming_vaccines), 1)
    
    def test_vaccine_child_vaccine_relationship(self):
        """Тест связи между моделями Vaccine и ChildVaccine."""
        # Создаем тестовую вакцину
        vaccine = Vaccine(
            name='Гепатит B',
            description='Вакцина против гепатита B',
            recommended_age='При рождении',
            is_mandatory=True
        )
        self.session.add(vaccine)
        self.session.commit()
        
        # Создаем несколько детей
        children = [
            Child(user_id=self.test_user.id, name='Child 1', birth_date=datetime.utcnow() - timedelta(days=365)),
            Child(user_id=self.test_user.id, name='Child 2', birth_date=datetime.utcnow() - timedelta(days=180))
        ]
        self.session.add_all(children)
        self.session.commit()
        
        # Создаем записи о прививках для разных детей
        child_vaccines = [
            ChildVaccine(child_id=children[0].id, vaccine_id=vaccine.id, is_completed=True),
            ChildVaccine(child_id=children[1].id, vaccine_id=vaccine.id, is_completed=False)
        ]
        self.session.add_all(child_vaccines)
        self.session.commit()
        
        # Обновляем вакцину из базы данных
        self.session.refresh(vaccine)
        
        # Проверяем, что записи о прививках доступны через связь с вакциной
        self.assertEqual(len(vaccine.child_vaccines), 2)
        
        # Проверяем, что можно получить информацию о детях через связь
        self.assertEqual(vaccine.child_vaccines[0].child.name, 'Child 1')
        self.assertEqual(vaccine.child_vaccines[1].child.name, 'Child 2')
    
    def test_cascade_delete(self):
        """Тест каскадного удаления связанных записей."""
        # Создаем тестовую вакцину
        vaccine = Vaccine(name='Тестовая вакцина')
        self.session.add(vaccine)
        self.session.commit()
        
        # Создаем записи о прививках для ребенка
        for i in range(3):
            child_vaccine = ChildVaccine(
                child_id=self.test_child.id,
                vaccine_id=vaccine.id,
                is_completed=(i % 2 == 0)
            )
            self.session.add(child_vaccine)
        self.session.commit()
        
        # Проверяем, что записи о прививках созданы
        child_vaccines_count = self.session.query(ChildVaccine).filter_by(vaccine_id=vaccine.id).count()
        self.assertEqual(child_vaccines_count, 3)
        
        # Удаляем вакцину
        self.session.delete(vaccine)
        self.session.commit()
        
        # Проверяем, что записи о прививках также были удалены
        child_vaccines_count = self.session.query(ChildVaccine).filter_by(vaccine_id=vaccine.id).count()
        self.assertEqual(child_vaccines_count, 0)
        
        # Создаем новую вакцину и записи о прививках
        vaccine = Vaccine(name='Другая тестовая вакцина')
        self.session.add(vaccine)
        self.session.commit()
        
        for i in range(3):
            child_vaccine = ChildVaccine(
                child_id=self.test_child.id,
                vaccine_id=vaccine.id
            )
            self.session.add(child_vaccine)
        self.session.commit()
        
        # Удаляем ребенка
        self.session.delete(self.test_child)
        self.session.commit()
        
        # Проверяем, что записи о прививках для этого ребенка также были удалены
        child_vaccines_count = self.session.query(ChildVaccine).filter_by(child_id=self.test_child.id).count()
        self.assertEqual(child_vaccines_count, 0)


if __name__ == '__main__':
    unittest.main()