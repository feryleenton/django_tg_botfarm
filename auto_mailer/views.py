import asyncio

from django.shortcuts import render

# Create your views here.

from django.contrib.auth.models import User
from telethon import TelegramClient, sync
from .helper_funcs import step_one, step_two
from django.http import JsonResponse, HttpResponse

from .helper_funcs.helper_steps import parse_to_meaning_ful_text
from .helper_funcs.step_four import create_new_tg_app
from .helper_funcs.step_three import scarp_tg_existing_app
from .models import RandHash, Bot

phone_code_hash = None
api_id = None
api_hash = None


def send_code(request):
    phone = request.GET.get('phone', None)
    random_hash = step_one.request_tg_code_get_random_hash(phone)

    if RandHash.objects.filter(phone=phone):
        print('deleting existed hash')
        hash = RandHash.objects.filter(phone=phone)
        hash.delete()

        bot = Bot.objects.filter(phone=phone)
        bot.delete()

        new_hash = RandHash(phone=phone, hash=random_hash)
        new_hash.save()
        print('new hash created')
    else:

        print('creating new hash obj')

        new_hash = RandHash(phone=phone, hash=random_hash)
        new_hash.save()

    return HttpResponse(200)


def send_auth_code(request):
    phone = request.GET.get('phone', None)
    ver_code = request.GET.get('ver_code', None)

    # создаем api_id, api_hash
    random_hash_qs = RandHash.objects.filter(phone=phone)
    random_hash = random_hash_qs[0].hash
    print('rh ' + str(random_hash))

    # login using provided code, and get cookie
    status_r, cookie_v = step_two.login_step_get_stel_cookie(
        phone,
        random_hash,
        ver_code
    )

    if status_r:
        # scrap the my.telegram.org/apps page
        # and check if the user had previously created an app
        status_t, response_dv = scarp_tg_existing_app(cookie_v)
        print(status_t)
        if not status_t:
            # if not created
            # create an app by the provided details
            create_new_tg_app(
                cookie_v,
                response_dv.get("tg_app_hash"),
                'hjehktherk',
                'kdfjhgjkhdh',
                'jhfgkjdhfg',
                'weuruweroi',
                'hjhdfgjkhd'
            )
            print('new tg app created')
        status_t, response_dv = scarp_tg_existing_app(cookie_v)
        if status_t:
            # parse the scrapped page into an user readable
            # message
            me_t = parse_to_meaning_ful_text(
                phone,
                response_dv
            )
            print(me_t[0], me_t[1])
            global api_id
            global api_hash
            api_id = me_t[0]
            api_hash = me_t[1]
            print('got api_id/api_hash')

    # отправка кода авторизации
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print('\n\n\n')
    print(api_id, api_hash)

    client = TelegramClient('sessions/' + str(phone), api_id, api_hash)

    client.connect()
    print(client.get_me())
    global phone_code_hash
    phone_code_hash = client.send_code_request(phone=phone)
    client.disconnect()

    return HttpResponse(200)
