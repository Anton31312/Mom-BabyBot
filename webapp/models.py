from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class FeedingSession(models.Model):
    """
    Модель сессии кормления с поддержкой двух таймеров для грудного вскармливания.
    
    Эта модель позволяет отслеживать кормление с отдельными таймерами для каждой груди,
    что соответствует требованию 6.3 о функции кормления с двумя таймерами.
    """
    
    FEEDING_TYPE_CHOICES = [
        ('breast', _('Breast feeding')),
        ('bottle', _('Bottle feeding')),
        ('mixed', _('Mixed feeding')),
    ]
    
    BREAST_CHOICES = [
        ('left', _('Left breast')),
        ('right', _('Right breast')),
        ('both', _('Both breasts')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('User'))
    start_time = models.DateTimeField(auto_now_add=True, verbose_name=_('Start time'))
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=_('End time'))
    
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


class UserProfile(models.Model):
    """
    Расширенный профиль пользователя для персонализации контента.
    
    Соответствует требованию 9.1 о персонализированном контенте на основе профиля пользователя.
    """
    
    PREGNANCY_STATUS_CHOICES = [
        ('not_pregnant', 'Не беременна'),
        ('pregnant', 'Беременна'),
        ('postpartum', 'После родов'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('first_time', 'Первый ребенок'),
        ('experienced', 'Есть опыт'),
        ('multiple_children', 'Несколько детей'),
    ]
    
    INTEREST_CHOICES = [
        ('nutrition', 'Питание'),
        ('development', 'Развитие ребенка'),
        ('health', 'Здоровье'),
        ('sleep', 'Сон'),
        ('activities', 'Активности'),
        ('safety', 'Безопасность'),
        ('education', 'Образование'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='profile'
    )
    
    # Основная информация для персонализации
    pregnancy_status = models.CharField(
        max_length=20,
        choices=PREGNANCY_STATUS_CHOICES,
        default='not_pregnant',
        verbose_name='Статус беременности'
    )
    pregnancy_week = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        verbose_name='Неделя беременности'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Предполагаемая дата родов'
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        default='first_time',
        verbose_name='Уровень опыта'
    )
    
    # Интересы пользователя (для персонализации контента)
    interests = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Интересы',
        help_text='Список интересов пользователя для персонализации контента'
    )
    
    # Настройки персонализации
    show_daily_tips = models.BooleanField(
        default=True,
        verbose_name='Показывать ежедневные советы'
    )
    preferred_content_frequency = models.CharField(
        max_length=10,
        choices=[
            ('daily', 'Ежедневно'),
            ('weekly', 'Еженедельно'),
            ('monthly', 'Ежемесячно'),
        ],
        default='daily',
        verbose_name='Частота показа контента'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f'Профиль {self.user.username}'
    
    @property
    def current_pregnancy_week(self):
        """Вычисляет текущую неделю беременности на основе предполагаемой даты родов."""
        if not self.due_date or self.pregnancy_status != 'pregnant':
            return self.pregnancy_week
        
        today = timezone.now().date()
        days_until_due = (self.due_date - today).days
        weeks_pregnant = 40 - (days_until_due // 7)
        return max(1, min(42, weeks_pregnant))
    
    @property
    def is_high_risk_pregnancy(self):
        """Определяет, является ли беременность высокого риска (для персонализации контента)."""
        if self.pregnancy_status != 'pregnant':
            return False
        
        current_week = self.current_pregnancy_week
        return current_week and (current_week < 12 or current_week > 37)
    
    def get_personalization_tags(self):
        """
        Возвращает теги для персонализации контента на основе профиля пользователя.
        
        Returns:
            list: Список тегов для фильтрации контента
        """
        tags = []
        
        # Добавляем теги на основе статуса беременности
        tags.append(self.pregnancy_status)
        
        # Добавляем теги на основе недели беременности
        if self.pregnancy_status == 'pregnant' and self.current_pregnancy_week:
            week = self.current_pregnancy_week
            if week <= 12:
                tags.append('first_trimester')
            elif week <= 28:
                tags.append('second_trimester')
            else:
                tags.append('third_trimester')
        
        # Добавляем теги на основе уровня опыта
        tags.append(self.experience_level)
        
        # Добавляем интересы
        tags.extend(self.interests)
        
        return tags
    
    def should_show_content_today(self):
        """
        Определяет, следует ли показывать персонализированный контент сегодня.
        
        Returns:
            bool: True если контент должен быть показан
        """
        if not self.show_daily_tips:
            return False
        
        # Логика на основе частоты показа контента
        if self.preferred_content_frequency == 'daily':
            return True
        elif self.preferred_content_frequency == 'weekly':
            # Показываем раз в неделю (например, по понедельникам)
            return timezone.now().weekday() == 0
        elif self.preferred_content_frequency == 'monthly':
            # Показываем раз в месяц (например, 1 числа)
            return timezone.now().day == 1
        
        return True


class PersonalizedContent(models.Model):
    """
    Модель для хранения персонализированного контента.
    
    Соответствует требованию 9.1 о системе персонализированного контента
    на основе профиля пользователя.
    """
    
    CONTENT_TYPE_CHOICES = [
        ('tip', 'Совет'),
        ('fact', 'Факт'),
        ('recommendation', 'Рекомендация'),
        ('warning', 'Предупреждение'),
        ('milestone', 'Веха развития'),
        ('activity', 'Активность'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    content = models.TextField(
        verbose_name='Содержание'
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='tip',
        verbose_name='Тип контента'
    )
    
    # Критерии персонализации
    pregnancy_status_filter = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Фильтр по статусу беременности',
        help_text='Список статусов беременности, для которых подходит контент'
    )
    pregnancy_week_min = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        verbose_name='Минимальная неделя беременности'
    )
    pregnancy_week_max = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        verbose_name='Максимальная неделя беременности'
    )
    experience_level_filter = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Фильтр по уровню опыта',
        help_text='Список уровней опыта, для которых подходит контент'
    )
    interest_tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Теги интересов',
        help_text='Список тегов интересов для фильтрации контента'
    )
    
    # Настройки отображения
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Приоритет'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    show_once = models.BooleanField(
        default=False,
        verbose_name='Показать только один раз',
        help_text='Если отмечено, контент будет показан пользователю только один раз'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )
    
    class Meta:
        verbose_name = 'Персонализированный контент'
        verbose_name_plural = 'Персонализированный контент'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f'{self.get_content_type_display()}: {self.title}'
    
    def is_suitable_for_user(self, user_profile):
        """
        Проверяет, подходит ли контент для указанного профиля пользователя.
        
        Args:
            user_profile (UserProfile): Профиль пользователя
            
        Returns:
            bool: True если контент подходит пользователю
        """
        # Проверяем статус беременности
        if (self.pregnancy_status_filter and 
            user_profile.pregnancy_status not in self.pregnancy_status_filter):
            return False
        
        # Проверяем неделю беременности
        current_week = user_profile.current_pregnancy_week
        if current_week:
            if (self.pregnancy_week_min and current_week < self.pregnancy_week_min):
                return False
            if (self.pregnancy_week_max and current_week > self.pregnancy_week_max):
                return False
        
        # Проверяем уровень опыта
        if (self.experience_level_filter and 
            user_profile.experience_level not in self.experience_level_filter):
            return False
        
        # Проверяем интересы
        if self.interest_tags:
            user_interests = set(user_profile.interests)
            content_interests = set(self.interest_tags)
            if not user_interests.intersection(content_interests):
                return False
        
        return True
    
    @classmethod
    def get_personalized_content_for_user(cls, user, limit=5):
        """
        Получает персонализированный контент для пользователя.
        
        Args:
            user (User): Пользователь
            limit (int): Максимальное количество элементов контента
            
        Returns:
            QuerySet: Отфильтрованный контент для пользователя
        """
        try:
            user_profile = user.profile
        except UserProfile.DoesNotExist:
            # Если профиль не существует, возвращаем общий контент
            return cls.objects.filter(
                is_active=True,
                pregnancy_status_filter=[],
                experience_level_filter=[],
                interest_tags=[]
            )[:limit]
        
        # Получаем все активные элементы контента
        queryset = cls.objects.filter(is_active=True)
        
        # Фильтруем контент, который уже был показан пользователю (если show_once=True)
        if hasattr(user, 'content_views'):
            viewed_content_ids = user.content_views.filter(
                content__show_once=True
            ).values_list('content_id', flat=True)
            queryset = queryset.exclude(id__in=viewed_content_ids)
        
        # Фильтруем по критериям персонализации
        suitable_content = []
        for content in queryset:
            if content.is_suitable_for_user(user_profile):
                suitable_content.append(content)
        
        # Сортируем по приоритету и возвращаем ограниченное количество
        suitable_content.sort(key=lambda x: (
            {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}[x.priority],
            x.created_at
        ), reverse=True)
        
        return suitable_content[:limit]


class UserContentView(models.Model):
    """
    Модель для отслеживания просмотров персонализированного контента пользователями.
    
    Используется для предотвращения повторного показа контента, помеченного как show_once,
    и для аналитики взаимодействия с контентом.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='content_views'
    )
    content = models.ForeignKey(
        PersonalizedContent,
        on_delete=models.CASCADE,
        verbose_name='Контент',
        related_name='views'
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата просмотра'
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=[
            ('viewed', 'Просмотрен'),
            ('clicked', 'Нажат'),
            ('dismissed', 'Отклонен'),
            ('saved', 'Сохранен'),
        ],
        default='viewed',
        verbose_name='Тип взаимодействия'
    )
    
    class Meta:
        verbose_name = 'Просмотр контента'
        verbose_name_plural = 'Просмотры контента'
        unique_together = ['user', 'content']  # Один пользователь может просмотреть контент только один раз
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.content.title} ({self.get_interaction_type_display()})'


class DailyTip(models.Model):
    """
    Модель для хранения ежедневных советов и фактов.
    
    Соответствует требованию 9.2 о реализации ежедневных советов и фактов,
    связанных с текущим этапом развития ребенка или беременности.
    """
    
    TIP_TYPE_CHOICES = [
        ('tip', 'Совет'),
        ('fact', 'Факт'),
        ('milestone', 'Веха развития'),
        ('reminder', 'Напоминание'),
        ('warning', 'Предупреждение'),
    ]
    
    AUDIENCE_CHOICES = [
        ('pregnant', 'Беременные'),
        ('new_mom', 'Молодые мамы'),
        ('experienced_mom', 'Опытные мамы'),
        ('all', 'Все пользователи'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    content = models.TextField(
        verbose_name='Содержание'
    )
    tip_type = models.CharField(
        max_length=20,
        choices=TIP_TYPE_CHOICES,
        default='tip',
        verbose_name='Тип совета'
    )
    
    # Критерии отображения
    pregnancy_week_min = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        verbose_name='Минимальная неделя беременности'
    )
    pregnancy_week_max = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        verbose_name='Максимальная неделя беременности'
    )
    baby_age_min_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Минимальный возраст ребенка (дни)'
    )
    baby_age_max_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Максимальный возраст ребенка (дни)'
    )
    audience = models.CharField(
        max_length=20,
        choices=AUDIENCE_CHOICES,
        default='all',
        verbose_name='Целевая аудитория'
    )
    
    # Настройки отображения
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Приоритет (1-10)',
        help_text='Чем выше число, тем выше приоритет'
    )
    show_date_start = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата начала показа'
    )
    show_date_end = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата окончания показа'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлен'
    )
    
    class Meta:
        verbose_name = 'Ежедневный совет'
        verbose_name_plural = 'Ежедневные советы'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f'{self.get_tip_type_display()}: {self.title}'
    
    def is_suitable_for_user_profile(self, user_profile):
        """
        Проверяет, подходит ли совет для указанного профиля пользователя.
        
        Args:
            user_profile (UserProfile): Профиль пользователя
            
        Returns:
            bool: True если совет подходит пользователю
        """
        # Проверяем активность
        if not self.is_active:
            return False
        
        # Проверяем даты показа
        today = timezone.now().date()
        if self.show_date_start and today < self.show_date_start:
            return False
        if self.show_date_end and today > self.show_date_end:
            return False
        
        # Проверяем целевую аудиторию
        if self.audience != 'all':
            if self.audience == 'pregnant' and user_profile.pregnancy_status != 'pregnant':
                return False
            elif self.audience == 'new_mom':
                # Для новых мам проверяем, что это первый ребенок И не беременна
                if user_profile.experience_level != 'first_time' or user_profile.pregnancy_status == 'pregnant':
                    return False
            elif self.audience == 'experienced_mom':
                # Для опытных мам проверяем, что это не первый ребенок
                if user_profile.experience_level == 'first_time':
                    return False
        
        # Проверяем неделю беременности
        if user_profile.pregnancy_status == 'pregnant':
            current_week = user_profile.current_pregnancy_week
            if current_week:
                if self.pregnancy_week_min and current_week < self.pregnancy_week_min:
                    return False
                if self.pregnancy_week_max and current_week > self.pregnancy_week_max:
                    return False
        
        # Проверяем возраст ребенка (если есть дети)
        # Для упрощения, пока не реализуем проверку возраста детей
        # Это можно добавить позже, когда будет интеграция с моделями детей
        
        return True
    
    @classmethod
    def get_daily_tip_for_user(cls, user):
        """
        Получает ежедневный совет для пользователя.
        
        Args:
            user (User): Пользователь Django
            
        Returns:
            DailyTip or None: Подходящий совет или None
        """
        from webapp.utils.personalization_utils import get_or_create_user_profile
        
        try:
            user_profile = get_or_create_user_profile(user)
            
            # Получаем все активные советы
            tips = cls.objects.filter(is_active=True)
            
            # Фильтруем подходящие советы
            suitable_tips = []
            for tip in tips:
                if tip.is_suitable_for_user_profile(user_profile):
                    suitable_tips.append(tip)
            
            if not suitable_tips:
                return None
            
            # Сортируем по приоритету и возвращаем первый
            suitable_tips.sort(key=lambda x: x.priority, reverse=True)
            return suitable_tips[0]
            
        except Exception:
            return None
    
    @classmethod
    def get_tips_for_week(cls, pregnancy_week):
        """
        Получает советы для определенной недели беременности.
        
        Args:
            pregnancy_week (int): Неделя беременности
            
        Returns:
            QuerySet: Подходящие советы
        """
        return cls.objects.filter(
            is_active=True,
            pregnancy_week_min__lte=pregnancy_week,
            pregnancy_week_max__gte=pregnancy_week
        ).order_by('-priority')


class UserDailyTipView(models.Model):
    """
    Модель для отслеживания просмотров ежедневных советов пользователями.
    
    Используется для предотвращения повторного показа одного и того же совета
    в течение определенного периода.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='daily_tip_views'
    )
    tip = models.ForeignKey(
        DailyTip,
        on_delete=models.CASCADE,
        verbose_name='Совет',
        related_name='user_views'
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата просмотра'
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=[
            ('viewed', 'Просмотрен'),
            ('liked', 'Понравился'),
            ('dismissed', 'Отклонен'),
            ('shared', 'Поделился'),
        ],
        default='viewed',
        verbose_name='Тип взаимодействия'
    )
    
    class Meta:
        verbose_name = 'Просмотр ежедневного совета'
        verbose_name_plural = 'Просмотры ежедневных советов'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.tip.title} ({self.viewed_at.strftime("%d.%m.%Y")})'
    
    @classmethod
    def mark_tip_as_viewed(cls, user, tip, interaction_type='viewed'):
        """
        Отмечает совет как просмотренный пользователем.
        
        Args:
            user (User): Пользователь
            tip (DailyTip): Совет
            interaction_type (str): Тип взаимодействия
            
        Returns:
            UserDailyTipView: Запись о просмотре
        """
        view, created = cls.objects.get_or_create(
            user=user,
            tip=tip,
            defaults={'interaction_type': interaction_type}
        )
        
        if not created and view.interaction_type != interaction_type:
            view.interaction_type = interaction_type
            view.save()
        
        return view
    
    @classmethod
    def has_user_seen_tip_today(cls, user, tip):
        """
        Проверяет, видел ли пользователь совет сегодня.
        
        Args:
            user (User): Пользователь
            tip (DailyTip): Совет
            
        Returns:
            bool: True если пользователь уже видел совет сегодня
        """
        today = timezone.now().date()
        return cls.objects.filter(
            user=user,
            tip=tip,
            viewed_at__date=today
        ).exists()


class Achievement(models.Model):
    """
    Модель для хранения достижений, которые могут быть присвоены пользователям.
    
    Соответствует требованию 9.3 о системе достижений для отметки важных вех
    в развитии ребенка или беременности.
    """
    
    ACHIEVEMENT_TYPE_CHOICES = [
        ('pregnancy_milestone', 'Веха беременности'),
        ('baby_milestone', 'Веха развития ребенка'),
        ('feeding_milestone', 'Достижение в кормлении'),
        ('health_milestone', 'Достижение в здоровье'),
        ('app_usage', 'Использование приложения'),
        ('data_tracking', 'Отслеживание данных'),
        ('special_event', 'Особое событие'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкое'),
        ('medium', 'Среднее'),
        ('hard', 'Сложное'),
        ('legendary', 'Легендарное'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Название достижения'
    )
    description = models.TextField(
        verbose_name='Описание достижения'
    )
    achievement_type = models.CharField(
        max_length=30,
        choices=ACHIEVEMENT_TYPE_CHOICES,
        verbose_name='Тип достижения'
    )
    difficulty = models.CharField(
        max_length=15,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name='Сложность'
    )
    icon = models.CharField(
        max_length=50,
        default='🏆',
        verbose_name='Иконка',
        help_text='Эмодзи или название иконки для отображения достижения'
    )
    points = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name='Очки за достижение'
    )
    
    # Условия для получения достижения
    condition_type = models.CharField(
        max_length=50,
        choices=[
            ('pregnancy_week', 'Достижение определенной недели беременности'),
            ('baby_age_days', 'Возраст ребенка в днях'),
            ('feeding_sessions', 'Количество сессий кормления'),
            ('weight_records', 'Количество записей веса'),
            ('blood_pressure_records', 'Количество записей давления'),
            ('app_usage_days', 'Дни использования приложения'),
            ('consecutive_days', 'Последовательные дни использования'),
            ('data_completeness', 'Полнота заполнения данных'),
            ('special_date', 'Особая дата'),
        ],
        verbose_name='Тип условия'
    )
    condition_value = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Значение условия',
        help_text='Числовое значение для условия (например, неделя беременности, количество записей)'
    )
    condition_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Дополнительные данные условия',
        help_text='Дополнительные параметры для сложных условий'
    )
    
    # Настройки отображения
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активно'
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name='Скрытое',
        help_text='Скрытые достижения не показываются пользователю до получения'
    )
    show_progress = models.BooleanField(
        default=True,
        verbose_name='Показывать прогресс',
        help_text='Показывать ли прогресс выполнения условия'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено'
    )
    
    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['difficulty', 'points', 'title']
    
    def __str__(self):
        return f'{self.icon} {self.title} ({self.points} очков)'
    
    def check_condition_for_user(self, user):
        """
        Проверяет, выполнено ли условие достижения для указанного пользователя.
        
        Args:
            user (User): Пользователь для проверки
            
        Returns:
            tuple: (bool, int) - (выполнено ли условие, текущий прогресс)
        """
        try:
            if self.condition_type == 'pregnancy_week':
                try:
                    profile = user.profile
                    current_week = profile.current_pregnancy_week
                    if current_week and current_week >= self.condition_value:
                        return True, current_week
                    return False, current_week or 0
                except UserProfile.DoesNotExist:
                    return False, 0
            
            elif self.condition_type == 'baby_age_days':
                # Предполагаем, что возраст ребенка рассчитывается на основе даты рождения
                # Это требует дополнительной модели для хранения информации о ребенке
                return False, 0
            
            elif self.condition_type == 'feeding_sessions':
                count = FeedingSession.objects.filter(user=user).count()
                return count >= self.condition_value, count
            
            elif self.condition_type == 'weight_records':
                count = WeightRecord.objects.filter(user=user).count()
                return count >= self.condition_value, count
            
            elif self.condition_type == 'blood_pressure_records':
                count = BloodPressureRecord.objects.filter(user=user).count()
                return count >= self.condition_value, count
            
            elif self.condition_type == 'app_usage_days':
                # Подсчитываем уникальные дни, когда пользователь был активен
                # Это требует отслеживания активности пользователя
                return False, 0
            
            elif self.condition_type == 'consecutive_days':
                # Подсчитываем последовательные дни использования
                return False, 0
            
            elif self.condition_type == 'data_completeness':
                # Проверяем полноту заполнения профиля
                try:
                    profile = user.profile
                    completeness = self._calculate_profile_completeness(profile)
                    return completeness >= self.condition_value, completeness
                except UserProfile.DoesNotExist:
                    return False, 0
            
            elif self.condition_type == 'special_date':
                # Проверяем особые даты (например, день рождения ребенка)
                special_date = self.condition_data.get('date')
                if special_date:
                    from datetime import datetime
                    target_date = datetime.strptime(special_date, '%Y-%m-%d').date()
                    today = timezone.now().date()
                    return today >= target_date, 1 if today >= target_date else 0
                return False, 0
            
        except Exception as e:
            # Логируем ошибку и возвращаем False
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Ошибка при проверке условия достижения {self.id}: {e}')
            return False, 0
        
        return False, 0
    
    def _calculate_profile_completeness(self, profile):
        """
        Рассчитывает процент заполненности профиля пользователя.
        
        Args:
            profile (UserProfile): Профиль пользователя
            
        Returns:
            int: Процент заполненности (0-100)
        """
        total_fields = 0
        filled_fields = 0
        
        # Проверяем основные поля профиля
        fields_to_check = [
            'pregnancy_status', 'experience_level', 'interests',
            'due_date', 'pregnancy_week'
        ]
        
        for field_name in fields_to_check:
            total_fields += 1
            field_value = getattr(profile, field_name, None)
            
            if field_value:
                if isinstance(field_value, list) and len(field_value) > 0:
                    filled_fields += 1
                elif not isinstance(field_value, list):
                    filled_fields += 1
        
        return int((filled_fields / total_fields) * 100) if total_fields > 0 else 0
    
    def get_progress_for_user(self, user):
        """
        Возвращает прогресс выполнения достижения для пользователя.
        
        Args:
            user (User): Пользователь
            
        Returns:
            dict: Информация о прогрессе
        """
        is_completed, current_progress = self.check_condition_for_user(user)
        
        return {
            'is_completed': is_completed,
            'current_progress': current_progress,
            'target_value': self.condition_value,
            'progress_percentage': min(100, int((current_progress / self.condition_value) * 100)) if self.condition_value else 0
        }
    
    @classmethod
    def get_available_achievements_for_user(cls, user, include_completed=False):
        """
        Возвращает список доступных достижений для пользователя.
        
        Args:
            user (User): Пользователь
            include_completed (bool): Включать ли уже полученные достижения
            
        Returns:
            QuerySet: Отфильтрованные достижения
        """
        queryset = cls.objects.filter(is_active=True)
        
        if not include_completed:
            # Исключаем уже полученные достижения
            earned_achievement_ids = UserAchievement.objects.filter(
                user=user
            ).values_list('achievement_id', flat=True)
            queryset = queryset.exclude(id__in=earned_achievement_ids)
        
        return queryset
    
    @classmethod
    def check_and_award_achievements(cls, user):
        """
        Проверяет все доступные достижения для пользователя и присваивает новые.
        
        Args:
            user (User): Пользователь для проверки
            
        Returns:
            list: Список новых достижений
        """
        new_achievements = []
        available_achievements = cls.get_available_achievements_for_user(user)
        
        for achievement in available_achievements:
            is_completed, _ = achievement.check_condition_for_user(user)
            if is_completed:
                user_achievement = UserAchievement.objects.create(
                    user=user,
                    achievement=achievement
                )
                new_achievements.append(user_achievement)
        
        return new_achievements


class UserAchievement(models.Model):
    """
    Модель для связи пользователей с полученными достижениями.
    
    Соответствует требованию 9.3 о системе достижений для отметки важных вех.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        verbose_name='Достижение',
        related_name='earned_by'
    )
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата получения'
    )
    
    # Дополнительные данные о получении достижения
    progress_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Данные прогресса',
        help_text='Дополнительная информация о том, как было получено достижение'
    )
    is_viewed = models.BooleanField(
        default=False,
        verbose_name='Просмотрено',
        help_text='Видел ли пользователь уведомление о получении достижения'
    )
    
    class Meta:
        verbose_name = 'Достижение пользователя'
        verbose_name_plural = 'Достижения пользователей'
        unique_together = ['user', 'achievement']  # Пользователь может получить каждое достижение только один раз
        ordering = ['-earned_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.achievement.title} ({self.earned_at.strftime("%d.%m.%Y")})'
    
    @property
    def days_since_earned(self):
        """Возвращает количество дней с момента получения достижения."""
        return (timezone.now() - self.earned_at).days
    
    def mark_as_viewed(self):
        """Отмечает достижение как просмотренное пользователем."""
        if not self.is_viewed:
            self.is_viewed = True
            self.save(update_fields=['is_viewed'])
    
    @classmethod
    def get_recent_achievements(cls, user, days=7):
        """
        Возвращает недавние достижения пользователя.
        
        Args:
            user (User): Пользователь
            days (int): Количество дней для поиска недавних достижений
            
        Returns:
            QuerySet: Недавние достижения
        """
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            user=user,
            earned_at__gte=cutoff_date
        ).select_related('achievement')
    
    @classmethod
    def get_unviewed_achievements(cls, user):
        """
        Возвращает непросмотренные достижения пользователя.
        
        Args:
            user (User): Пользователь
            
        Returns:
            QuerySet: Непросмотренные достижения
        """
        return cls.objects.filter(
            user=user,
            is_viewed=False
        ).select_related('achievement')
    
    @classmethod
    def get_user_statistics(cls, user):
        """
        Возвращает статистику достижений пользователя.
        
        Args:
            user (User): Пользователь
            
        Returns:
            dict: Статистика достижений
        """
        user_achievements = cls.objects.filter(user=user).select_related('achievement')
        
        total_achievements = user_achievements.count()
        total_points = sum(ua.achievement.points for ua in user_achievements)
        
        # Группировка по типам достижений
        achievements_by_type = {}
        for ua in user_achievements:
            achievement_type = ua.achievement.get_achievement_type_display()
            if achievement_type not in achievements_by_type:
                achievements_by_type[achievement_type] = 0
            achievements_by_type[achievement_type] += 1
        
        # Группировка по сложности
        achievements_by_difficulty = {}
        for ua in user_achievements:
            difficulty = ua.achievement.get_difficulty_display()
            if difficulty not in achievements_by_difficulty:
                achievements_by_difficulty[difficulty] = 0
            achievements_by_difficulty[difficulty] += 1
        
        return {
            'total_achievements': total_achievements,
            'total_points': total_points,
            'achievements_by_type': achievements_by_type,
            'achievements_by_difficulty': achievements_by_difficulty,
            'recent_achievements': cls.get_recent_achievements(user, days=30).count(),
            'unviewed_achievements': cls.get_unviewed_achievements(user).count(),
        }


class PregnancyWeekNotification(models.Model):
    """
    Модель для уведомлений о новых неделях беременности.
    
    Соответствует требованию 10.2 о реализации уведомлений о новой неделе беременности.
    Отслеживает, какие недели беременности уже были отмечены уведомлениями для каждого пользователя.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('delivered', 'Доставлено'),
        ('read', 'Прочитано'),
        ('failed', 'Ошибка отправки'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='pregnancy_week_notifications'
    )
    pregnancy_info = models.ForeignKey(
        'PregnancyInfo',
        on_delete=models.CASCADE,
        verbose_name='Информация о беременности',
        related_name='week_notifications'
    )
    week_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        verbose_name='Номер недели беременности'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок уведомления'
    )
    message = models.TextField(
        verbose_name='Текст уведомления'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Отправлено'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Прочитано'
    )
    
    class Meta:
        verbose_name = 'Уведомление о неделе беременности'
        verbose_name_plural = 'Уведомления о неделях беременности'
        unique_together = ['user', 'pregnancy_info', 'week_number']  # Одно уведомление на неделю
        ordering = ['-week_number', '-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.week_number} неделя ({self.get_status_display()})'
    
    def mark_as_sent(self):
        """Отмечает уведомление как отправленное."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_read(self):
        """Отмечает уведомление как прочитанное."""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    @classmethod
    def create_week_notification(cls, user, pregnancy_info, week_number):
        """
        Создает уведомление о новой неделе беременности.
        
        Args:
            user (User): Пользователь
            pregnancy_info (PregnancyInfo): Информация о беременности
            week_number (int): Номер недели
            
        Returns:
            PregnancyWeekNotification: Созданное уведомление или None если уже существует
        """
        # Проверяем, не создано ли уже уведомление для этой недели
        if cls.objects.filter(
            user=user, 
            pregnancy_info=pregnancy_info, 
            week_number=week_number
        ).exists():
            return None
        
        from webapp.utils.pregnancy_utils import get_week_description
        
        # Создаем персонализированное сообщение
        week_description = get_week_description(week_number)
        
        title = f"🤱 {week_number} неделя беременности!"
        message = f"""Поздравляем! Вы достигли {week_number} недели беременности.

{week_description}

Не забывайте:
• Регулярно посещать врача
• Принимать витамины
• Следить за своим самочувствием
• Отдыхать и заботиться о себе

Желаем вам здоровья и легкой беременности! 💕"""
        
        return cls.objects.create(
            user=user,
            pregnancy_info=pregnancy_info,
            week_number=week_number,
            title=title,
            message=message
        )
    
    @classmethod
    def get_unread_notifications(cls, user):
        """
        Возвращает непрочитанные уведомления о неделях беременности.
        
        Args:
            user (User): Пользователь
            
        Returns:
            QuerySet: Непрочитанные уведомления
        """
        return cls.objects.filter(
            user=user,
            status__in=['pending', 'sent', 'delivered']
        ).select_related('pregnancy_info')
    
    @classmethod
    def check_and_create_new_week_notifications(cls, user=None):
        """
        Проверяет и создает уведомления о новых неделях беременности.
        
        Args:
            user (User, optional): Конкретный пользователь или None для всех
            
        Returns:
            list: Список созданных уведомлений
        """
        created_notifications = []
        
        # Получаем активные беременности
        pregnancy_queryset = PregnancyInfo.objects.filter(is_active=True)
        if user:
            pregnancy_queryset = pregnancy_queryset.filter(user=user)
        
        for pregnancy_info in pregnancy_queryset:
            current_week = pregnancy_info.current_week
            
            if current_week and current_week > 0:
                # Проверяем, есть ли уже уведомление для текущей недели
                notification = cls.create_week_notification(
                    user=pregnancy_info.user,
                    pregnancy_info=pregnancy_info,
                    week_number=current_week
                )
                
                if notification:
                    created_notifications.append(notification)
        
        return created_notifications


class AchievementNotification(models.Model):
    """
    Модель для уведомлений о достижениях.
    
    Используется для отправки уведомлений пользователям о новых достижениях
    и важных вехах в их прогрессе.
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('achievement_earned', 'Достижение получено'),
        ('milestone_reached', 'Веха достигнута'),
        ('progress_update', 'Обновление прогресса'),
        ('encouragement', 'Поощрение'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('delivered', 'Доставлено'),
        ('read', 'Прочитано'),
        ('failed', 'Ошибка отправки'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='achievement_notifications'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Достижение',
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='Тип уведомления'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок уведомления'
    )
    message = models.TextField(
        verbose_name='Текст уведомления'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Отправлено'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Прочитано'
    )
    
    class Meta:
        verbose_name = 'Уведомление о достижении'
        verbose_name_plural = 'Уведомления о достижениях'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} - {self.title} ({self.get_status_display()})'
    
    def mark_as_sent(self):
        """Отмечает уведомление как отправленное."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_read(self):
        """Отмечает уведомление как прочитанное."""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    @classmethod
    def create_achievement_notification(cls, user, achievement):
        """
        Создает уведомление о получении достижения.
        
        Args:
            user (User): Пользователь
            achievement (Achievement): Достижение
            
        Returns:
            AchievementNotification: Созданное уведомление
        """
        return cls.objects.create(
            user=user,
            achievement=achievement,
            notification_type='achievement_earned',
            title=f'Поздравляем! Вы получили достижение "{achievement.title}"',
            message=f'{achievement.icon} {achievement.description}\n\nВы получили {achievement.points} очков!'
        )
    
    @classmethod
    def get_unread_notifications(cls, user):
        """
        Возвращает непрочитанные уведомления пользователя.
        
        Args:
            user (User): Пользователь
            
        Returns:
            QuerySet: Непрочитанные уведомления
        """
        return cls.objects.filter(
            user=user,
            status__in=['pending', 'sent', 'delivered']
        ).select_related('achievement')


class PregnancyInfo(models.Model):
    """
    Модель для хранения информации о беременности пользователя.
    
    Соответствует требованию 10.4 о создании модели для хранения информации о беременности
    для визуального таймера отсчета недель беременности.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='pregnancy_info'
    )
    due_date = models.DateField(
        verbose_name='Предполагаемая дата родов (ПДР)',
        help_text='Дата, рассчитанная врачом на основе УЗИ или последней менструации'
    )
    last_menstrual_period = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата последней менструации',
        help_text='Используется для расчета срока беременности'
    )
    conception_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата зачатия',
        help_text='Если известна точная дата зачатия'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активная беременность',
        help_text='False если беременность завершилась'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Заметки',
        help_text='Дополнительная информация о беременности'
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
        verbose_name = 'Информация о беременности'
        verbose_name_plural = 'Информация о беременности'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Беременность {self.user.username} - ПДР: {self.due_date.strftime("%d.%m.%Y")}'
    
    @property
    def start_date(self):
        """
        Рассчитывает дату начала беременности на основе ПДР.
        Стандартная беременность длится 280 дней (40 недель) от последней менструации.
        
        Returns:
            date: Дата начала беременности
        """
        from webapp.utils.pregnancy_utils import calculate_pregnancy_start_date
        return calculate_pregnancy_start_date(
            due_date=self.due_date,
            last_menstrual_period=self.last_menstrual_period,
            conception_date=self.conception_date
        )
    
    @property
    def current_week(self):
        """
        Рассчитывает текущую неделю беременности.
        
        Returns:
            int: Номер недели беременности (1-42)
        """
        from webapp.utils.pregnancy_utils import calculate_current_pregnancy_week
        return calculate_current_pregnancy_week(
            start_date=self.start_date,
            is_active=self.is_active
        )
    
    @property
    def current_day_of_week(self):
        """
        Рассчитывает текущий день недели беременности.
        
        Returns:
            int: День недели (1-7)
        """
        from webapp.utils.pregnancy_utils import calculate_current_day_of_week
        return calculate_current_day_of_week(
            start_date=self.start_date,
            is_active=self.is_active
        )
    
    @property
    def days_until_due(self):
        """
        Рассчитывает количество дней до ПДР.
        
        Returns:
            int: Количество дней (может быть отрицательным, если ПДР прошла)
        """
        from webapp.utils.pregnancy_utils import calculate_days_until_due
        return calculate_days_until_due(self.due_date)
    
    @property
    def weeks_until_due(self):
        """
        Рассчитывает количество недель до ПДР.
        
        Returns:
            int: Количество недель
        """
        from webapp.utils.pregnancy_utils import calculate_weeks_until_due
        return calculate_weeks_until_due(self.due_date)
    
    @property
    def trimester(self):
        """
        Определяет текущий триместр беременности.
        
        Returns:
            int: Номер триместра (1, 2, 3) или None если беременность неактивна
        """
        from webapp.utils.pregnancy_utils import determine_trimester
        return determine_trimester(self.current_week)
    
    @property
    def progress_percentage(self):
        """
        Рассчитывает процент прогресса беременности.
        
        Returns:
            float: Процент от 0 до 100
        """
        from webapp.utils.pregnancy_utils import calculate_progress_percentage
        return calculate_progress_percentage(self.current_week)
    
    @property
    def is_overdue(self):
        """
        Проверяет, просрочена ли беременность.
        
        Returns:
            bool: True если ПДР прошла
        """
        from webapp.utils.pregnancy_utils import is_pregnancy_overdue
        return is_pregnancy_overdue(self.due_date)
    
    @property
    def is_full_term(self):
        """
        Проверяет, является ли беременность доношенной (37+ недель).
        
        Returns:
            bool: True если беременность доношенная
        """
        from webapp.utils.pregnancy_utils import is_pregnancy_full_term
        return is_pregnancy_full_term(self.current_week)
    
    @property
    def is_preterm_risk(self):
        """
        Проверяет, есть ли риск преждевременных родов (менее 37 недель).
        
        Returns:
            bool: True если есть риск преждевременных родов
        """
        from webapp.utils.pregnancy_utils import is_pregnancy_preterm_risk
        return is_pregnancy_preterm_risk(self.current_week)
    
    @property
    def days_pregnant(self):
        """
        Возвращает количество дней беременности.
        
        Returns:
            int: Количество дней с начала беременности
        """
        from datetime import date
        today = date.today()
        if today < self.start_date:
            return 0
        return (today - self.start_date).days
    
    @property
    def current_trimester(self):
        """
        Возвращает текущий триместр (алиас для trimester).
        
        Returns:
            int: Номер триместра (1, 2, 3)
        """
        return self.trimester
    
    @property
    def is_high_risk_week(self):
        """
        Определяет, является ли текущая неделя беременности высокого риска.
        
        Returns:
            bool: True если неделя высокого риска
        """
        from webapp.utils.pregnancy_utils import is_high_risk_week
        return is_high_risk_week(self.current_week)
    
    @property
    def milestones(self):
        """
        Возвращает информацию о достигнутых вехах беременности.
        
        Returns:
            dict: Словарь с информацией о вехах
        """
        from webapp.utils.pregnancy_utils import get_pregnancy_milestones
        return get_pregnancy_milestones(self.current_week)
    
    def get_week_description(self):
        """
        Возвращает описание текущей недели беременности.
        
        Returns:
            str: Описание недели
        """
        from webapp.utils.pregnancy_utils import get_week_description
        return get_week_description(self.current_week)
    
    def get_important_dates(self):
        """
        Возвращает важные даты беременности.
        
        Returns:
            dict: Словарь с важными датами
        """
        from webapp.utils.pregnancy_utils import get_important_pregnancy_dates
        return get_important_pregnancy_dates(self.start_date, self.due_date)
    
    def should_notify_new_week(self):
        """
        Определяет, нужно ли отправить уведомление о новой неделе.
        Проверяет, изменилась ли неделя с момента последнего обновления.
        
        Returns:
            bool: True если нужно отправить уведомление
        """
        # Эта логика будет использоваться в задаче 11.4
        # Пока возвращаем False, реализация будет в следующей задаче
        return False
    
    @classmethod
    def get_active_pregnancies(cls):
        """
        Возвращает все активные беременности.
        
        Returns:
            QuerySet: Активные беременности
        """
        return cls.objects.filter(is_active=True)
    
    @classmethod
    def get_active_pregnancy(cls, user):
        """
        Возвращает активную беременность пользователя.
        
        Args:
            user (User): Пользователь
            
        Returns:
            PregnancyInfo: Активная беременность или None
        """
        try:
            return cls.objects.get(user=user, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_pregnancy(cls, user, due_date, last_menstrual_period=None, conception_date=None):
        """
        Создает новую запись о беременности.
        
        Args:
            user (User): Пользователь
            due_date (date): Предполагаемая дата родов
            last_menstrual_period (date): Дата последней менструации
            conception_date (date): Дата зачатия
            
        Returns:
            PregnancyInfo: Созданная запись
        """
        # Деактивируем предыдущие беременности
        cls.objects.filter(user=user, is_active=True).update(is_active=False)
        
        return cls.objects.create(
            user=user,
            due_date=due_date,
            last_menstrual_period=last_menstrual_period,
            conception_date=conception_date,
            is_active=True
        )


class FetalDevelopmentInfo(models.Model):
    """
    Модель для хранения информации о развитии плода по неделям беременности.
    
    Соответствует требованию 10.3 о предоставлении информации о развитии плода
    для каждой недели беременности.
    """
    
    week_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(42)],
        unique=True,
        verbose_name='Номер недели беременности'
    )
    
    # Основная информация о развитии
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок недели',
        help_text='Например: "4-я неделя беременности"'
    )
    
    # Размеры плода
    fetal_size_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Описание размера плода',
        help_text='Например: "Размером с маковое зернышко"'
    )
    
    fetal_length_mm = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Длина плода (мм)'
    )
    
    fetal_weight_g = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Вес плода (г)'
    )
    
    # Развитие органов и систем
    organ_development = models.TextField(
        blank=True,
        verbose_name='Развитие органов и систем',
        help_text='Описание того, какие органы и системы развиваются на этой неделе'
    )
    
    # Что происходит с мамой
    maternal_changes = models.TextField(
        blank=True,
        verbose_name='Изменения в организме мамы',
        help_text='Описание изменений, которые происходят в организме матери'
    )
    
    # Симптомы и ощущения
    common_symptoms = models.TextField(
        blank=True,
        verbose_name='Частые симптомы',
        help_text='Список симптомов, которые могут возникнуть на этой неделе'
    )
    
    # Рекомендации
    recommendations = models.TextField(
        blank=True,
        verbose_name='Рекомендации',
        help_text='Рекомендации по питанию, образу жизни, медицинским обследованиям'
    )
    
    # Что можно и нельзя делать
    dos_and_donts = models.TextField(
        blank=True,
        verbose_name='Что можно и нельзя делать',
        help_text='Список рекомендаций о том, что следует делать и чего избегать'
    )
    
    # Медицинские обследования
    medical_checkups = models.TextField(
        blank=True,
        verbose_name='Медицинские обследования',
        help_text='Рекомендуемые медицинские обследования на этой неделе'
    )
    
    # Интересные факты
    interesting_facts = models.TextField(
        blank=True,
        verbose_name='Интересные факты',
        help_text='Интересные факты о развитии плода на этой неделе'
    )
    
    # Изображение для визуализации
    illustration_image = models.ImageField(
        upload_to='fetal_development/',
        null=True,
        blank=True,
        verbose_name='Иллюстрация развития плода'
    )
    
    # Метаданные
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
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
        verbose_name = 'Информация о развитии плода'
        verbose_name_plural = 'Информация о развитии плода'
        ordering = ['week_number']
    
    def __str__(self):
        return f'{self.week_number}-я неделя: {self.title}'
    
    @property
    def trimester(self):
        """Определяет триместр беременности для данной недели."""
        if self.week_number <= 12:
            return 1
        elif self.week_number <= 28:
            return 2
        else:
            return 3
    
    @property
    def trimester_name(self):
        """Возвращает название триместра на русском языке."""
        trimester_names = {
            1: 'Первый триместр',
            2: 'Второй триместр',
            3: 'Третий триместр'
        }
        return trimester_names.get(self.trimester, 'Неизвестный триместр')
    
    @property
    def fetal_size_formatted(self):
        """Возвращает отформатированную информацию о размере плода."""
        parts = []
        
        if self.fetal_size_description:
            parts.append(self.fetal_size_description)
        
        size_details = []
        if self.fetal_length_mm:
            if self.fetal_length_mm < 10:
                size_details.append(f'{self.fetal_length_mm:.1f} мм')
            else:
                size_details.append(f'{self.fetal_length_mm/10:.1f} см')
        
        if self.fetal_weight_g:
            if self.fetal_weight_g < 1000:
                size_details.append(f'{self.fetal_weight_g:.0f} г')
            else:
                size_details.append(f'{self.fetal_weight_g/1000:.2f} кг')
        
        if size_details:
            parts.append(f"({', '.join(size_details)})")
        
        return ' '.join(parts) if parts else 'Информация о размере недоступна'
    
    def get_development_summary(self):
        """Возвращает краткое резюме развития на этой неделе."""
        summary_parts = []
        
        if self.organ_development:
            # Берем первое предложение из описания развития органов
            first_sentence = self.organ_development.split('.')[0] + '.'
            summary_parts.append(first_sentence)
        
        if self.fetal_size_description:
            summary_parts.append(f"Размер плода: {self.fetal_size_description.lower()}")
        
        return ' '.join(summary_parts) if summary_parts else 'Информация о развитии недоступна'
    
    @classmethod
    def get_info_for_week(cls, week_number):
        """
        Получает информацию о развитии плода для указанной недели.
        
        Args:
            week_number (int): Номер недели беременности
            
        Returns:
            FetalDevelopmentInfo: Информация о развитии или None
        """
        try:
            return cls.objects.get(week_number=week_number, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_weeks_range(cls, start_week, end_week):
        """
        Получает информацию о развитии плода для диапазона недель.
        
        Args:
            start_week (int): Начальная неделя
            end_week (int): Конечная неделя
            
        Returns:
            QuerySet: Информация о развитии для указанного диапазона
        """
        return cls.objects.filter(
            week_number__gte=start_week,
            week_number__lte=end_week,
            is_active=True
        ).order_by('week_number')
    
    @classmethod
    def get_by_trimester(cls, trimester):
        """
        Получает информацию о развитии плода для указанного триместра.
        
        Args:
            trimester (int): Номер триместра (1, 2 или 3)
            
        Returns:
            QuerySet: Информация о развитии для указанного триместра
        """
        if trimester == 1:
            return cls.objects.filter(week_number__lte=12, is_active=True)
        elif trimester == 2:
            return cls.objects.filter(week_number__gte=13, week_number__lte=28, is_active=True)
        elif trimester == 3:
            return cls.objects.filter(week_number__gte=29, is_active=True)
        else:
            return cls.objects.none()
    
    def get_next_week_info(self):
        """Возвращает информацию о следующей неделе."""
        try:
            return FetalDevelopmentInfo.objects.get(
                week_number=self.week_number + 1,
                is_active=True
            )
        except FetalDevelopmentInfo.DoesNotExist:
            return None
    
    def get_previous_week_info(self):
        """Возвращает информацию о предыдущей неделе."""
        try:
            return FetalDevelopmentInfo.objects.get(
                week_number=self.week_number - 1,
                is_active=True
            )
        except FetalDevelopmentInfo.DoesNotExist:
            return None