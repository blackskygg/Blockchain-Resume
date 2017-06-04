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
    companyName = StringField('companyName', [
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
            company = models.Company.query \
                .filter_by(companyName=form.companyName.data) \
                .first()
            assert company.check_password(form.password.data) is True
            form.kwargs['company'] = company
        except Exception:
            raise ValidationError(_('Email or password False.'))

    validate_password = validate_email


class RegisterForm(Form):
    companyName = StringField('companyName', [
        InputRequired(),
    ])
    password = StringField('password', [
        InputRequired(),
        Length(max=20),
    ])

    def validate_company_name(form, field):
        _ = field.gettext
        count = models.Company.query.filter(models.Company.companyName == field.data).count()
        if count != 0:
            raise ValidationError('This company_name has been used.')


class IssueForm(Form):
    realname = StringField('realname', [
        InputRequired(),
    ])
    identifyNum = StringField('identifyNum', [
        Length(max=18, min=18)
    ])
    content = StringField('content', [
        InputRequired()
    ])
    hash = StringField('hash', [
        InputRequired()
    ])
    certsName = StringField('certsName', [
        InputRequired()
    ])
