from django.db import models
from django.contrib.auth.models import User


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
