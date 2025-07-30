from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class FeedingSession(models.Model):
    """
    Модель сессии кормления с поддержкой двух таймеров для грудного вскармливания.
    
    Эта модель позволяет отслеживать кормление с отдельными таймерами для каждой груди,
    что соответствует требованию 6.3 о функции кормления с двумя таймерами.
    """
    
    FEEDING_TYPE_CHOICES = [
        ('breast', 'Грудное вскармливание'),
        ('bottle', 'Кормление из бутылочки'),
        ('mixed', 'Смешанное кормление'),
    ]
    
    BREAST_CHOICES = [
        ('left', 'Левая грудь'),
        ('right', 'Правая грудь'),
        ('both', 'Обе груди'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='Время начала')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='Время окончания')
    
    # Поля для отслеживания времени кормления каждой грудью
    left_breast_duration = models.DurationField(
        default=timedelta(0), 
        verbose_name='Продолжительность кормления левой грудью'
    )
    right_breast_duration = models.DurationField(
        default=timedelta(0), 
        verbose_name='Продолжительность кормления правой грудью'
    )
    
    # Поля для управления таймерами
    left_timer_start = models.DateTimeField(null=True, blank=True, verbose_name='Начало таймера левой груди')
    right_timer_start = models.DateTimeField(null=True, blank=True, verbose_name='Начало таймера правой груди')
    left_timer_active = models.BooleanField(default=False, verbose_name='Активен ли таймер левой груди')
    right_timer_active = models.BooleanField(default=False, verbose_name='Активен ли таймер правой груди')
    
    # Дополнительные поля
    feeding_type = models.CharField(
        max_length=10, 
        choices=FEEDING_TYPE_CHOICES, 
        default='breast',
        verbose_name='Тип кормления'
    )
    amount = models.FloatField(null=True, blank=True, verbose_name='Количество (мл)')
    notes = models.TextField(blank=True, verbose_name='Заметки')
    
    # Поля для отслеживания последней активной груди
    last_active_breast = models.CharField(
        max_length=5, 
        choices=BREAST_CHOICES, 
        null=True, 
        blank=True,
        verbose_name='Последняя активная грудь'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        verbose_name = 'Сессия кормления'
        verbose_name_plural = 'Сессии кормления'
        ordering = ['-start_time']
    
    def __str__(self):
        return f'Кормление {self.user.username} - {self.start_time.strftime("%d.%m.%Y %H:%M")}'
    
    @property
    def total_duration(self):
        """Общая продолжительность кормления (сумма времени обеих грудей)."""
        return self.left_breast_duration + self.right_breast_duration
    
    @property
    def is_active(self):
        """Проверяет, активна ли сессия кормления."""
        return self.left_timer_active or self.right_timer_active
    
    @property
    def session_duration(self):
        """Общая продолжительность сессии от начала до конца."""
        if not self.end_time:
            return None
        return self.end_time - self.start_time
    
    def get_breast_duration_minutes(self, breast):
        """
        Возвращает продолжительность кормления для указанной груди в минутах.
        
        Args:
            breast (str): 'left' или 'right'
            
        Returns:
            float: Продолжительность в минутах
        """
        if breast == 'left':
            return self.left_breast_duration.total_seconds() / 60
        elif breast == 'right':
            return self.right_breast_duration.total_seconds() / 60
        return 0
    
    def get_total_duration_minutes(self):
        """Возвращает общую продолжительность кормления в минутах."""
        return self.total_duration.total_seconds() / 60
    
    def get_breast_percentage(self, breast):
        """
        Возвращает процент времени кормления для указанной груди.
        
        Args:
            breast (str): 'left' или 'right'
            
        Returns:
            float: Процент времени (0-100)
        """
        total_seconds = self.total_duration.total_seconds()
        if total_seconds == 0:
            return 0
        
        if breast == 'left':
            breast_seconds = self.left_breast_duration.total_seconds()
        elif breast == 'right':
            breast_seconds = self.right_breast_duration.total_seconds()
        else:
            return 0
        
        return (breast_seconds / total_seconds) * 100


class WeightRecord(models.Model):
    """
    Модель для отслеживания записей веса пользователя.
    
    Соответствует требованию 7.1 о возможности отслеживания веса
    с привязкой к дате и времени.
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь',
        related_name='weight_records'
    )
    date = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Дата и время измерения'
    )
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[
            MinValueValidator(0.1),  # Минимальный вес 0.1 кг
            MaxValueValidator(999.99)  # Максимальный вес 999.99 кг
        ],
        verbose_name='Вес (кг)'
    )
    notes = models.TextField(
        blank=True, 
        verbose_name='Заметки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Обновлено'
    )
    
    class Meta:
        verbose_name = 'Запись веса'
        verbose_name_plural = 'Записи веса'
        ordering = ['-date']
        unique_together = ['user', 'date']  # Предотвращает дублирование записей в одно время
    
    def __str__(self):
        return f'{self.user.username} - {self.weight} кг ({self.date.strftime("%d.%m.%Y %H:%M")})'
    
    @property
    def weight_kg(self):
        """Возвращает вес в килограммах как float."""
        return float(self.weight)
    
    def is_within_normal_range(self, min_weight=None, max_weight=None):
        """
        Проверяет, находится ли вес в пределах нормы.
        
        Args:
            min_weight (float): Минимальный нормальный вес
            max_weight (float): Максимальный нормальный вес
            
        Returns:
            bool: True если в пределах нормы, False если нет, None если границы не заданы
        """
        if min_weight is None or max_weight is None:
            return None
        return min_weight <= self.weight_kg <= max_weight


class BloodPressureRecord(models.Model):
    """
    Модель для отслеживания записей артериального давления пользователя.
    
    Соответствует требованию 7.2 о возможности отслеживания артериального давления
    с сохранением систолического и диастолического значений.
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь',
        related_name='blood_pressure_records'
    )
    date = models.DateTimeField(
        default=timezone.now, 
        verbose_name='Дата и время измерения'
    )
    systolic = models.IntegerField(
        validators=[
            MinValueValidator(50),   # Минимальное систолическое давление
            MaxValueValidator(300)   # Максимальное систолическое давление
        ],
        verbose_name='Систолическое давление (верхнее)'
    )
    diastolic = models.IntegerField(
        validators=[
            MinValueValidator(30),   # Минимальное диастолическое давление
            MaxValueValidator(200)   # Максимальное диастолическое давление
        ],
        verbose_name='Диастолическое давление (нижнее)'
    )
    pulse = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(30),   # Минимальный пульс
            MaxValueValidator(250)   # Максимальный пульс
        ],
        verbose_name='Пульс (уд/мин)'
    )
    notes = models.TextField(
        blank=True, 
        verbose_name='Заметки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='Обновлено'
    )
    
    class Meta:
        verbose_name = 'Запись артериального давления'
        verbose_name_plural = 'Записи артериального давления'
        ordering = ['-date']
        unique_together = ['user', 'date']  # Предотвращает дублирование записей в одно время
    
    def __str__(self):
        pulse_str = f', пульс {self.pulse}' if self.pulse else ''
        return f'{self.user.username} - {self.systolic}/{self.diastolic}{pulse_str} ({self.date.strftime("%d.%m.%Y %H:%M")})'
    
    @property
    def pressure_reading(self):
        """Возвращает показания давления в формате 'систолическое/диастолическое'."""
        return f'{self.systolic}/{self.diastolic}'
    
    def is_systolic_normal(self):
        """
        Проверяет, находится ли систолическое давление в пределах нормы.
        Нормальное систолическое давление: 90-140 мм рт. ст.
        
        Returns:
            str: 'normal', 'low', 'high'
        """
        if self.systolic < 90:
            return 'low'
        elif self.systolic > 140:
            return 'high'
        else:
            return 'normal'
    
    def is_diastolic_normal(self):
        """
        Проверяет, находится ли диастолическое давление в пределах нормы.
        Нормальное диастолическое давление: 60-90 мм рт. ст.
        
        Returns:
            str: 'normal', 'low', 'high'
        """
        if self.diastolic < 60:
            return 'low'
        elif self.diastolic > 90:
            return 'high'
        else:
            return 'normal'
    
    def is_pressure_normal(self):
        """
        Проверяет, находится ли давление в целом в пределах нормы.
        
        Returns:
            bool: True если оба показателя в норме, False если хотя бы один вне нормы
        """
        return (self.is_systolic_normal() == 'normal' and 
                self.is_diastolic_normal() == 'normal')
    
    def get_pressure_category(self):
        """
        Определяет категорию артериального давления согласно медицинским стандартам.
        
        Returns:
            str: Категория давления
        """
        if self.systolic < 90 or self.diastolic < 60:
            return 'Пониженное'
        elif self.systolic <= 120 and self.diastolic <= 80:
            return 'Нормальное'
        elif self.systolic <= 129 and self.diastolic <= 80:
            return 'Повышенное нормальное'
        elif self.systolic <= 139 or self.diastolic <= 89:
            return 'Высокое нормальное'
        elif self.systolic <= 159 or self.diastolic <= 99:
            return 'Гипертония 1 степени'
        elif self.systolic <= 179 or self.diastolic <= 109:
            return 'Гипертония 2 степени'
        else:
            return 'Гипертония 3 степени'
    
    def needs_medical_attention(self):
        """
        Определяет, требует ли показание медицинского внимания.
        
        Returns:
            bool: True если требует внимания врача
        """
        # Критические значения, требующие немедленного внимания
        if (self.systolic >= 180 or self.diastolic >= 110 or 
            self.systolic < 90 or self.diastolic < 60):
            return True
        return False


class DisclaimerAcknowledgment(models.Model):
    """
    Модель для отслеживания подтверждений ознакомления пользователей с дисклеймером.
    
    Соответствует требованию 8.3 о необходимости запрашивать подтверждение 
    ознакомления с дисклеймером при первом использовании функций, 
    связанных с медицинскими рекомендациями.
    """
    
    FEATURE_CHOICES = [
        ('pregnancy_info', 'Информация о беременности'),
        ('nutrition_advice', 'Советы по питанию'),
        ('child_development', 'Развитие ребенка'),
        ('health_tracking', 'Отслеживание показателей здоровья'),
        ('kick_counter', 'Счетчик шевелений'),
        ('feeding_tracker', 'Отслеживание кормления'),
        ('sleep_tracker', 'Отслеживание сна'),
        ('vaccine_calendar', 'Календарь прививок'),
        ('general_recommendations', 'Общие рекомендации'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Пользователь',
        related_name='disclaimer_acknowledgments'
    )
    feature = models.CharField(
        max_length=50,
        choices=FEATURE_CHOICES,
        verbose_name='Функция/раздел'
    )
    acknowledged_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подтверждения'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-адрес'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        verbose_name = 'Подтверждение дисклеймера'
        verbose_name_plural = 'Подтверждения дисклеймера'
        unique_together = ['user', 'feature']  # Один пользователь может подтвердить каждую функцию только один раз
        ordering = ['-acknowledged_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.get_feature_display()} ({self.acknowledged_at.strftime("%d.%m.%Y %H:%M")})'
    
    @classmethod
    def has_user_acknowledged(cls, user, feature):
        """
        Проверяет, подтвердил ли пользователь ознакомление с дисклеймером для указанной функции.
        
        Args:
            user (User): Пользователь
            feature (str): Код функции
            
        Returns:
            bool: True если пользователь подтвердил ознакомление
        """
        return cls.objects.filter(user=user, feature=feature).exists()
    
    @classmethod
    def acknowledge_feature(cls, user, feature, ip_address=None, user_agent=None):
        """
        Создает запись о подтверждении ознакомления с дисклеймером.
        
        Args:
            user (User): Пользователь
            feature (str): Код функции
            ip_address (str): IP-адрес пользователя
            user_agent (str): User Agent браузера
            
        Returns:
            DisclaimerAcknowledgment: Созданная запись или существующая
        """
        acknowledgment, created = cls.objects.get_or_create(
            user=user,
            feature=feature,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent or ''
            }
        )
        return acknowledgment
    
    @classmethod
    def get_features_requiring_acknowledgment(cls):
        """
        Возвращает список функций, требующих подтверждения дисклеймера.
        
        Returns:
            list: Список кодов функций
        """
        return [choice[0] for choice in cls.FEATURE_CHOICES]
    
    def get_acknowledgment_age_days(self):
        """
        Возвращает количество дней с момента подтверждения.
        
        Returns:
            int: Количество дней
        """
        return (timezone.now() - self.acknowledged_at).days