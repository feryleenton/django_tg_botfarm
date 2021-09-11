import asyncio
from time import sleep

from django.contrib import admin, messages
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import PeerUser
from threading import Thread

from .models import Parsing, Mailings, User, Bot, Group, Inviting
from telethon.sync import TelegramClient
from sessions.parser.parser_config import api_id, api_hash, phone
import logging

admin.site.site_header = 'Mailing RUS'


class InvitingAdmin(admin.ModelAdmin):
    def start_inviting(self, request, queryset):
        messages.success(request, 'Инвайтинг начат')

        def do_inviting():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            for inviting in queryset:
                group_users = User.objects.filter(group=inviting.users_group_id)
                target_group = inviting.group
                bots = Bot.objects.filter(bot_type='INVITER')

                user_counter = 0

                for bot in bots:
                    while user_counter < len(group_users):
                        sleep(15)
                        if user_counter == 30:
                            # каждый бот может добавлять по N пользователей
                            break

                        try:
                            client = TelegramClient(str(bot.session_link), int(bot.api_id),
                                                    str(bot.api_hash))
                            client.connect()
                            try:
                                my_group = client.get_entity(target_group)
                                user_to_add = client.get_entity(group_users[user_counter].username)
                                client(InviteToChannelRequest(my_group, [user_to_add]))
                                print(str(bot.phone) + '----INVITED--->' + str(group_users[user_counter]))
                            except Exception as e:
                                logging.warning('INVITE ERROR: ' + str(e))
                                try:
                                    client.disconnect()
                                except:
                                    pass
                            client.disconnect()
                        except Exception as e:
                            logging.warning('INVITING ERROR: ' + str(e))

                        user_counter = user_counter + 1

        t = Thread(target=do_inviting)
        t.daemon = True
        t.start()

    start_inviting.short_description = 'Начать инвайтинг'

    actions = ['start_inviting', ]


class ParsingAdmin(admin.ModelAdmin):
    def start_parsing(self, request, queryset):
        logging.info('parsing action started')
        # авторизируемся, как парсинг-бот
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client = TelegramClient('sessions/parser/' + str(phone) + '.session', api_id, api_hash)

        client.start()
        # client.connect()

        try:
            logging.info('client connected')

            for parsing_obj in queryset:
                logging.info('scrapping started')
                target_group_id = parsing_obj.group.pk
                print('\n\n\ntarget group id: ' + str(target_group_id))
                target_group = Group.objects.filter(pk=target_group_id)
                print('target group qs: ' + str(target_group))
                entity = client.get_entity(target_group[0].link)
                logging.info('got entity')
                all_participants = []
                all_participants = client.get_participants(entity, aggressive=True)
                logging.info('got all group participants')

                for participant in all_participants:
                    if User.objects.filter(user_id=participant.id):
                        print('passed')
                    else:
                        if participant.username:
                            user = User(user_id=participant.id,
                                        user_full_name=str(participant.first_name) + ' ' + str(participant.last_name),
                                        group=target_group[0], username=participant.username)
                            user.save()
                        else:
                            pass
                messages.success(request, 'Парсинг успешно выполнен')
        except Exception as e:
            messages.error(request, 'Не удалось выполнить парсинг')
            logging.warning('PARSING EXCEPTION: ' + str(e))
        logging.info('scrapping finished')
        client.disconnect()
        logging.info('client disconnected')

    start_parsing.short_description = 'Начать парсинг'

    actions = ['start_parsing', ]


class GroupAdmin(admin.ModelAdmin):
    pass


class UserAdmin(admin.ModelAdmin):
    pass


class MailingsAdmin(admin.ModelAdmin):
    def start_mailing(self, request, queryset):
        messages.info(request, 'Рассылка начата')
        try:

            def do_mailing():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                for mailing in queryset:
                    group_users = User.objects.filter(group=mailing.group_id)
                    bots = Bot.objects.filter(bot_type='MAILER')

                    group_users_counter = 0
                    bots_counter = 0
                    while bots_counter < len(bots) and group_users_counter < len(group_users):

                        # print(str(bots[bots_counter]) + ' ----> ' + str(group_users[group_users_counter]))

                        sleep(10)

                        try:
                            client = TelegramClient(str(bots[bots_counter].session_link),
                                                    int(bots[bots_counter].api_id),
                                                    str(bots[bots_counter].api_hash))
                            client.connect()
                            my_user = client.get_entity(group_users[group_users_counter].username)
                            print(str(bots[bots_counter].phone) + ' ----> ' + str(
                                group_users[group_users_counter].username))
                            client.send_message(my_user, mailing.text)
                            client.disconnect()
                        except Exception as e:
                            logging.warning('SEND MESSAGE ERROR: ' + str(e))

                            try:
                                client.disconnect()
                            except Exception as e:
                                pass

                        if bots_counter == len(bots) - 1:
                            bots_counter = 0
                        else:
                            bots_counter = bots_counter + 1
                        group_users_counter = group_users_counter + 1

            t = Thread(target=do_mailing)
            t.daemon = True
            t.start()

        except Exception as e:
            messages.error(request, 'Рассылка не удалась (неизвестная ошибка)')
            logging.warning('MAILING ERROR: ' + str(e))

    start_mailing.short_description = 'Начать рассылку'

    actions = ['start_mailing', ]


class BotAdmin(admin.ModelAdmin):

    class Media:
        js = ('//ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js', '/static/admin_button.js',)

    fields = ('bot_type', 'phone', 'admin_unit_details', 'ver_code', 'admin_auth_code', 'auth_code')
    readonly_fields = ('admin_unit_details', 'admin_auth_code')


admin.site.register(Parsing, ParsingAdmin)
admin.site.register(Mailings, MailingsAdmin)
admin.site.register(Inviting, InvitingAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Bot, BotAdmin)
admin.site.register(Group, GroupAdmin)