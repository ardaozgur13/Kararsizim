from django import forms
from .models import Poll, Option


class PollCreateForm(forms.Form):
    question = forms.CharField(
        label="Kararsız Kaldığın Soru",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Örn: Bugün sinemaya mı gitsem, tiyatroya mı?",
                "autofocus": True,
            }
        ),
        help_text="En fazla 200 karakter. Topluluğun fikrini almak istediğin soruyu yaz.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleaned_options = []

    def clean_question(self):
        question = self.cleaned_data.get("question", "").strip()
        if not question:
            raise forms.ValidationError("Soru alanı boş bırakılamaz.")
        if len(question) < 5:
            raise forms.ValidationError("Soru en az 5 karakter uzunluğunda olmalıdır.")
        return question

    def clean(self):
        cleaned_data = super().clean()
        raw_options = self.data.getlist("options") if hasattr(self.data, "getlist") else []

        # Boşlukları temizle ve boş olmayanları al
        trimmed_options = [opt.strip() for opt in raw_options if opt.strip()]

        if len(trimmed_options) < 2:
            self.add_error(None, "Bir anket oluşturmak için en az 2 seçenek girmelisin.")
        elif len(trimmed_options) > 5:
            self.add_error(None, "Bir ankette en fazla 5 seçenek bulunabilir.")

        seen_normalized = set()
        for opt in trimmed_options:
            if len(opt) > 100:
                self.add_error(
                    None,
                    f"'{opt[:25]}...' seçeneği çok uzun (en fazla 100 karakter olabilir).",
                )
            normalized = opt.lower()
            if normalized in seen_normalized:
                self.add_error(
                    None,
                    f"Aynı seçenek birden fazla kez eklenemez: '{opt}'",
                )
            seen_normalized.add(normalized)

        self.cleaned_options = trimmed_options
        return cleaned_data

    def save(self, author):
        question = self.cleaned_data["question"]
        poll = Poll.objects.create(question=question, author=author)
        for index, option_text in enumerate(self.cleaned_options):
            Option.objects.create(poll=poll, text=option_text, position=index)
        return poll
