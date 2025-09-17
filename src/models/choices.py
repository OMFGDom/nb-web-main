from enum import Enum

LANGUAGE_CHOICES = [("en", "ENG"), ("ru", "РУС"), ("kz", "ҚАЗ")]

ANOUNC_TYPE_CHOICES = [("fb", "Forbes"), ("fw", "Forbes Women"), ("fk", "Forbes Kazakh")]

PR_ARTICLE_TYPE_CHOICES = [("1", "Со значком"), ("2", "Без значка")]

FIELD_TYPES_CHOICES = [("int", "Целое число"), ("float", "Дробное число"), ("str", "Текст")]

ORDER_TYPE_CHOICES = [("asc", "по возрастанию"), ("desk", "по убыванию")]

RUBRIC_TYPE_CHOICES = [("news", "Новость"), ("article", "Статья")]


class ANOUNC_TYPE_ENUM(Enum):
    fb = "Forbes"
    fw = "Forbes Women"
    fk = "Forbes Kazakh"


class PR_ARTICLE_TYPE_ENUM(Enum):
    with_icon = "Со значком"
    without_icon = "Без значка"


class LANGUAGE_ENUM(Enum):
    en = "ENG"
    ru = "РУС"
    kz = "ҚАЗ"


class FIELD_TYPES_ENUM(Enum):
    int_col = 'Целое число'
    float_col = 'Дробное число'
    str_col = 'Текст'


class ORDER_TYPE_ENUM(Enum):
    asc = "по возрастанию"
    desk = "по убыванию"


class ModuleTypeEnum(Enum):
    header = 'header'
    footer = 'footer'
    menu = 'menu'
