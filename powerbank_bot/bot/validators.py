import re
from abc import abstractmethod


class ValidationResult:
    def __init__(self, result, error=None):
        self.result = result
        self.error = error

    def __str__(self):
        return 'ValidationResult(result={0.result!r}, error={0.error!r})'.format(self)


class BaseValidator:
    @abstractmethod
    def __call__(self, value):
        pass


class IntegerValidator(BaseValidator):
    def __init__(self, error='Не число'):
        self.error = error

    def __call__(self, value):
        try:
            int(value)
        except ValueError:
            return ValidationResult(False, self.error)
        return ValidationResult(True)


class RangeIntegerValidator(IntegerValidator):
    def __init__(self, min_value, max_value):
        super().__init__()
        self.min_value = min_value
        self.max_value = max_value
        self.error = 'Введите число из диапазона [{}, {}]'.format(min_value, max_value)

    def __call__(self, value):
        parent_validation_res = super().__call__(value)
        if parent_validation_res.result:
            if self.min_value <= int(value) <= self.max_value:
                return ValidationResult(True)
            return ValidationResult(False, self.error)
        else:
            return parent_validation_res


class RegexpValidator(BaseValidator):
    def __init__(self, reg_exp, error=None):
        self.reg_exp = reg_exp
        self.error = error

    def __call__(self, value):
        is_match = bool(re.match(self.reg_exp, value))
        return ValidationResult(is_match, None if is_match else self.error)


class LoginValidator(BaseValidator):
    def __init__(self):
        self.error = 'Введите логин'

    def __call__(self, value):
        is_match = bool(value)
        return ValidationResult(is_match, None if is_match else self.error)


class PhoneNumberValidator(RegexpValidator):
    def __init__(self):
        super().__init__('\d{2}\s\d{7}')
        self.error = 'Номер не соответствует формату +375XX XXXXXXX'
