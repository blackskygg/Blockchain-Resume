from wtforms.fields import (
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    Field,
)
from wtforms.validators import (
    StopValidation,
    ValidationError,
    InputRequired,
    EqualTo,
    Email,
    Regexp,
    Length,
    Optional,
)
import models

from form import Form

from .. import baseForms
from .. import baseValidators


class LoginForm(Form):
    """
    Used in :
        user.LoginHandler
            method=['POST']
            Get auth token
    """
    identifyNum = StringField('identityNum', [
        InputRequired(),
        Length(max=30),
    ])
    password = StringField('password', [
        Length(max=30),
        InputRequired(),
    ])

    def validate_email(form, field):
        _ = field.gettext
        try:
            user = models.User.query \
                .filter_by(identityNum=form.identifyNum.data) \
                .first()
            assert user.check_password(form.password.data) is True
            form.kwargs['user'] = user
        except Exception:
            raise ValidationError(_('Email or password False.'))

    validate_password = validate_email


class RegisterForm(Form):
    password = StringField('password', [
        InputRequired(),
        Length(max=20),
    ])
    realname = StringField('realname', [
        InputRequired(),
        Length(max=30)
    ])
    identityNum = StringField('identityNum', [
        InputRequired(),
        Length(max=18)
    ])

    def validate_username(form, field):
        _ = field.gettext
        count = models.User.query.filter(models.User.identityNum == field.data).count()
        if count != 0:
            raise ValidationError('This identifyNum has been used.')

    def validata_username(form, field):
        return True
