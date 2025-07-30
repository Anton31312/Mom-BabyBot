"""
Тесты для API эндпоинтов профилей детей.

Этот модуль содержит тесты для API эндпоинтов профилей детей и измерений.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from botapp.models import User, db_manager
from botapp.models_child import Child, Measurement


class ChildAPITestCase(TestCase):
    """Тестовый случай для API эндпоинтов профилей детей."""
    
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
            
            # Create a test measurement
            self.measurement = Measurement(
                child_id=self.child.id,
                date=datetime.now(),
                height=75.0,
                weight=10.0,
                head_circumference=45.0,
                notes='Test measurement'
            )
            session.add(self.measurement)
            session.commit()
            session.refresh(self.measurement)
        finally:
            db_manager.close_session(session)
        
        # Set up test client
        self.client = Client()
    
    def tearDown(self):
        """Очистка тестовых данных."""
        session = db_manager.get_session()
        try:
            # Delete test measurement
            measurement = session.query(Measurement).filter_by(id=self.measurement.id).first()
            if measurement:
                session.delete(measurement)
            
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
    
    def test_get_children(self):
        """Тест получения всех детей для пользователя."""
        url = f'/api/users/{self.user.id}/children/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('children', data)
        self.assertEqual(len(data['children']), 1)
        self.assertEqual(data['children'][0]['name'], 'Test Child')
    
    def test_create_child(self):
        """Test creating a new child profile."""
        url = f'/api/users/{self.user.id}/children/'
        data = {
            'name': 'New Child',
            'birth_date': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),  # 6 months old
            'gender': 'female'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'New Child')
        self.assertEqual(response_data['gender'], 'female')
        
        # Clean up the created child
        session = db_manager.get_session()
        try:
            child = session.query(Child).filter_by(id=response_data['id']).first()
            if child:
                session.delete(child)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_child_profile(self):
        """Test getting a specific child profile."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['name'], 'Test Child')
        self.assertEqual(data['gender'], 'male')
    
    def test_update_child_profile(self):
        """Test updating a child profile."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/'
        data = {
            'name': 'Updated Child Name'
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['name'], 'Updated Child Name')
        
        # Verify the update in the database
        session = db_manager.get_session()
        try:
            child = session.query(Child).filter_by(id=self.child.id).first()
            self.assertEqual(child.name, 'Updated Child Name')
        finally:
            db_manager.close_session(session)
    
    def test_delete_child_profile(self):
        """Test deleting a child profile."""
        # Create a child to delete
        session = db_manager.get_session()
        try:
            child_to_delete = Child(
                user_id=self.user.id,
                name='Child to Delete',
                birth_date=datetime.now() - timedelta(days=730),  # 2 years old
                gender='female'
            )
            session.add(child_to_delete)
            session.commit()
            session.refresh(child_to_delete)
            child_id = child_to_delete.id
        finally:
            db_manager.close_session(session)
        
        url = f'/api/users/{self.user.id}/children/{child_id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Child profile deleted successfully')
        
        # Verify the deletion in the database
        session = db_manager.get_session()
        try:
            child = session.query(Child).filter_by(id=child_id).first()
            self.assertIsNone(child)
        finally:
            db_manager.close_session(session)
    
    def test_get_measurements(self):
        """Test getting all measurements for a child."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('measurements', data)
        self.assertEqual(len(data['measurements']), 1)
        self.assertEqual(data['measurements'][0]['height'], 75.0)
        self.assertEqual(data['measurements'][0]['weight'], 10.0)
        self.assertEqual(data['measurements'][0]['head_circumference'], 45.0)
    
    def test_create_measurement(self):
        """Test creating a new measurement."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/'
        data = {
            'height': 78.0,
            'weight': 10.5,
            'head_circumference': 46.0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'notes': 'New measurement'
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['height'], 78.0)
        self.assertEqual(response_data['weight'], 10.5)
        self.assertEqual(response_data['head_circumference'], 46.0)
        self.assertEqual(response_data['notes'], 'New measurement')
        
        # Clean up the created measurement
        session = db_manager.get_session()
        try:
            measurement = session.query(Measurement).filter_by(id=response_data['id']).first()
            if measurement:
                session.delete(measurement)
                session.commit()
        finally:
            db_manager.close_session(session)
    
    def test_get_measurement(self):
        """Test getting a specific measurement."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/{self.measurement.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['height'], 75.0)
        self.assertEqual(data['weight'], 10.0)
        self.assertEqual(data['head_circumference'], 45.0)
        self.assertEqual(data['notes'], 'Test measurement')
    
    def test_update_measurement(self):
        """Test updating a measurement."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/{self.measurement.id}/'
        data = {
            'height': 76.0,
            'notes': 'Updated measurement'
        }
        response = self.client.put(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['height'], 76.0)
        self.assertEqual(response_data['weight'], 10.0)  # Unchanged
        self.assertEqual(response_data['notes'], 'Updated measurement')
        
        # Verify the update in the database
        session = db_manager.get_session()
        try:
            measurement = session.query(Measurement).filter_by(id=self.measurement.id).first()
            self.assertEqual(measurement.height, 76.0)
            self.assertEqual(measurement.notes, 'Updated measurement')
        finally:
            db_manager.close_session(session)
    
    def test_delete_measurement(self):
        """Test deleting a measurement."""
        # Create a measurement to delete
        session = db_manager.get_session()
        try:
            measurement_to_delete = Measurement(
                child_id=self.child.id,
                date=datetime.now(),
                height=80.0,
                weight=11.0,
                head_circumference=47.0,
                notes='Measurement to delete'
            )
            session.add(measurement_to_delete)
            session.commit()
            session.refresh(measurement_to_delete)
            measurement_id = measurement_to_delete.id
        finally:
            db_manager.close_session(session)
        
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/{measurement_id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['message'], 'Measurement deleted successfully')
        
        # Verify the deletion in the database
        session = db_manager.get_session()
        try:
            measurement = session.query(Measurement).filter_by(id=measurement_id).first()
            self.assertIsNone(measurement)
        finally:
            db_manager.close_session(session)
    
    def test_user_not_found(self):
        """Test API response when user is not found."""
        url = f'/api/users/999999/children/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'User not found')
    
    def test_child_not_found(self):
        """Test API response when child is not found."""
        url = f'/api/users/{self.user.id}/children/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Child not found')
    
    def test_measurement_not_found(self):
        """Test API response when measurement is not found."""
        url = f'/api/users/{self.user.id}/children/{self.child.id}/measurements/999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Measurement not found')
    
    def test_child_does_not_belong_to_user(self):
        """Test API response when child does not belong to the user."""
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
            
            # Try to access the child with the other user
            url = f'/api/users/{other_user.id}/children/{self.child.id}/'
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)
            self.assertEqual(data['error'], 'Child does not belong to this user')
            
            # Clean up
            session.delete(other_user)
            session.commit()
        finally:
            db_manager.close_session(session)