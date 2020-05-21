from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class QueryTerm(FlaskForm):
	query_terms = StringField('Enter query below: ',
						   validators=[DataRequired(), Length(min=2, max=999)])
	submit = SubmitField('Submit')
