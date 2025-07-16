"""
Скрипт для заполнения базы данных стандартными прививками.

Этот скрипт заполняет базу данных стандартными прививками согласно
национальному календарю профилактических прививок России.
"""

from botapp.models import db_manager
from botapp.models_vaccine import Vaccine, create_vaccine

def populate_standard_vaccines():
    """
    Заполняет базу данных стандартными прививками.
    
    Возвращает:
        int: Количество добавленных вакцин
    """
    session = db_manager.get_session()
    try:
        # Проверяем, есть ли уже вакцины в базе
        existing_count = session.query(Vaccine).count()
        if existing_count > 0:
            print(f"В базе данных уже есть {existing_count} вакцин. Пропускаем заполнение.")
            return 0
        
        # Список стандартных вакцин согласно национальному календарю профилактических прививок России
        standard_vaccines = [
            {
                "name": "Гепатит B (1)",
                "description": "Первая вакцинация против вирусного гепатита B.",
                "recommended_age": "В первые 24 часа жизни",
                "is_mandatory": True
            },
            {
                "name": "БЦЖ",
                "description": "Вакцинация против туберкулеза.",
                "recommended_age": "3-7 день",
                "is_mandatory": True
            },
            {
                "name": "Гепатит B (2)",
                "description": "Вторая вакцинация против вирусного гепатита B.",
                "recommended_age": "1 месяц",
                "is_mandatory": True
            },
            {
                "name": "АКДС (1)",
                "description": "Первая вакцинация против дифтерии, коклюша, столбняка.",
                "recommended_age": "3 месяца",
                "is_mandatory": True
            },
            {
                "name": "Полиомиелит (1)",
                "description": "Первая вакцинация против полиомиелита.",
                "recommended_age": "3 месяца",
                "is_mandatory": True
            },
            {
                "name": "Пневмококковая инфекция (1)",
                "description": "Первая вакцинация против пневмококковой инфекции.",
                "recommended_age": "3 месяца",
                "is_mandatory": True
            },
            {
                "name": "АКДС (2)",
                "description": "Вторая вакцинация против дифтерии, коклюша, столбняка.",
                "recommended_age": "4.5 месяца",
                "is_mandatory": True
            },
            {
                "name": "Полиомиелит (2)",
                "description": "Вторая вакцинация против полиомиелита.",
                "recommended_age": "4.5 месяца",
                "is_mandatory": True
            },
            {
                "name": "Пневмококковая инфекция (2)",
                "description": "Вторая вакцинация против пневмококковой инфекции.",
                "recommended_age": "4.5 месяца",
                "is_mandatory": True
            },
            {
                "name": "АКДС (3)",
                "description": "Третья вакцинация против дифтерии, коклюша, столбняка.",
                "recommended_age": "6 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Полиомиелит (3)",
                "description": "Третья вакцинация против полиомиелита.",
                "recommended_age": "6 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Гепатит B (3)",
                "description": "Третья вакцинация против вирусного гепатита B.",
                "recommended_age": "6 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Корь, краснуха, паротит",
                "description": "Вакцинация против кори, краснухи, эпидемического паротита.",
                "recommended_age": "12 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Пневмококковая инфекция (3)",
                "description": "Ревакцинация против пневмококковой инфекции.",
                "recommended_age": "15 месяцев",
                "is_mandatory": True
            },
            {
                "name": "АКДС (4)",
                "description": "Первая ревакцинация против дифтерии, коклюша, столбняка.",
                "recommended_age": "18 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Полиомиелит (4)",
                "description": "Первая ревакцинация против полиомиелита.",
                "recommended_age": "18 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Полиомиелит (5)",
                "description": "Вторая ревакцинация против полиомиелита.",
                "recommended_age": "20 месяцев",
                "is_mandatory": True
            },
            {
                "name": "Корь, краснуха, паротит (2)",
                "description": "Ревакцинация против кори, краснухи, эпидемического паротита.",
                "recommended_age": "6 лет",
                "is_mandatory": True
            },
            {
                "name": "АДС",
                "description": "Вторая ревакцинация против дифтерии, столбняка.",
                "recommended_age": "6-7 лет",
                "is_mandatory": True
            },
            {
                "name": "БЦЖ (2)",
                "description": "Ревакцинация против туберкулеза.",
                "recommended_age": "7 лет",
                "is_mandatory": True
            },
            {
                "name": "АДС-М",
                "description": "Третья ревакцинация против дифтерии, столбняка.",
                "recommended_age": "14 лет",
                "is_mandatory": True
            },
            {
                "name": "Полиомиелит (6)",
                "description": "Третья ревакцинация против полиомиелита.",
                "recommended_age": "14 лет",
                "is_mandatory": True
            },
            # Рекомендуемые, но не обязательные вакцины
            {
                "name": "Ротавирусная инфекция (1)",
                "description": "Первая вакцинация против ротавирусной инфекции.",
                "recommended_age": "2 месяца",
                "is_mandatory": False
            },
            {
                "name": "Ротавирусная инфекция (2)",
                "description": "Вторая вакцинация против ротавирусной инфекции.",
                "recommended_age": "3 месяца",
                "is_mandatory": False
            },
            {
                "name": "Ротавирусная инфекция (3)",
                "description": "Третья вакцинация против ротавирусной инфекции.",
                "recommended_age": "4.5 месяца",
                "is_mandatory": False
            },
            {
                "name": "Грипп",
                "description": "Вакцинация против гриппа. Проводится ежегодно.",
                "recommended_age": "С 6 месяцев, ежегодно",
                "is_mandatory": False
            },
            {
                "name": "Гемофильная инфекция (1)",
                "description": "Первая вакцинация против гемофильной инфекции.",
                "recommended_age": "3 месяца",
                "is_mandatory": False
            },
            {
                "name": "Гемофильная инфекция (2)",
                "description": "Вторая вакцинация против гемофильной инфекции.",
                "recommended_age": "4.5 месяца",
                "is_mandatory": False
            },
            {
                "name": "Гемофильная инфекция (3)",
                "description": "Третья вакцинация против гемофильной инфекции.",
                "recommended_age": "6 месяцев",
                "is_mandatory": False
            },
            {
                "name": "Гемофильная инфекция (4)",
                "description": "Ревакцинация против гемофильной инфекции.",
                "recommended_age": "18 месяцев",
                "is_mandatory": False
            },
            {
                "name": "Менингококковая инфекция",
                "description": "Вакцинация против менингококковой инфекции.",
                "recommended_age": "С 9 месяцев",
                "is_mandatory": False
            },
            {
                "name": "Ветряная оспа",
                "description": "Вакцинация против ветряной оспы.",
                "recommended_age": "С 12 месяцев",
                "is_mandatory": False
            },
            {
                "name": "Гепатит A",
                "description": "Вакцинация против вирусного гепатита A.",
                "recommended_age": "С 12 месяцев",
                "is_mandatory": False
            },
            {
                "name": "ВПЧ",
                "description": "Вакцинация против вируса папилломы человека.",
                "recommended_age": "С 9 лет (девочки)",
                "is_mandatory": False
            }
        ]
        
        # Добавляем вакцины в базу данных
        for vaccine_data in standard_vaccines:
            create_vaccine(
                name=vaccine_data["name"],
                description=vaccine_data["description"],
                recommended_age=vaccine_data["recommended_age"],
                is_mandatory=vaccine_data["is_mandatory"]
            )
        
        print(f"Добавлено {len(standard_vaccines)} стандартных вакцин в базу данных.")
        return len(standard_vaccines)
    
    except Exception as e:
        print(f"Ошибка при заполнении базы данных вакцинами: {e}")
        session.rollback()
        raise e
    finally:
        db_manager.close_session(session)


if __name__ == "__main__":
    # Создаем таблицы, если они еще не существуют
    db_manager.create_tables()
    
    # Заполняем базу данных стандартными вакцинами
    populate_standard_vaccines()