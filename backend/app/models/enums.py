import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    prefer_not_to_say = "prefer_not_to_say"


class PriceRangeEnum(str, enum.Enum):
    one = "$"
    two = "$$"
    three = "$$$"
    four = "$$$$"


class DayOfWeekEnum(str, enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class SortPreferenceEnum(str, enum.Enum):
    rating = "rating"
    review_count = "review_count"
    distance = "distance"
    price = "price"
    recommended = "recommended"
    name = "name"
