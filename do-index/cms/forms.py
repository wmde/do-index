class LoginForm(forms.Form):
        email = forms.CharField(label=(u'Email'), max_length=30)
	password = forms.CharField(label=(u'Pass'), widget=forms.PasswordInput(render_value=False), max_length=30)
