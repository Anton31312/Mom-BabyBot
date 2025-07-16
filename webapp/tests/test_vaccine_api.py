"""
Тесты для API эндпоинтов календаря прививок.

Этот модуль содержит тесты для API эндпоинтов вакцин и записей о прививках.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from botapp.models import User, db_manager
from botapp.models_child import Child
from botapp.models_vaccine import Vaccine, ChildVaccine


class VaccineAPITestCase(TestCase):
    """Тестовый случай для API эндпоинтов календаря прививок."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Create a test user
        session = db_manager.get_session()
        try:
            self.user = User(
                telegram_id=123456789,
                username='testuser',
                first_name='Test',
                last_name='User'
            )
            session.add(self.user)
            session.commit()
            session.refresh(self.user)
            
            # Create a test child
            self.child = Child(
                user_id=self.user.id,
                name='Test Child',
                birth_date=datetime.now() - timedelta(days=365),  # 1 year old
                gender='male'
            )
            session.add(self.child)
            session.commit()
            session.refresh(self.child)
            
            # Create test vaccines
            self.vaccine1 = Vaccine(
                name='Test Vaccine 1',
                description='Test vaccine description 1',
                recommended_age='2 months',
                is_mandatory=True
            )
            self.vaccine2 = Vaccine(
                name='Test Vaccine 2',
                description='Test vaccine description 2',
                recommended_age='1 year',
                is_mandatory=False
            )
            session.add_all([self.vaccine1, self.vaccine2])
            session.commit()
            session.refresh(self.vaccine1)
            session.refresh(self.vaccine2)
            
            # Create a test child vaccine record
            self.child_vaccine = ChildVaccine(
                child_id=self.child.id,
                vaccine_id=self.vaccine1.id,
                date=datetime.now() - timedelta(days=30),
                is_completed=True,
                notes='Test vaccine record'
            )
            session.add(self.child_vaccine)
            session.commit()
            session.refresh(self.child_vaccine)
        finally:
            db_manager.close_session(session)
        
        # Set up test client
        self.client = Client()
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = db_manager.get_session()
        try:
            # Delete test child vaccine record
            child_vaccine = session.query(ChildVaccine).filter_by(id=self.child_vaccine.id).first()
            if child_vaccine:
                session.delete(child_vaccine)
            
            # Delete test vaccines
            vaccine1 = session.query(Vaccine).filter_by(id=self.vaccine1.id).first()
            if vaccine1:
                session.delete(vaccine1)
            
            vaccine2 = session.query(Vaccine).filter_by(id=self.vaccine2.id).first()
            if vaccine2:
                session.delete(vaccine2)
            
            # Delete test child
            child = session.query(Child).filter_by(id=self.child.id).first()
            if child:
                session.delete(child)
            
            # Delete test user
            user = session.query(User).filter_by(id=self.user.id).first()
            if user:
                session.delete(user)
            
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_vaccines(self):
        """Тест получения списка всех вакцин."""
        url = '/api/vaccines/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('vaccines', data)
        self.assertGreaterEqual(len(data['vaccines']), 2)  # At least our 2 test vaccines
        
        # Check if our test vaccines are in the list
        vaccine_names = [v['name'] for v in data['vaccines']]
        self.assertIn('Test Vaccine 1', vaccine_names)
        self.assertIn('Test Vaccine 2', vaccine_names)
    
    def test_get_vaccine_detail(self):
        """Тест получения информации о конкретной вакцине."""
        url = f'/api/vaccines/{self.vaccine1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Test Vaccine 1')
        self.assertEqual(data['description'], 'Test vaccine description 1')
        self.assertEqual(data['recommended_age'], '2 months')
        self.assertTrue(data['is_mandatory'])
    
    def test_get_child_vaccines(self):
        """Тест получения всех прививок для ребенка."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('child_vaccines', data)
        self.assertEqual(len(data['child_vaccines']), 1)
        self.assertEqual(data['child_vaccines'][0]['vaccine_name'], 'Test Vaccine 1')
        self.assertTrue(data['child_vaccines'][0]['is_completed'])
    
    def test_create_child_vaccine(self):
        """Тест создания новой записи о прививке для ребенка."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        data = {
            'vaccine_id': self.vaccine2.id,
            'is_completed': False,
            'notes': 'New vaccine record'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['vaccine_id'], self.vaccine2.id)
        self.assertEqual(response_data['vaccine_name'], 'Test Vaccine 2')
        self.assertFalse(response_data['is_completed'])
        self.assertEqual(response_data['notes'], 'New vaccine record')
        
        # Clean up the created record
        session = db_manager.get_session()
        try:
            child_vaccine = session.query(ChildVaccine).filter_by(id=response_data['id']).first()
            if child_vaccine:
                session.delete(child_vaccine)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_child_vaccine_detail(self):
        """Тест получения конкретной записи о прививке."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/{self.child_vaccine.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['vaccine_id'], self.vaccine1.id)
        self.assertEqual(data['vaccine_name'], 'Test Vaccine 1')
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['notes'], 'Test vaccine record')
    
    def test_update_child_vaccine(self):
        """Тест обновления записи о прививке."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/{self.child_vaccine.id}/'
        data = {
            'notes': 'Updated vaccine record'
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['notes'], 'Updated vaccine record')
        
        # Verify the update in the database
        session = db_manager.get_session()
        try:
            child_vaccine = session.query(ChildVaccine).filter_by(id=self.child_vaccine.id).first()
            self.assertEqual(child_vaccine.notes, 'Updated vaccine record')
        finally:
            db_manager.close_session(session)
    
    def test_delete_child_vaccine(self):
        """Тест удаления записи о прививке."""
        # Create a record to delete
        session = db_manager.get_session()
        try:
            child_vaccine_to_delete = ChildVaccine(
                child_id=self.child.id,
                vaccine_id=self.vaccine2.id,
                date=datetime.now(),
                is_completed=False,
                notes='Vaccine record to delete'
            )
            session.add(child_vaccine_to_delete)
            session.commit()
            session.refresh(child_vaccine_to_delete)
            child_vaccine_id = child_vaccine_to_delete.id
        finally:
            db_manager.close_session(session)
        
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/{child_vaccine_id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Vaccine record deleted successfully')
        
        # Verify the deletion in the database
        session = db_manager.get_session()
        try:
            child_vaccine = session.query(ChildVaccine).filter_by(id=child_vaccine_id).first()
            self.assertIsNone(child_vaccine)
        finally:
            db_manager.close_session(session)
    
    def test_mark_vaccine_completed(self):
        """Тест отметки прививки как выполненной."""
        # Create a record to mark as completed
        session = db_manager.get_session()
        try:
            child_vaccine_to_complete = ChildVaccine(
                child_id=self.child.id,
                vaccine_id=self.vaccine2.id,
                is_completed=False,
                notes='Vaccine to complete'
            )
            session.add(child_vaccine_to_complete)
            session.commit()
            session.refresh(child_vaccine_to_complete)
            child_vaccine_id = child_vaccine_to_complete.id
        finally:
            db_manager.close_session(session)
        
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/{child_vaccine_id}/complete/'
        data = {
            'notes': 'Completed vaccine record'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['is_completed'])
        self.assertEqual(response_data['notes'], 'Completed vaccine record')
        self.assertIsNotNone(response_data['date'])  # Date should be set automatically
        
        # Verify the update in the database
        session = db_manager.get_session()
        try:
            child_vaccine = session.query(ChildVaccine).filter_by(id=child_vaccine_id).first()
            self.assertTrue(child_vaccine.is_completed)
            self.assertEqual(child_vaccine.notes, 'Completed vaccine record')
            self.assertIsNotNone(child_vaccine.date)
            
            # Clean up
            session.delete(child_vaccine)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_vaccine_not_found(self):
        """Тест API-ответа, когда вакцина не найдена."""
        url = '/api/vaccines/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Вакцина не найдена')
    
    def test_child_vaccine_not_found(self):
        """Тест API-ответа, когда запись о прививке не найдена."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Запись о прививке не найдена')
    
    def test_child_does_not_belong_to_user(self):
        """Тест API-ответа, когда ребенок не принадлежит пользователю."""
        # Create another user
        session = db_manager.get_session()
        try:
            other_user = User(
                telegram_id=987654321,
                username='otheruser',
                first_name='Other',
                last_name='User'
            )
            session.add(other_user)
            session.commit()
            session.refresh(other_user)
            
            # Try to access the child's vaccines with the other user
            url = f'/api/users/{other_user.id}/children/{self.child.id}/vaccines/'
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Ребенок не принадлежит этому пользователю')
            
            # Clean up
            session.delete(other_user)
            session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_create_child_vaccine_invalid_vaccine(self):
        """Тест API-ответа при попытке создать запись с несуществующей вакциной."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        data = {
            'vaccine_id': 999999,
            'is_completed': False
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Вакцина не найдена')
    
    def test_create_child_vaccine_missing_vaccine_id(self):
        """Тест API-ответа при попытке создать запись без указания ID вакцины."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/vaccines/'
        data = {
            'is_completed': False,
            'notes': 'Missing vaccine ID'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Не указан ID вакцины')