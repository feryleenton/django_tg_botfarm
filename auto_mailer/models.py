import asyncio
import logging
import re

from django.db import models

# Create your models here.
from django.db import models
from telethon import TelegramClient, sync
from .helper_funcs import step_two
# Create your models here.
from django.utils.html import format_html

from .helper_funcs.helper_steps import parse_to_meaning_ful_text
from .helper_funcs.step_four import create_new_tg_app
from .helper_funcs.step_three import scarp_tg_existing_app


class Group(models.Model):
    class Meta:
        verbose_name = 'Группа для парсинга'
        verbose_name_plural = 'Группы для парсинга'
        db_table = 'group'

    title = models.CharField(max_length=225, verbose_name='Название группы')
    link = models.CharField(max_length=225, verbose_name='Ссылка на группу')

    def __str__(self):
        return self.title


class User(models.Model):
    """Пользователь полученый после парсинга групп"""
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'user'

    user_id = models.IntegerField()
    user_full_name = models.CharField(max_length=225, verbose_name='Имя пользователя')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Получен из группы')
    username = models.CharField(max_length=225, verbose_name='Юзернейм', null=True, blank=True)

    def __str__(self):
        return str(self.user_full_name) + ' ( ' + str(self.user_id) + ' ) '


class Parsing(models.Model):
    class Meta:
        verbose_name = 'Парсинг'
        verbose_name_plural = 'Парсинг'
        db_table = 'parsing'

    title = models.CharField(max_length=225, null=True, blank=True, verbose_name='Название')
    # link = models.CharField(max_length=225, verbose_name='Ссылка на группу')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа для парсинга')

    def __str__(self):
        return str(self.title) + ' ( ' + str(self.group) + ' )'


class Inviting(models.Model):
    class Meta:
        verbose_name = 'Инвайтинг'
        verbose_name_plural = 'Инвайтинг'
        db_table = 'inviting'

    title = models.CharField(max_length=225, null=True, blank=True, verbose_name='Название')
    group = models.CharField(max_length=225, verbose_name='Приглашать в группу (ссылка)')
    # link = models.CharField(max_length=225, verbose_name='Ссылка на группу')
    users_group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Приглашать пользователей из парсинг-группы')

    def __str__(self):
        return str(self.title) + ' ( ' + str(self.group) + ' )'


class Mailings(models.Model):
    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        db_table = 'mailing'

    title = models.CharField(max_length=225, verbose_name='Название')
    text = models.TextField(verbose_name='Сообщение')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Рассылка по группе')

    def __str__(self):
        return self.title


class Bot(models.Model):
    """Бот, от лица которого ведеться рассылка"""

    class Meta:
        verbose_name = 'Бот'
        verbose_name_plural = 'Боты'
        db_table = 'bot'

    def admin_unit_details(self):  # Button for admin to get to API
        return format_html(u'<a href="#" onclick="return false;" class="button" '
                           u'id="id_admin_unit_selected">Запросить код</a>')

    def admin_auth_code(self):  # Button for admin to get to API
        return format_html(u'<a href="#" onclick="return false;" class="button" '
                           u'id="id_admin_auth_code">Запросить код</a>')

    def save(self, *args, **kwargs):
        from .views import phone_code_hash, api_id, api_hash

        start = "SentCode(type=SentCodeTypeApp(length=5), phone_code_hash='"
        end = "', next_type=CodeTypeSms(), timeout=None)"
        phone_code_hash = str(phone_code_hash)[str(phone_code_hash).find(start)+len(start):str(phone_code_hash).rfind(end)]

        print(str(api_id), str(api_hash), str(phone_code_hash))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client = TelegramClient('sessions/' + str(self.phone), int(api_id), str(api_hash))

        print(phone_code_hash)

        client.connect()
        client.sign_in(str(self.phone), str(self.auth_code), phone_code_hash=phone_code_hash)
        self.api_id = api_id
        self.api_hash = api_hash
        self.status = True
        self.session_link = 'sessions/' + str(self.phone) + '.session'

        client.disconnect()

        super(Bot, self).save(*args, **kwargs)

    admin_unit_details.short_description = "Отправить код ClientAPI"
    admin_auth_code.short_description = "Отправить код аунтификации"

    CHOICES = (
        ('MAILER', 'Для рассылок'),
        ('INVITER', 'Для инвайтинга'),
    )

    phone = models.CharField(max_length=225, verbose_name='Номер телефона')
    ver_code = models.CharField(max_length=225, verbose_name='Код верефикации ClientAPI')
    auth_code = models.CharField(max_length=225, verbose_name='Код аунтификации Telegram')
    session_link = models.CharField(max_length=225, editable=False)
    api_id = models.IntegerField(blank=True, null=True, editable=False)
    api_hash = models.CharField(max_length=225, blank=True, null=True, editable=False)
    status = models.BooleanField(default=False, editable=False)
    bot_type = models.CharField(max_length=225, choices=CHOICES, verbose_name='Тип бота')

    def __str__(self):
        return self.phone


class RandHash(models.Model):
    phone = models.CharField(max_length=255)
    hash = models.CharField(max_length=1000)