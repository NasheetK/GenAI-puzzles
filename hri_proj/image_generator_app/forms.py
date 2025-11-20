from django import forms

class PuzzlePromptForm(forms.Form):
    CHARACTER_CHOICES = [
        ("Cat", "Cat"),
        ("Dog", "Dog"),
        ("Tiger", "Tiger"),
        ("Rabbit", "Rabbit"),
        ("Bear", "Bear"),
    ]
    ACTIVITY_CHOICES = [
        ("School", "School"),
        ("Playground", "Playground"),
        ("Forest", "Forest"),
    ]

    character = forms.ChoiceField(choices=CHARACTER_CHOICES)
    activity = forms.ChoiceField(choices=ACTIVITY_CHOICES)
