from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Poll(models.Model):
    question = models.CharField(max_length=200, verbose_name="Soru")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="polls",
        verbose_name="Yazar",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Anket"
        verbose_name_plural = "Anketler"

    def __str__(self):
        return self.question


class Option(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Anket",
    )
    text = models.CharField(max_length=100, verbose_name="Seçenek Metni")
    position = models.PositiveSmallIntegerField(default=0, verbose_name="Sıralama")

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Seçenek"
        verbose_name_plural = "Seçenekler"

    def __str__(self):
        return f"{self.poll.question[:30]} - {self.text}"


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Anket",
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Seçenek",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="votes",
        verbose_name="Kullanıcı",
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name="Oturum Anahtarı",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oy Tarihi")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_poll_user_vote",
            ),
            models.UniqueConstraint(
                fields=["poll", "session_key"],
                condition=models.Q(session_key__isnull=False),
                name="unique_poll_session_vote",
            ),
        ]
        verbose_name = "Oy"
        verbose_name_plural = "Oylar"

    def clean(self):
        super().clean()
        if self.option_id and self.poll_id and self.option.poll_id != self.poll_id:
            raise ValidationError("Seçenek bu ankete ait olmalıdır.")
        if not self.user and not self.session_key:
            raise ValidationError("Oy bir kullanıcıya veya bir ziyaretçi oturumuna ait olmalıdır.")

    def __str__(self):
        voter = f"@{self.user.username}" if self.user else f"Session({self.session_key})"
        return f"{voter} -> {self.option.text} ({self.poll.question[:20]})"
