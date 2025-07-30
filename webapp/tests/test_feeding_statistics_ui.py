"""
Тесты для пользовательского интерфейса статистики кормления.

Этот модуль содержит тесты для проверки отображения
статистики кормления в пользовательском интерфейсе.
"""

import unittest
from django.test import TestCase, Client
from django.urls import reverse


class FeedingStatisticsUITestCase(TestCase):
    """Тесты для пользовательского интерфейса статистики кормления."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = Client()
    
    def test_feeding_tracker_statistics_elements_present(self):
        """Тест наличия элементов статистики на странице отслеживания кормления."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие заголовка статистики
        self.assertContains(response, 'Статистика кормлений')
        
        # Проверяем наличие общих элементов статистики за сегодня
        self.assertContains(response, 'id="todayFeedingCount"')
        self.assertContains(response, 'id="todayBreastCount"')
        self.assertContains(response, 'id="todayBottleCount"')
        self.assertContains(response, 'id="todayFeedingDuration"')
        self.assertContains(response, 'id="todayFeedingAmount"')
        
        # Проверяем наличие элементов недельной статистики
        self.assertContains(response, 'id="weeklyFeedingAvg"')
        self.assertContains(response, 'id="weeklyDurationAvg"')
        self.assertContains(response, 'id="weeklyAmountAvg"')
        self.assertContains(response, 'id="weeklyAvgSessionDuration"')
        
        # Проверяем наличие элементов рекордов недели
        self.assertContains(response, 'id="weeklyLongestSession"')
        self.assertContains(response, 'id="weeklyShortestSession"')
        self.assertContains(response, 'id="weeklyTotalCount"')
    
    def test_breast_statistics_elements_present(self):
        """Тест наличия элементов детальной статистики по грудям."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие заголовков статистики по грудям
        self.assertContains(response, 'Статистика по грудям - Сегодня')
        self.assertContains(response, 'Статистика по грудям - За неделю')
        
        # Проверяем наличие элементов статистики левой груди за сегодня
        self.assertContains(response, 'id="todayLeftBreastDuration"')
        self.assertContains(response, 'id="todayLeftBreastPercentage"')
        self.assertContains(response, 'id="todayLeftBreastBar"')
        
        # Проверяем наличие элементов статистики правой груди за сегодня
        self.assertContains(response, 'id="todayRightBreastDuration"')
        self.assertContains(response, 'id="todayRightBreastPercentage"')
        self.assertContains(response, 'id="todayRightBreastBar"')
        
        # Проверяем наличие элементов статистики левой груди за неделю
        self.assertContains(response, 'id="weeklyLeftBreastDuration"')
        self.assertContains(response, 'id="weeklyLeftBreastPercentage"')
        self.assertContains(response, 'id="weeklyLeftBreastBar"')
        
        # Проверяем наличие элементов статистики правой груди за неделю
        self.assertContains(response, 'id="weeklyRightBreastDuration"')
        self.assertContains(response, 'id="weeklyRightBreastPercentage"')
        self.assertContains(response, 'id="weeklyRightBreastBar"')
        
        # Проверяем наличие элементов средних значений по грудям
        self.assertContains(response, 'id="weeklyAvgLeftBreastDuration"')
        self.assertContains(response, 'id="weeklyAvgRightBreastDuration"')
    
    def test_progress_bars_present(self):
        """Тест наличия прогресс-баров для визуализации статистики по грудям."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие прогресс-баров
        self.assertContains(response, 'bg-pink-400')  # Цвет для левой груди
        self.assertContains(response, 'bg-blue-400')  # Цвет для правой груди
        
        # Проверяем структуру прогресс-баров
        self.assertContains(response, 'bg-gray-200 rounded-full h-2')  # Фон прогресс-бара
        self.assertContains(response, 'h-2 rounded-full')  # Активная часть прогресс-бара
    
    def test_chart_container_present(self):
        """Тест наличия контейнера для графика статистики."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие контейнера для графика
        self.assertContains(response, 'id="feedingChart"')
        self.assertContains(response, 'id="feedingChartCanvas"')
        self.assertContains(response, 'График кормлений за неделю')
    
    def test_statistics_layout_responsive(self):
        """Тест адаптивности макета статистики."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие адаптивных классов
        self.assertContains(response, 'grid-cols-1')
        self.assertContains(response, 'md:grid-cols-2')
        self.assertContains(response, 'lg:grid-cols-3')
        
        # Проверяем наличие отступов и промежутков
        self.assertContains(response, 'gap-4')
        self.assertContains(response, 'mb-6')
        self.assertContains(response, 'space-y-2')
        self.assertContains(response, 'space-y-3')
    
    def test_statistics_cards_styling(self):
        """Тест стилизации карточек статистики."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие стилей карточек
        self.assertContains(response, 'glass-card')
        self.assertContains(response, 'p-4')
        
        # Проверяем наличие заголовков карточек
        self.assertContains(response, 'text-lg font-semibold mb-2')
        self.assertContains(response, 'text-lg font-semibold mb-4')
    
    def test_statistics_text_labels(self):
        """Тест наличия текстовых меток для статистики."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие основных меток
        self.assertContains(response, 'Всего кормлений:')
        self.assertContains(response, 'Грудное вскармливание:')
        self.assertContains(response, 'Из бутылочки:')
        self.assertContains(response, 'Общая продолжительность:')
        self.assertContains(response, 'Общий объем:')
        
        # Проверяем наличие меток для недельной статистики
        self.assertContains(response, 'Кормлений в день:')
        self.assertContains(response, 'Продолжительность:')
        self.assertContains(response, 'Длительность сессии:')
        
        # Проверяем наличие меток для рекордов
        self.assertContains(response, 'Самая долгая сессия:')
        self.assertContains(response, 'Самая короткая сессия:')
        self.assertContains(response, 'Всего сессий:')
        
        # Проверяем наличие меток для статистики по грудям
        self.assertContains(response, 'Левая грудь:')
        self.assertContains(response, 'Правая грудь:')
        self.assertContains(response, 'Среднее в день (левая):')
        self.assertContains(response, 'Среднее в день (правая):')
    
    def test_statistics_default_values(self):
        """Тест наличия значений по умолчанию для статистики."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что элементы инициализированы со значениями по умолчанию
        # Большинство элементов должны содержать "0" как начальное значение
        response_content = response.content.decode()
        
        # Подсчитываем количество элементов со значением "0"
        zero_count = response_content.count('>0<')
        self.assertGreater(zero_count, 10)  # Должно быть много элементов с нулевыми значениями
        
        # Проверяем наличие единиц измерения
        self.assertContains(response, '0 мин')
        self.assertContains(response, '0 мл')
        self.assertContains(response, '0%')
    
    def test_javascript_functions_present(self):
        """Тест наличия JavaScript функций для работы со статистикой."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие основных JavaScript функций
        self.assertContains(response, 'loadFeedingStatistics')
        self.assertContains(response, 'createFeedingChart')
        self.assertContains(response, 'updateElementText')
        self.assertContains(response, 'updateProgressBar')
    
    def test_chart_js_library_included(self):
        """Тест включения библиотеки Chart.js для графиков."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие ссылки на Chart.js
        self.assertContains(response, 'chart.js')
    
    def test_statistics_section_structure(self):
        """Тест структуры секции статистики."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие основного контейнера статистики
        self.assertContains(response, 'class="neo-container"')
        
        # Проверяем наличие сетки для карточек статистики
        self.assertContains(response, 'id="feedingStats"')
        
        # Проверяем наличие разделителей между секциями
        self.assertContains(response, 'border-t border-gray-200')
    
    def test_accessibility_attributes(self):
        """Тест наличия атрибутов доступности."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем наличие семантических элементов
        self.assertContains(response, '<h2')
        self.assertContains(response, '<h3')
        
        # Проверяем наличие структурированного контента
        self.assertContains(response, 'flex justify-between')  # Для выравнивания меток и значений
    
    def test_color_coding_consistency(self):
        """Тест согласованности цветового кодирования."""
        url = reverse('webapp:feeding_tracker')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что цвета для левой и правой груди используются последовательно
        # Розовый для левой груди
        self.assertContains(response, 'bg-pink-400')
        
        # Синий для правой груди
        self.assertContains(response, 'bg-blue-400')
        
        # Проверяем наличие серого цвета для фона прогресс-баров
        self.assertContains(response, 'bg-gray-200')


if __name__ == '__main__':
    unittest.main()